from pathlib import Path

from winlocalassistant.autonomy_readiness import (
    build_autonomy_readiness,
    render_autonomy_readiness_markdown,
)


def _write(path: Path, text: str = "") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _write_complete_tree(root: Path) -> None:
    _write(root / "run_nova_task_queue_loop.ps1", "function Pick-Task Resolve-TaskScore Get-TaskSignalSeverityPenalty Write-TaskFailureReviewReport NOVA_TASK_FAILURE_REVIEW_LATEST.md Record-TaskOutcome")
    _write(root / "tools/validate_task_loop_patch.ps1", "tests_task_loop_static_contract.py validate_idea_promotion_candidates.py Validation passed")
    _write(root / "tests_task_loop_static_contract.py", "contracts")
    _write(root / "tools/update_task_loop_roadmap.py", "NOVA_TASK_LOOP_ROADMAP last_updated latest_commits")
    _write(root / "docs/NOVA_TASK_LOOP_ROADMAP.md", "roadmap")
    _write(root / "winlocalassistant/screen_analysis.py", "classify_screen_context_need build_screen_analysis_prompt render_screen_analysis_prompt_help")
    _write(root / "winlocalassistant/tools.py", "screen_analysis_prompt image_analyze ToolRegistry")
    _write(root / "winlocalassistant/core.py", "/screen-analysis-prompt /image-analyze handle_command")
    _write(root / "local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json", "[]")
    _write(root / "docs/NOVA_AUTONOMY_FULL_CODEBASE_AUDIT.md", "audit")


def test_autonomy_readiness_scores_minimal_complete_tree(tmp_path: Path) -> None:
    _write_complete_tree(tmp_path)

    report = build_autonomy_readiness(tmp_path)

    assert report["score"] >= 90
    assert report["status"] == "ready-for-supervised-longer-runs"
    assert report["passed"] == report["total"]
    assert report["blocking_failures"] == []


def test_autonomy_readiness_reports_missing_items(tmp_path: Path) -> None:
    report = build_autonomy_readiness(tmp_path)
    rendered = render_autonomy_readiness_markdown(report)

    assert report["score"] < 70
    assert report["status"] == "not-ready"
    assert report["blocking_failures"]
    assert "Nova Autonomy Readiness" in rendered
    assert "Safety note" in rendered
    assert "does not run Aider" in rendered


def test_autonomy_readiness_blocks_on_latest_task_pool_exhaustion(tmp_path: Path) -> None:
    _write_complete_tree(tmp_path)
    _write(
        tmp_path / "local_ai_cycles/memory/NOVA_TASK_POOL_EXHAUSTED_LATEST.md",
        "No sufficiently productive task remained.",
    )

    report = build_autonomy_readiness(tmp_path)
    rendered = render_autonomy_readiness_markdown(report)

    assert report["status"] == "not-ready"
    assert report["blocking_failures"]
    assert "Blocking issues" in rendered
    assert "NOVA_TASK_POOL_EXHAUSTED_LATEST.md" in rendered
    assert "Add or approve fresh source-backed candidates" in rendered


def test_autonomy_readiness_blocks_on_summary_task_pool_exhaustion(tmp_path: Path) -> None:
    _write_complete_tree(tmp_path)
    _write(
        tmp_path / "local_ai_cycles/memory/NOVA_TASK_LOOP_SUMMARY_LATEST.md",
        "Outcome category: task-pool-exhausted\nBest candidate below productive minimum.",
    )

    report = build_autonomy_readiness(tmp_path)
    rendered = render_autonomy_readiness_markdown(report)

    assert report["status"] == "not-ready"
    assert report["blocking_failures"]
    assert "Blocking issues" in rendered
    assert "NOVA_TASK_LOOP_SUMMARY_LATEST.md" in rendered
    assert "Add or approve fresh source-backed candidates" in rendered


def test_autonomy_readiness_command_is_registered_static() -> None:
    core = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    tools = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")

    assert '"/autonomy-readiness"' in core
    assert 'self.tools.call("autonomy_readiness", path=rest or ".")' in core
    assert '"autonomy_readiness": self.autonomy_readiness_tool' in tools
    assert "def autonomy_readiness_tool" in tools


def test_autonomy_readiness_allows_recovered_autonomous_candidate_fallback(tmp_path: Path) -> None:
    _write_complete_tree(tmp_path)
    _write(
        tmp_path / "local_ai_cycles/memory/NOVA_TASK_LOOP_SUMMARY_LATEST.md",
        "\n".join(
            [
                "Best candidate below productive minimum: tiny-old-task: score=25; minimum=35",
                "Autonomous candidate fallback selected productive task: candidate-factory-bad-task-id-filter-v1",
                "Autonomous candidate fallback score: 70",
                "Result: preflight-only",
                "Selected task: candidate-factory-bad-task-id-filter-v1",
            ]
        ),
    )
    _write(
        tmp_path / "local_ai_cycles/memory/NOVA_TASK_POOL_EXHAUSTED_LATEST.md",
        "No sufficiently productive task remained.",
    )

    report = build_autonomy_readiness(tmp_path)
    rendered = render_autonomy_readiness_markdown(report)

    assert report["status"] == "ready-for-supervised-longer-runs"
    assert report["blocking_failures"] == []
    assert "autonomous fallback selected a productive candidate" in rendered
