#!/bin/bash
# setup_kvm.sh - Configure KVM virtualization for LinBlock
#
# This script sets up KVM on the host system, including:
# - Loading KVM kernel modules
# - Creating udev rules for /dev/kvm group access
# - Adding the current user to the kvm group
# - Checking nested virtualization support
# - Verifying /dev/dri access for GPU passthrough
#
# Usage: sudo ./setup_kvm.sh
#
# Rollback: See the end of this script for rollback instructions.

set -euo pipefail

# Color output helpers
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Track changes for rollback
CHANGES=()

record_change() {
    CHANGES+=("$1")
}

print_rollback() {
    if [ ${#CHANGES[@]} -gt 0 ]; then
        echo ""
        echo "=== Rollback Instructions ==="
        echo "To undo the changes made by this script, run the following commands:"
        echo ""
        for change in "${CHANGES[@]}"; do
            echo "  $change"
        done
        echo ""
    fi
}

# Check for root privileges
if [ "$(id -u)" -ne 0 ]; then
    error "This script must be run as root (use sudo)."
    echo "Usage: sudo $0"
    exit 1
fi

# Determine the actual user (not root) who invoked sudo
ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo '')}"
if [ -z "$ACTUAL_USER" ] || [ "$ACTUAL_USER" = "root" ]; then
    warn "Cannot determine non-root user. User group changes may need to be done manually."
fi

echo "======================================"
echo " LinBlock KVM Setup"
echo "======================================"
echo ""

# Step 1: Detect CPU vendor and load appropriate KVM module
info "Step 1: Detecting CPU and loading KVM modules..."

CPU_VENDOR=""
if grep -q 'vendor_id.*AuthenticAMD' /proc/cpuinfo 2>/dev/null; then
    CPU_VENDOR="amd"
    KVM_MODULE="kvm_amd"
    VIRT_FLAG="svm"
elif grep -q 'vendor_id.*GenuineIntel' /proc/cpuinfo 2>/dev/null; then
    CPU_VENDOR="intel"
    KVM_MODULE="kvm_intel"
    VIRT_FLAG="vmx"
else
    error "Unsupported CPU vendor. KVM requires AMD or Intel CPU."
    exit 1
fi

info "Detected CPU vendor: $CPU_VENDOR"

# Check if virtualization is enabled in BIOS/UEFI
if ! grep -qE "svm|vmx" /proc/cpuinfo 2>/dev/null; then
    error "Hardware virtualization ($VIRT_FLAG) not detected."
    error "Please enable VT-x (Intel) or AMD-V (AMD) in your BIOS/UEFI settings."
    exit 1
fi

info "Hardware virtualization ($VIRT_FLAG) is enabled."

# Load KVM modules
if ! lsmod | grep -q "^kvm " 2>/dev/null; then
    info "Loading kvm module..."
    modprobe kvm
    record_change "sudo modprobe -r $KVM_MODULE kvm  # Unload KVM modules"
    info "kvm module loaded."
else
    info "kvm module already loaded."
fi

if ! lsmod | grep -q "^${KVM_MODULE} " 2>/dev/null; then
    info "Loading $KVM_MODULE module..."
    modprobe "$KVM_MODULE"
    info "$KVM_MODULE module loaded."
else
    info "$KVM_MODULE module already loaded."
fi

# Ensure modules load at boot
MODULES_FILE="/etc/modules-load.d/linblock-kvm.conf"
if [ ! -f "$MODULES_FILE" ]; then
    info "Creating $MODULES_FILE for persistent module loading..."
    cat > "$MODULES_FILE" <<EOF
# LinBlock KVM modules - auto-loaded at boot
kvm
${KVM_MODULE}
EOF
    record_change "sudo rm $MODULES_FILE  # Remove auto-load config"
    info "Module auto-load configured."
else
    info "Module auto-load config already exists at $MODULES_FILE."
fi

echo ""

# Step 2: Create udev rule for /dev/kvm group access
info "Step 2: Setting up /dev/kvm permissions..."

UDEV_RULE="/etc/udev/rules.d/99-linblock-kvm.rules"
if [ ! -f "$UDEV_RULE" ]; then
    info "Creating udev rule for /dev/kvm group access..."
    cat > "$UDEV_RULE" <<EOF
# LinBlock: Allow kvm group access to /dev/kvm
KERNEL=="kvm", GROUP="kvm", MODE="0660"
EOF
    record_change "sudo rm $UDEV_RULE  # Remove udev rule"
    udevadm control --reload-rules 2>/dev/null || true
    udevadm trigger 2>/dev/null || true
    info "Udev rule created and reloaded."
else
    info "Udev rule already exists at $UDEV_RULE."
fi

# Ensure the kvm group exists
if ! getent group kvm >/dev/null 2>&1; then
    info "Creating kvm group..."
    groupadd kvm
    record_change "sudo groupdel kvm  # Remove kvm group"
    info "kvm group created."
else
    info "kvm group already exists."
fi

# Set permissions on /dev/kvm now (udev rule takes effect on next boot/replug)
if [ -e /dev/kvm ]; then
    chown root:kvm /dev/kvm
    chmod 0660 /dev/kvm
    info "/dev/kvm permissions set to root:kvm 0660."
