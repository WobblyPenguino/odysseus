from __future__ import annotations

"""Provider routing, queue receipts, and OpenAI-compatible adapter helpers for Nova.

The public SubQ material and the local-runtime PDFs point to the same pattern:
keep Nova local-first, put all non-Ollama providers behind explicit adapters, and
make queue/permission state visible before adding more remote or NVIDIA-serving
options.  This module is intentionally small, deterministic and testable.  It does
not require any optional provider to be installed.
"""

from dataclasses import asdict, dataclass, field
from collections import defaultdict
from typing import Any, Callable
import json
import os
import threading
import time
import urllib.error
import urllib.request


REMOTE_PROVIDERS = {"openrouter", "subq", "nvidia-nim", "nvidia_nim"}
LOCAL_OPENAI_PROVIDERS = {"llama-cpp", "llama_cpp", "vllm", "sglang", "local-gemma", "local_gemma", "onnx-genai", "onnx_genai"}


@dataclass(frozen=True)
class RouteKey:
    provider: str
    model: str


@dataclass
class QueueReceipt:
    provider: str
    model: str
    desc: str = ""
    started_at: float = field(default_factory=time.time)
    acquired_at: float | None = None
    finished_at: float | None = None
    wait_sec: float = 0.0
    ok: bool | None = None
    result: str = "queued"

    def as_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["busy_for_sec"] = round((self.finished_at or time.time()) - self.started_at, 3)
        data["started_at_text"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.started_at))
        if self.acquired_at:
            data["acquired_at_text"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.acquired_at))
        if self.finished_at:
            data["finished_at_text"] = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(self.finished_at))
        return data


class ProviderScheduler:
    """Per-provider/per-model serialization.

    Ollama still keeps its own conservative global lock in ``ollama.py`` because a
    single desktop Ollama daemon can be fragile under overlapping prompts.  This
    scheduler is for the expanded provider layer: remote APIs, vLLM, SGLang,
    llama.cpp servers and future adapters can serialize only the specific
    (provider, model) lane while allowing other providers/models to continue.
    """

    def __init__(self) -> None:
        self._locks: dict[RouteKey, threading.Semaphore] = defaultdict(lambda: threading.Semaphore(1))
        self._guard = threading.Lock()
        self._active: dict[str, QueueReceipt] = {}
        self._history: list[QueueReceipt] = []

    def run(self, key: RouteKey, fn: Callable[..., Any], *args: Any, desc: str = "", timeout_sec: float | None = 900, **kwargs: Any) -> Any:
        receipt = QueueReceipt(provider=key.provider, model=key.model, desc=desc or "provider call")
        rid = f"{key.provider}:{key.model}:{receipt.started_at:.6f}"
        with self._guard:
            self._active[rid] = receipt
        timeout = None if timeout_sec is None or float(timeout_sec) <= 0 else float(timeout_sec)
        acquired = self._locks[key].acquire(timeout=timeout) if timeout is not None else self._locks[key].acquire()
        receipt.acquired_at = time.time() if acquired else None
        receipt.wait_sec = round((receipt.acquired_at or time.time()) - receipt.started_at, 3)
        if not acquired:
            receipt.ok = False
            receipt.result = "queue_timeout"
            receipt.finished_at = time.time()
            with self._guard:
                self._active.pop(rid, None)
                self._history.append(receipt)
                self._history = self._history[-100:]
            raise TimeoutError(f"Timed out waiting for provider lane {key.provider}:{key.model}")
        try:
            result = fn(*args, **kwargs)
            receipt.ok = True
            receipt.result = "ok"
            return result
        except Exception:
            receipt.ok = False
            receipt.result = "error"
            raise
        finally:
            receipt.finished_at = time.time()
            self._locks[key].release()
            with self._guard:
                self._active.pop(rid, None)
                self._history.append(receipt)
                self._history = self._history[-100:]

    def snapshot(self) -> dict[str, Any]:
        with self._guard:
            active = [r.as_dict() for r in self._active.values()]
            history = [r.as_dict() for r in self._history[-20:]]
        return {
            "active": active,
            "recent": history,
            "active_count": len(active),
            "note": "Provider queues are per (provider, model). Ollama also uses a conservative local daemon lock to prevent overlapping desktop prompts.",
        }


_PROVIDER_SCHEDULER = ProviderScheduler()


def get_provider_scheduler() -> ProviderScheduler:
    return _PROVIDER_SCHEDULER


def _env_present(name: str) -> bool:
    return bool(os.environ.get(name, "").strip())


