# LinBlock GUI Interface Design

> Technical specification for the GTK3 sidebar-driven interface.

---

## 1. Overview

LinBlock uses a GTK3 (PyGObject) single-window application with a persistent
sidebar for navigation and a swappable content area. The interface follows the
structure established in the
[gtk-python-dashboard-starter](https://github.com/mikesdatawork/gtk-python-dashboard-starter)
template and extends it with dynamic sidebar buttons, an OS configuration
wizard, and an embedded emulator display.

---

## 2. Top-Level Window Layout

```
+----------------------------------------------------------+
|                    Gtk.ApplicationWindow                  |
| +----------+-------------------------------------------+ |
| |          |                                           | |
| | Sidebar  |            Content Area                   | |
| | (fixed   |         (Gtk.Stack / swappable)           | |
| |  150 px) |                                           | |
| |          |                                           | |
| +----------+-------------------------------------------+ |
| |                    Status Bar                        | |
| +------------------------------------------------------+ |
+----------------------------------------------------------+
```

- **Sidebar** -- `Sidebar(Gtk.Box)`, vertical, 150 px wide.
- **Content Area** -- `Gtk.Stack` that swaps pages based on sidebar selection.
- **Status Bar** -- Performance metrics, connection state (optional Phase 1).

---

## 3. Sidebar Navigation Structure

The sidebar contains a logo area, four fixed navigation buttons, and a dynamic
section that grows as the user saves OS instances.

```
+---------------------------+
|      LINBLOCK LOGO        |  150 x 150 px image area
+---------------------------+
|  About                    |  Static button
+---------------------------+
|  Load OS                  |  Static button
+---------------------------+
|  OS List                  |  Static button
+---------------------------+
|  [Saved OS Name 1]        |  Dynamic -- one per saved OS
|  [Saved OS Name 2]        |
|  [Saved OS Name N]        |
+---------------------------+
|         (spacer)          |  Gtk.Box expand to fill
+---------------------------+
```

### 3.1 Implementation Notes

| Element | Widget | Details |
|---------|--------|---------|
| Logo | `Gtk.Image` | Loaded from `resources/images/linblock_logo.png`, scaled to 150 x 150 |
| Fixed buttons | `Gtk.Button` | Styled with CSS class `.sidebar-button` |
| Dynamic buttons | `Gtk.Button` | Generated from saved OS profiles; right-click context menu for Rename / Delete |
| Spacer | `Gtk.Box` with `expand=True` | Pushes content upward |

- Sidebar extends the template's `Sidebar(Gtk.Box)` class.
- Dynamic buttons are rebuilt when an OS profile is created, renamed, or deleted.
- Active button receives the `.sidebar-button-active` CSS class.

---

## 4. Page Definitions

### 4.1 About Page

**Purpose:** Static informational page.

**Content:**

| Section | Description |
|---------|-------------|
| Project description | LinBlock as a hosting and emulation technology |
| Feature list | Current capabilities |
| Upcoming changes | Planned features and roadmap highlights |
| Licensing | License type and terms |
| Supported Android versions | List of tested AOSP/GSI versions |
| Known limitations | Current constraints and workarounds |

**Widget:** `Gtk.ScrolledWindow` containing a vertical `Gtk.Box` with `Gtk.Label`
elements (markup enabled for rich text).

---

### 4.2 Load OS Page (OS Configuration Wizard)

**Purpose:** Create a new OS instance by configuring all emulation parameters.

**Layout:** Scrollable vertical form divided into collapsible sections.
Each section is a `Gtk.Expander` with a descriptive header.

#### Section Breakdown

| # | Section | Key Fields |
|---|---------|-----------|
| 1 | Graphics / Rendering | GPU mode (host / software / off), OpenGL / Vulkan toggle, renderer backend dropdown |
| 2 | ADB Configuration | ADB binary path, port number, auto-connect on boot toggle |
| 3 | Device Simulation Defaults | Screen size presets (phone 1080x1920, tablet 1600x2560, custom WxH), device profile dropdown, sensor enables (accelerometer, gyroscope, proximity, GPS) |
| 4 | Storage Paths | Shared folders path, screenshot directory, image cache directory |
| 5 | Network | Bridge mode toggle, proxy address + port, port forwarding rules list |
| 6 | Input Mapping | Keyboard-to-touch enable, gamepad support toggle, mouse mode (direct / relative) |
| 7 | Camera / Media | Webcam passthrough toggle, microphone source selector, audio output device |
| 8 | Performance | KVM / HAXM selector, RAM profile (1 GB / 2 GB / 4 GB / 8 GB / custom), CPU core count spinner |
| 9 | Google Services | Checklist of Google services, **all disabled by default**, each with a one-line description |

#### Google Services Checklist

Every item is a `Gtk.CheckButton`, unchecked by default. Each row shows:

```
[ ] Google Play Store       -- App marketplace
[ ] Google Play Services    -- Background service framework
[ ] Google Play Protect     -- Malware scanning
[ ] Google Location Service -- Fused location provider
[ ] Google Contacts Sync    -- Contact synchronization
[ ] Google Calendar Sync    -- Calendar synchronization
[ ] Google Drive            -- Cloud storage integration
[ ] Google Chrome           -- Default browser
[ ] Google Maps             -- Mapping and navigation
[ ] Google Assistant        -- Voice assistant
```

#### Save Action

At the bottom of the form:

1. `Gtk.Entry` -- "OS Name" (required, validated for uniqueness).
2. `Gtk.Button` -- "Save OS Build".
3. On save:
   - Serialize form state to the OS profile schema (see Section 6).
   - Write profile to the config directory.
   - Add a dynamic sidebar button for the new OS.
   - Switch the content area to the OS List page.

---

### 4.3 OS List Page

**Purpose:** View and manage all saved OS builds.

**Widget:** `Gtk.ListBox` (or `Gtk.TreeView` for sortable columns).

| Column | Description |
|--------|-------------|
| Name | OS profile name (editable inline) |
| Screen Size | Configured resolution |
| RAM | Allocated memory |
| GPU Mode | Host / Software / Off |
| Status | Stopped / Running |
| Actions | Rename, Delete, Duplicate, Edit Settings |

- **Rename** -- inline `Gtk.Entry` swap; updates sidebar button text.
- **Delete** -- confirmation dialog; removes profile file and sidebar button.
- **Duplicate** -- copies profile with " (copy)" suffix appended.
- **Edit Settings** -- navigates to Load OS page pre-filled with this profile's values.

---

### 4.4 Saved OS Pages (Dynamic, Per Instance)

Each saved OS instance gets its own page in the `Gtk.Stack`, keyed by profile
name. The page is created when the profile is saved and destroyed when deleted.

#### Layout

```
+--------------------------------------------------+
|  Sidebar  |  Device Controls  |  Emulated Phone  |
|           |                   |                   |
|  About    |  On/Off toggle    | +-------------+  |
|  Load OS  |  Save State       | |             |  |
|  OS List  |  Reset            | |   Android   |  |
|  -------- |  Screenshot       | |   Display   |  |
|  MyOS 1   |  Record Video     | |             |  |
|  MyOS 2   |  ----------       | |             |  |
|           |  Settings  *      | +-------------+  |
|           |  WiFi  *          |                   |
|           |  Bluetooth  *     |                   |
|           |  Airplane Mode  * |                   |
|           |  Auto-Rotate  *   |                   |
|           |  Brightness  *    |                   |
|           |  Volume  *        |                   |
|           |  Do Not Disturb * |                   |
|           |  Location  *      |                   |
|           |  Battery  *       |                   |
+--------------------------------------------------+

*  = conditional controls (grayed out if not enabled during OS creation)
```

#### Control Categories

**Always-present controls** (functional regardless of OS config):

| Control | Widget | Behavior |
|---------|--------|----------|
| On / Off toggle | `Gtk.Switch` | Start or stop the emulator instance |
| Save State | `Gtk.Button` | Snapshot current VM state to disk |
| Reset | `Gtk.Button` | Hard-reset the running instance |
| Screenshot | `Gtk.Button` | Capture current display to screenshot directory |
| Record Video | `Gtk.ToggleButton` | Start / stop screen recording |

**Conditional controls** (visible but grayed/disabled when the corresponding
feature was not enabled during OS creation):

| Control | Widget | Enabled When |
|---------|--------|-------------|
| Settings | `Gtk.Button` | Always enabled (opens Android settings via ADB intent) |
| WiFi | `Gtk.Switch` | Network bridge mode enabled |
| Bluetooth | `Gtk.Switch` | Bluetooth passthrough enabled |
| Airplane Mode | `Gtk.Switch` | Any radio interface enabled |
| Auto-Rotate | `Gtk.Switch` | Accelerometer sensor enabled |
| Brightness | `Gtk.Scale` | Display brightness control enabled |
| Volume | `Gtk.Scale` | Audio output device configured |
| Do Not Disturb | `Gtk.Switch` | Notification system present |
| Location | `Gtk.Switch` | GPS sensor or Google Location enabled |
| Battery | `Gtk.LevelBar` | Battery simulation enabled |

The `sensitive` property on each widget is set to `False` when the control's
prerequisite is not met, rendering it grayed out but still visible.

#### Emulated Device Display

- Widget: `Gtk.DrawingArea` subclass (`EmulatorDisplay`).
- Receives framebuffer data from the emulator controller.
- Translates mouse events to Android touch events.
- Translates keyboard events to Android key events.
- Target: 30 fps rendering at native device resolution scaled to fit.

Reference mockup: `resources/images/screen_options.png`

---

## 5. Content Area Layout Details

### 5.1 Page Switching

```python
# Sidebar button click handler
def on_sidebar_button_clicked(self, button, page_name):
    self.content_stack.set_visible_child_name(page_name)
```

Pages are registered in the `Gtk.Stack` with string names:

| Page Name | Stack Child Name |
|-----------|-----------------|
| About | `"about"` |
| Load OS | `"load_os"` |
| OS List | `"os_list"` |
| Saved OS (dynamic) | `"os_{profile_name}"` |

### 5.2 Responsive Behavior

- Sidebar width is fixed at 150 px.
- Content area fills remaining horizontal space.
- Device controls column: 180 px fixed width.
- Emulated phone display: fills remaining space, maintains aspect ratio.
- Minimum window size: 1024 x 768.

---

## 6. Data Model

### 6.1 OS Profile Schema

```yaml
# ~/.config/linblock/profiles/{profile_name}.yaml
name: "MyAndroid14"
created: "2026-01-27T10:00:00Z"
modified: "2026-01-27T10:00:00Z"

graphics:
  gpu_mode: "host"          # host | software | off
  api: "opengl"             # opengl | vulkan
  renderer: "auto"          # auto | swiftshader | angle

adb:
  path: "/usr/bin/adb"
  port: 5555
  auto_connect: true

device:
  screen_preset: "phone"    # phone | tablet | custom
  screen_width: 1080
  screen_height: 1920
  device_profile: "generic_phone"
  sensors:
    accelerometer: true
    gyroscope: true
    proximity: true
    gps: true

storage:
  shared_folder: "~/LinBlock/shared"
  screenshot_dir: "~/LinBlock/screenshots"
  image_cache: "~/LinBlock/cache"

network:
  bridge_mode: false
  proxy_address: ""
  proxy_port: 0
  port_forwarding: []

input:
  keyboard_to_touch: true
  gamepad: false
  mouse_mode: "direct"      # direct | relative

camera_media:
  webcam_passthrough: false
  mic_source: "default"
  audio_output: "default"

performance:
  hypervisor: "kvm"         # kvm | haxm | software
  ram_mb: 4096
  cpu_cores: 4

google_services:
  play_store: false
  play_services: false
  play_protect: false
  location_service: false
  contacts_sync: false
  calendar_sync: false
  drive: false
  chrome: false
  maps: false
  assistant: false
```

### 6.2 Persistence

- Config directory: `~/.config/linblock/profiles/`
- Format: YAML (human-readable, easy to hand-edit).
- One file per OS profile, named `{profile_name}.yaml`.
- Profile list is derived by scanning the directory at startup.
- Changes are written immediately on save; no in-memory-only state.

### 6.3 Dynamic Sidebar Generation

On application startup and after any profile create/rename/delete:

```python
def rebuild_sidebar_dynamic_buttons(self):
    # Remove existing dynamic buttons
    for btn in self.dynamic_buttons:
        self.sidebar.remove(btn)
    self.dynamic_buttons.clear()

    # Scan profiles directory
    profiles = load_all_profiles()

    # Create a button for each profile
    for profile in sorted(profiles, key=lambda p: p.name):
        btn = Gtk.Button(label=profile.name)
        btn.connect("clicked", self.on_sidebar_button_clicked,
                     f"os_{profile.name}")
        self.sidebar.pack_start(btn, False, False, 0)
        self.dynamic_buttons.append(btn)

    self.sidebar.show_all()
```

---

## 7. GTK Implementation Notes

### 7.1 Widget Hierarchy

```
Gtk.ApplicationWindow
 +-- Gtk.Box (horizontal)
      +-- Sidebar (Gtk.Box, vertical, 150 px)
      |    +-- Gtk.Image (logo)
      |    +-- Gtk.Button ("About")
      |    +-- Gtk.Button ("Load OS")
      |    +-- Gtk.Button ("OS List")
      |    +-- Gtk.Separator
      |    +-- Gtk.Button ("MyOS 1")     [dynamic]
      |    +-- Gtk.Button ("MyOS 2")     [dynamic]
      |    +-- Gtk.Box (spacer, expand)
      |
      +-- Gtk.Stack (content area)
           +-- AboutPage (Gtk.ScrolledWindow)
           +-- LoadOSPage (Gtk.ScrolledWindow)
           +-- OSListPage (Gtk.ScrolledWindow)
           +-- RunningOSPage (Gtk.Box)   [dynamic, per profile]
                +-- DeviceControlsPanel (Gtk.Box, vertical, 180 px)
                +-- EmulatorDisplay (Gtk.DrawingArea)
```

### 7.2 Key Classes

| Class | Parent | File | Role |
|-------|--------|------|------|
| `LinBlockApp` | `Gtk.Application` | `src/main.py` | Application entry point |
| `MainWindow` | `Gtk.ApplicationWindow` | `src/ui/dashboard_window.py` | Top-level window |
| `Sidebar` | `Gtk.Box` | `src/ui/sidebar.py` | Navigation with dynamic buttons |
| `AboutPage` | `Gtk.ScrolledWindow` | `src/pages/about_page.py` | Static info page |
| `LoadOSPage` | `Gtk.ScrolledWindow` | `src/pages/load_os_page.py` | OS configuration wizard |
| `OSListPage` | `Gtk.ScrolledWindow` | `src/pages/os_list_page.py` | Saved OS management |
| `RunningOSPage` | `Gtk.Box` | `src/pages/running_os_page.py` | Emulator display + controls |
| `DeviceControlsPanel` | `Gtk.Box` | `src/ui/components/device_controls.py` | Control buttons/toggles |
| `EmulatorDisplay` | `Gtk.DrawingArea` | `src/ui/components/emulator_display.py` | Framebuffer renderer |
| `OSProfile` | `object` | `src/config/os_profile.py` | Profile data model + YAML I/O |

### 7.3 CSS Theming

Stylesheet loaded from `resources/css/linblock.css`:

```css
.sidebar {
    background-color: #2d2d2d;
    min-width: 150px;
    max-width: 150px;
}

.sidebar-button {
    border-radius: 0;
    padding: 12px 16px;
    background: transparent;
    color: #cccccc;
    border: none;
    text-align: left;
}

.sidebar-button-active {
    background-color: #3d3d3d;
    color: #ffffff;
    border-left: 3px solid #4a90d9;
}

.sidebar-button:hover {
    background-color: #353535;
}

.device-control-panel {
    min-width: 180px;
    max-width: 180px;
    padding: 8px;
    background-color: #1e1e1e;
}

.control-disabled {
    opacity: 0.4;
}
```

### 7.4 Load OS Form Sections

Each section is implemented as a `Gtk.Expander`:

```python
class LoadOSPage(Gtk.ScrolledWindow):
    def __init__(self):
        super().__init__()
        form = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)

        # Section 1: Graphics / Rendering
        graphics = Gtk.Expander(label="Graphics / Rendering", expanded=True)
        graphics_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        # ... GPU mode combo, API toggle, renderer dropdown
        graphics.add(graphics_box)
        form.pack_start(graphics, False, False, 0)

        # Section 2-8: similar pattern ...

        # Section 9: Google Services
        google = Gtk.Expander(label="Google Services")
        google_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        for service, desc in GOOGLE_SERVICES:
            row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
            check = Gtk.CheckButton(label=service)
            check.set_active(False)  # all disabled by default
            label = Gtk.Label(label=f"  -- {desc}")
            row.pack_start(check, False, False, 0)
            row.pack_start(label, False, False, 4)
            google_box.pack_start(row, False, False, 2)
        google.add(google_box)
        form.pack_start(google, False, False, 0)

        # Save action
        save_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self.name_entry = Gtk.Entry(placeholder_text="OS Name")
        save_btn = Gtk.Button(label="Save OS Build")
        save_btn.connect("clicked", self.on_save_clicked)
        save_box.pack_start(self.name_entry, True, True, 0)
        save_box.pack_start(save_btn, False, False, 0)
        form.pack_start(save_box, False, False, 12)

        self.add(form)
```

### 7.5 Conditional Controls Logic

```python
class DeviceControlsPanel(Gtk.Box):
    def configure_for_profile(self, profile: OSProfile):
        """Enable/disable controls based on profile settings."""
        self.wifi_switch.set_sensitive(profile.network.bridge_mode)
        self.bluetooth_switch.set_sensitive(
            getattr(profile, 'bluetooth_enabled', False))
        self.airplane_switch.set_sensitive(
            profile.network.bridge_mode or
            getattr(profile, 'bluetooth_enabled', False))
        self.auto_rotate_switch.set_sensitive(
            profile.device.sensors.accelerometer)
        self.brightness_scale.set_sensitive(True)  # always available
        self.volume_scale.set_sensitive(
            profile.camera_media.audio_output != "none")
        self.dnd_switch.set_sensitive(True)  # always available
        self.location_switch.set_sensitive(
            profile.device.sensors.gps or
            profile.google_services.location_service)
        self.battery_bar.set_sensitive(
            getattr(profile, 'battery_simulation', False))
```

---

## 8. Navigation Flow

```
Application Start
       |
       v
  About Page (default landing)
       |
       +-- User clicks "Load OS" ---------> Load OS Page
       |                                        |
       |                            User fills form, clicks Save
       |                                        |
       |                                        v
       |                              Profile written to disk
       |                              Sidebar button added
       |                                        |
       +-- User clicks "OS List" ---------> OS List Page
       |                                        |
       |                            User clicks a profile row
       |                                        |
       +-- User clicks sidebar OS btn --> Running OS Page
                                               |
                                    Emulator starts (On/Off)
                                    Display renders framebuffer
                                    Controls interact via ADB
```

---

## 9. File Manifest

Files to be created during GTK implementation:

```
src/
  main.py
  config/
    os_profile.py
  ui/
    dashboard_window.py
    sidebar.py
    content_area.py
    components/
      device_controls.py
      emulator_display.py
  pages/
    page_base.py
    about_page.py
    load_os_page.py
    os_list_page.py
    running_os_page.py
  utils/
    profile_manager.py

resources/
  css/
    linblock.css
  images/
    linblock_logo.png
    screen_options.png   (existing)
```

---

## 10. References

- GTK3 Python Reference: https://lazka.github.io/pgi-docs/Gtk-3.0/
- Dashboard Starter Template: https://github.com/mikesdatawork/gtk-python-dashboard-starter
- Device Controls Mockup: `resources/images/screen_options.png`
- Modular Architecture: `docs/design/modular_architecture.md`
- Phase 1 Plan: `docs/design/phase1_emulator_development.md`
