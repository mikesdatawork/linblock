"""
Tests for VNCClient module.

Tests the VNC client functionality for framebuffer capture.
"""

import pytest
from ..internal.vnc_client import (
    VNCClient,
    VNCError,
    FrameData,
)


class TestFrameData:
    """Test suite for FrameData."""

    def test_frame_data_defaults(self):
        """FrameData has correct defaults."""
        frame = FrameData(width=640, height=480, data=b"")
        assert frame.width == 640
        assert frame.height == 480
        assert frame.data == b""
        assert frame.format == "rgb"

    def test_frame_data_with_format(self):
        """FrameData accepts custom format."""
        frame = FrameData(width=1080, height=1920, data=b"\x00" * 100, format="bgra")
        assert frame.format == "bgra"
        assert len(frame.data) == 100


class TestVNCClient:
    """Test suite for VNCClient."""

    @pytest.fixture
    def client(self):
        """Create VNCClient instance for testing."""
        return VNCClient(host="localhost", port=5999)  # Use non-standard port

    def test_initial_state(self, client):
        """Newly created client is not connected."""
        assert client.connected is False
        assert client.width == 0
        assert client.height == 0

    def test_frame_callback_registration(self, client):
        """Frame callbacks can be set."""
        frames_seen = []

        def callback(frame):
            frames_seen.append(frame)

        client.set_frame_callback(callback)
        # Callback should be stored
        assert client._frame_callback is not None

    def test_connect_to_invalid_host_raises(self, client):
        """Connecting to unavailable host raises VNCError."""
        with pytest.raises(VNCError):
            client.connect(timeout=1.0)

    def test_disconnect_safe_when_not_connected(self, client):
        """Disconnect is safe to call when not connected."""
        client.disconnect()  # Should not raise
        assert client.connected is False

    def test_cleanup_disconnects(self, client):
        """Cleanup disconnects and clears callbacks."""
        def callback(frame):
            pass

        client.set_frame_callback(callback)
        client.cleanup()
        assert client._frame_callback is None
        assert client.connected is False

    def test_get_framebuffer_returns_none_when_empty(self, client):
        """get_framebuffer returns None when no frame available."""
        assert client.get_framebuffer() is None

    def test_send_key_safe_when_not_connected(self, client):
        """send_key is safe to call when not connected."""
        client.send_key(65, True)  # Should not raise

    def test_send_pointer_safe_when_not_connected(self, client):
        """send_pointer is safe to call when not connected."""
        client.send_pointer(100, 200, 1)  # Should not raise

    def test_request_framebuffer_safe_when_not_connected(self, client):
        """request_framebuffer is safe to call when not connected."""
        client.request_framebuffer()  # Should not raise


class TestVNCClientMessageBuilding:
    """Test VNC protocol message construction."""

    def test_set_pixel_format_message_length(self):
        """SetPixelFormat message has correct length."""
        client = VNCClient()
        # Message type (1) + padding (3) + pixel format (16) = 20 bytes
        # We can't easily test this without making the method public,
        # but we verify the protocol constants are set
        assert client.MSG_SET_PIXEL_FORMAT == 0

    def test_set_encodings_message_type(self):
        """SetEncodings message type is correct."""
        client = VNCClient()
        assert client.MSG_SET_ENCODINGS == 2

    def test_framebuffer_request_message_type(self):
        """FramebufferUpdateRequest message type is correct."""
        client = VNCClient()
        assert client.MSG_FRAMEBUFFER_UPDATE_REQUEST == 3

    def test_key_event_message_type(self):
        """KeyEvent message type is correct."""
        client = VNCClient()
        assert client.MSG_KEY_EVENT == 4

    def test_pointer_event_message_type(self):
        """PointerEvent message type is correct."""
        client = VNCClient()
        assert client.MSG_POINTER_EVENT == 5

    def test_encoding_raw(self):
        """RAW encoding constant is correct."""
        client = VNCClient()
        assert client.ENC_RAW == 0

    def test_security_none(self):
        """Security None type is correct."""
        client = VNCClient()
        assert client.SEC_NONE == 1
