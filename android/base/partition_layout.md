# LinBlock Partition Layout

## Overview

LinBlock uses a simplified partition layout optimized for an emulated environment.
Each partition is backed by a separate qcow2 disk image, presented to the guest
as individual virtio-blk devices. This design allows copy-on-write snapshots,
easy resizing, and independent management of each partition.

## Partition Table

| Partition | Size | Filesystem | Mount Point | Mode | virtio Device | Description |
|-----------|------|-----------|-------------|------|---------------|-------------|
| boot | 64 MB | none (raw) | N/A | ro | (loaded directly) | Kernel + initramfs |
| recovery | 64 MB | none (raw) | N/A | ro | (loaded directly) | Recovery kernel + initramfs |
| system | 2 GB | ext4 | /system | ro | /dev/vda | Android system image |
| vendor | 256 MB | ext4 | /vendor | ro | /dev/vdb | Vendor-specific HALs and configs |
| data | 4 GB | ext4 | /data | rw | /dev/vdc | User data, app data, settings |
| cache | 256 MB | ext4 | /cache | rw | /dev/vdd | OTA cache, temporary files |
| metadata | 16 MB | ext4 | /metadata | rw | /dev/vde | Encryption metadata |
| misc | 4 MB | none (raw) | N/A | rw | /dev/vdf | Bootloader messaging |
| shared | varies | 9pfs | /mnt/shared | rw | virtio-9p | Host directory sharing |

**Total minimum disk space:** ~6.7 GB (excluding shared storage)

## Detailed Partition Descriptions

### boot (64 MB)

The boot partition contains the Linux kernel image and the initial RAM filesystem
(initramfs). In the LinBlock emulator, the kernel and initramfs are loaded
directly into guest memory by the emulator, so this partition serves primarily
as a storage location for the build artifacts.

**Contents:**
- `kernel` - Linux kernel (bzImage format, ~10-15 MB)
- `initramfs.img` - Initial RAM filesystem (~20-30 MB)

**Boot process:**
The emulator loads the kernel and initramfs directly into guest physical memory
at well-known addresses, sets the kernel command line, and begins execution.
This is analogous to QEMU's `-kernel` and `-initrd` options.

### recovery (64 MB)

The recovery partition contains an alternative boot image used for system
recovery, factory reset, and OTA updates. In LinBlock, recovery is implemented
minimally.

**Contents:**
- Recovery kernel
- Recovery initramfs with minimal shell and wipe utilities

### system (2 GB, ext4, read-only)

The system partition contains the core Android operating system. It is mounted
read-only to ensure system integrity and to enable overlay-based modifications.

**Contents:**
- `/system/framework/` - Android framework JARs
- `/system/app/` - Pre-installed system apps
- `/system/priv-app/` - Privileged system apps
- `/system/lib64/` - Shared libraries (64-bit)
- `/system/lib/` - Shared libraries (32-bit)
- `/system/bin/` - System binaries
- `/system/etc/` - Configuration files
- `/system/fonts/` - System fonts

**qcow2 image:** `system.qcow2` (base image, ~1.5 GB actual)

**Overlay support:** An overlay qcow2 can be stacked on top of the base system
image to apply modifications without altering the original:
```
system_overlay.qcow2 -> system.qcow2 (base, read-only)
```

### vendor (256 MB, ext4, read-only)

The vendor partition contains hardware-specific HAL implementations and
configurations specific to the LinBlock virtual device.

**Contents:**
- `/vendor/lib64/hw/` - HAL shared libraries (gralloc, hwcomposer, audio, etc.)
- `/vendor/etc/` - Vendor configuration files
- `/vendor/etc/init/` - Vendor init scripts
- `/vendor/etc/vintf/` - VINTF manifests
- `/vendor/firmware/` - Firmware files (empty for emulator)
- `/vendor/overlay/` - Resource overlays

**qcow2 image:** `vendor.qcow2` (~150 MB actual)

### data (4 GB, ext4, read-write)

The data partition stores all user data, installed applications, app data,
and user settings. This is the primary read-write partition.

**Contents:**
- `/data/app/` - Installed applications (APKs)
- `/data/data/` - App-private data directories
- `/data/user/` - User profiles
- `/data/system/` - System databases (packages, settings)
- `/data/misc/` - Miscellaneous system data
- `/data/media/` - Internal shared storage (photos, downloads, etc.)
- `/data/local/tmp/` - Temporary files (ADB push target)

**qcow2 image:** `userdata.qcow2` (starts small, grows up to 4 GB)

**Encryption:** File-based encryption (FBE) is supported but optional in the
emulator. Default configuration leaves data unencrypted for easier debugging.
Production builds should enable FBE.

**Wiping:** Factory reset wipes this partition by creating a new empty qcow2,
preserving the system and vendor images.

### cache (256 MB, ext4, read-write)

The cache partition provides temporary storage for system operations.

**Contents:**
- OTA update packages (not used in emulator)
- Temporary system files
- Recovery logs

**qcow2 image:** `cache.qcow2` (~10 MB actual initially)

### metadata (16 MB, ext4, read-write)

The metadata partition stores encryption metadata and other system metadata
that must persist across wipes.

**Contents:**
- Encryption keys and state
- Checkpoint metadata
- Virtual A/B metadata (if used)

