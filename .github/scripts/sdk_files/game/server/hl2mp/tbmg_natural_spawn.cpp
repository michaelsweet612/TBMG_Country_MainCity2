//========= Copyright TBMG, All rights reserved. ==========================//
//
// Purpose: Naturally spawns mobile HL2 NPCs near walkable map AI ground nodes
//          around active players while keeping spawns clear of walls, player
//          spawn zones, and ammo pickups, and maintaining city-wide faction
//          territories (Civilians vs. Metrocops) and Power Plant patrols.
//
//=============================================================================//

#include "cbase.h"
#include "tbmg_natural_spawn.h"
#include "ai_basenpc.h"
#include "ai_default.h"
#include "ai_hull.h"
#include "ai_network.h"
#include "ai_node.h"
#include "datacache/imdlcache.h"
#include "entitylist.h"

// memdbgon must be the last include file in a .cpp file!!!
#include "tier0/memdbgon.h"

extern ConVar tbmg_natural_spawn;
extern ConVar tbmg_natural_spawn_interval;
extern ConVar tbmg_natural_spawn_max;

namespace
{
	struct NaturalSpawnEntry_t
	{
		const char *pszClassname;
		const char *pszWeapon;
		const char *pszModel;
		Hull_t      nHull;
		float       flExtraZ;
		int         iWeight;
		bool        bUnique;
	};

	// Mobile HL2 NPCs partitioned by faction (never spawn ammo crates/pickups or static props).
	const NaturalSpawnEntry_t s_CitizenPool[] =
	{
		{ "npc_citizen",     "weapon_smg1",    NULL,                              HULL_HUMAN,         0.0f,  6, false },
		{ "npc_citizen",     "weapon_ar2",     NULL,                              HULL_HUMAN,         0.0f,  4, false },
		{ "npc_citizen",     "weapon_shotgun", NULL,                              HULL_HUMAN,         0.0f,  3, false },
		{ "npc_citizen",     "weapon_pistol",  NULL,                              HULL_HUMAN,         0.0f,  2, false },
		{ "npc_citizen",     "weapon_rpg",     NULL,                              HULL_HUMAN,         0.0f,  1, false },
		{ "npc_vortigaunt",  NULL,             NULL,                              HULL_WIDE_HUMAN,    0.0f,  2, false },
		{ "npc_monk",        "weapon_shotgun", NULL,                              HULL_HUMAN,         0.0f,  1, true  },
		{ "npc_alyx",        "weapon_alyxgun", NULL,                              HULL_HUMAN,         0.0f,  1, true  },
		{ "npc_barney",      "weapon_ar2",     NULL,                              HULL_HUMAN,         0.0f,  1, true  },
		{ "npc_dog",         NULL,             NULL,                              HULL_WIDE_HUMAN,    0.0f,  1, true  },
	};

	const NaturalSpawnEntry_t s_MetrocopPool[] =
	{
		{ "npc_metropolice", "weapon_smg1",    NULL,                              HULL_HUMAN,         0.0f,  7, false },
		{ "npc_metropolice", "weapon_pistol",  NULL,                              HULL_HUMAN,         0.0f,  4, false },
		{ "npc_combine_s",   "weapon_ar2",     "models/combine_super_soldier.mdl",HULL_HUMAN,         0.0f,  2, false },
		{ "npc_manhack",     NULL,             NULL,                              HULL_TINY_CENTERED, 48.0f, 2, false },
		{ "npc_cscanner",    NULL,             NULL,                              HULL_TINY_CENTERED, 64.0f, 1, false },
		{ "npc_clawscanner", NULL,             NULL,                              HULL_TINY_CENTERED, 64.0f, 1, false },
		{ "npc_rollermine",  NULL,             NULL,                              HULL_SMALL_CENTERED,0.0f,  1, false },
	};

