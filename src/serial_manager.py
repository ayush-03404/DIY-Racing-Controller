"""
Non-blocking serial worker thread using PySide6 Signals and QThread.
"""

import time
from typing import Optional
from PySide6.QtCore import QThread, Signal, Slot
import serial
import serial.tools.list_ports

from src.protocol import ProtocolParser


class SerialWorker(QThread):
    packet_received = Signal(dict)
    connection_status = Signal(bool, str)
    stats_updated = Signal(float, int, int)  # fps, checksum_errors, dropped_packets

    def __init__(self, port: str, baudrate: int = 115200):
        super().__init__()
        self.port = port
        self.baudrate = baudrate
        self.running = False
        self.serial_conn: Optional[serial.Serial] = None
        self.checksum_errors = 0
        self.dropped_packets = 0
        self.packet_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0

    @staticmethod
    def get_available_ports():
        return [port.device for port in serial.tools.list_ports.comports()]

    def run(self):
        try:
            self.serial_conn = serial.Serial(self.port, self.baudrate, timeout=0.1)
            self.running = True
            self.connection_status.emit(True, f"Connected to {self.port}")
        except Exception as e:
            self.connection_status.emit(False, str(e))
            return

        while self.running and self.serial_conn and self.serial_conn.is_open:
            try:
                line = self.serial_conn.readline()
                if line:
                    try:
                        decoded_line = line.decode("ascii", errors="ignore")
                    except UnicodeDecodeError:
                        self.dropped_packets += 1
                        continue

                    packet = ProtocolParser.parse_rig_packet(decoded_line)
                    if packet:
                        self.packet_count += 1
                        self.packet_received.emit(packet)
                    else:
                        if "$" in decoded_line and "*" in decoded_line:
                            self.checksum_errors += 1
                        else:
                            self.dropped_packets += 1

                # Calculate packet rate
                now = time.time()
                if now - self.last_fps_time >= 1.0:
                    self.current_fps = self.packet_count / (now - self.last_fps_time)
                    self.stats_updated.emit(
                        self.current_fps, self.checksum_errors, self.dropped_packets
                    )
                    self.packet_count = 0
                    self.last_fps_time = now

            except serial.SerialException as se:
                self.connection_status.emit(False, f"Serial Exception: {se}")
                break
            except Exception:
                self.dropped_packets += 1

        if self.serial_conn and self.serial_conn.is_open:
            self.serial_conn.close()
        self.connection_status.emit(False, "Disconnected")

    @Slot()
    def stop(self):
        self.running = False
        self.wait(1000)