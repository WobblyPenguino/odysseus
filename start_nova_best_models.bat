@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Nova v55.3.168 - better model web launcher
echo Starting Nova v55.3.168 with better-model environment...
echo Tip: for first setup, double-click START_NOVA_HERE.bat.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_nova_best_models.ps1" -Mode web
pause
