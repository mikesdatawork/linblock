"""
Module: storage_manager
Layer: emulation

Disk image attachment, overlay creation, and storage lifecycle.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class StorageManagerError(Exception):
    """Base exception for storage_manager module."""
    pass


class ImageNotFoundError(StorageManagerError):
    """Raised when a referenced disk image is not attached."""
    pass


class DuplicateImageError(StorageManagerError):
    """Raised when attaching an image with a path already in use."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

@dataclass
class DiskImage:
    path: str
    format: str = "raw"
    size_mb: int = 0
    readonly: bool = False


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class StorageManagerInterface(ABC):
    """
    Abstract interface for disk image and storage management.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        pass

    @abstractmethod
    def attach_image(self, image: DiskImage) -> None:
        """Attach a disk image to the emulator."""
        pass

    @abstractmethod
    def detach_image(self, path: str) -> None:
        """Detach a disk image by its path."""
        pass

    @abstractmethod
    def list_images(self) -> List[DiskImage]:
        """Return all attached disk images."""
        pass

    @abstractmethod
    def create_overlay(self, base_path: str, overlay_path: str) -> str:
        """Create a copy-on-write overlay on top of a base image."""
        pass

    @abstractmethod
    def get_image_info(self, path: str) -> DiskImage:
        """Return info for a specific attached image."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Detach all images and release resources."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultStorageManager(StorageManagerInterface):
    """Default implementation of StorageManagerInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._images: Dict[str, DiskImage] = {}

    def attach_image(self, image: DiskImage) -> None:
        if image.path in self._images:
            raise DuplicateImageError(
                f"Image at '{image.path}' already attached"
            )
        self._images[image.path] = image

    def detach_image(self, path: str) -> None:
        if path not in self._images:
            raise ImageNotFoundError(f"Image '{path}' not attached")
        del self._images[path]

    def list_images(self) -> List[DiskImage]:
        return list(self._images.values())

    def create_overlay(self, base_path: str, overlay_path: str) -> str:
        if base_path not in self._images:
            raise ImageNotFoundError(
                f"Base image '{base_path}' not attached"
            )
        base = self._images[base_path]
        overlay = DiskImage(
            path=overlay_path,
            format="qcow2",
            size_mb=base.size_mb,
            readonly=False,
        )
        self._images[overlay_path] = overlay
        return overlay_path

    def get_image_info(self, path: str) -> DiskImage:
        if path not in self._images:
            raise ImageNotFoundError(f"Image '{path}' not attached")
        return self._images[path]

    def cleanup(self) -> None:
        self._images.clear()


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> StorageManagerInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)

    Returns:
        Configured StorageManagerInterface implementation
    """
    return DefaultStorageManager(config or {})
