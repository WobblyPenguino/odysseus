from __future__ import annotations

import json
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .project_type_registry import PROJECT_TYPES, infer_project_type


@dataclass
class AdaptiveProposal:
    key: str
    title: str
    why: str
    value: int
    risk: str
    status: str
    implementation_hint: str
    validation: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(path: Path, limit: int = 250000) -> str:
    try:
        if path.exists() and path.is_file():
            return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""
    return ""


def _has(root: Path, rel: str, text: str) -> bool:
    return text in _read(root / rel)


def build_generation_template_manifest(goal: str = "") -> dict[str, Any]:
    """Return a compact registry of deterministic generation paths Nova can fall back to.

    This is deliberately separate from model prompting so planning/repair can reason over
    concrete build types instead of vague prose.
    """
    inferred = infer_project_type(goal or "")
    templates: list[dict[str, Any]] = []
    for kind, spec in sorted(PROJECT_TYPES.items()):
        templates.append({
            "kind": kind,
            "recommended": kind == inferred,
            "files": list(spec.get("files", [])),
            "acceptance_markers": list(spec.get("markers", [])),
            "fallback_strategy": "deterministic_baseline_then_surgical_patch",
            "validation": _validation_for_kind(kind),
        })
    return {
        "goal": goal,
        "inferred_project_type": inferred,
        "template_count": len(templates),
        "templates": templates,
        "usage_rule": "Use a deterministic template when the same local-model failure repeats or when the project type is common and low-risk.",
    }


def _validation_for_kind(kind: str) -> list[str]:
    if kind == "html_css_js_game":
        return ["node --check app.js", "game runtime sanity", "controls/collision/score/restart evidence"]
    if kind in {"html_css_js_app", "data_dashboard"}:
        return ["HTML/JS reference check", "node --check app.js", "visible input/output behaviour evidence"]
    if kind.startswith("python") or kind in {"automation_script", "mcp_server", "fastapi_app"}:
        return ["python -m py_compile", "entrypoint/import smoke", "README usage evidence"]
    if kind == "node_cli_tool":
        return ["node --check index.js", "package metadata", "example command evidence"]
    return ["syntax check", "runtime smoke", "acceptance evidence"]


