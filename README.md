TBMG_Country_Game_HL2 — Standalone Source Engine Edition

**TBMG: Country & MainCity2** is a standalone **Source Engine** game built on **Source SDK Base 2013 Multiplayer** (`AppID 243750`). It runs directly on Valve's Source Engine with its own standalone mod directory (`tbmg/`) and does **not** require Garry's Mod or any legacy Python/WebGL wrapper.

---

## Quick Start

1. Make sure **Steam** is running and **Source SDK Base 2013 Multiplayer** (free in Steam Tools, AppID `243750`) is installed.
2. Double-click **`Play_TBMG.bat`** (or **`Play_TBMG (Needs Steam).bat`**).
3. The game launches directly into **`gm_bigcity_improved`** (**MainCity2**) with full HEV Suit HUD, weapons, soundscapes, and patrolling Combine/Rebel NPCs.

---

## Included Features & What's New in v2.2.0

- **Pure Standalone Source Engine Game (`tbmg/`)**:
  - Removed the legacy Python/Pygame/WebGL prototype and removed all Garry's Mod dependencies.
  - Native 32-bit Source SDK 2013 `client.dll` and `server.dll` in `tbmg/bin/`.
- **Fixed Skybox & HDR Sun Rendering**:
  - Replaced unsupported GMod `g_sky` (`painted`) skybox shaders in `gm_bigcity_improved.bsp` with native Source Engine `sky_day01_04` skyboxes, eliminating the Hall-of-Mirrors building edge smearing and the additive `env_sun` sky whiteout ("nuke sun") bug.
  - Calibrated HDR `TonemapController` (`AutoExposureMax 1.0`, `BloomScale 0.12`) and `env_sun` overlay scale for natural lighting.
- **Full Audio, City Soundscapes & Clean SDK UI**:
  - Added all 27 missing city ambient `.wav` sound files (dogs, traffic, car horns, sirens, garbage trucks, helicopters, distant trains, and Episode 1 citizen voice lines), registered `soundscapes_gm_bigcity_improved.txt` in `soundscapes_manifest.txt`, and fixed missing UI sounds (`wpn_select.wav` & `Hud.Hint`) in `game_sounds_ui.txt`.
  - Bundled all missing decals, sprites (`sprites/glow`, `effects/huntertracer`), and foliage models (`models/props/cs_militia/trees*`).
  - Removed 619 stale/duplicate GMod `source_engine/resource/` and `source_engine/scripts/` overrides so Source SDK 2013's native UI, options dialogs, closed-caption settings, and localization load cleanly, and set `closecaption "0"` by default (toggleable in Options → Audio).
- **Fixed NPC Health (`1 HP` Bug) & Vehicles**:
  - Restored full Half-Life 2 `tbmg/cfg/skill.cfg` ConVars (`sk_citizen_health "40"`, `sk_metropolice_health "40"`, `sk_combine_s_health "50"`, weapon damage, and ammo caps) so NPCs no longer default to `1 HP`.
  - **Full HEV Suit & Arsenal on Spawn**: Every spawn point automatically equips the **HEV Suit** (Health/Suit/Ammo HUD, `SHIFT` Sprint, `F` Flashlight, `Z` Zoom) and full Half-Life 2 weapon loadout (`Gravity Gun`, `Crowbar`, `USP Pistol`, `.357 Magnum`, `MP7 SMG1`, `AR2 Pulse Rifle`, `SPAS-12 Shotgun`, `Crossbow`, `RPG`, `Frag Grenades`, `Bugbait`).
  - **Active City AI & Fixed AI Node Graph**: Trimmed excess `info_node` count to `1,400` (within Source Engine's `1,500` node limit) and populated the streets with **Combine Civil Protection Metrocops**, **Combine Overwatch Soldiers**, **City Scanners**, **Resistance Rebels**, and **Ammo Crates**.
- **Clean HUD & Built-in Developer Console (`~`)**:
  - Configured `developer 0` and `con_notifytime 0` in `tbmg/cfg/autoexec.cfg` so debug/console messages never clutter the top-left corner of the screen and stay strictly inside the built-in Source Engine Developer Console (`~`).

---

> **Vehicles & NPC Health Fixed:** Drivable Scout Buggies (`F6`) and Airboats (`F7`) are restored with `r_shadowrendertotexture "0"` (preventing the `CUtlLinkedList overflow!` shadow decal crash), and `tbmg/cfg/skill.cfg` restores full Half-Life 2 NPC health & weapon damage values.

## Controls & Built-in Tactical Binds

| Key | Action | Console Command / Alias |
| :--- | :--- | :--- |
| **`W` `A` `S` `D`** | Move / Drive Vehicle | `+forward`, `+moveleft`, `+back`, `+moveright` |
| **`SPACE`** | Jump / Vehicle Handbrake | `+jump` |
| **`SHIFT`** | Sprint / Vehicle Turbo Boost | `+speed` |
| **`E`** | Enter / Exit Vehicle, Use Chargers & Doors | `+use` |
| **`F`** | Toggle HEV Flashlight | `impulse 100` |
| **`G`** | Quick-Swap Gravity Gun | `phys_swap` |
| **`Z`** | HEV Suit Zoom | `+zoom` |
| **`V`** | Toggle Noclip Flight | `noclip` |
| **`~` (Tilde)** | Open Built-in Source Developer Console | `toggleconsole` |
| **`F1`** | Give Full Arsenal + HEV Suit + Heal | `arsenal` (`impulse 101`) |
| **`F2`** | Spawn Combine Metrocop at Crosshair | `spawn_cop` |
| **`F3`** | Spawn Combine Overwatch Soldier at Crosshair | `spawn_soldier` |
| **`F4`** | Spawn Resistance Rebel at Crosshair | `spawn_rebel` |
| **`F5`** | Spawn Explosive Oil Drum at Crosshair | `spawn_barrel` |
| **`F6`** | Spawn Drivable Scout Buggy | `spawn_jeep` |
| **`F7`** | Spawn Drivable Airboat | `spawn_airboat` |
| **`F8`** | Toggle Invincibility (Godmode) | `god` |

---

## Repository Structure

```text
TBMG_Country_MainCity2/
├── Play_TBMG.bat                  # Main launcher for Source SDK Base 2013 Multiplayer
├── Play_TBMG (Needs Steam).bat    # Steam Source SDK Base 2013 Multiplayer launcher
├── tbmg/                          # Standalone Source Engine Mod configuration & binaries
│   ├── gameinfo.txt               # Standalone AppID 243750 search paths & metadata
│   ├── steam.inf                  # Source Engine 2013 version descriptor
│   ├── bin/                       # 32-bit Source SDK 2013 client.dll & server.dll
│   ├── cfg/                       # autoexec.cfg, config.cfg, skill.cfg
│   └── resource/                  # Custom main menu (gamemenu.res) & localization
└── source_engine/                 # Shared maps, materials, models, sounds, and scripts
    ├── maps/                      # gm_bigcity_improved.bsp (MainCity2)
    ├── materials/                 # Skyboxes, decals, sprites, and world materials
    ├── models/                    # Props, vehicles, weapons, and foliage models
    ├── scripts/                   # Custom BigCity soundscapes & UI sound fixes
    └── sound/                     # Ambient city sounds, vehicles, weapons, and VO
```
