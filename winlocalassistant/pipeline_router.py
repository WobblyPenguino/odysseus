from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_text, read_json_file


@dataclass(frozen=True)
class PipelineStage:
    name: str
    tool: str
    reason: str
    validates: str
    mutates: bool = False


@dataclass(frozen=True)
class PipelineRoute:
    kind: str
    title: str
    confidence: float
    reason: str
    stages: tuple[PipelineStage, ...]
    warnings: tuple[str, ...] = ()


STATUS_PIPELINE = PipelineRoute(
    kind="status",
    title="Status / explanation pipeline",
    confidence=0.72,
    reason="The request is best answered by deterministic state inspection before any model or file mutation.",
    stages=(
        PipelineStage("Inspect runtime status", "status", "Show workspace, model and safety configuration.", "Returns non-empty status text."),
        PipelineStage("Inspect recent activity", "activity_log", "Find recent failures or blocked steps.", "Activity log is readable."),
    ),
)

PIPELINES: dict[str, PipelineRoute] = {
    "repo_upgrade": PipelineRoute(
        kind="repo_upgrade",
        title="Repo-inspired capability upgrade pipeline",
        confidence=0.88,
        reason="The request references external repo ideas or integrations; select capability manifests and evidence checks before any coding model edit.",
        stages=(
            PipelineStage("Select capability manifests", "pipeline_catalog", "Map repo ideas to Nova-owned contracts before implementation.", "Relevant manifests are rendered."),
            PipelineStage("Inspect project patterns", "project_patterns", "Keep upgrades compatible with the current codebase shape.", "Pattern report is available."),
            PipelineStage("Collect session evidence", "session_evidence", "Review recent failures before proposing more changes.", "Recent evidence is summarized."),
            PipelineStage("Run browser smoke", "browser_smoke", "Catch GUI/runtime marker issues early.", "Browser smoke passes."),
            PipelineStage("Run bug review", "bug_review", "Look for high-risk regressions before packaging.", "No high severity issue remains."),
            PipelineStage("Run regression sweep", "regression_sweep", "Verify preserved functionality.", "Sweep returns ok."),
        ),
    ),
    "project_review": PipelineRoute(
        kind="project_review",
        title="Project library review pipeline",
        confidence=0.9,
        reason="The request mentions existing projects; creating a new app would be off-task.",
        stages=(
            PipelineStage("List registered projects", "projects", "Know what projects exist before judging them.", "Project registry can be read."),
            PipelineStage("Inspect project evidence", "investigate_logs", "Use recent run logs instead of guessing.", "Recent activity is summarized."),
            PipelineStage("Run regression sweep", "regression_sweep", "Check no-regression health before edits.", "Sweep returns pass/fail evidence."),
            PipelineStage("Run bug review", "bug_review", "Find code-flow and UX issues before proposals.", "Bug review returns no critical unhandled error."),
        ),
    ),
    "database_review": PipelineRoute(
        kind="database_review",
        title="Database/state integrity pipeline",
        confidence=0.9,
        reason="The request references database/state; use integrity audits and compactable maintenance, not app generation.",
        stages=(
            PipelineStage("Audit assistant DB", "assistant_db", "Check SQLite integrity and stored record quality.", "Integrity check is ok."),
            PipelineStage("Audit project state", "project_state", "Check project-state JSON safety and retention.", "State audit returns readable findings."),
            PipelineStage("Run bug review", "bug_review", "Catch data-flow issues before rewrite.", "No high severity issue remains."),
            PipelineStage("Run regression sweep", "regression_sweep", "Verify existing functionality remains present.", "Sweep returns ok."),
        ),
    ),
    "qa": PipelineRoute(
        kind="qa",
        title="Functionality QA pipeline",
        confidence=0.88,
        reason="The request asks to test/verify functionality, so deterministic QA tools should run before any build/edit loop.",
        stages=(
            PipelineStage("Run user-flow QA", "user_test_suite", "Exercise common workflows.", "QA report is generated."),
            PipelineStage("Run regression sweep", "regression_sweep", "Guard against feature loss.", "Sweep returns ok."),
            PipelineStage("Run Doctor", "nova_doctor", "Check release/runtime health.", "Doctor has no critical failures."),
            PipelineStage("Run command contracts", "command_verifier", "Verify important commands still work.", "Contracts pass."),
        ),
    ),
    "gui": PipelineRoute(
        kind="gui",
        title="GUI/browser smoke pipeline",
        confidence=0.84,
        reason="The request targets UI/GUI/browser layout; verify static JS and browser-ready markers before claiming a visual fix.",
        stages=(
            PipelineStage("Parse Web UI JavaScript", "browser_smoke", "Catch missing functions and syntax errors before launch.", "JS parse/checks pass."),
            PipelineStage("Run GUI regression sweep", "regression_sweep", "Ensure new layout did not drop features.", "GUI-related sweep returns ok."),
            PipelineStage("Run bug review", "bug_review", "Look for layout/routing regressions.", "No high severity issue remains."),
        ),
    ),

    "remote_access": PipelineRoute(
        kind="remote_access",
        title="Remote access / Wake-on-LAN setup pipeline",
        confidence=0.86,
        reason="The request targets phone/laptop remote access, Tailscale, Nova API health or Wake-on-LAN; use safe preflight and dry-run checks before any mutating action.",
        stages=(
            PipelineStage("Run remote preflight", "remote_access_test", "Check local prerequisites and separate code-verifiable items from manual BIOS/NIC checks.", "Preflight reports pass/warn/manual without changing state."),
            PipelineStage("Validate remote profile", "remote_profile_validate", "Use saved host/port/MAC details instead of repeated risky typing.", "Profile exists and does not store raw tokens."),
            PipelineStage("Probe API health", "remote_api_health", "Confirm localhost/LAN/Tailscale API reachability before relying on a phone/laptop workflow.", "Health probe reports auth/connectivity details."),
            PipelineStage("Dry-run Wake-on-LAN", "remote_wake", "Build and validate the magic packet without waking hardware until confirmed.", "Dry-run packet is valid and user confirmation is required for real send."),
        ),
    ),
    "media": PipelineRoute(
        kind="media",
        title="Image/video media planning pipeline",
        confidence=0.85,
        reason="The request asks for image/video/storyboard/media generation; check backend readiness and produce manifests before heavy rendering.",
        stages=(
            PipelineStage("Check media status", "media_status", "Know whether SD WebUI, Diffusers, ComfyUI, ffmpeg and Node are ready.", "Status distinguishes unavailable, simulated and real backends."),
            PipelineStage("Plan image prompts", "image_plan", "Create prompt variants before expensive generation.", "Prompt plan renders seeds/variants and negative prompts."),
            PipelineStage("Build video storyboard/package", "video_package", "Create storyboard/manifest/preview files before rendering.", "Package manifest is written and file paths are reported.", True),
            PipelineStage("Validate video stack", "video_status", "Confirm render backend state honestly after packaging.", "Video stack status is readable."),
        ),
    ),
    "voice": PipelineRoute(
        kind="voice",
        title="Voice state-machine pipeline",
        confidence=0.84,
        reason="The request targets wake/listen/speak flow; use voice review and live-state checks before changing code.",
        stages=(
            PipelineStage("Review voice pipeline", "voice_pipeline_review", "Check wake, ready cue, recording, thinking and speaking handoff.", "Voice pipeline contract is described."),
            PipelineStage("Inspect activity", "activity_log", "Find wake/listening errors and redundant transcript events.", "Recent voice events are readable."),
            PipelineStage("Run bug review", "bug_review", "Catch stale JS/state errors.", "No high severity issue remains."),
        ),
    ),
    "coding": PipelineRoute(
        kind="coding",
        title="Verified coding pipeline",
        confidence=0.86,
        reason="The request asks for code creation or repair; load patterns, preflight, patch, validate, then package.",
        stages=(
            PipelineStage("Load project patterns", "project_patterns", "Use existing runtime/style rules before writing.", "Pattern report is available."),
            PipelineStage("Plan coding execution", "coding_plan", "Choose the right runtime and files.", "Plan names entrypoint and verifier."),
            PipelineStage("Build/edit project", "ai_create_project", "Generate only after route and pattern checks.", "Files are written and accepted.", True),
            PipelineStage("Verify project", "auto_verify", "Run the smallest relevant verification.", "Verification passes."),
            PipelineStage("Final acceptance check", "final_project_check", "Compare output against the user goal.", "Acceptance passes."),
        ),
    ),
    "autonomous": PipelineRoute(
        kind="autonomous",
        title="Autonomous bounded cycle pipeline",
        confidence=0.82,
        reason="The request asks Nova to keep working safely; autonomous steps must be observable, bounded and verified.",
        stages=(
            PipelineStage("Resolve target", "detect_project", "Know whether Nova is improving itself or a user project.", "Target is explicit."),
            PipelineStage("Observe health", "runtime_self_check", "Avoid acting while core health is degraded.", "Self-check succeeds or records failure."),
            PipelineStage("Investigate logs", "investigate_logs", "Use fresh evidence for the next action.", "Evidence summary is recorded."),
            PipelineStage("Propose improvements", "propose_improvements", "Create small candidate changes before applying.", "Proposal exists."),
            PipelineStage("Validate candidate", "auto_verify", "No change is promoted without checks.", "Verification result is recorded."),
        ),
    ),
}


