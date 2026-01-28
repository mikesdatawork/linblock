"""
Mock implementation of emulator_core interface.

Use this mock when testing modules that depend on emulator_core.
"""

from typing import Dict, Any, List, Optional
from ..interface import EmulatorCoreInterface, VMState, VMInfo


class MockEmulatorCoreInterface(EmulatorCoreInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._state = VMState.STOPPED
        self._initialized = False

    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({
            "method": method,
            "args": kwargs,
        })

    def set_response(self, method: str, response: Any) -> None:
        """Configure response for a method."""
        self.responses[method] = response

    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def clear(self) -> None:
        """Clear recorded calls and responses."""
        self.calls = []
        self.responses = {}

    def initialize(self) -> None:
        self._record_call("initialize")
        self._initialized = True

    def start(self) -> None:
        self._record_call("start")
        self._state = VMState.RUNNING

    def stop(self) -> None:
        self._record_call("stop")
        self._state = VMState.STOPPED

    def pause(self) -> None:
        self._record_call("pause")
        self._state = VMState.PAUSED

    def resume(self) -> None:
        self._record_call("resume")
        self._state = VMState.RUNNING

    def reset(self) -> None:
        self._record_call("reset")
        self._state = VMState.RUNNING

    def get_state(self) -> VMState:
        self._record_call("get_state")
        if "get_state" in self.responses:
            return self.responses["get_state"]
        return self._state

    def get_info(self) -> VMInfo:
        self._record_call("get_info")
        if "get_info" in self.responses:
            return self.responses["get_info"]
        return VMInfo(state=self._state)

    def save_snapshot(self, name: str) -> str:
        self._record_call("save_snapshot", name=name)
        if "save_snapshot" in self.responses:
            return self.responses["save_snapshot"]
        return f"/mock/snapshots/{name}"

    def load_snapshot(self, name: str) -> None:
        self._record_call("load_snapshot", name=name)

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._state = VMState.STOPPED
        self._initialized = False
