param(
    [string]$Repo = "C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530"
)

$ErrorActionPreference = "Stop"
Set-Location $Repo

$OutDir = ".\local_ai_cycles\context"
New-Item -ItemType Directory -Force $OutDir | Out-Null

$Stamp = Get-Date -Format "yyyyMMdd_HHmmss"
$Out = Join-Path $OutDir "NOVA_CODE_RADAR_$Stamp.md"

"# Nova Code Radar $Stamp" | Set-Content $Out

"`n## Git HEAD" | Add-Content $Out
git log --oneline -12 | Add-Content $Out

"`n## Git status" | Add-Content $Out
git status --short | Add-Content $Out

"`n## Top-level architecture" | Add-Content $Out
Get-ChildItem -Name | Sort-Object | Add-Content $Out

"`n## Main packages" | Add-Content $Out
Get-ChildItem .\winlocalassistant -File -Filter "*.py" -ErrorAction SilentlyContinue |
    Select-Object -ExpandProperty Name |
    Sort-Object |
    Add-Content $Out

"`n## Test files" | Add-Content $Out
Get-ChildItem -Name "tests_*.py" | Sort-Object | Add-Content $Out

"`n## Areas of concern: TODO/pass/placeholders" | Add-Content $Out
Select-String -Path .\winlocalassistant\*.py,.\nova\*.py,.\tests_*.py -Pattern "TODO|FIXME|placeholder|pass\s*$|not implemented|would be implemented" -ErrorAction SilentlyContinue |
    Select-Object -First 160 |
    ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } |
    Add-Content $Out

"`n## Areas of concern: command/help/release/model timeout keywords" | Add-Content $Out
Select-String -Path .\winlocalassistant\*.py,.\nova\*.py,.\tests_*.py -Pattern "/help|help-full|release-readiness|legacy-continuity-audit|timeout|fallback|command|verify|current release|project state|context" -ErrorAction SilentlyContinue |
    Select-Object -First 220 |
    ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } |
    Add-Content $Out

"`n## Recent generated validation logs, tails only" | Add-Content $Out
if (Test-Path ".\logs") {
    Get-ChildItem .\logs -Recurse -File -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 12 |
        ForEach-Object {
            "`n### $($_.FullName)" | Add-Content $Out
            Get-Content $_.FullName -Tail 80 -ErrorAction SilentlyContinue | Add-Content $Out
        }
}

"`n## Previous Nova release folders near current repo" | Add-Content $Out
Get-ChildItem (Split-Path $Repo) -Directory -Filter "Nova_v*" -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending |
    Select-Object -First 20 |
    ForEach-Object { "$($_.Name) | $($_.LastWriteTime)" } |
    Add-Content $Out

"`n## Suggested safe target files" | Add-Content $Out
@(
    "tests_command_verifier.py",
    "tests_command_suggestions.py",
    "tests_runtime_usability_release_gate.py",
    "tests_model_health_timeout.py",
    "tests_validation_status_command.py",
    "tests_project_state_continuity.py",
    "tests_model_context_pack.py",
    "tests_report_hygiene.py",
    "tests_release_hygiene.py",
    "winlocalassistant/command_verifier.py",
    "winlocalassistant/command_suggestions.py",
    "winlocalassistant/model_health.py",
    "winlocalassistant/project_state.py",
    "winlocalassistant/validate.py",
    "nova/validate.py"
) | Add-Content $Out

Write-Host $Out
