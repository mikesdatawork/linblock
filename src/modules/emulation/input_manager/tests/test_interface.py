"""
Interface tests for input_manager.

Tests the public API contract for input event injection.
"""

import pytest
from ..interface import (
    InputManagerInterface,
    DefaultInputManager,
    create_interface,
    InputManagerError,
    InputEventType,
    InputEvent,
)


class TestInputManagerInterface:
    """Test suite for InputManagerInterface."""

    @pytest.fixture
    def config(self):
        return {}

    @pytest.fixture
    def manager(self, config):
        return create_interface(config)

    def test_create_with_defaults(self):
        """Interface creates with default config."""
        mgr = create_interface()
        assert mgr is not None
        assert isinstance(mgr, InputManagerInterface)

    def test_send_touch_queues_event(self, manager):
        """send_touch adds a touch event to the queue."""
        manager.send_touch(100, 200, InputEventType.TOUCH_DOWN)
        events = manager.get_pending_events()
        assert len(events) == 1
        assert events[0].event_type == InputEventType.TOUCH_DOWN
        assert events[0].x == 100
        assert events[0].y == 200

    def test_send_key_queues_event(self, manager):
        """send_key adds a key event to the queue."""
        manager.send_key(42, InputEventType.KEY_DOWN)
        events = manager.get_pending_events()
        assert len(events) == 1
        assert events[0].event_type == InputEventType.KEY_DOWN
        assert events[0].keycode == 42

    def test_send_scroll_queues_event(self, manager):
        """send_scroll adds a scroll event to the queue."""
        manager.send_scroll(50, 60, 0, -3)
        events = manager.get_pending_events()
        assert len(events) == 1
        assert events[0].event_type == InputEventType.SCROLL

    def test_get_pending_events_clears_queue(self, manager):
        """get_pending_events drains the event queue."""
        manager.send_touch(10, 20, InputEventType.TOUCH_DOWN)
        manager.send_touch(10, 20, InputEventType.TOUCH_UP)
        events = manager.get_pending_events()
        assert len(events) == 2
        # Second call returns empty
        assert manager.get_pending_events() == []

    def test_multiple_event_types(self, manager):
        """Mixed event types are queued in order."""
        manager.send_touch(0, 0, InputEventType.TOUCH_DOWN)
        manager.send_key(13, InputEventType.KEY_DOWN)
        manager.send_scroll(0, 0, 1, 0)
        events = manager.get_pending_events()
        assert len(events) == 3
        assert events[0].event_type == InputEventType.TOUCH_DOWN
        assert events[1].event_type == InputEventType.KEY_DOWN
        assert events[2].event_type == InputEventType.SCROLL

    def test_cleanup_clears_events(self, manager):
        """cleanup empties the event queue."""
        manager.send_touch(0, 0, InputEventType.TOUCH_DOWN)
        manager.cleanup()
        assert manager.get_pending_events() == []
