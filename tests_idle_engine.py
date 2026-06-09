from __future__ import annotations

import json
import tempfile
from pathlib import Path

from winlocalassistant.idle_engine import (
    IdleCandidate,
    IdleCycleReport,
    IdleEvidence,
    IdleStrategyState,
    classify_path_risk,
    collect_idle_candidates,
    default_verification_commands,
    load_strategy_state,
    make_candidate_id,
    save_strategy_state,
    score_candidate,
    select_candidate,
    update_strategy_state_after_report,
)


def _candidate(
    title: str,
    category: str,
    target_files: list[str],
    *,
    value: float = 0.6,
    confidence: float = 0.8,
    risk: float = 0.0,
    allowed: bool = False,
) -> IdleCandidate:
    return IdleCandidate(
        id=make_candidate_id(title, target_files),
        title=title,
        category=category,
        evidence=[IdleEvidence(source="test", summary="evidence")],
        target_files=target_files,
        value_score=value,
        risk_score=risk,
        confidence_score=confidence,
        allowed_to_auto_apply=allowed,
    )


def _report_for(candidate: IdleCandidate | None, status: str = "proposal-only") -> IdleCycleReport:
    return IdleCycleReport(
        run_id="test-run",
        timestamp="2026-05-22T00:00:00Z",
        selected_candidate=candidate,
        rejected_candidates=[],
        no_safe_candidate=candidate is None,
        status=status,
        verification_commands=default_verification_commands(),
    )


def test_make_candidate_id_is_deterministic() -> None:
    first = make_candidate_id("Improve Reports", ["b.py", "a.py"])
    second = make_candidate_id("Improve Reports", ["b.py", "a.py"])
    reordered = make_candidate_id("Improve Reports", ["a.py", "b.py"])
    different = make_candidate_id("Improve Tests", ["a.py", "b.py"])

    assert first == second
    assert first == reordered
    assert first != different
    assert first == first.lower()
    assert len(first) <= 90


def test_classify_path_risk_high_risk_paths() -> None:
    for path in [
        "winlocalassistant/security.py",
        "winlocalassistant/tools.py",
        "winlocalassistant/core.py",
        "winlocalassistant/internet_tools.py",
        "winlocalassistant/network.py",
    ]:
        risk, reason = classify_path_risk(path)
        assert risk >= 0.95, path
        assert reason, path


def test_classify_path_risk_low_risk_paths() -> None:
    for path in [
        "docs/IMPROVEMENT_REPORT.md",
        "tests_idle_engine.py",
        "README.md",
    ]:
        risk, reason = classify_path_risk(path)
        assert risk <= 0.25, path
        assert reason is None


def test_collect_idle_candidates_empty_profile_returns_noop() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_empty_") as tmp:
        profile = Path(tmp)
        candidates = collect_idle_candidates(profile, profile)
    assert len(candidates) == 1
    assert candidates[0].title == "No safe idle improvement found"
    assert candidates[0].category == "noop"
    assert candidates[0].allowed_to_auto_apply is False
    assert candidates[0].blocked_reason == "No useful idle evidence was found."


def test_collect_idle_candidates_from_error_evidence() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_error_") as tmp:
        profile = Path(tmp)
        (profile / "ERROR_INVESTIGATION.md").write_text("traceback failed exception", encoding="utf-8")
        candidates = collect_idle_candidates(profile, profile)
    assert any(candidate.category == "error-investigation" for candidate in candidates)


def test_collect_idle_candidates_from_test_evidence() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_tests_") as tmp:
        profile = Path(tmp)
        (profile / "IDLE_LESSONS.md").write_text("test smoke coverage verification", encoding="utf-8")
        candidates = collect_idle_candidates(profile, profile)
    assert any(candidate.category == "tests" for candidate in candidates)


