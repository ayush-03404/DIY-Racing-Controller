"""
Replaceable Virtual Gamepad backend adapter using vgamepad (Windows).
"""

import sys
class GamepadBackendAdapter:
    def __init__(self):
        self.active = False
        self.gamepad = None
        try:
            if sys.platform == "win32":
                import vgamepad as vg
                self.gamepad = vg.VX360Gamepad()
                self.active = True
        except Exception:
            self.active = False

    def update_axes(self, steering_norm: float, joy_x_norm: float, joy_y_norm: float):
        if not self.active or not self.gamepad:
            return
        # Map steering (-1.0 to 1.0) to XBOX left joystick X axis (-32768 to 32767)
        steer_val = int(steering_norm * 32767)
        self.gamepad.left_joystick(x_value=steer_val, y_value=0)
        self.gamepad.update()

    def set_button(self, button_name: str, pressed: bool):
        if not self.active or not self.gamepad:
            return
        import vgamepad as vg
        btn_map = {
            "A": vg.XUSB_BUTTON.XUSB_GAMEPAD_A,
            "B": vg.XUSB_BUTTON.XUSB_GAMEPAD_B,
            "X": vg.XUSB_BUTTON.XUSB_GAMEPAD_X,
            "Y": vg.XUSB_BUTTON.XUSB_GAMEPAD_Y,
        }
        if button_name in btn_map:
            if pressed:
                self.gamepad.press_button(btn_map[button_name])
            else:
                self.gamepad.release_button(btn_map[button_name])
            self.gamepad.update()

    def release_all(self):
        if not self.active or not self.gamepad:
            return
        self.gamepad.reset()
        self.gamepad.update()