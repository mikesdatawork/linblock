# LinBlock Emulator Architecture

## Overview

The LinBlock emulator provides a full x86_64 virtual machine environment capable of running
Android 14 (API 34) with near-native performance using KVM hardware-assisted virtualization.
When KVM is unavailable, a software-based interpreter fallback is provided at reduced
performance. The architecture is organized into layered components with well-defined
interfaces to support modularity, testability, and future extensibility.

## Component Diagram

```
+-------------------------------------------+
|              GTK GUI Layer                |
|  (Display Widget, Input Handling, Menus)  |
+-------------------------------------------+
|           Emulator Controller             |
|  (Lifecycle, Config, State Machine)       |
+----------+----------+----------+----------+
|   CPU    |  Memory  | Devices  | Display  |
| Manager  |  Manager | Manager  | Manager  |
+----------+----------+----------+----------+
|         Hardware Abstraction Layer        |
|  (KVM ioctls / Software Emulation)       |
+-------------------------------------------+
|     KVM / Software Emulation Core         |
|  (/dev/kvm or interpreter backend)       |
+-------------------------------------------+
|          Host Linux Kernel                |
+-------------------------------------------+
```

## Architectural Layers

### 1. GTK GUI Layer

The topmost layer handles all user-facing interaction. It is implemented using
PyGObject (GTK 3) and runs in the main process thread. The GUI layer communicates
with the Emulator Controller through a well-defined Python API and receives
framebuffer updates via shared memory.

Responsibilities:
- Render the emulated Android display in a GTK DrawingArea widget
- Capture and forward mouse/keyboard/touch input events
- Provide toolbar controls for VM lifecycle (start, pause, stop, snapshot)
- Display status indicators (CPU usage, FPS, memory)
- Host the app management sidebar and settings dialogs

### 2. Emulator Controller

The central orchestration component that manages the lifecycle of the emulated
machine. It coordinates startup sequencing, configuration loading, and the state
machine governing VM transitions.

State machine:
```
  [Stopped] --start--> [Booting] --ready--> [Running]
     ^                                          |
     |                    [Paused] <--pause-----+
     |                       |                  |
     +-------stop------------+------resume------+
```

Responsibilities:
- Parse and validate emulator configuration (YAML)
- Initialize subsystem managers in dependency order
- Manage VM state transitions with proper cleanup
- Provide snapshot save/restore coordination
- Handle graceful shutdown and error recovery

### 3. Subsystem Managers

#### CPU Manager
- Configures vCPU count (default: 2, max: host core count)
- Sets up KVM vCPU file descriptors via KVM_CREATE_VCPU
- Manages vCPU threads (one host thread per vCPU)
- Handles VMEXIT processing and interrupt injection
- Collects CPU performance metrics

#### Memory Manager
- Allocates guest physical memory via mmap (MAP_ANONYMOUS | MAP_PRIVATE)
- Registers memory regions with KVM via KVM_SET_USER_MEMORY_REGION
- Manages the shared framebuffer region (MAP_SHARED)
- Supports hugepages for reduced TLB pressure
- Monitors memory usage and enforces limits

#### Device Manager
- Maintains a registry of emulated devices
- Routes MMIO and PIO access to appropriate device handlers
- Manages device initialization and teardown order
- Supports hotplug for future extensibility
- Coordinates interrupt routing (IOAPIC emulation)

#### Display Manager
- Reads from the shared framebuffer memory region
- Converts raw pixel data (RGBA) to GTK-compatible format
- Manages refresh rate timing (target: 30 FPS)
- Handles resolution changes and rotation
- Provides screenshot capture functionality

### 4. Hardware Abstraction Layer (HAL)

The HAL provides a uniform interface that abstracts whether the underlying
execution engine is KVM-based or software-based. All upper layers interact
with the HAL interface, never directly with KVM ioctls or the software
interpreter.

```python
class EmulationBackend(Protocol):
    def create_vm(self) -> int: ...
    def create_vcpu(self, vm_fd: int, vcpu_id: int) -> int: ...
    def set_memory_region(self, vm_fd: int, slot: int,
                          guest_phys_addr: int, size: int,
                          host_virt_addr: int) -> None: ...
    def run_vcpu(self, vcpu_fd: int) -> VmExitReason: ...
    def get_regs(self, vcpu_fd: int) -> Registers: ...
    def set_regs(self, vcpu_fd: int, regs: Registers) -> None: ...
```

### 5. KVM / Software Emulation Core

#### KVM Backend (Primary)

Uses Linux KVM (Kernel-based Virtual Machine) for hardware-assisted
virtualization. This provides near-native execution speed for x86_64 guests
on x86_64 hosts.

**KVM ioctl sequence:**

1. Open `/dev/kvm` and verify API version (`KVM_GET_API_VERSION`)
2. Create VM (`KVM_CREATE_VM`) -> vm_fd
3. Set up guest memory regions (`KVM_SET_USER_MEMORY_REGION`)
4. Create vCPUs (`KVM_CREATE_VCPU`) -> vcpu_fd per core
5. Configure vCPU state (registers, CPUID, MSRs)
6. Enter run loop (`KVM_RUN`) per vCPU thread
7. Process VMEXITs (MMIO, PIO, HLT, shutdown)

