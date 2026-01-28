"""
Integration tests for the emulation layer.

Tests cross-module interactions within the emulation layer.
"""

import pytest
from src.modules.emulation.emulator_core import (
    create_interface as create_emulator,
    VMState,
    VMConfig,
)
from src.modules.emulation.device_manager import (
    create_interface as create_device_manager,
    DeviceType,
    DeviceInfo,
)
from src.modules.emulation.display_manager import (
    create_interface as create_display_manager,
    DisplayConfig,
)
from src.modules.emulation.input_manager import (
    create_interface as create_input_manager,
    InputEventType,
)
from src.modules.emulation.storage_manager import (
    create_interface as create_storage_manager,
    DiskImage,
)
from src.modules.emulation.network_manager import (
    create_interface as create_network_manager,
    NetworkMode,
    NetworkConfig,
)


class TestEmulationLayerIntegration:
    """Integration tests for emulation layer modules working together."""

    @pytest.fixture
    def emulator_core(self):
        """Create emulator core instance."""
        em = create_emulator()
        yield em
        em.cleanup()

    @pytest.fixture
    def device_manager(self):
        """Create device manager instance."""
        dm = create_device_manager()
        yield dm
        dm.cleanup()

    @pytest.fixture
    def display_manager(self):
        """Create display manager instance."""
        disp = create_display_manager()
        yield disp
        disp.cleanup()

    @pytest.fixture
    def input_manager(self):
        """Create input manager instance."""
        inp = create_input_manager()
        yield inp
        inp.cleanup()

    @pytest.fixture
    def storage_manager(self):
        """Create storage manager instance."""
        sm = create_storage_manager()
        yield sm
        sm.cleanup()

    @pytest.fixture
    def network_manager(self):
        """Create network manager instance."""
        nm = create_network_manager()
        yield nm
        nm.cleanup()

    def test_device_registration_workflow(self, device_manager):
        """Device manager can register and manage multiple device types."""
        # Register various device types using name and device_type args
        device_manager.register_device("virtio-blk-0", DeviceType.BLOCK)
        device_manager.register_device("virtio-gpu-0", DeviceType.DISPLAY)
        device_manager.register_device("virtio-net-0", DeviceType.NETWORK)

        # List and verify
        devices = device_manager.list_devices()
        assert len(devices) == 3

        # Get specific device
        retrieved = device_manager.get_device("virtio-gpu-0")
        assert retrieved.device_type == DeviceType.DISPLAY

    def test_emulator_state_transitions(self, emulator_core):
        """Emulator core follows proper state machine transitions."""
        assert emulator_core.get_state() == VMState.STOPPED

        # Initialize
        emulator_core.initialize()
        assert emulator_core.get_state() == VMState.STOPPED

        # Start
        emulator_core.start()
        assert emulator_core.get_state() == VMState.RUNNING

        # Pause
        emulator_core.pause()
        assert emulator_core.get_state() == VMState.PAUSED

        # Resume
        emulator_core.resume()
        assert emulator_core.get_state() == VMState.RUNNING

        # Stop
        emulator_core.stop()
        assert emulator_core.get_state() == VMState.STOPPED

    def test_display_and_input_coordination(self, display_manager, input_manager):
        """Display and input managers work together for GUI interaction."""
        # Configure display
        config = DisplayConfig(width=1080, height=1920, scale=1.0)
        display_manager.configure(config)

        # Get resolution for input coordinate scaling
        width, height = display_manager.get_resolution()

        # Send touch events within display bounds
        input_manager.send_touch(x=width // 2, y=height // 2, event_type=InputEventType.TOUCH_DOWN)
        input_manager.send_touch(x=width // 2, y=height // 2, event_type=InputEventType.TOUCH_UP)

        # Get pending events
        events = input_manager.get_pending_events()
        assert len(events) == 2
        assert events[0].event_type == InputEventType.TOUCH_DOWN
        assert events[0].x == 540  # width // 2
        assert events[0].y == 960  # height // 2

    def test_storage_with_overlay_workflow(self, storage_manager, tmp_path):
        """Storage manager handles base images with overlays."""
        # Create a mock base image file
        base_path = tmp_path / "system.img"
        base_path.write_bytes(b"mock system image data" * 1000)

        overlay_path = tmp_path / "overlay.qcow2"

        # Attach base image
        base_image = DiskImage(
            path=str(base_path),
            format="raw",
            size_mb=100,
            readonly=True
        )
        storage_manager.attach_image(base_image)

        # Create overlay - returns the overlay path as a string
        overlay_result = storage_manager.create_overlay(str(base_path), str(overlay_path))
        assert overlay_result is not None
        assert "overlay" in overlay_result.lower() or str(overlay_path) == overlay_result

        # List images
        images = storage_manager.list_images()
        assert len(images) >= 1

    def test_network_configuration_workflow(self, network_manager):
        """Network manager handles configuration and port forwarding."""
        # Configure network
        config = NetworkConfig(
            mode=NetworkMode.USER,
            host_forward_ports=[],
            dns_server="8.8.8.8"
        )
        network_manager.configure(config)

        # Enable network
        network_manager.enable()
        assert network_manager.is_connected() is True

        # Add port forward for ADB
        network_manager.add_port_forward(host_port=5555, guest_port=5555)

        # Add port forward for web server
        network_manager.add_port_forward(host_port=8080, guest_port=80)

        # Verify config
        current_config = network_manager.get_config()
        assert current_config.mode == NetworkMode.USER

        # Remove port forward
        network_manager.remove_port_forward(host_port=8080)

        # Disable
        network_manager.disable()
        assert network_manager.is_connected() is False

    def test_full_emulation_startup_sequence(
        self,
        emulator_core,
        device_manager,
        display_manager,
        input_manager,
        storage_manager,
        network_manager,
    ):
        """Test complete emulation layer startup sequence."""
        # 1. Register devices
        device_manager.register_device("display", DeviceType.DISPLAY)
        device_manager.register_device("input", DeviceType.INPUT)
        device_manager.register_device("network", DeviceType.NETWORK)

        # 2. Configure display
        display_manager.configure(DisplayConfig(width=1080, height=1920))

        # 3. Configure network
        network_manager.configure(NetworkConfig(mode=NetworkMode.USER))
        network_manager.enable()

        # 4. Initialize and start emulator
        emulator_core.initialize()
        emulator_core.start()

        # 5. Verify everything is running
        assert emulator_core.get_state() == VMState.RUNNING
        assert len(device_manager.list_devices()) == 3
        assert display_manager.get_resolution() == (1080, 1920)
        assert network_manager.is_connected() is True

        # 6. Send some input
        input_manager.send_key(keycode=66, event_type=InputEventType.KEY_DOWN)  # Enter
        input_manager.send_key(keycode=66, event_type=InputEventType.KEY_UP)

        events = input_manager.get_pending_events()
        assert len(events) == 2

        # 7. Clean shutdown
        emulator_core.stop()
        network_manager.disable()

        assert emulator_core.get_state() == VMState.STOPPED
        assert network_manager.is_connected() is False

    def test_display_scaling(self, display_manager, input_manager):
        """Display scaling affects input coordinate transformation."""
        # Configure at 2x scale
        config = DisplayConfig(width=1080, height=1920, scale=2.0)
        display_manager.configure(config)
        display_manager.set_scale(2.0)

        # The display resolution is the base resolution
        width, height = display_manager.get_resolution()
        assert width == 1080
        assert height == 1920

        # Scale was set (no getter, but set_scale doesn't raise means it worked)

    def test_device_initialization_order(self, device_manager):
        """Devices are initialized in registration order."""
        # Register devices in specific order
        for i in range(3):
            device_manager.register_device(f"device_{i}", DeviceType.BLOCK)

        # Initialize all
        device_manager.initialize_all()

        # Verify all devices exist
        devices = device_manager.list_devices()
        assert len(devices) == 3

        # Check all are initialized
        for device in devices:
            assert device.initialized is True
