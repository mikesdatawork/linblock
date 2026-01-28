"""
Mock implementation of event_bus interface.

Use this mock when testing modules that depend on event_bus.
"""

from typing import Dict, Any, List, Callable
from ..interface import EventBusInterface, Event, EventHandler


class MockEventBusInterface(EventBusInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self.published_events: List[Event] = []
        self._next_sub_id: int = 0
        self._initialized = True

    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({
            "method": method,
            "args": kwargs,
        })

    def set_response(self, method: str, response: Any) -> None:
        """Configure response for a method."""
        self.responses[method] = response

    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def reset(self) -> None:
        """Clear recorded calls and responses."""
        self.calls = []
        self.responses = {}
        self.published_events = []

    def subscribe(self, event_type: str, handler: EventHandler) -> str:
        self._record_call("subscribe", event_type=event_type)
        if "subscribe" in self.responses:
            return self.responses["subscribe"]
        self._next_sub_id += 1
        return f"mock-sub-{self._next_sub_id}"

    def unsubscribe(self, subscription_id: str) -> None:
        self._record_call("unsubscribe", subscription_id=subscription_id)

    def publish(self, event: Event) -> None:
        self._record_call("publish", event_type=event.type, source=event.source)
        self.published_events.append(event)

    def get_subscriber_count(self, event_type: str) -> int:
        self._record_call("get_subscriber_count", event_type=event_type)
        if "get_subscriber_count" in self.responses:
            return self.responses["get_subscriber_count"]
        return 0

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._initialized = False
