# LinBlock Memory Tuning Guide

## Overview

This guide provides detailed instructions for tuning the host system's memory
configuration to achieve optimal performance when running the LinBlock Android
emulator. The recommendations target a system with 12 GB of RAM, but guidance
is provided for other configurations as well.

## Recommended Host Configuration (12 GB RAM)

### Memory Budget

| Component | Allocation | Notes |
|-----------|-----------|-------|
| Guest RAM | 4,096 MB | Android 14 guest |
| Emulator process | 512 MB | Emulator overhead |
| Shared framebuffer | 16 MB | Double-buffered display |
| GTK GUI | 256 MB | UI rendering |
| Host OS + desktop | 2,048 MB | Kernel, systemd, DE |
| Disk cache / headroom | ~5,072 MB | Available for page cache |
| **Total** | **12,000 MB** | |

### Quick Setup Commands

```bash
# Apply all recommended settings (run as root)
sudo sysctl -w vm.swappiness=10
sudo sysctl -w vm.nr_hugepages=2048
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# Make persistent
cat <<EOF | sudo tee /etc/sysctl.d/99-linblock.conf
vm.swappiness = 10
vm.nr_hugepages = 2048
EOF
sudo sysctl -p /etc/sysctl.d/99-linblock.conf
```

## vm.swappiness

### What It Does

The `vm.swappiness` parameter controls the kernel's tendency to swap out application
memory pages versus dropping file system page cache. Values range from 0 to 200
(0 to 100 on older kernels).

- **0:** Strongly avoid swapping; only swap to prevent OOM
- **10:** Swap only when necessary (recommended for LinBlock)
- **60:** Default value; balanced between swap and page cache
- **100:** Aggressively swap out application pages

### Recommendation: vm.swappiness = 10

