"""
Integration tests for the infrastructure layer.

Tests cross-module interactions within the infrastructure layer.
"""

import pytest
from src.modules.infrastructure.config_manager import create_interface as create_config
from src.modules.infrastructure.log_manager import create_interface as create_log
from src.modules.infrastructure.event_bus import create_interface as create_event_bus, Event


class TestInfrastructureLayerIntegration:
    """Integration tests for infrastructure layer modules working together."""

    @pytest.fixture
    def config_manager(self):
        """Create config manager instance."""
        cm = create_config({"modules": {"log_manager": {"level": "DEBUG"}}})
        yield cm
        cm.cleanup()

    @pytest.fixture
    def log_manager(self):
        """Create log manager instance."""
        lm = create_log()
        yield lm
        lm.cleanup()

    @pytest.fixture
    def event_bus(self):
        """Create event bus instance."""
        eb = create_event_bus()
        yield eb
        eb.cleanup()

    def test_config_drives_log_level(self, config_manager, log_manager):
        """Config manager can provide log level to log manager."""
        # Set a value under log_manager key (not nested under modules)
        config_manager.set("log_manager.level", "DEBUG")
        module_config = config_manager.get_module_config("log_manager")
        assert "level" in module_config

        log_manager.set_level(module_config["level"])
        logger = log_manager.get_logger("test")

        # Logger should be at DEBUG level
        import logging
        assert logger.level == logging.DEBUG

    def test_event_bus_with_config_events(self, config_manager, event_bus):
        """Event bus can publish config change events."""
        received_events = []

        def on_config_change(event: Event):
            received_events.append(event)

        event_bus.subscribe("config_changed", on_config_change)

        # Simulate config change event
        config_manager.set("modules.emulator_core.memory_mb", 4096)

        event = Event(
            type="config_changed",
            source="config_manager",
            payload={"key": "modules.emulator_core.memory_mb", "value": 4096}
        )
        event_bus.publish(event)

        assert len(received_events) == 1
        assert received_events[0].payload["key"] == "modules.emulator_core.memory_mb"
        assert received_events[0].payload["value"] == 4096

    def test_log_manager_logs_event_bus_activity(self, log_manager, event_bus):
        """Log manager can capture event bus activity."""
        import io
        import logging

        logger = log_manager.get_logger("event_bus")

        # Capture log output
        log_capture = io.StringIO()
        handler = logging.StreamHandler(log_capture)
        handler.setLevel(logging.DEBUG)
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)

        # Log event bus activity
        sub_id = event_bus.subscribe("test_event", lambda e: None)
        logger.debug(f"Subscribed to test_event, id={sub_id}")

        event_bus.publish(Event(type="test_event", source="test"))
        logger.debug("Published test_event")

        log_output = log_capture.getvalue()
        assert "Subscribed" in log_output
        assert "Published" in log_output

    def test_full_infrastructure_lifecycle(self, config_manager, log_manager, event_bus):
        """Test full lifecycle with all infrastructure modules."""
        # 1. Load config
        module_config = config_manager.get_module_config("event_bus")

        # 2. Set up logging
        logger = log_manager.get_logger("integration_test")

        # 3. Set up event handling
        events_received = []
        event_bus.subscribe("lifecycle", lambda e: events_received.append(e))

        # 4. Perform operations
        config_manager.set("runtime.started", True)
        event_bus.publish(Event(type="lifecycle", source="test", payload={"state": "started"}))

        # 5. Verify state
        assert config_manager.get("runtime.started") is True
        assert len(events_received) == 1
        assert events_received[0].payload["state"] == "started"

    def test_multiple_subscribers_receive_events(self, event_bus):
        """Multiple subscribers all receive the same event."""
        results = {"a": [], "b": [], "c": []}

        event_bus.subscribe("broadcast", lambda e: results["a"].append(e))
        event_bus.subscribe("broadcast", lambda e: results["b"].append(e))
        event_bus.subscribe("broadcast", lambda e: results["c"].append(e))

        event = Event(type="broadcast", source="test", payload={"msg": "hello"})
        event_bus.publish(event)

        assert len(results["a"]) == 1
        assert len(results["b"]) == 1
        assert len(results["c"]) == 1
        assert all(r[0].payload["msg"] == "hello" for r in results.values())

    def test_config_persistence_across_operations(self, config_manager, tmp_path):
        """Config changes persist when saved and reloaded."""
        config_path = tmp_path / "test_config.yaml"

        # Set some values
        config_manager.set("emulator.memory_mb", 2048)
        config_manager.set("emulator.cpu_cores", 4)
        config_manager.set("gui.theme", "dark")

        # Save
        config_manager.save_config(str(config_path))

        # Create new config manager and load
        new_cm = create_config()
        new_cm.load_config(str(config_path))

        try:
            assert new_cm.get("emulator.memory_mb") == 2048
            assert new_cm.get("emulator.cpu_cores") == 4
            assert new_cm.get("gui.theme") == "dark"
        finally:
            new_cm.cleanup()
