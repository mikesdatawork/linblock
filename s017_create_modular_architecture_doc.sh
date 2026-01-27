#!/bin/bash
# s017_create_modular_architecture_doc.sh
# Creates docs/design/modular_architecture.md

PROJECT_ROOT="/home/user/projects/linblock"

cat > "$PROJECT_ROOT/docs/design/modular_architecture.md" << 'EOF'
# LinBlock Modular Architecture Design

Version: 1.0.0
Status: Draft
Last Updated: 2025-01-27

---

## 1. Overview

LinBlock uses a strict modular architecture. Each module is an isolated unit with defined boundaries, minimal dependencies, and independent build capability.

### 1.1 Core Principles

1. **Isolation** - Modules do not share internal state
2. **Defined Interfaces** - All communication through documented APIs
3. **Independent Builds** - Each module compiles/runs without others
4. **No Circular Dependencies** - Dependency graph is acyclic
5. **Replaceable** - Any module can be swapped with compatible implementation

### 1.2 Goals

- Parallel development across team members
- Isolated testing per module
- Reduced regression risk
- Clear ownership boundaries
- Simplified debugging

---

## 2. Module Definition

### 2.1 What Constitutes a Module

A module is:
- A self-contained unit of functionality
- Has a single responsibility
- Exposes a public interface
- Hides internal implementation
- Can be versioned independently

### 2.2 Module Structure

Every module follows this structure:

```
module_name/
├── README.md           # Module documentation (required)
├── INTERFACE.md        # Public API specification (required)
├── CHANGELOG.md        # Version history (required)
├── __init__.py         # Module entry point
├── interface.py        # Public API implementation
├── internal/           # Private implementation
│   └── ...
├── tests/              # Module-specific tests
│   ├── test_interface.py
│   └── test_internal.py
├── mocks/              # Mock implementations for testing
│   └── mock_interface.py
└── requirements.txt    # Module-specific dependencies
```

### 2.3 Module Documentation Requirements

Each module README.md must contain:

```markdown
# Module: [name]

## Purpose
[Single sentence describing what this module does]

## Responsibility
[Bullet list of what this module is responsible for]

## Not Responsible For
[Bullet list of what this module explicitly does NOT do]

## Dependencies
[List of other modules this depends on, ideally zero or minimal]

## Interface Summary
[Brief description of public API]

## Usage Example
[Code example showing basic usage]

## Build Instructions
[How to build/run this module independently]

## Test Instructions
[How to run module tests in isolation]
```

---

## 3. Module Inventory

### 3.1 Core Modules

| Module | Layer | Responsibility | Dependencies |
|--------|-------|----------------|--------------|
| emulator_core | Emulation | CPU/memory virtualization | None |
| device_manager | Emulation | Virtual device lifecycle | emulator_core (interface only) |
| display_manager | Emulation | Framebuffer rendering | None |
| input_manager | Emulation | Input event translation | None |
| storage_manager | Emulation | Disk image handling | None |
| network_manager | Emulation | Network emulation | None |

### 3.2 Android Modules

| Module | Layer | Responsibility | Dependencies |
|--------|-------|----------------|--------------|
| android_image | Android | System image management | None |
| permission_manager | Android | Permission enforcement | None |
| app_manager | Android | App lifecycle control | permission_manager (interface only) |
| process_manager | Android | Process freeze/control | None |

### 3.3 GUI Modules

| Module | Layer | Responsibility | Dependencies |
|--------|-------|----------------|--------------|
| gui_core | GUI | Window management | None |
| gui_display | GUI | Emulator display widget | display_manager (interface only) |
| gui_apps | GUI | App management UI | app_manager (interface only) |
| gui_permissions | GUI | Permission control UI | permission_manager (interface only) |
| gui_settings | GUI | Configuration UI | None |

### 3.4 Infrastructure Modules

| Module | Layer | Responsibility | Dependencies |
|--------|-------|----------------|--------------|
| config_manager | Infra | Configuration loading | None |
| log_manager | Infra | Logging infrastructure | None |
| event_bus | Infra | Inter-module messaging | None |

---

## 4. Dependency Rules

### 4.1 Allowed Dependencies

```
┌─────────────────────────────────────────────────────┐
│                      GUI Layer                       │
│  (can depend on: Android interfaces, Emulation      │
│   interfaces, Infrastructure)                        │
├─────────────────────────────────────────────────────┤
│                   Android Layer                      │
│  (can depend on: Infrastructure only)               │
├─────────────────────────────────────────────────────┤
│                  Emulation Layer                     │
│  (can depend on: Infrastructure only)               │
├─────────────────────────────────────────────────────┤
│                Infrastructure Layer                  │
│  (can depend on: Nothing - base layer)              │
└─────────────────────────────────────────────────────┘
```

### 4.2 Dependency Types

**Hard Dependency**: Module cannot function without it
- Minimize these
- Must be documented
- Must use interface only

**Soft Dependency**: Module works without it but with reduced features
- Preferred over hard dependencies
- Graceful degradation required
- Feature flags control behavior

