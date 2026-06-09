from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

from .pipeline_manifests import MANIFESTS
from .tool_orchestrator import audit_tool_awareness, build_tool_awareness_plan, plan_payload


@dataclass(frozen=True)
class RepoUpgradeCheck:
    name: str
    ok: bool
    detail: str
    category: str = "integration"


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _contains_any(text: str, markers: Iterable[str]) -> bool:
    lowered = text.lower()
    return any(str(marker).lower() in lowered for marker in markers)


def build_repo_upgrade_assurance(root: Path, *, available_tools: Iterable[str] | None = None) -> dict[str, Any]:
    """Audit the repo-research upgrades as one connected system.

    This is a readiness gate, not a broad runtime test. It verifies that the
    repo-inspired ideas Nova has been integrating are installed, command/tool
    routed, visible to autonomous/idle planning, and backed by validation hooks.
    """

    root = Path(root).resolve()
    tools = {str(t) for t in (available_tools or []) if str(t)}
    source_files = {
        "pipeline_router": root / "winlocalassistant" / "pipeline_router.py",
        "pipeline_manifests": root / "winlocalassistant" / "pipeline_manifests.py",
        "session_evidence": root / "winlocalassistant" / "session_evidence.py",
        "memory_inventory": root / "winlocalassistant" / "memory_inventory.py",
        "tool_orchestrator": root / "winlocalassistant" / "tool_orchestrator.py",
        "repo_upgrade_assurance": root / "winlocalassistant" / "repo_upgrade_assurance.py",
        "codebase_sanity_audit": root / "winlocalassistant" / "codebase_sanity_audit.py",
        "command_verifier": root / "winlocalassistant" / "command_verifier.py",
        "webui": root / "winlocalassistant" / "webui.py",
        "core": root / "winlocalassistant" / "core.py",
        "tools": root / "winlocalassistant" / "tools.py",
        "playwright_smoke": root / "playwright" / "nova_gui_smoke.spec.js",
    }
    texts = {name: _read(path) for name, path in source_files.items()}

    checks: list[RepoUpgradeCheck] = []

    for name, path in source_files.items():
        checks.append(RepoUpgradeCheck(f"module_or_asset:{name}", path.exists(), str(path), "files"))

    manifest_ids = set(MANIFESTS)
    expected_manifest_ids = {
        "checkpointed_patch",
        "coding_session_evidence",
        "browser_gui_smoke",
        "typed_memory_audit",
        "voice_state_machine",
        "local_code_index",
        "agent_observability_trace",
        "swe_issue_repair_loop",
        "agent_state_checkpoint_branch",
        "agent_control_plane",
    }
    checks.append(RepoUpgradeCheck(
        "capability_manifests:repo_research_set",
        expected_manifest_ids.issubset(manifest_ids),
        f"installed={sorted(manifest_ids)}",
        "manifests",
    ))

    required_tools = {
        "pipeline_preflight",
        "pipeline_catalog",
        "pipeline_manifest",
        "session_evidence",
        "memory_inventory",
        "project_patterns",
        "browser_smoke",
        "browser_harness",
        "tool_awareness",
        "tool_awareness_audit",
        "command_verify",
        "repo_upgrade_assurance",
        "codebase_sanity_audit",
        "repo_research_radar",
        "trace_observability_plan",
        "verifier_ladder",
    }
    missing_tools = sorted(required_tools - tools)
    checks.append(RepoUpgradeCheck(
        "tool_registry:repo_upgrade_surface",
        not missing_tools,
        "missing=" + (", ".join(missing_tools) if missing_tools else "none"),
        "tools",
    ))

    required_commands = {
        "/pipeline-preflight",
        "/pipeline-catalog",
        "/pipeline-manifest",
        "/session-evidence",
        "/memory-inventory",
        "/project-patterns",
        "/browser-smoke",
        "/tool-awareness-audit",
        "/autonomous-tool-plan",
        "/idle-tool-plan",
        "/command-verify",
        "/repo-upgrade-assurance",
        "/future-timeline",
        "/codebase-sanity-audit",
        "/repo-research-radar",
        "/trace-observability",
        "/verifier-ladder",
    }
    core_text = texts.get("core", "")
    missing_commands = sorted(command for command in required_commands if command not in core_text)
    checks.append(RepoUpgradeCheck(
        "command_routes:repo_upgrade_surface",
        not missing_commands,
        "missing=" + (", ".join(missing_commands) if missing_commands else "none"),
        "commands",
    ))

    for mode, goal in [
        ("manual", "continue integrating repo research ideas and fixing errors"),
        ("autonomous", "autonomous mode should choose tools safely before improving Nova"),
        ("idle", "idle mode should inspect logs and propose safe verified repairs"),
    ]:
        plan = build_tool_awareness_plan(goal, mode=mode, available_tools=tools)
        checks.append(RepoUpgradeCheck(
            f"tool_awareness:{mode}:coverage",
            plan.covered_tool_count >= 5 and len(plan.missing_tools) == 0,
            f"pipeline={plan.pipeline_kind}; covered={plan.covered_tool_count}/{len(plan.decisions)}; missing={list(plan.missing_tools)}",
            "orchestration",
        ))
        checks.append(RepoUpgradeCheck(
            f"tool_awareness:{mode}:validation_hooks",
            any(d.tool in {"command_verify", "tool_awareness_audit", "browser_smoke", "regression_sweep", "nova_doctor", "verifier_ladder", "auto_verify"} for d in plan.decisions),
            f"tools={[d.tool for d in plan.decisions[:12]]}",
            "orchestration",
        ))

    awareness_audit = audit_tool_awareness(tools)
    checks.append(RepoUpgradeCheck(
        "tool_awareness_audit:sample_goals",
        bool(awareness_audit.get("ok")) and not awareness_audit.get("missing_tools"),
        f"covered={len(awareness_audit.get('covered_tools') or [])}; missing={awareness_audit.get('missing_tools') or []}",
        "orchestration",
    ))

    webui_text = texts.get("webui", "")
    gui_markers = ["data-orbit-studio-shell", "messageTerminalHtml", "loadActivity", "announceNovaReady", "wlaVoiceAuthorized"]
    missing_gui = [marker for marker in gui_markers if marker not in webui_text]
    checks.append(RepoUpgradeCheck(
        "gui_voice_observability:markers",
        not missing_gui,
        "missing=" + (", ".join(missing_gui) if missing_gui else "none"),
        "gui",
    ))

    smoke_text = texts.get("playwright_smoke", "")
    checks.append(RepoUpgradeCheck(
        "browser_smoke:playwright_asset",
        "page.goto" in smoke_text and "#input" in smoke_text and "#activityLog" in smoke_text,
        "playwright/nova_gui_smoke.spec.js contains send/activity selectors",
        "gui",
    ))

    tools_text = texts.get("tools", "")
    checks.append(RepoUpgradeCheck(
        "command_verify:direct_toolregistry_tool",
        "def command_verify_tool" in tools_text and '"command_verify"' in tools_text,
        "Command verification is available as a ToolRegistry tool, not only a core-only branch.",
        "commands",
    ))
    checks.append(RepoUpgradeCheck(
        "codebase_sanity:direct_toolregistry_tool",
        "def codebase_sanity_audit_tool" in tools_text and '"codebase_sanity_audit"' in tools_text,
        "Codebase sanity audit is available as a ToolRegistry tool and command route.",
        "commands",
    ))

    checks.append(RepoUpgradeCheck(
        "autonomous_idle:tool_plan_hooks",
        "autonomous_tool_plan" in core_text and "idle_tool_plan" in core_text and "log_activity(\"autonomous_tool_plan\"" in core_text,
        "Autonomous and idle modes record tool-awareness plans before acting.",
        "background",
    ))

    passed = sum(1 for check in checks if check.ok)
    failed = len(checks) - passed
    next_timeline = [
        {
            "phase": "v55.3.150",
            "focus": "Repo research + codebase sanity gate",
            "work": "Install expanded repo-inspired manifests, add /codebase-sanity-audit and /repo-research-radar, and verify large-module/rewrite candidates without mutation.",
            "validation": "/codebase-sanity-audit + /repo-research-radar + /repo-upgrade-assurance + /regression-sweep",
        },
        {
            "phase": "v55.3.151",
            "focus": "Real browser click-through runner",
            "work": "Start Nova, run Playwright against the live Orbit GUI, capture screenshots/console errors, and link the result in /browser-smoke.",
            "validation": "Playwright + /browser-smoke + /doctor + /regression-sweep",
        },
        {
            "phase": "v55.3.152",
            "focus": "Autonomous pipeline executor",
            "work": "Move autonomous cycles from ad hoc step selection to manifest stages with checkpoint, selected tool, evidence, and validator per stage.",
            "validation": "/autonomous-tool-plan + synthetic autonomous cycle tests + rollback tests",
        },
        {
            "phase": "v55.3.153",
            "focus": "Project code index",
            "work": "Build a capped local symbol/file index for current project, used by /project-patterns and coding/repair flows before model calls.",
            "validation": "index fixtures + route checks + coding fallback tests",
        },
        {
            "phase": "v55.3.154",
            "focus": "Voice state-machine test harness",
            "work": "Add deterministic state transitions and a browser test page for wake, ready cue, listen, thinking, speaking, mute and lock states.",
            "validation": "/voice-pipeline-review + browser-smoke + JS unit checks",
        },
        {
            "phase": "v55.3.155",
            "focus": "Large-module decomposition",
            "work": "Split core.py/tools.py by command families behind compatibility wrappers, one family per patch.",
            "validation": "full command verification + feature continuity + regression sweep",
        },
    ]
    return {
        "ok": failed == 0,
        "passed": passed,
        "failed": failed,
        "total": len(checks),
        "checks": [check.__dict__ for check in checks],
        "repo_ideas_installed": sorted(expected_manifest_ids),
        "required_tools": sorted(required_tools),
        "required_commands": sorted(required_commands),
        "tool_awareness_sample": [plan_payload(build_tool_awareness_plan(goal, mode=mode, available_tools=tools, limit=10)) for mode, goal in [
            ("manual", "continue integrating repo research ideas and fixing errors"),
            ("autonomous", "autonomous mode should choose tools safely before improving Nova"),
            ("idle", "idle mode should inspect logs and propose safe verified repairs"),
        ]],
        "future_timeline": next_timeline,
    }


def render_repo_upgrade_assurance(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Repo Upgrade Assurance",
        "",
        f"Result: **{'PASS' if payload.get('ok') else 'FAIL'}**",
        f"Passed: {payload.get('passed', 0)}/{payload.get('total', 0)}",
        "",
        "## Installed repo-inspired capability set",
    ]
    for item in payload.get("repo_ideas_installed") or []:
        lines.append(f"- `{item}`")
    lines += ["", "## Readiness checks"]
    for check in payload.get("checks") or []:
        status = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- **{status}** `{check.get('name')}` — {check.get('detail')}")
    lines += ["", "## Future timeline"]
    for item in payload.get("future_timeline") or []:
        lines.append(f"- **{item.get('phase')} — {item.get('focus')}**")
        lines.append(f"  - Work: {item.get('work')}")
        lines.append(f"  - Validate: {item.get('validation')}")
    if not payload.get("ok"):
        lines += ["", "## Required next step", "Fix the failed checks above before treating repo-inspired integration as user-ready."]
    return "\n".join(lines)
