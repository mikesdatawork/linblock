# Phase 1 Milestones -- Emulator Foundation

**Document Owner:** Agent 001 (TPM)
**Last Updated:** 2026-01-28
**Status:** Phase A -- Planning

---

## Milestone Summary

| ID | Milestone                | Owner(s)         | Target   | Status  |
|----|--------------------------|------------------|----------|---------|
| M1 | Host Verification        | Agent 004        | Week 1   | Planned |
| M2 | Minimal Emulator Core    | Agent 003        | Week 3   | Planned |
| M3 | Device Framework         | Agent 003        | Week 5   | Planned |
| M4 | Display Output           | Agent 003 + 006  | Week 7   | Planned |
| M5 | Input Handling           | Agent 003        | Week 8   | Planned |
| M6 | Network Emulation        | Agent 003        | Week 9   | Planned |
| M7 | Storage Management       | Agent 003        | Week 10  | Planned |
| M8 | GUI Integration          | Agent 006        | Week 12  | Planned |

---

## M1: Host Verification Complete

**Description:**
The host verification subsystem can detect whether the current Linux host meets all requirements for running LinBlock. It checks for KVM availability, CPU virtualization extensions, sufficient RAM and disk, GPU capabilities, and required system packages. The output is a structured capability report that other modules consume at startup.

**Owner:** Agent 004

**Dependencies:** None (first milestone)

**Acceptance Criteria:**

1. Running `linblock --check-host` produces a JSON report containing:
   - `kvm_available`: boolean, true when `/dev/kvm` is accessible and functional.
   - `cpu_vendor`: string, "intel" or "amd".
   - `virt_extensions`: boolean, true when VT-x/AMD-V is enabled.
   - `ram_total_mb`: integer, host total RAM.
   - `ram_available_mb`: integer, host available RAM.
   - `disk_free_gb`: integer, free space on the LinBlock data directory.
   - `gpu_renderer`: string, OpenGL renderer string from the host GPU.
   - `missing_packages`: list of strings, any required packages not found.
2. The check completes in under 2 seconds on a reference machine.
3. If KVM is not available, the report clearly states the reason (module not loaded, no CPU support, permission denied).
4. Unit tests cover all detection paths, including mocked failure cases.
5. The module exposes a Python API: `host_check.verify() -> HostCapabilities`.

---

## M2: Minimal Emulator Core

**Description:**
A custom KVM-based emulator written in Python (with C extensions where needed) that can open `/dev/kvm`, create a virtual machine, configure vCPUs and memory, load a Linux kernel (bzImage), and execute the vCPU run-loop. The guest kernel boots and prints log output to a virtual serial console. This is the foundational component upon which all other stages build.

**Owner:** Agent 003

**Dependencies:** M1 (Host Verification -- must confirm KVM is usable)

**Acceptance Criteria:**

1. The emulator creates a VM with at least 1 vCPU and 512 MB of RAM using KVM ioctls (`KVM_CREATE_VM`, `KVM_CREATE_VCPU`, `KVM_SET_USER_MEMORY_REGION`).
2. A stock Linux kernel (bzImage, version 5.15+) is loaded into guest memory at the correct address and boots successfully.
3. The vCPU run-loop processes at minimum the following exit reasons:
   - `KVM_EXIT_IO` (port I/O for serial console)
   - `KVM_EXIT_MMIO` (memory-mapped I/O)
   - `KVM_EXIT_HLT` (guest halted)
   - `KVM_EXIT_SHUTDOWN` (guest shutdown/reset)
4. Kernel boot messages appear on the host terminal via the emulated serial port.
5. The guest kernel reaches the point where it attempts to mount a root filesystem (panic on no rootfs is acceptable at this stage).
6. Boot-to-serial-output time is under 5 seconds on the reference machine.
7. Clean shutdown: the emulator releases all KVM resources (VM fd, vCPU fd, mapped memory) on exit.
8. The module exposes a Python API: `EmulatorCore.create(config) -> VM`, `VM.start()`, `VM.stop()`, `VM.pause()`, `VM.resume()`.

