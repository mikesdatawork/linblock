"""
Mock implementation of gui_permissions interface.

Use this mock when testing modules that depend on gui_permissions.
"""

from typing import Dict, Any, List, Optional
from ..interface import GuiPermissionsInterface


class MockGuiPermissionsInterface(GuiPermissionsInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self._permission_manager: Any = None
        self._displayed_package: Optional[str] = None

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
        self._permission_manager = None
        self._displayed_package = None

    def set_permission_manager(self, source: Any) -> None:
        self._record_call("set_permission_manager")
        self._permission_manager = source

    def show_app_permissions(self, package: str) -> None:
        self._record_call("show_app_permissions", package=package)
        self._displayed_package = package

    def get_displayed_package(self) -> Optional[str]:
        self._record_call("get_displayed_package")
        return self._displayed_package

    def refresh(self) -> None:
        self._record_call("refresh")

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._permission_manager = None
        self._displayed_package = None
