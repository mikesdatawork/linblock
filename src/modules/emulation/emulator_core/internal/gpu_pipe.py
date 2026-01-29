"""
GPU command transport pipe for QEMU.

Provides an interface for receiving GPU commands from the Android guest
and forwarding them to the GPU renderer.

This module abstracts the transport mechanism, supporting:
1. Virtio-serial (standard QEMU) - uses a virtio serial port
2. Goldfish pipe (Android QEMU) - uses the goldfish_pipe device
3. Unix socket (testing) - direct connection for testing

The transport choice depends on the QEMU configuration and available devices.
"""

import os
import socket
import struct
import threading
import time
from typing import Optional, Callable, List
from dataclasses import dataclass
from enum import Enum
from abc import ABC, abstractmethod


class TransportType(Enum):
    VIRTIO_SERIAL = "virtio_serial"
    GOLDFISH_PIPE = "goldfish_pipe"
    UNIX_SOCKET = "unix_socket"


@dataclass
class GPUCommandPacket:
    """A GPU command packet received from the guest."""
    sequence: int = 0
    opcode: int = 0
    size: int = 0
    data: bytes = b""
    timestamp_ns: int = 0


class GPUPipeTransport(ABC):
    """Abstract base class for GPU command transport."""

    @abstractmethod
    def connect(self) -> bool:
        """Establish connection to the guest."""
        pass

    @abstractmethod
    def disconnect(self) -> None:
        """Close connection."""
        pass

    @abstractmethod
    def read_command(self) -> Optional[GPUCommandPacket]:
        """Read the next GPU command from the guest."""
        pass

    @abstractmethod
    def write_response(self, data: bytes) -> bool:
        """Write a response back to the guest."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if transport is connected."""
        pass


class VirtioSerialTransport(GPUPipeTransport):
    """
    GPU command transport using virtio-serial.

    Uses a virtio serial port exposed by QEMU. The guest side
    writes GPU commands to /dev/virtio-ports/gpu_pipe and reads
    responses from the same port.

    QEMU command line:
        -device virtio-serial \
        -chardev socket,path=/tmp/gpu_pipe.sock,server=on,wait=off,id=gpu \
        -device virtserialport,chardev=gpu,name=gpu_pipe
    """

    def __init__(self, socket_path: str):
        self._socket_path = socket_path
        self._socket: Optional[socket.socket] = None
        self._client: Optional[socket.socket] = None
        self._connected = False
        self._lock = threading.Lock()

    def connect(self) -> bool:
        """Create server socket and wait for QEMU to connect."""
        try:
            # Remove existing socket file
            if os.path.exists(self._socket_path):
                os.unlink(self._socket_path)

            # Create server socket
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.bind(self._socket_path)
            self._socket.listen(1)
            self._socket.settimeout(30.0)  # Wait up to 30s for QEMU

            # Wait for QEMU to connect
            self._client, _ = self._socket.accept()
            self._client.settimeout(1.0)
            self._connected = True
            return True

        except Exception as e:
            print(f"VirtioSerialTransport connect failed: {e}")
            self._connected = False
            return False

    def disconnect(self) -> None:
        """Close all sockets."""
        self._connected = False

        if self._client:
            try:
                self._client.close()
            except Exception:
                pass
            self._client = None

        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

        if os.path.exists(self._socket_path):
            try:
                os.unlink(self._socket_path)
            except Exception:
                pass

    def read_command(self) -> Optional[GPUCommandPacket]:
        """Read a GPU command packet from the guest."""
        if not self._client or not self._connected:
            return None

        try:
            with self._lock:
                # Read packet header: sequence(4) + opcode(4) + size(4)
                header = self._recv_exact(12)
                if not header:
                    return None

                sequence, opcode, size = struct.unpack("<III", header)

                # Read packet data
                data = b""
                if size > 0:
                    data = self._recv_exact(size)
                    if data is None:
                        return None

                return GPUCommandPacket(
                    sequence=sequence,
                    opcode=opcode,
                    size=size,
                    data=data,
                    timestamp_ns=int(time.time() * 1e9),
                )

        except socket.timeout:
            return None
        except Exception:
            return None

    def _recv_exact(self, size: int) -> Optional[bytes]:
        """Receive exactly size bytes."""
        data = b""
        while len(data) < size:
            try:
                chunk = self._client.recv(size - len(data))
                if not chunk:
                    return None
                data += chunk
            except socket.timeout:
                return None
        return data

    def write_response(self, data: bytes) -> bool:
        """Write response data to the guest."""
        if not self._client or not self._connected:
            return False

        try:
            with self._lock:
                self._client.sendall(data)
                return True
        except Exception:
            return False

    def is_connected(self) -> bool:
        return self._connected


