from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json

logger = logging.getLogger(__name__)

IDLE_POLICY_PATH = APP_DIR / "idle_policy.json"

IDLE_LEVELS: dict[int, dict[str, Any]] = {
    0: {
        "name": "watch",
        "title": "Watch only",
        "allows_proposals": False,
        "allows_patch_prepare": False,
        "allows_auto_apply": False,
        "description": "Observe logs and failures only. Never writes proposals or patches from background idle.",
    },
    1: {
        "name": "propose",
        "title": "Propose only",
        "allows_proposals": True,
        "allows_patch_prepare": False,
        "allows_auto_apply": False,
        "description": "Write reports/proposals only. No source edits are applied.",
    },
    2: {
        "name": "prepare",
        "title": "Prepare patch",
        "allows_proposals": True,
        "allows_patch_prepare": True,
        "allows_auto_apply": False,
        "description": "Prepare reviewable patches and validation plans. Live source promotion remains blocked.",
    },
    3: {
        "name": "apply-low-risk",
        "title": "Auto-apply low-risk",
        "allows_proposals": True,
        "allows_patch_prepare": True,
        "allows_auto_apply": True,
        "description": "May apply tiny low-risk changes only after backup, diff, validation and rollback evidence.",
    },
}

ALIASES = {
    "0": 0, "watch": 0, "watch-only": 0, "off": 0,
    "1": 1, "propose": 1, "proposal": 1, "propose-only": 1,
    "2": 2, "prepare": 2, "patch": 2, "patch-prepare": 2,
    "3": 3, "apply": 3, "low-risk": 3, "auto": 3, "auto-apply": 3, "apply-low-risk": 3,
}


def _default_policy() -> dict[str, Any]:
    return {"level": 1, "updated_at": "", "updated_by": "default"}


def load_idle_policy() -> dict[str, Any]:
    data = _default_policy()
    try:
        if IDLE_POLICY_PATH.exists():
            loaded = json.loads(IDLE_POLICY_PATH.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                data.update(loaded)
    except Exception as exc:
        logger.warning("Failed to load idle policy from %s: %s", IDLE_POLICY_PATH, exc)
    try:
        level = int(data.get("level", 1))
    except Exception:
        level = 1
    if level not in IDLE_LEVELS:
        level = 1
    spec = dict(IDLE_LEVELS[level])
    data["level"] = level
    data["spec"] = spec
    return data


def set_idle_policy_level(value: str | int, *, updated_by: str = "user") -> dict[str, Any]:
    if isinstance(value, int):
        level = value
    else:
        key = str(value or "").strip().lower()
        if key not in ALIASES:
            raise ValueError(f"Unknown idle level '{value}'. Use 0/watch, 1/propose, 2/prepare, or 3/apply-low-risk.")
        level = ALIASES[key]
    if level not in IDLE_LEVELS:
        raise ValueError(f"Unknown idle level '{value}'.")
    data = {"level": level, "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "updated_by": updated_by}
    atomic_write_json(IDLE_POLICY_PATH, data, ensure_ascii=False)
    return load_idle_policy()


def idle_allows(action: str, policy: dict[str, Any] | None = None) -> bool:
    spec = (policy or load_idle_policy()).get("spec") or {}
    action = str(action or "").strip().lower()
    if action in {"observe", "watch", "status"}:
        return True
    if action in {"propose", "report"}:
        return bool(spec.get("allows_proposals"))
    if action in {"prepare", "patch_prepare", "patch"}:
        return bool(spec.get("allows_patch_prepare"))
    if action in {"apply", "auto_apply", "promote"}:
        return bool(spec.get("allows_auto_apply"))
    return False


def render_idle_policy(policy: dict[str, Any] | None = None) -> str:
    policy = policy or load_idle_policy()
    spec = policy.get("spec") or {}
    lines = [
        "# Idle Behaviour Policy",
        "",
        f"Current level: {policy.get('level')} — {spec.get('title','')}",
        f"Mode key: `{spec.get('name','')}`",
        f"Updated: {policy.get('updated_at') or 'not explicitly set'}",
        "",
        str(spec.get("description") or ""),
        "",
        "## Allowed actions",
        f"- Observe/status: yes",
        f"- Write proposals/reports: {'yes' if spec.get('allows_proposals') else 'no'}",
        f"- Prepare reviewable patches: {'yes' if spec.get('allows_patch_prepare') else 'no'}",
        f"- Apply low-risk live edits: {'yes' if spec.get('allows_auto_apply') else 'no'}",
        "",
        "## Levels",
    ]
    for level, item in IDLE_LEVELS.items():
        mark = "current" if level == policy.get("level") else "available"
        lines.append(f"- {level}: **{item['title']}** ({mark}) — {item['description']}")
    return "\n".join(lines)
