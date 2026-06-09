from __future__ import annotations

import json
import logging
import re
import sqlite3
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from .safe_io import atomic_write_json, unique_path
from .config import APP_DIR

DB_DIR = APP_DIR / "assistant_databases"
INDEX_PATH = DB_DIR / "assistant_store.sqlite3"

_NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")
MAX_RECORD_JSON_BYTES = 2_000_000
LARGE_RECORD_WARNING_BYTES = 1_000_000


def _safe_name(name: str, default: str = "default") -> str:
    name = (name or default).strip()
    if not _NAME_RE.match(name):
        raise ValueError("Names may contain only letters, numbers, underscore, dot and dash, max 64 chars.")
    return name


def _decode_value(value_json: str) -> Any:
    """Decode stored JSON without letting one corrupt row break DB commands."""
    try:
        return json.loads(value_json)
    except Exception as exc:
        return {"_decode_error": repr(exc), "raw_preview": str(value_json)[:1000]}


def _configure_connection(con: sqlite3.Connection) -> sqlite3.Connection:
    try:
        con.execute("PRAGMA journal_mode=WAL")
        con.execute("PRAGMA synchronous=NORMAL")
        con.execute("PRAGMA busy_timeout=30000")
        con.execute("PRAGMA foreign_keys=ON")
    except sqlite3.Error:
        # Older SQLite builds or read-only filesystems can reject some PRAGMAs.
        # The DB still works with the defaults, so keep startup resilient.
        logging.getLogger(__name__).debug("SQLite PRAGMA configuration was skipped", exc_info=True)
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
    con.execute("CREATE INDEX IF NOT EXISTS idx_records_db_collection ON records(database_name, collection)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_records_updated_at ON records(updated_at)")
    con.execute("CREATE INDEX IF NOT EXISTS idx_records_key ON records(key)")
    return con


@contextmanager
def _connection() -> Iterator[sqlite3.Connection]:
    """Open the assistant SQLite store and always close it.

    All database functions share this cleanup/rollback path so a failed query,
    corrupt row, or interrupted request does not leave the SQLite connection open.
    """
    DB_DIR.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(INDEX_PATH, timeout=30)
    try:
        yield _configure_connection(con)
        con.commit()
    except Exception:
        try:
            con.rollback()
        except sqlite3.Error:
            logging.getLogger(__name__).debug("SQLite rollback failed", exc_info=True)
        raise
    finally:
        con.close()


def _encode_value(value: Any) -> str:
    value_json = json.dumps(value, ensure_ascii=False, indent=2)
    if len(value_json.encode("utf-8")) > MAX_RECORD_JSON_BYTES:
        raise ValueError(f"Assistant database record is too large; limit is {MAX_RECORD_JSON_BYTES} bytes of JSON.")
    return value_json


def list_databases() -> dict[str, Any]:
    with _connection() as con:
        rows = con.execute(
            "SELECT database_name, collection, COUNT(*) FROM records GROUP BY database_name, collection ORDER BY database_name, collection"
        ).fetchall()
    dbs: dict[str, Any] = {}
    for db, col, count in rows:
        dbs.setdefault(db, {})[col] = int(count)
    return {"path": str(INDEX_PATH), "databases": dbs}


def put_record(database: str, collection: str, key: str, value: Any, schema_hint: str = "") -> dict[str, Any]:
    database = _safe_name(database)
    collection = _safe_name(collection, "notes")
    key = _safe_name(key, str(int(time.time())))
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    value_json = _encode_value(value)
    with _connection() as con:
        existing = con.execute(
            "SELECT created_at FROM records WHERE database_name=? AND collection=? AND key=?",
            (database, collection, key),
        ).fetchone()
        created_at = existing[0] if existing else now
        con.execute(
            "REPLACE INTO records(database_name, collection, key, value_json, schema_hint, created_at, updated_at) VALUES(?,?,?,?,?,?,?)",
            (database, collection, key, value_json, str(schema_hint or ""), created_at, now),
        )
    return {"database": database, "collection": collection, "key": key, "created_at": created_at, "updated_at": now, "value": value}


