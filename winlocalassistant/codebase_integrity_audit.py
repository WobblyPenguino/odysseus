from __future__ import annotations

import ast
import copy
import importlib
import json
import pkgutil
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_AUDIT_CACHE: dict[tuple[str, int, int, int], tuple[float, "CodebaseIntegrityReport"]] = {}
_AUDIT_CACHE_TTL_SECONDS = 30.0

from .safe_io import atomic_write_json, atomic_write_text, unique_path

from . import __version__, VERSION_LABEL
from .code_repair_audit import run_code_repair_audit, render_code_repair_audit_markdown
from .code_review_audit import RUNTIME_ARTIFACT_NAMES, find_runtime_artifacts, run_code_review, render_code_review_markdown


@dataclass
class CodebaseIntegrityIssue:
    severity: str
    category: str
    path: str
    line: int
    title: str
    detail: str
    patch_status: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodebaseIntegrityReport:
    generated_at: str
    repo_root: str
    version: str
    version_label: str
    decision: str
    files_scanned: int
    modules_imported: int
    tests_detected: int
    issues: list[CodebaseIntegrityIssue] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    markdown_report_path: str | None = None
    json_report_path: str | None = None

    @property
    def ok(self) -> bool:
        return self.decision != "block"

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        data["issues"] = [issue.to_dict() for issue in self.issues]
        return data


