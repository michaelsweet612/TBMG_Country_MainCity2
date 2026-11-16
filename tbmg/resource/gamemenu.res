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
		"label" "PLAY GAME"
		"command" "OpenBonusMapsDialog"
		"InGameOrder" "20"
		"notmulti" "1"
	}
	"3"
	{
		"label" "SPAWN SCOUT BUGGY (IN-GAME)"
		"command" "engine ch_createjeep"
		"InGameOrder" "30"
		"OnlyInGame" "1"
	}
	"4"
	{
		"label" "FULL ARSENAL & HEV SUIT"
		"command" "engine arsenal"
		"InGameOrder" "35"
		"OnlyInGame" "1"
	}
	"5"
	{
		"label" "DEVELOPER CONSOLE (~)"
		"command" "engine showconsole"
		"InGameOrder" "40"
	}
	"6"
	{
		"label" "LEAVE MAP (MAIN MENU)"
		"command" "DisconnectNoConfirm"
		"InGameOrder" "50"
		"OnlyInGame" "1"
	}
	"7"
	{
		"label" "#GameUI_GameMenu_Options"
		"command" "OpenOptionsDialog"
		"InGameOrder" "55"
	}
	"8"
	{
		"label" "#GameUI_GameMenu_Quit"
		"command" "QuitNoConfirm"
		"InGameOrder" "60"
	}
}
