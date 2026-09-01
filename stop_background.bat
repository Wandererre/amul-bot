@echo off
title Stop Background Amul Tracker
echo Stopping Amul stock bot background processes...
powershell -Command "Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -like '*bot.py*' } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }"
echo Stopped.
pause
