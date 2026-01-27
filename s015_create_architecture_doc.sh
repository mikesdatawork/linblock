#!/bin/bash
# s015_create_architecture_doc.sh
# Creates docs/architecture/overview.md

PROJECT_ROOT="/home/user/projects/linblock"

cat > "$PROJECT_ROOT/docs/architecture/overview.md" << 'EOF'
# LinBlock Architecture Overview

## System Components

```
+-------------------------------------------------------------+
|                      GTK3 GUI Layer                         |
|  +----------+  +----------+  +----------+  +----------+     |
|  | Sidebar  |  | Display  |  |   Apps   |  | Settings |     |
|  |   Nav    |  |  Widget  |  |  Manager |  |  Panel   |     |
|  +----------+  +----------+  +----------+  +----------+     |
+-------------------------------------------------------------+
|                   Emulator Controller                       |
+-------------------------------------------------------------+
|  +----------+  +----------+  +----------+  +----------+     |
|  |   CPU    |  |  Memory  |  | Devices  |  | Display  |     |
|  | Manager  |  | Manager  |  | Manager  |  | Manager  |     |
|  +----------+  +----------+  +----------+  +----------+     |
+-------------------------------------------------------------+
|               Hardware Abstraction Layer                    |
+-------------------------------------------------------------+
|            KVM / Software Emulation Core                    |
+-------------------------------------------------------------+
|                    Linux Host (Mint 22.2)                   |
+-------------------------------------------------------------+
```

## Android OS Stack

```
+-------------------------------------------------------------+
|                     User Applications                       |
+-------------------------------------------------------------+
|                    App Management Layer                     |
|  +------------+  +------------+  +------------+             |
|  | Permission |  |  Process   |  |  Network   |             |
|  |  Manager   |  |  Manager   |  |  Manager   |             |
|  +------------+  +------------+  +------------+             |
+-------------------------------------------------------------+
|                   Android Framework                         |
|  (ActivityManager, PackageManager, WindowManager)           |
+-------------------------------------------------------------+
|                    SELinux Enforcement                      |
+-------------------------------------------------------------+
|                     Android Kernel                          |
+-------------------------------------------------------------+
|                   Virtual Hardware                          |
+-------------------------------------------------------------+
```

## Data Flow

### Boot Sequence
1. User launches LinBlock GUI
2. GUI initializes emulator controller
3. Emulator loads Android system image
4. Kernel boots, init starts
5. Zygote spawns system server
6. Launcher appears in display widget

### Permission Check Flow
1. App requests permission
2. PackageManager intercepts request
3. LinBlock permission manager checks policy
4. If "ask" mode, GUI prompts user
5. Decision recorded in audit log
6. Permission granted or denied

### App Control Flow
1. User selects app in GUI
2. GUI queries app management service
3. Service returns app state and permissions
4. User modifies settings
5. Service applies changes via Android APIs
6. Changes persisted and logged

## Key Interfaces

### Emulator <-> GUI
- D-Bus for control commands
- Shared memory for display buffer
- Event queue for input

### Host <-> Emulator
- KVM ioctls for CPU virtualization
- Memory mapping for RAM
- virtio for devices

### Android <-> App Management
- Binder IPC for service calls
- Content providers for data
- Broadcasts for state changes

## Security Boundaries

```
+-----------------------------------------+
|              Host System                |
|  +-----------------------------------+  |
|  |          Emulator Process         |  |
|  |  +-----------------------------+  |  |
|  |  |      Android Guest          |  |  |
|  |  |  +-----------------------+  |  |  |
|  |  |  |    App Sandbox        |  |  |  |
|  |  |  |  (per application)    |  |  |  |
|  |  |  +-----------------------+  |  |  |
|  |  +-----------------------------+  |  |
|  +-----------------------------------+  |
+-----------------------------------------+
```

Each boundary enforces isolation:
- Host <-> Emulator: Process isolation, memory protection
- Emulator <-> Android: Virtualization boundary
- Android <-> App: SELinux, UID separation, permissions
EOF

echo "Created: $PROJECT_ROOT/docs/architecture/overview.md"
