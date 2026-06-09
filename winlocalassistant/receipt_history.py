from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .nova_operating_context import RECEIPT_PATH


def load_receipts(limit: int = 20) -> list[dict[str, Any]]:
    if not RECEIPT_PATH.exists():
        return []
    rows: list[dict[str, Any]] = []
    try:
        for line in RECEIPT_PATH.read_text(encoding="utf-8", errors="replace").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                val = json.loads(line)
                if isinstance(val, dict):
                    rows.append(val)
            except Exception:
                continue
    except Exception:
        return []
    if limit and limit > 0:
        return rows[-int(limit):]
    return rows


def summarise_receipts(limit: int = 20) -> dict[str, Any]:
    receipts = load_receipts(limit=limit)
    ok_count = sum(1 for r in receipts if r.get("ok"))
    changed = []
    for r in receipts:
        for item in r.get("changed_files") or []:
            if item not in changed:
                changed.append(str(item))
    return {
        "ok": True,
        "path": str(RECEIPT_PATH),
        "count": len(receipts),
        "ok_count": ok_count,
        "attention_count": len(receipts) - ok_count,
        "changed_files": changed[-30:],
        "receipts": receipts,
        "summary": f"{len(receipts)} receipt(s), {ok_count} passed, {len(receipts)-ok_count} attention/no-op",
    }


def render_receipt_history(payload: dict[str, Any]) -> str:
    lines = ["# Nova Receipt History", "", f"Source: `{payload.get('path','')}`", f"Summary: {payload.get('summary','')}", "", "## Recent receipts"]
    receipts = payload.get("receipts") or []
    if not receipts:
        lines.append("No receipts have been recorded yet.")
        return "\n".join(lines)
    for item in reversed(receipts[-20:]):
        mark = "PASS" if item.get("ok") else "ATTENTION"
        lines.append(f"- {mark} {item.get('time','')} — {item.get('action','')} — {item.get('goal','')}")
        changed = item.get("changed_files") or []
        if changed:
            lines.append("  - Changed: " + ", ".join(str(x) for x in changed[:6]))
        validation = item.get("validation") or []
        if validation:
            good = sum(1 for v in validation if isinstance(v, dict) and v.get("ok"))
            lines.append(f"  - Validation: {good}/{len(validation)} passed")
        if item.get("notes"):
            lines.append(f"  - Notes: {str(item.get('notes'))[:220]}")
    return "\n".join(lines)
