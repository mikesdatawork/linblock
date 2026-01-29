"""Load OS page - configuration form for creating a new OS profile."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib
import os
import sys
from datetime import datetime

# Add parent to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.os_profile import OSProfile
from utils.profile_manager import ProfileManager


def _get_default_images_dir():
    """Get the default android-images directory path."""
    base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    images_dir = os.path.join(base, "android-images")
    if os.path.isdir(images_dir):
        return images_dir
    return os.path.expanduser("~/.linblock/android-images")


class LoadOSPage(Gtk.ScrolledWindow):
    """Load OS page with Android selection and configuration form."""

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._fields = {}
        self._os_info = {}
        self._images_dir = _get_default_images_dir()
        self._profile_manager = ProfileManager()
        self._current_image_path = None
        self._on_profile_saved_callback = None
        self._build_content()

    def set_on_profile_saved(self, callback):
        """Set callback to be called when a profile is saved."""
        self._on_profile_saved_callback = callback

    def _build_content(self):
        # Use Paned for adjustable center margin
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        paned.set_margin_start(20)
        paned.set_margin_end(20)
        paned.set_margin_top(20)
        paned.set_margin_bottom(20)

        # Left side: Form
        left_scroll = Gtk.ScrolledWindow()
        left_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        left_scroll.set_min_content_width(400)

        self._form_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._form_box.set_margin_end(10)
        left_scroll.add(self._form_box)

        # Right side: OS Info Panel with proper padding
        right_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        right_frame.set_margin_start(10)

        right_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        right_box.set_size_request(300, -1)
        right_box.get_style_context().add_class("os-info-panel")
        right_box.set_margin_start(16)
        right_box.set_margin_end(16)
        right_box.set_margin_top(16)
        right_box.set_margin_bottom(16)

        info_label = Gtk.Label()
        info_label.set_markup("<b>Android OS Information</b>")
        info_label.set_halign(Gtk.Align.START)
        right_box.pack_start(info_label, False, False, 0)

        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        right_box.pack_start(sep, False, False, 8)

        # Scrollable info display area
        info_scroll = Gtk.ScrolledWindow()
        info_scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)

        self._info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._info_box.set_margin_top(4)
        info_scroll.add(self._info_box)
        right_box.pack_start(info_scroll, True, True, 0)

        right_frame.pack_start(right_box, True, True, 0)

        paned.pack1(left_scroll, resize=True, shrink=False)
        paned.pack2(right_frame, resize=True, shrink=False)
        paned.set_position(480)

        self.add(paned)
        self._build_form()

    def _build_form(self):
        # Page header
        header = Gtk.Label()
        header.set_markup("<b><big>Create New OS Profile</big></b>")
        header.set_halign(Gtk.Align.START)
        self._form_box.pack_start(header, False, False, 0)

        desc = Gtk.Label(label="Select Android OS and configure emulator settings.")
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        self._form_box.pack_start(desc, False, False, 0)

        # === Android OS Selection Section ===
        os_frame = Gtk.Frame(label=" Android OS Selection ")
        os_frame.set_margin_top(12)
        os_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        os_box.set_margin_start(12)
        os_box.set_margin_end(12)
        os_box.set_margin_top(8)
        os_box.set_margin_bottom(8)

        # Stock Android option
        self._rb_stock = Gtk.RadioButton.new_with_label(None, "Stock Android (Default)")
        self._rb_stock.connect("toggled", self._on_os_source_toggled)
        os_box.pack_start(self._rb_stock, False, False, 0)

        stock_desc = Gtk.Label(label=f"    Location: {self._images_dir}")
        stock_desc.set_halign(Gtk.Align.START)
        stock_desc.set_opacity(0.7)
        os_box.pack_start(stock_desc, False, False, 0)

        # Stock Android version selector
        stock_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        stock_row.set_margin_start(24)
        stock_label = Gtk.Label(label="Version:")
        stock_label.set_size_request(80, -1)
        stock_label.set_halign(Gtk.Align.START)
        stock_row.pack_start(stock_label, False, False, 0)

        self._stock_combo = Gtk.ComboBoxText()
        self._populate_stock_images()
        self._stock_combo.connect("changed", self._on_stock_version_changed)
        self._fields["stock_version"] = self._stock_combo
        stock_row.pack_start(self._stock_combo, True, True, 0)

        self._download_btn = Gtk.Button(label="Download More...")
        self._download_btn.connect("clicked", self._on_download_clicked)
        stock_row.pack_start(self._download_btn, False, False, 0)
        os_box.pack_start(stock_row, False, False, 0)

        # Separator
        os_box.pack_start(Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL), False, False, 4)

        # Custom Android option
        self._rb_custom = Gtk.RadioButton.new_with_label_from_widget(
            self._rb_stock, "Custom Android OS"
        )
        self._rb_custom.connect("toggled", self._on_os_source_toggled)
        os_box.pack_start(self._rb_custom, False, False, 0)

        custom_desc = Gtk.Label(label="    Select a folder containing Android system image")
        custom_desc.set_halign(Gtk.Align.START)
        custom_desc.set_opacity(0.7)
        os_box.pack_start(custom_desc, False, False, 0)

        # Custom path selector
        custom_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        custom_row.set_margin_start(24)
        custom_label = Gtk.Label(label="Path:")
        custom_label.set_size_request(80, -1)
        custom_label.set_halign(Gtk.Align.START)
        custom_row.pack_start(custom_label, False, False, 0)

        self._custom_entry = Gtk.Entry()
        self._custom_entry.set_placeholder_text("Select Android OS folder...")
        self._custom_entry.set_sensitive(False)
        self._custom_entry.connect("changed", self._on_custom_path_changed)
        self._fields["custom_path"] = self._custom_entry
        custom_row.pack_start(self._custom_entry, True, True, 0)

        self._browse_btn = Gtk.Button(label="Browse...")
        self._browse_btn.connect("clicked", self._on_browse_os_clicked)
        self._browse_btn.set_sensitive(False)
        custom_row.pack_start(self._browse_btn, False, False, 0)
        os_box.pack_start(custom_row, False, False, 0)

        os_frame.add(os_box)
        self._form_box.pack_start(os_frame, False, False, 0)

        # Update info panel with default stock selection
        self._update_stock_info()

        # === Configuration Sections ===
        self._build_config_sections()

        # === Save Section ===
        self._build_save_section()

    def _build_config_sections(self):
        """Build the configuration expander sections."""

        # Section 1: Graphics / Rendering
        exp1 = Gtk.Expander(label="Graphics / Rendering")
        exp1.set_expanded(False)
        box1 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box1.set_margin_start(12)
        box1.set_margin_top(6)
        box1.set_margin_bottom(6)

        gpu_opts = ["host", "software", "off"]
        box1.pack_start(self._make_combo_row("GPU Mode:", gpu_opts, "gpu_mode"), False, False, 0)

        api_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        api_label = Gtk.Label(label="Graphics API:")
        api_label.set_size_request(120, -1)
        api_label.set_halign(Gtk.Align.START)
        api_box.pack_start(api_label, False, False, 0)
        rb_opengl = Gtk.RadioButton.new_with_label(None, "OpenGL")
        rb_vulkan = Gtk.RadioButton.new_with_label_from_widget(rb_opengl, "Vulkan")
        self._fields["api_opengl"] = rb_opengl
        self._fields["api_vulkan"] = rb_vulkan
        api_box.pack_start(rb_opengl, False, False, 0)
        api_box.pack_start(rb_vulkan, False, False, 0)
        box1.pack_start(api_box, False, False, 0)

        renderer_opts = ["auto", "angle", "swiftshader", "native"]
        box1.pack_start(self._make_combo_row("Renderer:", renderer_opts, "renderer"), False, False, 0)

        exp1.add(box1)
        self._form_box.pack_start(exp1, False, False, 0)

        # Section 2: ADB Configuration
        exp2 = Gtk.Expander(label="ADB Configuration")
        box2 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box2.set_margin_start(12)
        box2.set_margin_top(6)
        box2.set_margin_bottom(6)

        box2.pack_start(self._make_entry_row("ADB Path:", "/usr/bin/adb", "adb_path"), False, False, 0)
        box2.pack_start(self._make_spin_row("ADB Port:", 5555, 1024, 65535, "adb_port"), False, False, 0)
        box2.pack_start(self._make_check_row("Auto-connect on boot", True, "adb_auto"), False, False, 0)

        exp2.add(box2)
        self._form_box.pack_start(exp2, False, False, 0)

        # Section 3: Device Simulation
        exp3 = Gtk.Expander(label="Device Simulation")
        box3 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box3.set_margin_start(12)
        box3.set_margin_top(6)
        box3.set_margin_bottom(6)

        preset_opts = ["phone", "tablet", "custom"]
        box3.pack_start(self._make_combo_row("Screen Preset:", preset_opts, "screen_preset"), False, False, 0)
        box3.pack_start(self._make_spin_row("Width (px):", 1080, 240, 3840, "screen_width"), False, False, 0)
        box3.pack_start(self._make_spin_row("Height (px):", 1920, 320, 3840, "screen_height"), False, False, 0)

        sensor_label = Gtk.Label(label="Sensors:")
        sensor_label.set_halign(Gtk.Align.START)
        box3.pack_start(sensor_label, False, False, 0)
        for sensor in ["Accelerometer", "Gyroscope", "Proximity", "GPS"]:
            key = f"sensor_{sensor.lower()}"
            box3.pack_start(self._make_check_row(sensor, True, key), False, False, 0)

        exp3.add(box3)
        self._form_box.pack_start(exp3, False, False, 0)

        # Section 4: Storage Paths
        exp4 = Gtk.Expander(label="Storage Paths")
        box4 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box4.set_margin_start(12)
        box4.set_margin_top(6)
        box4.set_margin_bottom(6)

        box4.pack_start(self._make_file_row("Shared Folder:", "~/LinBlock/shared", "storage_shared"), False, False, 0)
        row = self._make_file_row("Screenshots:", "~/LinBlock/screenshots", "storage_screenshots")
        box4.pack_start(row, False, False, 0)
        box4.pack_start(self._make_file_row("Image Cache:", "~/LinBlock/cache", "storage_cache"), False, False, 0)

        exp4.add(box4)
        self._form_box.pack_start(exp4, False, False, 0)

        # Section 5: Network
        exp5 = Gtk.Expander(label="Network")
        box5 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box5.set_margin_start(12)
        box5.set_margin_top(6)
        box5.set_margin_bottom(6)

        box5.pack_start(self._make_check_row("Bridge Mode", False, "net_bridge"), False, False, 0)
        box5.pack_start(self._make_entry_row("Proxy Address:", "", "net_proxy_addr"), False, False, 0)
        box5.pack_start(self._make_spin_row("Proxy Port:", 0, 0, 65535, "net_proxy_port"), False, False, 0)

        exp5.add(box5)
        self._form_box.pack_start(exp5, False, False, 0)

        # Section 6: Input Mapping
        exp6 = Gtk.Expander(label="Input Mapping")
        box6 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box6.set_margin_start(12)
        box6.set_margin_top(6)
        box6.set_margin_bottom(6)

        box6.pack_start(self._make_check_row("Keyboard-to-touch mapping", True, "input_kbd"), False, False, 0)
        box6.pack_start(self._make_check_row("Gamepad support", False, "input_gamepad"), False, False, 0)
        mouse_opts = ["direct", "relative", "touch"]
        box6.pack_start(self._make_combo_row("Mouse Mode:", mouse_opts, "input_mouse"), False, False, 0)

        exp6.add(box6)
        self._form_box.pack_start(exp6, False, False, 0)

        # Section 7: Camera / Media
        exp7 = Gtk.Expander(label="Camera / Media")
        box7 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box7.set_margin_start(12)
        box7.set_margin_top(6)
        box7.set_margin_bottom(6)

        box7.pack_start(self._make_check_row("Webcam passthrough", False, "cam_webcam"), False, False, 0)
        media_opts = ["default", "none", "virtual"]
        box7.pack_start(self._make_combo_row("Microphone:", media_opts, "cam_mic"), False, False, 0)
        box7.pack_start(self._make_combo_row("Audio Output:", media_opts, "cam_audio"), False, False, 0)

        exp7.add(box7)
        self._form_box.pack_start(exp7, False, False, 0)

        # Section 8: Performance
        exp8 = Gtk.Expander(label="Performance")
        box8 = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        box8.set_margin_start(12)
        box8.set_margin_top(6)
        box8.set_margin_bottom(6)

        hyper_opts = ["kvm", "haxm", "software"]
        box8.pack_start(self._make_combo_row("Hypervisor:", hyper_opts, "perf_hypervisor"), False, False, 0)
        ram_opts = ["2048", "4096", "6144", "8192", "12288", "16384"]
        box8.pack_start(self._make_combo_row("RAM (MB):", ram_opts, "perf_ram"), False, False, 0)
        box8.pack_start(self._make_spin_row("CPU Cores:", 4, 1, 16, "perf_cpu_cores"), False, False, 0)

        exp8.add(box8)
        self._form_box.pack_start(exp8, False, False, 0)

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
            box9.pack_start(self._make_check_row(label_text, False, key), False, False, 0)

        exp9.add(box9)
        self._form_box.pack_start(exp9, False, False, 0)

    def _build_save_section(self):
        """Build the save profile section."""
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self._form_box.pack_start(sep, False, False, 8)

        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        name_label = Gtk.Label(label="Profile Name:")
        name_label.set_halign(Gtk.Align.START)
        save_box.pack_start(name_label, False, False, 0)

        self._os_name_entry = Gtk.Entry()
        self._os_name_entry.set_placeholder_text("Enter profile name...")
        self._fields["os_name"] = self._os_name_entry
        save_box.pack_start(self._os_name_entry, True, True, 0)

        save_btn = Gtk.Button(label="Save Profile")
        save_btn.get_style_context().add_class("suggested-action")
        save_btn.connect("clicked", self._on_save_clicked)
        save_box.pack_start(save_btn, False, False, 0)

        self._form_box.pack_start(save_box, False, False, 0)

    def _make_combo_row(self, label_text, options, key):
        """Create a label + combo box row."""
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        label = Gtk.Label(label=label_text)
        label.set_size_request(120, -1)
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
        label.set_size_request(120, -1)
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
        label.set_size_request(120, -1)
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
        label.set_size_request(120, -1)
        label.set_halign(Gtk.Align.START)
        box.pack_start(label, False, False, 0)

        entry = Gtk.Entry()
        entry.set_text(default)
        self._fields[key] = entry
        box.pack_start(entry, True, True, 0)

        browse_btn = Gtk.Button(label="...")
        browse_btn.connect("clicked", self._on_browse_clicked, entry)
        box.pack_start(browse_btn, False, False, 0)
        return box

    def _populate_stock_images(self):
        """Scan android-images directory and populate the combo box."""
        self._stock_images = {}

        if os.path.isdir(self._images_dir):
            for entry in sorted(os.listdir(self._images_dir)):
                entry_path = os.path.join(self._images_dir, entry)
                if os.path.isdir(entry_path):
                    has_system = os.path.exists(os.path.join(entry_path, "system.img"))
                    has_props = os.path.exists(os.path.join(entry_path, "source.properties"))

                    if has_system or has_props:
                        info = self._parse_android_folder(entry_path)
                        android_ver = info.get("AndroidVersion", "")
                        api_level = info.get("SystemImage.ApiLevel", "")
                        abi = info.get("SystemImage.Abi", "x86_64")
                        tag = info.get("SystemImage.TagDisplay", "")

                        if android_ver and api_level:
                            display = f"Android {android_ver} (API {api_level}) - {abi}"
                            if tag:
                                display += f" [{tag}]"
                        else:
                            display = entry

                        self._stock_images[entry] = entry_path
                        self._stock_combo.append(entry, display)

        if not self._stock_images:
            self._stock_combo.append("none", "No images found - click Download More...")
            self._stock_images["none"] = None

        self._stock_combo.set_active(0)

    def _on_os_source_toggled(self, button):
        """Handle OS source radio button toggle."""
        is_custom = self._rb_custom.get_active()
        self._stock_combo.set_sensitive(not is_custom)
        self._download_btn.set_sensitive(not is_custom)
        self._custom_entry.set_sensitive(is_custom)
        self._browse_btn.set_sensitive(is_custom)

        if not is_custom:
            self._update_stock_info()
        else:
            self._update_custom_info()

    def _on_stock_version_changed(self, combo):
        """Handle stock version selection change."""
        self._update_stock_info()

    def _on_custom_path_changed(self, entry):
        """Handle custom path entry change."""
        self._update_custom_info()

    def _on_download_clicked(self, button):
        """Handle download button click."""
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Download Android Images",
        )
        dialog.format_secondary_text(
            "Visit the Android GSI releases page to download system images:\n\n"
            "https://developer.android.com/topic/generic-system-image/releases\n\n"
            f"Extract downloaded images to:\n{self._images_dir}"
        )
        dialog.run()
        dialog.destroy()

    def _on_browse_os_clicked(self, button):
        """Handle browse for custom OS button click."""
        dialog = Gtk.FileChooserDialog(
            title="Select Android System Image Folder",
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(
            Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
        )
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self._custom_entry.set_text(dialog.get_filename())
        dialog.destroy()

    def _on_browse_clicked(self, button, entry):
        """Handle browse button click for path entries."""
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

    def _update_stock_info(self):
        """Update info panel with stock Android details."""
        version_id = self._stock_combo.get_active_id()

        if not version_id or version_id == "none":
            self._display_os_info({"Status": "No Android image selected"})
            self._current_image_path = None
            return

        image_path = self._stock_images.get(version_id)
        if image_path and os.path.isdir(image_path):
            self._current_image_path = image_path
            info = self._parse_android_folder(image_path)
            self._display_os_info(info)
        else:
            self._current_image_path = None
            self._display_os_info({"Status": "Image not found"})

    def _update_custom_info(self):
        """Update info panel with custom Android folder details."""
        path = self._custom_entry.get_text().strip()
        if not path or not os.path.isdir(path):
            self._display_os_info({"Status": "No valid folder selected"})
            self._current_image_path = None
            return

        self._current_image_path = path
        info = self._parse_android_folder(path)
        self._display_os_info(info)

    def _parse_android_folder(self, path):
        """Parse Android system image folder for metadata."""
        info = {}

        # Try to read source.properties
        source_props = os.path.join(path, "source.properties")
        if os.path.exists(source_props):
            try:
                with open(source_props, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            info[key.strip()] = value.strip()
            except Exception as e:
                info["Parse Error"] = str(e)

        # Try to read build.prop for additional info (only specific keys)
        build_prop = os.path.join(path, "build.prop")
        if os.path.exists(build_prop):
            try:
                with open(build_prop, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if '=' in line and not line.startswith('#'):
                            key, value = line.split('=', 1)
                            key = key.strip()
                            # Only add specific build.prop values
                            if key in [
                                "ro.build.version.release",
                                "ro.build.version.sdk",
                                "ro.build.id",
                                "ro.build.version.security_patch",
                                "ro.build.date",
                                "ro.product.cpu.abi",
                                "ro.build.description"
                            ] and key not in info:
                                info[key] = value.strip()
            except Exception:
                pass

        # Check for system.img
        system_img = os.path.join(path, "system.img")
        if os.path.exists(system_img):
            size_mb = os.path.getsize(system_img) / (1024 * 1024)
            info["system.img"] = f"{size_mb:.1f} MB"
            info["Status"] = "Ready to use"
        else:
            info["Status"] = "Warning: system.img not found"

        info["Path"] = path
        return info

    def _display_os_info(self, info):
        """Display OS information in the right panel."""
        # Clear existing info
        for child in self._info_box.get_children():
            self._info_box.remove(child)

        if not info:
            placeholder = Gtk.Label(label="Select an Android OS to view details")
            placeholder.set_halign(Gtk.Align.START)
            placeholder.set_opacity(0.6)
            self._info_box.pack_start(placeholder, False, False, 0)
            self._info_box.show_all()
            return

        # Map of source keys to display labels (priority order)
        # Only show one value per display label
        display_map = [
            ("Android Version", ["AndroidVersion", "ro.build.version.release"]),
            ("API Level", ["SystemImage.ApiLevel", "ro.build.version.sdk"]),
            ("Architecture", ["SystemImage.Abi", "ro.product.cpu.abi"]),
            ("Variant", ["SystemImage.TagDisplay", "SystemImage.TagId"]),
            ("Description", ["Pkg.Desc"]),
            ("Build ID", ["ro.build.id"]),
            ("Security Patch", ["ro.build.version.security_patch"]),
            ("Build Date", ["ro.build.date"]),
            ("System Image", ["system.img"]),
            ("Location", ["Path"]),
            ("Status", ["Status"]),
        ]

        for display_label, source_keys in display_map:
            for key in source_keys:
                if key in info:
                    self._add_info_row(display_label, info[key])
                    break  # Only show first matching key

        self._info_box.show_all()

    def _add_info_row(self, label, value):
        """Add an info row to the info panel."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)

        label_widget = Gtk.Label(label=f"{label}:")
        label_widget.set_size_request(110, -1)
        label_widget.set_halign(Gtk.Align.START)
        label_widget.set_valign(Gtk.Align.START)
        label_widget.get_style_context().add_class("dim-label")
        row.pack_start(label_widget, False, False, 0)

        value_widget = Gtk.Label(label=str(value))
        value_widget.set_halign(Gtk.Align.START)
        value_widget.set_line_wrap(True)
        value_widget.set_selectable(True)
        value_widget.set_max_width_chars(30)
        row.pack_start(value_widget, True, True, 0)

        self._info_box.pack_start(row, False, False, 0)

    def _on_save_clicked(self, button):
        """Handle save button click - save profile to disk."""
        os_name = self._os_name_entry.get_text().strip()
        if not os_name:
            self._show_message(Gtk.MessageType.WARNING, "Please enter a profile name.")
            return

        if not self._current_image_path:
            self._show_message(Gtk.MessageType.WARNING, "Please select an Android OS image.")
            return

        # Check if profile already exists
        if self._profile_manager.profile_exists(os_name):
            dialog = Gtk.MessageDialog(
                transient_for=self.get_toplevel(),
                message_type=Gtk.MessageType.QUESTION,
                buttons=Gtk.ButtonsType.YES_NO,
                text=f"Profile '{os_name}' already exists. Overwrite?",
            )
            response = dialog.run()
            dialog.destroy()
            if response != Gtk.ResponseType.YES:
                return

        # Create and save profile
        try:
            profile = self._create_profile_from_form(os_name)
            self._profile_manager.save_profile(profile)
            self._show_message(
                Gtk.MessageType.INFO,
                f"Profile '{os_name}' saved successfully!"
            )
            # Notify main window to refresh profile list
            if self._on_profile_saved_callback:
                self._on_profile_saved_callback(profile)
        except Exception as e:
            self._show_message(
                Gtk.MessageType.ERROR,
                f"Failed to save profile: {str(e)}"
            )

    def _create_profile_from_form(self, name):
        """Create an OSProfile from the current form values."""
        now = datetime.now().isoformat()
        profile = OSProfile()
        profile.name = name
        profile.image_path = self._current_image_path or ""
        profile.created = now
        profile.modified = now

        # Graphics
        profile.graphics.gpu_mode = self._get_combo_value("gpu_mode")
        profile.graphics.api = "vulkan" if self._fields.get("api_vulkan") and \
            self._fields["api_vulkan"].get_active() else "opengl"
        profile.graphics.renderer = self._get_combo_value("renderer")

        # ADB
        profile.adb.path = self._get_entry_value("adb_path")
        profile.adb.port = self._get_spin_value("adb_port")
        profile.adb.auto_connect = self._get_check_value("adb_auto")

        # Device
        profile.device.screen_preset = self._get_combo_value("screen_preset")
        profile.device.screen_width = self._get_spin_value("screen_width")
        profile.device.screen_height = self._get_spin_value("screen_height")
        profile.device.sensors.accelerometer = self._get_check_value("sensor_accelerometer")
        profile.device.sensors.gyroscope = self._get_check_value("sensor_gyroscope")
        profile.device.sensors.proximity = self._get_check_value("sensor_proximity")
        profile.device.sensors.gps = self._get_check_value("sensor_gps")

        # Storage
        profile.storage.shared_folder = self._get_entry_value("storage_shared")
        profile.storage.screenshot_dir = self._get_entry_value("storage_screenshots")
        profile.storage.image_cache = self._get_entry_value("storage_cache")

        # Network
        profile.network.bridge_mode = self._get_check_value("net_bridge")
        profile.network.proxy_address = self._get_entry_value("net_proxy_addr")
        profile.network.proxy_port = self._get_spin_value("net_proxy_port")

        # Input
        profile.input.keyboard_to_touch = self._get_check_value("input_kbd")
        profile.input.gamepad = self._get_check_value("input_gamepad")
        profile.input.mouse_mode = self._get_combo_value("input_mouse")

        # Camera/Media
        profile.camera_media.webcam_passthrough = self._get_check_value("cam_webcam")
        profile.camera_media.mic_source = self._get_combo_value("cam_mic")
        profile.camera_media.audio_output = self._get_combo_value("cam_audio")

        # Performance
        profile.performance.hypervisor = self._get_combo_value("perf_hypervisor")
        ram_str = self._get_combo_value("perf_ram")
        profile.performance.ram_mb = int(ram_str) if ram_str else 4096
        profile.performance.cpu_cores = self._get_spin_value("perf_cpu_cores")

        # Google Services
        profile.google_services.play_store = self._get_check_value("google_play_store")
        profile.google_services.play_services = self._get_check_value("google_play_services")
        profile.google_services.play_protect = self._get_check_value("google_play_protect")
        profile.google_services.location_service = self._get_check_value("google_location")
        profile.google_services.contacts_sync = self._get_check_value("google_contacts_sync")
        profile.google_services.calendar_sync = self._get_check_value("google_calendar_sync")
        profile.google_services.drive = self._get_check_value("google_drive")
        profile.google_services.chrome = self._get_check_value("google_chrome")
        profile.google_services.maps = self._get_check_value("google_maps")
        profile.google_services.assistant = self._get_check_value("google_assistant")

        return profile

    def _get_combo_value(self, key):
        """Get value from a combo box field."""
        widget = self._fields.get(key)
        if widget and isinstance(widget, Gtk.ComboBoxText):
            return widget.get_active_text() or ""
        return ""

    def _get_entry_value(self, key):
        """Get value from an entry field."""
        widget = self._fields.get(key)
        if widget and isinstance(widget, Gtk.Entry):
            return widget.get_text()
        return ""

    def _get_spin_value(self, key):
        """Get value from a spin button field."""
        widget = self._fields.get(key)
        if widget and isinstance(widget, Gtk.SpinButton):
            return widget.get_value_as_int()
        return 0

    def _get_check_value(self, key):
        """Get value from a check button field."""
        widget = self._fields.get(key)
        if widget and isinstance(widget, Gtk.CheckButton):
            return widget.get_active()
        return False

    def _show_message(self, msg_type, text):
        """Show a message dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            message_type=msg_type,
            buttons=Gtk.ButtonsType.OK,
            text=text,
        )
        dialog.run()
        dialog.destroy()

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
