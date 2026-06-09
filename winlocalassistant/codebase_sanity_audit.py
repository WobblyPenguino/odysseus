from __future__ import annotations

import ast
import re
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable

EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".nova_runtime",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
}

@dataclass(frozen=True)
class SanityFinding:
    severity: str
    category: str
    path: str
    detail: str
    recommendation: str


def _iter_python_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*.py"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path).replace("\\", "/")


def _function_names(tree: ast.AST) -> list[str]:
    return [node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))]


def _class_names(tree: ast.AST) -> list[str]:
    return [node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef)]


def _node_count(tree: ast.AST) -> int:
    return sum(1 for _ in ast.walk(tree))


def _count_tool_registry_entries(text: str) -> int:
    # Conservatively count string keys followed by self.<method> in the ToolRegistry dict.
    return len(re.findall(r'"[A-Za-z0-9_\-]+"\s*:\s*self\.[A-Za-z0-9_]+', text))


def _extract_core_commands(text: str) -> set[str]:
    return set(re.findall(r'"(/[-A-Za-z0-9_]+)', text)) | set(re.findall(r"'(/[-A-Za-z0-9_]+)", text))


def _risk_patterns(text: str, rel: str) -> list[SanityFinding]:
    findings: list[SanityFinding] = []
    lines = text.splitlines()
    raw_write_hits = []
    broad_except_hits = []
    sleep_hits = []
    todo_hits = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        # Avoid flagging this audit file's own string-pattern definitions.
        is_pattern_definition = stripped.startswith(("if ", "elif ")) and any(token in stripped for token in ("write_text", "write_bytes", "time.sleep"))
        if not is_pattern_definition and ("Path.write_text" in stripped or ".write_text(" in stripped or ".write_bytes(" in stripped):
            if "safe_io" not in rel and "atomic_write" not in stripped:
                raw_write_hits.append(i)
        if re.match(r"except\s+Exception\s*:", stripped):
            broad_except_hits.append(i)
        if not is_pattern_definition and "time.sleep(" in stripped and not rel.endswith("startup_validation.py"):
            sleep_hits.append(i)
        if any(marker in stripped.lower() for marker in ("todo", "fixme", "hack")):
            todo_hits.append(i)
    if raw_write_hits:
        findings.append(SanityFinding(
            severity="medium" if len(raw_write_hits) > 5 else "low",
            category="unsafe_write_pattern",
            path=rel,
            detail=f"raw write helpers on lines {raw_write_hits[:12]}",
            recommendation="Prefer safe_io.atomic_write_text/json/bytes or append helpers so failed writes do not corrupt state.",
        ))
    if len(broad_except_hits) > 20:
        findings.append(SanityFinding(
            severity="low",
            category="broad_exception_density",
            path=rel,
            detail=f"{len(broad_except_hits)} broad Exception handlers; first lines {broad_except_hits[:12]}",
            recommendation="Where practical, narrow high-traffic handlers or log explicit diagnostics so errors do not look like success.",
        ))
    if sleep_hits:
        findings.append(SanityFinding(
            severity="low",
            category="blocking_sleep",
            path=rel,
            detail=f"time.sleep calls on lines {sleep_hits[:12]}",
            recommendation="Ensure sleeps are bounded and do not run on GUI/request paths; prefer polling with visible activity events.",
        ))
    if len(todo_hits) > 10:
        findings.append(SanityFinding(
            severity="info",
            category="todo_density",
            path=rel,
            detail=f"{len(todo_hits)} TODO/FIXME/HACK markers; first lines {todo_hits[:12]}",
            recommendation="Review markers during the next staged refactor; do not treat them as release blockers by default.",
        ))
    return findings


