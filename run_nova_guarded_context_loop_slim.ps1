param(
    [int]$Cycles = 1,
    [string]$Repo = "C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530",
    [string]$AiderVenv = "C:\Users\Daniel\Documents\aider-venv-py312",
    [string]$Model = "",
    [ValidateSet("code", "plan", "fast")]
    [string]$TaskMode = "code",
    [int]$ContextBudgetKb = 64
)

$ErrorActionPreference = "Stop"
Set-Location $Repo

$Aider = Join-Path $AiderVenv "Scripts\aider.exe"
if (!(Test-Path $Aider)) {
    throw "Aider not found at $Aider"
}

$env:OLLAMA_API_BASE = "http://127.0.0.1:11434"

function Get-OllamaModelNames {
    try {
        $rows = ollama list 2>$null
        if (!$rows) { return @() }
        return $rows |
            Select-Object -Skip 1 |
            ForEach-Object {
                $parts = ($_ -split "\s+")
                if ($parts.Count -gt 0) { $parts[0] }
            } |
            Where-Object { $_ -and $_ -ne "" }
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

function Select-NovaLocalModel {
    param([string]$Mode)

    $models = @(Get-OllamaModelNames)
    $vram = Get-GpuVramMb

    Write-Host "Detected Ollama models: $($models -join ', ')"
    if ($vram -gt 0) {
        Write-Host "Detected NVIDIA VRAM: $vram MB"
    } else {
        Write-Host "Detected NVIDIA VRAM: unknown"
    }

    function HasModel([string]$Name) {
        return $models -contains $Name
    }

    if ($Mode -eq "code") {
        if ((HasModel "qwen3-coder:30b") -and (($vram -ge 14000) -or ($vram -eq 0))) { return "ollama_chat/qwen3-coder:30b" }
        if (HasModel "qwen2.5-coder:7b") { return "ollama_chat/qwen2.5-coder:7b" }
        if (HasModel "gpt-oss:20b") { return "ollama_chat/gpt-oss:20b" }
        if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }
    }

    if ($Mode -eq "plan") {
        if (HasModel "gpt-oss:20b") { return "ollama_chat/gpt-oss:20b" }
        if (HasModel "qwen3-coder:30b") { return "ollama_chat/qwen3-coder:30b" }
        if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }
    }

    if ($Mode -eq "fast") {
        if (HasModel "qwen2.5-coder:7b") { return "ollama_chat/qwen2.5-coder:7b" }
        if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }
        if (HasModel "gpt-oss:20b") { return "ollama_chat/gpt-oss:20b" }
    }

    if (HasModel "qwen3-coder:30b") { return "ollama_chat/qwen3-coder:30b" }
    if (HasModel "gpt-oss:20b") { return "ollama_chat/gpt-oss:20b" }
    if (HasModel "gemma3:12b") { return "ollama_chat/gemma3:12b" }

    throw "No suitable local Ollama model found. Run: ollama list"
}

if ([string]::IsNullOrWhiteSpace($Model)) {
    $Model = Select-NovaLocalModel -Mode $TaskMode
}

Write-Host "Selected Aider model for ${TaskMode}: $Model"

$LogDir = Join-Path $Repo "local_ai_cycles"
$MemoryDir = Join-Path $LogDir "memory"
New-Item -ItemType Directory -Force $LogDir | Out-Null
New-Item -ItemType Directory -Force $MemoryDir | Out-Null

$MistakeMemory = Join-Path $MemoryDir "MISTAKE_MEMORY.md"
$SuccessMemory = Join-Path $MemoryDir "SUCCESS_MEMORY.md"
$NoChangeTargets = Join-Path $MemoryDir "NO_CHANGE_TARGETS.md"
$LastTestResults = Join-Path $MemoryDir "LAST_TEST_RESULTS.md"

foreach ($f in @($MistakeMemory, $SuccessMemory, $NoChangeTargets, $LastTestResults)) {
    if (!(Test-Path $f)) {
        New-Item -ItemType File -Force $f | Out-Null
    }
}


