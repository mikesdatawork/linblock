"""
Mock implementation of app_manager interface.

Use this mock when testing modules that depend on app_manager.
"""

from typing import Dict, Any, Optional, List
from ..interface import (
    AppManagerInterface,
    AppState,
    AppInfo,
    AppNotFoundError,
)


class MockAppManagerInterface(AppManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._apps: Dict[str, AppInfo] = {}
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
        self._apps.clear()

    # -- interface methods ----------------------------------------------------

    def list_apps(self) -> List[AppInfo]:
        self._record_call("list_apps")
        if "list_apps" in self.responses:
            return self.responses["list_apps"]
        return list(self._apps.values())

    def get_app_info(self, package: str) -> AppInfo:
        self._record_call("get_app_info", package=package)
        if "get_app_info" in self.responses:
            return self.responses["get_app_info"]
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        return self._apps[package]

    def install_app(self, package: str, name: str) -> AppInfo:
        self._record_call("install_app", package=package, name=name)
        if "install_app" in self.responses:
            return self.responses["install_app"]
        info = AppInfo(package=package, name=name, state=AppState.INSTALLED)
        self._apps[package] = info
        return info

    def freeze_app(self, package: str) -> None:
        self._record_call("freeze_app", package=package)
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        self._apps[package].state = AppState.FROZEN

    def unfreeze_app(self, package: str) -> None:
        self._record_call("unfreeze_app", package=package)
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        self._apps[package].state = AppState.INSTALLED

    def enable_app(self, package: str) -> None:
        self._record_call("enable_app", package=package)
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        self._apps[package].state = AppState.INSTALLED

    def disable_app(self, package: str) -> None:
        self._record_call("disable_app", package=package)
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        self._apps[package].state = AppState.DISABLED

    def force_stop(self, package: str) -> None:
        self._record_call("force_stop", package=package)
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        self._apps[package].state = AppState.STOPPED

    def get_running_apps(self) -> List[AppInfo]:
        self._record_call("get_running_apps")
        if "get_running_apps" in self.responses:
            return self.responses["get_running_apps"]
        return [a for a in self._apps.values() if a.state == AppState.RUNNING]

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._apps.clear()
        self._initialized = False
