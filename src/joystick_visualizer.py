"""
Custom PySide6 Widget for live X/Y coordinate plane and H-pattern region overlay.
"""

from typing import Dict, List, Tuple, Any
from PySide6.QtCore import Qt, QRectF
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtWidgets import QWidget


class JoystickVisualizerWidget(QWidget):

    def __init__(self, parent=None):
        super().__init__(parent)
        self.raw_x = 512
        self.raw_y = 512
        self.norm_x = 0.0
        self.norm_y = 0.0
        self.regions: List[Dict[str, Any]] = []
        self.active_region_name = "Neutral"
        self.is_connected = False
        self.setMinimumSize(250, 250)

    def update_position(
        self,
        raw_x: int,
        raw_y: int,
        norm_x: float,
        norm_y: float,
        connected: bool,
    ):
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.norm_x = max(-1.0, min(1.0, norm_x))
        self.norm_y = max(-1.0, min(1.0, norm_y))
        self.is_connected = connected
        self.update()

    def set_regions(self, regions: List[Dict[str, Any]], active_name: str):
        self.regions = regions
        self.active_region_name = active_name
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()
        side = min(width, height)
        
        # Center square plane
        plane_rect = QRectF(
            (width - side) / 2 + 20,
            (height - side) / 2 + 20,
            side - 40,
            side - 40,
        )

        # Background
        painter.fillRect(plane_rect, QBrush(QColor(30, 30, 30)))
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawRect(plane_rect)

        # Center axes
        cx = plane_rect.center().x()
        cy = plane_rect.center().y()
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.DashLine))
        painter.drawLine(plane_rect.left(), cy, plane_rect.right(), cy)
        painter.drawLine(cx, plane_rect.top(), cx, plane_rect.bottom())

        # Draw H-pattern regions if configured
        for reg in self.regions:
            rx1 = plane_rect.left() + (reg["x_min"] + 1.0) / 2.0 * plane_rect.width()
            rx2 = plane_rect.left() + (reg["x_max"] + 1.0) / 2.0 * plane_rect.width()
            ry1 = plane_rect.top() + (1.0 - (reg["y_max"] + 1.0) / 2.0) * plane_rect.height()
            ry2 = plane_rect.top() + (1.0 - (reg["y_min"] + 1.0) / 2.0) * plane_rect.height()
            r_rect = QRectF(rx1, ry1, rx2 - rx1, ry2 - ry1)

            if reg["name"] == self.active_region_name:
                painter.fillRect(r_rect, QBrush(QColor(0, 120, 215, 80)))
                painter.setPen(QPen(QColor(0, 120, 215), 2))
            else:
                painter.fillRect(r_rect, QBrush(QColor(60, 60, 60, 40)))
                painter.setPen(QPen(QColor(100, 100, 100), 1))
            painter.drawRect(r_rect)

            painter.setPen(QPen(QColor(200, 200, 200), 1))
            painter.setFont(QFont("Segoe UI", 8))
            painter.drawText(r_rect, Qt.AlignCenter, reg["name"])

        # Current Position Marker
        if self.is_connected:
            marker_x = cx + self.norm_x * (plane_rect.width() / 2.0)
            marker_y = cy - self.norm_y * (plane_rect.height() / 2.0) # Screen Y inverted
            painter.setBrush(QBrush(QColor(0, 200, 100)))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawEllipse(QRectF(marker_x - 8, marker_y - 8, 16, 16))
        else:
            painter.setPen(QPen(QColor(200, 50, 50), 1))
            painter.setFont(QFont("Segoe UI", 12, QFont.Bold))
            painter.drawText(plane_rect, Qt.AlignCenter, "DISCONNECTED / STALE")