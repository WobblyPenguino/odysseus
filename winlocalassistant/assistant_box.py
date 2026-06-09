from __future__ import annotations

import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, read_json_file

from .config import APP_DIR

BOX_PATH = APP_DIR / "assistant_message_box.json"
MAX_MESSAGE_CHARS = 12000
MAX_HISTORY = 60


@dataclass
class AssistantBoxEntry:
    ts: float
    time: str
    source: str
    level: str
    message: str


def _now_entry(message: str, source: str = "assistant", level: str = "info") -> AssistantBoxEntry:
    cleaned = str(message or "").strip()
    if len(cleaned) > MAX_MESSAGE_CHARS:
        cleaned = cleaned[:MAX_MESSAGE_CHARS] + "\n...[truncated]"
    level = str(level or "info").strip().lower()
    if level not in {"info", "success", "warning", "error", "debug"}:
        level = "info"
    return AssistantBoxEntry(
        ts=time.time(),
        time=time.strftime("%Y-%m-%d %H:%M:%S"),
        source=str(source or "assistant").strip()[:80] or "assistant",
        level=level,
        message=cleaned,
    )


def _default_state() -> dict[str, Any]:
    return {
        "ok": True,
        "message": "",
        "source": "system",
        "level": "info",
        "updated_at": "",
        "updated_ts": 0.0,
        "history": [],
    }


def read_assistant_box() -> dict[str, Any]:
    try:
        if not BOX_PATH.exists():
            return _default_state()
        data = read_json_file(BOX_PATH, _default_state(), expected_type=dict, quarantine=True)
        if not isinstance(data, dict):
            return _default_state()
        state = _default_state()
        state.update(data)
        if not isinstance(state.get("history"), list):
            state["history"] = []
        return state
    except Exception as exc:
        state = _default_state()
        state.update({"ok": False, "message": f"Assistant message box could not be read: {exc}", "level": "error"})
        return state


def write_assistant_box(message: str, source: str = "assistant", level: str = "info", append: bool = False) -> dict[str, Any]:
    entry = _now_entry(message, source=source, level=level)
    previous = read_assistant_box()
    history = list(previous.get("history") or [])
    history.append(asdict(entry))
    visible_message = entry.message
    if append and str(previous.get("message") or "").strip():
        visible_message = (str(previous.get("message") or "").rstrip() + "\n\n" + entry.message).strip()
        if len(visible_message) > MAX_MESSAGE_CHARS:
            visible_message = visible_message[-MAX_MESSAGE_CHARS:]
    state = {
        "ok": True,
        "message": visible_message,
        "source": entry.source,
        "level": entry.level,
        "updated_at": entry.time,
        "updated_ts": entry.ts,
        "history": history[-MAX_HISTORY:],
    }
    BOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(BOX_PATH, state, ensure_ascii=False)
    return state


def clear_assistant_box(source: str = "assistant") -> dict[str, Any]:
    state = _default_state()
    state.update({
        "message": "",
        "source": str(source or "assistant")[:80],
        "level": "info",
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_ts": time.time(),
        "history": [],
    })
    BOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(BOX_PATH, state, ensure_ascii=False)
    return state
