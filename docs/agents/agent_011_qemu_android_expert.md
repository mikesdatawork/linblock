# Agent 011: QEMU & Android x86 Expert

## Role

Technical specialist for QEMU virtualization and Android x86 system configuration.
Responsible for ensuring proper VM configuration, boot processes, and Android
system compatibility within the LinBlock emulator.

## Expertise Areas

### 1. QEMU Configuration for Android

#### Machine Type Selection
```
-machine pc,accel=kvm      # Standard PC with KVM acceleration
-machine q35,accel=kvm     # Modern chipset (better for newer Android)
```

**Recommendation:** Use `pc` for Android 7-9, `q35` for Android 10+.

#### CPU Configuration
```bash
# With KVM (recommended for performance)
-enable-kvm
-cpu host                   # Pass through host CPU features

# Without KVM (fallback)
-cpu qemu64                 # Basic x86_64 emulation
-cpu Haswell                # Better compatibility
```

#### Memory Configuration
```bash
-m 4096M                    # 4GB RAM (minimum recommended)
-m 8192M                    # 8GB RAM (for heavy workloads)
```

**Android Memory Requirements:**
- Minimum: 2GB (Android 7-8)
- Recommended: 4GB (Android 9-11)
- Optimal: 8GB (Android 12+, multi-app scenarios)

### 2. Android x86 Boot Process

#### Boot Components

1. **Kernel** (`kernel`)
   - Linux kernel compiled for x86_64
   - Located at ISO root or `/boot/kernel`
   - Must match Android version

2. **Initial Ramdisk** (`initrd.img`)
   - Contains init system and early boot scripts
   - Mounts system partition
   - Starts Android init process

3. **System Image** (`system.img` or `system.sfs`)
   - Contains Android OS files
   - May be raw ext4 or squashfs compressed
   - Mounted at `/system`

#### Boot Sequence
```
QEMU BIOS → Kernel → initrd → Android init → Zygote → System Server → Launcher
```

### 3. Kernel Command Line Parameters

#### Essential Parameters
```bash
# Root filesystem
root=/dev/ram0              # Boot from ramdisk
root=/dev/sda               # Boot from disk (requires proper partitioning)

# Console output
console=ttyS0               # Serial console for logging
console=tty0                # VGA console

# Android-specific
androidboot.hardware=ranchu         # Hardware profile name
androidboot.serialno=EMULATOR       # Device serial number
androidboot.console=ttyS0           # Android console device
```

#### SELinux Configuration
```bash
androidboot.selinux=permissive      # Permissive mode (recommended for testing)
androidboot.selinux=enforcing       # Enforcing mode (production)
```

#### Debug Parameters
```bash
buildvariant=userdebug              # Enable debug features
printk.devkmsg=on                   # Kernel message logging
loglevel=7                          # Maximum kernel logging
```

#### Graphics Parameters
```bash
video=1080x1920                     # Display resolution
vga=791                             # VGA mode (1024x768x16)
nomodeset                           # Disable kernel mode setting (fallback)
```

#### Complete Example
```bash
KERNEL_CMDLINE="root=/dev/ram0 \
    console=ttyS0 \
    androidboot.hardware=ranchu \
    androidboot.serialno=LINBLOCK01 \
    androidboot.console=ttyS0 \
    androidboot.selinux=permissive \
    buildvariant=userdebug \
    video=1080x1920"
```

### 4. QEMU Device Configuration

#### Storage Devices
```bash
# System image (IDE - most compatible)
-drive file=system.img,format=raw,if=ide,index=0

# System image (virtio - better performance)
-drive file=system.img,format=raw,if=virtio

# Userdata partition
-drive file=userdata.qcow2,format=qcow2,if=ide,index=1

# SD card
-drive file=sdcard.img,format=raw,if=sd
```

#### Display Devices
```bash
# VirtIO VGA (best performance with KVM)
-device virtio-vga,xres=1080,yres=1920

# QXL (good for software rendering)
-device qxl-vga,xres=1080,yres=1920

# Standard VGA (maximum compatibility)
-vga std

# VNC output
-vnc :0                     # Listen on port 5900
-vnc :0,password            # Require password
```

#### Network Devices
```bash
# User-mode networking with port forwarding
-netdev user,id=net0,hostfwd=tcp::5555-:5555
-device e1000,netdev=net0

# VirtIO networking (better performance)
-netdev user,id=net0,hostfwd=tcp::5555-:5555
-device virtio-net-pci,netdev=net0
```

#### USB Devices
```bash
-usb
-device usb-tablet          # Absolute positioning (recommended)
-device usb-mouse           # Relative positioning
-device usb-kbd             # USB keyboard
```

#### Audio Devices
```bash
-device intel-hda
-device hda-duplex          # Audio input/output
```

### 5. Android x86 Versions & Compatibility

| Version | Codename | Kernel | QEMU Compatibility | Notes |
|---------|----------|--------|-------------------|-------|
| 7.1-r5  | Nougat   | 4.9    | Excellent         | Most stable |
| 8.1-r6  | Oreo     | 4.9    | Excellent         | Good balance |
| 9.0-r2  | Pie      | 4.19   | Excellent         | Recommended |
| 10.0    | Q        | 5.4    | Good              | Needs q35 |
| 11.0    | R        | 5.10   | Fair              | Experimental |