**qcow2 image:** `metadata.qcow2`

### misc (4 MB, raw, read-write)

The misc partition is used for bootloader-to-recovery communication,
such as signaling a factory reset or entering recovery mode.

**Contents:**
- Boot control block (BCB)
- Bootloader messages

**qcow2 image:** `misc.qcow2`

### shared (host directory, 9pfs, read-write)

The shared partition provides a bridge between the host filesystem and the
Android guest, allowing file exchange without ADB.

**Host side:** A configurable host directory (default: `~/.config/linblock/shared/`)
**Guest side:** Mounted at `/mnt/shared` via virtio-9p (Plan 9 filesystem)

**9p configuration:**
```
virtio-9p device:
  tag: linblock_shared
  path: /home/user/.config/linblock/shared
  security_model: mapped-xattr
```

**Guest fstab entry:**
```
linblock_shared  /mnt/shared  9p  trans=virtio,version=9p2000.L  0  0
```

## Disk Image Management

### Creating Images

```bash
# Create system image (from AOSP build output)
qemu-img create -f qcow2 system.qcow2 2G
# Populate from build: dd or qemu-img convert from raw

# Create vendor image
qemu-img create -f qcow2 vendor.qcow2 256M

# Create empty data image
qemu-img create -f qcow2 userdata.qcow2 4G

# Create cache image
qemu-img create -f qcow2 cache.qcow2 256M

# Create metadata image
qemu-img create -f qcow2 metadata.qcow2 16M

# Create misc image
qemu-img create -f qcow2 misc.qcow2 4M
```

### Creating Overlays (Copy-on-Write)

```bash
# Create overlay on top of system image (preserves base)
qemu-img create -f qcow2 -b system.qcow2 -F qcow2 system_overlay.qcow2

# Create snapshot of data partition
qemu-img create -f qcow2 -b userdata.qcow2 -F qcow2 userdata_snapshot.qcow2
```

### Image Information

```bash
# Check image details
qemu-img info system.qcow2

# Output:
# image: system.qcow2
# file format: qcow2
# virtual size: 2 GiB (2147483648 bytes)
# disk size: 1.5 GiB
# cluster_size: 65536
```

## Filesystem Formatting

### Initial Formatting (Build Time)

```bash
# Format system partition
mkfs.ext4 -L system -b 4096 system.raw 2G
# Populate with AOSP build output, then convert:
qemu-img convert -f raw -O qcow2 system.raw system.qcow2

# Format vendor partition
mkfs.ext4 -L vendor -b 4096 vendor.raw 256M

# Format data partition (empty)
mkfs.ext4 -L data -b 4096 -E lazy_itable_init=1 userdata.raw 4G

# Format cache partition
mkfs.ext4 -L cache -b 4096 cache.raw 256M
```

### Filesystem Mount Options

| Partition | Mount Options |
|-----------|--------------|
| system | `ro,noatime,errors=panic` |
| vendor | `ro,noatime,errors=panic` |
| data | `rw,noatime,nosuid,nodev,errors=continue` |
| cache | `rw,noatime,nosuid,nodev,errors=continue` |
| metadata | `rw,noatime,nosuid,nodev,errors=panic` |

## Guest fstab

File: `/vendor/etc/fstab.linblock`

```
# <device>      <mount>     <type>  <options>                          <fs_mgr_flags>
/dev/vda        /system     ext4    ro,noatime                         wait
/dev/vdb        /vendor     ext4    ro,noatime                         wait
/dev/vdc        /data       ext4    rw,noatime,nosuid,nodev            wait,check,formattable
/dev/vdd        /cache      ext4    rw,noatime,nosuid,nodev            wait,check
/dev/vde        /metadata   ext4    rw,noatime,nosuid,nodev            wait,check,formattable
linblock_shared /mnt/shared 9p      trans=virtio,version=9p2000.L      wait,nofail
```

## Storage Size Recommendations

### By Use Case

| Use Case | system | vendor | data | Total |
|----------|--------|--------|------|-------|
| Minimal (testing) | 2 GB | 256 MB | 2 GB | ~4.5 GB |
| Standard (development) | 2 GB | 256 MB | 4 GB | ~6.5 GB |
| Extended (heavy use) | 2 GB | 256 MB | 8 GB | ~10.5 GB |
| Full (power user) | 2 GB | 256 MB | 16 GB | ~18.5 GB |

### Growing the Data Partition

```bash
# Resize qcow2 image (offline)
qemu-img resize userdata.qcow2 +4G

# Inside guest, resize filesystem
resize2fs /dev/vdc
```

## Backup and Restore

### Full Backup

```bash
# Stop emulator first, then copy all images
mkdir -p backup/$(date +%Y%m%d)
cp *.qcow2 backup/$(date +%Y%m%d)/
```

### Data-Only Backup

```bash
# Backup just user data
cp userdata.qcow2 backup/userdata_$(date +%Y%m%d).qcow2
```

### Restore from Backup

```bash
# Restore data partition
cp backup/userdata_20260115.qcow2 userdata.qcow2
```

### Factory Reset

```bash
# Create fresh data partition (wipes all user data)
qemu-img create -f qcow2 userdata.qcow2 4G
# Guest will format on first boot
```
