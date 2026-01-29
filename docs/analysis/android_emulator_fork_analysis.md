# Android Emulator Fork Analysis - Build Engineering Perspective

**Agent**: 007 (Build Engineer)
**Date**: 2026-01-29
**Status**: Analysis Complete

---

## Executive Summary

Forking Google's Android Emulator from `platform/external/qemu` is **technically feasible but carries significant build complexity**. The repository uses CMake with extensive prebuilt dependencies, making a stripped fork moderate-to-high effort. For LinBlock's Linux-only target, a focused approach is viable.

**Recommendation**: Pursue a **hybrid approach** - fork the Android Emulator for its Android-specific optimizations (goldfish/ranchu devices, Android-tuned graphics pipeline), but strip aggressively and consider wrapping with LinBlock's existing Python/GTK infrastructure rather than forking the entire codebase.

---

## 1. Build System Analysis

### 1.1 Current Android Emulator Build System

The Android Emulator uses **CMake** as its meta-build generator with **Ninja** as the backend.

**Key Build Files**:
```
platform/external/qemu/
├── CMakeLists.txt              # Root build configuration
├── android/
│   ├── rebuild.sh              # Primary build script
│   ├── build/cmake/            # CMake toolchain files
│   └── third_party/            # Bundled dependencies (zlib, libpng, SDL)
├── android-qemu2-glue/         # Android-QEMU integration layer
└── qemu2-auto-generated/       # Generated QEMU configuration
```

**Build Initialization**:
```bash
# Full repository setup (required - uses Google's repo tool)
mkdir -p $HOME/emu-master-dev && cd $HOME/emu-master-dev
repo init -u https://android.googlesource.com/platform/manifest -b emu-master-dev
repo sync -j 8

# Build
cd external/qemu && android/rebuild.sh

# Incremental builds
ninja -C objs
```

### 1.2 Setting Up Build Environment for LinBlock

**Minimum System Requirements**:
| Requirement | Specification |
|-------------|---------------|
| OS | Linux (Ubuntu 20.04+ recommended) |
| RAM | 16 GB minimum, 32 GB recommended |
| Disk | 50-100 GB for full build tree |
| CPU | x86_64 with KVM support |

**Required Packages (Debian/Ubuntu)**:
```bash
sudo apt-get install -y \
    git \
    build-essential \
    python3 \
    python3-pip \
    qemu-kvm \
    ninja-build \
    ccache \
    cmake \
    pkg-config \
    libglib2.0-dev \
    libfdt-dev \
    libpixman-1-dev \
    zlib1g-dev \
    libsdl2-dev \
    libgtk-3-dev \
    libpulse-dev \
    libasound2-dev \
    libusb-1.0-0-dev \
    libvirglrenderer-dev
```

### 1.3 Stripping Unnecessary Components

The Android Emulator contains substantial code for features LinBlock does not need:

**Components to REMOVE** (high-value strip targets):
| Component | Size Impact | Removal Complexity |
|-----------|-------------|-------------------|
| Windows/MSVC support | ~15% build complexity | Low - CMake conditionals |
| macOS/Darwin support | ~10% build complexity | Low - CMake conditionals |
| Qt-based GUI | ~50 MB+ binaries | Medium - requires display abstraction |
| WebRTC support | ~30 MB dependencies | Low - CMake flag: `WEBRTC=FALSE` |
| Chromium location UI | ~100 MB+ | Low - CMake flag: `QTWEBENGINE=FALSE` |
| 32-bit guest support | ~20% code | Low - CMake flag: `OPTION_MINBUILD=TRUE` |
| Crash reporting (Breakpad) | ~5 MB | Low - conditional compilation |
| Android Studio integration | ~10% glue code | Medium - API dependencies |

**Components to KEEP**:
| Component | Reason |
|-----------|--------|
| KVM acceleration | Essential for performance |
| virtio devices | Required for Android I/O |
| goldfish/ranchu board | Android hardware model |
| SwiftShader/ANGLE | GPU emulation (software fallback) |
| ADB integration | Required for app management |
| virglrenderer | GPU acceleration on Linux |

