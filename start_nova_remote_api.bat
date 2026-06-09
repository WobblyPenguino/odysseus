@echo off
setlocal
cd /d "%~dp0"
REM Keep the default localhost-only. For Tailscale use PowerShell:
REM powershell -ExecutionPolicy Bypass -File .\\start_nova_remote_api.ps1 -HostAddress YOUR_TAILSCALE_IP -Port 8767
powershell -ExecutionPolicy Bypass -File "%~dp0start_nova_remote_api.ps1" -HostAddress 127.0.0.1 -Port 8767
