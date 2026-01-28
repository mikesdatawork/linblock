# Phase 1: Emulator Development

Version: 1.0.0
Status: Draft
Last Updated: 2025-01-27

---

## 1. Overview

This document outlines Phase 1 of the LinBlock project: building the emulator core before developing a custom Android OS. This approach follows established emulator development practices and reduces risk by isolating variables during debugging.

### 1.1 Why Emulator First?

Building the emulator before the custom Android OS provides several advantages:

**Known-Good Reference**

When testing with Google's official AOSP images, any failures are definitively emulator bugs. There is no ambiguity. If the same image boots correctly in QEMU or Android Studio's emulator but fails in LinBlock, the problem is in LinBlock's emulator code.

**Faster Iteration**

AOSP builds take hours. Downloading a prebuilt image takes minutes. During early emulator development, you will encounter many failures. Each failure requires testing a fix. Using prebuilt images means faster test cycles.

**Industry Standard Approach**

Every major emulator project follows this pattern:

- QEMU was developed and tested with existing operating systems before any QEMU-specific guest modifications were made
- Android Emulator (goldfish, then ranchu) was built to run stock AOSP
- VirtualBox runs unmodified guest operating systems
- Cuttlefish (Google's reference virtual device) boots standard AOSP images

There are no examples of successful emulator projects that developed a custom OS and custom emulator simultaneously from scratch.

**Reduced Debugging Complexity**

If both emulator and OS are custom and untested, a boot failure could be caused by:

- CPU emulation bug
- Memory mapping error
- Device emulation problem
- Kernel configuration issue
- Init script error
- System service crash
- Driver incompatibility
- Dozens of other possibilities

With a known-good OS image, the list of suspects is cut in half.

---

## 2. Phase 1 Goals

By the end of Phase 1, LinBlock will:

1. Boot a stock AOSP x86_64 system image to the launcher
2. Display the Android screen in a GTK window
3. Accept mouse input translated to touch events
4. Accept keyboard input
5. Provide basic emulator controls (start, stop, restart)
6. Achieve acceptable performance (30fps UI, <30s boot)

Phase 1 explicitly does NOT include:

- Custom Android OS
- App permission management
- Process freezing
- Network restrictions
- Any LinBlock-specific Android modifications

---

## 3. Test Images

### 3.1 Recommended Test Images

Use official Google AOSP prebuilt images for x86_64:

**Primary Test Image: AOSP x86_64 Generic System Image (GSI)**

Google provides Generic System Images for testing. These are vanilla AOSP without vendor customizations.

Download location:
```
https://ci.android.com/builds/branches/aosp-android14-gsi/grid
```

Select:
- Branch: aosp-android14-gsi
- Target: aosp_x86_64-userdebug
- Artifact: system image files

**Alternative: Android Studio AVD Images**

Android Studio includes prebuilt system images. These can be extracted and used directly.

Location after Android Studio installation:
```
~/.android/avd/
```

Or download via SDK Manager:
```
sdkmanager "system-images;android-34;google_apis;x86_64"
```

**Alternative: LineageOS x86_64**

LineageOS provides x86_64 builds that are closer to LinBlock's eventual target.

```
https://download.lineageos.org/
```

Look for x86_64 or generic targets.

### 3.2 Image Requirements

For LinBlock emulator testing, images must:

| Requirement | Reason |
|-------------|--------|
| x86_64 architecture | LinBlock targets x86_64 only |
| API 34 (Android 14) | Target Android version |
| Userdebug or eng build | Allows ADB root, debugging |
| No Google Play Services | Simpler, matches LinBlock goals |

### 3.3 Image Storage

Store test images in a dedicated location:

```
/mnt/data/linblock-images/
├── aosp/
│   ├── android14-x86_64-gsi/
│   │   ├── system.img
│   │   ├── vendor.img
│   │   └── boot.img
│   └── android14-x86_64-sdk/
│       └── ...
├── lineage/
│   └── lineage-21-x86_64/
│       └── ...
└── test/
    └── minimal-kernel-test/
        └── ...
```

This keeps images organized and separate from the LinBlock source code.

---

## 4. Development Stages

Phase 1 is divided into stages. Each stage builds on the previous and has clear success criteria.

### 4.1 Stage 1: Host Verification

**Objective**: Confirm the host system can run Android x86_64 under KVM.

**Tasks**:

1. Verify KVM is available and enabled
2. Install QEMU for reference testing
3. Download AOSP x86_64 image
4. Boot image using QEMU directly
5. Document working QEMU command line

**Success Criteria**:

- `/dev/kvm` exists and is accessible
- QEMU boots AOSP image to launcher
- Touch input works in QEMU
- Boot time under 60 seconds

**Commands**:

```bash
# Check KVM availability
ls -la /dev/kvm
lsmod | grep kvm

# Install QEMU for reference
sudo apt install qemu-system-x86 qemu-utils

# Test boot (example, adjust paths)
qemu-system-x86_64 \
    -enable-kvm \
    -m 4096 \
    -smp 4 \
    -cpu host \
    -drive file=system.img,format=raw \
    -device virtio-gpu-gl \
    -display gtk,gl=on
```

This stage produces documentation only. No LinBlock code is written. The goal is to validate the environment and understand what a working boot looks like.

### 4.2 Stage 2: Minimal Emulator Core

**Objective**: Create LinBlock's emulator core that boots to kernel output.

**Tasks**:

1. Create `emulator_core` module structure
2. Implement KVM wrapper for CPU virtualization
3. Implement basic memory manager (allocate guest RAM)
4. Implement serial console output (for kernel logs)
5. Boot a minimal Linux kernel (not Android yet)

**Success Criteria**:

- LinBlock initializes KVM virtual machine
- Guest kernel boots and outputs to serial console
- Memory is correctly mapped
- Clean shutdown without crashes

**Why Not Android Yet**:

A minimal Linux kernel (like a buildroot image) boots in seconds and produces clear serial output. This allows testing the fundamental virtualization layer without Android's complexity. If the kernel panics, the message appears on the serial console.

**Module**: `src/modules/emulation/emulator_core/`

**Key Components**:

```
emulator_core/
├── interface.py          # Public abstraction layer
├── internal/
│   ├── kvm_wrapper.py    # KVM ioctl interface
│   ├── vcpu.py           # Virtual CPU management
│   └── memory.py         # Guest memory management
├── tests/
│   └── test_kvm_init.py  # Verify KVM initialization
└── mocks/
    └── mock_interface.py # Testing mock
```

### 4.3 Stage 3: Device Framework

**Objective**: Implement virtual device infrastructure.

**Tasks**:

1. Create `device_manager` module
2. Define device abstraction layer
3. Implement virtio-console (serial)
4. Implement virtio-blk (storage)
5. Boot minimal Linux with mounted filesystem

**Success Criteria**:

- Devices register with device manager
- Storage device allows reading disk image
- Serial console captures kernel output
- Kernel mounts root filesystem

**Module**: `src/modules/emulation/device_manager/`

**Device Abstraction Layer**:

```python
class VirtualDevice(ABC):
    """Base class for all virtual devices."""
    
    @abstractmethod
    def initialize(self, vm: VirtualMachine) -> None:
        """Initialize device for given VM."""
        pass
    
    @abstractmethod
    def handle_io(self, port: int, data: bytes, is_write: bool) -> bytes:
        """Handle I/O operation."""
        pass
    
    @abstractmethod
    def reset(self) -> None:
        """Reset device to initial state."""
        pass
```

### 4.4 Stage 4: Display Output

**Objective**: Render graphical output from the emulator.

**Tasks**:

1. Create `display_manager` module
2. Implement virtio-gpu device
3. Create framebuffer capture mechanism
4. Create basic GTK window to display framebuffer
5. Boot Android and see graphical output

**Success Criteria**:

- Android boot animation appears
- Launcher renders correctly
- Frame rate is measurable (even if slow)
- No graphical corruption

**Module**: `src/modules/emulation/display_manager/`

**This is the first test with real Android image**.

At this stage, switch from minimal Linux to AOSP x86_64 GSI. Expect initial failures. This is normal.

Common issues at this stage:

| Symptom | Likely Cause |
|---------|--------------|
| Black screen | GPU device not recognized |
| Boot loop | Kernel panic, check serial log |
| Frozen on logo | System services crashing |
| Corrupted display | Framebuffer format mismatch |

### 4.5 Stage 5: Input Handling

**Objective**: Accept user input and translate to Android events.

**Tasks**:

1. Create `input_manager` module
2. Implement virtio-input device
3. Capture GTK mouse events
4. Translate mouse to touch events
5. Capture keyboard events
6. Translate to Android key events

**Success Criteria**:

- Tap on screen registers as touch
- Swipe gestures work
- Keyboard input appears in text fields
- Back/home/recent buttons work

**Module**: `src/modules/emulation/input_manager/`

**Input Translation**:

```
GTK Event              Android Event
-----------------------------------------
button-press-event  -> ACTION_DOWN (touch)
motion-notify       -> ACTION_MOVE (touch)
button-release      -> ACTION_UP (touch)
key-press-event     -> KeyEvent (keycode)
scroll-event        -> ACTION_SCROLL
```

### 4.6 Stage 6: Network Emulation

**Objective**: Provide network connectivity to the guest.

**Tasks**:

1. Create `network_manager` module
2. Implement virtio-net device
3. Configure user-mode networking (SLIRP-style)
4. Test connectivity from Android

**Success Criteria**:

- Android shows WiFi/Ethernet connected
- Can ping external hosts
- Can browse web (if browser installed)
- ADB over network functions

**Module**: `src/modules/emulation/network_manager/`

**Network Modes**:

For Phase 1, implement user-mode networking only:

```
Guest                LinBlock              Host              Internet
  |                     |                    |                   |
  |-- virtio-net ------>|                    |                   |
  |                     |-- NAT translation->|                   |
  |                     |                    |-- socket -------->|
```

User-mode networking requires no root privileges and no host configuration. It is sufficient for testing.

### 4.7 Stage 7: Storage Management

**Objective**: Provide persistent storage that survives restarts.

**Tasks**:

1. Create `storage_manager` module
2. Implement qcow2 or raw image handling
3. Support read-only base images
4. Support writable overlay images
5. Test data persistence across restarts

**Success Criteria**:

- Apps can be installed
- Data persists after clean restart
- Overlay image captures changes
- Base image remains unmodified

**Module**: `src/modules/emulation/storage_manager/`

**Storage Architecture**:

```
                    +-----------------+
                    | Writable Layer  |  <- User data, installed apps
                    | (overlay.qcow2) |
                    +-----------------+
                            |
                    +-----------------+
                    | Base Image      |  <- Read-only AOSP system
                    | (system.img)    |
                    +-----------------+
```

This copy-on-write approach allows:

- Multiple instances sharing one base image
- Quick reset by deleting overlay
- Smaller storage footprint

### 4.8 Stage 8: GUI Integration

**Objective**: Wrap emulator in complete GTK interface.

**Tasks**:

1. Create `gui_core` module (if not already exists)
2. Create `gui_display` module
3. Integrate display widget with emulator
4. Add control buttons (start, stop, restart)
5. Add status indicators
6. Test complete workflow

**Success Criteria**:

- Launch LinBlock application
- Click start, Android boots
- Use Android via GUI
- Click stop, Android shuts down
- All controls function correctly

**Modules**: `src/modules/gui/gui_core/`, `src/modules/gui/gui_display/`

---

## 5. Testing Strategy

### 5.1 Test Levels

Each stage has three test levels:

**Unit Tests**

Test individual functions and classes in isolation. Mock all dependencies.

```python
def test_kvm_init_returns_fd():
    kvm = KVMWrapper()
    fd = kvm.open()
    assert fd > 0
```

**Integration Tests**

Test module combinations. Use real implementations but controlled inputs.

```python
def test_vm_boots_minimal_kernel():
    core = create_emulator_core(config)
    devices = create_device_manager(config)
    
    core.load_kernel("test_kernel.bin")
    core.start()
    
    output = devices.get_serial_output(timeout=10)
    assert "Linux version" in output
```

**System Tests**

Test complete emulator with real Android image.

```python
def test_android_boots_to_launcher():
    emulator = LinBlockEmulator(config)
    emulator.load_image("aosp-x86_64.img")
    emulator.start()
    
    # Wait for boot
    assert emulator.wait_for_boot(timeout=60)
    
    # Verify launcher via ADB
    result = emulator.adb("shell dumpsys window | grep mCurrentFocus")
    assert "Launcher" in result
```

### 5.2 Test Images for Each Stage

| Stage | Test Image |
|-------|------------|
| 1 (Host Verify) | AOSP via QEMU (reference) |
| 2 (Emulator Core) | Minimal Linux kernel |
| 3 (Devices) | Minimal Linux + initrd |
| 4 (Display) | AOSP x86_64 GSI |
| 5 (Input) | AOSP x86_64 GSI |
| 6 (Network) | AOSP x86_64 GSI |
| 7 (Storage) | AOSP x86_64 GSI |
| 8 (GUI) | AOSP x86_64 GSI |

### 5.3 Performance Benchmarks

Track these metrics throughout Phase 1:

| Metric | Target | Acceptable |
|--------|--------|------------|
| Boot time (to launcher) | 20s | 30s |
| Memory usage (idle) | 2GB | 3GB |
| Memory usage (active) | 3GB | 4GB |
| Frame rate | 30fps | 24fps |
| Input latency | 30ms | 50ms |

Run benchmarks after each stage to catch performance regressions.

---

## 6. Host System Preparation

### 6.1 Required Packages

Install on Linux Mint 22.2 / Ubuntu 24.04:

```bash
# Virtualization
sudo apt install qemu-system-x86 qemu-utils
sudo apt install libvirt-daemon virt-manager

# Build tools
sudo apt install build-essential cmake ninja-build
sudo apt install python3-dev python3-pip python3-venv

# GTK development
sudo apt install libgtk-3-dev python3-gi python3-gi-cairo
sudo apt install gir1.2-gtk-3.0

# Android tools
sudo apt install adb fastboot

# Testing
sudo apt install python3-pytest python3-pytest-cov
```

### 6.2 KVM Access

Add user to kvm group:

```bash
sudo usermod -aG kvm $USER
# Log out and back in
```

Verify:

```bash
ls -la /dev/kvm
# Should show group kvm with rw permissions

groups
# Should include kvm
```

### 6.3 Resource Limits

Check ulimits for large memory allocations:

```bash
ulimit -l
# Should be "unlimited" or at least 4194304 (4GB in KB)

# If limited, add to /etc/security/limits.conf:
# username  hard  memlock  unlimited
# username  soft  memlock  unlimited
```

### 6.4 Directory Setup

```bash
# Project directory
mkdir -p /home/user/projects/linblock

# Image storage (on large partition)
mkdir -p /mnt/data/linblock-images/aosp
mkdir -p /mnt/data/linblock-images/test

# Build artifacts
mkdir -p /mnt/data/linblock-build
```

---

## 7. Risk Mitigation

### 7.1 Known Risks

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| KVM not available | Low | High | Check early in Stage 1 |
| GPU passthrough issues | Medium | Medium | Fall back to software rendering |
| Memory pressure (12GB host) | Medium | Medium | Careful guest allocation, max 4GB |
| AOSP image incompatibility | Low | Medium | Test multiple image sources |
| Performance too slow | Medium | Medium | Profile early, optimize critical paths |

### 7.2 Fallback Strategies

**If KVM unavailable**:

Some systems (nested VMs, older CPUs) lack KVM. Fallback to software emulation. Performance will be poor but functional.

**If GPU passthrough fails**:

virtio-gpu with OpenGL can fail on some hosts. Fallback to:
1. virtio-gpu without GL
2. Simple framebuffer device
3. VNC output

**If memory insufficient**:

12GB host RAM with 4GB guest leaves 8GB for host. If swap thrashing occurs:
1. Reduce guest RAM to 3GB
2. Close other applications
3. Add swap space
4. Accept slower performance

---

## 8. Deliverables

Phase 1 completion requires:

### 8.1 Code

- `emulator_core` module - complete and tested
- `device_manager` module - complete and tested
- `display_manager` module - complete and tested
- `input_manager` module - complete and tested
- `network_manager` module - complete and tested
- `storage_manager` module - complete and tested
- `gui_core` module - basic implementation
- `gui_display` module - basic implementation

### 8.2 Documentation

- Architecture document for each module
- Abstraction layer specification for each module
- Test coverage report
- Performance benchmark results
- Known issues and limitations

### 8.3 Artifacts

- Working LinBlock application
- Test image collection
- Automated test suite
- CI/CD pipeline (basic)

---

## 9. Timeline Estimate

Rough estimates assuming one developer:

| Stage | Duration | Cumulative |
|-------|----------|------------|
| Stage 1: Host Verify | 1-2 days | 2 days |
| Stage 2: Emulator Core | 2-3 weeks | 3 weeks |
| Stage 3: Device Framework | 1-2 weeks | 5 weeks |
| Stage 4: Display | 1-2 weeks | 7 weeks |
| Stage 5: Input | 1 week | 8 weeks |
| Stage 6: Network | 1 week | 9 weeks |
| Stage 7: Storage | 1 week | 10 weeks |
| Stage 8: GUI | 1-2 weeks | 12 weeks |

Total: approximately 3 months for Phase 1.

These estimates assume:
- Part-time work (not full-time)
- Learning curve for KVM/virtualization
- Debugging time for unexpected issues

---

## 10. Success Criteria Summary

Phase 1 is complete when:

1. LinBlock boots official AOSP x86_64 image to launcher
2. Display renders at 30fps with no corruption
3. Touch and keyboard input work correctly
4. Network connectivity functions
5. Storage persists across restarts
6. Boot time under 30 seconds
7. Memory usage under 4GB
8. All modules have 70%+ test coverage
9. Documentation is complete

Once these criteria are met, Phase 2 (Custom Android OS) begins.

---

## 11. Next Phase Preview

Phase 2 will:

1. Set up AOSP build environment
2. Create LinBlock device tree
3. Build minimal AOSP image
4. Integrate permission management hooks
5. Add app control capabilities
6. Replace test images with custom LinBlock OS

Phase 2 depends on a working, stable emulator from Phase 1. Do not begin Phase 2 until Phase 1 success criteria are fully met.
