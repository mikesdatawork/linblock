#!/bin/bash
# s022_create_phase2_android_os_doc.sh
# Creates docs/design/phase2_android_os_development.md

PROJECT_ROOT="/home/user/projects/linblock"

cat > "$PROJECT_ROOT/docs/design/phase2_android_os_development.md" << 'ENDOFFILE'
# Phase 2: Custom Android OS Development

Version: 1.0.0
Status: Draft
Last Updated: 2025-01-27

---

## 1. Overview

This document outlines Phase 2 of the LinBlock project: building a custom Android OS that embodies the security principles of GrapheneOS with the simplicity of LineageOS.

**Phase 2 begins only after Phase 1 (emulator) is complete and stable.**

The emulator must reliably boot stock AOSP images before custom OS development starts. This ensures any OS boot failures are OS issues, not emulator bugs.

### 1.1 Phase 2 Goals

By the end of Phase 2, LinBlock will have:

1. A custom minimal Android 14 x86_64 image
2. Zero bloatware (no Google services, no carrier apps)
3. System-level permission management hooks
4. App freeze/hibernate capability
5. Per-app network control foundation
6. Process visibility and control
7. Clean, auditable codebase

### 1.2 What LinBlock OS Is

LinBlock OS is:

- **Minimal**: Only essential system services
- **Transparent**: User sees all running processes
- **Controllable**: User manages all permissions
- **Private**: No telemetry, no tracking
- **Compatible**: Runs standard Android apps

LinBlock OS is NOT:

- A fork of GrapheneOS (different base, different goals)
- A fork of LineageOS (built from AOSP directly)
- A general-purpose mobile OS (emulator-only target)
- A secure phone OS (no hardware security features)

### 1.3 Security Model Position

```
Less Control                                          More Control
     |                                                      |
Stock Android --- LineageOS --- LinBlock OS --- GrapheneOS
     |                |              |               |
  Bloated        Cleaner        Minimal         Hardened
  Telemetry      No Google      User Control    Exploit Mitigations
  No Control     Basic Control  Full Control    Full Security
```

LinBlock OS sits between LineageOS and GrapheneOS:

- More control than LineageOS
- Less hardening than GrapheneOS
- Focused on permission management and transparency
- Not focused on exploit mitigation (emulator context)

---

## 2. Prerequisites

### 2.1 Phase 1 Completion

Before starting Phase 2, verify:

| Requirement | Verification |
|-------------|--------------|
| Emulator boots AOSP GSI | Boot to launcher, interact with UI |
| Display works at 30fps | Run frame rate counter |
| Input works correctly | Navigate UI, type text |
| Network functions | Browse web, ping hosts |
| Storage persists | Install app, restart, app remains |
| ADB connection works | `adb shell` succeeds |

Do not proceed until all boxes are checked.

### 2.2 Hardware Requirements

AOSP builds are resource-intensive:

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU cores | 4 | 8+ |
| RAM | 16GB | 32GB+ |
| Storage | 300GB | 500GB+ |
| Build time | 4-8 hours | 1-2 hours |

LinBlock host system has 12GB RAM. This is below minimum. Mitigation strategies:

1. Add 16GB swap space
2. Use `make -j4` instead of `-j8` (fewer parallel jobs)
3. Build overnight (accept longer times)
4. Consider remote build server

### 2.3 Storage Setup

AOSP source requires approximately 200GB. Use the large data partition:

```
/mnt/data/
├── aosp-source/          # 200GB - AOSP source tree
├── aosp-build/           # 100GB - Build output
├── linblock-images/      # Test images
└── ccache/               # 50GB - Compiler cache
```

Configure ccache to speed rebuilds:

```bash
export CCACHE_DIR=/mnt/data/ccache
export USE_CCACHE=1
ccache -M 50G
```

---

## 3. AOSP Source Setup

### 3.1 Install Build Dependencies

```bash
# Ubuntu 24.04 / Linux Mint 22.2
sudo apt install -y \
    git-core gnupg flex bison build-essential \
    zip curl zlib1g-dev libc6-dev-i386 \
    x11proto-core-dev libx11-dev \
    libgl1-mesa-dev libxml2-utils xsltproc unzip \
    fontconfig python3 python3-pip \
    openjdk-17-jdk \
    libncurses5 libncurses5-dev \
    libssl-dev bc lz4 \
    repo
```

