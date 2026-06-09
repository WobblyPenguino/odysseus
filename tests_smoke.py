from __future__ import annotations

import tempfile
import json
import os
from pathlib import Path

from winlocalassistant import __version__
from winlocalassistant.config import AssistantConfig
import winlocalassistant.core as core_module
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry, ToolResult
import winlocalassistant.tools as tools_module
import tests_format_result
import tests_idle_engine
import tests_idle_events
import tests_self_improve_guardrails
import tests_webui_idle_status
import tests_autonomous_failure
import tests_command_suggestions
import tests_creation_intent
import tests_request_intent
import tests_tool_guides
import tests_surgical_fallback
import tests_project_quality_ui
import tests_autonomous_memory_robustness
import tests_project_behaviour_contract
import tests_v52_roadmap
import tests_intent_planning
import tests_task_decomposition
import tests_project_quality_score
import tests_webui_planning_visibility
import tests_project_acceptance
import tests_game_design
import tests_project_runtime_probe
import tests_project_iteration
import tests_v52_7_iteration
import tests_v52_5_roadmap
import tests_release_hygiene
import tests_quality_dashboard
import tests_action_watcher
import tests_tool_catalog_interaction_learning
import tests_planning_dashboard
import tests_model_json_recovery
import tests_feature_continuity
import tests_autonomous_explain
import tests_autonomous_sequence
import tests_timeout_resilience
import tests_autonomous_journal
import tests_self_awareness
import tests_report_hygiene
import tests_command_verifier
import tests_command_contract_download
import tests_eventlog_resilience
import tests_model_health_timeout
import tests_architecture_audit
import tests_v55_ux_game
import tests_file_context
import tests_improvement_features_v55_3_124
import tests_nova_inspiration_v55_3_125
import tests_nova_coding_v55_3_126
import tests_nova_agent_upgrade_v55_3_127
import tests_nova_deep_research_v55_3_129
import tests_nova_route_resilience_v55_3_130
import tests_nova_improvement_assurance_v55_3_131
import tests_nova_capability_drift_v55_3_132
import tests_nova_reliability_v55_3_128


def test_core_starts() -> None:
    core = AssistantCore.load()
    out = core.chat("/status")
    assert "workspace" in out.lower()


def test_version_command() -> None:
    core = AssistantCore.load()
    out = core.chat("/version")
    assert __version__ in out
    assert "Version consistency" in out


def test_game_fallback_without_ollama() -> None:
    with tempfile.TemporaryDirectory(prefix="wla48_smoke_") as tmp:
        cfg = AssistantConfig(workspace=tmp, allow_mutating_tools=True)
        registry = ToolRegistry(cfg)
        old_model_chat = tools_module.model_chat
        try:
            tools_module.model_chat = lambda *args, **kwargs: None
            project = registry._ask_model_for_project("make a game", mode="create", build_mode="fast")
        finally:
            tools_module.model_chat = old_model_chat

        assert project is not None
        assert project["source"] == "deterministic_fallback"
        assert "app.js" in project["files"]
        assert project.get("attempt_history")
        assert any(item.get("status") == "used_deterministic_fallback" for item in project["attempt_history"])


def test_pong_arrow_state_repair_and_game_sanity() -> None:
    with tempfile.TemporaryDirectory(prefix="wla48_game_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text(
            "<!doctype html><canvas id='pongCanvas'></canvas><script src='app.js'></script>",
            encoding="utf-8",
        )
        (root / "app.js").write_text(
            """
const canvas = document.getElementById('pongCanvas');
const ctx = canvas.getContext('2d');
let score = 0;
let paddleX = 20;
let ballRadius = 8;
function draw() {
  if (rightPressed) paddleX += 4;
  if (leftPressed) paddleX -= 4;
  score += 1;
}
setInterval(draw, 16);
""",
            encoding="utf-8",
        )
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        fixes = registry._auto_fix_common_code_errors(root)
        assert fixes
        js = (root / "app.js").read_text(encoding="utf-8")
        assert "let rightPressed = false" in js
        assert "let leftPressed = false" in js
        assert "keydown" in js
        ok, problems = registry._game_runtime_sanity_check(root, "make a game")
        assert ok, problems


