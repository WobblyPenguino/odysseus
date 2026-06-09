from __future__ import annotations

import ast
import json
import re
import time
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .safe_io import atomic_write_json, atomic_write_text

CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
RUNTIME_NAMES = {".nova_runtime"}
REQUIRED_COMMANDS = (
    "/nova-mega-test",
    "/regression-sweep",
    "/weakspot-audit",
    "/improvement-roadmap",
    "/implement-improvements",
    "/prompt-contract",
    "/candidate-tournament",
    "/repair-plan",
    "/trace-status",
    "/mcp-risk-report",
    "/mission-create",
    "/model-output-coach",
    "/env-profile",
    "/project-state",
    "/regression-list",
)
REQUIRED_TOOL_NAMES = (
    "regression_sweep",
    "weakspot_audit",
    "improvement_roadmap",
    "implement_improvements",
    "prompt_contract",
    "candidate_tournament",
    "repair_plan_v2",
    "trace_status",
    "mcp_risk_report",
    "mission_create",
    "model_output_coach",
    "env_profile",
    "project_state",
    "regression_list",
)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _scan_python(root: Path) -> dict[str, Any]:
    python_files = sorted(root.glob("winlocalassistant/*.py")) + sorted(root.glob("tests_*.py")) + ([root / "app.py"] if (root / "app.py").exists() else [])
    parse_errors: list[dict[str, Any]] = []
    broad_exceptions: list[dict[str, Any]] = []
    todo_markers: list[dict[str, Any]] = []
    for path in python_files:
        rel = str(path.relative_to(root)) if path.is_relative_to(root) else str(path)
        text = _read_text(path)
        try:
            ast.parse(text, filename=rel)
        except SyntaxError as exc:
            parse_errors.append({"path": rel, "line": exc.lineno, "error": exc.msg})
        for idx, line in enumerate(text.splitlines(), 1):
            stripped = line.strip()
            if re.match(r"except\s+Exception\s*:\s*$", stripped) or stripped == "except:":
                broad_exceptions.append({"path": rel, "line": idx, "text": stripped})
            if "TODO" in line or "FIXME" in line:
                todo_markers.append({"path": rel, "line": idx, "text": stripped[:160]})
    return {
        "python_file_count": len(python_files),
        "parse_errors": parse_errors,
        "broad_exception_count": len(broad_exceptions),
        "broad_exception_examples": broad_exceptions[:20],
        "todo_count": len(todo_markers),
        "todo_examples": todo_markers[:20],
    }


def _scan_artifacts(root: Path) -> list[dict[str, Any]]:
    findings: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        rel = str(path.relative_to(root))
        if any(part in CACHE_NAMES for part in path.parts) or path.suffix in {".pyc", ".pyo"}:
            findings.append({"path": rel, "kind": "cache_or_bytecode"})
        elif any(part in RUNTIME_NAMES for part in path.parts):
            findings.append({"path": rel, "kind": "runtime_state"})
    return findings[:200]


def _scan_routes(root: Path, tool_names: list[str] | None = None) -> dict[str, Any]:
    core = _read_text(root / "winlocalassistant" / "core.py")
    tools_py = _read_text(root / "winlocalassistant" / "tools.py")
    webui = _read_text(root / "winlocalassistant" / "webui.py")
    route_missing = [cmd for cmd in REQUIRED_COMMANDS if cmd not in core and cmd not in webui and cmd not in tools_py]
    registered_text_missing = [name for name in REQUIRED_TOOL_NAMES if name not in tools_py]
    runtime_missing = []
    if tool_names is not None:
        runtime_missing = [name for name in REQUIRED_TOOL_NAMES if name not in tool_names]
    return {
        "required_commands_checked": list(REQUIRED_COMMANDS),
        "missing_command_markers": route_missing,
        "missing_tool_registry_markers": registered_text_missing,
        "missing_runtime_tools": runtime_missing,
    }


def _scan_docs(root: Path) -> dict[str, Any]:
    readme = _read_text(root / "README.md")
    changelog = _read_text(root / "CHANGELOG.md")
    label_lower = VERSION_LABEL.lower()
    return {
        "readme_mentions_version": f"v{__version__}" in readme or f"Nova v{__version__}" in readme,
        "changelog_mentions_version": f"v{__version__}" in changelog or __version__ in changelog,
        "version_label_mentions_current_version": f"v{__version__}" in VERSION_LABEL,
        "version_label_mentions_current_capabilities": any(term in label_lower for term in ("wake", "voice", "packaging", "codebase", "no-regression")),
    }


