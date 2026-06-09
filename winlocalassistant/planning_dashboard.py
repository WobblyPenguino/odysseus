from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from .action_watcher import evaluate_action_risk
from .command_suggestions import suggest_next_commands
try:
    from .task_decomposition import decompose_user_request
except Exception:  # pragma: no cover
    decompose_user_request = None
try:
    from .intent_planning import analyze_planning_dialog_need
except Exception:  # pragma: no cover
    analyze_planning_dialog_need = None


@dataclass
class PlanningDashboard:
    user_text: str
    intent: str
    confidence: float
    plan_level: str
    subtasks: list[str]
    suggested_commands: list[dict[str, Any]]
    watcher: dict[str, Any]
    needs_user_choice: bool
    verification: list[str]
    why: str
    recommended_next_action: str
    tool_sequence: list[str]
    risk_notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_planning_dashboard(user_text: str, context: dict | None = None) -> PlanningDashboard:
    text = user_text or ""
    low = text.lower()
    task_plan = decompose_user_request(text) if decompose_user_request is not None else None
    intent = _intent_from_task_plan(task_plan, low)
    confidence = float(getattr(task_plan, "intent_confidence", _confidence(low)))
    if task_plan is not None and getattr(task_plan, "normalized_text", text) != text:
        confidence = max(0.05, round(confidence - 0.08, 2))
    subtasks = _subtasks_from_task_plan(task_plan, text)
    plan_level = _plan_level_from_task_plan(task_plan, intent, subtasks, low)
    suggestions = [s.to_dict() for s in suggest_next_commands(text, context=context or {})]
    watcher = evaluate_action_risk({"name": intent, "command": text, "category": intent}).to_dict()
    needs_choice = bool(getattr(task_plan, "needs_clarification", False)) or confidence < 0.75 or len(subtasks) > 1 or watcher.get("requires_approval", False)
    verification = _verification_from_task_plan(task_plan, intent)
    why = _why_dashboard(intent, confidence, subtasks, watcher, needs_choice)
    recommended = _recommended_next_action(intent, confidence, needs_choice, watcher)
    tools = _tool_sequence(intent, subtasks, needs_choice)
    risks = _risk_notes(watcher, confidence, needs_choice)
    return PlanningDashboard(text, intent, confidence, plan_level, subtasks, suggestions, watcher, needs_choice, verification, why, recommended, tools, risks)


def render_planning_dashboard_markdown(dashboard: PlanningDashboard) -> str:
    lines = [
        "# Nova Planning Dashboard",
        "",
        f"Intent: {dashboard.intent}",
        f"Confidence: {dashboard.confidence:.2f}",
        f"Plan level: {dashboard.plan_level}",
        f"Needs user choice: {dashboard.needs_user_choice}",
        "",
        "## Why this plan",
        dashboard.why,
        "",
        "## Recommended next action",
        dashboard.recommended_next_action,
        "",
        "## Tool sequence",
    ]
    lines += [f"- {tool}" for tool in dashboard.tool_sequence] or ["- No tools selected yet."]
    lines += ["", "## Risk notes"]
    lines += [f"- {note}" for note in dashboard.risk_notes] or ["- No special risk notes."]
    lines += ["", "## Subtasks"]
    lines += [f"- {task}" for task in dashboard.subtasks] or ["- No subtasks detected."]
    lines += ["", "## Watcher", f"- Status: {dashboard.watcher.get('status')}", f"- Risk: {dashboard.watcher.get('risk')}", "", "## Verification"]
    lines += [f"- {item}" for item in dashboard.verification]
    lines += ["", "## Suggested commands"]
    lines += [f"- `{item.get('command')}` - {item.get('reason')}" for item in dashboard.suggested_commands]
    return "\n".join(lines)



def _why_dashboard(intent: str, confidence: float, subtasks: list[str], watcher: dict[str, Any], needs_choice: bool) -> str:
    if needs_choice:
        return "Nova should pause or show choices because the request has ambiguity, multiple steps, lower confidence, or watcher review requirements."
    if intent == "create_project":
        return "The request appears to be project creation; Nova should plan files, build project-local code, verify quality, and report results."
    if intent == "repair_or_debug":
        return "The request appears to be repair/debugging; Nova should reproduce or inspect the failure before editing."
    if intent == "verify":
        return "The request is verification-focused; Nova should run checks and summarize evidence."
    if watcher.get("status") in {"review-required", "blocked"}:
        return "The watcher identified risk, so user review or a safer plan is required before acting."
    return "The request is low-risk or general; Nova can answer or suggest a safe next command."


def _recommended_next_action(intent: str, confidence: float, needs_choice: bool, watcher: dict[str, Any]) -> str:
    if watcher.get("status") == "blocked":
        return "Do not execute yet; revise the plan or choose a safer diagnostic command."
    if needs_choice or confidence < 0.75:
        return "Ask an interactive planning question with a recommended choice before running tools."
    if intent == "create_project":
        return "Create project files, run acceptance/runtime probes, then repair only project-local issues if verification fails."
    if intent == "repair_or_debug":
        return "Inspect the failing file/log first, then propose the smallest surgical fix and verify it."
    if intent == "verify":
        return "Run the relevant verification suite and produce a concise report."
    return "Answer directly or offer safe command suggestions."


