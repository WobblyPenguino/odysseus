from __future__ import annotations

import base64
import json
import shutil
import subprocess
import threading
import time
import urllib.error
import urllib.request
import uuid
from typing import Any

# Ollama will happily accept more than one HTTP request, but small local models
# often degrade, stall or return partial JSON if we pile prompts onto them.
# This process-wide lock makes Nova send ONE model prompt at a time.
_OLLAMA_LOCK = threading.Lock()
_OLLAMA_QUEUE_LOCK = threading.Lock()
_OLLAMA_QUEUE_DEPTH = 0
_OLLAMA_QUEUE_LAST_WAIT_SEC = 0.0
_OLLAMA_BUSY_SINCE: float | None = None
_OLLAMA_BUSY_DESC: str = ""
_OLLAMA_BUSY_REQUEST_ID: str = ""
_OLLAMA_COOLDOWN_UNTIL: float | None = None
_OLLAMA_LAST: dict[str, Any] = {
    "request_id": "",
    "desc": "",
    "started_at": None,
    "finished_at": None,
    "duration_sec": 0,
    "result": "never_called",
    "received_chars": 0,
    "timed_out_or_error": False,
}


def ollama_busy_state() -> dict[str, Any]:
    now = time.time()
    cooldown_for = round(max(0.0, (_OLLAMA_COOLDOWN_UNTIL or 0) - now), 1)
    busy = _OLLAMA_LOCK.locked() or cooldown_for > 0
    return {
        "busy": busy,
        "queue_depth": _OLLAMA_QUEUE_DEPTH,
        "last_queue_wait_sec": _OLLAMA_QUEUE_LAST_WAIT_SEC,
        "prompt_active": _OLLAMA_LOCK.locked(),
        "cooldown_active": cooldown_for > 0,
        "cooldown_for_sec": cooldown_for,
        "busy_since": _OLLAMA_BUSY_SINCE,
        "busy_for_sec": round(now - _OLLAMA_BUSY_SINCE, 1) if _OLLAMA_BUSY_SINCE else 0,
        "busy_desc": _OLLAMA_BUSY_DESC,
        "request_id": _OLLAMA_BUSY_REQUEST_ID,
        "last_prompt": dict(_OLLAMA_LAST),
        "note": "ollama ps can show a loaded model after a prompt has finished; Nova prompt_active/cooldown is the source of truth for whether it is still sending a prompt.",
    }


def _acquire_ollama_lane(*, model: str, desc: str, queue_timeout_sec: float | None = 900.0) -> tuple[bool, float]:
    """Queue local model calls instead of failing when another Nova agent is prompting.

    Multi-agent orchestration may run many deterministic workers at once, but Ollama
    is fragile when the same local model receives overlapping prompts. This helper
    gives every model-bound worker a turn instead of returning None immediately.
    """
    global _OLLAMA_QUEUE_DEPTH, _OLLAMA_QUEUE_LAST_WAIT_SEC
    start = time.time()
    with _OLLAMA_QUEUE_LOCK:
        _OLLAMA_QUEUE_DEPTH += 1
    try:
        timeout = None if queue_timeout_sec is None or float(queue_timeout_sec) <= 0 else float(queue_timeout_sec)
        acquired = _OLLAMA_LOCK.acquire(timeout=timeout) if timeout is not None else _OLLAMA_LOCK.acquire()
        _OLLAMA_QUEUE_LAST_WAIT_SEC = round(time.time() - start, 3)
        if not acquired:
            _OLLAMA_LAST.update({
                "request_id": "",
                "desc": desc,
                "started_at": start,
                "finished_at": time.time(),
                "duration_sec": round(time.time() - start, 2),
                "result": "queue_timeout",
                "received_chars": 0,
                "timed_out_or_error": True,
                "model": model,
                "error": f"Timed out waiting for Ollama prompt lane after {timeout} seconds",
            })
        return bool(acquired), _OLLAMA_QUEUE_LAST_WAIT_SEC
    finally:
        with _OLLAMA_QUEUE_LOCK:
            _OLLAMA_QUEUE_DEPTH = max(0, _OLLAMA_QUEUE_DEPTH - 1)


