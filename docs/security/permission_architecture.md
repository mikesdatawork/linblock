# Permission Architecture

**Document Owner:** Agent 005 (Security)
**Last Updated:** 2026-01-28
**Status:** Phase A -- Planning

---

## 1. Overview

The LinBlock permission architecture provides the host user with fine-grained, per-app control over every Android permission. Unlike stock Android, where permissions are managed on-device, LinBlock's permission decisions originate from the host application and are enforced both at the Android framework level and the SELinux policy level.

---

## 2. Permission Categories

All Android permissions are classified into four categories based on their sensitivity and default behavior.

### 2.1 Critical (Always Prompt)

These permissions provide access to the most sensitive data and sensors. The user is prompted every time an app requests access, regardless of prior decisions, unless the user explicitly sets the permission to "always allow."

| Permission               | Android Equivalent                    | Rationale                                      |
|--------------------------|---------------------------------------|------------------------------------------------|
| Camera                   | `android.permission.CAMERA`           | Visual surveillance risk                       |
| Microphone               | `android.permission.RECORD_AUDIO`     | Audio surveillance risk                        |
| Fine Location            | `android.permission.ACCESS_FINE_LOCATION` | Precise physical location tracking         |
| Coarse Location          | `android.permission.ACCESS_COARSE_LOCATION` | Approximate location tracking            |
| Contacts (Read)          | `android.permission.READ_CONTACTS`    | Personal relationship data                     |
| Contacts (Write)         | `android.permission.WRITE_CONTACTS`   | Data integrity risk                            |
| Call Logs (Read)         | `android.permission.READ_CALL_LOG`    | Communication metadata                         |
| Call Logs (Write)        | `android.permission.WRITE_CALL_LOG`   | Data integrity risk                            |
| SMS (Read)               | `android.permission.READ_SMS`         | Authentication token interception              |
| SMS (Send)               | `android.permission.SEND_SMS`         | Financial fraud risk (premium SMS)             |

### 2.2 Sensitive (Prompt on First Use)

These permissions are prompted once on first use. The user's decision is remembered until manually changed.

| Permission               | Android Equivalent                    | Rationale                                      |
|--------------------------|---------------------------------------|------------------------------------------------|
| Storage (Read)           | `android.permission.READ_EXTERNAL_STORAGE` / `READ_MEDIA_*` | Access to user files              |
| Storage (Write)          | `android.permission.WRITE_EXTERNAL_STORAGE` | Modify/delete user files                |
| Network (Full)           | `android.permission.INTERNET`         | Data exfiltration vector                       |
| Body Sensors             | `android.permission.BODY_SENSORS`     | Health data (if emulated)                      |
| Calendar (Read)          | `android.permission.READ_CALENDAR`    | Schedule and event data                        |
| Calendar (Write)         | `android.permission.WRITE_CALENDAR`   | Data integrity risk                            |
| Phone State              | `android.permission.READ_PHONE_STATE` | Device identifiers, call state                 |
| Bluetooth                | `android.permission.BLUETOOTH_CONNECT` | Device discovery (if emulated)                |
| Nearby Devices           | `android.permission.NEARBY_WIFI_DEVICES` | Network environment discovery               |

### 2.3 Restricted (User Must Explicitly Enable)

These permissions are denied by default and not prompted automatically. The user must navigate to the Permissions page in LinBlock and manually enable them per app. These permissions enable potentially abusive background behaviors.

| Permission               | Android Equivalent / Behavior         | Rationale                                      |
|--------------------------|---------------------------------------|------------------------------------------------|
| Background Location      | `ACCESS_BACKGROUND_LOCATION`          | Continuous tracking without user awareness     |
| Background Network       | (Custom LinBlock permission)          | Silent data exfiltration while app is not visible |
| Autostart on Boot        | `RECEIVE_BOOT_COMPLETED`             | Persistent background execution                |
| Draw Over Other Apps     | `SYSTEM_ALERT_WINDOW`                | Overlay attacks, clickjacking                  |
| Install Unknown Apps     | `REQUEST_INSTALL_PACKAGES`           | Sideloading attack chain                       |
| Device Admin             | `BIND_DEVICE_ADMIN`                  | Anti-removal, remote wipe capability           |
| Accessibility Service    | `BIND_ACCESSIBILITY_SERVICE`         | Full screen reading, action injection          |
| Notification Listener    | `BIND_NOTIFICATION_LISTENER_SERVICE` | Read all notifications                         |
| Usage Stats Access       | `PACKAGE_USAGE_STATS`               | App usage surveillance                         |