class UnixSocketTransport(GPUPipeTransport):
    """
    Direct Unix socket transport for testing.

    Connects directly to a GPU renderer socket for testing
    without QEMU in the path.
    """

    def __init__(self, socket_path: str):
        self._socket_path = socket_path
        self._socket: Optional[socket.socket] = None
        self._connected = False

    def connect(self) -> bool:
        try:
            self._socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
            self._socket.connect(self._socket_path)
            self._socket.settimeout(1.0)
            self._connected = True
            return True
        except Exception as e:
            print(f"UnixSocketTransport connect failed: {e}")
            return False

    def disconnect(self) -> None:
        self._connected = False
        if self._socket:
            try:
                self._socket.close()
            except Exception:
                pass
            self._socket = None

    def read_command(self) -> Optional[GPUCommandPacket]:
        if not self._socket or not self._connected:
            return None

        try:
            header = self._socket.recv(12)
            if len(header) < 12:
                return None

            sequence, opcode, size = struct.unpack("<III", header)

            data = b""
            if size > 0:
                data = self._socket.recv(size)

            return GPUCommandPacket(
                sequence=sequence,
                opcode=opcode,
                size=size,
                data=data,
                timestamp_ns=int(time.time() * 1e9),
            )

        except socket.timeout:
            return None
        except Exception:
            return None

    def write_response(self, data: bytes) -> bool:
        if not self._socket or not self._connected:
            return False

        try:
            self._socket.sendall(data)
            return True
        except Exception:
            return False

    def is_connected(self) -> bool:
        return self._connected


class GPUCommandPipe:
    """
    High-level GPU command pipe manager.

    Manages the transport layer and provides a simple interface
    for forwarding GPU commands to the renderer.
    """

    def __init__(
        self,
        transport_type: TransportType = TransportType.VIRTIO_SERIAL,
        socket_path: str = "/tmp/linblock_gpu_pipe.sock",
    ):
        self._transport_type = transport_type
        self._socket_path = socket_path
        self._transport: Optional[GPUPipeTransport] = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._command_handler: Optional[Callable[[GPUCommandPacket], bytes]] = None
        self._error_callback: Optional[Callable[[str], None]] = None

    def set_command_handler(self, handler: Callable[[GPUCommandPacket], bytes]) -> None:
        """Set handler for GPU commands.

        Handler receives a GPUCommandPacket and returns response bytes.
        """
        self._command_handler = handler

    def set_error_callback(self, callback: Callable[[str], None]) -> None:
        """Set callback for error notifications."""
        self._error_callback = callback

    def start(self) -> bool:
        """Start the GPU command pipe."""
        if self._running:
            return True

        # Create transport based on type
        if self._transport_type == TransportType.VIRTIO_SERIAL:
            self._transport = VirtioSerialTransport(self._socket_path)
        elif self._transport_type == TransportType.UNIX_SOCKET:
            self._transport = UnixSocketTransport(self._socket_path)
        else:
            # Goldfish pipe not implemented - would require custom QEMU
            self._report_error("Goldfish pipe transport not available")
            return False

        # Connect transport
        if not self._transport.connect():
            self._report_error("Failed to connect transport")
            return False

        # Start processing thread
        self._running = True
        self._thread = threading.Thread(target=self._process_commands, daemon=True)
        self._thread.start()

        return True

    def stop(self) -> None:
        """Stop the GPU command pipe."""
        self._running = False

        if self._transport:
            self._transport.disconnect()
            self._transport = None

        if self._thread:
            self._thread.join(timeout=5.0)
            self._thread = None

    def _process_commands(self) -> None:
        """Command processing loop."""
        while self._running and self._transport and self._transport.is_connected():
            try:
                # Read command
                packet = self._transport.read_command()
                if packet is None:
                    continue

                # Process command
                if self._command_handler:
                    response = self._command_handler(packet)
                    if response:
                        self._transport.write_response(response)

            except Exception as e:
                self._report_error(f"Command processing error: {e}")
                break

    def _report_error(self, message: str) -> None:
        """Report error via callback."""
        if self._error_callback:
            self._error_callback(message)

    def is_running(self) -> bool:
        return self._running

    def get_socket_path(self) -> str:
        return self._socket_path


def create_gpu_pipe(
    transport_type: str = "virtio_serial",
    socket_path: str = "/tmp/linblock_gpu_pipe.sock",
) -> GPUCommandPipe:
    """Factory function to create a GPU command pipe.

    Args:
        transport_type: "virtio_serial", "unix_socket", or "goldfish_pipe"
        socket_path: Path for the socket

    Returns:
        Configured GPUCommandPipe instance
    """
    type_map = {
        "virtio_serial": TransportType.VIRTIO_SERIAL,
        "unix_socket": TransportType.UNIX_SOCKET,
        "goldfish_pipe": TransportType.GOLDFISH_PIPE,
    }

    transport = type_map.get(transport_type, TransportType.VIRTIO_SERIAL)
    return GPUCommandPipe(transport_type=transport, socket_path=socket_path)
