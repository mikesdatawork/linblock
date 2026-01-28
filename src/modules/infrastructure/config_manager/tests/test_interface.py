"""
Interface tests for config_manager.

Tests the public API contract.
"""

import pytest
import yaml
from ..interface import (
    ConfigManagerInterface,
    DefaultConfigManager,
    create_interface,
    ConfigManagerError,
    ConfigNotFoundError,
    ConfigValidationError,
)


class TestConfigManagerInterface:
    """Test suite for ConfigManagerInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {
            "graphics": {"gpu_mode": "auto", "resolution": "1920x1080"},
            "audio": {"volume": 80},
        }

    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)

    # ------------------------------------------------------------------
    # Creation
    # ------------------------------------------------------------------

    def test_create_with_config(self, config):
        """Interface creates successfully with provided config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, ConfigManagerInterface)

    def test_create_with_defaults(self):
        """Interface creates with default (empty) config."""
        iface = create_interface()
        assert iface is not None
        assert isinstance(iface, ConfigManagerInterface)

    # ------------------------------------------------------------------
    # load_config
    # ------------------------------------------------------------------

    def test_load_config_from_file(self, tmp_path):
        """load_config reads YAML file and merges into data."""
        cfg_file = tmp_path / "test_config.yaml"
        cfg_file.write_text(yaml.dump({"engine": {"fps": 60}}))

        iface = create_interface()
        result = iface.load_config(str(cfg_file))

        assert isinstance(result, dict)
        assert result["engine"]["fps"] == 60

    def test_load_config_file_not_found_raises(self):
        """load_config raises ConfigNotFoundError for missing file."""
        iface = create_interface()
        with pytest.raises(ConfigNotFoundError):
            iface.load_config("/nonexistent/path/config.yaml")

    # ------------------------------------------------------------------
    # get
    # ------------------------------------------------------------------

    def test_get_with_dotted_path(self, interface):
        """get retrieves nested value using dotted key path."""
        assert interface.get("graphics.gpu_mode") == "auto"

    def test_get_top_level_key(self, interface):
        """get retrieves top-level dict value."""
        result = interface.get("audio")
        assert isinstance(result, dict)
        assert result["volume"] == 80

    def test_get_returns_default_for_missing_key(self, interface):
        """get returns default when key does not exist."""
        assert interface.get("nonexistent.key", "fallback") == "fallback"

    def test_get_returns_none_default(self, interface):
        """get returns None by default for missing key."""
        assert interface.get("missing") is None

    # ------------------------------------------------------------------
    # set
    # ------------------------------------------------------------------

    def test_set_value(self, interface):
        """set stores a value retrievable by get."""
        interface.set("graphics.fullscreen", True)
        assert interface.get("graphics.fullscreen") is True

    def test_set_creates_intermediate_keys(self):
        """set creates intermediate dicts for deep paths."""
        iface = create_interface()
        iface.set("a.b.c", 42)
        assert iface.get("a.b.c") == 42

    # ------------------------------------------------------------------
    # save_config
    # ------------------------------------------------------------------

    def test_save_config(self, interface, tmp_path):
        """save_config writes current data to YAML file."""
        out_path = tmp_path / "output.yaml"
        interface.save_config(str(out_path))

        with open(str(out_path), 'r') as f:
            saved = yaml.safe_load(f)

        assert saved["graphics"]["gpu_mode"] == "auto"
        assert saved["audio"]["volume"] == 80

    def test_save_config_creates_directories(self, interface, tmp_path):
        """save_config creates parent directories if needed."""
        out_path = tmp_path / "subdir" / "deep" / "output.yaml"
        interface.save_config(str(out_path))
        assert out_path.exists()

    # ------------------------------------------------------------------
    # get_module_config
    # ------------------------------------------------------------------

    def test_get_module_config(self, interface):
        """get_module_config returns section dict for a module name."""
        section = interface.get_module_config("graphics")
        assert section == {"gpu_mode": "auto", "resolution": "1920x1080"}

    def test_get_module_config_missing_returns_empty(self, interface):
        """get_module_config returns empty dict for unknown module."""
        section = interface.get_module_config("nonexistent")
        assert section == {}

    # ------------------------------------------------------------------
    # validate
    # ------------------------------------------------------------------

    def test_validate_returns_true(self, interface):
        """validate returns True for a properly initialized manager."""
        assert interface.validate() is True

    # ------------------------------------------------------------------
    # cleanup
    # ------------------------------------------------------------------

    def test_cleanup(self, interface):
        """cleanup does not raise."""
        interface.cleanup()

    def test_method_after_cleanup_raises(self, interface):
        """Methods raise ConfigManagerError after cleanup."""
        interface.cleanup()
        with pytest.raises(ConfigManagerError):
            interface.get("graphics.gpu_mode")

    def test_load_config_after_cleanup_raises(self, interface, tmp_path):
        """load_config raises after cleanup."""
        interface.cleanup()
        with pytest.raises(ConfigManagerError):
            interface.load_config(str(tmp_path / "any.yaml"))

    def test_set_after_cleanup_raises(self, interface):
        """set raises after cleanup."""
        interface.cleanup()
        with pytest.raises(ConfigManagerError):
            interface.set("key", "value")

    def test_save_config_after_cleanup_raises(self, interface, tmp_path):
        """save_config raises after cleanup."""
        interface.cleanup()
        with pytest.raises(ConfigManagerError):
            interface.save_config(str(tmp_path / "out.yaml"))

    def test_get_module_config_after_cleanup_raises(self, interface):
        """get_module_config raises after cleanup."""
        interface.cleanup()
        with pytest.raises(ConfigManagerError):
            interface.get_module_config("graphics")