def build_codebase_sanity_audit(root: Path | str = ".") -> dict[str, Any]:
    """Audit Nova for redundancy, logic-risk and integration drift.

    This is intentionally read-only. It is a practical audit gate for future timeline
    work: find code that is becoming too large, duplicated, risky or not integrated
    with the repo-inspired tooling surface.
    """
    root = Path(root).resolve()
    package = root / "winlocalassistant"
    scan_root = package if package.exists() else root

    findings: list[SanityFinding] = []
    files: list[dict[str, Any]] = []
    function_index: dict[str, list[str]] = defaultdict(list)
    class_index: dict[str, list[str]] = defaultdict(list)
    parse_errors: list[dict[str, str]] = []

    for path in sorted(_iter_python_files(scan_root)):
        rel = _safe_rel(path, root)
        text = _read(path)
        lines = text.count("\n") + (1 if text else 0)
        size = path.stat().st_size if path.exists() else 0
        try:
            tree = ast.parse(text)
        except SyntaxError as exc:
            parse_errors.append({"path": rel, "error": str(exc)})
            findings.append(SanityFinding("critical", "syntax_error", rel, str(exc), "Fix syntax before any further refactor."))
            continue
        names = _function_names(tree)
        classes = _class_names(tree)
        for name in names:
            function_index[name].append(rel)
        for name in classes:
            class_index[name].append(rel)
        files.append({
            "path": rel,
            "lines": lines,
            "bytes": size,
            "functions": len(names),
            "classes": len(classes),
            "ast_nodes": _node_count(tree),
        })
        if lines > 2500:
            severity = "medium" if lines > 5000 else "low"
            findings.append(SanityFinding(
                severity,
                "large_module",
                rel,
                f"{lines} lines, {len(names)} functions, {len(classes)} classes",
                "Split behind compatibility wrappers by command family; preserve ToolRegistry/Core routes while moving one family per patch.",
            ))
        if len(names) > 120:
            findings.append(SanityFinding(
                "low",
                "large_function_surface",
                rel,
                f"{len(names)} functions/methods in one module",
                "Group by responsibility and add integration tests before moving code.",
            ))
        findings.extend(_risk_patterns(text, rel))

    duplicate_functions = {
        name: sorted(set(paths))
        for name, paths in function_index.items()
        if len(set(paths)) >= 4 and not name.startswith("test_") and name not in {"main", "render", "load", "save"}
    }
    duplicate_classes = {name: sorted(set(paths)) for name, paths in class_index.items() if len(set(paths)) >= 3}
    if duplicate_functions:
        top = sorted(duplicate_functions.items(), key=lambda item: len(item[1]), reverse=True)[:10]
        findings.append(SanityFinding(
            "info",
            "repeated_function_names",
            "winlocalassistant",
            "; ".join(f"{name} in {len(paths)} modules" for name, paths in top),
            "Repeated names are not always bugs, but they make audits harder; consider namespacing new helpers by subsystem.",
        ))
    if duplicate_classes:
        top = sorted(duplicate_classes.items(), key=lambda item: len(item[1]), reverse=True)[:10]
        findings.append(SanityFinding(
            "info",
            "repeated_class_names",
            "winlocalassistant",
            "; ".join(f"{name} in {len(paths)} modules" for name, paths in top),
            "Review repeated classes before large refactors; keep public dataclasses stable.",
        ))

    core_text = _read(package / "core.py")
    tools_text = _read(package / "tools.py")
    webui_text = _read(package / "webui.py")
    route_commands = _extract_core_commands(core_text)
    tool_entries = _count_tool_registry_entries(tools_text)
    repo_upgrade_commands = {
        "/repo-upgrade-assurance", "/tool-awareness-audit", "/pipeline-catalog", "/pipeline-preflight",
        "/session-evidence", "/memory-inventory", "/browser-smoke", "/command-verify",
    }
    missing_repo_commands = sorted(repo_upgrade_commands - route_commands)
    if missing_repo_commands:
        findings.append(SanityFinding(
            "medium",
            "repo_upgrade_route_gap",
            "winlocalassistant/core.py",
            "missing commands: " + ", ".join(missing_repo_commands),
            "Add Core.handle_command routes before claiming repo-inspired features are installed.",
        ))
    gui_required = ["data-orbit-studio-shell", "messageTerminalHtml", "announceNovaReady", "loadActivity"]
    missing_gui = [m for m in gui_required if m not in webui_text]
    if missing_gui:
        findings.append(SanityFinding(
            "medium",
            "gui_observability_marker_gap",
            "winlocalassistant/webui.py",
            "missing markers: " + ", ".join(missing_gui),
            "Restore Orbit GUI observability markers or update tests if the GUI intentionally changed.",
        ))

    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    findings_sorted = sorted(findings, key=lambda f: (severity_order.get(f.severity, 9), f.category, f.path))
    counts = Counter(f.severity for f in findings_sorted)
    largest = sorted(files, key=lambda item: item["lines"], reverse=True)[:12]

    rewrite_candidates = [
        {
            "path": item["path"],
            "reason": "large module" if item["lines"] > 2500 else "broad surface",
            "lines": item["lines"],
            "safe_next_step": "extract read-only helpers first; add compatibility wrapper and targeted tests",
        }
        for item in largest
        if item["lines"] > 1000
    ]

    # Release-readiness intentionally allows known large-module advisories.
    blockers = [f for f in findings_sorted if f.severity in {"critical", "high"}]
    return {
        "ok": not blockers and not parse_errors,
        "root": str(root),
        "files_scanned": len(files),
        "findings_total": len(findings_sorted),
        "severity_counts": dict(counts),
        "parse_errors": parse_errors,
        "largest_modules": largest,
        "tool_registry_entries_estimate": tool_entries,
        "core_command_count_estimate": len(route_commands),
        "duplicate_function_groups": {k: v for k, v in sorted(duplicate_functions.items())[:20]},
        "duplicate_class_groups": {k: v for k, v in sorted(duplicate_classes.items())[:20]},
        "rewrite_candidates": rewrite_candidates,
        "findings": [asdict(f) for f in findings_sorted[:120]],
        "recommendations": [
            "Use /patch-impact-plan before splitting large modules.",
            "Convert future broad audits into typed pipeline routes before mutation.",
            "Prioritise live browser click-through tests for GUI claims.",
            "Keep raw state/database writes on safe_io atomic helpers.",
            "Add route checks whenever a new repo-inspired command/tool is introduced.",
        ],
    }