def _tool_sequence(intent: str, subtasks: list[str], needs_choice: bool) -> list[str]:
    if needs_choice:
        return ["interactive planning", "user choice", "watcher review", "then selected tool"]
    if intent == "create_project":
        return ["creation intent", "project generator", "project quality score", "acceptance contract", "runtime probe", "iteration report"]
    if intent == "repair_or_debug":
        return ["read/log inspect", "failure classifier", "surgical repair proposal", "targeted verification"]
    if intent == "verify":
        return ["py_compile", "tests_smoke.py", "relevant pytest suites", "quality dashboard"]
    if len(subtasks) > 1:
        return ["task decomposition", "ordered subtasks", "one tool step at a time", "verification"]
    return ["chat answer", "suggested commands"]


def _risk_notes(watcher: dict[str, Any], confidence: float, needs_choice: bool) -> list[str]:
    notes: list[str] = []
    if confidence < 0.75:
        notes.append("Intent confidence is low enough to require clarification.")
    if needs_choice:
        notes.append("User choice is recommended before running mutating tools.")
    if watcher.get("requires_approval"):
        notes.append("Watcher requires approval/review for this action.")
    for reason in watcher.get("reasons") or []:
        notes.append(str(reason))
    return notes[:8]

def _intent_from_task_plan(task_plan: Any | None, low: str) -> str:
    if task_plan is None:
        return _intent(low)
    intents = [getattr(s, "intent", "") for s in getattr(task_plan, "subtasks", [])]
    if "create" in intents or any(w in low for w in ["make", "create", "build", "generate", "write an app", "write a game"]):
        return "create_project"
    if "repair" in intents:
        return "repair_or_debug"
    if "verify" in intents:
        return "verify"
    if "modify" in intents or any(w in low for w in ["improve", "autonomous", "self"]):
        return "improvement"
    if "inspect" in intents:
        return "inspect"
    return _intent(low)


def _subtasks_from_task_plan(task_plan: Any | None, text: str) -> list[str]:
    fallback = _subtasks(text)
    if task_plan is None:
        return fallback
    out = [getattr(s, "text", "").strip() for s in getattr(task_plan, "subtasks", []) if getattr(s, "text", "").strip()]
    # task_decomposition is deliberately conservative about splitting on plain
    # "and". For the dashboard, show the user-visible step breakdown when the
    # request clearly contains multiple action clauses.
    if len(out) <= 1 and len(fallback) > 1:
        return fallback
    return out or fallback


def _plan_level_from_task_plan(task_plan: Any | None, intent: str, subtasks: list[str], low: str) -> str:
    if task_plan is None:
        return _plan_level(intent, subtasks, low)
    level = int(getattr(task_plan, "plan_level", 0) or 0)
    labels = {
        0: "Level 0 answer-only",
        1: "Level 1 inspect/verify",
        2: "Level 2 surgical edit",
        3: "Level 3 multi-step project workflow",
        4: "Level 4 build/test/debug workflow",
        5: "Level 5 autonomous/high-risk proposal",
    }
    return labels.get(level, _plan_level(intent, subtasks, low))


def _verification_from_task_plan(task_plan: Any | None, intent: str) -> list[str]:
    base = _verification(intent)
    if task_plan is None:
        return base
    criteria = [str(c) for c in getattr(task_plan, "success_criteria", []) if str(c).strip()]
    merged: list[str] = []
    for item in base + criteria:
        if item not in merged:
            merged.append(item)
    return merged or base


def _intent(low: str) -> str:
    if any(w in low for w in ["make", "create", "build", "game", "app", "calculator", "todo"]):
        return "create_project"
    if any(w in low for w in ["fix", "broken", "error", "failed", "traceback"]):
        return "repair_or_debug"
    if any(w in low for w in ["test", "verify", "check"]):
        return "verify"
    if any(w in low for w in ["improve", "autonomous", "self"]):
        return "improvement"
    return "general"


def _confidence(low: str) -> float:
    if not low.strip():
        return 0.0
    vague = ["thing", "stuff", "something", "make it", "fix it", "better", "improve it"]
    score = 0.86
    if any(v in low for v in vague):
        score -= 0.32
    if len(low.split()) < 4:
        score -= 0.15
    if "?" in low:
        score += 0.04
    return max(0.25, min(0.98, score))


def _subtasks(text: str) -> list[str]:
    parts = [p.strip(" ,.;") for p in text.replace(" then ", " and ").split(" and ") if p.strip(" ,.;")]
    if len(parts) > 1:
        return parts[:8]
    if text.strip():
        return [text.strip()]
    return []


def _plan_level(intent: str, subtasks: list[str], low: str) -> str:
    if intent == "general":
        return "Level 0 answer-only"
    if intent == "verify":
        return "Level 1 inspect/verify"
    if len(subtasks) > 1:
        return "Level 3 multi-step project workflow"
    if any(w in low for w in ["app", "game", "project"]):
        return "Level 3 multi-file patch"
    return "Level 2 surgical edit"


def _verification(intent: str) -> list[str]:
    if intent == "create_project":
        return ["syntax/static checks", "project quality score", "acceptance contract", "runtime probe"]
    if intent == "repair_or_debug":
        return ["reproduce or inspect failure", "surgical repair", "rerun failing check"]
    return ["py_compile", "python tests_smoke.py", "relevant pytest suites"]
