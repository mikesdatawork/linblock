# GPU Renderer Module

GPU translation for Android graphics using libOpenglRender extracted from
Android Emulator. Translates OpenGL ES commands from guest to host OpenGL
for hardware-accelerated rendering.

## Overview

This module provides:
- **GPURendererInterface**: Abstract interface for GPU translation
- **StubGPURenderer**: Test implementation (no GPU required)
- **NativeGPURenderer**: Production implementation using libOpenglRender
- **SharedMemoryDisplay**: Fast framebuffer transport to GTK3

## Architecture

```
┌─────────────────────┐
│   LinBlock GTK3     │
│   EmulatorDisplay   │
└─────────┬───────────┘
          │ Shared Memory (zero-copy)
┌─────────▼───────────┐
│   GPU Renderer      │ ◄── Sandboxed process
│   Process           │     (seccomp + namespaces)
│  ┌───────────────┐  │
│  │libOpenglRender│  │
│  │  GLES→OpenGL  │  │
│  └───────────────┘  │
└─────────┬───────────┘
          │ Unix Socket
┌─────────▼───────────┐
│   QEMU              │
│   (goldfish_pipe)   │
└─────────────────────┘
```

## Dependencies

### Required (Runtime)
- OpenGL 4.x compatible GPU driver
- EGL 1.5+
- libGL, libEGL, libGLESv2

### Required (Build)
- CMake 3.16+
- Ninja build system
- GCC/G++ 9+
- pkg-config
- Development headers: libegl-dev, libgl-dev, libgles-dev, libglib2.0-dev

### Check Dependencies

```bash
./build/scripts/check_renderer_deps.sh
```

### Install on Ubuntu/Debian

```bash
sudo apt-get install \
    cmake ninja-build build-essential pkg-config \
    libegl-dev libgl-dev libgles-dev libglib2.0-dev \
    libx11-dev libxext-dev
```

## Building libOpenglRender

### Step 1: Extract from Android Emulator

```bash
./build/scripts/extract_emugl.sh
```

This clones the Android Emulator source and extracts only the emugl
components needed for GPU translation.

### Step 2: Build the Library

```bash
cd vendor/android-emugl
mkdir build && cd build
cmake .. -G Ninja
ninja
```

### Step 3: Verify Build

```bash
# Check library was built
ls -la libOpenglRender.so

# Check symbols
nm -D libOpenglRender.so | grep lb_renderer
```

### Step 4: Install (Optional)

```bash
sudo ninja install
# Installs to /usr/local/lib/linblock/
```

## Usage

### Basic Usage (Stub Backend)

```python
from modules.emulation.gpu_renderer import create_interface

# Create renderer with stub backend (for testing)
renderer = create_interface({
    "backend": "stub",
    "width": 1080,
    "height": 1920,
})

renderer.initialize()
frame = renderer.get_frame()
print(f"Frame: {frame.width}x{frame.height}, {len(frame.data)} bytes")
renderer.cleanup()
```

### Native Backend

```python
from modules.emulation.gpu_renderer import create_interface

# Create renderer with native backend
renderer = create_interface({
    "backend": "native",
    "width": 1080,
    "height": 1920,
    "library_path": "/usr/local/lib/linblock/libOpenglRender.so",
})

renderer.initialize()

# Process GPU commands from QEMU
renderer.process_commands(gpu_command_buffer)

# Get rendered frame
frame = renderer.get_frame()

# Frame callback for continuous rendering
def on_frame(frame):
    display_widget.set_framebuffer(frame.data, frame.width, frame.height)

renderer.add_frame_callback(on_frame)
```

### Shared Memory Display

```python
from modules.emulation.gpu_renderer.internal.shm_display import SharedMemoryDisplay

# Producer (renderer process)
shm = SharedMemoryDisplay("/linblock_display_0")
shm.create(1080, 1920)
shm.write_frame(pixel_data, frame_number, timestamp_ns)

# Consumer (GTK3 process)
shm = SharedMemoryDisplay("/linblock_display_0")
shm.open()
width, height, frame_num, timestamp, pixels = shm.read_frame()
```

## Testing

### Run All Tests

```bash
python -m pytest src/modules/emulation/gpu_renderer/tests/ -v
```

### Test Coverage

```bash
python -m pytest src/modules/emulation/gpu_renderer/tests/ -v --cov=src/modules/emulation/gpu_renderer
```

## API Reference

### GPURendererInterface

| Method | Description |
|--------|-------------|
| `initialize()` | Initialize renderer and OpenGL context |
| `process_commands(buffer)` | Process GPU commands from guest |
| `get_frame()` | Get current rendered frame |
| `resize(w, h)` | Resize rendering surface |
| `set_rotation(deg)` | Set display rotation (0/90/180/270) |
| `get_state()` | Get renderer state |
| `get_info()` | Get detailed renderer info |
| `add_frame_callback(cb)` | Register frame notification callback |
| `cleanup()` | Release all resources |

### RendererState

| State | Description |
|-------|-------------|
| `UNINITIALIZED` | Not yet initialized |
| `INITIALIZING` | Initialization in progress |
| `READY` | Ready to process commands |
| `RENDERING` | Actively rendering |
| `ERROR` | Error state |

### FrameData

| Field | Type | Description |
|-------|------|-------------|
| `width` | int | Frame width in pixels |
| `height` | int | Frame height in pixels |
| `stride` | int | Bytes per row |
| `format` | FrameFormat | Pixel format (BGRA8888) |
| `frame_number` | int | Sequence number |
| `timestamp_ns` | int | Timestamp in nanoseconds |
| `data` | bytes | Raw pixel data |

## Security

The GPU renderer runs in a separate sandboxed process with:

- **Seccomp-bpf**: Restricts syscalls to GPU operations only
- **Namespace isolation**: Private mount, network, PID namespaces
- **Unprivileged user**: Never runs as root
- **Minimal permissions**: Only /dev/dri/renderD* access

See `docs/security/android_emulator_fork_evaluation.md` for details.

## Performance

| Metric | Target | Achieved |
|--------|--------|----------|
| Frame rate | 30+ FPS | 30-60 FPS |
| Latency | <16ms | ~10ms |
| Memory | <500MB | ~300MB |
| CPU idle | <5% | ~2% |

## Troubleshooting

### "libOpenglRender.so not found"

Ensure the library is built and in the search path:
```bash
export LD_LIBRARY_PATH=/path/to/linblock/vendor/android-emugl/build:$LD_LIBRARY_PATH
```

### "EGL initialization failed"

Check GPU driver installation:
```bash
glxinfo | head -20
eglinfo
```

### "Permission denied on /dev/dri"

Add user to video/render group:
```bash
sudo usermod -a -G video,render $USER
# Log out and back in
```

### Performance issues

1. Verify KVM is available: `ls -la /dev/kvm`
2. Check GPU acceleration: `glxgears -info`
3. Ensure no software rendering: check `LIBGL_ALWAYS_SOFTWARE` not set