$ProtectedContextMentions = @(
    "README.md",
    "CHANGELOG.md",
    "app.py",
    "start_windows_assistant.bat",
    "START_NOVA_HERE.bat",
    "winlocalassistant/core.py",
    "winlocalassistant\\core.py",
    "winlocalassistant/tools.py",
    "winlocalassistant\\tools.py",
    "winlocalassistant/webui.py",
    "winlocalassistant\\webui.py"
)

$Candidates = @(
    @{
        Target = "tests_command_suggestions.py"
        Area = "command suggestions"
        Reads = @("winlocalassistant/command_suggestions.py")
        Tests = @("tests_command_suggestions.py", "tests_command_verifier.py", "tests_runtime_usability_release_gate.py")
    },
    @{
        Target = "tests_runtime_usability_release_gate.py"
        Area = "runtime usability release gate"
        Reads = @("winlocalassistant/command_help.py", "winlocalassistant/project_request_contract.py")
        Tests = @("tests_runtime_usability_release_gate.py", "tests_validation_status_command.py")
    },
    @{
        Target = "tests_project_state_continuity.py"
        Area = "project state continuity"
        Reads = @("winlocalassistant/project_state.py")
        Tests = @("tests_project_state_continuity.py", "tests_model_context_pack.py", "tests_feature_continuity.py")
    },
    @{
        Target = "tests_model_context_pack.py"
        Area = "model context pack"
        Reads = @("winlocalassistant/model_context.py", "winlocalassistant/project_state.py")
        Tests = @("tests_model_context_pack.py", "tests_project_state_continuity.py")
    },
    @{
        Target = "tests_validation_status_command.py"
        Area = "validation status command"
        Reads = @("winlocalassistant/validate.py", "nova/validate.py")
        Tests = @("tests_validation_status_command.py", "tests_validation_reporting.py")
    },
    @{
        Target = "tests_report_hygiene.py"
        Area = "report hygiene"
        Reads = @("winlocalassistant/release_readiness.py")
        Tests = @("tests_report_hygiene.py", "tests_release_hygiene.py", "tests_runtime_usability_release_gate.py")
    },
    @{
        Target = "tests_release_hygiene.py"
        Area = "release hygiene"
        Reads = @("winlocalassistant/release_readiness.py", "winlocalassistant/release_packager.py")
        Tests = @("tests_release_hygiene.py", "tests_report_hygiene.py")
    },
    @{
        Target = "tests_model_health_timeout.py"
        Area = "model health timeout"
        Reads = @("winlocalassistant/model_health.py", "winlocalassistant/ollama.py")
        Tests = @("tests_model_health_timeout.py", "tests_runtime_usability_release_gate.py")
    },
    @{
        Target = "tests_command_verifier.py"
        Area = "command verifier"
        Reads = @("winlocalassistant/command_verifier.py")
        Tests = @("tests_command_verifier.py", "tests_command_suggestions.py")
    }
)

function Restore-GeneratedNoise {
    git restore -- docs/NOVA_LEGACY_CONTINUITY_CONTRACT.json docs/NOVA_PROJECT_STATE_LATEST.json docs/NOVA_PROJECT_STATE_LATEST.md docs/NOVA_LLM_TRAINING_LAB_LATEST.json docs/NOVA_LLM_TRAINING_LAB_LATEST.md docs/NOVA_MODEL_CALIBRATION_LATEST.json docs/NOVA_MODEL_CALIBRATION_LATEST.md docs/NOVA_RELEASE_READINESS_LATEST.json docs/NOVA_RELEASE_READINESS_LATEST.md logs/release_readiness/host_ollama_gpu_probe_evidence.stdout.txt 2>$null
    git clean -fd code_quality_gates code_reviews codebase_integrity_reports logs/project_state logs/task_evidence 2>$null
}