	const NaturalSpawnEntry_t s_PowerPlantSoldierPool[] =
	{
		{ "npc_combine_s",   "weapon_ar2",     "models/combine_soldier.mdl",      HULL_HUMAN,         0.0f,  4, false },
		{ "npc_combine_s",   "weapon_shotgun", "models/combine_soldier.mdl",      HULL_HUMAN,         0.0f,  2, false },
		{ "npc_combine_s",   "weapon_ar2",     "models/combine_super_soldier.mdl",HULL_HUMAN,         0.0f,  2, false },
		{ "npc_rollermine",  NULL,             NULL,                              HULL_SMALL_CENTERED,0.0f,  1, false },
	};

	const NaturalSpawnEntry_t s_MonsterPool[] =
	{
		{ "npc_zombie",        NULL, NULL, HULL_HUMAN,  0.0f, 3, false },
		{ "npc_fastzombie",    NULL, NULL, HULL_HUMAN,  0.0f, 3, false },
		{ "npc_poisonzombie",  NULL, NULL, HULL_HUMAN,  0.0f, 1, false },
		{ "npc_headcrab",      NULL, NULL, HULL_TINY,   0.0f, 2, false },
		{ "npc_headcrab_fast", NULL, NULL, HULL_TINY,   0.0f, 2, false },
		{ "npc_headcrab_black",NULL, NULL, HULL_TINY,   0.0f, 1, false },
		{ "npc_antlion",       NULL, NULL, HULL_MEDIUM, 0.0f, 3, false },
	};

	const float TBMG_SPAWN_MIN_PLAYER_DIST    = 950.0f;
	const float TBMG_SPAWN_MAX_PLAYER_DIST    = 4200.0f;
	const float TBMG_SPAWN_MIN_MAP_SPAWN_DIST = 600.0f;
	const float TBMG_SPAWN_MIN_NPC_SPACING    = 280.0f;
	const float TBMG_SPAWN_DESPAWN_DIST       = 5500.0f;
	const float TBMG_PATROL_UPDATE_INTERVAL   = 4.0f;
	const float TBMG_WALL_CLEARANCE_RADIUS    = 12.0f;
	const int   TBMG_MAX_ENTITY_SAFE_CAP      = 1600;
	const int   TBMG_SPAWN_ATTEMPTS           = 10;

	// gm_bigcity territorial partitions matching pre-placed fronts and Power Plant yard.
	const float BIGCITY_CITIZEN_WEST_MAX_X = 1350.0f;
	const float BIGCITY_COMBINE_EAST_MIN_X = 1800.0f;
	const float BIGCITY_PP_MIN_X           = 7200.0f;
	const float BIGCITY_PP_MAX_X           = 11400.0f;
	const float BIGCITY_PP_MIN_Y           = 8800.0f;
	const float BIGCITY_PP_MAX_Y           = 11500.0f;

	CUtlVector< EHANDLE > s_TrackedNPCs;
	float s_flNextSpawnTime = 0.0f;
	float s_flNextPatrolUpdateTime = 0.0f;
	int   s_nTotalSpawned = 0;
	int   s_nSkippedStuck = 0;
	int   s_nLastCandidateCount = 0;
	bool  s_bLastNodeCheckLinked = true;
}

static bool IsBigCityMap( void )
{
	return gpGlobals && gpGlobals->mapname != NULL_STRING && Q_stristr( STRING( gpGlobals->mapname ), "gm_bigcity" ) != NULL;
}

static bool IsPowerPlantPoint( const Vector &pos )
{
	return pos.x >= BIGCITY_PP_MIN_X && pos.x <= BIGCITY_PP_MAX_X &&
	       pos.y >= BIGCITY_PP_MIN_Y && pos.y <= BIGCITY_PP_MAX_Y;
}

static int GatherActivePlayers( CUtlVector< CBasePlayer * > &players )
{
	players.RemoveAll();
	for ( int i = 1; i <= gpGlobals->maxClients; ++i )
	{
		CBasePlayer *pPlayer = UTIL_PlayerByIndex( i );
		if ( !pPlayer || !pPlayer->IsAlive() )
			continue;

		players.AddToTail( pPlayer );
	}
	return players.Count();
}

static float MinDistSqrToPlayers( const Vector &pos, const CUtlVector< CBasePlayer * > &players )
{
	float flBestSqr = FLT_MAX;
	for ( int i = 0; i < players.Count(); ++i )
	{
		float flDistSqr = pos.DistToSqr( players[i]->GetAbsOrigin() );
		if ( flDistSqr < flBestSqr )
		{
			flBestSqr = flDistSqr;
		}
	}
	return flBestSqr;
}

