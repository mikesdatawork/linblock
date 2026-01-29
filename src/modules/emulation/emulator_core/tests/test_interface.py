"""
Interface tests for emulator_core.

Tests the public API contract for CPU virtualization and VM lifecycle.
"""

import pytest
from ..interface import (
    EmulatorCoreInterface,
    DefaultEmulatorCore,
    create_interface,
    EmulatorCoreError,
    VMStartError,
    VMNotRunningError,
    VMState,
    VMConfig,
    VMInfo,
)


class TestEmulatorCoreInterface:
    """Test suite for EmulatorCoreInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration using stub backend."""
        return {"memory_mb": 2048, "cpu_cores": 2, "use_kvm": False, "backend": "stub"}

    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)

    def test_create_with_config(self, config):
        """Interface creates successfully with explicit config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, EmulatorCoreInterface)

    def test_create_with_defaults(self):
        """Interface creates with default config when none provided."""
        # Use stub backend to avoid QEMU dependency in tests
        iface = create_interface({"backend": "stub"})
        assert iface is not None
        assert isinstance(iface, EmulatorCoreInterface)

    def test_initial_state_stopped(self, interface):
        """Newly created VM is in STOPPED state."""
        assert interface.get_state() == VMState.STOPPED

    def test_start_requires_initialize(self, interface):
        """Starting without initialize raises VMStartError."""
        with pytest.raises(VMStartError):
            interface.start()

    def test_initialize_then_start(self, interface):
        """Initialize followed by start transitions to RUNNING."""
        interface.initialize()
        interface.start()
        assert interface.get_state() == VMState.RUNNING

    def test_stop_running_vm(self, interface):
        """Stopping a running VM transitions to STOPPED."""
        interface.initialize()
        interface.start()
        interface.stop()
        assert interface.get_state() == VMState.STOPPED

    def test_stop_non_running_raises(self, interface):
        """Stopping a non-running VM raises VMNotRunningError."""
        interface.initialize()
        with pytest.raises(VMNotRunningError):
            interface.stop()

    def test_pause_and_resume(self, interface):
        """Pausing and resuming cycles through correct states."""
        interface.initialize()
        interface.start()
        interface.pause()
        assert interface.get_state() == VMState.PAUSED
        interface.resume()
        assert interface.get_state() == VMState.RUNNING

    def test_resume_non_paused_raises(self, interface):
        """Resuming a VM that is not paused raises EmulatorCoreError."""
        interface.initialize()
        interface.start()
        with pytest.raises(EmulatorCoreError):
            interface.resume()

    def test_reset_running_vm(self, interface):
        """Resetting a running VM keeps it in RUNNING state."""
        interface.initialize()
        interface.start()
        interface.reset()
        assert interface.get_state() == VMState.RUNNING

    def test_get_info_returns_vminfo(self, interface):
        """get_info returns a VMInfo dataclass with correct state."""
        info = interface.get_info()
        assert isinstance(info, VMInfo)
        assert info.state == VMState.STOPPED

    def test_save_snapshot_returns_path(self, interface):
        """save_snapshot returns a snapshot path string."""
        interface.initialize()
        interface.start()
        path = interface.save_snapshot("my_snap")
        assert isinstance(path, str)
        assert "my_snap" in path

    def test_save_snapshot_non_running_raises(self, interface):
        """save_snapshot on a stopped VM raises VMNotRunningError."""
        interface.initialize()
        with pytest.raises(VMNotRunningError):
            interface.save_snapshot("fail_snap")

    def test_cleanup(self, interface):
        """cleanup stops a running VM and de-initializes."""
        interface.initialize()
        interface.start()
        interface.cleanup()
        assert interface.get_state() == VMState.STOPPED