def test_collect_idle_candidates_from_report_evidence() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_report_") as tmp:
        profile = Path(tmp)
        (profile / "IMPROVEMENT_PROPOSALS.md").write_text("log report diagnostic jsonl event", encoding="utf-8")
        candidates = collect_idle_candidates(profile, profile)
    reports = [candidate for candidate in candidates if candidate.category == "report"]
    assert reports
    assert reports[0].allowed_to_auto_apply is True


def test_collect_idle_candidates_self_improve_is_high_risk_proposal_only() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_self_") as tmp:
        profile = Path(tmp)
        (profile / "SELF_IMPROVEMENT_QUEUE.md").write_text(
            "self-improve should review rollback",
            encoding="utf-8",
        )
        candidates = collect_idle_candidates(profile, profile)
    found = [candidate for candidate in candidates if candidate.category == "self-improve-review"]
    assert found
    scored = score_candidate(found[0], None)
    assert scored.risk_score >= 0.70
    assert scored.allowed_to_auto_apply is False
    assert scored.blocked_reason


def test_score_candidate_blocks_high_risk_candidates() -> None:
    candidate = _candidate("Touch Core", "tests", ["winlocalassistant/core.py"], allowed=True)
    scored = score_candidate(candidate, None)
    assert scored.risk_score >= 0.70
    assert scored.allowed_to_auto_apply is False
    assert scored.blocked_reason


def test_score_candidate_allows_safe_report_auto_apply_when_preapproved() -> None:
    candidate = _candidate("Improve Report", "report", ["docs/IDLE_REPORTS.md"], allowed=True)
    scored = score_candidate(candidate, None)
    assert scored.risk_score <= 0.20
    assert scored.allowed_to_auto_apply is True
    assert scored.blocked_reason is None


def test_score_candidate_recent_candidate_penalty() -> None:
    candidate = _candidate("Improve Report", "report", ["docs/IDLE_REPORTS.md"])
    base = score_candidate(candidate, None)
    penalized = score_candidate(candidate, IdleStrategyState(recent_candidate_ids=[candidate.id]))
    assert penalized.final_score < base.final_score


def test_score_candidate_file_cooldown_penalty() -> None:
    candidate = _candidate("Improve Report", "report", ["docs/IDLE_REPORTS.md"])
    base = score_candidate(candidate, None)
    penalized = score_candidate(candidate, IdleStrategyState(file_cooldowns={"docs/IDLE_REPORTS.md": 2}))
    assert penalized.final_score < base.final_score


def test_score_candidate_failed_category_penalty() -> None:
    candidate = _candidate("Improve Report", "report", ["docs/IDLE_REPORTS.md"])
    base = score_candidate(candidate, None)
    penalized = score_candidate(candidate, IdleStrategyState(failed_categories={"report": 2}))
    assert penalized.final_score < base.final_score


def test_select_candidate_picks_highest_safe_candidate() -> None:
    low = _candidate("Low Value Report", "report", ["docs/LOW.md"], value=0.2)
    high = _candidate("High Value Tests", "tests", ["tests_idle_engine.py"], value=0.9)
    unsafe = _candidate("Unsafe Core", "tests", ["winlocalassistant/core.py"], value=1.0)
    report = select_candidate([low, high, unsafe], None)

    assert report.selected_candidate is not None
    assert report.selected_candidate.id == high.id
    assert report.status == "proposal-only"
    assert report.no_safe_candidate is False
    assert unsafe.id in {candidate.id for candidate in report.rejected_candidates}


def test_select_candidate_does_not_select_unsafe_or_noop() -> None:
    unsafe = _candidate("Unsafe Core", "tests", ["winlocalassistant/core.py"], value=1.0)
    noop = IdleCandidate(
        id=make_candidate_id("No safe idle improvement found", []),
        title="No safe idle improvement found",
        category="noop",
        evidence=[],
        target_files=[],
        confidence_score=1.0,
    )
    report = select_candidate([unsafe, noop], None)

    assert report.selected_candidate is None
    assert report.no_safe_candidate is True
    assert report.status == "no-safe-candidate"


