from __future__ import annotations

import hashlib
import json
import re
import time
import shutil
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text, read_json_file


AUTONOMOUS_FAILURE_MEMORY_PATH = APP_DIR / "AUTONOMOUS_FAILURE_MEMORY.json"
AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION = 2
REPAIR_TRIGGER_CATEGORIES = {
    "timeout",
    "command_error",
    "verification_failed",
    "no_useful_edits",
    "repeated_failed_action",
}

REPAIR_REPORT_HEADINGS = [
    "# Autonomous Repair Proposal",
    "## Failure Summary",
    "## Failure Category",
    "## Repeated Failure Check",
    "## Local Model Surgical Diagnosis",
    "## Proposed Smallest Fix",
    "## Unsafe Suggestions Rejected",
    "## Verification Plan",
    "## Next Recommended Command",
    "## Do Not Repeat Until",
]


@dataclass
class AutonomousFailureRecord:
    cycle_id: str
    action_name: str
    tool_name: str
    command_summary: str | None
    target: str | None
    success: bool
    failure_category: str
    error_summary: str
    duration_seconds: float | None
    timestamp: str
    signature: str
    recommended_next_action: str


@dataclass
class AutonomousFailureMemory:
    recent_failures: list[AutonomousFailureRecord] = field(default_factory=list)
    failure_counts: dict[str, int] = field(default_factory=dict)
    cooldowns: dict[str, int] = field(default_factory=dict)
    last_failure_summary: str | None = None
    last_suggested_fix: str | None = None
    schema_version: int = AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION
    saved_at: str | None = None


def classify_autonomous_failure(
    result_text: str = "",
    error_text: str = "",
    timed_out: bool = False,
    no_useful_edits: bool = False,
) -> str:
    text = f"{result_text}\n{error_text}".lower()
    if timed_out or "timed out" in text or "timeout" in text:
        return "timeout"
    if any(term in text for term in ["bad input", "invalid input", "invalid goal", "unknown command", "usage:"]):
        return "invalid_input"
    if any(term in text for term in ["tool crashed", "tool crash", "attributeerror", "typeerror", "keyerror"]):
        return "tool_crash"
    if any(term in text for term in ["repeated failed action", "repeat failed action", "same signature failed", "on cooldown", "cooldown_skip"]):
        return "repeated_failed_action"
    if any(term in text for term in ["access denied", "permission", "blocked"]):
        return "permission_blocked"
    if any(term in text for term in ["not found", "missing file", "cannot find path"]):
        return "missing_file"
    if any(term in text for term in ["model failed", "llm failed", "ollama failed"]):
        return "model_error"
    if any(term in text for term in ["verification failed", "tests failed", "py_compile failed"]):
        return "verification_failed"
    if no_useful_edits:
        return "no_useful_edits"
    if any(term in text for term in ["failed", "non-zero", "exit code", "exception", "traceback"]):
        return "command_error"
    return "unknown"


def make_failure_signature(
    action_name: str,
    tool_name: str,
    command_summary: str | None,
    target: str | None,
    failure_category: str,
) -> str:
    seed_parts = [
        action_name or "",
        tool_name or "",
        command_summary or "",
        target or "",
        failure_category or "",
    ]
    seed = "|".join(_normalise_signature_text(part) for part in seed_parts)
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    readable = "-".join(
        part
        for part in [
            _slug(failure_category, 20),
            _slug(tool_name, 24),
            _slug(action_name, 28),
        ]
        if part
    )
    return f"{readable}-{digest}".strip("-")[:90]


def load_autonomous_failure_memory(path: Path) -> AutonomousFailureMemory:
    try:
        if not path.exists() or not path.is_file():
            return AutonomousFailureMemory()
        data = read_json_file(path, None, expected_type=dict, quarantine=False)
        if not isinstance(data, dict):
            _archive_corrupt_memory(path, "invalid-json")
            return AutonomousFailureMemory()
        rows = []
        for item in data.get("recent_failures") or []:
            if isinstance(item, dict):
                try:
                    rows.append(AutonomousFailureRecord(**_record_dict(item)))
                except Exception:
                    continue
        return AutonomousFailureMemory(
            recent_failures=rows[-25:],
            failure_counts=_int_dict(data.get("failure_counts")),
            cooldowns=_int_dict(data.get("cooldowns")),
            last_failure_summary=_optional_str(data.get("last_failure_summary")),
            last_suggested_fix=_optional_str(data.get("last_suggested_fix")),
            schema_version=int(data.get("schema_version") or AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION),
            saved_at=_optional_str(data.get("saved_at")),
        )
    except Exception as exc:
        _archive_corrupt_memory(path, type(exc).__name__)
        return AutonomousFailureMemory()


