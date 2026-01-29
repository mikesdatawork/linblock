"""
Tests for GTK3 integration with GPU renderer.

Tests the SharedMemoryFrameSource and GPURendererDisplayBridge classes.
"""

import pytest
import os
import time
import threading
from unittest.mock import Mock, MagicMock, patch


class TestSharedMemoryFrameSourceUnit:
    """Unit tests for SharedMemoryFrameSource without GTK."""

    def test_init_default_fps(self):
        """Frame source initializes with default 60 FPS."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            # Import with mocked GTK
            from src.modules.emulation.gpu_renderer.gtk_integration import SharedMemoryFrameSource
            source = SharedMemoryFrameSource("/test_shm")
            assert source._target_fps == 60
            assert source._poll_interval_ms == 16  # ~60fps

    def test_init_custom_fps(self):
        """Frame source accepts custom FPS."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer.gtk_integration import SharedMemoryFrameSource
            source = SharedMemoryFrameSource("/test_shm", target_fps=30)
            assert source._target_fps == 30
            assert source._poll_interval_ms == 33  # ~30fps

    def test_get_shm_name(self):
        """Frame source returns shm name."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer.gtk_integration import SharedMemoryFrameSource
            source = SharedMemoryFrameSource("/linblock_display_123")
            assert source.get_shm_name() == "/linblock_display_123"

    def test_initial_state(self):
        """Frame source starts not running."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer.gtk_integration import SharedMemoryFrameSource
            source = SharedMemoryFrameSource("/test_shm")
            assert not source.is_running()
            assert source.get_fps() == 0.0


class TestGPURendererDisplayBridgeUnit:
    """Unit tests for GPURendererDisplayBridge without GTK."""

    def test_create_bridge(self):
        """Can create display bridge."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer.gtk_integration import GPURendererDisplayBridge
            bridge = GPURendererDisplayBridge()
            assert not bridge.is_running()
            assert bridge.get_fps() == 0.0

    def test_connect_extracts_shm_name(self):
        """Connect extracts shm_name from renderer."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer.gtk_integration import GPURendererDisplayBridge

            # Mock renderer with get_shm_name method
            renderer = Mock()
            # Disable _process attribute so it falls through to get_shm_name
            renderer._process = None
            renderer.get_shm_name.return_value = "/test_shm_456"

            widget = Mock()

            bridge = GPURendererDisplayBridge()
            bridge.connect(renderer, widget)

            assert bridge._shm_name == "/test_shm_456"


class TestSharedMemoryIntegration:
    """Integration tests with actual shared memory (no GTK)."""

    @pytest.fixture
    def shm_display(self):
        """Create shared memory display for testing."""
        from src.modules.emulation.gpu_renderer.internal.shm_display import SharedMemoryDisplay
        name = f"/test_gtk_int_{os.getpid()}"
        shm = SharedMemoryDisplay(name)
        shm.create(100, 100)
        yield shm
        shm.cleanup()

    def test_shared_memory_polling_logic(self, shm_display):
        """Test frame reading logic without GTK main loop."""
        from src.modules.emulation.gpu_renderer.internal.shm_display import SharedMemoryDisplay

        # Write a test frame
        pixels = bytes([i % 256 for i in range(100 * 100 * 4)])
        shm_display.write_frame(pixels, 1, 1000)

        # Read frame from consumer
        consumer = SharedMemoryDisplay(shm_display._name)
        consumer.open()

        result = consumer.read_frame()
        assert result is not None
        width, height, frame_num, timestamp, read_pixels = result
        assert width == 100
        assert height == 100
        assert frame_num == 1
        assert read_pixels == pixels

        consumer.cleanup()

    def test_frame_skip_when_same_number(self, shm_display):
        """Consumer skips frames with same number."""
        from src.modules.emulation.gpu_renderer.internal.shm_display import SharedMemoryDisplay

        # Write frame
        pixels = bytes([0] * 100 * 100 * 4)
        shm_display.write_frame(pixels, 1, 1000)

        # Consumer reads
        consumer = SharedMemoryDisplay(shm_display._name)
        consumer.open()

        result1 = consumer.read_frame()
        assert result1 is not None

        # Second read of same frame returns None
        result2 = consumer.read_frame()
        assert result2 is None

        # Write new frame
        shm_display.write_frame(pixels, 2, 2000)

        # Now we get the new frame
        result3 = consumer.read_frame()
        assert result3 is not None
        assert result3[2] == 2  # frame_num

        consumer.cleanup()


class TestFactoryFunction:
    """Test factory function for GTK integration."""

    def test_get_gtk_integration_returns_classes(self):
        """Factory returns GTK integration classes."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer import get_gtk_integration
            SharedMemoryFrameSource, GPURendererDisplayBridge, create_display_bridge = get_gtk_integration()

            assert SharedMemoryFrameSource is not None
            assert GPURendererDisplayBridge is not None
            assert callable(create_display_bridge)

    def test_create_display_bridge_factory(self):
        """Factory function creates bridge instance."""
        with patch.dict('sys.modules', {'gi': MagicMock(), 'gi.repository': MagicMock()}):
            from src.modules.emulation.gpu_renderer import get_gtk_integration
            _, _, create_display_bridge = get_gtk_integration()

            bridge = create_display_bridge()
            assert bridge is not None


class TestRendererIntegration:
    """Test GPU renderer with GTK integration hooks."""

    def test_stub_renderer_has_get_shm_name(self):
        """Stub renderer has get_shm_name method."""
        from src.modules.emulation.gpu_renderer import StubGPURenderer

        renderer = StubGPURenderer({"width": 100, "height": 100})
        assert hasattr(renderer, 'get_shm_name')
        assert renderer.get_shm_name() is None  # Stub returns None

    def test_native_renderer_has_get_shm_name(self):
        """Native renderer has get_shm_name method."""
        from src.modules.emulation.gpu_renderer import NativeGPURenderer

        renderer = NativeGPURenderer({"width": 100, "height": 100})
        assert hasattr(renderer, 'get_shm_name')
        # Before initialization, returns None
        assert renderer.get_shm_name() is None
