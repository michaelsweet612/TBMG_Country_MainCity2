"""Patch an upstream ValveSoftware/source-sdk-2013 checkout for TBMG x64 builds."""

from __future__ import annotations

import pathlib
import shutil
import sys


def copy_sdk_files(sdk_src: pathlib.Path) -> None:
    files_root = pathlib.Path(__file__).resolve().parent / "sdk_files"
    if not files_root.is_dir():
        raise RuntimeError(f"Missing TBMG SDK files directory: {files_root}")
    for src_file in files_root.rglob("*"):
        if src_file.is_file():
            rel = src_file.relative_to(files_root)
            dst_file = sdk_src / rel
            dst_file.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src_file, dst_file)


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

    # 1b. Compile hl2/npc_fastzombie.cpp and hl2/weapon_alyxgun.cpp in Server (HL2MP).
    replace_once(
        src / "game/server/server_hl2mp.vpc",
        '\t\t\t$File\t"hl2\\npc_enemyfinder.cpp"\n'
        '\t\t\t$File\t"hl2\\npc_fisherman.cpp"',
        '\t\t\t$File\t"hl2\\npc_enemyfinder.cpp"\n'
        '\t\t\t$File\t"hl2\\npc_fastzombie.cpp"\n'
        '\t\t\t$File\t"hl2\\npc_fisherman.cpp"',
    )

    replace_once(
        src / "game/server/server_hl2mp.vpc",
        '\t\t\t$File\t"hl2\\weapon_alyxgun.h"\n'
        '\t\t\t$File\t"hl2\\weapon_annabelle.cpp"',
        '\t\t\t$File\t"hl2\\weapon_alyxgun.cpp"\n'
        '\t\t\t$File\t"hl2\\weapon_alyxgun.h"\n'
        '\t\t\t$File\t"hl2\\weapon_annabelle.cpp"',
    )

    server_vcxproj = src / "game/server/server_win64_hl2mp.vcxproj"
    if server_vcxproj.is_file():
        replace_once(
            server_vcxproj,
            '    <ClCompile Include="hl2\\npc_enemyfinder.cpp" />\n'
            '    <ClCompile Include="hl2\\npc_fisherman.cpp" />',
            '    <ClCompile Include="hl2\\npc_enemyfinder.cpp" />\n'
            '    <ClCompile Include="hl2\\npc_fastzombie.cpp" />\n'
            '    <ClCompile Include="hl2\\npc_fisherman.cpp" />',
        )
        replace_once(
            server_vcxproj,
            '    <ClCompile Include="hl2\\vehicle_viewcontroller.cpp" />\n'
            '    <ClCompile Include="hl2\\weapon_annabelle.cpp" />',
            '    <ClCompile Include="hl2\\vehicle_viewcontroller.cpp" />\n'
            '    <ClCompile Include="hl2\\weapon_alyxgun.cpp" />\n'
            '    <ClCompile Include="hl2\\weapon_annabelle.cpp" />',
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
        '#include "ammodef.h"\n\n#ifdef CLIENT_DLL',
        '#include "ammodef.h"\n#include "hl2_shareddefs.h"\n\n#ifdef CLIENT_DLL',
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        '\t#include "hl2mp_cvars.h"',
        '\t#include "hl2mp_cvars.h"\n'
        '\t#include "hl2_gamerules.h"\n'
        '\t#include "tbmg_natural_spawn.h"',
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

    # 5. Add TBMG Natural Spawning server files + client Options UI bridge and wire hooks.
    copy_sdk_files(src)

    replace_once(
        src / "game/server/server_hl2mp.vpc",
        '\t\t\t$File\t"hl2mp\\hl2mp_gameinterface.cpp"\n'
        '\t\t\t$File\t"hl2mp\\hl2mp_gameinterface.h"',
        '\t\t\t$File\t"hl2mp\\hl2mp_gameinterface.cpp"\n'
        '\t\t\t$File\t"hl2mp\\hl2mp_gameinterface.h"\n'
        '\t\t\t$File\t"hl2mp\\tbmg_natural_spawn.cpp"\n'
        '\t\t\t$File\t"hl2mp\\tbmg_natural_spawn.h"',
    )

    replace_once(
        src / "game/client/client_hl2mp.vpc",
        '\t\t\t\t$File\t"hl2mp\\ui\\hl2mptextwindow.cpp"\n'
        '\t\t\t\t$File\t"hl2mp\\ui\\hl2mptextwindow.h"',
        '\t\t\t\t$File\t"hl2mp\\ui\\hl2mptextwindow.cpp"\n'
        '\t\t\t\t$File\t"hl2mp\\ui\\hl2mptextwindow.h"\n'
        '\t\t\t\t$File\t"hl2mp\\ui\\tbmg_options_bridge.cpp"\n'
        '\t\t\t\t$File\t"hl2mp\\ui\\tbmg_options_bridge.h"',
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        "extern CBaseEntity\t *g_pLastRebelSpawn;\n\n#define WEAPON_MAX_DISTANCE_FROM_SPAWN 64\n\n#endif\n\n\nREGISTER_GAMERULES_CLASS( CHL2MPRules );",
        "extern CBaseEntity\t *g_pLastRebelSpawn;\n\n#define WEAPON_MAX_DISTANCE_FROM_SPAWN 64\n\n#endif\n\n"
        'ConVar tbmg_natural_spawn( "tbmg_natural_spawn", "0", FCVAR_ARCHIVE | FCVAR_REPLICATED, "Enable natural NPC spawning at map NPC nodes (excludes ammo/items)." );\n'
        'ConVar tbmg_natural_spawn_interval( "tbmg_natural_spawn_interval", "6.0", FCVAR_ARCHIVE | FCVAR_REPLICATED, "Seconds between natural spawn attempts.", true, 1.0f, true, 60.0f );\n'
        'ConVar tbmg_natural_spawn_max( "tbmg_natural_spawn_max", "14", FCVAR_ARCHIVE | FCVAR_REPLICATED, "Maximum active naturally spawned NPCs.", true, 1.0f, true, 32.0f );\n\n'
        "REGISTER_GAMERULES_CLASS( CHL2MPRules );",
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        "\tm_bAwaitingReadyRestart = false;\n\tm_bChangelevelDone = false;\n\n#endif\n}",
        "\tm_bAwaitingReadyRestart = false;\n\tm_bChangelevelDone = false;\n\n"
        "\tTBMG_NaturalSpawn_Reset();\n\n#endif\n}",
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        "\tg_Teams.Purge();\n#endif\n}",
        "\tg_Teams.Purge();\n\tTBMG_NaturalSpawn_Reset();\n#endif\n}",
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        "\tManageObjectRelocation();\n\n#endif\n}",
        "\tManageObjectRelocation();\n\tTBMG_NaturalSpawn_Think();\n\n#endif\n}",
    )

    replace_once(
        src / "game/shared/hl2mp/hl2mp_gamerules.cpp",
        'void CHL2MPRules::Precache( void )\n{\n\tCBaseEntity::PrecacheScriptSound( "AlyxEmp.Charge" );\n}',
        'void CHL2MPRules::Precache( void )\n{\n\tCBaseEntity::PrecacheScriptSound( "AlyxEmp.Charge" );\n#ifndef CLIENT_DLL\n\tTBMG_NaturalSpawn_Precache();\n#endif\n}',
    )

    replace_once(
        src / "game/client/vgui_int.cpp",
        "void MP3Player_Create( vgui::VPANEL parent );\nvoid MP3Player_Destroy();",
        "void MP3Player_Create( vgui::VPANEL parent );\nvoid MP3Player_Destroy();\n"
        "#ifdef HL2MP\n"
        "void TBMG_OptionsBridge_Create( vgui::VPANEL parent );\n"
        "void TBMG_OptionsBridge_Destroy( void );\n"
        "#endif",
    )

    replace_once(
        src / "game/client/vgui_int.cpp",
        "\tMP3Player_Create( toolParent );",
        "\tMP3Player_Create( toolParent );\n#ifdef HL2MP\n\tTBMG_OptionsBridge_Create( toolParent );\n#endif",
    )

    replace_once(
        src / "game/client/vgui_int.cpp",
        "\tMP3Player_Destroy();",
        "\tMP3Player_Destroy();\n#ifdef HL2MP\n\tTBMG_OptionsBridge_Destroy();\n#endif",
    )

    # 6. Fall back from MOD to GAME when reading weapon scripts so HL2 base weapon scripts load.
    replace_once(
        src / "game/shared/weapon_parse.cpp",
        "KeyValues* ReadEncryptedKVFile( IFileSystem *pFilesystem, const char *szFilenameWithoutExtension, const unsigned char *pICEKey, bool bForceReadEncryptedFile /*= false*/ )\n"
        "{\n"
        "\tAssert( strchr( szFilenameWithoutExtension, '.' ) == NULL );\n"
        "\tchar szFullName[512];\n\n"
        '\tconst char *pSearchPath = "MOD";\n\n'
        "\tif ( pICEKey == NULL )\n"
        "\t{\n"
        '\t\tpSearchPath = "GAME";\n'
        "\t}\n\n"
        "\t// Open the weapon data file, and abort if we can't\n"
        '\tKeyValues *pKV = new KeyValues( "WeaponDatafile" );\n\n'
        '\tQ_snprintf(szFullName,sizeof(szFullName), "%s.txt", szFilenameWithoutExtension);\n\n'
        "\tif ( bForceReadEncryptedFile || !pKV->LoadFromFile( pFilesystem, szFullName, pSearchPath ) ) // try to load the normal .txt file first\n"
        "\t{\n"
        "#ifndef _XBOX\n"
        "\t\tif ( pICEKey )\n"
        "\t\t{\n"
        '\t\t\tQ_snprintf(szFullName,sizeof(szFullName), "%s.ctx", szFilenameWithoutExtension); // fall back to the .ctx file\n\n'
        '\t\t\tFileHandle_t f = pFilesystem->Open( szFullName, "rb", pSearchPath );\n\n'
        "\t\t\tif (!f)\n"
        "\t\t\t{\n"
        "\t\t\t\tpKV->deleteThis();\n"
        "\t\t\t\treturn NULL;\n"
        "\t\t\t}\n"
        "\t\t\t// load file into a null-terminated buffer\n"
        "\t\t\tint fileSize = pFilesystem->Size(f);\n"
        "\t\t\tchar *buffer = (char*)MemAllocScratch(fileSize + 1);\n\t\t\n"
        "\t\t\tAssert(buffer);\n\t\t\n"
        "\t\t\tpFilesystem->Read(buffer, fileSize, f); // read into local buffer\n"
        "\t\t\tbuffer[fileSize] = 0; // null terminate file as EOF\n"
        "\t\t\tpFilesystem->Close( f );\t// close file after reading\n\n"
        "\t\t\tUTIL_DecodeICE( (unsigned char*)buffer, fileSize, pICEKey );\n\n"
        "\t\t\tbool retOK = pKV->LoadFromBuffer( szFullName, buffer, pFilesystem );\n\n"
        "\t\t\tMemFreeScratch();\n\n"
        "\t\t\tif ( !retOK )\n"
        "\t\t\t{\n"
        "\t\t\t\tpKV->deleteThis();\n"
        "\t\t\t\treturn NULL;\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t\telse\n"
        "\t\t{\n"
        "\t\t\tpKV->deleteThis();\n"
        "\t\t\treturn NULL;\n"
        "\t\t}\n"
        "#else\n"
        "\t\tpKV->deleteThis();\n"
        "\t\treturn NULL;\n"
        "#endif\n"
        "\t}\n\n"
        "\treturn pKV;\n"
        "}",
        "static bool TryLoadWeaponKVFromPath( IFileSystem *pFilesystem, KeyValues *pKV, const char *szFilenameWithoutExtension, const unsigned char *pICEKey, bool bForceReadEncryptedFile, const char *pSearchPath )\n"
        "{\n"
        "\tchar szFullName[512];\n\n"
        '\tQ_snprintf( szFullName, sizeof( szFullName ), "%s.txt", szFilenameWithoutExtension );\n\n'
        "\tif ( !bForceReadEncryptedFile && pKV->LoadFromFile( pFilesystem, szFullName, pSearchPath ) ) // try to load the normal .txt file first\n"
        "\t\treturn true;\n\n"
        "#ifndef _XBOX\n"
        "\tif ( pICEKey )\n"
        "\t{\n"
        '\t\tQ_snprintf( szFullName, sizeof( szFullName ), "%s.ctx", szFilenameWithoutExtension ); // fall back to the .ctx file\n\n'
        '\t\tFileHandle_t f = pFilesystem->Open( szFullName, "rb", pSearchPath );\n'
        "\t\tif ( !f )\n"
        "\t\t\treturn false;\n\n"
        "\t\t// load file into a null-terminated buffer\n"
        "\t\tint fileSize = pFilesystem->Size( f );\n"
        "\t\tchar *buffer = (char*)MemAllocScratch( fileSize + 1 );\n\n"
        "\t\tAssert( buffer );\n\n"
        "\t\tpFilesystem->Read( buffer, fileSize, f ); // read into local buffer\n"
        "\t\tbuffer[fileSize] = 0; // null terminate file as EOF\n"
        "\t\tpFilesystem->Close( f ); // close file after reading\n\n"
        "\t\tUTIL_DecodeICE( (unsigned char*)buffer, fileSize, pICEKey );\n\n"
        "\t\tbool retOK = pKV->LoadFromBuffer( szFullName, buffer, pFilesystem );\n\n"
        "\t\tMemFreeScratch();\n\n"
        "\t\treturn retOK;\n"
        "\t}\n"
        "#endif\n\n"
        "\treturn false;\n"
        "}\n\n"
        "KeyValues* ReadEncryptedKVFile( IFileSystem *pFilesystem, const char *szFilenameWithoutExtension, const unsigned char *pICEKey, bool bForceReadEncryptedFile /*= false*/ )\n"
        "{\n"
        "\tAssert( strchr( szFilenameWithoutExtension, '.' ) == NULL );\n\n"
        '\tconst char *pSearchPath = "MOD";\n\n'
        "\tif ( pICEKey == NULL )\n"
        "\t{\n"
        '\t\tpSearchPath = "GAME";\n'
        "\t}\n\n"
        "\t// Open the weapon data file, and abort if we can't\n"
        '\tKeyValues *pKV = new KeyValues( "WeaponDatafile" );\n\n'
        "\tif ( !TryLoadWeaponKVFromPath( pFilesystem, pKV, szFilenameWithoutExtension, pICEKey, bForceReadEncryptedFile, pSearchPath ) )\n"
        "\t{\n"
        "\t\t// Standalone mods reusing Source SDK Base 2013 weapon scripts keep unencrypted/VPK scripts on GAME.\n"
        '\t\tif ( Q_stricmp( pSearchPath, "GAME" ) == 0 ||\n'
        '\t\t\t!TryLoadWeaponKVFromPath( pFilesystem, pKV, szFilenameWithoutExtension, pICEKey, bForceReadEncryptedFile, "GAME" ) )\n'
        "\t\t{\n"
        "\t\t\tpKV->deleteThis();\n"
        "\t\t\treturn NULL;\n"
        "\t\t}\n"
        "\t}\n\n"
        "\treturn pKV;\n"
        "}",
    )

    # 7. Guard unsafe static_cast<CHalfLife2 *>(g_pGameRules) calls in HL2MP NPCs and skip auto-MOTD popup locally.
    replace_once(
        src / "game/server/hl2/npc_combines.cpp",
        "\t\tCHalfLife2 *pHL2GameRules = static_cast<CHalfLife2 *>(g_pGameRules);\n\n"
        "\t\t// Attempt to drop health\n"
        "\t\tif ( pHL2GameRules->NPC_ShouldDropHealth( pPlayer ) )\n"
        "\t\t{\n"
        '\t\t\tDropItem( "item_healthvial", WorldSpaceCenter()+RandomVector(-4,4), RandomAngle(0,360) );\n'
        "\t\t\tpHL2GameRules->NPC_DroppedHealth();\n"
        "\t\t}\n"
        "\t\t\n"
        "\t\tif ( HasSpawnFlags( SF_COMBINE_NO_GRENADEDROP ) == false )\n"
        "\t\t{\n"
        "\t\t\t// Attempt to drop a grenade\n"
        "\t\t\tif ( pHL2GameRules->NPC_ShouldDropGrenade( pPlayer ) )\n"
        "\t\t\t{\n"
        '\t\t\t\tDropItem( "weapon_frag", WorldSpaceCenter()+RandomVector(-4,4), RandomAngle(0,360) );\n'
        "\t\t\t\tpHL2GameRules->NPC_DroppedGrenade();\n"
        "\t\t\t}\n"
        "\t\t}",
        "#if !defined( HL2MP )\n"
        "\t\tCHalfLife2 *pHL2GameRules = static_cast<CHalfLife2 *>(g_pGameRules);\n\n"
        "\t\t// Attempt to drop health\n"
        "\t\tif ( pHL2GameRules->NPC_ShouldDropHealth( pPlayer ) )\n"
        "\t\t{\n"
        '\t\t\tDropItem( "item_healthvial", WorldSpaceCenter()+RandomVector(-4,4), RandomAngle(0,360) );\n'
        "\t\t\tpHL2GameRules->NPC_DroppedHealth();\n"
        "\t\t}\n"
        "\t\t\n"
        "\t\tif ( HasSpawnFlags( SF_COMBINE_NO_GRENADEDROP ) == false )\n"
        "\t\t{\n"
        "\t\t\t// Attempt to drop a grenade\n"
        "\t\t\tif ( pHL2GameRules->NPC_ShouldDropGrenade( pPlayer ) )\n"
        "\t\t\t{\n"
        '\t\t\t\tDropItem( "weapon_frag", WorldSpaceCenter()+RandomVector(-4,4), RandomAngle(0,360) );\n'
        "\t\t\t\tpHL2GameRules->NPC_DroppedGrenade();\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "#endif",
    )

    replace_once(
        src / "game/server/hl2/npc_metropolice.cpp",
        "\tCBasePlayer *pPlayer = ToBasePlayer( info.GetAttacker() );\n\n"
        "\tif ( pPlayer != NULL )\n"
        "\t{\n"
        "\t\tCHalfLife2 *pHL2GameRules = static_cast<CHalfLife2 *>(g_pGameRules);\n\n"
        "\t\t// Attempt to drop health\n"
        "\t\tif ( pHL2GameRules->NPC_ShouldDropHealth( pPlayer ) )\n"
        "\t\t{\n"
        '\t\t\tDropItem( "item_healthvial", WorldSpaceCenter()+RandomVector(-4,4), RandomAngle(0,360) );\n'
        "\t\t\tpHL2GameRules->NPC_DroppedHealth();\n"
        "\t\t}\n"
        "\t}",
        "#if !defined( HL2MP )\n"
        "\tCBasePlayer *pPlayer = ToBasePlayer( info.GetAttacker() );\n\n"
        "\tif ( pPlayer != NULL )\n"
        "\t{\n"
        "\t\tCHalfLife2 *pHL2GameRules = static_cast<CHalfLife2 *>(g_pGameRules);\n\n"
        "\t\t// Attempt to drop health\n"
        "\t\tif ( pHL2GameRules->NPC_ShouldDropHealth( pPlayer ) )\n"
        "\t\t{\n"
        '\t\t\tDropItem( "item_healthvial", WorldSpaceCenter()+RandomVector(-4,4), RandomAngle(0,360) );\n'
        "\t\t\tpHL2GameRules->NPC_DroppedHealth();\n"
        "\t\t}\n"
        "\t}\n"
        "#endif",
    )

    replace_once(
        src / "game/server/hl2mp/hl2mp_client.cpp",
        '\tconst ConVar *hostname = cvar->FindVar( "hostname" );\n'
        '\tconst char *title = (hostname) ? hostname->GetString() : "MESSAGE OF THE DAY";\n\n'
        '\tKeyValues *data = new KeyValues("data");\n'
        '\tdata->SetString( "title", title );\t\t// info panel title\n'
        '\tdata->SetString( "type", "1" );\t\t\t// show userdata from stringtable entry\n'
        '\tdata->SetString( "msg",\t"motd" );\t\t// use this stringtable entry\n'
        '\tdata->SetBool( "unload", sv_motd_unload_on_dismissal.GetBool() );\n\n'
        "\tpPlayer->ShowViewPortPanel( PANEL_INFO, true, data );\n\n"
        "\tdata->deleteThis();",
        "\tif ( engine->IsDedicatedServer() )\n"
        "\t{\n"
        '\t\tconst ConVar *hostname = cvar->FindVar( "hostname" );\n'
        '\t\tconst char *title = (hostname) ? hostname->GetString() : "MESSAGE OF THE DAY";\n\n'
        '\t\tKeyValues *data = new KeyValues("data");\n'
        '\t\tdata->SetString( "title", title );\t\t// info panel title\n'
        '\t\tdata->SetString( "type", "1" );\t\t\t// show userdata from stringtable entry\n'
        '\t\tdata->SetString( "msg",\t"motd" );\t\t// use this stringtable entry\n'
        '\t\tdata->SetBool( "unload", sv_motd_unload_on_dismissal.GetBool() );\n\n'
        "\t\tpPlayer->ShowViewPortPanel( PANEL_INFO, true, data );\n\n"
        "\t\tdata->deleteThis();\n"
        "\t}",
    )

    # 8. Force Father Grigori (npc_monk) to ALWAYS equip weapon_shotgun cleanly, give Alyx/Barney
    # default HL2 weapons when spawned via npc_create, and restore HL2 NPC firing handlers
    # (#ifndef CLIENT_DLL) in shared HL2MP weapons (pistol, smg1, ar2, shotgun, rpg).
    replace_once(
        src / "game/server/hl2/npc_monk.cpp",
        "\tCNPC_Monk() {}\n"
        "\tvoid Spawn();\n"
        "\tvoid Precache();",
        "\tCNPC_Monk() {}\n"
        "\tvoid Spawn();\n"
        "\tvoid Precache();\n"
        "\tbool KeyValue( const char *szKeyName, const char *szValue );\n"
        "\tvoid Weapon_Equip( CBaseCombatWeapon *pWeapon );",
    )

    replace_once(
        src / "game/server/hl2/npc_monk.cpp",
        "\t// We need these so that we can pick up the shotgun to throw it in the balcony scene\n"
        "\tif ( eNewActivity == ACT_IDLE_ANGRY_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_IDLE_ANGRY_SMG1;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_WALK_AIM_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_WALK_AIM_RIFLE;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_RUN_AIM_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_RUN_AIM_RIFLE;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_RANGE_ATTACK_SHOTGUN_LOW )\n"
        "\t{\n"
        "\t\treturn ACT_RANGE_ATTACK_SMG1_LOW;\n"
        "\t}\n\n"
        "\treturn eNewActivity;",
        "\t// Father Grigori always uses weapon_shotgun with Monk.mdl.\n"
        "\tif ( eNewActivity == ACT_IDLE_ANGRY_SHOTGUN || eNewActivity == ACT_IDLE_SHOTGUN_AGITATED )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_IDLE_ANGRY_SMG1;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_IDLE_SHOTGUN_RELAXED )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_IDLE_SMG1_RELAXED;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_IDLE_SHOTGUN_STIMULATED )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_IDLE_SMG1_STIMULATED;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_WALK_AIM_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_WALK_AIM_RIFLE;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_RUN_AIM_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_RUN_AIM_RIFLE;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_RANGE_ATTACK_SHOTGUN_LOW )\n"
        "\t{\n"
        "\t\treturn ACT_RANGE_ATTACK_SMG1_LOW;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_RELOAD_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_RELOAD_SMG1;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_RELOAD_SHOTGUN_LOW )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_RELOAD_SMG1_LOW;\n"
        "\t}\n"
        "\telse if ( eNewActivity == ACT_GESTURE_RELOAD_SHOTGUN )\n"
        "\t{\n"
        "\t\teNewActivity = ACT_GESTURE_RELOAD_SMG1;\n"
        "\t}\n\n"
        "\treturn eNewActivity;",
    )

    replace_once(
        src / "game/server/hl2/npc_monk.cpp",
        "void CNPC_Monk::Precache()\n"
        "{\n"
        '\tPrecacheModel( "models/Monk.mdl" );\n'
        "\t\n"
        '\tPrecacheScriptSound( "NPC_Citizen.FootstepLeft" );\n'
        '\tPrecacheScriptSound( "NPC_Citizen.FootstepRight" );\n\n'
        "\tBaseClass::Precache();\n"
        "}",
        "bool CNPC_Monk::KeyValue( const char *szKeyName, const char *szValue )\n"
        "{\n"
        '\tif ( FStrEq( szKeyName, "additionalequipment" ) )\n'
        "\t{\n"
        '\t\tm_spawnEquipment = AllocPooledString( "weapon_shotgun" );\n'
        "\t\treturn true;\n"
        "\t}\n\n"
        "\treturn BaseClass::KeyValue( szKeyName, szValue );\n"
        "}\n\n"
        "void CNPC_Monk::Weapon_Equip( CBaseCombatWeapon *pWeapon )\n"
        "{\n"
        "\tBaseClass::Weapon_Equip( pWeapon );\n"
        "\tif ( pWeapon )\n"
        "\t{\n"
        "\t\tpWeapon->m_fMaxRange1 = MAX( pWeapon->m_fMaxRange1, 1500.0f );\n"
        "\t}\n"
        "}\n\n"
        "void CNPC_Monk::Precache()\n"
        "{\n"
        '\tm_spawnEquipment = AllocPooledString( "weapon_shotgun" );\n'
        '\tPrecacheModel( "models/Monk.mdl" );\n'
        "\t\n"
        '\tPrecacheScriptSound( "NPC_Citizen.FootstepLeft" );\n'
        '\tPrecacheScriptSound( "NPC_Citizen.FootstepRight" );\n\n'
        '\tUTIL_PrecacheOther( "weapon_shotgun" );\n\n'
        "\tBaseClass::Precache();\n"
        "}",
    )

    replace_once(
        src / "game/server/hl2/npc_monk.cpp",
        "\tCapabilitiesAdd( bits_CAP_AIM_GUN );\n"
        "\tCapabilitiesAdd( bits_CAP_MOVE_SHOOT );\n\n"
        "\tNPCInit();",
        "\tCapabilitiesAdd( bits_CAP_AIM_GUN );\n"
        "\tCapabilitiesAdd( bits_CAP_MOVE_SHOOT );\n\n"
        '\tm_spawnEquipment = AllocPooledString( "weapon_shotgun" );\n\n'
        "\tNPCInit();",
    )

    replace_once(
        src / "game/server/hl2/npc_alyx.cpp",
        "\tm_iHealth\t\t\t= 80;\n\n\tNPCInit();",
        "\tm_iHealth\t\t\t= 80;\n\n"
        '\tif ( m_spawnEquipment == NULL_STRING || !STRING( m_spawnEquipment )[0] )\n'
        "\t{\n"
        '\t\tm_spawnEquipment = AllocPooledString( "weapon_alyxgun" );\n'
        "\t}\n\n"
        "\tNPCInit();",
    )

    replace_once(
        src / "game/server/hl2/npc_alyx.cpp",
        '\tPrecacheModel( "models/alyx_emptool_prop.mdl" );\n}',
        '\tPrecacheModel( "models/alyx_emptool_prop.mdl" );\n'
        '\tUTIL_PrecacheOther( "weapon_alyxgun" );\n}',
    )

    replace_once(
        src / "game/server/hl2/npc_barney.cpp",
        '\t\tPrecacheScriptSound( "NPC_Barney.Die" );',
        '\t\tPrecacheScriptSound( "NPC_Barney.Die" );\n\t\tUTIL_PrecacheOther( "weapon_ar2" );',
    )

    replace_once(
        src / "game/server/hl2/npc_barney.cpp",
        "\tAddEFlags( EFL_NO_DISSOLVE | EFL_NO_MEGAPHYSCANNON_RAGDOLL | EFL_NO_PHYSCANNON_INTERACTION );\n\n\tNPCInit();",
        "\tAddEFlags( EFL_NO_DISSOLVE | EFL_NO_MEGAPHYSCANNON_RAGDOLL | EFL_NO_PHYSCANNON_INTERACTION );\n\n"
        '\tif ( m_spawnEquipment == NULL_STRING || !STRING( m_spawnEquipment )[0] )\n'
        "\t{\n"
        '\t\tm_spawnEquipment = AllocPooledString( "weapon_ar2" );\n'
        "\t}\n\n"
        "\tNPCInit();",
    )

    # Restore NPC weapon anim events & NPC acttables in HL2MP shared weapons (#ifndef CLIENT_DLL).
    replace_once(
        src / "game/shared/hl2mp/weapon_pistol.cpp",
        "#else\n\t#include \"hl2mp_player.h\"\n#endif",
        "#else\n\t#include \"hl2mp_player.h\"\n\t#include \"soundent.h\"\n\t#include \"ai_basenpc.h\"\n#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_pistol.cpp",
        "#ifndef CLIENT_DLL\n\tDECLARE_ACTTABLE();\n#endif\n\nprivate:\n\tCNetworkVar( float,\tm_flSoonestPrimaryAttack );",
        "#ifndef CLIENT_DLL\n"
        "\tvoid\tOperator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator );\n"
        "\tDECLARE_ACTTABLE();\n"
        "#endif\n\nprivate:\n\tCNetworkVar( float,\tm_flSoonestPrimaryAttack );",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_pistol.cpp",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_PISTOL,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_PISTOL,\t\t\t\tfalse },\n};",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_PISTOL,\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE,\t\t\t\t\t\t\tACT_IDLE_PISTOL,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_ANGRY,\t\t\t\t\tACT_IDLE_ANGRY_PISTOL,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_PISTOL,\t\t\t\ttrue },\n"
        "\t{ ACT_RELOAD,\t\t\t\t\t\tACT_RELOAD_PISTOL,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_AIM,\t\t\t\t\t\tACT_WALK_AIM_PISTOL,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_AIM,\t\t\t\t\t\tACT_RUN_AIM_PISTOL,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_GESTURE_RANGE_ATTACK1,\t\tACT_GESTURE_RANGE_ATTACK_PISTOL,\t\ttrue },\n"
        "\t{ ACT_RELOAD_LOW,\t\t\t\t\tACT_RELOAD_PISTOL_LOW,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1_LOW,\t\t\tACT_RANGE_ATTACK_PISTOL_LOW,\t\t\tfalse },\n"
        "\t{ ACT_COVER_LOW,\t\t\t\t\tACT_COVER_PISTOL_LOW,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_AIM_LOW,\t\t\t\tACT_RANGE_AIM_PISTOL_LOW,\t\t\t\tfalse },\n"
        "\t{ ACT_GESTURE_RELOAD,\t\t\t\tACT_GESTURE_RELOAD_PISTOL,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK,\t\t\t\t\t\t\tACT_WALK_PISTOL,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN,\t\t\t\t\t\t\tACT_RUN_PISTOL,\t\t\t\t\t\t\tfalse },\n};",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_pistol.cpp",
        "void CWeaponPistol::Precache( void )\n{\n\tBaseClass::Precache();\n}",
        "void CWeaponPistol::Precache( void )\n{\n\tBaseClass::Precache();\n}\n\n"
        "#ifndef CLIENT_DLL\n"
        "void CWeaponPistol::Operator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator )\n"
        "{\n"
        "\tswitch ( pEvent->event )\n"
        "\t{\n"
        "\t\tcase EVENT_WEAPON_PISTOL_FIRE:\n"
        "\t\t{\n"
        "\t\t\tCAI_BaseNPC *npc = pOperator->MyNPCPointer();\n"
        "\t\t\tASSERT( npc != NULL );\n"
        "\t\t\tif ( !npc )\n"
        "\t\t\t\treturn;\n\n"
        "\t\t\tVector vecShootOrigin = pOperator->Weapon_ShootPosition();\n"
        "\t\t\tVector vecShootDir = npc->GetActualShootTrajectory( vecShootOrigin );\n\n"
        "\t\t\tCSoundEnt::InsertSound( SOUND_COMBAT | SOUND_CONTEXT_GUNFIRE, pOperator->GetAbsOrigin(), SOUNDENT_VOLUME_PISTOL, 0.2, pOperator, SOUNDENT_CHANNEL_WEAPON, pOperator->GetEnemy() );\n"
        "\t\t\tWeaponSound( SINGLE_NPC );\n"
        "\t\t\tpOperator->FireBullets( 1, vecShootOrigin, vecShootDir, VECTOR_CONE_PRECALCULATED, MAX_TRACE_LENGTH, m_iPrimaryAmmoType, 2 );\n"
        "\t\t\tpOperator->DoMuzzleFlash();\n"
        "\t\t\tm_iClip1 = m_iClip1 - 1;\n"
        "\t\t}\n"
        "\t\tbreak;\n"
        "\t\tdefault:\n"
        "\t\t\tBaseClass::Operator_HandleAnimEvent( pEvent, pOperator );\n"
        "\t\t\tbreak;\n"
        "\t}\n"
        "}\n"
        "#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_smg1.cpp",
        "#else\n\t#include \"grenade_ar2.h\"\n\t#include \"hl2mp_player.h\"\n\t#include \"basegrenade_shared.h\"\n#endif",
        "#else\n\t#include \"grenade_ar2.h\"\n\t#include \"hl2mp_player.h\"\n\t#include \"basegrenade_shared.h\"\n\t#include \"soundent.h\"\n\t#include \"ai_basenpc.h\"\n#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_smg1.cpp",
        "#ifndef CLIENT_DLL\n\tDECLARE_ACTTABLE();\n#endif\n\nprotected:\n\n\tVector\tm_vecTossVelocity;",
        "#ifndef CLIENT_DLL\n"
        "\tvoid\tFireNPCPrimaryAttack( CBaseCombatCharacter *pOperator, Vector &vecShootOrigin, Vector &vecShootDir );\n"
        "\tvoid\tOperator_ForceNPCFire( CBaseCombatCharacter *pOperator, bool bSecondary );\n"
        "\tvoid\tOperator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator );\n"
        "\tDECLARE_ACTTABLE();\n"
        "#endif\n\nprotected:\n\n\tVector\tm_vecTossVelocity;",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_smg1.cpp",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_SMG1,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_SMG1,\t\t\t\t\tfalse },\n};",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_SMG1,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_SMG1,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RELOAD,\t\t\t\t\t\tACT_RELOAD_SMG1,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE,\t\t\t\t\t\t\tACT_IDLE_SMG1,\t\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_ANGRY,\t\t\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK,\t\t\t\t\t\t\tACT_WALK_RIFLE,\t\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_AIM,\t\t\t\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_RELAXED,\t\t\t\t\tACT_IDLE_SMG1_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_STIMULATED,\t\t\t\tACT_IDLE_SMG1_STIMULATED,\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AGITATED,\t\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_RELAXED,\t\t\t\t\tACT_WALK_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_STIMULATED,\t\t\t\tACT_WALK_RIFLE_STIMULATED,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AGITATED,\t\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_RELAXED,\t\t\t\t\tACT_RUN_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_STIMULATED,\t\t\t\tACT_RUN_RIFLE_STIMULATED,\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AGITATED,\t\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_RELAXED,\t\t\t\tACT_IDLE_SMG1_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_STIMULATED,\t\t\tACT_IDLE_AIM_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_AGITATED,\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_RELAXED,\t\t\t\tACT_WALK_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_STIMULATED,\t\t\tACT_WALK_AIM_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_AGITATED,\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_RELAXED,\t\t\t\tACT_RUN_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_STIMULATED,\t\t\tACT_RUN_AIM_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_AGITATED,\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_CROUCH,\t\t\t\t\tACT_WALK_CROUCH_RIFLE,\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_CROUCH_AIM,\t\t\t\tACT_WALK_CROUCH_AIM_RIFLE,\t\t\t\ttrue },\n"
        "\t{ ACT_RUN,\t\t\t\t\t\t\tACT_RUN_RIFLE,\t\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_AIM,\t\t\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH,\t\t\t\t\tACT_RUN_CROUCH_RIFLE,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH_AIM,\t\t\t\tACT_RUN_CROUCH_AIM_RIFLE,\t\t\t\ttrue },\n"
        "\t{ ACT_GESTURE_RANGE_ATTACK1,\t\tACT_GESTURE_RANGE_ATTACK_SMG1,\t\t\ttrue },\n"
        "\t{ ACT_RANGE_ATTACK1_LOW,\t\t\tACT_RANGE_ATTACK_SMG1_LOW,\t\t\t\ttrue },\n"
        "\t{ ACT_COVER_LOW,\t\t\t\t\tACT_COVER_SMG1_LOW,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_AIM_LOW,\t\t\t\tACT_RANGE_AIM_SMG1_LOW,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RELOAD_LOW,\t\t\t\t\tACT_RELOAD_SMG1_LOW,\t\t\t\t\tfalse },\n"
        "\t{ ACT_GESTURE_RELOAD,\t\t\t\tACT_GESTURE_RELOAD_SMG1,\t\t\t\ttrue },\n};",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_smg1.cpp",
        "void CWeaponSMG1::Equip( CBaseCombatCharacter *pOwner )\n"
        "{\n"
        "\tm_fMaxRange1 = 1400;\n\n"
        "\tBaseClass::Equip( pOwner );\n"
        "}",
        "void CWeaponSMG1::Equip( CBaseCombatCharacter *pOwner )\n"
        "{\n"
        "\tm_fMaxRange1 = 1400;\n\n"
        "\tBaseClass::Equip( pOwner );\n"
        "}\n\n"
        "#ifndef CLIENT_DLL\n"
        "void CWeaponSMG1::FireNPCPrimaryAttack( CBaseCombatCharacter *pOperator, Vector &vecShootOrigin, Vector &vecShootDir )\n"
        "{\n"
        "\tWeaponSoundRealtime( SINGLE_NPC );\n"
        "\tCSoundEnt::InsertSound( SOUND_COMBAT | SOUND_CONTEXT_GUNFIRE, pOperator->GetAbsOrigin(), SOUNDENT_VOLUME_MACHINEGUN, 0.2, pOperator, SOUNDENT_CHANNEL_WEAPON, pOperator->GetEnemy() );\n"
        "\tpOperator->FireBullets( 1, vecShootOrigin, vecShootDir, VECTOR_CONE_PRECALCULATED,\n"
        "\t\tMAX_TRACE_LENGTH, m_iPrimaryAmmoType, 2, entindex(), 0 );\n"
        "\tpOperator->DoMuzzleFlash();\n"
        "\tm_iClip1 = m_iClip1 - 1;\n"
        "}\n\n"
        "void CWeaponSMG1::Operator_ForceNPCFire( CBaseCombatCharacter *pOperator, bool bSecondary )\n"
        "{\n"
        "\tm_iClip1++;\n"
        "\tVector vecShootOrigin, vecShootDir;\n"
        "\tQAngle angShootDir;\n"
        '\tGetAttachment( LookupAttachment( "muzzle" ), vecShootOrigin, angShootDir );\n'
        "\tAngleVectors( angShootDir, &vecShootDir );\n"
        "\tFireNPCPrimaryAttack( pOperator, vecShootOrigin, vecShootDir );\n"
        "}\n\n"
        "void CWeaponSMG1::Operator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator )\n"
        "{\n"
        "\tswitch ( pEvent->event )\n"
        "\t{\n"
        "\t\tcase EVENT_WEAPON_SMG1:\n"
        "\t\t{\n"
        "\t\t\tVector vecShootOrigin, vecShootDir;\n"
        "\t\t\tQAngle angDiscard;\n\n"
        "\t\t\tif ( (pEvent->options == NULL) || (pEvent->options[0] == '\\0') || (!pOperator->GetAttachment( pEvent->options, vecShootOrigin, angDiscard )) )\n"
        "\t\t\t{\n"
        "\t\t\t\tvecShootOrigin = pOperator->Weapon_ShootPosition();\n"
        "\t\t\t}\n\n"
        "\t\t\tCAI_BaseNPC *npc = pOperator->MyNPCPointer();\n"
        "\t\t\tASSERT( npc != NULL );\n"
        "\t\t\tif ( !npc )\n"
        "\t\t\t\treturn;\n"
        "\t\t\tvecShootDir = npc->GetActualShootTrajectory( vecShootOrigin );\n"
        "\t\t\tFireNPCPrimaryAttack( pOperator, vecShootOrigin, vecShootDir );\n"
        "\t\t}\n"
        "\t\tbreak;\n"
        "\t\tdefault:\n"
        "\t\t\tBaseClass::Operator_HandleAnimEvent( pEvent, pOperator );\n"
        "\t\t\tbreak;\n"
        "\t}\n"
        "}\n"
        "#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_ar2.h",
        "#ifndef CLIENT_DLL\n\tDECLARE_ACTTABLE();\n#endif",
        "#ifndef CLIENT_DLL\n"
        "\tvoid\tFireNPCPrimaryAttack( CBaseCombatCharacter *pOperator, bool bUseWeaponAngles );\n"
        "\tvoid\tFireNPCSecondaryAttack( CBaseCombatCharacter *pOperator, bool bUseWeaponAngles );\n"
        "\tvoid\tOperator_ForceNPCFire( CBaseCombatCharacter *pOperator, bool bSecondary );\n"
        "\tvoid\tOperator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator );\n"
        "\tDECLARE_ACTTABLE();\n#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_ar2.cpp",
        "#else\n\t#include \"hl2mp_player.h\"\n\t#include \"te_effect_dispatch.h\"\n\t#include \"prop_combine_ball.h\"\n#endif",
        "#else\n\t#include \"hl2mp_player.h\"\n\t#include \"te_effect_dispatch.h\"\n\t#include \"prop_combine_ball.h\"\n\t#include \"soundent.h\"\n\t#include \"ai_basenpc.h\"\n\t#include \"npc_combine.h\"\n#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_ar2.cpp",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_AR2,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_AR2,\t\t\t\tfalse },\n};",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_AR2,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_AR2,\t\t\t\ttrue },\n"
        "\t{ ACT_RELOAD,\t\t\t\t\t\tACT_RELOAD_SMG1,\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE,\t\t\t\t\t\t\tACT_IDLE_SMG1,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_ANGRY,\t\t\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\ttrue },\n"
        "\t{ ACT_WALK,\t\t\t\t\t\t\tACT_WALK_RIFLE,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_RELAXED,\t\t\t\t\tACT_IDLE_SMG1_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_STIMULATED,\t\t\t\tACT_IDLE_SMG1_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AGITATED,\t\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_RELAXED,\t\t\t\t\tACT_WALK_RIFLE_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_STIMULATED,\t\t\t\tACT_WALK_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_WALK_AGITATED,\t\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_RELAXED,\t\t\t\t\tACT_RUN_RIFLE_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_STIMULATED,\t\t\t\tACT_RUN_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_RUN_AGITATED,\t\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_RELAXED,\t\t\t\tACT_IDLE_SMG1_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_STIMULATED,\t\t\tACT_IDLE_AIM_RIFLE_STIMULATED,\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_AGITATED,\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_RELAXED,\t\t\t\tACT_WALK_RIFLE_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_STIMULATED,\t\t\tACT_WALK_AIM_RIFLE_STIMULATED,\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_AGITATED,\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_RELAXED,\t\t\t\tACT_RUN_RIFLE_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_STIMULATED,\t\t\tACT_RUN_AIM_RIFLE_STIMULATED,\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_AGITATED,\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM,\t\t\t\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_CROUCH,\t\t\t\t\tACT_WALK_CROUCH_RIFLE,\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_CROUCH_AIM,\t\t\t\tACT_WALK_CROUCH_AIM_RIFLE,\t\t\ttrue },\n"
        "\t{ ACT_RUN,\t\t\t\t\t\t\tACT_RUN_RIFLE,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_AIM,\t\t\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH,\t\t\t\t\tACT_RUN_CROUCH_RIFLE,\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH_AIM,\t\t\t\tACT_RUN_CROUCH_AIM_RIFLE,\t\t\ttrue },\n"
        "\t{ ACT_GESTURE_RANGE_ATTACK1,\t\tACT_GESTURE_RANGE_ATTACK_AR2,\t\tfalse },\n"
        "\t{ ACT_COVER_LOW,\t\t\t\t\tACT_COVER_SMG1_LOW,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_AIM_LOW,\t\t\t\tACT_RANGE_AIM_AR2_LOW,\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1_LOW,\t\t\tACT_RANGE_ATTACK_SMG1_LOW,\t\t\ttrue },\n"
        "\t{ ACT_RELOAD_LOW,\t\t\t\t\tACT_RELOAD_SMG1_LOW,\t\t\t\tfalse },\n"
        "\t{ ACT_GESTURE_RELOAD,\t\t\t\tACT_GESTURE_RELOAD_SMG1,\t\t\ttrue },\n};",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_ar2.cpp",
        "\tUTIL_PrecacheOther( \"prop_combine_ball\" );\n\tUTIL_PrecacheOther( \"env_entity_dissolver\" );\n#endif\n\t\n}",
        "\tUTIL_PrecacheOther( \"prop_combine_ball\" );\n\tUTIL_PrecacheOther( \"env_entity_dissolver\" );\n#endif\n\t\n}\n\n"
        "#ifndef CLIENT_DLL\n"
        "void CWeaponAR2::FireNPCPrimaryAttack( CBaseCombatCharacter *pOperator, bool bUseWeaponAngles )\n"
        "{\n"
        "\tVector vecShootOrigin, vecShootDir;\n"
        "\tCAI_BaseNPC *npc = pOperator->MyNPCPointer();\n"
        "\tASSERT( npc != NULL );\n"
        "\tif ( !npc )\n"
        "\t\treturn;\n\n"
        "\tif ( bUseWeaponAngles )\n"
        "\t{\n"
        "\t\tQAngle angShootDir;\n"
        '\t\tGetAttachment( LookupAttachment( "muzzle" ), vecShootOrigin, angShootDir );\n'
        "\t\tAngleVectors( angShootDir, &vecShootDir );\n"
        "\t}\n"
        "\telse\n"
        "\t{\n"
        "\t\tvecShootOrigin = pOperator->Weapon_ShootPosition();\n"
        "\t\tvecShootDir = npc->GetActualShootTrajectory( vecShootOrigin );\n"
        "\t}\n\n"
        "\tWeaponSoundRealtime( SINGLE_NPC );\n"
        "\tCSoundEnt::InsertSound( SOUND_COMBAT | SOUND_CONTEXT_GUNFIRE, pOperator->GetAbsOrigin(), SOUNDENT_VOLUME_MACHINEGUN, 0.2, pOperator, SOUNDENT_CHANNEL_WEAPON, pOperator->GetEnemy() );\n"
        "\tpOperator->FireBullets( 1, vecShootOrigin, vecShootDir, VECTOR_CONE_PRECALCULATED, MAX_TRACE_LENGTH, m_iPrimaryAmmoType, 2 );\n"
        "\tpOperator->DoMuzzleFlash();\n"
        "\tm_iClip1 = m_iClip1 - 1;\n"
        "}\n\n"
        "void CWeaponAR2::FireNPCSecondaryAttack( CBaseCombatCharacter *pOperator, bool bUseWeaponAngles )\n"
        "{\n"
        "\tWeaponSound( WPN_DOUBLE );\n"
        "\tif ( !GetOwner() )\n"
        "\t\treturn;\n\n"
        "\tCAI_BaseNPC *pNPC = GetOwner()->MyNPCPointer();\n"
        "\tif ( !pNPC )\n"
        "\t\treturn;\n\n"
        "\tVector vecSrc, vecAiming;\n"
        "\tif ( bUseWeaponAngles )\n"
        "\t{\n"
        "\t\tQAngle angShootDir;\n"
        '\t\tGetAttachment( LookupAttachment( "muzzle" ), vecSrc, angShootDir );\n'
        "\t\tAngleVectors( angShootDir, &vecAiming );\n"
        "\t}\n"
        "\telse\n"
        "\t{\n"
        "\t\tvecSrc = pNPC->Weapon_ShootPosition();\n"
        "\t\tVector vecTarget;\n"
        "\t\tCNPC_Combine *pSoldier = dynamic_cast<CNPC_Combine *>( pNPC );\n"
        "\t\tif ( pSoldier )\n"
        "\t\t{\n"
        "\t\t\tvecTarget = pSoldier->GetAltFireTarget();\n"
        "\t\t}\n"
        "\t\telse\n"
        "\t\t{\n"
        "\t\t\tif ( !pNPC->GetEnemy() )\n"
        "\t\t\t\treturn;\n"
        "\t\t\tvecTarget = pNPC->GetEnemy()->BodyTarget( vecSrc );\n"
        "\t\t}\n"
        "\t\tvecAiming = vecTarget - vecSrc;\n"
        "\t\tVectorNormalize( vecAiming );\n"
        "\t}\n\n"
        "\tfloat flDuration = RemapValClamped( 1.0f, 0.0f, 1.0f, 0.5f, sk_weapon_ar2_alt_fire_duration.GetFloat() );\n"
        "\tfloat flRadius = RemapValClamped( 1.0f, 0.0f, 1.0f, 4.0f, sk_weapon_ar2_alt_fire_radius.GetFloat() );\n"
        "\tVector vecVelocity = vecAiming * 1000.0f;\n"
        "\tCreateCombineBall( vecSrc, vecVelocity, flRadius, sk_weapon_ar2_alt_fire_mass.GetFloat(), flDuration, pNPC );\n"
        "}\n\n"
        "void CWeaponAR2::Operator_ForceNPCFire( CBaseCombatCharacter *pOperator, bool bSecondary )\n"
        "{\n"
        "\tif ( bSecondary )\n"
        "\t{\n"
        "\t\tFireNPCSecondaryAttack( pOperator, true );\n"
        "\t}\n"
        "\telse\n"
        "\t{\n"
        "\t\tm_iClip1++;\n"
        "\t\tFireNPCPrimaryAttack( pOperator, true );\n"
        "\t}\n"
        "}\n\n"
        "void CWeaponAR2::Operator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator )\n"
        "{\n"
        "\tswitch ( pEvent->event )\n"
        "\t{\n"
        "\t\tcase EVENT_WEAPON_AR2:\n"
        "\t\t\tFireNPCPrimaryAttack( pOperator, false );\n"
        "\t\t\tbreak;\n"
        "\t\tcase EVENT_WEAPON_AR2_ALTFIRE:\n"
        "\t\t\tFireNPCSecondaryAttack( pOperator, false );\n"
        "\t\t\tbreak;\n"
        "\t\tdefault:\n"
        "\t\t\tCBaseCombatWeapon::Operator_HandleAnimEvent( pEvent, pOperator );\n"
        "\t\t\tbreak;\n"
        "\t}\n"
        "}\n"
        "#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_shotgun.cpp",
        "#else\n\t#include \"hl2mp_player.h\"\n#endif",
        "#else\n\t#include \"hl2mp_player.h\"\n\t#include \"soundent.h\"\n\t#include \"ai_basenpc.h\"\n#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_shotgun.cpp",
        "#ifndef CLIENT_DLL\n\tDECLARE_ACTTABLE();\n#endif\n\n\tCWeaponShotgun(void);",
        "#ifndef CLIENT_DLL\n"
        "\tvoid\tFireNPCPrimaryAttack( CBaseCombatCharacter *pOperator, bool bUseWeaponAngles );\n"
        "\tvoid\tOperator_ForceNPCFire( CBaseCombatCharacter *pOperator, bool bSecondary );\n"
        "\tvoid\tOperator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator );\n"
        "\tDECLARE_ACTTABLE();\n#endif\n\n\tCWeaponShotgun(void);",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_shotgun.cpp",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_SHOTGUN,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_SHOTGUN,\t\t\t\tfalse },\n};",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_SHOTGUN,\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE,\t\t\t\t\t\t\tACT_IDLE_SMG1,\t\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_SHOTGUN,\t\t\t\ttrue },\n"
        "\t{ ACT_RELOAD,\t\t\t\t\t\tACT_RELOAD_SHOTGUN,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK,\t\t\t\t\t\t\tACT_WALK_RIFLE,\t\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_ANGRY,\t\t\t\t\tACT_IDLE_ANGRY_SHOTGUN,\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_RELAXED,\t\t\t\t\tACT_IDLE_SHOTGUN_RELAXED,\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_STIMULATED,\t\t\t\tACT_IDLE_SHOTGUN_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AGITATED,\t\t\t\tACT_IDLE_SHOTGUN_AGITATED,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_RELAXED,\t\t\t\t\tACT_WALK_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_STIMULATED,\t\t\t\tACT_WALK_RIFLE_STIMULATED,\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AGITATED,\t\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_RELAXED,\t\t\t\t\tACT_RUN_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_STIMULATED,\t\t\t\tACT_RUN_RIFLE_STIMULATED,\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AGITATED,\t\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_RELAXED,\t\t\t\tACT_IDLE_SMG1_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_STIMULATED,\t\t\tACT_IDLE_AIM_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_IDLE_AIM_AGITATED,\t\t\tACT_IDLE_ANGRY_SMG1,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_RELAXED,\t\t\t\tACT_WALK_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_STIMULATED,\t\t\tACT_WALK_AIM_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM_AGITATED,\t\t\tACT_WALK_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_RELAXED,\t\t\t\tACT_RUN_RIFLE_RELAXED,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_STIMULATED,\t\t\tACT_RUN_AIM_RIFLE_STIMULATED,\t\t\tfalse },\n"
        "\t{ ACT_RUN_AIM_AGITATED,\t\t\t\tACT_RUN_AIM_RIFLE,\t\t\t\t\t\tfalse },\n"
        "\t{ ACT_WALK_AIM,\t\t\t\t\t\tACT_WALK_AIM_SHOTGUN,\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_CROUCH,\t\t\t\t\tACT_WALK_CROUCH_RIFLE,\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_CROUCH_AIM,\t\t\t\tACT_WALK_CROUCH_AIM_RIFLE,\t\t\t\ttrue },\n"
        "\t{ ACT_RUN,\t\t\t\t\t\t\tACT_RUN_RIFLE,\t\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_AIM,\t\t\t\t\t\tACT_RUN_AIM_SHOTGUN,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH,\t\t\t\t\tACT_RUN_CROUCH_RIFLE,\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH_AIM,\t\t\t\tACT_RUN_CROUCH_AIM_RIFLE,\t\t\t\ttrue },\n"
        "\t{ ACT_GESTURE_RANGE_ATTACK1,\t\tACT_GESTURE_RANGE_ATTACK_SHOTGUN,\t\ttrue },\n"
        "\t{ ACT_RANGE_ATTACK1_LOW,\t\t\tACT_RANGE_ATTACK_SHOTGUN_LOW,\t\t\ttrue },\n"
        "\t{ ACT_RELOAD_LOW,\t\t\t\t\tACT_RELOAD_SHOTGUN_LOW,\t\t\t\t\tfalse },\n"
        "\t{ ACT_GESTURE_RELOAD,\t\t\t\tACT_GESTURE_RELOAD_SHOTGUN,\t\t\t\tfalse },\n};",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_shotgun.cpp",
        "\tm_fMinRange1\t\t= 0.0;\n\tm_fMaxRange1\t\t= 500;\n\tm_fMinRange2\t\t= 0.0;\n\tm_fMaxRange2\t\t= 200;\n}",
        "\tm_fMinRange1\t\t= 0.0;\n\tm_fMaxRange1\t\t= 500;\n\tm_fMinRange2\t\t= 0.0;\n\tm_fMaxRange2\t\t= 200;\n}\n\n"
        "#ifndef CLIENT_DLL\n"
        "void CWeaponShotgun::FireNPCPrimaryAttack( CBaseCombatCharacter *pOperator, bool bUseWeaponAngles )\n"
        "{\n"
        "\tVector vecShootOrigin, vecShootDir;\n"
        "\tCAI_BaseNPC *npc = pOperator->MyNPCPointer();\n"
        "\tASSERT( npc != NULL );\n"
        "\tif ( !npc )\n"
        "\t\treturn;\n\n"
        "\tWeaponSound( SINGLE_NPC );\n"
        "\tCSoundEnt::InsertSound( SOUND_COMBAT | SOUND_CONTEXT_GUNFIRE, pOperator->GetAbsOrigin(), SOUNDENT_VOLUME_SHOTGUN, 0.2, pOperator, SOUNDENT_CHANNEL_WEAPON, pOperator->GetEnemy() );\n"
        "\tpOperator->DoMuzzleFlash();\n"
        "\tm_iClip1 = m_iClip1 - 1;\n\n"
        "\tif ( bUseWeaponAngles )\n"
        "\t{\n"
        "\t\tQAngle angShootDir;\n"
        '\t\tGetAttachment( LookupAttachment( "muzzle" ), vecShootOrigin, angShootDir );\n'
        "\t\tAngleVectors( angShootDir, &vecShootDir );\n"
        "\t}\n"
        "\telse\n"
        "\t{\n"
        "\t\tvecShootOrigin = pOperator->Weapon_ShootPosition();\n"
        "\t\tvecShootDir = npc->GetActualShootTrajectory( vecShootOrigin );\n"
        "\t}\n\n"
        "\tpOperator->FireBullets( 8, vecShootOrigin, vecShootDir, GetBulletSpread(), MAX_TRACE_LENGTH, m_iPrimaryAmmoType, 0 );\n"
        "}\n\n"
        "void CWeaponShotgun::Operator_ForceNPCFire( CBaseCombatCharacter *pOperator, bool bSecondary )\n"
        "{\n"
        "\tm_iClip1++;\n"
        "\tFireNPCPrimaryAttack( pOperator, true );\n"
        "}\n\n"
        "void CWeaponShotgun::Operator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator )\n"
        "{\n"
        "\tswitch ( pEvent->event )\n"
        "\t{\n"
        "\t\tcase EVENT_WEAPON_SHOTGUN_FIRE:\n"
        "\t\t\tFireNPCPrimaryAttack( pOperator, false );\n"
        "\t\t\tbreak;\n"
        "\t\tdefault:\n"
        "\t\t\tCBaseCombatWeapon::Operator_HandleAnimEvent( pEvent, pOperator );\n"
        "\t\t\tbreak;\n"
        "\t}\n"
        "}\n"
        "#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_rpg.h",
        "#ifndef CLIENT_DLL\n\tDECLARE_ACTTABLE();\n#endif",
        "#ifndef CLIENT_DLL\n"
        "\tvoid\tOperator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator );\n"
        "\tDECLARE_ACTTABLE();\n#endif",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_rpg.cpp",
        '\t#include "collisionutils.h"\n\t#include "hl2_shareddefs.h"\n#endif',
        '\t#include "collisionutils.h"\n\t#include "hl2_shareddefs.h"\n\t#include "ai_basenpc.h"\n#endif',
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_rpg.cpp",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_RPG,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_RPG,\t\t\t\tfalse },\n};",
        "\t{ ACT_HL2MP_JUMP,\t\t\t\t\tACT_HL2MP_JUMP_RPG,\t\t\t\t\tfalse },\n"
        "\t{ ACT_RANGE_ATTACK1,\t\t\t\tACT_RANGE_ATTACK_RPG,\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_RELAXED,\t\t\t\t\tACT_IDLE_RPG_RELAXED,\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_STIMULATED,\t\t\t\tACT_IDLE_ANGRY_RPG,\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_AGITATED,\t\t\t\tACT_IDLE_ANGRY_RPG,\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE,\t\t\t\t\t\t\tACT_IDLE_RPG,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_IDLE_ANGRY,\t\t\t\t\tACT_IDLE_ANGRY_RPG,\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK,\t\t\t\t\t\t\tACT_WALK_RPG,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_WALK_CROUCH,\t\t\t\t\tACT_WALK_CROUCH_RPG,\t\t\t\ttrue },\n"
        "\t{ ACT_RUN,\t\t\t\t\t\t\tACT_RUN_RPG,\t\t\t\t\t\ttrue },\n"
        "\t{ ACT_RUN_CROUCH,\t\t\t\t\tACT_RUN_CROUCH_RPG,\t\t\t\t\ttrue },\n"
        "\t{ ACT_COVER_LOW,\t\t\t\t\tACT_COVER_LOW_RPG,\t\t\t\t\ttrue },\n};",
    )

    replace_once(
        src / "game/shared/hl2mp/weapon_rpg.cpp",
        "#ifndef CLIENT_DLL\n\tUTIL_PrecacheOther( \"rpg_missile\" );\n#endif\n\n}",
        "#ifndef CLIENT_DLL\n\tUTIL_PrecacheOther( \"rpg_missile\" );\n#endif\n\n}\n\n"
        "#ifndef CLIENT_DLL\n"
        "void CWeaponRPG::Operator_HandleAnimEvent( animevent_t *pEvent, CBaseCombatCharacter *pOperator )\n"
        "{\n"
        "\tswitch ( pEvent->event )\n"
        "\t{\n"
        "\t\tcase EVENT_WEAPON_SMG1:\n"
        "\t\t{\n"
        "\t\t\tif ( m_hMissile != NULL )\n"
        "\t\t\t\treturn;\n\n"
        "\t\t\tCAI_BaseNPC *npc = pOperator->MyNPCPointer();\n"
        "\t\t\tASSERT( npc != NULL );\n"
        "\t\t\tif ( !npc )\n"
        "\t\t\t\treturn;\n\n"
        "\t\t\tVector muzzlePoint = GetOwner()->Weapon_ShootPosition();\n"
        "\t\t\tVector vecShootDir = npc->GetActualShootTrajectory( muzzlePoint );\n\n"
        "\t\t\tVector altLaunchPoint;\n"
        '\t\t\tif ( GetAttachment( "missile", altLaunchPoint ) )\n'
        "\t\t\t{\n"
        "\t\t\t\ttrace_t tr;\n"
        "\t\t\t\tAI_TraceHull( altLaunchPoint, altLaunchPoint + vecShootDir * (10.0f * 12.0f), Vector( -24, -24, -24 ), Vector( 24, 24, 24 ), MASK_NPCSOLID, NULL, &tr );\n"
        "\t\t\t\tif ( tr.fraction == 1.0 )\n"
        "\t\t\t\t{\n"
        "\t\t\t\t\tmuzzlePoint = altLaunchPoint;\n"
        "\t\t\t\t}\n"
        "\t\t\t}\n\n"
        "\t\t\tQAngle vecAngles;\n"
        "\t\t\tVectorAngles( vecShootDir, vecAngles );\n\n"
        "\t\t\tm_hMissile = CMissile::Create( muzzlePoint, vecAngles, GetOwner()->edict() );\n"
        "\t\t\tm_hMissile->m_hOwner = this;\n"
        "\t\t\tm_hMissile->SetGracePeriod( 0.5 );\n\n"
        "\t\t\tpOperator->DoMuzzleFlash();\n"
        "\t\t\tWeaponSound( SINGLE_NPC );\n"
        "\t\t\tm_bGuiding = false;\n"
        "\t\t\tif ( m_hLaserDot )\n"
        "\t\t\t{\n"
        "\t\t\t\tm_hLaserDot->TurnOff();\n"
        "\t\t\t}\n"
        "\t\t}\n"
        "\t\tbreak;\n"
        "\t\tdefault:\n"
        "\t\t\tBaseClass::Operator_HandleAnimEvent( pEvent, pOperator );\n"
        "\t\t\tbreak;\n"
        "\t}\n"
        "}\n"
        "#endif",
    )


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_sdk_x64.py <sdk_src_dir>")
    patch_sdk(pathlib.Path(sys.argv[1]).resolve())
    print("Patched Source SDK 2013 x64 cleanly.")


if __name__ == "__main__":
    main()
