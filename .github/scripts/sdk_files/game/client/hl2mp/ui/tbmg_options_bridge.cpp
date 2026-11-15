//========= Copyright TBMG, All rights reserved. ==========================//
//
// Purpose: Injects TBMG Natural Spawning settings directly into GameUI's
//          Options -> Difficulty panel and keeps changes synced to ConVars.
//
//=============================================================================//

#include "cbase.h"
#include "tbmg_options_bridge.h"

#include "ienginevgui.h"
#include <vgui/IPanel.h>
#include <vgui/IScheme.h>
#include <vgui/IVGui.h>
#include <vgui_controls/CheckButton.h>
#include <vgui_controls/Divider.h>
#include <vgui_controls/EditablePanel.h>
#include <vgui_controls/Label.h>

// memdbgon must be the last include file in a .cpp file!!!
#include "tier0/memdbgon.h"

namespace
{
	class CTBMGNaturalSpawnPanel : public vgui::EditablePanel
	{
		DECLARE_CLASS_SIMPLE( CTBMGNaturalSpawnPanel, vgui::EditablePanel );

	public:
		CTBMGNaturalSpawnPanel( vgui::Panel *parent )
			: BaseClass( parent, "TBMGNaturalSpawnPanel" )
		{
			SetAutoDelete( false );
			SetProportional( false );
			SetScheme( "SourceScheme" );
			SetPaintBackgroundEnabled( false );
			SetPaintBorderEnabled( false );

			m_pDivider = new vgui::Divider( this, "TBMGDivider" );
			m_pTitleLabel = new vgui::Label( this, "TBMGTitleLabel", "Natural spawning:" );
			m_pEnableCheck = new vgui::CheckButton( this, "TBMGNaturalSpawnCheck", "Enable natural spawning at NPC nodes (no ammo)" );
			m_pDescLabel = new vgui::Label( this, "TBMGDescLabel", "Spawns HL2 NPCs around walkable info_node points. Excludes ammo to avoid stuck/blocked paths." );

			m_pDivider->SetProportional( false );
			m_pTitleLabel->SetProportional( false );
			m_pEnableCheck->SetProportional( false );
			m_pDescLabel->SetProportional( false );

			m_pDescLabel->SetSize( 404, 32 );
			m_pDescLabel->SetContentAlignment( vgui::Label::a_northwest );
			m_pDescLabel->SetWrap( true );
			m_pEnableCheck->AddActionSignalTarget( this );

			SyncFromConVar();
		}

		virtual void ApplySchemeSettings( vgui::IScheme *pScheme )
		{
			BaseClass::ApplySchemeSettings( pScheme );

			if ( !pScheme )
				return;

			vgui::HFont hDefaultFont = pScheme->GetFont( "Default", false );
			vgui::HFont hSmallFont = pScheme->GetFont( "DefaultSmall", false );
			if ( hSmallFont == vgui::INVALID_FONT )
			{
				hSmallFont = hDefaultFont;
			}

			Color labelCol = pScheme->GetColor( "Label.TextColor", Color( 216, 222, 211, 255 ) );
			Color brightCol = pScheme->GetColor( "Label.TextBrightColor", Color( 255, 255, 255, 255 ) );
			Color dimCol = pScheme->GetColor( "Label.TextDullColor", Color( 195, 200, 190, 255 ) );

			m_pTitleLabel->SetFont( hDefaultFont );
			m_pTitleLabel->SetFgColor( labelCol );

			m_pEnableCheck->SetFont( hDefaultFont );
			m_pEnableCheck->SetFgColor( brightCol );

			m_pDescLabel->SetFont( hSmallFont );
			m_pDescLabel->SetFgColor( dimCol );
			m_pDescLabel->InvalidateLayout( true );
		}

		virtual void PerformLayout( void )
		{
			BaseClass::PerformLayout();

			int wide = GetWide();
			if ( wide < 200 )
			{
				wide = 420;
			}

			m_pDivider->SetBounds( 0, 0, wide, 2 );
			m_pTitleLabel->SetBounds( 0, 6, wide, 16 );
			m_pEnableCheck->SetBounds( -4, 24, wide + 4, 22 );
			m_pDescLabel->SetBounds( 24, 46, wide - 24, 32 );
			m_pDescLabel->InvalidateLayout( true );
		}

