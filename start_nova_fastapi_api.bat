@echo off
setlocal EnableExtensions
cd /d "%~dp0"
echo Starting Nova v55.3.161 API through the better-model launcher...
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_nova_best_models.ps1" -Mode api
pause
