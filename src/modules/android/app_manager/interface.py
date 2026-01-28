"""
Module: app_manager
Layer: android

Application lifecycle management - installing, freezing, enabling, disabling,
and force-stopping Android applications.
"""

from enum import Enum
from dataclasses import dataclass
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
from datetime import datetime, timezone


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class AppManagerError(Exception):
    """Base exception for app_manager module."""
    pass


class AppNotFoundError(AppManagerError):
    """Raised when a requested application package is not installed."""
    pass


# -----------------------------------------------------------------------------
# Enums
# -----------------------------------------------------------------------------

class AppState(Enum):
    """Possible lifecycle states of an installed application."""
    INSTALLED = "installed"
    RUNNING = "running"
    STOPPED = "stopped"
    FROZEN = "frozen"
    DISABLED = "disabled"


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------

@dataclass
class AppInfo:
    """Metadata describing an installed Android application."""
    package: str
    name: str
    version: str = "1.0"
    state: AppState = AppState.INSTALLED
    size_mb: float = 0.0
    install_time: Optional[str] = None
    last_active: Optional[str] = None


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class AppManagerInterface(ABC):
    """
    Abstract interface for Android application management.

    Provides operations for installing, listing, freezing/unfreezing,
    enabling/disabling, and force-stopping apps.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the app manager.

        Args:
            config: Module configuration dictionary.
        """
        pass

    @abstractmethod
    def list_apps(self) -> List[AppInfo]:
        """
        List all installed applications.

        Returns:
            List of AppInfo for every installed app.
        """
        pass

    @abstractmethod
    def get_app_info(self, package: str) -> AppInfo:
        """
        Get metadata for a single application.

        Args:
            package: Application package name.

        Returns:
            The matching AppInfo.

        Raises:
            AppNotFoundError: If the package is not installed.
        """
        pass

    @abstractmethod
    def install_app(self, package: str, name: str) -> AppInfo:
        """
        Install an application.

        Args:
            package: Application package name.
            name: Human-readable application name.

        Returns:
            AppInfo for the newly installed app.
        """
        pass

    @abstractmethod
    def freeze_app(self, package: str) -> None:
        """
        Freeze (suspend) an application.

        Args:
            package: Application package name.

        Raises:
            AppNotFoundError: If the package is not installed.
        """
        pass

    @abstractmethod
    def unfreeze_app(self, package: str) -> None:
        """
        Unfreeze a previously frozen application, returning it to INSTALLED state.

        Args:
            package: Application package name.

        Raises:
            AppNotFoundError: If the package is not installed.
        """
        pass

    @abstractmethod
    def enable_app(self, package: str) -> None:
        """
        Enable a disabled application, returning it to INSTALLED state.

        Args:
            package: Application package name.

        Raises:
            AppNotFoundError: If the package is not installed.
        """
        pass

    @abstractmethod
    def disable_app(self, package: str) -> None:
        """
        Disable an application.

        Args:
            package: Application package name.

        Raises:
            AppNotFoundError: If the package is not installed.
        """
        pass

    @abstractmethod
    def force_stop(self, package: str) -> None:
        """
        Force-stop a running application.

        Args:
            package: Application package name.

        Raises:
            AppNotFoundError: If the package is not installed.
        """
        pass

    @abstractmethod
    def get_running_apps(self) -> List[AppInfo]:
        """
        Get all applications currently in the RUNNING state.

        Returns:
            List of AppInfo for running apps.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources and clear all stored data."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultAppManager(AppManagerInterface):
    """Default in-memory implementation of AppManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._apps: Dict[str, AppInfo] = {}
        self._initialized = True

    def _now_iso(self) -> str:
        """Return the current UTC time as an ISO-8601 string."""
        return datetime.now(timezone.utc).isoformat()

    def _require_app(self, package: str) -> AppInfo:
        """Return the AppInfo for *package* or raise AppNotFoundError."""
        if package not in self._apps:
            raise AppNotFoundError(f"App not found: {package}")
        return self._apps[package]

    # -- public API -----------------------------------------------------------

    def list_apps(self) -> List[AppInfo]:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        return list(self._apps.values())

    def get_app_info(self, package: str) -> AppInfo:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        return self._require_app(package)

    def install_app(self, package: str, name: str) -> AppInfo:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        info = AppInfo(
            package=package,
            name=name,
            state=AppState.INSTALLED,
            install_time=self._now_iso(),
        )
        self._apps[package] = info
        return info

    def freeze_app(self, package: str) -> None:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        app = self._require_app(package)
        app.state = AppState.FROZEN

    def unfreeze_app(self, package: str) -> None:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        app = self._require_app(package)
        app.state = AppState.INSTALLED

    def enable_app(self, package: str) -> None:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        app = self._require_app(package)
        app.state = AppState.INSTALLED

    def disable_app(self, package: str) -> None:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        app = self._require_app(package)
        app.state = AppState.DISABLED

    def force_stop(self, package: str) -> None:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        app = self._require_app(package)
        app.state = AppState.STOPPED

    def get_running_apps(self) -> List[AppInfo]:
        if not self._initialized:
            raise AppManagerError("Not initialized")
        return [a for a in self._apps.values() if a.state == AppState.RUNNING]

    def cleanup(self) -> None:
        self._apps.clear()
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> AppManagerInterface:
    """
    Factory function to create an AppManagerInterface instance.

    Args:
        config: Module configuration (optional).

    Returns:
        Configured AppManagerInterface implementation.
    """
    return DefaultAppManager(config or {})