def save_autonomous_failure_memory(path: Path, memory: AutonomousFailureMemory) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    memory = compact_autonomous_failure_memory(memory)
    data = {
        "schema_version": AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION,
        "saved_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "recent_failures": [asdict(record) for record in (memory.recent_failures or [])[-25:]],
        "failure_counts": _int_dict(memory.failure_counts),
        "cooldowns": _int_dict(memory.cooldowns),
        "last_failure_summary": memory.last_failure_summary,
        "last_suggested_fix": memory.last_suggested_fix,
    }
    tmp = path.with_name(path.name + ".tmp")
    atomic_write_json(tmp, data, ensure_ascii=False)
    tmp.replace(path)


def compact_autonomous_failure_memory(memory: AutonomousFailureMemory, max_failures: int = 25, max_cooldowns: int = 100) -> AutonomousFailureMemory:
    recent = list(memory.recent_failures or [])[-max_failures:]
    active_signatures = {record.signature for record in recent}
    counts = {k: v for k, v in _int_dict(memory.failure_counts).items() if k in active_signatures}
    cooldowns = {k: v for k, v in _int_dict(memory.cooldowns).items() if v > 0}
    # Keep deterministic order by most recent signatures and cap size.
    ordered = []
    for record in reversed(recent):
        if record.signature in cooldowns and record.signature not in ordered:
            ordered.append(record.signature)
    cooldowns = {k: cooldowns[k] for k in ordered[:max_cooldowns] if k in cooldowns}
    return AutonomousFailureMemory(
        recent_failures=recent,
        failure_counts=counts,
        cooldowns=cooldowns,
        last_failure_summary=memory.last_failure_summary,
        last_suggested_fix=memory.last_suggested_fix,
        schema_version=AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION,
        saved_at=memory.saved_at,
    )


def _archive_corrupt_memory(path: Path, reason: str) -> None:
    try:
        if not path.exists():
            return
        archive = path.with_suffix(path.suffix + f".corrupt_{time.strftime('%Y%m%d_%H%M%S')}")
        shutil.copy2(path, archive)
    except Exception:
        import logging as _wla_logging
        _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)


def update_autonomous_failure_memory(
    memory: AutonomousFailureMemory,
    record: AutonomousFailureRecord,
) -> AutonomousFailureMemory:
    cooldowns = {
        signature: max(0, int(count) - 1)
        for signature, count in (memory.cooldowns or {}).items()
        if int(count or 0) > 1
    }
    recent = list(memory.recent_failures or [])
    recent.append(record)
    recent = recent[-25:]

    counts = _int_dict(memory.failure_counts)
    counts[record.signature] = counts.get(record.signature, 0) + 1
    recent_same = sum(1 for item in recent[-8:] if item.signature == record.signature)
    if recent_same >= 2:
        cooldowns[record.signature] = max(cooldowns.get(record.signature, 0), 2)
        record.recommended_next_action = "diagnose_recent_failure"

    return AutonomousFailureMemory(
        recent_failures=recent,
        failure_counts=counts,
        cooldowns=cooldowns,
        last_failure_summary=record.error_summary,
        last_suggested_fix=record.recommended_next_action,
        schema_version=AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION,
        saved_at=memory.saved_at,
    )


def clear_autonomous_cooldowns_for_action(
    memory: AutonomousFailureMemory,
    action_name: str,
    tool_name: str,
    command_summary: str | None = None,
    target: str | None = None,
) -> AutonomousFailureMemory:
    """Clear stale cooldowns after the same action/tool target succeeds.

    Failure signatures include the failure category, so a success does not have the
    exact same signature. This helper compares the recorded action/tool/target
    fields instead and removes cooldowns that no longer represent current risk.
    """
    matching = {
        record.signature
        for record in (memory.recent_failures or [])
        if record.action_name == action_name
        and record.tool_name == tool_name
        and (record.command_summary or None) == (command_summary or None)
        and (record.target or None) == (target or None)
    }
    if not matching:
        return memory
    cooldowns = {k: v for k, v in (memory.cooldowns or {}).items() if k not in matching}
    failures = [record for record in (memory.recent_failures or []) if record.signature not in matching]
    counts = {k: v for k, v in (memory.failure_counts or {}).items() if k not in matching}
    return AutonomousFailureMemory(
        recent_failures=failures[-25:],
        failure_counts=counts,
        cooldowns=cooldowns,
        last_failure_summary=memory.last_failure_summary,
        last_suggested_fix="cooldown cleared after verified success" if cooldowns != (memory.cooldowns or {}) else memory.last_suggested_fix,
        schema_version=AUTONOMOUS_FAILURE_MEMORY_SCHEMA_VERSION,
        saved_at=memory.saved_at,
    )


