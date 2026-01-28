"""Load OS page - configuration form for creating a new OS profile."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .page_base import PageBase


class LoadOSPage(PageBase):
    def __init__(self):
        super().__init__()
        self._fields = {}
        self._build_content()

    def _build_content(self):
        self.add_section_header("Create New OS Profile")
        self.add_text("Configure all emulator settings below, then save.")

        # Section 1: Graphics / Rendering
        exp1 = Gtk.Expander(label="Graphics / Rendering")
        exp1.set_expanded(True)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box1.set_margin_start(12)
        box1.set_margin_top(6)
        box1.set_margin_bottom(6)

        # GPU mode
        row = self._make_combo_row("GPU Mode:", ["host", "software", "off"], "gpu_mode")
        box1.pack_start(row, False, False, 0)

        # API radio buttons
        api_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        api_label = Gtk.Label(label="Graphics API:")
        api_label.set_size_request(140, -1)
        api_label.set_halign(Gtk.Align.START)
        api_box.pack_start(api_label, False, False, 0)
        rb_opengl = Gtk.RadioButton.new_with_label(None, "OpenGL")
        rb_vulkan = Gtk.RadioButton.new_with_label_from_widget(rb_opengl, "Vulkan")
        self._fields["api_opengl"] = rb_opengl
        self._fields["api_vulkan"] = rb_vulkan
        api_box.pack_start(rb_opengl, False, False, 0)
        api_box.pack_start(rb_vulkan, False, False, 0)
        box1.pack_start(api_box, False, False, 0)

        # Renderer
        row = self._make_combo_row("Renderer:", ["auto", "angle", "swiftshader", "native"], "renderer")
        box1.pack_start(row, False, False, 0)

        exp1.add(box1)
        self.add_widget(exp1)

        # Section 2: ADB Configuration
        exp2 = Gtk.Expander(label="ADB Configuration")
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box2.set_margin_start(12)
        box2.set_margin_top(6)
        box2.set_margin_bottom(6)

        row = self._make_entry_row("ADB Path:", "/usr/bin/adb", "adb_path")
        box2.pack_start(row, False, False, 0)
        row = self._make_spin_row("ADB Port:", 5555, 1024, 65535, "adb_port")
        box2.pack_start(row, False, False, 0)
        row = self._make_check_row("Auto-connect on boot", True, "adb_auto_connect")
        box2.pack_start(row, False, False, 0)

        exp2.add(box2)
        self.add_widget(exp2)

        # Section 3: Device Simulation
        exp3 = Gtk.Expander(label="Device Simulation")
        box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box3.set_margin_start(12)
        box3.set_margin_top(6)
        box3.set_margin_bottom(6)

        row = self._make_combo_row("Screen Preset:", ["phone", "tablet", "custom"], "screen_preset")
        box3.pack_start(row, False, False, 0)
        row = self._make_spin_row("Width (px):", 1080, 240, 3840, "screen_width")
        box3.pack_start(row, False, False, 0)
        row = self._make_spin_row("Height (px):", 1920, 320, 3840, "screen_height")
        box3.pack_start(row, False, False, 0)

        # Sensor checkboxes
        sensor_label = Gtk.Label(label="Sensors:")
        sensor_label.set_halign(Gtk.Align.START)
        box3.pack_start(sensor_label, False, False, 0)
        for sensor in ["Accelerometer", "Gyroscope", "Proximity", "GPS"]:
            key = f"sensor_{sensor.lower()}"
            row = self._make_check_row(sensor, True, key)
            box3.pack_start(row, False, False, 0)

        exp3.add(box3)
        self.add_widget(exp3)

        # Section 4: Storage Paths
        exp4 = Gtk.Expander(label="Storage Paths")
        box4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box4.set_margin_start(12)
        box4.set_margin_top(6)
        box4.set_margin_bottom(6)

        row = self._make_file_row("Shared Folder:", "~/LinBlock/shared", "storage_shared")
        box4.pack_start(row, False, False, 0)
        row = self._make_file_row("Screenshot Dir:", "~/LinBlock/screenshots", "storage_screenshots")
        box4.pack_start(row, False, False, 0)
        row = self._make_file_row("Image Cache:", "~/LinBlock/cache", "storage_cache")
        box4.pack_start(row, False, False, 0)

        exp4.add(box4)
        self.add_widget(exp4)

        # Section 5: Network
        exp5 = Gtk.Expander(label="Network")
        box5 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box5.set_margin_start(12)
        box5.set_margin_top(6)
        box5.set_margin_bottom(6)

        row = self._make_check_row("Bridge Mode", False, "net_bridge")
        box5.pack_start(row, False, False, 0)
        row = self._make_entry_row("Proxy Address:", "", "net_proxy_addr")
        box5.pack_start(row, False, False, 0)
        row = self._make_spin_row("Proxy Port:", 0, 0, 65535, "net_proxy_port")
        box5.pack_start(row, False, False, 0)

        exp5.add(box5)
        self.add_widget(exp5)

        # Section 6: Input Mapping
        exp6 = Gtk.Expander(label="Input Mapping")
        box6 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box6.set_margin_start(12)
        box6.set_margin_top(6)
        box6.set_margin_bottom(6)

        row = self._make_check_row("Keyboard-to-touch mapping", True, "input_kbd_touch")
        box6.pack_start(row, False, False, 0)
        row = self._make_check_row("Gamepad support", False, "input_gamepad")
        box6.pack_start(row, False, False, 0)
        row = self._make_combo_row("Mouse Mode:", ["direct", "relative", "touch"], "input_mouse_mode")
        box6.pack_start(row, False, False, 0)

        exp6.add(box6)
        self.add_widget(exp6)

        # Section 7: Camera / Media
        exp7 = Gtk.Expander(label="Camera / Media")
        box7 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box7.set_margin_start(12)
        box7.set_margin_top(6)
        box7.set_margin_bottom(6)

        row = self._make_check_row("Webcam passthrough", False, "cam_webcam")
        box7.pack_start(row, False, False, 0)
        row = self._make_combo_row("Microphone:", ["default", "none", "virtual"], "cam_mic")
        box7.pack_start(row, False, False, 0)
        row = self._make_combo_row("Audio Output:", ["default", "none", "virtual"], "cam_audio")
        box7.pack_start(row, False, False, 0)

        exp7.add(box7)
        self.add_widget(exp7)

        # Section 8: Performance
        exp8 = Gtk.Expander(label="Performance")
        box8 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box8.set_margin_start(12)
        box8.set_margin_top(6)
        box8.set_margin_bottom(6)

        row = self._make_combo_row("Hypervisor:", ["kvm", "haxm", "software"], "perf_hypervisor")
        box8.pack_start(row, False, False, 0)
        row = self._make_combo_row("RAM (MB):", ["2048", "4096", "6144", "8192", "12288", "16384"], "perf_ram")
        box8.pack_start(row, False, False, 0)
        row = self._make_spin_row("CPU Cores:", 4, 1, 16, "perf_cpu_cores")
        box8.pack_start(row, False, False, 0)

        exp8.add(box8)
        self.add_widget(exp8)

        # Section 9: Google Services
        exp9 = Gtk.Expander(label="Google Services")
        box9 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box9.set_margin_start(12)
        box9.set_margin_top(6)
        box9.set_margin_bottom(6)

        google_services = [
            ("Play Store", "google_play_store"),
            ("Play Services", "google_play_services"),
            ("Play Protect", "google_play_protect"),
            ("Location Service", "google_location"),
            ("Contacts Sync", "google_contacts_sync"),
            ("Calendar Sync", "google_calendar_sync"),
            ("Google Drive", "google_drive"),
            ("Chrome", "google_chrome"),
            ("Google Maps", "google_maps"),
            ("Google Assistant", "google_assistant"),
        ]
        for label_text, key in google_services:
            row = self._make_check_row(label_text, False, key)
            box9.pack_start(row, False, False, 0)

        exp9.add(box9)
        self.add_widget(exp9)

        # Bottom: OS Name + Save
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.add_widget(sep)

        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        save_box.set_margin_top(8)

        name_label = Gtk.Label(label="OS Name:")
        name_label.set_halign(Gtk.Align.START)
        save_box.pack_start(name_label, False, False, 0)

        self._os_name_entry = Gtk.Entry()
        self._os_name_entry.set_placeholder_text("Enter OS profile name...")
        self._os_name_entry.set_hexpand(True)
        self._fields["os_name"] = self._os_name_entry
        save_box.pack_start(self._os_name_entry, True, True, 0)

        save_btn = Gtk.Button(label="Save Profile")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        save_box.pack_start(save_btn, False, False, 0)

        self.add_widget(save_box)

    def _make_combo_row(self, label_text, options, key):
        """Create a label + combo box row."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=label_text)
        label.set_size_request(140, -1)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        combo = Gtk.ComboBoxText()
        for opt in options:
            combo.append_text(opt)
        combo.set_active(0)
        self._fields[key] = combo
        box.pack_start(combo, True, True, 0)
        return box

    def _make_entry_row(self, label_text, default, key):
        """Create a label + entry row."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=label_text)
        label.set_size_request(140, -1)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(default)
        self._fields[key] = entry
        box.pack_start(entry, True, True, 0)
        return box

    def _make_spin_row(self, label_text, default, min_val, max_val, key):
        """Create a label + spin button row."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=label_text)
        label.set_size_request(140, -1)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        adj = Gtk.Adjustment(
            value=default, lower=min_val, upper=max_val,
            step_increment=1, page_increment=10
        )
        spin = Gtk.SpinButton(adjustment=adj)
        spin.set_numeric(True)
        self._fields[key] = spin
        box.pack_start(spin, True, True, 0)
        return box

    def _make_check_row(self, label_text, default, key):
        """Create a check button row."""
        check = Gtk.CheckButton(label=label_text)
        check.set_active(default)
        self._fields[key] = check
        return check

    def _make_file_row(self, label_text, default, key):
        """Create a label + file entry row."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=label_text)
        label.set_size_request(140, -1)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(default)
        self._fields[key] = entry
        box.pack_start(entry, True, True, 0)

        browse_btn = Gtk.Button(label="Browse...")
        browse_btn.connect("clicked", self._on_browse_clicked, entry)
        box.pack_start(browse_btn, False, False, 0)
        return box

    def _on_browse_clicked(self, button, entry):
        """Handle browse button click."""
        dialog = Gtk.FileChooserDialog(
            title="Select Directory",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            entry.set_text(dialog.get_filename())
        dialog.destroy()

    def _on_save_clicked(self, button):
        """Handle save button click."""
        os_name = self._os_name_entry.get_text().strip()
        if not os_name:
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                message_type=Gtk.MessageType.WARNING,
                buttons=Gtk.ButtonsType.OK,
                text="Please enter an OS profile name.",
            )
            dialog.run()
            dialog.destroy()
            return
        # Profile saving will be connected to ProfileManager
        print(f"Save profile: {os_name}")

    def get_field_values(self):
        """Collect all form field values into a dictionary."""
        values = {}
        for key, widget in self._fields.items():
            if isinstance(widget, Gtk.ComboBoxText):
                values[key] = widget.get_active_text()
            elif isinstance(widget, Gtk.Entry):
                values[key] = widget.get_text()
            elif isinstance(widget, Gtk.SpinButton):
                values[key] = widget.get_value_as_int()
            elif isinstance(widget, Gtk.CheckButton):
                values[key] = widget.get_active()
            elif isinstance(widget, Gtk.RadioButton):
                values[key] = widget.get_active()
        return values
