"""
Module: app_manager
Layer: android

Application lifecycle management - installing, freezing, enabling, disabling,
and force-stopping Android applications.
"""

from .interface import (
    create_interface,
    AppManagerInterface,
    DefaultAppManager,
    AppManagerError,
    AppNotFoundError,
    AppState,
    AppInfo,
)

__all__ = [
    "create_interface",
    "AppManagerInterface",
    "DefaultAppManager",
    "AppManagerError",
    "AppNotFoundError",
    "AppState",
    "AppInfo",
]
