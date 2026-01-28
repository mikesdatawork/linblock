"""
Mock implementation of gui_settings interface.

Use this mock when testing modules that depend on gui_settings.
"""

from typing import Dict, Any, List, Optional
from ..interface import GuiSettingsInterface


class MockGuiSettingsInterface(GuiSettingsInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self._current_profile: Optional[Dict] = None

    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({"method": method, "args": kwargs})

    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def reset(self) -> None:
        """Clear recorded calls and state."""
        self.calls = []
        self._current_profile = None

    def load_profile(self, path: str) -> Dict:
        self._record_call("load_profile", path=path)
        self._current_profile = {"name": "mock_profile", "path": path}
        return self._current_profile

    def save_profile(self, path: str, data: Dict) -> None:
        self._record_call("save_profile", path=path)
        self._current_profile = data

    def get_current_profile(self) -> Optional[Dict]:
        self._record_call("get_current_profile")
        return self._current_profile

    def set_field(self, key: str, value: Any) -> None:
        self._record_call("set_field", key=key, value=value)
        if self._current_profile is not None:
            self._current_profile[key] = value

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._current_profile = None
