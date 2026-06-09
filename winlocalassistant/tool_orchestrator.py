from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any, Iterable

from .autonomy_capabilities import build_mutable_mission_plan, select_capabilities_for_goal
from .pipeline_manifests import choose_manifests_for_goal
from .pipeline_router import classify_pipeline


@dataclass(frozen=True)
class ToolDecision:
    """One explainable tool choice for autonomous, idle or manual planning.

    This is intentionally metadata-only: it teaches Nova which tool to choose,
    when to choose it, and what should validate it. Execution still goes through
    the existing ToolRegistry/capability gates.
    """

    stage: str
    tool: str
    reason: str
    validates_with: str
    available: bool
    mutates: bool = False
    source: str = "pipeline"


@dataclass(frozen=True)
class ToolAwarenessPlan:
    goal: str
    mode: str
    pipeline_kind: str
    pipeline_title: str
    manifest_ids: tuple[str, ...]
    selected_capabilities: tuple[str, ...]
    decisions: tuple[ToolDecision, ...]
    missing_tools: tuple[str, ...]
    covered_tool_count: int
    available_tool_count: int
    stop_conditions: tuple[str, ...]
    notes: tuple[str, ...]


def _normalise_tool_name(value: str) -> str:
    tool = (value or "").strip().strip("`")
    if tool.startswith("/"):
        tool = tool[1:]
    tool = tool.split()[0] if tool else ""
    tool = tool.replace("-", "_")
    aliases = {
        "nova_doctor": "nova_doctor",
        "doctor": "nova_doctor",
        "release_hygiene": "wla_release_gate",
        "project_state": "project_state",
        "project_state_audit": "project_state",
        "db": "assistant_db",
        "database": "assistant_db",
        "command_verifier": "command_verify",
        "command_verify": "command_verify",
        "command_contracts": "command_verify",
        "architecture_audit": "architecture_audit",
        "bug_review": "bug_review",
        "browser_harness": "browser_harness",
        "node": "browser_smoke",
        "node_check": "browser_smoke",
        "test_project": "auto_verify",
        "trace_observability": "trace_observability_plan",
        "trace_spec": "trace_observability_plan",
        "verifier_ladder": "verifier_ladder",
        "validation_ladder_plus": "verifier_ladder",
        "codebase_sanity_audit": "codebase_sanity_audit",
        "sanity_audit": "codebase_sanity_audit",
        "repo_research_radar": "repo_research_radar",
        "tool_awareness_audit": "tool_awareness_audit",
        "repo_upgrade_assurance": "repo_upgrade_assurance",
        "sidecar_policy": "sidecar_policy",
    }
    return aliases.get(tool, tool)


def _available_set(available_tools: Iterable[str] | None) -> set[str]:
    return {str(t).strip() for t in (available_tools or []) if str(t).strip()}


def _tool_available(tool: str, available: set[str]) -> bool:
    if not tool:
        return False
    if not available:
        return True
    return tool in available


def _append_decision(decisions: list[ToolDecision], seen: set[tuple[str, str]], *, stage: str, tool: str, reason: str, validates_with: str, available: bool, mutates: bool = False, source: str = "pipeline") -> None:
    key = (stage.lower(), tool)
    if key in seen or not tool:
        return
    seen.add(key)
    decisions.append(ToolDecision(stage=stage, tool=tool, reason=reason, validates_with=validates_with, available=available, mutates=mutates, source=source))


