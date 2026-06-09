from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from .creation_intent import analyze_creation_request, project_target_decision
from .task_decomposition import decompose_user_request


@dataclass
class PlanningChoice:
    label: str
    reply: str
    reason: str
    recommended: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlanningDialog:
    should_ask: bool
    question: str
    choices: list[PlanningChoice]
    recommended: str
    reason: str
    normalized_text: str
    detected_intents: list[str]
    ordered_subtasks: list[str]
    plan_level: int
    intent_confidence: float = 1.0
    ambiguity: list[str] | None = None
    success_criteria: list[str] | None = None
    custom_reply_allowed: bool = True

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["choices"] = [choice.to_dict() for choice in self.choices]
        return data


def normalize_user_goal(text: str) -> str:
    """Small typo/spacing normalizer for planning decisions, not user-visible rewriting."""
    raw = re.sub(r"\s+", " ", (text or "").strip())
    replacements = {
        r"\bmkae\b": "make",
        r"\bmkaing\b": "making",
        r"\bcaluclator\b": "calculator",
        r"\bcalcualtor\b": "calculator",
        r"\btodolis?t\b": "todo list",
        r"\btodo\s+list\b": "todo list",
        r"\bsnak\b": "snake",
        r"\bgaem\b": "game",
        r"\bwebiste\b": "website",
        r"\bintergrate\b": "integrate",
        r"\binterper?ting\b": "interpreting",
        r"\bimp,?lemen\s*t\b": "implement",
        r"\bimplemnt\b": "implement",
        r"\bdetermineing\b": "determining",
        r"\bhuma\b": "human",
        r"\bbvopice\b": "voice",
        r"\bvoicemode\b": "voice mode",
        r"\btalkl\b": "talk",
        r"\buit\b": "it",
    }
    text2 = raw
    for pat, repl in replacements.items():
        text2 = re.sub(pat, repl, text2, flags=re.I)
    return text2



def _is_custom_tool_creation_request(low: str) -> bool:
    """Return True for requests that should use Nova's custom-tool creator, not app/project planning."""
    if "tool" not in low:
        return False
    if any(term in low for term in ["custom tool", "tool creator", "tool-create", "make your own tool", "create your own tool"]):
        return True
    if any(term in low for term in ["yourself", "for yourself", "for wla", "for nova", "for the assistant", "for winlocalassistant"]):
        return any(verb in low for verb in ["make", "create", "build", "write", "generate"])
    return False

def analyze_planning_dialog_need(user_text: str, current_project: dict[str, Any] | None = None) -> PlanningDialog:
    normalized = normalize_user_goal(user_text)
    low = normalized.lower()
    if _is_custom_tool_creation_request(low):
        return PlanningDialog(False, "", [], "", "Custom-tool creation request should use the guarded tool creator, not the generic project/app planning dialog.", normalized, ["tool_create"], [], 1, 0.98, [], ["create or propose a safe reusable Nova custom tool"])
    intents = _detect_intents(low)
    task_plan = decompose_user_request(normalized)
    subtasks = [s.text for s in task_plan.subtasks] or _extract_subtasks(normalized)
    creation = analyze_creation_request(normalized)
    plan_level = max(_plan_level(low, intents, subtasks), task_plan.plan_level)
    intent_confidence = task_plan.intent_confidence
    ambiguity = task_plan.ambiguity
    success_criteria = task_plan.success_criteria

    target_decision = project_target_decision(normalized, current_project or {}) if current_project else {"decision": "new_project"}
    if target_decision.get("decision") == "clarify":
        return _dialog(
            question="This looks like a different artifact than the active project. What should I target?",
            choices=[
                PlanningChoice("Create new project", "create a new project for " + normalized, "Avoid mixing unrelated artifacts.", True),
                PlanningChoice("Modify current project", "modify the current project to include " + normalized, "Use only if this should belong inside the open project."),
                PlanningChoice("Plan only", "make a plan first without editing files", "Safest if you are unsure."),
            ],
            reason=str(target_decision.get("reason") or "active project conflict"),
            normalized=normalized,
            intents=intents,
            subtasks=subtasks,
            plan_level=max(plan_level, 3),
        )

    if _is_explicit_enough(low, creation):
        return PlanningDialog(False, "", [], "", "Request has enough detail.", normalized, intents, subtasks, plan_level, intent_confidence, ambiguity, success_criteria)

    if len(subtasks) >= 2 and not _has_ordering_language(low):
        return _dialog(
            question="Your request has multiple tasks. Which order should Nova use first?",
            choices=[
                PlanningChoice("Plan then implement", "make a plan first, then implement the safest first task", "Best balance of speed and safety.", True),
                PlanningChoice("UI first", "start with the UI/visible behaviour first", "Useful when the main problem is usability."),
                PlanningChoice("Reliability first", "start with tests and reliability fixes first", "Best if current behaviour is broken."),
            ],
            reason="multiple tasks without explicit order",
            normalized=normalized,
            intents=intents,
            subtasks=subtasks,
            plan_level=max(plan_level, 4),
        )

    if _is_vague_creation(low, creation):
        artifact = str(creation.get("artifact_type") or "project")
        return _dialog(
            question="I can build this, but the request is vague. Which version should I make?",
            choices=[
                PlanningChoice("Recommended: polished minimal", f"build a polished minimal {artifact} with instructions, verification, and a clear success check", "Creates a useful result without overbuilding.", True),
                PlanningChoice("Fast prototype", f"build a fast prototype {artifact}", "Quickest path, less polish."),
                PlanningChoice("Ask feature by feature", "ask me the feature list before creating files", "Best if you have a specific idea."),
            ],
            reason="creation request lacks enough feature/detail choices",
            normalized=normalized,
            intents=intents,
            subtasks=subtasks,
            plan_level=max(plan_level, 2),
        )

    if any(term in low for term in ["ask me", "before doing", "before making", "before building", "if unsure"]):
        return _dialog(
            question="How much planning should I do before touching files?",
            choices=[
                PlanningChoice("Plan first", "make a plan first and wait before editing", "Safest default.", True),
                PlanningChoice("Interactive build", "ask me one clarification then build", "Good for medium tasks."),
                PlanningChoice("Proceed", "proceed with the current request", "Use only when the goal is already clear."),
            ],
            reason="user asked for a pre-action check",
            normalized=normalized,
            intents=intents,
            subtasks=subtasks,
            plan_level=max(plan_level, 2),
        )

    return PlanningDialog(False, "", [], "", "No planning dialog needed.", normalized, intents, subtasks, plan_level, intent_confidence, ambiguity, success_criteria)


