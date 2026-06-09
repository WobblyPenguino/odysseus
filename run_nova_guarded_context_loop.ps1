param(
    [int]$Cycles = 1,
    [string]$Repo = "C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530",
    [string]$AiderVenv = "C:\Users\Daniel\Documents\aider-venv-py312",
    [string]$Model = "ollama_chat/qwen3-coder:30b"
)

$ErrorActionPreference = "Stop"
Set-Location $Repo

$Aider = Join-Path $AiderVenv "Scripts\aider.exe"
if (!(Test-Path $Aider)) { throw "Aider not found at $Aider" }

$env:OLLAMA_API_BASE = "http://127.0.0.1:11434"

$LogDir = Join-Path $Repo "local_ai_cycles"
$MemoryDir = Join-Path $LogDir "memory"
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $MemoryDir | Out-Null

$MistakeMemory = Join-Path $MemoryDir "MISTAKE_MEMORY.md"
$SuccessMemory = Join-Path $MemoryDir "SUCCESS_MEMORY.md"
$LastTestResults = Join-Path $MemoryDir "LAST_TEST_RESULTS.md"

function Run-Cmd {
    param([string]$Command, [string]$AppendTo = $null)
    Write-Host ""
    Write-Host ">>> $Command"
    $out = powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
    $out | Write-Host
    if ($AppendTo) {
        "`n>>> $Command" | Add-Content $AppendTo
        $out | Add-Content $AppendTo
        "exit code: $LASTEXITCODE" | Add-Content $AppendTo
    }
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Command" }
}

function Restore-GeneratedNoise {
    git restore -- docs/NOVA_LLM_TRAINING_LAB_LATEST.json docs/NOVA_LLM_TRAINING_LAB_LATEST.md docs/NOVA_MODEL_CALIBRATION_LATEST.json docs/NOVA_MODEL_CALIBRATION_LATEST.md docs/NOVA_RELEASE_READINESS_LATEST.json docs/NOVA_RELEASE_READINESS_LATEST.md logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null
    git clean -fd code_quality_gates code_reviews codebase_integrity_reports 2>$null
}

function Append-Mistake {
    param([string]$Reason)
    "`n## $(Get-Date -Format s)" | Add-Content $MistakeMemory
    "Reason: $Reason" | Add-Content $MistakeMemory
    "HEAD: $(git rev-parse --short HEAD)" | Add-Content $MistakeMemory
    "Status:" | Add-Content $MistakeMemory
    git status --short | Add-Content $MistakeMemory
}

function Pick-Target {
    $targets = @(
        "tests_command_verifier.py",
        "tests_command_suggestions.py",
        "tests_runtime_usability_release_gate.py",
        "tests_project_state_continuity.py",
        "tests_model_health_timeout.py",
        "tests_validation_status_command.py",
        "tests_report_hygiene.py",
        "tests_release_hygiene.py"
    )
    foreach ($t in $targets) {
        if (Test-Path $t) { return $t }
    }
    throw "No safe target test file found."
}