### 2.4 Normal (Auto-Granted)

These permissions are granted automatically at install time and do not require user interaction. They provide access to functionality that poses minimal privacy or security risk.

| Permission               | Android Equivalent                    | Rationale                                      |
|--------------------------|---------------------------------------|------------------------------------------------|
| Internet (basic)         | `android.permission.INTERNET`         | Note: categorized as Sensitive if full network control is enabled; Normal in default mode |
| Vibrate                  | `android.permission.VIBRATE`          | No data access, minimal impact                 |
| Wake Lock                | `android.permission.WAKE_LOCK`        | Battery impact only                            |
| Set Wallpaper            | `android.permission.SET_WALLPAPER`    | Cosmetic only                                  |
| NFC                      | `android.permission.NFC`              | Minimal risk in emulated environment           |
| Foreground Service       | `android.permission.FOREGROUND_SERVICE` | Visible to user via notification             |

---

## 3. Per-App Permission State Machine

Each permission for each app follows this state machine:

```
                     +----------+
                     |  UNSET   |  (initial state after app install)
                     +----+-----+
                          |
                     app requests permission
                          |
                +---------+---------+
                |                   |
          (Normal perm)      (Non-normal perm)
                |                   |
                v                   v
          +---------+         +-----------+
          | GRANTED |         | PROMPT    |
          +---------+         +-----+-----+
                                    |
                         user responds to prompt
                                    |
                    +---------------+---------------+
                    |               |               |
                    v               v               v
              +---------+    +---------+    +----------------+
              | GRANTED |    | DENIED  |    | ASK_EVERY_TIME |
              +---------+    +---------+    +----------------+
                    |               |               |
                    |               |               |
                    +-------+-------+               |
                            |                       |
                   user changes in UI               |
                            |                       |
                            v                       |
                    (any state transition            |
                     via Permissions page)           |
                            |                       |
                            +-----------------------+
```

### State Definitions

| State            | Behavior                                                                                           |
|------------------|----------------------------------------------------------------------------------------------------|
| `UNSET`          | No decision has been made. The first access triggers the appropriate prompt (or auto-grant for Normal permissions). |
| `GRANTED`        | Permission is allowed. Access succeeds silently. Logged to audit log.                              |
| `DENIED`         | Permission is blocked. Access fails silently (app receives standard Android denial). Logged to audit log. |
| `ASK_EVERY_TIME` | Each access triggers a user prompt. The user's one-time decision is not persisted. Useful for Critical permissions. |

### State Transitions

| From             | To               | Trigger                                               |
|------------------|------------------|-------------------------------------------------------|
| `UNSET`          | `GRANTED`        | Auto-grant (Normal permission) or user grants in prompt |
| `UNSET`          | `DENIED`         | User denies in prompt                                  |
| `UNSET`          | `ASK_EVERY_TIME` | User selects "ask every time" in prompt                |
| `GRANTED`        | `DENIED`         | User revokes in Permissions UI                         |
| `GRANTED`        | `ASK_EVERY_TIME` | User changes to "ask every time" in Permissions UI     |
| `DENIED`         | `GRANTED`        | User grants in Permissions UI                          |
| `DENIED`         | `ASK_EVERY_TIME` | User changes to "ask every time" in Permissions UI     |
| `ASK_EVERY_TIME` | `GRANTED`        | User changes to "always allow" in Permissions UI       |
| `ASK_EVERY_TIME` | `DENIED`         | User changes to "always deny" in Permissions UI        |
| Any              | `UNSET`          | App is uninstalled and reinstalled (permission reset)  |

---

## 4. Permission Enforcement Flow

