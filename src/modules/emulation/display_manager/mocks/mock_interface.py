"""
Mock implementation of display_manager interface.

Use this mock when testing modules that depend on display_manager.
"""

from typing import Dict, Any, List, Optional, Tuple
from ..interface import DisplayManagerInterface, DisplayConfig, FrameData


class MockDisplayManagerInterface(DisplayManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._display_config: Optional[DisplayConfig] = None

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

    def configure(self, display_config: DisplayConfig) -> None:
        self._record_call("configure", display_config=display_config)
        self._display_config = display_config

    def get_frame(self) -> Optional[FrameData]:
        self._record_call("get_frame")
        if "get_frame" in self.responses:
            return self.responses["get_frame"]
        if self._display_config is None:
            return None
        return FrameData(
            width=self._display_config.width,
            height=self._display_config.height,
            data=b"\x00" * 4,
            timestamp=0.0,
        )

    def get_resolution(self) -> Tuple[int, int]:
        self._record_call("get_resolution")
        if "get_resolution" in self.responses:
            return self.responses["get_resolution"]
        if self._display_config:
            return (self._display_config.width, self._display_config.height)
        return (0, 0)

    def set_scale(self, scale: float) -> None:
        self._record_call("set_scale", scale=scale)
        if self._display_config:
            self._display_config.scale = scale

    def get_fps(self) -> float:
        self._record_call("get_fps")
        if "get_fps" in self.responses:
            return self.responses["get_fps"]
        return 30.0

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._display_config = None
