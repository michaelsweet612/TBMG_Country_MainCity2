#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  TBMG_Country_MainCity2 — 3D THIRD-PERSON WARFARE EDITION        ║
║  True 3D OpenGL Engine · Over-The-Shoulder Tactical Camera       ║
║  Articulated 3D Character Rigs · 3D City & Vehicles · DarkRP     ║
║  7 Weapons · A* Tactical AI · Doors · Pickups · Automap          ║
║  Build 7000 | 3D Hardware Accelerated | Instability: HELLISH     ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pygame
import math
import random
import sys
import os
import json
import array
import time
import heapq
import subprocess
import atexit
import struct
import io
import numpy as np
import ctypes
from ctypes import c_int, c_uint, c_float, c_void_p, POINTER, byref

try:
    from live_log_terminal import (
        enable_windows_ansi_and_utf8,
        format_colored_log_line,
        LIVE_LOG_FILE,
    )
except Exception:
    LIVE_LOG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "live_game_log.log")

    def enable_windows_ansi_and_utf8():
        pass

    def format_colored_log_line(level, msg, sim_time=0.0):
        return f"[{sim_time:06.1f}s] [{level.upper()}] {msg}"


def print_colorful_launcher_banner():
    """Prints a rich ANSI-colored + emoji Half-Life 2 / Source Engine launcher banner to the terminal."""
    enable_windows_ansi_and_utf8()
    RST = "\033[0m"
    BOLD = "\033[1m"
    ORG = "\033[38;5;208m"
    AMB = "\033[38;5;214m"
    CYN = "\033[38;5;51m"
    GRN = "\033[38;5;82m"
    YEL = "\033[38;5;226m"
    MAG = "\033[38;5;201m"
    RED = "\033[38;5;196m"
    WHT = "\033[97m"
    DIM = "\033[38;5;245m"

    banner = f"""
{ORG}{BOLD}╔══════════════════════════════════════════════════════════════════════════════╗{RST}
{ORG}{BOLD}║{RST}  λ {AMB}{BOLD}TBMG_Country_MainCity2 — HALF-LIFE 2 × SOURCE ENGINE 3D EDITION{RST}  🎮🔫🌊   {ORG}{BOLD}║{RST}
{ORG}{BOLD}║{RST}  {CYN}⚡ Hardware OpenGL 3D Engine{RST} · {GRN}🔫 Genuine HL2 3D Weapons{RST} · {MAG}🛠️ Map Editor{RST}    {ORG}{BOLD}║{RST}
{ORG}{BOLD}║{RST}  {YEL}🚓 540+ Combine Radio Voice Lines{RST} · {CYN}🌊 VPhysics Water{RST} · {AMB}📡 Live Log Window{RST}  {ORG}{BOLD}║{RST}
{ORG}{BOLD}╚══════════════════════════════════════════════════════════════════════════════╝{RST}

  {AMB}{BOLD}🎮 TACTICAL CONTROLS & SOURCE ENGINE KEYBINDS:{RST}
  {DIM}──────────────────────────────────────────────────────────────────────────────{RST}
   🏃 {GRN}{BOLD}WASD{RST}            {WHT}Move / Strafe{RST}          ⚡ {GRN}{BOLD}W + LSHIFT{RST}    {WHT}HEV Tactical Sprint{RST}
   🎯 {CYN}{BOLD}Mouse + LMB{RST}     {WHT}Aim & Fire HL2 Weapon{RST}  🔭 {CYN}{BOLD}RMB (Hold){RST}    {WHT}Iron Sights (ADS){RST}
   🔄 {YEL}{BOLD}R{RST}               {WHT}Tactical Reload{RST}        🔫 {YEL}{BOLD}1-7 / Wheel{RST}   {WHT}HL2 Weapon Arsenal{RST}
   🖐️ {ORG}{BOLD}G{RST}               {WHT}Punt VPhysics Prop{RST}     🚪 {ORG}{BOLD}E / SPACE{RST}     {WHT}Open Door / Swim Up{RST}
   📷 {MAG}{BOLD}V{RST}               {WHT}1st / 3rd Person Cam{RST}   🗺️ {MAG}{BOLD}TAB{RST}           {WHT}Tactical Automap{RST}
   🛠️ {CYN}{BOLD}F2{RST}              {WHT}HL2 Hammer Map Editor{RST}  💾 {GRN}{BOLD}F5 / F7{RST}       {WHT}Save / Reset Map{RST}
   👑 {RED}{BOLD}F1{RST}              {WHT}Executive Admin Menu{RST}   ⚙️ {AMB}{BOLD}ESC{RST}           {WHT}Pause & Graphics Menu{RST}
  {DIM}──────────────────────────────────────────────────────────────────────────────{RST}
"""
    try:
        print(banner, flush=True)
    except Exception:
        pass


# ═══════════════════════════════════════════════════════════════════════════
#  NATIVE C / C++ SOURCE ENGINE BRIDGE (HL2 & GARRY'S MOD DLLs + .RES PARSER)
# ═══════════════════════════════════════════════════════════════════════════
class SourceEngineBridge:
    """
    Loads genuine 64-bit Valve Source Engine C++ binaries (tier0.dll, vstdlib.dll,
    vphysics.dll, filesystem_stdio.dll, vgui2.dll) via Python ctypes and parses
    authentic Half-Life 2 KeyValues scripts (gamemenu.res, hudlayout.res, clientscheme.res).
    """
    WEAPON_ICON_GLYPHS = {
        0: 'c',  # Crowbar
        1: 'd',  # 9mm USP Match Pistol
        2: 'a',  # MP7 SMG1
        3: 'b',  # SPAS-12 Pump Shotgun
        4: 'l',  # Overwatch Pulse Rifle (AR2)
        5: 'e',  # .357 Colt Python Magnum
        6: 'i',  # RPG-7 Laser Guided Launcher
    }

    def __init__(self, root_dir):
        self.root_dir = root_dir
        self.se_dir = os.path.join(root_dir, "source_engine")
        self.bin_dir = os.path.join(self.se_dir, "bin")
        self.res_dir = os.path.join(self.se_dir, "resource")
        self.scr_dir = os.path.join(self.se_dir, "scripts")
        self.mat_dir = os.path.join(self.se_dir, "materials")

        self.tier0 = None
        self.vstdlib = None
        self.vphysics = None
        self.filesystem = None
        self.vgui2 = None

        self.interfaces = {}
        self.gamemenu_items = []
        self.hud_layout = {}
        self.vmt_materials = {}
        self.prop_data = {}
        self.surface_properties = {}
        self.vehicle_scripts = {}
        self.vpk_packs = []
        self.scheme_colors = {
            "Orange": (255, 176, 0, 255),
            "OrangeDim": (255, 176, 0, 120),
            "Red": (255, 48, 32, 255),
        }

        self._load_native_dlls()
        self._parse_source_res_files()
        self._parse_source_vmt_materials()
        self._parse_source_scripts_and_vpks()

    def _load_native_dlls(self):
        if not os.path.isdir(self.bin_dir):
            return
        try:
            if hasattr(os, "add_dll_directory"):
                os.add_dll_directory(self.bin_dir)
            os.environ["PATH"] = self.bin_dir + os.pathsep + os.environ.get("PATH", "")

            t0_path = os.path.join(self.bin_dir, "tier0.dll")
            vs_path = os.path.join(self.bin_dir, "vstdlib.dll")
            vp_path = os.path.join(self.bin_dir, "vphysics.dll")
            fs_path = os.path.join(self.bin_dir, "filesystem_stdio.dll")
            vg_path = os.path.join(self.bin_dir, "vgui2.dll")

            if os.path.exists(t0_path):
                self.tier0 = ctypes.CDLL(t0_path)
                if hasattr(self.tier0, "Plat_FloatTime"):
                    self.tier0.Plat_FloatTime.restype = ctypes.c_double
                    self.interfaces["tier0::Plat_FloatTime"] = hex(ctypes.cast(self.tier0.Plat_FloatTime, ctypes.c_void_p).value or 0)

            if os.path.exists(vs_path):
                self.vstdlib = ctypes.CDLL(vs_path)
                if hasattr(self.vstdlib, "RandomSeed") and hasattr(self.vstdlib, "RandomFloat"):
                    self.vstdlib.RandomSeed.argtypes = [ctypes.c_int]
                    self.vstdlib.RandomFloat.argtypes = [ctypes.c_float, ctypes.c_float]
                    self.vstdlib.RandomFloat.restype = ctypes.c_float
                    self.vstdlib.RandomSeed(1337)
                    self.interfaces["vstdlib::RandomFloat"] = hex(ctypes.cast(self.vstdlib.RandomFloat, ctypes.c_void_p).value or 0)

            for dll_attr, dll_path, iface_candidates, key_name in (
                ("vphysics", vp_path, [b"VPhysics031", b"VPhysics030"], "VPhysics031"),
                ("filesystem", fs_path, [b"VFileSystem022", b"VFileSystem021", b"VFileSystem017", b"VBaseFileSystem011"], "VFileSystem022"),
                ("vgui2", vg_path, [b"VGUI_Panel009", b"VGUI_Panel010", b"VGUI_Surface030"], "VGUI_Panel009"),
            ):
                if os.path.exists(dll_path):
                    dll_obj = ctypes.CDLL(dll_path)
                    setattr(self, dll_attr, dll_obj)
                    if hasattr(dll_obj, "CreateInterface"):
                        create_fn = dll_obj.CreateInterface
                        create_fn.argtypes = [ctypes.c_char_p, ctypes.POINTER(ctypes.c_int)]
                        create_fn.restype = ctypes.c_void_p
                        ret_code = ctypes.c_int(0)
                        found_ptr = None
                        for cand in iface_candidates:
                            ptr = create_fn(cand, ctypes.byref(ret_code))
                            if ptr:
                                found_ptr = ptr
                                break
                        if not found_ptr:
                            found_ptr = ctypes.cast(create_fn, ctypes.c_void_p).value or 0
                        self.interfaces[key_name] = f"0x{found_ptr:016X}"
        except Exception:
            pass

    def plat_float_time(self):
        if self.tier0 and hasattr(self.tier0, "Plat_FloatTime"):
            try:
                return float(self.tier0.Plat_FloatTime())
            except Exception:
                pass
        return time.perf_counter()

    def random_float(self, low=0.0, high=1.0):
        if self.vstdlib and hasattr(self.vstdlib, "RandomFloat"):
            try:
                return float(self.vstdlib.RandomFloat(float(low), float(high)))
            except Exception:
                pass
        return random.uniform(low, high)

    def _parse_source_res_files(self):
        import re
        gm_path = os.path.join(self.res_dir, "gamemenu.res")
        if os.path.exists(gm_path):
            try:
                with open(gm_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                for m in re.finditer(r'"(\d+)"\s*\{([^}]+)\}', raw):
                    block = m.group(2)
                    lbl_m = re.search(r'"label"\s+"([^"]+)"', block)
                    cmd_m = re.search(r'"command"\s+"([^"]+)"', block)
                    if lbl_m and cmd_m:
                        self.gamemenu_items.append((lbl_m.group(1), cmd_m.group(1)))
            except Exception:
                pass

        hl_path = os.path.join(self.scr_dir, "hudlayout.res")
        if os.path.exists(hl_path):
            try:
                with open(hl_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                for sec in ("HUDQuickInfo", "HudHealth", "HudSuit", "HudAmmo", "HudWeaponSelection", "CHudDamageIndicator"):
                    m = re.search(rf'\b{sec}\b\s*\{{([^}}]+)\}}', raw)
                    if m:
                        props = {}
                        for kv in re.finditer(r'"([^"]+)"\s+"([^"]+)"', m.group(1)):
                            props[kv.group(1)] = kv.group(2)
                        self.hud_layout[sec] = props
            except Exception:
                pass

    def _parse_source_vmt_materials(self):
        """Parses genuine Valve Material Type (.vmt) shader scripts from source_engine/materials/."""
        if not os.path.isdir(self.mat_dir):
            return
        import re
        try:
            for fname in os.listdir(self.mat_dir):
                if not fname.lower().endswith(".vmt"):
                    continue
                fpath = os.path.join(self.mat_dir, fname)
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                shader_m = re.match(r'\s*"?([A-Za-z0-9_]+)"?', raw)
                shader_name = shader_m.group(1) if shader_m else "VertexLitGeneric"
                mat_props = {"shader": shader_name}
                for kv in re.finditer(r'"(\$[A-Za-z0-9_]+)"\s+"([^"]+)"', raw):
                    mat_props[kv.group(1).lower()] = kv.group(2)
                self.vmt_materials[os.path.splitext(fname)[0]] = mat_props
        except Exception:
            pass

    def _parse_source_scripts_and_vpks(self):
        """Parses propdata.txt, surfaceproperties_hl2.txt, scripts/vehicles/*.txt, and indexes VPK packs in source_engine/."""
        import re
        # 1. Parse propdata.txt (Breakable & VPhysics Prop Classes)
        pd_path = os.path.join(self.scr_dir, "propdata.txt")
        if os.path.exists(pd_path):
            try:
                with open(pd_path, "r", encoding="utf-8", errors="ignore") as f:
                    raw = f.read()
                for m in re.finditer(r'"([A-Za-z0-9_.]+)"\s*\{([^}]+)\}', raw):
                    cls_name = m.group(1)
                    if cls_name.lower() == "propdata.txt":
                        continue
                    props = {}
                    for kv in re.finditer(r'"([^"]+)"\s+"([^"]+)"', m.group(2)):
                        props[kv.group(1)] = kv.group(2)
                    self.prop_data[cls_name] = props
            except Exception:
                pass

        # 2. Parse surfaceproperties.txt & surfaceproperties_hl2.txt
        for sp_file in ("surfaceproperties.txt", "surfaceproperties_hl2.txt"):
            sp_path = os.path.join(self.scr_dir, sp_file)
            if os.path.exists(sp_path):
                try:
                    with open(sp_path, "r", encoding="utf-8", errors="ignore") as f:
                        raw = f.read()
                    for m in re.finditer(r'"([A-Za-z0-9_]+)"\s*\{([^}]+)\}', raw):
                        props = {}
                        for kv in re.finditer(r'"([^"]+)"\s+"([^"]+)"', m.group(2)):
                            props[kv.group(1)] = kv.group(2)
                        self.surface_properties[m.group(1).lower()] = props
                except Exception:
                    pass

        # 3. Parse scripts/vehicles/*.txt (jeep_test.txt, apc.txt, airboat.txt, etc.)
        veh_dir = os.path.join(self.scr_dir, "vehicles")
        if os.path.isdir(veh_dir):
            try:
                for fn in os.listdir(veh_dir):
                    if fn.lower().endswith(".txt"):
                        vpath = os.path.join(veh_dir, fn)
                        with open(vpath, "r", encoding="utf-8", errors="ignore") as f:
                            vraw = f.read()
                        vprops = {}
                        for kv in re.finditer(r'"(horsepower|maxrpm|maxspeed|maxReverseSpeed|axleratio|massoverride)"\s+"([^"]+)"', vraw):
                            vprops[kv.group(1)] = kv.group(2)
                        self.vehicle_scripts[os.path.splitext(fn)[0]] = vprops
            except Exception:
                pass

        # 4. Discover VPK archives in source_engine/ and source_engine/sourceengine - Copy/
        for cand_dir in (self.se_dir, os.path.join(self.se_dir, "sourceengine - Copy")):
            if os.path.isdir(cand_dir):
                try:
                    for fn in sorted(os.listdir(cand_dir)):
                        if fn.lower().endswith("_dir.vpk") and fn not in self.vpk_packs:
                            self.vpk_packs.append(fn)
                except Exception:
                    pass



# ═══════════════════════════════════════════════════
#  PERSISTENT USER SETTINGS SYSTEM (Auto-Default: "Standard User")
# ═══════════════════════════════════════════════════
GRAPHICS_PRESETS = [
    "Potato PC Graphics",
    "Standard User",
    "Alter Heavy Graphics",
]

DEFAULT_USER_SETTINGS = {
    "graphics_preset": "Standard User",
    "fog_enabled": True,
    "fog_distance": 46.0,
    "max_bullet_decals": 500,
    "selected_map": "MainCity2",
}

SETTINGS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_settings.json")


def load_user_settings():
    """
    Loads persistent settings from user_settings.json.
    On a new install or new device where the file does not exist, automatically defaults
    to 'Standard User' graphics preset with Fog ON (46m) and 500 bullet decals limit.
    """
    cfg = dict(DEFAULT_USER_SETTINGS)
    if os.path.exists(SETTINGS_FILE_PATH):
        try:
            with open(SETTINGS_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                preset = data.get("graphics_preset", "Standard User")
                if preset in GRAPHICS_PRESETS:
                    cfg["graphics_preset"] = preset
                if isinstance(data.get("fog_enabled"), bool):
                    cfg["fog_enabled"] = data["fog_enabled"]
                if isinstance(data.get("fog_distance"), (int, float)):
                    cfg["fog_distance"] = max(15.0, min(95.0, float(data["fog_distance"])))
                if isinstance(data.get("max_bullet_decals"), (int, float)):
                    cfg["max_bullet_decals"] = max(50, min(5000, int(data["max_bullet_decals"])))
                if data.get("selected_map") in ("MainCity2", "gm_bigcity", "BigCity5", "driving Test map"):
                    cfg["selected_map"] = data["selected_map"]
        except Exception:
            pass
    return cfg



def save_user_settings(cfg):
    """Persists user settings to user_settings.json so preferences are remembered across sessions."""
    try:
        with open(SETTINGS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
    except Exception:
        pass


# ═══════════════════════════════════════════════════
#  PERSISTENT MAP EDITOR SAVE / LOAD SYSTEM (custom_maps.json)
# ═══════════════════════════════════════════════════
CUSTOM_MAPS_FILE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "custom_maps.json")


def load_custom_maps():
    """Loads user-created/edited map grids and placed 3D HL2 resources (fences, barriers, entry lights, doors, props) from custom_maps.json."""
    if os.path.exists(CUSTOM_MAPS_FILE_PATH):
        try:
            with open(CUSTOM_MAPS_FILE_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except Exception:
            pass
    return {}


def save_custom_maps(custom_maps_data):
    """Saves user-edited map grids and placed 3D HL2 resources to custom_maps.json on disk."""
    try:
        with open(CUSTOM_MAPS_FILE_PATH, "w", encoding="utf-8") as f:
            json.dump(custom_maps_data, f, indent=2)
        return True
    except Exception:
        return False


# ═══════════════════════════════════════════════════
#  540+ AUTHENTIC HALF-LIFE 2 COMBINE & CITIZEN VOICE LINES
# ═══════════════════════════════════════════════════
_HL2_COMBINE_CORE_LINES = [
    "Pick up that can.",
    "Now, put it in the trash can.",
    "Alright, you can go. *chuckles*",
    "You knocked it over—pick it up!",
    "Citizen, hold it right there!",
    "Move along! Move along, citizen!",
    "Vacate this premises immediately, citizen!",
    "You want a malcompliance verdict?!",
    "Issuing malcompliance citation. Hold position.",
    "Possible Level 3 Civil Privacy Violator here!",
    "We have a 10-108! Officer down! Requesting Skyshield!",
    "10-103M! Subject is armed with a firearm!",
    "We are socio-stable at this location.",
    "Acquiring on visual! Target locked!",
    "Isolate! Isolate that subject!",
    "Prosecute! Administer final verdict!",
    "Amputate! Zero confirm on anti-citizen!",
    "Sterilize sector! Clear all non-tagged humanoids!",
    "Cauterize! Suppressing hostile movement!",
    "Protection team alert: evidence of anti-civil activity in this community.",
    "Attention ground units: mission failure will result in permanent off-world assignment.",
    "Overwatch reminder: inaction is conspiracy. Report counter-behavior immediately.",
    "Individual, you are charged with Socio-Endangerment Level 1. Protection unit prosecution code: DUTY, SWORD, MIDNIGHT.",
    "Individual, you are now charged with Socio-Endangerment Level 5. Cease evasion immediately.",
    "Attention please: unidentified person of interest, confirm your civil status with local protection team immediately.",
    "Attention residents: your block is now charged with Permissive Inactive Coercion. Five ration units deducted.",
    "Citizen reminder: radial compliance is mandatory inside Station Plaza.",
    "Overwatch dispatch: autonomous judgment is now in effect. Sentencing is discretionary.",
    "Protection team: lock down Terminal Checkpoint Alpha. No citizen transit permitted.",
    "Subject is demonstrating non-standard locomotion. Prepare stun baton for pacification.",
    "Warning: second malcompliance verdict will result in immediate physical pacification.",
    "Unit reporting: suspect is evading through the water canal! Engage!",
    "Overwatch: bio-signal flatline confirmed on Protection Unit. Dispatching reinforcement squad.",
    "All units, converge on suspect! Code 3 tactical response!",
    "ContactConfirmed! Anti-Citizen One spotted in Plaza Sector!",
    "Hold position, citizen! Prepare for civil inspection!",
    "First warning: step away from the checkpoint barrier!",
    "Second warning: failure to cooperate will result in permanent relocation!",
    "Final warning: pacification authorized! Charging stunstick!",
    "Viscerator deployed! Sweep the canal basin!",
    "Airwatch reports hostile movement near the Breencast monument!",
    "Outbreak! Outbreak! Sector is not sterile!",
    "Suppressing fire! Pin that anti-citizen down!",
    "Reloading sidearm! Cover my sector!",
    "Target is behind the Combine barricade! Flanking left!",
    "Target is using physics objects as cover! Clear the debris!",
    "We got a DB here—cancel 10-102.",
    "Unable to locate suspect. Switching to grid sweep protocol.",
    "Suspect is bleeding! Press the attack, protection team!",
    "Target designated as Primary Anti-Citizen! All weapons free!",
    "Overwatch acknowledges: Skyshield heavy units inbound to your vector.",
    "Sector 17-Alpha is under martial lock. Return to your designated tenement.",
    "Any citizen found near the security doors without transit papers will be prosecuted.",
    "Looking for trouble, citizen? Keep walking.",
    "Don't even think about crossing this chain-link perimeter.",
    "Check the upper windows! Rebels with RPGs reported on the rooftops!",
    "Combine Elite unit on station: dark energy ball primed.",
    "Affirmative. Pacifying non-compliant pedestrian now.",
    "Copy that, Overwatch. Proceeding to waypoint and checking all entry lights.",
    "Civil Protection Unit on patrol. All socio-metrics nominal.",
]

_HL2_UNITS = [
    "Union-1", "Union-2", "Union-4", "Defender-3", "Defender-7", "Jury-5", "Jury-9",
    "Line-2", "Line-6", "Patrol-8", "Quick-3", "Roller-1", "Stick-5", "Tap-4",
    "Vice-2", "Victor-7", "Xray-1", "Yellow-6", "Hero-3", "King-9"
]
_HL2_CODES = [
    "10-0 (Caution)", "10-2 (Signal Good)", "10-4 (Copy That)", "10-6 (Busy Pacifying)",
    "10-7 (Out of Service)", "10-8 (In Service / On Patrol)", "10-14 (Convoy Escort)",
    "10-15 (Prisoner in Custody)", "10-20 (Location Report)", "10-22 (Disregard Last)",
    "10-25 (Report in Person)", "10-30 (Unnecessary Radio Use)", "10-31 (Crime in Progress)",
    "10-32 (Man with Gun!)", "10-44 (Requesting Patrol Sweep)", "10-50 (Patrol Vehicle Crash)",
    "10-65 (Armed Robbery / Rebel Activity)", "10-78 (Need Assistance Immediately!)",
    "10-91D (Dead Citizen in Street)", "10-97 (Arrived at Scene)", "10-99 (Officer Under Fire!)",
    "10-103 (Disturbance by Mental Subject)", "10-103M (Disturbance by Armed Malcompliant)",
    "10-107 (Suspicious Person Near Checkpoint)", "10-108 (Officer Down / Bio-Signal Lost!)",
    "Code 2 (Urgent — No Siren)", "Code 3 (Emergency — Weapons Drawn)", "Code 7 (Ration Break)",
    "Code 100 (Precinct Clear)", "Violation 243 (Assault on Protection Team)",
    "Violation 404 (Street Riot)", "Violation 415 (Civic Disturbance)",
    "Violation 507 (Public Non-Compliance)", "Violation 603 (Unlawful Sector Entry)",
    "Violation 647E (Anti-Citizen Fugitive)"
]
_HL2_SECTORS = [
    "Terminal Station Plaza", "North Breencast Wall", "East Chain-Link Checkpoint",
    "Tenement Block C-17", "Water Canal Basin", "Industrial Warehouse District",
    "Twin Towers Skyway", "Precinct-4 Security Gate", "Neoclassical Avenue",
    "Combine Citadel Perimeter", "South Harbor Dock", "Transit Corridor 7",
    "Ration Distribution Center", "Sub-Level Drainage Canal"
]
_HL2_VERDICTS = [
    "Code: ISOLATE, EXPOSE, ADMINISTER.",
    "Code: LOCK, CAUTERIZE, STABILIZE.",
    "Code: DUTY, SWORD, OPERATE.",
    "Code: AMPUTATE, ZERO, CONFIRM.",
    "Code: CLAMP, CONTAIN, STERILIZE.",
    "Verdict: Immediate stun-baton pacification authorized.",
    "Verdict: Lethal 9mm sidearm engagement authorized.",
    "Verdict: Deploy Overwatch Elite strike team.",
    "Status: Sweeping entry lights and barricades.",
    "Status: Securing checkpoint doors and canal perimeter."
]

COMBINE_VOICE_LINES = list(_HL2_COMBINE_CORE_LINES)
for _u_idx, _unit in enumerate(_HL2_UNITS):
    for _c_idx, _code in enumerate(_HL2_CODES):
        _sec = _HL2_SECTORS[(_u_idx + _c_idx) % len(_HL2_SECTORS)]
        _vrd = _HL2_VERDICTS[(_u_idx * 3 + _c_idx) % len(_HL2_VERDICTS)]
        COMBINE_VOICE_LINES.append(f"[{_unit}] Dispatch {_code} at {_sec}. {_vrd}")
        if len(COMBINE_VOICE_LINES) >= 540:
            break
    if len(COMBINE_VOICE_LINES) >= 540:
        break

# ── Genuine Valve Half-Life 2 City 17 PA Loudspeaker Announcements (sound/npc/overwatch/cityvoice/*_spkr.wav) ──
OVERWATCH_ANNOUNCEMENTS = [
    ("f_anticitizenreport_spkr.wav", "ATTENTION GROUND UNITS: ANTI-CITIZEN REPORTED IN THIS COMMUNITY. CODE: LOCK, CAUTERIZE, STABILIZE"),
    ("f_anticivil1_5_spkr.wav", "WARNING: INDIVIDUAL, YOU ARE CONVICTED OF MULTI-ANTI-CIVIL VIOLATIONS. IMPLICIT CITIZENSHIP REVOKED"),
    ("f_anticivilevidence_3_spkr.wav", "ATTENTION: PROTECTION TEAM, CIVIL UNREST DETECTED. CODE 10-103M"),
    ("f_capitalmalcompliance_spkr.wav", "INDIVIDUAL: YOU ARE CHARGED WITH CAPITAL MALCOMPLIANCE. ANTI-CITIZEN STATUS APPROVED"),
    ("f_ceaseevasionlevelfive_spkr.wav", "INDIVIDUAL: CEASE EVASION IMMEDIATELY. LEVEL 5 PROSECUTION AUTHORIZED"),
    ("f_citizenshiprevoked_6_spkr.wav", "INDIVIDUAL: YOU ARE CHARGED WITH SOCIO-ENDANGERMENT LEVEL 1. PROTECTION RESPONSE PRIORITY 1"),
    ("f_confirmcivilstatus_1_spkr.wav", "ATTENTION ALL RESIDENTS: CONFIRM CIVIL STATUS WITH LOCAL PROTECTION TEAM IMMEDIATELY"),
    ("f_evasionbehavior_2_spkr.wav", "WARNING: EVASION BEHAVIOR WILL BE MET WITH AUTONOMOUS PROSECUTION"),
    ("f_innactionisconspiracy_spkr.wav", "REMINDER: INACTION IS CONSPIRACY. REPORT SUSPICIOUS ACTIVITY TO CIVIL PROTECTION"),
    ("f_localunrest_spkr.wav", "ATTENTION: LOCAL UNREST IN PROGRESS. CURFEW IS NOW MANDATORY"),
    ("f_protectionresponse_1_spkr.wav", "PROTECTION RESPONSE TEAM DISPATCHED TO SECTOR"),
    ("f_protectionresponse_4_spkr.wav", "ALERT: DEFENSE UNITS, RESPOND CODE 3"),
    ("f_protectionresponse_5_spkr.wav", "ATTENTION UNITS: DEPLOY TERMINAL PROSECUTION"),
    ("f_rationunitsdeduct_3_spkr.wav", "REMINDER: 100 RATION UNITS DEDUCTED FOR CIVIC NON-COMPLIANCE"),
    ("f_sociolevel1_4_spkr.wav", "WARNING: SOCIO-ENDANGERMENT LEVEL 1 CONFIRMED"),
    ("f_trainstation_assemble_spkr.wav", "ATTENTION RESIDENTS: INSPECTION TEAM IN SECTOR. ASSEMBLE AT CHECKPOINT"),
    ("f_trainstation_assumepositions_spkr.wav", "CITIZENS: ASSUME INSPECTION POSITIONS IMMEDIATELY"),
    ("f_trainstation_cooperation_spkr.wav", "COOPERATION WITH CIVIL PROTECTION WILL BE REWARDED WITH INCREASED RATION DISTRIBUTION"),
    ("f_trainstation_inform_spkr.wav", "ATTENTION: INFORM ON ANTI-CITIZENS TO RECEIVE PRIORITY HOUSING REALLOCATION"),
    ("f_trainstation_offworldrelocation_spkr.wav", "WARNING: CONTINUED CIVIL FAILURE WILL RESULT IN PERMANENT OFF-WORLD RELOCATION"),
    ("f_unrestprocedure1_spkr.wav", "ALERT: UNREST PROCEDURE CODE 1 ACTIVE"),
]

CITIZEN_VOICE_LINES = {
    "idle": [
        "Sometimes, I dream about cheese.",
        "They're always departing, but they never arrive... and the ones that do arrive, they never leave.",
        "Don't drink the water. They put something in it, to make you forget. I don't even remember how I got here.",
        "I don't even know how many cities they've relocated me to. City 14, City 17... it all blurs together.",
        "Keep your head down when you pass the Metrocops by the checkpoint fence.",
        "Did you see that new guy in the Plaza? The CPs made him pick up a trash can.",
        "Dr. Breen keeps telling us City 17 is the finest urban center remaining... look at this place.",
        "They took my suitcase at the train station and gave me this blue jumpsuit.",
        "No one ever gets on the trains, only off.",
        "Watch out for the stunbatons—one smack and your ribs ache for a week.",
        "I heard the Resistance is hiding weapons in the industrial block past the checkpoint.",
        "Whatever you do, don't bump into a Civil Protection officer!",
        "The entry lights hum all night long outside my tenement window.",
        "I miss real food. All we get are these desiccated water-flavored ration bars.",
        "Have you noticed the Combine barricades creeping closer every week?",
        "If the sirens start wailing, get inside the apartment block immediately!",
        "I used to be an architect before the Seven Hour War. Now I just sweep cobblestones.",
        "They say Gordon Freeman is back in City 17... could it really be true?",
        "Stay away from the red barrels near the canal—one stray bullet and they blow!",
        "Every time a Metrocop flatlines, Overwatch sends two more to replace him.",
    ],
    "panic": [
        "Civil Protection! Run for your life!",
        "CPs! Get down, they're shooting!",
        "Help! Somebody help me! Hostiles in the sector!",
        "Run! Run for your lives! It's a firefight!",
        "Watch out! Get behind cover!",
        "Oh God, not another street raid! Everyone scatter!",
        "Get out of the street! The Combine are opening fire!",
        "Head for the tenements! Don't stay in the open plaza!",
        "They're everywhere! Run!",
        "Don't let the Metrocops corner you against the fence!",
        "Incoming fire! Duck!",
        "Oh no, they've got guns drawn! Run!",
    ],
    "pain": [
        "Ow! Stop! Don't shoot, I'm a citizen!",
        "Agh! Why are you hitting me?! I didn't do anything!",
        "Oof! Please, I'm unarmed! Check my citizen ID!",
        "My arm! Agh, hold your fire! I'm with the Resistance!",
        "Gah! Help! I'm hit! Somebody call a medic!",
        "Ack! Please, spare me! I just got relocated to City 17!",
        "Ugh! That hurts! Stop shooting!",
        "Ow! Watch where you're aiming that weapon!",
        "Aghhh! My leg! I can't run!",
        "No! Please! Don't kill me!",
    ],
    "death": [
        "No... nooo... tell the Resistance we tried...",
        "Ughhh... I never even got my ration...",
        "Aghhh! Not like this... not in City 17...",
        "Oh God... everything's going dark...",
        "Ugh... Dr. Breen... you lied to us...",
        "Nooo... I just wanted to get out of the city...",
        "Aghh... tell my family in Sector 8...",
        "Ughhh... freedom... at last...",
    ],
}


# ═══════════════════════════════════════════════════
#  OPENGL 1.1 BINDINGS (Zero external dependencies)
# ═══════════════════════════════════════════════════
gl = ctypes.windll.opengl32

GL_FALSE = 0
GL_TRUE = 1

GL_COLOR_BUFFER_BIT = 0x00004000
GL_DEPTH_BUFFER_BIT = 0x00000100
GL_PROJECTION = 0x1701
GL_MODELVIEW = 0x1700
GL_DEPTH_TEST = 0x0B71
GL_LEQUAL = 0x0203
GL_BLEND = 0x0BE2
GL_SRC_ALPHA = 0x0302
GL_ONE_MINUS_SRC_ALPHA = 0x0303
GL_ONE = 0x0001
GL_TEXTURE_2D = 0x0DE1
GL_RGBA = 0x1908
GL_UNSIGNED_BYTE = 0x1401
GL_TEXTURE_MIN_FILTER = 0x2801
GL_TEXTURE_MAG_FILTER = 0x2800
GL_TEXTURE_WRAP_S = 0x2802
GL_TEXTURE_WRAP_T = 0x2803
GL_CLAMP = 0x2900
GL_REPEAT = 0x2901
GL_NEAREST = 0x2600
GL_LINEAR = 0x2601
GL_QUADS = 0x0007
GL_TRIANGLES = 0x0004
GL_LINES = 0x0001
GL_LINE_LOOP = 0x0002
GL_TRIANGLE_FAN = 0x0006
GL_QUAD_STRIP = 0x0008
GL_LIGHTING = 0x0B50
GL_LIGHT0 = 0x4000
GL_LIGHT1 = 0x4001
GL_POSITION = 0x1203
GL_AMBIENT = 0x1200
GL_DIFFUSE = 0x1201
GL_COLOR_MATERIAL = 0x0B57
GL_FRONT_AND_BACK = 0x0408
GL_AMBIENT_AND_DIFFUSE = 0x1602
GL_NORMALIZE = 0x0BA1
GL_SMOOTH = 0x1D01
GL_FOG = 0x0B60
GL_FOG_MODE = 0x0B65
GL_FOG_COLOR = 0x0B66
GL_FOG_START = 0x0B63
GL_FOG_END = 0x0B64
GL_LINEAR_FOG = 0x2601
GL_ALPHA_TEST = 0x0BC0
GL_GREATER = 0x0204
GL_COMPILE = 0x1300

gl.glClearColor.argtypes = [c_float, c_float, c_float, c_float]
gl.glAlphaFunc.argtypes = [c_uint, c_float]
gl.glClear.argtypes = [c_uint]
gl.glViewport.argtypes = [c_int, c_int, c_int, c_int]
gl.glMatrixMode.argtypes = [c_uint]
gl.glLoadIdentity.argtypes = []
gl.glLoadMatrixf.argtypes = [POINTER(c_float)]
gl.glMultMatrixf.argtypes = [POINTER(c_float)]
gl.glPushMatrix.argtypes = []
gl.glPopMatrix.argtypes = []
gl.glEnable.argtypes = [c_uint]
gl.glDisable.argtypes = [c_uint]
gl.glDepthFunc.argtypes = [c_uint]
gl.glDepthMask.argtypes = [c_uint]
gl.glBlendFunc.argtypes = [c_uint, c_uint]
gl.glTranslatef.argtypes = [c_float, c_float, c_float]
gl.glRotatef.argtypes = [c_float, c_float, c_float, c_float]
gl.glScalef.argtypes = [c_float, c_float, c_float]
gl.glColor3f.argtypes = [c_float, c_float, c_float]
gl.glColor4f.argtypes = [c_float, c_float, c_float, c_float]
gl.glNormal3f.argtypes = [c_float, c_float, c_float]
gl.glVertex3f.argtypes = [c_float, c_float, c_float]
gl.glVertex2f.argtypes = [c_float, c_float]
gl.glTexCoord2f.argtypes = [c_float, c_float]
gl.glBegin.argtypes = [c_uint]
gl.glEnd.argtypes = []
gl.glGenTextures.argtypes = [c_int, POINTER(c_uint)]
gl.glBindTexture.argtypes = [c_uint, c_uint]
gl.glTexParameteri.argtypes = [c_uint, c_uint, c_int]
gl.glTexImage2D.argtypes = [c_uint, c_int, c_int, c_int, c_int, c_int, c_uint, c_uint, c_void_p]
gl.glTexSubImage2D.argtypes = [c_uint, c_int, c_int, c_int, c_int, c_int, c_uint, c_uint, c_void_p]
gl.glLightfv.argtypes = [c_uint, c_uint, POINTER(c_float)]
gl.glColorMaterial.argtypes = [c_uint, c_uint]
gl.glShadeModel.argtypes = [c_uint]
gl.glFogi.argtypes = [c_uint, c_int]
gl.glFogfv.argtypes = [c_uint, POINTER(c_float)]
gl.glFogf.argtypes = [c_uint, c_float]
gl.glGenLists.argtypes = [c_int]
gl.glGenLists.restype = c_uint
gl.glNewList.argtypes = [c_uint, c_uint]
gl.glEndList.argtypes = []
gl.glCallList.argtypes = [c_uint]
gl.glLineWidth.argtypes = [c_float]
gl.glOrtho.argtypes = [ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double, ctypes.c_double]
gl.glReadPixels.argtypes = [c_int, c_int, c_int, c_int, c_uint, c_uint, c_void_p]


def gl_perspective(fov_y_deg, aspect, z_near, z_far):
    f = 1.0 / math.tan(math.radians(fov_y_deg) / 2.0)
    m = (c_float * 16)(
        f / aspect, 0.0, 0.0, 0.0,
        0.0, f, 0.0, 0.0,
        0.0, 0.0, (z_far + z_near) / (z_near - z_far), -1.0,
        0.0, 0.0, (2.0 * z_far * z_near) / (z_near - z_far), 0.0
    )
    gl.glMultMatrixf(m)


def gl_look_at(ex, ey, ez, cx, cy, cz, ux, uy, uz):
    fx, fy, fz = cx - ex, cy - ey, cz - ez
    fl = math.sqrt(fx * fx + fy * fy + fz * fz) or 1.0
    fx, fy, fz = fx / fl, fy / fl, fz / fl

    sx = fy * uz - fz * uy
    sy = fz * ux - fx * uz
    sz = fx * uy - fy * ux
    sl = math.sqrt(sx * sx + sy * sy + sz * sz) or 1.0
    sx, sy, sz = sx / sl, sy / sl, sz / sl

    upx = sy * fz - sz * fy
    upy = sz * fx - sx * fz
    upz = sx * fy - sy * fx

    m = (c_float * 16)(
        sx, upx, -fx, 0.0,
        sy, upy, -fy, 0.0,
        sz, upz, -fz, 0.0,
        0.0, 0.0, 0.0, 1.0
    )
    gl.glMultMatrixf(m)
    gl.glTranslatef(-ex, -ey, -ez)


def draw_box(w, h, d, r, g, b, a=1.0):
    """Draws a 3D shaded box centered at (0, 0, 0) with size (w, h, d)."""
    gl.glDisable(GL_TEXTURE_2D)
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
    gl.glBegin(GL_QUADS)
    # Top (+Y)
    gl.glColor4f(min(1.0, r * 1.15), min(1.0, g * 1.15), min(1.0, b * 1.15), a)
    gl.glNormal3f(0, 1, 0)
    gl.glVertex3f(-hw, hh, -hd)
    gl.glVertex3f(-hw, hh, hd)
    gl.glVertex3f(hw, hh, hd)
    gl.glVertex3f(hw, hh, -hd)
    # Bottom (-Y)
    gl.glColor4f(r * 0.55, g * 0.55, b * 0.55, a)
    gl.glNormal3f(0, -1, 0)
    gl.glVertex3f(-hw, -hh, -hd)
    gl.glVertex3f(hw, -hh, -hd)
    gl.glVertex3f(hw, -hh, hd)
    gl.glVertex3f(-hw, -hh, hd)
    # Front (+Z)
    gl.glColor4f(r, g, b, a)
    gl.glNormal3f(0, 0, 1)
    gl.glVertex3f(-hw, -hh, hd)
    gl.glVertex3f(hw, -hh, hd)
    gl.glVertex3f(hw, hh, hd)
    gl.glVertex3f(-hw, hh, hd)
    # Back (-Z)
    gl.glColor4f(r * 0.85, g * 0.85, b * 0.85, a)
    gl.glNormal3f(0, 0, -1)
    gl.glVertex3f(hw, -hh, -hd)
    gl.glVertex3f(-hw, -hh, -hd)
    gl.glVertex3f(-hw, hh, -hd)
    gl.glVertex3f(hw, hh, -hd)
    # Right (+X)
    gl.glColor4f(r * 0.75, g * 0.75, b * 0.75, a)
    gl.glNormal3f(1, 0, 0)
    gl.glVertex3f(hw, -hh, hd)
    gl.glVertex3f(hw, -hh, -hd)
    gl.glVertex3f(hw, hh, -hd)
    gl.glVertex3f(hw, hh, hd)
    # Left (-X)
    gl.glColor4f(r * 0.72, g * 0.72, b * 0.72, a)
    gl.glNormal3f(-1, 0, 0)
    gl.glVertex3f(-hw, -hh, -hd)
    gl.glVertex3f(-hw, -hh, hd)
    gl.glVertex3f(-hw, hh, hd)
    gl.glVertex3f(-hw, hh, -hd)
    gl.glEnd()


def draw_textured_box(w, h, d, tex_id, u_rep=1.0, v_rep=1.0, r=1.0, g=1.0, b=1.0):
    """Draws a UV-mapped 3D box using an OpenGL 2D texture for realistic building facades and fortifications."""
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
    gl.glEnable(GL_TEXTURE_2D)
    gl.glBindTexture(GL_TEXTURE_2D, tex_id)
    gl.glBegin(GL_QUADS)
    # Front (+Z)
    gl.glColor4f(r, g, b, 1.0)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-hw, -hh, hd)
    gl.glTexCoord2f(u_rep, 0.0); gl.glVertex3f(hw, -hh, hd)
    gl.glTexCoord2f(u_rep, v_rep); gl.glVertex3f(hw, hh, hd)
    gl.glTexCoord2f(0.0, v_rep); gl.glVertex3f(-hw, hh, hd)
    # Back (-Z)
    gl.glColor4f(r * 0.88, g * 0.88, b * 0.90, 1.0)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(hw, -hh, -hd)
    gl.glTexCoord2f(u_rep, 0.0); gl.glVertex3f(-hw, -hh, -hd)
    gl.glTexCoord2f(u_rep, v_rep); gl.glVertex3f(-hw, hh, -hd)
    gl.glTexCoord2f(0.0, v_rep); gl.glVertex3f(hw, hh, -hd)
    # Right (+X)
    gl.glColor4f(r * 0.78, g * 0.78, b * 0.82, 1.0)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(hw, -hh, hd)
    gl.glTexCoord2f(u_rep, 0.0); gl.glVertex3f(hw, -hh, -hd)
    gl.glTexCoord2f(u_rep, v_rep); gl.glVertex3f(hw, hh, -hd)
    gl.glTexCoord2f(0.0, v_rep); gl.glVertex3f(hw, hh, hd)
    # Left (-X)
    gl.glColor4f(r * 0.74, g * 0.74, b * 0.78, 1.0)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-hw, -hh, -hd)
    gl.glTexCoord2f(u_rep, 0.0); gl.glVertex3f(-hw, -hh, hd)
    gl.glTexCoord2f(u_rep, v_rep); gl.glVertex3f(-hw, hh, hd)
    gl.glTexCoord2f(0.0, v_rep); gl.glVertex3f(-hw, hh, -hd)
    # Top (+Y)
    gl.glColor4f(r * 0.65, g * 0.65, b * 0.68, 1.0)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-hw, hh, -hd)
    gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(-hw, hh, hd)
    gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(hw, hh, hd)
    gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(hw, hh, -hd)
    gl.glEnd()
    gl.glDisable(GL_TEXTURE_2D)


WORLD_TEXTURES = {}
GL_GENERATE_MIPMAP = 0x8191
GL_LINEAR_MIPMAP_LINEAR = 0x2703
GL_TEXTURE_MAX_ANISOTROPY_EXT = 0x84FE


def _upload_surf_to_gl_tex(surf, clamp=False):
    w, h = surf.get_size()
    raw = pygame.image.tostring(surf, "RGBA", True)
    tid = c_uint(0)
    gl.glGenTextures(1, byref(tid))
    gl.glBindTexture(GL_TEXTURE_2D, tid.value)
    # Hardware trilinear mipmapping + 8x anisotropic filtering for crisp Source VTF materials
    try:
        gl.glTexParameteri(GL_TEXTURE_2D, GL_GENERATE_MIPMAP, 1)
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR_MIPMAP_LINEAR)
    except Exception:
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    try:
        gl.glTexParameterf(GL_TEXTURE_2D, GL_TEXTURE_MAX_ANISOTROPY_EXT, 8.0)
    except Exception:
        pass
    wrap_mode = GL_CLAMP if clamp else GL_REPEAT
    gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, wrap_mode)
    gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, wrap_mode)
    gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0, GL_RGBA, GL_UNSIGNED_BYTE, raw)
    return tid.value


def draw_textured_cylinder(radius, height, tex_id, segs=16, u0=0.0, u1=1.0, v0=0.0, v1=1.0,
                           cap_r=0.22, cap_g=0.24, cap_b=0.28, r=1.0, g=1.0, b=1.0):
    """Draws a 3D cylindrical Source prop (barrels, drums, gas cans) wrapped with a genuine Source VTF texture."""
    if not tex_id:
        draw_box(radius * 2.0, height, radius * 2.0, r, g, b)
        return
    hh = height * 0.5
    gl.glEnable(GL_TEXTURE_2D)
    gl.glBindTexture(GL_TEXTURE_2D, tex_id)
    gl.glColor4f(r, g, b, 1.0)
    gl.glBegin(GL_QUADS)
    for i in range(segs):
        a0 = (i / segs) * math.tau
        a1 = ((i + 1) / segs) * math.tau
        c0, s0 = math.cos(a0), math.sin(a0)
        c1, s1 = math.cos(a1), math.sin(a1)
        tu0 = u1 - (i / segs) * (u1 - u0)
        tu1 = u1 - ((i + 1) / segs) * (u1 - u0)
        gl.glNormal3f((c0 + c1) * 0.5, 0.0, (s0 + s1) * 0.5)
        gl.glTexCoord2f(tu0, v0); gl.glVertex3f(c0 * radius, -hh, s0 * radius)
        gl.glTexCoord2f(tu1, v0); gl.glVertex3f(c1 * radius, -hh, s1 * radius)
        gl.glTexCoord2f(tu1, v1); gl.glVertex3f(c1 * radius,  hh, s1 * radius)
        gl.glTexCoord2f(tu0, v1); gl.glVertex3f(c0 * radius,  hh, s0 * radius)
    gl.glEnd()
    gl.glDisable(GL_TEXTURE_2D)

    # Top & bottom metallic/plastic drum lids with raised rim
    gl.glColor4f(cap_r, cap_g, cap_b, 1.0)
    for y_cap, ny in ((hh, 1.0), (-hh, -1.0)):
        gl.glBegin(GL_TRIANGLES)
        gl.glNormal3f(0.0, ny, 0.0)
        for i in range(segs):
            a0 = (i / segs) * math.tau
            a1 = ((i + 1) / segs) * math.tau
            gl.glVertex3f(0.0, y_cap, 0.0)
            gl.glVertex3f(math.cos(a0) * radius * 0.96, y_cap, math.sin(a0) * radius * 0.96)
            gl.glVertex3f(math.cos(a1) * radius * 0.96, y_cap, math.sin(a1) * radius * 0.96)
        gl.glEnd()


def draw_textured_quad_panel(w, h, tex_id, u_rep=1.0, v_rep=1.0, r=1.0, g=1.0, b=1.0, a=1.0):
    """Draws a double-sided textured 3D panel (for chainlink fences, posters, signs, Breencast screen)."""
    hw, hh = w * 0.5, h * 0.5
    gl.glEnable(GL_TEXTURE_2D)
    gl.glBindTexture(GL_TEXTURE_2D, tex_id)
    gl.glColor4f(r, g, b, a)
    gl.glBegin(GL_QUADS)
    # Front (+Z)
    gl.glNormal3f(0, 0, 1)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-hw, -hh, 0.0)
    gl.glTexCoord2f(u_rep, 0.0); gl.glVertex3f(hw, -hh, 0.0)
    gl.glTexCoord2f(u_rep, v_rep); gl.glVertex3f(hw, hh, 0.0)
    gl.glTexCoord2f(0.0, v_rep); gl.glVertex3f(-hw, hh, 0.0)
    # Back (-Z)
    gl.glNormal3f(0, 0, -1)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(hw, -hh, 0.0)
    gl.glTexCoord2f(u_rep, 0.0); gl.glVertex3f(-hw, -hh, 0.0)
    gl.glTexCoord2f(u_rep, v_rep); gl.glVertex3f(-hw, hh, 0.0)
    gl.glTexCoord2f(0.0, v_rep); gl.glVertex3f(hw, hh, 0.0)
    gl.glEnd()
    gl.glDisable(GL_TEXTURE_2D)


def generate_battlefield_textures():
    """
    Loads genuine extracted Half-Life 2 textures from ./assets/hl2/textures/ (extracted from
    the local Steam Half-Life 2 VPKs) with procedural fallbacks, matching all 3 reference screenshots:
    - Screenshot 1: Green-grey tenement corridor brick + peeling Cyrillic posters
    - Screenshot 2: Trainstation diamond terrazzo tiles, chainlink security fences, cyan Breencast screen
    - Screenshot 3: City-17 European terracotta & yellow turret facades, rusty shop awnings, cobblestones
    """
    rng = random.Random(2007)
    textures = {}
    S = 256
    tex_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "hl2", "textures")

    def load_hl2_or_fallback(filename, fallback_surf, clamp=False):
        p = os.path.join(tex_dir, filename)
        if os.path.exists(p):
            try:
                surf = pygame.image.load(p).convert_alpha()
                return _upload_surf_to_gl_tex(surf, clamp=clamp), surf
            except Exception:
                pass
        return _upload_surf_to_gl_tex(fallback_surf, clamp=clamp), fallback_surf

    # Procedural fallback surface helper
    def make_fallback_brick(col_base):
        s = pygame.Surface((S, S), pygame.SRCALPHA)
        s.fill((*col_base, 255))
        return s

    # Load all authentic Half-Life 2 textures
    textures['c17_terracotta'], _ = load_hl2_or_fallback("c17_terracotta.png", make_fallback_brick((155, 95, 72)))
    textures['c17_terracotta_win'], _ = load_hl2_or_fallback("c17_terracotta_win.png", make_fallback_brick((148, 88, 66)))
    textures['c17_yellow_turret'], _ = load_hl2_or_fallback("c17_yellow_turret.png", make_fallback_brick((195, 182, 128)))
    textures['c17_neoclassical'], _ = load_hl2_or_fallback("c17_neoclassical.png", make_fallback_brick((188, 184, 172)))
    textures['c17_facade_03'], _ = load_hl2_or_fallback("c17_facade_03.png", make_fallback_brick((152, 148, 138)))
    textures['c17_facade_12'], _ = load_hl2_or_fallback("c17_facade_12.png", make_fallback_brick((168, 148, 112)))
    textures['corridor_green_brick'], s_green = load_hl2_or_fallback("corridor_green_brick.png", make_fallback_brick((105, 118, 110)))
    textures['c17_red_brick'], _ = load_hl2_or_fallback("c17_red_brick.png", make_fallback_brick((122, 68, 54)))
    textures['c17_SlateRoof'], _ = load_hl2_or_fallback("c17_SlateRoof.png", make_fallback_brick((52, 56, 62)))
    textures['c17_awning'], _ = load_hl2_or_fallback("c17_awning.png", make_fallback_brick((128, 98, 76)))
    textures['trainstation_tile'], _ = load_hl2_or_fallback("trainstation_tile.png", make_fallback_brick((178, 172, 158)))
    textures['chainlink_fence'], _ = load_hl2_or_fallback("chainlink_fence.png", make_fallback_brick((90, 95, 98)))
    textures['iron_grille'], _ = load_hl2_or_fallback("iron_grille.png", make_fallback_brick((45, 48, 50)))
    textures['combine_bunker'], _ = load_hl2_or_fallback("combine_wall.png", make_fallback_brick((48, 56, 68)))
    textures['breencast_screen'], _ = load_hl2_or_fallback("breencast_screen.png", make_fallback_brick((90, 225, 245)), clamp=True)
    textures['posters_01'], s_post1 = load_hl2_or_fallback("posters_01.png", make_fallback_brick((180, 170, 140)), clamp=True)
    textures['posters_02'], s_post2 = load_hl2_or_fallback("posters_02.png", make_fallback_brick((175, 160, 135)), clamp=True)
    textures['cobble_street'], _ = load_hl2_or_fallback("cobble_street.png", make_fallback_brick((82, 80, 78)))
    textures['concrete_sidewalk'], _ = load_hl2_or_fallback("concrete_sidewalk.png", make_fallback_brick((148, 146, 140)))

    # Build Screenshot 1 composite: Green-grey painted brick wall with peeling Cyrillic posters plastered on it
    s_corridor_post = s_green.copy()
    p_scaled = pygame.transform.smoothscale(s_post1, (220, 110))
    s_corridor_post.blit(p_scaled, (18, 95))
    textures['corridor_poster_wall'] = _upload_surf_to_gl_tex(s_corridor_post)

    # Keep aliases for compatibility
    textures['euro_brick'] = textures['c17_terracotta_win']
    textures['plaster_facade'] = textures['c17_neoclassical']
    textures['bombed_ruin'] = textures['corridor_poster_wall']

    textures['metrocop_sheet'], _ = load_hl2_or_fallback("metrocop_sheet.png", make_fallback_brick((180, 180, 180)), clamp=False)
    textures['citizen_sheet'], _ = load_hl2_or_fallback("citizen_sheet.png", make_fallback_brick((90, 110, 145)), clamp=False)
    textures['wood_crate'], _ = load_hl2_or_fallback("wood_crate.png", make_fallback_brick((168, 128, 76)))
    textures['combine_barricade'], _ = load_hl2_or_fallback("combine_barricade.png", make_fallback_brick((54, 62, 74)))
    textures['combine_barricade_tall'], _ = load_hl2_or_fallback("combine_barricade_tall.png", make_fallback_brick((46, 54, 66)))
    textures['hl2_metal_door'], _ = load_hl2_or_fallback("hl2_metal_door.png", make_fallback_brick((78, 84, 88)))
    textures['entry_light'], _ = load_hl2_or_fallback("entry_light.png", make_fallback_brick((245, 225, 165)))

    # Genuine Half-Life 2 Weapon & HEV Hand Textures (extracted from Steam HL2 VPKs)
    textures['w_crowbar'], _ = load_hl2_or_fallback("w_crowbar.png", make_fallback_brick((185, 42, 32)))
    textures['w_pistol'], _ = load_hl2_or_fallback("w_pistol.png", make_fallback_brick((155, 162, 168)))
    textures['w_smg1'], _ = load_hl2_or_fallback("w_smg1.png", make_fallback_brick((68, 74, 82)))
    textures['w_shotgun'], _ = load_hl2_or_fallback("w_shotgun.png", make_fallback_brick((62, 65, 70)))
    textures['w_irifle'], _ = load_hl2_or_fallback("w_irifle.png", make_fallback_brick((58, 72, 92)))
    textures['w_357'], _ = load_hl2_or_fallback("w_357.png", make_fallback_brick((192, 196, 202)))
    textures['w_rpg_sheet'], _ = load_hl2_or_fallback("w_rpg_sheet.png", make_fallback_brick((82, 92, 62)))
    textures['w_stunbaton'], _ = load_hl2_or_fallback("stunbaton.png", make_fallback_brick((65, 82, 108)))
    textures['v_hand_sheet'], _ = load_hl2_or_fallback("v_hand_sheet.png", make_fallback_brick((218, 122, 28)))

    # ── Genuine Source Engine Props, Barrels, Pickups, Chargers & Walls (extracted from HL2 VPKs) ──
    textures['hl2_blue_barrel'], _ = load_hl2_or_fallback("hl2_blue_barrel.png", make_fallback_brick((38, 105, 195)))
    textures['hl2_explosive_drum'], _ = load_hl2_or_fallback("hl2_explosive_drum.png", make_fallback_brick((198, 42, 32)))
    textures['hl2_oil_drum'], _ = load_hl2_or_fallback("hl2_oil_drum.png", make_fallback_brick((68, 74, 80)))
    textures['hl2_healthkit'], _ = load_hl2_or_fallback("hl2_healthkit.png", make_fallback_brick((225, 228, 232)))
    textures['hl2_hev_battery'], _ = load_hl2_or_fallback("hl2_hev_battery.png", make_fallback_brick((45, 165, 215)))
    textures['hl2_car_battery'], _ = load_hl2_or_fallback("hl2_car_battery.png", make_fallback_brick((58, 62, 68)))
    textures['hl2_ammo_smg1'], _ = load_hl2_or_fallback("hl2_ammo_smg1.png", make_fallback_brick((112, 105, 78)))
    textures['hl2_ammo_pistol'], _ = load_hl2_or_fallback("hl2_ammo_pistol.png", make_fallback_brick((120, 112, 84)))
    textures['hl2_ammo_buckshot'], _ = load_hl2_or_fallback("hl2_ammo_buckshot.png", make_fallback_brick((175, 48, 38)))
    textures['hl2_ammocrate_smg1'], _ = load_hl2_or_fallback("hl2_ammocrate_smg1.png", make_fallback_brick((72, 85, 58)))
    textures['hl2_ammocrate_rockets'], _ = load_hl2_or_fallback("hl2_ammocrate_rockets.png", make_fallback_brick((68, 82, 54)))
    textures['hl2_health_charger'], _ = load_hl2_or_fallback("hl2_health_charger.png", make_fallback_brick((165, 185, 195)))
    textures['hl2_suit_charger'], _ = load_hl2_or_fallback("hl2_suit_charger.png", make_fallback_brick((210, 145, 38)))
    textures['hl2_soda_machine'], _ = load_hl2_or_fallback("hl2_soda_machine.png", make_fallback_brick((38, 95, 175)))
    textures['hl2_dumpster'], _ = load_hl2_or_fallback("hl2_dumpster.png", make_fallback_brick((54, 92, 64)))
    textures['hl2_cargo_container01'], _ = load_hl2_or_fallback("hl2_cargo_container01.png", make_fallback_brick((155, 52, 42)))
    textures['hl2_cargo_container02'], _ = load_hl2_or_fallback("hl2_cargo_container02.png", make_fallback_brick((42, 85, 145)))
    textures['hl2_wood_pallet'], _ = load_hl2_or_fallback("hl2_wood_pallet.png", make_fallback_brick((158, 122, 74)))
    textures['hl2_cardboard_box'], _ = load_hl2_or_fallback("hl2_cardboard_box.png", make_fallback_brick((172, 138, 92)))
    textures['hl2_gascan'], _ = load_hl2_or_fallback("hl2_gascan.png", make_fallback_brick((188, 45, 35)))
    textures['hl2_lockers'], _ = load_hl2_or_fallback("hl2_lockers.png", make_fallback_brick((92, 102, 98)))
    textures['hl2_bench'], _ = load_hl2_or_fallback("hl2_bench.png", make_fallback_brick((138, 102, 65)))
    textures['hl2_combine_generator'], _ = load_hl2_or_fallback("hl2_combine_generator.png", make_fallback_brick((58, 72, 88)))
    textures['hl2_wasteland_barricade'], _ = load_hl2_or_fallback("hl2_wasteland_barricade.png", make_fallback_brick((128, 124, 118)))
    textures['hl2_plastic_crate'], _ = load_hl2_or_fallback("hl2_plastic_crate.png", make_fallback_brick((185, 145, 42)))
    textures['hl2_road_asphalt'], s_hl2_road = load_hl2_or_fallback("hl2_road_asphalt.png", make_fallback_brick((56, 58, 62)))
    textures['hl2_road_crosswalk'], _ = load_hl2_or_fallback("hl2_road_crosswalk.png", make_fallback_brick((72, 74, 78)))
    textures['hl2_metal_wall'], _ = load_hl2_or_fallback("hl2_metal_wall.png", make_fallback_brick((78, 86, 94)))
    textures['hl2_brick_wall031'], _ = load_hl2_or_fallback("hl2_brick_wall031.png", make_fallback_brick((138, 78, 62)))
    textures['hl2_brick_wall045'], _ = load_hl2_or_fallback("hl2_brick_wall045.png", make_fallback_brick((128, 72, 58)))
    textures['hl2_plaster_wall013'], _ = load_hl2_or_fallback("hl2_plaster_wall013.png", make_fallback_brick((172, 166, 152)))

    # Woven sandbag texture
    s_sand = pygame.Surface((S, S), pygame.SRCALPHA)
    s_sand.fill((92, 82, 60, 255))
    sb_w, sb_h = 42, 20
    for row in range(S // sb_h + 1):
        y = row * sb_h
        off = (row % 2) * (sb_w // 2)
        for col in range(-1, S // sb_w + 1):
            x = col * sb_w + off
            v = rng.randint(-12, 12)
            pygame.draw.rect(s_sand, (138 + v, 124 + v, 92 + v), (x + 2, y + 2, sb_w - 4, sb_h - 4), border_radius=5)
    textures['sandbag'] = _upload_surf_to_gl_tex(s_sand)

    # Source Engine Refractive Water Texture (for Canal & Basin Water Physics)
    s_water = pygame.Surface((S, S), pygame.SRCALPHA)
    s_water.fill((28, 92, 128, 210))
    for wy in range(0, S, 4):
        for wx in range(0, S, 4):
            w_val = int(18 * math.sin(wx * 0.08 + wy * 0.05) + 14 * math.cos(wy * 0.11 - wx * 0.04))
            r_c = max(15, min(95, 34 + w_val))
            g_c = max(65, min(185, 118 + int(w_val * 1.3)))
            b_c = max(95, min(230, 156 + int(w_val * 1.5)))
            pygame.draw.rect(s_water, (r_c, g_c, b_c, 210), (wx, wy, 4, 4))
    for _ in range(36):
        rx, ry = rng.randint(0, S - 28), rng.randint(0, S - 6)
        pygame.draw.line(s_water, (145, 225, 250, 195), (rx, ry), (rx + rng.randint(12, 26), ry + rng.randint(-2, 2)), 2)
    textures['source_water'] = _upload_surf_to_gl_tex(s_water)

    # GM_BigCity High-Rise Glass & Steel Skyscraper Facade
    s_sky = pygame.Surface((S, S), pygame.SRCALPHA)
    s_sky.fill((68, 76, 86, 255))
    for gy in range(8, S, 32):
        pygame.draw.rect(s_sky, (52, 58, 66, 255), (0, gy - 4, S, 4))
        for gx in range(8, S, 24):
            lit = rng.random() < 0.38
            w_col = (145, 182, 210, 255) if lit else (34, 46, 62, 255)
            pygame.draw.rect(s_sky, w_col, (gx, gy, 16, 22))
            pygame.draw.rect(s_sky, (88, 98, 110, 255), (gx, gy, 16, 22), 1)
    textures['bigcity_skyscraper'] = _upload_surf_to_gl_tex(s_sky)

    # Genuine Source Engine Concrete/Asphalt Road (`concretefloor033o` / `hl2_road_asphalt.png`)
    textures['asphalt_road'] = textures['hl2_road_asphalt']

    # Authentic Off-Road Dirt & Soil Texture with tire ruts, clay pebbles, and dust particles
    s_dirt = pygame.Surface((S, S), pygame.SRCALPHA)
    s_dirt.fill((116, 85, 56, 255))
    for _ in range(480):
        dx, dy = rng.randint(0, S - 4), rng.randint(0, S - 4)
        dv = rng.randint(-24, 24)
        r = max(45, min(175, 116 + dv))
        g = max(32, min(142, 85 + int(dv * 0.85)))
        b = max(18, min(112, 56 + int(dv * 0.70)))
        pygame.draw.circle(s_dirt, (r, g, b, 255), (dx, dy), rng.randint(2, 5))
    # Parallel tire track ruts in the dirt soil
    for ty in (60, 80, 176, 196):
        pygame.draw.line(s_dirt, (78, 54, 34, 225), (0, ty), (S, ty), 6)
        pygame.draw.line(s_dirt, (138, 106, 72, 190), (0, ty + 4), (S, ty + 4), 2)
    # Scattered pebbles and sharp stones
    for _ in range(85):
        px, py = rng.randint(0, S - 3), rng.randint(0, S - 3)
        pv = rng.randint(140, 190)
        s_dirt.fill((pv, pv - 10, pv - 25, 255), (px, py, rng.randint(2, 4), rng.randint(2, 3)))
    textures['dirt_offroad'] = _upload_surf_to_gl_tex(s_dirt)

    # Authentic Off-Road Wet Mud & Bog Trail Texture
    s_mud = pygame.Surface((S, S), pygame.SRCALPHA)
    s_mud.fill((66, 48, 34, 255))
    for _ in range(380):
        mx, my = rng.randint(0, S - 5), rng.randint(0, S - 5)
        mv = rng.randint(-18, 18)
        pygame.draw.circle(s_mud, (68 + mv, 48 + mv, 34 + mv, 255), (mx, my), rng.randint(3, 7))
    for _ in range(6):
        pux, puy = rng.randint(25, S - 55), rng.randint(25, S - 55)
        pygame.draw.ellipse(s_mud, (38, 32, 28, 255), (pux, puy, rng.randint(32, 64), rng.randint(16, 32)))
        pygame.draw.ellipse(s_mud, (92, 108, 115, 175), (pux + 4, puy + 3, rng.randint(22, 48), rng.randint(8, 20)))
    textures['mud_trail'] = _upload_surf_to_gl_tex(s_mud)

    # Counter-Strike: Source VTF Textures from content_cstrike_dir.vpk (sourceengine - Copy)
    for css_key, css_file in (
        ('css_truck001a', 'css_truck001a.png'),
        ('css_truck001c', 'css_truck001c.png'),
        ('css_assault_pallet', 'css_assault_pallet.png'),
        ('css_nuke_window', 'css_nuke_window.png'),
        ('css_woodwall031a', 'css_woodwall031a.png'),
    ):
        textures[css_key], _ = load_hl2_or_fallback(css_file, make_fallback_brick((110, 110, 110)))

    WORLD_TEXTURES.clear()
    WORLD_TEXTURES.update(textures)
    return textures


# ═══════════════════════════════════════════════════
#  GENUINE VALVE 3D MODEL LOADER (.OBJ DISPLAY LIST)
# ═══════════════════════════════════════════════════
METROCOP_DLIST = 0
WEAPON_DLISTS = {}
HEV_HAND_TEX_ID = 0

def load_obj_to_display_list(obj_path, texture_id=None):
    """
    Parses a Wavefront .obj file and compiles it into a high-performance OpenGL 1.1 display list.
    Supports vertices, normals, and UV texture coordinates matching Valve Source Engine UVs.
    """
    if not os.path.exists(obj_path):
        return 0
    verts = []
    texcoords = []
    normals = []
    faces = []
    try:
        with open(obj_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                if line.startswith('v '):
                    p = line.strip().split()
                    verts.append((float(p[1]), float(p[2]), float(p[3])))
                elif line.startswith('vt '):
                    p = line.strip().split()
                    texcoords.append((float(p[1]), float(p[2])))
                elif line.startswith('vn '):
                    p = line.strip().split()
                    normals.append((float(p[1]), float(p[2]), float(p[3])))
                elif line.startswith('f '):
                    p = line.strip().split()[1:]
                    face = []
                    for item in p:
                        sub = item.split('/')
                        v_i = int(sub[0]) - 1 if sub[0] else None
                        t_i = int(sub[1]) - 1 if len(sub) > 1 and sub[1] else None
                        n_i = int(sub[2]) - 1 if len(sub) > 2 and sub[2] else None
                        face.append((v_i, t_i, n_i))
                    faces.append(face)
    except Exception as ex:
        print(f"Failed to load OBJ model '{obj_path}': {ex}")
        return 0

    dlist = gl.glGenLists(1)
    gl.glNewList(dlist, GL_COMPILE)
    if texture_id:
        gl.glEnable(GL_TEXTURE_2D)
        gl.glBindTexture(GL_TEXTURE_2D, texture_id)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    else:
        gl.glDisable(GL_TEXTURE_2D)

    gl.glBegin(GL_TRIANGLES)
    for face in faces:
        if len(face) == 3:
            for v_i, t_i, n_i in face:
                if t_i is not None and t_i < len(texcoords):
                    gl.glTexCoord2f(texcoords[t_i][0], texcoords[t_i][1])
                if n_i is not None and n_i < len(normals):
                    nx, ny, nz = normals[n_i]
                    gl.glNormal3f(nx, ny, nz)
                    shade = 0.78 + 0.24 * max(0.0, nx * 0.35 + ny * 0.72 + nz * 0.55)
                    gl.glColor4f(min(1.0, shade), min(1.0, shade), min(1.0, shade), 1.0)
                if v_i is not None and v_i < len(verts):
                    gl.glVertex3f(verts[v_i][0], verts[v_i][1], verts[v_i][2])
    gl.glEnd()

    if texture_id:
        gl.glDisable(GL_TEXTURE_2D)
    gl.glEndList()
    return dlist


GLB_BBOX_CACHE = {}


def load_glb_to_display_list(glb_filename):
    """
    Parses a game-ready glTF 2.0 binary (.glb) model, uploads all embedded PBR textures,
    and compiles all 26 mesh primitives into a high-performance OpenGL display list.
    """
    glb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), glb_filename)
    if not os.path.exists(glb_path):
        glb_path = glb_filename
    if not os.path.exists(glb_path):
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Test files & resources", os.path.basename(glb_filename))
        if os.path.exists(alt_path):
            glb_path = alt_path
        else:
            return 0
    try:
        with open(glb_path, "rb") as f:
            magic, version, length = struct.unpack("<4sII", f.read(12))
            if magic != b"glTF":
                return 0
            chunk0_len, _ = struct.unpack("<II", f.read(8))
            gltf = json.loads(f.read(chunk0_len).decode("utf-8"))
            chunk1_len, _ = struct.unpack("<II", f.read(8))
            bin_buf = f.read(chunk1_len)

        # Upload embedded textures into OpenGL
        textures = {}
        for i, img in enumerate(gltf.get("images", [])):
            bv_idx = img.get("bufferView")
            if bv_idx is not None:
                bv = gltf["bufferViews"][bv_idx]
                off = bv.get("byteOffset", 0)
                blen = bv["byteLength"]
                img_data = bin_buf[off: off + blen]
                try:
                    surf = pygame.image.load(io.BytesIO(img_data)).convert_alpha()
                    textures[i] = _upload_surf_to_gl_tex(surf)
                except Exception:
                    pass

        def get_acc(acc_idx):
            acc = gltf["accessors"][acc_idx]
            bv = gltf["bufferViews"][acc["bufferView"]]
            off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            cnt = acc["count"]
            ctype = acc["componentType"]
            ttype = acc["type"]
            num_c = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[ttype]
            dtypes = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
            dt = dtypes.get(ctype, np.float32)
            stride = bv.get("byteStride")
            if stride is not None and stride != num_c * dt().itemsize:
                raw = bin_buf[off: off + cnt * stride]
                out = np.empty((cnt, num_c), dtype=dt)
                for j in range(cnt):
                    out[j] = np.frombuffer(raw[j * stride: j * stride + num_c * dt().itemsize], dtype=dt)
                return out
            return np.frombuffer(bin_buf[off: off + cnt * num_c * dt().itemsize], dtype=dt).reshape((cnt, num_c) if num_c > 1 else (cnt,))

        nodes = gltf.get("nodes", [])
        meshes = gltf.get("meshes", [])

        def get_node_matrix(node):
            if "matrix" in node:
                return np.array(node["matrix"], dtype=np.float32).reshape((4, 4), order="F")
            m = np.identity(4, dtype=np.float32)
            if "translation" in node:
                t = node["translation"]
                tm = np.identity(4, dtype=np.float32); tm[0:3, 3] = t; m = m @ tm
            if "rotation" in node:
                x, y, z, w = node["rotation"]
                rm = np.array([
                    [1 - 2*y*y - 2*z*z, 2*x*y - 2*z*w, 2*x*z + 2*y*w, 0],
                    [2*x*y + 2*z*w, 1 - 2*x*x - 2*z*z, 2*y*z - 2*x*w, 0],
                    [2*x*z - 2*y*w, 2*y*z + 2*x*w, 1 - 2*x*x - 2*y*y, 0],
                    [0, 0, 0, 1]
                ], dtype=np.float32)
                m = m @ rm
            if "scale" in node:
                s = node["scale"]
                m = m @ np.diag([s[0], s[1], s[2], 1.0]).astype(np.float32)
            return m

        def collect_nodes(node_idx, parent_m):
            node = nodes[node_idx]
            cur_m = parent_m @ get_node_matrix(node)
            items = [(node_idx, node, cur_m)]
            for child_idx in node.get("children", []):
                items.extend(collect_nodes(child_idx, cur_m))
            return items

        scene_nodes = gltf.get("scenes", [{}])[0].get("nodes", [0]) if gltf.get("scenes") else [0]
        all_instances = []
        for r in scene_nodes:
            if r < len(nodes):
                all_instances.extend(collect_nodes(r, np.identity(4, dtype=np.float32)))

        dlist = gl.glGenLists(1)
        gl.glNewList(dlist, GL_COMPILE)
        gl.glEnable(GL_TEXTURE_2D)
        gl.glEnable(GL_DEPTH_TEST)
        gl.glEnable(GL_ALPHA_TEST)
        gl.glAlphaFunc(GL_GREATER, 0.35)

        bbox_min = None
        bbox_max = None

        for nidx, node, world_m in all_instances:
            mesh_idx = node.get("mesh")
            if mesh_idx is None or mesh_idx >= len(meshes):
                continue
            node_name = str(node.get("name", "")).lower()
            mesh = meshes[mesh_idx]
            mesh_name = str(mesh.get("name", "")).lower()

            # Filter out giant terrain/ground planes from building models that clip horizon
            if "city_infrastructure" not in str(glb_filename).lower():
                if "terrain" in node_name or "terrain" in mesh_name or "plane_material.001" in node_name or "plane_material.001" in mesh_name:
                    continue

            for prim in mesh.get("primitives", []):
                attrs = prim.get("attributes", {})
                if "POSITION" not in attrs:
                    continue
                raw_pos = get_acc(attrs["POSITION"])
                pos4 = np.hstack([raw_pos, np.ones((len(raw_pos), 1), dtype=np.float32)])
                trans_pos = (pos4 @ world_m.T)[:, :3]
                if len(trans_pos) > 0:
                    p_min = np.min(trans_pos, axis=0)
                    p_max = np.max(trans_pos, axis=0)
                    bbox_min = p_min if bbox_min is None else np.minimum(bbox_min, p_min)
                    bbox_max = p_max if bbox_max is None else np.maximum(bbox_max, p_max)
                uv = get_acc(attrs["TEXCOORD_0"]) if "TEXCOORD_0" in attrs else None
                indices = get_acc(prim["indices"]) if "indices" in prim else None

                mat_idx = prim.get("material")
                has_tex = False
                if mat_idx is not None and mat_idx < len(gltf.get("materials", [])):
                    mat = gltf["materials"][mat_idx]
                    pbr = mat.get("pbrMetallicRoughness", {})
                    col = pbr.get("baseColorFactor", [1, 1, 1, 1])
                    tex_info = pbr.get("baseColorTexture")
                    if tex_info and tex_info.get("index") is not None:
                        tex_obj = gltf["textures"][tex_info["index"]]
                        tid = textures.get(tex_obj["source"])
                        if tid:
                            gl.glEnable(GL_TEXTURE_2D)
                            gl.glBindTexture(GL_TEXTURE_2D, tid)
                            gl.glColor4f(col[0], col[1], col[2], col[3])
                            has_tex = True
                    if not has_tex:
                        gl.glDisable(GL_TEXTURE_2D)
                        gl.glBindTexture(GL_TEXTURE_2D, 0)
                        gl.glColor4f(col[0], col[1], col[2], col[3])
                else:
                    gl.glDisable(GL_TEXTURE_2D)
                    gl.glBindTexture(GL_TEXTURE_2D, 0)
                    gl.glColor4f(0.85, 0.85, 0.85, 1.0)

                gl.glBegin(GL_TRIANGLES)
                if indices is not None:
                    for vi in indices.flatten():
                        if uv is not None and has_tex:
                            gl.glTexCoord2f(float(uv[vi][0]), 1.0 - float(uv[vi][1]))
                        gl.glVertex3f(float(trans_pos[vi][0]), float(trans_pos[vi][1]), float(trans_pos[vi][2]))
                else:
                    for vi in range(len(trans_pos)):
                        if uv is not None and has_tex:
                            gl.glTexCoord2f(float(uv[vi][0]), 1.0 - float(uv[vi][1]))
                        gl.glVertex3f(float(trans_pos[vi][0]), float(trans_pos[vi][1]), float(trans_pos[vi][2]))
                gl.glEnd()

        gl.glEnable(GL_TEXTURE_2D)
        gl.glBindTexture(GL_TEXTURE_2D, 0)
        gl.glDisable(GL_ALPHA_TEST)
        gl.glEndList()
        if bbox_min is not None and bbox_max is not None:
            center = 0.5 * (bbox_min + bbox_max)
            half_ext = np.maximum(0.5 * (bbox_max - bbox_min), 0.001)
            GLB_BBOX_CACHE[dlist] = (
                (float(center[0]), float(center[1]), float(center[2])),
                (float(half_ext[0]), float(half_ext[1]), float(half_ext[2])),
            )
        return dlist
    except Exception as e:
        print(f"[WARN] Error compiling GLB to display list: {e}")
        return 0


def draw_subdivided_box(cx, cy, cz, w, h, d, r, g, b, a=1.0, divs=5):
    """
    Draws a 3D box at (cx, cy, cz) subdivided into a (divs x divs) grid per face
    so that the VPhysics GPU Vertex Crumple Shader can smoothly dent, buckle, and warp
    interior body panels inwards upon collision.
    """
    hw, hh, hd = w * 0.5, h * 0.5, d * 0.5
    gl.glDisable(GL_TEXTURE_2D)
    gl.glBegin(GL_QUADS)
    step = 1.0 / float(divs)
    for i in range(divs):
        u0 = -1.0 + 2.0 * i * step
        u1 = -1.0 + 2.0 * (i + 1) * step
        for j in range(divs):
            v0 = -1.0 + 2.0 * j * step
            v1 = -1.0 + 2.0 * (j + 1) * step
            # Top (+Y)
            gl.glColor4f(min(1.0, r * 1.12), min(1.0, g * 1.12), min(1.0, b * 1.12), a)
            gl.glNormal3f(0.0, 1.0, 0.0)
            gl.glVertex3f(cx + hw * u0, cy + hh, cz + hd * v0)
            gl.glVertex3f(cx + hw * u0, cy + hh, cz + hd * v1)
            gl.glVertex3f(cx + hw * u1, cy + hh, cz + hd * v1)
            gl.glVertex3f(cx + hw * u1, cy + hh, cz + hd * v0)
            # Bottom (-Y)
            gl.glColor4f(r * 0.55, g * 0.55, b * 0.55, a)
            gl.glNormal3f(0.0, -1.0, 0.0)
            gl.glVertex3f(cx + hw * u0, cy - hh, cz + hd * v0)
            gl.glVertex3f(cx + hw * u1, cy - hh, cz + hd * v0)
            gl.glVertex3f(cx + hw * u1, cy - hh, cz + hd * v1)
            gl.glVertex3f(cx + hw * u0, cy - hh, cz + hd * v1)
            # Right side (+Z)
            gl.glColor4f(r * 0.96, g * 0.96, b * 0.96, a)
            gl.glNormal3f(0.0, 0.0, 1.0)
            gl.glVertex3f(cx + hw * u0, cy + hh * v0, cz + hd)
            gl.glVertex3f(cx + hw * u1, cy + hh * v0, cz + hd)
            gl.glVertex3f(cx + hw * u1, cy + hh * v1, cz + hd)
            gl.glVertex3f(cx + hw * u0, cy + hh * v1, cz + hd)
            # Left side (-Z)
            gl.glColor4f(r * 0.90, g * 0.90, b * 0.90, a)
            gl.glNormal3f(0.0, 0.0, -1.0)
            gl.glVertex3f(cx + hw * u1, cy + hh * v0, cz - hd)
            gl.glVertex3f(cx + hw * u0, cy + hh * v0, cz - hd)
            gl.glVertex3f(cx + hw * u0, cy + hh * v1, cz - hd)
            gl.glVertex3f(cx + hw * u1, cy + hh * v1, cz - hd)
            # Front (+X)
            gl.glColor4f(r * 0.85, g * 0.85, b * 0.85, a)
            gl.glNormal3f(1.0, 0.0, 0.0)
            gl.glVertex3f(cx + hw, cy + hh * v0, cz + hd * u1)
            gl.glVertex3f(cx + hw, cy + hh * v0, cz + hd * u0)
            gl.glVertex3f(cx + hw, cy + hh * v1, cz + hd * u0)
            gl.glVertex3f(cx + hw, cy + hh * v1, cz + hd * u1)
            # Rear (-X)
            gl.glColor4f(r * 0.80, g * 0.80, b * 0.80, a)
            gl.glNormal3f(-1.0, 0.0, 0.0)
            gl.glVertex3f(cx - hw, cy + hh * v0, cz + hd * u0)
            gl.glVertex3f(cx - hw, cy + hh * v0, cz + hd * u1)
            gl.glVertex3f(cx - hw, cy + hh * v1, cz + hd * u1)
            gl.glVertex3f(cx - hw, cy + hh * v1, cz + hd * u0)
    gl.glEnd()


def build_police_cruiser_display_list():
    """
    Compiles a high-detail subdivided 3D MCPD Police Interceptor Cruiser display list (+X forward, +Y up, +Z right):
    - Black & White MCPD Civil Protection Police Livery
    - Heavy steel front PIT Push-Bumper (Bull-Bar), chrome radiator grille, headlights & taillights
    - Open/clear cabin windows with dashboard, steering wheel, MDT computer, and seats (for seated 3D driver)
    - Roof-mounted Red & Blue LED Police Lightbar rack
    - 4 detailed 3D pursuit wheels with radial tires and chrome center hubcaps
    """
    dlist = gl.glGenLists(1)
    gl.glNewList(dlist, GL_COMPILE)
    gl.glDisable(GL_TEXTURE_2D)
    gl.glEnable(GL_DEPTH_TEST)

    # 1. Underbody chassis frame & floorpan
    draw_subdivided_box(0.0, 0.34, 0.0, 4.65, 0.14, 1.78, 0.10, 0.11, 0.13, divs=6)

    # 2. Front Engine Bay & Gloss Black Hood (+X: 0.72 to 2.32)
    draw_subdivided_box(1.52, 0.62, 0.0, 1.60, 0.44, 1.84, 0.09, 0.10, 0.13, divs=6)
    # Hood raised power dome
    draw_subdivided_box(1.48, 0.86, 0.0, 1.44, 0.06, 1.15, 0.11, 0.12, 0.15, divs=5)

    # 3. Rear Trunk Deck & Gloss Black Quarter Panels (-X: -2.35 to -0.85)
    draw_subdivided_box(-1.60, 0.64, 0.0, 1.50, 0.48, 1.84, 0.09, 0.10, 0.13, divs=6)

    # 4. Crisp White Police Doors & Side Sills (X: -0.85 to +0.72)
    # Left Door (-Z) & Right Door (+Z)
    draw_subdivided_box(-0.06, 0.62, -0.86, 1.58, 0.46, 0.14, 0.94, 0.95, 0.97, divs=6)
    draw_subdivided_box(-0.06, 0.62,  0.86, 1.58, 0.46, 0.14, 0.94, 0.95, 0.97, divs=6)
    # Blue & Gold MCPD Police Interceptor badge stripe along both doors
    draw_subdivided_box(-0.06, 0.65, -0.935, 1.48, 0.09, 0.02, 0.10, 0.36, 0.82, divs=4)
    draw_subdivided_box(-0.06, 0.65,  0.935, 1.48, 0.09, 0.02, 0.10, 0.36, 0.82, divs=4)
    draw_subdivided_box(-0.06, 0.58, -0.935, 1.48, 0.03, 0.02, 0.92, 0.76, 0.18, divs=4)
    draw_subdivided_box(-0.06, 0.58,  0.935, 1.48, 0.03, 0.02, 0.92, 0.76, 0.18, divs=4)

    # 5. Interior Cabin: Seats, Dashboard, Steering Wheel & Police MDT Laptop
    # Driver & Passenger Seats
    draw_subdivided_box(-0.18, 0.48, -0.42, 0.48, 0.14, 0.46, 0.16, 0.18, 0.21, divs=2)
    draw_subdivided_box(-0.38, 0.78, -0.42, 0.12, 0.52, 0.44, 0.16, 0.18, 0.21, divs=2)
    draw_subdivided_box(-0.18, 0.48,  0.42, 0.48, 0.14, 0.46, 0.16, 0.18, 0.21, divs=2)
    draw_subdivided_box(-0.38, 0.78,  0.42, 0.12, 0.52, 0.44, 0.16, 0.18, 0.21, divs=2)
    # Rear Prisoner Bench Seat & Partition Cage
    draw_subdivided_box(-0.72, 0.82, 0.0, 0.04, 0.75, 1.56, 0.22, 0.24, 0.28, divs=2)
    # Front Dashboard & Steering Wheel
    draw_subdivided_box(0.56, 0.78, 0.0, 0.28, 0.24, 1.58, 0.14, 0.15, 0.18, divs=3)
    draw_subdivided_box(0.38, 0.85, -0.42, 0.06, 0.26, 0.26, 0.08, 0.09, 0.10, divs=2)
    # Police MDT Terminal Screen on Center Console
    draw_subdivided_box(0.42, 0.86, 0.05, 0.04, 0.16, 0.22, 0.12, 0.68, 0.95, divs=2)

    # 6. Cabin Greenhouse Pillars & White Police Roof (leaving side windows open so seated officer is clearly visible!)
    # Roof Panel (Crisp Police White)
    draw_subdivided_box(-0.14, 1.38, 0.0, 1.42, 0.07, 1.48, 0.95, 0.96, 0.98, divs=5)
    # A-Pillars (Front Windshield Frame)
    for sz in (-0.74, 0.74):
        draw_subdivided_box(0.62, 1.11, sz, 0.10, 0.52, 0.08, 0.12, 0.13, 0.16, divs=3)
    # B-Pillars (Center Door Frame)
    for sz in (-0.78, 0.78):
        draw_subdivided_box(-0.10, 1.11, sz, 0.12, 0.52, 0.08, 0.10, 0.11, 0.14, divs=3)
    # C-Pillars (Rear Window Frame)
    for sz in (-0.74, 0.74):
        draw_subdivided_box(-0.82, 1.11, sz, 0.14, 0.52, 0.08, 0.12, 0.13, 0.16, divs=3)
    # Side Wing Mirrors + Driver Pillar Police Spotlight
    draw_subdivided_box(0.55, 0.92, -0.98, 0.14, 0.10, 0.16, 0.08, 0.09, 0.11, divs=2)
    draw_subdivided_box(0.55, 0.92,  0.98, 0.14, 0.10, 0.16, 0.08, 0.09, 0.11, divs=2)
    draw_subdivided_box(0.64, 1.02, -0.88, 0.14, 0.12, 0.12, 0.85, 0.88, 0.92, divs=2)

    # 7. Front Chrome Grille, Headlight Housings, & Heavy Steel PIT Push-Bumper (Bull-Bar)
    draw_subdivided_box(2.33, 0.62, 0.0, 0.06, 0.26, 0.92, 0.72, 0.75, 0.80, divs=3)
    draw_subdivided_box(2.32, 0.64, -0.66, 0.06, 0.18, 0.34, 0.95, 0.95, 0.88, divs=2)
    draw_subdivided_box(2.32, 0.64,  0.66, 0.06, 0.18, 0.34, 0.95, 0.95, 0.88, divs=2)
    # Front Bumper Beam
    draw_subdivided_box(2.38, 0.42, 0.0, 0.14, 0.18, 1.88, 0.08, 0.09, 0.11, divs=4)
    # Steel Police PIT Push-Bar Uprights & Crossbars
    draw_subdivided_box(2.48, 0.58, -0.38, 0.08, 0.52, 0.07, 0.14, 0.15, 0.18, divs=3)
    draw_subdivided_box(2.48, 0.58,  0.38, 0.08, 0.52, 0.07, 0.14, 0.15, 0.18, divs=3)
    draw_subdivided_box(2.50, 0.72, 0.0, 0.06, 0.06, 0.82, 0.16, 0.17, 0.20, divs=3)
    draw_subdivided_box(2.50, 0.50, 0.0, 0.06, 0.06, 0.82, 0.16, 0.17, 0.20, divs=3)

    # 8. Rear Bumper, Taillight Bezels & Dual Exhausts
    draw_subdivided_box(-2.38, 0.42, 0.0, 0.14, 0.18, 1.88, 0.08, 0.09, 0.11, divs=4)
    draw_subdivided_box(-2.36, 0.66, -0.68, 0.06, 0.18, 0.36, 0.82, 0.08, 0.08, divs=2)
    draw_subdivided_box(-2.36, 0.66,  0.68, 0.06, 0.18, 0.36, 0.82, 0.08, 0.08, divs=2)

    # 9. Roof-Mounted 3D Police Lightbar Assembly (Y = 1.46)
    # Mounting feet
    draw_subdivided_box(-0.08, 1.43, -0.52, 0.18, 0.06, 0.08, 0.20, 0.22, 0.25, divs=2)
    draw_subdivided_box(-0.08, 1.43,  0.52, 0.18, 0.06, 0.08, 0.20, 0.22, 0.25, divs=2)
    # Center chrome/black siren speaker module
    draw_subdivided_box(-0.08, 1.49, 0.0, 0.24, 0.10, 0.26, 0.75, 0.78, 0.82, divs=2)
    # Left Red Police Strobe Dome (-Z)
    draw_subdivided_box(-0.08, 1.49, -0.38, 0.22, 0.09, 0.48, 0.92, 0.10, 0.10, divs=3)
    # Right Blue Police Strobe Dome (+Z)
    draw_subdivided_box(-0.08, 1.49,  0.38, 0.22, 0.09, 0.48, 0.10, 0.38, 0.98, divs=3)

    # 10. 4 Authentic 3D Police Interceptor Wheels (Black Steel Rims + Chrome Center Caps)
    wheel_coords = [
        ( 1.42, 0.36, -0.88),
        ( 1.42, 0.36,  0.88),
        (-1.42, 0.36, -0.88),
        (-1.42, 0.36,  0.88),
    ]
    num_seg = 16
    wr = 0.36
    ww = 0.24
    for wx, wy, wz in wheel_coords:
        # Outer rubber tire cylinder along Z axis
        gl.glColor3f(0.14, 0.14, 0.16)
        gl.glBegin(GL_QUADS)
        for i in range(num_seg):
            a0 = i * (2.0 * math.pi / num_seg)
            a1 = (i + 1) * (2.0 * math.pi / num_seg)
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            gl.glNormal3f((c0 + c1) * 0.5, (s0 + s1) * 0.5, 0.0)
            gl.glVertex3f(wx + wr * c0, wy + wr * s0, wz - ww * 0.5)
            gl.glVertex3f(wx + wr * c0, wy + wr * s0, wz + ww * 0.5)
            gl.glVertex3f(wx + wr * c1, wy + wr * s1, wz + ww * 0.5)
            gl.glVertex3f(wx + wr * c1, wy + wr * s1, wz - ww * 0.5)
        gl.glEnd()
        # Tire sidewalls & steel rim face
        for side_s in (-1.0, 1.0):
            sz_face = wz + side_s * ww * 0.5
            gl.glColor3f(0.18, 0.19, 0.22)
            gl.glBegin(GL_TRIANGLES)
            gl.glNormal3f(0.0, 0.0, side_s)
            for i in range(num_seg):
                a0 = i * (2.0 * math.pi / num_seg)
                a1 = (i + 1) * (2.0 * math.pi / num_seg)
                gl.glVertex3f(wx, wy, sz_face)
                gl.glVertex3f(wx + wr * 0.95 * math.cos(a0), wy + wr * 0.95 * math.sin(a0), sz_face)
                gl.glVertex3f(wx + wr * 0.95 * math.cos(a1), wy + wr * 0.95 * math.sin(a1), sz_face)
            gl.glEnd()
            # Chrome Police Interceptor Hubcap
            sz_cap = sz_face + side_s * 0.012
            gl.glColor3f(0.82, 0.85, 0.90)
            gl.glBegin(GL_TRIANGLES)
            for i in range(12):
                a0 = i * (2.0 * math.pi / 12)
                a1 = (i + 1) * (2.0 * math.pi / 12)
                gl.glVertex3f(wx, wy, sz_cap)
                gl.glVertex3f(wx + wr * 0.34 * math.cos(a0), wy + wr * 0.34 * math.sin(a0), sz_cap)
                gl.glVertex3f(wx + wr * 0.34 * math.cos(a1), wy + wr * 0.34 * math.sin(a1), sz_cap)
            gl.glEnd()

    gl.glEnable(GL_TEXTURE_2D)
    gl.glEndList()
    GLB_BBOX_CACHE[dlist] = (
        (0.0, 0.78, 0.0),
        (2.50, 0.75, 0.98),
    )
    return dlist


# ═══════════════════════════════════════════════════
#  VPHYSICS GPU 3D MESH INWARD CRUMPLE & WARPING SHADER
# ═══════════════════════════════════════════════════
_VPHYSICS_SHADER = {
    "initialized": False,
    "prog": 0,
    "glUseProgram": None,
    "glUniform1f": None,
    "glUniform1i": None,
    "glUniform3f": None,
    "glUniform4fv": None,
    "loc_center": -1,
    "loc_half": -1,
    "loc_crumple": -1,
    "loc_dent_count": -1,
    "loc_dents": -1,
}


def init_vphysics_crumple_shader():
    """
    Compiles and links a GLSL #version 120 GPU Vertex Crumple Shader via WGL that warps
    and crumples 3D vehicle models inwards around collision impact zones in real time
    while preserving fixed-function fragment texturing, alpha-test, and lighting.
    """
    if _VPHYSICS_SHADER["initialized"]:
        return _VPHYSICS_SHADER["prog"]
    _VPHYSICS_SHADER["initialized"] = True
    try:
        from ctypes import c_char_p
        gl.wglGetProcAddress.argtypes = [c_char_p]
        gl.wglGetProcAddress.restype = c_void_p

        def _wgl_proc(name, restype, argtypes):
            addr = gl.wglGetProcAddress(name.encode("ascii"))
            if not addr:
                return None
            return ctypes.WINFUNCTYPE(restype, *argtypes)(addr)

        glCreateShader = _wgl_proc("glCreateShader", c_uint, [c_uint])
        glShaderSource = _wgl_proc("glShaderSource", None, [c_uint, c_int, POINTER(c_char_p), POINTER(c_int)])
        glCompileShader = _wgl_proc("glCompileShader", None, [c_uint])
        glGetShaderiv = _wgl_proc("glGetShaderiv", None, [c_uint, c_uint, POINTER(c_int)])
        glCreateProgram = _wgl_proc("glCreateProgram", c_uint, [])
        glAttachShader = _wgl_proc("glAttachShader", None, [c_uint, c_uint])
        glLinkProgram = _wgl_proc("glLinkProgram", None, [c_uint])
        glGetProgramiv = _wgl_proc("glGetProgramiv", None, [c_uint, c_uint, POINTER(c_int)])
        glUseProgram = _wgl_proc("glUseProgram", None, [c_uint])
        glGetUniformLocation = _wgl_proc("glGetUniformLocation", c_int, [c_uint, c_char_p])
        glUniform1f = _wgl_proc("glUniform1f", None, [c_int, c_float])
        glUniform1i = _wgl_proc("glUniform1i", None, [c_int, c_int])
        glUniform3f = _wgl_proc("glUniform3f", None, [c_int, c_float, c_float, c_float])
        glUniform4fv = _wgl_proc("glUniform4fv", None, [c_int, c_int, POINTER(c_float)])

        if not (glCreateShader and glCreateProgram and glUseProgram and glGetUniformLocation):
            return 0

        vs_source = b"""#version 120
uniform vec3 u_bbox_center;
uniform vec3 u_bbox_half;
uniform float u_total_crumple;
uniform int u_dent_count;
uniform vec4 u_dents[8];

void main() {
    vec4 v = gl_Vertex;
    vec3 safe_half = max(u_bbox_half, vec3(0.001));
    vec3 np = (v.xyz - u_bbox_center) / safe_half;

    // Interior core point that crumpled bodywork collapses toward
    vec3 core = vec3(0.0, -0.15, 0.0);
    vec3 to_core = core - np;

    float inward_factor = 0.0;
    vec3 wrinkle_offset = vec3(0.0);

    for (int i = 0; i < 8; i++) {
        if (i >= u_dent_count) break;
        vec3 d_pos = u_dents[i].xyz;
        float d_sev = u_dents[i].w;
        float dist = length(np - d_pos);
        float radius = 1.05;
        if (dist < radius) {
            float falloff = 1.0 - (dist / radius);
            falloff = falloff * falloff * (3.0 - 2.0 * falloff);
            inward_factor += falloff * d_sev * 0.42;
            float w1 = sin(np.x * 13.0 + np.z * 9.0 + float(i) * 2.1) * cos(np.y * 11.0);
            float w2 = cos(np.z * 15.0 - np.x * 11.0) * sin(np.y * 9.0 + float(i));
            wrinkle_offset += vec3(w1, w2 * 0.7, -w1 * 0.8) * (falloff * d_sev * 0.09);
        }
    }

    if (u_total_crumple > 0.001) {
        float shell_dist = length(np.xz);
        float shell_mask = clamp((shell_dist - 0.25) / 0.75, 0.0, 1.0);
        float height_mask = clamp((np.y + 0.85) / 0.45, 0.25, 1.0);
        float fold = 0.65 + 0.35 * sin(np.x * 10.0) * cos(np.z * 10.0);
        inward_factor += u_total_crumple * shell_mask * height_mask * fold * 0.28;
        wrinkle_offset += vec3(
            sin(np.y * 12.0 + np.z * 8.0),
            cos(np.x * 10.0 + np.z * 10.0) * 0.6,
            sin(np.x * 12.0 - np.y * 8.0)
        ) * (u_total_crumple * shell_mask * 0.07);
    }

    inward_factor = clamp(inward_factor, 0.0, 0.48);
    if (inward_factor > 0.0001) {
        vec3 warped_np = np + to_core * inward_factor + wrinkle_offset;
        warped_np.y = max(warped_np.y, -1.02);
        v.xyz = u_bbox_center + warped_np * safe_half;
    }

    gl_Position = gl_ModelViewProjectionMatrix * v;
    float shade = clamp(1.0 - inward_factor * 0.58, 0.38, 1.0);
    gl_FrontColor = vec4(gl_Color.rgb * shade, gl_Color.a);
    gl_BackColor = gl_FrontColor;
    gl_TexCoord[0] = gl_MultiTexCoord0;
}
"""
        vs = glCreateShader(0x8B31)  # GL_VERTEX_SHADER
        src_ptr = c_char_p(vs_source)
        glShaderSource(vs, 1, byref(src_ptr), None)
        glCompileShader(vs)
        status = c_int(0)
        glGetShaderiv(vs, 0x8B81, byref(status))
        if not status.value:
            return 0

        prog = glCreateProgram()
        glAttachShader(prog, vs)
        glLinkProgram(prog)
        glGetProgramiv(prog, 0x8B82, byref(status))
        if not status.value:
            return 0

        _VPHYSICS_SHADER["prog"] = prog
        _VPHYSICS_SHADER["glUseProgram"] = glUseProgram
        _VPHYSICS_SHADER["glUniform1f"] = glUniform1f
        _VPHYSICS_SHADER["glUniform1i"] = glUniform1i
        _VPHYSICS_SHADER["glUniform3f"] = glUniform3f
        _VPHYSICS_SHADER["glUniform4fv"] = glUniform4fv
        _VPHYSICS_SHADER["loc_center"] = glGetUniformLocation(prog, b"u_bbox_center")
        _VPHYSICS_SHADER["loc_half"] = glGetUniformLocation(prog, b"u_bbox_half")
        _VPHYSICS_SHADER["loc_crumple"] = glGetUniformLocation(prog, b"u_total_crumple")
        _VPHYSICS_SHADER["loc_dent_count"] = glGetUniformLocation(prog, b"u_dent_count")
        _VPHYSICS_SHADER["loc_dents"] = glGetUniformLocation(prog, b"u_dents")
        return prog
    except Exception:
        return 0


def bind_vphysics_crumple_shader(dlist, crumple_amount=0.0, dents=None):
    """Binds the VPhysics GPU Vertex Crumple Shader if the vehicle has taken any collision/weapon damage."""
    dents = dents or []
    if crumple_amount <= 0.0005 and not dents:
        return False
    prog = init_vphysics_crumple_shader()
    if not prog or not _VPHYSICS_SHADER["glUseProgram"]:
        return False
    bbox = GLB_BBOX_CACHE.get(dlist, ((0.0, 0.5, 0.0), (2.0, 0.8, 1.0)))
    cx, cy, cz = bbox[0]
    hx, hy, hz = bbox[1]

    _VPHYSICS_SHADER["glUseProgram"](prog)
    if _VPHYSICS_SHADER["loc_center"] >= 0:
        _VPHYSICS_SHADER["glUniform3f"](_VPHYSICS_SHADER["loc_center"], cx, cy, cz)
    if _VPHYSICS_SHADER["loc_half"] >= 0:
        _VPHYSICS_SHADER["glUniform3f"](_VPHYSICS_SHADER["loc_half"], hx, hy, hz)
    if _VPHYSICS_SHADER["loc_crumple"] >= 0:
        _VPHYSICS_SHADER["glUniform1f"](_VPHYSICS_SHADER["loc_crumple"], float(crumple_amount))

    n_dents = min(8, len(dents))
    if _VPHYSICS_SHADER["loc_dent_count"] >= 0:
        _VPHYSICS_SHADER["glUniform1i"](_VPHYSICS_SHADER["loc_dent_count"], n_dents)
    if n_dents > 0 and _VPHYSICS_SHADER["loc_dents"] >= 0:
        arr = (c_float * (8 * 4))()
        for i in range(n_dents):
            dx, dy, dz, dsev = dents[i]
            arr[i * 4 + 0] = float(dx)
            arr[i * 4 + 1] = float(dy)
            arr[i * 4 + 2] = float(dz)
            arr[i * 4 + 3] = float(dsev)
        _VPHYSICS_SHADER["glUniform4fv"](_VPHYSICS_SHADER["loc_dents"], n_dents, arr)
    return True


def unbind_vphysics_crumple_shader():
    """Restores the standard fixed-function vertex pipeline after rendering a crumpled vehicle."""
    if _VPHYSICS_SHADER["glUseProgram"]:
        _VPHYSICS_SHADER["glUseProgram"](0)


SIGN_MESH_DLIST_CACHE = {}

def load_glb_single_mesh_display_list(glb_filename, target_mesh_idx):
    """
    Extracts and compiles a single isolated mesh primitive from a packed GLB asset collection
    (e.g. road_signs.glb) into its own standalone OpenGL display list with embedded textures.
    """
    cache_key = (glb_filename, target_mesh_idx)
    if cache_key in SIGN_MESH_DLIST_CACHE:
        return SIGN_MESH_DLIST_CACHE[cache_key]

    glb_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), glb_filename)
    if not os.path.exists(glb_path):
        glb_path = glb_filename
    if not os.path.exists(glb_path):
        alt_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Test files & resources", os.path.basename(glb_filename))
        if os.path.exists(alt_path):
            glb_path = alt_path
        else:
            return 0
    try:
        with open(glb_path, "rb") as f:
            magic, version, length = struct.unpack("<4sII", f.read(12))
            chunk0_len, _ = struct.unpack("<II", f.read(8))
            gltf = json.loads(f.read(chunk0_len).decode("utf-8"))
            chunk1_len, _ = struct.unpack("<II", f.read(8))
            bin_buf = f.read(chunk1_len)

        textures = {}
        for i, img in enumerate(gltf.get("images", [])):
            bv_idx = img.get("bufferView")
            if bv_idx is not None:
                bv = gltf["bufferViews"][bv_idx]
                off = bv.get("byteOffset", 0)
                blen = bv["byteLength"]
                img_data = bin_buf[off: off + blen]
                try:
                    surf = pygame.image.load(io.BytesIO(img_data)).convert_alpha()
                    textures[i] = _upload_surf_to_gl_tex(surf)
                except Exception:
                    pass

        def get_acc(acc_idx):
            acc = gltf["accessors"][acc_idx]
            bv = gltf["bufferViews"][acc["bufferView"]]
            off = bv.get("byteOffset", 0) + acc.get("byteOffset", 0)
            cnt = acc["count"]
            ctype = acc["componentType"]
            ttype = acc["type"]
            num_c = {"SCALAR": 1, "VEC2": 2, "VEC3": 3, "VEC4": 4}[ttype]
            dtypes = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
            dt = dtypes.get(ctype, np.float32)
            stride = bv.get("byteStride")
            if stride is not None and stride != num_c * dt().itemsize:
                raw = bin_buf[off: off + cnt * stride]
                out = np.empty((cnt, num_c), dtype=dt)
                for j in range(cnt):
                    out[j] = np.frombuffer(raw[j * stride: j * stride + num_c * dt().itemsize], dtype=dt)
                return out
            return np.frombuffer(bin_buf[off: off + cnt * num_c * dt().itemsize], dtype=dt).reshape((cnt, num_c) if num_c > 1 else (cnt,))

        meshes = gltf.get("meshes", [])
        if target_mesh_idx >= len(meshes):
            return 0
        mesh = meshes[target_mesh_idx]

        dlist = gl.glGenLists(1)
        gl.glNewList(dlist, GL_COMPILE)
        gl.glEnable(GL_TEXTURE_2D)
        gl.glEnable(GL_DEPTH_TEST)
        gl.glEnable(GL_ALPHA_TEST)
        gl.glAlphaFunc(GL_GREATER, 0.35)

        for prim in mesh.get("primitives", []):
            attrs = prim.get("attributes", {})
            if "POSITION" not in attrs:
                continue
            raw_pos = get_acc(attrs["POSITION"])
            uv = get_acc(attrs["TEXCOORD_0"]) if "TEXCOORD_0" in attrs else None
            indices = get_acc(prim["indices"]) if "indices" in prim else None

            mat_idx = prim.get("material")
            has_tex = False
            if mat_idx is not None and mat_idx < len(gltf.get("materials", [])):
                mat = gltf["materials"][mat_idx]
                pbr = mat.get("pbrMetallicRoughness", {})
                col = pbr.get("baseColorFactor", [1, 1, 1, 1])
                tex_info = pbr.get("baseColorTexture")
                if tex_info and tex_info.get("index") is not None:
                    tex_obj = gltf["textures"][tex_info["index"]]
                    tid = textures.get(tex_obj["source"])
                    if tid:
                        gl.glEnable(GL_TEXTURE_2D)
                        gl.glBindTexture(GL_TEXTURE_2D, tid)
                        gl.glColor4f(col[0], col[1], col[2], col[3])
                        has_tex = True
                if not has_tex:
                    gl.glDisable(GL_TEXTURE_2D)
                    gl.glBindTexture(GL_TEXTURE_2D, 0)
                    gl.glColor4f(col[0], col[1], col[2], col[3])
            else:
                gl.glDisable(GL_TEXTURE_2D)
                gl.glBindTexture(GL_TEXTURE_2D, 0)
                gl.glColor4f(0.85, 0.85, 0.85, 1.0)

            gl.glBegin(GL_TRIANGLES)
            if indices is not None:
                for vi in indices.flatten():
                    if uv is not None and has_tex:
                        gl.glTexCoord2f(float(uv[vi][0]), 1.0 - float(uv[vi][1]))
                    gl.glVertex3f(float(raw_pos[vi][0]), float(raw_pos[vi][1]), float(raw_pos[vi][2]))
            else:
                for vi in range(len(raw_pos)):
                    if uv is not None and has_tex:
                        gl.glTexCoord2f(float(uv[vi][0]), 1.0 - float(uv[vi][1]))
                    gl.glVertex3f(float(raw_pos[vi][0]), float(raw_pos[vi][1]), float(raw_pos[vi][2]))
            gl.glEnd()

        gl.glEnable(GL_TEXTURE_2D)
        gl.glBindTexture(GL_TEXTURE_2D, 0)
        gl.glDisable(GL_ALPHA_TEST)
        gl.glEndList()
        SIGN_MESH_DLIST_CACHE[cache_key] = dlist
        return dlist
    except Exception as e:
        print(f"[WARN] Error compiling single GLB mesh: {e}")
        return 0


def draw_3d_chainlink_checkpoint(x, z, yaw_deg, tex_fence, has_gate=True):
    """
    Renders the Half-Life 2 Point Insertion chain-link security fence checkpoint with
    galvanized steel pipe frames, angled 3-strand barbed-wire tops, and Combine camera (Screenshot 2).
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)
    pipe_c = (0.46, 0.49, 0.50)

    sections = [(-1.35, 1.1), (1.35, 1.1)] if has_gate else [(-1.1, 1.1), (0.0, 1.1), (1.1, 1.1)]
    for sx, sw in sections:
        gl.glPushMatrix()
        gl.glTranslatef(sx, 1.15, 0.0)
        # Galvanized vertical posts
        for side in (-sw * 0.5, sw * 0.5):
            gl.glPushMatrix()
            gl.glTranslatef(side, 0.0, 0.0)
            draw_box(0.05, 2.3, 0.05, *pipe_c)
            # Angled barbed-wire extension arm at top (Screenshot 2 signature detail)
            gl.glTranslatef(0.0, 1.22, 0.12)
            gl.glRotatef(35.0, 1.0, 0.0, 0.0)
            draw_box(0.035, 0.42, 0.035, *pipe_c)
            gl.glPopMatrix()
        # Top & middle horizontal rail pipes
        for ry in (1.12, 0.0, -1.10):
            gl.glPushMatrix()
            gl.glTranslatef(0.0, ry, 0.0)
            draw_box(sw, 0.04, 0.04, *pipe_c)
            gl.glPopMatrix()
        # 3 strands of taut barbed wire along angled top brackets
        for bz, by in ((0.06, 1.22), (0.14, 1.30), (0.22, 1.38)):
            gl.glPushMatrix()
            gl.glTranslatef(0.0, by, bz)
            draw_box(sw, 0.015, 0.015, 0.35, 0.37, 0.38)
            gl.glPopMatrix()
        # See-through diamond wire mesh panel with hardware alpha test so holes never block background depth
        gl.glEnable(GL_ALPHA_TEST)
        gl.glAlphaFunc(GL_GREATER, 0.25)
        draw_textured_quad_panel(sw - 0.06, 2.2, tex_fence, u_rep=2.5, v_rep=4.0, r=0.82, g=0.85, b=0.86, a=0.95)
        gl.glDisable(GL_ALPHA_TEST)
        gl.glPopMatrix()

    # Overhead checkpoint crossbar & glowing green Combine security camera (Screenshot 2)
    if has_gate:
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 2.28, 0.0)
        draw_box(1.65, 0.06, 0.06, *pipe_c)
        # Black checkpoint sign plate
        gl.glPushMatrix()
        gl.glTranslatef(-0.55, -0.45, 0.03)
        draw_box(0.42, 0.22, 0.03, 0.10, 0.10, 0.12)
        gl.glPopMatrix()
        # Combine security camera with glowing green optic
        gl.glTranslatef(0.65, -0.18, 0.14)
        draw_box(0.14, 0.14, 0.26, 0.18, 0.20, 0.22)
        gl.glTranslatef(0.0, -0.02, 0.14)
        draw_box(0.07, 0.07, 0.04, 0.15, 1.0, 0.25)
        gl.glPopMatrix()

    gl.glPopMatrix()


def draw_3d_breencast_screen(x, y, z, yaw_deg, tex_breen):
    """
    Renders the giant glowing cyan Dr. Wallace Breen propaganda monitor mounted high on
    City-17 walls and tilted downward toward the street/checkpoint (Screenshot 2).
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, y, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)
    gl.glRotatef(10.0, 1.0, 0.0, 0.0)  # Slight downward tilt like Screenshot 2
    # Heavy dark Combine steel casing & mounting brackets
    draw_box(1.55, 2.95, 0.16, 0.12, 0.15, 0.18)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.0, 0.09)
    draw_textured_quad_panel(1.42, 2.80, tex_breen, u_rep=1.0, v_rep=1.0, r=0.92, g=1.0, b=1.0, a=1.0)
    gl.glPopMatrix()
    gl.glPopMatrix()


def draw_3d_conical_turret(x, base_y, z, tex_yellow, tex_slate):
    """
    Renders the iconic City-17 cylindrical/octagonal corner building turret with a steep
    dark-slate conical spire roof and tall finial needle from Screenshot 3.
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, base_y, z)
    # Octagonal yellow neoclassical tower drum
    for ang_deg in (0.0, 45.0):
        gl.glPushMatrix()
        gl.glRotatef(ang_deg, 0.0, 1.0, 0.0)
        draw_textured_box(0.95, 1.6, 0.95, tex_yellow, u_rep=1.0, v_rep=1.0, r=1.0, g=0.98, b=0.90)
        gl.glPopMatrix()
    # Stone cornice ring
    gl.glTranslatef(0.0, 0.84, 0.0)
    draw_box(1.12, 0.10, 1.12, 0.62, 0.58, 0.48)
    # Steep multi-tiered dark slate conical spire roof (Screenshot 3 skyline centerpiece)
    tier_Data = [(0.96, 0.45), (0.76, 0.45), (0.56, 0.45), (0.38, 0.45), (0.20, 0.45)]
    for tw, th in tier_Data:
        gl.glTranslatef(0.0, th * 0.85, 0.0)
        for ang_deg in (0.0, 45.0):
            gl.glPushMatrix()
            gl.glRotatef(ang_deg, 0.0, 1.0, 0.0)
            draw_textured_box(tw, th, tw, tex_slate, u_rep=1.0, v_rep=1.0, r=0.45, g=0.48, b=0.54)
            gl.glPopMatrix()
    # Tall iron lightning finial spire at apex
    gl.glTranslatef(0.0, 0.65, 0.0)
    draw_box(0.035, 1.10, 0.035, 0.18, 0.20, 0.22)
    gl.glPopMatrix()


def draw_3d_shop_awning(x, z, yaw_deg, tex_awning, sign_type=0):
    """
    Renders the weathered corrugated rusty metal shopfront awning, iron support brackets,
    and red/blue European shop signage ('Teräs' / 'Café') from Screenshot 3.
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, 1.55, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)
    # Sloped corrugated metal canopy
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.0, 0.32)
    gl.glRotatef(22.0, 1.0, 0.0, 0.0)
    draw_textured_box(0.98, 0.05, 0.62, tex_awning, u_rep=1.0, v_rep=1.0, r=0.95, g=0.88, b=0.82)
    gl.glPopMatrix()
    # Vertical weathered billboard above awning (left building in Screenshot 3)
    if sign_type == 0:
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.42, 0.52)
        draw_textured_box(0.92, 0.58, 0.04, tex_awning, u_rep=1.0, v_rep=1.0, r=0.82, g=0.78, b=0.72)
        gl.glPopMatrix()
    elif sign_type == 1:
        # Red "Teräs" shop sign banner
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.26, 0.04)
        draw_box(0.88, 0.36, 0.03, 0.62, 0.12, 0.10)
        draw_box(0.68, 0.12, 0.04, 0.85, 0.72, 0.18)
        gl.glPopMatrix()
    else:
        # Blue "Café" sign banner
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.26, 0.04)
        draw_box(0.76, 0.34, 0.03, 0.14, 0.24, 0.58)
        draw_box(0.52, 0.12, 0.04, 0.92, 0.92, 0.95)
        gl.glPopMatrix()
    gl.glPopMatrix()


def draw_3d_sandbag_bunker(x, z, yaw_deg, tex_sandbag):
    """Renders a 3D curved/stacked sandbag barricade."""
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.34, 0.0)
    draw_textured_box(1.45, 0.68, 0.42, tex_sandbag, u_rep=2.0, v_rep=1.0)
    gl.glPopMatrix()
    for side in (-1, 1):
        gl.glPushMatrix()
        gl.glTranslatef(side * 0.78, 0.28, -0.22)
        gl.glRotatef(side * 32.0, 0.0, 1.0, 0.0)
        draw_textured_box(0.65, 0.56, 0.38, tex_sandbag, u_rep=1.0, v_rep=1.0)
        gl.glPopMatrix()
    gl.glPopMatrix()


def draw_3d_czech_hedgehog(x, z, yaw_deg=0.0):
    """Renders an iconic 3-beam crossed steel anti-tank obstacle."""
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.48, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)
    steel_c = (0.28, 0.26, 0.24)
    for rx, ry, rz in ((45.0, 0.0, 35.0), (-45.0, 60.0, -35.0), (35.0, 120.0, -45.0)):
        gl.glPushMatrix()
        gl.glRotatef(ry, 0.0, 1.0, 0.0)
        gl.glRotatef(rx, 1.0, 0.0, 0.0)
        gl.glRotatef(rz, 0.0, 0.0, 1.0)
        draw_box(0.11, 1.25, 0.11, *steel_c)
        gl.glPopMatrix()
    draw_box(0.24, 0.24, 0.24, 0.22, 0.20, 0.18)
    gl.glPopMatrix()


def draw_3d_rubble_crater(x, z):
    """Renders a street rubble pile & concrete debris."""
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.02, z)
    draw_box(1.3, 0.03, 1.3, 0.18, 0.17, 0.16)
    for ang_i in range(6):
        ang = ang_i * (math.pi / 3.0) + 0.3
        rx, rz = math.cos(ang) * 0.58, math.sin(ang) * 0.58
        gl.glPushMatrix()
        gl.glTranslatef(rx, 0.11, rz)
        gl.glRotatef(ang_i * 37.0, 0.3, 1.0, 0.2)
        draw_box(0.34, 0.20, 0.26, 0.48, 0.46, 0.42)
        gl.glPopMatrix()
    gl.glPopMatrix()


def draw_3d_combine_barricade(x, z, yaw_deg, tex_barricade):
    """
    Renders the iconic Half-Life 2 angled Combine armored street barricade (`props_combine/combine_barricade_short01a`)
    with dark Citadel steel plates, rear support struts, yellow hazard trim, and glowing blue Combine lock core.
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)

    # Base heavy steel anchor plate
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.08, 0.0)
    draw_box(1.48, 0.16, 0.62, 0.16, 0.19, 0.24)
    gl.glPopMatrix()

    # Angled forward Combine armor shield
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.58, 0.08)
    gl.glRotatef(-18.0, 1.0, 0.0, 0.0)
    if tex_barricade:
        draw_textured_box(1.42, 1.05, 0.22, tex_barricade, u_rep=1.0, v_rep=1.0, r=0.88, g=0.92, b=0.98)
    else:
        draw_box(1.42, 1.05, 0.22, 0.22, 0.27, 0.35)
    # Glowing cyan Combine status core & yellow hazard chevron bar
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.18, 0.12)
    draw_box(0.22, 0.22, 0.04, 0.15, 0.85, 1.0)
    gl.glTranslatef(0.0, 0.24, 0.0)
    draw_box(1.36, 0.09, 0.03, 0.92, 0.72, 0.12)
    gl.glPopMatrix()
    gl.glPopMatrix()

    # Rear diagonal hydraulic brace struts
    for sx in (-0.52, 0.52):
        gl.glPushMatrix()
        gl.glTranslatef(sx, 0.42, -0.18)
        gl.glRotatef(32.0, 1.0, 0.0, 0.0)
        draw_box(0.12, 0.82, 0.12, 0.14, 0.16, 0.20)
        gl.glPopMatrix()

    gl.glPopMatrix()


def draw_3d_entry_light(x, z, yaw_deg=0.0, tex_light=None, sim_time=0.0):
    """
    Renders a Half-Life 2 Combine Checkpoint Entry Light / Street Lamp Post (`props_c17/light_domelight02_on`)
    with dark steel post, dual armored floodlight heads, glowing bulb dome, and warm ground light pool.
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)

    # Heavy octagonal iron base & stanchion post
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.22, 0.0)
    draw_box(0.28, 0.44, 0.28, 0.16, 0.18, 0.21)
    gl.glTranslatef(0.0, 1.35, 0.0)
    draw_box(0.10, 2.70, 0.10, 0.20, 0.22, 0.25)
    gl.glPopMatrix()

    # Cross-arm bracket & Combine Entry Light Fixture at top (y = 2.85)
    pulse = 0.92 + 0.08 * math.sin(sim_time * 6.0 + x + z)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 2.85, 0.0)
    draw_box(0.18, 0.14, 0.68, 0.24, 0.26, 0.30)
    # Forward overhanging entry light hood
    gl.glTranslatef(0.0, -0.06, 0.28)
    draw_box(0.36, 0.10, 0.36, 0.18, 0.20, 0.24)
    # Glowing entry light bulb dome
    gl.glTranslatef(0.0, -0.08, 0.0)
    if tex_light:
        draw_textured_box(0.26, 0.14, 0.26, tex_light, u_rep=1.0, v_rep=1.0, r=1.0 * pulse, g=0.94 * pulse, b=0.72 * pulse)
    else:
        draw_box(0.26, 0.14, 0.26, 1.0 * pulse, 0.92 * pulse, 0.68 * pulse)
    # Secondary Combine cyan beacon LED on top of housing
    gl.glTranslatef(0.0, 0.22, 0.0)
    draw_box(0.10, 0.08, 0.10, 0.20, 0.88, 1.0)
    gl.glPopMatrix()

    # Soft illuminated light pool on the street below
    gl.glEnable(GL_BLEND)
    gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.015, 0.25)
    draw_box(1.65, 0.01, 1.65, 1.0, 0.90, 0.62, 0.22 * pulse)
    draw_box(0.95, 0.012, 0.95, 1.0, 0.95, 0.78, 0.32 * pulse)
    gl.glPopMatrix()
    gl.glDisable(GL_BLEND)

    gl.glPopMatrix()


# ═══════════════════════════════════════════════════
#  CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════
TITLE = "TBMG_Country_MainCity2 — 2007 WARFARE EDITION [CoD × Half-Life 2]"
SCREEN_W = 1280
SCREEN_H = 720
MAX_DEPTH = 48.0
FPS = 60
MOUSE_SENS = 0.0026
MOVE_SPEED = 4.3
SPRINT_SPEED = 7.8

# Colors (RGB 0-255 for HUD)
COL_FLOOR = (20, 18, 22)
COL_CEILING = (8, 8, 14)
COL_GREEN = (76, 254, 76)
COL_ORANGE = (255, 140, 0)
COL_RED = (255, 32, 32)
COL_BLUE = (85, 153, 255)
COL_PURPLE = (136, 0, 255)
COL_PINK = (255, 0, 255)
COL_WHITE = (255, 255, 255)
COL_DARKBG = (10, 10, 15)
COL_YELLOW = (255, 230, 50)
COL_CYAN = (50, 220, 255)
SOUND_RANGE = 18.0

# ═══════════════════════════════════════════════════
#  LORE & WORLD DATA
# ═══════════════════════════════════════════════════
LORE_TEXT = [
    "--- TBMG COUNTRY LORE BREAKDOWN ---",
    "1. Overview:",
    "   - Defined by extreme chaos, radical freedom, and harsh rules. No one knows what 'TBMG' stands for.",
    "   - Main city is a lawless disaster area with daily explosions.",
    "   - Countryside is peaceful and safe.",
    "   - Explosions created glowing plants and Cinder Foxes, though it became a barren wasteland later.",
    "",
    "2. Leadership:",
    "   - Corrupt government. Power is passed down to families.",
    "   - President max term: 50 years.",
    "   - President Tim: Unstable, rules via paranoia, brought back radical freedoms like Photoshop.",
    "   - President Michael: Brutal. Illegal to speak badly about government; punished by draining joyful memories.",
    "   - Dark Leader / The Vampire: True power. Never takes an oath, unknown age, never raises his voice.",
    "",
    "3. Law Enforcement:",
    "   - Main City Police Department (MCPD) operates like a criminal syndicate (FBI investigated).",
    "   - MCPD is trigger-happy: bumping into them gets you shot instantly.",
    "   - Rank is based on kill count. MCPD kills ~2 million people every day.",
    "   - Elite Combine Protection Units (ECPU) outrank all. Opaque helmets, no warnings, always shoot.",
    "",
    "4. Bizarre Laws & Culture:",
    "   - Jaywalking: drivers are encouraged to run over jaywalkers.",
    "   - Church: Secretly illegal to shoot a bullet inside (736,000-star wanted level).",
    "   - Events: 'Rubber Ducky Battle' and 'Pink Day' (45% must buy pink paint).",
    "   - Survival Guide: Must carry 4 Billion Mountain Dew bottles to look cool.",
]

# ═══════════════════════════════════════════════════
#  MAP DATA — MainCity2 (Fused Multi-Map Source Engine Mega-World: City-17 + gm_bigcity + BigCity5 Highway)
#  Cell legend:
#   0 = Open street / plaza / highway
#   1..5 = Building blocks / High-rise skyscrapers / Combine barriers
#   6 = Checkpoint gate / door
#   7 = Source Engine Water Canal / Pool (vphysics buoyancy + swimming)
# ═══════════════════════════════════════════════════
MAP_MAINCITY2 = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 4, 4, 4, 4, 4, 4, 4, 4, 4, 4, 6, 6, 6, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 5, 0, 0, 0, 0, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 4, 4, 4, 4, 0, 0, 1],
    [1, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 4, 4, 4, 4, 0, 0, 1],
    [1, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 1],
    [1, 0, 2, 2, 2, 2, 2, 0, 0, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# gm_bigcity — Garry's Mod / Source Engine iconic urban sandbox map:
# Wide asphalt avenues, towering Twin Towers / high-rise glass skyscrapers (2, 3, 5),
# industrial brick warehouses (1, 4), and a large Source Engine Water Canal & Harbor Basin (7).
MAP_GM_BIGCITY = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 1],
    [1, 0, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 5, 5, 5, 5, 5, 5, 5, 5, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 1],
    [1, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 1],
    [1, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 1],
    [1, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 0, 0, 0, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 7, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 1],
    [1, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 1],
    [1, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 1],
    [1, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 1],
    [1, 0, 3, 3, 3, 3, 3, 3, 3, 3, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

# Big City 5 (BigCity5) — 48x48 Urban Infrastructure & Highway Network
# Features central elevated highway viaduct & ramps, 3D Destroyed High-Rise,
# 3D Industrial Utility Complex, empty parking lot with vehicle spawner depot, and wide avenues.
MAP_BIGCITY5 = [
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 2, 2, 2, 2, 2, 2, 2, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 4, 4, 4, 4, 4, 4, 4, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1],
    [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
]

MAP_DRIVING_TEST = [
    [1 if (r == 0 or r == 47 or c == 0 or c == 47) else 0 for c in range(48)]
    for r in range(48)
]

MAP = [row[:] for row in MAP_MAINCITY2]
MAP_H = len(MAP)
MAP_W = len(MAP[0])

# Default 3D Half-Life 2 Fences, Combine Barriers, Entry Lights, Checkpoints & Props per map
DEFAULT_PLACED_OBJECTS = {
    "MainCity2": [
        # Classic City-17 Checkpoints & Lighting
        {"type": "combine_barrier", "x": 14.5, "y": 11.5, "yaw": 0.0},
        {"type": "combine_barrier", "x": 19.5, "y": 11.5, "yaw": 90.0},
        {"type": "combine_barrier", "x": 25.5, "y": 12.0, "yaw": 90.0},
        {"type": "entry_light", "x": 9.5, "y": 10.5, "yaw": 0.0},
        {"type": "entry_light", "x": 15.5, "y": 10.5, "yaw": 0.0},
        {"type": "entry_light", "x": 21.0, "y": 10.2, "yaw": 270.0},
        {"type": "entry_light", "x": 21.0, "y": 13.8, "yaw": 270.0},
        {"type": "entry_light", "x": 11.5, "y": 4.2, "yaw": 180.0},
        {"type": "fence", "x": 8.5, "y": 14.8, "yaw": 0.0},
        # Genuine Source Engine VTF Props & Stations in City-17 Plaza
        {"type": "vending_machine", "x": 15.2, "y": 13.5, "yaw": 180.0},
        {"type": "health_station", "x": 16.6, "y": 13.5, "yaw": 180.0},
        {"type": "suit_charger", "x": 17.6, "y": 13.5, "yaw": 180.0},
        {"type": "ammo_crate", "x": 16.2, "y": 14.8, "yaw": 0.0},
        {"type": "gas_canister", "x": 17.4, "y": 14.8, "yaw": 25.0},
        {"type": "park_bench", "x": 8.8, "y": 12.0, "yaw": 90.0},
        {"type": "park_bench", "x": 14.2, "y": 12.0, "yaw": 270.0},
        {"type": "dumpster", "x": 4.5, "y": 12.5, "yaw": 90.0},
        {"type": "metal_locker", "x": 3.2, "y": 8.5, "yaw": 90.0},
        {"type": "power_generator", "x": 20.5, "y": 8.2, "yaw": 0.0},
        # Northeast Freight & Container Yard (NorthernPetrol Cargo Containers & Pallets)
        {"type": "cargo_container", "x": 28.5, "y": 10.5, "yaw": 90.0},
        {"type": "cargo_container", "x": 34.5, "y": 10.5, "yaw": 90.0},
        {"type": "pallet_stack", "x": 26.2, "y": 10.5, "yaw": 15.0},
        {"type": "wooden_pallet", "x": 31.5, "y": 11.2, "yaw": 0.0},
        {"type": "cardboard_box", "x": 31.5, "y": 11.2, "z": 0.20, "yaw": 10.0},
        # South Highway District Barriers & Street Furniture
        {"type": "concrete_jersey", "x": 10.5, "y": 24.2, "yaw": 0.0},
        {"type": "concrete_jersey", "x": 24.5, "y": 24.2, "yaw": 0.0},
        {"type": "dumpster", "x": 9.5, "y": 31.8, "yaw": 0.0},
    ],
    "gm_bigcity": [
        {"type": "combine_barrier", "x": 16.5, "y": 17.2, "yaw": 0.0},
        {"type": "combine_barrier", "x": 21.5, "y": 17.2, "yaw": 0.0},
        {"type": "entry_light", "x": 15.5, "y": 17.5, "yaw": 0.0},
        {"type": "entry_light", "x": 23.5, "y": 17.5, "yaw": 0.0},
        {"type": "entry_light", "x": 18.5, "y": 10.5, "yaw": 180.0},
        {"type": "checkpoint_gate", "x": 19.0, "y": 21.5, "yaw": 0.0},
        {"type": "fence", "x": 14.5, "y": 10.8, "yaw": 0.0},
    ],
    "BigCity5": [],
    "driving Test map": [],
}

PROP_COLLISION_DATA = {
    # Vertical Architecture / Walkable surfaces
    "stairs_metal": {"shape": "ramp", "w": 1.6, "d": 3.2, "h": 2.8, "walkable": True},
    "stairs_wood": {"shape": "ramp", "w": 1.6, "d": 3.2, "h": 2.8, "walkable": True},
    "metal_ramp": {"shape": "ramp", "w": 1.8, "d": 3.4, "h": 2.8, "walkable": True},
    "scaffolding": {"shape": "platform", "w": 2.6, "d": 2.6, "h": 3.2, "walkable": True},
    "second_story_floor": {"shape": "platform", "w": 3.2, "d": 3.2, "h": 3.0, "walkable": True},
    "roof_walkway": {"shape": "platform", "w": 1.6, "d": 3.2, "h": 3.0, "walkable": True},
    "ladder": {"shape": "box", "w": 0.6, "d": 0.25, "h": 3.2},

    # Fences & Barricades (Thinner collision profile allows navigating 1-block corridors & openings)
    "fence": {"shape": "box", "w": 2.2, "d": 0.08, "h": 2.4},
    "chain_fence": {"shape": "box", "w": 2.2, "d": 0.08, "h": 2.4},
    "checkpoint_gate": {"shape": "gate", "w": 2.8, "d": 0.16, "h": 2.5, "open_w": 1.6, "walkable": True},
    "combine_barrier": {"shape": "box", "w": 1.2, "d": 0.10, "h": 1.4},
    "tall_combine_wall": {"shape": "box", "w": 2.2, "d": 0.16, "h": 4.0},
    "sandbag": {"shape": "box", "w": 1.4, "d": 0.16, "h": 1.1},
    "hedgehog": {"shape": "cylinder", "r": 0.45, "w": 0.9, "d": 0.9, "h": 1.3},
    "concrete_jersey": {"shape": "box", "w": 1.6, "d": 0.14, "h": 1.0},
    "concrete_barricade": {"shape": "box", "w": 1.6, "d": 0.14, "h": 1.0},
    "wooden_barricade": {"shape": "box", "w": 1.4, "d": 0.12, "h": 1.4},
    "razorwire": {"shape": "box", "w": 1.8, "d": 0.18, "h": 1.0},

    # Street Furniture & Props
    "entry_light": {"shape": "cylinder", "r": 0.35, "w": 0.7, "d": 0.7, "h": 3.5},
    "dumpster": {"shape": "box", "w": 2.0, "d": 1.3, "h": 1.4},
    "trash_can": {"shape": "cylinder", "r": 0.40, "w": 0.8, "d": 0.8, "h": 1.0},
    "vending_machine": {"shape": "box", "w": 1.1, "d": 0.85, "h": 2.1},
    "phone_booth": {"shape": "box", "w": 1.0, "d": 1.0, "h": 2.4},
    "park_bench": {"shape": "box", "w": 1.6, "d": 0.65, "h": 0.9},
    "fire_hydrant": {"shape": "cylinder", "r": 0.30, "w": 0.6, "d": 0.6, "h": 0.8},
    "traffic_cone": {"shape": "cylinder", "r": 0.30, "w": 0.6, "d": 0.6, "h": 0.75},
    "street_sign": {"shape": "cylinder", "r": 0.20, "w": 0.4, "d": 0.4, "h": 2.8},
    "manhole": {"shape": "none", "w": 1.0, "d": 1.0, "h": 0.05},

    # Industrial & Tech
    "breencast": {"shape": "box", "w": 2.6, "d": 0.50, "h": 2.2},
    "combine_terminal": {"shape": "box", "w": 0.9, "d": 0.70, "h": 1.4},
    "power_generator": {"shape": "box", "w": 1.8, "d": 1.20, "h": 1.4},
    "transformer_box": {"shape": "box", "w": 1.2, "d": 0.90, "h": 1.6},
    "fuel_tank": {"shape": "box", "w": 2.4, "d": 1.30, "h": 1.5},
    "ventilation_duct": {"shape": "box", "w": 2.2, "d": 1.00, "h": 1.0},
    "pipes_cluster": {"shape": "box", "w": 1.6, "d": 0.40, "h": 2.6},
    "satellite_dish": {"shape": "cylinder", "r": 0.80, "w": 1.6, "d": 1.6, "h": 1.8},
    "security_camera": {"shape": "cylinder", "r": 0.30, "w": 0.6, "d": 0.6, "h": 0.4},
    "floodlight": {"shape": "cylinder", "r": 0.40, "w": 0.8, "d": 0.8, "h": 2.2},

    # Interior Furniture & Warehouse
    "metal_table": {"shape": "box", "w": 1.6, "d": 0.90, "h": 0.9},
    "wooden_chair": {"shape": "box", "w": 0.55, "d": 0.55, "h": 0.9},
    "metal_locker": {"shape": "box", "w": 0.9, "d": 0.60, "h": 2.0},
    "wooden_shelf": {"shape": "box", "w": 1.4, "d": 0.55, "h": 2.0},
    "metal_crate": {"shape": "box", "w": 1.2, "d": 1.20, "h": 1.2},
    "wooden_pallet": {"shape": "box", "w": 1.3, "d": 1.10, "h": 0.22},
    "pallet_stack": {"shape": "box", "w": 1.3, "d": 1.10, "h": 0.85},
    "cardboard_box": {"shape": "box", "w": 0.9, "d": 0.90, "h": 0.9},
    "radio_receiver": {"shape": "box", "w": 0.6, "d": 0.40, "h": 0.5},
    "file_cabinet": {"shape": "box", "w": 0.6, "d": 0.70, "h": 1.4},

    # Storage & Hazards
    "barrel": {"shape": "cylinder", "r": 0.42, "w": 0.84, "d": 0.84, "h": 1.1},
    "explosive_barrel": {"shape": "cylinder", "r": 0.42, "w": 0.84, "d": 0.84, "h": 1.1},
    "toxic_barrel": {"shape": "cylinder", "r": 0.42, "w": 0.84, "d": 0.84, "h": 1.1},
    "water_drum": {"shape": "cylinder", "r": 0.50, "w": 1.0, "d": 1.0, "h": 1.2},
    "gas_canister": {"shape": "cylinder", "r": 0.30, "w": 0.6, "d": 0.6, "h": 1.3},
    "ammo_crate": {"shape": "box", "w": 0.9, "d": 0.60, "h": 0.45},
    "health_station": {"shape": "box", "w": 0.6, "d": 0.35, "h": 0.9},
    "suit_charger": {"shape": "box", "w": 0.6, "d": 0.35, "h": 0.9},

    # Vehicles & Heavy
    "wrecked_car": {"shape": "box", "w": 2.2, "d": 4.2, "h": 1.4},
    "charger": {"shape": "box", "w": 2.1, "d": 4.6, "h": 1.4},
    "cargo_container": {"shape": "box", "w": 2.4, "d": 4.6, "h": 2.6},
    "crate": {"shape": "box", "w": 1.0, "d": 1.0, "h": 1.0},

    # Live Entities
    "mcpd_stunstick": {"shape": "box", "w": 0.8, "d": 0.8, "h": 1.8},
    "mcpd_pistol": {"shape": "box", "w": 0.8, "d": 0.8, "h": 1.8},
    "civilian": {"shape": "box", "w": 0.8, "d": 0.8, "h": 1.8},
    "ecpu": {"shape": "box", "w": 0.8, "d": 0.8, "h": 1.8},
    "military": {"shape": "box", "w": 0.8, "d": 0.8, "h": 1.8},
    "rpg": {"shape": "box", "w": 0.8, "d": 0.8, "h": 1.8},
}

MAP_EDITOR_PALETTE = [
    # ── Category 1: Source BSP World Brushes & Infrastructure ──
    ("grid", 0, "0: Open Street / Plaza (Demolish / Erase)"),
    ("grid", 1, "1: City-17 Terracotta Brick Building"),
    ("grid", 2, "2: Combine Bunker / gm_bigcity Skyscraper"),
    ("grid", 3, "3: Green Tenement / Cyrillic Poster Wall"),
    ("grid", 4, "4: Neoclassical Facade / Red Warehouse"),
    ("grid", 5, "5: European Apartment Tenement Block"),
    ("grid", 6, "6: Combine Security Door ([E] Interactive)"),
    ("grid", 7, "7: Source Water Canal Basin (Swimmable)"),

    # ── Category 2: Vertical Architecture & Multi-Story Walkable Stairs ──
    ("prop_static", "stairs_metal", "Industrial Metal Stairs (Walkable 0-2.8m Ramp)"),
    ("prop_static", "stairs_wood", "Tenement Wooden Stairs (Walkable 0-2.8m Ramp)"),
    ("prop_static", "metal_ramp", "Diamond-Plate Loading Ramp (Walkable 0-2.8m)"),
    ("prop_static", "scaffolding", "Construction Steel Scaffolding Tower"),
    ("prop_static", "second_story_floor", "2nd Story Metal Floor Deck (3x3m Platform)"),
    ("prop_static", "roof_walkway", "Rooftop Catwalk / Bridge (Walkable Platform)"),
    ("prop_static", "ladder", "Industrial Steel Wall Ladder"),

    # ── Category 3: Fences, Gates & Security Barricades ──
    ("prop_static", "fence", "HL2 Chain-Link Security Fence (Solid Collision)"),
    ("prop_static", "checkpoint_gate", "Combine Checkpoint Gate + Camera"),
    ("prop_static", "combine_barrier", "Combine Armored Street Barrier"),
    ("prop_static", "tall_combine_wall", "Heavy Combine Blast Security Wall (4m)"),
    ("prop_static", "sandbag", "Sandbag Bunker Trench"),
    ("prop_static", "hedgehog", "Steel Czech Hedgehog Tank Trap"),
    ("prop_static", "concrete_jersey", "Concrete Highway K-Rail Barrier"),
    ("prop_static", "wooden_barricade", "Heavy Timber & Plank Barricade"),
    ("prop_static", "razorwire", "Triple Coiled Razorwire Barrier"),

    # ── Category 4: Street Furniture & City-17 Infrastructure ──
    ("prop_static", "entry_light", "Combine Checkpoint Street Lamp Post"),
    ("prop_static", "dumpster", "Green Heavy Municipal Dumpster"),
    ("prop_static", "trash_can", "City-17 Corrugated Street Trash Can"),
    ("prop_static", "vending_machine", "Breen's Water Dispensing Vending Machine"),
    ("prop_static", "phone_booth", "European Telecommunications Kiosk"),
    ("prop_static", "park_bench", "Cast-Iron Slat Park Bench"),
    ("prop_static", "fire_hydrant", "High-Pressure Municipal Fire Hydrant"),
    ("prop_static", "traffic_cone", "Reflective Orange Traffic Cone"),
    ("prop_static", "street_sign", "Cyrillic City-17 Street Name Pole"),
    ("prop_static", "manhole", "Cast-Iron Street Sewer Manhole"),

    # ── Category 5: Industrial & Combine Technology ──
    ("prop_static", "breencast", "Giant Dr. Breen Propaganda Broadcast Screen"),
    ("prop_static", "combine_terminal", "Combine Wall Diagnostic Interface Pedestal"),
    ("prop_static", "power_generator", "Industrial Diesel Electric Generator"),
    ("prop_static", "transformer_box", "High-Voltage Utility Transformer Box"),
    ("prop_static", "fuel_tank", "Horizontal Propane/Fuel Tank on Saddles"),
    ("prop_static", "ventilation_duct", "Large Galvanized HVAC Duct Pipe"),
    ("prop_static", "pipes_cluster", "Wall Conduit Steam & Coolant Pipes"),
    ("prop_static", "satellite_dish", "Rooftop Microwave Satellite Dish"),
    ("prop_static", "security_camera", "Blinking Combine Swivel Security Camera"),
    ("prop_static", "floodlight", "Halogen Twin Work Floodlight on Tripod"),

    # ── Category 6: Interior & Tenement Warehouse Furniture ──
    ("prop_static", "metal_table", "Heavy Workshop / Interrogation Metal Table"),
    ("prop_static", "wooden_chair", "Weathered Wood Tenement Dining Chair"),
    ("prop_static", "metal_locker", "Combine Secure Personnel Locker Unit"),
    ("prop_static", "wooden_shelf", "4-Tier Wooden Storage Utility Shelf"),
    ("prop_static", "metal_crate", "Corrugated Steel Shipping Container Crate"),
    ("prop_static", "wooden_pallet", "Standard Euro Shipping Wooden Pallet"),
    ("prop_static", "pallet_stack", "Warehouse Stack of 4 Wooden Pallets"),
    ("prop_static", "cardboard_box", "Sealed Corrugated Cardboard Cargo Boxes"),
    ("prop_static", "radio_receiver", "Resistance Ham Radio Tuner Unit"),
    ("prop_static", "file_cabinet", "4-Drawer Metal Office File Cabinet"),

    # ── Category 7: Barrels, Hazards, Supplies & Chargers ──
    ("prop_static", "barrel", "HL2 Blue Buoyancy Drum"),
    ("prop_static", "explosive_barrel", "HL2 Red Volatile Explosive Hazard Drum"),
    ("prop_static", "toxic_barrel", "Yellow Biohazard Radioactive Waste Drum"),
    ("prop_static", "water_drum", "Corrugated Blue HDPE Water Cistern"),
    ("prop_static", "gas_canister", "Orange Pressurized Gas Fuel Cylinder"),
    ("prop_static", "ammo_crate", "Olive Drab Military Munitions Crate"),
    ("prop_static", "health_station", "Combine Wall Medkit Dispenser Station"),
    ("prop_static", "suit_charger", "Combine Wall Mark V HEV Suit Charger"),

    # ── Category 8: Vehicles & Heavy Transport ──
    ("prop_static", "wrecked_car", "Burned-Out European Sedan Car Chassis"),
    ("prop_static", "charger", "The Iconic Pink 3D Dodge Charger"),
    ("prop_static", "cargo_container", "4.6m Blue Intermodal Shipping Container"),

    # ── Category 9: Live Interactive Entities & Spawners ──
    ("entity", "crate", "HL2 Wooden Physics Crate (Breakable)"),
    ("entity", "mcpd_stunstick", "Metrocop Officer (Stunstick Baton)"),
    ("entity", "mcpd_pistol", "Metrocop Officer (USP Match 9mm)"),
    ("entity", "civilian", "City-17 Citizen NPC"),
    ("entity", "ecpu", "Combine Overwatch Elite Unit"),
    ("entity", "military", "Heavy Combat Tactical Soldier"),
    ("entity", "rpg", "Rebel RPG Gunner"),
]

DOOR_POSITIONS = []


def rebuild_door_positions():
    DOOR_POSITIONS.clear()
    for y_d in range(MAP_H):
        for x_d in range(MAP_W):
            if MAP[y_d][x_d] == 6:
                DOOR_POSITIONS.append((y_d, x_d))


def set_active_map_data(map_name, ignore_custom=False):
    global MAP_H, MAP_W
    if map_name == "driving Test map":
        m_key = "driving Test map"
        default_src = MAP_DRIVING_TEST
    elif map_name == "BigCity5":
        m_key = "BigCity5"
        default_src = MAP_BIGCITY5
    elif map_name == "gm_bigcity":
        m_key = "gm_bigcity"
        default_src = MAP_GM_BIGCITY
    else:
        m_key = "MainCity2"
        default_src = MAP_MAINCITY2
    loaded_grid = None
    if not ignore_custom:
        custom_all = load_custom_maps()
        saved_entry = custom_all.get(m_key)
        if isinstance(saved_entry, dict) and isinstance(saved_entry.get("grid"), list):
            g = saved_entry["grid"]
            if len(g) == len(default_src) and all(isinstance(r, list) and len(r) == len(default_src[0]) for r in g):
                loaded_grid = g
    src = loaded_grid if loaded_grid is not None else default_src
    MAP[:] = [row[:] for row in src]
    MAP_H = len(MAP)
    MAP_W = len(MAP[0])
    rebuild_door_positions()
    return m_key


set_active_map_data("MainCity2")


# ═══════════════════════════════════════════════════
#  BIG CITY 5 DRIVABLE VEHICLES & VEHICLE CATALOG
# ═══════════════════════════════════════════════════
VEHICLE_CATALOG = [
    {
        "id": "canyon",
        "name": "2023 GMC CANYON AT4X",
        "category": "Off-Road Tactical Pickup",
        "glb_file": os.path.join("Test files & resources", "2023_gmc_canyon_at4x.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "gmc_canyon.png"),
        "scale": 0.95,
        "y_off": 0.0,
        "yaw_off": 90.0,
        "max_speed": 23.0,
        "accel": 16.0,
        "brake": 34.0,
        "turn_rate": 2.3,
        "armor": 120,
        "width": 2.26,
        "length": 5.44,
        "wheel_r": 0.42,
        "wheel_w": 0.28,
        "wheelbase_front": 1.45,
        "wheelbase_rear": -1.45,
        "track_w": 1.95,
        "desc": "High-clearance 4x4 off-road pickup with reinforced chassis and rugged suspension."
    },
    {
        "id": "crown_vic",
        "name": "MCPD POLICE INTERCEPTOR",
        "category": "Civil Protection Pursuit Cruiser",
        "glb_file": "__procedural_police_cruiser__",
        "thumb_file": os.path.join("vehicle_thumbnails", "crown_vic.png"),
        "is_police": True,
        "scale": 1.0,
        "y_off": 0.0,
        "yaw_off": 0.0,
        "max_speed": 31.0,
        "accel": 21.0,
        "brake": 36.0,
        "turn_rate": 2.75,
        "armor": 135,
        "width": 1.92,
        "length": 4.90,
        "wheel_r": 0.36,
        "wheel_w": 0.24,
        "wheelbase_front": 1.42,
        "wheelbase_rear": -1.42,
        "track_w": 1.76,
        "desc": "MCPD Pursuit Cruiser with flashing red/blue emergency lightbar, PIT push-bar, and siren [H]."
    },
    {
        "id": "savana",
        "name": "2003 GMC SAVANA VAN",
        "category": "Heavy Transport & Utility",
        "glb_file": os.path.join("Test files & resources", "gmc_savana_2003.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "gmc_savana.png"),
        "scale": 0.92,
        "y_off": 0.0,
        "yaw_off": 90.0,
        "max_speed": 19.5,
        "accel": 12.0,
        "brake": 26.0,
        "turn_rate": 1.85,
        "armor": 150,
        "width": 2.35,
        "length": 5.71,
        "wheel_r": 0.38,
        "wheel_w": 0.24,
        "wheelbase_front": 1.60,
        "wheelbase_rear": -1.55,
        "track_w": 1.90,
        "desc": "Heavy cargo transport van. Exceptional kinetic mass and battering ram capability."
    },
    {
        "id": "f350",
        "name": "FORD F-350 SUPER DUTY",
        "category": "Heavy Hauler & Bull-Bar",
        "glb_file": os.path.join("Test files & resources", "ford_f350.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "ford_f350.png"),
        "scale": 0.85,
        "y_off": 0.65,
        "yaw_off": -90.0,
        "max_speed": 21.0,
        "accel": 14.0,
        "brake": 28.0,
        "turn_rate": 2.0,
        "armor": 160,
        "width": 2.80,
        "length": 6.80,
        "wheel_r": 0.44,
        "wheel_w": 0.30,
        "wheelbase_front": -1.75,
        "wheelbase_rear": 1.70,
        "track_w": 2.10,
        "desc": "Heavy-duty truck with massive reinforced bull-bar bumper. Shatters Combine barricades."
    },
    {
        "id": "ford_v8",
        "name": "1940 FORD COUPE V8",
        "category": "Classic Vintage Hot-Rod",
        "glb_file": os.path.join("Test files & resources", "1940_ford_v8.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "ford_v8.png"),
        "scale": 1.05,
        "y_off": 0.0,
        "yaw_off": 90.0,
        "max_speed": 24.0,
        "accel": 17.0,
        "brake": 25.0,
        "turn_rate": 2.4,
        "armor": 85,
        "width": 1.86,
        "length": 4.58,
        "wheel_r": 0.36,
        "wheel_w": 0.20,
        "wheelbase_front": 1.30,
        "wheelbase_rear": -1.30,
        "track_w": 1.55,
        "desc": "Vintage retro coupe with responsive throttle, loud engine rumble, and classic chrome styling."
    },
    {
        "id": "mustang_65",
        "name": "1965 FORD MUSTANG CONVERTIBLE",
        "category": "Classic American Muscle",
        "glb_file": os.path.join("Test files & resources", "1965_ford_mustang_convertible.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "mustang.png"),
        "scale": 0.054,
        "y_off": 0.0,
        "yaw_off": 90.0,
        "max_speed": 34.0,
        "accel": 22.0,
        "brake": 35.0,
        "turn_rate": 2.7,
        "armor": 90,
        "width": 1.85,
        "length": 4.65,
        "wheel_r": 0.34,
        "wheel_w": 0.22,
        "wheelbase_front": 1.35,
        "wheelbase_rear": -1.35,
        "track_w": 1.55,
        "desc": "Classic 1965 American muscle convertible. Fast throttle response and agile cornering."
    },
    {
        "id": "sierra_hd",
        "name": "2024 GMC SIERRA 2500HD",
        "category": "Heavy-Duty 4x4 Crew Cab",
        "glb_file": os.path.join("Test files & resources", "gmc_sierra_hd2500.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "sierra.png"),
        "scale": 0.95,
        "y_off": 0.70,
        "yaw_off": 90.0,
        "max_speed": 26.0,
        "accel": 17.0,
        "brake": 32.0,
        "turn_rate": 2.2,
        "armor": 170,
        "width": 2.45,
        "length": 6.20,
        "wheel_r": 0.44,
        "wheel_w": 0.28,
        "wheelbase_front": 1.70,
        "wheelbase_rear": -1.70,
        "track_w": 2.05,
        "desc": "Heavy-duty 4x4 turbo-diesel crew cab. High ground clearance and unstoppable torque."
    },
    {
        "id": "caterpillar_ct680",
        "name": "CATERPILLAR CT680 HEAVY HAULER",
        "category": "Commercial Heavy Dump Truck",
        "glb_file": os.path.join("Test files & resources", "caterpillar_ct680.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "caterpillar.png"),
        "scale": 0.85,
        "y_off": 0.0,
        "yaw_off": 0.0,
        "max_speed": 22.0,
        "accel": 13.0,
        "brake": 30.0,
        "turn_rate": 1.7,
        "armor": 220,
        "width": 2.70,
        "length": 7.80,
        "wheel_r": 0.52,
        "wheel_w": 0.35,
        "wheelbase_front": 2.20,
        "wheelbase_rear": -2.10,
        "track_w": 2.30,
        "desc": "Massive commercial vocational truck with heavy chassis and brutal ramming power."
    },
    {
        "id": "durastar_box",
        "name": "INTERNATIONAL DURASTAR BOX TRUCK",
        "category": "Commercial Cargo Transport",
        "glb_file": os.path.join("Test files & resources", "international_durastar_box_truck_2axle.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "durastar.png"),
        "scale": 0.0072,
        "y_off": 0.0,
        "yaw_off": 90.0,
        "pitch_off": -90.0,
        "max_speed": 21.0,
        "accel": 12.0,
        "brake": 26.0,
        "turn_rate": 1.7,
        "armor": 180,
        "width": 2.50,
        "length": 8.20,
        "wheel_r": 0.48,
        "wheel_w": 0.30,
        "wheelbase_front": 2.30,
        "wheelbase_rear": -2.20,
        "track_w": 2.15,
        "desc": "Commercial 2-axle delivery freight transport with massive enclosed cargo capacity."
    },
    {
        "id": "semi_1940",
        "name": "1940 RETRO SEMI-TRUCK",
        "category": "Vintage Commercial Hauler",
        "glb_file": os.path.join("Test files & resources", "semi_truck_1940.glb"),
        "thumb_file": os.path.join("vehicle_thumbnails", "semi_1940.png"),
        "scale": 3.5,
        "y_off": 0.0,
        "yaw_off": 0.0,
        "max_speed": 22.5,
        "accel": 14.0,
        "brake": 25.0,
        "turn_rate": 1.9,
        "armor": 140,
        "width": 2.35,
        "length": 6.40,
        "wheel_r": 0.42,
        "wheel_w": 0.26,
        "wheelbase_front": 1.65,
        "wheelbase_rear": -1.65,
        "track_w": 1.90,
        "desc": "Vintage 1940s heavy commercial tractor. Distinct rounded fenders and classic industrial styling."
    }
]


def _world_hit_to_normalized_dent(spec, vx, vy, vyaw, hit_x, hit_y, hit_h=0.05):
    """Maps a world-space collision point (hit_x, hit_y) into normalized [-1, 1]^3 model coordinates."""
    dx = hit_x - vx
    dy = hit_y - vy
    cos_y = math.cos(vyaw)
    sin_y = math.sin(vyaw)
    fwd = dx * cos_y + dy * sin_y
    right = -dx * sin_y + dy * cos_y
    half_l = max(0.5, spec.get("length", 4.8) * 0.48)
    half_w = max(0.5, spec.get("width", 1.9) * 0.48)
    n_fwd = max(-1.0, min(1.0, fwd / half_l))
    n_right = max(-1.0, min(1.0, right / half_w))
    n_up = max(-0.6, min(0.8, hit_h))

    yaw_off = spec.get("yaw_off", 0.0)
    pitch_off = spec.get("pitch_off", 0.0)
    if abs(yaw_off - 90.0) < 10.0 and abs(pitch_off - (-90.0)) < 10.0:
        return (-n_right, n_fwd, n_up)
    elif abs(yaw_off - 90.0) < 10.0:
        return (-n_right, n_up, n_fwd)
    elif abs(yaw_off - (-90.0)) < 10.0:
        return (n_right, n_up, -n_fwd)
    return (n_fwd, n_up, n_right)


class DrivableVehicle:
    """Represents a drivable motor vehicle with vphysics acceleration, steering, braking, suspension and collision."""
    def __init__(self, spec, x, y, yaw=0.0):
        self.spec = spec
        self.id = spec["id"]
        self.name = spec["name"]
        self.x = float(x)
        self.y = float(y)
        self.z = 0.0
        self.yaw = float(yaw)
        self.speed = 0.0
        self.steer_angle = 0.0
        self.wheel_rot = 0.0
        self.body_pitch = 0.0
        self.body_roll = 0.0
        self.suspension_z = 0.0
        self.suspension_vz = 0.0
        self.on_dirt = False
        self.max_speed = spec["max_speed"]
        self.accel = spec["accel"]
        self.brake = spec["brake"]
        self.turn_rate = spec["turn_rate"]
        self.health = spec["armor"]
        self.max_health = spec["armor"]
        self.dlist = 0
        self.gear = "P"
        self.turn_signal = 0  # 0=off, -1=left, 1=right
        self.turn_signal_timer = 0.0
        self.brake_lights_on = False
        self.headlights_on = True
        self.is_police = bool(spec.get("is_police", False))
        self.siren_on = False
        self.crumple_amount = 0.0
        self.dents = []  # List of [nx, ny, nz, severity] for VPhysics inward mesh warping

    def apply_impact_damage(self, hit_world_x, hit_world_y, severity=0.35, hit_h=0.05):
        """Applies VPhysics inward mesh crumple/warping around the impact location and reduces vehicle armor."""
        sev = max(0.08, min(1.0, float(severity)))
        nx, ny, nz = _world_hit_to_normalized_dent(self.spec, self.x, self.y, self.yaw, hit_world_x, hit_world_y, hit_h)
        self.crumple_amount = min(1.0, self.crumple_amount + sev * 0.28)
        for d in self.dents:
            dist = math.sqrt((d[0] - nx) ** 2 + (d[1] - ny) ** 2 + (d[2] - nz) ** 2)
            if dist < 0.48:
                d[3] = min(1.0, d[3] + sev * 0.65)
                return
        if len(self.dents) < 8:
            self.dents.append([nx, ny, nz, min(1.0, sev * 0.85)])
        else:
            # Replace weakest dent
            weak_idx = min(range(len(self.dents)), key=lambda idx: self.dents[idx][3])
            self.dents[weak_idx] = [nx, ny, nz, min(1.0, max(self.dents[weak_idx][3], sev * 0.85))]


def get_offroad_elevation(x, y):
    """
    Calculates 3D ground height and terrain bumps for off-road dirt proving grounds and trails.
    Returns 0.0 on highway pavement, and positive undulating elevation over off-road dirt zones.
    """
    # Zone 1: East Off-Road Proving Grounds: X in [36.0, 125.0], Y in [-22.0, 78.0]
    if 36.0 <= x <= 125.0 and -22.0 <= y <= 78.0:
        fade_x = min(1.0, (x - 36.0) / 4.0)
        fade_y = min(1.0, min(y - (-22.0), 78.0 - y) / 4.0)
        fade = max(0.0, fade_x * fade_y)

        # Rolling mounds and moguls (0.08m to 0.85m)
        b1 = 0.22 * math.sin(0.35 * x) * math.cos(0.30 * y)
        b2 = 0.14 * math.sin(0.70 * x + 0.50 * y)
        b3 = 0.08 * math.cos(1.10 * y)
        # Dedicated dirt jump hill around (65.0, 25.0)
        dist_jump = math.hypot(x - 65.0, y - 25.0)
        jump = 0.65 * max(0.0, 1.0 - (dist_jump / 6.0) ** 2)

        return max(0.06 * fade, fade * (0.26 + b1 + b2 + b3 + jump))

    # Zone 2: West Trail Course: X in [-72.0, -12.0], Y in [-18.0, 65.0]
    if -72.0 <= x <= -12.0 and -18.0 <= y <= 65.0:
        fade_x = min(1.0, (-12.0 - x) / 4.0)
        fade_y = min(1.0, min(y - (-18.0), 65.0 - y) / 4.0)
        fade = max(0.0, fade_x * fade_y)

        b1 = 0.18 * math.cos(0.40 * x) * math.sin(0.32 * y)
        b2 = 0.12 * math.sin(0.85 * x - 0.45 * y)
        return max(0.06 * fade, fade * (0.24 + b1 + b2))

    return 0.0


# Proper modern skyscrapers & commercial architecture for Big City 5 (all set safely off-road)
BIGCITY5_OFFROAD_BUILDINGS = [
    # ── North-West Sector (X <= 12, Y <= 10) ──
    {"id": "apex_tower", "name": "Apex Horizon Tower", "x": -75.0, "y": -65.0, "w": 22.0, "d": 20.0, "h": 62.0, "style": "glass_skyscraper", "tint": (0.86, 0.92, 1.0)},
    {"id": "horizon_center", "name": "Horizon Corporate Center", "x": -48.0, "y": -65.0, "w": 18.0, "d": 18.0, "h": 48.0, "style": "modern_commercial", "tint": (0.92, 0.90, 0.88)},
    {"id": "zenith_financial", "name": "Zenith Financial Spire", "x": -72.0, "y": -22.0, "w": 22.0, "d": 20.0, "h": 72.0, "style": "glass_skyscraper", "tint": (0.84, 0.90, 0.98)},
    {"id": "vanguard_spire", "name": "Vanguard Trust Building", "x": -48.0, "y": -22.0, "w": 18.0, "d": 20.0, "h": 54.0, "style": "neoclassical_tower", "tint": (0.94, 0.92, 0.86)},
    {"id": "omnitech_hq", "name": "OmniTech Global HQ", "x": -14.0, "y": -66.0, "w": 18.0, "d": 18.0, "h": 68.0, "style": "glass_skyscraper", "tint": (0.82, 0.88, 0.96)},
    {"id": "aegis_tower", "name": "Aegis Executive Tower", "x": 4.0, "y": -66.0, "w": 12.0, "d": 18.0, "h": 58.0, "style": "modern_commercial", "tint": (0.90, 0.92, 0.95)},
    {"id": "civic_exchange", "name": "Civic Exchange Plaza", "x": -14.0, "y": -22.0, "w": 18.0, "d": 20.0, "h": 42.0, "style": "terracotta_commercial", "tint": (0.92, 0.88, 0.84)},
    {"id": "liberty_suites", "name": "Liberty Grand Suites", "x": 4.0, "y": -22.0, "w": 12.0, "d": 18.0, "h": 36.0, "style": "modern_residential", "tint": (0.94, 0.94, 0.96)},
    {"id": "west_transit_center", "name": "West City Transit Terminal", "x": -58.0, "y": 1.0, "w": 26.0, "d": 12.0, "h": 30.0, "style": "modern_commercial", "tint": (0.88, 0.88, 0.90)},

    # ── South-West Sector (X <= 12, Y >= 32) ──
    {"id": "metro_center", "name": "Grand Metropolitan Center", "x": -70.0, "y": 38.0, "w": 24.0, "d": 16.0, "h": 46.0, "style": "modern_commercial", "tint": (0.90, 0.90, 0.92)},
    {"id": "apex_media", "name": "Apex Media Tower", "x": -48.0, "y": 38.0, "w": 16.0, "d": 16.0, "h": 50.0, "style": "glass_skyscraper", "tint": (0.85, 0.92, 0.98)},
    {"id": "mercantile_tower", "name": "Mercantile Exchange Tower", "x": -70.0, "y": 63.0, "w": 22.0, "d": 18.0, "h": 56.0, "style": "glass_skyscraper", "tint": (0.88, 0.94, 0.98)},
    {"id": "pacific_grand_hotel", "name": "Pacific Grand Hotel", "x": -48.0, "y": 63.0, "w": 18.0, "d": 18.0, "h": 44.0, "style": "neoclassical_tower", "tint": (0.95, 0.92, 0.88)},
    {"id": "harborview_condos_w", "name": "West Marina Promenade Condos", "x": -65.0, "y": 95.0, "w": 26.0, "d": 22.0, "h": 40.0, "style": "modern_residential", "tint": (0.92, 0.94, 0.96)},
    {"id": "empire_state_annex", "name": "South Boulevard Commerce Annex", "x": -8.0, "y": 38.0, "w": 22.0, "d": 16.0, "h": 52.0, "style": "modern_commercial", "tint": (0.90, 0.92, 0.94)},
    {"id": "tribune_building", "name": "City Tribune Tower", "x": -8.0, "y": 63.0, "w": 22.0, "d": 18.0, "h": 45.0, "style": "terracotta_commercial", "tint": (0.92, 0.86, 0.82)},
    {"id": "marina_spire_w", "name": "South Marina Gateway Spire", "x": -8.0, "y": 95.0, "w": 20.0, "d": 20.0, "h": 48.0, "style": "glass_skyscraper", "tint": (0.84, 0.90, 0.96)},

    # ── North-East Sector (X >= 27.5, Y <= 10) ──
    {"id": "centennial_plaza", "name": "Centennial Plaza Hotel", "x": 40.0, "y": -66.0, "w": 20.0, "d": 18.0, "h": 44.0, "style": "neoclassical_tower", "tint": (0.95, 0.92, 0.88)},
    {"id": "olympus_tower", "name": "Olympus Crown Tower", "x": 58.0, "y": -66.0, "w": 12.0, "d": 18.0, "h": 60.0, "style": "glass_skyscraper", "tint": (0.86, 0.92, 0.98)},
    {"id": "highland_tech_1", "name": "Highland Research Labs", "x": 78.0, "y": -48.0, "w": 22.0, "d": 20.0, "h": 38.0, "style": "modern_commercial", "tint": (0.88, 0.90, 0.94)},
    {"id": "highland_tech_2", "name": "North Quantum Data Center", "x": 105.0, "y": -48.0, "w": 22.0, "d": 20.0, "h": 42.0, "style": "glass_skyscraper", "tint": (0.82, 0.88, 0.96)},
    {"id": "harborview_campus", "name": "Harborview Tech Campus", "x": 150.0, "y": -55.0, "w": 24.0, "d": 22.0, "h": 38.0, "style": "modern_commercial", "tint": (0.86, 0.92, 0.98)},
    {"id": "skyline_residences", "name": "Skyline Luxury Residences", "x": 180.0, "y": -55.0, "w": 22.0, "d": 20.0, "h": 54.0, "style": "modern_residential", "tint": (0.94, 0.94, 0.96)},
    {"id": "atlas_corporate_center", "name": "Atlas Corporate Center", "x": 152.0, "y": -10.0, "w": 24.0, "d": 22.0, "h": 46.0, "style": "glass_skyscraper", "tint": (0.85, 0.92, 0.98)},
    {"id": "gemini_towers_north", "name": "Gemini Financial North", "x": 185.0, "y": -10.0, "w": 22.0, "d": 22.0, "h": 65.0, "style": "glass_skyscraper", "tint": (0.88, 0.94, 1.0)},

    # ── South-East Sector (X >= 27.5, Y >= 32) ──
    {"id": "city_hall_annex", "name": "Municipal Civic Center", "x": 42.0, "y": 40.0, "w": 20.0, "d": 14.0, "h": 32.0, "style": "neoclassical_tower", "tint": (0.94, 0.90, 0.86)},
    {"id": "grand_central_hotel", "name": "Grand Central Hotel & Casino", "x": 44.0, "y": 63.0, "w": 22.0, "d": 18.0, "h": 50.0, "style": "glass_skyscraper", "tint": (0.88, 0.94, 0.98)},
    {"id": "oceanic_condos", "name": "Oceanic Harbor Residences", "x": 44.0, "y": 95.0, "w": 24.0, "d": 20.0, "h": 42.0, "style": "modern_residential", "tint": (0.92, 0.94, 0.96)},
    {"id": "eastside_logistics_hub", "name": "Eastside Logistics Terminal", "x": 90.0, "y": 40.0, "w": 26.0, "d": 16.0, "h": 28.0, "style": "modern_commercial", "tint": (0.88, 0.88, 0.90)},
    {"id": "bayside_financial", "name": "Bayside Banking Center", "x": 115.0, "y": 40.0, "w": 20.0, "d": 16.0, "h": 48.0, "style": "glass_skyscraper", "tint": (0.85, 0.92, 0.98)},
    {"id": "solaris_tower", "name": "Solaris Energy Tower", "x": 92.0, "y": 64.0, "w": 24.0, "d": 20.0, "h": 58.0, "style": "glass_skyscraper", "tint": (0.86, 0.90, 0.96)},
    {"id": "regency_plaza", "name": "Regency Commercial Plaza", "x": 118.0, "y": 64.0, "w": 22.0, "d": 18.0, "h": 40.0, "style": "terracotta_commercial", "tint": (0.92, 0.88, 0.84)},
    {"id": "harbor_grand_residences", "name": "Harbor Grand Waterfront Towers", "x": 100.0, "y": 96.0, "w": 28.0, "d": 22.0, "h": 44.0, "style": "modern_residential", "tint": (0.94, 0.94, 0.96)},
    {"id": "tech_corridor_tower_1", "name": "East Tech Corridor Spire 1", "x": 155.0, "y": 45.0, "w": 26.0, "d": 22.0, "h": 52.0, "style": "glass_skyscraper", "tint": (0.85, 0.90, 0.98)},
    {"id": "tech_corridor_tower_2", "name": "East Tech Corridor Spire 2", "x": 190.0, "y": 45.0, "w": 26.0, "d": 22.0, "h": 56.0, "style": "glass_skyscraper", "tint": (0.88, 0.94, 1.0)},
    {"id": "eastern_gateway_tower_a", "name": "Eastern Gateway Tower Alpha", "x": 270.0, "y": 48.0, "w": 28.0, "d": 24.0, "h": 64.0, "style": "glass_skyscraper", "tint": (0.86, 0.92, 0.98)},
    {"id": "eastern_gateway_tower_b", "name": "Eastern Gateway Tower Beta", "x": 330.0, "y": 48.0, "w": 28.0, "d": 24.0, "h": 60.0, "style": "glass_skyscraper", "tint": (0.84, 0.90, 0.96)},
    {"id": "metro_freight_depot", "name": "Metro Freight Logistics Depot", "x": 450.0, "y": 48.0, "w": 32.0, "d": 26.0, "h": 32.0, "style": "modern_commercial", "tint": (0.88, 0.88, 0.90)},
    {"id": "apex_logistics_east", "name": "Apex Cargo Terminal East", "x": 580.0, "y": 48.0, "w": 34.0, "d": 28.0, "h": 30.0, "style": "modern_commercial", "tint": (0.90, 0.90, 0.92)},
    {"id": "eastern_terminus_center", "name": "Eastern Highway Terminus Commerce", "x": 720.0, "y": 48.0, "w": 30.0, "d": 26.0, "h": 42.0, "style": "glass_skyscraper", "tint": (0.86, 0.92, 0.98)},
]


# ═══════════════════════════════════════════════════
#  BIG CITY 5 TRAFFIC LIGHTS, SPEED SIGNS & NPC TRAFFIC
# ═══════════════════════════════════════════════════

SPEED_SIGN_TEXS = {}
STOP_SIGN_TEX = None

def get_speed_sign_texture(kmh):
    if kmh in SPEED_SIGN_TEXS:
        return SPEED_SIGN_TEXS[kmh]
    surf = pygame.Surface((256, 384), pygame.SRCALPHA)
    surf.fill((245, 245, 248))
    pygame.draw.rect(surf, (20, 20, 20), (8, 8, 240, 368), 12, border_radius=18)
    font_top = pygame.font.SysFont("Arial", 42, bold=True)
    font_num = pygame.font.SysFont("Arial", 112, bold=True)
    font_bot = pygame.font.SysFont("Arial", 40, bold=True)
    t1 = font_top.render("SPEED", True, (20, 20, 20))
    t2 = font_top.render("LIMIT", True, (20, 20, 20))
    t_num = font_num.render(str(kmh), True, (20, 20, 20))
    t_bot = font_bot.render("km/h", True, (20, 20, 20))
    surf.blit(t1, (128 - t1.get_width() // 2, 28))
    surf.blit(t2, (128 - t2.get_width() // 2, 70))
    surf.blit(t_num, (128 - t_num.get_width() // 2, 130))
    surf.blit(t_bot, (128 - t_bot.get_width() // 2, 290))
    tex_id = _upload_surf_to_gl_tex(surf)
    SPEED_SIGN_TEXS[kmh] = tex_id
    return tex_id

def get_stop_sign_texture():
    global STOP_SIGN_TEX
    if STOP_SIGN_TEX is not None:
        return STOP_SIGN_TEX
    surf = pygame.Surface((256, 256), pygame.SRCALPHA)
    pts = [(75, 12), (181, 12), (244, 75), (244, 181), (181, 244), (75, 244), (12, 181), (12, 75)]
    pygame.draw.polygon(surf, (215, 25, 25), pts)
    pygame.draw.polygon(surf, (250, 250, 250), pts, 8)
    font = pygame.font.SysFont("Arial", 72, bold=True)
    txt = font.render("STOP", True, (255, 255, 255))
    surf.blit(txt, (128 - txt.get_width() // 2, 128 - txt.get_height() // 2))
    STOP_SIGN_TEX = _upload_surf_to_gl_tex(surf)
    return STOP_SIGN_TEX

BIGCITY5_INTERSECTIONS = [
    # ── West Highway & Avenue Intersections ──
    {"id": "west_highway_terminus", "name": "West Highway Interchange Terminus", "x": -60.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "west_financial_junction", "name": "West Financial Spire Junction", "x": -15.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "west_ave_north", "name": "West Avenue & North Commerce St", "x": -32.0, "y": -45.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "west_ave_south1", "name": "West Avenue & South Promenade", "x": -32.0, "y": 50.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "west_ave_south2", "name": "West Avenue & Marina Parkway", "x": -32.0, "y": 75.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},

    # ── Central Boulevard & Expressway Junctions ──
    {"id": "central_highway_junction", "name": "Central Boulevard & Expressway Interchange", "x": 20.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "north_financial_plaza", "name": "North Financial Plaza Intersection", "x": 20.0, "y": -45.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "north_corporate_gate", "name": "North Corporate Boulevard Gate", "x": 20.0, "y": -85.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "south_commercial_cross", "name": "South Commercial District Crossway", "x": 20.0, "y": 50.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "south_harbor_cross", "name": "South Promenade & Harbor Junction", "x": 20.0, "y": 75.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "south_marina_terminus", "name": "South Marina Boardwalk Terminus", "x": 20.0, "y": 105.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},

    # ── East Corridor Highway & Avenue Intersections ──
    {"id": "east_commercial_junction", "name": "East Commercial District Junction", "x": 65.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "east_commercial_north", "name": "East Commercial & North Boulevard", "x": 65.0, "y": -45.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "east_commercial_south", "name": "East Commercial & South Parkway", "x": 65.0, "y": 50.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "east_commercial_harbor", "name": "East Commercial & Harbor Link", "x": 65.0, "y": 75.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "east_industrial_junction", "name": "East Industrial Expressway Junction", "x": 140.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "east_tech_north", "name": "East Tech Campus & North Boulevard", "x": 140.0, "y": -45.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "east_tech_south", "name": "East Tech Campus & South Boulevard", "x": 140.0, "y": 50.0, "gantry_yaw": 0.0, "stop_line_dist": 8.0, "type": "city_cross"},
    {"id": "harborview_overpass", "name": "Harborview Expressway Overpass", "x": 220.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "metro_east_junction", "name": "Metro East Expressway Junction", "x": 340.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
    {"id": "far_east_terminus", "name": "Far East Expressway Terminus", "x": 480.0, "y": 25.0, "gantry_yaw": -90.0, "stop_line_dist": 10.0, "type": "highway"},
]

BIGCITY5_ROAD_SIGNS = [
    # ── Highway Speed Limit 200 km/h Signs (Eastbound on South Shoulder Y=28.5, yaw=-90 facing West) ──
    {"x": -120.0, "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": -40.0,  "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": 40.0,   "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": 120.0,  "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": 220.0,  "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": 350.0,  "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": 520.0,  "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},
    {"x": 700.0,  "y": 28.5, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 200},

    # ── Highway Speed Limit 200 km/h Signs (Westbound on North Shoulder Y=14.5, yaw=90 facing East) ──
    {"x": 720.0,  "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": 540.0,  "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": 370.0,  "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": 240.0,  "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": 140.0,  "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": 50.0,   "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": -30.0,  "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},
    {"x": -110.0, "y": 14.5, "z": 0.0, "yaw": 90.0, "type": "speed", "val": 200},

    # ── Central Boulevard Speed Limits (Southbound West curb X=16.5, yaw=180 facing North) ──
    {"x": 16.5, "y": -70.0, "z": 0.0, "yaw": 180.0, "type": "speed", "val": 60},
    {"x": 16.5, "y": -25.0, "z": 0.0, "yaw": 180.0, "type": "speed", "val": 50},
    {"x": 16.5, "y": 35.0,  "z": 0.0, "yaw": 180.0, "type": "speed", "val": 50},
    {"x": 16.5, "y": 65.0,  "z": 0.0, "yaw": 180.0, "type": "speed", "val": 60},
    {"x": 16.5, "y": 95.0,  "z": 0.0, "yaw": 180.0, "type": "speed", "val": 50},

    # ── Central Boulevard Speed Limits (Northbound East curb X=23.5, yaw=0 facing South) ──
    {"x": 23.5, "y": 95.0,  "z": 0.0, "yaw": 0.0, "type": "speed", "val": 50},
    {"x": 23.5, "y": 65.0,  "z": 0.0, "yaw": 0.0, "type": "speed", "val": 60},
    {"x": 23.5, "y": 35.0,  "z": 0.0, "yaw": 0.0, "type": "speed", "val": 50},
    {"x": 23.5, "y": -25.0, "z": 0.0, "yaw": 0.0, "type": "speed", "val": 50},
    {"x": 23.5, "y": -70.0, "z": 0.0, "yaw": 0.0, "type": "speed", "val": 60},

    # ── West & East Avenues (60 km/h) ──
    {"x": -34.5, "y": -20.0, "z": 0.0, "yaw": 180.0, "type": "speed", "val": 60},
    {"x": -27.5, "y": 40.0,  "z": 0.0, "yaw": 0.0,   "type": "speed", "val": 60},
    {"x": 63.5,  "y": -20.0, "z": 0.0, "yaw": 180.0, "type": "speed", "val": 60},
    {"x": 70.5,  "y": 40.0,  "z": 0.0, "yaw": 0.0,   "type": "speed", "val": 60},

    # ── Parking Lots (20 km/h and 10 km/h) ──
    {"x": 14.5, "y": 28.2, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 20},
    {"x": 21.0, "y": 30.2, "z": 0.0, "yaw": 180.0, "type": "speed", "val": 10},
    {"x": -36.0, "y": 20.0, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 20},
    {"x": 60.0,  "y": 82.0, "z": 0.0, "yaw": -90.0, "type": "speed", "val": 20},

    # ── Properly Positioned STOP Signs (Curbs at Exits & Non-Signalized T-Junctions) ──
    # 1. Parking Lot Exits onto streets (vehicles must stop before joining public traffic)
    {"x": 17.2, "y": 27.5, "z": 0.0, "yaw": 180.0, "type": "stop"},  # Spawner parking exit onto Central Blvd
    {"x": 24.8, "y": 28.2, "z": 0.0, "yaw": -90.0, "type": "stop"},  # Spawner parking exit onto Highway Eastbound
    {"x": -34.0, "y": 18.0, "z": 0.0, "yaw": 90.0, "type": "stop"},  # West commercial parking exit onto West Ave
    {"x": 62.0,  "y": 79.0, "z": 0.0, "yaw": 90.0, "type": "stop"},  # East harbor parking exit onto East Ave

    # 2. Off-Road Dirt Track Exits (must stop before rejoining paved public highway)
    {"x": 35.0, "y": 11.5, "z": 0.0, "yaw": 90.0, "type": "stop"},   # Dirt track West exit onto side road
    {"x": 85.0, "y": 13.2, "z": 0.0, "yaw": 180.0, "type": "stop"},  # Dirt track South exit onto Highway

    # 3. Side-Alleys & Loading Docks T-Junctions
    {"x": -31.5, "y": 10.0, "z": 0.0, "yaw": 90.0, "type": "stop"},  # West alley onto West Avenue
    {"x": -31.5, "y": 62.0, "z": 0.0, "yaw": 90.0, "type": "stop"},  # West promenade side junction
    {"x": 66.5,  "y": 10.0, "z": 0.0, "yaw": -90.0, "type": "stop"}, # East commercial alley
    {"x": 66.5,  "y": 62.0, "z": 0.0, "yaw": -90.0, "type": "stop"}, # East warehouse dock exit
    {"x": 139.0, "y": -42.0, "z": 0.0, "yaw": 180.0, "type": "stop"}, # Tech campus exit onto North Blvd
    {"x": 21.5,  "y": 102.0, "z": 0.0, "yaw": 0.0, "type": "stop"},  # Marina boat launch exit
]

TRAFFIC_LANES = {
    # ── Highway Eastbound (+X, yaw=0.0) - Speed Limit 200 km/h ──
    0: {"name": "Highway EB Fast Lane", "road_type": "highway", "direction": "+X", "y": 22.8, "speed_limit": 200.0, "yaw": 0.0, "adj": [1], "bounds": (-140.0, 780.0)},
    1: {"name": "Highway EB Cruise Lane", "road_type": "highway", "direction": "+X", "y": 24.8, "speed_limit": 190.0, "yaw": 0.0, "adj": [0, 2], "bounds": (-140.0, 780.0)},
    2: {"name": "Highway EB Slow Lane", "road_type": "highway", "direction": "+X", "y": 26.8, "speed_limit": 170.0, "yaw": 0.0, "adj": [1], "bounds": (-140.0, 780.0)},

    # ── Highway Westbound (-X, yaw=pi) - Speed Limit 200 km/h ──
    3: {"name": "Highway WB Fast Lane", "road_type": "highway", "direction": "-X", "y": 20.2, "speed_limit": 200.0, "yaw": math.pi, "adj": [4], "bounds": (-140.0, 780.0)},
    4: {"name": "Highway WB Cruise Lane", "road_type": "highway", "direction": "-X", "y": 18.2, "speed_limit": 190.0, "yaw": math.pi, "adj": [3, 5], "bounds": (-140.0, 780.0)},
    5: {"name": "Highway WB Slow Lane", "road_type": "highway", "direction": "-X", "y": 16.2, "speed_limit": 170.0, "yaw": math.pi, "adj": [4], "bounds": (-140.0, 780.0)},

    # ── Central Boulevard (X ~ 20.0, Y in -80 to 100) - Speed Limit 60 km/h ──
    6: {"name": "Central Blvd Southbound", "road_type": "main_road", "direction": "+Y", "x": 18.6, "speed_limit": 60.0, "yaw": math.pi / 2, "adj": [], "bounds": (-80.0, 100.0)},
    7: {"name": "Central Blvd Northbound", "road_type": "main_road", "direction": "-Y", "x": 21.4, "speed_limit": 60.0, "yaw": -math.pi / 2, "adj": [], "bounds": (-80.0, 100.0)},

    # ── West Avenue (X ~ -30.0, Y in -80 to 100) - Speed Limit 60 km/h ──
    8: {"name": "West Ave Southbound", "road_type": "main_road", "direction": "+Y", "x": -31.4, "speed_limit": 60.0, "yaw": math.pi / 2, "adj": [], "bounds": (-80.0, 100.0)},
    9: {"name": "West Ave Northbound", "road_type": "main_road", "direction": "-Y", "x": -28.6, "speed_limit": 60.0, "yaw": -math.pi / 2, "adj": [], "bounds": (-80.0, 100.0)},

    # ── East Avenue (X ~ 68.0, Y in -80 to 100) - Speed Limit 60 km/h ──
    10: {"name": "East Ave Southbound", "road_type": "main_road", "direction": "+Y", "x": 66.6, "speed_limit": 60.0, "yaw": math.pi / 2, "adj": [], "bounds": (-80.0, 100.0)},
    11: {"name": "East Ave Northbound", "road_type": "main_road", "direction": "-Y", "x": 69.4, "speed_limit": 60.0, "yaw": -math.pi / 2, "adj": [], "bounds": (-80.0, 100.0)},

    # ── North Crossway Avenue (Y ~ -45.0, X in -60 to 140) - Speed Limit 50 km/h ──
    12: {"name": "North Crossway Eastbound", "road_type": "main_road", "direction": "+X", "y": -43.8, "speed_limit": 50.0, "yaw": 0.0, "adj": [], "bounds": (-60.0, 140.0)},
    13: {"name": "North Crossway Westbound", "road_type": "main_road", "direction": "-X", "y": -46.2, "speed_limit": 50.0, "yaw": math.pi, "adj": [], "bounds": (-60.0, 140.0)},

    # ── South Promenade Crossway (Y ~ 50.0, X in -60 to 140) - Speed Limit 50 km/h ──
    14: {"name": "South Promenade Eastbound", "road_type": "main_road", "direction": "+X", "y": 51.2, "speed_limit": 50.0, "yaw": 0.0, "adj": [], "bounds": (-60.0, 140.0)},
    15: {"name": "South Promenade Westbound", "road_type": "main_road", "direction": "-X", "y": 48.8, "speed_limit": 50.0, "yaw": math.pi, "adj": [], "bounds": (-60.0, 140.0)},
}

class NPCTrafficVehicle:
    """
    Intelligent NPC Traffic Driver with dynamic multi-lane navigation,
    obstacle avoidance, efficient lane switching, turn signals, and brake lights.
    """
    def __init__(self, veh_id, spec, lane_id, start_x, start_y=None):
        self.id = veh_id
        self.spec = spec
        self.lane_id = lane_id
        self.lane_info = TRAFFIC_LANES[lane_id]
        self.road_type = self.lane_info["road_type"]
        self.direction = self.lane_info["direction"]
        self.yaw = self.lane_info["yaw"]

        is_x_axis = self.direction in ("+X", "-X")
        if is_x_axis:
            self.x = float(start_x)
            self.y = float(self.lane_info.get("y", 24.8))
        else:
            self.x = float(self.lane_info.get("x", 20.0))
            self.y = float(start_y if start_y is not None else start_x)

        self.z = 0.0
        self.target_speed = self.lane_info["speed_limit"] / 3.6
        self.speed = self.target_speed * random.uniform(0.80, 0.98)

        # Lane change state
        self.is_changing_lane = False
        self.target_lane_id = lane_id
        self.lane_change_t = 0.0
        self.start_offset = self.y if "y" in self.lane_info else self.x
        self.target_offset = self.start_offset
        self.turn_signal = 0  # 0=off, -1=left, 1=right
        self.turn_signal_timer = 0.0
        self.brake_lights_on = False
        self.headlights_on = True

        # Police Cruiser & VPhysics 3D Mesh Crumple State
        self.is_police = bool(spec.get("is_police", False))
        self.siren_on = False
        self.crumple_amount = 0.0
        self.dents = []

        # Physics & Animation
        self.steer_angle = 0.0
        self.wheel_rot = 0.0
        self.suspension_z = 0.0
        self.suspension_vz = 0.0
        self.body_pitch = 0.0
        self.body_roll = 0.0
        self.dlist = 0
        self.stuck_timer = 0.0
        self.should_despawn = False

    def apply_impact_damage(self, hit_world_x, hit_world_y, severity=0.35, hit_h=0.05):
        """
        Applies VPhysics 3D mesh inward crumple at the impact point on this NPC vehicle.
        """
        nx, ny, nz = _world_hit_to_normalized_dent(
            self.x, self.y, self.yaw, self.spec, hit_world_x, hit_world_y, hit_h=hit_h
        )
        sev = max(0.10, min(1.0, float(severity)))
        self.crumple_amount = min(1.0, self.crumple_amount + sev * 0.45)

        merged = False
        for d in self.dents:
            dist_sq = (d[0] - nx) ** 2 + (d[1] - ny) ** 2 + (d[2] - nz) ** 2
            if dist_sq < 0.22:
                d[3] = min(1.0, d[3] + sev * 0.65)
                merged = True
                break
        if not merged:
            self.dents.append([nx, ny, nz, min(1.0, sev * 0.85)])
            if len(self.dents) > 4:
                self.dents.sort(key=lambda item: item[3], reverse=True)
                self.dents = self.dents[:4]
        if self.is_police:
            self.siren_on = True

    def update(self, dt, all_traffic, player_x, player_y, player_veh, sim_time):
        dir_sign = 1.0 if self.direction in ("+X", "+Y") else -1.0
        is_x_axis = self.direction in ("+X", "-X")

        # 1. Forward scan in current lane
        dist_lead = 999.0
        lead_speed = self.target_speed
        at_red_light = False

        # Scan for player (player vehicle or player on foot)
        if player_x is not None and player_y is not None:
            lat_dist = abs(player_y - self.y) if is_x_axis else abs(player_x - self.x)
            if lat_dist < 2.0:
                dx = (player_x - self.x) * dir_sign if is_x_axis else (player_y - self.y) * dir_sign
                if 0.5 < dx < dist_lead:
                    dist_lead = dx
                    lead_speed = player_veh.speed if player_veh else 0.0

        # Scan for other traffic in current lane
        for other in all_traffic:
            if other.id == self.id:
                continue
            lat_dist = abs(other.y - self.y) if is_x_axis else abs(other.x - self.x)
            if lat_dist < 1.6:
                dx = (other.x - self.x) * dir_sign if is_x_axis else (other.y - self.y) * dir_sign
                if 0.5 < dx < dist_lead:
                    dist_lead = dx
                    lead_speed = other.speed

        # Scan for traffic lights at upcoming intersections
        for inter in BIGCITY5_INTERSECTIONS:
            ix, iy = inter["x"], inter["y"]
            dx = (ix - self.x) * dir_sign if is_x_axis else (iy - self.y) * dir_sign
            lat_dist = abs(iy - self.y) if is_x_axis else abs(ix - self.x)
            if lat_dist < 4.5 and 2.0 < dx < 36.0:
                cycle = 30.0
                t = sim_time % cycle
                if is_x_axis:
                    state = 'GREEN' if t < 13.0 else ('YELLOW' if t < 16.0 else 'RED')
                else:
                    state = 'RED' if t < 16.0 else ('GREEN' if t < 27.0 else 'YELLOW')
                if state in ('RED', 'YELLOW') and not (self.is_police and self.siren_on):
                    stop_dist = dx - inter.get("stop_line_dist", 8.0)
                    if 0.0 < stop_dist < dist_lead:
                        dist_lead = stop_dist
                        lead_speed = 0.0
                        at_red_light = True

        # 2. Dynamic Lane Switching Decision ("take more efficient route by switching lanes")
        safe_following = max(18.0 if self.road_type == "highway" else 8.0, self.speed * 0.70)
        adj_lanes = self.lane_info.get("adj", [])

        if dist_lead < safe_following * 1.5 and adj_lanes and not self.is_changing_lane and not at_red_light:
            for cand_id in adj_lanes:
                cand_info = TRAFFIC_LANES[cand_id]
                cand_offset = cand_info["y"] if is_x_axis else cand_info["x"]
                # Check blind spot & approaching traffic in candidate lane
                lane_clear = True
                for other in all_traffic:
                    if other.id == self.id:
                        continue
                    olat = abs(other.y - cand_offset) if is_x_axis else abs(other.x - cand_offset)
                    if olat < 1.6:
                        odx = (other.x - self.x) * dir_sign if is_x_axis else (other.y - self.y) * dir_sign
                        if -16.0 < odx < 32.0:
                            lane_clear = False
                            break

                if player_x is not None and player_y is not None:
                    plat = abs(player_y - cand_offset) if is_x_axis else abs(player_x - cand_offset)
                    if plat < 1.8:
                        pdx = (player_x - self.x) * dir_sign if is_x_axis else (player_y - self.y) * dir_sign
                        if -16.0 < pdx < 32.0:
                            lane_clear = False

                if lane_clear:
                    # Initiate lane switch!
                    self.is_changing_lane = True
                    self.target_lane_id = cand_id
                    self.lane_change_t = 0.0
                    self.start_offset = self.y if is_x_axis else self.x
                    self.target_offset = cand_offset
                    # Signal direction: left (-1) or right (+1)
                    if cand_offset < self.start_offset:
                        self.turn_signal = -1 if dir_sign > 0 else 1
                    else:
                        self.turn_signal = 1 if dir_sign > 0 else -1
                    break

        # 3. Acceleration / Braking Physics
        if self.is_changing_lane:
            self.brake_lights_on = False
            self.turn_signal_timer += dt
            self.lane_change_t += dt / 1.6
            prog = min(1.0, self.lane_change_t)
            ease = 0.5 - 0.5 * math.cos(prog * math.pi)
            cur_offset = self.start_offset + (self.target_offset - self.start_offset) * ease
            if is_x_axis:
                self.y = cur_offset
            else:
                self.x = cur_offset

            self.steer_angle = self.turn_signal * 0.08 * math.sin(prog * math.pi)
            self.body_roll = -self.turn_signal * 0.03 * math.sin(prog * math.pi)

            if prog >= 1.0:
                self.is_changing_lane = False
                self.lane_id = self.target_lane_id
                self.lane_info = TRAFFIC_LANES[self.lane_id]
                self.turn_signal = 0
                self.turn_signal_timer = 0.0
                self.steer_angle = 0.0
                self.body_roll = 0.0
        else:
            self.turn_signal = 0
            self.turn_signal_timer = 0.0
            self.steer_angle = 0.0
            self.body_roll = 0.0
            # Strict lane pinning: ensure vehicle never drifts off road
            if is_x_axis:
                self.y = self.lane_info["y"]
            else:
                self.x = self.lane_info["x"]

            if dist_lead < safe_following:
                # Brake smoothly and turn brake lights ON
                self.brake_lights_on = True
                desired_spd = max(0.0, lead_speed * 0.90)
                decel = 26.0 if dist_lead < safe_following * 0.5 else 16.0
                self.speed = max(desired_spd, self.speed - decel * dt)
                self.body_pitch = -0.02
            else:
                self.brake_lights_on = False
                target_v = (self.lane_info["speed_limit"] / 3.6) * (1.22 if (self.is_police and self.siren_on) else 1.0)
                if self.speed < target_v:
                    self.speed = min(target_v, self.speed + 14.0 * dt)
                self.body_pitch = 0.01

        # Yaw follows road lane and steering angle
        self.yaw = self.lane_info["yaw"] + self.steer_angle

        # 4. Translation
        step = dir_sign * self.speed * dt
        if is_x_axis:
            self.x += step
        else:
            self.y += step

        wheel_r = self.spec.get("wheel_r", 0.40)
        self.wheel_rot += (self.speed / wheel_r) * dt

        # 5. Road Boundaries & Anti-stuck recycling
        b_min, b_max = self.lane_info.get("bounds", (-140.0, 780.0))
        if self.direction == "+X" and self.x > b_max:
            self.should_despawn = True
        elif self.direction == "-X" and self.x < b_min:
            self.should_despawn = True
        elif self.direction == "+Y" and self.y > b_max:
            self.should_despawn = True
        elif self.direction == "-Y" and self.y < b_min:
            self.should_despawn = True

        if abs(self.speed) < 0.2 and not at_red_light:
            self.stuck_timer += dt
            if self.stuck_timer > 5.0:
                self.should_despawn = True
        else:
            self.stuck_timer = 0.0


def draw_3d_traffic_signal_head(state='GREEN', scale=1.0):
    gl.glPushMatrix()
    gl.glScalef(scale, scale, scale)
    gl.glDisable(GL_TEXTURE_2D)

    # Backplate
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.0, -0.05)
    draw_box(0.52, 1.40, 0.04, 0.08, 0.08, 0.09)
    gl.glPopMatrix()

    # Housing Box
    draw_box(0.42, 1.25, 0.32, 0.12, 0.13, 0.14)

    red_col = (1.0, 0.12, 0.12) if state == 'RED' else (0.24, 0.04, 0.04)
    yel_col = (1.0, 0.88, 0.10) if state == 'YELLOW' else (0.24, 0.20, 0.02)
    grn_col = (0.12, 1.0, 0.35) if state == 'GREEN' else (0.02, 0.22, 0.06)

    lens_info = [
        (0.38, red_col, state == 'RED'),
        (0.00, yel_col, state == 'YELLOW'),
        (-0.38, grn_col, state == 'GREEN'),
    ]
    for ly, col, is_lit in lens_info:
        # Visor Hood
        gl.glPushMatrix()
        gl.glTranslatef(0.0, ly + 0.14, 0.22)
        draw_box(0.28, 0.06, 0.18, 0.08, 0.08, 0.09)
        gl.glPopMatrix()

        # Lens
        gl.glPushMatrix()
        gl.glTranslatef(0.0, ly, 0.17)
        r = 0.12
        gl.glBegin(GL_TRIANGLES)
        gl.glColor4f(col[0], col[1], col[2], 1.0)
        segs = 12
        for s in range(segs):
            a1 = 2.0 * math.pi * s / segs
            a2 = 2.0 * math.pi * (s + 1) / segs
            gl.glVertex3f(0.0, 0.0, 0.0)
            gl.glVertex3f(math.cos(a1) * r, math.sin(a1) * r, 0.0)
            gl.glVertex3f(math.cos(a2) * r, math.sin(a2) * r, 0.0)
        gl.glEnd()

        if is_lit:
            gl.glEnable(GL_BLEND)
            gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE)
            gl.glBegin(GL_TRIANGLES)
            gl.glColor4f(col[0], col[1], col[2], 0.35)
            for s in range(segs):
                a1 = 2.0 * math.pi * s / segs
                a2 = 2.0 * math.pi * (s + 1) / segs
                gl.glVertex3f(0.0, 0.0, 0.02)
                gl.glVertex3f(math.cos(a1) * (r * 1.8), math.sin(a1) * (r * 1.8), 0.02)
                gl.glVertex3f(math.cos(a2) * (r * 1.8), math.sin(a2) * (r * 1.8), 0.02)
            gl.glEnd()
            gl.glDisable(GL_BLEND)
            gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glPopMatrix()

    gl.glEnable(GL_TEXTURE_2D)
    gl.glPopMatrix()

def draw_3d_traffic_light_gantry(x, z, yaw_deg, state_ew='GREEN', state_ns='RED'):
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    gl.glRotatef(yaw_deg, 0, 1, 0)
    gl.glDisable(GL_TEXTURE_2D)

    # Vertical Galvanized Mast (height 5.6m)
    gl.glPushMatrix()
    gl.glTranslatef(-5.0, 2.8, 0.0)
    draw_box(0.24, 5.6, 0.24, 0.28, 0.30, 0.32)
    gl.glPopMatrix()

    # Horizontal Cantilever Mast Arm (spans 10m across lanes)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 5.4, 0.0)
    draw_box(10.2, 0.20, 0.20, 0.28, 0.30, 0.32)
    gl.glPopMatrix()

    # Signal Head 1 (Lane 1, over road at x=-1.5)
    gl.glPushMatrix()
    gl.glTranslatef(-1.5, 4.6, 0.0)
    draw_3d_traffic_signal_head(state_ew, scale=1.0)
    gl.glPopMatrix()

    # Signal Head 2 (Lane 2, over road at x=+2.2)
    gl.glPushMatrix()
    gl.glTranslatef(2.2, 4.6, 0.0)
    draw_3d_traffic_signal_head(state_ew, scale=1.0)
    gl.glPopMatrix()

    # Signal Head 3 (Side post, at x=-4.8, facing N-S)
    gl.glPushMatrix()
    gl.glTranslatef(-4.8, 2.6, 0.0)
    gl.glRotatef(90.0, 0, 1, 0)
    draw_3d_traffic_signal_head(state_ns, scale=0.85)
    gl.glPopMatrix()

    # White painted stop bars on pavement
    gl.glBegin(GL_QUADS)
    gl.glColor4f(0.95, 0.95, 0.95, 1.0)
    gl.glVertex3f(-4.0, 0.015, 2.0)
    gl.glVertex3f(4.0, 0.015, 2.0)
    gl.glVertex3f(4.0, 0.015, 2.45)
    gl.glVertex3f(-4.0, 0.015, 2.45)
    gl.glEnd()

    gl.glEnable(GL_TEXTURE_2D)
    gl.glPopMatrix()

def draw_3d_speed_sign(x, y, z, yaw_deg, kmh):
    tex_id = get_speed_sign_texture(kmh)
    gl.glPushMatrix()
    gl.glTranslatef(x, y, z)
    gl.glRotatef(yaw_deg, 0, 1, 0)

    # Metal Post (height 2.8m)
    gl.glDisable(GL_TEXTURE_2D)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 1.4, 0.0)
    draw_box(0.08, 2.8, 0.08, 0.45, 0.48, 0.52)
    gl.glPopMatrix()

    # Sign Plate Backing
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 2.35, 0.05)
    draw_box(0.82, 1.22, 0.02, 0.35, 0.38, 0.40)
    gl.glPopMatrix()

    # Sign Textured Front Face (properly right-side-up)
    gl.glEnable(GL_TEXTURE_2D)
    gl.glBindTexture(GL_TEXTURE_2D, tex_id)
    gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    gl.glBegin(GL_QUADS)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-0.40, 1.75, 0.065)
    gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(0.40, 1.75, 0.065)
    gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(0.40, 2.95, 0.065)
    gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(-0.40, 2.95, 0.065)
    gl.glEnd()
    gl.glBindTexture(GL_TEXTURE_2D, 0)

    gl.glPopMatrix()

def draw_3d_stop_sign(x, y, z, yaw_deg):
    tex_id = get_stop_sign_texture()
    gl.glPushMatrix()
    gl.glTranslatef(x, y, z)
    gl.glRotatef(yaw_deg, 0, 1, 0)

    # Post
    gl.glDisable(GL_TEXTURE_2D)
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 1.4, 0.0)
    draw_box(0.08, 2.8, 0.08, 0.45, 0.48, 0.52)
    gl.glPopMatrix()

    # Sign Plate Backing
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 2.40, 0.05)
    draw_box(0.88, 0.88, 0.02, 0.35, 0.38, 0.40)
    gl.glPopMatrix()

    # Octagon Stop Sign Front (properly right-side-up)
    gl.glEnable(GL_TEXTURE_2D)
    gl.glBindTexture(GL_TEXTURE_2D, tex_id)
    gl.glColor4f(1.0, 1.0, 1.0, 1.0)
    gl.glBegin(GL_QUADS)
    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(-0.44, 1.96, 0.065)
    gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(0.44, 1.96, 0.065)
    gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(0.44, 2.84, 0.065)
    gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(-0.44, 2.84, 0.065)
    gl.glEnd()
    gl.glBindTexture(GL_TEXTURE_2D, 0)

    gl.glPopMatrix()




# ═══════════════════════════════════════════════════
#  A* PATHFINDING
# ═══════════════════════════════════════════════════
def _astar(start_x, start_y, goal_x, goal_y, max_steps=60):
    sx, sy = int(start_x), int(start_y)
    gx, gy = int(goal_x), int(goal_y)
    if sx == gx and sy == gy:
        return []
    if not (0 <= gx < MAP_W and 0 <= gy < MAP_H):
        return []
    dest_cell = MAP[gy][gx]
    if dest_cell not in (0, 6, 7):
        return []
    open_set = [(0, 0, sx, sy, [])]
    closed_set = set()
    while open_set:
        f, g, cx, cy, path = heapq.heappop(open_set)
        if (cx, cy) in closed_set:
            continue
        closed_set.add((cx, cy))
        if cx == gx and cy == gy:
            full = path + [(cx, cy)]
            return [(px + 0.5, py + 0.5) for px, py in full]
        if g >= max_steps:
            continue
        for ddx, ddy in ((0, 1), (0, -1), (1, 0), (-1, 0)):
            nx, ny = cx + ddx, cy + ddy
            if (nx, ny) in closed_set:
                continue
            if not (0 <= nx < MAP_W and 0 <= ny < MAP_H):
                continue
            cell = MAP[ny][nx]
            if cell not in (0, 6, 7):
                continue
            ng = g + 1
            h = abs(nx - gx) + abs(ny - gy)
            heapq.heappush(open_set, (ng + h, ng, nx, ny, path + [(cx, cy)]))
    return []


# ═══════════════════════════════════════════════════
#  WEAPON DEFINITIONS
# ═══════════════════════════════════════════════════
WEAPONS = {
    0: {
        'name': 'Tactical Crowbar',
        'damage': 30,
        'fire_rate': 0.35,
        'ammo_type': None,
        'ammo_use': 0,
        'clip_size': 0,
        'reload_time': 0.0,
        'range': 2.5,
        'spread': 0,
        'projectile': False,
        'hitscan': True,
        'color': (200, 90, 40),
    },
    1: {
        'name': 'USP Match 9mm Pistol',
        'damage': 18,
        'fire_rate': 0.22,
        'ammo_type': 'bullets',
        'ammo_use': 1,
        'clip_size': 18,
        'reload_time': 1.4,
        'range': MAX_DEPTH,
        'spread': 0.015,
        'projectile': False,
        'hitscan': True,
        'color': (200, 200, 180),
    },
    2: {
        'name': 'SMG1 Submachine Gun',
        'damage': 14,
        'fire_rate': 0.08,
        'ammo_type': 'bullets',
        'ammo_use': 1,
        'clip_size': 45,
        'reload_time': 1.6,
        'range': MAX_DEPTH,
        'spread': 0.035,
        'projectile': False,
        'hitscan': True,
        'color': (180, 190, 210),
    },
    3: {
        'name': 'SPAS-12 Combat Shotgun',
        'damage': 14,
        'fire_rate': 0.75,
        'ammo_type': 'shells',
        'ammo_use': 1,
        'clip_size': 6,
        'reload_time': 2.0,
        'range': 14.0,
        'spread': 0.07,
        'projectile': False,
        'hitscan': True,
        'pellets': 7,
        'color': (160, 140, 100),
    },
    4: {
        'name': 'AR2 Overwatch Pulse Rifle',
        'damage': 20,
        'fire_rate': 0.11,
        'ammo_type': 'cells',
        'ammo_use': 1,
        'clip_size': 30,
        'reload_time': 1.8,
        'range': MAX_DEPTH,
        'spread': 0.025,
        'projectile': False,
        'hitscan': True,
        'color': (100, 180, 255),
    },
    5: {
        'name': '.357 Magnum Revolver',
        'damage': 75,
        'fire_rate': 0.75,
        'ammo_type': 'bullets',
        'ammo_use': 1,
        'clip_size': 6,
        'reload_time': 2.2,
        'range': MAX_DEPTH,
        'spread': 0.008,
        'projectile': False,
        'hitscan': True,
        'color': (240, 220, 150),
    },
    6: {
        'name': 'RPG-7 Warhead Launcher',
        'damage': 150,
        'fire_rate': 1.2,
        'ammo_type': 'rockets',
        'ammo_use': 1,
        'clip_size': 1,
        'reload_time': 2.2,
        'range': MAX_DEPTH,
        'spread': 0,
        'projectile': True,
        'hitscan': False,
        'color': (220, 90, 30),
    },
}

PICKUP_DEFS = {
    'health_small': {'heal': 15, 'label': 'Field Stimpack', 'color': (0.3, 1.0, 0.4)},
    'health_large': {'heal': 35, 'label': 'Combat Medikit', 'color': (0.2, 0.85, 0.3)},
    'armor_small': {'armor': 10, 'label': 'Armor Plate', 'color': (0.3, 0.6, 1.0)},
    'armor_large': {'armor': 60, 'label': 'Heavy Kevlar Vest', 'color': (0.2, 0.45, 0.95)},
    'ammo_bullets': {'ammo': ('bullets', 25), 'label': '9mm Mag', 'color': (0.9, 0.8, 0.3)},
    'ammo_shells': {'ammo': ('shells', 10), 'label': '12-Gauge Box', 'color': (0.85, 0.45, 0.2)},
    'ammo_cells': {'ammo': ('cells', 40), 'label': 'Pulse Cell Pack', 'color': (0.3, 0.75, 1.0)},
    'ammo_rockets': {'ammo': ('rockets', 5), 'label': 'RPG Warhead Crate', 'color': (0.85, 0.3, 0.15)},
    'ammo_energy': {'ammo': ('energy', 25), 'label': 'Combine Energy Core', 'color': (1.0, 0.8, 0.2)},
    'berserk': {'berserk': True, 'label': 'BERSERK INJECTOR', 'color': (1.0, 0.1, 0.1)},
    'invuln': {'invuln': 30.0, 'label': 'EXECUTIVE IMMUNITY', 'color': (1.0, 1.0, 1.0)},
}


# ═══════════════════════════════════════════════════
#  PROCEDURAL AUDIO GENERATION
# ═══════════════════════════════════════════════════
SAMPLE_RATE = 22050

def gen_sound_buffer(func, duration=0.3, volume=0.3):
    n_samples = int(SAMPLE_RATE * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        val = func(t, duration) * volume
        buf[i] = max(-32767, min(32767, int(val * 32767)))
    return pygame.mixer.Sound(buffer=buf)

def metal_clang_func(t, dur):
    return math.exp(-t * 15) * (math.sin(t * 1200) * 0.5 + math.sin(t * 3400) * 0.3 + random.uniform(-0.2, 0.2))

def pistol_fire_func(t, dur):
    return math.exp(-t * 20) * (random.uniform(-1, 1) * 0.6 + math.sin(t * 1500) * 0.4)

def shotgun_fire_func(t, dur):
    return math.exp(-t * 10) * (random.uniform(-1, 1) * 0.8 + math.sin(t * 400) * 0.2)

def ar2_fire_func(t, dur):
    return math.exp(-t * 30) * (math.sin(t * 2000 + math.sin(t * 500) * 5) * 0.7)

def rpg_fire_func(t, dur):
    return (1 - t / dur) * (random.uniform(-1, 1) * 0.3 + math.sin(t * 80) * 0.7)

def combine_ball_fire_func(t, dur):
    return math.exp(-t * 8) * (math.sin(t * 800 + math.sin(t * 200) * 3) * 0.7)

def combine_ball_hit_func(t, dur):
    return math.exp(-t * 12) * (math.sin(t * 600) * 0.4 + math.sin(t * 1800) * 0.3)

def bfg_fire_func(t, dur):
    return math.exp(-t * 3) * (math.sin(t * 300 + math.sin(t * 80) * 8) * 0.5 + math.sin(t * 60) * 0.3)

def explosion_func(t, dur):
    return math.exp(-t * 4) * (random.uniform(-1, 1) * 0.6 + math.sin(t * 60) * 0.4)

def radio_click_func(t, dur):
    env = 1.0 if t < 0.02 else math.exp(-(t - 0.02) * 30)
    return env * random.uniform(-1, 1)

def footstep_func(t, dur):
    return math.exp(-t * 25) * (random.uniform(-1, 1) * 0.5 + math.sin(t * 200) * 0.3)

def pickup_func(t, dur):
    return math.exp(-t * 6) * math.sin(t * (800 + t * 2000)) * 0.5

def door_func(t, dur):
    return (1 - t / dur) * (math.sin(t * 200) * 0.3 + random.uniform(-0.1, 0.1))

def crowbar_func(t, dur):
    return math.exp(-t * 18) * (math.sin(t * 3000) * 0.3 + random.uniform(-0.5, 0.5) * 0.5)

def pain_func(t, dur):
    return math.exp(-t * 10) * math.sin(t * (300 + random.uniform(-50, 50))) * 0.4

def death_func(t, dur):
    return math.exp(-t * 4) * (math.sin(t * 150 - t * t * 50) * 0.5 + random.uniform(-0.2, 0.2))

def car_engine_start_func(t, dur):
    crank = math.sin(t * 180.0 + math.sin(t * 45.0) * 8.0) * 0.4 if t < 0.38 else 0.0
    rumble = math.exp(-(t - 0.35) * 3.5) * (math.sin(t * 85.0) * 0.5 + random.uniform(-0.15, 0.15)) if t >= 0.35 else 0.0
    return crank + rumble

def police_siren_func(t, dur):
    # Wail-yelp police cruiser siren chirp
    freq = 640.0 + 520.0 * (0.5 - 0.5 * math.cos(t * 2.0 * math.pi / max(0.1, dur)))
    return math.sin(t * freq * 2.0 * math.pi) * 0.48 + math.sin(t * freq * 4.0 * math.pi) * 0.16


# ═══════════════════════════════════════════════════
#  3D ARTICULATED CHARACTER & VEHICLE MODELS
# ═══════════════════════════════════════════════════
def draw_3d_humanoid(x, z, yaw_rad, char_type, anim_phase, is_moving, is_firing, is_pain, weapon_id=1, pose_mode=0, weapon_type='stunstick', weapon_drawn=True, is_melee=False, melee_timer=0.0):
    """
    Renders a full 3D articulated humanoid operator/NPC at world (x, 0, z).
    Faithfully recreates Half-Life 2 Civil Protection Metrocops (white gas-mask helmet,
    dual circular black ocular lenses, protruding snout respirator filter, black high-collar
    flak vest, white upper-arm shoulder pads, double silver belt buckles, olive-grey trousers,
    and glowing blue electric Stunstick / USP Match) and City-17 Citizens (Screenshots 1, 2 & 3).
    pose_mode: 0 = normal, 1 = citizen hands-against-wall inspection, 2 = citizen prone face-down on sidewalk,
               3 = seated driver pose inside a vehicle ("Sit down like").
    """
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    deg = 90.0 - math.degrees(yaw_rad)
    gl.glRotatef(deg, 0.0, 1.0, 0.0)

    if pose_mode == 2:
        # Screenshot 3: Citizen lying face-down on the sidewalk with hands behind head
        gl.glTranslatef(0.0, 0.11, 0.0)
        gl.glRotatef(90.0, 1.0, 0.0, 0.0)
        gl.glTranslatef(0.0, -0.55, 0.0)
    elif pose_mode == 3:
        # Seated driver inside vehicle cabin: lower hips onto the bucket seat
        gl.glTranslatef(0.0, -0.26, 0.0)

    swing = math.sin(anim_phase * 11.0) * 36.0 if (is_moving and pose_mode == 0) else 0.0
    bob = abs(math.sin(anim_phase * 11.0)) * 0.045 if (is_moving and pose_mode == 0) else 0.0
    gl.glTranslatef(0.0, bob, 0.0)

    # Faction color palettes matching Half-Life 2 Screenshots 1, 2 & 3
    if is_pain:
        torso_c = (1.0, 0.15, 0.15)
        leg_c = (0.8, 0.1, 0.1)
        head_c = (1.0, 0.3, 0.3)
        visor_c = (1.0, 0.8, 0.8)
        vest_c = (0.9, 0.1, 0.1)
    elif char_type == 'player':
        # Gordon / HEV Mk V Operator Suit (Charcoal + Amber-Orange HEV Plating)
        torso_c = (0.18, 0.20, 0.22)
        vest_c = (0.85, 0.46, 0.08)
        leg_c = (0.16, 0.18, 0.20)
        head_c = (0.90, 0.74, 0.60)
        visor_c = (1.0, 0.68, 0.12)
    elif char_type == 'mcpd':
        # Half-Life 2 Civil Protection Metrocop (Screenshots 1, 2 & 3)
        torso_c = (0.15, 0.18, 0.21)   # Dark slate-black uniform tunic
        vest_c = (0.09, 0.10, 0.12)    # Black padded Civil Protection flak vest
        leg_c = (0.20, 0.25, 0.23)     # Dark olive-grey Metrocop trousers
        head_c = (0.84, 0.86, 0.84)    # Iconic bone-white gas-mask dome
        visor_c = (0.06, 0.08, 0.10)   # Dark recessed circular ocular lenses
    elif char_type == 'ecpu':
        # Combine Overwatch Soldier / Elite
        torso_c = (0.20, 0.25, 0.32)
        vest_c = (0.12, 0.16, 0.22)
        leg_c = (0.18, 0.22, 0.28)
        head_c = (0.26, 0.30, 0.36)
        visor_c = (0.15, 0.88, 1.0)
    elif char_type == 'military':
        torso_c = (0.22, 0.30, 0.20)
        vest_c = (0.14, 0.20, 0.12)
        leg_c = (0.18, 0.24, 0.16)
        head_c = (0.22, 0.28, 0.18)
        visor_c = (1.0, 0.22, 0.15)
    elif char_type == 'rpg':
        # Resistance Fighter / Rebel RPG
        torso_c = (0.34, 0.38, 0.28)
        vest_c = (0.24, 0.22, 0.18)
        leg_c = (0.22, 0.28, 0.36)
        head_c = (0.86, 0.70, 0.56)
        visor_c = (0.18, 0.18, 0.18)
    elif char_type == 'imp':
        torso_c = (0.58, 0.26, 0.12)
        vest_c = (0.72, 0.35, 0.15)
        leg_c = (0.45, 0.20, 0.08)
        head_c = (0.55, 0.24, 0.10)
        visor_c = (1.0, 0.85, 0.0)
    else:  # City-17 Citizen (Olive-drab or Blue-denim jumpsuit as seen in Screenshots 1 & 3)
        is_olive = (int(x * 10 + z * 10) % 2 == 0)
        torso_c = (0.44, 0.41, 0.29) if is_olive else (0.20, 0.32, 0.44)
        vest_c = (0.38, 0.35, 0.24) if is_olive else (0.17, 0.28, 0.38)
        leg_c = (0.24, 0.20, 0.15) if is_olive else (0.18, 0.22, 0.28)
        head_c = (0.88, 0.72, 0.58)
        visor_c = (0.15, 0.15, 0.15)

    # ── Left Leg ──
    gl.glPushMatrix()
    gl.glTranslatef(-0.11, 0.38, 0.0)
    gl.glRotatef(-82.0 if pose_mode == 3 else swing, 1.0, 0.0, 0.0)
    gl.glTranslatef(0.0, -0.19, 0.0)
    draw_box(0.13, 0.38, 0.14, *leg_c)
    gl.glTranslatef(0.0, -0.17, 0.03)
    draw_box(0.14, 0.11, 0.20, 0.08, 0.08, 0.09)
    gl.glPopMatrix()

    # ── Right Leg ──
    gl.glPushMatrix()
    gl.glTranslatef(0.11, 0.38, 0.0)
    gl.glRotatef(-82.0 if pose_mode == 3 else -swing, 1.0, 0.0, 0.0)
    gl.glTranslatef(0.0, -0.19, 0.0)
    draw_box(0.13, 0.38, 0.14, *leg_c)
    gl.glTranslatef(0.0, -0.17, 0.03)
    draw_box(0.14, 0.11, 0.20, 0.08, 0.08, 0.09)
    gl.glPopMatrix()

    # ── Pelvis / Tactical Belt & Double Silver Buckles (Screenshots 1 & 2) ──
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.41, 0.0)
    draw_box(0.35, 0.11, 0.21, 0.10, 0.10, 0.12)
    if char_type in ('mcpd', 'ecpu'):
        # Double silver belt buckles on Metrocop waist (Screenshot 1)
        for by_off in (0.025, -0.025):
            gl.glPushMatrix()
            gl.glTranslatef(0.0, by_off, 0.11)
            draw_box(0.08, 0.032, 0.02, 0.72, 0.75, 0.78)
            gl.glPopMatrix()
    gl.glPopMatrix()

    # ── Torso & Padded Tactical Vest ──
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.66, 0.0)
    draw_box(0.36, 0.42, 0.22, *torso_c)
    draw_box(0.39, 0.32, 0.25, *vest_c)
    if char_type == 'mcpd':
        # High padded black gorget neck collar + silver chest vocoder plate (Screenshots 1 & 2)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.18, 0.02)
        draw_box(0.28, 0.10, 0.26, 0.08, 0.09, 0.10)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.01, 0.13)
        draw_box(0.09, 0.08, 0.02, 0.65, 0.68, 0.70)
        gl.glPopMatrix()
    elif char_type == 'civilian':
        # Red/orange Citizen ID patch on back (visible in Screenshot 3!)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.06, -0.13)
        draw_box(0.10, 0.12, 0.015, 0.78, 0.16, 0.12)
        gl.glPopMatrix()
    gl.glPopMatrix()

    # ── Upper-Arm / Shoulder Pads (Bright White on Metrocops in Screenshots 1 & 2!) ──
    if char_type in ('player', 'ecpu', 'military', 'mcpd'):
        pad_c = (0.84, 0.86, 0.85) if char_type == 'mcpd' else ((0.85, 0.55, 0.12) if char_type == 'player' else vest_c)
        for sx_p in (-0.23, 0.23):
            gl.glPushMatrix()
            gl.glTranslatef(sx_p, 0.78, 0.0)
            draw_box(0.13, 0.16, 0.20, *pad_c)
            gl.glPopMatrix()

    # ── Head & Half-Life 2 Gas-Mask Helmet ──
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.99, 0.0)
    if char_type == 'mcpd' and not is_pain:
        # Authentic Half-Life 2 Civil Protection Gas-Mask Helmet (Screenshots 1, 2 & 3)
        # Upper bone-white helmet dome
        draw_box(0.25, 0.25, 0.26, 0.84, 0.86, 0.84)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.11, -0.01)
        draw_box(0.22, 0.06, 0.23, 0.86, 0.88, 0.86)
        gl.glPopMatrix()
        # Dark lower jaw/cheek seal + side ear-pods
        gl.glPushMatrix()
        gl.glTranslatef(0.0, -0.07, 0.01)
        draw_box(0.26, 0.11, 0.25, 0.14, 0.16, 0.18)
        gl.glPopMatrix()
        for ex_s in (-0.135, 0.135):
            gl.glPushMatrix()
            gl.glTranslatef(ex_s, -0.01, -0.01)
            draw_box(0.03, 0.09, 0.09, 0.10, 0.11, 0.12)
            gl.glPopMatrix()
        # Two circular recessed dark ocular lenses with dark metallic rims
        for lx_s in (-0.058, 0.058):
            gl.glPushMatrix()
            gl.glTranslatef(lx_s, 0.02, 0.132)
            draw_box(0.078, 0.072, 0.02, 0.18, 0.20, 0.22)
            draw_box(0.058, 0.054, 0.028, 0.05, 0.07, 0.08)
            gl.glPopMatrix()
        # Protruding angled respirator snout filter at chin (signature Metrocop silhouette!)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, -0.065, 0.155)
        gl.glRotatef(22.0, 1.0, 0.0, 0.0)
        draw_box(0.11, 0.11, 0.10, 0.32, 0.34, 0.35)
        gl.glTranslatef(0.0, 0.0, 0.055)
        draw_box(0.085, 0.085, 0.03, 0.10, 0.11, 0.12)
        gl.glPopMatrix()
    else:
        draw_box(0.23, 0.24, 0.23, *head_c)
        if char_type == 'civilian':
            # Short dark hair cap
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.10, -0.01)
            draw_box(0.24, 0.07, 0.24, 0.16, 0.12, 0.09)
            gl.glPopMatrix()
        elif char_type in ('player', 'ecpu', 'military'):
            helm_c = (0.14, 0.16, 0.18) if char_type == 'player' else torso_c
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.05, 0.0)
            draw_box(0.26, 0.16, 0.26, *helm_c)
            gl.glPopMatrix()
        gl.glTranslatef(0.0, 0.02, 0.12)
        draw_box(0.18, 0.05, 0.025, *visor_c)
    gl.glPopMatrix()

    # ── Left Arm ──
    gl.glPushMatrix()
    gl.glTranslatef(-0.24, 0.78, 0.0)
    if pose_mode == 1:
        # Citizen leaning hands against wall (Screenshot 3)
        gl.glRotatef(-110.0, 1.0, 0.0, 0.0)
    elif pose_mode == 2:
        # Citizen hands behind head while lying prone (Screenshot 3)
        gl.glRotatef(-145.0, 1.0, 0.0, 0.0)
        gl.glRotatef(25.0, 0.0, 0.0, 1.0)
    elif pose_mode == 3:
        # Seated driver gripping left side of steering wheel
        gl.glRotatef(-62.0, 1.0, 0.0, 0.0)
        gl.glRotatef(14.0, 0.0, 1.0, 0.0)
    elif char_type == 'mcpd':
        if weapon_type == 'pistol' and weapon_drawn:
            # Tactical two-handed Weaver support stance
            gl.glRotatef(-68.0, 1.0, 0.0, 0.0)
            gl.glRotatef(28.0, 0.0, 1.0, 0.0)
        else:
            gl.glRotatef(-swing * 0.65, 1.0, 0.0, 0.0)
    elif char_type != 'civilian':
        gl.glRotatef(-55.0, 1.0, 0.0, 0.0)
        gl.glRotatef(15.0, 0.0, 1.0, 0.0)
    else:
        gl.glRotatef(-swing * 0.7, 1.0, 0.0, 0.0)
    gl.glTranslatef(0.0, -0.16, 0.0)
    draw_box(0.11, 0.34, 0.11, *torso_c)
    gl.glPopMatrix()

    # ── Right Arm + 3D Weapon (Stunstick / USP Match / Pulse Rifle) ──
    gl.glPushMatrix()
    gl.glTranslatef(0.24, 0.78, 0.0)
    if pose_mode == 1:
        gl.glRotatef(-110.0, 1.0, 0.0, 0.0)
    elif pose_mode == 2:
        gl.glRotatef(-145.0, 1.0, 0.0, 0.0)
        gl.glRotatef(-25.0, 0.0, 0.0, 1.0)
    elif pose_mode == 3:
        # Seated driver gripping right side of steering wheel
        gl.glRotatef(-62.0, 1.0, 0.0, 0.0)
        gl.glRotatef(-14.0, 0.0, 1.0, 0.0)
    elif char_type == 'mcpd':
        if weapon_type == 'stunstick':
            if is_melee or melee_timer > 0:
                # Aggressive overhead strike smack!
                m_prog = 1.0 - max(0.0, min(1.0, melee_timer / 0.45))
                strike_pitch = -135.0 + math.sin(m_prog * math.pi) * 145.0
                gl.glRotatef(strike_pitch, 1.0, 0.0, 0.0)
                gl.glRotatef(-12.0, 0.0, 1.0, 0.0)
            else:
                gl.glRotatef(-45.0 + swing * 0.3, 1.0, 0.0, 0.0)
        elif weapon_type == 'pistol':
            if weapon_drawn:
                recoil = -22.0 if is_firing else 0.0
                gl.glRotatef(-76.0 + recoil, 1.0, 0.0, 0.0)
                gl.glRotatef(-10.0, 0.0, 1.0, 0.0)
            else:
                gl.glRotatef(swing * 0.65, 1.0, 0.0, 0.0)
        else:
            gl.glRotatef(-50.0, 1.0, 0.0, 0.0)
    elif char_type != 'civilian':
        recoil = -18.0 if is_firing else 0.0
        arm_pitch = -75.0
        gl.glRotatef(arm_pitch + recoil, 1.0, 0.0, 0.0)
    else:
        gl.glRotatef(swing * 0.7, 1.0, 0.0, 0.0)
    gl.glTranslatef(0.0, -0.16, 0.0)
    draw_box(0.11, 0.34, 0.11, *torso_c)

    # Held 3D Weapon (Genuine Half-Life 2 3D .obj Models + Tactical Effects)
    if char_type == 'mcpd' and pose_mode == 0:
        if weapon_type == 'stunstick':
            gl.glTranslatef(-0.02, -0.18, 0.10)
            gl.glRotatef(75.0, 1.0, 0.0, 0.0)
            gl.glPushMatrix()
            gl.glRotatef(-35.0, 1.0, 0.0, 0.0)
            stun_dl = WEAPON_DLISTS.get(7, 0)
            if stun_dl:
                gl.glPushMatrix()
                gl.glRotatef(180.0, 0.0, 1.0, 0.0)
                gl.glScalef(0.95, 0.95, 0.95)
                gl.glCallList(stun_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.042, 0.042, 0.52, 0.10, 0.11, 0.13)  # Black baton shaft
            gl.glTranslatef(0.0, 0.0, 0.26)
            draw_box(0.065, 0.065, 0.08, 0.22, 0.24, 0.28)  # Metal stun head prongs
            spark_s = 0.18 + 0.06 * math.sin(anim_phase * 28.0)
            draw_box(spark_s, spark_s, spark_s, 0.25, 0.70, 1.0, 0.82)
            draw_box(spark_s * 0.55, spark_s * 0.55, spark_s * 0.55, 0.90, 0.96, 1.0, 0.95)
            gl.glPopMatrix()
        elif weapon_type == 'pistol' and weapon_drawn:
            gl.glTranslatef(-0.02, -0.18, 0.10)
            gl.glRotatef(75.0, 1.0, 0.0, 0.0)
            pist_dl = WEAPON_DLISTS.get(1, 0)
            if pist_dl:
                gl.glPushMatrix()
                gl.glRotatef(180.0, 0.0, 1.0, 0.0)
                gl.glScalef(1.15, 1.15, 1.15)
                gl.glCallList(pist_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.05, 0.08, 0.24, 0.18, 0.20, 0.22)
                gl.glTranslatef(0.0, 0.03, 0.02)
                draw_box(0.052, 0.042, 0.24, 0.75, 0.78, 0.82)
            if is_firing:
                gl.glTranslatef(0.0, 0.02, 0.22)
                draw_box(0.18, 0.18, 0.14, 1.0, 0.85, 0.25, 0.9)
                draw_box(0.08, 0.08, 0.22, 1.0, 1.0, 1.0, 1.0)
    elif char_type != 'civilian' and char_type != 'imp' and pose_mode == 0:
        gl.glTranslatef(-0.02, -0.18, 0.10)
        gl.glRotatef(75.0, 1.0, 0.0, 0.0)
        wid = weapon_id if char_type == 'player' else (6 if char_type == 'rpg' else (4 if char_type == 'ecpu' else 2))
        wpn_dl = WEAPON_DLISTS.get(wid, 0)
        if wpn_dl:
            gl.glPushMatrix()
            if wid == 0:
                gl.glRotatef(-25.0 if is_firing else 10.0, 1.0, 0.0, 0.0)
            gl.glRotatef(180.0, 0.0, 1.0, 0.0)
            w_scale = 0.12 if wid == 0 else (0.85 if wid in (3, 4, 6) else 1.05)
            gl.glScalef(w_scale, w_scale, w_scale)
            gl.glCallList(wpn_dl)
            gl.glPopMatrix()
        else:
            draw_box(0.06, 0.09, 0.38, 0.22, 0.24, 0.28)

        if is_firing and wid != 0:
            gl.glTranslatef(0.0, 0.02, 0.32)
            draw_box(0.24, 0.24, 0.24, 1.0, 0.9, 0.3, 0.9)
            draw_box(0.12, 0.12, 0.36, 1.0, 1.0, 1.0, 1.0)
    gl.glPopMatrix()

    # If pistol cop has weapon NOT drawn, show holstered USP Match on right hip!
    if char_type == 'mcpd' and weapon_type == 'pistol' and not weapon_drawn and pose_mode == 0:
        gl.glPushMatrix()
        gl.glTranslatef(0.20, 0.44, 0.02)
        draw_box(0.07, 0.16, 0.08, 0.10, 0.11, 0.12)
        gl.glTranslatef(0.0, 0.08, 0.02)
        gl.glRotatef(-25.0, 1.0, 0.0, 0.0)
        draw_box(0.045, 0.05, 0.14, 0.72, 0.75, 0.78)
        gl.glPopMatrix()

    gl.glPopMatrix()


def draw_3d_demon(x, z, yaw_rad, anim_phase, is_pain):
    """Renders a bulky 3D quadrupedal/armored Server Corruption Beast (Demon)."""
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    deg = 90.0 - math.degrees(yaw_rad)
    gl.glRotatef(deg, 0.0, 1.0, 0.0)

    swing = math.sin(anim_phase * 10.0) * 35.0
    r, g, b = (1.0, 0.2, 0.2) if is_pain else (0.78, 0.25, 0.45)

    # Bulky torso
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.52, 0.0)
    draw_box(0.58, 0.48, 0.72, r, g, b)
    # Spine ridge
    gl.glTranslatef(0.0, 0.26, 0.0)
    draw_box(0.16, 0.10, 0.60, r * 0.6, g * 0.4, b * 0.5)
    gl.glPopMatrix()

    # Massive Jaw / Head
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.62, 0.42)
    draw_box(0.42, 0.36, 0.36, r * 0.9, g * 0.8, b * 0.85)
    # Glowing red eyes
    gl.glTranslatef(0.0, 0.08, 0.18)
    draw_box(0.32, 0.06, 0.04, 1.0, 0.1, 0.0)
    gl.glPopMatrix()

    # 4 Muscular Legs
    for lx, lz, s_mult in [(-0.26, 0.22, 1), (0.26, 0.22, -1), (-0.26, -0.22, -1), (0.26, -0.22, 1)]:
        gl.glPushMatrix()
        gl.glTranslatef(lx, 0.35, lz)
        gl.glRotatef(swing * s_mult, 1.0, 0.0, 0.0)
        gl.glTranslatef(0.0, -0.17, 0.0)
        draw_box(0.16, 0.36, 0.18, r * 0.75, g * 0.7, b * 0.75)
        gl.glPopMatrix()

    gl.glPopMatrix()


def draw_3d_charger(x, z, yaw_rad):
    """Renders a 3D Pink Dodge Charger muscle car."""
    gl.glPushMatrix()
    gl.glTranslatef(x, 0.0, z)
    gl.glRotatef(math.degrees(yaw_rad), 0.0, 1.0, 0.0)

    # Main Lower Chassis
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.30, 0.0)
    draw_box(0.85, 0.32, 1.65, 1.0, 0.22, 0.78)
    gl.glPopMatrix()

    # Cabin / Roof
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.56, -0.08)
    draw_box(0.72, 0.26, 0.85, 0.92, 0.18, 0.72)
    # Windshield & Windows
    draw_box(0.74, 0.20, 0.78, 0.2, 0.75, 1.0)
    gl.glPopMatrix()

    # Headlights & Taillights
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.32, 0.83)
    draw_box(0.75, 0.08, 0.04, 1.0, 1.0, 0.85)
    gl.glPopMatrix()
    gl.glPushMatrix()
    gl.glTranslatef(0.0, 0.34, -0.83)
    draw_box(0.78, 0.09, 0.04, 1.0, 0.08, 0.15)
    gl.glPopMatrix()

    # 4 Wheels
    for wx, wz in [(-0.44, 0.52), (0.44, 0.52), (-0.44, -0.52), (0.44, -0.52)]:
        gl.glPushMatrix()
        gl.glTranslatef(wx, 0.16, wz)
        draw_box(0.12, 0.30, 0.30, 0.12, 0.12, 0.14)
        gl.glPopMatrix()

    gl.glPopMatrix()


def draw_3d_source_prop(x, y_elev, z, yaw_rad, prop_type, tex_crate=None):
    """Renders 3D Source Engine vphysics props (wooden crate, HL2 blue floating barrel, explosive barrel, or charger)."""
    if prop_type == 'charger':
        gl.glPushMatrix()
        gl.glTranslatef(0.0, y_elev, 0.0)
        draw_3d_charger(x, z, yaw_rad)
        gl.glPopMatrix()
        return

    gl.glPushMatrix()
    gl.glTranslatef(x, y_elev, z)
    gl.glRotatef(math.degrees(yaw_rad), 0.0, 1.0, 0.0)

    if prop_type == 'crate':
        # Classic Source Engine / Half-Life 2 Wooden Physics Crate (props_junk/wood_crate001a)
        tc = tex_crate or WORLD_TEXTURES.get('wood_crate', 0)
        gl.glTranslatef(0.0, 0.33, 0.0)
        if tc:
            draw_textured_box(0.66, 0.66, 0.66, tc, u_rep=1.0, v_rep=1.0, r=0.96, g=0.88, b=0.74)
        else:
            draw_box(0.64, 0.64, 0.64, 0.68, 0.50, 0.28)
    elif prop_type == 'barrel':
        # Iconic Half-Life 2 Blue Plastic Buoyancy Barrel (models/props_borealis/bluebarrel001.vtf)
        t_blue = WORLD_TEXTURES.get('hl2_blue_barrel', 0)
        gl.glTranslatef(0.0, 0.39, 0.0)
        if t_blue:
            draw_textured_cylinder(0.27, 0.78, t_blue, segs=16, u0=0.0, u1=0.66, v0=0.0, v1=1.0,
                                   cap_r=0.14, cap_g=0.40, cap_b=0.76)
        else:
            draw_box(0.46, 0.74, 0.46, 0.14, 0.46, 0.86)
    elif prop_type == 'explosive_barrel':
        # Genuine Source Engine Red Explosive Hazard Drum ("FLAMMABLE" models/props_c17/oil_drum001h.vtf)
        t_exp = WORLD_TEXTURES.get('hl2_explosive_drum', 0)
        gl.glTranslatef(0.0, 0.39, 0.0)
        if t_exp:
            draw_textured_cylinder(0.27, 0.78, t_exp, segs=16, u0=0.0, u1=1.0, v0=0.35, v1=1.0,
                                   cap_r=0.72, cap_g=0.18, cap_b=0.14)
        else:
            draw_box(0.46, 0.74, 0.46, 0.82, 0.18, 0.12)
    gl.glPopMatrix()


# ═══════════════════════════════════════════════════
#  AI STATES
# ═══════════════════════════════════════════════════
AI_IDLE = 0
AI_ALERT = 1
AI_CHASE = 2
AI_ATTACK = 3
AI_PAIN = 4
AI_DEAD = 5
AI_SEARCH = 6


# ═══════════════════════════════════════════════════
#  ENTITY / NPC CLASSES
# ═══════════════════════════════════════════════════
class Entity:
    _id_counter = 0

    def __init__(self, x, y, etype, sprite=None):
        Entity._id_counter += 1
        self.id = Entity._id_counter
        self.x = x
        self.y = y
        self.z = 0.0
        self.vz = 0.0
        self.in_water = False
        self.type = etype
        self.sprite = sprite
        self.alive = True
        self.health = 100
        self.max_health = 100
        self.speed = 1.0
        self.vx = 0
        self.vy = 0
        self.facing_yaw = random.uniform(0, math.pi * 2)
        self.shoot_timer = 0
        self.shoot_interval = 2.0
        self.age = random.uniform(0, 10.0)
        self.stuck = False
        self.stuck_timer = 0
        self.ai_state = AI_IDLE
        self.pain_timer = 0
        self.alert_timer = 0
        self.search_timer = 0.0
        self.damaged_player_first = False
        self.self_defense_valid = False
        self.attack_flash = 0.0
        self.last_known_px = 0
        self.last_known_py = 0
        self.pain_chance = 0.3
        self.see_player = False
        self.damage_given = 0
        self.path = []
        self.path_timer = 0.0
        self.path_target_x = 0.0
        self.path_target_y = 0.0

    def can_see_point(self, tx, ty, game=None):
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.1:
            return True
        steps = max(1, int(dist * 5))
        sx = dx / steps
        sy = dy / steps
        cx, cy = self.x, self.y
        for _ in range(steps):
            cx += sx
            cy += sy
            mx, my = int(cx), int(cy)
            if 0 <= mx < MAP_W and 0 <= my < MAP_H:
                cell = MAP[my][mx]
                if cell == 6:
                    if not (game and hasattr(game, 'is_door_open') and game.is_door_open(my, mx)):
                        return False
                elif cell not in (0, 7):
                    return False

                # Check solid opaque placed props (chainlink fences & wire gates are see-through!)
                if game and hasattr(game, 'placed_objects'):
                    for p_obj in game.placed_objects:
                        p_t = p_obj.get("type", "")
                        if p_t in ("chain_fence", "wire_gate", "security_gate", "scaffolding"):
                            continue
                        p_col = PROP_COLLISION_DATA.get(p_t)
                        if p_col and p_col.get("shape") in ("box", "cylinder"):
                            ox = float(p_obj.get("x", 0.0))
                            oy = float(p_obj.get("y", 0.0))
                            if (cx - ox) ** 2 + (cy - oy) ** 2 < 0.64:
                                return False
            else:
                return False
        return True

    def update(self, dt, game):
        self.age += dt
        self.shoot_timer += dt
        if self.attack_flash > 0:
            self.attack_flash -= dt * 4.0

        if self.ai_state == AI_PAIN:
            self.pain_timer -= dt
            if self.pain_timer <= 0:
                self.ai_state = AI_CHASE
            self.vx *= 0.8
            self.vy *= 0.8
        elif self.ai_state == AI_DEAD:
            return

        dist_to_player = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        in_spawn_grace = getattr(game, 'spawn_protection_timer', 0) > 0
        if in_spawn_grace and self.type in ('mcpd', 'rpg', 'military', 'demon', 'imp'):
            self.see_player = False
        else:
            self.see_player = dist_to_player < 22 and self.can_see_point(game.player_x, game.player_y, game)

        if self.see_player:
            self.last_known_px = game.player_x
            self.last_known_py = game.player_y
            if self.ai_state == AI_IDLE:
                self.ai_state = AI_ALERT
                self.alert_timer = 0.4

        # Update facing direction smoothly toward movement or target
        spd_sq = self.vx * self.vx + self.vy * self.vy
        if spd_sq > 0.04:
            self.facing_yaw = math.atan2(self.vy, self.vx)

        self.vx *= 0.85
        self.vy *= 0.85

        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        mx, my = int(nx), int(ny)
        if 0 <= mx < MAP_W and 0 <= my < MAP_H:
            if MAP[my][mx] == 6 and not game.is_door_open(my, mx):
                game.try_open_door(my, mx)

            blocked = game.is_position_blocked(nx, ny, 0.35, getattr(self, 'z', 0.0))
            if not blocked and (MAP[my][mx] in (0, 7) or (MAP[my][mx] == 6 and game.is_door_open(my, mx))):
                self.x = nx
                self.y = ny
                self.in_water = (MAP[my][mx] == 7)
                if self.in_water:
                    self.z = -0.22 + math.sin(game.hud_pulse * 3.0 + self.id) * 0.04
                else:
                    self.z = 0.0
            else:
                self.vx *= -0.5
                self.vy *= -0.5
        else:
            self.vx *= -0.5
            self.vy *= -0.5

    def take_damage(self, amt, game, source=None):
        if getattr(game, 'cheat_mode', False) and source == 'player':
            amt *= 2.0
        self.health -= amt

        if source == 'player' and hasattr(game, 'register_player_hit'):
            t_label = "MCPD CIVIL PROTECTION" if self.type == 'mcpd' else ("CITIZEN" if self.type == 'civilian' else self.type.upper())
            game.register_player_hit(
                f"{t_label} #{self.id}",
                max(0, self.health),
                getattr(self, 'max_health', 100),
                is_kill=(self.health <= 0),
                is_metal=(self.type in ('turret', 'drone')),
            )

        # Alert nearby citizens (70% flee / 30% armed vigilante)
        if hasattr(game, 'alert_nearby_citizens'):
            game.alert_nearby_citizens(self.x, self.y)

        if source == 'player' and self.type == 'mcpd' and self.health > 0:
            if getattr(self, 'self_defense_valid', False):
                game.add_log('sys', f'[SELF-DEFENSE] Engagement authorized on Unit #{self.id} — 0 Wanted Stars.')
            else:
                if game.wanted_level == 0:
                    game.add_wanted(1)

        if self.health > 0 and random.random() < self.pain_chance:
            self.ai_state = AI_PAIN
            self.pain_timer = 0.25
            game.play_pain(self.x, self.y, self.type, self.id)
        if self.health <= 0:
            self.die(game, source=source)

    def die(self, game, source='player'):
        self.alive = False
        self.ai_state = AI_DEAD
        game.spawn_explosion(self.x, self.y)
        game.kills += 1
        game.play_death(self.x, self.y, self.type, self.id)
        game.corpses.append({'x': self.x, 'y': self.y, 'type': self.type, 'age': 0, 'yaw': self.facing_yaw})

        if self.type == 'mcpd' and source == 'player':
            if getattr(self, 'self_defense_valid', False):
                game.add_log('sys', f'[JUSTIFIED SELF-DEFENSE] Elimination of rogue unit #{self.id} authorized by Overwatch. 0 Wanted Stars.')
            else:
                # Unprovoked cop kill: 3 Stars (not 5 Stars), subsequent kills escalate towards 5
                if game.wanted_level < 3:
                    game.wanted_level = 3
                else:
                    game.wanted_level = min(5, game.wanted_level + 1)
                game.trigger_overwatch_announcement(event='anticitizen', force=True)
                game.add_log('warn', f'[CRITICAL OFFENSE] Officer #{self.id} killed unprovoked! WANTED LEVEL ESCALATED TO {game.wanted_level} STARS!')

    def dist_to(self, px, py):
        return math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2)

    def _navigate_to(self, tx, ty, speed, dt):
        self.path_timer -= dt
        if (self.path_timer <= 0
                or abs(tx - self.path_target_x) > 1.5
                or abs(ty - self.path_target_y) > 1.5):
            self.path_timer = 1.0 + random.random() * 0.5
            self.path_target_x = tx
            self.path_target_y = ty
            self.path = _astar(self.x, self.y, tx, ty)

        if self.path:
            next_x, next_y = self.path[0]
            dx = next_x - self.x
            dy = next_y - self.y
            d = math.sqrt(dx * dx + dy * dy)
            if d < 0.6:
                self.path.pop(0)
                if not self.path:
                    return
                next_x, next_y = self.path[0]
                dx = next_x - self.x
                dy = next_y - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
            self.vx = (dx / d) * speed
            self.vy = (dy / d) * speed
        else:
            dx = tx - self.x
            dy = ty - self.y
            d = math.sqrt(dx * dx + dy * dy) or 1
            self.vx = (dx / d) * speed
            self.vy = (dy / d) * speed


class Civilian(Entity):
    def __init__(self, x, y, sprite=None):
        super().__init__(x, y, 'civilian', sprite)
        self.health = 60
        self.max_health = 60
        self.speed = 0.8
        self.wander_timer = 0
        self.pain_chance = 0.85
        self.panic_timer = 0
        self.scream_timer = 0
        self.idle_talk_timer = random.uniform(5.0, 16.0)
        self.is_armed = (random.random() < 0.30)  # 30% Armed TBMG Vigilante
        self.armed_weapon = random.choice(['pistol', 'smg1']) if self.is_armed else None
        self.is_premium = (random.random() < 0.30)  # 30% Premium VIP LifeShield plan
        self.respawn_plan = 'premium' if self.is_premium else 'standard'
        self.plan_name = "TBMG LifeShield Premium VIP Plan" if self.is_premium else "TBMG Standard Citizen Care"
        self.bg_shoot_timer = random.uniform(5.0, 12.0)
        self.citizen_state = None  # 'flee' or 'vigilante' or None
        self.vigilante_target = None
        self.flee_speed = 1.6 * 2.2
        self.flee_timer = 0.0
        self.flee_from_x = 0.0
        self.flee_from_y = 0.0
        self.npc_wanted = False
        self.npc_wanted_timer = 0.0

    def _find_nearest_danger(self, game):
        nearest = None
        nearest_d = float('inf')
        for e in game.entities:
            if not e.alive or e.type not in ('rpg', 'imp', 'demon'):
                continue
            d = self.dist_to(e.x, e.y)
            if d < nearest_d:
                nearest_d = d
                nearest = e
        return nearest, nearest_d

    def _find_nearest_mcpd(self, game):
        nearest = None
        nearest_d = float('inf')
        for e in game.entities:
            if not e.alive or e.type != 'mcpd':
                continue
            d = self.dist_to(e.x, e.y)
            if d < nearest_d:
                nearest_d = d
                nearest = e
        return nearest, nearest_d

    def react_to_threat(self, threat_x, threat_y, game, threat_entity=None):
        if not self.alive:
            return
        if self.is_armed:
            self.citizen_state = 'vigilante'
            self.vigilante_target = threat_entity or (threat_x, threat_y)
            self.last_known_px = threat_x
            self.last_known_py = threat_y
            if self.scream_timer <= 0:
                self.scream_timer = 4.0
                game.play_citizen_combat(self.x, self.y)
                combat_lines = ["Enough of this!", "Take cover!", "Behind you!", "Watch out!"]
                game.add_log('warn', f'Armed Citizen #{self.id}: "{random.choice(combat_lines)}"')
        else:
            self.citizen_state = 'flee'
            self.flee_timer = random.uniform(5.0, 8.5)
            self.flee_from_x = threat_x
            self.flee_from_y = threat_y
            if self.scream_timer <= 0:
                self.scream_timer = 5.0
                game.play_citizen_panic(self.x, self.y)
                panic_line = random.choice(CITIZEN_VOICE_LINES["panic"])
                game.add_log('warn', f'Citizen #{self.id}: "{panic_line}"', priority='ambient')

    def update(self, dt, game):
        super().update(dt, game)
        self.wander_timer += dt
        if self.panic_timer > 0:
            self.panic_timer -= dt
        if self.scream_timer > 0:
            self.scream_timer -= dt
        if self.idle_talk_timer > 0:
            self.idle_talk_timer -= dt

        # ── NPC ANTI-CITIZEN STATUS (this civilian shot at Civil Protection) ──
        if getattr(self, 'npc_wanted', False):
            self.npc_wanted_timer = getattr(self, 'npc_wanted_timer', 45.0) - dt
            if self.npc_wanted_timer <= 0:
                self.npc_wanted = False
                game.add_log('info', f'[ANTI-CITIZEN] Citizen #{self.id} evaded Civil Protection — status expired.', priority='ambient')
                if self.citizen_state == 'vigilante':
                    self.citizen_state = None
                    self.vigilante_target = None
            elif self.is_armed:
                # Keep fighting the nearest officer in sight
                cur = self.vigilante_target
                if not (hasattr(cur, 'alive') and cur.alive and getattr(cur, 'type', '') == 'mcpd'):
                    cop, cop_d = self._find_nearest_mcpd(game)
                    if cop and cop_d < 22.0 and self.can_see_point(cop.x, cop.y, game):
                        self.citizen_state = 'vigilante'
                        self.vigilante_target = cop

        # Reactive combat / flee state handling
        if self.citizen_state == 'flee':
            self.flee_timer -= dt
            dx = self.x - self.flee_from_x
            dy = self.y - self.flee_from_y
            d = math.hypot(dx, dy) or 1.0
            self.facing_yaw = math.atan2(dy, dx)
            self.vx = (dx / d) * self.flee_speed
            self.vy = (dy / d) * self.flee_speed
            if self.flee_timer <= 0:
                self.citizen_state = None
                self.vx *= 0.3
                self.vy *= 0.3
            return
        elif self.citizen_state == 'vigilante':
            tx, ty = (self.last_known_px, self.last_known_py)
            target_is_player = False
            if self.vigilante_target:
                if hasattr(self.vigilante_target, 'alive'):
                    if not self.vigilante_target.alive:
                        self.citizen_state = None
                        self.vigilante_target = None
                        return
                    tx, ty = self.vigilante_target.x, self.vigilante_target.y
                elif self.vigilante_target == 'player':
                    tx, ty = game.player_x, game.player_y
                    target_is_player = True
                elif isinstance(self.vigilante_target, (tuple, list)):
                    tx, ty = self.vigilante_target

            dist_t = math.hypot(tx - self.x, ty - self.y)
            self.facing_yaw = math.atan2(ty - self.y, tx - self.x)
            if dist_t > 6.0:
                self._navigate_to(tx, ty, self.speed * 1.5, dt)
            else:
                self.vx *= 0.6
                self.vy *= 0.6

            can_see = self.can_see_point(tx, ty, game)
            if can_see and dist_t < 22.0:
                self.shoot_timer += dt
                if self.shoot_timer > 1.2:
                    self.shoot_timer = 0.0
                    self.attack_flash = 0.3
                    game._play_spatial(game.snd_smg1 if self.armed_weapon == 'smg1' else game.snd_pistol, self.x, self.y, max_dist=40.0)
                    game.tracers.append([
                        self.x, 0.75, self.y,
                        tx, 0.75, ty,
                        (0.2, 0.85, 1.0), 0.12
                    ])
                    if target_is_player:
                        game.player_take_damage(10)
                        game.damage_flash = 0.3
                    elif hasattr(self.vigilante_target, 'take_damage'):
                        # Shooting at Civil Protection makes this citizen an anti-citizen
                        if getattr(self.vigilante_target, 'type', '') == 'mcpd':
                            game.report_npc_anticitizen(self, "Opened fire on Civil Protection")
                        self.vigilante_target.take_damage(14, game, source='vigilante')
            return

        danger, danger_dist = self._find_nearest_danger(game)
        gunfire_panic = self.see_player and game.weapon_fired > 0

        if danger and danger_dist < 10:
            self.react_to_threat(danger.x, danger.y, game, danger)
        elif gunfire_panic:
            self.react_to_threat(game.player_x, game.player_y, game, 'player')
        elif self.panic_timer <= 0 and self.ai_state in (AI_IDLE, AI_ALERT):
            if self.idle_talk_timer <= 0:
                self.idle_talk_timer = random.uniform(11.0, 24.0)
                if self.dist_to(game.player_x, game.player_y) < 13.0:
                    idle_line = random.choice(CITIZEN_VOICE_LINES["idle"])
                    game.add_log('info', f'Citizen #{self.id}: "{idle_line}"', priority='ambient')
                    game.play_citizen_talk(self.x, self.y)
            if self.wander_timer > 3 + random.random() * 3:
                self.wander_timer = 0
                self.vx = random.uniform(-1, 1) * self.speed
                self.vy = random.uniform(-1, 1) * self.speed
                if random.random() < 0.3:
                    self.vx = 0
                    self.vy = 0

            # Unprompted background target shooting for armed citizens
            if getattr(self, 'is_armed', False) and self.citizen_state is None and self.ai_state in (AI_IDLE, AI_ALERT):
                self.bg_shoot_timer -= dt
                if self.bg_shoot_timer <= 0:
                    self.bg_shoot_timer = random.uniform(7.0, 16.0)
                    t_ang = self.facing_yaw + random.uniform(-0.6, 0.6)
                    t_dist = random.uniform(6.0, 14.0)
                    tx = self.x + math.cos(t_ang) * t_dist
                    ty = self.y + math.sin(t_ang) * t_dist
                    wall_hit = False
                    steps = max(1, int(t_dist / 0.3))
                    hx, hy = tx, ty
                    for s in range(1, steps + 1):
                        cx = self.x + math.cos(t_ang) * (s * 0.3)
                        cy = self.y + math.sin(t_ang) * (s * 0.3)
                        mx, my = int(cx), int(cy)
                        if 0 <= mx < MAP_W and 0 <= my < MAP_H:
                            if MAP[my][mx] not in (0, 7):
                                wall_hit = True
                                hx, hy = cx, cy
                                break
                    self.facing_yaw = t_ang
                    self.attack_flash = 0.25
                    if self.armed_weapon == 'smg1':
                        game.snd_smg1.play()
                    else:
                        game.snd_pistol.play()
                    game.tracers.append([
                        self.x, 0.75, self.y,
                        hx, 0.75, hy,
                        (1.0, 0.85, 0.25), 0.10
                    ])
                    if wall_hit:
                        game.spawn_wall_bullet_decal(hx, hy, 0.75, -math.cos(t_ang), -math.sin(t_ang))
                    bg_quotes = ["Target practice.", "Testing my trigger.", "Take that, Combine metal!", "Keep off our street!"]
                    if random.random() < 0.40 and self.dist_to(game.player_x, game.player_y) < 22.0:
                        game.add_log('ambient', f'Armed Citizen #{self.id}: "{random.choice(bg_quotes)}"', priority='ambient')

                    # Civil Protection witnesses or hears public unauthorized firearm discharge
                    cop, cop_d = self._find_nearest_mcpd(game)
                    if cop and cop_d < 24.0:
                        game.report_npc_anticitizen(self, "Unauthorized public firearm discharge")
                        self.citizen_state = 'vigilante'
                        self.vigilante_target = cop

    def die(self, game, source='player'):
        super().die(game, source=source)
        # Anti-Citizen neutralization event
        if getattr(self, 'npc_wanted', False):
            self.npc_wanted = False
            game.trigger_overwatch_announcement(event='neutralized')
            game.add_log('sys', f'[OVERWATCH] Anti-Citizen #{self.id} neutralized by {source}. Civil containment restored.', priority='important')
            for e in game.entities:
                if e.type == 'mcpd' and getattr(e, 'npc_target', None) == self:
                    e.npc_target = None
                    if game.wanted_level == 0:
                        e.ai_state = AI_IDLE
                        e.weapon_drawn = False

        # TBMG Pay-to-Respawn Economy Script
        respawn_time = random.uniform(2.0, 3.5) if getattr(self, 'is_premium', False) else random.uniform(12.0, 18.0)
        game.civilian_respawn_queue.append({
            'timer': respawn_time,
            'plan': getattr(self, 'respawn_plan', 'standard'),
            'id': self.id
        })
        if getattr(self, 'is_premium', False):
            game.add_log('sys', f'[TBMG RESPAWN ECONOMY] Citizen #{self.id} LifeShield Premium VIP Plan triggered! Rapid street resurrection active ({respawn_time:.1f}s)...')
        else:
            game.add_log('info', f'[TBMG RESPAWN ECONOMY] Citizen #{self.id} died. Queued in LifeShield Standard Tier (Respawn in {int(respawn_time)}s)...')


class MCPDUnit(Entity):
    def __init__(self, x, y, sprite=None, weapon_type=None):
        super().__init__(x, y, 'mcpd', sprite)
        self.health = 180
        self.max_health = 180
        self.weapon_type = weapon_type if weapon_type else random.choice(['stunstick', 'pistol'])
        self.weapon_drawn = (self.weapon_type == 'stunstick')
        self.melee_timer = 0.0
        self.melee_cooldown = 0.0
        self.alert_voice_timer = random.uniform(1.0, 3.0)
        self.patrol_voice_timer = random.uniform(5.0, 14.0)
        self.speed = 2.4
        self.run_speed = 4.2
        self.shoot_interval = 1.3
        self.damage_given = 18
        self.pain_chance = 0.3
        self.patrol_waypoint = 0
        self.strafe_timer = 0
        self.strafe_dir = random.choice([-1, 1])
        self.call_timer = 0
        self.npc_target = None
        self.patrol_points = [
            (8.5, 6.5), (15.5, 6.5), (18.5, 12.5), (14.5, 18.5),
            (8.5, 18.5), (5.5, 12.5), (11.5, 12.0), (20.5, 12.0)
        ]
        random.shuffle(self.patrol_points)

    def _find_endangered_civilian(self, game):
        for civ in game.entities:
            if not civ.alive or civ.type != 'civilian':
                continue
            for mon in game.entities:
                if not mon.alive or mon.type not in ('rpg', 'imp', 'demon'):
                    continue
                if civ.dist_to(mon.x, mon.y) < 6:
                    return civ, mon
        return None, None

    def _count_nearby_mcpd(self, game, radius=8):
        return sum(1 for e in game.entities if e.alive and e.type == 'mcpd' and e.id != self.id and self.dist_to(e.x, e.y) < radius)

    def update(self, dt, game):
        super().update(dt, game)
        if self.ai_state == AI_PAIN:
            return
        if self.call_timer > 0:
            self.call_timer -= dt
        if self.melee_timer > 0:
            self.melee_timer -= dt
        if self.melee_cooldown > 0:
            self.melee_cooldown -= dt
        if self.alert_voice_timer > 0:
            self.alert_voice_timer -= dt
        if self.patrol_voice_timer > 0:
            self.patrol_voice_timer -= dt
        self.strafe_timer += dt

        in_spawn_grace = getattr(game, 'spawn_protection_timer', 0) > 0
        dist_to_p = math.hypot(self.x - game.player_x, self.y - game.player_y)
        can_see_p = (not in_spawn_grace) and dist_to_p < 24.0 and self.can_see_point(game.player_x, game.player_y, game)
        player_wanted = (game.wanted_level >= 1)

        # Occasional Half-Life 2 Combine radio dispatch chatter
        if self.patrol_voice_timer <= 0:
            self.patrol_voice_timer = random.uniform(8.0, 19.0)
            if dist_to_p < 18.0:
                vo_line = random.choice(COMBINE_VOICE_LINES)
                game.add_log('sys', f'Combine CP #{self.id}: "{vo_line}"', priority='ambient')
                game.play_combine_vo(self.x, self.y)

        # ── ACTIVE ENGAGEMENT OF NPC ANTI-CITIZEN / BACKGROUND SHOOTER ──
        if not getattr(self, 'npc_target', None) or not getattr(self.npc_target, 'alive', False) or not getattr(self.npc_target, 'npc_wanted', False):
            self.npc_target = game.find_nearest_npc_anticitizen(self.x, self.y, max_dist=32.0)

        if not player_wanted and self.npc_target and self.npc_target.alive and getattr(self.npc_target, 'npc_wanted', False):
            target = self.npc_target
            dist_to_t = math.hypot(self.x - target.x, self.y - target.y)
            can_see_t = self.can_see_point(target.x, target.y, game)

            self.ai_state = AI_ATTACK
            self.weapon_drawn = True
            self.last_known_px = target.x
            self.last_known_py = target.y
            self.facing_yaw = math.atan2(target.y - self.y, target.x - self.x)

            if self.alert_voice_timer <= 0:
                self.alert_voice_timer = random.uniform(5.5, 9.5)
                vo_line = random.choice(COMBINE_VOICE_LINES[:60])
                game.add_log('sys', f'Combine CP #{self.id}: "Engaging Anti-Citizen #{target.id}! {vo_line}"', priority='ambient')
                game.play_combine_vo(self.x, self.y)

            if self.weapon_type == 'stunstick':
                self._navigate_to(target.x, target.y, self.run_speed, dt)
                if dist_to_t <= 1.95 and self.melee_cooldown <= 0:
                    self.melee_timer = 0.45
                    self.melee_cooldown = 0.85
                    self.attack_flash = 0.5
                    target.take_damage(28, game, source='mcpd')
                    game.snd_metal.play()
                    game.snd_combine_hit.play()
                    game.add_log('warn', f'Civil Protection #{self.id} strikes Anti-Citizen #{target.id} with Stunstick! (-28 HP)')
                return
            elif self.weapon_type == 'pistol':
                dx = target.x - self.x
                dy = target.y - self.y
                d = dist_to_t or 1.0

                if dist_to_t > 20.0 or not can_see_t:
                    self._navigate_to(target.x, target.y, self.speed * 1.3, dt)
                elif dist_to_t > 8.0:
                    self._navigate_to(target.x, target.y, self.speed * 1.25, dt)
                elif dist_to_t < 3.5:
                    self.vx = -(dx / d) * self.speed * 1.2
                    self.vy = -(dy / d) * self.speed * 1.2
                else:
                    if self.strafe_timer > 1.4:
                        self.strafe_timer = 0
                        self.strafe_dir *= -1
                    perp_x, perp_y = -dy / d, dx / d
                    self.vx = (dx / d) * self.speed * 0.2 + perp_x * self.speed * self.strafe_dir * 0.8
                    self.vy = (dy / d) * self.speed * 0.2 + perp_y * self.speed * self.strafe_dir * 0.8

                # Hitscan firing check with wall & closed door obstacle testing
                if can_see_t and self.shoot_timer > self.shoot_interval and dist_to_t <= 22.0:
                    self.shoot_timer = 0
                    self.attack_flash = 0.35
                    game.snd_pistol.play()

                    steps = max(1, int(dist_to_t / 0.20))
                    step_x = dx / steps
                    step_y = dy / steps
                    curr_x, curr_y = self.x, self.y
                    bullet_blocked = False
                    block_hit_x, block_hit_y = 0.0, 0.0
                    block_nx, block_ny = 0.0, 0.0
                    for _ in range(steps):
                        curr_x += step_x
                        curr_y += step_y
                        mx, my = int(curr_x), int(curr_y)
                        if 0 <= mx < MAP_W and 0 <= my < MAP_H:
                            cell = MAP[my][mx]
                            if cell in (0, 7):
                                continue
                            if cell == 6 and game.is_door_open(my, mx):
                                continue
                            bullet_blocked = True
                            block_hit_x = curr_x
                            block_hit_y = curr_y
                            if abs(step_x) > abs(step_y):
                                block_nx = -1.0 if step_x > 0 else 1.0
                                block_ny = 0.0
                            else:
                                block_nx = 0.0
                                block_ny = -1.0 if step_y > 0 else 1.0
                            break
                        else:
                            bullet_blocked = True
                            block_hit_x, block_hit_y = curr_x, curr_y
                            break

                    if bullet_blocked:
                        game.spawn_wall_bullet_decal(block_hit_x, block_hit_y, 0.85, block_nx, block_ny)
                        game.tracers.append([
                            self.x, 0.85, self.y,
                            block_hit_x, 0.85, block_hit_y,
                            (1.0, 0.85, 0.25), 0.12
                        ])
                    else:
                        game.tracers.append([
                            self.x, 0.85, self.y,
                            target.x, 0.75, target.y,
                            (1.0, 0.85, 0.25), 0.12
                        ])
                        target.take_damage(16, game, source='mcpd')
                        game.add_log('warn', f'Officer #{self.id} shoots Anti-Citizen #{target.id} with USP Match 9mm! (-16 HP)')
                return

        # ── PEACEFUL PATROL AT 0 STARS (NO UNPROVOKED COMBAT) ──
        if not in_spawn_grace and not player_wanted:
            self.weapon_drawn = False
            # Physical officer bump check (separation push)
            if 0.01 < dist_to_p < 0.95:
                push_x = (game.player_x - self.x) / dist_to_p
                push_y = (game.player_y - self.y) / dist_to_p
                game.apply_player_knockback(push_x, push_y, dist=0.10)
                self.vx -= push_x * 1.5
                self.vy -= push_y * 1.5

                if getattr(game, 'bump_cooldown', 0.0) <= 0:
                    game.bump_cooldown = 4.0
                    if getattr(game, 'compliance_chronometer', 0.0) <= 0:
                        game.compliance_chronometer = 15.0
                        game.telemetry_active = True
                        game.compliance_stillness_timer = 0.0
                        game.telemetry_warn_step = 15
                        game.telemetry_officer_id = self.id
                        game.snd_radio.play()
                        game.play_combine_vo(self.x, self.y)
                        game.add_log('warn', f'Civil Protection #{self.id}: "Citizen, halt! Wave telemetry lock engaged — 15 SECONDS TO FREEZE AND COMPLY."')

            # Unlawful brandishing trigger in close range (< 4.2m)
            elif can_see_p and dist_to_p < 4.2 and getattr(game, 'current_weapon', 0) > 0 and getattr(game, 'compliance_chronometer', 0.0) <= 0 and getattr(game, 'bump_cooldown', 0.0) <= 0:
                game.bump_cooldown = 4.0
                game.compliance_chronometer = 15.0
                game.telemetry_active = True
                game.compliance_stillness_timer = 0.0
                game.telemetry_warn_step = 15
                game.telemetry_officer_id = self.id
                game.snd_radio.play()
                game.play_combine_vo(self.x, self.y)
                game.add_log('warn', f'Civil Protection #{self.id}: "Weapon brandishing detected! 15 SECONDS TO FREEZE AND DROP WEAPON."')

            # ── 15-SECOND COMPLIANCE CHRONOMETER & WAVE TELEMETRY CHECKS ──
            if getattr(game, 'compliance_chronometer', 0.0) > 0 and getattr(game, 'telemetry_officer_id', None) == self.id:
                self.facing_yaw = math.atan2(game.player_y - self.y, game.player_x - self.x)
                self.vx *= 0.2
                self.vy *= 0.2

                # Wave telemetry scan: test if target has frozen completely
                p_moving = (abs(game.player_vx) > 0.08 or abs(game.player_vy) > 0.08 or getattr(game, 'weapon_fired', 0) > 0 or dist_to_p > 13.0)
                if not p_moving:
                    # Player complies and stays still
                    game.compliance_stillness_timer += dt
                    if game.compliance_stillness_timer >= 3.5:
                        game.compliance_chronometer = 0.0
                        game.telemetry_active = False
                        game.telemetry_officer_id = None
                        game.bump_cooldown = 5.0
                        game.play_combine_vo(self.x, self.y)
                        game.add_log('sys', f'Civil Protection #{self.id}: "Wave telemetry scan cleared: Subject compliant. Move along, citizen."')
                else:
                    # Player fails to freeze: chronometer ticks down
                    game.compliance_stillness_timer = 0.0
                    game.compliance_chronometer -= dt

                    if game.compliance_chronometer <= 10.0 and game.telemetry_warn_step == 15:
                        game.telemetry_warn_step = 10
                        game.play_combine_vo(self.x, self.y)
                        game.add_log('warn', f'Civil Protection #{self.id}: "Telemetry warning: Movement detected! 10 seconds to freeze!"')
                    elif game.compliance_chronometer <= 5.0 and game.telemetry_warn_step == 10:
                        game.telemetry_warn_step = 5
                        game.play_combine_vo(self.x, self.y)
                        game.add_log('danger', f'Civil Protection #{self.id}: "FINAL WARNING: 5 seconds before LETHAL FORCE OVERRIDE!"')
                    elif game.compliance_chronometer <= 0.0:
                        # Lethal Override Trigger: Level 5-Star Wanted Level!
                        game.compliance_chronometer = 0.0
                        game.telemetry_active = False
                        game.telemetry_officer_id = None
                        game.wanted_level = 5
                        game.trigger_overwatch_announcement("WARNING: CITIZEN NON-COMPLIANCE. LETHAL OVERRIDE AUTHORIZED. TERMINAL PROSECUTION ENGAGED", force=True)
                        game.add_log('danger', f'Civil Protection #{self.id}: "FAILURE TO COMPLY! LETHAL OVERRIDE ENGAGED! LEVEL 5 STARS!"')
                        self.ai_state = AI_ATTACK
                        self.weapon_drawn = True

            # Idle face player if walking close peacefully
            elif dist_to_p < 3.2 and can_see_p:
                self.facing_yaw = math.atan2(game.player_y - self.y, game.player_x - self.x)
                self.vx *= 0.3
                self.vy *= 0.3

        # ── COMBAT AT WANTED LEVEL >= 1 OR ACTIVE SEARCH ──
        elif not in_spawn_grace and (player_wanted or self.search_timer > 0):
            if can_see_p:
                self.ai_state = AI_ATTACK
                self.last_known_px = game.player_x
                self.last_known_py = game.player_y
                self.search_timer = 18.0  # 18-second investigation memory
                self.weapon_drawn = True
                self.facing_yaw = math.atan2(game.player_y - self.y, game.player_x - self.x)

                if self.weapon_type == 'stunstick':
                    if self.alert_voice_timer <= 0:
                        self.alert_voice_timer = 6.5
                        vo_line = random.choice(COMBINE_VOICE_LINES[:60])
                        game.add_log('sys', f'Combine CP #{self.id}: "{vo_line}"', priority='ambient')
                        game.play_combine_vo(self.x, self.y)

                    self._navigate_to(game.player_x, game.player_y, self.run_speed, dt)
                    if dist_to_p <= 1.95 and self.melee_cooldown <= 0:
                        self.melee_timer = 0.45
                        self.melee_cooldown = 0.85
                        self.attack_flash = 0.5
                        game.player_take_damage(20)
                        k_dir_x = (game.player_x - self.x) / (dist_to_p or 1.0)
                        k_dir_y = (game.player_y - self.y) / (dist_to_p or 1.0)
                        game.apply_player_knockback(k_dir_x, k_dir_y, dist=0.35)
                        game.snd_metal.play()
                        game.snd_combine_hit.play()
                        game.damage_flash = 0.55
                        game.screen_shake = max(game.screen_shake, 0.35)
                        game.add_log('danger', f'Officer #{self.id} smacks you with Stunstick! (-20 HP)')
                    return

                elif self.weapon_type == 'pistol':
                    # Aim nerf: max firing distance is 24.0m
                    if dist_to_p > 24.0:
                        self._navigate_to(game.player_x, game.player_y, self.speed * 1.3, dt)
                    else:
                        dx, dy = game.player_x - self.x, game.player_y - self.y
                        d = dist_to_p or 1.0
                        if dist_to_p > 9.0:
                            self._navigate_to(game.player_x, game.player_y, self.speed * 1.25, dt)
                        elif dist_to_p < 4.0:
                            self.vx = -(dx / d) * self.speed * 1.2
                            self.vy = -(dy / d) * self.speed * 1.2
                        else:
                            if self.strafe_timer > 1.4:
                                self.strafe_timer = 0
                                self.strafe_dir *= -1
                            perp_x, perp_y = -dy / d, dx / d
                            self.vx = (dx / d) * self.speed * 0.2 + perp_x * self.speed * self.strafe_dir * 0.8
                            self.vy = (dy / d) * self.speed * 0.2 + perp_y * self.speed * self.strafe_dir * 0.8

                        # Hitscan firing check with wall & closed door obstacle testing
                        if self.shoot_timer > self.shoot_interval:
                            self.shoot_timer = 0
                            self.attack_flash = 0.35
                            game.snd_pistol.play()

                            # Raycast bullet in 0.20m steps
                            steps = max(1, int(dist_to_p / 0.20))
                            step_x = dx / steps
                            step_y = dy / steps
                            curr_x, curr_y = self.x, self.y
                            bullet_blocked = False
                            block_hit_x, block_hit_y = 0.0, 0.0
                            block_nx, block_ny = 0.0, 0.0
                            for _ in range(steps):
                                curr_x += step_x
                                curr_y += step_y
                                mx, my = int(curr_x), int(curr_y)
                                if 0 <= mx < MAP_W and 0 <= my < MAP_H:
                                    cell = MAP[my][mx]
                                    if cell in (0, 7):
                                        continue
                                    if cell == 6 and game.is_door_open(my, mx):
                                        continue
                                    bullet_blocked = True
                                    block_hit_x = curr_x
                                    block_hit_y = curr_y
                                    if abs(step_x) > abs(step_y):
                                        block_nx = -1.0 if step_x > 0 else 1.0
                                        block_ny = 0.0
                                    else:
                                        block_nx = 0.0
                                        block_ny = -1.0 if step_y > 0 else 1.0
                                    break
                                else:
                                    bullet_blocked = True
                                    block_hit_x, block_hit_y = curr_x, curr_y
                                    break

                            if bullet_blocked:
                                # Hit wall / door decal
                                game.spawn_wall_bullet_decal(block_hit_x, block_hit_y, 0.85, block_nx, block_ny)
                                game.tracers.append([
                                    self.x, 0.85, self.y,
                                    block_hit_x, 0.85, block_hit_y,
                                    (1.0, 0.85, 0.25), 0.12
                                ])
                            else:
                                # Tracer to player
                                game.tracers.append([
                                    self.x, 0.85, self.y,
                                    game.player_x, 0.82 + game.player_z, game.player_y,
                                    (1.0, 0.85, 0.25), 0.12
                                ])
                                # Distance-scaled inaccuracy spread cone
                                spread = 0.05 if dist_to_p < 6.0 else (0.16 if dist_to_p < 14.0 else 0.28)
                                if random.random() > spread:
                                    if game.wanted_level == 0:
                                        self.damaged_player_first = True
                                        self.self_defense_valid = True
                                    game.player_take_damage(14)
                                    game.damage_flash = 0.32
                                    game.damage_angle = self.facing_yaw
                                    game.add_log('danger', f'Officer #{self.id} shoots you with USP Match 9mm! (-14 HP)')
                    return

            else:
                # ── 18-SECOND SEARCH / INVESTIGATE MEMORY STATE ──
                if self.search_timer > 0:
                    self.search_timer -= dt
                    self.ai_state = AI_SEARCH
                    self.weapon_drawn = True
                    self.facing_yaw = math.atan2(self.last_known_py - self.y, self.last_known_px - self.x)
                    self._navigate_to(self.last_known_px, self.last_known_py, self.speed * 1.2, dt)
                    if math.hypot(self.x - self.last_known_px, self.y - self.last_known_py) < 1.0:
                        self.search_timer = 0.0
                else:
                    self.ai_state = AI_IDLE
                    self.weapon_drawn = False
                    self.vx *= 0.8
                    self.vy *= 0.8

        # ── INTERACTION WITH MONSTERS / RPG REBELS ──
        _, threat = self._find_endangered_civilian(game)
        target = game.find_nearest_hostile(self.x, self.y, ['rpg', 'imp', 'demon'])
        if threat and threat.alive:
            target = threat

        if target and self.dist_to(target.x, target.y) < 18:
            target_dist = self.dist_to(target.x, target.y)
            self.facing_yaw = math.atan2(target.y - self.y, target.x - self.x)
            self.weapon_drawn = True

            dx, dy = target.x - self.x, target.y - self.y
            d = math.sqrt(dx * dx + dy * dy) or 1
            if self.weapon_type == 'stunstick':
                self._navigate_to(target.x, target.y, self.run_speed, dt)
                if target_dist <= 1.95 and self.melee_cooldown <= 0:
                    self.melee_timer = 0.45
                    self.melee_cooldown = 0.85
                    self.attack_flash = 0.5
                    target.take_damage(25, game, source='mcpd')
                    game.snd_metal.play()
                    game.snd_combine_hit.play()
            else:
                if target_dist > 6:
                    self._navigate_to(target.x, target.y, self.speed * 1.2, dt)
                elif target_dist > 3:
                    perp_x, perp_y = -dy / d, dx / d
                    self.vx = (dx / d) * self.speed * 0.3 + perp_x * self.speed * self.strafe_dir
                    self.vy = (dy / d) * self.speed * 0.3 + perp_y * self.speed * self.strafe_dir
                else:
                    self.vx = -(dx / d) * self.speed * 1.5
                    self.vy = -(dy / d) * self.speed * 1.5

                if self.shoot_timer > self.shoot_interval and target_dist < 14:
                    self.shoot_timer = 0
                    self.attack_flash = 0.35
                    game.snd_pistol.play()
                    target.take_damage(16, game, source='mcpd')
            return

        # ── IDLE PATROL ──
        if self.ai_state == AI_IDLE:
            if self.patrol_waypoint < len(self.patrol_points):
                wp_x, wp_y = self.patrol_points[self.patrol_waypoint]
                if math.sqrt((wp_x - self.x)**2 + (wp_y - self.y)**2) < 1.5:
                    self.patrol_waypoint = (self.patrol_waypoint + 1) % len(self.patrol_points)
                    self.path = []
                else:
                    self._navigate_to(wp_x, wp_y, self.speed * 0.65, dt)
            else:
                self.patrol_waypoint = 0

    def die(self, game, source='player'):
        super().die(game, source=source)
        game.mcpd_respawn_queue.append({'timer': 30.0})
        if source != 'player':
            game.trigger_overwatch_announcement(event='response', force=True)
            game.add_log('danger', f'[OVERWATCH DISPATCH] Officer #{self.id} down (Bio-Signal Flatline)! Hostile Anti-Citizen engaged. Response team dispatched!', priority='important')
        else:
            game.add_log('sys', f'[OVERWATCH DISPATCH] Unit #{self.id} Bio-Signal Flatline (10-108) — reinforcement en route')


class ECPUUnit(Entity):
    def __init__(self, x, y, sprite=None):
        super().__init__(x, y, 'ecpu', sprite)
        self.health = 500
        self.max_health = 500
        self.speed = 2.2
        self.shoot_interval = 1.6
        self.patrol_angle = random.uniform(0, math.pi * 2)
        self.radio_timer = 0
        self.radio_interval = 3.5 + random.random() * 4.0
        self.home_x = x
        self.home_y = y
        self.damage_given = 25
        self.pain_chance = 0.15

    def update(self, dt, game):
        super().update(dt, game)
        self.radio_timer += dt
        if self.ai_state == AI_PAIN:
            return

        if self.ai_state == AI_IDLE:
            self.patrol_angle += dt * 0.4
            tx = self.home_x + math.cos(self.patrol_angle) * 2.5
            ty = self.home_y + math.sin(self.patrol_angle) * 2.5
            dx, dy = tx - self.x, ty - self.y
            d = math.sqrt(dx * dx + dy * dy)
            if d > 0.1:
                self.vx = (dx / d) * self.speed * 0.5
                self.vy = (dy / d) * self.speed * 0.5
        elif self.ai_state in (AI_ALERT, AI_CHASE, AI_ATTACK):
            target = game.find_nearest_hostile(self.x, self.y, ['rpg', 'imp', 'demon'])
            if target and self.dist_to(target.x, target.y) < 14:
                dx, dy = target.x - self.x, target.y - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx = (dx / d) * self.speed
                self.vy = (dy / d) * self.speed
                self.facing_yaw = math.atan2(dy, dx)
                if self.shoot_timer > self.shoot_interval:
                    self.shoot_timer = 0
                    self.attack_flash = 1.0
                    game.fire_combine_ball(self.x, self.y, target.x, target.y, 'ecpu')

        if self.radio_timer > self.radio_interval:
            self.radio_timer = 0
            self.radio_interval = 6.0 + random.random() * 8.0
            if self.dist_to(game.player_x, game.player_y) < 18.0:
                vo_line = random.choice(COMBINE_VOICE_LINES)
                game.add_log('sys', f'Overwatch Elite #{self.id}: "{vo_line}"', priority='ambient')
                game.play_combine_vo(self.x, self.y)
            else:
                game.play_radio_click(self.x, self.y)



class MilitaryUnit(Entity):
    def __init__(self, x, y, sprite=None):
        super().__init__(x, y, 'military', sprite)
        self.health = 250
        self.max_health = 250
        self.speed = 2.0
        self.shoot_interval = 0.9
        self.damage_given = 20
        self.pain_chance = 0.1

    def update(self, dt, game):
        super().update(dt, game)
        if getattr(game, 'spawn_protection_timer', 0) > 0:
            self.see_player = False
        if self.ai_state == AI_PAIN:
            return

        if self.ai_state == AI_IDLE:
            self.vx = 0
            self.vy = 0
            if self.see_player and (game.wanted_level >= 4 or (game.player_y >= 28 and game.player_x >= 32)):
                self.ai_state = AI_CHASE
                game.add_log('admin', f'[MILITARY] Target acquired by Heavy Unit #{self.id}')
                if game.wanted_level < 4:
                    game.add_wanted(4)
        elif self.ai_state in (AI_ALERT, AI_CHASE):
            target_dist = self.dist_to(game.player_x, game.player_y)
            self.facing_yaw = math.atan2(game.player_y - self.y, game.player_x - self.x)
            if target_dist > 8 and self.see_player:
                self._navigate_to(game.player_x, game.player_y, self.speed, dt)
            else:
                self.vx = 0
                self.vy = 0

            if self.see_player and self.shoot_timer > self.shoot_interval:
                self.shoot_timer = 0
                self.attack_flash = 1.0
                game.player_take_damage(self.damage_given)
                game.add_log('warn', f'[MILITARY] Hit by Heavy Unit #{self.id}')
                game._play_spatial(game.snd_ar2, self.x, self.y)


class RPGGanger(Entity):
    def __init__(self, x, y, sprite=None):
        super().__init__(x, y, 'rpg', sprite)
        self.health = 80
        self.max_health = 80
        self.speed = 2.5
        self.shoot_interval = 1.6 + random.random()
        self.move_timer = 0
        self.damage_given = 40
        self.pain_chance = 0.5

    def update(self, dt, game):
        super().update(dt, game)
        if getattr(game, 'spawn_protection_timer', 0) > 0:
            self.see_player = False
        self.move_timer += dt
        if self.ai_state == AI_PAIN:
            return

        if self.move_timer > 0.8:
            self.move_timer = 0
            if self.see_player and self.ai_state >= AI_ALERT:
                dx, dy = game.player_x - self.x, game.player_y - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx = (dx / d) * self.speed * 1.5 + random.uniform(-1, 1)
                self.vy = (dy / d) * self.speed * 1.5 + random.uniform(-1, 1)
            else:
                self.vx = random.uniform(-1, 1) * self.speed * 2
                self.vy = random.uniform(-1, 1) * self.speed * 2

        if self.shoot_timer > self.shoot_interval:
            self.shoot_timer = 0
            if self.see_player and self.dist_to(game.player_x, game.player_y) < 15:
                self.facing_yaw = math.atan2(game.player_y - self.y, game.player_x - self.x)
                self.attack_flash = 1.0
                game.fire_rpg_rocket(self.x, self.y, game.player_x, game.player_y, self)
                self.ai_state = AI_ATTACK
            else:
                target = game.find_nearest_hostile(self.x, self.y, ['civilian', 'mcpd', 'ecpu'])
                if target:
                    d = self.dist_to(target.x, target.y)
                    self.facing_yaw = math.atan2(target.y - self.y, target.x - self.x)
                    self.attack_flash = 1.0
                    game.fire_rpg_rocket(self.x, self.y, target.x, target.y, self)
                    if d < 3:
                        self.take_damage(25, game)


class ImpEntity(Entity):
    def __init__(self, x, y, sprite=None):
        super().__init__(x, y, 'imp', sprite)
        self.health = 60
        self.max_health = 60
        self.speed = 2.3
        self.shoot_interval = 2.0 + random.random()
        self.damage_given = 15
        self.pain_chance = 0.6
        self.melee_range = 1.6
        self.melee_damage = 20

    def update(self, dt, game):
        super().update(dt, game)
        if self.ai_state == AI_PAIN:
            return

        if self.ai_state == AI_IDLE:
            if random.random() < 0.01:
                angle = random.uniform(0, math.pi * 2)
                self.vx = math.cos(angle) * self.speed * 0.3
                self.vy = math.sin(angle) * self.speed * 0.3
        elif self.ai_state in (AI_ALERT, AI_CHASE, AI_ATTACK):
            in_grace = getattr(game, 'spawn_protection_timer', 0) > 0
            if in_grace:
                best_tx, best_ty = 0, 0
                best_dist = 9999.0
            else:
                best_tx, best_ty = game.player_x, game.player_y
                best_dist = self.dist_to(game.player_x, game.player_y)
            best_entity = None
            for e in game.entities:
                if not e.alive or e.type not in ('mcpd', 'ecpu', 'civilian'):
                    continue
                d = self.dist_to(e.x, e.y)
                if d < best_dist and d < 20:
                    best_dist = d
                    best_tx, best_ty = e.x, e.y
                    best_entity = e

            dist = best_dist
            can_see = self.can_see_point(best_tx, best_ty)
            self.facing_yaw = math.atan2(best_ty - self.y, best_tx - self.x)

            if dist < self.melee_range:
                if self.shoot_timer > 0.5:
                    self.shoot_timer = 0
                    self.attack_flash = 1.0
                    if best_entity:
                        best_entity.take_damage(self.melee_damage, game)
                    elif not in_grace:
                        game.player_take_damage(self.melee_damage)
            elif dist < 18 and can_see:
                if dist > 4:
                    self._navigate_to(best_tx, best_ty, self.speed, dt)
                else:
                    dx, dy = best_tx - self.x, best_ty - self.y
                    d = math.sqrt(dx * dx + dy * dy) or 1
                    self.vx = (dx / d) * self.speed * 0.3 + random.uniform(-2, 2)
                    self.vy = (dy / d) * self.speed * 0.3 + random.uniform(-2, 2)
                if self.shoot_timer > self.shoot_interval:
                    self.shoot_timer = 0
                    self.attack_flash = 1.0
                    game.fire_imp_fireball(self.x, self.y, best_tx, best_ty)
            elif self.last_known_px != 0:
                self._navigate_to(self.last_known_px, self.last_known_py, self.speed * 0.6, dt)


class DemonEntity(Entity):
    def __init__(self, x, y, sprite=None):
        super().__init__(x, y, 'demon', sprite)
        self.health = 160
        self.max_health = 160
        self.speed = 3.6
        self.melee_damage = 30
        self.pain_chance = 0.15
        self.charge_speed = 6.2

    def update(self, dt, game):
        super().update(dt, game)
        if self.ai_state == AI_PAIN:
            return

        if self.ai_state == AI_IDLE:
            if random.random() < 0.005:
                angle = random.uniform(0, math.pi * 2)
                self.vx = math.cos(angle) * self.speed * 0.3
                self.vy = math.sin(angle) * self.speed * 0.3
        elif self.ai_state in (AI_ALERT, AI_CHASE, AI_ATTACK):
            in_grace = getattr(game, 'spawn_protection_timer', 0) > 0
            if in_grace:
                best_tx, best_ty = 0, 0
                best_dist = 9999.0
            else:
                best_tx, best_ty = game.player_x, game.player_y
                best_dist = self.dist_to(game.player_x, game.player_y)
            best_entity = None
            for e in game.entities:
                if not e.alive or e.type not in ('mcpd', 'ecpu', 'civilian'):
                    continue
                d = self.dist_to(e.x, e.y)
                if d < best_dist and d < 20:
                    best_dist = d
                    best_tx, best_ty = e.x, e.y
                    best_entity = e

            dist = best_dist
            self.facing_yaw = math.atan2(best_ty - self.y, best_tx - self.x)
            if dist < 1.6:
                if self.shoot_timer > 0.8:
                    self.shoot_timer = 0
                    if best_entity:
                        best_entity.take_damage(self.melee_damage, game)
                    else:
                        game.player_take_damage(self.melee_damage)
                        game._play_spatial(game.snd_metal, self.x, self.y)
            elif self.can_see_point(best_tx, best_ty):
                spd = self.charge_speed if dist < 8 else self.speed
                self._navigate_to(best_tx, best_ty, spd, dt)
            elif self.last_known_px != 0:
                self._navigate_to(self.last_known_px, self.last_known_py, self.speed * 0.7, dt)


class PropEntity(Entity):
    def __init__(self, x, y, prop_type, sprite=None):
        super().__init__(x, y, prop_type, sprite)
        self.prop_type = prop_type
        if prop_type == 'explosive_barrel':
            self.health = 45
            self.max_health = 45
        elif prop_type in ('crate', 'barrel'):
            self.health = 90
            self.max_health = 90
        else:
            self.health = 200
            self.max_health = 200
        self.speed = 0
        self.vx = random.uniform(-1.5, 1.5) if prop_type == 'charger' else 0.0
        self.vy = random.uniform(-1.5, 1.5) if prop_type == 'charger' else 0.0
        self.z = 0.0
        self.vz = 0.0
        self.buoyancy_phase = random.uniform(0.0, math.pi * 2.0)

    def update(self, dt, game):
        self.age += dt
        if not self.alive:
            return
        # Push interaction if player walks into physics prop
        pdx = self.x - game.player_x
        pdy = self.y - game.player_y
        pdist = math.sqrt(pdx * pdx + pdy * pdy)
        if 0.05 < pdist < 0.72:
            push_f = (0.72 - pdist) * 14.0
            self.vx += (pdx / pdist) * push_f * dt
            self.vy += (pdy / pdist) * push_f * dt

        mx, my = int(self.x), int(self.y)
        self.in_water = (0 <= mx < MAP_W and 0 <= my < MAP_H and MAP[my][mx] == 7)

        # Source Engine vphysics fluid drag & Archimedes water buoyancy
        drag = 0.91 if self.in_water else 0.82
        self.vx *= drag
        self.vy *= drag

        if self.in_water:
            # Gentle current drift + Archimedes wave bobbing
            wave_target = -0.10 + math.sin(game.hud_pulse * 3.4 + self.x * 1.4 + self.y * 1.2 + self.buoyancy_phase) * 0.065
            spring_acc = (wave_target - self.z) * 18.0 - self.vz * 4.5
            self.vz += spring_acc * dt
            self.z += self.vz * dt
            self.facing_yaw += math.sin(game.hud_pulse * 1.8 + self.buoyancy_phase) * 0.25 * dt
        else:
            if self.z < 0.0 or self.vz != 0.0:
                self.z = max(0.0, self.z + self.vz * dt)
                self.vz -= 9.8 * dt
                if self.z <= 0.0:
                    self.z = 0.0
                    self.vz = 0.0

        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        nmx, nmy = int(nx), int(ny)
        if 0 <= nmx < MAP_W and 0 <= nmy < MAP_H:
            if MAP[nmy][nmx] in (0, 7) or (MAP[nmy][nmx] == 6 and game.is_door_open(nmy, nmx)):
                self.x = nx
                self.y = ny
            else:
                self.vx *= -0.6
                self.vy *= -0.6

    def take_damage(self, amt, game, source=None):
        if getattr(game, 'cheat_mode', False) and source == 'player':
            amt *= 2.0
        self.health -= amt
        if source == 'player' and hasattr(game, 'register_player_hit'):
            game.register_player_hit(
                f"VPHYSICS PROP ({self.prop_type.upper()}) #{self.id}",
                max(0, self.health),
                getattr(self, 'max_health', 45),
                is_kill=(self.health <= 0),
                is_metal=(self.prop_type != 'crate'),
            )
        if self.health > 0:
            if self.prop_type == 'crate' and getattr(game, 'snd_crate_impact_list', None):
                imp_snd = random.choice(game.snd_crate_impact_list)
            elif self.prop_type in ('barrel', 'explosive_barrel') and getattr(game, 'snd_barrel_impact_list', None):
                imp_snd = random.choice(game.snd_barrel_impact_list)
            else:
                imp_snd = game.snd_crowbar if self.prop_type == 'crate' else game.snd_metal
            game._play_spatial(imp_snd, self.x, self.y)
        else:
            self.die(game)

    def die(self, game):
        if not self.alive:
            return
        self.alive = False
        self.ai_state = AI_DEAD
        game.spawn_explosion(self.x, self.y)
        if self.prop_type == 'explosive_barrel':
            game.play_explosion(self.x, self.y)
            game.screen_shake = max(game.screen_shake, 0.75)
            game.add_log('danger', f'[VPHYSICS] Explosive Barrel #{self.id} detonated!')
            for e in game.entities:
                if e.alive and e is not self:
                    d = math.sqrt((e.x - self.x) ** 2 + (e.y - self.y) ** 2)
                    if d < 4.5:
                        e.take_damage(int(110 * (1.0 - d / 4.5)), game, source='player')
                        e.vx += ((e.x - self.x) / (d or 1.0)) * 9.0
                        e.vy += ((e.y - self.y) / (d or 1.0)) * 9.0
        else:
            if self.prop_type == 'crate' and getattr(game, 'snd_crate_break_list', None):
                brk_snd = random.choice(game.snd_crate_break_list)
            elif getattr(game, 'snd_barrel_impact_list', None):
                brk_snd = random.choice(game.snd_barrel_impact_list)
            else:
                brk_snd = game.snd_crowbar if self.prop_type == 'crate' else game.snd_metal
            game._play_spatial(brk_snd, self.x, self.y)
            game.add_log('info', f'[VPHYSICS] Prop {self.prop_type} #{self.id} shattered')


# ═══════════════════════════════════════════════════
#  PROJECTILES & EXPLOSIONS
# ═══════════════════════════════════════════════════
class CombineBall:
    def __init__(self, x, y, tx, ty, owner):
        self.x = x
        self.y = y
        self.owner = owner
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 12
        self.vx = ((tx - x) / d) * self.speed
        self.vy = ((ty - y) / d) * self.speed
        self.alive = True
        self.age = 0
        self.proj_type = 'combine'

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        mx, my = int(self.x), int(self.y)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            self._explode(game)
            return
        if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self._explode(game)
            return
        if self.age > 6:
            self._explode(game)
            return

        for e in game.entities:
            if not e.alive or e.type == self.owner:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 0.8:
                e.take_damage(9999, game, source=self.owner)
                game.add_log('sys', f'[AMMO SHIFT] combine_ball vaporized #{e.id} ({e.type})')
                self._explode(game)
                return

        if self.owner != 'player':
            pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
            if pd < 0.6:
                game.player_take_damage(25)
                self._explode(game)

    def _explode(self, game):
        if not self.alive:
            return
        self.alive = False
        game.spawn_explosion(self.x, self.y)
        game.play_combine_hit(self.x, self.y)
        for e in game.entities:
            if not e.alive or e.type == self.owner:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 2.5:
                e.take_damage(int(50 * (1 - d / 2.5)), game, source=self.owner)
        game.screen_shake = max(game.screen_shake, 0.2)


class RPGRocket:
    def __init__(self, x, y, tx, ty, owner):
        self.x = x
        self.y = y
        self.owner = owner
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 9
        self.vx = ((tx - x) / d) * self.speed
        self.vy = ((ty - y) / d) * self.speed
        self.alive = True
        self.age = 0
        self.proj_type = 'rocket'

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        mx, my = int(self.x), int(self.y)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            self.detonate(game)
            return
        if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self.detonate(game)
            return
        if self.age > 4:
            self.detonate(game)
            return

        for e in game.entities:
            if not e.alive or e is self.owner:
                continue
            if math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2) < 0.7:
                self.detonate(game)
                return

        if self.owner is not None:
            if math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2) < 0.6:
                game.player_take_damage(35)
                self.detonate(game)

    def detonate(self, game):
        if not self.alive:
            return
        self.alive = False
        game.spawn_explosion(self.x, self.y)
        game.play_explosion(self.x, self.y)
        for e in game.entities:
            if not e.alive:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 3.5:
                e.take_damage(int(80 * (1 - d / 3.5)), game, source='player' if self.owner is None else None)
                e.vx += ((e.x - self.x) / (d or 1)) * 6
                e.vy += ((e.y - self.y) / (d or 1)) * 6
        if self.owner is not None:
            pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
            if pd < 3:
                game.player_take_damage(int(30 * (1 - pd / 3)))


class ImpFireball:
    def __init__(self, x, y, tx, ty):
        self.x = x
        self.y = y
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 8
        self.vx = ((tx - x) / d) * self.speed
        self.vy = ((ty - y) / d) * self.speed
        self.alive = True
        self.age = 0
        self.proj_type = 'fireball'

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt
        mx, my = int(self.x), int(self.y)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            self.alive = False
            return
        if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self.alive = False
            return
        if self.age > 5:
            self.alive = False
            return
        if math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2) < 0.5:
            game.player_take_damage(15)
            self.alive = False


class BFGBall:
    def __init__(self, x, y, tx, ty):
        self.x = x
        self.y = y
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 6.5
        self.vx = ((tx - x) / d) * self.speed
        self.vy = ((ty - y) / d) * self.speed
        self.alive = True
        self.age = 0
        self.proj_type = 'bfg'
        self.trail_timer = 0

    def update(self, dt, game):
        self.age += dt
        self.trail_timer += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        mx, my = int(self.x), int(self.y)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            self.detonate(game)
            return
        if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self.detonate(game)
            return
        if self.age > 6:
            self.detonate(game)
            return

        if self.trail_timer > 0.2:
            self.trail_timer = 0
            for e in game.entities:
                if e.alive and math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2) < 4.5:
                    e.take_damage(35, game, source='player')

        for e in game.entities:
            if e.alive and math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2) < 0.8:
                self.detonate(game)
                return

    def detonate(self, game):
        if not self.alive:
            return
        self.alive = False
        game.spawn_explosion(self.x, self.y)
        game.play_explosion(self.x, self.y)
        for e in game.entities:
            if not e.alive:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 8:
                e.take_damage(int(220 * (1 - d / 8)), game, source='player')
                e.vx += ((e.x - self.x) / (d or 1)) * 10
                e.vy += ((e.y - self.y) / (d or 1)) * 10
        game.screen_shake = 1.0
        game.add_log('admin', f'[PRESIDENTIAL STRIKE] Impact at ({self.x:.1f}, {self.y:.1f})')


class Explosion:
    def __init__(self, x, y, sprite=None):
        self.x = x
        self.y = y
        self.life = 1.0
        self.alive = True
        # 3D debris particles
        self.debris = [
            [0.0, 0.3, 0.0, random.uniform(-4, 4), random.uniform(2, 7), random.uniform(-4, 4)]
            for _ in range(10)
        ]

    def update(self, dt):
        self.life -= dt * 2.2
        for p in self.debris:
            p[0] += p[3] * dt
            p[1] += p[4] * dt
            p[2] += p[5] * dt
            p[4] -= 12.0 * dt
            if p[1] < 0.05:
                p[1] = 0.05
        if self.life <= 0:
            self.alive = False


class Pickup:
    def __init__(self, x, y, pickup_type, sprite=None):
        self.x = x
        self.y = y
        self.type = pickup_type
        self.alive = True
        self.bob_timer = random.uniform(0, math.pi * 2)

    def update(self, dt, game):
        self.bob_timer += dt * 3
        d = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        if d < 1.1:
            self.try_pickup(game)

    def try_pickup(self, game):
        defn = PICKUP_DEFS.get(self.type)
        if not defn:
            return
        picked = False
        if 'heal' in defn and game.player_health < 100:
            game.player_health = min(100, game.player_health + defn['heal'])
            picked = True
        if 'armor' in defn and game.player_armor < 200:
            game.player_armor = min(200, game.player_armor + defn['armor'])
            picked = True
        if 'ammo' in defn:
            atype, amount = defn['ammo']
            max_ammo = game.ammo_max.get(atype, 999)
            if game.ammo.get(atype, 0) < max_ammo:
                game.ammo[atype] = min(max_ammo, game.ammo.get(atype, 0) + amount)
                picked = True
        if 'berserk' in defn:
            game.berserk_timer = 60.0
            game.player_health = max(game.player_health, 100)
            picked = True
        if 'invuln' in defn:
            game.invuln_timer = defn['invuln']
            picked = True

        if picked:
            self.alive = False
            game.play_pickup()
            game.add_log('info', f'Picked up {defn["label"]}')
            game.items_collected += 1


# ═══════════════════════════════════════════════════
#  MAIN 3D GAME ENGINE CLASS
# ═══════════════════════════════════════════════════
class Game:
    def __init__(self):
        print_colorful_launcher_banner()

        # Initialize Live External Overwatch Terminal Log File & Secondary Console Window
        self.live_log_proc = None
        try:
            with open(LIVE_LOG_FILE, "w", encoding="utf-8") as lf:
                lf.write("")
        except Exception:
            pass

        # Single main terminal logging: all logs stream cleanly directly to the main terminal (no secondary pop-up window)
        enable_windows_ansi_and_utf8()

        pygame.init()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=1024)
        pygame.mixer.set_num_channels(10)

        pygame.display.gl_set_attribute(pygame.GL_DEPTH_SIZE, 24)
        pygame.display.gl_set_attribute(pygame.GL_DOUBLEBUFFER, 1)
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H), pygame.OPENGL | pygame.DOUBLEBUF)
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.hud_surf = pygame.Surface((SCREEN_W, SCREEN_H), pygame.SRCALPHA)
        self.running = True

        # Game states & Persistent User Settings (Defaults to "Standard User" on new device/install)
        self.root_dir = os.path.dirname(os.path.abspath(__file__))
        self.source_bridge = SourceEngineBridge(self.root_dir)
        self.STATE_INTRO = -1
        self.STATE_TITLE = 0
        self.STATE_PLAYING = 1
        self.game_state = self.STATE_INTRO
        self.intro_timer = 0.0
        self.intro_frame_idx = -1
        self.intro_frame_surf = None
        self.intro_music_started = False
        self.title_timer = 0
        self.title_selection = 0
        self.prev_title_selection = -1
        self.quickinfo_target = None
        self.crosshair_hit_kill = False

        self.user_settings = load_user_settings()
        self.graphics_preset = self.user_settings['graphics_preset']
        self.fog_enabled = bool(self.user_settings['fog_enabled'])
        self.fog_distance = float(self.user_settings['fog_distance'])
        self.max_bullet_decals = int(self.user_settings.get('max_bullet_decals', 500))
        self.bullet_decals = []
        self.total_shots_fired = 0
        self.spawn_protection_timer = 5.0
        self.current_map = self.user_settings['selected_map']
        set_active_map_data(self.current_map)

        # Anti-Spam Clean Logging System (Suppresses ambient chatter & micro-ticks by default)
        self.log_mode = "clean"
        self.last_log_times = {}

        self.paused = False
        self.pause_selection = 0
        self.pause_rects = []
        self.pause_button_rects = []
        self.chunk_dlists = {}
        self.landmarks_dlist = None
        self.water_cells = []
        self.hud_pulse = 0.0
        self.player_in_water = False

        # In-Game Half-Life 2 Map Editor State ([F2] / Pause Menu / Title Menu)
        self.map_editor_active = False
        self.editor_idx = 10  # Defaults to HL2 Combine Armored Street Barrier
        self.editor_yaw = 0.0
        self.editor_target_x = 12.5
        self.editor_target_y = 12.5
        self.placed_objects = []
        self.editor_status_msg = "READY — [LMB] Place  [RMB] Delete  [Q/E/Wheel] Select  [R] Rotate  [F5] Save Map"
        self.editor_status_timer = 0.0

        # Fonts
        self.font_hud = pygame.font.SysFont('Consolas', 14, bold=True)
        self.font_hud_sm = pygame.font.SysFont('Consolas', 12, bold=True)
        self.font_title = pygame.font.SysFont('Consolas', 32, bold=True)
        self.font_console = pygame.font.SysFont('Consolas', 11)
        self.font_large = pygame.font.SysFont('Consolas', 24, bold=True)
        self.font_admin = pygame.font.SysFont('Consolas', 13, bold=True)
        self.font_doom = pygame.font.SysFont('Consolas', 44, bold=True)
        self.font_doom_sm = pygame.font.SysFont('Consolas', 18, bold=True)
        self.font_modern_title = pygame.font.SysFont('Trebuchet MS, Arial, Consolas', 26, bold=True)
        self.font_modern_card = pygame.font.SysFont('Segoe UI, Arial, Trebuchet MS, Consolas', 15, bold=True)
        self.font_modern_desc = pygame.font.SysFont('Segoe UI, Arial, Consolas', 11)
        self.font_modern_tag = pygame.font.SysFont('Consolas, Segoe UI', 11, bold=True)
        self.font_vgui_title = pygame.font.SysFont('Trebuchet MS, Arial', 44, bold=True)
        self.font_vgui_sub = pygame.font.SysFont('Trebuchet MS, Arial', 15, bold=True)
        self.font_vgui_menu = pygame.font.SysFont('Trebuchet MS, Arial', 21, bold=True)
        self.title_button_rects = []

        # Genuine Source Engine TrueType Fonts (hl2crosshairs.ttf & halflife2.ttf)
        hl2_ch_path = os.path.join(self.root_dir, "source_engine", "resource", "hl2crosshairs.ttf")
        hl2_fn_path = os.path.join(self.root_dir, "source_engine", "resource", "halflife2.ttf")
        try:
            self.font_hl2_quickinfo = pygame.font.Font(hl2_ch_path, 38) if os.path.exists(hl2_ch_path) else None
            self.font_hl2_reticle = pygame.font.Font(hl2_ch_path, 28) if os.path.exists(hl2_ch_path) else None
        except Exception:
            self.font_hl2_quickinfo = None
            self.font_hl2_reticle = None
        try:
            self.font_hl2_numbers = pygame.font.Font(hl2_fn_path, 34) if os.path.exists(hl2_fn_path) else self.font_title
            self.font_hl2_weapons = pygame.font.Font(hl2_fn_path, 34) if os.path.exists(hl2_fn_path) else None
            self.font_hl2_weapons_lg = pygame.font.Font(hl2_fn_path, 42) if os.path.exists(hl2_fn_path) else None
            self.font_hl2_logo = pygame.font.Font(hl2_fn_path, 52) if os.path.exists(hl2_fn_path) else None
        except Exception:
            self.font_hl2_numbers = self.font_title
            self.font_hl2_weapons = None
            self.font_hl2_weapons_lg = None
            self.font_hl2_logo = None

        # Initialize OpenGL state & HUD overlay texture
        self._init_opengl()

        # Load real Half-Life 2 WAV sounds from ./assets/hl2/sounds/, ./assets/hl2/sound/, & ./source_engine/sound/
        base_proj = os.path.dirname(os.path.abspath(__file__))
        snd_dirs = [
            os.path.join(base_proj, "assets", "hl2", "sounds"),
            os.path.join(base_proj, "assets", "hl2", "sound"),
            os.path.join(base_proj, "source_engine", "sound"),
        ]

        def load_hl2_snd(wav_name, fallback_fn, dur=0.3, vol=0.45):
            for sdir in snd_dirs:
                p = os.path.join(sdir, wav_name)
                if os.path.exists(p):
                    try:
                        s = pygame.mixer.Sound(p)
                        s.set_volume(vol)
                        return s
                    except Exception:
                        pass
            return gen_sound_buffer(fallback_fn, dur, vol)

        self.snd_metal = load_hl2_snd("stunstick_hit.wav", metal_clang_func, 0.3, 0.35)
        self.snd_crowbar = load_hl2_snd("crowbar_hit1.wav", crowbar_func, 0.15, 0.45)
        self.snd_pistol = load_hl2_snd("pistol_fire.wav", pistol_fire_func, 0.15, 0.5)
        self.snd_smg1 = load_hl2_snd("smg1_fire.wav", pistol_fire_func, 0.1, 0.45)
        self.snd_shotgun = load_hl2_snd("shotgun_fire.wav", shotgun_fire_func, 0.3, 0.55)
        self.snd_ar2 = load_hl2_snd("ar2_fire.wav", ar2_fire_func, 0.08, 0.45)
        self.snd_357 = load_hl2_snd("357_fire.wav", shotgun_fire_func, 0.35, 0.6)
        self.snd_rpg = load_hl2_snd("rpg_fire.wav", rpg_fire_func, 0.5, 0.5)
        self.snd_combine_fire = load_hl2_snd("ar2_altfire.wav", combine_ball_fire_func, 0.25, 0.45)
        self.snd_combine_hit = load_hl2_snd("stunstick_spark.wav", combine_ball_hit_func, 0.2, 0.4)
        self.snd_bfg = gen_sound_buffer(bfg_fire_func, 0.8, 0.6)

        # Genuine Half-Life 2 Explosions (extracted from hl2_sound_misc_dir.vpk)
        self.snd_explosion_list = [
            load_hl2_snd("hl2_explode3.wav", explosion_func, 0.6, 0.55),
            load_hl2_snd("hl2_explode4.wav", explosion_func, 0.6, 0.55),
            load_hl2_snd("hl2_explode5.wav", explosion_func, 0.6, 0.55),
        ]
        self.snd_explosion = self.snd_explosion_list[0]
        self.snd_radio = load_hl2_snd("metrocop_alert.wav", radio_click_func, 0.05, 0.4)

        # Genuine Half-Life 2 Surface-Aware Footsteps (Concrete, Metal, Water Slosh, Dirt)
        self.snd_footsteps_concrete = [
            load_hl2_snd(f"footstep_concrete{i}.wav", footstep_func, 0.1, 0.24) for i in range(1, 5)
        ]
        self.snd_footsteps_metal = [
            load_hl2_snd(f"footstep_metal{i}.wav", footstep_func, 0.1, 0.26) for i in range(1, 5)
        ]
        self.snd_footsteps_water = [
            load_hl2_snd(f"footstep_water{i}.wav", footstep_func, 0.15, 0.34) for i in range(1, 5)
        ]
        self.snd_footsteps_dirt = [
            load_hl2_snd(f"footstep_dirt{i}.wav", footstep_func, 0.1, 0.25) for i in range(1, 5)
        ]
        self.snd_footstep = self.snd_footsteps_concrete[0]

        self.snd_pickup = load_hl2_snd("wpn_select.wav", pickup_func, 0.3, 0.45)
        self.snd_wpn_move = load_hl2_snd("wpn_moveselect.wav", radio_click_func, 0.05, 0.45)
        self.snd_sprint = load_hl2_snd("suit_sprint.wav", radio_click_func, 0.2, 0.45)

        # Genuine Half-Life 2 Security Doors, Chargers, Pickups, Physics Impacts & V8 Vehicles
        self.snd_door = load_hl2_snd("hl2_door_move1.wav", door_func, 0.5, 0.42)
        self.snd_door_unlock = load_hl2_snd("hl2_door_unlock1.wav", door_func, 0.3, 0.45)
        self.snd_car_engine = load_hl2_snd("v8_start_loop1.wav", car_engine_start_func, 0.75, 0.42)
        self.snd_car_skid = load_hl2_snd("v8_skid.wav", car_engine_start_func, 0.4, 0.38)
        self.snd_car_crash_list = [
            load_hl2_snd("vehicle_impact_heavy1.wav", metal_clang_func, 0.4, 0.52),
            load_hl2_snd("vehicle_impact_heavy2.wav", metal_clang_func, 0.4, 0.52),
            load_hl2_snd("vehicle_impact_medium1.wav", metal_clang_func, 0.3, 0.46),
        ]
        self.snd_medshot = load_hl2_snd("hl2_medshot4.wav", pickup_func, 0.3, 0.52)
        self.snd_medshot_no = load_hl2_snd("hl2_medshotno1.wav", radio_click_func, 0.2, 0.45)
        self.snd_suitcharge_ok = load_hl2_snd("hl2_suitchargeok1.wav", pickup_func, 0.3, 0.52)
        self.snd_suitcharge_no = load_hl2_snd("hl2_suitchargeno1.wav", radio_click_func, 0.2, 0.45)
        self.snd_medkit_pickup = load_hl2_snd("hl2_smallmedkit1.wav", pickup_func, 0.3, 0.50)
        self.snd_battery_pickup = load_hl2_snd("hl2_battery_pickup.wav", pickup_func, 0.3, 0.50)
        self.snd_ammo_pickup = load_hl2_snd("hl2_ammo_pickup.wav", pickup_func, 0.3, 0.50)
        self.snd_ammocrate_open = load_hl2_snd("hl2_ammocrate_open.wav", door_func, 0.3, 0.50)
        self.snd_barrel_impact_list = [
            load_hl2_snd(f"metal_barrel_impact{i}.wav", metal_clang_func, 0.25, 0.46) for i in range(1, 4)
        ]
        self.snd_crate_impact_list = [
            load_hl2_snd(f"wood_crate_impact{i}.wav", crowbar_func, 0.25, 0.46) for i in range(1, 4)
        ]
        self.snd_crate_break_list = [
            load_hl2_snd(f"wood_crate_break{i}.wav", crowbar_func, 0.35, 0.52) for i in range(1, 3)
        ]
        self.snd_ricochet_list = [
            load_hl2_snd(f"ric{i}.wav", metal_clang_func, 0.15, 0.36) for i in range(1, 4)
        ]
        self.snd_physcannon_launch_list = [
            load_hl2_snd("physcannon_launch1.wav", combine_ball_fire_func, 0.3, 0.48),
            load_hl2_snd("physcannon_launch2.wav", combine_ball_fire_func, 0.3, 0.48),
        ]

        # EXCLUSIVE Metrocop Death Flatline & Pain Sounds (ONLY for Metro Police NPCs!)
        self.snd_metrocop_pain_list = [
            load_hl2_snd("metrocop_pain1.wav", pain_func, 0.2, 0.40),
            load_hl2_snd("metrocop_pain2.wav", pain_func, 0.2, 0.40),
            load_hl2_snd("metrocop_pain3.wav", pain_func, 0.2, 0.40),
            load_hl2_snd("metrocop_pain4.wav", pain_func, 0.2, 0.40),
        ]
        self.snd_metrocop_death_list = [
            load_hl2_snd("metrocop_die1.wav", death_func, 0.5, 0.50),
            load_hl2_snd("metrocop_die2.wav", death_func, 0.5, 0.50),
            load_hl2_snd("metrocop_die3.wav", death_func, 0.5, 0.50),
            load_hl2_snd("metrocop_die4.wav", death_func, 0.5, 0.50),
        ]
        self.snd_pain = self.snd_metrocop_pain_list[0]
        self.snd_death = self.snd_metrocop_death_list[0]

        # Genuine Half-Life 2 Combine / Metrocop Radio Voice WAV Bank
        self.snd_combine_vo_list = [
            load_hl2_snd(w_name, radio_click_func, 0.25, 0.45)
            for w_name in (
                "metrocop_alert.wav", "metrocop_takedown.wav", "metrocop_vo_citizen.wav",
                "metrocop_vo_movealong.wav", "metrocop_vo_holdit.wav", "metrocop_vo_isolate.wav",
                "metrocop_vo_prosecute.wav", "metrocop_vo_amputate.wav", "metrocop_vo_pickupcan.wav",
                "metrocop_vo_chuckle.wav", "metrocop_vo_10108.wav", "metrocop_vo_malcompliance.wav",
                "metrocop_vo_vacate.wav", "metrocop_vo_sociostable.wav", "metrocop_vo_watchit.wav",
            )
        ]

        # Genuine Half-Life 2 Citizen Pain, Death, Panic & Chatter WAV Banks (for Citizens & all non-Metrocop NPCs!)
        self.snd_citizen_pain_list = [
            load_hl2_snd("citizen_pain1.wav", pain_func, 0.25, 0.48),
            load_hl2_snd("citizen_pain2.wav", pain_func, 0.25, 0.48),
            load_hl2_snd("citizen_pain3.wav", pain_func, 0.25, 0.48),
            load_hl2_snd("citizen_pain4.wav", pain_func, 0.25, 0.48),
            load_hl2_snd("citizen_hit1.wav", pain_func, 0.25, 0.48),
            load_hl2_snd("citizen_hit2.wav", pain_func, 0.25, 0.48),
        ]
        self.snd_citizen_death_list = [
            load_hl2_snd("citizen_die1.wav", pain_func, 0.45, 0.52),
            load_hl2_snd("citizen_die2.wav", pain_func, 0.45, 0.52),
            load_hl2_snd("citizen_die3.wav", pain_func, 0.45, 0.52),
            load_hl2_snd("citizen_die4.wav", pain_func, 0.45, 0.52),
        ]
        self.snd_citizen_panic_list = [
            load_hl2_snd("citizen/cit_panic_help1.wav", pain_func, 0.35, 0.48),
            load_hl2_snd("citizen/cit_panic_run1.wav", pain_func, 0.35, 0.48),
            load_hl2_snd("citizen/cit_panic_run2.wav", pain_func, 0.35, 0.48),
            load_hl2_snd("citizen/cit_panic_run3.wav", pain_func, 0.35, 0.48),
            load_hl2_snd("citizen/cit_panic_getdown.wav", pain_func, 0.35, 0.48),
            load_hl2_snd("citizen_help1.wav", pain_func, 0.35, 0.48),
            load_hl2_snd("citizen_run1.wav", pain_func, 0.35, 0.48),
        ]
        self.snd_citizen_combat_list = [
            load_hl2_snd("citizen/cit_combat_behindyou.wav", radio_click_func, 0.35, 0.50),
            load_hl2_snd("citizen/cit_combat_cp1.wav", radio_click_func, 0.35, 0.50),
            load_hl2_snd("citizen/cit_combat_cp2.wav", radio_click_func, 0.35, 0.50),
            load_hl2_snd("citizen/cit_combat_incoming.wav", radio_click_func, 0.35, 0.50),
            load_hl2_snd("citizen/cit_combat_takecover.wav", radio_click_func, 0.35, 0.50),
            load_hl2_snd("citizen/cit_combat_watchout.wav", radio_click_func, 0.35, 0.50),
        ]
        self.snd_citizen_talk_list = [
            load_hl2_snd("citizen_talk1.wav", radio_click_func, 0.4, 0.45),
            load_hl2_snd("citizen_talk2.wav", radio_click_func, 0.4, 0.45),
            load_hl2_snd("citizen_talk3.wav", radio_click_func, 0.4, 0.45),
        ]

        # Half-Life 2 weapon reload & shotgun pump-action sounds
        self.snd_pistol_reload = load_hl2_snd("pistol_reload.wav", radio_click_func, 0.4, 0.5)
        self.snd_smg1_reload = load_hl2_snd("smg1_reload.wav", radio_click_func, 0.5, 0.5)
        self.snd_shotgun_reload = load_hl2_snd("shotgun_reload.wav", radio_click_func, 0.5, 0.55)
        self.snd_shotgun_reload_list = [
            load_hl2_snd("shotgun_reload1.wav", radio_click_func, 0.4, 0.55),
            load_hl2_snd("shotgun_reload2.wav", radio_click_func, 0.4, 0.55),
            load_hl2_snd("shotgun_reload3.wav", radio_click_func, 0.4, 0.55),
        ]
        self.snd_shotgun_cock = load_hl2_snd("shotgun_cock.wav", radio_click_func, 0.4, 0.72)
        self.snd_ar2_reload = load_hl2_snd("ar2_reload.wav", radio_click_func, 0.6, 0.5)
        self.snd_357_reload = load_hl2_snd("357_reload.wav", radio_click_func, 0.6, 0.5)
        self.snd_rpg_reload = load_hl2_snd("shotgun_cock.wav", radio_click_func, 0.4, 0.5)
        self.snd_police_siren = gen_sound_buffer(police_siren_func, 0.65, 0.36)
        self.siren_sound_timer = 0.0
        self.shotgun_pump_timer = 0.0
        self.shotgun_pump_anim = 0.0

        # ── Overwatch Dispatch System Initialization (Loudspeaker Bank) ──
        self.snd_overwatch_bank = []
        self.snd_overwatch_by_file = {}
        for f_name, caption in OVERWATCH_ANNOUNCEMENTS:
            snd = load_hl2_snd(f"cityvoice/{f_name}", radio_click_func, 0.4, 0.35)
            self.snd_overwatch_bank.append((snd, caption))
            self.snd_overwatch_by_file[f_name] = (snd, caption)
        self.pa_cooldown = 0.0
        self.pa_channel = None
        self.ambient_pa_timer = random.uniform(25.0, 45.0)
        self.snd_radio_on = load_hl2_snd("overwatch/on1.wav", radio_click_func, 0.08, 0.35)
        self.snd_radio_off = load_hl2_snd("overwatch/off2.wav", radio_click_func, 0.08, 0.35)
        self.snd_citadel_alert = load_hl2_snd("citadel_alert.wav", radio_click_func, 0.5, 0.35)

        # Genuine Source Engine VGUI2 Menu Rollover/Click Sounds & Hit Confirmation Audio
        self.snd_ui_rollover = load_hl2_snd("ui_buttonrollover.wav", radio_click_func, 0.04, 0.45)
        self.snd_ui_click = load_hl2_snd("ui_buttonclick.wav", radio_click_func, 0.05, 0.50)
        self.snd_ui_release = load_hl2_snd("ui_buttonclickrelease.wav", radio_click_func, 0.05, 0.52)
        self.snd_hitmarker_list = [
            load_hl2_snd("hitmarker_body1.wav", pistol_fire_func, 0.08, 0.52),
            load_hl2_snd("hitmarker_body2.wav", pistol_fire_func, 0.08, 0.52),
            load_hl2_snd("hitmarker_flesh1.wav", pistol_fire_func, 0.08, 0.52),
        ]

        self.overwatch_current_banner = ""
        self.overwatch_banner_timer = 0.0
        self.title_button_rects = []

        self.sandbox_mode = False
        self.cheat_mode = False
        self.init_game()
        self.start_valve_intro()

    def start_valve_intro(self):
        """Starts the classic Half-Life 2 / Source Engine Valve intro movie (valve.bik + hl2_intro.mp3)."""
        self.game_state = self.STATE_INTRO
        self.intro_timer = 0.0
        self.intro_frame_idx = -1
        self.intro_frame_surf = None
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        intro_mp3 = os.path.join(self.root_dir, "assets", "hl2", "sounds", "hl2_intro.mp3")
        if os.path.exists(intro_mp3):
            try:
                pygame.mixer.music.load(intro_mp3)
                pygame.mixer.music.set_volume(0.65)
                pygame.mixer.music.play()
                self.intro_music_started = True
            except Exception:
                self.intro_music_started = False

    def finish_intro_to_title(self):
        """Transitions from the Valve Source intro scene into the classic Half-Life 2 Main Menu."""
        try:
            pygame.mixer.music.stop()
        except Exception:
            pass
        self.game_state = self.STATE_TITLE
        self.title_timer = 0.0
        pygame.mouse.set_visible(True)
        pygame.event.set_grab(False)
        if hasattr(self, 'snd_ui_release') and self.snd_ui_release:
            self.snd_ui_release.play()

    def render_intro(self, surf):
        """Renders the genuine decoded Half-Life 2 valve.bik intro sequence & Powered by Source splash."""
        w, h = surf.get_size()
        surf.fill((0, 0, 0, 255))
        f_idx = min(119, max(0, int(self.intro_timer * 12.0)))
        if f_idx != self.intro_frame_idx or self.intro_frame_surf is None:
            self.intro_frame_idx = f_idx
            frame_path = os.path.join(self.root_dir, "assets", "hl2", "intro_valve", f"frame_{f_idx:04d}.jpg")
            if os.path.exists(frame_path):
                try:
                    raw_img = pygame.image.load(frame_path)
                    self.intro_frame_surf = pygame.transform.smoothscale(raw_img, (w, h))
                except Exception:
                    self.intro_frame_surf = None

        if self.intro_frame_surf is not None:
            surf.blit(self.intro_frame_surf, (0, 0))

        # Subtle Source Engine Bink Video telemetry & skip prompt
        skip_txt = self.font_console.render("[SPACE / ENTER / CLICK] SKIP VALVE SOURCE INTRO", True, (185, 195, 205))
        surf.blit(skip_txt, (w - skip_txt.get_width() - 28, h - 28))
        bink_txt = self.font_console.render(
            f"VALVE.BIK // NATIVE BINKW32 DECODE • FRAME {f_idx + 1}/120",
            True, (120, 130, 140)
        )
        surf.blit(bink_txt, (28, h - 28))

    def register_player_hit(self, target_name, cur_hp, max_hp, is_kill=False, is_metal=False):
        """Triggers Half-Life 2 hit confirmation audio, tactical crosshair hitmarker, and QuickInfo target telemetry."""
        self.crosshair_hit = 0.45 if is_kill else 0.34
        self.crosshair_hit_kill = bool(is_kill)
        self.quickinfo_target = {
            "name": str(target_name),
            "hp": max(0, int(cur_hp)),
            "max_hp": max(1, int(max_hp)),
            "timer": 2.4,
            "is_kill": bool(is_kill),
        }
        if is_metal:
            if hasattr(self, 'snd_metal') and self.snd_metal:
                self.snd_metal.play()
        elif getattr(self, 'snd_hitmarker_list', None):
            random.choice(self.snd_hitmarker_list).play()

    def _launch_external_log_terminal(self):
        """All game logs are unified in the primary terminal (stdout); no secondary popup window is spawned."""
        pass

    # PA lines grouped by the kind of city event they fit
    PA_EVENT_FILES = {
        'anticitizen': ["f_anticitizenreport_spkr.wav"],
        'unrest': ["f_anticivilevidence_3_spkr.wav", "f_localunrest_spkr.wav", "f_unrestprocedure1_spkr.wav"],
        'response': ["f_protectionresponse_1_spkr.wav", "f_protectionresponse_4_spkr.wav", "f_protectionresponse_5_spkr.wav"],
        'neutralized': ["f_trainstation_cooperation_spkr.wav", "f_rationunitsdeduct_3_spkr.wav"],
        'ambient': [
            "f_confirmcivilstatus_1_spkr.wav", "f_innactionisconspiracy_spkr.wav",
            "f_trainstation_assemble_spkr.wav", "f_trainstation_assumepositions_spkr.wav",
            "f_trainstation_cooperation_spkr.wav", "f_trainstation_inform_spkr.wav",
            "f_trainstation_offworldrelocation_spkr.wav", "f_rationunitsdeduct_3_spkr.wav",
        ],
    }

    def update_overwatch_dispatch(self, dt):
        """Ticks the PA banner/cooldown and plays periodic ambient City Voice broadcasts over the city."""
        if getattr(self, 'overwatch_banner_timer', 0.0) > 0:
            self.overwatch_banner_timer = max(0.0, self.overwatch_banner_timer - dt)
        if getattr(self, 'pa_cooldown', 0.0) > 0:
            self.pa_cooldown = max(0.0, self.pa_cooldown - dt)

        # Ambient City 17 broadcasts (play regardless of player wanted level; silent in Map Editor)
        if self.game_state == self.STATE_PLAYING and not getattr(self, 'map_editor_active', False):
            pending = getattr(self, 'pending_npc_pa', None)
            if pending and self.trigger_overwatch_announcement(event=pending):
                self.pending_npc_pa = None
            self.ambient_pa_timer = getattr(self, 'ambient_pa_timer', 40.0) - dt
            if self.ambient_pa_timer <= 0:
                self.ambient_pa_timer = random.uniform(55.0, 110.0)
                self.trigger_overwatch_announcement(event='ambient')

    def trigger_overwatch_announcement(self, caption=None, event=None, force=False):
        """
        Plays a City 17 PA loudspeaker announcement over the whole city.
        event: 'anticitizen' | 'unrest' | 'response' | 'neutralized' | 'ambient' | None (random)
        force: bypass the anti-overlap cooldown (used for player wanted escalations)
        Returns True if an announcement played.
        """
        if not getattr(self, 'snd_overwatch_bank', None):
            return False
        # Don't stack announcements on top of each other
        busy = self.pa_channel is not None and self.pa_channel.get_busy()
        if not force and (self.pa_cooldown > 0 or busy):
            return False

        snd, def_cap = None, None
        files = self.PA_EVENT_FILES.get(event) if event else None
        if files:
            avail = [f for f in files if f in self.snd_overwatch_by_file]
            if avail:
                snd, def_cap = self.snd_overwatch_by_file[random.choice(avail)]
        if snd is None:
            snd, def_cap = random.choice(self.snd_overwatch_bank)

        if busy and self.pa_channel is not None:
            self.pa_channel.stop()
        used_caption = caption or def_cap
        if hasattr(self, 'snd_radio_on') and self.snd_radio_on:
            self.snd_radio_on.play()
        self.pa_channel = snd.play()
        self.pa_cooldown = 14.0
        self.overwatch_current_banner = used_caption
        self.overwatch_banner_timer = 7.0
        self.add_log('dispatch', f'CITY VOICE PA: "{used_caption}"')
        return True

    def get_chunk_draw_distance(self):
        """Returns active spatial chunk draw distance & entity cull distance for the current graphics preset."""
        if self.graphics_preset == "Potato PC Graphics":
            return 22.0
        elif self.graphics_preset == "Alter Heavy Graphics":
            return 64.0
        return 38.0  # "Standard User"

    def save_current_settings(self):
        self.user_settings['graphics_preset'] = self.graphics_preset
        self.user_settings['fog_enabled'] = bool(self.fog_enabled)
        self.user_settings['fog_distance'] = float(self.fog_distance)
        self.user_settings['max_bullet_decals'] = int(self.max_bullet_decals)
        self.user_settings['selected_map'] = self.current_map
        save_user_settings(self.user_settings)

    def apply_graphics_and_fog_settings(self, rebuild_chunks=True):
        """Applies texture filtering (PS1 GL_NEAREST for Potato PC Graphics; Trilinear Mipmap for Standard/Heavy), fog ON/OFF, and spatial chunk compilation."""
        is_potato = (self.graphics_preset == "Potato PC Graphics")
        min_filt = GL_NEAREST if is_potato else GL_LINEAR_MIPMAP_LINEAR
        mag_filt = GL_NEAREST if is_potato else GL_LINEAR
        if hasattr(self, 'world_textures') and self.world_textures:
            for tid in self.world_textures.values():
                if tid:
                    gl.glBindTexture(GL_TEXTURE_2D, tid)
                    try:
                        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, min_filt)
                    except Exception:
                        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, mag_filt)
                    gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, mag_filt)

        # Sky & Fog color tailored to map
        if self.current_map in ("gm_bigcity", "BigCity5", "driving Test map"):
            sky_r, sky_g, sky_b = (0.64, 0.73, 0.82)
        else:
            sky_r, sky_g, sky_b = (0.71, 0.74, 0.77)
        gl.glClearColor(sky_r, sky_g, sky_b, 1.0)

        if self.fog_enabled:
            gl.glEnable(GL_FOG)
            gl.glFogi(GL_FOG_MODE, GL_LINEAR_FOG)
            fog_col = (c_float * 4)(sky_r, sky_g, sky_b, 1.0)
            gl.glFogfv(GL_FOG_COLOR, fog_col)
            gl.glFogf(GL_FOG_START, max(6.0, self.fog_distance * 0.32))
            gl.glFogf(GL_FOG_END, max(14.0, self.fog_distance))
        else:
            gl.glDisable(GL_FOG)

        if rebuild_chunks:
            self._rebuild_spatial_chunks()
        self.save_current_settings()

    def _init_opengl(self):
        gl.glViewport(0, 0, SCREEN_W, SCREEN_H)
        gl.glClearColor(0.71, 0.74, 0.77, 1.0)
        gl.glEnable(GL_DEPTH_TEST)
        gl.glDepthFunc(GL_LEQUAL)
        gl.glShadeModel(GL_SMOOTH)
        gl.glEnable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        # HUD Texture
        tex_id = c_uint(0)
        gl.glGenTextures(1, byref(tex_id))
        self.hud_tex_id = tex_id.value
        gl.glBindTexture(GL_TEXTURE_2D, self.hud_tex_id)
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
        gl.glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        empty = bytes(SCREEN_W * SCREEN_H * 4)
        gl.glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, SCREEN_W, SCREEN_H, 0, GL_RGBA, GL_UNSIGNED_BYTE, empty)

        # Load genuine Half-Life 2 City-17, Source gm_bigcity, and HL2 Weapon textures
        self.world_textures = generate_battlefield_textures()

        # Compile genuine Valve Civil Protection Metrocop 3D display list
        models_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "hl2", "models")
        model_path = os.path.join(models_dir, "police.obj")
        global METROCOP_DLIST, WEAPON_DLISTS, HEV_HAND_TEX_ID
        self.metrocop_display_list = load_obj_to_display_list(model_path, self.world_textures.get('metrocop_sheet'))
        METROCOP_DLIST = self.metrocop_display_list
        HEV_HAND_TEX_ID = self.world_textures.get('v_hand_sheet', 0)

        # Compile all genuine Valve Half-Life 2 3D Weapon models into OpenGL display lists
        # Weapon 0 (Crowbar) uses genuine 3D half-life_crowbar.glb
        hl2_weapon_objs = {
            0: ("half-life_crowbar.glb", "glb"),
            1: ("w_pistol.obj", "w_pistol"),
            2: ("w_smg1.obj", "w_smg1"),
            3: ("w_shotgun.obj", "w_shotgun"),
            4: ("w_irifle.obj", "w_irifle"),
            5: ("w_357.obj", "w_357"),
            6: ("w_rocket_launcher.obj", "w_rpg_sheet"),
            7: ("w_stunbaton.obj", "w_stunbaton"),
        }
        WEAPON_DLISTS.clear()
        for wid, (model_file, tex_key) in hl2_weapon_objs.items():
            if model_file.endswith(".glb"):
                WEAPON_DLISTS[wid] = load_glb_to_display_list(model_file)
            else:
                obj_full = os.path.join(models_dir, model_file)
                tex_id = self.world_textures.get(tex_key, 0)
                if os.path.exists(obj_full):
                    WEAPON_DLISTS[wid] = load_obj_to_display_list(obj_full, tex_id)
        self.weapon_dlists = WEAPON_DLISTS

        # Compile genuine 3D Industrial Utility Building & Substation Complex (gm_bigcity)
        self.industrial_utility_dlist = load_glb_to_display_list("industrial_utility_building_game-ready.glb")

        # Compile genuine 3D Destroyed High-Rise Apartment Block (gm_bigcity)
        self.destroyed_building_dlist = load_glb_to_display_list("ukrainewar_destroyed_building_block.glb")

        # Big City 5 infrastructure & vehicle display list cache
        self.city_infra_dlist = 0
        self.vehicle_dlists = {}

        # Apply user settings and compile 8x8 spatial chunks for anti-lag rendering
        self.apply_graphics_and_fog_settings(rebuild_chunks=True)

    def _is_interior_solid_cell(self, x, z):
        """Returns True if building cell (x, z) is completely surrounded on all 4 cardinal sides by solid building blocks."""
        for dx, dz in ((-1, 0), (1, 0), (0, -1), (0, 1)):
            nx, nz = x + dx, z + dz
            if not (0 <= nx < MAP_W and 0 <= nz < MAP_H):
                return False
            if MAP[nz][nx] in (0, 6, 7):
                return False
        return True

    def _rebuild_spatial_chunks(self):
        """
        Anti-Lag Spatial Chunk Compiler:
        Divides the 48x40 map into 8x8 sector display lists (6x5 = 30 spatial chunks) and culls unseen interior
        building cells so only visible chunks within the active draw distance are rendered each frame!
        """
        for dlist in self.chunk_dlists.values():
            try:
                gl.glDeleteLists(dlist, 1)
            except Exception:
                pass
        self.chunk_dlists.clear()
        if self.landmarks_dlist:
            try:
                gl.glDeleteLists(self.landmarks_dlist, 1)
            except Exception:
                pass

        self.water_cells = []
        for z in range(MAP_H):
            for x in range(MAP_W):
                if MAP[z][x] == 7:
                    self.water_cells.append((x, z))

        CHUNK_SIZE = 8
        chunks_x = (MAP_W + CHUNK_SIZE - 1) // CHUNK_SIZE
        chunks_z = (MAP_H + CHUNK_SIZE - 1) // CHUNK_SIZE

        for cz in range(chunks_z):
            for cx in range(chunks_x):
                x0 = cx * CHUNK_SIZE
                z0 = cz * CHUNK_SIZE
                x1 = min(MAP_W, x0 + CHUNK_SIZE)
                z1 = min(MAP_H, z0 + CHUNK_SIZE)
                dl = gl.glGenLists(1)
                gl.glNewList(dl, GL_COMPILE)
                self._build_chunk_geometry(x0, z0, x1, z1)
                gl.glEndList()
                self.chunk_dlists[(cx, cz)] = dl

        self.landmarks_dlist = gl.glGenLists(1)
        gl.glNewList(self.landmarks_dlist, GL_COMPILE)
        self._build_landmarks_geometry()
        gl.glEndList()

    def _build_chunk_geometry(self, x0, z0, x1, z1):
        """Builds static 3D geometry for a single 8x8 spatial chunk, honoring Graphics Preset and Current Map."""
        is_potato = (self.graphics_preset == "Potato PC Graphics")
        is_ultra = (self.graphics_preset == "Alter Heavy Graphics")
        is_bigcity = (self.current_map in ("gm_bigcity", "BigCity5", "driving Test map"))

        tex_street = self.world_textures['asphalt_road'] if is_bigcity else self.world_textures['cobble_street']
        tex_asphalt = self.world_textures.get('hl2_road_asphalt', self.world_textures['asphalt_road'])
        tex_crosswalk = self.world_textures.get('hl2_road_crosswalk', tex_asphalt)
        tex_tile = self.world_textures['trainstation_tile']
        tex_sidewalk = self.world_textures['concrete_sidewalk']
        tex_terracotta = self.world_textures['c17_terracotta']
        tex_terracotta_w = self.world_textures['c17_terracotta_win']
        tex_neoclass = self.world_textures['c17_neoclassical']
        tex_fac03 = self.world_textures['c17_facade_03']
        tex_fac12 = self.world_textures['c17_facade_12']
        tex_green_brick = self.world_textures['corridor_green_brick']
        tex_poster_wall = self.world_textures['corridor_poster_wall']
        tex_slate = self.world_textures['c17_SlateRoof']
        tex_awning = self.world_textures['c17_awning']
        tex_combine = self.world_textures['combine_bunker']
        tex_sandbag = self.world_textures['sandbag']
        tex_skyscraper = self.world_textures['bigcity_skyscraper']
        tex_brick31 = self.world_textures.get('hl2_brick_wall031', tex_terracotta)
        tex_brick45 = self.world_textures.get('hl2_brick_wall045', tex_terracotta_w)
        tex_plaster13 = self.world_textures.get('hl2_plaster_wall013', tex_neoclass)
        tex_metal_w = self.world_textures.get('hl2_metal_wall', tex_combine)

        # 1. Ground Tiles (Plaza Terrazzo, Source Asphalt Highway & Crosswalks, Cobble Streets, and Sunken Water Canal Beds)
        gl.glEnable(GL_TEXTURE_2D)
        if not is_bigcity:
            # 1a. City-17 Station Plaza Terrazzo Tiles (NW Sector: x=2..21, z=2..14)
            gl.glBindTexture(GL_TEXTURE_2D, tex_tile)
            gl.glBegin(GL_QUADS)
            for z in range(z0, z1):
                for x in range(x0, x1):
                    cell = MAP[z][x]
                    if (cell == 0 or cell == 6) and (2 <= x <= 21 and 2 <= z <= 14):
                        gl.glColor3f(0.96, 0.94, 0.90)
                        gl.glNormal3f(0, 1, 0)
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, 0.0, z)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.0, z + 1.0)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.0, z + 1.0)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, 0.0, z)
            gl.glEnd()

            # 1b. Connected BigCity5 / Source Engine 4-Lane Asphalt Highway & Boulevard (South Sector z=24..33 & Canal Bridges)
            gl.glBindTexture(GL_TEXTURE_2D, tex_asphalt)
            gl.glBegin(GL_QUADS)
            for z in range(z0, z1):
                for x in range(x0, x1):
                    cell = MAP[z][x]
                    is_hwy = (24 <= z <= 33) or (11 <= x <= 15 and 15 <= z <= 23) or (22 <= x <= 26 and 15 <= z <= 23)
                    if (cell == 0 or cell == 6) and is_hwy and x not in (14, 24, 34):
                        shade = 0.94 if (x + z) % 2 == 0 else 0.90
                        gl.glColor3f(shade, shade, shade * 1.02)
                        gl.glNormal3f(0, 1, 0)
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, 0.0, z)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.0, z + 1.0)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.0, z + 1.0)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, 0.0, z)
            gl.glEnd()

            # 1c. Genuine Source Engine Asphalt Crosswalk Stripes (`concretefloor033y`)
            gl.glBindTexture(GL_TEXTURE_2D, tex_crosswalk)
            gl.glBegin(GL_QUADS)
            for z in range(z0, z1):
                for x in range(x0, x1):
                    cell = MAP[z][x]
                    is_hwy = (24 <= z <= 33) or (11 <= x <= 15 and 15 <= z <= 23) or (22 <= x <= 26 and 15 <= z <= 23)
                    if (cell == 0 or cell == 6) and is_hwy and x in (14, 24, 34):
                        gl.glColor3f(0.96, 0.96, 0.96)
                        gl.glNormal3f(0, 1, 0)
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, 0.0, z)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.0, z + 1.0)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.0, z + 1.0)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, 0.0, z)
            gl.glEnd()

        gl.glBindTexture(GL_TEXTURE_2D, tex_street)
        gl.glBegin(GL_QUADS)
        for z in range(z0, z1):
            for x in range(x0, x1):
                cell = MAP[z][x]
                is_plaza = (not is_bigcity) and (2 <= x <= 21 and 2 <= z <= 14)
                is_hwy = (not is_bigcity) and ((24 <= z <= 33) or (11 <= x <= 15 and 15 <= z <= 23) or (22 <= x <= 26 and 15 <= z <= 23))
                if (cell == 0 or cell == 6) and not is_plaza and not is_hwy:
                    shade = 0.94 if (x + z) % 2 == 0 else 0.88
                    gl.glColor3f(shade, shade * 0.99, shade * 0.96)
                    gl.glNormal3f(0, 1, 0)
                    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, 0.0, z)
                    gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.0, z + 1.0)
                    gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.0, z + 1.0)
                    gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, 0.0, z)
        gl.glEnd()

        # Sunken Concrete Water Canal Basin Floor & Retaining Walls (cell == 7)
        gl.glBindTexture(GL_TEXTURE_2D, tex_sidewalk)
        gl.glBegin(GL_QUADS)
        for z in range(z0, z1):
            for x in range(x0, x1):
                if MAP[z][x] == 7:
                    # Canal seabed at y = -0.52
                    gl.glColor3f(0.42, 0.52, 0.58)
                    gl.glNormal3f(0, 1, 0)
                    gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, -0.52, z)
                    gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, -0.52, z + 1.0)
                    gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, -0.52, z + 1.0)
                    gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, -0.52, z)
                    # Concrete canal embankment walls where bordering dry ground
                    gl.glColor3f(0.62, 0.65, 0.68)
                    if z > 0 and MAP[z - 1][x] != 7:
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, -0.52, z)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, -0.52, z)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.02, z)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.02, z)
                    if z + 1 < MAP_H and MAP[z + 1][x] != 7:
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, -0.52, z + 1.0)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, -0.52, z + 1.0)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.02, z + 1.0)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.02, z + 1.0)
                    if x > 0 and MAP[z][x - 1] != 7:
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x, -0.52, z)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x, -0.52, z + 1.0)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x, 0.02, z + 1.0)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x, 0.02, z)
                    if x + 1 < MAP_W and MAP[z][x + 1] != 7:
                        gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(x + 1.0, -0.52, z)
                        gl.glTexCoord2f(1.0, 0.0); gl.glVertex3f(x + 1.0, -0.52, z + 1.0)
                        gl.glTexCoord2f(1.0, 1.0); gl.glVertex3f(x + 1.0, 0.02, z + 1.0)
                        gl.glTexCoord2f(0.0, 1.0); gl.glVertex3f(x + 1.0, 0.02, z)
        gl.glEnd()
        gl.glDisable(GL_TEXTURE_2D)

        # Driving Test Map and Big City 5 use the full highway template & dedicated off-road buildings (no procedural grid buildings in the road)
        if self.current_map in ("driving Test map", "BigCity5"):
            return

        # 2. Buildings & Street Props in this Chunk (with Interior Hidden-Cell Culling!)
        for z in range(z0, z1):
            for x in range(x0, x1):
                wt = MAP[z][x]
                if wt == 0:
                    if not is_potato and (x % 6 == 3 and z % 6 == 3) and (2 < x < MAP_W - 2 and 2 < z < MAP_H - 2):
                        gl.glPushMatrix()
                        gl.glTranslatef(x + 0.15, 0.0, z + 0.15)
                        gl.glPushMatrix()
                        gl.glTranslatef(0.0, 1.45, 0.0)
                        draw_box(0.07, 2.9, 0.07, 0.18, 0.20, 0.22)
                        gl.glPopMatrix()
                        gl.glPushMatrix()
                        gl.glTranslatef(0.18, 2.85, 0.0)
                        draw_box(0.42, 0.05, 0.08, 0.22, 0.24, 0.26)
                        gl.glTranslatef(0.14, -0.05, 0.0)
                        draw_box(0.18, 0.06, 0.14, 1.0, 0.92, 0.72)
                        gl.glPopMatrix()
                        gl.glPopMatrix()
                    elif not is_potato and not is_bigcity and x >= 28 and (x * 13 + z * 17) % 37 == 0 and not (10 <= z <= 14):
                        if (x + z) % 2 == 0:
                            draw_3d_sandbag_bunker(x + 0.5, z + 0.5, float((x * 45) % 360), tex_sandbag)
                        else:
                            draw_3d_czech_hedgehog(x + 0.5, z + 0.5, float((z * 35) % 360))
                    continue

                if wt in (6, 7):
                    continue

                # Anti-Lag Interior Culling: Skip solid building cells completely surrounded by other solid building cells!
                if self._is_interior_solid_cell(x, z):
                    continue

                if is_bigcity:
                    # Garry's Mod gm_bigcity High-Rise Skyscrapers, Twin Towers & Industrial Brick Warehouses
                    if wt == 2 and 20 <= z <= 24 and (12 <= x <= 16 or 21 <= x <= 25):
                        # Iconic gm_bigcity Twin Towers!
                        b_tex = tex_skyscraper
                        tint = (0.86, 0.93, 1.0)
                        bh = 16.5 if not is_potato else 12.0
                    elif wt == 2:
                        b_tex = tex_skyscraper
                        tint = (0.90, 0.95, 1.0)
                        bh = 13.5 if not is_potato else 10.0
                    elif wt == 3:
                        b_tex = tex_skyscraper if (x + z) % 2 == 0 else tex_neoclass
                        tint = (0.82, 0.88, 0.95)
                        bh = 11.5 if not is_potato else 8.5
                    elif wt == 5:
                        b_tex = tex_skyscraper
                        tint = (0.78, 0.84, 0.90)
                        bh = 14.0 if not is_potato else 10.0
                    elif wt == 4:
                        # Industrial red-brick warehouse blocks
                        b_tex = tex_terracotta_w if (x + z) % 2 == 0 else tex_terracotta
                        tint = (0.95, 0.88, 0.84)
                        bh = 5.4
                    else:  # Perimeter city skyline wall
                        b_tex = tex_fac12
                        tint = (0.85, 0.86, 0.88)
                        bh = 7.0
                else:
                    # Fused Multi-Map MainCity2 Architecture (City-17 + gm_bigcity Twin Towers + BigCity5 Highway District)
                    if z == 1 and 1 <= x <= 21:
                        b_tex = tex_neoclass
                        tint = (0.96, 0.95, 0.92)
                        bh = 5.2
                    elif wt == 2 and 2 <= z <= 6 and (26 <= x <= 30 or 36 <= x <= 40):
                        # Fused gm_bigcity High-Rise Twin Towers in Northeast Sector!
                        b_tex = tex_skyscraper
                        tint = (0.86, 0.93, 1.0)
                        bh = 16.5 if not is_potato else 12.0
                    elif wt == 2 and z >= 33:
                        # South Highway Glass Skyscraper Tower
                        b_tex = tex_skyscraper
                        tint = (0.90, 0.95, 1.0)
                        bh = 13.0 if not is_potato else 9.5
                    elif wt == 2:
                        b_tex = tex_combine if (x + z) % 2 == 0 else tex_metal_w
                        tint = (0.92, 0.96, 1.0)
                        bh = 5.8
                    elif wt == 3:
                        b_tex = tex_poster_wall if (x + z) % 2 == 0 else tex_green_brick
                        tint = (0.92, 0.96, 0.92)
                        bh = 4.4
                    elif wt == 4:
                        if x >= 25:
                            b_tex = tex_brick31 if (x + z) % 2 == 0 else tex_plaster13
                        else:
                            b_tex = tex_neoclass if (x % 3 != 0) else tex_fac03
                        tint = (0.98, 0.97, 0.95)
                        bh = 4.6
                    elif wt == 5:
                        if z >= 20:
                            b_tex = tex_brick45 if ((x + z) % 2 == 0) else tex_brick31
                        else:
                            b_tex = tex_terracotta_w if ((x + z) % 2 == 0) else tex_terracotta
                        tint = (1.0, 0.96, 0.94)
                        bh = 4.4
                    else:
                        b_tex = tex_fac12
                        tint = (0.95, 0.92, 0.88)
                        bh = 5.2

                v_repeats = max(1.0, round(bh / 1.8))

                gl.glPushMatrix()
                gl.glTranslatef(x + 0.5, bh * 0.5, z + 0.5)

                # Main UV-mapped building facade
                draw_textured_box(1.0, bh, 1.0, b_tex, u_rep=1.0, v_rep=v_repeats, r=tint[0], g=tint[1], b=tint[2])

                # Potato PC Graphics skips extra sidewalk aprons, multi-story cornices, and mansard roofs for maximum FPS!
                if not is_potato:
                    # Raised Concrete Sidewalk Apron around building base
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, -bh * 0.5 + 0.06, 0.0)
                    draw_textured_box(1.36, 0.12, 1.36, tex_sidewalk, u_rep=1.0, v_rep=1.0, r=0.88, g=0.87, b=0.84)
                    gl.glPopMatrix()

                    # Rooftop Parapet
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, bh * 0.5 + 0.06, 0.0)
                    draw_box(1.08, 0.12, 1.08, 0.48, 0.46, 0.43)
                    if is_ultra and not is_bigcity and wt != 2:
                        gl.glPushMatrix()
                        gl.glTranslatef(0.0, 0.22, 0.0)
                        draw_textured_box(0.94, 0.34, 0.94, tex_slate, u_rep=1.0, v_rep=1.0, r=0.55, g=0.58, b=0.64)
                        gl.glPopMatrix()
                    gl.glPopMatrix()

                if is_ultra and not is_bigcity:
                    # Multi-story Neoclassical Cornices (Alter Heavy Graphics exclusive detail)
                    floors = int(bh / 1.45)
                    for fl_i in range(1, floors + 1):
                        ly = -bh * 0.5 + fl_i * 1.40
                        if ly < bh * 0.5 - 0.2:
                            gl.glPushMatrix()
                            gl.glTranslatef(0.0, ly, 0.0)
                            draw_box(1.06, 0.08, 1.06, 0.62, 0.59, 0.54)
                            gl.glPopMatrix()

                gl.glPopMatrix()

                if is_ultra and not is_bigcity and b_tex in (tex_terracotta, tex_terracotta_w, tex_fac03) and z + 1 < MAP_H and MAP[z + 1][x] == 0 and x >= 23:
                    draw_3d_shop_awning(x + 0.5, z + 1.02, 0.0, tex_awning, sign_type=(x % 3))

    def _build_landmarks_geometry(self):
        """Builds map-specific landmarks (City-17 Station Plaza monument & Breencast + Fused gm_bigcity Twin Tower spires)."""
        is_potato = (self.graphics_preset == "Potato PC Graphics")
        is_ultra = (self.graphics_preset == "Alter Heavy Graphics")
        tex_sidewalk = self.world_textures['concrete_sidewalk']
        tex_combine = self.world_textures['combine_bunker']
        tex_fence = self.world_textures['chainlink_fence']
        tex_breen = self.world_textures['breencast_screen']
        tex_yellow = self.world_textures['c17_yellow_turret']
        tex_slate = self.world_textures['c17_SlateRoof']

        if self.current_map in ("gm_bigcity", "BigCity5", "driving Test map"):
            if self.current_map == "gm_bigcity":
                # gm_bigcity Twin Tower Rooftop Spires & Canal Dock Walkways
                for tx_c in (14.5, 23.5):
                    gl.glPushMatrix()
                    gl.glTranslatef(tx_c, 16.5 if not is_potato else 12.0, 22.5)
                    draw_box(1.8, 0.4, 1.8, 0.35, 0.38, 0.42)
                    gl.glTranslatef(0.0, 2.2, 0.0)
                    draw_box(0.12, 4.2, 0.12, 0.75, 0.78, 0.82)
                    # Red aviation warning beacon at top of spire
                    gl.glTranslatef(0.0, 2.2, 0.0)
                    draw_box(0.28, 0.28, 0.28, 1.0, 0.15, 0.10)
                    gl.glPopMatrix()
                # Giant Breencast billboard overlooking gm_bigcity Central Canal
                draw_3d_breencast_screen(23.0, 5.2, 10.5, 0.0, tex_breen)
            return

        # Fused MainCity2 Landmarks (City-17 + gm_bigcity Twin Towers):
        # 1. Central Station Plaza Raised Monument & Fountain (x=11.5, z=12.0)
        gl.glPushMatrix()
        gl.glTranslatef(11.5, 0.0, 12.0)
        draw_textured_box(4.2, 0.28, 4.2, tex_sidewalk, u_rep=2.0, v_rep=1.0, r=0.85, g=0.84, b=0.82)
        gl.glTranslatef(0.0, 0.26, 0.0)
        draw_box(3.2, 0.24, 3.2, 0.48, 0.46, 0.44)
        gl.glTranslatef(0.0, 1.5, 0.0)
        draw_textured_box(0.75, 2.8, 0.75, tex_combine, u_rep=1.0, v_rep=2.0, r=0.75, g=0.85, b=0.92)
        gl.glTranslatef(0.0, 1.5, 0.0)
        draw_box(0.92, 0.16, 0.92, 0.35, 0.38, 0.42)
        draw_box(0.40, 0.65, 0.40, 0.22, 0.24, 0.26)
        gl.glPopMatrix()

        # 1b. Fused gm_bigcity Twin Tower Rooftop Spires & Aviation Warning Beacons in Northeast Sector
        for tx_c in (28.5, 38.5):
            gl.glPushMatrix()
            gl.glTranslatef(tx_c, 16.5 if not is_potato else 12.0, 4.5)
            draw_box(1.8, 0.4, 1.8, 0.35, 0.38, 0.42)
            gl.glTranslatef(0.0, 2.2, 0.0)
            draw_box(0.12, 4.2, 0.12, 0.75, 0.78, 0.82)
            gl.glTranslatef(0.0, 2.2, 0.0)
            draw_box(0.28, 0.28, 0.28, 1.0, 0.15, 0.10)
            gl.glPopMatrix()

        # 2. Giant Cyan Breencast Screen on North Station Wall + East Canal Billboard
        draw_3d_breencast_screen(12.5, 3.4, 1.85, 0.0, tex_breen)
        draw_3d_breencast_screen(31.0, 4.8, 7.2, 0.0, tex_breen)

        # 3. 3D Red 'TERMINAL' Rooftop Sign above Station Entrance
        if not is_potato:
            gl.glPushMatrix()
            gl.glTranslatef(12.5, 5.35, 1.35)
            draw_box(2.8, 0.06, 0.06, 0.20, 0.20, 0.22)
            for lx_i in range(8):
                gl.glPushMatrix()
                gl.glTranslatef(-1.1 + lx_i * 0.32, 0.24, 0.0)
                draw_box(0.20, 0.42, 0.04, 0.72, 0.14, 0.12)
                gl.glPopMatrix()
            gl.glPopMatrix()

        # 4. Combine Security Checkpoint at Plaza East Gate
        draw_3d_chainlink_checkpoint(22.0, 10.5, 90.0, tex_fence, has_gate=False)
        draw_3d_chainlink_checkpoint(22.0, 12.0, 90.0, tex_fence, has_gate=True)
        draw_3d_chainlink_checkpoint(22.0, 13.5, 90.0, tex_fence, has_gate=False)

        # 5. Yellow Corner Turret with Conical Slate Spire
        if not is_potato:
            draw_3d_conical_turret(24.5, 4.0, 16.5, tex_yellow, tex_slate)

        # 6. Overhead Tram Catenary Wires (Alter Heavy Graphics)
        if is_ultra:
            gl.glDisable(GL_TEXTURE_2D)
            gl.glLineWidth(1.8)
            gl.glColor4f(0.10, 0.11, 0.12, 0.88)
            wire_spans = [
                ((24.5, 4.2, 9.5), (45.5, 4.2, 9.5)),
                ((24.5, 4.2, 14.5), (45.5, 4.2, 14.5)),
                ((24.5, 4.2, 12.0), (45.5, 4.2, 12.0)),
                ((27.5, 4.2, 9.5), (27.5, 4.2, 14.5)),
                ((35.5, 4.2, 9.5), (35.5, 4.2, 14.5)),
                ((43.5, 4.2, 9.5), (43.5, 4.2, 14.5)),
            ]
            gl.glBegin(GL_LINES)
            for (x1, y1, z1), (x2, y2, z2) in wire_spans:
                for seg in range(4):
                    t0, t1 = seg / 4.0, (seg + 1) / 4.0
                    sag0 = math.sin(t0 * math.pi) * 0.25
                    sag1 = math.sin(t1 * math.pi) * 0.25
                    gl.glVertex3f(x1 + (x2 - x1) * t0, y1 + (y2 - y1) * t0 - sag0, z1 + (z2 - z1) * t0)
                    gl.glVertex3f(x1 + (x2 - x1) * t1, y1 + (y2 - y1) * t1 - sag1, z1 + (z2 - z1) * t1)
            gl.glEnd()

    def _render_source_water(self):
        """Renders animated translucent Source Engine water surfaces (cell == 7) with scrolling UV wave refraction."""
        if not self.water_cells:
            return
        max_d = self.get_chunk_draw_distance()
        max_d_sq = (max_d + 6.0) ** 2
        tex_water = self.world_textures.get('source_water')
        is_ultra = (self.graphics_preset == "Alter Heavy Graphics")

        gl.glEnable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(GL_TEXTURE_2D)
        if tex_water:
            gl.glBindTexture(GL_TEXTURE_2D, tex_water)

        u_scroll = (self.sim_time * 0.14) % 1.0
        v_scroll = (self.sim_time * 0.09) % 1.0

        gl.glBegin(GL_QUADS)
        for wx, wz in self.water_cells:
            if (wx - self.player_x) ** 2 + (wz - self.player_y) ** 2 > max_d_sq:
                continue
            w00 = -0.08 + math.sin(self.sim_time * 3.0 + wx * 0.9 + wz * 0.7) * 0.035
            w10 = -0.08 + math.sin(self.sim_time * 3.0 + (wx + 1) * 0.9 + wz * 0.7) * 0.035
            w11 = -0.08 + math.sin(self.sim_time * 3.0 + (wx + 1) * 0.9 + (wz + 1) * 0.7) * 0.035
            w01 = -0.08 + math.sin(self.sim_time * 3.0 + wx * 0.9 + (wz + 1) * 0.7) * 0.035

            spec = 0.88 + 0.12 * math.sin(self.sim_time * 4.5 + wx + wz) if is_ultra else 0.90
            gl.glColor4f(0.28 * spec, 0.72 * spec, 0.88 * spec, 0.76)
            gl.glNormal3f(0.0, 1.0, 0.0)
            gl.glTexCoord2f(u_scroll, v_scroll);             gl.glVertex3f(wx, w00, wz)
            gl.glTexCoord2f(u_scroll, v_scroll + 1.0);       gl.glVertex3f(wx, w01, wz + 1.0)
            gl.glTexCoord2f(u_scroll + 1.0, v_scroll + 1.0); gl.glVertex3f(wx + 1.0, w11, wz + 1.0)
            gl.glTexCoord2f(u_scroll + 1.0, v_scroll);       gl.glVertex3f(wx + 1.0, w10, wz)
        gl.glEnd()
        gl.glDisable(GL_TEXTURE_2D)
        gl.glDisable(GL_BLEND)

    def _render_bullet_decals(self, max_draw_dist):
        """Renders persistent 3D bullet impact decals on wall surfaces with concentric scorch and concrete powder rings."""
        if not getattr(self, 'bullet_decals', None):
            return

        cull_sq = (max_draw_dist + 2.0) ** 2
        total = len(self.bullet_decals)
        limit = self.max_bullet_decals

        gl.glDisable(GL_TEXTURE_2D)
        gl.glEnable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glDepthMask(GL_FALSE)

        gl.glBegin(GL_QUADS)
        for i, d in enumerate(self.bullet_decals):
            dx = d['x'] - self.player_x
            dz = d['z'] - self.player_y
            if dx * dx + dz * dz > cull_sq:
                continue

            # Smooth fade-out for the oldest decals as they approach or exceed limit
            alpha = 1.0
            if total >= int(limit * 0.85):
                fade_window = max(25, int(limit * 0.15))
                if i < fade_window:
                    alpha = max(0.08, float(i) / float(fade_window))

            nx, ny, nz = d['nx'], d['ny'], d['nz']
            px = d['x'] + nx * 0.015
            py = d['y'] + ny * 0.015
            pz = d['z'] + nz * 0.015
            sz = d['size']

            if abs(nx) > 0.5:
                # Wall is aligned with Y-Z plane (X face)
                gl.glColor4f(0.14, 0.13, 0.12, alpha * 0.90)
                gl.glVertex3f(px, py - sz, pz - sz)
                gl.glVertex3f(px, py + sz, pz - sz)
                gl.glVertex3f(px, py + sz, pz + sz)
                gl.glVertex3f(px, py - sz, pz + sz)

                sz_in = sz * 0.52
                gl.glColor4f(0.74, 0.72, 0.68, alpha * 0.96)
                gl.glVertex3f(px + nx * 0.002, py - sz_in, pz - sz_in)
                gl.glVertex3f(px + nx * 0.002, py + sz_in, pz - sz_in)
                gl.glVertex3f(px + nx * 0.002, py + sz_in, pz + sz_in)
                gl.glVertex3f(px + nx * 0.002, py - sz_in, pz + sz_in)

                sz_p = sz * 0.22
                gl.glColor4f(0.02, 0.02, 0.02, alpha)
                gl.glVertex3f(px + nx * 0.004, py - sz_p, pz - sz_p)
                gl.glVertex3f(px + nx * 0.004, py + sz_p, pz - sz_p)
                gl.glVertex3f(px + nx * 0.004, py + sz_p, pz + sz_p)
                gl.glVertex3f(px + nx * 0.004, py - sz_p, pz + sz_p)

            else:
                # Wall is aligned with X-Y plane (Z face)
                gl.glColor4f(0.14, 0.13, 0.12, alpha * 0.90)
                gl.glVertex3f(px - sz, py - sz, pz)
                gl.glVertex3f(px - sz, py + sz, pz)
                gl.glVertex3f(px + sz, py + sz, pz)
                gl.glVertex3f(px + sz, py - sz, pz)

                sz_in = sz * 0.52
                gl.glColor4f(0.74, 0.72, 0.68, alpha * 0.96)
                gl.glVertex3f(px - sz_in, py - sz_in, pz + nz * 0.002)
                gl.glVertex3f(px - sz_in, py + sz_in, pz + nz * 0.002)
                gl.glVertex3f(px + sz_in, py + sz_in, pz + nz * 0.002)
                gl.glVertex3f(px + sz_in, py - sz_in, pz + nz * 0.002)

                sz_p = sz * 0.22
                gl.glColor4f(0.02, 0.02, 0.02, alpha)
                gl.glVertex3f(px - sz_p, py - sz_p, pz + nz * 0.004)
                gl.glVertex3f(px - sz_p, py + sz_p, pz + nz * 0.004)
                gl.glVertex3f(px + sz_p, py + sz_p, pz + nz * 0.004)
                gl.glVertex3f(px + sz_p, py - sz_p, pz + nz * 0.004)

        gl.glEnd()
        gl.glDepthMask(GL_TRUE)
        gl.glDisable(GL_BLEND)
        gl.glEnable(GL_TEXTURE_2D)

    def switch_map(self, new_map_name):
        """Switches active map between MainCity2, gm_bigcity, BigCity5, and driving Test map, rebuilding chunks & world."""
        if new_map_name in ("driving Test map", "BigCity5", "gm_bigcity", "MainCity2"):
            self.current_map = new_map_name
        else:
            self.current_map = "MainCity2"
        set_active_map_data(self.current_map)
        self.init_game()
        self.is_loading = False
        if getattr(self, 'game_state', 0) == getattr(self, 'STATE_PLAYING', 2):
            self.populate_world()
        self.add_log('sys', f'[SOURCE ENGINE] Loaded map: {self.current_map}')

    def punt_physics_prop(self):
        """Source Engine Gravity Gun / vphysics punt ([G] key): launches nearby crates, barrels, or chargers forward."""
        cos_a = math.cos(self.player_angle)
        sin_a = math.sin(self.player_angle)
        punted = False
        for e in self.entities:
            if not e.alive:
                continue
            dx = e.x - self.player_x
            dy = e.y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if 0.1 < dist < 3.6:
                dot = (dx * cos_a + dy * sin_a) / dist
                if dot > 0.35:
                    impulse = 12.5 if isinstance(e, PropEntity) else 7.5
                    e.vx += cos_a * impulse
                    e.vy += sin_a * impulse
                    e.vz = getattr(e, 'vz', 0.0) + 2.0
                    punted = True
                    self.add_log('info', f'[VPHYSICS] Punted {e.type} #{e.id}!')
        if punted:
            self.snd_combine_hit.play()
            self.screen_shake = max(self.screen_shake, 0.15)

    # ═══════════════════════════════════════════════
    #  HALF-LIFE 2 MAP EDITOR & PERSISTENT SAVE/LOAD (custom_maps.json)
    # ═══════════════════════════════════════════════
    def _load_placed_objects_for_map(self):
        custom_all = load_custom_maps()
        saved_entry = custom_all.get(self.current_map)
        if isinstance(saved_entry, dict) and isinstance(saved_entry.get("placed_objects"), list):
            self.placed_objects = [dict(o) for o in saved_entry["placed_objects"] if isinstance(o, dict)]
        else:
            self.placed_objects = [dict(o) for o in DEFAULT_PLACED_OBJECTS.get(self.current_map, [])]

    def save_custom_map_state(self):
        """Persists the current 2D map grid (buildings, doors, water) and all 3D placed HL2 resources to custom_maps.json."""
        custom_all = load_custom_maps()
        custom_all[self.current_map] = {
            "grid": [row[:] for row in MAP],
            "placed_objects": [dict(o) for o in self.placed_objects],
        }
        ok = save_custom_maps(custom_all)
        if ok:
            self.editor_status_msg = f"SAVED '{self.current_map}' TO custom_maps.json ({len(self.placed_objects)} HL2 objects)"
            self.editor_status_timer = 4.0
            self.add_log('sys', f'[MAP EDITOR] Saved map "{self.current_map}" to custom_maps.json!')
            self.snd_pickup.play()

    def load_custom_map_state(self):
        """Loads saved custom map grid and placed 3D HL2 resources from custom_maps.json."""
        set_active_map_data(self.current_map, ignore_custom=False)
        self._load_placed_objects_for_map()
        self.doors = {pos: {'open': 0.0, 'opening': False, 'timer': 0.0} for pos in DOOR_POSITIONS}
        self._rebuild_spatial_chunks()
        self.editor_status_msg = f"LOADED '{self.current_map}' FROM custom_maps.json ({len(self.placed_objects)} HL2 objects)"
        self.editor_status_timer = 4.0
        self.add_log('sys', f'[MAP EDITOR] Loaded custom map "{self.current_map}" from custom_maps.json!')
        self.snd_pickup.play()

    def reset_map_to_default(self):
        """Resets the current map to its factory Half-Life 2 / Source Engine layout and updates custom_maps.json."""
        custom_all = load_custom_maps()
        if self.current_map in custom_all:
            del custom_all[self.current_map]
            save_custom_maps(custom_all)
        set_active_map_data(self.current_map, ignore_custom=True)
        self.placed_objects = [dict(o) for o in DEFAULT_PLACED_OBJECTS.get(self.current_map, [])]
        self.doors = {pos: {'open': 0.0, 'opening': False, 'timer': 0.0} for pos in DOOR_POSITIONS}
        self._rebuild_spatial_chunks()
        self.editor_status_msg = f"RESET '{self.current_map}' TO DEFAULT LAYOUT"
        self.editor_status_timer = 4.0
        self.add_log('warn', f'[MAP EDITOR] Reset "{self.current_map}" to factory default layout.')

    def toggle_map_editor(self):
        self.map_editor_active = not self.map_editor_active
        if self.map_editor_active:
            self.paused = False
            self.admin_open = False
            pygame.mouse.set_visible(self.automap)
            pygame.event.set_grab(not self.automap)
            self._update_editor_cursor()
            self.editor_status_msg = "MAP EDITOR ACTIVE — [LMB] Place  [RMB] Delete  [Q/E/Wheel] Item  [R] Rotate  [F5] Save"
            self.editor_status_timer = 5.0
            self.add_log('sys', '[MAP EDITOR] Enabled! Place HL2 buildings, fences, barriers, entry lights, doors & water.')
        else:
            self.save_custom_map_state()
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
            self.add_log('sys', '[MAP EDITOR] Closed & auto-saved map to custom_maps.json.')

    def _update_editor_cursor(self):
        """
        Cast an accurate 3D ray from the camera eye along the look vector (where the center
        yellow indicator crosshair points). Automatically selects/targets the exact placed prop
        the player is looking at for precision deletion, and finds the exact 3D surface hit point
        (on ground, stairs, elevated second-story platforms, or walls) for object placement.
        """
        eye_x, eye_y, eye_z, _, _, _ = self._compute_camera()
        cos_p = math.cos(self.player_pitch)
        sin_p = math.sin(self.player_pitch)
        dir_x = math.cos(self.player_angle) * cos_p
        dir_y = -sin_p
        dir_z = math.sin(self.player_angle) * cos_p

        self.editor_targeted_prop_idx = None
        closest_t = 30.0

        # 1. Test 3D ray against all placed objects
        for i, obj in enumerate(getattr(self, 'placed_objects', [])):
            otype = obj.get("type", "")
            ox = float(obj.get("x", 0.0))
            oy = float(obj.get("y", 0.0))
            oz = float(obj.get("z", 0.0))
            yaw = float(obj.get("yaw", 0.0))

            col_info = PROP_COLLISION_DATA.get(otype, {"shape": "box", "w": 1.2, "d": 1.2, "h": 1.5})
            w = col_info.get("w", 1.2)
            d = col_info.get("d", 1.2)
            h = col_info.get("h", 1.5)

            # Center in OpenGL coordinates: (ox, oz + h/2, oy)
            cx, cy, cz = ox, oz + h * 0.5, oy

            # Transform ray to local coordinate space of object
            rel_x = eye_x - cx
            rel_y = eye_y - cy
            rel_z = eye_z - cz

            rad = math.radians(yaw)
            cos_y = math.cos(-rad)
            sin_y = math.sin(-rad)

            lx_o = rel_x * cos_y - rel_z * sin_y
            ly_o = rel_y
            lz_o = rel_x * sin_y + rel_z * cos_y

            lx_d = dir_x * cos_y - dir_z * sin_y
            ly_d = dir_y
            lz_d = dir_x * sin_y + dir_z * cos_y

            # Ray-AABB slab intersection test with generous margin for easy targeting
            tmin = 0.0
            tmax = 30.0
            hit = True
            for po, pd, bmin, bmax in [
                (lx_o, lx_d, -w * 0.5 - 0.20, w * 0.5 + 0.20),
                (ly_o, ly_d, -h * 0.5 - 0.20, h * 0.5 + 0.20),
                (lz_o, lz_d, -d * 0.5 - 0.20, d * 0.5 + 0.20)
            ]:
                if abs(pd) < 1e-6:
                    if po < bmin or po > bmax:
                        hit = False
                        break
                else:
                    t1 = (bmin - po) / pd
                    t2 = (bmax - po) / pd
                    if t1 > t2:
                        t1, t2 = t2, t1
                    tmin = max(tmin, t1)
                    tmax = min(tmax, t2)
                    if tmin > tmax:
                        hit = False
                        break

            if hit and 0.2 < tmin < closest_t:
                closest_t = tmin
                self.editor_targeted_prop_idx = i

        # 2. Find surface placement coordinates (ground, elevated platform, or walls)
        target_x = self.player_x + math.cos(self.player_angle) * 3.5
        target_y = self.player_y + math.sin(self.player_angle) * 3.5
        target_z = 0.0

        # Check elevated floors / walkways first
        elev_hit = False
        for obj in getattr(self, 'placed_objects', []):
            otype = obj.get("type", "")
            if otype in ("second_story_floor", "roof_walkway", "scaffolding"):
                oz = float(obj.get("z", 0.0))
                plat_z = oz + (2.8 if otype != "scaffolding" else 1.4)
                if eye_y > plat_z and dir_y < -0.01:
                    t_plat = (plat_z - eye_y) / dir_y
                    if 0.2 < t_plat < 30.0:
                        px_hit = eye_x + dir_x * t_plat
                        py_hit = eye_z + dir_z * t_plat
                        if abs(px_hit - float(obj.get("x", 0.0))) < 1.7 and abs(py_hit - float(obj.get("y", 0.0))) < 1.7:
                            target_x = px_hit
                            target_y = py_hit
                            target_z = plat_z
                            elev_hit = True
                            break

        if not elev_hit:
            # Check ground plane y = 0
            if dir_y < -0.01:
                t_ground = (0.0 - eye_y) / dir_y
                if 0.2 < t_ground < 35.0:
                    target_x = eye_x + dir_x * t_ground
                    target_y = eye_z + dir_z * t_ground
                    target_z = 0.0
            else:
                target_x = eye_x + dir_x * 3.8
                target_y = eye_z + dir_z * 3.8
                target_z = max(0.0, eye_y + dir_y * 3.8)

        # Step ray to detect wall face
        step = 0.20
        cur_d = 0.4
        while cur_d < min(closest_t, 25.0):
            rx = eye_x + dir_x * cur_d
            ry = eye_y + dir_y * cur_d
            rz = eye_z + dir_z * cur_d
            mx, my = int(rx), int(rz)
            if 0 <= mx < MAP_W and 0 <= my < MAP_H:
                if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and self.is_door_open(my, mx)):
                    target_x = rx - dir_x * 0.12
                    target_y = rz - dir_z * 0.12
                    target_z = max(0.0, ry)
                    break
            cur_d += step

        self.editor_target_x = max(1.0, min(MAP_W - 1.0, target_x))
        self.editor_target_y = max(1.0, min(MAP_H - 1.0, target_y))
        self.editor_target_z = round(max(0.0, target_z), 2)

    def _spawn_saved_entity_object(self, otype, ox, oy):
        if otype in ('crate', 'barrel', 'explosive_barrel', 'charger'):
            self.entities.append(PropEntity(ox, oy, otype))
        elif otype == 'mcpd_stunstick':
            self.entities.append(MCPDUnit(ox, oy, weapon_type='stunstick'))
        elif otype == 'mcpd_pistol':
            self.entities.append(MCPDUnit(ox, oy, weapon_type='pistol'))
        elif otype == 'civilian':
            self.entities.append(Civilian(ox, oy))
        elif otype == 'ecpu':
            self.entities.append(ECPUUnit(ox, oy))
        elif otype == 'military':
            self.entities.append(MilitaryUnit(ox, oy))
        elif otype == 'rpg':
            self.entities.append(RPGGanger(ox, oy))

    def editor_place_at(self, tx=None, ty=None, tz=None):
        """Places the selected Map Editor building/door/water cell or 3D prop/stair/platform and auto-saves."""
        if tx is None or ty is None:
            self._update_editor_cursor()
            tx, ty = self.editor_target_x, self.editor_target_y
            tz = getattr(self, 'editor_target_z', 0.0)
        elif tz is None:
            tz = getattr(self, 'editor_target_z', 0.0)

        cat, val, label = MAP_EDITOR_PALETTE[self.editor_idx % len(MAP_EDITOR_PALETTE)]
        gx = max(1, min(MAP_W - 2, int(tx)))
        gy = max(1, min(MAP_H - 2, int(ty)))

        if cat == "grid":
            MAP[gy][gx] = int(val)
            rebuild_door_positions()
            self.doors = {pos: self.doors.get(pos, {'open': 0.0, 'opening': False, 'timer': 0.0}) for pos in DOOR_POSITIONS}
            self._rebuild_spatial_chunks()
            self.save_custom_map_state()
            self.editor_status_msg = f"PLACED [{label}] AT CELL ({gx}, {gy}) — SAVED"
            self.editor_status_timer = 3.5
            self.snd_metal.play()
        elif cat == "prop_static":
            is_arch = val in ("stairs_metal", "stairs_wood", "metal_ramp", "scaffolding", "second_story_floor", "roof_walkway")
            if is_arch:
                px = math.floor(tx) + 0.5
                py = math.floor(ty) + 0.5
                pyaw = round(float(self.editor_yaw) / 90.0) * 90.0 % 360.0
                pz = round(float(tz) / 2.8) * 2.8 if val in ("second_story_floor", "roof_walkway") else round(float(tz), 2)
            else:
                px = round(float(tx), 2)
                py = round(float(ty), 2)
                pyaw = float(self.editor_yaw)
                pz = round(float(tz), 2)

            obj = {
                "type": val,
                "x": px,
                "y": py,
                "z": pz,
                "yaw": pyaw
            }
            self.placed_objects.append(obj)
            self.save_custom_map_state()
            self.editor_status_msg = f"PLACED [{label}] AT ({px:.1f}, {py:.1f}, z={pz:.1f}) — SAVED"
            self.editor_status_timer = 3.5
            self.snd_metal.play()
        elif cat == "entity":
            obj = {
                "type": val,
                "x": round(float(tx), 2),
                "y": round(float(ty), 2),
                "z": round(float(tz), 2),
                "yaw": float(self.editor_yaw)
            }
            self.placed_objects.append(obj)
            self._spawn_saved_entity_object(val, float(tx), float(ty))
            self.save_custom_map_state()
            self.editor_status_msg = f"SPAWNED & SAVED [{label}] AT ({tx:.1f}, {ty:.1f})"
            self.editor_status_timer = 3.5
            self.snd_pickup.play()

    def editor_delete_at(self, tx=None, ty=None):
        """
        Deletes the exact placed 3D prop/stair/platform/NPC currently targeted by the yellow crosshair
        indicator, or demolishes the targeted building block back to Open Street (0). Auto-saves state immediately.
        """
        self._update_editor_cursor()

        # 1. If an object is targeted by the center raycast pointer, delete THAT exact object!
        target_idx = getattr(self, 'editor_targeted_prop_idx', None)
        if target_idx is not None and 0 <= target_idx < len(self.placed_objects):
            rem = self.placed_objects.pop(target_idx)
            self.editor_targeted_prop_idx = None
            # Also remove matching live entity if it was an entity placement
            for e in self.entities:
                if e.alive and math.hypot(e.x - rem.get("x", 0), e.y - rem.get("y", 0)) < 1.4:
                    e.alive = False
                    break
            self.save_custom_map_state()
            self.editor_status_msg = f"DELETED [{rem.get('type')}] AT ({rem.get('x')}, {rem.get('y')}) — SAVED"
            self.editor_status_timer = 3.5
            self.snd_crowbar.play()
            return

        # 2. If looking at a wall/door building block, demolish back to Open Street (0)
        gx = max(1, min(MAP_W - 2, int(self.editor_target_x)))
        gy = max(1, min(MAP_H - 2, int(self.editor_target_y)))
        if MAP[gy][gx] != 0:
            old_v = MAP[gy][gx]
            MAP[gy][gx] = 0
            rebuild_door_positions()
            self.doors = {pos: self.doors.get(pos, {'open': 0.0, 'opening': False, 'timer': 0.0}) for pos in DOOR_POSITIONS}
            self._rebuild_spatial_chunks()
            self.save_custom_map_state()
            self.editor_status_msg = f"DEMOLISHED CELL ({gx}, {gy}) [was {old_v} -> Street] — SAVED"
            self.editor_status_timer = 3.5
            self.snd_crowbar.play()
            return

        # 3. Fallback: check nearest placed object within 2.0m of raycast hit
        best_i = -1
        best_d = 2.0
        for i, obj in enumerate(self.placed_objects):
            d = math.hypot(obj.get("x", 0) - self.editor_target_x, obj.get("y", 0) - self.editor_target_y)
            if d < best_d:
                best_d = d
                best_i = i

        if best_i >= 0:
            rem = self.placed_objects.pop(best_i)
            self.save_custom_map_state()
            self.editor_status_msg = f"DELETED [{rem.get('type')}] AT ({rem.get('x')}, {rem.get('y')}) — SAVED"
            self.editor_status_timer = 3.5
            self.snd_crowbar.play()

    def init_game(self):
        set_active_map_data(self.current_map)
        if getattr(self, 'game_state', 0) == getattr(self, 'STATE_PLAYING', 2):
            self._load_placed_objects_for_map()
        else:
            # Main Menu background preview map: empty copy of the map layout with zero props or enemies
            self.placed_objects = []
        if self.current_map == "driving Test map":
            self.player_x = 19.5
            self.player_y = 23.5
            self.player_angle = 0.0
        elif self.current_map == "BigCity5":
            self.player_x = 20.5
            self.player_y = 25.0
            self.player_angle = 0.0
        elif self.current_map == "gm_bigcity":
            self.player_x = 18.5
            self.player_y = 18.0
            self.player_angle = -math.pi / 2
        else:
            self.player_x = 12.0
            self.player_y = 15.0
            self.player_angle = -math.pi / 2
        self.in_vehicle = False
        self.active_vehicle = None
        self.vehicles = []
        self.traffic_vehicles = []
        self.vehicle_spawner_open = False
        self.vehicle_button_rects = []
        self.player_z = 0.0
        self.player_vz = 0.0
        self.player_pitch = 0.0
        self.player_health = 100
        self.player_in_water = False
        self.paused = False
        self.spawn_protection_timer = 5.0
        self.wanted_level = 0
        is_sandbox = getattr(self, 'sandbox_mode', False) or getattr(self, 'cheat_mode', False)
        self.player_armor = 100 if is_sandbox else 0
        self.player_money = 250000
        self.noclip = False
        self.sprint = False
        self.is_sprinting = False
        self.is_moving = False

        # Camera Modes: 2 = 1st Person (Default CoD/HL2 View), 0 = 3rd Person Tactical, 1 = 3rd Person Wide
        self.camera_mode = 2
        self.aim_zoom = False
        self.sprint_blend = 0.0
        self.ads_blend = 0.0
        self.current_fov = 68.0
        self.walk_phase = 0.0
        self.aux_power = 80.0
        self.weapon_hud_timer = 3.5
        self.damage_angle = 0.0

        # Start with iconic Half-Life 2 Crowbar in Tactical Mode; all weapons in Sandbox
        if is_sandbox:
            self.weapons_owned = {0: True, 1: True, 2: True, 3: True, 4: True, 5: True, 6: True}
            self.current_weapon = 1
        else:
            self.weapons_owned = {0: True, 1: False, 2: False, 3: False, 4: False, 5: False, 6: False}
            self.current_weapon = 0

        self.arms_shop_open = False
        self.shop_button_rects = []
        self.bump_cooldown = 0.0
        self.bump_warn_timer = 0.0
        self.bump_officer_id = None
        self.civilian_respawn_queue = []
        self.compliance_chronometer = 0.0
        self.telemetry_active = False
        self.compliance_stillness_timer = 0.0
        self.telemetry_warn_step = 15
        self.telemetry_officer_id = None
        self.ambient_gunfire_timer = random.uniform(5.0, 10.0)
        self.player_vx = 0.0
        self.player_vy = 0.0
        self.arms_shop_catalog = [
            {"wid": 1, "name": "USP Match 9mm Tactical Pistol", "price": 500, "desc": "MCPD sidearm · High accuracy · 18 round clip", "icon": "🔫"},
            {"wid": 2, "name": "SMG1 Submachine Gun (MP7)", "price": 1500, "desc": "Rapid-fire automatic PDW · 45 round clip", "icon": "⚡"},
            {"wid": 3, "name": "SPAS-12 Tactical Shotgun", "price": 2500, "desc": "Close-quarters double-barrel pump · 6 shells", "icon": "💥"},
            {"wid": 4, "name": "Combine Pulse Rifle (AR2)", "price": 4500, "desc": "Dark energy assault rifle · 30 cell core", "icon": "🔷"},
            {"wid": 5, "name": ".357 Magnum Hand Cannon", "price": 3000, "desc": "Heavy stopping power · 6 cylinder rounds", "icon": "🎯"},
            {"wid": 6, "name": "RPG-7 Rocket Launcher", "price": 10000, "desc": "Laser-guided high-explosive rocket", "icon": "🚀"},
            {"wid": "ammo", "name": "Tactical Munitions Crate", "price": 200, "desc": "Full ammunition reserve restock", "icon": "📦"},
            {"wid": "armor", "name": "HEV Shield Recharge", "price": 400, "desc": "Recharge Mark V HEV suit to 100%", "icon": "🛡️"},
        ]
        self.ammo = {
            'bullets': 90,
            'shells': 32,
            'cells': 120,
            'rockets': 6,
        }
        self.ammo_max = {
            'bullets': 200,
            'shells': 50,
            'cells': 300,
            'rockets': 30,
        }
        # Authentic magazine/clip capacities for all 7 Half-Life 2 weapons:
        # 0: Crowbar (0), 1: 9mm Pistol (18), 2: SMG1 (45), 3: SPAS-12 (6), 4: AR2 (30), 5: .357 (6), 6: RPG-7 (1)
        self.weapon_clips = {0: 0, 1: 18, 2: 45, 3: 6, 4: 30, 5: 6, 6: 1}
        self.is_reloading = False
        self.reload_timer = 0.0
        self.reload_duration = 0.0
        self.weapon_cooldown = 0
        self.weapon_switch_timer = 0.0
        self.berserk_timer = 0
        self.invuln_timer = 0

        self.sim_time = 0.0
        self.entities = []
        self.projectiles = []
        self.explosions_list = []
        self.tracers = []  # 3D bullet tracer lines: [x1, y1, z1, x2, y2, z2, color, life]
        self.shell_casings = []  # Ejected 3D brass casings in FP view
        self.smoke_columns = (
            [] if self.current_map == "driving Test map" else
            [[8.5, 11.5], [16.5, 7.5], [13.5, 18.5], [22.5, 14.5], [29.5, 9.5], [36.5, 22.5]]
        )
        self.pickups = []
        self.weapon_pickup_positions = []
        self.weapon_pickups_alive = []
        self.corpses = []
        self.mcpd_respawn_queue = []
        self.console_log = []
        self.is_loading = True
        self.loading_progress = 0
        self.loading_msg = f"Loading {self.current_map} Source Engine BSP & Water Physics..."
        self.is_crashed = False
        self.crash_progress = 0
        self.crash_reason = ""
        self.admin_open = False
        self.screen_shake = 0
        self.weapon_fired = 0
        self.step_timer = 0
        self.msg_timer = 0
        self.wanted_level = 0
        self.wanted_decay_timer = 0.0
        self.crosshair_hit = 0
        self.damage_flash = 0
        self.automap = False

        self.doors = {}
        for dy, dx in DOOR_POSITIONS:
            self.doors[(dy, dx)] = {'open': 0.0, 'opening': False, 'timer': 0.0}

        self.apply_graphics_and_fog_settings(rebuild_chunks=True)

        self.kills = 0
        self.items_collected = 0
        self.secrets_found = 0
        self.level_start_time = 0

        if getattr(self, 'game_state', 0) == getattr(self, 'STATE_PLAYING', 2):
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

        self.admin_items = [
            ("Open Half-Life 2 Map Editor ([F2])", self.toggle_map_editor),
            ("Save Custom Map ([F5])", self.save_custom_map_state),
            ("Spawn Civilian", lambda: self.admin_spawn('civilian')),
            ("Spawn MCPD Officer", lambda: self.admin_spawn('mcpd')),
            ("Spawn ECPU Elite", lambda: self.admin_spawn('ecpu')),
            ("Spawn RPG Ganger", lambda: self.admin_spawn('rpg')),
            ("Spawn Source Buoyancy Barrel", lambda: self.admin_spawn('barrel')),
            ("Spawn Source Physics Crate", lambda: self.admin_spawn('crate')),
            ("Spawn Explosive Barrel", lambda: self.admin_spawn('explosive_barrel')),
            ("Spawn 3D Pink Charger", lambda: self.admin_spawn('charger')),
            ("Toggle Noclip", self.toggle_noclip),
            ("Give All Weapons", self.give_all_weapons),
            ("Fire Combine Ball Burst", self.fire_burst),
            ("Load Map: driving Test map", lambda: self.switch_map("driving Test map")),
            ("Load Map: Big City 5", lambda: self.switch_map("BigCity5")),
            ("Load Map: gm_bigcity", lambda: self.switch_map("gm_bigcity")),
            ("Load Map: MainCity2", lambda: self.switch_map("MainCity2")),
            ("Reset Map to Default ([F7])", self.reset_map_to_default),
            ("Close Panel", lambda: self.toggle_admin()),
        ]

        if getattr(self, 'cheat_mode', False):
            self.give_all_weapons()

    # ── Door mechanics ──
    def is_door_open(self, dy, dx):
        door = self.doors.get((dy, dx))
        return door['open'] > 0.75 if door else False

    def try_open_door(self, dy, dx):
        door = self.doors.get((dy, dx))
        if door and not door['opening'] and door['open'] < 0.5:
            door['opening'] = True
            door['timer'] = 4.0
            if hasattr(self, 'snd_door_unlock') and self.snd_door_unlock:
                self.snd_door_unlock.play()
            self.snd_door.play()
            self.add_log('info', f'Security door opening at ({dx},{dy})')

    def update_doors(self, dt):
        for door in self.doors.values():
            if door['opening']:
                door['open'] = min(1.0, door['open'] + dt * 2.2)
                if door['open'] >= 1.0:
                    door['timer'] -= dt
                    if door['timer'] <= 0:
                        door['opening'] = False
            elif door['open'] > 0:
                door['open'] = max(0.0, door['open'] - dt * 1.5)

    def check_nearby_doors(self):
        for (dy, dx) in self.doors:
            dist = math.sqrt((self.player_x - (dx + 0.5)) ** 2 + (self.player_y - (dy + 0.5)) ** 2)
            if dist < 2.5:
                self.try_open_door(dy, dx)
                return

        # Also check nearby Source Engine interactive stations (Health Charger, HEV Suit Charger, Ammo Crate, Soda Machine)
        for obj in getattr(self, 'placed_objects', []):
            otype = obj.get("type", "")
            if otype not in ("health_station", "suit_charger", "ammo_crate", "vending_machine"):
                continue
            ox, oy = float(obj.get("x", 0.0)), float(obj.get("y", 0.0))
            if math.hypot(self.player_x - ox, self.player_y - oy) < 2.4:
                if otype == "health_station":
                    if self.player_health < 100:
                        self.player_health = min(100, self.player_health + 25)
                        if hasattr(self, 'snd_medshot') and self.snd_medshot:
                            self.snd_medshot.play()
                        else:
                            self.play_pickup()
                        self.add_log('info', f'[COMBINE MED-CHARGER] Vital signs restored to {self.player_health}%')
                    else:
                        if hasattr(self, 'snd_medshot_no') and self.snd_medshot_no:
                            self.snd_medshot_no.play()
                        self.add_log('info', '[COMBINE MED-CHARGER] Health already at 100%.')
                elif otype == "suit_charger":
                    if self.player_armor < 100:
                        self.player_armor = min(100, self.player_armor + 25)
                        if hasattr(self, 'snd_suitcharge_ok') and self.snd_suitcharge_ok:
                            self.snd_suitcharge_ok.play()
                        else:
                            self.play_pickup()
                        self.add_log('info', f'[HEV SUIT CHARGER] Reactive armor charged to {self.player_armor}%')
                    else:
                        if hasattr(self, 'snd_suitcharge_no') and self.snd_suitcharge_no:
                            self.snd_suitcharge_no.play()
                        self.add_log('info', '[HEV SUIT CHARGER] HEV Suit power already at 100%.')
                elif otype == "ammo_crate":
                    for k in self.ammo_max:
                        self.ammo[k] = self.ammo_max[k]
                    if hasattr(self, 'snd_ammocrate_open') and self.snd_ammocrate_open:
                        self.snd_ammocrate_open.play()
                    if hasattr(self, 'snd_ammo_pickup') and self.snd_ammo_pickup:
                        self.snd_ammo_pickup.play()
                    else:
                        self.play_pickup()
                    self.add_log('info', '[RESISTANCE AMMO CRATE] All ammunition reserves replenished!')
                elif otype == "vending_machine":
                    self.player_health = min(100, self.player_health + 15)
                    if hasattr(self, 'snd_medkit_pickup') and self.snd_medkit_pickup:
                        self.snd_medkit_pickup.play()
                    else:
                        self.play_pickup()
                    self.add_log('info', "[DR. BREEN'S PRIVATE RESERVE] Dispensed refreshing water can (+15 HP)")
                return

    def get_walkable_surface_z(self, px, py, pz=0.0):
        """
        Calculates the walkable surface height (Z elevation) at world position (px, py).
        Supports ground level (0.0), stair ramps climbing from 0.0 to 2.8m,
        elevated catwalks, scaffolding platforms, and second-story building floors (2.8m).
        """
        surface_z = 0.0
        for obj in getattr(self, 'placed_objects', []):
            otype = obj.get("type", "")
            ox = float(obj.get("x", 0.0))
            oy = float(obj.get("y", 0.0))
            oz = float(obj.get("z", 0.0))
            yaw = float(obj.get("yaw", 0.0))

            dx = px - ox
            dy = py - oy
            if dx * dx + dy * dy > 25.0:
                continue

            rad = math.radians(yaw)
            cos_a = math.cos(-rad)
            sin_a = math.sin(-rad)
            lx = dx * cos_a - dy * sin_a
            ly = dx * sin_a + dy * cos_a

            if otype in ("stairs_metal", "stairs_wood", "metal_ramp"):
                # Width: 1.6m (lx: -0.8 to +0.8), Length: 3.2m (ly: -1.6 to +1.6)
                # Climbs from oz to oz + 2.8m along local Y
                if abs(lx) <= 0.90 and -1.65 <= ly <= 1.65:
                    prog = (ly + 1.6) / 3.2
                    prog = max(0.0, min(1.0, prog))
                    ramp_z = oz + prog * 2.8
                    if pz >= ramp_z - 0.55:
                        if ramp_z > surface_z:
                            surface_z = ramp_z

            elif otype in ("second_story_floor", "roof_walkway", "scaffolding"):
                half_w = 1.65 if otype != "roof_walkway" else 0.90
                half_d = 1.65
                if abs(lx) <= half_w and abs(ly) <= half_d:
                    if otype == "scaffolding":
                        if pz >= oz + 2.2:
                            plat_z = oz + 2.8
                        elif pz >= oz + 0.8:
                            plat_z = oz + 1.4
                        else:
                            plat_z = 0.0
                    else:
                        plat_z = oz + 2.8
                    if pz >= plat_z - 0.55:
                        if plat_z > surface_z:
                            surface_z = plat_z

        return surface_z

    def is_position_blocked(self, px, py, radius=0.25, pz=0.0):
        """
        Tests if (px, py) with radius is blocked by world buildings, security doors,
        or solid placed props (fences, combine barricades, sandbags, dumpsters, barrels, etc.).
        """
        if getattr(self, 'current_map', '') in ("BigCity5", "driving Test map"):
            # Whole highway template bounds: spans kilometers across the 3D world
            if not (-880.0 <= px <= 1850.0 and -1150.0 <= py <= 1760.0):
                return True
            if self.current_map == "driving Test map":
                return (abs(px - 20.5) < 0.85 + radius and abs(py - 23.5) < 0.85 + radius)
            # BigCity5: check car spawner kiosk (15.2, 32.0), arms shop (18.5, 32.0), roadside breakdown Crown Vic (12.5, 32.0), and off-road buildings
            if abs(px - 15.2) < 0.85 + radius and abs(py - 32.0) < 0.85 + radius:
                return True
            if abs(px - 18.5) < 1.25 + radius and abs(py - 32.0) < 1.25 + radius:
                return True
            # Roadside breakdown Crown Victoria (safely parked at parking turnout 12.5, 32.0)
            if abs(px - 12.5) < 1.2 + radius and abs(py - 32.0) < 2.2 + radius:
                return True
            for b_def in BIGCITY5_OFFROAD_BUILDINGS:
                bx, by = b_def["x"], b_def["y"]
                bw, bd = b_def["w"], b_def["d"]
                if abs(px - bx) < (bw * 0.5 + radius) and abs(py - by) < (bd * 0.5 + radius):
                    return True
            return False

        # 1. World grid tiles (walls & locked doors)
        ix, iy = int(px), int(py)
        if ix < 0 or ix >= MAP_W or iy < 0 or iy >= MAP_H:
            return True
        cell = MAP[iy][ix]
        if cell not in (0, 7) and not (cell == 6 and self.is_door_open(iy, ix)):
            return True

        # Check neighbor tiles if within radius
        for ox_t in (-1, 0, 1):
            for oy_t in (-1, 0, 1):
                if ox_t == 0 and oy_t == 0:
                    continue
                tx, ty = ix + ox_t, iy + oy_t
                if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
                    c = MAP[ty][tx]
                    if c not in (0, 7) and not (c == 6 and self.is_door_open(ty, tx)):
                        closest_x = max(float(tx), min(px, float(tx + 1)))
                        closest_y = max(float(ty), min(py, float(ty + 1)))
                        if (px - closest_x) ** 2 + (py - closest_y) ** 2 < radius * radius:
                            return True

        # 2. Solid placed 3D objects (fences, barricades, barrels, dumpsters, etc.)
        for obj in getattr(self, 'placed_objects', []):
            otype = obj.get("type", "")
            col_info = PROP_COLLISION_DATA.get(otype)
            if not col_info:
                continue
            shape = col_info.get("shape", "box")
            if shape in ("none", "ramp", "platform"):
                continue

            ox = float(obj.get("x", 0.0))
            oy = float(obj.get("y", 0.0))
            oz = float(obj.get("z", 0.0))
            oh = col_info.get("h", 2.0)

            # Vertical overlap check (player is ~1.8m tall)
            if pz > oz + oh or pz + 1.8 < oz:
                continue

            dx = px - ox
            dy = py - oy
            max_r = max(col_info.get("w", 1.0), col_info.get("d", 1.0)) * 0.8 + radius
            if dx * dx + dy * dy > max_r * max_r:
                continue

            if shape == "cylinder":
                cr = col_info.get("r", 0.40) + radius
                if dx * dx + dy * dy < cr * cr:
                    return True
            elif shape == "box":
                yaw = float(obj.get("yaw", 0.0))
                rad = math.radians(yaw)
                cos_a = math.cos(-rad)
                sin_a = math.sin(-rad)
                lx = dx * cos_a - dy * sin_a
                ly = dx * sin_a + dy * cos_a
                hw = col_info.get("w", 1.0) * 0.5 + radius
                hd = col_info.get("d", 1.0) * 0.5 + radius
                if abs(lx) < hw and abs(ly) < hd:
                    return True
            elif shape == "gate":
                yaw = float(obj.get("yaw", 0.0))
                rad = math.radians(yaw)
                cos_a = math.cos(-rad)
                sin_a = math.sin(-rad)
                lx = dx * cos_a - dy * sin_a
                ly = dx * sin_a + dy * cos_a
                hw = col_info.get("w", 2.8) * 0.5 + radius
                hd = col_info.get("d", 0.16) * 0.5 + radius
                open_hw = max(0.15, col_info.get("open_w", 1.6) * 0.5 - radius)
                if abs(ly) < hd:
                    # Side wings and posts collide; open center doorway is walk-through!
                    if abs(lx) < hw and abs(lx) > open_hw:
                        return True

        # 3. Physical collision for 3D Industrial Utility Building & Substation Complex (gm_bigcity)
        if getattr(self, 'current_map', 'MainCity2') == "gm_bigcity":
            # Control Building (center: 7.0, 13.5, size: 2.3 x 3.3)
            if abs(px - 7.0) < 1.15 + radius and abs(py - 13.5) < 1.65 + radius:
                return True
            # Fuel Storage Tanks (center: 8.86, 16.48, radius: 0.9m)
            if (px - 8.86) ** 2 + (py - 16.48) ** 2 < (0.90 + radius) ** 2:
                return True
            # Generator Base (center: 8.24, 11.69, size: 1.6 x 1.2)
            if abs(px - 8.24) < 1.30 + radius and abs(py - 11.69) < 0.90 + radius:
                return True
            # Power Transmission Pole (center: 6.50, 10.90, radius: 0.35m)
            if (px - 6.50) ** 2 + (py - 10.90) ** 2 < (0.35 + radius) ** 2:
                return True
            # West Perimeter Fence (along col 1)
            if px < 1.45 + radius and abs(py - 13.5) < 5.8:
                return True
            # North Retaining Wall
            if abs(py - 10.42) < 0.15 + radius and px < 7.0:
                return True

            # 4. Physical collision for 3D Destroyed High-Rise Apartment Block (gm_bigcity)
            # West standing wing (apartment rooms & exterior walls)
            if 1.5 - radius <= px <= 5.2 + radius and 1.2 - radius <= py <= 4.8 + radius:
                return True
            # East standing wing (apartment rooms & exterior walls)
            if 8.8 - radius <= px <= 12.5 + radius and 1.2 - radius <= py <= 4.8 + radius:
                return True
            # North exterior back wall
            if 1.5 - radius <= px <= 12.5 + radius and 1.0 - radius <= py <= 1.4 + radius:
                return True

        return False

    def is_position_blocked_for_vehicle(self, px, py, radius=1.0):
        """Dedicated vehicular collision detection against world boundaries, buildings, and kiosks."""
        if getattr(self, 'current_map', '') in ("BigCity5", "driving Test map"):
            # Whole highway template bounds: spans kilometers across the 3D world
            if not (-880.0 <= px <= 1850.0 and -1150.0 <= py <= 1760.0):
                return True
            if self.current_map == "driving Test map":
                # Only car spawner kiosk
                return (abs(px - 20.5) < 0.85 + radius and abs(py - 23.5) < 0.85 + radius)

            # BigCity5: check car spawner kiosk (15.2, 32.0), arms shop (18.5, 32.0), roadside breakdown Crown Vic (12.5, 32.0), and off-road buildings
            if abs(px - 15.2) < 0.85 + radius and abs(py - 32.0) < 0.85 + radius:
                return True
            if abs(px - 18.5) < 1.25 + radius and abs(py - 32.0) < 1.25 + radius:
                return True
            # Roadside breakdown Crown Victoria (safely parked at parking turnout 12.5, 32.0)
            if abs(px - 12.5) < 1.2 + radius and abs(py - 32.0) < 2.2 + radius:
                return True
            # Off-road buildings (safely set back from lanes)
            for b_def in BIGCITY5_OFFROAD_BUILDINGS:
                bx, by = b_def["x"], b_def["y"]
                bw, bd = b_def["w"], b_def["d"]
                if abs(px - bx) < (bw * 0.5 + radius) and abs(py - by) < (bd * 0.5 + radius):
                    return True
            return False

        # Regular maps (MainCity2, gm_bigcity)
        ix, iy = int(px), int(py)
        if ix < 1 or ix >= MAP_W - 1 or iy < 1 or iy >= MAP_H - 1:
            return True
        if MAP[iy][ix] not in (0, 7):
            return True

        for ox in (-1, 0, 1):
            for oy in (-1, 0, 1):
                if ox == 0 and oy == 0:
                    continue
                tx, ty = ix + ox, iy + oy
                if 0 <= tx < MAP_W and 0 <= ty < MAP_H:
                    if MAP[ty][tx] not in (0, 7):
                        closest_x = max(float(tx), min(px, float(tx + 1)))
                        closest_y = max(float(ty), min(py, float(ty + 1)))
                        if (px - closest_x) ** 2 + (py - closest_y) ** 2 < radius * radius:
                            return True
        return False

    def get_civilian_respawn_point(self):
        """Finds a safe urban spawn point for resurrected civilians > 12m from player."""
        px, py = self.player_x, self.player_y
        candidate_nodes = [
            (7.5, 9.5), (16.5, 9.5), (6.5, 15.0), (17.5, 15.5),
            (5.5, 12.0), (18.5, 12.0), (7.5, 18.5), (16.5, 18.5),
            (28.0, 12.0), (34.0, 12.0), (38.5, 20.5), (32.5, 24.5),
            (29.5, 34.5), (39.5, 34.5), (33.5, 38.5), (29.5, 20.5)
        ]
        random.shuffle(candidate_nodes)
        for (cx, cy) in candidate_nodes:
            if math.hypot(cx - px, cy - py) >= 12.0:
                mx, my = int(cx), int(cy)
                if 0 <= mx < MAP_W and 0 <= my < MAP_H and MAP[my][mx] == 0:
                    return cx, cy
        for _ in range(25):
            rx = random.uniform(4.0, MAP_W - 4.0)
            ry = random.uniform(4.0, MAP_H - 4.0)
            if math.hypot(rx - px, ry - py) >= 12.0:
                mx, my = int(rx), int(ry)
                if 0 <= mx < MAP_W and 0 <= my < MAP_H and MAP[my][mx] == 0:
                    return rx, ry
        return 16.5, 12.0

    def update_civilian_respawns(self, dt):
        """TBMG Pay-to-Respawn Economy Queue: continuously resurrects deceased civilians to keep the city bustling."""
        if not hasattr(self, 'civilian_respawn_queue'):
            self.civilian_respawn_queue = []
            return
        for item in self.civilian_respawn_queue:
            item['timer'] -= dt
        ready = [item for item in self.civilian_respawn_queue if item['timer'] <= 0]
        self.civilian_respawn_queue = [item for item in self.civilian_respawn_queue if item['timer'] > 0]
        for item in ready:
            rx, ry = self.get_civilian_respawn_point()
            new_civ = Civilian(rx, ry)
            is_vip = (random.random() < 0.30) or (item.get('plan') == 'premium')
            new_civ.is_premium = is_vip
            new_civ.respawn_plan = 'premium' if is_vip else 'standard'
            new_civ.plan_name = "TBMG LifeShield Premium VIP Plan" if is_vip else "TBMG Standard Citizen Care"
            self.entities.append(new_civ)
            self.add_log('sys', f'[TBMG RESPAWN ECONOMY] Citizen #{new_civ.id} resurrected on street ({new_civ.plan_name}).')

    def update_ambient_gunfire(self, dt):
        """Generates authentic gritty atmospheric background gunfire and ricochet echoes in MainCity2 / Ravenholm alleys."""
        if not hasattr(self, 'ambient_gunfire_timer'):
            self.ambient_gunfire_timer = random.uniform(5.0, 10.0)
        self.ambient_gunfire_timer -= dt
        if self.ambient_gunfire_timer <= 0:
            self.ambient_gunfire_timer = random.uniform(5.5, 11.5)
            ang = random.uniform(0, math.tau)
            dist = random.uniform(22.0, 38.0)
            gx = self.player_x + math.cos(ang) * dist
            gy = self.player_y + math.sin(ang) * dist
            snd = random.choice([self.snd_pistol, self.snd_smg1, self.snd_ar2])
            self._play_spatial(snd, gx, gy, max_dist=45.0)
            if random.random() < 0.35:
                quotes = [
                    "[URBAN AMBIENCE] Distant small arms gunfire exchanges heard echoing across Sector 4 tenements.",
                    "[URBAN AMBIENCE] Automatic weapon bursts detected deep within Ravenholm alleyways.",
                    "[URBAN AMBIENCE] Remote Overwatch suppression skirmish reported in eastern residential blocks."
                ]
                self.add_log('ambient', random.choice(quotes), priority='ambient')

    def populate_world(self):
        px, py = self.player_x, self.player_y

        def is_safe_from_player(x, y, min_dist=13.5):
            return math.hypot(x - px, y - py) >= min_dist

        if self.current_map == "driving Test map":
            # Dedicated driving test map: strictly ZERO NPCs, monsters, or pickups!
            self.entities = []
            self.vehicles = []
            self.traffic_vehicles = []
            self.pickups = []
            self.weapon_pickup_positions = []
            return

        if self.current_map == "gm_bigcity":
            # Populate Garry's Mod gm_bigcity avenues, Twin Towers plaza, and Water Canals!
            civ_spawns = [
                (10.5, 8.5), (14.5, 8.5), (22.5, 8.5), (32.5, 8.5),
                (10.5, 18.5), (28.5, 18.5), (23.5, 25.5), (14.5, 25.5)
            ]
            for cx, cy in civ_spawns:
                if 0 <= int(cy) < MAP_H and 0 <= int(cx) < MAP_W and MAP[int(cy)][int(cx)] == 0:
                    self.entities.append(Civilian(cx, cy))

            baton_spawns = [
                (10.5, 6.5), (28.5, 6.5), (10.5, 28.5), (28.5, 28.5), (34.5, 18.5)
            ]
            for bx, by in baton_spawns:
                if 0 <= int(by) < MAP_H and 0 <= int(bx) < MAP_W and MAP[int(by)][int(bx)] == 0 and is_safe_from_player(bx, by, 12.0):
                    self.entities.append(MCPDUnit(bx, by, weapon_type='stunstick'))

            pistol_spawns = [
                (14.5, 6.5), (24.5, 6.5), (11.5, 30.5), (29.5, 30.5), (34.5, 10.5)
            ]
            for px_s, py_s in pistol_spawns:
                if 0 <= int(py_s) < MAP_H and 0 <= int(px_s) < MAP_W and MAP[int(py_s)][int(px_s)] == 0 and is_safe_from_player(px_s, py_s, 12.0):
                    self.entities.append(MCPDUnit(px_s, py_s, weapon_type='pistol'))

            # Source Engine Water Physics Props floating in gm_bigcity Central Canal (x=15..30, y=11..16) & South Harbor (y=27..30)
            water_props = [
                (17.5, 13.5, 'barrel'), (19.2, 14.5, 'barrel'), (21.5, 13.2, 'crate'),
                (23.5, 14.8, 'barrel'), (25.5, 13.5, 'crate'), (27.5, 14.2, 'explosive_barrel'),
                (18.5, 16.8, 'barrel'), (20.2, 16.8, 'crate'), (22.0, 16.8, 'explosive_barrel'),
                (10.5, 28.5, 'barrel'), (14.5, 28.5, 'crate'), (31.5, 28.5, 'barrel'), (35.5, 28.5, 'crate'),
            ]
            for px_p, py_p, ptype in water_props:
                self.entities.append(PropEntity(px_p, py_p, ptype))

            # Distant hostiles across gm_bigcity perimeter sectors (> 16m from player spawn 18.5, 18.0)
            rpg_spawns = [(5.5, 6.5), (38.5, 6.5), (5.5, 32.5), (38.5, 32.5)]
            for rx, ry in rpg_spawns:
                if 0 <= int(ry) < MAP_H and 0 <= int(rx) < MAP_W and MAP[int(ry)][int(rx)] == 0:
                    self.entities.append(RPGGanger(rx, ry))

            for _ in range(4):
                x, y = random.uniform(33, 44), random.uniform(28, 38)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 15.0):
                    self.entities.append(MilitaryUnit(x, y))

            for _ in range(4):
                x, y = random.uniform(2, 9), random.uniform(26, 36)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 15.0):
                    self.entities.append(ImpEntity(x, y))

            for _ in range(2):
                x, y = random.uniform(34, 40), random.uniform(2, 8)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 15.0):
                    self.entities.append(DemonEntity(x, y))

        elif self.current_map == "BigCity5":
            # Peaceful urban civilians strolling along Big City 5 sidewalks & promenades
            civ_spawns = [
                (20.5, 22.5), (25.5, 22.5), (15.5, 27.5), (24.5, 27.5), (18.5, 32.5),
                (12.5, 16.5), (28.5, 16.5), (10.5, 25.5), (31.5, 22.5), (16.5, 33.5)
            ]
            for cx, cy in civ_spawns:
                self.entities.append(Civilian(cx, cy))

            self.vehicles = []
            self._init_traffic_system()

        else:
            # Civilians milling around the City-17 Grand Station Plaza (spaced with breathing room > 3.0m from 12.0, 15.0)
            civ_spawns = [
                (7.5, 9.5), (16.5, 9.5), (6.5, 15.0), (17.5, 15.5),
                (5.5, 12.0), (18.5, 12.0), (7.5, 18.5), (16.5, 18.5),
                (28.0, 12.0), (34.0, 12.0)
            ]
            for cx, cy in civ_spawns:
                if 0 <= int(cy) < MAP_H and 0 <= int(cx) < MAP_W and MAP[int(cy)][int(cx)] == 0:
                    self.entities.append(Civilian(cx, cy))

            # Civil Protection Metrocops stationed at perimeter checkpoints (> 11m from player spawn)
            baton_spawns = [
                (9.5, 5.5), (14.5, 5.5), (24.5, 11.5), (32.0, 12.0),
                (14.5, 24.5), (22.5, 24.5)
            ]
            for bx, by in baton_spawns:
                if 0 <= int(by) < MAP_H and 0 <= int(bx) < MAP_W and MAP[int(by)][int(bx)] == 0 and is_safe_from_player(bx, by, 11.0):
                    self.entities.append(MCPDUnit(bx, by, weapon_type='stunstick'))

            pistol_spawns = [
                (11.5, 3.5), (13.5, 3.5),
                (25.5, 11.0), (25.5, 13.0),
                (28.0, 11.0), (38.0, 12.0)
            ]
            for px_s, py_s in pistol_spawns:
                if 0 <= int(py_s) < MAP_H and 0 <= int(px_s) < MAP_W and MAP[int(py_s)][int(px_s)] == 0 and is_safe_from_player(px_s, py_s, 11.0):
                    self.entities.append(MCPDUnit(px_s, py_s, weapon_type='pistol'))

            # Source Engine Water Physics Props floating in MainCity2 Canal & Dry-Land Explosive/Buoyancy Barrels
            water_props = [
                (7.2, 16.8, 'barrel'), (8.6, 17.5, 'barrel'), (7.8, 18.2, 'crate'),
                (9.4, 16.5, 'crate'), (10.3, 17.2, 'explosive_barrel'),
                (17.2, 16.8, 'barrel'), (18.8, 17.4, 'explosive_barrel'), (20.4, 16.8, 'crate'),
                (28.5, 16.8, 'barrel'), (30.5, 17.4, 'crate'), (32.5, 16.8, 'explosive_barrel'),
                (14.8, 14.8, 'explosive_barrel'), (15.6, 14.8, 'barrel'), (26.5, 12.2, 'explosive_barrel'),
            ]
            for px_p, py_p, ptype in water_props:
                self.entities.append(PropEntity(px_p, py_p, ptype))

            # Pre-spawn Drivable Vehicles on MainCity2's Connected South Highway (incl. MCPD Police Interceptor Cruiser!)
            self.vehicles = []
            cv_spec = next((v for v in VEHICLE_CATALOG if v["id"] == "crown_vic"), None)
            if cv_spec:
                police_veh = DrivableVehicle(cv_spec, 23.5, 28.5, 0.0)
                police_veh.dlist = self.get_vehicle_dlist("crown_vic")
                police_veh.siren_on = True
                self.vehicles.append(police_veh)
            sedan_spec = next((v for v in VEHICLE_CATALOG if v["id"] != "crown_vic"), None)
            if sedan_spec:
                bay_veh = DrivableVehicle(sedan_spec, 18.5, 31.0, 0.0)
                bay_veh.dlist = self.get_vehicle_dlist(sedan_spec["id"])
                self.vehicles.append(bay_veh)

            # Elite Combine Overwatch
            for _ in range(2):
                x, y = random.uniform(26, 30), random.uniform(3.5, 5.5)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 14.0):
                    self.entities.append(ECPUUnit(x, y))

            # Distant Hostiles: RPG Gangers in South Canal Alleyways (> 14m from player)
            for _ in range(4):
                x, y = random.uniform(4, 9), random.uniform(26, 32)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 14.0):
                    self.entities.append(RPGGanger(x, y))

            # Military Heavy Units in Citadel Sector
            for _ in range(4):
                x, y = random.uniform(35, 45), random.uniform(29, 37)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 16.0):
                    self.entities.append(MilitaryUnit(x, y))

            # Monsters in Far Industrial Alleys
            for _ in range(4):
                x, y = random.uniform(28, 36), random.uniform(22, 28)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 14.0):
                    self.entities.append(ImpEntity(x, y))

            for _ in range(2):
                x, y = random.uniform(32, 40), random.uniform(2, 6)
                if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0 and is_safe_from_player(x, y, 16.0):
                    self.entities.append(DemonEntity(x, y))

        # Spawn a couple of 3D Pink Dodge Chargers on the streets (MainCity2 & gm_bigcity only)
        if self.current_map not in ("BigCity5", "driving Test map"):
            self.entities.append(PropEntity(18.5, 19.5, 'charger'))
            self.entities.append(PropEntity(14.5, 25.5, 'charger'))

        # Spawn any user-placed Map Editor entities saved in custom_maps.json
        for obj in self.placed_objects:
            self._spawn_saved_entity_object(obj.get("type"), float(obj.get("x", 12.0)), float(obj.get("y", 12.0)))

        pickup_positions = [
            (3.5, 1.5, 'health_small'), (8.5, 3.5, 'ammo_bullets'),
            (5.5, 8.5, 'health_large'), (11.5, 9.5, 'ammo_shells'),
            (15.5, 5.5, 'armor_small'), (20.5, 6.5, 'health_small'),
            (3.5, 15.5, 'ammo_bullets'), (8.5, 18.5, 'health_small'),
            (14.5, 14.5, 'ammo_rockets'), (18.5, 10.5, 'armor_large'),
            (22.5, 5.5, 'ammo_energy'), (7.5, 10.5, 'ammo_cells'),
            (26.5, 2.5, 'health_large'), (28.5, 4.5, 'ammo_shells'),
            (26.5, 8.5, 'ammo_cells'), (28.5, 12.5, 'health_small'),
            (27.5, 15.5, 'ammo_rockets'), (26.5, 20.5, 'ammo_energy'),
            (29.5, 21.5, 'health_large'), (4.5, 12.5, 'armor_small'),
        ]
        for px, py, ptype in pickup_positions:
            if 0 <= int(py) < MAP_H and 0 <= int(px) < MAP_W and MAP[int(py)][int(px)] in (0, 7):
                self.pickups.append(Pickup(px, py, ptype))

        self.weapon_pickup_positions = [
            (8.5, 5.5, 2, 'SMG1 Submachine Gun'),
            (15.5, 8.5, 3, 'SPAS-12 Combat Shotgun'),
            (18.5, 14.5, 4, 'AR2 Overwatch Pulse Rifle'),
            (20.5, 4.5, 5, '.357 Magnum Revolver'),
            (27.5, 3.5, 6, 'RPG-7 Warhead Launcher'),
        ]
        self.weapon_pickups_alive = [True] * len(self.weapon_pickup_positions)

        if MAP[14][27] in (0, 7):
            self.pickups.append(Pickup(27.5, 14.5, 'berserk'))

        self.add_log('sys', f'Source Engine World [{self.current_map}] online. Units: {len(self.entities)}')
        self.add_log('info', f'Graphics Preset: {self.graphics_preset} | Fog: {"ON" if self.fog_enabled else "OFF"} ([ESC] Pause Menu)')
        self.level_start_time = self.sim_time

    def add_log(self, level, msg, priority="normal"):
        """
        Logs game events to the external terminal with smart anti-spam filtering.
        In 'clean' mode (default), ambient chatter, repetitive damage ticks,
        micro-events, and duplicate dispatches are suppressed so the terminal stays clean.
        """
        sim_t = getattr(self, 'sim_time', 0.0)
        u_msg = msg.upper()

        # In clean mode, filter out ambient chatter and micro events
        if getattr(self, 'log_mode', 'clean') == 'clean':
            if priority in ('ambient', 'micro'):
                return
            if (
                "SOMETIMES, I DREAM ABOUT CHEESE" in u_msg or
                "BUMPED OFFICER" in u_msg or
                "SECURITY DOOR OPENING" in u_msg or
                "CAMERA SWITCHED" in u_msg or
                "PUNTED " in u_msg or
                "RELOADING " in u_msg or
                "RELOADED!" in u_msg
            ):
                return
            # Rate-limit Combine CP radio lines: at most once every 14 seconds
            if "COMBINE CP" in u_msg or "CIVIL PROTECTION" in u_msg:
                last_t = self.last_log_times.get('combine_cp', -999.0)
                if sim_t - last_t < 14.0:
                    return
                self.last_log_times['combine_cp'] = sim_t

            # Rate-limit Citizen lines: at most once every 16 seconds
            if "CITIZEN #" in u_msg:
                last_t = self.last_log_times.get('citizen_voice', -999.0)
                if sim_t - last_t < 16.0:
                    return
                self.last_log_times['citizen_voice'] = sim_t

        # Deduplicate identical message within 3.5s
        msg_key = f"{level}:{msg[:40]}"
        last_msg_t = self.last_log_times.get(msg_key, -999.0)
        if sim_t - last_msg_t < 3.5:
            return
        self.last_log_times[msg_key] = sim_t

        self.console_log.append({'level': level, 'msg': msg, 'time': sim_t, 'age': 0})
        if len(self.console_log) > 16:
            self.console_log.pop(0)
        formatted = format_colored_log_line(level, msg, sim_t)
        try:
            with open(LIVE_LOG_FILE, "a", encoding="utf-8") as lf:
                lf.write(formatted + "\n")
        except Exception:
            pass
        try:
            print(formatted, flush=True)
        except Exception:
            pass

    def _play_spatial(self, snd, sx=None, sy=None, max_dist=None):
        if max_dist is None:
            max_dist = SOUND_RANGE
        if sx is not None and sy is not None:
            dist = math.sqrt((sx - self.player_x) ** 2 + (sy - self.player_y) ** 2)
            if dist > max_dist:
                return
            vol = max(0.05, 1.0 - (dist / max_dist) ** 0.6)
            snd.set_volume(vol)
        else:
            snd.set_volume(1.0)
        return snd.play()

    def play_radio_click(self, sx=None, sy=None):
        self._play_spatial(self.snd_radio, sx, sy)

    def play_combine_vo(self, sx=None, sy=None):
        if hasattr(self, 'snd_combine_vo_list') and self.snd_combine_vo_list:
            self._play_spatial(random.choice(self.snd_combine_vo_list), sx, sy, max_dist=22.0)
        else:
            self._play_spatial(self.snd_radio, sx, sy)

    def play_citizen_panic(self, sx=None, sy=None):
        if hasattr(self, 'snd_citizen_panic_list') and self.snd_citizen_panic_list:
            self._play_spatial(random.choice(self.snd_citizen_panic_list), sx, sy, max_dist=22.0)

    def play_citizen_combat(self, sx=None, sy=None):
        if hasattr(self, 'snd_citizen_combat_list') and self.snd_citizen_combat_list:
            self._play_spatial(random.choice(self.snd_citizen_combat_list), sx, sy, max_dist=22.0)

    def alert_nearby_citizens(self, threat_x, threat_y, threat_source=None):
        for e in self.entities:
            if e.alive and e.type == 'civilian':
                d = math.hypot(e.x - threat_x, e.y - threat_y)
                if d < 15.0:
                    e.react_to_threat(threat_x, threat_y, self, threat_source)

    def spawn_wall_bullet_decal(self, hit_x, hit_y, hit_z, nx, ny, nz=0.0):
        self.total_shots_fired = getattr(self, 'total_shots_fired', 0) + 1
        self.bullet_decals.append({
            'x': hit_x,
            'y': hit_z,
            'z': hit_y,
            'nx': nx,
            'ny': ny,
            'nz': nz,
            'size': random.uniform(0.09, 0.14),
            'rot': random.uniform(0.0, 360.0),
            'time': self.sim_time,
            'shot_num': self.total_shots_fired,
        })
        while len(self.bullet_decals) > self.max_bullet_decals:
            self.bullet_decals.pop(0)

    def play_citizen_talk(self, sx=None, sy=None):
        if hasattr(self, 'snd_citizen_talk_list') and self.snd_citizen_talk_list:
            self._play_spatial(random.choice(self.snd_citizen_talk_list), sx, sy, max_dist=16.0)

    def play_combine_hit(self, sx=None, sy=None):
        self._play_spatial(self.snd_combine_hit, sx, sy)

    def play_explosion(self, sx=None, sy=None):
        snd = random.choice(self.snd_explosion_list) if getattr(self, 'snd_explosion_list', None) else self.snd_explosion
        self._play_spatial(snd, sx, sy, max_dist=25.0)

    def play_surface_footstep(self):
        """Plays genuine Half-Life 2 surface-aware footstep audio (Water Slosh, Metal, Dirt, or Concrete)."""
        if getattr(self, 'player_in_water', False) and getattr(self, 'snd_footsteps_water', None):
            random.choice(self.snd_footsteps_water).play()
        elif getattr(self, 'player_z', 0.0) > 0.25 and getattr(self, 'snd_footsteps_metal', None):
            random.choice(self.snd_footsteps_metal).play()
        elif self.current_map == "BigCity5" and (self.player_x > 36.0 or self.player_x < -12.0) and getattr(self, 'snd_footsteps_dirt', None):
            random.choice(self.snd_footsteps_dirt).play()
        elif getattr(self, 'snd_footsteps_concrete', None):
            random.choice(self.snd_footsteps_concrete).play()
        elif hasattr(self, 'snd_footstep') and self.snd_footstep:
            self.snd_footstep.play()

    def play_pickup(self):
        self.snd_pickup.set_volume(1.0)
        self.snd_pickup.play()

    def play_pain(self, sx=None, sy=None, ent_type='civilian', ent_id=0):
        """
        Plays pain sound spatially. ONLY Metro Police NPCs ('mcpd') use the Metrocop pain sound;
        everything else uses Half-Life 2 Citizen pain sounds.
        Does not spam the external terminal on non-fatal bullet hits!
        """
        if ent_type == 'mcpd':
            snd = random.choice(self.snd_metrocop_pain_list) if getattr(self, 'snd_metrocop_pain_list', None) else self.snd_pain
            self._play_spatial(snd, sx, sy)
        else:
            snd = random.choice(self.snd_citizen_pain_list) if getattr(self, 'snd_citizen_pain_list', None) else self.snd_pain
            self._play_spatial(snd, sx, sy)

    def play_death(self, sx=None, sy=None, ent_type='civilian', ent_id=0):
        """
        Plays death sound and logs fatal combat milestone to the external terminal.
        """
        if ent_type == 'mcpd':
            snd = random.choice(self.snd_metrocop_death_list) if getattr(self, 'snd_metrocop_death_list', None) else self.snd_death
            self._play_spatial(snd, sx, sy, max_dist=24.0)
            self.add_log('error', f'Metrocop #{ent_id} Bio-Signal Flatline — Frequency Terminated', priority='important')
        else:
            snd = random.choice(self.snd_citizen_death_list) if getattr(self, 'snd_citizen_death_list', None) else self.snd_death
            self._play_spatial(snd, sx, sy, max_dist=22.0)
            death_line = random.choice(CITIZEN_VOICE_LINES["death"])
            label = "Citizen" if ent_type == 'civilian' else ent_type.upper()
            self.add_log('info', f'{label} #{ent_id} Eliminated: "{death_line}"', priority='important')

    def find_nearest_hostile(self, x, y, types):
        nearest = None
        nearest_d = float('inf')
        for e in self.entities:
            if not e.alive or e.type not in types:
                continue
            d = math.sqrt((e.x - x) ** 2 + (e.y - y) ** 2)
            if d < nearest_d:
                nearest_d = d
                nearest = e
        return nearest

    def report_npc_anticitizen(self, civ, reason="Discharging firearm at Civil Protection"):
        """
        A civilian NPC attacked police: flag them as an anti-citizen, broadcast the City Voice
        anti-citizen report over the whole city, and dispatch nearby Civil Protection to deal with them.
        """
        if civ is None or not civ.alive:
            return
        first_report = not getattr(civ, 'npc_wanted', False)
        civ.npc_wanted = True
        civ.npc_wanted_timer = 45.0  # stays wanted while police keep seeing them

        if first_report:
            self.add_log('danger', f'[ANTI-CITIZEN] Citizen #{civ.id}: {reason}! Civil Protection responding.', priority='important')
            # City-wide loudspeaker: anti-citizen report (falls back to a response line if PA is busy)
            if not self.trigger_overwatch_announcement(event='anticitizen'):
                self.pending_npc_pa = 'anticitizen'
            if hasattr(self, 'snd_radio') and self.snd_radio:
                self._play_spatial(self.snd_radio, civ.x, civ.y, max_dist=30.0)

        # Dispatch every officer within 30m (others will pick them up when they see them)
        responders = 0
        for e in self.entities:
            if e.alive and e.type == 'mcpd' and math.hypot(e.x - civ.x, e.y - civ.y) < 30.0:
                e.npc_target = civ
                e.last_known_px, e.last_known_py = civ.x, civ.y
                responders += 1
        if first_report and responders:
            self.add_log('sys', f'[DISPATCH] {responders} Civil Protection unit(s) en route to anti-citizen #{civ.id}', priority='ambient')

    def find_nearest_npc_anticitizen(self, x, y, max_dist=30.0):
        nearest, nearest_d = None, max_dist
        for e in self.entities:
            if e.alive and e.type == 'civilian' and getattr(e, 'npc_wanted', False):
                d = math.hypot(e.x - x, e.y - y)
                if d < nearest_d:
                    nearest, nearest_d = e, d
        return nearest

    def add_wanted(self, stars):
        old_level = self.wanted_level
        self.wanted_level = min(5, self.wanted_level + stars)
        self.wanted_decay_timer = 10.0
        if self.wanted_level > old_level:
            self.trigger_overwatch_announcement(event='anticitizen' if old_level == 0 else None, force=True)
            self.add_log('warn', f'[WANTED] Threat Level escalated to {self.wanted_level} stars')
            if self.wanted_level >= 3 and old_level < 3:
                self.add_log('sys', '[DISPATCH] ECPU Strike Teams deploying')
            if self.wanted_level >= 4 and old_level < 4:
                self.add_log('admin', '[DISPATCH] Heavy Military authorized')
            for e in self.entities:
                if e.type == 'mcpd' and e.alive:
                    if math.sqrt((e.x - self.player_x)**2 + (e.y - self.player_y)**2) < 30:
                        e.ai_state = AI_CHASE
                        e.last_known_px = self.player_x
                        e.last_known_py = self.player_y

    def report_sound_event(self, x, y, radius, factions):
        for e in self.entities:
            if not e.alive or e.type not in factions:
                continue
            if math.sqrt((e.x - x)**2 + (e.y - y)**2) < radius:
                if getattr(e, 'ai_state', AI_IDLE) == AI_IDLE:
                    e.ai_state = AI_ALERT
                    e.last_known_px = x + random.uniform(-2, 2)
                    e.last_known_py = y + random.uniform(-2, 2)

    def fire_combine_ball(self, x, y, tx, ty, owner):
        self.projectiles.append(CombineBall(x, y, tx, ty, owner))
        self._play_spatial(self.snd_combine_fire, x, y)

    def fire_rpg_rocket(self, x, y, tx, ty, owner):
        self.projectiles.append(RPGRocket(x, y, tx, ty, owner))

    def fire_imp_fireball(self, x, y, tx, ty):
        self.projectiles.append(ImpFireball(x, y, tx, ty))

    def spawn_explosion(self, x, y):
        self.explosions_list.append(Explosion(x, y))
        self.screen_shake = max(self.screen_shake, 0.35)
        # Apply VPhysics inward crumple damage to any nearby drivable or traffic vehicles
        all_vehs = list(getattr(self, 'vehicles', [])) + list(getattr(self, 'traffic_vehicles', []))
        for v in all_vehs:
            d_v = math.hypot(v.x - x, v.y - y)
            if d_v < 7.5 and hasattr(v, 'apply_impact_damage'):
                sev = max(0.30, min(1.0, (7.5 - d_v) / 6.0))
                v.apply_impact_damage(x, y, severity=sev, hit_h=0.20)

    def player_take_damage(self, amt):
        if self.invuln_timer > 0 or getattr(self, 'spawn_protection_timer', 0) > 0 or getattr(self, 'map_editor_active', False):
            return
        if self.player_armor > 0:
            absorbed = min(amt // 2, self.player_armor)
            self.player_armor -= absorbed
            amt -= absorbed
        self.player_health -= amt
        self.damage_flash = 0.35
        self.screen_shake = max(self.screen_shake, 0.25)
        if self.player_health <= 0:
            self.player_health = 100
            self.player_armor = 50
            if self.current_map == "driving Test map":
                self.player_x = 20.5
                self.player_y = 21.8
            elif self.current_map == "BigCity5":
                self.player_x = 22.5
                self.player_y = 24.5
            elif self.current_map == "gm_bigcity":
                self.player_x = 18.5
                self.player_y = 18.0
            else:
                self.player_x = 12.0
                self.player_y = 15.0
            self.spawn_protection_timer = 5.0
            self.wanted_level = 0
            self.add_log('error', '[DEATH] President Michael redeployed (executive privilege)')

    def apply_player_knockback(self, kx, ky, dist=0.35):
        """
        Safely applies physical pushback to the player with wall collision testing and sliding.
        Never allows the player to clip or teleport inside solid building walls or props.
        """
        if getattr(self, 'noclip', False):
            self.player_x += kx * dist
            self.player_y += ky * dist
            return

        steps = 4
        sx = (kx * dist) / steps
        sy = (ky * dist) / steps
        pz = getattr(self, 'player_z', 0.0)
        for _ in range(steps):
            cand_x = self.player_x + sx
            cand_y = self.player_y + sy
            if not self.is_position_blocked(cand_x, cand_y, radius=0.18, pz=pz):
                self.player_x = cand_x
                self.player_y = cand_y
            elif not self.is_position_blocked(cand_x, self.player_y, radius=0.18, pz=pz):
                self.player_x = cand_x
            elif not self.is_position_blocked(self.player_x, cand_y, radius=0.18, pz=pz):
                self.player_y = cand_y
            else:
                break

    def fire_weapon(self):
        if self.is_reloading:
            # SPAS-12 Shotgun (wid 3) allows interruptible firing during shell-by-shell reload
            if self.current_weapon == 3 and self.weapon_clips.get(3, 0) > 0:
                self.is_reloading = False
                self.reload_timer = 0.0
            else:
                return
        weap = WEAPONS[self.current_weapon]
        if self.weapon_cooldown > 0 or self.weapon_switch_timer > 0.08:
            return

        # Clip depletion check (both Sandbox and Survival modes require reload!)
        clip_size = weap.get('clip_size', 0)
        if clip_size > 0:
            cur_clip = self.weapon_clips.get(self.current_weapon, 0)
            if cur_clip <= 0:
                self.start_reload()
                return
            self.weapon_clips[self.current_weapon] = cur_clip - 1

        # Firing cancels tactical sprint pose immediately like Call of Duty
        self.is_sprinting = False
        self.sprint_blend = min(self.sprint_blend, 0.15)
        self.weapon_cooldown = weap['fire_rate']
        self.weapon_fired = 1.0
        self.screen_shake = max(self.screen_shake, 0.08)

        # Eject spinning 3D brass shell casing for ballistic weapons (USP Match, SMG1, SPAS-12)
        if self.current_weapon in (1, 2, 3):
            self.shell_casings.append([
                0.18 * (1.0 - self.ads_blend * 0.6), -0.14, -0.36,
                random.uniform(0.9, 1.5), random.uniform(0.6, 1.2), random.uniform(0.2, 0.6),
                0.0
            ])

        snd_map = {
            0: self.snd_crowbar,
            1: self.snd_pistol,
            2: self.snd_smg1,
            3: self.snd_shotgun,
            4: self.snd_ar2,
            5: self.snd_357,
            6: self.snd_rpg,
        }
        snd = snd_map.get(self.current_weapon)
        if snd:
            snd.play()

        # Schedule authentic Half-Life 2 SPAS-12 shotgun pump-action rack sound (shotgun_cock.wav)
        if self.current_weapon == 3:
            self.shotgun_pump_timer = 0.24

        radius = 30 if self.current_weapon in (3, 5, 6) else 15
        self.report_sound_event(self.player_x, self.player_y, radius, ['mcpd', 'military', 'ecpu', 'imp', 'demon', 'rpg'])

        if weap['hitscan']:
            pellets = weap.get('pellets', 1)
            spread_mult = 0.35 if self.aim_zoom else 1.0
            for _ in range(pellets):
                angle = self.player_angle + random.uniform(-weap['spread'] * spread_mult, weap['spread'] * spread_mult)
                self._hitscan_fire(angle, weap['damage'], weap['range'], weap['color'])
        elif weap['projectile']:
            tx = self.player_x + math.cos(self.player_angle) * 20
            ty = self.player_y + math.sin(self.player_angle) * 20
            if self.current_weapon == 6:  # RPG-7 Warhead Launcher
                self.projectiles.append(RPGRocket(self.player_x, self.player_y, tx, ty, None))
                self.screen_shake = 0.4

        # If clip is now empty, auto-trigger tactical reload immediately
        if clip_size > 0 and self.weapon_clips.get(self.current_weapon, 0) == 0:
            self.start_reload()

    def _hitscan_fire(self, angle, damage, max_range, col):
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)
        if self.berserk_timer > 0 and self.current_weapon == 0:
            damage *= 10

        step = 0.15
        dist = 0
        end_x = self.player_x + cos_a * max_range
        end_y = self.player_y + sin_a * max_range
        hit_wall = False
        hit_normal = (0.0, 0.0, 0.0)

        prev_rx = self.player_x
        prev_ry = self.player_y

        while dist < max_range:
            dist += step
            rx = self.player_x + cos_a * dist
            ry = self.player_y + sin_a * dist

            mx, my = int(rx), int(ry)
            if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
                end_x, end_y = rx, ry
                break
            if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and self.is_door_open(my, mx)):
                end_x, end_y = rx, ry
                hit_wall = True
                prev_mx = int(prev_rx)
                prev_my = int(prev_ry)
                if prev_mx < mx:
                    hit_normal = (-1.0, 0.0, 0.0)
                    end_x = float(mx)
                elif prev_mx > mx:
                    hit_normal = (1.0, 0.0, 0.0)
                    end_x = float(mx + 1)
                elif prev_my < my:
                    hit_normal = (0.0, 0.0, -1.0)
                    end_y = float(my)
                elif prev_my > my:
                    hit_normal = (0.0, 0.0, 1.0)
                    end_y = float(my + 1)
                else:
                    if abs(cos_a) > abs(sin_a):
                        hit_normal = (-1.0 if cos_a > 0 else 1.0, 0.0, 0.0)
                    else:
                        hit_normal = (0.0, 0.0, -1.0 if sin_a > 0 else 1.0)
                break

            # Check solid placed props (fences, barricades, sandbags, dumpsters, crates, barrels)
            bullet_z = max(0.1, 0.72 + self.player_z + math.tan(self.player_pitch) * dist)
            for p_obj in getattr(self, 'placed_objects', []):
                p_type = p_obj.get("type", "")
                p_col = PROP_COLLISION_DATA.get(p_type)
                if not p_col:
                    continue
                p_shape = p_col.get("shape", "box")
                if p_shape in ("none", "platform"):
                    continue
                ox = float(p_obj.get("x", 0.0))
                oy = float(p_obj.get("y", 0.0))
                oz = float(p_obj.get("z", 0.0))
                oh = p_col.get("h", 2.0)
                if not (oz - 0.1 <= bullet_z <= oz + oh + 0.1):
                    continue

                dx_p = rx - ox
                dy_p = ry - oy
                hit_prop = False
                if p_shape == "cylinder":
                    cr = p_col.get("r", 0.40)
                    if dx_p * dx_p + dy_p * dy_p < cr * cr:
                        hit_prop = True
                elif p_shape in ("box", "ramp"):
                    yaw = float(p_obj.get("yaw", 0.0))
                    rad = math.radians(yaw)
                    cos_y = math.cos(-rad)
                    sin_y = math.sin(-rad)
                    lx = dx_p * cos_y - dy_p * sin_y
                    ly = dx_p * sin_y + dy_p * cos_y
                    hw = p_col.get("w", 1.0) * 0.5
                    hd = p_col.get("d", 1.0) * 0.5
                    if abs(lx) < hw and abs(ly) < hd:
                        hit_prop = True
                elif p_shape == "gate":
                    yaw = float(p_obj.get("yaw", 0.0))
                    rad = math.radians(yaw)
                    cos_y = math.cos(-rad)
                    sin_y = math.sin(-rad)
                    lx = dx_p * cos_y - dy_p * sin_y
                    ly = dx_p * sin_y + dy_p * cos_y
                    hw = p_col.get("w", 2.8) * 0.5
                    hd = p_col.get("d", 0.22) * 0.5
                    open_hw = p_col.get("open_w", 1.5) * 0.5
                    if abs(ly) < hd and abs(lx) < hw and abs(lx) > open_hw:
                        hit_prop = True

                if hit_prop:
                    end_x, end_y = rx, ry
                    hit_wall = True
                    hit_normal = (-cos_a, 0.0, -sin_a)
                    if p_type in ('explosive_barrel', 'fuel_tank', 'gas_canister'):
                        if hasattr(self, 'trigger_explosion'):
                            self.trigger_explosion(ox, oy, 65, 4.0)
                    break

            if hit_wall:
                break

            # Check hit against drivable and NPC traffic vehicles (VPhysics 3D mesh inward crumple!)
            all_vehs = list(getattr(self, 'vehicles', [])) + list(getattr(self, 'traffic_vehicles', []))
            for v in all_vehs:
                if getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None) is v:
                    continue
                v_hw = v.spec.get("length", 4.8) * 0.48
                v_hd = v.spec.get("width", 2.0) * 0.48
                dx_v = rx - v.x
                dy_v = ry - v.y
                if dx_v * dx_v + dy_v * dy_v < (v_hw + v_hd) ** 2:
                    cos_vy = math.cos(-v.yaw)
                    sin_vy = math.sin(-v.yaw)
                    lvx = dx_v * cos_vy - dy_v * sin_vy
                    lvy = dx_v * sin_vy + dy_v * cos_vy
                    if abs(lvx) < v_hw and abs(lvy) < v_hd and 0.0 <= bullet_z <= 2.1:
                        if hasattr(v, 'apply_impact_damage'):
                            sev = min(0.65, max(0.14, damage / 75.0))
                            v.apply_impact_damage(rx, ry, severity=sev, hit_h=(bullet_z - 0.85) * 0.5)
                        v_integrity = max(5, int(100 - len(getattr(v, 'crumple_impacts', [])) * 12))
                        if hasattr(self, 'register_player_hit'):
                            self.register_player_hit(
                                v.spec.get("name", "VEHICLE").upper(),
                                v_integrity,
                                100,
                                is_kill=False,
                                is_metal=True,
                            )
                        self.crosshair_hit = 0.35
                        if hasattr(self, 'snd_metal') and self.snd_metal:
                            self.snd_metal.play()
                        end_x, end_y = rx, ry
                        if self.current_weapon != 0:
                            self.tracers.append([
                                self.player_x + cos_a * 0.4, 0.72 + self.player_z, self.player_y + sin_a * 0.4,
                                end_x, bullet_z, end_y,
                                (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0), 0.12
                            ])
                        return

            for e in self.entities:
                if not e.alive:
                    continue
                d = math.sqrt((rx - e.x) ** 2 + (ry - e.y) ** 2)
                if d < 0.65:
                    e.take_damage(damage, self, source='player')
                    self.crosshair_hit = 0.3
                    # Source vphysics ballistic impact impulse on props and NPCs!
                    k_mult = 6.5 if isinstance(e, PropEntity) else 3.5
                    e.vx += cos_a * k_mult
                    e.vy += sin_a * k_mult
                    end_x, end_y = rx, ry
                    if self.current_weapon != 0:
                        self.tracers.append([
                            self.player_x + cos_a * 0.4, 0.72 + self.player_z, self.player_y + sin_a * 0.4,
                            end_x, 0.65 + getattr(e, 'z', 0.0), end_y,
                            (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0), 0.12
                        ])
                    return

            prev_rx = rx
            prev_ry = ry

        hit_z = max(0.2, min(2.8, 0.72 + self.player_z + math.tan(self.player_pitch) * dist))

        # Add 3D persistent bullet impact decal to the wall face (Crowbar doesn't create bullet holes)
        if hit_wall and self.current_weapon != 0:
            nx, ny, nz = hit_normal
            self.total_shots_fired = getattr(self, 'total_shots_fired', 0) + 1
            self.bullet_decals.append({
                'x': end_x,
                'y': hit_z,
                'z': end_y,
                'nx': nx,
                'ny': ny,
                'nz': nz,
                'size': random.uniform(0.09, 0.14),
                'rot': random.uniform(0.0, 360.0),
                'time': self.sim_time,
                'shot_num': self.total_shots_fired,
            })
            # FIFO: When capacity exceeds limit, pop oldest decals first
            while len(self.bullet_decals) > self.max_bullet_decals:
                self.bullet_decals.pop(0)

        if self.current_weapon != 0:
            self.tracers.append([
                self.player_x + cos_a * 0.4, 0.72 + self.player_z, self.player_y + sin_a * 0.4,
                end_x, hit_z if hit_wall else 0.65, end_y,
                (col[0] / 255.0, col[1] / 255.0, col[2] / 255.0), 0.12
            ])

    # ── Admin commands ──
    def admin_spawn(self, etype):
        sx = self.player_x + math.cos(self.player_angle) * 2.5
        sy = self.player_y + math.sin(self.player_angle) * 2.5
        mx, my = int(sx), int(sy)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H or MAP[my][mx] not in (0, 7):
            sx, sy = self.player_x, self.player_y

        cls_map = {
            'civilian': Civilian, 'mcpd': MCPDUnit, 'ecpu': ECPUUnit,
            'rpg': RPGGanger, 'imp': ImpEntity, 'demon': DemonEntity,
        }
        if etype in cls_map:
            self.entities.append(cls_map[etype](sx, sy))
            self.add_log('admin', f'[PRESIDENT] Spawned 3D {etype} at ({sx:.1f},{sy:.1f})')
        elif etype in ('charger', 'barrel', 'crate', 'explosive_barrel', 'pillow'):
            self.entities.append(PropEntity(sx, sy, etype))
            self.add_log('admin', f'[VPHYSICS] Spawned 3D {etype} at ({sx:.1f},{sy:.1f})')
            self.snd_metal.play()
            self.check_crash_threshold()

    def check_crash_threshold(self):
        c = sum(1 for e in self.entities if e.alive and e.type == 'charger')
        p = sum(1 for e in self.entities if e.alive and e.type == 'pillow')
        if c + p > 50:
            self.add_log('error', f'[SERVER] PROP LIMIT ({c+p}) — crash imminent')
            self.trigger_crash(f'{c} Chargers + {p} Pillows exceed limit')

    def toggle_noclip(self):
        self.noclip = not self.noclip
        self.add_log('admin', f'[PRESIDENT] noclip {"ON" if self.noclip else "OFF"}')

    def give_all_weapons(self):
        for i in range(7):
            self.weapons_owned[i] = True
        self.ammo = {k: v for k, v in self.ammo_max.items()}
        for i in range(7):
            self.weapon_clips[i] = WEAPONS[i]['clip_size']
        self.add_log('admin', '[SANDBOX] All 7 Half-Life 2 weapons unlocked — FULLY ARMED')

    def start_reload(self):
        if self.is_reloading:
            return
        weap = WEAPONS[self.current_weapon]
        clip_size = weap.get('clip_size', 0)
        if clip_size <= 0:
            return
        cur_clip = self.weapon_clips.get(self.current_weapon, 0)
        if cur_clip >= clip_size:
            return
        is_sandbox = getattr(self, 'sandbox_mode', False) or getattr(self, 'cheat_mode', False)
        if not is_sandbox:
            if self.ammo.get(weap['ammo_type'], 0) <= 0:
                self.add_log('warn', f'No reserve ammo for {weap["name"]}!')
                return

        self.is_reloading = True
        if self.current_weapon == 3:  # SPAS-12 Shotgun loads one shell at a time (~0.48s per shell)
            self.reload_duration = 0.48
            self.reload_timer = 0.0
            if getattr(self, 'snd_shotgun_reload_list', None):
                random.choice(self.snd_shotgun_reload_list).play()
            elif hasattr(self, 'snd_shotgun_reload') and self.snd_shotgun_reload:
                self.snd_shotgun_reload.play()
        else:
            self.reload_duration = weap['reload_time']
            self.reload_timer = 0.0
            reload_snds = {
                1: self.snd_pistol_reload,
                2: self.snd_smg1_reload,
                4: self.snd_ar2_reload,
                5: self.snd_357_reload,
                6: self.snd_rpg_reload,
            }
            snd = reload_snds.get(self.current_weapon)
            if snd:
                snd.play()
        self.add_log('info', f'Reloading {weap["name"]}...')

    def fire_burst(self):
        for i in range(8):
            a = (i / 8) * math.pi * 2
            tx = self.player_x + math.cos(a) * 8
            ty = self.player_y + math.sin(a) * 8
            self.projectiles.append(CombineBall(self.player_x, self.player_y, tx, ty, 'player'))
        self.snd_combine_fire.play()
        self.add_log('admin', '[PRESIDENT] Combine ball burst (8 projectiles)')

    def mass_spawn_crash(self):
        for _ in range(55):
            sx = self.player_x + random.uniform(-3, 3)
            sy = self.player_y + random.uniform(-3, 3)
            self.entities.append(PropEntity(sx, sy, 'charger'))
        self.add_log('error', '[PRESIDENT] 55 Chargers spawned — CRASH IMMINENT')
        self.trigger_crash('55 pink Dodge Chargers exceeded heap limit')

    def clear_all(self):
        for e in self.entities:
            e.alive = False
        self.add_log('admin', '[PRESIDENT] ent_remove_all — all entities purged')

    def dark_leader_override(self):
        for e in self.entities:
            if e.type == 'mcpd':
                e.stuck = True
                e.stuck_timer = -9999
        self.add_log('admin', '[DARK LEADER] Authority override — all MCPD frozen')

    def toggle_admin(self):
        self.admin_open = not self.admin_open
        pygame.mouse.set_visible(self.admin_open)
        pygame.event.set_grab(not self.admin_open)

    def trigger_loading(self, zone_name):
        self.is_loading = True
        self.loading_progress = 0
        self.loading_msg = f"Loading {zone_name}..."
        self.admin_open = False
        if getattr(self, 'game_state', 0) == getattr(self, 'STATE_PLAYING', 2):
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)
        else:
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)

    def trigger_crash(self, reason):
        self.is_crashed = True
        self.crash_progress = 0
        self.crash_reason = reason
        self.admin_open = False

    # ═══════════════════════════════════════════════
    #  3D OPENGL WORLD, FIRST-PERSON VIEWMODEL & RENDERER
    # ═══════════════════════════════════════════════
    def _compute_camera(self):
        """Computes First-Person, 3rd-Person Over-The-Shoulder, or 2026 AAA Cinematic Title Orbit camera."""
        if self.game_state == self.STATE_TITLE:
            orbit_angle = self.title_timer * 0.12
            cx = 20.5 if self.current_map == 'driving Test map' else (11.5 if self.current_map == 'MainCity2' else 15.5)
            cz = 23.5 if self.current_map == 'driving Test map' else (12.0 if self.current_map == 'MainCity2' else 15.5)
            radius = 16.0 if self.current_map == 'driving Test map' else (15.5 if self.current_map == 'MainCity2' else 18.5)
            eye_x = cx + math.cos(orbit_angle) * radius
            eye_z = cz + math.sin(orbit_angle) * radius
            eye_y = 3.8 + math.sin(self.title_timer * 0.08) * 0.6
            look_x = cx
            look_y = 1.9 + math.sin(self.title_timer * 0.05) * 0.4
            look_z = cz
            return eye_x, eye_y, eye_z, look_x, look_y, look_z

        # 3rd-Person Vehicle Chase Camera (Big City 5)
        if getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None):
            veh = self.active_vehicle
            cam_dist = 6.8
            cam_h = 2.4
            fwd_x = math.cos(veh.yaw)
            fwd_z = math.sin(veh.yaw)
            cos_p = math.cos(self.player_pitch)
            sin_p = math.sin(self.player_pitch)

            eye_x = veh.x - fwd_x * cam_dist * cos_p
            eye_y = max(0.4, veh.z + cam_h - sin_p * 2.2)
            eye_z = veh.y - fwd_z * cam_dist * cos_p

            look_x = veh.x + fwd_x * 4.0
            look_y = veh.z + 1.2
            look_z = veh.y + fwd_z * 4.0
            return eye_x, eye_y, eye_z, look_x, look_y, look_z

        fwd_x = math.cos(self.player_angle)
        fwd_z = math.sin(self.player_angle)
        right_x = -math.sin(self.player_angle)
        right_z = math.cos(self.player_angle)

        if self.camera_mode == 2:  # 1st Person (Default CoD / Half-Life 2 View)
            bob_amt = 0.032 if self.is_sprinting else (0.016 if self.is_moving else 0.003)
            bob_y = math.sin(self.walk_phase * 2.0) * bob_amt * (1.0 - self.ads_blend * 0.7)
            eye_x = self.player_x + fwd_x * 0.12
            eye_y = 0.88 + self.player_z + bob_y
            eye_z = self.player_y + fwd_z * 0.12
            cos_p = math.cos(self.player_pitch)
            sin_p = math.sin(self.player_pitch)
            look_x = eye_x + fwd_x * 10.0 * cos_p
            look_y = eye_y - sin_p * 10.0
            look_z = eye_z + fwd_z * 10.0 * cos_p
            return eye_x, eye_y, eye_z, look_x, look_y, look_z

        # 3rd Person Over-The-Shoulder Warfare Camera
        target_dist = 1.65 if self.aim_zoom else (2.45 if self.camera_mode == 0 else 3.8)
        shoulder_offset = 0.42 if self.aim_zoom else 0.35
        cam_height = 1.25 + math.sin(self.player_pitch) * 1.1

        origin_x = self.player_x + right_x * shoulder_offset
        origin_z = self.player_y + right_z * shoulder_offset
        actual_dist = target_dist
        steps = 16
        for i in range(1, steps + 1):
            d = (target_dist * i) / steps
            cx = origin_x - fwd_x * d
            cz = origin_z - fwd_z * d
            mx, my = int(cx), int(cz)
            if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
                actual_dist = max(0.4, d - 0.25)
                break
            if MAP[my][mx] not in (0, 7) and not (MAP[my][mx] == 6 and self.is_door_open(my, mx)):
                actual_dist = max(0.4, d - 0.25)
                break

        eye_x = origin_x - fwd_x * actual_dist
        eye_y = max(0.25, cam_height + self.player_z)
        eye_z = origin_z - fwd_z * actual_dist

        cos_p = math.cos(self.player_pitch)
        sin_p = math.sin(self.player_pitch)
        look_x = self.player_x + fwd_x * 8.0 * cos_p + right_x * (shoulder_offset * 0.4)
        look_y = (0.85 + self.player_z) - sin_p * 8.0
        look_z = self.player_y + fwd_z * 8.0 * cos_p + right_z * (shoulder_offset * 0.4)
        return eye_x, eye_y, eye_z, look_x, look_y, look_z

    def render_fp_viewmodel(self):
        """
        Renders the animated 3D First-Person Weapon & HEV/Tactical Hands viewmodel
        with Call of Duty + Half-Life 2 procedural animations:
        - Idle breathing sway & walking figure-8 bob
        - SHIFT + W Tactical Sprint: sweeps weapon diagonally across the chest with vigorous sprint bobbing
        - RMB Iron Sights (ADS): aligns rear/front 3D sights to the center of the screen
        - Recoil kickback, muzzle climb, animated slide/pump/energy core, and 3D muzzle flash
        """
        if self.camera_mode != 2 or getattr(self, 'in_vehicle', False):
            return

        gl.glClear(GL_DEPTH_BUFFER_BIT)
        gl.glEnable(GL_DEPTH_TEST)
        gl.glDisable(GL_FOG)

        gl.glMatrixMode(GL_PROJECTION)
        gl.glLoadIdentity()
        gl_perspective(55.0 - self.ads_blend * 12.0, SCREEN_W / float(SCREEN_H), 0.05, 10.0)

        gl.glMatrixMode(GL_MODELVIEW)
        gl.glLoadIdentity()

        wid = self.current_weapon
        sp = self.sprint_blend
        ads = self.ads_blend
        recoil = max(0.0, self.weapon_fired)
        sw_drop = max(0.0, self.weapon_switch_timer) * 0.45

        # Procedural figure-8 walk/sprint bob + idle breathing
        bob_freq = self.walk_phase
        bob_amp_x = (0.028 * sp + 0.012 * (1.0 - sp) * (1.0 if self.is_moving else 0.15)) * (1.0 - ads * 0.85)
        bob_amp_y = (0.032 * sp + 0.010 * (1.0 - sp) * (1.0 if self.is_moving else 0.15)) * (1.0 - ads * 0.85)
        bob_x = math.cos(bob_freq) * bob_amp_x
        bob_y = abs(math.sin(bob_freq)) * bob_amp_y + math.sin(self.sim_time * 2.2) * 0.003 * (1.0 - ads)

        # Interpolate between Hipfire, RMB Iron Sights (ADS center), and SHIFT+W Tactical Sprint
        # Lowered hipfire position clears screen center; ADS elevates iron sights directly to center
        hip_x, hip_y, hip_z = 0.20, -0.165, -0.45
        ads_x, ads_y, ads_z = 0.0, -0.088, -0.35
        spr_x, spr_y, spr_z = 0.05, -0.24, -0.42

        wx = hip_x * (1.0 - ads) + ads_x * ads
        wy = hip_y * (1.0 - ads) + ads_y * ads
        wz = hip_z * (1.0 - ads) + ads_z * ads

        # Multi-Phase Procedural Weapon Reload Animations & Arm Displacements
        reload_dip_y = 0.0
        reload_rot_x = 0.0
        reload_rot_y = 0.0
        reload_rot_z = 0.0
        left_arm_off_x = 0.0
        left_arm_off_y = 0.0
        left_arm_off_z = 0.0

        if self.is_reloading and self.reload_duration > 0:
            prog = min(1.0, max(0.0, self.reload_timer / self.reload_duration))
            if wid == 1:  # USP Match 9mm Pistol
                reload_dip_y = math.sin(prog * math.pi) * 0.06
                reload_rot_x = -math.sin(prog * math.pi) * 22.0
                reload_rot_z = math.sin(prog * math.pi) * 14.0
                if prog < 0.25:
                    p = prog / 0.25
                    left_arm_off_y = -0.22 * p
                    left_arm_off_x = -0.05 * p
                elif prog < 0.65:
                    p = (prog - 0.25) / 0.40
                    left_arm_off_y = -0.22 * (1.0 - p)
                    left_arm_off_x = -0.05 * (1.0 - p)
            elif wid == 2:  # SMG1 MP7
                reload_dip_y = math.sin(prog * math.pi) * 0.08
                reload_rot_x = -math.sin(prog * math.pi) * 16.0
                reload_rot_z = -math.sin(prog * math.pi) * 18.0
                if prog < 0.30:
                    left_arm_off_y = -0.24 * (prog / 0.30)
                elif prog < 0.70:
                    p = (prog - 0.30) / 0.40
                    left_arm_off_y = -0.24 * (1.0 - p)
                elif prog < 0.90:
                    left_arm_off_y = 0.04
                    left_arm_off_z = -0.08
            elif wid == 3:  # SPAS-12 Shotgun (loads single shell per 0.48s cycle)
                reload_rot_z = -math.sin(prog * math.pi) * 26.0
                reload_rot_x = -math.sin(prog * math.pi) * 10.0
                reload_dip_y = math.sin(prog * math.pi) * 0.035
                shell_p = min(1.0, prog / 0.72)
                left_arm_off_y = -0.14 * (1.0 - shell_p)
                left_arm_off_z = 0.03 * math.sin(prog * math.pi)
            elif wid == 4:  # AR2 Overwatch Pulse Rifle
                reload_rot_x = math.sin(prog * math.pi) * 15.0
                reload_dip_y = math.sin(prog * math.pi) * 0.10
                if prog < 0.35:
                    left_arm_off_y = -0.18 * (prog / 0.35)
                elif prog < 0.75:
                    p = (prog - 0.35) / 0.40
                    left_arm_off_y = -0.18 * (1.0 - p)
            elif wid == 5:  # .357 Magnum Revolver
                reload_rot_x = -math.sin(prog * math.pi) * 18.0
                reload_rot_z = math.sin(prog * math.pi) * 26.0
                reload_dip_y = math.sin(prog * math.pi) * 0.06
                p = math.sin(prog * math.pi)
                left_arm_off_x = -0.08 * p
                left_arm_off_y = -0.12 * p
            elif wid == 6:  # RPG Launcher
                reload_rot_x = -math.sin(prog * math.pi) * 24.0
                reload_dip_y = math.sin(prog * math.pi) * 0.08
                p = math.sin(prog * math.pi)
                left_arm_off_z = -0.16 * p
                left_arm_off_y = 0.06 * p

        # Dynamic Crowbar Melee Swing
        melee_rot_x = 0.0
        melee_rot_y = 0.0
        melee_rot_z = 0.0
        melee_off_x = 0.0
        if wid == 0 and recoil > 0.05:
            melee_rot_x = -recoil * 48.0
            melee_rot_y = -recoil * 24.0
            melee_rot_z = -recoil * 42.0
            melee_off_x = recoil * 0.08

        wx = wx * (1.0 - sp) + spr_x * sp + bob_x + melee_off_x
        wy = wy * (1.0 - sp) + spr_y * sp - bob_y - sw_drop - reload_dip_y
        wz = wz * (1.0 - sp) + spr_z * sp + recoil * 0.085 - reload_dip_y * 0.3

        gl.glPushMatrix()
        gl.glTranslatef(wx, wy, wz)

        # Sprint diagonal cross-chest rotation, reload tilt, and recoil climb
        gl.glRotatef(sp * 42.0 + reload_rot_z + melee_rot_z, 0.0, 1.0, 0.0)
        gl.glRotatef(-sp * 18.0 + recoil * 11.0 + reload_rot_x + melee_rot_x, 1.0, 0.0, 0.0)
        gl.glRotatef(-sp * 16.0 + math.sin(bob_freq) * sp * 6.0 + reload_rot_z + melee_rot_y, 0.0, 0.0, 1.0)

        # ── Genuine Valve Half-Life 2 3D Weapon .OBJ Models + Tactical Details ──
        wpn_dl = WEAPON_DLISTS.get(wid, 0)
        if wid == 0:  # Genuine Half-Life Crowbar (half-life_crowbar.glb)
            gl.glPushMatrix()
            gl.glRotatef(-35.0 * recoil, 1.0, 0.0, 0.0)
            gl.glRotatef(12.0, 0.0, 0.0, 1.0)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.04, 0.08, -0.05)
                gl.glRotatef(-35.0, 1.0, 0.0, 0.0)
                gl.glRotatef(-65.0, 0.0, 1.0, 0.0)
                gl.glRotatef(25.0, 0.0, 0.0, 1.0)
                gl.glScalef(0.12, 0.12, 0.12)
                gl.glColor4f(1.0, 1.0, 1.0, 1.0)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.038, 0.46, 0.038, 0.78, 0.14, 0.10)
                gl.glTranslatef(0.0, 0.24, -0.05)
                gl.glRotatef(35.0, 1.0, 0.0, 0.0)
                draw_box(0.042, 0.14, 0.045, 0.68, 0.72, 0.76)
            gl.glPopMatrix()

        elif wid == 1:  # USP Match 9mm Pistol (w_pistol.obj)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.01, -0.03 + recoil * 0.05)
                gl.glScalef(1.38, 1.38, 1.38)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.055, 0.065, 0.28, 0.20, 0.22, 0.25)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.045, recoil * 0.06)
                draw_box(0.058, 0.052, 0.29, 0.58, 0.62, 0.66)
                gl.glPopMatrix()
            # Glowing green tritium iron sight dots
            gl.glPushMatrix()
            gl.glTranslatef(-0.018, 0.088, 0.11 + recoil * 0.05)
            draw_box(0.008, 0.015, 0.012, 0.2, 1.0, 0.3)
            gl.glTranslatef(0.036, 0.0, 0.0)
            draw_box(0.008, 0.015, 0.012, 0.2, 1.0, 0.3)
            gl.glPopMatrix()
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.088, -0.19 + recoil * 0.05)
            draw_box(0.008, 0.018, 0.012, 0.2, 1.0, 0.3)
            gl.glPopMatrix()

        elif wid == 2:  # SMG1 MP7 Submachine Gun (w_smg1.obj)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.0, -0.055, -0.16 + recoil * 0.03)
                gl.glScalef(1.05, 1.05, 1.05)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.068, 0.095, 0.44, 0.22, 0.24, 0.28)

            # Elevated Tactical Reflex Optic & Glowing Red Laser Sight (Unblocked in First-Person View)
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.0, recoil * 0.03)

            # Riser mount clamp on receiver top rail
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.062, -0.16)
            draw_box(0.036, 0.016, 0.055, 0.14, 0.15, 0.18)
            gl.glPopMatrix()

            # Hollow optic aperture frame (left post, right post, top hood)
            gl.glPushMatrix()
            gl.glTranslatef(-0.024, 0.088, -0.16)
            draw_box(0.007, 0.040, 0.038, 0.16, 0.18, 0.20)
            gl.glPopMatrix()

            gl.glPushMatrix()
            gl.glTranslatef(0.024, 0.088, -0.16)
            draw_box(0.007, 0.040, 0.038, 0.16, 0.18, 0.20)
            gl.glPopMatrix()

            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.108, -0.16)
            draw_box(0.055, 0.007, 0.038, 0.16, 0.18, 0.20)
            gl.glPopMatrix()

            # Translucent reflex glass lens + bright red laser sight dot
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.088, -0.16)
            draw_box(0.041, 0.034, 0.004, 0.12, 0.60, 0.80, 0.45)
            # Center bright glowing red laser sight reticle (perfectly unblocked)
            draw_box(0.008, 0.008, 0.008, 1.0, 0.08, 0.05, 1.0)
            # Laser halo glow
            draw_box(0.016, 0.016, 0.003, 1.0, 0.25, 0.15, 0.70)
            gl.glPopMatrix()

            gl.glPopMatrix()

        elif wid == 3:  # SPAS-12 Combat Shotgun (w_shotgun.obj)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.01, -0.10)
                gl.glScalef(0.88, 0.88, 0.88)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.072, 0.095, 0.48, 0.22, 0.23, 0.26)
            # Animated pump-action forend (slides back and forth on fire recoil and pump-action rack)
            pump_anim = getattr(self, 'shotgun_pump_anim', 0.0)
            pump_rack_offset = math.sin((pump_anim / 0.32) * math.pi) * 0.12 if pump_anim > 0.0 else 0.0
            pump_z = -0.22 + math.sin(recoil * math.pi) * 0.07 + pump_rack_offset
            gl.glPushMatrix()
            gl.glTranslatef(0.0, -0.035, pump_z)
            draw_box(0.082, 0.058, 0.20, 0.14, 0.14, 0.16)
            gl.glPopMatrix()

            # Front brass bead sight (centered at y = 0.088 for ADS precision)
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.088, -0.42)
            draw_box(0.010, 0.016, 0.010, 0.95, 0.75, 0.20)
            gl.glPopMatrix()

            # Sequential single-shell reload animation: inserting shell into underside gate
            if self.is_reloading:
                prog = min(1.0, max(0.0, self.reload_timer / max(0.01, self.reload_duration)))
                shell_p = min(1.0, prog / 0.72)
                shell_y = -0.16 * (1.0 - shell_p) - 0.035
                shell_z = -0.18 + shell_p * 0.06
                gl.glPushMatrix()
                gl.glTranslatef(0.012, shell_y, shell_z)
                gl.glRotatef(-18.0 * (1.0 - shell_p), 1.0, 0.0, 0.0)
                # Red 12-gauge shell body
                draw_box(0.018, 0.018, 0.058, 0.88, 0.14, 0.12)
                # Brass rim / base
                gl.glTranslatef(0.0, 0.0, 0.032)
                draw_box(0.020, 0.020, 0.016, 0.92, 0.76, 0.20)
                gl.glPopMatrix()

        elif wid == 4:  # AR2 Overwatch Pulse Rifle (w_irifle.obj)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.01, -0.10)
                gl.glScalef(0.92, 0.92, 0.92)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.078, 0.11, 0.52, 0.16, 0.19, 0.26)
            # Animated glowing cyan dark-energy core chamber
            pulse = 0.75 + 0.25 * math.sin(self.sim_time * 12.0)
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.025, -0.06)
            draw_box(0.082, 0.055, 0.18, 0.15 * pulse, 0.78 * pulse, 1.0, 0.82)
            gl.glPopMatrix()
            # Holographic front sight blade
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.088, -0.26)
            draw_box(0.008, 0.022, 0.014, 0.2, 0.9, 1.0, 0.9)
            gl.glPopMatrix()

        elif wid == 5:  # .357 Magnum Revolver (w_357.obj)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.02, -0.05)
                gl.glScalef(1.34, 1.34, 1.34)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.052, 0.092, 0.28, 0.75, 0.78, 0.82)
            # Front orange sight blade
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.088, -0.28)
            draw_box(0.008, 0.018, 0.012, 1.0, 0.45, 0.1)
            gl.glPopMatrix()

        else:  # wid == 6: HL2 Laser-Guided RPG Launcher (w_rocket_launcher.obj)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.01, -0.08)
                gl.glScalef(0.82, 0.82, 0.82)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.095, 0.095, 0.72, 0.28, 0.33, 0.20)
            # Glowing red laser sight emitter dot on side
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.088, -0.28)
            draw_box(0.016, 0.016, 0.024, 1.0, 0.15, 0.12)
            gl.glPopMatrix()
            gl.glPushMatrix()
            gl.glTranslatef(-0.055, 0.045, -0.28)
            draw_box(0.016, 0.016, 0.024, 1.0, 0.15, 0.12)
            gl.glPopMatrix()

        # 3D Volumetric Muzzle Flash at barrel tip
        if recoil > 0.65 and wid != 0:
            gl.glPushMatrix()
            gl.glTranslatef(0.0, 0.02, -0.56)
            gl.glRotatef(random.uniform(0, 90), 0.0, 0.0, 1.0)
            m_col = (0.3, 0.85, 1.0) if wid == 4 else (1.0, 0.85, 0.25)
            draw_box(0.22, 0.22, 0.12, m_col[0], m_col[1], m_col[2], 0.9)
            draw_box(0.10, 0.10, 0.28, 1.0, 1.0, 1.0, 1.0)
            gl.glPopMatrix()

        gl.glPopMatrix()

        # Render spinning 3D ejected brass shell casings in viewmodel space
        for sc in self.shell_casings:
            gl.glPushMatrix()
            gl.glTranslatef(sc[0], sc[1], sc[2])
            gl.glRotatef(sc[6] * 720.0, 1.0, 1.0, 0.0)
            draw_box(0.014, 0.014, 0.036, 0.92, 0.75, 0.22)
            gl.glPopMatrix()

    def render_3d_scene(self):
        gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        gl.glEnable(GL_DEPTH_TEST)
        gl.glDepthMask(GL_TRUE)
        gl.glDisable(GL_LIGHTING)
        gl.glDisable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(GL_TEXTURE_2D)
        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        if self.fog_enabled:
            gl.glEnable(GL_FOG)
        else:
            gl.glDisable(GL_FOG)

        max_draw_dist = self.get_chunk_draw_distance()
        z_far = max(28.0, max_draw_dist + 18.0)

        # Projection Matrix with smooth Sprint & ADS FOV interpolation
        gl.glMatrixMode(GL_PROJECTION)
        gl.glLoadIdentity()
        gl_perspective(self.current_fov, SCREEN_W / float(SCREEN_H), 0.12, z_far)

        # ModelView Matrix
        gl.glMatrixMode(GL_MODELVIEW)
        gl.glLoadIdentity()
        eye_x, eye_y, eye_z, look_x, look_y, look_z = self._compute_camera()
        if self.screen_shake > 0:
            eye_x += random.uniform(-0.07, 0.07) * self.screen_shake
            eye_y += random.uniform(-0.07, 0.07) * self.screen_shake
        gl_look_at(eye_x, eye_y, eye_z, look_x, look_y, look_z, 0.0, 1.0, 0.0)

        # 1. Anti-Lag Spatial Chunk Culling: Only draw 8x8 city sectors within active draw distance!
        ref_x = self.player_x if self.game_state != self.STATE_TITLE else (20.5 if self.current_map == 'driving Test map' else (11.5 if self.current_map == 'MainCity2' else 15.5))
        ref_z = self.player_y if self.game_state != self.STATE_TITLE else (23.5 if self.current_map == 'driving Test map' else (12.0 if self.current_map == 'MainCity2' else 15.5))
        chunk_cull_sq = (max_draw_dist + 8.5) ** 2
        for (cx, cz), dl in self.chunk_dlists.items():
            center_x = cx * 8.0 + 4.0
            center_z = cz * 8.0 + 4.0
            if (center_x - ref_x) ** 2 + (center_z - ref_z) ** 2 <= chunk_cull_sq:
                gl.glCallList(dl)

        if self.landmarks_dlist:
            gl.glCallList(self.landmarks_dlist)

        # ── MAIN MENU BACKGROUND PREVIEW COPY (EMPTY MAP LAYOUT — NO ENEMIES, NO PROPS, NO PICKUPS) ──
        if self.game_state == self.STATE_TITLE:
            if self.current_map in ("MainCity2", "gm_bigcity"):
                bx_d, bz_d = (39.5, 12.0) if self.current_map == "MainCity2" else (7.0, 4.0)
                if getattr(self, 'destroyed_building_dlist', 0):
                    gl.glPushMatrix()
                    gl.glTranslatef(bx_d, 0.03, bz_d)
                    draw_box(13.8, 0.06, 8.2, 0.28, 0.26, 0.24)
                    gl.glPopMatrix()
                    gl.glPushMatrix()
                    gl.glTranslatef(bx_d, 0.005, bz_d)
                    gl.glScalef(0.10, 0.20, 0.10)
                    gl.glCallList(self.destroyed_building_dlist)
                    gl.glPopMatrix()
                bx_i, bz_i = (41.5, 22.0) if self.current_map == "MainCity2" else (7.0, 13.5)
                if getattr(self, 'industrial_utility_dlist', 0):
                    gl.glPushMatrix()
                    gl.glTranslatef(bx_i, 0.04, bz_i)
                    draw_box(10.5, 0.08, 10.5, 0.35, 0.34, 0.32)
                    gl.glPopMatrix()
                    gl.glPushMatrix()
                    gl.glTranslatef(bx_i, 0.005, bz_i)
                    gl.glScalef(0.32, 0.32, 0.32)
                    gl.glCallList(self.industrial_utility_dlist)
                    gl.glPopMatrix()
            elif self.current_map in ("BigCity5", "driving Test map"):
                if not getattr(self, 'city_infra_dlist', 0):
                    self.city_infra_dlist = load_glb_to_display_list("city_infrastructure_map_3.glb")
                if self.city_infra_dlist:
                    gl.glPushMatrix()
                    gl.glTranslatef(439.0, 1.3, 269.0)
                    gl.glCallList(self.city_infra_dlist)
                    gl.glPopMatrix()
                self._render_offroad_dirt_zones(max_draw_dist)
                if self.current_map == "BigCity5":
                    self._render_bigcity5_proper_city_buildings(max_draw_dist)
            self._render_source_water()
            gl.glDisable(GL_BLEND)
            gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            gl.glEnable(GL_TEXTURE_2D)
            return

        # 1b. Draw Battlefield Fire & Rising Dark Smoke Columns (Skipped in Potato PC Graphics for max FPS)
        if self.graphics_preset != "Potato PC Graphics":
            for sx, sz in self.smoke_columns:
                if abs(sx - self.player_x) > max_draw_dist or abs(sz - self.player_y) > max_draw_dist:
                    continue
                flicker = 0.8 + 0.25 * math.sin(self.sim_time * 18.0 + sx)
                gl.glPushMatrix()
                gl.glTranslatef(sx, 0.25 * flicker, sz)
                draw_box(0.45 * flicker, 0.45 * flicker, 0.45 * flicker, 1.0, 0.45, 0.05, 0.85)
                gl.glPopMatrix()
                puff_count = 5 if self.graphics_preset == "Alter Heavy Graphics" else 3
                for puff_i in range(puff_count):
                    py = ((self.sim_time * 1.4 + puff_i * 1.1) % 5.5)
                    pscale = 0.45 + py * 0.32
                    alpha = max(0.05, 0.45 - py * 0.07)
                    gl.glPushMatrix()
                    gl.glTranslatef(sx + math.sin(self.sim_time + puff_i) * 0.25, 0.6 + py, sz + math.cos(self.sim_time + puff_i) * 0.25)
                    draw_box(pscale, pscale, pscale, 0.14, 0.14, 0.15, alpha)
                    gl.glPopMatrix()

        # 2. Draw Interactive 3D Doors (using genuine Half-Life 2 Metal Door texture)
        tex_door = self.world_textures.get('hl2_metal_door', self.world_textures['combine_bunker'])
        for (dy, dx), door in self.doors.items():
            if abs(dx - self.player_x) > max_draw_dist or abs(dy - self.player_y) > max_draw_dist:
                continue
            open_amt = door['open']
            if open_amt < 0.98:
                gl.glPushMatrix()
                gl.glTranslatef(dx + 0.5, 1.3 + open_amt * 2.3, dy + 0.5)
                draw_textured_box(0.96, 2.6, 0.28, tex_door, u_rep=1.0, v_rep=1.0)
                draw_box(0.98, 0.18, 0.30, 0.9, 0.65, 0.1)
                gl.glPopMatrix()

        # 2b. Draw All Placed 3D Half-Life 2 Resources (Fences, Checkpoints, Combine Barriers, Entry Lights, Sandbags, Breencast) & Editor 3D Preview
        self._render_placed_3d_objects_and_editor_preview(max_draw_dist)

        # 2c. Draw Physical 3D TBMG Unregulated Arms Shop Kiosk
        shop_x, shop_y = self.get_arms_shop_location()
        if abs(shop_x - self.player_x) <= max_draw_dist and abs(shop_y - self.player_y) <= max_draw_dist:
            self._render_3d_arms_shop_kiosk(shop_x, shop_y)

        # 2d. Draw Fused Multi-Map MainCity2 Landmarks, Ravenholm Hazards, 3D GLB Buildings & Highway/Vehicles
        if self.current_map == "MainCity2":
            self._render_ravenholm_hazards(max_draw_dist)
            # Fused 3D Destroyed High-Rise Apartment Block in Northeast Sector (39.5, 12.0)
            if getattr(self, 'destroyed_building_dlist', 0) and abs(39.5 - self.player_x) <= max_draw_dist + 14.0 and abs(12.0 - self.player_y) <= max_draw_dist + 14.0:
                gl.glPushMatrix()
                gl.glTranslatef(39.5, 0.03, 12.0)
                draw_box(13.8, 0.06, 8.2, 0.28, 0.26, 0.24)
                gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(39.5, 0.005, 12.0)
                gl.glScalef(0.10, 0.20, 0.10)
                gl.glCallList(self.destroyed_building_dlist)
                gl.glPopMatrix()
            # Fused 3D Industrial Utility Substation in East Sector (41.5, 22.0)
            if getattr(self, 'industrial_utility_dlist', 0) and abs(41.5 - self.player_x) <= max_draw_dist + 10.0 and abs(22.0 - self.player_y) <= max_draw_dist + 10.0:
                gl.glPushMatrix()
                gl.glTranslatef(41.5, 0.04, 22.0)
                draw_box(10.5, 0.08, 10.5, 0.35, 0.34, 0.32)
                gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(41.5, 0.005, 22.0)
                gl.glRotatef(0.0, 0.0, 1.0, 0.0)
                gl.glScalef(0.32, 0.32, 0.32)
                gl.glCallList(self.industrial_utility_dlist)
                gl.glPopMatrix()
            # Connected South Highway District: 3D Car Spawner Kiosk at (15.2, 31.0) & Parking Bay at (18.5, 31.0)
            if abs(16.5 - self.player_x) <= max_draw_dist + 10.0 and abs(31.0 - self.player_y) <= max_draw_dist + 10.0:
                self._render_3d_car_spawner_kiosk(15.2, 31.0, bay_x=18.5, bay_y=31.0)
            # 3D Traffic Light Gantries & Regulatory Speed/Stop Signs along South Highway
            sim_t = getattr(self, 'sim_time', 0.0) % 30.0
            ew_st = 'GREEN' if sim_t < 13.0 else ('YELLOW' if sim_t < 16.0 else 'RED')
            ns_st = 'RED' if sim_t < 16.0 else ('GREEN' if sim_t < 27.0 else 'YELLOW')
            for gx_pos in (13.5, 26.5):
                if abs(gx_pos - self.player_x) <= max_draw_dist + 18.0 and abs(28.0 - self.player_y) <= max_draw_dist + 18.0:
                    draw_3d_traffic_light_gantry(gx_pos - 3.5, 30.2, -90.0, state_ew=ew_st, state_ns=ns_st)
                    draw_3d_traffic_light_gantry(gx_pos + 3.5, 25.2, 90.0, state_ew=ew_st, state_ns=ns_st)
            for sx_s, sy_s, syaw_s, stype_s, sval_s in (
                (11.0, 30.5, 270.0, "speed", 200),
                (21.5, 30.5, 270.0, "speed", 60),
                (11.0, 24.8, 180.0, "stop", 0),
                (22.0, 24.8, 180.0, "stop", 0),
            ):
                if abs(sx_s - self.player_x) <= max_draw_dist + 14.0 and abs(sy_s - self.player_y) <= max_draw_dist + 14.0:
                    if stype_s == "speed":
                        draw_3d_speed_sign(sx_s, 0.0, sy_s, syaw_s, sval_s)
                    else:
                        draw_3d_stop_sign(sx_s, 0.0, sy_s, syaw_s)
            # Render all active Drivable Vehicles in MainCity2
            self._render_vehicles(max_draw_dist)
        elif self.current_map == "gm_bigcity":
            # 2e. Draw 3D Industrial Utility Building & Substation Complex (gm_bigcity)
            if getattr(self, 'industrial_utility_dlist', 0) and abs(7.0 - self.player_x) <= max_draw_dist + 8.0 and abs(13.5 - self.player_y) <= max_draw_dist + 8.0:
                # Beveled Concrete foundation plinth resting directly on ground (eliminates hovering)
                gl.glPushMatrix()
                gl.glTranslatef(7.0, 0.04, 13.5)
                draw_box(12.3, 0.08, 12.3, 0.35, 0.34, 0.32)
                gl.glPopMatrix()

                # Render 3D Model sitting flush on foundation plinth
                gl.glPushMatrix()
                gl.glTranslatef(7.0, 0.005, 13.5)
                gl.glRotatef(180.0, 0.0, 1.0, 0.0)  # Face East towards avenue & grand canal
                gl.glScalef(0.36, 0.36, 0.36)
                gl.glCallList(self.industrial_utility_dlist)
                gl.glPopMatrix()

            # 2f. Draw 3D Destroyed High-Rise Apartment Block (gm_bigcity)
            if getattr(self, 'destroyed_building_dlist', 0) and abs(7.0 - self.player_x) <= max_draw_dist + 12.0 and abs(4.0 - self.player_y) <= max_draw_dist + 12.0:
                # Beveled Concrete & Rubble foundation plinth (rests directly on ground at Y=0.03, eliminates hovering)
                gl.glPushMatrix()
                gl.glTranslatef(7.0, 0.03, 4.0)
                draw_box(13.8, 0.06, 8.2, 0.28, 0.26, 0.24)
                gl.glPopMatrix()

                # Render 3D Model sitting flush on ground/rubble foundation
                gl.glPushMatrix()
                gl.glTranslatef(7.0, 0.005, 4.0)
                gl.glScalef(0.10, 0.20, 0.10)
                gl.glCallList(self.destroyed_building_dlist)
                gl.glPopMatrix()
        elif self.current_map == "BigCity5":
            self._render_bigcity5_scene(max_draw_dist)
        elif self.current_map == "driving Test map":
            self._render_driving_test_scene(max_draw_dist)

        # 3. Draw 3D Player Character (when in 3rd-person modes and NOT in vehicle)
        if self.camera_mode != 2 and not getattr(self, 'in_vehicle', False):
            gl.glPushMatrix()
            gl.glTranslatef(0.0, self.player_z, 0.0)
            draw_3d_humanoid(
                self.player_x, self.player_y, self.player_angle,
                'player', self.sim_time, self.is_moving,
                self.weapon_fired > 0.5, self.damage_flash > 0.1,
                weapon_id=self.current_weapon
            )
            gl.glPopMatrix()

        # 4. Draw 3D Corpses
        for c in self.corpses:
            if abs(c['x'] - self.player_x) > max_draw_dist or abs(c['y'] - self.player_y) > max_draw_dist:
                continue
            gl.glPushMatrix()
            gl.glTranslatef(c['x'], 0.08, c['y'])
            gl.glRotatef(math.degrees(c.get('yaw', 0.0)), 0, 1, 0)
            draw_box(0.45, 0.14, 0.85, 0.45, 0.08, 0.08)
            gl.glPopMatrix()

        # 5. Draw 3D Pickups (Genuine Half-Life 2 Medkits, HEV Batteries & Ammo Boxes) & 3D Weapon Pickups
        spin_deg = (self.sim_time * 90.0) % 360.0
        for p in self.pickups:
            if not p.alive:
                continue
            if abs(p.x - self.player_x) > max_draw_dist or abs(p.y - self.player_y) > max_draw_dist:
                continue
            pdef = PICKUP_DEFS.get(p.type, PICKUP_DEFS['health_small'])
            col = pdef['color']
            bob_y = 0.28 + math.sin(p.bob_timer) * 0.08
            gl.glPushMatrix()
            gl.glTranslatef(p.x, bob_y, p.y)
            gl.glRotatef(spin_deg, 0, 1, 0)
            if p.type in ('health', 'health_small', 'health_large'):
                t_hk = self.world_textures.get('hl2_healthkit', 0)
                sz = 0.44 if p.type == 'health_large' else 0.36
                if t_hk:
                    draw_textured_box(sz * 1.25, sz * 0.72, sz, t_hk, u_rep=1.0, v_rep=1.0, r=1.0, g=1.0, b=1.0)
                else:
                    draw_box(0.32, 0.32, 0.32, col[0], col[1], col[2])
            elif p.type in ('armor', 'armor_small', 'armor_large'):
                t_bat = self.world_textures.get('hl2_hev_battery', 0)
                sz = 0.40 if p.type == 'armor_large' else 0.34
                if t_bat:
                    draw_textured_box(sz * 0.75, sz * 1.15, sz * 0.55, t_bat, u_rep=1.0, v_rep=1.0, r=0.95, g=0.98, b=1.0)
                else:
                    draw_box(0.32, 0.32, 0.32, col[0], col[1], col[2])
            elif p.type in ('shells', 'ammo_shells'):
                t_sh = self.world_textures.get('hl2_ammo_buckshot', 0)
                if t_sh:
                    draw_textured_box(0.36, 0.24, 0.28, t_sh, u_rep=1.0, v_rep=1.0, r=1.0, g=0.95, b=0.95)
                else:
                    draw_box(0.32, 0.32, 0.32, col[0], col[1], col[2])
            elif p.type in ('bullets', 'ammo_bullets'):
                t_bul = self.world_textures.get('hl2_ammo_smg1', 0) or self.world_textures.get('hl2_ammo_pistol', 0)
                if t_bul:
                    draw_textured_box(0.38, 0.26, 0.30, t_bul, u_rep=1.0, v_rep=1.0, r=0.98, g=0.96, b=0.92)
                else:
                    draw_box(0.32, 0.32, 0.32, col[0], col[1], col[2])
            elif p.type in ('rockets', 'ammo_rockets'):
                t_rk = self.world_textures.get('hl2_ammocrate_rockets', 0)
                if t_rk:
                    draw_textured_box(0.46, 0.30, 0.34, t_rk, u_rep=1.0, v_rep=1.0, r=0.96, g=0.98, b=0.94)
                else:
                    draw_box(0.32, 0.32, 0.32, col[0], col[1], col[2])
            else:
                t_ce = self.world_textures.get('hl2_car_battery', 0) or self.world_textures.get('hl2_ammocrate_smg1', 0)
                if t_ce:
                    draw_textured_box(0.38, 0.30, 0.30, t_ce, u_rep=1.0, v_rep=1.0, r=0.95, g=0.98, b=1.0)
                else:
                    draw_box(0.32, 0.32, 0.32, col[0], col[1], col[2])
            gl.glPopMatrix()

        for i, (wx, wy, wid, _) in enumerate(self.weapon_pickup_positions):
            if not self.weapon_pickups_alive[i]:
                continue
            col = WEAPONS[wid]['color']
            gl.glPushMatrix()
            gl.glTranslatef(wx, 0.38 + math.sin(self.sim_time * 3 + i) * 0.08, wy)
            gl.glRotatef(spin_deg, 0, 1, 0)
            wpn_dl = WEAPON_DLISTS.get(wid, 0)
            if wpn_dl:
                gl.glPushMatrix()
                gl.glScalef(1.15, 1.15, 1.15)
                gl.glCallList(wpn_dl)
                gl.glPopMatrix()
            else:
                draw_box(0.55, 0.22, 0.25, col[0] / 255.0, col[1] / 255.0, col[2] / 255.0)
            gl.glPopMatrix()

        # 6. Draw All 3D NPCs, Monsters, Vehicles & Floating Source Engine Physics Props
        ent_cull_sq = (max_draw_dist + 4.0) ** 2
        tex_crate = self.world_textures.get('wood_crate')
        for e in self.entities:
            if not e.alive:
                continue
            dist_sq = (e.x - self.player_x) ** 2 + (e.y - self.player_y) ** 2
            if dist_sq > ent_cull_sq:
                continue

            moving = (e.vx * e.vx + e.vy * e.vy) > 0.05
            pain = (e.ai_state == AI_PAIN)
            firing = getattr(e, 'attack_flash', 0) > 0.2
            ez = getattr(e, 'z', 0.0)

            if e.type in ('charger', 'barrel', 'crate', 'explosive_barrel'):
                draw_3d_source_prop(e.x, ez, e.y, e.facing_yaw, e.type, tex_crate)
            elif e.type == 'pillow':
                gl.glPushMatrix()
                gl.glTranslatef(e.x, 0.35 + ez, e.y)
                gl.glRotatef(math.degrees(e.facing_yaw), 0, 1, 0)
                draw_box(0.35, 0.65, 0.18, 1.0, 0.72, 0.95)
                gl.glPopMatrix()
            elif e.type == 'demon':
                gl.glPushMatrix()
                gl.glTranslatef(0.0, ez, 0.0)
                draw_3d_demon(e.x, e.y, e.facing_yaw, e.age, pain)
                gl.glPopMatrix()
            else:
                w_type = getattr(e, 'weapon_type', 'stunstick')
                w_drawn = getattr(e, 'weapon_drawn', True)
                m_timer = getattr(e, 'melee_timer', 0.0)
                is_m = (m_timer > 0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, ez, 0.0)
                draw_3d_humanoid(
                    e.x, e.y, e.facing_yaw, e.type, e.age, moving, firing, pain,
                    weapon_type=w_type, weapon_drawn=w_drawn, is_melee=is_m, melee_timer=m_timer
                )
                gl.glPopMatrix()

            if e.health < e.max_health:
                hp_pct = max(0.0, e.health / float(e.max_health))
                gl.glPushMatrix()
                gl.glTranslatef(e.x, 1.32 + ez, e.y)
                gl.glRotatef(90.0 - math.degrees(self.player_angle), 0, 1, 0)
                draw_box(0.52, 0.06, 0.02, 0.1, 0.1, 0.1)
                gl.glTranslatef(-(1.0 - hp_pct) * 0.25, 0.0, 0.01)
                draw_box(0.50 * hp_pct, 0.045, 0.03, 1.0 - hp_pct, hp_pct, 0.15)
                gl.glPopMatrix()

        # 7. Draw 3D Projectiles
        for p in self.projectiles:
            if not p.alive:
                continue
            gl.glPushMatrix()
            gl.glTranslatef(p.x, 0.68, p.y)
            gl.glRotatef((self.sim_time * 360.0) % 360.0, 1, 1, 0)
            ptype = getattr(p, 'proj_type', 'combine')
            if ptype == 'bfg':
                draw_box(0.45, 0.45, 0.45, 0.2, 1.0, 0.3, 0.85)
                draw_box(0.25, 0.25, 0.25, 0.85, 1.0, 0.85, 1.0)
            elif ptype == 'rocket':
                draw_box(0.22, 0.22, 0.45, 0.85, 0.35, 0.15, 1.0)
                draw_box(0.16, 0.16, 0.16, 1.0, 0.8, 0.2, 1.0)
            elif ptype == 'fireball':
                draw_box(0.24, 0.24, 0.24, 1.0, 0.45, 0.05, 0.9)
            else:
                draw_box(0.28, 0.28, 0.28, 1.0, 0.85, 0.2, 0.9)
                draw_box(0.16, 0.16, 0.16, 1.0, 1.0, 1.0, 1.0)
            gl.glPopMatrix()

        # 8. Draw 3D Bullet Tracers
        if self.tracers:
            gl.glLineWidth(2.5)
            gl.glBegin(GL_LINES)
            for tr in self.tracers:
                x1, y1, z1, x2, y2, z2, col, life = tr
                gl.glColor4f(col[0], col[1], col[2], min(1.0, life * 8.0))
                gl.glVertex3f(x1, y1, z1)
                gl.glVertex3f(x2, y2, z2)
            gl.glEnd()

        # 8b. Draw Persistent 3D Bullet Impact Wall Decals (Up to 500+ rounds with FIFO recycling)
        self._render_bullet_decals(max_draw_dist)

        # 9. Draw 3D Volumetric Explosions & Debris
        for ex in self.explosions_list:
            if not ex.alive:
                continue
            scale = (1.1 - ex.life) * 2.6 + 0.3
            gl.glPushMatrix()
            gl.glTranslatef(ex.x, 0.65, ex.y)
            gl.glRotatef(ex.life * 180.0, 1, 1, 0)
            draw_box(scale, scale, scale, 1.0, 0.45, 0.05, ex.life * 0.75)
            draw_box(scale * 0.6, scale * 0.6, scale * 0.6, 1.0, 0.9, 0.3, ex.life)
            gl.glPopMatrix()
            for p in ex.debris:
                gl.glPushMatrix()
                gl.glTranslatef(ex.x + p[0], p[1], ex.y + p[2])
                draw_box(0.12, 0.12, 0.12, 1.0, 0.6, 0.1, ex.life)
                gl.glPopMatrix()

        # 9b. Draw Animated Translucent Source Engine Water Canals & Basins (cell == 7)
        self._render_source_water()

        # 10. Draw Animated First-Person 3D Weapon Viewmodel on top
        if self.game_state != self.STATE_TITLE:
            self.render_fp_viewmodel()

        gl.glDisable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(GL_TEXTURE_2D)

    def _render_placed_3d_objects_and_editor_preview(self, max_draw_dist):
        """Renders all placed 3D Half-Life 2 objects, stairs, catwalks, props, and live 3D Map Editor cursor & selection box."""
        tex_fence = self.world_textures.get('chainlink_fence')
        tex_barricade = self.world_textures.get('combine_barricade')
        tex_light = self.world_textures.get('entry_light')
        tex_sandbag = self.world_textures.get('sandbag')
        tex_breen = self.world_textures.get('breencast_screen')
        tex_crate = self.world_textures.get('wood_crate')
        cull_sq = (max_draw_dist + 5.0) ** 2

        def _draw_static_hl2_obj(otype, ox, oy, oyaw, oz=0.0):
            # ── 1. Original Classic Props ──
            if otype == "fence":
                gl.glPushMatrix(); gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_chainlink_checkpoint(ox, oy, oyaw, tex_fence, has_gate=False)
                gl.glPopMatrix()
            elif otype == "checkpoint_gate":
                gl.glPushMatrix(); gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_chainlink_checkpoint(ox, oy, oyaw, tex_fence, has_gate=True)
                gl.glPopMatrix()
            elif otype == "combine_barrier":
                gl.glPushMatrix(); gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_combine_barricade(ox, oy, oyaw, tex_barricade)
                gl.glPopMatrix()
            elif otype == "entry_light":
                gl.glPushMatrix(); gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_entry_light(ox, oy, oyaw, tex_light, self.sim_time)
                gl.glPopMatrix()
            elif otype == "sandbag":
                gl.glPushMatrix(); gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_sandbag_bunker(ox, oy, oyaw, tex_sandbag)
                gl.glPopMatrix()
            elif otype == "hedgehog":
                gl.glPushMatrix(); gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_czech_hedgehog(ox, oy, oyaw)
                gl.glPopMatrix()
            elif otype == "breencast":
                draw_3d_breencast_screen(ox, oz + 2.8, oy, oyaw, tex_breen)

            # ── 2. Walkable Stairs & Vertical Structures ──
            elif otype == "stairs_metal":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for step_i in range(12):
                    sy = (step_i + 0.5) * (2.8 / 12.0)
                    sz = -1.6 + (step_i + 0.5) * (3.2 / 12.0)
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, sy + 0.10, sz)
                    draw_box(1.5, 0.05, 0.28, 0.36, 0.40, 0.45)
                    gl.glTranslatef(0.0, 0.02, -0.12)
                    draw_box(1.5, 0.02, 0.04, 0.95, 0.80, 0.10)
                    gl.glTranslatef(0.0, -(2.8 / 24.0), 0.12)
                    draw_box(1.5, 2.8 / 12.0, 0.04, 0.22, 0.25, 0.28)
                    gl.glPopMatrix()
                for side_x in (-0.78, 0.78):
                    for p_i in (0, 4, 8, 11):
                        py = (p_i + 1) * (2.8 / 12.0)
                        pz_val = -1.6 + (p_i + 0.5) * (3.2 / 12.0)
                        gl.glPushMatrix()
                        gl.glTranslatef(side_x, py + 0.45, pz_val)
                        draw_box(0.05, 0.90, 0.05, 0.30, 0.32, 0.36)
                        gl.glPopMatrix()
                    gl.glPushMatrix()
                    gl.glTranslatef(side_x, 1.4 + 0.90, 0.0)
                    gl.glRotatef(-40.0, 1.0, 0.0, 0.0)
                    draw_box(0.05, 0.05, 4.2, 0.92, 0.76, 0.15)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "stairs_wood":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for step_i in range(12):
                    sy = (step_i + 0.5) * (2.8 / 12.0)
                    sz = -1.6 + (step_i + 0.5) * (3.2 / 12.0)
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, sy + 0.10, sz)
                    draw_box(1.5, 0.06, 0.30, 0.56, 0.38, 0.22)
                    gl.glTranslatef(0.0, -(2.8 / 24.0), 0.13)
                    draw_box(1.5, 2.8 / 12.0, 0.04, 0.42, 0.28, 0.16)
                    gl.glPopMatrix()
                for side_x in (-0.78, 0.78):
                    for p_i in (0, 3, 6, 9, 11):
                        py = (p_i + 1) * (2.8 / 12.0)
                        pz_val = -1.6 + (p_i + 0.5) * (3.2 / 12.0)
                        gl.glPushMatrix()
                        gl.glTranslatef(side_x, py + 0.45, pz_val)
                        draw_box(0.06, 0.90, 0.06, 0.48, 0.32, 0.18)
                        gl.glPopMatrix()
                    gl.glPushMatrix()
                    gl.glTranslatef(side_x, 1.4 + 0.90, 0.0)
                    gl.glRotatef(-40.0, 1.0, 0.0, 0.0)
                    draw_box(0.08, 0.08, 4.2, 0.58, 0.40, 0.24)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "metal_ramp":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.4, 0.0)
                gl.glRotatef(-39.0, 1.0, 0.0, 0.0)
                draw_box(1.7, 0.08, 4.3, 0.32, 0.35, 0.38)
                for bx in (-0.86, 0.86):
                    gl.glPushMatrix()
                    gl.glTranslatef(bx, 0.04, 0.0)
                    draw_box(0.06, 0.09, 4.3, 0.95, 0.80, 0.10)
                    gl.glPopMatrix()
                gl.glPopMatrix()
                for sx in (-0.88, 0.88):
                    for pz_pos, py_pos in ((-1.6, 0.45), (-0.5, 1.35), (0.6, 2.25), (1.6, 3.25)):
                        gl.glPushMatrix()
                        gl.glTranslatef(sx, py_pos, pz_pos)
                        draw_box(0.06, 0.90, 0.06, 0.28, 0.30, 0.34)
                        gl.glPopMatrix()
                    gl.glPushMatrix()
                    gl.glTranslatef(sx, 1.4 + 0.90, 0.0)
                    gl.glRotatef(-39.0, 1.0, 0.0, 0.0)
                    draw_box(0.05, 0.05, 4.4, 0.95, 0.80, 0.10)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "second_story_floor":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for cx, cz in ((-1.5, -1.5), (1.5, -1.5), (-1.5, 1.5), (1.5, 1.5)):
                    gl.glPushMatrix()
                    gl.glTranslatef(cx, 1.4, cz)
                    draw_box(0.18, 2.8, 0.18, 0.24, 0.26, 0.30)
                    gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 2.72, 0.0)
                draw_box(3.2, 0.14, 0.14, 0.28, 0.30, 0.34)
                draw_box(0.14, 0.14, 3.2, 0.28, 0.30, 0.34)
                gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 2.84, 0.0)
                draw_box(3.2, 0.08, 3.2, 0.42, 0.44, 0.48)
                gl.glPopMatrix()
                for rx, rz, rw, rd in ((0.0, -1.55, 3.2, 0.06), (0.0, 1.55, 3.2, 0.06), (-1.55, 0.0, 0.06, 3.2), (1.55, 0.0, 0.06, 3.2)):
                    gl.glPushMatrix()
                    gl.glTranslatef(rx, 2.8 + 0.48, rz)
                    draw_box(rw, 0.05, rd, 0.90, 0.75, 0.15)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "roof_walkway":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for cx, cz in ((-0.75, -1.5), (0.75, -1.5), (-0.75, 1.5), (0.75, 1.5)):
                    gl.glPushMatrix()
                    gl.glTranslatef(cx, 1.4, cz)
                    draw_box(0.14, 2.8, 0.14, 0.22, 0.24, 0.28)
                    gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 2.84, 0.0)
                draw_box(1.6, 0.08, 3.2, 0.38, 0.40, 0.44)
                gl.glPopMatrix()
                for sx in (-0.76, 0.76):
                    gl.glPushMatrix()
                    gl.glTranslatef(sx, 2.8 + 0.48, 0.0)
                    draw_box(0.06, 0.05, 3.2, 0.90, 0.75, 0.15)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "scaffolding":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for cx in (-1.2, 1.2):
                    for cz in (-1.2, 1.2):
                        gl.glPushMatrix()
                        gl.glTranslatef(cx, 1.6, cz)
                        draw_box(0.08, 3.2, 0.08, 0.50, 0.53, 0.56)
                        gl.glPopMatrix()
                for py in (1.4, 2.8):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, py, 0.0)
                    draw_box(2.4, 0.06, 2.4, 0.58, 0.42, 0.26)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "ladder":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for rx in (-0.26, 0.26):
                    gl.glPushMatrix()
                    gl.glTranslatef(rx, 1.6, 0.0)
                    draw_box(0.05, 3.2, 0.05, 0.35, 0.38, 0.42)
                    gl.glPopMatrix()
                for rung_i in range(10):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, 0.3 + rung_i * 0.3, 0.0)
                    draw_box(0.52, 0.04, 0.04, 0.90, 0.75, 0.15)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            # ── 3. Fortifications & Barriers ──
            elif otype == "tall_combine_wall":
                t_cwall = self.world_textures.get('combine_barricade_tall', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 2.0, 0.0)
                if t_cwall:
                    draw_textured_box(2.8, 4.0, 0.55, t_cwall, u_rep=1.0, v_rep=1.0, r=0.88, g=0.92, b=0.98)
                else:
                    draw_box(2.8, 4.0, 0.55, 0.18, 0.22, 0.28)
                gl.glTranslatef(0.0, 0.0, 0.29)
                draw_box(2.6, 0.12, 0.04, 0.18, 0.85, 1.0)
                draw_box(0.12, 3.8, 0.04, 0.18, 0.85, 1.0)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "concrete_jersey":
                t_wbar = self.world_textures.get('hl2_wasteland_barricade', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.18, 0.0)
                if t_wbar:
                    draw_textured_box(2.2, 0.36, 0.60, t_wbar, u_rep=1.0, v_rep=0.5, r=0.92, g=0.90, b=0.88)
                    gl.glTranslatef(0.0, 0.32, 0.0)
                    draw_textured_box(2.2, 0.34, 0.42, t_wbar, u_rep=1.0, v_rep=0.5, r=0.96, g=0.94, b=0.92)
                    gl.glTranslatef(0.0, 0.24, 0.0)
                    draw_textured_box(2.2, 0.24, 0.24, t_wbar, u_rep=1.0, v_rep=0.4, r=0.90, g=0.88, b=0.86)
                else:
                    draw_box(2.2, 0.36, 0.60, 0.65, 0.63, 0.60)
                    gl.glTranslatef(0.0, 0.32, 0.0)
                    draw_box(2.2, 0.34, 0.42, 0.62, 0.60, 0.57)
                    gl.glTranslatef(0.0, 0.24, 0.0)
                    draw_box(2.2, 0.24, 0.24, 0.60, 0.58, 0.55)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "wooden_barricade":
                t_wpal = self.world_textures.get('hl2_wood_pallet', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(-0.6, 0.7, 0.0)
                gl.glRotatef(25.0, 0.0, 0.0, 1.0)
                draw_box(0.14, 1.5, 0.14, 0.48, 0.34, 0.20)
                gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.6, 0.7, 0.0)
                gl.glRotatef(-25.0, 0.0, 0.0, 1.0)
                draw_box(0.14, 1.5, 0.14, 0.48, 0.34, 0.20)
                gl.glPopMatrix()
                for by in (0.35, 0.75, 1.15):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, by, 0.10)
                    if t_wpal:
                        draw_textured_box(1.8, 0.18, 0.06, t_wpal, u_rep=1.0, v_rep=0.3, r=0.95, g=0.88, b=0.76)
                    else:
                        draw_box(1.8, 0.18, 0.06, 0.58, 0.42, 0.26)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "razorwire":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for px in (-1.1, 0.0, 1.1):
                    gl.glPushMatrix()
                    gl.glTranslatef(px, 0.5, 0.0)
                    draw_box(0.05, 1.0, 0.05, 0.32, 0.35, 0.38)
                    gl.glPopMatrix()
                for wy, wz in ((0.35, -0.2), (0.35, 0.2), (0.75, 0.0)):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, wy, wz)
                    draw_box(2.4, 0.38, 0.38, 0.45, 0.48, 0.52)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            # ── 4. Street Furniture (Genuine HL2 VTF Materials) ──
            elif otype == "dumpster":
                t_dump = self.world_textures.get('hl2_dumpster', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.66, 0.0)
                if t_dump:
                    draw_textured_box(2.0, 1.24, 1.25, t_dump, u_rep=1.0, v_rep=1.0, r=0.94, g=0.96, b=0.92)
                else:
                    draw_box(2.0, 1.2, 1.25, 0.18, 0.34, 0.20)
                gl.glTranslatef(0.0, 0.65, 0.0)
                draw_box(2.04, 0.10, 1.28, 0.14, 0.16, 0.18)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "trash_can":
                t_oil = self.world_textures.get('hl2_oil_drum', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.45, 0.0)
                if t_oil:
                    draw_textured_cylinder(0.28, 0.88, t_oil, segs=14, u0=0.0, u1=1.0, v0=0.35, v1=1.0,
                                           cap_r=0.28, cap_g=0.30, cap_b=0.32)
                else:
                    draw_box(0.55, 0.90, 0.55, 0.32, 0.36, 0.38)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "vending_machine":
                # Genuine Dr. Breen's Private Reserve Soda Machine (models/props_interiors/sodamachine01a.vtf)
                t_soda = self.world_textures.get('hl2_soda_machine', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.05, 0.0)
                if t_soda:
                    draw_textured_box(1.08, 2.10, 0.85, t_soda, u_rep=1.0, v_rep=1.0, r=1.0, g=1.0, b=1.0)
                else:
                    draw_box(1.05, 2.1, 0.85, 0.18, 0.22, 0.32)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "phone_booth":
                t_mwall = self.world_textures.get('hl2_metal_wall', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.2, 0.0)
                if t_mwall:
                    draw_textured_box(0.95, 2.3, 0.95, t_mwall, u_rep=1.0, v_rep=1.0, r=0.82, g=0.86, b=0.90)
                else:
                    draw_box(0.95, 2.3, 0.95, 0.28, 0.32, 0.36)
                gl.glTranslatef(0.0, 1.18, 0.0)
                draw_box(1.05, 0.15, 1.05, 0.95, 0.82, 0.15)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "park_bench":
                t_bench = self.world_textures.get('hl2_bench', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for bx in (-0.7, 0.7):
                    gl.glPushMatrix()
                    gl.glTranslatef(bx, 0.25, 0.0)
                    draw_box(0.08, 0.50, 0.55, 0.18, 0.22, 0.20)
                    gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.46, 0.0)
                if t_bench:
                    draw_textured_box(1.6, 0.06, 0.52, t_bench, u_rep=1.0, v_rep=0.5, r=0.95, g=0.90, b=0.84)
                    gl.glTranslatef(0.0, 0.28, -0.22)
                    gl.glRotatef(15.0, 1.0, 0.0, 0.0)
                    draw_textured_box(1.6, 0.34, 0.06, t_bench, u_rep=1.0, v_rep=0.5, r=0.95, g=0.90, b=0.84)
                else:
                    draw_box(1.6, 0.05, 0.50, 0.52, 0.35, 0.20)
                    gl.glTranslatef(0.0, 0.28, -0.22)
                    gl.glRotatef(15.0, 1.0, 0.0, 0.0)
                    draw_box(1.6, 0.32, 0.05, 0.52, 0.35, 0.20)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "fire_hydrant":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.4, 0.0)
                draw_box(0.35, 0.8, 0.35, 0.85, 0.18, 0.14)
                draw_box(0.55, 0.14, 0.14, 0.90, 0.22, 0.16)
                gl.glTranslatef(0.0, 0.44, 0.0)
                draw_box(0.18, 0.10, 0.18, 0.88, 0.78, 0.20)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "traffic_cone":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.04, 0.0)
                draw_box(0.44, 0.08, 0.44, 0.12, 0.14, 0.16)
                gl.glTranslatef(0.0, 0.35, 0.0)
                draw_box(0.28, 0.65, 0.28, 1.0, 0.45, 0.05)
                draw_box(0.30, 0.16, 0.30, 0.95, 0.95, 0.95)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "street_sign":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.4, 0.0)
                draw_box(0.08, 2.8, 0.08, 0.42, 0.45, 0.48)
                gl.glTranslatef(0.0, 1.25, 0.0)
                draw_box(0.95, 0.26, 0.04, 0.15, 0.35, 0.75)
                draw_box(0.85, 0.05, 0.05, 0.95, 0.95, 0.95)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "manhole":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz + 0.015, oy)
                draw_box(0.95, 0.02, 0.95, 0.22, 0.24, 0.26)
                draw_box(0.85, 0.025, 0.85, 0.18, 0.20, 0.22)
                gl.glPopMatrix()

            # ── 5. Industrial & Combine Tech ──
            elif otype == "combine_terminal":
                t_cgen = self.world_textures.get('hl2_combine_generator', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.7, 0.0)
                if t_cgen:
                    draw_textured_box(0.65, 1.4, 0.55, t_cgen, u_rep=1.0, v_rep=1.0, r=0.88, g=0.94, b=1.0)
                else:
                    draw_box(0.65, 1.4, 0.55, 0.16, 0.20, 0.26)
                gl.glTranslatef(0.0, 0.45, 0.12)
                gl.glRotatef(25.0, 1.0, 0.0, 0.0)
                draw_box(0.55, 0.08, 0.38, 0.20, 0.85, 1.0)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "power_generator":
                t_cgen = self.world_textures.get('hl2_combine_generator', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.7, 0.0)
                if t_cgen:
                    draw_textured_box(1.75, 1.4, 1.15, t_cgen, u_rep=1.0, v_rep=1.0, r=0.95, g=0.96, b=0.98)
                else:
                    draw_box(1.75, 1.4, 1.15, 0.22, 0.25, 0.28)
                gl.glTranslatef(0.5, 0.85, -0.1)
                draw_box(0.14, 0.55, 0.14, 0.45, 0.45, 0.48)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "transformer_box":
                t_cgen = self.world_textures.get('hl2_combine_generator', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.8, 0.0)
                if t_cgen:
                    draw_textured_box(1.15, 1.6, 0.85, t_cgen, u_rep=1.0, v_rep=1.0, r=0.88, g=0.94, b=0.90)
                else:
                    draw_box(1.15, 1.6, 0.85, 0.24, 0.32, 0.24)
                gl.glTranslatef(0.0, 0.2, 0.44)
                draw_box(0.24, 0.24, 0.02, 0.95, 0.85, 0.10)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "fuel_tank":
                t_oil = self.world_textures.get('hl2_oil_drum', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for sx in (-0.8, 0.8):
                    gl.glPushMatrix()
                    gl.glTranslatef(sx, 0.25, 0.0)
                    draw_box(0.35, 0.50, 1.25, 0.58, 0.58, 0.56)
                    gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.85, 0.0)
                if t_oil:
                    draw_textured_box(2.35, 0.95, 1.15, t_oil, u_rep=1.0, v_rep=1.0, r=0.94, g=0.95, b=0.96)
                else:
                    draw_box(2.35, 0.95, 1.15, 0.88, 0.90, 0.92)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "ventilation_duct":
                t_mwall = self.world_textures.get('hl2_metal_wall', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.5, 0.0)
                if t_mwall:
                    draw_textured_box(2.2, 0.95, 0.95, t_mwall, u_rep=1.5, v_rep=0.8, r=0.90, g=0.92, b=0.95)
                else:
                    draw_box(2.2, 0.95, 0.95, 0.62, 0.65, 0.68)
                for fx in (-1.0, 0.0, 1.0):
                    gl.glPushMatrix()
                    gl.glTranslatef(fx, 0.0, 0.0)
                    draw_box(0.08, 1.04, 1.04, 0.48, 0.50, 0.54)
                    gl.glPopMatrix()
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "pipes_cluster":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.3, 0.0)
                for py, col in ((-0.4, (0.78, 0.48, 0.28)), (0.0, (0.45, 0.48, 0.52)), (0.4, (0.85, 0.72, 0.22))):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, py, 0.0)
                    draw_box(1.6, 0.14, 0.14, *col)
                    gl.glPopMatrix()
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "satellite_dish":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.5, 0.0)
                draw_box(0.12, 1.0, 0.12, 0.35, 0.38, 0.42)
                gl.glTranslatef(0.0, 0.55, 0.0)
                gl.glRotatef(-45.0, 1.0, 0.0, 0.0)
                draw_box(1.5, 0.12, 1.5, 0.82, 0.84, 0.86)
                gl.glTranslatef(0.0, 0.4, 0.0)
                draw_box(0.12, 0.45, 0.12, 0.25, 0.28, 0.32)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "security_camera":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.25, 0.0)
                draw_box(0.24, 0.28, 0.48, 0.18, 0.22, 0.26)
                gl.glTranslatef(0.0, 0.0, 0.25)
                p_red = 0.5 + 0.5 * math.sin(self.sim_time * 8.0)
                draw_box(0.10, 0.10, 0.05, 1.0, 0.15 * p_red, 0.15 * p_red)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "floodlight":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.0, 0.0)
                draw_box(0.08, 2.0, 0.08, 0.95, 0.82, 0.10)
                gl.glTranslatef(0.0, 1.05, 0.0)
                draw_box(0.65, 0.08, 0.12, 0.95, 0.82, 0.10)
                for lx in (-0.24, 0.24):
                    gl.glPushMatrix()
                    gl.glTranslatef(lx, 0.12, 0.0)
                    draw_box(0.22, 0.18, 0.18, 0.20, 0.22, 0.25)
                    gl.glTranslatef(0.0, 0.0, 0.10)
                    draw_box(0.18, 0.14, 0.04, 1.0, 0.95, 0.80)
                    gl.glPopMatrix()
                gl.glPopMatrix()
                gl.glPopMatrix()

            # ── 6. Furniture & Storage (Genuine HL2 VTF Materials) ──
            elif otype == "metal_table":
                t_mwall = self.world_textures.get('hl2_metal_wall', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for lx in (-0.7, 0.7):
                    for lz in (-0.35, 0.35):
                        gl.glPushMatrix()
                        gl.glTranslatef(lx, 0.42, lz)
                        draw_box(0.08, 0.84, 0.08, 0.32, 0.35, 0.38)
                        gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.86, 0.0)
                if t_mwall:
                    draw_textured_box(1.6, 0.06, 0.90, t_mwall, u_rep=1.0, v_rep=1.0, r=0.88, g=0.90, b=0.92)
                else:
                    draw_box(1.6, 0.06, 0.90, 0.52, 0.56, 0.60)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "wooden_chair":
                t_bench = self.world_textures.get('hl2_bench', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for cx in (-0.22, 0.22):
                    for cz in (-0.22, 0.22):
                        gl.glPushMatrix()
                        gl.glTranslatef(cx, 0.22, cz)
                        draw_box(0.05, 0.44, 0.05, 0.45, 0.32, 0.18)
                        gl.glPopMatrix()
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.46, 0.0)
                if t_bench:
                    draw_textured_box(0.55, 0.05, 0.55, t_bench, u_rep=0.5, v_rep=0.5, r=0.94, g=0.88, b=0.80)
                    gl.glTranslatef(0.0, 0.24, -0.24)
                    draw_textured_box(0.52, 0.45, 0.04, t_bench, u_rep=0.5, v_rep=0.5, r=0.94, g=0.88, b=0.80)
                else:
                    draw_box(0.55, 0.05, 0.55, 0.58, 0.40, 0.24)
                    gl.glTranslatef(0.0, 0.24, -0.24)
                    draw_box(0.52, 0.45, 0.04, 0.52, 0.36, 0.20)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "metal_locker":
                # Genuine Source Engine Locker Unit (models/props_c17/lockers001a.vtf)
                t_lock = self.world_textures.get('hl2_lockers', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.0, 0.0)
                if t_lock:
                    draw_textured_box(0.92, 2.0, 0.58, t_lock, u_rep=1.0, v_rep=1.0, r=0.96, g=0.98, b=0.96)
                else:
                    draw_box(0.88, 2.0, 0.58, 0.35, 0.38, 0.42)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "wooden_shelf":
                t_wpal = self.world_textures.get('hl2_wood_pallet', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for sx in (-0.65, 0.65):
                    for sz in (-0.24, 0.24):
                        gl.glPushMatrix()
                        gl.glTranslatef(sx, 1.0, sz)
                        draw_box(0.08, 2.0, 0.08, 0.45, 0.30, 0.18)
                        gl.glPopMatrix()
                for sy in (0.3, 0.8, 1.3, 1.8):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, sy, 0.0)
                    if t_wpal:
                        draw_textured_box(1.38, 0.05, 0.54, t_wpal, u_rep=1.0, v_rep=0.5, r=0.95, g=0.88, b=0.78)
                    else:
                        draw_box(1.38, 0.05, 0.54, 0.56, 0.38, 0.22)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "metal_crate":
                t_mwall = self.world_textures.get('hl2_metal_wall', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.6, 0.0)
                if t_mwall:
                    draw_textured_box(1.2, 1.2, 1.2, t_mwall, u_rep=1.0, v_rep=1.0, r=0.90, g=0.92, b=0.95)
                else:
                    draw_box(1.2, 1.2, 1.2, 0.32, 0.36, 0.40)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "wooden_pallet":
                # Genuine Source Engine Euro Wood Pallet (models/props_junk/wood_pallet001a.vtf)
                t_wpal = self.world_textures.get('hl2_wood_pallet', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.10, 0.0)
                if t_wpal:
                    draw_textured_box(1.3, 0.20, 1.1, t_wpal, u_rep=1.0, v_rep=1.0, r=0.98, g=0.94, b=0.88)
                else:
                    draw_box(1.3, 0.20, 1.1, 0.58, 0.42, 0.26)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "pallet_stack":
                t_wpal = self.world_textures.get('hl2_wood_pallet', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                for pi in range(4):
                    gl.glPushMatrix()
                    gl.glTranslatef(0.0, 0.10 + pi * 0.20, 0.0)
                    if t_wpal:
                        draw_textured_box(1.3, 0.18, 1.1, t_wpal, u_rep=1.0, v_rep=1.0, r=0.96, g=0.92, b=0.86)
                    else:
                        draw_box(1.3, 0.18, 1.1, 0.54 + pi * 0.02, 0.38 + pi * 0.02, 0.24)
                    gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "cardboard_box":
                # Genuine Source Engine Cardboard Boxes (models/props_junk/cardboard_boxes001a.vtf)
                t_cbox = self.world_textures.get('hl2_cardboard_box', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.35, 0.0)
                if t_cbox:
                    draw_textured_box(0.85, 0.70, 0.85, t_cbox, u_rep=1.0, v_rep=1.0, r=0.98, g=0.96, b=0.92)
                    gl.glTranslatef(0.08, 0.60, 0.05)
                    draw_textured_box(0.65, 0.50, 0.65, t_cbox, u_rep=1.0, v_rep=1.0, r=0.95, g=0.92, b=0.88)
                else:
                    draw_box(0.85, 0.70, 0.85, 0.65, 0.52, 0.38)
                    gl.glTranslatef(0.08, 0.60, 0.05)
                    draw_box(0.65, 0.50, 0.65, 0.62, 0.48, 0.35)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "radio_receiver":
                t_cgen = self.world_textures.get('hl2_combine_generator', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.25, 0.0)
                if t_cgen:
                    draw_textured_box(0.60, 0.45, 0.38, t_cgen, u_rep=0.6, v_rep=0.6, r=0.90, g=0.95, b=0.92)
                else:
                    draw_box(0.60, 0.45, 0.38, 0.28, 0.32, 0.30)
                gl.glTranslatef(0.15, 0.05, 0.20)
                draw_box(0.18, 0.12, 0.04, 0.85, 0.75, 0.25)
                gl.glTranslatef(-0.35, 0.35, -0.20)
                draw_box(0.03, 0.65, 0.03, 0.70, 0.72, 0.75)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "file_cabinet":
                t_lock = self.world_textures.get('hl2_lockers', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.70, 0.0)
                if t_lock:
                    draw_textured_box(0.60, 1.40, 0.68, t_lock, u_rep=0.8, v_rep=1.0, r=0.92, g=0.95, b=0.96)
                else:
                    draw_box(0.60, 1.40, 0.68, 0.38, 0.42, 0.45)
                gl.glPopMatrix()
                gl.glPopMatrix()

            # ── 7. Barrels, Hazards & Stations (Genuine HL2 VTF Materials) ──
            elif otype in ("barrel", "explosive_barrel"):
                draw_3d_source_prop(ox, oz, oy, math.radians(oyaw), otype, tex_crate)

            elif otype == "toxic_barrel":
                t_oil = self.world_textures.get('hl2_oil_drum', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.55, 0.0)
                if t_oil:
                    draw_textured_cylinder(0.42, 1.10, t_oil, segs=16, u0=0.0, u1=1.0, v0=0.35, v1=1.0,
                                           cap_r=0.72, cap_g=0.68, cap_b=0.18, r=1.0, g=0.92, b=0.35)
                else:
                    draw_box(0.84, 1.10, 0.84, 0.92, 0.80, 0.12)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "water_drum":
                t_blue = self.world_textures.get('hl2_blue_barrel', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.60, 0.0)
                if t_blue:
                    draw_textured_cylinder(0.46, 1.20, t_blue, segs=16, u0=0.0, u1=0.66, v0=0.0, v1=1.0,
                                           cap_r=0.14, cap_g=0.40, cap_b=0.76)
                else:
                    draw_box(0.95, 1.20, 0.95, 0.15, 0.45, 0.85)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "gas_canister":
                # Genuine Source Engine Metal Jerrycan / Gas Can (models/props_junk/metalgascan.vtf)
                t_gas = self.world_textures.get('hl2_gascan', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.42, 0.0)
                if t_gas:
                    draw_textured_box(0.38, 0.78, 0.54, t_gas, u_rep=1.0, v_rep=1.0, r=1.0, g=0.96, b=0.94)
                else:
                    draw_box(0.55, 1.30, 0.55, 0.95, 0.45, 0.10)
                gl.glTranslatef(0.0, 0.44, 0.0)
                draw_box(0.14, 0.12, 0.24, 0.75, 0.22, 0.18)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "ammo_crate":
                # Genuine Source Engine Resistance Munitions Crate (models/items/ammocrate_smg1.vtf)
                t_acrate = self.world_textures.get('hl2_ammocrate_smg1', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.26, 0.0)
                if t_acrate:
                    draw_textured_box(0.96, 0.52, 0.62, t_acrate, u_rep=1.0, v_rep=1.0, r=0.98, g=0.98, b=0.96)
                else:
                    draw_box(0.88, 0.45, 0.58, 0.28, 0.36, 0.24)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "health_station":
                # Genuine Source Engine Combine Medkit Charger (models/props_combine/health_charger001.vtf)
                t_hchg = self.world_textures.get('hl2_health_charger', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.65, 0.0)
                if t_hchg:
                    draw_textured_box(0.62, 1.05, 0.34, t_hchg, u_rep=1.0, v_rep=1.0, r=0.95, g=1.0, b=0.98)
                else:
                    draw_box(0.58, 0.90, 0.32, 0.25, 0.28, 0.32)
                gl.glTranslatef(0.0, 0.15, 0.18)
                draw_box(0.18, 0.06, 0.04, 0.15, 1.0, 0.45)
                draw_box(0.06, 0.18, 0.04, 0.15, 1.0, 0.45)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "suit_charger":
                # Genuine Source Engine HEV Suit Power Charger (models/props_combine/suit_charger001_sheet.vtf)
                t_schg = self.world_textures.get('hl2_suit_charger', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.65, 0.0)
                if t_schg:
                    draw_textured_box(0.62, 1.05, 0.34, t_schg, u_rep=1.0, v_rep=1.0, r=1.0, g=0.96, b=0.90)
                else:
                    draw_box(0.58, 0.90, 0.32, 0.22, 0.25, 0.28)
                gl.glTranslatef(0.0, 0.15, 0.18)
                draw_box(0.22, 0.22, 0.04, 1.0, 0.65, 0.12)
                gl.glPopMatrix()
                gl.glPopMatrix()

            # ── 8. Vehicles & Heavy ──
            elif otype == "wrecked_car":
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 0.45, 0.0)
                draw_box(2.1, 0.65, 4.2, 0.45, 0.28, 0.20)
                gl.glTranslatef(0.0, 0.50, -0.3)
                draw_box(1.8, 0.55, 2.2, 0.35, 0.22, 0.16)
                gl.glPopMatrix()
                gl.glPopMatrix()

            elif otype == "charger":
                gl.glPushMatrix()
                gl.glTranslatef(0.0, oz, 0.0)
                draw_3d_charger(ox, oy, math.radians(oyaw))
                gl.glPopMatrix()

            elif otype == "cargo_container":
                # Genuine Source Engine NorthernPetrol Corrugated Cargo Container (cargo_container01/02.vtf)
                c_key = 'hl2_cargo_container02' if (int(ox + oy) % 2 == 1) else 'hl2_cargo_container01'
                t_cargo = self.world_textures.get(c_key, 0) or self.world_textures.get('hl2_cargo_container01', 0)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz, oy)
                gl.glRotatef(oyaw, 0.0, 1.0, 0.0)
                gl.glPushMatrix()
                gl.glTranslatef(0.0, 1.30, 0.0)
                if t_cargo:
                    draw_textured_box(2.4, 2.6, 4.6, t_cargo, u_rep=1.0, v_rep=1.0, r=0.98, g=0.98, b=0.98)
                else:
                    draw_box(2.4, 2.6, 4.6, 0.18, 0.38, 0.65)
                gl.glPopMatrix()
                gl.glPopMatrix()

            # ── 9. Live Entities ──
            elif otype == "crate":
                draw_3d_source_prop(ox, oz, oy, math.radians(oyaw), 'crate', tex_crate)
            elif otype == "mcpd_stunstick":
                draw_3d_humanoid(ox, oy, math.radians(oyaw), 'mcpd', 0, False, False, False, weapon_id=1, weapon_type='stunstick')
            elif otype == "mcpd_pistol":
                draw_3d_humanoid(ox, oy, math.radians(oyaw), 'mcpd', 0, False, False, False, weapon_id=1, weapon_type='pistol')
            elif otype == "civilian":
                draw_3d_humanoid(ox, oy, math.radians(oyaw), 'civilian', 0, False, False, False)
            elif otype == "ecpu":
                draw_3d_humanoid(ox, oy, math.radians(oyaw), 'ecpu', 0, False, False, False, weapon_id=4)
            elif otype == "military":
                draw_3d_humanoid(ox, oy, math.radians(oyaw), 'military', 0, False, False, False, weapon_id=4)
            elif otype == "rpg":
                draw_3d_humanoid(ox, oy, math.radians(oyaw), 'rpg', 0, False, False, False, weapon_id=6)

        # Draw all placed objects
        for i, obj in enumerate(getattr(self, 'placed_objects', [])):
            ox = float(obj.get("x", 0.0))
            oy = float(obj.get("y", 0.0))
            oz = float(obj.get("z", 0.0))
            if (ox - self.player_x) ** 2 + (oy - self.player_y) ** 2 > cull_sq:
                continue
            _draw_static_hl2_obj(obj.get("type", ""), ox, oy, float(obj.get("yaw", 0.0)), oz)

            # If this placed prop is currently targeted by the editor yellow pointer raycast:
            if self.map_editor_active and i == getattr(self, 'editor_targeted_prop_idx', None):
                cdata = PROP_COLLISION_DATA.get(obj.get("type", ""), {"shape": "box", "w": 1.2, "d": 1.2, "h": 1.5})
                bw = cdata.get("w", 1.2) + 0.16
                bd = cdata.get("d", 1.2) + 0.16
                bh = cdata.get("h", 1.5) + 0.16
                pulse = 0.70 + 0.30 * math.sin(self.sim_time * 10.0)
                gl.glEnable(GL_BLEND)
                gl.glPushMatrix()
                gl.glTranslatef(ox, oz + bh * 0.5, oy)
                gl.glRotatef(float(obj.get("yaw", 0.0)), 0.0, 1.0, 0.0)
                # Outer glowing translucent amber box
                gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
                draw_box(bw, bh, bd, 1.0, 0.88, 0.12, 0.38 * pulse)
                # Bright highlight edges
                draw_box(bw + 0.04, 0.06, bd + 0.04, 1.0, 0.95, 0.30, 0.90)
                draw_box(bw + 0.04, bh, 0.06, 1.0, 0.95, 0.30, 0.90)
                gl.glPopMatrix()
                gl.glDisable(GL_BLEND)

        # Live 3D Map Editor Placement Preview Cursor
        if self.map_editor_active:
            self._update_editor_cursor()
            cat, val, _ = MAP_EDITOR_PALETTE[self.editor_idx % len(MAP_EDITOR_PALETTE)]
            pulse = 0.65 + 0.35 * math.sin(self.sim_time * 8.0)
            gl.glEnable(GL_BLEND)
            gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
            tx, tz = self.editor_target_x, self.editor_target_y
            ty = getattr(self, 'editor_target_z', 0.0)
            if cat == "grid":
                gx = max(1, min(MAP_W - 2, int(tx))) + 0.5
                gz = max(1, min(MAP_H - 2, int(tz))) + 0.5
                gl.glPushMatrix()
                gl.glTranslatef(gx, 0.05 + ty, gz)
                col = (1.0, 0.25, 0.20) if val == 0 else ((0.20, 0.78, 1.0) if val == 7 else (0.25, 1.0, 0.45))
                draw_box(1.04, 0.08, 1.04, col[0], col[1], col[2], 0.55 * pulse)
                if val in (1, 2, 3, 4, 5, 6):
                    bh = 2.6 if val == 6 else 4.2
                    gl.glTranslatef(0.0, bh * 0.5, 0.0)
                    draw_box(1.02, bh, 1.02, col[0], col[1], col[2], 0.28 * pulse)
                gl.glPopMatrix()
            else:
                is_arch = val in ("stairs_metal", "stairs_wood", "metal_ramp", "scaffolding", "second_story_floor", "roof_walkway")
                if is_arch:
                    px = math.floor(tx) + 0.5
                    pz = math.floor(tz) + 0.5
                    pyaw = round(float(self.editor_yaw) / 90.0) * 90.0 % 360.0
                    py = round(ty / 2.8) * 2.8 if val in ("second_story_floor", "roof_walkway") else ty
                else:
                    px, pz, pyaw, py = tx, tz, float(self.editor_yaw), ty

                gl.glPushMatrix()
                gl.glTranslatef(px, 0.04 + py, pz)
                draw_box(1.1, 0.05, 1.1, 0.20, 0.95, 1.0, 0.50 * pulse)
                gl.glTranslatef(0.0, 1.5, 0.0)
                draw_box(0.05, 3.0, 0.05, 0.20, 0.95, 1.0, 0.65 * pulse)
                gl.glPopMatrix()
                gl.glDisable(GL_BLEND)
                _draw_static_hl2_obj(val, px, pz, pyaw, py)
            gl.glDisable(GL_BLEND)

    def get_arms_shop_location(self):
        if self.current_map == "driving Test map":
            return (-999.0, -999.0)
        elif self.current_map == "BigCity5":
            return (18.5, 32.0)
        elif self.current_map == "gm_bigcity":
            return (18.5, 16.5)
        return (10.5, 13.5)

    def toggle_arms_shop(self):
        self.arms_shop_open = not getattr(self, 'arms_shop_open', False)
        if self.arms_shop_open:
            self.paused = False
            self.admin_open = False
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            self.snd_pickup.play()
            self.add_log('sys', '[TBMG ARMS SHOP] Kiosk terminal accessed. Press [1-8] or click to purchase.')
        else:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)

    def buy_shop_item(self, item_wid):
        item = next((i for i in self.arms_shop_catalog if str(i["wid"]) == str(item_wid)), None)
        if not item:
            return False
        if self.player_money < item["price"]:
            self.snd_metal.play()
            self.add_log('warn', f'INSUFFICIENT FUNDS: {item["name"]} costs ${item["price"]:,} TMD!')
            return False
        if isinstance(item["wid"], int) and self.weapons_owned.get(item["wid"], False):
            self.add_log('info', f'ALREADY OWNED: You already possess {item["name"]}.')
            return False

        self.player_money -= item["price"]
        self.snd_pickup.play()

        if isinstance(item["wid"], int):
            self.weapons_owned[item["wid"]] = True
            self.current_weapon = item["wid"]
            w_defn = WEAPONS[item["wid"]]
            clip_sz = w_defn.get("clip_size", 0)
            if clip_sz > 0:
                self.weapon_clips[item["wid"]] = clip_sz
            self.add_log('info', f'[TBMG ARMS] Purchased {item["name"]} for ${item["price"]:,} TMD!')
        elif item["wid"] == "ammo":
            self.ammo['bullets'] = self.ammo_max['bullets']
            self.ammo['shells'] = self.ammo_max['shells']
            self.ammo['cells'] = self.ammo_max['cells']
            self.ammo['rockets'] = self.ammo_max['rockets']
            for wid, owned in self.weapons_owned.items():
                if owned:
                    cs = WEAPONS[wid].get("clip_size", 0)
                    if cs > 0:
                        self.weapon_clips[wid] = cs
            self.add_log('info', '[TBMG ARMS] All ammunition reserves restocked!')
        elif item["wid"] == "armor":
            self.player_armor = 100
            self.add_log('info', '[TBMG ARMS] HEV / Body Armor recharged to 100%!')
        return True

    def _render_3d_arms_shop_kiosk(self, sx, sy):
        gl.glPushMatrix()
        gl.glTranslatef(sx, 0.0, sy)

        # Counter booth base
        draw_box(2.2, 1.0, 1.4, 0.12, 0.15, 0.20)
        # Counter top
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 1.04, 0.0)
        draw_box(2.3, 0.08, 1.5, 0.22, 0.26, 0.32)
        gl.glPopMatrix()

        # 4 Support pillars
        for px in (-1.0, 1.0):
            for pz in (-0.6, 0.6):
                gl.glPushMatrix()
                gl.glTranslatef(px, 1.9, pz)
                draw_box(0.08, 1.8, 0.08, 0.95, 0.60, 0.20)
                gl.glPopMatrix()

        # Canopy
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 2.8, 0.0)
        draw_box(2.5, 0.15, 1.7, 0.12, 0.15, 0.20)
        # Glowing 3D Neon Sign
        gl.glTranslatef(0.0, 0.0, 0.86)
        draw_box(2.2, 0.45, 0.1, 0.15, 0.18, 0.24)
        draw_box(2.0, 0.30, 0.12, 1.0, 0.62, 0.15)
        gl.glPopMatrix()

        gl.glPopMatrix()

    def _render_ravenholm_hazards(self, max_draw_dist):
        """Renders authentic Ravenholm layout architecture and traps in MainCity2 (No Father Grigori):
        overhead dangling girders & counterweights, spinning sawblades with sparks, damaged gas pipe flame jets,
        and volatile red propane cylinder traps."""
        px, py = self.player_x, self.player_y

        hazards = [
            # Hanging girder & counterweight traps suspended by overhead cables across alleys
            {"type": "hanging_girder", "x": 30.5, "y": 34.5, "z": 2.8, "axis": "x", "span": 2.4},
            {"type": "hanging_girder", "x": 40.5, "y": 34.5, "z": 2.8, "axis": "x", "span": 2.4},
            {"type": "hanging_girder", "x": 35.5, "y": 38.5, "z": 2.9, "axis": "y", "span": 2.2},
            # Embedded spinning steel sawblade traps mounted on tenement walls
            {"type": "spinning_sawblade", "x": 29.2, "y": 32.5, "z": 1.15},
            {"type": "spinning_sawblade", "x": 39.2, "y": 32.5, "z": 1.15},
            {"type": "spinning_sawblade", "x": 33.5, "y": 36.8, "z": 1.25},
            # Damaged gas pipe fire jets venting animated flickering flames
            {"type": "gas_fire_jet", "x": 31.8, "y": 35.5, "z": 0.45, "dx": 1.0, "dy": 0.0},
            {"type": "gas_fire_jet", "x": 38.2, "y": 35.5, "z": 0.45, "dx": -1.0, "dy": 0.0},
            {"type": "gas_fire_jet", "x": 35.0, "y": 39.2, "z": 0.45, "dx": 0.0, "dy": -1.0},
            # Volatile red explosive propane / fuel cylinder traps
            {"type": "propane_trap", "x": 30.2, "y": 35.8, "z": 0.4},
            {"type": "propane_trap", "x": 41.2, "y": 35.8, "z": 0.4},
            {"type": "propane_trap", "x": 36.5, "y": 37.8, "z": 0.4},
        ]

        for h in hazards:
            hx, hy = h["x"], h["y"]
            dist = math.hypot(hx - px, hy - py)
            if dist > max_draw_dist:
                continue

            htype = h["type"]
            hz = h.get("z", 1.0)

            if htype == "hanging_girder":
                sway = math.sin(self.sim_time * 1.6 + hx) * 0.12
                gl.glPushMatrix()
                gl.glTranslatef(hx, hz, hy)
                gl.glDisable(GL_TEXTURE_2D)
                gl.glLineWidth(2.0)
                gl.glBegin(GL_LINES)
                gl.glColor4f(0.25, 0.25, 0.28, 0.9)
                gl.glVertex3f(-0.8, 1.8, 0.0)
                gl.glVertex3f(-0.8 + sway, 0.0, 0.0)
                gl.glVertex3f(0.8, 1.8, 0.0)
                gl.glVertex3f(0.8 + sway, 0.0, 0.0)
                gl.glEnd()
                gl.glLineWidth(1.0)
                gl.glTranslatef(sway, 0.0, 0.0)
                if h.get("axis") == "x":
                    draw_box(h.get("span", 2.4), 0.22, 0.22, 0.32, 0.35, 0.40)
                    draw_box(0.35, 0.45, 0.35, 0.22, 0.24, 0.28)
                else:
                    draw_box(0.22, 0.22, h.get("span", 2.4), 0.32, 0.35, 0.40)
                    draw_box(0.35, 0.45, 0.35, 0.22, 0.24, 0.28)
                gl.glPopMatrix()

            elif htype == "spinning_sawblade":
                spin_rot = (self.sim_time * 840.0) % 360.0
                gl.glPushMatrix()
                gl.glTranslatef(hx, hz, hy)
                draw_box(0.12, 1.2, 0.12, 0.28, 0.28, 0.32)
                gl.glTranslatef(0.0, 0.1, 0.0)
                gl.glRotatef(spin_rot, 0, 1, 0)
                draw_box(0.85, 0.04, 0.85, 0.78, 0.82, 0.90)
                draw_box(0.40, 0.06, 0.40, 0.45, 0.48, 0.52)
                if (int(self.sim_time * 24) % 3) == 0:
                    draw_box(0.15, 0.15, 0.15, 1.0, 0.9, 0.3, 0.8)
                gl.glPopMatrix()

            elif htype == "gas_fire_jet":
                gl.glPushMatrix()
                gl.glTranslatef(hx, hz, hy)
                draw_box(0.18, 0.18, 0.18, 0.22, 0.22, 0.26)
                flame_pulse = math.sin(self.sim_time * 18.0 + hx * 3.0) * 0.2 + 0.8
                flame_len = 0.9 * flame_pulse
                fdx, fdy = h.get("dx", 0.0) * flame_len, h.get("dy", 0.0) * flame_len
                gl.glTranslatef(fdx * 0.5, 0.0, fdy * 0.5)
                draw_box(max(0.18, abs(fdx)), 0.32 * flame_pulse, max(0.18, abs(fdy)), 1.0, 0.45, 0.05, 0.85)
                draw_box(max(0.08, abs(fdx) * 0.6), 0.18 * flame_pulse, max(0.08, abs(fdy) * 0.6), 1.0, 0.95, 0.3, 0.95)
                gl.glPopMatrix()

            elif htype == "propane_trap":
                gl.glPushMatrix()
                gl.glTranslatef(hx, hz, hy)
                draw_box(0.38, 0.75, 0.38, 0.88, 0.15, 0.10)
                gl.glTranslatef(0.0, 0.42, 0.0)
                draw_box(0.16, 0.16, 0.16, 0.85, 0.85, 0.15)
                gl.glPopMatrix()

    def render_arms_shop_modal(self, surf):
        w, h = surf.get_size()
        mw, mh = 680, 480
        mx, my = (w - mw) // 2, (h - mh) // 2

        # Dim background
        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 160))
        surf.blit(dim, (0, 0))

        # Main shop frame
        box = pygame.Surface((mw, mh), pygame.SRCALPHA)
        box.fill((15, 22, 32, 245))
        pygame.draw.rect(box, (245, 155, 56), (0, 0, mw, mh), 2, border_radius=10)

        # Header
        hdr_txt = self.font_modern_title.render("TBMG UNREGULATED ARMS & MUNITIONS", True, (245, 155, 56))
        box.blit(hdr_txt, (24, 18))
        sub_txt = self.font_console.render("Direct Resistance Black Market Distribution · [ESC / E] Close", True, (150, 175, 200))
        box.blit(sub_txt, (26, 52))

        # Close button [X]
        close_btn_rect = pygame.Rect(mx + mw - 38, my + 14, 26, 26)
        self.shop_button_rects = [(close_btn_rect, 'close')]
        close_s = pygame.Surface((26, 26), pygame.SRCALPHA)
        close_s.fill((60, 20, 20, 220))
        pygame.draw.rect(close_s, (240, 80, 80), (0, 0, 26, 26), 1, border_radius=4)
        x_txt = self.font_hud_sm.render("X", True, (255, 200, 200))
        close_s.blit(x_txt, (13 - x_txt.get_width() // 2, 5))
        box.blit(close_s, (mw - 38, 14))

        # Funds indicator
        funds_s = self.font_hud.render(f"FUNDS: ${self.player_money:,} TMD", True, (50, 255, 130))
        box.blit(funds_s, (mw - funds_s.get_width() - 48, 18))

        item_y = 80
        for idx, item in enumerate(self.arms_shop_catalog):
            btn_rect = pygame.Rect(mx + mw - 180, my + item_y + 6, 150, 30)
            self.shop_button_rects.append((btn_rect, item["wid"]))

            # Row background
            row_s = pygame.Surface((mw - 40, 42), pygame.SRCALPHA)
            row_s.fill((25, 35, 50, 200))
            pygame.draw.rect(row_s, (60, 80, 110), (0, 0, mw - 40, 42), 1, border_radius=6)
            box.blit(row_s, (20, item_y))

            # Icon & Name
            tag = f"[{idx + 1}] {item['icon']} {item['name']}"
            name_s = self.font_modern_card.render(tag, True, (245, 248, 255))
            box.blit(name_s, (32, item_y + 4))

            desc_s = self.font_console.render(item['desc'], True, (140, 160, 185))
            box.blit(desc_s, (34, item_y + 24))

            # Button state
            is_owned = isinstance(item['wid'], int) and self.weapons_owned.get(item['wid'], False)
            can_afford = self.player_money >= item['price']

            if is_owned:
                b_col = (50, 60, 75)
                b_lbl = "OWNED"
                t_col = (140, 150, 165)
            elif can_afford:
                b_col = (5, 150, 105)
                b_lbl = f"BUY (${item['price']:,})"
                t_col = (255, 255, 255)
            else:
                b_col = (90, 30, 30)
                b_lbl = f"${item['price']:,}"
                t_col = (240, 120, 120)

            btn_s = pygame.Surface((150, 30), pygame.SRCALPHA)
            btn_s.fill((*b_col, 220))
            pygame.draw.rect(btn_s, (255, 255, 255, 60), (0, 0, 150, 30), 1, border_radius=4)
            bl_txt = self.font_hud_sm.render(b_lbl, True, t_col)
            btn_s.blit(bl_txt, (75 - bl_txt.get_width() // 2, 8))
            box.blit(btn_s, (mw - 180, item_y + 6))

            item_y += 48

        surf.blit(box, (mx, my))

    def _get_vehicle_thumb_surf(self, thumb_file):
        if not hasattr(self, '_vehicle_thumb_surfs'):
            self._vehicle_thumb_surfs = {}
        if thumb_file not in self._vehicle_thumb_surfs:
            p = os.path.join(os.path.dirname(os.path.abspath(__file__)), thumb_file)
            if os.path.exists(p):
                try:
                    s = pygame.image.load(p).convert_alpha()
                    s = pygame.transform.smoothscale(s, (108, 62))
                    self._vehicle_thumb_surfs[thumb_file] = s
                except Exception:
                    self._vehicle_thumb_surfs[thumb_file] = None
            else:
                self._vehicle_thumb_surfs[thumb_file] = None
        return self._vehicle_thumb_surfs.get(thumb_file)

    def get_vehicle_dlist(self, vid):
        if not hasattr(self, 'vehicle_dlists'):
            self.vehicle_dlists = {}
        if vid not in self.vehicle_dlists:
            if vid == "crown_vic_wreck":
                p = os.path.join(os.path.dirname(os.path.abspath(__file__)), "crash_test_ford_crown_victoria.glb")
                self.vehicle_dlists[vid] = load_glb_to_display_list(p)
            else:
                spec = next((v for v in VEHICLE_CATALOG if v["id"] == vid), None)
                if spec:
                    if spec.get("glb_file") == "__procedural_police_cruiser__":
                        self.vehicle_dlists[vid] = build_police_cruiser_display_list()
                    else:
                        p = os.path.join(os.path.dirname(os.path.abspath(__file__)), spec["glb_file"])
                        self.vehicle_dlists[vid] = load_glb_to_display_list(p)
        return self.vehicle_dlists.get(vid, 0)

    def toggle_vehicle_spawner(self):
        if self.current_map not in ("MainCity2", "BigCity5", "driving Test map"):
            return
        self.vehicle_spawner_open = not getattr(self, 'vehicle_spawner_open', False)
        if self.vehicle_spawner_open:
            self.paused = False
            self.admin_open = False
            self.arms_shop_open = False
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
            if hasattr(self, 'snd_pickup'):
                self.snd_pickup.play()
            self.add_log('sys', '[CAR SPAWNER] Terminal online. Press [1-5] or click [SPAWN & DRIVE].')
        else:
            pygame.mouse.set_visible(False)
            pygame.event.set_grab(True)

    def spawn_vehicle(self, vid, drive_immediately=True):
        if self.current_map not in ("MainCity2", "BigCity5", "driving Test map"):
            return None
        spec = next((v for v in VEHICLE_CATALOG if v["id"] == vid), None)
        if not spec:
            return None

        if self.current_map == "driving Test map":
            # Spawn parking bay at (23.5, 23.5), facing East along highway (yaw = 0.0)
            spawn_x = 23.5
            spawn_y = 23.5
            spawn_yaw = 0.0
        elif self.current_map == "MainCity2":
            # Spawn parking bay on South Highway Boulevard at (18.5, 31.0), facing East (yaw = 0.0)
            spawn_x = 18.5
            spawn_y = 31.0
            spawn_yaw = 0.0
        else:
            # Spawn parking bay at (18.0, 29.0), facing East along highway (yaw = 0.0)
            spawn_x = 18.0
            spawn_y = 29.0
            spawn_yaw = 0.0

        # Clear parking bay of previous vehicles (single pristine vehicle on driving Test map)
        if self.current_map == "driving Test map":
            self.vehicles = []
        else:
            self.vehicles = [v for v in getattr(self, 'vehicles', []) if math.hypot(v.x - spawn_x, v.y - spawn_y) > 3.0]

        new_veh = DrivableVehicle(spec, spawn_x, spawn_y, spawn_yaw)
        new_veh.dlist = self.get_vehicle_dlist(vid)
        self.vehicles.append(new_veh)

        self.add_log('sys', f'[VEHICLE DISPATCH] Deployed {spec["name"]} at Parking Bay #1.')
        if hasattr(self, 'snd_pickup'):
            self.snd_pickup.play()

        if drive_immediately:
            self.enter_vehicle(new_veh)
            if self.vehicle_spawner_open:
                self.toggle_vehicle_spawner()
        return new_veh

    def enter_vehicle(self, veh):
        self.in_vehicle = True
        self.active_vehicle = veh
        self.player_x = veh.x
        self.player_y = veh.y
        self.player_z = veh.z
        self.player_angle = veh.yaw
        if hasattr(self, 'snd_car_engine') and self.snd_car_engine:
            self.snd_car_engine.play()
        self.add_log('info', f'[VEHICLE] Seated in {veh.name}. [W/S] Drive, [A/D] Steer, [SPACE] Handbrake, [E] Exit.')

    def exit_vehicle(self):
        if not getattr(self, 'in_vehicle', False) or not getattr(self, 'active_vehicle', None):
            return
        veh = self.active_vehicle
        cos_y = math.cos(veh.yaw)
        sin_y = math.sin(veh.yaw)
        exit_x = veh.x - sin_y * 1.85
        exit_y = veh.y + cos_y * 1.85
        if not self.is_position_blocked(exit_x, exit_y, 0.3):
            self.player_x = exit_x
            self.player_y = exit_y
        else:
            exit_x2 = veh.x + sin_y * 1.85
            exit_y2 = veh.y - cos_y * 1.85
            if not self.is_position_blocked(exit_x2, exit_y2, 0.3):
                self.player_x = exit_x2
                self.player_y = exit_y2
        self.in_vehicle = False
        self.active_vehicle = None
        veh.speed = 0.0
        self.add_log('info', f'[VEHICLE] Exited {veh.name}.')

    def render_vehicle_spawner_modal(self, surf):
        w, h = surf.get_size()
        mw, mh = 960, 530
        mx, my = (w - mw) // 2, (h - mh) // 2

        dim = pygame.Surface((w, h), pygame.SRCALPHA)
        dim.fill((0, 0, 0, 165))
        surf.blit(dim, (0, 0))

        box = pygame.Surface((mw, mh), pygame.SRCALPHA)
        box.fill((14, 20, 30, 248))
        pygame.draw.rect(box, (245, 195, 50), (0, 0, mw, mh), 2, border_radius=10)

        modal_title = "DRIVING TEST VEHICLE DISPATCH" if self.current_map == "driving Test map" else "BIG CITY 5 VEHICLE DISPATCH TERMINAL"
        hdr_txt = self.font_modern_title.render(modal_title, True, (245, 195, 50))
        box.blit(hdr_txt, (24, 16))
        sub_txt = self.font_console.render("Authorized Motor Pool (10 Vehicles) -- Press [1-9, 0] or click [SPAWN & DRIVE] -- [ESC / E] Close", True, (150, 180, 210))
        box.blit(sub_txt, (26, 48))

        close_btn_rect = pygame.Rect(mx + mw - 38, my + 14, 26, 26)
        self.vehicle_button_rects = [(close_btn_rect, 'close')]
        close_s = pygame.Surface((26, 26), pygame.SRCALPHA)
        close_s.fill((60, 20, 20, 220))
        pygame.draw.rect(close_s, (240, 80, 80), (0, 0, 26, 26), 1, border_radius=4)
        x_txt = self.font_hud_sm.render("X", True, (255, 200, 200))
        close_s.blit(x_txt, (13 - x_txt.get_width() // 2, 5))
        box.blit(close_s, (mw - 38, 14))

        col_w = 445
        for idx, item in enumerate(VEHICLE_CATALOG):
            col = 0 if idx < 5 else 1
            row = idx % 5
            rx = 20 if col == 0 else 495
            ry = 76 + row * 84

            btn_rect = pygame.Rect(mx + rx + col_w - 125, my + ry + 18, 120, 38)
            self.vehicle_button_rects.append((btn_rect, item["id"]))

            row_s = pygame.Surface((col_w, 78), pygame.SRCALPHA)
            row_s.fill((22, 32, 46, 210))
            pygame.draw.rect(row_s, (55, 80, 115), (0, 0, col_w, 78), 1, border_radius=6)
            box.blit(row_s, (rx, ry))

            thumb_surf = self._get_vehicle_thumb_surf(item["thumb_file"])
            if thumb_surf:
                box.blit(thumb_surf, (rx + 6, ry + 7))
                pygame.draw.rect(box, (80, 110, 145), (rx + 5, ry + 6, 110, 64), 1, border_radius=4)
            else:
                ph_rect = pygame.Rect(rx + 6, ry + 7, 108, 62)
                pygame.draw.rect(box, (35, 45, 60), ph_rect, border_radius=4)
                ph_txt = self.font_console.render("[PREVIEW]", True, (120, 140, 165))
                box.blit(ph_txt, (ph_rect.centerx - ph_txt.get_width() // 2, ph_rect.centery - 6))

            key_lbl = "0" if idx == 9 else str(idx + 1)
            tag = f"[{key_lbl}] {item['name']}"
            name_s = self.font_hud_sm.render(tag, True, (255, 255, 255))
            box.blit(name_s, (rx + 122, ry + 8))

            cat_s = self.font_modern_tag.render(item['category'], True, (245, 195, 50))
            box.blit(cat_s, (rx + 124, ry + 28))

            specs_str = f"{int(item['max_speed'] * 3.6)} KM/H | ARMOR {item['armor']}"
            specs_s = self.font_console.render(specs_str, True, (80, 235, 170))
            box.blit(specs_s, (rx + 124, ry + 48))

            btn_s = pygame.Surface((120, 38), pygame.SRCALPHA)
            btn_s.fill((10, 140, 85, 230))
            pygame.draw.rect(btn_s, (60, 240, 160), (0, 0, 120, 38), 1, border_radius=5)
            bl_txt = self.font_hud_sm.render(f"SPAWN [{key_lbl}]", True, (255, 255, 255))
            btn_s.blit(bl_txt, (60 - bl_txt.get_width() // 2, 10))
            box.blit(btn_s, (rx + col_w - 125, ry + 18))

        surf.blit(box, (mx, my))

    def render_vehicle_hud(self, surf):
        veh = self.active_vehicle
        if not veh:
            return
        w, h = surf.get_size()
        panel_w, panel_h = 240, 86
        panel_x = w - panel_w - 20
        panel_y = h - panel_h - 20

        p_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        p_surf.fill((12, 18, 26, 225))
        pygame.draw.rect(p_surf, (245, 195, 50), (0, 0, panel_w, panel_h), 2, border_radius=6)

        kmh = int(abs(veh.speed) * 3.6)
        spd_txt = self.font_title.render(f"{kmh:02d} KM/H", True, (80, 240, 255))
        p_surf.blit(spd_txt, (14, 8))

        gear_txt = self.font_title.render(f"[{veh.gear}]", True, (255, 215, 60))
        p_surf.blit(gear_txt, (panel_w - gear_txt.get_width() - 14, 8))

        vname_txt = self.font_console.render(veh.name[:22], True, (210, 225, 240))
        p_surf.blit(vname_txt, (15, 46))

        bar_w = panel_w - 30
        hp_ratio = max(0.0, min(1.0, veh.health / max(1, veh.max_health)))
        pygame.draw.rect(p_surf, (40, 50, 65), (15, 64, bar_w, 8), border_radius=3)
        pygame.draw.rect(p_surf, (50, 220, 120), (15, 64, int(bar_w * hp_ratio), 8), border_radius=3)

        surf.blit(p_surf, (panel_x, panel_y))

        hints_w, hints_h = 520, 26
        hints_x = (w - hints_w) // 2
        hints_y = h - 42
        h_surf = pygame.Surface((hints_w, hints_h), pygame.SRCALPHA)
        h_surf.fill((12, 18, 26, 210))
        pygame.draw.rect(h_surf, (60, 90, 130), (0, 0, hints_w, hints_h), 1, border_radius=4)
        siren_hint = "  |  [H] Police Siren" if getattr(veh, 'is_police', False) else "  |  [H] Horn"
        htxt = self.font_console.render(f"[W] Gas  |  [S] Brake/Rev  |  [A/D] Steer  |  [SPACE] Handbrake{siren_hint}  |  [E] Exit", True, (220, 235, 250))
        h_surf.blit(htxt, (hints_w // 2 - htxt.get_width() // 2, 6))
        surf.blit(h_surf, (hints_x, hints_y))

    def _draw_mini_display_car(self):
        """Draws miniature rotating 3D car sitting on top of the Car Spawner kiosk."""
        draw_box(1.8, 0.45, 3.6, 0.88, 0.16, 0.16)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.40, -0.25)
        draw_box(1.35, 0.40, 1.8, 0.16, 0.22, 0.28)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.05, 1.75)
        draw_box(1.4, 0.20, 0.10, 0.98, 0.98, 0.60)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.05, -1.75)
        draw_box(1.4, 0.20, 0.10, 0.95, 0.15, 0.15)
        gl.glPopMatrix()
        for wx, wz in ((-0.95, 1.1), (0.95, 1.1), (-0.95, -1.1), (0.95, -1.1)):
            gl.glPushMatrix()
            gl.glTranslatef(wx, -0.15, wz)
            draw_box(0.24, 0.44, 0.44, 0.08, 0.08, 0.08)
            gl.glPopMatrix()

    def _render_3d_car_spawner_kiosk(self, sx, sy, bay_x=18.0, bay_y=29.0):
        """Renders 3D Car Spawner kiosk and marked parking lot bay."""
        gl.glPushMatrix()
        gl.glTranslatef(bay_x, 0.015, bay_y)
        draw_box(3.6, 0.02, 7.2, 0.14, 0.15, 0.17)
        draw_box(3.8, 0.022, 0.15, 0.95, 0.95, 0.95)
        gl.glPushMatrix()
        gl.glTranslatef(0.0, 0.0, -3.5)
        draw_box(3.8, 0.022, 0.15, 0.95, 0.95, 0.95)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(-1.8, 0.0, 0.0)
        draw_box(0.15, 0.022, 7.0, 0.95, 0.95, 0.95)
        gl.glPopMatrix()
        gl.glPushMatrix()
        gl.glTranslatef(1.8, 0.0, 0.0)
        draw_box(0.15, 0.022, 7.0, 0.95, 0.95, 0.95)
        gl.glPopMatrix()
        gl.glPopMatrix()

        # 1. Black base plate on the ground
        gl.glPushMatrix()
        gl.glTranslatef(sx, 0.04, sy)
        draw_box(1.5, 0.08, 1.5, 0.07, 0.07, 0.08)
        gl.glPopMatrix()

        # 2. Grey pedestal post / base column
        gl.glPushMatrix()
        gl.glTranslatef(sx, 0.44, sy)
        draw_box(0.50, 0.72, 0.50, 0.48, 0.50, 0.52)
        gl.glPopMatrix()

        # 3. Angled grey upper console block (slightly angled towards user)
        gl.glPushMatrix()
        gl.glTranslatef(sx, 0.88, sy)
        gl.glRotatef(-28.0, 1.0, 0.0, 0.0)
        draw_box(0.96, 0.28, 0.76, 0.40, 0.42, 0.44)
        gl.glPopMatrix()

        # 4. Bright yellow block inside that one, lifted up a little bit
        gl.glPushMatrix()
        gl.glTranslatef(sx, 1.02, sy - 0.05)
        gl.glRotatef(-28.0, 1.0, 0.0, 0.0)
        pulse = 0.88 + 0.12 * math.sin(self.sim_time * 4.0)
        draw_box(0.70, 0.14, 0.50, 0.98 * pulse, 0.82 * pulse, 0.10)
        gl.glPopMatrix()

        # 5. Miniature 3D car on top rotating gently
        gl.glPushMatrix()
        gl.glTranslatef(sx, 1.25, sy - 0.05)
        gl.glRotatef(self.sim_time * 45.0, 0.0, 1.0, 0.0)
        gl.glScalef(0.14, 0.14, 0.14)
        self._draw_mini_display_car()
        gl.glPopMatrix()

    def _draw_3d_wheel(self, wheel_r, wheel_w, is_left):
        """Draws a detailed 3D wheel: rubber tire tread, sidewalls, alloy rim, 5 spinning spokes, hub, and brake disc."""
        gl.glPushMatrix()
        half_w = wheel_w * 0.5
        rim_r = wheel_r * 0.65
        hub_r = wheel_r * 0.22
        num_seg = 14

        # 1. Outer rubber tire tread (14-segment cylinder via GL_QUADS)
        gl.glDisable(GL_TEXTURE_2D)
        gl.glColor3f(0.16, 0.16, 0.18)
        gl.glBegin(GL_QUADS)
        for i in range(num_seg):
            a0 = i * (2.0 * math.pi / num_seg)
            a1 = (i + 1) * (2.0 * math.pi / num_seg)
            c0, s0 = math.cos(a0), math.sin(a0)
            c1, s1 = math.cos(a1), math.sin(a1)
            gl.glNormal3f(0.0, (s0 + s1) * 0.5, (c0 + c1) * 0.5)
            gl.glVertex3f(-half_w, wheel_r * s0, wheel_r * c0)
            gl.glVertex3f( half_w, wheel_r * s0, wheel_r * c0)
            gl.glVertex3f( half_w, wheel_r * s1, wheel_r * c1)
            gl.glVertex3f(-half_w, wheel_r * s1, wheel_r * c1)
        gl.glEnd()

        # 2. Tire sidewalls
        gl.glColor3f(0.13, 0.13, 0.15)
        gl.glBegin(GL_QUADS)
        for side in (-half_w, half_w):
            gl.glNormal3f(-1.0 if side < 0 else 1.0, 0.0, 0.0)
            for i in range(num_seg):
                a0 = i * (2.0 * math.pi / num_seg)
                a1 = (i + 1) * (2.0 * math.pi / num_seg)
                c0, s0 = math.cos(a0), math.sin(a0)
                c1, s1 = math.cos(a1), math.sin(a1)
                gl.glVertex3f(side, rim_r * s0, rim_r * c0)
                gl.glVertex3f(side, wheel_r * s0, wheel_r * c0)
                gl.glVertex3f(side, wheel_r * s1, wheel_r * c1)
                gl.glVertex3f(side, rim_r * s1, rim_r * c1)
        gl.glEnd()

        # 3. Metallic alloy rim ring
        out_side = half_w if is_left else -half_w
        gl.glColor3f(0.80, 0.82, 0.86)
        gl.glBegin(GL_LINES)
        for i in range(num_seg):
            a0 = i * (2.0 * math.pi / num_seg)
            a1 = (i + 1) * (2.0 * math.pi / num_seg)
            gl.glVertex3f(out_side, rim_r * math.sin(a0), rim_r * math.cos(a0))
            gl.glVertex3f(out_side, rim_r * math.sin(a1), rim_r * math.cos(a1))
        gl.glEnd()

        # 4. 5 Rim Spokes (visibly spin as the wheel rolls!)
        gl.glColor3f(0.84, 0.86, 0.90)
        gl.glBegin(GL_QUADS)
        gl.glNormal3f(1.0 if is_left else -1.0, 0.0, 0.0)
        num_spokes = 5
        spoke_w = wheel_r * 0.10
        for i in range(num_spokes):
            ang = i * (2.0 * math.pi / num_spokes)
            ca = math.cos(ang)
            sa = math.sin(ang)
            pa = -sa * spoke_w * 0.5
            pb = ca * spoke_w * 0.5
            gl.glVertex3f(out_side, hub_r * sa - pa, hub_r * ca - pb)
            gl.glVertex3f(out_side, hub_r * sa + pa, hub_r * ca + pb)
            gl.glVertex3f(out_side, rim_r * sa + pa, rim_r * ca + pb)
            gl.glVertex3f(out_side, rim_r * sa - pa, rim_r * ca - pb)
        gl.glEnd()

        # 5. Center hub cap & lug nuts
        gl.glColor3f(0.24, 0.25, 0.28)
        gl.glBegin(GL_TRIANGLES)
        gl.glNormal3f(1.0 if is_left else -1.0, 0.0, 0.0)
        hub_x = out_side + (0.015 if is_left else -0.015)
        for i in range(num_seg):
            a0 = i * (2.0 * math.pi / num_seg)
            a1 = (i + 1) * (2.0 * math.pi / num_seg)
            gl.glVertex3f(hub_x, 0.0, 0.0)
            gl.glVertex3f(hub_x, hub_r * math.sin(a0), hub_r * math.cos(a0))
            gl.glVertex3f(hub_x, hub_r * math.sin(a1), hub_r * math.cos(a1))
        gl.glEnd()

        # 6. Brake rotor disc inside wheel
        in_side = 0.0
        gl.glColor3f(0.48, 0.50, 0.53)
        gl.glBegin(GL_TRIANGLES)
        disc_r = rim_r * 0.82
        for i in range(12):
            a0 = i * (2.0 * math.pi / 12)
            a1 = (i + 1) * (2.0 * math.pi / 12)
            gl.glVertex3f(in_side, 0.0, 0.0)
            gl.glVertex3f(in_side, disc_r * math.sin(a0), disc_r * math.cos(a0))
            gl.glVertex3f(in_side, disc_r * math.sin(a1), disc_r * math.cos(a1))
        gl.glEnd()

        gl.glEnable(GL_TEXTURE_2D)
        gl.glPopMatrix()

    def _render_vehicle_wheels(self, veh):
        """Renders 4 functional 3D wheels with steering angle, rolling spin, alloy rims, and rubber tires."""
        spec = veh.spec
        wb_f = spec.get("wheelbase_front", 1.45)
        wb_r = spec.get("wheelbase_rear", -1.45)
        track_w = spec.get("track_w", 1.95)
        half_track = track_w * 0.5
        wheel_r = spec.get("wheel_r", 0.38)
        wheel_w = spec.get("wheel_w", 0.26)
        yaw_off = spec.get("yaw_off", 90.0)

        # Wheel hub sits at ground height + wheel radius
        hub_z = veh.z + wheel_r

        wheel_positions = [
            ( half_track, wb_f, True,  True),   # Front Left
            (-half_track, wb_f, True,  False),  # Front Right
            ( half_track, wb_r, False, True),   # Rear Left
            (-half_track, wb_r, False, False),  # Rear Right
        ]

        steer_sign = 1.0 if yaw_off > 0 else -1.0
        steer_deg = math.degrees(getattr(veh, 'steer_angle', 0.0)) * steer_sign
        roll_deg = math.degrees(getattr(veh, 'wheel_rot', 0.0))

        gl.glPushMatrix()
        gl.glTranslatef(veh.x, hub_z, veh.y)
        gl.glRotatef(-math.degrees(veh.yaw) + yaw_off, 0.0, 1.0, 0.0)

        for lx, lz, is_front, is_left in wheel_positions:
            gl.glPushMatrix()
            gl.glTranslatef(lx, 0.0, lz)
            if is_front:
                gl.glRotatef(steer_deg, 0.0, 1.0, 0.0)
            # Wheel axle roll (spinning tires)
            gl.glRotatef(roll_deg, 1.0, 0.0, 0.0)
            self._draw_3d_wheel(wheel_r, wheel_w, is_left)
            gl.glPopMatrix()

        gl.glPopMatrix()

    def _render_seated_vehicle_driver(self, veh, driver_type='player'):
        """
        Renders a 3D character seated inside the vehicle cabin ("Sit down like", pose_mode=3)
        with hands gripping the steering wheel and legs bent on the driver's bucket seat.
        """
        spec = veh.spec
        cos_y = math.cos(veh.yaw)
        sin_y = math.sin(veh.yaw)
        # Left-hand-drive driver seat offset: slightly forward (+0.05m) and to the left (+0.36m left)
        fwd_off = 0.25 if spec.get("id") in ("cat_ct680", "semi_truck") else 0.05
        left_off = 0.36
        drv_x = veh.x + cos_y * fwd_off + sin_y * left_off
        drv_y = veh.y + sin_y * fwd_off - cos_y * left_off
        seat_elev = 0.72 if spec.get("id") in ("cat_ct680", "semi_truck") else (0.50 if spec.get("id") in ("jeep_wrangler", "mercedes_sprinter") else 0.34)
        seat_y = veh.z + getattr(veh, 'suspension_z', 0.0) + seat_elev

        gl.glPushMatrix()
        gl.glTranslatef(0.0, seat_y, 0.0)
        draw_3d_humanoid(
            drv_x, drv_y, veh.yaw,
            driver_type, getattr(self, 'sim_time', 0.0),
            False, False, False,
            weapon_id=1, pose_mode=3, weapon_drawn=False
        )
        gl.glPopMatrix()

    def _render_vehicles(self, max_draw_dist):
        """Renders all active drivable vehicles with VPhysics 3D inward mesh crumple, seated driver, suspension, and lights."""
        for veh in getattr(self, 'vehicles', []):
            if abs(veh.x - self.player_x) > max_draw_dist + 16.0 or abs(veh.y - self.player_y) > max_draw_dist + 16.0:
                continue
            dlist = self.get_vehicle_dlist(veh.id)

            # 1. Seated 3D Driver inside cabin (Player when driving, or MCPD Officer in active police cruisers)
            if getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None) is veh:
                self._render_seated_vehicle_driver(veh, driver_type='player')
            elif getattr(veh, 'is_police', False) and getattr(veh, 'siren_on', False):
                self._render_seated_vehicle_driver(veh, driver_type='mcpd')

            # 2. Vehicle Chassis with suspension bounce, acceleration squat/dive, cornering roll, and VPhysics 3D mesh crumpling
            gl.glPushMatrix()
            gl.glTranslatef(veh.x, veh.z + getattr(veh, 'suspension_z', 0.0) + veh.spec["y_off"], veh.y)
            gl.glRotatef(-math.degrees(veh.yaw) + veh.spec["yaw_off"], 0.0, 1.0, 0.0)
            if "pitch_off" in veh.spec:
                gl.glRotatef(veh.spec["pitch_off"], 1.0, 0.0, 0.0)
            if "roll_off" in veh.spec:
                gl.glRotatef(veh.spec["roll_off"], 0.0, 0.0, 1.0)
            gl.glRotatef(math.degrees(getattr(veh, 'body_pitch', 0.0)), 1.0, 0.0, 0.0)
            gl.glRotatef(math.degrees(getattr(veh, 'body_roll', 0.0)), 0.0, 0.0, 1.0)
            s = veh.spec["scale"]
            gl.glScalef(s, s, s)
            if dlist:
                c_amt = getattr(veh, 'crumple_amount', 0.0)
                c_dents = getattr(veh, 'dents', None)
                shader_bound = False
                if c_amt > 0.001 or (c_dents and len(c_dents) > 0):
                    shader_bound = bind_vphysics_crumple_shader(dlist, c_amt, c_dents)
                gl.glCallList(dlist)
                if shader_bound:
                    unbind_vphysics_crumple_shader()
            gl.glPopMatrix()

            # 3. Headlights, Brake Lights, Turn Signals & Police Emergency Lightbar Strobes
            self._render_vehicle_lights(veh)

    def _render_vehicle_lights(self, veh):
        """Renders 3D glowing headlights, tail/brake lights, blinking turn signals, and Police Red/Blue emergency lightbar strobes."""
        spec = veh.spec
        length = spec.get("length", 4.8)
        width = spec.get("width", 2.0)
        c_shrink = 1.0 - min(0.32, getattr(veh, 'crumple_amount', 0.0) * 0.32)
        half_w = width * 0.45 * c_shrink
        half_l = length * 0.48 * c_shrink
        y_pos = veh.z + getattr(veh, 'suspension_z', 0.0) + spec.get("y_off", 0.0) + 0.62
        yaw_deg = -math.degrees(veh.yaw)
        is_police = getattr(veh, 'is_police', False) or bool(spec.get('is_police', False))
        siren_active = is_police and (getattr(veh, 'siren_on', False) or getattr(self, 'wanted_level', 0) >= 1)
        sim_t = getattr(self, 'sim_time', 0.0)

        gl.glPushMatrix()
        gl.glTranslatef(veh.x, y_pos, veh.y)
        gl.glRotatef(yaw_deg, 0.0, 1.0, 0.0)
        gl.glDisable(GL_TEXTURE_2D)
        gl.glEnable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE)

        # Front Headlights (with wig-wag alternating high-beams on police cruisers when siren is active)
        if getattr(veh, 'headlights_on', True):
            wigwag = int(sim_t * 9.0) % 2
            l_alpha = (1.0 if wigwag == 0 else 0.45) if siren_active else 0.85
            r_alpha = (1.0 if wigwag == 1 else 0.45) if siren_active else 0.85
            gl.glPushMatrix()
            gl.glTranslatef(half_l, 0.0, half_w)
            draw_box(0.12, 0.12, 0.16, 1.0, 0.95, 0.85, l_alpha)
            gl.glPopMatrix()
            gl.glPushMatrix()
            gl.glTranslatef(half_l, 0.0, -half_w)
            draw_box(0.12, 0.12, 0.16, 1.0, 0.95, 0.85, r_alpha)
            gl.glPopMatrix()

        # Police Emergency Roof Lightbar Strobes (Flashing Red & Blue Halo + Grille Strobes)
        if is_police:
            strobe_phase = int(sim_t * 11.0 + (0 if getattr(veh, 'id', '') == 'crown_vic' else hash(getattr(veh, 'id', '')) % 5)) % 2
            roof_rel_y = 0.80  # 0.62 + 0.80 = 1.42m (exact roof lightbar height)
            if siren_active:
                # Active Red (Driver/Left -Z) & Blue (Passenger/Right +Z) high-intensity strobes
                red_on = (strobe_phase == 0)
                blue_on = (strobe_phase == 1)
                # Left Red Roof Dome Halo
                gl.glPushMatrix()
                gl.glTranslatef(-0.10, roof_rel_y, -0.35)
                if red_on:
                    draw_box(0.42, 0.34, 0.68, 1.0, 0.08, 0.08, 0.92)
                    draw_box(0.75, 0.55, 1.05, 1.0, 0.05, 0.05, 0.42)
                else:
                    draw_box(0.24, 0.14, 0.48, 0.55, 0.05, 0.05, 0.45)
                gl.glPopMatrix()

                # Right Blue Roof Dome Halo
                gl.glPushMatrix()
                gl.glTranslatef(-0.10, roof_rel_y, 0.35)
                if blue_on:
                    draw_box(0.42, 0.34, 0.68, 0.08, 0.38, 1.0, 0.92)
                    draw_box(0.75, 0.55, 1.05, 0.05, 0.30, 1.0, 0.42)
                else:
                    draw_box(0.24, 0.14, 0.48, 0.05, 0.18, 0.55, 0.45)
                gl.glPopMatrix()

                # Front PIT Push-Bar Red/Blue LED Grille Strobes
                gl.glPushMatrix()
                gl.glTranslatef(half_l + 0.08, -0.05, -0.26 if red_on else 0.26)
                if red_on:
                    draw_box(0.16, 0.16, 0.26, 1.0, 0.10, 0.10, 0.95)
                else:
                    draw_box(0.16, 0.16, 0.26, 0.10, 0.42, 1.0, 0.95)
                gl.glPopMatrix()

        # Rear Brake / Tail Lights
        if getattr(veh, 'brake_lights_on', False):
            # Super bright red brake lights
            gl.glColor4f(1.0, 0.08, 0.08, 0.95)
            b_size = 0.22
            gl.glPushMatrix()
            gl.glTranslatef(-half_l, 0.0, half_w)
            draw_box(0.10, b_size, b_size, 1.0, 0.08, 0.08)
            gl.glPopMatrix()
            gl.glPushMatrix()
            gl.glTranslatef(-half_l, 0.0, -half_w)
            draw_box(0.10, b_size, b_size, 1.0, 0.08, 0.08)
            gl.glPopMatrix()
        else:
            # Standard dimmed red running taillights
            gl.glColor4f(0.55, 0.04, 0.04, 0.65)
            gl.glPushMatrix()
            gl.glTranslatef(-half_l, 0.0, half_w)
            draw_box(0.08, 0.14, 0.14, 0.55, 0.04, 0.04)
            gl.glPopMatrix()
            gl.glPushMatrix()
            gl.glTranslatef(-half_l, 0.0, -half_w)
            draw_box(0.08, 0.14, 0.14, 0.55, 0.04, 0.04)
            gl.glPopMatrix()

        # Turn Signals (Blinking amber indicator lamps)
        sig = getattr(veh, 'turn_signal', 0)
        timer = getattr(veh, 'turn_signal_timer', 0.0)
        is_lit = (sig != 0) and ((timer % 0.40) < 0.22)
        if is_lit:
            gl.glColor4f(1.0, 0.72, 0.04, 0.95)
            z_side = half_w if sig == -1 else -half_w
            gl.glPushMatrix()
            gl.glTranslatef(half_l * 0.95, 0.0, z_side)
            draw_box(0.14, 0.14, 0.14, 1.0, 0.72, 0.04)
            gl.glPopMatrix()
            gl.glPushMatrix()
            gl.glTranslatef(-half_l * 0.95, 0.0, z_side)
            draw_box(0.14, 0.14, 0.14, 1.0, 0.72, 0.04)
            gl.glPopMatrix()

        gl.glDisable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(GL_TEXTURE_2D)
        gl.glPopMatrix()

    def _init_traffic_system(self):
        """Initializes distributed starter NPC traffic vehicles across Big City 5 far from spawn to eliminate startup lag."""
        self.traffic_vehicles = []
        self.traffic_id_counter = 0
        self.traffic_stream_timer = 0.0
        specs_pool = VEHICLE_CATALOG[:]

        # 8 starter vehicles distributed across distant map sectors (far from spawn at 20.5, 25.0)
        # Format: (lane_id, pos_along_lane)
        starter_spawns = [
            # Far Eastbound Highway (well east of city core)
            (0, 240.0),
            (1, 420.0),
            # Far Westbound Highway (cruising west toward the city and beyond)
            (3, 340.0),
            (4, -65.0),
            (5, 520.0),
            # Uptown Central Boulevard Northbound
            (7, -35.0),
            # Downtown West Avenue Southbound
            (8, -25.0),
            # South Promenade Crossway Eastbound
            (14, 75.0)
        ]

        for spawn_info in starter_spawns:
            lane_id = spawn_info[0]
            pos = spawn_info[1]
            # Ensure MCPD Police Interceptor Cruisers regularly patrol the streets of Big City 5
            if self.traffic_id_counter in (0, 3, 6):
                spec = next((v for v in VEHICLE_CATALOG if v["id"] == "crown_vic"), specs_pool[0])
            else:
                spec = specs_pool[self.traffic_id_counter % len(specs_pool)]
            npc = NPCTrafficVehicle(f"npc_traffic_{self.traffic_id_counter}", spec, lane_id, pos)
            self.traffic_vehicles.append(npc)
            self.traffic_id_counter += 1

        self.add_log('sys', f'[TRAFFIC CONTROL] System online. {len(self.traffic_vehicles)} distributed starter vehicles (incl. MCPD Police Cruisers) cruising Big City 5.')

    def _update_traffic_system(self, dt):
        """
        High-performance Dynamic Traffic Streaming Engine:
        - Updates active AI drivers (radar, smooth lane switching, turn signals, brake lights, red light stopping)
        - Activates police lights/sirens on MCPD Police Cruisers when pursuing or when wanted_level >= 1
        - Prunes distant (>165m) and out-of-bounds vehicles
        - Streams in new vehicles naturally ahead/around player as they navigate the map
        """
        if self.current_map != "BigCity5":
            return
        if not hasattr(self, 'traffic_vehicles') or not hasattr(self, 'traffic_id_counter'):
            self._init_traffic_system()

        p_veh = self.active_vehicle if getattr(self, 'in_vehicle', False) else None
        px, py = self.player_x, self.player_y
        sim_time = getattr(self, 'sim_time', 0.0)
        wanted = getattr(self, 'wanted_level', 0)

        # 1. Update active traffic vehicles & police cruiser pursuit sirens
        any_siren_near = False
        if p_veh and getattr(p_veh, 'is_police', False) and getattr(p_veh, 'siren_on', False):
            any_siren_near = True
        for veh in self.traffic_vehicles:
            if getattr(veh, 'is_police', False):
                if wanted >= 1:
                    veh.siren_on = True
                if veh.siren_on and math.hypot(veh.x - px, veh.y - py) < 55.0:
                    any_siren_near = True
            veh.update(dt, self.traffic_vehicles, px, py, p_veh, sim_time)

        if any_siren_near:
            self.siren_sound_timer = getattr(self, 'siren_sound_timer', 0.0) - dt
            if self.siren_sound_timer <= 0.0:
                self.siren_sound_timer = 0.72
                if hasattr(self, 'snd_police_siren') and self.snd_police_siren:
                    self.snd_police_siren.play()

        # 2. Despawn distant or finished vehicles to eliminate lag and prevent pileups
        active_traffic = []
        for veh in self.traffic_vehicles:
            dist_p = math.hypot(veh.x - px, veh.y - py)
            if veh.should_despawn or dist_p > 165.0:
                continue
            active_traffic.append(veh)
        self.traffic_vehicles = active_traffic

        # 3. Dynamic World Traffic Streaming (Target ~8-10 active vehicles around the player)
        TARGET_ACTIVE = 9
        self.traffic_stream_timer = getattr(self, 'traffic_stream_timer', 0.0) + dt
        if len(self.traffic_vehicles) < TARGET_ACTIVE and self.traffic_stream_timer > 0.8:
            self.traffic_stream_timer = 0.0

            # Determine candidate lanes based on player proximity
            candidate_lanes = []
            for lane_id, lane_info in TRAFFIC_LANES.items():
                if "y" in lane_info:
                    lat_dist = abs(lane_info["y"] - py)
                else:
                    lat_dist = abs(lane_info["x"] - px)
                # Lane is within 85m laterally of player
                if lat_dist < 85.0:
                    candidate_lanes.append(lane_id)

            if not candidate_lanes:
                candidate_lanes = list(TRAFFIC_LANES.keys())

            random.shuffle(candidate_lanes)

            for cand_id in candidate_lanes:
                lane_info = TRAFFIC_LANES[cand_id]
                b_min, b_max = lane_info.get("bounds", (-140.0, 780.0))
                is_x = lane_info["direction"] in ("+X", "-X")

                # Stream ahead of player travel / oncoming
                offset_dist = random.uniform(65.0, 115.0)
                if random.random() < 0.70:
                    # Spawn ahead in travel direction
                    if lane_info["direction"] in ("+X", "+Y"):
                        cand_pos = (px if is_x else py) + offset_dist
                    else:
                        cand_pos = (px if is_x else py) - offset_dist
                else:
                    # Spawn oncoming or trailing
                    cand_pos = (px if is_x else py) + (offset_dist if random.random() < 0.5 else -offset_dist)

                if not (b_min + 15.0 <= cand_pos <= b_max - 15.0):
                    continue

                # Safety checks: ensure candidate position is clear of player and other vehicles
                spawn_x = cand_pos if is_x else float(lane_info.get("x", 20.0))
                spawn_y = float(lane_info.get("y", 24.8)) if is_x else cand_pos

                if math.hypot(spawn_x - px, spawn_y - py) < 40.0:
                    continue

                # Check spacing from existing traffic in same corridor
                clear = True
                for other in self.traffic_vehicles:
                    if is_x:
                        if abs(other.y - spawn_y) < 2.5 and abs(other.x - spawn_x) < 26.0:
                            clear = False
                            break
                    else:
                        if abs(other.x - spawn_x) < 2.5 and abs(other.y - spawn_y) < 26.0:
                            clear = False
                            break
                if not clear:
                    continue

                # Valid clear position found! Spawn streaming vehicle (28% chance of MCPD Police Cruiser)
                if random.random() < 0.28:
                    spec = next((v for v in VEHICLE_CATALOG if v["id"] == "crown_vic"), random.choice(VEHICLE_CATALOG))
                else:
                    spec = random.choice(VEHICLE_CATALOG)
                npc = NPCTrafficVehicle(f"npc_stream_{self.traffic_id_counter}", spec, cand_id, cand_pos)
                if getattr(npc, 'is_police', False) and getattr(self, 'wanted_level', 0) >= 1:
                    npc.siren_on = True
                self.traffic_vehicles.append(npc)
                self.traffic_id_counter += 1
                break

    def _render_traffic_intersections_and_lights(self, max_draw_dist):
        """Renders 3D traffic light gantries, mast arms, animated red/yellow/green signal heads, and stop bars across the entire map."""
        sim_time = getattr(self, 'sim_time', 0.0)
        cycle = 30.0
        t = sim_time % cycle
        # EW is Green 0-13, Yellow 13-16, Red 16-30
        ew_state = 'GREEN' if t < 13.0 else ('YELLOW' if t < 16.0 else 'RED')
        # NS is Red 0-16, Green 16-27, Yellow 27-30
        ns_state = 'RED' if t < 16.0 else ('GREEN' if t < 27.0 else 'YELLOW')

        for inter in BIGCITY5_INTERSECTIONS:
            ix, iy = inter["x"], inter["y"]
            if abs(ix - self.player_x) > max_draw_dist + 25.0 or abs(iy - self.player_y) > max_draw_dist + 25.0:
                continue
            itype = inter.get("type", "highway")
            if itype == "highway":
                # Eastbound approach gantry (mast on south shoulder, arm reaches across EB lanes, facing West toward oncoming traffic)
                draw_3d_traffic_light_gantry(ix - 5.0, iy + 2.0, -90.0, state_ew=ew_state, state_ns=ns_state)
                # Westbound approach gantry (mast on north shoulder, arm reaches across WB lanes, facing East toward oncoming traffic)
                draw_3d_traffic_light_gantry(ix + 5.0, iy - 2.0, 90.0, state_ew=ew_state, state_ns=ns_state)
            else:
                # City Cross intersection: Boulevard approaches (Northbound and Southbound) with crossway signals
                draw_3d_traffic_light_gantry(ix, iy - 4.0, 180.0, state_ew=ns_state, state_ns=ew_state)
                draw_3d_traffic_light_gantry(ix, iy + 4.0, 0.0, state_ew=ns_state, state_ns=ew_state)

    def _render_street_and_speed_signs(self, max_draw_dist):
        """Renders 3D regulatory speed limit signs (200, 60, 50, 20 km/h) and stop signs along Big City 5 roads."""
        for sign in BIGCITY5_ROAD_SIGNS:
            sx, sy, sz = sign["x"], sign["y"], sign.get("z", 0.0)
            if abs(sx - self.player_x) > max_draw_dist + 15.0 or abs(sy - self.player_y) > max_draw_dist + 15.0:
                continue
            yaw = sign.get("yaw", 0.0)
            stype = sign.get("type", "speed")
            if stype == "speed":
                draw_3d_speed_sign(sx, sz, sy, yaw, sign.get("val", 60))
            elif stype == "stop":
                draw_3d_stop_sign(sx, sz, sy, yaw)

    def _render_traffic_vehicles(self, max_draw_dist):
        """Renders NPC traffic vehicles with seated 3D drivers, VPhysics 3D mesh crumpling, headlights, brake lights, and police strobes."""
        for veh in getattr(self, 'traffic_vehicles', []):
            if abs(veh.x - self.player_x) > max_draw_dist + 20.0 or abs(veh.y - self.player_y) > max_draw_dist + 20.0:
                continue
            dlist = self.get_vehicle_dlist(veh.spec["id"])
            spec = veh.spec

            # 1. Seated 3D NPC Driver inside cabin (MCPD Officer in police cruisers, Citizen in civilian vehicles)
            drv_type = 'mcpd' if getattr(veh, 'is_police', False) else 'civilian'
            self._render_seated_vehicle_driver(veh, driver_type=drv_type)

            # 2. Chassis with authentic 3D model wheels & VPhysics 3D inward mesh crumple
            gl.glPushMatrix()
            gl.glTranslatef(veh.x, veh.z + getattr(veh, 'suspension_z', 0.0) + spec["y_off"], veh.y)
            gl.glRotatef(-math.degrees(veh.yaw) + spec["yaw_off"], 0.0, 1.0, 0.0)
            if "pitch_off" in spec:
                gl.glRotatef(spec["pitch_off"], 1.0, 0.0, 0.0)
            if "roll_off" in spec:
                gl.glRotatef(spec["roll_off"], 0.0, 0.0, 1.0)
            gl.glRotatef(math.degrees(getattr(veh, 'body_pitch', 0.0)), 1.0, 0.0, 0.0)
            gl.glRotatef(math.degrees(getattr(veh, 'body_roll', 0.0)), 0.0, 0.0, 1.0)
            s = spec["scale"]
            gl.glScalef(s, s, s)
            if dlist:
                c_amt = getattr(veh, 'crumple_amount', 0.0)
                c_dents = getattr(veh, 'dents', None)
                shader_bound = False
                if c_amt > 0.001 or (c_dents and len(c_dents) > 0):
                    shader_bound = bind_vphysics_crumple_shader(dlist, c_amt, c_dents)
                gl.glCallList(dlist)
                if shader_bound:
                    unbind_vphysics_crumple_shader()
            gl.glPopMatrix()

            # 3. Headlights, Brake Lights, Turn Signals & Police Emergency Lightbar Strobes
            self._render_vehicle_lights(veh)

    def _render_offroad_dirt_zones(self, max_draw_dist):
        """Renders 3D undulating off-road dirt proving grounds with rolling mounds, jumps, and mud ruts."""
        if not hasattr(self, 'world_textures'):
            return
        tex_dirt = self.world_textures.get('dirt_offroad', 0)
        if not tex_dirt:
            return

        gl.glEnable(GL_TEXTURE_2D)
        gl.glEnable(GL_DEPTH_TEST)
        gl.glBindTexture(GL_TEXTURE_2D, tex_dirt)

        # 1. East Off-Road Proving Grounds: X in [36.0, 125.0], Y in [-22.0, 78.0]
        if abs(80.0 - self.player_x) <= max_draw_dist + 65.0 and abs(28.0 - self.player_y) <= max_draw_dist + 65.0:
            gl.glBegin(GL_QUADS)
            step = 2.5
            x_steps = int((125.0 - 36.0) / step)
            y_steps = int((78.0 - (-22.0)) / step)
            for xi in range(x_steps):
                x0 = 36.0 + xi * step
                x1 = x0 + step
                u0 = xi * 0.45
                u1 = u0 + 0.45
                for yi in range(y_steps):
                    y0 = -22.0 + yi * step
                    y1 = y0 + step
                    v0 = yi * 0.45
                    v1 = v0 + 0.45

                    z00 = get_offroad_elevation(x0, y0)
                    z10 = get_offroad_elevation(x1, y0)
                    z11 = get_offroad_elevation(x1, y1)
                    z01 = get_offroad_elevation(x0, y1)

                    dzdx = (z10 - z00) / step
                    dzdy = (z01 - z00) / step
                    nx, ny, nz = -dzdx, 1.0, -dzdy
                    mag = math.sqrt(nx*nx + ny*ny + nz*nz)
                    nx, ny, nz = nx/mag, ny/mag, nz/mag
                    gl.glNormal3f(nx, ny, nz)

                    shade = 0.92 + 0.08 * math.sin(x0 * 0.2 + y0 * 0.3)
                    gl.glColor3f(shade, shade * 0.96, shade * 0.90)

                    gl.glTexCoord2f(u0, v0); gl.glVertex3f(x0, z00, y0)
                    gl.glTexCoord2f(u1, v0); gl.glVertex3f(x1, z10, y0)
                    gl.glTexCoord2f(u1, v1); gl.glVertex3f(x1, z11, y1)
                    gl.glTexCoord2f(u0, v1); gl.glVertex3f(x0, z01, y1)
            gl.glEnd()

        # 2. West Trail Course: X in [-72.0, -12.0], Y in [-18.0, 65.0]
        if abs(-42.0 - self.player_x) <= max_draw_dist + 55.0 and abs(23.0 - self.player_y) <= max_draw_dist + 55.0:
            gl.glBegin(GL_QUADS)
            step = 2.5
            x_steps = int((-12.0 - (-72.0)) / step)
            y_steps = int((65.0 - (-18.0)) / step)
            for xi in range(x_steps):
                x0 = -72.0 + xi * step
                x1 = x0 + step
                u0 = xi * 0.45
                u1 = u0 + 0.45
                for yi in range(y_steps):
                    y0 = -18.0 + yi * step
                    y1 = y0 + step
                    v0 = yi * 0.45
                    v1 = v0 + 0.45

                    z00 = get_offroad_elevation(x0, y0)
                    z10 = get_offroad_elevation(x1, y0)
                    z11 = get_offroad_elevation(x1, y1)
                    z01 = get_offroad_elevation(x0, y1)

                    dzdx = (z10 - z00) / step
                    dzdy = (z01 - z00) / step
                    nx, ny, nz = -dzdx, 1.0, -dzdy
                    mag = math.sqrt(nx*nx + ny*ny + nz*nz)
                    nx, ny, nz = nx/mag, ny/mag, nz/mag
                    gl.glNormal3f(nx, ny, nz)

                    shade = 0.88 + 0.10 * math.cos(x0 * 0.25 - y0 * 0.2)
                    gl.glColor3f(shade, shade * 0.94, shade * 0.88)

                    gl.glTexCoord2f(u0, v0); gl.glVertex3f(x0, z00, y0)
                    gl.glTexCoord2f(u1, v0); gl.glVertex3f(x1, z10, y0)
                    gl.glTexCoord2f(u1, v1); gl.glVertex3f(x1, z11, y1)
                    gl.glTexCoord2f(u0, v1); gl.glVertex3f(x0, z01, y1)
            gl.glEnd()

        # 3. Wooden trail marker posts along off-road perimeters
        marker_posts = [
            (38.0, 0.0), (38.0, 25.0), (38.0, 50.0), (65.0, 25.0), (95.0, 10.0), (95.0, 40.0),
            (-14.0, 0.0), (-14.0, 30.0), (-45.0, 15.0)
        ]
        gl.glDisable(GL_TEXTURE_2D)
        for mx, my in marker_posts:
            if abs(mx - self.player_x) <= max_draw_dist + 5.0 and abs(my - self.player_y) <= max_draw_dist + 5.0:
                mz = get_offroad_elevation(mx, my)
                gl.glPushMatrix()
                gl.glTranslatef(mx, mz + 0.6, my)
                draw_box(0.14, 1.2, 0.14, 0.55, 0.38, 0.22)
                gl.glTranslatef(0.0, 0.45, 0.0)
                draw_box(0.35, 0.16, 0.18, 0.95, 0.45, 0.15)
                gl.glPopMatrix()
        gl.glEnable(GL_TEXTURE_2D)
        gl.glBindTexture(GL_TEXTURE_2D, 0)

    def _render_static_broken_down_crown_vic(self, max_draw_dist):
        """Renders static damaged Ford Crown Victoria pulled over on the road shoulder with hazard flashers."""
        cv_dlist = self.get_vehicle_dlist('crown_vic_wreck')
        if not cv_dlist:
            return
        px, py = 12.5, 32.0
        if abs(px - self.player_x) > max_draw_dist + 15.0 or abs(py - self.player_y) > max_draw_dist + 15.0:
            return

        gl.glPushMatrix()
        # Lowered cleanly onto asphalt pavement: y = -0.03
        gl.glTranslatef(px, -0.03, py)
        gl.glRotatef(15.0 + 90.0, 0.0, 1.0, 0.0)
        s = 1.30
        gl.glScalef(s, s, s)
        gl.glCallList(cv_dlist)
        gl.glPopMatrix()

        # Blinking amber hazard warning flashers
        hazard_on = (int(self.sim_time * 2.2) % 2 == 0)
        if hazard_on:
            cos_a = math.cos(math.radians(15.0))
            sin_a = math.sin(math.radians(15.0))
            flasher_corners = [
                ( 0.85,  2.25, 0.52),
                (-0.85,  2.25, 0.52),
                ( 0.85, -2.25, 0.58),
                (-0.85, -2.25, 0.58),
            ]
            gl.glDisable(GL_TEXTURE_2D)
            gl.glDisable(GL_LIGHTING)
            gl.glColor3f(1.0, 0.65, 0.10)
            for lx, ly, lz in flasher_corners:
                wx = px + lx * cos_a - ly * sin_a
                wy = py + lx * sin_a + ly * cos_a
                gl.glPushMatrix()
                gl.glTranslatef(wx, lz, wy)
                draw_box(0.14, 0.08, 0.14, 1.0, 0.65, 0.10)
                gl.glPopMatrix()
            gl.glEnable(GL_TEXTURE_2D)

    def _render_bigcity5_proper_city_buildings(self, max_draw_dist):
        """Renders modern skyscrapers and commercial towers along North Boulevard, West Avenue, and East District."""
        if not hasattr(self, 'world_textures'):
            return
        tex_sky = self.world_textures.get('bigcity_skyscraper', 0)
        tex_neoclass = self.world_textures.get('c17_neoclassical', 0)
        tex_sidewalk = self.world_textures.get('concrete_sidewalk', 0)
        tex_fac12 = self.world_textures.get('c17_facade_12', 0)

        gl.glEnable(GL_TEXTURE_2D)
        gl.glEnable(GL_DEPTH_TEST)

        for b in BIGCITY5_OFFROAD_BUILDINGS:
            bx, by = b["x"], b["y"]
            bw, bd, bh = b["w"], b["d"], b["h"]
            if abs(bx - self.player_x) > max_draw_dist + bw + 20.0 or abs(by - self.player_y) > max_draw_dist + bd + 20.0:
                continue

            style = b.get("style", "glass_skyscraper")
            tint = b.get("tint", (0.9, 0.9, 0.95))

            # 1. Concrete sidewalk plaza surrounding the building
            gl.glBindTexture(GL_TEXTURE_2D, tex_sidewalk)
            gl.glColor3f(0.85, 0.85, 0.82)
            gl.glPushMatrix()
            gl.glTranslatef(bx, 0.02, by)
            draw_box(bw + 6.0, 0.04, bd + 6.0, 0.85, 0.85, 0.82)
            gl.glPopMatrix()

            # 2. Main High-Rise Building Tower
            tex_use = tex_sky if "glass" in style else (tex_neoclass if "neoclassical" in style else tex_fac12)
            gl.glBindTexture(GL_TEXTURE_2D, tex_use)

            half_w = bw * 0.5
            half_d = bd * 0.5
            u_tile = bw / 6.0
            v_tile = bh / 6.0
            u_tile_d = bd / 6.0

            gl.glColor3f(tint[0], tint[1], tint[2])
            gl.glBegin(GL_QUADS)
            # South wall (+y)
            gl.glNormal3f(0, 0, 1)
            gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(bx - half_w, 0.0, by + half_d)
            gl.glTexCoord2f(u_tile, 0.0); gl.glVertex3f(bx + half_w, 0.0, by + half_d)
            gl.glTexCoord2f(u_tile, v_tile); gl.glVertex3f(bx + half_w, bh, by + half_d)
            gl.glTexCoord2f(0.0, v_tile); gl.glVertex3f(bx - half_w, bh, by + half_d)

            # North wall (-y)
            gl.glNormal3f(0, 0, -1)
            gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(bx + half_w, 0.0, by - half_d)
            gl.glTexCoord2f(u_tile, 0.0); gl.glVertex3f(bx - half_w, 0.0, by - half_d)
            gl.glTexCoord2f(u_tile, v_tile); gl.glVertex3f(bx - half_w, bh, by - half_d)
            gl.glTexCoord2f(0.0, v_tile); gl.glVertex3f(bx + half_w, bh, by - half_d)

            # East wall (+x)
            gl.glNormal3f(1, 0, 0)
            gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(bx + half_w, 0.0, by + half_d)
            gl.glTexCoord2f(u_tile_d, 0.0); gl.glVertex3f(bx + half_w, 0.0, by - half_d)
            gl.glTexCoord2f(u_tile_d, v_tile); gl.glVertex3f(bx + half_w, bh, by - half_d)
            gl.glTexCoord2f(0.0, v_tile); gl.glVertex3f(bx + half_w, bh, by + half_d)

            # West wall (-x)
            gl.glNormal3f(-1, 0, 0)
            gl.glTexCoord2f(0.0, 0.0); gl.glVertex3f(bx - half_w, 0.0, by - half_d)
            gl.glTexCoord2f(u_tile_d, 0.0); gl.glVertex3f(bx - half_w, 0.0, by + half_d)
            gl.glTexCoord2f(u_tile_d, v_tile); gl.glVertex3f(bx - half_w, bh, by + half_d)
            gl.glTexCoord2f(0.0, v_tile); gl.glVertex3f(bx - half_w, bh, by - half_d)
            gl.glEnd()

            # 3. Ground floor illuminated storefront lobby
            gl.glDisable(GL_TEXTURE_2D)
            gl.glPushMatrix()
            gl.glTranslatef(bx, 1.8, by + half_d + 0.05)
            draw_box(bw * 0.75, 2.6, 0.15, 0.98, 0.88, 0.65)
            gl.glPopMatrix()

            # 4. Rooftop Penthouse & HVAC Chiller Units
            gl.glPushMatrix()
            gl.glTranslatef(bx, bh + 1.2, by)
            draw_box(bw * 0.45, 2.4, bd * 0.45, 0.35, 0.38, 0.42)
            gl.glTranslatef(0.0, 3.5, 0.0)
            draw_box(0.25, 5.0, 0.25, 0.85, 0.25, 0.20)
            gl.glPopMatrix()

            # 5. Sidewalk Trees along the street frontage
            for tx in (-half_w - 1.5, half_w + 1.5):
                gl.glPushMatrix()
                gl.glTranslatef(bx + tx, 1.2, by + half_d + 2.0)
                draw_box(0.22, 2.4, 0.22, 0.38, 0.26, 0.18)
                gl.glTranslatef(0.0, 1.8, 0.0)
                draw_box(1.8, 1.8, 1.8, 0.22, 0.55, 0.25)
                gl.glPopMatrix()

            gl.glEnable(GL_TEXTURE_2D)

    def _render_bigcity5_scene(self, max_draw_dist):
        """Renders 3D infrastructure, proper off-road city buildings, off-road dirt sections, roadside breakdown prop, and vehicles."""
        # 1. Foundation 3D Infrastructure Map (city_infrastructure_map_3.glb)
        if not getattr(self, 'city_infra_dlist', 0):
            self.city_infra_dlist = load_glb_to_display_list("city_infrastructure_map_3.glb")
        if self.city_infra_dlist:
            gl.glPushMatrix()
            gl.glTranslatef(439.0, 1.3, 269.0)
            gl.glCallList(self.city_infra_dlist)
            gl.glPopMatrix()

        # 2. 3D Off-Road Dirt Proving Grounds with rolling mounds & bumps
        self._render_offroad_dirt_zones(max_draw_dist)

        # 3. Proper Modern City Buildings (Safely off-road along North Boulevard, West Avenue, and East District)
        self._render_bigcity5_proper_city_buildings(max_draw_dist)

        # 4. Static Damaged Crown Victoria (Roadside breakdown prop on the shoulder with hazard flashers)
        self._render_static_broken_down_crown_vic(max_draw_dist)

        # 5. 3D Car Spawner Kiosk & Parking Lot (at 15.2, 32.0)
        if abs(16.5 - self.player_x) <= max_draw_dist + 10.0 and abs(32.0 - self.player_y) <= max_draw_dist + 10.0:
            self._render_3d_car_spawner_kiosk(15.2, 32.0, bay_x=18.0, bay_y=32.0)

        # 6. 3D Traffic Light Gantries & Signals at every intersection
        self._render_traffic_intersections_and_lights(max_draw_dist)

        # 7. 3D Regulatory Street Signs (Highway 200 km/h, Main Road 60/50 km/h, Parking 20/10 km/h, Stop signs)
        self._render_street_and_speed_signs(max_draw_dist)

        # 8. NPC Traffic Vehicles (Multi-lane highway & boulevard drivers with signals & brake lights)
        self._render_traffic_vehicles(max_draw_dist)

        # 9. Drivable Vehicles in Big City 5
        self._render_vehicles(max_draw_dist)

    def _render_driving_test_scene(self, max_draw_dist):
        """Renders dedicated highway infrastructure (city_infrastructure_map_3.glb), off-road dirt zones, car spawner kiosk, and vehicles."""
        # 1. Foundation 3D Highway Infrastructure Map (city_infrastructure_map_3.glb)
        if not getattr(self, 'city_infra_dlist', 0):
            self.city_infra_dlist = load_glb_to_display_list("city_infrastructure_map_3.glb")
        if self.city_infra_dlist:
            gl.glPushMatrix()
            gl.glTranslatef(439.0, 1.3, 269.0)
            gl.glCallList(self.city_infra_dlist)
            gl.glPopMatrix()

        # 2. 3D Off-Road Dirt Proving Grounds with rolling mounds & bumps
        self._render_offroad_dirt_zones(max_draw_dist)

        # 3. 3D Street Signs & Speed Limits (200 km/h highway speed limits)
        self._render_street_and_speed_signs(max_draw_dist)

        # 4. 3D Car Spawner Kiosk at (20.5, 23.5) with parking bay at (23.5, 23.5)
        if abs(20.5 - self.player_x) <= max_draw_dist + 10.0 and abs(23.5 - self.player_y) <= max_draw_dist + 10.0:
            self._render_3d_car_spawner_kiosk(20.5, 23.5, bay_x=23.5, bay_y=23.5)

        # 5. Drivable Vehicles
        self._render_vehicles(max_draw_dist)

    def _update_player_driving(self, dt, keys):
        """Updates vehicle physics, steering, acceleration, braking, suspension and collisions for the active vehicle."""
        veh = self.active_vehicle
        if not veh:
            return

        accel_input = 0.0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            accel_input = 1.0
            if veh.speed < -0.5:
                veh.speed += veh.brake * dt
            else:
                veh.speed = min(veh.max_speed, veh.speed + veh.accel * dt)
            veh.gear = "D"
        elif keys[pygame.K_s] or keys[pygame.K_DOWN]:
            accel_input = -1.0
            if veh.speed > 0.5:
                veh.speed = max(0.0, veh.speed - veh.brake * dt)
            else:
                rev_max = veh.max_speed * 0.38
                veh.speed = max(-rev_max, veh.speed - (veh.accel * 0.7) * dt)
                veh.gear = "R"
        else:
            if veh.speed > 0:
                veh.speed = max(0.0, veh.speed - 4.5 * dt)
            elif veh.speed < 0:
                veh.speed = min(0.0, veh.speed + 4.5 * dt)
            if abs(veh.speed) < 0.1:
                veh.speed = 0.0
                veh.gear = "P"

        if keys[pygame.K_SPACE]:
            veh.speed *= max(0.0, 1.0 - 12.0 * dt)
            if abs(veh.speed) < 0.2:
                veh.speed = 0.0

        # Brake lights logic
        veh.brake_lights_on = ((keys[pygame.K_s] or keys[pygame.K_DOWN]) and veh.speed > 0.4) or keys[pygame.K_SPACE]

        # Steering input
        turn_input = 0.0
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            turn_input -= 1.0
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            turn_input += 1.0

        # Player vehicle turn signals: disabled automatic blinking on steering
        veh.turn_signal = 0
        veh.turn_signal_timer = 0.0

        # Smooth steering rack angle animation (wheels turn smoothly to +/- 30 deg)
        max_steer = 0.52  # ~30 degrees
        target_steer = turn_input * max_steer
        veh.steer_angle += (target_steer - veh.steer_angle) * min(1.0, 10.0 * dt)

        # Wheel rolling spin animation (proportional to distance travelled)
        wheel_radius = veh.spec.get("wheel_r", 0.38)
        veh.wheel_rot += (veh.speed / wheel_radius) * dt

        # Vehicle turning yaw
        if abs(veh.speed) > 0.1:
            speed_ratio = min(1.0, abs(veh.speed) / veh.max_speed)
            sens = veh.turn_rate * (1.25 - 0.45 * speed_ratio)
            direction = 1.0 if veh.speed >= 0 else -1.0
            veh.yaw += turn_input * sens * direction * dt

        # Translation
        cos_y = math.cos(veh.yaw)
        sin_y = math.sin(veh.yaw)
        nx = veh.x + cos_y * veh.speed * dt
        ny = veh.y + sin_y * veh.speed * dt

        v_rad = veh.spec["width"] * 0.45
        half_l = veh.spec["length"] * 0.48
        if not self.is_position_blocked_for_vehicle(nx, ny, v_rad):
            veh.x = nx
            veh.y = ny
        else:
            impact_spd = abs(veh.speed)
            if impact_spd > 1.8:
                self.screen_shake = max(self.screen_shake, min(0.45, impact_spd * 0.025))
                if hasattr(self, 'snd_metal') and self.snd_metal:
                    self.snd_metal.play()
                # VPhysics 3D Mesh Inward Crumple at the front or rear bumper impact point!
                dir_sign = 1.0 if veh.speed >= 0 else -1.0
                hit_wx = veh.x + cos_y * (half_l * dir_sign) + sin_y * random.uniform(-0.35, 0.35)
                hit_wy = veh.y + sin_y * (half_l * dir_sign) - cos_y * random.uniform(-0.35, 0.35)
                sev = min(0.85, max(0.22, impact_spd / 22.0))
                if hasattr(veh, 'apply_impact_damage'):
                    veh.apply_impact_damage(hit_wx, hit_wy, severity=sev, hit_h=0.04)
                self.add_log('combat', f'[VPHYSICS CRASH] {veh.name} chassis crumpled inwards ({int(veh.crumple_amount * 100)}% deformation)!')
            veh.speed = -veh.speed * 0.25

        # Vehicle-to-Vehicle Collisions (Drivable & NPC Traffic Vehicles) with VPhysics Inward Crumpling!
        other_vehs = [ov for ov in getattr(self, 'vehicles', []) if ov is not veh] + list(getattr(self, 'traffic_vehicles', []))
        for ov in other_vehs:
            dx_v = ov.x - veh.x
            dy_v = ov.y - veh.y
            dist_v = math.hypot(dx_v, dy_v)
            min_sep = (veh.spec["width"] + ov.spec["width"]) * 0.52
            if 0.01 < dist_v < min_sep:
                nx_c = dx_v / dist_v
                ny_c = dy_v / dist_v
                overlap = min_sep - dist_v
                veh.x -= nx_c * overlap * 0.5
                veh.y -= ny_c * overlap * 0.5
                ov.x += nx_c * overlap * 0.5
                ov.y += ny_c * overlap * 0.5

                rel_spd = abs(veh.speed - getattr(ov, 'speed', 0.0))
                if rel_spd > 1.5:
                    mid_x = (veh.x + ov.x) * 0.5
                    mid_y = (veh.y + ov.y) * 0.5
                    sev = min(0.80, max(0.24, rel_spd / 20.0))
                    if hasattr(veh, 'apply_impact_damage'):
                        veh.apply_impact_damage(mid_x, mid_y, severity=sev, hit_h=0.05)
                    if hasattr(ov, 'apply_impact_damage'):
                        ov.apply_impact_damage(mid_x, mid_y, severity=sev, hit_h=0.05)
                    if getattr(ov, 'is_police', False):
                        ov.siren_on = True
                        if getattr(self, 'wanted_level', 0) < 1:
                            self.wanted_level = 1
                            self.add_log('warn', '[MCPD PURSUIT] Rammed MCPD Police Interceptor — Siren & Lights Activated!')
                    self.screen_shake = max(self.screen_shake, min(0.45, rel_spd * 0.025))
                    if hasattr(self, 'snd_metal') and self.snd_metal:
                        self.snd_metal.play()
                veh.speed *= 0.45

        # 3D Terrain Elevation & Off-road bumps
        target_ground_z = get_offroad_elevation(veh.x, veh.y)
        dz = target_ground_z - veh.z
        veh.z = target_ground_z
        veh.on_dirt = (target_ground_z > 0.02 or (36.0 <= veh.x <= 125.0 and -22.0 <= veh.y <= 78.0) or (-72.0 <= veh.x <= -12.0 and -18.0 <= veh.y <= 65.0))

        # Harmonic Spring-Damper Suspension Physics
        k_spring = 48.0   # spring stiffness
        c_damper = 9.5    # damping coefficient
        spring_force = -k_spring * veh.suspension_z - c_damper * veh.suspension_vz
        if abs(dz) > 0.005:
            spring_force += (dz / max(0.001, dt)) * 0.45
        veh.suspension_vz += spring_force * dt
        veh.suspension_z += veh.suspension_vz * dt
        veh.suspension_z = max(-0.25, min(0.25, veh.suspension_z))

        # Dynamic Body Pitch (acceleration squat & braking dive)
        target_pitch = 0.0
        if accel_input > 0 and veh.speed >= 0:
            target_pitch = -0.045 * (abs(veh.speed) / veh.max_speed)
        elif accel_input < 0 or (keys[pygame.K_SPACE] and abs(veh.speed) > 1.0):
            target_pitch = 0.075 * min(1.0, abs(veh.speed) / 10.0)
        veh.body_pitch += (target_pitch - veh.body_pitch) * min(1.0, 7.5 * dt)

        # Dynamic Body Roll (centrifugal cornering lean)
        speed_factor = min(1.0, abs(veh.speed) / (veh.max_speed * 0.6))
        target_roll = -turn_input * speed_factor * 0.065
        veh.body_roll += (target_roll - veh.body_roll) * min(1.0, 8.0 * dt)

        if abs(veh.speed) > 3.0:
            for e in self.entities:
                if getattr(e, 'alive', False) and not isinstance(e, Civilian):
                    if math.hypot(e.x - veh.x, e.y - veh.y) < (v_rad + 0.8):
                        dmg = int(abs(veh.speed) * 4.5)
                        e.take_damage(dmg, self)
                        self.add_log('combat', f'[VEHICLE RAM] Splattered {e.type} for {dmg} damage!')
                        if hasattr(self, 'snd_combine_hit'):
                            self.snd_combine_hit.play()

        self.player_x = veh.x
        self.player_y = veh.y
        self.player_z = veh.z + veh.suspension_z
        self.player_angle = veh.yaw
        self.is_moving = False
        self.is_sprinting = False
        self.step_timer = 0.0


    def blit_hud_overlay_to_opengl(self):
        """Uploads self.hud_surf to OpenGL texture without CPU vertical buffer copy and draws 2D overlay."""
        raw_data = pygame.image.tostring(self.hud_surf, "RGBA", False)
        gl.glDisable(GL_DEPTH_TEST)
        gl.glDisable(GL_FOG)
        gl.glDisable(GL_LIGHTING)

        gl.glMatrixMode(GL_PROJECTION)
        gl.glLoadIdentity()
        gl.glOrtho(0.0, SCREEN_W, 0.0, SCREEN_H, -1.0, 1.0)

        gl.glMatrixMode(GL_MODELVIEW)
        gl.glLoadIdentity()

        gl.glEnable(GL_BLEND)
        gl.glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

        gl.glEnable(GL_TEXTURE_2D)
        gl.glBindTexture(GL_TEXTURE_2D, self.hud_tex_id)
        gl.glTexSubImage2D(GL_TEXTURE_2D, 0, 0, 0, SCREEN_W, SCREEN_H, GL_RGBA, GL_UNSIGNED_BYTE, raw_data)

        gl.glColor4f(1.0, 1.0, 1.0, 1.0)
        gl.glBegin(GL_QUADS)
        gl.glTexCoord2f(0.0, 1.0); gl.glVertex2f(0.0, 0.0)
        gl.glTexCoord2f(1.0, 1.0); gl.glVertex2f(SCREEN_W, 0.0)
        gl.glTexCoord2f(1.0, 0.0); gl.glVertex2f(SCREEN_W, SCREEN_H)
        gl.glTexCoord2f(0.0, 0.0); gl.glVertex2f(0.0, SCREEN_H)
        gl.glEnd()

        gl.glDisable(GL_TEXTURE_2D)
        gl.glDisable(GL_BLEND)

    # ═══════════════════════════════════════════════
    #  AUTHENTIC HALF-LIFE 2 HEV HUD, MINIMAP & MENUS
    # ═══════════════════════════════════════════════
    def render_hud(self, surf):
        w, h = surf.get_size()
        HL2_AMBER = (255, 176, 0)
        HL2_AMBER_DIM = (180, 120, 0)
        HL2_RED = (255, 48, 32)
        HL2_BG = (12, 14, 10, 155)

        # Source Engine Water Immersion Overlay when wading/swimming in water
        if getattr(self, 'player_in_water', False):
            water_tint = pygame.Surface((w, h), pygame.SRCALPHA)
            submerged_alpha = 65 if self.player_z < -0.22 else 28
            water_tint.fill((18, 95, 135, submerged_alpha))
            surf.blit(water_tint, (0, 0))

        def draw_hl2_box(bx, by, bw, bh, border_col=None):
            box_s = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pygame.draw.rect(box_s, HL2_BG, (0, 0, bw, bh), border_radius=8)
            if border_col:
                pygame.draw.rect(box_s, (*border_col, 140), (0, 0, bw, bh), 1, border_radius=8)
            surf.blit(box_s, (bx, by))

        # ── 1. Reticle: Map Editor Yellow Precision Indicator vs Tactical HL2 Crosshair ──
        if getattr(self, 'map_editor_active', False):
            cx, cy = w // 2, h // 2
            self._update_editor_cursor()
            target_idx = getattr(self, 'editor_targeted_prop_idx', None)

            # High-visibility Pointy Yellow Indicator with dark contrast outline
            COL_YELLOW = (255, 235, 10)
            COL_AMBER = (255, 170, 20)
            COL_DARK = (15, 15, 0)
            tip_col = COL_AMBER if target_idx is not None else COL_YELLOW

            # Sharp pointy downward pointer triangle pointing exactly at (cx, cy)
            tip = (cx, cy)
            p_left = (cx - 7, cy - 15)
            p_right = (cx + 7, cy - 15)

            # Dark high-contrast silhouette
            pygame.draw.polygon(surf, COL_DARK, [(cx, cy + 3), (cx - 9, cy - 17), (cx + 9, cy - 17)])
            pygame.draw.polygon(surf, tip_col, [tip, p_left, p_right])

            # Center precision dot
            pygame.draw.circle(surf, COL_DARK, (cx, cy), 3)
            pygame.draw.circle(surf, (255, 255, 255), (cx, cy), 1)

            # Surrounding CAD precision reticle ticks
            pygame.draw.line(surf, tip_col, (cx - 16, cy), (cx - 4, cy), 2)
            pygame.draw.line(surf, tip_col, (cx + 4, cy), (cx + 16, cy), 2)
            pygame.draw.line(surf, tip_col, (cx, cy + 4), (cx, cy + 14), 2)

            if target_idx is not None and 0 <= target_idx < len(self.placed_objects):
                t_obj = self.placed_objects[target_idx]
                t_name = str(t_obj.get("type", "prop")).upper()
                ox = float(t_obj.get("x", 0.0))
                oy = float(t_obj.get("y", 0.0))
                oz = float(t_obj.get("z", 0.0))

                # Corner lock-on brackets [   ] around cursor
                b_size = 22
                b_col = (255, 190, 30)
                # Top-left
                pygame.draw.lines(surf, b_col, False, [(cx - b_size, cy - b_size + 7), (cx - b_size, cy - b_size), (cx - b_size + 7, cy - b_size)], 2)
                # Top-right
                pygame.draw.lines(surf, b_col, False, [(cx + b_size - 7, cy - b_size), (cx + b_size, cy - b_size), (cx + b_size, cy - b_size + 7)], 2)
                # Bottom-left
                pygame.draw.lines(surf, b_col, False, [(cx - b_size, cy + b_size - 7), (cx - b_size, cy + b_size), (cx - b_size + 7, cy + b_size)], 2)
                # Bottom-right
                pygame.draw.lines(surf, b_col, False, [(cx + b_size - 7, cy + b_size), (cx + b_size, cy + b_size), (cx + b_size, cy + b_size - 7)], 2)

                # Floating pill badge under cursor
                badge_text = f"TARGET LOCKED: #{target_idx+1} {t_name} ({ox:.1f}, {oy:.1f}, z={oz:.1f}) — [RMB / DEL] DELETE"
                b_surf = self.font_console.render(badge_text, True, (255, 240, 140))
                bg_w, bg_h = b_surf.get_width() + 16, b_surf.get_height() + 8
                s_bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                s_bg.fill((16, 12, 6, 220))
                pygame.draw.rect(s_bg, (255, 160, 20), (0, 0, bg_w, bg_h), 1, border_radius=4)
                surf.blit(s_bg, (cx - bg_w // 2, cy + 26))
                surf.blit(b_surf, (cx - bg_w // 2 + 8, cy + 30))
            else:
                cat, val, label = MAP_EDITOR_PALETTE[self.editor_idx % len(MAP_EDITOR_PALETTE)]
                tz = getattr(self, 'editor_target_z', 0.0)
                badge_text = f"SURFACE: ({self.editor_target_x:.1f}, {self.editor_target_y:.1f}, z={tz:.1f}) — [LMB] PLACE {label}"
                b_surf = self.font_console.render(badge_text, True, (210, 240, 255))
                bg_w, bg_h = b_surf.get_width() + 16, b_surf.get_height() + 8
                s_bg = pygame.Surface((bg_w, bg_h), pygame.SRCALPHA)
                s_bg.fill((8, 14, 22, 210))
                pygame.draw.rect(s_bg, (80, 180, 255), (0, 0, bg_w, bg_h), 1, border_radius=4)
                surf.blit(s_bg, (cx - bg_w // 2, cy + 26))
                surf.blit(b_surf, (cx - bg_w // 2 + 8, cy + 30))
        elif self.ads_blend < 0.85:
            cx, cy = w // 2, h // 2
            spread_px = int(7 + (9 if self.is_sprinting else (3 if self.is_moving else 0)) - self.ads_blend * 5)
            ch_col = HL2_RED if self.crosshair_hit > 0 else HL2_AMBER
            # Center dot + 4 classic HL2 crosshair pips
            surf.set_at((cx, cy), ch_col)
            pygame.draw.rect(surf, ch_col, (cx - 1, cy - 1, 3, 3))
            for dx_p, dy_p in ((-spread_px, 0), (spread_px, 0), (0, -spread_px), (0, spread_px)):
                pygame.draw.rect(surf, ch_col, (cx + dx_p - 1, cy + dy_p - 1, 3, 3))

            # ── 1b. GENUINE HALF-LIFE 2 CHudQuickInfo (hud_quickinfo 1 — hl2crosshairs.ttf) ──
            # Left curved bracket = Health (0-100%), Right curved bracket = Clip Ammo (0-100%)
            weap_qi = WEAPONS[self.current_weapon]
            hp_frac = max(0.0, min(1.0, self.player_health / 100.0))
            hp_warn = (self.player_health <= 25) or (self.damage_flash > 0)
            hp_br_col = (255, 48, 32) if hp_warn else (255, 176, 0)
            hp_dim_col = (130, 28, 20) if hp_warn else (110, 76, 12)

            if weap_qi['ammo_type'] is not None and weap_qi.get('clip_size', 0) > 0:
                cur_c = self.weapon_clips.get(self.current_weapon, 0)
                max_c = max(1, weap_qi.get('clip_size', 1))
                ammo_frac = max(0.0, min(1.0, cur_c / float(max_c)))
                ammo_warn = (cur_c <= max(1, max_c // 4)) or self.is_reloading
            else:
                ammo_frac = 1.0
                ammo_warn = False
            am_br_col = (255, 48, 32) if ammo_warn else (255, 176, 0)
            am_dim_col = (130, 28, 20) if ammo_warn else (110, 76, 12)

            if getattr(self, 'font_hl2_quickinfo', None) is not None:
                # '[' = Left Empty Bracket, '{' = Left Filled Bracket
                # ']' = Right Empty Bracket, '}' = Right Filled Bracket
                l_empty = self.font_hl2_quickinfo.render('[', True, hp_dim_col)
                l_full = self.font_hl2_quickinfo.render('{', True, hp_br_col)
                r_empty = self.font_hl2_quickinfo.render(']', True, am_dim_col)
                r_full = self.font_hl2_quickinfo.render('}', True, am_br_col)

                bw_l, bh_l = l_empty.get_size()
                bw_r, bh_r = r_empty.get_size()
                bx_l = cx - 18 - bw_l
                by_l = cy - bh_l // 2
                bx_r = cx + 18
                by_r = cy - bh_r // 2

                l_empty.set_alpha(155)
                r_empty.set_alpha(155)
                surf.blit(l_empty, (bx_l, by_l))
                surf.blit(r_empty, (bx_r, by_r))

                fill_hl = int(round(bh_l * hp_frac))
                if fill_hl > 0:
                    cut_l = bh_l - fill_hl
                    surf.blit(l_full, (bx_l, by_l + cut_l), area=pygame.Rect(0, cut_l, bw_l, fill_hl))

                fill_hr = int(round(bh_r * ammo_frac))
                if fill_hr > 0:
                    cut_r = bh_r - fill_hr
                    surf.blit(r_full, (bx_r, by_r + cut_r), area=pygame.Rect(0, cut_r, bw_r, fill_hr))
            else:
                # Vector fallback curved QuickInfo brackets if font unavailable
                arc_r = pygame.Rect(cx - 26, cy - 18, 16, 36)
                pygame.draw.arc(surf, hp_dim_col, arc_r, math.pi * 0.55, math.pi * 1.45, 2)
                if hp_frac > 0:
                    pygame.draw.arc(surf, hp_br_col, arc_r, math.pi * (1.45 - 0.9 * hp_frac), math.pi * 1.45, 3)
                arc_r2 = pygame.Rect(cx + 10, cy - 18, 16, 36)
                pygame.draw.arc(surf, am_dim_col, arc_r2, -math.pi * 0.45, math.pi * 0.45, 2)
                if ammo_frac > 0:
                    pygame.draw.arc(surf, am_br_col, arc_r2, -math.pi * 0.45, -math.pi * 0.45 + math.pi * 0.9 * ammo_frac, 3)

            # ── 1c. TACTICAL HIT CONFIRMATION RETICLE (X-Hitmarker + Target QuickInfo Readout) ──
            if self.crosshair_hit > 0:
                is_k = getattr(self, 'crosshair_hit_kill', False)
                hm_col = (255, 60, 40) if is_k else (255, 235, 175)
                inner_d = 5
                outer_d = 12 + int(self.crosshair_hit * 8)
                for sx_m, sy_m in ((-1, -1), (1, -1), (-1, 1), (1, 1)):
                    pygame.draw.line(
                        surf, (15, 10, 5),
                        (cx + sx_m * inner_d, cy + sy_m * inner_d),
                        (cx + sx_m * outer_d, cy + sy_m * outer_d), 4
                    )
                    pygame.draw.line(
                        surf, hm_col,
                        (cx + sx_m * inner_d, cy + sy_m * inner_d),
                        (cx + sx_m * outer_d, cy + sy_m * outer_d), 2
                    )

            # Update or inspect target under crosshair for QuickInfo target ID
            qi_info = getattr(self, 'quickinfo_target', None)
            if not qi_info or qi_info.get("timer", 0.0) <= 0:
                # Passive QuickInfo look-at scan within 18m
                cos_l = math.cos(self.player_angle)
                sin_l = math.sin(self.player_angle)
                best_d = 18.0
                found_qi = None
                for ent in self.entities:
                    if not ent.alive:
                        continue
                    dx_e = ent.x - self.player_x
                    dy_e = ent.y - self.player_y
                    dist_e = math.hypot(dx_e, dy_e)
                    if 0.4 < dist_e < best_d:
                        dot_e = (dx_e * cos_l + dy_e * sin_l) / dist_e
                        if dot_e > 0.985:
                            best_d = dist_e
                            if isinstance(ent, PropEntity):
                                t_nm = f"PROP: {ent.prop_type.upper()}"
                            else:
                                t_nm = "CIVIL PROTECTION" if ent.type == 'mcpd' else ("CITIZEN" if ent.type == 'civilian' else ent.type.upper())
                            found_qi = {
                                "name": f"{t_nm} #{ent.id}",
                                "hp": max(0, int(ent.health)),
                                "max_hp": max(1, int(getattr(ent, 'max_health', 100))),
                                "is_kill": False,
                            }
                qi_info = found_qi

            if qi_info:
                t_pct = int(round(100.0 * qi_info["hp"] / max(1, qi_info["max_hp"])))
                if qi_info.get("is_kill"):
                    qi_str = f"TARGET ELIMINATED // {qi_info['name']}"
                    qi_col = (255, 70, 50)
                else:
                    qi_str = f"{qi_info['name']}  [{t_pct}%]"
                    qi_col = (255, 190, 40) if self.crosshair_hit > 0 else (230, 175, 55)
                qi_surf = self.font_console.render(qi_str, True, qi_col)
                qw, qh = qi_surf.get_width() + 14, 22
                qx, qy = cx - qw // 2, cy + 25
                qbg = pygame.Surface((qw, qh), pygame.SRCALPHA)
                qbg.fill((12, 10, 6, 175))
                pygame.draw.rect(qbg, (qi_col[0], qi_col[1], qi_col[2], 140), (0, 0, qw, qh), 1, border_radius=3)
                surf.blit(qbg, (qx, qy))
                surf.blit(qi_surf, (qx + 7, qy + 4))

        # ── 1d. Half-Life 2 CHudDamageIndicator (Directional Crimson Warning Arcs) ──
        if self.damage_flash > 0:
            dmg_a = int(min(220, self.damage_flash * 520))
            dmg_s = pygame.Surface((w, h), pygame.SRCALPHA)
            cx_d, cy_d = w // 2, h // 2
            pygame.draw.arc(dmg_s, (255, 35, 20, dmg_a), (cx_d - 95, cy_d - 85, 190, 170), math.pi * 0.65, math.pi * 1.35, 6)
            pygame.draw.arc(dmg_s, (255, 35, 20, dmg_a), (cx_d - 95, cy_d - 85, 190, 170), -math.pi * 0.35, math.pi * 0.35, 6)
            surf.blit(dmg_s, (0, 0))

        # ── 2. Bottom-Left: HL2 AUX POWER & HEALTH (Driven by halflife2.ttf & hudlayout.res) ──
        base_y = h - 78
        hp_col = HL2_RED if self.player_health <= 25 else HL2_AMBER
        hl2_num_font = getattr(self, 'font_hl2_numbers', None) or self.font_title

        # AUX POWER (Directly above HEALTH box, 10 discrete amber bars as in Screenshot 1)
        aux_col = HL2_RED if self.aux_power < 25 else HL2_AMBER
        draw_hl2_box(24, base_y - 52, 185, 44, aux_col if self.is_sprinting else None)
        aux_lbl = self.font_console.render("AUX POWER", True, aux_col)
        surf.blit(aux_lbl, (34, base_y - 46))
        segs = 10
        active_segs = int((self.aux_power / 100.0) * segs + 0.5)
        for s_i in range(segs):
            sc = aux_col if s_i < active_segs else (60, 45, 10, 120)
            pygame.draw.rect(surf, sc, (34 + s_i * 16, base_y - 26, 12, 10))

        # Source Water Buoyancy Status Indicator
        if getattr(self, 'player_in_water', False):
            draw_hl2_box(218, base_y - 52, 235, 44, (65, 200, 255))
            w_lbl = self.font_console.render("VPHYSICS WATER — [SPACE] SWIM UP", True, (90, 220, 255))
            surf.blit(w_lbl, (228, base_y - 36))

        # HEALTH Panel (halflife2.ttf '+' cross icon + HEALTH label + HL2 numerals)
        draw_hl2_box(24, base_y, 165, 58)
        if getattr(self, 'font_hl2_weapons', None) is not None:
            cross_ic = self.font_hl2_weapons.render("+", True, hp_col)
            surf.blit(cross_ic, (32, base_y + 6))
        hp_lbl = self.font_console.render("HEALTH", True, hp_col)
        surf.blit(hp_lbl, (34, base_y + 36))
        hp_num = hl2_num_font.render(str(max(0, self.player_health)), True, hp_col)
        surf.blit(hp_num, (96, base_y + 12))

        # SUIT (Armor) Panel
        if self.player_armor > 0:
            draw_hl2_box(202, base_y, 165, 58)
            if getattr(self, 'font_hl2_weapons', None) is not None:
                suit_ic = self.font_hl2_weapons.render("*", True, HL2_AMBER)
                surf.blit(suit_ic, (212, base_y + 6))
            suit_lbl = self.font_console.render("SUIT", True, HL2_AMBER)
            surf.blit(suit_lbl, (214, base_y + 36))
            ar_num = hl2_num_font.render(str(max(0, self.player_armor)), True, HL2_AMBER)
            surf.blit(ar_num, (268, base_y + 12))

        # ── 3. Bottom-Right: HL2 AMMO & RELOAD Panel (Hidden when Crowbar/melee equipped) ──
        weap = WEAPONS[self.current_weapon]
        if weap['ammo_type'] is not None:
            draw_hl2_box(w - 255, base_y, 230, 58)
            ammo_lbl = self.font_console.render("AMMO", True, HL2_AMBER)
            surf.blit(ammo_lbl, (w - 242, base_y + 36))
            if getattr(self, 'font_hl2_weapons', None) is not None:
                w_glyph = SourceEngineBridge.WEAPON_ICON_GLYPHS.get(self.current_weapon, 'd')
                w_ic = self.font_hl2_weapons.render(w_glyph, True, HL2_AMBER_DIM)
                surf.blit(w_ic, (w - 244, base_y + 2))
            else:
                wname_lbl = self.font_console.render(weap['name'][:24].upper(), True, HL2_AMBER_DIM)
                surf.blit(wname_lbl, (w - 242, base_y + 6))

            cur_clip = self.weapon_clips.get(self.current_weapon, 0)
            if self.is_reloading:
                r_flash = int(self.sim_time * 8) % 2 == 0
                r_col = HL2_RED if r_flash else HL2_AMBER
                reload_lbl = self.font_console.render("RELOADING...", True, r_col)
                surf.blit(reload_lbl, (w - 170, base_y + 38))
                clip_num = hl2_num_font.render(f"{cur_clip}", True, (160, 140, 100))
            else:
                clip_col = HL2_RED if cur_clip <= (weap['clip_size'] // 4) else HL2_AMBER
                clip_num = hl2_num_font.render(f"{cur_clip}", True, clip_col)

            surf.blit(clip_num, (w - 168, base_y + 12))

            is_sandbox = getattr(self, 'sandbox_mode', False) or getattr(self, 'cheat_mode', False)
            if is_sandbox:
                res_str = "| INF"
            else:
                res_val = self.ammo.get(weap['ammo_type'], 0)
                res_str = f"| {res_val}"
            res_txt = self.font_hud.render(res_str, True, HL2_AMBER_DIM)
            surf.blit(res_txt, (w - 95, base_y + 26))

        # ── 4. Top-Screen Half-Life 2 Weapon Bucket Selector (1–7 with halflife2.ttf silhouettes) ──
        if self.weapon_hud_timer > 0:
            total_w = 7 * 92
            start_x = (w - total_w) // 2
            for i in range(7):
                owned = self.weapons_owned.get(i, False)
                is_sel = (i == self.current_weapon)
                bw_slot = 88
                bh_slot = 64 if is_sel else 42
                bx_slot = start_x + i * 92
                by_slot = 26
                draw_hl2_box(bx_slot, by_slot, bw_slot, bh_slot, HL2_AMBER if is_sel else None)
                num_col = HL2_AMBER if is_sel else (HL2_AMBER_DIM if owned else (80, 70, 50))
                slot_num = self.font_console.render(str(i + 1), True, num_col)
                surf.blit(slot_num, (bx_slot + 6, by_slot + 4))
                if getattr(self, 'font_hl2_weapons', None) is not None:
                    w_glyph = SourceEngineBridge.WEAPON_ICON_GLYPHS.get(i, 'd')
                    ic_surf = self.font_hl2_weapons.render(w_glyph, True, num_col)
                    surf.blit(ic_surf, (bx_slot + (bw_slot - ic_surf.get_width()) // 2, by_slot + (8 if is_sel else 4)))
                if is_sel:
                    short_n = WEAPONS[i]['name'].split()[0].upper()
                    wn_surf = self.font_console.render(short_n, True, HL2_AMBER)
                    surf.blit(wn_surf, (bx_slot + 8, by_slot + 46))

        # ── 4b. Combine Overwatch PA Announcement Banner ──
        if getattr(self, 'overwatch_banner_timer', 0.0) > 0 and getattr(self, 'overwatch_current_banner', None):
            fade_in = (7.0 - self.overwatch_banner_timer) / 0.5 if self.overwatch_banner_timer > 6.5 else 1.0
            fade_out = self.overwatch_banner_timer / 0.8
            alpha_mult = max(0.0, min(1.0, fade_in, fade_out))
            bg_alpha = int(max(0, min(255, 220 * alpha_mult)))
            border_alpha = int(max(0, min(255, 230 * alpha_mult)))
            bw, bh = min(780, w - 80), 40
            bx = (w - bw) // 2
            by = 48 if self.weapon_hud_timer <= 0 else 92
            banner_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            banner_surf.fill((10, 16, 26, bg_alpha))
            pygame.draw.rect(banner_surf, (0, 215, 255, border_alpha), (0, 0, bw, bh), 1, border_radius=4)
            tag_txt = self.font_hud.render("OVERWATCH DISPATCH //", True, (0, 230, 255))
            banner_surf.blit(tag_txt, (14, 11))
            msg_txt = self.font_console.render(f'"{self.overwatch_current_banner}"', True, (230, 240, 255))
            banner_surf.blit(msg_txt, (14 + tag_txt.get_width() + 10, 13))
            surf.blit(banner_surf, (bx, by))

        # Universal Anti-Spawn Kill Treaty Grace Period Banner
        if getattr(self, 'spawn_protection_timer', 0.0) > 0:
            sp_timer = self.spawn_protection_timer
            bw, bh = 540, 32
            bx = (w - bw) // 2
            by = 96 if getattr(self, 'overwatch_banner_timer', 0.0) > 0 else 52
            sh_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            sh_surf.fill((12, 28, 38, 220))
            pygame.draw.rect(sh_surf, (0, 230, 180, 200), (0, 0, bw, bh), 1, border_radius=6)
            sh_txt = self.font_hud.render(f"UNIVERSAL ANTI-SPAWN KILL TREATY ACTIVE ({sp_timer:.1f}s)", True, (0, 255, 200))
            sh_surf.blit(sh_txt, (bw // 2 - sh_txt.get_width() // 2, 7))
            surf.blit(sh_surf, (bx, by))

        # Compliance Chronometer / MCPD Wave Telemetry Banner
        if getattr(self, 'compliance_chronometer', 0.0) > 0:
            c_timer = self.compliance_chronometer
            bw, bh = 580, 36
            bx = (w - bw) // 2
            by = 136 if (getattr(self, 'spawn_protection_timer', 0.0) > 0 and getattr(self, 'overwatch_banner_timer', 0.0) > 0) else (96 if (getattr(self, 'spawn_protection_timer', 0.0) > 0 or getattr(self, 'overwatch_banner_timer', 0.0) > 0) else 52)
            c_surf = pygame.Surface((bw, bh), pygame.SRCALPHA)
            pulse = math.sin(self.sim_time * 8.0) * 0.5 + 0.5
            border_alpha = int(140 + 115 * pulse)
            c_surf.fill((28, 14, 10, 230))
            pygame.draw.rect(c_surf, (255, 60, 40, border_alpha), (0, 0, bw, bh), 2, border_radius=6)
            c_txt = self.font_hud.render(f"[MCPD WAVE TELEMETRY] FREEZE & COMPLY: {c_timer:.1f}s", True, (255, 80, 50))
            c_sub = self.font_console.render("STATIONARY SCAN IN PROGRESS — MOVEMENT WILL TRIGGER LETHAL FORCE", True, (255, 200, 160))
            c_surf.blit(c_txt, (bw // 2 - c_txt.get_width() // 2, 3))
            c_surf.blit(c_sub, (bw // 2 - c_sub.get_width() // 2, 19))
            surf.blit(c_surf, (bx, by))

        # Wanted Level Stars
        if self.wanted_level > 0:
            star_txt = self.font_hud.render("OVERWATCH ALERT:", True, HL2_RED)
            surf.blit(star_txt, (w - 245, 12))
            for idx in range(self.wanted_level):
                sx = w - 100 + idx * 18
                sy = 18
                pygame.draw.polygon(surf, HL2_AMBER, [
                    (sx, sy - 6), (sx + 2, sy - 2), (sx + 6, sy - 2),
                    (sx + 3, sy + 1), (sx + 4, sy + 5), (sx, sy + 3),
                    (sx - 4, sy + 5), (sx - 3, sy + 1), (sx - 6, sy - 2),
                    (sx - 2, sy - 2)
                ])

        # Top telemetry bar
        top_surf = pygame.Surface((w, 24), pygame.SRCALPHA)
        top_surf.fill((0, 0, 0, 145))
        surf.blit(top_surf, (0, 0))
        cam_names = ["3RD PERSON", "3RD WIDE", "1ST PERSON [HL2]"]
        mode_label = "SANDBOX" if (getattr(self, 'sandbox_mode', False) or getattr(self, 'cheat_mode', False)) else "TACTICAL"
        fog_str = "FOG:ON" if self.fog_enabled else "FOG:OFF"
        sv_txt = self.font_console.render(
            f"Map: {self.current_map} | {self.graphics_preset} ({fog_str}) | {mode_label} | {cam_names[self.camera_mode]} | Kills: {self.kills} | ${self.player_money:,}",
            True, HL2_AMBER
        )
        surf.blit(sv_txt, (10, 5))

        hints = [
            "[ESC] Pause & Graphics Settings  [G] Punt Physics Prop",
            "[W+SHIFT] Tactical Sprint        [RMB] Iron Sights (ADS)",
            "[LMB] Fire HL2 Weapon            [R] Tactical Reload",
            "[1-7] HL2 Weapon Arsenal         [V] Toggle 1st/3rd Person",
            "[E] Open Door / Arms Shop        [F1] Admin  [TAB] Map",
        ]
        for i, h_text in enumerate(hints):
            ht = self.font_console.render(h_text, True, (210, 175, 95))
            surf.blit(ht, (w - ht.get_width() - 12, 165 + i * 14))

        # Directional HL2 Red Damage Flash & Indicator
        if self.damage_flash > 0:
            flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            flash_alpha = int(max(0, min(255, self.damage_flash * 105)))
            flash_surf.fill((220, 15, 10, flash_alpha))
            surf.blit(flash_surf, (0, 0))
            pygame.draw.rect(surf, (255, 30, 20), (0, 0, w, h), 6)

        # Proximity Prompt for Arms Shop Kiosk
        shop_x, shop_y = self.get_arms_shop_location()
        dist_shop = math.hypot(self.player_x - shop_x, self.player_y - shop_y)
        if dist_shop < 3.2 and not getattr(self, 'arms_shop_open', False):
            pw, ph = 380, 36
            px = (w - pw) // 2
            py = h - 145
            p_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
            p_surf.fill((15, 22, 32, 225))
            pygame.draw.rect(p_surf, (245, 155, 56), (0, 0, pw, ph), 2, border_radius=6)
            ptxt = self.font_hud.render("[E] OPEN TBMG UNREGULATED ARMS SHOP", True, (255, 200, 80))
            p_surf.blit(ptxt, (pw // 2 - ptxt.get_width() // 2, 9))
            surf.blit(p_surf, (px, py))

        # Render Arms Shop Modal when Open
        if getattr(self, 'arms_shop_open', False):
            self.render_arms_shop_modal(surf)

        # Vehicle Proximity Prompts & Modals (MainCity2, Big City 5 & driving Test map)
        if self.current_map in ("MainCity2", "BigCity5", "driving Test map"):
            # 1. Proximity Prompt for 3D Car Spawner Kiosk
            kiosk_x, kiosk_y = (20.5, 23.5) if self.current_map == "driving Test map" else ((15.2, 31.0) if self.current_map == "MainCity2" else (15.2, 32.0))
            dist_spawner = math.hypot(self.player_x - kiosk_x, self.player_y - kiosk_y)
            if dist_spawner < 2.8 and not getattr(self, 'in_vehicle', False) and not getattr(self, 'vehicle_spawner_open', False):
                pw, ph = 380, 36
                px = (w - pw) // 2
                py = h - 145
                p_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
                p_surf.fill((15, 22, 32, 235))
                pygame.draw.rect(p_surf, (255, 205, 45), (0, 0, pw, ph), 2, border_radius=6)
                ptxt = self.font_hud.render("[E] OPEN TBMG VEHICLE SPAWNER", True, (255, 215, 50))
                p_surf.blit(ptxt, (pw // 2 - ptxt.get_width() // 2, 9))
                surf.blit(p_surf, (px, py))

            # 2. Proximity Prompt for Parked Vehicles
            if not getattr(self, 'in_vehicle', False) and not getattr(self, 'vehicle_spawner_open', False):
                for veh in getattr(self, 'vehicles', []):
                    if math.hypot(self.player_x - veh.x, self.player_y - veh.y) < 2.5:
                        pw, ph = 420, 36
                        px = (w - pw) // 2
                        py = h - 185
                        p_surf = pygame.Surface((pw, ph), pygame.SRCALPHA)
                        p_surf.fill((15, 22, 32, 235))
                        pygame.draw.rect(p_surf, (50, 240, 140), (0, 0, pw, ph), 2, border_radius=6)
                        ptxt = self.font_hud.render(f"[E] ENTER VEHICLE ({veh.name})", True, (70, 255, 160))
                        p_surf.blit(ptxt, (pw // 2 - ptxt.get_width() // 2, 9))
                        surf.blit(p_surf, (px, py))
                        break

            # 3. Vehicle Driving HUD (Speedometer, Gear, Health)
            if getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None):
                self.render_vehicle_hud(surf)

            # 4. Vehicle Spawner Modal
            if getattr(self, 'vehicle_spawner_open', False):
                self.render_vehicle_spawner_modal(surf)

    def render_minimap(self, surf):
        mm_w, mm_h = 150, 115
        mm_x = surf.get_width() - mm_w - 12
        mm_y = 40

        mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm_surf.fill((8, 10, 16, 190))
        pygame.draw.rect(mm_surf, (255, 140, 0, 140), (0, 0, mm_w, mm_h), 1)

        sx = mm_w / MAP_W
        sy = mm_h / MAP_H
        for y in range(MAP_H):
            for x in range(MAP_W):
                cell = MAP[y][x]
                if cell == 7:
                    pygame.draw.rect(mm_surf, (30, 130, 195), (int(x * sx), int(y * sy), max(1, int(sx) + 1), max(1, int(sy) + 1)))
                elif cell != 0:
                    pygame.draw.rect(mm_surf, (65, 70, 82), (int(x * sx), int(y * sy), max(1, int(sx) + 1), max(1, int(sy) + 1)))

        type_colors = {
            'civilian': (130, 170, 255), 'mcpd': (60, 120, 255), 'ecpu': (180, 60, 255),
            'rpg': (255, 70, 0), 'imp': (255, 180, 0), 'demon': (255, 80, 120),
            'charger': (255, 68, 204), 'military': (100, 220, 100),
            'crate': (210, 155, 75), 'barrel': (50, 160, 255), 'explosive_barrel': (255, 60, 60),
        }
        for e in self.entities:
            if e.alive:
                c = type_colors.get(e.type, (255, 255, 255))
                px, py = min(mm_w - 2, max(1, int(e.x * sx))), min(mm_h - 2, max(1, int(e.y * sy)))
                pygame.draw.circle(mm_surf, c, (px, py), 2)

        # Arms Shop Kiosk [$] icon on minimap
        shop_x, shop_y = self.get_arms_shop_location()
        spx, spy = int(shop_x * sx), int(shop_y * sy)
        pygame.draw.circle(mm_surf, (50, 255, 80), (spx, spy), 4)
        pygame.draw.circle(mm_surf, (255, 255, 255), (spx, spy), 4, 1)

        ppx, ppy = int(self.player_x * sx), int(self.player_y * sy)
        pygame.draw.circle(mm_surf, COL_GREEN, (ppx, ppy), 3)
        dx = math.cos(self.player_angle) * 8
        dy = math.sin(self.player_angle) * 8
        pygame.draw.line(mm_surf, COL_GREEN, (ppx, ppy), (ppx + int(dx), ppy + int(dy)), 2)

        surf.blit(mm_surf, (mm_x, mm_y))

    def render_map_editor_hud(self, surf):
        if not getattr(self, 'map_editor_active', False):
            return
        w, h = surf.get_size()

        # Top Source Hammer / Garry's Mod style Map Editor Banner
        banner_h = 68
        banner = pygame.Surface((w, banner_h), pygame.SRCALPHA)
        banner.fill((12, 16, 22, 230))
        pygame.draw.line(banner, (255, 176, 0), (0, banner_h - 2), (w, banner_h - 2), 2)
        surf.blit(banner, (0, 0))

        cat, val, label = MAP_EDITOR_PALETTE[self.editor_idx % len(MAP_EDITOR_PALETTE)]
        rot_deg = int(round(self.editor_yaw)) % 360
        self._update_editor_cursor()
        tx, ty = self.editor_target_x, self.editor_target_y
        tz = getattr(self, 'editor_target_z', 0.0)
        t_idx = getattr(self, 'editor_targeted_prop_idx', None)

        if t_idx is not None and 0 <= t_idx < len(self.placed_objects):
            t_obj = self.placed_objects[t_idx]
            t_type = str(t_obj.get("type", "prop")).upper()
            tox, toy, toz = float(t_obj.get("x", 0.0)), float(t_obj.get("y", 0.0)), float(t_obj.get("z", 0.0))
            title_s = self.font_title.render(
                f"SOURCE MAP EDITOR [{self.current_map}] — TARGET LOCKED: #{t_idx+1} {t_type}",
                True, (255, 120, 40)
            )
            ctrl_s = self.font_console.render(
                f"Target Prop at ({tox:.1f}, {toy:.1f}, z={toz:.1f}) | [RMB] or [DEL] DELETE TARGET | [LMB] Place | [Q/E/Wheel] ({self.editor_idx + 1}/{len(MAP_EDITOR_PALETTE)}) | [R] Rotate 45° | [F2] Exit",
                True, (255, 235, 120)
            )
        else:
            title_s = self.font_title.render(
                f"SOURCE MAP EDITOR [{self.current_map}] — SELECTED: {label} ({cat.upper()})",
                True, (255, 195, 40)
            )
            ctrl_s = self.font_console.render(
                f"Surface: ({tx:.1f}, {ty:.1f}, z={tz:.1f}) | Rot: {rot_deg}° | [LMB] Place {label} | [RMB] Delete | [Q/E/Wheel] Item ({self.editor_idx + 1}/{len(MAP_EDITOR_PALETTE)}) | [R] Rotate 45° | [F2] Exit",
                True, (200, 225, 250)
            )
        surf.blit(title_s, (18, 8))
        surf.blit(ctrl_s, (18, 32))

        status_msg = getattr(self, 'editor_status_msg', '') if getattr(self, 'editor_status_timer', 0.0) > 0 else "Auto-saves to custom_maps.json | AI & NPC Combat: FROZEN"
        stat_s = self.font_console.render(
            f"Placed Props/Catwalks: {len(self.placed_objects)}  |  Status: {status_msg}",
            True, (130, 255, 150)
        )
        surf.blit(stat_s, (18, 50))

        # Right-hand scrollable palette strip showing nearby items
        strip_w, strip_h = 310, 330
        sx, sy = w - strip_w - 14, 78
        strip = pygame.Surface((strip_w, strip_h), pygame.SRCALPHA)
        strip.fill((10, 14, 20, 215))
        pygame.draw.rect(strip, (255, 176, 0, 180), (0, 0, strip_w, strip_h), 1, border_radius=6)
        surf.blit(strip, (sx, sy))

        hdr = self.font_hud.render("HL2 RESOURCE PALETTE [Q/E]", True, (255, 176, 0))
        surf.blit(hdr, (sx + 10, sy + 6))

        n_items = len(MAP_EDITOR_PALETTE)
        half_vis = 5
        row_y = sy + 28
        for offset in range(-half_vis, half_vis + 1):
            idx = (self.editor_idx + offset) % n_items
            p_cat, _, p_label = MAP_EDITOR_PALETTE[idx]
            is_cur = (offset == 0)
            row_rect = pygame.Rect(sx + 6, row_y, strip_w - 12, 24)
            if is_cur:
                pygame.draw.rect(surf, (255, 176, 0, 85), row_rect, border_radius=4)
                pygame.draw.rect(surf, (255, 200, 60), row_rect, 1, border_radius=4)
            cat_col = (120, 210, 255) if p_cat == 'grid' else ((120, 255, 150) if p_cat == 'prop_static' else (255, 150, 120))
            pygame.draw.circle(surf, cat_col, (sx + 16, row_y + 12), 4)
            lbl = self.font_console.render(f"{idx + 1:02d}. {p_label}", True, (255, 240, 180) if is_cur else (185, 190, 200))
            surf.blit(lbl, (sx + 26, row_y + 5))
            row_y += 26

    def render_automap(self, surf):
        w, h = surf.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((5, 8, 14, 220))
        surf.blit(overlay, (0, 0))

        scale = min((w - 60) / MAP_W, (h - 140) / MAP_H)
        ox = (w - MAP_W * scale) // 2
        oy = (h - MAP_H * scale) // 2 + 20
        self._automap_transform = (ox, oy, scale)

        for y in range(MAP_H):
            for x in range(MAP_W):
                rx, ry = ox + x * scale, oy + y * scale
                cell = MAP[y][x]
                if cell == 7:
                    c = (28, 125, 185)
                elif cell == 6:
                    c = (50, 200, 80)
                elif cell != 0:
                    c = (65, 70, 82)
                else:
                    c = (18, 20, 28)
                pygame.draw.rect(surf, c, (rx, ry, max(1, scale - 1), max(1, scale - 1)))

        for obj in getattr(self, 'placed_objects', []):
            px, py = ox + obj.get('x', 0) * scale, oy + obj.get('y', 0) * scale
            pygame.draw.circle(surf, (80, 220, 255), (int(px), int(py)), max(3, int(scale * 0.26)))

        for e in self.entities:
            if e.alive:
                px, py = ox + e.x * scale, oy + e.y * scale
                col_e = (80, 180, 255) if e.type == 'mcpd' else (255, 120, 40)
                pygame.draw.circle(surf, col_e, (int(px), int(py)), max(3, int(scale * 0.3)))

        ppx, ppy = ox + self.player_x * scale, oy + self.player_y * scale
        pygame.draw.circle(surf, COL_GREEN, (int(ppx), int(ppy)), max(4, int(scale * 0.4)))

        # Draw Arms Shop [$] on automap
        shop_x, shop_y = self.get_arms_shop_location()
        spx, spy = ox + shop_x * scale, oy + shop_y * scale
        pygame.draw.circle(surf, (50, 255, 80), (int(spx), int(spy)), max(5, int(scale * 0.45)))
        pygame.draw.circle(surf, (255, 255, 255), (int(spx), int(spy)), max(5, int(scale * 0.45)), 1)
        sh_lbl = self.font_hud_sm.render("[$] ARMS SHOP", True, (50, 255, 100))
        surf.blit(sh_lbl, (int(spx) + 8, int(spy) - 6))

        if getattr(self, 'map_editor_active', False):
            mx, my = pygame.mouse.get_pos()
            gx = (mx - ox) / max(1e-5, scale)
            gy = (my - oy) / max(1e-5, scale)
            if 0 <= gx < MAP_W and 0 <= gy < MAP_H:
                hrx, hry = ox + int(gx) * scale, oy + int(gy) * scale
                pygame.draw.rect(surf, (255, 220, 40), (hrx, hry, scale, scale), 2)
            _, _, label = MAP_EDITOR_PALETTE[self.editor_idx % len(MAP_EDITOR_PALETTE)]
            title = self.font_hud.render(
                f"2D MAP EDITOR GRID — {self.current_map} | Selected: {label} | [LMB] Place | [RMB] Delete | [F5] Save",
                True, (255, 200, 50)
            )
        else:
            title = self.font_hud.render(f"TACTICAL SATELLITE AUTOMAP — {self.current_map} (Press [F2] for Map Editor)", True, COL_ORANGE)
        surf.blit(title, (w // 2 - title.get_width() // 2, 16))

    def _get_pause_menu_items(self):
        fog_state = "ON" if self.fog_enabled else "OFF"
        editor_state = "ACTIVE" if getattr(self, 'map_editor_active', False) else "OFF"
        decal_count = len(getattr(self, 'bullet_decals', []))
        return [
            {
                "id": 0, "type": "action", "cat": "SIMULATION",
                "label": f"Resume Simulation ({self.current_map})",
                "val": "[ESC / CLICK]",
                "desc": "Return directly to active first-person tactical combat"
            },
            {
                "id": 1, "type": "stepper", "cat": "ATMOSPHERE",
                "label": "Graphics Engine Preset",
                "val": self.graphics_preset,
                "desc": "Potato PC (22m PS1) | Standard User (38m Balanced) | Alter Heavy (64m Ultra)"
            },
            {
                "id": 2, "type": "toggle", "cat": "ATMOSPHERE",
                "label": "Atmospheric Volumetric Fog",
                "val": fog_state,
                "desc": "City 17 weather haze and volumetric depth attenuation"
            },
            {
                "id": 3, "type": "stepper", "cat": "ATMOSPHERE",
                "label": "Fog Distance / Draw Scale",
                "val": f"{int(self.fog_distance)}m",
                "desc": "Adjust horizon visibility radius between 20m and 95m (Click [-] to Lower, [+] to Raise)"
            },
            {
                "id": 4, "type": "stepper", "cat": "SIMULATION",
                "label": "Wall Bullet Impact Decals Limit",
                "val": f"{self.max_bullet_decals} rounds",
                "desc": f"Active: {decal_count}/{self.max_bullet_decals} decals | Oldest bullet holes fade out on limit"
            },
            {
                "id": 5, "type": "stepper", "cat": "SECTOR",
                "label": "Active City Sector / Map",
                "val": self.current_map,
                "desc": "Switch between City 17 Plaza, gm_bigcity Highrise, Big City 5 Highway, and driving Test map"
            },
            {
                "id": 6, "type": "toggle", "cat": "HAMMER",
                "label": "Hammer / Source Map Editor [F2]",
                "val": editor_state,
                "desc": "Live 3D asset placer, Combine street barrier constructor, and building demolition"
            },
            {
                "id": 7, "type": "action", "cat": "HAMMER",
                "label": f"Save Custom Map to Disk [F5] ({self.current_map})",
                "val": "[SAVE MAP]",
                "desc": "Commit all placed HL2 objects and grid structures to storage (custom_maps.json)"
            },
            {
                "id": 8, "type": "action", "cat": "HAMMER",
                "label": f"Load Saved Custom Map [F6] ({self.current_map})",
                "val": "[LOAD MAP]",
                "desc": "Reload customized map structures from persistent JSON storage"
            },
            {
                "id": 9, "type": "action", "cat": "HAMMER",
                "label": f"Reset Map to Factory Default [F7] ({self.current_map})",
                "val": "[RESET MAP]",
                "desc": "Clear all custom additions and revert to standard layout"
            },
            {
                "id": 10, "type": "action", "cat": "SYSTEM",
                "label": "Reset All Settings to Factory Default",
                "val": "[RESET CFG]",
                "desc": "Restore default 46m Fog, Standard User graphics, and 500 decal buffer"
            },
            {
                "id": 11, "type": "action", "cat": "SYSTEM",
                "label": "Return to Main Title Screen",
                "val": "[TITLE]",
                "desc": "Exit to the 2026 AAA live 3D orbital title screen"
            },
            {
                "id": 12, "type": "action", "cat": "SYSTEM",
                "label": "Quit to Desktop",
                "val": "[QUIT]",
                "desc": "Safely unload assets, close log window, and terminate application"
            },
        ]

    def _execute_pause_option(self, idx, delta=1):
        if idx == 0:
            self.paused = False
            pygame.mouse.set_visible(self.map_editor_active and self.automap)
            pygame.event.set_grab(not (self.map_editor_active and self.automap))
        elif idx == 1:
            cur_i = GRAPHICS_PRESETS.index(self.graphics_preset) if self.graphics_preset in GRAPHICS_PRESETS else 1
            new_i = (cur_i + delta) % len(GRAPHICS_PRESETS)
            self.graphics_preset = GRAPHICS_PRESETS[new_i]
            self.apply_graphics_and_fog_settings(rebuild_chunks=True)
            self.add_log('sys', f'[SETTINGS] Graphics Engine set to "{self.graphics_preset}" (Saved)')
        elif idx == 2:
            self.fog_enabled = not self.fog_enabled
            self.apply_graphics_and_fog_settings(rebuild_chunks=False)
            self.add_log('sys', f'[SETTINGS] Atmospheric Fog turned {"ON" if self.fog_enabled else "OFF"} (Saved)')
        elif idx == 3:
            # Intuitive decrement and increment: can lower or raise fog distance between 20m and 95m
            self.fog_distance = max(20.0, min(95.0, self.fog_distance + delta * 10.0))
            self.apply_graphics_and_fog_settings(rebuild_chunks=False)
            self.add_log('sys', f'[SETTINGS] Fog Distance set to {int(self.fog_distance)}m (Saved)')
        elif idx == 4:
            # Bullet impact decal limit stepper
            decal_options = [100, 250, 500, 1000, 2000]
            try:
                cur_i = decal_options.index(self.max_bullet_decals)
            except ValueError:
                cur_i = 2
            new_i = max(0, min(len(decal_options) - 1, cur_i + delta))
            self.max_bullet_decals = decal_options[new_i]
            while len(self.bullet_decals) > self.max_bullet_decals:
                self.bullet_decals.pop(0)
            self.save_current_settings()
            self.add_log('sys', f'[SETTINGS] Wall Bullet Decal Limit set to {self.max_bullet_decals} rounds (FIFO Saved)')
        elif idx == 5:
            maps_seq = ["MainCity2", "gm_bigcity", "BigCity5", "driving Test map"]
            if self.current_map in maps_seq:
                cur_i = maps_seq.index(self.current_map)
                next_map = maps_seq[(cur_i + delta) % len(maps_seq)]
            else:
                next_map = "MainCity2"
            self.switch_map(next_map)
        elif idx == 6:
            self.paused = False
            self.toggle_map_editor()
            pygame.mouse.set_visible(self.map_editor_active and self.automap)
            pygame.event.set_grab(not (self.map_editor_active and self.automap))
        elif idx == 7:
            self.save_custom_map_state()
        elif idx == 8:
            self.load_custom_map_state()
        elif idx == 9:
            self.reset_map_to_default()
        elif idx == 10:
            self.graphics_preset = DEFAULT_USER_SETTINGS["graphics_preset"]
            self.fog_enabled = DEFAULT_USER_SETTINGS["fog_enabled"]
            self.fog_distance = DEFAULT_USER_SETTINGS["fog_distance"]
            self.max_bullet_decals = DEFAULT_USER_SETTINGS["max_bullet_decals"]
            self.apply_graphics_and_fog_settings(rebuild_chunks=True)
            self.add_log('sys', '[SETTINGS] Factory Reset: Standard User, Fog ON (46m), 500 Decals')
        elif idx == 11:
            self.paused = False
            self.game_state = self.STATE_TITLE
            pygame.mouse.set_visible(True)
            pygame.event.set_grab(False)
        elif idx == 12:
            self.running = False

    def render_pause_menu(self, surf):
        if not self.paused:
            return
        w, h = surf.get_size()
        dim_overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        dim_overlay.fill((5, 8, 14, 215))
        surf.blit(dim_overlay, (0, 0))

        panel_w = min(760, w - 40)
        panel_h = min(575, h - 30)
        px, py = w // 2 - panel_w // 2, h // 2 - panel_h // 2

        # 2026 AAA Frosted Glass Panel
        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((10, 14, 22, 246))
        pygame.draw.rect(panel_surf, (0, 215, 255, 185), (0, 0, panel_w, panel_h), 1, border_radius=10)
        # Top glowing accent line
        pygame.draw.line(panel_surf, (0, 235, 255, 240), (14, 0), (panel_w - 14, 0), 2)
        surf.blit(panel_surf, (px, py))

        # Title & Sector Status Header
        title = self.font_large.render("OVERWATCH TACTICAL SUSPENSION // 2026 SETTINGS", True, (0, 225, 255))
        surf.blit(title, (px + 20, py + 12))

        sub = self.font_console.render(
            f"SECTOR: {self.current_map.upper()}  |  GRAPHICS: {self.graphics_preset.upper()}  |  FOG: {int(self.fog_distance)}m  |  WALL DECALS: {len(self.bullet_decals)}/{self.max_bullet_decals}",
            True, (175, 210, 240)
        )
        surf.blit(sub, (px + 20, py + 38))

        items = self._get_pause_menu_items()
        mouse_pos = pygame.mouse.get_pos()
        self.pause_button_rects = []

        cat_colors = {
            "ATMOSPHERE": (0, 210, 255),
            "SIMULATION": (255, 176, 40),
            "SECTOR": (120, 225, 140),
            "HAMMER": (255, 130, 80),
            "SYSTEM": (160, 175, 195),
        }

        row_h = 28
        row_gap = 4
        start_y = py + 62

        for i, item in enumerate(items):
            iy = start_y + i * (row_h + row_gap)
            rect = pygame.Rect(px + 16, iy, panel_w - 32, row_h)
            hovered = rect.collidepoint(mouse_pos)
            if hovered and not getattr(self, 'pause_button_rects', None):
                self.pause_selection = i
            is_sel = (i == self.pause_selection)

            row_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            if is_sel:
                row_surf.fill((16, 40, 68, 235))
                pygame.draw.rect(row_surf, (0, 215, 255, 200), (0, 0, rect.w, rect.h), 1, border_radius=5)
                # Left indicator stripe
                pygame.draw.rect(row_surf, (0, 240, 255), (0, 0, 4, rect.h), border_top_left_radius=5, border_bottom_left_radius=5)
            else:
                row_surf.fill((255, 255, 255, 10))
                pygame.draw.rect(row_surf, (255, 255, 255, 20), (0, 0, rect.w, rect.h), 1, border_radius=5)
            surf.blit(row_surf, rect.topleft)

            # Category pill tag
            cat = item.get("cat", "SYSTEM")
            cat_c = cat_colors.get(cat, (180, 190, 205))
            cat_s = self.font_console.render(f"[{cat}]", True, cat_c)
            surf.blit(cat_s, (rect.x + 12, rect.y + 7))

            # Main item label
            lbl_c = (255, 255, 255) if is_sel else (205, 215, 225)
            lbl = self.font_hud.render(item["label"], True, lbl_c)
            surf.blit(lbl, (rect.x + 105, rect.y + 6))

            # Interactive controls on the right side
            itype = item.get("type", "action")
            minus_r = None
            plus_r = None

            if itype == "stepper":
                # Dedicated interactive [-] button
                minus_r = pygame.Rect(rect.right - 172, rect.y + 3, 24, 22)
                m_hov = minus_r.collidepoint(mouse_pos)
                m_surf = pygame.Surface((minus_r.w, minus_r.h), pygame.SRCALPHA)
                m_surf.fill((255, 176, 0, 180) if m_hov else (255, 255, 255, 25))
                pygame.draw.rect(m_surf, (255, 195, 60) if m_hov else (255, 255, 255, 60), (0, 0, minus_r.w, minus_r.h), 1, border_radius=4)
                m_txt = self.font_hud.render("-", True, (0, 0, 0) if m_hov else (255, 220, 100))
                m_surf.blit(m_txt, (minus_r.w // 2 - m_txt.get_width() // 2, 2))
                surf.blit(m_surf, minus_r.topleft)

                # Center value display badge
                val_r = pygame.Rect(rect.right - 144, rect.y + 3, 112, 22)
                v_surf = pygame.Surface((val_r.w, val_r.h), pygame.SRCALPHA)
                v_surf.fill((8, 18, 30, 200))
                pygame.draw.rect(v_surf, (0, 215, 255, 120), (0, 0, val_r.w, val_r.h), 1, border_radius=4)
                val_txt = self.font_console.render(item["val"][:16], True, (0, 235, 255))
                v_surf.blit(val_txt, (val_r.w // 2 - val_txt.get_width() // 2, 4))
                surf.blit(v_surf, val_r.topleft)

                # Dedicated interactive [+] button
                plus_r = pygame.Rect(rect.right - 28, rect.y + 3, 24, 22)
                p_hov = plus_r.collidepoint(mouse_pos)
                p_surf = pygame.Surface((plus_r.w, plus_r.h), pygame.SRCALPHA)
                p_surf.fill((0, 225, 255, 180) if p_hov else (255, 255, 255, 25))
                pygame.draw.rect(p_surf, (0, 245, 255) if p_hov else (255, 255, 255, 60), (0, 0, plus_r.w, plus_r.h), 1, border_radius=4)
                p_txt = self.font_hud.render("+", True, (0, 0, 0) if p_hov else (0, 240, 255))
                p_surf.blit(p_txt, (plus_r.w // 2 - p_txt.get_width() // 2, 2))
                surf.blit(p_surf, plus_r.topleft)

            elif itype == "toggle":
                t_val = item["val"]
                t_is_on = ("ON" in t_val.upper() or "ACTIVE" in t_val.upper())
                t_r = pygame.Rect(rect.right - 92, rect.y + 3, 84, 22)
                t_surf = pygame.Surface((t_r.w, t_r.h), pygame.SRCALPHA)
                if t_is_on:
                    t_surf.fill((15, 75, 45, 220))
                    pygame.draw.rect(t_surf, (40, 240, 140), (0, 0, t_r.w, t_r.h), 1, border_radius=4)
                    t_txt = self.font_console.render(f"● {t_val}", True, (50, 255, 150))
                else:
                    t_surf.fill((65, 20, 25, 220))
                    pygame.draw.rect(t_surf, (255, 70, 70), (0, 0, t_r.w, t_r.h), 1, border_radius=4)
                    t_txt = self.font_console.render(f"○ {t_val}", True, (255, 120, 120))
                t_surf.blit(t_txt, (t_r.w // 2 - t_txt.get_width() // 2, 4))
                surf.blit(t_surf, t_r.topleft)

            else:
                a_r = pygame.Rect(rect.right - 108, rect.y + 3, 100, 22)
                a_surf = pygame.Surface((a_r.w, a_r.h), pygame.SRCALPHA)
                a_surf.fill((255, 255, 255, 15))
                pygame.draw.rect(a_surf, (255, 255, 255, 35), (0, 0, a_r.w, a_r.h), 1, border_radius=4)
                a_txt = self.font_console.render(item["val"][:14], True, (215, 225, 235))
                a_surf.blit(a_txt, (a_r.w // 2 - a_txt.get_width() // 2, 4))
                surf.blit(a_surf, a_r.topleft)

            self.pause_button_rects.append((rect, minus_r, plus_r, i))

        # Selected Item Description Card (Above Footer)
        cur_item = items[self.pause_selection % len(items)]
        desc_card = pygame.Surface((panel_w - 32, 28), pygame.SRCALPHA)
        desc_card.fill((12, 22, 34, 220))
        pygame.draw.rect(desc_card, (0, 215, 255, 100), (0, 0, panel_w - 32, 28), 1, border_radius=4)
        info_txt = self.font_console.render(f"ℹ️ {cur_item['desc']}", True, (160, 220, 255))
        desc_card.blit(info_txt, (10, 6))
        surf.blit(desc_card, (px + 16, py + panel_h - 58))

        # Modern Tactical Controls Footer
        footer = self.font_console.render(
            "[◄ / - Click] Lower Setting  |  [► / + Click] Raise Setting  |  [LMB/ENTER] Select  |  [RMB/Wheel] Adjust  |  [ESC] Resume",
            True, (140, 185, 220)
        )
        surf.blit(footer, (px + 20, py + panel_h - 22))

    def render_admin(self, surf):
        if not self.admin_open:
            return
        w, h = surf.get_size()
        panel_w, panel_h = 440, 450
        px, py = w // 2 - panel_w // 2, h // 2 - panel_h // 2

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((10, 12, 20, 240))
        pygame.draw.rect(panel_surf, (200, 80, 255), (0, 0, panel_w, panel_h), 2)
        surf.blit(panel_surf, (px, py))

        title = self.font_admin.render("PRESIDENT MICHAEL — 3D EXECUTIVE TERMINAL", True, (220, 150, 255))
        surf.blit(title, (px + 14, py + 8))

        mouse_pos = pygame.mouse.get_pos()
        for i, (label, _) in enumerate(self.admin_items):
            iy = py + 38 + i * 24
            rect = pygame.Rect(px + 12, iy, panel_w - 24, 21)
            hovered = rect.collidepoint(mouse_pos)
            btn_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            btn_surf.fill((255, 140, 0, 80) if hovered else (255, 255, 255, 18))
            surf.blit(btn_surf, rect.topleft)
            txt = self.font_admin.render(label, True, COL_WHITE if hovered else (200, 200, 210))
            surf.blit(txt, (rect.x + 10, rect.y + 3))

    def _execute_title_option(self, idx, delta=1):
        if hasattr(self, 'snd_ui_release') and self.snd_ui_release:
            self.snd_ui_release.play()
        if idx == 0:  # New Game (Half-Life 2 Tactical Survival)
            self.sandbox_mode = False
            self.cheat_mode = False
            self.map_editor_open = False
            self.game_state = self.STATE_PLAYING
            self.init_game()
        elif idx == 1:  # Sandbox Mode (Garry's Mod Unrestricted)
            self.sandbox_mode = True
            self.cheat_mode = True
            self.map_editor_open = False
            self.game_state = self.STATE_PLAYING
            self.init_game()
        elif idx == 2:  # Switch Chapter / Map
            maps_seq = ["MainCity2", "gm_bigcity", "BigCity5", "driving Test map"]
            if self.current_map in maps_seq:
                cur_i = maps_seq.index(self.current_map)
                next_map = maps_seq[(cur_i + delta) % len(maps_seq)]
            else:
                next_map = "MainCity2"
            self.switch_map(next_map)
        elif idx == 3:  # Hammer Map Editor
            self.sandbox_mode = True
            self.cheat_mode = True
            self.game_state = self.STATE_PLAYING
            self.init_game()
            self.map_editor_open = True
            self.toggle_map_editor()
            self.add_log('sys', '[MAP EDITOR] Hammer / Source Map Editor Active!')
        elif idx == 4:  # Options / Graphics Preset
            cur_i = GRAPHICS_PRESETS.index(self.graphics_preset) if self.graphics_preset in GRAPHICS_PRESETS else 1
            self.graphics_preset = GRAPHICS_PRESETS[(cur_i + delta) % len(GRAPHICS_PRESETS)]
            self.apply_graphics_and_fog_settings(rebuild_chunks=True)
            self.save_current_settings()
            self.add_log('sys', f'[SETTINGS] Graphics Preset set to "{self.graphics_preset}"')
        elif idx == 5:  # Replay Valve Intro (valve.bik)
            self.start_valve_intro()
        elif idx == 6:  # Quit
            self.running = False

    def render_title(self, surf):
        w, h = surf.get_size()
        mouse_pos = pygame.mouse.get_pos()
        self.title_button_rects = []

        # 1. Classic Half-Life 2 3D Background Map Vignette (Left-side gradient only so 3D city shines through!)
        vignette = pygame.Surface((w, h), pygame.SRCALPHA)
        for band_i in range(28):
            bx_w = 24
            alpha_v = int(max(0, 195 * (1.0 - band_i / 28.0) ** 1.4))
            pygame.draw.rect(vignette, (6, 8, 10, alpha_v), (band_i * bx_w, 0, bx_w, h))
        # Subtle bottom bar gradient
        pygame.draw.rect(vignette, (6, 8, 10, 165), (0, h - 42, w, 42))
        surf.blit(vignette, (0, 0))

        # 2. Classic Half-Life 2 / Source Engine Title Logo on the Left
        lx = 62
        logo_y = 76
        # Iconic HL2 Orange Lambda Circle Emblem
        emblem_cx, emblem_cy = lx + 28, logo_y + 28
        pygame.draw.circle(surf, (20, 14, 8, 220), (emblem_cx, emblem_cy), 28)
        pygame.draw.circle(surf, (255, 150, 0), (emblem_cx, emblem_cy), 28, 3)
        lam_f = self.font_ModernLambda if hasattr(self, 'font_ModernLambda') else self.font_title
        lam_s = lam_f.render("λ", True, (255, 165, 20))
        surf.blit(lam_s, (emblem_cx - lam_s.get_width() // 2, emblem_cy - lam_s.get_height() // 2 - 2))

        hl2_title = self.font_vgui_title.render("H A L F - L I F E ²", True, (242, 240, 232))
        hl2_shadow = self.font_vgui_title.render("H A L F - L I F E ²", True, (10, 10, 10))
        surf.blit(hl2_shadow, (lx + 70, logo_y + 3))
        surf.blit(hl2_title, (lx + 68, logo_y + 1))

        sub_title = self.font_vgui_sub.render("TBMG: SOURCE ENGINE  //  VALVE VGUI2 & VPHYSICS EDITION", True, (255, 176, 0))
        surf.blit(sub_title, (lx + 70, logo_y + 52))

        # Genuine halflife2.ttf weapon silhouette strip under title
        if getattr(self, 'font_hl2_weapons', None) is not None:
            strip_x = lx + 70
            for w_slot in range(7):
                g_ch = SourceEngineBridge.WEAPON_ICON_GLYPHS.get(w_slot, 'd')
                g_ic = self.font_hl2_weapons.render(g_ch, True, (255, 176, 0))
                g_ic.set_alpha(150)
                surf.blit(g_ic, (strip_x, logo_y + 72))
                strip_x += g_ic.get_width() + 10

        # 3. Classic Source Engine GameMenu.res Left-Aligned Menu List
        menu_items = [
            ("NEW GAME", "Deploy into Half-Life 2 Tactical Survival Campaign (Combine Patrols & Scavenging)"),
            ("SANDBOX MODE (GMOD)", "Deploy with all 7 HL2 weapons, infinite reserve ammo, and VPhysics prop punting"),
            (f"CHAPTER / MAP:  < {self.current_map} >", "Click or press Left/Right to switch active 3D Source background map & sector"),
            ("HAMMER LEVEL EDITOR  [F2]", "Launch in-engine Source Hammer Map Editor to place barriers, props & NPCs"),
            (f"OPTIONS — VIDEO:  < {self.graphics_preset} >", "Cycle Source OpenGL renderer preset (Potato PC / Standard User / Alter Heavy)"),
            ("REPLAY VALVE INTRO  (VALVE.BIK)", "Watch the classic Valve 'Open Your Mind' & 'Powered by Source' Bink intro scene"),
            ("QUIT", "Shut down Source Engine C++ interfaces and exit to desktop"),
        ]

        menu_y = 225
        row_h = 44
        for i, (m_label, m_desc) in enumerate(menu_items):
            ry = menu_y + i * row_h
            item_rect = pygame.Rect(lx, ry, 520, 38)
            self.title_button_rects.append(item_rect)

            if item_rect.collidepoint(mouse_pos):
                if self.title_selection != i:
                    self.title_selection = i
                    if hasattr(self, 'snd_ui_rollover') and self.snd_ui_rollover:
                        self.snd_ui_rollover.play()

            is_sel = (i == self.title_selection)
            if is_sel:
                hl_bar = pygame.Surface((490, 36), pygame.SRCALPHA)
                hl_bar.fill((255, 165, 20, 38))
                pygame.draw.rect(hl_bar, (255, 176, 0, 230), (0, 0, 4, 36))
                surf.blit(hl_bar, (lx - 10, ry))
                txt_col = (255, 215, 90)
            else:
                txt_col = (225, 225, 220)

            sh_txt = self.font_vgui_menu.render(m_label, True, (12, 12, 12))
            fg_txt = self.font_vgui_menu.render(m_label, True, txt_col)
            surf.blit(sh_txt, (lx + 8, ry + 7))
            surf.blit(fg_txt, (lx + 6, ry + 5))

        # Active selection description below menu list
        sel_desc = menu_items[self.title_selection % len(menu_items)][1]
        desc_s = self.font_hud.render(sel_desc, True, (255, 185, 60))
        surf.blit(desc_s, (lx + 6, menu_y + len(menu_items) * row_h + 14))

        # 4. Compact Classic Source VGUI2 Engine Dialog in Bottom-Right (leaves 3D scene open!)
        pw, ph = 500, 215
        px, py = w - pw - 36, h - ph - 54
        vgui_box = pygame.Surface((pw, ph), pygame.SRCALPHA)
        vgui_box.fill((28, 32, 28, 205))
        pygame.draw.rect(vgui_box, (110, 120, 105, 190), (0, 0, pw, ph), 1, border_radius=4)
        pygame.draw.line(vgui_box, (255, 176, 0, 180), (12, 32), (pw - 12, 32), 1)
        surf.blit(vgui_box, (px, py))

        hdr = self.font_hud.render("SOURCE ENGINE C++ BRIDGE (NATIVE WIN64 DLLs)", True, (255, 176, 0))
        surf.blit(hdr, (px + 14, py + 10))

        ifaces = getattr(self.source_bridge, 'interfaces', {})
        vphys_ptr = ifaces.get("VPhysics031", "ACTIVE")
        vfs_ptr = ifaces.get("VFileSystem022", "ACTIVE")
        vgui_ptr = ifaces.get("VGUI_Panel009", "ACTIVE")
        n_vpk = len(getattr(self.source_bridge, 'vpk_packs', []))
        n_vmt = len(getattr(self.source_bridge, 'vmt_materials', {}))
        n_pd = len(getattr(self.source_bridge, 'prop_data', {}))
        dll_lines = [
            f"vphysics.dll   [VPhysics031]    @ {vphys_ptr}",
            f"filesystem.dll [VFileSystem022] @ {vfs_ptr}",
            f"vgui2.dll      [VGUI_Panel009]  @ {vgui_ptr}",
            f"VPK Archives   [{n_vpk} Mounted] : HL2 + CS:S + Sound + Textures",
            f"Source Scripts [{n_vmt} VMT / {n_pd} PropData] : surfaceproperties_hl2.txt",
            "Controls: [WASD] Move  [LMB/RMB] Fire/Aim  [1-7] Weapons  [E] Drive",
            "          [G] Punt Prop  [V] Camera  [H] Siren  [F2] Hammer  [ESC] Menu",
        ]
        for l_i, line_str in enumerate(dll_lines):
            col_l = (165, 235, 165) if l_i < 3 else ((255, 200, 90) if l_i < 5 else (205, 215, 205))
            ls = self.font_console.render(line_str, True, col_l)
            surf.blit(ls, (px + 14, py + 40 + l_i * 23))

        # 5. Bottom Status Bar
        foot_txt = self.font_console.render(
            f"SOURCE ENGINE BUILD 7000  •  PREVIEW MAP: {self.current_map.upper()}_BG (EMPTY LAYOUT — 0 ENTITIES)  •  [ENTER / CLICK] SELECT",
            True, (185, 190, 185)
        )
        surf.blit(foot_txt, (lx, h - 28))

    def render_loading(self, surf):
        w, h = surf.get_size()
        surf.fill((8, 10, 12, 255))
        title = self.font_title.render(f"TBMG — LOADING {self.current_map.upper()} ({self.graphics_preset})", True, (255, 176, 0))
        surf.blit(title, (w // 2 - title.get_width() // 2, h // 3))

        bar_w, bar_h = 380, 10
        bx, by = w // 2 - bar_w // 2, h // 2 + 20
        pygame.draw.rect(surf, (35, 35, 30), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surf, (255, 176, 0), (bx, by, int(bar_w * min(100, self.loading_progress) / 100), bar_h))

        msg = self.font_hud.render(self.loading_msg, True, (200, 185, 150))
        surf.blit(msg, (w // 2 - msg.get_width() // 2, by + 22))

    def render_crash(self, surf):
        w, h = surf.get_size()
        surf.fill((10, 0, 0, 255))
        title = self.font_large.render("SERVER CRASH DETECTED", True, COL_RED)
        surf.blit(title, (w // 2 - title.get_width() // 2, h // 3))
        msg = self.font_hud.render(f"Reason: {self.crash_reason} — Rebooting...", True, (220, 180, 180))
        surf.blit(msg, (w // 2 - msg.get_width() // 2, h // 3 + 45))

    # ═══════════════════════════════════════════════
    #  UPDATE LOOP
    # ═══════════════════════════════════════════════
    def update(self, dt):
        if self.paused:
            return

        if getattr(self, 'editor_status_timer', 0.0) > 0:
            self.editor_status_timer = max(0.0, self.editor_status_timer - dt)

        if self.is_loading:
            self.loading_progress += dt * 65
            if self.loading_progress >= 100:
                self.is_loading = False
                if not self.entities:
                    self.populate_world()
                self.add_log('info', f'{self.current_map} Online ({self.graphics_preset}) — [ESC] Pause/Settings, [F2] Map Editor, [G] Punt Props')
            return

        if self.is_crashed:
            self.crash_progress += dt * 25
            if self.crash_progress >= 100:
                self.is_crashed = False
                self.entities = [e for e in self.entities if e.alive and e.type not in ('charger', 'pillow')]
                self.add_log('sys', 'Server reboot complete. Props purged.')
            return

        self.sim_time += dt
        if getattr(self, 'spawn_protection_timer', 0.0) > 0:
            self.spawn_protection_timer = max(0.0, self.spawn_protection_timer - dt)
        if getattr(self, 'bump_cooldown', 0.0) > 0:
            self.bump_cooldown = max(0.0, self.bump_cooldown - dt)
        self.update_overwatch_dispatch(dt)
        self.hud_pulse += dt
        if self.weapon_fired > 0:
            self.weapon_fired = max(0.0, self.weapon_fired - dt * 5.5)
        if getattr(self, 'shotgun_pump_anim', 0.0) > 0:
            self.shotgun_pump_anim = max(0.0, self.shotgun_pump_anim - dt)
        if getattr(self, 'shotgun_pump_timer', 0.0) > 0:
            self.shotgun_pump_timer -= dt
            if self.shotgun_pump_timer <= 0:
                self.shotgun_pump_timer = 0.0
                if self.current_weapon == 3 and hasattr(self, 'snd_shotgun_cock') and self.snd_shotgun_cock:
                    self.snd_shotgun_cock.play()
                    self.shotgun_pump_anim = 0.32
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= dt
        if self.is_reloading:
            self.reload_timer += dt
            if self.current_weapon == 3:  # SPAS-12 Shotgun sequential shell reload
                if self.reload_timer >= self.reload_duration:
                    self.reload_timer = 0.0
                    clip_size = WEAPONS[3].get('clip_size', 6)
                    cur_clip = self.weapon_clips.get(3, 0)
                    is_sandbox = getattr(self, 'sandbox_mode', False) or getattr(self, 'cheat_mode', False)
                    avail = self.ammo.get('shells', 0) if not is_sandbox else 999

                    if cur_clip < clip_size and avail > 0:
                        self.weapon_clips[3] = cur_clip + 1
                        if not is_sandbox:
                            self.ammo['shells'] -= 1
                        if getattr(self, 'snd_shotgun_reload_list', None):
                            random.choice(self.snd_shotgun_reload_list).play()
                        elif hasattr(self, 'snd_shotgun_reload') and self.snd_shotgun_reload:
                            self.snd_shotgun_reload.play()
                        self.add_log('info', f'SPAS-12 loaded shell [{self.weapon_clips[3]}/{clip_size}]')

                    # Continue to next shell or finish with pump-action rack sound (shotgun_cock.wav)
                    cur_clip = self.weapon_clips.get(3, 0)
                    avail = self.ammo.get('shells', 0) if not is_sandbox else 999
                    if cur_clip >= clip_size or avail <= 0:
                        self.is_reloading = False
                        self.reload_timer = 0.0
                        self.shotgun_pump_timer = 0.14
                        self.add_log('info', f'SPAS-12 reload complete! [{cur_clip}/{clip_size}]')
            else:
                if self.reload_timer >= self.reload_duration:
                    self.is_reloading = False
                    self.reload_timer = 0.0
                    weap = WEAPONS[self.current_weapon]
                    clip_size = weap.get('clip_size', 0)
                    cur_clip = self.weapon_clips.get(self.current_weapon, 0)
                    needed = clip_size - cur_clip

                    is_sandbox = getattr(self, 'sandbox_mode', False) or getattr(self, 'cheat_mode', False)
                    if is_sandbox:
                        self.weapon_clips[self.current_weapon] = clip_size
                    else:
                        avail = self.ammo.get(weap['ammo_type'], 0)
                        added = min(needed, avail)
                        self.weapon_clips[self.current_weapon] += added
                        self.ammo[weap['ammo_type']] -= added
                    self.add_log('info', f'{weap["name"]} reloaded! [{self.weapon_clips[self.current_weapon]}/{clip_size}]')
        if self.weapon_switch_timer > 0:
            self.weapon_switch_timer = max(0.0, self.weapon_switch_timer - dt * 2.5)
        if self.weapon_hud_timer > 0:
            self.weapon_hud_timer = max(0.0, self.weapon_hud_timer - dt)
        if self.screen_shake > 0:
            self.screen_shake -= dt * 2.5
        if self.crosshair_hit > 0:
            self.crosshair_hit = max(0.0, self.crosshair_hit - dt * 3.5)
        if getattr(self, 'quickinfo_target', None):
            self.quickinfo_target['timer'] -= dt
            if self.quickinfo_target['timer'] <= 0:
                self.quickinfo_target = None
        if self.damage_flash > 0:
            self.damage_flash -= dt * 3
        if self.berserk_timer > 0:
            self.berserk_timer -= dt
        if self.invuln_timer > 0:
            self.invuln_timer -= dt

        keys = pygame.key.get_pressed()
        mouse_btns = pygame.mouse.get_pressed()
        if getattr(self, 'arms_shop_open', False) or getattr(self, 'vehicle_spawner_open', False):
            class _DummyKeys:
                def __getitem__(self, k):
                    return False
            keys = _DummyKeys()
            mouse_btns = (False, False, False)

        if self.current_map in ("MainCity2", "BigCity5", "driving Test map") and getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None):
            self._update_player_driving(dt, pygame.key.get_pressed())

        if self.current_map == "BigCity5":
            self._update_traffic_system(dt)

        if getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None):
            self.is_moving = False
            self.is_sprinting = False
            self.player_vx = 0.0
            self.player_vy = 0.0
            self.player_vz = 0.0
            self.step_timer = 0.0
        else:
            # Check Source Engine Water Cell (cell == 7) for Buoyancy & Swimming Physics
            px_i, py_i = int(self.player_x), int(self.player_y)
            in_water_now = (0 <= px_i < MAP_W and 0 <= py_i < MAP_H and MAP[py_i][px_i] == 7)
            if in_water_now and not self.player_in_water:
                self.add_log('info', '[VPHYSICS WATER] Entered water canal — Hold [SPACE] to swim up, push floating props!')
            self.player_in_water = in_water_now

            if self.player_in_water:
                # Source Engine Water Buoyancy & Swimming
                wave_bob = math.sin(self.hud_pulse * 3.0 + self.player_x * 0.9 + self.player_y * 0.9) * 0.035
                target_water_z = -0.22 + wave_bob
                if keys[pygame.K_SPACE]:
                    # Swim upward / tread water high
                    self.player_vz = min(2.4, self.player_vz + 8.5 * dt)
                else:
                    # Buoyancy spring toward surface equilibrium
                    buoyancy_accel = (target_water_z - self.player_z) * 6.5
                    self.player_vz += buoyancy_accel * dt
                    self.player_vz *= max(0.0, 1.0 - 4.2 * dt)  # Fluid viscosity damping
                self.player_z += self.player_vz * dt
                self.player_z = max(-0.42, min(0.35, self.player_z))
            else:
                # Walkable stairs, ramp gradients, and second-story building floors
                ground_z = self.get_walkable_surface_z(self.player_x, self.player_y, self.player_z)
                if self.player_z < ground_z:
                    # Step up onto stairs/ramp/platform smoothly
                    step_speed = 14.0
                    self.player_z = min(ground_z, self.player_z + step_speed * dt)
                    self.player_vz = 0.0
                elif self.player_z > ground_z:
                    # In air (falling or jumping): apply gravity
                    self.player_vz -= 9.8 * dt
                    self.player_z += self.player_vz * dt
                    if self.player_z <= ground_z:
                        self.player_z = ground_z
                        self.player_vz = 0.0
                else:
                    self.player_vz = 0.0

                # Jump key [SPACE] on dry land
                if keys[pygame.K_SPACE] and abs(self.player_z - ground_z) < 0.08 and self.player_vz <= 0:
                    self.player_vz = 4.2
                    if hasattr(self, 'snd_footstep') and self.snd_footstep:
                        self.snd_footstep.play()

            # Mouse ADS & Fire state
            mouse_btns = pygame.mouse.get_pressed()
            self.aim_zoom = bool(mouse_btns[2]) and not self.admin_open and not self.paused and not getattr(self, 'map_editor_active', False) and not getattr(self, 'map_editor_open', False) and not getattr(self, 'arms_shop_open', False)

            # Player Movement & Call of Duty / Half-Life 2 SHIFT + W Tactical Sprint
            shift_held = bool(keys[pygame.K_LSHIFT] or keys[pygame.K_RSHIFT])
            w_held = bool(keys[pygame.K_w])

            if shift_held and w_held and self.aux_power > 1.0 and not self.aim_zoom:
                if not self.is_sprinting and hasattr(self, 'snd_sprint'):
                    self.snd_sprint.play()
                self.is_sprinting = True
                self.aux_power = max(0.0, self.aux_power - dt * 22.0)
            else:
                self.is_sprinting = False
                if not shift_held or not w_held:
                    self.aux_power = min(100.0, self.aux_power + dt * 18.0)

            # Smoothly blend Sprint, Iron Sights (ADS), and Dynamic FOV
            target_sprint = 1.0 if self.is_sprinting else 0.0
            self.sprint_blend += (target_sprint - self.sprint_blend) * min(1.0, dt * 11.0)

            target_ads = 1.0 if (self.aim_zoom and not self.is_sprinting) else 0.0
            self.ads_blend += (target_ads - self.ads_blend) * min(1.0, dt * 14.0)

            target_fov = 78.0 if self.is_sprinting else (45.0 if self.aim_zoom else 68.0)
            self.current_fov += (target_fov - self.current_fov) * min(1.0, dt * 12.0)

            speed = SPRINT_SPEED if self.is_sprinting else (MOVE_SPEED * 0.65 if self.aim_zoom else MOVE_SPEED)
            if self.player_in_water:
                speed *= 0.72  # Source Engine fluid drag while wading/swimming
            dx, dy = 0.0, 0.0
            if w_held:
                dx += math.cos(self.player_angle) * speed * dt
                dy += math.sin(self.player_angle) * speed * dt
            if keys[pygame.K_s]:
                dx -= math.cos(self.player_angle) * speed * 0.85 * dt
                dy -= math.sin(self.player_angle) * speed * 0.85 * dt
            if keys[pygame.K_a]:
                dx += math.cos(self.player_angle - math.pi / 2) * speed * 0.85 * dt
                dy += math.sin(self.player_angle - math.pi / 2) * speed * 0.85 * dt
            if keys[pygame.K_d]:
                dx += math.cos(self.player_angle + math.pi / 2) * speed * 0.85 * dt
                dy += math.sin(self.player_angle + math.pi / 2) * speed * 0.85 * dt

            self.is_moving = (abs(dx) + abs(dy)) > 0.005
            self.player_vx = (dx / dt) if (dt > 0 and self.is_moving) else 0.0
            self.player_vy = (dy / dt) if (dt > 0 and self.is_moving) else 0.0
            if self.is_moving:
                self.walk_phase += dt * (13.5 if self.is_sprinting else 8.0)
                self.step_timer += dt
                step_interval = 0.24 if self.is_sprinting else 0.38
                if self.step_timer > step_interval:
                    self.step_timer = 0
                    self.play_surface_footstep()

            P_RADIUS = 0.18  # Allows walking freely through 1-block wide corridors between buildings!
            if self.noclip:
                self.player_x += dx
                self.player_y += dy
            else:
                nx = self.player_x + dx
                ny = self.player_y + dy
                pz = self.player_z

                # X-axis movement with wall sliding (unblocked in 1-block corridors between buildings)
                if not self.is_position_blocked(nx, self.player_y, radius=P_RADIUS, pz=pz):
                    self.player_x = nx

                # Y-axis movement with wall sliding (unblocked in 1-block corridors between buildings)
                if not self.is_position_blocked(self.player_x, ny, radius=P_RADIUS, pz=pz):
                    self.player_y = ny

                # Unstuck / Wall Depenetration Safeguard:
                # If player is ever stuck inside a wall or solid prop (from knockback, spawn, or edits), immediately pop out!
                if self.is_position_blocked(self.player_x, self.player_y, radius=0.14, pz=pz):
                    for r_dist in (0.15, 0.30, 0.50, 0.85):
                        found_open = False
                        for ang_deg in (0, 45, 90, 135, 180, 225, 270, 315):
                            rad = math.radians(ang_deg)
                            test_x = self.player_x + math.cos(rad) * r_dist
                            test_y = self.player_y + math.sin(rad) * r_dist
                            if not self.is_position_blocked(test_x, test_y, radius=0.18, pz=pz):
                                self.player_x = test_x
                                self.player_y = test_y
                                found_open = True
                                break
                        if found_open:
                            break

        self.update_doors(dt)

        for i, (wx, wy, wid, wname) in enumerate(self.weapon_pickup_positions):
            if not self.weapon_pickups_alive[i]:
                continue
            if math.sqrt((self.player_x - wx) ** 2 + (self.player_y - wy) ** 2) < 1.1:
                self.weapons_owned[wid] = True
                self.current_weapon = wid
                self.weapon_switch_timer = 0.28
                self.weapon_hud_timer = 3.0
                self.weapon_pickups_alive[i] = False
                self.play_pickup()
                self.add_log('info', f'Picked up {wname}!')
                atype = WEAPONS[wid]['ammo_type']
                if atype:
                    self.ammo[atype] = min(self.ammo_max[atype], self.ammo.get(atype, 0) + WEAPONS[wid]['ammo_use'] * 10)

        # ── ENTITY SIMULATION & COMBAT (FROZEN WHEN MAP EDITOR IS ACTIVE) ──
        if not self.map_editor_active:
            for e in self.entities:
                if e.alive:
                    e.update(dt, self)

            # Entity-to-entity & player collision physics
            alive_ents = [e for e in self.entities if e.alive]
            for i in range(len(alive_ents)):
                a = alive_ents[i]
                # Soft physical pushback between player and entity
                dx_p = self.player_x - a.x
                dy_p = self.player_y - a.y
                pdist = math.hypot(dx_p, dy_p)
                if 0 < pdist < 0.78:
                    nx_p = dx_p / pdist
                    ny_p = dy_p / pdist
                    self.apply_player_knockback(nx_p, ny_p, dist=0.04)
                    a.x -= nx_p * 0.04
                    a.y -= ny_p * 0.04
                    if a.type == 'mcpd':
                        if self.wanted_level > 0:
                            # Only attack on contact if the player is actively wanted and engaged in combat!
                            if getattr(a, 'melee_cooldown', 0) <= 0:
                                a.melee_cooldown = 0.95
                                self.player_take_damage(8)
                                self.add_log('warn', f'Combine CP #{a.id}: Stunstick shock on contact! (-8 HP)')
                        else:
                            # Peaceful player bump: issue verbal warning with cooldown (NO DAMAGE, NO WANTED STARS!)
                            if getattr(a, 'bump_warn_timer', 0) <= 0:
                                a.bump_warn_timer = 4.5
                                self.add_log('sys', f'Combine CP #{a.id}: "Citizen, step back. Move along." [PROXIMITY WARNING]', priority='ambient')
                                self.play_combine_vo(a.x, a.y)

                for j in range(i + 1, len(alive_ents)):
                    b = alive_ents[j]
                    dx_c, dy_c = b.x - a.x, b.y - a.y
                    dist_c = math.sqrt(dx_c * dx_c + dy_c * dy_c)
                    if 0 < dist_c < 0.75:
                        nx_c, ny_c = dx_c / dist_c, dy_c / dist_c
                        a.x -= nx_c * 0.04
                        a.y -= ny_c * 0.04
                        b.x += nx_c * 0.04
                        b.y += ny_c * 0.04
                        # Friendly pushback between cops and civilians without execution
                        if a.type in ('charger', 'crate', 'barrel', 'explosive_barrel') or b.type in ('charger', 'crate', 'barrel', 'explosive_barrel'):
                            other = b if a.type in ('charger', 'crate', 'barrel', 'explosive_barrel') else a
                            prop = a if other is b else b
                            speed_p = math.hypot(prop.vx, prop.vy)
                            if speed_p > 1.8:
                                other.vx += nx_c * 4.5
                                other.vy += ny_c * 4.5
                                if hasattr(other, 'take_damage'):
                                    other.take_damage(int(speed_p * 3.5), self)
                                self._play_spatial(self.snd_metal, a.x, a.y)

            self.entities = [e for e in self.entities if e.alive]

            # MCPD Respawn Queue
            for item in self.mcpd_respawn_queue:
                item['timer'] -= dt
            ready = [item for item in self.mcpd_respawn_queue if item['timer'] <= 0]
            self.mcpd_respawn_queue = [item for item in self.mcpd_respawn_queue if item['timer'] > 0]
            for _ in ready:
                self.entities.append(MCPDUnit(11.5 + random.uniform(-1, 1), 19.5 + random.uniform(-1, 1)))
                self.add_log('sys', '[MCPD DISPATCH] Overwatch reinforcement arrived at Precinct')

            # TBMG Civilian Pay-to-Respawn Economy Queue
            self.update_civilian_respawns(dt)

            # Distant Urban Ambient Gunfire Soundscape
            self.update_ambient_gunfire(dt)

            # Wanted Level Decay
            if self.wanted_level > 0:
                self.wanted_decay_timer -= dt
                if self.wanted_decay_timer <= 0:
                    self.wanted_level = max(0, self.wanted_level - 1)
                    self.wanted_decay_timer = 12.0
                    self.add_log('info', f'[WANTED] Overwatch alert cooled to {self.wanted_level} stars')

            for p in self.projectiles:
                if p.alive:
                    p.update(dt, self)
            self.projectiles = [p for p in self.projectiles if p.alive]

        for ex in self.explosions_list:
            if ex.alive:
                ex.update(dt)
        self.explosions_list = [ex for ex in self.explosions_list if ex.alive]

        for tr in self.tracers:
            tr[7] -= dt
        self.tracers = [tr for tr in self.tracers if tr[7] > 0]

        for sc in self.shell_casings:
            sc[0] += sc[3] * dt
            sc[1] += sc[4] * dt
            sc[2] += sc[5] * dt
            sc[4] -= 6.5 * dt
            sc[6] += dt
        self.shell_casings = [sc for sc in self.shell_casings if sc[6] < 0.45]

        for p in self.pickups:
            if p.alive:
                p.update(dt, self)
        self.pickups = [p for p in self.pickups if p.alive]

        for c in self.corpses:
            c['age'] += dt
        self.corpses = [c for c in self.corpses if c['age'] < 30]

        for entry in self.console_log:
            entry['age'] += dt

        if self.cheat_mode:
            self.player_health = 100
            self.player_armor = 100

        if mouse_btns[0] and not self.admin_open and not self.paused and not getattr(self, 'map_editor_active', False) and not getattr(self, 'map_editor_open', False) and not getattr(self, 'arms_shop_open', False) and not getattr(self, 'vehicle_spawner_open', False) and not getattr(self, 'in_vehicle', False):
            self.fire_weapon()

    def run(self):
        while self.running:
            dt = min(self.clock.tick(FPS) / 1000.0, 0.05)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    if self.game_state == self.STATE_INTRO:
                        if event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_ESCAPE):
                            self.finish_intro_to_title()
                        continue

                    if self.game_state == self.STATE_TITLE:
                        num_title_opts = 7
                        if event.key == pygame.K_UP:
                            self.title_selection = (self.title_selection - 1) % num_title_opts
                            if hasattr(self, 'snd_ui_rollover') and self.snd_ui_rollover:
                                self.snd_ui_rollover.play()
                        elif event.key == pygame.K_DOWN:
                            self.title_selection = (self.title_selection + 1) % num_title_opts
                            if hasattr(self, 'snd_ui_rollover') and self.snd_ui_rollover:
                                self.snd_ui_rollover.play()
                        elif event.key == pygame.K_LEFT:
                            self._execute_title_option(self.title_selection, delta=-1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_RETURN, pygame.K_SPACE):
                            self._execute_title_option(self.title_selection, delta=1)
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                        continue

                    # In-Game Vehicle Spawner Modal Key Handling (Big City 5 Exclusive)
                    if getattr(self, 'vehicle_spawner_open', False):
                        if event.key in (pygame.K_ESCAPE, pygame.K_e):
                            self.toggle_vehicle_spawner()
                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8, pygame.K_9, pygame.K_0):
                            idx = 9 if event.key == pygame.K_0 else (event.key - pygame.K_1)
                            if idx < len(VEHICLE_CATALOG):
                                self.spawn_vehicle(VEHICLE_CATALOG[idx]["id"], drive_immediately=True)
                        continue

                    # In-Game Arms Shop Modal Key Handling
                    if getattr(self, 'arms_shop_open', False):
                        if event.key in (pygame.K_ESCAPE, pygame.K_e):
                            self.toggle_arms_shop()
                        elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7, pygame.K_8):
                            idx = event.key - pygame.K_1
                            if idx < len(self.arms_shop_catalog):
                                self.buy_shop_item(self.arms_shop_catalog[idx]["wid"])
                        continue

                    # In-Game Pause Menu Key Handling
                    if self.paused:
                        items_count = len(self._get_pause_menu_items())
                        if event.key == pygame.K_ESCAPE:
                            self.paused = False
                            pygame.mouse.set_visible(self.map_editor_open and self.automap)
                            pygame.event.set_grab(not (self.map_editor_open and self.automap))
                        elif event.key == pygame.K_UP:
                            self.pause_selection = (self.pause_selection - 1) % items_count
                        elif event.key == pygame.K_DOWN:
                            self.pause_selection = (self.pause_selection + 1) % items_count
                        elif event.key == pygame.K_LEFT:
                            self._execute_pause_option(self.pause_selection, delta=-1)
                        elif event.key in (pygame.K_RIGHT, pygame.K_RETURN):
                            self._execute_pause_option(self.pause_selection, delta=1)
                        continue

                    if event.key == pygame.K_ESCAPE:
                        if getattr(self, 'vehicle_spawner_open', False):
                            self.toggle_vehicle_spawner()
                        elif getattr(self, 'arms_shop_open', False):
                            self.toggle_arms_shop()
                        elif self.admin_open:
                            self.toggle_admin()
                        elif self.automap:
                            self.automap = False
                            pygame.mouse.set_visible(False)
                            pygame.event.set_grab(True)
                        else:
                            # Open In-Game Pause & Settings Menu instead of exiting to Title
                            self.paused = True
                            self.pause_selection = 0
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)
                    elif event.key == pygame.K_F1:
                        self.toggle_admin()
                    elif event.key == pygame.K_F2:
                        self.toggle_map_editor()
                        pygame.mouse.set_visible(self.map_editor_active and self.automap)
                        pygame.event.set_grab(not (self.map_editor_active and self.automap))
                    elif event.key == pygame.K_F5:
                        self.save_custom_map_state()
                    elif event.key == pygame.K_F6:
                        self.load_custom_map_state()
                    elif event.key == pygame.K_F7:
                        self.reset_map_to_default()
                    elif event.key == pygame.K_TAB:
                        self.automap = not self.automap
                        if self.map_editor_active:
                            pygame.mouse.set_visible(self.automap)
                            pygame.event.set_grab(not self.automap)
                    elif event.key == pygame.K_q and self.map_editor_active:
                        self.editor_idx = (self.editor_idx - 1) % len(MAP_EDITOR_PALETTE)
                        _, _, label = MAP_EDITOR_PALETTE[self.editor_idx]
                        self.editor_status_msg = f"Selected: {label}"
                        self.editor_status_timer = 2.5
                    elif event.key == pygame.K_e:
                        if self.map_editor_active:
                            self.editor_idx = (self.editor_idx + 1) % len(MAP_EDITOR_PALETTE)
                            _, _, label = MAP_EDITOR_PALETTE[self.editor_idx]
                            self.editor_status_msg = f"Selected: {label}"
                            self.editor_status_timer = 2.5
                        elif getattr(self, 'in_vehicle', False):
                            self.exit_vehicle()
                        elif self.current_map in ("MainCity2", "BigCity5", "driving Test map") and (
                            (self.current_map == "driving Test map" and math.hypot(self.player_x - 20.5, self.player_y - 23.5) < 2.8) or
                            (self.current_map == "MainCity2" and math.hypot(self.player_x - 15.2, self.player_y - 31.0) < 2.8) or
                            (self.current_map == "BigCity5" and math.hypot(self.player_x - 15.2, self.player_y - 32.0) < 2.8)
                        ):
                            self.toggle_vehicle_spawner()
                        elif self.current_map in ("MainCity2", "BigCity5", "driving Test map") and getattr(self, 'vehicles', []):
                            near_v = min(self.vehicles, key=lambda v: math.hypot(self.player_x - v.x, self.player_y - v.y), default=None)
                            if near_v and math.hypot(self.player_x - near_v.x, self.player_y - near_v.y) < 2.5:
                                self.enter_vehicle(near_v)
                            else:
                                shop_x, shop_y = self.get_arms_shop_location()
                                if math.hypot(self.player_x - shop_x, self.player_y - shop_y) < 3.2:
                                    self.toggle_arms_shop()
                                else:
                                    self.check_nearby_doors()
                        else:
                            shop_x, shop_y = self.get_arms_shop_location()
                            if math.hypot(self.player_x - shop_x, self.player_y - shop_y) < 3.2:
                                self.toggle_arms_shop()
                            else:
                                self.check_nearby_doors()
                    elif event.key == pygame.K_r:
                        if self.map_editor_active:
                            self.editor_yaw = (self.editor_yaw + 45.0) % 360.0
                            self.editor_status_msg = f"Rotated object to {int(self.editor_yaw)} deg"
                            self.editor_status_timer = 2.5
                        else:
                            self.start_reload()
                    elif (event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE) and self.map_editor_active:
                        self.editor_delete_at()
                    elif event.key == pygame.K_g:
                        self.punt_physics_prop()
                    elif event.key == pygame.K_h and getattr(self, 'in_vehicle', False) and getattr(self, 'active_vehicle', None):
                        veh = self.active_vehicle
                        if getattr(veh, 'is_police', False):
                            veh.siren_on = not getattr(veh, 'siren_on', False)
                            if veh.siren_on and hasattr(self, 'snd_police_siren') and self.snd_police_siren:
                                self.snd_police_siren.play()
                            state_str = "ACTIVE (Red/Blue Strobes + Wail)" if veh.siren_on else "OFF"
                            self.add_log('sys', f'[MCPD INTERCEPTOR] Emergency Lightbar & Siren: {state_str}')
                        else:
                            if hasattr(self, 'snd_police_siren') and self.snd_police_siren:
                                self.snd_police_siren.play()
                    elif event.key == pygame.K_v:
                        self.camera_mode = (self.camera_mode + 1) % 3
                        cam_labels = ["3rd-Person Tactical", "3rd-Person Wide", "1st-Person [CoD/HL2]"]
                        self.add_log('info', f'Camera switched to {cam_labels[self.camera_mode]}')
                    elif event.key == pygame.K_SPACE and not self.player_in_water and self.player_z <= 0.01:
                        self.player_vz = 4.2
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7):
                        slot = event.key - pygame.K_1
                        if self.weapons_owned.get(slot, False):
                            if self.current_weapon != slot:
                                self.is_reloading = False
                                self.reload_timer = 0.0
                                self.weapon_switch_timer = 0.28
                                if hasattr(self, 'snd_wpn_move'):
                                    self.snd_wpn_move.play()
                            self.current_weapon = slot
                            self.weapon_hud_timer = 3.0
                        else:
                            if hasattr(self, 'snd_metal'):
                                self.snd_metal.play()
                            weap_name = WEAPONS[slot]['name']
                            self.add_log('warn', f'LOCKED: {weap_name} not owned! Purchase at TBMG Arms Shop kiosk [E].')

                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == self.STATE_INTRO:
                        self.finish_intro_to_title()
                        continue
                    elif self.game_state == self.STATE_TITLE and event.button == 1:
                        mouse_pos = pygame.mouse.get_pos()
                        clicked = False
                        for i, r in enumerate(getattr(self, 'title_button_rects', [])):
                            if r.collidepoint(mouse_pos):
                                self.title_selection = i
                                self._execute_title_option(i, delta=1)
                                clicked = True
                                break
                        if not clicked:
                            self._execute_title_option(self.title_selection, delta=1)
                    elif self.game_state == self.STATE_TITLE and event.button == 3:
                        mouse_pos = pygame.mouse.get_pos()
                        for i, r in enumerate(getattr(self, 'title_button_rects', [])):
                            if r.collidepoint(mouse_pos):
                                self.title_selection = i
                                self._execute_title_option(i, delta=-1)
                                break
                    elif self.game_state == self.STATE_PLAYING:
                        if getattr(self, 'vehicle_spawner_open', False):
                            if event.button == 1:
                                mouse_pos = pygame.mouse.get_pos()
                                handled = False
                                for rect, vid in getattr(self, 'vehicle_button_rects', []):
                                    if rect.collidepoint(mouse_pos):
                                        handled = True
                                        if vid == 'close':
                                            self.toggle_vehicle_spawner()
                                        else:
                                            self.spawn_vehicle(vid, drive_immediately=True)
                                        break
                                if not handled:
                                    mw, mh = 960, 530
                                    mx, my = (SCREEN_W - mw) // 2, (SCREEN_H - mh) // 2
                                    if not pygame.Rect(mx, my, mw, mh).collidepoint(mouse_pos):
                                        self.toggle_vehicle_spawner()
                            continue
                        elif getattr(self, 'arms_shop_open', False):
                            if event.button == 1:
                                mouse_pos = pygame.mouse.get_pos()
                                handled = False
                                for rect, wid in getattr(self, 'shop_button_rects', []):
                                    if rect.collidepoint(mouse_pos):
                                        handled = True
                                        if wid == 'close':
                                            self.toggle_arms_shop()
                                        else:
                                            self.buy_shop_item(wid)
                                        break
                                if not handled:
                                    mw, mh = 680, 480
                                    mx, my = (SCREEN_W - mw) // 2, (SCREEN_H - mh) // 2
                                    if not pygame.Rect(mx, my, mw, mh).collidepoint(mouse_pos):
                                        self.toggle_arms_shop()
                            continue
                        elif self.paused:
                            mouse_pos = pygame.mouse.get_pos()
                            handled = False
                            for row_rect, minus_r, plus_r, idx in getattr(self, 'pause_button_rects', []):
                                if minus_r and minus_r.collidepoint(mouse_pos):
                                    self.pause_selection = idx
                                    self._execute_pause_option(idx, delta=-1)
                                    handled = True
                                    break
                                elif plus_r and plus_r.collidepoint(mouse_pos):
                                    self.pause_selection = idx
                                    self._execute_pause_option(idx, delta=1)
                                    handled = True
                                    break
                                elif row_rect.collidepoint(mouse_pos):
                                    self.pause_selection = idx
                                    if event.button == 1:
                                        self._execute_pause_option(idx, delta=1)
                                    elif event.button == 3:
                                        self._execute_pause_option(idx, delta=-1)
                                    elif event.button == 4:
                                        self._execute_pause_option(idx, delta=1)
                                    elif event.button == 5:
                                        self._execute_pause_option(idx, delta=-1)
                                    handled = True
                                    break
                            if handled:
                                continue
                        elif self.admin_open and event.button == 1:
                            mouse_pos = pygame.mouse.get_pos()
                            w, h = SCREEN_W, SCREEN_H
                            panel_w, panel_h = 440, 450
                            px, spy = w // 2 - panel_w // 2, h // 2 - panel_h // 2
                            for i, (_, action) in enumerate(self.admin_items):
                                rect = pygame.Rect(px + 12, spy + 38 + i * 24, panel_w - 24, 21)
                                if rect.collidepoint(mouse_pos):
                                    action()
                                    break
                        elif self.map_editor_active and event.button in (1, 3):
                            target_xy = None
                            if self.automap and hasattr(self, '_automap_transform'):
                                ox, oy, scale = self._automap_transform
                                mx, my = pygame.mouse.get_pos()
                                gx = (mx - ox) / max(1e-5, scale)
                                gy = (my - oy) / max(1e-5, scale)
                                if 0 <= gx < MAP_W and 0 <= gy < MAP_H:
                                    target_xy = (gx, gy)
                            if event.button == 1:
                                if target_xy:
                                    self.editor_place_at(target_xy[0], target_xy[1])
                                else:
                                    self.editor_place_at()
                            elif event.button == 3:
                                if target_xy:
                                    self.editor_delete_at(target_xy[0], target_xy[1])
                                else:
                                    self.editor_delete_at()
                        elif self.map_editor_active and event.button in (4, 5):
                            delta = 1 if event.button == 5 else -1
                            self.editor_idx = (self.editor_idx + delta) % len(MAP_EDITOR_PALETTE)
                            _, _, label = MAP_EDITOR_PALETTE[self.editor_idx]
                            self.editor_status_msg = f"Selected: {label}"
                            self.editor_status_timer = 2.0
                        elif event.button == 1 and not self.map_editor_active and not getattr(self, 'vehicle_spawner_open', False) and not getattr(self, 'in_vehicle', False):
                            self.fire_weapon()

                elif event.type == pygame.MOUSEMOTION:
                    if self.game_state == self.STATE_TITLE:
                        mpos = event.pos
                        for i, r in enumerate(getattr(self, 'title_button_rects', [])):
                            if r.collidepoint(mpos):
                                self.title_selection = i
                                break
                    elif not self.admin_open and not self.paused and not getattr(self, 'arms_shop_open', False) and not getattr(self, 'vehicle_spawner_open', False) and self.game_state == self.STATE_PLAYING:
                        if not (self.map_editor_active and self.automap):
                            mx, my = event.rel
                            sens_mult = 0.55 if self.aim_zoom else 1.0
                            self.player_angle += mx * MOUSE_SENS * sens_mult
                            self.player_pitch = max(-1.38, min(1.38, self.player_pitch + my * MOUSE_SENS * 0.7 * sens_mult))

                elif event.type == pygame.MOUSEWHEEL and self.game_state == self.STATE_PLAYING and not self.admin_open and not self.paused and not getattr(self, 'arms_shop_open', False):
                    if self.map_editor_active:
                        step = -1 if event.y > 0 else 1
                        self.editor_idx = (self.editor_idx + step) % len(MAP_EDITOR_PALETTE)
                        _, _, label = MAP_EDITOR_PALETTE[self.editor_idx]
                        self.editor_status_msg = f"Selected: {label}"
                        self.editor_status_timer = 2.5
                    else:
                        owned = sorted([k for k, v in self.weapons_owned.items() if v])
                        if owned:
                            idx = owned.index(self.current_weapon) if self.current_weapon in owned else 0
                            idx = (idx + (1 if event.y > 0 else -1)) % len(owned)
                            if self.current_weapon != owned[idx]:
                                self.is_reloading = False
                                self.reload_timer = 0.0
                            self.current_weapon = owned[idx]
                            self.weapon_switch_timer = 0.28
                            self.weapon_hud_timer = 3.0
                            if hasattr(self, 'snd_wpn_move'):
                                self.snd_wpn_move.play()

            self.hud_surf.fill((0, 0, 0, 0))

            if self.game_state == self.STATE_INTRO:
                self.intro_timer += dt
                if self.intro_timer >= 10.0:
                    self.finish_intro_to_title()
                else:
                    gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                    self.render_intro(self.hud_surf)
                    self.blit_hud_overlay_to_opengl()
                    pygame.display.flip()
                    continue

            if self.game_state == self.STATE_TITLE:
                self.title_timer += dt
                self.sim_time += dt
                gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.render_3d_scene()
                self.render_title(self.hud_surf)
                self.blit_hud_overlay_to_opengl()
                pygame.display.flip()
                continue

            self.update(dt)

            if self.is_loading:
                gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.render_loading(self.hud_surf)
            elif self.is_crashed:
                gl.glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
                self.render_crash(self.hud_surf)
            else:
                self.render_3d_scene()
                self.render_hud(self.hud_surf)
                if not self.automap:
                    self.render_minimap(self.hud_surf)
                else:
                    self.render_automap(self.hud_surf)
                self.render_map_editor_hud(self.hud_surf)
                self.render_admin(self.hud_surf)
                self.render_pause_menu(self.hud_surf)

            self.blit_hud_overlay_to_opengl()
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == '__main__':
    game = Game()
    game.run()