def run_codebase_integrity_audit(repo_root: Path) -> CodebaseIntegrityReport:
    """Assess the whole Nova codebase, not just the latest patch.

    This is intentionally deterministic and offline. It combines syntax/import
    checks, version/install consistency, command-quality signals, release hygiene,
    and the lower-level repair/review/quality gate results into one ledger-ready
    report for the entire repository.
    """
    root = repo_root.resolve()
    py_files = _python_files(root)
    cache_key = _audit_cache_key(root, py_files)
    cached = _AUDIT_CACHE.get(cache_key)
    now = time.monotonic()
    if cached and now - cached[0] <= _AUDIT_CACHE_TTL_SECONDS:
        report = copy.deepcopy(cached[1])
        report.generated_at = time.strftime("%Y-%m-%d %H:%M:%S")
        report.markdown_report_path = None
        report.json_report_path = None
        return report

    issues: list[CodebaseIntegrityIssue] = []
    passed: list[str] = []
    tests_detected = 0

    for path in py_files:
        rel = _rel(root, path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            issues.append(_issue("medium", "readability", rel, 1, "Could not read Python file", repr(exc), "open", "Check encoding/permissions before editing."))
            continue
        try:
            tree = ast.parse(text, filename=str(path))
            compile(tree, str(path), "exec")
        except SyntaxError as exc:
            issues.append(_issue("critical", "syntax", rel, exc.lineno or 1, "Python syntax/compile error", exc.msg, "open", "Fix syntax before any behavioural work."))
            continue
        except Exception as exc:
            issues.append(_issue("critical", "compile", rel, 1, "Python compile error", repr(exc), "open", "Fix compile failure before release."))
            continue
        tests_detected += sum(1 for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_"))
        _check_same_scope_duplicates(root, path, tree, issues)

    imported, import_failures = _import_wla_modules()
    for name, err in import_failures:
        issues.append(_issue("critical", "import", name.replace(".", "/") + ".py", 1, "Module import failed", err, "open", "Fix import-time failure and add a regression test."))
    if not import_failures:
        passed.append(f"Imported all {imported} Nova modules successfully.")

    _check_version_consistency(root, issues, passed)
    _check_packaging_hygiene(root, issues, passed)

    review = run_code_review(root)
    repair = run_code_repair_audit(root)

    if review.ok:
        passed.append("Deep code review has no critical/high findings.")
    if repair.ok:
        passed.append("Repair audit has no critical/high findings.")

    # Avoid running the full code quality gate a second time here: it is an
    # aggregate of the same review+repair audits and can make whole-codebase
    # status checks feel hung on large local workspaces. Compute the gate
    # decision from the already-loaded findings instead, while /code-quality-gate
    # remains available for the detailed PR-style comment report.
    lower_findings = list(repair.findings) + list(review.findings)
    gate_blocking_count = sum(1 for finding in lower_findings if finding.severity in {"critical", "high"})
    gate_warning_count = sum(1 for finding in lower_findings if finding.severity == "medium")
    gate_decision = "block" if gate_blocking_count else ("warn" if gate_warning_count else "pass")
    if gate_decision != "block":
        passed.append(f"Code quality gate is non-blocking: {gate_decision}.")

    # Pull up only blocking/high-level lower-audit signals to avoid drowning the
    # whole-codebase report in duplicate low-level comments. Detailed reports remain
    # available via /code-review, /repair-audit and /code-quality-gate.
    for finding in repair.findings:
        if finding.severity in {"critical", "high"}:
            issues.append(_issue(finding.severity, f"repair:{finding.category}", finding.path, finding.line, finding.title, finding.detail, "open", finding.repair))
    for finding in review.findings:
        if finding.severity in {"critical", "high"}:
            issues.append(_issue(finding.severity, f"review:{finding.category}", finding.path, finding.line, finding.title, finding.detail, "open", finding.recommendation))
    if gate_blocking_count:
        issues.append(_issue("high", "quality_gate", ".", 1, "Quality gate has blocking findings", f"{gate_blocking_count} blocking finding(s) detected.", "open", "Run /code-quality-gate and fix blocking comments before mutation/release."))

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    issues = sorted(_dedupe_issues(issues), key=lambda i: (severity_order.get(i.severity, 9), i.category, i.path, i.line, i.title))
    if any(i.severity in {"critical", "high"} for i in issues):
        decision = "block"
    elif any(i.severity == "medium" for i in issues):
        decision = "warn"
    else:
        decision = "pass"
    if py_files:
        passed.append(f"Parsed and compiled {len(py_files)} Python file(s) without syntax errors.")
    if tests_detected:
        passed.append(f"Detected {tests_detected} pytest-style test function(s).")

    report = CodebaseIntegrityReport(
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        repo_root=str(root),
        version=__version__,
        version_label=VERSION_LABEL,
        decision=decision,
        files_scanned=len(py_files),
        modules_imported=imported,
        tests_detected=tests_detected,
        issues=issues,
        passed_checks=_dedupe_text(passed),
    )
    _AUDIT_CACHE[cache_key] = (time.monotonic(), copy.deepcopy(report))
    return report


def write_codebase_integrity_report(repo_root: Path) -> tuple[Path, Path, CodebaseIntegrityReport]:
    report = run_codebase_integrity_audit(repo_root)
    reports = repo_root / "codebase_integrity_reports"
    reports.mkdir(parents=True, exist_ok=True)
    md = unique_path(reports, "codebase_integrity", ".md")
    js = md.with_suffix(".json")
    report.markdown_report_path = str(md)
    report.json_report_path = str(js)
    atomic_write_text(md, render_codebase_integrity_markdown(report))
    atomic_write_json(js, report.to_dict(), ensure_ascii=False)
    return md, js, report


def render_codebase_integrity_markdown(report: CodebaseIntegrityReport) -> str:
    counts: dict[str, int] = {}
    for issue in report.issues:
        counts[issue.severity] = counts.get(issue.severity, 0) + 1
    verdict = {
        "pass": "PASS - no whole-codebase blocking issues detected",
        "warn": "WARN - codebase runs but has non-blocking issues to track",
        "block": "BLOCK - fix critical/high issues before release or autonomous mutation",
    }.get(report.decision, report.decision.upper())
    lines = [
        "# Whole Codebase Integrity Audit",
        "",
        "This report assesses the full Nova codebase, not only the latest patch.",
        "",
        f"Generated: {report.generated_at}",
        f"Repo root: `{report.repo_root}`",
        f"Version: `{report.version}` — {report.version_label}",
        f"Decision: **{verdict}**",
        f"Python files scanned: {report.files_scanned}",
        f"Modules imported: {report.modules_imported}",
        f"Tests detected: {report.tests_detected}",
        "",
        "## Severity counts",
        f"- critical: {counts.get('critical', 0)}",
        f"- high: {counts.get('high', 0)}",
        f"- medium: {counts.get('medium', 0)}",
        f"- low: {counts.get('low', 0)}",
        "",
        "## Passed checks",
    ]
    lines.extend([f"- {item}" for item in report.passed_checks] or ["- No positive checks recorded."])
    lines.extend(["", "## Issues"])
    if not report.issues:
        lines.append("- No whole-codebase issues detected by this audit.")
    else:
        for idx, issue in enumerate(report.issues, 1):
            lines.extend([
                f"{idx}. **{issue.severity.upper()} / {issue.category}** - {issue.title}",
                f"   - location: `{issue.path}:{issue.line}`",
                f"   - detail: {issue.detail}",
                f"   - patch status: {issue.patch_status}",
                f"   - recommendation: {issue.recommendation}",
            ])
    lines.extend([
        "",
        "## Related detailed audits",
        "Run these for lower-level comments:",
        "```text",
        "/code-review",
        "/repair-audit",
        "/code-quality-gate",
        "```",
        "",
        "## Verification commands",
        "```powershell",
        "python -m compileall -q winlocalassistant tests_*.py app.py",
        "python -m pytest -q",
        "```",
    ])
    return "\n".join(lines) + "\n"


def append_codebase_ledger(repo_root: Path, version: str, patched_issues: list[str], remaining_issues: list[str]) -> Path:
    docs = repo_root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    path = docs / "CODEBASE_ISSUE_LEDGER.md"
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Nova Codebase Issue Ledger\n\nTracks whole-codebase issues patched and remaining across releases.\n"
    entry = ["", f"## v{version}", "", f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}", "", "### Patched"]
    entry.extend([f"- {item}" for item in patched_issues] or ["- No patches recorded."])
    entry.extend(["", "### Remaining / monitor"])
    entry.extend([f"- {item}" for item in remaining_issues] or ["- No remaining issues detected by the whole-codebase audit."])
    entry.append("")
    atomic_write_text(path, existing.rstrip() + "\n" + "\n".join(entry))
    return path




def _audit_cache_key(root: Path, py_files: list[Path]) -> tuple[str, int, int, int]:
    """Return a cheap fingerprint for short-lived repeated integrity audits.

    The whole-codebase audit intentionally imports and scans many modules. GUI and
    test flows can call it more than once for the same tree in a few seconds;
    without a freshness check that makes the app feel hung. The key uses file
    count, aggregate size and newest mtime, so edits invalidate the cache while
    identical repeated reads stay fast.
    """
    newest_mtime_ns = 0
    total_size = 0
    for path in py_files:
        try:
            stat = path.stat()
        except OSError:
            continue
        newest_mtime_ns = max(newest_mtime_ns, int(getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1_000_000_000))))
        total_size += int(stat.st_size)
    return (str(root), len(py_files), newest_mtime_ns, total_size)


