from __future__ import annotations

"""Host model/runtime calibration probes for Nova.

This module is deliberately advisory unless the user explicitly enables live
benchmarks. Release-readiness can record whether Ollama/NVIDIA tools are visible
without pretending this container is the user's Windows/5070 Ti machine.
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .config import AssistantConfig
from .core import AssistantCore
from .safe_io import atomic_write_json, atomic_write_text

LATEST_JSON = Path("docs") / "NOVA_MODEL_CALIBRATION_LATEST.json"
LATEST_MD = Path("docs") / "NOVA_MODEL_CALIBRATION_LATEST.md"
DEFAULT_PROMPTS = [
    "hi",
    "what can you do?",
    "write me a Python file that prints hello",
    "explain this project",
    "make a browser game",
    "run a command safely",
]


def _tail(text: str, limit: int = 3000) -> str:
    return (text or "")[-limit:]


def _run_command(args: list[str], timeout: int = 12) -> dict[str, Any]:
    exe = shutil.which(args[0])
    result: dict[str, Any] = {
        "command": args,
        "executable": exe or "",
        "available": bool(exe),
        "ok": False,
        "returncode": None,
        "stdout_tail": "",
        "stderr_tail": "",
        "duration_sec": 0.0,
    }
    if not exe:
        result["error"] = f"{args[0]} not found on PATH"
        return result
    start = time.monotonic()
    try:
        cp = subprocess.run([exe, *args[1:]], capture_output=True, text=True, timeout=timeout)
        result.update({
            "ok": cp.returncode == 0,
            "returncode": cp.returncode,
            "stdout_tail": _tail(cp.stdout),
            "stderr_tail": _tail(cp.stderr),
        })
    except subprocess.TimeoutExpired as exc:
        result.update({
            "ok": False,
            "error": f"timed out after {timeout}s",
            "stdout_tail": _tail(exc.stdout if isinstance(exc.stdout, str) else ""),
            "stderr_tail": _tail(exc.stderr if isinstance(exc.stderr, str) else ""),
        })
    except Exception as exc:  # pragma: no cover - defensive host probe
        result.update({"ok": False, "error": repr(exc)})
    finally:
        result["duration_sec"] = round(time.monotonic() - start, 3)
    return result


def benchmark_deterministic_chat(root: Path, prompts: list[str] | None = None) -> list[dict[str, Any]]:
    """Benchmark Nova's non-broken-response path without requiring Ollama.

    Live model benchmarks are intentionally separate because an unavailable
    Ollama server can quarantine the prompt lane and slow CI/release checks.
    """
    prompts = prompts or DEFAULT_PROMPTS
    runtime = root / ".nova_runtime" / "model_calibration_chat"
    runtime.mkdir(parents=True, exist_ok=True)
    cfg = AssistantConfig(
        workspace=str(root),
        allow_mutating_tools=False,
        local_model_timeout_sec=0,
        chat_model_timeout_sec=0,
        code_model_timeout_sec=0,
        autonomous_model_timeout_sec=0,
    )
    core = AssistantCore(cfg)
    rows: list[dict[str, Any]] = []
    for prompt in prompts:
        start = time.monotonic()
        try:
            reply = core.chat(prompt)
            ok = bool(str(reply or "").strip())
            error = ""
        except Exception as exc:
            reply = ""
            ok = False
            error = repr(exc)
        rows.append({
            "prompt": prompt,
            "ok": ok,
            "duration_sec": round(time.monotonic() - start, 3),
            "reply_preview": str(reply or "")[:500],
            "fallback_or_deterministic": True,
            "error": error,
        })
    return rows


def build_model_calibration(root: str | Path = ".", *, run_benchmarks: bool = False) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    (root / "docs").mkdir(parents=True, exist_ok=True)
    probes = {
        "ollama_list": _run_command(["ollama", "list"], timeout=12),
        "ollama_ps": _run_command(["ollama", "ps"], timeout=12),
        "nvidia_smi": _run_command(["nvidia-smi"], timeout=12),
    }
    chat_benchmarks = benchmark_deterministic_chat(root) if run_benchmarks else []
    host_ready = bool(probes["ollama_list"].get("ok"))
    gpu_visible = bool(probes["nvidia_smi"].get("ok"))
    status = "READY" if host_ready else "HOST_CHECK_NEEDED"
    summary = (
        "Ollama and GPU tooling are visible; use benchmark rows to tune chat/code/autonomous timeouts."
        if host_ready else
        "Host model calibration was recorded, but Ollama is not visible in this environment. Run this on the Windows Nova PC for real timings."
    )
    payload = {
        "ok": True,
        "status": status,
        "summary": summary,
        "root": str(root),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "probes": probes,
        "gpu_visible": gpu_visible,
        "ollama_visible": host_ready,
        "benchmarks_enabled": bool(run_benchmarks),
        "chat_benchmarks": chat_benchmarks,
        "recommended_windows_commands": [
            "ollama list",
            "ollama ps",
            "nvidia-smi",
            "python -m winlocalassistant.model_calibration --root . --bench",
            "python -m winlocalassistant.release_readiness --root . --full",
        ],
    }
    atomic_write_json(root / LATEST_JSON, payload, ensure_ascii=True)
    atomic_write_text(root / LATEST_MD, render_model_calibration_markdown(payload))
    return payload


def render_model_calibration_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Model Calibration",
        "",
        f"Status: **{payload.get('status', 'UNKNOWN')}**",
        f"Summary: {payload.get('summary', '')}",
        f"Root: `{payload.get('root', '')}`",
        "",
        "## Host probes",
    ]
    for name, probe in (payload.get("probes") or {}).items():
        marker = "PASS" if probe.get("ok") else ("MISSING" if not probe.get("available") else "CHECK")
        lines.append(f"- **{marker}** `{name}`: `{' '.join(probe.get('command') or [])}` ({probe.get('duration_sec', 0)}s)")
        if probe.get("error"):
            lines.append(f"  - {probe.get('error')}")
        preview = (probe.get("stdout_tail") or probe.get("stderr_tail") or "").strip().splitlines()[:3]
        for ln in preview:
            lines.append(f"  - `{ln[:180]}`")
    benches = payload.get("chat_benchmarks") or []
    lines.extend(["", "## Chat benchmark evidence"])
    if benches:
        for row in benches:
            marker = "PASS" if row.get("ok") else "FAIL"
            lines.append(f"- **{marker}** `{row.get('prompt')}` — {row.get('duration_sec')}s")
            preview = str(row.get("reply_preview") or "").replace("\n", " ")[:180]
            if preview:
                lines.append(f"  - {preview}")
    else:
        lines.append("- Live benchmark rows were not run during release-readiness. Run `python -m winlocalassistant.model_calibration --root . --bench` on the Windows Nova PC for real timings.")
    lines.extend(["", "## Recommended local tuning flow"])
    for cmd in payload.get("recommended_windows_commands") or []:
        lines.append(f"- `{cmd}`")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe Nova host model calibration evidence.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--bench", action="store_true", help="Run deterministic chat responsiveness benchmarks. Does not require Ollama.")
    args = parser.parse_args(argv)
    payload = build_model_calibration(args.root, run_benchmarks=args.bench)
    print(render_model_calibration_markdown(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
