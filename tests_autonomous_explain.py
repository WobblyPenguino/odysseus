from __future__ import annotations

from winlocalassistant.autonomous_explain import explain_autonomous_state, render_autonomous_explanation_markdown
from winlocalassistant.core import AssistantCore


def test_explain_autonomous_state_includes_why_next_risk_and_verification() -> None:
    state = {
        "running": True,
        "enabled": True,
        "phase": "act_failed",
        "current_action": "Improve project failed",
        "current_tool": "improve_project",
        "last_failure_category": "timeout",
        "last_failure_signature": "improve-project-timeout",
        "last_suggested_fix": "diagnose_recent_failure",
        "last_repair_proposal_path": "repair.md",
        "events": [{"time": "now", "kind": "act_failed", "message": "timed out"}],
    }
    explanation = explain_autonomous_state(state)
    assert "phase" in explanation.summary or "actively" in explanation.summary
    assert "diagnos" in explanation.why.lower() or "failure" in explanation.why.lower()
    assert "repair" in explanation.next_expected_step.lower()
    assert "timeout" in explanation.risk.lower()
    assert explanation.verification
    assert "improve-project-timeout" in explanation.failure_memory
    assert explanation.repair_proposal == "repair.md"


def test_autonomous_explanation_markdown_has_user_readable_sections() -> None:
    md = render_autonomous_explanation_markdown(explain_autonomous_state({"phase": "planning", "current_action": "Planning next step"}))
    assert "# Autonomous Explanation" in md
    assert "Why this is happening" in md
    assert "Next expected step" in md
    assert "Risk / safety state" in md
    assert "Failure memory" in md


def test_core_autonomous_explain_command_is_read_only_and_useful() -> None:
    core = AssistantCore.load()
    out = core.chat("/autonomous-explain make a calculator and verify it")
    assert "Planning Dashboard" in out
    assert "Autonomous Explanation" in out
    assert "Recommended next action" in out


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
