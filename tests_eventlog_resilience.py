from __future__ import annotations

import json
from pathlib import Path

import winlocalassistant.eventlog as eventlog


def test_log_activity_redacts_nested_sensitive_values(tmp_path, monkeypatch):
    path = tmp_path / "activity.jsonl"
    monkeypatch.setattr(eventlog, "ACTIVITY_PATH", path)
    eventlog.log_activity(
        "secret_test",
        "token=abc123456789 should not leak",
        {"nested": {"api_key": "sk-test-secret", "note": "Bearer abcdefghijklmnop"}},
    )
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    payload = json.dumps(row, ensure_ascii=False).lower()
    assert "sk-test-secret" not in payload
    assert "abcdefghijklmnop" not in payload
    assert "abc123456789" not in payload
    assert "[redacted]" in payload


def test_log_model_io_redacts_prompt_response_and_data(tmp_path, monkeypatch):
    path = tmp_path / "model_io.jsonl"
    monkeypatch.setattr(eventlog, "MODEL_IO_PATH", path)
    eventlog.log_model_io(
        "prompt",
        prompt="use Authorization: Bearer abcdefgh12345678",
        response="password=supersecretvalue",
        data={"token": "local-token-secret"},
    )
    row = json.loads(path.read_text(encoding="utf-8").splitlines()[-1])
    payload = json.dumps(row, ensure_ascii=False).lower()
    assert "abcdefgh12345678" not in payload
    assert "supersecretvalue" not in payload
    assert "local-token-secret" not in payload
    assert "[redacted]" in payload


def test_logging_failures_do_not_crash(tmp_path, monkeypatch):
    blocker = tmp_path / "not_a_dir"
    blocker.write_text("blocks mkdir", encoding="utf-8")
    monkeypatch.setattr(eventlog, "ACTIVITY_PATH", blocker / "activity.jsonl")
    monkeypatch.setattr(eventlog, "MODEL_IO_PATH", blocker / "model_io.jsonl")
    eventlog.log_activity("x", "message", {"secret": "value"})
    eventlog.log_model_io("x", prompt="api_key=abc12345")


def test_tail_jsonl_handles_unreadable_or_corrupt_content(tmp_path):
    missing = tmp_path / "missing.jsonl"
    assert eventlog.tail_jsonl(missing) == []
    path = tmp_path / "bad.jsonl"
    path.write_text("not json api_key=abc12345\n", encoding="utf-8")
    rows = eventlog.tail_jsonl(path)
    assert rows
    assert "abc12345" not in json.dumps(rows, ensure_ascii=False)


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        # pytest-style tests needing fixtures are intentionally covered by pytest.
        if fn.__code__.co_argcount:
            continue
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