### 3.2 Install Repo Tool

```bash
mkdir -p ~/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/bin/repo
chmod a+x ~/bin/repo
export PATH=~/bin:$PATH
```

Add to `.bashrc`:
```bash
export PATH=~/bin:$PATH
```

### 3.3 Initialize AOSP Source

```bash
cd /mnt/data/aosp-source

# Configure git identity
git config --global user.email "linblock@local"
git config --global user.name "LinBlock Build"

# Initialize repo with Android 14 branch
repo init -u https://android.googlesource.com/platform/manifest \
    -b android-14.0.0_r1 \
    --depth=1

# Sync source (takes several hours)
repo sync -c -j4 --no-tags --no-clone-bundle
```

**Note**: `--depth=1` creates a shallow clone. This saves significant disk space but limits git history access.

### 3.4 Verify Source

After sync completes:

```bash
cd /mnt/data/aosp-source

# Check key directories exist
ls -la build/
ls -la frameworks/
ls -la device/
ls -la kernel/

# Count files (should be millions)
find . -type f | wc -l
```

---

## 4. LinBlock Device Tree

### 4.1 Device Tree Structure

Create LinBlock's device configuration:

```
device/linblock/
├── x86_64/
│   ├── AndroidProducts.mk
│   ├── linblock_x86_64.mk
│   ├── BoardConfig.mk
│   ├── device.mk
│   ├── vendorsetup.sh
│   └── overlay/
│       └── frameworks/
│           └── base/
│               └── core/
│                   └── res/
│                       └── res/
│                           └── values/
│                               └── config.xml
└── common/
    ├── linblock.mk
    ├── permissions/
    │   └── linblock_permissions.xml
    └── apps/
        └── (LinBlock system apps)
```

### 4.2 AndroidProducts.mk

```makefile
# device/linblock/x86_64/AndroidProducts.mk

PRODUCT_MAKEFILES := \
    $(LOCAL_DIR)/linblock_x86_64.mk

COMMON_LUNCH_CHOICES := \
    linblock_x86_64-userdebug \
    linblock_x86_64-user \
    linblock_x86_64-eng
```

### 4.3 Main Product Makefile

```makefile
# device/linblock/x86_64/linblock_x86_64.mk

# Inherit from AOSP x86_64 base
$(call inherit-product, $(SRC_TARGET_DIR)/product/core_64_bit_only.mk)
$(call inherit-product, $(SRC_TARGET_DIR)/product/full_base.mk)

# Inherit LinBlock common configuration
$(call inherit-product, device/linblock/common/linblock.mk)

# Device identifiers
PRODUCT_NAME := linblock_x86_64
PRODUCT_DEVICE := x86_64
PRODUCT_BRAND := LinBlock
PRODUCT_MODEL := LinBlock Emulator
PRODUCT_MANUFACTURER := LinBlock

# Use AOSP emulator kernel
PRODUCT_COPY_FILES += \
    kernel/prebuilts/5.15/x86_64/kernel-5.15:kernel

# Build type
PRODUCT_BUILD_PROP_OVERRIDES += \
    PRODUCT_NAME=linblock_x86_64 \
    BUILD_FINGERPRINT=LinBlock/linblock_x86_64/x86_64:14/LinBlock/$(BUILD_ID):userdebug/dev-keys

# Enable ADB by default (development)
PRODUCT_PROPERTY_OVERRIDES += \
    ro.adb.secure=0 \
    persist.sys.usb.config=adb
```

### 4.4 LinBlock Common Configuration

