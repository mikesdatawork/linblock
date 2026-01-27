#!/bin/bash
# s002_create_readme.sh
# Creates the main project README.md

PROJECT_ROOT="/home/user/projects/linblock"

cat > "$PROJECT_ROOT/README.md" << 'EOF'
# LinBlock

A custom Android emulator with a minimal, secure, bloatware-free Android OS.

## Overview

LinBlock is a custom x86_64 Android emulator built from scratch with a GTK3/Python GUI. The bundled Android OS sits between LineageOS simplicity and GrapheneOS security.

The system gives users complete control over installed applications, including permissions, background activity, network access, and process management.

## Goals

- Custom emulator optimized for Linux desktop
- Minimal Android OS with zero bloatware
- User controls all app permissions
- No Google Play Services dependency
- Compatible with F-Droid and Aurora Store
- Strong app isolation and sandboxing

## Target System

```
OS: Linux Mint 22.2 / Debian-based
CPU: x86_64 (AMD/Intel with virtualization)
RAM: 12GB minimum
GPU: AMD/Intel/NVIDIA with OpenGL support
```

## Project Structure

```
linblock/
├── agents/           # AI agent configurations
├── android/          # Android OS build components
├── build/            # Build scripts and configs
├── docs/             # Documentation
├── resources/        # Static assets (CSS, images)
├── scripts/          # Utility scripts
├── src/              # Source code
│   ├── app-manager/  # App control subsystem
│   ├── config/       # Configuration modules
│   ├── emulator/     # Emulator core
│   ├── modules/      # Feature modules
│   ├── pages/        # GUI pages
│   ├── ui/           # GUI components
│   └── utils/        # Utilities
├── tests/            # Test suites
└── vendor/           # Third-party components
```

## Components

### Emulator
- Custom x86_64 virtualization layer
- KVM acceleration when available
- Virtual device framework
- Display rendering via host GPU

### Android OS
- Android 14 (API 34) base
- Minimal system services
- SELinux enforcement
- No pre-installed bloatware

### App Management
- Per-app permission control
- Process freeze/hibernate
- Background restriction
- Network firewall per app
- Permission usage audit

### GUI
- GTK3/Python based
- Dark theme
- Emulator display rendering
- App management interface
- Permission control panels

## Status

Early development. See [docs/](docs/) for current progress.

## License

TBD

## Repository

https://github.com/mikesdatawork/linblock
EOF

echo "Created: $PROJECT_ROOT/README.md"
