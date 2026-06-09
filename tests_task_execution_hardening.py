from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.release_readiness import build_release_readiness
from winlocalassistant.task_execution import (
    autonomous_safety_snapshot,
    build_task_contract,
    build_task_execution_status,
    build_verify_summary,
    decompose_task,
    latest_task_evidence,
    record_failure_result,
    record_task_evidence,
    render_task_contract,
    repeated_failure_block,
)


def make_core(tmp_path: Path) -> AssistantCore:
    return AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, local_model_timeout_sec=0, chat_model_timeout_sec=0))


def test_task_contract_creation_and_broad_prompt_decomposition(tmp_path: Path):
    contract = build_task_contract("continue where it left off and improve Nova", root=tmp_path)
    assert contract.inferred_intent in {"broad_maintenance", "nova_source_edit"}
    assert contract.risk_level == "medium"
    assert contract.user_review_needed is True
    assert "inspect current files" in contract.task_plan[0]
    assert any("random new project" in item for item in contract.forbidden_actions)
    rendered = render_task_contract(contract)
    assert "Nova Task Contract" in rendered
    assert "Verification commands" in rendered
    assert decompose_task("fix bugs")[0].startswith("inspect")


def test_generation_intent_detection_one_file_project_and_nova_edit(tmp_path: Path):
    py_contract = build_task_contract("make one python file that bolds let", root=tmp_path)
    assert py_contract.inferred_intent == "file_write"
    assert py_contract.expected_outputs == ["script.py"]
    assert any("py_compile" in cmd for cmd in py_contract.verification_commands)

    game_contract = build_task_contract("make a browser game", root=tmp_path)
    assert game_contract.inferred_intent == "new_project"
    assert {"index.html", "style.css", "app.js"}.issubset(set(game_contract.expected_outputs))

    nova_contract = build_task_contract("add a feature to Nova", root=tmp_path)
    assert nova_contract.inferred_intent == "nova_source_edit"
    assert "winlocalassistant/" in nova_contract.target_files_or_folders
    assert any("release_readiness" in cmd for cmd in nova_contract.verification_commands)


def test_task_evidence_files_and_status(tmp_path: Path):
    evidence = record_task_evidence(
        tmp_path,
        action="unit_test_patch",
        command="python -m pytest -q tests_task_execution_hardening.py",
        files_changed=["winlocalassistant/task_execution.py"],
        tests_run=["python -m pytest -q tests_task_execution_hardening.py"],
        result="PASS",
        stdout="1 passed",
        verification_passed=True,
    )
    assert Path(evidence["json_path"]).exists()
    assert Path(evidence["markdown_path"]).exists()
    rows = latest_task_evidence(tmp_path)
    assert rows and rows[0]["action"] == "unit_test_patch"
    status = build_task_execution_status(tmp_path)
    assert status["status"] == "PASS"
    assert status["evidence_count"] >= 1


def test_repeated_failure_guard_blocks_after_two_identical_failures(tmp_path: Path):
    first = repeated_failure_block(tmp_path, "run_shell", "python missing_file.py")
    assert first.ok_to_run is True
    one = record_failure_result(tmp_path, "run_shell", "python missing_file.py", ok=False, output="No such file", returncode=2)
    assert one.count == 1 and one.repeated is False
    two = record_failure_result(tmp_path, "run_shell", "python missing_file.py", ok=False, output="No such file", returncode=2)
    assert two.repeated is True
    blocked = repeated_failure_block(tmp_path, "run_shell", "python missing_file.py")
    assert blocked.ok_to_run is False
    status = build_task_execution_status(tmp_path)
    assert status["status"] == "FAIL"


def test_verify_summary_and_core_routes_record_evidence(tmp_path: Path):
    core = make_core(tmp_path)
    write = core.handle_command("/write notes.txt hello")
    assert "evidence" in write.lower() or "wrote" in write.lower()
    verify = core.handle_command("/verify python --version")
    assert "verification" in verify.lower() or "python" in verify.lower()
    summary = core.handle_command("/verify")
    assert "Verify Summary" in summary
    status = core.handle_command("/task-evidence")
    assert "Task Execution Status" in status
    assert build_verify_summary(tmp_path)["final_result"] in {"PASS", "REVIEW"}


def test_core_task_contract_route_and_do_usage(tmp_path: Path):
    core = make_core(tmp_path)
    contract = core.handle_command("/task-contract fix bugs")
    assert "Nova Task Contract" in contract
    assert "inspect" in contract.lower()
    do_usage = core.handle_command("/do")
    assert "/task-contract" in do_usage


def test_autonomous_safety_snapshot_fields():
    snap = autonomous_safety_snapshot({"current_action": "fix Nova", "phase": "verify"}, allowed_to_edit=True, allowed_to_run=True, allowed_to_package=False)
    assert snap["current_task"] == "fix Nova"
    assert snap["current_step"] == "verify"
    assert snap["allowed_to_edit_files"] is True
    assert snap["allowed_to_package"] is False
    assert any("release-readiness" in item for item in snap["must_stop_conditions"])


def test_release_readiness_mentions_task_execution_category(tmp_path: Path, monkeypatch):
    import winlocalassistant.release_readiness as rr

    root = Path(__file__).resolve().parent

    def fake_run(root_arg, name, command, **kwargs):
        return rr._virtual(name, ok=True, required=kwargs.get("required", True), reason="unit test stub", category=kwargs.get("category", "general"))

    def fake_pytest(root_arg, name, selectors, **kwargs):
        return rr._virtual(name, ok=True, required=kwargs.get("required", True), reason="unit test pytest stub", category=kwargs.get("category", "tests"))

    monkeypatch.setattr(rr, "_run", fake_run)
    monkeypatch.setattr(rr, "_pytest", fake_pytest)
    payload = build_release_readiness(root, full=True, include_browser=False)
    assert "task_execution" in payload["category_status"]
    assert any("task contract" in check["name"] for check in payload["checks"])
