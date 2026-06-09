from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from . import __version__
from .autonomy_capabilities import get_capability_catalog, select_capabilities_for_goal
from .safe_io import atomic_write_json, atomic_write_text

CRITICAL_FLOW_GROUPS: dict[str, dict[str, Any]] = {
    "build_and_validate": {
        "description": "Prompt-specific app/file building path from user goal to validated artifact.",
        "commands": ["/prompt-contract", "/candidate-tournament", "/iterative-code-loop", "/build-quality-report", "/browser-run-test", "/model-output-coach"],
        "tools": ["prompt_contract", "candidate_tournament", "iterative_coding_loop", "build_quality_report", "browser_runtime_test", "model_output_coach"],
        "capabilities": ["prompt_to_test", "candidate_tournament", "iterative_coding_repair", "build_quality_browser_runtime"],
        "why": "Prevents technically-valid-but-wrong projects and validates real prompt requirements.",
    },
    "repair_and_fallback": {
        "description": "Minimal-diff repair path before broad regeneration.",
        "commands": ["/repair-diagnose", "/repair-plan", "/surgical-fallback-v2", "/edit-repair-plan", "/repair-verify", "/patch-propose"],
        "tools": ["repair_plan_v2", "surgical_fallback_v2", "edit_repair_plan", "patch_queue"],
        "capabilities": ["surgical_repair_v2", "iterative_coding_repair", "patch_queue_and_learning"],
        "why": "Keeps repairs small, evidence-driven, staged and reversible.",
    },
    "autonomous_idle_learning": {
        "description": "Mission-aware autonomy with progress scoring, repetition guard and mistake learning.",
        "commands": ["/mission-dashboard", "/cycle-score", "/tool-choice-trace", "/repetition-guard-status", "/mistake-learning-status", "/mistake-to-regression"],
        "tools": ["mission_dashboard", "cycle_score", "tool_choice_trace", "repetition_guard_status", "mistake_learning_status", "mistake_to_regression"],
        "capabilities": ["mission_intelligence", "cycle_progress_scoring", "tool_choice_trace", "repetition_guard", "patch_queue_and_learning"],
        "why": "Stops vague no-op cycles and records lessons from repeated failures.",
    },
    "model_dependency_and_reliability": {
        "description": "Model readiness, fallback, stuck detection and confirmable model downloads.",
        "commands": ["/model-requirements", "/model-readiness", "/model-download-plan", "/model-install", "/model-reliability", "/model-fallback-strategy"],
        "tools": ["model_readiness", "model_requirements", "model_download_plan", "model_install", "model_reliability", "model_fallback_strategy"],
        "capabilities": ["model_dependency_management", "model_reliability_controller"],
        "why": "Prevents long stuck prompts and explains when a stronger/missing model is required.",
    },
    "regression_support_and_reporting": {
        "description": "No-regression checks, support export, error translation and one-command coverage.",
        "commands": ["/regression-sweep", "/bug-review", "/whole-codebase-review", "/nova-mega-test", "/support-report", "/explain-error"],
        "tools": ["regression_sweep", "bug_review", "whole_codebase_review", "support_report", "explain_error"],
        "capabilities": ["weakspot_error_hunt", "support_and_error_translation", "improvement_roadmap"],
        "why": "Keeps new features from hiding old breakage and produces clean diagnostics.",
    },
    "tool_extension_and_sandboxing": {
        "description": "Guarded self-extension and copied-workspace sandbox testing before live promotion.",
        "commands": ["/tool-create", "/tool-test", "/tool-run", "/sandbox-dev-run", "/docker-validate"],
        "tools": ["tool_create", "tool_test", "tool_run", "sandbox_dev_run", "docker_validate"],
        "capabilities": ["custom_tool_extension", "sandbox_dev_copy"],
        "why": "Lets Nova add helpers while keeping new code validated away from live files.",
    },
}

def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""

def _command_visible(command: str, core_text: str, readme_text: str, webui_text: str) -> bool:
    return command in core_text or command in readme_text or command in webui_text

