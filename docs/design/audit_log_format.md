# LinBlock Audit Log Format

## Overview

The LinBlock audit log system records all security-relevant actions related to
application management, permission enforcement, and system configuration changes.
Logs are stored as structured JSON Lines (JSONL) files for easy parsing,
querying, and integration with external analysis tools.

## Log Entry JSON Schema

### Schema Definition

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "title": "LinBlock Audit Log Entry",
  "type": "object",
  "required": ["timestamp", "action", "result"],
  "properties": {
    "timestamp": {
      "type": "string",
      "format": "date-time",
      "description": "ISO 8601 timestamp with timezone (UTC)"
    },
    "package": {
      "type": "string",
      "description": "Android package name (e.g., com.example.app)",
      "pattern": "^[a-zA-Z][a-zA-Z0-9_.]*$"
    },
    "action": {
      "type": "string",
      "description": "The action being audited",
      "enum": [
        "permission_check",
        "permission_grant",
        "permission_revoke",
        "permission_change",
        "app_install",
        "app_uninstall",
        "app_update",
        "app_freeze",
        "app_unfreeze",
        "app_launch",
        "app_stop",
        "app_clear_data",
        "network_access",
        "storage_access",
        "policy_change",
        "config_change",
        "snapshot_save",
        "snapshot_restore"
      ]
    },
    "permission": {
      "type": "string",
      "description": "Android permission name (if applicable)",
      "examples": [
        "android.permission.INTERNET",
        "android.permission.CAMERA",
        "android.permission.READ_CONTACTS"
      ]
    },
    "result": {
      "type": "string",
      "description": "Outcome of the action",
      "enum": ["allowed", "denied", "success", "failure", "error"]
    },
    "source": {
      "type": "string",
      "description": "What initiated the action",
      "enum": ["user", "system", "policy", "app", "adb"]
    },
    "details": {
      "type": "object",
      "description": "Additional context-specific details",
      "additionalProperties": true
    },
    "uid": {
      "type": "integer",
      "description": "Android UID of the app (if applicable)"
    },
    "pid": {
      "type": "integer",
      "description": "Process ID (if applicable)"
    },
    "session_id": {
      "type": "string",
      "description": "Emulator session identifier"
    }
  }
}
```

### Field Descriptions

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `timestamp` | string (ISO 8601) | Yes | When the event occurred, in UTC |
| `package` | string | No | Android package name involved |
| `action` | string (enum) | Yes | Type of action being logged |
| `permission` | string | No | Permission being checked/changed |
| `result` | string (enum) | Yes | Outcome of the action |
| `source` | string (enum) | No | Who/what initiated the action |
| `details` | object | No | Additional context (varies by action) |
| `uid` | integer | No | Android UID of the app |
| `pid` | integer | No | Process ID |
| `session_id` | string | No | Emulator session ID for correlation |

## Storage Format

### File Format: JSON Lines (JSONL)

Each log entry is a single JSON object on one line, terminated by a newline
character. This format enables:
- Append-only writing (no need to parse entire file to add entries)
- Line-by-line streaming reads
- Easy integration with tools like `jq`, `grep`, and log aggregators
- Simple file rotation

### Storage Location

```
~/.config/linblock/audit/
    audit_2026-01-15.jsonl
    audit_2026-01-16.jsonl
    audit_2026-01-17.jsonl
    ...
```

**Base directory:** `~/.config/linblock/audit/`
(Follows XDG Base Directory specification; configurable via `LINBLOCK_AUDIT_DIR`
environment variable or `audit_dir` in config YAML.)

### File Naming Convention

```
audit_YYYY-MM-DD.jsonl
```

- **Pattern:** `audit_` prefix + ISO 8601 date + `.jsonl` extension
- **Granularity:** One file per calendar day (UTC)
- **Examples:**
  - `audit_2026-01-15.jsonl`
  - `audit_2026-01-28.jsonl`

### File Rotation

- **Rotation trigger:** Midnight UTC (new day = new file)
- **Retention:** 90 days by default (configurable)
- **Cleanup:** Files older than the retention period are automatically deleted
  on emulator startup and every 24 hours while running
- **Compression:** Files older than 7 days may be gzip-compressed to save space
  (e.g., `audit_2026-01-10.jsonl.gz`)

### Retention Configuration

In `~/.config/linblock/config.yaml`:

```yaml
audit:
  enabled: true
  directory: ~/.config/linblock/audit
  retention_days: 90
  compress_after_days: 7
  max_file_size_mb: 100
  log_level: info  # debug, info, warn, error
