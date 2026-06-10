param(
    [int]$Cycles = 3,
    [ValidateSet("fast", "code", "plan")]
    [string]$Mode = "code",
    [switch]$AllowTestOnly,
    [int]$MinChangedLines = 6,
    [int]$MaxRecentTaskFailures = 2,
    [Alias("DryRun")]
    [switch]$PreflightOnly
)

$ErrorActionPreference = "Stop"

$Repo = (Get-Location).Path
$Aider = "C:\Users\Daniel\Documents\aider-venv-py312\Scripts\aider.exe"
if (!$PreflightOnly -and !(Test-Path $Aider)) {
    throw "Aider not found at $Aider"
}

$env:OLLAMA_API_BASE = "http://127.0.0.1:11434"

# Keep Aider/Rich output safe in Windows PowerShell and VS Code terminals.
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$env:NO_COLOR = "1"
$env:FORCE_COLOR = "0"
$env:RICH_NO_COLOR = "1"
$env:TERM = "dumb"
$env:PAGER = "cat"
$env:GIT_PAGER = "cat"
$env:LESS = "-F -X"
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
} catch {}

$LogDir = Join-Path $Repo "local_ai_cycles"
$MemoryDir = Join-Path $LogDir "memory"
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $MemoryDir | Out-Null

$TaskMemory = Join-Path $MemoryDir "TASK_LOOP_MEMORY.md"
$SummaryLatest = Join-Path $MemoryDir "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
$NoChangeTargets = Join-Path $MemoryDir "NO_CHANGE_TARGETS.md"
$MistakeMemory = Join-Path $MemoryDir "MISTAKE_MEMORY.md"
$TaskEventMemory = Join-Path $MemoryDir "TASK_LOOP_EVENTS.jsonl"

foreach ($f in @($TaskMemory, $SummaryLatest, $NoChangeTargets, $MistakeMemory, $TaskEventMemory)) {
    if (!(Test-Path $f)) {
        New-Item -ItemType File -Force $f | Out-Null
    }
}

function Add-Summary {
    param([string]$Text)
    $Text | Add-Content $SummaryLatest
    $Text | Add-Content $TaskMemory
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
    Add-Summary ""
    Add-Summary ">>> $Command"

    $out = powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
    $out | Write-Host
    $out | Add-Content $SummaryLatest
    $out | Add-Content $TaskMemory

    if ($LASTEXITCODE -ne 0) {
        throw "Command failed: $Command"
    }
}

function Get-OllamaModelNames {
    try {
        $rows = ollama list 2>$null
        if (!$rows) { return @() }
        return $rows | Select-Object -Skip 1 | ForEach-Object {
            $parts = ($_ -split "\s+")
            if ($parts.Count -gt 0) { $parts[0] }
        } | Where-Object { $_ -and $_ -ne "" }
    }
    catch {
        return @()
    }
}

function Get-GpuVramMb {
    try {
        $raw = nvidia-smi --query-gpu=memory.total --format=csv,noheader,nounits 2>$null | Select-Object -First 1
        if ($raw) { return [int]($raw.Trim()) }
    }
    catch {}
    return 0
}

function Select-TaskModel {
    param([string]$Mode)

    $models = @(Get-OllamaModelNames)
    $vram = Get-GpuVramMb

    function HasModel([string]$Name) {
        return $models -contains $Name
    }

    Write-Host "Detected Ollama models: $($models -join ', ')"
    Write-Host "Detected NVIDIA VRAM: $vram MB"

    if ($Mode -eq "fast") {
        if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }
        if (HasModel "gemma2:2b") { return "ollama_chat/gemma2:2b" }
        if (HasModel "gpt-oss:20b") { return "ollama_chat/gpt-oss:20b" }
    }

    if ($Mode -eq "code") {
        if ((HasModel "gpt-oss:20b") -and ($vram -ge 12000)) { return "ollama_chat/gpt-oss:20b" }
        if ((HasModel "gemma3:12b") -and ($vram -ge 8000)) { return "ollama_chat/gemma3:12b" }
        if (HasModel "gemma2:2b") { return "ollama_chat/gemma2:2b" }
    }

    if ($Mode -eq "plan") {
        if (HasModel "gpt-oss:20b") { return "ollama_chat/gpt-oss:20b" }
        if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }
    }

    if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }
    if (HasModel "gemma2:2b") { return "ollama_chat/gemma2:2b" }

    throw "No suitable local model found. Run: ollama list"
}

try {
    $Model = Select-TaskModel -Mode $Mode
}
catch {
    if (!$PreflightOnly) {
        throw
    }
    $Model = "preflight/no-local-model-selected"
    Write-Host "Preflight continuing without model selection: $($_.Exception.Message)"
}

