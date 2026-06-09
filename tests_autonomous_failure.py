from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant.autonomous_failure import (
    AutonomousFailureMemory,
    AutonomousFailureRecord,
    classify_autonomous_failure,
    clear_autonomous_cooldowns_for_action,
    detect_unsafe_suggestions,
    load_autonomous_failure_memory,
    make_failure_signature,
    save_autonomous_failure_memory,
    should_cooldown_autonomous_action,
    update_autonomous_failure_memory,
    write_autonomous_repair_proposal,
)
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
import winlocalassistant.tools as tools_module
import winlocalassistant.core as core_module
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolResult


def _record(signature: str = "") -> AutonomousFailureRecord:
    signature = signature or make_failure_signature("Improve current project", "improve_project", "goal", ".", "timeout")
    return AutonomousFailureRecord(
        cycle_id="1",
        action_name="Improve current project",
        tool_name="improve_project",
        command_summary="goal",
        target=".",
        success=False,
        failure_category="timeout",
        error_summary="PowerShell command timed out",
        duration_seconds=120.0,
        timestamp="2026-05-24 10:00:00",
        signature=signature,
        recommended_next_action="diagnose_recent_failure",
    )


def test_failure_classification_categories() -> None:
    assert classify_autonomous_failure(timed_out=True) == "timeout"
    assert classify_autonomous_failure("command failed with exit code 1") == "command_error"
    assert classify_autonomous_failure("verification failed: tests failed") == "verification_failed"
    assert classify_autonomous_failure(no_useful_edits=True) == "no_useful_edits"
    assert classify_autonomous_failure("failed before useful edits", no_useful_edits=True) == "no_useful_edits"
    assert classify_autonomous_failure("same signature failed and action is on cooldown") == "repeated_failed_action"
    assert classify_autonomous_failure("Cannot find path missing file") == "missing_file"
    assert classify_autonomous_failure("access denied permission blocked") == "permission_blocked"
    assert classify_autonomous_failure("ollama failed during prompt") == "model_error"


def test_failure_signature_is_deterministic_and_safe() -> None:
    a = make_failure_signature("Improve current project", "improve_project", ".\\OrganizeFiles.ps1", ".", "timeout")
    b = make_failure_signature("Improve current project", "improve_project", ".\\OrganizeFiles.ps1", ".", "timeout")
    assert a == b
    assert a == a.lower()
    assert " " not in a
    assert len(a) <= 90


def test_memory_save_load_and_corrupt_recovery() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autofail_") as tmp:
        path = Path(tmp) / "memory.json"
        memory = update_autonomous_failure_memory(AutonomousFailureMemory(), _record())
        save_autonomous_failure_memory(path, memory)
        loaded = load_autonomous_failure_memory(path)
        assert len(loaded.recent_failures) == 1
        assert loaded.last_failure_summary == "PowerShell command timed out"
        path.write_text("{broken", encoding="utf-8")
        recovered = load_autonomous_failure_memory(path)
        assert recovered.recent_failures == []


def test_repeated_failure_creates_cooldown() -> None:
    rec = _record()
    memory = update_autonomous_failure_memory(AutonomousFailureMemory(), rec)
    memory = update_autonomous_failure_memory(memory, _record(rec.signature))
    on_cooldown, reason = should_cooldown_autonomous_action(memory, rec.signature)
    assert on_cooldown
    assert "cooldown" in reason
    assert memory.last_suggested_fix == "diagnose_recent_failure"


def test_success_clears_matching_autonomous_failure_cooldown() -> None:
    rec = _record()
    memory = update_autonomous_failure_memory(AutonomousFailureMemory(), rec)
    memory = update_autonomous_failure_memory(memory, _record(rec.signature))
    assert should_cooldown_autonomous_action(memory, rec.signature)[0] is True
    cleared = clear_autonomous_cooldowns_for_action(
        memory,
        "Improve current project",
        "improve_project",
        "goal",
        ".",
    )
    assert should_cooldown_autonomous_action(cleared, rec.signature)[0] is False
    assert not any(item.signature == rec.signature for item in cleared.recent_failures)



def test_repair_proposal_writer_creates_markdown_json_with_required_headings() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autorepair_") as tmp:
        payload = write_autonomous_repair_proposal(
            Path(tmp),
            _record(),
            local_model_diagnosis="Smallest fix: inspect the timed-out script and avoid repeating it.",
            repeated_failure=True,
            verification_commands=["python tests_smoke.py"],
        )
        md = Path(payload["markdown_path"])
        js = Path(payload["json_path"])
        assert md.exists()
        assert js.exists()
        text = md.read_text(encoding="utf-8")
        for heading in [
            "# Autonomous Repair Proposal",
            "## Failure Summary",
            "## Failure Category",
            "## Repeated Failure Check",
            "## Local Model Surgical Diagnosis",
            "## Proposed Smallest Fix",
            "## Unsafe Suggestions Rejected",
            "## Verification Plan",
            "## Next Recommended Command",
            "## Do Not Repeat Until",
        ]:
            assert heading in text
        data = json.loads(js.read_text(encoding="utf-8"))
        assert data["repeated_failure"] is True


