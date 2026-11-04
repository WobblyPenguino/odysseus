"""Autonomy readiness reporting for Nova.

This module is read-only and side-effect free. It inspects the local repository
for the capability surfaces Nova needs before it can safely keep improving a
project over repeated cycles.
"""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class ReadinessCheck:
    area: str
    name: str
    ok: bool
    evidence: str
    next_action: str = ""
    blocking: bool = False

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _has_file(root: Path, relative: str) -> bool:
    return (root / relative).exists()


def _file_contains(root: Path, relative: str, tokens: Iterable[str]) -> bool:
    text = _read_text(root / relative)
    return all(token in text for token in tokens)


def _check_file(root: Path, area: str, relative: str, purpose: str, *, blocking: bool = False) -> ReadinessCheck:
    ok = _has_file(root, relative)
    return ReadinessCheck(
        area=area,
        name=relative,
        ok=ok,
        evidence="present" if ok else "missing",
        next_action="" if ok else f"Restore or add {relative} for {purpose}.",
        blocking=blocking,
    )


def _check_tokens(
    root: Path,
    area: str,
    relative: str,
    tokens: list[str],
    purpose: str,
    *,
    blocking: bool = False,
) -> ReadinessCheck:
    path = root / relative
    text = _read_text(path)
    missing = [token for token in tokens if token not in text]
    ok = path.exists() and not missing
    evidence = "all required markers present" if ok else "missing marker(s): " + ", ".join(missing[:6])
    return ReadinessCheck(
        area=area,
        name=relative,
        ok=ok,
        evidence=evidence,
        next_action="" if ok else f"Update {relative} so Nova can support {purpose}.",
        blocking=blocking,
    )


def _check_task_pool_health(root: Path) -> ReadinessCheck:
    """Treat current task-pool exhaustion evidence as a blocking readiness issue."""

    pool_relative = "local_ai_cycles/memory/NOVA_TASK_POOL_EXHAUSTED_LATEST.md"
    summary_relative = "local_ai_cycles/memory/NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    pool_path = root / pool_relative
    summary_path = root / summary_relative

    pool_text = _read_text(pool_path).lower()
    summary_text = _read_text(summary_path).lower()

    exhausted_markers = (
        "no sufficiently productive task remained",
        "task-pool-exhausted",
        "task pool is exhausted",
        "best candidate below productive minimum",
        "no aider invocation, commit, or source edit was attempted because the task pool is exhausted",
    )
    summary_exhausted = any(marker in summary_text for marker in exhausted_markers)
    pool_exhausted = any(marker in pool_text for marker in exhausted_markers)
    exhausted = summary_exhausted or pool_exhausted

    fallback_score_match = re.search(r"autonomous candidate fallback score:\s*(-?\d+)", summary_text)
    fallback_score = int(fallback_score_match.group(1)) if fallback_score_match else 0

    recovered_by_autonomous_fallback = (
        "result: preflight-only" in summary_text
        and "autonomous candidate fallback selected productive task:" in summary_text
        and "autonomous candidate fallback score:" in summary_text
        and "selected task:" in summary_text
        and (
            "source+test candidate" in summary_text
            or "editable files:" in summary_text
            or "targeted tests:" in summary_text
        )
        and fallback_score >= 70
    )

    successful_committed_fallback = (
        "result: committed" in summary_text
        and "validation gates passed" in summary_text
        and (
            "autonomous candidate fallback selected productive task" in summary_text
            or "best task candidate candidate-factory-" in summary_text
        )
    )

    if exhausted and not (recovered_by_autonomous_fallback or successful_committed_fallback):
        evidence_source = summary_relative if summary_exhausted else pool_relative
        return ReadinessCheck(
            area="candidate pool",
            name=evidence_source,
            ok=False,
            evidence="latest task-loop evidence reports no sufficiently productive task remained",
            next_action=(
                "Add or approve fresh source-backed candidates, then run a preflight before any live autonomy cycle."
            ),
            blocking=True,
        )

    if successful_committed_fallback:
        return ReadinessCheck(
            area="candidate pool",
            name=summary_relative,
            ok=True,
            evidence="latest task-loop evidence shows autonomous fallback committed and passed validation",
            next_action="",
            blocking=True,
        )

    if recovered_by_autonomous_fallback:
        return ReadinessCheck(
            area="candidate pool",
            name=summary_relative,
            ok=True,
            evidence="latest task-loop evidence shows autonomous fallback selected a productive candidate",
            next_action="",
            blocking=True,
        )

    if pool_path.exists() or summary_path.exists():
        return ReadinessCheck(
            area="candidate pool",
            name=f"{pool_relative}; {summary_relative}",
            ok=True,
            evidence="latest task-loop evidence does not show task-pool exhaustion",
            next_action="",
            blocking=True,
        )

    return ReadinessCheck(
        area="candidate pool",
        name=f"{pool_relative}; {summary_relative}",
        ok=True,
        evidence="no latest task-pool exhaustion or task-loop summary report found",
        next_action="",
        blocking=True,
    )

