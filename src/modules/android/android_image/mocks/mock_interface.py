"""
Mock implementation of android_image interface.

Use this mock when testing modules that depend on android_image.
"""

from typing import Dict, Any, Optional, List
from ..interface import AndroidImageInterface, ImageInfo


class MockAndroidImageInterface(AndroidImageInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._current_image: Optional[ImageInfo] = None
        self._initialized = True

    # -- call tracking helpers ------------------------------------------------

    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({"method": method, "args": kwargs})

    def set_response(self, method: str, response: Any) -> None:
        """Configure a canned response for a method."""
        self.responses[method] = response

    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method name."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def reset(self) -> None:
        """Clear recorded calls and canned responses."""
        self.calls = []
        self.responses = {}
        self._current_image = None

    # -- interface methods ----------------------------------------------------

    def load_image(self, path: str) -> ImageInfo:
        self._record_call("load_image", path=path)
        if "load_image" in self.responses:
            return self.responses["load_image"]
        info = ImageInfo(path=path)
        self._current_image = info
        return info

    def validate_image(self, path: str) -> bool:
        self._record_call("validate_image", path=path)
        if "validate_image" in self.responses:
            return self.responses["validate_image"]
        return True

    def get_image_info(self) -> Optional[ImageInfo]:
        self._record_call("get_image_info")
        if "get_image_info" in self.responses:
            return self.responses["get_image_info"]
        return self._current_image

    def list_available_images(self, directory: str) -> List[ImageInfo]:
        self._record_call("list_available_images", directory=directory)
        if "list_available_images" in self.responses:
            return self.responses["list_available_images"]
        return []

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._current_image = None
        self._initialized = False
