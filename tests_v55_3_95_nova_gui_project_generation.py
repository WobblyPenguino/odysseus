from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.system_test import render_massive_system_test
from winlocalassistant.tools import ToolRegistry


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def test_version_and_nova_gui_controls_are_updated() -> None:
    from winlocalassistant import __version__
    assert __version__ in Path("winlocalassistant/__init__.py").read_text(encoding="utf-8")
    html = _webui()
    for needle in [
        "novaPersonality",
        "voiceStyle",
        "preferredSpeechVoice",
        "!avatarAudioActivated",
        "function toggleAudioMute",
        "function deleteSelectedRuns",
        "/api/activity-delete-runs",
        "/api/projects-delete",
        "Modified: ",
        "projectMeta",
        "settingsPanel",
    ]:
        assert needle in html


def test_file_creation_script_candidate_accepts_real_file_workflow(tmp_path: Path) -> None:
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    candidate = reg._fallback_file_creation_script_project("make an interesting script about file creation")
    ok, reason = reg._validate_model_project(candidate, "make an interesting script about file creation")
    assert ok, reason
    assert candidate["main_file"] == "file_creator.py"
    assert "write_text" in candidate["files"]["file_creator.py"]
    assert "generated_files" in candidate["files"]["file_creator.py"]


def test_file_creation_script_rejects_unrelated_john_doe_demo(tmp_path: Path) -> None:
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    candidate = {
        "files": {
            "index.html": "<form id='nameForm'><input id='nameInput'><div id='result'></div><script src='app.js'></script></form>",
            "app.js": "document.getElementById('nameForm').addEventListener('submit', e => { e.preventDefault(); const name=document.getElementById('nameInput').value; document.getElementById('result').textContent = name === 'John Doe' ? 'Success' : 'Failure'; });",
            "README.md": "file creation script " + ("generic unrelated verification demo " * 80),
        }
    }
    ok, reason = reg._validate_model_project(candidate, "make an interesting script about file creation")
    assert not ok
    assert "file_creation" in reason or "domain" in reason.lower() or "concept" in reason.lower()


def test_rejected_file_creation_candidate_uses_domain_fallback_without_loop(tmp_path: Path) -> None:
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    candidate = {
        "folder": "Filescript",
        "files": {
            "index.html": "<form id='nameForm'><input id='nameInput'><div id='result'></div><script src='app.js'></script></form>",
            "app.js": "document.getElementById('nameForm').addEventListener('submit', e => { e.preventDefault(); document.getElementById('result').textContent = 'Success: John Doe'; });",
        },
    }
    refined, trace, status = reg._refine_rejected_candidate(
        candidate,
        "make an interesting script about file creation",
        "model output did not contain enough user-requested concepts in actual code/UI files; matched [\"script\", \"file\"]",
        "long",
        max_rounds=2,
    )
    assert refined is not None
    assert status == "accepted_after_domain_fallback"
    assert refined["main_file"] == "file_creator.py"
    assert trace and trace[0]["stage"] == "deterministic_domain_fallback"


def test_create_rabbit_game_fallback_handles_string_validation_problems(tmp_path: Path, monkeypatch) -> None:
    import winlocalassistant.tools as tools_module

    monkeypatch.setattr(tools_module, "model_chat", lambda *args, **kwargs: None)
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    result = reg.ai_create_project("make a polished browser game about rabbits", build_mode="long")
    assert result.ok, result.data
    workspace = Path(result.data["workspace"])
    assert (workspace / "index.html").exists()
    assert (workspace / "app.js").exists()
    combined = (workspace / "index.html").read_text(encoding="utf-8", errors="replace").lower() + (workspace / "app.js").read_text(encoding="utf-8", errors="replace").lower()
    assert "rabbit" in combined or "bunny" in combined
    assert "static_acceptance" in str(result.data.get("verification", {}))


def test_delete_activity_runs_removes_selected_run_rows(tmp_path: Path, monkeypatch) -> None:
    import winlocalassistant.eventlog as eventlog

    activity = tmp_path / "activity.jsonl"
    model_io = tmp_path / "model_io.jsonl"
    rows = [
        {"run_id": "keep", "kind": "x"},
        {"run_id": "delete-me", "kind": "y"},
    ]
    activity.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    model_io.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    monkeypatch.setattr(eventlog, "ACTIVITY_PATH", activity)
    monkeypatch.setattr(eventlog, "MODEL_IO_PATH", model_io)
    result = eventlog.delete_activity_runs(["delete-me"])
    assert result["deleted"] == 2
    assert "delete-me" not in activity.read_text(encoding="utf-8")
    assert "delete-me" not in model_io.read_text(encoding="utf-8")
    assert "keep" in activity.read_text(encoding="utf-8")


def test_massive_system_test_renderer_keeps_chat_summary_short() -> None:
    payload = {
        "ok": False,
        "duration_sec": 1.2,
        "steps": [
            {"name": "pytest_group_1", "ok": False, "stdout": "x\n" * 200 + "AssertionError: boom\nFAILED test_example\n"},
        ],
        "markdown_path": "docs/NOVA_MASSIVE_SYSTEM_TEST_LATEST.md",
    }
    rendered = render_massive_system_test(payload)
    assert "Full stdout/stderr is saved" in rendered
    assert "Failure summary" in rendered
    assert len(rendered) < 1600
