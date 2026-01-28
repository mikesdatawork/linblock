"""
Interface tests for network_manager.

Tests the public API contract for virtual network management.
"""

import pytest
from ..interface import (
    NetworkManagerInterface,
    DefaultNetworkManager,
    create_interface,
    NetworkManagerError,
    NetworkNotEnabledError,
    PortForwardError,
    NetworkMode,
    NetworkConfig,
)


class TestNetworkManagerInterface:
    """Test suite for NetworkManagerInterface."""

    @pytest.fixture
    def config(self):
        return {}

    @pytest.fixture
    def manager(self, config):
        return create_interface(config)

    def test_create_with_defaults(self):
        """Interface creates with default config."""
        mgr = create_interface()
        assert mgr is not None
        assert isinstance(mgr, NetworkManagerInterface)

    def test_initial_state_disconnected(self, manager):
        """Network is not connected by default."""
        assert manager.is_connected() is False

    def test_configure_and_get_config(self, manager):
        """configure stores the config, get_config retrieves it."""
        cfg = NetworkConfig(mode=NetworkMode.BRIDGE, dns_server="1.1.1.1")
        manager.configure(cfg)
        result = manager.get_config()
        assert result.mode == NetworkMode.BRIDGE
        assert result.dns_server == "1.1.1.1"

    def test_enable_and_disable(self, manager):
        """enable/disable toggle the connection state."""
        manager.enable()
        assert manager.is_connected() is True
        manager.disable()
        assert manager.is_connected() is False

    def test_enable_none_mode_raises(self, manager):
        """Enabling with NONE mode raises NetworkManagerError."""
        manager.configure(NetworkConfig(mode=NetworkMode.NONE))
        with pytest.raises(NetworkManagerError):
            manager.enable()

    def test_add_port_forward(self, manager):
        """add_port_forward succeeds when network is enabled."""
        manager.enable()
        manager.add_port_forward(8080, 80)
        # Should not raise

    def test_add_port_forward_not_enabled_raises(self, manager):
        """add_port_forward raises when network is not enabled."""
        with pytest.raises(NetworkNotEnabledError):
            manager.add_port_forward(8080, 80)

    def test_add_duplicate_port_forward_raises(self, manager):
        """Adding the same host port twice raises PortForwardError."""
        manager.enable()
        manager.add_port_forward(8080, 80)
        with pytest.raises(PortForwardError):
            manager.add_port_forward(8080, 443)

    def test_remove_port_forward(self, manager):
        """remove_port_forward removes an existing rule."""
        manager.enable()
        manager.add_port_forward(8080, 80)
        manager.remove_port_forward(8080)
        # Re-adding should now succeed
        manager.add_port_forward(8080, 80)

    def test_remove_nonexistent_port_forward_raises(self, manager):
        """Removing a rule that does not exist raises PortForwardError."""
        with pytest.raises(PortForwardError):
            manager.remove_port_forward(9999)

    def test_cleanup(self, manager):
        """cleanup disables network and clears forwarding rules."""
        manager.enable()
        manager.add_port_forward(8080, 80)
        manager.cleanup()
        assert manager.is_connected() is False
