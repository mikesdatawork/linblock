"""
Interface tests for device_manager.

Tests the public API contract for virtual device management.
"""

import pytest
from ..interface import (
    DeviceManagerInterface,
    DefaultDeviceManager,
    create_interface,
    DeviceManagerError,
    DeviceNotFoundError,
    DuplicateDeviceError,
    DeviceType,
    DeviceInfo,
)


class TestDeviceManagerInterface:
    """Test suite for DeviceManagerInterface."""

    @pytest.fixture
    def config(self):
        return {}

    @pytest.fixture
    def manager(self, config):
        return create_interface(config)

    def test_create_with_config(self, config):
        """Interface creates successfully with config."""
        mgr = create_interface(config)
        assert mgr is not None
        assert isinstance(mgr, DeviceManagerInterface)

    def test_create_with_defaults(self):
        """Interface creates with default config."""
        mgr = create_interface()
        assert mgr is not None

    def test_register_device(self, manager):
        """Registering a device returns DeviceInfo."""
        info = manager.register_device("vda", DeviceType.BLOCK)
        assert isinstance(info, DeviceInfo)
        assert info.name == "vda"
        assert info.device_type == DeviceType.BLOCK
        assert info.initialized is False

    def test_register_duplicate_raises(self, manager):
        """Registering same name twice raises DuplicateDeviceError."""
        manager.register_device("vda", DeviceType.BLOCK)
        with pytest.raises(DuplicateDeviceError):
            manager.register_device("vda", DeviceType.BLOCK)

    def test_get_device(self, manager):
        """get_device returns the registered device."""
        manager.register_device("eth0", DeviceType.NETWORK)
        info = manager.get_device("eth0")
        assert info.name == "eth0"
        assert info.device_type == DeviceType.NETWORK

    def test_get_device_not_found(self, manager):
        """get_device for unknown name raises DeviceNotFoundError."""
        with pytest.raises(DeviceNotFoundError):
            manager.get_device("nonexistent")

    def test_list_devices(self, manager):
        """list_devices returns all registered devices."""
        manager.register_device("vda", DeviceType.BLOCK)
        manager.register_device("fb0", DeviceType.DISPLAY)
        devices = manager.list_devices()
        assert len(devices) == 2
        names = {d.name for d in devices}
        assert names == {"vda", "fb0"}

    def test_unregister_device(self, manager):
        """unregister_device removes the device."""
        manager.register_device("serial0", DeviceType.SERIAL)
        manager.unregister_device("serial0")
        with pytest.raises(DeviceNotFoundError):
            manager.get_device("serial0")

    def test_initialize_all(self, manager):
        """initialize_all marks every device as initialized."""
        manager.register_device("vda", DeviceType.BLOCK)
        manager.register_device("kbd0", DeviceType.INPUT)
        manager.initialize_all()
        for d in manager.list_devices():
            assert d.initialized is True

    def test_reset_device(self, manager):
        """reset_device sets initialized back to False."""
        manager.register_device("vda", DeviceType.BLOCK)
        manager.initialize_all()
        manager.reset_device("vda")
        assert manager.get_device("vda").initialized is False

    def test_cleanup_clears_devices(self, manager):
        """cleanup removes all devices."""
        manager.register_device("vda", DeviceType.BLOCK)
        manager.cleanup()
        assert manager.list_devices() == []
