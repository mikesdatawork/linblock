#!/bin/bash
# build_all.sh - Build all LinBlock layers in dependency order
#
# Usage: ./build_all.sh
#
# Builds layers in order:
#   1. infrastructure (config, logging, common utilities)
#   2. emulation (emulator core, device managers)
#   3. android (app management, Android integration)
#   4. gui (GTK interface)
#
# Each layer is built using build_layer.sh. If a layer fails, subsequent
# layers are skipped (since they may depend on the failed layer).

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

# Determine project root
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

BUILD_LAYER="$SCRIPT_DIR/build_layer.sh"
BUILD_CONFIG="$PROJECT_ROOT/build/configs/build_config.yaml"

# Parse options
STOP_ON_FAILURE=true
LAYERS=()

while [[ $# -gt 0 ]]; do
    case "$1" in
        --continue-on-failure)
            STOP_ON_FAILURE=false
            shift
            ;;
        --layer)
            LAYERS+=("$2")
            shift 2
            ;;
        -h|--help)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --continue-on-failure   Continue building even if a layer fails"
            echo "  --layer <name>          Build only specified layer(s)"
            echo "  -h, --help              Show this help"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            exit 1
            ;;
    esac
done

# Default layer order
if [ ${#LAYERS[@]} -eq 0 ]; then
    # Try to read from build config
    if [ -f "$BUILD_CONFIG" ] && command -v python3 &>/dev/null; then
        CONFIGURED_LAYERS=$(python3 -c "
import yaml
try:
    with open('$BUILD_CONFIG') as f:
        cfg = yaml.safe_load(f)
    layers = cfg.get('layers', {}).get('build_order', [])
    print(' '.join(layers))
except:
    print('')
" 2>/dev/null || echo "")

        if [ -n "$CONFIGURED_LAYERS" ]; then
            read -ra LAYERS <<< "$CONFIGURED_LAYERS"
        fi
    fi

    # Fallback to default order
    if [ ${#LAYERS[@]} -eq 0 ]; then
        LAYERS=(infrastructure emulation android gui)
    fi
fi

START_TIME=$(date +%s)

echo -e "${BOLD}"
echo "############################################"
echo "#         LinBlock Full Build              #"
echo "############################################"
echo -e "${NC}"
echo ""
info "Project root: $PROJECT_ROOT"
info "Build order: ${LAYERS[*]}"
info "Stop on failure: $STOP_ON_FAILURE"
echo ""
echo "Start time: $(date '+%Y-%m-%d %H:%M:%S')"
echo ""

# Check build_layer.sh exists
if [ ! -f "$BUILD_LAYER" ]; then
    fail "build_layer.sh not found at: $BUILD_LAYER"
    exit 1
fi

# Run dependency check first (if available)
CHECK_DEPS="$SCRIPT_DIR/check_dependencies.sh"
if [ -f "$CHECK_DEPS" ]; then
    echo "============================================"
    info "Running dependency check..."
    echo "============================================"
    if bash "$CHECK_DEPS"; then
        success "Dependency check passed."
    else
        warn "Dependency check found issues (see above)."
        if [ "$STOP_ON_FAILURE" = true ]; then
            fail "Aborting build due to dependency issues."
            exit 1
        fi
    fi
    echo ""
fi

# Build each layer
TOTAL_LAYERS=${#LAYERS[@]}
PASSED_LAYERS=0
FAILED_LAYERS=0
SKIPPED_LAYERS=0
FAILED_LAYER_NAMES=()

for i in "${!LAYERS[@]}"; do
    LAYER="${LAYERS[$i]}"
    LAYER_NUM=$((i + 1))

    echo -e "${BOLD}"
    echo "============================================"
    echo " Layer $LAYER_NUM/$TOTAL_LAYERS: $LAYER"
    echo "============================================"
    echo -e "${NC}"

    LAYER_DIR="$PROJECT_ROOT/src/$LAYER"
    if [ ! -d "$LAYER_DIR" ]; then
        warn "Layer directory not found: $LAYER_DIR (skipping)"
        ((SKIPPED_LAYERS++))
        continue
    fi

    if bash "$BUILD_LAYER" "$LAYER"; then
        ((PASSED_LAYERS++))
        success "Layer $LAYER: PASSED"
    else
        ((FAILED_LAYERS++))
        FAILED_LAYER_NAMES+=("$LAYER")
        fail "Layer $LAYER: FAILED"

        if [ "$STOP_ON_FAILURE" = true ]; then
            REMAINING=$((TOTAL_LAYERS - LAYER_NUM))
            if [ "$REMAINING" -gt 0 ]; then
                warn "Skipping $REMAINING remaining layer(s) due to failure."
                SKIPPED_LAYERS=$REMAINING
            fi
            break
        fi
    fi

    echo ""
done

END_TIME=$(date +%s)
DURATION=$((END_TIME - START_TIME))
MINUTES=$((DURATION / 60))
SECONDS=$((DURATION % 60))

# Final summary
echo ""
echo -e "${BOLD}"
echo "############################################"
echo "#         Build Summary                    #"
echo "############################################"
echo -e "${NC}"
echo ""
echo "  Total layers:   $TOTAL_LAYERS"
success "  Passed:         $PASSED_LAYERS"
if [ "$FAILED_LAYERS" -gt 0 ]; then
    fail "  Failed:         $FAILED_LAYERS"
else
    echo -e "  ${GREEN}Failed:         0${NC}"
fi
if [ "$SKIPPED_LAYERS" -gt 0 ]; then
    warn "  Skipped:        $SKIPPED_LAYERS"
fi
echo ""
echo "  Duration:       ${MINUTES}m ${SECONDS}s"
echo "  End time:       $(date '+%Y-%m-%d %H:%M:%S')"

if [ ${#FAILED_LAYER_NAMES[@]} -gt 0 ]; then
    echo ""
    echo "  Failed layers:"
    for name in "${FAILED_LAYER_NAMES[@]}"; do
        echo "    - $name"
    done
fi

echo ""

if [ "$FAILED_LAYERS" -gt 0 ]; then
    fail "Build FAILED."
    exit 1
else
    success "Build PASSED."
    exit 0
fi
