from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text, read_json_file
from .security_status import build_security_status, render_security_status

WATCH_DIR = APP_DIR / "security_reports"
WATCH_STATE = WATCH_DIR / "security_watch_state.json"
WATCH_MD = WATCH_DIR / "security_watch_latest.md"
WATCH_JSON = WATCH_DIR / "security_watch_latest.json"


def _port_keys(payload: dict[str, Any]) -> set[str]:
    rows = payload.get("listening_ports") or []
    out = set()
    for row in rows:
        if isinstance(row, dict):
            out.add(f"{row.get('local','')}|{row.get('pid','')}")
    return out


def run_security_watch() -> dict[str, Any]:
    """Read-only defensive delta check.

    This does not retaliate, exploit, scan public targets, quarantine files, or
    change firewall/AV settings. It records local evidence and highlights deltas
    that the user may want to inspect.
    """
    WATCH_DIR.mkdir(parents=True, exist_ok=True)
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    current = build_security_status()
    previous = read_json_file(WATCH_STATE, {}, expected_type=dict, quarantine=True)
    old_ports = _port_keys(previous.get("security_status") or {}) if previous else set()
    new_ports = _port_keys(current)
    added_ports = sorted(new_ports - old_ports)[:50]
    removed_ports = sorted(old_ports - new_ports)[:50]
    recommendations = [
        "Review newly listening local services before taking action.",
        "Keep response defensive: isolate, capture evidence, stop known unwanted local processes manually, and run vendor AV tools.",
        "Use Kali tools only inside owned/local lab containers for defensive validation, not retaliation.",
    ]
    status = "attention" if added_ports else "stable"
    payload = {
        "ok": True,
        "created_at": now,
        "status": status,
        "summary": "Security watch found new listening services" if added_ports else "Security watch found no new listening services since the last snapshot",
        "added_listeners": added_ports,
        "removed_listeners": removed_ports,
        "security_status": current,
        "recommendations": recommendations,
        "defensive_only": True,
    }
    atomic_write_json(WATCH_JSON, payload, ensure_ascii=True)
    atomic_write_text(WATCH_MD, render_security_watch(payload), encoding="utf-8")
    atomic_write_json(WATCH_STATE, {"updated_at": now, "security_status": current}, ensure_ascii=True)
    payload["markdown_path"] = str(WATCH_MD)
    payload["json_path"] = str(WATCH_JSON)
    return payload


def render_security_watch(payload: dict[str, Any]) -> str:
    lines = ["# Nova Security Watch", "", f"Status: **{payload.get('status')}**", f"Summary: {payload.get('summary','')}", "", "This is defensive-only. It does not perform offensive response or external scanning."]
    if payload.get("added_listeners"):
        lines += ["", "## New listening services"] + [f"- `{x}`" for x in payload.get("added_listeners", [])]
    if payload.get("removed_listeners"):
        lines += ["", "## Removed listening services"] + [f"- `{x}`" for x in payload.get("removed_listeners", [])]
    lines += ["", "## Current security snapshot", "", render_security_status(payload.get("security_status") or {})]
    lines += ["", "## Recommendations"] + [f"- {r}" for r in payload.get("recommendations", [])]
    if payload.get("markdown_path"):
        lines += ["", f"Report: `{payload.get('markdown_path')}`"]
    return "\n".join(lines)
