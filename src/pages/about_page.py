"""About page - static information about LinBlock."""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from .page_base import PageBase


class AboutPage(PageBase):
    def __init__(self):
        super().__init__()
        self._build_content()

    def _build_content(self):
        self.add_section_header("LinBlock")
        self.add_text(
            "LinBlock is a custom Android emulator with a minimal, "
            "security-hardened Android OS. It provides full control over "
            "app permissions, network access, and system services."
        )

        self.add_section_header("Features")
        features = [
            "Custom Android 14 (API 34) emulation",
            "GTK3 native Linux interface",
            "Per-app permission control",
            "Process freeze and management",
            "Network isolation and monitoring",
            "No Google Services by default",
            "KVM hardware acceleration",
        ]
        for f in features:
            self.add_text(f"  \u2022 {f}")

        self.add_section_header("Supported Android Versions")
        self.add_text("  \u2022 Android 14 (API 34) - Primary target")

        self.add_section_header("Known Limitations")
        limitations = [
            "x86_64 host architecture required",
            "KVM required for hardware acceleration",
            "Minimum 8GB RAM recommended (12GB+ preferred)",
            "Linux host only (tested on Linux Mint 22.2 / Ubuntu 24.04)",
        ]
        for l in limitations:
            self.add_text(f"  \u2022 {l}")

        self.add_section_header("License")
        self.add_text("License: TBD")

        self.add_section_header("Version")
        self.add_text("Version: 0.1.0 (Development)")
