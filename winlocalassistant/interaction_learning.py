from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import append_jsonl, tail_jsonl_rows

LESSONS_PATH = APP_DIR / "INTERACTION_LESSONS.jsonl"


@dataclass
class InteractionLesson:
    timestamp: str
    user_request: str
    intent: str
    tool_used: str
    outcome: str
    user_feedback: str
    lesson: str
    tags: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def derive_interaction_lesson(user_request: str, tool_used: str = "", outcome: str = "", user_feedback: str = "") -> InteractionLesson:
    text = "\n".join([user_request, outcome, user_feedback]).lower()
    intent = "create_project" if any(w in text for w in ["make", "create", "build", "app", "game", "calculator", "todo"]) else "general"
    tags: list[str] = []
    if "calculator" in text:
        tags.append("calculator")
    if "game" in text or "snake" in text:
        tags.append("game")
    if "not functional" in text or "bad" in text or "broken" in text:
        tags.append("quality_failure")
    if "repeat" in text or "same" in text:
        tags.append("repetition")
    lesson = _lesson_text(user_request, outcome, user_feedback, tags)
    return InteractionLesson(time.strftime("%Y-%m-%d %H:%M:%S"), user_request, intent, tool_used or "unknown", outcome or "unknown", user_feedback or "", lesson, tags)


def append_interaction_lesson(lesson: InteractionLesson, path: Path = LESSONS_PATH) -> Path:
    append_jsonl(path, lesson.to_dict(), ensure_ascii=False)
    return path


def load_interaction_lessons(path: Path = LESSONS_PATH, limit: int = 50) -> list[InteractionLesson]:
    rows: list[InteractionLesson] = []
    for data in tail_jsonl_rows(path, max(1, int(limit)), multiplier=1):
        try:
            rows.append(InteractionLesson(**data))
        except Exception:
            continue
    return rows


def relevant_lessons(query: str, path: Path = LESSONS_PATH, limit: int = 5) -> list[InteractionLesson]:
    terms = {w for w in (query or "").lower().split() if len(w) > 3}
    scored: list[tuple[int, InteractionLesson]] = []
    for lesson in load_interaction_lessons(path, limit=100):
        hay = " ".join([lesson.user_request, lesson.intent, lesson.lesson, " ".join(lesson.tags)]).lower()
        score = sum(1 for term in terms if term in hay) + sum(2 for tag in lesson.tags if tag in terms)
        if score:
            scored.append((score, lesson))
    return [lesson for _, lesson in sorted(scored, key=lambda item: item[0], reverse=True)[:limit]]


def render_lessons_markdown(lessons: list[InteractionLesson]) -> str:
    if not lessons:
        return "No interaction lessons recorded yet."
    lines = ["# Interaction Lessons", ""]
    for lesson in lessons:
        lines += [f"- **{lesson.intent}** via `{lesson.tool_used}` at {lesson.timestamp}: {lesson.lesson}"]
    return "\n".join(lines)


def _lesson_text(user_request: str, outcome: str, feedback: str, tags: list[str]) -> str:
    if "calculator" in tags and "quality_failure" in tags:
        return "Calculator outputs need working buttons, operation state, clear/backspace and visible result updates before success is claimed."
    if "game" in tags and "quality_failure" in tags:
        return "Game outputs need controls, objective, score/progress, interaction/collision, restart and instructions before success is claimed."
    if "repetition" in tags:
        return "Avoid repeating the same failed action; diagnose and choose a different repair or ask the user."
    return (feedback or outcome or user_request or "Record outcome and improve future planning.")[:400]