---

## M3: Device Framework

**Description:**
A virtual device framework that allows device implementations (serial, block, network, input, display) to register themselves and handle I/O requests dispatched from the vCPU run-loop. The framework manages I/O port ranges, MMIO address regions, and interrupt injection.

**Owner:** Agent 003

**Dependencies:** M2 (Emulator Core -- the run-loop must be functional to dispatch I/O)

**Acceptance Criteria:**

1. A `DeviceRegistry` class allows devices to register for specific I/O port ranges and MMIO address ranges.
2. When the vCPU exits with `KVM_EXIT_IO` or `KVM_EXIT_MMIO`, the run-loop dispatches the request to the correct registered device handler.
3. A virtual UART 16550A serial device is implemented and produces correct serial output from the guest kernel.
4. A virtio-blk device is implemented and can serve a raw disk image as a block device to the guest.
5. The guest kernel, when provided with a root filesystem on the virtio-blk device, successfully mounts it and proceeds to userspace init.
6. Devices support lifecycle methods: `reset()`, `attach()`, `detach()`.
7. IRQ injection works: devices can raise interrupts via `KVM_INTERRUPT` or `KVM_SIGNAL_MSI` and the guest handles them.
8. At least 10 unit tests cover device registration, dispatch, read/write operations, and lifecycle.

---

## M4: Display Output

**Description:**
The guest Android graphical output is captured from a virtual display device and rendered in a GTK window on the host. The user sees the Android boot animation and home screen inside the LinBlock window.

**Owner:** Agent 003 (virtual display device), Agent 006 (GTK rendering)

**Dependencies:** M3 (Device Framework -- virtio-gpu or framebuffer device must be registerable)

**Acceptance Criteria:**

1. A virtual display device (virtio-gpu 2D or simple framebuffer) exposes a linear framebuffer to the guest at a configurable resolution (default: 1280x720).
2. Guest Android renders its UI into the virtual framebuffer.
3. The host reads the framebuffer contents and presents them in a `Gtk.DrawingArea` using a Cairo image surface.
4. Frame rate is at least 30 fps at 1280x720 resolution, measured by an internal FPS counter displayed in the status bar.
5. The display correctly handles resolution changes if the guest requests them.
6. The display window can be resized; the framebuffer scales proportionally.
7. No visible tearing or corruption under normal operation.
8. The display pipeline has a documented latency measurement point (framebuffer write to screen present).

---

## M5: Input Handling

**Description:**
Host-side mouse and keyboard events captured by the GTK window are translated into Android-compatible touch and key events and injected into the guest via a virtio-input device. The user can interact with the Android UI naturally.

**Owner:** Agent 003

**Dependencies:** M4 (Display Output -- input coordinates must map to the displayed framebuffer)

**Acceptance Criteria:**

1. Mouse motion events in the GTK display area are translated to Android `ABS_MT_POSITION_X` / `ABS_MT_POSITION_Y` touch events and injected via virtio-input.
2. Mouse button press/release maps to Android touch down/up events.
3. Keyboard key press/release events map to Android key events using a configurable keymap.
4. Ctrl+click produces a simulated two-finger pinch gesture for zoom testing.
5. Input coordinates correctly account for display scaling (if the GTK window is resized).
6. Input-to-display latency (button press to visible UI change) is below 50 ms, verified by a timestamp-based test.
7. The input device reports correct device capabilities to the guest (supported event types, axis ranges).
8. At least 5 unit tests cover coordinate translation, key mapping, and multi-touch simulation.

---

## M6: Network Emulation

**Description:**
The guest Android instance has working network connectivity. A virtual network device connects the guest to the host network via NAT, allowing the guest to access the internet for app downloads, updates, and general use.

**Owner:** Agent 003

**Dependencies:** M3 (Device Framework -- virtio-net device registration)

