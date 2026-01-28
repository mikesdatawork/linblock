#!/bin/bash
# setup_aosp_build.sh - Install AOSP build dependencies and configure environment
#
# This script installs all packages required to build AOSP on Ubuntu/Debian,
# configures ccache, sets up environment variables, and validates the Java version.
#
# Usage: sudo ./setup_aosp_build.sh
# After running, source ~/.bashrc or open a new terminal.

set -euo pipefail

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}[INFO]${NC} $1"; }
warn()  { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Determine actual user (not root)
ACTUAL_USER="${SUDO_USER:-$(logname 2>/dev/null || echo '')}"
ACTUAL_HOME=""
if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
    ACTUAL_HOME=$(eval echo "~$ACTUAL_USER")
else
    ACTUAL_HOME="$HOME"
fi

echo "============================================"
echo " LinBlock AOSP Build Environment Setup"
echo "============================================"
echo ""

# Check for root
if [ "$(id -u)" -ne 0 ]; then
    error "This script must be run as root (use sudo)."
    echo "Usage: sudo $0"
    exit 1
fi

# Detect distro
if [ -f /etc/os-release ]; then
    . /etc/os-release
    DISTRO="$ID"
    DISTRO_VERSION="$VERSION_ID"
    info "Detected: $PRETTY_NAME"
else
    error "Cannot detect Linux distribution. This script requires Ubuntu or Debian."
    exit 1
fi

if [[ "$DISTRO" != "ubuntu" && "$DISTRO" != "debian" ]]; then
    warn "This script is designed for Ubuntu/Debian. Other distros may need manual adjustment."
fi

# Step 1: Install build dependencies
info "Step 1: Installing build dependencies..."

apt-get update

apt-get install -y \
    build-essential \
    git \
    git-lfs \
    curl \
    wget \
    zip \
    unzip \
    python3 \
    python3-pip \
    python3-venv \
    python3-mako \
    openjdk-17-jdk \
    openjdk-17-jre \
    flex \
    bison \
    gperf \
    libncurses5 \
    lib32ncurses-dev \
    libxml2-utils \
    xsltproc \
    zlib1g-dev \
    libssl-dev \
    libc6-dev \
    libgl1-mesa-dev \
    g++-multilib \
    gcc-multilib \
    gnupg \
    bc \
    rsync \
    lz4 \
    ccache \
    fontconfig \
    libfontconfig1 \
    libfontconfig1-dev \
    libfreetype6-dev \
    e2fsprogs \
    dosfstools \
    mtools \
    device-tree-compiler \
    libelf-dev \
    squashfs-tools \
    pngcrush \
    schedtool \
    dpkg-dev \
    liblz4-tool \
    optipng \
    maven \
    imagemagick

info "Build dependencies installed."

# Step 2: Install repo tool
info "Step 2: Installing repo tool..."

REPO_BIN="/usr/local/bin/repo"
if [ ! -f "$REPO_BIN" ] || ! "$REPO_BIN" version &>/dev/null; then
    curl -s https://storage.googleapis.com/git-repo-downloads/repo > "$REPO_BIN"
    chmod a+x "$REPO_BIN"
    info "repo tool installed at $REPO_BIN."
else
    info "repo tool already installed."
fi

# Verify repo
repo version 2>/dev/null || warn "repo tool may not be fully functional."

echo ""

# Step 3: Configure Java
info "Step 3: Configuring Java..."

JAVA_HOME_PATH="/usr/lib/jvm/java-17-openjdk-amd64"
if [ ! -d "$JAVA_HOME_PATH" ]; then
    # Try alternative path
    JAVA_HOME_PATH=$(dirname $(dirname $(readlink -f $(which java 2>/dev/null) || echo "/usr/lib/jvm/java-17-openjdk-amd64/bin/java")))
fi

if [ -d "$JAVA_HOME_PATH" ]; then
    info "Java home: $JAVA_HOME_PATH"
else
    warn "Could not determine JAVA_HOME. Please set it manually."
fi

# Verify Java version
JAVA_VER=$(java -version 2>&1 | head -1 | grep -oP '\d+' | head -1)
if [ "$JAVA_VER" = "17" ]; then
    info "Java version: 17 (correct)"
else
    warn "Java version is $JAVA_VER. AOSP Android 14 requires Java 17."
    warn "Set JAVA_HOME to point to JDK 17."
fi

echo ""

# Step 4: Configure ccache
info "Step 4: Configuring ccache..."

CCACHE_DIR_PATH="$ACTUAL_HOME/.ccache"
CCACHE_SIZE="50G"

# Create ccache directory
mkdir -p "$CCACHE_DIR_PATH"
if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
    chown "$ACTUAL_USER:$ACTUAL_USER" "$CCACHE_DIR_PATH"
fi

# Set ccache max size
ccache -M "$CCACHE_SIZE" 2>/dev/null || true

info "ccache configured: dir=$CCACHE_DIR_PATH, max_size=$CCACHE_SIZE"

echo ""

# Step 5: Configure environment variables
info "Step 5: Setting up environment variables..."

BASHRC="$ACTUAL_HOME/.bashrc"
ENV_MARKER="# LinBlock AOSP Build Environment"

if ! grep -q "$ENV_MARKER" "$BASHRC" 2>/dev/null; then
    cat >> "$BASHRC" <<EOF

$ENV_MARKER
export JAVA_HOME=$JAVA_HOME_PATH
export PATH="\$JAVA_HOME/bin:\$PATH"
export USE_CCACHE=1
export CCACHE_EXEC=\$(which ccache)
export CCACHE_DIR=$CCACHE_DIR_PATH
export CCACHE_MAXSIZE=$CCACHE_SIZE

# Android build settings
export ALLOW_MISSING_DEPENDENCIES=true
export BUILD_BROKEN_DUP_RULES=true
export LC_ALL=C

# LinBlock device
export LINBLOCK_DEVICE=linblock_x86_64
EOF

    if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
        chown "$ACTUAL_USER:$ACTUAL_USER" "$BASHRC"
    fi

    info "Environment variables added to $BASHRC."
    warn "Run 'source $BASHRC' or open a new terminal to activate."
else
    info "Environment variables already configured in $BASHRC."
fi

echo ""

# Step 6: Configure git (if not already configured)
info "Step 6: Checking git configuration..."

if [ -n "$ACTUAL_USER" ] && [ "$ACTUAL_USER" != "root" ]; then
    GIT_NAME=$(su - "$ACTUAL_USER" -c 'git config --global user.name' 2>/dev/null || echo "")
    GIT_EMAIL=$(su - "$ACTUAL_USER" -c 'git config --global user.email' 2>/dev/null || echo "")

    if [ -z "$GIT_NAME" ] || [ -z "$GIT_EMAIL" ]; then
        warn "git user.name and/or user.email not configured."
        echo "  Run these commands as your regular user:"
        echo "    git config --global user.name 'Your Name'"
        echo "    git config --global user.email 'your.email@example.com'"
    else
        info "git configured: $GIT_NAME <$GIT_EMAIL>"
    fi
fi

echo ""

# Step 7: Validate installation
info "Step 7: Validating installation..."

ERRORS=0

# Check critical commands
for cmd in git python3 java javac make gcc g++ flex bison gperf repo ccache; do
    if command -v "$cmd" &>/dev/null; then
        VER=$("$cmd" --version 2>&1 | head -1 || echo "unknown")
        info "  $cmd: $VER"
    else
        error "  $cmd: NOT FOUND"
        ((ERRORS++))
    fi
done

echo ""

# Step 8: System resource check
info "Step 8: System resource check..."

# RAM
TOTAL_RAM_GB=$(awk '/MemTotal/ {printf "%.0f", $2/1024/1024}' /proc/meminfo)
if [ "$TOTAL_RAM_GB" -ge 16 ]; then
    info "RAM: ${TOTAL_RAM_GB} GB (OK)"
else
    warn "RAM: ${TOTAL_RAM_GB} GB (16 GB+ recommended for AOSP builds)"
fi

# Disk space
AVAIL_GB=$(df -BG --output=avail "$ACTUAL_HOME" | tail -1 | tr -d ' G')
if [ "$AVAIL_GB" -ge 300 ]; then
    info "Disk: ${AVAIL_GB} GB available (OK)"
elif [ "$AVAIL_GB" -ge 100 ]; then
    warn "Disk: ${AVAIL_GB} GB available (300 GB+ recommended)"
else
    error "Disk: ${AVAIL_GB} GB available (300 GB+ required)"
    ((ERRORS++))
fi

# CPU cores
CORES=$(nproc)
info "CPU cores: $CORES (build will use -j$CORES)"

echo ""
echo "============================================"
echo " Setup Complete"
echo "============================================"
echo ""

if [ "$ERRORS" -gt 0 ]; then
    error "$ERRORS critical issues found. Please resolve before building."
    exit 1
else
    info "All checks passed. Build environment is ready."
fi

echo ""
echo "Next steps:"
echo "  1. source $BASHRC"
echo "  2. mkdir -p ~/aosp && cd ~/aosp"
echo "  3. repo init -u https://android.googlesource.com/platform/manifest -b android-14.0.0_r1"
echo "  4. repo sync -c -j8 --no-tags --no-clone-bundle"
echo "  5. source build/envsetup.sh"
echo "  6. lunch linblock_x86_64-userdebug"
echo "  7. make -j$(nproc)"
echo ""
echo "See docs/guides/aosp_fetch.md for detailed instructions."
