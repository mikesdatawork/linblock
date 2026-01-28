# SELinux Requirements

**Document Owner:** Agent 005 (Security)
**Last Updated:** 2026-01-28
**Status:** Phase A -- Planning

---

## 1. Overview

LinBlock enforces mandatory access control (MAC) at two levels:

1. **Guest-side (SELinux):** The custom AOSP build runs SELinux in enforcing mode with custom policy modules that align with LinBlock's permission manager.
2. **Host-side (AppArmor):** The Linux host confines the emulator process with an AppArmor profile that restricts file access, network access, and capability usage.

This document specifies the requirements for both layers.

---

## 2. Guest-Side SELinux Requirements

### 2.1 Enforcing Mode

- The guest Android OS MUST boot with SELinux in **enforcing** mode.
- There MUST be no mechanism for user-installed apps to switch SELinux to permissive mode.
- The LinBlock system service MUST NOT run in an unconfined domain.
- `setenforce 0` MUST be blocked by policy (even for root/shell users).
- The kernel command line MUST NOT contain `androidboot.selinux=permissive` or `selinux=0`.

### 2.2 App Domain Isolation

- Each user-installed app MUST run in the `untrusted_app` SELinux domain (or a more restrictive custom domain).
- Apps MUST NOT be able to:
  - Access another app's private data directory (`/data/data/<other_package>/`).
  - Read or write to `/system`, `/vendor`, or `/product` partitions.
  - Access raw block devices (`/dev/block/*`).
  - Load kernel modules.
  - Access `/proc/kcore`, `/proc/kallsyms`, or other sensitive proc entries.
  - Use `ptrace` on other processes.
  - Bind to privileged ports (< 1024).

### 2.3 Network Access Control

- Apps without the `INTERNET` permission MUST be denied network socket creation at the SELinux level (not just the Android permission framework).
- Policy rules:
  - `untrusted_app` domain: `neverallow` for `tcp_socket` and `udp_socket` unless the app's UID is in the network-allowed group.
  - Apps with network permission: allowed `tcp_socket`, `udp_socket`, `inet_stream_socket`.
  - No app may create `raw_socket` or `packet_socket` (required for network sniffing).
  - DNS resolution is proxied through a system service; direct DNS queries to external servers are blocked.

### 2.4 File Access Control

- `/system` partition: mounted read-only, protected by dm-verity. SELinux labels: `system_file`.
- `/data` partition: per-app directories labeled with app-specific SELinux contexts (`app_data_file` with per-UID MLS categories).
- `/sdcard` (shared storage): scoped storage rules enforced. Apps access shared storage only through the MediaProvider, which runs in a privileged domain.
- Temporary files: apps may write to their own cache directory only. Cross-app temp file access is denied.

### 2.5 Sensor and Hardware Access Control

- Camera (`/dev/video*`): accessible only to apps with `CAMERA` permission, enforced by both Android permission framework and SELinux device node labeling.
- Microphone (`/dev/snd/*`): accessible only to apps with `RECORD_AUDIO` permission.
- Location: no direct hardware access; location is provided by a system service that checks permissions before responding.
- USB devices: no USB passthrough from host to guest by default. If enabled, accessible only to system apps.

### 2.6 LinBlock System Service Domain

- The LinBlock system service (`com.linblock.system`) runs in a custom SELinux domain: `linblock_system`.
- Allowed operations for `linblock_system`:
  - Read and write to the LinBlock configuration directory.
  - Communicate with the host via a designated virtio-serial channel.
  - Query `PackageManager` and `ActivityManager` system services.
  - Read app permission state from the permission database.
  - Send signals to app processes (for freeze/unfreeze/kill).
- Denied operations for `linblock_system`:
  - Access user app data directories.
  - Modify SELinux policy.
  - Access raw network sockets.
  - Mount or unmount filesystems.

---

## 3. Host-Side Requirements

### 3.1 AppArmor Profile for Emulator Process

The LinBlock emulator process MUST run under an AppArmor profile that restricts its capabilities:

