"""
Tests for QEMUProcess module.

Tests the QEMU process management functionality.
"""

import pytest
from ..internal.qemu_process import (
    QEMUProcess,
    QEMUConfig,
    QEMUState,
    QEMUProcessError,
)


class TestQEMUConfig:
    """Test suite for QEMUConfig."""

    def test_default_config(self):
        """Config has sensible defaults."""
        config = QEMUConfig()
        assert config.memory_mb == 4096
        assert config.cpu_cores == 4
        assert config.use_kvm is True
        assert config.vnc_port == 5900
        assert config.adb_port == 5555

    def test_custom_config(self):
        """Config accepts custom values."""
        config = QEMUConfig(
            system_image="/path/to/image.img",
            memory_mb=8192,
            cpu_cores=8,
            use_kvm=False,
            vnc_port=5901,
        )
        assert config.system_image == "/path/to/image.img"
        assert config.memory_mb == 8192
        assert config.cpu_cores == 8
        assert config.use_kvm is False
        assert config.vnc_port == 5901


class TestQEMUProcess:
    """Test suite for QEMUProcess."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return QEMUConfig(
            system_image="/tmp/nonexistent.img",
            memory_mb=2048,
            cpu_cores=2,
            use_kvm=False,
        )

    @pytest.fixture
    def process(self, config):
        """Create QEMUProcess instance for testing."""
        return QEMUProcess(config)

    def test_initial_state_stopped(self, process):
        """Newly created process is in STOPPED state."""
        assert process.state == QEMUState.STOPPED

    def test_initial_pid_none(self, process):
        """Newly created process has no PID."""
        assert process.pid is None

    def test_state_callback_registration(self, process):
        """State callbacks can be registered and unregistered."""
        states_seen = []

        def callback(state):
            states_seen.append(state)

        process.add_state_callback(callback)
        # Manually trigger state change
        process._set_state(QEMUState.STARTING)
        assert QEMUState.STARTING in states_seen

        process.remove_state_callback(callback)
        process._set_state(QEMUState.RUNNING)
        assert QEMUState.RUNNING not in states_seen

    def test_vnc_address(self, config, process):
        """VNC address is formatted correctly."""
        addr = process.get_vnc_address()
        assert addr == f"localhost:{config.vnc_port}"

    def test_start_without_qemu_raises(self, process):
        """Start fails gracefully when QEMU is not available."""
        # On systems without QEMU, this should raise
        with pytest.raises(QEMUProcessError):
            process.start()

    def test_start_with_missing_image_raises(self, process):
        """Start fails when system image doesn't exist."""
        with pytest.raises(QEMUProcessError) as exc:
            process.start()
        # Error should mention either QEMU or image
        assert "not found" in str(exc.value).lower()

    def test_cleanup_resets_state(self, process):
        """Cleanup returns process to stopped state."""
        process._state = QEMUState.RUNNING
        process.cleanup()
        assert process.state == QEMUState.STOPPED

    def test_force_stop_clears_pid(self, process):
        """Force stop clears PID and resets state."""
        process._pid = 12345
        process._state = QEMUState.RUNNING
        process.force_stop()
        assert process.pid is None
        assert process.state == QEMUState.STOPPED


class TestQEMUProcessCommandBuild:
    """Test QEMU command building."""

    def test_build_command_includes_memory(self):
        """Built command includes memory configuration."""
        config = QEMUConfig(
            system_image="/tmp/test.img",
            memory_mb=2048,
        )
        process = QEMUProcess(config)
        cmd = process._build_command()
        assert "-m" in cmd
        idx = cmd.index("-m")
        assert cmd[idx + 1] == "2048M"

    def test_build_command_includes_cpu_cores(self):
        """Built command includes SMP configuration."""
        config = QEMUConfig(
            system_image="/tmp/test.img",
            cpu_cores=8,
        )
        process = QEMUProcess(config)
        cmd = process._build_command()
        assert "-smp" in cmd
        idx = cmd.index("-smp")
        assert cmd[idx + 1] == "8"

    def test_build_command_includes_vnc(self):
        """Built command includes VNC display."""
        config = QEMUConfig(
            system_image="/tmp/test.img",
            vnc_port=5902,
        )
        process = QEMUProcess(config)
        cmd = process._build_command()
        assert "-vnc" in cmd
        idx = cmd.index("-vnc")
        assert cmd[idx + 1] == ":2"  # 5902 - 5900 = 2

    def test_build_command_includes_drive(self):
        """Built command includes system drive."""
        config = QEMUConfig(
            system_image="/tmp/test.img",
        )
        process = QEMUProcess(config)
        cmd = process._build_command()
        assert "-drive" in cmd
        # Find the drive argument
        drive_found = False
        for i, arg in enumerate(cmd):
            if arg == "-drive" and "/tmp/test.img" in cmd[i + 1]:
                drive_found = True
                break
        assert drive_found
