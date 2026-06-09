param(
    [int]$Cycles = 5,
    [ValidateSet("fast", "code", "plan")]
    [string]$Mode = "fast",
    [int]$MaxCommits = 10
)

$ErrorActionPreference = "Stop"

$MemoryDir = ".\local_ai_cycles\memory"
New-Item -ItemType Directory -Force $MemoryDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$report = Join-Path $MemoryDir "RELIABILITY_GATE_$stamp.md"
$latest = Join-Path $MemoryDir "NOVA_LOOP_SUMMARY_LATEST.md"
$fence = '```'

function Add-Report {
    param([string]$Text)
    $Text | Add-Content $report
    $Text | Add-Content $latest
}

function Run-Cmd {
    param([string]$Command)

    Write-Host ""
    Write-Host ">>> $Command"

    Add-Report ""
    Add-Report "$fence`powershell"
    Add-Report ">>> $Command"

    $out = powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
    $out | Write-Host
    $out | Add-Content $report
    $out | Add-Content $latest

    Add-Report $fence

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

function Clean-GeneratedNoise {
    git restore -- docs/NOVA_LEGACY_CONTINUITY_CONTRACT.json docs/NOVA_PROJECT_STATE_LATEST.json docs/NOVA_PROJECT_STATE_LATEST.md docs/NOVA_LLM_TRAINING_LAB_LATEST.json docs/NOVA_LLM_TRAINING_LAB_LATEST.md docs/NOVA_MODEL_CALIBRATION_LATEST.json docs/NOVA_MODEL_CALIBRATION_LATEST.md docs/NOVA_RELEASE_READINESS_LATEST.json docs/NOVA_RELEASE_READINESS_LATEST.md logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null
    git clean -fd logs/project_state logs/task_evidence code_quality_gates code_reviews codebase_integrity_reports 2>$null
}

function Assert-CleanGit {
    $status = git status --short
    if ($status) {
        Add-Report ""
        Add-Report "## STOP: dirty git state"
        $status | Add-Content $report
        $status | Add-Content $latest
        git status --short
        throw "Dirty git state"
    }
}

function Add-CommitComparison {
    param(
        [string]$Before,
        [string]$After
    )

    Add-Report ""
    Add-Report "### Version comparison"
    Add-Report "- Before: $Before"
    Add-Report "- After: $After"

    if ($Before -eq $After) {
        Add-Report "- Result: no commit"
        Add-Report "- Benefit: safe no-op. The loop found no useful patch and left Nova unchanged."
        Add-Report "- Justification: no code changed, validation still passed, and git remained clean."
        return
    }

    $subject = git log -1 --pretty=format:"%h %s"
    Add-Report "- Commit: $subject"
    Add-Report "- Benefit justification: accepted only after compile checks, targeted tests, baseline regression tests, Nova user sanity tests, generated-noise cleanup, and clean-git verification passed."
    Add-Report "- Regression risk: reduced by post-commit validation and clean working tree checks."

    Add-Report ""
    Add-Report "Changed files:"
    Add-Report $fence
    git diff --name-status "$Before..$After" | Add-Content $report
    git diff --name-status "$Before..$After" | Add-Content $latest
    Add-Report $fence

    Add-Report ""
    Add-Report "Diff stat:"
    Add-Report $fence
    git diff --stat "$Before..$After" | Add-Content $report
    git diff --stat "$Before..$After" | Add-Content $latest
    Add-Report $fence
}

$startHead = git rev-parse --short HEAD
$commitsMade = 0

"# Nova Loop Reliability and Improvement Summary" | Set-Content $latest
"# Nova Loop Reliability Gate $stamp" | Set-Content $report

Add-Report ""
Add-Report "Start HEAD: $startHead"
Add-Report "Cycles requested: $Cycles"
Add-Report "Mode: $Mode"
Add-Report "Max commits allowed: $MaxCommits"
Add-Report "Purpose: continuously improve Nova only when each cycle produces a small validated patch or a clean no-op."
Add-Report ""
Add-Report "Acceptance rules:"
Add-Report "- compile checks must pass"
Add-Report "- targeted tests must pass inside the slim loop"
Add-Report "- baseline regression tests must pass"
Add-Report "- Nova user sanity tests must pass"
Add-Report "- generated report noise must be cleaned"
Add-Report "- git must be clean after every cycle"

Clean-GeneratedNoise
Assert-CleanGit

Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== RELIABILITY CYCLE $i / $Cycles ====="

    $before = git rev-parse --short HEAD

    Add-Report ""
    Add-Report "## Cycle $i"
    Add-Report "Before HEAD: $before"
    Add-Report "Intent: run one guarded local teacher cycle, then validate Nova from a user-facing perspective."

    try {
        Run-Cmd ".\run_nova_guarded_context_loop_slim.ps1 -Cycles 1 -TaskMode $Mode"
    }
    catch {
        Add-Report ""
        Add-Report "Result: FAILED"
        Add-Report "Reason: $($_.Exception.Message)"
        throw
    }

    Clean-GeneratedNoise
    Assert-CleanGit

    Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
    Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

    $after = git rev-parse --short HEAD
    Add-Report "After HEAD: $after"

    if ($after -eq $before) {
        Add-Report "Result: clean no-change cycle"
    } else {
        $commitsMade += 1
        Add-Report "Result: clean committed cycle"
    }

    Add-CommitComparison -Before $before -After $after

    if ($commitsMade -ge $MaxCommits) {
        Add-Report ""
        Add-Report "Stopping early because MaxCommits was reached."
        break
    }
}

$endHead = git rev-parse --short HEAD

Add-Report ""
Add-Report "## Final summary"
Add-Report "Finished cleanly."
Add-Report "End HEAD: $endHead"
Add-Report "Commits made: $commitsMade"
Add-Report "Reliability verdict: passed this gated run. Still use supervised batches until 10+ clean fast cycles and 10+ clean code cycles pass with useful target rotation."

Write-Host ""
Write-Host "Reliability gate passed."
Write-Host "Report: $report"
Write-Host "Latest summary: $latest"
