from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant.creation_intent import analyze_creation_request, project_target_decision
from winlocalassistant.planner import make_plan
from winlocalassistant.webui import HTML
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def test_project_target_decision_clarifies_different_artifact():
    decision = project_target_decision("make a snake game", {"goal": "build a todo list web app"})
    assert decision["decision"] == "clarify"
    assert "new project" in decision["question"].lower()
    assert any(cmd.startswith("/do create a new project") for cmd in decision["recommended_commands"])


def test_project_target_decision_respects_explicit_current_project():
    decision = project_target_decision("add a snake game inside this current project", {"goal": "build a todo list web app"})
    assert decision["decision"] == "current_project"


def test_make_plan_asks_project_target_for_ambiguous_current_workspace(tmp_path):
    (tmp_path / "PROJECT_MANIFEST.json").write_text(json.dumps({"goal": "build a todo list web app"}), encoding="utf-8")
    plan = make_plan("add a snake game", workspace=tmp_path, mode="auto")
    assert plan.mode == "clarify"
    assert plan.steps[0].tool == "project_target_decision"


def test_tool_project_target_decision_returns_user_commands(tmp_path):
    (tmp_path / "PROJECT_MANIFEST.json").write_text(json.dumps({"goal": "build a todo list web app"}), encoding="utf-8")
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False)
    result = ToolRegistry(cfg).call("project_target_decision", goal="make a snake game")
    assert result.ok
    assert "Project target decision needed" in result.data["message"]
    assert "/do create a new project" in result.data["message"]


def test_creation_intent_keeps_dodge_guardrails():
    assert analyze_creation_request("make a calculator")["dodge_fallback_allowed"] is False
    assert analyze_creation_request("make a dodge game")["dodge_fallback_allowed"] is True


def test_webui_feedback_and_settings_controls_exist():
    assert "showFeedbackButtons" in HTML
    assert "recordFeedback" in HTML
    assert "Was this useful" in HTML
    assert "showComposerButtons" in HTML
    assert "showCommandSuggestions" in HTML
    assert "Suggested commands never auto-run" in HTML


def test_webui_created_output_metadata_and_refresh_notice():
    assert "Created output ready" in HTML
    assert "Project:" in HTML
    assert "Project/file lists refresh automatically" in HTML
    assert "loadFiles();loadProjects();loadActivity();" in HTML


def run_all():
    tests = [
        test_project_target_decision_clarifies_different_artifact,
        test_project_target_decision_respects_explicit_current_project,
        lambda: test_make_plan_asks_project_target_for_ambiguous_current_workspace(Path(__import__('tempfile').TemporaryDirectory().name)),
    ]
    # The tmp_path tests are handled better by pytest; direct smoke imports this module only.
    for fn in [
        test_creation_intent_keeps_dodge_guardrails,
        test_webui_feedback_and_settings_controls_exist,
        test_webui_created_output_metadata_and_refresh_notice,
    ]:
        fn()
        print(f"PASS {fn.__name__}")


if __name__ == "__main__":
    run_all()
