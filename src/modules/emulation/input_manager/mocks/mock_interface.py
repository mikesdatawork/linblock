"""
Mock implementation of input_manager interface.

Use this mock when testing modules that depend on input_manager.
"""

from typing import Dict, Any, List
from ..interface import InputManagerInterface, InputEventType, InputEvent


class MockInputManagerInterface(InputManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._events: List[InputEvent] = []

    def _record_call(self, method: str, **kwargs) -> None:
        self.calls.append({"method": method, "args": kwargs})

    def set_response(self, method: str, response: Any) -> None:
        self.responses[method] = response

    def get_calls(self, method: str = None) -> List[Dict]:
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def clear(self) -> None:
        self.calls = []
        self.responses = {}

    def send_touch(self, x: int, y: int, event_type: InputEventType) -> None:
        self._record_call("send_touch", x=x, y=y, event_type=event_type)
        self._events.append(InputEvent(event_type=event_type, x=x, y=y))

    def send_key(self, keycode: int, event_type: InputEventType) -> None:
        self._record_call("send_key", keycode=keycode, event_type=event_type)
        self._events.append(InputEvent(event_type=event_type, keycode=keycode))

    def send_scroll(self, x: int, y: int, dx: int, dy: int) -> None:
        self._record_call("send_scroll", x=x, y=y, dx=dx, dy=dy)
        self._events.append(InputEvent(event_type=InputEventType.SCROLL, x=x, y=y))

    def get_pending_events(self) -> List[InputEvent]:
        self._record_call("get_pending_events")
        if "get_pending_events" in self.responses:
            return self.responses["get_pending_events"]
        events = list(self._events)
        self._events.clear()
        return events

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._events.clear()
