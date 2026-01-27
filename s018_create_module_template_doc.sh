#!/bin/bash
# s018_create_module_template_doc.sh
# Creates docs/design/module_template.md

PROJECT_ROOT="/home/user/projects/linblock"

cat > "$PROJECT_ROOT/docs/design/module_template.md" << 'EOF'
# LinBlock Module Template

Use this template when creating new modules.

---

## Quick Start

To create a new module:

```bash
./scripts/dev/create_module.sh <layer> <module_name>

# Examples:
./scripts/dev/create_module.sh emulation display_manager
./scripts/dev/create_module.sh android permission_manager
./scripts/dev/create_module.sh gui gui_settings
./scripts/dev/create_module.sh infrastructure event_bus
```

---

## Module README Template

File: `README.md`

```markdown
# Module: [module_name]

## Purpose

[One sentence: What does this module do?]

## Responsibility

This module is responsible for:
- [Responsibility 1]
- [Responsibility 2]
- [Responsibility 3]

## Not Responsible For

This module does NOT handle:
- [Exclusion 1 - handled by X module]
- [Exclusion 2 - handled by Y module]

## Dependencies

| Module | Type | Reason |
|--------|------|--------|
| [module_name] | Hard/Soft | [Why needed] |

Or: **None** - This module has no external dependencies.

## Interface Summary

| Method | Description |
|--------|-------------|
| `method_one()` | Brief description |
| `method_two(param)` | Brief description |

## Usage Example

```python
from modules.[layer].[module_name].interface import [InterfaceName]

instance = [InterfaceName](config)
result = instance.method_one()
```

## Build Instructions

```bash
cd src/modules/[layer]/[module_name]
pip install -r requirements.txt
python -m build
```

## Test Instructions

```bash
cd src/modules/[layer]/[module_name]
pytest tests/ -v
```

## Configuration

```yaml
[module_name]:
  option_one: value
  option_two: value
```

## Status

- [ ] Interface defined
- [ ] Mock implemented
- [ ] Core implementation complete
- [ ] Unit tests passing
- [ ] Integration tested
- [ ] Documentation complete
```

---

## Module INTERFACE Template

File: `INTERFACE.md`

```markdown
# Interface: [ModuleName]Interface

Version: 0.1.0
Stability: experimental

---

## Overview

[Brief description of what this interface provides]

---

## Classes

### [ModuleName]Interface

Main interface class for [module_name] functionality.

#### Constructor

```python
__init__(self, config: dict) -> None
```

Initialize the module with configuration.

**Parameters:**
- config: Module configuration dictionary

**Raises:**
- ConfigurationError: If required config keys missing

---

## Methods

### method_name

```python
method_name(self, param1: str, param2: int = 0) -> ReturnType
```

[Description of what this method does]

**Parameters:**
- param1 (str): Description of param1
- param2 (int, optional): Description of param2. Default: 0

**Returns:**
- ReturnType: Description of return value

**Raises:**
- ErrorType: When [condition]

**Example:**
```python
interface = ModuleInterface(config)
result = interface.method_name("value", param2=10)
```

---

## Events

Events published by this module:

| Event Type | Payload | Description |
|------------|---------|-------------|
| `module.action.started` | `{"id": str}` | Fired when action begins |
| `module.action.completed` | `{"id": str, "result": any}` | Fired when action ends |

---

## Exceptions

### ModuleError

Base exception for this module.

```python
class ModuleError(Exception):
    pass
```

### SpecificError

Raised when [specific condition].

```python
class SpecificError(ModuleError):
    pass
```

---

## Types

### CustomType

```python
@dataclass
class CustomType:
    field1: str
    field2: int
    field3: Optional[bool] = None
```

---

## Compatibility

| Version | Breaking Changes |
|---------|------------------|
| 0.1.0 | Initial release |
```

---

## Module CHANGELOG Template

File: `CHANGELOG.md`

