# LinBlock Emulator Architecture

## Overview

The LinBlock emulator provides a full x86_64 virtual machine environment capable of running
Android-x86 (currently 9.0-r2, with Android 14 planned) with near-native performance using
QEMU with KVM hardware-assisted virtualization. The architecture uses QEMU as the
virtualization backend, providing excellent hardware compatibility and mature device
emulation. The system is organized into layered components with well-defined interfaces
to support modularity, testability, and future extensibility.

## Component Diagram

```
+-------------------------------------------+
|              GTK GUI Layer                |
|  (Dashboard, VNC Display, Device Panel)   |
+-------------------------------------------+
|           Emulator Controller             |
|  (Lifecycle, Config, State Machine)       |
+----------+----------+----------+----------+
|   QEMU   |  Profile | Logging  | Display  |
| Process  |  Manager | Manager  | Manager  |
+----------+----------+----------+----------+
|         QEMU System Emulator              |
|  (qemu-system-x86_64 with KVM accel)     |
+-------------------------------------------+
|            KVM Hypervisor                 |
|  (/dev/kvm hardware virtualization)       |
+-------------------------------------------+
|          Host Linux Kernel                |
+-------------------------------------------+
```

## Architectural Layers

### 1. GTK GUI Layer

The topmost layer handles all user-facing interaction. It is implemented using
PyGObject (GTK 3) and runs in the main process thread. The GUI layer communicates
with the Emulator Controller through a well-defined Python API and receives
display output via VNC connection to QEMU.

Responsibilities:
- Render the emulated Android display via VNC widget (GtkVncDisplay)
- Capture and forward mouse/keyboard/touch input events through VNC
- Provide sidebar navigation (About, Load OS, OS List, Running OS)
- Device controls panel for power, reset, screenshot, recording, logging
- Conditional controls for WiFi, Bluetooth, brightness, volume, etc.
- Settings dialogs for profile configuration

### 2. Emulator Controller

The central orchestration component that manages the lifecycle of the QEMU
virtual machine. It coordinates startup sequencing, configuration loading,
profile management, and the state machine governing VM transitions.

State machine:
```
  [Stopped] --start--> [Booting] --ready--> [Running]
     ^                                          |
     |                    [Paused] <--pause-----+
     |                       |                  |
     +-------stop------------+------resume------+
```

Responsibilities:
- Parse and validate OS profile configuration (YAML)
- Build QEMU command-line arguments from profile settings
- Manage QEMU process lifecycle (start, stop, reset)
- Handle boot configuration (direct kernel vs CD-ROM boot)
- Configure GPU mode (software, host, virgl)
- Set up serial console logging with timestamps
- Port management for VNC and ADB connections
- Handle graceful shutdown and orphaned process cleanup

### 3. Subsystem Managers

#### QEMU Process Manager
- Builds QEMU command-line from profile configuration
- Manages QEMU subprocess lifecycle
- Handles process termination and cleanup
- Monitors process health and restarts if needed
- Registers cleanup handlers for signal/atexit

#### Profile Manager
- Loads OS profiles from YAML configuration files
- Validates profile settings (boot config, paths, parameters)
- Supports profile creation, editing, duplication, deletion
- Auto-detects ISO files and extracts kernel/initrd
- Manages per-profile storage directories (screenshots, videos, logs)

#### Logging Manager
- Captures QEMU serial console output to timestamped files
- Stores logs in `~/LinBlock/{profile}/logging/boot_{timestamp}.log`
- Provides "View Logs" functionality to open log directory
- Always enabled for debugging and troubleshooting

#### Display Manager
- Connects to QEMU VNC server (localhost:5900+)
- Renders display output in GTK VNC widget
- Handles resolution changes and scaling
- Provides screenshot capture functionality
- Supports video recording (planned)

### 4. QEMU Backend

LinBlock uses QEMU (qemu-system-x86_64) as the virtualization backend. QEMU provides
mature hardware emulation, excellent device support, and integrates seamlessly with
KVM for hardware-accelerated virtualization.

#### QEMU Integration

**Machine Configuration:**
```bash
qemu-system-x86_64 \
  -machine pc,accel=kvm \
  -enable-kvm \
  -cpu host \
  -smp {cpu_cores} \
  -m {ram_mb}M
```

**Boot Modes:**

1. **Direct Kernel Boot** (Recommended for Android-x86):
   - Extract kernel and initrd from ISO
   - Boot directly with custom kernel parameters
   - Faster boot, more control over parameters
   ```bash
   -kernel /path/to/kernel \
   -initrd /path/to/initrd.img \
   -append "console=ttyS0 root=/dev/ram0 nomodeset HWACCEL=0"
   ```

2. **CD-ROM Boot** (GRUB menu):
   - Boot from ISO directly
   - Uses GRUB bootloader for menu selection
   ```bash
   -cdrom /path/to/android.iso \
   -boot order=d,menu=on
   ```

#### GPU Modes