def test_select_candidate_rejections_are_sorted_by_final_score() -> None:
    first = _candidate("First", "report", ["docs/FIRST.md"], value=0.7)
    second = _candidate("Second", "report", ["docs/SECOND.md"], value=0.4)
    unsafe = _candidate("Unsafe", "tests", ["winlocalassistant/core.py"], value=1.0)
    report = select_candidate([first, second, unsafe], None)
    scores = [candidate.final_score for candidate in report.rejected_candidates]
    assert scores == sorted(scores, reverse=True)


def test_select_candidate_skips_twice_repeated_candidate_when_alternative_exists() -> None:
    repeated = _candidate("Strengthen idle verification tests", "tests", ["tests_smoke.py"], value=0.95)
    alternative = _candidate("Improve idle report quality", "report", ["docs/IDLE_REPORTS.md"], value=0.55)
    state = IdleStrategyState(recent_candidate_ids=[repeated.id, repeated.id])
    report = select_candidate([repeated, alternative], state)

    assert report.selected_candidate is not None
    assert report.selected_candidate.id == alternative.id
    assert repeated.id in {candidate.id for candidate in report.rejected_candidates}


def test_load_strategy_state_missing_file_returns_empty_state() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_state_missing_") as tmp:
        state = load_strategy_state(Path(tmp) / "missing.json")
    assert state == IdleStrategyState()


def test_load_strategy_state_corrupt_json_returns_empty_state() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_state_corrupt_") as tmp:
        path = Path(tmp) / "state.json"
        path.write_text("{not json", encoding="utf-8")
        state = load_strategy_state(path)
    assert state == IdleStrategyState()


def test_save_strategy_state_writes_readable_json() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_idle_state_save_") as tmp:
        path = Path(tmp) / "state.json"
        save_strategy_state(path, IdleStrategyState(recent_candidate_ids=["abc"], file_cooldowns={"docs/a.md": 3}))
        data = json.loads(path.read_text(encoding="utf-8"))
    assert data["recent_candidate_ids"] == ["abc"]
    assert data["file_cooldowns"] == {"docs/a.md": 3}


def test_update_strategy_state_after_report_tracks_recent_and_cooldowns() -> None:
    old_ids = [f"old-{idx}" for idx in range(12)]
    candidate = _candidate("Improve Report", "report", ["docs/IDLE_REPORTS.md"])
    state = IdleStrategyState(recent_candidate_ids=old_ids, file_cooldowns={"docs/old.md": 2, "docs/remove.md": 1})
    updated = update_strategy_state_after_report(state, _report_for(candidate))

    assert updated.recent_candidate_ids[-1] == candidate.id
    assert len(updated.recent_candidate_ids) == 10
    assert updated.file_cooldowns["docs/idle_reports.md"] == 3
    assert updated.file_cooldowns["docs/old.md"] == 1
    assert "docs/remove.md" not in updated.file_cooldowns


def test_update_strategy_state_after_report_counts_failed_and_success_status() -> None:
    failed_candidate = _candidate("Improve Report", "report", ["docs/IDLE_REPORTS.md"])
    success_candidate = _candidate("Improve Tests", "tests", ["tests_idle_engine.py"])
    failed = update_strategy_state_after_report(
        IdleStrategyState(),
        _report_for(failed_candidate, status="failed-verification"),
    )
    succeeded = update_strategy_state_after_report(
        failed,
        _report_for(success_candidate, status="success-verification"),
    )

    assert failed.failed_categories["report"] == 1
    assert succeeded.successful_categories["tests"] == 1
    assert succeeded.last_successful_candidate == success_candidate.id


def test_default_verification_commands_include_required_commands() -> None:
    commands = default_verification_commands()
    joined = "\n".join(commands)
    assert "py_compile" in joined
    assert "python tests_smoke.py" in commands
    assert "python -m pytest tests_smoke.py" in commands
    assert "python -m pytest tests_cli_user_mode.py" in commands


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
