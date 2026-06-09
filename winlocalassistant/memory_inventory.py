from __future__ import annotations

from pathlib import Path
from typing import Any

from .config import APP_DIR
from .assistant_datastore import list_databases, audit_database
from .project_state_db import audit_project_state


def build_memory_inventory(workspace: Path) -> dict[str, Any]:
    workspace = Path(workspace).resolve()
    db_listing = list_databases()
    dbs = db_listing.get("databases", {}) if isinstance(db_listing, dict) else {}
    audits: dict[str, Any] = {}
    for db_name in list(dbs.keys())[:12]:
        try:
            audits[db_name] = audit_database(db_name)
        except Exception as exc:
            audits[db_name] = {"ok": False, "error": repr(exc)}
    project_audit = audit_project_state(workspace)
    app_files = []
    for name in ["memory.json", "regressions.json", "autonomous_failure_memory.json", "idle_policy.json"]:
        path = APP_DIR / name
        app_files.append({"name": name, "path": str(path), "exists": path.exists(), "size_bytes": path.stat().st_size if path.exists() else 0})
    recommendations = []
    if not dbs:
        recommendations.append("Assistant SQLite store is empty or unused; no compaction needed.")
    if any((f.get("size_bytes") or 0) > 1_000_000 for f in app_files):
        recommendations.append("One or more JSON memory files is large; inspect or export before pruning.")
    if project_audit.get("warnings"):
        recommendations.append("Project state has warnings; review /project-state audit before more edits.")
    if not recommendations:
        recommendations.append("Memory stores look bounded; keep using typed records and explicit audit/compact commands.")
    return {
        "workspace": str(workspace),
        "assistant_db_path": db_listing.get("path") if isinstance(db_listing, dict) else "",
        "databases": dbs,
        "database_audits": audits,
        "project_state_audit": project_audit,
        "app_memory_files": app_files,
        "recommendations": recommendations,
    }


def render_memory_inventory(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Memory Inventory",
        "",
        f"Workspace: `{payload.get('workspace','')}`",
        f"Assistant DB: `{payload.get('assistant_db_path','')}`",
        "",
        "## Assistant databases",
    ]
    dbs = payload.get("databases") or {}
    if dbs:
        for db, cols in dbs.items():
            total = sum(int(v) for v in cols.values()) if isinstance(cols, dict) else 0
            lines.append(f"- `{db}`: {total} record(s) across {len(cols) if isinstance(cols, dict) else 0} collection(s)")
    else:
        lines.append("- No assistant DB records found.")
    lines += ["", "## Project state audit"]
    p = payload.get("project_state_audit") or {}
    lines.append(f"- Path: `{p.get('path','')}`")
    lines.append(f"- OK: {p.get('ok', True)}")
    for warning in p.get("warnings", [])[:8]:
        lines.append(f"- Warning: {warning}")
    lines += ["", "## App memory files"]
    for item in payload.get("app_memory_files") or []:
        lines.append(f"- `{item.get('name')}`: {'present' if item.get('exists') else 'missing'}, {item.get('size_bytes', 0)} bytes")
    lines += ["", "## Recommendations"] + [f"- {x}" for x in payload.get("recommendations", [])]
    return "\n".join(lines)
