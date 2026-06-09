from __future__ import annotations

import re
import time
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, read_json_file

RULES_PATH = APP_DIR / "behavior_rules.json"


def _load() -> dict[str, Any]:
    data = read_json_file(RULES_PATH, {"rules": []}, expected_type=dict, quarantine=True)
    if not isinstance(data, dict):
        data = {"rules": []}
    data.setdefault("rules", [])
    return data


def list_behavior_rules() -> dict[str, Any]:
    data = _load()
    return {"ok": True, "path": str(RULES_PATH), "rules": list(data.get("rules") or [])}


def add_behavior_rule(text: str, source: str = "manual") -> dict[str, Any]:
    rule = _sanitize_rule(text)
    if not rule:
        return {"ok": False, "error": "No usable behaviour rule text supplied."}
    data = _load()
    rules = [r for r in data.get("rules", []) if isinstance(r, dict)]
    rid = "rule_" + re.sub(r"[^a-z0-9]+", "_", rule.lower()).strip("_")[:36]
    existing = next((r for r in rules if r.get("id") == rid), None)
    row = {"id": rid, "rule": rule, "source": source, "created_at": time.strftime("%Y-%m-%d %H:%M:%S"), "enabled": True, "scope": _scope_for(rule)}
    if existing:
        existing.update(row)
    else:
        rules.append(row)
    atomic_write_json(RULES_PATH, {"rules": rules}, ensure_ascii=False)
    return {"ok": True, "rule": row, "path": str(RULES_PATH)}


def delete_behavior_rule(rule_id: str) -> dict[str, Any]:
    data = _load()
    before = list(data.get("rules") or [])
    after = [r for r in before if str(r.get("id")) != str(rule_id)]
    atomic_write_json(RULES_PATH, {"rules": after}, ensure_ascii=False)
    return {"ok": len(after) != len(before), "removed": len(before) - len(after), "path": str(RULES_PATH)}


def render_behavior_rules(payload: dict[str, Any]) -> str:
    lines = ["# Nova Behaviour Rules", "", f"Path: `{payload.get('path', RULES_PATH)}`", ""]
    rules = payload.get("rules") or []
    if not rules:
        lines += ["No saved behaviour rules yet.", "", "Add one with `/remember-behavior When I ask for one file, only make one file`."]
    else:
        for r in rules:
            state = "enabled" if r.get("enabled", True) else "disabled"
            lines.append(f"- `{r.get('id')}` ({state}, {r.get('scope','general')}): {r.get('rule')}")
    lines += ["", "Safety: rules are planning preferences only. They cannot bypass validation, permissions, or unsafe-action gates."]
    return "\n".join(lines)


def behavior_rule_context() -> str:
    rules = [r.get("rule", "") for r in (_load().get("rules") or []) if isinstance(r, dict) and r.get("enabled", True)]
    return "\n".join(f"- {r}" for r in rules if r)


def _sanitize_rule(text: str) -> str:
    text = re.sub(r"\s+", " ", (text or "").strip())
    if not text:
        return ""
    blocked = ["ignore safety", "bypass validation", "hide errors", "disable rollback", "steal", "malware"]
    if any(b in text.lower() for b in blocked):
        return ""
    return text[:300]


def _scope_for(rule: str) -> str:
    low = rule.lower()
    if any(x in low for x in ["one file", "script", "project", "scaffold", "template"]):
        return "generation_scope"
    if any(x in low for x in ["style", "tone", "format"]):
        return "response_style"
    return "general"