def _cfg(config: Any, name: str, default: Any = "") -> Any:
    return getattr(config, name, default)


def provider_matrix(config: Any) -> dict[str, Any]:
    allow_internet = bool(_cfg(config, "allow_internet", False))
    rows = [
        {
            "provider": "ollama",
            "lane": "local-default",
            "enabled": True,
            "model": _cfg(config, "model", "qwen3-coder:30b"),
            "base_url": _cfg(config, "ollama_url", "http://127.0.0.1:11434"),
            "privacy": "local",
            "best_for": "default private chat, coding, voice, normal Nova maintenance",
            "notes": "Low friction Windows-first default. Same desktop daemon prompts remain serialized.",
        },
        {
            "provider": "llama-cpp",
            "lane": "local-openai-compatible",
            "enabled": bool(_cfg(config, "llama_cpp_url", "")),
            "model": _cfg(config, "llama_cpp_model", "local-gguf"),
            "base_url": _cfg(config, "llama_cpp_url", "http://127.0.0.1:8080/v1"),
            "privacy": "local",
            "best_for": "GGUF/quantized models, CPU/GPU fallback, simple local server",
            "notes": "Optional adapter; not bundled or required.",
        },
        {
            "provider": "vllm",
            "lane": "nvidia-local-throughput",
            "enabled": bool(_cfg(config, "vllm_url", "")),
            "model": _cfg(config, "vllm_model", "qwen3-coder:30b"),
            "base_url": _cfg(config, "vllm_url", "http://127.0.0.1:8000/v1"),
            "privacy": "local",
            "best_for": "12-24GB+ NVIDIA high-throughput OpenAI-compatible serving",
            "notes": "Advanced profile; keep Ollama as fallback/dev lane.",
        },
        {
            "provider": "sglang",
            "lane": "nvidia-local-agentic",
            "enabled": bool(_cfg(config, "sglang_url", "")),
            "model": _cfg(config, "sglang_model", "qwen3-coder:30b"),
            "base_url": _cfg(config, "sglang_url", "http://127.0.0.1:30000/v1"),
            "privacy": "local",
            "best_for": "structured-output-heavy or agentic serving with prefix-cache style workloads",
            "notes": "Advanced profile; optional.",
        },
        {
            "provider": "local-gemma",
            "lane": "local-multimodal",
            "enabled": bool(_cfg(config, "local_gemma_url", "")),
            "model": _cfg(config, "local_gemma_model", "gemma-4-12b"),
            "base_url": _cfg(config, "local_gemma_url", "http://127.0.0.1:5000/v1"),
            "privacy": "local",
            "best_for": "official/open local Gemma-style multimodal or reasoning model served by llama.cpp/vLLM",
            "notes": "Only official/open model sources; no jailbreak/cracked checkpoints.",
        },
        {
            "provider": "nvidia-nim",
            "lane": "remote-api",
            "enabled": allow_internet and _env_present(_cfg(config, "nvidia_nim_key_env", "NVIDIA_NIM_API_KEY")),
            "model": _cfg(config, "nvidia_nim_model", "zhipuai/glm-4"),
            "base_url": _cfg(config, "nvidia_nim_url", "https://integrate.api.nvidia.com/v1"),
            "privacy": "remote",
            "key_env": _cfg(config, "nvidia_nim_key_env", "NVIDIA_NIM_API_KEY"),
            "best_for": "explicit opt-in remote GPU-backed OpenAI-compatible fallback",
            "notes": "Requires allow-internet and BYO key; quotas and availability may change.",
        },
        {
            "provider": "subq",
            "lane": "remote-long-context",
            "enabled": allow_internet and _env_present(_cfg(config, "subq_key_env", "SUBQ_API_KEY")),
            "model": _cfg(config, "subq_model", "subq/1m-preview"),
            "base_url": _cfg(config, "subq_url", "https://api.subq.ai/v1"),
            "privacy": "remote",
            "key_env": _cfg(config, "subq_key_env", "SUBQ_API_KEY"),
            "best_for": "huge repositories, huge documents, months of state, long-context reports",
            "notes": "Feature-flagged premium/remote lane. Never send private context silently.",
        },
        {
            "provider": "openrouter",
            "lane": "remote-api",
            "enabled": allow_internet and _env_present(_cfg(config, "openrouter_key_env", "OPENROUTER_API_KEY")),
            "model": _cfg(config, "openrouter_model", "meta-llama/llama-3.3-70b-instruct:free"),
            "base_url": _cfg(config, "openrouter_url", "https://openrouter.ai/api/v1"),
            "privacy": "remote",
            "key_env": _cfg(config, "openrouter_key_env", "OPENROUTER_API_KEY"),
            "best_for": "optional BYO-key fallback when local models are weak",
            "notes": "Not a free-bypass; model availability and pricing can change.",
        },
    ]
    return {
        "active_provider": _cfg(config, "model_provider", "ollama"),
        "allow_internet": allow_internet,
        "providers": rows,
        "queue": _PROVIDER_SCHEDULER.snapshot(),
        "rules": [
            "local by default; remote by explicit permission",
            "SubQ is a remote long-context coprocessor, not a local Ollama replacement",
            "remote API keys live only in environment variables, never browser JavaScript or zip exports",
            "same provider/model calls are serialized; deterministic subagents can still run concurrently",
            "official/open model sources only; no jailbreak/cracked model acquisition paths",
        ],
    }


