param(
    [string]$Repo = (Get-Location).Path,
    [int]$RefreshSeconds = 2
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Nova Teacher Loop Monitor"
$form.Width = 1250
$form.Height = 850
$form.StartPosition = "CenterScreen"

$font = New-Object System.Drawing.Font("Consolas", 10)

$tabs = New-Object System.Windows.Forms.TabControl
$tabs.Dock = "Fill"

function New-Tab {
    param([string]$Name)

    $page = New-Object System.Windows.Forms.TabPage
    $page.Text = $Name

    $box = New-Object System.Windows.Forms.RichTextBox
    $box.ReadOnly = $true
    $box.ScrollBars = "Both"
    $box.WordWrap = $false
    $box.Dock = "Fill"
    $box.Font = $font

    $page.Controls.Add($box)
    $tabs.TabPages.Add($page) | Out-Null
    return $box
}

$statusBox = New-Tab "Status"
$summaryBox = New-Tab "Summary"
$eventsBox = New-Tab "Task Events"
$traceBox = New-Tab "Mistake Traces"
$aiderBox = New-Tab "Latest Aider Output"
$mistakeBox = New-Tab "Mistakes"
$reviewBox = New-Tab "Manual Review"

$form.Controls.Add($tabs)

function Read-Tail {
    param(
        [string]$Path,
        [int]$Lines = 180
    )

    if (!(Test-Path $Path)) {
        return "Missing: $Path"
    }

    try {
        return (Get-Content $Path -Tail $Lines -ErrorAction Stop) -join [Environment]::NewLine
    }
    catch {
        return "Could not read $Path`r`n$($_.Exception.Message)"
    }
}

function Run-GitText {
    param([string[]]$Args)

    try {
        $out = & git -C $Repo @Args 2>&1
        if (!$out) {
            return "Clean"
        }
        return ($out -join [Environment]::NewLine)
    }
    catch {
        return "Git command failed: $($_.Exception.Message)"
    }
}

function Read-JsonlTail {
    param(
        [string]$Path,
        [int]$Lines = 40
    )

    if (!(Test-Path $Path)) {
        return @()
    }

    $rows = @()
    foreach ($line in (Get-Content $Path -Tail $Lines -ErrorAction SilentlyContinue)) {
        if (!$line) { continue }
        try {
            $rows += ($line | ConvertFrom-Json -ErrorAction Stop)
        }
        catch {}
    }
    return $rows
}

function Format-ValueList {
    param($Value)

    if ($null -eq $Value) { return "" }
    if ($Value -is [array]) { return (($Value | Where-Object { $_ }) -join ", ") }
    return [string]$Value
}

function Format-LoopEvent {
    param($Event)

    if ($null -eq $Event) {
        return "(none)"
    }

    $parts = @(
        "Created: $($Event.created_at)",
        "Task: $($Event.task)",
        "Result: $($Event.result)",
        "Category: $($Event.category)",
        "Stage: $($Event.stage)",
        "Model: $($Event.model)",
        "Head: $($Event.head)",
        "Before: $($Event.before)",
        "After: $($Event.after)",
        "Reason: $($Event.reason)",
        "Message: $($Event.message)",
        "Action taken: $($Event.action_taken)",
        "Changed files: $(Format-ValueList $Event.changed_files)",
        "Validation gates: $(Format-ValueList $Event.validation_gates)",
        "Validation commands: $(Format-ValueList $Event.validation_commands)",
        "Audit note: $($Event.audit_note)",
        "Diff/stat:",
        "$($Event.diff_stat)"
    )
    return ($parts -join [Environment]::NewLine).Trim()
}

function Format-LoopEvents {
    param(
        [string]$Title,
        [object[]]$Rows
    )

    if (!$Rows -or $Rows.Count -eq 0) {
        return "$Title`r`n(no JSONL rows found)"
    }

    $nl = [Environment]::NewLine
    $chunks = @($Title, "")
    foreach ($row in ($Rows | Select-Object -Last 20)) {
        $chunks += Format-LoopEvent $row
        $chunks += ("-" * 80)
    }
    return $chunks -join $nl
}

function Format-CompactEvent {
    param($Event)

    if ($null -eq $Event) { return "(none)" }
    $stage = if ($Event.stage) { " stage=$($Event.stage)" } else { "" }
    return "$($Event.created_at) task=$($Event.task) result=$($Event.result) category=$($Event.category)$stage model=$($Event.model) head=$($Event.head)"
}

function Refresh-NovaMonitor {
    $nl = [Environment]::NewLine
    $memory = Join-Path $Repo "local_ai_cycles\memory"
    $summary = Join-Path $memory "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    $mistakes = Join-Path $memory "MISTAKE_MEMORY.md"
    $events = Join-Path $memory "TASK_LOOP_EVENTS.jsonl"
    $mistakeTraces = Join-Path $memory "MISTAKES.jsonl"
    $manualReview = Join-Path $memory "NOVA_TASK_LOOP_MANUAL_REVIEW_LATEST.md"

    $gitStatus = Run-GitText @("status", "--short")
    $head = Run-GitText @("log", "--oneline", "-8")
    $eventRows = @(Read-JsonlTail $events 80)
    $mistakeRows = @(Read-JsonlTail $mistakeTraces 80)
    $latestEvent = $eventRows | Select-Object -Last 1
    $latestMistake = $mistakeRows | Select-Object -Last 1

    $latestAider = Get-ChildItem (Join-Path $Repo "local_ai_cycles") -Filter "task_aider_*.out.txt" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    if ($latestAider) {
        $aiderText = "File: $($latestAider.FullName)$nl$nl" + (Read-Tail $latestAider.FullName 260)
    } else {
        $aiderText = "No task_aider_*.out.txt found yet."
    }

    $statusLines = @(
        "Repo: $Repo",
        "Updated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')",
        "",
        "Git status:",
        $gitStatus,
        "",
        "Latest structured event:",
        (Format-CompactEvent $latestEvent),
        "",
        "Latest structured mistake:",
        (Format-CompactEvent $latestMistake),
        "",
        "Manual review note:",
        $manualReview,
        "",
        "Recent commits:",
        $head,
        "",
        "Terminal-only:",
        ".\run_nova_task_queue_loop_with_monitor.ps1 -Cycles 3 -Mode fast",
        ".\run_nova_task_queue_loop_with_monitor.ps1 -Cycles 3 -Mode code",
        "",
        "With this monitor:",
        ".\run_nova_task_queue_loop_with_monitor.ps1 -Cycles 3 -Mode fast -Monitor",
        ".\run_nova_task_queue_loop_with_monitor.ps1 -Cycles 3 -Mode code -Monitor"
    )

    $statusBox.Text = $statusLines -join $nl
    $summaryBox.Text = Read-Tail $summary 260
    $eventsBox.Text = Format-LoopEvents "Structured Task Events" $eventRows
    $traceBox.Text = Format-LoopEvents "Structured Mistake Traces" $mistakeRows
    $aiderBox.Text = $aiderText
    $mistakeBox.Text = Read-Tail $mistakes 220
    $reviewBox.Text = Read-Tail $manualReview 220
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = [Math]::Max(1, $RefreshSeconds) * 1000
$timer.Add_Tick({ Refresh-NovaMonitor })
$timer.Start()

Refresh-NovaMonitor
[void]$form.ShowDialog()