**CMake Configuration for Stripped Build**:
```cmake
# linblock_emulator_config.cmake
set(OPTION_MINBUILD TRUE)           # 64-bit guests only
set(WEBRTC FALSE)                   # No WebRTC
set(QTWEBENGINE FALSE)              # No Chromium UI
set(OPTION_TCMALLOC TRUE)           # Keep for performance
set(GFXSTREAM FALSE)                # Disable unless needed
set(OPTION_RUST FALSE)              # Disable Rust dependencies

# Linux-only targets
set(CMAKE_SYSTEM_NAME Linux)
set(ANDROID_TARGET_TAG linux-x86_64)
```

### 1.4 Producing Standalone Binaries

**Build Output Structure**:
```
objs/
├── emulator                    # Main emulator binary
├── emulator64-x86              # x86_64 target binary
├── lib64/
│   ├── libEGL_swiftshader.so
│   ├── libGLESv2_swiftshader.so
│   ├── libvirglrenderer.so
│   └── [other shared libraries]
├── qemu/linux-x86_64/
│   └── qemu-system-x86_64      # Core QEMU binary
└── resources/                  # ROM files, skins, etc.
```

**Standalone Package Script**:
```bash
#!/bin/bash
# scripts/package_emulator.sh

BUILD_DIR="objs"
PACKAGE_DIR="linblock-emulator"

mkdir -p "$PACKAGE_DIR"/{bin,lib,share}

# Core binaries
cp "$BUILD_DIR"/emulator "$PACKAGE_DIR/bin/"
cp "$BUILD_DIR"/qemu/linux-x86_64/qemu-system-x86_64 "$PACKAGE_DIR/bin/"

# Required libraries (audit with ldd)
for lib in "$BUILD_DIR"/lib64/*.so*; do
    cp "$lib" "$PACKAGE_DIR/lib/"
done

# Strip binaries
strip --strip-unneeded "$PACKAGE_DIR"/bin/*
strip --strip-unneeded "$PACKAGE_DIR"/lib/*.so*

# Create wrapper script
cat > "$PACKAGE_DIR/bin/linblock-emu" << 'EOF'
#!/bin/bash
DIR="$(dirname "$(readlink -f "$0")")"
export LD_LIBRARY_PATH="$DIR/../lib:$LD_LIBRARY_PATH"
exec "$DIR/emulator" "$@"
EOF
chmod +x "$PACKAGE_DIR/bin/linblock-emu"

# Package
tar -czvf linblock-emulator.tar.gz "$PACKAGE_DIR"
```

---

## 2. Dependencies Analysis

### 2.1 External Dependencies Matrix

| Dependency | Version | Purpose | Bundled? | Notes |
|------------|---------|---------|----------|-------|
| glib2 | 2.56+ | Core utilities | Prebuilt | Required |
| pixman | 0.36+ | Pixel manipulation | Prebuilt | Required |
| zlib | 1.2+ | Compression | Bundled | android/third_party |
| libfdt | 1.5+ | Device tree | Prebuilt | Required |
| libusb | 1.0+ | USB passthrough | Prebuilt | Optional |
| SDL2 | 2.0+ | Display/input | Prebuilt | LinBlock uses GTK instead |
| virglrenderer | 0.8+ | GPU acceleration | Prebuilt | Linux only |
| SwiftShader | - | Software GPU | Bundled | Fallback renderer |
| ANGLE | - | Shader translation | Bundled | Graphics compatibility |
| Python3 | 3.8+ | Build scripts | System | Required for build |
| Ninja | 1.10+ | Build backend | System | Required |
| CMake | 3.18+ | Meta-build | System | Required |

### 2.2 Prebuilt Dependencies Location

The Android Emulator relies heavily on prebuilts:
```
prebuilts/android-emulator-build/
├── common/
│   ├── breakpad/
│   ├── e2fsprogs/
│   ├── protobuf/
│   └── ...
├── linux-x86_64/
│   ├── clang/          # Compiler toolchain
│   ├── glib/
│   ├── pixman/
│   ├── virglrenderer/
│   └── ...
└── qt/                 # Qt libraries (can remove for LinBlock)
```

**Critical**: The emulator includes its own clang/LLVM toolchain. This ensures reproducible builds but adds ~2 GB to the source tree.

### 2.3 Compiler Requirements

| Tool | Required Version | Notes |
|------|-----------------|-------|
| Clang | 12+ (bundled) | Uses prebuilt from repo |
| GCC | 9+ (alternative) | For system builds |
| C++ Standard | C++17 | Required |

---

