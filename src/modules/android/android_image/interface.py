"""
Module: android_image
Layer: android

System image management - loading, validating, and querying Android OS images.
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
import os


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class AndroidImageError(Exception):
    """Base exception for android_image module."""
    pass


class ImageNotFoundError(AndroidImageError):
    """Raised when a requested image file does not exist."""
    pass


class InvalidImageError(AndroidImageError):
    """Raised when an image file is corrupt or invalid."""
    pass


# -----------------------------------------------------------------------------
# Data classes
# -----------------------------------------------------------------------------

@dataclass
class ImageInfo:
    """Metadata describing an Android system image."""
    path: str
    android_version: str = "14"
    api_level: int = 34
    architecture: str = "x86_64"
    size_mb: int = 0
    build_type: str = "userdebug"


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class AndroidImageInterface(ABC):
    """
    Abstract interface for Android system image management.

    Provides operations for loading, validating, and querying Android OS images
    used by the emulator or virtual device layer.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize the image manager with configuration.

        Args:
            config: Module configuration dictionary.
        """
        pass

    @abstractmethod
    def load_image(self, path: str) -> ImageInfo:
        """
        Load an Android system image from disk.

        Args:
            path: Filesystem path to the image file.

        Returns:
            ImageInfo populated with the image metadata.

        Raises:
            ImageNotFoundError: If the path does not exist.
            AndroidImageError: If the module is not initialized.
        """
        pass

    @abstractmethod
    def validate_image(self, path: str) -> bool:
        """
        Validate that an image file exists and is non-empty.

        Args:
            path: Filesystem path to the image file.

        Returns:
            True if the image is valid, False otherwise.

        Raises:
            AndroidImageError: If the module is not initialized.
        """
        pass

    @abstractmethod
    def get_image_info(self) -> Optional[ImageInfo]:
        """
        Return metadata for the currently loaded image.

        Returns:
            ImageInfo for the current image, or None if no image is loaded.

        Raises:
            AndroidImageError: If the module is not initialized.
        """
        pass

    @abstractmethod
    def list_available_images(self, directory: str) -> List[ImageInfo]:
        """
        List all .img files in a directory.

        Args:
            directory: Directory path to scan.

        Returns:
            List of ImageInfo for every .img file found.

        Raises:
            AndroidImageError: If the module is not initialized.
        """
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release resources and mark the module as uninitialized."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultAndroidImage(AndroidImageInterface):
    """Default implementation of AndroidImageInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._current_image: Optional[ImageInfo] = None
        self._initialized = True

    def load_image(self, path: str) -> ImageInfo:
        if not self._initialized:
            raise AndroidImageError("Not initialized")
        if not os.path.exists(path):
            raise ImageNotFoundError(f"Image not found: {path}")
        size = os.path.getsize(path) // (1024 * 1024)
        info = ImageInfo(path=path, size_mb=size)
        self._current_image = info
        return info

    def validate_image(self, path: str) -> bool:
        if not self._initialized:
            raise AndroidImageError("Not initialized")
        return os.path.exists(path) and os.path.getsize(path) > 0

    def get_image_info(self) -> Optional[ImageInfo]:
        if not self._initialized:
            raise AndroidImageError("Not initialized")
        return self._current_image

    def list_available_images(self, directory: str) -> List[ImageInfo]:
        if not self._initialized:
            raise AndroidImageError("Not initialized")
        images: List[ImageInfo] = []
        if os.path.isdir(directory):
            for f in os.listdir(directory):
                if f.endswith(".img"):
                    path = os.path.join(directory, f)
                    size = os.path.getsize(path) // (1024 * 1024)
                    images.append(ImageInfo(path=path, size_mb=size))
        return images

    def cleanup(self) -> None:
        self._current_image = None
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> AndroidImageInterface:
    """
    Factory function to create an AndroidImageInterface instance.

    Args:
        config: Module configuration (optional).

    Returns:
        Configured AndroidImageInterface implementation.
    """
    return DefaultAndroidImage(config or {})
