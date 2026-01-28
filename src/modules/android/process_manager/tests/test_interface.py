"""
Interface tests for process_manager.

Tests the public API contract for listing, inspecting, spawning,
killing, and querying resource usage of Android processes.
"""

import pytest
from ..interface import (
    ProcessManagerInterface,
    DefaultProcessManager,
    create_interface,
    ProcessManagerError,
    ProcessNotFoundError,
    ProcessInfo,
)


class TestProcessManagerInterface:
    """Test suite for ProcessManagerInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def mgr(self, config):
        """Create a fresh process manager for each test."""
        return create_interface(config)

    # -- creation tests -------------------------------------------------------

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, ProcessManagerInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config when None is passed."""
        iface = create_interface()
        assert iface is not None

    # -- add_process / list_processes tests -----------------------------------

    def test_add_process_returns_process_info(self, mgr):
        """add_process returns a populated ProcessInfo."""
        info = mgr.add_process(1001, "com.example.app", "main")
        assert isinstance(info, ProcessInfo)
        assert info.pid == 1001
        assert info.package == "com.example.app"
        assert info.name == "main"
        assert info.state == "running"

    def test_list_processes_includes_added(self, mgr):
        """list_processes returns all added processes."""
        mgr.add_process(1, "com.a", "proc_a")
        mgr.add_process(2, "com.b", "proc_b")
        procs = mgr.list_processes()
        assert len(procs) == 2

    def test_list_processes_empty_initially(self, mgr):
        """list_processes returns empty list when nothing is tracked."""
        assert mgr.list_processes() == []

    # -- get_process tests ----------------------------------------------------

    def test_get_process_returns_correct_process(self, mgr):
        """get_process returns the ProcessInfo for the given PID."""
        mgr.add_process(42, "com.example.app", "worker")
        proc = mgr.get_process(42)
        assert proc.pid == 42
        assert proc.name == "worker"

    def test_get_process_not_found(self, mgr):
        """get_process raises ProcessNotFoundError for unknown PID."""
        with pytest.raises(ProcessNotFoundError):
            mgr.get_process(9999)

    # -- kill_process tests ---------------------------------------------------

    def test_kill_process_removes_from_list(self, mgr):
        """kill_process removes the process so it no longer appears."""
        mgr.add_process(10, "com.a", "proc")
        mgr.kill_process(10)
        assert mgr.list_processes() == []

    def test_kill_process_not_found(self, mgr):
        """kill_process raises ProcessNotFoundError for unknown PID."""
        with pytest.raises(ProcessNotFoundError):
            mgr.kill_process(9999)

    # -- get_processes_by_package tests ---------------------------------------

    def test_get_processes_by_package_filters(self, mgr):
        """get_processes_by_package returns only matching processes."""
        mgr.add_process(1, "com.a", "main")
        mgr.add_process(2, "com.b", "main")
        mgr.add_process(3, "com.a", "worker")
        procs = mgr.get_processes_by_package("com.a")
        assert len(procs) == 2
        assert all(p.package == "com.a" for p in procs)

    def test_get_processes_by_package_empty(self, mgr):
        """get_processes_by_package returns empty list for unknown package."""
        mgr.add_process(1, "com.a", "main")
        assert mgr.get_processes_by_package("com.unknown") == []

    # -- get_resource_usage tests ---------------------------------------------

    def test_get_resource_usage_aggregates(self, mgr):
        """get_resource_usage sums CPU and memory across processes."""
        p1 = mgr.add_process(1, "com.a", "main")
        p1.cpu_percent = 10.5
        p1.memory_mb = 128.0
        p2 = mgr.add_process(2, "com.b", "main")
        p2.cpu_percent = 5.5
        p2.memory_mb = 64.0
        usage = mgr.get_resource_usage()
        assert usage["total_cpu_percent"] == 16.0
        assert usage["total_memory_mb"] == 192.0
        assert usage["process_count"] == 2

    def test_get_resource_usage_empty(self, mgr):
        """get_resource_usage returns zeros when no processes exist."""
        usage = mgr.get_resource_usage()
        assert usage["total_cpu_percent"] == 0.0
        assert usage["total_memory_mb"] == 0.0
        assert usage["process_count"] == 0

    # -- cleanup tests --------------------------------------------------------

    def test_cleanup_clears_all_processes(self, mgr):
        """cleanup empties the process table."""
        mgr.add_process(1, "com.a", "main")
        mgr.cleanup()
        with pytest.raises(ProcessManagerError):
            mgr.list_processes()

    def test_method_after_cleanup_raises(self, mgr):
        """Methods raise ProcessManagerError after cleanup."""
        mgr.cleanup()
        with pytest.raises(ProcessManagerError):
            mgr.add_process(1, "com.a", "main")
