from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text, unique_path

from .code_repair_audit import run_code_repair_audit
from .code_review_audit import run_code_review

BLOCKING_SEVERITIES = {"critical", "high"}
WARNING_SEVERITIES = {"medium"}


@dataclass
class ReviewComment:
    severity: str
    category: str
    path: str
    line: int
    title: str
    body: str
    suggestion: str
    confidence: str = "medium"
    blocking: bool = False
    source: str = "code_quality_gate"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodeQualityGateReport:
    generated_at: str
    repo_root: str
    decision: str
    files_scanned: int
    blocking_count: int
    warning_count: int
    note_count: int
    comments: list[ReviewComment] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    markdown_report_path: str | None = None
    json_report_path: str | None = None
    total_comment_count: int = 0
    total_blocking_count: int = 0
    total_warning_count: int = 0
    total_note_count: int = 0
    displayed_comment_count: int = 0
    truncated_comment_count: int = 0

    @property
    def ok(self) -> bool:
        return self.decision != "block"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        data["comments"] = [comment.to_dict() for comment in self.comments]
        return data


def run_code_quality_gate(repo_root: Path, *, max_comments: int = 120) -> CodeQualityGateReport:
    """Run a deterministic CodeRabbit-style verification pass.

    This does not call an external service. It mimics the useful behaviour of an
    automated PR reviewer: aggregate low-level audits, turn them into concise
    file/line comments, mark which ones block mutation, and produce a merge/gate
    verdict that autonomous mode can use before accepting code changes.
    """
    root = repo_root.resolve()
    review = run_code_review(root)
    repair = run_code_repair_audit(root)
    comments: list[ReviewComment] = []

    for finding in review.findings:
        comments.append(_comment_from_review_finding(finding.to_dict(), "deep_code_review"))
    for finding in repair.findings:
        comments.append(_comment_from_repair_finding(finding.to_dict(), "repair_audit"))

    all_comments = _dedupe_comments(comments)
    all_comments = sorted(all_comments, key=lambda c: (_severity_rank(c.severity), c.path, c.line, c.title))
    total_blocking = sum(1 for c in all_comments if c.blocking)
    total_warnings = sum(1 for c in all_comments if c.severity in WARNING_SEVERITIES)
    total_notes = len(all_comments) - total_blocking - total_warnings

    if total_blocking:
        decision = "block"
    elif total_warnings:
        decision = "warn"
    else:
        decision = "pass"

    displayed_comments = all_comments[: max(0, int(max_comments))]
    blocking = sum(1 for c in displayed_comments if c.blocking)
    warnings = sum(1 for c in displayed_comments if c.severity in WARNING_SEVERITIES)
    notes = len(displayed_comments) - blocking - warnings

    passed = []
    passed.extend(review.passed_checks[:12])
    passed.extend(repair.passed_checks[:12])
    if not total_blocking:
        passed.append("No critical/high deterministic review findings block autonomous mutation.")
    if review.ok and repair.ok:
        passed.append("Deep review and repair audit both returned non-blocking status.")

    return CodeQualityGateReport(
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        repo_root=str(root),
        decision=decision,
        files_scanned=max(review.files_scanned, repair.files_scanned),
        blocking_count=blocking,
        warning_count=warnings,
        note_count=notes,
        comments=displayed_comments,
        passed_checks=_dedupe_text(passed),
        total_comment_count=len(all_comments),
        total_blocking_count=total_blocking,
        total_warning_count=total_warnings,
        total_note_count=total_notes,
        displayed_comment_count=len(displayed_comments),
        truncated_comment_count=max(0, len(all_comments) - len(displayed_comments)),
    )


def write_code_quality_gate_report(repo_root: Path) -> tuple[Path, Path, CodeQualityGateReport]:
    report = run_code_quality_gate(repo_root)
    reports = repo_root / "code_quality_gates"
    reports.mkdir(parents=True, exist_ok=True)
    md = unique_path(reports, "code_quality_gate", ".md")
    js = md.with_suffix(".json")
    report.markdown_report_path = str(md)
    report.json_report_path = str(js)
    atomic_write_text(md, render_code_quality_gate_markdown(report))
    atomic_write_json(js, report.to_dict(), ensure_ascii=False)
    return md, js, report


