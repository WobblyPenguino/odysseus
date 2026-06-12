"""Evidence-backed autonomous task candidate generation for Nova.

This module is deliberately pure and local-first:
- no shell execution
- no file writes unless callers choose to persist returned data
- no network access
- no model calls
- no runtime mutation

It turns local evidence into narrow source+test candidate drafts that can be
validated by Nova's existing candidate validators before a task loop may run.
"""

from __future__ import annotations

from dataclasses import dataclass
import re
from typing import Iterable, List, Dict


@dataclass(frozen=True)
class EvidenceBundle:
    roadmap: str = ""
    latest_summary: str = ""
    task_pool_exhausted: str = ""
    failure_review: str = ""
    audit: str = ""
    research_notes: str = ""


BAD_OUTCOME_MARKERS = (
    "validation-failed",
    "required-diff",
    "required-file",
    "test-failed",
    "no-change",
    "low-significance",
    "documentation/comment-only",
    "placeholder-or-speculative",
    "reverted-success",
)


def normalise_evidence_text(bundle: EvidenceBundle) -> str:
    """Return one searchable text blob from local evidence."""
    return "\n".join(
        part
        for part in (
            bundle.roadmap,
            bundle.latest_summary,
            bundle.task_pool_exhausted,
            bundle.failure_review,
            bundle.audit,
            bundle.research_notes,
        )
        if part
    )


def evidence_mentions_task_pool_exhaustion(bundle: EvidenceBundle) -> bool:
    """Detect whether Nova recently ran out of productive task candidates."""
    text = normalise_evidence_text(bundle).lower()
    return "task-pool-exhausted" in text or "no sufficiently productive task" in text


def detect_failure_feedback_gap(bundle: EvidenceBundle) -> bool:
    """Return true when recent evidence shows failed generated tasks need clearer feedback."""
    text = "\n".join(
        part
        for part in (
            bundle.latest_summary,
            bundle.failure_review,
            bundle.task_pool_exhausted,
        )
        if part
    ).lower()
    return (
        "result: rejected" in text
        or "stage: validation-gate" in text
        or "command failed:" in text
        or "outcome category: test-failed" in text
    )


def extract_recent_bad_task_ids(text: str) -> set[str]:
    """Extract recently failed task ids from summaries, pool reports, and failure reviews."""

    if isinstance(text, EvidenceBundle):
        normalised = normalise_evidence_text(text).lower()
    else:
        normalised = str(text or "").lower()
    found: set[str] = set()

    if not normalised:
        return found

    bad_context = (
        any(marker in normalised for marker in BAD_OUTCOME_MARKERS)
        or "command failed" in normalised
        or "stage: validation-gate" in normalised
        or "result: rejected" in normalised
        or "outcome category: test-failed" in normalised
    )

    if not bad_context:
        return found

    for task_id in re.findall(r"(?im)^\s*task id:\s*([a-z0-9][a-z0-9_-]+)\s*$", normalised):
        found.add(task_id)

    for task_id in re.findall(r"(?im)task ['\"]([a-z0-9][a-z0-9_-]+)['\"]", normalised):
        found.add(task_id)

    for task_id in re.findall(
        r"(?im)^-\s*([a-z0-9][a-z0-9_-]+):.*(?:score=-?\d+|category=|validation-failed|test-failed)",
        normalised,
    ):
        found.add(task_id)

    return found


def summarise_failure_feedback(bundle: EvidenceBundle) -> str:
    """Return a concise summary of recent rejected generated candidates.

    The summary lists the IDs of tasks that were recently rejected, extracted
    from ``bundle.failure_review``.  If no failures are detected an empty string
    is returned.
    """
    bad_ids = extract_recent_bad_task_ids(bundle.failure_review)
    if not bad_ids:
        return ""
    # Sort for deterministic output
    sorted_ids = sorted(bad_ids)
    return "Failed tasks: " + ", ".join(sorted_ids)



def extract_recent_completed_task_ids(text: str | EvidenceBundle) -> set[str]:
    """Extract recently completed task ids from roadmap and candidate-doctor evidence."""

    if isinstance(text, EvidenceBundle):
        normalised = normalise_evidence_text(text).lower()
    else:
        normalised = str(text or "").lower()

    found: set[str] = set()
    if not normalised:
        return found

    for task_id in re.findall(r"task queue improvement:\s*([a-z0-9][a-z0-9_-]+)", normalised):
        found.add(task_id)

    for task_id in re.findall(r"(?im)^-\s*([a-z0-9][a-z0-9_-]+)\s+\[recently-completed\]", normalised):
        found.add(task_id)

    return found


