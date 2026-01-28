"""Base class for all LinBlock pages."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class PageBase(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        self.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self._content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        self._content.set_margin_start(20)
        self._content.set_margin_end(20)
        self._content.set_margin_top(20)
        self._content.set_margin_bottom(20)
        self.add(self._content)

    def add_section_header(self, text):
        label = Gtk.Label()
        label.set_markup(f"<b><big>{text}</big></b>")
        label.set_halign(Gtk.Align.START)
        self._content.pack_start(label, False, False, 8)

    def add_text(self, text):
        label = Gtk.Label(label=text)
        label.set_line_wrap(True)
        label.set_halign(Gtk.Align.START)
        label.set_xalign(0)
        self._content.pack_start(label, False, False, 0)

    def add_widget(self, widget):
        self._content.pack_start(widget, False, False, 0)
