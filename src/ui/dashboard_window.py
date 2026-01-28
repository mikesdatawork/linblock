"""Main application window."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk

from .sidebar import Sidebar
from .content_area import ContentArea


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinBlock Emulator")
        self.set_default_size(1024, 768)
        self.set_size_request(1024, 768)

        self._load_css()
        self._build_ui()

    def _load_css(self):
        css_path = None
        import os
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        candidate = os.path.join(base, '..', 'resources', 'css', 'linblock.css')
        if os.path.exists(candidate):
            css_path = candidate

        if css_path:
            provider = Gtk.CssProvider()
            provider.load_from_path(css_path)
            screen = Gdk.Screen.get_default()
            Gtk.StyleContext.add_provider_for_screen(
                screen, provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )

    def _build_ui(self):
        main_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        self.add(main_box)

        self.sidebar = Sidebar()
        main_box.pack_start(self.sidebar, False, False, 0)

        self.content = ContentArea()
        main_box.pack_start(self.content, True, True, 0)

        # Register pages
        from pages.about_page import AboutPage
        from pages.load_os_page import LoadOSPage
        from pages.os_list_page import OSListPage

        self.content.add_page("about", AboutPage())
        self.content.add_page("load_os", LoadOSPage())
        self.content.add_page("os_list", OSListPage())

        self.content.show_page("about")

        # Connect sidebar buttons
        self.sidebar.connect_button("about", lambda: self.content.show_page("about"))
        self.sidebar.connect_button("load_os", lambda: self.content.show_page("load_os"))
        self.sidebar.connect_button("os_list", lambda: self.content.show_page("os_list"))
