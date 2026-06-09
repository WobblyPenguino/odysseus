from __future__ import annotations

import ast
import json
import time
from pathlib import Path
from typing import Any

RUNTIME_DIR_NAMES = {"__pycache__", ".pytest_cache", ".nova_runtime"}
RUNTIME_SUFFIXES = {".pyc", ".pyo"}


def _rel(root: Path, path: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except Exception:
        return str(path)


def _issue(severity: str, category: str, path: str, detail: str, recommendation: str) -> dict[str, Any]:
    return {
        "severity": severity,
        "category": category,
        "path": path,
        "detail": detail,
        "recommendation": recommendation,
    }


def _silent_exception_passes(root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for path in sorted(root.rglob("*.py")):
        if any(part in RUNTIME_DIR_NAMES for part in path.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        except SyntaxError as exc:
            issues.append(_issue("high", "syntax", _rel(root, path), f"Syntax error during weakspot scan: {exc}", "Fix syntax before autonomous mutation or release."))
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append(_issue("medium", "observability", f"{_rel(root, path)}:{node.lineno}", "Silent `except: pass` hides root causes from idle/autonomous repair memory.", "Log the exception at debug level or return a structured warning."))
    return issues


def _runtime_artifacts(root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    for path in root.rglob("*"):
        rel = _rel(root, path)
        if path.name in RUNTIME_DIR_NAMES:
            issues.append(_issue("warning", "release_hygiene", rel, "Runtime/cache directory present in working tree.", "Run /release-hygiene clean before packaging."))
        elif path.suffix.lower() in RUNTIME_SUFFIXES:
            issues.append(_issue("warning", "release_hygiene", rel, "Compiled Python artifact present in working tree.", "Run /release-hygiene clean before packaging."))
    return issues


def _autonomy_command_coverage(root: Path) -> list[dict[str, Any]]:
    issues: list[dict[str, Any]] = []
    core = root / "winlocalassistant" / "core.py"
    tools = root / "winlocalassistant" / "tools.py"
    if not core.exists() or not tools.exists():
        return [_issue("high", "targeting", str(root), "Nova source files were not found at the audit target.", "Open the Nova source root before running autonomous code review.")]
    core_text = core.read_text(encoding="utf-8", errors="replace")
    tools_text = tools.read_text(encoding="utf-8", errors="replace")
    tool_names = [
        "prompt_contract", "candidate_tournament", "repair_plan_v2", "trace_status", "mcp_risk_report",
        "mission_create", "mission_step", "model_output_coach", "env_profile", "benchmark_system",
        "project_state", "regression_list", "regression_add",
    ]
    for name in tool_names:
        if f'"{name}"' not in tools_text and f"'{name}'" not in tools_text:
            issues.append(_issue("high", "autonomy_tools", f"winlocalassistant/tools.py", f"ToolRegistry wrapper `{name}` is not visibly registered.", "Register command-layer capabilities as internal tools so idle/autonomous can call them."))
    required_commands = [
        "/prompt-contract", "/candidate-tournament", "/repair-plan", "/trace-status", "/mcp-risk-report",
        "/mission-create", "/model-output-coach", "/env-profile", "/benchmark-system", "/project-state", "/regression-list",
    ]
    for cmd in required_commands:
        if cmd not in core_text:
            issues.append(_issue("medium", "command_routing", "winlocalassistant/core.py", f"Command `{cmd}` is not visibly routed.", "Add or restore command routing and regression tests."))
    return issues


def build_weakspot_audit(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).resolve()
    issues: list[dict[str, Any]] = []
    issues.extend(_silent_exception_passes(root))
    issues.extend(_autonomy_command_coverage(root))
    issues.extend(_runtime_artifacts(root)[:80])
    severity_order = {"critical": 4, "high": 3, "medium": 2, "warning": 1, "low": 0}
    blockers = [i for i in issues if severity_order.get(i.get("severity", "low"), 0) >= 3]
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "ok": not blockers,
        "blockers": len(blockers),
        "issue_count": len(issues),
        "issues": sorted(issues, key=lambda i: (-severity_order.get(i.get("severity", "low"), 0), i.get("path", ""))),
        "next_actions": [
            "Run /release-hygiene clean after tests before packaging.",
            "Fix high issues before autonomous mutation.",
            "Use /nova-mega-test --confirm after patching.",
        ],
    }


def render_weakspot_audit(report: dict[str, Any]) -> str:
    lines = [
        "# Nova Weakspot and Error-Hunt Audit",
        "",
        f"Generated: {report.get('generated_at', '')}",
        f"Root: `{report.get('root', '')}`",
        f"Overall: **{'PASS' if report.get('ok') else 'ATTENTION'}**",
        f"Issues: **{report.get('issue_count', 0)}**; blockers: **{report.get('blockers', 0)}**",
        "",
        "## Findings",
    ]
    issues = report.get("issues") or []
    if not issues:
        lines.append("- No weakspots found by this audit.")
    for item in issues[:60]:
        lines.append(f"- **{item.get('severity','')} / {item.get('category','')}** `{item.get('path','')}` — {item.get('detail','')}")
        lines.append(f"  - Fix: {item.get('recommendation','')}")
    if len(issues) > 60:
        lines.append(f"- ... {len(issues) - 60} additional hygiene/runtime findings hidden from chat output.")
    lines += ["", "## Recommended next actions"]
    lines += [f"- {x}" for x in report.get("next_actions", [])]
    return "\n".join(lines)


def write_weakspot_report(root: str | Path = ".") -> tuple[Path, Path, dict[str, Any]]:
    root = Path(root)
    report = build_weakspot_audit(root)
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    md = docs / "NOVA_WEAKSPOT_AUDIT_LATEST.md"
    js = docs / "NOVA_WEAKSPOT_AUDIT_LATEST.json"
    md.write_text(render_weakspot_audit(report), encoding="utf-8")
    js.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return md, js, report
