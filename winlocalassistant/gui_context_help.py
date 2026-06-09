from __future__ import annotations

"""Contextual GUI help for Nova.

This module is deliberately small and deterministic.  The browser overlay sends
only a short description of the clicked element; this renderer turns it into
honest, command-oriented help and optional next commands.  It does not execute
mutating commands on its own.
"""

import json
import re
from dataclasses import dataclass
from typing import Any
from urllib.parse import unquote_plus


@dataclass(frozen=True)
class GuiHelpTopic:
    key: str
    matches: tuple[str, ...]
    title: str
    purpose: str
    common_commands: tuple[str, ...]
    safe_next_steps: tuple[str, ...]


_TOPICS: tuple[GuiHelpTopic, ...] = (
    GuiHelpTopic(
        key="chat",
        matches=("chat", "composer", "send", "ask nova", "message", "input"),
        title="Chat composer and conversation",
        purpose="Type normal prompts or slash commands. Use it for planning, code help, validation checks, and GUI recovery commands.",
        common_commands=("/help", "/tool-use-plan YOUR_GOAL", "/pipeline-route YOUR_GOAL", "/role-router YOUR_GOAL"),
        safe_next_steps=("Ask Nova to plan before mutating files.", "Use /validation-status after changes.", "Attach files only when they are relevant."),
    ),
    GuiHelpTopic(
        key="files",
        matches=("file", "project files", "download", "zip", "open"),
        title="Project files drawer",
        purpose="Browse, open, download, and package project files from the current workspace.",
        common_commands=("/files", "/tree", "/read PATH", "/zip PATH", "/download PATH"),
        safe_next_steps=("Use /project-files to confirm workspace scope.", "Avoid setting the workspace to your whole user folder.", "Use /patch-impact-plan after editing files."),
    ),
    GuiHelpTopic(
        key="commands",
        matches=("command", "search", "route", "routes", "help"),
        title="Commands and route discovery",
        purpose="Find available Nova commands and check whether the visible GUI is connected to the correct backend routes.",
        common_commands=("/help", "/command-catalog", "/tool-health-map", "/gui-layout-status", "/build-info"),
        safe_next_steps=("Click routes if a button appears stale.", "Run /build-info to confirm the patch folder.", "Use /explain-command COMMAND for command-specific help."),
    ),
    GuiHelpTopic(
        key="gui",
        matches=("gui", "layout", "drawer", "panel", "reset ui", "focus", "left rail", "right drawer", "visual"),
        title="GUI layout and visual recovery",
        purpose="Diagnose drawer overlap, stale browser state, clipped panels, and backend/frontend route mismatch.",
        common_commands=("/gui-layout-status", "/gui-reset-help", "/build-info", "/gui-visual-test", "/pipeline-route fix GUI layout"),
        safe_next_steps=("Click reset UI, then layout.", "Use Ctrl+Shift+R after extracting a new patch.", "Upload a screenshot if the layout diagnostic reports warnings."),
    ),
    GuiHelpTopic(
        key="media",
        matches=("image", "video", "media", "comfyui", "ffmpeg", "storyboard", "generate"),
        title="Image/video/media workflow",
        purpose="Plan image prompts, create video manifests/storyboards, and report whether real render backends are available.",
        common_commands=("/media-status", "/image-status", "/image-plan PROMPT", "/video-status", "/video-package PROMPT"),
        safe_next_steps=("Use /media-status before expecting real renders.", "If ComfyUI/ffmpeg are missing, Nova can still create plans and manifests.", "Do not claim real generation worked unless a backend produced a file."),
    ),
    GuiHelpTopic(
        key="remote",
        matches=("remote", "tailscale", "wake", "wol", "phone", "laptop", "api", "token"),
        title="Remote PC/Nova access",
        purpose="Set up safe private access through Tailscale/local network, test Nova API health, and dry-run Wake-on-LAN.",
        common_commands=("/remote-access-test", "/remote-access-scripts", "/remote-api-health HOST 8767 --dry-run", "/remote-profile list", "/remote-wake MAC --dry-run"),
        safe_next_steps=("Do not port-forward Nova or RDP publicly.", "Keep raw tokens in environment variables, not profiles.", "Use --dry-run before real Wake-on-LAN."),
    ),
    GuiHelpTopic(
        key="validation",
        matches=("validation", "test", "pytest", "smoke", "build", "pass", "fail"),
        title="Validation and regression safety",
        purpose="Run compile, smoke, targeted, and chunked full validation so fixes are verified instead of guessed.",
        common_commands=("/validation-status", "/maintenance-validate", "python -m pytest -q tests_smoke.py", "python -m winlocalassistant.validate --all"),
        safe_next_steps=("Run changed-file tests first.", "Use chunked full validation for large suites.", "Investigate failures instead of weakening tests."),
    ),
    GuiHelpTopic(
        key="model",
        matches=("model", "provider", "queue", "ollama", "qwen", "gemma", "local"),
        title="Local model and provider routing",
        purpose="Check local model readiness, route work to the right provider, and explain model queues honestly.",
        common_commands=("/model-doctor", "/model-health", "/providers", "/provider-status", "/route-explain YOUR_GOAL"),
        safe_next_steps=("Check /model-health before blaming GUI issues on the model.", "Use /queue-status when a model seems stuck.", "Keep remote providers gated behind /allow-internet."),
    ),
    GuiHelpTopic(
        key="autonomous",
        matches=("autonomous", "idle", "self repair", "agent", "mission", "improve"),
        title="Autonomous/idle/self-repair controls",
        purpose="Run bounded improvement loops with status, stop conditions, validation, and user confirmation gates.",
        common_commands=("/autonomous status", "/autonomous-plan GOAL", "/idle status", "/self-repair-status", "/self-repair-validate"),
        safe_next_steps=("Preview autonomous plans before long runs.", "Stop on repeated blockers.", "Require validation evidence before claiming success."),
    ),
)


