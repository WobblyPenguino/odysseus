from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.next_feature_suite import (
    build_quality_report,
    build_browser_runtime_test,
    build_model_reliability,
    patch_queue_action,
    build_gui_cockpit_v2,
    list_templates,
    build_template_project,
    build_feature_readiness,
    explain_error,
    build_support_report,
    docs_index,
    regression_test_generate,
    learning_status,
)


def test_version_metadata_mentions_major_quality_suite():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    for word in ["voice", "codebase", "packaging"]:
        assert word in low


def test_quality_and_browser_runtime_detect_notes_app(tmp_path):
    (tmp_path / "index.html").write_text('<body><form id="noteForm"><input id="noteInput"><button>Add</button></form><ul id="notesList"></ul><button id="exportBtn">Export</button><script src="app.js"></script></body>', encoding="utf-8")
    (tmp_path / "app.js").write_text('const notes=[];localStorage.setItem("notes",JSON.stringify(notes));localStorage.getItem("notes");new Blob([JSON.stringify(notes)]);const a=document.createElement("a");a.download="notes.json";document.getElementById("noteForm");document.getElementById("exportBtn");', encoding="utf-8")
    (tmp_path / "README.md").write_text('Run by opening index.html. Includes localStorage and export.', encoding="utf-8")
    q = build_quality_report(tmp_path, "notes app with localStorage and JSON export")
    b = build_browser_runtime_test(tmp_path, "notes app with localStorage and JSON export")
    assert q["score"] >= 85
    assert b["ok"]


def test_new_feature_helpers_return_structured_payloads(tmp_path):
    assert isinstance(build_model_reliability(tmp_path), dict)
    assert patch_queue_action("propose", "test patch")["patches"]
    assert build_gui_cockpit_v2(tmp_path)["classic_preserved"] is True
    assert "notes-app" in list_templates()["templates"]
    assert "index.html" in build_template_project(tmp_path, "notes-app")["files"]
    assert build_feature_readiness(tmp_path)["features"]
    assert explain_error("TypeError: Failed to fetch")["next_steps"]
    assert build_support_report(tmp_path)["activity_tail"] is not None
    assert "matches" in docs_index(tmp_path)
    assert regression_test_generate(tmp_path, "panel stuck")["test_name"].endswith(".py")
    assert learning_status(tmp_path)["mistake_learning"] == "active"


def test_core_routes_and_tool_registry_expose_new_features(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    app = AssistantCore(cfg)
    for tool in ["build_quality_report", "browser_runtime_test", "model_reliability", "patch_queue", "feature_readiness", "support_report", "mistake_learning_status"]:
        assert tool in app.tools.tools
    commands = [
        "/build-quality-report notes app",
        "/browser-run-test notes app",
        "/model-reliability",
        "/patch-queue",
        "/gui-feature-coverage",
        "/voice-device-status",
        "/template-list",
        "/preview-status",
        "/feature-readiness",
        "/explain-error TypeError: Failed to fetch",
        "/support-report",
        "/index-nova Nova",
        "/regression-test-generate stuck panel",
        "/new-pc-benchmark",
        "/mistake-learning-status",
    ]
    for command in commands:
        text = app.handle_command(command)
        assert isinstance(text, str) and len(text) > 20, command