function Append-Mistake {
    param([string]$Reason, [string]$Target)
    "`n## $(Get-Date -Format s)" | Add-Content $MistakeMemory
    "Target: $Target" | Add-Content $MistakeMemory
    "Reason: $Reason" | Add-Content $MistakeMemory
    "HEAD: $(git rev-parse --short HEAD)" | Add-Content $MistakeMemory
    "Status:" | Add-Content $MistakeMemory
    git status --short | Add-Content $MistakeMemory
}


function Target-HasProtectedContextMentions {
    param([string]$Target)

    if (!(Test-Path $Target)) {
        return $true
    }

    $text = Get-Content $Target -Raw -ErrorAction SilentlyContinue
    foreach ($name in $ProtectedContextMentions) {
        if ($text -match [Regex]::Escape($name)) {
            return $true
        }
    }

    return $false
}

function Pick-Target {
    $recentNoChange = @()
    if (Test-Path $NoChangeTargets) {
        $recentNoChange = Get-Content $NoChangeTargets -Tail 20 | ForEach-Object {
            if ($_ -match "target=([^\s|]+)") { $Matches[1].Trim() }
        }
    }

    foreach ($c in $Candidates) {
        if ((Test-Path $c.Target) -and ($recentNoChange -notcontains $c.Target) -and !(Target-HasProtectedContextMentions $c.Target)) {
            return $c
        }
    }

    foreach ($c in $Candidates) {
        if ((Test-Path $c.Target) -and !(Target-HasProtectedContextMentions $c.Target)) {
            return $c
        }
    }

    foreach ($c in $Candidates) {
        if (Test-Path $c.Target) {
            "$(Get-Date -Format s) target=$($c.Target) reason=all-safe-targets-exhausted-or-protected-context" | Add-Content $NoChangeTargets
        }
    }

    throw "No safe target found."
}

function Add-SafeTail {
    param(
        [string]$File,
        [string]$Output,
        [int]$Tail = 80
    )

    if (!(Test-Path $File)) {
        return
    }

    Get-Content $File -Tail $Tail -ErrorAction SilentlyContinue | ForEach-Object {
        $line = $_
        $skip = $false

        foreach ($name in $ProtectedContextMentions) {
            if ($line -like "*$name*") {
                $skip = $true
            }
        }

        if ($line -match "estimated chat context|token limit|```|Added .* to the chat|Warning: it's best|Please paste|provide the current content|complete updated file|Aider v|No filename provided|exceeds the") {
            $skip = $true
        }

        if (-not $skip) {
            $line
        }
    } | Add-Content $Output
}

function Write-SlimContext {
    param([string]$Path, [hashtable]$Candidate)

    "# Nova Slim Context" | Set-Content $Path
    "Generated: $(Get-Date -Format s)" | Add-Content $Path
    "Editable target: $($Candidate.Target)" | Add-Content $Path
    "Area: $($Candidate.Area)" | Add-Content $Path

    "`n## Recent commits" | Add-Content $Path
    git log --oneline -8 | Add-Content $Path

    "`n## Recent no-change targets" | Add-Content $Path
    Add-SafeTail -File $NoChangeTargets -Output $Path -Tail 20

    "`n## Recent mistakes" | Add-Content $Path
    Add-SafeTail -File $MistakeMemory -Output $Path -Tail 80

    "`n## Recent successes" | Add-Content $Path
    Add-SafeTail -File $SuccessMemory -Output $Path -Tail 60

    "`n## Last test results" | Add-Content $Path
    Add-SafeTail -File $LastTestResults -Output $Path -Tail 80

    "`n## Approved work summary" | Add-Content $Path
    Get-Content .\NOVA_APPROVED_FEATURE_BACKLOG.md -TotalCount 80 -ErrorAction SilentlyContinue | Add-Content $Path

    "`n## Development director summary" | Add-Content $Path
    Get-Content .\NOVA_DEVELOPMENT_DIRECTOR.md -TotalCount 100 -ErrorAction SilentlyContinue | Add-Content $Path

    "`n## Target file outline" | Add-Content $Path
    Select-String -Path $Candidate.Target -Pattern "^def test_|^class |TODO|placeholder|pass\s*$|assert True" -ErrorAction SilentlyContinue |
        Select-Object -First 80 |
        ForEach-Object { "$($_.Path):$($_.LineNumber): $($_.Line.Trim())" } |
        Add-Content $Path

    "`n## Read-only implementation outlines" | Add-Content $Path
    foreach ($r in $Candidate.Reads) {
        if (Test-Path $r) {
            "`n### $r" | Add-Content $Path
            Select-String -Path $r -Pattern "^def |^class |/help|release-readiness|command|timeout|fallback|return |raise " -ErrorAction SilentlyContinue |
                Select-Object -First 100 |
                ForEach-Object { "$($_.LineNumber): $($_.Line.Trim())" } |
                Add-Content $Path
        }
    }
}

