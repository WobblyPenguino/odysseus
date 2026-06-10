from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CommandSuggestion:
    label: str
    command: str
    reason: str
    risk: str
    category: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def suggest_next_commands(
    user_text: str,
    last_response: str = "",
    context: dict | None = None,
) -> list[CommandSuggestion]:
    context = context or {}
    context_text = _flatten_context(context)
    text = f"{user_text or ''}\n{last_response or ''}\n{context_text}".lower()
    suggestions: list[CommandSuggestion] = []

    def add(label: str, command: str, reason: str, risk: str = "low", category: str = "general") -> None:
        if len(suggestions) >= 3:
            return
        if _is_disallowed(command):
            return
        if any(item.command == command for item in suggestions):
            return
        suggestions.append(CommandSuggestion(label, command, reason, risk, category))

    self_improve_mentioned = any(term in text for term in ["self-improve", "self improve", "self-improvement", "self improvement", "improve itself", "improve yourself"])
    wla_source_review = any(term in text for term in [
        "your own files", "your files", "your own code", "review your code", "wla source",
        "winlocalassistant", "coding capabilities", "validation capabilities",
    ])
    if wla_source_review:
        add("Codebase audit", "/codebase-audit", "Review Nova source integrity from Nova's own files.", category="wla")
        add("Code review", "/code-review", "Run deeper reliability and UX review over the Nova codebase.", category="wla")
        add("Model context", "/model-context", "Show the source/context pack available to the local model.", category="wla")
        add("Feature continuity", "/feature-continuity-audit", "Check key Nova GUI/tool surfaces were not accidentally removed.", category="wla")

    if any(term in text for term in ["prompt active", "prompt busy", "local model/task", "ollama", "stopping..."]):
        add("LLM status", "/llm-status", "Check whether Nova is actively prompting or Ollama is only loaded/stopping.", category="llm")
        add("Interrupt current", "/interrupt-current --confirm", "Stop a broken active Nova model request after review.", risk="medium", category="llm")
        add("Stop Ollama", "/ollama-stop --confirm", "Unload a stale/stuck Ollama model after confirming no prompt should be running.", risk="medium", category="llm")

    if any(term in text for term in ["gui", "ui", "layout", "drawer", "blank panel", "broken screen", "screenshot"]):
        add("Focus chat", "/validation-status", "Check whether the running backend is current before changing GUI code.", category="gui")
        add("GUI visual test", "/gui-visual-test", "Use the existing GUI visual-regression gate before and after layout changes.", category="gui")
        add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")

    if any(term in text for term in ["video", "image", "media", "comfyui", "storyboard", "trailer", "render"]):
        add("Media status", "/media-status", "Check image/video backend readiness before trying expensive generation.", category="media")
        add("Image plan", "/image-plan cinematic robot dog mascot", "Create prompt variants and safety metadata before generation.", category="media")
        add("Video package", "/video-package 10 second cinematic trailer about Nova improving a project", "Create a resumable render package instead of calling missing backends blindly.", category="media")

    if any(term in text for term in ["remote pc", "remote access", "tailscale", "wake-on-lan", "wake on lan", "phone", "laptop"]):
        add("Remote preflight", "/remote-access-test", "Check scripts, token, Tailscale and manual setup gaps without changing files.", category="remote")
        add("Remote profiles", "/remote-profile list", "Show saved private remote targets without revealing tokens.", category="remote")
        add("Remote API health", "/remote-api-health 127.0.0.1 8767 --dry-run", "Verify the API test command shape before probing a network endpoint.", category="remote")

    if any(term in text for term in ["use tools", "choose tools", "planning", "planner", "not rigid", "template", "adaptive", "intelligence"]):
        add("Tool-use plan", "/tool-use-plan adaptively solve this prompt", "Ask Nova to choose a tool sequence from the current registry for the actual prompt.", category="planning")
        add("Pipeline route", "/pipeline-route adaptively solve this prompt", "Classify the task into observe/plan/act/verify stages before execution.", category="planning")
        add("Role router", "/role-router current task", "Pick planner/builder/verifier/repairer roles instead of one rigid template.", category="planning")

    if any(term in text for term in ["health gate blocked", "loop guard", "same health-gate", "repeated base diagnostic", "autonomous cycle"]):
        add("Auto status", "/autonomous status", "Show the current autonomous phase, target and blocker.", category="autonomous")
        add("Auto explain", "/autonomous-explain", "Explain why autonomous is waiting, blocked or repeating.", category="autonomous")
        add("Auto memory", "/autonomous-memory", "Inspect failure signatures and cooldowns before retrying.", category="autonomous")

    if any(term in text for term in ["manifest verification failed", "then : the term", "verify_command", "powershell", "play-test"]):
        add("Repair verifier", "/surgical-repair fix the project verification command so only machine-checkable commands run", "Target the verifier failure before asking the model to regenerate code.", category="verify")
        add("Final check", "/final-check .", "Recheck the project against the original request after verifier repair.", category="verify")

    if self_improve_mentioned:
        add("Safe plan", "/idle propose create a safe self-improvement plan", "Keep self-improvement manual and proposal-only.", category="self-improve")
        if _clearly_manual_self_improve(user_text):
            add("Manual self-improve", "/self-improve <goal>", "Manual guarded mode only; review before sending.", risk="high", category="self-improve")

    if any(term in text for term in ["idle", "autonomous"]) or self_improve_mentioned:
        add("Idle status", "/idle status", "Check idle/autonomous self-improvement state without changing files.", category="idle")
        add("Idle once", "/idle once inspect logs and propose safe improvements", "Run a report-only idle inspection.", category="idle")
        add("Idle propose", "/idle propose improve idle self-improvement safely", "Create a dry-run proposal only.", category="idle")

    if any(term in text for term in ["logs", "error", "crash", "failed", "traceback", "exception"]):
        add("Investigate logs", "/idle once investigate logs and propose safe improvements", "Inspect recent failures without applying changes.", category="diagnostics")
        add("Add diagnostics", "/idle propose add diagnostics for recent failures", "Draft a safe diagnostics proposal.", category="diagnostics")

    if any(term in text for term in ["test", "verify", "broken", "check"]):
        add("Test all", "/test-all", "Run the existing verification command.", category="verify")
        add("Doctor", "/nova-doctor", "Run Nova's self-diagnosis before changing code.", category="verify")
        add("Docker quick", "/docker-validate quick", "Validate a copied workspace when Docker is available.", category="verify")

    if any(term in text for term in ["docker", "sandbox", "kali", "container"]):
        add("Docker status", "/docker-status", "Show Docker readiness and recent validation history.", category="docker")
        add("Docker history", "/docker-history", "Inspect recent copied-workspace and patch validations.", category="docker")
        add("Sandbox status", "/sandbox-status", "Show Linux/Kali policy and running sandbox state.", category="sandbox")

    if any(term in text for term in ["project", "code", "app", "generated", "files"]):
        add("Projects", "/projects", "Confirm the active project/workspace before editing.", category="project")
        add("Project memory", "/project-memory", "Show saved facts for the current project.", category="project")
        add("Remember project", "/remember-project important project detail", "Save a fact for later context.", category="project")

    if any(term in text for term in ["research", "source", "citation", "reference"]):
        add("Research", "/research topic to investigate", "Gather sources with excerpts, source scoring and synthesis.", category="research")
        add("Research DB", "/db schema research", "Inspect stored research report metadata.", category="research")

    if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):
        add("Help", "/help", "Show available commands.", category="help")
        add("Tool guide", "/tool-guide", "Show the local model tool-use guide.", category="help")

    if not suggestions:
        add("Help", "/help", "Show available commands.", category="help")
        add("Idle status", "/idle status", "Check idle self-improvement state.", category="idle")

    return suggestions[:3]


def _flatten_context(context: dict[str, Any]) -> str:
    try:
        parts: list[str] = []
        avatar = context.get("avatar") if isinstance(context, dict) else {}
        if isinstance(avatar, dict):
            parts.extend(str(avatar.get(k, "")) for k in ["mood", "title", "text", "current_task", "disclosure"])
        live = context.get("live") if isinstance(context, dict) else {}
        if isinstance(live, dict):
            parts.extend(str(live.get(k, "")) for k in ["current_task"])
        return "\n".join(p for p in parts if p)
    except Exception:
        return ""


def _clearly_manual_self_improve(text: str) -> bool:
    low = (text or "").lower()
    return any(term in low for term in [
        "/self-improve",
        "manual self-improve",
        "manual guarded self-improvement",
        "run self-improve manually",
        "use self-improve",
    ])


def _is_disallowed(command: str) -> bool:
    low = (command or "").lower()
    blocked = [
        "/idle start",
        "powershell",
        "pwsh",
        "cmd.exe",
        "pip install",
        "npm install",
        "/pip-install",
        "/allow-internet on",
        "/internet-fetch",
        "/self-improve automatically",
        "/reset-project",
    ]
    return any(term in low for term in blocked)
