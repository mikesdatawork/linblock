"""OS List page - manage saved OS builds."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .page_base import PageBase


class OSListPage(PageBase):
    def __init__(self):
        super().__init__()
        self._build_content()

    def _build_content(self):
        self.add_section_header("Saved OS Builds")
        self.add_text("Manage your saved OS configurations.")

        # Column headers
        cols = ["Name", "Screen Size", "RAM", "GPU Mode", "Status", "Actions"]
        self._list_store = Gtk.ListStore(str, str, str, str, str, str)
        self._tree_view = Gtk.TreeView(model=self._list_store)

        for i, title in enumerate(cols):
            renderer = Gtk.CellRendererText()
            column = Gtk.TreeViewColumn(title, renderer, text=i)
            column.set_resizable(True)
            column.set_min_width(80)
            self._tree_view.append_column(column)

        scroll = Gtk.ScrolledWindow()
        scroll.set_min_content_height(300)
        scroll.add(self._tree_view)
        self.add_widget(scroll)

        # Action buttons
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        for label in ["Rename", "Delete", "Duplicate", "Edit Settings"]:
            btn = Gtk.Button(label=label)
            btn_box.pack_start(btn, False, False, 0)
        self.add_widget(btn_box)

    def add_os_entry(self, name, screen, ram, gpu, status):
        self._list_store.append([name, screen, ram, gpu, status, "..."])

    def clear_entries(self):
        self._list_store.clear()
