# LinBlock Threat Model

**Document Owner:** Agent 005 (Security)
**Last Updated:** 2026-01-28
**Status:** Phase A -- Planning

---

## 1. System Overview

LinBlock runs an Android guest operating system inside a KVM virtual machine on a Linux host. The host application (written in Python with GTK) manages the VM lifecycle, translates input, renders display output, and enforces security policies. The guest runs a custom AOSP build with a LinBlock system service that communicates with the host.

### Trust Boundaries

```
+------------------------------------------------------------------+
|                         HOST (Trusted)                           |
|                                                                  |
|  +-------------------+    +------------------+    +------------+ |
|  | LinBlock GUI      |    | Permission       |    | Storage    | |
|  | (GTK Application) |    | Manager          |    | Manager    | |
|  +--------+----------+    +--------+---------+    +------+-----+ |
|           |                        |                      |      |
|  +--------+------------------------+----------------------+----+ |
|  |                  Emulator Core (KVM)                        | |
|  |  +-----------+  +-----------+  +-----------+  +-----------+ | |
|  |  | virtio-   |  | virtio-   |  | virtio-   |  | virtio-   | | |
|  |  | gpu       |  | input     |  | net       |  | blk       | | |
|  |  +-----------+  +-----------+  +-----------+  +-----------+ | |
|  +==========================+==================================+ |
|  |     TRUST BOUNDARY       |  /dev/kvm  (Hardware enforced)   | |
|  +==========================+==================================+ |
|  |                  GUEST (Untrusted)                          | |
|  |  +------------------+  +------------------+                 | |
|  |  | Android OS       |  | LinBlock System  |                 | |
|  |  | (Custom AOSP)    |  | Service          |                 | |
|  |  +------------------+  +------------------+                 | |
|  |  +------------------+  +------------------+                 | |
|  |  | User Apps        |  | System Apps      |                 | |
|  |  | (UNTRUSTED)      |  | (Semi-trusted)   |                 | |
|  |  +------------------+  +------------------+                 | |
|  +-------------------------------------------------------------+ |
+------------------------------------------------------------------+
```

### Trust Levels

| Level | Domain                  | Trust   | Rationale                                         |
|-------|-------------------------|---------|---------------------------------------------------|
| T1    | Host kernel + KVM       | Trusted | Maintained by OS vendor, hardware-enforced isolation |
| T2    | LinBlock host app       | Trusted | Our code, runs with user privileges on host        |
| T3    | LinBlock system service | Semi-trusted | Our code running inside the guest               |
| T4    | Android system services | Semi-trusted | Stock AOSP, well-audited but complex            |
| T5    | User-installed apps     | Untrusted | Arbitrary third-party code                       |

---

## 2. Attack Surface Analysis

### 2.1 Host-Guest Boundary (KVM + Virtio Devices)

**Components:** `/dev/kvm` ioctls, virtio-gpu, virtio-blk, virtio-net, virtio-input, shared memory regions.

**Attack vectors:**

- **VM escape via KVM exploit:** A vulnerability in the KVM kernel module could allow guest code to execute on the host. This is the highest-impact attack.
- **Virtio device handler bugs:** The host-side virtio device implementations process data from the untrusted guest. Buffer overflows, integer overflows, or logic errors in the host device handlers could be exploited.
- **Shared memory corruption:** If guest-accessible memory regions overlap with host data structures due to misconfiguration of `KVM_SET_USER_MEMORY_REGION`, the guest could read or write host memory.
- **MMIO/PIO handler confusion:** Incorrect dispatch of I/O exits could route guest data to the wrong device handler or bypass validation.

**Severity:** Critical

### 2.2 ADB Bridge

**Components:** ADB server on guest, ADB client connection from host, command forwarding.

**Attack vectors:**

- **Command injection:** If the host constructs ADB commands using unsanitized input (e.g., app package names), a malicious app name could inject shell commands.
- **Unauthorized ADB access:** If ADB is exposed on a network port (TCP mode), other processes on the host or the local network could send commands to the guest.
- **ADB as a privilege escalation vector:** ADB shell runs as the `shell` user but can escalate to `root` on debug builds. The LinBlock guest must never be a debug build in production.

**Severity:** High

### 2.3 Shared Storage

**Components:** QCOW2 disk images, overlay images, snapshot files, host filesystem paths.

**Attack vectors:**