else
    warn "/dev/kvm does not exist. It should appear after KVM modules are loaded."
fi

echo ""

# Step 3: Add user to kvm group
info "Step 3: Adding user to kvm group..."

if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
    if id -nG "$ACTUAL_USER" | grep -qw kvm 2>/dev/null; then
        info "User '$ACTUAL_USER' is already in the kvm group."
    else
        usermod -aG kvm "$ACTUAL_USER"
        record_change "sudo gpasswd -d $ACTUAL_USER kvm  # Remove user from kvm group"
        info "User '$ACTUAL_USER' added to kvm group."
        warn "You must log out and log back in for group changes to take effect."
        warn "Alternatively, run: newgrp kvm"
    fi
else
    warn "Skipping user group addition (could not determine non-root user)."
    echo "  Manually run: sudo usermod -aG kvm YOUR_USERNAME"
fi

echo ""

# Step 4: Check nested virtualization
info "Step 4: Checking nested virtualization..."

NESTED_PATH=""
if [ "$CPU_VENDOR" = "intel" ]; then
    NESTED_PATH="/sys/module/kvm_intel/parameters/nested"
elif [ "$CPU_VENDOR" = "amd" ]; then
    NESTED_PATH="/sys/module/kvm_amd/parameters/nested"
fi

if [ -n "$NESTED_PATH" ] && [ -f "$NESTED_PATH" ]; then
    NESTED_VAL=$(cat "$NESTED_PATH")
    if [ "$NESTED_VAL" = "Y" ] || [ "$NESTED_VAL" = "1" ]; then
        info "Nested virtualization is ENABLED."
    else
        info "Nested virtualization is DISABLED."
        info "LinBlock does not require nested virtualization, but it can be enabled with:"
        echo "  echo 'options ${KVM_MODULE} nested=1' | sudo tee /etc/modprobe.d/kvm-nested.conf"
        echo "  sudo modprobe -r ${KVM_MODULE} && sudo modprobe ${KVM_MODULE}"
    fi
else
    warn "Unable to determine nested virtualization status."
fi

echo ""

# Step 5: Verify /dev/dri access for GPU rendering
info "Step 5: Checking GPU device access (/dev/dri)..."

if [ -d /dev/dri ]; then
    info "/dev/dri exists."
    ls -la /dev/dri/ 2>/dev/null | while read -r line; do
        echo "  $line"
    done

    # Check if user has access to render nodes
    if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
        RENDER_NODES=$(ls /dev/dri/renderD* 2>/dev/null || true)
        if [ -n "$RENDER_NODES" ]; then
            info "Render nodes found. Checking access for user '$ACTUAL_USER'..."
            # Ensure user is in the render or video group
            DRI_GROUP=$(stat -c '%G' /dev/dri/renderD128 2>/dev/null || echo "render")
            if id -nG "$ACTUAL_USER" | grep -qw "$DRI_GROUP" 2>/dev/null; then
                info "User '$ACTUAL_USER' has access to GPU render nodes (group: $DRI_GROUP)."
            else
                warn "User '$ACTUAL_USER' may not have GPU access."
                echo "  Run: sudo usermod -aG $DRI_GROUP $ACTUAL_USER"
            fi
        else
            warn "No GPU render nodes found. Software rendering will be used."
        fi
    fi
else
    warn "/dev/dri not found. GPU acceleration will not be available."
    warn "LinBlock will fall back to software rendering (SwiftShader)."
fi

echo ""

# Step 6: Verify KVM is functional
info "Step 6: Verifying KVM functionality..."

if [ -e /dev/kvm ]; then
    # Quick test: try to open /dev/kvm
    if python3 -c "
import fcntl, os, struct
fd = os.open('/dev/kvm', os.O_RDWR)
KVM_GET_API_VERSION = 0xAE00
version = fcntl.ioctl(fd, KVM_GET_API_VERSION, 0)
os.close(fd)
print(f'KVM API version: {version}')
assert version == 12, f'Unexpected KVM API version: {version}'
" 2>/dev/null; then
        info "KVM is functional. API version verified."
    else
        # Try simpler check
        if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
            info "/dev/kvm is accessible (read/write)."
        else
            warn "/dev/kvm exists but may not be fully accessible."
        fi
    fi
else
    error "/dev/kvm does not exist. KVM setup may have failed."
fi

echo ""
echo "======================================"
echo " Setup Complete"
echo "======================================"
echo ""
info "KVM has been configured for LinBlock."
if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
    echo ""
    echo "IMPORTANT: Log out and log back in for group changes to take effect."
    echo "Then verify with: groups $ACTUAL_USER"
fi

# Print rollback instructions
print_rollback

echo ""
echo "=== Quick Verification ==="
echo "After logging back in, run these commands to verify:"
echo "  groups                    # Should include 'kvm'"
echo "  ls -la /dev/kvm           # Should show group 'kvm' with rw access"
echo "  ./scripts/setup/check_prerequisites.sh   # Full prerequisite check"
