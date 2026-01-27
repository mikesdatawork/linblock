# LinBlock Build Process

Version: 1.0.0
Status: Draft

---

## 1. Build Philosophy

### 1.1 Core Principles

1. **Module Independence** - Each module builds alone
2. **No Hidden Dependencies** - All requirements explicit
3. **Reproducible** - Same inputs produce same outputs
4. **Incremental** - Only rebuild what changed
5. **Verifiable** - Build can be validated at each step

### 1.2 Build Layers

```
Layer 4: System Assembly
         ↑
Layer 3: Integration Build
         ↑
Layer 2: Module Build
         ↑
Layer 1: Dependency Resolution
```

---

## 2. Module Build Process

### 2.1 Single Module Build

Each module can be built independently:

```bash
cd src/modules/<layer>/<module_name>

# Step 1: Install dependencies
pip install -r requirements.txt

# Step 2: Run linter
flake8 . --max-line-length=100

# Step 3: Run type checker (optional)
mypy . --ignore-missing-imports

# Step 4: Run tests
pytest tests/ -v --cov=.

# Step 5: Build package (if distributable)
python -m build
```

### 2.2 Module Build Script

```bash
#!/bin/bash
# build/scripts/build_module.sh

MODULE_PATH="$1"

if [ -z "$MODULE_PATH" ]; then
    echo "Usage: build_module.sh <module_path>"
    echo "Example: build_module.sh src/modules/emulation/display_manager"
    exit 1
fi

if [ ! -d "$MODULE_PATH" ]; then
    echo "ERROR: Module not found: $MODULE_PATH"
    exit 1
fi

MODULE_NAME=$(basename "$MODULE_PATH")
echo "=========================================="
echo "Building module: $MODULE_NAME"
echo "=========================================="

cd "$MODULE_PATH"

# Check for requirements
if [ -f "requirements.txt" ]; then
    echo "[1/4] Installing dependencies..."
    pip install -r requirements.txt -q
else
    echo "[1/4] No requirements.txt found, skipping..."
fi

# Lint
echo "[2/4] Running linter..."
if ! flake8 . --max-line-length=100 --exclude=__pycache__; then
    echo "ERROR: Linting failed"
    exit 1
fi

# Tests
echo "[3/4] Running tests..."
if [ -d "tests" ]; then
    if ! pytest tests/ -v --tb=short; then
        echo "ERROR: Tests failed"
        exit 1
    fi
else
    echo "WARNING: No tests directory found"
fi

# Verify interface
echo "[4/4] Verifying interface..."
if [ ! -f "interface.py" ]; then
    echo "ERROR: interface.py not found"
    exit 1
fi

if [ ! -f "INTERFACE.md" ]; then
    echo "WARNING: INTERFACE.md not found"
fi

echo ""
echo "Module build complete: $MODULE_NAME"
echo "=========================================="
```

### 2.3 Build Output

Module build produces:
- Verified source code (lint passed)
- Test results
- Coverage report (optional)

No compiled artifacts for Python modules. Build is verification only.

---

## 3. Dependency Management

### 3.1 Dependency Rules

| Dependency Type | Allowed | Example |
|-----------------|---------|---------|
| Interface import | Yes | `from ..other_module.interface import X` |
| Internal import | No | `from ..other_module.internal import Y` |
| Mock import | Yes (tests only) | `from ..other_module.mocks import MockX` |

### 3.2 Dependency Declaration

Each module declares dependencies in requirements.txt:

```
# requirements.txt

# External packages
pytest>=7.0.0
flake8>=6.0.0

# Internal module dependencies (interface only)
# Documented here but not installed via pip
# Module: emulator_core (interface)
# Module: event_bus (interface)
```

### 3.3 Dependency Graph Validation

