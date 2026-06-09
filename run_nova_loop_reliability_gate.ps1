param(
    [int]$Cycles = 5,
    [string]$Mode = "fast"
)

$ErrorActionPreference = "Stop"

function Run-Cmd {
    param([string]$Command)

    Write-Host ""
    Write-Host ">>> $Command"
    powershell -NoProfile -ExecutionPolicy Bypass -Command $Command
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

function Assert-CleanGit {
    $status = git status --short
    if ($status) {
        Write-Host "STOP: git is dirty:"
        git status --short
        throw "Dirty git state"
    }
}

function Clean-GeneratedNoise {
    git restore -- docs/NOVA_LEGACY_CONTINUITY_CONTRACT.json docs/NOVA_PROJECT_STATE_LATEST.json docs/NOVA_PROJECT_STATE_LATEST.md docs/NOVA_LLM_TRAINING_LAB_LATEST.json docs/NOVA_LLM_TRAINING_LAB_LATEST.md docs/NOVA_MODEL_CALIBRATION_LATEST.json docs/NOVA_MODEL_CALIBRATION_LATEST.md docs/NOVA_RELEASE_READINESS_LATEST.json docs/NOVA_RELEASE_READINESS_LATEST.md logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null
    git clean -fd logs/project_state logs/task_evidence code_quality_gates code_reviews codebase_integrity_reports 2>$null
}

$startHead = git rev-parse --short HEAD
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$report = ".\local_ai_cycles\memory\RELIABILITY_GATE_$stamp.md"

New-Item -ItemType Directory -Force .\local_ai_cycles\memory | Out-Null

"# Nova Loop Reliability Gate $stamp" | Set-Content $report
"Start HEAD: $startHead" | Add-Content $report
"Cycles requested: $Cycles" | Add-Content $report
"Mode: $Mode" | Add-Content $report

Clean-GeneratedNoise
Assert-CleanGit

Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== RELIABILITY CYCLE $i / $Cycles ====="

    $before = git rev-parse --short HEAD
    ".`n## Cycle $i" | Add-Content $report
    "Before HEAD: $before" | Add-Content $report

    try {
        Run-Cmd ".\run_nova_guarded_context_loop_slim.ps1 -Cycles 1 -TaskMode $Mode"
    }
    catch {
        "Result: FAILED" | Add-Content $report
        "Reason: $($_.Exception.Message)" | Add-Content $report
        throw
    }

    Clean-GeneratedNoise
    Assert-CleanGit

    Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
    Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

    $after = git rev-parse --short HEAD
    "After HEAD: $after" | Add-Content $report

    if ($after -eq $before) {
        "Result: clean no-change cycle" | Add-Content $report
    } else {
        "Result: clean committed cycle" | Add-Content $report
    }
}

$endHead = git rev-parse --short HEAD
"`nFinished cleanly." | Add-Content $report
"End HEAD: $endHead" | Add-Content $report

Write-Host ""
Write-Host "Reliability gate passed."
Write-Host "Report: $report"
