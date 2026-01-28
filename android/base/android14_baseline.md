# Android 14 Baseline Configuration

## Target Platform

| Property | Value |
|----------|-------|
| Android Version | 14 (Upside Down Cake) |
| API Level | 34 |
| Build ID | UP1A (template, date-stamped at build time) |
| Architecture | x86_64 (primary), x86 (secondary) |
| Build Type | userdebug (development), user (release) |
| Security Patch Level | Set at build time |

## Build Fingerprint

The build fingerprint uniquely identifies LinBlock builds and follows Android's
standard format:

```
linblock/linblock_x86_64/x86_64:14/UP1A.YYMMDD.NNN/eng.linblock:userdebug/test-keys
```

**Breakdown:**

| Segment | Value | Description |
|---------|-------|-------------|
| Brand | linblock | Product brand |
| Product | linblock_x86_64 | Product name |
| Device | x86_64 | Device name |
| Platform Version | 14 | Android version |
| Build ID | UP1A.YYMMDD.NNN | Date-stamped build ID |
| Build Type | eng.linblock | Build variant |
| Tags | userdebug/test-keys | Build tags |

Example concrete fingerprint:
```
linblock/linblock_x86_64/x86_64:14/UP1A.260115.001/eng.linblock:userdebug/test-keys
```

## System Property Overrides

### Device Identity

```properties
# Hardware identification
ro.hardware=linblock
ro.hardware.chipname=linblock_virtual
ro.board.platform=linblock

# Product information
ro.product.brand=LinBlock
ro.product.device=x86_64
ro.product.manufacturer=LinBlock
ro.product.model=LinBlock Emulator
ro.product.name=linblock_x86_64

# Build information
ro.build.display.id=LinBlock-14-$(BUILD_ID)
ro.build.product=linblock_x86_64
ro.build.description=linblock_x86_64-userdebug 14 UP1A eng.linblock test-keys
ro.build.type=userdebug
ro.build.tags=test-keys
```

### Emulator-Specific Properties

```properties
# Identify as emulator
ro.emulator=true
ro.kernel.qemu=1
ro.kernel.qemu.gles=1

# ADB configuration
ro.adb.secure=0
ro.debuggable=1
persist.sys.usb.config=adb
service.adb.root=1

# Display
ro.sf.lcd_density=420
ro.surface_flinger.max_frame_buffer_acquired_buffers=3

# Network
ro.radio.noril=yes

# Performance
dalvik.vm.heapsize=512m
dalvik.vm.heapgrowthlimit=256m
dalvik.vm.heapmaxfree=8m
dalvik.vm.heapminfree=512k
dalvik.vm.heaptargetutilization=0.75
```

### Security Properties

```properties
# SELinux (enforcing for security, permissive for development)
ro.build.selinux=1

# Verified boot (disabled for emulator)
ro.boot.verifiedbootstate=orange
ro.boot.flash.locked=0

# Encryption
ro.crypto.state=unencrypted
```

## HAL (Hardware Abstraction Layer) Requirements

LinBlock requires the following HAL implementations, either as stubs or
functional implementations:

### Graphics HAL

| Component | Implementation | Notes |
|-----------|---------------|-------|
| EGL / GLES | SwiftShader (software) or Mesa/virgl | Primary rendering path |
| Gralloc | gralloc.linblock | Buffer allocation for display |
| HWComposer | hwcomposer.linblock | Minimal; pass-through to SurfaceFlinger |
| Vulkan | SwiftShader Vulkan (optional) | For apps requiring Vulkan |

**Graphics pipeline:**
```
App (OpenGL ES) -> SurfaceFlinger -> HWComposer -> virtio-gpu -> Host Display
                                        |
                    SwiftShader (CPU) or Mesa/virgl (GPU passthrough)
```

### Audio HAL

| Component | Implementation | Notes |
|-----------|---------------|-------|
| Audio HAL | audio.linblock | Null sink (silent) by default |
| Audio Policy | audio_policy_configuration.xml | Minimal output config |
| AAudio | Stub | Low-latency audio (optional) |

The audio HAL provides a null (silent) sink to satisfy Android's audio requirements.
Audio output can be routed to the host's PulseAudio/ALSA in a future version.

### Sensor HAL

| Sensor | Implementation | Notes |
|--------|---------------|-------|
| Accelerometer | Software stub | Returns static (0, 0, -9.81) |
| Gyroscope | Software stub | Returns static (0, 0, 0) |
| Magnetometer | Software stub | Returns static north |
| Light | Software stub | Returns constant ambient |
| Proximity | Software stub | Returns "far" |

All sensors return plausible static values. Future versions may allow dynamic
input from the host GUI (e.g., virtual accelerometer controlled by mouse drag).

