"""
Interface tests for storage_manager.

Tests the public API contract for disk image and storage management.
"""

import pytest
from ..interface import (
    StorageManagerInterface,
    DefaultStorageManager,
    create_interface,
    StorageManagerError,
    ImageNotFoundError,
    DuplicateImageError,
    DiskImage,
)


class TestStorageManagerInterface:
    """Test suite for StorageManagerInterface."""

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
        assert isinstance(mgr, StorageManagerInterface)

    def test_attach_image(self, manager):
        """attach_image adds the image to the manager."""
        img = DiskImage(path="/images/system.raw", size_mb=4096)
        manager.attach_image(img)
        assert len(manager.list_images()) == 1

    def test_attach_duplicate_raises(self, manager):
        """Attaching the same path twice raises DuplicateImageError."""
        img = DiskImage(path="/images/system.raw")
        manager.attach_image(img)
        with pytest.raises(DuplicateImageError):
            manager.attach_image(img)

    def test_detach_image(self, manager):
        """detach_image removes an attached image."""
        img = DiskImage(path="/images/data.raw")
        manager.attach_image(img)
        manager.detach_image("/images/data.raw")
        assert manager.list_images() == []

    def test_detach_not_found_raises(self, manager):
        """Detaching a non-existent image raises ImageNotFoundError."""
        with pytest.raises(ImageNotFoundError):
            manager.detach_image("/nope")

    def test_get_image_info(self, manager):
        """get_image_info returns the correct DiskImage."""
        img = DiskImage(path="/images/boot.img", format="qcow2", size_mb=512)
        manager.attach_image(img)
        info = manager.get_image_info("/images/boot.img")
        assert info.format == "qcow2"
        assert info.size_mb == 512

    def test_create_overlay(self, manager):
        """create_overlay creates a qcow2 overlay referencing the base."""
        base = DiskImage(path="/images/base.raw", size_mb=2048)
        manager.attach_image(base)
        result = manager.create_overlay("/images/base.raw", "/images/overlay.qcow2")
        assert result == "/images/overlay.qcow2"
        overlay = manager.get_image_info("/images/overlay.qcow2")
        assert overlay.format == "qcow2"
        assert overlay.size_mb == 2048

    def test_create_overlay_missing_base_raises(self, manager):
        """create_overlay raises when the base image is not attached."""
        with pytest.raises(ImageNotFoundError):
            manager.create_overlay("/missing", "/overlay.qcow2")

    def test_cleanup(self, manager):
        """cleanup removes all attached images."""
        manager.attach_image(DiskImage(path="/a"))
        manager.attach_image(DiskImage(path="/b"))
        manager.cleanup()
        assert manager.list_images() == []
