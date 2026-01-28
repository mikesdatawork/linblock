"""Content area with Gtk.Stack for page switching."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class ContentArea(Gtk.Box):
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL)
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        self._stack.set_transition_duration(200)
        self.pack_start(self._stack, True, True, 0)

    def add_page(self, name, widget):
        self._stack.add_named(widget, name)

    def remove_page(self, name):
        child = self._stack.get_child_by_name(name)
        if child:
            self._stack.remove(child)

    def show_page(self, name):
        self._stack.set_visible_child_name(name)

    def get_current_page(self):
        visible = self._stack.get_visible_child_name()
        return visible if visible else ""
