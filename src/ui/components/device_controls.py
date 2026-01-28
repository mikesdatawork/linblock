"""Device controls panel - always-visible and conditional controls for running OS."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class DeviceControlsPanel(Gtk.Box):
    """Vertical control panel for device management.

    Always-present controls:
        On/Off Switch, Save State, Reset, Screenshot, Record Video

    Conditional controls (can be set insensitive based on profile):
        Settings, WiFi, Bluetooth, Airplane Mode, Auto-Rotate,
        Brightness, Volume, Do Not Disturb, Location, Battery Level
    """

    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        self.set_margin_start(6)
        self.set_margin_end(6)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.get_style_context().add_class("device-controls")

        self._controls = {}
        self._build_always_present()
        self._build_separator()
        self._build_conditional()

    def _build_always_present(self):
        """Build always-present device controls."""
        header = Gtk.Label()
        header.set_markup("<b>Device Controls</b>")
        header.set_halign(Gtk.Align.START)
        self.pack_start(header, False, False, 4)

        # On/Off switch
        on_off_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        on_off_label = Gtk.Label(label="Power")
        on_off_label.set_halign(Gtk.Align.START)
        on_off_box.pack_start(on_off_label, True, True, 0)
        self._power_switch = Gtk.Switch()
        self._power_switch.set_active(False)
        self._controls["power"] = self._power_switch
        on_off_box.pack_start(self._power_switch, False, False, 0)
        self.pack_start(on_off_box, False, False, 0)

        # Save State button
        self._save_state_btn = Gtk.Button(label="Save State")
        self._save_state_btn.get_style_context().add_class("device-button")
        self._controls["save_state"] = self._save_state_btn
        self.pack_start(self._save_state_btn, False, False, 0)

        # Reset button
        self._reset_btn = Gtk.Button(label="Reset")
        self._reset_btn.get_style_context().add_class("device-button")
        self._controls["reset"] = self._reset_btn
        self.pack_start(self._reset_btn, False, False, 0)

        # Screenshot button
        self._screenshot_btn = Gtk.Button(label="Screenshot")
        self._screenshot_btn.get_style_context().add_class("device-button")
        self._controls["screenshot"] = self._screenshot_btn
        self.pack_start(self._screenshot_btn, False, False, 0)

        # Record Video toggle
        self._record_btn = Gtk.ToggleButton(label="Record Video")
        self._record_btn.get_style_context().add_class("device-button")
        self._controls["record_video"] = self._record_btn
        self.pack_start(self._record_btn, False, False, 0)

    def _build_separator(self):
        """Add a visual separator between always and conditional controls."""
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep, False, False, 6)

    def _build_conditional(self):
        """Build conditional device controls."""
        # Settings button
        self._settings_btn = Gtk.Button(label="Settings")
        self._settings_btn.get_style_context().add_class("device-button")
        self._controls["settings"] = self._settings_btn
        self.pack_start(self._settings_btn, False, False, 0)

        # WiFi switch
        wifi_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        wifi_label = Gtk.Label(label="WiFi")
        wifi_label.set_halign(Gtk.Align.START)
        wifi_box.pack_start(wifi_label, True, True, 0)
        self._wifi_switch = Gtk.Switch()
        self._wifi_switch.set_active(True)
        self._controls["wifi"] = self._wifi_switch
        wifi_box.pack_start(self._wifi_switch, False, False, 0)
        self.pack_start(wifi_box, False, False, 0)

        # Bluetooth switch
        bt_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        bt_label = Gtk.Label(label="Bluetooth")
        bt_label.set_halign(Gtk.Align.START)
        bt_box.pack_start(bt_label, True, True, 0)
        self._bt_switch = Gtk.Switch()
        self._bt_switch.set_active(False)
        self._controls["bluetooth"] = self._bt_switch
        bt_box.pack_start(self._bt_switch, False, False, 0)
        self.pack_start(bt_box, False, False, 0)

        # Airplane Mode switch
        air_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        air_label = Gtk.Label(label="Airplane")
        air_label.set_halign(Gtk.Align.START)
        air_box.pack_start(air_label, True, True, 0)
        self._airplane_switch = Gtk.Switch()
        self._airplane_switch.set_active(False)
        self._controls["airplane_mode"] = self._airplane_switch
        air_box.pack_start(self._airplane_switch, False, False, 0)
        self.pack_start(air_box, False, False, 0)

        # Auto-Rotate switch
        rot_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        rot_label = Gtk.Label(label="Auto-Rotate")
        rot_label.set_halign(Gtk.Align.START)
        rot_box.pack_start(rot_label, True, True, 0)
        self._rotate_switch = Gtk.Switch()
        self._rotate_switch.set_active(True)
        self._controls["auto_rotate"] = self._rotate_switch
        rot_box.pack_start(self._rotate_switch, False, False, 0)
        self.pack_start(rot_box, False, False, 0)

        # Brightness scale
        bright_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        bright_label = Gtk.Label(label="Brightness")
        bright_label.set_halign(Gtk.Align.START)
        bright_box.pack_start(bright_label, False, False, 0)
        self._brightness_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self._brightness_scale.set_value(80)
        self._brightness_scale.set_draw_value(False)
        self._controls["brightness"] = self._brightness_scale
        bright_box.pack_start(self._brightness_scale, False, False, 0)
        self.pack_start(bright_box, False, False, 0)

        # Volume scale
        vol_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vol_label = Gtk.Label(label="Volume")
        vol_label.set_halign(Gtk.Align.START)
        vol_box.pack_start(vol_label, False, False, 0)
        self._volume_scale = Gtk.Scale.new_with_range(
            Gtk.Orientation.HORIZONTAL, 0, 100, 1
        )
        self._volume_scale.set_value(50)
        self._volume_scale.set_draw_value(False)
        self._controls["volume"] = self._volume_scale
        vol_box.pack_start(self._volume_scale, False, False, 0)
        self.pack_start(vol_box, False, False, 0)

        # Do Not Disturb switch
        dnd_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        dnd_label = Gtk.Label(label="DND")
        dnd_label.set_halign(Gtk.Align.START)
        dnd_box.pack_start(dnd_label, True, True, 0)
        self._dnd_switch = Gtk.Switch()
        self._dnd_switch.set_active(False)
        self._controls["do_not_disturb"] = self._dnd_switch
        dnd_box.pack_start(self._dnd_switch, False, False, 0)
        self.pack_start(dnd_box, False, False, 0)

        # Location switch
        loc_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        loc_label = Gtk.Label(label="Location")
        loc_label.set_halign(Gtk.Align.START)
        loc_box.pack_start(loc_label, True, True, 0)
        self._location_switch = Gtk.Switch()
        self._location_switch.set_active(True)
        self._controls["location"] = self._location_switch
        loc_box.pack_start(self._location_switch, False, False, 0)
        self.pack_start(loc_box, False, False, 0)

        # Battery LevelBar
        bat_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        bat_label = Gtk.Label(label="Battery")
        bat_label.set_halign(Gtk.Align.START)
        bat_box.pack_start(bat_label, False, False, 0)
        self._battery_bar = Gtk.LevelBar()
        self._battery_bar.set_min_value(0)
        self._battery_bar.set_max_value(100)
        self._battery_bar.set_value(100)
        self._controls["battery"] = self._battery_bar
        bat_box.pack_start(self._battery_bar, False, False, 0)
        self.pack_start(bat_box, False, False, 0)

    def configure_for_profile(self, profile_dict):
        """Set control sensitivity based on profile settings.

        Args:
            profile_dict: OS profile configuration dictionary.
                Keys checked: sensors.gps, sensors.accelerometer,
                network.bridge_mode, camera_media.webcam_passthrough, etc.
        """
        if not profile_dict:
            return

        # GPS sensor controls location
        sensors = profile_dict.get("sensors", profile_dict.get("device", {}).get("sensors", {}))
        if isinstance(sensors, dict):
            has_gps = sensors.get("gps", True)
            self._location_switch.set_sensitive(has_gps)

            has_accel = sensors.get("accelerometer", True)
            self._rotate_switch.set_sensitive(has_accel)

        # Network bridge mode
        network = profile_dict.get("network", {})
        if isinstance(network, dict):
            bridge = network.get("bridge_mode", False)
            self._wifi_switch.set_sensitive(not bridge)

    def get_control(self, name):
        """Get a control widget by name."""
        return self._controls.get(name)
