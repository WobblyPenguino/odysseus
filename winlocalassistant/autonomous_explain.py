from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class AutonomousExplanation:
    summary: str
    phase: str
    current_action: str
    why: str
    next_expected_step: str
    risk: str
    verification: list[str]
    failure_memory: str
    repair_proposal: str
    recent_events: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def explain_autonomous_state(state: dict[str, Any]) -> AutonomousExplanation:
    """Turn raw autonomous state into a user-readable explanation.

    This is deliberately deterministic and read-only. It does not execute tools or
    alter autonomous state; it only explains what the existing state means.
    """
    phase = str(state.get("phase") or "idle")
    action = str(state.get("current_action") or state.get("last_message") or "Waiting for work")
    detail = str(state.get("current_detail") or state.get("last_summary") or "")
    tool = str(state.get("current_tool") or state.get("last_tool") or "")
    failure_category = str(state.get("last_failure_category") or "")
    repair_path = str(state.get("last_repair_proposal_path") or "")
    running = bool(state.get("running"))
    enabled = bool(state.get("enabled"))

    why = _why_for_phase(phase, action, tool, detail)
    next_step = _next_step_for_phase(phase, running, enabled, failure_category, repair_path)
    risk = _risk_for_state(state, failure_category)
    verification = _verification_for_state(state, phase, tool)
    failure_memory = _failure_memory_summary(state, failure_category)
    repair = repair_path or "No repair proposal has been written for the current cycle."
    recent_events = []
    for ev in list(state.get("events") or [])[-6:]:
        if isinstance(ev, dict):
            recent_events.append(f"{ev.get('time','')} {ev.get('kind','')}: {ev.get('message','')}")
    summary = _summary(running, enabled, phase, action)
    return AutonomousExplanation(summary, phase, action, why, next_step, risk, verification, failure_memory, repair, recent_events)


def render_autonomous_explanation_markdown(explanation: AutonomousExplanation) -> str:
    lines = [
        "# Autonomous Explanation",
        "",
        "## What autonomous is doing now",
        f"Summary: {explanation.summary}",
        f"Phase: {explanation.phase}",
        f"Current action: {explanation.current_action}",
        "",
        "## Why this is happening",
        explanation.why,
        "",
        "## Next expected step",
        explanation.next_expected_step,
        "",
        "## Risk / safety state",
        explanation.risk,
        "",
        "## Verification expected",
    ]
    lines += [f"- {v}" for v in explanation.verification] or ["- No verification selected yet."]
    lines += ["", "## Failure memory", explanation.failure_memory, "", "## Repair proposal", explanation.repair_proposal]
    lines += ["", "## Recent autonomous events"]
    lines += [f"- {ev}" for ev in explanation.recent_events] or ["- No recent autonomous events."]
    return "\n".join(lines)


def _summary(running: bool, enabled: bool, phase: str, action: str) -> str:
    if running:
        return f"Autonomous mode is actively working in phase '{phase}'."
    if enabled:
        return "Autonomous mode is enabled but between safe steps."
    if action and action != "Waiting for work":
        return "Autonomous mode is stopped; showing the last known action."
    return "Autonomous mode is idle."


def _why_for_phase(phase: str, action: str, tool: str, detail: str) -> str:
    text = " ".join([phase, action, tool, detail]).lower()
    if "diagnose" in text or "failure" in text or "failed" in text:
        return "Nova is diagnosing a previous failure instead of repeating the same action blindly."
    if "repair" in text:
        return "Nova is preparing or recording a repair proposal so the smallest safe fix can be reviewed."
    if "verify" in text or "test" in text:
        return "Nova is checking whether the previous action actually worked before claiming success."
    if "plan" in text or "proposal" in text:
        return "Nova is planning before acting so the next step has clear scope and verification."
    if tool:
        return f"Nova selected tool '{tool}' because the current cycle requires a bounded tool step."
    return "Nova is waiting or has not yet selected a tool for this cycle."


def _next_step_for_phase(phase: str, running: bool, enabled: bool, failure_category: str, repair_path: str) -> str:
    if failure_category and repair_path:
        return "Review the repair proposal, then run a targeted verification or manual repair command."
    if failure_category:
        return "Classify the failure, record memory/cooldown, and write a repair proposal if safe."
    if running:
        return "Finish the current tool step, verify the result, then either repair, report, or continue."
    if enabled:
        return "Wait for the next bounded autonomous cycle or stop autonomous mode."
    return "Use /autonomous once GOAL for one safe cycle, or /planning-dashboard GOAL before running."


def _risk_for_state(state: dict[str, Any], failure_category: str) -> str:
    if failure_category:
        return f"Attention needed: last failure category is {failure_category}. Repetition should be cooled down."
    tool = str(state.get("current_tool") or state.get("last_tool") or "")
    if tool in {"self_improve", "run_shell", "install_package"}:
        return "High risk tool observed; watcher/approval/verification rules should apply."
    if tool in {"improve_project", "surgical_repair", "ai_create_project"}:
        return "Medium risk project-changing action; verify output and preserve rollback/fallback information."
    return "Low/unknown current risk based on visible autonomous state."


def _verification_for_state(state: dict[str, Any], phase: str, tool: str) -> list[str]:
    if tool == "ai_create_project":
        return ["syntax/static checks", "project acceptance contract", "runtime interaction probe", "request-match check"]
    if tool in {"improve_project", "surgical_repair"}:
        return ["project-specific verification", "quality score", "iteration log", "changed-file review"]
    if "failure" in phase or "repair" in phase:
        return ["repair proposal exists", "unsafe suggestions rejected", "next command is manual/reviewable"]
    return ["py_compile if Nova code changed", "python tests_smoke.py", "relevant pytest suites"]


def _failure_memory_summary(state: dict[str, Any], failure_category: str) -> str:
    sig = str(state.get("last_failure_signature") or "")
    fix = str(state.get("last_suggested_fix") or "")
    summary = str(state.get("last_failure_summary") or "")
    if not (failure_category or sig or summary):
        return "No recent autonomous failure is recorded in the visible state."
    return f"Category: {failure_category or 'unknown'}; signature: {sig or 'none'}; recommended next action: {fix or 'inspect_recent_events'}; summary: {summary[:500]}"
