"""
Interface tests for permission_manager.

Tests the public API contract for granting, revoking,
auditing, and querying Android permissions.
"""

import pytest
from ..interface import (
    PermissionManagerInterface,
    DefaultPermissionManager,
    create_interface,
    PermissionManagerError,
    PermissionNotFoundError,
    PermissionState,
    PermissionCategory,
    PermissionRecord,
    AuditEntry,
)


class TestPermissionManagerInterface:
    """Test suite for PermissionManagerInterface."""

    @pytest.fixture
    def config(self):
        """Standard test configuration."""
        return {}

    @pytest.fixture
    def mgr(self, config):
        """Create a fresh permission manager for each test."""
        return create_interface(config)

    # -- creation tests -------------------------------------------------------

    def test_create_with_valid_config(self, config):
        """Interface creates successfully with valid config."""
        iface = create_interface(config)
        assert iface is not None
        assert isinstance(iface, PermissionManagerInterface)

    def test_create_with_no_config(self):
        """Interface creates with default config when None is passed."""
        iface = create_interface()
        assert iface is not None

    # -- set / get permission tests -------------------------------------------

    def test_set_then_get_permission(self, mgr):
        """set_permission followed by get_permission returns the record."""
        mgr.set_permission("com.example.app", "android.permission.CAMERA", PermissionState.GRANTED)
        record = mgr.get_permission("com.example.app", "android.permission.CAMERA")
        assert record.package == "com.example.app"
        assert record.permission == "android.permission.CAMERA"
        assert record.state == PermissionState.GRANTED
        assert record.grant_time is not None

    def test_get_permission_not_found(self, mgr):
        """get_permission raises PermissionNotFoundError for unknown record."""
        with pytest.raises(PermissionNotFoundError):
            mgr.get_permission("com.missing", "android.permission.INTERNET")

    def test_set_permission_updates_existing(self, mgr):
        """Setting a permission twice updates state rather than duplicating."""
        mgr.set_permission("com.example.app", "android.permission.CAMERA", PermissionState.DENIED)
        mgr.set_permission("com.example.app", "android.permission.CAMERA", PermissionState.GRANTED)
        record = mgr.get_permission("com.example.app", "android.permission.CAMERA")
        assert record.state == PermissionState.GRANTED
        # Should still be one record, not two.
        assert len(mgr.get_all_permissions()) == 1

    # -- get_app_permissions tests --------------------------------------------

    def test_get_app_permissions_filters_by_package(self, mgr):
        """get_app_permissions returns only records for the given package."""
        mgr.set_permission("com.a", "android.permission.CAMERA", PermissionState.GRANTED)
        mgr.set_permission("com.b", "android.permission.CAMERA", PermissionState.DENIED)
        mgr.set_permission("com.a", "android.permission.LOCATION", PermissionState.ASK)
        records = mgr.get_app_permissions("com.a")
        assert len(records) == 2
        assert all(r.package == "com.a" for r in records)

    # -- get_all_permissions tests --------------------------------------------

    def test_get_all_permissions(self, mgr):
        """get_all_permissions returns every stored record."""
        mgr.set_permission("com.a", "android.permission.CAMERA", PermissionState.GRANTED)
        mgr.set_permission("com.b", "android.permission.INTERNET", PermissionState.DENIED)
        all_perms = mgr.get_all_permissions()
        assert len(all_perms) == 2

    # -- record_usage tests ---------------------------------------------------

    def test_record_usage_increments_count(self, mgr):
        """record_usage increments use_count and sets last_used."""
        mgr.set_permission("com.app", "android.permission.CAMERA", PermissionState.GRANTED)
        mgr.record_usage("com.app", "android.permission.CAMERA")
        mgr.record_usage("com.app", "android.permission.CAMERA")
        record = mgr.get_permission("com.app", "android.permission.CAMERA")
        assert record.use_count == 2
        assert record.last_used is not None

    def test_record_usage_not_found(self, mgr):
        """record_usage raises PermissionNotFoundError for unknown record."""
        with pytest.raises(PermissionNotFoundError):
            mgr.record_usage("com.missing", "android.permission.CAMERA")

    # -- audit log tests ------------------------------------------------------

    def test_get_audit_log(self, mgr):
        """get_audit_log returns entries for all operations."""
        mgr.set_permission("com.a", "android.permission.CAMERA", PermissionState.GRANTED)
        mgr.set_permission("com.b", "android.permission.INTERNET", PermissionState.DENIED)
        log = mgr.get_audit_log()
        assert len(log) == 2
        # Most recent first.
        assert log[0].package == "com.b"
        assert log[1].package == "com.a"

    def test_get_audit_log_filtered_by_package(self, mgr):
        """get_audit_log with package filter returns only matching entries."""
        mgr.set_permission("com.a", "android.permission.CAMERA", PermissionState.GRANTED)
        mgr.set_permission("com.b", "android.permission.INTERNET", PermissionState.DENIED)
        mgr.set_permission("com.a", "android.permission.LOCATION", PermissionState.ASK)
        log = mgr.get_audit_log(package="com.a")
        assert len(log) == 2
        assert all(e.package == "com.a" for e in log)

    def test_get_audit_log_respects_limit(self, mgr):
        """get_audit_log returns at most 'limit' entries."""
        for i in range(10):
            mgr.set_permission("com.app", f"perm.{i}", PermissionState.GRANTED)
        log = mgr.get_audit_log(limit=3)
        assert len(log) == 3

    # -- cleanup tests --------------------------------------------------------

    def test_cleanup_clears_all_data(self, mgr):
        """cleanup empties permissions and audit log."""
        mgr.set_permission("com.a", "android.permission.CAMERA", PermissionState.GRANTED)
        mgr.cleanup()
        with pytest.raises(PermissionManagerError):
            mgr.get_all_permissions()
