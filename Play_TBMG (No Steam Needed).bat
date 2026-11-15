@echo off
title TBMG: Country & MainCity2 (No Steam Needed)
color 0a

echo ===============================================================================
echo     TBMG: Country ^& MainCity2 — Desktop 3D Edition (No Steam Needed)
echo ===============================================================================
echo  Map:        MainCity2 / BigCity5 / Driving Test Map
echo  Features:   Animated First-Person Viewmodels, Tactical Sprint (SHIFT+W),
echo              Amber HEV HUD, Iron Sights (RMB), Drivable Vehicles, F1 Admin Menu
echo ===============================================================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to PATH.
    echo Opening WebGL 3D Browser version instead...
    start "" index.html
    pause
    exit /b 1
)

echo Starting desktop 3D OpenGL game...
python game.py

if %errorlevel% neq 0 (
    echo.
    echo [NOTE] If you encountered an issue, you can also play the WebGL version.
    echo Opening WebGL Browser edition...
    start "" index.html
    pause
)

