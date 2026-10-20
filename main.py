"""d4bot - Diablo IV Helltide bot.

  python main.py calibrate   one-time setup (screenshots + regions)
  python main.py debug       live view of what the bot sees, sends no input
  python main.py run         combat bot (F9 start/pause, F8 re-summon, F12 quit)
"""
import argparse
import os
import time

import yaml

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def make_logger():
    os.makedirs(os.path.join(BASE_DIR, "logs"), exist_ok=True)
    path = os.path.join(BASE_DIR, "logs", time.strftime("bot_%Y%m%d_%H%M%S.log"))
    f = open(path, "a", encoding="utf-8")

    def log(msg):
        line = time.strftime("%H:%M:%S ") + msg
        print(line)
        f.write(line + "\n")
        f.flush()
    return log


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("mode", choices=["calibrate", "debug", "run"])
    args = parser.parse_args()

    with open(os.path.join(BASE_DIR, "config.yaml"), encoding="utf-8") as f:
        cfg = yaml.safe_load(f)

    if args.mode == "calibrate":
        from bot import calibrate
        calibrate.run(cfg, BASE_DIR)
    elif args.mode == "debug":
        from bot import debug_view
        debug_view.run(cfg, BASE_DIR)
    else:
        from bot.combat import CombatBot
        CombatBot(cfg, BASE_DIR, make_logger()).run()


if __name__ == "__main__":
    main()
