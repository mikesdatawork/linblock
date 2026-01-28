"""
Mock implementation of device_manager interface.

Use this mock when testing modules that depend on device_manager.
"""

from typing import Dict, Any, List, Optional
from ..interface import DeviceManagerInterface, DeviceType, DeviceInfo


class MockDeviceManagerInterface(DeviceManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._devices: Dict[str, DeviceInfo] = {}

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

    def register_device(self, name: str, device_type: DeviceType) -> DeviceInfo:
        self._record_call("register_device", name=name, device_type=device_type)
        info = DeviceInfo(name=name, device_type=device_type, initialized=False)
        self._devices[name] = info
        return info

    def unregister_device(self, name: str) -> None:
        self._record_call("unregister_device", name=name)
        self._devices.pop(name, None)

    def get_device(self, name: str) -> DeviceInfo:
        self._record_call("get_device", name=name)
        if "get_device" in self.responses:
            return self.responses["get_device"]
        return self._devices.get(
            name, DeviceInfo(name=name, device_type=DeviceType.BLOCK)
        )

    def list_devices(self) -> List[DeviceInfo]:
        self._record_call("list_devices")
        if "list_devices" in self.responses:
            return self.responses["list_devices"]
        return list(self._devices.values())

    def initialize_all(self) -> None:
        self._record_call("initialize_all")
        for d in self._devices.values():
            d.initialized = True

    def reset_device(self, name: str) -> None:
        self._record_call("reset_device", name=name)

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._devices.clear()
