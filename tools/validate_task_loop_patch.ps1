$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory=$true)]
        [string]$Command
    )

    Write-Host ""
    Write-Host ">>> $Command"
    cmd /c $Command

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $Command"
    }
}

$errors = $null
[System.Management.Automation.PSParser]::Tokenize((Get-Content .\run_nova_task_queue_loop.ps1 -Raw), [ref]$errors) | Out-Null
if ($errors) {
    $errors
    throw "Task loop PowerShell parse errors found."
}

Invoke-Checked "python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py tests_task_loop_static_contract.py tests_improvement_lab_contract.py"

Invoke-Checked "python -m pytest -q tests_improvement_lab_contract.py tests_task_loop_static_contract.py tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py tests_command_suggestions.py"

Write-Host ""

$CandidateValidatorCommand = "python .\tools\validate_idea_promotion_candidates.py --config .\local_ai_cycles\config\NOVA_IDEA_PROMOTION_CANDIDATES.json --probe"
Write-Host "`n>>> $CandidateValidatorCommand"
& python .\tools\validate_idea_promotion_candidates.py --config .\local_ai_cycles\config\NOVA_IDEA_PROMOTION_CANDIDATES.json --probe
if ($LASTEXITCODE -ne 0) {
    throw "Candidate validation probe failed"
}

$CandidateValidatorTestsCommand = "python -m pytest -q tests_idea_promotion_candidate_validator.py"
Write-Host "`n>>> $CandidateValidatorTestsCommand"
& python -m pytest -q tests_idea_promotion_candidate_validator.py
if ($LASTEXITCODE -ne 0) {
    throw "Candidate validator tests failed"
}


$doubleQuotedMarkdownFenceLines = Select-String -Path .\run_nova_task_queue_loop.ps1 -Pattern '"```' -SimpleMatch
if ($doubleQuotedMarkdownFenceLines) {
    Write-Host "Task loop double-quoted Markdown fence strings found."
    $doubleQuotedMarkdownFenceLines | Format-Table LineNumber, Line -AutoSize
    throw "Task loop double-quoted Markdown fence strings found."
}


Write-Host ""
Write-Host ">>> python -m py_compile tools/update_task_loop_roadmap.py"
python -m py_compile tools/update_task_loop_roadmap.py
if ($LASTEXITCODE -ne 0) {
    throw "Roadmap updater compile failed"
}

Write-Host "Validation passed."