```

## Example Log Entries

### permission_check - Permission Runtime Check

When an app attempts to use a permission-guarded API:

```json
{"timestamp":"2026-01-15T14:23:45.123Z","package":"com.example.socialapp","action":"permission_check","permission":"android.permission.CAMERA","result":"denied","source":"app","uid":10045,"pid":12345,"session_id":"sess_abc123","details":{"api":"android.hardware.camera2.CameraManager.openCamera","caller_class":"com.example.socialapp.CameraActivity"}}
```

### permission_grant - Permission Granted by User

When the user grants a runtime permission:

```json
{"timestamp":"2026-01-15T14:24:01.456Z","package":"com.example.socialapp","action":"permission_grant","permission":"android.permission.CAMERA","result":"success","source":"user","uid":10045,"session_id":"sess_abc123","details":{"grant_type":"runtime","previous_state":"denied","dialog_shown":true}}
```

### permission_revoke - Permission Revoked by User

When the user revokes a previously granted permission:

```json
{"timestamp":"2026-01-15T15:30:22.789Z","package":"com.example.socialapp","action":"permission_revoke","permission":"android.permission.CAMERA","result":"success","source":"user","uid":10045,"session_id":"sess_abc123","details":{"previous_state":"granted","method":"settings_ui"}}
```

### permission_change - Bulk Permission Policy Change

When a permission policy is changed affecting multiple apps:

```json
{"timestamp":"2026-01-15T16:00:00.000Z","package":"*","action":"permission_change","permission":"android.permission.READ_PHONE_STATE","result":"success","source":"policy","session_id":"sess_abc123","details":{"policy":"deny_all_telephony","affected_packages":["com.example.app1","com.example.app2"],"affected_count":2}}
```

### app_install - Application Installation

When an APK is installed:

```json
{"timestamp":"2026-01-15T10:15:33.321Z","package":"com.example.newapp","action":"app_install","result":"success","source":"user","session_id":"sess_abc123","details":{"version_code":42,"version_name":"2.1.0","apk_size_bytes":15728640,"install_source":"sideload","sha256":"a1b2c3d4e5f6...","permissions_declared":["android.permission.INTERNET","android.permission.CAMERA"]}}
```

### app_uninstall - Application Removal

When an app is uninstalled:

```json
{"timestamp":"2026-01-15T11:20:00.000Z","package":"com.example.oldapp","action":"app_uninstall","result":"success","source":"user","uid":10032,"session_id":"sess_abc123","details":{"version_code":10,"data_cleared":true,"reason":"user_request"}}
```

### app_freeze - Application Frozen

When LinBlock freezes an app (disables without uninstalling):

```json
{"timestamp":"2026-01-15T12:00:00.000Z","package":"com.example.bloatware","action":"app_freeze","result":"success","source":"user","uid":10050,"session_id":"sess_abc123","details":{"previous_state":"enabled","reason":"user_freeze","processes_killed":2}}
```

### app_unfreeze - Application Unfrozen

When a frozen app is re-enabled:

```json
{"timestamp":"2026-01-15T13:00:00.000Z","package":"com.example.bloatware","action":"app_unfreeze","result":"success","source":"user","uid":10050,"session_id":"sess_abc123","details":{"previous_state":"frozen","frozen_duration_hours":1.0}}
```

### network_access - Network Access Attempt

When an app attempts network communication:

```json
{"timestamp":"2026-01-15T14:30:00.000Z","package":"com.example.app","action":"network_access","result":"allowed","source":"app","uid":10045,"pid":12345,"session_id":"sess_abc123","details":{"destination":"api.example.com","port":443,"protocol":"tcp","direction":"outbound"}}
```

### storage_access - Sensitive Storage Access

When an app accesses shared storage:

```json
{"timestamp":"2026-01-15T14:35:00.000Z","package":"com.example.filemanager","action":"storage_access","result":"allowed","source":"app","uid":10060,"session_id":"sess_abc123","details":{"path":"/storage/emulated/0/DCIM/","access_type":"read","scope":"media_images"}}
```

### snapshot_save - VM Snapshot Saved

When the emulator state is saved:

```json
{"timestamp":"2026-01-15T18:00:00.000Z","action":"snapshot_save","result":"success","source":"user","session_id":"sess_abc123","details":{"snapshot_name":"before_testing","snapshot_size_mb":2048,"includes_memory":true,"includes_disk":true}}
```

## Query Interface

### Command-Line Queries Using jq

The JSONL format integrates naturally with `jq` for ad-hoc queries:

```bash
# All denied permission checks
jq -c 'select(.action == "permission_check" and .result == "denied")' \
    ~/.config/linblock/audit/audit_2026-01-15.jsonl

# All actions for a specific package
jq -c 'select(.package == "com.example.app")' \
    ~/.config/linblock/audit/audit_2026-01-15.jsonl

# Count of actions by type
jq -r '.action' ~/.config/linblock/audit/audit_2026-01-15.jsonl | sort | uniq -c | sort -rn

# Permission grants in a date range (search multiple files)
cat ~/.config/linblock/audit/audit_2026-01-1*.jsonl | \
    jq -c 'select(.action == "permission_grant")'