### Camera HAL

| Component | Implementation | Notes |
|-----------|---------------|-------|
| Camera2 HAL | Virtual camera | Returns test pattern or host webcam feed |
| Camera Provider | camera.linblock | Exposes 1 front camera |

Initially provides a test pattern (color bars). Future: passthrough from host
webcam via V4L2.

### Other HALs

| HAL | Status | Notes |
|-----|--------|-------|
| Bluetooth | Stub | Returns "not available" |
| Telephony / RIL | Stub (no RIL) | Returns "no SIM" |
| WiFi | Stub or virtio-net | Connects via virtio-net |
| GPS / Location | Stub | Returns fixed coordinates (configurable) |
| Fingerprint | Not included | Not needed for emulator |
| NFC | Not included | Not needed for emulator |
| USB | Minimal | ADB over USB emulation |
| Power | Stub | Always reports "AC charging, 100%" |
| Thermal | Stub | Always reports normal temperature |

## Kernel Configuration

The guest Linux kernel must include the following configuration options for
proper operation inside the LinBlock emulator:

### Virtio Drivers (Required)

```
CONFIG_VIRTIO=y
CONFIG_VIRTIO_PCI=y
CONFIG_VIRTIO_PCI_MODERN=y
CONFIG_VIRTIO_NET=y
CONFIG_VIRTIO_BLK=y
CONFIG_VIRTIO_GPU=y
CONFIG_VIRTIO_CONSOLE=y
CONFIG_VIRTIO_INPUT=y
CONFIG_VIRTIO_BALLOON=y
CONFIG_VIRTIO_MMIO=y
```

### KVM Guest Support

```
CONFIG_KVM_GUEST=y
CONFIG_PARAVIRT=y
CONFIG_PARAVIRT_CLOCK=y
CONFIG_HYPERVISOR_GUEST=y
```

### Filesystem and Storage

```
CONFIG_EXT4_FS=y
CONFIG_EXT4_FS_POSIX_ACL=y
CONFIG_F2FS_FS=y
CONFIG_FUSE_FS=y
CONFIG_OVERLAY_FS=y
CONFIG_TMPFS=y
CONFIG_9P_FS=y
CONFIG_9P_FS_POSIX_ACL=y
CONFIG_NET_9P=y
CONFIG_NET_9P_VIRTIO=y
```

### Android-Specific

```
CONFIG_ANDROID=y
CONFIG_ANDROID_BINDER_IPC=y
CONFIG_ANDROID_BINDER_DEVICES="binder,hwbinder,vndbinder"
CONFIG_ASHMEM=y
CONFIG_STAGING=y
CONFIG_ION=y
```

### Networking

```
CONFIG_NET=y
CONFIG_INET=y
CONFIG_PACKET=y
CONFIG_UNIX=y
CONFIG_NETFILTER=y
CONFIG_IP_NF_IPTABLES=y
CONFIG_IP_NF_FILTER=y
CONFIG_IP_NF_NAT=y
```

### Debug (userdebug builds)

```
CONFIG_PRINTK=y
CONFIG_SERIAL_8250=y
CONFIG_SERIAL_8250_CONSOLE=y
CONFIG_EARLY_PRINTK=y
CONFIG_DEBUG_INFO=y
CONFIG_KGDB=y
```

## Boot Configuration

### Kernel Command Line

```
androidboot.hardware=linblock
androidboot.serialno=LINBLOCK0001
console=ttyS0,115200
androidboot.console=ttyS0
androidboot.selinux=enforcing
androidboot.boot_devices=pci0000:00
loop.max_part=7
printk.devkmsg=on
```

### Init Configuration

LinBlock uses Android's standard init process with the following property
triggers:

```
# init.linblock.rc
on early-init
    write /proc/sys/kernel/printk "7"

on init
    # Set up virtio block devices
    symlink /dev/vda /dev/block/system
    symlink /dev/vdb /dev/block/vendor
    symlink /dev/vdc /dev/block/userdata
    symlink /dev/vdd /dev/block/cache

on boot
    # GPU permissions
    chmod 0666 /dev/dri/renderD128
    chmod 0666 /dev/dri/card0

    # Enable ADB
    setprop sys.usb.configfs 0
    setprop sys.usb.config adb
```

## Build Variants

| Variant | Purpose | ADB | SELinux | Debug |
|---------|---------|-----|---------|-------|
| eng | Development | Root | Permissive | Full |
| userdebug | Testing | Root | Enforcing | Partial |
| user | Release | Non-root | Enforcing | Minimal |

The default build variant for development is `userdebug`, which provides
root ADB access with enforcing SELinux for realistic security testing.
