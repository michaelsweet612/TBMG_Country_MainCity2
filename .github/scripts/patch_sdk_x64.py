"""Patch an upstream ValveSoftware/source-sdk-2013 checkout for TBMG x64 builds."""

from __future__ import annotations

import pathlib
import sys


def replace_once(path: pathlib.Path, target: str, replacement: str) -> None:
    text = path.read_text(encoding="utf-8", errors="surrogateescape")
    # Handle CRLF checkouts identically to LF
    newline = "\r\n" if "\r\n" in text else "\n"
    t_norm = target.replace("\r\n", "\n").replace("\n", newline)
    r_norm = replacement.replace("\r\n", "\n").replace("\n", newline)
    if r_norm in text:
        return
    if t_norm not in text:
        raise RuntimeError(f"Target snippet not found in {path}:\n{target[:200]}")
    path.write_text(text.replace(t_norm, r_norm, 1), encoding="utf-8", errors="surrogateescape")


def patch_sdk(sdk_root: pathlib.Path) -> None:
    src = sdk_root / "src"

    # 1. Include Scout Buggy (hl2/vehicle_jeep.cpp & .h) in Server (HL2MP).
    # Client (HL2MP) already includes c_vehicle_jeep.cpp via client_base.vpc.
    replace_once(
        src / "game/server/server_hl2mp.vpc",
        '\t\t\t$File\t"hl2\\vehicle_airboat.cpp"',
        '\t\t\t$File\t"hl2\\vehicle_airboat.cpp"\n'
        '\t\t\t$File\t"hl2\\vehicle_jeep.cpp"\n'
        '\t\t\t$File\t"hl2\\vehicle_jeep.h"',
    )

    # 2. Expose canonical HL2 AI faction relationships & class names to HL2MP gamerules.
    replace_once(
        src / "game/shared/hl2/hl2_gamerules.h",
        "inline CHalfLife2* HL2GameRules()",
        "#ifndef CLIENT_DLL\n"
        "void HL2_InitDefaultAIRelationships( void );\n"
        "const char *HL2_AIClassText( int classType );\n"
        "#endif\n\n"
        "inline CHalfLife2* HL2GameRules()",
    )

    replace_once(
        src / "game/shared/hl2/hl2_gamerules.cpp",
        "\tvoid CHalfLife2::InitDefaultAIRelationships( void )\n\t{",
        "\tvoid HL2_InitDefaultAIRelationships( void )\n\t{",
    )

    replace_once(
        src / "game/shared/hl2/hl2_gamerules.cpp",
        "\tconst char* CHalfLife2::AIClassText(int classType)\n\t{",
        "\tvoid CHalfLife2::InitDefaultAIRelationships( void )\n"
        "\t{\n"
        "\t\tHL2_InitDefaultAIRelationships();\n"
        "\t}\n\n"
        "\tconst char* HL2_AIClassText(int classType)\n\t{",
    )

    replace_once(
        src / "game/shared/hl2/hl2_gamerules.cpp",
        '\t\t\tdefault:\t\t\t\t\treturn "MISSING CLASS in ClassifyText()";\n\t\t}\n\t}',
        '\t\t\tdefault:\t\t\t\t\treturn "MISSING CLASS in ClassifyText()";\n'
        "\t\t}\n\t}\n\n"
        "\tconst char* CHalfLife2::AIClassText(int classType)\n"
        "\t{\n"
        "\t\treturn HL2_AIClassText( classType );\n"
        "\t}",
    )

    # 3. Wire HL2_InitDefaultAIRelationships & HL2_AIClassText into CHL2MPRules.
    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.h",
        "\tvirtual bool\tCanHavePlayerItem( CBasePlayer *pPlayer, CBaseCombatWeapon *pItem );\n"
        "\tvirtual bool FShouldSwitchWeapon( CBasePlayer *pPlayer, CBaseCombatWeapon *pWeapon );",
        "\tvirtual void InitDefaultAIRelationships( void );\n"
        "\tvirtual const char *AIClassText( int classType );\n"
        "\tvirtual bool\tCanHavePlayerItem( CBasePlayer *pPlayer, CBaseCombatWeapon *pItem );\n"
        "\tvirtual bool FShouldSwitchWeapon( CBasePlayer *pPlayer, CBaseCombatWeapon *pWeapon );",
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        '\t#include "hl2mp_cvars.h"',
        '\t#include "hl2mp_cvars.h"\n'
        '\t#include "hl2_gamerules.h"',
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        "const char *CHL2MPRules::GetGameDescription( void )\n"
        "{ \n"
        "\tif ( IsTeamplay() )\n"
        '\t\treturn "Team Deathmatch"; \n\n'
        '\treturn "Deathmatch"; \n'
        "} ",
        "#ifndef CLIENT_DLL\n"
        "void CHL2MPRules::InitDefaultAIRelationships( void )\n"
        "{\n"
        "\tHL2_InitDefaultAIRelationships();\n"
        "}\n\n"
        "const char *CHL2MPRules::AIClassText( int classType )\n"
        "{\n"
        "\treturn HL2_AIClassText( classType );\n"
        "}\n"
        "#endif\n\n"
        "const char *CHL2MPRules::GetGameDescription( void )\n"
        "{\n"
        '\treturn "TBMG: Country & MainCity2";\n'
        "} ",
    )

    # 4. Bind skill.cfg ConVars and register missing HL2 vehicle/NPC ammo types
    # (GaussEnergy for Scout Buggy, AirboatGun, CombineCannon, AlyxGun, SniperRound).
    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        '\t\tdef.AddAmmoType("AR2",\t\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t0,\t\t\t0,\t\t\t60,\t\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("AR2AltFire",\t\tDMG_DISSOLVE,\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t0,\t\t\t3,\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("Pistol",\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t0,\t\t\t0,\t\t\t150,\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("SMG1",\t\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t0,\t\t\t0,\t\t\t225,\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("357",\t\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t0,\t\t\t0,\t\t\t12,\t\t\tBULLET_IMPULSE(800, 5000),\t0 );\n'
        '\t\tdef.AddAmmoType("XBowBolt",\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE,\t\t\t0,\t\t\t0,\t\t\t10,\t\t\tBULLET_IMPULSE(800, 8000),\t0 );\n'
        '\t\tdef.AddAmmoType("Buckshot",\t\t\tDMG_BULLET | DMG_BUCKSHOT,\tTRACER_LINE,\t\t\t0,\t\t\t0,\t\t\t30,\t\t\tBULLET_IMPULSE(400, 1200),\t0 );\n'
        '\t\tdef.AddAmmoType("RPG_Round",\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t0,\t\t\t3,\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("SMG1_Grenade",\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t0,\t\t\t3,\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("Grenade",\t\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t0,\t\t\t5,\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("slam",\t\t\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t0,\t\t\t5,\t\t\t0,\t\t\t\t\t\t\t0 );',
        '\t\tdef.AddAmmoType("AR2",\t\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t"sk_plr_dmg_ar2",\t\t\t"sk_npc_dmg_ar2",\t\t\t"sk_max_ar2",\t\t\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("AR2AltFire",\t\tDMG_DISSOLVE,\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t\t\t\t\t0,\t\t\t\t\t\t\t"sk_max_ar2_altfire",\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("AlyxGun",\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE,\t\t\t"sk_plr_dmg_alyxgun",\t\t"sk_npc_dmg_alyxgun",\t\t"sk_max_alyxgun",\t\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("Pistol",\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t"sk_plr_dmg_pistol",\t\t"sk_npc_dmg_pistol",\t\t"sk_max_pistol",\t\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("SMG1",\t\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t"sk_plr_dmg_smg1",\t\t\t"sk_npc_dmg_smg1",\t\t\t"sk_max_smg1",\t\t\t\tBULLET_IMPULSE(200, 1225),\t0 );\n'
        '\t\tdef.AddAmmoType("357",\t\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE_AND_WHIZ,\t"sk_plr_dmg_357",\t\t\t"sk_npc_dmg_357",\t\t\t"sk_max_357",\t\t\t\tBULLET_IMPULSE(800, 5000),\t0 );\n'
        '\t\tdef.AddAmmoType("XBowBolt",\t\t\tDMG_BULLET,\t\t\t\t\tTRACER_LINE,\t\t\t"sk_plr_dmg_crossbow",\t\t"sk_npc_dmg_crossbow",\t\t"sk_max_crossbow",\t\t\tBULLET_IMPULSE(800, 8000),\t0 );\n'
        '\t\tdef.AddAmmoType("Buckshot",\t\t\tDMG_BULLET | DMG_BUCKSHOT,\tTRACER_LINE,\t\t\t"sk_plr_dmg_buckshot",\t\t"sk_npc_dmg_buckshot",\t\t"sk_max_buckshot",\t\t\tBULLET_IMPULSE(400, 1200),\t0 );\n'
        '\t\tdef.AddAmmoType("RPG_Round",\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t"sk_plr_dmg_rpg_round",\t\t"sk_npc_dmg_rpg_round",\t\t"sk_max_rpg_round",\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("SMG1_Grenade",\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t"sk_plr_dmg_smg1_grenade",\t"sk_npc_dmg_smg1_grenade",\t"sk_max_smg1_grenade",\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("SniperRound",\t\tDMG_BULLET | DMG_SNIPER,\tTRACER_NONE,\t\t\t"sk_plr_dmg_sniper_round",\t"sk_npc_dmg_sniper_round",\t"sk_max_sniper_round",\t\tBULLET_IMPULSE(650, 6000),\t0 );\n'
        '\t\tdef.AddAmmoType("SniperPenetratedRound", DMG_BULLET | DMG_SNIPER, TRACER_NONE,\t\t"sk_dmg_sniper_penetrate_plr", "sk_dmg_sniper_penetrate_npc", "sk_max_sniper_round", BULLET_IMPULSE(150, 6000), 0 );\n'
        '\t\tdef.AddAmmoType("Grenade",\t\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t"sk_plr_dmg_grenade",\t\t"sk_npc_dmg_grenade",\t\t"sk_max_grenade",\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("Thumper",\t\t\tDMG_SONIC,\t\t\t\t\tTRACER_NONE,\t\t\t10,\t\t\t\t\t\t\t10,\t\t\t\t\t\t\t2,\t\t\t\t\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("Gravity",\t\t\tDMG_CLUB,\t\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t\t\t\t\t0,\t\t\t\t\t\t\t8,\t\t\t\t\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("Battery",\t\t\tDMG_CLUB,\t\t\t\t\tTRACER_NONE,\t\t\tNULL,\t\t\t\t\t\tNULL,\t\t\t\t\t\tNULL,\t\t\t\t\t\t0,\t\t\t\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("GaussEnergy",\t\tDMG_SHOCK,\t\t\t\t\tTRACER_NONE,\t\t\t"sk_jeep_gauss_damage",\t\t"sk_jeep_gauss_damage",\t\t"sk_max_gauss_round",\t\tBULLET_IMPULSE(650, 8000),\t0 );\n'
        '\t\tdef.AddAmmoType("CombineCannon",\tDMG_BULLET,\t\t\t\t\tTRACER_LINE,\t\t\t"sk_npc_dmg_gunship_to_plr", "sk_npc_dmg_gunship",\t\tNULL,\t\t\t\t\t\t1.5 * 750 * 12,\t\t\t\t0 );\n'
        '\t\tdef.AddAmmoType("AirboatGun",\t\tDMG_AIRBOAT,\t\t\t\tTRACER_LINE,\t\t\t"sk_plr_dmg_airboat",\t\t"sk_npc_dmg_airboat",\t\tNULL,\t\t\t\t\t\tBULLET_IMPULSE(10, 600),\t0 );\n'
        '\t\tdef.AddAmmoType("slam",\t\t\t\tDMG_BURN,\t\t\t\t\tTRACER_NONE,\t\t\t0,\t\t\t\t\t\t\t0,\t\t\t\t\t\t\t5,\t\t\t\t\t\t\t0,\t\t\t\t\t\t\t0 );',
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_sdk_x64.py <sdk_src_dir>")
    patch_sdk(pathlib.Path(sys.argv[1]).resolve())
    print("Patched Source SDK 2013 x64 cleanly.")


if __name__ == "__main__":
    main()
