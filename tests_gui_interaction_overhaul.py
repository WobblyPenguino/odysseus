from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.creation_intent import analyze_creation_request
from winlocalassistant.deterministic_generation import deterministic_simple_project

ROOT = Path(__file__).resolve().parent


def test_interaction_overhaul_is_injected_into_webui_html():
    from winlocalassistant.webui import HTML

    assert "NovaInteractionOverhaul" in HTML
    assert "novaMicListenerStatus" in HTML
    assert "novaModelStatusMini" in HTML
    assert "novaAutonomousGuardOverlay" in HTML
    assert "novaCommandHelpOverlay" in HTML
    assert "msgNav" in HTML
    assert "novaCodeBox" in HTML
    assert "interaction overhaul v1" in HTML


def test_interaction_overhaul_static_contract_markers():
    src = (ROOT / "winlocalassistant" / "webui_interaction_overhaul.py").read_text(encoding="utf-8")
    assert "backdrop-filter:none" in src
    assert "bottom:calc(var(--nova-composer-safe)" in src
    assert "makeMovableResizable" in src
    assert "enhanceCodeBlocks" in src
    assert "renderSafeComponents" in src
    assert "updateAutonomousGuard" in src


def test_behavior_rules_commands_roundtrip(tmp_path, monkeypatch):
    from winlocalassistant import behavior_rules

    path = tmp_path / "rules.json"
    monkeypatch.setattr(behavior_rules, "RULES_PATH", path)
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    reply = core.handle_command("/remember-behavior When I ask for one file, only make one file")
    assert "Saved behaviour rule" in reply
    assert "one file" in core.handle_command("/behavior-rules")
    rid = behavior_rules.list_behavior_rules()["rules"][0]["id"]
    reply = core.handle_command(f"/forget-behavior {rid}")
    assert "Removed behaviour rule" in reply


def test_creation_intent_respects_one_file_script_scope():
    analysis = analyze_creation_request("make one file python script that bolds let")
    assert analysis["artifact_type"] == "automation_script"
    assert analysis["likely_files"] == ["script.py"]
    assert not any(p.endswith("html") for p in analysis["likely_files"])


def test_deterministic_fallback_for_simple_bold_script():
    analysis = analyze_creation_request("make a simple script that bolds let")
    data = deterministic_simple_project("make a simple script that bolds let", analysis)
    assert data is not None
    assert list(data["files"].keys()) == ["script.py"]
    assert "bold_word" in data["files"]["script.py"]
    assert data["source"] == "deterministic_fallback"


def test_ai_create_project_uses_one_file_fallback_when_model_unavailable(tmp_path, monkeypatch):
    from winlocalassistant.config import AssistantConfig
    from winlocalassistant.tools import ToolRegistry

    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    tools = ToolRegistry(cfg)
    monkeypatch.setattr(tools, "_ask_model_for_project", lambda *a, **k: None)
    monkeypatch.setattr(tools, "_repair_until_accepted", lambda *a, **k: (True, {"ok": True, "summary": "skipped for deterministic fallback unit test"}))
    result = tools.ai_create_project("make a simple script that bolds let", folder="bold-let", build_mode="fast")
    assert result.ok, result.summary
    project_root = Path(result.data["workspace"])
    assert (project_root / "script.py").exists()
    assert not (project_root / "index.html").exists()
    assert result.data["source"] == "deterministic_fallback"
