from __future__ import annotations

import json
import re
import shutil
import subprocess
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


@dataclass(frozen=True)
class OllamaModelSpec:
    key: str
    model: str
    title: str
    purpose: str
    use_when: tuple[str, ...]
    avoid_when: tuple[str, ...]
    approximate_size: str
    risk: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


MODEL_CATALOG: dict[str, OllamaModelSpec] = {
    "coder7b": OllamaModelSpec(
        key="coder7b",
        model="qwen2.5-coder:7b",
        title="Qwen2.5 Coder 7B",
        purpose="Default Nova coding, file generation, repair, JSON plans and validation-aware edits.",
        use_when=("building or repairing code", "local model output needs stronger coding behaviour", "default Nova coder model is missing"),
        avoid_when=("very low RAM/VRAM machine and tiny chat-only task",),
        approximate_size="~5GB download/model storage",
    ),
    "chat3b": OllamaModelSpec(
        key="chat3b",
        model="gemma2:2b",
        title="Llama 3.2 3B Chat",
        purpose="Fast local chat, status explanation, short planning and non-code replies.",
        use_when=("normal conversation", "summaries", "low latency chat fallback"),
        avoid_when=("large code generation or deep repair task",),
        approximate_size="~2GB download/model storage",
    ),
    "smallfast": OllamaModelSpec(
        key="smallfast",
        model="gemma2:2b",
        title="Gemma 2 2B fast fallback",
        purpose="Very small fallback model for quick replies on slower machines.",
        use_when=("primary chat model is slow", "fast draft response is acceptable"),
        avoid_when=("complex project generation", "strict JSON coding output"),
        approximate_size="~1.6GB download/model storage",
    ),
    "coder14b": OllamaModelSpec(
        key="coder14b",
        model="qwen2.5-coder:14b",
        title="Qwen2.5 Coder 14B",
        purpose="Optional stronger coding model for better project generation and surgical repair on capable hardware.",
        use_when=("new PC or >10GB VRAM/RAM headroom", "7B coder repeatedly fails candidate validation"),
        avoid_when=("GTX 1650-class 4GB VRAM machine", "quick tiny app when 7B is adequate"),
        approximate_size="~9GB+ download/model storage",
        risk="medium",
    ),
    "vision": OllamaModelSpec(
        key="vision",
        model="llama3.2-vision:11b",
        title="Llama 3.2 Vision 11B",
        purpose="Optional image/photo understanding for uploaded screenshots and visual repair context.",
        use_when=("image analysis is requested", "GUI screenshot diagnosis", "visual project repair"),
        avoid_when=("no image tasks", "low VRAM/disk headroom"),
        approximate_size="large download/model storage",
        risk="medium",
    ),
    "embed": OllamaModelSpec(
        key="embed",
        model="nomic-embed-text",
        title="Nomic Embed Text",
        purpose="Optional local embeddings for future document/search memory improvements.",
        use_when=("semantic project memory/search is enabled", "local docs index should support embeddings"),
        avoid_when=("keyword search is sufficient",),
        approximate_size="~300MB download/model storage",
    ),
}

ALIASES: dict[str, str] = {
    "code": "coder7b",
    "coder": "coder7b",
    "qwen": "coder7b",
    "chat": "chat3b",
    "llama": "chat3b",
    "fast": "smallfast",
    "gemma": "smallfast",
    "strong-coder": "coder14b",
    "coder14": "coder14b",
    "image": "vision",
    "photo": "vision",
    "screenshot": "vision",
    "embedding": "embed",
    "embeddings": "embed",
}


def normalise_model_key(name: str) -> str:
    raw = (name or "").strip().lower()
    if raw in MODEL_CATALOG:
        return raw
    if raw in ALIASES:
        return ALIASES[raw]
    for key, spec in MODEL_CATALOG.items():
        if raw == spec.model.lower() or raw == spec.title.lower():
            return key
    return raw


def _ollama_exists() -> bool:
    return bool(shutil.which("ollama") or shutil.which("ollama.exe"))


