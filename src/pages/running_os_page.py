"""Running OS page - live emulator view with device controls."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .page_base import PageBase
from ui.components.device_controls import DeviceControlsPanel
from ui.components.emulator_display import EmulatorDisplay


class RunningOSPage(Gtk.Box):
    """Page displayed when an OS profile is running.

    Horizontal layout: DeviceControlsPanel (180px fixed) + EmulatorDisplay (fill).
    """

    def __init__(self, profile_name=""):
        super().__init__(orientation=Gtk.Orientation.HORIZONTAL, spacing=0)
        self._profile_name = profile_name
        self._build_ui()

    def _build_ui(self):
        # Left panel: device controls
        self.controls = DeviceControlsPanel()
        self.controls.set_size_request(180, -1)
        self.pack_start(self.controls, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.VERTICAL)
        self.pack_start(sep, False, False, 0)

        # Right area: emulator display
        self.display = EmulatorDisplay()
        self.pack_start(self.display, True, True, 0)

    def configure_for_profile(self, profile_dict):
        """Configure controls based on the OS profile settings."""
        self.controls.configure_for_profile(profile_dict)

    def get_profile_name(self):
        return self._profile_name