**Key ioctls used:**

| ioctl | Purpose |
|-------|---------|
| `KVM_GET_API_VERSION` | Verify KVM API compatibility |
| `KVM_CREATE_VM` | Create a new virtual machine |
| `KVM_CHECK_EXTENSION` | Query KVM capability support |
| `KVM_CREATE_VCPU` | Create a virtual CPU |
| `KVM_RUN` | Execute guest code until VMEXIT |
| `KVM_SET_USER_MEMORY_REGION` | Map host memory into guest physical space |
| `KVM_SET_REGS` | Set general-purpose registers |
| `KVM_GET_REGS` | Read general-purpose registers |
| `KVM_SET_SREGS` | Set special registers (CR0, CR3, etc.) |
| `KVM_GET_SREGS` | Read special registers |
| `KVM_SET_CPUID2` | Configure CPUID responses |
| `KVM_CREATE_IRQCHIP` | Create in-kernel interrupt controller |
| `KVM_CREATE_PIT2` | Create in-kernel PIT timer |
| `KVM_SET_TSS_ADDR` | Set Task State Segment address |
| `KVM_SIGNAL_MSI` | Inject MSI interrupt |

**Performance characteristics:**
- Near-native CPU performance (within 5% of bare metal)
- Memory access at native speed (EPT/NPT hardware support)
- I/O emulation is the primary bottleneck

#### Software Fallback Backend

When KVM is unavailable (no hardware support, containerized environments,
or non-x86_64 hosts), a software interpreter executes x86_64 instructions.

**Characteristics:**
- Significantly slower (10-50x compared to KVM)
- Full x86_64 instruction set interpretation
- Useful for development and testing only
- Same HAL interface as KVM backend

## KVM Integration Approach

### Host Requirements
- x86_64 host CPU with VT-x (Intel) or AMD-V (AMD) support
- Linux kernel 5.10+ with KVM module loaded
- Read/write access to `/dev/kvm`
- User membership in the `kvm` group

### Guest Architecture
- x86_64 guest running Android 14 kernel (5.15 LTS)
- Guest boots in long mode (64-bit) with identity-mapped page tables initially
- UEFI boot not required; direct kernel boot supported
- Custom bootloader loads kernel + initramfs into guest memory

### vCPU Threading Model
```
Host Process
  |
  +-- Main Thread (GTK event loop, Emulator Controller)
  |
  +-- vCPU Thread 0 (KVM_RUN loop)
  |
  +-- vCPU Thread 1 (KVM_RUN loop)
  |
  +-- I/O Thread (device emulation, network)
  |
  +-- Display Thread (framebuffer refresh)
```

Each vCPU runs in a dedicated host thread. The KVM_RUN ioctl blocks until
a VMEXIT occurs, at which point the thread handles the exit reason (MMIO
access, PIO access, HLT, etc.) and re-enters the guest.

## Virtio Device Strategy

Virtio paravirtualized devices provide high-performance I/O by avoiding
full hardware emulation. The guest kernel includes virtio drivers, and the
host emulator implements the device backends.

### virtio-gpu (Display)
- **Purpose:** GPU rendering and display output
- **Implementation:** Virtio GPU device with 2D operations
- **Rendering:** OpenGL ES passthrough via virgl (optional) or software rendering via SwiftShader
- **Framebuffer:** Scanout to shared memory region consumed by GTK display widget
- **Resolution:** 1080x1920 default (portrait), configurable
- **Features:** Cursor plane, multiple scanouts (future multi-display)

### virtio-net (Network)
- **Purpose:** Guest network connectivity
- **Implementation:** Virtio network device with user-mode NAT
- **NAT:** SLIRP-style user-mode networking (no root required)
- **Guest IP:** 10.0.2.15/24 (default SLIRP subnet)
- **Host forwarding:** Configurable port forwarding (e.g., ADB on 5555)
- **Performance:** Adequate for app installation and light browsing
- **Future:** TAP backend option for bridged networking

### virtio-input (Input)
- **Purpose:** Touch, keyboard, and mouse event injection
- **Implementation:** Virtio input device presenting as multi-touch screen
- **Events:** Linux input event protocol (EV_ABS for touch, EV_KEY for keyboard)
- **Touch:** Multi-touch type B protocol, up to 10 simultaneous contacts
- **Mapping:** GTK mouse events translated to Android touch coordinates

### virtio-blk (Storage)
- **Purpose:** Block device for system, vendor, data partitions
- **Implementation:** Virtio block device backed by qcow2 images
- **Overlay:** Copy-on-write overlay for non-destructive modifications
- **Cache:** Writeback caching with periodic flush
- **Partitions:** Separate virtio-blk devices per Android partition
- **Shared storage:** Plan 9 filesystem (9pfs) for host directory sharing

### virtio-console (Debug)
- **Purpose:** Serial console for kernel and system debug output
- **Implementation:** Virtio console device connected to host terminal/log
- **Usage:** Kernel boot messages, Android logcat relay, ADB-over-serial
- **Multiplexing:** Multiple ports for different log streams

