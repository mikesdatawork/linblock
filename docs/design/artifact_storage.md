# LinBlock Artifact Storage Layout

Version: 1.0.0
Status: Draft
Last Updated: 2025-01-28
Owner: Agent 010 (DevOps)

---

## 1. Overview

This document defines the artifact storage conventions for the LinBlock project, including build artifact naming, storage locations, retention policies, and release artifact management.

---

## 2. Build Artifact Naming Convention

All build artifacts follow a consistent naming scheme:

```
linblock-{version}-{date}-{git_hash}.tar.gz
```

### 2.1 Components

| Component    | Format              | Example            |
|--------------|---------------------|--------------------|
| `version`    | `MAJOR.MINOR.PATCH` | `0.1.0`            |
| `date`       | `YYYYMMDD`          | `20250128`         |
| `git_hash`   | 7-char short SHA    | `a3f9c1b`          |

### 2.2 Examples

```
linblock-0.1.0-20250128-a3f9c1b.tar.gz
linblock-0.2.0-20250315-e7d2f4a.tar.gz
linblock-1.0.0-20251001-b1c3e5f.tar.gz
```

### 2.3 Nightly Build Naming

Nightly builds append `-nightly` before the date:

```
linblock-0.1.0-nightly-20250128-a3f9c1b.tar.gz
```

### 2.4 Development Snapshot Naming

Development snapshots use `-dev` suffix:

```
linblock-0.1.0-dev-20250128-a3f9c1b.tar.gz
```

---

## 3. Artifact Types

### 3.1 GTK Application Bundle

The primary desktop application packaged for Linux distribution.

| Attribute     | Detail                                          |
|---------------|-------------------------------------------------|
| Contents      | Python application, GTK resources, configs      |
| Format        | `.tar.gz` archive                               |
| Name pattern  | `linblock-{version}-{date}-{git_hash}.tar.gz`  |
| Install target| `/opt/linblock/` or user home                   |

**Bundle contents:**
```
linblock-{version}/
    bin/
        linblock              # Main launcher script
    lib/
        python/               # Python modules
    share/
        linblock/
            resources/        # GTK UI resources, icons, themes
            configs/          # Default configuration files
    docs/
        README.md
        LICENSE
```

### 3.2 AOSP System Images

Pre-built Android system images for the emulator.

| Attribute     | Detail                                              |
|---------------|-----------------------------------------------------|
| Contents      | system.img, vendor.img, ramdisk.img, kernel         |
| Format        | `.tar.gz` archive                                   |
| Name pattern  | `linblock-aosp-{android_ver}-{arch}-{date}.tar.gz` |
| Supported arch| `x86_64`, `arm64`                                   |

**Example names:**
```
linblock-aosp-14-x86_64-20250128.tar.gz
linblock-aosp-14-arm64-20250128.tar.gz
```

### 3.3 Setup Scripts

Installation and setup automation scripts.

| Attribute     | Detail                                          |
|---------------|-------------------------------------------------|
| Contents      | Shell scripts, dependency checks, config setup  |
| Format        | `.sh` files or `.tar.gz` bundle                 |
| Name pattern  | `linblock-setup-{platform}-{version}.sh`        |

---

## 4. GitHub Releases

### 4.1 Tag Format

Release tags follow strict semantic versioning:

```
v{MAJOR}.{MINOR}.{PATCH}
```

**Examples:**
```
v0.1.0    # First alpha release
v0.2.0    # Second alpha with new features
v1.0.0    # First stable release
v1.0.1    # Patch release
v1.1.0    # Minor feature release
```

### 4.2 Pre-release Tags

Pre-release versions use suffixes:

```
v0.1.0-alpha.1
v0.1.0-beta.1
v0.1.0-rc.1
```

### 4.3 Release Assets

Each GitHub Release includes:

