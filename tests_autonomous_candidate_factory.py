from nova_improvement_lab.autonomous_candidate_factory import (
    EvidenceBundle,
    build_autonomous_candidate_drafts,
    candidate_ids,
    evidence_mentions_task_pool_exhaustion,
    extract_recent_bad_task_ids,
    filter_recent_bad_candidate_ids,
)


def test_candidate_factory_detects_task_pool_exhaustion() -> None:
    bundle = EvidenceBundle(latest_summary="Outcome category: task-pool-exhausted")
    assert evidence_mentions_task_pool_exhaustion(bundle) is True


def test_candidate_factory_extracts_recent_bad_task_ids() -> None:
    text = "\n".join(
        [
            "- tiny-old-task-v1: score=-5 category=validation-failed",
            "Rejected required-diff contract breach for task 'another-task-v1'",
        ]
    )
    assert extract_recent_bad_task_ids(text) == {"tiny-old-task-v1", "another-task-v1"}


def test_candidate_factory_generates_pool_exhaustion_candidate() -> None:
    bundle = EvidenceBundle(
        latest_summary="No sufficiently productive task remained.",
        failure_review="- tiny-old-task-v1: category=validation-failed",
    )

    candidates = build_autonomous_candidate_drafts(bundle)

    assert "candidate-factory-pool-exhaustion-summary-v1" in candidate_ids(candidates)
    first = candidates[0]
    assert first["Editable"] == [
        "nova_improvement_lab\\autonomous_candidate_factory.py",
        "tests_autonomous_candidate_factory.py",
    ]
    assert first["Tests"] == ["tests_autonomous_candidate_factory.py"]


def test_candidate_factory_generates_bad_task_filter_candidate() -> None:
    bundle = EvidenceBundle(
        failure_review="Rejected required-diff contract breach for task 'tiny-failed-v1'"
    )

    candidates = build_autonomous_candidate_drafts(bundle)

    assert "candidate-factory-bad-task-id-filter-v1" in candidate_ids(candidates)


def test_candidate_factory_detects_agent_browser_research_evidence() -> None:
    bundle = EvidenceBundle(research_notes="Agent Browser should stay localhost-only and read-only first.")

    candidates = build_autonomous_candidate_drafts(bundle)

    assert "candidate-factory-agent-browser-evidence-v1" in candidate_ids(candidates)


def test_candidate_factory_candidates_have_validator_shape() -> None:
    bundle = EvidenceBundle(
        latest_summary="task-pool-exhausted",
        audit="validation and regression testing should improve",
    )

    for candidate in build_autonomous_candidate_drafts(bundle):
        assert candidate["Id"]
        assert candidate["Goal"]
        assert candidate["Editable"]
        assert candidate["RequiredChangedFiles"]
        assert candidate["RequiredDiffContains"]
        assert candidate["Tests"]


def test_candidate_factory_filters_recent_bad_candidate_ids() -> None:
    # Create a set of candidates including the bad-task-id-filter candidate
    candidates = [
        {"Id": "c1"},
        {"Id": "candidate-factory-bad-task-id-filter-v1"},
        {"Id": "c3"},
    ]
    bad_ids = {"candidate-factory-bad-task-id-filter-v1", "c2"}
    filtered = filter_recent_bad_candidate_ids(candidates, bad_ids)
    # The candidate with the matching Id should be removed
    assert len(filtered) == 2
    assert all(c["Id"] != "candidate-factory-bad-task-id-filter-v1" for c in filtered)


def test_candidate_factory_extracts_failure_review_task_id() -> None:
    text = "\n".join(
        [
            "Task ID: candidate-factory-agent-browser-evidence-v1",
            "Stage: validation-gate",
            "Reason: Command failed: python -m pytest -q tests_autonomous_candidate_factory.py",
        ]
    )

    assert extract_recent_bad_task_ids(text) == {"candidate-factory-agent-browser-evidence-v1"}


def test_candidate_factory_filters_failed_generated_candidate_before_return() -> None:
    bundle = EvidenceBundle(
        research_notes="Agent Browser should stay localhost-only and read-only first.",
        failure_review="\n".join(
            [
                "Task ID: candidate-factory-agent-browser-evidence-v1",
                "Stage: validation-gate",
                "Reason: Command failed: python -m pytest -q tests_autonomous_candidate_factory.py",
            ]
        ),
    )

    ids = candidate_ids(build_autonomous_candidate_drafts(bundle))

    assert "candidate-factory-agent-browser-evidence-v1" not in ids
