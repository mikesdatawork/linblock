#!/usr/bin/env python3
"""
GPU Renderer Worker Process.

This script runs in a sandboxed subprocess and hosts the libOpenglRender
library. It communicates with the main LinBlock process via Unix socket
and shared memory.

Usage:
    python renderer_worker.py --config '{"width": 1080, "height": 1920, ...}'
"""

import os
import sys
import socket
import struct
import signal
import argparse
import json
import ctypes
import mmap
from typing import Optional

# Add parent paths for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))


class RendererWorker:
    """
    Worker process that hosts libOpenglRender.

    Receives GPU commands via Unix socket and writes rendered frames
    to shared memory.
    """

    # Message types (must match renderer_process.py)
    MSG_INIT = 0x01
    MSG_PROCESS_COMMANDS = 0x02
    MSG_GET_FRAME = 0x03
    MSG_RESIZE = 0x04
    MSG_ROTATE = 0x05
    MSG_SHUTDOWN = 0xFF

    # Response codes
    RSP_OK = 0x00
    RSP_ERROR = 0x01

    # Shared memory header
    SHM_MAGIC = 0x4C424B44  # "LBKD"
    SHM_VERSION = 1
    SHM_HEADER_FORMAT = "<IIIIIIQQ"  # magic, version, w, h, stride, format, frame_num, timestamp
    SHM_HEADER_SIZE = struct.calcsize(SHM_HEADER_FORMAT)

    def __init__(self, config: dict):
        self._config = config
        self._width = config.get("width", 1080)
        self._height = config.get("height", 1920)
        self._library_path = config.get("library_path", "")
        self._socket_path = config.get("socket_path", "")
        self._shm_name = config.get("shm_name", "")

        self._socket: Optional[socket.socket] = None
        self._lib = None
        self._context = None
        self._shm_fd: Optional[int] = None
        self._shm_mmap: Optional[mmap.mmap] = None
        self._frame_number = 0
        self._running = True
        self._use_stub = True  # Use stub if native library not available

    def _load_native_library(self) -> bool:
        """Attempt to load libOpenglRender."""
        if not self._library_path:
            return False

        if not os.path.exists(self._library_path):
            return False

        try:
            self._lib = ctypes.CDLL(self._library_path)

            # Set up function signatures
            self._lib.lb_renderer_init.argtypes = [
                ctypes.c_uint32, ctypes.c_uint32,
                ctypes.POINTER(ctypes.c_void_p)
            ]
            self._lib.lb_renderer_init.restype = ctypes.c_int

            self._lib.lb_renderer_process_commands.argtypes = [
                ctypes.c_void_p, ctypes.c_void_p, ctypes.c_size_t
            ]
            self._lib.lb_renderer_process_commands.restype = ctypes.c_int

            self._lib.lb_renderer_cleanup.argtypes = [ctypes.c_void_p]
            self._lib.lb_renderer_cleanup.restype = None

            return True

        except (OSError, AttributeError) as e:
            print(f"Failed to load native library: {e}", file=sys.stderr)
            return False

    def _init_native_renderer(self) -> bool:
        """Initialize the native renderer."""
        if not self._lib:
            return False

        try:
            context = ctypes.c_void_p()
            result = self._lib.lb_renderer_init(
                self._width, self._height,
                ctypes.byref(context)
            )

            if result != 0:
                return False

            self._context = context
            return True

        except Exception as e:
            print(f"Native renderer init failed: {e}", file=sys.stderr)
            return False

    def _setup_shared_memory(self) -> None:
        """Set up shared memory for framebuffer."""
        stride = self._width * 4  # BGRA
        pixel_size = stride * self._height
        total_size = self.SHM_HEADER_SIZE + pixel_size

        # Create POSIX shared memory
        shm_path = f"/dev/shm{self._shm_name}"

        try:
            # Remove existing
            if os.path.exists(shm_path):
                os.unlink(shm_path)

            self._shm_fd = os.open(shm_path, os.O_CREAT | os.O_RDWR, 0o600)
            os.ftruncate(self._shm_fd, total_size)

            self._shm_mmap = mmap.mmap(self._shm_fd, total_size)

            # Write initial header
            header = struct.pack(
                self.SHM_HEADER_FORMAT,
                self.SHM_MAGIC,
                self.SHM_VERSION,
                self._width,
                self._height,
                stride,
                1,  # BGRA8888
                0,  # frame_number
                0,  # timestamp
            )
            self._shm_mmap[:self.SHM_HEADER_SIZE] = header

        except OSError as e:
            print(f"Failed to set up shared memory: {e}", file=sys.stderr)
            raise

    def _write_frame(self, pixels: bytes) -> None:
        """Write a frame to shared memory."""
        if not self._shm_mmap:
            return

        import time
        self._frame_number += 1
        timestamp_ns = int(time.time() * 1e9)

        # Update header
        stride = self._width * 4
        header = struct.pack(
            self.SHM_HEADER_FORMAT,
            self.SHM_MAGIC,
            self.SHM_VERSION,
            self._width,
            self._height,
            stride,
            1,  # BGRA8888
            self._frame_number,
            timestamp_ns,
        )
        self._shm_mmap[:self.SHM_HEADER_SIZE] = header

        # Write pixels
        expected_size = self._width * self._height * 4
        pixel_data = pixels[:expected_size] if len(pixels) >= expected_size else pixels
        self._shm_mmap[self.SHM_HEADER_SIZE:self.SHM_HEADER_SIZE + len(pixel_data)] = pixel_data

    def _generate_stub_frame(self) -> bytes:
        """Generate a stub test frame (gradient pattern)."""
        w, h = self._width, self._height
        data = bytearray(w * h * 4)

        # Animated gradient based on frame number
        offset = (self._frame_number * 2) % 256

        for y in range(h):
            for x in range(w):
                idx = (y * w + x) * 4
                data[idx] = ((x * 255 // w) + offset) & 0xFF      # B
                data[idx + 1] = ((y * 255 // h) + offset) & 0xFF  # G
                data[idx + 2] = 128                                # R
                data[idx + 3] = 255                                # A

        return bytes(data)

    def _connect_to_parent(self) -> None:
        """Connect to parent process via Unix socket."""
        self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self._socket.connect(self._socket_path)
        self._socket.settimeout(30.0)

    def _recv_message(self) -> tuple:
        """Receive a message from parent."""
        # Message format: type (1) + length (4) + data
        header = self._socket.recv(5)
        if len(header) < 5:
            raise ConnectionError("Connection closed")

        msg_type, length = struct.unpack("<BI", header)

        data = b""
        while len(data) < length:
            chunk = self._socket.recv(min(length - len(data), 65536))
            if not chunk:
                raise ConnectionError("Connection closed")
            data += chunk

        return (msg_type, data)

    def _send_response(self, status: int, data: bytes = b"") -> None:
        """Send a response to parent."""
        # Response format: status (1) + length (4) + data
        header = struct.pack("<BI", status, len(data))
        self._socket.sendall(header + data)

    def _handle_init(self, data: bytes) -> None:
        """Handle initialization message."""
        try:
            # Try native library first
            if self._load_native_library():
                if self._init_native_renderer():
                    self._use_stub = False
                    print("Using native GPU renderer", file=sys.stderr)
                else:
                    self._use_stub = True
                    print("Native init failed, using stub renderer", file=sys.stderr)
            else:
                self._use_stub = True
                print("Native library not available, using stub renderer", file=sys.stderr)

            # Set up shared memory
            self._setup_shared_memory()

            # Generate initial frame
            if self._use_stub:
                pixels = self._generate_stub_frame()
                self._write_frame(pixels)

            self._send_response(self.RSP_OK)

        except Exception as e:
            self._send_response(self.RSP_ERROR, str(e).encode())

    def _handle_process_commands(self, data: bytes) -> None:
        """Handle GPU command processing."""
        try:
            if self._use_stub:
                # Stub: generate new frame
                pixels = self._generate_stub_frame()
                self._write_frame(pixels)
            else:
                # Native: process actual GPU commands
                if self._lib and self._context:
                    cmd_ptr = ctypes.c_char_p(data)
                    result = self._lib.lb_renderer_process_commands(
                        self._context, cmd_ptr, len(data)
                    )
                    if result != 0:
                        raise RuntimeError(f"GPU command processing failed: {result}")

                    # TODO: Get frame from native renderer and write to shm

            self._send_response(self.RSP_OK)

        except Exception as e:
            self._send_response(self.RSP_ERROR, str(e).encode())

    def _handle_resize(self, data: bytes) -> None:
        """Handle resize message."""
        try:
            width, height = struct.unpack("<II", data)
            self._width = width
            self._height = height

            # Recreate shared memory with new size
            if self._shm_mmap:
                self._shm_mmap.close()
            if self._shm_fd:
                os.close(self._shm_fd)

            self._setup_shared_memory()

            self._send_response(self.RSP_OK)

        except Exception as e:
            self._send_response(self.RSP_ERROR, str(e).encode())

    def _handle_rotate(self, data: bytes) -> None:
        """Handle rotation message."""
        try:
            degrees = struct.unpack("<I", data)[0]
            if degrees not in (0, 90, 180, 270):
                raise ValueError(f"Invalid rotation: {degrees}")

            # TODO: Apply rotation to renderer

            self._send_response(self.RSP_OK)

        except Exception as e:
            self._send_response(self.RSP_ERROR, str(e).encode())

    def _enter_sandbox(self) -> None:
        """Enter sandbox mode before processing any commands."""
        try:
            from .sandbox import enter_sandbox, SandboxConfig

            config = SandboxConfig(
                max_memory_bytes=512 * 1024 * 1024,  # 512 MB
                max_open_files=64,
                max_processes=1,
            )
            enter_sandbox(config)
            print("Entered sandbox mode", file=sys.stderr)

        except Exception as e:
            print(f"Warning: Failed to enter sandbox: {e}", file=sys.stderr)

    def run(self) -> None:
        """Main worker loop."""
        # Set up signal handlers
        signal.signal(signal.SIGTERM, lambda s, f: setattr(self, '_running', False))
        signal.signal(signal.SIGINT, lambda s, f: setattr(self, '_running', False))

        try:
            self._connect_to_parent()

            # Enter sandbox after connecting but before processing commands
            self._enter_sandbox()

            while self._running:
                try:
                    msg_type, data = self._recv_message()

                    if msg_type == self.MSG_INIT:
                        self._handle_init(data)
                    elif msg_type == self.MSG_PROCESS_COMMANDS:
                        self._handle_process_commands(data)
                    elif msg_type == self.MSG_RESIZE:
                        self._handle_resize(data)
                    elif msg_type == self.MSG_ROTATE:
                        self._handle_rotate(data)
                    elif msg_type == self.MSG_SHUTDOWN:
                        self._running = False
                        self._send_response(self.RSP_OK)
                        break
                    else:
                        self._send_response(self.RSP_ERROR, b"Unknown message type")

                except socket.timeout:
                    continue
                except ConnectionError:
                    break

        except Exception as e:
            print(f"Worker error: {e}", file=sys.stderr)

        finally:
            self._cleanup()

    def _cleanup(self) -> None:
        """Clean up resources."""
        if self._lib and self._context:
            try:
                self._lib.lb_renderer_cleanup(self._context)
            except Exception:
                pass

        if self._shm_mmap:
            try:
                self._shm_mmap.close()
            except Exception:
                pass

        if self._shm_fd:
            try:
                os.close(self._shm_fd)
            except Exception:
                pass

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass

        # Remove shared memory file
        shm_path = f"/dev/shm{self._shm_name}"
        if os.path.exists(shm_path):
            try:
                os.unlink(shm_path)
            except Exception:
                pass


def main():
    parser = argparse.ArgumentParser(description="GPU Renderer Worker")
    parser.add_argument("--config", type=str, required=True,
                        help="JSON configuration")
    args = parser.parse_args()

    config = json.loads(args.config)
    worker = RendererWorker(config)
    worker.run()


if __name__ == "__main__":
    main()
