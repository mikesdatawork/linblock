"""
Module: device_manager
Layer: emulation

Virtual device registration, lifecycle, and lookup.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class DeviceManagerError(Exception):
    """Base exception for device_manager module."""
    pass


class DeviceNotFoundError(DeviceManagerError):
    """Raised when a requested device does not exist."""
    pass


class DuplicateDeviceError(DeviceManagerError):
    """Raised when registering a device with a name that already exists."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

class DeviceType(Enum):
    BLOCK = "block"
    DISPLAY = "display"
    INPUT = "input"
    NETWORK = "network"
    SERIAL = "serial"


@dataclass
class DeviceInfo:
    name: str
    device_type: DeviceType
    initialized: bool = False


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class DeviceManagerInterface(ABC):
    """
    Abstract interface for managing virtual devices.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def register_device(self, name: str, device_type: DeviceType) -> DeviceInfo:
        """Register a new virtual device."""
        pass

    @abstractmethod
    def unregister_device(self, name: str) -> None:
        """Remove a registered device."""
        pass

    @abstractmethod
    def get_device(self, name: str) -> DeviceInfo:
        """Return info for a specific device."""
        pass

    @abstractmethod
    def list_devices(self) -> List[DeviceInfo]:
        """Return all registered devices."""
        pass

    @abstractmethod
    def initialize_all(self) -> None:
        """Initialize every registered device."""
        pass

    @abstractmethod
    def reset_device(self, name: str) -> None:
        """Reset a single device to its default state."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release all devices and resources."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultDeviceManager(DeviceManagerInterface):
    """Default implementation of DeviceManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._devices: Dict[str, DeviceInfo] = {}

    def register_device(self, name: str, device_type: DeviceType) -> DeviceInfo:
        if name in self._devices:
            raise DuplicateDeviceError(f"Device '{name}' already registered")
        info = DeviceInfo(name=name, device_type=device_type, initialized=False)
        self._devices[name] = info
        return info

    def unregister_device(self, name: str) -> None:
        if name not in self._devices:
            raise DeviceNotFoundError(f"Device '{name}' not found")
        del self._devices[name]

    def get_device(self, name: str) -> DeviceInfo:
        if name not in self._devices:
            raise DeviceNotFoundError(f"Device '{name}' not found")
        return self._devices[name]

    def list_devices(self) -> List[DeviceInfo]:
        return list(self._devices.values())

    def initialize_all(self) -> None:
        for device in self._devices.values():
            device.initialized = True

    def reset_device(self, name: str) -> None:
        if name not in self._devices:
            raise DeviceNotFoundError(f"Device '{name}' not found")
        self._devices[name].initialized = False

    def cleanup(self) -> None:
        self._devices.clear()


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> DeviceManagerInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)

    Returns:
        Configured DeviceManagerInterface implementation
    """
    return DefaultDeviceManager(config or {})
