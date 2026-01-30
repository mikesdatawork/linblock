# Android-x86 Boot Troubleshooting Guide

## Technical Document: LinBlock Android-x86 Emulation

**Date:** 2026-01-29
**Version:** 1.0
**Status:** Resolved

---

## Executive Summary

This document details the issues encountered while configuring Android-x86 9.0-r2 to boot successfully in the LinBlock emulator, the diagnostic process, resolutions applied, and recommendations for improving the "Load OS" page to prevent similar issues in the future.

---

## 1. Issues Encountered

### 1.1 "No Bootable Device" Error

**Symptom:** QEMU displayed "No bootable device" when attempting to power on the profile.

**Root Cause:** The OS profile was created without proper boot configuration. The `boot` section in the profile YAML was empty or missing kernel/initrd/cdrom paths.

**Technical Details:**
- Profile pointed to an image directory but had no boot configuration
- QEMU had no system image, kernel, or CD-ROM to boot from

### 1.2 Port Conflict Error

**Symptom:** Error message: `Could not set up host forwarding rule 'tcp::5555-:5555'`

**Root Cause:** ADB port 5555 was already in use by another process or a previous QEMU instance that wasn't properly cleaned up.

**Technical Details:**
- QEMU network configuration uses user-mode networking with port forwarding
- Port 5555 is the default ADB port for Android emulators

### 1.3 Boot Stuck at "Detecting Android-x86"

**Symptom:** Serial console showed `Detecting Android-x86...` but never progressed.

**Root Cause:** Initial boot attempts used direct kernel boot without proper kernel command line parameters to locate the system image.

**Technical Details:**
- Android-x86 init script searches for system files based on `SRC=` parameter
- Without proper parameters, init couldn't find system.sfs

### 1.4 Boot Stuck at Android Logo (Boot Animation)

**Symptom:** Android logo displayed indefinitely, system never reached the home screen or setup wizard.

**Root Cause:** GPU/graphics incompatibility between QEMU's virtio-vga device and Android-x86's SurfaceFlinger.

**Technical Details:**
- `virtio-vga` and `qxl-vga` devices require specific guest drivers
- Android-x86 SurfaceFlinger couldn't initialize OpenGL context
- Hardware acceleration (`HWACCEL=1`) was enabled by default
- The graphics stack was waiting for a GPU that wasn't properly emulated

### 1.5 Orphaned QEMU Processes

**Symptom:** When the LinBlock application crashed or was closed, QEMU processes continued running in the background.

**Root Cause:** No cleanup handlers were registered for application shutdown.

**Technical Details:**
- GTK application destroy signal wasn't connected to cleanup
- No signal handlers for SIGINT/SIGTERM
- No atexit handler for unexpected exits

### 1.6 "View Logs" Button Crash

**Symptom:** Clicking "View Logs" button caused application crash.

**Root Cause:** Under investigation - likely file manager subprocess issue or path handling.

---

## 2. Diagnostic Process

### 2.1 Log Analysis

Serial console logging was enabled via QEMU's `-serial file:` option. Logs captured:

```
[    0.000000] Linux version 4.19.110-android-x86_64...
[    0.979263] Run /init as init process
Detecting Android-x86... found at /dev/sr0
console:/ #
```

**Key Findings:**
- Kernel booted successfully (sub-1-second boot to init)
- Android init ran and detected system at `/dev/sr0` (CD-ROM)
- Shell prompt appeared, confirming basic Android functionality
- Issue was in graphics layer, not boot process

### 2.2 GRUB Configuration Analysis

Extracted and analyzed Android-x86 ISO's GRUB configuration:

```bash
7z e -so android-x86-9.0-r2.iso efi/boot/android.cfg
```

**Discovered boot options:**
- `quiet` - Reduce boot verbosity
- `nomodeset` - Disable kernel mode setting
- `HWACCEL=0` - Disable hardware acceleration (software rendering)
- `DEBUG=2` - Enable debug mode

### 2.3 ISO Structure Analysis

```
android-x86-9.0-r2.iso
├── kernel (7.5MB)
├── initrd.img (1.3MB)
├── system.sfs (900MB) - Main system image
├── ramdisk.img (1.9MB)
└── boot/grub/ - GRUB bootloader
```

---

## 3. Resolutions Applied

### 3.1 Boot Configuration Fix

**Solution:** Added `BootConfig` dataclass to `os_profile.py`:

```python
@dataclass
class BootConfig:
    kernel: str = ""           # Path to kernel image
    initrd: str = ""           # Path to initrd/ramdisk
    system_image: str = ""     # Path to system.img
    kernel_cmdline: str = ""   # Kernel command line parameters
    cdrom_image: str = ""      # Path to ISO for CD-ROM boot
```

### 3.2 Dynamic Port Allocation