def test_reasoning_and_known_error_recovery() -> None:
    with tempfile.TemporaryDirectory(prefix="wla49_recovery_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text(
            "<!doctype html><canvas id='pongCanvas'></canvas><script src='app.js'></script>",
            encoding="utf-8",
        )
        (root / "app.js").write_text(
            """
const canvas = document.getElementById('pongCanvas');
const ctx = canvas.getContext('2d');
let score = 0;
let paddleX = 20;
let ballRadius = 8;
function draw() {
  if (rightPressed) paddleX += 4;
  if (leftPressed) paddleX -= 4;
  score += 1;
}
setInterval(draw, 16);
""",
            encoding="utf-8",
        )
        (root / "PROJECT_MANIFEST.json").write_text(
            json.dumps(
                {
                    "goal": "make a game",
                    "main_file": "index.html",
                    "run_command": "start .\\index.html",
                    "verify_command": "",
                },
                indent=2,
            ),
            encoding="utf-8",
        )
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        diag = registry.reasoning_diagnostics(goal="make a game", failed_tool="auto_verify", failure={"error": "ReferenceError: rightPressed is not defined"})
        assert diag.ok
        assert "js_input_state" in diag.data["diagnosis"]["tags"]
        recovered = registry.known_error_recover(goal="make a game", failed_step="smoke", failed_tool="auto_verify", failure={"error": "ReferenceError: rightPressed is not defined"})
        assert recovered.ok, recovered.data
        js = (root / "app.js").read_text(encoding="utf-8")
        assert "let rightPressed = false" in js
        assert "keydown" in js


def test_iterative_candidate_refinement_accepts_editable_draft() -> None:
    with tempfile.TemporaryDirectory(prefix="wla50_candidate_") as tmp:
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        old_model_chat = tools_module.model_chat
        weak = {
            "folder": "WeakGame",
            "main_file": "index.html",
            "files": {
                "index.html": "<!doctype html><html><body><h1>Game</h1><script src=\"app.js\"></script></body></html>",
                "app.js": "let player = {x: 10}; function draw(){ player.x += 1; } setInterval(draw, 16);",
                "README.md": "# Tiny game draft",
            },
        }
        try:
            tools_module.model_chat = lambda *args, **kwargs: None
            refined, trace, status = registry._refine_rejected_candidate(weak, "make a game", "model output did not implement the requested domain", "fast", max_rounds=1)
        finally:
            tools_module.model_chat = old_model_chat
        assert refined is not None
        assert status == "accepted_after_deterministic_refinement"
        assert refined["source"] == "deterministic_fallback+iterative_refinement" or refined["source"].startswith("deterministic_fallback")
        assert trace
        assert "app.js" in refined["files"]


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


def test_idle_once_runs_existing_sequence_and_writes_report_only_decision() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_once_") as tmp:
        root = Path(tmp)
        profile = root / "profile"
        profile.mkdir()
        (profile / "IDLE_STRATEGY_STATE.json").write_text("{broken json", encoding="utf-8")
        logs = []
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda kind, message, data=None: logs.append((kind, message, data or {}))
            core = _make_idle_core(profile)
            reply = core._idle_once("inspect idle reports")
        finally:
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

        assert core.tools.calls == [
            "idle_tool_plan",
            "heartbeat",
            "idle_lessons",
            "investigate_logs",
            "known_issues",
            "propose_improvements",
            "self_improvement_queue",
        ]
        assert "self_improve" not in core.tools.calls
        assert "No source files were modified by idle mode." in reply
        assert "Selected candidate: Improve idle report quality" in reply
        assert "Scores: value=" in reply
        markdown_reports = sorted((profile / "idle_runs").glob("idle_cycle_*.md"))
        json_reports = sorted((profile / "idle_runs").glob("idle_cycle_*.json"))
        assert len(markdown_reports) == 1
        assert len(json_reports) == 1
        assert f"Markdown report: {markdown_reports[0]}" in reply
        assert f"JSON report: {json_reports[0]}" in reply

        markdown = markdown_reports[0].read_text(encoding="utf-8")
        for heading in [
            "# Nova Idle Cycle Report",
            "## Status",
            "## Selected Candidate",
            "## Scores",
            "## Evidence",
            "## Rejected Candidates",
            "## Verification Commands",
            "## Decision",
            "## Next Suggested Manual Command",
        ]:
            assert heading in markdown

        data = json.loads(json_reports[0].read_text(encoding="utf-8"))
        assert data["status"] == "proposal-only"
        assert data["selected_candidate"]["title"] == "Improve idle report quality"
        assert data["markdown_report_path"] == str(markdown_reports[0])
        assert data["json_report_path"] == str(json_reports[0])
        state = json.loads((profile / "IDLE_STRATEGY_STATE.json").read_text(encoding="utf-8"))
        assert data["selected_candidate"]["id"] in state["recent_candidate_ids"]
        assert any(kind == "idle_decision_report" for kind, _message, _data in logs)


