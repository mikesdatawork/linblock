"""
Virtual CPU stub.

Represents a single virtual CPU within the emulator.
"""

from typing import Optional
from dataclasses import dataclass, field


@dataclass
class VCPURegisters:
    """General-purpose register state for a virtual CPU."""
    rax: int = 0
    rbx: int = 0
    rcx: int = 0
    rdx: int = 0
    rsi: int = 0
    rdi: int = 0
    rsp: int = 0
    rbp: int = 0
    r8: int = 0
    r9: int = 0
    r10: int = 0
    r11: int = 0
    r12: int = 0
    r13: int = 0
    r14: int = 0
    r15: int = 0
    rip: int = 0
    rflags: int = 0x0002  # Reserved bit always set


class VirtualCPU:
    """
    Represents a single virtual CPU.

    Stub implementation -- all execution methods raise NotImplementedError.
    """

    def __init__(self, vcpu_id: int) -> None:
        self._id = vcpu_id
        self._fd: Optional[int] = None
        self._registers = VCPURegisters()
        self._running = False

    @property
    def vcpu_id(self) -> int:
        return self._id

    @property
    def registers(self) -> VCPURegisters:
        return self._registers

    def attach(self, vcpu_fd: int) -> None:
        """Attach to a KVM vCPU file descriptor."""
        raise NotImplementedError("VirtualCPU requires KVM backend")

    def run(self) -> None:
        """Execute until the next VM exit."""
        raise NotImplementedError("VirtualCPU requires KVM backend")

    def halt(self) -> None:
        """Request the vCPU to halt at the next opportunity."""
        raise NotImplementedError("VirtualCPU requires KVM backend")

    def read_registers(self) -> VCPURegisters:
        """Read current register state from KVM."""
        raise NotImplementedError("VirtualCPU requires KVM backend")

    def write_registers(self, regs: VCPURegisters) -> None:
        """Write register state to KVM."""
        raise NotImplementedError("VirtualCPU requires KVM backend")

    def reset(self) -> None:
        """Reset vCPU to initial power-on state."""
        self._registers = VCPURegisters()
        self._running = False
