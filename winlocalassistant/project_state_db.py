from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, read_json_file

STATE_FILE = ".wla_project_state.json"
MAX_STATE_ITEMS_PER_BUCKET = 250


def _path(root: Path) -> Path:
    return root / STATE_FILE


def _empty_state(root: Path, *, reason: str = "") -> dict[str, Any]:
    state: dict[str, Any] = {
        "root": str(root),
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "original_prompt": "",
        "blueprints": [],
        "candidates": [],
        "validation_failures": [],
        "repair_attempts": [],
        "file_diffs": [],
        "user_feedback": [],
    }
    if reason:
        state["validation_failures"].append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "data": reason})
    return state


def _normalise_state(root: Path, data: Any) -> dict[str, Any]:
    if not isinstance(data, dict):
        return _empty_state(root, reason="project state was not a JSON object")
    state = _empty_state(root)
    state.update(data)
    state["root"] = str(state.get("root") or root)
    state.setdefault("created_at", time.strftime("%Y-%m-%d %H:%M:%S"))
    state["updated_at"] = str(state.get("updated_at") or time.strftime("%Y-%m-%d %H:%M:%S"))
    for key in ["blueprints", "candidates", "validation_failures", "repair_attempts", "file_diffs", "user_feedback"]:
        if not isinstance(state.get(key), list):
            state[key] = [{"time": time.strftime("%Y-%m-%d %H:%M:%S"), "data": f"{key} was not a list and was reset"}]
        if len(state[key]) > MAX_STATE_ITEMS_PER_BUCKET:
            state[key] = state[key][-MAX_STATE_ITEMS_PER_BUCKET:]
    return state


def load_project_state(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    p = _path(root)
    if not p.exists():
        return _empty_state(root)
    data = read_json_file(p, None, expected_type=dict, quarantine=True)
    if data is None:
        return _empty_state(root, reason="project state JSON could not be decoded; corrupt copy was quarantined")
    return _normalise_state(root, data)


def append_project_state(root: str | Path = ".", kind: str = "note", data: Any = None) -> dict[str, Any]:
    root = Path(root)
    s = load_project_state(root)
    key = {
        "blueprint": "blueprints",
        "candidate": "candidates",
        "failure": "validation_failures",
        "repair": "repair_attempts",
        "diff": "file_diffs",
        "feedback": "user_feedback",
    }.get(kind, "user_feedback")
    s.setdefault(key, []).append({"time": time.strftime("%Y-%m-%d %H:%M:%S"), "data": data})
    if len(s[key]) > MAX_STATE_ITEMS_PER_BUCKET:
        s[key] = s[key][-MAX_STATE_ITEMS_PER_BUCKET:]
    s["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    atomic_write_json(_path(root), s, ensure_ascii=False)
    return s


def audit_project_state(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    path = _path(root)
    state = load_project_state(root)
    counts = {k: len(state.get(k) or []) for k in ["blueprints", "candidates", "validation_failures", "repair_attempts", "file_diffs", "user_feedback"]}
    warnings: list[str] = []
    if not path.exists():
        warnings.append("No project state database exists yet for this workspace.")
    if any(v >= MAX_STATE_ITEMS_PER_BUCKET for v in counts.values()):
        warnings.append("One or more project-state buckets are at the retention cap; older entries were trimmed to keep state responsive.")
    if not state.get("original_prompt") and any(counts.values()):
        warnings.append("Project state has events but no original prompt; future recovery may be less specific.")
    return {
        "ok": not warnings,
        "path": str(path),
        "exists": path.exists(),
        "counts": counts,
        "updated_at": state.get("updated_at", ""),
        "warnings": warnings,
    }


def render_project_state(s: dict[str, Any]) -> str:
    lines = [
        "# Nova Project State Database v2",
        "",
        f"Root: `{s.get('root','')}`",
        f"Original prompt: {s.get('original_prompt','') or '(not recorded)' }",
        f"Updated: {s.get('updated_at','(unknown)')}",
        "",
        "## Counts",
    ]
    for k in ["blueprints", "candidates", "validation_failures", "repair_attempts", "file_diffs", "user_feedback"]:
        lines.append(f"- {k}: {len(s.get(k, []))}")
    lines += ["", "## Latest failures"]
    failures = s.get("validation_failures", [])[-5:]
    if not failures:
        lines.append("- None recorded.")
    for item in failures:
        lines.append(f"- {item.get('time')}: {str(item.get('data'))[:180]}")
    return "\n".join(lines)