def build_whole_codebase_review(root: str | Path, tool_names: list[str] | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    py = _scan_python(root)
    artifacts = _scan_artifacts(root)
    routes = _scan_routes(root, tool_names=tool_names)
    docs = _scan_docs(root)
    blockers: list[str] = []
    warnings: list[str] = []
    if py["parse_errors"]:
        blockers.append(f"{len(py['parse_errors'])} Python syntax/parse error(s) detected")
    if routes["missing_command_markers"]:
        blockers.append("missing command route markers: " + ", ".join(routes["missing_command_markers"]))
    if routes["missing_runtime_tools"]:
        blockers.append("missing runtime ToolRegistry tools: " + ", ".join(routes["missing_runtime_tools"]))
    if artifacts:
        warnings.append(f"{len(artifacts)} cache/runtime artifact(s) detected")
    if py["broad_exception_count"] > 120:
        warnings.append(f"high broad-exception count ({py['broad_exception_count']}); keep converting high-risk paths to structured diagnostics")
    if not all(docs.values()):
        warnings.append("README/CHANGELOG/version-label documentation consistency needs attention")
    improvements = [
        {
            "title": "Keep direct CLI command execution for one-shot QA",
            "status": "implemented_in_v55.3.89",
            "why": "Allows `python app.py /nova-mega-test --confirm` and other copy/paste diagnostics without opening the GUI.",
        },
        {
            "title": "Use whole-codebase review before packaging",
            "status": "implemented_in_v55.3.89",
            "why": "Aggregates syntax, route/tool visibility, docs, cache artifacts and broad exception risk into one report.",
        },
        {
            "title": "Continue reducing broad exception paths",
            "status": "next_safe_follow_up",
            "why": "Many are acceptable optional best-effort paths, but high-risk paths should log context instead of silently recovering.",
        },
    ]
    payload = {
        "ok": not blockers,
        "summary": "Whole-codebase review passed" if not blockers else "Whole-codebase review found blockers",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "version": __version__,
        "version_label": VERSION_LABEL,
        "blockers": blockers,
        "warnings": warnings,
        "python": py,
        "artifacts": artifacts,
        "routes": routes,
        "docs": docs,
        "improvements": improvements,
    }
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(docs_dir / "NOVA_WHOLE_CODEBASE_REVIEW_LATEST.json", payload)
    atomic_write_text(docs_dir / "NOVA_WHOLE_CODEBASE_REVIEW_LATEST.md", render_whole_codebase_review(payload))
    return payload


def render_whole_codebase_review(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Whole Codebase Review",
        "",
        f"Generated: {payload.get('generated_at','')}",
        f"Root: `{payload.get('root','')}`",
        f"Version: {payload.get('version','')}",
        f"Overall: {'PASS' if payload.get('ok') else 'BLOCKED'}",
        "",
    ]
    blockers = payload.get("blockers") or []
    warnings = payload.get("warnings") or []
    if blockers:
        lines += ["## Blockers"] + [f"- {b}" for b in blockers] + [""]
    if warnings:
        lines += ["## Warnings"] + [f"- {w}" for w in warnings] + [""]
    py = payload.get("python") or {}
    lines += [
        "## Code scan",
        f"- Python files scanned: {py.get('python_file_count', 0)}",
        f"- Parse errors: {len(py.get('parse_errors') or [])}",
        f"- Broad exception handlers: {py.get('broad_exception_count', 0)}",
        f"- TODO/FIXME markers: {py.get('todo_count', 0)}",
        "",
    ]
    if py.get("parse_errors"):
        lines += ["### Parse errors"] + [f"- {e.get('path')}:{e.get('line')} — {e.get('error')}" for e in py.get("parse_errors", [])[:20]] + [""]
    routes = payload.get("routes") or {}
    lines += [
        "## Command/tool integration",
        f"- Required command markers checked: {len(routes.get('required_commands_checked') or [])}",
        f"- Missing command markers: {', '.join(routes.get('missing_command_markers') or []) or 'none'}",
        f"- Missing registered tool markers: {', '.join(routes.get('missing_tool_registry_markers') or []) or 'none'}",
        f"- Missing runtime tools: {', '.join(routes.get('missing_runtime_tools') or []) or 'none'}",
        "",
        "## Package hygiene",
        f"- Cache/runtime artifacts detected: {len(payload.get('artifacts') or [])}",
        "",
        "## Documentation/version consistency",
    ]
    for key, value in (payload.get("docs") or {}).items():
        lines.append(f"- {'✅' if value else '❌'} {key}")
    lines += ["", "## Completed / proposed improvements"]
    for item in payload.get("improvements") or []:
        lines.append(f"- **{item.get('title')}** — {item.get('status')}: {item.get('why')}")
    lines += ["", "## Recommended validation ladder", "- python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py", "- python tests_smoke.py", "- /nova-mega-test --confirm", "- /release-hygiene clean before zipping"]
    return "\n".join(lines)
