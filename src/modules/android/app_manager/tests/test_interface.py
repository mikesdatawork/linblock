"""
Interface tests for app_manager.

Tests the public API contract for installing, freezing, enabling,
disabling, and force-stopping Android applications.
"""

import pytest
from ..interface import (
    AppManagerInterface,
    DefaultAppManager,
    create_interface,
    AppManagerError,
    AppNotFoundError,
    AppState,
    AppInfo,
)


class TestAppManagerInterface:
    """Test suite for AppManagerInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def mgr(self, config):
        """Create a fresh app manager for each test."""
        return create_interface(config)

    # -- creation tests -------------------------------------------------------

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, AppManagerInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config when None is passed."""
        iface = create_interface()
        assert iface is not None

    # -- install_app tests ----------------------------------------------------

    def test_install_app_returns_app_info(self, mgr):
        """install_app returns a populated AppInfo."""
        info = mgr.install_app("com.example.app", "Example App")
        assert isinstance(info, AppInfo)
        assert info.package == "com.example.app"
        assert info.name == "Example App"
        assert info.state == AppState.INSTALLED
        assert info.install_time is not None

    def test_install_app_appears_in_list(self, mgr):
        """Installed app is visible via list_apps."""
        mgr.install_app("com.example.app", "Example App")
        apps = mgr.list_apps()
        assert len(apps) == 1
        assert apps[0].package == "com.example.app"

    # -- get_app_info tests ---------------------------------------------------

    def test_get_app_info_returns_correct_app(self, mgr):
        """get_app_info returns the right AppInfo."""
        mgr.install_app("com.example.app", "Example App")
        info = mgr.get_app_info("com.example.app")
        assert info.package == "com.example.app"

    def test_get_app_info_not_found(self, mgr):
        """get_app_info raises AppNotFoundError for unknown package."""
        with pytest.raises(AppNotFoundError):
            mgr.get_app_info("com.nonexistent")

    # -- freeze / unfreeze tests ----------------------------------------------

    def test_freeze_app_sets_frozen_state(self, mgr):
        """freeze_app changes state to FROZEN."""
        mgr.install_app("com.example.app", "Example App")
        mgr.freeze_app("com.example.app")
        info = mgr.get_app_info("com.example.app")
        assert info.state == AppState.FROZEN

    def test_unfreeze_app_restores_installed_state(self, mgr):
        """unfreeze_app changes state back to INSTALLED."""
        mgr.install_app("com.example.app", "Example App")
        mgr.freeze_app("com.example.app")
        mgr.unfreeze_app("com.example.app")
        info = mgr.get_app_info("com.example.app")
        assert info.state == AppState.INSTALLED

    def test_freeze_unknown_app_raises(self, mgr):
        """freeze_app raises AppNotFoundError for unknown package."""
        with pytest.raises(AppNotFoundError):
            mgr.freeze_app("com.unknown")

    # -- enable / disable tests -----------------------------------------------

    def test_disable_app_sets_disabled_state(self, mgr):
        """disable_app changes state to DISABLED."""
        mgr.install_app("com.example.app", "Example App")
        mgr.disable_app("com.example.app")
        info = mgr.get_app_info("com.example.app")
        assert info.state == AppState.DISABLED

    def test_enable_app_restores_installed_state(self, mgr):
        """enable_app changes state back to INSTALLED."""
        mgr.install_app("com.example.app", "Example App")
        mgr.disable_app("com.example.app")
        mgr.enable_app("com.example.app")
        info = mgr.get_app_info("com.example.app")
        assert info.state == AppState.INSTALLED

    # -- force_stop tests -----------------------------------------------------

    def test_force_stop_sets_stopped_state(self, mgr):
        """force_stop changes state to STOPPED."""
        mgr.install_app("com.example.app", "Example App")
        mgr.force_stop("com.example.app")
        info = mgr.get_app_info("com.example.app")
        assert info.state == AppState.STOPPED

    def test_force_stop_unknown_app_raises(self, mgr):
        """force_stop raises AppNotFoundError for unknown package."""
        with pytest.raises(AppNotFoundError):
            mgr.force_stop("com.unknown")

    # -- get_running_apps tests -----------------------------------------------

    def test_get_running_apps_empty_when_none_running(self, mgr):
        """get_running_apps returns empty list when no apps are running."""
        mgr.install_app("com.a", "App A")
        assert mgr.get_running_apps() == []

    def test_get_running_apps_filters_correctly(self, mgr):
        """get_running_apps returns only apps with RUNNING state."""
        mgr.install_app("com.a", "App A")
        mgr.install_app("com.b", "App B")
        # Manually set one to RUNNING to simulate the runtime.
        mgr._apps["com.a"].state = AppState.RUNNING
        running = mgr.get_running_apps()
        assert len(running) == 1
        assert running[0].package == "com.a"

    # -- list_apps tests ------------------------------------------------------

    def test_list_apps_empty_initially(self, mgr):
        """list_apps returns empty list before any installs."""
        assert mgr.list_apps() == []

    def test_list_apps_multiple(self, mgr):
        """list_apps returns all installed apps."""
        mgr.install_app("com.a", "App A")
        mgr.install_app("com.b", "App B")
        mgr.install_app("com.c", "App C")
        apps = mgr.list_apps()
        assert len(apps) == 3

    # -- cleanup tests --------------------------------------------------------

    def test_cleanup_clears_all_apps(self, mgr):
        """cleanup empties the app store."""
        mgr.install_app("com.example.app", "Example App")
        mgr.cleanup()
        with pytest.raises(AppManagerError):
            mgr.list_apps()

    def test_method_after_cleanup_raises(self, mgr):
        """Methods raise AppManagerError after cleanup."""
        mgr.cleanup()
        with pytest.raises(AppManagerError):
            mgr.install_app("com.a", "App A")
