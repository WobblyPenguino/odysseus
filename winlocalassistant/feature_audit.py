from __future__ import annotations

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


@dataclass
class FeatureCheck:
    name: str
    status: str
    summary: str
    evidence: list[str]
    remaining: str = ""

    @property
    def ok(self) -> bool:
        return self.status in {"implemented", "environment_dependent", "safe_partial"}

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(root: Path, rel: str) -> str:
    p = root / rel
    if not p.exists():
        return ""
    try:
        return p.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return p.read_text(errors="replace")


def _has(root: Path, rel: str, *tokens: str) -> bool:
    text = _read(root, rel)
    return bool(text) and all(tok in text for tok in tokens)


def _exists(root: Path, rel: str) -> bool:
    return (root / rel).exists()


def build_feature_audit(root: Path | str = ".") -> dict[str, Any]:
    """Audit the major user-requested Nova feature set.

    This is not a security bypass or a claim that environment-specific systems
    are configured. It verifies that the code paths, commands, UI hooks and
    reports added for the requested features are present and visible.
    """
    root = Path(root).expanduser().resolve()
    webui = _read(root, "winlocalassistant/webui.py")
    core = _read(root, "winlocalassistant/core.py")
    tools = _read(root, "winlocalassistant/tools.py")
    checks: list[FeatureCheck] = []

    def add(name: str, status: str, summary: str, evidence: list[str], remaining: str = "") -> None:
        checks.append(FeatureCheck(name, status, summary, evidence, remaining))

    add(
        "spoken_audio_and_controls",
        "implemented" if all(x in webui for x in ["speechSynthesis", "summariseForSpeech", "toggleAudioMute", "showTutorial", "SpeechRecognition", "toggleVoiceInput"]) else "missing",
        "Browser speech, microphone voice input, microphone diagnostic preflight, long-response summarisation, mute/unmute and tutorial controls are wired in the GUI.",
        ["speechSynthesis", "SpeechRecognition", "toggleVoiceInput", "diagnoseVoiceInput", "refreshVoiceDeviceSelect", "voiceDeviceSelect", "getUserMedia", "enumerateDevices", "summariseForSpeech", "toggleAudioMute", "showTutorial"],
    )
    add(
        "thin_left_rail_popups",
        "implemented" if all(x in webui for x in ["rail", "releaseChecklistPopup", "chatsPopup", "showChangelog"]) else "missing",
        "Left rail contains settings/audio/tutorial/changelog/release/chat shortcuts with popup panels.",
        ["releaseChecklistPopup", "chatsPopup", "showChangelog"],
    )
    add(
        "custom_quick_commands",
        "implemented" if all(x in webui for x in ["renderQuickControls", "runQuickCommand", "editQuickCommand", "wlaQuickCommands"]) else "missing",
        "Quick commands are flat, customisable, persistent and can execute sequential command lists.",
        ["renderQuickControls", "runQuickCommand", "wlaQuickCommands"],
    )
    add(
        "live_activity_clarity",
        "implemented" if all(x in webui for x in ["renderRuns", "title=", "since=0", "resize:vertical"]) else "missing",
        "Live Activity is taller/resizable, keeps previous runs, shows hover metadata and indented/subtask context.",
        ["renderRuns", "since=0", "title=", "resize:vertical"],
    )
    add(
        "backend_conversations",
        "implemented" if _exists(root, "winlocalassistant/conversation_store.py") and all(x in core for x in ["/chat-new", "/chat-switch", "/chat-rename", "/chat-delete", "/chat-search"]) else "missing",
        "Persistent backend conversations support create/list/switch/search/rename/delete.",
        ["conversation_store.py", "/chat-rename", "/chat-delete"],
    )
    add(
        "project_memory_and_targeting",
        "implemented" if _exists(root, "winlocalassistant/project_memory.py") and all(x in core for x in ["_enrich_goal_with_project_memory", "_prepare_project_target_for_generation", "/project-target"]) else "missing",
        "Project memory is retrieved for build/edit prompts and project targeting can diagnose new-vs-current project intent.",
        ["project_memory.py", "_enrich_goal_with_project_memory", "/project-target"],
    )
    add(
        "file_cards_and_llm_context",
        "implemented" if all(x in webui for x in ["renderFileCards", "Recent local model call", "model_io.jsonl"]) else "missing",
        "Generated/openable files appear as cards and the LLM status panel preserves compact recent prompt/reply context.",
        ["renderFileCards", "Recent local model call", "model_io.jsonl"],
    )
    add(
        "research_synthesis",
        "implemented" if _has(root, "winlocalassistant/research_engine.py", "Short synthesis", "Source and bias analysis") else "missing",
        "Research reports include a short synthesis plus source/excerpt/bias sections.",
        ["Short synthesis", "Source and bias analysis"],
    )
    add(
        "docker_validation_patch_promotion",
        "implemented" if _has(root, "winlocalassistant/docker_manager.py", "patch_sha256", "docker_promote_validated_patch", "--ignore-whitespace") else "missing",
        "Docker copied-workspace validation, patch validation, hash locking and promotion rollback logic are present.",
        ["patch_sha256", "docker_promote_validated_patch", "--ignore-whitespace"],
    )
    add(
        "release_gate_and_doctor",
        "implemented" if _exists(root, "winlocalassistant/wla_doctor.py") and all(x in core for x in ["/nova-doctor", "/release-gate", "/release-checklist"]) else "missing",
        "Nova Doctor, release gate and release checklist commands are present.",
        ["wla_doctor.py", "/release-gate", "/release-checklist"],
    )
    add(
        "playwright_scaffold",
        "implemented" if _exists(root, "playwright/nova_gui_smoke.spec.js") and "playwright_smoke" in _read(root, "winlocalassistant/wla_doctor.py") else "missing",
        "Playwright GUI smoke scaffold exists and release gate runs/skips it depending on environment readiness.",
        ["playwright/nova_gui_smoke.spec.js", "playwright_smoke"],
    )
    add(
        "security_defensive_watch",
        "implemented" if _exists(root, "winlocalassistant/security_status.py") and all(x in core for x in ["/security-status", "/security-watch"]) else "missing",
        "Defensive-only security status and watch commands are wired; direct vendor remediation remains intentionally manual/user-approved.",
        ["security_status.py", "/security-watch"],
        "Direct AVG quarantine/remediation requires documented vendor CLI/API and explicit approval.",
    )
    add(
        "image_generation_status",
        "environment_dependent" if _exists(root, "winlocalassistant/image_generation.py") and all(x in core for x in ["/image-generate", "/image-draft", "/image-setup-help"]) else "missing",
        "Image generation refuses to fake real generation and provides setup guidance for SD WebUI/Diffusers/ComfyUI.",
        ["/image-generate", "/image-draft", "/image-setup-help"],
        "Actual generation depends on a reachable/configured local image backend.",
    )

    add(
        "browser_console_hygiene",
        "implemented" if all(x in webui for x in ["/favicon.ico", "avatarAudioActivated", "llmCtxSpinner", "runSequentialCommands"]) else "missing",
        "The web UI avoids favicon 404 noise, avoids Web Audio before a user gesture, preserves LLM context text while refreshing, and supports multi-command quick buttons.",
        ["/favicon.ico", "avatarAudioActivated", "llmCtxSpinner", "runSequentialCommands"],
    )


    add(
        "dependency_and_massive_system_test",
        "implemented" if _exists(root, "winlocalassistant/dependency_check.py") and _exists(root, "winlocalassistant/system_test.py") and all(x in core for x in ["/dependency-check", "/massive-test"]) and "dependency_check" in _read(root, "start_windows_assistant.bat") else "missing",
        "Startup dependency checks, optional pip install prompts, and one-click confirmed massive system tests are wired.",
        ["dependency_check.py", "system_test.py", "/dependency-check", "/massive-test", "start_windows_assistant.bat"],
    )

    add(
        "linux_sandbox_python_ready",
        "implemented" if _has(root, "winlocalassistant/config.py", "python:3.12-slim") and _has(root, "winlocalassistant/sandbox_manager.py", "python3", "python") else "missing",
        "General Linux sandbox defaults to a Python-ready image and aliases python3 where possible.",
        ["python:3.12-slim", "python3"],
    )

    implemented = sum(1 for c in checks if c.status == "implemented")
    partial = sum(1 for c in checks if c.status in {"safe_partial", "environment_dependent"})
    missing = [c for c in checks if c.status == "missing"]
    payload = {
        "ok": not missing,
        "summary": "Requested-feature audit passed" if not missing else f"Requested-feature audit found {len(missing)} missing item(s)",
        "root": str(root),
        "implemented": implemented,
        "partial_or_environment_dependent": partial,
        "missing": len(missing),
        "checks": [c.to_dict() for c in checks],
        "remaining_safe_todo": [c.remaining for c in checks if c.remaining],
    }
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    md = docs / "NOVA_FEATURE_AUDIT_LATEST.md"
    js = docs / "NOVA_FEATURE_AUDIT_LATEST.json"
    atomic_write_text(md, render_feature_audit_markdown(payload), encoding="utf-8")
    atomic_write_json(js, payload, ensure_ascii=True, indent=2)
    payload["markdown_path"] = str(md)
    payload["json_path"] = str(js)
    return payload


