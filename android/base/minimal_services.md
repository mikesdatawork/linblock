# LinBlock Minimal Services Manifest

## Overview

LinBlock runs a minimal Android 14 system image with only the services required
for a functional app execution environment. Non-essential services, Google
proprietary services, and carrier-specific components are excluded to reduce
resource usage, improve boot time, and eliminate unnecessary dependencies.

## Service Categories

### Enabled Services (Required)

These services are essential for Android to boot and run applications:

| Service | Package/Component | Purpose |
|---------|------------------|---------|
| ServiceManager | `servicemanager` | Core IPC service registry |
| ActivityManagerService | `com.android.server` | Activity lifecycle, process management |
| PackageManagerService | `com.android.server` | App installation, package resolution |
| WindowManagerService | `com.android.server` | Window management, transitions |
| InputManagerService | `com.android.server` | Input event dispatch |
| SurfaceFlinger | `surfaceflinger` | Display composition, rendering |
| DisplayManagerService | `com.android.server` | Display configuration, resolution |
| PowerManagerService | `com.android.server` | Wake locks, power state |
| AlarmManagerService | `com.android.server` | Scheduled alarms, timers |
| StorageManagerService | `com.android.server` | Storage volumes, mount management |
| UserManagerService | `com.android.server` | User accounts (single user) |
| NetworkStack | `com.android.networkstack` | Network configuration |
| ConnectivityService | `com.android.server` | Network connectivity management |
| AudioService | `com.android.server` | Audio routing and management |
| ContentService | `com.android.server` | Content provider management |
| AccountManagerService | `com.android.server` | Account management (local only) |
| NotificationManagerService | `com.android.server` | Notification dispatch and display |
| JobSchedulerService | `com.android.server` | Background job scheduling |
| DevicePolicyManager | `com.android.server` | Device administration |
| ClipboardService | `com.android.server` | Clipboard operations |
| VibratorService | `com.android.server` | Vibration feedback (stub) |
| BatteryService | `com.android.server` | Battery state (always 100%, AC) |
| AccessibilityManager | `com.android.server` | Accessibility services |
| UriGrantsManagerService | `com.android.server` | URI permission grants |
| RoleManagerService | `com.android.server` | Default app roles |
| PermissionManagerService | `com.android.server` | Runtime permission management |

### Enabled System Apps (Required)

| App | Package | Purpose |
|-----|---------|---------|
| SystemUI | `com.android.systemui` | Status bar, navigation, quick settings |
| Launcher3 | `com.android.launcher3` | Home screen |
| Settings | `com.android.settings` | System settings |
| SettingsProvider | `com.android.providers.settings` | Settings database |
| DocumentsUI | `com.android.documentsui` | File picker / document access |
| Shell | `com.android.shell` | ADB shell |
| PackageInstaller | `com.android.packageinstaller` | APK installation UI |
| PermissionController | `com.android.permissioncontroller` | Permission grant UI |
| ContactsProvider | `com.android.providers.contacts` | Contacts database (for apps) |
| MediaProvider | `com.android.providers.media` | Media database (for storage access) |
| DownloadProvider | `com.android.providers.downloads` | Download management |
| CalendarProvider | `com.android.providers.calendar` | Calendar database (for apps) |
| ExternalStorageProvider | `com.android.externalstorage` | External storage access |
| CertInstaller | `com.android.certinstaller` | Certificate management |
| KeyChain | `com.android.keychain` | Key storage |
| InputDevices | `com.android.inputdevices` | Input method management |
| Traceur | `com.android.traceur` | System tracing (debug) |

### Disabled / Excluded Services

These services are explicitly excluded from the LinBlock system image:

#### Google Play Services (GMS)

| Component | Package | Reason for Exclusion |
|-----------|---------|---------------------|
| Google Play Services | `com.google.android.gms` | Proprietary; not required for basic functionality |
| Google Services Framework | `com.google.android.gsf` | GMS dependency |
| Google Play Store | `com.android.vending` | Proprietary app store |
| Google Account Manager | `com.google.android.gms.auth` | Google account dependency |
| Firebase Cloud Messaging | `com.google.android.gms.gcm` | Push notification (Google) |

**Impact of excluding GMS:**
- Apps depending on Google Play Services will show errors or reduced functionality
- No Google account login
- No Google Maps API (apps can use alternative map providers)
- No Google Play Store (use APK sideloading or F-Droid)
- No Firebase push notifications
- SafetyNet / Play Integrity checks will fail

**Mitigation:** Users may optionally install microG (open-source GMS replacement)
for basic GMS API compatibility.

#### Carrier Services

| Component | Package | Reason for Exclusion |
|-----------|---------|---------------------|
| Carrier Services | `com.google.android.ims` | No cellular connectivity |
| Carrier Setup | `com.android.carrierconfig` | No SIM card |
| Phone | `com.android.phone` | No telephony |
| Dialer | `com.android.dialer` | No telephony |
| Messaging | `com.android.messaging` | No SMS capability |
| Stk (SIM Toolkit) | `com.android.stk` | No SIM card |
| IMS Service | `com.android.ims` | No IMS/VoLTE |

