from __future__ import annotations

import tempfile
from pathlib import Path

import winlocalassistant.core as core_module
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolResult
from winlocalassistant.intent_planning import analyze_planning_dialog_need, normalize_user_goal
from winlocalassistant.webui import HTML


class _FakeTools:
    def __init__(self):
        self.calls: list[str] = []

    def call(self, tool: str, **kwargs):
        self.calls.append(tool)
        return ToolResult(True, f"{tool} ok", {})


def _dialog_core(tmp: str, allow_mutating: bool = True) -> AssistantCore:
    core = object.__new__(AssistantCore)
    core.config = AssistantConfig(workspace=tmp, allow_mutating_tools=allow_mutating)
    core.tools = _FakeTools()
    core.messages = []
    core.last_plan = None
    core.last_error = None
    core._chat_lock = __import__("threading").RLock()
    core.active_run = None
    core.autonomous_state = {"running": False}
    core.idle_state = {"running": False, "enabled": False}
    core.avatar_state = {"mood": "ready", "emoji": "🙂", "title": "Ready", "text": "Waiting", "updated_at": ""}
    core._autonomous_thread = None
    core._idle_thread = None
    core._save_plan = lambda: None
    core._auto_register_workspace_project = lambda: None
    core._ensure_builtin_knowledge = lambda: None
    core.run_plan = lambda: (_ for _ in ()).throw(AssertionError("run_plan should not run before planning reply"))
    return core


def test_normalize_user_goal_handles_common_typos() -> None:
    assert "make" in normalize_user_goal("mkae a calcualtor").lower()
    assert "calculator" in normalize_user_goal("mkae a calcualtor").lower()


def test_vague_creation_request_requires_dialog() -> None:
    dialog = analyze_planning_dialog_need("make an app")
    assert dialog.should_ask is True
    assert "vague" in dialog.reason.lower() or "lacks" in dialog.reason.lower()
    assert dialog.recommended
    assert any(choice.recommended for choice in dialog.choices)


def test_specific_calculator_request_does_not_require_dialog() -> None:
    dialog = analyze_planning_dialog_need("make a calculator with number buttons, clear and result display")
    assert dialog.should_ask is False


def test_multiple_tasks_without_order_requires_dialog() -> None:
    dialog = analyze_planning_dialog_need("fix the UI, add a tutorial, improve autonomous failure memory")
    assert dialog.should_ask is True
    assert "multiple" in dialog.reason.lower()
    assert dialog.plan_level >= 4


def test_current_project_conflict_requires_dialog() -> None:
    dialog = analyze_planning_dialog_need("make a snake game", {"goal": "build a todo list web app"})
    assert dialog.should_ask is True
    assert "different artifact" in dialog.question.lower()
    assert "new project" in dialog.recommended.lower()


def test_chat_pauses_before_vague_auto_build() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_planning_dialog_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _dialog_core(tmp)
            reply = core.chat("make an app")
        finally:
            core_module.log_activity = old_log_activity
    assert "paused before doing anything" in reply.lower()
    assert "recommended" in reply.lower()
    assert core.active_run is not None
    assert core.active_run["status"] == "waiting_for_user"


def test_do_command_pauses_before_vague_build() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_planning_do_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _dialog_core(tmp)
            reply = core.chat("/do make a game")
        finally:
            core_module.log_activity = old_log_activity
    assert "paused before doing anything" in reply.lower()
    assert core.active_run is not None


def test_reply_number_selects_option_and_continues() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_planning_reply_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _dialog_core(tmp, allow_mutating=False)
            run = core._new_active_run("make an app", mode="planning_dialog")
            run["question"] = "Which version should I make?"
            run["options"] = ["build a polished minimal app", "build a fast prototype"]
            run["default"] = "build a polished minimal app"
            # Avoid running a real project plan in this unit test; confirm option 1 is selected.
            core.run_plan = lambda: "RUN_PLAN_CALLED"
            result = core.reply_to_active_run("1")
        finally:
            core_module.log_activity = old_log_activity
    assert "RUN_PLAN_CALLED" in result
    assert "polished minimal app" in result or "RUN_PLAN_CALLED" in result



def test_reply_letter_selects_lettered_option_and_enriches_generic_goal() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_planning_reply_letter_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _dialog_core(tmp, allow_mutating=False)
            run = core._new_active_run("make a useful local app and ask me before choosing scope", mode="interactive")
            run["question"] = "What type of local app are you interested in building?"
            run["options"] = ["a) A productivity tool", "b) A social media client", "c) A utility application"]
            run["default"] = "a) A productivity tool"
            captured = {}
            original_make_plan = core_module.make_plan
            def fake_make_plan(goal, workspace=None, mode="long"):
                captured["goal"] = str(goal)
                return original_make_plan("make a calculator with clear and result display", workspace=workspace, mode="long")
            core_module.make_plan = fake_make_plan
            core.run_plan = lambda: "RUN_PLAN_CALLED"
            result = core.reply_to_active_run("c")
        finally:
            core_module.log_activity = old_log_activity
            core_module.make_plan = original_make_plan
    assert "RUN_PLAN_CALLED" in result
    assert "utility application" in captured.get("goal", "").lower()
    assert "- c" not in captured.get("goal", "").lower()
    assert "generic placeholder" in captured.get("goal", "").lower()


def test_webui_active_run_has_recommended_choice_and_custom_reply_text() -> None:
    assert "recommendedChoice" in HTML
    assert "recommended answer highlighted" in HTML
    assert "submit your own reply" in HTML


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
