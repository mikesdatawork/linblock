"""
Interface tests for log_manager.

Tests the public API contract.
"""

import logging
import pytest
from ..interface import (
    LogManagerInterface,
    DefaultLogManager,
    create_interface,
    LogManagerError,
)


class TestLogManagerInterface:
    """Test suite for LogManagerInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {"log_level": "DEBUG"}

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
        assert isinstance(iface, LogManagerInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        iface = create_interface()
        assert iface is not None
        assert isinstance(iface, LogManagerInterface)

    # ------------------------------------------------------------------
    # get_logger
    # ------------------------------------------------------------------

    def test_get_logger_returns_logger(self, interface):
        """get_logger returns a logging.Logger instance."""
        logger = interface.get_logger("test_module")
        assert isinstance(logger, logging.Logger)

    def test_get_logger_same_name_returns_same_instance(self, interface):
        """get_logger returns the same Logger for the same name."""
        logger_a = interface.get_logger("renderer")
        logger_b = interface.get_logger("renderer")
        assert logger_a is logger_b

    def test_get_logger_different_names_return_different(self, interface):
        """get_logger returns different loggers for different names."""
        logger_a = interface.get_logger("audio")
        logger_b = interface.get_logger("physics")
        assert logger_a is not logger_b

    def test_get_logger_name_prefixed(self, interface):
        """Logger name is prefixed with 'linblock.'."""
        logger = interface.get_logger("gameplay")
        assert logger.name == "linblock.gameplay"

    # ------------------------------------------------------------------
    # set_level
    # ------------------------------------------------------------------

    def test_set_level_changes_level(self, interface):
        """set_level updates the level on existing loggers."""
        logger = interface.get_logger("level_test")
        interface.set_level("WARNING")
        assert logger.level == logging.WARNING

    def test_set_level_case_insensitive(self, interface):
        """set_level accepts lowercase level strings."""
        interface.get_logger("ci_test")
        interface.set_level("error")
        # No exception means success; verify via logger level
        logger = interface.get_logger("ci_test")
        assert logger.level == logging.ERROR

    # ------------------------------------------------------------------
    # add_file_handler
    # ------------------------------------------------------------------

    def test_add_file_handler(self, interface, tmp_path):
        """add_file_handler creates a file handler writing logs."""
        log_file = tmp_path / "test.log"
        logger = interface.get_logger("file_test")
        interface.add_file_handler(str(log_file))

        logger.info("hello from test")

        # Flush handlers
        for h in logger.handlers:
            h.flush()

        contents = log_file.read_text()
        assert "hello from test" in contents

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------

    def test_cleanup(self, interface):
        """cleanup does not raise."""
        interface.get_logger("cleanup_test")
        interface.cleanup()

    def test_get_logger_after_cleanup_raises(self, interface):
        """get_logger raises LogManagerError after cleanup."""
        interface.cleanup()
        with pytest.raises(LogManagerError):
            interface.get_logger("post_cleanup")

    def test_set_level_after_cleanup_raises(self, interface):
        """set_level raises LogManagerError after cleanup."""
        interface.cleanup()
        with pytest.raises(LogManagerError):
            interface.set_level("DEBUG")

    def test_add_file_handler_after_cleanup_raises(self, interface, tmp_path):
        """add_file_handler raises LogManagerError after cleanup."""
        interface.cleanup()
        with pytest.raises(LogManagerError):
            interface.add_file_handler(str(tmp_path / "nope.log"))
