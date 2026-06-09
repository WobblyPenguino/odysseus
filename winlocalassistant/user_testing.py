from __future__ import annotations

import ast
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .candidate_tournament import build_candidate_tournament
from .feature_audit import run_feature_audit
from .gui_redesign import build_gui_feature_map, gui_regression_check
from .mcp_security import inspect_mcp_security
from .prompt_test_compiler import build_prompt_contract
from .release_hygiene import build_release_hygiene_report
from .trace_cockpit import build_trace
from .weakspot_audit import build_weakspot_audit


@dataclass
class UserTestCheck:
    name: str
    ok: bool
    summary: str
    severity: str = "info"
    detail: dict[str, Any] | None = None


def _py_files(root: Path) -> list[Path]:
    ignored = {"__pycache__", ".pytest_cache", ".git", ".nova_runtime"}
    out: list[Path] = []
    for p in root.rglob("*.py"):
        if any(part in ignored for part in p.parts):
            continue
        out.append(p)
    return sorted(out)


def _syntax_check(root: Path) -> UserTestCheck:
    bad: list[dict[str, Any]] = []
    for p in _py_files(root):
        try:
            ast.parse(p.read_text(encoding="utf-8", errors="replace"), filename=str(p))
        except SyntaxError as exc:
            bad.append({"path": p.relative_to(root).as_posix(), "line": exc.lineno, "message": exc.msg})
    return UserTestCheck("python_syntax", not bad, "Python source parses" if not bad else f"{len(bad)} syntax error(s)", "critical" if bad else "info", {"problems": bad[:20]})


def _route_visibility(root: Path) -> UserTestCheck:
    core = root / "winlocalassistant" / "core.py"
    text = core.read_text(encoding="utf-8", errors="replace") if core.exists() else ""
    required = [
        "/nova-mega-test", "/prompt-contract", "/candidate-tournament", "/repair-diagnose",
        "/trace-status", "/mcp-risk-report", "/mission-create", "/model-output-coach",
        "/env-doctor", "/project-state", "/regression-list", "/weakspot-audit",
    ]
    missing = [cmd for cmd in required if cmd not in text]
    return UserTestCheck("command_routes", not missing, "Major QA/build/autonomy commands are routed" if not missing else f"Missing routes: {', '.join(missing)}", "high" if missing else "info", {"missing": missing})


def _user_flow_contracts() -> list[UserTestCheck]:
    goals = [
        "make a tiny useful local notes app with localStorage and JSON export",
        "repair this project without rewriting unrelated files",
        "improve Nova validation and surgical repair without regressing existing tools",
    ]
    checks: list[UserTestCheck] = []
    for goal in goals:
        contract = build_prompt_contract(goal)
        has_contract = bool(contract.get("must_have") or contract.get("static_checks") or contract.get("must_not_have"))
        checks.append(UserTestCheck(
            f"prompt_contract:{goal[:34]}",
            has_contract,
            "Prompt contract generated with prompt-specific checks" if has_contract else "Prompt contract was empty",
            "high" if not has_contract else "info",
            {"goal": goal, "must_have": contract.get("must_have", []), "must_not_have": contract.get("must_not_have", []), "static_checks": contract.get("static_checks", [])},
        ))
    return checks


