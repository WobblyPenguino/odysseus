from __future__ import annotations

"""Project-state snapshot helpers for Nova continuity.

This module intentionally stays small.  It reads existing release, task and
host-calibration evidence and writes one current snapshot so commands such as
/project-state and "continue where it left off" can use concrete state instead
of guessing from chat history.
"""

import argparse
import json
import time
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .safe_io import atomic_write_json, atomic_write_text
from .task_execution import latest_task_evidence, build_task_execution_status

SCHEMA_VERSION = 1
SNAPSHOT_DIR = Path("logs") / "project_state"
LATEST_JSON = Path("docs") / "NOVA_PROJECT_STATE_LATEST.json"
LATEST_MD = Path("docs") / "NOVA_PROJECT_STATE_LATEST.md"
DOC_PATH = Path("docs") / "NOVA_CONTINUITY_AND_PROJECT_STATE.md"


def _root(root: str | Path = ".") -> Path:
    return Path(root).expanduser().resolve()


def _read_json(path: Path, default: Any = None) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return default


def _latest_file(root: Path, patterns: list[str]) -> Path | None:
    candidates: list[Path] = []
    for pat in patterns:
        candidates.extend(root.glob(pat))
    candidates = [p for p in candidates if p.exists() and p.is_file()]
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


def _rel(root: Path, path: Path | str | None) -> str:
    if not path:
        return ""
    try:
        p = Path(path)
        if p.is_absolute():
            return p.relative_to(root).as_posix()
        return p.as_posix()
    except Exception:
        return str(path)


def latest_release_readiness_summary(root: str | Path = ".") -> dict[str, Any]:
    root_path = _root(root)
    path = root_path / "docs" / "NOVA_RELEASE_READINESS_LATEST.json"
    data = _read_json(path, {})
    if not isinstance(data, dict) or not data:
        return {
            "ok": False,
            "status": "MISSING",
            "summary": "No release-readiness evidence found yet.",
            "path": str(path),
            "required_failed": [],
            "optional_failed": [],
        }
    return {
        "ok": bool(data.get("ok")),
        "status": str(data.get("status") or "UNKNOWN"),
        "summary": str(data.get("summary") or ""),
        "created_at": str(data.get("created_at") or ""),
        "path": str(path),
        "required_failed": list(data.get("required_failed") or []),
        "optional_failed": list(data.get("optional_failed") or []),
        "category_status": data.get("category_status") or {},
    }


def latest_package_manifest_summary(root: str | Path = ".") -> dict[str, Any]:
    root_path = _root(root)
    candidates = [root_path / "RELEASE_MANIFEST.json"]
    candidates.extend((root_path / "docs").glob("*manifest*.json") if (root_path / "docs").exists() else [])
    candidates = [p for p in candidates if p.exists()]
    if not candidates:
        return {"ok": False, "status": "MISSING", "summary": "No package manifest found.", "path": ""}
    path = max(candidates, key=lambda p: p.stat().st_mtime)
    data = _read_json(path, {})
    return {
        "ok": bool(data),
        "status": "FOUND" if data else "UNREADABLE",
        "path": str(path),
        "version": str((data or {}).get("version") or ""),
        "release_name": str((data or {}).get("release_name") or ""),
        "package_path": str((data or {}).get("package_path") or ""),
        "file_count": int((data or {}).get("file_count") or len((data or {}).get("files") or []) or 0),
    }


def latest_host_checks(root: str | Path = ".") -> list[dict[str, Any]]:
    root_path = _root(root)
    rows: list[dict[str, Any]] = []
    model_path = root_path / "docs" / "NOVA_MODEL_CALIBRATION_LATEST.json"
    model_data = _read_json(model_path, {})
    if isinstance(model_data, dict) and model_data:
        status = str(model_data.get("status") or model_data.get("summary") or "HOST_CHECK_NEEDED")
        rows.append({
            "name": "model/Ollama/GPU calibration",
            "status": status,
            "advisory": True,
            "path": str(model_path),
            "summary": str(model_data.get("summary") or "Run on the real Windows/Ollama host for accurate GPU/model timing."),
        })
    else:
        rows.append({
            "name": "model/Ollama/GPU calibration",
            "status": "HOST_CHECK_NEEDED",
            "advisory": True,
            "path": str(model_path),
            "summary": "No host calibration evidence in this extracted folder. Run /model-calibration --bench on the Windows Nova PC.",
        })
    return rows


def infer_recommended_next_action(readiness: dict[str, Any], task_status: dict[str, Any]) -> str:
    status = str(readiness.get("status") or "MISSING").upper()
    if status == "FAIL":
        failed = ", ".join(readiness.get("required_failed") or []) or "the failed required checks"
        return f"Fix {failed}, then rerun /release-readiness --full before packaging."
    if task_status.get("active_repeated_failures"):
        return "Stop automatic retries, inspect /task-evidence, fix the first repeated error, then rerun verification."
    if status == "PASS":
        return "Safe next action: choose one small improvement, create a /task-contract, patch narrowly, then rerun /release-readiness --full."
    return "Generate fresh evidence with /verify --full or /release-readiness --full before continuing automatically."


