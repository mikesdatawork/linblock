"""
Module: storage_manager
Layer: emulation

Disk image attachment, overlay creation, and storage lifecycle.
"""

from .interface import (
    create_interface,
    StorageManagerInterface,
    DiskImage,
)

__all__ = [
    "create_interface",
    "StorageManagerInterface",
    "DiskImage",
]
