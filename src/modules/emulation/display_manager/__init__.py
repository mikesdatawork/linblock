"""
Module: display_manager
Layer: emulation

Virtual display output, framebuffer capture, and scaling.
"""

from .interface import (
    create_interface,
    DisplayManagerInterface,
    DisplayConfig,
    FrameData,
)

__all__ = [
    "create_interface",
    "DisplayManagerInterface",
    "DisplayConfig",
    "FrameData",
]