def test_idle_running_mode_auto_applies_low_risk_report_patch_by_default() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_background_apply_") as tmp:
        root = Path(tmp)
        profile = root / "profile"
        repo = root / "repo"
        profile.mkdir()
        repo.mkdir()
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        old_cwd = Path.cwd()
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            os.chdir(repo)
            core = _make_idle_core(profile)
            core.idle_state["enabled"] = True
            core._idle_auto_apply_verification_plan = lambda repo_root: [("stub", ["stub"])]
            core._run_idle_auto_apply_verification = lambda repo_root: (True, [{"name": "stub", "ok": True, "returncode": 0, "output": "ok"}])
            reply = core._idle_once("inspect idle reports")
            target = repo / "docs" / "IDLE_REPORTS.md"
            report_json = sorted((profile / "idle_auto_apply_reports").glob("idle_auto_apply_*.json"))
            target_exists = target.exists()
            target_text = target.read_text(encoding="utf-8") if target_exists else ""
            report_data = json.loads(report_json[-1].read_text(encoding="utf-8")) if report_json else {}
            report_markdown_path = report_json[-1].with_suffix(".md") if report_json else None
            tool_calls = list(core.tools.calls)
        finally:
            os.chdir(old_cwd)
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

    assert target_exists
    assert "Auto-Applied Idle Report Entry" in target_text
    assert "Background auto-apply: applied" in reply
    assert report_json
    assert report_data["status"] == "applied"
    assert report_data["gate"]["allowed"] is True
    assert f"Auto-apply report: {report_markdown_path}" in reply
    assert "self_improve" not in tool_calls


def test_idle_propose_writes_proposal_without_source_edits() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_propose_") as tmp:
        profile = Path(tmp) / "profile"
        profile.mkdir()
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        logs = []
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda kind, message, data=None: logs.append((kind, message, data or {}))
            core = _make_idle_core(profile)
            reply = core.idle_command("propose add tests for idle candidate scoring")
        finally:
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

        assert "Idle proposal: Improve idle report quality" in reply
        assert "Status: proposal-only" in reply
        assert "Scores: value=" in reply
        assert "Suggested manual command: /self-improve Add tests or reporting for Improve idle report quality without changing idle auto-apply behaviour" in reply
        assert "No source files were modified by idle propose." in reply
        assert "self_improve" not in core.tools.calls

        markdown_proposals = sorted((profile / "idle_patch_proposals").glob("idle_patch_proposal_*.md"))
        json_proposals = sorted((profile / "idle_patch_proposals").glob("idle_patch_proposal_*.json"))
        assert len(markdown_proposals) == 1
        assert len(json_proposals) == 1
        assert f"Markdown proposal: {markdown_proposals[0]}" in reply
        assert f"JSON proposal: {json_proposals[0]}" in reply

        markdown = markdown_proposals[0].read_text(encoding="utf-8")
        for heading in [
            "# Nova Idle Patch Proposal",
            "## Status",
            "## User Goal",
            "## Selected Candidate",
            "## Evidence",
            "## Target Files",
            "## Planned Change",
            "## Non-goals",
            "## Safety Checks",
            "## Verification Commands",
            "## Rollback Plan",
            "## Suggested Manual Command",
        ]:
            assert heading in markdown
        for non_goal in [
            "Do not apply unguarded or high-risk edits automatically.",
            "Do not loosen self-improve safety.",
            "Do not change internet/package/install behaviour.",
            "Do not integrate external repo code.",
            "Do not remove backup or rollback logic.",
            "Do not change command names unexpectedly.",
        ]:
            assert non_goal in markdown

        data = json.loads(json_proposals[0].read_text(encoding="utf-8"))
        assert data["status"] == "proposal-only"
        assert data["candidate"]["title"] == "Improve idle report quality"
        assert data["suggested_self_improve_command"].startswith("/self-improve Add tests or reporting for")
        assert data["markdown_proposal_path"] == str(markdown_proposals[0])
        assert data["json_proposal_path"] == str(json_proposals[0])
        assert any(kind == "idle_patch_proposal" for kind, _message, _data in logs)


