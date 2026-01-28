"""
Mock implementation of gui_core interface.

Use this mock when testing modules that depend on gui_core.
"""

from typing import Dict, Any, List, Optional
from ..interface import GuiCoreInterface


class MockGuiCoreInterface(GuiCoreInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self._pages: Dict[str, Any] = {}
        self._current_page: str = ""
        self._initialized = False

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
        self._pages.clear()
        self._current_page = ""
        self._initialized = False

    def initialize(self) -> None:
        self._record_call("initialize")
        self._initialized = True

    def register_page(self, name: str, widget: Any) -> None:
        self._record_call("register_page", name=name)
        self._pages[name] = widget
        if not self._current_page:
            self._current_page = name

    def switch_page(self, name: str) -> None:
        self._record_call("switch_page", name=name)
        self._current_page = name

    def get_current_page(self) -> str:
        self._record_call("get_current_page")
        return self._current_page

    def list_pages(self) -> List[str]:
        self._record_call("list_pages")
        return list(self._pages.keys())

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._pages.clear()
        self._current_page = ""
        self._initialized = False
