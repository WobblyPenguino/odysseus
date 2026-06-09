from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence, render_autonomous_sequence_markdown
from winlocalassistant.config import AssistantConfig
import winlocalassistant.core as core_module
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry, ToolResult


def test_create_project_sequence_uses_generation_then_verification() -> None:
    plan = build_autonomous_tool_sequence("make a calculator app and verify it")
    tools = [s.tool for s in plan.steps]
    assert plan.intent == "create_project"
    assert "ai_create_project" in tools
    assert "auto_verify" in tools
    assert "final_project_check" in tools
    assert tools.index("ai_create_project") < tools.index("final_project_check")


def test_repair_sequence_inspects_then_surgical_repairs() -> None:
    plan = build_autonomous_tool_sequence("fix the broken game error and verify it")
    tools = [s.tool for s in plan.steps]
    assert plan.intent == "repair_or_debug"
    assert "investigate_logs" in tools
    assert "surgical_repair" in tools
    assert "auto_verify" in tools
    assert tools.index("investigate_logs") < tools.index("surgical_repair")


def test_verify_sequence_is_not_project_generation() -> None:
    plan = build_autonomous_tool_sequence("verify the current project")
    tools = [s.tool for s in plan.steps]
    assert plan.intent == "verify"
    assert "auto_verify" in tools
    assert "ai_create_project" not in tools


def test_autonomous_plan_command_is_read_only_and_explains_sequence() -> None:
    core = AssistantCore.load()
    out = core.chat("/autonomous-plan make a snake game and verify it")
    assert "Autonomous Tool Sequence" in out
    assert "ai_create_project" in out
    assert "final_project_check" in out


def test_autonomous_explain_includes_sequence_preview() -> None:
    core = AssistantCore.load()
    out = core.chat("/autonomous-explain fix calculator bug and verify it")
    assert "Autonomous Tool Sequence" in out
    assert "Nova Planning Dashboard" in out


class FakeSequencedTools(ToolRegistry):
    def __init__(self, config: AssistantConfig):
        super().__init__(config)
        self.calls: list[str] = []

    def call(self, tool_name: str, **kwargs):  # type: ignore[override]
        self.calls.append(tool_name)
        if tool_name == "ai_create_project":
            return ToolResult(True, "created project", {"written": [{"path": "index.html", "bytes": 10}]})
        return ToolResult(True, f"{tool_name} ok", {})


def test_autonomous_once_executes_task_specific_sequence_after_observation() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autoseq_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        core.tools = FakeSequencedTools(cfg)
        out = core.autonomous_once("make a calculator app")
        calls = core.tools.calls  # type: ignore[attr-defined]
        assert "ai_create_project" in calls
        assert "final_project_check" in calls
        assert "zip_path" in calls
        assert calls.index("ai_create_project") < calls.index("final_project_check")
        assert "Sequenced tool plan" in out


def test_markdown_renderer_lists_reasons_and_risks() -> None:
    plan = build_autonomous_tool_sequence("improve current project")
    md = render_autonomous_sequence_markdown(plan)
    assert "Why this sequence" in md
    assert "Steps" in md
    assert "Risk notes" in md


def test_autonomous_enabled_cycle_runs_guarded_auto_apply_hook() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autoapply_hook_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        old_loader = core_module.load_idle_autonomy_settings
        calls: list[str] = []
        try:
            core_module.load_idle_autonomy_settings = lambda: {"idle_auto_apply_low_risk": True}  # type: ignore[assignment]
            core._idle_auto_apply_once = lambda goal: calls.append(goal) or "Idle auto-apply applied one low-risk patch.\nStatus: applied"  # type: ignore[method-assign]
            core._set_autonomous_state(enabled=True, current_run_id="run-auto", cycle=1)
            report: list[str] = []
            core._autonomous_auto_apply_low_risk_idle_candidate("improve reports", report, "run-auto")
        finally:
            core_module.load_idle_autonomy_settings = old_loader  # type: ignore[assignment]

    assert calls == ["Autonomous cycle: improve reports"]
    assert any("Autonomous low-risk auto-apply result" in line for line in report)
    assert any("Status: applied" in line for line in report)


def run_all(verbose: bool = False) -> None:
    tests = [
        test_create_project_sequence_uses_generation_then_verification,
        test_repair_sequence_inspects_then_surgical_repairs,
        test_verify_sequence_is_not_project_generation,
        test_autonomous_plan_command_is_read_only_and_explains_sequence,
        test_autonomous_explain_includes_sequence_preview,
        test_autonomous_once_executes_task_specific_sequence_after_observation,
        test_markdown_renderer_lists_reasons_and_risks,
        test_autonomous_enabled_cycle_runs_guarded_auto_apply_hook,
    ]
    for fn in tests:
        fn()
        if verbose:
            print(f"PASS {fn.__name__}")

class SlowHeartbeatTools(ToolRegistry):
    def __init__(self, config: AssistantConfig):
        super().__init__(config)
        self.calls: list[str] = []

    def call(self, tool_name: str, **kwargs):  # type: ignore[override]
        import time
        self.calls.append(tool_name)
        if tool_name == "heartbeat":
            time.sleep(0.15)
            return ToolResult(True, "late heartbeat", {})
        return ToolResult(True, f"{tool_name} ok", {})


def test_autonomous_tool_timeout_returns_instead_of_freezing() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autotimeout_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        core.tools = SlowHeartbeatTools(cfg)
        original = core._autonomous_tool_timeout
        core._autonomous_tool_timeout = lambda tool: 0.05 if tool == "heartbeat" else original(tool)  # type: ignore[method-assign]
        report: list[str] = []
        result = core._autonomous_call_tool("Heartbeat", "heartbeat", {}, report, "run-timeout-test")
        assert not result.ok
        assert result.data.get("timed_out") is True
        assert "instead of freezing" in result.summary
        assert any("Heartbeat" in line for line in report)


def test_autonomous_start_sets_visible_starting_state_before_worker_runs() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autostart_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        core = AssistantCore(cfg)
        core._autonomous_loop = lambda: None  # type: ignore[method-assign]
        out = core.autonomous_command("start test visible start state")
        state = core.autonomous_status_data()
        assert "Autonomous mode started" in out
        assert state["enabled"] is True
        assert state["phase"] in {"starting", "observe", "plan", "act", "cycle_done", "cooldown"}
        assert state.get("last_progress_ts") is not None
        core.autonomous_command("stop")
