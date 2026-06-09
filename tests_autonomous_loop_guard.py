from winlocalassistant.autonomous_loop_guard import (
    action_signature,
    finite_goal_should_stop,
    should_skip_repeated_action,
    summarize_cycle_outcome,
    update_loop_guard_state,
)
from winlocalassistant.tools import ToolResult


def test_action_signature_is_stable_and_ignores_volatile_fields():
    a = action_signature("Create", "ai_create_project", {"goal": "build snake", "run_id": "one", "cycle": 1})
    b = action_signature("Create", "ai_create_project", {"cycle": 2, "goal": "build snake", "run_id": "two"})
    assert a == b


def test_loop_guard_skips_repeated_optional_diagnostic():
    sig = action_signature("Investigate recent logs", "investigate_logs", {"focus": "same"})
    state = {"recent_action_signatures": [sig, sig], "no_progress_cycles": 0}
    skip, reason = should_skip_repeated_action(state, "Investigate recent logs", "investigate_logs", {"focus": "same"}, required=False)
    assert skip
    assert "repeated optional diagnostic" in reason


def test_loop_guard_blocks_repeated_mutation_after_no_progress():
    sig = action_signature("Improve current project", "improve_project", {"goal": "same"})
    state = {"recent_action_signatures": [sig, sig], "no_progress_cycles": 1}
    skip, reason = should_skip_repeated_action(state, "Improve current project", "improve_project", {"goal": "same"}, required=True)
    assert skip
    assert "same mutating action" in reason


def test_finite_goal_stops_after_progress():
    assert finite_goal_should_stop("build a snake game", had_progress=True, had_successful_verification=False)
    assert not finite_goal_should_stop("keep improving continuously", had_progress=True, had_successful_verification=True)


def test_cycle_outcome_and_state_detect_no_progress_loop():
    result = ToolResult(True, "No actionable changes found", {"tool": "investigate_logs", "title": "Investigate"})
    outcome = summarize_cycle_outcome(goal="improve project", base_results=[("Investigate", "investigate_logs", result)], sequence_results=[], diagnostic_only=False)
    assert outcome["had_progress"] is False
    state, notes = update_loop_guard_state({"no_progress_cycles": 1, "recent_cycle_fingerprints": [outcome["fingerprint"]]}, outcome)
    assert state["loop_guard_stop_recommended"] is True
    assert state["no_progress_cycles"] == 2
    assert any("no measurable progress" in n for n in notes)


def test_cycle_outcome_marks_created_project_as_progress_and_complete():
    result = ToolResult(True, "Created project files", {"tool": "ai_create_project", "title": "Create requested project", "written": [{"path": "app.py"}]})
    outcome = summarize_cycle_outcome(goal="build a calculator app", sequence_results=[result], diagnostic_only=False)
    assert outcome["had_progress"] is True
    assert outcome["finite_goal_complete"] is True
    state, notes = update_loop_guard_state({}, outcome)
    assert state["loop_guard_stop_recommended"] is True
    assert any("finite user goal" in n for n in notes)
