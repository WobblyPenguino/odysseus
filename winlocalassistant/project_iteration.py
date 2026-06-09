from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path

from .safe_io import append_text_line, atomic_write_text
from typing import Any


@dataclass
class ProjectIterationEvent:
    round_no: int
    stage: str
    ok: bool
    summary: str
    problems: list[str] = field(default_factory=list)
    repair_source: str = ""
    changed_files: list[str] = field(default_factory=list)
    quality_percent: float | None = None
    timestamp: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        if not data.get("timestamp"):
            data["timestamp"] = _now()
        return data


def append_project_iteration_event(root: Path, event: ProjectIterationEvent | dict[str, Any]) -> Path:
    """Append one project development/verification event to PROJECT_ITERATION_LOG.jsonl.

    This intentionally appends one JSON object per line instead of reading and
    rewriting the whole file. Generated projects can accumulate many repair and
    verification events, so append-only logging avoids unnecessary I/O, reduces
    corruption risk, and keeps prior events intact if a later write fails.
    """
    root = Path(root)
    path = root / "PROJECT_ITERATION_LOG.jsonl"
    path.parent.mkdir(parents=True, exist_ok=True)
    data = event.to_dict() if isinstance(event, ProjectIterationEvent) else dict(event)
    data.setdefault("timestamp", _now())
    line = json.dumps(_safe_json(data), ensure_ascii=False, default=str)
    append_text_line(path, line)
    return path


def build_project_iteration_event(round_no: int, stage: str, quality_result: Any, repair_source: str = "", changed_files: list[str] | None = None) -> ProjectIterationEvent:
    """Create a compact event from a ToolResult-like object or verification dict."""
    ok = bool(getattr(quality_result, "ok", False)) if not isinstance(quality_result, dict) else bool(quality_result.get("ok", False))
    summary = str(getattr(quality_result, "summary", "") if not isinstance(quality_result, dict) else quality_result.get("summary", ""))
    data = getattr(quality_result, "data", {}) if not isinstance(quality_result, dict) else quality_result
    problems = _extract_problem_summaries(data)
    quality_percent = _extract_quality_percent(data)
    return ProjectIterationEvent(
        round_no=round_no,
        stage=stage,
        ok=ok,
        summary=summary or ("passed" if ok else "failed"),
        problems=problems,
        repair_source=repair_source,
        changed_files=list(changed_files or []),
        quality_percent=quality_percent,
    )


def write_project_verification_report(root: Path, goal: str, status: str, events: list[ProjectIterationEvent | dict[str, Any]], final_data: dict[str, Any] | None = None) -> Path:
    """Write a human-readable verification and repair-loop report for a generated project."""
    root = Path(root)
    path = root / "PROJECT_VERIFICATION_REPORT.md"
    rows: list[str] = []
    for raw in events:
        event = raw.to_dict() if isinstance(raw, ProjectIterationEvent) else dict(raw)
        problems = event.get("problems") or []
        rows.extend([
            f"### Round {event.get('round_no', '?')} - {event.get('stage', 'unknown')}",
            f"- Status: {'PASS' if event.get('ok') else 'FAIL'}",
            f"- Summary: {event.get('summary', '')}",
            f"- Quality: {event.get('quality_percent', 'n/a')}",
            f"- Repair source: {event.get('repair_source') or 'n/a'}",
            f"- Changed files: {', '.join(event.get('changed_files') or []) or 'none'}",
            "- Problems: " + ("; ".join(str(p) for p in problems[:8]) if problems else "none"),
            "",
        ])
    final_data = final_data or {}
    content = "\n".join([
        "# Project Verification and Iteration Report",
        "",
        f"Original request: {goal}",
        f"Final status: {status}",
        "",
        "## What this report means",
        "Nova generated or updated the project, ran static/behavioural acceptance checks, and recorded repair attempts instead of claiming success from file creation alone.",
        "",
        "## Iteration timeline",
        "",
        *rows,
        "## Final verification data",
        "",
        "```json",
        json.dumps(_safe_json(final_data), indent=2, ensure_ascii=False, default=str)[:16000],
        "```",
        "",
        "## Manual follow-up",
        "Open the main file, follow the project instructions, and confirm the app/game behaves like the original request. If anything is missing, repair only the listed behaviours and rerun verification.",
        "",
    ])
    atomic_write_text(path, content)
    return path


def proposed_files_digest(files: dict[str, Any] | None) -> str:
    """Stable digest for a proposed repair file set, used to detect looped repairs."""
    if not isinstance(files, dict) or not files:
        return ""
    payload = json.dumps({str(k): str(v) for k, v in sorted(files.items())}, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8", errors="replace")).hexdigest()[:16]


def is_repeated_repair(proposed_files: dict[str, Any] | None, seen_digests: set[str]) -> bool:
    digest = proposed_files_digest(proposed_files)
    if not digest:
        return False
    if digest in seen_digests:
        return True
    seen_digests.add(digest)
    return False


def _extract_problem_summaries(data: dict[str, Any]) -> list[str]:
    problems: list[str] = []
    if not isinstance(data, dict):
        return problems
    for item in data.get("problems") or []:
        if isinstance(item, dict):
            problems.append(str(item.get("message") or item.get("detail") or item.get("kind") or item))
        else:
            problems.append(str(item))
    for check in data.get("checks") or []:
        if isinstance(check, dict) and not check.get("ok", True):
            name = str(check.get("name") or "check")
            detail = check.get("problems") or check.get("output") or check.get("summary") or check.get("detail") or "failed"
            problems.append(f"{name}: {str(detail)[:500]}")
    if not problems and isinstance(data.get("runtime_probe"), dict):
        for suggestion in data["runtime_probe"].get("repair_suggestions") or []:
            problems.append(str(suggestion))
    return problems[:20]


def _extract_quality_percent(data: dict[str, Any]) -> float | None:
    if not isinstance(data, dict):
        return None
    score = data.get("quality_score") or {}
    if isinstance(score, dict) and score.get("overall_percent") is not None:
        try:
            return float(score.get("overall_percent"))
        except Exception:
            return None
    probe = data.get("runtime_probe") or {}
    if isinstance(probe, dict) and probe.get("percent") is not None:
        try:
            return float(probe.get("percent"))
        except Exception:
            return None
    return None


def _safe_json(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _safe_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_safe_json(v) for v in value[:200]]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value if not isinstance(value, str) or len(value) <= 2000 else value[:2000] + "...[truncated]"
    return str(value)


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
