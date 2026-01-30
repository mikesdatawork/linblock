#!/bin/bash
#
# fetch_android_x86.sh - Download and extract Android-x86 kernel and system files
#
# This script downloads an Android-x86 ISO and extracts the kernel, initrd,
# and system image files needed for LinBlock emulation.
#
# Usage:
#   ./fetch_android_x86.sh [OPTIONS]
#
# Options:
#   -v, --version VERSION   Android version to download (default: 9.0-r2)
#   -o, --output DIR        Output directory (default: ~/LinBlock/images)
#   -k, --keep-iso          Keep the downloaded ISO after extraction
#   -h, --help              Show this help message
#
# Supported versions:
#   9.0-r2    - Android 9 Pie (stable, recommended)
#   8.1-r6    - Android 8.1 Oreo (stable)
#   7.1-r5    - Android 7.1 Nougat (legacy)
#

set -e

# Default configuration
ANDROID_VERSION="9.0-r2"
OUTPUT_DIR="$HOME/LinBlock/images"
KEEP_ISO=false
TEMP_DIR=""

# Android-x86 download base URL
BASE_URL="https://sourceforge.net/projects/android-x86/files/Release"

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

show_help() {
    head -30 "$0" | tail -25 | sed 's/^# //' | sed 's/^#//'
    exit 0
}

cleanup() {
    if [ -n "$TEMP_DIR" ] && [ -d "$TEMP_DIR" ]; then
        print_info "Cleaning up temporary files..."
        sudo umount "$TEMP_DIR/mnt" 2>/dev/null || true
        rm -rf "$TEMP_DIR"
    fi
}

trap cleanup EXIT

check_dependencies() {
    local missing=()

    for cmd in wget unsquashfs; do
        if ! command -v "$cmd" &> /dev/null; then
            missing+=("$cmd")
        fi
    done

    if [ ${#missing[@]} -gt 0 ]; then
        print_error "Missing required tools: ${missing[*]}"
        echo ""
        echo "Install them with:"
        echo "  sudo apt-get install wget squashfs-tools"
        exit 1
    fi
}

get_iso_url() {
    local version="$1"
    local arch="x86_64"

    # Construct the download URL based on version
    case "$version" in
        9.0-r2)
            echo "${BASE_URL}%209.0/android-x86_64-9.0-r2.iso/download"
            ;;
        8.1-r6)
            echo "${BASE_URL}%208.1/android-x86_64-8.1-r6.iso/download"
            ;;
        7.1-r5)
            echo "${BASE_URL}%207.1/android-x86_64-7.1-r5.iso/download"
            ;;
        *)
            print_error "Unsupported version: $version"
            echo "Supported versions: 9.0-r2, 8.1-r6, 7.1-r5"
            exit 1
            ;;
    esac
}

get_iso_filename() {
    local version="$1"
    echo "android-x86_64-${version}.iso"
}

download_iso() {
    local url="$1"
    local output="$2"

    print_info "Downloading Android-x86 ISO..."
    print_info "URL: $url"
    print_info "This may take a while (600-900 MB)..."
    echo ""

    if [ -f "$output" ]; then
        print_warning "ISO already exists: $output"
        read -p "Re-download? [y/N] " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_info "Using existing ISO"
            return 0
        fi
    fi

    wget --progress=bar:force -O "$output" "$url" || {
        print_error "Download failed"
        exit 1
    }

    print_success "Download complete: $output"
}

