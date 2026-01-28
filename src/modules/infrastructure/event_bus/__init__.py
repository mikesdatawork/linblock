"""
Module: event_bus
Layer: infrastructure

Inter-module event messaging system.
"""

from .interface import create_interface, EventBusInterface, Event, EventHandler

__all__ = ["create_interface", "EventBusInterface", "Event", "EventHandler"]