def build_user_testing_report(root: Path) -> dict[str, Any]:
    root = root.resolve()
    checks: list[UserTestCheck] = []
    checks.append(_syntax_check(root))
    checks.append(_route_visibility(root))

    hygiene = build_release_hygiene_report(root)
    hygiene_blockers = [f for f in hygiene.get("findings", []) if f.get("severity") == "warning"]
    checks.append(UserTestCheck("release_hygiene", not hygiene_blockers, str(hygiene.get("summary", "Release hygiene checked")), "warning" if hygiene_blockers else "info", {"warning_count": len(hygiene_blockers)}))

    weakspot = build_weakspot_audit(root)
    weakspot_issue_count = weakspot.get("issue_count", 0)
    weakspot_summary = str(weakspot.get("summary") or f"Weakspot audit found {weakspot_issue_count} issue(s)")
    checks.append(UserTestCheck("weakspot_audit", bool(weakspot.get("ok", True)), weakspot_summary, "high" if not weakspot.get("ok", True) else "info", {"blockers": weakspot.get("blockers", 0), "issues": (weakspot.get("issues") or [])[:10]}))

    feature = run_feature_audit(root)
    feature_ok = bool(feature.get("ok", True)) if isinstance(feature, dict) else bool(getattr(feature, "ok", True))
    feature_summary = str(feature.get("summary", "Feature audit completed")) if isinstance(feature, dict) else str(getattr(feature, "summary", "Feature audit completed"))
    if isinstance(feature, dict):
        implemented_value = feature.get("implemented", 0)
        missing_value = feature.get("missing", 0)
        implemented_count = implemented_value if isinstance(implemented_value, int) else len(implemented_value or [])
        missing_count = missing_value if isinstance(missing_value, int) else len(missing_value or [])
    else:
        implemented_count = int(getattr(feature, "implemented_count", 0))
        missing_count = int(getattr(feature, "missing_count", 0))
    checks.append(UserTestCheck("feature_audit", feature_ok, feature_summary, "high" if not feature_ok else "info", {"implemented": implemented_count, "missing": missing_count}))

    fmap = build_gui_feature_map(root)
    missing_gui = [item for item in fmap.get("features", []) if not item.get("ok", item.get("present", False))]
    checks.append(UserTestCheck("gui_feature_map", not missing_gui, "GUI feature map has no missing required features" if not missing_gui else f"{len(missing_gui)} GUI feature(s) missing", "high" if missing_gui else "info", {"missing": missing_gui[:10]}))

    gui_reg = gui_regression_check(root)
    checks.append(UserTestCheck("gui_regression", bool(gui_reg.get("ok", True)), str(gui_reg.get("summary", "GUI regression check completed")), "high" if not gui_reg.get("ok", True) else "info", gui_reg))

    tournament = build_candidate_tournament("make a tiny useful local notes app with localStorage and JSON export")
    checks.append(UserTestCheck("candidate_tournament", bool(tournament.get("ok", True)), str(tournament.get("summary", "Candidate tournament generated")), "high" if not tournament.get("ok", True) else "info", {"winner": tournament.get("winner", {})}))

    trace = build_trace(limit=80)
    checks.append(UserTestCheck("trace_cockpit", bool(trace.get("events") is not None), f"Trace cockpit loaded {len(trace.get('events', []))} event(s)", "info", {"event_count": len(trace.get("events", []))}))

    mcp = inspect_mcp_security(root=root)
    checks.append(UserTestCheck("mcp_security", bool(mcp.get("ok", True)), str(mcp.get("summary", "MCP security inspected")), "high" if not mcp.get("ok", True) else "info", mcp))

    checks.extend(_user_flow_contracts())

    data = [asdict(c) for c in checks]
    critical_or_high = [c for c in data if not c["ok"] and c["severity"] in {"critical", "high"}]
    warnings = [c for c in data if not c["ok"] and c["severity"] == "warning"]
    return {
        "ok": not critical_or_high,
        "summary": "Comprehensive user testing passed" if not critical_or_high else f"Comprehensive user testing found {len(critical_or_high)} blocking issue(s)",
        "root": str(root),
        "checks": data,
        "passed": sum(1 for c in data if c["ok"]),
        "total": len(data),
        "blocking_count": len(critical_or_high),
        "warning_count": len(warnings),
    }


def render_user_testing_report(report: dict[str, Any]) -> str:
    lines = ["# Nova Comprehensive User Testing", "", f"Overall: **{'PASS' if report.get('ok') else 'ISSUES'}**", f"Summary: {report.get('summary','')}", f"Root: `{report.get('root','')}`", "", f"Checks: {report.get('passed',0)}/{report.get('total',0)} passed", "", "## Checks"]
    for check in report.get("checks", []):
        icon = "✅" if check.get("ok") else "❌" if check.get("severity") in {"critical", "high"} else "⚠️"
        lines.append(f"- {icon} **{check.get('name')}** — {check.get('summary')}")
    lines += ["", "## Recommended follow-up", "- If any high/critical item fails, run `/weakspot-audit`, `/nova-mega-test --confirm`, and the named command area before packaging.", "- For user-flow issues, run `/prompt-contract GOAL`, `/candidate-tournament GOAL`, then `/repair-diagnose`.", "- For GUI issues, run `/gui-feature-map` and `/gui-regression-test` before switching GUI modes."]
    return "\n".join(lines)


def write_user_testing_report(root: Path) -> tuple[Path, Path, dict[str, Any]]:
    report = build_user_testing_report(root)
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    md = docs / "NOVA_COMPREHENSIVE_USER_TEST_LATEST.md"
    js = docs / "NOVA_COMPREHENSIVE_USER_TEST_LATEST.json"
    md.write_text(render_user_testing_report(report), encoding="utf-8")
    js.write_text(json.dumps(report, indent=2), encoding="utf-8")
    return md, js, report
