@echo off
title Amul Whey Stock Tracker
cd /d "%~dp0"
echo ===================================================
echo     Amul Whey Protein Stock Availability Bot
echo ===================================================
echo.
echo Checking Python environment...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python is not found in PATH. Please install Python 3.10+.
    pause
    exit /b
)

echo Starting stock monitoring loop for Pincode 721302...
echo (Press Ctrl+C at any time to stop)
echo.
python bot.py
pause
