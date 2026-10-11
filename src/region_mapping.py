"""
H-pattern joystick region boundary checking and activation mode processing.
"""

from typing import Dict, Any, List, Optional


class RegionMappingEngine:

    def __init__(self):
        self.regions: List[Dict[str, Any]] = []
        self.active_region: Optional[str] = None
        self.latched_region: Optional[str] = None

    def add_region(self, region_config: Dict[str, Any]):
        """
        region_config structure:
        {
            "name": "Gear 1",
            "x_min": -0.8, "x_max": -0.4,
            "y_min": 0.4, "y_max": 0.9,
            "output": "KEY_1",
            "mode": "hold" # hold, trigger, latch
        }
        """
        self.regions.append(region_config)

    def evaluate(self, norm_x: float, norm_y: float) -> Optional[str]:
        matched = None
        for reg in self.regions:
            if (
                reg.get("x_min", -1.0) <= norm_x <= reg.get("x_max", 1.0)
                and reg.get("y_min", -1.0) <= norm_y <= reg.get("y_max", 1.0)
            ):
                matched = reg["name"]
                break
        self.active_region = matched
        return matched