from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.core import AssistantCore
from winlocalassistant.assistant_datastore import put_record, get_record, search_records, delete_record, list_databases


def test_research_tool_requires_topic_without_crash(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    tools = ToolRegistry(cfg)
    result = tools.call("research", topic="")
    assert not result.ok
    assert "topic" in result.summary.lower()


def test_research_manual_url_disabled_still_attempts_only_given_sources(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_internet=False)
    tools = ToolRegistry(cfg)
    result = tools.call("research", topic="PFAS persistence", urls="")
    assert result.ok
    assert result.data["internet_allowed"] is False
    assert "Research report" in result.data["message"]


def test_assistant_database_put_get_search_delete(tmp_path):
    payload = put_record("testdb", "notes", "alpha", {"claim": "PFAS persists"}, schema_hint="test schema")
    assert payload["database"] == "testdb"
    got = get_record("testdb", "notes", "alpha")
    assert got["found"] is True
    assert got["value"]["claim"] == "PFAS persists"
    hits = search_records("testdb", "PFAS")
    assert hits["matches"]
    deleted = delete_record("testdb", "notes", "alpha")
    assert deleted["deleted"] >= 1


def test_core_db_command_and_research_usage(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    msg = core.handle_command("/research")
    assert "Usage: /research" in msg
    put_msg = core.handle_command('/db put mydb.notes.first {"text":"hello"}')
    assert "Assistant database" in put_msg
    get_msg = core.handle_command('/db get mydb.notes.first')
    assert "hello" in get_msg


def test_webui_contains_right_side_ai_presence_panel():
    text = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "AI state & communication" in text
    assert "id=\"aiPresenceBox\"" in text
    assert "id=\"assistantBoxPanel\"" in text
    right_idx = text.index('<aside class="rightbar card">')
    panel_idx = text.index('id="assistantBoxPanel"')
    assert panel_idx > right_idx
