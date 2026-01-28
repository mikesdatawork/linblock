"""
Interface tests for android_image.

Tests the public API contract for loading, validating,
and querying Android system images.
"""

import os
import pytest
from ..interface import (
    AndroidImageInterface,
    DefaultAndroidImage,
    create_interface,
    AndroidImageError,
    ImageNotFoundError,
    ImageInfo,
)


class TestAndroidImageInterface:
    """Test suite for AndroidImageInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)

    # -- creation tests -------------------------------------------------------

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, AndroidImageInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config when None is passed."""
        iface = create_interface()
        assert iface is not None

    # -- load_image tests -----------------------------------------------------

    def test_load_image_success(self, interface, tmp_path):
        """load_image returns ImageInfo for a valid .img file."""
        img = tmp_path / "system.img"
        img.write_bytes(b"\x00" * 2048)
        info = interface.load_image(str(img))
        assert isinstance(info, ImageInfo)
        assert info.path == str(img)

    def test_load_image_not_found_raises(self, interface, tmp_path):
        """load_image raises ImageNotFoundError for missing path."""
        missing = tmp_path / "nonexistent.img"
        with pytest.raises(ImageNotFoundError):
            interface.load_image(str(missing))

    # -- validate_image tests -------------------------------------------------

    def test_validate_image_returns_true_for_valid_file(self, interface, tmp_path):
        """validate_image returns True for an existing non-empty file."""
        img = tmp_path / "valid.img"
        img.write_bytes(b"\x01" * 512)
        assert interface.validate_image(str(img)) is True

    def test_validate_image_returns_false_for_missing_file(self, interface, tmp_path):
        """validate_image returns False when path does not exist."""
        missing = tmp_path / "missing.img"
        assert interface.validate_image(str(missing)) is False

    def test_validate_image_returns_false_for_empty_file(self, interface, tmp_path):
        """validate_image returns False for a zero-byte file."""
        empty = tmp_path / "empty.img"
        empty.write_bytes(b"")
        assert interface.validate_image(str(empty)) is False

    # -- get_image_info tests -------------------------------------------------

    def test_get_image_info_none_before_load(self, interface):
        """get_image_info returns None when no image has been loaded."""
        assert interface.get_image_info() is None

    def test_get_image_info_after_load(self, interface, tmp_path):
        """get_image_info returns the loaded ImageInfo after load_image."""
        img = tmp_path / "system.img"
        img.write_bytes(b"\x00" * 4096)
        loaded = interface.load_image(str(img))
        current = interface.get_image_info()
        assert current is loaded
        assert current.path == str(img)

    # -- list_available_images tests ------------------------------------------

    def test_list_available_images_finds_img_files(self, interface, tmp_path):
        """list_available_images returns entries for .img files in directory."""
        for name in ("a.img", "b.img", "c.txt"):
            (tmp_path / name).write_bytes(b"\xAA" * 128)
        images = interface.list_available_images(str(tmp_path))
        paths = [i.path for i in images]
        assert len(images) == 2
        assert str(tmp_path / "a.img") in paths
        assert str(tmp_path / "b.img") in paths

    def test_list_available_images_empty_directory(self, interface, tmp_path):
        """list_available_images returns empty list for directory with no .img files."""
        (tmp_path / "readme.txt").write_text("hello")
        images = interface.list_available_images(str(tmp_path))
        assert images == []

    # -- cleanup tests --------------------------------------------------------

    def test_cleanup_clears_current_image(self, interface, tmp_path):
        """After cleanup, the module is no longer usable."""
        img = tmp_path / "system.img"
        img.write_bytes(b"\x00" * 1024)
        interface.load_image(str(img))
        interface.cleanup()
        with pytest.raises(AndroidImageError):
            interface.get_image_info()

    def test_method_after_cleanup_raises(self, interface):
        """Methods raise AndroidImageError after cleanup."""
        interface.cleanup()
        with pytest.raises(AndroidImageError):
            interface.load_image("/fake/path")