```bash
#!/bin/bash
# build/scripts/check_dependencies.sh

PROJECT_ROOT="/home/user/projects/linblock"
MODULES_DIR="$PROJECT_ROOT/src/modules"

echo "Checking dependency graph..."
echo ""

errors=0

# Find all modules
for module in $(find "$MODULES_DIR" -name "interface.py" -type f); do
    module_dir=$(dirname "$module")
    module_name=$(basename "$module_dir")
    layer=$(basename $(dirname "$module_dir"))
    
    echo "Checking: $layer/$module_name"
    
    # Check for internal imports from other modules
    if grep -r "from \.\.\.*\.internal" "$module_dir"/*.py 2>/dev/null | grep -v "^Binary"; then
        echo "  ERROR: Internal import detected"
        errors=$((errors + 1))
    fi
    
    # Check for circular dependencies (simplified)
    # Full implementation would build dependency graph
done

echo ""
if [ $errors -eq 0 ]; then
    echo "All modules: PASS"
else
    echo "Errors found: $errors"
    exit 1
fi
```

---

## 4. Layer Build Order

### 4.1 Build Sequence

Modules must build in layer order:

```
1. infrastructure/
   ├── config_manager
   ├── log_manager
   └── event_bus

2. emulation/
   ├── emulator_core
   ├── device_manager
   ├── display_manager
   ├── input_manager
   ├── storage_manager
   └── network_manager

3. android/
   ├── android_image
   ├── permission_manager
   ├── app_manager
   └── process_manager

4. gui/
   ├── gui_core
   ├── gui_display
   ├── gui_apps
   ├── gui_permissions
   └── gui_settings
```

### 4.2 Layer Build Script

```bash
#!/bin/bash
# build/scripts/build_layer.sh

LAYER="$1"
PROJECT_ROOT="/home/user/projects/linblock"
LAYER_DIR="$PROJECT_ROOT/src/modules/$LAYER"

if [ -z "$LAYER" ]; then
    echo "Usage: build_layer.sh <layer>"
    echo "Layers: infrastructure, emulation, android, gui"
    exit 1
fi

if [ ! -d "$LAYER_DIR" ]; then
    echo "ERROR: Layer not found: $LAYER"
    exit 1
fi

echo "Building layer: $LAYER"
echo ""

failed=0

for module_dir in "$LAYER_DIR"/*/; do
    if [ -d "$module_dir" ]; then
        module_name=$(basename "$module_dir")
        
        if ! ./build/scripts/build_module.sh "$module_dir"; then
            echo "FAILED: $module_name"
            failed=$((failed + 1))
        fi
    fi
done

echo ""
if [ $failed -eq 0 ]; then
    echo "Layer $LAYER: ALL PASSED"
else
    echo "Layer $LAYER: $failed module(s) failed"
    exit 1
fi
```

---

## 5. Full System Build

### 5.1 Build All Script

```bash
#!/bin/bash
# build/scripts/build_all.sh

set -e

PROJECT_ROOT="/home/user/projects/linblock"
cd "$PROJECT_ROOT"

echo "============================================"
echo "LinBlock Full System Build"
echo "============================================"
echo ""

# Build in layer order
LAYERS="infrastructure emulation android gui"

for layer in $LAYERS; do
    echo ""
    echo ">>> Building layer: $layer"
    echo ""
    
    if ! ./build/scripts/build_layer.sh "$layer"; then
        echo "ERROR: Layer $layer failed"
        exit 1
    fi
done

echo ""
echo "============================================"
echo "Full build complete"
echo "============================================"
```

### 5.2 Build Configuration

```yaml
# build/configs/build_config.yaml

build:
  parallel: false          # Build modules sequentially for now
  stop_on_error: true      # Stop at first failure
  coverage_threshold: 70   # Minimum code coverage %

lint:
  max_line_length: 100
  ignore:
    - E501  # Line too long (handled separately)
    - W503  # Line break before binary operator

test:
  verbose: true
  timeout: 300             # 5 minute timeout per module
  markers:
    - "not slow"           # Skip slow tests by default
```

---

## 6. Integration Build

### 6.1 Integration Test Phase

