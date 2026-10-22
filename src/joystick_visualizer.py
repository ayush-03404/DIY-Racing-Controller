from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from PySide6.QtCore import Qt

class JoystickVisualizerWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.norm_x = 0.0
        self.norm_y = 0.0
        self.raw_x = 512
        self.raw_y = 512
        self.regions = []
        self.active_gear = "Neutral"
        self.is_live = False

        # Map gear names to their respective virtual gamepad button tags for the UI display
        self.gear_to_button = {
            "Gear 1": "LB",
            "Gear 2": "RB",
            "Gear 3": "BACK",
            "Gear 4": "START",
            "Gear 5": "LS",
            "Gear 6": "RS",
            "Reverse": "UP"
        }

    def set_regions(self, regions, active_gear):
        self.regions = regions
        self.active_gear = active_gear
        self.update()

    def update_position(self, raw_x, raw_y, norm_x, norm_y, is_live):
        self.raw_x = raw_x
        self.raw_y = raw_y
        self.norm_x = norm_x
        self.norm_y = norm_y
        self.is_live = is_live
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        width = self.width()
        height = self.height()

        # Background box
        painter.setBrush(QBrush(QColor(30, 30, 30)))
        painter.setPen(QPen(QColor(80, 80, 80), 2))
        painter.drawRect(0, 0, width, height)

        # Draw crosshairs (Neutral center)
        painter.setPen(QPen(QColor(60, 60, 60), 1, Qt.DashLine))
        painter.drawLine(width // 2, 0, width // 2, height)
        painter.drawLine(0, height // 2, width, height // 2)

        # Draw mapped regions & their assigned button labels
        for reg in self.regions:
            name = reg.get("name", "")
            btn_label = self.gear_to_button.get(name, "")
            
            x_min_px = int((reg["x_min"] + 1.0) / 2.0 * width)
            x_max_px = int((reg["x_max"] + 1.0) / 2.0 * width)
            y_min_px = int((reg["y_min"] + 1.0) / 2.0 * height)
            y_max_px = int((reg["y_max"] + 1.0) / 2.0 * height)

            r_w = x_max_px - x_min_px
            r_h = y_max_px - y_min_px

            if name == self.active_gear:
                painter.setBrush(QBrush(QColor(0, 120, 215, 120)))  # Highlight active gear
                painter.setPen(QPen(QColor(0, 150, 255), 2))
            else:
                painter.setBrush(QBrush(QColor(70, 70, 70, 80)))
                painter.setPen(QPen(QColor(120, 120, 120), 1))

            painter.drawRect(x_min_px, y_min_px, r_w, r_h)

            # Draw text inside region: Gear Name + Assigned Button
            painter.setPen(QPen(QColor(255, 255, 255)))
            painter.setFont(QFont("Arial", 9, QFont.Bold))
            display_text = f"{name}\n[{btn_label}]" if btn_label else name
            painter.drawText(x_min_px, y_min_px, r_w, r_h, Qt.AlignCenter, display_text)

        # Draw live joystick ball position
        dot_x = int((self.norm_x + 1.0) / 2.0 * width)
        dot_y = int((self.norm_y + 1.0) / 2.0 * height)

        if self.is_live:
            painter.setBrush(QBrush(QColor(40, 200, 80)))
            painter.setPen(QPen(QColor(255, 255, 255), 2))
        else:
            painter.setBrush(QBrush(QColor(150, 150, 150)))
            painter.setPen(QPen(QColor(100, 100, 100), 1))

        painter.drawEllipse(dot_x - 10, dot_y - 10, 20, 20)