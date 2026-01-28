"""OS Profile data model with YAML persistence."""

from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
import yaml
import os


@dataclass
class GraphicsConfig:
    gpu_mode: str = "host"
    api: str = "opengl"
    renderer: str = "auto"

@dataclass
class AdbConfig:
    path: str = "/usr/bin/adb"
    port: int = 5555
    auto_connect: bool = True

@dataclass
class SensorConfig:
    accelerometer: bool = True
    gyroscope: bool = True
    proximity: bool = True
    gps: bool = True

@dataclass
class DeviceConfig:
    screen_preset: str = "phone"
    screen_width: int = 1080
    screen_height: int = 1920
    device_profile: str = "generic_phone"
    sensors: SensorConfig = field(default_factory=SensorConfig)

@dataclass
class StorageConfig:
    shared_folder: str = "~/LinBlock/shared"
    screenshot_dir: str = "~/LinBlock/screenshots"
    image_cache: str = "~/LinBlock/cache"

@dataclass
class NetworkConfig:
    bridge_mode: bool = False
    proxy_address: str = ""
    proxy_port: int = 0
    port_forwarding: List[str] = field(default_factory=list)

@dataclass
class InputConfig:
    keyboard_to_touch: bool = True
    gamepad: bool = False
    mouse_mode: str = "direct"

@dataclass
class CameraMediaConfig:
    webcam_passthrough: bool = False
    mic_source: str = "default"
    audio_output: str = "default"

@dataclass
class PerformanceConfig:
    hypervisor: str = "kvm"
    ram_mb: int = 4096
    cpu_cores: int = 4

@dataclass
class GoogleServicesConfig:
    play_store: bool = False
    play_services: bool = False
    play_protect: bool = False
    location_service: bool = False
    contacts_sync: bool = False
    calendar_sync: bool = False
    drive: bool = False
    chrome: bool = False
    maps: bool = False
    assistant: bool = False

@dataclass
class OSProfile:
    name: str = ""
    created: str = ""
    modified: str = ""
    graphics: GraphicsConfig = field(default_factory=GraphicsConfig)
    adb: AdbConfig = field(default_factory=AdbConfig)
    device: DeviceConfig = field(default_factory=DeviceConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)
    network: NetworkConfig = field(default_factory=NetworkConfig)
    input: InputConfig = field(default_factory=InputConfig)
    camera_media: CameraMediaConfig = field(default_factory=CameraMediaConfig)
    performance: PerformanceConfig = field(default_factory=PerformanceConfig)
    google_services: GoogleServicesConfig = field(default_factory=GoogleServicesConfig)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    def save(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, 'w') as f:
            yaml.dump(self.to_dict(), f, default_flow_style=False)

    @classmethod
    def load(cls, path: str) -> 'OSProfile':
        with open(path, 'r') as f:
            data = yaml.safe_load(f) or {}
        profile = cls()
        profile.name = data.get('name', '')
        profile.created = data.get('created', '')
        profile.modified = data.get('modified', '')
        if 'graphics' in data:
            profile.graphics = GraphicsConfig(**data['graphics'])
        if 'adb' in data:
            profile.adb = AdbConfig(**data['adb'])
        if 'device' in data:
            device_data = dict(data['device'])
            sensors_data = device_data.pop('sensors', None)
            profile.device = DeviceConfig(**device_data)
            if sensors_data:
                profile.device.sensors = SensorConfig(**sensors_data)
        if 'storage' in data:
            profile.storage = StorageConfig(**data['storage'])
        if 'network' in data:
            profile.network = NetworkConfig(**data['network'])
        if 'input' in data:
            profile.input = InputConfig(**data['input'])
        if 'camera_media' in data:
            profile.camera_media = CameraMediaConfig(**data['camera_media'])
        if 'performance' in data:
            profile.performance = PerformanceConfig(**data['performance'])
        if 'google_services' in data:
            profile.google_services = GoogleServicesConfig(**data['google_services'])
        return profile
