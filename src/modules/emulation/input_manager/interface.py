"""
Module: input_manager
Layer: emulation

Touch, keyboard, and scroll input injection for the emulated device.
"""
from typing import Dict, Any, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class InputManagerError(Exception):
    """Base exception for input_manager module."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

class InputEventType(Enum):
    TOUCH_DOWN = "touch_down"
    TOUCH_UP = "touch_up"
    TOUCH_MOVE = "touch_move"
    KEY_DOWN = "key_down"
    KEY_UP = "key_up"
    SCROLL = "scroll"


@dataclass
class InputEvent:
    event_type: InputEventType
    x: int = 0
    y: int = 0
    keycode: int = 0
    timestamp: float = 0.0


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class InputManagerInterface(ABC):
    """
    Abstract interface for input event injection.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def send_touch(self, x: int, y: int, event_type: InputEventType) -> None:
        """Inject a touch event at the given coordinates."""
        pass

    @abstractmethod
    def send_key(self, keycode: int, event_type: InputEventType) -> None:
        """Inject a key event."""
        pass

    @abstractmethod
    def send_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        """Inject a scroll event at the given position with deltas."""
        pass

    @abstractmethod
    def get_pending_events(self) -> List[InputEvent]:
        """Return and clear all queued input events."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release input resources."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultInputManager(InputManagerInterface):
    """Default implementation of InputManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._events: List[InputEvent] = []

    def send_touch(self, x: int, y: int, event_type: InputEventType) -> None:
        self._events.append(InputEvent(
            event_type=event_type,
            x=x,
            y=y,
        ))

    def send_key(self, keycode: int, event_type: InputEventType) -> None:
        self._events.append(InputEvent(
            event_type=event_type,
            keycode=keycode,
        ))

    def send_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self._events.append(InputEvent(
            event_type=InputEventType.SCROLL,
            x=x,
            y=y,
        ))

    def get_pending_events(self) -> List[InputEvent]:
        events = list(self._events)
        self._events.clear()
        return events

    def cleanup(self) -> None:
        self._events.clear()


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> InputManagerInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)

    Returns:
        Configured InputManagerInterface implementation
    """
    return DefaultInputManager(config or {})
