from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.project_memory import remember_project_fact, list_project_memory, search_project_memory
from winlocalassistant.safe_io import atomic_write_text


def test_webui_has_audio_settings_rail_quick_editor_and_changelog():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "edgeRail" in html
    assert "toggleAudioMute" in html
    assert "speechSynthesis" in html
    assert "SpeechRecognition" in html
    assert "toggleVoiceInput" in html
    assert "voiceMode" in html
    assert "summariseForSpeech" in html
    assert "quickControlsGrouped" in html
    assert "addQuickCommandFromForm" in html
    assert "/api/changelog" in html
    assert "showChangelogPopup" in html


def test_webui_live_activity_is_resizable_and_more_informative():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "height:220px" in html
    assert "resize:vertical" in html
    assert "Decision context" in html
    assert "showHoverContext" in html
    assert "activityResizeHint" in html


def test_webui_file_cards_and_recent_llm_context_present():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "renderFileCards" in html
    assert "fileCards" in html
    assert "llmRecentContext" in html
    assert "loadRecentModelContext" in html


def test_project_memory_round_trip(tmp_path, monkeypatch):
    import winlocalassistant.project_memory as pm
    monkeypatch.setattr(pm, "PROJECT_MEMORY_PATH", tmp_path / "project_memory.json")
    project = tmp_path / "DemoProject"
    payload = remember_project_fact(project, "Uses localStorage for saved bugs", source="test")
    assert payload["ok"]
    listed = list_project_memory(project)
    assert listed["facts"][-1]["fact"] == "Uses localStorage for saved bugs"
    found = search_project_memory("localStorage bugs")
    assert found["matches"]


def test_core_project_memory_commands(tmp_path, monkeypatch):
    import winlocalassistant.project_memory as pm
    monkeypatch.setattr(pm, "PROJECT_MEMORY_PATH", tmp_path / "project_memory.json")
    cfg = AssistantConfig(workspace=str(tmp_path / "Proj"))
    core = AssistantCore(cfg)
    reply = core.handle_command("/remember-project main file is app.js")
    assert "Project memory saved" in reply
    reply = core.handle_command("/project-memory")
    assert "main file is app.js" in reply


def test_atomic_write_text_retries_has_permission_error_loop():
    src = Path("winlocalassistant/safe_io.py").read_text(encoding="utf-8")
    assert "except PermissionError" in src
    assert "for attempt in range(8)" in src
