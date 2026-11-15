//========= Copyright TBMG, All rights reserved. ==========================//
//
// Purpose: Natural NPC spawning around map AI nodes (never spawns ammo items).
//
//=============================================================================//

#ifndef TBMG_NATURAL_SPAWN_H
#define TBMG_NATURAL_SPAWN_H
#ifdef _WIN32
#pragma once
#endif

void TBMG_NaturalSpawn_Precache( void );
void TBMG_NaturalSpawn_Reset( void );
void TBMG_NaturalSpawn_Think( void );

#endif // TBMG_NATURAL_SPAWN_H
