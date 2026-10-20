# d4bot — Diablo IV Helltide bot (Blazing Scream Warlock)

Screen-reading bot: it looks at the game window and presses keys. It does not read game memory or inject anything.
Using a bot breaks Blizzard's Terms of Service and can get your account banned. Use it at your own risk.

**Phase 1 = combat assist.** You move the character; the bot handles skills, Metamorphosis and potions.
Movement, looting and chests come in later phases.

## Setup (once)

```bash
python -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Game settings: **Windowed, 2560x1440**. Keep the window fully visible.
Key binds: 1 = cooldown, 2 = Metamorphosis, 3 = Summon Abodian, 4 = cooldown, 5 = basic attack (unused), 6 = Blazing Scream, Q = potion.

> If hotkeys don't respond, run the terminal **as Administrator** (the `keyboard` library needs it when the game runs elevated).

## 1. Calibrate

```bash
.venv\Scripts\python.exe main.py calibrate
```

In game:
- **F5**: human form, Metamorphosis ready, **full HP**, out of combat
- **F6**: in **demon** form
- **F7** (optional): human form, Metamorphosis on **cooldown**
- **F10**: done

Then, in the window that pops up, drag a box around **skill slot 2** and press Enter. Then drag a box around the **HP orb** and press Enter.

## 2. Check what the bot sees (sends no keys)

```bash
.venv\Scripts\python.exe main.py debug
```

Check that:
- HP % follows your real HP
- `Metamorphosis:` says `ready` / `demon` / `cooldown` correctly. It should **never** say `ready` while you are a demon.

ESC closes the view.

## 3. Run

```bash
.venv\Scripts\python.exe main.py run
```

| Key | Action |
|---|---|
| F9 | start / pause |
| F8 | re-summon the tiger (after a death or teleport) |
| F12 | quit |

The bot sends nothing while Diablo IV isn't the active window. Logs are written to `logs/`.

## How the bot fights

| Priority | Action |
|---|---|
| 1 | HP < 40% → Q (at most every 2 s) |
| 2 | Press 3 once (at start and after F8) |
| 3 | Slot 2 looks **ready** → press 2, then never again for 3 s |
| 4 | Spam 6 |
| 5 | Press 1 and 4 every 0.4 s (does nothing while they're on cooldown) |

Settings are in `config.yaml`. `scream_mode: combat` makes the bot scream only when it sees enemy health bars. It's off by default because the Helltide's red tint can confuse that detection.

## Tests

```bash
.venv\Scripts\python.exe tests\test_offline.py
```

## Roadmap
- [x] Phase 1: combat, kill switch, calibration, debug view
- [ ] Route recorder (F9 while you play) and replay on the minimap
- [ ] Stuck detection
- [ ] Loot pickup (clicks every label your loot filter shows)
- [ ] Death, then respawn, then walk back
- [ ] Helltide detection, teleport, Tortured Gift chests, town trips
