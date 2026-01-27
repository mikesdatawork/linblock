#!/bin/bash
# s019_create_module_generator.sh
# Creates scripts/dev/create_module.sh

PROJECT_ROOT="/home/user/projects/linblock"

mkdir -p "$PROJECT_ROOT/scripts/dev"

cat > "$PROJECT_ROOT/scripts/dev/create_module.sh" << 'OUTER_EOF'
#!/bin/bash
# create_module.sh - Create new module from template
# Usage: ./create_module.sh <layer> <module_name>

set -e

LAYER="$1"
MODULE_NAME="$2"

if [ -z "$LAYER" ] || [ -z "$MODULE_NAME" ]; then
    echo "Usage: create_module.sh <layer> <module_name>"
    echo ""
    echo "Layers:"
    echo "  infrastructure  - Base services (config, logging, events)"
    echo "  emulation       - Emulator core components"
    echo "  android         - Android OS integration"
    echo "  gui             - GTK user interface"
    echo ""
    echo "Example:"
    echo "  ./create_module.sh emulation display_manager"
    exit 1
fi

# Validate layer
case "$LAYER" in
    infrastructure|emulation|android|gui)
        ;;
    *)
        echo "ERROR: Invalid layer: $LAYER"
        echo "Valid layers: infrastructure, emulation, android, gui"
        exit 1
        ;;
esac

# Validate module name (lowercase, underscores only)
if [[ ! "$MODULE_NAME" =~ ^[a-z][a-z0-9_]*$ ]]; then
    echo "ERROR: Invalid module name: $MODULE_NAME"
    echo "Module names must be lowercase with underscores only"
    exit 1
fi

PROJECT_ROOT="/home/user/projects/linblock"
MODULE_DIR="$PROJECT_ROOT/src/modules/$LAYER/$MODULE_NAME"

if [ -d "$MODULE_DIR" ]; then
    echo "ERROR: Module already exists: $MODULE_DIR"
    exit 1
fi

echo "Creating module: $LAYER/$MODULE_NAME"
echo "Location: $MODULE_DIR"
echo ""

# Create directory structure
mkdir -p "$MODULE_DIR"
mkdir -p "$MODULE_DIR/internal"
mkdir -p "$MODULE_DIR/tests"
mkdir -p "$MODULE_DIR/mocks"

# Convert module name to class name (snake_case to PascalCase)
CLASS_NAME=$(echo "$MODULE_NAME" | sed -r 's/(^|_)([a-z])/\U\2/g')

# Create __init__.py
cat > "$MODULE_DIR/__init__.py" << EOF
"""
Module: $MODULE_NAME
Layer: $LAYER

[Add module description here]
"""

from .interface import create_interface, ${CLASS_NAME}Interface

__all__ = ["create_interface", "${CLASS_NAME}Interface"]
EOF

# Create requirements.txt
cat > "$MODULE_DIR/requirements.txt" << EOF
# Module dependencies for $MODULE_NAME
# Add dependencies here, one per line
EOF

# Create README.md
cat > "$MODULE_DIR/README.md" << EOF
# Module: $MODULE_NAME

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
| None | - | This module has no external dependencies |

## Interface Summary

