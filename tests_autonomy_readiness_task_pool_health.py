from winlocalassistant.autonomy_readiness import _check_task_pool_health


def _write_summary(root, text):
    memory = root / "local_ai_cycles" / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    (memory / "NOVA_TASK_LOOP_SUMMARY_LATEST.md").write_text(text, encoding="utf-8")


def _write_pool_exhausted(root):
    memory = root / "local_ai_cycles" / "memory"
    memory.mkdir(parents=True, exist_ok=True)
    (memory / "NOVA_TASK_POOL_EXHAUSTED_LATEST.md").write_text(
        "Outcome category: task-pool-exhausted\nNo sufficiently productive task remained.",
        encoding="utf-8",
    )


def test_task_pool_health_accepts_successful_committed_fallback(tmp_path):
    _write_pool_exhausted(tmp_path)
    _write_summary(
        tmp_path,
        "\n".join(
            [
                "Live best candidate below productive minimum before autonomous fallback",
                "Live autonomous candidate fallback selected productive task: candidate-factory-failure-feedback-gap-v1",
                "Live autonomous candidate fallback score: 70",
                "Result: committed",
                "Validation gates passed",
            ]
        ),
    )

    check = _check_task_pool_health(tmp_path)

    assert check.ok is True
    assert "committed and passed validation" in check.evidence


def test_task_pool_health_blocks_genuine_exhausted_summary(tmp_path):
    _write_summary(
        tmp_path,
        "\n".join(
            [
                "Outcome category: task-pool-exhausted",
                "No sufficiently productive task remained.",
            ]
        ),
    )

    check = _check_task_pool_health(tmp_path)

    assert check.ok is False
    assert check.blocking is True
    assert "no sufficiently productive task remained" in check.evidence


def test_task_pool_health_accepts_productive_preflight_fallback(tmp_path):
    _write_pool_exhausted(tmp_path)
    _write_summary(
        tmp_path,
        "\n".join(
            [
                "Preflight best candidate below productive minimum before autonomous fallback",
                "Autonomous candidate fallback selected productive task: nova-lab-autodev-sandbox-task-selection-diagnostics-v1",
                "Autonomous candidate fallback score: 70",
                "Result: preflight-only",
                "Selected task: nova-lab-autodev-sandbox-task-selection-diagnostics-v1",
                "Editable files: nova_improvement_lab\\autodev_sandbox.py, tests_autodev_sandbox.py",
                "Targeted tests: tests_autodev_sandbox.py",
            ]
        ),
    )

    check = _check_task_pool_health(tmp_path)

    assert check.ok is True
    assert "autonomous fallback selected a productive candidate" in check.evidence


def test_task_pool_health_rejects_low_score_preflight_fallback(tmp_path):
    _write_pool_exhausted(tmp_path)
    _write_summary(
        tmp_path,
        "\n".join(
            [
                "Outcome category: task-pool-exhausted",
                "Autonomous candidate fallback selected productive task: weak-v1",
                "Autonomous candidate fallback score: 69",
                "Result: preflight-only",
                "Selected task: weak-v1",
                "Editable files: file.py",
                "Targeted tests: tests_file.py",
            ]
        ),
    )

    check = _check_task_pool_health(tmp_path)

    assert check.ok is False
    assert check.blocking is True
    assert "no sufficiently productive task remained" in check.evidence
