from __future__ import annotations

import json
import tempfile
from pathlib import Path

import winlocalassistant.core as core_module
from winlocalassistant.core import AssistantCore
from winlocalassistant.idle_engine import append_idle_event
from winlocalassistant.tools import ToolResult


class _FakeIdleTools:
    def __init__(self, profile: Path):
        self.profile = profile
        self.calls: list[str] = []

    def call(self, tool: str, **kwargs):
        del kwargs
        self.calls.append(tool)
        if tool == "investigate_logs":
            (self.profile / "ERROR_INVESTIGATION.md").write_text("traceback failed exception", encoding="utf-8")
        if tool == "propose_improvements":
            (self.profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        if tool == "self_improvement_queue":
            (self.profile / "SELF_IMPROVEMENT_QUEUE.md").write_text("self-improve should review rollback", encoding="utf-8")
        return ToolResult(True, f"{tool} ok", {})


def _make_idle_core(profile: Path) -> AssistantCore:
    core = object.__new__(AssistantCore)
    core.idle_state = {
        "enabled": False,
        "running": False,
        "stop_requested": False,
        "paused_for_user": False,
        "cycle": 0,
        "last_started": None,
        "last_finished": None,
        "last_summary": "Idle mode is off.",
        "last_error": "",
        "events": [],
        "current_action": "Idle",
        "current_detail": "Idle mode is off.",
    }
    core.avatar_state = {"mood": "ready", "emoji": "", "title": "Ready", "text": ""}
    core.tools = _FakeIdleTools(profile)
    core._idle_thread = None
    return core


def _read_events(profile: Path) -> list[dict]:
    path = profile / "idle_logs" / "idle_events.jsonl"
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def test_append_idle_event_writes_valid_jsonl() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_events_") as tmp:
        profile = Path(tmp) / "profile"
        path = append_idle_event(profile, {"event": "unit_test_event", "path": Path("reports/example.md")})
        events = _read_events(profile)

    assert path.name == "idle_events.jsonl"
    assert len(events) == 1
    assert events[0]["event"] == "unit_test_event"
    assert "timestamp" in events[0]
    assert events[0]["path"].replace("\\", "/") == "reports/example.md"


def test_append_idle_event_appends_multiple_lines_and_redacts_content() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_events_multi_") as tmp:
        profile = Path(tmp) / "profile"
        append_idle_event(profile, {"event": "first", "source_contents": "full source should not be logged"})
        append_idle_event(profile, {"event": "second", "prompt": "full prompt should not be logged"})
        events = _read_events(profile)

    assert [item["event"] for item in events] == ["first", "second"]
    assert events[0]["source_contents"] == "[redacted]"
    assert events[1]["prompt"] == "[redacted]"
    assert all("timestamp" in item for item in events)


def test_idle_once_appends_started_and_completed_events() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_once_events_") as tmp:
        profile = Path(tmp) / "profile"
        profile.mkdir()
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            core = _make_idle_core(profile)
            reply = core._idle_once("inspect idle events")
        finally:
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

        events = _read_events(profile)

    event_names = [item["event"] for item in events]
    assert "idle_cycle_started" in event_names
    assert "idle_cycle_completed" in event_names
    assert "No source files were modified by idle mode." in reply
    assert "self_improve" not in core.tools.calls


def test_idle_propose_appends_started_and_completed_events() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_propose_events_") as tmp:
        profile = Path(tmp) / "profile"
        profile.mkdir()
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            core = _make_idle_core(profile)
            reply = core.idle_command("propose inspect idle events")
        finally:
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

        events = _read_events(profile)

    event_names = [item["event"] for item in events]
    assert "idle_proposal_started" in event_names
    assert "idle_proposal_completed" in event_names
    assert "proposal_written" in event_names
    assert "No source files were modified by idle propose." in reply
    assert "self_improve" not in core.tools.calls


def test_idle_event_logging_failure_does_not_crash_idle_once() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_event_fail_") as tmp:
        profile = Path(tmp) / "profile"
        profile.mkdir()
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        old_append_idle_event = core_module.append_idle_event
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None

            def fail_append(*args, **kwargs):
                del args, kwargs
                raise OSError("event log unavailable")

            core_module.append_idle_event = fail_append
            core = _make_idle_core(profile)
            reply = core._idle_once("inspect idle logging failure")
        finally:
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity
            core_module.append_idle_event = old_append_idle_event

    assert "No source files were modified by idle mode." in reply
    assert "Idle JSONL event logging warning" in reply


def run_all(verbose: bool = False) -> None:
    tests = [
        (name, fn)
        for name, fn in sorted(globals().items())
        if name.startswith("test_") and callable(fn)
    ]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
