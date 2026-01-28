"""
Module: permission_manager
Layer: android

Android permission management - granting, revoking, auditing, and querying
runtime permissions for installed packages.
"""

from .interface import (
    create_interface,
    PermissionManagerInterface,
    DefaultPermissionManager,
    PermissionManagerError,
    PermissionNotFoundError,
    PermissionState,
    PermissionCategory,
    PermissionRecord,
    AuditEntry,
)

__all__ = [
    "create_interface",
    "PermissionManagerInterface",
    "DefaultPermissionManager",
    "PermissionManagerError",
    "PermissionNotFoundError",
    "PermissionState",
    "PermissionCategory",
    "PermissionRecord",
    "AuditEntry",
]