| Mode | QEMU Flag | Description | Use Case |
|------|-----------|-------------|----------|
| Software | `-vga std` | Standard VGA, CPU rendering | Most compatible, first boot |
| Host | `-device virtio-gpu-pci` | Virtio GPU device | Host GPU passthrough |
| Virgl | `-device virtio-gpu-pci,virgl=on` | OpenGL passthrough | Experimental acceleration |

**Software Rendering** (Recommended for Android-x86):
- Uses `-vga std` with `-global VGA.vgamem_mb=64`
- Requires kernel parameters: `nomodeset HWACCEL=0`
- Most compatible with Android-x86 SurfaceFlinger

### 5. KVM Acceleration

When KVM is available (`/dev/kvm` exists and user is in `kvm` group), QEMU uses
hardware-assisted virtualization for near-native performance.

**Verification:**
```bash
ls -la /dev/kvm
groups | grep kvm
```

**Performance characteristics:**
- Near-native CPU performance (within 5% of bare metal)
- Memory access at native speed (EPT/NPT hardware support)
- I/O emulation handled by QEMU

**Fallback without KVM:**
- QEMU uses TCG (Tiny Code Generator) software emulation
- Significantly slower but functional
- GUI shows warning indicator in Performance section

## QEMU Configuration

### Host Requirements
- x86_64 host CPU with VT-x (Intel) or AMD-V (AMD) support
- Linux kernel 5.10+ with KVM module loaded
- QEMU 6.0+ installed (`qemu-system-x86_64`)
- Read/write access to `/dev/kvm`
- User membership in the `kvm` group

### Guest Architecture
- x86_64 guest running Android-x86 (currently 9.0-r2, kernel 4.19)
- Future: Android 14 (API 34) with kernel 5.15 LTS
- Direct kernel boot from extracted kernel/initrd
- CD-ROM provides system.sfs and other Android files

### Process Model
```
LinBlock GTK Application
  |
  +-- Main Thread (GTK event loop, UI rendering)
  |
  +-- QEMU subprocess (qemu-system-x86_64)
        |
        +-- vCPU threads (managed by QEMU)
        +-- VNC server (port 5900+)
        +-- Serial console (to log file)
        +-- Network (user-mode NAT)
```

LinBlock manages QEMU as a subprocess. Communication occurs via:
- VNC for display output and input
- Serial console for logging
- QMP (QEMU Monitor Protocol) for control commands (future)

### Network Configuration
```bash
-netdev user,id=net0,hostfwd=tcp::5555-:5555 \
-device e1000,netdev=net0,romfile=
```

- User-mode networking (no root required)
- ADB port forwarding (5555 -> guest 5555)
- Dynamic port allocation if 5555 is in use

## Device Configuration

QEMU provides comprehensive device emulation. The current configuration uses
proven, compatible devices for maximum stability with Android-x86.

### Display (VGA/VNC)
- **Software Mode:** `-vga std -global VGA.vgamem_mb=64`
- **VNC Server:** `-vnc :0` (port 5900)
- **Resolution:** Configurable (default 1080x1920 portrait)
- **Access:** GTK VNC widget connects to localhost:5900

### Network (e1000)
- **Device:** Intel e1000 NIC (`-device e1000,netdev=net0,romfile=`)
- **Backend:** User-mode networking (`-netdev user,id=net0`)
- **ADB:** Port forwarding `hostfwd=tcp::5555-:5555`
- **Guest IP:** 10.0.2.15/24 (QEMU SLIRP default)
- **Dynamic ports:** Auto-increment if 5555 is occupied

### Input (USB Tablet)
- **Device:** `-usb -device usb-tablet`
- **Purpose:** Absolute pointer positioning for VNC
- **Touch:** VNC sends mouse events as touch input

### Storage (CD-ROM)
- **Boot Image:** `-cdrom /path/to/android.iso`
- **Contains:** kernel, initrd, system.sfs, ramdisk
- **Future:** virtio-blk for persistent data partitions

### Serial Console
- **Config:** `-serial file:/path/to/boot.log`
- **Kernel param:** `console=ttyS0`
- **Purpose:** Boot logging, debugging, troubleshooting
- **Storage:** `~/LinBlock/{profile}/logging/boot_{timestamp}.log`

### Random Number Generator
- **Device:** `-device virtio-rng-pci`
- **Purpose:** Entropy source for Android (required for crypto)

### Future Devices (Planned)
- **virtio-gpu:** Hardware-accelerated graphics
- **virtio-blk:** Persistent storage with qcow2 overlay
- **virtio-snd:** Audio output/input
- **9pfs:** Host directory sharing

## VNC Display Architecture

### Architecture
```
+-------------------+          +-------------------+
| QEMU Process      |   VNC    | GTK Application   |
|                   | Protocol |                   |
| VGA Device ------>| :5900   |-----> GtkVncDisplay|
| frame renders     |          | decodes & renders |
|                   |          |                   |
| VNC Server        |  <----   | VNC Client        |
| (built-in)        |  input   | (gtk-vnc)         |
+-------------------+          +-------------------+
```

