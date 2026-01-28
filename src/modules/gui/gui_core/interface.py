"""
Module: gui_core
Layer: gui

Window management and page switching.
"""
from typing import Dict, Any, List
from abc import ABC, abstractmethod


class GuiCoreError(Exception):
    pass


class GuiCoreInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass
    @abstractmethod
    def initialize(self) -> None: pass
    @abstractmethod
    def register_page(self, name: str, widget: Any) -> None: pass
    @abstractmethod
    def switch_page(self, name: str) -> None: pass
    @abstractmethod
    def get_current_page(self) -> str: pass
    @abstractmethod
    def list_pages(self) -> List[str]: pass
    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultGuiCore(GuiCoreInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._pages: Dict[str, Any] = {}
        self._current_page: str = ""
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def register_page(self, name: str, widget: Any) -> None:
        if not self._initialized:
            raise GuiCoreError("Not initialized")
        self._pages[name] = widget
        if not self._current_page:
            self._current_page = name

    def switch_page(self, name: str) -> None:
        if not self._initialized:
            raise GuiCoreError("Not initialized")
        if name not in self._pages:
            raise GuiCoreError(f"Page not found: {name}")
        self._current_page = name

    def get_current_page(self) -> str:
        return self._current_page

    def list_pages(self) -> List[str]:
        return list(self._pages.keys())

    def cleanup(self) -> None:
        self._pages.clear()
        self._current_page = ""
        self._initialized = False


def create_interface(config: Dict[str, Any] = None) -> GuiCoreInterface:
    return DefaultGuiCore(config or {})
