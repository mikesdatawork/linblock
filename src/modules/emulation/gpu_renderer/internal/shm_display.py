"""
Shared memory display for GPU renderer output.

Provides a fast path for transferring rendered frames from the
GPU renderer process to the GTK3 display widget.
"""

import mmap
import struct
import os
import ctypes
from typing import Optional, Callable
from dataclasses import dataclass
import threading


# Shared memory layout constants
SHM_MAGIC = 0x4C424B44  # "LBKD"
SHM_VERSION = 1
SHM_HEADER_SIZE = 64  # Fixed header size


@dataclass
class ShmHeader:
    """Header structure for shared memory display."""
    magic: int = SHM_MAGIC
    version: int = SHM_VERSION
    width: int = 0
    height: int = 0
    stride: int = 0
    format: int = 1  # BGRA8888
    frame_number: int = 0
    timestamp_ns: int = 0


class SharedMemoryDisplay:
    """
    Manages shared memory for display frame transfer.

    Used to transfer rendered frames from the GPU renderer process
    to the GTK3 display widget without copying.
    """

    HEADER_FORMAT = "<IIIIIIQQ"  # magic, version, w, h, stride, format, frame_num, timestamp
    HEADER_SIZE = struct.calcsize(HEADER_FORMAT)

    def __init__(self, name: str = "/linblock_display"):
        self._name = name
        self._fd: Optional[int] = None
        self._mmap: Optional[mmap.mmap] = None
        self._size = 0
        self._width = 0
        self._height = 0
        self._frame_callback: Optional[Callable] = None
        self._lock = threading.Lock()
        self._last_frame_number = 0

    def create(self, width: int, height: int) -> None:
        """Create shared memory region for display.

        Args:
            width: Display width in pixels
            height: Display height in pixels
        """
        self._width = width
        self._height = height
        stride = width * 4  # BGRA
        pixel_size = stride * height
        self._size = self.HEADER_SIZE + pixel_size

        # Create POSIX shared memory
        try:
            # Remove existing if present
            try:
                os.unlink(f"/dev/shm{self._name}")
            except FileNotFoundError:
                pass

            self._fd = os.open(
                f"/dev/shm{self._name}",
                os.O_CREAT | os.O_RDWR,
                0o600
            )
            os.ftruncate(self._fd, self._size)

            self._mmap = mmap.mmap(self._fd, self._size)

            # Write header
            header = struct.pack(
                self.HEADER_FORMAT,
                SHM_MAGIC,
                SHM_VERSION,
                width,
                height,
                stride,
                1,  # BGRA8888
                0,  # frame_number
                0,  # timestamp
            )
            self._mmap[:self.HEADER_SIZE] = header

        except OSError as e:
            self.cleanup()
            raise RuntimeError(f"Failed to create shared memory: {e}")

    def open(self) -> None:
        """Open existing shared memory region (consumer side)."""
        try:
            self._fd = os.open(
                f"/dev/shm{self._name}",
                os.O_RDONLY
            )

            # Read header to get size
            self._mmap = mmap.mmap(self._fd, 0, access=mmap.ACCESS_READ)

            header = struct.unpack(
                self.HEADER_FORMAT,
                self._mmap[:self.HEADER_SIZE]
            )

            if header[0] != SHM_MAGIC:
                raise RuntimeError("Invalid shared memory magic")

            self._width = header[2]
            self._height = header[3]
            self._size = self.HEADER_SIZE + header[4] * header[3]

        except OSError as e:
            self.cleanup()
            raise RuntimeError(f"Failed to open shared memory: {e}")

    def write_frame(self, pixels: bytes, frame_number: int, timestamp_ns: int = 0) -> None:
        """Write a frame to shared memory (producer side).

        Args:
            pixels: Raw pixel data (BGRA format)
            frame_number: Frame sequence number
            timestamp_ns: Frame timestamp in nanoseconds
        """
        if not self._mmap:
            raise RuntimeError("Shared memory not initialized")

        with self._lock:
            # Update header
            header = struct.pack(
                self.HEADER_FORMAT,
                SHM_MAGIC,
                SHM_VERSION,
                self._width,
                self._height,
                self._width * 4,
                1,  # BGRA8888
                frame_number,
                timestamp_ns,
            )
            self._mmap[:self.HEADER_SIZE] = header

            # Write pixels
            pixel_offset = self.HEADER_SIZE
            expected_size = self._width * self._height * 4
            if len(pixels) >= expected_size:
                self._mmap[pixel_offset:pixel_offset + expected_size] = pixels[:expected_size]

    def read_frame(self) -> Optional[tuple]:
        """Read a frame from shared memory (consumer side).

        Returns:
            Tuple of (width, height, frame_number, timestamp_ns, pixels) or None
        """
        if not self._mmap:
            return None

        with self._lock:
            # Read header
            header = struct.unpack(
                self.HEADER_FORMAT,
                self._mmap[:self.HEADER_SIZE]
            )

            if header[0] != SHM_MAGIC:
                return None

            width = header[2]
            height = header[3]
            frame_number = header[6]
            timestamp_ns = header[7]

            # Skip if same frame
            if frame_number == self._last_frame_number:
                return None

            self._last_frame_number = frame_number

            # Read pixels
            pixel_offset = self.HEADER_SIZE
            pixel_size = width * height * 4
            pixels = bytes(self._mmap[pixel_offset:pixel_offset + pixel_size])

            return (width, height, frame_number, timestamp_ns, pixels)

    def get_dimensions(self) -> tuple:
        """Get current display dimensions."""
        return (self._width, self._height)

    def resize(self, width: int, height: int) -> None:
        """Resize the shared memory region."""
        self.cleanup()
        self.create(width, height)

    def set_frame_callback(self, callback: Callable) -> None:
        """Set callback for new frame notifications."""
        self._frame_callback = callback

    def cleanup(self) -> None:
        """Clean up shared memory resources."""
        if self._mmap:
            self._mmap.close()
            self._mmap = None

        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

        try:
            os.unlink(f"/dev/shm{self._name}")
        except FileNotFoundError:
            pass