LinBlock's guest RAM must remain in physical memory for acceptable performance.
Swapping guest pages to disk would cause catastrophic slowdowns. Setting swappiness
to 10 tells the kernel to strongly prefer keeping application pages (including
the mmap'd guest RAM) in physical memory.

```bash
# Set immediately
sudo sysctl -w vm.swappiness=10

# Verify
cat /proc/sys/vm/swappiness
# Expected output: 10

# Make persistent across reboots
echo "vm.swappiness = 10" | sudo tee -a /etc/sysctl.d/99-linblock.conf
```

## Hugepages Setup

### Why Hugepages Matter

Standard Linux uses 4 KB memory pages. For 4 GB of guest RAM, this means
1,048,576 page table entries. Each TLB (Translation Lookaside Buffer) miss
requires a page table walk, which is expensive.

Using 2 MB hugepages reduces the page count to 2,048, dramatically improving
TLB hit rates and reducing page table walk overhead.

### Performance Impact

| Metric | 4 KB Pages | 2 MB Hugepages |
|--------|-----------|----------------|
| Pages for 4 GB | 1,048,576 | 2,048 |
| Page table memory | ~8 MB | ~16 KB |
| TLB coverage (typical) | ~8 MB | ~4 GB |
| Guest boot time | Baseline | 5-15% faster |
| Memory-intensive workloads | Baseline | 10-30% faster |

### Allocating Hugepages

**For 4 GB guest RAM (2048 x 2 MB hugepages):**

```bash
# Allocate at runtime
echo 2048 | sudo tee /proc/sys/vm/nr_hugepages

# Verify allocation
grep HugePages /proc/meminfo
# HugePages_Total:    2048
# HugePages_Free:     2048
# HugePages_Rsvd:        0
# HugePages_Surp:        0
# Hugepagesize:       2048 kB
```

**Make persistent via sysctl:**
```bash
echo "vm.nr_hugepages = 2048" | sudo tee -a /etc/sysctl.d/99-linblock.conf
sudo sysctl -p /etc/sysctl.d/99-linblock.conf
```

**Make persistent via kernel command line (most reliable):**
```bash
# Edit GRUB configuration
sudo vi /etc/default/grub
# Add to GRUB_CMDLINE_LINUX:
#   hugepages=2048

# Update GRUB and reboot
sudo update-grub
sudo reboot
```

### Hugepage Allocation by Host RAM

| Host RAM | Guest RAM | Hugepages | Allocation Command |
|----------|-----------|-----------|-------------------|
| 8 GB | 2 GB | 1024 | `echo 1024 > /proc/sys/vm/nr_hugepages` |
| 12 GB | 4 GB | 2048 | `echo 2048 > /proc/sys/vm/nr_hugepages` |
| 16 GB | 4 GB | 2048 | `echo 2048 > /proc/sys/vm/nr_hugepages` |
| 16 GB | 6 GB | 3072 | `echo 3072 > /proc/sys/vm/nr_hugepages` |
| 32 GB | 8 GB | 4096 | `echo 4096 > /proc/sys/vm/nr_hugepages` |

### Troubleshooting Hugepage Allocation

If the system cannot allocate the requested number of hugepages:

```bash
# Check how many were actually allocated
cat /proc/sys/vm/nr_hugepages

# Check system memory fragmentation
cat /proc/buddyinfo

# Compact memory to create contiguous regions
echo 1 | sudo tee /proc/sys/vm/compact_memory

# Retry allocation
echo 2048 | sudo tee /proc/sys/vm/nr_hugepages
```

If allocation still fails, allocate at boot time (via kernel command line) when
memory is not yet fragmented.

## Transparent Hugepages (THP)

### Modes

| Mode | Behavior |
|------|----------|
| `always` | Kernel aggressively promotes all allocations to THP |
| `madvise` | Only use THP for regions marked with `madvise(MADV_HUGEPAGE)` |
| `never` | THP completely disabled |

### Recommendation: madvise

The `madvise` mode is recommended because:
- LinBlock explicitly requests THP for guest RAM via `madvise(MADV_HUGEPAGE)`
- Other processes are not affected by THP compaction overhead
- No unexpected latency spikes from background compaction
- Predictable memory behavior

```bash
# Set madvise mode
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/enabled

# Verify
cat /sys/kernel/mm/transparent_hugepage/enabled
# Expected: always [madvise] never

# Make persistent via kernel command line
# Add to GRUB_CMDLINE_LINUX: transparent_hugepage=madvise
```

### THP Defrag Settings

When THP is in `madvise` mode, the defrag behavior controls what happens when
a hugepage cannot be allocated immediately:

```bash
# Set defrag to madvise as well (only defrag on explicit request)
echo madvise | sudo tee /sys/kernel/mm/transparent_hugepage/defrag

# Alternatively, defer defragmentation to a background thread
echo defer+madvise | sudo tee /sys/kernel/mm/transparent_hugepage/defrag
```

## OOM Killer Configuration

### Process Protection

The Linux OOM (Out of Memory) killer terminates processes when the system
runs out of memory. The `oom_score_adj` value controls kill priority:

| Value | Meaning |
|-------|---------|
| -1000 | Never kill (requires root) |
| -500 | Strongly protected (LinBlock emulator) |
| 0 | Default priority |
| +1000 | Kill first |

### Setting oom_score_adj for the Emulator

LinBlock automatically sets `oom_score_adj` to -500 when it starts. To
configure this manually or for testing:

```bash
# For a running emulator process
echo -500 | sudo tee /proc/$(pgrep -f linblock)/oom_score_adj

# Verify
cat /proc/$(pgrep -f linblock)/oom_score_adj
```

### systemd Service Override

If LinBlock is managed by systemd:

```ini
# /etc/systemd/system/linblock.service.d/oom.conf
[Service]
OOMScoreAdjust=-500
```

## cgroup Memory Limits

### Why Use cgroups

cgroups (control groups) provide hard limits on memory usage, preventing the
emulator from consuming all available host memory. This is especially useful
when running LinBlock alongside other important applications.

### Setup (cgroup v2)

```bash
# Create LinBlock cgroup
sudo mkdir -p /sys/fs/cgroup/linblock

# Set limits
# memory.max: hard limit (OOM kill if exceeded)
# memory.high: soft limit (throttle if exceeded)
echo "8G" | sudo tee /sys/fs/cgroup/linblock/memory.max
echo "7G" | sudo tee /sys/fs/cgroup/linblock/memory.high

# Move emulator process into cgroup
echo $(pgrep -f linblock) | sudo tee /sys/fs/cgroup/linblock/cgroup.procs

# Monitor usage
cat /sys/fs/cgroup/linblock/memory.current
cat /sys/fs/cgroup/linblock/memory.stat
```

### Recommended cgroup Limits

| Host RAM | memory.max | memory.high | Guest RAM |
|----------|-----------|-------------|-----------|
| 8 GB | 5 GB | 4.5 GB | 2 GB |
| 12 GB | 8 GB | 7 GB | 4 GB |
| 16 GB | 10 GB | 9 GB | 4-6 GB |
| 32 GB | 12 GB | 11 GB | 4-8 GB |

### Using systemd Slice

For a systemd-managed setup:

```bash
# Create a systemd slice for LinBlock
sudo systemd-run --slice=linblock.slice \
    --property=MemoryMax=8G \
    --property=MemoryHigh=7G \
    -- linblock start
```

## Swap Configuration

### Recommendations

A properly configured swap space acts as a safety net against OOM conditions.

**Swap size recommendations:**

| Host RAM | Swap Size | Notes |
|----------|-----------|-------|
| 8 GB | 8 GB | Equal to RAM for safety |
| 12 GB | 6 GB | Half of RAM is sufficient |
| 16 GB+ | 4-8 GB | Swap is rarely used |

### Creating a Swap File

```bash
# Create 6 GB swap file
sudo fallocate -l 6G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make persistent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab

# Verify
swapon --show
```

### zswap (Compressed Swap Cache)

zswap compresses swap pages in RAM before writing them to disk, reducing
I/O and improving performance when swap is needed.

```bash
# Enable zswap
echo 1 | sudo tee /sys/module/zswap/parameters/enabled

# Use lz4 compression (fast)
echo lz4 | sudo tee /sys/module/zswap/parameters/compressor

# Set pool size to 20% of RAM
echo 20 | sudo tee /sys/module/zswap/parameters/max_pool_percent

# Make persistent via kernel command line
# Add to GRUB_CMDLINE_LINUX: zswap.enabled=1 zswap.compressor=lz4
```

### zram (Alternative to Disk Swap)

zram creates a compressed RAM disk for swap, which is faster than disk-based
swap and useful on systems without an SSD:

```bash
# Load zram module
sudo modprobe zram

# Create 4 GB zram device
echo 4G | sudo tee /sys/block/zram0/disksize
sudo mkswap /dev/zram0
sudo swapon -p 10 /dev/zram0  # Priority 10 (higher = preferred)
```

## Monitoring Memory Usage

### Key Commands

```bash
# Overall memory status
free -h

# Detailed memory info
cat /proc/meminfo

# Hugepage status
grep HugePages /proc/meminfo

# LinBlock process memory
ps -o pid,rss,vsz,comm -p $(pgrep -f linblock)

# Detailed process memory map
pmap -x $(pgrep -f linblock)

# cgroup memory usage
cat /sys/fs/cgroup/linblock/memory.current 2>/dev/null

# Watch memory pressure in real-time
watch -n 1 'free -h; echo "---"; grep HugePages /proc/meminfo'
```

### Memory Pressure Indicators

| Indicator | Normal | Warning | Critical |
|-----------|--------|---------|----------|
| MemAvailable | > 2 GB | 512 MB - 2 GB | < 512 MB |
| Swap usage | < 100 MB | 100 MB - 1 GB | > 1 GB |
| Page faults/sec | Low | Increasing | Very high |
| oom_kill count | 0 | 0 | Any non-zero |

## Complete Configuration Script

For convenience, here is a complete script that applies all recommended settings:

```bash
#!/bin/bash
# linblock-memory-tune.sh - Apply all recommended memory settings
set -e

if [ "$(id -u)" -ne 0 ]; then
    echo "Run as root: sudo $0"
    exit 1
fi

echo "Applying LinBlock memory tuning..."

# Swappiness
sysctl -w vm.swappiness=10

# Hugepages (adjust count for your guest RAM size)
sysctl -w vm.nr_hugepages=2048

# Transparent hugepages
echo madvise > /sys/kernel/mm/transparent_hugepage/enabled
echo madvise > /sys/kernel/mm/transparent_hugepage/defrag

# zswap
echo 1 > /sys/module/zswap/parameters/enabled 2>/dev/null || true
echo lz4 > /sys/module/zswap/parameters/compressor 2>/dev/null || true

# Persist sysctl settings
cat > /etc/sysctl.d/99-linblock.conf <<EOF
vm.swappiness = 10
vm.nr_hugepages = 2048
EOF
sysctl -p /etc/sysctl.d/99-linblock.conf

echo "Memory tuning applied successfully."
echo "Note: Some settings require a reboot to take full effect."
```

## Troubleshooting

### Emulator runs slowly

1. Check if guest RAM is being swapped: `grep VmSwap /proc/$(pgrep -f linblock)/status`
2. If VmSwap is high, reduce swappiness or increase host RAM
3. Check hugepage allocation: `grep HugePages /proc/meminfo`

### Cannot allocate hugepages

1. Try allocating at boot time via kernel command line
2. Compact memory: `echo 1 > /proc/sys/vm/compact_memory`
3. Ensure no other hugepage consumers are present

### OOM kills during emulation

1. Reduce guest RAM size in LinBlock configuration
2. Increase swap space
3. Close other memory-intensive applications
4. Set up cgroup limits to prevent runaway memory usage

### High memory usage even when guest is idle

1. This is normal; guest RAM remains mapped even when the guest is idle
2. The host kernel may page out unused guest pages if swap is available
3. Future: memory ballooning will allow reclaiming unused guest pages
