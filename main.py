import sys
import os
from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QFont, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QComboBox, QLabel, QGroupBox, QCheckBox, QTabWidget,
    QFormLayout, QProgressBar, QGridLayout, QMessageBox, QSpinBox
)

from src.serial_manager import SerialWorker
from src.steering import SteeringEngine
from src.joystick_visualizer import JoystickVisualizerWidget
from src.region_mapping import RegionMappingEngine
from src.gamepad_backend import GamepadBackendAdapter
from src.keyboard_output import KeyboardOutputManager
from src.profile_manager import ProfileManager

class RacingControllerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DIY Racing Controller Dashboard")
        self.resize(1000, 750)
        
        icon_path = self.resource_path("icon.ico")
        self.setWindowIcon(QIcon(icon_path))

        self.profile_manager = ProfileManager()
        self.region_engine = RegionMappingEngine()
        self.steering_engine = SteeringEngine(max_steering_angle=450.0, counts_per_degree=0.08333)
        self.gamepad = GamepadBackendAdapter()
        self.keyboard = KeyboardOutputManager()
        
        self.serial_worker = None
        self.is_connected = False
        
        self.current_norm_x = 0.0
        self.current_norm_y = 0.0
        self.current_raw_encoder = 0
        
        self.load_active_profile()
        self.init_ui()

    def resource_path(self, relative_path):
        try:
            base_path = sys._MEIPASS
        except Exception:
            base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    def load_active_profile(self):
        profile = self.profile_manager.load_profile()
        self.steering_engine.counts_per_degree = profile["steering"].get("counts_per_degree", 0.08333)
        self.steering_engine.max_steering_angle = profile["steering"].get("max_angle", 450.0)
        self.steering_engine.calibrate_centre(profile["steering"].get("center_count", 0))
        
        self.region_engine.regions.clear()
        for reg in profile.get("regions", []):
            self.region_engine.add_region(reg)

    def save_active_profile(self):
        data = {
            "profile_name": "Default",
            "steering": {
                "max_angle": self.steering_engine.max_steering_angle,
                "counts_per_degree": self.steering_engine.counts_per_degree,
                "center_count": self.steering_engine.centre_reference_count
            },
            "regions": self.region_engine.regions
        }
        success = self.profile_manager.save_profile(data)
        if success:
            QMessageBox.information(self, "Success", "Profile saved successfully!")
            self.status_lbl.setText("Profile saved to disk.")
        else:
            QMessageBox.critical(self, "Error", "Failed to save profile.")

    def init_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        top_bar = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        
        self.btn_refresh = QPushButton("Refresh Ports")
        self.btn_refresh.clicked.connect(self.refresh_ports)
        
        self.btn_connect = QPushButton("Connect")
        self.btn_connect.clicked.connect(self.toggle_connection)
        
        self.chk_enable_output = QCheckBox("Enable Game Controls (Disable for Preview Mode)")
        self.chk_enable_output.setChecked(False)

        self.btn_release_all = QPushButton("EMERGENCY RELEASE ALL CONTROLS")
        self.btn_release_all.setStyleSheet("background-color: darkred; color: white; font-weight: bold;")
        self.btn_release_all.clicked.connect(self.release_all_outputs)

        top_bar.addWidget(QLabel("COM Port:"))
        top_bar.addWidget(self.port_combo)
        top_bar.addWidget(self.btn_refresh)
        top_bar.addWidget(self.btn_connect)
        top_bar.addStretch()
        top_bar.addWidget(self.chk_enable_output)
        top_bar.addWidget(self.btn_release_all)
        main_layout.addLayout(top_bar)

        tabs = QTabWidget()
        main_layout.addWidget(tabs)

        dash_widget = QWidget()
        dash_layout = QHBoxLayout(dash_widget)
        
        left_panel = QVBoxLayout()
        steer_box = QGroupBox("Steering Telemetry")
        steer_layout = QFormLayout(steer_box)
        
        self.spin_max_angle = QSpinBox()
        self.spin_max_angle.setRange(45, 1080)
        self.spin_max_angle.setSingleStep(15)
        self.spin_max_angle.setSuffix("°")
        self.spin_max_angle.setValue(int(self.steering_engine.max_steering_angle))
        self.spin_max_angle.valueChanged.connect(self.update_max_angle)

        self.lbl_steer_raw = QLabel("0")
        self.lbl_steer_phys = QLabel("0.0°")
        self.lbl_steer_virt = QLabel("0.0°")
        self.lbl_steer_norm = QLabel("0.00")
        self.lbl_ratio = QLabel(f"{self.steering_engine.counts_per_degree:.4f} counts/deg")
        
        self.btn_center_steer = QPushButton("Set Current Position as Center")
        self.btn_center_steer.clicked.connect(self.calibrate_steering_center)

        self.btn_auto_calibrate = QPushButton("Auto-Calibrate 360° Rotation")
        self.btn_auto_calibrate.setStyleSheet("background-color: #28a745; color: white; font-weight: bold;")
        self.btn_auto_calibrate.clicked.connect(self.auto_calibrate_steering)

        steer_layout.addRow("Max Angle (Soft Lock):", self.spin_max_angle)
        steer_layout.addRow("Active Ratio:", self.lbl_ratio)
        steer_layout.addRow("Raw Encoder:", self.lbl_steer_raw)
        steer_layout.addRow("Physical Angle:", self.lbl_steer_phys)
        steer_layout.addRow("Virtual (Clamped):", self.lbl_steer_virt)
        steer_layout.addRow("Normalized Output:", self.lbl_steer_norm)
        steer_layout.addRow("", self.btn_center_steer)
        steer_layout.addRow("", self.btn_auto_calibrate)
        left_panel.addWidget(steer_box)

        pedal_box = QGroupBox("Pedals & Horn")
        pedal_layout = QFormLayout(pedal_box)
        self.bar_accel = QProgressBar()
        self.bar_accel.setMaximum(1)
        self.bar_brake = QProgressBar()
        self.bar_brake.setMaximum(1)
        self.bar_clutch = QProgressBar()
        self.bar_clutch.setMaximum(1)
        self.lbl_horn = QLabel("RELEASED")
        
        pedal_layout.addRow("Accelerator:", self.bar_accel)
        pedal_layout.addRow("Brake:", self.bar_brake)
        pedal_layout.addRow("Clutch:", self.bar_clutch)
        pedal_layout.addRow("Horn:", self.lbl_horn)
        left_panel.addWidget(pedal_box)
        left_panel.addStretch()
        dash_layout.addLayout(left_panel, 1)

        right_panel = QVBoxLayout()
        visualizer_box = QGroupBox("Live H-Pattern Visualizer")
        vis_layout = QVBoxLayout(visualizer_box)
        self.joystick_viz = JoystickVisualizerWidget()
        self.joystick_viz.set_regions(self.region_engine.regions, "Neutral")
        
        self.lbl_joy_data = QLabel("X: 512 | Y: 512 | Gear: Neutral")
        self.lbl_joy_data.setAlignment(Qt.AlignCenter)
        self.lbl_joy_data.setFont(QFont("Consolas", 11, QFont.Bold))
        
        vis_layout.addWidget(self.joystick_viz, 1)
        vis_layout.addWidget(self.lbl_joy_data)
        right_panel.addWidget(visualizer_box, 3)

        mapping_box = QGroupBox("Quick Gear Mapping (Move Joystick, then click Set)")
        mapping_layout = QGridLayout(mapping_box)
        
        # Sequentially ordered mapping buttons
        gears = ["Gear 1", "Gear 2", "Gear 3", "Gear 4", "Gear 5", "Gear 6", "Reverse"]
        for i, g_name in enumerate(gears):
            btn = QPushButton(f"Set {g_name}")
            btn.clicked.connect(lambda checked, name=g_name: self.set_gear_region(name))
            mapping_layout.addWidget(btn, i // 2, i % 2)

        self.btn_clear_gears = QPushButton("Clear All Gears")
        self.btn_clear_gears.setStyleSheet("background-color: darkorange; color: white; font-weight: bold;")
        self.btn_clear_gears.clicked.connect(self.clear_all_gears)
        mapping_layout.addWidget(self.btn_clear_gears, 4, 0, 1, 2)

        right_panel.addWidget(mapping_box, 1)
        dash_layout.addLayout(right_panel, 2)
        tabs.addTab(dash_widget, "Dashboard")

        settings_widget = QWidget()
        settings_layout = QVBoxLayout(settings_widget)
        
        profile_box = QGroupBox("Profile Management")
        profile_hlayout = QHBoxLayout(profile_box)
        
        self.btn_save_profile = QPushButton("Save Settings & Gear Map to Profile")
        self.btn_save_profile.setStyleSheet("background-color: #0078D7; color: white; padding: 10px; font-weight: bold;")
        self.btn_save_profile.clicked.connect(self.save_active_profile)
        
        self.btn_load_profile = QPushButton("Reload Profile from Disk")
        self.btn_load_profile.clicked.connect(self.trigger_profile_reload)

        profile_hlayout.addWidget(self.btn_save_profile)
        profile_hlayout.addWidget(self.btn_load_profile)
        
        settings_layout.addWidget(profile_box)
        settings_layout.addStretch()
        tabs.addTab(settings_widget, "Settings & Profiles")

        self.status_lbl = QLabel("Ready. Disconnected.")
        self.statusBar().addWidget(self.status_lbl)

    def auto_calibrate_steering(self):
        if not self.is_connected:
            QMessageBox.warning(self, "Not Connected", "Please connect to the controller first.")
            return

        msg1 = QMessageBox(self)
        msg1.setWindowTitle("Auto-Calibrate 360° - Step 1 of 2")
        msg1.setText("1. Hold your steering wheel completely steady.\n2. Click OK to record the start position.")
        msg1.exec()
        start_count = self.current_raw_encoder

        msg2 = QMessageBox(self)
        msg2.setWindowTitle("Auto-Calibrate 360° - Step 2 of 2")
        msg2.setText("1. Turn your steering wheel EXACTLY one full rotation (360°) in either direction.\n2. Hold it there and click OK.")
        msg2.exec()
        end_count = self.current_raw_encoder

        delta = abs(end_count - start_count)
        if delta < 5:
            QMessageBox.warning(self, "Calibration Failed", f"No significant movement detected (only {delta} counts). Please try again.")
            return

        new_cpd = delta / 360.0
        self.steering_engine.counts_per_degree = new_cpd
        self.lbl_ratio.setText(f"{new_cpd:.4f} counts/deg")
        self.steering_engine.calibrate_centre(end_count)

        self.status_lbl.setText(f"Calibrated: {delta} counts per 360°")
        QMessageBox.information(self, "Calibration Successful", 
                                f"Hardware detected {delta} raw counts in one 360° rotation.\n\n"
                                f"New ratio set to: {new_cpd:.4f} counts/degree.\n\n"
                                "Remember to go to Settings to Save your Profile!")

    def update_max_angle(self, value):
        self.steering_engine.max_steering_angle = float(value)
        self.status_lbl.setText(f"Max Steering Angle set to ±{value}°")

    def trigger_profile_reload(self):
        self.load_active_profile()
        self.spin_max_angle.setValue(int(self.steering_engine.max_steering_angle))
        self.lbl_ratio.setText(f"{self.steering_engine.counts_per_degree:.4f} counts/deg")
        self.joystick_viz.set_regions(self.region_engine.regions, "Neutral")
        self.status_lbl.setText("Profile reloaded from disk.")

    def set_gear_region(self, gear_name: str):
        if not self.is_connected:
            self.status_lbl.setText("Cannot map gear: Controller is not connected!")
            return
            
        # Tighter radii to prevent overlapping zones between adjacent gates (e.g. 4th triggering 2nd)
        radius_x = 0.07
        radius_y = 0.09
        x_min = max(-1.0, self.current_norm_x - radius_x)
        x_max = min(1.0, self.current_norm_x + radius_x)
        y_min = max(-1.0, self.current_norm_y - radius_y)
        y_max = min(1.0, self.current_norm_y + radius_y)
        
        found = False
        for reg in self.region_engine.regions:
            if reg["name"] == gear_name:
                reg["x_min"], reg["x_max"] = x_min, x_max
                reg["y_min"], reg["y_max"] = y_min, y_max
                found = True
                break
        
        if not found:
            self.region_engine.add_region({
                "name": gear_name,
                "x_min": x_min, "x_max": x_max,
                "y_min": y_min, "y_max": y_max
            })
            
        self.joystick_viz.set_regions(self.region_engine.regions, self.region_engine.active_region)
        self.status_lbl.setText(f"{gear_name} mapped with tight bounds. REMEMBER TO SAVE PROFILE!")

    def clear_all_gears(self):
        self.region_engine.regions.clear()
        self.joystick_viz.set_regions(self.region_engine.regions, "Neutral")
        self.status_lbl.setText("All gears cleared. REMEMBER TO SAVE PROFILE!")

    def refresh_ports(self):
        self.port_combo.clear()
        ports = SerialWorker.get_available_ports()
        if ports:
            self.port_combo.addItems(ports)
        else:
            self.port_combo.addItem("No Ports Found")

    def toggle_connection(self):
        if self.is_connected:
            self.disconnect_serial()
        else:
            self.connect_serial()

    def connect_serial(self):
        port = self.port_combo.currentText()
        if not port or port == "No Ports Found": return

        self.serial_worker = SerialWorker(port=port, baudrate=115200)
        self.serial_worker.connection_status.connect(self.on_connection_status)
        self.serial_worker.packet_received.connect(self.on_packet_received)
        self.serial_worker.stats_updated.connect(self.on_serial_stats)
        self.serial_worker.start()

    def disconnect_serial(self):
        if self.serial_worker:
            self.serial_worker.stop()
            self.serial_worker = None
        self.release_all_outputs()

    def release_all_outputs(self):
        self.gamepad.release_all()
        self.keyboard.release_all()
        self.lbl_horn.setText("RELEASED")
        self.status_lbl.setText("All outputs released securely.")

    def calibrate_steering_center(self):
        try:
            current_raw = int(self.lbl_steer_raw.text())
            self.steering_engine.calibrate_centre(current_raw)
            self.status_lbl.setText(f"Steering centered at raw count: {current_raw}")
        except ValueError:
            pass

    @Slot(bool, str)
    def on_connection_status(self, connected: bool, message: str):
        self.is_connected = connected
        self.btn_connect.setText("Disconnect" if connected else "Connect")
        self.status_lbl.setText(message)
        self.port_combo.setEnabled(not connected)
        
        if not connected:
            self.joystick_viz.update_position(512, 512, 0.0, 0.0, False)
            self.release_all_outputs()

    @Slot(float, int, int)
    def on_serial_stats(self, fps: float, cs_errs: int, dropped: int):
        self.status_lbl.setText(f"Telemetry FPS: {fps:.1f} | Checksum Errors: {cs_errs} | Dropped: {dropped}")

    @Slot(dict)
    def on_packet_received(self, packet: dict):
        raw_enc = packet["encoder"]
        self.current_raw_encoder = raw_enc 
        
        phys_deg, virt_deg = self.steering_engine.process_encoder(raw_enc)
        norm_steer = self.steering_engine.get_normalized_output(virt_deg)
        
        self.lbl_steer_raw.setText(str(raw_enc))
        self.lbl_steer_phys.setText(f"{phys_deg:.1f}°")
        self.lbl_steer_virt.setText(f"{virt_deg:.1f}°")
        self.lbl_steer_norm.setText(f"{norm_steer:.3f}")

        accel_state = packet["accelerator"] == 1
        brake_state = packet["brake"] == 1
        clutch_state = packet["clutch"] == 1
        horn_state = packet["horn"] == 1

        self.bar_accel.setValue(int(accel_state))
        self.bar_brake.setValue(int(brake_state))
        self.bar_clutch.setValue(int(clutch_state))
        
        self.lbl_horn.setText("PRESSED" if horn_state else "RELEASED")
        self.lbl_horn.setStyleSheet("color: red; font-weight: bold;" if horn_state else "")

        raw_x = packet["joyX"]
        raw_y = packet["joyY"]
        slave_age = packet["slaveAgeMs"]

        self.current_norm_x = (raw_x - 512) / 512.0
        self.current_norm_y = (raw_y - 512) / 512.0
        is_hardware_live = slave_age < 100

        active_gear = self.region_engine.evaluate(self.current_norm_x, self.current_norm_y) or "Neutral"
        
        self.joystick_viz.set_regions(self.region_engine.regions, active_gear)
        self.joystick_viz.update_position(raw_x, raw_y, self.current_norm_x, self.current_norm_y, is_hardware_live)

        self.lbl_joy_data.setText(
            f"X: {raw_x} ({self.current_norm_x:+.2f}) | Y: {raw_y} ({self.current_norm_y:+.2f}) | "
            f"Gear: {active_gear} | Slave Lag: {slave_age}ms"
        )

        if self.chk_enable_output.isChecked() and is_hardware_live:
            self.gamepad.update_axes(steering_norm=norm_steer, joy_x_norm=0.0, joy_y_norm=0.0)
            self.gamepad.update_triggers(clutch_pressed=clutch_state)
            
            self.gamepad.set_button("A", accel_state)
            self.gamepad.set_button("B", brake_state)
            self.gamepad.set_button("Y", horn_state)

            # Steady-state mapping
            self.gamepad.set_button("LB", active_gear == "Gear 1")
            self.gamepad.set_button("RB", active_gear == "Gear 2")
            self.gamepad.set_button("BACK", active_gear == "Gear 3")
            self.gamepad.set_button("START", active_gear == "Gear 4")
            self.gamepad.set_button("LS", active_gear == "Gear 5")
            self.gamepad.set_button("RS", active_gear == "Gear 6")
            self.gamepad.set_button("UP", active_gear == "Reverse")
        elif not self.chk_enable_output.isChecked():
            self.gamepad.release_all()

    def closeEvent(self, event: QCloseEvent):
        self.disconnect_serial()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RacingControllerApp()
    window.show()
    sys.exit(app.exec())