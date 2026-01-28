"""
Interface tests for display_manager.

Tests the public API contract for virtual display management.
"""

import pytest
from ..interface import (
    DisplayManagerInterface,
    DefaultDisplayManager,
    create_interface,
    DisplayManagerError,
    DisplayNotConfiguredError,
    DisplayConfig,
    FrameData,
)


class TestDisplayManagerInterface:
    """Test suite for DisplayManagerInterface."""

    @pytest.fixture
    def config(self):
        return {}

    @pytest.fixture
    def manager(self, config):
        return create_interface(config)

    @pytest.fixture
    def configured_manager(self, manager):
        manager.configure(DisplayConfig())
        return manager

    def test_create_with_defaults(self):
        """Interface creates with default config."""
        mgr = create_interface()
        assert mgr is not None
        assert isinstance(mgr, DisplayManagerInterface)

    def test_get_frame_before_configure_returns_none(self, manager):
        """get_frame returns None before configure is called."""
        assert manager.get_frame() is None

    def test_configure_and_get_frame(self, configured_manager):
        """After configure, get_frame returns FrameData."""
        frame = configured_manager.get_frame()
        assert frame is not None
        assert isinstance(frame, FrameData)
        assert frame.width == 1080
        assert frame.height == 1920

    def test_get_resolution(self, configured_manager):
        """get_resolution returns configured width and height."""
        w, h = configured_manager.get_resolution()
        assert w == 1080
        assert h == 1920

    def test_get_resolution_not_configured(self, manager):
        """get_resolution raises when display not configured."""
        with pytest.raises(DisplayNotConfiguredError):
            manager.get_resolution()

    def test_set_scale(self, configured_manager):
        """set_scale updates scale, affecting frame dimensions."""
        configured_manager.set_scale(2.0)
        frame = configured_manager.get_frame()
        assert frame is not None
        assert frame.width == 2160
        assert frame.height == 3840

    def test_get_fps_zero_initially(self, manager):
        """get_fps returns 0.0 when no frames have been captured."""
        assert manager.get_fps() == 0.0

    def test_get_fps_after_frames(self, configured_manager):
        """get_fps returns a positive value after capturing frames."""
        configured_manager.get_frame()
        configured_manager.get_frame()
        fps = configured_manager.get_fps()
        assert fps > 0.0

    def test_cleanup(self, configured_manager):
        """cleanup resets the display to unconfigured state."""
        configured_manager.cleanup()
        assert configured_manager.get_frame() is None
