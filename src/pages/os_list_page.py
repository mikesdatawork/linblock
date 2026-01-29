"""OS List page - manage saved OS builds with profile cards."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.profile_manager import ProfileManager


class ProfileCard(Gtk.Box):
    """A card widget displaying a saved OS profile."""

    def __init__(self, profile, on_launch, on_edit, on_delete):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        self._profile = profile
        self._on_launch = on_launch
        self._on_edit = on_edit
        self._on_delete = on_delete

        self.set_margin_start(8)
        self.set_margin_end(8)
        self.set_margin_top(8)
        self.set_margin_bottom(8)
        self.get_style_context().add_class("os-info-panel")

        self._build_ui()

    def _build_ui(self):
        # Profile name header
        name_label = Gtk.Label()
        name_label.set_markup(f"<b>{self._profile.name}</b>")
        name_label.set_halign(Gtk.Align.START)
        self.pack_start(name_label, False, False, 0)

        # Info grid
        info_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        info_box.set_margin_top(4)

        # Screen resolution
        screen = f"{self._profile.device.screen_width}x{self._profile.device.screen_height}"
        info_box.pack_start(self._make_info_row("Screen:", screen), False, False, 0)

        # RAM
        ram = f"{self._profile.performance.ram_mb} MB"
        info_box.pack_start(self._make_info_row("RAM:", ram), False, False, 0)

        # CPU Cores
        cores = f"{self._profile.performance.cpu_cores} cores"
        info_box.pack_start(self._make_info_row("CPU:", cores), False, False, 0)

        # GPU Mode
        gpu = self._profile.graphics.gpu_mode
        info_box.pack_start(self._make_info_row("GPU:", gpu), False, False, 0)

        # Image path (truncated)
        if self._profile.image_path:
            img_path = self._profile.image_path
            if len(img_path) > 35:
                img_path = "..." + img_path[-32:]
            info_box.pack_start(self._make_info_row("Image:", img_path), False, False, 0)

        # Created date (if available)
        if self._profile.created:
            created = self._profile.created.split('T')[0] if 'T' in self._profile.created else self._profile.created
            info_box.pack_start(self._make_info_row("Created:", created), False, False, 0)

        self.pack_start(info_box, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(sep, False, False, 4)

        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        launch_btn = Gtk.Button(label="Launch")
        launch_btn.get_style_context().add_class("suggested-action")
        launch_btn.connect("clicked", self._on_launch_clicked)
        btn_box.pack_start(launch_btn, True, True, 0)

        edit_btn = Gtk.Button(label="Edit")
        edit_btn.connect("clicked", self._on_edit_clicked)
        btn_box.pack_start(edit_btn, False, False, 0)

        delete_btn = Gtk.Button(label="Delete")
        delete_btn.get_style_context().add_class("destructive-action")
        delete_btn.connect("clicked", self._on_delete_clicked)
        btn_box.pack_start(delete_btn, False, False, 0)

        self.pack_start(btn_box, False, False, 0)

    def _make_info_row(self, label, value):
        """Create a label: value row."""
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)

        label_widget = Gtk.Label(label=label)
        label_widget.set_size_request(60, -1)
        label_widget.set_halign(Gtk.Align.START)
        label_widget.get_style_context().add_class("dim-label")
        row.pack_start(label_widget, False, False, 0)

        value_widget = Gtk.Label(label=value)
        value_widget.set_halign(Gtk.Align.START)
        value_widget.set_line_wrap(True)
        row.pack_start(value_widget, True, True, 0)

        return row

    def _on_launch_clicked(self, button):
        if self._on_launch:
            self._on_launch(self._profile)

    def _on_edit_clicked(self, button):
        if self._on_edit:
            self._on_edit(self._profile)

    def _on_delete_clicked(self, button):
        if self._on_delete:
            self._on_delete(self._profile)

    def get_profile(self):
        return self._profile


class OSListPage(Gtk.ScrolledWindow):
    """OS List page displaying saved profiles as cards."""

    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._profile_manager = ProfileManager()
        self._profile_cards = {}
        self._on_launch_callback = None
        self._on_edit_callback = None
        self._build_content()

    def _build_content(self):
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        main_box.set_margin_start(20)
        main_box.set_margin_end(20)
        main_box.set_margin_top(20)
        main_box.set_margin_bottom(20)

        # Header
        header = Gtk.Label()
        header.set_markup("<b><big>Saved OS Profiles</big></b>")
        header.set_halign(Gtk.Align.START)
        main_box.pack_start(header, False, False, 0)

        desc = Gtk.Label(label="Select a profile to launch or manage your saved configurations.")
        desc.set_halign(Gtk.Align.START)
        desc.set_line_wrap(True)
        main_box.pack_start(desc, False, False, 0)

        # Separator
        sep = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        main_box.pack_start(sep, False, False, 8)

        # Profiles container (FlowBox for responsive layout)
        self._flow_box = Gtk.FlowBox()
        self._flow_box.set_valign(Gtk.Align.START)
        self._flow_box.set_max_children_per_line(4)
        self._flow_box.set_min_children_per_line(1)
        self._flow_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._flow_box.set_homogeneous(False)
        self._flow_box.set_column_spacing(12)
        self._flow_box.set_row_spacing(12)

        main_box.pack_start(self._flow_box, True, True, 0)

        # Empty state placeholder
        self._empty_label = Gtk.Label()
        self._empty_label.set_markup(
            "<span color='#a6adc8'>No saved profiles yet.\n\n"
            "Go to <b>Load OS</b> to create a new profile.</span>"
        )
        self._empty_label.set_justify(Gtk.Justification.CENTER)
        self._empty_label.set_halign(Gtk.Align.CENTER)
        self._empty_label.set_valign(Gtk.Align.CENTER)
        main_box.pack_start(self._empty_label, True, True, 40)

        self.add(main_box)

        # Load profiles
        self.refresh_profiles()

    def set_on_launch(self, callback):
        """Set callback for when Launch button is clicked."""
        self._on_launch_callback = callback

    def set_on_edit(self, callback):
        """Set callback for when Edit button is clicked."""
        self._on_edit_callback = callback

    def refresh_profiles(self):
        """Reload profiles from disk and refresh the display."""
        # Clear existing cards
        for child in self._flow_box.get_children():
            self._flow_box.remove(child)
        self._profile_cards.clear()

        # Load profiles
        profiles = self._profile_manager.list_profiles()

        if not profiles:
            self._empty_label.show()
            self._flow_box.hide()
            return

        self._empty_label.hide()
        self._flow_box.show()

        for profile_name in sorted(profiles):
            try:
                profile = self._profile_manager.load_profile(profile_name)
                card = ProfileCard(
                    profile,
                    on_launch=self._handle_launch,
                    on_edit=self._handle_edit,
                    on_delete=self._handle_delete
                )
                card.set_size_request(280, -1)
                self._flow_box.add(card)
                self._profile_cards[profile_name] = card
            except Exception as e:
                print(f"Error loading profile {profile_name}: {e}")

        self._flow_box.show_all()

    def add_profile(self, profile):
        """Add or update a single profile card."""
        # Remove existing card if present
        if profile.name in self._profile_cards:
            old_card = self._profile_cards[profile.name]
            parent = old_card.get_parent()
            if parent:
                self._flow_box.remove(parent)
            del self._profile_cards[profile.name]

        # Create new card
        card = ProfileCard(
            profile,
            on_launch=self._handle_launch,
            on_edit=self._handle_edit,
            on_delete=self._handle_delete
        )
        card.set_size_request(280, -1)
        self._flow_box.add(card)
        self._profile_cards[profile.name] = card

        self._empty_label.hide()
        self._flow_box.show()
        self._flow_box.show_all()

    def remove_profile(self, profile_name):
        """Remove a profile card."""
        if profile_name in self._profile_cards:
            card = self._profile_cards[profile_name]
            parent = card.get_parent()
            if parent:
                self._flow_box.remove(parent)
            del self._profile_cards[profile_name]

        # Show empty state if no profiles
        if not self._profile_cards:
            self._empty_label.show()
            self._flow_box.hide()

    def _handle_launch(self, profile):
        """Handle launch button click."""
        if self._on_launch_callback:
            self._on_launch_callback(profile)

    def _handle_edit(self, profile):
        """Handle edit button click."""
        if self._on_edit_callback:
            self._on_edit_callback(profile)

    def _handle_delete(self, profile):
        """Handle delete button click - show confirmation dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self.get_toplevel(),
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=f"Delete profile '{profile.name}'?",
        )
        dialog.format_secondary_text(
            "This action cannot be undone. The profile configuration will be permanently deleted."
        )
        response = dialog.run()
        dialog.destroy()

        if response == Gtk.ResponseType.YES:
            try:
                self._profile_manager.delete_profile(profile.name)
                self.remove_profile(profile.name)
            except Exception as e:
                error_dialog = Gtk.MessageDialog(
                    transient_for=self.get_toplevel(),
                    message_type=Gtk.MessageType.ERROR,
                    buttons=Gtk.ButtonsType.OK,
                    text=f"Failed to delete profile: {e}",
                )
                error_dialog.run()
                error_dialog.destroy()
