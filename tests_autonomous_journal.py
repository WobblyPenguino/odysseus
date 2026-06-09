from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant.autonomous_journal import (
    build_run_journal,
    latest_run_journal,
    make_step_event,
    redact_journal_value,
    render_run_journal_markdown,
    summarize_args,
    write_run_journal,
)


def test_step_event_summarizes_large_args() -> None:
    ev = make_step_event(run_id="r1", cycle=2, step_index=1, title="Build", tool="ai_create_project", status="ok", args={"goal": "x" * 600})
    assert ev.args_summary
    assert len(ev.args_summary) < 340
    assert ev.run_id == "r1"


def test_run_journal_counts_failures_and_next_action() -> None:
    events = [
        make_step_event(run_id="r2", cycle=1, step_index=1, title="Inspect", tool="auto_verify", status="ok"),
        make_step_event(run_id="r2", cycle=1, step_index=2, title="Build", tool="ai_create_project", status="failed", failure_category="model_error"),
        make_step_event(run_id="r2", cycle=1, step_index=3, title="Zip", tool="zip_path", status="skipped_previous_failed"),
    ]
    journal = build_run_journal("r2", 1, "make a useful app", events)
    assert journal.status == "failed_with_report"
    assert journal.executed_steps == 2
    assert journal.skipped_steps == 1
    assert journal.failed_steps == 1
    assert journal.next_recommended_action == "inspect_failure_memory_or_repair_proposal"


def test_journal_writes_markdown_and_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        events = [make_step_event(run_id="r3", cycle=3, step_index=1, title="Verify", tool="auto_verify", status="ok", summary="passed")]
        journal = build_run_journal("r3", 3, "verify project", events)
        md, js = write_run_journal(journal, Path(tmp))
        assert md.exists()
        assert js.exists()
        assert "# Autonomous Sequence Journal" in md.read_text(encoding="utf-8")
        data = json.loads(js.read_text(encoding="utf-8"))
        assert data["run_id"] == "r3"
        assert data["events"][0]["tool"] == "auto_verify"
        latest_path, latest_data = latest_run_journal(Path(tmp))
        assert latest_path == js
        assert latest_data and latest_data["status"] == "completed"


def test_render_journal_includes_review_counts() -> None:
    journal = build_run_journal(
        "r4",
        4,
        "run risky command",
        [make_step_event(run_id="r4", cycle=4, step_index=1, title="Shell", tool="run_shell", status="blocked", watcher_status="blocked")],
    )
    text = render_run_journal_markdown(journal)
    assert "Blocked/review-required: 1" in text
    assert "needs_user_review" in text


def test_summarize_args_handles_unserializable_values() -> None:
    text = summarize_args({"path": Path("abc")})
    assert "abc" in text


def test_journal_args_redact_secrets() -> None:
    text = summarize_args({"api_key": "sk-secret", "nested": {"authorization": "Bearer abc123"}, "url": "x?token=abc"})
    assert "sk-secret" not in text
    assert "abc123" not in text
    assert "token=abc" not in text
    assert "[REDACTED]" in text
    cleaned = redact_journal_value({"password": "pw", "ok": "value"})
    assert cleaned["password"] == "[REDACTED]"
    assert cleaned["ok"] == "value"


def test_latest_run_journal_skips_corrupt_newest_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        directory = Path(tmp)
        older = directory / "autonomous_sequence_journal_older.json"
        newer = directory / "autonomous_sequence_journal_newer.json"
        older.write_text(json.dumps({"run_id": "older", "status": "completed"}), encoding="utf-8")
        newer.write_text("{not json", encoding="utf-8")
        # Ensure newer has later mtime.
        newer.touch()
        path, data = latest_run_journal(directory)
        assert path == older
        assert data and data["run_id"] == "older"


def run_all(verbose: bool = False) -> None:
    for fn in [
        test_step_event_summarizes_large_args,
        test_run_journal_counts_failures_and_next_action,
        test_journal_writes_markdown_and_json,
        test_render_journal_includes_review_counts,
        test_summarize_args_handles_unserializable_values,
        test_journal_args_redact_secrets,
        test_latest_run_journal_skips_corrupt_newest_file,
    ]:
        fn()
        if verbose:
            print(f"PASS {fn.__name__}")
