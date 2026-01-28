"""
Internal permission model for Android 14.

Contains well-known permission groups and a policy dataclass used by the
permission manager implementation.  This module is an internal implementation
detail -- consumers should use the public interface instead.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Android 14 permission groups
# ---------------------------------------------------------------------------

PERMISSION_GROUPS: Dict[str, List[str]] = {
    "android.permission-group.CALENDAR": [
        "android.permission.READ_CALENDAR",
        "android.permission.WRITE_CALENDAR",
    ],
    "android.permission-group.CAMERA": [
        "android.permission.CAMERA",
    ],
    "android.permission-group.CONTACTS": [
        "android.permission.READ_CONTACTS",
        "android.permission.WRITE_CONTACTS",
        "android.permission.GET_ACCOUNTS",
    ],
    "android.permission-group.LOCATION": [
        "android.permission.ACCESS_FINE_LOCATION",
        "android.permission.ACCESS_COARSE_LOCATION",
        "android.permission.ACCESS_BACKGROUND_LOCATION",
    ],
    "android.permission-group.MICROPHONE": [
        "android.permission.RECORD_AUDIO",
    ],
    "android.permission-group.NEARBY_DEVICES": [
        "android.permission.BLUETOOTH_ADVERTISE",
        "android.permission.BLUETOOTH_CONNECT",
        "android.permission.BLUETOOTH_SCAN",
        "android.permission.NEARBY_WIFI_DEVICES",
    ],
    "android.permission-group.NOTIFICATIONS": [
        "android.permission.POST_NOTIFICATIONS",
    ],
    "android.permission-group.PHONE": [
        "android.permission.READ_PHONE_STATE",
        "android.permission.READ_PHONE_NUMBERS",
        "android.permission.CALL_PHONE",
        "android.permission.ANSWER_PHONE_CALLS",
        "android.permission.ADD_VOICEMAIL",
        "android.permission.USE_SIP",
    ],
    "android.permission-group.READ_MEDIA_AURAL": [
        "android.permission.READ_MEDIA_AUDIO",
    ],
    "android.permission-group.READ_MEDIA_VISUAL": [
        "android.permission.READ_MEDIA_IMAGES",
        "android.permission.READ_MEDIA_VIDEO",
    ],
    "android.permission-group.SENSORS": [
        "android.permission.BODY_SENSORS",
        "android.permission.BODY_SENSORS_BACKGROUND",
    ],
    "android.permission-group.SMS": [
        "android.permission.SEND_SMS",
        "android.permission.RECEIVE_SMS",
        "android.permission.READ_SMS",
        "android.permission.RECEIVE_WAP_PUSH",
        "android.permission.RECEIVE_MMS",
    ],
    "android.permission-group.STORAGE": [
        "android.permission.READ_EXTERNAL_STORAGE",
        "android.permission.WRITE_EXTERNAL_STORAGE",
        "android.permission.MANAGE_EXTERNAL_STORAGE",
    ],
}


# ---------------------------------------------------------------------------
# Permission policy dataclass
# ---------------------------------------------------------------------------

@dataclass
class PermissionPolicy:
    """
    Policy that governs how a permission is handled at runtime.

    Attributes:
        permission: The fully-qualified Android permission string.
        group: The permission group this permission belongs to, if any.
        max_target_sdk: Maximum SDK level at which the permission is enforced
                        (None means enforced on all levels).
        auto_grant: Whether the system can auto-grant without user prompt.
        background_eligible: Whether background access can be granted.
        tags: Arbitrary metadata tags for policy engines.
    """
    permission: str
    group: Optional[str] = None
    max_target_sdk: Optional[int] = None
    auto_grant: bool = False
    background_eligible: bool = False
    tags: List[str] = field(default_factory=list)
