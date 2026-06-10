from __future__ import annotations

import json
import re
import time
from dataclasses import dataclass
from functools import lru_cache
from hashlib import sha256
from pathlib import Path
from typing import Any

from .config import APP_DIR, AssistantConfig
from .response_quality import response_contract_for_intents
from .safe_io import tail_jsonl_rows

CONTEXT_HEADER = "WINLOCALASSISTANT CONTEXT PACK"


@dataclass
class ContextPack:
    purpose: str
    text: str
    metadata: dict[str, Any]


def _safe_read_text(path: Path, limit: int = 6000) -> str:
    try:
        if not path.exists() or not path.is_file():
            return ""
        text = path.read_text(encoding="utf-8", errors="replace")
        if len(text) > limit:
            return text[:limit] + "\n...[truncated]"
        return text
    except Exception:
        return ""


def _tail_jsonl(path: Path, limit: int = 8) -> list[dict[str, Any]]:
    return tail_jsonl_rows(path, max(1, int(limit)), multiplier=3)


def _first_json_file(folder: Path, patterns: list[str]) -> Path | None:
    candidates: list[Path] = []
    for pattern in patterns:
        try:
            candidates.extend(folder.glob(pattern))
        except Exception:
            continue
    candidates = [p for p in candidates if p.is_file()]
    if not candidates:
        return None
    try:
        return max(candidates, key=lambda p: p.stat().st_mtime)
    except Exception:
        return candidates[-1]


def _resolve_prompt_named_file(match: str, workspace: Path) -> Path | None:
    """Resolve a file name from the prompt to an absolute path inside the workspace.

    Returns the resolved Path if it is within the workspace and exists as a file,
    otherwise returns None.
    """
    candidate = (workspace / match).resolve()
    try:
        # Ensure the candidate is inside the workspace
        if workspace.resolve() in candidate.parents or candidate == workspace.resolve():
            if candidate.exists() and candidate.is_file():
                return candidate
    except Exception:
        pass
    return None


def _prompt_named_files(prompt: str, workspace: Path) -> list[tuple[str, str]]:
    """Return a list of (filename, preview) for small top‑level files explicitly named in the prompt."""
    named_files = []
    for match in re.findall(r"[A-Za-z0-9_./\\-]+\.(?:py|js|ts|html|css|md|json|txt|bat|ps1|yaml|yml)", prompt or ""):
        candidate = _resolve_prompt_named_file(match, workspace)
        if candidate is not None:
            named_files.append((match, _safe_read_text(candidate, limit=2200)))
    return named_files


def _prompt_named_file_signature(prompt: str, workspace: Path) -> str:
    """Return a hash that changes when any prompt‑named file content changes."""
    named = []
    for match in re.findall(r"[A-Za-z0-9_./\\-]+\.(?:py|js|ts|html|css|md|json|txt|bat|ps1|yaml|yml)", prompt or ""):
        candidate = _resolve_prompt_named_file(match, workspace)
        if candidate is not None:
            # Use full content for signature to detect any change
            text = candidate.read_text(encoding="utf-8", errors="replace")
            named.append((match, text))
    # Sort to ensure deterministic order
    named.sort(key=lambda x: x[0])
    sig_str = "".join(f"{name}:{content}" for name, content in named)
    return sha256(sig_str.encode("utf-8")).hexdigest()


def _workspace_summary(workspace: Path, prompt: str) -> dict[str, Any]:
    summary: dict[str, Any] = {"path": str(workspace), "exists": workspace.exists()}
    if not workspace.exists() or not workspace.is_dir():
        return summary
    try:
        entries = sorted([p for p in workspace.iterdir()], key=lambda p: (not p.is_dir(), p.name.lower()))[:80]
        summary["top_level"] = [p.name + ("/" if p.is_dir() else "") for p in entries]
    except Exception as exc:
        summary["top_level_error"] = repr(exc)
    project_markers = ["package.json", "pyproject.toml", "requirements.txt", "pytest.ini", "index.html", "app.py", "README.md", "PROJECT_BUILD_BRIEF.md", "PROJECT_BUILD_BRIEF.json"]
    found = []
    for name in project_markers:
        p = workspace / name
        if p.exists():
            found.append(name)
    summary["project_markers"] = found
    # Include tiny previews only for high-value local project context files.
    previews: dict[str, str] = {}
    for name in ["README.md", "PROJECT_BUILD_BRIEF.md", "PROJECT_BUILD_BRIEF.json", "AUTONOMOUS_IMPROVEMENTS.md"]:
        p = workspace / name
        text = _safe_read_text(p, limit=1600)
        if text:
            previews[name] = text
    if previews:
        summary["previews"] = previews
    # If the prompt names a file, include a compact preview when it is in workspace.
    named_files = _prompt_named_files(prompt, workspace)
    if named_files:
        summary["named_file_previews"] = {name: text for name, text in named_files[:4] if text}
    return summary


