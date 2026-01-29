# LinBlock Hybrid Emulator Architecture

## Overview

LinBlock uses a **hybrid extraction** approach that combines:
- **LinBlock's QEMU base** for CPU virtualization and device emulation
- **Android Emulator's libOpenglRender** for GPU translation (OpenGL ES → Host OpenGL)
- **gRPC control protocol** for extended emulator control and sensor injection

This provides the performance benefits of Android's GPU translation while maintaining
control over the virtualization layer.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         LinBlock GTK3 Application                        │
│  ┌─────────────┐  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐  │
│  │   Sidebar   │  │ Device Panel │  │   Display   │  │  App Manager │  │
│  └─────────────┘  └──────────────┘  └──────┬──────┘  └──────────────┘  │
└────────────────────────────────────────────┼────────────────────────────┘
                                             │ Shared Memory
                    ┌────────────────────────┼────────────────────────────┐
                    │                        ▼                            │
                    │  ┌──────────────────────────────────────────────┐  │
                    │  │         GPU Renderer Process                  │  │
                    │  │  ┌────────────────────────────────────────┐  │  │
                    │  │  │         libOpenglRender                 │  │  │
                    │  │  │  OpenGL ES 3.2 → Host OpenGL 4.x       │  │  │
                    │  │  │  EGL surface management                 │  │  │
                    │  │  │  Gralloc buffer allocation              │  │  │
                    │  │  └────────────────────────────────────────┘  │  │
                    │  │                     ▲                         │  │
                    │  │                     │ Unix Socket             │  │
                    │  └─────────────────────┼─────────────────────────┘  │
                    │                        │                            │
                    │  ┌─────────────────────┼─────────────────────────┐  │
                    │  │     QEMU Process    │                         │  │
                    │  │  ┌──────────────────┴───────────────────────┐ │  │
                    │  │  │              virtio-gpu                   │ │  │
                    │  │  │         (goldfish_pipe bridge)            │ │  │
                    │  │  └───────────────────────────────────────────┘ │  │
                    │  │  ┌───────────────────────────────────────────┐ │  │
                    │  │  │  KVM  │ virtio-blk │ virtio-net │ Sensors │ │  │
                    │  │  └───────────────────────────────────────────┘ │  │
                    │  └───────────────────────────────────────────────┘  │
                    │                    Emulator Core                     │
                    └──────────────────────────────────────────────────────┘
                                             │
                    ┌────────────────────────┼────────────────────────────┐
                    │                        ▼                            │
                    │  ┌───────────────────────────────────────────────┐  │
                    │  │              Android Guest (GSI)               │  │
                    │  │  ┌─────────┐ ┌─────────┐ ┌─────────────────┐  │  │
                    │  │  │ SurfaceF│ │   Apps  │ │ System Services │  │  │
                    │  │  │ linger  │ │         │ │                 │  │  │
                    │  │  └────┬────┘ └─────────┘ └─────────────────┘  │  │
                    │  │       │                                        │  │
                    │  │  ┌────┴────────────────────────────────────┐  │  │
                    │  │  │  GLES Driver (goldfish_opengl)          │  │  │
                    │  │  │  Sends GL commands via virtio-gpu       │  │  │
                    │  │  └─────────────────────────────────────────┘  │  │
                    │  └───────────────────────────────────────────────┘  │
                    │                     Android VM                       │
                    └──────────────────────────────────────────────────────┘