- **Path traversal:** If the guest can influence file paths used by the storage manager (e.g., via crafted filenames in shared directories), it might read or write files outside the intended storage directory.
- **Image file corruption:** A malicious guest could write crafted data to the virtio-blk device that, when interpreted as QCOW2 metadata by the host, triggers a vulnerability in the QCOW2 parser.
- **Data exfiltration:** If the guest has access to a shared folder, a malicious app could copy sensitive host files into the guest and exfiltrate them via the network.
- **Snapshot manipulation:** If snapshot metadata is stored in a guest-accessible location, a compromised guest could alter snapshot data.

**Severity:** High

### 2.4 Network Bridge

**Components:** TAP/TUN interface, NAT rules, virtio-net device, DNS configuration.

**Attack vectors:**

- **Traffic sniffing:** If the TAP interface is bridged to the host's physical network (rather than NATed), the guest can see other hosts' traffic.
- **Unauthorized outbound connections:** A malicious app could establish C2 connections, exfiltrate data, or participate in botnets.
- **DNS rebinding:** A malicious app could use DNS rebinding to access host-local services (e.g., localhost:8080).
- **ARP spoofing:** In bridged mode, the guest could ARP-spoof the host or other network devices.
- **Resource exhaustion:** The guest could flood the network, consuming host bandwidth and degrading host network performance.

**Severity:** High

### 2.5 GPU Passthrough

**Components:** virtio-gpu, virgl renderer, DRM/DRI device access, shader compilation.

**Attack vectors:**

- **Malicious shaders:** If virgl or GPU passthrough is used, a malicious app could submit crafted shaders that exploit GPU driver vulnerabilities, potentially causing host GPU hangs or memory corruption.
- **GPU memory leaks:** The guest could allocate GPU memory and never release it, exhausting host GPU resources.
- **DRI device access:** If `/dev/dri` is passed through to the guest without proper filtering, the guest might access host GPU resources directly.

**Severity:** Medium

---

## 3. Threat Actors

| Actor                  | Capability  | Motivation                                      | Examples                              |
|------------------------|-------------|--------------------------------------------------|---------------------------------------|
| Malicious Android app  | Medium      | Data theft, crypto mining, botnet participation  | Trojanized APK, fake utility app      |
| Compromised APK        | Medium      | Supply chain attack, backdoor installation       | Modified open-source app, repackaged popular app |
| Network attacker       | Medium-High | Intercept data, MITM, exploit services           | Attacker on same WiFi, compromised router |
| Curious/naive user     | Low         | Accidental misconfiguration, disabling security  | Granting all permissions, disabling SELinux |

---

## 4. STRIDE Analysis

### 4.1 emulator_core

| Threat Category         | Threat                                                              | Risk   | Mitigation                                                                                              |
|-------------------------|---------------------------------------------------------------------|--------|----------------------------------------------------------------------------------------------------------|
| **Spoofing**            | VM escape: guest code executes as host process                      | High   | Keep host kernel updated. Minimize KVM ioctl surface. Seccomp-bpf filter on emulator process.            |
| **Tampering**           | Guest corrupts host memory via misconfigured memory regions         | High   | Validate all `KVM_SET_USER_MEMORY_REGION` calls. Never map host data structures into guest-accessible memory. Fuzz virtio device handlers. |
| **Repudiation**         | No record of VM lifecycle events                                    | Low    | Log all VM create/start/stop/destroy events with timestamps to the audit log.                            |
| **Info. Disclosure**    | Guest reads host memory via side-channel (Spectre/Meltdown)        | Medium | Enable kernel mitigations (KPTI, retpoline). Pin guest to specific CPU cores if needed.                  |
| **Denial of Service**   | Guest consumes all host CPU/RAM, starving host applications        | Medium | Enforce cgroup limits on the emulator process (CPU quota, memory limit). Use KVM `KVM_CAP_NR_VCPUS` limits. |
| **Elevation of Priv.**  | KVM vulnerability allows guest-to-host privilege escalation        | High   | Run emulator as unprivileged user. AppArmor profile. Seccomp filter. Monitor CVEs for KVM.               |

### 4.2 permission_manager

