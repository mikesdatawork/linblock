"""
Module: network_manager
Layer: emulation

Virtual network configuration, port forwarding, and connectivity.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class NetworkManagerError(Exception):
    """Base exception for network_manager module."""
    pass


class NetworkNotEnabledError(NetworkManagerError):
    """Raised when an operation requires the network to be enabled."""
    pass


class PortForwardError(NetworkManagerError):
    """Raised on port forwarding conflicts or errors."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

class NetworkMode(Enum):
    USER = "user"
    BRIDGE = "bridge"
    NONE = "none"


@dataclass
class NetworkConfig:
    mode: NetworkMode = NetworkMode.USER
    host_forward_ports: List[int] = field(default_factory=list)
    dns_server: str = "8.8.8.8"


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class NetworkManagerInterface(ABC):
    """
    Abstract interface for virtual network management.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def configure(self, net_config: NetworkConfig) -> None:
        """Apply network configuration."""
        pass

    @abstractmethod
    def enable(self) -> None:
        """Enable the virtual network."""
        pass

    @abstractmethod
    def disable(self) -> None:
        """Disable the virtual network."""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Return True if the network is currently enabled."""
        pass

    @abstractmethod
    def add_port_forward(self, host_port: int, guest_port: int) -> None:
        """Forward a host port to a guest port."""
        pass

    @abstractmethod
    def remove_port_forward(self, host_port: int) -> None:
        """Remove a host-port forwarding rule."""
        pass

    @abstractmethod
    def get_config(self) -> NetworkConfig:
        """Return the current network configuration."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Disable the network and release resources."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultNetworkManager(NetworkManagerInterface):
    """Default implementation of NetworkManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._net_config = NetworkConfig()
        self._enabled = False
        self._forwards: Dict[int, int] = {}

    def configure(self, net_config: NetworkConfig) -> None:
        self._net_config = net_config

    def enable(self) -> None:
        if self._net_config.mode == NetworkMode.NONE:
            raise NetworkManagerError("Cannot enable network in NONE mode")
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def is_connected(self) -> bool:
        return self._enabled

    def add_port_forward(self, host_port: int, guest_port: int) -> None:
        if not self._enabled:
            raise NetworkNotEnabledError("Network is not enabled")
        if host_port in self._forwards:
            raise PortForwardError(
                f"Host port {host_port} is already forwarded"
            )
        self._forwards[host_port] = guest_port

    def remove_port_forward(self, host_port: int) -> None:
        if host_port not in self._forwards:
            raise PortForwardError(
                f"No forwarding rule for host port {host_port}"
            )
        del self._forwards[host_port]

    def get_config(self) -> NetworkConfig:
        return self._net_config

    def cleanup(self) -> None:
        self._enabled = False
        self._forwards.clear()


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> NetworkManagerInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)

    Returns:
        Configured NetworkManagerInterface implementation
    """
    return DefaultNetworkManager(config or {})
