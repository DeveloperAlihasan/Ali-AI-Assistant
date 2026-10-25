@echo off
title Stonic AI (Ali ^& Shampa) - 1-Click Installer ^& Launcher
color 0B
echo ============================================================================
echo    STONIC AI (ALI ^& SHAMPA) - AUTOMATIC INSTALLER ^& LAUNCHER
echo ============================================================================
echo.
echo [1/3] Installing required Python packages...
py -m pip install --upgrade pip
py -m pip install -r requirements.txt
echo.
if not exist ".env" (
    copy ".env.example" ".env" >nul
    echo [2/3] Created .env file! Please paste your GROQ_API_KEY / GEMINI_API_KEY inside .env.
    notepad .env
) else (
    echo [2/3] .env configuration found.
)
echo.
echo [3/3] Starting Stonic AI Assistant (Ali ^& Shampa)...
py main.py
pause
