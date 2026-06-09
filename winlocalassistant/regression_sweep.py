from __future__ import annotations

import json
import re
import time
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .release_hygiene import build_release_hygiene_report, find_release_hygiene_findings

CORE_COMMANDS = [
    "/nova-doctor", "/test-all", "/release-gate", "/nova-mega-test", "/feature-audit",
    "/weakspot-audit", "/error-hunt", "/comprehensive-user-test", "/improvement-cycle", "/improvement-roadmap", "/improvement-impact", "/implement-improvements", "/proposal-ledger",
    "/prompt-contract", "/prompt-test-run", "/candidate-tournament", "/repair-plan",
    "/trace-status", "/mcp-risk-report", "/mission-create", "/model-output-coach",
    "/env-doctor", "/benchmark-system", "/project-state", "/regression-list",
    "/sandbox-dev-run", "/docker-validate", "/voice-troubleshoot", "/mic-test",
]

AUTONOMY_TOOL_EXPECTED = [
    "prompt_contract", "prompt_test_run", "candidate_tournament", "candidate_failure_report",
    "repair_plan_v2", "trace_status", "mcp_risk_report", "mission_create", "mission_step",
    "model_output_coach", "env_profile", "benchmark_system", "project_state",
    "regression_list", "regression_add", "weakspot_audit", "error_hunt", "user_test_suite",
    "improvement_proposals_v2", "improvement_cycle", "improvement_status", "improvement_roadmap", "improvement_impact", "implement_improvements", "proposal_ledger",
]

CAPABILITY_KEYWORDS = [
    "prompt_to_test", "candidate_tournament", "surgical_repair_v2", "trace_observability",
    "safe_mcp_connector", "mission_planner", "model_output_coach",
    "environment_profiles", "project_state", "regression_memory", "weakspot_error_hunt",
    "improvement_proposal_cycle", "improvement_roadmap",
]


def build_regression_sweep(root: str | Path, app: Any | None = None, tool_names: list[str] | None = None) -> dict[str, Any]:
    root = Path(root).resolve()
    checks: list[dict[str, Any]] = []
    core_text = _read(root / "winlocalassistant" / "core.py")
    tools_text = _read(root / "winlocalassistant" / "tools.py")
    cap_text = _read(root / "winlocalassistant" / "autonomy_capabilities.py")
    webui_text = _read(root / "winlocalassistant" / "webui.py")
    readme_text = _read(root / "README.md")

    def add(name: str, ok: bool, detail: str, severity: str = "medium") -> None:
        checks.append({"name": name, "ok": bool(ok), "detail": detail, "severity": severity})

    add("version_marker", f"v{__version__}" in VERSION_LABEL and f"v{__version__}" in readme_text and f"v{__version__}" in webui_text, f"version={__version__}")
    for word in ["sandbox", "dependency", "capability", "mutable", "local-model", "comprehensive code review", "package hygiene"]:
        add(f"label_word:{word}", word in VERSION_LABEL.lower(), "legacy/version compatibility word present", "high")

    missing_commands = [cmd for cmd in CORE_COMMANDS if cmd not in core_text and cmd not in webui_text]
    add("core_command_visibility", not missing_commands, "missing: " + ", ".join(missing_commands[:12]) if missing_commands else f"{len(CORE_COMMANDS)} core commands visible", "high")

    if tool_names is None and app is not None:
        try:
            tool_names = sorted(getattr(getattr(app, "tools", None), "tools", {}).keys())
        except Exception:
            tool_names = []
    tool_names = list(tool_names or [])
    missing_tools = [name for name in AUTONOMY_TOOL_EXPECTED if name not in tool_names and f'"{name}"' not in tools_text]
    add("autonomy_tool_registry", not missing_tools, "missing: " + ", ".join(missing_tools[:12]) if missing_tools else f"{len(AUTONOMY_TOOL_EXPECTED)} autonomy tools exposed", "high")

    missing_caps = [name for name in CAPABILITY_KEYWORDS if name not in cap_text]
    add("autonomy_capability_catalog", not missing_caps, "missing: " + ", ".join(missing_caps) if missing_caps else f"{len(CAPABILITY_KEYWORDS)} capability keys present", "high")

    add("feature_audit_chat_formatter", "def _chat_check_ok" in core_text and "implemented" in core_text and "environment_dependent" in core_text, "feature-audit status values counted as pass instead of false failures", "medium")

    # Regression sweep is often run *after* Python has imported Nova and created
    # __pycache__/.pytest_cache in a temporary extracted tree. Those live-test
    # caches should not make a no-regression sweep look dirty; the strict
    # release/doctor/zip scans still catch cache artifacts before sharing.
    findings = [f for f in find_release_hygiene_findings(root, include_python_cache=False) if f.severity == "warning"]
    add("release_hygiene", not findings, f"warning artifacts: {len(findings)}; strict release hygiene remains covered by /doctor and zip artifact scan", "low")

    top_dirs = [p.name for p in root.parent.iterdir() if p.is_dir()] if root.parent.exists() else []
    add("package_folder_name", (__version__.replace(".", "_") in root.name or __version__ in root.name or "Nova" in root.name), f"current folder: {root.name}", "low")

    duplicate_route_count = len(re.findall(r'if cmd in \{[^\n]+/nova-mega-test', core_text))
    add("mega_test_routing_guard", duplicate_route_count <= 1, f"mega route blocks found: {duplicate_route_count}", "low")

    ok = all(c["ok"] or c["severity"] == "low" for c in checks)
    return {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "version": __version__,
        "ok": ok,
        "summary": "Regression sweep passed" if ok else "Regression sweep found issues",
        "checks": checks,
        "recommendations": _recommendations(checks),
    }


def _recommendations(checks: list[dict[str, Any]]) -> list[str]:
    recs = []
    if any(not c.get("ok") and c.get("name") == "autonomy_tool_registry" for c in checks):
        recs.append("Register new command families as ToolRegistry tools so idle/autonomous can actually call them.")
    if any(not c.get("ok") and c.get("name") == "core_command_visibility" for c in checks):
        recs.append("Add missing routes to core.py and quick/help visibility before release.")
    if any(not c.get("ok") and c.get("name") == "feature_audit_chat_formatter" for c in checks):
        recs.append("Fix chat check formatting so status=implemented counts as PASS.")
    if any(not c.get("ok") and c.get("name") == "release_hygiene" for c in checks):
        recs.append("Run /release-hygiene clean or remove cache/bytecode artifacts before packaging.")
    return recs or ["Keep running /regression-sweep and /nova-mega-test before sharing release zips."]


def render_regression_sweep(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Regression Sweep",
        "",
        f"Generated: {payload.get('generated_at','')}",
        f"Root: `{payload.get('root','')}`",
        f"Version: `{payload.get('version','')}`",
        f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**",
        f"Summary: {payload.get('summary','')}",
        "",
        "## Checks",
    ]
    for c in payload.get("checks", []):
        mark = "✅" if c.get("ok") else ("⚠️" if c.get("severity") == "low" else "❌")
        lines.append(f"- {mark} **{c.get('name')}** — {c.get('detail','')}")
    lines += ["", "## Recommendations"]
    lines += [f"- {x}" for x in payload.get("recommendations", [])]
    return "\n".join(lines)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""
