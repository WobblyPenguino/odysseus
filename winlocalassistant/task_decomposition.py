from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class Subtask:
    index: int
    text: str
    intent: str
    needs_tools: bool
    needs_local_model: bool
    needs_verification: bool
    risk_level: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class TaskPlan:
    original_text: str
    normalized_text: str
    task_count: int
    subtasks: list[Subtask]
    plan_level: int
    intent_confidence: float
    ambiguity: list[str]
    needs_clarification: bool
    recommended_first_step: str
    success_criteria: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["subtasks"] = [s.to_dict() for s in self.subtasks]
        return data


_TYPO_REPLACEMENTS = {
    r"\bmkae\b": "make",
    r"\bmaek\b": "make",
    r"\bmakr\b": "make",
    r"\bcalcualtor\b": "calculator",
    r"\bcaluclator\b": "calculator",
    r"\bsnak\b": "snake",
    r"\bgaem\b": "game",
    r"\btodolis?t\b": "todo list",
    r"\bintergrate\b": "integrate",
    r"\bimprv\w*\b": "improve",
    r"\bimp,?lemen\s*t\b": "implement",
    r"\bimplemnt\b": "implement",
    r"\bdetermineing\b": "determining",
    r"\bhuma\b": "human",
    r"\bbvopice\b": "voice",
    r"\bvoicemode\b": "voice mode",
    r"\btalkl\b": "talk",
    r"\buit\b": "it",
}


def normalize_request_text(text: str) -> str:
    out = re.sub(r"\s+", " ", (text or "").strip())
    for pat, repl in _TYPO_REPLACEMENTS.items():
        out = re.sub(pat, repl, out, flags=re.I)
    return out


def decompose_user_request(text: str) -> TaskPlan:
    original = text or ""
    normalized = normalize_request_text(original)
    low = normalized.lower()
    pieces = [p.strip(" .") for p in re.split(r",|;|\band then\b|\bthen\b|\balso\b|\bafter that\b", normalized, flags=re.I) if p.strip(" .")]
    if not pieces:
        pieces = [normalized] if normalized else []
    actionful = [p for p in pieces if _intent_for(p) != "chat"] or pieces[:1]
    subtasks: list[Subtask] = []
    for i, part in enumerate(actionful[:8], 1):
        intent = _intent_for(part)
        subtasks.append(Subtask(
            index=i,
            text=part,
            intent=intent,
            needs_tools=intent in {"create", "modify", "repair", "verify", "inspect"},
            needs_local_model=intent in {"create", "modify", "repair"} or _is_vague(part),
            needs_verification=intent in {"create", "modify", "repair", "verify"},
            risk_level=_risk_for(part, intent),
        ))
    ambiguity = _ambiguities(low, subtasks)
    confidence = _confidence(low, ambiguity, subtasks)
    needs_clarification = confidence < 0.85 or bool(ambiguity)
    plan_level = _plan_level(subtasks, low)
    criteria = _success_criteria(subtasks, low)
    first = "ask_clarifying_question" if needs_clarification else (subtasks[0].intent if subtasks else "answer")
    return TaskPlan(original, normalized, len(subtasks), subtasks, plan_level, confidence, ambiguity, needs_clarification, first, criteria)


def _intent_for(text: str) -> str:
    low = text.lower()
    if any(k in low for k in ["verify", "test", "check", "validate", "confirm"]):
        return "verify"
    if any(k in low for k in ["fix", "repair", "broken", "error", "not working", "bug", "regression"]):
        return "repair"
    if any(k in low for k in ["inspect", "look at", "read", "analyse", "analyze", "audit", "review"]):
        return "inspect"
    if any(k in low for k in ["improve", "update", "change", "add", "refactor", "implement", "integrate", "make better", "better at"]):
        return "modify"
    if any(k in low for k in ["make", "build", "create", "generate", "write", "scaffold"]):
        return "create"
    return "chat"


def _is_vague(text: str) -> bool:
    low = text.lower()
    return any(x in low for x in ["make an app", "make a game", "make something", "fix it", "improve it", "make it better", "make the ai better", "what the human is asking"])


def _risk_for(text: str, intent: str) -> str:
    low = text.lower()
    if any(x in low for x in ["self-improve", "wla source", "autonomous", "auto apply", "delete", "install", "network", "voice mode", "intent router"]):
        return "high"
    if intent in {"create", "modify", "repair"}:
        return "medium"
    return "low"


def _ambiguities(low: str, subtasks: list[Subtask]) -> list[str]:
    out: list[str] = []
    if any(x in low for x in ["make an app", "make a game", "make something", "fix it", "improve it", "make the ai better"]):
        out.append("request is vague")
    if len(subtasks) > 1 and not any(x in low for x in ["first", "then", "after", "in order"]):
        out.append("multiple tasks without explicit order")
    if any(s.risk_level == "high" for s in subtasks):
        out.append("high-risk mutation or autonomous behaviour mentioned")
    return out


def _confidence(low: str, ambiguity: list[str], subtasks: list[Subtask]) -> float:
    score = 0.92
    score -= 0.18 * len(ambiguity)
    if not subtasks or any(s.intent == "chat" for s in subtasks):
        score -= 0.12
    if any(word in low for word in ["calculator", "todo", "snake", "file organiser", "file organizer"]):
        score += 0.08
    return max(0.05, min(0.99, round(score, 2)))


def _plan_level(subtasks: list[Subtask], low: str) -> int:
    if not subtasks or subtasks[0].intent == "chat":
        return 0
    if any(s.risk_level == "high" for s in subtasks):
        return 5
    if len(subtasks) >= 3:
        return 4
    if len(subtasks) == 2:
        return 3
    if subtasks[0].intent in {"create", "modify", "repair"}:
        return 2
    return 1


def _success_criteria(subtasks: list[Subtask], low: str) -> list[str]:
    criteria = ["requested behaviour is visible", "relevant verification passes", "final response lists changed files and remaining limits"]
    if any(x in low for x in ["human is asking", "intent", "determine what", "understand"]):
        criteria.append("intent analysis separates build, edit, inspect, verify, chat, and self-improvement requests")
    if "voice" in low or "talk" in low or "speech" in low:
        criteria.append("voice mode can transcribe user speech into the composer and speak assistant replies")
    if "calculator" in low:
        criteria.append("calculator accepts input, computes results, and supports clear/backspace")
    if "todo" in low or "to-do" in low:
        criteria.append("todo app can add, delete, complete, and re-render tasks")
    if "game" in low or "snake" in low:
        criteria.append("game has controls, objective, score/progress, collision/interaction, restart, and instructions")
    if any(s.risk_level == "high" for s in subtasks):
        criteria.append("high-risk actions remain proposal-only unless explicitly approved and verified")
    return criteria
