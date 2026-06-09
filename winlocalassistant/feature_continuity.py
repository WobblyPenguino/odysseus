from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import json
import re
from typing import Any


CRITICAL_WEBUI_MARKERS = {
    "chat_input": ["id=\"msg\"", "send()"],
    "project_panel": ["id=\"projects\"", "loadProjects", "bulkDeleteSelectedProjects"],
    "toolbox": ["id=\"customTools\"", "loadTools", "createTool", "runToolForm"],
    "live_activity_runs": ["id=\"activityLog\"", "deleteSelectedRuns", "runSelect"],
    "assistant_box": ["loadAssistantBox", "synthAssistantBox", "clearAssistantBox"],
    "audio_guard": ["avatarAudioActivated=false", "!avatarAudioActivated"],
    "inspector": ["inspectorTabs", "openFile", "saveOpenFile"],
    "settings_popup": ["settingsPanel", "toggleSettingsPanel"],
    "validation_matrix": ["validation-matrix", "adaptive-backlog"],
    "role_router": ["role-router"],
    "jarvis_bridge": ["jarvis-bridge", "jarvis-doctor", "sidecar-preflight", "sidecar-policy", "Workflow blueprint", "Jarvis bridge"],
    "left_action_cockpit": ["leftActionDock", "leftFileDock", "Action dock", "Transparent output"],
    "transparent_output": ["transparentOutputPanel", "transparentDiffPanel", "renderTransparentOutputEvidence", "Before / after diff"],
    "jarvis_ui_harness": ["sidecar-enrollment", "bridge-receipts", "browser-harness", "jarvis-test-prompts"],
    "hey_nova_voice": ["wakeWordEnabled", "toggleWakeWordListening", "Hey Nova", "voiceCommandToAction"],
    "per_chat_mute": ["toggleCurrentChatMute", "wlaMutedChatSessions", "chatMuteBtn", "toggleGlobalAudio"],
    "conversational_speech": ["conversationalVoiceSummary", "I have code output ready in the chat", "Done. The checks passed"],
    "persona_editor": ["personaMiniPanel", "personaCommandPreview", "custom-chat-window", "persona-set", "Nova persona sliders"],
    "local_model_optimizer": ["local-model-optimizer", "agent-harness", "voice-audit", "Model optimiser"],
    "startup_validation_and_audit": ["startup-validation", "audit-log", "workflow-run", "Startup Validation"],
    "unified_voice_ux": ["novaOrbPanel", "voiceWaveCanvas", "rightVoiceWaveCanvas", "Always-listening", "edgeRailToggle"],
    "autonomous_cockpit_reasoning": ["autonomousCockpit", "autoThoughtNow", "Scrollable reasoning timeline", "current_thought", "self_validation", "autonomousThoughtRows"],
    "voice_reliability_auth": ["voiceAuthPanel", "voiceScreenTranscript", "collapseRepeatedTranscript", "issueVoiceToChat", "Test AI voice", "wlaAutoIdleExplicitOptIn"],
    "voice_profile_lock_pipeline": ["communicationCentreBoard", "voiceGuardCard", "startVoiceProfileEnrollment", "voiceTestingBypassActive", "findWakeMatch", "startPostWakeCommandCapture", "session-isolated"],
    "wake_handoff_desktop_launcher": ["wakeRestartPausedForCommand", "finishPostWakeCapture", "restartWakeAfterCommand", "hidden-panel layout reclaim", "Wake accepted. Listening for your request"],
    "nova_full_system_test": ["nova-system-test", "Nova full system test", "nova_system_test"],
    "codebase_packaging_advisor": ["release-package", "codebase-advisor", "Release package", "Codebase advisor"],
    "completion_audit": ["completion-audit", "Completion audit", "completion_audit"],
}

