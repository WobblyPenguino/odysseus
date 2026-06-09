from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.feature_continuity import build_feature_continuity_audit, render_feature_continuity_audit
from winlocalassistant.tools import ToolRegistry


def test_version_55_3_102_markers_are_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 113)
    assert f"v{__version__}" in VERSION_LABEL
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert __version__ in src
    assert "Feature-continuity audit" in src


def test_feature_continuity_audit_catches_required_surfaces():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    payload = build_feature_continuity_audit(Path.cwd(), tool_names=sorted(registry.tools))
    assert payload["ok"], payload.get("failed")
    names = {check["name"] for check in payload["checks"]}
    assert "webui:project_panel" in names
    assert "webui:toolbox" in names
    assert "webui:live_activity_runs" in names
    assert "tool_registry:critical_commands" in names
    md = render_feature_continuity_audit(payload)
    assert "Nova Feature Continuity Audit" in md
    assert "Do not remove existing GUI/backend surfaces" in md


def test_feature_continuity_tool_is_registered_and_reports():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    assert "feature_continuity_audit" in registry.tools
    result = registry.call("feature_continuity_audit", path=".")
    assert result.ok, result.data
    assert result.data["target_resolution"]["target_type"] == "wla_source"
    assert "report" in result.data


def test_local_model_context_includes_preservation_contract():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    text = registry._local_model_implementation_context(Path.cwd(), goal="redesign the GUI and improve the game builder", last_reason="game_missing_collision")
    assert "feature_preservation_contract" in text
    assert "preserve" in text.lower()
    assert "collision" in text.lower()
    assert "verification_conditions" in text
