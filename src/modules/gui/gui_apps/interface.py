"""
Module: gui_apps
Layer: gui

Application list display and selection management.
"""
from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod


class GuiAppsError(Exception):
    pass


class GuiAppsInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass
    @abstractmethod
    def set_app_manager(self, source: Any) -> None: pass
    @abstractmethod
    def refresh_app_list(self) -> None: pass
    @abstractmethod
    def get_selected_app(self) -> Optional[str]: pass
    @abstractmethod
    def select_app(self, package: str) -> None: pass
    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultGuiApps(GuiAppsInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._app_manager: Any = None
        self._app_list: List[str] = []
        self._selected_app: Optional[str] = None

    def set_app_manager(self, source: Any) -> None:
        self._app_manager = source

    def refresh_app_list(self) -> None:
        if self._app_manager is None:
            raise GuiAppsError("No app manager set")
        if hasattr(self._app_manager, 'list_apps'):
            self._app_list = self._app_manager.list_apps()
        else:
            self._app_list = []

    def get_selected_app(self) -> Optional[str]:
        return self._selected_app

    def select_app(self, package: str) -> None:
        self._selected_app = package

    def cleanup(self) -> None:
        self._app_manager = None
        self._app_list.clear()
        self._selected_app = None


def create_interface(config: Dict[str, Any] = None) -> GuiAppsInterface:
    return DefaultGuiApps(config or {})
