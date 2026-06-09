from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.adaptive_backlog import build_adaptive_backlog, build_generation_template_manifest
from winlocalassistant.validation_matrix import build_validation_matrix
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def test_version_55_3_106_markers_are_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 113)
    assert f"v{__version__}" in VERSION_LABEL
    text = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert __version__ in text


def test_generation_template_manifest_recommends_game_template():
    payload = build_generation_template_manifest("make a dodge game about hair")
    assert payload["inferred_project_type"] == "html_css_js_game"
    recommended = [t for t in payload["templates"] if t["recommended"]]
    assert recommended and recommended[0]["kind"] == "html_css_js_game"
    assert "controls/collision/score/restart evidence" in recommended[0]["validation"]


def test_adaptive_backlog_is_grounded_in_current_codebase():
    root = Path.cwd()
    payload = build_adaptive_backlog(root, goal="improve Nova autonomous planning")
    assert payload["ok"] is True
    assert payload["proposals"]
    assert payload["implemented_markers"]["nova_context"] is True
    assert payload["implemented_markers"]["feature_continuity"] is True
    assert any(p["key"] == "validation_matrix_command" for p in payload["proposals"])


def test_validation_matrix_checks_behaviour_not_just_compile():
    payload = build_validation_matrix(Path.cwd(), goal="validate Nova behaviour")
    names = {c["name"] for c in payload["checks"]}
    assert {"python_compile", "webui_contract", "feature_continuity", "behaviour_evidence"}.issubset(names)
    assert payload["ok"], payload


def test_tool_registry_exposes_new_adaptive_tools(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    for name in ["adaptive_backlog", "validation_matrix", "generation_template_manifest"]:
        assert name in registry.tools
    backlog = registry.call("adaptive_backlog", goal="improve Nova")
    assert backlog.ok
    assert "Adaptive Improvement Backlog" in backlog.data.get("message", "")
    manifest = registry.call("generation_template_manifest", goal="make a game")
    assert manifest.ok
    assert manifest.data["inferred_project_type"] == "html_css_js_game"


def test_local_model_context_includes_template_manifest(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    text = registry._local_model_implementation_context(tmp_path, goal="make a game about hair", last_reason="game_missing_collision")
    assert "generation_template_manifest" in text
    assert "html_css_js_game" in text
    assert "deterministic" in text.lower()
