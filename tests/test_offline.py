"""Offline tests with synthetic frames - no game needed, no keys sent.

Run: .venv\\Scripts\\python.exe -m pytest -q   (or python tests\\test_offline.py)
"""
import ctypes
import json
import os
import sys
import tempfile

import cv2
import numpy as np
import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from bot import combat, keys  # noqa: E402
from bot.vision import Vision  # noqa: E402

W, H = 2560, 1440
META = (1200, 1300, 80, 80)
ORB = (700, 1200, 160, 160)
COLORS = {"ready": (40, 160, 230), "demon": (60, 30, 200), "cooldown": (70, 70, 70)}


def make_frame(meta="ready", hp=1.0, bars=0):
    img = np.full((H, W, 3), 30, np.uint8)
    x, y, w, h = META
    img[y:y + h, x:x + w] = COLORS[meta]
    x, y, w, h = ORB
    filled = int(h * hp)
    img[y + h - filled:y + h, x:x + w] = (0, 0, 220)        # orb drains from the top
    for i in range(bars):
        img[400 + i * 60:408 + i * 60, 900:980] = (0, 0, 230)  # 80x8 enemy bar
    return img


def make_base_dir():
    base = tempfile.mkdtemp()
    cdir = os.path.join(base, "calibration")
    os.makedirs(cdir)
    x, y, w, h = META
    for name in COLORS:
        cv2.imwrite(os.path.join(cdir, f"meta_{name}.png"), make_frame(name)[y:y + h, x:x + w])
    from bot.vision import red_ratio
    ox, oy, ow, oh = ORB
    calib = {
        "client_size": [W, H],
        "regions": {"skill_2": list(META), "hp_orb": list(ORB)},
        "full_hp_red": red_ratio(make_frame()[oy:oy + oh, ox:ox + ow]),
        "meta_templates": {n: f"meta_{n}.png" for n in COLORS},
    }
    with open(os.path.join(cdir, "calibration.json"), "w") as f:
        json.dump(calib, f)
    return base


def load_cfg():
    with open(os.path.join(ROOT, "config.yaml")) as f:
        return yaml.safe_load(f)


def test_input_struct_size():
    assert ctypes.sizeof(keys.INPUT) == (40 if ctypes.sizeof(ctypes.c_void_p) == 8 else 28)


def test_vision():
    v = Vision(load_cfg(), make_base_dir())
    assert v.meta_state(make_frame("ready"))[0] == "ready"
    assert v.meta_state(make_frame("demon"))[0] == "demon"
    assert v.meta_state(make_frame("cooldown"))[0] == "cooldown"
    assert abs(v.hp(make_frame(hp=1.0)) - 1.0) < 0.02
    assert abs(v.hp(make_frame(hp=0.3)) - 0.3) < 0.03
    assert len(v.enemy_bars(make_frame(bars=3))) == 3
    assert len(v.enemy_bars(make_frame(bars=0))) == 0
    # scaled window still works
    small = cv2.resize(make_frame("demon"), (1920, 1080))
    assert v.meta_state(small)[0] == "demon"


def run_ticks(bot, frames):
    pressed = []
    keys.press = lambda key, hold_s=0.03: pressed.append(key)
    t = 100.0
    for frame in frames:
        bot.tick(frame, t)
        t += 0.05
    return pressed


def make_bot(**combat_overrides):
    cfg = load_cfg()
    cfg["combat"].update(combat_overrides)
    bot = combat.CombatBot.__new__(combat.CombatBot)
    bot.cfg, bot.k, bot.c = cfg, cfg["keys"], cfg["combat"]
    bot.log = lambda m: None
    bot.vision = Vision(cfg, make_base_dir())
    bot.hold, bot.need_summon, bot.last, bot.last_enemy_seen = 0, True, {}, 0.0
    return bot


def test_combat_never_presses_2_in_demon_form():
    pressed = run_ticks(make_bot(), [make_frame("demon")] * 200)
    assert "2" not in pressed
    assert pressed.count("3") == 1          # summon exactly once
    assert pressed.count("6") >= 40         # scream spammed (~every 150-200ms over 10s)
    assert "1" in pressed and "4" in pressed
    assert "5" not in pressed               # basic attack never used


def test_combat_meta_pressed_once_then_locked_out():
    # screen still shows "ready" for a bit after pressing (lag) - must not double-tap
    pressed = run_ticks(make_bot(), [make_frame("ready")] * 40)   # 2 seconds
    assert pressed.count("2") == 1


def test_potion_on_low_hp():
    pressed = run_ticks(make_bot(), [make_frame("demon", hp=0.25)] * 20)
    assert pressed.count("q") == 1          # 2s potion cooldown
    pressed = run_ticks(make_bot(), [make_frame("demon", hp=0.9)] * 20)
    assert "q" not in pressed


def test_combat_mode_only_screams_with_enemies():
    bot = make_bot(scream_mode="combat")
    pressed = run_ticks(bot, [make_frame("demon", bars=0)] * 40)
    assert "6" not in pressed
    pressed = run_ticks(bot, [make_frame("demon", bars=2)] * 40)
    assert "6" in pressed


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("PASS", name)