```makefile
# device/linblock/common/linblock.mk

# ============================================
# LinBlock Minimal Android Configuration
# ============================================

# System properties
PRODUCT_PROPERTY_OVERRIDES += \
    ro.linblock.version=0.1.0 \
    ro.linblock.build_type=development \
    persist.sys.timezone=UTC

# ============================================
# INCLUDED: Essential System Components
# ============================================

PRODUCT_PACKAGES += \
    # Core UI
    SystemUI \
    Launcher3QuickStep \
    Settings \
    \
    # Essential services
    framework \
    services \
    \
    # File management
    DocumentsUI \
    \
    # Package management
    PackageInstaller \
    \
    # Basic connectivity
    WifiService \
    \
    # ADB support
    adbd \
    \
    # Shell utilities
    sh \
    toolbox \
    toybox

# ============================================
# EXCLUDED: Bloatware and Unnecessary Apps
# ============================================

# The following are explicitly NOT included:
#
# Google Services:
#   - GmsCore (Google Play Services)
#   - GoogleServicesFramework
#   - Phonesky (Play Store)
#   - GoogleLoginService
#
# Carrier Apps:
#   - CarrierConfig
#   - CarrierDefaultApp
#
# Telemetry:
#   - StatsCompanion
#   - Statsd
#
# Unused Features:
#   - PrintSpooler
#   - WallpaperCropper
#   - BasicDreams
#   - Calendar
#   - Email
#   - Music
#   - Camera (unless explicitly needed)

# ============================================
# LinBlock Custom Components
# ============================================

PRODUCT_PACKAGES += \
    # Permission manager (Phase 2 deliverable)
    LinBlockPermissionManager \
    \
    # App controller (Phase 2 deliverable)
    LinBlockAppController

# ============================================
# Permissions Configuration
# ============================================

PRODUCT_COPY_FILES += \
    device/linblock/common/permissions/linblock_permissions.xml:$(TARGET_COPY_OUT_SYSTEM)/etc/permissions/linblock_permissions.xml

# ============================================
# Overlays
# ============================================

DEVICE_PACKAGE_OVERLAYS += \
    device/linblock/x86_64/overlay
```

### 4.5 Board Configuration

```makefile
# device/linblock/x86_64/BoardConfig.mk

# CPU Architecture
TARGET_ARCH := x86_64
TARGET_ARCH_VARIANT := x86_64
TARGET_CPU_ABI := x86_64
TARGET_CPU_VARIANT := generic

TARGET_2ND_ARCH := x86
TARGET_2ND_ARCH_VARIANT := x86_64
TARGET_2ND_CPU_ABI := x86
TARGET_2ND_CPU_VARIANT := generic

# Kernel
BOARD_KERNEL_CMDLINE := console=ttyS0 androidboot.hardware=linblock

# Partitions
BOARD_SYSTEMIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_SYSTEMIMAGE_PARTITION_SIZE := 2147483648  # 2GB
BOARD_USERDATAIMAGE_PARTITION_SIZE := 4294967296  # 4GB
BOARD_VENDORIMAGE_FILE_SYSTEM_TYPE := ext4
BOARD_VENDORIMAGE_PARTITION_SIZE := 268435456  # 256MB

# Build system
BUILD_BROKEN_DUP_RULES := true

# SELinux
BOARD_SEPOLICY_DIRS += device/linblock/common/sepolicy
```

---

## 5. Minimal System Definition

### 5.1 System Services Analysis

Android includes hundreds of system services. LinBlock needs only a subset.

**Required Services** (system cannot function without):

| Service | Purpose |
|---------|---------|
| ActivityManagerService | App lifecycle |
| PackageManagerService | App installation |
| WindowManagerService | Window management |
| InputManagerService | Input routing |
| DisplayManagerService | Display management |
| PowerManagerService | Power state |
| BatteryService | Battery status |
| SurfaceFlinger | Graphics composition |
| ServiceManager | Service registry |
| Zygote | Process forking |

**Optional Services** (include for functionality):

| Service | Purpose | Include? |
|---------|---------|----------|
| ConnectivityService | Network management | Yes |
| WifiService | WiFi control | Yes |
| AudioService | Sound | Yes |
| NotificationManagerService | Notifications | Yes |
| AlarmManagerService | Timers | Yes |
| JobSchedulerService | Background jobs | Yes |
| StorageManagerService | Storage | Yes |

**Excluded Services** (bloatware):

| Service | Purpose | Exclude Reason |
|---------|---------|----------------|
| TelephonyRegistry | Cellular | No cellular in emulator |
| BluetoothManagerService | Bluetooth | Not needed |
| NfcService | NFC | Not needed |
| PrintService | Printing | Not needed |
| VrManagerService | VR | Not needed |
| SliceManagerService | Slices | Not needed |

### 5.2 System Apps Analysis

**Included Apps**:

| App | Package | Purpose |
|-----|---------|---------|
| System UI | com.android.systemui | Status bar, navigation |
| Launcher | com.android.launcher3 | Home screen |
| Settings | com.android.settings | System settings |
| Documents UI | com.android.documentsui | File access |
| Package Installer | com.android.packageinstaller | App installation |