$Tasks = @(
    [ordered]@{
        Id = "command-suggestions-behaviour"
        Goal = "Improve Nova command suggestion behaviour only with a real source-backed source+test improvement."
        Editable = @("winlocalassistant\command_suggestions.py", "tests_command_suggestions.py")
        Tests = @("tests_command_suggestions.py")
    },
    [ordered]@{
        Id = "command-verifier-contracts"
        Goal = "Improve Nova command verification contracts/reporting only if a real edge case exists."
        Editable = @("winlocalassistant\command_verifier.py", "tests_command_verifier.py")
        Tests = @("tests_command_verifier.py")
    },
    [ordered]@{
        Id = "model-health-timeout"
        Goal = "Improve model health, Ollama timeout, or fallback reliability only if source-backed."
        Editable = @("winlocalassistant\model_health.py", "winlocalassistant\ollama.py", "tests_model_health_timeout.py")
        Tests = @("tests_model_health_timeout.py")
    },
    [ordered]@{
        Id = "project-state-continuity"
        Goal = "Improve project-state/context continuity only if a real source-backed gap exists."
        Editable = @("winlocalassistant\project_state.py", "tests_project_state_continuity.py", "tests_model_context_pack.py")
        Tests = @("tests_project_state_continuity.py", "tests_model_context_pack.py")
    },
    [ordered]@{
        Id = "validation-status"
        Goal = "Improve validation status/reporting only if it strengthens real validation reliability."
        Editable = @("winlocalassistant\validate.py", "nova\validate.py", "tests_validation_status_command.py", "tests_validation_reporting.py")
        Tests = @("tests_validation_status_command.py", "tests_validation_reporting.py")
    }
)

$RunTaskCooldown = New-Object "System.Collections.Generic.HashSet[string]"
$Script:RevertedTaskCommitIds = $null

function Add-TaskSignal {
    param([hashtable]$Signals, [string]$Reason, [string]$Category = "")

    $lower = ($Reason -as [string]).ToLowerInvariant()
    $categoryLower = ($Category -as [string]).ToLowerInvariant()
    if (!$lower -and !$categoryLower) { return }

    if (($categoryLower -eq "context-protected-file") -and ($lower -match "command failed: python -m pytest|tests_.*\.py|pytest")) {
        $categoryLower = "test-failed"
    }

    if (($categoryLower -eq "success-cooldown") -or ($lower -match "recent-success-cooldown|result:\s*committed|source/test task passed")) {
        $Signals.RecentSuccess += 1
        $Signals.Reasons += "category=success-cooldown"
        return
    }

    if (($categoryLower -in @("no-change", "low-significance", "reverted-success")) -or ($lower -match "no-change|no change|low-significance|low significance|only \d+ changed lines")) {
        $Signals.LowValue += 1
        if ($categoryLower -eq "no-change") {
            $Signals.NoChange += 1
        }
        if ($categoryLower -eq "reverted-success") {
            $Signals.RevertedSuccess += 1
        }
        $Signals.Reasons += "category=$($categoryLower -replace '^$', 'low-value')"
    }

    if (($categoryLower -in @("aider-failed", "context-protected-file", "test-failed", "validation-failed", "generated-noise-dirty-state", "bad-command-suggestion-invention", "command-verifier-output-bloat", "placeholder-or-speculative", "unknown-failure")) -or
        ($lower -match "aider failed|command failed|validation-or-significance-failed|validation failed|rejected|context-token|protected-file|speculative|placeholder|failed")) {
        $Signals.Failures += 1
        $Signals.Reasons += "category=$($categoryLower -replace '^$', 'legacy-failure'): $Reason"
    }
}

function Get-TaskOutcomeCategory {
    param([string]$Reason, [string]$Result = "rejected")

    $lower = ($Reason -as [string]).ToLowerInvariant()
    if (($Result -eq "committed") -or ($lower -match "recent-success-cooldown|source/test task passed")) { return "success-cooldown" }
    if ($lower -match "no source diff after cleanup|generated-noise|dirty git state") { return "generated-noise-dirty-state" }
    if ($lower -match "no-change|no change") { return "no-change" }
    if ($lower -match "reverted-success|success commit was later reverted") { return "reverted-success" }
    if ($lower -match "claim/diff mismatch|dead error-body|dead added variable|unreachable error-body|no-op") { return "low-significance" }
    if ($lower -match "low-significance|low significance|only \d+ changed lines") { return "low-significance" }
    if ($lower -match "aider failed|aider exited") { return "aider-failed" }
    if ($lower -match "command_suggestions|command-suggestions|dangerous command|suggestion") { return "bad-command-suggestion-invention" }
    if ($lower -match "command_verifier|command-verifier|full command output|output_preview|default_command_contracts|/command-verify") { return "command-verifier-output-bloat" }
    if ($lower -match "placeholder|speculative|assert true|magicmock|mock|todo|would be implemented") { return "placeholder-or-speculative" }
    if ($lower -match "command failed: python -m pytest|tests_.*\.py|pytest") { return "test-failed" }
    if ($lower -match "context/token|token-limit|token limit|protected-file|protected file|added app\.py|added readme\.md|added changelog\.md") { return "context-protected-file" }
    if ($lower -match "validation|compileall|py_compile|rejected") { return "validation-failed" }
    return "unknown-failure"
}