def build_local_discovery_inventory(bundle: EvidenceBundle) -> dict[str, object]:
    """Build a read-only local discovery inventory from already-loaded evidence strings.

    This does not inspect the filesystem, run commands, call models, or generate
    executable candidates. It only classifies evidence so later candidate
    generation can avoid invented files and repeated failed/completed work.
    """

    text = normalise_evidence_text(bundle)
    lowered = text.lower()

    themes: set[str] = set()

    def has_any(*needles: str) -> bool:
        return any(needle in lowered for needle in needles)

    if has_any("stale", "cleanup", "generated-noise", "state consistency", "snapshot"):
        themes.add("stale_state")

    if has_any("validation", "reporting", "diagnostic", "compile failed", "gate:"):
        themes.add("validation_reporting")

    if (
        evidence_mentions_task_pool_exhaustion(bundle)
        or has_any("task selection", "score", "scoring", "productive minimum", "best candidate below productive minimum")
    ):
        themes.add("task_selection_scoring")

    if has_any("low-value", "no-change", "repeated", "success cooldown", "reverted-success"):
        themes.add("repeated_low_value")

    if has_any("missing tests", "no tests", "coverage", "untested"):
        themes.add("missing_tests")

    if has_any("command", "help", "contract", "/help"):
        themes.add("command_help_contracts")

    completed_ids = extract_recent_completed_task_ids(bundle.roadmap)
    failed_ids = extract_recent_bad_task_ids(
        "\n".join(
            part
            for part in (
                bundle.latest_summary,
                bundle.task_pool_exhausted,
                bundle.failure_review,
            )
            if part
        )
    )

    non_meta_markers = (
        "real codebase",
        "codebase improvement",
        "non-meta",
        "source+test",
        "existing module",
        "validation reporting",
        "task selection",
        "command help",
        "stale state",
        "missing tests",
    )

    return {
        "problem_themes": sorted(themes),
        "completed_task_ids": sorted(completed_ids),
        "failed_task_ids": sorted(failed_ids),
        "task_pool_exhausted": evidence_mentions_task_pool_exhaustion(bundle),
        "asks_for_non_meta_codebase_improvements": any(marker in lowered for marker in non_meta_markers),
    }


def _inventory_backed_candidate(
    *,
    candidate_id: str,
    goal: str,
    editable: list[str],
    required_diff_contains: list[str],
    tests: list[str],
) -> dict[str, object]:
    """Build a validator-shaped non-meta candidate from an allowlisted source+test pair."""

    return {
        "Id": candidate_id,
        "Goal": goal,
        "Editable": editable,
        "RequiredChangedFiles": editable,
        "RequiredDiffContains": required_diff_contains,
        "Tests": tests,
    }