```markdown
# Changelog: [module_name]

All notable changes to this module will be documented here.

Format based on [Keep a Changelog](https://keepachangelog.com/).

---

## [Unreleased]

### Added
- 

### Changed
- 

### Fixed
- 

---

## [0.1.0] - YYYY-MM-DD

### Added
- Initial module implementation
- Core interface methods
- Basic test coverage
```

---

## Module interface.py Template

File: `interface.py`

```python
"""
Module: [module_name]
Layer: [layer]

Public interface for [module_name] functionality.
"""

from dataclasses import dataclass
from typing import Optional, List, Dict, Any
from abc import ABC, abstractmethod


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class ModuleError(Exception):
    """Base exception for [module_name] module."""
    pass


class ConfigurationError(ModuleError):
    """Raised when module configuration is invalid."""
    pass


class OperationError(ModuleError):
    """Raised when an operation fails."""
    pass


# -----------------------------------------------------------------------------
# Types
# -----------------------------------------------------------------------------

@dataclass
class ExampleType:
    """Example data type returned by interface."""
    id: str
    name: str
    value: int
    metadata: Optional[Dict[str, Any]] = None


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class ModuleInterface(ABC):
    """
    Abstract interface for [module_name].
    
    All implementations must inherit from this class.
    """
    
    @abstractmethod
    def __init__(self, config: dict) -> None:
        """
        Initialize module with configuration.
        
        Args:
            config: Module configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def example_method(self, param: str) -> ExampleType:
        """
        Example method description.
        
        Args:
            param: Description of parameter
            
        Returns:
            ExampleType with result data
            
        Raises:
            OperationError: If operation fails
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """
        Release resources held by module.
        
        Should be called before discarding module instance.
        """
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultModuleImplementation(ModuleInterface):
    """Default implementation of ModuleInterface."""
    
    def __init__(self, config: dict) -> None:
        self._validate_config(config)
        self._config = config
        self._initialized = True
    
    def _validate_config(self, config: dict) -> None:
        """Validate configuration dictionary."""
        # Add validation logic
        pass
    
    def example_method(self, param: str) -> ExampleType:
        if not self._initialized:
            raise OperationError("Module not initialized")
        
        # Implementation
        return ExampleType(
            id="example",
            name=param,
            value=42
        )
    
    def cleanup(self) -> None:
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: dict) -> ModuleInterface:
    """
    Factory function to create module interface.
    
    Args:
        config: Module configuration
        
    Returns:
        Configured ModuleInterface implementation
    """
    return DefaultModuleImplementation(config)
```

---

## Module Mock Template

File: `mocks/mock_interface.py`

```python
"""
Mock implementation of [module_name] interface.

Use this mock when testing modules that depend on [module_name].
"""

from typing import List, Optional, Dict, Any
from ..interface import ModuleInterface, ExampleType


class MockModuleInterface(ModuleInterface):
    """
    Mock implementation for testing.
    
    Tracks all method calls and allows configuring responses.
    """
    
    def __init__(self, config: dict = None) -> None:
        self.config = config or {}
        self.calls: List[Dict[str, Any]] = []
        self.responses: Dict[str, Any] = {}
        self._initialized = True
    
    def _record_call(self, method: str, **kwargs) -> None:
        """Record a method call for verification."""
        self.calls.append({
            "method": method,
            "args": kwargs
        })
    
    def set_response(self, method: str, response: Any) -> None:
        """Configure response for a method."""
        self.responses[method] = response
    
    def get_calls(self, method: str = None) -> List[Dict]:
        """Get recorded calls, optionally filtered by method."""
        if method:
            return [c for c in self.calls if c["method"] == method]
        return self.calls
    
    def reset(self) -> None:
        """Clear recorded calls and responses."""
        self.calls = []
        self.responses = {}
    
    # Interface methods
    
    def example_method(self, param: str) -> ExampleType:
        self._record_call("example_method", param=param)
        
        if "example_method" in self.responses:
            return self.responses["example_method"]
        
        return ExampleType(id="mock", name=param, value=0)
    
    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._initialized = False
```

---

## Module Test Template

File: `tests/test_interface.py`

