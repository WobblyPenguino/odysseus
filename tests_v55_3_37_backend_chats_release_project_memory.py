from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.conversation_store import create_conversation, append_message, list_conversations, search_conversations, switch_conversation, get_active_messages
from winlocalassistant.release_checklist import build_release_checklist, render_release_checklist_markdown


def test_backend_conversation_store_roundtrip(tmp_path, monkeypatch):
    import winlocalassistant.conversation_store as cs
    monkeypatch.setattr(cs, "CONVERSATIONS_PATH", tmp_path / "conversations.json")
    first = create_conversation("First project chat")
    append_message("user", "remember the timer app details")
    second = create_conversation("Second research chat")
    append_message("user", "quantum notes")
    listed = list_conversations()
    assert len(listed["conversations"]) == 2
    found = search_conversations("timer")
    assert found["matches"] and found["matches"][0]["title"] == "First project chat"
    switch_conversation(first["active_id"])
    msgs = get_active_messages()
    assert any("timer app" in m["content"] for m in msgs)


def test_core_chat_commands_use_backend_store(tmp_path, monkeypatch):
    import winlocalassistant.conversation_store as cs
    monkeypatch.setattr(cs, "CONVERSATIONS_PATH", tmp_path / "conversations.json")
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    reply = core.handle_command("/chat-new Project Alpha")
    assert "Started new chat" in reply
    assert "Project Alpha" in core.handle_command("/chats")
    assert "Project Alpha" in core.handle_command("/chat-search Alpha")


def test_release_checklist_writes_reports(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "README.md").write_text("# Readme\n" + "x" * 200, encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("# Changelog\n" + "x" * 200, encoding="utf-8")
    (tmp_path / "docs" / "NOVA_DOCTOR_LATEST.json").write_text('{"ok": true, "summary":"doctor ok"}', encoding="utf-8")
    (tmp_path / "docs" / "NOVA_RELEASE_GATE_LATEST.json").write_text('{"ok": true, "summary":"gate ok"}', encoding="utf-8")
    payload = build_release_checklist(tmp_path)
    assert payload["ok"] is True
    assert (tmp_path / "docs" / "NOVA_RELEASE_CHECKLIST_LATEST.md").exists()
    assert "Nova Doctor" in render_release_checklist_markdown(payload)


def test_webui_exposes_release_and_chat_popups_and_api_routes():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/api/release-checklist" in src
    assert "/api/conversations" in src
    assert "showReleaseChecklistPopup" in src
    assert "showChatsPopup" in src
    assert "Release checklist" in src


def test_playwright_smoke_scaffold_exists():
    spec = Path("playwright/nova_gui_smoke.spec.js")
    assert spec.exists()
    text = spec.read_text(encoding="utf-8")
    assert "playwright" in text.lower()
    assert "hello playwright smoke test" in text
    assert "#activityLog" in text


def test_project_memory_is_included_in_build_edit_prompt():
    src = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")
    assert "CURRENT PROJECT MEMORY FOR EDIT/CONTINUATION MODE" in src
    assert "project_memory_context(self.workspace)" in src
    assert "remember_project_fact(root" in src