```
+-------------------+
| App calls API     |
| (e.g., getLastLocation())
+--------+----------+
         |
         v
+-------------------+
| Android Framework |
| permission check  |
+--------+----------+
         |
         v
+-------------------+
| LinBlock System   |
| Service intercept |
+--------+----------+
         |
         v
+-------------------+     +-------------------+
| Query host        +---->| Host Permission   |
| (virtio-serial)   |     | Manager           |
+-------------------+     +--------+----------+
                                   |
                          +--------+----------+
                          |                   |
                    state=GRANTED       state=DENIED
                          |                   |
                          v                   v
                    +-----------+       +-----------+
                    | Allow     |       | Deny      |
                    | access    |       | access    |
                    +-----------+       +-----------+
                          |                   |
                          |    state=ASK      |
                          |        |          |
                          |        v          |
                          |  +-----------+    |
                          |  | Show user |    |
                          |  | prompt    |    |
                          |  +-----+-----+    |
                          |        |          |
                          |   +----+----+     |
                          |   |         |     |
                          |  Allow    Deny    |
                          |   |         |     |
                          v   v         v     v
                    +---------------------------+
                    | Log to audit log          |
                    | (timestamp, package,      |
                    |  permission, action,      |
                    |  result, source)          |
                    +---------------------------+
```

### Enforcement Layers

Permission enforcement happens at multiple layers for defense-in-depth:

1. **Android Framework:** The standard `checkPermission()` / `checkSelfPermission()` call in the Android framework queries the LinBlock system service instead of (or in addition to) the standard `PackageManager`.
2. **SELinux Policy:** Even if the framework check is bypassed, SELinux policy denies access to the underlying device nodes, files, or sockets. For example, an app denied `CAMERA` permission cannot open `/dev/video0` because its SELinux domain lacks the required `allow` rule.
3. **Host-Side Verification:** For critical operations, the LinBlock system service queries the host permission manager over the virtio-serial channel. This provides a hardware-isolated trust boundary for permission decisions.

---

## 5. Audit Log Specification

### 5.1 Format

Audit logs are stored in **JSON Lines** format (one JSON object per line). Each line is a self-contained record.

### 5.2 Log File Location

- **Host:** `~/.local/share/linblock/logs/audit.jsonl`
- **Rotation:** Daily rotation, retained for 90 days. Files named `audit-YYYY-MM-DD.jsonl`.
- **Maximum size:** 100 MB per file. If exceeded, oldest entries are truncated.

### 5.3 Record Schema

```json
{
    "timestamp": "2026-01-28T14:30:00.123Z",
    "event_type": "permission_check",
    "package": "com.example.app",
    "uid": 10042,
    "permission": "android.permission.CAMERA",
    "action": "check",
    "result": "denied",
    "source": "framework",
    "details": {
        "api_call": "CameraManager.openCamera",
        "state": "DENIED",
        "category": "critical"
    }
}
```

### 5.4 Field Definitions

| Field        | Type   | Required | Description                                                    |
|--------------|--------|----------|----------------------------------------------------------------|
| `timestamp`  | string | Yes      | ISO 8601 timestamp with millisecond precision, UTC timezone.   |
| `event_type` | string | Yes      | One of: `permission_check`, `permission_change`, `app_install`, `app_uninstall`, `app_start`, `app_stop`, `app_freeze`, `app_kill`, `user_prompt`, `policy_update`. |
| `package`    | string | Yes      | Android package name of the app involved.                      |
| `uid`        | int    | Yes      | Android UID of the app.                                        |
| `permission` | string | No       | Android permission string (present for permission events).     |
| `action`     | string | Yes      | The action taken: `check`, `grant`, `deny`, `revoke`, `prompt`, `install`, `uninstall`, `start`, `stop`, `freeze`, `kill`. |
| `result`     | string | Yes      | The outcome: `granted`, `denied`, `pending`, `completed`, `failed`. |
| `source`     | string | Yes      | Where the action originated: `framework`, `selinux`, `user`, `system`, `host`. |
| `details`    | object | No       | Additional context, varies by event type.                      |

### 5.5 Example Records

**Permission check (denied):**
```json
{"timestamp":"2026-01-28T14:30:00.123Z","event_type":"permission_check","package":"com.example.app","uid":10042,"permission":"android.permission.CAMERA","action":"check","result":"denied","source":"framework","details":{"api_call":"CameraManager.openCamera","state":"DENIED","category":"critical"}}
```

**Permission change (user grants):**
```json
{"timestamp":"2026-01-28T14:31:00.456Z","event_type":"permission_change","package":"com.example.app","uid":10042,"permission":"android.permission.CAMERA","action":"grant","result":"granted","source":"user","details":{"previous_state":"DENIED","new_state":"GRANTED","category":"critical"}}
```

