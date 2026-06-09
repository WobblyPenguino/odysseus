from __future__ import annotations

import json
import os
import statistics
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from .safe_io import append_jsonl, atomic_write_json, atomic_write_text, tail_jsonl_rows, unique_path

from .config import APP_DIR

EFFICIENCY_LOG_PATH = APP_DIR / "efficiency_metrics.jsonl"
EFFICIENCY_REPORT_DIR = APP_DIR / "efficiency_reports"
_RUNTIME_PROFILER_ENABLED: bool | None = None


@dataclass
class EfficiencySample:
    kind: str
    name: str
    ok: bool
    wall_ms: float
    process_cpu_ms: float
    cpu_util_ratio: float
    estimated_joules: float
    estimated_wh: float
    started_at: str
    finished_at: str
    run_id: str
    meta: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "kind": self.kind,
            "name": self.name,
            "ok": self.ok,
            "wall_ms": round(self.wall_ms, 3),
            "process_cpu_ms": round(self.process_cpu_ms, 3),
            "cpu_util_ratio": round(self.cpu_util_ratio, 4),
            "estimated_joules": round(self.estimated_joules, 5),
            "estimated_wh": round(self.estimated_wh, 8),
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "run_id": self.run_id,
            "meta": self.meta,
        }


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _safe_float(value: Any, default: float) -> float:
    try:
        return float(value)
    except Exception:
        return default


def profiler_enabled(config: Any) -> bool:
    if _RUNTIME_PROFILER_ENABLED is False:
        return False
    return bool(getattr(config, "efficiency_profiler_enabled", True))


def set_runtime_profiler_enabled(enabled: bool) -> None:
    """Apply an in-process profiler gate for existing core/tool instances."""
    global _RUNTIME_PROFILER_ENABLED
    _RUNTIME_PROFILER_ENABLED = bool(enabled)


def _power_estimate(config: Any, wall_s: float, process_cpu_s: float, meta: dict[str, Any] | None = None) -> tuple[float, float]:
    """Return (joules, watt_hours) using a transparent heuristic.

    Nova cannot read accurate wall power from arbitrary Windows PCs without vendor
    sensors, so this intentionally stores an estimate. It is useful for spotting
    relative weak spots: long-running local model/image/tool calls, high CPU time,
    and repeated command runs.
    """
    cpu_watts = _safe_float(getattr(config, "efficiency_cpu_watts", 45.0), 45.0)
    model_watts = _safe_float(getattr(config, "efficiency_model_extra_watts", 25.0), 25.0)
    gpu_watts = _safe_float(getattr(config, "efficiency_gpu_watts", 0.0), 0.0)
    wall_s = max(0.0, float(wall_s or 0.0))
    process_cpu_s = max(0.0, float(process_cpu_s or 0.0))
    cpu_ratio = min(1.0, process_cpu_s / wall_s) if wall_s > 0 else 0.0
    kind = str((meta or {}).get("kind") or "")
    extra = model_watts if kind in {"model_call", "image_generation"} else 0.0
    # Weight CPU by measured process CPU and add optional model/GPU budget over wall time.
    joules = (cpu_watts * cpu_ratio + gpu_watts + extra) * wall_s
    return joules, joules / 3600.0


def append_efficiency_sample(config: Any, *, kind: str, name: str, ok: bool, wall_s: float, process_cpu_s: float, run_id: str | None = None, meta: dict[str, Any] | None = None, started_at: str | None = None, finished_at: str | None = None, force: bool = False) -> dict[str, Any]:
    if not force and not profiler_enabled(config):
        return {}
    meta = dict(meta or {})
    meta.setdefault("kind", kind)
    wall_s = max(0.0, float(wall_s or 0.0))
    process_cpu_s = max(0.0, float(process_cpu_s or 0.0))
    joules, wh = _power_estimate(config, wall_s, process_cpu_s, meta)
    sample = EfficiencySample(
        kind=kind,
        name=name,
        ok=bool(ok),
        wall_ms=wall_s * 1000.0,
        process_cpu_ms=process_cpu_s * 1000.0,
        cpu_util_ratio=(min(1.0, process_cpu_s / wall_s) if wall_s > 0 else 0.0),
        estimated_joules=joules,
        estimated_wh=wh,
        started_at=started_at or _now(),
        finished_at=finished_at or _now(),
        run_id=run_id or (time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]),
        meta=meta,
    )
    row = sample.to_dict()
    append_jsonl(EFFICIENCY_LOG_PATH, row, ensure_ascii=False)
    return row


def profile_call(config: Any, *, kind: str, name: str, func: Callable[[], Any], meta: dict[str, Any] | None = None) -> tuple[Any, dict[str, Any] | None]:
    if not profiler_enabled(config):
        return func(), None
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    started_at = _now()
    ok = False
    try:
        result = func()
        ok = bool(getattr(result, "ok", True))
        return result, append_efficiency_sample(
            config,
            kind=kind,
            name=name,
            ok=ok,
            wall_s=time.perf_counter() - started_wall,
            process_cpu_s=time.process_time() - started_cpu,
            meta=meta or {},
            started_at=started_at,
            finished_at=_now(),
        )
    except Exception:
        append_efficiency_sample(
            config,
            kind=kind,
            name=name,
            ok=False,
            wall_s=time.perf_counter() - started_wall,
            process_cpu_s=time.process_time() - started_cpu,
            meta={**(meta or {}), "exception": True},
            started_at=started_at,
            finished_at=_now(),
        )
        raise


