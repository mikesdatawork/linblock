"""
Module: config_manager
Layer: infrastructure

Configuration loading, validation, and persistence using YAML.
"""

from typing import Dict, Any, Optional, List
from abc import ABC, abstractmethod
import os
import yaml


class ConfigManagerError(Exception):
    pass

class ConfigNotFoundError(ConfigManagerError):
    pass

class ConfigValidationError(ConfigManagerError):
    pass


class ConfigManagerInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass

    @abstractmethod
    def load_config(self, path: str) -> Dict[str, Any]:
        """Load configuration from YAML file."""
        pass

    @abstractmethod
    def get(self, key: str, default: Any = None) -> Any:
        """Get value by dotted key path (e.g. 'graphics.gpu_mode')."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set value by dotted key path."""
        pass

    @abstractmethod
    def save_config(self, path: str) -> None:
        """Save current configuration to YAML file."""
        pass

    @abstractmethod
    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        """Get configuration section for a specific module."""
        pass

    @abstractmethod
    def validate(self) -> bool:
        """Validate current configuration. Returns True if valid."""
        pass

    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultConfigManager(ConfigManagerInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._data: Dict[str, Any] = dict(config) if config else {}
        self._initialized = True

    def load_config(self, path: str) -> Dict[str, Any]:
        if not self._initialized:
            raise ConfigManagerError("Manager not initialized")
        if not os.path.exists(path):
            raise ConfigNotFoundError(f"Config file not found: {path}")
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        self._data.update(data)
        return dict(self._data)

    def get(self, key: str, default: Any = None) -> Any:
        if not self._initialized:
            raise ConfigManagerError("Manager not initialized")
        parts = key.split('.')
        current = self._data
        for part in parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                return default
        return current

    def set(self, key: str, value: Any) -> None:
        if not self._initialized:
            raise ConfigManagerError("Manager not initialized")
        parts = key.split('.')
        current = self._data
        for part in parts[:-1]:
            if part not in current or not isinstance(current[part], dict):
                current[part] = {}
            current = current[part]
        current[parts[-1]] = value

    def save_config(self, path: str) -> None:
        if not self._initialized:
            raise ConfigManagerError("Manager not initialized")
        os.makedirs(os.path.dirname(path) if os.path.dirname(path) else '.', exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(self._data, f, default_flow_style=False)

    def get_module_config(self, module_name: str) -> Dict[str, Any]:
        if not self._initialized:
            raise ConfigManagerError("Manager not initialized")
        return self._data.get(module_name, {})

    def validate(self) -> bool:
        return self._initialized and isinstance(self._data, dict)

    def cleanup(self) -> None:
        self._initialized = False
        self._data = {}


def create_interface(config: Dict[str, Any] = None) -> ConfigManagerInterface:
    return DefaultConfigManager(config or {})