		void SyncFromConVar( void )
		{
			ConVarRef naturalSpawn( "tbmg_natural_spawn" );
			if ( naturalSpawn.IsValid() )
			{
				const bool bWant = naturalSpawn.GetBool();
				if ( m_pEnableCheck->IsSelected() != bWant )
				{
					m_pEnableCheck->SetSelected( bWant );
				}
			}
		}

		MESSAGE_FUNC_PTR( OnCheckButtonChecked, "CheckButtonChecked", panel )
		{
			if ( panel != m_pEnableCheck )
				return;

			ConVarRef naturalSpawn( "tbmg_natural_spawn" );
			if ( naturalSpawn.IsValid() )
			{
				const bool bChecked = m_pEnableCheck->IsSelected();
				if ( naturalSpawn.GetBool() != bChecked )
				{
					naturalSpawn.SetValue( bChecked ? 1 : 0 );
					engine->ClientCmd_Unrestricted( "host_writeconfig\n" );
				}
			}
		}

	private:
		vgui::Divider *m_pDivider;
		vgui::Label *m_pTitleLabel;
		vgui::CheckButton *m_pEnableCheck;
		vgui::Label *m_pDescLabel;
	};

	static vgui::VPANEL FindPanelRecursive( vgui::VPANEL root, const char *pszName, bool bRequireVisible, int nDepth )
	{
		if ( !root || nDepth > 8 )
			return NULL;

		const char *pszCurName = vgui::ipanel()->GetName( root );
		if ( pszCurName && !Q_stricmp( pszCurName, pszName ) )
		{
			if ( !bRequireVisible || vgui::ipanel()->IsVisible( root ) )
				return root;
		}

		const int nChildren = vgui::ipanel()->GetChildCount( root );
		for ( int i = 0; i < nChildren; ++i )
		{
			vgui::VPANEL child = vgui::ipanel()->GetChild( root, i );
			if ( bRequireVisible && child && !vgui::ipanel()->IsVisible( child ) )
				continue;

			vgui::VPANEL found = FindPanelRecursive( child, pszName, bRequireVisible, nDepth + 1 );
			if ( found )
				return found;
		}

		return NULL;
	}

	class CTBMGOptionsWatcher : public vgui::Panel
	{
		DECLARE_CLASS_SIMPLE( CTBMGOptionsWatcher, vgui::Panel );

	public:
		CTBMGOptionsWatcher( vgui::VPANEL parent )
			: BaseClass( NULL, "TBMGOptionsWatcher" )
		{
			SetParent( parent );
			SetVisible( false );
			SetMouseInputEnabled( false );
			SetKeyBoardInputEnabled( false );

			m_pEmbedPanel = new CTBMGNaturalSpawnPanel( this );
			m_pEmbedPanel->SetVisible( false );

			vgui::ivgui()->AddTickSignal( GetVPanel(), 50 );
		}

		~CTBMGOptionsWatcher( void )
		{
			if ( m_pEmbedPanel )
			{
				m_pEmbedPanel->SetParent( (vgui::VPANEL)NULL );
				delete m_pEmbedPanel;
				m_pEmbedPanel = NULL;
			}
		}

