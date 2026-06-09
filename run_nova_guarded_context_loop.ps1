param(
    [int]$Cycles = 1,
    [string]$Repo = "C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530",
    [string]$AiderVenv = "C:\Users\Daniel\Documents\aider-venv-py312",
    [string]$Model = "ollama_chat/qwen3-coder:30b",
    [int]$ContextMaxKB = 420,
    [int]$ContextMaxEstimatedTokens = 120000,
    [int]$SourceExcerptLines = 80,
    [int]$LogTailLines = 25,
    [int]$RadarMaxKB = 120,
    [int]$SearchHintLimit = 80,
    [int]$AiderMapTokens = 0,
    [string]$AiderMapRefresh = "manual"
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

function Get-TextBudget {
    param([string]$Text)
    $safeText = ""
    if ($null -ne $Text) { $safeText = [string]$Text }
    $chars = $safeText.Length
    return [pscustomobject]@{
        Chars = $chars
        KB = [Math]::Round($chars / 1024, 1)
        EstimatedTokens = [Math]::Ceiling($chars / 4)
    }
}

function Get-FileBudget {
    param([string]$Path)
    if (!(Test-Path $Path)) { return Get-TextBudget "" }
    return Get-TextBudget (Get-Content $Path -Raw -ErrorAction SilentlyContinue)
}

function Add-CappedFileContent {
    param(
        [string]$Source,
        [string]$Destination,
        [int]$MaxKB,
        [string]$Label = ""
    )
    if (!(Test-Path $Source)) { return }
    $raw = Get-Content $Source -Raw -ErrorAction SilentlyContinue
    $budget = Get-TextBudget $raw
    if ($Label) { "`n### $Label" | Add-Content $Destination }
    if ($budget.KB -le $MaxKB) {
        $raw | Add-Content $Destination
        return
    }
    $maxChars = [Math]::Max(1024, $MaxKB * 1024)
    $raw.Substring(0, [Math]::Min($raw.Length, $maxChars)) | Add-Content $Destination
    "`n[Context capped: omitted approximately $([Math]::Round($budget.KB - $MaxKB, 1)) KB from $Source.]" | Add-Content $Destination
}

function Write-ContextBudgetNote {
    param(
        [string]$Path,
        [string]$Target,
        [object]$Budget,
        [string[]]$Files
    )
    $note = Join-Path $LogDir ("NEEDS_MANUAL_REVIEW_CONTEXT_BUDGET_{0}.md" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
@"
# Nova Guarded Loop Context Budget Stop

Question:
How should the local loop reduce context for `$Target` before asking Aider/Ollama to edit?

Why it matters:
The assembled context is about $($Budget.KB) KB / $($Budget.EstimatedTokens) estimated tokens, above the configured safe window of $ContextMaxKB KB / $ContextMaxEstimatedTokens estimated tokens. Sending it risks model truncation, irrelevant file additions, or fake edits.

Files involved:
$($Files -join "`n")

Risk:
Oversized context can make the model ignore the chosen target, invent APIs, or add unrelated files to the chat.

Validation plan:
- Reduce source excerpts, log tails, or read-only files.
- Re-run `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nova_guarded_context_loop.ps1 -Cycles 1`.
- Confirm Aider reports a context below the model limit and the loop still validates before commit.

Needs Daniel approval: yes, if the loop needs broader file access or a larger model/context window.
"@ | Set-Content $note
    Write-Host "STOP: context budget exceeded. Wrote manual-review note: $note"
}

function Write-AiderContextStopNote {
    param(
        [string]$Target,
        [string]$OutputPath,
        [string]$ContextPath,
        [string]$Reason
    )
    $note = Join-Path $LogDir ("NEEDS_MANUAL_REVIEW_AIDER_CONTEXT_{0}.md" -f (Get-Date -Format "yyyyMMdd_HHmmss"))
@"
# Nova Guarded Loop Aider Context Stop

Question:
How should the local loop prevent Aider from expanding the chat beyond the safe model window for `$Target`?

Why it matters:
$Reason

Files involved:
$Target
$ContextPath
$OutputPath

Risk:
Aider can auto-add files after the preflight if the model names more files, causing truncation, irrelevant edits, or a failed cycle that looks like a normal no-change run.

Validation plan:
- Keep repo-map disabled or tightly capped for guarded cycles.
- Reduce read-only context if the warning repeats.
- Re-run `powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nova_guarded_context_loop.ps1 -Cycles 1`.
- Confirm Aider does not report an oversized chat and the loop still validates before commit.

Needs Daniel approval: yes, if the loop needs broader file access, a larger model/context window, or manual review of additional files.
"@ | Set-Content $note
    Write-Host "STOP: Aider context budget exceeded. Wrote manual-review note: $note"
}

function Test-ContextBudget {
    param([string]$ContextPath, [string]$PromptPath, [string]$Target)
    $files = @(
        $ContextPath,
        $PromptPath,
        "NOVA_AGENT_MEMORY.md",
        "NOVA_ARCHITECTURE_CONTEXT.md",
        "NOVA_APPROVED_FEATURE_BACKLOG.md",
        "NOVA_RESEARCH_QUEUE.md",
        "winlocalassistant/command_verifier.py",
        "winlocalassistant/main.py",
        "winlocalassistant/command_suggestions.py",
        $Target
    ) | Where-Object { $_ -and (Test-Path $_) }
    $text = ""
    foreach ($file in $files) {
        $text += "`n## $file`n"
        $text += Get-Content $file -Raw -ErrorAction SilentlyContinue
    }
    $budget = Get-TextBudget $text
    Write-Host "Context preflight: $($budget.KB) KB, approx $($budget.EstimatedTokens) tokens."
    if ($budget.KB -gt $ContextMaxKB -or $budget.EstimatedTokens -gt $ContextMaxEstimatedTokens) {
        Write-ContextBudgetNote -Path $ContextPath -Target $Target -Budget $budget -Files $files
        return $false
    }
    return $true
}

function Get-AiderContextStopReason {
    param([string]$OutputPath)
    if (!(Test-Path $OutputPath)) { return "" }
    $raw = Get-Content $OutputPath -Raw -ErrorAction SilentlyContinue
    $esc = [char]27
    $plain = $raw -replace "$esc\[[0-9;?]*[ -/]*[@-~]", ""

    if ($plain -match "estimated chat context of\s+([\d,]+)\s+tokens exceeds the\s+([\d,]+)\s+token limit") {
        return "Aider reported an estimated chat context of $($Matches[1]) tokens, above the $($Matches[2]) token model limit."
    }

    $sentMatches = [regex]::Matches($plain, "Tokens:\s+([0-9.,]+)\s*k\s+sent")
    foreach ($match in $sentMatches) {
        $sentK = [double]::Parse($match.Groups[1].Value.Replace(",", ""), [Globalization.CultureInfo]::InvariantCulture)
        $sentTokens = [int][Math]::Round($sentK * 1000)
        if ($sentTokens -gt $ContextMaxEstimatedTokens) {
            return "Aider sent approximately $sentTokens tokens, above the configured safe budget of $ContextMaxEstimatedTokens estimated tokens."
        }
    }

    return ""
}

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

function Get-TextTail {
    param([string]$Path, [int]$Lines = 120)
    if (Test-Path $Path) {
        return ((Get-Content $Path -Tail $Lines -ErrorAction SilentlyContinue) -join "`n")
    }
    return ""
}

function Append-Mistake {
    param(
        [string]$Target = "unknown",
        [string]$Reason,
        [string]$OutputPath = "",
        [string]$RiskyDiffReason = "",
        [string]$ValidationFailure = "",
        [string]$WhatNotToRepeat = ""
    )
    "`n## $(Get-Date -Format s)" | Add-Content $MistakeMemory
    "Target file: $Target" | Add-Content $MistakeMemory
    "Reason: $Reason" | Add-Content $MistakeMemory
    if ($RiskyDiffReason) { "Risky diff reason: $RiskyDiffReason" | Add-Content $MistakeMemory }
    if ($ValidationFailure) { "Exact validation failure: $ValidationFailure" | Add-Content $MistakeMemory }
    if ($OutputPath -and (Test-Path $OutputPath)) {
        "Command output summary:" | Add-Content $MistakeMemory
        Get-Content $OutputPath -Tail 60 -ErrorAction SilentlyContinue | Add-Content $MistakeMemory
    }
    if ($WhatNotToRepeat) { "What not to repeat: $WhatNotToRepeat" | Add-Content $MistakeMemory }
    "HEAD: $(git rev-parse --short HEAD)" | Add-Content $MistakeMemory
    "Status:" | Add-Content $MistakeMemory
    git status --short | Add-Content $MistakeMemory
}

function Get-RelatedFiles {
    param([string]$Target)
    switch -Regex ($Target) {
        "command_verifier" { return @("winlocalassistant/command_verifier.py", "winlocalassistant/core.py") }
        "command_suggestions" { return @("winlocalassistant/command_suggestions.py", "winlocalassistant/webui.py") }
        "runtime_usability|model_health_timeout" { return @("winlocalassistant/core.py", "winlocalassistant/model_health.py", "winlocalassistant/ollama.py") }
        "project_state|context|memory" { return @("winlocalassistant/project_state.py", "winlocalassistant/model_context.py") }
        "validation|hygiene|release" { return @("winlocalassistant/validate.py", "winlocalassistant/release_readiness.py") }
        default { return @("winlocalassistant/core.py") }
    }
}

function Get-TargetCandidates {
    $backlog = (Get-TextTail "NOVA_BACKLOG.md" 200) + "`n" + (Get-TextTail "NOVA_APPROVED_FEATURE_BACKLOG.md" 200)
    $success = Get-TextTail $SuccessMemory 120
    $mistakes = Get-TextTail $MistakeMemory 160
    $lastTests = Get-TextTail $LastTestResults 160
    $definitions = @(
        "tests_command_verifier.py|command/help consistency|command,help,verify",
        "tests_command_suggestions.py|user-facing command suggestions|command,help,sanity",
        "tests_runtime_usability_release_gate.py|runtime usability and model fallback|fallback,timeout,chat",
        "tests_project_state_continuity.py|project-state memory continuity|project-state,memory,continue",
        "tests_model_health_timeout.py|model timeout and health|model,timeout,fallback",
        "tests_validation_status_command.py|validation status reporting|validation,reporting,status",
        "tests_report_hygiene.py|generated report hygiene|report,generated,hygiene",
        "tests_release_hygiene.py|release hygiene|release,hygiene,readiness"
    )

    $rows = @()
    foreach ($definition in $definitions) {
        $parts = $definition -split "\|"
        $path = $parts[0]
        $theme = $parts[1]
        $keywords = $parts[2] -split ","
        if (!(Test-Path $path)) { continue }
        $score = 20
        $reasons = @("existing safe test target")
        foreach ($keyword in $keywords) {
            if ($backlog -match [regex]::Escape($keyword)) {
                $score += 4
                $reasons += "backlog:$keyword"
            }
        }
        $related = Get-RelatedFiles -Target $path
        $searchPaths = @($path) + $related | Where-Object { Test-Path $_ }
        $hits = Select-String -Path $searchPaths -Pattern "TODO|FIXME|placeholder|timeout|fallback|help-full|release-readiness|project state|context|validation|command" -ErrorAction SilentlyContinue |
            Select-Object -First 8
        if ($hits) {
            $score += [Math]::Min(8, ($hits | Measure-Object).Count)
            $reasons += "code-radar-hits"
        }
        if ($success -match [regex]::Escape("committed $path")) {
            $score -= 35
            $reasons += "recently-committed"
        }
        if ($success -match [regex]::Escape("no safe change made | target $path")) {
            $score -= 25
            $reasons += "recent-no-change"
        }
        if ($mistakes -match [regex]::Escape("Target file: $path")) {
            if ($mistakes -match "fix plan|how to fix|exact validation failure") {
                $score += 6
                $reasons += "failure-memory-has-fix-context"
            } else {
                $score -= 30
                $reasons += "recent-failure-without-fix"
            }
        }
        if ($lastTests -match [regex]::Escape($path)) {
            $score += 3
            $reasons += "mentioned-in-last-tests"
        }
        $rows += [pscustomobject]@{
            Path = $path
            Score = $score
            Theme = $theme
            Reasons = ($reasons -join ", ")
            Related = ((Get-RelatedFiles -Target $path) -join ", ")
        }
    }
    return @($rows | Sort-Object -Property Score, Path -Descending)
}

function Pick-Target {
    $Script:LastTargetCandidates = @(Get-TargetCandidates)
    if (!$Script:LastTargetCandidates -or $Script:LastTargetCandidates.Count -eq 0) {
        throw "No safe target test file found."
    }
    return $Script:LastTargetCandidates[0].Path
}

function Get-NextSuggestedTarget {
    param([string]$Current)
    $next = $Script:LastTargetCandidates | Where-Object { $_.Path -ne $Current } | Select-Object -First 1
    if ($next) { return $next.Path }
    return "Ask Daniel for the next approved target."
}

function Append-Success {
    param(
        [string]$Target,
        [string]$CommitHash,
        [string]$TestsPassed,
        [string]$WhySafe,
        [string]$NextSuggestedTarget
    )
    "`n## $(Get-Date -Format s)" | Add-Content $SuccessMemory
    "Target file: $Target" | Add-Content $SuccessMemory
    "Commit hash: $CommitHash" | Add-Content $SuccessMemory
    "Tests passed: $TestsPassed" | Add-Content $SuccessMemory
    "Why safe: $WhySafe" | Add-Content $SuccessMemory
    "Next suggested target: $NextSuggestedTarget" | Add-Content $SuccessMemory
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

    "`n## Scored candidate target list" | Add-Content $Path
    if ($Script:LastTargetCandidates) {
        $Script:LastTargetCandidates |
            ForEach-Object { "$($_.Score) | $($_.Path) | $($_.Theme) | $($_.Reasons) | related: $($_.Related)" } |
            Add-Content $Path
    } else {
        "No candidate list was available." | Add-Content $Path
    }

    "`n## Source files related to chosen target" | Add-Content $Path
    foreach ($rel in (Get-RelatedFiles -Target $Target)) {
        if (Test-Path $rel) {
            "`n### $rel" | Add-Content $Path
            Get-Content $rel -TotalCount $SourceExcerptLines -ErrorAction SilentlyContinue | Add-Content $Path
            "[Source excerpt capped at $SourceExcerptLines lines. Inspect the real file before asserting APIs.]" | Add-Content $Path
        }
    }

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
            Select-Object -First 6 |
            ForEach-Object {
                "`n### $($_.FullName)" | Add-Content $Path
                Get-Content $_.FullName -Tail $LogTailLines -ErrorAction SilentlyContinue | Add-Content $Path
                "[Log tail capped at $LogTailLines lines.]" | Add-Content $Path
            }
    }

    "`n## Relevant command/help/release search hints" | Add-Content $Path
    Select-String -Path .\tests_*.py, .\winlocalassistant\*.py, .\nova\*.py -Pattern "/help","help-full","release-readiness","legacy-continuity-audit","command" -ErrorAction SilentlyContinue |
        Select-Object -First $SearchHintLimit |
        ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } |
        Add-Content $Path
    "[Search hints capped at $SearchHintLimit matches.]" | Add-Content $Path
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
- Do not guess APIs or report dictionary fields.
- Inspect the read-only implementation files before asserting behaviour.
- If validation failed previously, use MISTAKE_MEMORY.md and LAST_TEST_RESULTS.md to avoid repeating the same mistake.
- This target was chosen from a scored candidate list. Do not repeat a recently failed/no-change idea unless the context explains a concrete fix.
- If the useful next step is a feature, it must match NOVA_APPROVED_FEATURE_BACKLOG.md and be source+test or test-only. Otherwise make no changes.
- If the useful next step needs outside knowledge, a new dependency, or an unfamiliar architecture change, do not edit code.
- If unsure, make no changes.
- Do not ask Aider to add more files to the chat.
- Do not name unrelated files as files to inspect. If the provided context is insufficient, make no changes.
- Do not print or request full file contents.
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

    $radarPath = powershell -NoProfile -ExecutionPolicy Bypass -File .\build_nova_agent_context.ps1
    Write-ContextPack -Path $context -Target $target
    Add-Content $context "`n## Code radar"
    Add-CappedFileContent -Source $radarPath -Destination $context -MaxKB $RadarMaxKB -Label "Capped generated code radar"
    Write-Prompt -Path $prompt -Target $target

    if (!(Test-ContextBudget -ContextPath $context -PromptPath $prompt -Target $target)) {
        Append-Mistake -Target $target -Reason "Context budget exceeded before Aider run" -OutputPath $context -WhatNotToRepeat "Do not send oversized context to Aider/Ollama; reduce excerpts, log tails, or read-only files first."
        exit 0
    }

    Write-Host "Editable target: $target"
    Write-Host "Context: $context"

    & $Aider `
        --model $Model `
        --message-file $prompt `
        --map-tokens $AiderMapTokens `
        --map-refresh $AiderMapRefresh `
        --read $context `
        --read NOVA_AGENT_MEMORY.md `
        --read NOVA_ARCHITECTURE_CONTEXT.md `
        --read NOVA_APPROVED_FEATURE_BACKLOG.md `
        --read NOVA_RESEARCH_QUEUE.md `
        --read winlocalassistant/command_verifier.py `
        --read winlocalassistant/main.py `
        --read winlocalassistant/command_suggestions.py `
        --no-auto-commits `
        --no-dirty-commits `
        --no-gitignore `
        --subtree-only `
        --yes `
        $target `
        2>&1 | Tee-Object -FilePath $out

    $aiderContextStopReason = Get-AiderContextStopReason -OutputPath $out
    if ($aiderContextStopReason) {
        Write-AiderContextStopNote -Target $target -OutputPath $out -ContextPath $context -Reason $aiderContextStopReason
        Append-Mistake -Target $target -Reason $aiderContextStopReason -OutputPath $out -WhatNotToRepeat "Do not accept an Aider cycle after it reports an oversized chat context; reduce repo-map/read files or stop for manual review first."
        git reset --hard
        git clean -fd
        exit 0
    }

    if ($LASTEXITCODE -ne 0) {
        Append-Mistake -Target $target -Reason "Aider failed in cycle $i" -OutputPath $out -WhatNotToRepeat "Do not retry this target without using the aider output to identify a concrete smaller fix."
        git reset --hard
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    if (!(git status --porcelain)) {
        Append-Success -Target $target -CommitHash "none - no change made" -TestsPassed "not run because no diff was created" -WhySafe "The loop made no code changes and stopped safely." -NextSuggestedTarget (Get-NextSuggestedTarget -Current $target)
        Write-Host "No changes made. Stopping safely."
        exit 0
    }

    git status --short
    git diff --stat

    $risk = Is-RiskyDiff -AllowedTarget $target
    if ($risk) {
        Write-Host "STOP: Risky diff detected: $risk"
        Append-Mistake -Target $target -Reason "Risky diff detected before validation" -OutputPath $out -RiskyDiffReason $risk -WhatNotToRepeat "Do not change files outside the selected target, generated reports, app.py, startup scripts, or placeholder tests."
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
        Append-Mistake -Target $target -Reason "Validation failed for target $target" -OutputPath $LastTestResults -ValidationFailure $_.Exception.Message -WhatNotToRepeat "Do not retry the same edit until the exact failing command is addressed."
        git reset --hard
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    $risk = Is-RiskyDiff -AllowedTarget $target
    if ($risk) {
        Write-Host "STOP: Risk after validation: $risk"
        Append-Mistake -Target $target -Reason "Risk detected after validation" -OutputPath $LastTestResults -RiskyDiffReason $risk -WhatNotToRepeat "Do not let validation-generated files or broad diffs remain after tests."
        git reset --hard
        git clean -fd
        exit 1
    }

    git add $target
    git commit -m "Guarded local improvement: $target"

    Append-Success -Target $target -CommitHash (git rev-parse --short HEAD) -TestsPassed "compileall, baseline pytest, target pytest, and area-specific pytest from Validate-Nova" -WhySafe "Only the selected target changed; risky diff guard and validation passed." -NextSuggestedTarget (Get-NextSuggestedTarget -Current $target)
    Write-Host "Cycle $i committed successfully."
}

Write-Host "Finished $Cycles context-aware guarded cycles."
