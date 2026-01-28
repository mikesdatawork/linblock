"""
Interface tests for event_bus.

Tests the public API contract.
"""

import pytest
from ..interface import (
    EventBusInterface,
    DefaultEventBus,
    create_interface,
    EventBusError,
    Event,
    EventHandler,
)


class TestEventBusInterface:
    """Test suite for EventBusInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, EventBusInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        iface = create_interface()
        assert iface is not None
        assert isinstance(iface, EventBusInterface)

    # ------------------------------------------------------------------
    # subscribe
    # ------------------------------------------------------------------

    def test_subscribe_returns_id(self, interface):
        """subscribe returns a non-empty subscription ID string."""
        sub_id = interface.subscribe("test.event", lambda e: None)
        assert isinstance(sub_id, str)
        assert len(sub_id) > 0

    def test_subscribe_multiple_returns_unique_ids(self, interface):
        """Each subscribe call returns a unique ID."""
        id_a = interface.subscribe("test.event", lambda e: None)
        id_b = interface.subscribe("test.event", lambda e: None)
        assert id_a != id_b

    # ------------------------------------------------------------------
    # publish
    # ------------------------------------------------------------------

    def test_publish_delivers_to_handler(self, interface):
        """publish delivers event to subscribed handler."""
        received = []
        interface.subscribe("player.moved", lambda e: received.append(e))

        event = Event(type="player.moved", source="test")
        interface.publish(event)

        assert len(received) == 1
        assert received[0].type == "player.moved"
        assert received[0].source == "test"

    def test_publish_with_payload(self, interface):
        """publish delivers event payload to handler."""
        received = []
        interface.subscribe("score.updated", lambda e: received.append(e))

        event = Event(
            type="score.updated",
            source="game",
            payload={"score": 100, "combo": 4},
        )
        interface.publish(event)

        assert len(received) == 1
        assert received[0].payload["score"] == 100
        assert received[0].payload["combo"] == 4

    def test_publish_no_subscribers_does_not_raise(self, interface):
        """publish with no matching subscribers does not raise."""
        event = Event(type="unknown.event", source="test")
        interface.publish(event)  # should not raise

    # ------------------------------------------------------------------
    # unsubscribe
    # ------------------------------------------------------------------

    def test_unsubscribe_stops_delivery(self, interface):
        """After unsubscribe, handler no longer receives events."""
        received = []
        sub_id = interface.subscribe("block.placed", lambda e: received.append(e))

        # First publish: delivered
        interface.publish(Event(type="block.placed", source="test"))
        assert len(received) == 1

        # Unsubscribe
        interface.unsubscribe(sub_id)

        # Second publish: not delivered
        interface.publish(Event(type="block.placed", source="test"))
        assert len(received) == 1

    def test_unsubscribe_invalid_id_raises(self, interface):
        """unsubscribe with unknown ID raises EventBusError."""
        with pytest.raises(EventBusError):
            interface.unsubscribe("nonexistent-id")

    # ------------------------------------------------------------------
    # Multiple handlers
    # ------------------------------------------------------------------

    def test_multiple_handlers_same_event(self, interface):
        """Multiple handlers for the same event type all receive it."""
        results_a = []
        results_b = []
        interface.subscribe("line.cleared", lambda e: results_a.append(e))
        interface.subscribe("line.cleared", lambda e: results_b.append(e))

        interface.publish(Event(type="line.cleared", source="board"))

        assert len(results_a) == 1
        assert len(results_b) == 1

    # ------------------------------------------------------------------
    # Event type filtering
    # ------------------------------------------------------------------

    def test_event_type_filtering(self, interface):
        """Subscriber to type A does not receive type B events."""
        received_a = []
        received_b = []
        interface.subscribe("type.a", lambda e: received_a.append(e))
        interface.subscribe("type.b", lambda e: received_b.append(e))

        interface.publish(Event(type="type.a", source="test"))

        assert len(received_a) == 1
        assert len(received_b) == 0

    # ------------------------------------------------------------------
    # get_subscriber_count
    # ------------------------------------------------------------------

    def test_get_subscriber_count(self, interface):
        """get_subscriber_count returns correct count."""
        assert interface.get_subscriber_count("game.over") == 0

        interface.subscribe("game.over", lambda e: None)
        assert interface.get_subscriber_count("game.over") == 1

        interface.subscribe("game.over", lambda e: None)
        assert interface.get_subscriber_count("game.over") == 2

    def test_get_subscriber_count_after_unsubscribe(self, interface):
        """get_subscriber_count decreases after unsubscribe."""
        sub_id = interface.subscribe("tick", lambda e: None)
        assert interface.get_subscriber_count("tick") == 1

        interface.unsubscribe(sub_id)
        assert interface.get_subscriber_count("tick") == 0

    # ------------------------------------------------------------------
    # Event dataclass
    # ------------------------------------------------------------------

    def test_event_auto_timestamp(self):
        """Event auto-generates a timestamp when not provided."""
        event = Event(type="test", source="unit")
        assert event.timestamp != ""
        assert len(event.timestamp) > 0

    def test_event_custom_timestamp(self):
        """Event accepts a custom timestamp."""
        event = Event(type="test", source="unit", timestamp="2025-01-01T00:00:00Z")
        assert event.timestamp == "2025-01-01T00:00:00Z"

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------

    def test_cleanup(self, interface):
        """cleanup does not raise."""
        interface.subscribe("x", lambda e: None)
        interface.cleanup()

    def test_subscribe_after_cleanup_raises(self, interface):
        """subscribe raises EventBusError after cleanup."""
        interface.cleanup()
        with pytest.raises(EventBusError):
            interface.subscribe("x", lambda e: None)

    def test_publish_after_cleanup_raises(self, interface):
        """publish raises EventBusError after cleanup."""
        interface.cleanup()
        with pytest.raises(EventBusError):
            interface.publish(Event(type="x", source="test"))

    def test_unsubscribe_after_cleanup_raises(self, interface):
        """unsubscribe raises EventBusError after cleanup."""
        interface.cleanup()
        with pytest.raises(EventBusError):
            interface.unsubscribe("any-id")

    def test_get_subscriber_count_after_cleanup_raises(self, interface):
        """get_subscriber_count raises EventBusError after cleanup."""
        interface.cleanup()
        with pytest.raises(EventBusError):
            interface.get_subscriber_count("x")
