from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


@dataclass(frozen=True)
class CapabilityManifest:
    """A small OpenMontage-style manifest that maps outside repo ideas to Nova.

    These manifests are intentionally source-code-independent: Nova borrows the
    workflow pattern, not third-party code. They give the router/autonomous mode a
    stable contract for what to observe, what may mutate, and what must validate.
    """

    manifest_id: str
    inspired_by: str
    purpose: str
    nova_area: str
    triggers: tuple[str, ...]
    stages: tuple[str, ...]
    validation: tuple[str, ...]
    guardrails: tuple[str, ...]
    upgrade_notes: str


MANIFESTS: dict[str, CapabilityManifest] = {
    "checkpointed_patch": CapabilityManifest(
        manifest_id="checkpointed_patch",
        inspired_by="OpenMontage pipeline/checkpoint workflow",
        purpose="Make self-edits observable and reversible before promotion.",
        nova_area="patching/autonomous/code-review",
        triggers=("patch", "self-edit", "autonomous improvement", "fix Nova", "rewrite"),
        stages=(
            "classify request into a typed pipeline",
            "capture checkpoint and file impact plan",
            "apply the smallest patch",
            "run impact tests and release hygiene",
            "promote only after explicit validation evidence",
        ),
        validation=("/pipeline-preflight", "/patch-impact-plan", "/regression-sweep", "/doctor"),
        guardrails=("no broad rewrite without a manifest", "preserve rollback path", "show evidence in timeline"),
        upgrade_notes="Use for future Nova self-improvement cycles instead of improvised direct edits.",
    ),
    "coding_session_evidence": CapabilityManifest(
        manifest_id="coding_session_evidence",
        inspired_by="OpenHands coding-session observability",
        purpose="Show the commands, tools, files and validation evidence behind a reply.",
        nova_area="chat/live-activity/developer-mode",
        triggers=("what did you run", "show evidence", "terminal", "commands", "why did it fail"),
        stages=(
            "collect recent run events",
            "group by run/tool/file context",
            "summarise commands and validation outcomes",
            "render a compact expandable transcript",
        ),
        validation=("/session-evidence", "/live-timeline", "/command-verify"),
        guardrails=("redact secrets", "cap event count", "never claim success without an event"),
        upgrade_notes="Backs the collapsed terminal indicator requested in the Orbit GUI.",
    ),
    "browser_gui_smoke": CapabilityManifest(
        manifest_id="browser_gui_smoke",
        inspired_by="browser-use style web interaction checks",
        purpose="Catch GUI regressions that static JS parsing misses.",
        nova_area="webui/orbit-gui/voice-panels",
        triggers=("gui", "drawer", "button", "browser", "overlap", "console error"),
        stages=(
            "parse inline JS",
            "verify required UI markers",
            "prepare browser harness command",
            "record console/layout risk notes",
        ),
        validation=("/browser-smoke", "/browser-harness", "node --check extracted JS"),
        guardrails=("do not rely on screenshots alone", "record console errors", "keep fallback static smoke"),
        upgrade_notes="Next step is a real Playwright click-through when browser automation is available.",
    ),
    "typed_memory_audit": CapabilityManifest(
        manifest_id="typed_memory_audit",
        inspired_by="Mem0/OpenMemory typed memory layers",
        purpose="Separate user, project, bug, model and UI memory so recall is auditable.",
        nova_area="assistant datastore/project_state_db/regression memory",
        triggers=("memory", "database", "state", "remember", "stale", "recall"),
        stages=(
            "list typed stores",
            "audit record counts and invalid JSON",
            "flag stale or oversized records",
            "recommend compact/export/forget actions",
        ),
        validation=("/db audit", "/project-state audit", "/memory-inventory"),
        guardrails=("do not delete without confirmation", "preserve source timestamps", "quarantine corrupt state"),
        upgrade_notes="Keeps Nova from silently overwriting corrupted or stale project state.",
    ),
    "voice_state_machine": CapabilityManifest(
        manifest_id="voice_state_machine",
        inspired_by="LiveKit/TEN real-time voice-agent state machines",
        purpose="Make wake, ready cue, recording, thinking and speaking mutually exclusive and testable.",
        nova_area="web voice pipeline/communication centre",
        triggers=("Hey Nova", "wake", "ready sound", "listening", "speaking", "voice lock"),
        stages=(
            "wake detected",
            "ready cue attempted and reported",
            "record/transcribe after cue",
            "pause wake while thinking/speaking",
            "speak concise summary only",
        ),
        validation=("/voice-pipeline-review", "/browser-smoke", "/live-timeline"),
        guardrails=("browser audio failure must be visible", "avoid transcript spam", "respect mute"),
        upgrade_notes="Improves the Alexa-style handoff sound and reduces redundant sub-chat text.",
    ),

    "agent_observability_trace": CapabilityManifest(
        manifest_id="agent_observability_trace",
        inspired_by="OpenTelemetry, Langfuse and AgentOps agent observability",
        purpose="Make agent runs traceable with spans for route, tool, model, file, validation and outcome.",
        nova_area="activity/session-evidence/trace-cockpit",
        triggers=("observability", "trace", "span", "telemetry", "langfuse", "agentops", "opentelemetry"),
        stages=(
            "create route span",
            "record tool/model/file spans",
            "attach validation outcome",
            "summarise evidence without secrets",
        ),
        validation=("/trace-observability", "/session-evidence", "/live-timeline", "/codebase-sanity-audit"),
        guardrails=("redact prompt secrets", "cap payload size", "do not claim success without a validation span"),
        upgrade_notes="Use this to converge Nova activity logs, collapsed terminal evidence and future OpenTelemetry exports.",
    ),
    "swe_issue_repair_loop": CapabilityManifest(
        manifest_id="swe_issue_repair_loop",
        inspired_by="SWE-agent and mini-swe-agent issue-driven repair loops",
        purpose="Turn a bug/request into inspect, patch, test and evidence steps instead of improvising a new app.",
        nova_area="coding/repair/project-review",
        triggers=("github issue", "bug", "repair", "fix issue", "swe-agent", "mini-swe"),
        stages=(
            "parse issue/request",
            "inspect relevant files",
            "apply minimal patch",
            "run verifier ladder",
            "record session evidence",
        ),
        validation=("/pipeline-preflight", "/patch-impact-plan", "/verifier-ladder", "/session-evidence"),
        guardrails=("no unrelated project generation", "patch only relevant files", "rollback if verifier fails"),
        upgrade_notes="This addresses repeated failures where broad repair prompts became unrelated stock-app generations.",
    ),
    "agent_state_checkpoint_branch": CapabilityManifest(
        manifest_id="agent_state_checkpoint_branch",
        inspired_by="AgentGit-style checkpoint, branch and rollback for agent workflows",
        purpose="Let autonomous/idle explore safe branches while preserving a known-good state.",
        nova_area="autonomous/idle/recovery/project_state_db",
        triggers=("checkpoint", "rollback", "branch", "agentgit", "backtrack", "revert"),
        stages=(
            "snapshot current state",
            "label proposed branch",
            "run bounded experiment",
            "compare evidence",
            "promote or preserve checkpoint",
        ),
        validation=("/project-state audit", "/session-evidence", "/regression-sweep", "/doctor"),
        guardrails=("never delete checkpoint automatically", "no broad mutation without verifier", "prefer deterministic fix first"),
        upgrade_notes="Use for future autonomous executor work so failed attempts do not corrupt the active workspace.",
    ),
    "agent_control_plane": CapabilityManifest(
        manifest_id="agent_control_plane",
        inspired_by="Agno control-plane patterns with scheduling, RBAC and human review loops",
        purpose="Expose which agent/tool can act, when it may run, and what approval or validation is required.",
        nova_area="tool-awareness/permissions/scheduler/autonomous",
        triggers=("control plane", "rbac", "permission", "schedule", "human review", "approval"),
        stages=(
            "identify requested capability",
            "check tool permission and schedule",
            "require human review for mutation",
            "log approval/evidence",
        ),
        validation=("/tool-awareness-audit", "/sidecar-policy", "/command-verify", "/repo-upgrade-assurance"),
        guardrails=("user-facing approval for risky actions", "tool availability checked before execution", "stop on missing permission"),
        upgrade_notes="This should become the shared policy layer for idle, autonomous and manual action buttons.",
    ),
    "local_code_index": CapabilityManifest(
        manifest_id="local_code_index",
        inspired_by="Tabby/local code assistant indexing",
        purpose="Find related files and project structure before asking the model to edit.",
        nova_area="project-patterns/search/code review",
        triggers=("find file", "related files", "codebase", "index", "explain this file"),
        stages=(
            "scan file suffixes and entrypoints",
            "write NOVA_PATTERNS.md when confirmed",
            "choose verifiers from project shape",
            "route edits through pattern-aware coding",
        ),
        validation=("/project-patterns --write", "/search-nova-code", "/patch-impact-plan"),
        guardrails=("ignore caches/runtime folders", "cap scan size", "prefer project-local evidence"),
        upgrade_notes="Prevents unrelated stock-app/file-creator outputs by grounding the task in the current project.",
    ),
}