# All app installations with their permissions
jq -c 'select(.action == "app_install") | {package, permissions: .details.permissions_declared}' \
    ~/.config/linblock/audit/audit_2026-01-15.jsonl
```

### Python Query API

LinBlock provides a Python API for programmatic log queries:

```python
from linblock.audit import AuditLogQuery

query = AuditLogQuery(audit_dir="~/.config/linblock/audit")

# Filter by package
entries = query.filter(
    package="com.example.app",
    start_date="2026-01-01",
    end_date="2026-01-31"
)

# Filter by action and result
denied = query.filter(
    action="permission_check",
    result="denied",
    start_date="2026-01-15"
)

# Filter by permission
camera_events = query.filter(
    permission="android.permission.CAMERA"
)

# Get summary statistics
stats = query.summary(date="2026-01-15")
# Returns: {"total_entries": 1234, "by_action": {...}, "by_result": {...}}
```

### Query Interface Protocol

```python
class AuditLogQueryInterface(Protocol):
    def filter(
        self,
        package: Optional[str] = None,
        action: Optional[str] = None,
        permission: Optional[str] = None,
        result: Optional[str] = None,
        source: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
        limit: int = 1000
    ) -> list[dict]: ...

    def summary(
        self,
        date: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> dict: ...

    def tail(
        self,
        n: int = 50,
        follow: bool = False
    ) -> Iterator[dict]: ...
```

## Log Writer Interface

### Python Implementation

```python
import json
import os
from datetime import datetime, timezone
from pathlib import Path

class AuditLogger:
    def __init__(self, audit_dir: str = "~/.config/linblock/audit"):
        self.audit_dir = Path(audit_dir).expanduser()
        self.audit_dir.mkdir(parents=True, exist_ok=True)
        self._current_file = None
        self._current_date = None

    def _get_log_file(self):
        today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
        if today != self._current_date:
            if self._current_file:
                self._current_file.close()
            path = self.audit_dir / f"audit_{today}.jsonl"
            self._current_file = open(path, "a", encoding="utf-8")
            self._current_date = today
        return self._current_file

    def log(self, action: str, result: str, **kwargs):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "action": action,
            "result": result,
        }
        entry.update({k: v for k, v in kwargs.items() if v is not None})
        f = self._get_log_file()
        f.write(json.dumps(entry, separators=(",", ":")) + "\n")
        f.flush()

    def close(self):
        if self._current_file:
            self._current_file.close()
```

### Usage Examples

```python
logger = AuditLogger()

# Log permission check
logger.log(
    action="permission_check",
    result="denied",
    package="com.example.app",
    permission="android.permission.CAMERA",
    source="app",
    uid=10045,
    details={"api": "CameraManager.openCamera"}
)

# Log app installation
logger.log(
    action="app_install",
    result="success",
    package="com.example.newapp",
    source="user",
    details={
        "version_code": 42,
        "version_name": "2.1.0",
        "apk_size_bytes": 15728640,
        "install_source": "sideload"
    }
)

# Log app freeze
logger.log(
    action="app_freeze",
    result="success",
    package="com.example.bloatware",
    source="user",
    uid=10050,
    details={"reason": "user_freeze"}
)
```

## Log Integrity

### Checksums

Each daily log file has an accompanying checksum file for integrity verification:

```
~/.config/linblock/audit/
    audit_2026-01-15.jsonl
    audit_2026-01-15.jsonl.sha256
```

The checksum is updated when the file is rotated (at end of day). To verify:

```bash
sha256sum -c ~/.config/linblock/audit/audit_2026-01-15.jsonl.sha256
```

### Tamper Detection

The audit system can optionally maintain a hash chain where each entry includes
the hash of the previous entry, enabling detection of log modification:

```json
{"timestamp":"...","action":"...","result":"...","_prev_hash":"sha256:abc123..."}
```

This is optional and can be enabled in configuration:

```yaml
audit:
  integrity:
    hash_chain: true
    algorithm: sha256
```

## Performance Considerations

### Write Performance

- **Append-only:** Writing is always sequential append, minimizing I/O
- **Buffered writes:** Entries are buffered and flushed periodically or on critical events
- **Async option:** Non-critical log entries can be written asynchronously via a queue
- **Target:** < 1 ms per log entry write

### Storage Estimates

| Activity Level | Entries/Day | File Size/Day | 90-Day Total |
|---------------|-------------|---------------|--------------|
| Light | 1,000 | ~500 KB | ~45 MB |
| Normal | 10,000 | ~5 MB | ~450 MB |
| Heavy | 100,000 | ~50 MB | ~4.5 GB |
| Debug mode | 1,000,000 | ~500 MB | ~45 GB |

With gzip compression (after 7 days), storage is reduced by approximately 80-90%.
