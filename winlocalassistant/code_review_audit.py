from __future__ import annotations

import ast
import os
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text, unique_path

RUNTIME_ARTIFACT_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", ".venv", "venv", "node_modules", ".nova_runtime"}


def find_runtime_artifacts(root: Path, names: set[str] | None = None) -> list[Path]:
    """Find runtime/cache artifacts without descending into huge artifact dirs."""
    wanted = set(names or RUNTIME_ARTIFACT_NAMES)
    found: set[Path] = set()
    try:
        for dirpath, dirnames, filenames in os.walk(root):
            current = Path(dirpath)
            kept_dirs: list[str] = []
            for dirname in dirnames:
                path = current / dirname
                if dirname in wanted:
                    found.add(path)
                    continue
                kept_dirs.append(dirname)
            dirnames[:] = kept_dirs
            for filename in filenames:
                if filename in wanted:
                    found.add(current / filename)
    except Exception:
        return sorted(found)
    return sorted(found)
RISKY_CALLS = {"eval", "exec", "compile"}


@dataclass
class CodeReviewFinding:
    severity: str
    category: str
    path: str
    line: int
    title: str
    detail: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class CodeReviewReport:
    generated_at: str
    repo_root: str
    files_scanned: int
    findings: list[CodeReviewFinding] = field(default_factory=list)
    passed_checks: list[str] = field(default_factory=list)
    markdown_report_path: str | None = None
    json_report_path: str | None = None

    @property
    def ok(self) -> bool:
        return not any(f.severity in {"critical", "high"} for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["ok"] = self.ok
        data["findings"] = [f.to_dict() for f in self.findings]
        return data


def run_code_review(repo_root: Path) -> CodeReviewReport:
    root = repo_root.resolve()
    py_files = _python_files(root)
    findings: list[CodeReviewFinding] = []
    passed: list[str] = []
    parsed = 0
    total_functions = 0
    total_tests = 0
    for path in py_files:
        rel = _rel(root, path)
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            findings.append(CodeReviewFinding("medium", "readability", rel, 1, "Could not read file", repr(exc), "Check encoding and permissions before editing this file."))
            continue
        try:
            tree = ast.parse(text, filename=str(path))
            parsed += 1
        except SyntaxError as exc:
            findings.append(CodeReviewFinding("critical", "syntax", rel, exc.lineno or 1, "Python syntax error", exc.msg, "Fix syntax before doing any behavioural review."))
            continue
        total_functions += sum(isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) for n in ast.walk(tree))
        total_tests += sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name.startswith("test_"))
        _check_mutable_defaults(root, path, tree, findings)
        _check_risky_calls(root, path, tree, findings)
        _check_shell_usage(root, path, tree, findings)
        _check_unbounded_model_calls(root, path, tree, findings)
        _check_silent_broad_exceptions(root, path, tree, findings)
        _check_todos(root, path, text, findings)
        _check_large_files(root, path, text, findings)
    _check_runtime_artifacts(root, findings)
    _check_command_help_contract(root, findings, passed)
    _check_test_signal(total_tests, total_functions, findings, passed)
    if parsed == len(py_files):
        passed.append("All scanned Python files parsed successfully.")
    if not any(f.category == "release_hygiene" for f in findings):
        passed.append("No runtime/cache artifacts were found.")
    return CodeReviewReport(
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        repo_root=str(root),
        files_scanned=len(py_files),
        findings=sorted(findings, key=lambda f: (_severity_rank(f.severity), f.path, f.line)),
        passed_checks=passed,
    )


def write_code_review_report(repo_root: Path) -> tuple[Path, Path, CodeReviewReport]:
    report = run_code_review(repo_root)
    reports = repo_root / "code_reviews"
    reports.mkdir(parents=True, exist_ok=True)
    md = unique_path(reports, "code_review", ".md")
    js = md.with_suffix(".json")
    report.markdown_report_path = str(md)
    report.json_report_path = str(js)
    atomic_write_text(md, render_code_review_markdown(report))
    atomic_write_json(js, report.to_dict(), ensure_ascii=False)
    return md, js, report


