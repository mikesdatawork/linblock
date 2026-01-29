#!/bin/bash
# extract_emugl.sh - Extract libOpenglRender from Android Emulator source
#
# This script clones the Android Emulator source and extracts only the
# components needed for GPU translation (libOpenglRender).

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
VENDOR_DIR="$PROJECT_ROOT/vendor"
EMUGL_DIR="$VENDOR_DIR/android-emugl"
BUILD_DIR="$EMUGL_DIR/build"

# Android Emulator source location
AOSP_QEMU_URL="https://android.googlesource.com/platform/external/qemu"
AOSP_QEMU_BRANCH="aosp-emu-34-release"  # Android 14 stable

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_dependencies() {
    log_info "Checking dependencies..."

    local missing=()

    for cmd in git cmake ninja-build; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -ne 0 ]; then
        log_error "Missing dependencies: ${missing[*]}"
        echo "Install with: sudo apt-get install ${missing[*]}"
        exit 1
    fi

    log_info "All dependencies present"
}

clone_source() {
    log_info "Cloning Android Emulator source (this may take a while)..."

    if [ -d "$VENDOR_DIR/platform_external_qemu" ]; then
        log_warn "Source already exists, updating..."
        cd "$VENDOR_DIR/platform_external_qemu"
        git fetch origin
        git checkout "$AOSP_QEMU_BRANCH"
        git pull
    else
        mkdir -p "$VENDOR_DIR"
        cd "$VENDOR_DIR"

        # Shallow clone to save space/time
        git clone --depth 1 --branch "$AOSP_QEMU_BRANCH" \
            "$AOSP_QEMU_URL" platform_external_qemu
    fi

    log_info "Source cloned successfully"
}

extract_emugl() {
    log_info "Extracting emugl components..."

    local SRC="$VENDOR_DIR/platform_external_qemu/android/android-emugl"

    if [ ! -d "$SRC" ]; then
        log_error "Source directory not found: $SRC"
        exit 1
    fi

    # Create extraction directory
    rm -rf "$EMUGL_DIR"
    mkdir -p "$EMUGL_DIR"

    # Copy required components
    log_info "Copying host libraries..."
    cp -r "$SRC/host" "$EMUGL_DIR/"

    log_info "Copying shared components..."
    cp -r "$SRC/shared" "$EMUGL_DIR/"

    log_info "Copying protocol definitions..."
    if [ -d "$SRC/protocol" ]; then
        cp -r "$SRC/protocol" "$EMUGL_DIR/"
    fi

    # Copy build files
    log_info "Copying build configuration..."
    cp "$SRC/CMakeLists.txt" "$EMUGL_DIR/" 2>/dev/null || true

    # Copy DESIGN doc for reference
    cp "$SRC/DESIGN" "$EMUGL_DIR/" 2>/dev/null || true

    log_info "Extraction complete"
}

create_linblock_cmake() {
    log_info "Creating LinBlock CMake configuration..."

    cat > "$EMUGL_DIR/CMakeLists.txt" << 'EOF'
# LinBlock libOpenglRender Build Configuration
# Extracted from Android Emulator for GPU translation

cmake_minimum_required(VERSION 3.16)
project(linblock_opengl_render C CXX)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_POSITION_INDEPENDENT_CODE ON)

# Find required packages
find_package(PkgConfig REQUIRED)
pkg_check_modules(EGL REQUIRED egl)
pkg_check_modules(GLES2 REQUIRED glesv2)
pkg_check_modules(GL REQUIRED gl)

# Include directories
include_directories(
    ${CMAKE_CURRENT_SOURCE_DIR}/host/include
    ${CMAKE_CURRENT_SOURCE_DIR}/shared
    ${CMAKE_CURRENT_SOURCE_DIR}/shared/OpenglCodecCommon
)

# Collect source files
file(GLOB_RECURSE RENDER_SOURCES
    "host/libs/libOpenglRender/*.cpp"
    "host/libs/libOpenglRender/*.c"
)

file(GLOB_RECURSE GLES1_DEC_SOURCES
    "host/libs/GLESv1_dec/*.cpp"
)

file(GLOB_RECURSE GLES2_DEC_SOURCES
    "host/libs/GLESv2_dec/*.cpp"
)

file(GLOB_RECURSE TRANSLATOR_SOURCES
    "host/libs/Translator/EGL/*.cpp"
    "host/libs/Translator/GLES_V2/*.cpp"
    "host/libs/Translator/GLcommon/*.cpp"
)

file(GLOB_RECURSE SHARED_SOURCES
    "shared/OpenglCodecCommon/*.cpp"
)

# Build libOpenglRender
add_library(OpenglRender SHARED
    ${RENDER_SOURCES}
    ${GLES1_DEC_SOURCES}
    ${GLES2_DEC_SOURCES}
    ${TRANSLATOR_SOURCES}
    ${SHARED_SOURCES}
)

target_link_libraries(OpenglRender
    ${EGL_LIBRARIES}
    ${GLES2_LIBRARIES}
    ${GL_LIBRARIES}
    pthread
    dl
)

