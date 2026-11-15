"GameMenu"
{
	"1"
	{
		"label" "#GameUI_GameMenu_ResumeGame"
		"command" "ResumeGame"
		"InGameOrder" "10"
		"OnlyInGame" "1"
	}
	"2"
	{
		"label" "ENTER MAINCITY2 (BIG CITY)"
		"command" "engine map gm_bigcity_improved"
		"InGameOrder" "20"
		"notmulti" "1"
	}
	"3"
	{
		"label" "ENTER BIGCITY ROLEPLAY"
		"command" "engine map gm_bigcity_improved_rp"
		"InGameOrder" "25"
		"notmulti" "1"
	}
	"4"
	{
		"label" "SPAWN SCOUT BUGGY (IN-GAME)"
		"command" "engine ch_createjeep"
		"InGameOrder" "30"
		"OnlyInGame" "1"
	}
	"5"
	{
		"label" "FULL ARSENAL & HEV SUIT"
		"command" "engine arsenal"
		"InGameOrder" "35"
		"OnlyInGame" "1"
	}
	"6"
	{
		"label" "DEVELOPER CONSOLE (~)"
		"command" "engine showconsole"
		"InGameOrder" "40"
	}
	"7"
	{
		"label" "#GameUI_GameMenu_LoadGame"
		"command" "OpenLoadGameDialog"
		"InGameOrder" "45"
		"notmulti" "1"
	}
	"8"
	{
		"label" "#GameUI_GameMenu_SaveGame"
		"command" "OpenSaveGameDialog"
		"InGameOrder" "50"
		"notmulti" "1"
		"OnlyInGame" "1"
	}
	"9"
	{
		"label" "#GameUI_GameMenu_Options"
		"command" "OpenOptionsDialog"
		"InGameOrder" "55"
	}
	"10"
	{
		"label" "#GameUI_GameMenu_Quit"
		"command" "Quit"
		"InGameOrder" "60"
	}
}
