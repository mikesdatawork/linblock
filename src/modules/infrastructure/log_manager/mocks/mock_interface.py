"""
Mock implementation of log_manager interface.

Use this mock when testing modules that depend on log_manager.
"""

from typing import Dict, Any, List
import logging
from ..interface import LogManagerInterface


class MockLogManagerInterface(LogManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._initialized = True

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

    def reset(self) -> None:
        """Clear recorded calls and responses."""
        self.calls = []
        self.responses = {}

    def get_logger(self, name: str) -> logging.Logger:
        self._record_call("get_logger", name=name)
        if "get_logger" in self.responses:
            return self.responses["get_logger"]
        return logging.getLogger(f"mock.{name}")

    def set_level(self, level: str) -> None:
        self._record_call("set_level", level=level)

    def add_file_handler(self, path: str) -> None:
        self._record_call("add_file_handler", path=path)

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._initialized = False
