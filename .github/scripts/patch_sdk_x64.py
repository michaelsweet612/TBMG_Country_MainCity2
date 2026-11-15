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


def main() -> None:
    if len(sys.argv) != 2:
        raise SystemExit("Usage: patch_sdk_x64.py <sdk_src_dir>")
    patch_sdk(pathlib.Path(sys.argv[1]).resolve())
    print("Patched Source SDK 2013 x64 cleanly.")


if __name__ == "__main__":
    main()
