@echo off
setlocal
cd /d "%~dp0"
title Nova Desktop Voice Listener
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start_nova_desktop_voice_listener.ps1"
pause
