from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.autonomy_capabilities import build_mutable_mission_plan, select_capabilities_for_goal
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_v55_3_72_metadata_mentions_autonomous_command_access_and_tools():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    for word in ["voice", "autonomous", "codebase"]:
        assert word in label


def test_capability_catalog_understands_new_major_command_families():
    plan = build_mutable_mission_plan("use idle and autonomous to build a notes app, run candidate tournament, repair bugs, remember regressions, and make its own custom tool if useful")
    names = {m.capability.name for m in plan.capabilities}
    assert "candidate_tournament" in names or "prompt_to_test" in names
    assert "custom_tool_extension" in names
    assert any("prompt" in item or "unrelated" in item for item in plan.validation_contract)


def test_autonomous_create_project_sequence_uses_contract_tournament_and_model_coach():
    seq = build_autonomous_tool_sequence("make a tiny useful notes app with localStorage and JSON export")
    tools = [s.tool for s in seq.steps]
    assert "prompt_contract" in tools
    assert "candidate_tournament" in tools
    assert "ai_create_project" in tools
    assert "prompt_test_run" in tools
    assert "model_output_coach" in tools


def test_autonomous_custom_tool_request_uses_guarded_tool_creator():
    seq = build_autonomous_tool_sequence("make its own custom tool to summarize TODO comments and run it when useful")
    tools = [s.tool for s in seq.steps]
    assert "custom_tools" in tools
    assert "tool_create" in tools
    assert "tool_clean_proposals" in tools
    assert seq.intent == "custom_tool_extension"


def test_tool_registry_exposes_new_autonomy_callable_tools(tmp_path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    for name in [
        "prompt_contract", "prompt_test_run", "candidate_tournament", "repair_plan_v2",
        "trace_status", "mcp_risk_report", "mission_create", "model_output_coach",
        "env_profile", "benchmark_system", "project_state", "regression_list"
    ]:
        assert name in app.tools.tools
        result = app.tools.call(name, goal="notes app with export") if name in {"prompt_contract", "prompt_test_run", "candidate_tournament", "model_output_coach", "mission_create"} else app.tools.call(name)
        assert result.ok or name in {"env_profile", "prompt_test_run"}
        assert result.summary


def test_command_routes_still_work_and_do_not_trigger_mega_test_gate(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    out = app.chat("/prompt-contract notes app with export")
    assert "Prompt Contract" in out
    assert "Mega Test" not in out
    out = app.chat("/candidate-tournament notes app with export")
    assert "Candidate Tournament" in out
    assert "Mega Test" not in out