def build_tool_awareness_plan(goal: str, *, mode: str = "manual", available_tools: Iterable[str] | None = None, limit: int = 16) -> ToolAwarenessPlan:
    """Build a repo-inspired, tool-aware plan for Nova background modes.

    The plan fuses:
    - pipeline routing (OpenMontage-style staged workflows),
    - capability manifests (repo-research contracts),
    - autonomy capability matches (when/how/validation guidance), and
    - the actual ToolRegistry surface so idle/autonomous can avoid nonexistent tools.
    """

    text = (goal or "Improve Nova safely").strip()
    mode_clean = (mode or "manual").strip().lower() or "manual"
    available = _available_set(available_tools)
    route = classify_pipeline(text)
    manifests = choose_manifests_for_goal(text)
    mission_plan = build_mutable_mission_plan(text)
    matches = select_capabilities_for_goal(text, limit=12)

    decisions: list[ToolDecision] = []
    seen: set[tuple[str, str]] = set()

    # Always start background modes with the same safe awareness checks.
    if mode_clean in {"autonomous", "idle"}:
        prefix = "Autonomous" if mode_clean == "autonomous" else "Idle"
        for stage, tool, reason, validation in [
            (f"{prefix} route preflight", "pipeline_preflight", "Classify the goal before model calls or mutation.", "route kind and stages are recorded"),
            (f"{prefix} tool awareness", "tool_awareness", "Check that selected tools exist in the current registry.", "missing tools are reported before use"),
            (f"{prefix} evidence", "session_evidence", "Use recent run evidence instead of guessing.", "recent events are summarized"),
            (f"{prefix} memory", "memory_inventory", "Inspect typed memory/state stores for lessons and stale data.", "memory inventory is readable"),
        ]:
            _append_decision(decisions, seen, stage=stage, tool=tool, reason=reason, validates_with=validation, available=_tool_available(tool, available), source="background-preflight")

    for stage in route.stages:
        tool = _normalise_tool_name(stage.tool)
        _append_decision(
            decisions,
            seen,
            stage=stage.name,
            tool=tool,
            reason=stage.reason,
            validates_with=stage.validates,
            mutates=stage.mutates,
            available=_tool_available(tool, available),
            source="pipeline-router",
        )

    for manifest in manifests:
        for raw_tool in manifest.validation[:3]:
            tool = _normalise_tool_name(raw_tool)
            _append_decision(
                decisions,
                seen,
                stage=f"Manifest: {manifest.manifest_id}",
                tool=tool,
                reason=f"{manifest.purpose} ({manifest.inspired_by}).",
                validates_with=", ".join(manifest.validation),
                available=_tool_available(tool, available),
                source="capability-manifest",
            )

    for match in matches[:6]:
        cap = match.capability
        first = cap.commands[0] if cap.commands else ""
        tool = _normalise_tool_name(first)
        _append_decision(
            decisions,
            seen,
            stage=f"Capability: {cap.name}",
            tool=tool,
            reason="; ".join(cap.use_when[:2]) or match.why,
            validates_with=", ".join(cap.validates_with) or "manual evidence",
            available=_tool_available(tool, available),
            mutates=cap.risk not in {"low", "read_only"} and any(w in tool for w in ("write", "apply", "create", "improve")),
            source="autonomy-capability",
        )

    decisions = decisions[: max(1, int(limit or 16))]
    missing = tuple(d.tool for d in decisions if not d.available)
    covered = len({d.tool for d in decisions if d.available})
    notes = [
        "Idle/autonomous should consult this plan before choosing tools.",
        "Unavailable tools are evidence, not fatal errors; Nova should choose the next safe available diagnostic.",
        "Mutating steps require existing safety gates, backups and validation.",
    ]
    if any(d.mutates for d in decisions):
        notes.append("At least one selected step can mutate; validation/rollback evidence is required before claiming success.")
    if missing:
        notes.append("Some selected commands are not registered as tools and should be routed through existing command handlers or replaced with available equivalents.")

    stop_conditions = tuple(dict.fromkeys(list(mission_plan.stop_conditions) + [
        "selected tool is unavailable and no safe equivalent exists",
        "validation tool fails twice without a new strategy",
        "user foreground task or model prompt becomes active",
    ]))

    return ToolAwarenessPlan(
        goal=text,
        mode=mode_clean,
        pipeline_kind=route.kind,
        pipeline_title=route.title,
        manifest_ids=tuple(m.manifest_id for m in manifests),
        selected_capabilities=tuple(m.capability.name for m in matches),
        decisions=tuple(decisions),
        missing_tools=missing,
        covered_tool_count=covered,
        available_tool_count=len(available),
        stop_conditions=stop_conditions,
        notes=tuple(notes),
    )