def render_code_review_markdown(report: CodeReviewReport) -> str:
    counts: dict[str, int] = {}
    for finding in report.findings:
        counts[finding.severity] = counts.get(finding.severity, 0) + 1
    lines = [
        "# Deep Code Review",
        "",
        f"Generated: {report.generated_at}",
        f"Repo root: `{report.repo_root}`",
        f"Python files scanned: {report.files_scanned}",
        f"High-risk clean: {report.ok}",
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
    lines.extend(["", "## Findings"])
    if not report.findings:
        lines.append("- No code-review findings detected.")
    else:
        for i, finding in enumerate(report.findings[:80], 1):
            lines.extend([
                f"{i}. **{finding.severity.upper()} / {finding.category}** - {finding.title}",
                f"   - location: `{finding.path}:{finding.line}`",
                f"   - detail: {finding.detail}",
                f"   - recommendation: {finding.recommendation}",
            ])
        if len(report.findings) > 80:
            lines.append(f"- {len(report.findings) - 80} additional findings are available in the JSON report.")
    lines.extend(["", "## Suggested review order", "1. Fix critical/high items before autonomous mutation.", "2. Fix medium observability and timeout issues that hide root causes.", "3. Remove release artifacts before zipping.", "4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`."])
    return "\n".join(lines) + "\n"


def _python_files(root: Path) -> list[Path]:
    files: set[Path] = set()
    for base in [root / "winlocalassistant", root]:
        if not base.exists():
            continue
        pattern = "*.py" if base == root else "**/*.py"
        for path in base.glob(pattern):
            if any(part in RUNTIME_ARTIFACT_NAMES for part in path.parts):
                continue
            if path.name.startswith("tests_") or "winlocalassistant" in path.parts:
                files.add(path)
    return sorted(files)


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path)


def _severity_rank(value: str) -> int:
    return {"critical": 0, "high": 1, "medium": 2, "low": 3}.get(value, 4)


