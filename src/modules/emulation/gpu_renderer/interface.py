"""
Module: gpu_renderer
Layer: emulation

GPU translation for Android graphics using libOpenglRender.
Translates OpenGL ES commands from guest to host OpenGL.
"""

from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass
from abc import ABC, abstractmethod
from enum import Enum
import ctypes
import os


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class GPURendererError(Exception):
    """Base exception for gpu_renderer module."""
    pass


class RendererInitError(GPURendererError):
    """Raised when renderer initialization fails."""
    pass


class RendererNotReadyError(GPURendererError):
    """Raised when operation requires initialized renderer."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

class RendererState(Enum):
    UNINITIALIZED = "uninitialized"
    INITIALIZING = "initializing"
    READY = "ready"
    RENDERING = "rendering"
    ERROR = "error"


class FrameFormat(Enum):
    RGBA8888 = 0
    BGRA8888 = 1
    RGB888 = 2


@dataclass
class FrameData:
    """Container for rendered frame data."""
    width: int = 0
    height: int = 0
    stride: int = 0
    format: FrameFormat = FrameFormat.BGRA8888
    frame_number: int = 0
    timestamp_ns: int = 0
    data: bytes = b""


@dataclass
class RendererConfig:
    """Configuration for GPU renderer."""
    width: int = 1080
    height: int = 1920
    library_path: str = ""
    use_software_renderer: bool = False
    enable_vsync: bool = True


@dataclass
class RendererInfo:
    """Information about renderer state."""
    state: RendererState = RendererState.UNINITIALIZED
    width: int = 0
    height: int = 0
    frames_rendered: int = 0
    gpu_vendor: str = ""
    gl_version: str = ""
    error_message: str = ""


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class GPURendererInterface(ABC):
    """
    Abstract interface for GPU translation.

    Provides methods for initializing the renderer, processing GPU commands
    from the guest, and retrieving rendered frames.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize module with configuration."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Initialize the GPU renderer and OpenGL context."""
        pass

    @abstractmethod
    def process_commands(self, command_buffer: bytes) -> None:
        """Process GPU commands from the guest.

        Args:
            command_buffer: Encoded GPU commands from virtio-gpu/goldfish_pipe
        """
        pass

    @abstractmethod
    def get_frame(self) -> Optional[FrameData]:
        """Get the current rendered frame.

        Returns:
            FrameData containing the rendered pixels, or None if no frame ready
        """
        pass

    @abstractmethod
    def resize(self, width: int, height: int) -> None:
        """Resize the rendering surface.

        Args:
            width: New width in pixels
            height: New height in pixels
        """
        pass

    @abstractmethod
    def set_rotation(self, degrees: int) -> None:
        """Set display rotation.

        Args:
            degrees: Rotation angle (0, 90, 180, 270)
        """
        pass

    @abstractmethod
    def get_state(self) -> RendererState:
        """Get current renderer state."""
        pass

    @abstractmethod
    def get_info(self) -> RendererInfo:
        """Get detailed renderer information."""
        pass

    @abstractmethod
    def add_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        """Register callback for new frame notifications."""
        pass

    @abstractmethod
    def remove_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        """Unregister frame callback."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release all renderer resources."""
        pass


# -----------------------------------------------------------------------------
# Stub Implementation (for testing without libOpenglRender)
# -----------------------------------------------------------------------------

