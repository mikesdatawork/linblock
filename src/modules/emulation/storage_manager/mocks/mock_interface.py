"""
Mock implementation of storage_manager interface.

Use this mock when testing modules that depend on storage_manager.
"""

from typing import Dict, Any, List
from ..interface import StorageManagerInterface, DiskImage


class MockStorageManagerInterface(StorageManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._images: Dict[str, DiskImage] = {}

    def _record_call(self, method: str, **kwargs) -> None:
        self.calls.append({"method": method, "args": kwargs})

    def set_response(self, method: str, response: Any) -> None:
        self.responses[method] = response

    def get_calls(self, method: str = None) -> List[Dict]:
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def clear(self) -> None:
        self.calls = []
        self.responses = {}

    def attach_image(self, image: DiskImage) -> None:
        self._record_call("attach_image", path=image.path)
        self._images[image.path] = image

    def detach_image(self, path: str) -> None:
        self._record_call("detach_image", path=path)
        self._images.pop(path, None)

    def list_images(self) -> List[DiskImage]:
        self._record_call("list_images")
        if "list_images" in self.responses:
            return self.responses["list_images"]
        return list(self._images.values())

    def create_overlay(self, base_path: str, overlay_path: str) -> str:
        self._record_call(
            "create_overlay", base_path=base_path, overlay_path=overlay_path
        )
        if "create_overlay" in self.responses:
            return self.responses["create_overlay"]
        return overlay_path

    def get_image_info(self, path: str) -> DiskImage:
        self._record_call("get_image_info", path=path)
        if "get_image_info" in self.responses:
            return self.responses["get_image_info"]
        if path in self._images:
            return self._images[path]
        return DiskImage(path=path)

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._images.clear()