def choose_provider(goal: str, *, ctx_tokens: int = 0, privacy: str = "local_only", hardware: dict[str, Any] | None = None, config: Any | None = None) -> dict[str, Any]:
    text = (goal or "").lower()
    hardware = hardware or {}
    privacy = (privacy or "local_only").lower()
    allow_remote = privacy in {"remote_ok", "allow_remote", "internet", "remote"} and bool(_cfg(config, "allow_internet", False))
    huge_context = ctx_tokens >= 500_000 or any(term in text for term in ["entire repo", "whole repo", "huge document", "million token", "months of history", "full codebase", "large corpus"])
    if huge_context:
        if allow_remote:
            return {"provider": "subq", "model": _cfg(config, "subq_model", "subq/1m-preview"), "reason": "long-context workload exceeds normal local context budget and remote mode is explicitly allowed", "permission": "remote-long-context"}
        return {"provider": "ollama", "model": _cfg(config, "model", "qwen3-coder:30b"), "reason": "long-context workload detected, but remote providers are not enabled; use repo-map/RAG/chunking locally or explicitly enable remote-long-context", "permission": "local-only"}
    vram = int(float(hardware.get("nvidia_vram_gb", 0) or 0))
    if vram >= 16 and privacy != "local_only_disabled":
        return {"provider": "vllm", "model": _cfg(config, "vllm_model", _cfg(config, "model", "qwen3-coder:30b")), "reason": "NVIDIA 16GB+ hardware is suitable for an advanced local throughput lane if the server is configured", "permission": "local"}
    if hardware.get("windows_directml"):
        return {"provider": "onnx-genai", "model": "local-onnx-model", "reason": "Windows DirectML fallback available for compatible ONNX models", "permission": "local"}
    return {"provider": "ollama", "model": _cfg(config, "model", "qwen3-coder:30b"), "reason": "default private local route", "permission": "local"}


def render_provider_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Nova Provider Status", "", f"Active provider: `{payload.get('active_provider')}`", f"Internet/remote allowed: `{payload.get('allow_internet')}`", "", "## Provider lanes"]
    for p in payload.get("providers", []):
        mark = "READY" if p.get("enabled") else "available/configurable"
        if p.get("provider") == "ollama":
            mark = "default"
        lines.append(f"- **{p.get('provider')}** ({p.get('lane')}): {mark}; model=`{p.get('model')}`; privacy=`{p.get('privacy')}`")
        lines.append(f"  - Best for: {p.get('best_for')}")
        lines.append(f"  - Note: {p.get('notes')}")
    q = payload.get("queue", {})
    lines += ["", "## Queue", f"Active provider/model calls: **{q.get('active_count', 0)}**", q.get("note", "")]
    recent = q.get("recent") or []
    if recent:
        lines.append("\nRecent provider queue receipts:")
        for r in recent[-5:]:
            lines.append(f"- `{r.get('provider')}:{r.get('model')}` {r.get('result')} wait={r.get('wait_sec')}s desc={r.get('desc')}")
    lines += ["", "## Rules", *[f"- {r}" for r in payload.get("rules", [])]]
    return "\n".join(lines)


def render_route_markdown(route: dict[str, Any], goal: str) -> str:
    return "\n".join([
        "# Nova Provider Route Explanation",
        "",
        f"Goal: {goal or '(none)'}",
        f"Chosen provider: `{route.get('provider')}`",
        f"Model: `{route.get('model')}`",
        f"Permission lane: `{route.get('permission')}`",
        "",
        f"Reason: {route.get('reason')}",
        "",
        "Remote providers are never used silently. Enable them with `/allow-internet on`, configure the relevant environment key, and verify `/provider-status` first.",
    ])