```python
"""
Interface tests for [module_name].

Tests the public API contract.
"""

import pytest
from ..interface import (
    ModuleInterface,
    DefaultModuleImplementation,
    create_interface,
    ExampleType,
    ConfigurationError,
    OperationError
)


class TestModuleInterface:
    """Test suite for ModuleInterface."""
    
    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {
            "option_one": "value",
            "option_two": 42
        }
    
    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)
    
    # Construction tests
    
    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        interface = create_interface(config)
        assert interface is not None
    
    def test_create_with_empty_config(self):
        """Interface handles empty config appropriately."""
        interface = create_interface({})
        assert interface is not None
    
    # Method tests
    
    def test_example_method_returns_expected_type(self, interface):
        """example_method returns ExampleType."""
        result = interface.example_method("test")
        assert isinstance(result, ExampleType)
    
    def test_example_method_uses_parameter(self, interface):
        """example_method incorporates parameter in result."""
        result = interface.example_method("my_value")
        assert result.name == "my_value"
    
    # Cleanup tests
    
    def test_cleanup_releases_resources(self, interface):
        """cleanup allows interface to be discarded."""
        interface.cleanup()
        # Verify no exceptions and state is cleared
    
    def test_method_after_cleanup_raises(self, interface):
        """Methods raise after cleanup called."""
        interface.cleanup()
        with pytest.raises(OperationError):
            interface.example_method("test")
```

---

## Directory Creation Script

File: `scripts/dev/create_module.sh`

```bash
#!/bin/bash
# create_module.sh - Create new module from template

LAYER="$1"
MODULE_NAME="$2"

if [ -z "$LAYER" ] || [ -z "$MODULE_NAME" ]; then
    echo "Usage: create_module.sh <layer> <module_name>"
    echo "Layers: infrastructure, emulation, android, gui"
    exit 1
fi

# Validate layer
case "$LAYER" in
    infrastructure|emulation|android|gui)
        ;;
    *)
        echo "Invalid layer: $LAYER"
        echo "Valid layers: infrastructure, emulation, android, gui"
        exit 1
        ;;
esac

PROJECT_ROOT="/home/user/projects/linblock"
MODULE_DIR="$PROJECT_ROOT/src/modules/$LAYER/$MODULE_NAME"

if [ -d "$MODULE_DIR" ]; then
    echo "Module already exists: $MODULE_DIR"
    exit 1
fi

echo "Creating module: $LAYER/$MODULE_NAME"

# Create directory structure
mkdir -p "$MODULE_DIR"
mkdir -p "$MODULE_DIR/internal"
mkdir -p "$MODULE_DIR/tests"
mkdir -p "$MODULE_DIR/mocks"

# Create __init__.py
cat > "$MODULE_DIR/__init__.py" << EOF
"""
Module: $MODULE_NAME
Layer: $LAYER
"""

from .interface import create_interface

__all__ = ["create_interface"]
EOF

# Create empty requirements.txt
touch "$MODULE_DIR/requirements.txt"

# Create placeholder files
touch "$MODULE_DIR/README.md"
touch "$MODULE_DIR/INTERFACE.md"
touch "$MODULE_DIR/CHANGELOG.md"
touch "$MODULE_DIR/interface.py"
touch "$MODULE_DIR/internal/__init__.py"
touch "$MODULE_DIR/tests/__init__.py"
touch "$MODULE_DIR/tests/test_interface.py"
touch "$MODULE_DIR/mocks/__init__.py"
touch "$MODULE_DIR/mocks/mock_interface.py"

echo "Module created: $MODULE_DIR"
echo ""
echo "Next steps:"
echo "1. Edit README.md with module purpose"
echo "2. Define interface in INTERFACE.md"
echo "3. Implement interface.py"
echo "4. Create mock in mocks/mock_interface.py"
echo "5. Write tests in tests/test_interface.py"
```

---

## Summary

Use these templates to ensure all modules follow the same structure. Consistency makes the codebase easier to navigate and maintain.
EOF

echo "Created: $PROJECT_ROOT/docs/design/module_template.md"
