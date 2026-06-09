from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.conversation_store import create_conversation, rename_conversation, delete_conversation, list_conversations
from winlocalassistant.security_watch import run_security_watch
from winlocalassistant.wla_doctor import run_wla_release_gate


def test_backend_conversations_can_be_renamed_and_deleted(tmp_path, monkeypatch):
    import winlocalassistant.conversation_store as cs
    store = tmp_path / "conversations.json"
    monkeypatch.setattr(cs, "CONVERSATIONS_PATH", store)
    created = create_conversation("Original title", make_active=True)
    cid = created["active_id"]
    renamed = rename_conversation(cid, "Better title")
    assert renamed["ok"] is True
    assert renamed["conversation"]["title"] == "Better title"
    deleted = delete_conversation(cid)
    assert deleted["ok"] is True
    rows = list_conversations()["conversations"]
    assert all(r["id"] != cid for r in rows)


def test_core_chat_rename_delete_commands(tmp_path, monkeypatch):
    import winlocalassistant.conversation_store as cs
    monkeypatch.setattr(cs, "CONVERSATIONS_PATH", tmp_path / "conversations.json")
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    msg = core.handle_command("/chat-new Testing chat")
    cid = msg.split("ID:", 1)[1].splitlines()[0].strip()
    assert "Renamed chat" in core.handle_command(f"/chat-rename {cid} => Renamed chat")
    assert "Deleted chat" in core.handle_command(f"/chat-delete {cid}")


def test_security_watch_is_defensive_only(tmp_path, monkeypatch):
    import winlocalassistant.security_watch as sw
    monkeypatch.setattr(sw, "WATCH_DIR", tmp_path)
    monkeypatch.setattr(sw, "WATCH_STATE", tmp_path / "state.json")
    monkeypatch.setattr(sw, "WATCH_MD", tmp_path / "watch.md")
    monkeypatch.setattr(sw, "WATCH_JSON", tmp_path / "watch.json")
    payload = run_security_watch()
    assert payload["ok"] is True
    assert payload["defensive_only"] is True
    assert "offensive" not in " ".join(payload.get("recommendations", [])).lower()


def test_release_gate_records_playwright_skip_without_failing(tmp_path):
    root = Path.cwd()
    payload = run_wla_release_gate(root, "playwright optional check", "python -m pytest -q tests_release_hygiene.py tests_report_hygiene.py")
    names = {c.get("name"): c for c in payload.get("commands", [])}
    assert "playwright_smoke" in names
    assert names["playwright_smoke"].get("ok") is True


def test_project_target_and_image_setup_commands(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    target = core.handle_command("/project-target make a tiny useful app")
    assert "Project targeting diagnostic" in target
    assert "Decision:" in target
    image = core.handle_command("/image-setup-help")
    assert "Image generation status" in image
    assert "Stable Diffusion" in image or "Diffusers" in image


def test_webui_has_chat_management_and_release_gate_wiring():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "deleteChatFromPopup" in src
    assert "/api/conversation-delete" in src
    assert "/chat-rename" in src
    assert "playwright" in Path("winlocalassistant/wla_doctor.py").read_text(encoding="utf-8")
