from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .safe_io import atomic_write_json, atomic_write_text, read_json_file

def _resolve_app_dir() -> Path:
    """Return a writable profile directory.

    Nova stores profile data in ``~/.nova``. Some verification/sandbox
    environments expose a read-only or partially-owned home profile; in that
    case fall back to a repository-local runtime directory instead of crashing
    during tests or startup. Users can set ``NOVA_APP_DIR`` for isolated runs;
    the legacy ``WLA_APP_DIR`` name is still accepted as a compatibility alias.
    """
    import os
    import tempfile

    explicit = os.environ.get("NOVA_APP_DIR") or os.environ.get("WLA_APP_DIR")
    candidates = [Path(explicit)] if explicit else []
    candidates.extend([
        Path.home() / ".nova",
        Path.home() / ".winlocalassistant",  # compatibility migration path
        Path.cwd() / ".nova_runtime",
        Path(tempfile.gettempdir()) / "nova_profile",
    ])
    for candidate in candidates:
        try:
            candidate.mkdir(parents=True, exist_ok=True)
            probe = candidate / ".write_test"
            atomic_write_text(probe, "ok")
            probe.unlink(missing_ok=True)
            return candidate
        except Exception:
            continue
    return Path(tempfile.gettempdir()) / "nova_profile"


APP_DIR = _resolve_app_dir()
CONFIG_PATH = APP_DIR / "config.json"
TRACE_PATH = APP_DIR / "traces.jsonl"
MEMORY_PATH = APP_DIR / "memory.jsonl"
PLAN_PATH = APP_DIR / "last_plan.json"


def _apply_env_overrides(cfg: "AssistantConfig") -> "AssistantConfig":
    """Apply explicit per-session model overrides without editing config.json."""
    import os

    mapping = {
        "NOVA_MODEL": "model",
        "NOVA_CODE_MODEL": "model",
        "OLLAMA_MODEL": "model",
        "NOVA_CHAT_MODEL": "chat_model",
        "NOVA_PLANNER_MODEL": "planner_model",
        "NOVA_VISION_MODEL": "vision_model",
        "NOVA_MODEL_ROUTE": "model_route",
    }
    for env_name, attr in mapping.items():
        value = os.environ.get(env_name)
        if value:
            setattr(cfg, attr, value.strip())
    timeout = os.environ.get("NOVA_LOCAL_MODEL_TIMEOUT_SEC")
    if timeout:
        try:
            cfg.local_model_timeout_sec = max(0, int(float(timeout)))
        except ValueError:
            pass
    chat_timeout = os.environ.get("NOVA_CHAT_MODEL_TIMEOUT_SEC")
    if chat_timeout:
        try:
            cfg.chat_model_timeout_sec = max(0, int(float(chat_timeout)))
        except ValueError:
            pass
    code_timeout = os.environ.get("NOVA_CODE_MODEL_TIMEOUT_SEC")
    if code_timeout:
        try:
            cfg.code_model_timeout_sec = max(0, int(float(code_timeout)))
        except ValueError:
            pass
    autonomous_timeout = os.environ.get("NOVA_AUTONOMOUS_MODEL_TIMEOUT_SEC")
    if autonomous_timeout:
        try:
            cfg.autonomous_model_timeout_sec = max(0, int(float(autonomous_timeout)))
        except ValueError:
            pass
    context_chars = os.environ.get("NOVA_LOCAL_MODEL_CONTEXT_MAX_CHARS")
    if context_chars:
        try:
            cfg.local_model_context_max_chars = max(2000, int(float(context_chars)))
        except ValueError:
            pass
    return cfg


