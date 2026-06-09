from __future__ import annotations

import json
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text, unique_path

CORE_MODULES = [
    "core.py",
    "tools.py",
    "webui.py",
    "action_watcher.py",
    "autonomous_failure.py",
    "autonomous_sequence.py",
    "autonomous_journal.py",
    "command_verifier.py",
    "planning_dashboard.py",
    "project_acceptance.py",
    "project_runtime_probe.py",
    "project_iteration.py",
    "quality_dashboard.py",
    "self_awareness.py",
    "docker_manager.py",
    "sandbox_permissions.py",
    "cohesion_engine.py",
]

DOCS_REQUIRED = [
    "CHANGELOG.md",
    "README.md",
    "AGENTS.md",
    "docs/NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md",
    "docs/NOVA_TOOL_CATALOG.md",
]

RUNTIME_ARTIFACT_MARKERS = ["__pycache__", ".pytest_cache", ".nova_runtime"]

@dataclass
class ArchitectureFinding:
    severity: str
    category: str
    title: str
    detail: str
    recommendation: str

@dataclass
class ArchitectureAuditReport:
    version: str
    version_label: str
    repo_root: str
    generated_at: str
    checks: list[dict[str, Any]] = field(default_factory=list)
    findings: list[ArchitectureFinding] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    markdown_report_path: str | None = None
    json_report_path: str | None = None


def _read_text(path: Path, limit: int = 750_000) -> str:
    try:
        if not path.exists() or not path.is_file():
            return ""
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _rendered_webui_text_for_root(repo_root: Path, fallback: str) -> str:
    try:
        package_root = Path(__file__).resolve().parents[1]
        if repo_root.resolve() == package_root.resolve():
            from .webui import HTML

            return str(HTML)
    except Exception:
        return fallback
    return fallback


def _py_files(repo_root: Path) -> list[Path]:
    return sorted(p for p in repo_root.rglob("*.py") if "__pycache__" not in p.parts)


def _test_files(repo_root: Path) -> list[Path]:
    return sorted(repo_root.glob("tests_*.py"))


def _contains_command_route(core_text: str, command: str) -> bool:
    return command in core_text


