from __future__ import annotations

import re
import time
import uuid
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, read_json_file

CONVERSATIONS_PATH = APP_DIR / "conversations.json"
MAX_MESSAGES_PER_CONVERSATION = 120


def _safe_title(title: str) -> str:
    title = re.sub(r"\s+", " ", str(title or "")).strip()
    return title[:80] or "New chat"


def _load() -> dict[str, Any]:
    data = read_json_file(CONVERSATIONS_PATH, {}, expected_type=dict, quarantine=True)
    if not isinstance(data, dict):
        data = {}
    data.setdefault("active_id", "")
    data.setdefault("conversations", {})
    return data


def _save(data: dict[str, Any]) -> None:
    CONVERSATIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(CONVERSATIONS_PATH, data, ensure_ascii=False)


def ensure_active_conversation() -> dict[str, Any]:
    data = _load()
    active_id = str(data.get("active_id") or "")
    convs = data.setdefault("conversations", {})
    if active_id and active_id in convs:
        return convs[active_id]
    cid = time.strftime("chat_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    conv = {"id": cid, "title": "Main chat", "created_at": time.strftime("%Y-%m-%d %H:%M:%S"), "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "messages": []}
    convs[cid] = conv
    data["active_id"] = cid
    _save(data)
    return conv


def active_conversation_id() -> str:
    return str(ensure_active_conversation().get("id") or "")


def list_conversations(limit: int = 30) -> dict[str, Any]:
    data = _load()
    convs = list((data.get("conversations") or {}).values())
    convs.sort(key=lambda c: str(c.get("updated_at") or c.get("created_at") or ""), reverse=True)
    return {"ok": True, "active_id": data.get("active_id", ""), "conversations": convs[:max(1, int(limit))]}


def create_conversation(title: str = "New chat", make_active: bool = True) -> dict[str, Any]:
    data = _load()
    cid = time.strftime("chat_%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    now = time.strftime("%Y-%m-%d %H:%M:%S")
    conv = {"id": cid, "title": _safe_title(title), "created_at": now, "updated_at": now, "messages": []}
    data.setdefault("conversations", {})[cid] = conv
    if make_active:
        data["active_id"] = cid
    _save(data)
    return {"ok": True, "conversation": conv, "active_id": data.get("active_id", "")}


def switch_conversation(identifier: str) -> dict[str, Any]:
    ident = (identifier or "").strip()
    data = _load()
    convs = data.get("conversations") or {}
    if ident in convs:
        data["active_id"] = ident
        _save(data)
        return {"ok": True, "conversation": convs[ident], "active_id": ident}
    low = ident.lower()
    matches = [c for c in convs.values() if low and low in str(c.get("title") or "").lower()]
    if len(matches) == 1:
        data["active_id"] = matches[0]["id"]
        _save(data)
        return {"ok": True, "conversation": matches[0], "active_id": matches[0]["id"]}
    return {"ok": False, "summary": "Conversation not found or ambiguous", "matches": matches[:10]}


def append_message(role: str, content: str, *, conversation_id: str | None = None) -> dict[str, Any]:
    data = _load()
    convs = data.setdefault("conversations", {})
    cid = conversation_id or str(data.get("active_id") or "")
    if not cid or cid not in convs:
        conv = ensure_active_conversation()
        data = _load()
        convs = data.setdefault("conversations", {})
        cid = conv["id"]
    conv = convs[cid]
    msg = {"role": str(role), "content": str(content or "")[:20000], "time": time.strftime("%Y-%m-%d %H:%M:%S"), "ts": time.time()}
    conv.setdefault("messages", []).append(msg)
    conv["messages"] = conv["messages"][-MAX_MESSAGES_PER_CONVERSATION:]
    if role == "user" and (not conv.get("title") or conv.get("title") == "New chat"):
        conv["title"] = _safe_title(content)[:70]
    conv["updated_at"] = msg["time"]
    convs[cid] = conv
    data["active_id"] = cid
    _save(data)
    return {"ok": True, "conversation_id": cid, "message": msg}


def get_active_messages(limit: int = 40) -> list[dict[str, str]]:
    conv = ensure_active_conversation()
    msgs = conv.get("messages") or []
    return [{"role": str(m.get("role") or "user"), "content": str(m.get("content") or "")} for m in msgs[-max(1, int(limit)):]]


def search_conversations(query: str, limit: int = 20) -> dict[str, Any]:
    q = (query or "").lower().strip()
    terms = [t for t in re.findall(r"[a-z0-9_\-]{3,}", q)]
    rows: list[dict[str, Any]] = []
    data = _load()
    for conv in (data.get("conversations") or {}).values():
        text = (str(conv.get("title") or "") + "\n" + "\n".join(str(m.get("content") or "") for m in conv.get("messages") or [])).lower()
        score = sum(1 for t in terms if t in text) if terms else 0
        if score:
            rows.append({"id": conv.get("id"), "title": conv.get("title"), "updated_at": conv.get("updated_at"), "score": score})
    rows.sort(key=lambda r: (-int(r.get("score") or 0), str(r.get("updated_at") or "")), reverse=False)
    return {"ok": True, "query": query, "matches": rows[:max(1, int(limit))]}



def rename_conversation(identifier: str, title: str) -> dict[str, Any]:
    """Rename a saved backend conversation by id or unique title fragment."""
    title = _safe_title(title or "Renamed chat")[:90]
    data = _load()
    convs = data.get("conversations") or {}
    target_id = ""
    if identifier in convs:
        target_id = identifier
    else:
        low = (identifier or "").strip().lower()
        matches = [c for c in convs.values() if low and low in str(c.get("title") or "").lower()]
        if len(matches) == 1:
            target_id = str(matches[0].get("id") or "")
    if not target_id or target_id not in convs:
        return {"ok": False, "summary": "Conversation not found or ambiguous"}
    convs[target_id]["title"] = title
    convs[target_id]["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
    _save(data)
    return {"ok": True, "conversation": convs[target_id], "active_id": data.get("active_id", "")}


def delete_conversation(identifier: str) -> dict[str, Any]:
    """Delete a saved backend conversation. If it was active, switch to another or create a new chat."""
    data = _load()
    convs = data.setdefault("conversations", {})
    target_id = ""
    if identifier in convs:
        target_id = identifier
    else:
        low = (identifier or "").strip().lower()
        matches = [c for c in convs.values() if low and low in str(c.get("title") or "").lower()]
        if len(matches) == 1:
            target_id = str(matches[0].get("id") or "")
    if not target_id or target_id not in convs:
        return {"ok": False, "summary": "Conversation not found or ambiguous"}
    deleted = convs.pop(target_id)
    if data.get("active_id") == target_id:
        data["active_id"] = next(iter(convs.keys()), "")
    _save(data)
    if not data.get("active_id"):
        created = create_conversation("New chat", make_active=True)
        return {"ok": True, "deleted": deleted, "active_id": created.get("active_id"), "created_replacement": True}
    return {"ok": True, "deleted": deleted, "active_id": data.get("active_id")}