def _clean_goal(goal: str) -> str:
    return re.sub(r"\s+", " ", (goal or "").strip())


def classify_pipeline(goal: str) -> PipelineRoute:
    g = _clean_goal(goal).lower()
    if not g:
        return STATUS_PIPELINE
    if any(x in g for x in ["repo", "repos", "github", "openmontage", "openhands", "open hands", "browser-use", "mem0", "tabby", "livekit", "odysseus"]):
        if any(x in g for x in ["integrat", "ideas", "capabil", "upgrade", "continue", "improv", "fix", "errors"]):
            return PIPELINES["repo_upgrade"]
    if any(x in g for x in ["all our projects", "all my projects", "our projects", "my projects", "project library", "look at all projects"]):
        return PIPELINES["project_review"]
    if any(x in g for x in ["database", "datastore", "data store", "project state", "sqlite", "records"]):
        if any(x in g for x in ["review", "audit", "look", "improv", "rewrite", "sanity", "regression", "entire"]):
            return PIPELINES["database_review"]
    if any(x in g for x in ["test each", "each individual functionality", "test all", "all functionality", "no regression", "validate results", "verify results", "ensure it works"]):
        return PIPELINES["qa"]
    if any(x in g for x in ["remote", "phone", "laptop", "tailscale", "wake-on-lan", "wake on lan", "wol", "rdp", "remote desktop", "nova api"]):
        return PIPELINES["remote_access"]
    if any(x in g for x in ["video", "image", "media", "storyboard", "trailer", "comfyui", "sd webui", "diffusers", "ffmpeg"]):
        return PIPELINES["media"]
    if any(x in g for x in ["gui", "layout", "browser", "panel", "drawer", "chat popup", "live activity", "css", "visual"]) or re.search(r"\bui\b", g):
        return PIPELINES["gui"]
    if any(x in g for x in ["voice", "hey nova", "wake", "listening", "speak", "tts", "ready sound", "microphone", "mic"]):
        return PIPELINES["voice"]
    if any(x in g for x in ["autonomous", "idle", "keep running", "safe cycle", "bounded cycle"]):
        return PIPELINES["autonomous"]
    if any(x in g for x in ["make", "build", "create", "write", "script", "program", "app", "game", "implement", "patch", "fix"]):
        return PIPELINES["coding"]
    return STATUS_PIPELINE


