from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.autonomy_capabilities import build_mutable_mission_plan, get_capability_catalog
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.flow_audit import build_flow_audit, render_flow_audit
from winlocalassistant.tools import ToolRegistry


def test_version_and_label_mentions_flow_validation():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice" in label


def test_flow_audit_passes_for_current_command_tool_capability_surfaces(tmp_path: Path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    reg = ToolRegistry(cfg)
    payload = build_flow_audit(Path.cwd(), tool_names=sorted(reg.tools.keys()))
    assert payload["ok"] is True
    groups = {g["name"]: g for g in payload["groups"]}
    assert groups["build_and_validate"]["ok"] is True
    assert groups["tool_extension_and_sandboxing"]["ok"] is True
    assert not any(i["severity"] == "high" for i in payload["issues"])
    assert "Interaction Flow" in render_flow_audit(payload)


def test_core_routes_flow_commands(tmp_path: Path):
    app = AssistantCore(AssistantConfig(workspace=str(Path.cwd())))
    out = app.handle_command("/flow-audit")
    assert "Interaction Flow" in out
    assert "PASS" in out
    completed = app.handle_command("/flow-improvements")
    assert "Reports written" in completed


def test_tool_registry_exposes_flow_and_sandbox_dev_tools(tmp_path: Path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    for name in ["flow_audit", "interaction_flow_audit", "command_flow_verify", "learning_loop_audit", "flow_improvements", "sandbox_dev_run"]:
        assert name in reg.tools
    result = reg.call("flow_audit")
    assert result.ok is True
    assert "Interaction Flow" in result.data.get("message", "")


def test_autonomy_capability_catalog_selects_flow_validation():
    names = {cap.name for cap in get_capability_catalog()}
    assert "interaction_flow_validation" in names
    plan = build_mutable_mission_plan("ensure no regression across all commands and learn from mistakes")
    selected = [m.capability.name for m in plan.capabilities]
    assert "interaction_flow_validation" in selected
