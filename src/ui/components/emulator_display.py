"""Emulator display widget - renders Android framebuffer."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import cairo


class EmulatorDisplay(Gtk.DrawingArea):
    def __init__(self):
        super().__init__()
        self.set_can_focus(True)
        self.add_events(
            Gdk.EventMask.BUTTON_PRESS_MASK |
            Gdk.EventMask.BUTTON_RELEASE_MASK |
            Gdk.EventMask.POINTER_MOTION_MASK |
            Gdk.EventMask.KEY_PRESS_MASK |
            Gdk.EventMask.KEY_RELEASE_MASK |
            Gdk.EventMask.SCROLL_MASK
        )
        self.connect("draw", self._on_draw)
        self.connect("button-press-event", self._on_button_press)
        self.connect("key-press-event", self._on_key_press)

        self._framebuffer = None
        self._display_width = 1080
        self._display_height = 1920
        self._scale = 0.4

    def _on_draw(self, widget, cr):
        alloc = self.get_allocation()

        # Draw background matching app theme (#1e1e2e)
        cr.set_source_rgb(0.118, 0.118, 0.180)
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.fill()

        # Draw phone outline (darker than background)
        phone_w = int(self._display_width * self._scale)
        phone_h = int(self._display_height * self._scale)
        x = (alloc.width - phone_w) // 2
        y = (alloc.height - phone_h) // 2

        # Phone screen area (#181825 - sidebar color)
        cr.set_source_rgb(0.094, 0.094, 0.145)
        cr.rectangle(x, y, phone_w, phone_h)
        cr.fill()

        # Phone border (#313244)
        cr.set_source_rgb(0.192, 0.196, 0.267)
        cr.set_line_width(2)
        cr.rectangle(x, y, phone_w, phone_h)
        cr.stroke()

        # Placeholder text
        cr.set_source_rgb(0.651, 0.706, 0.957)  # #a6adc8 dim-label color
        cr.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
        cr.set_font_size(14)
        text = "Android Display"
        extents = cr.text_extents(text)
        cr.move_to(x + (phone_w - extents.width) / 2, y + phone_h / 2)
        cr.show_text(text)

    def _on_button_press(self, widget, event):
        pass  # Will translate to touch events

    def _on_key_press(self, widget, event):
        pass  # Will translate to key events

    def set_scale(self, scale):
        self._scale = scale
        self.queue_draw()

    def set_framebuffer(self, data, width, height):
        self._framebuffer = data
        self._display_width = width
        self._display_height = height
        self.queue_draw()
