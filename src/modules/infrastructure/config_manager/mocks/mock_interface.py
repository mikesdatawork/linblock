"""
Mock implementation of config_manager interface.

Use this mock when testing modules that depend on config_manager.
"""

from typing import Dict, Any, List
from ..interface import ConfigManagerInterface


class MockConfigManagerInterface(ConfigManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._data: Dict[str, Any] = dict(self.config)
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

    def load_config(self, path: str) -> Dict[str, Any]:
        self._record_call("load_config", path=path)
        if "load_config" in self.responses:
            return self.responses["load_config"]
        return dict(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        self._record_call("get", key=key, default=default)
        if "get" in self.responses:
            return self.responses["get"]
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._record_call("set", key=key, value=value)
        self._data[key] = value

    def save_config(self, path: str) -> None:
        self._record_call("save_config", path=path)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        self._record_call("get_module_config", module_name=module_name)
        if "get_module_config" in self.responses:
            return self.responses["get_module_config"]
        return self._data.get(module_name, {})

    def validate(self) -> bool:
        self._record_call("validate")
        if "validate" in self.responses:
            return self.responses["validate"]
        return True

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._initialized = False
