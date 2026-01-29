"""Main application window."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from .sidebar import Sidebar
from .content_area import ContentArea
from utils.profile_manager import ProfileManager


class MainWindow(Gtk.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.set_title("LinBlock Emulator")
        self.set_default_size(1024, 768)
        self.set_size_request(1024, 768)

        self._profile_manager = ProfileManager()
        self._running_profiles = {}  # profile_name -> RunningOSPage

        self._load_css()
        self._build_ui()
        self._load_saved_profiles()

    def _load_css(self):
        css_path = None
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

        self._about_page = AboutPage()
        self._load_os_page = LoadOSPage()
        self._os_list_page = OSListPage()

        self.content.add_page("about", self._about_page)
        self.content.add_page("load_os", self._load_os_page)
        self.content.add_page("os_list", self._os_list_page)

        self.content.show_page("about")

        # Connect sidebar buttons
        self.sidebar.connect_button("about", lambda: self.content.show_page("about"))
        self.sidebar.connect_button("load_os", lambda: self.content.show_page("load_os"))
        self.sidebar.connect_button("os_list", self._show_os_list)

        # Connect page callbacks
        self._load_os_page.set_on_profile_saved(self._on_profile_saved)
        self._os_list_page.set_on_launch(self._on_profile_launch)
        self._os_list_page.set_on_edit(self._on_profile_edit)
        self._os_list_page.set_on_delete(self._on_profile_deleted)

    def _load_saved_profiles(self):
        """Load saved profiles and add them to the sidebar."""
        profiles = self._profile_manager.list_profiles()
        for profile_name in sorted(profiles):
            self._add_profile_to_sidebar(profile_name)

    def _add_profile_to_sidebar(self, profile_name):
        """Add a profile button to the sidebar."""
        self.sidebar.add_os_button(
            profile_name,
            lambda name=profile_name: self._launch_profile_by_name(name)
        )

    def _remove_profile_from_sidebar(self, profile_name):
        """Remove a profile button from the sidebar."""
        self.sidebar.remove_os_button(profile_name)

        # Remove running page if exists
        if profile_name in self._running_profiles:
            page_name = f"running_{profile_name}"
            self.content.remove_page(page_name)
            del self._running_profiles[profile_name]

    def _on_profile_saved(self, profile):
        """Called when a new profile is saved from Load OS page."""
        # Check if button already exists (update case)
        existing_profiles = self._profile_manager.list_profiles()
        if profile.name not in [p for p in existing_profiles if p != profile.name]:
            # New profile - add to sidebar
            self._add_profile_to_sidebar(profile.name)

        # Refresh OS List page
        self._os_list_page.add_profile(profile)

    def _on_profile_launch(self, profile):
        """Called when Launch button is clicked in OS List page."""
        self._launch_profile(profile)

    def _on_profile_edit(self, profile):
        """Called when Edit button is clicked in OS List page."""
        # TODO: Navigate to Load OS page with profile pre-filled
        self.content.show_page("load_os")

    def _on_profile_deleted(self, profile_name):
        """Called when a profile is deleted from OS List page."""
        self._remove_profile_from_sidebar(profile_name)

    def _launch_profile_by_name(self, profile_name):
        """Launch a profile by its name."""
        try:
            profile = self._profile_manager.load_profile(profile_name)
            self._launch_profile(profile)
        except Exception as e:
            dialog = Gtk.MessageDialog(
                transient_for=self,
                message_type=Gtk.MessageType.ERROR,
                buttons=Gtk.ButtonsType.OK,
                text=f"Failed to load profile: {e}",
            )
            dialog.run()
            dialog.destroy()

    def _launch_profile(self, profile):
        """Launch a profile - show the Running OS page."""
        from pages.running_os_page import RunningOSPage

        page_name = f"running_{profile.name}"

        # Check if already running
        if profile.name in self._running_profiles:
            # Just switch to existing page
            self.content.show_page(page_name)
            return

        # Create new Running OS page
        running_page = RunningOSPage(profile_name=profile.name)
        running_page.configure_for_profile(profile.to_dict())

        # Add to content area
        self.content.add_page(page_name, running_page)
        running_page.show_all()

        # Track running profile
        self._running_profiles[profile.name] = running_page

        # Switch to the running page
        self.content.show_page(page_name)

    def _show_os_list(self):
        """Show OS List page and refresh it."""
        self._os_list_page.refresh_profiles()
        self.content.show_page("os_list")
