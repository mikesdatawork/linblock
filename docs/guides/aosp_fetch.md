# AOSP Fetch Procedure

## Overview

This guide covers how to download, configure, and prepare the Android Open Source
Project (AOSP) source code for building LinBlock's Android 14 system image. It also
describes a faster Phase 1 alternative using prebuilt Generic System Images (GSI).

## Prerequisites

### Hardware Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| Disk space | 300 GB free | 500 GB free (SSD strongly recommended) |
| RAM | 16 GB | 32 GB or more |
| CPU | 4 cores | 8+ cores (for faster builds) |
| Network | Broadband | 50+ Mbps (initial sync downloads ~100 GB) |

**Disk breakdown:**
- AOSP source tree: ~200 GB
- Build output: ~100 GB
- ccache: ~50 GB (optional but recommended)
- Working space: ~50 GB

### Software Requirements

```bash
# Install required packages (Ubuntu 22.04 / 24.04)
sudo apt-get update
sudo apt-get install -y \
    git curl wget \
    python3 python3-pip \
    openjdk-17-jdk \
    build-essential \
    zip unzip \
    libssl-dev \
    repo

# If 'repo' is not in apt, install manually:
mkdir -p ~/.local/bin
curl https://storage.googleapis.com/git-repo-downloads/repo > ~/.local/bin/repo
chmod a+x ~/.local/bin/repo
export PATH="$HOME/.local/bin:$PATH"
```

## Phase 1 Alternative: Prebuilt GSI Images

For initial development and testing, prebuilt Generic System Images (GSI) can
be used instead of building from source. This saves significant time and disk space.

### Downloading GSI

```bash
# Create working directory
mkdir -p ~/linblock-images && cd ~/linblock-images

# Download Android 14 GSI (x86_64)
# Check https://developer.android.com/topic/generic-system-image/releases for latest
wget https://dl.google.com/developers/android/sc/gsi/gsi_gms_x86_64-img.zip

# Extract
unzip gsi_gms_x86_64-img.zip
```

### Converting GSI for LinBlock

```bash
# Convert raw system image to qcow2
qemu-img convert -f raw -O qcow2 system.img system.qcow2

# Create vendor image (minimal, LinBlock-specific)
# This will be built separately
```

**Advantages of GSI approach:**
- No AOSP source download required
- No build time (saves hours)
- Quick start for emulator development
- Can test boot and display pipeline immediately

**Limitations:**
- Includes Google services (may not match LinBlock minimal goals)
- Cannot customize system internals
- May include unnecessary components
- Not suitable for final LinBlock builds

## Full AOSP Source Fetch

### Step 1: Initialize Repo

```bash
# Create AOSP directory
mkdir -p ~/aosp && cd ~/aosp

# Initialize repo with Android 14 manifest
repo init \
    -u https://android.googlesource.com/platform/manifest \
    -b android-14.0.0_r1 \
    --depth=1

# Note: --depth=1 creates a shallow clone, saving disk space
# Remove --depth=1 if you need full git history
```

**Available Android 14 branches:**
| Branch | Description |
|--------|-------------|
| `android-14.0.0_r1` | Initial release |
| `android-14.0.0_r2` | First patch release |
| `android-14.0.0_r17` | Latest stable (check for updates) |

Use the latest stable tag for best compatibility and security patches.

### Step 2: Sync Source

```bash
# Full sync (initial download)
repo sync \
    -c \
    -j8 \
    --no-tags \
    --no-clone-bundle \
    --optimized-fetch

# Flag explanation:
#   -c                  : Only fetch the current branch (saves bandwidth)
#   -j8                 : Use 8 parallel download threads
#   --no-tags           : Don't fetch git tags (saves bandwidth/space)
#   --no-clone-bundle   : Don't use bundle files (more reliable on some networks)
#   --optimized-fetch   : Use optimized fetch algorithm
```

**Expected download:**
- Size: ~80-100 GB
- Time: 1-4 hours depending on network speed
- Projects: ~1000 git repositories

### Step 3: Verify Sync

```bash
# Check sync status
repo status

# Verify key directories exist
ls -d \
    build/make \
    frameworks/base \
    packages/apps \
    device \
    kernel \
    system/core
```

## Mirror Setup (For Repeated Syncs)

If you plan to maintain multiple AOSP working directories or rebuild frequently,
setting up a local mirror avoids repeated downloads from Google's servers.

### Creating a Mirror