After module builds pass, run integration tests:

```bash
#!/bin/bash
# build/scripts/integration_test.sh

PROJECT_ROOT="/home/user/projects/linblock"
cd "$PROJECT_ROOT"

echo "Running integration tests..."

# Test cross-module interactions
pytest tests/integration/ -v --tb=short

echo "Integration tests complete"
```

### 6.2 Integration Points

Test these module combinations:

| Test | Modules | Purpose |
|------|---------|---------|
| emulator_boot | emulator_core + device_manager + display_manager | Boot sequence works |
| gui_display | gui_display + display_manager | Display renders correctly |
| app_control | gui_apps + app_manager + permission_manager | App management works |
| full_stack | All modules | System works end-to-end |

---

## 7. Incremental Builds

### 7.1 Change Detection

Only rebuild modules that changed:

```bash
#!/bin/bash
# build/scripts/build_changed.sh

# Get changed files since last build
CHANGED=$(git diff --name-only HEAD~1)

# Find affected modules
MODULES=""
for file in $CHANGED; do
    if [[ "$file" == src/modules/* ]]; then
        # Extract module path
        module=$(echo "$file" | cut -d'/' -f1-4)
        if [[ ! "$MODULES" == *"$module"* ]]; then
            MODULES="$MODULES $module"
        fi
    fi
done

# Build affected modules
for module in $MODULES; do
    echo "Building changed module: $module"
    ./build/scripts/build_module.sh "$module"
done
```

### 7.2 Dependency Cascade

When a module changes, rebuild dependents:

```
emulator_core changes
    → rebuild emulator_core
    → rebuild device_manager (depends on emulator_core)
    → rebuild gui_display (depends on display_manager)
```

---

## 8. Build Verification

### 8.1 Pre-Commit Checks

```bash
#!/bin/bash
# build/scripts/pre_commit.sh

# Run on changed modules only
CHANGED_MODULES=$(./build/scripts/find_changed_modules.sh)

for module in $CHANGED_MODULES; do
    echo "Checking: $module"
    
    # Quick checks only
    cd "$module"
    
    flake8 . --max-line-length=100 --select=E,F,W
    pytest tests/ -v --tb=line -q
    
    cd - > /dev/null
done
```

### 8.2 Build Artifacts

Track build state:

```
build/output/
├── build_manifest.json    # What was built and when
├── test_results/          # Test output per module
│   ├── emulator_core.xml
│   └── display_manager.xml
└── coverage/              # Coverage reports
    ├── emulator_core.html
    └── display_manager.html
```

Build manifest:
```json
{
  "timestamp": "2025-01-27T15:30:00Z",
  "git_commit": "abc123",
  "modules": {
    "emulator_core": {
      "status": "passed",
      "tests": 42,
      "coverage": 85.3
    },
    "display_manager": {
      "status": "passed",
      "tests": 28,
      "coverage": 78.1
    }
  }
}
```

---

## 9. Build Troubleshooting

### 9.1 Common Issues

| Issue | Cause | Solution |
|-------|-------|----------|
| Import error | Missing dependency | Add to requirements.txt |
| Circular import | Modules reference each other | Use interface pattern |
| Test isolation | Tests affect each other | Reset state in fixtures |
| Flaky tests | External dependencies | Mock external services |

### 9.2 Debugging Build Failures

```bash
# Verbose module build
./build/scripts/build_module.sh src/modules/emulation/display_manager --verbose

# Run single test
cd src/modules/emulation/display_manager
pytest tests/test_interface.py::test_specific -v -s

# Check imports
python -c "from modules.emulation.display_manager import create_interface"
```

---

## 10. Summary

Build process ensures:

1. **Modules build independently** - No hidden coupling
2. **Layer order respected** - Infrastructure first
3. **Tests run at each level** - Catch issues early
4. **Incremental is possible** - Don't rebuild everything
5. **State is tracked** - Know what was built

Follow this process for all development and CI/CD pipelines.
