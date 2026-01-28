"""
Module: gui_settings
Layer: gui

Profile settings management with YAML I/O.
"""
from typing import Dict, Any, Optional
from abc import ABC, abstractmethod
import yaml
import os


class GuiSettingsError(Exception):
    pass


class GuiSettingsInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass
    @abstractmethod
    def load_profile(self, path: str) -> Dict: pass
    @abstractmethod
    def save_profile(self, path: str, data: Dict) -> None: pass
    @abstractmethod
    def get_current_profile(self) -> Optional[Dict]: pass
    @abstractmethod
    def set_field(self, key: str, value: Any) -> None: pass
    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultGuiSettings(GuiSettingsInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._current_profile: Optional[Dict] = None

    def load_profile(self, path: str) -> Dict:
        if not os.path.exists(path):
            raise GuiSettingsError(f"Profile not found: {path}")
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        self._current_profile = data
        return data

    def save_profile(self, path: str, data: Dict) -> None:
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False)
        self._current_profile = data

    def get_current_profile(self) -> Optional[Dict]:
        return self._current_profile

    def set_field(self, key: str, value: Any) -> None:
        if self._current_profile is None:
            raise GuiSettingsError("No profile loaded")
        self._current_profile[key] = value

    def cleanup(self) -> None:
        self._current_profile = None


def create_interface(config: Dict[str, Any] = None) -> GuiSettingsInterface:
    return DefaultGuiSettings(config or {})
