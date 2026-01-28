"""
Mock implementation of gui_display interface.

Use this mock when testing modules that depend on gui_display.
"""

from typing import Dict, Any, List, Optional
from ..interface import GuiDisplayInterface


class MockGuiDisplayInterface(GuiDisplayInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self._framebuffer_source: Any = None
        self._rendering: bool = False
        self._scale: float = 1.0

    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({"method": method, "args": kwargs})

    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls

    def reset(self) -> None:
        """Clear recorded calls and state."""
        self.calls = []
        self._framebuffer_source = None
        self._rendering = False
        self._scale = 1.0

    def set_framebuffer_source(self, source: Any) -> None:
        self._record_call("set_framebuffer_source")
        self._framebuffer_source = source

    def start_rendering(self) -> None:
        self._record_call("start_rendering")
        self._rendering = True

    def stop_rendering(self) -> None:
        self._record_call("stop_rendering")
        self._rendering = False

    def is_rendering(self) -> bool:
        self._record_call("is_rendering")
        return self._rendering

    def set_scale(self, scale: float) -> None:
        self._record_call("set_scale", scale=scale)
        self._scale = scale

    def get_scale(self) -> float:
        self._record_call("get_scale")
        return self._scale

    def capture_screenshot(self, path: str) -> str:
        self._record_call("capture_screenshot", path=path)
        return path

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._rendering = False
        self._framebuffer_source = None
        self._scale = 1.0