def get_record(database: str, collection: str, key: str = "") -> dict[str, Any]:
    database = _safe_name(database)
    collection = _safe_name(collection, "notes")
    with _connection() as con:
        if key:
            key = _safe_name(key)
            row = con.execute(
                "SELECT value_json, schema_hint, created_at, updated_at FROM records WHERE database_name=? AND collection=? AND key=?",
                (database, collection, key),
            ).fetchone()
            if not row:
                return {"found": False, "database": database, "collection": collection, "key": key}
            return {
                "found": True,
                "database": database,
                "collection": collection,
                "key": key,
                "value": _decode_value(row[0]),
                "schema_hint": row[1],
                "created_at": row[2],
                "updated_at": row[3],
            }
        rows = con.execute(
            "SELECT key, value_json, schema_hint, created_at, updated_at FROM records WHERE database_name=? AND collection=? ORDER BY updated_at DESC LIMIT 200",
            (database, collection),
        ).fetchall()
    return {
        "found": bool(rows),
        "database": database,
        "collection": collection,
        "records": [
            {"key": r[0], "value": _decode_value(r[1]), "schema_hint": r[2], "created_at": r[3], "updated_at": r[4]}
            for r in rows
        ],
    }


def search_records(database: str, query: str) -> dict[str, Any]:
    database = _safe_name(database)
    q = (query or "").lower()
    with _connection() as con:
        rows = con.execute(
            "SELECT collection, key, value_json, schema_hint, updated_at FROM records WHERE database_name=? ORDER BY updated_at DESC LIMIT 1000",
            (database,),
        ).fetchall()
    hits = []
    for col, key, value_json, hint, updated in rows:
        hay = (col + " " + key + " " + hint + " " + value_json).lower()
        if not q or q in hay:
            hits.append({"collection": col, "key": key, "value": _decode_value(value_json), "schema_hint": hint, "updated_at": updated})
        if len(hits) >= 100:
            break
    return {"database": database, "query": query, "matches": hits}


def delete_record(database: str, collection: str, key: str = "") -> dict[str, Any]:
    database = _safe_name(database)
    collection = _safe_name(collection, "notes")
    with _connection() as con:
        if key:
            key = _safe_name(key)
            cur = con.execute("DELETE FROM records WHERE database_name=? AND collection=? AND key=?", (database, collection, key))
        else:
            cur = con.execute("DELETE FROM records WHERE database_name=? AND collection=?", (database, collection))
        count = cur.rowcount
    return {"database": database, "collection": collection, "key": key, "deleted": int(count)}


def merge_record(database: str, collection: str, key: str, patch: Any, schema_hint: str = "") -> dict[str, Any]:
    """Merge a JSON object patch into an existing JSON object record, or replace if either side is non-object."""
    current = get_record(database, collection, key)
    if current.get("found") and isinstance(current.get("value"), dict) and isinstance(patch, dict):
        value = dict(current["value"])
        value.update(patch)
    else:
        value = patch
    stored = put_record(database, collection, key, value, schema_hint=schema_hint or current.get("schema_hint", ""))
    stored["merged"] = True
    return stored


def database_schema(database: str) -> dict[str, Any]:
    database = _safe_name(database)
    with _connection() as con:
        rows = con.execute(
            "SELECT collection, key, value_json, schema_hint, updated_at FROM records WHERE database_name=? ORDER BY collection, updated_at DESC LIMIT 1000",
            (database,),
        ).fetchall()
    collections: dict[str, Any] = {}
    for col, key, value_json, hint, updated in rows:
        val = _decode_value(value_json)
        info = collections.setdefault(col, {"records": 0, "schema_hints": set(), "fields": {}, "examples": []})
        info["records"] += 1
        if hint:
            info["schema_hints"].add(hint)
        if isinstance(val, dict):
            for k, v in val.items():
                typ = type(v).__name__
                info["fields"].setdefault(k, set()).add(typ)
        if len(info["examples"]) < 3:
            info["examples"].append({"key": key, "value": val, "updated_at": updated})
    for info in collections.values():
        info["schema_hints"] = sorted(info["schema_hints"])
        info["fields"] = {k: sorted(v) for k, v in info["fields"].items()}
    return {"database": database, "collections": collections, "path": str(INDEX_PATH)}