function Is-BadAiderOutput {
    param([string]$OutFile)
    if (!(Test-Path $OutFile)) { return $null }

    $text = Get-Content $OutFile -Raw -ErrorAction SilentlyContinue

    if ($text -match "exceeds the .* token limit") { return "Aider context budget exceeded" }
    # Asking to add files is allowed only because scripted n-input refuses it.
    # Actual protected additions and context-limit explosions are still fatal below.
    if ($text -match "Added app\.py|Added README\.md|Added CHANGELOG\.md|Added start_.*|Added winlocalassistant\\core\.py|Added winlocalassistant\\tools\.py|Added winlocalassistant\\webui\.py") {
        return "Aider added protected/broad files to chat"
    }
    if ($text -match "placeholder|would be implemented|assert True|MagicMock|Mock") {
        return "Aider output contained placeholder/fake-test language"
    }
    if ($text -match "please provide.*content|paste the content|I don't see the actual content|without seeing the actual content|cannot see the current implementation") {
        return "Aider claimed it could not see the editable target content"
    }
    if ($text -match "should be present|should be included|specific contract elements that should be present|expected to be present") {
        return "Aider used speculative exact-string assertion language"
    }

    return $null
}

function Is-RiskyDiff {
    param([string]$AllowedTarget)

    $status = git status --porcelain
    if ($status -match "\.venv/|\.venv\\") { return "Touched .venv" }
    if ($status -match "(^|`n) D ") { return "Deleted file" }
    if ($status -match "docs/NOVA_.*_LATEST|logs/release_readiness|code_quality_gates|code_reviews|codebase_integrity_reports") { return "Generated report/log noise" }
    if ($status -match "NOVA_GUARDED_LOCAL_IMPROVEMENT_RULES.md") { return "Touched guardrails" }
    if ($status -match "(^|`n)(\?\?|A |AM) test_") { return "Created non-standard test_*.py file" }
    if ($status -match "app.py") { return "Touched app.py" }
    if ($status -match "start_.*\.ps1|start_.*\.bat|START_NOVA_HERE\.bat") { return "Touched startup script" }

    $changedFiles = git diff --name-only
    foreach ($f in $changedFiles) {
        if ($f -ne $AllowedTarget) {
            return "Changed outside allowed target: $f"
        }
    }

    $stat = git diff --shortstat
    if ($stat -match "(\d+) insertions") {
        if ([int]$Matches[1] -gt 80) { return "Too many insertions: $($Matches[1])" }
    }
    if ($stat -match "(\d+) deletions") {
        if ([int]$Matches[1] -gt 40) { return "Too many deletions: $($Matches[1])" }
    }

    if (Test-Path $AllowedTarget) {
        $bad = Select-String -Path $AllowedTarget -Pattern "^\s*pass\s*$|TODO|placeholder|would be implemented|assert True|MagicMock|Mock" -ErrorAction SilentlyContinue
        if ($bad) {
            return "Placeholder/fake content in target"
        }
    }

    return $null
}