| Method | Description |
|--------|-------------|
| \`example_method()\` | [Description] |

## Usage Example

\`\`\`python
from modules.$LAYER.$MODULE_NAME import create_interface

config = {}
instance = create_interface(config)
result = instance.example_method()
\`\`\`

## Build Instructions

\`\`\`bash
cd src/modules/$LAYER/$MODULE_NAME
pip install -r requirements.txt
\`\`\`

## Test Instructions

\`\`\`bash
cd src/modules/$LAYER/$MODULE_NAME
pytest tests/ -v
\`\`\`

## Configuration

\`\`\`yaml
$MODULE_NAME:
  # Add configuration options here
\`\`\`

## Status

- [ ] Interface defined
- [ ] Mock implemented
- [ ] Core implementation complete
- [ ] Unit tests passing
- [ ] Integration tested
- [ ] Documentation complete
EOF

# Create INTERFACE.md
cat > "$MODULE_DIR/INTERFACE.md" << EOF
# Interface: ${CLASS_NAME}Interface

Version: 0.1.0
Stability: experimental

---

## Overview

[Brief description of what this interface provides]

---

## Methods

### example_method

\`\`\`python
example_method(self, param: str) -> str
\`\`\`

[Description of what this method does]

**Parameters:**
- param (str): Description of parameter

**Returns:**
- str: Description of return value

**Raises:**
- ${CLASS_NAME}Error: When operation fails

**Example:**
\`\`\`python
interface = create_interface(config)
result = interface.example_method("value")
\`\`\`

---

## Exceptions

### ${CLASS_NAME}Error

Base exception for this module.

---

## Compatibility

| Version | Changes |
|---------|---------|
| 0.1.0 | Initial release |
EOF

# Create CHANGELOG.md
cat > "$MODULE_DIR/CHANGELOG.md" << EOF
# Changelog: $MODULE_NAME

All notable changes to this module will be documented here.

---

## [Unreleased]

### Added
- Initial module structure

---

## [0.1.0] - $(date +%Y-%m-%d)

### Added
- Initial module implementation
- Basic interface definition
EOF

# Create interface.py
cat > "$MODULE_DIR/interface.py" << EOF
"""
Module: $MODULE_NAME
Layer: $LAYER

Public interface for $MODULE_NAME functionality.
"""

from typing import Dict, Any, Optional
from abc import ABC, abstractmethod


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class ${CLASS_NAME}Error(Exception):
    """Base exception for $MODULE_NAME module."""
    pass


class ConfigurationError(${CLASS_NAME}Error):
    """Raised when module configuration is invalid."""
    pass


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class ${CLASS_NAME}Interface(ABC):
    """
    Abstract interface for $MODULE_NAME.
    
    All implementations must inherit from this class.
    """
    
    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """
        Initialize module with configuration.
        
        Args:
            config: Module configuration dictionary
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        pass
    
    @abstractmethod
    def example_method(self, param: str) -> str:
        """
        Example method - replace with actual functionality.
        
        Args:
            param: Example parameter
            
        Returns:
            Example return value
            
        Raises:
            ${CLASS_NAME}Error: If operation fails
        """
        pass
    
    @abstractmethod
    def cleanup(self) -> None:
        """Release resources held by module."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class Default${CLASS_NAME}(${CLASS_NAME}Interface):
    """Default implementation of ${CLASS_NAME}Interface."""
    
    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config
        self._initialized = True
    
    def example_method(self, param: str) -> str:
        if not self._initialized:
            raise ${CLASS_NAME}Error("Module not initialized")
        return f"Processed: {param}"
    
    def cleanup(self) -> None:
        self._initialized = False


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> ${CLASS_NAME}Interface:
    """
    Factory function to create module interface.
    
    Args:
        config: Module configuration (optional)
        
    Returns:
        Configured ${CLASS_NAME}Interface implementation
    """
    return Default${CLASS_NAME}(config or {})
EOF

# Create internal/__init__.py
cat > "$MODULE_DIR/internal/__init__.py" << EOF
"""
Internal implementation details for $MODULE_NAME.

Do not import from this package directly.
Use the public interface instead.
"""
EOF

# Create tests/__init__.py
touch "$MODULE_DIR/tests/__init__.py"

# Create tests/test_interface.py
cat > "$MODULE_DIR/tests/test_interface.py" << EOF
"""
Interface tests for $MODULE_NAME.

Tests the public API contract.
"""

import pytest
from ..interface import (
    ${CLASS_NAME}Interface,
    Default${CLASS_NAME},
    create_interface,
    ${CLASS_NAME}Error,
    ConfigurationError
)


class Test${CLASS_NAME}Interface:
    """Test suite for ${CLASS_NAME}Interface."""
    
    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}
    
    @pytest.fixture
    def interface(self, config):
        """Create interface instance for testing."""
        return create_interface(config)
    
    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        interface = create_interface(config)
        assert interface is not None
    
    def test_create_with_no_config(self):
        """Interface creates with default config."""
        interface = create_interface()
        assert interface is not None
    
    def test_example_method_returns_string(self, interface):
        """example_method returns string."""
        result = interface.example_method("test")
        assert isinstance(result, str)
    
    def test_cleanup_allows_discard(self, interface):
        """cleanup allows interface to be discarded."""
        interface.cleanup()
        # Should not raise
    
    def test_method_after_cleanup_raises(self, interface):
        """Methods raise after cleanup called."""
        interface.cleanup()
        with pytest.raises(${CLASS_NAME}Error):
            interface.example_method("test")
EOF

# Create mocks/__init__.py
cat > "$MODULE_DIR/mocks/__init__.py" << EOF
"""
Mock implementations for $MODULE_NAME.

Use these mocks when testing modules that depend on $MODULE_NAME.
"""

from .mock_interface import Mock${CLASS_NAME}Interface

__all__ = ["Mock${CLASS_NAME}Interface"]
EOF

# Create mocks/mock_interface.py
cat > "$MODULE_DIR/mocks/mock_interface.py" << EOF
"""
Mock implementation of $MODULE_NAME interface.

Use this mock when testing modules that depend on $MODULE_NAME.
"""

from typing import Dict, Any, List
from ..interface import ${CLASS_NAME}Interface


class Mock${CLASS_NAME}Interface(${CLASS_NAME}Interface):
    """
    Mock implementation for testing.
    
    Tracks all method calls and allows configuring responses.
    """
    
    def __init__(self, config: Dict[str, Any] = None) -> None:
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
    
    def example_method(self, param: str) -> str:
        self._record_call("example_method", param=param)
        if "example_method" in self.responses:
            return self.responses["example_method"]
        return f"mock: {param}"
    
    def cleanup(self) -> None:
        self._record_call("cleanup")
        self._initialized = False
EOF

echo ""
echo "Module created successfully!"
echo ""
echo "Files created:"
find "$MODULE_DIR" -type f | sort | sed 's|^|  |'
echo ""
echo "Next steps:"
echo "  1. Edit README.md - Define module purpose and responsibilities"
echo "  2. Edit INTERFACE.md - Document public API"
echo "  3. Edit interface.py - Implement real functionality"
echo "  4. Run tests: cd $MODULE_DIR && pytest tests/ -v"
OUTER_EOF

chmod +x "$PROJECT_ROOT/scripts/dev/create_module.sh"

echo "Created: $PROJECT_ROOT/scripts/dev/create_module.sh"
