"""Running OS page - live emulator view with device controls."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os

from .page_base import PageBase
from ui.components.device_controls import DeviceControlsPanel
from ui.components.emulator_display import EmulatorDisplay


class RunningOSPage(Gtk.Box):
    """Page displayed when an OS profile is running.

    Horizontal layout: DeviceControlsPanel (180px fixed) + EmulatorDisplay (fill).

    Supports two display modes:
    1. Direct frame callback - uses emulator's frame callback
    2. Shared memory - uses GPU renderer's SharedMemoryFrameSource for better performance
    """

    def __init__(self, profile_name=""):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._profile_name = profile_name
        self._profile_dict = None
        self._emulator = None
        self._emulator_initialized = False
        self._gpu_renderer = None
        self._frame_source = None

        # Add padding around the entire page
        self.set_margin_start(16)
        self.set_margin_end(16)
        self.set_margin_top(16)
        self.set_margin_bottom(16)

        self._build_ui()

    def _build_ui(self):
        # Left panel: device controls
        self.controls = DeviceControlsPanel()
        self.controls.set_size_request(180, -1)
        self.pack_start(self.controls, False, False, 0)

        # Connect power switch to emulator control
        power_switch = self.controls.get_control("power")
        if power_switch:
            power_switch.connect("notify::active", self._on_power_toggled)

        # Connect reset button
        reset_btn = self.controls.get_control("reset")
        if reset_btn:
            reset_btn.connect("clicked", self._on_reset_clicked)

        # Separator with margin
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        sep.set_margin_start(8)
        sep.set_margin_end(8)
        self.pack_start(sep, False, False, 0)

        # Right area: emulator display
        self.display = EmulatorDisplay()
        self.pack_start(self.display, True, True, 0)

    def configure_for_profile(self, profile_dict):
        """Configure controls and emulator based on the OS profile settings."""
        self._profile_dict = profile_dict
        self.controls.configure_for_profile(profile_dict)

        # Initialize emulator with profile settings
        self._init_emulator()

    def _init_emulator(self):
        """Initialize the emulator core with profile configuration."""
        if self._emulator_initialized:
            return

        if not self._profile_dict:
            return

        try:
            from modules.emulation.emulator_core.interface import create_interface

            # Extract configuration from profile
            performance = self._profile_dict.get("performance", {})
            device = self._profile_dict.get("device", {})
            graphics = self._profile_dict.get("graphics", {})
            adb = self._profile_dict.get("adb", {})

            # Get system image path
            image_path = self._profile_dict.get("image_path", "")

            # If image_path is a directory, look for system.img inside it
            if image_path and os.path.isdir(image_path):
                system_img = os.path.join(image_path, "system.img")
                if os.path.exists(system_img):
                    image_path = system_img

            config = {
                "system_image": image_path,
                "memory_mb": performance.get("ram_mb", 4096),
                "cpu_cores": performance.get("cpu_cores", 4),
                "use_kvm": performance.get("hypervisor", "kvm") == "kvm",
                "screen_width": device.get("screen_width", 1080),
                "screen_height": device.get("screen_height", 1920),
                "gpu_mode": graphics.get("gpu_mode", "host"),
                "adb_port": adb.get("port", 5555),
                "vnc_port": 5900,  # Will need port allocation for multiple instances
            }

            self._emulator = create_interface(config)
            self._emulator.initialize()

            # Register callbacks for state and frame updates
            if hasattr(self._emulator, 'add_state_callback'):
                self._emulator.add_state_callback(self._on_emulator_state)
            if hasattr(self._emulator, 'add_frame_callback'):
                self._emulator.add_frame_callback(self._on_frame_update)

            self._emulator_initialized = True

            # Initialize GPU renderer for hardware-accelerated display
            self._init_gpu_renderer(device, graphics)

            # Update display with configured resolution
            self.display.set_resolution(
                device.get("screen_width", 1080),
                device.get("screen_height", 1920)
            )

        except Exception as e:
            self._show_error(f"Failed to initialize emulator: {e}")

    def _init_gpu_renderer(self, device, graphics):
        """Initialize GPU renderer and shared memory frame source."""
        try:
            from modules.emulation.gpu_renderer import create_interface as create_gpu_renderer

            gpu_mode = graphics.get("gpu_mode", "host")

            # Create GPU renderer config
            gpu_config = {
                "backend": "stub" if gpu_mode == "software" else "native",
                "width": device.get("screen_width", 1080),
                "height": device.get("screen_height", 1920),
                "use_sandbox": True,
            }

            self._gpu_renderer = create_gpu_renderer(gpu_config)
            self._gpu_renderer.initialize()

            # If renderer has shared memory, set up frame source
            if hasattr(self._gpu_renderer, 'get_shm_name'):
                shm_name = self._gpu_renderer.get_shm_name()
                if shm_name:
                    self._setup_shared_memory_display(shm_name)

        except Exception as e:
            # GPU renderer is optional - log and continue
            print(f"GPU renderer initialization failed (using fallback): {e}")

    def _setup_shared_memory_display(self, shm_name):
        """Set up shared memory frame source for display."""
        try:
            from modules.emulation.gpu_renderer.gtk_integration import SharedMemoryFrameSource

            self._frame_source = SharedMemoryFrameSource(shm_name, target_fps=60)
            self._frame_source.attach(self.display)
            self._frame_source.set_frame_callback(self._on_shm_frame)

        except Exception as e:
            print(f"Shared memory display setup failed: {e}")

    def _on_shm_frame(self, frame_number, width, height):
        """Handle frame delivered from shared memory."""
        # Frame is already sent to display via SharedMemoryFrameSource
        # This callback is for additional processing if needed
        pass

    def _on_power_toggled(self, switch, pspec):
        """Handle power switch toggle."""
        if not self._emulator:
            self._show_error("Emulator not initialized")
            return

        is_on = switch.get_active()

        if is_on:
            self._start_emulator()
        else:
            self._stop_emulator()

    def _start_emulator(self):
        """Start the emulator."""
        if not self._emulator:
            return

        try:
            from modules.emulation.emulator_core.interface import VMState

            state = self._emulator.get_state()
            if state == VMState.RUNNING:
                return

            # Update display to show starting state
            self.display.set_status("Starting Android...")

            # Start emulator (this may take a moment)
            self._emulator.start()

            # Start frame source if using shared memory
            if self._frame_source:
                self._frame_source.start()

        except Exception as e:
            self._show_error(f"Failed to start emulator: {e}")
            # Reset power switch
            power_switch = self.controls.get_control("power")
            if power_switch:
                power_switch.set_active(False)

    def _stop_emulator(self):
        """Stop the emulator."""
        if not self._emulator:
            return

        try:
            from modules.emulation.emulator_core.interface import VMState

            # Stop frame source first
            if self._frame_source:
                self._frame_source.stop()

            state = self._emulator.get_state()
            if state == VMState.STOPPED:
                return

            self.display.set_status("Stopping...")
            self._emulator.stop()
            self.display.set_status("Powered Off")

        except Exception as e:
            self._show_error(f"Failed to stop emulator: {e}")

    def _on_reset_clicked(self, button):
        """Handle reset button click."""
        if not self._emulator:
            return

        try:
            self.display.set_status("Resetting...")
            self._emulator.reset()
        except Exception as e:
            self._show_error(f"Reset failed: {e}")

    def _on_emulator_state(self, state):
        """Handle emulator state changes (called from background thread)."""
        from modules.emulation.emulator_core.interface import VMState

        # Update UI from main thread
        def update_ui():
            if state == VMState.RUNNING:
                self.display.set_status("")
                power_switch = self.controls.get_control("power")
                if power_switch and not power_switch.get_active():
                    power_switch.set_active(True)
            elif state == VMState.STOPPED:
                self.display.set_status("Powered Off")
                power_switch = self.controls.get_control("power")
                if power_switch and power_switch.get_active():
                    power_switch.set_active(False)
            elif state == VMState.ERROR:
                info = self._emulator.get_info() if self._emulator else None
                error_msg = info.error_message if info else "Unknown error"
                self.display.set_status(f"Error: {error_msg}")
            elif state == VMState.STARTING:
                self.display.set_status("Starting...")
            elif state == VMState.STOPPING:
                self.display.set_status("Stopping...")
            return False

        GLib.idle_add(update_ui)

    def _on_frame_update(self, frame):
        """Handle framebuffer update (called from background thread)."""
        def update_display():
            self.display.set_framebuffer(frame.data, frame.width, frame.height, frame.format)
            return False

        GLib.idle_add(update_display)

    def _show_error(self, message):
        """Show error message in a dialog."""
        def show_dialog():
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=message,
            )
            dialog.run()
            dialog.destroy()
            return False

        GLib.idle_add(show_dialog)

    def get_profile_name(self):
        return self._profile_name

    def cleanup(self):
        """Clean up emulator and GPU renderer resources."""
        # Stop frame source first
        if self._frame_source:
            try:
                self._frame_source.stop()
            except Exception:
                pass
            self._frame_source = None

        # Clean up GPU renderer
        if self._gpu_renderer:
            try:
                self._gpu_renderer.cleanup()
            except Exception:
                pass
            self._gpu_renderer = None

        # Clean up emulator
        if self._emulator:
            try:
                self._emulator.cleanup()
            except Exception:
                pass
            self._emulator = None

        self._emulator_initialized = False