target_include_directories(OpenglRender PUBLIC
    ${EGL_INCLUDE_DIRS}
    ${GLES2_INCLUDE_DIRS}
    ${GL_INCLUDE_DIRS}
)

# Install
install(TARGETS OpenglRender
    LIBRARY DESTINATION lib
    ARCHIVE DESTINATION lib
)

install(DIRECTORY host/include/
    DESTINATION include/linblock/emugl
)
EOF

    log_info "CMake configuration created"
}

create_wrapper_header() {
    log_info "Creating C API wrapper header..."

    mkdir -p "$EMUGL_DIR/linblock"

    cat > "$EMUGL_DIR/linblock/render_api.h" << 'EOF'
/*
 * LinBlock GPU Renderer API
 *
 * C wrapper around libOpenglRender for use by LinBlock emulator.
 * This provides a simplified interface for:
 * - Initializing the renderer
 * - Processing GPU commands from guest
 * - Retrieving rendered frames
 */

#ifndef LINBLOCK_RENDER_API_H
#define LINBLOCK_RENDER_API_H

#include <stdint.h>
#include <stddef.h>

#ifdef __cplusplus
extern "C" {
#endif

/* Renderer handle */
typedef void* LBRenderContext;

/* Frame format */
typedef enum {
    LB_FORMAT_RGBA8888 = 0,
    LB_FORMAT_BGRA8888 = 1,
    LB_FORMAT_RGB888   = 2,
} LBFrameFormat;

/* Error codes */
typedef enum {
    LB_OK = 0,
    LB_ERROR_INIT_FAILED = -1,
    LB_ERROR_INVALID_CONTEXT = -2,
    LB_ERROR_INVALID_PARAMS = -3,
    LB_ERROR_GPU_ERROR = -4,
    LB_ERROR_OUT_OF_MEMORY = -5,
} LBError;

/* Frame data structure */
typedef struct {
    uint32_t width;
    uint32_t height;
    uint32_t stride;
    LBFrameFormat format;
    uint64_t frame_number;
    uint64_t timestamp_ns;
    uint8_t* pixels;
} LBFrame;

/*
 * Initialize the renderer.
 *
 * @param width    Initial display width
 * @param height   Initial display height
 * @param context  Output: renderer context handle
 * @return         LB_OK on success, error code otherwise
 */
LBError lb_renderer_init(uint32_t width, uint32_t height, LBRenderContext* context);

/*
 * Process GPU commands from guest.
 *
 * @param context    Renderer context
 * @param cmd_buffer Buffer containing encoded GPU commands
 * @param cmd_size   Size of command buffer in bytes
 * @return           LB_OK on success, error code otherwise
 */
LBError lb_renderer_process_commands(LBRenderContext context,
                                      const void* cmd_buffer,
                                      size_t cmd_size);

/*
 * Get the current rendered frame.
 *
 * @param context  Renderer context
 * @param frame    Output: frame data (pixels pointer valid until next call)
 * @return         LB_OK on success, error code otherwise
 */
LBError lb_renderer_get_frame(LBRenderContext context, LBFrame* frame);

/*
 * Resize the display.
 *
 * @param context  Renderer context
 * @param width    New display width
 * @param height   New display height
 * @return         LB_OK on success, error code otherwise
 */
LBError lb_renderer_resize(LBRenderContext context, uint32_t width, uint32_t height);

/*
 * Set display rotation.
 *
 * @param context  Renderer context
 * @param rotation Rotation in degrees (0, 90, 180, 270)
 * @return         LB_OK on success, error code otherwise
 */
LBError lb_renderer_set_rotation(LBRenderContext context, int rotation);

/*
 * Clean up renderer resources.
 *
 * @param context  Renderer context (will be invalidated)
 */
void lb_renderer_cleanup(LBRenderContext context);

/*
 * Get error message for error code.
 *
 * @param error  Error code
 * @return       Human-readable error message
 */
const char* lb_renderer_error_string(LBError error);

#ifdef __cplusplus
}
#endif

#endif /* LINBLOCK_RENDER_API_H */
EOF

    log_info "Wrapper header created"
}

print_summary() {
    echo ""
    echo "=========================================="
    echo "  libOpenglRender Extraction Complete"
    echo "=========================================="
    echo ""
    echo "Extracted to: $EMUGL_DIR"
    echo ""
    echo "Next steps:"
    echo "  1. Install build dependencies:"
    echo "     sudo apt-get install libegl-dev libgles-dev libgl-dev"
    echo ""
    echo "  2. Build libOpenglRender:"
    echo "     cd $EMUGL_DIR"
    echo "     mkdir build && cd build"
    echo "     cmake .."
    echo "     ninja"
    echo ""
    echo "  3. The library will be at:"
    echo "     $EMUGL_DIR/build/libOpenglRender.so"
    echo ""
}

# Main execution
main() {
    log_info "LinBlock libOpenglRender Extraction"
    log_info "==================================="

    check_dependencies
    clone_source
    extract_emugl
    create_linblock_cmake
    create_wrapper_header
    print_summary
}

main "$@"
