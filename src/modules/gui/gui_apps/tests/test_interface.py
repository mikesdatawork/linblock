"""
Interface tests for gui_apps.

Tests application list display and selection.
"""

import pytest
from ..interface import (
    GuiAppsInterface,
    DefaultGuiApps,
    create_interface,
    GuiAppsError,
)


class _FakeAppManager:
    """Fake app manager for testing."""
    def __init__(self, apps=None):
        self._apps = apps or []

    def list_apps(self):
        return self._apps


class TestGuiAppsInterface:
    """Test suite for GuiAppsInterface."""

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
        assert isinstance(interface, GuiAppsInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        interface = create_interface()
        assert interface is not None

    def test_set_app_manager(self, interface):
        """set_app_manager accepts a manager object."""
        manager = _FakeAppManager(["com.example.app"])
        interface.set_app_manager(manager)
        # Should not raise on refresh
        interface.refresh_app_list()

    def test_refresh_without_manager_raises(self, interface):
        """refresh_app_list raises when no app manager set."""
        with pytest.raises(GuiAppsError, match="No app manager set"):
            interface.refresh_app_list()

    def test_get_selected_app_default_none(self, interface):
        """get_selected_app returns None by default."""
        assert interface.get_selected_app() is None

    def test_select_app(self, interface):
        """select_app sets the selected app package."""
        interface.select_app("com.example.browser")
        assert interface.get_selected_app() == "com.example.browser"

    def test_select_app_overwrite(self, interface):
        """select_app overwrites previous selection."""
        interface.select_app("com.example.first")
        interface.select_app("com.example.second")
        assert interface.get_selected_app() == "com.example.second"

    def test_cleanup(self, interface):
        """cleanup resets all state."""
        manager = _FakeAppManager(["com.example.app"])
        interface.set_app_manager(manager)
        interface.select_app("com.example.app")
        interface.cleanup()
        assert interface.get_selected_app() is None
        with pytest.raises(GuiAppsError, match="No app manager set"):
            interface.refresh_app_list()