```
# /etc/apparmor.d/linblock-emulator (conceptual, not final syntax)

profile linblock-emulator {
    # File access
    /dev/kvm                          rw,    # KVM device
    /dev/dri/renderD*                  rw,    # GPU rendering (if enabled)
    /home/*/.local/share/linblock/**   rwk,   # LinBlock data directory
    /tmp/linblock-*                    rwk,   # Temporary files
    /usr/share/linblock/**             r,     # Application resources

    # Deny access to sensitive host paths
    deny /etc/shadow                   r,
    deny /etc/passwd                   r,
    deny /root/**                      rwx,
    deny /home/*/.ssh/**               rwx,
    deny /home/*/.gnupg/**             rwx,

    # Network
    network inet stream,                      # TCP for ADB forwarding
    network inet dgram,                       # UDP for DNS forwarding
    deny network raw,                         # No raw sockets

    # Capabilities
    capability net_admin,                     # For TAP interface setup
    deny capability sys_admin,
    deny capability sys_module,
    deny capability sys_rawio,

    # Signals
    signal send set=(term, kill) peer=linblock-emulator,
}
```

### 3.2 `/dev/kvm` Access Control

- The emulator process MUST access `/dev/kvm` as an unprivileged user (not root).
- The user MUST be a member of the `kvm` group (or equivalent, depending on distribution).
- File permissions on `/dev/kvm` MUST be `0660` owned by `root:kvm`.
- The installer MUST check and configure this as part of the setup process.

### 3.3 `/dev/dri` Isolation

- If GPU rendering is enabled, the emulator accesses `/dev/dri/renderD128` (or the appropriate render node).
- The render node provides unprivileged GPU access (no modesetting capability).
- The emulator MUST NOT access `/dev/dri/card*` (master DRM nodes) to prevent interference with the host display server.
- The AppArmor profile enforces this restriction.

### 3.4 Seccomp-BPF Filter

- The emulator process SHOULD apply a seccomp-BPF filter after initialization that restricts the allowed syscall set.
- Allowed syscalls include: `read`, `write`, `ioctl` (filtered to KVM ioctls), `mmap`, `munmap`, `close`, `open`/`openat` (filtered by path), `poll`, `epoll_*`, `futex`, `clock_gettime`, `sigaction`, `rt_sigprocmask`.
- Denied syscalls include: `execve` (after init), `fork`/`clone` (after thread creation), `mount`, `umount`, `reboot`, `kexec_load`, `init_module`, `ptrace`.

---

## 4. MAC Strategy

### 4.1 Deny-by-Default

- All app permissions default to **denied** until explicitly granted by the user through the LinBlock permission manager UI.
- This applies to both Android runtime permissions and SELinux-enforced access.
- Even after an app declares a permission in its manifest, the permission is not granted until the user approves it.

### 4.2 Allowlisting for System Services

- Core Android system services (e.g., `system_server`, `surfaceflinger`, `installd`, `vold`) run in their standard AOSP SELinux domains with the standard AOSP policy.
- The LinBlock system service is the only additional allowlisted service.
- No other third-party services may run in privileged domains.

### 4.3 Policy Update Mechanism

- SELinux policy modules can be updated by the LinBlock host application (via the system service) when the permission manager configuration changes.
- Policy updates are applied without rebooting the guest (using `semodule` or runtime policy reload).
- Policy updates are logged to the audit log.

---

## 5. Policy Module Structure

The SELinux policy is organized into modules that align with the LinBlock permission manager categories:

```
sepolicy/
  linblock_base.te          # Base policy: domain definitions, type declarations
  linblock_system.te        # LinBlock system service domain and permissions
  linblock_network.te       # Network access control rules
  linblock_storage.te       # Storage and file access rules
  linblock_sensors.te       # Camera, microphone, location access rules
  linblock_app_template.te  # Template for per-app domain generation
  file_contexts             # File labeling rules
  property_contexts         # System property labeling
  seapp_contexts            # App-to-domain mapping
```

### Module-to-Permission-Manager Alignment

| Permission Manager Category | SELinux Module          | Controls                                   |
|-----------------------------|-------------------------|--------------------------------------------|
| Critical                    | `linblock_sensors.te`   | Camera, microphone, location device access |
| Sensitive                   | `linblock_storage.te`, `linblock_network.te` | File access, network sockets |
| Restricted                  | `linblock_base.te`      | Background execution, overlay windows      |
| Normal                      | (default AOSP policy)   | Internet, vibrate, wake lock               |

---

## 6. Compliance and Auditing

- All SELinux denials (`avc: denied`) MUST be captured and forwarded to the host audit log.
- The host displays SELinux denial events in the Logs page of the GUI, with human-readable descriptions.
- A weekly compliance report can be generated showing:
  - Number of SELinux denials by app and by access type.
  - Apps running in unexpected domains.
  - Policy changes made during the period.

---

## Revision History

| Date       | Author    | Change                              |
|------------|-----------|-------------------------------------|
| 2026-01-28 | Agent 005 | Initial SELinux requirements doc    |