function Write-ContextPack {
    param([string]$Path, [string]$Target)

    "# Nova Local Agent Context Pack" | Set-Content $Path
    "Generated: $(Get-Date -Format s)" | Add-Content $Path
    "Editable target for this cycle: $Target" | Add-Content $Path

    "`n## Current HEAD" | Add-Content $Path
    git log --oneline -8 | Add-Content $Path

    "`n## Current git status" | Add-Content $Path
    git status --short | Add-Content $Path

    "`n## Recent successful local loop memory" | Add-Content $Path
    if (Test-Path $SuccessMemory) { Get-Content $SuccessMemory -Tail 80 | Add-Content $Path } else { "No success memory yet." | Add-Content $Path }

    "`n## Recent mistake memory" | Add-Content $Path
    if (Test-Path $MistakeMemory) { Get-Content $MistakeMemory -Tail 120 | Add-Content $Path } else { "No mistake memory yet." | Add-Content $Path }

    "`n## Last test results" | Add-Content $Path
    if (Test-Path $LastTestResults) { Get-Content $LastTestResults -Tail 160 | Add-Content $Path } else { "No test result memory yet." | Add-Content $Path }

    "`n## Available similar tests" | Add-Content $Path
    Get-ChildItem -Name "tests_*.py" | Select-Object -First 160 | Add-Content $Path

    "`n## Previous Nova release folders near this repo" | Add-Content $Path
    Get-ChildItem (Split-Path $Repo) -Directory -Filter "Nova_v*" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 12 |
        ForEach-Object { "$($_.Name) | $($_.LastWriteTime)" } |
        Add-Content $Path

    "`n## Latest local logs, tails only" | Add-Content $Path
    if (Test-Path "logs") {
        Get-ChildItem logs -Recurse -File -ErrorAction SilentlyContinue |
            Sort-Object LastWriteTime -Descending |
            Select-Object -First 8 |
            ForEach-Object {
                "`n### $($_.FullName)" | Add-Content $Path
                Get-Content $_.FullName -Tail 60 -ErrorAction SilentlyContinue | Add-Content $Path
            }
    }

    "`n## Relevant command/help/release search hints" | Add-Content $Path
    Select-String -Path .\tests_*.py, .\winlocalassistant\*.py, .\nova\*.py -Pattern "/help","help-full","release-readiness","legacy-continuity-audit","command" -ErrorAction SilentlyContinue |
        Select-Object -First 120 |
        ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } |
        Add-Content $Path
}

function Is-RiskyDiff {
    param([string]$AllowedTarget)

    $status = git status --porcelain

    if ($status -match "\.venv/|\.venv\\") { return "Touched .venv" }
    if ($status -match "(^|`n) D ") { return "Deleted file" }
    if ($status -match "docs/NOVA_.*_LATEST|logs/release_readiness|code_quality_gates|code_reviews|codebase_integrity_reports") { return "Generated report/log noise" }
    if ($status -match "NOVA_GUARDED_LOCAL_IMPROVEMENT_RULES.md") { return "Touched guardrail rules; requires manual review" }
    if ($status -match "(^|`n)(\?\?|A |AM) test_") { return "Created non-standard top-level test_*.py file" }
    if ($status -match "(^|`n)(\?\?|A |AM) NOVA_RELEASE") { return "Created release placeholder file" }
    if ($status -match "app.py") { return "Touched app.py; requires manual review" }
    if ($status -match "start_.*\.ps1|start_.*\.bat|START_NOVA_HERE\.bat") { return "Touched startup script; requires manual review" }

    $changedFiles = git diff --name-only
    foreach ($f in $changedFiles) {
        if ($f -ne $AllowedTarget) {
            return "Changed file outside allowed target: $f"
        }
    }

    $stat = git diff --shortstat
    if ($stat -match "(\d+) insertions") {
        if ([int]$Matches[1] -gt 120) { return "Too many insertions: $($Matches[1])" }
    }
    if ($stat -match "(\d+) deletions") {
        if ([int]$Matches[1] -gt 60) { return "Too many deletions: $($Matches[1])" }
    }

    if (Test-Path $AllowedTarget) {
        $placeholder = Select-String -Path $AllowedTarget -Pattern "^\s*pass\s*$|TODO|placeholder|would be implemented|This would|assert True|MagicMock|Mock" -ErrorAction SilentlyContinue
        if ($placeholder) {
            return "Placeholder/fake test content detected in $AllowedTarget"
        }
    }

    return $null
}