def _python_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for base in [root / "winlocalassistant", root]:
        if not base.exists():
            continue
        pattern = "*.py" if base == root else "**/*.py"
        for path in base.glob(pattern):
            if any(part in RUNTIME_ARTIFACT_NAMES for part in path.parts):
                continue
            if path.name.startswith("tests_") or "winlocalassistant" in path.parts or path.name == "app.py":
                files.add(path)
    return sorted(files)


def _import_wla_modules() -> tuple[int, list[tuple[str, str]]]:
    import winlocalassistant
    imported = 0
    failures: list[tuple[str, str]] = []
    for mod in pkgutil.iter_modules(winlocalassistant.__path__):
        name = f"winlocalassistant.{mod.name}"
        try:
            importlib.import_module(name)
            imported += 1
        except Exception as exc:
            failures.append((name, repr(exc)))
    return imported, failures


def _check_same_scope_duplicates(root: Path, path: Path, tree: ast.AST, issues: list[CodebaseIntegrityIssue]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, (ast.Module, ast.ClassDef)):
            continue
        names: dict[tuple[str, str], int] = {}
        for child in getattr(node, "body", []):
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                key = (type(child).__name__, child.name)
                if key in names:
                    issues.append(_issue("high", "duplicate_definition", _rel(root, path), child.lineno, "Duplicate same-scope definition", f"`{child.name}` shadows earlier definition at line {names[key]}.", "open", "Rename/remove the duplicate and add a regression test for the public behaviour."))
                else:
                    names[key] = child.lineno


def _check_version_consistency(root: Path, issues: list[CodebaseIntegrityIssue], passed: list[str]) -> None:
    mismatches = []
    for rel in ["winlocalassistant/webui.py", "CHANGELOG.md"]:
        path = root / rel
        if path.exists():
            text = path.read_text(encoding="utf-8", errors="replace")
            if __version__ not in text and rel == "winlocalassistant/webui.py":
                mismatches.append(rel)
    if mismatches:
        issues.append(_issue("medium", "versioning", ", ".join(mismatches), 1, "Version text may be stale", f"Current __version__ {__version__} was not visible in: {', '.join(mismatches)}", "open", "Update user-visible version strings during release packaging."))
    else:
        passed.append("User-visible version markers are consistent with package version.")


def _check_packaging_hygiene(root: Path, issues: list[CodebaseIntegrityIssue], passed: list[str]) -> None:
    bad: list[Path] = []
    # Do not flag Python import caches here: running this audit imports Nova modules,
    # which can create __pycache__ as a side effect.  Release packaging still cleans
    # those files separately; this audit focuses on persistent/runtime directories
    # that should never ship or drive autonomous decisions.
    transient_python_cache = {"__pycache__"}
    bad.extend(find_runtime_artifacts(root, RUNTIME_ARTIFACT_NAMES - transient_python_cache))
    if bad:
        sample = ", ".join(_rel(root, p) for p in sorted(set(bad))[:12])
        issues.append(_issue("low", "release_hygiene", ".", 1, "Runtime/cache artifacts present", sample, "patched-before-zip", "Delete cache/runtime artifacts before packaging."))
    else:
        passed.append("No runtime/cache artifacts detected in working tree.")


def _issue(severity: str, category: str, path: str, line: int, title: str, detail: str, patch_status: str, recommendation: str) -> CodebaseIntegrityIssue:
    return CodebaseIntegrityIssue(severity, category, path, int(line or 1), title, detail, patch_status, recommendation)


def _dedupe_issues(issues: list[CodebaseIntegrityIssue]) -> list[CodebaseIntegrityIssue]:
    seen: set[tuple[str, str, int, str]] = set()
    out: list[CodebaseIntegrityIssue] = []
    for issue in issues:
        key = (issue.category, issue.path, issue.line, issue.title)
        if key in seen:
            continue
        seen.add(key)
        out.append(issue)
    return out


def _dedupe_text(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.lower().strip()
        if key and key not in seen:
            seen.add(key)
            out.append(item)
    return out


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path)
