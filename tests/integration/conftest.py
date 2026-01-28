"""Integration test fixtures. Test cross-module interactions."""
import pytest


@pytest.fixture
def infrastructure_config():
    """Config for infrastructure layer integration tests."""
    return {
        "config_manager": {"config_dir": "/tmp/linblock-test/config"},
        "log_manager": {"log_level": "DEBUG", "log_dir": "/tmp/linblock-test/logs"},
        "event_bus": {"async_dispatch": False},
    }