def render_codebase_sanity_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Codebase Sanity Audit",
        "",
        f"Result: **{'PASS' if payload.get('ok') else 'ATTENTION'}**",
        f"Files scanned: {payload.get('files_scanned', 0)}",
        f"Findings: {payload.get('findings_total', 0)}",
        f"Severity counts: {payload.get('severity_counts') or {}}",
        f"ToolRegistry entries estimate: {payload.get('tool_registry_entries_estimate', 0)}",
        f"Core command estimate: {payload.get('core_command_count_estimate', 0)}",
        "",
        "## Largest modules",
    ]
    for item in payload.get("largest_modules") or []:
        lines.append(f"- `{item['path']}` — {item['lines']} lines, {item['functions']} functions, {item['classes']} classes")
    lines += ["", "## Rewrite candidates"]
    for item in payload.get("rewrite_candidates") or []:
        lines.append(f"- `{item['path']}` — {item['reason']} ({item['lines']} lines). Next: {item['safe_next_step']}")
    findings = payload.get("findings") or []
    if findings:
        lines += ["", "## Findings"]
        for finding in findings[:40]:
            lines.append(f"- **{finding['severity']} / {finding['category']}** `{finding['path']}` — {finding['detail']}")
            lines.append(f"  - Fix direction: {finding['recommendation']}")
    lines += ["", "## Recommendations"]
    lines.extend(f"- {item}" for item in payload.get("recommendations") or [])
    return "\n".join(lines)
