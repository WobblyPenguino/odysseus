from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text, read_json_file

AUTONOMOUS_JOURNAL_DIR = APP_DIR / "autonomous_sequence_journals"


@dataclass
class AutonomousStepJournalEvent:
    """A durable record of one autonomous sequence decision or tool outcome."""

    run_id: str
    cycle: int
    step_index: int
    title: str
    tool: str
    status: str
    reason: str = ""
    watcher_status: str = ""
    failure_category: str = ""
    summary: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_seconds: float | None = None
    args_summary: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AutonomousRunJournal:
    """Run-level summary of what autonomous mode planned, ran, skipped and verified."""

    run_id: str
    cycle: int
    goal: str
    status: str
    started_at: str
    finished_at: str
    total_steps: int
    executed_steps: int
    skipped_steps: int
    failed_steps: int
    blocked_steps: int
    events: list[AutonomousStepJournalEvent] = field(default_factory=list)
    next_recommended_action: str = "review_autonomous_report"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["events"] = [ev.to_dict() for ev in self.events]
        return data


def now_text() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


SENSITIVE_KEY_RE = re.compile(r"(api[_-]?key|token|secret|password|authorization|bearer|credential)", re.I)
SENSITIVE_TEXT_PATTERNS = [
    re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.I),
    re.compile(r"(api[_-]?key|token|secret|password)=([^\s&]+)", re.I),
]


def redact_journal_value(value: Any) -> Any:
    """Return a JSON-safe value with secrets redacted for autonomous journals."""
    if isinstance(value, dict):
        cleaned: dict[str, Any] = {}
        for key, val in value.items():
            key_text = str(key)
            if SENSITIVE_KEY_RE.search(key_text):
                cleaned[key_text] = "[REDACTED]"
            else:
                cleaned[key_text] = redact_journal_value(val)
        return cleaned
    if isinstance(value, list):
        return [redact_journal_value(v) for v in value]
    if isinstance(value, tuple):
        return [redact_journal_value(v) for v in value]
    if isinstance(value, str):
        text = value
        for pattern in SENSITIVE_TEXT_PATTERNS:
            text = pattern.sub(lambda m: f"{m.group(1)}=[REDACTED]" if len(m.groups()) >= 2 else "Bearer [REDACTED]", text)
        return text
    return value


def summarize_args(args: dict[str, Any] | None, limit: int = 320) -> str:
    if not args:
        return ""
    safe_args = redact_journal_value(args)
    try:
        text = json.dumps(safe_args, ensure_ascii=False, default=str, sort_keys=True)
    except Exception:
        text = str(safe_args)
    # Keep journals useful but avoid huge prompts/file contents.
    return text[:limit] + ("..." if len(text) > limit else "")


def make_step_event(
    *,
    run_id: str,
    cycle: int,
    step_index: int,
    title: str,
    tool: str,
    status: str,
    reason: str = "",
    watcher_status: str = "",
    failure_category: str = "",
    summary: str = "",
    started_at: str | None = None,
    finished_at: str | None = None,
    duration_seconds: float | None = None,
    args: dict[str, Any] | None = None,
) -> AutonomousStepJournalEvent:
    return AutonomousStepJournalEvent(
        run_id=run_id,
        cycle=cycle,
        step_index=step_index,
        title=title,
        tool=tool,
        status=status,
        reason=reason,
        watcher_status=watcher_status,
        failure_category=failure_category,
        summary=str(summary or "")[:1000],
        started_at=started_at or now_text(),
        finished_at=finished_at or now_text(),
        duration_seconds=duration_seconds,
        args_summary=summarize_args(args),
    )


def build_run_journal(run_id: str, cycle: int, goal: str, events: list[AutonomousStepJournalEvent]) -> AutonomousRunJournal:
    executed = sum(1 for ev in events if ev.status in {"ok", "failed"})
    skipped = sum(1 for ev in events if ev.status.startswith("skipped"))
    failed = sum(1 for ev in events if ev.status == "failed")
    blocked = sum(1 for ev in events if ev.status in {"blocked", "review-required"})
    if failed:
        status = "failed_with_report"
        next_action = "inspect_failure_memory_or_repair_proposal"
    elif blocked:
        status = "needs_user_review"
        next_action = "review_blocked_or_approval_required_steps"
    elif skipped:
        status = "completed_with_skips"
        next_action = "review_skipped_steps"
    else:
        status = "completed"
        next_action = "continue_or_run_quality_dashboard"
    return AutonomousRunJournal(
        run_id=run_id,
        cycle=cycle,
        goal=goal,
        status=status,
        started_at=events[0].started_at if events else now_text(),
        finished_at=now_text(),
        total_steps=len(events),
        executed_steps=executed,
        skipped_steps=skipped,
        failed_steps=failed,
        blocked_steps=blocked,
        events=events,
        next_recommended_action=next_action,
    )


def render_run_journal_markdown(journal: AutonomousRunJournal) -> str:
    lines = [
        "# Autonomous Sequence Journal",
        "",
        f"Run ID: `{journal.run_id}`",
        f"Cycle: {journal.cycle}",
        f"Goal: {journal.goal}",
        f"Status: **{journal.status}**",
        f"Started: {journal.started_at}",
        f"Finished: {journal.finished_at}",
        "",
        "## Summary",
        f"- Total steps: {journal.total_steps}",
        f"- Executed: {journal.executed_steps}",
        f"- Skipped: {journal.skipped_steps}",
        f"- Failed: {journal.failed_steps}",
        f"- Blocked/review-required: {journal.blocked_steps}",
        f"- Next recommended action: `{journal.next_recommended_action}`",
        "",
        "## Step Trace",
    ]
    if not journal.events:
        lines.append("No autonomous sequence events were recorded.")
    for ev in journal.events:
        lines.append(f"{ev.step_index}. **{ev.title}** → `{ev.tool}` — **{ev.status}**")
        if ev.reason:
            lines.append(f"   - reason: {ev.reason}")
        if ev.watcher_status:
            lines.append(f"   - watcher: {ev.watcher_status}")
        if ev.failure_category:
            lines.append(f"   - failure category: {ev.failure_category}")
        if ev.summary:
            lines.append(f"   - summary: {ev.summary}")
        if ev.args_summary:
            lines.append(f"   - args: `{ev.args_summary}`")
    return "\n".join(lines)


def write_run_journal(journal: AutonomousRunJournal, directory: Path = AUTONOMOUS_JOURNAL_DIR) -> tuple[Path, Path]:
    directory.mkdir(parents=True, exist_ok=True)
    safe_run = "".join(ch if ch.isalnum() or ch in "-_" else "_" for ch in journal.run_id or str(int(time.time())))
    md_path = directory / f"autonomous_sequence_journal_{safe_run}.md"
    json_path = directory / f"autonomous_sequence_journal_{safe_run}.json"
    atomic_write_text(md_path, render_run_journal_markdown(journal))
    atomic_write_json(json_path, journal.to_dict(), ensure_ascii=False)
    return md_path, json_path


def latest_run_journal(directory: Path = AUTONOMOUS_JOURNAL_DIR) -> tuple[Path | None, dict[str, Any] | None]:
    """Return the newest readable journal, skipping corrupt newest files."""
    try:
        files = sorted(directory.glob("autonomous_sequence_journal_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        return None, None
    for path in files:
        data = read_json_file(path, None, expected_type=dict, quarantine=True)
        if isinstance(data, dict):
            return path, data
    return None, None
