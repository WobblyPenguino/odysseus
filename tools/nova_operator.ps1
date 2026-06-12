param(
    [ValidateSet("Status", "Clean", "Check", "Preflight", "DryRun", "LiveOnce", "Triage", "SafeCycle")]
    [string]$Mode = "Status",

    [string]$PackageLabel = ""
)

$ErrorActionPreference = "Stop"

function Run-Step {
    param([string]$Name, [scriptblock]$Block)

    Write-Host ""
    Write-Host "========== $Name ==========" -ForegroundColor Cyan
    & $Block
    if ($LASTEXITCODE -ne 0) {
        throw "$Name failed with exit code $LASTEXITCODE"
    }
}

function Clean-GeneratedNoise {
    git restore -- `
      docs/NOVA_TASK_LOOP_ROADMAP.json `
      docs/NOVA_TASK_LOOP_ROADMAP.md `
      docs/NOVA_LLM_TRAINING_LAB_LATEST.json `
      docs/NOVA_LLM_TRAINING_LAB_LATEST.md `
      docs/NOVA_MODEL_CALIBRATION_LATEST.json `
      docs/NOVA_MODEL_CALIBRATION_LATEST.md `
      docs/NOVA_RELEASE_READINESS_LATEST.json `
      docs/NOVA_RELEASE_READINESS_LATEST.md `
      logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null

    Remove-Item .\local_ai_cycles\config\NOVA_AUTONOMOUS_IDEA_CANDIDATES.json -Force -ErrorAction SilentlyContinue
    Remove-Item .\local_ai_cycles\memory\NOVA_AUTONOMOUS_IDEA_CANDIDATES_LATEST.md -Force -ErrorAction SilentlyContinue
}

function Assert-CleanGit {
    $status = git status --short
    if ($status) {
        $status
        throw "Git is dirty. Stop and inspect before running this mode."
    }
}

function Show-Status {
    Write-Host ""
    Write-Host "========== Git ==========" -ForegroundColor Cyan
    git status --short
    git --no-pager log --oneline -10

    Write-Host ""
    Write-Host "========== Supervised State ==========" -ForegroundColor Cyan
    python .\tools\report_supervised_autonomy_state.py

    Write-Host ""
    Write-Host "========== Latest Failure Triage ==========" -ForegroundColor Cyan
    if (Test-Path .\local_ai_cycles\memory\NOVA_FAILURE_TRIAGE_LATEST.md) {
        Get-Content .\local_ai_cycles\memory\NOVA_FAILURE_TRIAGE_LATEST.md -Tail 180
    }

    Write-Host ""
    Write-Host "========== Latest Batch ==========" -ForegroundColor Cyan
    if (Test-Path .\local_ai_cycles\memory\NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.md) {
        Get-Content .\local_ai_cycles\memory\NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.md -Tail 140
    }

    Write-Host ""
    Write-Host "========== Latest Task Loop ==========" -ForegroundColor Cyan
    if (Test-Path .\local_ai_cycles\memory\NOVA_TASK_LOOP_SUMMARY_LATEST.md) {
        Get-Content .\local_ai_cycles\memory\NOVA_TASK_LOOP_SUMMARY_LATEST.md -Tail 180
    }
}

function Validate-All {
    Run-Step "Compile" {
        python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tools tests_nova_user_sanity.py
    }

    Run-Step "Candidate factory tests" {
        python -m pytest -q tests_autonomous_candidate_factory.py
    }

    Run-Step "Task-loop static tests" {
        python -m pytest -q tests_task_loop_static_contract.py
    }

    Run-Step "Supervised autonomy tests" {
        python -m pytest -q tests_autonomy_readiness_task_pool_health.py tests_supervised_autonomy_batch.py tests_supervised_autonomy_state_report.py
    }

    Run-Step "Baseline tests" {
        python -m pytest -q tests_nova_user_sanity.py tests_runtime_usability_release_gate.py
    }
}

function Package-Checkpoint {
    param([string]$Label)

    if (-not $Label) {
        $Label = "operator_checkpoint"
    }

    Assert-CleanGit

    $short = (git rev-parse --short HEAD).Trim()
    $safeLabel = $Label -replace "[^A-Za-z0-9_\-]", "_"
    $tag = "nova-${safeLabel}-good-${short}"
    $zip = "..\Nova_v55_3_168_${safeLabel}_good_${short}.zip"

    git tag $tag $short 2>$null
    if (Test-Path $zip) { Remove-Item $zip -Force }
    git archive --format=zip --output=$zip HEAD
    Get-FileHash $zip -Algorithm SHA256
    Get-Item $zip | Select-Object FullName, Length, LastWriteTime
}

$stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$logDir = ".\local_ai_cycles\operator_logs"
New-Item -ItemType Directory -Force $logDir | Out-Null
$transcript = Join-Path $logDir "nova_operator_${Mode}_${stamp}.log"
Start-Transcript -Path $transcript -Force | Out-Null

try {
    Write-Host "Nova operator mode: $Mode" -ForegroundColor Green
    Write-Host "Transcript: $transcript"

    if ($Mode -eq "Status") {
        Show-Status
        return
    }

    if ($Mode -eq "Clean") {
        Clean-GeneratedNoise
        Show-Status
        return
    }

    if ($Mode -eq "Triage") {
        Run-Step "Failure triage" {
            python .\tools\nova_failure_triage.py
        }
        Show-Status
        return
    }

    Clean-GeneratedNoise
    Assert-CleanGit

    if ($Mode -eq "Check") {
        Validate-All
        Clean-GeneratedNoise
        Assert-CleanGit
        Show-Status
        return
    }

    if ($Mode -eq "Preflight") {
        Run-Step "Direct preflight only" {
            .\run_nova_task_queue_loop.ps1 -Cycles 1 -Mode code -PreflightOnly -MaxRecoveryCandidates 3
        }
        Clean-GeneratedNoise
        Show-Status
        return
    }

    if ($Mode -eq "DryRun") {
        Run-Step "Supervised batch dry-run" {
            python .\tools\run_supervised_autonomy_batch.py --max-cycles 1 --dry-run
        }
        Clean-GeneratedNoise
        Show-Status
        return
    }

    if ($Mode -eq "LiveOnce") {
        Run-Step "Supervised batch live once" {
            python .\tools\run_supervised_autonomy_batch.py --max-cycles 1
        }
        Clean-GeneratedNoise
        Run-Step "Failure triage after live attempt" {
            python .\tools\nova_failure_triage.py
        }
        Show-Status
        return
    }

    if ($Mode -eq "SafeCycle") {
        Validate-All
        Clean-GeneratedNoise
        Assert-CleanGit

        Run-Step "Direct preflight only" {
            .\run_nova_task_queue_loop.ps1 -Cycles 1 -Mode code -PreflightOnly -MaxRecoveryCandidates 3
        }
        Clean-GeneratedNoise

        Run-Step "Supervised batch dry-run" {
            python .\tools\run_supervised_autonomy_batch.py --max-cycles 1 --dry-run
        }
        Clean-GeneratedNoise

        Run-Step "Supervised batch live once" {
            python .\tools\run_supervised_autonomy_batch.py --max-cycles 1
        }
        Clean-GeneratedNoise

        Run-Step "Failure triage after safe cycle" {
            python .\tools\nova_failure_triage.py
        }

        Show-Status
        return
    }
}
finally {
    Stop-Transcript | Out-Null
}
