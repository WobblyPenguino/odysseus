param(
    [string]$TaskName = "Nova Remote API",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8767
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Script = Join-Path $Root "start_nova_remote_api.ps1"
if (!(Test-Path $Script)) { throw "Missing $Script. Run /remote-access-scripts first." }

if ($HostAddress -ne "127.0.0.1" -and $HostAddress -ne "localhost" -and -not $env:NOVA_API_TOKEN) {
    throw "Refusing remote bind without NOVA_API_TOKEN. Set it as a User environment variable first."
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$Script`" -HostAddress $HostAddress -Port $Port"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Start Nova API bridge at user logon. Use only on localhost or Tailscale with NOVA_API_TOKEN." -Force | Out-Null
Write-Host "Installed scheduled task: $TaskName" -ForegroundColor Green
Write-Host "Test with: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