def route_to_dict(route: PipelineRoute) -> dict[str, Any]:
    return {
        "kind": route.kind,
        "title": route.title,
        "confidence": route.confidence,
        "reason": route.reason,
        "warnings": list(route.warnings),
        "stages": [asdict(stage) for stage in route.stages],
    }


def render_pipeline_route(route: PipelineRoute, goal: str = "") -> str:
    lines = [
        "# Nova Pipeline Preflight",
        "",
        f"Goal: {goal or '(none supplied)'}",
        f"Selected pipeline: **{route.title}** (`{route.kind}`)",
        f"Confidence: {route.confidence:.0%}",
        f"Reason: {route.reason}",
        "",
        "## Stages",
    ]
    for i, stage in enumerate(route.stages, 1):
        mut = "writes possible" if stage.mutates else "read-only/status"
        lines.append(f"{i}. **{stage.name}** — `{stage.tool}` ({mut})")
        lines.append(f"   - Why: {stage.reason}")
        lines.append(f"   - Validates: {stage.validates}")
    if route.warnings:
        lines += ["", "## Warnings"] + [f"- {w}" for w in route.warnings]
    lines += [
        "",
        "## Guardrail",
        "Nova should show this route before expensive model prompts or mutation when the user request is broad or ambiguous.",
    ]
    return "\n".join(lines)


