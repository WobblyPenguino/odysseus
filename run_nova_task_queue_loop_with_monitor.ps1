param(
    [int]$Cycles = 3,
    [ValidateSet("fast", "code", "plan")]
    [string]$Mode = "fast",
    [switch]$AllowTestOnly,
    [int]$MinChangedLines = 6,
    [int]$MaxRecentTaskFailures = 2,
    [Alias("DryRun")]
    [switch]$PreflightOnly,
    [switch]$Monitor
)

$ErrorActionPreference = "Stop"
$Repo = (Get-Location).Path

$MonitorScript = Join-Path $Repo "Start-NovaLoopMonitor.ps1"
$LoopScript = Join-Path $Repo "run_nova_task_queue_loop.ps1"

if (!(Test-Path $LoopScript)) {
    throw "Missing loop script: $LoopScript"
}

if ($Monitor) {
    if (!(Test-Path $MonitorScript)) {
        throw "Missing monitor script: $MonitorScript"
    }

    Start-Process powershell -ArgumentList @(
        "-NoExit",
        "-ExecutionPolicy", "Bypass",
        "-File", $MonitorScript,
        "-Repo", $Repo
    )
}

$loopParams = @{
    Cycles = $Cycles
    Mode = $Mode
    MinChangedLines = $MinChangedLines
    MaxRecentTaskFailures = $MaxRecentTaskFailures
}

if ($AllowTestOnly) {
    $loopParams.AllowTestOnly = $true
}

if ($PreflightOnly) {
    $loopParams.PreflightOnly = $true
}

# Run the real task loop in this terminal. The monitor is only an optional viewer.
& $LoopScript @loopParams
