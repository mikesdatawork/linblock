"""
Interface tests for gui_display.

Tests framebuffer rendering and display management.
"""

import pytest
from ..interface import (
    GuiDisplayInterface,
    DefaultGuiDisplay,
    create_interface,
    GuiDisplayError,
)


class TestGuiDisplayInterface:
    """Test suite for GuiDisplayInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        interface = create_interface(config)
        assert interface is not None
        assert isinstance(interface, GuiDisplayInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        interface = create_interface()
        assert interface is not None

    def test_set_framebuffer_source(self, interface):
        """set_framebuffer_source accepts a source object."""
        source = object()
        interface.set_framebuffer_source(source)
        # Should now be able to start rendering
        interface.start_rendering()
        assert interface.is_rendering()

    def test_start_rendering_without_source_raises(self, interface):
        """start_rendering raises when no framebuffer source set."""
        with pytest.raises(GuiDisplayError, match="No framebuffer source"):
            interface.start_rendering()

    def test_stop_rendering(self, interface):
        """stop_rendering sets rendering state to False."""
        interface.set_framebuffer_source(object())
        interface.start_rendering()
        assert interface.is_rendering()
        interface.stop_rendering()
        assert not interface.is_rendering()

    def test_is_rendering_default_false(self, interface):
        """is_rendering returns False by default."""
        assert not interface.is_rendering()

    def test_set_and_get_scale(self, interface):
        """set_scale and get_scale manage display scale."""
        assert interface.get_scale() == 1.0
        interface.set_scale(0.5)
        assert interface.get_scale() == 0.5
        interface.set_scale(2.0)
        assert interface.get_scale() == 2.0

    def test_set_invalid_scale_raises(self, interface):
        """set_scale raises for non-positive scale."""
        with pytest.raises(GuiDisplayError, match="Invalid scale"):
            interface.set_scale(0)
        with pytest.raises(GuiDisplayError, match="Invalid scale"):
            interface.set_scale(-1.0)

    def test_capture_screenshot(self, interface):
        """capture_screenshot returns path when rendering."""
        interface.set_framebuffer_source(object())
        interface.start_rendering()
        result = interface.capture_screenshot("/tmp/shot.png")
        assert result == "/tmp/shot.png"

    def test_capture_screenshot_not_rendering_raises(self, interface):
        """capture_screenshot raises when not rendering."""
        with pytest.raises(GuiDisplayError, match="Not currently rendering"):
            interface.capture_screenshot("/tmp/shot.png")

    def test_cleanup(self, interface):
        """cleanup resets all state."""
        interface.set_framebuffer_source(object())
        interface.start_rendering()
        interface.set_scale(2.0)
        interface.cleanup()
        assert not interface.is_rendering()
        assert interface.get_scale() == 1.0
