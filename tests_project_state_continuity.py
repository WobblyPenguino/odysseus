from __future__ import annotations

import json
from pathlib import Path

from winlocalassistant.command_help import command_help_payload
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.project_state import (
    build_autonomous_continuity_status,
    build_continue_context_reply,
    build_project_state_snapshot,
    check_project_state_contract,
    render_project_state_command,
)
from winlocalassistant.task_execution import record_task_evidence
from winlocalassistant.release_readiness import build_release_readiness


def _seed_readiness(root: Path, status: str = "PASS") -> None:
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    payload = {
        "ok": status == "PASS",
        "status": status,
        "summary": "PASS: safe to package" if status == "PASS" else "FAIL: do not ship",
        "created_at": "2026-06-09 00:00:00",
        "required_failed": [] if status == "PASS" else ["compileall"],
        "optional_failed": [],
        "category_status": {"chat": "PASS"},
    }
    (docs / "NOVA_RELEASE_READINESS_LATEST.json").write_text(json.dumps(payload), encoding="utf-8")


def test_project_state_snapshot_writes_markdown_and_json(tmp_path: Path):
    _seed_readiness(tmp_path)
    record_task_evidence(
        tmp_path,
        action="verify",
        command="python -m compileall winlocalassistant",
        files_changed=["winlocalassistant/project_state.py"],
        tests_run=["python -m compileall winlocalassistant"],
        result="PASS",
        verification_passed=True,
    )
    payload = build_project_state_snapshot(tmp_path, write=True)
    assert payload["current_version"]
    assert payload["latest_release_readiness"]["status"] == "PASS"
    assert payload["packaging_allowed"] is True
    assert "winlocalassistant/project_state.py" in payload["latest_changed_files"]
    assert Path(payload["latest_json"]).exists()
    assert Path(payload["latest_markdown"]).exists()
    assert "Safe next action" in Path(payload["latest_markdown"]).read_text(encoding="utf-8")


def test_project_state_json_and_next_commands(tmp_path: Path):
    _seed_readiness(tmp_path)
    record_task_evidence(tmp_path, action="verify", result="PASS", verification_passed=True)
    rendered = render_project_state_command("--next", root=tmp_path)
    assert "Nova Continue / Next Step" in rendered
    raw_json = render_project_state_command("--json", root=tmp_path)
    data = json.loads(raw_json)
    assert data["current_version"]
    assert data["continue_readiness"] in {"PASS", "REVIEW", "FAIL"}


def test_continue_again_prompt_uses_project_state(tmp_path: Path):
    _seed_readiness(tmp_path)
    record_task_evidence(tmp_path, action="verify", result="PASS", verification_passed=True)
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False, local_model_timeout_sec=0, chat_model_timeout_sec=0))
    reply = core.chat("again")
    assert "Current version" in reply
    assert "Last release-readiness verdict" in reply
    assert "Safest next action" in reply


def test_latest_task_evidence_fields_are_backwards_compatible(tmp_path: Path):
    _seed_readiness(tmp_path)
    evidence = record_task_evidence(
        tmp_path,
        action="shell",
        command="python --version",
        files_changed=["README.md"],
        tests_run=["python --version"],
        result="PASS",
        verification_passed=True,
    )
    assert evidence["changed_files"] == ["README.md"]
    assert evidence["verification_commands"] == ["python --version"]
    assert evidence["review_status"] == "PASS"
    payload = build_project_state_snapshot(tmp_path, write=True)
    assert payload["latest_task_evidence"][0]["changed_files"] == ["README.md"]


def test_autonomous_continuity_guard_blocks_failed_last_task(tmp_path: Path):
    _seed_readiness(tmp_path)
    record_task_evidence(tmp_path, action="verify", result="FAIL", verification_passed=False, user_review_needed=True)
    continuity = build_autonomous_continuity_status(tmp_path)
    assert continuity["safe_to_continue_automatically"] is False
    assert continuity["blockers"]
    assert "last task result" in continuity["stop_reason"]


def test_release_readiness_includes_project_state_check(tmp_path: Path):
    _seed_readiness(tmp_path)
    # Run against real repo root because readiness selectors expect the test files to exist.
    payload = build_release_readiness(Path.cwd(), full=True, include_browser=False)
    names = [c["name"] for c in payload["checks"]]
    assert "project-state snapshot and continue-readiness status" in names
    assert "project_state" in payload["category_status"]


def test_command_help_includes_project_state_commands():
    payload = command_help_payload("project-state")
    commands = {item["command"] for items in payload["categories"].values() for item in items}
    assert "/project-state" in commands
    assert "/project-state --next" in commands


def test_project_state_contract_function(tmp_path: Path):
    _seed_readiness(tmp_path)
    record_task_evidence(tmp_path, action="verify", result="PASS", verification_passed=True)
    message = check_project_state_contract(tmp_path)
    assert "Project-state snapshot written" in message


