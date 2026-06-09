from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_odysseus_suite import (
    build_fastapi_architecture_plan,
    build_gui_workbench_plan,
    build_odysseus_workspace_snapshot,
    build_suite_status,
    odysseus_dependency_status,
    odysseus_runtime_action,
    odysseus_workspace_action,
)


def test_fastapi_plan_recommends_hybrid_not_wholesale_rewrite(tmp_path: Path) -> None:
    payload = build_fastapi_architecture_plan(tmp_path)

    assert payload["recommendation"] == "hybrid_fastapi_sidecar"
    assert "FastAPI" in payload["decision"]
    assert any("copy Odysseus app.py wholesale" in item for item in payload["not_recommended"])
    assert any("NovaCore" in item for item in payload["keep"])
    assert payload["phases"][0]["risk"] == "low"


def test_core_routes_fastapi_and_gui_plans(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "docs").mkdir()
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))

    fastapi = core.handle_command("/nova-fastapi-plan")
    assert "Nova FastAPI Architecture Plan" in fastapi
    assert "hybrid_fastapi_sidecar" in fastapi
    assert "copy Odysseus app.py wholesale" in fastapi

    gui = core.handle_command("/nova-gui-workbench-plan")
    assert "Nova Odysseus GUI Workbench Plan" in gui
    assert "Left command rail" in gui
    assert "/nova-fastapi-plan" in gui


def test_gui_workbench_plan_detects_webui_markers() -> None:
    root = Path(__file__).resolve().parent
    payload = build_gui_workbench_plan(root)

    assert payload["webui_present"] is True
    assert payload["ui_markers"]["workbench_panel"] is True
    assert payload["ui_markers"]["rail_buttons"] is True
    assert payload["ui_markers"]["fastapi_plan_button"] is True
    assert payload["ui_markers"]["workspace_windows"] is True
    assert payload["ui_markers"]["code_tabs"] is True
    assert payload["ui_markers"]["json_workbench_actions"] is True
    assert payload["ui_markers"]["research_upload_windows"] is True
    assert payload["ui_markers"]["odysseus_deep_links"] is True
    assert payload["ui_markers"]["odysseus_runtime_launcher"] is True
    assert any(item["label"] == "Code" for item in payload["rail_items"])
    assert any(item["label"] == "Runtime" for item in payload["rail_items"])
    assert any(item["label"] == "Research" for item in payload["rail_items"])
    assert any(item["label"] == "Uploads" for item in payload["rail_items"])
    assert any(item["command"] == "/nova-fastapi-plan" for item in payload["rail_items"])


def test_webui_contains_odysseus_workbench_markers() -> None:
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")

    assert "id=\"odysseusWorkbenchPanel\"" in webui
    assert "class=\"odysseusWorkbenchBtn\"" in webui
    assert "data-odysseus-command" in webui
    assert "id=\"odysseusWorkspacePopup\"" in webui
    assert "function loadOdysseusWorkspace" in webui
    assert "function loadOdysseusRuntime" in webui
    assert "function runOdysseusRuntimeAction" in webui
    assert "function registerNovaServiceWorker" in webui
    assert "function renderCodeWorkbench" in webui
    assert "function submitOdysseusWorkbenchAction" in webui
    assert "data-workbench-action" in webui
    assert "/api/odysseus-workspace-action" in webui
    assert "/api/odysseus-runtime-action" in webui
    assert "/manifest.webmanifest" in webui
    assert "/service-worker.js" in webui
    assert "function openOdysseusDeepLink" in webui
    assert "/odysseus-runtime" in webui
    assert "/odysseus-research" in webui
    assert webui.count("function renderOdysseusWorkspaceBody") == 1
    assert "/nova-fastapi-plan" in webui
    assert "Hybrid sidecar" in webui


def test_odysseus_workspace_snapshot_lists_windows_and_code_tabs(tmp_path: Path) -> None:
    (tmp_path / "winlocalassistant").mkdir()
    (tmp_path / "winlocalassistant" / "demo.py").write_text("print('nova')\n", encoding="utf-8")

    payload = build_odysseus_workspace_snapshot(tmp_path)
    ids = {item["id"] for item in payload["windows"]}

    assert payload["ok"] is True
    assert {"docs", "runtime", "research", "uploads", "compare", "cookbook", "skills", "memory", "gates", "code"}.issubset(ids)
    assert payload["commands"]["docs"] == "/nova-docs list"
    assert payload["commands"]["runtime"] == "/nova-odysseus-runtime"
    assert payload["commands"]["research"] == "/research topic to investigate"
    assert payload["commands"]["uploads"] == "/context-files"
    assert any(item["path"] == "winlocalassistant/demo.py" for item in payload["code_files"])
    assert payload["odysseus_runtime"]["status"] in {"missing", "configured", "running"}


