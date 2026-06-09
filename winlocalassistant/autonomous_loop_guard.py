from __future__ import annotations

import json
import re
from typing import Any

MUTATING_TOOLS = {
    "ai_create_project",
    "ai_edit_project",
    "improve_project",
    "surgical_repair",
    "backtrack_recover",
    "tool_create",
    "tool_delete",
    "write_file",
    "write_files",
    "append_file",
    "find_replace",
    "make_dir",
    "project_create",
    "project_delete",
    "project_remove",
    "install_package",
    "self_improve",
    "zip_path",
}

DIAGNOSTIC_TOOLS = {
    "heartbeat",
    "runtime_self_check",
    "idle_lessons",
    "investigate_logs",
    "code_repair_audit",
    "code_review_audit",
    "code_quality_gate",
    "tool_use_guide",
    "tool_clean_proposals",
    "propose_improvements",
    "detect_project",
    "list_files",
}

VERIFICATION_TOOLS = {
    "auto_verify",
    "final_project_check",
    "run_project",
}

FINITE_GOAL_TERMS = (
    "build", "create", "make", "generate", "write", "add", "implement", "fix", "repair", "debug", "update", "improve",
)
CONTINUOUS_GOAL_TERMS = (
    "forever", "continuously", "continuous", "keep running", "keep improving", "monitor", "watch", "every cycle", "background",
)


def canonical_json(value: Any) -> str:
    try:
        return json.dumps(value, ensure_ascii=False, sort_keys=True, default=str)
    except Exception:
        return repr(value)


def action_signature(title: str, tool: str, kwargs: dict[str, Any] | None = None) -> str:
    """Return a stable signature for loop detection.

    Volatile fields are removed so the same action is recognised across cycles.
    """
    clean: dict[str, Any] = {}
    for key, value in (kwargs or {}).items():
        if key.lower() in {"run_id", "timestamp", "started_at", "cycle"}:
            continue
        clean[key] = value
    return f"{tool}|{title}|{canonical_json(clean)}"[:500]


def result_progress_score(tool: str, ok: bool, summary: str = "", data: dict[str, Any] | None = None) -> int:
    """Score whether a tool result appears to have moved the user's task forward.

    This is deliberately conservative: diagnostic tools can be useful, but they
    do not count as completing an autonomous user request by themselves.
    """
    if not ok:
        return 0
    data = data or {}
    summary_l = (summary or "").lower()
    score = 0
    if tool in MUTATING_TOOLS:
        score += 2
    if tool in VERIFICATION_TOOLS and any(term in summary_l for term in ["pass", "passed", "ok", "verified", "success", "started", "available"]):
        score += 1
    written = data.get("written") or data.get("files_written") or data.get("created") or data.get("modified")
    if written:
        score += 3
    if data.get("path") and tool in MUTATING_TOOLS | {"zip_path"}:
        score += 1
    if any(term in summary_l for term in ["created", "wrote", "written", "updated", "fixed", "repaired", "generated", "packaged", "saved"]):
        score += 1
    return score


def finite_goal_should_stop(goal: str, *, had_progress: bool, had_successful_verification: bool, diagnostic_only: bool = False, continuous_mode: bool = False) -> bool:
    """Return True when a finite autonomous mission should stop after success.

    Without this, `/autonomous start build X` can keep rebuilding/checking the
    same target forever even after it has already done the requested work.
    """
    if continuous_mode:
        return False
    if diagnostic_only or not had_progress:
        return False
    low = (goal or "").lower()
    if any(term in low for term in CONTINUOUS_GOAL_TERMS):
        return False
    if any(term in low for term in FINITE_GOAL_TERMS):
        return True if had_successful_verification else had_progress
    return False