function Record-TaskOutcome {
    param(
        [string]$TaskId,
        [string]$Result,
        [string]$Reason,
        [string]$Category = "",
        [string[]]$Tests = @(),
        [string]$Before = "",
        [string]$After = "",
        [int]$LinesChanged = -1,
        [string[]]$ChangedFiles = @(),
        [string[]]$ValidationCommands = @(),
        [string]$AuditNote = ""
    )

    if (!$Category) {
        $Category = Get-TaskOutcomeCategory -Reason $Reason -Result $Result
    }

    $head = ""
    try { $head = (git rev-parse --short HEAD) } catch {}
    $event = [ordered]@{
        created_at = Get-Date -Format s
        task = $TaskId
        result = $Result
        category = $Category
        reason = $Reason
        model = $Model
        mode = $Mode
        head = $head
        before = $Before
        after = $After
        lines_changed = $LinesChanged
        changed_files = @($ChangedFiles)
        validation_commands = @($ValidationCommands)
        audit_note = $AuditNote
        tests = @($Tests)
    }
    ($event | ConvertTo-Json -Compress -Depth 4) | Add-Content $TaskEventMemory
    Add-Summary "Outcome category: $Category"
}

function Get-RevertedTaskCommitIds {
    if ($null -ne $Script:RevertedTaskCommitIds) {
        return $Script:RevertedTaskCommitIds
    }

    $ids = @()
    try {
        $messages = git log --format=%B -n 200 2>$null
        foreach ($line in $messages) {
            if ($line -match "This reverts commit ([0-9a-fA-F]{7,40})") {
                $full = $Matches[1].ToLowerInvariant()
                $ids += $full
                if ($full.Length -gt 7) {
                    $ids += $full.Substring(0, 7)
                }
            }
        }
    }
    catch {}

    $Script:RevertedTaskCommitIds = @($ids | Select-Object -Unique)
    return $Script:RevertedTaskCommitIds
}

function Test-TaskEventWasReverted {
    param($Event)

    $commit = [string]($Event.after -as [string])
    if (!$commit) { $commit = [string]($Event.head -as [string]) }
    if (!$commit) { return $false }

    $commit = $commit.ToLowerInvariant()
    $ids = @(Get-RevertedTaskCommitIds)
    return ($ids -contains $commit) -or (($commit.Length -gt 7) -and ($ids -contains $commit.Substring(0, 7)))
}

function Get-TaskEventCommitKey {
    param($Event)

    $task = [string]($Event.task -as [string])
    $commit = [string]($Event.after -as [string])
    if (!$commit) { $commit = [string]($Event.head -as [string]) }
    if (!$task -or !$commit) { return "" }
    $commit = $commit.ToLowerInvariant()
    if ($commit.Length -gt 7) { $commit = $commit.Substring(0, 7) }
    return "$task|$commit"
}

function Read-TaskEvents {
    if (!(Test-Path $TaskEventMemory)) { return @() }
    $rows = @()
    foreach ($raw in (Get-Content $TaskEventMemory -Tail 240 -ErrorAction SilentlyContinue)) {
        try {
            $rows += ($raw | ConvertFrom-Json -ErrorAction Stop)
        }
        catch {}
    }
    return $rows
}

