# LinBlock Project Roadmap

**Document Owner:** Agent 001 (TPM)
**Last Updated:** 2026-01-28
**Status:** Phase A -- Planning

---

## Overview

LinBlock is a Linux-native Android emulator with enterprise-grade security controls, built on KVM virtualization with a custom GTK-based management interface. The project proceeds through five sequential phases, each building on the deliverables of the prior phase.

---

## Phase 1: Emulator Foundation

**Goal:** Boot a stock AOSP x86_64 image inside a GTK window on a Linux host, with mouse/keyboard input and basic playback controls (start, stop, pause, restart).

**Duration estimate:** 8--12 weeks

### Stage 1: Host Verification

- Detect KVM availability (`/dev/kvm` access, CPU virtualization flags).
- Verify minimum host resources (RAM, disk, GPU).
- Validate required packages and kernel modules.
- Produce a machine-readable capability report (JSON).

### Stage 2: Minimal Emulator Core

- Open `/dev/kvm`, create VM file descriptor, configure vCPUs and memory regions.
- Load a minimal Linux kernel (bzImage) into guest physical memory.
- Implement the vCPU run-loop (`KVM_RUN` ioctl) with exit-reason dispatch.
- Handle `KVM_EXIT_IO`, `KVM_EXIT_MMIO`, `KVM_EXIT_HLT`, `KVM_EXIT_SHUTDOWN`.
- Boot to kernel log output on a virtual serial console.

### Stage 3: Device Framework

- Implement a virtual serial device (UART 16550A) for console I/O.
- Implement a virtio-blk device for block storage.
- Create a device registry that maps I/O port ranges and MMIO regions to device handlers.
- Support device reset and hot-removal lifecycle.

### Stage 4: Display Output

- Map guest framebuffer memory to a host-side buffer.
- Implement a virtio-gpu device (or direct framebuffer protocol) that exposes a linear framebuffer.
- Render framebuffer contents to a GTK `DrawingArea` via Cairo surface.
- Achieve a minimum of 30 fps at 1280x720 resolution.

### Stage 5: Input Handling

- Translate GTK mouse events (motion, button press/release) into Android touch events via virtio-input.
- Translate GTK keyboard events into Android key events via virtio-input.
- Support multi-touch emulation (Ctrl+click for pinch-zoom simulation).
- Measure and maintain input-to-display latency below 50 ms.

### Stage 6: Network Emulation

- Create a TAP/TUN interface on the host and bridge it to a virtio-net device in the guest.
- Configure NAT via iptables/nftables so the guest can reach the internet.
- Support user-mode networking (SLIRP-style) as a fallback when TAP is unavailable.
- Expose DNS configuration to the guest.

### Stage 7: Storage Management

- Implement QCOW2 (or raw + overlay) image management for the guest root filesystem.
- Support persistent `/data` partition across emulator restarts.
- Implement snapshot and restore of disk state.
- Provide copy-on-write overlay images for quick rollback.

### Stage 8: GUI Integration

- Build a GTK 4 dashboard shell with a sidebar navigation and page-based content area.
- Pages: Home (emulator viewport + controls), Apps, Permissions, Network, Storage, Logs.
- Implement start / stop / pause / restart controls wired to the emulator core.
- Status bar showing guest CPU, RAM, FPS, and network throughput.

---

## Phase 2: Custom Android OS

**Goal:** Replace the stock AOSP image with a purpose-built, minimal Android distribution that exposes the control hooks LinBlock requires.

**Duration estimate:** 6--8 weeks
**Depends on:** Phase 1 (Stages 1--7 complete)

### Key deliverables

- AOSP build system integration (lunch target, device tree, vendor partition).
- Custom device tree (`linblock_x86_64`) with hardware abstraction for the virtual devices from Phase 1.
- Minimal system image: stripped services, no Google Play, no default launcher.
- LinBlock system service (`com.linblock.system`) running as a privileged process.
- Binder IPC interface for the host to query and control the guest.
- Custom init.rc with LinBlock-specific service entries.

---

## Phase 3: App Management

**Goal:** Give the host full control over which apps run, what permissions they hold, and how resources are allocated.

**Duration estimate:** 6--8 weeks
**Depends on:** Phase 2 (system service running); can partially overlap with Phase 2 once the system service skeleton is in place.

### Key deliverables