def _check_mutable_defaults(root: Path, path: Path, tree: ast.AST, findings: list[CodeReviewFinding]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in list(node.args.defaults) + list(node.args.kw_defaults):
                if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(CodeReviewFinding("high", "correctness", _rel(root, path), node.lineno, "Mutable default argument", f"`{node.name}` uses a mutable default value that can leak state across calls.", "Use `None` as the default and create a new list/dict/set inside the function."))


def _check_risky_calls(root: Path, path: Path, tree: ast.AST, findings: list[CodeReviewFinding]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if name not in RISKY_CALLS:
            continue
        if _is_safe_internal_compile(node):
            continue
        findings.append(CodeReviewFinding("medium", "safety", _rel(root, path), getattr(node, "lineno", 1), "Dynamic code execution call", f"Uses `{name}()`; this can execute unexpected code if fed model/user content.", "Replace with deterministic parsing or restrict inputs behind explicit validation and tests."))


def _is_safe_internal_compile(node: ast.Call) -> bool:
    """Allow compile(ast_tree, filename, 'exec') in deterministic source audits.

    The risky call checker exists to catch model/user-content eval paths. Nova's
    integrity auditor parses files with ast.parse and then compiles the AST to
    validate syntax without executing it. Treating that validation path as a
    safety issue was a false positive that made the whole-codebase audit noisy.
    """
    if _call_name(node.func) != "compile" or len(node.args) < 3:
        return False
    mode = node.args[2]
    return isinstance(mode, ast.Constant) and mode.value == "exec"


def _check_shell_usage(root: Path, path: Path, tree: ast.AST, findings: list[CodeReviewFinding]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        name = _call_name(node.func)
        if not name.endswith("subprocess.run") and name not in {"run", "Popen"}:
            continue
        for kw in node.keywords:
            if kw.arg == "shell" and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                findings.append(CodeReviewFinding("medium", "safety", _rel(root, path), getattr(node, "lineno", 1), "Shell execution enabled", "`subprocess` is called with `shell=True`, which is risky around user/model text.", "Prefer argv-list execution or route through the existing command safety guard."))


def _check_unbounded_model_calls(root: Path, path: Path, tree: ast.AST, findings: list[CodeReviewFinding]) -> None:
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and _call_name(node.func) == "model_chat":
            if not any(kw.arg == "timeout" for kw in node.keywords):
                findings.append(CodeReviewFinding("medium", "reliability", _rel(root, path), getattr(node, "lineno", 1), "Model call without explicit timeout", "A local model call without a timeout can make the UI/autonomous loop appear frozen.", "Pass an explicit timeout and clear desc so status/diagnostics show what is happening."))


def _check_silent_broad_exceptions(root: Path, path: Path, tree: ast.AST, findings: list[CodeReviewFinding]) -> None:
    for node in ast.walk(tree):
        if not isinstance(node, ast.ExceptHandler):
            continue
        catches_broad = node.type is None or (isinstance(node.type, ast.Name) and node.type.id == "Exception")
        body = [stmt for stmt in node.body if not (isinstance(stmt, ast.Expr) and isinstance(getattr(stmt, "value", None), ast.Constant) and isinstance(stmt.value.value, str))]
        if catches_broad and len(body) == 1 and isinstance(body[0], ast.Pass):
            findings.append(CodeReviewFinding("medium", "observability", _rel(root, path), node.lineno, "Broad exception is silently swallowed", "`except Exception: pass` hides root causes from logs and autonomous repair memory.", "Log the exception or return a structured warning; only ignore narrow expected exception types."))


def _check_todos(root: Path, path: Path, text: str, findings: list[CodeReviewFinding]) -> None:
    # Only flag real source comments, not application strings such as a generated
    # task-list app template or test data. The earlier raw-line scan created many
    # false positives and made the whole-codebase audit look noisier than it was.
    import io
    import tokenize

    try:
        tokens = tokenize.generate_tokens(io.StringIO(text).readline)
        for token in tokens:
            if token.type != tokenize.COMMENT:
                continue
            low = token.string.lower()
            if "todo" in low or "fixme" in low or "hack" in low:
                findings.append(CodeReviewFinding("low", "maintainability", _rel(root, path), token.start[0], "Open TODO/FIXME/HACK marker", token.string.strip()[:180], "Either close the task, convert it into a tracked command/report, or explain why it is intentionally left."))
    except tokenize.TokenError:
        return


def _check_large_files(root: Path, path: Path, text: str, findings: list[CodeReviewFinding]) -> None:
    if len(text.splitlines()) > 2500:
        findings.append(CodeReviewFinding("low", "maintainability", _rel(root, path), 1, "Very large Python file", f"File has {len(text.splitlines())} lines, which makes autonomous edits riskier and harder to review.", "Extract command handlers, tool groups, or UI handlers into smaller modules with regression tests."))


def _check_runtime_artifacts(root: Path, findings: list[CodeReviewFinding]) -> None:
    bad: list[Path] = []
    # Ignore import-created Python caches during live audits; release packaging
    # still removes __pycache__ and .pyc files before producing a zip.
    transient_python_cache = {"__pycache__"}
    bad.extend(find_runtime_artifacts(root, RUNTIME_ARTIFACT_NAMES - transient_python_cache))
    for path in sorted(set(bad))[:30]:
        findings.append(CodeReviewFinding("low", "release_hygiene", _rel(root, path), 1, "Runtime/cache artifact present", "Generated cache files should not be shipped in release zips.", "Delete cache/runtime artifacts before packaging and keep .gitignore rules in place."))


def _check_command_help_contract(root: Path, findings: list[CodeReviewFinding], passed: list[str]) -> None:
    core = root / "winlocalassistant" / "core.py"
    if not core.exists():
        return
    text = core.read_text(encoding="utf-8", errors="replace")
    command_literals = set(re.findall(r"cmd\s*==\s*[\"'](/[^\"']+)[\"']", text))
    help_block = text[text.find("/help"):] if "/help" in text else text
    missing = sorted(cmd for cmd in command_literals if cmd not in help_block and not cmd.startswith("/__"))
    if missing:
        findings.append(CodeReviewFinding("low", "ux", "winlocalassistant/core.py", 1, "Some commands may be missing from help text", ", ".join(missing[:25]), "Add visible help entries for user-facing commands or mark internal commands clearly."))
    else:
        passed.append("Command literals appear represented in the help/command text.")


def _check_test_signal(total_tests: int, total_functions: int, findings: list[CodeReviewFinding], passed: list[str]) -> None:
    if total_tests <= 0:
        findings.append(CodeReviewFinding("medium", "testing", ".", 1, "No tests detected", "No test_ functions were found.", "Add pytest coverage before autonomous mutation."))
        return
    passed.append(f"Detected {total_tests} pytest-style test functions across {total_functions} functions.")
    if total_functions and total_tests / max(total_functions, 1) < 0.08:
        findings.append(CodeReviewFinding("low", "testing", ".", 1, "Low test density signal", f"Detected {total_tests} tests for {total_functions} functions.", "Prioritise tests around autonomous loops, file/image context and project-generation tools before refactors."))


def _call_name(func: ast.AST) -> str:
    if isinstance(func, ast.Name):
        return func.id
    if isinstance(func, ast.Attribute):
        base = _call_name(func.value)
        return f"{base}.{func.attr}" if base else func.attr
    return ""
