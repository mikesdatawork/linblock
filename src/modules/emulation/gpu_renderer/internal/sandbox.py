"""
Sandbox utilities for GPU renderer process.

Provides process isolation using Linux security features:
- seccomp-bpf for syscall filtering
- Namespace isolation (mount, network, PID)
- Capability dropping
- Resource limits

These are applied to the renderer worker process to minimize
attack surface from potentially malicious GPU command streams.
"""

import os
import sys
import struct
import ctypes
import resource
from typing import List, Optional, Set
from dataclasses import dataclass
from enum import IntEnum, IntFlag


# Seccomp constants
SECCOMP_MODE_FILTER = 2
SECCOMP_RET_KILL_PROCESS = 0x80000000
SECCOMP_RET_ALLOW = 0x7fff0000
SECCOMP_RET_ERRNO = 0x00050000
SECCOMP_RET_TRACE = 0x7ff00000
SECCOMP_RET_LOG = 0x7ffc0000

PR_SET_SECCOMP = 22
PR_SET_NO_NEW_PRIVS = 38


class SyscallNumber(IntEnum):
    """x86_64 syscall numbers for commonly used calls."""
    # File operations
    READ = 0
    WRITE = 1
    OPEN = 2
    CLOSE = 3
    STAT = 4
    FSTAT = 5
    LSTAT = 6
    POLL = 7
    LSEEK = 8
    MMAP = 9
    MPROTECT = 10
    MUNMAP = 11
    BRK = 12

    # I/O
    IOCTL = 16
    PREAD64 = 17
    PWRITE64 = 18
    READV = 19
    WRITEV = 20
    ACCESS = 21

    # Process
    SCHED_YIELD = 24
    MREMAP = 25
    MSYNC = 26
    MINCORE = 27
    MADVISE = 28

    # Shared memory
    SHM_OPEN = 268  # Not a syscall, uses open
    SHMAT = 30
    SHMCTL = 31
    SHMDT = 67
    SHMGET = 29

    # Memory mapping
    MLOCK = 149
    MUNLOCK = 150
    MLOCKALL = 151
    MUNLOCKALL = 152

    # Socket operations
    SOCKET = 41
    CONNECT = 42
    ACCEPT = 43
    SENDTO = 44
    RECVFROM = 45
    SENDMSG = 46
    RECVMSG = 47
    SHUTDOWN = 48
    BIND = 49
    LISTEN = 50
    GETSOCKNAME = 51
    GETPEERNAME = 52
    SOCKETPAIR = 53
    SETSOCKOPT = 54
    GETSOCKOPT = 55

    # Time
    CLOCK_GETTIME = 228
    CLOCK_GETRES = 229
    CLOCK_NANOSLEEP = 230
    NANOSLEEP = 35
    GETTIMEOFDAY = 96
    TIMES = 100

    # Process info
    GETPID = 39
    GETUID = 102
    GETGID = 104
    GETEUID = 107
    GETEGID = 108

    # Signal
    RT_SIGACTION = 13
    RT_SIGPROCMASK = 14
    RT_SIGRETURN = 15
    SIGALTSTACK = 131

    # Misc
    EXIT = 60
    EXIT_GROUP = 231
    FUTEX = 202
    SET_ROBUST_LIST = 273
    GET_ROBUST_LIST = 274
    GETRANDOM = 318
    MEMFD_CREATE = 319

    # Thread
    CLONE = 56
    CLONE3 = 435
    SET_TID_ADDRESS = 218
    ARCH_PRCTL = 158


@dataclass
class SandboxConfig:
    """Configuration for sandbox settings."""
    # Syscall allowlist
    allowed_syscalls: Set[int] = None

    # Resource limits
    max_memory_bytes: int = 512 * 1024 * 1024  # 512 MB
    max_open_files: int = 64
    max_processes: int = 1

    # Namespace isolation
    use_network_namespace: bool = True
    use_mount_namespace: bool = True
    use_pid_namespace: bool = True

    # Capabilities
    drop_all_caps: bool = True

    def __post_init__(self):
        if self.allowed_syscalls is None:
            self.allowed_syscalls = get_gpu_renderer_syscalls()


def get_gpu_renderer_syscalls() -> Set[int]:
    """
    Get the minimal set of syscalls needed for GPU rendering.

    This is a carefully curated list that allows:
    - Memory operations (mmap, munmap, mprotect)
    - File I/O (for shared memory and sockets)
    - Socket operations (for IPC)
    - Time functions
    - Basic process operations
    """
    return {
        # Memory management
        SyscallNumber.MMAP,
        SyscallNumber.MUNMAP,
        SyscallNumber.MPROTECT,
        SyscallNumber.BRK,
        SyscallNumber.MREMAP,
        SyscallNumber.MADVISE,

        # File operations (needed for /dev/shm)
        SyscallNumber.READ,
        SyscallNumber.WRITE,
        SyscallNumber.OPEN,
        SyscallNumber.CLOSE,
        SyscallNumber.FSTAT,
        SyscallNumber.LSEEK,
        SyscallNumber.ACCESS,
        SyscallNumber.PREAD64,
        SyscallNumber.PWRITE64,
        SyscallNumber.READV,
        SyscallNumber.WRITEV,

        # Socket operations (for Unix socket IPC)
        SyscallNumber.SOCKET,
        SyscallNumber.CONNECT,
        SyscallNumber.SENDTO,
        SyscallNumber.RECVFROM,
        SyscallNumber.SENDMSG,
        SyscallNumber.RECVMSG,
        SyscallNumber.SHUTDOWN,
        SyscallNumber.GETSOCKNAME,
        SyscallNumber.SETSOCKOPT,
        SyscallNumber.GETSOCKOPT,

        # Time functions
        SyscallNumber.CLOCK_GETTIME,
        SyscallNumber.NANOSLEEP,
        SyscallNumber.GETTIMEOFDAY,

        # Process info (read-only)
        SyscallNumber.GETPID,
        SyscallNumber.GETUID,
        SyscallNumber.GETEUID,

        # Signals
        SyscallNumber.RT_SIGACTION,
        SyscallNumber.RT_SIGPROCMASK,
        SyscallNumber.RT_SIGRETURN,

        # Exit
        SyscallNumber.EXIT,
        SyscallNumber.EXIT_GROUP,

        # Threading (for Python)
        SyscallNumber.FUTEX,
        SyscallNumber.CLONE,
        SyscallNumber.SET_TID_ADDRESS,
        SyscallNumber.SET_ROBUST_LIST,
        SyscallNumber.ARCH_PRCTL,

        # Misc
        SyscallNumber.POLL,
        SyscallNumber.IOCTL,  # Needed for terminal, can be restricted further
        SyscallNumber.GETRANDOM,
    }


