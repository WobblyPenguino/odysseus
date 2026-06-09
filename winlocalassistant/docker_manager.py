from __future__ import annotations

import hashlib
import glob
import json
import logging
import os
import shlex
import shutil
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any

from .config import APP_DIR, AssistantConfig
from .eventlog import log_activity
from .safe_io import append_jsonl, atomic_write_json

DOCKER_AUDIT_PATH = APP_DIR / "docker_audit.jsonl"
DOCKER_LAST_STATUS_PATH = APP_DIR / "docker_status.json"
DOCKER_RUNS_DIR = APP_DIR / "docker_runs"
DOCKER_LAST_VALIDATION_PATH = APP_DIR / "docker_last_validation.json"


def _now() -> float:
    return time.time()


def _sha256_text(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def _sha256_file(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def _run(args: list[str], timeout: int = 20, cwd: str | Path | None = None) -> dict[str, Any]:
    started = _now()
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=max(1, timeout), cwd=str(cwd) if cwd else None)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-12000:],
            "stderr": (proc.stderr or "")[-12000:],
            "elapsed_sec": round(_now() - started, 3),
            "command": args,
            "cwd": str(cwd) if cwd else "",
        }
    except subprocess.TimeoutExpired as exc:
        return {
            "ok": False,
            "returncode": None,
            "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "",
            "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "",
            "elapsed_sec": round(_now() - started, 3),
            "timeout": timeout,
            "command": args,
            "cwd": str(cwd) if cwd else "",
            "error": "timeout",
        }
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": "", "elapsed_sec": round(_now() - started, 3), "command": args, "error": repr(exc)}


def _run_local_command(command: str, timeout: int = 300, cwd: str | Path | None = None) -> dict[str, Any]:
    """Run a local validation command with Windows-friendly simple parsing.

    PowerShell changes POSIX-style single quotes inside commands such as
    `python -c 'print("ok")'`, and Windows shells do not expand `tests_*.py`
    globs for Python commands. For simple commands, run the parsed argument list
    directly and expand globs ourselves. Fall back to the platform shell only
    when the command uses shell operators.
    """
    command = (command or "").strip()
    if not command:
        return {"ok": True, "summary": "No local post-promotion command requested", "stdout": "", "stderr": ""}
    try:
        args = shlex.split(command, posix=True)
    except ValueError:
        args = []
    shell_tokens = {"&&", "||", "|", ";"}
    if args and not any(token in shell_tokens or token.startswith((">", "<")) for token in args):
        base = Path(cwd or ".").expanduser()
        expanded: list[str] = []
        for arg in args:
            if any(ch in arg for ch in "*?["):
                pattern = arg if Path(arg).is_absolute() else str(base / arg)
                matches = sorted(glob.glob(pattern))
                expanded.extend(matches or [arg])
            else:
                expanded.append(arg)
        return _run(expanded, timeout=timeout, cwd=cwd)
    return _run(["sh", "-lc", command], timeout=timeout, cwd=cwd) if os.name != "nt" else _run(["powershell", "-NoProfile", "-Command", command], timeout=timeout, cwd=cwd)



def _short_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]


def _docker_mount_path(path: Path) -> str:
    """Return a Docker -v compatible path string for the host platform."""
    return str(path.resolve())


def _copy_workspace_for_validation(source: Path, dest: Path) -> dict[str, Any]:
    excluded_dirs = {".git", ".hg", ".svn", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "node_modules", "dist", "build", ".winlocalassistant", ".nova_runtime", "docker_runs", "htmlcov", ".coverage"}
    excluded_suffixes = {".pyc", ".pyo", ".log"}
    copied_files = 0
    skipped_items = 0

    def ignore(directory: str, names: list[str]) -> set[str]:
        nonlocal skipped_items
        ignored: set[str] = set()
        for name in names:
            if name in excluded_dirs or Path(name).suffix.lower() in excluded_suffixes:
                ignored.add(name)
                skipped_items += 1
        return ignored

    if source.is_file():
        dest.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, dest / source.name)
        copied_files = 1
    else:
        shutil.copytree(source, dest, ignore=ignore, dirs_exist_ok=True)
        for item in dest.rglob("*"):
            if item.is_file():
                copied_files += 1
    return {"copied_files": copied_files, "skipped_items": skipped_items, "source": str(source), "dest": str(dest)}

def _audit(event: str, payload: dict[str, Any]) -> None:
    row = {"ts": _now(), "event": event, **payload}
    append_jsonl(DOCKER_AUDIT_PATH, row)
    try:
        log_activity("docker_" + event, "Docker event: " + event, payload)
    except Exception as exc:
        try:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        except Exception as log_exc:
            logging.getLogger(__name__).debug("Docker audit activity logging failed: %r", log_exc, exc_info=True)


