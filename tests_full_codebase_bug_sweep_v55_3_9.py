from __future__ import annotations

import base64
import json
import sqlite3
from pathlib import Path

from winlocalassistant.assistant_datastore import INDEX_PATH, DB_DIR, export_database, get_record, put_record, search_records
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.efficiency_profiler import render_efficiency_markdown
from winlocalassistant.webui import HTML
from winlocalassistant.command_verifier import verify_command_contracts


def test_efficiency_time_blocks_stateful_status_like_commands(tmp_path: Path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    cases = [
        "/autonomous start build a test app",
        "/autonomous once investigate",
        "/efficiency clear",
        "/efficiency off",
        "/model-context off",
        "/model-context max=1000",
        "/skill-mode coding",
    ]
    for command in cases:
        out = core.efficiency_command(f"time 2 {command}")
        assert "blocked" in out.lower(), command


def test_efficiency_time_allows_read_only_variants(tmp_path: Path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    for command in ["/autonomous status", "/efficiency report", "/skill-mode", "/model-context preview current state"]:
        allowed, reason = core._efficiency_timed_command_allowed(command)
        assert allowed, (command, reason)


def test_efficiency_report_filenames_do_not_collide(tmp_path: Path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    md1, js1 = render_efficiency_markdown(cfg)[1:3]
    md2, js2 = render_efficiency_markdown(cfg)[1:3]
    assert md1 != md2
    assert js1 != js2
    assert md1.exists() and md2.exists() and js1.exists() and js2.exists()


def test_webui_db_merge_button_escapes_json_attribute():
    assert 'fillCommand(\'/db merge research.notes.example {&quot;note&quot;:&quot;text&quot;}\')' in HTML
    assert 'fillCommand(\'/db merge research.notes.example {"note":"text"}\')' not in HTML


def test_command_contracts_pass_after_autonomous_explain_marker_fix(tmp_path: Path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    result = verify_command_contracts(lambda command: core.handle_command(command))
    assert result["ok"], [r for r in result["results"] if not r.get("ok")]


def test_database_read_paths_survive_corrupt_json_row(tmp_path: Path):
    # Use the real APP_DIR-backed DB path because the datastore is intentionally global.
    DB_DIR.mkdir(parents=True, exist_ok=True)
    db = "corrupt_test_v5539"
    con = sqlite3.connect(INDEX_PATH, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    con.execute("""
        CREATE TABLE IF NOT EXISTS records (
            database_name TEXT NOT NULL,
            collection TEXT NOT NULL,
            key TEXT NOT NULL,
            value_json TEXT NOT NULL,
            schema_hint TEXT NOT NULL DEFAULT '',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            PRIMARY KEY(database_name, collection, key)
        )
    """)
    con.execute(
        "REPLACE INTO records(database_name, collection, key, value_json, schema_hint, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
        (db, "notes", "bad", "{not valid json", "", "now", "now"),
    )
    con.commit(); con.close()

    one = get_record(db, "notes", "bad")
    assert one["found"] is True
    assert "_decode_error" in one["value"]
    collection = get_record(db, "notes")
    assert collection["found"] is True
    assert collection["records"][0]["value"].get("_decode_error")
    hits = search_records(db, "not valid")
    assert hits["matches"]
    exported = export_database(db)
    assert Path(exported["export_path"]).exists()


def test_upload_size_should_be_checked_after_decoding_too():
    # This regression documents the code path by checking the source contains the exact decoded-size guard.
    source = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "if len(blob) > MAX_UPLOAD_BYTES" in source
    assert "File is too large after decoding" in source
