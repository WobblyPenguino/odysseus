from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.autonomy_idle_intelligence import (
    build_mission_dashboard,
    build_tool_choice_trace,
    repeated_signature,
    clear_repetition_memory,
    set_background_setting,
    load_background_settings,
    autonomous_last_report,
)
from winlocalassistant.autonomy_capabilities import build_mutable_mission_plan
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_version_bumped_for_autonomous_idle_intelligence():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    for word in ["voice", "autonomous", "codebase"]:
        assert word in label


def test_mission_dashboard_and_tool_trace_are_actionable():
    payload = build_mission_dashboard("make autonomous actually do useful build tasks")
    assert payload["progress_score"]["score"] >= 0
    assert payload["tool_choice_trace"]["choices"]
    trace = build_tool_choice_trace("fix a broken notes app")
    commands = [c["command"] for c in trace["choices"]]
    assert "/repair-diagnose" in commands or "/trace-errors" in commands


def test_background_idle_settings_and_repetition_guard():
    settings = set_background_setting("idle_background_only", True)
    assert settings["idle_background_only"] is True
    assert load_background_settings()["idle_background_only"] is True
    cleared = clear_repetition_memory()
    assert cleared["cleared"] is True
    status = repeated_signature([])
    assert status["repeated"] is False


def test_capability_catalog_knows_new_idle_autonomous_tools():
    plan = build_mutable_mission_plan("make autonomous less useless by scoring progress and avoiding repeats")
    names = {m.capability.name for m in plan.capabilities}
    assert "mission_intelligence" in names or "cycle_progress_scoring" in names
    assert "repetition_guard" in names


def test_tool_registry_exposes_autonomy_idle_intelligence_tools(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    tools = ToolRegistry(cfg)
    for name in ["mission_dashboard", "cycle_score", "tool_choice_trace", "repetition_guard_status", "idle_background_settings", "autonomous_last_report"]:
        assert name in tools.tools
    result = tools.call("tool_choice_trace", goal="build an app and validate it")
    assert result.ok
    assert "/prompt-contract" in result.data["message"]


def test_core_commands_route_to_new_reports(tmp_path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "Mission" in app.handle_command("/mission-dashboard improve autonomous")
    assert "Tool Choice" in app.handle_command("/tool-choice-trace build app")
    assert "Repetition" in app.handle_command("/repetition-guard-status")
    assert "Progress" in app.handle_command("/cycle-score")
    assert "Autonomous Last Detailed Report" in app.handle_command("/autonomous-last-report")