## 3. Linux-Only Build Complexity

### 3.1 Platform Complexity Breakdown

| Platform | Files | Complexity | LinBlock Needs |
|----------|-------|------------|----------------|
| Linux x86_64 | ~60% | Baseline | **YES** |
| Linux aarch64 | ~10% | Low | Optional |
| Windows MSVC | ~15% | High | **NO** |
| macOS x86_64 | ~10% | Medium | **NO** |
| macOS ARM64 | ~5% | Medium | **NO** |

### 3.2 Linux-Only Simplifications

Removing non-Linux platforms provides:

1. **Simpler CMake configuration** - No cross-compilation toolchains
2. **Reduced dependency tree** - No Windows SDK, no macOS frameworks
3. **Smaller prebuilt set** - Only linux-x86_64 prebuilts needed
4. **Cleaner codebase** - Remove `#ifdef _WIN32`, `#ifdef __APPLE__` sections

**Estimated reduction**: 30-40% of build complexity

### 3.3 Linux Build Command

```bash
#!/bin/bash
# build_linux_only.sh

export OPTION_MINBUILD=1
export WEBRTC=0
export QTWEBENGINE=0

./android/rebuild.sh \
    --target linux \
    --build-dir=objs-linux \
    --cmake-option="-DCMAKE_BUILD_TYPE=Release" \
    --cmake-option="-DOPTION_TCMALLOC=ON" \
    --no-tests
```

---

## 4. Binary Size Estimates

### 4.1 Full Android Studio Emulator

| Component | Size |
|-----------|------|
| emulator package (sdk-repo-linux-system-images.zip) | 250-300 MB |
| Uncompressed emulator binaries | ~400 MB |
| Qt libraries | ~150 MB |
| SwiftShader/ANGLE | ~50 MB |
| System images (per API level) | 1-2 GB each |

### 4.2 Stripped LinBlock Emulator (Projected)

| Component | Size | Notes |
|-----------|------|-------|
| Core emulator binary | ~40-60 MB | Stripped, no Qt |
| qemu-system-x86_64 | ~15-20 MB | Stripped |
| Required shared libs | ~30-40 MB | virglrenderer, glib, etc. |
| SwiftShader (if kept) | ~25 MB | Software GPU fallback |
| **Total Runtime** | **~100-150 MB** | **50-60% reduction** |

### 4.3 Comparison with Vanilla QEMU

| Variant | Binary Size | Notes |
|---------|-------------|-------|
| QEMU system-x86_64 (Debian package) | ~15 MB | No Android features |
| QEMU + virgl + required libs | ~40 MB | Basic graphics |
| Android Emulator (stripped) | ~100-150 MB | Full Android support |
| Android Emulator (full) | ~400 MB | All features |

**Verdict**: A stripped fork is ~3-4x larger than vanilla QEMU but 2-3x smaller than the full Android Emulator.

---

## 5. Maintenance Burden Assessment

### 5.1 Upstream Activity

- **Repository Status**: The `aosp-mirror/platform_external_qemu` is **archived** (November 2022)
- **Active Development**: Continues at `android.googlesource.com/platform/external/qemu`
- **Release Cadence**: Monthly security patches, quarterly feature releases

### 5.2 Security Patch Integration

**Challenge Level**: HIGH

Security patches flow through multiple layers:
```
Linux Kernel CVEs
       ↓
Upstream QEMU fixes
       ↓
Google's Android Emulator fork
       ↓
LinBlock fork (you are here)
```

**Patch Sources**:
| Source | Frequency | Integration Effort |
|--------|-----------|-------------------|
| QEMU upstream | Monthly | Medium - merge conflicts likely |
| Android security bulletin | Monthly | Low - mostly guest-side |
| Android Emulator releases | Quarterly | High - feature changes |

### 5.3 Recommended Maintenance Strategy

```
Option A: Minimal Fork (RECOMMENDED)
├── Fork from stable release tag (e.g., aosp-emu-34-release)
├── Apply only critical security patches manually
├── Track upstream for major version bumps (yearly)
└── Effort: ~5 hours/month

Option B: Active Tracking
├── Fork from emu-master-dev
├── Regular rebases onto upstream
├── Cherry-pick all security patches
└── Effort: ~20 hours/month

Option C: Snapshot Fork
├── Fork once, never update
├── Accept growing security debt
├── Eventually replace with upstream QEMU
└── Effort: ~0 hours/month (not recommended)
```

