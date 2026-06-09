param([int]$GpuSeconds = 90)
$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root
$Out = Join-Path $Root "logs\nova_perf"
New-Item -ItemType Directory -Force -Path $Out | Out-Null
"Nova performance collection $(Get-Date -Format o)" | Set-Content (Join-Path $Out "environment.txt")
"Python:" | Add-Content (Join-Path $Out "environment.txt")
python --version 2>&1 | Add-Content (Join-Path $Out "environment.txt")
"PowerShell:" | Add-Content (Join-Path $Out "environment.txt")
$PSVersionTable | Out-String | Add-Content (Join-Path $Out "environment.txt")
"Env:" | Add-Content (Join-Path $Out "environment.txt")
Get-ChildItem Env: | Where-Object { $_.Name -match '^(OLLAMA|NOVA|CUDA|OMP|TOKENIZERS|HF_)' -and $_.Name -notmatch 'TOKEN|KEY|SECRET' } | Sort-Object Name | Format-Table -AutoSize | Out-String | Add-Content (Join-Path $Out "environment.txt")
if (Get-Command nvidia-smi -ErrorAction SilentlyContinue) {
  nvidia-smi --query-gpu=timestamp,name,driver_version,utilization.gpu,utilization.memory,memory.used,memory.total,temperature.gpu,power.draw --format=csv -l 1 -f (Join-Path $Out "gpu_log.csv") | Out-Null &
}
if (Get-Command ollama -ErrorAction SilentlyContinue) { ollama list | Out-File -Encoding utf8 (Join-Path $Out "ollama_list.txt") }
python scripts\nova_perf_probe.py
Start-Sleep -Seconds 2
Get-Process python,ollama -ErrorAction SilentlyContinue | Select-Object ProcessName,Id,CPU,PM,WS,StartTime | Format-Table -AutoSize | Out-File -Encoding utf8 (Join-Path $Out "process_snapshot.txt")
Write-Host "Performance artifacts written to $Out"