def build_adaptive_backlog(root: Path, goal: str = "") -> dict[str, Any]:
    root = Path(root)
    webui = _read(root / "winlocalassistant" / "webui.py")
    tools = _read(root / "winlocalassistant" / "tools.py")
    core = _read(root / "winlocalassistant" / "core.py")
    continuity = _read(root / "winlocalassistant" / "feature_continuity.py")
    proposals: list[AdaptiveProposal] = []

    def add(prop: AdaptiveProposal) -> None:
        proposals.append(prop)

    add(AdaptiveProposal(
        key="autonomy_context_panel",
        title="Add a visible Nova/mission context panel",
        why="Autonomous and iterative build decisions are easier to trust when the current goal, last failure, strategy and acceptance checks are visible without reading raw logs.",
        value=95,
        risk="low",
        status="ready",
        implementation_hint="Render the existing nova_context/mission_contract/development_strategy data in a compact inspector panel without removing existing controls.",
        validation=["browser JS syntax", "feature continuity audit", "manual check: panel displays goal/failure/next action"],
    ))
    add(AdaptiveProposal(
        key="template_first_generation",
        title="Use deterministic templates earlier for common project types",
        why="Small local models repeatedly fail when asked for full projects. A deterministic baseline plus surgical patch is more reliable for games, scripts, dashboards and tools.",
        value=94,
        risk="medium",
        status="partially_implemented",
        implementation_hint="Expose the generation template manifest to planning/model context and switch after repeated validation failure.",
        validation=["template manifest smoke", "game fallback regression", "validation evidence checks"],
    ))
    add(AdaptiveProposal(
        key="validation_matrix_command",
        title="Add a compact validation matrix command",
        why="Users need one quick command proving the code is not just compiling but still has key behaviours and no obvious GUI/tool regressions.",
        value=90,
        risk="low",
        status="implemented_in_this_pass",
        implementation_hint="Combine compile, browser-JS extraction signal, feature-continuity markers and behaviour evidence into one tool result.",
        validation=["validation matrix unit test", "feature-continuity audit", "compileall"],
    ))
    add(AdaptiveProposal(
        key="idle_levels",
        title="Make idle mode explicitly levelled",
        why="Idle should distinguish watch/propose/prepare/apply so it remains useful without silently mutating the codebase.",
        value=88,
        risk="medium",
        status="implemented_in_this_pass",
        implementation_hint="Use /idle level 0-3 or /idle-policy to set watch/propose/prepare/apply-low-risk modes. Auto-apply is blocked below level 3.",
        validation=["idle policy command smoke", "no mutation below level 3", "receipt on level 3 apply"],
    ))
    add(AdaptiveProposal(
        key="receipt_history_viewer",
        title="Expose action/build receipts as a first-class command",
        why="Users need a short evidence trail showing what changed, what validation ran, and what still needs attention without hunting through project files.",
        value=86,
        risk="low",
        status="implemented_in_this_pass",
        implementation_hint="Use /receipt-history or /action-receipts to review recent ACTION_RECEIPT entries written by project/build/repair flows.",
        validation=["receipt history smoke", "feature-continuity audit", "compileall"],
    ))
    add(AdaptiveProposal(
        key="local_model_role_router",
        title="Route local-model calls through narrow roles",
        why="Planner, Builder, Verifier, Repairer and Toolsmith prompts need different context and output contracts; a role router reduces giant prompts and repeated off-course model output.",
        value=92,
        risk="low",
        status="implemented_in_this_pass",
        implementation_hint="Use /role-router or backend role_router to choose a role, context sections, output contract and validation focus before model/tool calls.",
        validation=["role router smoke", "nova context includes role route", "feature-continuity audit"],
    ))
    add(AdaptiveProposal(
        key="jarvis_style_supervised_bridge",
        title="Add supervised Jarvis-style daemon and sidecar bridge",
        why="Nova can learn from always-on assistants without granting unsafe authority: monitor local daemons, define sidecar policy, queue proactive actions, and keep Nova as verifier/promoter.",
        value=89,
        risk="medium",
        status="implemented_in_this_pass",
        implementation_hint="Use /jarvis-bridge, /jarvis-status, /sidecar-policy and /proactive-actions. Keep sidecar/screen/shell/browser permissions off by default and route action proposals through receipts.",
        validation=["jarvis bridge unit tests", "feature-continuity audit", "validation matrix", "localhost-only probe check"],
    ))

    add(AdaptiveProposal(
        key="left_action_transparent_inspector",
        title="Move controls left and make the right inspector output-transparent",
        why="The user should not hunt across panels for buttons. The left column should contain actions; the right column should explain state, diffs, receipts and output evidence.",
        value=93,
        risk="low",
        status="implemented_in_this_pass",
        implementation_hint="Use leftActionDock/leftFileDock for controls and transparentOutputPanel/bridgeReceiptPanel for state/output evidence.",
        validation=["webui JS syntax", "feature-continuity audit", "manual check: buttons left, output/diff right"],
    ))
    add(AdaptiveProposal(
        key="jarvis_usability_harness",
        title="Add Jarvis test prompts, bridge receipts, sidecar enrollment and safe browser harness",
        why="Jarvis integration is more useful when Nova can prove reachability, show receipts, plan browser tests and keep sidecar enrollment explicit.",
        value=91,
        risk="medium",
        status="implemented_in_this_pass",
        implementation_hint="Use /jarvis-test-prompts, /bridge-receipts, /sidecar-enrollment and /browser-harness.",
        validation=["jarvis bridge tests", "validation matrix", "policy defaults remain off"],
    ))

    add(AdaptiveProposal(
        key="hey_nova_voice_control",
        title="Add Hey Nova always-listening voice control with per-chat mute",
        why="Voice should feel conversational and controllable: wake-word activation, natural commands for settings/status, and chat-specific mute prevent global audio surprises.",
        value=87,
        risk="medium",
        status="implemented_in_this_pass",
        implementation_hint="Use /settings or the rail to enable Hey Nova. Voice commands route through voiceCommandToAction before normal chat/tool routing.",
        validation=["webui JS syntax", "feature-continuity audit", "manual check: Hey Nova wakes, chat mute affects only current chat"],
    ))

    add(AdaptiveProposal(
        key="persona_custom_chat_window",
        title="Add custom chat/persona window with sliders and response contract",
        why="Nova should be configurable as a local assistant: identity, self-model, response style and voice tone should be explicit and persistent rather than hidden in one hard-coded prompt.",
        value=90,
        risk="low",
        status="implemented_in_this_pass",
        implementation_hint="Use /persona, /persona-set, /persona-prompt and /custom-chat-window. The GUI settings panel exposes sliders that fill/apply persona commands.",
        validation=["persona tool smoke", "webui marker check", "normal chat prompt includes persona addendum"],
    ))
    add(AdaptiveProposal(
        key="local_model_optimizer_and_harness",
        title="Add local-model optimiser and iterative agent harness",
        why="Small local models need concise role-routed prompts, prompt-section caching, deterministic fallbacks and generate/execute/observe repair loops to avoid repeating failures.",
        value=91,
        risk="low",
        status="implemented_in_this_pass",
        implementation_hint="Use /local-model-optimizer and /agent-harness. Inject persona, model optimisation and harness contracts into local-model implementation context.",
        validation=["local-model-optimizer smoke", "agent-harness smoke", "context pack includes persona and optimisation contracts"],
    ))

    add(AdaptiveProposal(
        key="bug_to_test_pipeline",
        title="Turn recurring GUI/runtime bugs into regression tests automatically",
        why="ReferenceError, stale lock, broken tool refresh and wrong-target bugs should generate tests as soon as they are fixed.",
        value=85,
        risk="low",
        status="partially_implemented",
        implementation_hint="Use self_test_from_bug and add it as a suggested next step in validation receipts.",
        validation=["self-test generator smoke", "new test file syntax", "targeted pytest"],
    ))

    # Mark known implementation surfaces so the backlog is grounded in real code.
    implemented_markers = {
        "nova_context": "nova_context" in tools and "/nova-context" in core,
        "mission_contract": "mission_contract" in tools and "/mission-contract" in core,
        "development_strategy": "development_strategy" in tools and "/development-strategy" in core,
        "feature_continuity": "build_feature_continuity_audit" in continuity or "feature_continuity_audit" in tools,
        "run_deletion_gui": "deleteSelectedRuns" in webui and "runSelect" in webui,
        "idle_policy": "idle_policy" in tools and "/idle level" in core,
        "receipt_history": "receipt_history" in tools and "/receipt-history" in core,
        "role_router": "role_router" in tools and "/role-router" in core and "build_role_route" in _read(root / "winlocalassistant" / "role_router.py"),
        "jarvis_bridge": "jarvis_bridge" in tools and "/jarvis-bridge" in core and "probe_jarvis_daemon" in _read(root / "winlocalassistant" / "jarvis_bridge.py"),
        "left_action_transparent_inspector": "leftActionDock" in webui and "transparentOutputPanel" in webui and "bridgeReceiptPanel" in webui,
        "jarvis_usability_harness": "bridge_receipts" in tools and "sidecar_enrollment" in tools and "browser_harness" in tools and "/jarvis-test-prompts" in core,
        "hey_nova_voice_control": "toggleWakeWordListening" in webui and "voiceCommandToAction" in webui and "toggleCurrentChatMute" in webui,
        "persona_custom_chat_window": "personaMiniPanel" in webui and "custom-chat-window" in webui and "persona_profile" in tools,
        "local_model_optimizer_and_harness": "local_model_optimizer" in tools and "agent_harness" in tools and "local_model_optimization_plan" in tools,
        "startup_validation_audit_workflow": "startup_validation" in tools and "audit_log" in tools and "workflow_run" in tools and "startup-validation" in core,
    }
    return {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "goal": goal,
        "implemented_markers": implemented_markers,
        "proposals": [p.to_dict() for p in sorted(proposals, key=lambda p: p.value, reverse=True)],
        "top_recommendation": "Use the left action dock for commands, keep the right inspector transparent, use Hey Nova for conversational voice control, run Jarvis doctor/test prompts, and make template-first generation automatic after repeated behaviour failures.",
    }