```

## Component Breakdown

### 1. LinBlock QEMU (Modified)

Base: Upstream QEMU 8.x with minimal patches for goldfish_pipe support.

**Responsibilities:**
- CPU virtualization (KVM)
- Memory management
- virtio devices (blk, net, input, rng)
- goldfish_pipe for GPU command transport
- Sensor injection (accelerometer, GPS, battery)

**Patches Required:**
- `goldfish_pipe` device from Android Emulator
- virtio-gpu modifications for external renderer

### 2. libOpenglRender (Extracted)

Source: `external/qemu/android/android-emugl/host/libs/libOpenglRender/`

**Responsibilities:**
- Translate OpenGL ES 2.0/3.0/3.1/3.2 → Host OpenGL 4.x
- EGL context and surface management
- Gralloc buffer allocation on host GPU
- Shader compilation and caching

**Extraction Scope:**
```
android-emugl/
├── host/
│   ├── libs/
│   │   ├── libOpenglRender/     # Core translator (EXTRACT)
│   │   ├── libGLESv1_dec/       # GLES 1.x decoder (EXTRACT)
│   │   ├── libGLESv2_dec/       # GLES 2.0/3.x decoder (EXTRACT)
│   │   ├── libGLSnapshot/       # GL state snapshots (OPTIONAL)
│   │   └── Translator/          # GL dispatch (EXTRACT)
│   └── include/                 # Headers (EXTRACT)
└── shared/                      # Shared utilities (EXTRACT)
```

### 3. GPU Renderer Process

A separate sandboxed process that hosts libOpenglRender.

**Security Properties:**
- Runs as unprivileged user
- Seccomp-bpf syscall filter (GPU operations only)
- No network access
- No KVM access
- Read-only filesystem (except /tmp)
- Communicates only via Unix socket

**Interface:**
```c
// render_api.h
int renderer_init(int width, int height);
int renderer_process_commands(void* cmd_buffer, size_t size);
int renderer_get_framebuffer(void* out_buffer, size_t* size);
void renderer_cleanup();
```

### 4. Shared Memory Display

Fast path for framebuffer transfer to GTK3.

**Layout:**
```c
struct DisplayShm {
    uint32_t magic;           // 0x4C424B44 "LBKD"
    uint32_t version;         // Protocol version
    uint32_t width;           // Frame width
    uint32_t height;          // Frame height
    uint32_t stride;          // Bytes per row
    uint32_t format;          // BGRA8888
    uint64_t frame_number;    // Incremented each frame
    uint64_t timestamp_ns;    // Frame timestamp
    sem_t frame_ready;        // Posted when new frame available
    uint8_t pixels[];         // width * height * 4
};
```

### 5. gRPC Control Interface

For sensor injection and extended control.

```protobuf
syntax = "proto3";

service LinBlockEmulator {
    // VM lifecycle
    rpc Start(StartRequest) returns (StatusResponse);
    rpc Stop(StopRequest) returns (StatusResponse);
    rpc Reset(ResetRequest) returns (StatusResponse);

    // Sensors
    rpc SetAccelerometer(AccelData) returns (StatusResponse);
    rpc SetGPS(GPSData) returns (StatusResponse);
    rpc SetBattery(BatteryData) returns (StatusResponse);

    // Display
    rpc GetScreenshot(ImageFormat) returns (ImageData);
    rpc SetRotation(RotationData) returns (StatusResponse);

    // Input
    rpc SendTouch(TouchEvent) returns (StatusResponse);
    rpc SendKey(KeyEvent) returns (StatusResponse);
}
```

## Data Flow

### GPU Command Flow

```
1. Android app issues OpenGL ES call
2. goldfish_opengl driver encodes command
3. Command sent via virtio-gpu / goldfish_pipe
4. QEMU forwards to GPU Renderer via Unix socket
5. libOpenglRender decodes and executes on host GPU
6. Rendered frame written to shared memory
7. GTK3 display reads and presents frame
```

### Input Event Flow

```
1. User clicks/touches GTK3 display widget
2. Coordinates translated to Android screen space
3. Event sent to QEMU via virtio-input
4. Android receives touch event via input subsystem
5. App processes touch
```

### Sensor Injection Flow

```
1. LinBlock UI changes sensor value (e.g., GPS)
2. gRPC call to emulator control service
3. QEMU injects sensor data via goldfish_sensors
4. Android SensorManager receives updated value
5. App gets sensor event callback
```

## Build Structure

```
linblock/
├── src/
│   └── modules/
│       └── emulation/
│           ├── emulator_core/           # Existing QEMU wrapper
│           ├── gpu_renderer/            # NEW: libOpenglRender wrapper
│           │   ├── interface.py
│           │   ├── internal/
│           │   │   ├── renderer_process.py
│           │   │   └── shm_display.py
│           │   └── tests/
│           └── control_service/         # NEW: gRPC control
│               ├── interface.py
│               ├── proto/
│               │   └── linblock.proto
│               └── internal/
│                   └── sensor_injection.py
├── vendor/
│   └── android-emugl/                   # Extracted libOpenglRender
│       ├── CMakeLists.txt
│       ├── host/
│       │   └── libs/
│       └── build/
│           └── libOpenglRender.so
└── build/
    └── scripts/
        ├── build_renderer.sh
        └── extract_emugl.sh
