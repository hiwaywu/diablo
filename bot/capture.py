"""Grab the game's client area as a BGR numpy image."""
import mss
import numpy as np

from . import window


class Capture:
    def __init__(self, title):
        self.title = title
        self.hwnd = None
        self.sct = mss.mss()

    def _ensure_window(self):
        if not window.is_window(self.hwnd):
            self.hwnd = window.find_window(self.title)
        return self.hwnd

    def is_active(self):
        return self._ensure_window() is not None and window.is_foreground(self.hwnd)

    def grab(self):
        """Return the client area as BGR, or None if the window is missing/minimized."""
        if not self._ensure_window():
            return None
        left, top, width, height = window.client_rect(self.hwnd)
        if width <= 0 or height <= 0:
            return None
        shot = self.sct.grab({"left": left, "top": top, "width": width, "height": height})
        return np.ascontiguousarray(np.asarray(shot)[:, :, :3])