def _set_last(request_id: str, desc: str, started: float, result: str, received_chars: int = 0, timed_out_or_error: bool = False) -> None:
    _OLLAMA_LAST.update({
        "request_id": request_id,
        "desc": desc,
        "started_at": started,
        "finished_at": time.time(),
        "duration_sec": round(time.time() - started, 2),
        "result": result,
        "received_chars": received_chars,
        "timed_out_or_error": timed_out_or_error,
    })


def _set_last_error(
    request_id: str,
    desc: str,
    started: float,
    result: str,
    error: str,
    *,
    received_chars: int = 0,
    timed_out_or_error: bool = True,
) -> None:
    _set_last(request_id, desc, started, result, received_chars, timed_out_or_error)
    _OLLAMA_LAST["error"] = error[:2000]


def _log_ollama_preflight(kind: str, message: str, payload: dict[str, Any]) -> None:
    """Best-effort logging that still records logger failures for diagnostics."""
    try:
        from .eventlog import log_activity

        log_activity(kind, message, payload)
    except Exception as exc:
        _OLLAMA_LAST["preflight_log_error"] = repr(exc)
        _OLLAMA_LAST["preflight_log_kind"] = kind


def _try_stop_stopping_model(model: str) -> None:
    """Best-effort cleanup for an Ollama model stuck in Stopping before a new prompt."""
    if _OLLAMA_LOCK.locked():
        return
    exe = shutil.which("ollama")
    if not exe:
        return
    try:
        cp = subprocess.run([exe, "ps"], capture_output=True, text=True, timeout=6)
    except Exception as exc:
        _OLLAMA_LAST["preflight_ps_error"] = repr(exc)
        return
    raw = ((cp.stdout or "") + (cp.stderr or "")).strip()
    model_key = (model or "").lower()
    model_family = model_key.split(":", 1)[0]
    stopping = [
        line for line in raw.splitlines()
        if "stopping" in line.lower() and (model_key in line.lower() or (model_family and model_family in line.lower()))
    ]
    if not stopping:
        return
    try:
        stop = subprocess.run([exe, "stop", model], capture_output=True, text=True, timeout=10)
        _log_ollama_preflight("ollama_preflight_stop_stale", "Stopped stale Ollama model before starting a new prompt", {
            "model": model,
            "returncode": stop.returncode,
            "output": ((stop.stdout or "") + (stop.stderr or "")).strip()[:1000],
            "ps_line": stopping[0][:1000],
        })
    except Exception as exc:
        _log_ollama_preflight("ollama_preflight_stop_stale_failed", "Could not stop stale Ollama model before prompt", {
            "model": model,
            "error": repr(exc),
            "ps_line": stopping[0][:1000],
        })


