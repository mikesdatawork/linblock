"""
Module: gui_settings
Layer: gui

Profile settings management with YAML I/O.
"""

from .interface import create_interface, GuiSettingsInterface, GuiSettingsError

__all__ = ["create_interface", "GuiSettingsInterface", "GuiSettingsError"]