static void PruneTrackedNPCs( const CUtlVector< CBasePlayer * > &players )
{
	const float flDespawnDistSqr = TBMG_SPAWN_DESPAWN_DIST * TBMG_SPAWN_DESPAWN_DIST;

	for ( int i = s_TrackedNPCs.Count() - 1; i >= 0; --i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		CAI_BaseNPC *pNPC = pEnt ? pEnt->MyNPCPointer() : NULL;
		if ( !pNPC || pNPC->IsMarkedForDeletion() || !pNPC->IsAlive() )
		{
			s_TrackedNPCs.FastRemove( i );
			continue;
		}

		if ( players.Count() > 0 && MinDistSqrToPlayers( pNPC->GetAbsOrigin(), players ) > flDespawnDistSqr )
		{
			UTIL_Remove( pNPC );
			s_TrackedNPCs.FastRemove( i );
		}
	}
}

static void NudgeNPCIntoPatrol( CAI_BaseNPC *pNPC, bool bUseCombinePatrol )
{
	if ( !pNPC || !pNPC->IsAlive() || pNPC->IsMarkedForDeletion() )
		return;

	if ( pNPC->GetEnemy() != NULL || pNPC->GetState() != NPC_STATE_IDLE || pNPC->IsMoving() )
		return;

	if ( bUseCombinePatrol )
	{
		variant_t emptyVar;
		pNPC->AcceptInput( "StartPatrolling", NULL, NULL, emptyVar, 0 );
		if ( pNPC->IsMoving() )
			return;
	}

	pNPC->SetSchedule( SCHED_PATROL_WALK );
}

// Keep pre-placed Power Plant Combine Soldiers, city patrol NPCs, and tracked spawns roaming when idle.
static void TBMG_UpdatePatrollingNPCs( void )
{
	if ( !gpGlobals || gpGlobals->curtime < s_flNextPatrolUpdateTime )
		return;

	s_flNextPatrolUpdateTime = gpGlobals->curtime + TBMG_PATROL_UPDATE_INTERVAL;

	for ( CBaseEntity *pEnt = gEntList.FindEntityByName( NULL, "tbmg_pp_soldier_*" ); pEnt != NULL; pEnt = gEntList.FindEntityByName( pEnt, "tbmg_pp_soldier_*" ) )
	{
		NudgeNPCIntoPatrol( pEnt->MyNPCPointer(), true );
	}

	for ( CBaseEntity *pEnt = gEntList.FindEntityByName( NULL, "tbmg_patrol_*" ); pEnt != NULL; pEnt = gEntList.FindEntityByName( pEnt, "tbmg_patrol_*" ) )
	{
		NudgeNPCIntoPatrol( pEnt->MyNPCPointer(), false );
	}

	for ( int i = 0; i < s_TrackedNPCs.Count(); ++i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		CAI_BaseNPC *pNPC = pEnt ? pEnt->MyNPCPointer() : NULL;
		if ( pNPC )
		{
			NudgeNPCIntoPatrol( pNPC, FClassnameIs( pNPC, "npc_combine_s" ) );
		}
	}
}

static bool IsNearAnyMapSpawnPoint( const Vector &pos )
{
	const float flMinDistSqr = TBMG_SPAWN_MIN_MAP_SPAWN_DIST * TBMG_SPAWN_MIN_MAP_SPAWN_DIST;
	for ( CBaseEntity *pSpawn = gEntList.FindEntityByClassname( NULL, "info_player_*" ); pSpawn != NULL; pSpawn = gEntList.FindEntityByClassname( pSpawn, "info_player_*" ) )
	{
		if ( pos.DistToSqr( pSpawn->GetAbsOrigin() ) < flMinDistSqr )
			return true;
	}
	return false;
}

