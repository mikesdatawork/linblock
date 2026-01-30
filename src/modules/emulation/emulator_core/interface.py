"""
Module: emulator_core
Layer: emulation

CPU virtualization and VM lifecycle management.
"""
from typing import Dict, Any, Optional, Callable, List
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
from enum import Enum


# -----------------------------------------------------------------------------
# Exceptions
# -----------------------------------------------------------------------------

class EmulatorCoreError(Exception):
    """Base exception for emulator_core module."""
    pass


class VMStartError(EmulatorCoreError):
    """Raised when VM cannot be started."""
    pass


class VMNotRunningError(EmulatorCoreError):
    """Raised when operation requires a running VM but VM is not running."""
    pass


# -----------------------------------------------------------------------------
# Data types
# -----------------------------------------------------------------------------

class VMState(Enum):
    STOPPED = "stopped"
    STARTING = "starting"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    ERROR = "error"


@dataclass
class VMConfig:
    memory_mb: int = 4096
    cpu_cores: int = 4
    use_kvm: bool = True
    kernel_path: Optional[str] = None
    initrd_path: Optional[str] = None
    kernel_cmdline: str = ""
    system_image: Optional[str] = None
    cdrom_image: Optional[str] = None  # ISO for CD-ROM boot
    screen_width: int = 1080
    screen_height: int = 1920
    vnc_port: int = 5900
    adb_port: int = 5555
    gpu_mode: str = "host"


@dataclass
class VMInfo:
    state: VMState = VMState.STOPPED
    pid: Optional[int] = None
    memory_used_mb: int = 0
    cpu_usage_percent: float = 0.0
    uptime_seconds: float = 0.0
    vnc_address: str = ""
    error_message: str = ""


@dataclass
class FrameBuffer:
    """Container for display framebuffer data."""
    width: int = 0
    height: int = 0
    data: bytes = b""
    format: str = "bgra"


# -----------------------------------------------------------------------------
# Interface
# -----------------------------------------------------------------------------

class EmulatorCoreInterface(ABC):
    """
    Abstract interface for CPU virtualization and VM lifecycle management.

    All implementations must inherit from this class.
    """

    @abstractmethod
    def __init__(self, config: Dict[str, Any]) -> None:
        """Initialize module with configuration."""
        pass

    @abstractmethod
    def initialize(self) -> None:
        """Prepare the emulator runtime (allocate resources, verify KVM, etc.)."""
        pass

    @abstractmethod
    def start(self) -> None:
        """Start the virtual machine."""
        pass

    @abstractmethod
    def stop(self) -> None:
        """Stop the virtual machine."""
        pass

    @abstractmethod
    def pause(self) -> None:
        """Pause the running virtual machine."""
        pass

    @abstractmethod
    def resume(self) -> None:
        """Resume a paused virtual machine."""
        pass

    @abstractmethod
    def reset(self) -> None:
        """Hard-reset the virtual machine."""
        pass

    @abstractmethod
    def get_state(self) -> VMState:
        """Return the current VM state."""
        pass

    @abstractmethod
    def get_info(self) -> VMInfo:
        """Return detailed VM information."""
        pass

    @abstractmethod
    def save_snapshot(self, name: str) -> str:
        """Save a named snapshot, returning its path."""
        pass

    @abstractmethod
    def load_snapshot(self, name: str) -> None:
        """Restore from a named snapshot."""
        pass

    @abstractmethod
    def cleanup(self) -> None:
        """Release all resources held by the module."""
        pass


# -----------------------------------------------------------------------------
# Implementation
# -----------------------------------------------------------------------------

