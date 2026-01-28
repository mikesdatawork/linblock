"""
Module: gui_permissions
Layer: gui

Permission display and management UI logic.
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class GuiPermissionsError(Exception):
    pass


class GuiPermissionsInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass
    @abstractmethod
    def set_permission_manager(self, source: Any) -> None: pass
    @abstractmethod
    def show_app_permissions(self, package: str) -> None: pass
    @abstractmethod
    def get_displayed_package(self) -> Optional[str]: pass
    @abstractmethod
    def refresh(self) -> None: pass
    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultGuiPermissions(GuiPermissionsInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._permission_manager: Any = None
        self._displayed_package: Optional[str] = None

    def set_permission_manager(self, source: Any) -> None:
        self._permission_manager = source

    def show_app_permissions(self, package: str) -> None:
        if self._permission_manager is None:
            raise GuiPermissionsError("No permission manager set")
        self._displayed_package = package

    def get_displayed_package(self) -> Optional[str]:
        return self._displayed_package

    def refresh(self) -> None:
        if self._permission_manager is None:
            raise GuiPermissionsError("No permission manager set")

    def cleanup(self) -> None:
        self._permission_manager = None
        self._displayed_package = None


def create_interface(config: Dict[str, Any] = None) -> GuiPermissionsInterface:
    return DefaultGuiPermissions(config or {})
