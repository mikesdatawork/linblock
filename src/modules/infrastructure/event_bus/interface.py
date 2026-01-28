"""
Module: event_bus
Layer: infrastructure

Inter-module event messaging system.
"""

from typing import Dict, Any, Callable, List, Optional
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import uuid
from datetime import datetime, timezone


class EventBusError(Exception):
    pass


@dataclass
class Event:
    type: str
    source: str
    timestamp: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


EventHandler = Callable[[Event], None]


class EventBusInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass

    @abstractmethod
    def subscribe(self, event_type: str, handler: EventHandler) -> str:
        """Subscribe to event type. Returns subscription ID."""
        pass

    @abstractmethod
    def unsubscribe(self, subscription_id: str) -> None:
        """Remove subscription by ID."""
        pass

    @abstractmethod
    def publish(self, event: Event) -> None:
        """Publish event to all matching subscribers."""
        pass

    @abstractmethod
    def get_subscriber_count(self, event_type: str) -> int:
        """Get count of subscribers for event type."""
        pass

    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultEventBus(EventBusInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._subscriptions: Dict[str, Dict[str, EventHandler]] = {}
        self._initialized = True

    def subscribe(self, event_type: str, handler: EventHandler) -> str:
        if not self._initialized:
            raise EventBusError("Bus not initialized")
        sub_id = str(uuid.uuid4())
        if event_type not in self._subscriptions:
            self._subscriptions[event_type] = {}
        self._subscriptions[event_type][sub_id] = handler
        return sub_id

    def unsubscribe(self, subscription_id: str) -> None:
        if not self._initialized:
            raise EventBusError("Bus not initialized")
        for event_type in self._subscriptions:
            if subscription_id in self._subscriptions[event_type]:
                del self._subscriptions[event_type][subscription_id]
                return
        raise EventBusError(f"Subscription not found: {subscription_id}")

    def publish(self, event: Event) -> None:
        if not self._initialized:
            raise EventBusError("Bus not initialized")
        handlers = self._subscriptions.get(event.type, {})
        for handler in handlers.values():
            handler(event)

    def get_subscriber_count(self, event_type: str) -> int:
        if not self._initialized:
            raise EventBusError("Bus not initialized")
        return len(self._subscriptions.get(event_type, {}))

    def cleanup(self) -> None:
        self._subscriptions.clear()
        self._initialized = False


def create_interface(config: Dict[str, Any] = None) -> EventBusInterface:
    return DefaultEventBus(config or {})
