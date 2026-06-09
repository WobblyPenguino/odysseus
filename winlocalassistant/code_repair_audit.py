from __future__ import annotations

import ast
import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text, unique_path

RUNTIME_ARTIFACT_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
MUTATION_TOOL_NAMES = {"ai_create_project", "ai_edit_project", "improve_project", "surgical_repair", "backtrack_recover", "self_improve", "write_files", "append_file", "find_replace"}


@dataclass
class CodeRepairFinding:
    severity: str
    category: str
    path: str
    line: int
    title: str
    detail: str
    repair: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodeRepairAuditReport:
    generated_at: str
    repo_root: str
    files_scanned: int
    findings: list[CodeRepairFinding] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    markdown_report_path: str | None = None
    json_report_path: str | None = None

    @property
    def ok(self) -> bool:
        return not any(f.severity in {"high", "critical"} for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        data["findings"] = [f.to_dict() for f in self.findings]
        return data


def run_code_repair_audit(repo_root: Path) -> CodeRepairAuditReport:
    root = repo_root.resolve()
    py_files = _python_files(root)
    findings: list[CodeRepairFinding] = []
    passed: list[str] = []
    parsed_files = 0
    if not py_files:
        findings.append(CodeRepairFinding(
            "high", "targeting", ".", 1,
            "No Python source files found at audit target",
            f"The audit target `{root}` contains no Python files. This usually means Nova/project autonomous routing selected the wrong workspace.",
            "Resolve the intended Nova source or project root before running code repair/quality gates.",
        ))
        return CodeRepairAuditReport(
            generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
            repo_root=str(root),
            files_scanned=0,
            findings=findings,
            passed_checks=["No Python files were scanned; autonomous guard checks were skipped to avoid false NOVA-core findings."],
        )
    for path in py_files:
        rel = _rel(root, path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            findings.append(CodeRepairFinding("medium", "readability", rel, 1, "Could not read Python file", repr(exc), "Check file permissions or encoding."))
            continue
        try:
            tree = ast.parse(text, filename=str(path))
            parsed_files += 1
        except SyntaxError as exc:
            findings.append(CodeRepairFinding("critical", "syntax", rel, exc.lineno or 1, "Python syntax error", exc.msg, "Fix syntax first, then run python -m compileall -q winlocalassistant tests_*.py."))
            continue
        _check_duplicate_defs(root, path, tree, findings)
        _check_empty_broad_except(root, path, tree, findings, text)
        _check_large_functions(root, path, tree, findings)
    _check_runtime_artifacts(root, findings)
    _check_autonomous_guards(root, findings, passed)
    if parsed_files == len(py_files):
        passed.append("All scanned Python files parsed successfully.")
    if not any(f.category == "release_hygiene" for f in findings):
        passed.append("No cache/runtime artifacts were found in the working tree.")
    return CodeRepairAuditReport(
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        repo_root=str(root),
        files_scanned=len(py_files),
        findings=findings,
        passed_checks=passed,
    )


def write_code_repair_audit_report(repo_root: Path) -> tuple[Path, Path, CodeRepairAuditReport]:
    report = run_code_repair_audit(repo_root)
    reports = repo_root / "repair_audits"
    reports.mkdir(parents=True, exist_ok=True)
    md = unique_path(reports, "code_repair_audit", ".md")
    js = md.with_suffix(".json")
    report.markdown_report_path = str(md)
    report.json_report_path = str(js)
    atomic_write_text(md, render_code_repair_audit_markdown(report))
    atomic_write_json(js, report.to_dict(), ensure_ascii=False)
    return md, js, report


def render_code_repair_audit_markdown(report: CodeRepairAuditReport) -> str:
    lines = [
        "# Code Repair Audit",
        "",
        f"Generated: {report.generated_at}",
        f"Repo root: `{report.repo_root}`",
        f"Python files scanned: {report.files_scanned}",
        f"High-risk clean: {report.ok}",
        "",
        "## Passed checks",
    ]
    lines.extend([f"- {item}" for item in report.passed_checks] or ["- No positive checks recorded."])
    lines.extend(["", "## Findings"])
    if not report.findings:
        lines.append("- No repair findings detected.")
    else:
        for i, finding in enumerate(report.findings, 1):
            lines.extend([
                f"{i}. **{finding.severity.upper()} / {finding.category}** - {finding.title}",
                f"   - location: `{finding.path}:{finding.line}`",
                f"   - detail: {finding.detail}",
                f"   - repair: {finding.repair}",
            ])
    lines.extend([
        "",
        "## Recommended repair order",
        "1. Fix critical syntax/import errors first.",
        "2. Remove runtime/cache artifacts before packaging.",
        "3. Add tests for any changed autonomous or project-generation path.",
        "4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.",
    ])
    return "\n".join(lines) + "\n"


def _python_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for base in [root / "winlocalassistant", root]:
        if not base.exists():
            continue
        pattern = "*.py" if base == root else "**/*.py"
        for path in base.glob(pattern):
            if _skip_path(path):
                continue
            if path.name.startswith("tests_") or "winlocalassistant" in path.parts:
                files.append(path)
    return sorted(set(files))


def _skip_path(path: Path) -> bool:
    return any(part in RUNTIME_ARTIFACT_NAMES for part in path.parts)


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path)


def _check_duplicate_defs(root: Path, path: Path, tree: ast.AST, findings: list[CodeRepairFinding]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.Module, ast.ClassDef)):
            names: dict[str, int] = {}
            for child in getattr(node, "body", []):
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                    if child.name in names:
                        findings.append(CodeRepairFinding(
                            "high", "maintainability", _rel(root, path), child.lineno,
                            "Duplicate definition shadows earlier code",
                            f"`{child.name}` is defined again in the same scope; earlier line {names[child.name]} will be shadowed.",
                            "Rename or remove the duplicate definition and add a regression test for the public behaviour.",
                        ))
                    else:
                        names[child.name] = child.lineno


