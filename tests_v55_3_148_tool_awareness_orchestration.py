from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.tool_orchestrator import build_tool_awareness_plan, audit_tool_awareness
from winlocalassistant.core import AssistantCore


def test_tool_awareness_plan_uses_pipeline_manifests_and_registry(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    plan = build_tool_awareness_plan(
        "continue implementing repo research ideas into Nova and ensure autonomous mode knows tools",
        mode="autonomous",
        available_tools=registry.tools.keys(),
    )
    assert plan.pipeline_kind == "repo_upgrade"
    assert "checkpointed_patch" in plan.manifest_ids or "coding_session_evidence" in plan.manifest_ids
    assert any(step.tool == "pipeline_preflight" for step in plan.decisions)
    assert any(step.tool in registry.tools for step in plan.decisions)
    assert plan.covered_tool_count >= 4


def test_idle_tool_plan_contains_safe_background_preflight(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    result = registry.call("idle_tool_plan", goal="idle should inspect logs and propose safe improvements", mode="idle")
    assert result.ok
    assert result.data["mode"] == "idle"
    assert "pipeline_kind" in result.data
    assert "Tool-Awareness" in result.data["message"]
    assert any(d["tool"] == "pipeline_preflight" for d in result.data["decisions"])


def test_tool_awareness_audit_samples_background_modes(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    payload = audit_tool_awareness(registry.tools.keys())
    assert payload["ok"] is True
    assert payload["available_tool_count"] > 50
    assert payload["covered_tools"]
    assert not payload["missing_tools"]


def test_core_commands_render_tool_awareness(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    text = core.handle_command("/autonomous-tool-plan continue integrating repo ideas and fixing errors")
    assert "Tool-Awareness" in text
    assert "repo_upgrade" in text
    audit = core.handle_command("/tool-awareness-audit")
    assert "Tool Awareness Audit" in audit


def test_background_modes_log_tool_awareness(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    # Do not run a full autonomous cycle here; verify the preflight command the cycle calls is registered and succeeds.
    auto = core.tools.call("autonomous_tool_plan", goal="autonomous mode should use all tools safely", mode="autonomous")
    idle = core.tools.call("idle_tool_plan", goal="idle mode should know when to use tools", mode="idle")
    assert auto.ok and idle.ok
    assert auto.data["mode"] == "autonomous"
    assert idle.data["mode"] == "idle"

def test_tool_awareness_uses_adaptive_remote_and_media_routes(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    remote = build_tool_awareness_plan(
        "set up remote phone laptop access with Tailscale and Wake-on-LAN",
        mode="manual",
        available_tools=registry.tools.keys(),
    )
    media = build_tool_awareness_plan(
        "make a 10 second video trailer and check ComfyUI ffmpeg",
        mode="manual",
        available_tools=registry.tools.keys(),
    )
    assert remote.pipeline_kind == "remote_access"
    assert any("remote" in d.tool for d in remote.decisions)
    assert media.pipeline_kind == "media"
    assert any(d.tool == "media_status" for d in media.decisions)
    assert any(d.tool == "image_plan" for d in media.decisions)