**App frozen by user:**
```json
{"timestamp":"2026-01-28T14:35:00.789Z","event_type":"app_freeze","package":"com.example.app","uid":10042,"action":"freeze","result":"completed","source":"user","details":{"reason":"user_initiated","pid":1234}}
```

---

## 6. Permission Manager API

The `permission_manager` module exposes the following Python API for use by the GUI, the emulator core, and the LinBlock system service.

### 6.1 Core Interface

```python
from enum import Enum
from dataclasses import dataclass
from typing import Optional


class PermissionState(Enum):
    UNSET = "unset"
    GRANTED = "granted"
    DENIED = "denied"
    ASK_EVERY_TIME = "ask_every_time"


class PermissionCategory(Enum):
    CRITICAL = "critical"
    SENSITIVE = "sensitive"
    RESTRICTED = "restricted"
    NORMAL = "normal"


@dataclass
class PermissionRecord:
    package: str
    permission: str
    state: PermissionState
    category: PermissionCategory
    last_changed: str          # ISO 8601 timestamp
    last_used: Optional[str]   # ISO 8601 timestamp or None
    usage_count: int


@dataclass
class AuditEntry:
    timestamp: str
    event_type: str
    package: str
    uid: int
    permission: Optional[str]
    action: str
    result: str
    source: str
    details: Optional[dict]


class PermissionManager:
    """
    Central permission management interface.

    All methods are thread-safe. State is persisted to a SQLite database
    on the host at ~/.local/share/linblock/permissions.db.
    """

    def get_permission(
        self, package: str, permission: str
    ) -> PermissionState:
        """
        Get the current state of a specific permission for a specific app.

        Args:
            package: Android package name (e.g., "com.example.app").
            permission: Android permission string
                        (e.g., "android.permission.CAMERA").

        Returns:
            The current PermissionState for this (package, permission) pair.
            Returns PermissionState.UNSET if no decision has been recorded.
        """
        ...

    def set_permission(
        self,
        package: str,
        permission: str,
        state: PermissionState,
        source: str = "user",
    ) -> None:
        """
        Set the state of a specific permission for a specific app.

        This records the change in the permission database and writes
        an audit log entry.

        Args:
            package: Android package name.
            permission: Android permission string.
            state: The new PermissionState to set.
            source: Who initiated the change ("user", "system", "host").

        Raises:
            ValueError: If the permission string is not recognized.
            PermissionError: If the source is not authorized to change
                             this permission (e.g., system-only permissions).
        """
        ...

    def get_app_permissions(
        self, package: str
    ) -> list[PermissionRecord]:
        """
        Get all permission records for a specific app.

        Args:
            package: Android package name.

        Returns:
            A list of PermissionRecord objects, one per permission
            declared in the app's manifest. Permissions not yet
            decided have state=UNSET.
        """
        ...

    def record_usage(
        self,
        package: str,
        permission: str,
        api_call: str,
        result: str,
    ) -> None:
        """
        Record a permission usage event in the audit log.

        Called by the LinBlock system service each time an app
        exercises (or is denied) a permission.

        Args:
            package: Android package name.
            permission: Android permission string.
            api_call: The API method that triggered the check
                      (e.g., "CameraManager.openCamera").
            result: "granted" or "denied".
        """
        ...

    def get_audit_log(
        self,
        package: Optional[str] = None,
        permission: Optional[str] = None,
        event_type: Optional[str] = None,
        since: Optional[str] = None,
        limit: int = 100,
    ) -> list[AuditEntry]:
        """
        Query the audit log with optional filters.

        Args:
            package: Filter by package name (None = all packages).
            permission: Filter by permission string (None = all).
            event_type: Filter by event type (None = all).
            since: ISO 8601 timestamp; return only entries after this
                   time (None = no time filter).
            limit: Maximum number of entries to return (default 100).

        Returns:
            A list of AuditEntry objects, ordered by timestamp descending
            (most recent first).
        """
        ...
```

### 6.2 Convenience Methods

```python
class PermissionManager:
    # ... (core methods above) ...

    def get_all_apps(self) -> list[str]:
        """Return a list of all known package names."""
        ...

    def get_permissions_by_category(
        self, category: PermissionCategory
    ) -> list[str]:
        """Return all permission strings in a given category."""
        ...

    def reset_app_permissions(self, package: str) -> None:
        """
        Reset all permissions for an app to UNSET.
        Called when an app is uninstalled or when the user
        requests a full permission reset.
        """
        ...

    def bulk_set_permissions(
        self,
        package: str,
        permissions: dict[str, PermissionState],
        source: str = "user",
    ) -> None:
        """
        Set multiple permissions at once for an app.
        Atomic: either all succeed or none are changed.
        """
        ...

    def export_audit_log(
        self,
        path: str,
        since: Optional[str] = None,
        until: Optional[str] = None,
    ) -> int:
        """
        Export audit log entries to a file.
        Returns the number of entries exported.
        """
        ...
```