function Run-Cmd {
    param([string]$Command)
    Write-Host ""
    Write-Host ">>> $Command"
    $out = powershell -NoProfile -ExecutionPolicy Bypass -Command $Command 2>&1
    $out | Write-Host
    "`n>>> $Command" | Add-Content $LastTestResults
    $out | Add-Content $LastTestResults
    "exit code: $LASTEXITCODE" | Add-Content $LastTestResults
    if ($LASTEXITCODE -ne 0) { throw "Command failed: $Command" }
}

function Validate-Target {
    param([hashtable]$Candidate)

    "# Test results $(Get-Date -Format s)" | Set-Content $LastTestResults
    Run-Cmd "python -m compileall -q app.py winlocalassistant nova"
    Run-Cmd "python -m pytest -q $($Candidate.Target)"

    foreach ($t in $Candidate.Tests) {
        if ((Test-Path $t) -and ($t -ne $Candidate.Target)) {
            Run-Cmd "python -m pytest -q $t"
        }
    }

    Run-Cmd "python -m pytest -q tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py"
    Run-Cmd "python -m pytest -q tests_nova_user_sanity.py"
}

function Write-Prompt {
    param([string]$Path, [hashtable]$Candidate)

@"
You are improving Nova, Daniel's local-first Windows AI assistant.

Local model selected by loop: $Model
Task mode: $TaskMode
Context budget KB: $ContextBudgetKb

You may edit ONLY this file:
$($Candidate.Target)

Do not mention or request any other files.
Do not add files to the chat.
Do not print a full-file rewrite unless you are actually editing $($Candidate.Target).
Do not mention app.py, README.md, CHANGELOG.md, startup scripts, core.py, tools.py, or webui.py.
If the target file contains references to broad/protected files, make no changes and do not ask to add them.
Do not ask Daniel to paste file contents. The editable target is already in chat. If you cannot inspect it safely, make no changes.
Do not create new files.

Task:
Make exactly one tiny real improvement to $($Candidate.Target), or make no changes.

Allowed improvement types:
- strengthen an existing test assertion using real implementation behaviour
- add one small test case inside the existing target file if it imports real Nova code and asserts real behaviour
- improve sanity coverage for $($Candidate.Area)

Hard bans:
- no placeholder tests
- no pass
- no TODO
- no assert True
- no Mock or MagicMock
- no guessed APIs
- no new dependencies
- no broad feature work
- no generated report edits

If there is no obviously safe real improvement, make no changes.
Do not add exact-string assertions for prose unless that exact string already exists in the editable target or read-only implementation source.
Do not assert guessed response-quality contract wording. Prefer asserting existing stable keys, commands, filenames, statuses, or structures.
The PowerShell loop will run validation and commit only if safe.
"@ | Set-Content $Path
}