def build_project_state_snapshot(root: str | Path = ".", *, write: bool = True) -> dict[str, Any]:
    root_path = _root(root)
    docs = root_path / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    (root_path / SNAPSHOT_DIR).mkdir(parents=True, exist_ok=True)
    readiness = latest_release_readiness_summary(root_path)
    task_status = build_task_execution_status(root_path)
    task_evidence = latest_task_evidence(root_path, limit=5)
    latest_manifest = latest_package_manifest_summary(root_path)
    manifest_release = latest_manifest.get("release_name") or latest_manifest.get("package_path") or ""
    known_limitations = [
        item.get("summary", "") for item in latest_host_checks(root_path) if item.get("advisory") and str(item.get("status", "")).upper() != "PASS"
    ]
    changed_files: list[str] = []
    for ev in task_evidence:
        for key in ("changed_files", "files_changed"):
            for item in ev.get(key) or []:
                if item and item not in changed_files:
                    changed_files.append(str(item))
    packaging_allowed = readiness.get("status") == "PASS" and bool(readiness.get("ok")) and not task_status.get("active_repeated_failures")
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "ok": True,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "current_version": __version__,
        "version_label": VERSION_LABEL,
        "root": str(root_path),
        "latest_release_readiness": readiness,
        "latest_task_evidence": task_evidence,
        "latest_task_result": (task_evidence[0].get("result") if task_evidence else "MISSING"),
        "latest_changed_files": changed_files[:30],
        "latest_package_manifest": latest_manifest,
        "last_completed_patch": manifest_release or f"Nova v{__version__}",
        "task_execution_status": task_status,
        "host_only_checks": latest_host_checks(root_path),
        "known_limitations": known_limitations,
        "packaging_allowed": packaging_allowed,
        "continue_readiness": "PASS" if packaging_allowed else ("FAIL" if readiness.get("status") == "FAIL" or task_status.get("active_repeated_failures") else "REVIEW"),
        "recommended_next_action": infer_recommended_next_action(readiness, task_status),
        "needs_inspection_before_editing": readiness.get("status") != "PASS" or not task_evidence,
        "latest_json": str(root_path / LATEST_JSON),
        "latest_markdown": str(root_path / LATEST_MD),
    }
    if write:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        snap_path = root_path / SNAPSHOT_DIR / f"project_state_{stamp}.json"
        snapshot["snapshot_path"] = str(snap_path)
        atomic_write_json(snap_path, snapshot, ensure_ascii=True)
        atomic_write_json(root_path / LATEST_JSON, snapshot, ensure_ascii=True)
        atomic_write_text(root_path / LATEST_MD, render_project_state_snapshot(snapshot))
    return snapshot


def render_project_state_snapshot(payload: dict[str, Any]) -> str:
    readiness = payload.get("latest_release_readiness") or {}
    manifest = payload.get("latest_package_manifest") or {}
    task = payload.get("task_execution_status") or {}
    lines = [
        "# Nova Project State Snapshot",
        "",
        f"Version: `{payload.get('current_version', '')}`",
        f"Root: `{payload.get('root', '')}`",
        f"Last completed patch/package: `{payload.get('last_completed_patch', '') or 'unknown'}`",
        f"Release-readiness: **{readiness.get('status', 'UNKNOWN')}** — {readiness.get('summary', '')}",
        f"Continue readiness: **{payload.get('continue_readiness', 'UNKNOWN')}**",
        f"Packaging allowed: `{payload.get('packaging_allowed')}`",
        f"Recommended next action: {payload.get('recommended_next_action', '')}",
        f"Needs inspection before editing: `{payload.get('needs_inspection_before_editing')}`",
        "",
        "## Latest task evidence",
    ]
    evidence = payload.get("latest_task_evidence") or []
    if not evidence:
        lines.append("- No task evidence found yet.")
    for ev in evidence[:5]:
        lines.append(f"- **{ev.get('result', 'UNKNOWN')}** `{ev.get('action', '')}` command=`{ev.get('command', '')}` path=`{_rel(Path(payload.get('root', '.')), ev.get('json_path'))}`")
    lines.extend(["", "## Changed files from evidence"])
    changed = payload.get("latest_changed_files") or []
    if not changed:
        lines.append("- None recorded in latest task evidence.")
    else:
        lines.extend(f"- `{item}`" for item in changed[:30])
    lines.extend(["", "## Package manifest"])
    if manifest.get("ok"):
        lines.append(f"- `{manifest.get('release_name') or manifest.get('path')}` version=`{manifest.get('version')}` files=`{manifest.get('file_count')}`")
    else:
        lines.append(f"- {manifest.get('summary', 'No package manifest found.')}")
    lines.extend(["", "## Host-only advisory checks"])
    for item in payload.get("host_only_checks") or []:
        lines.append(f"- **{item.get('status')}** — {item.get('name')}: {item.get('summary')}")
    lines.extend(["", "## Task execution status", f"- Status: **{task.get('status', 'UNKNOWN')}** — {task.get('summary', '')}"])
    if task.get("active_repeated_failures"):
        lines.append("- Repeated-failure guard is active; do not continue automatically.")
    return "\n".join(lines).strip() + "\n"


