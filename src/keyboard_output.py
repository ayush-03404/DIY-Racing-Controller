"""
Safe keyboard output manager.
"""

from typing import Set
from PySide6.QtCore import Qt


class KeyboardOutputManager:
    def __init__(self):
        self.active_keys: Set[int] = {}

    def press_key(self, key_code: int):
        # In actual PyQt/PySide app, use QKeyEvent or win32api/pynput
        self.active_keys.add(key_code)

    def release_key(self, key_code: int):
        if key_code in self.active_keys:
            self.active_keys.remove(key_code)

    def release_all(self):
        self.active_keys.clear()