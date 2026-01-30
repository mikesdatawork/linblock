"""
QEMU process management for Android emulation.

Handles launching, monitoring, and stopping QEMU instances
with appropriate flags for Android system images.
"""

import os
import socket
import subprocess
import signal
import threading
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum


def _is_port_available(port: int) -> bool:
    """Check if a TCP port is available."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('127.0.0.1', port))
            return True
    except OSError:
        return False


def _find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """Find an available port starting from start_port."""
    for offset in range(max_attempts):
        port = start_port + offset
        if _is_port_available(port):
            return port
    raise RuntimeError(f"Could not find available port starting from {start_port}")


class QEMUState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class QEMUConfig:
    """Configuration for QEMU instance."""
    system_image: str = ""
    memory_mb: int = 4096
    cpu_cores: int = 4
    use_kvm: bool = True
    screen_width: int = 1080
    screen_height: int = 1920
    vnc_port: int = 5900
    adb_port: int = 5555
    gpu_mode: str = "host"  # host, software, auto

    # Boot configuration
    kernel: Optional[str] = None  # Path to kernel image
    initrd: Optional[str] = None  # Path to ramdisk/initrd
    boot_image: Optional[str] = None  # Path to boot.img
    kernel_cmdline: str = ""  # Additional kernel parameters
    cdrom_image: Optional[str] = None  # Path to ISO for CD-ROM boot

    # Additional disk images
    userdata_image: Optional[str] = None
    cache_image: Optional[str] = None
    data_image: Optional[str] = None  # For /data partition

    # GPU command pipe (for hardware-accelerated rendering)
    gpu_pipe_socket: Optional[str] = None  # Path to GPU pipe socket

    # Logging
    log_dir: Optional[str] = None  # Directory for QEMU logs
    serial_log: Optional[str] = None  # Path for serial console log

    # Advanced options
    extra_args: List[str] = field(default_factory=list)


class QEMUProcessError(Exception):
    """Raised when QEMU process operation fails."""
    pass


class QEMUProcess:
    """
    Manages a QEMU process for Android emulation.

    Provides methods to start, stop, and monitor QEMU instances.
    Supports VNC display output and ADB port forwarding.
    """

    QEMU_BINARY = "qemu-system-x86_64"

    def __init__(self, config: QEMUConfig):
        self._config = config
        self._process: Optional[subprocess.Popen] = None
        self._state = QEMUState.STOPPED
        self._pid: Optional[int] = None
        self._monitor_thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._state_callbacks: List[Callable[[QEMUState], None]] = []
        self._error_message: str = ""

    @property
    def state(self) -> QEMUState:
        return self._state

    @property
    def pid(self) -> Optional[int]:
        return self._pid

    @property
    def error_message(self) -> str:
        return self._error_message

    def add_state_callback(self, callback: Callable[[QEMUState], None]) -> None:
        """Register a callback for state changes."""
        self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable[[QEMUState], None]) -> None:
        """Unregister a state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def _set_state(self, state: QEMUState) -> None:
        """Update state and notify callbacks."""
        old_state = self._state
        self._state = state
        if old_state != state:
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception:
                    pass

    def _check_qemu_available(self) -> bool:
        """Check if QEMU binary is available."""
        try:
            result = subprocess.run(
                [self.QEMU_BINARY, "--version"],
                capture_output=True,
                timeout=5
            )
            return result.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def _check_kvm_available(self) -> bool:
        """Check if KVM is available."""
        return os.path.exists("/dev/kvm") and os.access("/dev/kvm", os.R_OK | os.W_OK)

    def _build_command(self) -> List[str]:
        """Build QEMU command line arguments."""
        cmd = [self.QEMU_BINARY]

        # Machine type - use pc for better Android compatibility
        cmd.extend(["-machine", "pc,accel=kvm" if self._check_kvm_available() else "pc"])

        # CPU configuration
        if self._config.use_kvm and self._check_kvm_available():
            cmd.extend(["-enable-kvm"])
            cmd.extend(["-cpu", "host"])
        else:
            cmd.extend(["-cpu", "qemu64"])

        cmd.extend(["-smp", str(self._config.cpu_cores)])

        # Memory
        cmd.extend(["-m", f"{self._config.memory_mb}M"])

        # Boot configuration (kernel, initrd, cmdline)
        if self._config.kernel:
            cmd.extend(["-kernel", self._config.kernel])

            if self._config.initrd:
                cmd.extend(["-initrd", self._config.initrd])

            # Kernel command line for Android (only valid with -kernel)
            kernel_cmdline = self._config.kernel_cmdline or ""
            if not kernel_cmdline:
                # Default Android kernel parameters with video mode
                width = self._config.screen_width
                height = self._config.screen_height
                kernel_cmdline = (
                    "root=/dev/ram0 "
                    "console=ttyS0 "
                    "androidboot.hardware=ranchu "
                    "androidboot.serialno=EMULATOR "
                    "androidboot.console=ttyS0 "
                    "androidboot.selinux=permissive "
                    f"video={width}x{height} "
                )
            else:
                # Ensure console=ttyS0 is included for serial logging
                if "console=" not in kernel_cmdline:
                    kernel_cmdline = f"console=ttyS0 {kernel_cmdline}"
            if kernel_cmdline:
                cmd.extend(["-append", kernel_cmdline])

        # System image (main drive) - use IDE for better boot compatibility
        if self._config.system_image:
            cmd.extend([
                "-drive",
                f"file={self._config.system_image},format=raw,if=ide,index=0"
            ])

        # Userdata image (persistent storage)
        if self._config.userdata_image:
            cmd.extend([
                "-drive",
                f"file={self._config.userdata_image},format=qcow2,if=ide,index=1"
            ])

        # Data image
        if self._config.data_image:
            cmd.extend([
                "-drive",
                f"file={self._config.data_image},format=qcow2,if=ide,index=2"
            ])

        # Display via VNC with specific resolution
        vnc_display = self._config.vnc_port - 5900
        cmd.extend(["-vnc", f":{vnc_display}"])

        # Serial console for logging
        if self._config.serial_log:
            cmd.extend(["-serial", f"file:{self._config.serial_log}"])
        else:
            cmd.extend(["-serial", "stdio"])

        # GPU/Graphics configuration
        # Android-x86 works best with standard VGA for software rendering
        # virtio-gpu and QXL have compatibility issues with Android's SurfaceFlinger
        width = self._config.screen_width
        height = self._config.screen_height

        if self._config.gpu_mode == "host":
            # Try virtio-gpu-pci for better performance (requires guest driver support)
            cmd.extend(["-device", "virtio-gpu-pci"])
        elif self._config.gpu_mode == "virgl":
            # Virgil3D for OpenGL passthrough (experimental)
            cmd.extend(["-device", "virtio-gpu-pci,virgl=on"])
        else:
            # Software mode: use standard VGA - most compatible with Android-x86
            # This uses Android's built-in software renderer (swrast/llvmpipe)
            cmd.extend(["-vga", "std"])

        # Set VGA memory for higher resolutions
        cmd.extend(["-global", "VGA.vgamem_mb=64"])

        # GPU command pipe (virtio-serial for GPU command transport)
        if self._config.gpu_pipe_socket:
            cmd.extend([
                "-device", "virtio-serial",
                "-chardev", f"socket,path={self._config.gpu_pipe_socket},server=on,wait=off,id=gpu_chardev",
                "-device", "virtserialport,chardev=gpu_chardev,name=gpu_pipe",
            ])

        # Network with ADB port forwarding (disable PXE boot ROM)
        cmd.extend([
            "-netdev", f"user,id=net0,hostfwd=tcp::{self._config.adb_port}-:5555",
            "-device", "e1000,netdev=net0,romfile="  # Disable PXE ROM
        ])

        # USB support for ADB
        cmd.extend(["-usb", "-device", "usb-tablet"])

        # Random number generator
        cmd.extend(["-device", "virtio-rng-pci"])

        # CD-ROM for ISO boot (Android-x86)
        if self._config.cdrom_image:
            cmd.extend(["-cdrom", self._config.cdrom_image])

        # Boot order
        if self._config.kernel:
            # Direct kernel boot - no menu needed
            cmd.extend(["-boot", "order=c,strict=on"])
        elif self._config.cdrom_image:
            # Boot from CD-ROM first (for ISO boot)
            cmd.extend(["-boot", "order=d,menu=on"])
        else:
            # Disk boot with menu for debugging
            cmd.extend(["-boot", "order=cd,menu=on"])

        # Extra arguments
        cmd.extend(self._config.extra_args)

        return cmd

    def _monitor_process(self) -> None:
        """Monitor the QEMU process in a background thread."""
        while not self._stop_event.is_set():
            if self._process is None:
                break

            # Check if process is still running
            retcode = self._process.poll()
            if retcode is not None:
                # Process has exited
                if retcode == 0:
                    self._set_state(QEMUState.STOPPED)
                else:
                    self._error_message = f"QEMU exited with code {retcode}"
                    self._set_state(QEMUState.ERROR)
                self._pid = None
                break

            time.sleep(0.5)

    def start(self) -> None:
        """Start the QEMU process."""
        if self._state in (QEMUState.RUNNING, QEMUState.STARTING):
            raise QEMUProcessError("QEMU is already running")

        if not self._check_qemu_available():
            self._error_message = f"QEMU binary '{self.QEMU_BINARY}' not found"
            self._set_state(QEMUState.ERROR)
            raise QEMUProcessError(self._error_message)

        if not self._config.system_image:
            self._error_message = "No system image specified"
            self._set_state(QEMUState.ERROR)
            raise QEMUProcessError(self._error_message)

        if not os.path.exists(self._config.system_image):
            self._error_message = f"System image not found: {self._config.system_image}"
            self._set_state(QEMUState.ERROR)
            raise QEMUProcessError(self._error_message)

        # Find available ports if configured ones are in use
        if not _is_port_available(self._config.adb_port):
            self._config.adb_port = _find_available_port(self._config.adb_port)
        if not _is_port_available(self._config.vnc_port):
            self._config.vnc_port = _find_available_port(self._config.vnc_port)

        self._set_state(QEMUState.STARTING)
        self._stop_event.clear()

        try:
            cmd = self._build_command()
            self._process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                stdin=subprocess.PIPE,
            )
            self._pid = self._process.pid

            # Start monitoring thread
            self._monitor_thread = threading.Thread(
                target=self._monitor_process,
                daemon=True
            )
            self._monitor_thread.start()

            # Give QEMU a moment to start
            time.sleep(1)

            # Check if it's still running
            if self._process.poll() is None:
                self._set_state(QEMUState.RUNNING)
            else:
                stderr = self._process.stderr.read().decode() if self._process.stderr else ""
                self._error_message = f"QEMU failed to start: {stderr}"
                self._set_state(QEMUState.ERROR)
                raise QEMUProcessError(self._error_message)

        except FileNotFoundError:
            self._error_message = f"QEMU binary '{self.QEMU_BINARY}' not found"
            self._set_state(QEMUState.ERROR)
            raise QEMUProcessError(self._error_message)
        except Exception as e:
            self._error_message = str(e)
            self._set_state(QEMUState.ERROR)
            raise QEMUProcessError(self._error_message)

    def stop(self, timeout: float = 10.0) -> None:
        """Stop the QEMU process gracefully."""
        if self._state not in (QEMUState.RUNNING, QEMUState.STARTING):
            return

        self._set_state(QEMUState.STOPPING)
        self._stop_event.set()

        if self._process is not None:
            try:
                # Try graceful shutdown first
                self._process.terminate()
                try:
                    self._process.wait(timeout=timeout)
                except subprocess.TimeoutExpired:
                    # Force kill if timeout
                    self._process.kill()
                    self._process.wait(timeout=5)
            except Exception:
                pass
            finally:
                self._process = None
                self._pid = None

        if self._monitor_thread is not None:
            self._monitor_thread.join(timeout=2)
            self._monitor_thread = None

        self._set_state(QEMUState.STOPPED)

    def force_stop(self) -> None:
        """Forcefully kill the QEMU process."""
        if self._process is not None:
            try:
                self._process.kill()
            except Exception:
                pass
        self._stop_event.set()
        self._process = None
        self._pid = None
        self._set_state(QEMUState.STOPPED)

    def send_key(self, key: str) -> None:
        """Send a key event to the VM (requires QEMU monitor)."""
        # This would require QEMU monitor connection
        pass

    def get_vnc_address(self) -> str:
        """Get the VNC server address for this instance."""
        return f"localhost:{self._config.vnc_port}"

    def get_gpu_pipe_socket(self) -> Optional[str]:
        """Get the GPU command pipe socket path."""
        return self._config.gpu_pipe_socket

    def cleanup(self) -> None:
        """Clean up all resources."""
        self.force_stop()
        self._state_callbacks.clear()

        # Clean up GPU pipe socket if we created it
        if self._config.gpu_pipe_socket and os.path.exists(self._config.gpu_pipe_socket):
            try:
                os.unlink(self._config.gpu_pipe_socket)
            except Exception:
                pass