class DefaultEmulatorCore(EmulatorCoreInterface):
    """Default stub implementation of EmulatorCoreInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = VMConfig(
            memory_mb=config.get("memory_mb", 4096),
            cpu_cores=config.get("cpu_cores", 4),
            use_kvm=config.get("use_kvm", True),
            kernel_path=config.get("kernel_path"),
            initrd_path=config.get("initrd_path"),
        )
        self._state = VMState.STOPPED
        self._initialized = False

    def initialize(self) -> None:
        self._initialized = True

    def start(self) -> None:
        if not self._initialized:
            raise VMStartError("Must call initialize() first")
        if self._state == VMState.RUNNING:
            raise EmulatorCoreError("VM already running")
        self._state = VMState.RUNNING

    def stop(self) -> None:
        if self._state not in (VMState.RUNNING, VMState.PAUSED):
            raise VMNotRunningError("VM is not running")
        self._state = VMState.STOPPED

    def pause(self) -> None:
        if self._state != VMState.RUNNING:
            raise VMNotRunningError("VM is not running")
        self._state = VMState.PAUSED

    def resume(self) -> None:
        if self._state != VMState.PAUSED:
            raise EmulatorCoreError("VM is not paused")
        self._state = VMState.RUNNING

    def reset(self) -> None:
        was_running = self._state in (VMState.RUNNING, VMState.PAUSED)
        self._state = VMState.STOPPED
        if was_running:
            self._state = VMState.RUNNING

    def get_state(self) -> VMState:
        return self._state

    def get_info(self) -> VMInfo:
        return VMInfo(state=self._state)

    def save_snapshot(self, name: str) -> str:
        if self._state not in (VMState.RUNNING, VMState.PAUSED):
            raise VMNotRunningError("VM must be running or paused")
        return f"/snapshots/{name}"

    def load_snapshot(self, name: str) -> None:
        if not self._initialized:
            raise EmulatorCoreError("Must initialize first")

    def cleanup(self) -> None:
        if self._state in (VMState.RUNNING, VMState.PAUSED):
            self._state = VMState.STOPPED
        self._initialized = False


class QEMUEmulatorCore(EmulatorCoreInterface):
    """QEMU-based implementation of EmulatorCoreInterface."""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = VMConfig(
            memory_mb=config.get("memory_mb", 4096),
            cpu_cores=config.get("cpu_cores", 4),
            use_kvm=config.get("use_kvm", True),
            kernel_path=config.get("kernel_path"),
            initrd_path=config.get("initrd_path"),
            kernel_cmdline=config.get("kernel_cmdline", ""),
            system_image=config.get("system_image"),
            cdrom_image=config.get("cdrom_image"),
            screen_width=config.get("screen_width", 1080),
            screen_height=config.get("screen_height", 1920),
            vnc_port=config.get("vnc_port", 5900),
            adb_port=config.get("adb_port", 5555),
            gpu_mode=config.get("gpu_mode", "host"),
        )
        self._state = VMState.STOPPED
        self._initialized = False
        self._qemu_process = None
        self._vnc_client = None
        self._state_callbacks: List[Callable[[VMState], None]] = []
        self._frame_callbacks: List[Callable[[FrameBuffer], None]] = []
        self._error_message = ""
        self._start_time = 0.0
        self._serial_log_path: Optional[str] = None
        self._kernel_cmdline: str = config.get("kernel_cmdline", "")

    def add_state_callback(self, callback: Callable[[VMState], None]) -> None:
        """Register callback for VM state changes."""
        self._state_callbacks.append(callback)

    def remove_state_callback(self, callback: Callable[[VMState], None]) -> None:
        """Unregister state change callback."""
        if callback in self._state_callbacks:
            self._state_callbacks.remove(callback)

    def add_frame_callback(self, callback: Callable[[FrameBuffer], None]) -> None:
        """Register callback for framebuffer updates."""
        self._frame_callbacks.append(callback)

    def remove_frame_callback(self, callback: Callable[[FrameBuffer], None]) -> None:
        """Unregister framebuffer callback."""
        if callback in self._frame_callbacks:
            self._frame_callbacks.remove(callback)

    def _notify_state(self, state: VMState) -> None:
        """Notify all state callbacks."""
        old_state = self._state
        self._state = state
        if old_state != state:
            for callback in self._state_callbacks:
                try:
                    callback(state)
                except Exception:
                    pass

    def _notify_frame(self, frame_data) -> None:
        """Notify all frame callbacks."""
        frame = FrameBuffer(
            width=frame_data.width,
            height=frame_data.height,
            data=frame_data.data,
            format=frame_data.format
        )
        for callback in self._frame_callbacks:
            try:
                callback(frame)
            except Exception:
                pass

    def _on_qemu_state(self, qemu_state) -> None:
        """Handle QEMU state changes."""
        from .internal.qemu_process import QEMUState

        state_map = {
            QEMUState.STOPPED: VMState.STOPPED,
            QEMUState.STARTING: VMState.STARTING,
            QEMUState.RUNNING: VMState.RUNNING,
            QEMUState.STOPPING: VMState.STOPPING,
            QEMUState.ERROR: VMState.ERROR,
        }
        vm_state = state_map.get(qemu_state, VMState.ERROR)
        self._notify_state(vm_state)

    def set_serial_log(self, path: Optional[str]) -> None:
        """Set the serial console log file path.

        Can be called before start() to enable serial logging.

        Args:
            path: Path to log file, or None to disable serial logging.
        """
        self._serial_log_path = path
        # Update the QEMU process config if already initialized
        if self._qemu_process and hasattr(self._qemu_process, '_config'):
            self._qemu_process._config.serial_log = path

    def initialize(self) -> None:
        """Initialize QEMU process manager."""
        from .internal.qemu_process import QEMUProcess, QEMUConfig
        from .internal.vnc_client import VNCClient

        qemu_config = QEMUConfig(
            system_image=self._config.system_image or "",
            memory_mb=self._config.memory_mb,
            cpu_cores=self._config.cpu_cores,
            use_kvm=self._config.use_kvm,
            screen_width=self._config.screen_width,
            screen_height=self._config.screen_height,
            vnc_port=self._config.vnc_port,
            adb_port=self._config.adb_port,
            gpu_mode=self._config.gpu_mode,
            serial_log=self._serial_log_path,
            kernel=self._config.kernel_path,
            initrd=self._config.initrd_path,
            kernel_cmdline=self._kernel_cmdline or "",
            cdrom_image=self._config.cdrom_image,
        )

        self._qemu_process = QEMUProcess(qemu_config)
        self._qemu_process.add_state_callback(self._on_qemu_state)

        self._vnc_client = VNCClient(port=self._config.vnc_port)
        self._vnc_client.set_frame_callback(self._notify_frame)

        self._initialized = True

    def start(self) -> None:
        """Start the QEMU virtual machine."""
        import time

        if not self._initialized:
            raise VMStartError("Must call initialize() first")
        if self._state == VMState.RUNNING:
            raise EmulatorCoreError("VM already running")

        self._notify_state(VMState.STARTING)

        try:
            # Start QEMU process
            self._qemu_process.start()
            self._start_time = time.time()

            # Try to connect VNC (may take a moment for QEMU to be ready)
            max_retries = 30
            for i in range(max_retries):
                try:
                    time.sleep(0.5)
                    self._vnc_client.connect(timeout=5.0)
                    break
                except Exception:
                    if i == max_retries - 1:
                        # VNC connection failed but QEMU might still be running
                        pass

            self._notify_state(VMState.RUNNING)

        except Exception as e:
            self._error_message = str(e)
            self._notify_state(VMState.ERROR)
            raise VMStartError(str(e))

    def stop(self) -> None:
        """Stop the QEMU virtual machine."""
        if self._state not in (VMState.RUNNING, VMState.PAUSED, VMState.STARTING):
            raise VMNotRunningError("VM is not running")

        self._notify_state(VMState.STOPPING)

        # Disconnect VNC
        if self._vnc_client:
            self._vnc_client.disconnect()

        # Stop QEMU
        if self._qemu_process:
            self._qemu_process.stop()

        self._notify_state(VMState.STOPPED)

    def pause(self) -> None:
        """Pause the running VM (not fully supported by QEMU without monitor)."""
        if self._state != VMState.RUNNING:
            raise VMNotRunningError("VM is not running")
        # QEMU pause would require monitor connection
        self._notify_state(VMState.PAUSED)

    def resume(self) -> None:
        """Resume a paused VM."""
        if self._state != VMState.PAUSED:
            raise EmulatorCoreError("VM is not paused")
        self._notify_state(VMState.RUNNING)

    def reset(self) -> None:
        """Hard reset the VM."""
        if self._state in (VMState.RUNNING, VMState.PAUSED):
            self.stop()
        if self._initialized:
            self.start()

    def get_state(self) -> VMState:
        """Get current VM state."""
        return self._state

    def get_info(self) -> VMInfo:
        """Get detailed VM information."""
        import time

        uptime = 0.0
        if self._state == VMState.RUNNING and self._start_time > 0:
            uptime = time.time() - self._start_time

        return VMInfo(
            state=self._state,
            pid=self._qemu_process.pid if self._qemu_process else None,
            memory_used_mb=self._config.memory_mb if self._state == VMState.RUNNING else 0,
            cpu_usage_percent=0.0,
            uptime_seconds=uptime,
            vnc_address=f"localhost:{self._config.vnc_port}" if self._state == VMState.RUNNING else "",
            error_message=self._error_message,
        )

    def save_snapshot(self, name: str) -> str:
        """Save VM snapshot (requires QEMU monitor)."""
        if self._state not in (VMState.RUNNING, VMState.PAUSED):
            raise VMNotRunningError("VM must be running or paused")
        # Would require QEMU monitor command
        return f"/snapshots/{name}"

    def load_snapshot(self, name: str) -> None:
        """Load VM snapshot (requires QEMU monitor)."""
        if not self._initialized:
            raise EmulatorCoreError("Must initialize first")
        # Would require QEMU monitor command

    def send_key(self, keycode: int, down: bool) -> None:
        """Send key event to VM via VNC."""
        if self._vnc_client and self._vnc_client.connected:
            self._vnc_client.send_key(keycode, down)

    def send_pointer(self, x: int, y: int, buttons: int) -> None:
        """Send pointer event to VM via VNC."""
        if self._vnc_client and self._vnc_client.connected:
            self._vnc_client.send_pointer(x, y, buttons)

    def get_framebuffer(self) -> Optional[FrameBuffer]:
        """Get current framebuffer data."""
        if self._vnc_client:
            frame = self._vnc_client.get_framebuffer()
            if frame:
                return FrameBuffer(
                    width=frame.width,
                    height=frame.height,
                    data=frame.data,
                    format=frame.format
                )
        return None

    def cleanup(self) -> None:
        """Clean up all resources - ensures QEMU is always terminated."""
        # First try graceful stop if running
        if self._state in (VMState.RUNNING, VMState.PAUSED, VMState.STARTING):
            try:
                self.stop()
            except Exception:
                pass

        # Always force cleanup QEMU process to ensure no orphans
        if self._qemu_process:
            try:
                self._qemu_process.cleanup()  # This calls force_stop()
            except Exception:
                # Last resort: try to kill by PID
                if self._qemu_process.pid:
                    try:
                        import os
                        import signal
                        os.kill(self._qemu_process.pid, signal.SIGKILL)
                    except Exception:
                        pass
            self._qemu_process = None

        # Cleanup VNC client
        if self._vnc_client:
            try:
                self._vnc_client.cleanup()
            except Exception:
                pass
            self._vnc_client = None

        self._state_callbacks.clear()
        self._frame_callbacks.clear()
        self._initialized = False
        self._state = VMState.STOPPED


# -----------------------------------------------------------------------------
# Factory
# -----------------------------------------------------------------------------

def create_interface(config: Dict[str, Any] = None) -> EmulatorCoreInterface:
    """
    Factory function to create module interface.

    Args:
        config: Module configuration (optional)
            - backend: "qemu" or "stub" (default: "qemu")
            - system_image: Path to Android system image
            - memory_mb, cpu_cores, etc.

    Returns:
        Configured EmulatorCoreInterface implementation
    """
    config = config or {}
    backend = config.get("backend", "qemu")

    if backend == "stub":
        return DefaultEmulatorCore(config)
    else:
        return QEMUEmulatorCore(config)
