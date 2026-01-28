"""
Mock implementation of permission_manager interface.

Use this mock when testing modules that depend on permission_manager.
"""

from typing import Dict, Any, Optional, List, Tuple
from ..interface import (
    PermissionManagerInterface,
    PermissionState,
    PermissionRecord,
    AuditEntry,
    PermissionNotFoundError,
)


class MockPermissionManagerInterface(PermissionManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._permissions: Dict[Tuple[str, str], PermissionRecord] = {}
        self._audit_log: List[AuditEntry] = []
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
        self._permissions.clear()
        self._audit_log.clear()

    # -- interface methods ----------------------------------------------------

    def get_permission(self, package: str, permission: str) -> PermissionRecord:
        self._record_call("get_permission", package=package, permission=permission)
        if "get_permission" in self.responses:
            return self.responses["get_permission"]
        key = (package, permission)
        if key not in self._permissions:
            raise PermissionNotFoundError(f"No record for {package} / {permission}")
        return self._permissions[key]

    def set_permission(self, package: str, permission: str, state: PermissionState) -> None:
        self._record_call("set_permission", package=package, permission=permission, state=state)
        key = (package, permission)
        if key in self._permissions:
            self._permissions[key].state = state
        else:
            self._permissions[key] = PermissionRecord(
                package=package, permission=permission, state=state
            )

    def get_app_permissions(self, package: str) -> List[PermissionRecord]:
        self._record_call("get_app_permissions", package=package)
        if "get_app_permissions" in self.responses:
            return self.responses["get_app_permissions"]
        return [r for r in self._permissions.values() if r.package == package]

    def get_all_permissions(self) -> List[PermissionRecord]:
        self._record_call("get_all_permissions")
        if "get_all_permissions" in self.responses:
            return self.responses["get_all_permissions"]
        return list(self._permissions.values())

    def record_usage(self, package: str, permission: str) -> None:
        self._record_call("record_usage", package=package, permission=permission)
        key = (package, permission)
        if key not in self._permissions:
            raise PermissionNotFoundError(f"No record for {package} / {permission}")
        self._permissions[key].use_count += 1

    def get_audit_log(self, package: Optional[str] = None, limit: int = 100) -> List[AuditEntry]:
        self._record_call("get_audit_log", package=package, limit=limit)
        if "get_audit_log" in self.responses:
            return self.responses["get_audit_log"]
        return []

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._permissions.clear()
        self._audit_log.clear()
        self._initialized = False
