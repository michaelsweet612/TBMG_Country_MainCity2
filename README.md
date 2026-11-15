# TBMG_Country_MainCity2 — 2007 Warfare Edition (Call of Duty × Half-Life 2)

A hardware-accelerated **2007-Era First-Person Warfare & DarkRP** action game set in the devastated WWII × City-17 battlefield of **MainCity2**. Combines *Call of Duty*-style animated first-person weapon handling, `SHIFT + W` tactical sprinting, and Iron Sights (ADS) with *Half-Life 2*'s iconic amber HEV HUD, multi-textured European masonry buildings, and WWII street fortifications in both **Desktop OpenGL** ([`game.py`](file:///c:/Users/Michael/Downloads/Antigravity/TBMG_Country_MainCity2/game.py)) and **Browser WebGL / Three.js** ([`index.html`](file:///c:/Users/Michael/Downloads/Antigravity/TBMG_Country_MainCity2/index.html)).

---

## Major 2007 Warfare Upgrades

1. **Primary First-Person Gameplay with Animated 3D Viewmodels**
   - Starts by default in **First-Person (`1ST-PERSON (COD/HL2)`)** with `[V]` available to toggle into 3rd-Person Tactical or Wide views at any time.
   - **3D HEV / Spec-Ops Hands & Arms**: Articulated 3D forearms with dark grey armored sleeves, amber HEV wrist trim, and gloved hands gripping each weapon in 3D space.
   - **Procedural Weapon Animations**: Breathing idle sway, figure-8 walking bob, `SHIFT + W` diagonal cross-chest sprint posture, `RMB` centered Iron Sights (ADS), snappy recoil kickback with barrel climb, and physical 3D brass shell casings ejecting from the receiver.

2. **`SHIFT + W` Tactical Sprint & Half-Life 2 `AUX POWER`**
   - Holding **`SHIFT`** while pushing **`W`** initiates a high-speed tactical sprint (`1.68x` movement speed), dynamic FOV surge, heavy footstep cadence, and a *Call of Duty* cross-chest weapon sprint animation.
   - Drains the Half-Life 2 **`AUX POWER`** stamina bar (`0`–`100`), which glows amber when active, turns red when critically low, and recharges automatically when walking or standing still.

3. **Authentic Half-Life 2 HEV Suit HUD**
   - Translucent dark rounded HUD boxes (`rgba(15, 12, 8, 0.68)`) with glowing amber (`#FFB000`) typography:
     - **Bottom-Left**: `HEALTH` and `SUIT` readouts + dynamic `AUX POWER · SPRINT` bar.
     - **Bottom-Right**: `AMMO` primary clip, reserve pool, and secondary tactical charges.
     - **Top-Center**: Classic Half-Life 2 `1`–`7` weapon bucket selector bar that expands when switching weapons.
     - **Center Screen**: 5-dot Half-Life 2 amber bracket reticle that tightens or hides during `RMB` Iron Sights (ADS), paired with directional red blood-splatter damage arcs.

4. **Authentic Half-Life 2 Assets & 3 Reference Screenshot Scenes**
   - **Genuine Half-Life 2 Textures & Audio**: Extracted directly from the local Steam Half-Life 2 installation into `./assets/hl2/textures/*.png` and `./assets/hl2/sounds/*.wav` via `extract_hl2_assets.py`.
   - **Screenshot 1 Recreated (Tenement Corridor & Metrocop Raid)**: Green-grey painted brick walls plastered with peeling Cyrillic posters, indoor ceiling slab, overhead steel I-beam trusses with diagonal knee braces, Crowbar viewmodel, and two Combine Civil Protection Metrocops facing the player with glowing blue electric Stunsticks.
   - **Screenshot 2 Recreated (Point Insertion Checkpoint)**: See-through galvanized chain-link security fence (`metalfence004a` with hardware alpha testing), angled 3-strand barbed-wire tops, green-optic Combine security camera, beige diamond-inlaid terrazzo floor (`tilefloor011a`), and giant cyan Dr. Wallace Breen propaganda screen (`breencast_screen.png`).
   - **Screenshot 3 Recreated (City-17 European Street Plaza & "Terminal")**: European facades (`building_template011g`, `011c`, `005b`, `002b`), yellow neoclassical building with steep dark-slate conical turret spire and finial needle, corrugated rusty metal shopfront awnings with red `"Teräs"` and blue `"Café"` signs, red 3D `"TERMINAL"` rooftop sign, overhead criss-crossing tram catenary cables against pale overcast sky, and Citizens lined up with hands against the wall + prone on the sidewalk with a Metrocop standing over them.

---

## How to Launch

Choose between the two launchers depending on whether you want to use Steam's Source Engine or the standalone desktop engine:

1. **👉 [`Play_TBMG (Needs Steam).bat`](file:///c:/Users/Michael/Downloads/Antigravity/TBMG_Country_MainCity2/Play_TBMG%20(Needs%20Steam).bat)**:
   - Launches **TBMG: Country & MainCity2** as its own standalone **Source Engine** game powered by **Source SDK Base 2013 Multiplayer** (free on Steam, AppID `243750` — no Garry's Mod required!).
   - Uses the included [`tbmg/`](file:///c:/Users/Michael/Downloads/Antigravity/TBMG_Country_MainCity2/tbmg) mod directory (`gameinfo.txt`, `bin/client.dll`, `bin/server.dll`, `cfg/`, `resource/gamemenu.res`) and [`source_engine/`](file:///c:/Users/Michael/Downloads/Antigravity/TBMG_Country_MainCity2/source_engine) maps/assets to boot directly into **MainCity2** (`gm_bigcity_improved`) and **BigCity Roleplay** (`gm_bigcity_improved_rp`).

2. **👉 [`Play_TBMG (No Steam Needed).bat`](file:///c:/Users/Michael/Downloads/Antigravity/TBMG_Country_MainCity2/Play_TBMG%20(No%20Steam%20Needed).bat)**:
   - 100% standalone desktop 3D game — **No Steam required**.
   - Runs the hardware-accelerated 2007 Warfare 3D game with tactical sprinting, amber HEV HUD, drivable vehicles, and custom maps. Fallback to WebGL in browser if needed.

---

## Controls

| Key / Input | Action |
|---|---|
| `W` `A` `S` `D` | First-Person Operator Movement |
| `SHIFT + W` | Tactical Sprint (COD Cross-Chest Lower + HL2 `AUX POWER`) |
| `SPACE` | Jump |
| `Mouse` | First-Person Look & Aim |
| `Left Click (LMB)` | Fire Equipped Warfare Weapon |
| `Right Click (RMB)` | Iron Sights (ADS) Centering & Zoom |
| `V` | Cycle Camera (`1st-Person COD/HL2` / `3rd-Person Tactical` / `3rd-Person Wide`) |
| `1` – `7` / `Mouse Wheel` | Switch Weapons (HL2 Top Weapon Bucket Selector) |
| `E` | Open Nearby 3D Security Door |
| `TAB` | Toggle Tactical Satellite Automap |
| `F1` | Open President Michael's Executive Admin Terminal |
| `ESC` | Pause / Title Screen |
