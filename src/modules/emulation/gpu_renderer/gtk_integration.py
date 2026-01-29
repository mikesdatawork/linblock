"""
GTK3 integration for GPU renderer shared memory display.

Provides a frame source that polls shared memory and delivers
frames to the EmulatorDisplay widget using GTK's main loop.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import GLib

from typing import Optional, Callable, TYPE_CHECKING
import threading
import time

from .internal.shm_display import SharedMemoryDisplay

if TYPE_CHECKING:
    from src.ui.components.emulator_display import EmulatorDisplay


class SharedMemoryFrameSource:
    """
    Polls shared memory for new frames and delivers them to GTK widget.

    Uses GLib.timeout_add() to poll shared memory at regular intervals
    and update the EmulatorDisplay widget with new frames.
    """

    def __init__(self, shm_name: str, target_fps: int = 60):
        """
        Initialize the frame source.

        Args:
            shm_name: Shared memory name (e.g., "/linblock_display_1234")
            target_fps: Target frame rate for polling (default 60)
        """
        self._shm_name = shm_name
        self._target_fps = target_fps
        self._poll_interval_ms = max(1, 1000 // target_fps)

        self._shm: Optional[SharedMemoryDisplay] = None
        self._widget: Optional['EmulatorDisplay'] = None
        self._running = False
        self._timeout_id: Optional[int] = None
        self._frame_callback: Optional[Callable[[int, int, int], None]] = None
        self._last_frame_time = 0.0
        self._frame_count = 0
        self._fps = 0.0

    def attach(self, widget: 'EmulatorDisplay') -> None:
        """
        Attach to an EmulatorDisplay widget.

        Args:
            widget: The GTK EmulatorDisplay widget to update
        """
        self._widget = widget

    def set_frame_callback(self, callback: Callable[[int, int, int], None]) -> None:
        """
        Set callback for frame delivery notifications.

        Args:
            callback: Function called with (frame_number, width, height)
        """
        self._frame_callback = callback

    def start(self) -> bool:
        """
        Start polling shared memory for frames.

        Returns:
            True if started successfully, False otherwise
        """
        if self._running:
            return True

        try:
            self._shm = SharedMemoryDisplay(self._shm_name)
            self._shm.open()
        except Exception as e:
            print(f"Failed to open shared memory: {e}")
            return False

        self._running = True
        self._last_frame_time = time.time()
        self._frame_count = 0

        # Schedule polling on GTK main loop
        self._timeout_id = GLib.timeout_add(
            self._poll_interval_ms,
            self._poll_frame
        )

        return True

    def stop(self) -> None:
        """Stop polling and release resources."""
        self._running = False

        if self._timeout_id is not None:
            GLib.source_remove(self._timeout_id)
            self._timeout_id = None

        if self._shm is not None:
            try:
                self._shm.cleanup()
            except Exception:
                pass
            self._shm = None

    def _poll_frame(self) -> bool:
        """
        Poll for new frame (called from GTK main loop).

        Returns:
            True to continue polling, False to stop
        """
        if not self._running:
            return False

        if self._shm is None or self._widget is None:
            return True

        try:
            result = self._shm.read_frame()
            if result is not None:
                width, height, frame_number, timestamp_ns, pixels = result

                # Update widget on main thread
                self._widget.set_framebuffer(pixels, width, height, format="bgra")

                # Update FPS counter
                self._frame_count += 1
                now = time.time()
                elapsed = now - self._last_frame_time
                if elapsed >= 1.0:
                    self._fps = self._frame_count / elapsed
                    self._frame_count = 0
                    self._last_frame_time = now

                # Notify callback
                if self._frame_callback:
                    self._frame_callback(frame_number, width, height)

        except Exception as e:
            print(f"Frame poll error: {e}")

        return True  # Continue polling

    def get_fps(self) -> float:
        """Get current measured frame rate."""
        return self._fps

    def is_running(self) -> bool:
        """Check if frame source is running."""
        return self._running

    def get_shm_name(self) -> str:
        """Get the shared memory name."""
        return self._shm_name


class GPURendererDisplayBridge:
    """
    High-level bridge between GPURenderer and EmulatorDisplay.

    Manages the complete lifecycle of GPU rendering display:
    - Creates/destroys shared memory
    - Starts/stops frame polling
    - Handles resize events
    """

    def __init__(self):
        self._renderer = None
        self._frame_source: Optional[SharedMemoryFrameSource] = None
        self._widget: Optional['EmulatorDisplay'] = None
        self._shm_name: Optional[str] = None

    def connect(self, renderer, widget: 'EmulatorDisplay') -> None:
        """
        Connect a GPU renderer to an EmulatorDisplay widget.

        Args:
            renderer: GPURendererInterface instance
            widget: EmulatorDisplay GTK widget
        """
        self._renderer = renderer
        self._widget = widget

        # Get shared memory name from renderer process
        if hasattr(renderer, '_process') and renderer._process:
            self._shm_name = renderer._process.get_shm_name()
        elif hasattr(renderer, 'get_shm_name'):
            self._shm_name = renderer.get_shm_name()

    def start(self) -> bool:
        """
        Start rendering frames to the display.

        Returns:
            True if started successfully
        """
        if not self._shm_name or not self._widget:
            return False

        self._frame_source = SharedMemoryFrameSource(self._shm_name)
        self._frame_source.attach(self._widget)
        return self._frame_source.start()

    def stop(self) -> None:
        """Stop rendering."""
        if self._frame_source:
            self._frame_source.stop()
            self._frame_source = None

    def get_fps(self) -> float:
        """Get current frame rate."""
        if self._frame_source:
            return self._frame_source.get_fps()
        return 0.0

    def is_running(self) -> bool:
        """Check if bridge is active."""
        return self._frame_source is not None and self._frame_source.is_running()


def create_display_bridge() -> GPURendererDisplayBridge:
    """Factory function to create a display bridge."""
    return GPURendererDisplayBridge()