def _docker_cli() -> str:
    return shutil.which("docker") or ""


def _wsl_cli() -> str:
    return shutil.which("wsl") or ""


def _parse_json_lines(text: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in (text or "").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
            if isinstance(obj, dict):
                rows.append(obj)
        except Exception:
            rows.append({"raw": line})
    return rows


def docker_status(config: AssistantConfig, include_raw: bool = True) -> dict[str, Any]:
    """Return Docker diagnostics without requiring Docker to be installed.

    This intentionally uses short timeouts and captures raw command output so the
    GUI can show why Docker is unavailable instead of silently failing.
    """
    docker = _docker_cli()
    wsl = _wsl_cli()
    payload: dict[str, Any] = {
        "checked_at": _now(),
        "installed": bool(docker),
        "cli_path": docker,
        "wsl_path": wsl,
        "daemon_running": False,
        "compose_available": False,
        "containers": [],
        "images": [],
        "raw": {},
        "notes": [],
    }
    if not docker:
        payload["notes"].append("Docker CLI was not found on PATH. Install/start Docker Desktop or add Docker to PATH, then restart Nova/PowerShell.")
        if wsl:
            payload["raw"]["wsl_list"] = _run([wsl, "--list", "--verbose"], timeout=12)
        _save_status(payload)
        _audit("status", {"installed": False})
        return payload

    payload["raw"]["docker_version"] = _run([docker, "--version"], timeout=8)
    compose = _run([docker, "compose", "version"], timeout=8)
    payload["raw"]["docker_compose_version"] = compose
    payload["compose_available"] = bool(compose.get("ok"))

    info = _run([docker, "info"], timeout=18)
    payload["raw"]["docker_info"] = info if include_raw else {k: info.get(k) for k in ["ok", "returncode", "stderr", "elapsed_sec"]}
    payload["daemon_running"] = bool(info.get("ok"))
    if not info.get("ok"):
        payload["notes"].append("Docker CLI exists, but the Docker daemon did not respond. Start Docker Desktop and wait until it says Docker is running.")

    ps = _run([docker, "ps", "-a", "--format", "{{json .}}"], timeout=12)
    payload["raw"]["docker_ps"] = ps if include_raw else {k: ps.get(k) for k in ["ok", "returncode", "stderr", "elapsed_sec"]}
    if ps.get("ok"):
        payload["containers"] = _parse_json_lines(ps.get("stdout", ""))

    images = _run([docker, "images", "--format", "{{json .}}"], timeout=12)
    payload["raw"]["docker_images"] = images if include_raw else {k: images.get(k) for k in ["ok", "returncode", "stderr", "elapsed_sec"]}
    if images.get("ok"):
        payload["images"] = _parse_json_lines(images.get("stdout", ""))[:80]

    if wsl:
        payload["raw"]["wsl_list"] = _run([wsl, "--list", "--verbose"], timeout=12)

    try:
        last_validation = json.loads(DOCKER_LAST_VALIDATION_PATH.read_text(encoding="utf-8")) if DOCKER_LAST_VALIDATION_PATH.exists() else {}
        if isinstance(last_validation, dict) and last_validation:
            payload["last_validation"] = last_validation
    except Exception:
        payload["last_validation"] = {}
    try:
        payload["validation_history"] = docker_validation_history(config, limit=8).get("runs", [])
    except Exception:
        payload["validation_history"] = []
    _save_status(payload)
    _audit("status", {"installed": payload["installed"], "daemon_running": payload["daemon_running"], "containers": len(payload["containers"])})
    return payload


def docker_ps(config: AssistantConfig) -> dict[str, Any]:
    docker = _docker_cli()
    if not docker:
        return {"ok": False, "summary": "Docker CLI not found", "containers": [], "hint": "Install/start Docker Desktop, then restart Nova."}
    ps = _run([docker, "ps", "-a", "--format", "{{json .}}"], timeout=12)
    rows = _parse_json_lines(ps.get("stdout", "")) if ps.get("ok") else []
    _audit("ps", {"ok": bool(ps.get("ok")), "containers": len(rows)})
    return {"ok": bool(ps.get("ok")), "summary": "Docker containers listed" if ps.get("ok") else "Docker ps failed", "containers": rows, "raw": ps}


def docker_smoke(config: AssistantConfig, image: str = "python:3.12-slim") -> dict[str, Any]:
    docker = _docker_cli()
    if not docker:
        return {"ok": False, "summary": "Docker CLI not found", "hint": "Install/start Docker Desktop, then restart Nova."}
    # Deliberately simple smoke test. It may pull the image if missing, so expose the exact command.
    args = [docker, "run", "--rm", image, "python", "--version"]
    result = _run(args, timeout=180)
    _audit("smoke", {"ok": bool(result.get("ok")), "image": image, "returncode": result.get("returncode")})
    return {"ok": bool(result.get("ok")), "summary": "Docker smoke test completed" if result.get("ok") else "Docker smoke test failed", "image": image, "raw": result}




def _docker_daemon_unavailable(raw: dict[str, Any]) -> bool:
    text = " ".join(str(raw.get(k, "")) for k in ("stderr", "stdout", "error")).lower()
    markers = [
        "dockerdesktoplinuxengine",
        "cannot connect to the docker daemon",
        "is the docker daemon running",
        "open //./pipe/docker",
        "the system cannot find the file specified",
        "error during connect",
    ]
    return any(m in text for m in markers)


def _docker_skipped_payload(run_id: str, image: str, command: str, source: Path | None, result: dict[str, Any], reason: str) -> dict[str, Any]:
    payload = {
        "ok": True,
        "skipped": True,
        "degraded": True,
        "summary": "Docker validation skipped - Docker Desktop/Linux engine is unavailable",
        "run_id": run_id,
        "image": image,
        "command": command,
        "source_path": str(source) if source else "",
        "run_dir": "",
        "workspace_copy": "",
        "copy_info": {"copied_files": 0, "skipped_items": 0},
        "raw": result,
        "reason": reason,
        "next_steps": [
            "Start Docker Desktop and wait until the Linux engine says it is running.",
            "Run /docker-status or docker ps to confirm the daemon is reachable.",
            "Re-run /docker-validate quick when Docker is available.",
            "Use python -m winlocalassistant.validate --all for non-Docker validation in the meantime.",
        ],
    }
    try:
        DOCKER_RUNS_DIR.mkdir(parents=True, exist_ok=True)
        run_dir = DOCKER_RUNS_DIR / run_id
        run_dir.mkdir(parents=True, exist_ok=True)
        payload["run_dir"] = str(run_dir)
        _write_validation_report(run_dir, payload)
    except Exception:
        pass
    _audit("validate_skipped", {"ok": True, "skipped": True, "run_id": run_id, "image": image, "reason": reason[:300]})
    return payload

def docker_validate_project(
    config: AssistantConfig,
    path: str = ".",
    command: str = "python -m compileall -q winlocalassistant tests_*.py app.py",
    image: str = "python:3.12-slim",
    timeout: int = 300,
) -> dict[str, Any]:
    """Validate a project inside a disposable Docker container using a copied workspace.

    The real project is never mounted directly. Nova copies the source tree into
    ~/.nova/docker_runs/<run_id>/workspace, mounts that copy, runs
    the command, and saves a structured report.
    """
    docker = _docker_cli()
    run_id = _short_id()
    if not docker:
        return {"ok": False, "summary": "Docker CLI not found", "run_id": run_id, "hint": "Install/start Docker Desktop, then restart Nova."}
    source = Path(path or ".").expanduser()
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve()
    if not source.exists():
        return {"ok": False, "summary": "Validation path does not exist", "run_id": run_id, "path": str(source)}
    DOCKER_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = DOCKER_RUNS_DIR / run_id
    workspace_copy = run_dir / "workspace"
    run_dir.mkdir(parents=True, exist_ok=True)
    copy_info = _copy_workspace_for_validation(source, workspace_copy)
    safe_command = (command or "python -m compileall -q winlocalassistant tests_*.py app.py").strip()
    args = [
        docker,
        "run",
        "--rm",
        "--network",
        "none",
        "--cpus",
        "2",
        "--memory",
        "3g",
        "--pids-limit",
        "768",
        "--security-opt",
        "no-new-privileges:true",
        "-v",
        f"{_docker_mount_path(workspace_copy)}:/workspace:rw",
        "-w",
        "/workspace",
        image or "python:3.12-slim",
        "sh",
        "-lc",
        safe_command,
    ]
    result = _run(args, timeout=max(1, min(int(timeout or 300), 1200)))
    if not result.get("ok") and _docker_daemon_unavailable(result):
        return _docker_skipped_payload(
            run_id,
            image or "python:3.12-slim",
            safe_command,
            source,
            result,
            "Docker CLI exists, but the Docker Desktop/Linux engine pipe is not reachable.",
        )
    payload = {
        "ok": bool(result.get("ok")),
        "summary": "Docker validation passed" if result.get("ok") else "Docker validation failed",
        "run_id": run_id,
        "image": image,
        "command": safe_command,
        "source_path": str(source),
        "run_dir": str(run_dir),
        "workspace_copy": str(workspace_copy),
        "copy_info": copy_info,
        "raw": result,
    }
    _write_validation_report(run_dir, payload)
    _audit("validate", {"ok": bool(payload.get("ok")), "run_id": run_id, "image": image, "command": safe_command[:300]})
    return payload


def _write_validation_report(run_dir: Path, payload: dict[str, Any]) -> None:
    try:
        atomic_write_json(run_dir / "validation_report.json", payload, ensure_ascii=True, indent=2)
        atomic_write_json(DOCKER_LAST_VALIDATION_PATH, payload, ensure_ascii=True, indent=2)
    except Exception as exc:
        _audit("validate_report_write_failed", {"run_id": payload.get("run_id", ""), "error": repr(exc)})


def docker_validate_patch(
    config: AssistantConfig,
    path: str = ".",
    patch_file: str = "",
    patch_text: str = "",
    command: str = "python -m compileall -q winlocalassistant tests_*.py app.py",
    image: str = "python:3.12-slim",
    timeout: int = 300,
) -> dict[str, Any]:
    """Validate a unified diff patch inside a copied workspace before touching real files.

    The project is copied to ~/.nova/docker_runs/<run_id>/workspace.
    Nova applies the patch only to that copy using `git apply`, then runs Docker
    validation against the patched copy. The live project is never modified.
    """
    docker = _docker_cli()
    run_id = _short_id()
    if not docker:
        return {"ok": False, "summary": "Docker CLI not found", "run_id": run_id, "hint": "Install/start Docker Desktop, then restart Nova."}
    git = shutil.which("git") or ""
    if not git:
        return {"ok": False, "summary": "Git CLI not found for patch validation", "run_id": run_id, "hint": "Install Git or use /docker-validate for non-patch validation."}
    source = Path(path or ".").expanduser()
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve()
    if not source.exists():
        return {"ok": False, "summary": "Validation path does not exist", "run_id": run_id, "path": str(source)}
    patch_content = patch_text or ""
    patch_source = "inline"
    if patch_file:
        pf = Path(patch_file).expanduser()
        if not pf.is_absolute():
            pf = (Path.cwd() / pf).resolve()
        if not pf.exists():
            return {"ok": False, "summary": "Patch file does not exist", "run_id": run_id, "patch_file": str(pf)}
        patch_content = pf.read_text(encoding="utf-8", errors="replace")
        patch_source = str(pf)
    if not patch_content.strip():
        return {"ok": False, "summary": "No patch content supplied", "run_id": run_id, "usage": "/docker-validate-patch PATH_TO_PATCH.diff"}
    patch_sha256 = _sha256_text(patch_content)
    DOCKER_RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_dir = DOCKER_RUNS_DIR / run_id
    workspace_copy = run_dir / "workspace"
    run_dir.mkdir(parents=True, exist_ok=True)
    copy_info = _copy_workspace_for_validation(source, workspace_copy)
    patch_path = run_dir / "input.patch"
    patch_path.write_text(patch_content, encoding="utf-8")
    check = _run([git, "-C", str(workspace_copy), "apply", "--check", str(patch_path)], timeout=60)
    if not check.get("ok"):
        payload = {
            "ok": False,
            "summary": "Patch validation failed before Docker: patch does not apply cleanly",
            "run_id": run_id,
            "type": "patch_validation",
            "stage": "patch_check",
            "image": image,
            "command": command,
            "source_path": str(source),
            "patch_source": patch_source,
            "patch_path": str(patch_path),
            "patch_sha256": patch_sha256,
            "run_dir": str(run_dir),
            "workspace_copy": str(workspace_copy),
            "copy_info": copy_info,
            "raw": check,
        }
        _write_validation_report(run_dir, payload)
        _audit("patch_validate", {"ok": False, "run_id": run_id, "stage": "patch_check"})
        return payload
    apply_result = _run([git, "-C", str(workspace_copy), "apply", str(patch_path)], timeout=60)
    if not apply_result.get("ok"):
        payload = {
            "ok": False,
            "summary": "Patch validation failed before Docker: git apply failed",
            "run_id": run_id,
            "type": "patch_validation",
            "stage": "patch_apply",
            "image": image,
            "command": command,
            "source_path": str(source),
            "patch_source": patch_source,
            "patch_path": str(patch_path),
            "patch_sha256": patch_sha256,
            "run_dir": str(run_dir),
            "workspace_copy": str(workspace_copy),
            "copy_info": copy_info,
            "raw": apply_result,
        }
        _write_validation_report(run_dir, payload)
        _audit("patch_validate", {"ok": False, "run_id": run_id, "stage": "patch_apply"})
        return payload
    safe_command = (command or "python -m compileall -q winlocalassistant tests_*.py app.py").strip()
    args = [
        docker, "run", "--rm", "--network", "none", "--cpus", "2", "--memory", "3g", "--pids-limit", "768",
        "--security-opt", "no-new-privileges:true",
        "-v", f"{_docker_mount_path(workspace_copy)}:/workspace:rw",
        "-w", "/workspace", image or "python:3.12-slim", "sh", "-lc", safe_command,
    ]
    result = _run(args, timeout=max(1, min(int(timeout or 300), 1200)))
    payload = {
        "ok": bool(result.get("ok")),
        "summary": "Docker patch validation passed" if result.get("ok") else "Docker patch validation failed",
        "run_id": run_id,
        "type": "patch_validation",
        "stage": "docker_validate",
        "image": image,
        "command": safe_command,
        "source_path": str(source),
        "patch_source": patch_source,
        "patch_path": str(patch_path),
        "patch_sha256": patch_sha256,
        "run_dir": str(run_dir),
        "workspace_copy": str(workspace_copy),
        "copy_info": copy_info,
        "patch_apply": apply_result,
        "raw": result,
    }
    _write_validation_report(run_dir, payload)
    _audit("patch_validate", {"ok": bool(payload.get("ok")), "run_id": run_id, "image": image, "command": safe_command[:300]})
    return payload

def _save_status(payload: dict[str, Any]) -> None:
    try:
        atomic_write_json(DOCKER_LAST_STATUS_PATH, payload, ensure_ascii=True, indent=2)
    except Exception as exc:
        try:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        except Exception as log_exc:
            logging.getLogger(__name__).debug("Docker status persistence logging failed: %r", log_exc, exc_info=True)


def docker_validation_history(config: AssistantConfig, limit: int = 20) -> dict[str, Any]:
    """Return recent Docker validation reports saved by Nova.

    This is intentionally local-file based so it works even when Docker is
    currently offline.
    """
    runs: list[dict[str, Any]] = []
    limit = max(1, min(int(limit or 20), 100))
    if DOCKER_RUNS_DIR.exists():
        for run_dir in sorted([p for p in DOCKER_RUNS_DIR.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True):
            report_path = run_dir / "validation_report.json"
            if not report_path.exists():
                continue
            try:
                data = json.loads(report_path.read_text(encoding="utf-8"))
                if isinstance(data, dict):
                    runs.append({
                        "run_id": data.get("run_id") or run_dir.name,
                        "ok": bool(data.get("ok")),
                        "summary": data.get("summary", ""),
                        "type": data.get("type", "project_validation"),
                        "stage": data.get("stage", ""),
                        "command": data.get("command", ""),
                        "image": data.get("image", ""),
                        "patch_source": data.get("patch_source", ""),
                        "run_dir": str(run_dir),
                        "report_path": str(report_path),
                        "elapsed_sec": (data.get("raw") or {}).get("elapsed_sec"),
                        "modified_at": run_dir.stat().st_mtime,
                    })
            except Exception as exc:
                runs.append({"run_id": run_dir.name, "ok": False, "summary": "Could not read validation report", "run_dir": str(run_dir), "error": repr(exc), "modified_at": run_dir.stat().st_mtime})
            if len(runs) >= limit:
                break
    return {"ok": True, "summary": "Docker validation history loaded", "runs": runs, "limit": limit}


def docker_cleanup(config: AssistantConfig, keep: int = 20) -> dict[str, Any]:
    """Remove old Docker validation run folders, keeping the newest N reports."""
    keep = max(1, min(int(keep or 20), 100))
    removed: list[str] = []
    errors: list[dict[str, str]] = []
    if not DOCKER_RUNS_DIR.exists():
        return {"ok": True, "summary": "No Docker validation runs to clean", "removed": removed, "kept": 0}
    run_dirs = sorted([p for p in DOCKER_RUNS_DIR.iterdir() if p.is_dir()], key=lambda p: p.stat().st_mtime, reverse=True)
    for run_dir in run_dirs[keep:]:
        try:
            shutil.rmtree(run_dir)
            removed.append(str(run_dir))
        except Exception as exc:
            errors.append({"path": str(run_dir), "error": repr(exc)})
    _audit("cleanup", {"removed": len(removed), "errors": len(errors), "keep": keep})
    return {"ok": not errors, "summary": f"Docker validation cleanup removed {len(removed)} old run(s)", "removed": removed, "errors": errors, "kept": min(len(run_dirs), keep)}



def _load_validation_report_for_promotion(run_id: str = "") -> tuple[dict[str, Any], Path | None]:
    """Load a Docker validation report by run id, or the latest patch validation report.

    Promotion deliberately works from a saved report, not from a user-supplied
    patch path alone. That keeps the workflow tied to a prior copied-workspace
    validation result.
    """
    candidates: list[Path] = []
    if run_id:
        candidates.append(DOCKER_RUNS_DIR / run_id / "validation_report.json")
    elif DOCKER_RUNS_DIR.exists():
        candidates.extend(
            sorted(
                [p / "validation_report.json" for p in DOCKER_RUNS_DIR.iterdir() if (p / "validation_report.json").exists()],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
        )
    for report_path in candidates:
        try:
            data = json.loads(report_path.read_text(encoding="utf-8"))
            if isinstance(data, dict) and (run_id or data.get("type") == "patch_validation"):
                return data, report_path
        except Exception:
            continue
    return {}, None


def _write_promotion_report(promotion_dir: Path, payload: dict[str, Any]) -> None:
    promotion_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(promotion_dir / "promotion_report.json", payload, ensure_ascii=True, indent=2)
    lines = [
        "# Docker Patch Promotion Report",
        "",
        f"OK: **{bool(payload.get('ok'))}**",
        f"Summary: {payload.get('summary','')}",
        f"Validation run: `{payload.get('validation_run_id','')}`",
        f"Source path: `{payload.get('source_path','')}`",
        f"Patch: `{payload.get('patch_path','')}`",
    ]
    if payload.get("backup_dir"):
        lines.append(f"Backup/report folder: `{payload.get('backup_dir')}`")
    if payload.get("local_check"):
        check = payload.get("local_check") or {}
        lines += ["", "## Local post-promotion check", "```", str(check.get("stdout") or check.get("stderr") or check.get("error") or "")[-4000:], "```"]
    if payload.get("rollback"):
        lines += ["", "## Rollback", "```", json.dumps(payload.get("rollback"), indent=2)[:4000], "```"]
    atomic_write_json(promotion_dir / "promotion_report.machine.json", payload, ensure_ascii=True, indent=2)
    (promotion_dir / "promotion_report.md").write_text("\n".join(lines), encoding="utf-8")


def docker_promote_validated_patch(
    config: AssistantConfig,
    run_id: str = "",
    path: str = ".",
    local_command: str = "python -m compileall -q winlocalassistant tests_*.py app.py",
    rollback_on_failure: bool = True,
) -> dict[str, Any]:
    """Apply a previously Docker-validated patch to the live workspace.

    The guardrails are intentionally strict:
    - the saved validation report must be a passing patch_validation report;
    - the original patch from that run is used, not a new patch path;
    - `git apply --check` is rerun against the current live tree;
    - a promotion report folder is written before applying;
    - a local post-promotion validation command runs;
    - failed local validation attempts a reverse patch rollback.
    """
    report, report_path = _load_validation_report_for_promotion((run_id or "").strip())
    if not report:
        return {"ok": False, "summary": "No Docker patch validation report found to promote", "run_id": run_id, "hint": "Run /docker-validate-patch PATCH.diff first, then /docker-promote-patch RUN_ID."}
    validation_run_id = str(report.get("run_id") or run_id or "")
    if report.get("type") != "patch_validation":
        return {"ok": False, "summary": "Selected validation report is not a patch validation report", "validation_run_id": validation_run_id, "report_path": str(report_path or "")}
    if not bool(report.get("ok")):
        return {"ok": False, "summary": "Refusing to promote a patch because its Docker validation did not pass", "validation_run_id": validation_run_id, "report_path": str(report_path or ""), "validation_summary": report.get("summary", "")}
    patch_path = Path(str(report.get("patch_path") or ""))
    if not patch_path.exists():
        return {"ok": False, "summary": "Validated patch file is missing from the Docker run folder", "validation_run_id": validation_run_id, "patch_path": str(patch_path)}
    expected_patch_sha256 = str(report.get("patch_sha256") or "").strip()
    actual_patch_sha256 = _sha256_file(patch_path)
    if expected_patch_sha256 and actual_patch_sha256 != expected_patch_sha256:
        return {
            "ok": False,
            "summary": "Refusing to promote because the saved patch hash no longer matches its validation report",
            "validation_run_id": validation_run_id,
            "report_path": str(report_path or ""),
            "patch_path": str(patch_path),
            "expected_patch_sha256": expected_patch_sha256,
            "actual_patch_sha256": actual_patch_sha256,
            "hint": "Re-run /docker-validate-patch so the patch content and validation report are locked together again.",
        }
    source = Path(path or report.get("source_path") or ".").expanduser()
    if not source.is_absolute():
        source = (Path.cwd() / source).resolve()
    if not source.exists():
        return {"ok": False, "summary": "Live promotion path does not exist", "validation_run_id": validation_run_id, "source_path": str(source)}
    git = shutil.which("git") or ""
    if not git:
        return {"ok": False, "summary": "Git CLI not found; cannot safely apply or roll back patch", "validation_run_id": validation_run_id}
    promo_id = _short_id()
    promotion_dir = APP_DIR / "patch_promotions" / promo_id
    promotion_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(patch_path, promotion_dir / "promoted.patch")
    status_before = _run([git, "-C", str(source), "status", "--short"], timeout=20)
    diff_before = _run([git, "-C", str(source), "diff", "--binary"], timeout=30)
    try:
        (promotion_dir / "status_before.txt").write_text(str(status_before.get("stdout") or status_before.get("stderr") or ""), encoding="utf-8")
        (promotion_dir / "diff_before.patch").write_text(str(diff_before.get("stdout") or ""), encoding="utf-8")
    except Exception:
        logging.getLogger(__name__).debug("Could not write Docker promotion pre-apply snapshot", exc_info=True)
    apply_check_args = [git, "-C", str(source), "apply", "--check", str(patch_path)]
    apply_args = [git, "-C", str(source), "apply", str(patch_path)]
    live_check = _run(apply_check_args, timeout=60)
    # Windows worktrees often have CRLF conversion enabled. A patch generated in
    # the copied Docker/Linux workspace may be semantically correct but fail a
    # strict whitespace check on Windows. Retry with whitespace ignored before
    # rejecting a previously validated patch.
    if not live_check.get("ok"):
        live_check_relaxed = _run([git, "-C", str(source), "apply", "--check", "--ignore-whitespace", "--whitespace=nowarn", str(patch_path)], timeout=60)
        if live_check_relaxed.get("ok"):
            live_check = {**live_check_relaxed, "strict_check": live_check, "whitespace_relaxed": True}
            apply_args = [git, "-C", str(source), "apply", "--ignore-whitespace", "--whitespace=nowarn", str(patch_path)]
        else:
            payload = {
                "ok": False,
                "summary": "Validated patch no longer applies cleanly to the live tree",
                "validation_run_id": validation_run_id,
                "report_path": str(report_path or ""),
                "patch_path": str(patch_path),
                "patch_sha256": actual_patch_sha256,
                "source_path": str(source),
                "backup_dir": str(promotion_dir),
                "live_check": live_check,
                "live_check_relaxed": live_check_relaxed,
            }
            _write_promotion_report(promotion_dir, payload)
            _audit("promote_patch_blocked", {"ok": False, "run_id": validation_run_id, "reason": "live apply check failed"})
            return payload
    apply_result = _run(apply_args, timeout=60)
    if not apply_result.get("ok"):
        payload = {
            "ok": False,
            "summary": "Validated patch passed live check but git apply failed",
            "validation_run_id": validation_run_id,
            "report_path": str(report_path or ""),
            "patch_path": str(patch_path),
            "patch_sha256": actual_patch_sha256,
            "source_path": str(source),
            "backup_dir": str(promotion_dir),
            "apply_result": apply_result,
        }
        _write_promotion_report(promotion_dir, payload)
        _audit("promote_patch_failed", {"ok": False, "run_id": validation_run_id, "reason": "apply failed"})
        return payload
    command = (local_command or "").strip()
    local_check = {"ok": True, "summary": "No local post-promotion command requested", "stdout": "", "stderr": ""}
    rollback = None
    if command:
        local_check = _run_local_command(command, timeout=300, cwd=source)
    ok = bool(local_check.get("ok"))
    summary = "Validated patch promoted to live tree" if ok else "Patch applied but local post-promotion validation failed"
    if not ok and rollback_on_failure:
        rollback = _run([git, "-C", str(source), "apply", "-R", str(patch_path)], timeout=60)
        if rollback.get("ok"):
            summary += "; reverse patch rollback succeeded"
        else:
            summary += "; reverse patch rollback failed, inspect promotion report immediately"
    status_after = _run([git, "-C", str(source), "status", "--short"], timeout=20)
    payload = {
        "ok": ok,
        "summary": summary,
        "promotion_id": promo_id,
        "validation_run_id": validation_run_id,
        "report_path": str(report_path or ""),
        "patch_path": str(patch_path),
        "patch_sha256": actual_patch_sha256,
        "source_path": str(source),
        "backup_dir": str(promotion_dir),
        "status_before": status_before,
        "diff_before": {k: v for k, v in diff_before.items() if k != "stdout"},
        "live_check": live_check,
        "apply_result": apply_result,
        "local_command": command,
        "local_check": local_check,
        "rollback": rollback,
        "status_after": status_after,
    }
    _write_promotion_report(promotion_dir, payload)
    _audit("promote_patch", {"ok": bool(payload.get("ok")), "promotion_id": promo_id, "validation_run_id": validation_run_id, "rollback": bool(rollback)})
    return payload

def render_docker_history_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Docker Validation History", "", f"Runs shown: **{len(payload.get('runs') or [])}**"]
    runs = payload.get("runs") or []
    if not runs:
        lines.append("No Docker validation reports have been saved yet. Run `/docker-validate` first.")
        return "\n".join(lines)
    for row in runs:
        lines.append("")
        lines.append(f"- `{row.get('run_id','')}` — {'passed' if row.get('ok') else 'failed'} — `{row.get('image','')}`")
        if row.get("elapsed_sec") is not None:
            lines.append(f"  - Duration: {row.get('elapsed_sec')} sec")
        if row.get("command"):
            lines.append(f"  - Command: `{row.get('command')}`")
        if row.get("report_path"):
            lines.append(f"  - Report: `{row.get('report_path')}`")
    return "\n".join(lines)


def render_docker_cleanup_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Docker Validation Cleanup", "", payload.get("summary", "")]
    lines.append(f"Kept newest run folders: **{payload.get('kept', 0)}**")
    if payload.get("removed"):
        lines += ["", "Removed:"] + [f"- `{p}`" for p in payload.get("removed", [])[:30]]
    if payload.get("errors"):
        lines += ["", "Errors:"] + [f"- `{e.get('path')}`: {e.get('error')}" for e in payload.get("errors", [])[:10]]
    return "\n".join(lines)


def render_docker_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Docker Status", ""]
    lines.append(f"Docker CLI installed: **{bool(payload.get('installed'))}**")
    if payload.get("cli_path"):
        lines.append(f"CLI path: `{payload.get('cli_path')}`")
    lines.append(f"Docker daemon running: **{bool(payload.get('daemon_running'))}**")
    lines.append(f"Docker Compose available: **{bool(payload.get('compose_available'))}**")
    lines.append(f"Containers found: **{len(payload.get('containers') or [])}**")
    lines.append(f"Images found: **{len(payload.get('images') or [])}**")
    last_validation = payload.get("last_validation") or {}
    if isinstance(last_validation, dict) and last_validation:
        lines += ["", "## Last Docker validation"]
        lines.append(f"- Run: `{last_validation.get('run_id','')}`")
        lines.append(f"- OK: **{bool(last_validation.get('ok'))}**")
        lines.append(f"- Command: `{last_validation.get('command','')}`")
        if last_validation.get("run_dir"):
            lines.append(f"- Report folder: `{last_validation.get('run_dir')}`")
    history = payload.get("validation_history") or []
    if history:
        lines += ["", "## Recent validation runs"]
        for row in history[:8]:
            lines.append(f"- `{row.get('run_id','')}` — {'passed' if row.get('ok') else 'failed'} — `{row.get('command','')}`")
    notes = payload.get("notes") or []
    if notes:
        lines += ["", "## Notes"] + [f"- {n}" for n in notes]
    containers = payload.get("containers") or []
    if containers:
        lines += ["", "## Containers"]
        for row in containers[:20]:
            name = row.get("Names") or row.get("Name") or row.get("ID") or "container"
            status = row.get("Status") or row.get("State") or ""
            image = row.get("Image") or ""
            lines.append(f"- `{name}` — {status} — `{image}`")
    raw = payload.get("raw") or {}
    if raw:
        lines += ["", "## Raw diagnostics"]
        for key in ["docker_version", "docker_compose_version", "docker_info", "docker_ps", "docker_images", "wsl_list"]:
            item = raw.get(key)
            if not isinstance(item, dict):
                continue
            stdout = str(item.get("stdout") or "").strip()
            stderr = str(item.get("stderr") or "").strip()
            compact = stdout or stderr or str(item.get("error") or "")
            lines.append(f"### {key}")
            lines.append("```")
            lines.append(compact[-2500:] if compact else f"ok={item.get('ok')} returncode={item.get('returncode')}")
            lines.append("```")
    return "\n".join(lines)


def render_docker_setup_help() -> str:
    return """# Docker Integration Help

Nova can use Docker as an optional sandbox and diagnostics backend. Docker is not required for normal chat.

## Recommended first tests

```powershell
docker --version
docker compose version
docker info
docker ps -a
```

If PowerShell says `docker` is not recognised, install/start Docker Desktop and restart PowerShell or Nova.

## Nova commands

- `/docker-status` shows Docker, Compose, WSL, containers and raw diagnostics.
- `/docker-ps` lists containers.
- `/docker-smoke` runs `python --version` inside a disposable Python container.
- `/docker-validate` copies the current Nova folder into a temporary Docker validation workspace and runs compile checks there.
- `/docker-validate-patch PATCH.diff` applies a patch only inside a copied workspace and validates it in Docker before real files are touched.
- `/docker-history` shows recent validation run reports.
- `/docker-clean` removes old Docker validation run folders while keeping the newest reports.
- `/sandbox-status` remains the Linux/Kali sandbox status command.

## Design

Docker support is optional. Nova should run normally on Windows, then use Docker when it needs isolated code execution, clean dependency checks, or service orchestration.
"""
