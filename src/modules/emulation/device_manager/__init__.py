"""
Module: device_manager
Layer: emulation

Virtual device registration, lifecycle, and lookup.
"""

from .interface import (
    create_interface,
    DeviceManagerInterface,
    DeviceType,
    DeviceInfo,
)

__all__ = [
    "create_interface",
    "DeviceManagerInterface",
    "DeviceType",
    "DeviceInfo",
]