def _run(command: list[str], root: Path | str = ".", timeout: int = 300) -> dict[str, Any]:
    try:
        cp = subprocess.run(command, cwd=Path(root), text=True, capture_output=True, timeout=timeout, shell=False)
        return {"ok": cp.returncode == 0, "returncode": cp.returncode, "command": command, "stdout": cp.stdout[-5000:], "stderr": cp.stderr[-5000:]}
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": 127, "command": command, "stdout": "", "stderr": str(exc)}
    except subprocess.TimeoutExpired as exc:
        out = exc.stdout if isinstance(exc.stdout, str) else ""
        err = exc.stderr if isinstance(exc.stderr, str) else ""
        return {"ok": False, "returncode": 124, "command": command, "stdout": out[-5000:], "stderr": (err or f"Timed out after {timeout}s")[-5000:]}


def installed_ollama_models() -> dict[str, Any]:
    if not _ollama_exists():
        return {"ok": False, "available": False, "models": [], "raw": "", "summary": "Ollama CLI not found"}
    result = _run(["ollama", "list"], timeout=45)
    models: list[str] = []
    if result.get("ok"):
        for line in str(result.get("stdout") or "").splitlines()[1:]:
            parts = line.split()
            if parts:
                models.append(parts[0])
    return {"ok": bool(result.get("ok")), "available": True, "models": models, "raw": result.get("stdout") or result.get("stderr") or "", "summary": "Ollama models listed" if result.get("ok") else "Could not list Ollama models"}


def recommend_models_for_goal(goal: str = "", current_coder: str = "qwen3-coder:30b", current_chat: str = "gemma2:2b") -> list[dict[str, Any]]:
    low = (goal or "").lower()
    keys: list[str] = []
    if any(w in low for w in ("code", "app", "build", "repair", "fix", "file", "json", "candidate", "surgical", "edit")):
        keys.append("coder7b")
    if any(w in low for w in ("chat", "story", "explain", "summary", "conversation", "talk")):
        keys.append("chat3b")
    if any(w in low for w in ("image", "photo", "screenshot", "vision", "gui screenshot", "visual")):
        keys.append("vision")
    if any(w in low for w in ("semantic", "embedding", "search memory", "docs index", "knowledge base")):
        keys.append("embed")
    if any(w in low for w in ("new pc", "stronger", "better coder", "14b", "large model")):
        keys.append("coder14b")
    if not keys:
        keys = ["coder7b", "chat3b"]
    # Current configured models should still be represented even if custom.
    recommendations = []
    for key in dict.fromkeys(keys):
        spec = MODEL_CATALOG[key]
        recommendations.append({**spec.to_dict(), "required": key in {"coder7b", "chat3b"}, "install_command": ["ollama", "pull", spec.model]})
    for custom, title in [(current_coder, "Configured coding model"), (current_chat, "Configured chat model")]:
        if custom and custom not in [r["model"] for r in recommendations]:
            recommendations.append({"key": custom, "model": custom, "title": title, "purpose": "Configured in Nova settings.", "use_when": ["Nova is configured to use it"], "avoid_when": [], "approximate_size": "unknown", "risk": "low", "required": True, "install_command": ["ollama", "pull", custom]})
    return recommendations


def build_model_readiness(goal: str = "", root: str | Path = ".", current_coder: str = "qwen3-coder:30b", current_chat: str = "gemma2:2b") -> dict[str, Any]:
    installed = installed_ollama_models()
    installed_names = set(installed.get("models") or [])
    recs = recommend_models_for_goal(goal, current_coder=current_coder, current_chat=current_chat)
    items = []
    missing_required = []
    missing_optional = []
    for rec in recs:
        present = rec["model"] in installed_names
        item = {**rec, "installed": present, "install_command_text": " ".join(rec["install_command"])}
        items.append(item)
        if not present and rec.get("required"):
            missing_required.append(item)
        elif not present:
            missing_optional.append(item)
    ok = bool(installed.get("available")) and not missing_required
    return {
        "ok": ok,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "goal": goal,
        "root": str(root),
        "ollama": installed,
        "items": items,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "summary": "Required local models are ready" if ok else "Required local models need attention or download approval",
        "next_step": "Run /model-install NAME --confirm only after reviewing the exact ollama pull command." if missing_required or missing_optional else "No model download needed for this goal.",
    }


