from __future__ import annotations

import json
import re
import time
import uuid
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import append_jsonl, tail_text_lines

ACTIVITY_PATH = APP_DIR / "activity.jsonl"
MODEL_IO_PATH = APP_DIR / "model_io.jsonl"
SESSION_ID = time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:8]
_CURRENT_RUN_ID: str | None = None

SENSITIVE_KEYS = {
    "api_key", "apikey", "token", "password", "passwd", "secret", "authorization",
    "auth", "bearer", "openrouter_api_key", "hf_token", "key",
}
_TOKEN_PATTERNS = [
    re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),
    re.compile(r"(?i)(api[_-]?key|token|password|passwd|secret|authorization)\s*[:=]\s*[^\s,;&\"']{4,}"),
]


def new_run_id() -> str:
    return time.strftime("%Y%m%d_%H%M%S") + "_" + uuid.uuid4().hex[:6]


def set_current_run(run_id: str | None) -> None:
    global _CURRENT_RUN_ID
    _CURRENT_RUN_ID = run_id


def current_run_id() -> str | None:
    return _CURRENT_RUN_ID


def _redact_text(text: str) -> str:
    redacted = text
    for pattern in _TOKEN_PATTERNS:
        redacted = pattern.sub(lambda m: (m.group(1) + "=[redacted]") if m.lastindex else "Bearer [redacted]", redacted)
    return redacted


def _redact(obj: Any) -> Any:
    if isinstance(obj, dict):
        out: dict[str, Any] = {}
        for key, value in obj.items():
            key_text = str(key)
            if any(secret in key_text.lower() for secret in SENSITIVE_KEYS):
                out[key_text] = "[redacted]"
            else:
                out[key_text] = _redact(value)
        return out
    if isinstance(obj, list):
        return [_redact(item) for item in obj]
    if isinstance(obj, tuple):
        return [_redact(item) for item in obj]
    if isinstance(obj, str):
        return _redact_text(obj)
    return obj


def _safe(obj: Any, max_chars: int = 12000) -> Any:
    """Return JSON-safe event data with secrets redacted and bounded size."""
    try:
        text = json.dumps(_redact(obj), ensure_ascii=False, default=str)
    except Exception:
        text = _redact_text(repr(obj))
    if len(text) > max_chars:
        text = text[:max_chars] + "...<truncated>"
    try:
        return json.loads(text)
    except Exception:
        return text


def _append_jsonl(path: Path, row: dict[str, Any]) -> None:
    """Best-effort append used by logging paths.

    Logging must never take down chat, autonomous cycles, or verification. If the
    profile directory is read-only or a log file is temporarily locked, the caller
    should still continue safely.
    """
    try:
        append_jsonl(path, row, ensure_ascii=False)
    except Exception:
        return


def log_activity(kind: str, message: str, data: dict[str, Any] | None = None) -> None:
    row = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ts": time.time(),
        "session_id": SESSION_ID,
        "run_id": _CURRENT_RUN_ID,
        "kind": kind,
        "message": _redact_text(message),
        "data": _safe(data or {}),
    }
    _append_jsonl(ACTIVITY_PATH, row)


def log_model_io(phase: str, prompt: str = "", response: str = "", data: dict[str, Any] | None = None) -> None:
    row = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "ts": time.time(),
        "session_id": SESSION_ID,
        "run_id": _CURRENT_RUN_ID,
        "phase": phase,
        "prompt_preview": _redact_text(prompt)[:8000],
        "response_preview": _redact_text(response)[:20000],
        "data": _safe(data or {}),
    }
    _append_jsonl(MODEL_IO_PATH, row)


def tail_jsonl(path: Path, limit: int = 80, *, session_only: bool = False, since_ts: float | None = None) -> list[dict[str, Any]]:
    if not path.exists():
        return []
    lines = tail_text_lines(path, max(int(limit) * 20, int(limit)))
    out: list[dict[str, Any]] = []
    for line in lines:
        try:
            row = json.loads(line)
            if not isinstance(row, dict):
                row = {"time": "", "kind": "raw", "message": _redact_text(line), "data": {}}
        except Exception:
            row = {"time": "", "kind": "raw", "message": _redact_text(line), "data": {}}
        if session_only and row.get("session_id") not in {SESSION_ID, None}:
            continue
        if since_ts is not None:
            try:
                row_ts = float(row.get("ts") or 0)
            except Exception:
                row_ts = 0.0
            if row_ts < since_ts:
                continue
        out.append(row)
    return out[-int(limit):]


def delete_activity_runs(run_ids: list[str]) -> dict[str, Any]:
    """Remove selected run rows from activity/model logs.

    This is a GUI cleanup helper only. It does not touch project files, model output
    files, reports, or hidden run IDs stored elsewhere.
    """
    wanted = {str(r) for r in (run_ids or []) if str(r).strip()}
    if not wanted:
        return {"deleted": 0, "requested": [], "files": []}

    def filter_jsonl(path: Path, key: str) -> dict[str, Any]:
        if not path.exists():
            return {"path": str(path), "deleted": 0, "kept": 0, "existed": False}
        kept: list[str] = []
        deleted = 0
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
            for line in lines:
                try:
                    row = json.loads(line)
                    rid = str(row.get("run_id") or (row.get("data") or {}).get("run_id") or "")
                except Exception:
                    rid = ""
                if rid in wanted:
                    deleted += 1
                else:
                    kept.append(line)
            path.write_text(("\n".join(kept) + ("\n" if kept else "")), encoding="utf-8")
            return {"path": str(path), "deleted": deleted, "kept": len(kept), "existed": True}
        except Exception as exc:
            return {"path": str(path), "deleted": deleted, "kept": len(kept), "existed": True, "error": repr(exc)}

    results = [filter_jsonl(ACTIVITY_PATH, "run_id"), filter_jsonl(MODEL_IO_PATH, "run_id")]
    return {"requested": sorted(wanted), "deleted": sum(int(r.get("deleted") or 0) for r in results), "files": results}