CRITICAL_TOOL_NAMES = {
    "projects",
    "project_open",
    "project_delete",
    "custom_tools",
    "tool_create",
    "tool_run",
    "tool_test",
    "activity_log",
    "llm_status",
    "codebase_integrity_audit",
    "implement_improvements",
    "model_context",
    "docker_validate",
    "sandbox_status",
    "runtime_self_check",
    "nova_context",
    "idle_policy",
    "receipt_history",
    "validation_matrix",
    "adaptive_backlog",
    "role_router",
    "local_model_roles",
    "jarvis_bridge",
    "jarvis_status",
    "jarvis_doctor",
    "sidecar_policy",
    "sidecar_preflight",
    "bridge_authority",
    "workflow_blueprint",
    "proactive_actions",
    "bridge_receipts",
    "sidecar_enrollment",
    "browser_harness",
    "jarvis_test_prompts",
    "persona_profile",
    "persona_set",
    "persona_prompt",
    "custom_chat_window",
    "voice_audit",
    "local_model_optimizer",
    "agent_harness",
    "startup_validation",
    "audit_log",
    "workflow_run",
}


@dataclass
class ContinuityCheck:
    name: str
    ok: bool
    detail: str
    missing: list[str]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def build_feature_continuity_audit(root: str | Path, tool_names: list[str] | None = None) -> dict[str, Any]:
    """Check that previously-added Nova capability surfaces are still present.

    This is intentionally conservative: it does not prove every feature works end-to-end,
    but it catches accidental GUI rewrites, missing JS functions, removed command tools,
    and user-visible version drift before release packaging.
    """
    root = Path(root).expanduser().resolve()
    webui = _read(root / "winlocalassistant" / "webui.py")
    init_text = _read(root / "winlocalassistant" / "__init__.py")
    registered = set(tool_names or [])
    checks: list[ContinuityCheck] = []

    for name, markers in CRITICAL_WEBUI_MARKERS.items():
        missing = [marker for marker in markers if marker not in webui]
        checks.append(ContinuityCheck(
            name=f"webui:{name}",
            ok=not missing,
            detail="required browser/UI markers are present" if not missing else "missing required browser/UI markers",
            missing=missing,
        ))

    if registered:
        missing_tools = sorted(CRITICAL_TOOL_NAMES - registered)
        checks.append(ContinuityCheck(
            name="tool_registry:critical_commands",
            ok=not missing_tools,
            detail="critical backend tools are registered" if not missing_tools else "critical backend tools disappeared from registry",
            missing=missing_tools,
        ))

    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    expected_version = version_match.group(1) if version_match else ""
    version_ok = bool(expected_version and expected_version in init_text and expected_version in webui)
    checks.append(ContinuityCheck(
        name="version:visible_consistency",
        ok=version_ok,
        detail="version appears in package and GUI" if version_ok else "version marker is not visible in both package and GUI",
        missing=[] if version_ok else [f"{expected_version or 'current version'} in __init__.py and webui.py"],
    ))

    failed = [asdict(check) for check in checks if not check.ok]
    return {
        "ok": not failed,
        "root": str(root),
        "checks": [asdict(check) for check in checks],
        "failed": failed,
        "summary": "Feature continuity audit passed" if not failed else f"Feature continuity audit found {len(failed)} regression risk(s)",
        "guidance": [
            "Do not remove existing GUI/backend surfaces to make a redesign cleaner; hide, group, or improve them instead.",
            "When rewriting webui.py, keep compatibility wrappers for existing JS entry points and tests.",
            "Treat missing custom-tool, project, activity, assistant-box, audio, role-router, Jarvis-bridge/sidecar-policy, Hey Nova voice activation, per-chat mute, persona/custom-chat-window, local-model optimizer, voice-audit, startup-validation, audit-log, workflow-run, and implementation-pipeline markers as release blockers.",
        ],
    }


def render_feature_continuity_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Feature Continuity Audit", "", payload.get("summary", ""), ""]
    lines.append(f"Root: `{payload.get('root','')}`")
    lines.append("")
    lines.append("## Checks")
    for check in payload.get("checks", []):
        mark = "✅" if check.get("ok") else "❌"
        lines.append(f"- {mark} **{check.get('name')}** — {check.get('detail')}")
        if check.get("missing"):
            lines.append("  - Missing: " + ", ".join(f"`{m}`" for m in check.get("missing", [])))
    lines.append("")
    lines.append("## Guidance")
    for item in payload.get("guidance", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"