def _parse_context(raw: str) -> dict[str, Any]:
    text = (raw or "").strip()
    if not text:
        return {}
    try:
        decoded = unquote_plus(text)
    except Exception:
        decoded = text
    for candidate in (decoded, text):
        if candidate.startswith("{") and candidate.endswith("}"):
            try:
                obj = json.loads(candidate)
                if isinstance(obj, dict):
                    return {str(k): v for k, v in obj.items()}
            except Exception:
                pass
    return {"text": decoded}


def _context_text(ctx: dict[str, Any]) -> str:
    parts: list[str] = []
    for key in ("label", "title", "aria", "placeholder", "command", "id", "classes", "text", "role"):
        val = ctx.get(key)
        if val:
            parts.append(str(val))
    return " ".join(parts).lower()


def _find_topic(ctx: dict[str, Any]) -> GuiHelpTopic:
    text = _context_text(ctx)
    scores: list[tuple[int, GuiHelpTopic]] = []
    for topic in _TOPICS:
        score = sum(1 for token in topic.matches if token in text)
        if score:
            scores.append((score, topic))
    if scores:
        scores.sort(key=lambda item: item[0], reverse=True)
        return scores[0][1]
    return _TOPICS[0]


def build_gui_context_help(raw: str) -> dict[str, Any]:
    ctx = _parse_context(raw)
    topic = _find_topic(ctx)
    label = ctx.get("label") or ctx.get("title") or ctx.get("aria") or ctx.get("placeholder") or ctx.get("id") or ctx.get("text") or "selected GUI element"
    command = ctx.get("command") or ""
    return {
        "ok": True,
        "label": str(label)[:160],
        "topic": topic.key,
        "title": topic.title,
        "purpose": topic.purpose,
        "element_context": {k: str(v)[:240] for k, v in ctx.items() if v is not None},
        "common_commands": list(topic.common_commands),
        "safe_next_steps": list(topic.safe_next_steps),
        "command_from_element": str(command)[:200],
        "ai_followups": [
            f"/tool-use-plan use {topic.title} for: {str(label)[:80]}",
            f"/pipeline-route {str(label)[:80]}",
            f"/role-router {str(label)[:80]}",
        ],
    }


def render_gui_context_help(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova GUI AI Help",
        "",
        f"Element: **{payload.get('label')}**",
        f"Topic: `{payload.get('topic')}` — {payload.get('title')}",
        "",
        "## What this part does",
        str(payload.get("purpose") or ""),
        "",
        "## Useful commands",
    ]
    for cmd in payload.get("common_commands", []):
        lines.append(f"- `{cmd}`")
    cmd = payload.get("command_from_element")
    if cmd:
        lines.extend(["", f"Command/action detected from this element: `{cmd}`"])
    lines.extend(["", "## Safe next steps"])
    for step in payload.get("safe_next_steps", []):
        lines.append(f"- {step}")
    lines.extend(["", "## Ask Nova to plan with this context"])
    for followup in payload.get("ai_followups", []):
        lines.append(f"- `{followup}`")
    ctx = payload.get("element_context") or {}
    if ctx:
        lines.extend(["", "## Element context received"])
        for key, value in ctx.items():
            if value:
                lines.append(f"- `{key}`: {value}")
    return "\n".join(lines)


def render_repo_inspired_gui_help_upgrades() -> str:
    return """# Nova GUI/Agent Upgrade Ideas Applied

Implemented in this patch:

- Contextual inline help dots on GUI controls, panels and command rows.
- A deterministic `/gui-ai-help` backend command that turns clicked GUI context into command help and safe next steps.
- Browser-side help panel buttons for Explain, Plan, Pipeline, Role route and Copy context.
- A help registry designed for future AI agents to extend without editing the large legacy web UI string.

Design inspirations adapted safely, not copied:

- Codebase-map style context: the help overlay sends a compact element context instead of dumping the whole UI.
- Agentic plan/execute/verify loops: help panels suggest `/tool-use-plan`, `/pipeline-route` and `/role-router` instead of blindly running tools.
- Source-controlled checks: GUI help diagnostics are covered by tests and docs so future patches can verify the interface contract.
"""