```bash
# Create mirror directory (needs ~200 GB)
mkdir -p ~/aosp-mirror && cd ~/aosp-mirror

# Initialize mirror
repo init \
    -u https://android.googlesource.com/platform/manifest \
    --mirror

# Sync mirror (initial download, same as full sync)
repo sync -j8
```

### Using the Mirror

```bash
# Create working directory using local mirror
mkdir -p ~/aosp-work && cd ~/aosp-work

# Initialize from local mirror instead of Google servers
repo init \
    -u ~/aosp-mirror/platform/manifest.git \
    -b android-14.0.0_r1

# Sync from mirror (much faster, no network needed)
repo sync -j8 --local-only
```

### Updating the Mirror

```bash
# Periodically update mirror from upstream
cd ~/aosp-mirror
repo sync -j8
```

## Applying LinBlock Customizations

After syncing AOSP, add the LinBlock device tree and vendor files:

### Step 1: Add Device Tree

```bash
# Create LinBlock device directory
mkdir -p ~/aosp/device/linblock/x86_64

# Copy LinBlock device files
cp -r /path/to/linblock/android/vendor/linblock/* ~/aosp/device/linblock/x86_64/
```

### Step 2: Add Local Manifests (Optional)

For automated inclusion of LinBlock repositories:

```bash
mkdir -p ~/aosp/.repo/local_manifests

cat > ~/aosp/.repo/local_manifests/linblock.xml <<EOF
<?xml version="1.0" encoding="UTF-8"?>
<manifest>
    <remote name="linblock" fetch="https://github.com/linblock" />
    <project path="device/linblock/x86_64"
             name="device_linblock_x86_64"
             remote="linblock"
             revision="main" />
    <project path="vendor/linblock"
             name="vendor_linblock"
             remote="linblock"
             revision="main" />
</manifest>
EOF
```

### Step 3: Set Up Build Environment

```bash
cd ~/aosp

# Initialize build environment
source build/envsetup.sh

# Select LinBlock build target
lunch linblock_x86_64-userdebug
```

## Incremental Syncs

After the initial sync, subsequent syncs are much faster:

```bash
cd ~/aosp

# Quick sync (only changed projects)
repo sync -c -j8 --no-tags

# Force sync (if there are conflicts)
repo sync -c -j8 --no-tags --force-sync
```

## Disk Space Management

### Cleaning Build Output

```bash
# Remove all build output
cd ~/aosp
make clean           # or: rm -rf out/

# Remove only target-specific output
make installclean
```

### Reducing Source Size

```bash
# Remove .git directories (saves ~50% space but loses history)
# WARNING: Cannot update after this!
repo forall -c 'rm -rf .git'
```

### Checking Disk Usage

```bash
# AOSP source size
du -sh ~/aosp --exclude=out
# Expected: ~150-200 GB

# Build output size
du -sh ~/aosp/out
# Expected: ~80-100 GB

# Total
du -sh ~/aosp
# Expected: ~250-300 GB
```

## Troubleshooting

### Sync Failures

```bash
# Retry failed sync
repo sync -c -j4 --no-tags --fail-fast

# If specific project fails, sync it individually
repo sync platform/frameworks/base

# Network timeout: reduce parallelism
repo sync -c -j2 --no-tags
```

### Disk Space Issues

```bash
# Check available space
df -h .

# If space is low:
# 1. Use --depth=1 for shallow clone
# 2. Exclude unnecessary projects via local manifest
# 3. Use an external drive (SSD recommended)
```

### Java Version Issues

```bash
# Verify Java version
java -version
# Expected: openjdk version "17.x.x"

# If wrong version, set JAVA_HOME
export JAVA_HOME=/usr/lib/jvm/java-17-openjdk-amd64
export PATH="$JAVA_HOME/bin:$PATH"
```

### Repo Tool Issues

```bash
# Update repo tool
repo selfupdate

# If repo is not found
export PATH="$HOME/.local/bin:$PATH"

# Python version issues (repo requires Python 3)
python3 --version
```

## Build Quick Start

After successfully syncing AOSP and adding LinBlock files:

```bash
cd ~/aosp

# Set up environment
source build/envsetup.sh
lunch linblock_x86_64-userdebug

# Build (use -jN where N = number of CPU cores)
make -j$(nproc)

# Build output location
ls out/target/product/x86_64/
# system.img, vendor.img, userdata.img, etc.
```

See the AOSP build setup script (`scripts/setup/setup_aosp_build.sh`) for
detailed build dependency installation.