def render_project_state_next(payload: dict[str, Any]) -> str:
    readiness = payload.get("latest_release_readiness") or {}
    lines = [
        "# Nova Continue / Next Step",
        "",
        f"Current version: `{payload.get('current_version', '')}`",
        f"Last completed patch: `{payload.get('last_completed_patch', '') or 'unknown'}`",
        f"Last release-readiness verdict: **{readiness.get('status', 'UNKNOWN')}**",
        f"Known limitations: {('; '.join(payload.get('known_limitations') or []) or 'None recorded beyond host-only checks.')}",
        f"Safest next action: {payload.get('recommended_next_action', '')}",
        f"Inspect before editing: `{payload.get('needs_inspection_before_editing')}`",
        "",
        "Use `/project-state` for the full snapshot and `/task-evidence` for detailed run evidence.",
    ]
    return "\n".join(lines).strip() + "\n"


def build_continue_context_reply(root: str | Path = ".") -> str:
    payload = build_project_state_snapshot(root, write=True)
    return render_project_state_next(payload)


def build_autonomous_continuity_status(root: str | Path = ".") -> dict[str, Any]:
    snap = build_project_state_snapshot(root, write=True)
    task = snap.get("task_execution_status") or {}
    readiness = snap.get("latest_release_readiness") or {}
    last_evidence = (snap.get("latest_task_evidence") or [{}])[0]
    blockers: list[str] = []
    if not snap.get("snapshot_path") and not Path(str(snap.get("latest_json", ""))).exists():
        blockers.append("project-state snapshot missing")
    if str(last_evidence.get("result", "PASS")).upper() in {"FAIL", "REVIEW"}:
        blockers.append(f"last task result is {last_evidence.get('result')}")
    if task.get("active_repeated_failures"):
        blockers.append("repeated-failure guard active")
    if str(readiness.get("status", "")).upper() == "FAIL":
        blockers.append("release-readiness failed")
    if snap.get("latest_changed_files") and not last_evidence.get("verification_passed"):
        blockers.append("changed files exist without passing verification evidence")
    return {
        "ok": not blockers,
        "safe_to_continue_automatically": not blockers,
        "blockers": blockers,
        "project_state_snapshot_path": snap.get("snapshot_path") or snap.get("latest_json"),
        "last_task_evidence_path": last_evidence.get("json_path") or "",
        "last_release_readiness_verdict": readiness.get("status"),
        "stop_reason": "; ".join(blockers) if blockers else "No continuity blockers detected.",
        "next_recommended_safe_step": snap.get("recommended_next_action"),
    }


def render_project_state_command(rest: str = "", *, root: str | Path = ".") -> str:
    raw = (rest or "").strip().lower()
    payload = build_project_state_snapshot(root, write=True)
    if "--json" in raw or raw == "json":
        return json.dumps(payload, indent=2, ensure_ascii=True)
    if "--next" in raw or raw in {"next", "continue"}:
        return render_project_state_next(payload)
    return render_project_state_snapshot(payload)


def check_project_state_contract(root: str | Path = ".") -> str:
    payload = build_project_state_snapshot(root, write=True)
    assert payload.get("current_version"), payload
    assert Path(str(payload.get("latest_json"))).exists(), payload
    assert Path(str(payload.get("latest_markdown"))).exists(), payload
    assert payload.get("continue_readiness") in {"PASS", "REVIEW", "FAIL"}, payload
    continuity = build_autonomous_continuity_status(root)
    assert "safe_to_continue_automatically" in continuity, continuity
    return f"Project-state snapshot written to {payload.get('latest_json')} with continue readiness {payload.get('continue_readiness')}."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Write/read Nova project-state snapshot evidence")
    parser.add_argument("--root", default=".")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--next", action="store_true")
    args = parser.parse_args()
    payload = build_project_state_snapshot(args.root, write=True)
    if args.json:
        print(json.dumps(payload, indent=2, ensure_ascii=True))
    elif args.next:
        print(render_project_state_next(payload))
    else:
        print(render_project_state_snapshot(payload))
