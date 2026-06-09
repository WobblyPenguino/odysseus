from __future__ import annotations

import tempfile
from pathlib import Path

import winlocalassistant.core as core_module
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.request_intent import analyze_request_intent, should_block_automatic_mutation
from winlocalassistant.tools import ToolResult


class _FakeAutonomousTools:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def call(self, tool: str, **kwargs):
        del kwargs
        self.calls.append(tool)
        return ToolResult(True, f"{tool} ok", {})


def _guarded_core(tmp: str) -> AssistantCore:
    core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
    core.last_plan = None
    core.run_plan = lambda: (_ for _ in ()).throw(AssertionError("run_plan should not be called"))
    return core


def test_request_intent_blocks_wla_source_auto_mutation() -> None:
    intent = analyze_request_intent("Improve Nova safely by adding autonomous failure memory. Do not auto-apply edits.")
    assert intent.category == "self_improvement"
    assert intent.target_is_wla_source is True
    assert intent.forbids_auto_apply is True
    assert should_block_automatic_mutation(intent) is True


def test_request_intent_detects_no_auto_apply_variants() -> None:
    for text in [
        "Improve Nova but do not auto apply edits",
        "Improve Nova with no auto apply",
        "Improve Nova in proposal-only mode",
    ]:
        intent = analyze_request_intent(text)
        assert intent.forbids_auto_apply is True
        assert should_block_automatic_mutation(intent) is True


def test_request_intent_allows_normal_project_build() -> None:
    intent = analyze_request_intent("make a snake game")
    assert intent.category == "project_build"
    assert intent.target_is_wla_source is False
    assert should_block_automatic_mutation(intent) is False


def test_plain_english_project_request_routes_to_create_project() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_plain_build_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
            core.run_plan = lambda: "stubbed run complete"
            reply = core.chat("make a polished browser game about rabbits")
        finally:
            core_module.log_activity = old_log_activity

    assert "I treated that as a build/edit task" in reply
    assert "stubbed run complete" in reply
    assert core.last_plan is not None
    assert core.last_plan.steps
    assert core.last_plan.steps[0].tool == "ai_create_project"
    assert "rabbit" in str(core.last_plan.steps[0].args).lower()


def test_manual_self_improve_command_is_explicit_manual_flow() -> None:
    intent = analyze_request_intent("/self-improve add a small report-only test")
    assert intent.explicit_manual_self_improve is True
    assert intent.target_is_wla_source is True
    assert should_block_automatic_mutation(intent) is False


def test_chat_guard_does_not_auto_run_wla_edit_plan() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_intent_chat_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _guarded_core(tmp)
            reply = core.chat("Improve Nova safely by adding request intent checks. Do not auto-apply edits.")
        finally:
            core_module.log_activity = old_log_activity

    assert "did not run an automatic edit/build plan" in reply
    assert "/idle propose" in reply
    assert core.last_plan is None


def test_do_command_guard_does_not_auto_run_wla_edit_plan() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_intent_do_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _guarded_core(tmp)
            reply = core.chat("/do Improve Nova safely by adding request intent checks")
        finally:
            core_module.log_activity = old_log_activity

    assert "did not run an automatic edit/build plan" in reply
    assert core.last_plan is None


def test_all_mutating_commands_guard_wla_or_no_auto_apply_goals() -> None:
    commands = [
        "/fast Improve Nova safely",
        "/long Improve Nova safely",
        "/continue Improve Nova safely",
        "/agent Improve Nova safely",
        "/improve-project Improve Nova safely",
        "/do make a calculator with no auto apply",
    ]
    with tempfile.TemporaryDirectory(prefix="wla_intent_commands_") as tmp:
        old_log_activity = core_module.log_activity
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core = _guarded_core(tmp)
            replies = [core.chat(command) for command in commands]
        finally:
            core_module.log_activity = old_log_activity

    assert all("did not run an automatic edit/build plan" in reply for reply in replies)
    assert core.last_plan is None


def test_autonomous_self_improvement_goal_stays_proposal_only() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_intent_autonomous_") as tmp:
        old_log_activity = core_module.log_activity
        old_set_current_run = core_module.set_current_run
        try:
            core_module.log_activity = lambda *args, **kwargs: None
            core_module.set_current_run = lambda *args, **kwargs: None
            core = object.__new__(AssistantCore)
            core.config = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
            core.tools = _FakeAutonomousTools()
            core.autonomous_state = {
                "enabled": False,
                "running": False,
                "stop_requested": False,
                "cycle": 0,
                "goal": "",
                "events": [],
                "cycle_summaries": [],
                "improvement_log": [],
            }
            core._set_autonomous_state = lambda **updates: core.autonomous_state.update(updates)

            reply = core.autonomous_once("Improve Nova safely. Do not auto-apply edits.")
        finally:
            core_module.log_activity = old_log_activity
            core_module.set_current_run = old_set_current_run

    assert "Request intent guard" in reply
    assert "improve_project" not in core.tools.calls
    assert "self_improve" not in core.tools.calls
    assert "tool_create" not in core.tools.calls
    assert "propose_improvements" in core.tools.calls


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
