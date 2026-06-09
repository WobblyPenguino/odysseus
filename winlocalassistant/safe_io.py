from __future__ import annotations

import json
import logging
import os
import shutil
import threading
import time
import uuid
from pathlib import Path
from typing import Any

_LOGGER = logging.getLogger(__name__)

_APPEND_LOCKS: dict[str, threading.Lock] = {}
_APPEND_LOCKS_GUARD = threading.Lock()


def _append_lock_for(path: Path) -> threading.Lock:
    key = str(Path(path).resolve())
    with _APPEND_LOCKS_GUARD:
        lock = _APPEND_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _APPEND_LOCKS[key] = lock
        return lock


def append_text_line(path: Path, line: str, *, encoding: str = "utf-8", fsync: bool = False) -> Path:
    """Append one logical line with an in-process lock.

    JSONL/event logs are append-heavy and should not use read+rewrite atomic
    replacement. This helper still improves integrity over scattered raw
    ``open("a")`` calls by centralising parent creation, newline handling and
    per-file locking so concurrent Nova threads do not interleave writes inside a
    process. Set ``fsync=True`` for critical low-volume journals.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    text = str(line)
    if not text.endswith("\n"):
        text += "\n"
    lock = _append_lock_for(path)
    with lock:
        with path.open("a", encoding=encoding) as handle:
            handle.write(text)
            handle.flush()
            if fsync:
                os.fsync(handle.fileno())
    return path


def open_binary_append_handle(path: Path):
    """Open a binary append handle for subprocess log capture.

    Most Nova append writes should use ``append_text_line``/``append_jsonl`` so
    newline and locking rules stay centralised. Long-running subprocess stdout
    redirection still needs a real file descriptor; this helper keeps parent
    creation and raw append mode in ``safe_io`` so call sites do not scatter
    direct ``open("ab")`` calls. The caller owns and must close the returned
    handle.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    return path.open("ab")


def append_jsonl(path: Path, payload: Any, *, ensure_ascii: bool = False, fsync: bool = False) -> Path:
    """Append a JSON object as one JSONL row using ``append_text_line``."""
    return append_text_line(path, json.dumps(payload, ensure_ascii=ensure_ascii, default=str), fsync=fsync)


def timestamp_id() -> str:
    """Return a sortable timestamp with enough entropy for repeated report writes."""
    return time.strftime("%Y%m%d_%H%M%S") + f"_{time.time_ns() % 1_000_000_000:09d}_{uuid.uuid4().hex[:6]}"


def unique_path(directory: Path, stem: str, suffix: str) -> Path:
    """Create a collision-safe path without creating the final file."""
    directory.mkdir(parents=True, exist_ok=True)
    suffix = suffix if suffix.startswith(".") else "." + suffix
    base = timestamp_id()
    path = directory / f"{stem}_{base}{suffix}"
    counter = 1
    while path.exists():
        path = directory / f"{stem}_{base}_{counter}{suffix}"
        counter += 1
    return path


def atomic_write_text(path, text, encoding="utf-8"):
    """Write text safely, creating the parent directory first.

    Uses a temp file when possible, then falls back to direct write if Windows
    blocks or loses the temp path during replace.
    """
    from pathlib import Path as _Path
    import os as _os
    import tempfile as _tempfile

    path = _Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    tmp_name = None
    try:
        fd, tmp_name = _tempfile.mkstemp(
            prefix="." + path.name + ".",
            suffix=".tmp",
            dir=str(path.parent),
            text=True,
        )
        with _os.fdopen(fd, "w", encoding=encoding) as handle:
            handle.write(text)
        _os.replace(tmp_name, str(path))
    except Exception:
        if tmp_name:
            try:
                _os.unlink(tmp_name)
            except Exception:
                _LOGGER.debug("Failed to remove temporary atomic-write file %s", tmp_name, exc_info=True)
        path.write_text(text, encoding=encoding)


