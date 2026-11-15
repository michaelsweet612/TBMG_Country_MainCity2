//========= Copyright TBMG, All rights reserved. ==========================//
//
// Purpose: Naturally spawns mobile HL2 NPCs near walkable map AI ground nodes
//          around active players while strictly excluding ammo crates, ammo
//          pickups, and static props that can lodge in walls or block routes.
//
//=============================================================================//

#include "cbase.h"
#include "tbmg_natural_spawn.h"
#include "ai_basenpc.h"
#include "ai_network.h"
#include "ai_node.h"
#include "ai_hull.h"
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
		Hull_t      nHull;
		float       flExtraZ;
		int         iWeight;
	};

	// Mobile NPCs only: never spawn item_ammo_*, item_box_*, item_item_crate, or blocking props.
	const NaturalSpawnEntry_t s_NaturalSpawnPool[] =
	{
		{ "npc_citizen",     "weapon_smg1",    HULL_HUMAN,         0.0f,  2 },
		{ "npc_citizen",     "weapon_pistol",  HULL_HUMAN,         0.0f,  2 },
		{ "npc_citizen",     "weapon_shotgun", HULL_HUMAN,         0.0f,  1 },
		{ "npc_metropolice", "weapon_pistol",  HULL_HUMAN,         0.0f,  3 },
		{ "npc_metropolice", "weapon_smg1",    HULL_HUMAN,         0.0f,  2 },
		{ "npc_combine_s",   "weapon_ar2",     HULL_HUMAN,         0.0f,  2 },
		{ "npc_combine_s",   "weapon_smg1",    HULL_HUMAN,         0.0f,  2 },
		{ "npc_vortigaunt",  NULL,             HULL_WIDE_HUMAN,    0.0f,  1 },
		{ "npc_zombie",      NULL,             HULL_HUMAN,         0.0f,  2 },
		{ "npc_manhack",     NULL,             HULL_TINY_CENTERED, 48.0f, 1 },
	};

	const float TBMG_SPAWN_MIN_PLAYER_DIST = 500.0f;
	const float TBMG_SPAWN_MAX_PLAYER_DIST = 3400.0f;
	const float TBMG_SPAWN_MIN_NPC_SPACING = 220.0f;
	const float TBMG_SPAWN_DESPAWN_DIST    = 4800.0f;
	const int   TBMG_MAX_ENTITY_SAFE_CAP   = 1600;
	const int   TBMG_SPAWN_ATTEMPTS        = 8;

	CUtlVector< EHANDLE > s_TrackedNPCs;
	float s_flNextSpawnTime = 0.0f;
	int   s_nTotalSpawned = 0;
	int   s_nSkippedStuck = 0;
	int   s_nLastCandidateCount = 0;
	bool  s_bLastNodeCheckLinked = true;
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

static bool IsTooCloseToTrackedNPC( const Vector &pos )
{
	const float flMinDistSqr = TBMG_SPAWN_MIN_NPC_SPACING * TBMG_SPAWN_MIN_NPC_SPACING;
	for ( int i = 0; i < s_TrackedNPCs.Count(); ++i )
	{
		CBaseEntity *pEnt = s_TrackedNPCs[i].Get();
		if ( !pEnt || !pEnt->IsAlive() )
			continue;

		if ( pos.DistToSqr( pEnt->GetAbsOrigin() ) < flMinDistSqr )
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

static const NaturalSpawnEntry_t &PickWeightedEntry( void )
{
	int nTotalWeight = 0;
	for ( int i = 0; i < ARRAYSIZE( s_NaturalSpawnPool ); ++i )
	{
		nTotalWeight += s_NaturalSpawnPool[i].iWeight;
	}

	int nRoll = RandomInt( 0, nTotalWeight - 1 );
	for ( int i = 0; i < ARRAYSIZE( s_NaturalSpawnPool ); ++i )
	{
		nRoll -= s_NaturalSpawnPool[i].iWeight;
		if ( nRoll < 0 )
			return s_NaturalSpawnPool[i];
	}

	return s_NaturalSpawnPool[0];
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

		candidates.AddToTail( i );
	}

	return candidates.Count();
}

static bool ComputeClearSpawnOrigin( const Vector &nodePos, const NaturalSpawnEntry_t &entry, Vector &outOrigin )
{
	// Pad hull horizontally and vertically so NPCs never clip walls or tight alcoves.
	const Vector vecPadMins = NAI_Hull::Mins( entry.nHull ) - Vector( 4.0f, 4.0f, 0.0f );
	const Vector vecPadMaxs = NAI_Hull::Maxs( entry.nHull ) + Vector( 4.0f, 4.0f, 4.0f );

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

	Vector vecStanding = trGround.endpos + Vector( 0.0f, 0.0f, 2.0f );

	// Verify unobstructed full standing volume after floor snap.
	trace_t trClear;
	UTIL_TraceHull( vecStanding, vecStanding + Vector( 0.0f, 0.0f, 4.0f ), vecPadMins, vecPadMaxs, MASK_NPCSOLID, NULL, COLLISION_GROUP_NONE, &trClear );
	if ( trClear.startsolid || trClear.allsolid || trClear.fraction < 1.0f )
		return false;

	outOrigin = vecStanding;
	return true;
}

static bool TrySpawnAtCandidateNode( CAI_Node *pNode, const CUtlVector< CBasePlayer * > &players )
{
	if ( !pNode )
		return false;

	const NaturalSpawnEntry_t &entry = PickWeightedEntry();
	Vector nodePos = pNode->GetPosition( HULL_HUMAN );

	if ( IsTooCloseToAnyPlayerHull( nodePos, players ) || IsTooCloseToTrackedNPC( nodePos ) )
		return false;

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
	pNPC->AddSpawnFlags( SF_NPC_FALL_TO_GROUND | SF_NPC_FADE_CORPSE );

	if ( entry.pszWeapon && entry.pszWeapon[0] )
	{
		pNPC->KeyValue( "additionalequipment", entry.pszWeapon );
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

	EHANDLE hNPC = pNPC;
	s_TrackedNPCs.AddToTail( hNPC );
	++s_nTotalSpawned;
	return true;
}

void TBMG_NaturalSpawn_Precache( void )
{
	TBMG_NaturalSpawn_Reset();

	// Precache candidate NPCs and their weapons so enabling Natural Spawning mid-game works cleanly.
	UTIL_PrecacheOther( "npc_citizen" );
	UTIL_PrecacheOther( "npc_metropolice" );
	UTIL_PrecacheOther( "npc_combine_s" );
	UTIL_PrecacheOther( "npc_vortigaunt" );
	UTIL_PrecacheOther( "npc_zombie" );
	UTIL_PrecacheOther( "npc_manhack" );

	UTIL_PrecacheOther( "weapon_pistol" );
	UTIL_PrecacheOther( "weapon_smg1" );
	UTIL_PrecacheOther( "weapon_ar2" );
	UTIL_PrecacheOther( "weapon_shotgun" );
}

void TBMG_NaturalSpawn_Reset( void )
{
	s_TrackedNPCs.Purge();
	s_flNextSpawnTime = ( gpGlobals ? gpGlobals->curtime : 0.0f ) + 3.0f;
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