def render_code_quality_gate_markdown(report: CodeQualityGateReport) -> str:
    verdict = {
        "pass": "PASS - no blocking deterministic review comments",
        "warn": "WARN - non-blocking quality issues should be prioritised",
        "block": "BLOCK - fix blocking comments before autonomous mutation or release",
    }.get(report.decision, report.decision.upper())
    lines = [
        "# Code Quality Gate",
        "",
        "CodeRabbit-style local verification: structured PR-review comments, severity, file/line references, suggested fixes and a gate verdict. This is local/deterministic and does not require CodeRabbit SaaS.",
        "",
        f"Generated: {report.generated_at}",
        f"Repo root: `{report.repo_root}`",
        f"Files scanned: {report.files_scanned}",
        f"Decision: **{verdict}**",
        "",
        "## Counts",
        f"- displayed blocking: {report.blocking_count}",
        f"- displayed warning: {report.warning_count}",
        f"- displayed notes: {report.note_count}",
        f"- total comments found: {report.total_comment_count}",
        f"- total blocking found: {report.total_blocking_count}",
        f"- total warnings found: {report.total_warning_count}",
        f"- total notes found: {report.total_note_count}",
        f"- hidden by display cap: {report.truncated_comment_count}",
        "",
        "## Passed checks",
    ]
    lines.extend([f"- {item}" for item in report.passed_checks] or ["- No positive checks recorded."])
    lines.extend(["", "## Review comments"])
    if not report.comments:
        lines.append("- No review comments.")
    else:
        for idx, comment in enumerate(report.comments[:90], 1):
            block = "BLOCKING" if comment.blocking else "non-blocking"
            lines.extend([
                f"{idx}. **{comment.severity.upper()} / {comment.category} / {block}** - {comment.title}",
                f"   - location: `{comment.path}:{comment.line}`",
                f"   - source: `{comment.source}`; confidence: {comment.confidence}",
                f"   - why it matters: {comment.body}",
                f"   - suggested fix: {comment.suggestion}",
            ])
        hidden = max(0, int(report.total_comment_count or 0) - min(90, int(report.displayed_comment_count or len(report.comments))))
        if hidden:
            lines.append(f"- {hidden} additional comments are available in the JSON report or were hidden by the display cap.")
    lines.extend([
        "",
        "## Autonomous policy",
        "- PASS: autonomous mode may continue to project verification/build steps if other health gates pass.",
        "- WARN: autonomous mode may continue, but should prefer small, test-backed changes and address warnings soon.",
        "- BLOCK: autonomous mode should skip mutation/release steps and report the blocking comments first.",
        "",
        "## Suggested verification commands",
        "```powershell",
        "python -m compileall -q winlocalassistant tests_*.py",
        "python -m pytest -q",
        "```",
    ])
    return "\n".join(lines) + "\n"


def _comment_from_review_finding(f: dict[str, Any], source: str) -> ReviewComment:
    sev = str(f.get("severity") or "low")
    return ReviewComment(
        severity=sev,
        category=str(f.get("category") or "quality"),
        path=str(f.get("path") or "."),
        line=int(f.get("line") or 1),
        title=str(f.get("title") or "Code review finding"),
        body=str(f.get("detail") or "Review this code-quality signal."),
        suggestion=str(f.get("recommendation") or "Apply the smallest test-backed fix."),
        confidence=_confidence_for(sev, str(f.get("category") or "")),
        blocking=sev in BLOCKING_SEVERITIES,
        source=source,
    )


def _comment_from_repair_finding(f: dict[str, Any], source: str) -> ReviewComment:
    sev = str(f.get("severity") or "low")
    return ReviewComment(
        severity=sev,
        category=str(f.get("category") or "repair"),
        path=str(f.get("path") or "."),
        line=int(f.get("line") or 1),
        title=str(f.get("title") or "Repair audit finding"),
        body=str(f.get("detail") or "Repair audit flagged this location."),
        suggestion=str(f.get("repair") or "Apply the smallest safe repair and rerun tests."),
        confidence=_confidence_for(sev, str(f.get("category") or "")),
        blocking=sev in BLOCKING_SEVERITIES,
        source=source,
    )


def _confidence_for(severity: str, category: str) -> str:
    if severity in {"critical", "high"}:
        return "high"
    if category in {"syntax", "correctness", "release_hygiene"}:
        return "high"
    if severity == "medium":
        return "medium"
    return "low"


def _dedupe_comments(comments: list[ReviewComment]) -> list[ReviewComment]:
    seen: set[tuple[str, int, str, str]] = set()
    out: list[ReviewComment] = []
    for c in comments:
        key = (c.path, c.line, c.title.lower().strip(), c.category.lower().strip())
        if key in seen:
            continue
        seen.add(key)
        out.append(c)
    return out


def _dedupe_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        text = str(item).strip()
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _severity_rank(value: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(str(value), 4)
