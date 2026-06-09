from __future__ import annotations

import ast
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .release_hygiene import build_release_hygiene_report


@dataclass
class BugFinding:
    severity: str
    category: str
    path: str
    line: int
    title: str
    detail: str
    recommendation: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(encoding="utf-8", errors="replace")


def _iter_py_files(root: Path) -> list[Path]:
    ignored = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", "node_modules", ".nova_runtime"}
    out: list[Path] = []
    for p in root.rglob("*.py"):
        if any(part in ignored for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)


def _current_readme_version_surface(text: str, expected: str) -> str:
    """Return only the current README release block, leaving historical notes alone."""
    release_line = re.compile(r"^\s*(?:#+\s*)?(?:Nova\s+)?v?55\.3\.\d+\b", re.IGNORECASE)
    selected: list[str] = []
    saw_current = False
    for line in text.splitlines(keepends=True):
        if saw_current and release_line.search(line) and expected not in line:
            break
        selected.append(line)
        if expected in line or f"v{expected}" in line:
            saw_current = True
    return "".join(selected)


def _line_for_match(text: str, start: int) -> str:
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", start)
    if line_end == -1:
        line_end = len(text)
    return text[line_start:line_end]


def _is_non_user_visible_version_marker(path: Path, text: str, start: int) -> bool:
    line = _line_for_match(text, start).strip()
    lowered = line.lower()
    if path.name == "README.md" and any(marker in lowered for marker in ["legacy continuity", "history", "preserv"]):
        return True
    if line.startswith(("/*", "#", "//")):
        return True
    if path.name == "webui.py" and (
        "data-ui-overhaul" in lowered
        or "data-" in lowered
        or "window.nova" in lowered
        or "patchid" in lowered
        or "storageversion" in lowered
        or "overhaul" in lowered
        or "legacy" in lowered
        or "continuity audit" in lowered
        or "hidden-panel layout reclaim" in lowered
        or ("localstorage" in lowered and "wakedefaultapplied" in lowered)
    ):
        return True
    return False


def _rendered_webui_text_for_root(root: Path, fallback: str) -> str:
    try:
        package_root = Path(__file__).resolve().parents[1]
        if root.resolve() == package_root.resolve():
            from .webui import HTML

            return str(HTML)
    except Exception:
        return fallback
    return fallback


def _detect_syntax(root: Path, findings: list[BugFinding]) -> None:
    for p in _iter_py_files(root):
        try:
            ast.parse(_read_text(p), filename=str(p))
        except SyntaxError as exc:
            findings.append(BugFinding(
                severity="critical",
                category="syntax",
                path=_rel(root, p),
                line=int(exc.lineno or 1),
                title="Python syntax error",
                detail=str(exc),
                recommendation="Fix the syntax error before running autonomous mutation or packaging.",
            ))


def _detect_broad_except_hotspots(root: Path, findings: list[BugFinding]) -> None:
    # These are warnings, not blockers. Some Nova UI/log/report paths intentionally degrade gracefully.
    allowed_markers = (
        "log_activity(",
        "return ToolResult(False",
        "return f\"",
        "quarantine",
        "best-effort",
        "best effort",
        "debug",
        "suppressed_optional_exception",
    )
    for p in _iter_py_files(root):
        text = _read_text(p)
        try:
            tree = ast.parse(text, filename=str(p))
        except SyntaxError:
            continue
        lines = text.splitlines()
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is not None:
                name = getattr(node.type, "id", "") or getattr(getattr(node.type, "attr", ""), "id", "")
                if name != "Exception":
                    continue
                start = max(0, (node.lineno or 1) - 1)
                end = min(len(lines), start + 12)
                block = "\n".join(lines[start:end])
                if any(marker in block for marker in allowed_markers):
                    continue
                findings.append(BugFinding(
                    severity="low",
                    category="diagnostics",
                    path=_rel(root, p),
                    line=int(node.lineno or 1),
                    title="Broad exception handler may hide useful diagnostics",
                    detail="A broad `except Exception` block was found without an obvious structured log, ToolResult error, or return message in the nearby code.",
                    recommendation="Add structured logging or return a specific recoverable warning so failures are visible in Live Activity and reports.",
                ))


