"""
QEMU process management for Android emulation.

Handles launching, monitoring, and stopping QEMU instances
with appropriate flags for Android system images.
"""

import os
import subprocess
import signal
import threading
import time
from typing import Optional, Dict, Any, Callable, List
from dataclasses import dataclass, field
from enum import Enum


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

    # Additional disk images
    userdata_image: Optional[str] = None
    cache_image: Optional[str] = None

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

        # Machine type
        cmd.extend(["-machine", "q35"])

        # CPU configuration
        if self._config.use_kvm and self._check_kvm_available():
            cmd.extend(["-enable-kvm"])
            cmd.extend(["-cpu", "host"])
        else:
            cmd.extend(["-cpu", "qemu64"])

        cmd.extend(["-smp", str(self._config.cpu_cores)])

        # Memory
        cmd.extend(["-m", f"{self._config.memory_mb}M"])

        # System image (main drive)
        if self._config.system_image:
            cmd.extend([
                "-drive",
                f"file={self._config.system_image},format=raw,if=virtio,readonly=on"
            ])

        # Userdata image (persistent storage)
        if self._config.userdata_image:
            cmd.extend([
                "-drive",
                f"file={self._config.userdata_image},format=qcow2,if=virtio"
            ])

        # Display via VNC
        vnc_display = self._config.vnc_port - 5900
        cmd.extend(["-vnc", f":{vnc_display}"])

        # No graphical output (we use VNC)
        cmd.extend(["-nographic"])

        # GPU/Graphics
        if self._config.gpu_mode == "host":
            cmd.extend(["-device", "virtio-gpu-pci"])
        else:
            cmd.extend(["-device", "VGA"])

        # Network with ADB port forwarding
        cmd.extend([
            "-netdev", f"user,id=net0,hostfwd=tcp::{self._config.adb_port}-:5555",
            "-device", "virtio-net-pci,netdev=net0"
        ])

        # Audio (disabled for now)
        cmd.extend(["-audiodev", "none,id=audio0"])

        # Random number generator
        cmd.extend(["-device", "virtio-rng-pci"])

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

    def cleanup(self) -> None:
        """Clean up all resources."""
        self.force_stop()
        self._state_callbacks.clear()
