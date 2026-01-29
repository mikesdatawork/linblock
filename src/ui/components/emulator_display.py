"""Emulator display widget - renders Android framebuffer."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf, GLib
import cairo


class EmulatorDisplay(Gtk.DrawingArea):
    """Widget that displays the Android emulator screen.

    Renders framebuffer data from the emulator VNC connection,
    or shows a placeholder when not running.
    """

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
        self.connect("button-release-event", self._on_button_release)
        self.connect("motion-notify-event", self._on_motion)
        self.connect("key-press-event", self._on_key_press)
        self.connect("key-release-event", self._on_key_release)

        self._framebuffer = None
        self._pixbuf = None
        self._display_width = 1080
        self._display_height = 1920
        self._scale = 0.4
        self._status_text = ""
        self._format = "bgra"

        # Input callbacks (set by RunningOSPage)
        self._on_touch = None
        self._on_key = None

    def _on_draw(self, widget, cr):
        alloc = self.get_allocation()

        # Draw background matching app theme (#1e1e2e)
        cr.set_source_rgb(0.118, 0.118, 0.180)
        cr.rectangle(0, 0, alloc.width, alloc.height)
        cr.fill()

        # Calculate phone dimensions with auto-scaling
        phone_w = int(self._display_width * self._scale)
        phone_h = int(self._display_height * self._scale)

        # Auto-scale to fit container while maintaining aspect ratio
        max_width = alloc.width - 40
        max_height = alloc.height - 40
        if phone_w > max_width or phone_h > max_height:
            scale_w = max_width / self._display_width
            scale_h = max_height / self._display_height
            auto_scale = min(scale_w, scale_h)
            phone_w = int(self._display_width * auto_scale)
            phone_h = int(self._display_height * auto_scale)

        x = (alloc.width - phone_w) // 2
        y = (alloc.height - phone_h) // 2

        # Store for coordinate translation
        self._phone_rect = (x, y, phone_w, phone_h)

        if self._pixbuf is not None:
            # Draw actual framebuffer
            scaled = self._pixbuf.scale_simple(phone_w, phone_h, GdkPixbuf.InterpType.BILINEAR)
            Gdk.cairo_set_source_pixbuf(cr, scaled, x, y)
            cr.rectangle(x, y, phone_w, phone_h)
            cr.fill()
        else:
            # Phone screen area placeholder (#181825 - sidebar color)
            cr.set_source_rgb(0.094, 0.094, 0.145)
            cr.rectangle(x, y, phone_w, phone_h)
            cr.fill()

        # Phone border (#313244)
        cr.set_source_rgb(0.192, 0.196, 0.267)
        cr.set_line_width(2)
        cr.rectangle(x, y, phone_w, phone_h)
        cr.stroke()

        # Status or placeholder text
        if self._status_text or self._pixbuf is None:
            cr.set_source_rgb(0.651, 0.706, 0.957)  # #a6adc8 dim-label color
            cr.select_font_face("sans-serif", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
            cr.set_font_size(14)
            text = self._status_text if self._status_text else "Android Display"
            extents = cr.text_extents(text)
            cr.move_to(x + (phone_w - extents.width) / 2, y + phone_h / 2)
            cr.show_text(text)

    def _translate_coords(self, event_x, event_y):
        """Translate widget coordinates to emulator screen coordinates."""
        if not hasattr(self, '_phone_rect'):
            return None, None

        x, y, w, h = self._phone_rect

        # Check if inside phone area
        if event_x < x or event_x > x + w or event_y < y or event_y > y + h:
            return None, None

        # Translate to emulator coordinates
        emu_x = int((event_x - x) / w * self._display_width)
        emu_y = int((event_y - y) / h * self._display_height)

        return emu_x, emu_y

    def _on_button_press(self, widget, event):
        self.grab_focus()
        emu_x, emu_y = self._translate_coords(event.x, event.y)
        if emu_x is not None and self._on_touch:
            self._on_touch(emu_x, emu_y, "press", event.button)

    def _on_button_release(self, widget, event):
        emu_x, emu_y = self._translate_coords(event.x, event.y)
        if emu_x is not None and self._on_touch:
            self._on_touch(emu_x, emu_y, "release", event.button)

    def _on_motion(self, widget, event):
        emu_x, emu_y = self._translate_coords(event.x, event.y)
        if emu_x is not None and self._on_touch:
            self._on_touch(emu_x, emu_y, "motion", 0)

    def _on_key_press(self, widget, event):
        if self._on_key:
            self._on_key(event.keyval, True)

    def _on_key_release(self, widget, event):
        if self._on_key:
            self._on_key(event.keyval, False)

    def set_scale(self, scale):
        """Set display scale factor."""
        self._scale = scale
        self.queue_draw()

    def set_resolution(self, width, height):
        """Set the emulator display resolution."""
        self._display_width = width
        self._display_height = height
        self.queue_draw()

    def set_status(self, text):
        """Set status text to display over the screen."""
        self._status_text = text
        self.queue_draw()

    def set_framebuffer(self, data, width, height, format="bgra"):
        """Update the display with new framebuffer data.

        Args:
            data: Raw pixel data as bytes
            width: Frame width in pixels
            height: Frame height in pixels
            format: Pixel format - "bgra", "rgba", "rgb", or "bgr"
        """
        self._framebuffer = data
        self._display_width = width
        self._display_height = height
        self._format = format

        if data and len(data) > 0:
            try:
                # Convert to RGB for GdkPixbuf
                if format == "bgra":
                    # BGRA to RGB conversion
                    rgb_data = bytearray(width * height * 3)
                    for i in range(width * height):
                        src_idx = i * 4
                        dst_idx = i * 3
                        rgb_data[dst_idx] = data[src_idx + 2]      # R
                        rgb_data[dst_idx + 1] = data[src_idx + 1]  # G
                        rgb_data[dst_idx + 2] = data[src_idx]      # B
                    rgb_data = bytes(rgb_data)
                elif format == "rgba":
                    # RGBA to RGB conversion
                    rgb_data = bytearray(width * height * 3)
                    for i in range(width * height):
                        src_idx = i * 4
                        dst_idx = i * 3
                        rgb_data[dst_idx] = data[src_idx]          # R
                        rgb_data[dst_idx + 1] = data[src_idx + 1]  # G
                        rgb_data[dst_idx + 2] = data[src_idx + 2]  # B
                    rgb_data = bytes(rgb_data)
                elif format == "bgr":
                    # BGR to RGB conversion
                    rgb_data = bytearray(width * height * 3)
                    for i in range(width * height):
                        src_idx = i * 3
                        dst_idx = i * 3
                        rgb_data[dst_idx] = data[src_idx + 2]      # R
                        rgb_data[dst_idx + 1] = data[src_idx + 1]  # G
                        rgb_data[dst_idx + 2] = data[src_idx]      # B
                    rgb_data = bytes(rgb_data)
                else:
                    # Assume RGB
                    rgb_data = data

                # Create pixbuf from RGB data
                self._pixbuf = GdkPixbuf.Pixbuf.new_from_data(
                    rgb_data,
                    GdkPixbuf.Colorspace.RGB,
                    False,  # no alpha
                    8,      # bits per sample
                    width,
                    height,
                    width * 3,  # rowstride
                )

            except Exception as e:
                print(f"Framebuffer conversion error: {e}")
                self._pixbuf = None

        self.queue_draw()

    def set_touch_callback(self, callback):
        """Set callback for touch/mouse events.

        Callback signature: callback(x, y, event_type, button)
        event_type: "press", "release", "motion"
        """
        self._on_touch = callback

    def set_key_callback(self, callback):
        """Set callback for key events.

        Callback signature: callback(keyval, is_press)
        """
        self._on_key = callback

    def clear(self):
        """Clear the display."""
        self._framebuffer = None
        self._pixbuf = None
        self._status_text = ""
        self.queue_draw()
