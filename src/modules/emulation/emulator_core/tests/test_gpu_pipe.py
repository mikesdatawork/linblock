"""
Tests for GPU command pipe transport.

Tests the GPU command transport layer for QEMU integration.
"""

import pytest
import os
import socket
import struct
import threading
import time
from ..internal.gpu_pipe import (
    GPUCommandPipe,
    GPUCommandPacket,
    TransportType,
    VirtioSerialTransport,
    UnixSocketTransport,
    create_gpu_pipe,
)


class TestGPUCommandPacket:
    """Tests for GPUCommandPacket dataclass."""

    def test_default_values(self):
        """Packet has sensible defaults."""
        packet = GPUCommandPacket()
        assert packet.sequence == 0
        assert packet.opcode == 0
        assert packet.size == 0
        assert packet.data == b""

    def test_create_with_values(self):
        """Packet accepts custom values."""
        packet = GPUCommandPacket(
            sequence=1,
            opcode=0x100,
            size=16,
            data=b"test data bytes!",
            timestamp_ns=1234567890,
        )
        assert packet.sequence == 1
        assert packet.opcode == 0x100
        assert packet.size == 16
        assert packet.data == b"test data bytes!"


class TestVirtioSerialTransport:
    """Tests for virtio-serial transport."""

    @pytest.fixture
    def socket_path(self, tmp_path):
        """Unique socket path for each test."""
        return str(tmp_path / f"gpu_pipe_{os.getpid()}.sock")

    def test_initial_state(self, socket_path):
        """Transport starts disconnected."""
        transport = VirtioSerialTransport(socket_path)
        assert not transport.is_connected()

    def test_connect_creates_socket(self, socket_path):
        """Connect creates server socket file."""
        transport = VirtioSerialTransport(socket_path)

        # Start connect in thread (blocks waiting for client)
        connect_result = [None]
        def do_connect():
            connect_result[0] = transport.connect()

        thread = threading.Thread(target=do_connect)
        thread.start()

        # Give server time to start
        time.sleep(0.1)

        # Check socket file exists
        assert os.path.exists(socket_path)

        # Connect as client to unblock server
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(socket_path)

        thread.join(timeout=2.0)

        assert connect_result[0] is True
        assert transport.is_connected()

        client.close()
        transport.disconnect()

    def test_disconnect_cleans_up(self, socket_path):
        """Disconnect closes socket and removes file."""
        transport = VirtioSerialTransport(socket_path)

        # Quick connect/disconnect
        def do_connect():
            transport.connect()

        thread = threading.Thread(target=do_connect)
        thread.start()

        time.sleep(0.1)
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        client.connect(socket_path)
        thread.join(timeout=2.0)

        # Now disconnect
        transport.disconnect()

        assert not transport.is_connected()
        assert not os.path.exists(socket_path)

        client.close()


class TestUnixSocketTransport:
    """Tests for Unix socket transport."""

    @pytest.fixture
    def socket_server(self, tmp_path):
        """Create a server socket for transport to connect to."""
        socket_path = str(tmp_path / f"test_server_{os.getpid()}.sock")
        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(socket_path)
        server.listen(1)
        server.settimeout(5.0)
        yield socket_path, server
        server.close()
        if os.path.exists(socket_path):
            os.unlink(socket_path)

    def test_initial_state(self):
        """Transport starts disconnected."""
        transport = UnixSocketTransport("/nonexistent")
        assert not transport.is_connected()

    def test_connect_to_server(self, socket_server):
        """Transport can connect to server."""
        socket_path, server = socket_server
        transport = UnixSocketTransport(socket_path)

        # Connect transport
        result = transport.connect()
        assert result is True
        assert transport.is_connected()

        # Server should have accepted connection
        client, _ = server.accept()
        client.close()
        transport.disconnect()

    def test_read_command(self, socket_server):
        """Transport can read command packets."""
        socket_path, server = socket_server
        transport = UnixSocketTransport(socket_path)
        transport.connect()

        client, _ = server.accept()

        # Send a command packet
        sequence = 1
        opcode = 0x100
        data = b"hello"
        header = struct.pack("<III", sequence, opcode, len(data))
        client.sendall(header + data)

        # Read command
        packet = transport.read_command()

        assert packet is not None
        assert packet.sequence == 1
        assert packet.opcode == 0x100
        assert packet.data == b"hello"

        client.close()
        transport.disconnect()

    def test_write_response(self, socket_server):
        """Transport can write response data."""
        socket_path, server = socket_server
        transport = UnixSocketTransport(socket_path)
        transport.connect()

        client, _ = server.accept()

        # Write response
        response = b"response data"
        result = transport.write_response(response)

        assert result is True

        # Server receives response
        received = client.recv(1024)
        assert received == response

        client.close()
        transport.disconnect()


