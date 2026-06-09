from __future__ import annotations

"""Local AI performance tuning and benchmarking helpers for Nova.

These helpers implement the safe parts of the performance research PDF: set
non-destructive runtime defaults, report hardware/runtime readiness, and produce
reproducible benchmark commands/artifacts. They do not change Windows Defender,
install drivers, move models, or store secrets.
"""

import csv
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

SAFE_ENV_DEFAULTS: dict[str, str] = {
    "OLLAMA_FLASH_ATTENTION": "1",
    "TOKENIZERS_PARALLELISM": "false",
    "CUDA_LAUNCH_BLOCKING": "0",
    "NOVA_PERF_ENV_PROFILE": "safe-local-ai-v1",
}

PATCH_ID = "local-ai-performance-tuning-v1"


def _sensible_omp_default() -> str:
    try:
        cores = os.cpu_count() or 4
        return str(max(1, min(8, cores // 2 or 1)))
    except Exception:
        return "4"


def apply_startup_performance_environment() -> dict[str, Any]:
    """Apply safe env defaults without overwriting user choices."""
    applied: dict[str, str] = {}
    preserved: dict[str, str] = {}
    for key, value in SAFE_ENV_DEFAULTS.items():
        if os.environ.get(key):
            preserved[key] = "already-set"
        else:
            os.environ[key] = value
            applied[key] = value
    if os.environ.get("OMP_NUM_THREADS"):
        preserved["OMP_NUM_THREADS"] = "already-set"
    else:
        value = _sensible_omp_default()
        os.environ["OMP_NUM_THREADS"] = value
        applied["OMP_NUM_THREADS"] = value
    return {"ok": True, "patch_id": PATCH_ID, "applied": applied, "preserved": preserved}


def _run_short(cmd: list[str] | None, timeout: int = 5) -> dict[str, Any]:
    if not cmd or not cmd[0]:
        return {"ok": False, "available": False, "stdout": "", "stderr": ""}
    try:
        cp = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {
            "ok": cp.returncode == 0,
            "available": True,
            "returncode": cp.returncode,
            "stdout": cp.stdout.strip()[:2000],
            "stderr": cp.stderr.strip()[:1000],
        }
    except Exception as exc:
        return {"ok": False, "available": True, "error": str(exc), "stdout": "", "stderr": ""}


def collect_performance_status(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    env_keys = [*SAFE_ENV_DEFAULTS.keys(), "OMP_NUM_THREADS", "HF_HOME", "OLLAMA_MODELS", "NOVA_API_TOKEN"]
    env: dict[str, dict[str, Any]] = {}
    for key in env_keys:
        value = os.environ.get(key)
        if value is None:
            env[key] = {"set": False, "value": ""}
        elif "TOKEN" in key or "KEY" in key or "SECRET" in key:
            env[key] = {"set": True, "value": "<redacted>"}
        else:
            env[key] = {"set": True, "value": value}

    ollama = shutil.which("ollama")
    nvidia_smi = shutil.which("nvidia-smi")
    gpu = _run_short([nvidia_smi, "--query-gpu=name,memory.total,driver_version", "--format=csv,noheader"] if nvidia_smi else None, timeout=5)
    model_dirs = []
    for maybe in [os.environ.get("OLLAMA_MODELS"), str(Path.home() / ".ollama" / "models"), str(root / "models")]:
        if not maybe:
            continue
        p = Path(maybe)
        try:
            model_dirs.append({"path": str(p), "exists": p.exists(), "is_dir": p.is_dir()})
        except Exception as exc:
            model_dirs.append({"path": str(p), "exists": False, "is_dir": False, "error": str(exc)})

    return {
        "ok": True,
        "patch_id": PATCH_ID,
        "root": str(root),
        "platform": platform.platform(),
        "python": platform.python_version(),
        "env": env,
        "tools": {"ollama": bool(ollama), "ollama_path": ollama or "", "nvidia_smi": bool(nvidia_smi), "nvidia_smi_path": nvidia_smi or ""},
        "gpu_query": gpu,
        "model_dirs": model_dirs,
        "safe_env_defaults": SAFE_ENV_DEFAULTS | {"OMP_NUM_THREADS": _sensible_omp_default()},
        "manual_only": [
            "Windows Defender model-folder exclusion must be applied manually as Administrator and only for trusted model folders.",
            "Driver updates, BIOS, large-page privileges and model relocation are not changed by Nova automatically.",
        ],
        "recommended_next_steps": [
            "Run /perf-benchmark --write-scripts and execute the generated PowerShell script on the target PC.",
            "Prefer quantized GPU-fit models such as q4_K_M/q5_K_M when quality allows.",
            "Keep models on NVMe and consider a Windows Defender exclusion only for trusted model folders.",
            "Use NOVA_PERF_MODE=benchmark to reduce background noise while collecting timings.",
        ],
    }


def render_performance_status(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Local AI Performance Status",
        "",
        f"Patch: `{payload.get('patch_id')}`",
        f"Root: `{payload.get('root')}`",
        f"Python: `{payload.get('python')}`",
        f"Platform: `{payload.get('platform')}`",
        "",
        "## Runtime tools",
    ]
    tools = payload.get("tools", {}) or {}
    lines.append(f"- Ollama: `{tools.get('ollama')}` {tools.get('ollama_path') or ''}")
    lines.append(f"- nvidia-smi: `{tools.get('nvidia_smi')}` {tools.get('nvidia_smi_path') or ''}")
    gpu = payload.get("gpu_query", {}) or {}
    if gpu.get("stdout"):
        lines += ["", "## GPU", "```", str(gpu.get("stdout")), "```"]
    elif gpu.get("error"):
        lines += ["", "## GPU", f"nvidia-smi error: `{gpu.get('error')}`"]
    lines += ["", "## Environment"]
    for key, meta in (payload.get("env", {}) or {}).items():
        lines.append(f"- {key}: set=`{meta.get('set')}` value=`{meta.get('value')}`")
    lines += ["", "## Model directories"]
    for item in payload.get("model_dirs", []):
        lines.append(f"- `{item.get('path')}` exists=`{item.get('exists')}` dir=`{item.get('is_dir')}`")
    lines += ["", "## Manual-only changes Nova will not apply automatically"]
    for item in payload.get("manual_only", []):
        lines.append(f"- {item}")
    lines += ["", "## Next steps"]
    for item in payload.get("recommended_next_steps", []):
        lines.append(f"- {item}")
    lines += ["", "Use `/perf-benchmark --write-scripts` to generate reproducible benchmark scripts and `/perf-artifact-checklist` before uploading results."]
    return "\n".join(lines)


def build_tuning_plan() -> dict[str, Any]:
    return {
        "ok": True,
        "patch_id": PATCH_ID,
        "principles": [
            "Prefer GPU-fit quantized models before trying broad code rewrites.",
            "Measure before/after using the same prompts and save GPU/CPU logs.",
            "Do not silently apply admin/security changes such as Defender exclusions.",
            "Keep CLI/API/UI behavior compatible; performance defaults must be overrideable by env vars.",
        ],
        "phases": [
            {"phase": "baseline", "actions": ["/perf-status", "/perf-benchmark --write-scripts", "run scripts/nova_perf_collect.ps1"], "acceptance": "baseline JSON/CSV logs created"},
            {"phase": "safe env", "actions": ["startup env defaults: OLLAMA_FLASH_ATTENTION=1, TOKENIZERS_PARALLELISM=false, CUDA_LAUNCH_BLOCKING=0"], "acceptance": "/perf-status shows defaults set or preserved"},
            {"phase": "model choice", "actions": ["compare current model vs q4_K_M/q5_K_M GPU-fit model", "capture tokens/sec and p95 latency"], "acceptance": "chosen model improves latency without unacceptable quality loss"},
            {"phase": "orchestration", "actions": ["reduce repeated subprocess/model calls", "keep Ollama server warm", "route trivial planning to deterministic tools first"], "acceptance": "Nova command p95 latency reduced with existing tests passing"},
        ],
        "rollback": [
            "Unset env vars to return to previous runtime behavior.",
            "Switch back to previous model name in Nova settings/launchers.",
            "Do not keep Defender exclusions if model source is not trusted.",
        ],
    }


def render_tuning_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Local AI Performance Tuning Plan", "", f"Patch: `{payload.get('patch_id')}`", "", "## Principles"]
    for item in payload.get("principles", []):
        lines.append(f"- {item}")
    lines += ["", "## Phases"]
    for phase in payload.get("phases", []):
        lines.append(f"### {phase.get('phase')}")
        for action in phase.get("actions", []):
            lines.append(f"- {action}")
        lines.append(f"Acceptance: `{phase.get('acceptance')}`")
        lines.append("")
    lines += ["## Rollback"]
    for item in payload.get("rollback", []):
        lines.append(f"- {item}")
    return "\n".join(lines)


def benchmark_plan_payload(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    commands = [
        "python app.py /version",
        "python app.py /perf-status",
        "python app.py /validation-status",
        "python app.py /model-health",
        "python app.py /model-benchmark",
        "python app.py /do \"Explain how a binary search tree works in 120 words.\"",
        "python app.py /coding-plan \"Add a small regression test for command routing.\"",
    ]
    return {
        "ok": True,
        "patch_id": PATCH_ID,
        "root": str(root),
        "metrics": ["wall_ms", "exit_code", "stdout_bytes", "stderr_bytes", "approx_output_tokens", "gpu_utilization", "gpu_memory_mb", "cpu_percent", "rss_mb"],
        "commands": commands,
        "outputs": {
            "summary_json": "logs/nova_perf/summary.json",
            "command_csv": "logs/nova_perf/command_timings.csv",
            "gpu_csv": "logs/nova_perf/gpu_log.csv",
            "env_txt": "logs/nova_perf/environment.txt",
            "ollama_models_txt": "logs/nova_perf/ollama_list.txt",
        },
    }


def render_benchmark_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Performance Benchmark Plan", "", f"Patch: `{payload.get('patch_id')}`", "", "## Metrics"]
    for metric in payload.get("metrics", []):
        lines.append(f"- {metric}")
    lines += ["", "## Commands"]
    for command in payload.get("commands", []):
        lines.append(f"- `{command}`")
    lines += ["", "## Outputs"]
    for name, path in (payload.get("outputs", {}) or {}).items():
        lines.append(f"- {name}: `{path}`")
    lines += ["", "Run `/perf-benchmark --write-scripts` to write `scripts/nova_perf_collect.ps1` and `scripts/nova_perf_probe.py`."]
    return "\n".join(lines)


def write_benchmark_scripts(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    scripts = root / "scripts"
    scripts.mkdir(exist_ok=True)
    (scripts / "nova_perf_probe.py").write_text(_PY_PROBE, encoding="utf-8")
    (scripts / "nova_perf_collect.ps1").write_text(_PS_COLLECT, encoding="utf-8")
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "NOVA_LOCAL_AI_PERFORMANCE_TUNING.md").write_text(_PERF_DOC, encoding="utf-8")
    return {
        "ok": True,
        "written": ["scripts/nova_perf_probe.py", "scripts/nova_perf_collect.ps1", "docs/NOVA_LOCAL_AI_PERFORMANCE_TUNING.md"],
        "next": [
            "powershell -ExecutionPolicy Bypass -File scripts\\nova_perf_collect.ps1",
            "Compress-Archive -Path logs\\nova_perf -DestinationPath nova_perf_results.zip -Force",
        ],
    }


def render_write_result(payload: dict[str, Any]) -> str:
    lines = ["# Nova Performance Benchmark Scripts", "", f"OK: `{payload.get('ok')}`", "", "## Written"]
    for path in payload.get("written", []):
        lines.append(f"- `{path}`")
    lines += ["", "## Run next"]
    for cmd in payload.get("next", []):
        lines.append(f"- `{cmd}`")
    return "\n".join(lines)


def render_artifact_checklist() -> str:
    return """# Nova Performance Artifact Checklist

Upload these after running the benchmark collector:

- `logs/nova_perf/summary.json`
- `logs/nova_perf/command_timings.csv`
- `logs/nova_perf/gpu_log.csv` if present
- `logs/nova_perf/environment.txt`
- `logs/nova_perf/ollama_list.txt`
- `logs/validation_latest.txt`
- a short note naming the active model, whether Ollama was already warm, and whether Windows Defender/NVMe/driver changes were applied

Privacy note: GPU logs reveal hardware/driver info. API tokens are not collected and should not be pasted.
"""

_PY_PROBE = r'''from __future__ import annotations
import csv, json, os, subprocess, sys, time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "logs" / "nova_perf"
OUT.mkdir(parents=True, exist_ok=True)
COMMANDS = [
    [sys.executable, "app.py", "/version"],
    [sys.executable, "app.py", "/perf-status"],
    [sys.executable, "app.py", "/validation-status"],
    [sys.executable, "app.py", "/model-health"],
    [sys.executable, "app.py", "/do", "Explain how a binary search tree works in 120 words."],
    [sys.executable, "app.py", "/coding-plan", "Add a small regression test for command routing."],
]

def approx_tokens(text: str) -> int:
    return max(1, len(text.split()))

rows = []
for idx, cmd in enumerate(COMMANDS, 1):
    start = time.perf_counter()
    cp = subprocess.run(cmd, cwd=str(ROOT), text=True, capture_output=True, timeout=240)
    elapsed = (time.perf_counter() - start) * 1000
    out_path = OUT / f"command_{idx:02d}.txt"
    out_path.write_text(cp.stdout + "\n\n--- STDERR ---\n" + cp.stderr, encoding="utf-8", errors="replace")
    rows.append({
        "index": idx,
        "command": " ".join(cmd),
        "returncode": cp.returncode,
        "wall_ms": round(elapsed, 2),
        "stdout_bytes": len(cp.stdout.encode("utf-8", errors="ignore")),
        "stderr_bytes": len(cp.stderr.encode("utf-8", errors="ignore")),
        "approx_output_tokens": approx_tokens(cp.stdout),
        "tokens_per_sec_rough": round(approx_tokens(cp.stdout) / max(elapsed / 1000, 0.001), 2),
        "output_file": str(out_path.relative_to(ROOT)),
    })
with (OUT / "command_timings.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader(); writer.writerows(rows)
summary = {"ok": all(r["returncode"] == 0 for r in rows), "rows": rows, "env": {k: ("<redacted>" if "TOKEN" in k else os.environ.get(k,"")) for k in ["OLLAMA_FLASH_ATTENTION","TOKENIZERS_PARALLELISM","CUDA_LAUNCH_BLOCKING","OMP_NUM_THREADS","OLLAMA_MODELS","NOVA_PERF_MODE"]}}
(OUT / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
print(json.dumps(summary, indent=2))
'''

_PS_COLLECT = r'''param([int]$GpuSeconds = 90)
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
'''

_PERF_DOC = r'''# Nova Local AI Performance Tuning

This document implements the safe parts of the uploaded performance research PDF.

## Commands

- `/perf-status` - inspect local AI runtime status, env flags and GPU tool availability.
- `/perf-tune-plan` - show the staged improvement plan and rollback notes.
- `/perf-benchmark` - show benchmark metrics and commands.
- `/perf-benchmark --write-scripts` - write `scripts/nova_perf_collect.ps1` and `scripts/nova_perf_probe.py`.
- `/perf-artifact-checklist` - show exactly what to upload for further tuning.

## What Nova sets automatically

Nova sets these only when the user has not already set them:

- `OLLAMA_FLASH_ATTENTION=1`
- `TOKENIZERS_PARALLELISM=false`
- `CUDA_LAUNCH_BLOCKING=0`
- `OMP_NUM_THREADS=<sensible default>`

## What Nova does not do automatically

- Windows Defender exclusions.
- Driver installation or rollback.
- Admin/elevated large-page configuration.
- Moving model files.
- Downloading or replacing models.

Those are manual because they affect security or system configuration.
'''
