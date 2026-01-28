# LinBlock Memory Management

## Overview

This document describes the memory management architecture for the LinBlock emulator,
covering guest memory allocation, shared framebuffer design, host memory budgeting,
hugepage optimization, and OOM protection strategies. The design targets a host system
with 12 GB of RAM running an x86_64 guest with up to 4 GB of allocated memory.

## Guest Memory Allocation

### Allocation Method

Guest physical memory is allocated using `mmap` with anonymous private mappings:

```c
void *guest_ram = mmap(
    NULL,                           // Let kernel choose address
    guest_ram_size,                 // Up to 4 GB (4294967296 bytes)
    PROT_READ | PROT_WRITE,        // Read/write access
    MAP_ANONYMOUS | MAP_PRIVATE,   // Anonymous, private mapping
    -1,                            // No file descriptor
    0                              // No offset
);
```

**Rationale for MAP_ANONYMOUS | MAP_PRIVATE:**
- `MAP_ANONYMOUS`: No backing file needed; memory is zero-initialized
- `MAP_PRIVATE`: Copy-on-write semantics ensure isolation
- Linux will lazily allocate physical pages on first access (demand paging)
- Allows overcommit: not all 4 GB needs to be physically resident immediately

### Guest Physical Address Map

```
Guest Physical Memory Layout (4 GB):
+------------------+ 0x0000_0000
| Real Mode IVT    | (1 KB)
+------------------+ 0x0000_0400
| BDA              | (256 bytes)
+------------------+ 0x0000_7C00
| Bootloader       | (512 bytes)
+------------------+ 0x0010_0000  (1 MB)
| Kernel + Initram | (~32 MB)
+------------------+ 0x0200_0000  (32 MB)
| Guest RAM        | (main memory)
+------------------+ 0xC000_0000  (3 GB)
| MMIO Region      | (device MMIO space)
+------------------+ 0xFEC0_0000
| IOAPIC           | (4 KB)
+------------------+ 0xFEE0_0000
| Local APIC       | (4 KB)
+------------------+ 0xFFFF_FFFF  (4 GB)
```

### KVM Memory Region Setup

Guest memory is registered with KVM using the `KVM_SET_USER_MEMORY_REGION` ioctl:

```c
struct kvm_userspace_memory_region region = {
    .slot = 0,                          // Memory slot index
    .flags = 0,                         // No special flags (or KVM_MEM_LOG_DIRTY_PAGES for migration)
    .guest_phys_addr = 0,               // Guest physical address start
    .memory_size = guest_ram_size,       // Size in bytes
    .userspace_addr = (uint64_t)guest_ram  // Host virtual address from mmap
};

ioctl(vm_fd, KVM_SET_USER_MEMORY_REGION, &region);
```

For the split below/above 3GB (to accommodate the MMIO hole):

```c
// Region 0: 0 to 3 GB (below MMIO hole)
struct kvm_userspace_memory_region low_region = {
    .slot = 0,
    .guest_phys_addr = 0,
    .memory_size = 0xC0000000,          // 3 GB
    .userspace_addr = (uint64_t)guest_ram
};

// Region 1: 4 GB to 4 GB + remainder (above MMIO hole)
struct kvm_userspace_memory_region high_region = {
    .slot = 1,
    .guest_phys_addr = 0x100000000ULL,  // 4 GB
    .memory_size = guest_ram_size - 0xC0000000,  // Remainder
    .userspace_addr = (uint64_t)(guest_ram + 0xC0000000)
};
```

## Shared Framebuffer

### Design

The framebuffer is a shared memory region accessible by both the emulator core
(which writes pixel data from the virtio-gpu device) and the GTK display widget
(which reads pixel data for rendering).

### Implementation

```c
// Create a memfd for the shared framebuffer
int fb_fd = memfd_create("linblock_framebuffer", MFD_CLOEXEC);
ftruncate(fb_fd, framebuffer_total_size);

// Map in emulator process
void *fb_emulator = mmap(
    NULL,
    framebuffer_total_size,
    PROT_READ | PROT_WRITE,
    MAP_SHARED,
    fb_fd,
    0
);

// Map in GTK process (or same process, different thread)
void *fb_display = mmap(
    NULL,
    framebuffer_total_size,
    PROT_READ,               // Display only reads
    MAP_SHARED,
    fb_fd,
    0
);
```

### Framebuffer Layout

```
Shared Memory Region (~16 MB):
+------------------+ offset 0
| Metadata Header  | (4 KB)
|  - magic number  |
|  - width/height  |
|  - format        |
|  - front_index   |
|  - frame_counter |
|  - futex word    |
+------------------+ offset 4096
| Buffer 0 (front) | (8,294,400 bytes = 1080 * 1920 * 4)
+------------------+ offset 8,298,496
| Buffer 1 (back)  | (8,294,400 bytes)
+------------------+ offset 16,592,896
```

### Double Buffering Protocol