def build_flow_audit(root: Path, *, tool_names: list[str] | None = None) -> dict[str, Any]:
    root = Path(root)
    core_text = _read_text(root / "winlocalassistant" / "core.py")
    readme_text = _read_text(root / "README.md")
    webui_text = _read_text(root / "winlocalassistant" / "webui.py")
    cap_names = {cap.name for cap in get_capability_catalog()}
    tool_set = set(tool_names or [])
    groups: list[dict[str, Any]] = []
    issues: list[dict[str, Any]] = []
    for group_name, spec in CRITICAL_FLOW_GROUPS.items():
        missing_commands = [cmd for cmd in spec["commands"] if not _command_visible(cmd, core_text, readme_text, webui_text)]
        missing_tools = [tool for tool in spec["tools"] if tool_set and tool not in tool_set]
        missing_caps = [cap for cap in spec["capabilities"] if cap not in cap_names]
        ok = not missing_commands and not missing_tools and not missing_caps
        group = {"name": group_name, "ok": ok, "description": spec["description"], "why": spec["why"], "commands": spec["commands"], "tools": spec["tools"], "capabilities": spec["capabilities"], "missing_commands": missing_commands, "missing_tools": missing_tools, "missing_capabilities": missing_caps}
        groups.append(group)
        for kind, missing in (("command", missing_commands), ("tool", missing_tools), ("capability", missing_caps)):
            for item in missing:
                issues.append({"severity": "high", "group": group_name, "kind": kind, "item": item, "recommendation": "Wire this surface into chat routing, ToolRegistry and autonomy capability selection."})
    scenario_goals = {
        "build_path": "make a tiny useful notes app with localStorage and JSON export",
        "repair_path": "fix the app because export button and localStorage are broken",
        "model_path": "download or request the required coding model for a difficult repair",
        "autonomy_path": "make autonomous and idle learn from mistakes and avoid repeating failed strategies",
        "tool_path": "make yourself a useful custom tool and test it in a sandbox copy",
    }
    scenarios = []
    for name, goal in scenario_goals.items():
        matches = select_capabilities_for_goal(goal, limit=8)
        scenarios.append({"name": name, "goal": goal, "selected_capabilities": [m.capability.name for m in matches], "tool_reasons": [m.why for m in matches], "first_commands": [m.suggested_first_command for m in matches]})
    ok = not any(i.get("severity") in {"critical", "high"} for i in issues)
    return {"ok": ok, "version": __version__, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "root": str(root), "summary": "Interaction flow audit passed" if ok else f"Interaction flow audit found {len(issues)} issue(s)", "groups": groups, "scenarios": scenarios, "issues": issues, "proposed_improvements": ["Keep generated-project flows gated by prompt contracts, candidate tournaments and browser/runtime quality checks.", "Use repair v2 and iterative coding before broad regeneration when a project is close but broken.", "Require model-readiness checks before model-heavy/vision/coding tasks and explicit --confirm before downloads.", "Route idle/autonomous through mission progress scoring and repetition guard after every cycle.", "Export support reports after failures so future debugging carries version, trace, model and project state together."]}

def render_flow_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Interaction Flow and No-Regression Audit", "", f"Generated: {payload.get('generated_at')}", f"Root: `{payload.get('root')}`", f"Version: {payload.get('version')}", f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**", f"Summary: {payload.get('summary')}", "", "## Flow groups"]
    for group in payload.get("groups", []):
        icon = "✅" if group.get("ok") else "❌"
        lines += [f"- {icon} **{group.get('name')}** — {group.get('description')}", f"  - why: {group.get('why')}", f"  - commands: {', '.join(f'`{c}`' for c in group.get('commands', []))}", f"  - tools: {', '.join(f'`{t}`' for t in group.get('tools', []))}", f"  - capabilities: {', '.join(f'`{c}`' for c in group.get('capabilities', []))}"]
        for label, key in (("missing commands", "missing_commands"), ("missing tools", "missing_tools"), ("missing capabilities", "missing_capabilities")):
            if group.get(key):
                lines.append(f"  - {label}: {', '.join(group[key])}")
    lines += ["", "## Scenario tool choices"]
    for scenario in payload.get("scenarios", []):
        lines += [f"- **{scenario.get('name')}** — {scenario.get('goal')}", f"  - selected: {', '.join(scenario.get('selected_capabilities', []))}", f"  - first commands: {', '.join(f'`{c}`' for c in scenario.get('first_commands', [])[:5])}"]
    if payload.get("issues"):
        lines += ["", "## Issues"]
        for i, issue in enumerate(payload.get("issues", []), 1):
            lines.append(f"{i}. **{str(issue.get('severity','')).upper()}** / {issue.get('group')} / {issue.get('kind')} — {issue.get('item') or issue.get('path')}")
            if issue.get("recommendation"):
                lines.append(f"   - recommendation: {issue.get('recommendation')}")
    lines += ["", "## Implemented/proposed improvement policy"]
    for item in payload.get("proposed_improvements", []):
        lines.append(f"- {item}")
    return "\n".join(lines)

def write_flow_audit(root: Path, *, tool_names: list[str] | None = None):
    payload = build_flow_audit(root, tool_names=tool_names)
    docs = Path(root) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    md = docs / "NOVA_INTERACTION_FLOW_AUDIT_LATEST.md"
    js = docs / "NOVA_INTERACTION_FLOW_AUDIT_LATEST.json"
    atomic_write_text(md, render_flow_audit(payload))
    atomic_write_json(js, payload)
    return md, js, payload