static bool IsTooCloseToExistingNPC( const Vector &pos )
{
	const float flTrackedMinDistSqr = TBMG_SPAWN_MIN_NPC_SPACING * TBMG_SPAWN_MIN_NPC_SPACING;
	for ( int i = 0; i < s_TrackedNPCs.Count(); ++i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		if ( !pEnt || !pEnt->IsAlive() )
			continue;

		if ( pos.DistToSqr( pEnt->GetAbsOrigin() ) < flTrackedMinDistSqr )
			return true;
	}

	const float flStaticMinDistSqr = 200.0f * 200.0f;
	for ( CBaseEntity *pEnt = gEntList.FindEntityByClassname( NULL, "npc_*" ); pEnt != NULL; pEnt = gEntList.FindEntityByClassname( pEnt, "npc_*" ) )
	{
		if ( !pEnt->IsAlive() )
			continue;

		if ( pos.DistToSqr( pEnt->GetAbsOrigin() ) < flStaticMinDistSqr )
			return true;
	}
	return false;
}

static bool IsTooCloseToAnyPlayerHull( const Vector &pos, const CUtlVector< CBasePlayer * > &players )
{
	const float flMinDistSqr = TBMG_SPAWN_MIN_PLAYER_DIST * TBMG_SPAWN_MIN_PLAYER_DIST;
	for ( int i = 0; i < players.Count(); ++i )
	{
		if ( pos.DistToSqr( players[i]->GetAbsOrigin() ) < flMinDistSqr )
			return true;
	}
	return false;
}

static bool HasLiveEntityOfClass( const char *pszClassname )
{
	for ( CBaseEntity *pEnt = gEntList.FindEntityByClassname( NULL, pszClassname ); pEnt != NULL; pEnt = gEntList.FindEntityByClassname( pEnt, pszClassname ) )
	{
		if ( !pEnt->IsMarkedForDeletion() && pEnt->IsAlive() )
			return true;
	}
	return false;
}