def should_skip_repeated_action(state: dict[str, Any], title: str, tool: str, kwargs: dict[str, Any] | None = None, *, required: bool = False) -> tuple[bool, str]:
    """Decide whether a planned action should be skipped to break a loop."""
    sig = action_signature(title, tool, kwargs or {})
    recent = list(state.get("recent_action_signatures") or [])[-30:]
    no_progress_cycles = int(state.get("no_progress_cycles") or 0)
    repeats = recent.count(sig)

    if tool in DIAGNOSTIC_TOOLS and repeats >= 2 and not required:
        return True, "loop guard skipped repeated optional diagnostic step already run in recent cycles"
    if tool in MUTATING_TOOLS and repeats >= 2 and no_progress_cycles >= 1:
        return True, "loop guard blocked repeating the same mutating action after a no-progress cycle; choose a different strategy or inspect the failure first"
    return False, ""


def summarize_cycle_outcome(
    *,
    goal: str,
    base_results: list[tuple[str, str, Any]] | None = None,
    sequence_results: list[Any] | None = None,
    diagnostic_only: bool = False,
    continuous_mode: bool = False,
) -> dict[str, Any]:
    """Summarise one autonomous cycle for progress/repetition memory."""
    entries: list[dict[str, Any]] = []
    for title, tool, result in base_results or []:
        data = getattr(result, "data", {}) if result is not None else {}
        entries.append({
            "title": title,
            "tool": tool,
            "ok": bool(getattr(result, "ok", False)),
            "summary": str(getattr(result, "summary", ""))[:500],
            "data": data if isinstance(data, dict) else {},
            "signature": action_signature(title, tool, {}),
        })
    for result in sequence_results or []:
        data = getattr(result, "data", {}) if result is not None else {}
        tool = str(data.get("tool") or data.get("tool_name") or "sequenced_tool") if isinstance(data, dict) else "sequenced_tool"
        title = str(data.get("title") or data.get("action") or tool) if isinstance(data, dict) else tool
        entries.append({
            "title": title,
            "tool": tool,
            "ok": bool(getattr(result, "ok", False)),
            "summary": str(getattr(result, "summary", ""))[:500],
            "data": data if isinstance(data, dict) else {},
            "signature": action_signature(title, tool, data if isinstance(data, dict) else {}),
        })

    progress_score = 0
    verification_ok = False
    mutation_attempted = False
    failure_count = 0
    for entry in entries:
        tool = entry["tool"]
        if tool in MUTATING_TOOLS:
            mutation_attempted = True
        if not entry["ok"]:
            failure_count += 1
        progress_score += result_progress_score(tool, entry["ok"], entry["summary"], entry["data"])
        if tool in VERIFICATION_TOOLS and entry["ok"]:
            verification_ok = True

    # If a sequenced mutating tool result did not carry a tool name in data, fall
    # back to summary cues so older tools still register progress.
    joined_summary = "\n".join(entry["summary"] for entry in entries).lower()
    if any(term in joined_summary for term in ["created", "wrote", "updated", "fixed", "repaired", "generated", "packaged"]):
        progress_score += 1

    had_progress = progress_score > 0
    fingerprint_parts = []
    for entry in entries:
        summary_key = re.sub(r"\s+", " ", entry["summary"].strip().lower())[:120]
        fingerprint_parts.append(f"{entry['tool']}:{'ok' if entry['ok'] else 'fail'}:{summary_key}")
    fingerprint = "|".join(fingerprint_parts)[-4000:]
    return {
        "goal": goal,
        "diagnostic_only": diagnostic_only,
        "entries": entries[-50:],
        "action_signatures": [entry["signature"] for entry in entries][-80:],
        "fingerprint": fingerprint,
        "progress_score": progress_score,
        "had_progress": had_progress,
        "mutation_attempted": mutation_attempted,
        "verification_ok": verification_ok,
        "failure_count": failure_count,
        "finite_goal_complete": finite_goal_should_stop(goal, had_progress=had_progress, had_successful_verification=verification_ok, diagnostic_only=diagnostic_only, continuous_mode=continuous_mode),
        "continuous_mode": bool(continuous_mode),
        "finite_goal_milestone": finite_goal_should_stop(goal, had_progress=had_progress, had_successful_verification=verification_ok, diagnostic_only=diagnostic_only, continuous_mode=False),
    }