**Excluded Apps**:

| App | Package | Exclude Reason |
|-----|---------|----------------|
| Calculator | com.android.calculator2 | User can install |
| Calendar | com.android.calendar | User can install |
| Camera | com.android.camera | Not needed |
| Clock | com.android.deskclock | User can install |
| Contacts | com.android.contacts | User can install |
| Dialer | com.android.dialer | No telephony |
| Email | com.android.email | User can install |
| Gallery | com.android.gallery3d | User can install |
| Music | com.android.music | User can install |

Total preinstalled apps: 5 (compared to 50+ in stock Android)

---

## 6. LinBlock Custom Components

### 6.1 Permission Manager

**Module**: `LinBlockPermissionManager`

**Purpose**: Intercept and control all permission requests at the system level.

**Architecture**:

```
App requests permission
         |
         v
+---------------------------+
| Android PermissionManager |
+---------------------------+
         |
         v
+---------------------------+
| LinBlock Permission Hook  |  <-- Intercepts here
+---------------------------+
         |
    +----+----+
    |         |
    v         v
 Granted   Prompt User
            (via UI)
```

**Implementation Approach**:

1. Create system service `LinBlockPermissionService`
2. Hook into `PermissionManagerService`
3. Intercept `checkPermission()` calls
4. Query LinBlock permission database
5. If "ask every time", trigger UI prompt
6. Log all permission checks

**Key Files**:

```
frameworks/base/services/core/java/com/android/server/pm/permission/
    LinBlockPermissionService.java      # New service
    PermissionManagerService.java       # Modified (hooks added)

packages/apps/LinBlockPermissionManager/
    src/
        LinBlockPermissionActivity.java  # Permission prompt UI
        PermissionDatabase.java          # Permission storage
        PermissionAuditLog.java          # Usage logging
```

**Data Model**:

```java
class PermissionRecord {
    String packageName;       // com.example.app
    String permission;        // android.permission.CAMERA
    PermissionState state;    // GRANTED, DENIED, ASK
    long grantTime;           // When granted
    long lastUsed;            // Last access time
    int useCount;             // Total access count
    boolean backgroundAllowed; // Background access
}
```

### 6.2 App Controller

**Module**: `LinBlockAppController`

**Purpose**: Enable/disable, freeze, and manage app execution.

**Capabilities**:

| Feature | Description |
|---------|-------------|
| Enable/Disable | Standard Android app disable |
| Freeze | Complete process stop via cgroups |
| Background Restrict | Prevent background execution |
| Network Control | Per-app firewall rules |
| Autostart Control | Prevent boot-time startup |

**Freeze Implementation**:

Uses cgroups v2 freezer:

```bash
# Freeze app
echo 1 > /sys/fs/cgroup/apps/{uid}/cgroup.freeze

# Unfreeze app
echo 0 > /sys/fs/cgroup/apps/{uid}/cgroup.freeze
```

**System Service**:

```java
// frameworks/base/services/core/java/com/android/server/linblock/
// LinBlockAppControlService.java

public class LinBlockAppControlService extends SystemService {
    
    public void freezeApp(String packageName) {
        int uid = getUidForPackage(packageName);
        writeCgroupFreeze(uid, true);
        mFrozenApps.add(packageName);
    }
    
    public void unfreezeApp(String packageName) {
        int uid = getUidForPackage(packageName);
        writeCgroupFreeze(uid, false);
        mFrozenApps.remove(packageName);
    }
    
    public void setBackgroundRestricted(String packageName, boolean restricted) {
        // Use AppOpsManager or ActivityManager
    }
    
    public void setNetworkAllowed(String packageName, boolean allowed) {
        // Configure iptables rules
    }
}
```

### 6.3 Process Monitor

**Module**: `LinBlockProcessMonitor`

**Purpose**: Provide visibility into all running processes and resource usage.

**Exposed Information**:

| Data | Source |
|------|--------|
| Running processes | `/proc` |
| CPU usage per process | `/proc/{pid}/stat` |
| Memory usage per process | `/proc/{pid}/statm` |
| Network usage per app | `NetworkStatsService` |
| Wake locks held | `PowerManagerService` |
| Scheduled jobs | `JobSchedulerService` |

**No Hidden Processes**:

