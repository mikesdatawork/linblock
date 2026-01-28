"""
Interface tests for gui_permissions.

Tests permission display and management UI logic.
"""

import pytest
from ..interface import (
    GuiPermissionsInterface,
    DefaultGuiPermissions,
    create_interface,
    GuiPermissionsError,
)


class TestGuiPermissionsInterface:
    """Test suite for GuiPermissionsInterface."""

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
        assert isinstance(interface, GuiPermissionsInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        interface = create_interface()
        assert interface is not None

    def test_set_permission_manager(self, interface):
        """set_permission_manager accepts a manager object."""
        manager = object()
        interface.set_permission_manager(manager)
        # Should not raise
        interface.show_app_permissions("com.example.app")

    def test_show_app_permissions_without_manager_raises(self, interface):
        """show_app_permissions raises when no permission manager set."""
        with pytest.raises(GuiPermissionsError, match="No permission manager set"):
            interface.show_app_permissions("com.example.app")

    def test_get_displayed_package_default_none(self, interface):
        """get_displayed_package returns None by default."""
        assert interface.get_displayed_package() is None

    def test_show_and_get_displayed_package(self, interface):
        """show_app_permissions sets displayed package."""
        interface.set_permission_manager(object())
        interface.show_app_permissions("com.example.browser")
        assert interface.get_displayed_package() == "com.example.browser"

    def test_refresh_without_manager_raises(self, interface):
        """refresh raises when no permission manager set."""
        with pytest.raises(GuiPermissionsError, match="No permission manager set"):
            interface.refresh()

    def test_refresh_with_manager(self, interface):
        """refresh succeeds with permission manager set."""
        interface.set_permission_manager(object())
        interface.refresh()  # Should not raise

    def test_cleanup(self, interface):
        """cleanup resets all state."""
        interface.set_permission_manager(object())
        interface.show_app_permissions("com.example.app")
        interface.cleanup()
        assert interface.get_displayed_package() is None
        with pytest.raises(GuiPermissionsError, match="No permission manager set"):
            interface.show_app_permissions("com.example.app")
