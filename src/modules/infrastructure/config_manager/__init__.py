"""
Module: config_manager
Layer: infrastructure

Configuration loading, validation, and persistence using YAML.
"""

from .interface import create_interface, ConfigManagerInterface

__all__ = ["create_interface", "ConfigManagerInterface"]
