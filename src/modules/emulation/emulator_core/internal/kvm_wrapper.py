"""
KVM ioctl wrapper stub.

Low-level interface to the KVM hypervisor via /dev/kvm.
This module provides constants and placeholder methods for KVM operations.
"""

import os
from typing import Optional

# KVM ioctl command numbers (from linux/kvm.h)
KVM_GET_API_VERSION = 0xAE00
KVM_CREATE_VM = 0xAE01
KVM_CHECK_EXTENSION = 0xAE03
KVM_GET_VCPU_MMAP_SIZE = 0xAE04
KVM_CREATE_VCPU = 0xAE41
KVM_SET_USER_MEMORY_REGION = 0x4020AE46
KVM_RUN = 0xAE80
KVM_GET_REGS = 0x8090AE81
KVM_SET_REGS = 0x4090AE82
KVM_GET_SREGS = 0x8138AE83
KVM_SET_SREGS = 0x4138AE84

KVM_DEVICE_PATH = "/dev/kvm"


class KVMError(Exception):
    """Raised when a KVM operation fails."""
    pass


class KVMWrapper:
    """
    Wrapper around KVM kernel module ioctls.

    All methods raise NotImplementedError as this is a stub that requires
    a real KVM-capable host to function.
    """

    def __init__(self) -> None:
        self._fd: Optional[int] = None

    def open(self) -> None:
        """Open /dev/kvm file descriptor."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def close(self) -> None:
        """Close the KVM file descriptor."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def get_api_version(self) -> int:
        """Return the KVM API version supported by the kernel."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def create_vm(self) -> int:
        """Create a new VM and return its file descriptor."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def create_vcpu(self, vm_fd: int, vcpu_id: int) -> int:
        """Create a virtual CPU within a VM, returning its fd."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def set_user_memory_region(
        self,
        vm_fd: int,
        slot: int,
        guest_phys_addr: int,
        memory_size: int,
        userspace_addr: int,
    ) -> None:
        """Map a region of host memory into guest physical address space."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def run_vcpu(self, vcpu_fd: int) -> None:
        """Execute the vCPU until it exits."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def get_regs(self, vcpu_fd: int) -> dict:
        """Read general-purpose registers from a vCPU."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )

    def set_regs(self, vcpu_fd: int, regs: dict) -> None:
        """Write general-purpose registers to a vCPU."""
        raise NotImplementedError(
            "KVM wrapper requires a real KVM-capable host"
        )
