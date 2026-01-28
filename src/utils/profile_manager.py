"""Profile directory scanner and manager."""

import os
from typing import List, Optional
from config.os_profile import OSProfile


class ProfileManager:
    def __init__(self, profiles_dir: str = None):
        self._dir = profiles_dir or os.path.expanduser("~/.config/linblock/profiles")

    def ensure_dir(self):
        os.makedirs(self._dir, exist_ok=True)

    def list_profiles(self) -> List[str]:
        self.ensure_dir()
        return [
            f[:-5] for f in os.listdir(self._dir)
            if f.endswith('.yaml')
        ]

    def load_profile(self, name: str) -> OSProfile:
        path = os.path.join(self._dir, f"{name}.yaml")
        return OSProfile.load(path)

    def save_profile(self, profile: OSProfile) -> None:
        self.ensure_dir()
        path = os.path.join(self._dir, f"{profile.name}.yaml")
        profile.save(path)

    def delete_profile(self, name: str) -> None:
        path = os.path.join(self._dir, f"{name}.yaml")
        if os.path.exists(path):
            os.remove(path)

    def profile_exists(self, name: str) -> bool:
        return os.path.exists(os.path.join(self._dir, f"{name}.yaml"))
