"""Read game state from a screenshot: HP, Metamorphosis state, enemy health bars."""
import json
import os

import cv2
import numpy as np


def red_mask(img):
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    low = cv2.inRange(hsv, (0, 120, 70), (10, 255, 255))
    high = cv2.inRange(hsv, (170, 120, 70), (180, 255, 255))
    return cv2.bitwise_or(low, high)


def red_ratio(img):
    if img.size == 0:
        return 0.0
    return float(np.count_nonzero(red_mask(img))) / (img.shape[0] * img.shape[1])


class Vision:
    def __init__(self, cfg, base_dir):
        calib_dir = os.path.join(base_dir, "calibration")
        path = os.path.join(calib_dir, "calibration.json")
        if not os.path.exists(path):
            raise SystemExit("No calibration found - run: python main.py calibrate")
        with open(path) as f:
            self.calib = json.load(f)
        self.cfg = cfg
        self.templates = {
            name: cv2.imread(os.path.join(calib_dir, fname)).astype(np.float32)
            for name, fname in self.calib["meta_templates"].items()
        }
        self._warned_size = False

    def _region(self, frame, name):
        x, y, w, h = self.calib["regions"][name]
        cw, ch = self.calib["client_size"]
        fh, fw = frame.shape[:2]
        if (fw, fh) != (cw, ch):
            if not self._warned_size:
                print(f"WARNING: window is {fw}x{fh} but calibration was {cw}x{ch} - recalibrate!")
                self._warned_size = True
            sx, sy = fw / cw, fh / ch
            x, y, w, h = int(x * sx), int(y * sy), int(w * sx), int(h * sy)
        return frame[y:y + h, x:x + w]

    def hp(self, frame):
        """HP as 0..1, estimated from the amount of red in the orb vs. full HP."""
        full = self.calib["full_hp_red"]
        if full <= 0:
            return 1.0
        return min(1.0, red_ratio(self._region(frame, "hp_orb")) / full)

    def meta_state(self, frame):
        """Return (state, scores). state is 'ready', 'demon', 'cooldown' or 'unknown'."""
        crop = self._region(frame, "skill_2").astype(np.float32)
        scores = {}
        for name, tpl in self.templates.items():
            if crop.shape != tpl.shape:
                crop_r = cv2.resize(crop, (tpl.shape[1], tpl.shape[0]))
            else:
                crop_r = crop
            scores[name] = float(np.mean(np.abs(crop_r - tpl)))
        ranked = sorted(scores, key=scores.get)
        best = ranked[0]
        margin = scores[ranked[1]] - scores[best] if len(ranked) > 1 else 999.0
        if margin < self.cfg["combat"]["meta_min_margin"]:
            return "unknown", scores
        return best, scores

    def enemy_bars(self, frame):
        """Bounding boxes of thin red horizontal bars (enemy health bars) in the play area."""
        eb = self.cfg["enemy_bars"]
        fh, fw = frame.shape[:2]
        x1, y1, x2, y2 = eb["play_area"]
        ox, oy = int(x1 * fw), int(y1 * fh)
        area = frame[oy:int(y2 * fh), ox:int(x2 * fw)]
        mask = red_mask(area)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        bars = []
        for c in contours:
            x, y, w, h = cv2.boundingRect(c)
            if (w >= eb["min_width"] and eb["min_height"] <= h <= eb["max_height"]
                    and w / h >= eb["min_aspect"]
                    and cv2.contourArea(c) >= 0.7 * w * h):   # solid bar, not a red smear
                bars.append((x + ox, y + oy, w, h))
        return bars
