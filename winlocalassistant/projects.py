from __future__ import annotations

import re
import shutil
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, read_json_file

PROJECTS_PATH = APP_DIR / "projects.json"


def _safe_name(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_. -]+", "", name or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)[:80].strip(" .")
    return cleaned or "UntitledProject"


def _is_transient_test_path(path: Path | str) -> bool:
    text = str(path).lower().replace("\\", "/")
    return "pytest-of-" in text or "/pytest-" in text or "/appdata/local/temp/" in text or "/temp/pytest-" in text


def load_projects() -> dict[str, Any]:
    if not PROJECTS_PATH.exists():
        return {"current": "", "projects": {}}
    try:
        data = read_json_file(PROJECTS_PATH, {"current": "", "projects": {}}, expected_type=dict, quarantine=True)
        if not isinstance(data, dict):
            raise ValueError("bad projects data")
        data.setdefault("current", "")
        data.setdefault("projects", {})
        return data
    except Exception:
        return {"current": "", "projects": {}}


def save_projects(data: dict[str, Any]) -> None:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(PROJECTS_PATH, data, ensure_ascii=False)


def register_project(name: str, path: str, make_current: bool = True) -> dict[str, Any]:
    data = load_projects()
    safe = _safe_name(name)
    resolved = str(Path(path).expanduser().resolve())
    existing = data.get("projects", {}).get(safe, {}) if isinstance(data.get("projects"), dict) else {}
    project = {"name": safe, "path": resolved, "created_at": existing.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S")}
    if _is_transient_test_path(resolved):
        project["transient"] = True
        project["stale"] = True
        project["stale_reason"] = "Transient pytest/temp workspace; hidden from normal project lists."
    data["projects"][safe] = project
    if make_current:
        data["current"] = safe
    save_projects(data)
    return project


def remove_project(name: str, delete_files: bool = False) -> dict[str, Any]:
    data = load_projects()
    safe = _safe_name(name)
    project = data["projects"].pop(safe, None)
    existed = project is not None
    deleted = False
    delete_error = ""
    if data.get("current") == safe:
        data["current"] = ""
    save_projects(data)
    if existed and delete_files and project:
        try:
            path = Path(project["path"]).expanduser().resolve()
            # Refuse to delete obviously broad folders.
            dangerous_names = {"", "users", "documents", "desktop", "downloads", "projects", "winlocalassistantprojects"}
            if path.name.lower() in dangerous_names or len(path.parts) < 4:
                raise ValueError(f"Refusing to delete broad folder: {path}")
            if path.exists():
                shutil.rmtree(path)
                deleted = True
        except Exception as exc:
            delete_error = repr(exc)
    return {"existed": existed, "deleted_files": deleted, "delete_error": delete_error, "project": project}


def list_projects() -> list[dict[str, Any]]:
    data = load_projects()
    current = data.get("current", "")
    rows: list[dict[str, Any]] = []
    for key, project in sorted(data.get("projects", {}).items(), key=lambda kv: kv[0].lower()):
        row = dict(project)
        row["current"] = key == current
        path = Path(row["path"])
        row["exists"] = path.exists()
        row["stale"] = (not row["exists"]) or _is_transient_test_path(path)
        row.setdefault("created_at", project.get("created_at", ""))
        row["modified_at"] = ""
        row["file_count"] = 0
        row["project_size_bytes"] = 0
        row["main_file"] = ""
        if path.exists() and path.is_dir():
            try:
                latest = path.stat().st_mtime
                total = 0
                count = 0
                for child in path.rglob("*"):
                    if child.is_file():
                        count += 1
                        try:
                            st = child.stat()
                            latest = max(latest, st.st_mtime)
                            total += st.st_size
                        except OSError:
                            pass
                row["file_count"] = count
                row["project_size_bytes"] = total
                row["modified_at"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(latest))
                for candidate in ["PROJECT_MANIFEST.json", "index.html", "main.py", "app.py", "README.md"]:
                    if (path / candidate).exists():
                        row["main_file"] = candidate
                        break
            except Exception as exc:
                row["metadata_error"] = repr(exc)
        if _is_transient_test_path(path):
            row["stale_reason"] = "Transient pytest/temp workspace registration."
            continue
        elif not row["exists"]:
            row["stale_reason"] = "Project path no longer exists."
        rows.append(row)
    return rows


def get_project(name: str | None = None) -> dict[str, Any] | None:
    data = load_projects()
    key = _safe_name(name) if name else data.get("current", "")
    return data.get("projects", {}).get(key)