def render_model_readiness(report: dict[str, Any]) -> str:
    lines = ["Nova Model Requirement and Download Planner", "", f"Goal: {report.get('goal') or '(general Nova use)'}", f"Status: {'PASS' if report.get('ok') else 'ATTENTION'}", f"Summary: {report.get('summary')}", ""]
    ollama = report.get("ollama") or {}
    lines.append(f"Ollama CLI: {'available' if ollama.get('available') else 'not found'}")
    if ollama.get("models"):
        lines.append("Installed models: " + ", ".join(ollama.get("models") or []))
    elif ollama.get("raw"):
        lines.append("Installed models: none detected from `ollama list`")
    lines.append("")
    lines.append("## Recommended models")
    for item in report.get("items", []):
        flag = "✅" if item.get("installed") else ("❌" if item.get("required") else "⚪")
        required = "required" if item.get("required") else "optional"
        lines.append(f"- {flag} **{item.get('title')}** (`{item.get('model')}`) — {required}; risk {item.get('risk')}")
        lines.append(f"  - Purpose: {item.get('purpose')}")
        lines.append(f"  - Size: {item.get('approximate_size')}")
        lines.append(f"  - Install: `{item.get('install_command_text')}`")
    lines.append("")
    lines.append("## Safe download rule")
    lines.append("Nova may request a missing model, but it only downloads through `/model-install NAME --confirm` after showing the exact command.")
    lines.append(f"Next step: {report.get('next_step')}")
    return "\n".join(lines)


def install_model(name: str, root: str | Path = ".", confirm: bool = False, timeout: int = 1800) -> dict[str, Any]:
    key = normalise_model_key(name)
    spec = MODEL_CATALOG.get(key)
    if spec is None:
        # Permit exact model names only if they look like a local Ollama tag, not shell text.
        raw = (name or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]+(?::[A-Za-z0-9_.-]+)?", raw):
            return {"ok": False, "summary": f"Unknown or unsafe model name: {name}", "available": sorted(MODEL_CATALOG)}
        spec = OllamaModelSpec(key=raw, model=raw, title=f"Custom Ollama model {raw}", purpose="User-specified Ollama model tag.", use_when=("user explicitly requested this model",), avoid_when=(), approximate_size="unknown", risk="medium")
    command = ["ollama", "pull", spec.model]
    result: dict[str, Any] = {"ok": True, "dry_run": not confirm, "model": spec.to_dict(), "command": command, "command_text": " ".join(command), "summary": "Dry run only; add --confirm to download the model."}
    if not confirm:
        return result
    if not _ollama_exists():
        result.update({"ok": False, "summary": "Ollama CLI not found; install/start Ollama before downloading models."})
        return result
    pull = _run(command, root=root, timeout=timeout)
    result["pull"] = pull
    result["ok"] = bool(pull.get("ok"))
    result["summary"] = "Model downloaded successfully" if result["ok"] else "Model download failed or timed out"
    out = Path(root) / "docs"
    out.mkdir(exist_ok=True)
    safe_key = re.sub(r"[^A-Za-z0-9_.-]+", "_", spec.model)
    json_path = out / f"MODEL_INSTALL_{safe_key}_LATEST.json"
    md_path = out / f"MODEL_INSTALL_{safe_key}_LATEST.md"
    atomic_write_json(json_path, result)
    atomic_write_text(md_path, render_model_install_result(result))
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(md_path)
    return result


def render_model_install_result(result: dict[str, Any]) -> str:
    model = result.get("model") or {}
    lines = ["Nova Model Install", "", f"Model: `{model.get('model')}`", f"Status: {'PASS' if result.get('ok') else 'ATTENTION'}", f"Summary: {result.get('summary')}", f"Command: `{result.get('command_text')}`"]
    if result.get("dry_run"):
        lines.append("")
        lines.append("Dry run only. Nothing was downloaded. Re-run with `--confirm` after reviewing the command.")
    pull = result.get("pull") or {}
    if pull:
        lines += ["", "## ollama pull", f"Return code: {pull.get('returncode')}"]
        if pull.get("stdout"):
            lines += ["stdout:", "```text", str(pull.get("stdout"))[-2000:], "```"]
        if pull.get("stderr"):
            lines += ["stderr:", "```text", str(pull.get("stderr"))[-2000:], "```"]
    return "\n".join(lines)
