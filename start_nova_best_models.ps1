param(
    [ValidateSet('cli','web','api','validate','setup')]
    [string]$Mode = 'web',
    [int]$Port = 8766,
    [int]$ApiPort = 8767,
    [switch]$Setup,
    [switch]$SkipValidation,
    [switch]$NoStopOldServer
)

$ErrorActionPreference = 'Stop'
Set-Location -LiteralPath $PSScriptRoot
$NovaVersion = '55.3.168'

function Add-PathIfExists([string]$PathToAdd) {
    if ($PathToAdd -and (Test-Path -LiteralPath $PathToAdd) -and ($env:Path -notlike "*$PathToAdd*")) {
        $env:Path = "$env:Path;$PathToAdd"
    }
}
function Find-BasePython {
    $py = Get-Command py -ErrorAction SilentlyContinue
    if ($py) {
        foreach ($ver in @('3.12','3.11','3.13')) {
            try { & $py.Source "-$ver" --version *> $null; if ($LASTEXITCODE -eq 0) { return @($py.Source, "-$ver") } } catch {}
        }
    }
    $python = Get-Command python -ErrorAction SilentlyContinue
    if ($python) { return @($python.Source) }
    throw 'Python was not found. Install Python 3.11+ or add it to PATH.'
}
function Invoke-BasePython([string[]]$ArgsList) {
    if ($script:BasePython.Count -gt 1) { & $script:BasePython[0] $script:BasePython[1] @ArgsList }
    else { & $script:BasePython[0] @ArgsList }
}
function Test-VenvValid([string]$Path) {
    return (Test-Path -LiteralPath (Join-Path $Path 'Scripts\python.exe')) -and (Test-Path -LiteralPath (Join-Path $Path 'Scripts\Activate.ps1'))
}
function Ensure-Venv {
    $venvPath = Join-Path $PSScriptRoot '.venv'
    if ((Test-Path -LiteralPath $venvPath) -and (-not (Test-VenvValid $venvPath))) {
        Write-Host 'Existing .venv is incomplete or corrupted; repairing it before setup...'
        try { Remove-Item -LiteralPath $venvPath -Recurse -Force -ErrorAction Stop } catch { Write-Host "Could not remove broken .venv: $($_.Exception.Message)" }
    }
    if (-not (Test-VenvValid $venvPath)) {
        Write-Host 'Creating .venv...'
        Invoke-BasePython @('-m','venv','.venv')  # legacy validation marker: -m venv .venv
    }
    if (-not (Test-VenvValid $venvPath)) { throw '.venv creation failed. Close terminals using this folder, then run START_NOVA_HERE.bat again.' }
    return (Join-Path $venvPath 'Scripts\python.exe')
}
function Install-Requirements([string]$PythonExe) {
    Write-Host 'Installing/updating Nova Python dependencies when requirement files are present...'
    & $PythonExe -m ensurepip --upgrade | Out-Host
    if (Test-Path -LiteralPath '.\requirements-dev.txt') { & $PythonExe -m pip install --disable-pip-version-check -r .\requirements-dev.txt | Out-Host }
    if (Test-Path -LiteralPath '.\requirements-api.txt') { & $PythonExe -m pip install --disable-pip-version-check -r .\requirements-api.txt | Out-Host }
}
function Get-RunningNovaVersion([int]$PortToCheck) {
    try {
        $res = Invoke-RestMethod -Uri "http://127.0.0.1:$PortToCheck/api/version?ts=$(Get-Date -UFormat %s)" -TimeoutSec 2 -ErrorAction Stop
        return [string]$res.version
    } catch { return '' }
}
function Stop-StaleNovaServer([int]$PortToCheck) {
    $runningVersion = Get-RunningNovaVersion $PortToCheck
    if ($runningVersion -eq $NovaVersion) {
        Write-Host "Nova v$NovaVersion is already running at http://127.0.0.1:$PortToCheck. Opening it instead of starting a duplicate."
        Start-Process "http://127.0.0.1:$PortToCheck/?nova_ui=v55.3.168&ts=$(Get-Date -UFormat %s)"
        exit 0
    }
    $conns = @(Get-NetTCPConnection -LocalPort $PortToCheck -State Listen -ErrorAction SilentlyContinue)
    if (-not $conns.Count) { return }
    foreach ($c in $conns) {
        try {
            $p = Get-Process -Id $c.OwningProcess -ErrorAction Stop
            if (($p.ProcessName -match 'python|py') -and (-not $NoStopOldServer)) {
                Write-Host "Stopping stale Nova/Python server on port $PortToCheck (pid $($p.Id), version '$runningVersion')..."
                Stop-Process -Id $p.Id -Force -ErrorAction Stop
                Start-Sleep -Milliseconds 700
            } else {
                Write-Host "Port $PortToCheck is occupied by $($p.ProcessName). Nova will use the requested port only if it becomes free."
            }
        } catch {}
    }
}