def plan_payload(plan: ToolAwarenessPlan) -> dict[str, Any]:
    return asdict(plan)


def render_tool_awareness_plan(plan: ToolAwarenessPlan) -> str:
    lines = [
        "# Nova Tool-Awareness Plan",
        "",
        f"Goal: {plan.goal}",
        f"Mode: `{plan.mode}`",
        f"Pipeline: **{plan.pipeline_title}** (`{plan.pipeline_kind}`)",
        f"Repo-inspired manifests: {', '.join(plan.manifest_ids) or 'none'}",
        f"Selected capabilities: {', '.join(plan.selected_capabilities) or 'none'}",
        f"Registered tool coverage: {plan.covered_tool_count}/{len(plan.decisions)} selected tools available",
        "",
        "## Tool decisions",
    ]
    for index, decision in enumerate(plan.decisions, 1):
        status = "available" if decision.available else "missing"
        mut = "; mutates" if decision.mutates else ""
        lines.append(f"{index}. **{decision.stage}** → `{decision.tool}` ({status}{mut}; source={decision.source})")
        lines.append(f"   - When/why: {decision.reason}")
        lines.append(f"   - Validate with: {decision.validates_with}")
    if plan.missing_tools:
        lines += ["", "## Missing / command-only tools", *[f"- `{tool}`" for tool in plan.missing_tools]]
    lines += ["", "## Stop conditions"]
    lines.extend(f"- {item}" for item in plan.stop_conditions[:8])
    lines += ["", "## Notes"]
    lines.extend(f"- {item}" for item in plan.notes)
    return "\n".join(lines)


def audit_tool_awareness(available_tools: Iterable[str], goals: Iterable[str] | None = None) -> dict[str, Any]:
    available = sorted(_available_set(available_tools))
    goal_list = list(goals or [
        "continue integrating repo ideas and fixing errors",
        "run autonomous mode to improve Nova safely",
        "idle mode should inspect logs and propose safe fixes",
        "test all functionality and ensure no regression",
        "review database/state integrity",
    ])
    plans = [build_tool_awareness_plan(goal, mode="autonomous", available_tools=available) for goal in goal_list]
    all_missing = sorted({tool for plan in plans for tool in plan.missing_tools})
    covered = sorted({decision.tool for plan in plans for decision in plan.decisions if decision.available})
    return {
        "available_tool_count": len(available),
        "sample_goals": goal_list,
        "plans": [plan_payload(plan) for plan in plans],
        "covered_tools": covered,
        "missing_tools": all_missing,
        "ok": len(covered) >= 5,
    }


def render_tool_awareness_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Tool Awareness Audit",
        "",
        f"Registered tools: {payload.get('available_tool_count', 0)}",
        f"Sample plans: {len(payload.get('plans') or [])}",
        f"Coverage result: {'PASS' if payload.get('ok') else 'ATTENTION'}",
        "",
        "## Covered tools",
    ]
    covered = payload.get("covered_tools") or []
    lines.extend(f"- `{tool}`" for tool in covered[:80])
    missing = payload.get("missing_tools") or []
    if missing:
        lines += ["", "## Missing / command-only selected tools"]
        lines.extend(f"- `{tool}`" for tool in missing[:80])
    lines += ["", "## Goal samples"]
    for plan in payload.get("plans") or []:
        lines.append(f"- `{plan.get('pipeline_kind')}` — {plan.get('goal')} ({plan.get('covered_tool_count')}/{len(plan.get('decisions') or [])} selected tools available)")
    return "\n".join(lines)
