"""LinBlock - Custom Android Emulator Application."""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gio
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False


def main():
    if not GTK_AVAILABLE:
        print("ERROR: GTK3 (PyGObject) not available.")
        print("Install with: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        sys.exit(1)

    from ui.dashboard_window import MainWindow

    app = Gtk.Application(
        application_id="com.linblock.emulator",
        flags=Gio.ApplicationFlags.FLAGS_NONE,
    )

    def on_activate(app):
        win = MainWindow(application=app)
        win.show_all()

    app.connect("activate", on_activate)
    app.run(sys.argv)


if __name__ == "__main__":
    main()