class StubGPURenderer(GPURendererInterface):
    """Stub implementation that generates test frames without real GPU."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = RendererConfig(
            width=config.get("width", 1080),
            height=config.get("height", 1920),
            library_path=config.get("library_path", ""),
            use_software_renderer=config.get("use_software_renderer", True),
        )
        self._state = RendererState.UNINITIALIZED
        self._frame_count = 0
        self._frame_callbacks: List[Callable[[FrameData], None]] = []
        self._rotation = 0
        self._error_message = ""

    def initialize(self) -> None:
        self._state = RendererState.INITIALIZING
        # Stub: just transition to ready
        self._state = RendererState.READY

    def process_commands(self, command_buffer: bytes) -> None:
        if self._state != RendererState.READY:
            raise RendererNotReadyError("Renderer not initialized")
        # Stub: ignore commands, generate test frame
        self._frame_count += 1

    def get_frame(self) -> Optional[FrameData]:
        if self._state != RendererState.READY:
            return None

        # Generate a test pattern frame
        w, h = self._config.width, self._config.height
        # Simple gradient pattern
        data = bytearray(w * h * 4)
        for y in range(h):
            for x in range(w):
                idx = (y * w + x) * 4
                data[idx] = (x * 255 // w) & 0xFF      # B
                data[idx + 1] = (y * 255 // h) & 0xFF  # G
                data[idx + 2] = 128                     # R
                data[idx + 3] = 255                     # A

        frame = FrameData(
            width=w,
            height=h,
            stride=w * 4,
            format=FrameFormat.BGRA8888,
            frame_number=self._frame_count,
            timestamp_ns=0,
            data=bytes(data),
        )

        # Notify callbacks
        for callback in self._frame_callbacks:
            try:
                callback(frame)
            except Exception:
                pass

        return frame

    def resize(self, width: int, height: int) -> None:
        self._config.width = width
        self._config.height = height

    def set_rotation(self, degrees: int) -> None:
        if degrees not in (0, 90, 180, 270):
            raise GPURendererError(f"Invalid rotation: {degrees}")
        self._rotation = degrees

    def get_state(self) -> RendererState:
        return self._state

    def get_info(self) -> RendererInfo:
        return RendererInfo(
            state=self._state,
            width=self._config.width,
            height=self._config.height,
            frames_rendered=self._frame_count,
            gpu_vendor="Stub",
            gl_version="Stub 1.0",
            error_message=self._error_message,
        )

    def add_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        self._frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)

    def get_shm_name(self) -> Optional[str]:
        """Get the shared memory name (stub returns None)."""
        return None

    def cleanup(self) -> None:
        self._state = RendererState.UNINITIALIZED
        self._frame_callbacks.clear()


# -----------------------------------------------------------------------------
# Native Implementation (uses libOpenglRender via sandboxed process)
# -----------------------------------------------------------------------------

class NativeGPURenderer(GPURendererInterface):
    """
    Native implementation using libOpenglRender library.

    Uses a sandboxed subprocess (RendererProcess) to host the GPU renderer,
    communicating via Unix socket and shared memory for security isolation.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = RendererConfig(
            width=config.get("width", 1080),
            height=config.get("height", 1920),
            library_path=config.get("library_path", ""),
            use_software_renderer=config.get("use_software_renderer", False),
        )
        self._state = RendererState.UNINITIALIZED
        self._process = None  # RendererProcess instance
        self._frame_count = 0
        self._frame_callbacks: List[Callable[[FrameData], None]] = []
        self._error_message = ""
        self._use_sandbox = config.get("use_sandbox", True)

    def _find_library(self) -> str:
        """Find libOpenglRender.so library."""
        # Check explicit path first
        if self._config.library_path and os.path.exists(self._config.library_path):
            return self._config.library_path

        # Check common locations
        search_paths = [
            # LinBlock vendor directory
            os.path.expanduser("~/projects/linblock/vendor/android-emugl/build/libOpenglRender.so"),
            # System-wide installation
            "/usr/local/lib/linblock/libOpenglRender.so",
            "/usr/lib/linblock/libOpenglRender.so",
            # Local build
            "./libOpenglRender.so",
        ]

        for path in search_paths:
            if os.path.exists(path):
                return path

        return ""

    def initialize(self) -> None:
        from .internal.renderer_process import RendererProcess, RendererProcessConfig

        self._state = RendererState.INITIALIZING

        try:
            # Create renderer process configuration
            process_config = RendererProcessConfig(
                width=self._config.width,
                height=self._config.height,
                library_path=self._find_library(),
                use_sandbox=self._use_sandbox,
            )

            # Create and start renderer process
            self._process = RendererProcess(process_config)
            self._process.start()

            self._state = RendererState.READY

        except Exception as e:
            self._error_message = str(e)
            self._state = RendererState.ERROR
            raise RendererInitError(self._error_message)

    def process_commands(self, command_buffer: bytes) -> None:
        if self._state != RendererState.READY or not self._process:
            raise RendererNotReadyError("Renderer not initialized")

        self._process.process_commands(command_buffer)
        self._frame_count += 1

    def get_frame(self) -> Optional[FrameData]:
        """Get frame from shared memory.

        Note: For GTK integration, use SharedMemoryFrameSource instead
        of polling this method directly for better performance.
        """
        if self._state != RendererState.READY or not self._process:
            return None

        # Read from shared memory
        from .internal.shm_display import SharedMemoryDisplay

        try:
            shm = SharedMemoryDisplay(self._process.get_shm_name())
            shm.open()
            result = shm.read_frame()
            shm.cleanup()

            if result:
                width, height, frame_number, timestamp_ns, pixels = result
                return FrameData(
                    width=width,
                    height=height,
                    stride=width * 4,
                    format=FrameFormat.BGRA8888,
                    frame_number=frame_number,
                    timestamp_ns=timestamp_ns,
                    data=pixels,
                )
        except Exception:
            pass

        return None

    def resize(self, width: int, height: int) -> None:
        self._config.width = width
        self._config.height = height

        if self._process:
            self._process.resize(width, height)

    def set_rotation(self, degrees: int) -> None:
        if degrees not in (0, 90, 180, 270):
            raise GPURendererError(f"Invalid rotation: {degrees}")

        if self._process:
            self._process.set_rotation(degrees)

    def get_state(self) -> RendererState:
        return self._state

    def get_info(self) -> RendererInfo:
        return RendererInfo(
            state=self._state,
            width=self._config.width,
            height=self._config.height,
            frames_rendered=self._frame_count,
            gpu_vendor="",  # TODO: Query from process
            gl_version="",  # TODO: Query from process
            error_message=self._error_message,
        )

    def add_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        self._frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[FrameData], None]) -> None:
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)

    def get_shm_name(self) -> Optional[str]:
        """Get the shared memory name for GTK integration."""
        if self._process:
            return self._process.get_shm_name()
        return None

    def cleanup(self) -> None:
        if self._process:
            self._process.cleanup()
            self._process = None

        self._state = RendererState.UNINITIALIZED
        self._frame_callbacks.clear()


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> GPURendererInterface:
    """
    Factory function to create GPU renderer interface.

    Args:
        config: Module configuration
            - backend: "native" or "stub" (default: "native")
            - width, height: Display dimensions
            - library_path: Path to libOpenglRender.so

    Returns:
        Configured GPURendererInterface implementation
    """
    config = config or {}
    backend = config.get("backend", "native")

    if backend == "stub":
        return StubGPURenderer(config)
    else:
        return NativeGPURenderer(config)
