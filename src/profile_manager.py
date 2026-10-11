"""
Persistent JSON profile management for controller settings and mappings.
"""

import json
import os
from typing import Dict, Any

class ProfileManager:
    def __init__(self):
        # Save to My Documents to bypass Program Files permission blocks
        base_dir = os.path.join(os.path.expanduser("~"), "Documents", "DIY Racing Controller")
        self.profiles_dir = os.path.join(base_dir, "profiles")
        os.makedirs(self.profiles_dir, exist_ok=True)
        self.default_filename = "default_profile.json"

    def get_default_profile(self) -> Dict[str, Any]:
        """Returns a safe fallback profile with NO predefined gears."""
        return {
            "profile_name": "Default",
            "steering": {
                "max_angle": 450.0,
                "counts_per_degree": 0.08333,
                "center_count": 0
            },
            "regions": [] 
        }

    def save_profile(self, data: Dict[str, Any], filename: str = None) -> bool:
        if filename is None:
            filename = self.default_filename
            
        filepath = os.path.join(self.profiles_dir, filename)
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4)
            return True
        except Exception as e:
            print(f"Failed to save profile: {e}")
            return False

    def load_profile(self, filename: str = None) -> Dict[str, Any]:
        if filename is None:
            filename = self.default_filename
            
        filepath = os.path.join(self.profiles_dir, filename)
        if not os.path.exists(filepath):
            return self.get_default_profile()

        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                
            if "regions" not in data or "steering" not in data:
                return self.get_default_profile()
                
            return data
        except Exception as e:
            print(f"Failed to load profile (corrupted): {e}")
            return self.get_default_profile()