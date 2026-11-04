from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ModelHealthReport:
    ok: bool
    provider: str
    model: str
    status: str
    issues: list[str]
    recommendations: list[str]
    timeout_seconds: int
    command_timeout_seconds: int
    chat_timeout_seconds: int = 0
    code_timeout_seconds: int = 0
    autonomous_timeout_seconds: int = 0
    prompt_active: bool = False
    cooldown_active: bool = False
    available: bool | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def assess_model_dependency(config: Any, ollama_ps: dict[str, Any] | None = None, busy_state: dict[str, Any] | None = None) -> ModelHealthReport:
    """Return a non-throwing model dependency report.

    This intentionally does not call the model.  It summarizes the configuration
    and already-known status so command/UI paths can explain degraded operation
    without blocking on a slow or unavailable local LLM.
    """
    provider = str(getattr(config, "model_provider", "ollama") or "ollama").lower()
    model = str(getattr(config, "model", "") or "")
    local_timeout = int(getattr(config, "local_model_timeout_sec", 0) or 0)
    chat_timeout = int(getattr(config, "chat_model_timeout_sec", local_timeout) or 0)
    code_timeout = int(getattr(config, "code_model_timeout_sec", local_timeout) or 0)
    autonomous_timeout = int(getattr(config, "autonomous_model_timeout_sec", local_timeout) or 0)
    command_timeout = int(getattr(config, "command_timeout_sec", 120) or 120)
    issues: list[str] = []
    recommendations: list[str] = []
    available: bool | None = None

    busy_state = busy_state or {}
    prompt_active = bool(busy_state.get("prompt_active"))
    cooldown_active = bool(busy_state.get("cooldown_active"))
    if prompt_active:
        issues.append("A local-model prompt is currently active.")
        recommendations.append("Wait for it to finish or use /interrupt-current if it is stuck.")
    if cooldown_active:
        issues.append("The local-model prompt lane is cooling down after a recent timeout/error.")
        recommendations.append("Wait for cooldown to end before starting another generation.")

    if provider == "openrouter":
        if not bool(getattr(config, "allow_internet", False)):
            issues.append("OpenRouter is selected but internet access is disabled.")
            recommendations.append("Use /allow-internet on only if you intentionally want BYO-key remote model access, or switch back to Ollama.")
        if not str(getattr(config, "openrouter_model", "") or ""):
            issues.append("OpenRouter provider has no model configured.")
            recommendations.append("Set /model-route auto and configure an OpenRouter model, or use a local Ollama model.")
    else:
        if ollama_ps is not None:
            available = bool(ollama_ps.get("available"))
            if not available:
                issues.append("Ollama is not available from the current PATH/session.")
                recommendations.append("Start Ollama with: ollama serve")
                if model:
                    recommendations.append(f"Pull the selected coder model with: ollama pull {model}")
        if not model:
            issues.append("No local code/build model is configured.")
            recommendations.append("Set a coder model with /model-code qwen3-coder:30b or another installed coder model.")

    if local_timeout <= 0:
        recommendations.append("Local-model timeout is off; long generations may wait indefinitely. Use /model-timeout SECONDS if you prefer bounded waits.")
    if chat_timeout > 0 and chat_timeout >= local_timeout and local_timeout > 0:
        recommendations.append("Normal chat timeout is not shorter than code/autonomous timeout; use NOVA_CHAT_MODEL_TIMEOUT_SEC for faster fallback.")
    if command_timeout < 10:
        issues.append("Shell command timeout is very low and may interrupt normal verification commands.")
        recommendations.append("Use /command-timeout 120 or higher for normal project verification.")

    # New check - warn if all timeouts are zero
    if local_timeout == 0 and chat_timeout == 0 and code_timeout == 0 and autonomous_timeout == 0:
        issues.append("All model timeouts are set to zero, which may lead to indefinite hangs.")
        recommendations.append("Set at least one timeout value (e.g., local-model-timeout) to prevent unexpected behavior.")

    ok = not issues
    status = "ready" if ok else "degraded"
    return ModelHealthReport(
        ok=ok,
        provider=provider,
        model=model,
        status=status,
        issues=issues,
        recommendations=recommendations,
        timeout_seconds=local_timeout,
        command_timeout_seconds=command_timeout,
        chat_timeout_seconds=chat_timeout,
        code_timeout_seconds=code_timeout,
        autonomous_timeout_seconds=autonomous_timeout,
        prompt_active=prompt_active,
        cooldown_active=cooldown_active,
        available=available,
    )


def render_model_health_markdown(report: ModelHealthReport | dict[str, Any]) -> str:
    data = report.to_dict() if hasattr(report, "to_dict") else dict(report)
    lines = [
        "# Model Health",
        "",
        f"Status: **{data.get('status', 'unknown')}**",
        f"Provider: `{data.get('provider', '')}`",
        f"Code/build model: `{data.get('model', '')}`",
        f"Local model timeout: `{data.get('timeout_seconds', 0)}` seconds (`0` means off)",
        f"Chat timeout tier: `{data.get('chat_timeout_seconds', 0)}` seconds",
        f"Code timeout tier: `{data.get('code_timeout_seconds', 0)}` seconds",
        f"Autonomous timeout tier: `{data.get('autonomous_timeout_seconds', 0)}` seconds",
        f"Shell command timeout: `{data.get('command_timeout_seconds', 0)}` seconds",
        f"Prompt active: `{data.get('prompt_active', False)}`",
        f"Cooldown active: `{data.get('cooldown_active', False)}`",
        "",
        "## Issues",
    ]
    issues = list(data.get("issues") or [])
    if issues:
        lines.extend(f"- {issue}" for issue in issues)
    else:
        lines.append("- No blocking model dependency issue detected from current status.")
    lines.extend(["", "## Recommendations"])
    recs = list(data.get("recommendations") or [])
    if recs:
        lines.extend(f"- {rec}" for rec in recs)
    else:
        lines.append("- No immediate action required.")
    return "\n".join(lines)