def _dialog(question: str, choices: list[PlanningChoice], reason: str, normalized: str, intents: list[str], subtasks: list[str], plan_level: int) -> PlanningDialog:
    rec = next((choice.reply for choice in choices if choice.recommended), choices[0].reply if choices else "")
    plan = decompose_user_request(normalized)
    return PlanningDialog(True, question, choices, rec, reason, normalized, intents, subtasks, plan_level, plan.intent_confidence, plan.ambiguity, plan.success_criteria)


def _detect_intents(low: str) -> list[str]:
    intents: list[str] = []
    if any(k in low for k in ["make", "build", "create", "generate", "write", "scaffold"]):
        intents.append("create")
    if any(k in low for k in ["fix", "repair", "broken", "not working", "error", "bug", "regression"]):
        intents.append("repair")
    if any(k in low for k in ["inspect", "look over", "look at", "audit", "review"]):
        intents.append("inspect")
    if any(k in low for k in ["improve", "update", "change", "add", "implement", "integrate", "better at"]):
        intents.append("modify")
    if any(k in low for k in ["test", "verify", "check", "validate"]):
        intents.append("verify")
    if any(k in low for k in ["voice mode", "speech", "talk to it", "talk back"]):
        intents.append("voice")
    return intents or ["chat"]


def _extract_subtasks(text: str) -> list[str]:
    parts = [p.strip(" .") for p in re.split(r",|;|\band then\b|\bthen\b|\balso\b", text, flags=re.I) if p.strip(" .")]
    actionful = [p for p in parts if re.search(r"\b(make|build|create|fix|improve|add|update|change|test|verify|validate|repair|implement|integrate|audit|review|inspect)\b", p, re.I)]
    return actionful[:8]


def _has_ordering_language(low: str) -> bool:
    return any(term in low for term in ["first", "then", "after", "before", "step 1", "in order"])


def _is_vague_creation(low: str, creation: dict[str, Any]) -> bool:
    if not any(k in low for k in ["make", "build", "create", "generate", "write"]):
        return False
    if _is_custom_tool_creation_request(low):
        return False
    vague_terms = ["make an app", "make a app", "make a game", "make something", "create a project", "build a project", "make it better"]
    if any(term in low for term in vague_terms):
        return True
    artifact = str(creation.get("artifact_type") or "")
    features = creation.get("requested_features") or []
    theme = str(creation.get("requested_theme") or "")
    return artifact in {"unknown", "html_css_js_page"} and not features and not theme and len(low.split()) < 8


def _is_explicit_enough(low: str, creation: dict[str, Any]) -> bool:
    if any(term in low for term in ["make a game", "make an app", "make a app", "make something", "create a project", "build a project"]):
        return False
    game_design = creation.get("game_design") if isinstance(creation, dict) else None
    if isinstance(game_design, dict) and game_design.get("genre") == "generic_browser_game":
        return False
    if any(term in low for term in ["calculator", "todo", "snake", "file organiser", "file organizer", "dodge game"]):
        return True
    # Generic game scaffold adds baseline behaviours automatically; do not treat those as user-specified detail.
    if "game" not in low and len(creation.get("requested_features") or []) >= 2:
        return True
    if any(term in low for term in ["fast minimal", "long polished", "with controls", "with search", "with export", "with login"]):
        return True
    return False


def _plan_level(low: str, intents: list[str], subtasks: list[str]) -> int:
    if intents == ["chat"]:
        return 0
    if "verify" in intents and len(intents) == 1:
        return 1
    if len(subtasks) >= 3:
        return 4
    if "create" in intents or "modify" in intents:
        return 2 if len(subtasks) <= 1 else 3
    return 1
