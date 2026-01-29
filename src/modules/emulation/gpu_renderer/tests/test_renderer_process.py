"""
Tests for renderer process management.

Tests the sandboxed GPU renderer process and IPC communication.
"""

import pytest
import os
import time
import struct
import tempfile
from ..internal.renderer_process import (
    RendererProcess,
    RendererProcessConfig,
    RendererProcessError,
    ProcessState,
)
from ..internal.shm_display import SharedMemoryDisplay


class TestRendererProcessConfig:
    """Test renderer process configuration."""

    def test_default_config(self):
        """Config has sensible defaults."""
        config = RendererProcessConfig()
        assert config.width == 1080
        assert config.height == 1920
        assert config.use_sandbox is True

    def test_custom_config(self):
        """Config accepts custom values."""
        config = RendererProcessConfig(
            width=720,
            height=1280,
            use_sandbox=False,
        )
        assert config.width == 720
        assert config.height == 1280
        assert config.use_sandbox is False


class TestRendererProcess:
    """Test renderer process management."""

    @pytest.fixture
    def config(self):
        """Test configuration without sandbox (for CI)."""
        return RendererProcessConfig(
            width=320,
            height=240,
            use_sandbox=False,  # Disable sandbox for tests
        )

    @pytest.fixture
    def process(self, config):
        """Create process instance for testing."""
        proc = RendererProcess(config)
        yield proc
        # Cleanup
        proc.cleanup()

    def test_initial_state(self, process):
        """Process starts in STOPPED state."""
        assert process.state == ProcessState.STOPPED

    def test_generates_socket_path(self, process):
        """Process generates unique socket path."""
        path = process.get_socket_path()
        assert path.startswith("/tmp/linblock_renderer_")
        assert path.endswith(".sock")

    def test_generates_shm_name(self, process):
        """Process generates unique shm name."""
        name = process.get_shm_name()
        assert name.startswith("/linblock_display_")

    def test_start_creates_process(self, process):
        """Start creates subprocess."""
        process.start()
        assert process.state == ProcessState.RUNNING
        assert process.is_running()

    def test_stop_terminates_process(self, process):
        """Stop terminates subprocess."""
        process.start()
        assert process.is_running()

        process.stop()
        assert process.state == ProcessState.STOPPED
        assert not process.is_running()

    def test_double_start_raises(self, process):
        """Starting twice raises error."""
        process.start()
        with pytest.raises(RendererProcessError):
            process.start()

    def test_stop_when_stopped_is_safe(self, process):
        """Stopping when already stopped is safe."""
        process.stop()  # Should not raise
        assert process.state == ProcessState.STOPPED

    def test_state_callback_registration(self, process):
        """State callbacks are called on transitions."""
        states_seen = []

        def callback(state):
            states_seen.append(state)

        process.add_state_callback(callback)
        process.start()
        process.stop()

        assert ProcessState.STARTING in states_seen
        assert ProcessState.RUNNING in states_seen
        assert ProcessState.STOPPING in states_seen
        assert ProcessState.STOPPED in states_seen

    def test_resize_while_running(self, process):
        """Resize works while running."""
        process.start()
        process.resize(640, 480)
        # Should not raise

    def test_resize_when_stopped_raises(self, process):
        """Resize when stopped raises error."""
        with pytest.raises(RendererProcessError):
            process.resize(640, 480)

    def test_set_rotation_valid_values(self, process):
        """set_rotation accepts valid values."""
        process.start()
        for rotation in [0, 90, 180, 270]:
            process.set_rotation(rotation)  # Should not raise

    def test_cleanup_stops_process(self, process):
        """Cleanup stops running process."""
        process.start()
        process.cleanup()
        assert process.state == ProcessState.STOPPED


class TestRendererProcessIntegration:
    """Integration tests for renderer process with shared memory."""

    @pytest.fixture
    def running_process(self):
        """Create and start a renderer process."""
        config = RendererProcessConfig(
            width=320,
            height=240,
            use_sandbox=False,
        )
        proc = RendererProcess(config)
        proc.start()
        yield proc
        proc.cleanup()

    def test_shared_memory_created(self, running_process):
        """Shared memory is created when process starts."""
        shm_name = running_process.get_shm_name()
        shm_path = f"/dev/shm{shm_name}"
        assert os.path.exists(shm_path)

    def test_can_read_frame_from_shm(self, running_process):
        """Can read frame data from shared memory."""
        shm_name = running_process.get_shm_name()

        # Open shared memory
        shm = SharedMemoryDisplay(shm_name)
        shm.open()

        # Give process time to generate frame
        time.sleep(0.1)

        # Read frame
        result = shm.read_frame()
        if result:
            width, height, frame_num, timestamp, pixels = result
            assert width == 320
            assert height == 240
            assert len(pixels) == width * height * 4

        shm.cleanup()

    def test_process_commands_updates_frame(self, running_process):
        """Processing commands updates the frame."""
        shm_name = running_process.get_shm_name()
        shm = SharedMemoryDisplay(shm_name)
        shm.open()

        # Get initial frame number
        time.sleep(0.1)
        result1 = shm.read_frame()
        frame1 = result1[2] if result1 else 0

        # Process some commands
        running_process.process_commands(b"\x00" * 100)

        # Check frame number increased
        time.sleep(0.1)
        result2 = shm.read_frame()
        frame2 = result2[2] if result2 else 0

        assert frame2 > frame1

        shm.cleanup()


class TestSharedMemoryDisplay:
    """Tests for shared memory display transport."""

    @pytest.fixture
    def shm(self):
        """Create shared memory display."""
        name = f"/test_shm_{os.getpid()}"
        display = SharedMemoryDisplay(name)
        yield display
        display.cleanup()

    def test_create_allocates_memory(self, shm):
        """Create allocates shared memory."""
        shm.create(640, 480)
        shm_path = f"/dev/shm{shm._name}"
        assert os.path.exists(shm_path)

    def test_write_and_read_frame(self, shm):
        """Can write and read frame data."""
        shm.create(100, 100)

        # Write frame
        pixels = bytes([i % 256 for i in range(100 * 100 * 4)])
        shm.write_frame(pixels, 1, 12345)

        # Read frame (need second instance to simulate consumer)
        shm2 = SharedMemoryDisplay(shm._name)
        shm2.open()

        result = shm2.read_frame()
        assert result is not None
        width, height, frame_num, timestamp, read_pixels = result
        assert width == 100
        assert height == 100
        assert frame_num == 1
        assert timestamp == 12345
        assert read_pixels == pixels

        shm2.cleanup()

    def test_resize_recreates_memory(self, shm):
        """Resize recreates shared memory."""
        shm.create(100, 100)
        shm.resize(200, 200)
        assert shm.get_dimensions() == (200, 200)

    def test_cleanup_removes_file(self, shm):
        """Cleanup removes shared memory file."""
        shm.create(100, 100)
        shm_path = f"/dev/shm{shm._name}"
        assert os.path.exists(shm_path)

        shm.cleanup()
        assert not os.path.exists(shm_path)