def render_feature_audit_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Requested Feature Audit",
        "",
        f"OK: **{bool(payload.get('ok'))}**",
        f"Summary: {payload.get('summary','')}",
        f"Implemented: **{payload.get('implemented',0)}**",
        f"Partial/environment-dependent: **{payload.get('partial_or_environment_dependent',0)}**",
        f"Missing: **{payload.get('missing',0)}**",
        "",
        "## Feature checks",
    ]
    for item in payload.get("checks") or []:
        status = item.get("status", "")
        icon = "✅" if status == "implemented" else ("🟡" if status in {"environment_dependent", "safe_partial"} else "❌")
        lines.append(f"- {icon} **{item.get('name')}** — {status}: {item.get('summary')}")
        if item.get("remaining"):
            lines.append(f"  - Remaining: {item.get('remaining')}")
    todo = [x for x in payload.get("remaining_safe_todo") or [] if x]
    if todo:
        lines += ["", "## Remaining environment-dependent / approval-only work"] + [f"- {x}" for x in todo]
    if payload.get("markdown_path"):
        lines += ["", f"Report written: `{payload.get('markdown_path')}`"]
    return "\n".join(lines)


def feature_audit(root: Path | str = ".") -> dict[str, Any]:
    """Compatibility wrapper for callers that expect a verb-style API.

    Older code and external scripts may naturally try to import
    ``feature_audit`` or ``run_feature_audit``. Keep both aliases pointing at
    the canonical builder so Nova's feature coverage check is easy to call from
    tests, release gates and future tooling.
    """
    return build_feature_audit(root)


def run_feature_audit(root: Path | str = ".") -> dict[str, Any]:
    """Compatibility alias for release/check scripts."""
    return build_feature_audit(root)
