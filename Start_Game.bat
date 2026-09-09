@echo off
title TBMG Country MainCity2
color 0a

echo.
echo ===================================================
echo   Starting TBMG Country MainCity2 (DOOM Engine)
echo ===================================================
echo.

:: Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not installed or not added to your PATH.
    echo Please install Python to run this game.
    pause
    exit /b
)

:: Run the game
python game.py

:: Pause only if the game crashes so the user can see the error
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] The game exited unexpectedly.
    pause
)
