from __future__ import annotations

import ast
import json
import threading
from pathlib import Path

from winlocalassistant.action_watcher import record_action_outcome
from winlocalassistant.safe_io import append_jsonl, append_text_line


ALLOWED_RAW_OPEN_FILES = {"winlocalassistant/safe_io.py"}


def test_append_jsonl_handles_concurrent_writes(tmp_path: Path) -> None:
    path = tmp_path / "events.jsonl"

    def worker(offset: int) -> None:
        for i in range(20):
            append_jsonl(path, {"idx": offset + i, "text": "hello"})

    threads = [threading.Thread(target=worker, args=(i * 100,)) for i in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()

    rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 80
    assert all("idx" in row for row in rows)


def test_append_text_line_normalises_newlines(tmp_path: Path) -> None:
    path = tmp_path / "notes.log"
    append_text_line(path, "one")
    append_text_line(path, "two\n")
    assert path.read_text(encoding="utf-8") == "one\ntwo\n"


def test_action_watcher_uses_safe_jsonl_append(tmp_path: Path) -> None:
    path = tmp_path / "watcher.jsonl"
    record_action_outcome({"name": "status"}, {"ok": True}, path=path)
    row = json.loads(path.read_text(encoding="utf-8"))
    assert row["action"]["name"] == "status"
    assert row["decision"]["status"] in {"allow", "review-required"}


def test_no_raw_append_open_calls_outside_safe_io() -> None:
    offenders: list[str] = []
    for path in Path("winlocalassistant").rglob("*.py"):
        rel = path.as_posix()
        if rel in ALLOWED_RAW_OPEN_FILES:
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if isinstance(func, ast.Attribute) and func.attr == "open":
                for arg in list(node.args) + [kw.value for kw in node.keywords if kw.arg == "mode"]:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str) and "a" in arg.value:
                        offenders.append(f"{rel}:{node.lineno}")
    assert offenders == []
