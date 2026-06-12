from nova_improvement_lab.autonomous_candidate_factory import (
    EvidenceBundle,
    build_autonomous_candidate_drafts,
    candidate_ids,
    evidence_mentions_task_pool_exhaustion,
    extract_recent_bad_task_ids,
    filter_recent_bad_candidate_ids,
    summarise_failure_feedback,
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
    assert all(c["Id"] != "candidate-factory-bad-task-id-filter_v1" for c in filtered)


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


def test_candidate_factory_ignores_failure_review_for_agent_browser_generation() -> None:
    bundle = EvidenceBundle(
        failure_review="Task ID: candidate-factory-agent-browser-evidence-v1\nStage: validation-gate"
    )

    ids = candidate_ids(build_autonomous_candidate_drafts(bundle))

    assert "candidate-factory-agent-browser-evidence-v1" not in ids


def test_candidate_factory_still_uses_research_notes_for_agent_browser_generation() -> None:
    bundle = EvidenceBundle(
        research_notes="Agent Browser should stay localhost-only and read-only first."
    )

    ids = candidate_ids(build_autonomous_candidate_drafts(bundle))

    assert "candidate-factory-agent-browser-evidence-v1" in ids


def test_candidate_factory_generates_failure_feedback_gap_candidate() -> None:
    bundle = EvidenceBundle(
        failure_review="Task ID: candidate-factory-validation-gap-v1\nStage: validation-gate\nReason: Command failed: python -m pytest -q tests_autonomous_candidate_factory.py"
    )

    ids = candidate_ids(build_autonomous_candidate_drafts(bundle))

    assert "candidate-factory-failure-feedback-gap-v1" in ids


def test_candidate_factory_summarises_failure_feedback() -> None:
    bundle = EvidenceBundle(
        failure_review="\n".join(
            [
                "Task ID: candidate-factory-validation-gap-v1",
                "Stage: validation-gate",
                "Reason: Command failed: python -m pytest -q tests_autonomous_candidate_factory.py",
            ]
        )
    )

    summary = summarise_failure_feedback(bundle)
    assert "candidate-factory-validation-gap-v1" in summary
    assert summary.startswith("Failed tasks:")


from nova_improvement_lab.autonomous_candidate_factory import (
    build_local_discovery_inventory,
    build_inventory_backed_candidate_drafts,
    extract_recent_completed_task_ids,
)


def test_local_discovery_inventory_detects_task_selection_scoring() -> None:
    bundle = EvidenceBundle(
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted\nBest candidate below productive minimum.",
    )

    inventory = build_local_discovery_inventory(bundle)

    assert inventory["task_pool_exhausted"] is True
    assert "task_selection_scoring" in inventory["problem_themes"]


def test_local_discovery_inventory_extracts_completed_task_ids() -> None:
    roadmap = "\n".join(
        [
            "- abc1234 Task queue improvement: real-model-context-prompt-file-safety-v1",
            "- tiny-autodev-sandbox-next-item-line-v1 [recently-completed]",
        ]
    )

    assert extract_recent_completed_task_ids(roadmap) == {
        "real-model-context-prompt-file-safety-v1",
        "tiny-autodev-sandbox-next-item-line-v1",
    }


def test_local_discovery_inventory_extracts_failed_task_ids() -> None:
    bundle = EvidenceBundle(
        failure_review="Task ID: candidate-factory-agent-browser-evidence-v1\nStage: validation-gate\nReason: Command failed"
    )

    inventory = build_local_discovery_inventory(bundle)

    assert inventory["failed_task_ids"] == ["candidate-factory-agent-browser-evidence-v1"]


def test_local_discovery_inventory_is_read_only_and_deterministic() -> None:
    bundle = EvidenceBundle(
        roadmap="Task queue improvement: completed-task-v1",
        latest_summary="validation reporting and repeated low-value cycles",
        task_pool_exhausted="task-pool-exhausted",
    )

    first = build_local_discovery_inventory(bundle)
    second = build_local_discovery_inventory(bundle)

    assert first == second
    assert bundle.roadmap == "Task queue improvement: completed-task-v1"


def test_local_discovery_inventory_does_not_generate_candidates_for_nonexistent_files_yet() -> None:
    bundle = EvidenceBundle(
        audit="validation reporting diagnostics for real codebase improvement"
    )

    inventory = build_local_discovery_inventory(bundle)

    assert "Editable" not in inventory
    assert "RequiredChangedFiles" not in inventory
    assert "winlocalassistant\\validate.py" not in str(inventory)


def test_inventory_backed_generation_produces_non_meta_source_test_candidate() -> None:
    bundle = EvidenceBundle(
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted\nBest candidate below productive minimum.",
        audit="real codebase source+test improvement",
    )

    candidates = build_inventory_backed_candidate_drafts(bundle)
    ids = candidate_ids(candidates)

    assert "tools-report-state-task-pool-diagnostics-v1" in ids
    candidate = next(c for c in candidates if c["Id"] == "tools-report-state-task-pool-diagnostics-v1")
    assert candidate["Editable"] == [
        "tools\\report_supervised_autonomy_state.py",
        "tests_supervised_autonomy_state_report.py",
    ]
    assert candidate["RequiredChangedFiles"] == candidate["Editable"]
    assert candidate["Tests"] == ["tests_supervised_autonomy_state_report.py"]


def test_inventory_backed_generation_avoids_completed_task_ids() -> None:
    bundle = EvidenceBundle(
        roadmap="Task queue improvement: tools-report-state-task-pool-diagnostics-v1",
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted",
        audit="real codebase source+test improvement",
    )

    ids = candidate_ids(build_inventory_backed_candidate_drafts(bundle))

    assert "tools-report-state-task-pool-diagnostics-v1" not in ids


def test_inventory_backed_generation_avoids_failed_task_ids() -> None:
    bundle = EvidenceBundle(
        failure_review="Task ID: tools-report-state-task-pool-diagnostics-v1\nStage: validation-gate",
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted",
        audit="real codebase source+test improvement",
    )

    ids = candidate_ids(build_inventory_backed_candidate_drafts(bundle))

    assert "tools-report-state-task-pool-diagnostics-v1" not in ids


def test_inventory_backed_candidates_have_validator_shape() -> None:
    bundle = EvidenceBundle(
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted",
        audit="real codebase source+test improvement",
    )

    candidates = build_inventory_backed_candidate_drafts(bundle)

    assert candidates
    for candidate in candidates:
        assert set(["Id", "Goal", "Editable", "RequiredChangedFiles", "RequiredDiffContains", "Tests"]).issubset(candidate)
        assert candidate["Editable"]
        assert candidate["RequiredChangedFiles"] == candidate["Editable"]
        assert candidate["Tests"]


def test_inventory_backed_generation_does_not_generate_nonexistent_file_candidate() -> None:
    bundle = EvidenceBundle(
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted",
        audit="real codebase source+test improvement in winlocalassistant validate.py project_state.py",
    )

    candidates = build_inventory_backed_candidate_drafts(bundle)
    rendered = str(candidates)

    assert "winlocalassistant\\validate.py" not in rendered
    assert "winlocalassistant\\project_state.py" not in rendered


def test_build_autonomous_candidate_drafts_preserves_meta_candidates_with_inventory_backed_candidates() -> None:
    bundle = EvidenceBundle(
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted",
        audit="real codebase source+test improvement",
    )

    ids = candidate_ids(build_autonomous_candidate_drafts(bundle))

    assert "tools-report-state-task-pool-diagnostics-v1" in ids
    assert "candidate-factory-pool-exhaustion-summary-v1" in ids