#### OEM / Vendor Customization

| Component | Reason for Exclusion |
|-----------|---------------------|
| OEM Setup Wizard | Not needed; emulator starts directly |
| Vendor bloatware | Not applicable |
| Custom launchers | Using stock Launcher3 |
| Vendor analytics | Privacy; not needed |

#### Telemetry and Advertising

| Component | Reason for Exclusion |
|-----------|---------------------|
| Usage Stats (Google) | Privacy |
| Ad Services | Not needed in emulator |
| Analytics frameworks | Privacy |
| Crash reporting (Google) | Not needed |

#### Setup and Onboarding

| Component | Package | Reason for Exclusion |
|-----------|---------|---------------------|
| SetupWizard | `com.google.android.setupwizard` | Not needed; direct boot to home |
| Android Setup | `com.android.provision` | Replaced by minimal provisioning |
| Welcome screen | N/A | Not needed |

### Stubbed Services

These services must exist for API compatibility but return minimal/default responses:

#### TelephonyManager (Stubbed)

```java
// Stub behavior:
getSimState() -> SIM_STATE_ABSENT
getNetworkOperatorName() -> ""
getPhoneType() -> PHONE_TYPE_NONE
getDataState() -> DATA_DISCONNECTED
getCallState() -> CALL_STATE_IDLE
getLine1Number() -> null
getSubscriberId() -> null
```

**Implementation:** LinBlock provides a minimal TelephonyManager stub that
returns "no SIM" state for all queries. This prevents apps from crashing
when they query telephony state.

#### BluetoothManager (Stubbed - Optional)

```java
// Stub behavior:
getAdapter() -> null (or disabled adapter)
isEnabled() -> false
getState() -> STATE_OFF
```

**Implementation:** Returns Bluetooth as unavailable. Can optionally be
omitted entirely if the BluetoothManager service is not started.

#### WifiManager (Partially Stubbed)

```java
// Stub behavior:
isWifiEnabled() -> true
getConnectionInfo() -> WifiInfo(SSID="LinBlock-Virtual", linkSpeed=100)
getDhcpInfo() -> DhcpInfo(ipAddress=10.0.2.15, gateway=10.0.2.2)
```

**Implementation:** Reports WiFi as connected via the virtio-net bridge.
Network traffic flows through virtio-net to the host's NAT.

#### LocationManager (Stubbed)

```java
// Stub behavior:
getLastKnownLocation() -> Location(lat=37.4220, lng=-122.0841)  // Configurable
isProviderEnabled(GPS_PROVIDER) -> false
isProviderEnabled(NETWORK_PROVIDER) -> true
```

**Implementation:** Returns a configurable fixed location. GPS provider is
disabled; network provider returns the configured location.

## Boot Sequence

The minimal services boot in the following order:

```
1. Kernel boot
2. init (first process)
3. servicemanager
4. surfaceflinger
5. zygote (app process spawner)
6. system_server
   a. ActivityManagerService
   b. PowerManagerService
   c. PackageManagerService
   d. DisplayManagerService
   e. WindowManagerService
   f. InputManagerService
   g. ... (remaining system services)
7. SystemUI
8. Launcher3 (home screen)
```

**Target boot time:** Under 30 seconds from VM start to home screen displayed.

## Resource Impact

### Comparison with Full Android

| Metric | Full Android + GMS | LinBlock Minimal |
|--------|-------------------|-----------------|
| System image size | ~4-6 GB | ~2 GB |
| Boot time | 45-90 seconds | 15-30 seconds |
| Idle RAM usage | ~2-3 GB | ~800 MB - 1.2 GB |
| Running processes | 80-120 | 30-50 |
| Background services | 30-50 | 10-15 |

### Process Count Breakdown (Idle)

| Category | Count | Examples |
|----------|-------|---------|
| System core | 8 | init, zygote, servicemanager, surfaceflinger, etc. |
| System server | 1 | system_server (hosts most system services) |
| System apps | 5-8 | SystemUI, Launcher, Settings, etc. |
| Kernel threads | 15-20 | kworker, kswapd, etc. |
| **Total** | **~30-40** | |

## Configuration Files

### Disabled packages list

File: `overlay/etc/linblock-disabled-packages.txt`
```
com.google.android.gms
com.google.android.gsf
com.android.vending
com.google.android.setupwizard
com.android.phone
com.android.dialer
com.android.messaging
com.android.stk
com.android.carrierconfig
```

### System properties for minimal mode

File: `overlay/system/build.prop` (appended)
```properties
# LinBlock minimal mode
ro.setupwizard.mode=DISABLED
ro.config.notification_sound=
ro.config.alarm_alert=
ro.com.google.gmsversion=
persist.sys.strictmode.disable=1
```