def update_loop_guard_state(state: dict[str, Any], outcome: dict[str, Any], *, continuous_mode: bool = False) -> tuple[dict[str, Any], list[str]]:
    """Return state updates and human-readable notes for loop prevention."""
    history = list(state.get("loop_guard_history") or [])
    recent_fingerprints = list(state.get("recent_cycle_fingerprints") or [])
    recent_actions = list(state.get("recent_action_signatures") or [])

    fingerprint = str(outcome.get("fingerprint") or "")
    repeated_fingerprint_count = recent_fingerprints[-4:].count(fingerprint) if fingerprint else 0
    had_progress = bool(outcome.get("had_progress"))
    no_progress_cycles = 0 if had_progress else int(state.get("no_progress_cycles") or 0) + 1

    notes: list[str] = []
    loop_breaker_active = False
    stop_recommended = False
    next_strategy_hint = ""

    if repeated_fingerprint_count >= 1 and not had_progress:
        loop_breaker_active = True
        notes.append("Loop guard: this cycle looked the same as a recent no-progress cycle, so the next cycle should avoid repeating the same diagnostics/actions.")
        next_strategy_hint = "avoid_repeated_diagnostics_and_choose_new_strategy"
    if no_progress_cycles >= 2:
        loop_breaker_active = True
        if continuous_mode:
            notes.append("Loop guard: two autonomous cycles made no measurable progress; continuous mode will switch strategy instead of stopping.")
            stop_recommended = False
            next_strategy_hint = "switch_strategy_after_no_progress"
        else:
            notes.append("Loop guard: two autonomous cycles made no measurable progress; continuous mode should stop or switch to a new strategy instead of looping.")
            stop_recommended = True
            next_strategy_hint = "stop_and_report_no_progress"
    if outcome.get("finite_goal_milestone") and continuous_mode:
        notes.append("Loop guard: finite milestone appears completed; continuous mission mode will choose the next safe verified improvement instead of stopping.")
        stop_recommended = False
        next_strategy_hint = "choose_next_safe_improvement"
    elif outcome.get("finite_goal_complete"):
        notes.append("Loop guard: finite user goal appears completed, so finite autonomous mode should stop instead of repeating the same completed work.")
        stop_recommended = True
        next_strategy_hint = "goal_complete_stop"

    history.append({
        "goal": outcome.get("goal", ""),
        "fingerprint": fingerprint,
        "progress_score": outcome.get("progress_score", 0),
        "had_progress": had_progress,
        "mutation_attempted": outcome.get("mutation_attempted", False),
        "verification_ok": outcome.get("verification_ok", False),
        "failure_count": outcome.get("failure_count", 0),
        "finite_goal_complete": outcome.get("finite_goal_complete", False),
    })

    recent_actions.extend(list(outcome.get("action_signatures") or []))
    if fingerprint:
        recent_fingerprints.append(fingerprint)

    updates = {
        "loop_guard_history": history[-20:],
        "recent_action_signatures": recent_actions[-120:],
        "recent_cycle_fingerprints": recent_fingerprints[-12:],
        "no_progress_cycles": no_progress_cycles,
        "loop_breaker_active": loop_breaker_active,
        "loop_guard_stop_recommended": stop_recommended,
        "next_strategy_hint": next_strategy_hint,
        "last_progress_score": outcome.get("progress_score", 0),
        "last_cycle_had_progress": had_progress,
        "last_cycle_finite_goal_complete": bool(outcome.get("finite_goal_complete")),
        "last_cycle_finite_goal_milestone": bool(outcome.get("finite_goal_milestone")),
        "continuous_mode": bool(continuous_mode),
    }
    return updates, notes
