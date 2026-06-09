from __future__ import annotations

import re
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, read_json_file

PROJECT_MEMORY_PATH = APP_DIR / "project_memory.json"
MAX_FACTS_PER_PROJECT = 80


def _load() -> dict[str, Any]:
    data = read_json_file(PROJECT_MEMORY_PATH, {}, expected_type=dict, quarantine=True)
    return data if isinstance(data, dict) else {}


def _save(data: dict[str, Any]) -> None:
    PROJECT_MEMORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(PROJECT_MEMORY_PATH, data, ensure_ascii=False)


def project_key(path: str | Path) -> str:
    try:
        return str(Path(path).expanduser().resolve())
    except Exception:
        return str(path)


def remember_project_fact(project_path: str | Path, fact: str, *, source: str = "user") -> dict[str, Any]:
    fact = re.sub(r"\s+", " ", str(fact or "")).strip()
    if not fact:
        return {"ok": False, "summary": "No project memory fact supplied"}
    key = project_key(project_path)
    data = _load()
    item = data.setdefault(key, {"project_path": key, "facts": []})
    facts = list(item.get("facts") or [])
    record = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": time.time(), "source": str(source or "user")[:80], "fact": fact[:1200]}
    if not any((f.get("fact") or "") == record["fact"] for f in facts):
        facts.append(record)
    item["facts"] = facts[-MAX_FACTS_PER_PROJECT:]
    item["updated_at"] = record["time"]
    data[key] = item
    _save(data)
    return {"ok": True, "summary": "Project memory saved", "project_path": key, "fact": record}


def list_project_memory(project_path: str | Path, *, limit: int = 20) -> dict[str, Any]:
    key = project_key(project_path)
    item = _load().get(key, {"project_path": key, "facts": []})
    facts = list(item.get("facts") or [])[-max(1, int(limit)):]
    return {"ok": True, "project_path": key, "facts": facts, "updated_at": item.get("updated_at", "")}


def search_project_memory(query: str, *, limit: int = 12) -> dict[str, Any]:
    terms = [t.lower() for t in re.findall(r"[A-Za-z0-9_\-]{3,}", str(query or ""))]
    rows: list[dict[str, Any]] = []
    for path, item in _load().items():
        for fact in item.get("facts") or []:
            text = (fact.get("fact") or "").lower()
            score = sum(1 for t in terms if t in text) if terms else 0
            if score or not terms:
                rows.append({"project_path": path, "score": score, **fact})
    rows.sort(key=lambda r: (-int(r.get("score") or 0), -float(r.get("ts") or 0)))
    return {"ok": True, "query": query, "matches": rows[:max(1, int(limit))]}


def project_memory_context(project_path: str | Path, *, limit: int = 8) -> str:
    facts = list_project_memory(project_path, limit=limit).get("facts", [])
    if not facts:
        return ""
    lines = ["\n\nProject memory for the current workspace:"]
    for f in facts[-limit:]:
        lines.append(f"- {f.get('fact','')}")
    return "\n".join(lines)
