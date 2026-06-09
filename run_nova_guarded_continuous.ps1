param(
    [int]$Cycles = 3,
    [string]$Repo = "C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530",
    [string]$AiderVenv = "C:\Users\Daniel\Documents\aider-venv-py312",
    [string]$Model = "ollama_chat/qwen3-coder:30b"
)

$ErrorActionPreference = "Stop"

Set-Location $Repo

$LogDir = Join-Path $Repo "local_ai_cycles"
New-Item -ItemType Directory -Force $LogDir | Out-Null

$Aider = Join-Path $AiderVenv "Scripts\aider.exe"
if (!(Test-Path $Aider)) {
    throw "Aider not found at $Aider"
}

$env:OLLAMA_API_BASE = "http://127.0.0.1:11434"

function Run-Cmd {
    param([string]$Command)
    Write-Host ""
    Write-Host ">>> $Command"
    powershell -NoProfile -ExecutionPolicy Bypass -Command $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

function Get-GitStatus {
    return (git status --porcelain)
}

function Restore-GeneratedNoise {
    git restore -- docs/NOVA_LLM_TRAINING_LAB_LATEST.json docs/NOVA_LLM_TRAINING_LAB_LATEST.md docs/NOVA_MODEL_CALIBRATION_LATEST.json docs/NOVA_MODEL_CALIBRATION_LATEST.md docs/NOVA_RELEASE_READINESS_LATEST.json docs/NOVA_RELEASE_READINESS_LATEST.md logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null
    git clean -fd code_quality_gates code_reviews codebase_integrity_reports local_ai_cycles 2>$null
}

function Is-RiskyDiff {
    $status = git status --porcelain

    if ($status -match "\.venv/|\.venv\\") { return "Touched .venv" }
    if ($status -match "^ D ") { return "Deleted file" }
    if ($status -match "docs/NOVA_.*_LATEST|logs/release_readiness|code_quality_gates|code_reviews|codebase_integrity_reports") { return "Generated report/log noise" }
    if ($status -match "app.py") { return "Touched app.py; requires manual review" }
    if ($status -match "start_.*\.ps1|start_.*\.bat|START_NOVA_HERE\.bat") { return "Touched startup script; requires manual review" }

    $changedFiles = git diff --name-only
    $count = ($changedFiles | Where-Object { $_ -ne "" }).Count
    if ($count -gt 3) { return "Too many changed files: $count" }

    $stat = git diff --shortstat
    if ($stat -match "(\d+) insertions") {
        $insertions = [int]$Matches[1]
        if ($insertions -gt 160) { return "Too many insertions: $insertions" }
    }
    if ($stat -match "(\d+) deletions") {
        $deletions = [int]$Matches[1]
        if ($deletions -gt 80) { return "Too many deletions: $deletions" }
    }

    return $null
}

function Validate-Nova {
    Run-Cmd "python -m compileall -q app.py winlocalassistant nova"
    Run-Cmd "python -m pytest -q tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

    $changed = git diff --name-only

    if ($changed -match "command|help|app.py|main.py") {
        Run-Cmd "python -m pytest -q tests_command_suggestions.py tests_command_verifier.py tests_runtime_usability_release_gate.py"
    }

    if ($changed -match "project|context|memory|state") {
        Run-Cmd "python -m pytest -q tests_project_state_continuity.py tests_model_context_pack.py tests_feature_continuity.py"
    }

    if ($changed -match "release|validation|validate") {
        Run-Cmd "python -m pytest -q tests_validation_reporting.py tests_validation_status_command.py tests_runtime_usability_release_gate.py tests_autonomous_release_gate.py"
    }
}

function Write-CyclePrompt {
    param([int]$Cycle, [string]$Path)

    $status = git status --short
    $recent = git log --oneline -5

@"
You are improving Nova, Daniel's local-first Windows AI assistant.

You must perform exactly ONE tiny, safe, low-risk improvement.

Hard rules:
- Edit at most 1-2 source/test files.
- Do not delete files.
- Do not edit app.py unless explicitly necessary; prefer tests or focused modules.
- Do not edit startup scripts.
- Do not hand-edit generated LATEST reports.
- Do not add flashy new feature categories.
- Do not broad-refactor.
- Do not claim success without validation.
- If unsure, make no code changes and instead add a short note to local_ai_cycles/NEEDS_MANUAL_REVIEW_$Cycle.md explaining what Daniel should inspect.

Preferred work:
- Add or improve one regression test.
- Improve command/help duplication guardrails.
- Improve project-state/current-release memory.
- Improve validation/report hygiene in generators or tests, not generated outputs.
- Improve model timeout/fallback reliability.
- Improve release-readiness checks.

Before editing:
- Inspect AGENTS.md, NOVA_BACKLOG.md, and NOVA_GUARDED_LOCAL_IMPROVEMENT_RULES.md.
- Inspect relevant source/test files.
- Choose one tiny patch.

After editing:
- Leave a small diff.
- Do not run package/release creation.

Current git status:
$status

Recent commits:
$recent
"@ | Set-Content $Path
}

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== NOVA GUARDED LOCAL IMPROVEMENT CYCLE $i / $Cycles ====="

    Restore-GeneratedNoise

    $dirty = Get-GitStatus
    if ($dirty) {
        Write-Host "STOP: repo is dirty before cycle."
        git status --short
        exit 1
    }

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $promptFile = Join-Path $LogDir "aider_cycle_${i}_$stamp.md"
    $outFile = Join-Path $LogDir "aider_cycle_${i}_$stamp.out.txt"

    Write-CyclePrompt -Cycle $i -Path $promptFile

    Write-Host "Running Aider one-shot..."
    & $Aider `
        --model $Model `
        --message-file $promptFile `
        --no-auto-commits `
        --no-dirty-commits `
        --no-gitignore `
        --subtree-only `
        --yes `
        AGENTS.md `
        NOVA_BACKLOG.md `
        NOVA_GUARDED_LOCAL_IMPROVEMENT_RULES.md `
        2>&1 | Tee-Object -FilePath $outFile

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Aider failed. Reverting any changes."
        git restore .
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    $changed = Get-GitStatus
    if (!$changed) {
        Write-Host "No changes made. Stopping."
        exit 0
    }

    Write-Host ""
    Write-Host "Changed files:"
    git status --short
    git diff --stat

    $risk = Is-RiskyDiff
    if ($risk) {
        Write-Host "STOP: Risky diff detected: $risk"
        git diff --stat
        git diff
        git restore .
        git clean -fd
        exit 1
    }

    try {
        Validate-Nova
    }
    catch {
        Write-Host "Validation failed. Reverting this cycle."
        git diff --stat
        git restore .
        git clean -fd
        exit 1
    }

    $remainingRisk = Is-RiskyDiff
    if ($remainingRisk) {
        Write-Host "STOP: Risk detected after validation: $remainingRisk"
        git restore .
        git clean -fd
        exit 1
    }

    git add .
    git commit -m "Guarded local Nova improvement cycle $i"

    Write-Host "Cycle $i committed successfully."
}

Write-Host ""
Write-Host "Finished $Cycles guarded cycles."