---

## 7. Background Permission Model

LinBlock distinguishes between **foreground** and **background** usage for permissions that can operate in both contexts. This provides an additional layer of control that stock Android partially implements but LinBlock enforces more strictly.

### 7.1 Foreground vs. Background

| Context       | Definition                                                                                |
|---------------|-------------------------------------------------------------------------------------------|
| Foreground    | The app has a visible Activity in the foreground, or a foreground service with a visible notification. |
| Background    | The app is running but has no visible UI. This includes background services, broadcast receivers, and jobs. |

### 7.2 Permissions with Separate Background Grants

The following permissions have independent foreground and background grant states:

| Permission        | Foreground Grant   | Background Grant (Separate)       |
|-------------------|--------------------|-----------------------------------|
| Location          | `ACCESS_FINE_LOCATION` / `ACCESS_COARSE_LOCATION` | `ACCESS_BACKGROUND_LOCATION` |
| Camera            | `CAMERA`           | `CAMERA_BACKGROUND` (custom LinBlock) |
| Microphone        | `RECORD_AUDIO`     | `RECORD_AUDIO_BACKGROUND` (custom LinBlock) |
| Network           | `INTERNET`         | `INTERNET_BACKGROUND` (custom LinBlock) |

### 7.3 Background Grant Rules

1. A background grant CANNOT be issued unless the corresponding foreground grant is already `GRANTED`.
2. Revoking a foreground grant automatically revokes the corresponding background grant.
3. Background permissions are always in the **Restricted** category, meaning the user must manually enable them in the Permissions UI (they are never prompted automatically).
4. Background permission usage is logged with `"context": "background"` in the audit log details.

### 7.4 Enforcement Mechanism

Background permission enforcement works as follows:

1. The LinBlock system service monitors the `ActivityManager` for app lifecycle transitions (foreground/background).
2. When an app moves to the background, the system service checks whether it holds any background-restricted permissions without a background grant.
3. If so, the system service revokes the runtime permission for the app's process and injects an SELinux context transition that moves the app to a more restricted domain (`untrusted_app_background`).
4. When the app returns to the foreground, permissions are restored according to the foreground grant state.

```
App in foreground          App moves to background         App returns to foreground
     |                              |                              |
     v                              v                              v
[Full permissions           [Check background grants]       [Restore foreground
 per grant state]                   |                        permissions]
                            +-------+--------+
                            |                |
                      BG granted       BG not granted
                            |                |
                            v                v
                      [Keep access]    [Revoke access,
                                        switch to
                                        restricted
                                        SELinux domain]
```

---

## 8. Storage and Persistence

### 8.1 Permission Database

- **Location:** `~/.local/share/linblock/permissions.db` (SQLite 3)
- **Schema:**

```sql
CREATE TABLE permissions (
    package       TEXT NOT NULL,
    permission    TEXT NOT NULL,
    state         TEXT NOT NULL DEFAULT 'unset',
    category      TEXT NOT NULL,
    last_changed  TEXT NOT NULL,
    last_used     TEXT,
    usage_count   INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (package, permission)
);

CREATE TABLE apps (
    package       TEXT PRIMARY KEY,
    label         TEXT,
    version_code  INTEGER,
    installed_at  TEXT NOT NULL,
    manifest_permissions TEXT  -- JSON array of declared permissions
);

CREATE INDEX idx_permissions_package ON permissions(package);
CREATE INDEX idx_permissions_state ON permissions(state);
```

### 8.2 Backup and Restore

- Permission state is included in LinBlock snapshots (Phase 1, M7).
- The database can be exported to JSON for manual backup: `linblock permissions export --output perms.json`.
- Importing permissions from a backup resets all app permissions to the backed-up state.

---

## Revision History

| Date       | Author    | Change                                  |
|------------|-----------|-----------------------------------------|
| 2026-01-28 | Agent 005 | Initial permission architecture doc     |
