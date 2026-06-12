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


def test_inventory_backed_generation_produces_safe_source_test_candidate() -> None:
    bundle = EvidenceBundle(
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted\nBest candidate below productive minimum.",
        audit="real codebase source+test improvement",
    )

    candidates = build_inventory_backed_candidate_drafts(bundle)
    ids = candidate_ids(candidates)

    assert "tools-report-state-task-pool-diagnostics-v1" not in ids
    assert "candidate-factory-task-pool-exhaustion-diagnostics-v1" in ids
    candidate = next(c for c in candidates if c["Id"] == "candidate-factory-task-pool-exhaustion-diagnostics-v1")
    assert candidate["Editable"] == [
        "nova_improvement_lab\\autonomous_candidate_factory.py",
        "tests_autonomous_candidate_factory.py",
    ]
    assert candidate["RequiredChangedFiles"] == candidate["Editable"]
    assert candidate["Tests"] == ["tests_autonomous_candidate_factory.py"]


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

    assert "tools-report-state-task-pool-diagnostics-v1" not in ids
    assert "candidate-factory-pool-exhaustion-summary-v1" in ids
    assert "candidate-factory-task-pool-exhaustion-diagnostics-v1" in ids


def test_inventory_backed_generation_expands_after_primary_inventory_candidates_completed() -> None:
    roadmap = "\n".join(
        [
            "- abc1234 Task queue improvement: tools-report-state-task-pool-diagnostics-v1",
            "- def5678 Task queue improvement: nova-lab-autodev-sandbox-task-selection-diagnostics-v1",
            "- candidate-factory-bad-task-id-filter-v1 [recently-completed]",
            "- candidate-factory-failure-feedback-gap-v1 [recently-completed]",
        ]
    )
    bundle = EvidenceBundle(
        roadmap=roadmap,
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted\nNo sufficiently productive task remained.",
        audit="real codebase source+test improvement",
    )

    candidates = build_inventory_backed_candidate_drafts(bundle)
    ids = candidate_ids(candidates)

    assert "tools-report-state-task-pool-diagnostics-v1" not in ids
    assert "nova-lab-autodev-sandbox-task-selection-diagnostics-v1" not in ids
    assert "candidate-factory-task-pool-exhaustion-diagnostics-v1" in ids
    assert "candidate-factory-promotion-skip-reason-diagnostics-v1" in ids

    for candidate in candidates:
        assert set(["Id", "Goal", "Editable", "RequiredChangedFiles", "RequiredDiffContains", "Tests"]).issubset(candidate)
        assert candidate["Editable"] == [
            "nova_improvement_lab\\autonomous_candidate_factory.py",
            "tests_autonomous_candidate_factory.py",
        ]
        assert candidate["RequiredChangedFiles"] == candidate["Editable"]
        assert candidate["Tests"] == ["tests_autonomous_candidate_factory.py"]


def test_build_autonomous_candidate_drafts_includes_fresh_inventory_expansion_when_pool_exhausted() -> None:
    roadmap = "\n".join(
        [
            "- abc1234 Task queue improvement: tools-report-state-task-pool-diagnostics-v1",
            "- def5678 Task queue improvement: nova-lab-autodev-sandbox-task-selection-diagnostics-v1",
        ]
    )
    bundle = EvidenceBundle(
        roadmap=roadmap,
        latest_summary="Task selection scoring diagnostics are needed.",
        task_pool_exhausted="Outcome category: task-pool-exhausted\nNo sufficiently productive task remained.",
        audit="real codebase source+test improvement",
    )

    ids = candidate_ids(build_autonomous_candidate_drafts(bundle, limit=8))

    assert "candidate-factory-task-pool-exhaustion-diagnostics-v1" in ids
    assert "candidate-factory-promotion-skip-reason-diagnostics-v1" in ids


def test_generator_evidence_bundle_accepts_current_exhaustion_hint(tmp_path) -> None:
    from tools.generate_autonomous_idea_candidates import build_evidence_bundle

    (tmp_path / "docs").mkdir(parents=True)
    (tmp_path / "local_ai_cycles" / "memory").mkdir(parents=True)

    bundle = build_evidence_bundle(
        tmp_path,
        current_exhaustion_hint="Preflight best candidate below productive minimum before autonomous fallback",
    )

    assert "preflight best candidate below productive minimum" in bundle.latest_summary.lower()
    assert "preflight best candidate below productive minimum" in bundle.task_pool_exhausted.lower()


