"""
Central Mapping Engine to process controller state, apply bindings, and dispatch outputs safely.
"""

from typing import Dict, Set
from src.gamepad_backend import GamepadBackendAdapter
from src.keyboard_output import KeyboardOutputManager

class MappingEngine:
    def __init__(self, gamepad: GamepadBackendAdapter, keyboard: KeyboardOutputManager):
        self.gamepad = gamepad
        self.keyboard = keyboard
        # Example format: {"Gear 1": {"type": "gamepad", "target": "A"}, "Accelerator": {"type": "keyboard", "target": "W"}}
        self.bindings: Dict[str, Dict[str, str]] = {}
        self.active_targets: Set[tuple] = set()
        self.enabled = False

    def set_enabled(self, enabled: bool):
        """Enables or disables physical output generation."""
        self.enabled = enabled
        if not enabled:
            self.release_all()

    def update_bindings(self, new_bindings: Dict[str, Dict[str, str]]):
        """Updates the input-to-output mapping dictionary."""
        self.bindings = new_bindings
        self.release_all()

    def process_state(self, active_inputs: Set[str], steering_norm: float, joy_x: float, joy_y: float):
        """Processes a snapshot of the current controller inputs."""
        if not self.enabled:
            return
            
        # 1. Update Continuous Axes
        self.gamepad.update_axes(steering_norm, joy_x, joy_y)

        # 2. Evaluate Digital Buttons / Gears against bindings
        current_targets = set()
        for inp in active_inputs:
            if inp in self.bindings:
                target = self.bindings[inp]
                current_targets.add((target["type"], target["target"]))

        # 3. Release targets that are no longer active (prevents stuck keys)
        for t_type, t_val in self.active_targets - current_targets:
            if t_type == "gamepad":
                self.gamepad.set_button(t_val, False)
            elif t_type == "keyboard":
                self.keyboard.release_key(t_val)

        # 4. Press new targets that just became active
        for t_type, t_val in current_targets - self.active_targets:
            if t_type == "gamepad":
                self.gamepad.set_button(t_val, True)
            elif t_type == "keyboard":
                self.keyboard.press_key(t_val)

        self.active_targets = current_targets

    def release_all(self):
        """Emergency release of all currently held keys and buttons."""
        for t_type, t_val in self.active_targets:
            if t_type == "gamepad":
                self.gamepad.set_button(t_val, False)
            elif t_type == "keyboard":
                self.keyboard.release_key(t_val)
        self.active_targets.clear()
        self.gamepad.release_all()
        self.keyboard.release_all()