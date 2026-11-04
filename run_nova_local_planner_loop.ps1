$Repo = "C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530"
$Model = "qwen3-coder:30b"
$Cycles = 3

Set-Location $Repo

New-Item -ItemType Directory -Force ".\local_ai_cycles" | Out-Null

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== NOVA LOCAL PLANNING CYCLE $i / $Cycles ====="

    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $contextFile = ".\local_ai_cycles\nova_context_$stamp.md"
    $planFile = ".\local_ai_cycles\nova_plan_$stamp.md"

    "# Nova Local Context Snapshot $stamp" | Set-Content $contextFile
    "`n## Git status" | Add-Content $contextFile
    git status --short | Add-Content $contextFile

    "`n## Diff stat" | Add-Content $contextFile
    git diff --stat | Add-Content $contextFile

    "`n## Top-level files" | Add-Content $contextFile
    Get-ChildItem -Name | Select-Object -First 80 | Add-Content $contextFile

    "`n## Important docs present" | Add-Content $contextFile
    Get-ChildItem -Name AGENTS.md,NOVA_BACKLOG.md,NOVA_LOCAL_AGENT_RULES.md,NOVA_START_HERE.txt,README.md -ErrorAction SilentlyContinue | Add-Content $contextFile

    "`n## Python compile smoke" | Add-Content $contextFile
    python -m compileall -q winlocalassistant 2>&1 | Add-Content $contextFile
    "compileall exit code: $LASTEXITCODE" | Add-Content $contextFile

    "`n## Targeted quick tests" | Add-Content $contextFile
    if (Test-Path ".\tests_model_health_timeout.py") {
        python -m pytest -q .\tests_model_health_timeout.py 2>&1 | Add-Content $contextFile
        "tests_model_health_timeout exit code: $LASTEXITCODE" | Add-Content $contextFile
    }

    if (Test-Path ".\tests_runtime_usability_release_gate.py") {
        python -m pytest -q .\tests_runtime_usability_release_gate.py 2>&1 | Add-Content $contextFile
        "tests_runtime_usability_release_gate exit code: $LASTEXITCODE" | Add-Content $contextFile
    }

    $prompt = @"
You are planning improvements for Nova, a local-first Windows AI assistant.

You cannot edit files directly.
You are only allowed to produce a careful improvement plan.

Read this context:

$(Get-Content $contextFile -Raw)

Task:
Propose exactly ONE small, safe, reversible Nova improvement.

Focus areas:
- project-state memory
- current release awareness
- startup reliability
- model timeout/fallback behaviour
- command/help consistency
- release-readiness validation
- generated report hygiene
- tests that prevent regressions

Rules:
- No broad refactors.
- No flashy new feature categories.
- Do not suggest deleting important source files.
- Include exact files to inspect.
- Include exact validation commands.
- Include what success should look like.
- Include rollback instructions.

Output format:
# Proposed Nova Improvement

## Problem
## Files to inspect
## Small patch plan
## Validation commands
## Success criteria
## Rollback
"@

    $prompt | ollama run $Model | Set-Content $planFile

    Write-Host ""
    Write-Host "Plan written to: $planFile"
    Get-Content $planFile

    "`n---`n" | Add-Content ".\NOVA_LOCAL_AI_PLANS.md"
    Get-Content $planFile | Add-Content ".\NOVA_LOCAL_AI_PLANS.md"
}

Write-Host ""
Write-Host "Finished planning cycles. Review NOVA_LOCAL_AI_PLANS.md before editing code."