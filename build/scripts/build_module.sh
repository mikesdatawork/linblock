#!/bin/bash
# build_module.sh - Build, lint, and test a single LinBlock module
#
# Usage: ./build_module.sh <layer> <module_name>
# Example: ./build_module.sh emulation emulator_core
#
# Steps:
#   1. cd to module directory
#   2. Install requirements (if requirements.txt exists)
#   3. Run flake8 linting
#   4. Run pytest with coverage
#   5. Report pass/fail

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $1"; }
success() { echo -e "${GREEN}[PASS]${NC} $1"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $1"; }
fail()    { echo -e "${RED}[FAIL]${NC} $1"; }

# Parse arguments
if [ $# -lt 2 ]; then
    echo "Usage: $0 <layer> <module_name>"
    echo "Example: $0 emulation emulator_core"
    echo ""
    echo "Layers: infrastructure, emulation, android, gui"
    exit 1
fi

LAYER="$1"
MODULE="$2"

# Determine project root (relative to this script's location)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

MODULE_DIR="$PROJECT_ROOT/src/$LAYER/$MODULE"

echo ""
echo "=========================================="
echo " Building module: $LAYER/$MODULE"
echo "=========================================="
echo ""

# Check module directory exists
if [ ! -d "$MODULE_DIR" ]; then
    fail "Module directory not found: $MODULE_DIR"
    exit 1
fi

info "Module directory: $MODULE_DIR"

ERRORS=0

# Step 1: Install requirements
info "Step 1: Installing dependencies..."
if [ -f "$MODULE_DIR/requirements.txt" ]; then
    if pip install -r "$MODULE_DIR/requirements.txt" -q 2>/dev/null; then
        success "Dependencies installed."
    else
        warn "Some dependencies failed to install (non-fatal)."
    fi
else
    info "No requirements.txt found (skipping)."
fi

echo ""

# Step 2: Lint with flake8
info "Step 2: Running flake8 lint..."

# Load lint settings from build config if available
MAX_LINE_LENGTH=100
BUILD_CONFIG="$PROJECT_ROOT/build/configs/build_config.yaml"
if [ -f "$BUILD_CONFIG" ] && command -v python3 &>/dev/null; then
    CONFIGURED_LENGTH=$(python3 -c "
import yaml
try:
    with open('$BUILD_CONFIG') as f:
        cfg = yaml.safe_load(f)
    print(cfg.get('lint', {}).get('max_line_length', 100))
except:
    print(100)
" 2>/dev/null || echo "100")
    MAX_LINE_LENGTH="$CONFIGURED_LENGTH"
fi

if command -v flake8 &>/dev/null; then
    if flake8 "$MODULE_DIR" \
        --max-line-length="$MAX_LINE_LENGTH" \
        --exclude=__pycache__,.git,*.egg-info \
        --count \
        --statistics 2>&1; then
        success "flake8 lint passed."
    else
        fail "flake8 lint failed."
        ((ERRORS++))
    fi
else
    warn "flake8 not installed (skipping lint). Install with: pip install flake8"
fi

echo ""

# Step 3: Run tests with coverage
info "Step 3: Running pytest with coverage..."

TEST_DIR="$MODULE_DIR/tests"
if [ ! -d "$TEST_DIR" ]; then
    # Also check for test files directly in module
    TEST_DIR="$MODULE_DIR"
fi

# Load coverage threshold from build config
COV_THRESHOLD=80
if [ -f "$BUILD_CONFIG" ] && command -v python3 &>/dev/null; then
    CONFIGURED_COV=$(python3 -c "
import yaml
try:
    with open('$BUILD_CONFIG') as f:
        cfg = yaml.safe_load(f)
    print(cfg.get('coverage', {}).get('minimum_threshold', 80))
except:
    print(80)
" 2>/dev/null || echo "80")
    COV_THRESHOLD="$CONFIGURED_COV"
fi

if command -v pytest &>/dev/null || python3 -m pytest --version &>/dev/null 2>&1; then
    PYTEST_CMD="python3 -m pytest"

    if $PYTEST_CMD "$TEST_DIR" \
        -v \
        --tb=short \
        --cov="$MODULE_DIR" \
        --cov-report=term-missing \
        --cov-fail-under="$COV_THRESHOLD" \
        2>&1; then
        success "Tests passed with >= ${COV_THRESHOLD}% coverage."
    else
        EXIT_CODE=$?
        if [ $EXIT_CODE -eq 5 ]; then
            warn "No tests found in $TEST_DIR (exit code 5)."
        else
            fail "Tests failed or coverage below ${COV_THRESHOLD}%."
            ((ERRORS++))
        fi
    fi
else
    warn "pytest not installed (skipping tests). Install with: pip install pytest pytest-cov"
fi

echo ""

# Summary
echo "=========================================="
if [ "$ERRORS" -eq 0 ]; then
    success "Module $LAYER/$MODULE: BUILD PASSED"
    exit 0
else
    fail "Module $LAYER/$MODULE: BUILD FAILED ($ERRORS error(s))"
    exit 1
fi
