param(
    [int]$Cycles = 3,
    [ValidateSet("fast", "code", "plan")]
    [string]$Mode = "fast",
    [switch]$AllowTestOnly,
    [int]$MinChangedLines = 6
)

$ErrorActionPreference = "Stop"
$Repo = (Get-Location).Path

Start-Process powershell -ArgumentList @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", (Join-Path $Repo "Start-NovaLoopMonitor.ps1"),
    "-Repo", $Repo
)

$argsList = @("-Cycles", $Cycles, "-Mode", $Mode, "-MinChangedLines", $MinChangedLines)
if ($AllowTestOnly) {
    $argsList += "-AllowTestOnly"
}

& (Join-Path $Repo "run_nova_task_queue_loop.ps1") @argsList