| Asset                          | Required | Description                    |
|--------------------------------|----------|--------------------------------|
| `linblock-{ver}-*.tar.gz`     | Yes      | Application bundle             |
| `linblock-aosp-*-.tar.gz`     | Yes      | System image (per arch)        |
| `SHA256SUMS.txt`               | Yes      | Checksums for all artifacts    |
| `CHANGELOG.md`                 | Yes      | Release notes                  |
| `linblock-setup-*.sh`         | Optional | Setup script                   |

### 4.4 Release Notes Template

```markdown
## LinBlock v{VERSION}

### Highlights
- Key feature or fix 1
- Key feature or fix 2

### Changes
- [module_name] Description of change
- [module_name] Description of change

### Bug Fixes
- [module_name] Description of fix

### Known Issues
- Description of known issue

### Checksums
See SHA256SUMS.txt for artifact verification.
```

---

## 5. Local Storage Layout

### 5.1 Directory Structure

Local artifact storage follows this structure:

```
/mnt/data/linblock-artifacts/
    releases/                  # Permanent release artifacts
        v0.1.0/
            linblock-0.1.0-20250128-a3f9c1b.tar.gz
            linblock-aosp-14-x86_64-20250128.tar.gz
            SHA256SUMS.txt
            CHANGELOG.md
        v0.2.0/
            ...
    nightly/                   # Nightly build artifacts (auto-cleaned)
        2025-01-28/
            linblock-0.1.0-nightly-20250128-a3f9c1b.tar.gz
            test-results.xml
            coverage.xml
        2025-01-27/
            ...
    cache/                     # Build cache and intermediate artifacts
        pip-cache/             # Python package cache
        aosp-cache/            # AOSP build cache
        ccache/                # C/C++ compilation cache
```

### 5.2 Permissions

| Directory    | Owner     | Group     | Permissions |
|--------------|-----------|-----------|-------------|
| `releases/`  | `ci-user` | `linblock`| `755`       |
| `nightly/`   | `ci-user` | `linblock`| `755`       |
| `cache/`     | `ci-user` | `linblock`| `775`       |

---

## 6. Retention Policy

### 6.1 Retention Rules

| Artifact Type     | Retention Period | Cleanup Method        |
|-------------------|------------------|-----------------------|
| Releases          | Permanent        | Manual removal only   |
| Nightly builds    | 14 days          | Automated daily cron  |
| Build cache       | 30 days LRU      | Automated weekly cron |
| CI artifacts      | 14 days          | GitHub auto-cleanup   |
| Coverage reports  | 14 days          | GitHub auto-cleanup   |

### 6.2 Cleanup Automation

Nightly cleanup script (`scripts/cleanup_artifacts.sh`):

```bash
#!/bin/bash
# Clean up nightly artifacts older than 14 days
find /mnt/data/linblock-artifacts/nightly/ -maxdepth 1 -type d -mtime +14 -exec rm -rf {} \;

# Clean up cache entries older than 30 days
find /mnt/data/linblock-artifacts/cache/ -type f -atime +30 -delete
```

This script is scheduled via cron:
```
0 3 * * * /path/to/scripts/cleanup_artifacts.sh
```

### 6.3 Storage Budget

| Category       | Estimated Size per Item | Max Total   |
|----------------|-------------------------|-------------|
| Release        | ~2 GB (app + images)    | Unlimited   |
| Nightly        | ~500 MB                 | ~7 GB       |
| Build cache    | Variable                | 20 GB cap   |

---

## 7. Artifact Verification

### 7.1 Checksums

All release artifacts include SHA-256 checksums:

```bash
# Generate checksums
sha256sum linblock-*.tar.gz > SHA256SUMS.txt

# Verify checksums
sha256sum -c SHA256SUMS.txt
```

### 7.2 Signing (Future)

Future releases will include GPG signatures:

```
linblock-{ver}-*.tar.gz.asc    # Detached GPG signature
```

---

## 8. References

- LinBlock Release Procedure: `docs/guides/release_procedure.md`
- LinBlock CI Pipeline: `.github/workflows/ci.yml`
- Semantic Versioning: https://semver.org/