| Threat Category         | Threat                                                              | Risk   | Mitigation                                                                                              |
|-------------------------|---------------------------------------------------------------------|--------|----------------------------------------------------------------------------------------------------------|
| **Spoofing**            | App bypasses permission check by spoofing its UID/package name      | Medium | Verify permissions using kernel-level UID, not self-reported package name. SELinux domain enforcement.    |
| **Tampering**           | App modifies its own permission state in the database               | Medium | Permission database is on the host, inaccessible from the guest. All writes go through the host API.     |
| **Repudiation**         | Permission changes occur with no audit trail                        | High   | Every permission query, grant, and denial is logged to an append-only audit log with timestamps.          |
| **Info. Disclosure**    | App discovers which permissions other apps hold                     | Low    | Permission queries are scoped to the calling app's UID. Cross-app queries require system privilege.       |
| **Denial of Service**   | App floods the permission manager with requests                     | Low    | Rate-limit permission check API. Cache recent decisions.                                                  |
| **Elevation of Priv.**  | App obtains system-level permissions (e.g., INSTALL_PACKAGES)       | High   | System permissions are never grantable via the UI. Hardcoded deny list. SELinux policy prevents access.   |

### 4.3 network_manager

| Threat Category         | Threat                                                              | Risk   | Mitigation                                                                                              |
|-------------------------|---------------------------------------------------------------------|--------|----------------------------------------------------------------------------------------------------------|
| **Spoofing**            | Guest spoofs its MAC address to bypass network rules                | Low    | MAC address is set by the host and cannot be changed by the guest (virtio-net configuration).             |
| **Tampering**           | Guest modifies NAT rules on the host                                | Low    | Guest has no access to host iptables. NAT rules are managed by the host process only.                    |
| **Repudiation**         | Network connections made by apps are not logged                     | Medium | Log all outbound connection attempts with source app UID, destination IP, port, and timestamp.            |
| **Info. Disclosure**    | Traffic between guest and host is captured by another host process  | Medium | Use a dedicated TAP interface. Consider encrypting virtio-net traffic (low priority for localhost).       |
| **Denial of Service**   | Guest floods the network, saturating host bandwidth                 | High   | Apply traffic shaping (tc) on the TAP interface. Per-app bandwidth limits enforced in the guest.         |
| **Elevation of Priv.**  | Guest accesses host-only network services (e.g., Docker API)        | Medium | Firewall rules block guest access to host loopback and sensitive ports. Default-deny for host services.   |

### 4.4 storage_manager

| Threat Category         | Threat                                                              | Risk   | Mitigation                                                                                              |
|-------------------------|---------------------------------------------------------------------|--------|----------------------------------------------------------------------------------------------------------|
| **Spoofing**            | Guest presents a fake disk image to the host                        | Low    | Disk images are created and managed by the host only. The guest cannot replace its own disk image.        |
| **Tampering**           | Malicious app modifies other apps' data in `/data`                  | Medium | Android's per-app directory isolation (enforced by SELinux and Unix permissions). dm-verity on `/system`. |
| **Repudiation**         | File modifications occur with no record                             | Low    | Snapshot diffs can be used for forensic analysis. Critical file access logged by audit subsystem.         |
| **Info. Disclosure**    | App reads another app's private data                                | Medium | SELinux enforces per-app file access. Scoped storage (Android 11+) limits file visibility.                |
| **Denial of Service**   | App fills the disk, preventing other apps from writing              | Medium | Per-app storage quotas. Disk usage monitoring with alerts.                                                |
| **Elevation of Priv.**  | App gains write access to `/system` partition                       | High   | `/system` mounted read-only with dm-verity. Remount requires root, which is blocked by SELinux.          |

---

## 5. Data Flow Diagram

