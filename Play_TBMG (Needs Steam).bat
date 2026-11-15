@echo off
setlocal EnableDelayedExpansion
title TBMG: Country ^& MainCity2 — Standalone Source Engine Edition (Needs Steam)
color 06

echo ===============================================================================
echo     TBMG: Country ^& MainCity2 — Source SDK 2013 Standalone Game (Steam)
echo ===============================================================================
echo  Engine:     Source SDK Base 2013 Multiplayer (AppID 243750)
echo  Mod Dir:    tbmg\
echo  Default Map: gm_bigcity_improved (MainCity2)
echo ===============================================================================
echo.

set "MOD_DIR=%~dp0tbmg"
if not exist "%MOD_DIR%\gameinfo.txt" (
    echo [ERROR] Standalone mod folder "tbmg\gameinfo.txt" was not found!
    echo Make sure you extracted the entire TBMG_Country_MainCity2 folder.
    pause
    exit /b 1
)

set "SDK_DIR="
set "SDK_EXE="

for %%P in (
    "C:\Program Files (x86)\Steam\steamapps\common\Source SDK Base 2013 Multiplayer"
    "C:\Program Files\Steam\steamapps\common\Source SDK Base 2013 Multiplayer"
    "D:\SteamLibrary\steamapps\common\Source SDK Base 2013 Multiplayer"
    "E:\SteamLibrary\steamapps\common\Source SDK Base 2013 Multiplayer"
    "F:\SteamLibrary\steamapps\common\Source SDK Base 2013 Multiplayer"
) do (
    if not defined SDK_EXE if exist "%%~P\hl2.exe" (
        set "SDK_DIR=%%~P"
        set "SDK_EXE=%%~P\hl2.exe"
    )
)

if not defined SDK_EXE (
    for /f "tokens=2,*" %%A in ('reg query "HKCU\Software\Valve\Steam" /v SteamPath 2^>nul') do (
        set "STEAM_ROOT=%%B"
        set "STEAM_ROOT=!STEAM_ROOT:/=\!"
        if exist "!STEAM_ROOT!\steamapps\common\Source SDK Base 2013 Multiplayer\hl2.exe" (
            set "SDK_DIR=!STEAM_ROOT!\steamapps\common\Source SDK Base 2013 Multiplayer"
            set "SDK_EXE=!SDK_DIR!\hl2.exe"
        )
    )
)

if defined SDK_EXE (
    echo Found Source SDK Base 2013 Multiplayer at:
    echo   "%SDK_DIR%"
    echo.
    echo Launching TBMG as its own standalone Source Engine game...
    cd /d "%SDK_DIR%"
    start "" "%SDK_EXE%" -steam -game "%MOD_DIR%" +map gm_bigcity_improved
    exit /b 0
)

echo [ERROR] Source SDK Base 2013 Multiplayer was not found on this PC.
echo.
echo TBMG runs on its own standalone Source Engine mod (no Garry's Mod needed).
echo Please install the free "Source SDK Base 2013 Multiplayer" in Steam
echo (AppID 243750), or click Yes below to open Steam's install page.
echo.
choice /c YN /n /m "Open Steam to install Source SDK Base 2013 Multiplayer now? [Y/N]: "
if %errorlevel% equ 1 (
    start "" "steam://install/243750"
)
exit /b 1
