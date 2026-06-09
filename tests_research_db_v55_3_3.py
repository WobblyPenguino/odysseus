
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.assistant_datastore import put_record, merge_record, get_record, database_schema, export_database


def test_db_merge_schema_and_export(tmp_path):
    put_record("v5533", "notes", "alpha", {"a": 1, "keep": True}, schema_hint="unit")
    merged = merge_record("v5533", "notes", "alpha", {"b": 2})
    assert merged["value"]["a"] == 1
    assert merged["value"]["b"] == 2
    schema = database_schema("v5533")
    assert schema["collections"]["notes"]["fields"]["a"] == ["int"]
    exported = export_database("v5533")
    assert exported["records"]
    assert exported["export_path"].endswith(".json")


def test_core_db_merge_schema_export_commands(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "Assistant database" in core.handle_command('/db put cdb.notes.item {"a":1}')
    assert "Assistant database" in core.handle_command('/db merge cdb.notes.item {"b":2}')
    got = core.handle_command('/db get cdb.notes.item')
    assert '"a": 1' in got and '"b": 2' in got
    assert "schema" in core.handle_command('/db schema cdb').lower()
    assert "export" in core.handle_command('/db export cdb').lower()


def test_research_payload_has_claim_map_and_db_index(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_internet=False)
    tools = ToolRegistry(cfg)
    result = tools.call("research", topic="testable research topic")
    assert result.ok
    msg = result.data["message"]
    assert "Claim/source map" in msg
    assert "Source scores" in msg
    core = AssistantCore(cfg)
    db_msg = core.handle_command('/db search research testable')
    assert "testable research topic" in db_msg


def test_webui_has_ai_memory_status_endpoint_and_panel():
    text = open('winlocalassistant/webui.py', encoding='utf-8').read()
    assert '/api/ai-memory-status' in text
    assert 'id="aiMemoryStatus"' in text
    assert 'loadAiMemoryStatus' in text
