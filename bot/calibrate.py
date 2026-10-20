"""One-time setup: capture reference screenshots and mark screen regions.

Step 1 (in game, hotkeys):
  F5  human form, Metamorphosis READY, full HP   (required)
  F6  in DEMON form                              (required)
  F7  human form, Metamorphosis on COOLDOWN      (optional)
  F10 done
Step 2 (OpenCV window): drag a box around skill slot 2, then the HP orb.
"""
import json
import os
import threading

import cv2
import keyboard

from .capture import Capture
from .vision import red_ratio

SHOTS = {"f5": "ready", "f6": "demon", "f7": "cooldown"}
REGIONS = [
    ("skill_2", "Drag a box tightly around skill slot 2 (Metamorphosis), then press ENTER"),
    ("hp_orb", "Drag a box around the red HP orb, then press ENTER"),
]
DISPLAY_SCALE = 0.6


def _select(img, prompt):
    small = cv2.resize(img, None, fx=DISPLAY_SCALE, fy=DISPLAY_SCALE, interpolation=cv2.INTER_AREA)
    print("  " + prompt)
    x, y, w, h = cv2.selectROI(prompt, small, showCrosshair=True)
    cv2.destroyWindow(prompt)
    if w == 0 or h == 0:
        raise SystemExit("Selection cancelled.")
    s = DISPLAY_SCALE
    return [int(x / s), int(y / s), int(w / s), int(h / s)]


def run(cfg, base_dir):
    cap = Capture(cfg["window_title"])
    shots_dir = os.path.join(base_dir, "calibration")
    os.makedirs(shots_dir, exist_ok=True)
    shots = {}
    done = threading.Event()

    def take(key):
        img = cap.grab()
        if img is None:
            print("  Diablo IV window not found!")
            return
        name = SHOTS[key]
        shots[name] = img
        cv2.imwrite(os.path.join(shots_dir, f"{name}.png"), img)
        print(f"  captured '{name}' ({img.shape[1]}x{img.shape[0]})")

    for key in SHOTS:
        keyboard.add_hotkey(key, take, args=(key,))
    keyboard.add_hotkey("f10", done.set)

    print(__doc__)
    print("Switch to Diablo IV and press the hotkeys...")
    done.wait()
    keyboard.unhook_all_hotkeys()

    for required in ("ready", "demon"):
        if required not in shots:
            raise SystemExit(f"Missing the '{required}' screenshot - run calibrate again.")

    ready = shots["ready"]
    regions = {name: _select(ready, prompt) for name, prompt in REGIONS}

    x, y, w, h = regions["hp_orb"]
    full_hp_red = red_ratio(ready[y:y + h, x:x + w])
    if full_hp_red < 0.05:
        print("  WARNING: HP orb region has almost no red - was HP full and the box on the orb?")

    x, y, w, h = regions["skill_2"]
    for name, img in shots.items():
        cv2.imwrite(os.path.join(shots_dir, f"meta_{name}.png"), img[y:y + h, x:x + w])

    calib = {
        "client_size": [ready.shape[1], ready.shape[0]],
        "regions": regions,
        "full_hp_red": full_hp_red,
        "meta_templates": {name: f"meta_{name}.png" for name in shots},
    }
    with open(os.path.join(shots_dir, "calibration.json"), "w") as f:
        json.dump(calib, f, indent=2)
    print("Calibration saved. Next: python main.py debug")
