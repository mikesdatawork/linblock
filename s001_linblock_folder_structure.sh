#!/bin/bash
# s001_linblock_folder_structure.sh
# Creates the LinBlock project folder structure
# Project: LinBlock - Custom Android Emulator with Secure Minimal OS

PROJECT_ROOT="/home/user/projects/linblock"

echo "Creating LinBlock project structure at: $PROJECT_ROOT"

# Create main project directory
mkdir -p "$PROJECT_ROOT"

# Documentation structure
mkdir -p "$PROJECT_ROOT/docs/architecture"
mkdir -p "$PROJECT_ROOT/docs/design"
mkdir -p "$PROJECT_ROOT/docs/guides"
mkdir -p "$PROJECT_ROOT/docs/api"
mkdir -p "$PROJECT_ROOT/docs/security"
mkdir -p "$PROJECT_ROOT/docs/meeting-notes"

# AI Agent configurations
mkdir -p "$PROJECT_ROOT/agents/configs"
mkdir -p "$PROJECT_ROOT/agents/prompts"
mkdir -p "$PROJECT_ROOT/agents/tools"
mkdir -p "$PROJECT_ROOT/agents/workflows"

# Source code - Emulator GUI (based on GTK dashboard pattern)
mkdir -p "$PROJECT_ROOT/src/config"
mkdir -p "$PROJECT_ROOT/src/ui/components"
mkdir -p "$PROJECT_ROOT/src/pages"
mkdir -p "$PROJECT_ROOT/src/modules"
mkdir -p "$PROJECT_ROOT/src/utils"

# Source code - Emulator core
mkdir -p "$PROJECT_ROOT/src/emulator/cpu"
mkdir -p "$PROJECT_ROOT/src/emulator/memory"
mkdir -p "$PROJECT_ROOT/src/emulator/devices"
mkdir -p "$PROJECT_ROOT/src/emulator/display"
mkdir -p "$PROJECT_ROOT/src/emulator/network"
mkdir -p "$PROJECT_ROOT/src/emulator/storage"

# Android OS build components
mkdir -p "$PROJECT_ROOT/android/base"
mkdir -p "$PROJECT_ROOT/android/kernel"
mkdir -p "$PROJECT_ROOT/android/system"
mkdir -p "$PROJECT_ROOT/android/vendor"
mkdir -p "$PROJECT_ROOT/android/packages"
mkdir -p "$PROJECT_ROOT/android/security"
mkdir -p "$PROJECT_ROOT/android/overlays"

# App management subsystem
mkdir -p "$PROJECT_ROOT/src/app-manager/permissions"
mkdir -p "$PROJECT_ROOT/src/app-manager/process"
mkdir -p "$PROJECT_ROOT/src/app-manager/freeze"
mkdir -p "$PROJECT_ROOT/src/app-manager/install"

# Resources (following GTK starter pattern)
mkdir -p "$PROJECT_ROOT/resources/css"
mkdir -p "$PROJECT_ROOT/resources/fonts"
mkdir -p "$PROJECT_ROOT/resources/images"
mkdir -p "$PROJECT_ROOT/resources/icons"
mkdir -p "$PROJECT_ROOT/resources/videos"

# Testing
mkdir -p "$PROJECT_ROOT/tests/unit"
mkdir -p "$PROJECT_ROOT/tests/integration"
mkdir -p "$PROJECT_ROOT/tests/emulator"
mkdir -p "$PROJECT_ROOT/tests/security"
mkdir -p "$PROJECT_ROOT/tests/performance"

# Build and CI/CD
mkdir -p "$PROJECT_ROOT/build/scripts"
mkdir -p "$PROJECT_ROOT/build/configs"
mkdir -p "$PROJECT_ROOT/build/output"

# Scripts and utilities
mkdir -p "$PROJECT_ROOT/scripts/setup"
mkdir -p "$PROJECT_ROOT/scripts/dev"
mkdir -p "$PROJECT_ROOT/scripts/release"

# Vendor and third-party
mkdir -p "$PROJECT_ROOT/vendor"

# Temporary and cache (gitignored)
mkdir -p "$PROJECT_ROOT/.cache"
mkdir -p "$PROJECT_ROOT/.tmp"

echo "Folder structure created successfully."
echo ""
echo "Structure overview:"
find "$PROJECT_ROOT" -type d | head -60