		virtual void OnTick( void )
		{
			if ( !m_pEmbedPanel || !enginevgui )
				return;

			vgui::VPANEL targetPage = NULL;
			bool bIsMultiplayerFallback = false;

			if ( enginevgui->IsGameUIVisible() )
			{
				vgui::VPANEL gameUIRoot = enginevgui->GetPanel( PANEL_GAMEUIDLL );
				if ( gameUIRoot )
				{
					vgui::VPANEL optionsDlg = FindPanelRecursive( gameUIRoot, "OptionsDialog", true, 0 );
					if ( optionsDlg )
					{
						// Difficulty PropertyPage itself has an empty name (""); identify it via Skill1Radio.
						vgui::VPANEL skillRadio = FindPanelRecursive( optionsDlg, "Skill1Radio", true, 0 );
						if ( skillRadio )
						{
							targetPage = vgui::ipanel()->GetParent( skillRadio );
						}
						else if ( !FindPanelRecursive( optionsDlg, "Skill1Radio", false, 0 ) )
						{
							targetPage = FindPanelRecursive( optionsDlg, "OptionsSubMultiplayer", true, 0 );
							bIsMultiplayerFallback = ( targetPage != NULL );
						}
					}
				}
			}

			if ( targetPage )
			{
				int parentW = 496;
				int parentH = 312;
				vgui::ipanel()->GetSize( targetPage, parentW, parentH );

				const int x = 34;
				const int y = bIsMultiplayerFallback ? MAX( 220, parentH - 90 ) : 228;
				const int w = MAX( 360, parentW - 68 );
				const int h = MAX( 72, parentH - y - 4 );

				bool bNeedLayout = false;
				if ( m_pEmbedPanel->GetVParent() != targetPage )
				{
					m_pEmbedPanel->SetParent( targetPage );
					m_pEmbedPanel->SyncFromConVar();
					bNeedLayout = true;
				}

				int curX = 0, curY = 0, curW = 0, curH = 0;
				m_pEmbedPanel->GetBounds( curX, curY, curW, curH );
				if ( curX != x || curY != y || curW != w || curH != h )
				{
					m_pEmbedPanel->SetBounds( x, y, w, h );
					bNeedLayout = true;
				}

				if ( !m_pEmbedPanel->IsVisible() )
				{
					m_pEmbedPanel->SyncFromConVar();
					m_pEmbedPanel->SetVisible( true );
					bNeedLayout = true;
				}

				if ( bNeedLayout )
				{
					m_pEmbedPanel->MoveToFront();
					m_pEmbedPanel->InvalidateLayout( false, true );
				}
			}
			else
			{
				if ( m_pEmbedPanel->IsVisible() )
				{
					m_pEmbedPanel->SetVisible( false );
				}
				if ( m_pEmbedPanel->GetVParent() != GetVPanel() )
				{
					m_pEmbedPanel->SetParent( GetVPanel() );
				}
			}
		}

		vgui::VPANEL GetEmbedParent( void ) const
		{
			return m_pEmbedPanel ? m_pEmbedPanel->GetVParent() : NULL;
		}

		bool IsEmbedVisible( void ) const
		{
			return m_pEmbedPanel && m_pEmbedPanel->IsVisible();
		}

	private:
		CTBMGNaturalSpawnPanel *m_pEmbedPanel;
	};

	static CTBMGOptionsWatcher *s_pOptionsWatcher = NULL;

	static void DumpVisibleTree_r( vgui::VPANEL panel, int depth )
	{
		if ( !panel || depth > 5 )
			return;

		int x = 0, y = 0, w = 0, h = 0;
		vgui::ipanel()->GetPos( panel, x, y );
		vgui::ipanel()->GetSize( panel, w, h );
		Msg( "%*s- %s (vis=%d pos=%d,%d size=%dx%d)\n",
			depth * 2, "",
			vgui::ipanel()->GetName( panel ),
			vgui::ipanel()->IsVisible( panel ) ? 1 : 0,
			x, y, w, h );

		const int nChildren = vgui::ipanel()->GetChildCount( panel );
		for ( int i = 0; i < nChildren; ++i )
		{
			DumpVisibleTree_r( vgui::ipanel()->GetChild( panel, i ), depth + 1 );
		}
	}
}

void TBMG_OptionsBridge_Create( vgui::VPANEL parent )
{
	if ( !s_pOptionsWatcher )
	{
		s_pOptionsWatcher = new CTBMGOptionsWatcher( parent );
	}
}

void TBMG_OptionsBridge_Destroy( void )
{
	if ( s_pOptionsWatcher )
	{
		s_pOptionsWatcher->MarkForDeletion();
		s_pOptionsWatcher = NULL;
	}
}

CON_COMMAND( tbmg_options_debug, "Dump GameUI Options panel hierarchy and TBMG Natural Spawning embed state." )
{
	if ( !enginevgui )
		return;

	vgui::VPANEL gameUIRoot = enginevgui->GetPanel( PANEL_GAMEUIDLL );
	vgui::VPANEL optionsDlg = gameUIRoot ? FindPanelRecursive( gameUIRoot, "OptionsDialog", false, 0 ) : NULL;

	Msg( "[TBMG Options Bridge] GameUIVisible=%d EmbedVisible=%d EmbedParent=%s\n",
		enginevgui->IsGameUIVisible() ? 1 : 0,
		( s_pOptionsWatcher && s_pOptionsWatcher->IsEmbedVisible() ) ? 1 : 0,
		( s_pOptionsWatcher && s_pOptionsWatcher->GetEmbedParent() ) ? vgui::ipanel()->GetName( s_pOptionsWatcher->GetEmbedParent() ) : "NULL" );

	if ( optionsDlg )
	{
		DumpVisibleTree_r( optionsDlg, 0 );
	}
	else
	{
		Msg( "  OptionsDialog not currently constructed.\n" );
	}
}
