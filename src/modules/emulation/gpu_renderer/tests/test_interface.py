"""
Interface tests for gpu_renderer.

Tests the GPU renderer interface using the stub backend.
"""

import pytest
from ..interface import (
    GPURendererInterface,
    StubGPURenderer,
    create_interface,
    GPURendererError,
    RendererInitError,
    RendererNotReadyError,
    RendererState,
    FrameData,
    FrameFormat,
)


class TestGPURendererInterface:
    """Test suite for GPURendererInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration using stub backend."""
        return {
            "width": 1080,
            "height": 1920,
            "backend": "stub",
        }

    @pytest.fixture
    def renderer(self, config):
        """Create renderer instance for testing."""
        return create_interface(config)

    def test_create_with_config(self, config):
        """Interface creates successfully with explicit config."""
        renderer = create_interface(config)
        assert renderer is not None
        assert isinstance(renderer, GPURendererInterface)

    def test_create_with_stub_backend(self):
        """Stub backend creates successfully."""
        renderer = create_interface({"backend": "stub"})
        assert isinstance(renderer, StubGPURenderer)

    def test_initial_state_uninitialized(self, renderer):
        """Newly created renderer is in UNINITIALIZED state."""
        assert renderer.get_state() == RendererState.UNINITIALIZED

    def test_initialize_transitions_to_ready(self, renderer):
        """Initialize transitions to READY state."""
        renderer.initialize()
        assert renderer.get_state() == RendererState.READY

    def test_process_commands_requires_init(self, renderer):
        """Processing commands before init raises error."""
        with pytest.raises(RendererNotReadyError):
            renderer.process_commands(b"\x00" * 100)

    def test_process_commands_after_init(self, renderer):
        """Processing commands works after init."""
        renderer.initialize()
        renderer.process_commands(b"\x00" * 100)
        # Should not raise

    def test_get_frame_returns_none_before_init(self, renderer):
        """get_frame returns None before initialization."""
        assert renderer.get_frame() is None

    def test_get_frame_returns_data_after_init(self, renderer):
        """get_frame returns FrameData after initialization."""
        renderer.initialize()
        frame = renderer.get_frame()
        assert frame is not None
        assert isinstance(frame, FrameData)
        assert frame.width == 1080
        assert frame.height == 1920

    def test_frame_has_correct_format(self, renderer):
        """Frame has correct pixel format."""
        renderer.initialize()
        frame = renderer.get_frame()
        assert frame.format == FrameFormat.BGRA8888
        assert frame.stride == frame.width * 4

    def test_frame_has_pixel_data(self, renderer):
        """Frame contains pixel data."""
        renderer.initialize()
        frame = renderer.get_frame()
        expected_size = frame.width * frame.height * 4
        assert len(frame.data) == expected_size

    def test_resize_changes_dimensions(self, renderer):
        """Resize updates frame dimensions."""
        renderer.initialize()
        renderer.resize(720, 1280)
        frame = renderer.get_frame()
        assert frame.width == 720
        assert frame.height == 1280

    def test_set_rotation_valid_values(self, renderer):
        """set_rotation accepts valid rotation values."""
        renderer.initialize()
        for rotation in [0, 90, 180, 270]:
            renderer.set_rotation(rotation)  # Should not raise

    def test_set_rotation_invalid_raises(self, renderer):
        """set_rotation raises for invalid values."""
        renderer.initialize()
        with pytest.raises(GPURendererError):
            renderer.set_rotation(45)

    def test_get_info_returns_info(self, renderer):
        """get_info returns RendererInfo."""
        info = renderer.get_info()
        assert info.state == RendererState.UNINITIALIZED

        renderer.initialize()
        info = renderer.get_info()
        assert info.state == RendererState.READY
        assert info.width == 1080
        assert info.height == 1920

    def test_frame_callback_registration(self, renderer):
        """Frame callbacks can be registered and called."""
        frames_received = []

        def callback(frame):
            frames_received.append(frame)

        renderer.initialize()
        renderer.add_frame_callback(callback)
        renderer.get_frame()

        assert len(frames_received) == 1
        assert isinstance(frames_received[0], FrameData)

    def test_frame_callback_removal(self, renderer):
        """Frame callbacks can be removed."""
        frames_received = []

        def callback(frame):
            frames_received.append(frame)

        renderer.initialize()
        renderer.add_frame_callback(callback)
        renderer.get_frame()
        assert len(frames_received) == 1

        renderer.remove_frame_callback(callback)
        renderer.get_frame()
        assert len(frames_received) == 1  # No new frame added

    def test_cleanup_resets_state(self, renderer):
        """Cleanup resets renderer to uninitialized."""
        renderer.initialize()
        assert renderer.get_state() == RendererState.READY

        renderer.cleanup()
        assert renderer.get_state() == RendererState.UNINITIALIZED

    def test_frame_number_increments(self, renderer):
        """Frame number increments with each frame."""
        renderer.initialize()

        frame1 = renderer.get_frame()
        renderer.process_commands(b"\x00")
        frame2 = renderer.get_frame()

        assert frame2.frame_number > frame1.frame_number


class TestStubGPURenderer:
    """Tests specific to stub implementation."""

    def test_generates_gradient_pattern(self):
        """Stub generates a gradient test pattern."""
        renderer = StubGPURenderer({"width": 100, "height": 100})
        renderer.initialize()
        frame = renderer.get_frame()

        # Check that pixels vary (gradient pattern)
        pixels = frame.data
        # First pixel
        b1, g1, r1, a1 = pixels[0:4]
        # Last pixel
        last_idx = (99 * 100 + 99) * 4
        b2, g2, r2, a2 = pixels[last_idx:last_idx + 4]

        # Should be different due to gradient
        assert (b1, g1) != (b2, g2)
        # Alpha should be 255
        assert a1 == 255
        assert a2 == 255
