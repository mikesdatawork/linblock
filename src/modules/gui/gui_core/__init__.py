"""
Module: gui_core
Layer: gui

Window management and page switching.
"""

from .interface import create_interface, GuiCoreInterface, GuiCoreError

__all__ = ["create_interface", "GuiCoreInterface", "GuiCoreError"]