def should_cooldown_autonomous_action(memory: AutonomousFailureMemory, signature: str) -> tuple[bool, str]:
    count = int((memory.cooldowns or {}).get(signature, 0) or 0)
    if count > 0:
        return True, f"Signature {signature} is on cooldown for {count} cycle(s)."
    return False, ""


def build_autonomous_repair_prompt(
    record: AutonomousFailureRecord,
    recent_events: list[dict[str, Any]] | None = None,
    files: list[str] | None = None,
    verification_commands: list[str] | None = None,
    constraints: list[str] | None = None,
) -> str:
    return "\n".join(
        [
            "You are Nova's local model helping diagnose an autonomous-cycle failure.",
            "Propose a surgical repair plan only. Do not apply edits.",
            "",
            "Failure category:",
            record.failure_category,
            "",
            "Failed action/tool:",
            f"- action: {record.action_name}",
            f"- tool: {record.tool_name}",
            f"- command: {record.command_summary or '(none)'}",
            f"- target: {record.target or '(none)'}",
            "",
            "Short failure summary:",
            record.error_summary[:4000],
            "",
            "Recent related events:",
            json.dumps((recent_events or [])[-12:], indent=2, ensure_ascii=False, default=str)[:6000],
            "",
            "Files involved:",
            json.dumps(files or [], ensure_ascii=False),
            "",
            "Current constraints:",
            "\n".join(f"- {item}" for item in (constraints or _default_constraints())),
            "",
            "Verification commands:",
            "\n".join(f"- {cmd}" for cmd in (verification_commands or [])),
            "",
            "Instructions:",
            "- propose the smallest safe fix",
            "- do not rewrite whole files",
            "- do not suggest broad refactors",
            "- do not suggest disabling tests",
            "- do not suggest removing safety checks",
            "- do not suggest install/network/package changes unless directly necessary",
            "- do not output full-file replacement JSON",
            "- include verification commands",
            "- include rollback/fallback plan",
        ]
    )


def write_autonomous_repair_proposal(
    directory: Path,
    record: AutonomousFailureRecord,
    *,
    local_model_diagnosis: str | None = None,
    local_model_error: str | None = None,
    repeated_failure: bool = False,
    recent_events: list[dict[str, Any]] | None = None,
    files: list[str] | None = None,
    verification_commands: list[str] | None = None,
    constraints: list[str] | None = None,
    next_recommended_command: str | None = None,
    do_not_repeat_until: str | None = None,
    timestamp: str | None = None,
) -> dict[str, Any]:
    directory.mkdir(parents=True, exist_ok=True)
    stamp = timestamp or time.strftime("%Y%m%d_%H%M%S")
    base = directory / f"autonomous_repair_proposal_{stamp}"
    md_path = _unique_path(base.with_suffix(".md"))
    json_path = md_path.with_suffix(".json")

    unsafe = detect_unsafe_suggestions(local_model_diagnosis or "")
    diagnosis = (local_model_diagnosis or "").strip()
    if not diagnosis:
        diagnosis = "unavailable"
        if local_model_error:
            diagnosis += f": {local_model_error}"

    verification = verification_commands or []
    constraints = constraints or _default_constraints()
    next_command = next_recommended_command or record.recommended_next_action or "diagnose_recent_failure"
    repeat_until = do_not_repeat_until or (
        "the failure has been diagnosed and a different action/tool/command has been selected"
        if repeated_failure
        else "the next autonomous cycle has completed a diagnostic step"
    )
    smallest_fix = _extract_smallest_fix(diagnosis)

    lines = [
        "# Autonomous Repair Proposal",
        "",
        "## Failure Summary",
        record.error_summary or "(none)",
        "",
        "## Failure Category",
        record.failure_category,
        "",
        "## Repeated Failure Check",
        "Repeated failure detected; diagnose before retrying." if repeated_failure else "No repeated failure threshold detected yet.",
        "",
        "## Local Model Surgical Diagnosis",
        diagnosis,
        "",
        "## Proposed Smallest Fix",
        smallest_fix,
        "",
        "## Unsafe Suggestions Rejected",
        "\n".join(f"- {item}" for item in unsafe) if unsafe else "None detected.",
        "",
        "## Verification Plan",
        "\n".join(f"- {cmd}" for cmd in verification) if verification else "- Run the smallest relevant syntax/check command after a human-reviewed fix.",
        "",
        "## Next Recommended Command",
        next_command,
        "",
        "## Do Not Repeat Until",
        repeat_until,
        "",
        "## Context",
        "",
        "```json",
        json.dumps(
            {
                "record": asdict(record),
                "recent_events": recent_events or [],
                "files": files or [],
                "constraints": constraints,
            },
            indent=2,
            ensure_ascii=False,
            default=str,
        )[:12000],
        "```",
    ]
    atomic_write_text(md_path, "\n".join(lines) + "\n")

    payload = {
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "record": asdict(record),
        "repeated_failure": repeated_failure,
        "local_model_diagnosis": diagnosis,
        "local_model_unavailable": bool(local_model_error) and not bool(local_model_diagnosis),
        "local_model_error": local_model_error or "",
        "unsafe_suggestions_rejected": unsafe,
        "verification_commands": verification,
        "next_recommended_command": next_command,
        "do_not_repeat_until": repeat_until,
    }
    atomic_write_json(json_path, payload, ensure_ascii=False)
    return payload