1. Emulator renders frame into the back buffer (index = 1 - front_index)
2. Emulator atomically writes `front_index = 1 - front_index`
3. Emulator increments `frame_counter`
4. Emulator calls `futex(FUTEX_WAKE)` on the futex word
5. Display thread wakes from `futex(FUTEX_WAIT)`, reads front buffer
6. Display thread copies data to GdkPixbuf and triggers GTK repaint

### Bandwidth Analysis

| Resolution | Format | Bytes/Frame | FPS | Bandwidth |
|-----------|--------|-------------|-----|-----------|
| 1080x1920 | RGBA8888 | 8,294,400 | 30 | 237 MB/s |
| 720x1280 | RGBA8888 | 3,686,400 | 30 | 105 MB/s |
| 1080x1920 | RGBA8888 | 8,294,400 | 60 | 474 MB/s |

The default target of 1080x1920 @ 30 FPS produces 237 MB/s of memory bandwidth,
which is well within the capability of modern DDR4/DDR5 systems.

## Host Memory Budget (12 GB System)

### Allocation Plan

| Component | Memory | Notes |
|-----------|--------|-------|
| Guest RAM | 4,096 MB | mmap'd, demand-paged |
| Emulator overhead | 512 MB | Code, data structures, device state |
| Shared framebuffer | 16 MB | Double-buffered display |
| GTK GUI process | 256 MB | Widgets, rendering surfaces |
| QCOW2 cache | 256 MB | Block device read cache |
| Host OS + services | 2,048 MB | Kernel, systemd, desktop environment |
| **Total reserved** | **7,184 MB** | |
| **Available headroom** | **~4,816 MB** | For OS page cache, other apps |

### Memory Configuration by Host RAM

| Host RAM | Guest RAM | Recommended Config |
|----------|-----------|-------------------|
| 8 GB | 2 GB | Minimal; close other apps |
| 12 GB | 4 GB | Standard; comfortable |
| 16 GB | 4-6 GB | Generous headroom |
| 32 GB+ | 4-8 GB | Full headroom for development |

## Hugepages Configuration

### Why Hugepages

Standard 4 KB pages require 1,048,576 page table entries for 4 GB of guest RAM.
This causes significant TLB (Translation Lookaside Buffer) pressure. Hugepages
(2 MB) reduce this to 2,048 entries, dramatically improving TLB hit rates.

### Setup

**Allocate hugepages at boot (recommended):**

Add to `/etc/default/grub`:
```
GRUB_CMDLINE_LINUX="hugepages=2048"
```

Then run:
```bash
sudo update-grub
sudo reboot
```

**Allocate hugepages at runtime:**
```bash
# Allocate 2048 x 2MB hugepages = 4 GB
echo 2048 | sudo tee /proc/sys/vm/nr_hugepages

# Verify allocation
cat /proc/meminfo | grep HugePages
```

**Persistent configuration via sysctl:**
```bash
echo "vm.nr_hugepages = 2048" | sudo tee /etc/sysctl.d/99-linblock-hugepages.conf
sudo sysctl -p /etc/sysctl.d/99-linblock-hugepages.conf
```

### Using Hugepages in the Emulator

```c
// Mount hugetlbfs (or use system-provided mount)
// Typically at /dev/hugepages or /run/hugepages

void *guest_ram = mmap(
    NULL,
    guest_ram_size,
    PROT_READ | PROT_WRITE,
    MAP_ANONYMOUS | MAP_PRIVATE | MAP_HUGETLB,
    -1,
    0
);

if (guest_ram == MAP_FAILED) {
    // Fallback to regular pages
    guest_ram = mmap(
        NULL,
        guest_ram_size,
        PROT_READ | PROT_WRITE,
        MAP_ANONYMOUS | MAP_PRIVATE,
        -1,
        0
    );
}
```

### Performance Impact

| Metric | 4 KB Pages | 2 MB Hugepages | Improvement |
|--------|-----------|----------------|-------------|
| TLB entries needed | 1,048,576 | 2,048 | 512x fewer |
| Page table memory | ~8 MB | ~16 KB | 500x smaller |
| TLB miss rate | Higher | Significantly lower | Variable |
| Guest boot time | Baseline | 5-15% faster | Measurable |

## Transparent Hugepages (THP)

### Recommendation: madvise Mode

Transparent Hugepages can be set to three modes:
- `always`: Kernel aggressively uses THP (can cause latency spikes from compaction)
- `madvise`: Only use THP for memory regions marked with `madvise(MADV_HUGEPAGE)` (recommended)
- `never`: THP disabled

```bash
# Set madvise mode
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# Persistent via sysctl/kernel cmdline
# Add to /etc/default/grub: transparent_hugepage=madvise
```

In the emulator code, mark guest RAM for THP:
```c
madvise(guest_ram, guest_ram_size, MADV_HUGEPAGE);
```

This gives the kernel permission to use transparent hugepages for guest RAM
without affecting other processes or causing unexpected compaction latency.

## Memory Ballooning (Future)