def test_idle_command_routes_status_once_propose_start_stop() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_routes_") as tmp:
        profile = Path(tmp) / "profile"
        profile.mkdir()
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            core = _make_idle_core(profile)
            core._idle_loop = lambda goal: None

            status = core.idle_command("status")
            once = core.idle_command("once inspect reports")
            propose = core.idle_command("propose inspect reports")
            start = core.idle_command("start inspect reports")
            stop = core.idle_command("stop")
        finally:
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

        assert "Idle mode:" in status
        assert "No source files were modified by idle mode." in once
        assert "No source files were modified by idle propose." in propose
        assert "Idle mode started." in start
        assert stop == "Idle mode stopped."
        assert "self_improve" not in core.tools.calls


def test_idle_auto_apply_default_allows_low_risk_report_patch_and_setting_still_works() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_auto_apply_") as tmp:
        root = Path(tmp)
        profile = root / "profile"
        repo = root / "repo"
        profile.mkdir()
        repo.mkdir()
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        old_cwd = Path.cwd()
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            os.chdir(repo)
            core = _make_idle_core(profile)
            core._run_idle_auto_apply_verification = lambda repo_root: (True, [{"name": "stub", "ok": True, "returncode": 0, "output": "ok"}])

            blocked = core.idle_command("auto-apply run improve idle report")
            enabled = core.idle_command("auto-apply on")
            applied = core.idle_command("auto-apply run improve idle report")
            target = repo / "docs" / "IDLE_REPORTS.md"
            target_exists = target.exists()
            target_text = target.read_text(encoding="utf-8") if target.exists() else ""
            reports = sorted((profile / "idle_auto_apply_reports").glob("idle_auto_apply_*.json"))
            backups = sorted((profile / "idle_auto_apply_backups").glob("*.bak"))
            report_data = json.loads(reports[-1].read_text(encoding="utf-8")) if reports else {}
        finally:
            os.chdir(old_cwd)
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

    assert "Idle auto-apply is disabled" in blocked
    assert "setting: on" in enabled
    assert "Idle auto-apply applied one low-risk patch." in applied
    assert target_exists
    assert "Auto-Applied Idle Report Entry" in target_text
    assert reports
    assert backups
    assert report_data["status"] == "applied"
    assert report_data["self_improve_called"] is False
    assert report_data["gate"]["allowed"] is True
    assert "self_improve" not in core.tools.calls


def test_idle_auto_apply_surgical_fallback_repairs_trivial_doc_damage() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_auto_apply_surgical_") as tmp:
        root = Path(tmp)
        profile = root / "profile"
        repo = root / "repo"
        profile.mkdir()
        repo.mkdir()
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        old_app_dir = core_module.APP_DIR
        old_log_activity = core_module.log_activity
        old_cwd = Path.cwd()
        try:
            core_module.APP_DIR = profile
            core_module.log_activity = lambda *args, **kwargs: None
            os.chdir(repo)
            core = _make_idle_core(profile)
            core.idle_command("auto-apply on")

            def fake_patch(selected, goal, repo_root):
                target = repo_root / "docs" / "IDLE_REPORTS.md"
                original = "# Reports\n\n"
                proposed = original + "verifiaction sucess improves capabiltiies\n"
                return {
                    "ok": True,
                    "relative_path": "docs/IDLE_REPORTS.md",
                    "target_path": str(target),
                    "target_existed": False,
                    "original": original,
                    "proposed": proposed,
                    "diff": "-# Reports\n+# Reports\n+verifiaction sucess improves capabiltiies",
                }

            def fake_verify(repo_root):
                text = (repo_root / "docs" / "IDLE_REPORTS.md").read_text(encoding="utf-8", errors="replace")
                ok = "verification success improves capabilities" in text
                return ok, [{"name": "stub", "ok": ok, "returncode": 0 if ok else 1, "output": "ok" if ok else "spelling verification failed"}]

            core._idle_auto_apply_build_patch = fake_patch
            core._run_idle_auto_apply_verification = fake_verify
            applied = core.idle_command("auto-apply run repair typo in idle report")
            target = repo / "docs" / "IDLE_REPORTS.md"
            text = target.read_text(encoding="utf-8")
            reports = sorted((profile / "idle_auto_apply_reports").glob("idle_auto_apply_*.json"))
            report_data = json.loads(reports[-1].read_text(encoding="utf-8"))
        finally:
            os.chdir(old_cwd)
            core_module.APP_DIR = old_app_dir
            core_module.log_activity = old_log_activity

    assert "applied one low-risk patch" in applied.lower()
    assert "verification success improves capabilities" in text
    assert report_data["status"] == "applied-after-surgical-fallback"
    assert report_data["surgical_fallback"]["changed"] is True
    assert "self_improve" not in core.tools.calls


assert tuple(map(int, __version__.split("."))) >= (55, 3, 113)


