#!/bin/bash
# check_renderer_deps.sh - Check dependencies for GPU renderer build
#
# Run this script to verify all required dependencies are installed
# before attempting to build libOpenglRender.

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

pass() { echo -e "${GREEN}[PASS]${NC} $1"; }
fail() { echo -e "${RED}[FAIL]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }

MISSING=()

echo "========================================"
echo "  LinBlock GPU Renderer Dependency Check"
echo "========================================"
echo ""

# Build tools
echo "=== Build Tools ==="

if command -v git &> /dev/null; then
    pass "git: $(git --version | head -1)"
else
    fail "git: NOT FOUND"
    MISSING+=("git")
fi

if command -v cmake &> /dev/null; then
    pass "cmake: $(cmake --version | head -1)"
else
    fail "cmake: NOT FOUND"
    MISSING+=("cmake")
fi

if command -v ninja &> /dev/null; then
    pass "ninja: $(ninja --version)"
else
    fail "ninja: NOT FOUND"
    MISSING+=("ninja-build")
fi

if command -v pkg-config &> /dev/null; then
    pass "pkg-config: found"
else
    fail "pkg-config: NOT FOUND"
    MISSING+=("pkg-config")
fi

if command -v python3 &> /dev/null; then
    pass "python3: $(python3 --version)"
else
    fail "python3: NOT FOUND"
    MISSING+=("python3")
fi

echo ""
echo "=== C/C++ Compiler ==="

if command -v gcc &> /dev/null; then
    pass "gcc: $(gcc --version | head -1)"
else
    fail "gcc: NOT FOUND"
    MISSING+=("build-essential")
fi

if command -v g++ &> /dev/null; then
    pass "g++: $(g++ --version | head -1)"
else
    fail "g++: NOT FOUND"
    MISSING+=("build-essential")
fi

echo ""
echo "=== OpenGL Libraries ==="

if pkg-config --exists egl 2>/dev/null; then
    pass "EGL: $(pkg-config --modversion egl 2>/dev/null || echo 'found')"
else
    fail "EGL development files: NOT FOUND"
    MISSING+=("libegl-dev")
fi

if pkg-config --exists gl 2>/dev/null; then
    pass "OpenGL: $(pkg-config --modversion gl 2>/dev/null || echo 'found')"
else
    fail "OpenGL development files: NOT FOUND"
    MISSING+=("libgl-dev")
fi

if pkg-config --exists glesv2 2>/dev/null; then
    pass "OpenGL ES 2.0: $(pkg-config --modversion glesv2 2>/dev/null || echo 'found')"
else
    fail "OpenGL ES development files: NOT FOUND"
    MISSING+=("libgles-dev")
fi

echo ""
echo "=== Additional Libraries ==="

if pkg-config --exists x11 2>/dev/null; then
    pass "X11: $(pkg-config --modversion x11 2>/dev/null || echo 'found')"
else
    warn "X11 development files: NOT FOUND (optional)"
fi

if pkg-config --exists glib-2.0 2>/dev/null; then
    pass "GLib: $(pkg-config --modversion glib-2.0 2>/dev/null || echo 'found')"
else
    fail "GLib development files: NOT FOUND"
    MISSING+=("libglib2.0-dev")
fi

echo ""
echo "=== KVM Support ==="

if [ -e /dev/kvm ]; then
    if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
        pass "KVM: available and accessible"
    else
        warn "KVM: exists but not accessible (add user to kvm group)"
    fi
else
    warn "KVM: not available (emulation will be slower)"
fi

echo ""
echo "=== GPU Support ==="

if [ -e /dev/dri/renderD128 ]; then
    pass "GPU render node: available"
    if command -v glxinfo &> /dev/null; then
        RENDERER=$(glxinfo 2>/dev/null | grep "OpenGL renderer" | cut -d: -f2 | xargs)
        if [ -n "$RENDERER" ]; then
            pass "GPU Renderer: $RENDERER"
        fi
    fi
else
    warn "GPU render node: not found (will use software rendering)"
fi

echo ""
echo "========================================"

if [ ${#MISSING[@]} -eq 0 ]; then
    echo -e "${GREEN}All required dependencies are installed!${NC}"
    echo ""
    echo "You can proceed with building libOpenglRender:"
    echo "  ./build/scripts/extract_emugl.sh"
    exit 0
else
    echo -e "${RED}Missing dependencies:${NC}"
    echo ""
    echo "Install with:"
    echo "  sudo apt-get install ${MISSING[*]}"
    echo ""
    echo "Or on Fedora/RHEL:"
    echo "  sudo dnf install ${MISSING[*]//build-essential/gcc gcc-c++ make}"
    echo ""
    exit 1
fi
