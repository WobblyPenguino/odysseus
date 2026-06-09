from __future__ import annotations

import os
import platform
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(frozen=True)
class HighSpecProfile:
    name: str
    code_model: str
    chat_model: str
    planner_model: str
    vision_model: str
    embed_model: str
    local_model_timeout_sec: int
    context_chars: int
    command_timeout_sec: int
    recommended_subagent_slots: int
    notes: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_high_spec_profile(cpu_hint: str = "", gpu_hint: str = "", ram_gb: int | None = None) -> HighSpecProfile:
    """Return Nova's upgraded-PC runtime profile.

    The profile is intentionally conservative for Ollama: it allows more context
    and longer jobs, but still serializes LLM prompts unless an adapter proves
    it can isolate concurrent model workers.
    """
    cpu = cpu_hint or platform.processor() or platform.machine()
    gpu = gpu_hint or os.environ.get("NOVA_GPU_HINT", "RTX 5070 Ti class / 16GB VRAM if installed")
    ram_text = f"{ram_gb}GB RAM" if ram_gb else "user-upgraded PC memory"
    notes = [
        f"Detected/hinted CPU: {cpu}",
        f"Detected/hinted GPU: {gpu}",
        f"RAM profile: {ram_text}",
        "Use qwen3-coder:30b for code/planning when responsiveness is acceptable.",
        "Use gemma2:2b for quick chat/status fallbacks so the large coder model is not used for every tiny task.",
        "Keep vision model on demand; vision/video jobs are expensive and should not stay hot unnecessarily.",
        "Do not remove the Ollama prompt lock: subagents may parallelise deterministic diagnostics, while LLM calls remain serialized per local runtime.",
    ]
    return HighSpecProfile(
        name="upgraded_pc_qwen3_coder_30b",
        code_model="qwen3-coder:30b",
        chat_model="gemma2:2b",
        planner_model="qwen3-coder:30b",
        vision_model="llama3.2-vision:11b",
        embed_model="nomic-embed-text:latest",
        local_model_timeout_sec=420,
        context_chars=16000,
        command_timeout_sec=300,
        recommended_subagent_slots=3,
        notes=notes,
    )


def render_high_spec_profile(profile: HighSpecProfile | dict[str, Any]) -> str:
    data = profile.to_dict() if isinstance(profile, HighSpecProfile) else dict(profile or {})
    lines = [
        "# Nova High-Spec Local Profile",
        "",
        f"Profile: `{data.get('name','upgraded_pc')}`",
        f"Code/build model: `{data.get('code_model')}`",
        f"Chat/fast model: `{data.get('chat_model')}`",
        f"Planner/review model: `{data.get('planner_model')}`",
        f"Vision model: `{data.get('vision_model')}`",
        f"Embedding model: `{data.get('embed_model')}`",
        f"Local model timeout: {data.get('local_model_timeout_sec')}s",
        f"Context budget: {data.get('context_chars')} chars",
        f"Command timeout: {data.get('command_timeout_sec')}s",
        f"Recommended safe subagent slots: {data.get('recommended_subagent_slots')}",
        "",
        "## Safety/performance policy",
    ]
    lines.extend(f"- {note}" for note in data.get("notes", []))
    lines += [
        "",
        "## Windows environment",
        "Use `start_better_models_env.ps1` or `START_NOVA_HERE.bat` to load this profile.",
    ]
    return "\n".join(lines)
