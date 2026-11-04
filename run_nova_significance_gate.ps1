param(
    [int]$Cycles = 5,
    [ValidateSet("fast", "code", "plan")]
    [string]$Mode = "fast",
    [int]$MinChangedLines = 3
)

$ErrorActionPreference = "Stop"

$MemoryDir = ".\local_ai_cycles\memory"
New-Item -ItemType Directory -Force $MemoryDir | Out-Null

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$report = Join-Path $MemoryDir "SIGNIFICANCE_GATE_$stamp.md"
$latest = Join-Path $MemoryDir "NOVA_SIGNIFICANCE_SUMMARY_LATEST.md"

function Add-Report {
    param([string]$Text)
    $Text | Add-Content $report
    $Text | Add-Content $latest
}

function Clean-GeneratedNoise {
    git restore -- docs/NOVA_LEGACY_CONTINUITY_CONTRACT.json docs/NOVA_PROJECT_STATE_LATEST.json docs/NOVA_PROJECT_STATE_LATEST.md docs/NOVA_LLM_TRAINING_LAB_LATEST.json docs/NOVA_LLM_TRAINING_LAB_LATEST.md docs/NOVA_MODEL_CALIBRATION_LATEST.json docs/NOVA_MODEL_CALIBRATION_LATEST.md docs/NOVA_RELEASE_READINESS_LATEST.json docs/NOVA_RELEASE_READINESS_LATEST.md logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null
    git clean -fd logs/project_state logs/task_evidence code_quality_gates code_reviews codebase_integrity_reports 2>$null
}

function Assert-CleanGit {
    $status = git status --short
    if ($status) {
        Write-Host "STOP: dirty git state"
        git status --short
        throw "Dirty git state"
    }
}

function Run-Cmd {
    param([string]$Command)
    Write-Host ""
    Write-Host ">>> $Command"
    $out = powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
    $out | Write-Host
    $out | Add-Content $report
    $out | Add-Content $latest
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

function Get-ChangedLineCount {
    param([string]$Before, [string]$After)

    $numstat = git diff --numstat "$Before..$After"
    $total = 0
    foreach ($line in $numstat) {
        $parts = $line -split "\s+"
        if ($parts.Count -ge 2) {
            $adds = 0
            $dels = 0
            [int]::TryParse($parts[0], [ref]$adds) | Out-Null
            [int]::TryParse($parts[1], [ref]$dels) | Out-Null
            $total += $adds + $dels
        }
    }
    return $total
}

function Test-SignificantCommit {
    param([string]$Before, [string]$After)

    if ($Before -eq $After) {
        return @{ Ok = $true; Reason = "No commit; clean no-op is acceptable." }
    }

    $files = @(git diff --name-only "$Before..$After")
    $lineCount = Get-ChangedLineCount -Before $Before -After $After
    $subject = git log -1 --pretty=format:"%s"

    if ($files.Count -eq 1 -and $files[0] -eq "tests_command_suggestions.py" -and $lineCount -lt 6) {
        return @{ Ok = $false; Reason = "Low-value repeated command suggestion test tweak: $lineCount changed lines." }
    }

    if ($lineCount -lt $MinChangedLines) {
        return @{ Ok = $false; Reason = "Too small to count as significant: $lineCount changed lines." }
    }

    if ($subject -match "Slim guarded improvement: tests_command_suggestions.py" -and $lineCount -lt 8) {
        return @{ Ok = $false; Reason = "Repeated low-impact tests_command_suggestions.py hardening." }
    }

    return @{ Ok = $true; Reason = "Passed significance check with $lineCount changed lines across $($files.Count) file(s)." }
}

"# Nova Significance Gate $stamp" | Set-Content $report
"# Nova Significance Summary Latest" | Set-Content $latest

Add-Report "Mode: $Mode"
Add-Report "Cycles: $Cycles"
Add-Report "Goal: only keep loop commits that are validated and meaningfully beneficial."

Clean-GeneratedNoise
Assert-CleanGit

Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== SIGNIFICANCE CYCLE $i / $Cycles ====="

    $before = git rev-parse --short HEAD
    Add-Report ""
    Add-Report "## Cycle $i"
    Add-Report "Before: $before"

    Run-Cmd ".\run_nova_guarded_context_loop_slim.ps1 -Cycles 1 -TaskMode $Mode"

    Clean-GeneratedNoise
    Assert-CleanGit

    $after = git rev-parse --short HEAD
    Add-Report "After: $after"

    $sig = Test-SignificantCommit -Before $before -After $after
    Add-Report "Significance result: $($sig.Reason)"

    if (-not $sig.Ok) {
        Add-Report "Action: reverting low-value commit/noise to preserve quality."
        if ($before -ne $after) {
            git reset --hard $before
        }
        "$(Get-Date -Format s) target=significance-gate reason=$($sig.Reason)" | Add-Content ".\local_ai_cycles\memory\NO_CHANGE_TARGETS.md"
        continue
    }

    Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
    Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

    Add-Report "Action: accepted."
    git diff --stat "$before..$after" | Add-Content $report
    git diff --stat "$before..$after" | Add-Content $latest
}

Clean-GeneratedNoise
Assert-CleanGit

Add-Report ""
Add-Report "Finished significance-gated run."
Write-Host "Significance gate finished."
Write-Host "Report: $report"
Write-Host "Latest: $latest"
