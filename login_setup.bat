@echo off
title Amul Account Login Setup
cd /d "%~dp0"
echo ===================================================
echo     Amul Account One-Time Login Setup
echo ===================================================
echo.
echo Opening browser window for Amul login...
python bot.py --setup
pause