def build_inventory_backed_candidate_drafts(bundle: EvidenceBundle) -> list[dict[str, object]]:
    """Generate tiny, allowlisted non-meta candidates from local discovery inventory.

    This is intentionally pure and deterministic: it does not scan the filesystem,
    run shell commands, call models, or invent target files.
    """

    inventory = build_local_discovery_inventory(bundle)
    themes = set(inventory.get("problem_themes", []))
    blocked_ids = set(inventory.get("completed_task_ids", [])) | set(
        inventory.get("failed_task_ids", [])
    )
    exhausted = bool(inventory.get("task_pool_exhausted", False))

    candidates: list[dict[str, object]] = []

    wants_scoring_or_reporting = exhausted and (
        "task_selection_scoring" in themes
        or "validation_reporting" in themes
        or bool(inventory.get("asks_for_non_meta_codebase_improvements", False))
    )

    if wants_scoring_or_reporting:
        candidate_id = "tools-report-state-task-pool-diagnostics-v1"
        if candidate_id not in blocked_ids:
            candidates.append(
                _inventory_backed_candidate(
                    candidate_id=candidate_id,
                    goal=(
                        "Improve Nova's supervised autonomy state report with clearer "
                        "task-pool diagnostics. Update tools\\report_supervised_autonomy_state.py "
                        "to surface the latest task-pool exhaustion reason and selected candidate "
                        "score context, and verify with tests_supervised_autonomy_state_report.py."
                    ),
                    editable=[
                        "tools\\report_supervised_autonomy_state.py",
                        "tests_supervised_autonomy_state_report.py",
                    ],
                    required_diff_contains=[
                        "task-pool diagnostics",
                        "test_report",
                    ],
                    tests=["tests_supervised_autonomy_state_report.py"],
                )
            )

    if len(candidates) < 2 and (
        "task_selection_scoring" in themes or "repeated_low_value" in themes
    ):
        candidate_id = "nova-lab-autodev-sandbox-task-selection-diagnostics-v1"
        if candidate_id not in blocked_ids:
            candidates.append(
                _inventory_backed_candidate(
                    candidate_id=candidate_id,
                    goal=(
                        "Improve Nova's autonomous development sandbox with small task "
                        "selection diagnostics. Update nova_improvement_lab\\autodev_sandbox.py "
                        "to expose a deterministic task selection diagnostics helper, and verify "
                        "with tests_autodev_sandbox.py."
                    ),
                    editable=[
                        "nova_improvement_lab\\autodev_sandbox.py",
                        "tests_autodev_sandbox.py",
                    ],
                    required_diff_contains=[
                        "task_selection_diagnostics",
                        "test_autodev_sandbox_task_selection_diagnostics",
                    ],
                    tests=["tests_autodev_sandbox.py"],
                )
            )

    if exhausted and len(candidates) < 2:
        fallback_specs = [
            (
                "candidate-factory-task-pool-exhaustion-diagnostics-v1",
                (
                    "Improve Nova's autonomous candidate factory with deterministic task-pool "
                    "exhaustion diagnostics. Update nova_improvement_lab\\autonomous_candidate_factory.py "
                    "to expose a small helper for summarising exhausted candidate-pool state, and verify "
                    "with tests_autonomous_candidate_factory.py."
                ),
                [
                    "task_pool_exhaustion_diagnostics",
                    "test_candidate_factory_task_pool_exhaustion_diagnostics",
                ],
            ),
            (
                "candidate-factory-promotion-skip-reason-diagnostics-v1",
                (
                    "Improve Nova's autonomous candidate factory with deterministic promotion-skip "
                    "diagnostics. Update nova_improvement_lab\\autonomous_candidate_factory.py to expose "
                    "a small helper for explaining why generated candidates are skipped, and verify with "
                    "tests_autonomous_candidate_factory.py."
                ),
                [
                    "promotion_skip_reason_diagnostics",
                    "test_candidate_factory_promotion_skip_reason_diagnostics",
                ],
            ),
        ]

        for candidate_id, goal, required_diff_contains in fallback_specs:
            if len(candidates) >= 2:
                break
            if candidate_id in blocked_ids:
                continue
            candidates.append(
                _inventory_backed_candidate(
                    candidate_id=candidate_id,
                    goal=goal,
                    editable=[
                        "nova_improvement_lab\\autonomous_candidate_factory.py",
                        "tests_autonomous_candidate_factory.py",
                    ],
                    required_diff_contains=required_diff_contains,
                    tests=["tests_autonomous_candidate_factory.py"],
                )
            )

    return candidates[:2]

def _candidate(
    *,
    candidate_id: str,
    goal: str,
    diff_markers: Iterable[str],
) -> dict[str, object]:
    markers = list(diff_markers)
    return {
        "Id": candidate_id,
        "Goal": goal,
        "Editable": [
            "nova_improvement_lab\\autonomous_candidate_factory.py",
            "tests_autonomous_candidate_factory.py",
        ],
        "RequiredChangedFiles": [
            "nova_improvement_lab\\autonomous_candidate_factory.py",
            "tests_autonomous_candidate_factory.py",
        ],
        "RequiredDiffContains": markers,
        "Tests": ["tests_autonomous_candidate_factory.py"],
    }