class TestGPUCommandPipe:
    """Tests for high-level GPU command pipe."""

    def test_create_pipe(self):
        """Can create GPU command pipe."""
        pipe = GPUCommandPipe()
        assert not pipe.is_running()

    def test_factory_function_virtio(self):
        """Factory creates virtio transport."""
        pipe = create_gpu_pipe("virtio_serial", "/tmp/test.sock")
        assert pipe._transport_type == TransportType.VIRTIO_SERIAL

    def test_factory_function_unix(self):
        """Factory creates unix socket transport."""
        pipe = create_gpu_pipe("unix_socket", "/tmp/test.sock")
        assert pipe._transport_type == TransportType.UNIX_SOCKET

    def test_set_command_handler(self):
        """Can set command handler."""
        pipe = GPUCommandPipe()

        handler_called = [False]
        def handler(packet):
            handler_called[0] = True
            return b"ok"

        pipe.set_command_handler(handler)
        assert pipe._command_handler is not None

    def test_set_error_callback(self):
        """Can set error callback."""
        pipe = GPUCommandPipe()

        errors = []
        def on_error(msg):
            errors.append(msg)

        pipe.set_error_callback(on_error)
        pipe._report_error("test error")

        assert "test error" in errors

    def test_get_socket_path(self):
        """Returns configured socket path."""
        pipe = GPUCommandPipe(socket_path="/custom/path.sock")
        assert pipe.get_socket_path() == "/custom/path.sock"


class TestGPUPipeIntegration:
    """Integration tests with actual socket communication."""

    @pytest.fixture
    def socket_pair(self, tmp_path):
        """Create connected socket pair for testing."""
        socket_path = str(tmp_path / f"integration_{os.getpid()}.sock")

        server = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        server.bind(socket_path)
        server.listen(1)
        server.settimeout(5.0)

        # Connect client in thread
        client = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)

        def connect_client():
            time.sleep(0.1)
            client.connect(socket_path)

        thread = threading.Thread(target=connect_client)
        thread.start()

        conn, _ = server.accept()
        thread.join()

        yield client, conn

        client.close()
        conn.close()
        server.close()
        if os.path.exists(socket_path):
            os.unlink(socket_path)

    def test_bidirectional_communication(self, socket_pair):
        """Test sending commands and receiving responses."""
        client, server = socket_pair

        # Client sends command
        sequence = 42
        opcode = 0x200
        data = b"gpu command data"
        header = struct.pack("<III", sequence, opcode, len(data))
        client.sendall(header + data)

        # Server receives
        recv_header = server.recv(12)
        recv_seq, recv_op, recv_size = struct.unpack("<III", recv_header)
        recv_data = server.recv(recv_size)

        assert recv_seq == 42
        assert recv_op == 0x200
        assert recv_data == data

        # Server sends response
        response = struct.pack("<I", 0)  # Success code
        server.sendall(response)

        # Client receives response
        client_response = client.recv(4)
        result = struct.unpack("<I", client_response)[0]
        assert result == 0
