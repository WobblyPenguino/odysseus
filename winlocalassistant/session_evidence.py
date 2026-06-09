from __future__ import annotations

from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

from .eventlog import ACTIVITY_PATH, MODEL_IO_PATH, tail_jsonl

SIGNIFICANT_KINDS = {
    "run_started", "plan_start", "pipeline_preflight", "pipeline_stage_start", "pipeline_stage_done",
    "step_start", "step_failed", "step_done", "tool_result", "llm_attempt", "llm_failed", "llm_rejected",
    "file_write", "project_open", "browser_smoke", "bug_review", "regression_sweep", "nova_doctor",
    "autonomous_cycle_start", "autonomous_observe", "autonomous_target_resolved", "autonomous_cycle_done",
}


def _event_run_id(event: dict[str, Any]) -> str:
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    return str(event.get("run_id") or data.get("run_id") or data.get("request_id") or "")


def _summarise_event(event: dict[str, Any]) -> str:
    data = event.get("data") if isinstance(event.get("data"), dict) else {}
    bits = [str(event.get("time", "")), f"`{event.get('kind','')}`", str(event.get("message", ""))]
    extras: list[str] = []
    for key in ("tool", "file", "path", "ok", "cycle", "route", "stage"):
        if key in data and data.get(key) not in (None, ""):
            extras.append(f"{key}={data.get(key)}")
    if extras:
        bits.append("(" + ", ".join(extras[:5]) + ")")
    return " ".join(x for x in bits if x).strip()


def build_session_evidence(run_id: str = "latest", *, limit: int = 120) -> dict[str, Any]:
    try:
        n = max(20, min(int(limit or 120), 500))
    except Exception:
        n = 120
    events = tail_jsonl(ACTIVITY_PATH, n, session_only=False)
    model_events = tail_jsonl(MODEL_IO_PATH, max(20, n // 3), session_only=False) if MODEL_IO_PATH.exists() else []
    requested = (run_id or "latest").strip()
    resolved = requested
    if requested in {"", "latest", "last"}:
        for event in reversed(events):
            rid = _event_run_id(event)
            if rid:
                resolved = rid
                break
    selected = [event for event in events if _event_run_id(event) == resolved] if resolved not in {"", "latest", "last"} else events[-n:]
    if not selected:
        selected = [event for event in events if event.get("kind") in SIGNIFICANT_KINDS][-50:]
    kind_counts = Counter(str(e.get("kind", "")) for e in selected)
    tools = Counter()
    files: set[str] = set()
    failures: list[str] = []
    for event in selected:
        data = event.get("data") if isinstance(event.get("data"), dict) else {}
        if data.get("tool"):
            tools[str(data["tool"])] += 1
        if data.get("file"):
            files.add(str(data["file"]))
        if data.get("path") and any(str(data.get("path", "")).endswith(s) for s in (".py", ".js", ".html", ".css", ".md", ".json")):
            files.add(str(data["path"]))
        if event.get("kind") in {"step_failed", "llm_failed", "llm_rejected", "known_error_recovery_failed", "backtrack_failed"}:
            failures.append(_summarise_event(event))
    model_summary = []
    for row in model_events[-10:]:
        model_summary.append({
            "phase": row.get("phase"),
            "time": row.get("time"),
            "response_preview": str(row.get("response_preview", ""))[:240],
        })
    return {
        "requested_run_id": requested,
        "resolved_run_id": resolved,
        "event_count": len(selected),
        "kind_counts": dict(kind_counts.most_common()),
        "tools": dict(tools.most_common()),
        "files": sorted(files)[:40],
        "failures": failures[:20],
        "events": selected[-80:],
        "model_events": model_summary,
    }


def render_session_evidence(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Session Evidence",
        "",
        f"Run: `{payload.get('resolved_run_id') or '(no run id found)'}`",
        f"Events: {payload.get('event_count', 0)}",
        "",
        "## Event kinds",
    ]
    if payload.get("kind_counts"):
        lines += [f"- `{k}`: {v}" for k, v in payload["kind_counts"].items()]
    else:
        lines.append("- No recent events found.")
    lines += ["", "## Tools observed"]
    lines += [f"- `{k}`: {v}" for k, v in (payload.get("tools") or {}).items()] or ["- No tool names found in recent events."]
    lines += ["", "## Files mentioned"]
    lines += [f"- `{x}`" for x in (payload.get("files") or [])[:20]] or ["- No file paths found in recent events."]
    if payload.get("failures"):
        lines += ["", "## Failures / blockers"] + [f"- {x}" for x in payload["failures"][:10]]
    lines += ["", "## Timeline"]
    for event in payload.get("events", [])[-25:]:
        lines.append(f"- {_summarise_event(event)}")
    if payload.get("model_events"):
        lines += ["", "## Recent model I/O previews"]
        for row in payload["model_events"][-5:]:
            preview = str(row.get("response_preview") or "").replace("\n", " ")[:180]
            lines.append(f"- {row.get('time','')} `{row.get('phase','')}` {preview}")
    lines += ["", "## Guardrail", "Use this evidence before claiming a task succeeded or before retrying a failed autonomous/coding step."]
    return "\n".join(lines)
