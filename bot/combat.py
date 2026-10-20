"""Combat loop for the Blazing Scream Warlock."""
import threading
import time

import keyboard

from . import keys
from .capture import Capture
from .vision import Vision


class CombatBot:
    def __init__(self, cfg, base_dir, log):
        self.cfg = cfg
        self.k = cfg["keys"]
        self.c = cfg["combat"]
        self.log = log
        self.cap = Capture(cfg["window_title"])
        self.vision = Vision(cfg, base_dir)
        self.hold = self.c["key_hold_ms"] / 1000
        self.running = False
        self.need_summon = True
        self.stop = threading.Event()
        self.last = {}
        self.last_enemy_seen = 0.0

    # ---- hotkeys ----
    def toggle(self):
        self.running = not self.running
        self.log("RUNNING" if self.running else "PAUSED")

    def resummon(self):
        self.need_summon = True
        self.log("re-summon requested")

    def kill(self):
        self.log("KILL SWITCH")
        self.stop.set()

    # ---- helpers ----
    def _ready(self, name, interval_s, now):
        return now - self.last.get(name, 0.0) >= interval_s

    def _press(self, name, key, now):
        keys.press(key, self.hold)
        self.last[name] = now

    def tick(self, frame, now):
        c, k = self.c, self.k

        hp = self.vision.hp(frame)
        if hp < c["potion_below"] and self._ready("potion", c["potion_cooldown_s"], now):
            self._press("potion", k["potion"], now)
            self.log(f"potion (hp {hp:.0%})")

        if self.need_summon:
            self._press("summon", k["summon"], now)
            self.need_summon = False
            self.log("summoned Abodian")

        meta, _ = self.vision.meta_state(frame)
        if meta == "ready" and self._ready("meta", c["meta_lockout_s"], now):
            self._press("meta", k["metamorphosis"], now)
            self.log("metamorphosis")

        if c["scream_mode"] == "combat":
            if self.vision.enemy_bars(frame):
                self.last_enemy_seen = now
            in_fight = now - self.last_enemy_seen < c["combat_linger_s"]
        else:
            in_fight = True

        if in_fight:
            if self._ready("scream", c["scream_interval_ms"] / 1000, now):
                self._press("scream", k["scream"], now)
            for key in k["cooldowns"]:
                if self._ready("cd_" + key, c["cooldown_interval_ms"] / 1000, now):
                    self._press("cd_" + key, key, now)

    def run(self):
        hk = self.cfg["hotkeys"]
        keyboard.add_hotkey(hk["start_pause"], self.toggle)
        keyboard.add_hotkey(hk["resummon"], self.resummon)
        keyboard.add_hotkey(hk["kill"], self.kill)
        self.log(f"Ready. Focus Diablo IV, press {hk['start_pause'].upper()} to start/pause, "
                 f"{hk['resummon'].upper()} to re-summon, {hk['kill'].upper()} to quit.")

        tick_s = self.c["tick_ms"] / 1000
        was_focused = True
        try:
            while not self.stop.is_set():
                start = time.monotonic()
                focused = self.cap.is_active()
                if focused != was_focused:
                    self.log("game focused" if focused else "game not focused - holding inputs")
                    was_focused = focused
                if self.running and focused:
                    frame = self.cap.grab()
                    if frame is not None:
                        self.tick(frame, time.monotonic())
                time.sleep(max(0.0, tick_s - (time.monotonic() - start)))
        finally:
            keyboard.unhook_all_hotkeys()
            self.log("stopped")
