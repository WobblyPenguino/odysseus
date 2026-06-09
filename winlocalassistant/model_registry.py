from __future__ import annotations

"""Local model registry and role-routing report for Nova."""

import shutil
import subprocess
from dataclasses import asdict, dataclass
from typing import Any


@dataclass(slots=True)
class ModelRole:
    role: str
    preferred: str
    installed: bool
    fallback: str = ""
    note: str = ""


def _ollama_models() -> list[str]:
    exe = shutil.which("ollama")
    if not exe:
        return []
    try:
        cp = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=20)
        models = []
        for line in (cp.stdout or "").splitlines()[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except Exception:
        return []


def build_model_registry(installed: list[str] | None = None) -> dict[str, Any]:
    installed = installed if installed is not None else _ollama_models()
    installed_set = set(installed)
    roles = [
        ModelRole("code", "qwen3-coder:30b", "qwen3-coder:30b" in installed_set, "qwen3-coder:30b", "primary coding/build model for upgraded PC"),
        ModelRole("chat", "qwen3-coder:30b", "qwen3-coder:30b" in installed_set, "gemma2:2b", "use fast fallback only for short chat"),
        ModelRole("planner", "qwen3-coder:30b", "qwen3-coder:30b" in installed_set, "qwen3-coder:30b", "planning/review should use the strongest local model"),
        ModelRole("fast", "gemma2:2b", "gemma2:2b" in installed_set, "qwen3-coder:30b", "low-latency fallback"),
        ModelRole("vision", "llama3.2-vision:11b", "llama3.2-vision:11b" in installed_set, "", "image analysis only"),
        ModelRole("embedding", "nomic-embed-text:latest", "nomic-embed-text:latest" in installed_set, "", "RAG embeddings only, never chat/code"),
    ]
    missing = list(dict.fromkeys(role.preferred for role in roles if role.preferred and not role.installed))
    return {
        "ok": not any(role.role in {"code", "chat", "planner"} and not role.installed for role in roles),
        "installed_models": installed,
        "roles": [asdict(role) for role in roles],
        "missing_models": missing,
        "safety_rules": [
            "embedding models are not valid chat/code models",
            "vision models are only selected for image tasks",
            "role routing should prefer local Ollama unless a configured remote provider is explicitly enabled",
        ],
    }


def render_model_registry(payload: dict[str, Any]) -> str:
    lines = ["# Nova Local Model Registry", "", f"Status: {'PASS' if payload.get('ok') else 'REVIEW'}", "", "## Roles"]
    for role in payload.get("roles", []):
        mark = "✅" if role.get("installed") else "⚠️"
        lines.append(f"- {mark} **{role.get('role')}**: `{role.get('preferred')}` fallback=`{role.get('fallback')}` — {role.get('note')}")
    if payload.get("missing_models"):
        lines += ["", "## Missing", *[f"- `ollama pull {m}`" for m in payload.get("missing_models", [])]]
    lines += ["", "## Safety rules", *[f"- {r}" for r in payload.get("safety_rules", [])]]
    return "\n".join(lines)
