from __future__ import annotations

import json
import shutil
import subprocess
import sys
import threading
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .eventlog import log_activity
from .ollama import ollama_busy_state
from .safe_io import atomic_write_json, read_json_file

WATCHDOG_PATH = APP_DIR / "watchdog_status.json"
_WATCHDOG_THREAD: threading.Thread | None = None
_WATCHDOG_STOP = threading.Event()
_WATCHDOG_INTERVAL = 30


def heartbeat(config: Any, workspace: Path) -> dict[str, Any]:
    APP_DIR.mkdir(parents=True, exist_ok=True)
    ollama = {"available": False, "active_models": [], "raw": ""}
    exe = shutil.which("ollama")
    if exe:
        try:
            cp = subprocess.run([exe, "ps"], capture_output=True, text=True, timeout=6)
            raw = ((cp.stdout or "") + (cp.stderr or "")).strip()
            ollama = {
                "available": cp.returncode == 0,
                "returncode": cp.returncode,
                "raw": raw,
                "active_models": [line for line in raw.splitlines()[1:] if line.strip()],
            }
        except Exception as exc:
            ollama = {"available": False, "error": repr(exc), "active_models": []}
    disk = shutil.disk_usage(str(workspace if workspace.exists() else Path.home()))
    data = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "python": sys.version.split()[0],
        "workspace": str(workspace),
        "workspace_exists": workspace.exists(),
        "allow_mutating_tools": bool(getattr(config, "allow_mutating_tools", False)),
        "model": getattr(config, "model", ""),
        "ollama_url": getattr(config, "ollama_url", ""),
        "ollama": ollama,
        "llm_prompt_lock": ollama_busy_state(),
        "disk_free_gb": round(disk.free / (1024**3), 2),
        "status": "ok" if workspace.exists() and ollama.get("available") else "attention",
    }
    atomic_write_json(WATCHDOG_PATH, data, ensure_ascii=True)
    log_activity("heartbeat", "Watchdog heartbeat", data)
    return data


def start_watchdog(config: Any, workspace: Path, interval: int = 30) -> dict[str, Any]:
    global _WATCHDOG_THREAD, _WATCHDOG_INTERVAL
    _WATCHDOG_INTERVAL = max(10, int(interval or 30))
    if _WATCHDOG_THREAD and _WATCHDOG_THREAD.is_alive():
        return {"running": True, "message": "watchdog already running", "interval": _WATCHDOG_INTERVAL}
    _WATCHDOG_STOP.clear()

    def loop() -> None:
        while not _WATCHDOG_STOP.wait(_WATCHDOG_INTERVAL):
            try:
                heartbeat(config, workspace)
            except Exception as exc:
                log_activity("heartbeat_failed", "Watchdog heartbeat failed", {"error": repr(exc)})

    _WATCHDOG_THREAD = threading.Thread(target=loop, name="NovaWatchdog", daemon=True)
    _WATCHDOG_THREAD.start()
    first = heartbeat(config, workspace)
    return {"running": True, "interval": _WATCHDOG_INTERVAL, "first": first}


def stop_watchdog() -> dict[str, Any]:
    _WATCHDOG_STOP.set()
    return {"running": False, "message": "watchdog stop requested"}


def watchdog_state() -> dict[str, Any]:
    data = {"running": bool(_WATCHDOG_THREAD and _WATCHDOG_THREAD.is_alive()), "status_file": str(WATCHDOG_PATH)}
    if WATCHDOG_PATH.exists():
        try:
            data["last"] = read_json_file(WATCHDOG_PATH, {}, expected_type=dict, quarantine=True)
        except Exception:
            import logging as _wla_logging
            _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)
    return data