### Implementation Details
- **VNC Server:** QEMU built-in VNC server (`-vnc :0`)
- **VNC Client:** gtk-vnc library (GtkVncDisplay widget)
- **Protocol:** RFB (Remote Framebuffer) protocol
- **Encoding:** Tight, ZRLE, or Raw depending on content
- **Resolution:** Configurable via guest, scaled in GTK widget
- **Input:** Mouse and keyboard events sent via VNC protocol
- **Latency:** Typically <50ms for local connections

### Display Flow
1. QEMU VGA device renders frame to internal framebuffer
2. VNC server encodes changed regions
3. GTK VNC widget receives and decodes updates
4. Widget redraws affected areas
5. Input events from widget sent back to QEMU

## Module Mapping

| Component | Module/File | Description | Layer |
|-----------|-------------|-------------|-------|
| QEMU Process | `emulator_core/internal/qemu_process.py` | QEMU subprocess management | emulation |
| Boot Config | `emulator_core/internal/qemu_process.py` | Kernel boot configuration | emulation |
| Emulator Interface | `emulator_core/interface.py` | `EmulatorCoreInterface` ABC | emulation |
| Profile Manager | `src/utils/profile_manager.py` | Profile discovery and loading | infrastructure |
| OS Profile | `src/config/os_profile.py` | OSProfile dataclass + YAML I/O | infrastructure |
| Dashboard Window | `src/ui/dashboard_window.py` | Main GTK window, cleanup handlers | gui |
| Sidebar | `src/ui/sidebar.py` | Navigation sidebar | gui |
| Device Controls | `src/ui/components/device_controls.py` | Power, reset, screenshot, logs | gui |
| Emulator Display | `src/ui/components/emulator_display.py` | VNC display widget | gui |
| Load OS Page | `src/pages/load_os_page.py` | Profile creation with boot config | gui |
| OS List Page | `src/pages/os_list_page.py` | Profile management | gui |
| Running OS Page | `src/pages/running_os_page.py` | Active emulator view | gui |

## Interface Contracts

### EmulatorCoreInterface
```python
class EmulatorCoreInterface(ABC):
    @abstractmethod
    def initialize(self, profile: OSProfile) -> None: ...
    @abstractmethod
    def start(self) -> None: ...
    @abstractmethod
    def stop(self) -> None: ...
    @abstractmethod
    def pause(self) -> None: ...
    @abstractmethod
    def resume(self) -> None: ...
    @abstractmethod
    def reset(self) -> None: ...
    @abstractmethod
    def get_state(self) -> VMState: ...
    @abstractmethod
    def get_vnc_port(self) -> int: ...
    @abstractmethod
    def cleanup(self) -> None: ...
```

### OSProfile (dataclass)
```python
@dataclass
class OSProfile:
    name: str
    image_path: str
    device: DeviceConfig
    graphics: GraphicsConfig
    performance: PerformanceConfig
    boot: BootConfig
    network: NetworkConfig
    ...
```

### BootConfig (dataclass)
```python
@dataclass
class BootConfig:
    kernel: str = ""           # Path to kernel image
    initrd: str = ""           # Path to initrd/ramdisk
    system_image: str = ""     # Path to system.img
    kernel_cmdline: str = ""   # Kernel command line
    cdrom_image: str = ""      # Path to ISO for CD-ROM boot
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
| Boot time | < 60 seconds | From VM start to Android setup wizard |
| Display FPS | 30 FPS sustained | VNC refresh rate |
| Input latency | < 100 ms | Touch event to visual response |
| Memory overhead | < 500 MB | LinBlock process (QEMU manages guest RAM) |
| CPU idle usage | < 10% | Host CPU when guest is idle |

## Known Working Configuration

### Android-x86 9.0-r2 (Verified)
```yaml
boot:
  kernel: /path/to/boot/kernel
  initrd: /path/to/boot/initrd.img
  cdrom_image: /path/to/android-x86-9.0-r2.iso
  kernel_cmdline: "root=/dev/ram0 androidboot.selinux=permissive quiet nomodeset HWACCEL=0"
graphics:
  gpu_mode: software
performance:
  cpu_cores: 4
  ram_mb: 4096
  hypervisor: kvm
```

### Kernel Parameters Reference

| Parameter | Required | Description |
|-----------|----------|-------------|
| `root=/dev/ram0` | Yes | Boot from ramdisk |
| `console=ttyS0` | Recommended | Enable serial logging |
| `androidboot.selinux=permissive` | Recommended | Avoid SELinux denials |
| `nomodeset` | For software GPU | Disable kernel mode setting |
| `HWACCEL=0` | For software GPU | Use software renderer |
| `quiet` | Optional | Reduce boot verbosity |
| `DEBUG=2` | Optional | Enable Android debug mode |

## Future Extensibility

- **Android 14:** Upgrade to Android 14 (API 34) with kernel 5.15
- **GPU passthrough:** virtio-gpu with virgl for OpenGL acceleration
- **Persistent storage:** qcow2 images for data partition
- **Audio:** virtio-snd for audio output/input
- **Camera:** Virtual camera with host webcam passthrough
- **Sensors:** Accelerometer, gyroscope simulation
- **Snapshots:** QEMU savevm/loadvm for full state save/restore
- **QMP:** QEMU Monitor Protocol for programmatic control
