"""
Module: emulator_core
Layer: emulation

CPU virtualization and VM lifecycle management.
"""
from typing import Dict, Any, Optional
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class EmulatorCoreError(Exception):
    """Base exception for emulator_core module."""
    pass


class VMStartError(EmulatorCoreError):
    """Raised when VM cannot be started."""
    pass


class VMNotRunningError(EmulatorCoreError):
    """Raised when operation requires a running VM but VM is not running."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

class VMState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class VMConfig:
    memory_mb: int = 4096
    cpu_cores: int = 4
    use_kvm: bool = True
    kernel_path: Optional[str] = None
    initrd_path: Optional[str] = None


@dataclass
class VMInfo:
    state: VMState = VMState.STOPPED
    pid: Optional[int] = None
    memory_used_mb: int = 0
    cpu_usage_percent: float = 0.0
    uptime_seconds: float = 0.0


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class EmulatorCoreInterface(ABC):
    """
    Abstract interface for CPU virtualization and VM lifecycle management.

    All implementations must inherit from this class.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize module with configuration."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the emulator runtime (allocate resources, verify KVM, etc.)."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the virtual machine."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the virtual machine."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause the running virtual machine."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume a paused virtual machine."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Hard-reset the virtual machine."""
        pass

    @abstractmethod
    def get_state(self) -> VMState:
        """Return the current VM state."""
        pass

    @abstractmethod
    def get_info(self) -> VMInfo:
        """Return detailed VM information."""
        pass

    @abstractmethod
    def save_snapshot(self, name: str) -> str:
        """Save a named snapshot, returning its path."""
        pass

    @abstractmethod
    def load_snapshot(self, name: str) -> None:
        """Restore from a named snapshot."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources held by the module."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultEmulatorCore(EmulatorCoreInterface):
    """Default implementation of EmulatorCoreInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = VMConfig(
            memory_mb=config.get("memory_mb", 4096),
            cpu_cores=config.get("cpu_cores", 4),
            use_kvm=config.get("use_kvm", True),
            kernel_path=config.get("kernel_path"),
            initrd_path=config.get("initrd_path"),
        )
        self._state = VMState.STOPPED
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def start(self) -> None:
        if not self._initialized:
            raise VMStartError("Must call initialize() first")
        if self._state == VMState.RUNNING:
            raise EmulatorCoreError("VM already running")
        self._state = VMState.RUNNING

    def stop(self) -> None:
        if self._state not in (VMState.RUNNING, VMState.PAUSED):
            raise VMNotRunningError("VM is not running")
        self._state = VMState.STOPPED

    def pause(self) -> None:
        if self._state != VMState.RUNNING:
            raise VMNotRunningError("VM is not running")
        self._state = VMState.PAUSED

    def resume(self) -> None:
        if self._state != VMState.PAUSED:
            raise EmulatorCoreError("VM is not paused")
        self._state = VMState.RUNNING

    def reset(self) -> None:
        was_running = self._state in (VMState.RUNNING, VMState.PAUSED)
        self._state = VMState.STOPPED
        if was_running:
            self._state = VMState.RUNNING

    def get_state(self) -> VMState:
        return self._state

    def get_info(self) -> VMInfo:
        return VMInfo(state=self._state)

    def save_snapshot(self, name: str) -> str:
        if self._state not in (VMState.RUNNING, VMState.PAUSED):
            raise VMNotRunningError("VM must be running or paused")
        return f"/snapshots/{name}"

    def load_snapshot(self, name: str) -> None:
        if not self._initialized:
            raise EmulatorCoreError("Must initialize first")

    def cleanup(self) -> None:
        if self._state in (VMState.RUNNING, VMState.PAUSED):
            self._state = VMState.STOPPED
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> EmulatorCoreInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)

    Returns:
        Configured EmulatorCoreInterface implementation
    """
    return DefaultEmulatorCore(config or {})