def _check_version_consistency(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    # The full VERSION_LABEL is intentionally long because it preserves many
    # historic capability markers for regression tests. Requiring that entire
    # sentence in README/CHANGELOG/Web UI caused false release warnings whenever
    # the current version and user-visible release theme were actually synced.
    label_head = VERSION_LABEL.split("|", 1)[0].replace(f"v{__version__}", "").strip()
    needles = [__version__, f"v{__version__.rsplit('.', 1)[0]}"]
    if label_head:
        needles.append(label_head)
    readme = _read_text(repo_root / "README.md")
    changelog = _read_text(repo_root / "CHANGELOG.md")
    webui_source = _read_text(repo_root / "winlocalassistant" / "webui.py")
    webui = _rendered_webui_text_for_root(repo_root, webui_source)
    combined = readme + changelog + webui
    missing = [str(n) for n in needles if n and str(n) not in combined]
    ok = not missing
    if not ok:
        findings.append(ArchitectureFinding(
            "medium", "versioning", "Version text may be inconsistent",
            "README, CHANGELOG or Web UI may not mention the current package version/release theme.",
            "Update version metadata, visible GUI text, README and CHANGELOG together in every release.",
        ))
    return {"name": "version_consistency", "ok": ok, "version": __version__, "label": VERSION_LABEL, "missing": missing}


def _check_required_modules(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    missing = [m for m in CORE_MODULES if not (repo_root / "winlocalassistant" / m).exists()]
    if missing:
        findings.append(ArchitectureFinding(
            "high", "continuity", "Expected roadmap modules are missing",
            "Missing modules: " + ", ".join(missing),
            "Restore missing modules or update continuity tests if the capability was intentionally replaced.",
        ))
    return {"name": "required_modules", "ok": not missing, "missing": missing, "count": len(CORE_MODULES)}


def _check_required_docs(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    missing = [d for d in DOCS_REQUIRED if not (repo_root / d).exists()]
    if missing:
        findings.append(ArchitectureFinding(
            "medium", "documentation", "Required operating docs are missing",
            "Missing docs: " + ", ".join(missing),
            "Keep architecture, tool catalogue and autonomous operating guides versioned with the build.",
        ))
    return {"name": "required_docs", "ok": not missing, "missing": missing}


def _check_command_routing(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    core = _read_text(repo_root / "winlocalassistant" / "core.py")
    expected = [
        "/command-verify", "/quality-dashboard", "/self-awareness", "/planning-dashboard",
        "/autonomous-plan", "/autonomous-explain", "/autonomous-journal", "/tool-catalog",
        "/interaction-lessons", "/action-watch", "/idle", "/autonomous", "/interactive",
        "/docker-status", "/docker-validate", "/docker-validate-patch", "/cohesion-report",
        "/validation-ladder", "/iteration-plan",
    ]
    missing = [c for c in expected if not _contains_command_route(core, c)]
    if missing:
        findings.append(ArchitectureFinding(
            "high", "commands", "Important commands are not routed",
            "Missing command markers in core.py: " + ", ".join(missing),
            "Add explicit routing and command-verifier contracts for any missing user-facing commands.",
        ))
    return {"name": "command_routes", "ok": not missing, "missing": missing, "checked": expected}


def _check_test_to_module_ratio(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    modules = _py_files(repo_root / "winlocalassistant")
    tests = _test_files(repo_root)
    ratio = round(len(tests) / max(1, len(modules)), 2)
    ok = ratio >= 0.75 and len(tests) >= 20
    if not ok:
        findings.append(ArchitectureFinding(
            "medium", "tests", "Test/module ratio is low",
            f"Found {len(tests)} tests_*.py files for {len(modules)} package modules.",
            "Add focused contract tests for every new command, report writer, verifier and autonomous helper.",
        ))
    return {"name": "test_to_module_ratio", "ok": ok, "module_count": len(modules), "test_file_count": len(tests), "ratio": ratio}


def _check_large_modules(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    large = []
    for p in _py_files(repo_root / "winlocalassistant"):
        try:
            lines = len(p.read_text(encoding="utf-8", errors="replace").splitlines())
        except Exception:
            lines = 0
        if lines > 2500:
            large.append({"path": str(p.relative_to(repo_root)), "lines": lines})
    if large:
        findings.append(ArchitectureFinding(
            "low", "maintainability", "Large modules remain architectural risk",
            "Large files: " + ", ".join(f"{x['path']} ({x['lines']} lines)" for x in large[:5]),
            "Continue extracting isolated helpers from large modules, but only with regression tests.",
        ))
    return {"name": "large_modules", "ok": not large, "large": large}


def _check_runtime_artifacts(repo_root: Path, findings: list[ArchitectureFinding]) -> dict[str, Any]:
    bad = []
    # Importing the audit module can create __pycache__ during normal use, so
    # avoid reporting self-created Python caches as architecture warnings.
    # Packaging scripts still remove __pycache__ and .pyc files before zipping.
    transient_python_cache = {"__pycache__"}
    for marker in set(RUNTIME_ARTIFACT_MARKERS) - transient_python_cache:
        bad.extend(str(p.relative_to(repo_root)) for p in repo_root.rglob(marker))
    if bad:
        findings.append(ArchitectureFinding(
            "low", "release_hygiene", "Runtime/cache artifacts are present in the working tree",
            "Examples: " + ", ".join(bad[:8]),
            "Clean cache/runtime artifacts before packaging releases.",
        ))
    return {"name": "runtime_artifacts", "ok": not bad, "count": len(bad), "examples": bad[:12]}


def run_architecture_audit(repo_root: Path | str = ".") -> ArchitectureAuditReport:
    root = Path(repo_root).resolve()
    findings: list[ArchitectureFinding] = []
    checks = [
        _check_version_consistency(root, findings),
        _check_required_modules(root, findings),
        _check_required_docs(root, findings),
        _check_command_routing(root, findings),
        _check_test_to_module_ratio(root, findings),
        _check_large_modules(root, findings),
        _check_runtime_artifacts(root, findings),
    ]
    recommendations = [
        "Keep command contract verification in CI/smoke tests so user-facing commands fail loudly.",
        "Use architecture-audit before packaging to catch missing modules, stale versions and release artifacts.",
        "Prioritise extracting tested helpers from very large modules over broad rewrites.",
        "Add optional browser automation later for true interactive project acceptance tests.",
    ]
    return ArchitectureAuditReport(
        version=__version__,
        version_label=VERSION_LABEL,
        repo_root=str(root),
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        checks=checks,
        findings=findings,
        recommendations=recommendations,
    )


def render_architecture_audit_markdown(report: ArchitectureAuditReport) -> str:
    lines = [
        "# Nova Architecture Audit",
        "",
        f"Version: **{report.version}** ({report.version_label})",
        f"Repo root: `{report.repo_root}`",
        f"Generated: {report.generated_at}",
        "",
        "## Check Summary",
    ]
    for c in report.checks:
        lines.append(f"- {'PASS' if c.get('ok') else 'WARN'} **{c.get('name','check')}**: `{json.dumps(c, default=str)[:500]}`")
    lines.append("")
    lines.append("## Findings")
    if not report.findings:
        lines.append("No blocking architecture findings were detected.")
    else:
        for f in report.findings:
            lines.extend([
                f"### {f.severity.upper()}: {f.title}",
                f"Category: `{f.category}`",
                "",
                f.detail,
                "",
                f"Recommendation: {f.recommendation}",
                "",
            ])
    lines.append("## Recommendations")
    for r in report.recommendations:
        lines.append(f"- {r}")
    return "\n".join(lines) + "\n"


def write_architecture_audit_report(repo_root: Path | str = ".", profile_dir: Path | None = None) -> tuple[Path, Path, ArchitectureAuditReport]:
    report = run_architecture_audit(repo_root)
    outdir = (profile_dir or APP_DIR) / "architecture_audits"
    outdir.mkdir(parents=True, exist_ok=True)
    md_path = unique_path(outdir, "architecture_audit", ".md")
    json_path = md_path.with_suffix(".json")
    report.markdown_report_path = str(md_path)
    report.json_report_path = str(json_path)
    atomic_write_text(md_path, render_architecture_audit_markdown(report))
    payload = asdict(report)
    atomic_write_json(json_path, payload, ensure_ascii=False)
    return md_path, json_path, report