@dataclass
class AssistantConfig:
    workspace: str = str(Path.home() / "Documents" / "NovaProjects")
    allow_mutating_tools: bool = True
    allow_internet: bool = False
    ollama_url: str = "http://127.0.0.1:11434"
    # Code/build model. Use a coder model here.
    model: str = "qwen3-coder:30b"
    # Normal chat/creative model. This can be a general instruct model, not a coder.
    chat_model: str = "gemma2:2b"
    # Optional planning/review model. Blank means use code model.
    planner_model: str = ""
    model_route: str = "auto"
    # Skill profile routing for normal chat and direct tutoring/writing commands.
    skill_mode: str = "auto"
    # v40: optional BYO-key remote provider. OpenRouter requires allow_internet=True and OPENROUTER_API_KEY.
    model_provider: str = "ollama"
    openrouter_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct:free"
    openrouter_key_env: str = "OPENROUTER_API_KEY"
    # v55.3.164 provider-runtime adapters. These are optional and disabled unless
    # the user configures a local server or BYO remote API key. Remote providers
    # also require /allow-internet on.
    subq_url: str = "https://api.subq.ai/v1"
    subq_model: str = "subq/1m-preview"
    subq_key_env: str = "SUBQ_API_KEY"
    nvidia_nim_url: str = "https://integrate.api.nvidia.com/v1"
    nvidia_nim_model: str = "zhipuai/glm-4"
    nvidia_nim_key_env: str = "NVIDIA_NIM_API_KEY"
    llama_cpp_url: str = ""
    llama_cpp_model: str = "local-gguf"
    vllm_url: str = ""
    vllm_model: str = "qwen3-coder:30b"
    sglang_url: str = ""
    sglang_model: str = "qwen3-coder:30b"
    local_gemma_url: str = ""
    local_gemma_model: str = "gemma-4-12b"
    # Optional local vision model for /image-analyze and visual project audits.
    vision_model: str = "llama3.2-vision:11b"
    command_timeout_sec: int = 300
    # Upgraded-PC default: wait long enough for qwen3-coder:30b, but not indefinitely.
    local_model_timeout_sec: int = 420
    # Runtime tiering: normal chat must fail fast into deterministic fallback,
    # while code/planning/autonomous work can wait longer.
    chat_model_timeout_sec: int = 45
    code_model_timeout_sec: int = 180
    autonomous_model_timeout_sec: int = 420
    # Add compact Nova/project/tool context to local model prompts.
    local_model_context_enabled: bool = True
    local_model_context_max_chars: int = 16000
    # Measure command/tool/model/chat durations and estimate relative energy use.
    efficiency_profiler_enabled: bool = True
    efficiency_cpu_watts: float = 45.0
    efficiency_gpu_watts: float = 0.0
    efficiency_model_extra_watts: float = 25.0
    # Disposable Linux/Kali sandbox settings.  Network and authorised lab mode
    # default to off; commands remain logged and policy-gated.
    sandbox_backend: str = "auto"
    sandbox_linux_image: str = "python:3.12-slim"
    sandbox_kali_image: str = "kalilinux/kali-rolling"
    sandbox_cpu_limit: str = "6"
    sandbox_memory_limit: str = "8g"
    sandbox_pids_limit: int = 768
    sandbox_allow_network: bool = False
    sandbox_authorized_security_lab: bool = False
    # Sandbox policy levels:
    # - strict: prompt/deny anything beyond basic local commands.
    # - balanced: default; allow metadata checks and prompt for high-risk/networked lab work.
    # - trusted_lab: less strict mode for user-owned/local labs. High-risk Kali tools
    #   and network-capable tools are allowed without per-command approval while
    #   host escape and destructive root patterns remain blocked.
    sandbox_policy_level: str = "balanced"

    # Bounded self-repair: this package enables deterministic, test-backed self-repair
    # because the user explicitly granted permission. Destructive/OS/account actions
    # still remain behind command-specific approval gates.
    self_repair_permission: bool = True
    self_repair_auto_apply: bool = True
    self_repair_max_patch_files: int = 3
    # Ollama queueing: multi-agent workers can run in parallel, but same/local model
    # prompts wait in a queue instead of hitting Ollama concurrently.
    local_model_queue_timeout_sec: int = 900

    @classmethod
    def load(cls) -> "AssistantConfig":
        APP_DIR.mkdir(parents=True, exist_ok=True)
        if not CONFIG_PATH.exists():
            cfg = cls()
            cfg.save()
            return _apply_env_overrides(cfg)
        try:
            data = read_json_file(CONFIG_PATH, {}, expected_type=dict, quarantine=True)
            defaults = asdict(cls())
            # v15 migration: for this local builder, file mutation is ON by default
            # and the workspace defaults to Documents\NovaProjects.
            # Existing users can still turn it off with /allow-mutate off.
            if not data.get("v15_defaults_applied"):
                data["allow_mutating_tools"] = True
                old_ws = str(data.get("workspace", ""))
                if old_ws.lower() in {str(Path.home()).lower(), str((Path.home() / "Documents" / "Projects")).lower()}:
                    data["workspace"] = defaults["workspace"]
                data["v15_defaults_applied"] = True
                try:
                    atomic_write_json(CONFIG_PATH, data, ensure_ascii=True)
                except Exception:
                    import logging as _wla_logging
                    _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)
            data = {k: v for k, v in data.items() if k in defaults}
            return _apply_env_overrides(cls(**{**defaults, **data}))
        except Exception:
            cfg = cls()
            cfg.save()
            return _apply_env_overrides(cfg)

    def save(self) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write_json(CONFIG_PATH, asdict(self), ensure_ascii=True)
