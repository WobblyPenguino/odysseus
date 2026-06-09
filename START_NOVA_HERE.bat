@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title Nova v55.3.168 - START HERE
echo ============================================================
echo  START HERE: Nova v55.3.168 setup + web launcher
echo ============================================================
echo This is the recommended first thing to run after extracting Nova.
echo It repairs .venv if needed, validates, prevents stale old web servers, and opens the clean web UI.
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_nova_best_models.ps1" -Setup -Mode web
if errorlevel 1 (
  echo.
  echo Nova did not start cleanly. Check logs\validation_latest.txt if it exists.
)
echo.
pause
