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
Write-Host "Validation passed."