def write_project_patterns(workspace: Path, *, write: bool = False) -> dict[str, Any]:
    root = Path(workspace).expanduser().resolve()
    files = [p for p in root.rglob("*") if p.is_file() and not any(part in {".git", "__pycache__", ".pytest_cache", ".nova_runtime"} for part in p.parts)] if root.exists() else []
    suffix_counts: dict[str, int] = {}
    for p in files[:2000]:
        suffix_counts[p.suffix.lower() or "(none)"] = suffix_counts.get(p.suffix.lower() or "(none)", 0) + 1
    has = lambda name: (root / name).exists()
    runtime = "generic"
    verifiers: list[str] = []
    if has("pyproject.toml") or any(p.suffix == ".py" for p in files[:500]):
        runtime = "python"
        verifiers.append("python -m compileall -q .")
    if has("package.json") or any(p.suffix == ".js" for p in files[:500]):
        runtime = "node/browser"
        verifiers.append("node --check app.js if app.js exists")
    if has("index.html"):
        runtime = "browser"
        verifiers.append("open index.html or run browser-smoke checks")
    if has("PROJECT_MANIFEST.json"):
        verifiers.append("python app.py /project-state audit if this is a Nova project")
    if not verifiers:
        verifiers.append("run the smallest available syntax/runtime check")
    patterns = {
        "workspace": str(root),
        "runtime": runtime,
        "file_count": len(files),
        "suffix_counts": dict(sorted(suffix_counts.items(), key=lambda kv: (-kv[1], kv[0]))[:20]),
        "entrypoints": [name for name in ["app.py", "main.py", "index.html", "package.json", "PROJECT_MANIFEST.json", "README.md"] if has(name)],
        "preferred_verifiers": verifiers,
        "rules": [
            "Load this file before editing so generated code follows the current project shape.",
            "Prefer targeted edits over unrelated new projects.",
            "Record commands run and validation evidence in the activity timeline.",
            "Do not claim success unless a verifier or deterministic check passed.",
        ],
        "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if write:
        lines = [
            "# NOVA_PATTERNS",
            "",
            f"Workspace: `{patterns['workspace']}`",
            f"Detected runtime: **{patterns['runtime']}**",
            "",
            "## Entrypoints",
        ]
        lines += [f"- `{x}`" for x in patterns["entrypoints"]] or ["- No obvious entrypoint found yet."]
        lines += ["", "## Preferred verification commands"]
        lines += [f"- `{x}`" for x in patterns["preferred_verifiers"]]
        lines += ["", "## Editing rules"]
        lines += [f"- {x}" for x in patterns["rules"]]
        lines += ["", "## File-type counts", "```json", json.dumps(patterns["suffix_counts"], indent=2), "```", ""]
        atomic_write_text(root / "NOVA_PATTERNS.md", "\n".join(lines))
        patterns["written"] = str(root / "NOVA_PATTERNS.md")
    return patterns


def render_project_patterns(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Project Patterns",
        "",
        f"Workspace: `{payload.get('workspace','')}`",
        f"Detected runtime: **{payload.get('runtime','generic')}**",
        f"Files scanned: {payload.get('file_count', 0)}",
        "",
        "## Entrypoints",
    ]
    lines += [f"- `{x}`" for x in payload.get("entrypoints") or []] or ["- No obvious entrypoint found."]
    lines += ["", "## Preferred verifiers"]
    lines += [f"- `{x}`" for x in payload.get("preferred_verifiers") or []]
    lines += ["", "## Rules"] + [f"- {x}" for x in payload.get("rules") or []]
    if payload.get("written"):
        lines += ["", f"Written: `{payload['written']}`"]
    return "\n".join(lines)
