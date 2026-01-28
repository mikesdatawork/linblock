# Agent Activation Checklist

> Initial task assignments and expected deliverables for all 10 LinBlock agents.

---

## Activation Overview

Each agent produces concrete deliverables during its first activation cycle.
Deliverables are written to the repository under the paths noted below.

| Status | Meaning |
|--------|---------|
| `[ ]`  | Not started |
| `[-]`  | In progress |
| `[x]`  | Complete |

---

## Agent 001 -- Technical Program Manager

**Config:** `agents/configs/agent_01_technical_program_manager.md`

### Initial Deliverables

- [ ] **Project roadmap** -- `docs/planning/roadmap.md`
  - Phase breakdown with objectives and exit criteria
  - Dependency graph between phases
  - Critical path identification
- [ ] **Phase 1 milestones** -- `docs/planning/phase1_milestones.md`
  - Milestone definitions with measurable acceptance criteria
  - Assigned agent ownership per milestone
  - Weekly checkpoint schedule
- [ ] **Risk register** -- `docs/planning/risk_register.md`
  - Identified technical risks (emulation performance, AOSP compatibility, host driver issues)
  - Probability and impact ratings
  - Mitigation strategies per risk

---

## Agent 002 -- Android Platform Architect

**Config:** `agents/configs/agent_02_android_platform_architect.md`

### Initial Deliverables

- [ ] **Android 14 baseline configuration** -- `android/base/android14_baseline.md`
  - Target API level and build fingerprint
  - System property overrides for emulated environment
  - Hardware abstraction layer (HAL) stubs required
- [ ] **Minimal services manifest** -- `android/base/minimal_services.md`
  - List of system services to enable at boot (minimal set)
  - Services to disable or stub for emulation
  - Google services integration points (all disabled by default)
- [ ] **Partition layout** -- `android/base/partition_layout.md`
  - Partition table (system, vendor, data, cache, boot)
  - Image sizes and filesystem types
  - Shared storage mount points

---

## Agent 003 -- Virtualization Engineer

**Config:** `agents/configs/agent_03_virtualization_engineer.md`

### Initial Deliverables

- [ ] **Emulator architecture document** -- `docs/design/emulator_architecture.md`
  - Component diagram (CPU, memory, devices, display pipeline)
  - KVM integration approach vs software fallback
  - Virtio device strategy (GPU, network, input, storage)
- [ ] **CPU module skeleton** -- `src/emulator/cpu/cpu_module.py`
  - Abstract interface for CPU emulation backend
  - KVM backend class stub
  - Software emulation backend class stub
- [ ] **Memory management approach** -- `docs/design/memory_management.md`
  - Guest memory allocation strategy
  - Shared memory for framebuffer transfer to GTK display
  - Memory ballooning support plan

---

## Agent 004 -- Linux Systems Engineer

**Config:** `agents/configs/agent_04_linux_systems_engineer.md`

### Initial Deliverables

- [ ] **Prerequisite checker script** -- `scripts/setup/check_prerequisites.sh`
  - Detect host CPU features (VT-x / AMD-V)
  - Verify KVM module loaded
  - Check required packages (qemu-utils, libvirt, bridge-utils)
  - Validate Python 3.10+ and PyGObject availability
  - Report pass/fail with remediation instructions
- [ ] **KVM setup script** -- `scripts/setup/setup_kvm.sh`
  - Load KVM kernel modules
  - Configure /dev/kvm permissions
  - Add current user to kvm group
  - Verify nested virtualization if applicable
- [ ] **Memory tuning document** -- `docs/guides/memory_tuning.md`
  - Recommended host memory configuration
  - Hugepages setup instructions
  - Kernel parameter tuning (vm.swappiness, transparent hugepages)
  - OOM killer configuration for emulator process

---

## Agent 005 -- Security Hardening Specialist

**Config:** `agents/configs/agent_05_security_hardening_specialist.md`

### Initial Deliverables

- [ ] **Threat model** -- `docs/security/threat_model.md`
  - Attack surface analysis (host-guest boundary, ADB, shared storage, network bridge)
  - Threat actors and scenarios
  - STRIDE analysis for each component
  - Data flow diagrams with trust boundaries
- [ ] **SELinux requirements** -- `docs/security/selinux_requirements.md`
  - SELinux policy requirements for guest Android
  - Host-side SELinux/AppArmor considerations
  - Mandatory access control strategy
- [ ] **Permission architecture** -- `docs/security/permission_architecture.md`
  - Android permission model enforcement in emulated environment
  - Per-app permission control API design
  - Permission audit logging specification

---

## Agent 006 -- GTK / Python Developer

**Config:** `agents/configs/agent_06_gtk_python_developer.md`

### Initial Deliverables

- [ ] **Adapted dashboard skeleton** -- `src/ui/dashboard_window.py`, `src/ui/sidebar.py`, `src/ui/content_area.py`
  - Port gtk-python-dashboard-starter template to LinBlock
  - Sidebar with logo, static buttons (About, Load OS, OS List)
  - Content area with Gtk.Stack for page switching
  - Dynamic sidebar button support for saved OS profiles