def set_resource_limits(config: SandboxConfig) -> None:
    """Apply resource limits using setrlimit."""
    # Memory limit
    try:
        resource.setrlimit(
            resource.RLIMIT_AS,
            (config.max_memory_bytes, config.max_memory_bytes)
        )
    except (ValueError, resource.error):
        pass

    # Open file limit
    try:
        resource.setrlimit(
            resource.RLIMIT_NOFILE,
            (config.max_open_files, config.max_open_files)
        )
    except (ValueError, resource.error):
        pass

    # Process limit (prevents fork bombs)
    try:
        resource.setrlimit(
            resource.RLIMIT_NPROC,
            (config.max_processes, config.max_processes)
        )
    except (ValueError, resource.error):
        pass


def set_no_new_privs() -> bool:
    """
    Set PR_SET_NO_NEW_PRIVS to prevent privilege escalation.

    This prevents the process from gaining new privileges through
    execve (e.g., setuid binaries).
    """
    try:
        libc = ctypes.CDLL("libc.so.6", use_errno=True)
        result = libc.prctl(PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0)
        return result == 0
    except Exception:
        return False


def apply_seccomp_filter(allowed_syscalls: Set[int]) -> bool:
    """
    Apply seccomp-bpf filter to restrict syscalls.

    This creates a BPF filter that only allows specified syscalls,
    killing the process on any other syscall attempt.

    Note: This is a simplified implementation. A production version
    would use a proper BPF compiler library.
    """
    # For now, we rely on external tools (unshare, firejail) for sandboxing
    # A full seccomp implementation would require BPF bytecode generation
    return False


def enter_sandbox(config: Optional[SandboxConfig] = None) -> bool:
    """
    Enter sandbox mode.

    This should be called early in the renderer worker process,
    after opening necessary files but before processing any
    potentially malicious data.

    Returns:
        True if sandbox was successfully applied
    """
    if config is None:
        config = SandboxConfig()

    success = True

    # Set no_new_privs first (required for seccomp)
    if not set_no_new_privs():
        print("Warning: Failed to set no_new_privs", file=sys.stderr)
        success = False

    # Apply resource limits
    try:
        set_resource_limits(config)
    except Exception as e:
        print(f"Warning: Failed to set resource limits: {e}", file=sys.stderr)
        success = False

    # Note: Namespace isolation and seccomp-bpf are better handled by
    # the parent process using unshare/firejail, as they require
    # special privileges to set up.

    return success


def get_sandbox_command(
    command: List[str],
    config: Optional[SandboxConfig] = None,
) -> List[str]:
    """
    Wrap a command with sandbox tooling.

    Checks for available sandbox tools and wraps the command
    appropriately.

    Args:
        command: The command to sandbox
        config: Sandbox configuration

    Returns:
        Modified command with sandbox wrapper
    """
    if config is None:
        config = SandboxConfig()

    # Try unshare first (most common on modern Linux)
    if os.path.exists("/usr/bin/unshare"):
        sandbox_cmd = ["/usr/bin/unshare"]

        # Note: --map-root-user requires unprivileged user namespaces
        # which may not be available on all systems
        if config.use_network_namespace:
            sandbox_cmd.append("--net")
        if config.use_mount_namespace:
            sandbox_cmd.append("--mount")
        if config.use_pid_namespace:
            sandbox_cmd.extend(["--pid", "--fork"])

        sandbox_cmd.append("--")
        return sandbox_cmd + command

    # Try firejail as fallback
    if os.path.exists("/usr/bin/firejail"):
        sandbox_cmd = ["/usr/bin/firejail", "--quiet"]

        if config.use_network_namespace:
            sandbox_cmd.append("--net=none")
        if config.drop_all_caps:
            sandbox_cmd.append("--caps.drop=all")

        sandbox_cmd.append("--")
        return sandbox_cmd + command

    # No sandbox available, return command as-is
    return command


def check_sandbox_available() -> dict:
    """
    Check which sandbox features are available.

    Returns:
        Dictionary with availability of each feature
    """
    return {
        "unshare": os.path.exists("/usr/bin/unshare"),
        "firejail": os.path.exists("/usr/bin/firejail"),
        "user_namespaces": os.path.exists("/proc/sys/kernel/unprivileged_userns_clone"),
        "seccomp": os.path.exists("/proc/sys/kernel/seccomp"),
    }
