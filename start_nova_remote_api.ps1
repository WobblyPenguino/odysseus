param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8767,
    [switch]$RequireToken
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if ($HostAddress -ne "127.0.0.1" -and $HostAddress -ne "localhost") {
    if (-not $env:NOVA_API_TOKEN) {
        Write-Host "Refusing to expose Nova API beyond localhost without NOVA_API_TOKEN." -ForegroundColor Red
        Write-Host "Set a user environment token first, for example:" -ForegroundColor Yellow
        Write-Host '  [Environment]::SetEnvironmentVariable("NOVA_API_TOKEN", "paste-a-long-random-token", "User")'
        exit 2
    }
}

if ($RequireToken -and -not $env:NOVA_API_TOKEN) {
    Write-Host "NOVA_API_TOKEN is required but not set." -ForegroundColor Red
    exit 2
}

Write-Host "Starting Nova API on http://$HostAddress`:$Port" -ForegroundColor Cyan
Write-Host "Use Tailscale/VPN only. Do not router-port-forward this API." -ForegroundColor Yellow
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    & $VenvPython app.py --api --host $HostAddress --port $Port
} else {
    py -3 app.py --api --host $HostAddress --port $Port
}