def _detect_stale_version_markers(root: Path, findings: list[BugFinding]) -> None:
    expected = __version__
    version_pat = re.compile(r"55\.3\.(\d+)")
    # Only scan current, user-visible version surfaces. Historical changelog entries
    # and old regression test names intentionally contain older version numbers.
    targets = [
        root / "README.md",
        root / "app.py",
        root / "winlocalassistant" / "__init__.py",
        root / "winlocalassistant" / "webui.py",
    ]
    for p in targets:
        if not p.exists() or not p.is_file():
            continue
        text = _read_text(p)
        if p.name == "README.md":
            scan_text = _current_readme_version_surface(text, expected)
        elif p.name == "webui.py":
            scan_text = _rendered_webui_text_for_root(root, text)
        else:
            scan_text = text
        for m in version_pat.finditer(scan_text):
            literal = m.group(0)
            if literal == expected:
                continue
            if _is_non_user_visible_version_marker(p, scan_text, m.start()):
                continue
            findings.append(BugFinding(
                severity="medium",
                category="versioning",
                path=_rel(root, p),
                line=scan_text[:m.start()].count("\n") + 1,
                title="Stale user-visible version marker",
                detail=f"Found `{literal}` while package version is `{expected}` in a current user-visible surface.",
                recommendation="Update visible docs/UI/version labels and matching regression tests in the same patch.",
            ))


def _detect_tool_markdown_formatting_risk(root: Path, findings: list[BugFinding]) -> None:
    core = root / "winlocalassistant" / "core.py"
    tools = root / "winlocalassistant" / "tools.py"
    if not core.exists() or not tools.exists():
        return
    core_text = _read_text(core)
    tools_text = _read_text(tools)
    if 'data.get("markdown")' not in core_text and "data.get('markdown')" not in core_text:
        if '"markdown"' in tools_text:
            findings.append(BugFinding(
                severity="medium",
                category="chat_formatting",
                path="winlocalassistant/core.py",
                line=5161,
                title="Tool markdown can be hidden behind JSON details",
                detail="Several ToolRegistry tools return a `markdown` field, but format_result does not render it directly.",
                recommendation="Render `markdown` like `message`/`human_report` so autonomy-accessible tools are readable in chat and summaries.",
            ))


def _detect_command_integration(root: Path, findings: list[BugFinding]) -> None:
    core = root / "winlocalassistant" / "core.py"
    tools = root / "winlocalassistant" / "tools.py"
    caps = root / "winlocalassistant" / "autonomy_capabilities.py"
    if not core.exists() or not tools.exists() or not caps.exists():
        return
    core_text = _read_text(core)
    tools_text = _read_text(tools)
    caps_text = _read_text(caps)
    expected_commands = [
        "/nova-mega-test", "/regression-sweep", "/whole-codebase-review", "/improvement-roadmap",
        "/prompt-contract", "/candidate-tournament", "/repair-plan", "/trace-status", "/mcp-risk-report",
        "/mission-create", "/model-output-coach", "/env-doctor", "/project-state", "/regression-list",
    ]
    for cmd in expected_commands:
        if cmd not in core_text:
            findings.append(BugFinding("high", "command_routing", "winlocalassistant/core.py", 1, "Command missing from core routing", f"`{cmd}` was not found in core.py.", "Restore the command route or remove it from docs/tests."))
        if cmd not in caps_text and cmd not in {"/nova-mega-test"}:
            findings.append(BugFinding("medium", "autonomy_capabilities", "winlocalassistant/autonomy_capabilities.py", 1, "Command missing from autonomy capability catalog", f"`{cmd}` was not found in the capability catalog.", "Add the command to the relevant capability record so idle/autonomous know when to use it."))
    expected_tools = ["regression_sweep", "whole_codebase_review", "improvement_roadmap", "prompt_contract", "candidate_tournament", "repair_plan_v2", "mcp_risk_report", "mission_create", "model_output_coach", "env_profile", "project_state", "regression_list"]
    for tool in expected_tools:
        if f'"{tool}"' not in tools_text and f"'{tool}'" not in tools_text:
            findings.append(BugFinding("high", "tool_registry", "winlocalassistant/tools.py", 1, "Internal tool missing", f"`{tool}` was not found in ToolRegistry registrations.", "Register the tool so autonomous/idle can call it."))


