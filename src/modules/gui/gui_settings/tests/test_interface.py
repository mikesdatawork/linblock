"""
Interface tests for gui_settings.

Tests profile settings management with YAML I/O.
"""

import pytest
import yaml
from ..interface import (
    GuiSettingsInterface,
    DefaultGuiSettings,
    create_interface,
    GuiSettingsError,
)


class TestGuiSettingsInterface:
    """Test suite for GuiSettingsInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        interface = create_interface(config)
        assert interface is not None
        assert isinstance(interface, GuiSettingsInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config."""
        interface = create_interface()
        assert interface is not None

    def test_load_profile(self, interface, tmp_path):
        """load_profile reads YAML data from file."""
        profile_data = {"name": "test_os", "ram_mb": 4096}
        profile_path = tmp_path / "test.yaml"
        with open(profile_path, 'w') as f:
            yaml.dump(profile_data, f)

        result = interface.load_profile(str(profile_path))
        assert result["name"] == "test_os"
        assert result["ram_mb"] == 4096

    def test_load_nonexistent_profile_raises(self, interface, tmp_path):
        """load_profile raises for missing file."""
        with pytest.raises(GuiSettingsError, match="Profile not found"):
            interface.load_profile(str(tmp_path / "nonexistent.yaml"))

    def test_save_profile(self, interface, tmp_path):
        """save_profile writes YAML data to file."""
        profile_data = {"name": "saved_os", "gpu_mode": "host"}
        profile_path = tmp_path / "saved.yaml"

        interface.save_profile(str(profile_path), profile_data)

        with open(profile_path, 'r') as f:
            loaded = yaml.safe_load(f)
        assert loaded["name"] == "saved_os"
        assert loaded["gpu_mode"] == "host"

    def test_get_current_profile_default_none(self, interface):
        """get_current_profile returns None before loading."""
        assert interface.get_current_profile() is None

    def test_get_current_profile_after_load(self, interface, tmp_path):
        """get_current_profile returns loaded data."""
        profile_data = {"name": "loaded_os"}
        profile_path = tmp_path / "profile.yaml"
        with open(profile_path, 'w') as f:
            yaml.dump(profile_data, f)

        interface.load_profile(str(profile_path))
        assert interface.get_current_profile() == {"name": "loaded_os"}

    def test_set_field(self, interface, tmp_path):
        """set_field modifies current profile."""
        profile_data = {"name": "editable_os"}
        profile_path = tmp_path / "edit.yaml"
        with open(profile_path, 'w') as f:
            yaml.dump(profile_data, f)

        interface.load_profile(str(profile_path))
        interface.set_field("ram_mb", 8192)
        assert interface.get_current_profile()["ram_mb"] == 8192

    def test_set_field_without_profile_raises(self, interface):
        """set_field raises when no profile loaded."""
        with pytest.raises(GuiSettingsError, match="No profile loaded"):
            interface.set_field("name", "value")

    def test_cleanup(self, interface, tmp_path):
        """cleanup resets profile state."""
        profile_data = {"name": "cleanup_test"}
        profile_path = tmp_path / "cleanup.yaml"
        with open(profile_path, 'w') as f:
            yaml.dump(profile_data, f)

        interface.load_profile(str(profile_path))
        interface.cleanup()
        assert interface.get_current_profile() is None
