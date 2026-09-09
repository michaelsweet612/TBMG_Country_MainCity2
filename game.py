#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════════╗
║  TBMG_Country_MainCity2 — DOOM-STYLE FPS                        ║
║  Inspired by id Software's DOOM (1993) architecture              ║
║  Raycasting Engine · DarkRP · sv_cheats 1                        ║
║  7 Weapons · AI States · Doors · Pickups · Automap               ║
║  Build 6660 | Tickrate 35 | Instability: HELLISH                 ║
╚══════════════════════════════════════════════════════════════════╝
"""

import pygame
import math
import random
import sys
import os
import array
import time
import heapq

# ═══════════════════════════════════════════════════
#  CONSTANTS & CONFIGURATION
# ═══════════════════════════════════════════════════
TITLE = "TBMG_Country_MainCity2 — DOOM [sv_cheats 1]"
SCREEN_W = 1024
SCREEN_H = 640
INTERNAL_W = 512
INTERNAL_H = 320
FOV = math.pi / 3      # 60 degrees
HALF_FOV = FOV / 2
NUM_RAYS = INTERNAL_W
DELTA_ANGLE = FOV / NUM_RAYS
MAX_DEPTH = 40.0
SCALE = INTERNAL_W / NUM_RAYS
TILE_SIZE = 64
FPS = 60
MOUSE_SENS = 0.003
MOVE_SPEED = 3.5
SPRINT_SPEED = 6.0

# Colors
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
SOUND_RANGE = 15.0          # Max distance (tiles) for spatial audio
SOUND_CHANNEL_BUDGET = 6    # Max concurrent NPC sound channels

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
    "     People write laws just to avoid upsetting him.",
    "",
    "3. Law Enforcement:",
    "   - Main City Police Department (MCPD) operates like a criminal syndicate (FBI investigated).",
    "   - MCPD is trigger-happy: bumping into them gets you shot instantly.",
    "   - Rank is based on kill count. MCPD kills ~2 million people every day.",
    "   - Elite Combine Protection Units (ECPU) outrank all. Opaque helmets, no warnings, always shoot.",
    "",
    "4. Bizarre Laws & Culture:",
    "   - Jaywalking: drivers are encouraged to run over jaywalkers.",
    "   - Traffic lights: decorations. Zero crashes miraculously.",
    "   - Church: Secretly illegal to shoot a bullet inside (736,000-star wanted level).",
    "   - Money: Citizens can print their own money, but getting caught gives a 7-star wanted level.",
    "   - Events: 'Rubber Ducky Battle' and 'Pink Day' (45% must buy pink paint).",
    "   - Survival Guide: Must carry 4 Billion Mountain Dew bottles to look cool.",
    "",
    "5. Multiverse Conquest:",
    "   - TBMG claims right to invade any universe (Universal Collapse Treaty 9982-A).",
    "   - Combine Empire made TBMG its primary force for conquering other universes.",
    "   - Cannot manufacture normal bullets (obsolete), so they use Combine Energy Balls instead.",
    "   - Formed 'TBMG NATO', an internet-driven coalition that mocks global power structures."
]

# ═══════════════════════════════════════════════════
#  MAP DATA — MainCity2 DOOM EDITION
# ═══════════════════════════════════════════════════
# Wall types:
# 0 = empty
# 1 = concrete (standard)
# 2 = dark purple (ECPU HQ)
# 3 = dark blue (MCPD)
# 4 = rust/red (RPG Depot)
# 5 = dirty brown (Slums)
# 6 = door (interactive)
# 7 = pink/black checkerboard (texture fail)
# 8 = ERROR wall (bright red)
# 9 = HQ interior (president office)
# 10 = metal reinforced (armory)
# 10 = metal reinforced (armory)
# 11 = sewer/green (underground)
# 12 = military compound wall (dark green)

MAP = [
    #0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7 8 9 0 1 2 3 4 5 6 7
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  # 0
    [1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 1 - Church of Server
    [1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,2,2,2,2,2,1,0,0,0,0,0,0,0,1,0,0,9,9,0,9,9,0,0,0,0,0,0,0,0,1],  # 2
    [1,0,0,0,0,0,0,0,0,0,0,0,6,0,0,0,0,2,0,0,0,0,2,1,0,0,10,10,0,0,0,1,0,0,9,0,0,0,9,0,0,0,0,0,0,0,0,1],  # 3
    [1,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,2,0,9,0,0,2,1,0,0,10,0,0,0,0,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 4
    [1,0,0,0,0,0,1,0,0,0,0,0,1,0,0,0,0,2,0,0,0,0,2,1,0,0,0,0,0,0,0,1,0,0,9,0,0,0,9,0,0,0,10,10,10,10,10,1],  # 5
    [1,1,7,1,0,0,1,1,6,1,1,1,1,0,0,0,0,2,0,0,0,0,2,1,10,10,10,10,10,10,10,1,0,0,9,9,0,9,9,0,0,0,0,0,0,0,0,1],  # 6 - Armory
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,2,2,6,2,2,2,1,0,0,0,0,0,0,0,1,1,6,1,1,1,1,1,1,0,0,0,0,0,0,0,1],  # 7
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 8 - Rooftop
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,0,0,0,11,11,11,11,0,1],  # 9
    [1,0,0,0,0,0,8,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,6,1,1,1,1,1,0,0,0,0,0,0,0,0,0,0,11,0,0,11,0,1],  # 10 - East monster cave
    [1,1,5,5,5,5,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 11
    [1,5,0,0,0,5,1,0,0,0,0,0,0,0,0,4,4,4,4,4,4,4,4,1,0,0,0,0,0,0,0,1,0,0,0,0,8,0,0,0,0,0,11,0,0,11,0,1],  # 12
    [1,5,0,0,0,5,1,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,4,1,0,0,11,11,11,0,0,6,0,0,0,0,0,0,0,0,0,0,11,11,11,11,0,1],  # 13 - Sewer
    [1,5,0,0,0,5,1,0,0,0,0,0,0,0,0,6,0,0,0,0,0,0,4,1,0,0,11,0,11,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 14
    [1,5,0,0,0,5,1,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,4,1,0,0,0,0,0,0,0,1,1,1,1,6,1,1,1,1,1,1,1,1,1,1,1,1],  # 15
    [1,5,0,0,0,0,6,0,0,0,0,0,0,0,0,4,0,0,0,0,0,0,4,1,0,0,11,0,11,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 16 - Underground Labs
    [1,5,5,5,5,5,1,0,0,0,3,3,3,3,0,4,0,0,0,0,0,0,4,1,0,0,11,11,11,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 17
    [1,0,0,0,0,0,0,0,0,0,3,0,0,3,0,4,4,4,4,4,4,4,4,1,0,0,0,0,0,0,0,1,0,0,2,2,0,0,2,2,0,0,0,0,0,0,0,1],  # 18
    [1,0,0,0,0,0,0,0,0,0,3,0,0,3,0,0,0,0,0,0,0,0,0,1,1,1,1,6,1,1,1,1,0,0,2,0,0,0,0,2,0,0,0,0,0,0,0,1],  # 19
    [1,0,0,0,0,0,0,0,0,0,3,0,0,6,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,6,0,0,2,0,0,0,0,2,0,0,0,0,0,0,0,1],  # 20 - Labs East
    [1,0,0,0,7,0,0,0,0,0,3,0,0,3,0,0,0,0,8,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,2,0,0,0,0,2,0,0,0,0,0,0,0,1],  # 21
    [1,0,0,0,0,0,0,0,0,0,3,3,3,3,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,2,2,6,2,2,2,0,0,0,0,0,0,0,1],  # 22
    [1,1,1,1,1,6,1,1,1,1,1,1,1,1,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 23
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 24 - Market District
    [1,0,0,0,0,0,0,0,0,0,4,0,0,4,0,0,0,0,0,0,0,0,0,6,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 25
    [1,0,0,0,0,0,0,0,0,0,4,0,0,4,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,7,0,0,0,0,0,0,0,1],  # 26
    [1,0,0,5,5,0,0,0,0,0,4,0,0,4,0,0,5,5,5,5,0,0,0,1,0,0,0,0,0,0,0,1,1,1,1,1,1,1,6,1,1,1,1,1,1,1,1,1],  # 27
    [1,0,0,5,0,0,0,0,0,0,0,0,0,0,0,0,5,0,0,5,0,0,0,1,0,0,0,0,0,0,0,0,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,1],  # 28 - Deep Sewer / Military
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,5,0,0,5,0,0,0,1,0,0,11,11,0,11,11,0,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 29
    [1,0,0,5,0,0,0,0,0,0,4,0,0,4,0,0,5,5,5,5,0,0,0,1,0,0,11,0,0,0,11,0,12,0,0,0,12,12,12,12,12,12,0,0,0,0,0,1],  # 30
    [1,0,0,5,5,0,0,0,0,0,4,0,0,4,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,0,12,0,0,0,12,0,0,0,0,12,0,0,0,0,0,1],  # 31
    [1,0,0,0,0,0,0,0,0,0,4,4,6,4,0,0,0,0,0,0,0,0,0,1,0,0,11,0,0,0,11,0,12,0,0,0,12,0,0,0,0,12,0,0,0,0,0,1],  # 32
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,11,11,0,11,11,0,6,0,0,0,12,12,6,12,12,12,0,0,0,0,0,1],  # 33 - Monster Den / Military Gates
    [1,0,0,0,0,0,0,0,0,0,0,0,8,0,0,0,0,0,7,0,0,0,0,1,0,0,0,0,0,0,0,0,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 34
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 35 - Hell portal
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,0,0,0,0,0,0,0,1,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 36
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1,1,1,1,6,1,1,1,1,12,0,0,0,0,0,0,0,0,0,0,0,0,0,0,1],  # 37
    [1,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,12,12,12,12,12,12,12,12,12,12,12,12,12,12,12,1],  # 38
    [1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1,1],  # 39
]

MAP_H = len(MAP)
MAP_W = len(MAP[0])

# Door state tracking: key = (y, x), value = {'open': float 0-1, 'opening': bool, 'timer': float}
DOOR_POSITIONS = []
for y_d in range(MAP_H):
    for x_d in range(MAP_W):
        if MAP[y_d][x_d] == 6:
            DOOR_POSITIONS.append((y_d, x_d))


# ═══════════════════════════════════════════════════
#  A* PATHFINDING (grid-based, used by all NPC AI)
# ═══════════════════════════════════════════════════
def _astar(start_x, start_y, goal_x, goal_y, max_steps=60):
    """A* on the MAP grid. Returns list of (cx, cy) tile-centre waypoints, or []."""
    sx, sy = int(start_x), int(start_y)
    gx, gy = int(goal_x), int(goal_y)
    if sx == gx and sy == gy:
        return []
    if not (0 <= gx < MAP_W and 0 <= gy < MAP_H):
        return []
    dest_cell = MAP[gy][gx]
    if dest_cell != 0 and dest_cell != 6:
        return []   # goal is inside a wall
    # open_set: (f_cost, g_cost, x, y, path)
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
            if cell != 0 and cell != 6:   # solid wall — skip
                continue
            ng = g + 1
            h = abs(nx - gx) + abs(ny - gy)
            heapq.heappush(open_set, (ng + h, ng, nx, ny, path + [(cx, cy)]))
    return []   # no path found


# ═══════════════════════════════════════════════════
#  WEAPON DEFINITIONS (Doom-style)
# ═══════════════════════════════════════════════════
# Weapons: 0=Crowbar, 1=Pistol, 2=Shotgun, 3=AR2 Pulse, 4=RPG, 5=Combine Ball, 6=Presidential Strike

WEAPONS = {
    0: {
        'name': 'Crowbar',
        'damage': 25,
        'fire_rate': 0.4,
        'ammo_type': None,
        'ammo_use': 0,
        'range': 2.0,
        'spread': 0,
        'projectile': False,
        'hitscan': True,
        'color': (180, 100, 50),
    },
    1: {
        'name': 'M9 Pistol',
        'damage': 15,
        'fire_rate': 0.3,
        'ammo_type': 'bullets',
        'ammo_use': 1,
        'range': MAX_DEPTH,
        'spread': 0.02,
        'projectile': False,
        'hitscan': True,
        'color': (200, 200, 180),
    },
    2: {
        'name': 'Pump Shotgun',
        'damage': 12,
        'fire_rate': 0.8,
        'ammo_type': 'shells',
        'ammo_use': 1,
        'range': 12.0,
        'spread': 0.08,
        'projectile': False,
        'hitscan': True,
        'pellets': 7,
        'color': (160, 140, 100),
    },
    3: {
        'name': 'AR2 Pulse Rifle',
        'damage': 10,
        'fire_rate': 0.08,
        'ammo_type': 'cells',
        'ammo_use': 1,
        'range': MAX_DEPTH,
        'spread': 0.04,
        'projectile': False,
        'hitscan': True,
        'color': (100, 160, 255),
    },
    4: {
        'name': 'RPG-7',
        'damage': 80,
        'fire_rate': 1.5,
        'ammo_type': 'rockets',
        'ammo_use': 1,
        'range': MAX_DEPTH,
        'spread': 0,
        'projectile': True,
        'hitscan': False,
        'color': (200, 80, 30),
    },
    5: {
        'name': 'Combine Ball Launcher',
        'damage': 9999,
        'fire_rate': 1.0,
        'ammo_type': 'energy',
        'ammo_use': 1,
        'range': MAX_DEPTH,
        'spread': 0,
        'projectile': True,
        'hitscan': False,
        'color': (255, 200, 50),
    },
    6: {
        'name': 'Presidential Strike [BFG]',
        'damage': 200,
        'fire_rate': 3.0,
        'ammo_type': 'energy',
        'ammo_use': 40,
        'range': MAX_DEPTH,
        'spread': 0,
        'projectile': True,
        'hitscan': False,
        'color': (100, 255, 100),
    },
}


# ═══════════════════════════════════════════════════
#  PICKUP TYPES
# ═══════════════════════════════════════════════════
PICKUP_DEFS = {
    'health_small': {'heal': 10, 'label': 'Stimpack', 'color': (100, 255, 100)},
    'health_large': {'heal': 25, 'label': 'Medikit', 'color': (50, 200, 50)},
    'armor_small': {'armor': 5, 'label': 'Armor Shard', 'color': (100, 150, 255)},
    'armor_large': {'armor': 50, 'label': 'Kevlar Vest', 'color': (50, 100, 200)},
    'ammo_bullets': {'ammo': ('bullets', 20), 'label': 'Clip', 'color': (220, 200, 100)},
    'ammo_shells': {'ammo': ('shells', 8), 'label': 'Shell Box', 'color': (200, 120, 60)},
    'ammo_cells': {'ammo': ('cells', 30), 'label': 'Cell Pack', 'color': (100, 180, 255)},
    'ammo_rockets': {'ammo': ('rockets', 5), 'label': 'Rocket Crate', 'color': (200, 80, 30)},
    'ammo_energy': {'ammo': ('energy', 20), 'label': 'Energy Core', 'color': (255, 200, 50)},
    'berserk': {'berserk': True, 'label': 'BERSERK', 'color': (255, 0, 0)},
    'invuln': {'invuln': 30.0, 'label': 'INVULNERABILITY', 'color': (255, 255, 255)},
}


# ═══════════════════════════════════════════════════
#  TEXTURE GENERATION (PROCEDURAL)
# ═══════════════════════════════════════════════════
TEX_SIZE = 64

def gen_texture_concrete():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 80 + random.randint(-15, 15)
            if y % 16 < 2:
                base -= 20
            if x % 32 < 1:
                base -= 10
            base = max(0, min(255, base))
            surf.set_at((x, y), (base, base, base + 5))
    return surf

def gen_texture_ecpu():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 30 + random.randint(-8, 8)
            g = 10 + random.randint(-5, 5)
            b = 50 + random.randint(-10, 10)
            if y % 16 == 0 or y % 16 == 1:
                r, g, b = 120, 40, 200
            if x % 32 < 2:
                g += 15
                b += 30
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_mcpd():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 15 + random.randint(-5, 5)
            g = 25 + random.randint(-8, 8)
            b = 55 + random.randint(-10, 10)
            if y % 16 < 2:
                r += 5; g += 10; b += 30
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_rpg():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 80 + random.randint(-20, 20)
            g = 35 + random.randint(-10, 10)
            b = 15 + random.randint(-8, 8)
            if random.random() < 0.05:
                r = min(255, r + 40)
                g = max(0, g - 10)
            if y % 16 < 1:
                r -= 15; g -= 8; b -= 5
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_slums():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 60 + random.randint(-15, 15)
            g = 55 + random.randint(-12, 12)
            b = 30 + random.randint(-10, 10)
            if random.random() < 0.08:
                r = max(0, r - 20)
                g = max(0, g + 10)
            if y % 32 < 2:
                r -= 10; g -= 8; b -= 5
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_door():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 50 + random.randint(-5, 5)
            g = 55 + random.randint(-5, 5)
            b = 60 + random.randint(-5, 5)
            if 4 < x < 60 and 4 < y < 60:
                r += 10; g += 10; b += 12
            if 48 < x < 54 and 28 < y < 36:
                r, g, b = 180, 160, 80
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_checkerboard():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    sz = 8
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            cell = (x // sz + y // sz) % 2
            if cell == 0:
                surf.set_at((x, y), (255, 0, 255))
            else:
                surf.set_at((x, y), (0, 0, 0))
    return surf

def gen_texture_error():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    surf.fill((180, 0, 0))
    font_small = pygame.font.SysFont('Consolas', 12, bold=True)
    err_text = font_small.render("ERROR", True, (255, 255, 255))
    surf.blit(err_text, (TEX_SIZE // 2 - err_text.get_width() // 2, TEX_SIZE // 2 - err_text.get_height() // 2))
    return surf

def gen_texture_hq_interior():
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 20 + random.randint(-3, 3)
            g = 18 + random.randint(-3, 3)
            b = 35 + random.randint(-5, 5)
            if 10 < x < 54 and 8 < y < 30:
                r = 15; g = 60 + random.randint(-10, 10); b = 30 + random.randint(-5, 5)
            if y % 16 < 1:
                r += 8; g += 5; b += 12
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_metal():
    """Reinforced metal armory wall."""
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 55 + random.randint(-8, 8)
            r = base
            g = base + 5
            b = base + 10
            # Rivets
            if (x % 16 < 3 and y % 16 < 3):
                r = min(255, r + 40)
                g = min(255, g + 30)
                b = min(255, b + 20)
            # Horizontal panels
            if y % 32 < 2:
                r -= 15; g -= 12; b -= 10
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_sewer():
    """Green sewer/underground wall."""
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            r = 20 + random.randint(-8, 8)
            g = 45 + random.randint(-15, 15)
            b = 25 + random.randint(-8, 8)
            # Slime drips
            if random.random() < 0.03:
                g = min(255, g + 80)
            # Brick pattern
            row = y // 8
            if y % 8 < 1:
                r -= 10; g -= 10; b -= 5
            offset = 0 if row % 2 == 0 else 16
            if (x + offset) % 32 < 1:
                r -= 10; g -= 10; b -= 5
            surf.set_at((x, y), (max(0, min(255, r)), max(0, min(255, g)), max(0, min(255, b))))
    return surf

def gen_texture_floor():
    """Dark floor texture."""
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 30 + random.randint(-8, 8)
            # Tile pattern
            if x % 32 < 1 or y % 32 < 1:
                base -= 10
            surf.set_at((x, y), (base, base - 2, base + 3))
    return surf

def gen_texture_ceiling():
    """Dark ceiling texture."""
    surf = pygame.Surface((TEX_SIZE, TEX_SIZE))
    for y in range(TEX_SIZE):
        for x in range(TEX_SIZE):
            base = 15 + random.randint(-5, 5)
            if x % 16 == 0 or y % 16 == 0:
                base += 5
            surf.set_at((x, y), (base, base, base + 8))
    return surf


# ═══════════════════════════════════════════════════
#  SPRITE GENERATION (PROCEDURAL NPC SPRITES)
# ═══════════════════════════════════════════════════
SPRITE_SIZE = 64

def gen_sprite_civilian():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, (100, 130, 200), (20, 28, 24, 30))
    pygame.draw.circle(surf, (245, 200, 160), (32, 22), 10)
    pygame.draw.circle(surf, (30, 30, 30), (28, 20), 2)
    pygame.draw.circle(surf, (30, 30, 30), (36, 20), 2)
    pygame.draw.rect(surf, (60, 60, 90), (22, 56, 8, 8))
    pygame.draw.rect(surf, (60, 60, 90), (34, 56, 8, 8))
    return surf

def gen_sprite_mcpd_frames():
    """Returns 4 frames for MCPD animations: Idle, Alert, Fire, Walk."""
    frames = []
    base_color = (30, 50, 140)
    for i in range(4):
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        # Body
        pygame.draw.rect(surf, base_color, (18, 24, 28, 34))
        # Head (visor)
        pygame.draw.ellipse(surf, (20, 30, 100), (20, 8, 24, 16))
        pygame.draw.rect(surf, (80, 130, 255), (24, 16, 16, 5))
        # Badge
        pygame.draw.circle(surf, (200, 200, 60), (38, 32), 4)
        
        if i == 0:  # Idle - gun down
            pygame.draw.rect(surf, (20, 30, 80), (20, 56, 10, 8)) # Left leg
            pygame.draw.rect(surf, (20, 30, 80), (34, 56, 10, 8)) # Right leg
            pygame.draw.rect(surf, (40, 40, 40), (14, 30, 6, 16)) # Gun down
        elif i == 1:  # Alert - gun up
            pygame.draw.rect(surf, (20, 30, 80), (20, 56, 10, 8))
            pygame.draw.rect(surf, (20, 30, 80), (34, 56, 10, 8))
            pygame.draw.rect(surf, (40, 40, 40), (46, 26, 14, 6)) # Gun aimed
        elif i == 2:  # Fire - muzzle flash
            pygame.draw.rect(surf, (20, 30, 80), (20, 56, 10, 8))
            pygame.draw.rect(surf, (20, 30, 80), (34, 56, 10, 8))
            pygame.draw.rect(surf, (40, 40, 40), (46, 26, 14, 6)) # Gun aimed
            pygame.draw.circle(surf, (255, 200, 50), (62, 29), 6) # Muzzle flash
            pygame.draw.circle(surf, (255, 255, 200), (62, 29), 3)
        elif i == 3:  # Walk - step
            pygame.draw.rect(surf, (20, 30, 80), (24, 56, 10, 8)) # Leg 1
            pygame.draw.rect(surf, (20, 30, 80), (30, 52, 10, 8)) # Leg 2 raised
            pygame.draw.rect(surf, (40, 40, 40), (46, 30, 12, 6)) # Gun slightly lowered
            
        frames.append(surf)
    return frames

def gen_sprite_mcpd():
    return gen_sprite_mcpd_frames()[0]

def gen_sprite_military():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, (40, 60, 30), (16, 24, 32, 34)) # Camo body
    pygame.draw.circle(surf, (30, 50, 20), (32, 16), 10) # Helmet
    pygame.draw.rect(surf, (0, 0, 0), (24, 18, 16, 4)) # Goggles
    pygame.draw.rect(surf, (150, 40, 40), (38, 20, 4, 4)) # Laser eye
    pygame.draw.rect(surf, (60, 60, 60), (46, 30, 18, 6)) # Heavy gun
    pygame.draw.rect(surf, (20, 30, 15), (20, 58, 10, 6))
    pygame.draw.rect(surf, (20, 30, 15), (34, 58, 10, 6))
    return surf

def gen_sprite_ecpu():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, (50, 10, 90), (14, 20, 36, 38))
    pygame.draw.rect(surf, (70, 20, 120), (10, 20, 10, 10))
    pygame.draw.rect(surf, (70, 20, 120), (44, 20, 10, 10))
    pygame.draw.rect(surf, (40, 8, 70), (18, 4, 28, 20))
    pygame.draw.rect(surf, (180, 80, 255), (22, 12, 20, 6))
    pygame.draw.rect(surf, (35, 5, 60), (18, 56, 12, 8))
    pygame.draw.rect(surf, (35, 5, 60), (34, 56, 12, 8))
    return surf

def gen_sprite_rpg_ganger():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, (140, 50, 20), (20, 26, 24, 30))
    pygame.draw.circle(surf, (200, 160, 120), (32, 18), 10)
    pygame.draw.rect(surf, (255, 50, 0), (22, 10, 20, 6))
    pygame.draw.rect(surf, (80, 80, 80), (44, 28, 16, 6))
    pygame.draw.rect(surf, (60, 60, 60), (56, 24, 4, 14))
    pygame.draw.rect(surf, (80, 30, 10), (22, 54, 8, 10))
    pygame.draw.rect(surf, (80, 30, 10), (34, 54, 8, 10))
    return surf

def gen_sprite_imp():
    """Doom Imp-style enemy — a corrupted data entity."""
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    # Hunched body
    pygame.draw.ellipse(surf, (120, 60, 30), (16, 22, 32, 36))
    # Head/horns
    pygame.draw.circle(surf, (100, 50, 25), (32, 18), 12)
    pygame.draw.polygon(surf, (80, 30, 10), [(24, 10), (22, 0), (28, 8)])
    pygame.draw.polygon(surf, (80, 30, 10), [(40, 10), (42, 0), (36, 8)])
    # Eyes (glowing)
    pygame.draw.circle(surf, (255, 180, 0), (27, 16), 3)
    pygame.draw.circle(surf, (255, 180, 0), (37, 16), 3)
    pygame.draw.circle(surf, (255, 255, 100), (27, 16), 1)
    pygame.draw.circle(surf, (255, 255, 100), (37, 16), 1)
    # Claws
    pygame.draw.polygon(surf, (150, 70, 30), [(10, 30), (6, 38), (14, 34)])
    pygame.draw.polygon(surf, (150, 70, 30), [(54, 30), (58, 38), (50, 34)])
    # Legs
    pygame.draw.rect(surf, (90, 40, 20), (20, 56, 10, 8))
    pygame.draw.rect(surf, (90, 40, 20), (34, 56, 10, 8))
    return surf

def gen_sprite_demon():
    """Doom Pinky Demon-style enemy — a server corruption beast."""
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    # Large body
    pygame.draw.ellipse(surf, (200, 80, 120), (8, 18, 48, 40))
    # Head
    pygame.draw.ellipse(surf, (180, 60, 100), (14, 6, 36, 20))
    # Jaws
    pygame.draw.polygon(surf, (255, 100, 100), [(20, 20), (44, 20), (32, 30)])
    # Teeth
    for tx in range(22, 42, 4):
        pygame.draw.rect(surf, (255, 255, 255), (tx, 18, 2, 5))
    # Eyes
    pygame.draw.circle(surf, (255, 0, 0), (24, 12), 3)
    pygame.draw.circle(surf, (255, 0, 0), (40, 12), 3)
    # Legs
    pygame.draw.rect(surf, (160, 50, 80), (14, 54, 12, 10))
    pygame.draw.rect(surf, (160, 50, 80), (38, 54, 12, 10))
    return surf

def gen_sprite_charger():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, (255, 68, 204), (4, 20, 56, 28))
    pygame.draw.rect(surf, (230, 50, 180), (14, 14, 36, 12))
    pygame.draw.rect(surf, (100, 200, 255, 150), (16, 16, 14, 8))
    pygame.draw.rect(surf, (100, 200, 255, 150), (34, 16, 14, 8))
    pygame.draw.circle(surf, (30, 30, 30), (14, 48), 6)
    pygame.draw.circle(surf, (30, 30, 30), (50, 48), 6)
    pygame.draw.rect(surf, (255, 255, 200), (4, 24, 4, 6))
    pygame.draw.rect(surf, (255, 50, 50), (56, 24, 4, 6))
    return surf

def gen_sprite_pillow():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.rect(surf, (255, 180, 255), (12, 8, 40, 52), border_radius=6)
    pygame.draw.ellipse(surf, (255, 220, 240), (18, 14, 28, 24))
    pygame.draw.ellipse(surf, (60, 60, 200), (22, 20, 8, 10))
    pygame.draw.ellipse(surf, (60, 60, 200), (34, 20, 8, 10))
    pygame.draw.circle(surf, (255, 255, 255), (25, 22), 2)
    pygame.draw.circle(surf, (255, 255, 255), (37, 22), 2)
    return surf

def gen_sprite_combine_ball():
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 200, 0, 60), (16, 16), 14)
    pygame.draw.circle(surf, (255, 220, 50, 120), (16, 16), 10)
    pygame.draw.circle(surf, (255, 255, 200), (16, 16), 6)
    pygame.draw.circle(surf, (255, 255, 255), (16, 16), 3)
    return surf

def gen_sprite_explosion():
    surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
    pygame.draw.circle(surf, (255, 100, 0, 100), (32, 32), 28)
    pygame.draw.circle(surf, (255, 180, 0, 150), (32, 32), 20)
    pygame.draw.circle(surf, (255, 255, 100, 200), (32, 32), 12)
    pygame.draw.circle(surf, (255, 255, 255), (32, 32), 5)
    return surf

def gen_sprite_bfg_ball():
    """Big green energy ball for Presidential Strike."""
    surf = pygame.Surface((48, 48), pygame.SRCALPHA)
    pygame.draw.circle(surf, (0, 255, 0, 60), (24, 24), 22)
    pygame.draw.circle(surf, (50, 255, 50, 100), (24, 24), 16)
    pygame.draw.circle(surf, (100, 255, 100, 160), (24, 24), 10)
    pygame.draw.circle(surf, (200, 255, 200), (24, 24), 5)
    return surf

def gen_sprite_rocket():
    """RPG rocket projectile."""
    surf = pygame.Surface((16, 16), pygame.SRCALPHA)
    pygame.draw.rect(surf, (180, 80, 30), (4, 6, 10, 4))
    pygame.draw.polygon(surf, (200, 200, 200), [(14, 6), (16, 8), (14, 10)])
    pygame.draw.rect(surf, (255, 150, 0), (2, 7, 3, 2))
    return surf

def gen_sprite_pickup(color, label_char):
    """Generic pickup sprite."""
    surf = pygame.Surface((32, 32), pygame.SRCALPHA)
    pygame.draw.circle(surf, (*color, 80), (16, 16), 14)
    pygame.draw.circle(surf, (*color, 160), (16, 16), 10)
    pygame.draw.circle(surf, (255, 255, 255, 200), (16, 16), 6)
    return surf

def gen_sprite_corpse(base_color):
    """Dead entity sprite."""
    surf = pygame.Surface((SPRITE_SIZE, 24), pygame.SRCALPHA)
    pygame.draw.ellipse(surf, base_color, (8, 4, 48, 16))
    # Blood pool
    pygame.draw.ellipse(surf, (120, 0, 0, 150), (12, 8, 40, 12))
    return surf


# ═══════════════════════════════════════════════════
#  SOUND GENERATION (PROCEDURAL)
# ═══════════════════════════════════════════════════
SAMPLE_RATE = 22050

def gen_sound_buffer(func, duration=0.3, volume=0.3):
    n_samples = int(SAMPLE_RATE * duration)
    buf = array.array('h', [0] * n_samples)
    for i in range(n_samples):
        t = i / SAMPLE_RATE
        val = func(t, duration) * volume
        buf[i] = max(-32767, min(32767, int(val * 32767)))
    sound = pygame.mixer.Sound(buffer=buf)
    return sound

def metal_clang_func(t, dur):
    env = math.exp(-t * 15)
    return env * (math.sin(t * 1200) * 0.5 + math.sin(t * 3400) * 0.3 + random.uniform(-0.2, 0.2))

def pistol_fire_func(t, dur):
    env = math.exp(-t * 20)
    return env * (random.uniform(-1, 1) * 0.6 + math.sin(t * 1500) * 0.4)

def shotgun_fire_func(t, dur):
    env = math.exp(-t * 10)
    return env * (random.uniform(-1, 1) * 0.8 + math.sin(t * 400) * 0.2)

def ar2_fire_func(t, dur):
    env = math.exp(-t * 30)
    return env * (math.sin(t * 2000 + math.sin(t * 500) * 5) * 0.7)

def rpg_fire_func(t, dur):
    env = 1 - t / dur
    return env * (random.uniform(-1, 1) * 0.3 + math.sin(t * 80) * 0.7)

def combine_ball_fire_func(t, dur):
    env = math.exp(-t * 8)
    return env * (math.sin(t * 800 + math.sin(t * 200) * 3) * 0.7)

def combine_ball_hit_func(t, dur):
    env = math.exp(-t * 12)
    return env * (math.sin(t * 600) * 0.4 + math.sin(t * 1800) * 0.3)

def bfg_fire_func(t, dur):
    env = math.exp(-t * 3)
    return env * (math.sin(t * 300 + math.sin(t * 80) * 8) * 0.5 + math.sin(t * 60) * 0.3)

def explosion_func(t, dur):
    env = math.exp(-t * 4)
    return env * (random.uniform(-1, 1) * 0.6 + math.sin(t * 60) * 0.4)

def radio_click_func(t, dur):
    env = 1.0 if t < 0.02 else math.exp(-(t - 0.02) * 30)
    return env * random.uniform(-1, 1)

def footstep_func(t, dur):
    env = math.exp(-t * 25)
    return env * (random.uniform(-1, 1) * 0.5 + math.sin(t * 200) * 0.3)

def pickup_func(t, dur):
    env = math.exp(-t * 6)
    freq = 800 + t * 2000
    return env * math.sin(t * freq) * 0.5

def door_func(t, dur):
    env = 1 - t / dur
    return env * (math.sin(t * 200) * 0.3 + random.uniform(-0.1, 0.1))

def crowbar_func(t, dur):
    env = math.exp(-t * 18)
    return env * (math.sin(t * 3000) * 0.3 + random.uniform(-0.5, 0.5) * 0.5)

def pain_func(t, dur):
    env = math.exp(-t * 10)
    freq = 300 + random.uniform(-50, 50)
    return env * math.sin(t * freq) * 0.4

def death_func(t, dur):
    env = math.exp(-t * 4)
    return env * (math.sin(t * 150 - t * t * 50) * 0.5 + random.uniform(-0.2, 0.2))

def ambient_hum_func(t, dur):
    return (math.sin(t * 60) * 0.1 + math.sin(t * 120) * 0.05 + random.uniform(-0.03, 0.03))


# ═══════════════════════════════════════════════════
#  AI STATES (Doom-style)
# ═══════════════════════════════════════════════════
AI_IDLE = 0
AI_ALERT = 1
AI_CHASE = 2
AI_ATTACK = 3
AI_PAIN = 4
AI_DEAD = 5


# ═══════════════════════════════════════════════════
#  ENTITY / NPC CLASSES
# ═══════════════════════════════════════════════════
class Entity:
    _id_counter = 0

    def __init__(self, x, y, etype, sprite):
        Entity._id_counter += 1
        self.id = Entity._id_counter
        self.x = x
        self.y = y
        self.type = etype
        self.sprite = sprite
        self.alive = True
        self.health = 100
        self.max_health = 100
        self.speed = 1.0
        self.vx = 0
        self.vy = 0
        self.shoot_timer = 0
        self.shoot_interval = 2.0
        self.age = 0
        self.stuck = False
        self.stuck_timer = 0
        self.idle_anim = 0
        self.texture_failure = random.random() < 0.05
        self.model_missing = random.random() < 0.02
        # Doom AI
        self.ai_state = AI_IDLE
        self.pain_timer = 0
        self.alert_timer = 0
        self.attack_anim = 0
        self.last_known_px = 0
        self.last_known_py = 0
        self.pain_chance = 0.3  # chance to enter pain state when hit
        self.see_player = False
        self.damage_given = 0  # damage dealt per attack
        self.corpse_sprite = None
        # A* pathfinding state
        self.path = []          # list of (wx, wy) waypoints
        self.path_timer = 0.0   # countdown to next path refresh
        self.path_target_x = 0.0
        self.path_target_y = 0.0

    def can_see_point(self, tx, ty):
        """Simplified line-of-sight check."""
        dx = tx - self.x
        dy = ty - self.y
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 0.1:
            return True
        steps = int(dist * 4)
        if steps < 1:
            steps = 1
        sx = dx / steps
        sy = dy / steps
        cx, cy = self.x, self.y
        for _ in range(steps):
            cx += sx
            cy += sy
            mx, my = int(cx), int(cy)
            if 0 <= mx < MAP_W and 0 <= my < MAP_H:
                if MAP[my][mx] != 0 and MAP[my][mx] != 6:
                    return False
            else:
                return False
        return True

    def update(self, dt, game):
        self.age += dt
        self.shoot_timer += dt

        # Pain state
        if self.ai_state == AI_PAIN:
            self.pain_timer -= dt
            if self.pain_timer <= 0:
                self.ai_state = AI_CHASE
            self.vx *= 0.8
            self.vy *= 0.8
        elif self.ai_state == AI_DEAD:
            return

        # Check if can see player
        dist_to_player = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        self.see_player = dist_to_player < 20 and self.can_see_point(game.player_x, game.player_y)

        if self.see_player:
            self.last_known_px = game.player_x
            self.last_known_py = game.player_y
            if self.ai_state == AI_IDLE:
                self.ai_state = AI_ALERT
                self.alert_timer = 0.5

        # Friction
        self.vx *= 0.85
        self.vy *= 0.85

        # Move
        nx = self.x + self.vx * dt
        ny = self.y + self.vy * dt
        mx, my = int(nx), int(ny)
        if 0 <= mx < MAP_W and 0 <= my < MAP_H:
            if MAP[my][mx] == 6 and not game.is_door_open(my, mx):
                game.try_open_door(my, mx)

            if MAP[my][mx] == 0 or (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
                self.x = nx
                self.y = ny
            else:
                self.vx *= -0.5
                self.vy *= -0.5
        else:
            self.vx *= -0.5
            self.vy *= -0.5

    def take_damage(self, amt, game, source=None):
        if getattr(game, 'cheat_mode', False) and source == 'player':
            amt *= 2.0  # Enemies are weaker in cheat mode
        self.health -= amt
        
        # Trigger wanted level if player shoots cop
        if source == 'player' and self.type == 'mcpd' and self.health > 0:
            if game.wanted_level < 5:
                game.add_wanted(1)
                
        # Pain state
        if self.health > 0 and random.random() < self.pain_chance:
            self.ai_state = AI_PAIN
            self.pain_timer = 0.3
            game.play_pain(self.x, self.y)
        if self.health <= 0:
            self.die(game)

    def die(self, game):
        self.alive = False
        self.ai_state = AI_DEAD
        game.spawn_explosion(self.x, self.y)
        game.add_log('sys', f'Entity #{self.id} ({self.type}) eliminated')
        game.kills += 1
        game.play_death(self.x, self.y)
        # Leave corpse
        game.corpses.append({'x': self.x, 'y': self.y, 'type': self.type, 'age': 0})

    def dist_to(self, px, py):
        return math.sqrt((self.x - px) ** 2 + (self.y - py) ** 2)

    def _navigate_to(self, tx, ty, speed, dt):
        """Move toward (tx, ty) using A* pathfinding. Sets vx/vy."""
        self.path_timer -= dt
        # Refresh path when timer expires or target has moved significantly
        if (self.path_timer <= 0
                or abs(tx - self.path_target_x) > 1.5
                or abs(ty - self.path_target_y) > 1.5):
            self.path_timer = 1.2 + random.random() * 0.5
            self.path_target_x = tx
            self.path_target_y = ty
            self.path = _astar(self.x, self.y, tx, ty)

        if self.path:
            next_x, next_y = self.path[0]
            dx = next_x - self.x
            dy = next_y - self.y
            d = math.sqrt(dx * dx + dy * dy)
            if d < 0.6:               # reached this waypoint
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
            # A* failed (open area or too far) — fall back to direct movement
            dx = tx - self.x
            dy = ty - self.y
            d = math.sqrt(dx * dx + dy * dy) or 1
            self.vx = (dx / d) * speed
            self.vy = (dy / d) * speed


class Civilian(Entity):
    """Smarter civilian — flees from monsters AND gunfire, seeks MCPD protection."""
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'civilian', sprite)
        self.health = 60
        self.max_health = 60
        self.speed = 0.6
        self.wander_timer = 0
        self.pain_chance = 0.8
        self.panic_timer = 0
        self.scream_timer = 0
        self.flee_x = 0
        self.flee_y = 0

    def _find_nearest_danger(self, game):
        """Find the closest monster or explosion."""
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
        """Find closest MCPD officer for protection."""
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

    def update(self, dt, game):
        super().update(dt, game)
        self.wander_timer += dt
        if self.panic_timer > 0:
            self.panic_timer -= dt
        if self.scream_timer > 0:
            self.scream_timer -= dt

        # Check for nearby dangers (monsters)
        danger, danger_dist = self._find_nearest_danger(game)

        # Flee from nearby gunfire
        gunfire_panic = self.see_player and game.weapon_fired > 0

        if danger and danger_dist < 10:
            # PANIC! Monster nearby!
            self.panic_timer = 3.0
            self.ai_state = AI_ALERT

            # Scream to alert MCPD
            if self.scream_timer <= 0:
                self.scream_timer = 5.0
                game.add_log('warn', f'Civilian #{self.id}: "HELP! MONSTER!"')
                # Alert all nearby MCPD
                for e in game.entities:
                    if e.alive and e.type == 'mcpd' and self.dist_to(e.x, e.y) < 20:
                        e.ai_state = AI_CHASE
                        e.last_known_px = danger.x
                        e.last_known_py = danger.y

            # Try to run toward nearest MCPD officer for protection
            cop, cop_dist = self._find_nearest_mcpd(game)
            if cop and cop_dist < 15 and cop_dist > 2:
                # Run toward the cop
                dx = cop.x - self.x
                dy = cop.y - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx = (dx / d) * self.speed * 4
                self.vy = (dy / d) * self.speed * 4
            else:
                # No cop nearby — flee AWAY from the monster
                dx = self.x - danger.x
                dy = self.y - danger.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx = (dx / d) * self.speed * 4
                self.vy = (dy / d) * self.speed * 4

        elif gunfire_panic:
            # Flee from player shooting
            dx = self.x - game.player_x
            dy = self.y - game.player_y
            d = math.sqrt(dx * dx + dy * dy) or 1
            self.vx = (dx / d) * self.speed * 3
            self.vy = (dy / d) * self.speed * 3
            self.panic_timer = 2.0

        elif self.panic_timer > 0:
            # Still panicked — keep running in current direction
            pass

        elif self.ai_state in (AI_IDLE, AI_ALERT):
            # Peaceful wandering
            if self.wander_timer > 3 + random.random() * 3:
                self.wander_timer = 0
                self.vx = random.uniform(-1, 1) * self.speed
                self.vy = random.uniform(-1, 1) * self.speed
                # Occasionally stop and idle
                if random.random() < 0.3:
                    self.vx = 0
                    self.vy = 0


class MCPDUnit(Entity):
    """Smarter MCPD — tactical flanking, civilian protection, coordinated attacks, reinforcement calls."""
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'mcpd', sprite)
        self.health = 180
        self.max_health = 180
        self.speed = 2.2
        self.shoot_interval = 1.5  # Faster shooting
        self.patrol_dir = random.choice([-1, 1])
        self.damage_given = 15
        self.pain_chance = 0.3
        self.patrol_waypoint = 0
        self.reinforce_cooldown = 0
        self.strafe_timer = 0
        self.strafe_dir = random.choice([-1, 1])
        self.call_timer = 0  # Cooldown between radio calls
        # Patrol routes: MCPD patrols across the whole city
        self.patrol_points = [
            (11.5, 19.5), (8.5, 15.5), (5.5, 9.5), (8.5, 4.5),
            (14.5, 8.5), (18.5, 10.5), (14.5, 14.5), (8.5, 18.5),
        ]
        random.shuffle(self.patrol_points)

    def _find_endangered_civilian(self, game):
        """Find a civilian being threatened by a monster."""
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
        """Count other MCPD within radius for coordination."""
        count = 0
        for e in game.entities:
            if e.alive and e.type == 'mcpd' and e.id != self.id:
                if self.dist_to(e.x, e.y) < radius:
                    count += 1
        return count

    def update(self, dt, game):
        super().update(dt, game)

        if self.ai_state == AI_PAIN:
            return

        if self.reinforce_cooldown > 0:
            self.reinforce_cooldown -= dt
        if self.call_timer > 0:
            self.call_timer -= dt
        self.strafe_timer += dt

        frames = game.sprite_mcpd_frames
        
        # --- Priority 1: Protect endangered civilians ---
        civ_in_danger, threat = self._find_endangered_civilian(game)

        # --- Priority 2: Scan for any hostile monster ---
        target = game.find_nearest_hostile(self.x, self.y, ['rpg', 'imp', 'demon'])

        # Use the civilian's attacker as priority target
        if threat and threat.alive:
            target = threat

        if target and self.dist_to(target.x, target.y) < 18:
            # ENGAGE!
            target_dist = self.dist_to(target.x, target.y)

            if self.ai_state == AI_IDLE:
                self.ai_state = AI_CHASE
                game.add_log('sys', f'MCPD #{self.id} engaging {target.type} #{target.id}!')

            # Call for reinforcements if outnumbered or fighting demon
            allies_nearby = self._count_nearby_mcpd(game)
            if allies_nearby < 2 and self.call_timer <= 0 and target.type in ('demon', 'imp'):
                self.call_timer = 15.0
                self.reinforce_cooldown = 0
                game.add_log('sys', f'MCPD #{self.id}: "10-78 requesting backup!"')
                game.play_radio_click(self.x, self.y)
                # Alert other MCPD across the map
                for e in game.entities:
                    if e.alive and e.type == 'mcpd' and e.id != self.id:
                        e.ai_state = AI_CHASE
                        e.last_known_px = target.x
                        e.last_known_py = target.y

            # Tactical movement using A* pathfinding
            dx = target.x - self.x
            dy = target.y - self.y
            d = math.sqrt(dx * dx + dy * dy) or 1

            if target_dist > 6:
                # Use A* to navigate around walls toward target
                self._navigate_to(target.x, target.y, self.speed * 1.2, dt)
            elif target_dist > 3:
                # Combat range — strafe while shooting
                if self.strafe_timer > 1.5:
                    self.strafe_timer = 0
                    self.strafe_dir *= -1
                perp_x = -dy / d
                perp_y = dx / d
                self.vx = (dx / d) * self.speed * 0.3 + perp_x * self.speed * self.strafe_dir
                self.vy = (dy / d) * self.speed * 0.3 + perp_y * self.speed * self.strafe_dir
            else:
                # Too close to melee enemy (demon) — back up!
                self.vx = -(dx / d) * self.speed * 1.5
                self.vy = -(dy / d) * self.speed * 1.5

            # Shoot at target — faster when coordinating with allies
            fire_rate = self.shoot_interval * (0.6 if allies_nearby > 0 else 1.0)
            if self.shoot_timer > fire_rate and target_dist < 12:
                self.shoot_timer = 0
                self.sprite = frames[2] # Fire
                # Lead the target slightly for moving enemies
                lead = 0.3
                tx = target.x + target.vx * lead
                ty = target.y + target.vy * lead
                game.fire_combine_ball(self.x, self.y, tx, ty, 'mcpd')
            else:
                # Combat movement
                self.sprite = frames[3] if int(self.age * 6) % 2 == 0 else frames[1]

        elif self.ai_state == AI_IDLE:
            # No threats — patrol along waypoints using A*
            if self.patrol_waypoint < len(self.patrol_points):
                wp_x, wp_y = self.patrol_points[self.patrol_waypoint]
                d = math.sqrt((wp_x - self.x)**2 + (wp_y - self.y)**2)
                if d < 1.5:
                    # Reached waypoint, go to next
                    self.patrol_waypoint = (self.patrol_waypoint + 1) % len(self.patrol_points)
                    self.path = []   # reset path for new waypoint
                else:
                    self._navigate_to(wp_x, wp_y, self.speed * 0.6, dt)
            else:
                self.patrol_waypoint = 0
            # Idle walk animation
            self.sprite = frames[3] if int(self.age * 4) % 2 == 0 else frames[0]

        elif self.ai_state in (AI_ALERT, AI_CHASE):
            # Investigate last known position using A* (Search Mode)
            d = math.sqrt((self.last_known_px - self.x)**2 + (self.last_known_py - self.y)**2)
            if d > 1.5:
                # Slow walk in search mode
                self._navigate_to(self.last_known_px, self.last_known_py, self.speed * 0.5, dt)
                # Search mode walk animation
                self.sprite = frames[3] if int(self.age * 3) % 2 == 0 else frames[1]
            else:
                # Arrived at last known pos — back to patrol
                self.path = []
                self.ai_state = AI_IDLE
                self.sprite = frames[0]

        # Random stuck on door (Source Engine bug — rare now)
        if random.random() < 0.0003:
            self.stuck = True
            self.stuck_timer = 2
            self.vx = 0
            self.vy = 0
            game.add_log('warn', f'MCPD #{self.id} stuck on prop door')

        if self.stuck:
            self.stuck_timer -= dt
            if self.stuck_timer <= 0:
                self.stuck = False

    def die(self, game):
        """MCPD officers respawn after a delay."""
        super().die(game)
        game.mcpd_respawn_queue.append({'timer': 30.0, 'sprite': self.sprite})
        game.add_log('sys', f'[MCPD DISPATCH] Officer #{self.id} KIA — reinforcement en route in 30s')


class ECPUUnit(Entity):
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'ecpu', sprite)
        self.health = 500
        self.max_health = 500
        self.speed = 2.0
        self.shoot_interval = 1.8
        self.patrol_angle = random.uniform(0, math.pi * 2)
        self.radio_timer = 0
        self.radio_interval = 1.5 + random.random()
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
            # Orbit patrol
            self.patrol_angle += dt * 0.4
            r = 2.5
            tx = self.home_x + math.cos(self.patrol_angle) * r
            ty = self.home_y + math.sin(self.patrol_angle) * r
            dx = tx - self.x
            dy = ty - self.y
            d = math.sqrt(dx * dx + dy * dy)
            if d > 0.1:
                self.vx = (dx / d) * self.speed * 0.5
                self.vy = (dy / d) * self.speed * 0.5
        elif self.ai_state in (AI_ALERT, AI_CHASE, AI_ATTACK):
            # Hunt hostiles
            target = game.find_nearest_hostile(self.x, self.y, ['rpg', 'imp', 'demon'])
            if target and self.dist_to(target.x, target.y) < 12:
                dx = target.x - self.x
                dy = target.y - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx = (dx / d) * self.speed
                self.vy = (dy / d) * self.speed

                if self.shoot_timer > self.shoot_interval:
                    self.shoot_timer = 0
                    game.fire_combine_ball(self.x, self.y, target.x, target.y, 'ecpu')

        # Radio clicks (spatial — only audible near player)
        if self.radio_timer > self.radio_interval:
            self.radio_timer = 0
            self.radio_interval = 0.8 + random.random() * 2
            game.play_radio_click(self.x, self.y)


class MilitaryUnit(Entity):
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'military', sprite)
        self.health = 250
        self.max_health = 250
        self.speed = 1.8
        self.shoot_interval = 1.0
        self.damage_given = 20
        self.pain_chance = 0.1
        self.patrol_waypoint = 0

    def update(self, dt, game):
        super().update(dt, game)
        
        if self.ai_state == AI_PAIN:
            return

        if self.ai_state == AI_IDLE:
            # Stand guard
            self.vx = 0
            self.vy = 0
            # Become hostile if player is wanted level 4+ OR player enters military zone (y >= 28, x >= 32)
            if self.see_player and (game.wanted_level >= 4 or (game.player_y >= 28 and game.player_x >= 32)):
                self.ai_state = AI_CHASE
                game.add_log('admin', f'[MILITARY] Target acquired by Unit #{self.id}')
                if game.wanted_level < 4:
                    game.add_wanted(4)
        elif self.ai_state in (AI_ALERT, AI_CHASE):
            target_dist = self.dist_to(game.player_x, game.player_y)
            if target_dist > 8 and self.see_player:
                self._navigate_to(game.player_x, game.player_y, self.speed, dt)
            else:
                self.vx = 0
                self.vy = 0
            
            if self.see_player and self.shoot_timer > self.shoot_interval:
                self.shoot_timer = 0
                game.player_take_damage(self.damage_given)
                game.add_log('warn', f'[MILITARY] You were shot by Heavy Unit #{self.id}')
                game._play_spatial(game.snd_ar2, self.x, self.y)

class RPGGanger(Entity):
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'rpg', sprite)
        self.health = 80
        self.max_health = 80
        self.speed = 2.5
        self.shoot_interval = 1.5 + random.random()
        self.move_timer = 0
        self.damage_given = 40
        self.pain_chance = 0.5

    def update(self, dt, game):
        super().update(dt, game)
        self.move_timer += dt

        if self.ai_state == AI_PAIN:
            return

        # Wander chaotically
        if self.move_timer > 0.8:
            self.move_timer = 0
            if self.see_player and self.ai_state >= AI_ALERT:
                # Chase player
                dx = game.player_x - self.x
                dy = game.player_y - self.y
                d = math.sqrt(dx * dx + dy * dy) or 1
                self.vx = (dx / d) * self.speed * 1.5 + random.uniform(-1, 1)
                self.vy = (dy / d) * self.speed * 1.5 + random.uniform(-1, 1)
            else:
                self.vx = random.uniform(-1, 1) * self.speed * 2
                self.vy = random.uniform(-1, 1) * self.speed * 2

        # Fire at player or nearest entity
        if self.shoot_timer > self.shoot_interval:
            self.shoot_timer = 0
            if self.see_player and self.dist_to(game.player_x, game.player_y) < 15:
                game.fire_rpg_rocket(self.x, self.y, game.player_x, game.player_y, self)
                self.ai_state = AI_ATTACK
            else:
                target = game.find_nearest_hostile(self.x, self.y, ['civilian', 'mcpd', 'ecpu'])
                if target:
                    d = self.dist_to(target.x, target.y)
                    game.fire_rpg_rocket(self.x, self.y, target.x, target.y, self)
                    if d < 3:
                        self.take_damage(25, game)
                        game.add_log('warn', f'RPG #{self.id} self-damage! (range {d:.1f}u)')


class ImpEntity(Entity):
    """Doom Imp equivalent — corrupted data entities that hurl fireballs."""
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'imp', sprite)
        self.health = 60
        self.max_health = 60
        self.speed = 2.2
        self.shoot_interval = 2.0 + random.random()
        self.damage_given = 15
        self.pain_chance = 0.6
        self.melee_range = 1.5
        self.melee_damage = 20

    def update(self, dt, game):
        super().update(dt, game)

        if self.ai_state == AI_PAIN:
            return

        if self.ai_state == AI_IDLE:
            # Wander slowly
            if random.random() < 0.01:
                angle = random.uniform(0, math.pi * 2)
                self.vx = math.cos(angle) * self.speed * 0.3
                self.vy = math.sin(angle) * self.speed * 0.3
        elif self.ai_state in (AI_ALERT, AI_CHASE, AI_ATTACK):
            # Find nearest target: player OR any nearby law enforcement / civilian
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

            if dist < self.melee_range:
                if self.shoot_timer > 0.5:
                    self.shoot_timer = 0
                    if best_entity:
                        best_entity.take_damage(self.melee_damage, game)
                        game.add_log('warn', f'Imp #{self.id} clawed {best_entity.type}!')
                    else:
                        game.player_take_damage(self.melee_damage)
                        game.add_log('warn', f'Imp #{self.id} clawed you!')
            elif dist < 18 and can_see:
                if dist > 4:
                    self._navigate_to(best_tx, best_ty, self.speed, dt)
                else:
                    dx = best_tx - self.x
                    dy = best_ty - self.y
                    d = math.sqrt(dx * dx + dy * dy) or 1
                    self.vx = (dx / d) * self.speed * 0.3 + random.uniform(-2, 2)
                    self.vy = (dy / d) * self.speed * 0.3 + random.uniform(-2, 2)
                if self.shoot_timer > self.shoot_interval:
                    self.shoot_timer = 0
                    game.fire_imp_fireball(self.x, self.y, best_tx, best_ty)
            elif self.last_known_px != 0:
                # Navigate to last known position when target not visible
                self._navigate_to(self.last_known_px, self.last_known_py, self.speed * 0.6, dt)


class DemonEntity(Entity):
    """Doom Pinky Demon — charges and bites."""
    def __init__(self, x, y, sprite):
        super().__init__(x, y, 'demon', sprite)
        self.health = 150
        self.max_health = 150
        self.speed = 3.5
        self.melee_damage = 30
        self.pain_chance = 0.15
        self.charge_speed = 6.0
        self.charging = False

    def update(self, dt, game):
        super().update(dt, game)

        if self.ai_state == AI_PAIN:
            self.charging = False
            return

        if self.ai_state == AI_IDLE:
            if random.random() < 0.005:
                angle = random.uniform(0, math.pi * 2)
                self.vx = math.cos(angle) * self.speed * 0.3
                self.vy = math.sin(angle) * self.speed * 0.3
        elif self.ai_state in (AI_ALERT, AI_CHASE, AI_ATTACK):
            # Find nearest target: player OR any nearby law enforcement / civilian
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
            if dist < 1.5:
                if self.shoot_timer > 0.8:
                    self.shoot_timer = 0
                    if best_entity:
                        best_entity.take_damage(self.melee_damage, game)
                        game.add_log('warn', f'Demon #{self.id} bit {best_entity.type}!')
                    else:
                        game.player_take_damage(self.melee_damage)
                        game.add_log('warn', f'Demon #{self.id} bit you!')
                        game._play_spatial(game.snd_metal, self.x, self.y)
            elif self.can_see_point(best_tx, best_ty):
                # Charge using A* pathfinding
                spd = self.charge_speed if dist < 8 else self.speed
                self._navigate_to(best_tx, best_ty, spd, dt)
            elif self.last_known_px != 0:
                # Navigate to last known position when target not visible
                self._navigate_to(self.last_known_px, self.last_known_py, self.speed * 0.7, dt)


class PropEntity(Entity):
    def __init__(self, x, y, prop_type, sprite):
        super().__init__(x, y, prop_type, sprite)
        self.prop_type = prop_type
        self.health = 200
        self.max_health = 200
        self.speed = 0
        self.vx = random.uniform(-5, 5)
        self.vy = random.uniform(-5, 5)


# ═══════════════════════════════════════════════════
#  PROJECTILE CLASSES
# ═══════════════════════════════════════════════════
class CombineBall:
    def __init__(self, x, y, tx, ty, owner):
        self.x = x
        self.y = y
        self.owner = owner
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 10
        self.vx = ((tx - x) / d) * self.speed
        self.vy = ((ty - y) / d) * self.speed
        self.alive = True
        self.age = 0
        self.bounces = 0
        self.max_bounces = 3
        self.proj_type = 'combine'

    def update(self, dt, game):
        self.age += dt
        self.x += self.vx * dt
        self.y += self.vy * dt

        mx, my = int(self.x), int(self.y)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
            self._explode(game)
            return
        if MAP[my][mx] != 0 and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            # EXPLODE on wall impact instead of bouncing
            self._explode(game)
            return

        if self.age > 6:
            self._explode(game)
            return

        for e in game.entities:
            if not e.alive:
                continue
            if e.type == self.owner:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 0.8:
                e.take_damage(9999, game)
                game.add_log('sys', f'[AMMO SHIFT] combine_ball vaporized #{e.id} ({e.type})')
                self._explode(game)
                return

        if self.owner != 'player':
            pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
            if pd < 0.5:
                game.player_take_damage(30)
                self._explode(game)

    def _explode(self, game):
        """Explode on impact with energy blast and splash damage."""
        if not self.alive:
            return
        self.alive = False
        game.spawn_explosion(self.x, self.y)
        game.play_combine_hit(self.x, self.y)
        # Splash damage to all nearby entities
        for e in game.entities:
            if not e.alive or e.type == self.owner:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 2.5:
                e.take_damage(int(50 * (1 - d / 2.5)), game)
                e.vx += ((e.x - self.x) / (d or 0.1)) * 4
                e.vy += ((e.y - self.y) / (d or 0.1)) * 4
        # Player splash
        pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        if pd < 2.5 and self.owner != 'player':
            game.player_take_damage(int(20 * (1 - pd / 2.5)))
        game.screen_shake = max(game.screen_shake, 0.2)


class RPGRocket:
    def __init__(self, x, y, tx, ty, owner):
        self.x = x
        self.y = y
        self.owner = owner
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 6
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
        if MAP[my][mx] != 0 and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self.detonate(game)
            return

        if self.age > 4:
            self.detonate(game)
            return

        for e in game.entities:
            if not e.alive or e is self.owner:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 0.6:
                self.detonate(game)
                return

        pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        if pd < 0.6:
            game.player_take_damage(40)
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
            if d < 3:
                e.take_damage(int(40 * (1 - d / 3)), game)
                e.vx += ((e.x - self.x) / (d or 1)) * 5
                e.vy += ((e.y - self.y) / (d or 1)) * 5
        # Player splash
        pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        if pd < 3:
            game.player_take_damage(int(30 * (1 - pd / 3)))
        game.add_log('warn', f'[RPG] Detonation at ({self.x:.1f}, {self.y:.1f})')


class ImpFireball:
    """Imp fireball projectile."""
    def __init__(self, x, y, tx, ty):
        self.x = x
        self.y = y
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 7
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
        if MAP[my][mx] != 0 and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self.alive = False
            return

        if self.age > 5:
            self.alive = False
            return

        # Hit player
        pd = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        if pd < 0.5:
            game.player_take_damage(15)
            self.alive = False


class BFGBall:
    """Presidential Strike (BFG equivalent) projectile."""
    def __init__(self, x, y, tx, ty):
        self.x = x
        self.y = y
        d = math.sqrt((tx - x) ** 2 + (ty - y) ** 2) or 1
        self.speed = 5
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
        if MAP[my][mx] != 0 and not (MAP[my][mx] == 6 and game.is_door_open(my, mx)):
            self.detonate(game)
            return

        if self.age > 6:
            self.detonate(game)
            return

        # Zap nearby enemies as it travels (BFG behavior)
        if self.trail_timer > 0.2:
            self.trail_timer = 0
            for e in game.entities:
                if not e.alive:
                    continue
                d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
                if d < 4:
                    e.take_damage(30, game)

        # Hit wall/entity
        for e in game.entities:
            if not e.alive:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 0.8:
                self.detonate(game)
                return

    def detonate(self, game):
        if not self.alive:
            return
        self.alive = False
        game.spawn_explosion(self.x, self.y)
        game.play_explosion(self.x, self.y)
        # Massive AoE
        for e in game.entities:
            if not e.alive:
                continue
            d = math.sqrt((self.x - e.x) ** 2 + (self.y - e.y) ** 2)
            if d < 8:
                e.take_damage(int(200 * (1 - d / 8)), game)
                e.vx += ((e.x - self.x) / (d or 1)) * 10
                e.vy += ((e.y - self.y) / (d or 1)) * 10
        game.screen_shake = 1.0
        game.add_log('admin', f'[PRESIDENTIAL STRIKE] Impact at ({self.x:.1f}, {self.y:.1f})')


class Explosion:
    def __init__(self, x, y, sprite):
        self.x = x
        self.y = y
        self.sprite = sprite
        self.life = 1.0
        self.alive = True

    def update(self, dt):
        self.life -= dt * 3
        if self.life <= 0:
            self.alive = False


# ═══════════════════════════════════════════════════
#  PICKUP CLASS
# ═══════════════════════════════════════════════════
class Pickup:
    def __init__(self, x, y, pickup_type, sprite):
        self.x = x
        self.y = y
        self.type = pickup_type
        self.sprite = sprite
        self.alive = True
        self.bob_timer = random.uniform(0, math.pi * 2)

    def update(self, dt, game):
        self.bob_timer += dt * 3

        # Check player proximity
        d = math.sqrt((self.x - game.player_x) ** 2 + (self.y - game.player_y) ** 2)
        if d < 1.0:
            self.try_pickup(game)

    def try_pickup(self, game):
        defn = PICKUP_DEFS.get(self.type)
        if not defn:
            return

        picked = False

        if 'heal' in defn:
            if game.player_health < 100:
                game.player_health = min(100, game.player_health + defn['heal'])
                picked = True
        if 'armor' in defn:
            if game.player_armor < 200:
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
#  MAIN GAME CLASS
# ═══════════════════════════════════════════════════
class Game:
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=1024)
        pygame.mixer.set_num_channels(10)  # Cap concurrent channels to prevent overload
        self.screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.render_surf = pygame.Surface((INTERNAL_W, INTERNAL_H))
        self.z_buffer = [0.0] * INTERNAL_W
        self.running = True

        # Game states
        self.STATE_TITLE = 0
        self.STATE_PLAYING = 1
        self.STATE_INTERMISSION = 2
        self.game_state = self.STATE_TITLE
        self.title_timer = 0
        self.title_selection = 0

        # Fonts
        self.font_hud = pygame.font.SysFont('Consolas', 14, bold=True)
        self.font_hud_sm = pygame.font.SysFont('Consolas', 11)
        self.font_title = pygame.font.SysFont('Consolas', 28, bold=True)
        self.font_console = pygame.font.SysFont('Consolas', 10)
        self.font_large = pygame.font.SysFont('Consolas', 22, bold=True)
        self.font_admin = pygame.font.SysFont('Consolas', 12, bold=True)
        self.font_doom = pygame.font.SysFont('Consolas', 40, bold=True)
        self.font_doom_sm = pygame.font.SysFont('Consolas', 16, bold=True)

        # Generate textures
        print("Generating textures...")
        self.textures = {
            1: gen_texture_concrete(),
            2: gen_texture_ecpu(),
            3: gen_texture_mcpd(),
            4: gen_texture_rpg(),
            5: gen_texture_slums(),
            6: gen_texture_door(),
            7: gen_texture_checkerboard(),
            8: gen_texture_error(),
            9: gen_texture_hq_interior(),
            10: gen_texture_metal(),
            11: gen_texture_sewer(),
        }
        self.textures_dark = {}
        for k, v in self.textures.items():
            dark = v.copy()
            dark.fill((40, 40, 40), special_flags=pygame.BLEND_RGB_SUB)
            self.textures_dark[k] = dark

        self.tex_floor = gen_texture_floor()
        self.tex_ceiling = gen_texture_ceiling()

        # Generate sprites
        print("Generating sprites...")
        self.sprite_civilian = gen_sprite_civilian()
        self.sprite_mcpd_frames = gen_sprite_mcpd_frames()
        self.sprite_mcpd = self.sprite_mcpd_frames[0]
        self.sprite_ecpu = gen_sprite_ecpu()
        self.sprite_military = gen_sprite_military()
        self.sprite_rpg = gen_sprite_rpg_ganger()
        self.sprite_imp = gen_sprite_imp()
        self.sprite_demon = gen_sprite_demon()
        self.sprite_charger = gen_sprite_charger()
        self.sprite_pillow = gen_sprite_pillow()
        self.sprite_combine_ball = gen_sprite_combine_ball()
        self.sprite_explosion = gen_sprite_explosion()
        self.sprite_bfg = gen_sprite_bfg_ball()
        self.sprite_rocket = gen_sprite_rocket()
        self.sprite_error = self._gen_error_sprite()
        self.sprite_checker = self._gen_checker_sprite()

        # Pickup sprites
        self.pickup_sprites = {}
        for ptype, pdef in PICKUP_DEFS.items():
            self.pickup_sprites[ptype] = gen_sprite_pickup(pdef['color'], ptype[0].upper())

        # Corpse sprites
        self.corpse_sprites = {
            'civilian': gen_sprite_corpse((100, 130, 200)),
            'mcpd': gen_sprite_corpse((30, 50, 140)),
            'ecpu': gen_sprite_corpse((50, 10, 90)),
            'rpg': gen_sprite_corpse((140, 50, 20)),
            'imp': gen_sprite_corpse((120, 60, 30)),
            'demon': gen_sprite_corpse((200, 80, 120)),
        }

        # Generate sounds
        print("Generating audio...")
        self.snd_metal = gen_sound_buffer(metal_clang_func, 0.3, 0.3)
        self.snd_pistol = gen_sound_buffer(pistol_fire_func, 0.15, 0.5)
        self.snd_shotgun = gen_sound_buffer(shotgun_fire_func, 0.3, 0.6)
        self.snd_ar2 = gen_sound_buffer(ar2_fire_func, 0.08, 0.4)
        self.snd_rpg = gen_sound_buffer(rpg_fire_func, 0.5, 0.5)
        self.snd_combine_fire = gen_sound_buffer(combine_ball_fire_func, 0.25, 0.4)
        self.snd_combine_hit = gen_sound_buffer(combine_ball_hit_func, 0.2, 0.4)
        self.snd_bfg = gen_sound_buffer(bfg_fire_func, 0.8, 0.6)
        self.snd_explosion = gen_sound_buffer(explosion_func, 0.6, 0.5)
        self.snd_radio = gen_sound_buffer(radio_click_func, 0.05, 0.5)
        self.snd_footstep = gen_sound_buffer(footstep_func, 0.1, 0.15)
        self.snd_pickup = gen_sound_buffer(pickup_func, 0.3, 0.4)
        self.snd_door = gen_sound_buffer(door_func, 0.5, 0.3)
        self.snd_crowbar = gen_sound_buffer(crowbar_func, 0.15, 0.4)
        self.snd_pain = gen_sound_buffer(pain_func, 0.2, 0.3)
        self.snd_death = gen_sound_buffer(death_func, 0.5, 0.4)
        self.snd_ambient = gen_sound_buffer(ambient_hum_func, 2.0, 0.1)

        # Initialize game state
        self.cheat_mode = False
        self.init_game()

        print("Boot complete.")

    def init_game(self):
        """Reset all game state for new game."""
        # Player state
        self.player_x = 4.5
        self.player_y = 4.5
        self.player_angle = 0.0
        self.player_health = 100
        self.player_armor = 100 if self.cheat_mode else 0
        self.player_money = 250000
        self.noclip = False
        self.sprint = False

        # Weapons
        self.current_weapon = 1  # Start with pistol
        self.weapons_owned = {0: True, 1: True}  # Crowbar + pistol
        self.ammo = {
            'bullets': 50,
            'shells': 0,
            'cells': 0,
            'rockets': 0,
            'energy': 0,
        }
        self.ammo_max = {
            'bullets': 200,
            'shells': 50,
            'cells': 300,
            'rockets': 50,
            'energy': 100,
        }
        self.weapon_cooldown = 0
        self.weapon_switch_timer = 0

        # Powerups
        self.berserk_timer = 0
        self.invuln_timer = 0

        # Game state
        self.sim_time = 0.0
        self.entities = []
        self.projectiles = []
        self.explosions_list = []
        self.pickups = []
        self.corpses = []
        self.mcpd_respawn_queue = []  # list of {'timer': float, 'sprite': Surface}
        self.console_log = []
        self.pink_charger_count = 0
        self.anime_pillow_count = 0
        self.is_loading = True
        self.loading_progress = 0
        self.loading_msg = "Initializing..."
        self.is_crashed = False
        self.crash_progress = 0
        self.crash_reason = ""
        self.admin_open = False
        self.admin_selection = 0
        self.screen_shake = 0
        self.weapon_fired = 0
        self.step_timer = 0
        self.msg_timer = 0
        self.wanted_level = 0
        self.wanted_decay_timer = 0.0
        self.crosshair_hit = 0
        self.damage_flash = 0
        self.automap = False

        # Doors
        self.doors = {}
        for dy, dx in DOOR_POSITIONS:
            self.doors[(dy, dx)] = {'open': 0.0, 'opening': False, 'timer': 0.0}

        # Statistics
        self.kills = 0
        self.items_collected = 0
        self.secrets_found = 0
        self.level_start_time = 0

        # Mouse
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

        # Admin items
        self.admin_items = [
            ("Spawn Civilian", lambda: self.admin_spawn('civilian')),
            ("Spawn MCPD", lambda: self.admin_spawn('mcpd')),
            ("Spawn ECPU", lambda: self.admin_spawn('ecpu')),
            ("Spawn RPG Ganger", lambda: self.admin_spawn('rpg')),
            ("Spawn Imp", lambda: self.admin_spawn('imp')),
            ("Spawn Demon", lambda: self.admin_spawn('demon')),
            ("Spawn Pink Charger", lambda: self.admin_spawn('charger')),
            ("Spawn Anime Pillow", lambda: self.admin_spawn('pillow')),
            ("Toggle Noclip", self.toggle_noclip),
            ("Give All Weapons", self.give_all_weapons),
            ("Fire Combine Ball Burst", self.fire_burst),
            ("SPAWN 55 CHARGERS [CRASH]", self.mass_spawn_crash),
            ("Teleport → Maine HQ", lambda: self.trigger_loading("Maine HQ")),
            ("ent_remove_all", self.clear_all),
            ("Kill Server", lambda: self.trigger_crash("Manual exec override")),
            ("Dark Leader Override", self.dark_leader_override),
            ("Close Panel", lambda: self.toggle_admin()),
        ]

        # Cheat mode weapon grant
        if getattr(self, 'cheat_mode', False):
            self.give_all_weapons()

    def _gen_error_sprite(self):
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        surf.fill((200, 0, 0, 200))
        t = self.font_hud.render("ERROR", True, (255, 255, 255))
        surf.blit(t, (SPRITE_SIZE // 2 - t.get_width() // 2, SPRITE_SIZE // 2 - t.get_height() // 2))
        return surf

    def _gen_checker_sprite(self):
        surf = pygame.Surface((SPRITE_SIZE, SPRITE_SIZE), pygame.SRCALPHA)
        sz = 8
        for y in range(SPRITE_SIZE):
            for x in range(SPRITE_SIZE):
                cell = (x // sz + y // sz) % 2
                if cell == 0:
                    surf.set_at((x, y), (255, 0, 255, 200))
                else:
                    surf.set_at((x, y), (0, 0, 0, 200))
        return surf

    # ── Door mechanics ──
    def is_door_open(self, dy, dx):
        door = self.doors.get((dy, dx))
        if door:
            return door['open'] > 0.8
        return False

    def try_open_door(self, dy, dx):
        door = self.doors.get((dy, dx))
        if door and not door['opening'] and door['open'] < 0.5:
            door['opening'] = True
            door['timer'] = 4.0  # stays open for 4 sec
            self.snd_door.play()
            self.add_log('info', f'Door opening at ({dx},{dy})')

    def update_doors(self, dt):
        for key, door in self.doors.items():
            if door['opening']:
                door['open'] = min(1.0, door['open'] + dt * 2)
                if door['open'] >= 1.0:
                    door['timer'] -= dt
                    if door['timer'] <= 0:
                        door['opening'] = False
            else:
                if door['open'] > 0:
                    door['open'] = max(0.0, door['open'] - dt * 1.5)

    def check_nearby_doors(self):
        """Auto-open doors near the player (Doom-style use key)."""
        for (dy, dx), door in self.doors.items():
            dist = math.sqrt((self.player_x - (dx + 0.5)) ** 2 + (self.player_y - (dy + 0.5)) ** 2)
            if dist < 2.0:
                self.try_open_door(dy, dx)

    # ── World population ──
    def populate_world(self):
        # Civilians scattered across city
        civilian_zones = [
            (2, 5, 2, 5),       # Plaza
            (7, 12, 7, 11),     # Central
            (1, 5, 7, 10),      # West side
            (7, 14, 1, 5),      # North corridor
            (2, 10, 24, 30),    # Market District
            (14, 22, 24, 30),   # Market East
            (33, 40, 1, 7),     # Church area
        ]
        for _ in range(14):
            zone = random.choice(civilian_zones)
            x = random.uniform(zone[0], zone[1])
            y = random.uniform(zone[2], zone[3])
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(Civilian(x, y, self.sprite_civilian))

        # MCPD units — 8 officers across all patrol zones
        mcpd_spawns = [
            (11.5, 19.5), (12.0, 20.5),  # MCPD station
            (5.5, 8.5),   (8.5, 4.5),    # Plaza patrol
            (14.5, 9.5),  (8.5, 15.5),   # Central patrol
            (5.5, 26.5),  (15.5, 28.5),  # Market district patrol
        ]
        for sx, sy in mcpd_spawns:
            if 0 <= int(sy) < MAP_H and 0 <= int(sx) < MAP_W and MAP[int(sy)][int(sx)] == 0:
                self.entities.append(MCPDUnit(sx, sy, self.sprite_mcpd))

        # ECPU at HQ
        for _ in range(2):
            x = random.uniform(19, 21)
            y = random.uniform(3.5, 5.5)
            if MAP[int(y)][int(x)] == 0:
                self.entities.append(ECPUUnit(x, y, self.sprite_ecpu))

        # RPG Gang at depot
        for _ in range(4):
            x = random.uniform(16.5, 21.5)
            y = random.uniform(13.5, 16.5)
            if MAP[int(y)][int(x)] == 0:
                self.entities.append(RPGGanger(x, y, self.sprite_rpg))

        # RPG Gang in market stalls
        for _ in range(3):
            x = random.uniform(3, 10)
            y = random.uniform(25, 30)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(RPGGanger(x, y, self.sprite_rpg))

        # Military Units at Military Base
        for _ in range(6):
            x = random.uniform(33, 45)
            y = random.uniform(29, 37)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(MilitaryUnit(x, y, self.sprite_military))

        # === MONSTER SPAWNER ZONE (east wing / sewer / monster den) ===
        # Original east sector
        for _ in range(6):
            x = random.uniform(25, 31)
            y = random.uniform(8, 22)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(ImpEntity(x, y, self.sprite_imp))

        # NEW: Far east monster cave (the big new area)
        for _ in range(5):
            x = random.uniform(33, 46)
            y = random.uniform(8, 14)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(ImpEntity(x, y, self.sprite_imp))

        # NEW: Monster Den (south-east)
        for _ in range(6):
            x = random.uniform(33, 46)
            y = random.uniform(28, 38)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(ImpEntity(x, y, self.sprite_imp))

        # Demons in armory area
        for _ in range(3):
            x = random.uniform(25, 30)
            y = random.uniform(1.5, 5)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(DemonEntity(x, y, self.sprite_demon))

        # Demons in original sewer tunnels
        for _ in range(3):
            x = random.uniform(25, 31)
            y = random.uniform(19, 22)
            if 0 <= int(y) < MAP_H and 0 <= int(x) < MAP_W and MAP[int(y)][int(x)] == 0:
                self.entities.append(DemonEntity(x, y, self.sprite_demon))

        # Pickups scattered
        pickup_positions = [
            (3.5, 1.5, 'health_small'),
            (8.5, 3.5, 'ammo_bullets'),
            (5.5, 8.5, 'health_large'),
            (11.5, 9.5, 'ammo_shells'),
            (15.5, 5.5, 'armor_small'),
            (20.5, 6.5, 'health_small'),
            (3.5, 15.5, 'ammo_bullets'),
            (8.5, 18.5, 'health_small'),
            (14.5, 14.5, 'ammo_rockets'),
            (18.5, 10.5, 'armor_large'),
            (22.5, 5.5, 'ammo_energy'),
            (7.5, 10.5, 'ammo_cells'),
            (26.5, 2.5, 'health_large'),
            (28.5, 4.5, 'ammo_shells'),
            (26.5, 8.5, 'ammo_cells'),
            (28.5, 12.5, 'health_small'),
            (27.5, 15.5, 'ammo_rockets'),
            (26.5, 20.5, 'ammo_energy'),
            (29.5, 21.5, 'health_large'),
            (4.5, 12.5, 'armor_small'),
        ]

        for px, py, ptype in pickup_positions:
            if 0 <= int(py) < MAP_H and 0 <= int(px) < MAP_W and MAP[int(py)][int(px)] == 0:
                spr = self.pickup_sprites.get(ptype, self.pickup_sprites['health_small'])
                self.pickups.append(Pickup(px, py, ptype, spr))

        # Weapon pickups (as entities near spawn)
        self.weapon_pickup_positions = [
            (8.5, 5.5, 2, 'Shotgun'),   # Shotgun near plaza
            (15.5, 8.5, 3, 'AR2 Pulse Rifle'),  # AR2 in corridor
            (18.5, 14.5, 4, 'RPG-7'),   # RPG near depot
            (20.5, 4.5, 5, 'Combine Ball Launcher'),  # At ECPU HQ
            (27.5, 3.5, 6, 'Presidential Strike'),  # Deep in armory
        ]
        self.weapon_pickups_alive = [True] * len(self.weapon_pickup_positions)

        # Berserk pack in sewer
        if MAP[14][27] == 0:
            self.pickups.append(Pickup(27.5, 14.5, 'berserk', self.pickup_sprites['berserk']))

        self.add_log('sys', f'World populated. Entity count: {len(self.entities)}')
        self.add_log('info', 'Ammo Shift ACTIVE — item_ammo_smg1 deprecated')
        self.add_log('admin', 'President Michael logged in [superuser | sv_cheats 1]')
        self.level_start_time = self.sim_time

    # ── Logging ──
    def add_log(self, level, msg):
        self.console_log.append({'level': level, 'msg': msg, 'time': self.sim_time, 'age': 0})
        if len(self.console_log) > 16:
            self.console_log.pop(0)

    # ── Sound helpers (spatial attenuation) ──
    def _play_spatial(self, snd, sx=None, sy=None, max_dist=None):
        """Play a sound attenuated by distance. Silent if source is outside SOUND_RANGE."""
        if max_dist is None:
            max_dist = SOUND_RANGE
        if sx is not None and sy is not None:
            dist = math.sqrt((sx - self.player_x) ** 2 + (sy - self.player_y) ** 2)
            if dist > max_dist:
                return  # Too far away — skip entirely
            vol = max(0.05, 1.0 - (dist / max_dist) ** 0.6)
            snd.set_volume(vol)
        else:
            snd.set_volume(1.0)
        ch = snd.play()
        return ch

    def play_radio_click(self, sx=None, sy=None):
        self._play_spatial(self.snd_radio, sx, sy)

    def play_combine_hit(self, sx=None, sy=None):
        self._play_spatial(self.snd_combine_hit, sx, sy)

    def play_explosion(self, sx=None, sy=None):
        self._play_spatial(self.snd_explosion, sx, sy, max_dist=22.0)

    def play_pickup(self):
        self.snd_pickup.set_volume(1.0)
        self.snd_pickup.play()

    def play_pain(self, sx=None, sy=None):
        self._play_spatial(self.snd_pain, sx, sy)

    def play_death(self, sx=None, sy=None):
        self._play_spatial(self.snd_death, sx, sy)

    # ── Combat helpers ──
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

    def add_wanted(self, stars):
        """Increase wanted level and trigger appropriate response."""
        old_level = self.wanted_level
        self.wanted_level = min(5, self.wanted_level + stars)
        self.wanted_decay_timer = 10.0  # 10 seconds before decay starts
        
        if self.wanted_level > old_level:
            self.add_log('warn', f'[WANTED] Level increased to {self.wanted_level} stars')
            if self.wanted_level >= 3 and old_level < 3:
                self.add_log('sys', '[DISPATCH] ECPU Units deploying to sector')
            if self.wanted_level >= 4 and old_level < 4:
                self.add_log('admin', '[DISPATCH] Foreign Military authorized')
            
            # Alert nearby cops
            for e in self.entities:
                if e.type == 'mcpd' and e.alive:
                    d = math.sqrt((e.x - self.player_x)**2 + (e.y - self.player_y)**2)
                    if d < 30:
                        e.ai_state = AI_CHASE
                        e.last_known_px = self.player_x
                        e.last_known_py = self.player_y

    def report_sound_event(self, x, y, radius, factions):
        """Alert nearby NPCs of a specific sound (gunshots, explosions)."""
        for e in self.entities:
            if not e.alive or e.type not in factions:
                continue
            d = math.sqrt((e.x - x)**2 + (e.y - y)**2)
            if d < radius:
                # If they are idle, put them in alert to investigate
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
        self.explosions_list.append(Explosion(x, y, self.sprite_explosion))
        self.screen_shake = max(self.screen_shake, 0.3)

    def player_take_damage(self, amt):
        if self.invuln_timer > 0:
            return
        if self.player_armor > 0:
            absorbed = min(amt // 2, self.player_armor)
            self.player_armor -= absorbed
            amt -= absorbed
        self.player_health -= amt
        self.damage_flash = 0.3
        self.screen_shake = max(self.screen_shake, 0.2)
        if self.player_health <= 0:
            self.player_health = 100
            self.player_armor = 0
            self.player_x = 4.5
            self.player_y = 4.5
            self.add_log('error', '[DEATH] President Michael respawned (executive privilege)')

    # ── Weapon firing ──
    def fire_weapon(self):
        weap = WEAPONS[self.current_weapon]
        if self.weapon_cooldown > 0:
            return

        # Check ammo
        if weap['ammo_type'] and not getattr(self, 'cheat_mode', False):
            if self.ammo.get(weap['ammo_type'], 0) < weap['ammo_use']:
                return
            self.ammo[weap['ammo_type']] -= weap['ammo_use']

        self.weapon_cooldown = weap['fire_rate']
        self.weapon_fired = 1.0
        self.screen_shake = max(self.screen_shake, 0.1)

        # Play weapon sound
        snd_map = {
            0: self.snd_crowbar, 1: self.snd_pistol, 2: self.snd_shotgun,
            3: self.snd_ar2, 4: self.snd_rpg, 5: self.snd_combine_fire,
            6: self.snd_bfg,
        }
        snd = snd_map.get(self.current_weapon)
        if snd:
            snd.play()

        # Report sound event to alert AI (larger radius for heavier weapons)
        radius = 30 if self.current_weapon in (2, 4, 6) else 15
        self.report_sound_event(self.player_x, self.player_y, radius, ['mcpd', 'military', 'ecpu', 'imp', 'demon', 'rpg'])

        if weap['hitscan']:
            # Hitscan weapons
            pellets = weap.get('pellets', 1)
            for _ in range(pellets):
                angle = self.player_angle + random.uniform(-weap['spread'], weap['spread'])
                self._hitscan_fire(angle, weap['damage'], weap['range'])
        elif weap['projectile']:
            tx = self.player_x + math.cos(self.player_angle) * 20
            ty = self.player_y + math.sin(self.player_angle) * 20
            if self.current_weapon == 4:  # RPG
                self.projectiles.append(RPGRocket(self.player_x, self.player_y, tx, ty, None))
            elif self.current_weapon == 5:  # Combine ball
                self.projectiles.append(CombineBall(self.player_x, self.player_y, tx, ty, 'player'))
            elif self.current_weapon == 6:  # BFG
                self.projectiles.append(BFGBall(self.player_x, self.player_y, tx, ty))
                self.screen_shake = 0.5

    def _hitscan_fire(self, angle, damage, max_range):
        """Fire a hitscan ray and damage the first entity hit."""
        sin_a = math.sin(angle)
        cos_a = math.cos(angle)

        if self.berserk_timer > 0 and self.current_weapon == 0:
            damage *= 10  # Berserk crowbar

        # Step along ray
        step = 0.2
        dist = 0
        while dist < max_range:
            dist += step
            rx = self.player_x + cos_a * dist
            ry = self.player_y + sin_a * dist

            # Wall check
            mx, my = int(rx), int(ry)
            if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H:
                break
            if MAP[my][mx] != 0 and not (MAP[my][mx] == 6 and self.is_door_open(my, mx)):
                break

            # Entity check
            for e in self.entities:
                if not e.alive:
                    continue
                d = math.sqrt((rx - e.x) ** 2 + (ry - e.y) ** 2)
                if d < 0.6:
                    e.take_damage(damage, self, source='player')
                    self.crosshair_hit = 0.3
                    if self.current_weapon == 2:  # Shotgun pushback
                        pushx = cos_a * 3
                        pushy = sin_a * 3
                        e.vx += pushx
                        e.vy += pushy
                    return

    # ── Admin commands ──
    def admin_spawn(self, etype):
        sx = self.player_x + math.cos(self.player_angle) * 2
        sy = self.player_y + math.sin(self.player_angle) * 2
        mx, my = int(sx), int(sy)
        if mx < 0 or mx >= MAP_W or my < 0 or my >= MAP_H or MAP[my][mx] != 0:
            sx, sy = self.player_x, self.player_y

        sprite_map = {
            'civilian': (Civilian, self.sprite_civilian),
            'mcpd': (MCPDUnit, self.sprite_mcpd),
            'ecpu': (ECPUUnit, self.sprite_ecpu),
            'rpg': (RPGGanger, self.sprite_rpg),
            'imp': (ImpEntity, self.sprite_imp),
            'demon': (DemonEntity, self.sprite_demon),
        }

        if etype in sprite_map:
            cls, spr = sprite_map[etype]
            self.entities.append(cls(sx, sy, spr))
            self.add_log('admin', f'[PRESIDENT] Spawned {etype} at ({sx:.1f},{sy:.1f})')
        elif etype == 'charger':
            self.entities.append(PropEntity(sx, sy, 'charger', self.sprite_charger))
            self.add_log('admin', '[PRESIDENT] Pink Charger spawned — instability ↑')
            self.snd_metal.play()
            self.check_crash_threshold()
        elif etype == 'pillow':
            self.entities.append(PropEntity(sx, sy, 'pillow', self.sprite_pillow))
            self.add_log('admin', '[PRESIDENT] Anime Pillow spawned')
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
        self.add_log('admin', '[PRESIDENT] All weapons given — FULLY ARMED')

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
            self.entities.append(PropEntity(sx, sy, 'charger', self.sprite_charger))
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
        self.admin_selection = 0
        pygame.mouse.set_visible(self.admin_open)
        pygame.event.set_grab(not self.admin_open)

    def trigger_loading(self, zone_name):
        self.is_loading = True
        self.loading_progress = 0
        self.loading_msg = f"Loading {zone_name}..."
        self.admin_open = False
        pygame.mouse.set_visible(False)
        pygame.event.set_grab(True)

    def trigger_crash(self, reason):
        self.is_crashed = True
        self.crash_progress = 0
        self.crash_reason = reason
        self.admin_open = False

    # ═══════════════════════════════════════════════
    #  RAYCASTING RENDERER
    # ═══════════════════════════════════════════════
    def raycast(self):
        surf = self.render_surf
        half_h = INTERNAL_H // 2

        # Draw floor/ceiling gradient
        for y in range(INTERNAL_H):
            if y < half_h:
                t = y / half_h
                r = int(8 + t * 8)
                g = int(8 + t * 6)
                b = int(14 + t * 12)
                pygame.draw.line(surf, (r, g, b), (0, y), (INTERNAL_W, y))
            else:
                t = (y - half_h) / half_h
                r = int(20 + t * 15)
                g = int(18 + t * 12)
                b = int(22 + t * 8)
                pygame.draw.line(surf, (r, g, b), (0, y), (INTERNAL_W, y))

        # Cast rays
        ray_angle = self.player_angle - HALF_FOV
        for ray_idx in range(NUM_RAYS):
            sin_a = math.sin(ray_angle)
            cos_a = math.cos(ray_angle)

            depth, wall_type, tex_x, side = self._dda(sin_a, cos_a)

            depth *= math.cos(ray_angle - self.player_angle)
            # Clamp minimum depth — increased to stop near-wall texture stretching
            depth = max(0.5, depth)
            self.z_buffer[ray_idx] = depth

            if depth < MAX_DEPTH and wall_type > 0:
                # Handle doors — reduce visible wall height based on door open state
                effective_wall = wall_type
                if wall_type == 6:
                    # Find which door this ray hit
                    hit_x = self.player_x + cos_a * (depth / math.cos(ray_angle - self.player_angle))
                    hit_y = self.player_y + sin_a * (depth / math.cos(ray_angle - self.player_angle))
                    dx, dy = int(hit_x), int(hit_y)
                    door = self.doors.get((dy, dx))
                    if door and door['open'] > 0.01:
                        # Partially open door — render shorter
                        wall_height = min(INTERNAL_H, int(INTERNAL_H / depth))
                        wall_height = int(wall_height * (1 - door['open']))
                        if wall_height < 2:
                            ray_angle += DELTA_ANGLE
                            continue
                        draw_start = half_h - wall_height // 2
                        tex = self.textures_dark[6] if side == 1 else self.textures[6]
                        tex_col_x = int(tex_x * TEX_SIZE) % TEX_SIZE
                        src_rect = pygame.Rect(tex_col_x, 0, 1, TEX_SIZE)
                        col_surf = tex.subsurface(src_rect)
                        scaled = pygame.transform.scale(col_surf, (max(1, int(SCALE)), max(1, wall_height)))
                        fog = max(0, min(1, 1 - depth / MAX_DEPTH))
                        if fog < 1.0:
                            fog_surf = pygame.Surface(scaled.get_size())
                            fog_surf.fill(COL_DARKBG)
                            fog_surf.set_alpha(int((1 - fog) * 200))
                            scaled.blit(fog_surf, (0, 0))
                        surf.blit(scaled, (int(ray_idx * SCALE), draw_start))
                        ray_angle += DELTA_ANGLE
                        continue

                wall_height = min(INTERNAL_H - 2, int(INTERNAL_H / depth))
                draw_start = half_h - wall_height // 2

                tex = self.textures_dark.get(effective_wall, self.textures.get(effective_wall))
                if not tex:
                    tex = self.textures[1]
                if side == 0 and effective_wall in self.textures:
                    tex = self.textures[effective_wall]

                tex_col_x = int(tex_x * TEX_SIZE) % TEX_SIZE
                src_rect = pygame.Rect(tex_col_x, 0, 1, TEX_SIZE)
                col_surf = tex.subsurface(src_rect)
                scaled = pygame.transform.scale(col_surf, (max(1, int(SCALE)), max(1, wall_height)))

                fog = max(0, min(1, 1 - depth / MAX_DEPTH))
                if fog < 1.0:
                    fog_surf = pygame.Surface(scaled.get_size())
                    fog_surf.fill(COL_DARKBG)
                    fog_surf.set_alpha(int((1 - fog) * 200))
                    scaled.blit(fog_surf, (0, 0))

                surf.blit(scaled, (int(ray_idx * SCALE), draw_start))

            ray_angle += DELTA_ANGLE

    def _dda(self, sin_a, cos_a):
        px, py = self.player_x, self.player_y
        if cos_a == 0: cos_a = 0.00001
        if sin_a == 0: sin_a = 0.00001

        # Horizontal
        y_hor = int(py) + (1 if sin_a > 0 else 0)
        dy = 1 if sin_a > 0 else -1
        depth_hor = (y_hor - py) / sin_a
        x_hor = px + depth_hor * cos_a
        delta_depth_hor = dy / sin_a
        dx_hor = delta_depth_hor * cos_a

        wall_hor = 0
        tex_x_hor = 0
        for _ in range(int(MAX_DEPTH)):
            mx = int(x_hor)
            my = int(y_hor) if sin_a > 0 else int(y_hor) - 1
            if 0 <= mx < MAP_W and 0 <= my < MAP_H and MAP[my][mx] != 0:
                # Check if door and open
                if MAP[my][mx] == 6 and self.is_door_open(my, mx):
                    pass  # Treat as open
                else:
                    wall_hor = MAP[my][mx]
                    tex_x_hor = x_hor % 1
                    break
            x_hor += dx_hor
            y_hor += dy
            depth_hor += abs(delta_depth_hor)
        else:
            depth_hor = MAX_DEPTH

        # Vertical
        x_ver = int(px) + (1 if cos_a > 0 else 0)
        dx = 1 if cos_a > 0 else -1
        depth_ver = (x_ver - px) / cos_a
        y_ver = py + depth_ver * sin_a
        delta_depth_ver = dx / cos_a
        dy_ver = delta_depth_ver * sin_a

        wall_ver = 0
        tex_x_ver = 0
        for _ in range(int(MAX_DEPTH)):
            mx = int(x_ver) if cos_a > 0 else int(x_ver) - 1
            my = int(y_ver)
            if 0 <= mx < MAP_W and 0 <= my < MAP_H and MAP[my][mx] != 0:
                if MAP[my][mx] == 6 and self.is_door_open(my, mx):
                    pass
                else:
                    wall_ver = MAP[my][mx]
                    tex_x_ver = y_ver % 1
                    break
            x_ver += dx
            y_ver += dy_ver
            depth_ver += abs(delta_depth_ver)
        else:
            depth_ver = MAX_DEPTH

        if depth_ver < depth_hor:
            return depth_ver, wall_ver, tex_x_ver, 1
        else:
            return depth_hor, wall_hor, tex_x_hor, 0

    # ═══════════════════════════════════════════════
    #  SPRITE RENDERER (BILLBOARD)
    # ═══════════════════════════════════════════════
    def render_sprites(self):
        surf = self.render_surf
        half_h = INTERNAL_H // 2
        sprites_to_draw = []

        # Entities
        for e in self.entities:
            if not e.alive:
                continue
            dx = e.x - self.player_x
            dy = e.y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.3 or dist > MAX_DEPTH:
                continue

            sprite_angle = math.atan2(dy, dx) - self.player_angle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            if abs(sprite_angle) > HALF_FOV + 0.3:
                continue

            if e.model_missing:
                spr = self.sprite_error
            elif e.texture_failure:
                spr = self.sprite_checker
            elif e.ai_state == AI_PAIN:
                # Flash red on pain
                spr = e.sprite.copy()
                red_tint = pygame.Surface(spr.get_size(), pygame.SRCALPHA)
                red_tint.fill((255, 0, 0, 100))
                spr.blit(red_tint, (0, 0))
            else:
                spr = e.sprite

            sprites_to_draw.append((dist, sprite_angle, spr, e))

        # Corpses
        for corpse in self.corpses:
            dx = corpse['x'] - self.player_x
            dy = corpse['y'] - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.3 or dist > MAX_DEPTH:
                continue
            sprite_angle = math.atan2(dy, dx) - self.player_angle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            if abs(sprite_angle) > HALF_FOV + 0.3:
                continue
            spr = self.corpse_sprites.get(corpse['type'])
            if spr:
                sprites_to_draw.append((dist, sprite_angle, spr, None))

        # Pickups
        for p in self.pickups:
            if not p.alive:
                continue
            dx = p.x - self.player_x
            dy = p.y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.2 or dist > MAX_DEPTH:
                continue
            sprite_angle = math.atan2(dy, dx) - self.player_angle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            if abs(sprite_angle) > HALF_FOV + 0.3:
                continue
            sprites_to_draw.append((dist, sprite_angle, p.sprite, None))

        # Weapon pickups
        for i, (wx, wy, wid, wname) in enumerate(self.weapon_pickup_positions):
            if not self.weapon_pickups_alive[i]:
                continue
            dx = wx - self.player_x
            dy = wy - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.2 or dist > MAX_DEPTH:
                continue
            sprite_angle = math.atan2(dy, dx) - self.player_angle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            if abs(sprite_angle) > HALF_FOV + 0.3:
                continue
            # Use combine ball sprite with weapon color
            col = WEAPONS[wid]['color']
            spr = pygame.Surface((32, 32), pygame.SRCALPHA)
            pygame.draw.circle(spr, (*col, 100), (16, 16), 14)
            pygame.draw.circle(spr, (*col, 200), (16, 16), 8)
            pygame.draw.circle(spr, (255, 255, 255, 200), (16, 16), 4)
            sprites_to_draw.append((dist, sprite_angle, spr, None))

        # Projectiles
        for p in self.projectiles:
            if not p.alive:
                continue
            dx = p.x - self.player_x
            dy = p.y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.2 or dist > MAX_DEPTH:
                continue
            sprite_angle = math.atan2(dy, dx) - self.player_angle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            if abs(sprite_angle) > HALF_FOV + 0.3:
                continue

            if hasattr(p, 'proj_type'):
                if p.proj_type == 'bfg':
                    spr = self.sprite_bfg
                elif p.proj_type == 'rocket':
                    spr = self.sprite_rocket
                elif p.proj_type == 'fireball':
                    # Orange fireball
                    spr = pygame.Surface((16, 16), pygame.SRCALPHA)
                    pygame.draw.circle(spr, (255, 150, 0, 200), (8, 8), 7)
                    pygame.draw.circle(spr, (255, 255, 100), (8, 8), 4)
                else:
                    spr = self.sprite_combine_ball
            else:
                spr = self.sprite_combine_ball

            sprites_to_draw.append((dist, sprite_angle, spr, None))

        # Explosions
        for ex in self.explosions_list:
            if not ex.alive:
                continue
            dx = ex.x - self.player_x
            dy = ex.y - self.player_y
            dist = math.sqrt(dx * dx + dy * dy)
            if dist < 0.2 or dist > MAX_DEPTH:
                continue
            sprite_angle = math.atan2(dy, dx) - self.player_angle
            while sprite_angle > math.pi: sprite_angle -= 2 * math.pi
            while sprite_angle < -math.pi: sprite_angle += 2 * math.pi
            if abs(sprite_angle) > HALF_FOV + 0.3:
                continue
            sprites_to_draw.append((dist, sprite_angle, ex.sprite, None))

        # Sort far to near
        sprites_to_draw.sort(key=lambda s: s[0], reverse=True)

        for dist, angle, spr, ent in sprites_to_draw:
            sprite_h = min(INTERNAL_H, int(INTERNAL_H / (dist + 0.001) * 0.6))
            sprite_w = sprite_h
            if sprite_w < 2 or sprite_h < 2:
                continue

            screen_x = int((angle / FOV + 0.5) * INTERNAL_W)
            draw_x = screen_x - sprite_w // 2
            draw_y = half_h - sprite_h // 2

            scaled = pygame.transform.scale(spr, (sprite_w, sprite_h))

            fog = max(0, min(1, 1 - dist / MAX_DEPTH))
            if fog < 0.95:
                fog_surf = pygame.Surface((sprite_w, sprite_h))
                fog_surf.fill(COL_DARKBG)
                fog_surf.set_alpha(int((1 - fog) * 180))
                scaled.blit(fog_surf, (0, 0), special_flags=0)

            # Column Z-test
            for col in range(sprite_w):
                screen_col = draw_x + col
                if 0 <= screen_col < INTERNAL_W:
                    if dist < self.z_buffer[screen_col]:
                        col_surf = scaled.subsurface(pygame.Rect(col, 0, 1, sprite_h))
                        surf.blit(col_surf, (screen_col, draw_y))

            # Health bar
            if ent and hasattr(ent, 'health') and ent.health < ent.max_health:
                bar_w = max(sprite_w // 2, 8)
                bar_h = max(2, sprite_h // 20)
                bar_x = screen_x - bar_w // 2
                bar_y = draw_y - bar_h - 2
                if 0 <= bar_x < INTERNAL_W and 0 <= bar_y < INTERNAL_H:
                    hp_pct = ent.health / ent.max_health
                    pygame.draw.rect(surf, (0, 0, 0), (bar_x, bar_y, bar_w, bar_h))
                    color = (60, 255, 60) if hp_pct > 0.5 else (255, 60, 60)
                    pygame.draw.rect(surf, color, (bar_x, bar_y, int(bar_w * hp_pct), bar_h))

    # ═══════════════════════════════════════════════
    #  WEAPON VIEWMODEL
    # ═══════════════════════════════════════════════
    def render_weapon(self, surf):
        w, h = surf.get_size()
        bob_x = math.sin(self.sim_time * 4) * 4
        bob_y = abs(math.sin(self.sim_time * 8)) * 3

        # Weapon kick from firing
        kick = max(0, self.weapon_fired) * 20

        wx = w // 2 + 60 + int(bob_x)
        wy = h - 24 + int(bob_y) + int(kick)

        weap = WEAPONS[self.current_weapon]
        col = weap['color']
        dark_col = tuple(max(0, c - 50) for c in col)
        light_col = tuple(min(255, c + 50) for c in col)

        if self.current_weapon == 0:  # Crowbar
            # Wooden handle with grain
            pygame.draw.rect(surf, (90, 55, 25), (wx - 5, wy - 55, 10, 55))
            pygame.draw.rect(surf, (110, 65, 30), (wx - 3, wy - 55, 3, 55))  # Highlight
            # Metal head with curve
            pygame.draw.rect(surf, col, (wx - 14, wy - 68, 28, 15))
            pygame.draw.rect(surf, light_col, (wx - 14, wy - 68, 28, 3))  # Top edge
            # Claw prongs
            pygame.draw.polygon(surf, dark_col, [(wx - 12, wy - 68), (wx - 16, wy - 80), (wx - 8, wy - 68)])
            pygame.draw.polygon(surf, dark_col, [(wx + 8, wy - 68), (wx + 12, wy - 80), (wx + 4, wy - 68)])
            # Rivet detail
            pygame.draw.circle(surf, (60, 60, 60), (wx, wy - 62), 2)

        elif self.current_weapon == 1:  # M9 Pistol
            # Grip with grooves
            pygame.draw.rect(surf, (35, 35, 35), (wx - 7, wy - 32, 14, 35))
            for gy in range(wy - 28, wy, 4):
                pygame.draw.line(surf, (50, 50, 50), (wx - 5, gy), (wx + 5, gy))
            # Trigger guard
            pygame.draw.rect(surf, (30, 30, 30), (wx - 9, wy - 26, 3, 12))
            # Slide
            pygame.draw.rect(surf, col, (wx - 6, wy - 60, 12, 30))
            pygame.draw.rect(surf, light_col, (wx - 6, wy - 60, 12, 3))  # Top highlight
            pygame.draw.rect(surf, dark_col, (wx - 6, wy - 32, 12, 3))  # Bottom shadow
            # Barrel
            pygame.draw.rect(surf, (60, 60, 55), (wx - 3, wy - 68, 6, 10))
            # Sight
            pygame.draw.rect(surf, (255, 255, 255), (wx - 1, wy - 62, 2, 3))
            # Ejection port
            pygame.draw.rect(surf, (80, 80, 75), (wx + 2, wy - 50, 4, 8))

        elif self.current_weapon == 2:  # Pump Shotgun
            # Buttstock
            pygame.draw.rect(surf, (70, 45, 20), (wx - 10, wy - 28, 20, 38))
            pygame.draw.rect(surf, (85, 55, 25), (wx - 8, wy - 28, 4, 38))  # Wood grain
            # Receiver
            pygame.draw.rect(surf, (50, 50, 50), (wx - 8, wy - 45, 16, 20))
            pygame.draw.rect(surf, (65, 65, 65), (wx - 8, wy - 45, 16, 3))  # Highlight
            # Barrel (long)
            pygame.draw.rect(surf, col, (wx - 5, wy - 82, 10, 40))
            pygame.draw.rect(surf, light_col, (wx - 5, wy - 82, 3, 40))  # Side highlight
            # Pump grip
            pygame.draw.rect(surf, (90, 75, 50), (wx - 7, wy - 55, 14, 10))
            pygame.draw.rect(surf, (110, 90, 60), (wx - 7, wy - 55, 14, 2))  # Pump highlight
            # Muzzle
            pygame.draw.rect(surf, dark_col, (wx - 6, wy - 85, 12, 5))
            pygame.draw.circle(surf, (0, 0, 0), (wx, wy - 85), 3)  # Bore
            # Shell tube
            pygame.draw.rect(surf, (45, 45, 45), (wx + 4, wy - 72, 4, 25))

        elif self.current_weapon == 3:  # AR2 Pulse Rifle
            # Grip
            pygame.draw.rect(surf, (25, 25, 35), (wx - 9, wy - 28, 18, 32))
            # Body
            pygame.draw.rect(surf, (35, 40, 55), (wx - 8, wy - 68, 16, 44))
            pygame.draw.rect(surf, col, (wx - 8, wy - 68, 16, 3))  # Top highlight
            # Barrel shroud
            pygame.draw.rect(surf, (50, 60, 80), (wx - 5, wy - 80, 10, 14))
            # Muzzle with glow
            pygame.draw.rect(surf, (40, 80, 180), (wx - 4, wy - 84, 8, 6))
            # Energy cell window (animated)
            glow = int(128 + 127 * math.sin(self.sim_time * 10))
            pygame.draw.rect(surf, (0, glow, 255), (wx - 4, wy - 58, 8, 4))
            # Scope rail
            pygame.draw.rect(surf, (60, 60, 60), (wx - 6, wy - 72, 12, 2))
            # Magazine
            pygame.draw.rect(surf, (30, 30, 40), (wx + 5, wy - 50, 6, 18))

        elif self.current_weapon == 4:  # RPG-7
            # Grip tube
            pygame.draw.rect(surf, (55, 50, 45), (wx - 12, wy - 25, 24, 30))
            # Launch tube (thick)
            pygame.draw.rect(surf, col, (wx - 10, wy - 82, 20, 60))
            pygame.draw.rect(surf, light_col, (wx - 10, wy - 82, 5, 60))  # Side highlight
            # Muzzle bell
            pygame.draw.ellipse(surf, dark_col, (wx - 13, wy - 88, 26, 10))
            pygame.draw.ellipse(surf, (0, 0, 0), (wx - 9, wy - 86, 18, 6))  # Bore
            # Rear sight
            pygame.draw.rect(surf, (80, 80, 80), (wx - 14, wy - 55, 3, 10))
            pygame.draw.rect(surf, (80, 80, 80), (wx + 11, wy - 55, 3, 10))
            # Warhead visible in tube
            pygame.draw.polygon(surf, (180, 60, 30), [(wx, wy - 90), (wx - 5, wy - 82), (wx + 5, wy - 82)])

        elif self.current_weapon == 5:  # Combine Ball Launcher
            # Heavy housing
            pygame.draw.rect(surf, (45, 45, 60), (wx - 18, wy - 30, 36, 50))
            pygame.draw.rect(surf, (55, 55, 70), (wx - 16, wy - 30, 4, 50))  # Side highlight
            # Upper body
            pygame.draw.rect(surf, (55, 55, 70), (wx - 13, wy - 55, 26, 28))
            # Barrel assembly
            pygame.draw.rect(surf, (40, 40, 55), (wx - 7, wy - 78, 14, 26))
            # Energy core (animated glow)
            pulse = math.sin(self.sim_time * 12)
            core_r = int(6 + pulse * 3)
            # Outer glow
            glow_surf = pygame.Surface((core_r * 4, core_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 200, 0, 60), (core_r * 2, core_r * 2), core_r * 2)
            pygame.draw.circle(glow_surf, (255, 220, 50, 120), (core_r * 2, core_r * 2), core_r)
            surf.blit(glow_surf, (wx - core_r * 2, wy - 82 - core_r * 2))
            pygame.draw.circle(surf, col, (wx, wy - 82), core_r)
            pygame.draw.circle(surf, (255, 255, 200), (wx, wy - 82), core_r // 2)
            # Tech details
            pygame.draw.rect(surf, (80, 80, 100), (wx - 15, wy - 44, 30, 2))
            pygame.draw.rect(surf, (80, 80, 100), (wx - 15, wy - 38, 30, 2))

        elif self.current_weapon == 6:  # BFG / Presidential Strike
            # Massive body
            pygame.draw.rect(surf, (25, 45, 25), (wx - 22, wy - 25, 44, 38))
            pygame.draw.rect(surf, (35, 60, 35), (wx - 20, wy - 25, 6, 38))  # Side highlight
            # Main chamber
            pygame.draw.rect(surf, (35, 75, 35), (wx - 18, wy - 70, 36, 48))
            pygame.draw.rect(surf, (45, 95, 45), (wx - 18, wy - 70, 36, 4))  # Top highlight
            # Barrel array (3 barrels)
            for bx in [-8, 0, 8]:
                pygame.draw.rect(surf, col, (wx + bx - 3, wy - 84, 6, 16))
                pygame.draw.circle(surf, (0, 0, 0), (wx + bx, wy - 84), 2)  # Bores
            # Giant pulsing energy core
            pulse = math.sin(self.sim_time * 6)
            glow_r = int(10 + pulse * 4)
            glow_surf = pygame.Surface((glow_r * 4, glow_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 255, 0, 40), (glow_r * 2, glow_r * 2), glow_r * 2)
            pygame.draw.circle(glow_surf, (50, 255, 50, 80), (glow_r * 2, glow_r * 2), glow_r)
            surf.blit(glow_surf, (wx - glow_r * 2, wy - 90 - glow_r * 2))
            pygame.draw.circle(surf, (100, 255, 100), (wx, wy - 90), glow_r // 2)
            pygame.draw.circle(surf, (200, 255, 200), (wx, wy - 90), 3)

        # Muzzle flash (enhanced)
        if self.weapon_fired > 0.5:
            flash_intensity = self.weapon_fired
            flash_r = int(flash_intensity * 30)
            # Outer glow
            flash_surf = pygame.Surface((flash_r * 4, flash_r * 4), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 200, 50, 80), (flash_r * 2, flash_r * 2), flash_r * 2)
            pygame.draw.circle(flash_surf, (255, 255, 150, 150), (flash_r * 2, flash_r * 2), flash_r)
            surf.blit(flash_surf, (wx - flash_r * 2, wy - 90 - flash_r * 2))
            # Core flash
            pygame.draw.circle(surf, col, (wx, wy - 88), flash_r)
            pygame.draw.circle(surf, (255, 255, 255), (wx, wy - 88), flash_r // 2)

    # ═══════════════════════════════════════════════
    #  HUD RENDERING (Doom-style Status Bar)
    # ═══════════════════════════════════════════════
    def render_hud(self, surf):
        w, h = surf.get_size()

        # ── Wanted Level ──
        if self.wanted_level > 0:
            star_txt = self.font_hud.render("WANTED:", True, (255, 100, 100))
            surf.blit(star_txt, (w - 150, 10))
            for idx in range(self.wanted_level):
                sx = w - 90 + idx * 16
                sy = 16
                # Draw simple 5-point star
                pygame.draw.polygon(surf, (255, 200, 50), [
                    (sx, sy - 6), (sx + 2, sy - 2), (sx + 6, sy - 2),
                    (sx + 3, sy + 1), (sx + 4, sy + 5), (sx, sy + 3),
                    (sx - 4, sy + 5), (sx - 3, sy + 1), (sx - 6, sy - 2),
                    (sx - 2, sy - 2)
                ])

        # ── Crosshair ──
        cx, cy = w // 2, h // 2
        gap = 4
        size = 8
        col = (255, 255, 255) if self.crosshair_hit <= 0 else (255, 80, 80)
        if self.berserk_timer > 0:
            col = (255, 0, 0)
        pygame.draw.line(surf, col, (cx - size, cy), (cx - gap, cy), 2)
        pygame.draw.line(surf, col, (cx + gap, cy), (cx + size, cy), 2)
        pygame.draw.line(surf, col, (cx, cy - size), (cx, cy - gap), 2)
        pygame.draw.line(surf, col, (cx, cy + gap), (cx, cy + size), 2)

        # ── Doom-style status bar ──
        bar_h = 58
        bar_surf = pygame.Surface((w, bar_h), pygame.SRCALPHA)
        bar_surf.fill((20, 20, 22, 230))
        # Top border
        pygame.draw.line(bar_surf, (80, 80, 80), (0, 0), (w, 0), 2)
        surf.blit(bar_surf, (0, h - bar_h))

        base_y = h - bar_h + 4

        # ── AMMO section (left) ──
        ammo_label = self.font_hud_sm.render("AMMO", True, (120, 120, 120))
        surf.blit(ammo_label, (12, base_y))
        weap = WEAPONS[self.current_weapon]
        if weap['ammo_type'] and not getattr(self, 'cheat_mode', False):
            ammo_val = str(self.ammo.get(weap['ammo_type'], 0))
        else:
            ammo_val = "∞"
        ammo_txt = self.font_doom_sm.render(ammo_val, True, COL_ORANGE)
        surf.blit(ammo_txt, (12, base_y + 14))

        # ── HEALTH section (center-left) ──
        hp_label = self.font_hud_sm.render("HEALTH", True, (120, 120, 120))
        surf.blit(hp_label, (w // 4, base_y))

        hp_col = COL_RED if self.player_health < 25 else COL_ORANGE if self.player_health < 50 else COL_GREEN
        hp_txt = self.font_doom_sm.render(f"{max(0, self.player_health)}%", True, hp_col)
        surf.blit(hp_txt, (w // 4, base_y + 14))

        # Health bar
        hp_bar_w = 100
        hp_bar_x = w // 4
        hp_bar_y = base_y + 38
        pygame.draw.rect(surf, (40, 0, 0), (hp_bar_x, hp_bar_y, hp_bar_w, 8))
        fill = int(hp_bar_w * max(0, self.player_health) / 100)
        pygame.draw.rect(surf, hp_col, (hp_bar_x, hp_bar_y, fill, 8))

        # ── FACE (center) — Doom status face approximation ──
        face_x = w // 2 - 20
        face_y = base_y + 6
        face_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        # Background
        pygame.draw.rect(face_surf, (80, 80, 80), (0, 0, 40, 40))
        # Face
        pygame.draw.circle(face_surf, (240, 200, 160), (20, 20), 14)
        # Eyes — angrier as health drops
        if self.player_health > 60:
            pygame.draw.circle(face_surf, (40, 40, 40), (14, 17), 3)
            pygame.draw.circle(face_surf, (40, 40, 40), (26, 17), 3)
            # Mouth — slight grin
            pygame.draw.arc(face_surf, (40, 40, 40), (12, 22, 16, 8), 3.14, 6.28, 2)
        elif self.player_health > 30:
            pygame.draw.circle(face_surf, (60, 30, 30), (14, 17), 3)
            pygame.draw.circle(face_surf, (60, 30, 30), (26, 17), 3)
            # Grimace
            pygame.draw.line(face_surf, (40, 40, 40), (14, 28), (26, 28), 2)
        else:
            pygame.draw.circle(face_surf, (160, 30, 30), (14, 17), 3)
            pygame.draw.circle(face_surf, (160, 30, 30), (26, 17), 3)
            # Bloody
            pygame.draw.circle(face_surf, (180, 0, 0), (18, 12), 2)
            pygame.draw.line(face_surf, (40, 40, 40), (14, 26), (26, 30), 2)

        if self.damage_flash > 0:
            pain_tint = pygame.Surface((40, 40), pygame.SRCALPHA)
            pain_tint.fill((255, 0, 0, int(self.damage_flash * 150)))
            face_surf.blit(pain_tint, (0, 0))

        if self.berserk_timer > 0:
            berserk_tint = pygame.Surface((40, 40), pygame.SRCALPHA)
            berserk_tint.fill((255, 0, 0, 60))
            face_surf.blit(berserk_tint, (0, 0))

        surf.blit(face_surf, (face_x, face_y))

        # ── ARMOR section (center-right) ──
        ar_label = self.font_hud_sm.render("ARMOR", True, (120, 120, 120))
        surf.blit(ar_label, (3 * w // 4 - 40, base_y))
        ar_txt = self.font_doom_sm.render(f"{max(0, self.player_armor)}%", True, COL_BLUE)
        surf.blit(ar_txt, (3 * w // 4 - 40, base_y + 14))

        # Armor bar
        ar_bar_x = 3 * w // 4 - 40
        pygame.draw.rect(surf, (0, 0, 40), (ar_bar_x, base_y + 38, 100, 8))
        ar_fill = int(100 * max(0, self.player_armor) / 200)
        pygame.draw.rect(surf, COL_BLUE, (ar_bar_x, base_y + 38, ar_fill, 8))

        # ── WEAPON NAME (right) ──
        weap_name = self.font_hud_sm.render(weap['name'], True, (200, 200, 200))
        surf.blit(weap_name, (w - weap_name.get_width() - 10, base_y))

        # Weapon slots
        for i in range(7):
            if self.weapons_owned.get(i, False):
                slot_col = COL_YELLOW if i == self.current_weapon else (80, 80, 80)
                slot_txt = self.font_console.render(str(i + 1), True, slot_col)
                surf.blit(slot_txt, (w - 10 - (7 - i) * 14, base_y + 16))

        # Money
        money_str = f"${self.player_money:,}"
        money_txt = self.font_hud_sm.render(money_str, True, COL_GREEN)
        surf.blit(money_txt, (w - money_txt.get_width() - 10, base_y + 32))

        # ── Top bar ──
        top_surf = pygame.Surface((w, 22), pygame.SRCALPHA)
        top_surf.fill((0, 0, 0, 140))
        surf.blit(top_surf, (0, 0))

        sv_txt = self.font_console.render(
            f"TBMG_Country — DOOM [DarkRP v2.4.3] | sv_cheats 1 | tick 35 | sim: {self.sim_time:.1f} | kills: {self.kills}",
            True, (80, 80, 80)
        )
        surf.blit(sv_txt, (6, 4))

        pc_txt = self.font_console.render("64/64", True, COL_ORANGE)
        surf.blit(pc_txt, (w - pc_txt.get_width() - 10, 4))

        # Noclip
        if self.noclip:
            nc_txt = self.font_hud.render("[ NOCLIP — sv_cheats 1 ]", True, (200, 100, 255))
            surf.blit(nc_txt, (w // 2 - nc_txt.get_width() // 2, 26))

        # Invulnerability
        if self.invuln_timer > 0:
            inv_txt = self.font_hud.render(f"[ INVULNERABLE — {self.invuln_timer:.0f}s ]", True, (255, 255, 255))
            surf.blit(inv_txt, (w // 2 - inv_txt.get_width() // 2, 44))

        # Berserk
        if self.berserk_timer > 0:
            ber_txt = self.font_hud.render("[ BERSERK ]", True, (255, 0, 0))
            surf.blit(ber_txt, (w // 2 - ber_txt.get_width() // 2, self.noclip and 62 or 26))

        # Key hints
        hints = ["[F1] Admin", "[TAB] Map", "[E] Door", "[1-7] Weapons", "[WASD] Move"]
        for i, h_text in enumerate(hints):
            ht = self.font_console.render(h_text, True, (50, 50, 50))
            surf.blit(ht, (w - ht.get_width() - 10, 18 + i * 11))

        # ── Console log ──
        log_y = h - 75
        for entry in reversed(self.console_log[-8:]):
            if entry['age'] > 8:
                continue
            alpha = max(0, 1 - entry['age'] / 8)
            colors = {
                'error': (255, 60, 60), 'warn': (255, 200, 0),
                'info': (100, 255, 100), 'sys': (120, 180, 255),
                'admin': (255, 120, 255),
            }
            col = colors.get(entry['level'], (180, 180, 180))
            col = tuple(int(c * alpha) for c in col)
            line = self.font_console.render(f"[{entry['time']:.1f}] {entry['msg']}", True, col)
            surf.blit(line, (6, log_y))
            log_y -= 11

        # ── Damage flash ──
        if self.damage_flash > 0:
            flash_surf = pygame.Surface((w, h), pygame.SRCALPHA)
            flash_surf.fill((255, 0, 0, int(self.damage_flash * 100)))
            surf.blit(flash_surf, (0, 0))

    # ═══════════════════════════════════════════════
    #  AUTOMAP (TAB)
    # ═══════════════════════════════════════════════
    def render_automap(self, surf):
        w, h = surf.get_size()

        # Dark overlay
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        surf.blit(overlay, (0, 0))

        # Scale to fit screen
        scale = min((w - 40) / MAP_W, (h - 100) / MAP_H)
        ox = (w - MAP_W * scale) // 2
        oy = (h - MAP_H * scale) // 2

        # Draw map
        for y in range(MAP_H):
            for x in range(MAP_W):
                rx = ox + x * scale
                ry = oy + y * scale
                if MAP[y][x] != 0:
                    colors = {
                        1: (60, 60, 65), 2: (50, 15, 80), 3: (20, 30, 70),
                        4: (70, 30, 15), 5: (55, 50, 30), 6: (50, 180, 50),
                        7: (255, 0, 255), 8: (180, 0, 0), 9: (20, 20, 40),
                        10: (70, 75, 80), 11: (20, 50, 25),
                    }
                    c = colors.get(MAP[y][x], (40, 40, 40))
                    pygame.draw.rect(surf, c, (rx, ry, scale, scale))
                else:
                    pygame.draw.rect(surf, (15, 15, 20), (rx, ry, scale, scale))

        # Entities
        type_colors = {
            'civilian': (130, 170, 255), 'mcpd': (60, 60, 255), 'ecpu': (136, 0, 255),
            'rpg': (255, 70, 0), 'imp': (255, 180, 0), 'demon': (255, 80, 120),
            'charger': (255, 68, 204), 'pillow': (255, 170, 255),
        }
        for e in self.entities:
            if not e.alive:
                continue
            c = type_colors.get(e.type, (255, 255, 255))
            px = ox + e.x * scale
            py = oy + e.y * scale
            pygame.draw.circle(surf, c, (int(px), int(py)), max(2, int(scale * 0.3)))

        # Pickups
        for p in self.pickups:
            if not p.alive:
                continue
            px = ox + p.x * scale
            py = oy + p.y * scale
            pygame.draw.circle(surf, COL_YELLOW, (int(px), int(py)), max(2, int(scale * 0.2)))

        # Player
        ppx = ox + self.player_x * scale
        ppy = oy + self.player_y * scale
        pygame.draw.circle(surf, COL_GREEN, (int(ppx), int(ppy)), max(3, int(scale * 0.4)))
        # Direction
        dx = math.cos(self.player_angle) * scale * 2
        dy = math.sin(self.player_angle) * scale * 2
        pygame.draw.line(surf, COL_GREEN, (int(ppx), int(ppy)), (int(ppx + dx), int(ppy + dy)), 2)

        # Title
        title = self.font_hud.render("AUTOMAP — TBMG_Country_MainCity2", True, (150, 150, 150))
        surf.blit(title, (w // 2 - title.get_width() // 2, 10))

        # Legend
        legend_y = h - 30
        legend_items = [
            ("Civilian", (130, 170, 255)), ("MCPD", (60, 60, 255)), ("ECPU", (136, 0, 255)),
            ("RPG", (255, 70, 0)), ("Imp", (255, 180, 0)), ("Demon", (255, 80, 120)),
        ]
        lx = 10
        for name, col in legend_items:
            pygame.draw.circle(surf, col, (lx + 5, legend_y + 5), 4)
            txt = self.font_console.render(name, True, (120, 120, 120))
            surf.blit(txt, (lx + 12, legend_y))
            lx += txt.get_width() + 22

    # ═══════════════════════════════════════════════
    #  MINIMAP (corner)
    # ═══════════════════════════════════════════════
    def render_minimap(self, surf):
        mm_w, mm_h = 120, 90
        mm_x = surf.get_width() - mm_w - 10
        mm_y = 70

        mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)
        mm_surf.fill((0, 0, 0, 150))

        sx = mm_w / MAP_W
        sy = mm_h / MAP_H

        for y in range(MAP_H):
            for x in range(MAP_W):
                if MAP[y][x] != 0:
                    zone_colors = {
                        1: (60, 60, 65), 2: (50, 15, 80), 3: (20, 30, 70),
                        4: (70, 30, 15), 5: (55, 50, 30), 6: (50, 55, 60),
                        7: (255, 0, 255), 8: (180, 0, 0), 9: (20, 20, 40),
                        10: (70, 75, 80), 11: (20, 50, 25),
                    }
                    c = zone_colors.get(MAP[y][x], (40, 40, 40))
                    pygame.draw.rect(mm_surf, c, (int(x * sx), int(y * sy), max(1, int(sx) + 1), max(1, int(sy) + 1)))

        type_colors = {
            'civilian': (130, 170, 255), 'mcpd': (60, 60, 255), 'ecpu': (136, 0, 255),
            'rpg': (255, 70, 0), 'imp': (255, 180, 0), 'demon': (255, 80, 120),
            'charger': (255, 68, 204), 'pillow': (255, 170, 255),
        }
        for e in self.entities:
            if not e.alive:
                continue
            c = type_colors.get(e.type, (255, 255, 255))
            px = int(e.x * sx)
            py = int(e.y * sy)
            mm_surf.set_at((min(px, mm_w - 1), min(py, mm_h - 1)), c)

        ppx = int(self.player_x * sx)
        ppy = int(self.player_y * sy)
        pygame.draw.circle(mm_surf, COL_GREEN, (ppx, ppy), 2)
        dx = math.cos(self.player_angle) * 6
        dy = math.sin(self.player_angle) * 6
        pygame.draw.line(mm_surf, COL_GREEN, (ppx, ppy), (ppx + int(dx), ppy + int(dy)), 1)

        surf.blit(mm_surf, (mm_x, mm_y))
        label = self.font_console.render("MAP", True, (60, 60, 60))
        surf.blit(label, (mm_x + mm_w // 2 - label.get_width() // 2, mm_y + mm_h + 2))

    # ═══════════════════════════════════════════════
    #  ADMIN PANEL
    # ═══════════════════════════════════════════════
    def render_admin(self, surf):
        if not self.admin_open:
            return

        w, h = surf.get_size()
        panel_w, panel_h = 420, 440
        px = w // 2 - panel_w // 2
        py = h // 2 - panel_h // 2

        panel_surf = pygame.Surface((panel_w, panel_h), pygame.SRCALPHA)
        panel_surf.fill((8, 8, 14, 240))
        pygame.draw.rect(panel_surf, (180, 0, 255, 120), (0, 0, panel_w, panel_h), 1)
        surf.blit(panel_surf, (px, py))

        header = pygame.Surface((panel_w, 28), pygame.SRCALPHA)
        header.fill((80, 0, 140, 120))
        surf.blit(header, (px, py))
        title = self.font_admin.render("PRESIDENT MICHAEL — EXECUTIVE TERMINAL [DOOM]", True, (200, 130, 255))
        surf.blit(title, (px + 10, py + 6))

        mouse_pos = pygame.mouse.get_pos()
        for i, (label, _) in enumerate(self.admin_items):
            iy = py + 38 + i * 24
            rect = pygame.Rect(px + 10, iy, panel_w - 20, 20)

            hovered = rect.collidepoint(mouse_pos)
            bg_col = (255, 140, 0, 50) if hovered else (255, 255, 255, 10)

            btn_surf = pygame.Surface((rect.w, rect.h), pygame.SRCALPHA)
            btn_surf.fill(bg_col)
            surf.blit(btn_surf, rect.topleft)

            if 'CRASH' in label or 'Kill' in label:
                col = COL_RED
            elif 'Dark Leader' in label or 'Noclip' in label or 'Burst' in label or 'Give' in label:
                col = (220, 130, 255)
            elif 'Charger' in label or 'Pillow' in label:
                col = COL_PINK
            elif 'Imp' in label or 'Demon' in label:
                col = (255, 180, 0)
            else:
                col = (200, 200, 200)

            txt = self.font_admin.render(label, True, col)
            surf.blit(txt, (rect.x + 8, rect.y + 3))

    # ═══════════════════════════════════════════════
    #  TITLE SCREEN
    # ═══════════════════════════════════════════════
    def render_title(self, surf):
        w, h = surf.get_size()
        surf.fill((0, 0, 0))

        # Animated background lines
        for i in range(20):
            y = (i * 40 + int(self.title_timer * 30)) % h
            alpha = 20 + int(math.sin(self.title_timer + i) * 10)
            pygame.draw.line(surf, (alpha, 0, 0), (0, y), (w, y), 1)

        # Title
        title1 = self.font_doom.render("TBMG COUNTRY", True, COL_RED)
        surf.blit(title1, (w // 2 - title1.get_width() // 2, h // 5))

        title2 = self.font_doom.render("D O O M", True, (255, 80, 0))
        surf.blit(title2, (w // 2 - title2.get_width() // 2, h // 5 + 50))

        # Subtitle
        sub = self.font_doom_sm.render("MainCity2 — DarkRP Edition", True, (180, 180, 180))
        surf.blit(sub, (w // 2 - sub.get_width() // 2, h // 5 + 100))

        # Menu items
        menu = ["New Game (Cheat Mode)", "New Game (Survival Mode)", "Quit"]
        for i, item in enumerate(menu):
            col = COL_ORANGE if i == self.title_selection else (120, 120, 120)
            prefix = "▶ " if i == self.title_selection else "  "
            txt = self.font_doom_sm.render(prefix + item, True, col)
            surf.blit(txt, (w // 2 - txt.get_width() // 2, h // 2 + 40 + i * 35))

        # Info
        info_lines = [
            "sv_cheats 1 | Build 6660 | Instability: HELLISH",
            "7 Weapons · Doom AI · Doors · Pickups · Automap",
            "Factions: MCPD · ECPU · RPG Gang · Imps · Demons",
        ]
        for i, line in enumerate(info_lines):
            txt = self.font_console.render(line, True, (60, 60, 60))
            surf.blit(txt, (w // 2 - txt.get_width() // 2, h - 60 + i * 14))

        # Blink prompt
        if int(self.title_timer * 2) % 2:
            prompt = self.font_hud_sm.render("Press ENTER to begin", True, (100, 100, 100))
            surf.blit(prompt, (w // 2 - prompt.get_width() // 2, h // 2 + 120))

    # ═══════════════════════════════════════════════
    #  LOADING SCREEN
    # ═══════════════════════════════════════════════
    def render_loading(self, surf):
        w, h = surf.get_size()
        surf.fill((0, 0, 0))

        logo = self.font_hud_sm.render("TBMG engine — dedicated server build 6660", True, (40, 40, 40))
        surf.blit(logo, (w // 2 - logo.get_width() // 2, h // 3 - 40))

        title = self.font_title.render("TBMG_Country_MainCity2", True, COL_WHITE)
        surf.blit(title, (w // 2 - title.get_width() // 2, h // 3))

        sub = self.font_hud_sm.render("doom mode | sv_cheats 1 | instability: HELLISH", True, (100, 100, 100))
        surf.blit(sub, (w // 2 - sub.get_width() // 2, h // 3 + 35))

        bar_w, bar_h = 320, 6
        bx = w // 2 - bar_w // 2
        by = h // 2 + 30
        pygame.draw.rect(surf, (30, 30, 30), (bx, by, bar_w, bar_h))
        fill_w = int(bar_w * self.loading_progress / 100)
        pygame.draw.rect(surf, COL_ORANGE, (bx, by, fill_w, bar_h))

        msg = self.font_hud_sm.render(self.loading_msg, True, (140, 140, 140))
        surf.blit(msg, (w // 2 - msg.get_width() // 2, by + 16))

    # ═══════════════════════════════════════════════
    #  CRASH SCREEN
    # ═══════════════════════════════════════════════
    def render_crash(self, surf):
        w, h = surf.get_size()
        surf.fill((0, 0, 0))

        title = self.font_large.render("SERVER CRASH DETECTED", True, COL_RED)
        surf.blit(title, (w // 2 - title.get_width() // 2, h // 3))

        lines = [
            f"Segmentation fault — {self.crash_reason}",
            "Heap overflow at engine/doom_bridge.cpp:666",
            "Connected clients: 64 → 0",
            "Server will reboot automatically..."
        ]
        for i, line in enumerate(lines):
            txt = self.font_hud_sm.render(line, True, (100, 100, 100))
            surf.blit(txt, (w // 2 - txt.get_width() // 2, h // 3 + 40 + i * 18))

        bar_w = 200
        bx = w // 2 - bar_w // 2
        by = h // 3 + 130
        pygame.draw.rect(surf, (30, 30, 30), (bx, by, bar_w, 4))
        fill = int(bar_w * self.crash_progress / 100)
        pygame.draw.rect(surf, COL_RED, (bx, by, fill, 4))

    # ═══════════════════════════════════════════════
    #  RANDOM CONSOLE MESSAGES
    # ═══════════════════════════════════════════════
    RANDOM_MSGS = [
        ('warn', 'prop_physics clipping through world geometry'),
        ('error', 'SteamNetworking: timeout client 47'),
        ('info', 'DarkRP: Money printer overheated — $500 fine'),
        ('sys', 'Doom: linedef overflow (instability detected)'),
        ('warn', 'WAD: texture lookup failed — ERROR mesh rendered'),
        ('sys', 'MCPD quota met — 3 civilians fined for "existing"'),
        ('error', 'lua error: nil value in darkrp_jobs (line 666)'),
        ('info', 'DarkRP: "xXshadowkill3rXx" rocket-jumping detected'),
        ('warn', 'ECPU lost radio — reestablishing authority'),
        ('sys', 'sv_cheats 1: executive command accepted'),
        ('error', 'ERROR: missing model imp_fireball_corrupted.mdl'),
        ('info', 'Ammo Shift: item_ammo_smg1 removed from pool'),
        ('warn', 'Demon pathfinding stuck — A* overflow'),
        ('sys', 'Visplane overflow — DOOM rendering degraded'),
    ]

    # ═══════════════════════════════════════════════
    #  UPDATE LOOP
    # ═══════════════════════════════════════════════
    def update(self, dt):
        # ── Loading state ──
        if self.is_loading:
            self.loading_progress += dt * 35
            steps = [
                (15, "Initializing WAD lumps..."),
                (30, "Precaching sprites..."),
                (45, "Building BSP tree..."),
                (60, "Spawning things..."),
                (75, "Generating visplanes..."),
                (85, "Linking linedef triggers..."),
                (95, "Connecting to server..."),
                (100, "Server ready."),
            ]
            for threshold, msg in steps:
                if self.loading_progress < threshold:
                    self.loading_msg = msg
                    break
            if self.loading_progress >= 100:
                self.is_loading = False
                if not self.entities:
                    self.populate_world()
                self.add_log('info', 'Map loaded successfully — DOOM mode active')
            return

        # ── Crash state ──
        if self.is_crashed:
            self.crash_progress += dt * 20
            if self.crash_progress >= 100:
                self.is_crashed = False
                self.entities = [e for e in self.entities if e.alive and e.type not in ('charger', 'pillow')]
                self.add_log('sys', 'Server reboot complete. Props purged.')
            return

        self.sim_time += dt

        # Timers
        if self.weapon_fired > 0:
            self.weapon_fired -= dt * 5
        if self.weapon_cooldown > 0:
            self.weapon_cooldown -= dt
        if self.screen_shake > 0:
            self.screen_shake -= dt * 2
        if self.crosshair_hit > 0:
            self.crosshair_hit -= dt * 4
        if self.damage_flash > 0:
            self.damage_flash -= dt * 3
        if self.berserk_timer > 0:
            self.berserk_timer -= dt
        if self.invuln_timer > 0:
            self.invuln_timer -= dt
        if self.weapon_switch_timer > 0:
            self.weapon_switch_timer -= dt

        # ── Player movement ──
        keys = pygame.key.get_pressed()
        speed = SPRINT_SPEED if keys[pygame.K_LSHIFT] else MOVE_SPEED

        dx, dy = 0, 0
        if keys[pygame.K_w]:
            dx += math.cos(self.player_angle) * speed * dt
            dy += math.sin(self.player_angle) * speed * dt
        if keys[pygame.K_s]:
            dx -= math.cos(self.player_angle) * speed * dt
            dy -= math.sin(self.player_angle) * speed * dt
        if keys[pygame.K_a]:
            dx += math.cos(self.player_angle - math.pi / 2) * speed * dt
            dy += math.sin(self.player_angle - math.pi / 2) * speed * dt
        if keys[pygame.K_d]:
            dx += math.cos(self.player_angle + math.pi / 2) * speed * dt
            dy += math.sin(self.player_angle + math.pi / 2) * speed * dt

        # Footsteps
        if abs(dx) + abs(dy) > 0.01:
            self.step_timer += dt
            if self.step_timer > 0.4:
                self.step_timer = 0
                self.snd_footstep.play()

        # Wall collision with margin to prevent texture warping
        MARGIN = 0.25
        if self.noclip:
            self.player_x += dx
            self.player_y += dy
        else:
            nx = self.player_x + dx
            ny = self.player_y + dy

            # X-axis collision with margin
            def is_wall(cx, cy):
                ix, iy = int(cx), int(cy)
                if ix < 0 or ix >= MAP_W or iy < 0 or iy >= MAP_H:
                    return True
                cell = MAP[iy][ix]
                if cell == 0:
                    return False
                if cell == 6 and self.is_door_open(iy, ix):
                    return False
                return True

            # Check X movement with margin probes
            sign_x = 1 if dx > 0 else -1
            probe_x = nx + sign_x * MARGIN
            if not is_wall(probe_x, self.player_y) and not is_wall(probe_x, self.player_y + MARGIN) and not is_wall(probe_x, self.player_y - MARGIN):
                self.player_x = nx

            # Check Y movement with margin probes
            sign_y = 1 if dy > 0 else -1
            probe_y = ny + sign_y * MARGIN
            if not is_wall(self.player_x, probe_y) and not is_wall(self.player_x + MARGIN, probe_y) and not is_wall(self.player_x - MARGIN, probe_y):
                self.player_y = ny

        # ── Update doors ──
        self.update_doors(dt)

        # ── Check weapon pickups ──
        for i, (wx, wy, wid, wname) in enumerate(self.weapon_pickup_positions):
            if not self.weapon_pickups_alive[i]:
                continue
            d = math.sqrt((self.player_x - wx) ** 2 + (self.player_y - wy) ** 2)
            if d < 1.0:
                if not self.weapons_owned.get(wid, False):
                    self.weapons_owned[wid] = True
                    self.current_weapon = wid
                    self.weapon_pickups_alive[i] = False
                    self.play_pickup()
                    self.add_log('info', f'Picked up {wname}!')
                    # Give starting ammo for weapon
                    atype = WEAPONS[wid]['ammo_type']
                    if atype:
                        self.ammo[atype] = self.ammo.get(atype, 0) + WEAPONS[wid]['ammo_use'] * 10
                elif self.weapons_owned.get(wid, False):
                    # Already have it, give ammo
                    atype = WEAPONS[wid]['ammo_type']
                    if atype and self.ammo.get(atype, 0) < self.ammo_max.get(atype, 999):
                        self.ammo[atype] = min(self.ammo_max[atype], self.ammo.get(atype, 0) + WEAPONS[wid]['ammo_use'] * 5)
                        self.weapon_pickups_alive[i] = False
                        self.play_pickup()

        # ── Update entities ──
        for e in self.entities:
            if e.alive:
                e.update(dt, self)
        self.entities = [e for e in self.entities if e.alive]

        # ── Update projectiles ──
        for p in self.projectiles:
            if p.alive:
                p.update(dt, self)
        self.projectiles = [p for p in self.projectiles if p.alive]

        # ── Update explosions ──
        for ex in self.explosions_list:
            if ex.alive:
                ex.update(dt)
        self.explosions_list = [ex for ex in self.explosions_list if ex.alive]

        # ── Update pickups ──
        for p in self.pickups:
            if p.alive:
                p.update(dt, self)
        self.pickups = [p for p in self.pickups if p.alive]

        # ── Age corpses ──
        for c in self.corpses:
            c['age'] += dt
        self.corpses = [c for c in self.corpses if c['age'] < 30]

        # ── Physics collisions ──
        for i in range(len(self.entities)):
            if not self.entities[i].alive:
                continue
            for j in range(i + 1, len(self.entities)):
                if not self.entities[j].alive:
                    continue
                a, b = self.entities[i], self.entities[j]
                d = math.sqrt((a.x - b.x) ** 2 + (a.y - b.y) ** 2)
                if d < 0.8:
                    nx = (b.x - a.x) / (d or 0.1)
                    ny = (b.y - a.y) / (d or 0.1)
                    spike = 3 + (0.8 - d) * 4
                    a.vx -= nx * spike
                    a.vy -= ny * spike
                    b.vx += nx * spike
                    b.vy += ny * spike
                    if random.random() < 0.1:
                        self._play_spatial(self.snd_metal, a.x, a.y)

        # ── Wanted Level Decay ──
        if self.wanted_level > 0:
            # Check if player is visible to any MCPD/ECPU/Military
            player_visible = False
            for e in self.entities:
                if e.alive and e.type in ('mcpd', 'ecpu', 'military') and getattr(e, 'see_player', False):
                    player_visible = True
                    break
            
            if player_visible:
                self.wanted_decay_timer = 10.0
            else:
                self.wanted_decay_timer -= dt
                if self.wanted_decay_timer <= 0:
                    self.wanted_level -= 1
                    self.wanted_decay_timer = 10.0
                    if self.wanted_level > 0:
                        self.add_log('sys', f'[WANTED] Heat decreasing... ({self.wanted_level} stars)')
                    else:
                        self.add_log('sys', '[WANTED] Evaded. Law enforcement standing down.')
                        # Reset cop aggro if they were just chasing
                        for e in self.entities:
                            if e.alive and e.type in ('mcpd', 'ecpu', 'military') and e.ai_state == AI_CHASE:
                                e.ai_state = AI_IDLE

        # ── MCPD Respawn Queue ──
        new_q = []
        for entry in self.mcpd_respawn_queue:
            entry['timer'] -= dt
            if entry['timer'] <= 0:
                zones = [(11.5, 19.5), (12.0, 20.5), (5.5, 8.5), (8.5, 4.5),
                         (14.5, 9.5), (5.5, 26.5), (15.5, 28.5)]
                spawned = False
                for _ in range(10):
                    pos = random.choice(zones)
                    sx = pos[0] + random.uniform(-1, 1)
                    sy = pos[1] + random.uniform(-1, 1)
                    if (0 <= int(sy) < MAP_H and 0 <= int(sx) < MAP_W
                            and MAP[int(sy)][int(sx)] == 0):
                        new_unit = MCPDUnit(sx, sy, entry['sprite'])
                        new_unit.ai_state = AI_CHASE
                        tgt = self.find_nearest_hostile(sx, sy, ['imp', 'demon', 'rpg'])
                        if tgt:
                            new_unit.last_known_px = tgt.x
                            new_unit.last_known_py = tgt.y
                        self.entities.append(new_unit)
                        self.add_log('sys', '[MCPD DISPATCH] Officer returned to duty — engaging threats')
                        spawned = True
                        break
                if not spawned:
                    entry['timer'] = 5.0   # retry in 5 s
                    new_q.append(entry)
            else:
                new_q.append(entry)
        self.mcpd_respawn_queue = new_q

        # ── Random spawns ──

        # RPG Ganger respawns
        if random.random() < 0.003 and sum(1 for e in self.entities if e.type == 'rpg') < 6:
            sx = random.uniform(16.5, 21.5)
            sy = random.uniform(13.5, 16.5)
            if MAP[int(sy)][int(sx)] == 0:
                self.entities.append(RPGGanger(sx, sy, self.sprite_rpg))
                self.add_log('sys', '[RPG GANG] Reinforcements from Depot')

        # Civilian respawns (wider area)
        if random.random() < 0.003 and sum(1 for e in self.entities if e.type == 'civilian') < 12:
            zones = [(2, 5, 2, 5), (7, 12, 7, 11), (1, 5, 7, 10)]
            zone = random.choice(zones)
            sx = random.uniform(zone[0], zone[1])
            sy = random.uniform(zone[2], zone[3])
            if 0 <= int(sy) < MAP_H and 0 <= int(sx) < MAP_W and MAP[int(sy)][int(sx)] == 0:
                self.entities.append(Civilian(sx, sy, self.sprite_civilian))

        # MCPD reinforcements — spawn frequently to keep the city defended
        if random.random() < 0.008 and sum(1 for e in self.entities if e.type == 'mcpd') < 12:
            mcpd_zones = [(11.5, 19.5), (12.0, 20.5), (5.5, 8.5), (8.5, 4.5), (14.5, 9.5), (5.5, 26.5), (15.5, 28.5)]
            pos = random.choice(mcpd_zones)
            sx, sy = pos[0] + random.uniform(-1, 1), pos[1] + random.uniform(-1, 1)
            if 0 <= int(sy) < MAP_H and 0 <= int(sx) < MAP_W and MAP[int(sy)][int(sx)] == 0:
                self.entities.append(MCPDUnit(sx, sy, self.sprite_mcpd))
                self.add_log('sys', '[MCPD DISPATCH] Officer deployed to patrol')

        # === MONSTER SPAWNER ZONES ===
        # Imps — corrupted east sector + new far-east cave + monster den
        if random.random() < 0.008 and sum(1 for e in self.entities if e.type == 'imp') < 16:
            spawn_area = random.choice(['east', 'cave', 'den'])
            if spawn_area == 'east':
                sx = random.uniform(25, 31)
                sy = random.uniform(8, 22)
            elif spawn_area == 'cave':
                sx = random.uniform(33, 46)
                sy = random.uniform(8, 14)
            else:  # den
                sx = random.uniform(33, 46)
                sy = random.uniform(28, 38)
            if 0 <= int(sy) < MAP_H and 0 <= int(sx) < MAP_W and MAP[int(sy)][int(sx)] == 0:
                self.entities.append(ImpEntity(sx, sy, self.sprite_imp))
                self.add_log('error', '[CORRUPTION] Data entity materialized!')

        # Demons spawn from sewer/armory + new monster den
        if random.random() < 0.004 and sum(1 for e in self.entities if e.type == 'demon') < 10:
            spawn_area = random.choice(['armory', 'sewer', 'den'])
            if spawn_area == 'armory':
                sx = random.uniform(25, 30)
                sy = random.uniform(1.5, 5)
            elif spawn_area == 'sewer':
                sx = random.uniform(25, 31)
                sy = random.uniform(19, 22)
            else:  # den
                sx = random.uniform(33, 46)
                sy = random.uniform(30, 37)
            if 0 <= int(sy) < MAP_H and 0 <= int(sx) < MAP_W and MAP[int(sy)][int(sx)] == 0:
                self.entities.append(DemonEntity(sx, sy, self.sprite_demon))
                self.add_log('error', '[CORRUPTION] Server beast detected!')

        # ── Random console messages ──
        self.msg_timer += dt
        if self.msg_timer > 4 + random.random() * 3:
            self.msg_timer = 0
            msg = random.choice(Game.RANDOM_MSGS)
            self.add_log(msg[0], msg[1])

        # ── Age console entries ──
        for entry in self.console_log:
            entry['age'] += dt

        # ── Cheat mode auto-heal ──
        if self.cheat_mode:
            self.player_health = 100
            self.player_armor = 100

        # ── Auto-fire if holding mouse ──
        if pygame.mouse.get_pressed()[0] and not self.admin_open:
            self.fire_weapon()

    # ═══════════════════════════════════════════════
    #  MAIN LOOP
    # ═══════════════════════════════════════════════
    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)

            # ── Events ──
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

                elif event.type == pygame.KEYDOWN:
                    # ── Title screen ──
                    if self.game_state == self.STATE_TITLE:
                        if event.key == pygame.K_UP:
                            self.title_selection = max(0, self.title_selection - 1)
                        elif event.key == pygame.K_DOWN:
                            self.title_selection = min(2, self.title_selection + 1)
                        elif event.key == pygame.K_RETURN:
                            if self.title_selection in (0, 1):
                                self.cheat_mode = (self.title_selection == 0)
                                self.game_state = self.STATE_PLAYING
                                self.init_game()
                                pygame.mouse.set_visible(False)
                                pygame.event.set_grab(True)
                            else:
                                self.running = False
                        elif event.key == pygame.K_ESCAPE:
                            self.running = False
                        continue

                    # ── Playing ──
                    if event.key == pygame.K_ESCAPE:
                        if self.admin_open:
                            self.toggle_admin()
                        elif self.automap:
                            self.automap = False
                        else:
                            self.game_state = self.STATE_TITLE
                            pygame.mouse.set_visible(True)
                            pygame.event.set_grab(False)

                    elif event.key == pygame.K_F1:
                        self.toggle_admin()

                    elif event.key == pygame.K_TAB:
                        self.automap = not self.automap

                    elif event.key == pygame.K_e:
                        # Use key — open doors
                        self.check_nearby_doors()

                    elif event.key == pygame.K_F2:
                        self.trigger_loading("Maine HQ Sector 7")

                    elif event.key == pygame.K_r and not self.admin_open:
                        for e in self.entities:
                            if e.alive:
                                e.vx += random.uniform(-10, 10)
                                e.vy += random.uniform(-10, 10)
                        self.snd_metal.play()
                        self.screen_shake = 0.5
                        self.add_log('warn', '[PHYSICS] Global velocity spike injected')

                    # Weapon switching (1-7)
                    elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4, pygame.K_5, pygame.K_6, pygame.K_7):
                        slot = event.key - pygame.K_1
                        if self.weapons_owned.get(slot, False):
                            self.current_weapon = slot
                            self.weapon_switch_timer = 0.3

                elif event.type == pygame.MOUSEBUTTONDOWN and self.game_state == self.STATE_PLAYING:
                    if event.button == 1:
                        if self.admin_open:
                            mouse_pos = pygame.mouse.get_pos()
                            w, h = self.screen.get_size()
                            panel_w, panel_h = 420, 440
                            px = w // 2 - panel_w // 2
                            spy = h // 2 - panel_h // 2
                            for i, (label, action) in enumerate(self.admin_items):
                                rect = pygame.Rect(px + 10, spy + 38 + i * 24, panel_w - 20, 20)
                                if rect.collidepoint(mouse_pos):
                                    action()
                                    break
                        else:
                            self.fire_weapon()

                elif event.type == pygame.MOUSEMOTION and not self.admin_open and self.game_state == self.STATE_PLAYING:
                    mx, _ = event.rel
                    self.player_angle += mx * MOUSE_SENS

                # Mouse wheel weapon switch
                elif event.type == pygame.MOUSEWHEEL and self.game_state == self.STATE_PLAYING and not self.admin_open:
                    owned = sorted([k for k, v in self.weapons_owned.items() if v])
                    if owned:
                        idx = owned.index(self.current_weapon) if self.current_weapon in owned else 0
                        if event.y > 0:
                            idx = (idx + 1) % len(owned)
                        else:
                            idx = (idx - 1) % len(owned)
                        self.current_weapon = owned[idx]
                        self.weapon_switch_timer = 0.3

            # ── Title screen ──
            if self.game_state == self.STATE_TITLE:
                self.title_timer += dt
                self.render_title(self.screen)
                pygame.display.flip()
                continue

            # ── Update ──
            self.update(dt)

            # ── Render ──
            if self.is_loading:
                self.render_loading(self.screen)
            elif self.is_crashed:
                self.render_crash(self.screen)
            else:
                self.raycast()
                self.render_sprites()
                self.render_weapon(self.render_surf)

                shake_x = int(random.uniform(-3, 3) * self.screen_shake) if self.screen_shake > 0 else 0
                shake_y = int(random.uniform(-3, 3) * self.screen_shake) if self.screen_shake > 0 else 0

                scaled = pygame.transform.scale(self.render_surf, (SCREEN_W, SCREEN_H))
                self.screen.blit(scaled, (shake_x, shake_y))

                # HUD
                self.render_hud(self.screen)
                if not self.automap:
                    self.render_minimap(self.screen)
                else:
                    self.render_automap(self.screen)
                self.render_admin(self.screen)

            pygame.display.flip()

        pygame.quit()
        sys.exit()


# ═══════════════════════════════════════════════════
#  ENTRY POINT
# ═══════════════════════════════════════════════════
if __name__ == '__main__':
    game = Game()
    game.run()