def build_autonomous_candidate_drafts(bundle: EvidenceBundle, *, limit: int = 5) -> list[dict[str, object]]:
    """Build safe source+test candidate drafts from evidence.

    These drafts are intentionally about improving the factory first. Runtime
    integration should happen only after this pure layer is tested and validated.
    """
    text = normalise_evidence_text(bundle)
    lowered = text.lower()
    proposal_text = "\n".join(
        part
        for part in (
            bundle.roadmap,
            bundle.audit,
            bundle.research_notes,
        )
        if part
    ).lower()
    validation_text = "\n".join(
        part
        for part in (
            bundle.roadmap,
            bundle.latest_summary,
            bundle.task_pool_exhausted,
            bundle.audit,
            bundle.research_notes,
        )
        if part
    ).lower()
    bad_ids = extract_recent_bad_task_ids(text)

    candidates: list[dict[str, object]] = []



    if evidence_mentions_task_pool_exhaustion(bundle):
        candidates.append(
            _candidate(
                candidate_id="candidate-factory-pool-exhaustion-summary-v1",
                goal=(
                    "Improve Nova's autonomous candidate factory with one small source+test change. "
                    "Add build_task_pool_exhaustion_summary(bundle: EvidenceBundle) -> str so Nova can explain "
                    "why the candidate pool exhausted, including count of recent bad task ids and whether fresh "
                    "candidate generation is needed. Add a regression test named "
                    "test_candidate_factory_builds_task_pool_exhaustion_summary."
                ),
                diff_markers=[
                    "build_task_pool_exhaustion_summary",
                    "test_candidate_factory_builds_task_pool_exhaustion_summary",
                ],
            )
        )


    candidates.extend(build_inventory_backed_candidate_drafts(bundle))
    if bad_ids:
        candidates.append(
            _candidate(
                candidate_id="candidate-factory-bad-task-id-filter-v1",
                goal=(
                    "Improve Nova's autonomous candidate factory with one small source+test change. "
                    "Add filter_recent_bad_candidate_ids(candidates: list[dict[str, object]], bad_ids: set[str]) "
                    "-> list[dict[str, object]] so generated candidate drafts do not repeat recently failed task ids. "
                    "Add a regression test named test_candidate_factory_filters_recent_bad_candidate_ids."
                ),
                diff_markers=[
                    "filter_recent_bad_candidate_ids",
                    "test_candidate_factory_filters_recent_bad_candidate_ids",
                ],
            )
        )

    if "agent browser" in proposal_text or "browser" in proposal_text:
        candidates.append(
            _candidate(
                candidate_id="candidate-factory-agent-browser-evidence-v1",
                goal=(
                    "Improve Nova's autonomous candidate factory with one small source+test change. "
                    "Add detect_agent_browser_opportunity(bundle: EvidenceBundle) -> bool so Nova can identify "
                    "local browser-testing opportunities from research notes without installing or running browser tools. "
                    "Add a regression test named test_candidate_factory_detects_agent_browser_opportunity."
                ),
                diff_markers=[
                    "detect_agent_browser_opportunity",
                    "test_candidate_factory_detects_agent_browser_opportunity",
                ],
            )
        )

    if detect_failure_feedback_gap(bundle):
        candidates.append(
            _candidate(
                candidate_id="candidate-factory-failure-feedback-gap-v1",
                goal=(
                    "Improve Nova's autonomous candidate factory with one small source+test change. "
                    "Add summarise_failure_feedback(bundle: EvidenceBundle) -> str so Nova can summarise recent "
                    "rejected generated candidates without treating failure logs as proposal evidence. Add a regression "
                    "test named test_candidate_factory_summarises_failure_feedback."
                ),
                diff_markers=[
                    "summarise_failure_feedback",
                    "test_candidate_factory_summarises_failure_feedback",
                ],
            )
        )

    if "regression" in validation_text or "validation" in validation_text or "tests" in validation_text:
        candidates.append(
            _candidate(
                candidate_id="candidate-factory-validation-gap-v1",
                goal=(
                    "Improve Nova's autonomous candidate factory with one small source+test change. "
                    "Add detect_validation_gap(bundle: EvidenceBundle) -> bool so Nova can notice when evidence "
                    "points to missing or weak validation. Add a regression test named "
                    "test_candidate_factory_detects_validation_gap."
                ),
                diff_markers=[
                    "detect_validation_gap",
                    "test_candidate_factory_detects_validation_gap",
                ],
            )
        )

    if not candidates:
        candidates.append(
            _candidate(
                candidate_id="candidate-factory-baseline-evidence-summary-v1",
                goal=(
                    "Improve Nova's autonomous candidate factory with one small source+test change. "
                    "Add summarise_candidate_evidence(bundle: EvidenceBundle) -> str so Nova can produce a stable "
                    "local evidence summary before proposing tasks. Add a regression test named "
                    "test_candidate_factory_summarises_candidate_evidence."
                ),
                diff_markers=[
                    "summarise_candidate_evidence",
                    "test_candidate_factory_summarises_candidate_evidence",
                ],
            )
        )

    if bad_ids:
        candidates = filter_recent_bad_candidate_ids(candidates, bad_ids)

    return candidates[: max(1, limit)]


def candidate_ids(candidates: Iterable[dict[str, object]]) -> list[str]:
    """Return candidate ids as strings for reporting and tests."""
    return [str(candidate.get("Id", "")).strip() for candidate in candidates if candidate.get("Id")]


def filter_recent_bad_candidate_ids(
    candidates: List[Dict[str, object]], bad_ids: set[str]
) -> List[Dict[str, object]]:
    """Return a new list of candidates excluding any whose Id is in bad_ids."""
    return [c for c in candidates if str(c.get("Id", "")).strip() not in bad_ids]