**Solution:** Added port availability checking in `qemu_process.py`:

```python
def _is_port_available(port: int) -> bool:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False

def _find_available_port(start_port: int, max_attempts: int = 100) -> int:
    for offset in range(max_attempts):
        port = start_port + offset
        if _is_port_available(port):
            return port
    raise RuntimeError(f"Could not find available port")
```

### 3.3 Direct Kernel Boot with Software Rendering

**Solution:** Extract kernel/initrd from ISO and boot directly with proper parameters:

```bash
# Extract from ISO
7z e -o./boot android-x86-9.0-r2.iso kernel initrd.img

# Profile configuration
boot:
  kernel: /path/to/boot/kernel
  initrd: /path/to/boot/initrd.img
  cdrom_image: /path/to/android-x86-9.0-r2.iso
  kernel_cmdline: "root=/dev/ram0 androidboot.selinux=permissive quiet nomodeset HWACCEL=0"

graphics:
  gpu_mode: software
```

### 3.4 GPU Configuration Fix

**Solution:** Updated QEMU GPU device selection in `qemu_process.py`:

```python
if self._config.gpu_mode == "host":
    cmd.extend(["-device", "virtio-gpu-pci"])
elif self._config.gpu_mode == "virgl":
    cmd.extend(["-device", "virtio-gpu-pci,virgl=on"])
else:
    # Software mode: use standard VGA - most compatible
    cmd.extend(["-vga", "std"])
```

### 3.5 Cleanup Handlers

**Solution:** Added comprehensive cleanup in `main.py`:

```python
# Signal handlers
signal.signal(signal.SIGINT, _signal_handler)
signal.signal(signal.SIGTERM, _signal_handler)
atexit.register(_cleanup_handler)

# GTK signal handling
GLib.unix_signal_add(GLib.PRIORITY_HIGH, signal.SIGINT, ...)

# Window destroy handler
self.connect("destroy", self._on_destroy)
```

---

## 4. Working Configuration

### 4.1 Profile YAML (Verified Working)

```yaml
name: Android 9 Phone
image_path: /home/user/LinBlock/images/android-x86-9.0-r2

boot:
  cdrom_image: /path/to/android-x86-9.0-r2.iso
  kernel: /path/to/boot/kernel
  initrd: /path/to/boot/initrd.img
  system_image: ""
  kernel_cmdline: "root=/dev/ram0 androidboot.selinux=permissive quiet nomodeset HWACCEL=0"

graphics:
  api: opengl
  gpu_mode: software
  renderer: auto

performance:
  cpu_cores: 4
  hypervisor: kvm
  ram_mb: 4096

device:
  screen_width: 1080
  screen_height: 1920
  screen_preset: phone
```

### 4.2 Required Kernel Command Line Parameters

| Parameter | Required | Description |
|-----------|----------|-------------|
| `root=/dev/ram0` | Yes | Boot from ramdisk |
| `console=ttyS0` | Recommended | Enable serial console logging |
| `androidboot.selinux=permissive` | Recommended | Avoid SELinux denials |
| `nomodeset` | For software rendering | Disable kernel mode setting |
| `HWACCEL=0` | For software rendering | Use software renderer |
| `quiet` | Optional | Reduce boot messages |
| `DEBUG=2` | Optional | Enable Android debug mode |

### 4.3 QEMU Command Line (Generated)

```bash
qemu-system-x86_64 \
  -machine pc,accel=kvm \
  -enable-kvm \
  -cpu host \
  -smp 4 \
  -m 4096M \
  -kernel /path/to/kernel \
  -initrd /path/to/initrd.img \
  -append "console=ttyS0 root=/dev/ram0 androidboot.selinux=permissive quiet nomodeset HWACCEL=0" \
  -cdrom /path/to/android-x86-9.0-r2.iso \
  -vga std \
  -global VGA.vgamem_mb=64 \
  -vnc :0 \
  -serial file:/path/to/boot.log \
  -netdev user,id=net0,hostfwd=tcp::5555-:5555 \
  -device e1000,netdev=net0,romfile= \
  -usb -device usb-tablet \
  -device virtio-rng-pci \
  -boot order=d,menu=on
```

---

## 5. Recommendations for "Load OS" Page

### 5.1 Auto-Detection Improvements

The "Load OS" page should automatically detect and configure:

1. **ISO Detection:**
   - Scan selected image directory for `.iso` files
   - Extract kernel/initrd from ISO automatically
   - Parse GRUB config to determine available boot options

2. **Boot Mode Selection:**
   ```
   [ ] CD-ROM Boot (GRUB menu - manual selection)
   [x] Direct Kernel Boot (Recommended - faster, configurable)
   ```