def _check_empty_broad_except(root: Path, path: Path, tree: ast.AST, findings: list[CodeRepairFinding], text: str) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        catches_broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception")
        if not catches_broad:
            continue
        body = [stmt for stmt in node.body if not (isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and isinstance(stmt.value.value, str))]
        if len(body) == 1 and isinstance(body[0], ast.Pass):
            nearby = "\n".join(text.splitlines()[max(0, node.lineno - 10):node.lineno + 1])
            if "log_activity(" in nearby or "log_model_io(" in nearby:
                continue
            findings.append(CodeRepairFinding(
                "medium", "observability", _rel(root, path), node.lineno,
                "Broad exception is silently swallowed",
                "A bare `except Exception: pass` hides the root cause from logs and autonomous repair memory.",
                "Log the exception with context, or narrow the exception type and explain why it is safe to ignore.",
            ))


def _check_large_functions(root: Path, path: Path, tree: ast.AST, findings: list[CodeRepairFinding]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, "end_lineno", node.lineno)
            length = int(end or node.lineno) - int(node.lineno) + 1
            if length > 220:
                findings.append(CodeRepairFinding(
                    "low", "maintainability", _rel(root, path), node.lineno,
                    "Very large function",
                    f"`{node.name}` is {length} lines long, which makes autonomous repair riskier.",
                    "Extract deterministic helper functions behind tests instead of editing the large function directly.",
                ))


def _check_runtime_artifacts(root: Path, findings: list[CodeRepairFinding]) -> None:
    bad: list[Path] = []
    # Ignore import-created Python caches during live audits; release packaging
    # still removes __pycache__ and .pyc files before producing a zip.
    transient_python_cache = {"__pycache__"}
    for name in RUNTIME_ARTIFACT_NAMES - transient_python_cache:
        bad.extend(p for p in root.rglob(name) if p.exists())
    for path in sorted(set(bad))[:25]:
        findings.append(CodeRepairFinding(
            "low", "release_hygiene", _rel(root, path), 1,
            "Runtime/cache artifact present",
            "Generated cache files should not be shipped in release zips.",
            "Delete cache/runtime artifacts before packaging and keep .gitignore rules in place.",
        ))


def _check_autonomous_guards(root: Path, findings: list[CodeRepairFinding], passed: list[str]) -> None:
    core = root / "winlocalassistant" / "core.py"
    text = core.read_text(encoding="utf-8", errors="replace") if core.exists() else ""
    required = ["_call_tool_for_autonomous", "_autonomous_base_health_allows_mutation", "stop_requested", "max_cycles"]
    missing = [name for name in required if name not in text]
    if missing:
        findings.append(CodeRepairFinding(
            "high", "autonomous_safety", "winlocalassistant/core.py", 1,
            "Autonomous guard markers missing",
            "Missing guard markers: " + ", ".join(missing),
            "Restore bounded tool calls, health gates, stop requests and cycle limits before releasing.",
        ))
    else:
        passed.append("Autonomous loop includes bounded tool calls, health gates, stop requests and cycle limits.")
    if "code_repair_audit" in text:
        passed.append("Autonomous/project repair workflow exposes code repair audit command/tool.")
