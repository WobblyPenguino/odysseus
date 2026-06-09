from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from winlocalassistant.assistant_datastore import MAX_RECORD_JSON_BYTES, get_record, put_record
import winlocalassistant.assistant_datastore as datastore
from winlocalassistant.config import AssistantConfig
from winlocalassistant.research_engine import build_research_report


def test_assistant_database_rejects_oversized_records_without_corrupting_existing(monkeypatch) -> None:
    with tempfile.TemporaryDirectory(prefix="wla_db_limit_") as tmp:
        db_path = Path(tmp) / "assistant_store.sqlite3"
        monkeypatch.setattr(datastore, "DB_DIR", Path(tmp))
        monkeypatch.setattr(datastore, "INDEX_PATH", db_path)
        monkeypatch.setattr(datastore, "MAX_RECORD_JSON_BYTES", 80)

        put_record("self", "notes", "small", {"text": "ok"})
        with pytest.raises(ValueError):
            put_record("self", "notes", "huge", {"text": "x" * 500})

        assert get_record("self", "notes", "small")["value"] == {"text": "ok"}
        assert get_record("self", "notes", "huge")["found"] is False


def test_research_rejects_duplicate_and_unsafe_source_urls(monkeypatch, tmp_path: Path) -> None:
    import winlocalassistant.research_engine as research_engine

    monkeypatch.setattr(research_engine, "RESEARCH_DIR", tmp_path / "research")
    fetched: list[str] = []

    def fake_fetch(url: str, max_chars: int = 16000) -> tuple[str, str]:
        fetched.append(url)
        return "Example source", "This source provides evidence and data about PFAS persistence because the carbon fluorine bond is very stable."

    monkeypatch.setattr(research_engine, "_fetch_url", fake_fetch)
    cfg = AssistantConfig(allow_internet=True)
    _md, _json, payload = build_research_report(
        cfg,
        "PFAS persistence",
        source_urls=[
            "https://example.com/report,",
            "https://example.com/report",
            "http://localhost:8000/private",
            "file:///etc/passwd",
            "https://EXAMPLE.com/report#fragment",
        ],
        max_sources=8,
    )

    assert fetched == ["https://example.com/report"]
    assert payload["accepted_source_count"] == 1
    assert payload["requested_source_count"] == 5
    assert any("Blocked local/private" in err["reason"] for err in payload["rejected_sources"])
    assert any("Only absolute http/https" in err["reason"] for err in payload["rejected_sources"])
    assert payload["sources"][0]["domain"] == "example.com"