3. **Graphics Mode Selection:**
   ```
   [ ] Hardware Acceleration (Requires compatible GPU passthrough)
   [x] Software Rendering (Most compatible - recommended for first boot)
   [ ] Virgil3D (Experimental OpenGL passthrough)
   ```

### 5.2 Recommended UI Additions

#### Boot Configuration Section
```
┌─ Boot Configuration ─────────────────────────────────┐
│ Boot Mode: [Direct Kernel ▼]                         │
│                                                      │
│ Kernel:  [/path/to/kernel        ] [Auto-detect]    │
│ Initrd:  [/path/to/initrd.img    ] [Auto-detect]    │
│ CD-ROM:  [/path/to/android.iso   ] [Browse...]      │
│                                                      │
│ Kernel Parameters:                                   │
│ [root=/dev/ram0 quiet nomodeset HWACCEL=0         ] │
│                                                      │
│ Presets: [Software Rendering ▼]                      │
│          ├─ Software Rendering (nomodeset HWACCEL=0)│
│          ├─ Hardware Acceleration                    │
│          ├─ Debug Mode (DEBUG=2)                     │
│          └─ Custom...                                │
└──────────────────────────────────────────────────────┘
```

#### Validation Checks
Before saving profile, validate:
- [ ] Kernel file exists (if direct boot)
- [ ] Initrd file exists (if direct boot)
- [ ] ISO/system image exists
- [ ] Ports 5555+ and 5900+ are available
- [ ] KVM is available (warn if not)

### 5.3 Profile Templates

Provide pre-configured templates:

| Template | Use Case | GPU Mode | Notes |
|----------|----------|----------|-------|
| Android-x86 (Safe) | First boot, testing | Software | Most compatible |
| Android-x86 (Fast) | Daily use | Host | Requires working virtio-gpu |
| Android-x86 (Debug) | Development | Software | DEBUG=2, verbose logging |

### 5.4 ISO Processing Workflow

When user selects an Android-x86 ISO:

```
1. Detect ISO type (Android-x86, BlissOS, PrimeOS, etc.)
2. Extract kernel + initrd to profile directory
3. Parse GRUB config for boot options
4. Set recommended defaults based on ISO type
5. Display summary with "Advanced Options" expander
```

---

## 6. Parameters Reference

### 6.1 Modifiable Parameters

| Parameter | Location | Default | Range/Options |
|-----------|----------|---------|---------------|
| RAM | performance.ram_mb | 4096 | 1024-16384 MB |
| CPU Cores | performance.cpu_cores | 4 | 1-8 |
| Screen Width | device.screen_width | 1080 | 320-3840 |
| Screen Height | device.screen_height | 1920 | 480-2160 |
| GPU Mode | graphics.gpu_mode | software | host, software, virgl |
| ADB Port | adb.port | 5555 | 5555-5600 |
| VNC Port | (internal) | 5900 | 5900-5999 |

### 6.2 Fixed/Derived Parameters

| Parameter | Value | Notes |
|-----------|-------|-------|
| Machine Type | pc | i440FX for compatibility |
| Network | e1000 | Reliable, well-supported |
| USB | usb-tablet | Absolute pointer for VNC |
| RNG | virtio-rng-pci | Required for Android entropy |

---

## 7. Troubleshooting Checklist

### Boot Issues
- [ ] Check kernel/initrd paths exist
- [ ] Verify ISO is valid (7z l /path/to/iso)
- [ ] Review serial log for errors
- [ ] Try software rendering mode first

### Graphics Issues
- [ ] Set gpu_mode: software
- [ ] Add nomodeset to kernel cmdline
- [ ] Add HWACCEL=0 to kernel cmdline
- [ ] Check VNC connection (localhost:5900)

### Network Issues
- [ ] Verify ADB port is available
- [ ] Check for conflicting QEMU instances
- [ ] Try alternative port (5556, 5557, etc.)

### Performance Issues
- [ ] Verify KVM is enabled (/dev/kvm exists)
- [ ] Check host CPU supports virtualization
- [ ] Increase RAM allocation
- [ ] Reduce screen resolution for software rendering

---

## 8. Conclusion

The Android-x86 boot issues were primarily caused by:

1. **Missing boot configuration** in profiles
2. **GPU incompatibility** with default virtio-vga device
3. **Lack of software rendering fallback**

The resolutions involved:
1. Adding proper boot configuration with kernel/initrd extraction
2. Implementing software rendering mode with `-vga std`
3. Using correct kernel parameters (`nomodeset HWACCEL=0`)
4. Adding cleanup handlers for process management

The "Load OS" page should be enhanced with:
- Automatic ISO detection and kernel extraction
- Boot mode presets (Software/Hardware/Debug)
- Validation checks before profile creation
- Clear documentation of available options

---

*Document generated by LinBlock development team*
