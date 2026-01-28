"""
Module: process_manager
Layer: android

Android process management - listing, inspecting, killing, and monitoring
system and application processes.
"""

from dataclasses import dataclass
from typing import Dict, Any, List
from abc import ABC, abstractmethod


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class ProcessManagerError(Exception):
    """Base exception for process_manager module."""
    pass


class ProcessNotFoundError(ProcessManagerError):
    """Raised when a requested PID does not exist."""
    pass


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------

@dataclass
class ProcessInfo:
    """Metadata describing an Android process."""
    pid: int
    package: str
    name: str
    cpu_percent: float = 0.0
    memory_mb: float = 0.0
    state: str = "running"
    threads: int = 1


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class ProcessManagerInterface(ABC):
    """
    Abstract interface for Android process management.

    Provides operations for listing, inspecting, spawning, killing,
    and querying resource usage of processes.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the process manager.

        Args:
            config: Module configuration dictionary.
        """
        pass

    @abstractmethod
    def list_processes(self) -> List[ProcessInfo]:
        """
        List all tracked processes.

        Returns:
            List of ProcessInfo for every tracked process.
        """
        pass

    @abstractmethod
    def get_process(self, pid: int) -> ProcessInfo:
        """
        Get metadata for a single process.

        Args:
            pid: Process identifier.

        Returns:
            The matching ProcessInfo.

        Raises:
            ProcessNotFoundError: If the PID does not exist.
        """
        pass

    @abstractmethod
    def kill_process(self, pid: int) -> None:
        """
        Kill (remove) a process by PID.

        Args:
            pid: Process identifier.

        Raises:
            ProcessNotFoundError: If the PID does not exist.
        """
        pass

    @abstractmethod
    def get_processes_by_package(self, package: str) -> List[ProcessInfo]:
        """
        Get all processes belonging to a package.

        Args:
            package: Application package name.

        Returns:
            List of ProcessInfo for the matching package.
        """
        pass

    @abstractmethod
    def add_process(self, pid: int, package: str, name: str) -> ProcessInfo:
        """
        Register a new process.

        Args:
            pid: Process identifier.
            package: Owning application package name.
            name: Human-readable process name.

        Returns:
            The newly created ProcessInfo.
        """
        pass

    @abstractmethod
    def get_resource_usage(self) -> Dict[str, Any]:
        """
        Compute aggregate resource usage across all tracked processes.

        Returns:
            Dictionary with keys ``total_cpu_percent``, ``total_memory_mb``,
            and ``process_count``.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources and clear all tracked processes."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultProcessManager(ProcessManagerInterface):
    """Default in-memory implementation of ProcessManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._processes: Dict[int, ProcessInfo] = {}
        self._initialized = True

    # -- public API -----------------------------------------------------------

    def list_processes(self) -> List[ProcessInfo]:
        if not self._initialized:
            raise ProcessManagerError("Not initialized")
        return list(self._processes.values())

    def get_process(self, pid: int) -> ProcessInfo:
        if not self._initialized:
            raise ProcessManagerError("Not initialized")
        if pid not in self._processes:
            raise ProcessNotFoundError(f"Process not found: {pid}")
        return self._processes[pid]

    def kill_process(self, pid: int) -> None:
        if not self._initialized:
            raise ProcessManagerError("Not initialized")
        if pid not in self._processes:
            raise ProcessNotFoundError(f"Process not found: {pid}")
        del self._processes[pid]

    def get_processes_by_package(self, package: str) -> List[ProcessInfo]:
        if not self._initialized:
            raise ProcessManagerError("Not initialized")
        return [p for p in self._processes.values() if p.package == package]

    def add_process(self, pid: int, package: str, name: str) -> ProcessInfo:
        if not self._initialized:
            raise ProcessManagerError("Not initialized")
        info = ProcessInfo(pid=pid, package=package, name=name)
        self._processes[pid] = info
        return info

    def get_resource_usage(self) -> Dict[str, Any]:
        if not self._initialized:
            raise ProcessManagerError("Not initialized")
        total_cpu = sum(p.cpu_percent for p in self._processes.values())
        total_mem = sum(p.memory_mb for p in self._processes.values())
        return {
            "total_cpu_percent": round(total_cpu, 2),
            "total_memory_mb": round(total_mem, 2),
            "process_count": len(self._processes),
        }

    def cleanup(self) -> None:
        self._processes.clear()
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> ProcessManagerInterface:
    """
    Factory function to create a ProcessManagerInterface instance.

    Args:
        config: Module configuration (optional).

    Returns:
        Configured ProcessManagerInterface implementation.
    """
    return DefaultProcessManager(config or {})
