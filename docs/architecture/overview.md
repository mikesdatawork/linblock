# LinBlock Architecture Overview

## System Components

```
+-------------------------------------------------------------+
|                      GTK3 GUI Layer                         |
|  +----------+  +----------+  +----------+  +----------+     |
|  | Sidebar  |  |   VNC    |  | Device   |  | Profile  |     |
|  |   Nav    |  | Display  |  | Controls |  | Manager  |     |
|  +----------+  +----------+  +----------+  +----------+     |
+-------------------------------------------------------------+
|                   Emulator Controller                       |
|              (QEMU Process Management)                      |
+-------------------------------------------------------------+
|  +----------+  +----------+  +----------+  +----------+     |
|  |  QEMU    |  | Profile  |  | Logging  |  |  Port    |     |
|  | Process  |  |  Config  |  | Manager  |  | Manager  |     |
|  +----------+  +----------+  +----------+  +----------+     |
+-------------------------------------------------------------+
|              QEMU System Emulator                           |
|           (qemu-system-x86_64 + KVM)                        |
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
2. User selects profile and clicks Power switch
3. Emulator controller builds QEMU command line from profile
4. QEMU subprocess starts with KVM acceleration
5. Kernel boots (direct boot or CD-ROM/GRUB)
6. Serial console output captured to timestamped log file
7. Android init runs, detects system at /dev/sr0
8. SurfaceFlinger initializes (software or hardware rendering)
9. Setup wizard or launcher appears in VNC display

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

### GUI <-> Emulator Controller
- Python API for lifecycle control (start, stop, reset)
- Profile configuration via OSProfile dataclass
- State callbacks for UI updates
- Cleanup handlers for process termination

### GUI <-> QEMU Display
- VNC protocol for display output (localhost:5900+)
- VNC for input events (mouse, keyboard)
- gtk-vnc library (GtkVncDisplay widget)

### Emulator Controller <-> QEMU
- Subprocess management (Popen)
- Command-line arguments for configuration
- Serial console for logging (file output)
- Future: QMP for programmatic control

### Logging
- Serial console: `-serial file:/path/to/boot.log`
- Kernel param: `console=ttyS0`
- Storage: `~/LinBlock/{profile}/logging/boot_{timestamp}.log`

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