Add-PathIfExists 'C:\Program Files\Git\cmd'
Add-PathIfExists 'C:\Program Files\nodejs'
Add-PathIfExists "$env:APPDATA\npm"
Add-PathIfExists "$env:LOCALAPPDATA\Programs\Ollama"

$env:OLLAMA_MODEL = 'qwen3-coder:30b'
$env:NOVA_MODEL = 'qwen3-coder:30b'
$env:NOVA_CODE_MODEL = 'qwen3-coder:30b'
$env:NOVA_CHAT_MODEL = 'qwen3-coder:30b'
$env:NOVA_PLANNER_MODEL = 'qwen3-coder:30b'
$env:NOVA_FAST_MODEL = 'gemma2:2b'
$env:NOVA_VISION_MODEL = 'llama3.2-vision:11b'
$env:NOVA_EMBED_MODEL = 'nomic-embed-text:latest'
$env:NOVA_LOCAL_MODEL_TIMEOUT_SEC = '420'

Write-Host '============================================================'
Write-Host " Nova v$NovaVersion START HERE launcher"
Write-Host '============================================================'
Write-Host 'Main/code/chat/planner: qwen3-coder:30b'
Write-Host 'Fast: gemma2:2b | Vision: llama3.2-vision:11b | Embeddings: nomic-embed-text:latest'
Write-Host 'This launcher repairs invalid .venv folders and prevents stale older web servers on port 8766.'

$script:BasePython = Find-BasePython
$pythonExe = Ensure-Venv
if ($Setup -or $Mode -eq 'setup') { Install-Requirements $pythonExe }

$ollama = Get-Command ollama -ErrorAction SilentlyContinue
if ($ollama) {
    try { Invoke-RestMethod -Uri 'http://127.0.0.1:11434/api/tags' -TimeoutSec 2 | Out-Null; Write-Host 'Ollama API reachable.' }
    catch { Write-Host 'Ollama installed but API was not reachable. Requesting background ollama serve...'; Start-Process -FilePath $ollama.Source -ArgumentList 'serve' -WindowStyle Minimized -ErrorAction SilentlyContinue | Out-Null; Start-Sleep -Seconds 2 }
} else { Write-Host 'Ollama not found on PATH. Nova can still open, but local chat/model calls need Ollama installed.' }

if ($Mode -eq 'setup') { & $pythonExe -m winlocalassistant.validate --all; exit $LASTEXITCODE }
if ($Mode -eq 'validate') { & $pythonExe -m winlocalassistant.validate --all; exit $LASTEXITCODE }

if ((-not $SkipValidation) -and ($env:NOVA_SKIP_STARTUP_TESTS -ne '1')) {
    Write-Host 'Running Nova startup validation. Set NOVA_STRICT_STARTUP_TESTS=1 to block launch on validation REVIEW/FAIL.'
    # Keep this exact marker for legacy launcher tests: winlocalassistant.validate --all
    & $pythonExe -m winlocalassistant.startup_validation --mode quick --root . --timeout 90
    if ($LASTEXITCODE -ne 0) {
        Write-Host 'Nova quick startup validation reported REVIEW/FAIL. Continuing normal launch so you can use Nova; run SETUP_NOVA_FIRST.bat or inspect logs\startup_validation_latest.json before treating this build as release-clean.'
        if ($env:NOVA_STRICT_STARTUP_TESTS -eq '1') { throw 'Nova quick startup validation failed under strict startup mode.' }
    }
}

if ($Mode -eq 'api') { & $pythonExe app.py --api --host 127.0.0.1 --port $ApiPort }
elseif ($Mode -eq 'web') {
    Stop-StaleNovaServer $Port
    Start-Process "http://127.0.0.1:$Port/?nova_ui=v55.3.168&ts=$(Get-Date -UFormat %s)"
    & $pythonExe app.py --web --host 127.0.0.1 --port $Port
} else { & $pythonExe app.py }
