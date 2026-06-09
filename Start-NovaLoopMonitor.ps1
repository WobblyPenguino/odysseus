param(
    [string]$Repo = (Get-Location).Path,
    [int]$RefreshSeconds = 2
)

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$form = New-Object System.Windows.Forms.Form
$form.Text = "Nova Teacher Loop Monitor"
$form.Width = 1200
$form.Height = 800
$form.StartPosition = "CenterScreen"

$font = New-Object System.Drawing.Font("Consolas", 10)

$tabs = New-Object System.Windows.Forms.TabControl
$tabs.Dock = "Fill"

function New-Tab {
    param([string]$Name)
    $page = New-Object System.Windows.Forms.TabPage
    $page.Text = $Name
    $box = New-Object System.Windows.Forms.TextBox
    $box.Multiline = $true
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
$aiderBox = New-Tab "Latest Aider Output"
$mistakeBox = New-Tab "Mistakes"

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
        return "Could not read $Path`n$($_.Exception.Message)"
    }
}

function Refresh-NovaMonitor {
    $memory = Join-Path $Repo "local_ai_cycles\memory"
    $summary = Join-Path $memory "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    $mistakes = Join-Path $memory "MISTAKE_MEMORY.md"

    $gitStatus = ""
    try {
        $gitStatus = (& git -C $Repo status --short 2>&1) -join [Environment]::NewLine
        if ([string]::IsNullOrWhiteSpace($gitStatus)) {
            $gitStatus = "Clean"
        }
    }
    catch {
        $gitStatus = "Could not run git status: $($_.Exception.Message)"
    }

    $head = ""
    try {
        $head = (& git -C $Repo log --oneline -8 2>&1) -join [Environment]::NewLine
    }
    catch {
        $head = "Could not read git log: $($_.Exception.Message)"
    }

    $latestAider = Get-ChildItem (Join-Path $Repo "local_ai_cycles") -Filter "task_aider_*.out.txt" -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending |
        Select-Object -First 1

    $aiderText = "No task_aider_*.out.txt found yet."
    if ($latestAider) {
        $aiderText = "File: $($latestAider.FullName)`r`n`r`n" + (Read-Tail $latestAider.FullName 260)
    }

    $statusBox.Text = @"
Repo: $Repo
Updated: $(Get-Date -Format "yyyy-MM-dd HH:mm:ss")

Git status:
$gitStatus

Recent commits:
$head

Useful commands:
.\run_nova_task_queue_loop_with_monitor.ps1 -Cycles 3 -Mode fast
.\run_nova_task_queue_loop_with_monitor.ps1 -Cycles 3 -Mode code
"@

    $summaryBox.Text = Read-Tail $summary 260
    $aiderBox.Text = $aiderText
    $mistakeBox.Text = Read-Tail $mistakes 220
}

$timer = New-Object System.Windows.Forms.Timer
$timer.Interval = [Math]::Max(1, $RefreshSeconds) * 1000
$timer.Add_Tick({ Refresh-NovaMonitor })
$timer.Start()

Refresh-NovaMonitor
[void]$form.ShowDialog()