if __name__ == "__main__":
    tests_quality_dashboard.run_all()
    tests_action_watcher.run_all(verbose=True)
    tests_tool_catalog_interaction_learning.run_all(verbose=True)
    tests_planning_dashboard.run_all(verbose=True)
    tests_model_json_recovery.run_all(verbose=True)
    tests_feature_continuity.run_all(verbose=True)
    tests_autonomous_explain.run_all(verbose=True)
    tests_autonomous_sequence.run_all(verbose=True)
    tests_timeout_resilience.run_all()
    tests_autonomous_journal.run_all(verbose=True)
    tests_self_awareness.run_all(verbose=True)
    tests_v52_roadmap.run_all()
    test_idle_once_runs_existing_sequence_and_writes_report_only_decision()
    print("PASS test_idle_once_runs_existing_sequence_and_writes_report_only_decision")
    test_idle_running_mode_auto_applies_low_risk_report_patch_by_default()
    print("PASS test_idle_running_mode_auto_applies_low_risk_report_patch_by_default")
    test_idle_propose_writes_proposal_without_source_edits()
    print("PASS test_idle_propose_writes_proposal_without_source_edits")
    test_idle_command_routes_status_once_propose_start_stop()
    print("PASS test_idle_command_routes_status_once_propose_start_stop")
    test_idle_auto_apply_default_allows_low_risk_report_patch_and_setting_still_works()
    print("PASS test_idle_auto_apply_default_allows_low_risk_report_patch_and_setting_still_works")
    test_idle_auto_apply_surgical_fallback_repairs_trivial_doc_damage()
    print("PASS test_idle_auto_apply_surgical_fallback_repairs_trivial_doc_damage")
    tests_format_result.run_all(verbose=True)
    tests_idle_engine.run_all(verbose=True)
    tests_idle_events.run_all(verbose=True)
    tests_self_improve_guardrails.run_all(verbose=True)
    tests_webui_idle_status.run_all(verbose=True)
    tests_autonomous_failure.run_all(verbose=True)
    tests_command_suggestions.run_all(verbose=True)
    tests_creation_intent.run_all(verbose=True)
    tests_request_intent.run_all(verbose=True)
    tests_tool_guides.run_all(verbose=True)
    tests_surgical_fallback.run_all(verbose=True)
    tests_project_quality_ui.run_all(verbose=True)
    tests_intent_planning.run_all(verbose=True)
    tests_webui_planning_visibility.run_all(verbose=True)
    tests_project_quality_score.run_all(verbose=True)
    tests_project_acceptance.run_all(verbose=True)
    tests_game_design.run_all(verbose=True)
    tests_project_runtime_probe.run_all(verbose=True)
    tests_task_decomposition.run_all(verbose=True)
    tests_v52_5_roadmap.run_all(verbose=True)
    tests_release_hygiene.run_all(verbose=True)
    tests_command_verifier.test_command_verifier_detects_success_and_missing_markers()
    print("PASS test_command_verifier_detects_success_and_missing_markers")
    tests_command_verifier.test_command_verifier_flags_command_error_and_unknown_command()
    print("PASS test_command_verifier_flags_command_error_and_unknown_command")
    tests_command_verifier.test_default_contracts_are_safe_and_do_not_include_mutating_commands()
    print("PASS test_default_contracts_are_safe_and_do_not_include_mutating_commands")
    tests_command_verifier.test_core_command_verify_runs_existing_safe_commands()
    print("PASS test_core_command_verify_runs_existing_safe_commands")
    tests_architecture_audit.run_all(verbose=True)
    tests_command_contract_download.run_all(verbose=True)
    tests_eventlog_resilience.run_all(verbose=True)
    tests_model_health_timeout.run_all(verbose=True)
    tests_v55_ux_game.run_all(verbose=True)
    tests_file_context.run_all(verbose=True)
    tests_improvement_features_v55_3_124.run_all(verbose=True)
    tests_nova_inspiration_v55_3_125.run_all(verbose=True)
    tests_nova_coding_v55_3_126.run_all(verbose=True)
    tests_nova_agent_upgrade_v55_3_127.run_all(verbose=True)
    tests_nova_deep_research_v55_3_129.run_all(verbose=True)
    tests_nova_reliability_v55_3_128.run_all(verbose=True)
    tests_nova_route_resilience_v55_3_130.run_all(verbose=True)
    tests_nova_improvement_assurance_v55_3_131.run_all(verbose=True)
    tests_nova_capability_drift_v55_3_132.run_all(verbose=True)
