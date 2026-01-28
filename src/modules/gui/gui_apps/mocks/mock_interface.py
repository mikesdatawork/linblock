"""
Mock implementation of gui_apps interface.

Use this mock when testing modules that depend on gui_apps.
"""

from typing import Dict, Any, List, Optional
from ..interface import GuiAppsInterface


class MockGuiAppsInterface(GuiAppsInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self._app_manager: Any = None
        self._app_list: List[str] = []
        self._selected_app: Optional[str] = None

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
        self._app_manager = None
        self._app_list.clear()
        self._selected_app = None

    def set_app_manager(self, source: Any) -> None:
        self._record_call("set_app_manager")
        self._app_manager = source

    def refresh_app_list(self) -> None:
        self._record_call("refresh_app_list")

    def get_selected_app(self) -> Optional[str]:
        self._record_call("get_selected_app")
        return self._selected_app

    def select_app(self, package: str) -> None:
        self._record_call("select_app", package=package)
        self._selected_app = package

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._app_manager = None
        self._app_list.clear()
        self._selected_app = None
