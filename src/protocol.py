"""
Shared Serial Protocol Parser and Checksum Validator for Master-PC Link ($RIG).
"""

from typing import Dict, Any, Optional, Tuple


class ProtocolParser:
    @staticmethod
    def calculate_xor_checksum(payload: str) -> int:
        cs = 0
        for char in payload:
            cs ^= ord(char)
        return cs

    @classmethod
    def parse_rig_packet(cls, raw_line: str) -> Optional[Dict[str, Any]]:
        line = raw_line.strip()
        if not line.startswith("$") or "*" not in line:
            return None

        try:
            payload_part, cs_str = line[1:].rsplit("*", 1)
            received_cs = int(cs_str, 16)
        except (ValueError, IndexError):
            return None

        calculated_cs = cls.calculate_xor_checksum(payload_part)
        if calculated_cs != received_cs:
            return None

        fields = payload_part.split(",")
        if len(fields) != 10 or fields[0] != "RIG":
            return None

        try:
            packet = {
                "header": fields[0],
                "sequence": int(fields[1]),
                "encoder": int(fields[2]),
                "joyX": int(fields[3]),
                "joyY": int(fields[4]),
                "horn": int(fields[5]),
                "accelerator": int(fields[6]),
                "brake": int(fields[7]),
                "clutch": int(fields[8]),
                "slaveAgeMs": int(fields[9]),
            }
        except ValueError:
            return None

        # Validate ranges
        if not (0 <= packet["joyX"] <= 1023 and 0 <= packet["joyY"] <= 1023):
            return None
        if not all(
            v in (0, 1)
            for v in (
                packet["horn"],
                packet["accelerator"],
                packet["brake"],
                packet["clutch"],
            )
        ):
            return None

        return packet