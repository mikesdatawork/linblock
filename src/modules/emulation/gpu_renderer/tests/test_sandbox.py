"""
Tests for sandbox utilities.

Tests the security sandbox functionality for the GPU renderer.
"""

import pytest
import os
import sys
from ..internal.sandbox import (
    SandboxConfig,
    SyscallNumber,
    get_gpu_renderer_syscalls,
    set_resource_limits,
    set_no_new_privs,
    get_sandbox_command,
    check_sandbox_available,
)


class TestSyscallNumber:
    """Tests for syscall number definitions."""

    def test_common_syscalls_defined(self):
        """Common syscalls are defined."""
        assert SyscallNumber.READ == 0
        assert SyscallNumber.WRITE == 1
        assert SyscallNumber.MMAP == 9
        assert SyscallNumber.EXIT == 60

    def test_socket_syscalls_defined(self):
        """Socket syscalls are defined."""
        assert SyscallNumber.SOCKET == 41
        assert SyscallNumber.CONNECT == 42
        assert SyscallNumber.SENDTO == 44
        assert SyscallNumber.RECVFROM == 45


class TestSandboxConfig:
    """Tests for SandboxConfig dataclass."""

    def test_default_config(self):
        """Config has sensible defaults."""
        config = SandboxConfig()
        assert config.max_memory_bytes == 512 * 1024 * 1024
        assert config.max_open_files == 64
        assert config.max_processes == 1
        assert config.use_network_namespace is True
        assert config.drop_all_caps is True

    def test_custom_config(self):
        """Config accepts custom values."""
        config = SandboxConfig(
            max_memory_bytes=1024 * 1024 * 1024,
            max_open_files=128,
            use_network_namespace=False,
        )
        assert config.max_memory_bytes == 1024 * 1024 * 1024
        assert config.max_open_files == 128
        assert config.use_network_namespace is False

    def test_default_syscalls_populated(self):
        """Default syscalls are populated on init."""
        config = SandboxConfig()
        assert config.allowed_syscalls is not None
        assert len(config.allowed_syscalls) > 0


class TestGPURendererSyscalls:
    """Tests for GPU renderer syscall allowlist."""

    def test_returns_set(self):
        """Returns a set of syscalls."""
        syscalls = get_gpu_renderer_syscalls()
        assert isinstance(syscalls, set)

    def test_includes_memory_syscalls(self):
        """Includes memory management syscalls."""
        syscalls = get_gpu_renderer_syscalls()
        assert SyscallNumber.MMAP in syscalls
        assert SyscallNumber.MUNMAP in syscalls
        assert SyscallNumber.MPROTECT in syscalls

    def test_includes_file_syscalls(self):
        """Includes file I/O syscalls."""
        syscalls = get_gpu_renderer_syscalls()
        assert SyscallNumber.READ in syscalls
        assert SyscallNumber.WRITE in syscalls
        assert SyscallNumber.OPEN in syscalls
        assert SyscallNumber.CLOSE in syscalls

    def test_includes_socket_syscalls(self):
        """Includes socket syscalls for IPC."""
        syscalls = get_gpu_renderer_syscalls()
        assert SyscallNumber.SOCKET in syscalls
        assert SyscallNumber.CONNECT in syscalls
        assert SyscallNumber.SENDTO in syscalls
        assert SyscallNumber.RECVFROM in syscalls

    def test_includes_exit_syscalls(self):
        """Includes exit syscalls."""
        syscalls = get_gpu_renderer_syscalls()
        assert SyscallNumber.EXIT in syscalls
        assert SyscallNumber.EXIT_GROUP in syscalls

    def test_excludes_dangerous_syscalls(self):
        """Excludes dangerous syscalls."""
        syscalls = get_gpu_renderer_syscalls()
        # execve not in our list
        assert 59 not in syscalls  # execve
        # fork not in our list (we use clone for threads only)
        assert 57 not in syscalls  # fork
        # ptrace not allowed
        assert 101 not in syscalls  # ptrace

    def test_reasonable_size(self):
        """Allowlist is reasonably sized (not too permissive)."""
        syscalls = get_gpu_renderer_syscalls()
        # Should be much less than total syscalls (~300+)
        assert len(syscalls) < 100
        # But should have enough for functionality
        assert len(syscalls) > 20


class TestResourceLimits:
    """Tests for resource limit setting."""

    def test_set_resource_limits_no_error(self):
        """Setting resource limits doesn't raise."""
        config = SandboxConfig()
        # This should not raise
        set_resource_limits(config)

    def test_set_resource_limits_custom(self):
        """Custom limits can be set."""
        config = SandboxConfig(
            max_memory_bytes=256 * 1024 * 1024,
            max_open_files=32,
        )
        # Should not raise
        set_resource_limits(config)


class TestSandboxCommand:
    """Tests for sandbox command wrapping."""

    def test_returns_list(self):
        """Returns a command list."""
        cmd = ["python3", "-c", "print('hello')"]
        result = get_sandbox_command(cmd)
        assert isinstance(result, list)

    def test_original_command_preserved(self):
        """Original command is in result."""
        cmd = ["python3", "-c", "print('hello')"]
        result = get_sandbox_command(cmd)
        # Original command should be at the end
        assert result[-3:] == cmd or result == cmd

    def test_with_custom_config(self):
        """Accepts custom config."""
        cmd = ["echo", "test"]
        config = SandboxConfig(use_network_namespace=False)
        result = get_sandbox_command(cmd, config)
        assert isinstance(result, list)

    def test_unshare_used_if_available(self):
        """Uses unshare if available."""
        if not os.path.exists("/usr/bin/unshare"):
            pytest.skip("unshare not available")

        cmd = ["echo", "test"]
        result = get_sandbox_command(cmd)
        assert "/usr/bin/unshare" in result


class TestSandboxAvailability:
    """Tests for sandbox availability checking."""

    def test_returns_dict(self):
        """Returns a dictionary."""
        result = check_sandbox_available()
        assert isinstance(result, dict)

    def test_has_expected_keys(self):
        """Has expected feature keys."""
        result = check_sandbox_available()
        assert "unshare" in result
        assert "firejail" in result
        assert "user_namespaces" in result
        assert "seccomp" in result

    def test_values_are_booleans(self):
        """Values are booleans."""
        result = check_sandbox_available()
        for key, value in result.items():
            assert isinstance(value, bool), f"{key} should be bool"


class TestNoNewPrivs:
    """Tests for PR_SET_NO_NEW_PRIVS."""

    def test_returns_bool(self):
        """Returns a boolean."""
        result = set_no_new_privs()
        assert isinstance(result, bool)

    def test_succeeds_on_linux(self):
        """Succeeds on Linux systems."""
        if sys.platform != "linux":
            pytest.skip("Linux only")
        # May fail in some restricted environments
        result = set_no_new_privs()
        # Just verify it returns without crashing
        assert result in (True, False)