def read_efficiency_samples(limit: int = 500) -> list[dict[str, Any]]:
    if _RUNTIME_PROFILER_ENABLED is False:
        return []
    return tail_jsonl_rows(EFFICIENCY_LOG_PATH, max(1, int(limit)), multiplier=1)


def clear_efficiency_samples() -> None:
    EFFICIENCY_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_text(EFFICIENCY_LOG_PATH, "")


def _group_samples(samples: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for sample in samples:
        groups.setdefault((str(sample.get("kind", "unknown")), str(sample.get("name", "unknown"))), []).append(sample)
    rows: list[dict[str, Any]] = []
    for (kind, name), items in groups.items():
        walls = [_safe_float(x.get("wall_ms"), 0.0) for x in items]
        cpus = [_safe_float(x.get("process_cpu_ms"), 0.0) for x in items]
        joules = [_safe_float(x.get("estimated_joules"), 0.0) for x in items]
        rows.append({
            "kind": kind,
            "name": name,
            "count": len(items),
            "failures": sum(1 for x in items if not bool(x.get("ok", True))),
            "avg_wall_ms": statistics.mean(walls) if walls else 0.0,
            "max_wall_ms": max(walls) if walls else 0.0,
            "avg_cpu_ms": statistics.mean(cpus) if cpus else 0.0,
            "total_estimated_joules": sum(joules),
            "last_seen": items[-1].get("finished_at", ""),
        })
    rows.sort(key=lambda x: (float(x.get("avg_wall_ms") or 0.0), float(x.get("total_estimated_joules") or 0.0)), reverse=True)
    return rows


def render_efficiency_markdown(config: Any, limit: int = 500) -> tuple[str, Path, Path, dict[str, Any]]:
    samples = read_efficiency_samples(limit=limit)
    rows = _group_samples(samples)
    total_j = sum(_safe_float(x.get("estimated_joules"), 0.0) for x in samples)
    total_wall = sum(_safe_float(x.get("wall_ms"), 0.0) for x in samples)
    total_cpu = sum(_safe_float(x.get("process_cpu_ms"), 0.0) for x in samples)
    payload = {
        "generated_at": _now(),
        "sample_count": len(samples),
        "total_wall_ms": round(total_wall, 3),
        "total_process_cpu_ms": round(total_cpu, 3),
        "total_estimated_joules": round(total_j, 5),
        "total_estimated_wh": round(total_j / 3600.0, 8),
        "power_assumptions": {
            "cpu_watts": _safe_float(getattr(config, "efficiency_cpu_watts", 45.0), 45.0),
            "gpu_watts": _safe_float(getattr(config, "efficiency_gpu_watts", 0.0), 0.0),
            "model_extra_watts": _safe_float(getattr(config, "efficiency_model_extra_watts", 25.0), 25.0),
            "note": "Power is an estimate from elapsed time and process CPU time, not a hardware wattmeter reading.",
        },
        "weakspots": rows[:20],
        "recent_samples": samples[-50:],
    }
    lines = [
        "# Nova Efficiency Report",
        "",
        "## Summary",
        f"- Samples: {len(samples)}",
        f"- Total wall time: {total_wall:.1f} ms",
        f"- Total process CPU time: {total_cpu:.1f} ms",
        f"- Estimated energy: {total_j:.3f} J ({total_j / 3600.0:.6f} Wh)",
        "- Power estimate is heuristic; use it for relative weak-spot detection, not billing-grade measurement.",
        "",
        "## Slowest / highest-cost groups",
    ]
    if not rows:
        lines.append("No efficiency samples have been recorded yet. Run commands, model calls, or `/efficiency time 3 /status`.")
    else:
        lines.extend([
            "| Kind | Name | Count | Failures | Avg wall ms | Max wall ms | Avg CPU ms | Est. joules | Last seen |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ])
        for row in rows[:25]:
            lines.append(
                f"| {row['kind']} | `{row['name']}` | {row['count']} | {row['failures']} | "
                f"{row['avg_wall_ms']:.1f} | {row['max_wall_ms']:.1f} | {row['avg_cpu_ms']:.1f} | "
                f"{row['total_estimated_joules']:.3f} | {row['last_seen']} |"
            )
    lines.extend([
        "",
        "## Improvement hints",
        "- High `model_call` wall time means prompt/context size, model size, timeout, or Ollama load time is a bottleneck.",
        "- High `tool` wall time with low CPU time usually means waiting on subprocesses, network, files or model locks.",
        "- High `chat_turn` time captures user input received → final reply returned, including planning, tools and model calls.",
        "- Re-run a command with `/efficiency time N /command ...` to compare changes before and after an optimisation.",
    ])
    EFFICIENCY_REPORT_DIR.mkdir(parents=True, exist_ok=True)
    md = unique_path(EFFICIENCY_REPORT_DIR, "efficiency_report", ".md")
    js = md.with_suffix(".json")
    atomic_write_text(md, "\n".join(lines))
    atomic_write_json(js, payload, ensure_ascii=False)
    return "\n".join(lines), md, js, payload