## Shared Memory Framebuffer

### Architecture
```
+-------------------+          +-------------------+
| Emulator Core     |          | GTK Display       |
|                   |   mmap   |                   |
| virtio-gpu ------>| shared  |-----> DrawingArea  |
| scanout writes    | memory  | reads & renders    |
|                   |          |                   |
| Buffer A (write)  |          | Buffer B (read)   |
| Buffer B (idle)   |          | Buffer A (idle)   |
+-------------------+          +-------------------+
```

### Implementation Details
- **Shared region:** Created via `mmap(MAP_SHARED)` on a memfd or `/dev/shm` file
- **Double buffering:** Two framebuffers to prevent tearing
  - Emulator writes to back buffer while GTK reads from front buffer
  - Atomic pointer swap signals buffer flip
- **Format:** RGBA8888 (4 bytes per pixel)
- **Resolution:** 1080 x 1920 pixels (portrait)
- **Buffer size:** 1080 * 1920 * 4 = 8,294,400 bytes (~7.9 MB per buffer)
- **Total shared region:** ~16 MB (two buffers + metadata)
- **Bandwidth:** At 30 FPS: 7.9 MB * 30 = ~237 MB/s
- **Synchronization:** Futex-based signaling between producer and consumer

### Synchronization Protocol
1. Emulator finishes rendering frame into back buffer
2. Emulator atomically swaps front/back buffer pointers
3. Emulator signals futex to wake display thread
4. Display thread reads front buffer into GTK surface
5. Display thread calls `queue_draw()` to trigger GTK repaint

## Module Mapping

| Component | Module | Interface | Layer |
|-----------|--------|-----------|-------|
| CPU Manager | `emulator_core` | `EmulatorCoreInterface` | emulation |
| Memory Manager | `emulator_core` (internal) | `GuestMemory` | emulation |
| Device Framework | `device_manager` | `DeviceManagerInterface` | emulation |
| Display Manager | `display_manager` | `DisplayManagerInterface` | emulation |
| Input Manager | `input_manager` | `InputManagerInterface` | emulation |
| Storage Manager | `storage_manager` | `StorageManagerInterface` | emulation |
| Network Manager | `network_manager` | `NetworkManagerInterface` | emulation |
| Emulator Controller | `emulator_controller` | `EmulatorControllerInterface` | emulation |
| GTK Display Widget | `gui_main` | `GUIInterface` | gui |
| App Manager | `app_manager` | `AppManagerInterface` | android |
| Config Manager | `config_manager` | `ConfigManagerInterface` | infrastructure |
| Log Manager | `log_manager` | `LogManagerInterface` | infrastructure |

## Interface Contracts

### EmulatorCoreInterface
```python
class EmulatorCoreInterface(Protocol):
    def initialize(self, config: dict) -> bool: ...
    def start(self) -> bool: ...
    def stop(self) -> None: ...
    def pause(self) -> None: ...
    def resume(self) -> None: ...
    def get_state(self) -> str: ...
    def save_snapshot(self, path: str) -> bool: ...
    def load_snapshot(self, path: str) -> bool: ...
```

### DeviceManagerInterface
```python
class DeviceManagerInterface(Protocol):
    def register_device(self, device: VirtioDevice) -> None: ...
    def remove_device(self, device_id: str) -> None: ...
    def get_device(self, device_id: str) -> Optional[VirtioDevice]: ...
    def handle_mmio(self, addr: int, size: int, is_write: bool,
                    data: bytes) -> Optional[bytes]: ...
    def handle_pio(self, port: int, size: int, is_write: bool,
                   data: bytes) -> Optional[bytes]: ...
```

### DisplayManagerInterface
```python
class DisplayManagerInterface(Protocol):
    def initialize(self, width: int, height: int) -> bool: ...
    def get_framebuffer(self) -> memoryview: ...
    def set_resolution(self, width: int, height: int) -> bool: ...
    def get_fps(self) -> float: ...
    def capture_screenshot(self, path: str) -> bool: ...
```

## Error Handling Strategy

1. **KVM initialization failure:** Fall back to software emulation with user notification
2. **Memory allocation failure:** Report error, suggest reducing guest RAM
3. **Device initialization failure:** Log error, continue without failed device if non-critical
4. **Guest crash:** Capture register state, offer snapshot restore
5. **Host resource exhaustion:** Graceful pause with user notification

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| Boot time | < 30 seconds | From VM start to Android home screen |
| Display FPS | 30 FPS sustained | Framebuffer refresh rate |
| Input latency | < 50 ms | Touch event to visual response |
| Memory overhead | < 1 GB | Emulator process RSS minus guest RAM |
| CPU idle usage | < 5% | Host CPU when guest is idle |

## Future Extensibility

- **GPU passthrough:** VFIO-based GPU passthrough for dedicated GPU scenarios
- **Multi-display:** Multiple virtio-gpu scanouts for multi-monitor emulation
- **Audio:** virtio-snd for audio output/input
- **Camera:** Virtual camera device with host webcam passthrough
- **Sensors:** Accelerometer, gyroscope simulation via host input
- **Snapshots:** Full VM state save/restore with memory compression