**No Dependency**: Module is fully standalone
- Ideal state
- Communicate via event bus if needed

### 4.3 Forbidden Patterns

1. **Circular dependencies** - Never allowed
2. **Cross-layer direct access** - Use interfaces
3. **Shared mutable state** - No globals
4. **Implicit dependencies** - All must be declared
5. **Version coupling** - Depend on interfaces, not implementations

---

## 5. Interface Design

### 5.1 Interface Contract

Each module's INTERFACE.md defines:

```markdown
# Module Interface: [name]

## Version
[Semantic version of this interface]

## Stability
[stable | beta | experimental]

## Methods

### method_name(param1: type, param2: type) -> return_type
Description of what this method does.

**Parameters:**
- param1: Description
- param2: Description

**Returns:**
Description of return value

**Raises:**
- ErrorType: When this occurs

**Example:**
```python
result = module.method_name("value", 123)
```
```

### 5.2 Interface Versioning

- Interfaces use semantic versioning (MAJOR.MINOR.PATCH)
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes only

### 5.3 Interface Isolation

```python
# CORRECT: Import interface only
from emulator_core.interface import EmulatorInterface

# WRONG: Import internal implementation
from emulator_core.internal.cpu import CPUEmulator
```

---

## 6. Communication Patterns

### 6.1 Event Bus

Modules communicate through a central event bus for loose coupling.

```
Module A                Event Bus               Module B
    |                       |                       |
    |-- publish(event) ---->|                       |
    |                       |---- deliver(event) -->|
    |                       |                       |
```

Event structure:
```python
{
    "type": "event.category.action",
    "source": "module_name",
    "timestamp": "ISO8601",
    "payload": { ... }
}
```

### 6.2 Direct Interface Calls

For synchronous operations where response is needed:

```python
# Consumer module
class AppManagerUI:
    def __init__(self, app_manager: AppManagerInterface):
        self.app_manager = app_manager
    
    def refresh_apps(self):
        apps = self.app_manager.list_installed()
        self.render(apps)
```

### 6.3 No Shared State

Modules do not share:
- Global variables
- Singletons (except event bus)
- File handles
- Database connections

Each module manages its own state.

---

## 7. Build Process

### 7.1 Independent Module Build

Each module can be built in isolation:

```bash
# Build single module
cd src/modules/emulator_core
python -m build

# Run module tests
pytest tests/

# Check module dependencies
pip-audit -r requirements.txt
```

### 7.2 Module Build Script Template

```bash
#!/bin/bash
# build_module.sh - Standard module build script

MODULE_NAME="$1"
MODULE_DIR="src/modules/$MODULE_NAME"

if [ ! -d "$MODULE_DIR" ]; then
    echo "Module not found: $MODULE_NAME"
    exit 1
fi

cd "$MODULE_DIR"

echo "Building module: $MODULE_NAME"

# Install dependencies
pip install -r requirements.txt

# Run linter
flake8 . --max-line-length=100

# Run tests
pytest tests/ -v

# Build package
python -m build

echo "Module build complete: $MODULE_NAME"
```

### 7.3 Full System Build

System build assembles modules:

```bash
# Build order respects dependency graph
# Infrastructure -> Emulation -> Android -> GUI

./build/scripts/build_all.sh

# Build order:
# 1. config_manager
# 2. log_manager
# 3. event_bus
# 4. emulator_core
# 5. device_manager
# 6. display_manager
# ... etc
```

### 7.4 Dependency Graph Validation

Before build, validate no circular dependencies:

```bash
./build/scripts/check_dependencies.sh

# Output:
# Checking dependency graph...
# emulator_core: OK (no dependencies)
# device_manager: OK (depends on emulator_core interface)
# gui_display: OK (depends on display_manager interface)
# ...
# All modules: PASS
```

---

## 8. Testing Strategy

### 8.1 Module Testing Levels

```
┌─────────────────────────────────────────┐
│         Integration Tests               │  <- Minimal, test module boundaries
├─────────────────────────────────────────┤
│          Interface Tests                │  <- Test public API contracts
├─────────────────────────────────────────┤
│           Unit Tests                    │  <- Test internal logic
└─────────────────────────────────────────┘
```

### 8.2 Mock Strategy

Each module provides its own mock:

```python
# emulator_core/mocks/mock_interface.py

class MockEmulatorInterface:
    """Mock implementation for testing consumers"""
    
    def __init__(self):
        self.started = False
        self.calls = []
    
    def start(self):
        self.calls.append("start")
        self.started = True
        return True
    
    def stop(self):
        self.calls.append("stop")
        self.started = False
        return True
```

Consumer modules use these mocks:

```python
# gui_display/tests/test_display_widget.py

from emulator_core.mocks import MockEmulatorInterface

def test_display_starts_emulator():
    mock_emu = MockEmulatorInterface()
    widget = DisplayWidget(emulator=mock_emu)
    
    widget.on_start_clicked()
    
    assert "start" in mock_emu.calls
```

### 8.3 No Cross-Module Test Dependencies

Tests must not:
- Require other modules to be running
- Share test fixtures across modules
- Access other module internals

