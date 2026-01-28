"""
Module: log_manager
Layer: infrastructure

Structured logging infrastructure.
"""

from .interface import create_interface, LogManagerInterface

__all__ = ["create_interface", "LogManagerInterface"]
