"""
Module: display_manager
Layer: emulation

Virtual display output, framebuffer capture, and scaling.
"""
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from abc import ABC, abstractmethod
import time


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class DisplayManagerError(Exception):
    """Base exception for display_manager module."""
    pass


class DisplayNotConfiguredError(DisplayManagerError):
    """Raised when operations are attempted before configure()."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

@dataclass
class DisplayConfig:
    width: int = 1080
    height: int = 1920
    scale: float = 1.0
    fps_target: int = 30


@dataclass
class FrameData:
    width: int
    height: int
    data: bytes
    timestamp: float


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class DisplayManagerInterface(ABC):
    """
    Abstract interface for virtual display management.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def configure(self, display_config: DisplayConfig) -> None:
        """Apply display configuration."""
        pass

    @abstractmethod
    def get_frame(self) -> Optional[FrameData]:
        """Capture the current framebuffer contents."""
        pass

    @abstractmethod
    def get_resolution(self) -> Tuple[int, int]:
        """Return (width, height) of the display."""
        pass

    @abstractmethod
    def set_scale(self, scale: float) -> None:
        """Update display scale factor."""
        pass

    @abstractmethod
    def get_fps(self) -> float:
        """Return the current frames-per-second rate."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release display resources."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultDisplayManager(DisplayManagerInterface):
    """Default implementation of DisplayManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._display_config: Optional[DisplayConfig] = None
        self._frame_count: int = 0
        self._start_time: Optional[float] = None

    def configure(self, display_config: DisplayConfig) -> None:
        self._display_config = display_config
        self._frame_count = 0
        self._start_time = time.monotonic()

    def get_frame(self) -> Optional[FrameData]:
        if self._display_config is None:
            return None
        self._frame_count += 1
        w = int(self._display_config.width * self._display_config.scale)
        h = int(self._display_config.height * self._display_config.scale)
        # Placeholder: 4 bytes per pixel (RGBA), all zeros
        data = bytes(w * h * 4)
        return FrameData(
            width=w,
            height=h,
            data=data,
            timestamp=time.monotonic(),
        )

    def get_resolution(self) -> Tuple[int, int]:
        if self._display_config is None:
            raise DisplayNotConfiguredError("Display not configured")
        return (self._display_config.width, self._display_config.height)

    def set_scale(self, scale: float) -> None:
        if self._display_config is None:
            raise DisplayNotConfiguredError("Display not configured")
        self._display_config.scale = scale

    def get_fps(self) -> float:
        if self._start_time is None or self._frame_count == 0:
            return 0.0
        elapsed = time.monotonic() - self._start_time
        if elapsed <= 0:
            return 0.0
        return self._frame_count / elapsed

    def cleanup(self) -> None:
        self._display_config = None
        self._frame_count = 0
        self._start_time = None


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> DisplayManagerInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)

    Returns:
        Configured DisplayManagerInterface implementation
    """
    return DefaultDisplayManager(config or {})
