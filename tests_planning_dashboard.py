from __future__ import annotations

from winlocalassistant.core import AssistantCore
from winlocalassistant.planning_dashboard import build_planning_dashboard, render_planning_dashboard_markdown


def test_planning_dashboard_detects_multistep_create_request() -> None:
    dash = build_planning_dashboard("make a calculator and add tests and verify it")
    assert dash.intent == "create_project"
    assert len(dash.subtasks) >= 2
    assert dash.needs_user_choice is True
    assert dash.watcher["status"] in {"allow", "review-required", "blocked"}


def test_planning_dashboard_markdown_has_verification_and_suggestions() -> None:
    md = render_planning_dashboard_markdown(build_planning_dashboard("verify broken game"))
    assert "# Nova Planning Dashboard" in md
    assert "Verification" in md
    assert "Suggested commands" in md


def test_core_new_commands_return_useful_text() -> None:
    core = AssistantCore.load()
    assert "Action Watcher Decision" in core.chat("/action-watch /self-improve rewrite core.py")
    assert "Nova Tool Catalogue" in core.chat("/tool-catalog")
    assert "Planning Dashboard" in core.chat("/planning-dashboard make a todo app and verify it")
    assert "Interaction Lessons" in core.chat("/interaction-lessons") or "No interaction lessons" in core.chat("/interaction-lessons")


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)


def test_planning_dashboard_reuses_task_decomposition_success_criteria() -> None:
    dash = build_planning_dashboard("mkae a snak gaem then verify it")
    assert dash.intent == "create_project"
    assert dash.confidence < 0.99
    assert any("game has controls" in item for item in dash.verification)
    assert dash.needs_user_choice is True


def test_planning_dashboard_uses_multistep_plan_level_from_task_plan() -> None:
    dash = build_planning_dashboard("fix the calculator, add tests, then verify it")
    assert len(dash.subtasks) >= 3
    assert "Level 4" in dash.plan_level or "Level 3" in dash.plan_level


def test_planning_dashboard_explains_why_and_next_action() -> None:
    dash = build_planning_dashboard("make a calculator and add tests and verify it")
    assert dash.why
    assert dash.recommended_next_action
    assert dash.tool_sequence
    assert isinstance(dash.risk_notes, list)
    md = render_planning_dashboard_markdown(dash)
    assert "Why this plan" in md
    assert "Recommended next action" in md
    assert "Tool sequence" in md
    assert "Risk notes" in md