for ($i = 1; $i -le $Cycles; $i++) {
    Write-Host ""
    Write-Host "===== NOVA SLIM GUARDED CYCLE $i / $Cycles ====="

    Restore-GeneratedNoise

    if (git status --porcelain) {
        Write-Host "STOP: repo is dirty before cycle."
        git status --short
        exit 1
    }

    $candidate = Pick-Target
    $target = $candidate.Target
    $stamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $context = Join-Path $LogDir "slim_context_$stamp.md"
    $prompt = Join-Path $LogDir "slim_prompt_$stamp.md"
    $out = Join-Path $LogDir "slim_aider_$stamp.out.txt"

    Write-SlimContext -Path $context -Candidate $candidate

    $protectedHit = $null
    foreach ($name in $ProtectedContextMentions) {
        if (Select-String -Path $context -Pattern ([Regex]::Escape($name)) -Quiet -ErrorAction SilentlyContinue) {
            $protectedHit = $name
            break
        }
    }

    if ($protectedHit) {
        Write-Host "STOP: Slim context contains protected file mention before Aider runs: $protectedHit"
        Append-Mistake "Slim context contained protected file mention before Aider: $protectedHit" $target
        "$(Get-Date -Format s) target=$target reason=protected-context-mention-$protectedHit" | Add-Content $NoChangeTargets
        continue
    }

    Write-Prompt -Path $prompt -Candidate $candidate

    $contextKb = [Math]::Round((Get-Item $context).Length / 1KB, 1)
    Write-Host "Editable target: $target"
    Write-Host "Slim context: $contextKb KB"

    if ($contextKb -gt $ContextBudgetKb) {
        Write-Host "STOP: Slim context exceeds budget: $contextKb KB > $ContextBudgetKb KB"
        Append-Mistake "Slim context exceeds budget: $contextKb KB > $ContextBudgetKb KB" $target
        "$(Get-Date -Format s) target=$target reason=context-budget-exceeded" | Add-Content $NoChangeTargets
        continue
    }

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

    foreach ($r in $candidate.Reads) {
        if (Test-Path $r) {
            $aiderArgs += @("--read", $r)
        }
    }

    $aiderArgs += $target

    # Feed "n" repeatedly so Aider refuses add-file/context-expansion prompts.
    # This prevents broad files such as app.py, README.md, core.py, tools.py, or webui.py
    # from being added to the chat after the first model response.
    $denyInput = ((1..200 | ForEach-Object { "n" }) -join "`n") + "`n"
    $denyInput | & $Aider @aiderArgs 2>&1 | Tee-Object -FilePath $out

    if ((Select-String -Path $out -Pattern "Add file to the chat" -Quiet -ErrorAction SilentlyContinue) -and
        !(Select-String -Path $out -Pattern "exceeds the .* token limit|Added app\.py|Added README\.md|Added CHANGELOG\.md|Added start_.*|Added winlocalassistant\\core\.py|Added winlocalassistant\\tools\.py|Added winlocalassistant\\webui\.py" -Quiet -ErrorAction SilentlyContinue)) {
        Write-Host "Aider asked to add files, but scripted n-input should have refused them. Continuing to diff/test checks."
    }

    $badOutput = Is-BadAiderOutput -OutFile $out
    if ($badOutput) {
        Write-Host "STOP: $badOutput"
        Append-Mistake $badOutput $target
        "$(Get-Date -Format s) target=$target reason=$badOutput" | Add-Content $NoChangeTargets
        git reset --hard
        git clean -fd
        exit 1
    }

    if ($LASTEXITCODE -ne 0) {
        Append-Mistake "Aider failed" $target
        git reset --hard
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    if (!(git status --porcelain)) {
        "$(Get-Date -Format s) target=$target" | Add-Content $NoChangeTargets
        "## $(Get-Date -Format s)`nTarget file: $target`nCommit hash: none - no change made`nWhy safe: no diff created.`n" | Add-Content $SuccessMemory
        Write-Host "No changes made for $target. Continuing."
        continue
    }

    git status --short
    git diff --stat

    $risk = Is-RiskyDiff -AllowedTarget $target
    if ($risk) {
        Write-Host "STOP: Risky diff detected: $risk"
        Append-Mistake $risk $target
        git diff
        git reset --hard
        git clean -fd
        exit 1
    }

    try {
        Validate-Target -Candidate $candidate
    }
    catch {
        Write-Host "STOP: Validation failed."
        Append-Mistake "Validation failed" $target
        "$(Get-Date -Format s) target=$target reason=validation-failed" | Add-Content $NoChangeTargets
        git reset --hard
        git clean -fd
        exit 1
    }

    Restore-GeneratedNoise

    $risk = Is-RiskyDiff -AllowedTarget $target
    if ($risk) {
        Write-Host "STOP: Risk after validation: $risk"
        Append-Mistake $risk $target
        git reset --hard
        git clean -fd
        exit 1
    }

    git add $target
    git commit -m "Slim guarded improvement: $target"

    "## $(Get-Date -Format s)`nTarget file: $target`nCommit hash: $(git rev-parse --short HEAD)`nTests passed: yes`n" | Add-Content $SuccessMemory
    Write-Host "Cycle $i committed successfully."
}

Write-Host "Finished $Cycles slim guarded cycles."
