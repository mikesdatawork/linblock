"""
Internal application state persistence layer.

Provides an in-memory store for tracking application state transitions.
This module is an internal implementation detail -- consumers should use
the public interface instead.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from datetime import datetime, timezone


@dataclass
class AppStateRecord:
    """
    A snapshot of an application's state at a point in time.

    Attributes:
        package: Application package name.
        state: The state string (e.g. "installed", "running").
        timestamp: ISO-8601 timestamp when this record was created.
        previous_state: The state the app was in before the transition, if any.
        metadata: Arbitrary key-value metadata attached to the record.
    """
    package: str
    state: str
    timestamp: str = ""
    previous_state: Optional[str] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()


class AppStateStore:
    """
    In-memory store that tracks the latest state and full history of
    application state transitions.

    Usage::

        store = AppStateStore()
        store.record("com.example.app", "installed")
        store.record("com.example.app", "running")
        current = store.get_current("com.example.app")
        history = store.get_history("com.example.app")
    """

    def __init__(self) -> None:
        self._current: Dict[str, AppStateRecord] = {}
        self._history: Dict[str, List[AppStateRecord]] = {}

    def record(self, package: str, state: str, metadata: Optional[Dict[str, str]] = None) -> AppStateRecord:
        """
        Record a state transition for *package*.

        Args:
            package: Application package name.
            state: New state string.
            metadata: Optional metadata to attach.

        Returns:
            The newly created AppStateRecord.
        """
        previous = self._current.get(package)
        record = AppStateRecord(
            package=package,
            state=state,
            previous_state=previous.state if previous else None,
            metadata=metadata or {},
        )
        self._current[package] = record
        self._history.setdefault(package, []).append(record)
        return record

    def get_current(self, package: str) -> Optional[AppStateRecord]:
        """Return the latest state record for *package*, or None."""
        return self._current.get(package)

    def get_history(self, package: str) -> List[AppStateRecord]:
        """Return the full state history for *package* (oldest first)."""
        return list(self._history.get(package, []))

    def remove(self, package: str) -> None:
        """Remove all records for *package*."""
        self._current.pop(package, None)
        self._history.pop(package, None)

    def clear(self) -> None:
        """Remove all records for all packages."""
        self._current.clear()
        self._history.clear()

    @property
    def packages(self) -> List[str]:
        """Return a list of all tracked package names."""
        return list(self._current.keys())
