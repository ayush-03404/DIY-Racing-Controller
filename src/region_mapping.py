from typing import Optional, List, Dict, Any

class RegionMappingEngine:
    def __init__(self):
        self.regions: List[Dict[str, Any]] = []
        self.active_region: str = "Neutral"

    def add_region(self, region_dict: Dict[str, Any]):
        # Replace if region name already exists, otherwise append
        for reg in self.regions:
            if reg["name"] == region_dict["name"]:
                reg.update(region_dict)
                return
        self.regions.append(region_dict)

    def evaluate(self, norm_x: float, norm_y: float) -> Optional[str]:
        matched = None
        # Iterate through regions to find where the normalized point falls
        for reg in self.regions:
            if (
                reg.get("x_min", -1.0) <= norm_x <= reg.get("x_max", 1.0)
                and reg.get("y_min", -1.0) <= norm_y <= reg.get("y_max", 1.0)
            ):
                matched = reg["name"]
                break  # Stop at the first valid matching gate
        
        self.active_region = matched or "Neutral"
        return matched