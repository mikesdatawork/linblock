"""
Simple VNC client for receiving framebuffer from QEMU.

Implements the RFB (Remote Framebuffer) protocol to receive
display updates from the QEMU VNC server.
"""

import socket
import struct
import threading
import time
from typing import Optional, Callable, Tuple
from dataclasses import dataclass


@dataclass
class FrameData:
    """Container for framebuffer data."""
    width: int
    height: int
    data: bytes  # Raw RGB or RGBA pixel data
    format: str = "rgb"  # rgb, rgba, bgr, bgra


class VNCError(Exception):
    """Raised when VNC operation fails."""
    pass


class VNCClient:
    """
    Minimal VNC client for QEMU framebuffer capture.

    Connects to a VNC server and receives framebuffer updates.
    Only implements the subset of RFB protocol needed for display.
    """

    # RFB protocol constants
    RFB_VERSION = b"RFB 003.008\n"

    # Security types
    SEC_NONE = 1
    SEC_VNC_AUTH = 2

    # Client messages
    MSG_SET_PIXEL_FORMAT = 0
    MSG_SET_ENCODINGS = 2
    MSG_FRAMEBUFFER_UPDATE_REQUEST = 3
    MSG_KEY_EVENT = 4
    MSG_POINTER_EVENT = 5

    # Server messages
    MSG_FRAMEBUFFER_UPDATE = 0

    # Encodings
    ENC_RAW = 0
    ENC_DESKTOP_SIZE = -223

    def __init__(self, host: str = "localhost", port: int = 5900):
        self._host = host
        self._port = port
        self._socket: Optional[socket.socket] = None
        self._connected = False
        self._width = 0
        self._height = 0
        self._framebuffer: Optional[bytes] = None
        self._frame_callback: Optional[Callable[[FrameData], None]] = None
        self._receiver_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self._connected

    @property
    def width(self) -> int:
        return self._width

    @property
    def height(self) -> int:
        return self._height

    def set_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        """Set callback for framebuffer updates."""
        self._frame_callback = callback

    def connect(self, timeout: float = 10.0) -> None:
        """Connect to VNC server and perform handshake."""
        try:
            self._socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self._socket.settimeout(timeout)
            self._socket.connect((self._host, self._port))

            # Protocol version exchange
            server_version = self._socket.recv(12)
            if not server_version.startswith(b"RFB "):
                raise VNCError(f"Invalid server version: {server_version}")

            self._socket.send(self.RFB_VERSION)

            # Security handshake
            num_sec_types = struct.unpack("!B", self._socket.recv(1))[0]
            if num_sec_types == 0:
                # Server error
                reason_len = struct.unpack("!I", self._socket.recv(4))[0]
                reason = self._socket.recv(reason_len).decode()
                raise VNCError(f"Server rejected connection: {reason}")

            sec_types = self._socket.recv(num_sec_types)
            if self.SEC_NONE in sec_types:
                self._socket.send(bytes([self.SEC_NONE]))
            else:
                raise VNCError("Server requires authentication (not supported)")

            # Check security result
            result = struct.unpack("!I", self._socket.recv(4))[0]
            if result != 0:
                raise VNCError("Security handshake failed")

            # Send client init (shared flag = 1)
            self._socket.send(bytes([1]))

            # Receive server init
            init_data = self._socket.recv(24)
            self._width, self._height = struct.unpack("!HH", init_data[:4])

            # Skip pixel format (16 bytes) and name length
            name_len = struct.unpack("!I", init_data[20:24])[0]
            self._socket.recv(name_len)  # Skip server name

            # Set pixel format to 32-bit RGBX
            self._set_pixel_format()

            # Set encodings (RAW only for simplicity)
            self._set_encodings()

            self._connected = True

            # Start receiver thread
            self._stop_event.clear()
            self._receiver_thread = threading.Thread(
                target=self._receive_loop,
                daemon=True
            )
            self._receiver_thread.start()

        except socket.error as e:
            self.disconnect()
            raise VNCError(f"Connection failed: {e}")

    def _set_pixel_format(self) -> None:
        """Set pixel format to 32-bit RGB."""
        # MessageType + padding + PixelFormat
        msg = struct.pack(
            "!BBBBBBBBHHHBBBxxx",
            self.MSG_SET_PIXEL_FORMAT,  # message type
            0, 0, 0,  # padding
            32,  # bits per pixel
            24,  # depth
            0,   # big endian (0 = little)
            1,   # true color
            255, 255, 255,  # max RGB values
            16, 8, 0,  # RGB shifts
        )
        self._socket.send(msg)

    def _set_encodings(self) -> None:
        """Set supported encodings."""
        encodings = [self.ENC_RAW, self.ENC_DESKTOP_SIZE]
        msg = struct.pack(
            "!BBH",
            self.MSG_SET_ENCODINGS,
            0,  # padding
            len(encodings)
        )
        for enc in encodings:
            msg += struct.pack("!i", enc)
        self._socket.send(msg)

    def request_framebuffer(self, incremental: bool = False) -> None:
        """Request a framebuffer update from server."""
        if not self._connected or not self._socket:
            return

        msg = struct.pack(
            "!BBHHHH",
            self.MSG_FRAMEBUFFER_UPDATE_REQUEST,
            1 if incremental else 0,
            0, 0,  # x, y
            self._width, self._height
        )
        try:
            self._socket.send(msg)
        except socket.error:
            pass

    def _receive_loop(self) -> None:
        """Background thread to receive framebuffer updates."""
        while not self._stop_event.is_set() and self._connected:
            try:
                # Request full update initially, then incremental
                self.request_framebuffer(incremental=False)

                # Wait for response
                self._socket.settimeout(1.0)
                try:
                    msg_type = self._socket.recv(1)
                    if not msg_type:
                        break

                    msg_type = struct.unpack("!B", msg_type)[0]

                    if msg_type == self.MSG_FRAMEBUFFER_UPDATE:
                        self._handle_framebuffer_update()

                except socket.timeout:
                    continue

                time.sleep(0.033)  # ~30 FPS

            except socket.error:
                break
            except Exception:
                break

    def _handle_framebuffer_update(self) -> None:
        """Handle framebuffer update message."""
        try:
            # Read header: padding + num rectangles
            header = self._socket.recv(3)
            num_rects = struct.unpack("!xH", header)[0]

            for _ in range(num_rects):
                # Rectangle header
                rect_header = self._socket.recv(12)
                x, y, w, h, encoding = struct.unpack("!HHHHi", rect_header)

                if encoding == self.ENC_RAW:
                    # Raw pixel data (4 bytes per pixel)
                    data_size = w * h * 4
                    data = b""
                    while len(data) < data_size:
                        chunk = self._socket.recv(min(data_size - len(data), 65536))
                        if not chunk:
                            break
                        data += chunk

                    if len(data) == data_size:
                        # Update framebuffer
                        with self._lock:
                            if x == 0 and y == 0 and w == self._width and h == self._height:
                                # Full frame update
                                self._framebuffer = data
                            else:
                                # Partial update - merge into existing framebuffer
                                if self._framebuffer is None:
                                    self._framebuffer = bytes(self._width * self._height * 4)
                                # Simple approach: just use full framebuffer updates
                                self._framebuffer = data

                        # Notify callback
                        if self._frame_callback:
                            frame = FrameData(
                                width=w,
                                height=h,
                                data=data,
                                format="bgra"  # VNC typically uses BGRA
                            )
                            try:
                                self._frame_callback(frame)
                            except Exception:
                                pass

                elif encoding == self.ENC_DESKTOP_SIZE:
                    # Desktop resize
                    self._width = w
                    self._height = h

        except socket.error:
            pass

    def send_key(self, keycode: int, down: bool) -> None:
        """Send a key event to the server."""
        if not self._connected or not self._socket:
            return

        msg = struct.pack(
            "!BBxxI",
            self.MSG_KEY_EVENT,
            1 if down else 0,
            keycode
        )
        try:
            self._socket.send(msg)
        except socket.error:
            pass

    def send_pointer(self, x: int, y: int, buttons: int) -> None:
        """Send a pointer/mouse event to the server."""
        if not self._connected or not self._socket:
            return

        msg = struct.pack(
            "!BBHH",
            self.MSG_POINTER_EVENT,
            buttons,
            x, y
        )
        try:
            self._socket.send(msg)
        except socket.error:
            pass

    def get_framebuffer(self) -> Optional[FrameData]:
        """Get the current framebuffer data."""
        with self._lock:
            if self._framebuffer is None:
                return None
            return FrameData(
                width=self._width,
                height=self._height,
                data=self._framebuffer,
                format="bgra"
            )

    def disconnect(self) -> None:
        """Disconnect from VNC server."""
        self._stop_event.set()
        self._connected = False

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        if self._receiver_thread:
            self._receiver_thread.join(timeout=2)
            self._receiver_thread = None

    def cleanup(self) -> None:
        """Clean up all resources."""
        self.disconnect()
        self._frame_callback = None
