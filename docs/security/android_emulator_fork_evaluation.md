# Security Evaluation: Forking Google's Android Emulator (AOSP external/qemu)

**Document Owner:** Agent 005 (Security Architect)
**Last Updated:** 2026-01-29
**Status:** Security Review - Decision Pending

---

## Executive Summary

This document evaluates the security implications of forking Google's Android Emulator (AOSP `external/qemu`) to replace LinBlock's planned custom QEMU-based emulator. The Android Emulator offers better Android compatibility and GPU acceleration via `libOpenglRender`, but introduces significant security trade-offs.

**Recommendation:** CONDITIONAL PROCEED with significant security requirements. The fork provides compelling benefits for Android compatibility, but LinBlock MUST implement additional isolation layers beyond what the Android Emulator provides.

---

## 1. Attack Surface Analysis

### 1.1 Codebase Size Comparison

| Component | Raw QEMU | Android Emulator | Delta |
|-----------|----------|------------------|-------|
| Core QEMU | ~2.5M LOC | ~2.5M LOC | 0 |
| Android-specific additions | N/A | ~500K LOC | +500K |
| libOpenglRender | N/A | ~150K LOC | +150K |
| Goldfish/Ranchu devices | N/A | ~100K LOC | +100K |
| Android Studio integration | N/A | ~200K LOC | (not needed) |
| **Total attack surface** | ~2.5M LOC | ~3.4M+ LOC | **+36%** |

### 1.2 Additional Attack Vectors Introduced

The Android Emulator introduces attack vectors not present in raw QEMU:

#### 1.2.1 GPU Translation Layer (libOpenglRender) - CRITICAL

```
+----------------+     OpenGL ES calls     +------------------+
| Guest Android  | ----------------------> | libOpenglRender  |
| (Untrusted)    |   via virtio-gpu pipe   | (Host process)   |
+----------------+                         +------------------+
                                                  |
                                           Host OpenGL/Vulkan
                                                  |
                                           +------v------+
                                           | Host GPU    |
                                           | Driver      |
                                           +-------------+
```

**Security Concerns:**

1. **Shader Parsing:** Guest-provided shaders are translated and compiled on the host. Malicious shaders could exploit:
   - Buffer overflows in the ANGLE shader translator
   - GPU driver vulnerabilities via crafted shader code
   - Denial of service via resource exhaustion (infinite loops, memory bombs)

2. **OpenGL State Machine Complexity:** OpenGL has ~3,000 entry points. Each is a potential:
   - Use-after-free (texture/buffer handle reuse)
   - Out-of-bounds access (vertex buffer indexing)
   - Integer overflow (size calculations)

3. **Memory Sharing:** Texture uploads and framebuffer transfers involve shared memory regions between guest and host, increasing the risk of memory corruption attacks.