def export_database(database: str) -> dict[str, Any]:
    database = _safe_name(database)
    with _connection() as con:
        rows = con.execute(
            "SELECT collection, key, value_json, schema_hint, created_at, updated_at FROM records WHERE database_name=? ORDER BY collection, key",
            (database,),
        ).fetchall()
    payload = {"database": database, "exported_at": time.strftime("%Y-%m-%d %H:%M:%S"), "records": []}
    for col, key, value_json, hint, created, updated in rows:
        payload["records"].append({"collection": col, "key": key, "value": _decode_value(value_json), "schema_hint": hint, "created_at": created, "updated_at": updated})
    DB_DIR.mkdir(parents=True, exist_ok=True)
    path = unique_path(DB_DIR, f"{database}_export", ".json")
    atomic_write_json(path, payload, ensure_ascii=False)
    payload["export_path"] = str(path)
    return payload


def audit_database(database: str = "") -> dict[str, Any]:
    """Run a read-only integrity and hygiene review over assistant SQLite data.

    This is intentionally deterministic: it does not use the local LLM, does not
    mutate records, and reports concrete issues Nova can act on before a backup,
    export, or compaction step.
    """
    requested = (database or "").strip()
    database_filter = _safe_name(requested) if requested else ""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    with _connection() as con:
        integrity_row = con.execute("PRAGMA integrity_check").fetchone()
        integrity = str(integrity_row[0] if integrity_row else "unknown")
        if database_filter:
            rows = con.execute(
                "SELECT database_name, collection, key, value_json, schema_hint, created_at, updated_at FROM records WHERE database_name=? ORDER BY database_name, collection, key",
                (database_filter,),
            ).fetchall()
        else:
            rows = con.execute(
                "SELECT database_name, collection, key, value_json, schema_hint, created_at, updated_at FROM records ORDER BY database_name, collection, key"
            ).fetchall()
        page_count = int((con.execute("PRAGMA page_count").fetchone() or [0])[0] or 0)
        page_size = int((con.execute("PRAGMA page_size").fetchone() or [0])[0] or 0)
        wal_checkpoint = con.execute("PRAGMA wal_checkpoint(PASSIVE)").fetchone()

    per_database: dict[str, Any] = {}
    invalid_json: list[dict[str, Any]] = []
    large_records: list[dict[str, Any]] = []
    schema_hints_missing = 0
    newest = ""
    oldest = ""
    for db, col, key, value_json, hint, created, updated in rows:
        rec_bytes = len(str(value_json).encode("utf-8"))
        db_info = per_database.setdefault(db, {"records": 0, "collections": {}, "bytes": 0})
        db_info["records"] += 1
        db_info["collections"][col] = int(db_info["collections"].get(col, 0)) + 1
        db_info["bytes"] += rec_bytes
        if not hint:
            schema_hints_missing += 1
        try:
            json.loads(value_json)
        except Exception as exc:
            invalid_json.append({"database": db, "collection": col, "key": key, "error": repr(exc), "raw_preview": str(value_json)[:300]})
        if rec_bytes >= LARGE_RECORD_WARNING_BYTES:
            large_records.append({"database": db, "collection": col, "key": key, "bytes": rec_bytes})
        newest = max(newest, str(updated or "")) if newest else str(updated or "")
        oldest = min(oldest, str(created or "")) if oldest else str(created or "")

    recommendations: list[str] = []
    if integrity.lower() != "ok":
        recommendations.append("SQLite integrity_check is not OK; export readable records and inspect the database file before more writes.")
    if invalid_json:
        recommendations.append("Repair or delete records with invalid JSON so search/schema/export stay reliable.")
    if large_records:
        recommendations.append("Export or split very large records to keep the local assistant database responsive.")
    if rows and schema_hints_missing / max(1, len(rows)) > 0.5:
        recommendations.append("Add schema_hints to important records so /db schema is more informative.")
    if not recommendations:
        recommendations.append("No blocking database issues found. Keep using /db export before large cleanups or migrations.")

    size_bytes = INDEX_PATH.stat().st_size if INDEX_PATH.exists() else 0
    ok = integrity.lower() == "ok" and not invalid_json
    return {
        "ok": ok,
        "action": "audit",
        "path": str(INDEX_PATH),
        "database": database_filter or "all",
        "integrity_check": integrity,
        "record_count": len(rows),
        "database_count": len(per_database),
        "per_database": per_database,
        "invalid_json_count": len(invalid_json),
        "invalid_json": invalid_json[:25],
        "large_record_count": len(large_records),
        "large_records": sorted(large_records, key=lambda r: int(r.get("bytes") or 0), reverse=True)[:25],
        "schema_hints_missing": schema_hints_missing,
        "oldest_created_at": oldest,
        "newest_updated_at": newest,
        "sqlite_size_bytes": size_bytes,
        "sqlite_page_count": page_count,
        "sqlite_page_size": page_size,
        "wal_checkpoint_passive": list(wal_checkpoint) if wal_checkpoint is not None else [],
        "recommendations": recommendations,
    }