static bool IsResistanceClassname( const char *pszClassname )
{
	return Q_stricmp( pszClassname, "npc_citizen" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_vortigaunt" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_monk" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_alyx" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_barney" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_dog" ) == 0;
}

static bool IsCombineClassname( const char *pszClassname )
{
	return Q_stricmp( pszClassname, "npc_metropolice" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_combine_s" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_manhack" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_cscanner" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_clawscanner" ) == 0 ||
	       Q_stricmp( pszClassname, "npc_rollermine" ) == 0;
}

static const NaturalSpawnEntry_t &PickWeightedFromPool( const NaturalSpawnEntry_t *pPool, int nCount )
{
	int nTotalWeight = 0;
	for ( int i = 0; i < nCount; ++i )
	{
		if ( pPool[i].bUnique && HasLiveEntityOfClass( pPool[i].pszClassname ) )
			continue;
		nTotalWeight += pPool[i].iWeight;
	}

	if ( nTotalWeight <= 0 )
		return pPool[0];

	int nRoll = RandomInt( 0, nTotalWeight - 1 );
	for ( int i = 0; i < nCount; ++i )
	{
		if ( pPool[i].bUnique && HasLiveEntityOfClass( pPool[i].pszClassname ) )
			continue;
		nRoll -= pPool[i].iWeight;
		if ( nRoll < 0 )
			return pPool[i];
	}

	return pPool[0];
}

static void CountTrackedFactions( int &outCivilians, int &outCombine )
{
	outCivilians = 0;
	outCombine = 0;

	for ( int i = 0; i < s_TrackedNPCs.Count(); ++i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		if ( !pEnt || !pEnt->IsAlive() )
			continue;

		const char *pszClass = pEnt->GetClassname();
		if ( IsResistanceClassname( pszClass ) )
		{
			++outCivilians;
		}
		else if ( IsCombineClassname( pszClass ) )
		{
			++outCombine;
		}
	}
}

static const NaturalSpawnEntry_t &PickEntryForPosition( const Vector &pos, bool &outPowerPlantSoldier )
{
	outPowerPlantSoldier = false;

	if ( IsBigCityMap() )
	{
		if ( IsPowerPlantPoint( pos ) )
		{
			outPowerPlantSoldier = true;
			return PickWeightedFromPool( s_PowerPlantSoldierPool, ARRAYSIZE( s_PowerPlantSoldierPool ) );
		}

		// Keep core street blocks focused on Civilians vs. Metrocops; let Ravenholm/Xen creatures roam the outer perimeter too.
		if ( ( fabsf( pos.x ) > 4800.0f || fabsf( pos.y ) > 5200.0f ) && RandomInt( 0, 99 ) < 30 )
		{
			return PickWeightedFromPool( s_MonsterPool, ARRAYSIZE( s_MonsterPool ) );
		}

		if ( pos.x <= BIGCITY_CITIZEN_WEST_MAX_X )
		{
			return PickWeightedFromPool( s_CitizenPool, ARRAYSIZE( s_CitizenPool ) );
		}

		if ( pos.x >= BIGCITY_COMBINE_EAST_MIN_X )
		{
			return PickWeightedFromPool( s_MetrocopPool, ARRAYSIZE( s_MetrocopPool ) );
		}
	}

	if ( !IsBigCityMap() && RandomInt( 0, 99 ) < 25 )
	{
		return PickWeightedFromPool( s_MonsterPool, ARRAYSIZE( s_MonsterPool ) );
	}

	int nCivilians = 0;
	int nCombine = 0;
	CountTrackedFactions( nCivilians, nCombine );

	bool bPickCitizen = ( nCivilians < nCombine ) || ( nCivilians == nCombine && RandomInt( 0, 1 ) == 0 );
	if ( bPickCitizen )
	{
		return PickWeightedFromPool( s_CitizenPool, ARRAYSIZE( s_CitizenPool ) );
	}

	if ( !IsBigCityMap() && RandomInt( 0, 3 ) == 0 )
	{
		return PickWeightedFromPool( s_PowerPlantSoldierPool, ARRAYSIZE( s_PowerPlantSoldierPool ) );
	}

	return PickWeightedFromPool( s_MetrocopPool, ARRAYSIZE( s_MetrocopPool ) );
}

static int GatherCandidateNodes( const CUtlVector< CBasePlayer * > &players, CUtlVector< int > &candidates, bool bRequireLinks )
{
	candidates.RemoveAll();
	if ( !g_pBigAINet )
		return 0;

	const float flMinDistSqr = TBMG_SPAWN_MIN_PLAYER_DIST * TBMG_SPAWN_MIN_PLAYER_DIST;
	const float flMaxDistSqr = TBMG_SPAWN_MAX_PLAYER_DIST * TBMG_SPAWN_MAX_PLAYER_DIST;

	const int nNodes = g_pBigAINet->NumNodes();
	for ( int i = 0; i < nNodes; ++i )
	{
		CAI_Node *pNode = g_pBigAINet->GetNode( i );
		if ( !pNode || pNode->GetType() != NODE_GROUND )
			continue;

		if ( pNode->m_eNodeInfo & ( bits_NODE_FALLEN | bits_NODE_WONT_FIT_HULL ) )
			continue;

		if ( bRequireLinks && pNode->NumLinks() <= 0 )
			continue;

		Vector nodePos = pNode->GetPosition( HULL_HUMAN );
		float flDistSqr = MinDistSqrToPlayers( nodePos, players );
		if ( flDistSqr < flMinDistSqr || flDistSqr > flMaxDistSqr )
			continue;

		if ( IsNearAnyMapSpawnPoint( nodePos ) )
			continue;

		candidates.AddToTail( i );
	}

	return candidates.Count();
}

static bool ComputeClearSpawnOrigin( const Vector &nodePos, const NaturalSpawnEntry_t &entry, Vector &outOrigin )
{
	if ( UTIL_PointContents( nodePos + Vector( 0.0f, 0.0f, 16.0f ) ) & ( CONTENTS_WATER | CONTENTS_SLIME ) )
		return false;

	// Expand hull footprint horizontally and vertically so NPCs never clip or hug walls.
	const Vector vecPadMins = NAI_Hull::Mins( entry.nHull ) - Vector( 6.0f, 6.0f, 0.0f );
	const Vector vecPadMaxs = NAI_Hull::Maxs( entry.nHull ) + Vector( 6.0f, 6.0f, 4.0f );

	if ( entry.flExtraZ > 0.0f )
	{
		Vector vecAirPos = nodePos + Vector( 0.0f, 0.0f, entry.flExtraZ );
		trace_t trAir;
		UTIL_TraceHull( vecAirPos, vecAirPos + Vector( 0.0f, 0.0f, 4.0f ), vecPadMins, vecPadMaxs, MASK_NPCSOLID, NULL, COLLISION_GROUP_NONE, &trAir );
		if ( trAir.startsolid || trAir.allsolid || trAir.fraction < 1.0f )
			return false;

		outOrigin = vecAirPos;
		return true;
	}

	Vector vecStart = nodePos + Vector( 0.0f, 0.0f, 16.0f );
	Vector vecEnd   = nodePos - Vector( 0.0f, 0.0f, 64.0f );

	trace_t trGround;
	UTIL_TraceHull( vecStart, vecEnd, vecPadMins, vecPadMaxs, MASK_NPCSOLID, NULL, COLLISION_GROUP_NONE, &trGround );

	if ( trGround.startsolid || trGround.allsolid || !trGround.DidHit() || trGround.plane.normal.z < 0.7f )
		return false;

	if ( UTIL_PointContents( trGround.endpos + Vector( 0.0f, 0.0f, 8.0f ) ) & ( CONTENTS_WATER | CONTENTS_SLIME ) )
		return false;

	Vector vecStanding = trGround.endpos + Vector( 0.0f, 0.0f, 2.0f );

	static const Vector s_CardinalOffsets[4] =
	{
		Vector(  TBMG_WALL_CLEARANCE_RADIUS,  0.0f, 2.0f ),
		Vector( -TBMG_WALL_CLEARANCE_RADIUS,  0.0f, 2.0f ),
		Vector(  0.0f,  TBMG_WALL_CLEARANCE_RADIUS, 2.0f ),
		Vector(  0.0f, -TBMG_WALL_CLEARANCE_RADIUS, 2.0f ),
	};

	for ( int i = 0; i < ARRAYSIZE( s_CardinalOffsets ); ++i )
	{
		trace_t trClear;
		UTIL_TraceHull( vecStanding, vecStanding + s_CardinalOffsets[i], vecPadMins, vecPadMaxs, MASK_NPCSOLID, NULL, COLLISION_GROUP_NONE, &trClear );
		if ( trClear.startsolid || trClear.allsolid || trClear.fraction < 1.0f )
			return false;
	}

	outOrigin = vecStanding;
	return true;
}

static bool TrySpawnAtCandidateNode( CAI_Node *pNode, const CUtlVector< CBasePlayer * > &players )
{
	if ( !pNode )
		return false;

	Vector nodePos = pNode->GetPosition( HULL_HUMAN );
	if ( IsNearAnyMapSpawnPoint( nodePos ) || IsTooCloseToAnyPlayerHull( nodePos, players ) || IsTooCloseToExistingNPC( nodePos ) )
		return false;

	bool bPowerPlantSoldier = false;
	const NaturalSpawnEntry_t &entry = PickEntryForPosition( nodePos, bPowerPlantSoldier );

	Vector spawnPos;
	if ( !ComputeClearSpawnOrigin( nodePos, entry, spawnPos ) )
	{
		++s_nSkippedStuck;
		return false;
	}

	CBaseEntity *pEnt = CreateEntityByName( entry.pszClassname );
	CAI_BaseNPC *pNPC = pEnt ? pEnt->MyNPCPointer() : NULL;
	if ( !pNPC )
	{
		if ( pEnt )
		{
			UTIL_RemoveImmediate( pEnt );
		}
		return false;
	}

	pNPC->SetAbsOrigin( spawnPos );
	pNPC->SetAbsAngles( QAngle( 0.0f, pNode->GetYaw(), 0.0f ) );
	pNPC->AddSpawnFlags( ( entry.flExtraZ <= 0.0f ? SF_NPC_FALL_TO_GROUND : 0 ) | SF_NPC_FADE_CORPSE | SF_NPC_LONG_RANGE );

	if ( entry.pszWeapon && entry.pszWeapon[0] )
	{
		pNPC->KeyValue( "additionalequipment", entry.pszWeapon );
	}

	if ( Q_stricmp( entry.pszClassname, "npc_citizen" ) == 0 )
	{
		pNPC->KeyValue( "citizentype", "3" );
		pNPC->KeyValue( "ammosupply", "SMG1" );
		pNPC->KeyValue( "ammoamount", "45" );
	}
	else if ( entry.pszModel && entry.pszModel[0] )
	{
		pNPC->KeyValue( "model", entry.pszModel );
		bool bShotgunner = ( Q_stricmp( entry.pszClassname, "npc_combine_s" ) == 0 && entry.pszWeapon && Q_stricmp( entry.pszWeapon, "weapon_shotgun" ) == 0 );
		pNPC->KeyValue( "skin", bShotgunner ? "1" : "0" );
	}

	DispatchSpawn( pNPC );
	{
		bool bAsyncAnims = mdlcache->SetAsyncLoad( MDLCACHE_ANIMBLOCK, false );
		pNPC->Activate();
		mdlcache->SetAsyncLoad( MDLCACHE_ANIMBLOCK, bAsyncAnims );
	}

	// Post-spawn hull safety verify: reject immediately if entity physics bounds overlap geometry.
	trace_t trPost;
	UTIL_TraceHull( pNPC->GetAbsOrigin(), pNPC->GetAbsOrigin(), pNPC->WorldAlignMins(), pNPC->WorldAlignMaxs(), MASK_NPCSOLID, pNPC, COLLISION_GROUP_NONE, &trPost );
	if ( trPost.startsolid || trPost.allsolid )
	{
		UTIL_RemoveImmediate( pNPC );
		++s_nSkippedStuck;
		return false;
	}

	if ( bPowerPlantSoldier )
	{
		NudgeNPCIntoPatrol( pNPC, true );
	}
	else if ( entry.flExtraZ <= 0.0f )
	{
		pNPC->SetSchedule( SCHED_PATROL_WALK );
	}

	EHANDLE hNPC = pNPC;
	s_TrackedNPCs.AddToTail( hNPC );
	++s_nTotalSpawned;
	return true;
}

void TBMG_NaturalSpawn_Precache( void )
{
	TBMG_NaturalSpawn_Reset();

	// Precache full HL2 NPC & weapon roster so natural spawning and console creation work immediately.
	static const char * const s_PrecacheEntities[] =
	{
		"npc_citizen",
		"npc_metropolice",
		"npc_combine_s",
		"npc_manhack",
		"npc_cscanner",
		"npc_clawscanner",
		"npc_rollermine",
		"npc_vortigaunt",
		"npc_monk",
		"npc_alyx",
		"npc_barney",
		"npc_dog",
		"npc_zombie",
		"npc_fastzombie",
		"npc_poisonzombie",
		"npc_headcrab",
		"npc_headcrab_fast",
		"npc_headcrab_black",
		"npc_antlion",
		"npc_antlionguard",
		"npc_turret_floor",
		"npc_crow",
		"npc_pigeon",
		"npc_seagull",
		"weapon_pistol",
		"weapon_smg1",
		"weapon_ar2",
		"weapon_shotgun",
		"weapon_alyxgun",
		"weapon_rpg",
	};

	for ( int i = 0; i < ARRAYSIZE( s_PrecacheEntities ); ++i )
	{
		UTIL_PrecacheOther( s_PrecacheEntities[i] );
	}

	CBaseEntity::PrecacheModel( "models/combine_soldier.mdl" );
	CBaseEntity::PrecacheModel( "models/combine_super_soldier.mdl" );
}

void TBMG_NaturalSpawn_Reset( void )
{
	s_TrackedNPCs.Purge();
	s_flNextSpawnTime = ( gpGlobals ? gpGlobals->curtime : 0.0f ) + 3.0f;
	s_flNextPatrolUpdateTime = ( gpGlobals ? gpGlobals->curtime : 0.0f ) + 2.0f;
	s_nTotalSpawned = 0;
	s_nSkippedStuck = 0;
	s_nLastCandidateCount = 0;
	s_bLastNodeCheckLinked = true;
}

void TBMG_NaturalSpawn_Think( void )
{
	if ( !gpGlobals )
		return;

	CUtlVector< CBasePlayer * > players;
	GatherActivePlayers( players );
	PruneTrackedNPCs( players );
	TBMG_UpdatePatrollingNPCs();

	if ( !tbmg_natural_spawn.GetBool() )
	{
		s_flNextSpawnTime = gpGlobals->curtime + 1.0f;
		return;
	}

	if ( players.Count() == 0 || !g_pBigAINet || g_pBigAINet->NumNodes() <= 0 )
		return;

	// Guard against unexpected clock jump back.
	if ( gpGlobals->curtime + 120.0f < s_flNextSpawnTime )
	{
		s_flNextSpawnTime = gpGlobals->curtime + tbmg_natural_spawn_interval.GetFloat();
	}

	if ( gpGlobals->curtime < s_flNextSpawnTime )
		return;

	s_flNextSpawnTime = gpGlobals->curtime + tbmg_natural_spawn_interval.GetFloat();

	if ( s_TrackedNPCs.Count() >= tbmg_natural_spawn_max.GetInt() )
		return;

	if ( gEntList.NumberOfEntities() >= TBMG_MAX_ENTITY_SAFE_CAP )
		return;

	CUtlVector< int > candidateNodes;
	bool bRequireLinks = true;
	if ( GatherCandidateNodes( players, candidateNodes, true ) == 0 )
	{
		bRequireLinks = false;
		GatherCandidateNodes( players, candidateNodes, false );
	}

	s_bLastNodeCheckLinked = bRequireLinks;
	s_nLastCandidateCount = candidateNodes.Count();

	if ( candidateNodes.Count() == 0 )
		return;

	for ( int nAttempt = 0; nAttempt < TBMG_SPAWN_ATTEMPTS; ++nAttempt )
	{
		int nPick = RandomInt( 0, candidateNodes.Count() - 1 );
		CAI_Node *pNode = g_pBigAINet->GetNode( candidateNodes[nPick] );
		if ( TrySpawnAtCandidateNode( pNode, players ) )
			break;
	}
}

CON_COMMAND( tbmg_natural_spawn_status, "Print status of TBMG node-based natural NPC spawning." )
{
	CUtlVector< CBasePlayer * > players;
	GatherActivePlayers( players );
	PruneTrackedNPCs( players );

	const int nTotalNodes = g_pBigAINet ? g_pBigAINet->NumNodes() : 0;
	Msg( "[TBMG Natural Spawn] enabled=%d interval=%.1f max=%d nodes=%d candidates=%d(%s) active=%d total_spawned=%d skipped_blocked=%d entities=%d\n",
		tbmg_natural_spawn.GetInt(),
		tbmg_natural_spawn_interval.GetFloat(),
		tbmg_natural_spawn_max.GetInt(),
		nTotalNodes,
		s_nLastCandidateCount,
		s_bLastNodeCheckLinked ? "linked" : "unlinked_fallback",
		s_TrackedNPCs.Count(),
		s_nTotalSpawned,
		s_nSkippedStuck,
		gEntList.NumberOfEntities() );

	for ( int i = 0; i < s_TrackedNPCs.Count(); ++i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		if ( pEnt )
		{
			Vector v = pEnt->GetAbsOrigin();
			Msg( "  [%d] %s at (%.0f, %.0f, %.0f)\n", i, pEnt->GetClassname(), v.x, v.y, v.z );
		}
	}
}

CON_COMMAND( tbmg_natural_spawn_clear, "Remove all currently tracked naturally spawned NPCs." )
{
	int nRemoved = 0;
	for ( int i = 0; i < s_TrackedNPCs.Count(); ++i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		if ( pEnt && !pEnt->IsMarkedForDeletion() )
		{
			UTIL_Remove( pEnt );
			++nRemoved;
		}
	}
	s_TrackedNPCs.Purge();
	Msg( "[TBMG Natural Spawn] Removed %d naturally spawned NPCs.\n", nRemoved );
}
