"""
GPU Renderer Module

Provides GPU translation capabilities using extracted Android Emulator
libOpenglRender library. Translates OpenGL ES commands from guest to
host OpenGL for hardware-accelerated Android graphics.
"""

from .interface import (
    GPURendererInterface,
    create_interface,
    GPURendererError,
    RendererState,
    FrameData,
    RendererConfig,
    RendererInfo,
    StubGPURenderer,
    NativeGPURenderer,
)

# GTK integration (lazy import to avoid GTK dependency when not needed)
def get_gtk_integration():
    """Get GTK integration classes (lazy load)."""
    from .gtk_integration import (
        SharedMemoryFrameSource,
        GPURendererDisplayBridge,
        create_display_bridge,
    )
    return SharedMemoryFrameSource, GPURendererDisplayBridge, create_display_bridge

__all__ = [
    "GPURendererInterface",
    "create_interface",
    "GPURendererError",
    "RendererState",
    "FrameData",
    "RendererConfig",
    "RendererInfo",
    "StubGPURenderer",
    "NativeGPURenderer",
    "get_gtk_integration",
]
