"""
Gamepad Backend Adapter using vgamepad for Virtual Xbox 360 Controller emulation.
Includes smooth anti-stall clutch release filtering.
"""

import vgamepad as vg

class GamepadBackendAdapter:
    def __init__(self):
        try:
            self.gamepad = vg.VX360Gamepad()
        except Exception as e:
            print(f"Failed to initialize ViGEmBus driver: {e}")
            self.gamepad = None

        self.button_map = {
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
            "LB": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_SHOULDER,
            "RB": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_SHOULDER,
            "BACK": vg.XUSB_BUTTON.XUSB_GAMEPAD_BACK,
            "START": vg.XUSB_BUTTON.XUSB_GAMEPAD_START,
            "LS": vg.XUSB_BUTTON.XUSB_GAMEPAD_LEFT_THUMB,
            "RS": vg.XUSB_BUTTON.XUSB_GAMEPAD_RIGHT_THUMB,
            "UP": vg.XUSB_BUTTON.XUSB_GAMEPAD_DPAD_UP,
        }

        # Anti-stall smoothing variable for clutch
        self.current_clutch_val = 0.0

    def update_axes(self, steering_norm: float, joy_x_norm: float, joy_y_norm: float):
        if not self.gamepad: return
        steer_val = int(max(-1.0, min(1.0, steering_norm)) * 32767)
        self.gamepad.left_joystick(x_value=steer_val, y_value=0)
        self.gamepad.update()

    def update_triggers(self, clutch_pressed: bool):
        if not self.gamepad: return
        target_val = 1.0 if clutch_pressed else 0.0
        
        # Anti-stall smoothing: instant down when pressing, gradual easing up when releasing
        if target_val > self.current_clutch_val:
            self.current_clutch_val = target_val  # instant engagement
        else:
            # Step down gradually to prevent stalling (adjust 0.15 for release speed)
            self.current_clutch_val = max(target_val, self.current_clutch_val - 0.005)

        self.gamepad.left_trigger_float(self.current_clutch_val)
        self.gamepad.update()

    def set_button(self, button_name: str, pressed: bool):
        if not self.gamepad or button_name not in self.button_map: return
        btn = self.button_map[button_name]
        if pressed:
            self.gamepad.press_button(btn)
        else:
            self.gamepad.release_button(btn)
        self.gamepad.update()

    def release_all(self):
        if not self.gamepad: return
        self.gamepad.reset()
        self.current_clutch_val = 0.0
        self.gamepad.update()