function Ensure-RevertedSuccessEvents {
    $events = @(Read-TaskEvents)
    if (!$events) { return }

    $existing = New-Object "System.Collections.Generic.HashSet[string]"
    foreach ($event in $events) {
        if ([string]$event.category -eq "reverted-success") {
            $key = Get-TaskEventCommitKey -Event $event
            if ($key) { [void]$existing.Add($key) }
        }
    }

    foreach ($event in $events) {
        if ([string]$event.category -ne "success-cooldown") { continue }
        if (!(Test-TaskEventWasReverted -Event $event)) { continue }
        $key = Get-TaskEventCommitKey -Event $event
        if (!$key -or $existing.Contains($key)) { continue }

        Record-TaskOutcome `
            -TaskId ([string]$event.task) `
            -Result "rejected" `
            -Reason "success commit was later reverted: $($event.after)" `
            -Category "reverted-success" `
            -Tests @($event.tests) `
            -Before ([string]$event.before) `
            -After ([string]$event.after) `
            -LinesChanged ([int]$event.lines_changed) `
            -ChangedFiles @($event.changed_files) `
            -ValidationCommands @($event.validation_commands) `
            -AuditNote "Reverted success event synthesized from git revert history."
        [void]$existing.Add($key)
    }
}

function Get-RecentTaskSignals {
    param([string]$TaskId)

    $signals = @{
        Failures = 0
        LowValue = 0
        NoChange = 0
        RevertedSuccess = 0
        RecentSuccess = 0
        Reasons = @()
    }

    if (Test-Path $TaskEventMemory) {
        $events = @(Read-TaskEvents)
        $revertedKeys = New-Object "System.Collections.Generic.HashSet[string]"
        foreach ($event in $events) {
            if ([string]$event.category -eq "reverted-success") {
                $key = Get-TaskEventCommitKey -Event $event
                if ($key) { [void]$revertedKeys.Add($key) }
            }
        }

        foreach ($event in $events) {
            if ([string]$event.task -eq $TaskId) {
                if (([string]$event.category -eq "success-cooldown") -and (Test-TaskEventWasReverted -Event $event)) {
                    $key = Get-TaskEventCommitKey -Event $event
                    if (!$key -or !$revertedKeys.Contains($key)) {
                        Add-TaskSignal -Signals $signals -Reason "success commit was later reverted: $($event.after)" -Category "reverted-success"
                    }
                } else {
                    Add-TaskSignal -Signals $signals -Reason ([string]$event.reason) -Category ([string]$event.category)
                }
            }
        }
    }

    $sources = @($NoChangeTargets, $MistakeMemory)
    foreach ($src in $sources) {
        if (Test-Path $src) {
            $lines = Get-Content $src -Tail 240 -ErrorAction SilentlyContinue
            $currentTask = ""
            $currentStructured = $false
            foreach ($line in $lines) {
                if ($line -match "structured_event=1") { $currentStructured = $true }
                $lineTask = ""
                $reason = ""
                if ($line -match "(^|\s)task=([^\s|]+)") {
                    if ($line -match "structured_event=1") { continue }
                    $lineTask = $Matches[2].Trim()
                    if ($line -match "reason=(.+)$") { $reason = $Matches[1].Trim() }
                } elseif ($line -match "^Task:\s*([^\s]+)") {
                    $currentTask = $Matches[1].Trim()
                    $currentStructured = ($line -match "structured_event=1")
                    continue
                } elseif (($currentTask -eq $TaskId) -and ($line -match "^Reason:\s*(.+)$")) {
                    if ($currentStructured) { continue }
                    $lineTask = $currentTask
                    $reason = $Matches[1].Trim()
                }

                if ($lineTask -eq $TaskId) {
                    if (!$reason) { $reason = $line }
                    Add-TaskSignal -Signals $signals -Reason $reason
                }
            }
        }
    }
    return [pscustomobject]@{
        Failures = [int]$signals.Failures
        LowValue = [int]$signals.LowValue
        NoChange = [int]$signals.NoChange
        RevertedSuccess = [int]$signals.RevertedSuccess
        RecentSuccess = [int]$signals.RecentSuccess
        Reasons = (($signals.Reasons | Select-Object -Unique -First 3) -join "; ")
    }
}

function Get-RecentTaskFailureCount {
    param([string]$TaskId)
    return (Get-RecentTaskSignals -TaskId $TaskId).Failures
}

function Test-TaskFilesExist {
    param($Task)
    foreach ($f in $Task.Editable) {
        if (!(Test-Path $f)) {
            return $false
        }
    }
    return $true
}

function Pick-Task {
    $rows = @()
    foreach ($task in $Tasks) {
        if (!(Test-TaskFilesExist $task)) {
            Add-Summary "Skipping task $($task.Id): editable/test file missing."
            continue
        }

        $signals = Get-RecentTaskSignals -TaskId $task.Id
        $hasSource = @($task.Editable | Where-Object { $_ -notmatch "(^|\\|/)tests_.*\.py$" }).Count -gt 0
        $hasTests = @($task.Tests | Where-Object { Test-Path $_ }).Count -gt 0
        $usedThisRun = $RunTaskCooldown.Contains([string]$task.Id)
        $successOffsets = [Math]::Min($signals.Failures, $signals.RecentSuccess)
        $effectiveFailures = [Math]::Max(0, $signals.Failures - $successOffsets)
        $score = 50
        $reasons = @()

        if ($hasSource -and $hasTests) {
            $score += 20
            $reasons += "source+test candidate"
        }
        if ($signals.Failures -gt 0) {
            $score -= 25 * $effectiveFailures
            if ($successOffsets -gt 0) {
                $reasons += "$effectiveFailures effective recent failure(s); $successOffsets stale failure(s) offset by later success"
            } else {
                $reasons += "$($signals.Failures) recent failure(s)"
            }
        }
        if ($signals.LowValue -gt 0) {
            $score -= 15 * $signals.LowValue
            $reasons += "$($signals.LowValue) recent low-value/no-change outcome(s)"
        }
        if ($signals.RevertedSuccess -gt 0) {
            $score -= 35 * $signals.RevertedSuccess
            $reasons += "$($signals.RevertedSuccess) reverted accepted commit(s)"
        }
        if ($signals.NoChange -gt 0) {
            $score -= 20 * $signals.NoChange
            $reasons += "$($signals.NoChange) recent no-change outcome(s)"
        }
        if ($signals.RecentSuccess -gt 0) {
            $score -= 12 * $signals.RecentSuccess
            $reasons += "$($signals.RecentSuccess) recent success cooldown(s)"
        }
        if ($usedThisRun) {
            $score -= 100
            $reasons += "already tried this run"
        }

        $quarantined = $false
        $quarantineReason = ""
        if ($effectiveFailures -ge $MaxRecentTaskFailures) {
            $quarantined = $true
            $quarantineReason = "quarantined after $effectiveFailures effective recent failure(s)"
        } elseif (($signals.RevertedSuccess -gt 0) -and ($signals.NoChange -gt 0)) {
            $quarantined = $true
            $quarantineReason = "quarantined after reverted accepted commit plus no-change outcome"
        } elseif ($signals.LowValue -ge ($MaxRecentTaskFailures + 1)) {
            $quarantined = $true
            $quarantineReason = "quarantined after $($signals.LowValue) recent low-value/no-change outcome(s)"
        }

        if ($signals.Reasons) { $reasons += $signals.Reasons }

        $rows += [pscustomobject]@{
            Task = $task
            Id = [string]$task.Id
            Score = $score
            Quarantined = $quarantined
            QuarantineReason = $quarantineReason
            UsedThisRun = $usedThisRun
            Reasons = (($reasons | Select-Object -Unique) -join "; ")
        }
    }

    foreach ($row in $rows | Where-Object { $_.Quarantined }) {
        Add-Summary "Skipping task $($row.Id): $($row.QuarantineReason)."
    }

    Add-Summary "Task selection candidates:"
    foreach ($row in ($rows | Sort-Object Score -Descending)) {
        $state = if ($row.Quarantined) { "quarantined" } elseif ($row.UsedThisRun) { "cooldown" } else { "eligible" }
        Add-Summary "- $($row.Id): score=$($row.Score), state=$state, reasons=$($row.Reasons)"
    }

    $eligible = @($rows | Where-Object { -not $_.Quarantined })
    if (!$eligible) {
        throw "No healthy task available. All tasks are missing files or quarantined by recent failures/low-value outcomes."
    }

    $available = @($eligible | Where-Object { -not $_.UsedThisRun })
    if (!$available) { $available = $eligible }

    $choice = $available | Sort-Object Score -Descending | Select-Object -First 1
    Add-Summary "Selected task $($choice.Id): score=$($choice.Score); reasons=$($choice.Reasons)"
    Write-Host "Selected task $($choice.Id): score=$($choice.Score); $($choice.Reasons)"
    return $choice.Task
}

function Get-ChangedLineCount {
    param([string]$Before, [string]$After)

    $total = 0
    foreach ($line in git diff --numstat "$Before..$After") {
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

function Get-ChangedFilesBetween {
    param([string]$Before, [string]$After)

    return @(git diff --name-only "$Before..$After" | Where-Object { $_ })
}

function Get-AddedDiffLines {
    param([string]$DiffText)

    return @($DiffText -split "`r?`n" |
        Where-Object { $_ -match "^\+" -and $_ -notmatch "^\+\+\+" } |
        ForEach-Object { $_.Substring(1) })
}

function Get-DeadAddedVariableName {
    param([string[]]$AddedLines)

    $assignments = @{}
    foreach ($line in $AddedLines) {
        if ($line -match '^\s*([A-Za-z_][A-Za-z0-9_]*)\s*=(?!=)') {
            $name = $Matches[1]
            if ($name -notmatch '^_' -and $name -cnotmatch '^[A-Z0-9_]+$') {
                if (!$assignments.ContainsKey($name)) {
                    $assignments[$name] = 0
                }
                $assignments[$name] += 1
            }
        }
    }

    foreach ($name in $assignments.Keys) {
        $escaped = [regex]::Escape($name)
        $readCount = 0
        foreach ($line in $AddedLines) {
            if (($line -match "\b$escaped\b") -and ($line -notmatch "^\s*$escaped\s*=(?!=)")) {
                $readCount += 1
            }
        }
        if ($readCount -eq 0) {
            return $name
        }
    }

    return ""
}

function Remove-AnsiText {
    param([string]$Text)

    $esc = [char]27
    return ($Text -replace "$esc\[[0-9;?]*[ -/]*[@-~]", "")
}

function Test-AddedLinesUseErrorBody {
    param([string[]]$AddedLines)

    foreach ($line in $AddedLines) {
        if ($line -match '_set_last_error\(.*\bbody\b') {
            return $true
        }
        if ($line -match '_OLLAMA_LAST\[[^\]]*error[^\]]*\].*\bbody\b') {
            return $true
        }
        if ($line -match '\["error"\]\s*=.*\bbody\b') {
            return $true
        }
    }
    return $false
}

function Validate-AiderClaimsAgainstDiff {
    param([string]$OutputPath, [string]$DiffText)

    if (!$OutputPath -or !(Test-Path $OutputPath)) { return }
    $raw = Get-Content $OutputPath -Raw -ErrorAction SilentlyContinue
    $plain = Remove-AnsiText $raw
    $claimsHttpBodyCapture = (
        $plain -match '(?is)(full\s+)?http\s+response\s+body' -or
        $plain -match '(?is)response\s+body\s+is\s+captured' -or
        $plain -match '(?is)captur(?:e|ed|ing).*response\s+body'
    )

    if ($claimsHttpBodyCapture) {
        $addedLines = Get-AddedDiffLines -DiffText $DiffText
        if (!(Test-AddedLinesUseErrorBody -AddedLines $addedLines)) {
            throw "Rejected Aider claim/diff mismatch: claimed HTTP response body capture but diff does not use body in error recording."
        }
    }
}

function Validate-Diff {
    param([hashtable]$Task, [string]$AiderOutputPath = "")

    $allowed = @($Task.Editable | ForEach-Object { $_ -replace "/", "\" })
    $changed = @(git diff --name-only | ForEach-Object { $_ -replace "/", "\" })

    foreach ($f in $changed) {
        if ($allowed -notcontains $f) {
            throw "Changed outside task boundary: $f"
        }
    }

    if ($changed.Count -eq 0) {
        return "no-change"
    }

    $sourceChanged = $false
    foreach ($f in $changed) {
        if ($f -notmatch "^tests_.*\.py$") {
            $sourceChanged = $true
        }
    }

    if (!$AllowTestOnly -and !$sourceChanged) {
        throw "Rejected test-only patch. Use -AllowTestOnly for supervised test-only hardening."
    }

    $numstat = git diff --numstat
    $lines = 0
    foreach ($line in $numstat) {
        $parts = $line -split "\s+"
        if ($parts.Count -ge 2) {
            $a = 0
            $d = 0
            [int]::TryParse($parts[0], [ref]$a) | Out-Null
            [int]::TryParse($parts[1], [ref]$d) | Out-Null
            $lines += $a + $d
        }
    }

    if ($lines -lt $MinChangedLines) {
        throw "Rejected low-significance patch: only $lines changed lines."
    }

    $bad = git diff
    Validate-AiderClaimsAgainstDiff -OutputPath $AiderOutputPath -DiffText $bad

    $addedLines = Get-AddedDiffLines -DiffText $bad
    $deadAddedVariable = Get-DeadAddedVariableName -AddedLines $addedLines
    if ($deadAddedVariable) {
        throw "Rejected dead added variable '$deadAddedVariable' with no read in the added diff."
    }

    if ($bad -match "TODO|placeholder|would be implemented|assert True|MagicMock|Mock|should be present|should be included") {
        throw "Rejected placeholder/speculative patch language."
    }

    if ($bad.Contains("-def default_command_contracts")) {
        throw "Rejected patch that removes or breaks default_command_contracts."
    }

    if ($bad.Contains('CommandContract("/command-verify"') -or $bad.Contains("CommandContract('/command-verify'")) {
        throw "Rejected recursive /command-verify default contract."
    }

    if ($bad.Contains("output: str =") -or $bad.Contains("output=output_text") -or $bad.Contains("item.get('output')")) {
        throw "Rejected full command output capture in verifier; use bounded output_preview instead."
    }

    if (($bad -match '\+\s+body = ""') -and
        ($bad -match 'isinstance\(exc, urllib\.error\.HTTPError\)') -and
        ($bad -match '_set_last_error\(request_id, desc, started, "timeout_or_error", repr\(exc\), received_chars=0')) {
        throw "Rejected dead error-body capture in non-HTTP exception handler."
    }

    if ($bad.Contains("test_idle_propose_is_suggested") -or $bad.Contains("test_self_improve_suggestion") -or $bad.Contains("/idle propose what can I improve?")) {
        throw "Rejected invented exact self-improve suggestion test."
    }

    if ($bad.Contains("/self-improve automatically") -or $bad.Contains("/self-improve blocked") -or $bad.Contains("/self-improve disallowed")) {
        throw "Rejected blanket self-improve blocking."
    }

    if ($bad -match 'CommandContract\("\/command-verify"') {
        throw "Rejected recursive /command-verify default contract. Existing tests require /command-verify to stay outside default contracts."
    }

    if ($bad -match '"\/self-improve"\s*,\s*#|''\/self-improve''\s*,\s*#|"/self-improve",|''/self-improve'',') {
        throw "Rejected blanket /self-improve block. Manual guarded self-improve must remain suggestible as high-risk."
    }

    return "changed"
}

function Write-TaskContext {
    param([string]$Path, [hashtable]$Task)

    "# Nova Task Context" | Set-Content $Path
    "Task: $($Task.Id)" | Add-Content $Path
    "Goal: $($Task.Goal)" | Add-Content $Path
    "Mode: $Mode" | Add-Content $Path
    "Model: $Model" | Add-Content $Path
    "" | Add-Content $Path
    "## Recent commits" | Add-Content $Path
    git log --oneline -8 | Add-Content $Path
    "" | Add-Content $Path
    "## Recent task memory" | Add-Content $Path
    Get-Content $TaskMemory -Tail 80 -ErrorAction SilentlyContinue | Add-Content $Path
    "" | Add-Content $Path
    "## Structured task outcome events" | Add-Content $Path
    Get-Content $TaskEventMemory -Tail 60 -ErrorAction SilentlyContinue | Add-Content $Path
    "" | Add-Content $Path
    "## Recent mistakes" | Add-Content $Path
    Get-Content $MistakeMemory -Tail 80 -ErrorAction SilentlyContinue | Add-Content $Path
    "" | Add-Content $Path
    "## Task queue rules" | Add-Content $Path
    Get-Content .\NOVA_AGENT_TASK_QUEUE.md -TotalCount 120 | Add-Content $Path
}

function Write-TaskPrompt {
    param([string]$Path, [hashtable]$Task)

    $lines = @(
        "You are improving Nova, Daniel's local-first Windows AI assistant.",
        "",
        "You may edit only these files:",
        ($Task.Editable | ForEach-Object { "- $_" }),
        "",
        "Task:",
        $Task.Id,
        "",
        "Goal:",
        $Task.Goal,
        "",
        "Rules:",
        "- Make exactly one small real improvement, or make no changes.",
        "- Prefer source + test changes.",
        "- Do not make test-only changes unless the task is already impossible as source+test.",
        "- Do not invent APIs, classes, commands, or output text.",
        "- Do not add placeholder tests, TODOs, pass-only tests, Mock, MagicMock, or assert True.",
        "- Do not ask to add files.",
        "- Do not mention or request app.py, README.md, CHANGELOG.md, core.py, tools.py, webui.py, or startup scripts.",
        "- Do not rewrite whole files.",
        "- Keep the diff small and reversible.",
        "",
        "Acceptance:",
        "- Existing targeted tests must pass.",
        "- Nova user sanity tests must pass.",
        "- If no source-backed improvement is obvious, make no changes."
    )

    $flat = @()
    foreach ($item in $lines) {
        if ($item -is [array]) { $flat += $item } else { $flat += $item }
    }

    $flat | Set-Content $Path
}

function Append-Mistake {
    param([string]$TaskId, [string]$Reason, [string]$Category = "")

    if (!$Category) {
        $Category = Get-TaskOutcomeCategory -Reason $Reason -Result "rejected"
    }
    Record-TaskOutcome -TaskId $TaskId -Result "rejected" -Reason $Reason -Category $Category

    "" | Add-Content $MistakeMemory
    "## $(Get-Date -Format s)" | Add-Content $MistakeMemory
    "Task: $TaskId structured_event=1" | Add-Content $MistakeMemory
    "Category: $Category" | Add-Content $MistakeMemory
    "Reason: $Reason" | Add-Content $MistakeMemory
    "HEAD: $(git rev-parse --short HEAD)" | Add-Content $MistakeMemory
}

"# Nova Task Loop Summary Latest" | Set-Content $SummaryLatest
Add-Summary "Started: $(Get-Date -Format s)"
Add-Summary "Mode: $Mode"
Add-Summary "Model: $Model"
Add-Summary "AllowTestOnly: $AllowTestOnly"
Add-Summary "MinChangedLines: $MinChangedLines"
Add-Summary "MaxRecentTaskFailures: $MaxRecentTaskFailures"
Add-Summary "PreflightOnly: $PreflightOnly"
Ensure-RevertedSuccessEvents

Assert-CleanGit

if ($PreflightOnly) {
    Add-Summary ""
    Add-Summary "## Preflight task selection"
    $task = Pick-Task
    Add-Summary "Result: preflight-only"
    Add-Summary "Selected task: $($task.Id)"
    Add-Summary "Editable files: $($task.Editable -join ', ')"
    Add-Summary "Targeted tests: $($task.Tests -join ', ')"
    Add-Summary "No Aider invocation, validation run, commit, or source edit was attempted."
    Write-Host "Preflight selected task: $($task.Id)"
    Write-Host "Editable files: $($task.Editable -join ', ')"
    Write-Host "Targeted tests: $($task.Tests -join ', ')"
    Write-Host "No Aider invocation, validation run, commit, or source edit was attempted."
    Write-Host "Summary: $SummaryLatest"
    exit 0
}

Clean-GeneratedNoise
Assert-CleanGit

Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== NOVA TASK QUEUE CYCLE $i / $Cycles ====="

    Clean-GeneratedNoise
    Assert-CleanGit

    $task = Pick-Task
    [void]$RunTaskCooldown.Add([string]$task.Id)
    $before = git rev-parse --short HEAD
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $context = Join-Path $LogDir "task_context_$stamp.md"
    $prompt = Join-Path $LogDir "task_prompt_$stamp.md"
    $out = Join-Path $LogDir "task_aider_$stamp.out.txt"

    Write-TaskContext -Path $context -Task $task
    Write-TaskPrompt -Path $prompt -Task $task

    Add-Summary ""
    Add-Summary "## Cycle $i"
    Add-Summary "Task: $($task.Id)"
    Add-Summary "Before: $before"
    Add-Summary "Editable files: $($task.Editable -join ', ')"

    Write-Host "Task: $($task.Id)"
    Write-Host "Editable files: $($task.Editable -join ', ')"

    $aiderArgs = @(
        "--model", $Model,
        "--message-file", $prompt,
        "--read", $context,
        "--no-auto-commits",
        "--no-dirty-commits",
        "--no-gitignore",
        "--subtree-only",
        "--map-tokens", "0"
    )

    foreach ($f in $task.Editable) {
        $aiderArgs += $f
    }

    $denyInput = ((1..200 | ForEach-Object { "skip" }) -join "`n") + "`n"
    $denyInput | & $Aider @aiderArgs 2>&1 | Tee-Object -FilePath $out

    $text = Get-Content $out -Raw -ErrorAction SilentlyContinue
    if ($text -match "exceeds the .* token limit|has hit a token limit|Token counts below are approximate|Open URL for more info|Added app\.py|Added README\.md|Added CHANGELOG\.md|Added winlocalassistant\\core\.py|Added winlocalassistant\\tools\.py|Added winlocalassistant\\webui\.py") {
        Append-Mistake $task.Id "Aider context/token/protected-file failure" "context-protected-file"
        "$(Get-Date -Format s) task=$($task.Id) category=context-protected-file reason=context-token-or-protected-file-failure structured_event=1" | Add-Content $NoChangeTargets
        Add-Summary "Result: rejected"
        Add-Summary "Why: Aider reported token-limit/context/protected-file output."
        git reset --hard
        git clean -fd
        Clean-GeneratedNoise
        continue
    }

    if ($LASTEXITCODE -ne 0) {
        Append-Mistake $task.Id "Aider failed" "aider-failed"
        "$(Get-Date -Format s) task=$($task.Id) category=aider-failed reason=aider-failed structured_event=1" | Add-Content $NoChangeTargets
        Add-Summary "Result: rejected"
        Add-Summary "Why: Aider exited with a non-zero status."
        git reset --hard
        git clean -fd
        Clean-GeneratedNoise
        continue
    }

    Clean-GeneratedNoise

    if (!(git status --porcelain)) {
        Record-TaskOutcome -TaskId $task.Id -Result "no-change" -Reason "model found no source-backed improvement or produced identical output" -Category "no-change" -Tests $task.Tests -Before $before
        Add-Summary "Result: no change"
        Add-Summary "Why: model found no source-backed improvement or produced identical output."
        Add-Summary "Cooldown note: this task will be skipped for the rest of this run."
        "$(Get-Date -Format s) task=$($task.Id) category=no-change reason=no-change structured_event=1" | Add-Content $NoChangeTargets
        continue
    }

    git status --short
    git diff --stat

    try {
        $diffResult = Validate-Diff -Task $task -AiderOutputPath $out
        if ($diffResult -eq "no-change") {
            Record-TaskOutcome -TaskId $task.Id -Result "no-change" -Reason "no change after diff validation" -Category "no-change" -Tests $task.Tests -Before $before
            Add-Summary "Result: no change after diff validation"
            "$(Get-Date -Format s) task=$($task.Id) category=no-change reason=no-change-after-diff structured_event=1" | Add-Content $NoChangeTargets
            continue
        }

        Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
        Run-Cmd "python -m pytest -q $($task.Tests -join ' ')"
        Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"
    }
    catch {
        $category = Get-TaskOutcomeCategory -Reason $_.Exception.Message -Result "rejected"
        Append-Mistake $task.Id $_.Exception.Message $category
        "$(Get-Date -Format s) task=$($task.Id) category=$category reason=validation-or-significance-failed structured_event=1" | Add-Content $NoChangeTargets
        Add-Summary "Result: rejected"
        Add-Summary "Why: $($_.Exception.Message)"
        git diff --stat
        git reset --hard
        git clean -fd
        Clean-GeneratedNoise
        continue
    }

    Clean-GeneratedNoise

    if (!(git status --porcelain)) {
        Record-TaskOutcome -TaskId $task.Id -Result "no-change" -Reason "no source diff after generated-noise cleanup" -Category "generated-noise-dirty-state" -Tests $task.Tests -Before $before
        Add-Summary "Result: no source diff after cleanup"
        "$(Get-Date -Format s) task=$($task.Id) category=generated-noise-dirty-state reason=no-source-diff-after-cleanup structured_event=1" | Add-Content $NoChangeTargets
        continue
    }

    git add $($task.Editable)
    git commit -m "Task queue improvement: $($task.Id)"

    Clean-GeneratedNoise
    Assert-CleanGit

    $after = git rev-parse --short HEAD
    $linesChanged = Get-ChangedLineCount -Before $before -After $after
    $changedFiles = @(Get-ChangedFilesBetween -Before $before -After $after)
    $validationCommands = @(
        "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py",
        "python -m pytest -q $($task.Tests -join ' ')",
        "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"
    )
    $auditNote = "Manual audit needed if this commit is later reverted or judged weak: $after"

    Add-Summary "Result: committed"
    Add-Summary "After: $after"
    Add-Summary "Lines changed: $linesChanged"
    Add-Summary "Changed files: $($changedFiles -join ', ')"
    Add-Summary "Validation commands passed: $($validationCommands -join ' | ')"
    Add-Summary "Post-commit audit marker: $auditNote"
    Add-Summary "Why beneficial: source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated-noise cleanup, and clean-git verification."
    git diff --stat "$before..$after" | Add-Content $SummaryLatest
    Record-TaskOutcome -TaskId $task.Id -Result "committed" -Reason "source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated-noise cleanup, and clean-git verification" -Category "success-cooldown" -Tests $task.Tests -Before $before -After $after -LinesChanged $linesChanged -ChangedFiles $changedFiles -ValidationCommands $validationCommands -AuditNote $auditNote
    "$(Get-Date -Format s) task=$($task.Id) category=success-cooldown reason=recent-success-cooldown structured_event=1" | Add-Content $NoChangeTargets
}

Clean-GeneratedNoise
Assert-CleanGit

Add-Summary ""
Add-Summary "Finished task queue loop cleanly."
Write-Host "Task queue loop finished cleanly."
Write-Host "Summary: $SummaryLatest"