function Validate-Nova {
    param([string]$Target)

    "# Nova test results $(Get-Date -Format s)" | Set-Content $LastTestResults
    Run-Cmd "python -m compileall -q app.py winlocalassistant nova" $LastTestResults
    Run-Cmd "python -m pytest -q tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py" $LastTestResults
    Run-Cmd "python -m pytest -q $Target" $LastTestResults

    if ($Target -match "command|help") {
        Run-Cmd "python -m pytest -q tests_command_suggestions.py tests_command_verifier.py tests_runtime_usability_release_gate.py" $LastTestResults
    }
    if ($Target -match "project|context|memory|state") {
        Run-Cmd "python -m pytest -q tests_project_state_continuity.py tests_model_context_pack.py tests_feature_continuity.py" $LastTestResults
    }
    if ($Target -match "release|validation|validate|hygiene") {
        Run-Cmd "python -m pytest -q tests_validation_reporting.py tests_validation_status_command.py tests_runtime_usability_release_gate.py tests_autonomous_release_gate.py tests_report_hygiene.py tests_release_hygiene.py" $LastTestResults
    }
}

function Write-Prompt {
    param([string]$Path, [string]$Target)

@"
You are improving Nova, Daniel's local-first Windows AI assistant.

You may edit ONLY this file:
$Target

Everything else is read-only context.

Task:
Make exactly one tiny real improvement to $Target, or make no changes if no safe real improvement is available.

Hard rules:
- Edit only $Target.
- Do not create new files.
- Do not edit app.py.
- Do not edit startup scripts.
- Do not edit generated reports.
- Do not edit guardrail/memory files.
- Do not use placeholder tests.
- Do not use pass, TODO, assert True, MagicMock, Mock, or "would be implemented".
- Tests must import real Nova code and assert real behaviour.
- If unsure, make no changes.
- Do not claim success; the PowerShell loop will validate.

Use the read-only context files to remember past mistakes, logs, architecture, previous versions, and test results.
"@ | Set-Content $Path
}

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== NOVA CONTEXT-AWARE GUARDED CYCLE $i / $Cycles ====="

    Restore-GeneratedNoise

    if (git status --porcelain) {
        Write-Host "STOP: repo is dirty before cycle."
        git status --short
        exit 1
    }

    $target = Pick-Target
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $context = Join-Path $LogDir "context_$stamp.md"
    $prompt = Join-Path $LogDir "prompt_$stamp.md"
    $out = Join-Path $LogDir "aider_$stamp.out.txt"

    Write-ContextPack -Path $context -Target $target
    Write-Prompt -Path $prompt -Target $target

    Write-Host "Editable target: $target"
    Write-Host "Context: $context"

    & $Aider `
        --model $Model `
        --message-file $prompt `
        --read $context `
        --read NOVA_AGENT_MEMORY.md `
        --read NOVA_ARCHITECTURE_CONTEXT.md `
        --no-auto-commits `
        --no-dirty-commits `
        --no-gitignore `
        --subtree-only `
        --yes `
        $target `
        2>&1 | Tee-Object -FilePath $out

    if ($LASTEXITCODE -ne 0) {
        Append-Mistake "Aider failed in cycle $i"
        git reset --hard
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    if (!(git status --porcelain)) {
        "## $(Get-Date -Format s) | cycle $i | no safe change made | target $target" | Add-Content $SuccessMemory
        Write-Host "No changes made. Stopping safely."
        exit 0
    }

    git status --short
    git diff --stat

    $risk = Is-RiskyDiff -AllowedTarget $target
    if ($risk) {
        Write-Host "STOP: Risky diff detected: $risk"
        Append-Mistake $risk
        git diff --stat
        git diff
        git reset --hard
        git clean -fd
        exit 1
    }

    try {
        Validate-Nova -Target $target
    }
    catch {
        Append-Mistake "Validation failed for target $target"
        git reset --hard
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    $risk = Is-RiskyDiff -AllowedTarget $target
    if ($risk) {
        Write-Host "STOP: Risk after validation: $risk"
        Append-Mistake $risk
        git reset --hard
        git clean -fd
        exit 1
    }

    git add $target
    git commit -m "Guarded local improvement: $target"

    "## $(Get-Date -Format s) | cycle $i | committed $target | HEAD $(git rev-parse --short HEAD)" | Add-Content $SuccessMemory
    Write-Host "Cycle $i committed successfully."
}

Write-Host "Finished $Cycles context-aware guarded cycles."
