from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.core import AssistantCore


def test_assistant_box_tool_write_append_clear(tmp_path, monkeypatch):
    import winlocalassistant.assistant_box as ab

    monkeypatch.setattr(ab, "BOX_PATH", tmp_path / "assistant_message_box.json")
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    tools = ToolRegistry(cfg)

    written = tools.call("assistant_box", action="write", message="First message", source="test", level="warning")
    assert written.ok
    assert written.data["box"]["message"] == "First message"
    assert written.data["box"]["level"] == "warning"

    appended = tools.call("assistant_box", action="append", message="Second message", source="test")
    assert appended.ok
    assert "First message" in appended.data["box"]["message"]
    assert "Second message" in appended.data["box"]["message"]

    cleared = tools.call("assistant_box", action="clear")
    assert cleared.ok
    assert cleared.data["box"]["message"] == ""


def test_comm_box_command_uses_tool(tmp_path, monkeypatch):
    import winlocalassistant.assistant_box as ab

    monkeypatch.setattr(ab, "BOX_PATH", tmp_path / "assistant_message_box.json")
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    core = AssistantCore(cfg)

    reply = core.chat("/comm-box Hello from command")
    assert "Assistant communication box updated" in reply
    state = ab.read_assistant_box()
    assert state["message"] == "Hello from command"


def test_webui_contains_assistant_box_elements():
    text = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "assistantBoxPanel" in text
    assert "/api/assistant-box" in text
    assert "loadAssistantBox" in text
    assert "Nova communication box" in text
    assert "live_snapshot" in text


def test_core_live_snapshot_has_expected_sections(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False))
    snap = core.assistant_live_snapshot_data()
    assert snap["assistant_name"] == "Nova"
    assert "llm" in snap
    assert "idle" in snap
    assert "recent_events" in snap
    assert "file_focus" in snap
    assert "persisted_note" in snap