```

## Performance Targets

| Metric | Target | Method |
|--------|--------|--------|
| Display FPS | 30-60 | Shared memory, no copies |
| GPU latency | <16ms | Direct host GPU rendering |
| Boot time | <30s | virtio-blk, snapshot support |
| Memory overhead | <500MB | Renderer in separate process |
| Input latency | <50ms | virtio-input direct injection |

## Security Model

### Process Isolation

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│  LinBlock GUI   │     │  QEMU Process   │     │  GPU Renderer   │
│  (user process) │     │  (sandboxed)    │     │  (sandboxed++)  │
│                 │     │                 │     │                 │
│  - GTK3 UI      │     │  - KVM access   │     │  - GPU only     │
│  - gRPC client  │     │  - virtio devs  │     │  - No KVM       │
│  - SHM reader   │     │  - goldfish     │     │  - No network   │
└────────┬────────┘     └────────┬────────┘     └────────┬────────┘
         │                       │                       │
         │ gRPC                  │ Unix Socket           │ DRI
         │                       │                       │
         ▼                       ▼                       ▼
    Control plane           GPU commands            /dev/dri/renderD*
```

### Seccomp Filters

**QEMU Process:**
- Allow: read, write, mmap, ioctl (KVM), futex, etc.
- Deny: execve, ptrace, module operations

**GPU Renderer:**
- Allow: read, write, mmap, ioctl (DRI), futex, openat (read-only)
- Deny: execve, ptrace, network, KVM ioctls

## Implementation Phases

### Phase 1: libOpenglRender Extraction (Week 1-2)
- Clone android-emulator source
- Extract emugl components
- Build standalone libOpenglRender.so
- Create C API wrapper

### Phase 2: Renderer Process (Week 3)
- Implement renderer_process.py
- Unix socket communication
- Shared memory framebuffer
- Basic seccomp filter

### Phase 3: QEMU Integration (Week 4)
- Add goldfish_pipe device to QEMU
- Configure virtio-gpu for external renderer
- Test with Android GSI

### Phase 4: GTK3 Display (Week 5)
- Shared memory consumer in EmulatorDisplay
- Frame synchronization
- Input event forwarding

### Phase 5: gRPC Control (Week 6)
- Implement linblock.proto
- Sensor injection
- Extended controls

### Phase 6: Security Hardening (Week 7)
- Full seccomp profiles
- Namespace isolation
- Fuzzing libOpenglRender
- Security audit

## References

- [Android Emulator Source](https://android.googlesource.com/platform/external/qemu/)
- [libOpenglRender Design](https://android.googlesource.com/platform/external/qemu/+/refs/heads/emu-master-dev/android/android-emugl/DESIGN)
- [virtio-gpu Specification](https://docs.oasis-open.org/virtio/virtio/v1.1/virtio-v1.1.html)
- [goldfish Platform](https://android.googlesource.com/device/generic/goldfish/)