def _active_file_contexts() -> list[dict[str, Any]]:
    try:
        from .file_context import list_file_contexts

        rows = []
        for ctx in list_file_contexts(limit=6):
            rows.append({
                "id": ctx.context_id,
                "name": ctx.original_name,
                "kind": ctx.kind,
                "size_bytes": ctx.size_bytes,
                "summary": ctx.summary,
                "image_hint": f"Use /image-analyze context:{ctx.context_id} => PROMPT analyzes an uploaded image/photo" if ctx.kind == "image" else "",
            })
        return rows
    except Exception:
        return []


def _assistant_box_state() -> dict[str, Any] | None:
    try:
        from .assistant_box import read_assistant_box

        state = read_assistant_box()
        if not isinstance(state, dict):
            return None
        msg = str(state.get("message") or "")
        if len(msg) > 1200:
            state = dict(state)
            state["message"] = msg[:1200] + "\n...[truncated]"
        return state
    except Exception:
        return None


def _recent_audits(workspace: Path) -> list[dict[str, Any]]:
    folders = [workspace / "repair_audits", workspace / "code_reviews", APP_DIR / "repair_audits", APP_DIR / "code_reviews"]
    found: list[dict[str, Any]] = []
    for folder in folders:
        if not folder.exists() or not folder.is_dir():
            continue
        try:
            files = sorted(folder.glob("*.md"), key=lambda p: p.stat().st_mtime, reverse=True)[:2]
        except Exception:
            files = []
        for p in files:
            text = _safe_read_text(p, limit=1400)
            if text:
                found.append({"path": str(p), "preview": text})
    return found[:3]


def _recent_activity() -> list[dict[str, Any]]:
    activity_path = APP_DIR / "activity.jsonl"
    rows = _tail_jsonl(activity_path, limit=8)
    compact = []
    for row in rows:
        compact.append({
            "time": row.get("time") or row.get("ts") or "",
            "kind": row.get("kind") or row.get("event") or row.get("type") or "",
            "message": str(row.get("message") or row.get("summary") or row.get("detail") or "")[:300],
            "data": _compact_json_value(row.get("data"), 600),
        })
    return compact


