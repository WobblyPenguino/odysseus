from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.blueprint_engine import build_project_blueprint, build_candidate_set, score_candidate
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.gui_redesign import build_gui_feature_map, gui_regression_check
from winlocalassistant.mcp_export import build_mcp_manifest
from winlocalassistant.trace_cockpit import build_trace
from winlocalassistant.visual_regression import build_gui_snapshot_status
from winlocalassistant.wla_mega_test import run_wla_mega_test


def test_version_55_3_63_metadata_preserves_release_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    label = VERSION_LABEL.lower()
    for word in ["wake", "voice", "codebase"]:
        assert word in label


def test_blueprint_for_notes_export_blocks_dodge_default():
    bp = build_project_blueprint("make a tiny useful local notes app with localStorage and JSON export")
    assert "localStorage persistence" in bp["must_have"]
    assert "JSON export" in bp["must_have"]
    assert "Dodge Game" in bp["must_not_have"]
    assert bp["artifact_type"] == "html_css_js_app"


def test_candidate_score_catches_missing_and_forbidden_content():
    score = score_candidate("notes app with localStorage and JSON export", text="Dodge Game score controls")
    assert not score["passed"]
    assert score["forbidden_hits"]
    good = score_candidate("notes app with localStorage and JSON export", text="localStorage JSON Blob download add notes delete notes list saved notes")
    assert good["overall_percent"] >= 75


def test_candidate_build_returns_multiple_variants():
    payload = build_candidate_set("notes app with localStorage and JSON export")
    assert len(payload["candidates"]) >= 3
    assert payload["recommended"] in {c["name"] for c in payload["candidates"]}


def test_gui_feature_map_and_regression_cover_classic_features():
    fmap = build_gui_feature_map(Path.cwd())
    assert fmap["ok"]
    assert any(f["name"] == "Live Activity" and f["ok"] for f in fmap["features"])
    assert gui_regression_check(Path.cwd())["ok"]


def test_mcp_manifest_exports_internal_tools():
    app = AssistantCore(AssistantConfig())
    manifest = build_mcp_manifest(app=app, root=Path.cwd())
    assert manifest["tools"]
    assert any(t["name"] == "wla_doctor" for t in manifest["tools"])
    assert "no arbitrary remote tool execution" in manifest["security"]


def test_trace_and_visual_status_are_available():
    assert "events" in build_trace(limit=5)
    status = build_gui_snapshot_status(Path.cwd())
    assert "command" in status and "playwright" in status["command"]


def test_core_new_commands_return_expected_sections():
    app = AssistantCore(AssistantConfig())
    assert "Project Blueprint" in app.handle_command("/blueprint notes app with export")
    assert "Candidate Build Plan" in app.handle_command("/candidate-build notes app with export")
    assert "Agent Trace Cockpit" in app.handle_command("/trace-last")
    assert "GUI Feature Map" in app.handle_command("/gui-feature-map")
    assert "MCP-style" in app.handle_command("/mcp-status")
    assert "GUI Visual Regression" in app.handle_command("/gui-visual-test")


def test_wla_mega_test_runs_and_writes_report():
    app = AssistantCore(AssistantConfig())
    payload = run_wla_mega_test(Path.cwd(), app=app)
    assert payload["total"] >= 10
    assert payload["passed"] >= 9
    assert Path(payload["report_path"]).exists()
