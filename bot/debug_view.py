"""Live view of what the bot sees. Sends NO input - safe to run any time. ESC to close."""
import time

import cv2

from .capture import Capture
from .vision import Vision

SCALE = 0.5


def _box(img, rect, color, label=None):
    x, y, w, h = rect
    cv2.rectangle(img, (x, y), (x + w, y + h), color, 3)
    if label:
        cv2.putText(img, label, (x, max(25, y - 8)), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)


def run(cfg, base_dir):
    cap = Capture(cfg["window_title"])
    vision = Vision(cfg, base_dir)
    regions = vision.calib["regions"]
    print("Debug view running (no inputs are sent). Press ESC in the view window to close.")

    while True:
        frame = cap.grab()
        if frame is None:
            print("Waiting for the Diablo IV window...")
            time.sleep(1)
            continue

        hp = vision.hp(frame)
        meta, scores = vision.meta_state(frame)
        bars = vision.enemy_bars(frame)

        view = frame.copy()
        _box(view, regions["hp_orb"], (0, 255, 0), f"HP {hp:.0%}")
        _box(view, regions["skill_2"], (255, 255, 0), f"META {meta}")
        for b in bars:
            _box(view, b, (0, 255, 255))

        lines = [
            f"HP: {hp:.0%}",
            f"Metamorphosis: {meta}   " + "  ".join(f"{n}={s:.1f}" for n, s in scores.items()),
            f"Enemy bars: {len(bars)}  (lower score = better match)",
        ]
        for i, line in enumerate(lines):
            cv2.putText(view, line, (20, 50 + i * 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 0, 0), 6)
            cv2.putText(view, line, (20, 50 + i * 45), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

        cv2.imshow("d4bot debug", cv2.resize(view, None, fx=SCALE, fy=SCALE))
        if cv2.waitKey(100) & 0xFF == 27:
            break
    cv2.destroyAllWindows()
