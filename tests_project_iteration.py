from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant.project_iteration import (
    ProjectIterationEvent,
    append_project_iteration_event,
    build_project_iteration_event,
    is_repeated_repair,
    proposed_files_digest,
    write_project_verification_report,
)
from winlocalassistant.tools import ToolResult


def test_project_iteration_event_log_appends_jsonl() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        path = append_project_iteration_event(root, ProjectIterationEvent(0, "initial", False, "failed", problems=["missing score"]))
        append_project_iteration_event(root, {"round_no": 1, "stage": "repair", "ok": True, "summary": "passed"})
        rows = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines()]
    assert len(rows) == 2
    assert rows[0]["stage"] == "initial"
    assert rows[0]["problems"] == ["missing score"]
    assert rows[1]["ok"] is True


def test_project_verification_report_contains_timeline_and_final_json() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        event = ProjectIterationEvent(1, "post_repair", True, "Project quality verification passed", changed_files=["app.js"], quality_percent=92)
        path = write_project_verification_report(root, "make a game", "passed", [event], {"quality_score": {"overall_percent": 92}})
        text = path.read_text(encoding="utf-8")
    assert "Project Verification and Iteration Report" in text
    assert "make a game" in text
    assert "Round 1 - post_repair" in text
    assert "app.js" in text
    assert '"overall_percent": 92' in text


def test_build_iteration_event_extracts_failed_check_problem() -> None:
    result = ToolResult(False, "Runtime probe failed", {"checks": [{"name": "project_runtime_probe", "ok": False, "problems": ["missing restart"]}], "runtime_probe": {"percent": 50}})
    event = build_project_iteration_event(2, "verify", result)
    assert event.ok is False
    assert event.quality_percent == 50
    assert any("project_runtime_probe" in problem for problem in event.problems)


def test_repeated_repair_detection_uses_stable_digest() -> None:
    seen: set[str] = set()
    files = {"app.js": "console.log('fix')"}
    assert proposed_files_digest(files) == proposed_files_digest({"app.js": "console.log('fix')"})
    assert is_repeated_repair(files, seen) is False
    assert is_repeated_repair(files, seen) is True