**Acceptance Criteria:**

1. A virtio-net device is presented to the guest and recognized by the Android network stack.
2. A TAP interface is created on the host and bridged to the virtio-net device.
3. NAT is configured (via iptables or nftables) so the guest can reach external networks through the host's default route.
4. The guest can resolve DNS names and fetch HTTPS URLs (verified by `ping 8.8.8.8` and `curl https://example.com` from an adb shell).
5. When TAP is unavailable (insufficient privileges), a user-mode networking fallback (SLIRP-style) is used automatically.
6. Host-to-guest port forwarding is supported (e.g., forward host port 5555 to guest ADB port 5555).
7. Network throughput is at least 10 Mbps between host and guest, measured with iperf3.
8. The network subsystem logs connection events and errors to the LinBlock log.

---

## M7: Storage Management

**Description:**
Guest data persists across emulator restarts. The storage subsystem manages disk images, supports snapshots for quick rollback, and provides overlay images for copy-on-write operation.

**Owner:** Agent 003

**Dependencies:** M3 (Device Framework -- virtio-blk device must be functional)

**Acceptance Criteria:**

1. The guest root filesystem is served from a QCOW2 image (or raw image with overlay support).
2. A separate `/data` partition image persists user data (installed apps, settings, files) across emulator stop/start cycles.
3. Snapshot creation: `storage_manager.snapshot("name")` saves the current state of all disk images; completes in under 10 seconds for a 4 GB image.
4. Snapshot restore: `storage_manager.restore("name")` reverts all disk images to the named snapshot; completes in under 5 seconds.
5. Overlay images: the system can create a copy-on-write overlay so that the base image is never modified; discarding the overlay reverts all changes.
6. Disk image integrity is verified on load (checksum validation).
7. Storage usage is reported: total size, allocated size, available space.
8. At least 5 integration tests verify persistence, snapshot, restore, and overlay discard.

---

## M8: GUI Integration

**Description:**
A complete GTK 4 dashboard application that wraps the emulator viewport and provides navigation to all management pages. The user interacts with LinBlock entirely through this interface.

**Owner:** Agent 006

**Dependencies:** M4 (Display Output), M5 (Input Handling) -- the emulator viewport must be renderable and interactive.

**Acceptance Criteria:**

1. The application launches as a GTK 4 window with a sidebar navigation panel and a main content area.
2. Sidebar contains navigation entries: Home, Apps, Permissions, Network, Storage, Logs.
3. The Home page embeds the emulator display viewport (from M4) and control buttons: Start, Stop, Pause, Restart.
4. Control buttons correctly invoke `EmulatorCore` methods and update their visual state (e.g., Start grays out while running, Stop grays out while stopped).
5. A status bar at the bottom shows: guest CPU usage (%), guest RAM usage (MB), display FPS, network throughput (KB/s).
6. The Apps, Permissions, Network, Storage, and Logs pages display placeholder content with correct page titles (full content is Phase 3).
7. The window supports resizing; the emulator viewport scales proportionally while sidebar and status bar remain at fixed widths.
8. The application handles emulator crashes gracefully: displays an error message and allows restart without crashing the GUI.
9. Window state (size, position, sidebar collapsed/expanded) persists across application restarts via a settings file.
10. The application starts and displays the Home page in under 2 seconds (without emulator boot time).

---

## Milestone Dependency Graph

```
M1 (Host Verification)
 |
 v
M2 (Emulator Core) <<<--- CRITICAL PATH
 |
 v
M3 (Device Framework)
 |_________________________
 |           |             |
 v           v             v
M4 (Display) M6 (Network) M7 (Storage)
 |
 v
M5 (Input)
 |
 v
M8 (GUI Integration) <--- also depends on M4, M5
```

---

## Revision History

| Date       | Author    | Change                          |
|------------|-----------|---------------------------------|
| 2026-01-28 | Agent 001 | Initial milestone definitions   |