Memory ballooning allows dynamic adjustment of guest memory at runtime. A balloon
driver inside the guest inflates (reclaims pages) or deflates (releases pages)
on command from the host.

### Planned Implementation
- virtio-balloon device in the emulator
- Guest kernel driver communicates with host
- Host can request guest to return unused pages
- Useful for running multiple VMs or reclaiming memory when guest is idle

### Interface (Future)
```python
class MemoryBalloonInterface(Protocol):
    def inflate(self, pages: int) -> bool: ...
    def deflate(self, pages: int) -> bool: ...
    def get_guest_free_memory(self) -> int: ...
    def set_target_memory(self, target_mb: int) -> bool: ...
```

## OOM Protection

### oom_score_adj Configuration

The Linux OOM killer uses `/proc/<pid>/oom_score_adj` to prioritize which processes
to kill under memory pressure. LinBlock sets this value to protect the emulator:

```bash
# Set during emulator startup
echo -500 > /proc/$$/oom_score_adj
```

**Score values:**
- `-1000`: Never kill (requires root; not recommended for LinBlock)
- `-500`: Strongly prefer not to kill (LinBlock emulator)
- `0`: Default for normal processes
- `+1000`: Kill first

### Implementation in Python

```python
import os

def set_oom_protection():
    """Reduce likelihood of OOM killer targeting the emulator process."""
    try:
        pid = os.getpid()
        with open(f'/proc/{pid}/oom_score_adj', 'w') as f:
            f.write('-500')
    except PermissionError:
        # Non-root users may not be able to set negative values
        # This is acceptable; log a warning
        pass
    except OSError:
        pass
```

### Memory Pressure Monitoring

The emulator monitors host memory pressure and can proactively respond:

```python
def check_memory_pressure() -> str:
    """Check current memory pressure level."""
    with open('/proc/meminfo', 'r') as f:
        meminfo = {}
        for line in f:
            parts = line.split()
            meminfo[parts[0].rstrip(':')] = int(parts[1])

    available_mb = meminfo.get('MemAvailable', 0) // 1024

    if available_mb < 512:
        return 'critical'   # Should pause guest
    elif available_mb < 1024:
        return 'warning'    # Alert user
    else:
        return 'normal'
```

**Response actions:**
| Pressure Level | Available RAM | Action |
|---------------|---------------|--------|
| normal | > 1 GB | No action |
| warning | 512 MB - 1 GB | Display warning to user |
| critical | < 512 MB | Auto-pause guest, prompt user |

## cgroup Memory Limits

For advanced deployments, LinBlock can be run inside a cgroup to enforce hard
memory limits:

```bash
# Create cgroup (cgroup v2)
sudo mkdir -p /sys/fs/cgroup/linblock
echo "8G" | sudo tee /sys/fs/cgroup/linblock/memory.max
echo "7G" | sudo tee /sys/fs/cgroup/linblock/memory.high

# Move emulator process into cgroup
echo $PID | sudo tee /sys/fs/cgroup/linblock/cgroup.procs
```

**Recommended limits:**

| Host RAM | memory.max | memory.high | Guest RAM |
|----------|-----------|-------------|-----------|
| 8 GB | 5 GB | 4.5 GB | 2 GB |
| 12 GB | 8 GB | 7 GB | 4 GB |
| 16 GB | 10 GB | 9 GB | 4-6 GB |

## Swap Configuration

### Recommendations

- **vm.swappiness = 10:** Prefer keeping application pages in RAM; only swap under heavy pressure
- **Swap size:** At least 4 GB swap partition or file
- **zswap:** Enable for compressed swap cache (reduces I/O)

```bash
# Set swappiness
echo 10 | sudo tee /proc/sys/vm/swappiness

# Persistent
echo "vm.swappiness = 10" | sudo tee /etc/sysctl.d/99-linblock-swap.conf

# Enable zswap
echo 1 | sudo tee /sys/module/zswap/parameters/enabled
echo lz4 | sudo tee /sys/module/zswap/parameters/compressor
```

### MLOCK for Guest Memory

To prevent guest RAM from being swapped (which would cause severe performance
degradation), the emulator can lock guest memory:

```c
mlock(guest_ram, guest_ram_size);
```

Note: This requires `RLIMIT_MEMLOCK` to be set high enough, or `CAP_IPC_LOCK`
capability. The emulator should attempt mlock but gracefully degrade if it fails.

## Summary of Memory-Related Kernel Parameters

| Parameter | Recommended Value | Purpose |
|-----------|------------------|---------|
| `vm.swappiness` | 10 | Minimize swapping |
| `vm.nr_hugepages` | 2048 | Pre-allocate 4 GB hugepages |
| `transparent_hugepage` | madvise | THP on request only |
| `vm.overcommit_memory` | 0 (default) | Heuristic overcommit |
| `vm.dirty_ratio` | 20 (default) | Writeback threshold |
| `vm.dirty_background_ratio` | 10 (default) | Background writeback |
