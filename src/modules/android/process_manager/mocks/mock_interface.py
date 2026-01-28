"""
Mock implementation of process_manager interface.

Use this mock when testing modules that depend on process_manager.
"""

from typing import Dict, Any, List
from ..interface import (
    ProcessManagerInterface,
    ProcessInfo,
    ProcessNotFoundError,
)


class MockProcessManagerInterface(ProcessManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._processes: Dict[int, ProcessInfo] = {}
        self._initialized = True

    # -- call tracking helpers ------------------------------------------------

    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({"method": method, "args": kwargs})

    def set_response(self, method: str, response: Any) -> None:
        """Configure a canned response for a method."""
        self.responses[method] = response

    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method name."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def reset(self) -> None:
        """Clear recorded calls and canned responses."""
        self.calls = []
        self.responses = {}
        self._processes.clear()

    # -- interface methods ----------------------------------------------------

    def list_processes(self) -> List[ProcessInfo]:
        self._record_call("list_processes")
        if "list_processes" in self.responses:
            return self.responses["list_processes"]
        return list(self._processes.values())

    def get_process(self, pid: int) -> ProcessInfo:
        self._record_call("get_process", pid=pid)
        if "get_process" in self.responses:
            return self.responses["get_process"]
        if pid not in self._processes:
            raise ProcessNotFoundError(f"Process not found: {pid}")
        return self._processes[pid]

    def kill_process(self, pid: int) -> None:
        self._record_call("kill_process", pid=pid)
        if pid not in self._processes:
            raise ProcessNotFoundError(f"Process not found: {pid}")
        del self._processes[pid]

    def get_processes_by_package(self, package: str) -> List[ProcessInfo]:
        self._record_call("get_processes_by_package", package=package)
        if "get_processes_by_package" in self.responses:
            return self.responses["get_processes_by_package"]
        return [p for p in self._processes.values() if p.package == package]

    def add_process(self, pid: int, package: str, name: str) -> ProcessInfo:
        self._record_call("add_process", pid=pid, package=package, name=name)
        if "add_process" in self.responses:
            return self.responses["add_process"]
        info = ProcessInfo(pid=pid, package=package, name=name)
        self._processes[pid] = info
        return info

    def get_resource_usage(self) -> Dict[str, Any]:
        self._record_call("get_resource_usage")
        if "get_resource_usage" in self.responses:
            return self.responses["get_resource_usage"]
        total_cpu = sum(p.cpu_percent for p in self._processes.values())
        total_mem = sum(p.memory_mb for p in self._processes.values())
        return {
            "total_cpu_percent": round(total_cpu, 2),
            "total_memory_mb": round(total_mem, 2),
            "process_count": len(self._processes),
        }

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._processes.clear()
        self._initialized = False
