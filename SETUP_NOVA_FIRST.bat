@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Nova v55.3.168 - setup and validation
echo ============================================================
echo  SETUP ONLY: Nova v55.3.168
echo ============================================================
echo This creates/repairs .venv, installs requirements, and runs validation without starting the web UI.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_nova_best_models.ps1" -Setup -Mode setup
pause
