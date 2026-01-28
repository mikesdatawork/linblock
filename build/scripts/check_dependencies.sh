#!/bin/bash
# check_dependencies.sh - Scan for forbidden cross-module imports in LinBlock
#
# This script enforces module boundaries by checking that modules only import
# from other modules through their public interface.py files, not through
# internal implementation files.
#
# Rules:
# - Modules may import from their own package freely
# - Modules may import from other modules ONLY via interface.py
# - No circular dependencies between layers
# - Infrastructure layer has no dependencies on other layers
# - GUI layer may depend on all other layers (via interfaces)
#
# Usage: ./check_dependencies.sh

set -uo pipefail

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

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

SRC_DIR="$PROJECT_ROOT/src"

echo ""
echo "=========================================="
echo " LinBlock Dependency Check"
echo "=========================================="
echo ""

if [ ! -d "$SRC_DIR" ]; then
    fail "Source directory not found: $SRC_DIR"
    exit 1
fi

VIOLATIONS=0
WARNINGS=0
FILES_CHECKED=0

# Define layer dependency rules
# Format: layer -> allowed dependencies (space-separated)
declare -A LAYER_DEPS
LAYER_DEPS[infrastructure]=""
LAYER_DEPS[emulation]="infrastructure"
LAYER_DEPS[android]="infrastructure emulation"
LAYER_DEPS[gui]="infrastructure emulation android"

# Check 1: Scan interface.py files exist for each module
info "Check 1: Verifying interface.py files exist..."

for layer_dir in "$SRC_DIR"/*/; do
    if [ ! -d "$layer_dir" ]; then continue; fi
    LAYER=$(basename "$layer_dir")

    for module_dir in "$layer_dir"*/; do
        if [ ! -d "$module_dir" ]; then continue; fi
        MODULE=$(basename "$module_dir")

        # Skip __pycache__ and hidden dirs
        if [[ "$MODULE" == __pycache__* ]] || [[ "$MODULE" == .* ]]; then
            continue
        fi

        INTERFACE_FILE="$module_dir/interface.py"
        if [ ! -f "$INTERFACE_FILE" ]; then
            warn "Missing interface.py: $LAYER/$MODULE"
            ((WARNINGS++))
        fi
    done
done

echo ""

# Check 2: Scan for forbidden cross-module imports
info "Check 2: Scanning for forbidden cross-module imports..."

# Find all Python files
while IFS= read -r -d '' pyfile; do
    ((FILES_CHECKED++))

    # Determine which layer and module this file belongs to
    REL_PATH="${pyfile#$SRC_DIR/}"
    FILE_LAYER=$(echo "$REL_PATH" | cut -d'/' -f1)
    FILE_MODULE=$(echo "$REL_PATH" | cut -d'/' -f2)

    # Skip if not in a recognized layer
    if [[ ! -v "LAYER_DEPS[$FILE_LAYER]" ]]; then
        continue
    fi

    # Extract import statements
    while IFS= read -r line; do
        # Match: from src.layer.module.something import ...
        # or: import src.layer.module.something
        if echo "$line" | grep -qE '^\s*(from|import)\s+'; then

            # Check for imports from other layers
            for other_layer in infrastructure emulation android gui; do
                if [ "$other_layer" = "$FILE_LAYER" ]; then
                    # Same layer - check for cross-module internal imports
                    # Extract imported module name
                    IMPORTED_MODULE=$(echo "$line" | grep -oP "(?:from|import)\s+(?:src\.)?${other_layer}\.(\w+)" | grep -oP "\w+$" || true)

                    if [ -n "$IMPORTED_MODULE" ] && [ "$IMPORTED_MODULE" != "$FILE_MODULE" ]; then
                        # Importing from another module in the same layer
                        # Check if it's importing from interface.py
                        if echo "$line" | grep -qP "\.interface\s|\.interface$"; then
                            # Importing from interface - OK
                            :
                        elif echo "$line" | grep -qP "from\s+(?:src\.)?${other_layer}\.${IMPORTED_MODULE}\s+import"; then
                            # Importing directly from module package (may be __init__.py which re-exports interface)
                            :
                        else
                            # Might be importing internal module
                            INTERNAL=$(echo "$line" | grep -oP "(?:from|import)\s+(?:src\.)?${other_layer}\.${IMPORTED_MODULE}\.\K\w+" || true)
                            if [ -n "$INTERNAL" ] && [ "$INTERNAL" != "interface" ]; then
                                fail "Forbidden import in $REL_PATH:"
                                echo "       $line"
                                echo "       -> Importing internal module '$INTERNAL' from $other_layer/$IMPORTED_MODULE"
                                echo "       -> Use: from ${other_layer}.${IMPORTED_MODULE}.interface import ..."
                                ((VIOLATIONS++))
                            fi
                        fi
                    fi
                else
                    # Different layer - check if allowed
                    if echo "$line" | grep -qP "(?:from|import)\s+(?:src\.)?${other_layer}\."; then
                        ALLOWED="${LAYER_DEPS[$FILE_LAYER]}"
                        if echo "$ALLOWED" | grep -qw "$other_layer"; then
                            # Allowed layer dependency - check if using interface
                            INTERNAL=$(echo "$line" | grep -oP "(?:from|import)\s+(?:src\.)?${other_layer}\.\w+\.\K\w+" || true)
                            if [ -n "$INTERNAL" ] && [ "$INTERNAL" != "interface" ]; then
                                fail "Forbidden internal import in $REL_PATH:"
                                echo "       $line"
                                echo "       -> Import from $other_layer must use interface.py"
                                ((VIOLATIONS++))
                            fi
                        else
                            fail "Forbidden layer dependency in $REL_PATH:"
                            echo "       $line"
                            echo "       -> Layer '$FILE_LAYER' cannot import from '$other_layer'"
                            echo "       -> Allowed dependencies: ${ALLOWED:-none}"
                            ((VIOLATIONS++))
                        fi
                    fi
                fi
            done
        fi
    done < <(grep -nE '^\s*(from|import)\s+' "$pyfile" 2>/dev/null || true)

done < <(find "$SRC_DIR" -name "*.py" -not -path "*/__pycache__/*" -print0 2>/dev/null)

echo ""

# Check 3: Look for circular layer dependencies
info "Check 3: Checking for circular layer dependencies..."

# The layer order is: infrastructure -> emulation -> android -> gui
# As long as dependencies only point to earlier layers, no cycles are possible.
# We already enforce this in Check 2 via LAYER_DEPS.
success "Layer dependency order is acyclic by construction."

echo ""

# Summary
echo "=========================================="
echo " Dependency Check Summary"
echo "=========================================="
echo ""
echo "  Files checked:  $FILES_CHECKED"
echo "  Violations:     $VIOLATIONS"
echo "  Warnings:       $WARNINGS"
echo ""

if [ "$VIOLATIONS" -gt 0 ]; then
    fail "Found $VIOLATIONS dependency violation(s). Please fix before building."
    exit 1
elif [ "$WARNINGS" -gt 0 ]; then
    warn "Found $WARNINGS warning(s) but no violations."
    exit 0
else
    success "All dependency checks passed."
    exit 0
fi