### 5.4 Git Workflow for Upstream Sync

```bash
# Initial setup
git remote add upstream https://android.googlesource.com/platform/external/qemu
git fetch upstream --tags

# Create LinBlock branch from stable release
git checkout -b linblock-main aosp-emu-34-release

# Monthly security sync
git fetch upstream
git log upstream/aosp-emu-34-release --oneline --since="1 month ago"
# Cherry-pick relevant security commits
git cherry-pick <commit-hash>
```

---

## 6. LinBlock Build Pipeline Integration

### 6.1 Proposed Directory Structure

```
linblock/
├── src/
│   └── modules/
│       └── emulation/
│           └── emulator_core/
│               ├── interface.py      # Python wrapper API
│               ├── internal/
│               │   └── qemu_bridge.py
│               └── vendor/
│                   └── android-emu/   # Forked emulator (git submodule)
├── build/
│   ├── configs/
│   │   └── emulator_build.yaml
│   └── scripts/
│       ├── build_emulator.sh
│       ├── package_emulator.sh
│       └── update_emulator.sh
└── third_party/
    └── prebuilts/
        └── linux-x86_64/            # Minimal prebuilt set
```

### 6.2 Build Pipeline Stages

```yaml
# .github/workflows/build_emulator.yml (or local CI equivalent)
stages:
  - name: fetch_dependencies
    script: |
      ./build/scripts/fetch_prebuilts.sh linux-x86_64
    cache:
      key: prebuilts-linux-${PREBUILT_VERSION}
      paths:
        - third_party/prebuilts/

  - name: build_emulator
    script: |
      cd src/modules/emulation/emulator_core/vendor/android-emu
      ./android/rebuild.sh \
        --target linux \
        --build-dir=$CI_BUILD_DIR/emulator \
        --prebuilt-dir=$CI_PROJECT_DIR/third_party/prebuilts
    artifacts:
      paths:
        - emulator-linux-x86_64.tar.gz
      expire_in: 7 days

  - name: test_emulator
    script: |
      tar xzf emulator-linux-x86_64.tar.gz
      ./emulator/bin/linblock-emu -version
      ./emulator/bin/linblock-emu -accel-check
    needs: [build_emulator]

  - name: package_linblock
    script: |
      ./build/scripts/assemble_release.sh
    needs: [build_emulator, build_gui, build_android_services]
```

### 6.3 Integration with LinBlock Python Modules

```python
# src/modules/emulation/emulator_core/interface.py

import subprocess
import os
from pathlib import Path

class EmulatorInterface:
    """
    LinBlock interface to the Android Emulator binary.
    Wraps the forked emulator with Python control.
    """

    def __init__(self, emulator_path: Path = None):
        self.emulator_path = emulator_path or self._find_emulator()
        self.process = None

    def _find_emulator(self) -> Path:
        """Locate emulator binary in expected locations."""
        candidates = [
            Path(__file__).parent / "vendor" / "android-emu" / "objs" / "emulator",
            Path("/opt/linblock/bin/emulator"),
            Path.home() / ".linblock" / "emulator" / "bin" / "emulator",
        ]
        for path in candidates:
            if path.exists():
                return path
        raise FileNotFoundError("Emulator binary not found")

    def start(self, avd_name: str, headless: bool = True, **kwargs) -> int:
        """Start emulator instance."""
        cmd = [
            str(self.emulator_path),
            "-avd", avd_name,
            "-no-snapshot-load",
            "-gpu", "swiftshader_indirect",
        ]
        if headless:
            cmd.extend(["-no-window", "-no-audio"])

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=self._get_env()
        )
        return self.process.pid

    def _get_env(self) -> dict:
        """Set up library paths for emulator."""
        env = os.environ.copy()
        lib_path = self.emulator_path.parent.parent / "lib"
        env["LD_LIBRARY_PATH"] = f"{lib_path}:{env.get('LD_LIBRARY_PATH', '')}"
        return env

    def stop(self) -> bool:
        """Stop emulator instance."""
        if self.process:
            self.process.terminate()
            self.process.wait(timeout=10)
            return True
        return False
```

### 6.4 Build Script for LinBlock