def build_autonomy_readiness(root: str | Path = ".") -> dict[str, object]:
    """Build a deterministic readiness report for Nova's autonomy loop."""

    root_path = Path(root).expanduser().resolve()

    checks: list[ReadinessCheck] = [
        _check_tokens(
            root_path,
            "task selection",
            "run_nova_task_queue_loop.ps1",
            ["function Pick-Task", "Resolve-TaskScore", "Get-TaskSignalSeverityPenalty"],
            "scored task selection with failure-severity ranking",
            blocking=True,
        ),
        _check_tokens(
            root_path,
            "failure recovery",
            "run_nova_task_queue_loop.ps1",
            ["Write-TaskFailureReviewReport", "NOVA_TASK_FAILURE_REVIEW_LATEST.md", "Record-TaskOutcome"],
            "failure review and structured outcome memory",
            blocking=True,
        ),
        _check_tokens(
            root_path,
            "validation",
            "tools/validate_task_loop_patch.ps1",
            ["tests_task_loop_static_contract.py", "validate_idea_promotion_candidates.py", "Validation passed"],
            "repeatable task-loop validation",
            blocking=True,
        ),
        _check_file(
            root_path,
            "validation",
            "tests_task_loop_static_contract.py",
            "static task-loop contracts",
            blocking=True,
        ),
        _check_tokens(
            root_path,
            "roadmap memory",
            "tools/update_task_loop_roadmap.py",
            ["NOVA_TASK_LOOP_ROADMAP", "last_updated", "latest_commits"],
            "living roadmap updates",
        ),
        _check_file(
            root_path,
            "roadmap memory",
            "docs/NOVA_TASK_LOOP_ROADMAP.md",
            "current development memory",
        ),
        _check_tokens(
            root_path,
            "screen context",
            "winlocalassistant/screen_analysis.py",
            ["classify_screen_context_need", "build_screen_analysis_prompt", "render_screen_analysis_prompt_help"],
            "manual screenshot/image analysis flow",
        ),
        _check_tokens(
            root_path,
            "tool routing",
            "winlocalassistant/tools.py",
            ["screen_analysis_prompt", "image_analyze", "ToolRegistry"],
            "tool registry access to vision and screen-analysis helpers",
            blocking=True,
        ),
        _check_tokens(
            root_path,
            "command routing",
            "winlocalassistant/core.py",
            ["/screen-analysis-prompt", "/image-analyze", "handle_command"],
            "user-facing command access",
            blocking=True,
        ),
        _check_file(
            root_path,
            "candidate pool",
            "local_ai_cycles/config/NOVA_IDEA_PROMOTION_CANDIDATES.json",
            "fresh task candidates",
            blocking=True,
        ),
        _check_task_pool_health(root_path),
        _check_file(
            root_path,
            "audit evidence",
            "docs/NOVA_AUTONOMY_FULL_CODEBASE_AUDIT.md",
            "autonomy audit trail",
        ),
    ]

    ok_count = sum(1 for check in checks if check.ok)
    total = len(checks)
    score = round((ok_count / total) * 100) if total else 0
    blocking_failures = [check for check in checks if check.blocking and not check.ok]

    if blocking_failures:
        status = "not-ready"
    elif score >= 90:
        status = "ready-for-supervised-longer-runs"
    elif score >= 70:
        status = "ready-for-short-supervised-runs"
    else:
        status = "not-ready"

    next_actions = [check.next_action for check in checks if not check.ok and check.next_action]

    if not next_actions and status != "ready-for-supervised-longer-runs":
        next_actions.append("Run one preflight and inspect task ranking before any live autonomy cycle.")
    elif not next_actions:
        next_actions.append("Run a short supervised task-loop preflight, then one live cycle only if the tree is clean.")

    return {
        "root": str(root_path),
        "score": score,
        "status": status,
        "passed": ok_count,
        "total": total,
        "checks": [check.to_dict() for check in checks],
        "blocking_failures": [check.to_dict() for check in blocking_failures],
        "next_actions": next_actions,
    }


def render_autonomy_readiness_markdown(report: dict[str, object]) -> str:
    """Render an autonomy readiness report as Markdown."""

    checks = list(report.get("checks", []))
    blocking_failures = list(report.get("blocking_failures", []))
    next_actions = list(report.get("next_actions", []))

    lines = [
        "# Nova Autonomy Readiness",
        "",
        f"Status: **{report.get('status', 'unknown')}**",
        f"Score: **{report.get('score', 0)} / 100**",
        f"Checks: `{report.get('passed', 0)}` / `{report.get('total', 0)}` passing",
        f"Root: `{report.get('root', '')}`",
        "",
    ]

    if blocking_failures:
        lines += ["## Blocking issues"]
        for issue in blocking_failures:
            lines.append(
                f"- `{issue.get('area')}` / `{issue.get('name')}` — {issue.get('evidence')}"
            )
        lines.append("")

    lines.append("## Checks")
    for check in checks:
        mark = "PASS" if check.get("ok") else "FAIL"
        blocking = " blocking" if check.get("blocking") else ""
        lines.append(
            f"- **{mark}**{blocking} `{check.get('area')}` / `{check.get('name')}` — {check.get('evidence')}"
        )

    lines += ["", "## Next actions"]
    for action in next_actions:
        lines.append(f"- {action}")

    lines += [
        "",
        "## Safety note",
        "- This report is read-only. It does not run Aider, edit files, capture the screen, or start autonomy.",
    ]

    return "\n".join(lines)
