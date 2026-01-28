#!/bin/bash
# check_prerequisites.sh - Verify host system requirements for LinBlock
set -e

PASS=0
FAIL=0
WARN=0

check() {
    local desc="$1"
    local result="$2"
    if [ "$result" = "pass" ]; then
        echo "[PASS] $desc"
        ((PASS++))
    elif [ "$result" = "warn" ]; then
        echo "[WARN] $desc"
        ((WARN++))
    else
        echo "[FAIL] $desc"
        ((FAIL++))
    fi
}

echo "=== LinBlock Prerequisite Check ==="
echo ""

# CPU virtualization
if grep -qE 'svm|vmx' /proc/cpuinfo 2>/dev/null; then
    check "CPU virtualization support (SVM/VMX)" "pass"
else
    check "CPU virtualization support (SVM/VMX) - Enable in BIOS" "fail"
fi

# KVM module
if lsmod | grep -q kvm 2>/dev/null; then
    check "KVM kernel module loaded" "pass"
else
    check "KVM kernel module not loaded - run: sudo modprobe kvm kvm_amd" "fail"
fi

# /dev/kvm access
if [ -r /dev/kvm ] && [ -w /dev/kvm ]; then
    check "/dev/kvm accessible" "pass"
elif [ -e /dev/kvm ]; then
    check "/dev/kvm exists but not accessible - run: sudo usermod -aG kvm $USER" "fail"
else
    check "/dev/kvm not found" "fail"
fi

# Python 3.10+
PYTHON_VER=$(python3 --version 2>/dev/null | grep -oP '\d+\.\d+' | head -1)
if [ -n "$PYTHON_VER" ]; then
    MAJOR=$(echo "$PYTHON_VER" | cut -d. -f1)
    MINOR=$(echo "$PYTHON_VER" | cut -d. -f2)
    if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
        check "Python $PYTHON_VER (>= 3.10 required)" "pass"
    else
        check "Python $PYTHON_VER (>= 3.10 required)" "fail"
    fi
else
    check "Python 3 not found" "fail"
fi

# PyGObject
if python3 -c "import gi; gi.require_version('Gtk', '3.0'); from gi.repository import Gtk" 2>/dev/null; then
    check "PyGObject (GTK3 bindings)" "pass"
else
    check "PyGObject not found - run: sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0" "fail"
fi

# PyYAML
if python3 -c "import yaml" 2>/dev/null; then
    check "PyYAML" "pass"
else
    check "PyYAML not found - run: pip install PyYAML" "warn"
fi

# pytest
if python3 -c "import pytest" 2>/dev/null; then
    check "pytest" "pass"
else
    check "pytest not found - run: pip install pytest" "warn"
fi

# qemu-utils
if command -v qemu-img &>/dev/null; then
    check "qemu-utils (qemu-img)" "pass"
else
    check "qemu-utils not found - run: sudo apt install qemu-utils" "warn"
fi

# Memory check
TOTAL_MEM_KB=$(grep MemTotal /proc/meminfo | awk '{print $2}')
TOTAL_MEM_GB=$((TOTAL_MEM_KB / 1024 / 1024))
if [ "$TOTAL_MEM_GB" -ge 8 ]; then
    check "RAM: ${TOTAL_MEM_GB}GB (>= 8GB required)" "pass"
elif [ "$TOTAL_MEM_GB" -ge 4 ]; then
    check "RAM: ${TOTAL_MEM_GB}GB (8GB+ recommended)" "warn"
else
    check "RAM: ${TOTAL_MEM_GB}GB (8GB+ required)" "fail"
fi

# Disk space check
AVAIL_DISK_GB=$(df --output=avail -BG . 2>/dev/null | tail -1 | tr -d ' G')
if [ -n "$AVAIL_DISK_GB" ] && [ "$AVAIL_DISK_GB" -ge 50 ]; then
    check "Disk space: ${AVAIL_DISK_GB}GB available (>= 50GB required)" "pass"
elif [ -n "$AVAIL_DISK_GB" ] && [ "$AVAIL_DISK_GB" -ge 20 ]; then
    check "Disk space: ${AVAIL_DISK_GB}GB available (50GB+ recommended)" "warn"
elif [ -n "$AVAIL_DISK_GB" ]; then
    check "Disk space: ${AVAIL_DISK_GB}GB available (50GB+ required)" "fail"
else
    check "Disk space: unable to determine" "warn"
fi

# /dev/dri for GPU
if [ -d /dev/dri ]; then
    check "GPU device /dev/dri available" "pass"
else
    check "GPU device /dev/dri not found (software rendering will be used)" "warn"
fi

# git
if command -v git &>/dev/null; then
    GIT_VER=$(git --version | grep -oP '\d+\.\d+\.\d+')
    check "git $GIT_VER" "pass"
else
    check "git not found - run: sudo apt install git" "fail"
fi

# Kernel version check (5.10+)
KERNEL_VER=$(uname -r | grep -oP '^\d+\.\d+')
if [ -n "$KERNEL_VER" ]; then
    K_MAJOR=$(echo "$KERNEL_VER" | cut -d. -f1)
    K_MINOR=$(echo "$KERNEL_VER" | cut -d. -f2)
    if [ "$K_MAJOR" -gt 5 ] || { [ "$K_MAJOR" -eq 5 ] && [ "$K_MINOR" -ge 10 ]; }; then
        check "Kernel $(uname -r) (>= 5.10 required)" "pass"
    else
        check "Kernel $(uname -r) (>= 5.10 required)" "fail"
    fi
else
    check "Unable to determine kernel version" "warn"
fi

echo ""
echo "=== Results ==="
echo "Passed: $PASS  Warnings: $WARN  Failed: $FAIL"
if [ "$FAIL" -gt 0 ]; then
    echo "Some checks FAILED. Please resolve before running LinBlock."
    exit 1
else
    echo "All critical checks passed."
    exit 0
fi
