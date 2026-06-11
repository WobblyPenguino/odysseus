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
from typing import Iterable


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


def extract_recent_bad_task_ids(text: str) -> set[str]:
    """Extract task ids tied to recent bad outcomes from evidence lines."""
    bad_ids: set[str] = set()

    for line in text.splitlines():
        lowered = line.lower()
        if not any(marker in lowered for marker in BAD_OUTCOME_MARKERS):
            continue

        quoted = re.findall(r"task '([^']+)'", line)
        for task_id in quoted:
            if task_id.strip():
                bad_ids.add(task_id.strip())

        leading = re.match(r"\s*-\s*([a-z0-9][a-z0-9_-]+):", line, flags=re.IGNORECASE)
        if leading:
            bad_ids.add(leading.group(1))

    return bad_ids


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

    if "agent browser" in lowered or "browser" in lowered:
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

    if "regression" in lowered or "validation" in lowered or "tests" in lowered:
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

    return candidates[: max(1, limit)]


def candidate_ids(candidates: Iterable[dict[str, object]]) -> list[str]:
    """Return candidate ids as strings for reporting and tests."""
    return [str(candidate.get("Id", "")).strip() for candidate in candidates if candidate.get("Id")]