- Permission manager: per-app grant/deny/ask-every-time for every Android permission.
- Process controller: freeze, unfreeze, kill individual apps from the host.
- App installer: sideload APKs with pre-install permission review.
- Resource quotas: per-app CPU, memory, network bandwidth limits.
- Audit logger: JSON-lines log of every permission check, app lifecycle event, and user action.

---

## Phase 4: Security Hardening

**Goal:** Harden both the guest OS and the host boundary so that a compromised app cannot affect the host or other apps beyond its granted permissions.

**Duration estimate:** 4--6 weeks
**Depends on:** Phase 2 (custom OS) + Phase 3 (permission system) both substantially complete.

### Key deliverables

- SELinux enforcing mode with custom policy modules aligned to the permission manager.
- Verified boot chain: signed kernel, signed system image, dm-verity on system partition.
- Network isolation: per-app firewall rules enforced via eBPF or iptables inside the guest.
- Storage encryption: dm-crypt on `/data`, key derived from host-provided passphrase.
- Host-side hardening: AppArmor profile for the emulator process, seccomp-bpf filter on syscalls.
- Penetration test plan and execution.

---

## Phase 5: Polish and Release

**Goal:** Optimize performance, refine the UI, complete documentation, and ship a v1.0 release.

**Duration estimate:** 4--6 weeks
**Depends on:** All prior phases complete.

### Key deliverables

- Performance profiling and optimization (target: boot < 15 s, 60 fps display, < 50 ms input latency).
- UI/UX refinement based on usability testing.
- Comprehensive user documentation (installation, configuration, usage).
- Developer documentation (architecture, API reference, contribution guide).
- Automated CI/CD pipeline (build, test, package).
- Release artifacts: `.deb` package, Flatpak, AppImage.

---

## Dependency Graph

```
Phase 1: Emulator Foundation
    |
    |--- blocks ---> Phase 2: Custom Android OS
    |                    |
    |                    |--- blocks (partially) ---> Phase 3: App Management
    |                    |                                |
    |                    |--- both block ----------------+---> Phase 4: Security Hardening
    |                                                              |
    |                                                              |
    +--- all phases block -----------------------------------------+---> Phase 5: Polish & Release
```

### Detailed dependency edges

```
P1.S1 (Host Verification)    --> P1.S2 (Emulator Core)
P1.S2 (Emulator Core)        --> P1.S3 (Device Framework)
P1.S3 (Device Framework)     --> P1.S4 (Display Output)
P1.S3 (Device Framework)     --> P1.S5 (Input Handling)
P1.S3 (Device Framework)     --> P1.S6 (Network Emulation)
P1.S3 (Device Framework)     --> P1.S7 (Storage Management)
P1.S4 (Display Output)       --> P1.S8 (GUI Integration)
P1.S5 (Input Handling)       --> P1.S8 (GUI Integration)

P1.S2 (Emulator Core)        --> P2 (Custom Android OS)
P1.S7 (Storage Management)   --> P2 (Custom Android OS)

P2 (Custom Android OS)        --> P3 (App Management)      [partial overlap OK]
P2 (Custom Android OS)        --> P4 (Security Hardening)
P3 (App Management)           --> P4 (Security Hardening)

P4 (Security Hardening)       --> P5 (Polish & Release)
P3 (App Management)           --> P5 (Polish & Release)
P1.S8 (GUI Integration)       --> P5 (Polish & Release)
```

---

## Critical Path

The single most critical deliverable in the entire project is **Phase 1, Stage 2: Minimal Emulator Core** (`emulator_core`). Every subsequent stage, phase, and deliverable depends directly or transitively on the ability to create a KVM virtual machine, load a kernel, and run a vCPU loop.

**Critical path sequence:**

```
P1.S1 --> P1.S2 (CRITICAL) --> P1.S3 --> P1.S4 --> P1.S8 --> P5
                                  |
                                  +--> P1.S6
                                  +--> P1.S7 --> P2 --> P3 --> P4 --> P5
```

If `emulator_core` slips, every other deliverable slips by at least the same amount. Mitigation: allocate the strongest systems engineer (Agent 003) to this stage, time-box to 2 weeks with a hard checkpoint, and maintain QEMU as a fallback backend (see Risk Register R006).

---

## Revision History

| Date       | Author    | Change                          |
|------------|-----------|---------------------------------|
| 2026-01-28 | Agent 001 | Initial roadmap creation        |
