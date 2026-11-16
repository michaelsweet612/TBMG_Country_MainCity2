# TBMG: Country & MainCity2 — Standalone 64-Bit Source Engine Edition

**TBMG: Country & MainCity2** (`v2.3.0`) is a standalone **64-bit Source Engine** game built directly on **Source SDK Base 2013 Multiplayer** (`AppID 243750`). It runs in its own self-contained mod directory (`tbmg/`) — **neither Half-Life 2 nor Garry's Mod is required**.

---

## Table of Contents

- [Requirements](#requirements)
- [Quick Start & Installation](#quick-start--installation)
- [Maps & Play Game Selector](#maps--play-game-selector)
- [Natural Spawning Settings](#natural-spawning-settings)
- [What's New in v2.3.0](#whats-new-in-v230)
- [What's New in v2.2.0](#whats-new-in-v220)
- [Core Gameplay Features](#core-gameplay-features)
- [Controls, Tactical Binds & Console Commands](#controls-tactical-binds--console-commands)
- [Building 64-Bit Game DLLs from Source](#building-64-bit-game-dlls-from-source)
- [Repository Structure](#repository-structure)
- [Troubleshooting](#troubleshooting)

---

## Requirements

- **OS**: Windows (64-bit recommended for `hl2_win64.exe` and `tbmg/bin/x64/`; 32-bit fallback binaries remain in `tbmg/bin/`).
- **Steam + Source SDK Base 2013 Multiplayer**: Free under **Steam → Library → Tools** (`AppID 243750`). Steam must be running when launching the game.
- **No Half-Life 2 or Garry's Mod Required**: You do **not** need to own or install Half-Life 2 or Garry's Mod. Everything needed is bundled in `tbmg/` and `source_engine/` on top of the free Source SDK Base 2013 Multiplayer runtime.

---

## Quick Start & Installation

### Option A — Standalone Release Download (Recommended)

1. Install and launch **Steam**, and install the free **Source SDK Base 2013 Multiplayer** (`AppID 243750` from **Steam → Library → Tools**).
2. Download **`TBMG_Standalone_Source2013_v2.3.0.zip`** from the [Releases](https://github.com/michaelsweet612/TBMG_Country_Game_HL2/releases) page and extract the entire folder.
3. Double-click **`Play_TBMG.bat`** (or **`Play_TBMG (Needs Steam).bat`**).
   - The launcher automatically detects **Source SDK Base 2013 Multiplayer** across standard Steam library drives and the Windows Registry, prefers `hl2_win64.exe` (falling back to `hl2.exe` if unavailable), and opens `steam://install/243750` if you prompt it to install the SDK.
4. On the **Main Menu**, click **PLAY GAME** to open the **Select Map** window and pick your map.

### Option B — Clone from Git Repository

Map `.bsp` and `.nav` files are tracked with **Git LFS**, so ensure Git LFS is enabled before cloning:

```bash
git lfs install
git clone https://github.com/michaelsweet612/TBMG_Country_Game_HL2.git
cd TBMG_Country_MainCity2
git lfs pull
```

Then run **`Play_TBMG.bat`** or **`Play_TBMG (Needs Steam).bat`**.

---

## Maps & Play Game Selector

Instead of dropping straight into a map on launch, **TBMG** boots cleanly to the **Main Menu** (`tbmg/resource/gamemenu.res`). Clicking **PLAY GAME** opens the map selector dialog (`tbmg/maps/*.bns`):

| Menu Title | Map File | Description |
| :--- | :--- | :--- |
| **`MainCity2 (Big City)`** | `gm_bigcity_improved` | Large open urban sandbox city featuring a clear central spawn plaza (ammo outside the South wall), active West Civilians/Rebels vs East Metrocops gunbattles, Combine Soldiers roaming the Power Plant, full Half-Life 2 NPC cast, parked Scout Buggies, rebuilt AI node graph (`1,500` AI nodes), calibrated HDR lighting (`sky_day01_04`), and custom city soundscapes. |
| **`Flatgrass`** | `gm_flatgrass` | Open green flatgrass plain with central concrete structure and prebuilt AI node graph (`gm_flatgrass.ain`). |

> **Additional Bundled Map Variant:** `gm_bigcity_improved_rp` (`source_engine/maps/gm_bigcity_improved_rp.bsp`, paired with `.nav` and refreshed `source_engine/maps/graphs/gm_bigcity_improved_rp.ain`) is also included and trimmed under Source's `8,192` brush limit (`8,080` brushes) so it loads cleanly via developer console (`~`) with `map gm_bigcity_improved_rp`. The editable Hammer source `MainCity2.vmf` is included under `source_engine/maps/`.

---

## Natural Spawning Settings

You can toggle dynamic NPC world population directly in the in-game settings menu:

1. Open **Options → Difficulty**.
2. Locate the **Natural spawning** section near the bottom of the tab.
3. Check or uncheck **`Enable natural spawning at NPC nodes (no ammo)`**.
   - Changing the checkbox updates `tbmg_natural_spawn` immediately and saves it to `tbmg/cfg/config.cfg` via `host_writeconfig`.

### How It Works

- **Node-Based Placement**: Uses verified `NODE_GROUND` AI `info_node` points in the map's AI node graph (`g_pBigAINet`, excluding fallen or hull-blocked nodes and preferring linked graph nodes) between **`500` and `3400` units** from active players and at least **`220` units** apart from other naturally spawned NPCs.
- **Collision & Clearance Checks**: Performs padded `UTIL_TraceHull` (`MASK_NPCSOLID`) ground-snapping and post-spawn clearance verification so spawned NPCs do not clip into geometry or block walkways, and automatically cleans up tracked NPCs that fall too far out of range (`> 4800` units).
- **Zero Ammo Spawning & Full HL2 Cast**: Spawns sector-aware mobile Half-Life 2 NPCs (`npc_citizen`, `npc_metropolice`, `npc_combine_s`, `npc_vortigaunt`, `npc_zombie`, `npc_fastzombie`, `npc_poisonzombie`, `npc_headcrab`, `npc_headcrab_fast`, `npc_headcrab_black`, `npc_antlion`, `npc_manhack`, `npc_cscanner`, `npc_clawscanner`, and `npc_monk` with `weapon_shotgun`) without ever spawning `item_ammo_*`, `item_box_*`, or `item_item_crate` entities inside walls.

### Natural Spawning Console Variables & Commands

| Command / ConVar | Default | Description |
| :--- | :--- | :--- |
| `tbmg_natural_spawn` | `0` | Master toggle (`0` = off, `1` = on). Replicated & archived (`FCVAR_ARCHIVE \| FCVAR_REPLICATED`); synced with the **Options → Difficulty** checkbox. |
| `tbmg_natural_spawn_interval` | `6.0` | Seconds between natural spawn evaluation ticks. |
| `tbmg_natural_spawn_max` | `14` | Maximum concurrent naturally spawned NPCs allowed alive at once (with entity budget safety cap). |
| `tbmg_natural_spawn_status` | *(command)* | Prints current node counts, linked candidate count, active tracked NPC count, total spawned, and current entity count. |
| `tbmg_natural_spawn_clear` | *(command)* | Immediately removes all currently tracked naturally spawned NPCs. |

---

## What's New in v2.3.0

- **Full Half-Life 2 NPC Cast & Working NPC Gunfire**:
  - Compiled `npc_fastzombie.cpp` and `weapon_alyxgun.cpp` into 64-bit `server.dll`, and restored server-side NPC acttables and animation fire handlers (`Operator_HandleAnimEvent` / `FireNPCPrimaryAttack`) in `weapon_smg1.cpp`, `weapon_ar2.cpp`, `weapon_shotgun.cpp`, and `weapon_rpg.cpp` so NPCs fire weapons cleanly without missing-event warnings.
  - Forced Father Grigori (`npc_monk`) to **always** spawn armed with `weapon_shotgun`.
- **Territorial BigCity Battles & Clean Spawn Zone (`gm_bigcity_improved` / `gm_bigcity_improved_rp`)**:
  - Cleared the immediate player spawn plaza and relocated ammo crates outside the South wall away from map geometry.
  - Spread NPCs cleanly across zones for continuous combat: West Civilians/Rebels battling East Metrocops, Combine Soldiers roaming the Power Plant, plus Alyx, Barney, Dog, Father Grigori, Vortigaunts, Zombies (`zombie`, `fastzombie`, `poisonzombie`), Headcrabs, Antlions, Antlion Guard, Scanners, Manhacks, Rollermines, Floor Turrets, and birds.
  - Compacted `gm_bigcity_improved_rp.bsp` from `9,076` brushes down to `8,080` (within Source SDK 2013 MP's `8,192` brush cap) and updated `source_engine/maps/graphs/gm_bigcity_improved_rp.ain` so the RP map loads without `"Map has too many brushes"` errors.
- **No Save-on-Leave Prompts & Map-Owned NPCs**:
  - Removed singleplayer **Save Game** / **Load Game** menu buttons (`tbmg/resource/gamemenu.res`) and `bind "F9" "load quick"` (`tbmg/cfg/config.cfg`), added **LEAVE MAP (MAIN MENU)** (`DisconnectNoConfirm`), switched **Quit** to `QuitNoConfirm`, disabled `sv_autosave` (`0` default) and set `save_disable 1` (`tbmg/cfg/autoexec.cfg`), and added `CHL2MP_Player::OnRestore()` so leaving never saves or corrupts map NPCs.
- **Standard Surface Footsteps & Rebel Player Default**:
  - Delegated `CHL2MP_Player::PlayStepSound` to `BaseClass::PlayStepSound` (`player/footsteps/*.wav` surface steps instead of Combine soldier gear clanks) and changed default `cl_playermodel` / team fallback from `models/combine_soldier.mdl` to `models/humans/group03/male_07.mdl` (`TEAM_REBELS`).

---

## What's New in v2.2.0

- **Native 64-Bit Engine Binaries & Launcher (`tbmg/bin/x64/`)**:
  - Compiled `Release|win64` `client.dll` and `server.dll` directly from `ValveSoftware/source-sdk-2013` + TBMG C++ patches, resolving 32-bit `CUtlLinkedList overflow!` crashes and 64-bit `DMG_SNIPER` compilation issues.
  - Updated `Play_TBMG (Needs Steam).bat` to launch `hl2_win64.exe` automatically when present (with `hl2.exe` fallback).
- **Natural Spawning UI & Node Spawner**:
  - Added `CTBMGNaturalSpawnPanel` into the SDK Difficulty tab (`tbmg_options_bridge`) and server-side node spawner (`tbmg_natural_spawn`).
- **Map Selector & Main Menu Flow**:
  - Booting the game lands on the Main Menu with **PLAY GAME** opening the map selection dialog (`gm_bigcity_improved`, `gm_flatgrass`) instead of bypassing menus.
- **Weapon Script & HL2MP Crash Fixes**:
  - Updated `ReadEncryptedKVFile` in `weapon_parse.cpp` to fall back from `"MOD"` to `"GAME"` search paths and mounted `hl2mp/hl2mp_pak.vpk` in `tbmg/gameinfo.txt`, eliminating missing `weapon_*.txt` script errors.
  - Guarded HL2-only `CHalfLife2 *` casts on NPC death in `npc_combines.cpp` and `npc_metropolice.cpp` under `#if !defined( HL2MP )` so killing Combine Metrocops and Soldiers in 64-bit HL2MP never crashes.
  - Restricted the server HTML MOTD popup in `hl2mp_client.cpp` to dedicated servers (`engine->IsDedicatedServer()`) so local games aren't covered by a blank MOTD box on spawn.
- **Inherited Core Fixes from v2.1.x**:
  - Replaced GMod `g_sky` (`painted`) skyboxes with native `sky_day01_04` and calibrated HDR (`mat_hdr_level 2`, `mat_autoexposure_max 1.0`, `mat_bloomscale 0.12`) to fix hall-of-mirrors smearing and blown-out sun glare.
  - Restored full HL2 `tbmg/cfg/skill.cfg` ConVars (`sk_citizen_health "40"`, `sk_metropolice_health "40"`, `sk_combine_s_health "50"`, weapon damages, and ammo limits) so NPCs never spawn with `1 HP`.
  - Enabled `r_shadowrendertotexture "0"` for safe vehicle shadows, set `developer 0` / `con_notifytime 0` (keeping console output inside `~`), bundled 27 missing city ambient `.wav` files and soundscapes, and removed 619 stale GMod resource/script overrides so native SDK dialogs & closed captions work cleanly (`closecaption "0"` by default, configurable in **Options → Audio**).

---

## Core Gameplay Features

- **Full HEV Suit & Arsenal on Spawn**: Equips the HEV Suit (Health/Suit/Ammo HUD, Sprint, Flashlight, Suit Zoom) and Half-Life 2 arsenal (`Gravity Gun`, `Crowbar`, `USP Pistol`, `.357 Magnum`, `MP7 SMG1`, `AR2 Pulse Rifle`, `SPAS-12 Shotgun`, `Crossbow`, `RPG`, `Frag Grenades`, `Bugbait`).
- **Drivable Vehicles**: Drivable HL2 Scout Buggies (`ch_createjeep` / `F6`) parked in MainCity2 or spawned on demand, plus Airboats (`ch_createairboat` / `F7`).
- **Main Menu Quick Shortcuts (`tbmg/resource/gamemenu.res`)**: When paused in-game, you can jump straight to **SPAWN SCOUT BUGGY (IN-GAME)**, **FULL ARSENAL & HEV SUIT**, **DEVELOPER CONSOLE (~)**, **LEAVE MAP (MAIN MENU)**, **Options**, or **Quit** (without save-on-leave prompts).

---

## Controls, Tactical Binds & Console Commands

### Movement, Combat & Vehicles

| Key | Action | Command / Bind |
| :--- | :--- | :--- |
| **`W` `A` `S` `D`** | Move / Drive Vehicle | `+forward`, `+moveleft`, `+back`, `+moveright` |
| **`MOUSE1` / `MOUSE2`** | Primary / Secondary Fire | `+attack` / `+attack2` |
| **`1` – `7` / Scroll / `Q`** | Select Weapon Category / Cycle / Last Weapon | `slot1`–`slot7`, `invprev`/`invnext`, `lastinv` |
| **`R`** | Reload | `+reload` |
| **`SPACE`** | Jump / Vehicle Handbrake | `+jump` |
| **`SHIFT`** | Sprint / Vehicle Turbo Boost | `+speed` |
| **`CTRL` / `ALT`** | Crouch / Slow Walk | `+duck` / `+walk` |
| **`E`** | Enter/Exit Vehicle, Use Chargers & Doors | `+use` |
| **`F`** | Toggle HEV Flashlight | `impulse 100` |
| **`G`** | Quick-Swap Gravity Gun | `phys_swap` |
| **`Z`** | HEV Suit Zoom | `+zoom` |
| **`C`** | Send/Recall Citizens | `impulse 50` |
| **`~` (Tilde)** | Open Built-in Source Developer Console | `toggleconsole` |

### Built-In Sandbox & Tactical Hotkeys (`tbmg/cfg/autoexec.cfg`)

| Key | Action | Alias / Command |
| :--- | :--- | :--- |
| **`V`** | Toggle Noclip Flight | `noclip` |
| **`F1`** | Full Arsenal + HEV Suit + Health/Armor | `arsenal` (`give item_suit; impulse 101; give item_healthkit; give item_battery`) |
| **`F2`** | Spawn Combine Metrocop (SMG1) at Crosshair | `spawn_cop` |
| **`F3`** | Spawn Combine Overwatch Soldier (AR2) at Crosshair | `spawn_soldier` |
| **`F4`** | Spawn Resistance Citizen (SMG1) at Crosshair | `spawn_rebel` |
| **`F5`** | Spawn Explosive Oil Drum at Crosshair | `spawn_barrel` |
| **`F6`** | Spawn Drivable Scout Buggy | `spawn_jeep` (`ch_createjeep`) |
| **`F7`** | Spawn Drivable Airboat | `spawn_airboat` (`ch_createairboat`) |
| **`F8`** | Toggle Invincibility (Godmode) | `god` |

Additional console aliases: `spawn_monk` (Shotgun), `spawn_alyx`, `spawn_barney`, `spawn_vort`, `spawn_dog`, `spawn_zombie`, `spawn_fastzombie`, and `spawn_antlion`.

---

## Building 64-Bit Game DLLs from Source

Prebuilt binaries are already included in `tbmg/bin/x64/` (`client.dll` and `server.dll`), so end users do **not** need to compile anything to play. Developers who want to rebuild or customize the C++ code can build natively on Windows with **Visual Studio 2022 Build Tools** (with **Desktop development with C++** / `VC.Tools.x86.x64`) and Python 3:

1. Clone Valve's Source SDK 2013 repository into `sdk_src` (ignored by `.gitignore`):
   ```bash
   git clone --depth 1 --branch master https://github.com/ValveSoftware/source-sdk-2013.git sdk_src
   ```
2. Apply TBMG's C++ patches and copy `.github/scripts/sdk_files/` into `sdk_src`:
   ```bash
   python .github/scripts/patch_sdk_x64.py sdk_src
   ```
3. Generate the Visual Studio 2022 `win64` solution and compile:
   ```cmd
   cd sdk_src\src
   devtools\bin\vpc.exe /hl2mp /define:SOURCESDK /mksln tbmg_x64.sln +game
   msbuild tbmg_x64.sln /p:Configuration=Release /p:Platform=win64 /t:client_win64_hl2mp;server_win64_hl2mp /m /v:minimal
   ```
4. Copy `sdk_src\game\mod_hl2mp\bin\x64\client.dll` and `server.dll` into `tbmg\bin\x64\`.

Automated CI builds are also configured via `.github/workflows/build-x64.yml` (`workflow_dispatch`).

---

## Repository Structure

```text
TBMG_Country_MainCity2/
├── Play_TBMG.bat                      # Convenience wrapper calling Play_TBMG (Needs Steam).bat
├── Play_TBMG (Needs Steam).bat        # Steam Source SDK Base 2013 MP launcher (prefers hl2_win64.exe)
├── .github/
│   ├── scripts/
│   │   ├── patch_sdk_x64.py           # Reproducible patcher for ValveSoftware/source-sdk-2013
│   │   └── sdk_files/                 # TBMG C++ modules (tbmg_natural_spawn, tbmg_options_bridge)
│   └── workflows/
│       └── build-x64.yml              # GitHub Actions MSBuild Release|win64 workflow
├── tbmg/                              # Standalone Source Engine mod configuration & binaries
│   ├── gameinfo.txt                   # AppID 243750 search paths (mounts source_engine + hl2/hl2mp VPKs)
│   ├── steam.inf                      # Source Engine 2013 app/version metadata
│   ├── bin/                           # 32-bit fallback client.dll & server.dll
│   │   └── x64/                       # Native 64-bit Release|win64 client.dll & server.dll
│   ├── cfg/                           # autoexec.cfg, config.cfg, skill.cfg
│   ├── maps/                          # .bns map selector entries & graphs/*.ain nodegraphs
│   ├── materials/                     # Main menu backgrounds & map_thumbs previews
│   ├── resource/                      # gamemenu.res, bonusmapsdialog.res, schemes & localization
│   └── scripts/                       # bonus_maps_manifest.txt & chapterbackgrounds.txt
└── source_engine/                     # Shared maps, materials, models, sounds, and scripts
    ├── maps/                          # gm_bigcity_improved, gm_flatgrass, gm_bigcity_improved_rp (+ .nav/.ain/.vmf)
    ├── materials/                     # Skyboxes, decals, sprites, flatgrass/water & world materials
    ├── models/                        # Props, vehicles, weapons, and foliage models
    ├── scripts/                       # BigCity soundscapes & UI sound fixes
    ├── sound/                         # City ambient WAVs, vehicles, weapons, and citizen VO
    └── vgui/                          # Shared HUD/resource VGUI corner & status icons
```

---

## Troubleshooting

- **"Source SDK Base 2013 Multiplayer was not found"**: Install **Source SDK Base 2013 Multiplayer** in Steam (**Library → Tools**, `AppID 243750`). Make sure Steam is open before running `Play_TBMG (Needs Steam).bat`.
- **Map fails to load or tiny 1 KB `.bsp` files (when cloned with `git clone`)**: You have Git LFS pointer files instead of the map binaries. Install Git LFS and run `git lfs pull`, or download the prebuilt Release ZIP instead.
- **Natural spawning seems inactive or too crowded**: Check **Options → Difficulty → Natural spawning**, or open `~` console and run `tbmg_natural_spawn_status` to inspect candidate nodes (`nodes` / `candidates`), adjust `tbmg_natural_spawn_interval` / `tbmg_natural_spawn_max`, or run `tbmg_natural_spawn_clear` to despawn tracked NPCs.
