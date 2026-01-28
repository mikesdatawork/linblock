#!/bin/bash
# build_layer.sh - Build all modules in a LinBlock layer
#
# Usage: ./build_layer.sh <layer>
# Example: ./build_layer.sh emulation
#
# Iterates over all module subdirectories in src/<layer>/ and runs
# build_module.sh for each one. Reports a summary of pass/fail results.

set -uo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[PASS]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()    { echo -e "${RED}[FAIL]${NC} $1"; }

# Parse arguments
if [ $# -lt 1 ]; then
    echo "Usage: $0 <layer>"
    echo "Example: $0 emulation"
    echo ""
    echo "Available layers: infrastructure, emulation, android, gui"
    exit 1
fi

LAYER="$1"

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

LAYER_DIR="$PROJECT_ROOT/src/$LAYER"
BUILD_MODULE="$SCRIPT_DIR/build_module.sh"

echo ""
echo -e "${BOLD}=========================================="
echo " Building layer: $LAYER"
echo -e "==========================================${NC}"
echo ""

# Check layer directory exists
if [ ! -d "$LAYER_DIR" ]; then
    fail "Layer directory not found: $LAYER_DIR"
    exit 1
fi

# Check build_module.sh exists
if [ ! -f "$BUILD_MODULE" ]; then
    fail "build_module.sh not found at: $BUILD_MODULE"
    exit 1
fi

# Find all module directories
MODULES=()
for dir in "$LAYER_DIR"/*/; do
    if [ -d "$dir" ]; then
        MODULE_NAME=$(basename "$dir")
        # Skip __pycache__ and hidden directories
        if [[ "$MODULE_NAME" != __pycache__* ]] && [[ "$MODULE_NAME" != .* ]]; then
            MODULES+=("$MODULE_NAME")
        fi
    fi
done

if [ ${#MODULES[@]} -eq 0 ]; then
    warn "No modules found in $LAYER_DIR"
    exit 0
fi

info "Found ${#MODULES[@]} module(s): ${MODULES[*]}"
echo ""

# Build each module
PASSED=0
FAILED=0
SKIPPED=0
FAILED_MODULES=()

for MODULE in "${MODULES[@]}"; do
    echo "-------------------------------------------"
    info "Building: $LAYER/$MODULE"
    echo "-------------------------------------------"

    if bash "$BUILD_MODULE" "$LAYER" "$MODULE"; then
        ((PASSED++))
    else
        ((FAILED++))
        FAILED_MODULES+=("$MODULE")
    fi

    echo ""
done

# Summary
echo -e "${BOLD}=========================================="
echo " Layer Summary: $LAYER"
echo -e "==========================================${NC}"
echo ""
echo "  Total modules:  ${#MODULES[@]}"
success "  Passed:         $PASSED"
if [ "$FAILED" -gt 0 ]; then
    fail "  Failed:         $FAILED"
    echo ""
    echo "  Failed modules:"
    for mod in "${FAILED_MODULES[@]}"; do
        echo "    - $mod"
    done
else
    echo -e "  ${GREEN}Failed:         0${NC}"
fi

echo ""

if [ "$FAILED" -gt 0 ]; then
    fail "Layer $LAYER: $FAILED module(s) failed."
    exit 1
else
    success "Layer $LAYER: All $PASSED module(s) passed."
    exit 0
fi
