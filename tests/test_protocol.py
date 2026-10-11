"""
Automated unit tests for protocol parsing and steering overtravel.
"""

import pytest
from src.protocol import ProtocolParser
from src.steering import SteeringEngine


def test_valid_rig_packet():
    raw = "$RIG,100,50,512,512,0,1,0,0,15*5A\n"
    # Calculate checksum for payload RIG,100,50,512,512,0,1,0,0,15
    payload = "RIG,100,50,512,512,0,1,0,0,15"
    cs = ProtocolParser.calculate_xor_checksum(payload)
    packet_str = f"${payload}*{cs:02X}\n"

    parsed = ProtocolParser.parse_rig_packet(packet_str)
    assert parsed is not None
    assert parsed["sequence"] == 100
    assert parsed["encoder"] == 50
    assert parsed["accelerator"] == 1


def test_steering_overtravel():
    engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=2.0)
    engine.calibrate_centre(1000)

    # Turn right past full lock (+550 deg -> 1000 + 1100 = 2100 counts)
    phys, virt = engine.process_encoder(2100)
    assert phys == 550.0
    assert virt == 450.0  # Clamped to max range

    # Turn back by 100 deg (+450 deg -> 1900 counts)
    phys, virt = engine.process_encoder(1900)
    assert phys == 450.0
    assert virt == 450.0  # Still at lock

    # Turn back another 100 deg (+350 deg -> 1700 counts)
    phys, virt = engine.process_encoder(1700)
    assert phys == 350.0
    assert virt == 350.0  # Unclamped movement resumes immediately