def manifest_payload(manifest: CapabilityManifest) -> dict[str, Any]:
    return asdict(manifest)


def list_manifest_payloads() -> list[dict[str, Any]]:
    return [manifest_payload(m) for m in MANIFESTS.values()]


def choose_manifests_for_goal(goal: str) -> list[CapabilityManifest]:
    g = (goal or "").lower()
    matches: list[CapabilityManifest] = []
    for manifest in MANIFESTS.values():
        if any(trigger.lower() in g for trigger in manifest.triggers):
            matches.append(manifest)
    if not matches:
        matches = [MANIFESTS["checkpointed_patch"], MANIFESTS["coding_session_evidence"], MANIFESTS["browser_gui_smoke"]]
    return matches[:4]


def render_manifest_catalog(goal: str = "") -> str:
    selected = choose_manifests_for_goal(goal)
    selected_ids = {m.manifest_id for m in selected}
    lines = [
        "# Nova Repo-Inspired Capability Manifests",
        "",
        "These are fresh Nova contracts inspired by the repo research. They borrow architecture ideas, not third-party code.",
        "",
    ]
    if goal:
        lines += [f"Goal focus: `{goal}`", "", "## Best matching manifests"]
        for manifest in selected:
            lines.append(f"- **{manifest.manifest_id}** — {manifest.purpose}")
        lines.append("")
    lines.append("## Catalog")
    for manifest in MANIFESTS.values():
        prefix = "★ " if manifest.manifest_id in selected_ids else "- "
        lines.append(f"{prefix}**{manifest.manifest_id}** ({manifest.inspired_by})")
        lines.append(f"  - Area: {manifest.nova_area}")
        lines.append(f"  - Purpose: {manifest.purpose}")
        lines.append(f"  - Validate with: {', '.join(manifest.validation)}")
    return "\n".join(lines)


