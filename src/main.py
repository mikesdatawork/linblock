"""LinBlock - Custom Android Emulator Application."""

import sys
import os
import signal
import atexit
import subprocess

# Add src to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk, Gio, GLib
    GTK_AVAILABLE = True
except (ImportError, ValueError):
    GTK_AVAILABLE = False

# Global reference to the main window for cleanup
_main_window = None


def _kill_orphan_qemu_processes():
    """Kill any QEMU processes started by this application."""
    try:
        # Find and kill qemu-system processes
        result = subprocess.run(
            ["pgrep", "-f", "qemu-system"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            pids = result.stdout.strip().split('\n')
            for pid in pids:
                if pid:
                    try:
                        os.kill(int(pid), signal.SIGKILL)
                        print(f"Killed orphaned QEMU process: {pid}")
                    except (OSError, ValueError):
                        pass
    except Exception:
        pass


def _cleanup_handler():
    """Cleanup handler called on exit."""
    global _main_window

    # Try graceful cleanup through the window first
    if _main_window:
        try:
            _main_window.cleanup_all_profiles()
        except Exception:
            pass

    # Force kill any remaining QEMU processes
    _kill_orphan_qemu_processes()


def _signal_handler(signum, frame):
    """Handle termination signals."""
    print(f"\nReceived signal {signum}, cleaning up...")
    _cleanup_handler()
    sys.exit(0)


def main():
    global _main_window

    if not GTK_AVAILABLE:
        print("ERROR: GTK3 (PyGObject) not available.")
        print("Install with: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0")
        sys.exit(1)

    # Register cleanup handlers
    atexit.register(_cleanup_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    signal.signal(signal.SIGTERM, _signal_handler)

    # Handle SIGINT in GTK main loop
    GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGINT, lambda: Gtk.main_quit() or True)

    from ui.dashboard_window import MainWindow

    app = Gtk.Application(
        application_id="com.linblock.emulator",
        flags=Gio.ApplicationFlags.FLAGS_NONE,
    )

    def on_activate(app):
        global _main_window
        win = MainWindow(application=app)
        _main_window = win
        win.show_all()

    def on_shutdown(app):
        """Called when application is shutting down."""
        _cleanup_handler()

    app.connect("activate", on_activate)
    app.connect("shutdown", on_shutdown)
    app.run(sys.argv)


if __name__ == "__main__":
    main()
