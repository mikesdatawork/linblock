# Risk Register

**Document Owner:** Agent 001 (TPM)
**Last Updated:** 2026-01-28
**Status:** Phase A -- Planning

---

## Risk Matrix Legend

**Probability:** L = Low (< 20%), M = Medium (20--60%), H = High (> 60%)

**Impact:** L = Low (workaround exists, < 1 week delay), M = Medium (significant rework, 1--3 week delay), H = High (blocks critical path, > 3 week delay or architectural change)

**Status:** Open, Mitigating, Accepted, Closed

---

## Risk Table

| ID   | Risk Description                                                        | Prob | Impact | Mitigation Strategy                                                                                                                                                                       | Owner     | Status |
|------|-------------------------------------------------------------------------|------|--------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-----------|--------|
| R001 | KVM not available on target hardware (missing CPU extensions, module not loaded, or permission denied on `/dev/kvm`)                  | L    | H      | 1. Document minimum hardware requirements upfront. 2. Host verification (M1) detects this on first run. 3. Fallback: software emulation via TCG (QEMU backend) with degraded performance warning. | Agent 004 | Open   |
| R002 | AOSP image boot failure (kernel panic, init crash, missing drivers for virtual hardware)                                              | M    | H      | 1. Test with multiple AOSP images (API 33, 34, 35). 2. Use Android Studio AVD as a reference to validate virtual hardware configuration. 3. Maintain a known-good image in CI artifacts.   | Agent 003 | Open   |
| R003 | Display rendering performance below 30 fps at 1280x720                                                                                | M    | M      | 1. Profile framebuffer transfer path and eliminate copies. 2. Investigate GPU passthrough or virgl for hardware-accelerated rendering. 3. Allow resolution downscaling as a fallback.       | Agent 003 | Open   |
| R004 | Memory constraints: host has only 12 GB RAM, guest needs 4 GB, AOSP build needs 16 GB+                                               | M    | M      | 1. Limit guest RAM to 4 GB maximum. 2. Configure zram/swap for the host. 3. AOSP builds use `-j2` parallelism and run on a build server, not the development machine.                      | Agent 003 | Open   |
| R005 | GTK/GLib thread safety issues when emulator threads update UI                                                                         | H    | M      | 1. All UI updates go through `GLib.idle_add()` to marshal onto the main thread. 2. Emulator core communicates with UI via a thread-safe queue. 3. Code review checklist includes thread safety. | Agent 006 | Open   |
| R006 | KVM ioctl API complexity leads to implementation delays or subtle bugs in the emulator core                                           | M    | H      | 1. Start with QEMU as the VM backend (via QMP protocol) to unblock other stages. 2. Develop custom KVM backend in parallel. 3. Abstract behind a `VMBackend` interface so backends are swappable. | Agent 003 | Open   |
| R007 | AMD GPU driver compatibility issues (mesa vs AMDGPU-PRO, Vulkan/OpenGL version mismatches)                                            | L    | M      | 1. Target mesa open-source drivers as the primary path. 2. Test on both AMD and Intel GPUs in CI. 3. Software rendering (llvmpipe) as a fallback for headless/CI environments.              | Agent 003 | Open   |
| R008 | AOSP build requires more than 16 GB RAM, exceeding available resources on developer machines                                          | H    | M      | 1. Use swap space (32 GB swap file). 2. Limit build parallelism (`-j2`). 3. Provision a dedicated build server or use cloud CI with 32 GB+ RAM. 4. Use prebuilt AOSP images for development. | Agent 004 | Open   |
| R009 | Input latency exceeds 50 ms, making the Android UI feel unresponsive                                                                  | M    | M      | 1. Inject input events directly via virtio-input (bypass ADB). 2. Minimize buffering layers between GTK event and guest injection. 3. Profile and measure latency at each stage of the pipeline. | Agent 003 | Open   |
| R010 | Module integration issues: incompatible interfaces between emulator_core, gui_shell, permission_manager, and other modules             | M    | M      | 1. Define strict interface contracts (Python ABCs / Protocols) before implementation begins. 2. Integration tests run in CI on every merge. 3. Weekly integration checkpoint meetings.      | Agent 001 | Open   |

---

## Risk Response Actions Log

| Date       | Risk ID | Action Taken                                    | Result          |
|------------|---------|-------------------------------------------------|-----------------|
| 2026-01-28 | ALL     | Initial risk identification and documentation   | Register created |

---

## Review Schedule

This risk register is reviewed and updated at every weekly TPM sync. Any team member may add a new risk at any time by appending a row and notifying Agent 001.

---

## Escalation Criteria

A risk is escalated to the full team when:

- Its probability increases to **H** AND its impact is **H**.
- A mitigation strategy has failed and no alternative is identified.
- The risk materializes and impacts the critical path (M2: Emulator Core or any of its downstream dependencies).

---

## Revision History

| Date       | Author    | Change                          |
|------------|-----------|---------------------------------|
| 2026-01-28 | Agent 001 | Initial risk register creation  |