def render_manifest(manifest_id: str) -> str:
    key = (manifest_id or "").strip().lower().replace(" ", "_")
    manifest = MANIFESTS.get(key)
    if not manifest:
        return render_manifest_catalog(manifest_id)
    lines = [
        f"# Capability Manifest: {manifest.manifest_id}",
        "",
        f"Inspired by: **{manifest.inspired_by}**",
        f"Nova area: `{manifest.nova_area}`",
        f"Purpose: {manifest.purpose}",
        "",
        "## Triggers",
        *[f"- {x}" for x in manifest.triggers],
        "",
        "## Stages",
        *[f"{i}. {stage}" for i, stage in enumerate(manifest.stages, 1)],
        "",
        "## Validation",
        *[f"- `{x}`" for x in manifest.validation],
        "",
        "## Guardrails",
        *[f"- {x}" for x in manifest.guardrails],
        "",
        "## Upgrade note",
        manifest.upgrade_notes,
    ]
    return "\n".join(lines)


def write_manifest_snapshot(root: Path, goal: str = "") -> dict[str, Any]:
    root = Path(root).resolve()
    selected = choose_manifests_for_goal(goal)
    payload = {
        "goal": goal,
        "selected": [manifest_payload(m) for m in selected],
        "catalog": list_manifest_payloads(),
    }
    out_dir = root / "docs"
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "NOVA_CAPABILITY_MANIFESTS_LATEST.json"
    md_path = out_dir / "NOVA_CAPABILITY_MANIFESTS_LATEST.md"
    atomic_write_json(json_path, payload)
    atomic_write_text(md_path, render_manifest_catalog(goal))
    return {"markdown_path": str(md_path), "json_path": str(json_path), **payload}