---

## 9. Module Development Workflow

### 9.1 Creating a New Module

1. Create module directory structure
2. Write README.md with responsibility definition
3. Define interface in INTERFACE.md
4. Implement mock first
5. Write interface tests against mock
6. Implement real interface
7. Write unit tests for internals
8. Register module in build system

### 9.2 Modifying Existing Module

1. Check if change affects interface
2. If interface change:
   - Update INTERFACE.md
   - Update version (MAJOR if breaking)
   - Update mock
   - Notify dependent module owners
3. Implement change
4. Update tests
5. Update CHANGELOG.md

### 9.3 Module Review Checklist

- [ ] README.md complete and accurate
- [ ] INTERFACE.md defines all public methods
- [ ] No imports from other module internals
- [ ] All dependencies declared in requirements.txt
- [ ] Mock provided and functional
- [ ] Tests pass in isolation
- [ ] No circular dependencies introduced
- [ ] CHANGELOG.md updated

---

## 10. Directory Structure

```
linblock/
├── src/
│   └── modules/
│       ├── infrastructure/
│       │   ├── config_manager/
│       │   ├── log_manager/
│       │   └── event_bus/
│       ├── emulation/
│       │   ├── emulator_core/
│       │   ├── device_manager/
│       │   ├── display_manager/
│       │   ├── input_manager/
│       │   ├── storage_manager/
│       │   └── network_manager/
│       ├── android/
│       │   ├── android_image/
│       │   ├── permission_manager/
│       │   ├── app_manager/
│       │   └── process_manager/
│       └── gui/
│           ├── gui_core/
│           ├── gui_display/
│           ├── gui_apps/
│           ├── gui_permissions/
│           └── gui_settings/
├── build/
│   └── scripts/
│       ├── build_module.sh
│       ├── build_all.sh
│       ├── check_dependencies.sh
│       └── run_module_tests.sh
└── docs/
    └── modules/
        ├── emulator_core.md
        ├── device_manager.md
        └── ... (one per module)
```

---

## 11. Versioning

### 11.1 Module Versions

Each module has independent version:

```
emulator_core: 1.2.0
device_manager: 1.0.3
gui_display: 0.9.1
```

### 11.2 System Version

System version reflects overall release:

```
LinBlock 0.1.0
  - emulator_core 1.2.0
  - device_manager 1.0.3
  - gui_display 0.9.1
  - ...
```

### 11.3 Compatibility Matrix

Maintain compatibility between module versions:

| gui_display | display_manager | Status |
|-------------|-----------------|--------|
| 0.9.x | 1.0.x | Compatible |
| 0.9.x | 1.1.x | Compatible |
| 0.9.x | 2.0.x | Breaking |

---

## 12. Anti-Patterns to Avoid

### 12.1 God Module
One module doing too much. Split by responsibility.

### 12.2 Hidden Dependencies
Using reflection or dynamic imports to bypass interface.

### 12.3 Leaky Abstraction
Internal types exposed through interface.

### 12.4 Chatty Interface
Too many small calls between modules. Batch operations.

### 12.5 Shared Database
Multiple modules accessing same data store directly.

---

## 13. Exception Handling

### 13.1 Module Boundaries

Exceptions do not cross module boundaries raw:

```python
# WRONG
def get_app(self, package):
    return self.internal.fetch(package)  # May raise InternalDBError

# CORRECT
def get_app(self, package):
    try:
        return self.internal.fetch(package)
    except InternalDBError as e:
        raise AppNotFoundError(package) from e
```

### 13.2 Interface Exceptions

Each module defines its own exception types in interface:

```python
# app_manager/interface.py

class AppManagerError(Exception):
    """Base exception for app_manager module"""
    pass

class AppNotFoundError(AppManagerError):
    """Raised when requested app does not exist"""
    pass

class AppFrozenError(AppManagerError):
    """Raised when operation attempted on frozen app"""
    pass
```

---

## 14. Configuration

### 14.1 Module Configuration

Each module has its own config section:

```yaml
# config/linblock.yaml

emulator_core:
  memory_mb: 4096
  cpu_cores: 4

display_manager:
  width: 1080
  height: 1920
  scale: 1.0

app_manager:
  audit_log: true
  freeze_method: cgroup
```

### 14.2 Configuration Loading

Modules receive only their config section:

```python
# Module receives only its portion
class EmulatorCore:
    def __init__(self, config: dict):
        self.memory = config.get("memory_mb", 2048)
        self.cores = config.get("cpu_cores", 2)
```

---

## 15. Summary

This modular architecture ensures:

1. **Independent development** - Work on modules in parallel
2. **Isolated failures** - One module crash does not cascade
3. **Easy testing** - Test modules in isolation with mocks
4. **Clear boundaries** - Know where each feature lives
5. **Replaceable parts** - Swap implementations without rewrite
6. **Manageable complexity** - Each module is small and focused

All team members must follow these guidelines. Deviations require documented justification and team review.
EOF

echo "Created: $PROJECT_ROOT/docs/design/modular_architecture.md"
