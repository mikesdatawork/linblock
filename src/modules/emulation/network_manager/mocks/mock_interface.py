"""
Mock implementation of network_manager interface.

Use this mock when testing modules that depend on network_manager.
"""

from typing import Dict, Any, List
from ..interface import NetworkManagerInterface, NetworkMode, NetworkConfig


class MockNetworkManagerInterface(NetworkManagerInterface):
    """
    Mock implementation for testing.

    Tracks all method calls and allows configuring responses.
    """

    def __init__(self, config: Dict[str, Any] = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._net_config = NetworkConfig()
        self._enabled = False
        self._forwards: Dict[int, int] = {}

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

    def configure(self, net_config: NetworkConfig) -> None:
        self._record_call("configure", net_config=net_config)
        self._net_config = net_config

    def enable(self) -> None:
        self._record_call("enable")
        self._enabled = True

    def disable(self) -> None:
        self._record_call("disable")
        self._enabled = False

    def is_connected(self) -> bool:
        self._record_call("is_connected")
        if "is_connected" in self.responses:
            return self.responses["is_connected"]
        return self._enabled

    def add_port_forward(self, host_port: int, guest_port: int) -> None:
        self._record_call(
            "add_port_forward", host_port=host_port, guest_port=guest_port
        )
        self._forwards[host_port] = guest_port

    def remove_port_forward(self, host_port: int) -> None:
        self._record_call("remove_port_forward", host_port=host_port)
        self._forwards.pop(host_port, None)

    def get_config(self) -> NetworkConfig:
        self._record_call("get_config")
        if "get_config" in self.responses:
            return self.responses["get_config"]
        return self._net_config

    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._enabled = False
        self._forwards.clear()