def test_odysseus_workspace_action_mutates_json_backed_windows(tmp_path: Path) -> None:
    doc = odysseus_workspace_action(tmp_path, {"surface": "docs", "action": "create", "payload": {"title": "Plan", "content": "# Plan"}})
    note = odysseus_workspace_action(tmp_path, {"surface": "notes", "action": "add", "payload": {"text": "remember this"}})
    task = odysseus_workspace_action(tmp_path, {"surface": "tasks", "action": "add", "payload": {"text": "verify workbench"}})
    done = odysseus_workspace_action(tmp_path, {"surface": "tasks", "action": "done", "payload": {"id": task["result"]["item"]["id"]}})
    skill = odysseus_workspace_action(tmp_path, {"surface": "skills", "action": "add", "payload": {"name": "tester", "text": "Run focused tests"}})
    preset = odysseus_workspace_action(tmp_path, {"surface": "presets", "action": "add", "payload": {"name": "careful", "text": "Be precise"}})
    gate = odysseus_workspace_action(tmp_path, {"surface": "gates", "action": "set", "payload": {"tool": "memory", "level": "block", "reason": "test gate"}})

    assert doc["ok"] is True
    assert note["ok"] is True
    assert done["result"]["item"]["done"] is True
    assert skill["snapshot"]["skills"]["tester"]["text"] == "Run focused tests"
    assert preset["snapshot"]["presets"]["careful"]["text"] == "Be precise"
    assert gate["snapshot"]["policy"]["policy"]["memory"]["level"] == "block"


def test_odysseus_workspace_action_requires_confirm_for_allow_gate(tmp_path: Path) -> None:
    blocked = odysseus_workspace_action(tmp_path, {"surface": "gates", "action": "set", "payload": {"tool": "memory", "level": "allow"}})
    allowed = odysseus_workspace_action(tmp_path, {"surface": "gates", "action": "set", "payload": {"tool": "memory", "level": "allow", "confirmed": True}})

    assert blocked["ok"] is False
    assert "confirmed=true" in blocked["summary"]
    assert allowed["ok"] is True


def test_odysseus_workspace_research_action_creates_report(tmp_path: Path) -> None:
    report = odysseus_workspace_action(tmp_path, {"surface": "research", "action": "run", "payload": {"topic": "Nova Odysseus GUI parity"}})
    blocked_url = odysseus_workspace_action(tmp_path, {"surface": "research", "action": "run", "payload": {"topic": "Nova", "urls": "https://example.com"}})

    assert report["ok"] is True
    assert report["result"]["topic"] == "Nova Odysseus GUI parity"
    assert report["result"]["path"].endswith(".md")
    assert any(item["id"] == "research" for item in report["snapshot"]["windows"])
    assert blocked_url["ok"] is False
    assert "confirmed=true" in blocked_url["summary"]


def test_odysseus_workspace_upload_clear_requires_confirmation(tmp_path: Path) -> None:
    blocked = odysseus_workspace_action(tmp_path, {"surface": "uploads", "action": "clear", "payload": {}})

    assert blocked["ok"] is False
    assert "confirmed=true" in blocked["summary"]


def test_odysseus_runtime_configure_and_start_requires_confirmation(tmp_path: Path) -> None:
    ody = tmp_path / "odysseus-main"
    ody.mkdir()
    (ody / "app.py").write_text("app = object()\n", encoding="utf-8")
    (ody / "setup.py").write_text("print('setup')\n", encoding="utf-8")

    missing = odysseus_dependency_status(tmp_path)
    configured = odysseus_runtime_action(tmp_path, {"action": "configure", "payload": {"path": str(ody), "mode": "native", "port": 7012}})
    blocked_start = odysseus_runtime_action(tmp_path, {"action": "start", "payload": {}})
    blocked_stop = odysseus_runtime_action(tmp_path, {"action": "stop", "payload": {}})

    assert missing["ok"] is True
    assert configured["ok"] is True
    assert configured["status"]["configured"] is True
    assert configured["status"]["port"] == 7012
    assert blocked_start["ok"] is False
    assert "confirmed=true" in blocked_start["error"]
    assert blocked_stop["ok"] is False
    assert "confirmed=true" in blocked_stop["error"]


def test_odysseus_workspace_runtime_surface_uses_same_launcher(tmp_path: Path) -> None:
    ody = tmp_path / "odysseus"
    ody.mkdir()
    (ody / "app.py").write_text("app = object()\n", encoding="utf-8")
    (ody / "requirements.txt").write_text("fastapi\n", encoding="utf-8")

    result = odysseus_workspace_action(tmp_path, {"surface": "runtime", "action": "configure", "payload": {"path": str(ody)}})

    assert result["ok"] is True
    assert result["snapshot"]["odysseus_runtime"]["configured"] is True
    assert any(item["id"] == "runtime" for item in result["snapshot"]["windows"])


def test_odysseus_suite_counts_new_architecture_and_gui_features(tmp_path: Path) -> None:
    payload = build_suite_status(tmp_path)
    ids = {feature["id"] for feature in payload["features"]}

    assert payload["coverage"]["covered"] == payload["coverage"]["total"]
    assert payload["coverage"]["total"] >= 16
    assert "fastapi_workspace_shell" in ids
    assert "gui_workbench_layout" in ids
    assert "optional_odysseus_runtime" in ids
    assert "/nova-fastapi-plan" in payload["primary_commands"]
    assert "/nova-gui-workbench-plan" in payload["primary_commands"]
    assert "/nova-odysseus-runtime" in payload["primary_commands"]