def render_adaptive_backlog(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Adaptive Improvement Backlog",
        "",
        f"Root: `{payload.get('root','')}`",
        f"Goal/focus: {payload.get('goal') or 'general Nova improvement'}",
        "",
        "## Implemented capability markers",
    ]
    for key, ok in (payload.get("implemented_markers") or {}).items():
        lines.append(f"- {'PASS' if ok else 'MISSING'} {key}")
    lines.append("\n## Ranked proposals")
    for idx, prop in enumerate(payload.get("proposals") or [], 1):
        lines += [
            f"{idx}. **{prop.get('title')}** — value {prop.get('value')} / risk {prop.get('risk')} / status {prop.get('status')}",
            f"   - Why: {prop.get('why')}",
            f"   - Implementation: {prop.get('implementation_hint')}",
            f"   - Validate: {', '.join(prop.get('validation') or [])}",
        ]
    lines += ["", "## Next best action", str(payload.get("top_recommendation") or "Run validation matrix, then implement the smallest safe proposal.")]
    return "\n".join(lines)


def render_template_manifest(payload: dict[str, Any]) -> str:
    lines = [
        "# Generation Template Manifest",
        "",
        f"Goal: {payload.get('goal') or 'not specified'}",
        f"Inferred type: `{payload.get('inferred_project_type')}`",
        "",
        "## Templates",
    ]
    for item in payload.get("templates") or []:
        mark = "recommended" if item.get("recommended") else "available"
        lines.append(f"- **{item.get('kind')}** ({mark}) — files: {', '.join(item.get('files') or [])}")
        lines.append(f"  - Acceptance: {', '.join(item.get('acceptance_markers') or [])}")
        lines.append(f"  - Validation: {', '.join(item.get('validation') or [])}")
    lines.append("\n" + str(payload.get("usage_rule") or ""))
    return "\n".join(lines)