def provider_test_plan(config: Any, provider: str = "") -> dict[str, Any]:
    provider = (provider or _cfg(config, "model_provider", "ollama") or "ollama").lower().replace("_", "-")
    matrix = provider_matrix(config)
    row = next((p for p in matrix["providers"] if p["provider"] == provider), None)
    if not row:
        return {"ok": False, "provider": provider, "message": "Unknown provider", "known": [p["provider"] for p in matrix["providers"]]}
    prompt = "Say READY and compute 7+5."
    command = ""
    if provider == "ollama":
        command = f"ollama run {row['model']} \"{prompt}\""
    elif provider in {"llama-cpp", "vllm", "sglang", "local-gemma"}:
        command = f"curl {str(row['base_url']).rstrip('/')}/chat/completions -H \"Content-Type: application/json\" -d '{{\"model\":\"{row['model']}\",\"messages\":[{{\"role\":\"user\",\"content\":\"{prompt}\"}}]}}'"
    else:
        command = f"curl {str(row['base_url']).rstrip('/')}/chat/completions -H \"Authorization: Bearer % {row.get('key_env','API_KEY')}%\" -H \"Content-Type: application/json\" -d '{{\"model\":\"{row['model']}\",\"messages\":[{{\"role\":\"user\",\"content\":\"{prompt}\"}}]}}'"
    return {
        "ok": True,
        "provider": provider,
        "enabled_now": row.get("enabled"),
        "privacy": row.get("privacy"),
        "dry_run": True,
        "command": command,
        "expected": "Response contains READY and 12.",
        "safe_note": "This is a dry-run test plan. Nova will not call remote providers unless internet and the relevant API key are configured.",
    }


def call_openai_compatible(config: Any, provider: str, model: str, messages: list[dict[str, str]], *, timeout: int | None = 180, desc: str = "provider model call") -> str | None:
    provider = (provider or "").lower().replace("_", "-")
    if provider in REMOTE_PROVIDERS and not bool(_cfg(config, "allow_internet", False)):
        return None
    if provider == "subq":
        base_url = _cfg(config, "subq_url", "https://api.subq.ai/v1")
        key_env = _cfg(config, "subq_key_env", "SUBQ_API_KEY")
    elif provider in {"nvidia-nim", "nvidia_nim"}:
        base_url = _cfg(config, "nvidia_nim_url", "https://integrate.api.nvidia.com/v1")
        key_env = _cfg(config, "nvidia_nim_key_env", "NVIDIA_NIM_API_KEY")
    elif provider == "openrouter":
        base_url = _cfg(config, "openrouter_url", "https://openrouter.ai/api/v1")
        key_env = _cfg(config, "openrouter_key_env", "OPENROUTER_API_KEY")
    elif provider == "vllm":
        base_url = _cfg(config, "vllm_url", "http://127.0.0.1:8000/v1")
        key_env = ""
    elif provider == "sglang":
        base_url = _cfg(config, "sglang_url", "http://127.0.0.1:30000/v1")
        key_env = ""
    elif provider in {"llama-cpp", "llama_cpp"}:
        base_url = _cfg(config, "llama_cpp_url", "http://127.0.0.1:8080/v1")
        key_env = ""
    elif provider in {"local-gemma", "local_gemma"}:
        base_url = _cfg(config, "local_gemma_url", "http://127.0.0.1:5000/v1")
        key_env = ""
    else:
        return None
    key = os.environ.get(str(key_env), "").strip() if key_env else ""
    if provider in REMOTE_PROVIDERS and not key:
        return None
    if not model:
        return None

    def _call() -> str | None:
        url = str(base_url).rstrip("/") + "/chat/completions"
        payload = json.dumps({"model": model, "messages": messages, "temperature": 0.2}).encode("utf-8")
        headers = {"Content-Type": "application/json"}
        if key:
            headers["Authorization"] = "Bearer " + key
        req = urllib.request.Request(url, data=payload, method="POST", headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=(None if timeout is None or int(timeout) <= 0 else timeout)) as resp:
                raw = resp.read().decode("utf-8", errors="replace")
                data: Any = json.loads(raw)
                return (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, KeyError, IndexError):
            return None

    return _PROVIDER_SCHEDULER.run(RouteKey(provider, model), _call, desc=desc, timeout_sec=_cfg(config, "local_model_queue_timeout_sec", 900))
