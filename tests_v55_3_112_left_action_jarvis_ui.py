from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.feature_continuity import build_feature_continuity_audit
from winlocalassistant.validation_matrix import build_validation_matrix
from winlocalassistant.jarvis_bridge import (
    build_bridge_receipts,
    build_jarvis_test_prompts,
    build_safe_browser_harness,
    build_sidecar_enrollment_checklist,
)


def _root() -> Path:
    return Path(__file__).resolve().parent


def _webui() -> str:
    return (_root() / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")


def test_gui_moves_commands_left_and_right_is_transparent_output():
    src = _webui()
    assert "leftActionDock" in src
    assert "leftFileDock" in src
    assert "transparentOutputPanel" in src
    assert "transparentDiffPanel" in src
    assert "Bridge receipts" in src
    assert "Action dock" in src or "Build / repair" in src
    assert "renderTransparentOutputEvidence" in src


def test_right_inspector_tabs_are_state_output_bridge_editor():
    src = _webui()
    assert "data-tab=\"state\"" in src
    assert "data-tab=\"output\"" in src
    assert "data-tab=\"bridge\"" in src
    assert "data-tab=\"editor\"" in src
    assert "data-tab=\"files\"" not in src


def test_jarvis_harness_tools_are_registered():
    reg = ToolRegistry(AssistantConfig(workspace=str(_root())))
    for name in ["bridge_receipts", "sidecar_enrollment", "browser_harness", "jarvis_test_prompts"]:
        assert name in reg.tools


def test_sidecar_enrollment_and_browser_harness_are_policy_first():
    checklist = build_sidecar_enrollment_checklist("terminal filesystem browser screenshot")
    assert checklist["ok"] is True
    assert any(step["id"] == "receipt" for step in checklist["steps"])
    harness = build_safe_browser_harness("http://127.0.0.1:3142")
    assert harness["ok"] is True
    assert "Playwright" in " ".join(harness["steps"])
    blocked = build_safe_browser_harness("https://example.com")
    assert blocked["ok"] is False
    assert blocked["blockers"]


def test_bridge_receipts_and_test_prompts_render_safe_paths():
    receipts = build_bridge_receipts(limit=5)
    assert "actions" in receipts
    prompts = build_jarvis_test_prompts()
    names = [p["prompt"] for p in prompts["prompts"]]
    assert "/jarvis-status" in names
    assert "/bridge-receipts" in names
    assert "/browser-harness http://127.0.0.1:3142" in names


def test_continuity_and_validation_matrix_include_v112_markers():
    reg = ToolRegistry(AssistantConfig(workspace=str(_root())))
    cont = build_feature_continuity_audit(_root(), tool_names=sorted(reg.tools))
    assert cont["ok"], cont.get("failed")
    check_names = {c["name"] for c in cont["checks"]}
    assert "webui:left_action_cockpit" in check_names
    assert "webui:transparent_output" in check_names
    assert "webui:jarvis_ui_harness" in check_names
    matrix = build_validation_matrix(_root(), goal="jarvis bridge transparent output validation")
    assert matrix["ok"], matrix.get("failed")
