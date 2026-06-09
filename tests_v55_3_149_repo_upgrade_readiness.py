from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.repo_upgrade_assurance import build_repo_upgrade_assurance
from winlocalassistant.tool_orchestrator import build_tool_awareness_plan
from winlocalassistant.tools import ToolRegistry


def test_command_verify_is_direct_toolregistry_tool(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    assert "command_verify" in registry.tools
    result = registry.call("command_verify")
    assert result.ok
    assert "Nova Command Verification" in result.data["message"]
    assert result.data["passed"] == result.data["total"]


def test_repo_upgrade_assurance_checks_all_repo_inspired_wiring(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    payload = build_repo_upgrade_assurance(registry._wla_source_root(), available_tools=registry.tools.keys())
    assert payload["ok"] is True
    names = {check["name"] for check in payload["checks"]}
    assert "tool_registry:repo_upgrade_surface" in names
    assert "command_routes:repo_upgrade_surface" in names
    assert "autonomous_idle:tool_plan_hooks" in names
    assert any(item["phase"] == "v55.3.150" for item in payload["future_timeline"])


def test_core_repo_upgrade_assurance_and_future_timeline_commands(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    text = core.handle_command("/repo-upgrade-assurance")
    assert "Nova Repo Upgrade Assurance" in text
    assert "Result: **PASS**" in text
    timeline = core.handle_command("/future-timeline")
    assert "v55.3.150" in timeline
    assert "Real browser click-through" in timeline


def test_tool_awareness_prefers_direct_command_verify_tool(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    plan = build_tool_awareness_plan(
        "show evidence and verify commands after a repo upgrade",
        mode="autonomous",
        available_tools=registry.tools.keys(),
    )
    assert any(decision.tool == "command_verify" for decision in plan.decisions)
    assert not plan.missing_tools


def test_autonomous_and_idle_plans_include_repo_readiness_validation(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    auto = registry.call("autonomous_tool_plan", goal="continue repo integrations and validate no regression", mode="autonomous")
    idle = registry.call("idle_tool_plan", goal="idle should notice broken repo integrations and propose fixes", mode="idle")
    assert auto.ok and idle.ok
    auto_tools = {decision["tool"] for decision in auto.data["decisions"]}
    idle_tools = {decision["tool"] for decision in idle.data["decisions"]}
    assert "pipeline_preflight" in auto_tools
    assert "tool_awareness" in idle_tools
    assert "command_verify" in auto_tools or "tool_awareness_audit" in auto_tools
