"""
Module: gui_display
Layer: gui

Framebuffer rendering and display management.
"""

from .interface import create_interface, GuiDisplayInterface, GuiDisplayError

__all__ = ["create_interface", "GuiDisplayInterface", "GuiDisplayError"]
