"""
GPU Renderer Process Manager.

Manages a sandboxed subprocess that hosts the libOpenglRender library.
Provides IPC via Unix sockets for GPU command transport.
"""

import os
import sys
import socket
import struct
import subprocess
import threading
import signal
import tempfile
import time
from typing import Optional, Callable, List, Tuple
from dataclasses import dataclass
from enum import Enum
import json


class ProcessState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class RendererProcessConfig:
    """Configuration for renderer process."""
    width: int = 1080
    height: int = 1920
    library_path: str = ""
    socket_path: str = ""
    shm_name: str = ""
    use_sandbox: bool = True
    log_path: str = ""


class RendererProcessError(Exception):
    """Raised when renderer process operation fails."""
    pass


class RendererProcess:
    """
    Manages a sandboxed GPU renderer subprocess.

    The renderer process hosts libOpenglRender and communicates via:
    - Unix socket for GPU commands (control plane)
    - Shared memory for framebuffer (data plane)
    """

    # Protocol message types
    MSG_INIT = 0x01
    MSG_PROCESS_COMMANDS = 0x02
    MSG_GET_FRAME = 0x03
    MSG_RESIZE = 0x04
    MSG_ROTATE = 0x05
    MSG_SHUTDOWN = 0xFF

    # Response codes
    RSP_OK = 0x00
    RSP_ERROR = 0x01

    def __init__(self, config: RendererProcessConfig):
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._socket: Optional[socket.socket] = None
        self._state = ProcessState.STOPPED
        self._state_callbacks: List[Callable[[ProcessState], None]] = []
        self._error_message = ""
        self._lock = threading.Lock()

        # Generate paths if not specified
        if not self._config.socket_path:
            self._config.socket_path = f"/tmp/linblock_renderer_{os.getpid()}.sock"
        if not self._config.shm_name:
            self._config.shm_name = f"/linblock_display_{os.getpid()}"

    @property
    def state(self) -> ProcessState:
        return self._state

    @property
    def error_message(self) -> str:
        return self._error_message

    def add_state_callback(self, callback: Callable[[ProcessState], None]) -> None:
        """Register callback for state changes."""
        self._state_callbacks.append(callback)

    def _set_state(self, state: ProcessState) -> None:
        """Update state and notify callbacks."""
        old_state = self._state
        self._state = state
        if old_state != state:
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception:
                    pass

    def _find_renderer_executable(self) -> str:
        """Find the renderer worker executable."""
        # Check common locations
        search_paths = [
            os.path.join(os.path.dirname(__file__), "renderer_worker.py"),
            os.path.expanduser("~/projects/linblock/src/modules/emulation/gpu_renderer/internal/renderer_worker.py"),
            "/usr/local/lib/linblock/renderer_worker.py",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        # Fallback to relative path
        return os.path.join(os.path.dirname(__file__), "renderer_worker.py")

    def _build_sandbox_command(self, worker_path: str) -> List[str]:
        """Build command with sandbox wrapper if enabled."""
        cmd = [sys.executable, worker_path]

        # Add configuration as JSON argument
        config_json = json.dumps({
            "width": self._config.width,
            "height": self._config.height,
            "library_path": self._config.library_path,
            "socket_path": self._config.socket_path,
            "shm_name": self._config.shm_name,
        })
        cmd.extend(["--config", config_json])

        if self._config.use_sandbox:
            # Check for sandbox tools
            if os.path.exists("/usr/bin/unshare"):
                # Use unshare for namespace isolation
                sandbox_cmd = [
                    "/usr/bin/unshare",
                    "--map-root-user",  # Map to root in namespace
                    "--net",            # New network namespace
                    "--",
                ]
                cmd = sandbox_cmd + cmd
            elif os.path.exists("/usr/bin/firejail"):
                # Use firejail as alternative
                sandbox_cmd = [
                    "/usr/bin/firejail",
                    "--quiet",
                    "--private-dev",
                    "--net=none",
                    "--",
                ]
                cmd = sandbox_cmd + cmd
            # If no sandbox tool, run without (log warning)

        return cmd

    def start(self) -> None:
        """Start the renderer process."""
        if self._state in (ProcessState.RUNNING, ProcessState.STARTING):
            raise RendererProcessError("Renderer already running")

        self._set_state(ProcessState.STARTING)

        try:
            # Remove existing socket
            if os.path.exists(self._config.socket_path):
                os.unlink(self._config.socket_path)

            # Create socket for IPC
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.bind(self._config.socket_path)
            self._socket.listen(1)
            self._socket.settimeout(10.0)  # Timeout for accept

            # Find and start worker process
            worker_path = self._find_renderer_executable()
            cmd = self._build_sandbox_command(worker_path)

            # Start process
            stderr_path = self._config.log_path or "/dev/null"
            stderr_file = open(stderr_path, "w") if stderr_path != "/dev/null" else subprocess.DEVNULL

            self._process = subprocess.Popen(
                cmd,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=stderr_file,
            )

            # Wait for worker to connect
            try:
                conn, addr = self._socket.accept()
                self._socket.close()
                self._socket = conn
                self._socket.settimeout(5.0)
            except socket.timeout:
                self._error_message = "Renderer worker failed to connect"
                self._set_state(ProcessState.ERROR)
                self.stop()
                raise RendererProcessError(self._error_message)

            # Send initialization message
            self._send_message(self.MSG_INIT, b"")
            response = self._recv_response()

            if response[0] != self.RSP_OK:
                self._error_message = f"Renderer init failed: {response[1].decode()}"
                self._set_state(ProcessState.ERROR)
                raise RendererProcessError(self._error_message)

            self._set_state(ProcessState.RUNNING)

        except Exception as e:
            self._error_message = str(e)
            self._set_state(ProcessState.ERROR)
            self.stop()
            raise RendererProcessError(self._error_message)

    def stop(self) -> None:
        """Stop the renderer process."""
        if self._state == ProcessState.STOPPED:
            return

        self._set_state(ProcessState.STOPPING)

        # Send shutdown message
        if self._socket:
            try:
                self._send_message(self.MSG_SHUTDOWN, b"")
            except Exception:
                pass

            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        # Terminate process
        if self._process:
            try:
                self._process.terminate()
                self._process.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self._process.kill()
                self._process.wait()
            except Exception:
                pass
            self._process = None

        # Clean up socket file
        if os.path.exists(self._config.socket_path):
            try:
                os.unlink(self._config.socket_path)
            except Exception:
                pass

        self._set_state(ProcessState.STOPPED)

    def _send_message(self, msg_type: int, data: bytes) -> None:
        """Send a message to the renderer process."""
        if not self._socket:
            raise RendererProcessError("Not connected")

        with self._lock:
            # Message format: type (1) + length (4) + data
            header = struct.pack("<BI", msg_type, len(data))
            self._socket.sendall(header + data)

    def _recv_response(self) -> Tuple[int, bytes]:
        """Receive a response from the renderer process."""
        if not self._socket:
            raise RendererProcessError("Not connected")

        with self._lock:
            # Response format: status (1) + length (4) + data
            header = self._socket.recv(5)
            if len(header) < 5:
                raise RendererProcessError("Connection closed")

            status, length = struct.unpack("<BI", header)

            data = b""
            while len(data) < length:
                chunk = self._socket.recv(min(length - len(data), 65536))
                if not chunk:
                    raise RendererProcessError("Connection closed")
                data += chunk

            return (status, data)

    def process_commands(self, command_buffer: bytes) -> None:
        """Send GPU commands to the renderer."""
        if self._state != ProcessState.RUNNING:
            raise RendererProcessError("Renderer not running")

        self._send_message(self.MSG_PROCESS_COMMANDS, command_buffer)
        response = self._recv_response()

        if response[0] != self.RSP_OK:
            raise RendererProcessError(f"Process commands failed: {response[1].decode()}")

    def resize(self, width: int, height: int) -> None:
        """Resize the rendering surface."""
        if self._state != ProcessState.RUNNING:
            raise RendererProcessError("Renderer not running")

        data = struct.pack("<II", width, height)
        self._send_message(self.MSG_RESIZE, data)
        response = self._recv_response()

        if response[0] != self.RSP_OK:
            raise RendererProcessError(f"Resize failed: {response[1].decode()}")

        self._config.width = width
        self._config.height = height

    def set_rotation(self, degrees: int) -> None:
        """Set display rotation."""
        if self._state != ProcessState.RUNNING:
            raise RendererProcessError("Renderer not running")

        data = struct.pack("<I", degrees)
        self._send_message(self.MSG_ROTATE, data)
        response = self._recv_response()

        if response[0] != self.RSP_OK:
            raise RendererProcessError(f"Set rotation failed: {response[1].decode()}")

    def get_shm_name(self) -> str:
        """Get shared memory name for display."""
        return self._config.shm_name

    def get_socket_path(self) -> str:
        """Get socket path for IPC."""
        return self._config.socket_path

    def is_running(self) -> bool:
        """Check if renderer process is running."""
        if self._process is None:
            return False
        return self._process.poll() is None

    def cleanup(self) -> None:
        """Clean up all resources."""
        self.stop()
        self._state_callbacks.clear()