```
                    EXTERNAL NETWORK
                         |
                    [NAT / Firewall]          <-- Trust Boundary: Host Network
                         |
+------------------------+---------------------------------------------------+
|  HOST                  |                                                   |
|                   [TAP Interface]                                          |
|                        |                                                   |
|  +-----------+    +----+------+    +---------------+    +--------------+   |
|  | GTK GUI   |--->| Emulator  |--->| virtio-net    |--->|              |   |
|  |           |    | Core      |    +---------------+    |              |   |
|  |  Display <-+---|           |                         |   KVM VM     |   |
|  |  Input   --+-->|           |--->| virtio-input  |--->|              |   |
|  +-----------+    |           |    +---------------+    |              |   |
|                   |           |                         |              |   |
|  +-----------+    |           |--->| virtio-gpu    |--->|              |   |
|  | Permission|--->|           |    +---------------+    |              |   |
|  | Manager   |    |           |                         |              |   |
|  +-----------+    |           |--->| virtio-blk    |--->|              |   |
|                   |           |    +---------------+    |              |   |
|  +-----------+    |           |                         |              |   |
|  | Storage   |--->|           |    +---------------+    |              |   |
|  | Manager   |    |           |--->| serial/UART   |--->|              |   |
|  +-----------+    +-----------+    +---------------+    |              |   |
|                                                         |              |   |
|  +-----------+         ADB (localhost:5555)              |              |   |
|  | Audit Log |<-----------------------------------------|              |   |
|  +-----------+                                          +--------------+   |
|                                                                            |
|  [QCOW2 Images]  [Permission DB]  [Config Files]  [Audit Logs]           |
|                                                                            |
+============================================================================+
|                    TRUST BOUNDARY (KVM Hardware Isolation)                  |
+============================================================================+
|  GUEST (Android)                                                           |
|                                                                            |
|  +-----------------+  +------------------+  +--------------------------+   |
|  | Android Runtime |  | LinBlock System  |  | SELinux Enforcing        |   |
|  | (ART + Zygote)  |  | Service          |  | (MAC Policy)             |   |
|  +-----------------+  +------------------+  +--------------------------+   |
|                                                                            |
|  +-----------------+  +------------------+  +--------------------------+   |
|  | User App A      |  | User App B       |  | User App C               |   |
|  | (Untrusted)     |  | (Untrusted)      |  | (Untrusted)              |   |
|  +-----------------+  +------------------+  +--------------------------+   |
|                                                                            |
+----------------------------------------------------------------------------+
```

### Data flows across trust boundaries

| # | From             | To               | Data                        | Trust Boundary Crossed     | Controls                                |
|---|------------------|------------------|-----------------------------|----------------------------|-----------------------------------------|
| 1 | GTK GUI          | Emulator Core    | Input events                | None (same process)        | Input validation                        |
| 2 | Emulator Core    | KVM VM           | vCPU run, memory, I/O       | Host-Guest (hardware)      | KVM isolation, seccomp, AppArmor        |
| 3 | virtio-net       | Guest network    | Network packets             | Host-Guest                 | NAT, firewall, traffic shaping          |
| 4 | virtio-blk       | Guest filesystem | Block I/O                   | Host-Guest                 | Image file permissions, dm-verity       |
| 5 | Guest ADB        | Host ADB client  | Shell commands, file transfer| Guest-Host                 | ADB auth, localhost-only binding        |
| 6 | Guest apps       | External network | App traffic                 | Guest-Host-Network         | Per-app firewall, NAT, DNS filtering    |
| 7 | Permission Mgr   | Guest service    | Permission decisions        | Host-Guest                 | Authenticated IPC channel               |

---

## 6. Out of Scope

The following threats are explicitly out of scope for this threat model:

- **Physical attacks:** An attacker with physical access to the host machine (cold boot attacks, JTAG, evil maid).
- **Nation-state adversaries:** Advanced persistent threats with zero-day capabilities targeting KVM or the host kernel.
- **Supply chain attacks on the build toolchain:** Compromised compilers, build systems, or OS packages used to build LinBlock.
- **Side-channel attacks between VMs:** LinBlock runs a single guest; cross-VM side channels are not applicable.
- **Attacks on the host OS itself:** Kernel vulnerabilities, compromised system services, or malware on the host are outside our control.
- **Social engineering:** Tricking the user into granting dangerous permissions is addressed by the permission UI design, not the threat model.

---

## 7. Residual Risks

Even with all mitigations in place, the following residual risks remain:

1. **KVM zero-day:** A previously unknown vulnerability in KVM could allow VM escape. Mitigation is defense-in-depth (seccomp, AppArmor, unprivileged user) but cannot eliminate this risk.
2. **GPU driver vulnerabilities:** If GPU passthrough or virgl is used, host GPU driver bugs are outside our control.
3. **Performance vs. security trade-offs:** Some security measures (e.g., disabling speculative execution mitigations for performance) may be requested by users. We will not provide such options.

---

## Revision History

| Date       | Author    | Change                          |
|------------|-----------|---------------------------------|
| 2026-01-28 | Agent 005 | Initial threat model creation   |
