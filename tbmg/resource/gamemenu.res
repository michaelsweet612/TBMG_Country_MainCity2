"GameMenu"
{
	"1"
	{
		"label" "#GameUI_GameMenu_ResumeGame"
		"command" "ResumeGame"
		"InGameOrder" "10"
		"OnlyInGame" "1"
	}
	"5"
	{
		"label" "ENTER MAINCITY2 (BIG CITY)"
		"command" "engine map gm_bigcity_improved"
		"InGameOrder" "40"
		"notmulti" "1"
	}
	"6"
	{
		"label" "ENTER BIGCITY ROLEPLAY"
		"command" "engine map gm_bigcity_improved_rp"
		"InGameOrder" "45"
		"notmulti" "1"
	}
	"7"
	{
		"label" "#GameUI_GameMenu_LoadGame"
		"command" "OpenLoadGameDialog"
		"InGameOrder" "30"
		"notmulti" "1"
	}
	"8"
	{
		"label" "#GameUI_GameMenu_SaveGame"
		"command" "OpenSaveGameDialog"
		"InGameOrder" "20"
		"notmulti" "1"
		"OnlyInGame" "1"
	}
	"9"
	{
		"label" "#GameUI_GameMenu_Options"
		"command" "OpenOptionsDialog"
		"InGameOrder" "50"
	}
	"10"
	{
		"label" "#GameUI_GameMenu_Quit"
		"command" "Quit"
		"InGameOrder" "60"
	}
}
