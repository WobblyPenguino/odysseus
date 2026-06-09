from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.interaction_learning import append_interaction_lesson, derive_interaction_lesson, load_interaction_lessons, relevant_lessons, render_lessons_markdown
from winlocalassistant.tool_catalog import find_tool_entry, get_tool_catalog, render_tool_catalog_markdown


def test_tool_catalog_contains_risk_verification_and_fallback_metadata() -> None:
    catalog = get_tool_catalog()
    assert any(entry.name == "self_improve" and entry.risk == "high" for entry in catalog)
    assert all(entry.verification and entry.fallback for entry in catalog)
    assert find_tool_entry("idle-propose") is not None


def test_tool_catalog_markdown_mentions_never_use() -> None:
    md = render_tool_catalog_markdown()
    assert "Never use for" in md
    assert "self_improve" in md


def test_interaction_lesson_records_project_quality_feedback() -> None:
    lesson = derive_interaction_lesson("make calculator", "ai_create_project", "created", "calculator was bad and not functional")
    assert "Calculator outputs" in lesson.lesson
    assert "quality_failure" in lesson.tags


def test_interaction_lesson_jsonl_load_and_relevance() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_lessons_") as tmp:
        path = Path(tmp) / "lessons.jsonl"
        lesson = derive_interaction_lesson("make snake game", "ai_create_project", "failed", "game was broken")
        append_interaction_lesson(lesson, path)
        loaded = load_interaction_lessons(path)
        assert loaded and loaded[0].intent == "create_project"
        assert relevant_lessons("snake game", path)
        assert "Interaction Lessons" in render_lessons_markdown(loaded)


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
