"""Find the Diablo IV window and its client area in real screen pixels."""
import ctypes
from ctypes import wintypes

user32 = ctypes.windll.user32

# Make coordinates match physical pixels even with Windows display scaling.
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    user32.SetProcessDPIAware()


def find_window(title):
    hwnd = user32.FindWindowW(None, title)
    return hwnd or None


def is_window(hwnd):
    return bool(hwnd) and bool(user32.IsWindow(hwnd))


def client_rect(hwnd):
    """(left, top, width, height) of the client area in screen coordinates."""
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    pt = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return pt.x, pt.y, rect.right - rect.left, rect.bottom - rect.top


def is_foreground(hwnd):
    return user32.GetForegroundWindow() == hwnd