def atomic_append_text(path: Path, text: str, *, encoding: str = "utf-8") -> Path:
    """Append text by atomically replacing a low-volume ledger/report file.

    Unlike ``append_text_line``, this preserves all existing file content in a
    single replacement write. It is intentionally locked per path so two Nova
    threads do not read the same old content and then overwrite each other's
    appended data.
    """
    path = Path(path)
    lock = _append_lock_for(path)
    with lock:
        existing = path.read_text(encoding=encoding) if path.exists() else ""
        return atomic_write_text(path, existing + text, encoding=encoding)


def atomic_write_bytes(path: Path, data: bytes) -> Path:
    """Write bytes atomically using a sibling temporary file."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with tmp.open("wb") as handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        last_error = None
        for attempt in range(8):
            try:
                tmp.replace(path)
                last_error = None
                break
            except PermissionError as exc:
                last_error = exc
                time.sleep(0.035 * (attempt + 1))
        if last_error is not None:
            raise last_error
    except Exception:
        try:
            tmp.unlink(missing_ok=True)
        except Exception as cleanup_exc:
            _LOGGER.debug("Failed to remove temporary atomic-write file", exc_info=cleanup_exc)
        raise
    return path


def atomic_write_json(path: Path, payload: Any, *, ensure_ascii: bool = False, indent: int = 2) -> Path:
    return atomic_write_text(path, json.dumps(payload, indent=indent, ensure_ascii=ensure_ascii), encoding="utf-8")


def quarantine_corrupt_file(path: Path, *, reason: str = "invalid_json") -> Path | None:
    """Copy a corrupt state file to a sibling quarantine backup.

    State readers often recover with defaults; without a copy, the original
    problem is invisible and can be overwritten by a later save. This keeps a
    forensic breadcrumb while still allowing Nova to start.
    """
    path = Path(path)
    if not path.exists() or not path.is_file():
        return None
    try:
        backup = unique_path(path.parent, f"{path.name}.{reason}.corrupt", ".bak")
        shutil.copy2(path, backup)
        return backup
    except Exception:
        _LOGGER.debug("Failed to quarantine corrupt state file %s", path, exc_info=True)
        return None


def read_json_file(
    path: Path,
    default: Any,
    *,
    expected_type: type | tuple[type, ...] | None = None,
    quarantine: bool = False,
) -> Any:
    """Read JSON with optional type validation and corrupt-file quarantine."""
    path = Path(path)
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if expected_type is not None and not isinstance(data, expected_type):
            raise TypeError(f"Expected JSON {expected_type}, got {type(data).__name__}")
        return data
    except Exception:
        if quarantine:
            quarantine_corrupt_file(path)
        return default


def tail_text_lines(path: Path, limit: int, *, encoding: str = "utf-8", errors: str = "replace") -> list[str]:
    """Return the last ``limit`` lines without loading an entire large log file.

    JSONL/activity logs can grow for a long-running assistant. Using
    ``Path.read_text().splitlines()`` for every status/context request scales
    with total log size rather than the small tail the UI needs. This helper
    reads from the end in chunks, preserving order, and falls back safely.
    """
    path = Path(path)
    try:
        n = max(0, int(limit))
    except Exception:
        n = 0
    if n <= 0 or not path.exists() or not path.is_file():
        return []
    chunk_size = 8192
    data = b""
    try:
        with path.open("rb") as handle:
            handle.seek(0, os.SEEK_END)
            pos = handle.tell()
            while pos > 0 and data.count(b"\n") <= n:
                read_size = min(chunk_size, pos)
                pos -= read_size
                handle.seek(pos)
                data = handle.read(read_size) + data
        return data.decode(encoding, errors=errors).splitlines()[-n:]
    except Exception:
        _LOGGER.debug("Failed to tail text lines from %s", path, exc_info=True)
        return []


def tail_jsonl_rows(path: Path, limit: int, *, multiplier: int = 3) -> list[dict[str, Any]]:
    """Return recent JSONL dict rows, skipping malformed/non-dict lines."""
    try:
        line_limit = max(1, int(limit) * max(1, int(multiplier)))
    except Exception:
        line_limit = 1
    rows: list[dict[str, Any]] = []
    for line in tail_text_lines(path, line_limit):
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    try:
        return rows[-max(1, int(limit)): ]
    except Exception:
        return rows
