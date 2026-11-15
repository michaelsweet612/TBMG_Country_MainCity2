//========= Copyright TBMG, All rights reserved. ==========================//
//
// Purpose: Injects TBMG natural spawning controls into Valve's Options dialog
//          (Difficulty tab) without requiring modified GameUI.dll binaries.
//
//=============================================================================//

#ifndef TBMG_OPTIONS_BRIDGE_H
#define TBMG_OPTIONS_BRIDGE_H
#ifdef _WIN32
#pragma once
#endif

#include <vgui/VGUI.h>

void TBMG_OptionsBridge_Create( vgui::VPANEL parent );
void TBMG_OptionsBridge_Destroy( void );

#endif // TBMG_OPTIONS_BRIDGE_H
