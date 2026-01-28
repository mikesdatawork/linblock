"""
Module: gui_display
Layer: gui

Framebuffer rendering and display management.
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


class GuiDisplayError(Exception):
    pass


class GuiDisplayInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass
    @abstractmethod
    def set_framebuffer_source(self, source: Any) -> None: pass
    @abstractmethod
    def start_rendering(self) -> None: pass
    @abstractmethod
    def stop_rendering(self) -> None: pass
    @abstractmethod
    def is_rendering(self) -> bool: pass
    @abstractmethod
    def set_scale(self, scale: float) -> None: pass
    @abstractmethod
    def get_scale(self) -> float: pass
    @abstractmethod
    def capture_screenshot(self, path: str) -> str: pass
    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultGuiDisplay(GuiDisplayInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._framebuffer_source: Any = None
        self._rendering: bool = False
        self._scale: float = 1.0

    def set_framebuffer_source(self, source: Any) -> None:
        self._framebuffer_source = source

    def start_rendering(self) -> None:
        if self._framebuffer_source is None:
            raise GuiDisplayError("No framebuffer source set")
        self._rendering = True

    def stop_rendering(self) -> None:
        self._rendering = False

    def is_rendering(self) -> bool:
        return self._rendering

    def set_scale(self, scale: float) -> None:
        if scale <= 0:
            raise GuiDisplayError(f"Invalid scale: {scale}")
        self._scale = scale

    def get_scale(self) -> float:
        return self._scale

    def capture_screenshot(self, path: str) -> str:
        if not self._rendering:
            raise GuiDisplayError("Not currently rendering")
        return path

    def cleanup(self) -> None:
        self._rendering = False
        self._framebuffer_source = None
        self._scale = 1.0


def create_interface(config: Dict[str, Any] = None) -> GuiDisplayInterface:
    return DefaultGuiDisplay(config or {})
