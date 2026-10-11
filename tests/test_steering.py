"""
Automated unit tests for SteeringEngine calibration, overtravel, and output normalization.
"""

import pytest
from src.steering import SteeringEngine


def test_steering_centre_calibration():
    engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=2.0)
    engine.calibrate_centre(500)
    phys, virt = engine.process_encoder(500)
    assert phys == 0.0
    assert virt == 0.0


def test_steering_rotation_positive_negative():
    engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=2.0)
    engine.calibrate_centre(0)

    # Clockwise rotation (+90 degrees -> 180 counts)
    phys, virt = engine.process_encoder(180)
    assert phys == 90.0
    assert virt == 90.0

    # Counter-clockwise rotation (-90 degrees -> -180 counts)
    phys, virt = engine.process_encoder(-180)
    assert phys == -90.0
    assert virt == -90.0


def test_steering_overtravel_clamping():
    engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=2.0)
    engine.calibrate_centre(1000)

    # Turn right past full lock (+550 deg -> 1000 + 1100 = 2100 counts)
    phys, virt = engine.process_encoder(2100)
    assert phys == 550.0
    assert virt == 450.0  # Virtual output is clamped

    # Turn left past full lock (-550 deg -> 1000 - 1100 = -100 counts)
    phys, virt = engine.process_encoder(-100)
    assert phys == -550.0
    assert virt == -450.0  # Virtual output is clamped


def test_steering_overtravel_recovery_sequence():
    engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=2.0)
    engine.calibrate_centre(1000)

    # 1. Turn to +550 deg (2100 counts) -> Virtual = +450 deg
    engine.process_encoder(2100)
    
    # 2. Turn back by 100 deg to +450 deg (1900 counts) -> Virtual should still be locked at +450 deg
    phys, virt = engine.process_encoder(1900)
    assert phys == 450.0
    assert virt == 450.0

    # 3. Turn back another 100 deg to +350 deg (1700 counts) -> Virtual should now decrease to +350 deg
    phys, virt = engine.process_encoder(1700)
    assert phys == 350.0
    assert virt == 350.0


def test_steering_output_normalization():
    engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=2.0)
    assert engine.get_normalized_output(0.0) == 0.0
    assert engine.get_normalized_output(450.0) == 1.0
    assert engine.get_normalized_output(-450.0) == -1.0
    assert engine.get_normalized_output(900.0) == 1.0  # Clamped normalization