def build_bug_review(root: str | Path, *, tool_names: list[str] | None = None) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    findings: list[BugFinding] = []
    _detect_syntax(root, findings)
    _detect_stale_version_markers(root, findings)
    _detect_command_integration(root, findings)
    _detect_tool_markdown_formatting_risk(root, findings)
    _detect_broad_except_hotspots(root, findings)
    hygiene = build_release_hygiene_report(root)
    hygiene_findings = hygiene.get("findings") or []
    bad_hygiene = [f for f in hygiene_findings if isinstance(f, dict) and f.get("severity") == "warning"]
    runtime_cache_kinds = {"cache_directory", "compiled_python"}
    non_runtime_hygiene = [f for f in bad_hygiene if f.get("kind") not in runtime_cache_kinds]
    # Importing Nova to run /bug-review creates __pycache__/pyc files. Treat those as a
    # package-cleaning note instead of making the live diagnostic look failed forever.
    if non_runtime_hygiene:
        findings.append(BugFinding(
            severity="medium",
            category="release_hygiene",
            path=".",
            line=1,
            title="Non-cache package artifacts are present",
            detail=f"Release hygiene reports {len(non_runtime_hygiene)} non-cache warning artifact(s).",
            recommendation="Run `/release-hygiene clean` before packaging or sharing a zip.",
        ))
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    findings.sort(key=lambda f: (severity_order.get(f.severity, 9), f.path, f.line, f.title))
    blockers = [f for f in findings if f.severity in {"critical", "high"}]
    counts: dict[str, int] = {"critical": 0, "high": 0, "medium": 0, "low": 0}
    for f in findings:
        counts[f.severity] = counts.get(f.severity, 0) + 1
    return {
        "ok": not blockers,
        "summary": "Bug review passed" if not blockers else f"Bug review found {len(blockers)} blocking issue(s)",
        "root": str(root),
        "version": __version__,
        "version_label": VERSION_LABEL,
        "severity_counts": counts,
        "findings": [f.to_dict() for f in findings],
        "tool_names_seen": sorted(tool_names or []),
        "checks": [
            {"name": "python_syntax", "ok": not any(f.category == "syntax" for f in findings)},
            {"name": "version_markers", "ok": not any(f.category == "versioning" for f in findings)},
            {"name": "command_tool_integration", "ok": not any(f.category in {"command_routing", "tool_registry"} for f in findings)},
            {"name": "chat_markdown_formatting", "ok": not any(f.category == "chat_formatting" for f in findings)},
            {"name": "release_hygiene", "ok": not non_runtime_hygiene, "note": f"{len(bad_hygiene)} runtime cache artifact(s) may exist after imports; clean before packaging" if bad_hygiene else "clean"},
        ],
    }


def render_bug_review(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Bug Review",
        "",
        f"Root: `{payload.get('root','')}`",
        f"Version: {payload.get('version','')}",
        f"Overall: **{'PASS' if payload.get('ok') else 'BLOCKED'}**",
        f"Summary: {payload.get('summary','')}",
        "",
        "## Check summary",
    ]
    for check in payload.get("checks", []):
        icon = "✅" if check.get("ok") else "❌"
        lines.append(f"- {icon} {check.get('name','check')}")
    counts = payload.get("severity_counts", {})
    lines += ["", "## Severity counts"]
    for key in ("critical", "high", "medium", "low"):
        lines.append(f"- {key}: {counts.get(key, 0)}")
    findings = payload.get("findings") or []
    if findings:
        lines += ["", "## Findings"]
        for i, f in enumerate(findings[:40], 1):
            lines += [
                f"{i}. **{str(f.get('severity','')).upper()} / {f.get('category','')}** — {f.get('title','')}",
                f"   - location: `{f.get('path','.')}`:{f.get('line',1)}",
                f"   - detail: {f.get('detail','')}",
                f"   - recommendation: {f.get('recommendation','')}",
            ]
        if len(findings) > 40:
            lines.append(f"- ... {len(findings) - 40} more finding(s) hidden by display cap")
    else:
        lines += ["", "No bug findings detected by this review layer."]
    lines += ["", "## Recommended validation", "- `python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py`", "- `python tests_smoke.py`", "- `/nova-mega-test --confirm`", "- `/bug-review` after major patches"]
    return "\n".join(lines)