**Historical CVEs in Similar Systems:**
- [CVE-2024-7730](https://www.cvedetails.com/vulnerability-list/vendor_id-7506/Qemu.html): virtio-snd heap buffer overflow
- [CVE-2024-6505](https://www.cvedetails.com/vulnerability-list/vendor_id-7506/Qemu.html): virtio-net RSS index out-of-bounds
- [CVE-2023-6693](https://www.cvedetails.com/vulnerability-list/vendor_id-7506/Qemu.html): virtio-net stack buffer overflow

#### 1.2.2 Goldfish/Ranchu Virtual Devices

The Android Emulator includes custom virtual devices:

| Device | Function | Attack Surface |
|--------|----------|----------------|
| goldfish_battery | Battery state simulation | Low (read-only state) |
| goldfish_pipe | High-speed guest-host communication | **HIGH** (arbitrary data) |
| goldfish_audio | Audio I/O | Medium (buffer handling) |
| goldfish_sensors | Accelerometer, GPS, etc. | Low (simple data) |
| goldfish_sync | Fence synchronization | Medium (timing side channels) |

**goldfish_pipe is the primary concern:** It provides a high-bandwidth channel for OpenGL command streams and is the conduit for all GPU translation traffic.

#### 1.2.3 ADB Integration

The Android Emulator has tighter ADB integration than raw QEMU:
- ADB daemon runs automatically
- Guest-host communication channels are pre-configured
- Risk of command injection if package names are not sanitized (see existing threat model)

### 1.3 Attack Surface Verdict

| Aspect | Raw QEMU | Android Emulator | Verdict |
|--------|----------|------------------|---------|
| Code complexity | Lower | Higher (+36%) | CONCERN |
| Virtual devices | Standard virtio | Custom goldfish + virtio | CONCERN |
| GPU passthrough | None or virgl | libOpenglRender | **MAJOR CONCERN** |
| Guest-host channels | virtio-serial | goldfish_pipe + virtio | CONCERN |
| Maintenance burden | Upstream community | Google + LinBlock | NEUTRAL |

---

## 2. Supply Chain Security

### 2.1 Dependency on Google's Codebase

**Risks:**

1. **Upstream Changes:** Google may make breaking changes, abandon features, or introduce telemetry that conflicts with LinBlock's privacy goals.

2. **Delayed Security Patches:** Google's emulator patches are tied to Android Studio releases, which may lag behind upstream QEMU security fixes.

3. **Divergence Over Time:** As LinBlock customizes the fork, rebasing becomes increasingly difficult, potentially leaving security fixes unapplied.

4. **Binary Blobs:** The Android Emulator may include or require binary components (GPU libraries, firmware) that cannot be audited.

### 2.2 Integrity Verification Strategy

**REQUIRED CONTROLS:**

```
+------------------+     Fetch      +------------------+
| LinBlock CI/CD   | <------------- | Google Git       |
| (Isolated runner)|                | (android.google  |
+--------+---------+                |  source.com)     |
         |                          +------------------+
         | Verify
         v
+------------------+
| 1. GPG signature |
| 2. Commit hash   |
| 3. SBOM compare  |
| 4. Reproducible  |
|    build check   |
+------------------+
         |
         | Only if passes
         v
+------------------+
| LinBlock Fork    |
| Repository       |
+------------------+
```

**Verification Checklist:**

1. **Pin to specific commit hashes**, never branches
2. **Verify GPG signatures** on commits (if signed)
3. **Generate and compare SBOM** (Software Bill of Materials) on each sync
4. **Reproducible builds:** Build the same commit twice and verify identical output
5. **Static analysis:** Run Coverity, CodeQL, or similar on each sync
6. **Diff review:** Manual review of changes between syncs (at least security-relevant code)

### 2.3 Recommended Sync Cadence

| Event | Action |
|-------|--------|
| Monthly | Sync with upstream, full verification |
| Security bulletin (any) | Immediate evaluation, expedited sync if affected |
| Major Android release | Full sync with extended testing |
| LinBlock feature freeze | Freeze sync, security patches only |

---

## 3. Sandboxing Analysis

### 3.1 Android Emulator Built-in Sandboxing

**Current state:** The Android Emulator (AOSP `external/qemu`) has **minimal built-in sandboxing**:

- No seccomp-bpf filter applied by default
- No namespace isolation
- No cgroup confinement
- Relies on user-level process isolation only
- Designed to run on developer workstations with broad permissions

**This is inadequate for LinBlock's security goals.**

### 3.2 Required Additional Isolation

LinBlock MUST implement isolation layers on top of the Android Emulator fork:

#### 3.2.1 Seccomp-BPF Filter (MANDATORY)

```c
// Conceptual seccomp policy for LinBlock emulator

ALLOWED_SYSCALLS = {
    // Memory management
    mmap, munmap, mprotect, brk, mremap,

    // File I/O (filtered by path)
    openat, read, write, close, fstat, lseek,
    pread64, pwrite64, readv, writev,

    // KVM operations
    ioctl,  // FILTERED: only KVM_* ioctls allowed

    // Process management
    exit_group, rt_sigaction, rt_sigprocmask,
    rt_sigreturn, sigaltstack,

    // Threading
    clone,      // FILTERED: only CLONE_THREAD allowed post-init
    futex, set_robust_list, get_robust_list,

    // Time
    clock_gettime, gettimeofday, nanosleep,

    // Networking (for virtio-net backend)
    socket,     // FILTERED: AF_INET/AF_INET6 only, no AF_NETLINK
    bind, connect, sendto, recvfrom, sendmsg, recvmsg,
    poll, ppoll, epoll_create1, epoll_ctl, epoll_wait,

    // GPU rendering (if enabled)
    // DRM ioctls via ioctl() - filtered by fd
};

DENIED_SYSCALLS = {
    execve, execveat,           // No spawning new processes
    fork, vfork,                // No forking (post-init)
    ptrace,                     // No debugging other processes
    mount, umount2,             // No filesystem changes
    reboot, kexec_load,         // No system control
    init_module, delete_module, // No kernel modules
    pivot_root, chroot,         // No namespace escapes
    setns, unshare,             // No namespace manipulation
    acct,                       // No process accounting
    swapon, swapoff,            // No swap control
    sethostname, setdomainname, // No system identity changes
};
```

**Implementation:** Use [libseccomp](https://github.com/seccomp/libseccomp) or raw `prctl(PR_SET_SECCOMP)`.

#### 3.2.2 Linux Namespaces (MANDATORY)

| Namespace | Purpose | Configuration |
|-----------|---------|---------------|
| `CLONE_NEWUSER` | Unprivileged user namespace | Map host UID to container UID 0 |
| `CLONE_NEWNS` | Mount namespace | Private `/dev` with only required nodes |
| `CLONE_NEWNET` | Network namespace | Only veth pair to host, no external access |
| `CLONE_NEWIPC` | IPC namespace | Isolate shared memory from host |
| `CLONE_NEWPID` | PID namespace | Hide host processes from emulator |
| `CLONE_NEWUTS` | UTS namespace | Isolated hostname |

**Implementation:** Use [nsjail](https://github.com/google/nsjail), bubblewrap, or direct syscalls.

#### 3.2.3 Cgroup Limits (MANDATORY)

```yaml
# /sys/fs/cgroup/linblock-emulator/

# CPU: 80% of available cores
cpu.max: "800000 1000000"  # 800ms per 1000ms

# Memory: Guest RAM + 1GB overhead
memory.max: "5368709120"   # 5 GB for 4 GB guest

# IO: Rate limit disk writes
io.max: "8:0 wbps=104857600"  # 100 MB/s

# PIDs: Limit process count
pids.max: "256"
```

#### 3.2.4 AppArmor/SELinux Profile (MANDATORY)

See `/home/user/projects/linblock/docs/security/selinux_requirements.md` Section 3.1 for the existing AppArmor profile specification. This must be extended to cover:

- libOpenglRender specific file access
- DRI render node access (deny master nodes)
- goldfish_pipe communication channels

### 3.3 Sandboxing Implementation Priority

| Layer | Priority | Blocks Release? |
|-------|----------|-----------------|
| Unprivileged user | P0 | YES |
| Seccomp-bpf filter | P0 | YES |
| Mount namespace | P0 | YES |
| Cgroup limits | P1 | YES |
| Network namespace | P1 | NO (but recommended) |
| AppArmor profile | P1 | YES |
| PID namespace | P2 | NO |

---

## 4. Guest-Host Isolation: GPU Translation Layer

### 4.1 Threat Model for libOpenglRender

```
+------------------------------------------------------------------+
|                        GUEST (Untrusted)                          |
|                                                                   |
|  +------------------+    +------------------+                     |
|  | Malicious App    |    | Benign App       |                     |
|  | (attacker)       |    |                  |                     |
|  +--------+---------+    +--------+---------+                     |
|           |                       |                               |
|           v                       v                               |
|  +--------------------------------------------+                   |
|  |        Android Graphics Stack              |                   |
|  |  (SurfaceFlinger, EGL, OpenGL ES driver)   |                   |
|  +---------------------+----------------------+                   |
|                        |                                          |
+========================|==========================================+
     TRUST BOUNDARY      |  goldfish_pipe / virtio-gpu
+========================|==========================================+
|                        v                                          |
|  +--------------------------------------------+                   |
|  |           libOpenglRender                  |  HOST (Trusted)   |
|  |  +----------------+  +------------------+  |                   |
|  |  | Command Parser |  | Shader Translator|  |                   |
|  |  +-------+--------+  +--------+---------+  |                   |
|  |          |                    |            |                   |
|  |          v                    v            |                   |
|  |  +--------------------------------------------+                |
|  |  |     Host OpenGL / Vulkan Implementation    |                |
|  |  +---------------------+----------------------+                |
|  +------------------------|---------------------------+           |
|                           v                                       |
|                  +--------+--------+                              |
|                  | Host GPU Driver |   <-- Kernel attack surface  |
|                  +-----------------+                              |
+-------------------------------------------------------------------+
```

### 4.2 Security Implications

#### 4.2.1 Parser Vulnerabilities

The OpenGL command stream from the guest is parsed by `libOpenglRender`. Vulnerabilities here allow:

- **Memory corruption:** Heap/stack buffer overflows
- **Type confusion:** Incorrect GL object type handling
- **Use-after-free:** GL object lifecycle bugs

**Mitigation:**
1. Fuzz the command parser with AFL/libFuzzer (REQUIRED before release)
2. Enable AddressSanitizer in CI builds
3. Apply bounds checking on all buffer operations

#### 4.2.2 Shader Compilation Attacks

Guest-provided shaders are compiled on the host using ANGLE's shader translator. Risks:

- **Compiler bugs:** ANGLE or host GL driver compiler vulnerabilities
- **GPU hangs:** Infinite loops in shaders freeze the host GPU
- **Memory exhaustion:** Large array declarations consume GPU memory

**Mitigation:**
1. Validate shader complexity (instruction count, loop bounds) before compilation
2. Set GPU timeout watchdog (requires driver support)
3. Run shader compilation in a separate process with strict resource limits
4. Consider using [SwiftShader](https://github.com/aspect-dev/aspect_aspect_rules_swiftshader) (software renderer) as a fallback for untrusted workloads

#### 4.2.3 Texture/Buffer Data Injection

Guest-provided texture data flows to host GPU memory. Risks:

- **Format string bugs:** If texture data is logged or displayed
- **GPU driver bugs:** Malformed texture data triggers driver vulnerabilities

**Mitigation:**
1. Validate all texture dimensions and formats
2. Impose maximum texture size limits
3. Do not log or display raw texture data

### 4.3 Isolation Architecture for GPU Translation

**REQUIRED:** Run libOpenglRender in a separate process with additional isolation:

```
+-------------------+
| Emulator Core     |  Main emulator process (KVM, devices)
| (Sandboxed)       |
+--------+----------+
         |
         | Unix socket (or shared memory with strict permissions)
         |
+--------v----------+
| GPU Renderer      |  Separate process
| (Extra Sandboxed) |
|                   |
| - Tighter seccomp |
| - No network      |
| - Read-only /     |
| - Separate cgroup |
+-------------------+
         |
         | DRI render node only
         v
+-------------------+
| /dev/dri/renderD* |
+-------------------+
```

**This architecture ensures that a GPU translation exploit only compromises the renderer process, not the main emulator process with KVM access.**

---

## 5. Update Strategy for Security Patches

### 5.1 Patch Sources

| Source | Content | Latency | Action |
|--------|---------|---------|--------|
| [QEMU Security Advisories](https://www.qemu.org/contribute/security-process/) | Upstream QEMU fixes | Immediate | Monitor, evaluate |
| [Android Security Bulletins](https://source.android.com/docs/security/bulletin) | Android + emulator fixes | Monthly | Monitor, evaluate |
| [AOSP external/qemu commits](https://android.googlesource.com/platform/external/qemu/) | Upstream commits | Continuous | Monthly sync |
| [NVD / CVE Database](https://www.cvedetails.com/vulnerability-list/vendor_id-7506/Qemu.html) | Public CVEs | As published | Monitor daily |

### 5.2 Patch Triage Process

```
+------------------+     +------------------+     +------------------+
| CVE Published    | --> | Evaluate Impact  | --> | Affected?        |
| (or bulletin)    |     | on LinBlock      |     |                  |
+------------------+     +------------------+     +--------+---------+
                                                          |
                                    +---------------------+---------------------+
                                    |                                           |
                                    v                                           v
                            +-------+--------+                          +-------+--------+
                            | YES            |                          | NO             |
                            | (Affected)     |                          | (Not affected) |
                            +-------+--------+                          +-------+--------+
                                    |                                           |
                          +---------+---------+                                 |
                          |                   |                                 |
                          v                   v                                 v
                   +------+------+     +------+------+                   +------+------+
                   | Critical/   |     | Medium/Low  |                   | Document &  |
                   | High        |     |             |                   | Close       |
                   +------+------+     +------+------+                   +-------------+
                          |                   |
                          v                   v
                   +------+------+     +------+------+
                   | Emergency   |     | Next regular|
                   | release     |     | release     |
                   | (< 72 hours)|     | (< 30 days) |
                   +-------------+     +-------------+
```

### 5.3 Backporting Strategy

Since LinBlock will diverge from upstream, security patches must be backported:

1. **Isolate security-relevant commits** from upstream
2. **Cherry-pick** onto LinBlock's fork
3. **Test** in CI with existing test suite + specific regression test for the vulnerability
4. **Review** by Agent 005 (Security) before merge
5. **Document** in `SECURITY_PATCHES.md` with CVE references

### 5.4 Fork Maintenance Burden

**Estimated ongoing effort:**

| Task | Frequency | Effort |
|------|-----------|--------|
| Monitor security sources | Daily | 15 min |
| Monthly upstream sync | Monthly | 4-8 hours |
| Security patch backport | As needed | 2-8 hours per patch |
| Regression testing | Per patch | 1-2 hours |
| Security review | Per release | 4-8 hours |

**Total: ~16-32 hours/month** for security maintenance alone.

---

## 6. Host Permissions Analysis

### 6.1 Required Permissions

| Permission | Reason | Risk | Mitigation |
|------------|--------|------|------------|
| `/dev/kvm` (rw) | Hardware virtualization | VM escape via KVM exploit | Unprivileged user, seccomp filter on ioctls |
| `/dev/dri/renderD*` (rw) | GPU rendering | GPU driver exploit | Render node only (not master), separate renderer process |
| `/dev/net/tun` (rw) | TAP networking | Network traffic manipulation | User-mode networking preferred, namespace isolation |
| `CAP_NET_ADMIN` | TAP interface setup | Network configuration abuse | Drop immediately after setup |
| Disk image files (rw) | Guest storage | Data access | Restricted to LinBlock data directory |
| Shared memory (rw) | Framebuffer, guest communication | Memory corruption | Strict size limits, separate mmap region |

### 6.2 Permissions to NEVER Grant

| Permission | Reason |
|------------|--------|
| `CAP_SYS_ADMIN` | Too broad, enables many attacks |
| `CAP_SYS_RAWIO` | Direct I/O port access |
| `CAP_SYS_MODULE` | Kernel module loading |
| `CAP_SYS_PTRACE` | Process debugging |
| `/dev/mem` or `/dev/kmem` | Direct memory access |
| `/dev/dri/card*` | GPU master node (modesetting) |
| Root (UID 0) | Never run emulator as root |

### 6.3 Permission Setup Sequence

```python
def secure_emulator_startup():
    # 1. Start as regular user (not root)
    assert os.getuid() != 0, "Never run as root"

    # 2. Create namespaces BEFORE acquiring any capabilities
    unshare(CLONE_NEWUSER | CLONE_NEWNS | CLONE_NEWIPC | CLONE_NEWPID)

    # 3. Set up user namespace mapping
    write_uid_map(inside=0, outside=os.getuid(), count=1)

    # 4. Mount private /dev with only required nodes
    mount("tmpfs", "/dev", "tmpfs", MS_NOSUID | MS_NOEXEC)
    mknod("/dev/kvm", S_IFCHR | 0666, makedev(10, 232))
    mknod("/dev/dri/renderD128", S_IFCHR | 0666, get_render_node())

    # 5. Apply cgroup limits
    apply_cgroup_limits()

    # 6. Apply seccomp filter LAST (locks down the process)
    apply_seccomp_filter()

    # 7. Drop all capabilities
    cap_clear(CAP_ALL)

    # 8. Now safe to initialize emulator
    emulator_main()
```

---

## 7. Security Recommendations

### 7.1 MUST DO (Blocking)

These items MUST be completed before any release:

| ID | Requirement | Rationale |
|----|-------------|-----------|
| S001 | Run emulator as unprivileged user | Basic process isolation |
| S002 | Apply seccomp-bpf filter | Reduce kernel attack surface |
| S003 | Use mount namespace with private /dev | Limit device access |
| S004 | Fuzz libOpenglRender command parser | Find memory corruption bugs |
| S005 | Validate shader complexity before compilation | Prevent GPU DoS |
| S006 | Apply cgroup resource limits | Prevent resource exhaustion |
| S007 | Pin upstream commits by hash | Supply chain integrity |
| S008 | Document security update process | Ensure patches are applied |

### 7.2 SHOULD DO (Highly Recommended)

| ID | Requirement | Rationale |
|----|-------------|-----------|
| S009 | Run GPU renderer in separate process | Isolate GPU attack surface |
| S010 | Implement network namespace | Full network isolation |
| S011 | Use AppArmor profile | Defense in depth |
| S012 | Enable ASLR/PIE/RELRO | Exploit mitigations |
| S013 | Run continuous fuzzing in CI | Ongoing vulnerability discovery |
| S014 | Implement reproducible builds | Supply chain verification |

### 7.3 CONSIDER (Nice to Have)

| ID | Requirement | Rationale |
|----|-------------|-----------|
| S015 | Use SwiftShader for untrusted apps | Eliminate GPU driver attack surface |
| S016 | Implement fine-grained seccomp per device | Minimal syscall set per component |
| S017 | Consider MicroVM architecture (Firecracker-style) | Minimal VMM attack surface |

---

## 8. Security Concerns That Could Block This Approach

### 8.1 Critical Blockers

1. **No seccomp support in fork:** If the Android Emulator codebase cannot be modified to support seccomp, this is a **blocker**. LinBlock must have syscall filtering.

2. **Unfixable GPU translation vulnerabilities:** If fuzzing reveals systemic vulnerabilities in libOpenglRender that cannot be fixed, LinBlock should consider:
   - Software rendering only (SwiftShader)
   - virgl instead of libOpenglRender
   - Not forking (use raw QEMU + virgl)

3. **Upstream abandonment:** If Google abandons the AOSP emulator (e.g., fully moves to Cuttlefish/CrosVM), the maintenance burden becomes untenable.

### 8.2 High Concerns (Not Blocking, But Require Attention)

1. **Binary blob dependencies:** If libOpenglRender requires closed-source GPU libraries (e.g., proprietary OpenGL implementations), this conflicts with LinBlock's auditable security posture.

2. **Telemetry/analytics code:** The Android Emulator may include analytics that must be identified and removed.

3. **License compatibility:** Verify that all forked code is compatible with LinBlock's license (Apache 2.0, GPL, etc.).

---

## 9. Comparison: Fork Android Emulator vs. Continue with Raw QEMU

| Aspect | Raw QEMU + virgl | Android Emulator Fork |
|--------|------------------|----------------------|
| Android compatibility | Good (requires tuning) | Excellent |
| GPU acceleration | virgl (good, upstream) | libOpenglRender (excellent, but larger attack surface) |
| Attack surface | Smaller | Larger (+36% LOC) |
| Maintenance burden | Lower (upstream) | Higher (fork) |
| Security patches | Upstream QEMU | QEMU + Android Emulator + LinBlock |
| Built-in sandboxing | None (same) | None (same) |
| Long-term viability | Excellent | Depends on Google |

**Verdict:** The Android Emulator fork is justified IF:
1. LinBlock implements all MUST DO security requirements
2. The team commits to ongoing maintenance burden
3. Android compatibility is a higher priority than minimizing attack surface

---

## 10. Revision History

| Date | Author | Change |
|------|--------|--------|
| 2026-01-29 | Agent 005 | Initial security evaluation |

---

## References

- [QEMU Security Documentation](https://qemu-project.gitlab.io/qemu/system/security.html)
- [QEMU CVE List](https://www.cvedetails.com/vulnerability-list/vendor_id-7506/Qemu.html)
- [Black Hat: Guest-to-Host Escape on QEMU/KVM Virtio Device](https://i.blackhat.com/asia-20/Thursday/asia-20-Shao-3D-Red-Pill-A-Guest-To-Host-Escape-On-QEMUKVM-Virtio-Device.pdf)
- [libvirt QEMU Security](https://libvirt.org/kbase/qemu-passthrough-security.html)
- [Google nsjail](https://github.com/google/nsjail)
- [Android Security Bulletins](https://source.android.com/docs/security/bulletin)
- [Android Emulator AOSP Repository](https://android.googlesource.com/platform/external/qemu/)
- [Eshard: Android Graphical Stack Virtualization](https://www.eshard.com/posts/Android-graphical-stack-virtualization)