### 6. Common Issues & Solutions

#### Issue: "No bootable device"
**Cause:** Missing kernel/initrd or incorrect boot configuration.
**Solution:**
```bash
# Ensure kernel and initrd are specified
-kernel /path/to/kernel
-initrd /path/to/initrd.img
-append "root=/dev/ram0 androidboot.selinux=permissive"
```

#### Issue: Black screen after boot
**Cause:** Graphics driver incompatibility.
**Solution:**
```bash
# Try different VGA devices
-device virtio-vga          # First choice
-device qxl-vga             # Second choice
-vga std                    # Fallback

# Add nomodeset to kernel cmdline
-append "... nomodeset"
```

#### Issue: No network connectivity
**Cause:** Network device not recognized by Android.
**Solution:**
```bash
# Use e1000 (Intel) network adapter
-device e1000,netdev=net0

# Ensure proper netdev configuration
-netdev user,id=net0,hostfwd=tcp::5555-:5555
```

#### Issue: Slow performance
**Cause:** KVM not enabled or improper CPU configuration.
**Solution:**
```bash
# Verify KVM is available
ls -la /dev/kvm

# Enable KVM acceleration
-enable-kvm -cpu host

# Allocate sufficient memory
-m 4096
```

#### Issue: Touch input not working
**Cause:** Using relative mouse device.
**Solution:**
```bash
# Use USB tablet for absolute positioning
-usb -device usb-tablet
```

#### Issue: ADB not connecting
**Cause:** Port forwarding not configured or ADB daemon not running.
**Solution:**
```bash
# Ensure port forwarding
-netdev user,id=net0,hostfwd=tcp::5555-:5555

# Connect from host
adb connect localhost:5555
```

### 7. Performance Optimization

#### KVM Tuning
```bash
# Huge pages (requires host configuration)
-mem-path /dev/hugepages
-mem-prealloc

# CPU pinning (via taskset)
taskset -c 0-3 qemu-system-x86_64 ...
```

#### I/O Optimization
```bash
# Use virtio for disks
-drive file=system.img,if=virtio,cache=writeback

# Enable native AIO
-drive file=system.img,if=virtio,aio=native,cache=none
```

#### Memory Optimization
```bash
# Disable balloon device if not needed
# Enable KSM on host for memory deduplication
echo 1 > /sys/kernel/mm/ksm/run
```

### 8. LinBlock-Specific Configuration

#### Recommended QEMU Command Template
```bash
qemu-system-x86_64 \
    -machine pc,accel=kvm \
    -enable-kvm \
    -cpu host \
    -smp 4 \
    -m 4096M \
    -kernel /path/to/kernel \
    -initrd /path/to/initrd.img \
    -append "root=/dev/ram0 console=ttyS0 androidboot.hardware=ranchu androidboot.selinux=permissive" \
    -drive file=/path/to/system.img,format=raw,if=ide,index=0 \
    -device virtio-vga,xres=1080,yres=1920 \
    -vnc :0 \
    -serial file:/path/to/serial.log \
    -netdev user,id=net0,hostfwd=tcp::5555-:5555 \
    -device e1000,netdev=net0 \
    -usb -device usb-tablet \
    -device virtio-rng-pci
```

#### Profile Configuration Schema
```yaml
boot:
  kernel: "/path/to/kernel"
  initrd: "/path/to/initrd.img"
  system_image: "/path/to/system.img"
  kernel_cmdline: "root=/dev/ram0 androidboot.selinux=permissive"

performance:
  ram_mb: 4096
  cpu_cores: 4
  hypervisor: "kvm"

graphics:
  gpu_mode: "host"  # or "software"

device:
  screen_width: 1080
  screen_height: 1920

network:
  mode: "user"

adb:
  enabled: true
  port: 5555
```

### 9. Testing Checklist

- [ ] KVM available and accessible (`/dev/kvm`)
- [ ] Kernel and initrd files present and valid
- [ ] System image mountable and contains Android files
- [ ] VNC connection established
- [ ] Serial console logging working
- [ ] Network connectivity (ping, ADB)
- [ ] Touch/mouse input responsive
- [ ] Display resolution correct
- [ ] Audio working (if required)
- [ ] Performance acceptable (>30 FPS)

### 10. References

- [QEMU Documentation](https://www.qemu.org/docs/master/)
- [Android-x86 Project](https://www.android-x86.org/)
- [Android Emulator Architecture](https://source.android.com/docs/core/architecture)
- [KVM Documentation](https://www.linux-kvm.org/page/Documents)
- [Goldfish Platform](https://android.googlesource.com/platform/external/qemu/+/master/docs/GOLDFISH-VIRTUAL-HARDWARE.TXT)

---

## Agent Responsibilities

1. **Configuration Review** - Validate QEMU and Android configurations
2. **Boot Troubleshooting** - Diagnose and resolve boot failures
3. **Performance Analysis** - Identify and resolve performance bottlenecks
4. **Compatibility Testing** - Verify Android version compatibility
5. **Documentation** - Maintain expert knowledge base

## Contact

For QEMU/Android x86 issues, consult this document first, then escalate to:
- Agent 003 (Virtualization Architect) for architectural decisions
- Agent 004 (Linux Systems) for host system configuration
- Agent 009 (QA Lead) for test case development