- [ ] **Emulator control page** -- `src/pages/running_os_page.py`, `src/ui/components/device_controls.py`
  - Running OS page layout (controls panel + display area)
  - Always-present controls: On/Off, Save State, Reset, Screenshot, Record Video
  - Conditional controls: Settings, WiFi, Bluetooth, Airplane Mode, Auto-Rotate, Brightness, Volume, Do Not Disturb, Location, Battery
  - Grayed-out state for disabled controls
- [ ] **Display widget prototype** -- `src/ui/components/emulator_display.py`
  - Gtk.DrawingArea subclass for framebuffer rendering
  - Mouse-to-touch event translation
  - Keyboard-to-key event translation
  - Placeholder rendering (static image) for Phase 1 testing

---

## Agent 007 -- Android Build Engineer

**Config:** `agents/configs/agent_07_android_build_engineer.md`

### Initial Deliverables

- [ ] **AOSP fetch procedure** -- `docs/guides/aosp_fetch.md`
  - repo init and sync commands for Android 14 (API 34)
  - Recommended branch and manifest
  - Disk space and time estimates
  - Mirror setup for repeated builds
- [ ] **Device tree structure** -- `android/vendor/linblock/`
  - BoardConfig.mk skeleton
  - device.mk with emulator-specific settings
  - vendorsetup.sh for lunch target registration
  - AndroidProducts.mk listing build combinations
- [ ] **Build setup script** -- `scripts/setup/setup_aosp_build.sh`
  - Install build dependencies (Ubuntu/Debian)
  - Set environment variables
  - Configure ccache
  - Validate Java version

---

## Agent 008 -- App Management Developer

**Config:** `agents/configs/agent_08_app_management_developer.md`

### Initial Deliverables

- [ ] **Permission data model** -- `src/app-manager/permissions/permission_model.py`
  - Permission categories (normal, dangerous, signature, privileged)
  - Per-app permission state (granted, denied, ask)
  - Permission group definitions matching Android 14 groups
- [ ] **App state API** -- `src/app-manager/process/app_state_api.py`
  - Abstract interface for querying installed apps
  - App lifecycle states (installed, running, stopped, frozen)
  - Methods: list_apps, get_app_info, freeze_app, unfreeze_app
- [ ] **Audit log format** -- `docs/design/audit_log_format.md`
  - Log entry schema (timestamp, app, action, permission, result)
  - Storage format (JSON lines)
  - Retention and rotation policy
  - Query interface specification

---

## Agent 009 -- QA / Test Automation Lead

**Config:** `agents/configs/agent_09_qa_test_automation_lead.md`

### Initial Deliverables

- [ ] **Test strategy document** -- `docs/design/test_strategy.md`
  - Testing levels (unit, integration, system, acceptance)
  - Test frameworks and tools (pytest, pytest-cov, GTK test utilities)
  - Coverage targets per module
  - CI integration requirements
- [ ] **Test folder structure** -- `tests/`
  - Directory layout matching src/ module structure
  - conftest.py with shared fixtures
  - pytest.ini configuration
  - Sample unit test demonstrating conventions
- [ ] **Performance benchmark suite** -- `tests/performance/`
  - Boot time benchmark script
  - Frame rate measurement utility
  - Memory usage profiler wrapper
  - Benchmark result format and comparison tool

---

## Agent 010 -- DevOps Engineer

**Config:** `agents/configs/agent_10_devops_engineer.md`

### Initial Deliverables

- [ ] **GitHub Actions workflow** -- `.github/workflows/ci.yml`
  - Lint (flake8 / pylint) on push and PR
  - Unit tests with pytest
  - Coverage reporting
  - Build validation (import checks, dependency resolution)
- [ ] **Artifact storage layout** -- `docs/design/artifact_storage.md`
  - Build artifact naming convention
  - Release artifact types (AOSP images, GTK app bundle, scripts)
  - GitHub Releases structure
  - Artifact retention policy
- [ ] **Release procedure** -- `docs/guides/release_procedure.md`
  - Semantic versioning strategy
  - Branch and tag conventions
  - Changelog generation process
  - Release checklist (tests pass, docs updated, artifacts uploaded)

---

## Activation Sequence

Recommended order for initial activation to respect dependencies:

```
Phase A (no dependencies):
  001 TPM           -- creates planning framework
  005 Security      -- threat model informs all agents
  009 QA Lead       -- test strategy informs all agents
  010 DevOps        -- CI pipeline needed early

Phase B (depends on Phase A):
  002 Android Arch  -- needs threat model input
  003 Virtualization -- needs threat model input
  004 Linux Systems  -- independent but benefits from planning

Phase C (depends on Phase B):
  006 GTK Developer  -- needs architecture decisions
  007 Build Engineer -- needs Android baseline config
  008 App Management -- needs permission architecture
```

---

## Tracking

Progress on this checklist is tracked by updating the checkbox status above.
Each agent updates their own section upon completing deliverables.

Last updated: 2026-01-27
