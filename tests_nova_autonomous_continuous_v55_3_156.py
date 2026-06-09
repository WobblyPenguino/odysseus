from __future__ import annotations

from winlocalassistant.autonomous_loop_guard import (
    finite_goal_should_stop,
    summarize_cycle_outcome,
    update_loop_guard_state,
)
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolResult


def test_finite_goal_stops_only_in_finite_mode():
    assert finite_goal_should_stop("make a game", had_progress=True, had_successful_verification=True) is True
    assert finite_goal_should_stop("make a game", had_progress=True, had_successful_verification=True, continuous_mode=True) is False


def test_continuous_loop_guard_keeps_running_after_verified_milestone():
    result = ToolResult(True, "created and verified project", {"tool": "ai_create_project", "written": ["index.html"]})
    outcome = summarize_cycle_outcome(goal="make a game", sequence_results=[result], continuous_mode=True)
    assert outcome["finite_goal_complete"] is False
    assert outcome["finite_goal_milestone"] is True
    updates, notes = update_loop_guard_state({"enabled": True}, outcome, continuous_mode=True)
    assert updates["loop_guard_stop_recommended"] is False
    assert updates["next_strategy_hint"] == "choose_next_safe_improvement"
    assert any("continuous mission mode" in note for note in notes)


def test_autonomous_start_defaults_to_continuous_and_finite_flag_is_available(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    cleaned, persistence = core._parse_autonomous_persistence_options("--continuous improve Nova")
    assert cleaned == "improve Nova"
    assert persistence is True
    cleaned, persistence = core._parse_autonomous_persistence_options("--finite make a game")
    assert cleaned == "make a game"
    assert persistence is False