```bash
#!/bin/bash
# build/scripts/build_emulator.sh

set -e

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"
EMU_DIR="$PROJECT_ROOT/src/modules/emulation/emulator_core/vendor/android-emu"
BUILD_DIR="$PROJECT_ROOT/build/output/emulator"
PREBUILT_DIR="$PROJECT_ROOT/third_party/prebuilts/linux-x86_64"

echo "=========================================="
echo "LinBlock Emulator Build"
echo "=========================================="

# Check prerequisites
command -v cmake >/dev/null 2>&1 || { echo "cmake required"; exit 1; }
command -v ninja >/dev/null 2>&1 || { echo "ninja required"; exit 1; }

# Fetch prebuilts if not present
if [ ! -d "$PREBUILT_DIR" ]; then
    echo "Fetching prebuilts..."
    ./build/scripts/fetch_prebuilts.sh
fi

# Configure
echo "[1/4] Configuring..."
cd "$EMU_DIR"
cmake -B "$BUILD_DIR" \
    -G Ninja \
    -DCMAKE_BUILD_TYPE=Release \
    -DOPTION_MINBUILD=ON \
    -DWEBRTC=OFF \
    -DQTWEBENGINE=OFF \
    -DOPTION_TCMALLOC=ON \
    -DANDROID_EMULATOR_PREBUILTS="$PREBUILT_DIR"

# Build
echo "[2/4] Building..."
ninja -C "$BUILD_DIR" -j$(nproc)

# Strip
echo "[3/4] Stripping binaries..."
find "$BUILD_DIR" -name "*.so" -exec strip --strip-unneeded {} \;
strip --strip-unneeded "$BUILD_DIR/emulator"

# Package
echo "[4/4] Packaging..."
"$PROJECT_ROOT/build/scripts/package_emulator.sh" "$BUILD_DIR"

echo ""
echo "Build complete: $PROJECT_ROOT/build/output/linblock-emulator.tar.gz"
```

---

## 7. Recommendations Summary

### 7.1 Go / No-Go Decision Matrix

| Factor | Assessment | Recommendation |
|--------|------------|----------------|
| Build complexity | Medium-High | Mitigate with scripts |
| Linux-only feasibility | Good | Simplifies significantly |
| Binary size | Acceptable (100-150 MB) | Within targets |
| Maintenance burden | Medium | Use minimal fork strategy |
| Security updates | Challenging | Cherry-pick critical only |
| Integration effort | Medium | 2-3 weeks for initial setup |

### 7.2 Final Recommendations

1. **Fork Strategy**: Use `aosp-emu-34-release` as base (stable, recent)

2. **Build Approach**:
   - Strip all non-Linux platforms
   - Disable Qt GUI (LinBlock uses GTK)
   - Keep SwiftShader for compatibility
   - Enable KVM and virglrenderer

3. **Integration Method**:
   - Git submodule for emulator fork
   - Python wrapper interface
   - Shared build pipeline with LinBlock modules

4. **Maintenance Plan**:
   - Monthly security review
   - Quarterly upstream sync evaluation
   - Yearly major version consideration

5. **Alternative Consideration**:
   If maintenance proves too burdensome, consider:
   - Upstream QEMU with goldfish patches
   - Cuttlefish (Google's alternative emulator)
   - Container-based Android (Anbox/Waydroid model)

---

## 8. Next Steps

1. [ ] Create proof-of-concept stripped build
2. [ ] Benchmark performance vs full emulator
3. [ ] Test GTK display integration
4. [ ] Establish security patch monitoring
5. [ ] Document build reproducibility

---

## Sources

- [Android Emulator Linux Development](https://android.googlesource.com/platform/external/qemu/+/emu-master-dev/android/docs/LINUX-DEV.md)
- [QEMU-Sideswipe Fork](https://github.com/royalgraphx/qemu-sideswipe)
- [kunpengcompute Android QEMU](https://github.com/kunpengcompute/android-qemu)
- [SecurePatchedEmulator](https://github.com/cxxsheng/SecurePatchedEmulator)
- [Setting Up Minimal Android Emulator](https://blogs.igalia.com/jaragunde/2023/12/setting-up-a-minimal-command-line-android-emulator-on-linux/)
- [Android Emulator Release Notes](https://developer.android.com/studio/releases/emulator)
- [QEMU Official Documentation](https://www.qemu.org/docs/master/system/introduction.html)
