"""
Module: process_manager
Layer: android

Android process management - listing, inspecting, killing, and monitoring
system and application processes.
"""

from .interface import (
    create_interface,
    ProcessManagerInterface,
    DefaultProcessManager,
    ProcessManagerError,
    ProcessNotFoundError,
    ProcessInfo,
)

__all__ = [
    "create_interface",
    "ProcessManagerInterface",
    "DefaultProcessManager",
    "ProcessManagerError",
    "ProcessNotFoundError",
    "ProcessInfo",
]
