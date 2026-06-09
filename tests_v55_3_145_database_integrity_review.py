from __future__ import annotations

from pathlib import Path

import winlocalassistant.assistant_datastore as datastore
from winlocalassistant.assistant_datastore import audit_database, compact_database, put_record, search_records
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.planner import make_plan
from winlocalassistant.project_state_db import MAX_STATE_ITEMS_PER_BUCKET, append_project_state, audit_project_state, load_project_state


def test_assistant_database_audit_reports_integrity_and_counts(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(datastore, "DB_DIR", tmp_path / "assistant_db")
    monkeypatch.setattr(datastore, "INDEX_PATH", tmp_path / "assistant_db" / "assistant_store.sqlite3")

    put_record("auditdb", "notes", "alpha", {"text": "hello", "n": 1}, schema_hint="unit")
    put_record("auditdb", "notes", "beta", {"text": "world"}, schema_hint="unit")

    payload = audit_database("auditdb")
    assert payload["ok"] is True
    assert payload["integrity_check"].lower() == "ok"
    assert payload["record_count"] == 2
    assert payload["per_database"]["auditdb"]["collections"]["notes"] == 2
    assert "No blocking database issues" in " ".join(payload["recommendations"])
    assert search_records("auditdb", "world")["matches"]


def test_assistant_database_compact_is_explicit_and_safe(monkeypatch, tmp_path: Path) -> None:
    monkeypatch.setattr(datastore, "DB_DIR", tmp_path / "assistant_db")
    monkeypatch.setattr(datastore, "INDEX_PATH", tmp_path / "assistant_db" / "assistant_store.sqlite3")
    put_record("compactdb", "notes", "alpha", {"text": "hello"})
    payload = compact_database()
    assert payload["ok"] is True
    assert payload["action"] == "compact"
    assert payload["after_bytes"] >= 0


def test_project_state_uses_quarantine_and_retention(tmp_path: Path) -> None:
    state_path = tmp_path / ".wla_project_state.json"
    state_path.write_text("not valid json", encoding="utf-8")
    state = load_project_state(tmp_path)
    assert state["validation_failures"]
    assert list(tmp_path.glob("*.corrupt_*.bak")) or list(tmp_path.glob("*.corrupt*.bak"))

    for i in range(MAX_STATE_ITEMS_PER_BUCKET + 5):
        append_project_state(tmp_path, "failure", {"i": i})
    state = load_project_state(tmp_path)
    assert len(state["validation_failures"]) <= MAX_STATE_ITEMS_PER_BUCKET
    audit = audit_project_state(tmp_path)
    assert audit["exists"] is True
    assert "validation_failures" in audit["counts"]


def test_database_review_request_routes_to_audits_not_project_generation() -> None:
    plan = make_plan("review the entire database look for areas that need improving or rewriting and make improvements ensure no regression")
    tools = [step.tool for step in plan.steps]
    assert plan.mode == "database_review"
    assert "assistant_db" in tools
    assert "project_state" in tools
    assert "bug_review" in tools
    assert "regression_sweep" in tools
    assert "ai_create_project" not in tools


def test_core_db_audit_and_review_route(tmp_path: Path) -> None:
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    out = core.handle_command('/db put c145.notes.item {"a":1}')
    assert "Assistant database" in out
    audit = core.handle_command("/db audit c145")
    assert "SQLite integrity" in audit
    compact_guard = core.handle_command("/db compact")
    assert "--confirm" in compact_guard
    dry_core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False))
    route = dry_core.chat("review the entire database look for areas that need improving or rewriting and make improvements ensure no regression")
    assert "concrete executable plan" in route
    assert dry_core.last_plan is not None
    assert dry_core.last_plan.mode == "database_review"
    assert "ai_create_project" not in route
