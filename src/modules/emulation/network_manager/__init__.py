"""
Module: network_manager
Layer: emulation

Virtual network configuration, port forwarding, and connectivity.
"""

from .interface import (
    create_interface,
    NetworkManagerInterface,
    NetworkMode,
    NetworkConfig,
)

__all__ = [
    "create_interface",
    "NetworkManagerInterface",
    "NetworkMode",
    "NetworkConfig",
]
