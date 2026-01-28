"""
Module: permission_manager
Layer: android

Android permission management - granting, revoking, auditing, and querying
runtime permissions for installed packages.
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List, Tuple
from abc import ABC, abstractmethod
from datetime import datetime, timezone


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class PermissionManagerError(Exception):
    """Base exception for permission_manager module."""
    pass


class PermissionNotFoundError(PermissionManagerError):
    """Raised when a requested permission record does not exist."""
    pass


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class PermissionState(Enum):
    """Possible states of an Android runtime permission."""
    GRANTED = "granted"
    DENIED = "denied"
    ASK = "ask"
    UNSET = "unset"


class PermissionCategory(Enum):
    """Android permission protection levels."""
    NORMAL = "normal"
    DANGEROUS = "dangerous"
    SIGNATURE = "signature"
    PRIVILEGED = "privileged"


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------

@dataclass
class PermissionRecord:
    """A single permission binding for a package."""
    package: str
    permission: str
    state: PermissionState = PermissionState.UNSET
    category: PermissionCategory = PermissionCategory.NORMAL
    grant_time: Optional[str] = None
    last_used: Optional[str] = None
    use_count: int = 0
    background_allowed: bool = False


@dataclass
class AuditEntry:
    """An entry in the permission audit log."""
    timestamp: str
    package: str
    permission: str
    action: str
    result: str
    source: str = "runtime"


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class PermissionManagerInterface(ABC):
    """
    Abstract interface for Android permission management.

    Provides operations for querying, granting, revoking, and auditing
    runtime permissions.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the permission manager.

        Args:
            config: Module configuration dictionary.
        """
        pass

    @abstractmethod
    def get_permission(self, package: str, permission: str) -> PermissionRecord:
        """
        Get a specific permission record.

        Args:
            package: Application package name.
            permission: Android permission string.

        Returns:
            The matching PermissionRecord.

        Raises:
            PermissionNotFoundError: If the record does not exist.
        """
        pass

    @abstractmethod
    def set_permission(self, package: str, permission: str, state: PermissionState) -> None:
        """
        Set the state of a permission for a package.

        Creates the record if it does not yet exist.

        Args:
            package: Application package name.
            permission: Android permission string.
            state: New permission state.
        """
        pass

    @abstractmethod
    def get_app_permissions(self, package: str) -> List[PermissionRecord]:
        """
        Get all permissions for a specific package.

        Args:
            package: Application package name.

        Returns:
            List of PermissionRecord entries belonging to the package.
        """
        pass

    @abstractmethod
    def get_all_permissions(self) -> List[PermissionRecord]:
        """
        Get every permission record across all packages.

        Returns:
            List of all PermissionRecord entries.
        """
        pass

    @abstractmethod
    def record_usage(self, package: str, permission: str) -> None:
        """
        Record that a permission was used by a package at this moment.

        Args:
            package: Application package name.
            permission: Android permission string.

        Raises:
            PermissionNotFoundError: If the permission record does not exist.
        """
        pass

    @abstractmethod
    def get_audit_log(self, package: Optional[str] = None, limit: int = 100) -> List[AuditEntry]:
        """
        Retrieve audit log entries.

        Args:
            package: If provided, filter entries by this package name.
            limit: Maximum number of entries to return.

        Returns:
            List of AuditEntry entries, most recent first.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources and clear all stored data."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultPermissionManager(PermissionManagerInterface):
    """Default in-memory implementation of PermissionManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._permissions: Dict[Tuple[str, str], PermissionRecord] = {}
        self._audit_log: List[AuditEntry] = []
        self._initialized = True

    def _now_iso(self) -> str:
        """Return the current UTC time as an ISO-8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def _add_audit(self, package: str, permission: str, action: str, result: str) -> None:
        """Append an entry to the audit log."""
        self._audit_log.append(
            AuditEntry(
                timestamp=self._now_iso(),
                package=package,
                permission=permission,
                action=action,
                result=result,
            )
        )

    # -- public API -----------------------------------------------------------

    def get_permission(self, package: str, permission: str) -> PermissionRecord:
        if not self._initialized:
            raise PermissionManagerError("Not initialized")
        key = (package, permission)
        if key not in self._permissions:
            raise PermissionNotFoundError(
                f"No record for {package} / {permission}"
            )
        return self._permissions[key]

    def set_permission(self, package: str, permission: str, state: PermissionState) -> None:
        if not self._initialized:
            raise PermissionManagerError("Not initialized")
        key = (package, permission)
        if key in self._permissions:
            self._permissions[key].state = state
            if state == PermissionState.GRANTED:
                self._permissions[key].grant_time = self._now_iso()
        else:
            record = PermissionRecord(
                package=package,
                permission=permission,
                state=state,
                grant_time=self._now_iso() if state == PermissionState.GRANTED else None,
            )
            self._permissions[key] = record
        self._add_audit(package, permission, "set_permission", state.value)

    def get_app_permissions(self, package: str) -> List[PermissionRecord]:
        if not self._initialized:
            raise PermissionManagerError("Not initialized")
        return [r for r in self._permissions.values() if r.package == package]

    def get_all_permissions(self) -> List[PermissionRecord]:
        if not self._initialized:
            raise PermissionManagerError("Not initialized")
        return list(self._permissions.values())

    def record_usage(self, package: str, permission: str) -> None:
        if not self._initialized:
            raise PermissionManagerError("Not initialized")
        key = (package, permission)
        if key not in self._permissions:
            raise PermissionNotFoundError(
                f"No record for {package} / {permission}"
            )
        record = self._permissions[key]
        record.use_count += 1
        record.last_used = self._now_iso()
        self._add_audit(package, permission, "record_usage", "ok")

    def get_audit_log(self, package: Optional[str] = None, limit: int = 100) -> List[AuditEntry]:
        if not self._initialized:
            raise PermissionManagerError("Not initialized")
        entries = self._audit_log
        if package is not None:
            entries = [e for e in entries if e.package == package]
        # Most recent first, capped at limit.
        return list(reversed(entries))[:limit]

    def cleanup(self) -> None:
        self._permissions.clear()
        self._audit_log.clear()
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> PermissionManagerInterface:
    """
    Factory function to create a PermissionManagerInterface instance.

    Args:
        config: Module configuration (optional).

    Returns:
        Configured PermissionManagerInterface implementation.
    """
    return DefaultPermissionManager(config or {})
