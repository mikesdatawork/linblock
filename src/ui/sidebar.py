"""Sidebar navigation with logo, static buttons, and dynamic OS buttons."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GdkPixbuf
import os


class Sidebar(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_size_request(150, -1)
        self.get_style_context().add_class("sidebar")

        self._buttons = {}
        self._callbacks = {}
        self._dynamic_buttons = []

        self._build_ui()

    def _build_ui(self):
        # Logo area
        logo_frame = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        logo_frame.set_size_request(150, 150)
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        logo_path = os.path.join(base, '..', 'resources', 'images', 'linblock_logo.png')
        if os.path.exists(logo_path):
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 120, 120, True)
            logo = Gtk.Image.new_from_pixbuf(pixbuf)
        else:
            logo = Gtk.Label(label="LINBLOCK")
            logo.get_style_context().add_class("logo-text")
        logo_frame.pack_start(logo, True, True, 10)
        self.pack_start(logo_frame, False, False, 0)

        # Static buttons
        for name, label in [("about", "About"), ("load_os", "Load OS"), ("os_list", "Profiles")]:
            btn = Gtk.Button(label=label)
            btn.get_style_context().add_class("sidebar-button")
            btn.connect("clicked", self._on_button_clicked, name)
            self._buttons[name] = btn
            self.pack_start(btn, False, False, 0)

        # Separator
        self._separator = Gtk.Separator(orientation=Gtk.Orientation.HORIZONTAL)
        self.pack_start(self._separator, False, False, 4)

        # Dynamic buttons container
        self._dynamic_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.pack_start(self._dynamic_box, False, False, 0)

        # Spacer
        spacer = Gtk.Box()
        self.pack_start(spacer, True, True, 0)

    def _on_button_clicked(self, button, name):
        # Update active state
        for btn in self._buttons.values():
            btn.get_style_context().remove_class("sidebar-button-active")
        for btn in self._dynamic_buttons:
            btn.get_style_context().remove_class("sidebar-button-active")
        button.get_style_context().add_class("sidebar-button-active")

        if name in self._callbacks:
            self._callbacks[name]()

    def connect_button(self, name, callback):
        self._callbacks[name] = callback

    def add_os_button(self, profile_name, callback):
        btn = Gtk.Button(label=profile_name)
        btn.get_style_context().add_class("sidebar-button")
        btn.connect("clicked", self._on_button_clicked, f"os_{profile_name}")
        self._buttons[f"os_{profile_name}"] = btn
        self._callbacks[f"os_{profile_name}"] = callback
        self._dynamic_buttons.append(btn)
        self._dynamic_box.pack_start(btn, False, False, 0)
        btn.show()

    def remove_os_button(self, profile_name):
        key = f"os_{profile_name}"
        if key in self._buttons:
            btn = self._buttons.pop(key)
            self._dynamic_box.remove(btn)
            self._dynamic_buttons.remove(btn)
            self._callbacks.pop(key, None)

    def clear_dynamic_buttons(self):
        for btn in self._dynamic_buttons:
            self._dynamic_box.remove(btn)
        self._dynamic_buttons.clear()