def _compact_json_value(value: Any, limit: int = 1000) -> Any:
    try:
        text = json.dumps(value, ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    if len(text) <= limit:
        try:
            return json.loads(text)
        except Exception:
            return text
    return text[:limit] + "...[truncated]"


def _intent_tags(prompt: str, desc: str) -> list[str]:
    text = (prompt + " " + desc).lower()
    tags = []
    checks = {
        "autonomous": ["autonomous", "cycle", "heartbeat", "self improve", "idle"],
        "project_build": ["build", "create", "app", "website", "game", "project", "files", "json schema"],
        "code_debug": ["code", "traceback", "bug", "fix", "repair", "test", "pytest", "compile", ".py", ".js"],
        "file_context": ["uploaded", "attached", "file", "photo", "image", "screenshot", "context"],
        "math_science": ["math", "solve", "equation", "science", "chemistry", "physics", "units"],
        "communication": ["rewrite", "email", "letter", "communicate", "answer", "paragraph"],
    }
    for tag, words in checks.items():
        if any(w in text for w in words):
            tags.append(tag)
    return tags or ["general"]


def _prompt_excerpt(messages: list[dict[str, str]], limit: int = 2800) -> str:
    parts = []
    for m in messages[-4:]:
        role = m.get("role", "user")
        content = str(m.get("content") or "")
        parts.append(f"{role}: {content}")
    text = "\n\n".join(parts)
    return text[-limit:]


@lru_cache(maxsize=64)
def _build_model_context_pack_cached(
    workspace: str,
    workspace_mtime: float,
    prompt_excerpt: str,
    desc: str,
    max_chars: int,
    local_model_context_enabled: bool,
    local_model_context_max_chars: int,
    allow_internet: bool,
    model: str,
    chat_model: str,
    planner_model: str,
    model_provider: str,
    skill_mode: str,
    prompt_named_file_signature: str,
) -> ContextPack:
    config = AssistantConfig(
        workspace=workspace,
        allow_mutating_tools=False,
        allow_internet=allow_internet,
        ollama_url="http://127.0.0.1:11434",
        model=model,
        chat_model=chat_model,
        planner_model=planner_model,
        model_route="auto",
        skill_mode=skill_mode,
        model_provider=model_provider,
        openrouter_url="https://openrouter.ai/api/v1",
        openrouter_model="",
        openrouter_key_env="OPENROUTER_API_KEY",
        vision_model="",
        command_timeout_sec=120,
        local_model_timeout_sec=0,
        local_model_context_enabled=local_model_context_enabled,
        local_model_context_max_chars=local_model_context_max_chars,
        efficiency_profiler_enabled=False,
        efficiency_cpu_watts=0.0,
        efficiency_gpu_watts=0.0,
        efficiency_model_extra_watts=0.0,
    )
    intent_tags = _intent_tags(prompt_excerpt, desc)
    payload = {
        "identity": "Nova (Nova), a local-first Windows assistant for chat, coding, project generation, autonomous diagnostics, file/photo context and local tools.",
        "purpose": desc or "model call",
        "intent_tags": intent_tags,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "model_roles": {
            "build_model": model,
            "chat_model": chat_model,
            "planner_model": planner_model,
            "provider": model_provider,
            "skill_mode": skill_mode,
        },
        "response_quality_contract": response_contract_for_intents(intent_tags),
        "workspace": _workspace_summary(Path(workspace), prompt_excerpt),
        "active_file_contexts": _active_file_contexts(),
        "assistant_message_box": _assistant_box_state(),
        "recent_activity": _recent_activity(),
        "recent_audits": _recent_audits(Path(workspace)),
        "command_capabilities": [
            "/project-spec GOAL creates a deterministic implementation brief before build",
            "/code-review and /repair-audit inspect Nova/project reliability before mutation",
            "/context-files lists uploaded files/photos and IDs",
            "/image-analyze context:ID => PROMPT analyzes an uploaded image/photo",
            "/autonomous plan|once|start --cycles N [--diagnostic] GOAL controls autonomous cycles",
            "/comm-box MESSAGE writes to the GUI AI communication box",
            "/model-health and /llm-status diagnose local model readiness",
        ],
        "operating_rules": [
            "Use this context only when relevant to the user's prompt; do not dump it back to the user.",
            "Do not claim a tool/file/action happened unless the prompt includes a result or the tool actually ran.",
            "For project builds, satisfy the user's exact domain and acceptance terms, not a generic demo.",
            "For JSON-only prompts, return only the requested valid JSON schema.",
            "When unsure, state assumptions and give concrete verification commands.",
        ],
    }
    text = CONTEXT_HEADER + "\n" + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        payload["recent_audits"] = payload.get("recent_audits", [])[:1]
        payload["recent_activity"] = payload.get("recent_activity", [])[-4:]
        ws = dict(payload.get("workspace") or {})
        if isinstance(ws.get("previews"), dict):
            ws["previews"] = {k: str(v)[:800] + ("...[truncated]" if len(str(v)) > 800 else "") for k, v in ws["previews"].items()}
        if isinstance(ws.get("named_file_previews"), dict):
            ws["named_file_previews"] = {k: str(v)[:900] + ("...[truncated]" if len(str(v)) > 900 else "") for k, v in ws["named_file_previews"].items()}
        payload["workspace"] = ws
        text = CONTEXT_HEADER + "\n" + json.dumps(payload, ensure_ascii=False, indent=2, default=str)
    if len(text) > max_chars:
        text = text[:max_chars] + "\n...[context pack truncated]"
    return ContextPack(purpose=desc or "model call", text=text, metadata={"tags": payload["intent_tags"], "max_chars": max_chars, "workspace": workspace})


def build_model_context_pack(config: AssistantConfig, messages: list[dict[str, str]], desc: str = "model call", max_chars: int | None = None) -> ContextPack:
    """Build a compact, relevant Nova context block for local model calls.

    The pack is deliberately bounded and factual. It is a context aid, not a new
    user request, so it tells the model to use only relevant details and to keep
    JSON-only calls JSON-only.
    """
    prompt_excerpt = _prompt_excerpt(messages)
    workspace = Path(getattr(config, "workspace", ".") or ".").expanduser().resolve()
    max_chars = int(max_chars or getattr(config, "local_model_context_max_chars", 9000) or 9000)
    workspace_mtime = 0.0
    try:
        if workspace.exists():
            workspace_mtime = workspace.stat().st_mtime
    except Exception:
        workspace_mtime = 0.0
    # Compute signature of any prompt‑named files to invalidate cache when they change
    prompt_named_file_signature = _prompt_named_file_signature(prompt_excerpt, workspace)
    return _build_model_context_pack_cached(
        str(workspace),
        workspace_mtime,
        prompt_excerpt,
        desc or "model call",
        max_chars,
        bool(getattr(config, "local_model_context_enabled", True)),
        int(getattr(config, "local_model_context_max_chars", 9000) or 9000),
        bool(getattr(config, "allow_internet", False)),
        str(getattr(config, "model", "") or ""),
        str(getattr(config, "chat_model", "") or ""),
        str(getattr(config, "planner_model", "") or getattr(config, "model", "") or ""),
        str(getattr(config, "model_provider", "ollama") or "ollama"),
        str(getattr(config, "skill_mode", "auto") or "auto"),
        prompt_named_file_signature,
    )


def enrich_messages_with_context(config: AssistantConfig, messages: list[dict[str, str]], desc: str = "model call") -> list[dict[str, str]]:
    enabled = bool(getattr(config, "local_model_context_enabled", True))
    if not enabled:
        return messages
    # Avoid duplicate packs when callers intentionally provide one.
    joined = "\n".join(str(m.get("content") or "") for m in messages[:2])
    if CONTEXT_HEADER in joined:
        return messages
    pack = build_model_context_pack(config, messages, desc=desc)
    return [{"role": "system", "content": pack.text}] + list(messages)


def render_model_context_preview(config: AssistantConfig, prompt: str = "") -> str:
    messages = [{"role": "user", "content": prompt or "general Nova context preview"}]
    pack = build_model_context_pack(config, messages, desc="manual context preview")
    return "# Local Model Context Pack Preview\n\n" + pack.text