def test_local_model_unavailable_still_writes_report_and_unsafe_rejected() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autorepair_unavailable_") as tmp:
        payload = write_autonomous_repair_proposal(
            Path(tmp),
            _record(),
            local_model_error="model unavailable",
        )
        text = Path(payload["markdown_path"]).read_text(encoding="utf-8")
        assert "unavailable" in text.lower()
        unsafe = detect_unsafe_suggestions("Do a broad rewrite, disable tests, pip install things, and call /self-improve automatically.")
        assert "broad rewrite" in unsafe
        assert "disable tests" in unsafe
        assert "call /self-improve automatically" in unsafe


def test_unsafe_suggestions_cover_permissions_network_auto_apply_and_rollback() -> None:
    unsafe = detect_unsafe_suggestions(
        "Remove safety checks, bypass permissions, enable internet, auto-apply edits, and remove rollback."
    )
    assert "delete safety checks" in unsafe
    assert "bypass permissions" in unsafe
    assert "network access without explicit user approval" in unsafe
    assert "apply source edits automatically" in unsafe
    assert "remove backup/rollback" in unsafe


def test_autonomous_call_tool_failure_records_memory_and_report() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autonomous_hook_") as tmp:
        profile = Path(tmp) / "profile"
        reports = profile / "autonomous_repair_proposals"
        failure_path = profile / "AUTONOMOUS_FAILURE_MEMORY.json"
        old_failure_path = core_module.AUTONOMOUS_FAILURE_MEMORY_PATH
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        old_model_chat = core_module.model_chat
        try:
            core_module.AUTONOMOUS_FAILURE_MEMORY_PATH = failure_path
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            core_module.model_chat = lambda *args, **kwargs: "Smallest fix: inspect the failed command and choose a different diagnostic."

            core = object.__new__(AssistantCore)
            core.config = AssistantConfig(workspace=tmp)
            core.autonomous_state = {
                "cycle": 7,
                "events": [],
                "repair_proposal_written_this_cycle": False,
            }
            core._set_autonomous_state = lambda **updates: core.autonomous_state.update(updates)
            core._select_model_for = lambda purpose: "test-model"

            class FailingTools:
                def call(self, tool: str, **kwargs):
                    del tool, kwargs
                    return ToolResult(False, "verification failed: tests failed", {"error": "tests failed"})

            core.tools = FailingTools()
            result = core._autonomous_call_tool("Run failing check", "verify", {"command": "python tests_smoke.py"}, [], "run-1")
            memory = load_autonomous_failure_memory(failure_path)
            report_files = list(reports.glob("autonomous_repair_proposal_*.md"))
        finally:
            core_module.AUTONOMOUS_FAILURE_MEMORY_PATH = old_failure_path
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity
            core_module.model_chat = old_model_chat

    assert result.ok is False
    assert memory.recent_failures
    assert memory.recent_failures[-1].failure_category == "verification_failed"
    assert core.autonomous_state["repair_proposal_written_this_cycle"] is True
    assert report_files


def test_autonomous_memory_command_includes_failure_memory() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_autonomous_memory_cmd_") as tmp:
        profile = Path(tmp)
        cycle_path = profile / "AUTONOMOUS_CYCLE_MEMORY.jsonl"
        cycle_path.write_text('{"failure":"old cycle row"}\n', encoding="utf-8")
        failure_path = profile / "AUTONOMOUS_FAILURE_MEMORY.json"
        memory = update_autonomous_failure_memory(AutonomousFailureMemory(), _record())
        save_autonomous_failure_memory(failure_path, memory)

        old_app_dir = tools_module.APP_DIR
        old_failure_path = tools_module.AUTONOMOUS_FAILURE_MEMORY_PATH
        try:
            tools_module.APP_DIR = profile
            tools_module.AUTONOMOUS_FAILURE_MEMORY_PATH = failure_path
            result = ToolRegistry(AssistantConfig(workspace=tmp)).autonomous_memory()
        finally:
            tools_module.APP_DIR = old_app_dir
            tools_module.AUTONOMOUS_FAILURE_MEMORY_PATH = old_failure_path

    assert result.ok
    assert result.data["rows"]
    assert result.data["recent_failures"]
    assert result.data["failure_memory_path"] == str(failure_path)


def test_autonomous_guide_contains_failure_and_stop_guidance() -> None:
    guide = Path("docs/NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md").read_text(encoding="utf-8")
    low = guide.lower()
    assert "repeated" in low
    assert "verification ladder" in low
    assert "local-model repair" in low or "local-model" in low
    assert "stop conditions" in low


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