def test_generator_current_exhaustion_hint_surfaces_inventory_expansion(tmp_path) -> None:
    from tools.generate_autonomous_idea_candidates import build_evidence_bundle

    docs = tmp_path / "docs"
    memory = tmp_path / "local_ai_cycles" / "memory"
    docs.mkdir(parents=True)
    memory.mkdir(parents=True)

    (docs / "NOVA_TASK_LOOP_ROADMAP.md").write_text(
        "\n".join(
            [
                "- abc1234 Task queue improvement: tools-report-state-task-pool-diagnostics-v1",
                "- def5678 Task queue improvement: nova-lab-autodev-sandbox-task-selection-diagnostics-v1",
            ]
        ),
        encoding="utf-8",
    )

    bundle = build_evidence_bundle(
        tmp_path,
        current_exhaustion_hint="preflight best candidate below productive minimum",
    )
    ids = candidate_ids(build_autonomous_candidate_drafts(bundle, limit=8))

    assert "candidate-factory-task-pool-exhaustion-diagnostics-v1" in ids
    assert "candidate-factory-promotion-skip-reason-diagnostics-v1" in ids


def test_candidate_factory_builds_task_pool_exhaustion_summary() -> None:
    from nova_improvement_lab.autonomous_candidate_factory import (
        EvidenceBundle,
        build_task_pool_exhaustion_summary,
    )

    bundle = EvidenceBundle(
        latest_summary=(
            "Best candidate below productive minimum before autonomous fallback. "
            "candidate-factory-bad-task-id-filter-v1 failed previously."
        ),
        task_pool_exhausted=(
            "Outcome category: task-pool-exhausted\n"
            "No sufficiently productive task remained.\n"
            "candidate-factory-agent-browser-evidence-v1"
        ),
        failure_review="Rejected task-pool candidate.",
        roadmap="",
        audit="real codebase source+test improvement",
    )

    summary = build_task_pool_exhaustion_summary(bundle)

    assert "task-pool-exhausted=True" in summary
    assert "recent_bad_task_ids=2" in summary
    assert "fresh_candidate_generation_needed=True" in summary


def test_candidate_factory_task_pool_exhaustion_diagnostics() -> None:
    from nova_improvement_lab.autonomous_candidate_factory import (
        EvidenceBundle,
        task_pool_exhaustion_diagnostics,
    )

    bundle = EvidenceBundle(
        latest_summary=(
            "Live best candidate below productive minimum. "
            "candidate-factory-task-pool-exhaustion-diagnostics-v1"
        ),
        task_pool_exhausted=(
            "Outcome category: task-pool-exhausted\n"
            "No sufficiently productive task remained.\n"
            "candidate-factory-agent-browser-evidence-v1"
        ),
        failure_review=(
            "Rejected required-file contract breach: missing required changed file(s): "
            "tests_autonomous_candidate_factory.py."
        ),
        roadmap="candidate-factory-bad-task-id-filter-v1",
        audit="real codebase source+test improvement",
    )

    diagnostics = task_pool_exhaustion_diagnostics(bundle)

    assert diagnostics["task_pool_exhausted"] is True
    assert diagnostics["needs_fresh_candidate_generation"] is True
    assert diagnostics["has_required_file_contract_failure"] is True
    assert diagnostics["candidate_id_count"] == 3
    assert "candidate-factory-agent-browser-evidence-v1" in diagnostics["candidate_ids"]


def test_inventory_backed_generation_continues_after_exhaustion_diagnostics_completed() -> None:
    from nova_improvement_lab.autonomous_candidate_factory import (
        EvidenceBundle,
        build_autonomous_candidate_drafts,
        candidate_ids,
    )

    completed = "\n".join(
        [
            "Task queue improvement: tools-report-state-task-pool-diagnostics-v1",
            "Task queue improvement: nova-lab-autodev-sandbox-task-selection-diagnostics-v1",
            "Task queue improvement: candidate-factory-pool-exhaustion-summary-v1",
            "Task queue improvement: candidate-factory-task-pool-exhaustion-diagnostics-v1",
            "Task queue improvement: candidate-factory-bad-task-id-filter-v1",
            "Task queue improvement: candidate-factory-failure-feedback-gap-v1",
        ]
    )

    bundle = EvidenceBundle(
        roadmap=completed,
        latest_summary="Preflight best candidate below productive minimum before autonomous fallback",
        task_pool_exhausted=(
            "Outcome category: task-pool-exhausted\n"
            "No sufficiently productive task remained.\n"
            "external candidate pool exhausted"
        ),
        audit="real codebase source+test improvement",
    )

    candidates = build_autonomous_candidate_drafts(bundle, limit=8)
    ids = candidate_ids(candidates)

    assert "candidate-factory-continuation-after-exhaustion-v1" in ids
    candidate = next(
        c
        for c in candidates
        if c["Id"] == "candidate-factory-continuation-after-exhaustion-v1"
    )
    assert candidate["Editable"] == [
        "nova_improvement_lab\\autonomous_candidate_factory.py",
        "tests_autonomous_candidate_factory.py",
    ]
    assert candidate["RequiredChangedFiles"] == candidate["Editable"]
    assert candidate["Tests"] == ["tests_autonomous_candidate_factory.py"]
    assert candidate["RequiredDiffContains"]

