"""
Module: emulator_core
Layer: emulation

CPU virtualization and VM lifecycle management.
"""

from .interface import (
    create_interface,
    EmulatorCoreInterface,
    VMState,
    VMConfig,
    VMInfo,
)

__all__ = [
    "create_interface",
    "EmulatorCoreInterface",
    "VMState",
    "VMConfig",
    "VMInfo",
]