def ollama_chat(
    base_url: str,
    model: str,
    messages: list[dict[str, str]],
    timeout: int | None = 180,
    desc: str = "local model call",
    keep_alive: str = "30s",
    cooldown_sec: float = 2.0,
    timeout_quarantine_sec: float = 25.0,
) -> str | None:
    """Call Ollama through /api/chat with strict single-prompt lifecycle tracking.

    Important detail: `ollama ps` can continue to show the model after the HTTP
    response has completed because Ollama keeps the model loaded for a while.
    That does NOT mean Nova is still prompting it. This function
    exposes prompt_active/cooldown state so the UI can show the difference.

    If the HTTP call times out/errors, we hold a short quarantine cooldown before
    releasing the prompt lane, because the server may still be finishing or
    cleaning up the abandoned request. v45 normally disables local Ollama HTTP timeouts so long generations can return.
    """
    global _OLLAMA_BUSY_SINCE, _OLLAMA_BUSY_DESC, _OLLAMA_BUSY_REQUEST_ID, _OLLAMA_COOLDOWN_UNTIL

    now = time.time()
    if _OLLAMA_COOLDOWN_UNTIL and now < _OLLAMA_COOLDOWN_UNTIL:
        return None
    _try_stop_stopping_model(model)

    acquired, queue_wait_sec = _acquire_ollama_lane(model=model, desc=desc, queue_timeout_sec=900.0)
    if not acquired:
        return None

    request_id = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    started = time.time()
    _OLLAMA_BUSY_SINCE = started
    _OLLAMA_BUSY_DESC = desc
    _OLLAMA_BUSY_REQUEST_ID = request_id
    _OLLAMA_LAST.update({
        "request_id": request_id,
        "desc": desc,
        "started_at": started,
        "finished_at": None,
        "duration_sec": 0,
        "result": "running",
        "received_chars": 0,
        "timed_out_or_error": False,
        "queue_wait_sec": queue_wait_sec,
    })
    try:
        url = base_url.rstrip("/") + "/api/chat"
        payload = json.dumps({
            "model": model,
            "messages": messages,
            "stream": False,
            "keep_alive": keep_alive,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=(None if timeout is None or int(timeout) <= 0 else timeout)) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data: Any = json.loads(raw)
                content = data.get("message", {}).get("content") or data.get("response") or ""
                _set_last(request_id, desc, started, "ok", len(content), False)
                _OLLAMA_COOLDOWN_UNTIL = time.time() + max(0.0, cooldown_sec)
                return content
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            _set_last_error(request_id, desc, started, f"http_{exc.code}", body or repr(exc), timed_out_or_error=True)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            _set_last_error(request_id, desc, started, "timeout_or_error", repr(exc), timed_out_or_error=True)
    finally:
        _OLLAMA_BUSY_SINCE = None
        _OLLAMA_BUSY_DESC = ""
        _OLLAMA_BUSY_REQUEST_ID = ""
        _OLLAMA_LOCK.release()


def ollama_vision_chat(
    base_url: str,
    model: str,
    prompt: str,
    image_paths: list[str],
    timeout: int | None = 180,
    desc: str = "local vision model call",
    keep_alive: str = "30s",
    cooldown_sec: float = 2.0,
    timeout_quarantine_sec: float = 25.0,
) -> str | None:
    """Call Ollama vision-capable models through /api/chat using image inputs.

    This uses the same single-prompt lock as text generation. Ollama vision-capable
    models accept base64-encoded images in the message `images` field. If the
    selected model is not a vision model, Ollama will usually return an error or
    an unhelpful response; callers should surface that clearly rather than hiding
    the problem.
    """
    global _OLLAMA_BUSY_SINCE, _OLLAMA_BUSY_DESC, _OLLAMA_BUSY_REQUEST_ID, _OLLAMA_COOLDOWN_UNTIL

    now = time.time()
    if _OLLAMA_COOLDOWN_UNTIL and now < _OLLAMA_COOLDOWN_UNTIL:
        return None
    _try_stop_stopping_model(model)

    acquired, queue_wait_sec = _acquire_ollama_lane(model=model, desc=desc, queue_timeout_sec=900.0)
    if not acquired:
        return None

    request_id = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    started = time.time()
    _OLLAMA_BUSY_SINCE = started
    _OLLAMA_BUSY_DESC = desc
    _OLLAMA_BUSY_REQUEST_ID = request_id
    _OLLAMA_LAST.update({
        "request_id": request_id,
        "desc": desc,
        "started_at": started,
        "finished_at": None,
        "duration_sec": 0,
        "result": "running",
        "received_chars": 0,
        "timed_out_or_error": False,
        "queue_wait_sec": queue_wait_sec,
    })
    try:
        images: list[str] = []
        for image_path in image_paths:
            with open(image_path, "rb") as f:
                images.append(base64.b64encode(f.read()).decode("ascii"))
        url = base_url.rstrip("/") + "/api/chat"
        payload = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt, "images": images}],
            "stream": False,
            "keep_alive": keep_alive,
        }).encode("utf-8")
        req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
        try:
            with urllib.request.urlopen(req, timeout=(None if timeout is None or int(timeout) <= 0 else timeout)) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data: Any = json.loads(raw)
                content = data.get("message", {}).get("content") or data.get("response") or ""
                _set_last(request_id, desc, started, "ok", len(content), False)
                _OLLAMA_COOLDOWN_UNTIL = time.time() + max(0.0, cooldown_sec)
                return content
        except urllib.error.HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")
            _set_last_error(request_id, desc, started, f"http_{exc.code}", body or repr(exc), timed_out_or_error=True)
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError) as exc:
            _set_last_error(request_id, desc, started, "timeout_or_error", repr(exc), timed_out_or_error=True)
    finally:
        _OLLAMA_BUSY_SINCE = None
        _OLLAMA_BUSY_DESC = ""
        _OLLAMA_BUSY_REQUEST_ID = ""
        _OLLAMA_LOCK.release()