Unlike stock Android, LinBlock exposes all processes to the user. System processes are visible. The user can see exactly what is running.

---

## 7. SELinux Policy

### 7.1 Policy Approach

LinBlock uses enforcing SELinux but with policies that allow user control:

- System services remain restricted
- LinBlock services have necessary permissions
- User-initiated actions are allowed
- Logging enabled for auditing

### 7.2 LinBlock SELinux Policy

```
# device/linblock/common/sepolicy/linblock_permission_service.te

type linblock_permission_service, domain;
type linblock_permission_service_exec, exec_type, file_type;

init_daemon_domain(linblock_permission_service)

# Allow reading permission database
allow linblock_permission_service linblock_data_file:file { read write create };

# Allow interacting with apps
allow linblock_permission_service appdomain:process { signal };

# Allow logging
allow linblock_permission_service linblock_audit_log:file { append };
```

### 7.3 File Contexts

```
# device/linblock/common/sepolicy/file_contexts

/system/bin/linblock_permission_service    u:object_r:linblock_permission_service_exec:s0
/data/linblock(/.*)?                       u:object_r:linblock_data_file:s0
/data/linblock/audit.log                   u:object_r:linblock_audit_log:s0
```

---

## 8. Build Process

### 8.1 Environment Setup

```bash
cd /mnt/data/aosp-source
source build/envsetup.sh
lunch linblock_x86_64-userdebug
```

### 8.2 Build Commands

**Full Build**:

```bash
# First build (takes hours)
make -j4 2>&1 | tee build.log
```

**Incremental Build** (after changes):

```bash
# Rebuild specific module
mmm frameworks/base/services
mmm packages/apps/LinBlockPermissionManager

# Rebuild system image
make systemimage -j4
```

### 8.3 Build Output

```
out/target/product/x86_64/
├── system.img           # Main system partition
├── vendor.img           # Vendor partition
├── boot.img             # Kernel + ramdisk
├── userdata.img         # Empty user data
├── recovery.img         # Recovery (optional)
├── system/              # Unpacked system files
│   ├── app/
│   ├── priv-app/
│   ├── framework/
│   └── bin/
└── obj/                 # Build intermediates
```

### 8.4 Build Verification

After build completes:

```bash
# Check image sizes
ls -lh out/target/product/x86_64/*.img

# Expected sizes:
# system.img    ~1.5GB (target <2GB)
# vendor.img    ~100MB
# boot.img      ~50MB

# Check for LinBlock components
unzip -l out/target/product/x86_64/system.img | grep linblock
```

---

## 9. Testing Strategy

### 9.1 Boot Testing

**First Boot Test**:

```bash
# Copy images to LinBlock emulator
cp out/target/product/x86_64/system.img /mnt/data/linblock-images/linblock/

# Boot with LinBlock emulator
linblock --image /mnt/data/linblock-images/linblock/system.img

# Expected: Boot to launcher within 30 seconds
```

**Boot Failure Debug**:

If boot fails:

1. Check serial console output
2. Look for kernel panic
3. Check for SELinux denials: `adb shell dmesg | grep avc`
4. Check system server crash: `adb logcat -b crash`

### 9.2 Component Testing

| Component | Test Method |
|-----------|-------------|
| Permission Manager | Grant/deny permissions, verify enforcement |
| App Controller | Freeze app, verify process stopped |
| Process Monitor | Compare with `ps` output |
| Network Control | Block app, verify no connectivity |

### 9.3 Compatibility Testing

Test with common F-Droid apps:

| App | Tests |
|-----|-------|
| F-Droid | Install, update apps |
| Simple Gallery | Storage permission |
| Simple Calendar | Calendar permission |
| Termux | Shell access |
| Firefox | Network, storage |

---

## 10. Development Stages

### 10.1 Stage 1: Minimal Boot

**Objective**: Boot custom AOSP with LinBlock branding only.

**Tasks**:

1. Set up AOSP source
2. Create device tree
3. Configure minimal packages
4. Build and boot
5. Verify boot to launcher

**Success Criteria**:

- Boots in LinBlock emulator
- Shows LinBlock branding
- Launcher functions
- Settings opens
- No crashes for 10 minutes

### 10.2 Stage 2: Permission Hooks

**Objective**: Implement permission interception.

**Tasks**:

1. Create LinBlockPermissionService
2. Hook PermissionManagerService
3. Create permission database
4. Implement basic grant/deny
5. Test with sample app

**Success Criteria**:

- App permission request intercepted
- Can grant from database
- Can deny from database
- Permission state persists

### 10.3 Stage 3: Permission UI

**Objective**: User interface for permission management.

**Tasks**:

1. Create permission prompt activity
2. Implement "ask every time" mode
3. Create permission settings page
4. Add audit log viewer
5. Integrate with Settings app

**Success Criteria**:

- Permission prompt appears
- User can grant/deny
- Settings shows all permissions
- Audit log records accesses

### 10.4 Stage 4: App Control

**Objective**: Enable, disable, freeze apps.

**Tasks**:

1. Create LinBlockAppControlService
2. Implement cgroup freezing
3. Create app control UI
4. Add background restriction
5. Test with multiple apps

**Success Criteria**:

- Can freeze app (process stops)
- Can unfreeze app (process resumes)
- Background restriction works
- State persists across reboot

### 10.5 Stage 5: Network Control

**Objective**: Per-app network firewall.

**Tasks**:

1. Implement iptables integration
2. Create network rules per UID
3. Add network UI to app control
4. Test connectivity blocking
5. Verify rules persist

**Success Criteria**:

- Can block app network
- App cannot connect when blocked
- Other apps unaffected
- Rules survive reboot

### 10.6 Stage 6: Process Visibility

**Objective**: Full process transparency.

**Tasks**:

1. Create process monitor service
2. Expose all processes via API
3. Create process viewer UI
4. Add resource usage display
5. Implement force stop

**Success Criteria**:

- All processes visible
- Resource usage accurate
- Can force stop any process
- UI updates in real-time

### 10.7 Stage 7: Polish and Documentation

**Objective**: Complete and document system.

**Tasks**:

1. Fix remaining bugs
2. Performance optimization
3. Complete documentation
4. Write user guide
5. Final testing pass

**Success Criteria**:

- No critical bugs
- Boot under 30s
- Memory under 2GB
- Docs complete

---

## 11. Timeline Estimate

| Stage | Duration | Cumulative |
|-------|----------|------------|
| Stage 1: Minimal Boot | 2-3 weeks | 3 weeks |
| Stage 2: Permission Hooks | 2-3 weeks | 6 weeks |
| Stage 3: Permission UI | 2 weeks | 8 weeks |
| Stage 4: App Control | 2 weeks | 10 weeks |
| Stage 5: Network Control | 2 weeks | 12 weeks |
| Stage 6: Process Visibility | 1-2 weeks | 14 weeks |
| Stage 7: Polish | 2 weeks | 16 weeks |

Total: approximately 4 months for Phase 2.

Combined with Phase 1 (3 months): **7 months total project duration**.

---

## 12. Deliverables

Phase 2 completion requires:

### 12.1 Code

- LinBlock device tree in AOSP
- LinBlockPermissionService
- LinBlockAppControlService
- LinBlockProcessMonitor
- Permission manager app
- App controller UI
- SELinux policies

### 12.2 Images

- `linblock-system.img` - System partition
- `linblock-vendor.img` - Vendor partition
- `linblock-boot.img` - Boot image
- Image builder script

### 12.3 Documentation

- Build instructions
- Architecture documentation
- API documentation
- User guide

---

## 13. Success Criteria Summary

Phase 2 is complete when:

1. Custom LinBlock OS boots in LinBlock emulator
2. System image under 2GB
3. Only 5 system apps installed
4. Permission manager intercepts all permission requests
5. "Ask every time" mode works
6. Permission audit log functions
7. App freeze/unfreeze works
8. Background restriction works
9. Per-app network control works
10. All processes visible to user
11. No Google services present
12. F-Droid and Aurora Store install and work
13. Documentation complete

---

## 14. Future Phases Preview

**Phase 3: Enhanced Security**

- Verified boot implementation
- Storage encryption
- App signature verification
- Enhanced sandboxing

**Phase 4: Usability**

- First-run wizard
- Backup/restore
- Theme customization
- Performance tuning

**Phase 5: Distribution**

- Release builds
- Update mechanism
- User community
- Documentation website
ENDOFFILE

echo "Created: $PROJECT_ROOT/docs/design/phase2_android_os_development.md"
