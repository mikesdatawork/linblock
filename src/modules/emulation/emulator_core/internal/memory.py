"""
Guest memory management stub.

Manages the guest physical address space and host memory mappings.
"""

from typing import Optional
from dataclasses import dataclass


@dataclass
class MemoryRegion:
    """A mapped region of guest physical memory."""
    slot: int
    guest_phys_addr: int
    size: int
    host_addr: Optional[int] = None
    readonly: bool = False


class GuestMemory:
    """
    Manages guest physical memory layout.

    Stub implementation -- allocation methods raise NotImplementedError
    since actual mmap operations require a real host environment.
    """

    def __init__(self, total_mb: int) -> None:
        self._total_bytes = total_mb * 1024 * 1024
        self._regions: dict[int, MemoryRegion] = {}
        self._next_slot = 0

    @property
    def total_bytes(self) -> int:
        return self._total_bytes

    @property
    def region_count(self) -> int:
        return len(self._regions)

    def allocate_region(
        self,
        guest_phys_addr: int,
        size: int,
        readonly: bool = False,
    ) -> MemoryRegion:
        """
        Allocate and map a region of guest physical memory.

        Raises NotImplementedError because actual allocation requires mmap.
        """
        raise NotImplementedError(
            "GuestMemory allocation requires mmap on a real host"
        )

    def free_region(self, slot: int) -> None:
        """Free a previously allocated memory region."""
        raise NotImplementedError(
            "GuestMemory deallocation requires munmap on a real host"
        )

    def read(self, guest_phys_addr: int, size: int) -> bytes:
        """Read bytes from guest physical memory."""
        raise NotImplementedError(
            "GuestMemory read requires mapped host memory"
        )

    def write(self, guest_phys_addr: int, data: bytes) -> None:
        """Write bytes to guest physical memory."""
        raise NotImplementedError(
            "GuestMemory write requires mapped host memory"
        )

    def cleanup(self) -> None:
        """Release all allocated memory regions."""
        self._regions.clear()
        self._next_slot = 0
