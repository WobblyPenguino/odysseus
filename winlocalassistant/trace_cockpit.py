from __future__ import annotations
import json, time
from pathlib import Path
from typing import Any
from .eventlog import ACTIVITY_PATH, MODEL_IO_PATH, tail_jsonl

_TRACE_KINDS = {
    "user": ["request", "chat", "interactive"],
    "planner": ["planning", "intent", "plan"],
    "model": ["llm", "model"],
    "files": ["file_write", "code_write", "code_edit"],
    "command": ["command_start", "command_done", "docker", "sandbox"],
    "validate": ["verify", "validation", "release_gate", "test"],
    "repair": ["repair", "backtrack", "recover"],
    "memory": ["memory", "idle_lessons", "autonomous_memory"],
}


def _bucket(kind: str) -> str:
    low = kind.lower()
    for bucket, needles in _TRACE_KINDS.items():
        if any(n in low for n in needles):
            return bucket
    return "other"


def build_trace(limit: int = 120, run_id: str = "") -> dict[str, Any]:
    events = []
    for item in tail_jsonl(ACTIVITY_PATH, limit=limit):
        if run_id and str(item.get("run_id", "")) != run_id and str((item.get("data") or {}).get("run_id", "")) != run_id:
            continue
        kind = str(item.get("kind", ""))
        events.append({"time": item.get("time"), "run_id": item.get("run_id") or (item.get("data") or {}).get("run_id", ""), "kind": kind, "bucket": _bucket(kind), "message": item.get("message", ""), "data": item.get("data", {})})
    counts: dict[str, int] = {}
    for ev in events:
        counts[ev["bucket"]] = counts.get(ev["bucket"], 0) + 1
    model_events = tail_jsonl(MODEL_IO_PATH, limit=20)
    return {"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "run_id": run_id, "events": events, "counts": counts, "model_event_count": len(model_events), "activity_path": str(ACTIVITY_PATH), "model_io_path": str(MODEL_IO_PATH)}


def render_trace_markdown(trace: dict[str, Any]) -> str:
    title = "# Agent Trace Cockpit"
    if trace.get("run_id"):
        title += f" — `{trace['run_id']}`"
    lines = [title, "", f"Generated: {trace.get('generated_at','')}", f"Activity log: `{trace.get('activity_path','')}`", f"Model log: `{trace.get('model_io_path','')}`", "", "## Event buckets"]
    for k in ["user", "planner", "model", "files", "command", "validate", "repair", "memory", "other"]:
        lines.append(f"- {k}: {trace.get('counts',{}).get(k,0)}")
    lines += ["", "## Recent events"]
    for ev in trace.get("events", [])[-40:]:
        msg = str(ev.get("message", "")).replace("\n", " ")[:180]
        lines.append(f"- `{ev.get('time','')}` **{ev.get('bucket')}** `{ev.get('kind')}` — {msg}")
    return "\n".join(lines)


def render_performance_dashboard(trace: dict[str, Any]) -> str:
    counts = trace.get("counts", {})
    busy = counts.get("model", 0) + counts.get("command", 0) + counts.get("validate", 0)
    lines = ["# Nova Performance Dashboard", "", f"Generated: {trace.get('generated_at','')}", f"Recent operational events: **{len(trace.get('events', []))}**", f"Model log entries sampled: **{trace.get('model_event_count', 0)}**", "", "## Activity mix"]
    for k, v in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])):
        lines.append(f"- {k}: {v}")
    lines += ["", "## Interpretation", f"- Work intensity score: {busy}", "- If model events dominate, investigate prompt size/model speed.", "- If repair/backtrack events dominate, strengthen blueprint/candidate validation.", "- If command/validate events dominate and pass, Nova is likely doing useful verification rather than being stuck."]
    return "\n".join(lines)