def compact_database() -> dict[str, Any]:
    """Checkpoint and vacuum the assistant SQLite file after the user confirms mutation."""
    DB_DIR.mkdir(parents=True, exist_ok=True)
    before = INDEX_PATH.stat().st_size if INDEX_PATH.exists() else 0
    con = sqlite3.connect(INDEX_PATH, timeout=30)
    try:
        _configure_connection(con)
        con.commit()
        checkpoint = con.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        con.commit()
        con.execute("VACUUM")
        con.commit()
    except Exception:
        try:
            con.rollback()
        except sqlite3.Error:
            logging.getLogger(__name__).debug("SQLite compact rollback failed", exc_info=True)
        raise
    finally:
        con.close()
    after = INDEX_PATH.stat().st_size if INDEX_PATH.exists() else 0
    return {
        "ok": True,
        "action": "compact",
        "path": str(INDEX_PATH),
        "before_bytes": before,
        "after_bytes": after,
        "saved_bytes": max(0, before - after),
        "wal_checkpoint_truncate": list(checkpoint) if checkpoint is not None else [],
    }


def render_db_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Assistant database result", "", f"Store path: `{INDEX_PATH}`", ""]
    if payload.get("action") == "audit":
        ok = "PASS" if payload.get("ok") else "ATTENTION"
        lines += [
            f"Status: **{ok}**",
            f"SQLite integrity: `{payload.get('integrity_check')}`",
            f"Database scope: `{payload.get('database', 'all')}`",
            f"Records checked: **{payload.get('record_count', 0)}** across **{payload.get('database_count', 0)}** database(s)",
            f"Invalid JSON rows: **{payload.get('invalid_json_count', 0)}**",
            f"Large records: **{payload.get('large_record_count', 0)}**",
            f"SQLite file size: **{payload.get('sqlite_size_bytes', 0)} bytes**",
            "",
            "## Collections",
        ]
        per_database = payload.get("per_database") or {}
        if not per_database:
            lines.append("No assistant database records yet.")
        for db, info in per_database.items():
            lines.append(f"- `{db}`: {info.get('records', 0)} records, {info.get('bytes', 0)} bytes")
            for col, count in sorted((info.get("collections") or {}).items()):
                lines.append(f"  - `{col}`: {count}")
        if payload.get("invalid_json"):
            lines += ["", "## Invalid JSON examples"]
            for item in payload.get("invalid_json", [])[:8]:
                lines.append(f"- `{item.get('database')}.{item.get('collection')}.{item.get('key')}`: {item.get('error')}")
        if payload.get("large_records"):
            lines += ["", "## Large record examples"]
            for item in payload.get("large_records", [])[:8]:
                lines.append(f"- `{item.get('database')}.{item.get('collection')}.{item.get('key')}`: {item.get('bytes')} bytes")
        lines += ["", "## Recommendations"]
        lines.extend(f"- {rec}" for rec in payload.get("recommendations", []))
        return "\n".join(lines)
    if payload.get("action") == "compact":
        lines += [
            "## Compact result",
            f"Before: **{payload.get('before_bytes', 0)} bytes**",
            f"After: **{payload.get('after_bytes', 0)} bytes**",
            f"Saved: **{payload.get('saved_bytes', 0)} bytes**",
        ]
        return "\n".join(lines)
    if "databases" in payload:
        if not payload["databases"]:
            lines.append("No assistant databases yet.")
        for db, cols in payload["databases"].items():
            lines.append(f"## {db}")
            for col, count in cols.items():
                lines.append(f"- `{col}`: {count} records")
        return "\n".join(lines)
    lines.append("```json")
    lines.append(json.dumps(payload, indent=2, ensure_ascii=False)[:12000])
    lines.append("```")
    return "\n".join(lines)