extract_from_iso() {
    local iso_path="$1"
    local output_dir="$2"
    local version="$3"

    TEMP_DIR=$(mktemp -d)
    local mount_point="$TEMP_DIR/mnt"
    mkdir -p "$mount_point"

    print_info "Mounting ISO..."
    sudo mount -o loop,ro "$iso_path" "$mount_point" || {
        print_error "Failed to mount ISO. Try running with sudo."
        exit 1
    }

    # Create version-specific output directory
    local version_dir="$output_dir/android-x86-$version"
    mkdir -p "$version_dir"
    mkdir -p "$version_dir/boot"

    print_info "Extracting kernel files..."

    # Extract kernel
    if [ -f "$mount_point/kernel" ]; then
        cp "$mount_point/kernel" "$version_dir/boot/kernel"
        print_success "Extracted: kernel"
    else
        print_error "kernel not found in ISO"
    fi

    # Extract initrd
    if [ -f "$mount_point/initrd.img" ]; then
        cp "$mount_point/initrd.img" "$version_dir/boot/initrd.img"
        print_success "Extracted: initrd.img"
    else
        print_error "initrd.img not found in ISO"
    fi

    # Extract ramdisk if present
    if [ -f "$mount_point/ramdisk.img" ]; then
        cp "$mount_point/ramdisk.img" "$version_dir/boot/ramdisk.img"
        print_success "Extracted: ramdisk.img"
    fi

    # Extract system image
    print_info "Extracting system image (this may take a few minutes)..."

    if [ -f "$mount_point/system.sfs" ]; then
        # System is in squashfs format, need to extract
        print_info "Extracting system.sfs (squashfs)..."

        local sfs_temp="$TEMP_DIR/system_sfs"
        mkdir -p "$sfs_temp"

        sudo unsquashfs -d "$sfs_temp" "$mount_point/system.sfs" || {
            print_error "Failed to extract system.sfs"
            sudo umount "$mount_point"
            exit 1
        }

        # The system.img is inside the squashfs
        if [ -f "$sfs_temp/system.img" ]; then
            sudo cp "$sfs_temp/system.img" "$version_dir/system.img"
            sudo chown $(id -u):$(id -g) "$version_dir/system.img"
            print_success "Extracted: system.img (from system.sfs)"
        else
            print_warning "system.img not found inside system.sfs"
            # List contents for debugging
            ls -la "$sfs_temp/"
        fi

    elif [ -f "$mount_point/system.img" ]; then
        # System is already an img file
        cp "$mount_point/system.img" "$version_dir/system.img"
        print_success "Extracted: system.img"
    else
        print_error "No system image found in ISO"
    fi

    # Copy install scripts if present (useful for reference)
    if [ -f "$mount_point/install.img" ]; then
        cp "$mount_point/install.img" "$version_dir/boot/install.img"
        print_info "Copied: install.img (installer ramdisk)"
    fi

    # Unmount ISO
    print_info "Unmounting ISO..."
    sudo umount "$mount_point"

    # Create a profile template
    create_profile_template "$version_dir" "$version"

    print_success "Extraction complete!"
    echo ""
    echo "Files extracted to: $version_dir"
    echo ""
    ls -lh "$version_dir/"
    ls -lh "$version_dir/boot/"
}

create_profile_template() {
    local version_dir="$1"
    local version="$2"

    cat > "$version_dir/profile_template.yaml" << EOF
# LinBlock Profile Template for Android-x86 $version
# Copy this to your profile and customize as needed

name: "Android-x86 $version"
description: "Android-x86 $version running in LinBlock"

# Boot configuration
boot:
  kernel: "$version_dir/boot/kernel"
  initrd: "$version_dir/boot/initrd.img"
  system_image: "$version_dir/system.img"
  kernel_cmdline: "root=/dev/ram0 androidboot.selinux=permissive buildvariant=userdebug"

# Device settings
device:
  screen_width: 1080
  screen_height: 1920
  dpi: 480

# Performance settings
performance:
  ram_mb: 4096
  cpu_cores: 4
  hypervisor: "kvm"

# Graphics settings
graphics:
  gpu_mode: "host"

# Network settings
network:
  mode: "user"

# ADB settings
adb:
  enabled: true
  port: 5555
EOF

    print_success "Created profile template: $version_dir/profile_template.yaml"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -v|--version)
            ANDROID_VERSION="$2"
            shift 2
            ;;
        -o|--output)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        -k|--keep-iso)
            KEEP_ISO=true
            shift
            ;;
        -h|--help)
            show_help
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            ;;
    esac
done

# Main execution
echo ""
echo "=========================================="
echo "  LinBlock Android-x86 Fetcher"
echo "=========================================="
echo ""
print_info "Android version: $ANDROID_VERSION"
print_info "Output directory: $OUTPUT_DIR"
echo ""

# Check dependencies
check_dependencies

# Create output directory
mkdir -p "$OUTPUT_DIR"

# Get download URL and filename
ISO_URL=$(get_iso_url "$ANDROID_VERSION")
ISO_FILENAME=$(get_iso_filename "$ANDROID_VERSION")
ISO_PATH="$OUTPUT_DIR/$ISO_FILENAME"

# Download ISO
download_iso "$ISO_URL" "$ISO_PATH"

# Extract files
extract_from_iso "$ISO_PATH" "$OUTPUT_DIR" "$ANDROID_VERSION"

# Clean up ISO if not keeping
if [ "$KEEP_ISO" = false ]; then
    print_info "Removing ISO to save space..."
    rm -f "$ISO_PATH"
    print_success "ISO removed"
else
    print_info "ISO kept at: $ISO_PATH"
fi

echo ""
echo "=========================================="
echo "  Setup Complete!"
echo "=========================================="
echo ""
echo "To use these files in LinBlock:"
echo ""
echo "1. Edit your OS profile to include:"
echo "   - kernel: $OUTPUT_DIR/android-x86-$ANDROID_VERSION/boot/kernel"
echo "   - initrd: $OUTPUT_DIR/android-x86-$ANDROID_VERSION/boot/initrd.img"
echo "   - system_image: $OUTPUT_DIR/android-x86-$ANDROID_VERSION/system.img"
echo ""
echo "2. Or copy the profile template:"
echo "   cp $OUTPUT_DIR/android-x86-$ANDROID_VERSION/profile_template.yaml ~/LinBlock/profiles/"
echo ""
print_success "Done!"
