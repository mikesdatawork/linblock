"""
Module: input_manager
Layer: emulation

Touch, keyboard, and scroll input injection for the emulated device.
"""

from .interface import (
    create_interface,
    InputManagerInterface,
    InputEventType,
    InputEvent,
)

__all__ = [
    "create_interface",
    "InputManagerInterface",
    "InputEventType",
    "InputEvent",
]
