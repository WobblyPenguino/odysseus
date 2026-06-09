param(
    [int]$Cycles = 3,
    [ValidateSet("fast", "code", "plan")]
    [string]$Mode = "code",
    [switch]$AllowTestOnly,
    [int]$MinChangedLines = 6
)

$ErrorActionPreference = "Stop"

$Repo = (Get-Location).Path
$Aider = "C:\Users\Daniel\Documents\aider-venv-py312\Scripts\aider.exe"
if (!(Test-Path $Aider)) {
    throw "Aider not found at $Aider"
}

$env:OLLAMA_API_BASE = "http://127.0.0.1:11434"

$LogDir = Join-Path $Repo "local_ai_cycles"
$MemoryDir = Join-Path $LogDir "memory"
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $MemoryDir | Out-Null

$TaskMemory = Join-Path $MemoryDir "TASK_LOOP_MEMORY.md"
$SummaryLatest = Join-Path $MemoryDir "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
$NoChangeTargets = Join-Path $MemoryDir "NO_CHANGE_TARGETS.md"
$MistakeMemory = Join-Path $MemoryDir "MISTAKE_MEMORY.md"

foreach ($f in @($TaskMemory, $SummaryLatest, $NoChangeTargets, $MistakeMemory)) {
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

$Model = Select-TaskModel -Mode $Mode

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

function Pick-Task {
    $recent = @()
    if (Test-Path $NoChangeTargets) {
        $recent = Get-Content $NoChangeTargets -Tail 40 | ForEach-Object {
            if ($_ -match "task=([^\s|]+)") { $Matches[1].Trim() }
        }
    }

    foreach ($task in $Tasks) {
        if ($recent -notcontains $task.Id) {
            $allExist = $true
            foreach ($f in $task.Editable) {
                if (!(Test-Path $f)) { $allExist = $false }
            }
            if ($allExist) { return $task }
        }
    }

    foreach ($task in $Tasks) {
        $allExist = $true
        foreach ($f in $task.Editable) {
            if (!(Test-Path $f)) { $allExist = $false }
        }
        if ($allExist) { return $task }
    }

    throw "No task has all editable files present."
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

function Validate-Diff {
    param([hashtable]$Task)

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
    if ($bad -match "TODO|placeholder|would be implemented|assert True|MagicMock|Mock|should be present|should be included") {
        throw "Rejected placeholder/speculative patch language."
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
    param([string]$TaskId, [string]$Reason)

    "" | Add-Content $MistakeMemory
    "## $(Get-Date -Format s)" | Add-Content $MistakeMemory
    "Task: $TaskId" | Add-Content $MistakeMemory
    "Reason: $Reason" | Add-Content $MistakeMemory
    "HEAD: $(git rev-parse --short HEAD)" | Add-Content $MistakeMemory
}

"# Nova Task Loop Summary Latest" | Set-Content $SummaryLatest
Add-Summary "Started: $(Get-Date -Format s)"
Add-Summary "Mode: $Mode"
Add-Summary "Model: $Model"
Add-Summary "AllowTestOnly: $AllowTestOnly"
Add-Summary "MinChangedLines: $MinChangedLines"

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

    $denyInput = "s`n" + ((1..100 | ForEach-Object { "n" }) -join "`n") + "`n"
    $denyInput | & $Aider @aiderArgs 2>&1 | Tee-Object -FilePath $out

    $text = Get-Content $out -Raw -ErrorAction SilentlyContinue
    if ($text -match "exceeds the .* token limit|Added app\.py|Added README\.md|Added CHANGELOG\.md|Added winlocalassistant\\core\.py|Added winlocalassistant\\tools\.py|Added winlocalassistant\\webui\.py") {
        Append-Mistake $task.Id "Aider context/protected-file failure"
        "$(Get-Date -Format s) task=$($task.Id) reason=context-or-protected-file-failure" | Add-Content $NoChangeTargets
        git reset --hard
        git clean -fd
        throw "Aider context/protected-file failure"
    }

    if ($LASTEXITCODE -ne 0) {
        Append-Mistake $task.Id "Aider failed"
        "$(Get-Date -Format s) task=$($task.Id) reason=aider-failed" | Add-Content $NoChangeTargets
        git reset --hard
        git clean -fd
        throw "Aider failed"
    }

    Clean-GeneratedNoise

    if (!(git status --porcelain)) {
        Add-Summary "Result: no change"
        Add-Summary "Why: model found no source-backed improvement or produced identical output."
        "$(Get-Date -Format s) task=$($task.Id) reason=no-change" | Add-Content $NoChangeTargets
        continue
    }

    git status --short
    git diff --stat

    try {
        $diffResult = Validate-Diff -Task $task
        if ($diffResult -eq "no-change") {
            Add-Summary "Result: no change after diff validation"
            "$(Get-Date -Format s) task=$($task.Id) reason=no-change-after-diff" | Add-Content $NoChangeTargets
            continue
        }

        Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"
        Run-Cmd "python -m pytest -q $($task.Tests -join ' ')"
        Run-Cmd "python -m pytest -q tests_nova_user_sanity.py tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"
    }
    catch {
        Append-Mistake $task.Id $_.Exception.Message
        "$(Get-Date -Format s) task=$($task.Id) reason=validation-or-significance-failed" | Add-Content $NoChangeTargets
        git diff --stat
        git reset --hard
        git clean -fd
        throw
    }

    Clean-GeneratedNoise
    Assert-CleanGit

    # Re-apply staged decision after clean check by checking committed diff from working tree.
    # If the cleaner left no diff, skip.
    if (!(git status --porcelain)) {
        Add-Summary "Result: no source diff after cleanup"
        "$(Get-Date -Format s) task=$($task.Id) reason=no-source-diff-after-cleanup" | Add-Content $NoChangeTargets
        continue
    }

    git add $($task.Editable)
    git commit -m "Task queue improvement: $($task.Id)"

    $after = git rev-parse --short HEAD
    $linesChanged = Get-ChangedLineCount -Before $before -After $after

    Add-Summary "Result: committed"
    Add-Summary "After: $after"
    Add-Summary "Lines changed: $linesChanged"
    Add-Summary "Why beneficial: source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated-noise cleanup, and clean-git verification."
    git diff --stat "$before..$after" | Add-Content $SummaryLatest
    "$(Get-Date -Format s) task=$($task.Id) reason=recent-success-cooldown" | Add-Content $NoChangeTargets
}

Clean-GeneratedNoise
Assert-CleanGit

Add-Summary ""
Add-Summary "Finished task queue loop cleanly."
Write-Host "Task queue loop finished cleanly."
Write-Host "Summary: $SummaryLatest"
