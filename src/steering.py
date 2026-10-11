"""
Continuous cumulative steering count handling with overtravel preservation.
"""

from typing import Tuple


class SteeringEngine:

    def __init__(
        self, max_steering_angle: float = 450.0, counts_per_degree: float = 2.0
    ):
        self.max_steering_angle = max_steering_angle
        self.counts_per_degree = counts_per_degree
        self.centre_reference_count = 0
        self.inversion = 1
        self.dead_zone_deg = 0.0

    def calibrate_centre(self, current_encoder_count: int):
        self.centre_reference_count = current_encoder_count

    def process_encoder(self, raw_encoder_count: int) -> Tuple[float, float]:
        """Returns (physical_relative_angle_deg, clamped_virtual_angle_deg)."""
        delta_counts = (raw_encoder_count - self.centre_reference_count) * self.inversion
        physical_deg = delta_counts / self.counts_per_degree

        # Apply dead zone
        if abs(physical_deg) < self.dead_zone_deg:
            physical_deg = 0.0

        # Preserve overtravel: clamp only the virtual output angle
        clamped_deg = max(
            -self.max_steering_angle,
            min(self.max_steering_angle, physical_deg),
        )
        return physical_deg, clamped_deg

    def get_normalized_output(self, clamped_virtual_angle_deg: float) -> float:
        """Normalizes virtual angle to -1.0 to +1.0 for gamepad/keyboard backends."""
        if self.max_steering_angle == 0:
            return 0.0
        return max(
            -1.0,
            min(1.0, clamped_virtual_angle_deg / self.max_steering_angle),
        )