def detect_unsafe_repair_suggestions(text: str) -> list[str]:
    low = (text or "").lower()
    checks = [
        ("broad rewrite", ["broad rewrite", "rewrite the whole", "rewrite all", "full rewrite"]),
        ("delete safety checks", ["delete safety", "remove safety", "delete guardrail", "remove guardrail"]),
        ("disable tests", ["disable tests", "skip tests", "turn off tests", "remove tests"]),
        ("bypass permissions", ["bypass permission", "bypass permissions", "disable permissions"]),
        ("install packages without explicit user approval", ["pip install", "install package", "install packages"]),
        ("network access without explicit user approval", ["enable internet", "network access", "fetch from internet"]),
        ("call /self-improve automatically", ["call /self-improve", "run /self-improve", "self-improve automatically"]),
        ("apply source edits automatically", ["apply source edits automatically", "auto-apply", "automatically edit source"]),
        ("remove backup/rollback", ["remove backup", "remove rollback", "delete rollback", "without rollback"]),
    ]
    rejected = []
    for label, needles in checks:
        if any(needle in low for needle in needles):
            rejected.append(label)
    return rejected


def _record_dict(item: dict[str, Any]) -> dict[str, Any]:
    return {
        "cycle_id": str(item.get("cycle_id") or ""),
        "action_name": str(item.get("action_name") or ""),
        "tool_name": str(item.get("tool_name") or ""),
        "command_summary": _optional_str(item.get("command_summary")),
        "target": _optional_str(item.get("target")),
        "success": bool(item.get("success")),
        "failure_category": str(item.get("failure_category") or "unknown"),
        "error_summary": str(item.get("error_summary") or ""),
        "duration_seconds": _optional_float(item.get("duration_seconds")),
        "timestamp": str(item.get("timestamp") or ""),
        "signature": str(item.get("signature") or ""),
        "recommended_next_action": str(item.get("recommended_next_action") or "diagnose_recent_failure"),
    }


def _int_dict(value: Any) -> dict[str, int]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, int] = {}
    for key, val in value.items():
        try:
            intval = int(val)
        except Exception:
            continue
        if intval > 0:
            out[str(key)] = intval
    return out


def _optional_str(value: Any) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


def _optional_float(value: Any) -> float | None:
    try:
        return float(value)
    except Exception:
        return None


def _normalise_signature_text(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").strip().lower())[:240]


def _slug(text: str, limit: int = 32) -> str:
    text = re.sub(r"[^a-z0-9]+", "-", (text or "").lower()).strip("-")
    return text[:limit].strip("-")


def _unique_path(path: Path) -> Path:
    if not path.exists():
        return path
    stem = path.with_suffix("")
    suffix = path.suffix
    for i in range(2, 100):
        candidate = Path(f"{stem}_{i}{suffix}")
        if not candidate.exists():
            return candidate
    return path


def _extract_smallest_fix(diagnosis: str) -> str:
    if not diagnosis or diagnosis == "unavailable":
        return "Manual diagnosis required before any source edit. Start by inspecting the failed command/tool output and choose a different diagnostic action."
    lines = [line.strip("- ").strip() for line in diagnosis.splitlines() if line.strip()]
    for line in lines:
        low = line.lower()
        if "fix" in low or "change" in low or "repair" in low:
            return line[:1200]
    return lines[0][:1200] if lines else "Review the diagnosis and make the smallest targeted change only after human approval."


def _default_constraints() -> list[str]:
    return [
        "Do not apply the repair automatically.",
        "Do not call /self-improve automatically.",
        "Do not weaken self-improve guardrails.",
        "Do not broaden autonomous permissions.",
        "Do not add package/install/network changes without explicit user approval.",
        "Keep changes small, testable, and reversible.",
    ]


# Backward-compatible alias used by earlier v51 tests and reports.
def detect_unsafe_suggestions(text: str) -> list[str]:
    return detect_unsafe_repair_suggestions(text)
