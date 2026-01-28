"""
Interface tests for gui_core.

Tests window management and page switching.
"""

import pytest
from ..interface import (
    GuiCoreInterface,
    DefaultGuiCore,
    create_interface,
    GuiCoreError,
)


class TestGuiCoreInterface:
    """Test suite for GuiCoreInterface."""

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
        assert isinstance(interface, GuiCoreInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        interface = create_interface()
        assert interface is not None

    def test_initialize(self, interface):
        """initialize enables page registration."""
        interface.initialize()
        # Should not raise when registering after init
        interface.register_page("test", object())

    def test_register_page_before_init_raises(self, interface):
        """register_page raises GuiCoreError when not initialized."""
        with pytest.raises(GuiCoreError, match="Not initialized"):
            interface.register_page("test", object())

    def test_register_page_sets_current(self, interface):
        """First registered page becomes current page."""
        interface.initialize()
        interface.register_page("home", object())
        assert interface.get_current_page() == "home"

    def test_switch_page(self, interface):
        """switch_page changes current page."""
        interface.initialize()
        interface.register_page("home", object())
        interface.register_page("settings", object())
        interface.switch_page("settings")
        assert interface.get_current_page() == "settings"

    def test_switch_nonexistent_page_raises(self, interface):
        """switch_page raises for unknown page name."""
        interface.initialize()
        interface.register_page("home", object())
        with pytest.raises(GuiCoreError, match="Page not found"):
            interface.switch_page("nonexistent")

    def test_list_pages(self, interface):
        """list_pages returns all registered page names."""
        interface.initialize()
        interface.register_page("home", object())
        interface.register_page("settings", object())
        interface.register_page("about", object())
        pages = interface.list_pages()
        assert pages == ["home", "settings", "about"]

    def test_get_current_page_empty_before_register(self, interface):
        """get_current_page returns empty string before any pages registered."""
        assert interface.get_current_page() == ""

    def test_cleanup(self, interface):
        """cleanup resets all state."""
        interface.initialize()
        interface.register_page("home", object())
        interface.cleanup()
        assert interface.get_current_page() == ""
        assert interface.list_pages() == []
        # After cleanup, register should fail (not initialized)
        with pytest.raises(GuiCoreError, match="Not initialized"):
            interface.register_page("test", object())
