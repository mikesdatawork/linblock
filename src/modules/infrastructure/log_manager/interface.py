"""
Module: log_manager
Layer: infrastructure

Structured logging infrastructure.
"""

from typing import Dict, Any
from abc import ABC, abstractmethod
import logging
import json


class LogManagerError(Exception):
    pass


class LogManagerInterface(ABC):
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None: pass

    @abstractmethod
    def get_logger(self, name: str) -> logging.Logger:
        """Get a named logger instance."""
        pass

    @abstractmethod
    def set_level(self, level: str) -> None:
        """Set global log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)."""
        pass

    @abstractmethod
    def add_file_handler(self, path: str) -> None:
        """Add file output handler."""
        pass

    @abstractmethod
    def cleanup(self) -> None: pass


class DefaultLogManager(LogManagerInterface):
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._loggers: Dict[str, logging.Logger] = {}
        self._handlers: list = []
        self._level = getattr(logging, config.get("log_level", "INFO").upper(), logging.INFO)
        self._initialized = True

    def get_logger(self, name: str) -> logging.Logger:
        if not self._initialized:
            raise LogManagerError("Manager not initialized")
        if name not in self._loggers:
            logger = logging.getLogger(f"linblock.{name}")
            logger.setLevel(self._level)
            if not logger.handlers:
                handler = logging.StreamHandler()
                handler.setLevel(self._level)
                formatter = logging.Formatter(
                    '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
            self._loggers[name] = logger
        return self._loggers[name]

    def set_level(self, level: str) -> None:
        if not self._initialized:
            raise LogManagerError("Manager not initialized")
        self._level = getattr(logging, level.upper(), logging.INFO)
        for logger in self._loggers.values():
            logger.setLevel(self._level)

    def add_file_handler(self, path: str) -> None:
        if not self._initialized:
            raise LogManagerError("Manager not initialized")
        handler = logging.FileHandler(path)
        handler.setLevel(self._level)
        formatter = logging.Formatter(
            '%(asctime)s [%(name)s] %(levelname)s: %(message)s'
        )
        handler.setFormatter(formatter)
        self._handlers.append(handler)
        for logger in self._loggers.values():
            logger.addHandler(handler)

    def cleanup(self) -> None:
        for handler in self._handlers:
            handler.close()
        self._handlers.clear()
        self._loggers.clear()
        self._initialized = False


def create_interface(config: Dict[str, Any] = None) -> LogManagerInterface:
    return DefaultLogManager(config or {})
