from __future__ import annotations

import json
import os
import time
import urllib.error
import urllib.request
from typing import Any

from .ollama import ollama_chat, _OLLAMA_LOCK, _set_last  # reuse one-prompt-at-a-time lifecycle
from .model_context import enrich_messages_with_context
from .provider_runtime import call_openai_compatible
from .efficiency_profiler import append_efficiency_sample, profiler_enabled


def _resolve_model_name(config: Any, model: str | None, provider: str) -> str:
    candidate = str(model or "").strip()
    p = (provider or "ollama").lower().replace("_", "-")
    if p == "openrouter":
        return candidate or str(getattr(config, "openrouter_model", "") or "")
    if p == "subq":
        return candidate or str(getattr(config, "subq_model", "subq/1m-preview") or "")
    if p == "nvidia-nim":
        return candidate or str(getattr(config, "nvidia_nim_model", "zhipuai/glm-4") or "")
    if p == "llama-cpp":
        return candidate or str(getattr(config, "llama_cpp_model", "local-gguf") or "")
    if p == "vllm":
        return candidate or str(getattr(config, "vllm_model", getattr(config, "model", "")) or "")
    if p == "sglang":
        return candidate or str(getattr(config, "sglang_model", getattr(config, "model", "")) or "")
    if p == "local-gemma":
        return candidate or str(getattr(config, "local_gemma_model", "gemma-4-12b") or "")
    return candidate or str(getattr(config, "model", "") or "")


def _openrouter_chat(config: Any, model: str, messages: list[dict[str, str]], timeout: int | None = 180, desc: str = "openrouter model call") -> str | None:
    """Call OpenRouter only when the user has explicitly enabled internet/provider use.

    This is intentionally BYO-key. It does not use or scrape godmod3.ai and it does
    not bypass provider limits. Some OpenRouter models have ':free' variants, but
    they still require an OpenRouter key and provider/rate-limit rules apply.
    """
    if not bool(getattr(config, "allow_internet", False)):
        return None
    key = os.environ.get(str(getattr(config, "openrouter_key_env", "OPENROUTER_API_KEY")) or "OPENROUTER_API_KEY", "").strip()
    if not key:
        return None

    acquired = _OLLAMA_LOCK.acquire(blocking=False)
    if not acquired:
        return None

    import uuid
    request_id = time.strftime("%Y%m%d_%H%M%S_") + uuid.uuid4().hex[:8]
    started = time.time()
    try:
        url = str(getattr(config, "openrouter_url", "https://openrouter.ai/api/v1")).rstrip("/") + "/chat/completions"
        if model.startswith("openrouter:"):
            model = model.split(":", 1)[1]
        if not model:
            model = str(getattr(config, "openrouter_model", "meta-llama/llama-3.3-70b-instruct:free"))
        payload = json.dumps({"model": model, "messages": messages, "temperature": 0.2}).encode("utf-8")
        req = urllib.request.Request(url, data=payload, method="POST", headers={
            "Content-Type": "application/json",
            "Authorization": "Bearer " + key,
            "HTTP-Referer": "http://127.0.0.1:8766",
            "X-Title": "Nova",
        })
        with urllib.request.urlopen(req, timeout=(None if timeout is None or int(timeout) <= 0 else timeout)) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
            data: Any = json.loads(raw)
            content = (data.get("choices") or [{}])[0].get("message", {}).get("content", "")
            _set_last(request_id, desc, started, "ok", len(content), False)
            return content
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError, KeyError, IndexError):
        _set_last(request_id, desc, started, "openrouter_timeout_or_error", 0, True)
        return None
    finally:
        _OLLAMA_LOCK.release()


def model_chat(config: Any, model: str, messages: list[dict[str, str]], timeout: int | None = 180, desc: str = "model call", **kwargs: Any) -> str | None:
    provider = str(getattr(config, "model_provider", "ollama") or "ollama").lower().strip()
    selected_model = _resolve_model_name(config, model, provider)
    if provider == "openrouter" and not bool(getattr(config, "allow_internet", False)):
        return None
    if not selected_model:
        return None
    messages = enrich_messages_with_context(config, messages, desc=desc)
    started_wall = time.perf_counter()
    started_cpu = time.process_time()
    started_at = time.strftime("%Y-%m-%d %H:%M:%S")
    ok = False
    try:
        normalized_provider = provider.replace("_", "-")
        if selected_model.startswith("openrouter:") or normalized_provider == "openrouter":
            result = _openrouter_chat(config, selected_model, messages, timeout=timeout, desc=desc)
        elif normalized_provider in {"subq", "nvidia-nim", "llama-cpp", "vllm", "sglang", "local-gemma"}:
            result = call_openai_compatible(config, normalized_provider, selected_model, messages, timeout=timeout, desc=desc)
        else:
            result = ollama_chat(getattr(config, "ollama_url", "http://127.0.0.1:11434"), selected_model, messages, timeout=timeout, desc=desc, **kwargs)
        ok = result is not None
        return result
    finally:
        if profiler_enabled(config):
            try:
                append_efficiency_sample(
                    config,
                    kind="model_call",
                    name=str(desc or selected_model or "model_call"),
                    ok=ok,
                    wall_s=time.perf_counter() - started_wall,
                    process_cpu_s=time.process_time() - started_cpu,
                    meta={
                        "provider": provider,
                        "model": str(selected_model or ""),
                        "message_count": len(messages),
                        "timeout": timeout,
                    },
                    started_at=started_at,
                    finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception:
                import logging as _wla_logging
                _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)
