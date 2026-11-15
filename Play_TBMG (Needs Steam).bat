@echo off
title TBMG: Country & MainCity2 — Source Engine Edition (Needs Steam)
color 06

echo ===============================================================================
echo     TBMG: Country ^& MainCity2 — Source Engine Edition (Needs Steam)
echo ===============================================================================
echo  Map:        gm_bigcity_improved (MainCity2)
echo  Features:   Full Physics Gun, Tool Gun, Q Spawn Menu, F1 Admin Menu, Weapons
echo ===============================================================================

set GMOD_EXE=C:\Program Files (x86)\Steam\steamapps\common\GarrysMod\gmod.exe
set SDK_EXE=C:\Program Files (x86)\Steam\steamapps\common\Swelter\hl2.exe
set SDK_DIR=C:\Program Files (x86)\Steam\steamapps\common\Swelter

if exist "%GMOD_EXE%" (
    echo Starting Garry's Mod Source Engine...
    start "" "%GMOD_EXE%" -game garrysmod +gamemode tbmg +map gm_bigcity_improved
    exit /b 0
)

if exist "%SDK_EXE%" (
    echo Starting Standalone Source Mod (Entropy: Zero 2 style)...
    cd /d "%SDK_DIR%"
    start "" "%SDK_EXE%" -steam -game "tbmg" +map gm_bigcity_improved
    exit /b 0
)

echo [ERROR] Neither Garry's Mod nor Source SDK Base executable was found.
echo Make sure Steam and Garry's Mod are installed.
pause
exit /b 1

