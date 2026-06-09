from __future__ import annotations

import json
import logging
import os
import platform
import re
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any
from urllib.error import URLError
from urllib.request import Request, urlopen

from .safe_io import atomic_write_json, atomic_write_text, open_binary_append_handle, read_json_file, unique_path

LOGGER = logging.getLogger(__name__)

ODYSSEUS_SOURCE = "uploaded odysseus-main.zip and public README feature map"
SUITE_VERSION = "v55.3.137"

RUNTIME_DIRNAME = ".nova_runtime"
SUITE_DIRNAME = "odysseus_suite"

PRIVILEGE_LEVELS = ("allow", "ask", "block", "admin")
ODYSSEUS_DEFAULT_HOST = "127.0.0.1"
ODYSSEUS_DEFAULT_PORT = 7000
ODYSSEUS_LAUNCH_MODES = ("auto", "native", "windows_launcher", "docker")

ODYSSEUS_FEATURES: list[dict[str, Any]] = [
    {
        "id": "chat",
        "name": "Chat / provider switching",
        "odysseus_surface": "Chat with local or API models: vLLM, llama.cpp, Ollama, OpenRouter, OpenAI.",
        "nova_command": "/providers, /provider, /ollama-multi, /openrouter-model",
        "status": "native_plus_mapped",
        "nova_adaptation": "Nova keeps its existing provider commands and exposes this suite as the feature coverage audit.",
    },
    {
        "id": "agent_tools",
        "name": "Agent tools + guarded autonomy",
        "odysseus_surface": "Agent with MCP, web, files, shell, skills and memory tools.",
        "nova_command": "/autonomous, /nova-self-apply, /nova-tool-permissions",
        "status": "native_plus_new_gate",
        "nova_adaptation": "Nova already has autonomous/tool routing; this patch adds an Odysseus-style privilege policy table and command checker.",
    },
    {
        "id": "cookbook",
        "name": "Hardware-aware model cookbook",
        "odysseus_surface": "Hardware scan, VRAM-aware fit scoring, model recommendations and serving/download planning.",
        "nova_command": "/nova-cookbook",
        "status": "implemented",
        "nova_adaptation": "Nova now detects RAM/CPU/NVIDIA VRAM where available, accepts what-if hardware hints, ranks local model choices and prints install/serve guidance without auto-downloading.",
    },
    {
        "id": "deep_research",
        "name": "Deep research reports",
        "odysseus_surface": "Multi-step source gathering, reading and synthesis into a report.",
        "nova_command": "/research, /nova-deep-research, /nova-odysseus-suite",
        "status": "native_plus_mapped",
        "nova_adaptation": "Nova keeps its existing research engine and documents the Odysseus deep-research target in the suite manifest.",
    },
    {
        "id": "compare",
        "name": "Blind model comparison",
        "odysseus_surface": "Prompt two models side-by-side, hide model names, record winner/tie and reveal after vote.",
        "nova_command": "/nova-compare",
        "status": "implemented",
        "nova_adaptation": "Nova now creates blind comparison packets and stores comparison/vote receipts under the workspace runtime directory.",
    },
    {
        "id": "documents",
        "name": "Documents-first editing",
        "odysseus_surface": "Markdown/HTML/CSV editor with AI suggestions while the user owns the text.",
        "nova_command": "/nova-docs",
        "status": "implemented",
        "nova_adaptation": "Nova now has a workspace document vault with create/list/read/suggest/export commands and explicit AI-suggestion sidecars.",
    },
    {
        "id": "memory_skills",
        "name": "Memory and skills",
        "odysseus_surface": "Persistent memory/skills with vector + keyword retrieval, import/export and audit surfaces.",
        "nova_command": "/nova-memory-vault, /nova-skills, /memory, /remember",
        "status": "implemented",
        "nova_adaptation": "Nova now adds skill library CRUD/export and memory-vault audit/export commands on top of its existing memory commands.",
    },
    {
        "id": "email",
        "name": "Email triage scaffold",
        "odysseus_surface": "IMAP/SMTP inbox with urgency reminders, tags, summaries and reply drafts.",
        "nova_command": "/nova-email-plan",
        "status": "safe_scaffold",
        "nova_adaptation": "Nova now exposes a no-secret integration checklist and triage schema. It does not connect to mail until credentials and explicit consent are configured.",
    },
    {
        "id": "notes_tasks",
        "name": "Notes and tasks",
        "odysseus_surface": "Quick notes, checklist tasks, reminder channels and scheduled agent actions.",
        "nova_command": "/nova-notes, /nova-tasks",
        "status": "implemented",
        "nova_adaptation": "Nova now stores notes/tasks as workspace JSON with add/list/search/done/export operations.",
    },
    {
        "id": "calendar",
        "name": "Calendar scaffold",
        "odysseus_surface": "Local-first calendar, CalDAV sync, .ics import/export and agent-aware events.",
        "nova_command": "/nova-calendar-plan",
        "status": "safe_scaffold",
        "nova_adaptation": "Nova now provides an .ics-oriented integration plan and event schema without silently syncing external calendars.",
    },
    {
        "id": "mobile_pwa",
        "name": "Mobile/PWA readiness",
        "odysseus_surface": "Responsive, installable and touch-friendly mobile UI.",
        "nova_command": "/nova-mobile-plan",
        "status": "implemented",
        "nova_adaptation": "Nova now has a mobile/PWA readiness checklist plus a served manifest, icon and conservative static-shell service worker for workbench routes.",
    },
    {
        "id": "extras",
        "name": "Extras: uploads, vision, image, themes, sessions, web search, presets, 2FA style hardening",
        "odysseus_surface": "Image editor, theme editor, uploads, vision/PDF, web search, presets, sessions and two-factor extras.",
        "nova_command": "/attach-file, /image-analyze, /image-generate, /chats, /nova-presets, /nova-theme-plan, /nova-auth-plan",
        "status": "native_plus_scaffold",
        "nova_adaptation": "Nova already has file/image/chat/web search surfaces; this patch adds presets plus theme/auth hardening plans.",
    },
    {
        "id": "backup_vault_webhooks",
        "name": "Backup, vault and webhooks",
        "odysseus_surface": "Backup/vault/API token/webhook admin surfaces.",
        "nova_command": "/nova-integration-gates, /webhook-status",
        "status": "safe_scaffold",
        "nova_adaptation": "Nova now has a privileged-integration gate command that classifies risky actions before implementation or use.",
    },
    {
        "id": "fastapi_workspace_shell",
        "name": "FastAPI workspace shell",
        "odysseus_surface": "Odysseus uses a FastAPI app with route modules, static assets, auth middleware, request timeouts, background jobs and API-first tool surfaces.",
        "nova_command": "/nova-fastapi-plan",
        "status": "implemented_as_plan",
        "nova_adaptation": "Nova now has a staged migration plan that keeps the CLI/core stable while adding optional FastAPI routes for chat, events, files, commands and health checks.",
    },
    {
        "id": "gui_workbench_layout",
        "name": "Odysseus-style GUI workbench layout",
        "odysseus_surface": "Odysseus uses an icon rail, collapsible sidebar, tool launchers, modals/fullscreen workspaces, settings tabs, theme controls and mobile/PWA routing.",
        "nova_command": "/nova-gui-workbench-plan",
        "status": "implemented_as_plan_plus_ui",
        "nova_adaptation": "Nova now exposes an Odysseus-inspired workbench panel in the web UI and a command-level layout plan for converting feature commands into first-class panels.",
    },
    {
        "id": "optional_odysseus_runtime",
        "name": "Optional Odysseus dependency launcher",
        "odysseus_surface": "Odysseus can be run as a separate self-hosted workspace on localhost while Nova stays available.",
        "nova_command": "/nova-odysseus-runtime",
        "status": "implemented",
        "nova_adaptation": "Nova now detects a configured Odysseus checkout, reports runtime health, and exposes confirmed GUI/API controls to start or stop the optional dependency.",
    },
]

DEFAULT_TOOL_POLICY: dict[str, dict[str, str]] = {
    "bash": {"level": "admin", "reason": "shell execution can modify or exfiltrate local files"},
    "python": {"level": "admin", "reason": "arbitrary code execution can mutate files and access secrets"},
    "read_file": {"level": "ask", "reason": "file reads can expose private project or user data"},
    "write_file": {"level": "admin", "reason": "file writes can damage project state without preview/backup"},
    "delete_file": {"level": "admin", "reason": "destructive file operation"},
    "mcp": {"level": "admin", "reason": "external tool bus can expand authority beyond Nova"},
    "memory": {"level": "ask", "reason": "persistent memory changes should be visible and reversible"},
    "skills": {"level": "ask", "reason": "skills alter future agent behavior"},
    "email": {"level": "admin", "reason": "email can expose/send private messages"},
    "calendar": {"level": "admin", "reason": "calendar can expose private schedule or send invitations"},
    "webhook": {"level": "admin", "reason": "webhooks/API tokens can permit remote control"},
    "model_download": {"level": "ask", "reason": "large downloads consume disk/network and can run untrusted model files"},
    "model_serve": {"level": "ask", "reason": "serving models consumes GPU/RAM and can bind network ports"},
    "internet_fetch": {"level": "ask", "reason": "external network access should remain opt-in"},
    "image_generation": {"level": "ask", "reason": "generation uses external/local GPU resources and may write files"},
    "backup": {"level": "ask", "reason": "backup writes archives of local data"},
    "vault": {"level": "admin", "reason": "secret store access is high sensitivity"},
}

MODEL_CATALOG: list[dict[str, Any]] = [
    {"name": "tinyllama:1.1b-chat", "size_b": 1.1, "min_ram_gb": 4, "min_vram_gb": 0, "use": "fast smoke tests / tiny fallback", "backend": "ollama"},
    {"name": "qwen2.5:3b-instruct", "size_b": 3, "min_ram_gb": 8, "min_vram_gb": 2, "use": "general Nova chat on low VRAM", "backend": "ollama"},
    {"name": "phi3.5:3.8b-mini-instruct", "size_b": 3.8, "min_ram_gb": 8, "min_vram_gb": 3, "use": "compact reasoning and summaries", "backend": "ollama"},
    {"name": "qwen2.5-coder:7b-instruct", "size_b": 7, "min_ram_gb": 16, "min_vram_gb": 6, "use": "coding patches and test explanation", "backend": "ollama/llama.cpp"},
    {"name": "mistral:7b-instruct", "size_b": 7, "min_ram_gb": 16, "min_vram_gb": 6, "use": "general chat and planning", "backend": "ollama/llama.cpp"},
    {"name": "llama3.1:8b-instruct", "size_b": 8, "min_ram_gb": 16, "min_vram_gb": 8, "use": "balanced local assistant", "backend": "ollama/llama.cpp"},
    {"name": "qwen2.5:14b-instruct-q4", "size_b": 14, "min_ram_gb": 32, "min_vram_gb": 12, "use": "higher quality planning with 16GB-class GPU", "backend": "llama.cpp/Ollama quant"},
    {"name": "qwen2.5-coder:14b-instruct-q4", "size_b": 14, "min_ram_gb": 32, "min_vram_gb": 12, "use": "stronger coding with 16GB-class GPU", "backend": "llama.cpp/Ollama quant"},
    {"name": "deepseek-r1-distill-qwen:14b-q4", "size_b": 14, "min_ram_gb": 32, "min_vram_gb": 12, "use": "reasoning-heavy local planning", "backend": "llama.cpp/Ollama quant"},
    {"name": "qwen2.5:32b-instruct-q4", "size_b": 32, "min_ram_gb": 64, "min_vram_gb": 24, "use": "high quality local reasoning if RAM/VRAM allows", "backend": "llama.cpp/vLLM"},
    {"name": "llama3.3:70b-instruct-q4", "size_b": 70, "min_ram_gb": 96, "min_vram_gb": 48, "use": "large-model quality on multi-GPU/high-RAM hosts", "backend": "llama.cpp/vLLM"},
]

RISKY_KEYWORDS = {
    "shell": "bash",
    "cmd": "bash",
    "powershell": "bash",
    "python": "python",
    "file": "read_file",
    "write": "write_file",
    "delete": "delete_file",
    "memory": "memory",
    "skill": "skills",
    "email": "email",
    "calendar": "calendar",
    "webhook": "webhook",
    "token": "webhook",
    "mcp": "mcp",
    "download": "model_download",
    "serve": "model_serve",
    "internet": "internet_fetch",
    "web": "internet_fetch",
    "vault": "vault",
    "backup": "backup",
}


def _runtime_dir(root: Path | str) -> Path:
    root = Path(root).resolve()
    path = root / RUNTIME_DIRNAME / SUITE_DIRNAME
    path.mkdir(parents=True, exist_ok=True)
    return path


def _safe_slug(value: str, default: str = "item") -> str:
    slug = re.sub(r"[^A-Za-z0-9_.-]+", "-", (value or default).strip()).strip(".-_").lower()
    return (slug or default)[:80]


def _state_path(root: Path | str, name: str) -> Path:
    return _runtime_dir(root) / f"{_safe_slug(name)}.json"


def _load_state(root: Path | str, name: str, default: Any) -> Any:
    return read_json_file(_state_path(root, name), default, expected_type=type(default), quarantine=True)


def _save_state(root: Path | str, name: str, payload: Any) -> Path:
    return atomic_write_json(_state_path(root, name), payload, ensure_ascii=False)


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _split_arrow(text: str) -> tuple[str, str]:
    if "=>" in text:
        left, right = text.split("=>", 1)
        return left.strip(), right.strip()
    return text.strip(), ""


def _read_ram_gb() -> float:
    try:
        import psutil  # type: ignore
        return round(float(psutil.virtual_memory().total) / (1024 ** 3), 1)
    except Exception:
        LOGGER.debug("Failed to read RAM size with psutil", exc_info=True)
    try:
        if hasattr(os, "sysconf"):
            pages = os.sysconf("SC_PHYS_PAGES")
            page_size = os.sysconf("SC_PAGE_SIZE")
            return round(float(pages * page_size) / (1024 ** 3), 1)
    except Exception:
        LOGGER.debug("Failed to read RAM size with os.sysconf", exc_info=True)
    return 0.0


def _read_nvidia_vram() -> tuple[float, list[str]]:
    exe = shutil.which("nvidia-smi")
    if not exe:
        return 0.0, []
    try:
        proc = subprocess.run(
            [exe, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=4,
            check=False,
        )
    except Exception:
        return 0.0, []
    names: list[str] = []
    total = 0.0
    for line in (proc.stdout or "").splitlines():
        bits = [b.strip() for b in line.split(",")]
        if len(bits) >= 2:
            names.append(bits[0])
            try:
                total += float(bits[1]) / 1024.0
            except ValueError:
                pass
    return round(total, 1), names


def detect_hardware(hints: str = "") -> dict[str, Any]:
    ram_gb = _read_ram_gb()
    vram_gb, gpu_names = _read_nvidia_vram()
    lowered = (hints or "").lower()
    for key in ("ram", "ram_gb", "memory"):
        m = re.search(rf"\b{key}\s*=?\s*(\d+(?:\.\d+)?)", lowered)
        if m:
            ram_gb = float(m.group(1))
            break
    for key in ("vram", "vram_gb", "gpu_vram"):
        m = re.search(rf"\b{key}\s*=?\s*(\d+(?:\.\d+)?)", lowered)
        if m:
            vram_gb = float(m.group(1))
            break
    gpu_hint = ""
    m = re.search(r"gpu\s*=?\s*([A-Za-z0-9 _.-]{3,80})", hints or "")
    if m:
        gpu_hint = m.group(1).strip()
    return {
        "generated_at": _now(),
        "os": platform.platform(),
        "python": platform.python_version(),
        "cpu_count": os.cpu_count() or 0,
        "ram_gb": round(ram_gb, 1),
        "vram_gb": round(vram_gb, 1),
        "gpu_names": gpu_names or ([gpu_hint] if gpu_hint else []),
        "hints_used": hints,
    }


def recommend_models(hardware: dict[str, Any], use_case: str = "") -> dict[str, Any]:
    ram = float(hardware.get("ram_gb") or 0)
    vram = float(hardware.get("vram_gb") or 0)
    use_case_l = (use_case or "").lower()
    ranked = []
    for model in MODEL_CATALOG:
        min_ram = float(model["min_ram_gb"])
        min_vram = float(model["min_vram_gb"])
        ram_fit = 1.0 if not ram else min(1.0, ram / max(min_ram, 1.0))
        vram_fit = 1.0 if min_vram == 0 else (min(1.0, vram / min_vram) if vram else min(0.55, ram / (min_ram * 1.75)))
        score = round((ram_fit * 0.45 + vram_fit * 0.45) * 100, 1)
        if use_case_l and any(word in str(model.get("use", "")).lower() for word in use_case_l.split()):
            score = min(100.0, score + 8.0)
        status = "fits" if score >= 85 else "possible_with_offload" if score >= 60 else "not_recommended"
        ranked.append({**model, "fit_score": score, "status": status})
    ranked.sort(key=lambda item: (item["fit_score"], item["size_b"]), reverse=True)
    return {"generated_at": _now(), "hardware": hardware, "use_case": use_case or "general Nova use", "models": ranked[:8]}


def load_tool_policy(root: Path | str) -> dict[str, Any]:
    stored = _load_state(root, "tool_policy", {})
    policy = dict(DEFAULT_TOOL_POLICY)
    if isinstance(stored, dict):
        for name, item in stored.get("overrides", {}).items() if isinstance(stored.get("overrides"), dict) else []:
            if isinstance(item, dict):
                level = item.get("level")
                if level in PRIVILEGE_LEVELS:
                    policy[_safe_slug(name)] = {"level": level, "reason": str(item.get("reason") or "user override")}
    return {"generated_at": _now(), "policy": policy, "levels": PRIVILEGE_LEVELS, "path": str(_state_path(root, "tool_policy"))}


def update_tool_policy(root: Path | str, tool: str, level: str, reason: str = "user override") -> dict[str, Any]:
    tool = _safe_slug(tool)
    level = (level or "").strip().lower()
    if level not in PRIVILEGE_LEVELS:
        return {"ok": False, "error": f"level must be one of {', '.join(PRIVILEGE_LEVELS)}"}
    stored = _load_state(root, "tool_policy", {"overrides": {}})
    if not isinstance(stored, dict):
        stored = {"overrides": {}}
    overrides = stored.setdefault("overrides", {})
    overrides[tool] = {"level": level, "reason": reason or "user override", "updated_at": _now()}
    path = _save_state(root, "tool_policy", stored)
    return {"ok": True, "tool": tool, "level": level, "path": str(path), "policy": load_tool_policy(root)["policy"].get(tool)}


def classify_action(root: Path | str, text: str) -> dict[str, Any]:
    policy = load_tool_policy(root)["policy"]
    found: list[dict[str, Any]] = []
    lowered = (text or "").lower()
    for key, tool in RISKY_KEYWORDS.items():
        if key in lowered:
            found.append({"keyword": key, "tool": tool, **policy.get(tool, {"level": "ask", "reason": "uncategorised risky surface"})})
    worst = "allow"
    order = {"allow": 0, "ask": 1, "block": 2, "admin": 3}
    for item in found:
        if order.get(item.get("level", "allow"), 0) > order.get(worst, 0):
            worst = item.get("level", "allow")
    return {"generated_at": _now(), "action": text, "decision": worst, "matched_surfaces": found, "requires_confirmation": worst in {"ask", "admin"}, "blocked": worst == "block"}


def build_suite_status(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    modules = [p.name for p in (root / "winlocalassistant").glob("*.py")] if (root / "winlocalassistant").exists() else []
    docs = [p.name for p in (root / "docs").glob("*.md")] if (root / "docs").exists() else []
    covered = sum(1 for f in ODYSSEUS_FEATURES if f["status"] in {"implemented", "native_plus_mapped", "native_plus_new_gate", "native_plus_scaffold", "implemented_as_audit", "safe_scaffold", "implemented_as_plan", "implemented_as_plan_plus_ui"})
    return {
        "ok": True,
        "generated_at": _now(),
        "source": ODYSSEUS_SOURCE,
        "suite_version": SUITE_VERSION,
        "root": str(root),
        "coverage": {"covered": covered, "total": len(ODYSSEUS_FEATURES), "percent": round(covered / len(ODYSSEUS_FEATURES) * 100, 1)},
        "features": ODYSSEUS_FEATURES,
        "signals": {
            "nova_modules": len(modules),
            "docs_markdown": len(docs),
            "has_verified_self_apply": "nova_verified_changes.py" in modules,
            "has_eval_packs": "nova_eval_packs.py" in modules,
            "has_research_lab": "nova_deep_research_lab.py" in modules,
            "has_file_context": "file_context.py" in modules,
        },
        "primary_commands": [
            "/nova-odysseus-suite",
            "/nova-odysseus-runtime",
            "/nova-tool-permissions",
            "/nova-cookbook",
            "/nova-compare",
            "/nova-docs",
            "/nova-notes",
            "/nova-tasks",
            "/nova-skills",
            "/nova-presets",
            "/nova-memory-vault",
            "/nova-integration-gates",
            "/nova-fastapi-plan",
            "/nova-gui-workbench-plan",
        ],
    }


CODE_WORKSPACE_SUFFIXES = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".json", ".md"}


def _recent_code_files(root: Path | str, limit: int = 18) -> list[dict[str, Any]]:
    root = Path(root).resolve()
    candidates: list[Path] = []
    for path in [root / "app.py", root / "webui_extracted.js"]:
        if path.exists() and path.is_file():
            candidates.append(path)
    for directory in ["winlocalassistant", "playwright"]:
        base = root / directory
        if base.exists() and base.is_dir():
            candidates.extend(p for p in base.rglob("*") if p.is_file() and p.suffix.lower() in CODE_WORKSPACE_SUFFIXES)
    candidates.extend(p for p in root.glob("tests*.py") if p.is_file())
    seen: set[str] = set()
    rows: list[Path] = []
    for path in candidates:
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
        if "__pycache__" in rel or "/.pytest_cache/" in rel:
            continue
        if rel not in seen:
            seen.add(rel)
            rows.append(path)
    rows.sort(key=lambda p: (p.stat().st_mtime, p.name), reverse=True)
    result = []
    for path in rows[: max(1, limit)]:
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
        result.append(
            {
                "path": rel,
                "name": path.name,
                "suffix": path.suffix.lower(),
                "bytes": path.stat().st_size,
                "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime)),
                "open_api": f"/api/open-file?path={rel}",
            }
        )
    return result


def _item_count(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if isinstance(value, dict):
        return len(value)
    if isinstance(value, list):
        return len(value)
    return 0


def _recent_research_reports(limit: int = 12) -> list[dict[str, Any]]:
    from .research_engine import RESEARCH_DIR

    if not RESEARCH_DIR.exists():
        return []
    rows: list[dict[str, Any]] = []
    for path in sorted(RESEARCH_DIR.glob("research_*.json"), key=lambda p: p.stat().st_mtime, reverse=True)[: max(1, limit)]:
        data = read_json_file(path, {}, expected_type=dict, quarantine=True)
        md_path = path.with_suffix(".md")
        rows.append(
            {
                "topic": str(data.get("topic") or path.stem),
                "created_at": str(data.get("created_at") or time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(path.stat().st_mtime))),
                "json_path": str(path),
                "md_path": str(md_path) if md_path.exists() else "",
                "source_count": len(data.get("sources") or []),
                "claim_count": len(data.get("key_claims") or []),
                "fetch_error_count": len(data.get("fetch_errors") or []),
                "best_source": (data.get("source_scores") or [{}])[0].get("domain") if isinstance(data.get("source_scores"), list) and data.get("source_scores") else "",
            }
        )
    return rows


def _shared_upload_contexts(limit: int = 20) -> list[dict[str, Any]]:
    from .file_context import list_file_contexts

    rows: list[dict[str, Any]] = []
    for ctx in list_file_contexts(limit=limit):
        item = ctx.to_dict()
        item.pop("context_text", None)
        item["id"] = item.get("context_id", "")
        item["name"] = item.get("original_name", "")
        if item.get("kind") == "image":
            item["analyze_command"] = f"/image-analyze context:{item.get('context_id')} => describe this image and any issues"
        rows.append(item)
    return rows


def _coerce_port(value: Any, default: int = ODYSSEUS_DEFAULT_PORT) -> int:
    try:
        port = int(value)
    except (TypeError, ValueError):
        port = default
    return max(1, min(65535, port))


def _coerce_host(value: Any) -> str:
    host = str(value or "").strip()
    if not host:
        return ODYSSEUS_DEFAULT_HOST
    # Keep launcher defaults local-first. Users can still run Odysseus with a
    # wider bind inside Odysseus itself, but Nova should not silently expose it.
    if host in {"localhost", "127.0.0.1", "::1"}:
        return host
    return ODYSSEUS_DEFAULT_HOST


def _odysseus_runtime_state(root: Path | str) -> dict[str, Any]:
    state = _load_state(root, "odysseus_runtime", {})
    return state if isinstance(state, dict) else {}


def _save_odysseus_runtime_state(root: Path | str, state: dict[str, Any]) -> Path:
    return _save_state(root, "odysseus_runtime", state)


def _resolve_odysseus_path(root: Path | str, value: Any) -> Path | None:
    text = str(value or "").strip().strip('"')
    if not text:
        return None
    path = Path(text).expanduser()
    if not path.is_absolute():
        path = Path(root).resolve() / path
    try:
        return path.resolve()
    except Exception:
        return path


def _odysseus_markers(path: Path | None) -> dict[str, Any]:
    if path is None:
        return {"exists": False, "is_dir": False, "valid_checkout": False}
    markers = {
        "exists": path.exists(),
        "is_dir": path.is_dir(),
        "app_py": (path / "app.py").is_file(),
        "requirements": (path / "requirements.txt").is_file(),
        "setup_py": (path / "setup.py").is_file(),
        "launch_windows": (path / "launch-windows.ps1").is_file(),
        "docker_compose": (path / "docker-compose.yml").is_file() or (path / "compose.yml").is_file(),
        "readme": (path / "README.md").is_file(),
    }
    markers["valid_checkout"] = bool(
        markers["is_dir"]
        and (
            (markers["app_py"] and (markers["requirements"] or markers["setup_py"] or markers["launch_windows"]))
            or markers["docker_compose"]
        )
    )
    return markers


def _candidate_odysseus_paths(root: Path | str, state: dict[str, Any]) -> list[dict[str, Any]]:
    root = Path(root).resolve()
    raw_candidates: list[tuple[str, Any]] = [
        ("configured", state.get("path")),
        ("env:NOVA_ODYSSEUS_PATH", os.environ.get("NOVA_ODYSSEUS_PATH")),
        ("workspace/odysseus", root / "odysseus"),
        ("workspace/odysseus-main", root / "odysseus-main"),
        ("workspace-parent/odysseus", root.parent / "odysseus"),
        ("workspace-parent/odysseus-main", root.parent / "odysseus-main"),
    ]
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for source, raw in raw_candidates:
        path = _resolve_odysseus_path(root, raw)
        if path is None:
            continue
        key = str(path).lower()
        if key in seen:
            continue
        seen.add(key)
        markers = _odysseus_markers(path)
        rows.append({"source": source, "path": str(path), "valid": bool(markers.get("valid_checkout")), "markers": markers})
    return rows


def _pid_alive(pid: Any) -> bool:
    try:
        pid_int = int(pid)
    except (TypeError, ValueError):
        return False
    if pid_int <= 0:
        return False
    if os.name == "nt":
        tasklist = shutil.which("tasklist")
        if not tasklist:
            return False
        try:
            proc = subprocess.run(
                [tasklist, "/FI", f"PID eq {pid_int}", "/FO", "CSV", "/NH"],
                capture_output=True,
                text=True,
                timeout=3,
                check=False,
            )
            return str(pid_int) in (proc.stdout or "")
        except Exception:
            return False
    try:
        os.kill(pid_int, 0)
        return True
    except OSError:
        return False


def _http_probe(url: str) -> dict[str, Any]:
    if not url:
        return {"ok": False, "status": 0, "error": "No URL configured."}
    try:
        req = Request(url, method="GET", headers={"User-Agent": "Nova-Odysseus-Launcher/1"})
        with urlopen(req, timeout=1.2) as response:
            return {"ok": 200 <= int(response.status) < 500, "status": int(response.status), "error": ""}
    except URLError as exc:
        return {"ok": False, "status": 0, "error": str(exc.reason if hasattr(exc, "reason") else exc)}
    except Exception as exc:
        return {"ok": False, "status": 0, "error": str(exc)}


def _select_odysseus_mode(path: Path | None, requested: str = "auto") -> str:
    requested = (requested or "auto").strip().lower()
    if requested in set(ODYSSEUS_LAUNCH_MODES) - {"auto"}:
        return requested
    markers = _odysseus_markers(path)
    if os.name == "nt" and markers.get("launch_windows"):
        return "windows_launcher"
    if markers.get("docker_compose") and shutil.which("docker"):
        return "docker"
    return "native"


def _odysseus_python(path: Path) -> str:
    candidates = [
        path / "venv" / "Scripts" / "python.exe",
        path / ".venv" / "Scripts" / "python.exe",
        path / "venv" / "bin" / "python",
        path / ".venv" / "bin" / "python",
    ]
    for candidate in candidates:
        if candidate.exists():
            return str(candidate)
    return shutil.which("python") or sys.executable


def _odysseus_start_command(path: Path, mode: str, host: str, port: int) -> list[str]:
    if mode == "docker":
        docker = shutil.which("docker") or "docker"
        return [docker, "compose", "up", "-d", "--build"]
    if mode == "windows_launcher":
        powershell = shutil.which("powershell.exe") or shutil.which("powershell") or "powershell"
        return [powershell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(path / "launch-windows.ps1")]
    return [_odysseus_python(path), "-m", "uvicorn", "app:app", "--host", host, "--port", str(port)]


def odysseus_dependency_status(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    state = _odysseus_runtime_state(root)
    candidates = _candidate_odysseus_paths(root, state)
    selected = next((item for item in candidates if item["source"] == "configured" and item["valid"]), None)
    if selected is None:
        selected = next((item for item in candidates if item["valid"]), None)
    path = _resolve_odysseus_path(root, selected.get("path") if selected else state.get("path"))
    markers = _odysseus_markers(path)
    host = _coerce_host(state.get("host"))
    port = _coerce_port(state.get("port"))
    url = str(state.get("url") or f"http://{host}:{port}")
    pid = state.get("pid")
    pid_alive = _pid_alive(pid)
    probe = _http_probe(url)
    running = bool(pid_alive or probe.get("ok"))
    mode = _select_odysseus_mode(path, str(state.get("mode") or "auto"))
    status = "running" if running else ("configured" if markers.get("valid_checkout") else "missing")
    notes = []
    if not markers.get("valid_checkout"):
        notes.append("Configure an Odysseus checkout path that contains app.py plus setup/requirements, launch-windows.ps1, or docker-compose.yml.")
    if mode == "native" and markers.get("valid_checkout"):
        notes.append("Native launch expects Odysseus dependencies to already be installed or available in its venv.")
    if mode == "docker":
        notes.append("Docker launch can build/pull images and may take time on the first run.")
    return {
        "ok": True,
        "generated_at": _now(),
        "configured": bool(markers.get("valid_checkout")),
        "status": status,
        "running": running,
        "url": url,
        "host": host,
        "port": port,
        "path": str(path) if path else "",
        "mode": mode,
        "requested_mode": str(state.get("mode") or "auto"),
        "pid": pid,
        "pid_alive": pid_alive,
        "http_probe": probe,
        "markers": markers,
        "candidates": candidates,
        "start_command": _odysseus_start_command(path, mode, host, port) if path and markers.get("valid_checkout") else [],
        "log_path": str(_runtime_dir(root) / "odysseus_launcher.log"),
        "notes": notes,
        "state_path": str(_state_path(root, "odysseus_runtime")),
    }


def _configure_odysseus_dependency(root: Path | str, payload: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
    root = Path(root).resolve()
    path = _resolve_odysseus_path(root, payload.get("path") or state.get("path") or os.environ.get("NOVA_ODYSSEUS_PATH"))
    markers = _odysseus_markers(path)
    if path is None or not markers.get("valid_checkout"):
        return {"ok": False, "mode": "configure", "error": "Odysseus path is not a valid checkout.", "path": str(path) if path else "", "markers": markers}
    mode = str(payload.get("mode") or state.get("mode") or "auto").strip().lower()
    if mode not in ODYSSEUS_LAUNCH_MODES:
        mode = "auto"
    host = _coerce_host(payload.get("host") or state.get("host"))
    port = _coerce_port(payload.get("port") or state.get("port"))
    next_state = dict(state)
    next_state.update(
        {
            "path": str(path),
            "mode": mode,
            "host": host,
            "port": port,
            "url": f"http://{host}:{port}",
            "configured_at": _now(),
        }
    )
    saved = _save_odysseus_runtime_state(root, next_state)
    status = odysseus_dependency_status(root)
    return {"ok": True, "mode": "configure", "path": str(path), "state_path": str(saved), "status": status}


def odysseus_runtime_action(root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    """Configure and manage an optional Odysseus checkout as a separate runtime."""
    root = Path(root).resolve()
    raw = dict(request or {})
    payload = _request_payload(raw)
    action = _safe_slug(_payload_text(payload, "action", default="status"))
    state = _odysseus_runtime_state(root)

    if action in {"status", "list", "refresh"}:
        return {"ok": True, "mode": "status", "status": odysseus_dependency_status(root)}
    if action in {"configure", "config", "set"}:
        return _configure_odysseus_dependency(root, payload, state)
    if action in {"open", "url"}:
        status = odysseus_dependency_status(root)
        return {"ok": True, "mode": "open", "url": status.get("url"), "status": status}
    if action == "start":
        if not bool(payload.get("confirmed")):
            return {"ok": False, "mode": action, "error": "Starting Odysseus requires confirmed=true."}
        if payload.get("path"):
            configured = _configure_odysseus_dependency(root, payload, state)
            if not configured.get("ok"):
                return configured
            state = _odysseus_runtime_state(root)
        status = odysseus_dependency_status(root)
        if status.get("running"):
            return {"ok": True, "mode": "start", "status": status, "pid": status.get("pid"), "url": status.get("url"), "already_running": True}
        path = _resolve_odysseus_path(root, status.get("path"))
        markers = _odysseus_markers(path)
        if path is None or not markers.get("valid_checkout"):
            return {"ok": False, "mode": action, "error": "Configure a valid Odysseus checkout before starting.", "status": status}
        mode = _select_odysseus_mode(path, str(payload.get("mode") or state.get("mode") or "auto"))
        host = _coerce_host(payload.get("host") or state.get("host"))
        port = _coerce_port(payload.get("port") or state.get("port"))
        command = _odysseus_start_command(path, mode, host, port)
        log_path = _runtime_dir(root) / "odysseus_launcher.log"
        log_handle = open_binary_append_handle(log_path)
        creationflags = 0
        if os.name == "nt":
            creationflags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
            creationflags |= getattr(subprocess, "CREATE_NO_WINDOW", 0)
        env = os.environ.copy()
        env.setdefault("APP_BIND", host)
        env.setdefault("APP_PORT", str(port))
        env.setdefault("ODYSSEUS_HOST", host)
        env.setdefault("ODYSSEUS_PORT", str(port))
        try:
            proc = subprocess.Popen(command, cwd=str(path), stdout=log_handle, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, env=env, creationflags=creationflags)
        except Exception as exc:
            log_handle.close()
            return {"ok": False, "mode": action, "error": f"Could not start Odysseus: {exc}", "command": command, "log_path": str(log_path)}
        log_handle.close()
        state.update({"path": str(path), "mode": str(payload.get("mode") or state.get("mode") or "auto"), "host": host, "port": port, "url": f"http://{host}:{port}", "pid": proc.pid, "started_at": _now(), "last_command": command, "log_path": str(log_path)})
        _save_odysseus_runtime_state(root, state)
        time.sleep(0.2)
        return {"ok": True, "mode": "start", "pid": proc.pid, "url": state["url"], "command": command, "log_path": str(log_path), "status": odysseus_dependency_status(root)}
    if action == "stop":
        if not bool(payload.get("confirmed")):
            return {"ok": False, "mode": action, "error": "Stopping Odysseus requires confirmed=true."}
        status = odysseus_dependency_status(root)
        path = _resolve_odysseus_path(root, status.get("path"))
        mode = str(status.get("mode") or state.get("mode") or "native")
        stopped = False
        errors: list[str] = []
        if mode == "docker" and path:
            docker = shutil.which("docker") or "docker"
            try:
                proc = subprocess.run([docker, "compose", "stop"], cwd=str(path), capture_output=True, text=True, timeout=20, check=False)
                stopped = proc.returncode == 0
                if proc.returncode != 0:
                    errors.append((proc.stderr or proc.stdout or "docker compose stop failed").strip())
            except Exception as exc:
                errors.append(str(exc))
        else:
            pid = status.get("pid")
            if _pid_alive(pid):
                try:
                    if os.name == "nt" and shutil.which("taskkill"):
                        proc = subprocess.run([shutil.which("taskkill") or "taskkill", "/PID", str(int(pid)), "/T", "/F"], capture_output=True, text=True, timeout=8, check=False)
                        stopped = proc.returncode == 0
                        if proc.returncode != 0:
                            errors.append((proc.stderr or proc.stdout or "taskkill failed").strip())
                    else:
                        os.kill(int(pid), 15)
                        stopped = True
                except Exception as exc:
                    errors.append(str(exc))
            else:
                errors.append("No live Nova-managed Odysseus PID was found.")
        state["stopped_at"] = _now()
        if stopped:
            state["pid"] = None
        _save_odysseus_runtime_state(root, state)
        next_status = odysseus_dependency_status(root)
        return {"ok": stopped, "mode": "stop", "stopped": stopped, "errors": errors, "status": next_status}
    return {"ok": False, "mode": action, "error": "Usage: status|configure|start|stop|open"}


def build_odysseus_workspace_snapshot(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    docs_payload = docs_action(root, "list")
    compare_payload = compare_action(root, "list")
    notes_payload = notes_action(root, "list", task_mode=False)
    tasks_payload = notes_action(root, "list", task_mode=True)
    skills_payload = keyed_library_action(root, "list", store_name="skills")
    presets_payload = keyed_library_action(root, "list", store_name="presets")
    memory_payload = memory_vault_action(root, "audit")
    cookbook_payload = recommend_models(detect_hardware(""), "coding")
    policy_payload = load_tool_policy(root)
    code_files = _recent_code_files(root)
    research_reports = _recent_research_reports()
    upload_contexts = _shared_upload_contexts()
    odysseus_runtime = odysseus_dependency_status(root)
    policy_levels: dict[str, int] = {}
    for item in (policy_payload.get("policy") or {}).values():
        level = str(item.get("level") or "ask")
        policy_levels[level] = policy_levels.get(level, 0) + 1
    windows = [
        {"id": "docs", "label": "Docs", "command": "/nova-docs list", "count": _item_count(docs_payload, "documents"), "summary": "Markdown document vault with sidecar suggestions."},
        {"id": "runtime", "label": "Runtime", "command": "/nova-odysseus-runtime", "count": 1 if odysseus_runtime.get("configured") or odysseus_runtime.get("running") else 0, "summary": "Optional Odysseus dependency launcher and localhost status."},
        {"id": "research", "label": "Research", "command": "/research topic to investigate", "count": len(research_reports), "summary": "Deep-research reports, source maps, claims and evidence gaps."},
        {"id": "uploads", "label": "Uploads", "command": "/context-files", "count": len(upload_contexts), "summary": "Shared text/image/PDF context files for chat and vision."},
        {"id": "compare", "label": "Compare", "command": "/nova-compare list", "count": _item_count(compare_payload, "comparisons"), "summary": "Blind model comparison receipts and vote state."},
        {"id": "cookbook", "label": "Cookbook", "command": "/nova-cookbook recommend coding", "count": _item_count(cookbook_payload, "models"), "summary": "Hardware-aware local model recommendations."},
        {"id": "notes", "label": "Notes", "command": "/nova-notes list", "count": _item_count(notes_payload, "items"), "summary": "Local quick notes."},
        {"id": "tasks", "label": "Tasks", "command": "/nova-tasks list", "count": _item_count(tasks_payload, "items"), "summary": "Local task checklist."},
        {"id": "skills", "label": "Skills", "command": "/nova-skills", "count": _item_count(skills_payload, "items"), "summary": "Reusable behavior snippets."},
        {"id": "memory", "label": "Memory", "command": "/nova-memory-vault audit", "count": _item_count(memory_payload, "items"), "summary": "Odysseus-suite memory artifact audit."},
        {"id": "gates", "label": "Gates", "command": "/nova-tool-permissions", "count": len(policy_payload.get("policy") or {}), "summary": "Privilege policy for risky tools and integrations."},
        {"id": "code", "label": "Code", "command": "/search-nova-code", "count": len(code_files), "summary": "Recent Nova code files that can open in the existing editor."},
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "root": str(root),
        "windows": windows,
        "documents": docs_payload.get("documents") or [],
        "comparisons": compare_payload.get("comparisons") or [],
        "cookbook": cookbook_payload,
        "research_reports": research_reports,
        "upload_contexts": upload_contexts,
        "notes": notes_payload.get("items") or [],
        "tasks": tasks_payload.get("items") or [],
        "skills": skills_payload.get("items") or {},
        "presets": presets_payload.get("items") or {},
        "memory": memory_payload,
        "policy": policy_payload,
        "policy_level_counts": policy_levels,
        "code_files": code_files,
        "odysseus_runtime": odysseus_runtime,
        "commands": {item["id"]: item["command"] for item in windows},
    }


def _request_payload(request: dict[str, Any]) -> dict[str, Any]:
    payload = request.get("payload")
    if isinstance(payload, dict):
        merged = dict(payload)
        for key in ("surface", "window", "action", "confirmed"):
            if key in request and key not in merged:
                merged[key] = request[key]
        return merged
    return dict(request)


def _payload_text(payload: dict[str, Any], *keys: str, default: str = "") -> str:
    for key in keys:
        value = payload.get(key)
        if value is not None:
            return str(value).strip()
    return default


def _workbench_summary(surface: str, action: str, result: dict[str, Any]) -> str:
    if not result.get("ok", True):
        return str(result.get("error") or "Workbench action failed.")
    item = result.get("item") if isinstance(result.get("item"), dict) else {}
    if item:
        return f"{surface} {action}: {item.get('id') or item.get('text') or 'saved'}"
    for key in ("url", "status", "name", "path", "export_path", "count"):
        if result.get(key):
            return f"{surface} {action}: {result.get(key)}"
    mode = result.get("mode") or action
    return f"{surface} {mode} completed."


def odysseus_workspace_action(root: Path | str, request: dict[str, Any]) -> dict[str, Any]:
    """Run one JSON-backed Odysseus workbench action through existing stores."""
    root = Path(root).resolve()
    raw = dict(request or {})
    payload = _request_payload(raw)
    surface = _safe_slug(_payload_text(payload, "surface", "window", default="workspace"))
    action = _safe_slug(_payload_text(payload, "action", default="list"))
    result: dict[str, Any]

    if surface in {"docs", "documents"}:
        if action in {"create", "new"}:
            title = _payload_text(payload, "title", "name", default="Nova document")
            content = str(payload.get("content") or "")
            result = docs_action(root, f"new {title} => {content}")
        elif action in {"read", "show"}:
            result = docs_action(root, f"read {_payload_text(payload, 'name', 'title')}")
        elif action in {"suggest", "edit"}:
            name = _payload_text(payload, "name", "title")
            instruction = _payload_text(payload, "instruction", "text", default="improve clarity without changing meaning")
            result = docs_action(root, f"suggest {name} => {instruction}")
        elif action == "export":
            result = docs_action(root, "export")
        else:
            result = docs_action(root, "list")
    elif surface == "notes":
        if action in {"add", "create", "new"}:
            result = notes_action(root, f"add {_payload_text(payload, 'text', 'content')}", task_mode=False)
        elif action == "search":
            result = notes_action(root, f"search {_payload_text(payload, 'query', 'text')}", task_mode=False)
        elif action == "export":
            result = notes_action(root, "export", task_mode=False)
        else:
            result = notes_action(root, "list", task_mode=False)
    elif surface == "tasks":
        if action in {"add", "create", "new"}:
            result = notes_action(root, f"add {_payload_text(payload, 'text', 'content')}", task_mode=True)
        elif action in {"done", "complete"}:
            result = notes_action(root, f"done {_payload_text(payload, 'id', 'text')}", task_mode=True)
        elif action == "search":
            result = notes_action(root, f"search {_payload_text(payload, 'query', 'text')}", task_mode=True)
        elif action == "export":
            result = notes_action(root, "export", task_mode=True)
        else:
            result = notes_action(root, "list", task_mode=True)
    elif surface in {"skills", "presets"}:
        store_name = surface
        if action in {"add", "create", "new", "set"}:
            name = _payload_text(payload, "name", "title")
            text = _payload_text(payload, "text", "content", "value")
            result = keyed_library_action(root, f"add {name} => {text}", store_name=store_name)
        elif action in {"show", "get"}:
            result = keyed_library_action(root, f"show {_payload_text(payload, 'name', 'key')}", store_name=store_name)
        elif action == "export":
            result = keyed_library_action(root, "export", store_name=store_name)
        else:
            result = keyed_library_action(root, "list", store_name=store_name)
    elif surface == "compare":
        if action in {"plan", "start", "new", "create"}:
            prompt = _payload_text(payload, "prompt", "text", default="Improve Nova")
            models = payload.get("models")
            if isinstance(models, list):
                models_text = ", ".join(str(m).strip() for m in models if str(m).strip())
            else:
                models_text = _payload_text(payload, "models", default="qwen2.5-coder:7b, qwen2.5:14b")
            result = compare_action(root, f"plan {prompt} => {models_text}")
        elif action in {"vote", "record"}:
            result = compare_action(root, f"vote {_payload_text(payload, 'id', 'comparison_id')} {_payload_text(payload, 'winner', default='tie')}")
        else:
            result = compare_action(root, "list")
    elif surface in {"gates", "policy", "permissions"}:
        if action in {"check", "classify", "review"}:
            result = classify_action(root, _payload_text(payload, "text", "action_text", "query"))
        elif action == "set":
            tool = _payload_text(payload, "tool", "name")
            level = _payload_text(payload, "level", default="ask").lower()
            reason = _payload_text(payload, "reason", default="workbench override")
            if not tool:
                result = {"ok": False, "mode": action, "error": "Tool name is required."}
            elif level == "allow" and not bool(payload.get("confirmed")):
                result = {"ok": False, "mode": action, "error": "Setting a tool to allow requires confirmed=true."}
            else:
                result = update_tool_policy(root, tool, level, reason)
        else:
            result = load_tool_policy(root)
    elif surface == "cookbook":
        if action == "whatif":
            result = recommend_models(detect_hardware(_payload_text(payload, "hints", "hardware")), _payload_text(payload, "use_case", "task", default="coding"))
        else:
            result = recommend_models(detect_hardware(""), _payload_text(payload, "use_case", "task", default="coding"))
    elif surface == "research":
        if action in {"run", "create", "start", "report"}:
            from .config import AssistantConfig
            from .research_engine import build_research_report

            topic = _payload_text(payload, "topic", "query", "text", default="Nova Odysseus integration ideas")
            urls_raw = payload.get("urls") or payload.get("sources") or []
            if isinstance(urls_raw, str):
                urls = [u.strip() for u in re.split(r"[\s,]+", urls_raw) if u.strip()]
            elif isinstance(urls_raw, list):
                urls = [str(u).strip() for u in urls_raw if str(u).strip()]
            else:
                urls = []
            if urls and not bool(payload.get("confirmed")):
                result = {"ok": False, "mode": action, "error": "Fetching research source URLs requires confirmed=true."}
            else:
                md_path, json_path, report = build_research_report(AssistantConfig(workspace=str(root), allow_internet=bool(payload.get("allow_internet"))), topic, urls)
                result = {
                    "ok": True,
                    "mode": "report",
                    "topic": report.get("topic"),
                    "path": str(md_path),
                    "json_path": str(json_path),
                    "source_count": len(report.get("sources") or []),
                    "claim_count": len(report.get("key_claims") or []),
                }
        else:
            result = {"ok": True, "mode": "list", "reports": _recent_research_reports()}
    elif surface in {"uploads", "upload", "context"}:
        if action == "clear":
            if not bool(payload.get("confirmed")):
                result = {"ok": False, "mode": action, "error": "Clearing shared uploads requires confirmed=true."}
            else:
                from .file_context import clear_file_contexts

                result = {"ok": True, "mode": "clear", "count": clear_file_contexts()}
        else:
            result = {"ok": True, "mode": "list", "items": _shared_upload_contexts()}
    elif surface in {"runtime", "launcher", "odysseus"}:
        result = odysseus_runtime_action(root, {**payload, "action": action})
    elif surface == "memory":
        result = memory_vault_action(root, "export" if action == "export" else "audit")
    else:
        result = {"ok": False, "mode": action, "error": f"Unknown Odysseus workspace surface: {surface}"}

    ok = bool(result.get("ok", True))
    response = {
        "ok": ok,
        "surface": surface,
        "action": action,
        "summary": _workbench_summary(surface, action, result),
        "result": result,
    }
    if ok:
        response["snapshot"] = build_odysseus_workspace_snapshot(root)
    return response


def write_suite_report(root: Path | str) -> dict[str, Any]:
    payload = build_suite_status(root)
    docs = Path(root) / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    md_path = docs / "NOVA_ODYSSEUS_FULL_FEATURE_PORT.md"
    json_path = docs / "NOVA_ODYSSEUS_FULL_FEATURE_PORT.json"
    atomic_write_text(md_path, render_suite_status(payload))
    atomic_write_json(json_path, payload, ensure_ascii=False)
    payload["report_path"] = str(md_path)
    payload["json_path"] = str(json_path)
    return payload


def render_suite_status(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Odysseus Feature Suite",
        "",
        f"Source: {payload.get('source', ODYSSEUS_SOURCE)}",
        f"Generated: {payload.get('generated_at', '')}",
        f"Coverage: **{payload.get('coverage', {}).get('covered', 0)}/{payload.get('coverage', {}).get('total', 0)}** ({payload.get('coverage', {}).get('percent', 0)}%)",
        "",
        "## Commands added or mapped",
    ]
    for command in payload.get("primary_commands", []):
        lines.append(f"- `{command}`")
    lines += ["", "## Feature coverage"]
    for item in payload.get("features", []):
        lines.append(f"- **{item['name']}** — `{item['status']}` via `{item['nova_command']}`")
        lines.append(f"  - Adaptation: {item['nova_adaptation']}")
    signals = payload.get("signals") or {}
    if signals:
        lines += ["", "## Local Nova signals"]
        for k, v in signals.items():
            lines.append(f"- `{k}`: {v}")
    if payload.get("report_path"):
        lines += ["", f"Report: `{payload['report_path']}`"]
    return "\n".join(lines)


def render_policy(payload: dict[str, Any]) -> str:
    lines = ["# Nova Tool Permissions", "", f"Generated: {payload.get('generated_at', _now())}"]
    if "decision" in payload:
        lines += ["", f"Decision: **{payload.get('decision')}**", f"Requires confirmation: **{payload.get('requires_confirmation')}**", f"Blocked: **{payload.get('blocked')}**"]
        matches = payload.get("matched_surfaces") or []
        if matches:
            lines += ["", "## Matched surfaces"]
            for item in matches:
                lines.append(f"- `{item.get('tool')}` from `{item.get('keyword')}` -> `{item.get('level')}` — {item.get('reason')}")
        else:
            lines += ["", "No risky tool surface was detected from the supplied text."]
        return "\n".join(lines)
    if payload.get("ok") is False:
        return "# Nova Tool Permissions\n\n" + payload.get("error", "Unknown error")
    lines += ["", "Levels: `allow`, `ask`, `block`, `admin`", "", "## Policy"]
    for name, item in sorted((payload.get("policy") or {}).items()):
        lines.append(f"- `{name}` -> `{item.get('level')}` — {item.get('reason')}")
    lines += ["", "Usage: `/nova-tool-permissions check ACTION`, `/nova-tool-permissions set TOOL LEVEL => REASON`"]
    return "\n".join(lines)


def render_cookbook(payload: dict[str, Any]) -> str:
    if payload.get("kind") == "system":
        hw = payload.get("hardware", {})
        lines = ["# Nova Model Cookbook", "", "## Detected / simulated hardware"]
        for key in ["os", "python", "cpu_count", "ram_gb", "vram_gb", "gpu_names", "hints_used"]:
            lines.append(f"- `{key}`: {hw.get(key)}")
        lines += ["", "Use `/nova-cookbook recommend`, or `/nova-cookbook whatif ram=32 vram=16 gpu=RTX 5070 Ti => coding`."]
        return "\n".join(lines)
    lines = ["# Nova Model Cookbook", "", f"Use case: **{payload.get('use_case', 'general Nova use')}**"]
    hw = payload.get("hardware", {})
    lines.append(f"Hardware: RAM **{hw.get('ram_gb')}GB**, VRAM **{hw.get('vram_gb')}GB**, CPU cores **{hw.get('cpu_count')}**")
    if hw.get("gpu_names"):
        lines.append("GPU: " + ", ".join(map(str, hw.get("gpu_names") or [])))
    lines += ["", "## Recommended local models"]
    for item in payload.get("models", []):
        lines.append(f"- **{item['name']}** — score `{item['fit_score']}` / `{item['status']}` / {item['use']} / backend: {item['backend']}")
    lines += ["", "Safety: this command only recommends. Downloads/serving should remain explicit and confirmation-gated."]
    return "\n".join(lines)


def compare_action(root: Path | str, rest: str) -> dict[str, Any]:
    words = rest.strip().split(maxsplit=1)
    action = words[0].lower() if words else "plan"
    body = words[1] if len(words) > 1 else ""
    state = _load_state(root, "comparisons", {"comparisons": []})
    comps = state.setdefault("comparisons", [])
    if action in {"list", "history"}:
        return {"ok": True, "mode": "list", "comparisons": comps[-20:], "path": str(_state_path(root, "comparisons"))}
    if action in {"vote", "record"}:
        bits = body.split(maxsplit=1)
        if len(bits) < 2:
            return {"ok": False, "mode": action, "error": "Usage: /nova-compare vote COMPARISON_ID left|right|tie"}
        comp_id, winner = bits[0], bits[1].strip().lower()
        if winner not in {"left", "right", "tie", "a", "b"}:
            return {"ok": False, "mode": action, "error": "winner must be left, right, tie, a or b"}
        for comp in comps:
            if comp.get("id") == comp_id:
                comp["winner"] = winner
                comp["voted_at"] = _now()
                _save_state(root, "comparisons", state)
                return {"ok": True, "mode": action, "comparison": comp, "revealed": comp.get("mapping")}
        return {"ok": False, "mode": action, "error": "comparison id not found"}
    prompt, models_raw = _split_arrow(body if action in {"plan", "start", "new"} else rest)
    models = [m.strip() for m in re.split(r"[,|]", models_raw) if m.strip()]
    if len(models) < 2:
        models = ["current-primary-model", "candidate-secondary-model"]
    comp_id = "cmp_" + uuid.uuid4().hex[:10]
    flip = int(uuid.uuid5(uuid.NAMESPACE_URL, comp_id).int % 2)
    left, right = (models[1], models[0]) if flip else (models[0], models[1])
    record = {
        "id": comp_id,
        "created_at": _now(),
        "prompt": prompt or "Compare two candidate model answers to the same Nova task.",
        "models": models[:4],
        "blind": True,
        "left_label": "Model A",
        "right_label": "Model B",
        "mapping": {"left": left, "right": right},
        "winner": "",
        "instructions": [
            "Run the same prompt against both models with the same context budget.",
            "Paste each answer into the left/right slots without revealing names.",
            "Vote left/right/tie, then reveal the mapping from this receipt.",
        ],
    }
    comps.append(record)
    _save_state(root, "comparisons", state)
    return {"ok": True, "mode": "plan", "comparison": record, "path": str(_state_path(root, "comparisons"))}


def render_compare(payload: dict[str, Any]) -> str:
    lines = ["# Nova Blind Model Compare", ""]
    if not payload.get("ok"):
        return "\n".join(lines + [payload.get("error", "Unknown compare error")])
    if payload.get("mode") == "list":
        rows = payload.get("comparisons") or []
        if not rows:
            return "\n".join(lines + ["No comparison records yet."])
        for comp in rows:
            lines.append(f"- `{comp.get('id')}` — winner: `{comp.get('winner') or 'pending'}` — prompt: {str(comp.get('prompt',''))[:100]}")
        return "\n".join(lines)
    comp = payload.get("comparison", {})
    lines += [
        f"Comparison ID: `{comp.get('id')}`",
        f"Prompt: {comp.get('prompt')}",
        "",
        "## Blind slots",
        f"- Left: **{comp.get('left_label', 'Model A')}**",
        f"- Right: **{comp.get('right_label', 'Model B')}**",
        "",
        "## Instructions",
    ]
    for item in comp.get("instructions", []):
        lines.append(f"- {item}")
    if comp.get("winner"):
        lines += ["", f"Winner: `{comp.get('winner')}`", f"Reveal: `{json.dumps(comp.get('mapping'), ensure_ascii=False)}`"]
    else:
        lines += ["", f"Vote with `/nova-compare vote {comp.get('id')} left|right|tie`.", "Reveal is stored in the receipt but do not inspect it until after voting if you want a blind test."]
    return "\n".join(lines)


def docs_action(root: Path | str, rest: str) -> dict[str, Any]:
    words = rest.strip().split(maxsplit=1)
    action = words[0].lower() if words else "list"
    body = words[1] if len(words) > 1 else ""
    docs_dir = _runtime_dir(root) / "documents"
    docs_dir.mkdir(parents=True, exist_ok=True)
    if action in {"list", "ls", ""}:
        docs = sorted([p for p in docs_dir.glob("*.md")], key=lambda p: p.stat().st_mtime, reverse=True)
        return {"ok": True, "mode": "list", "documents": [{"name": p.stem, "path": str(p), "updated_at": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(p.stat().st_mtime))} for p in docs[:50]]}
    if action in {"new", "create"}:
        title, content = _split_arrow(body)
        title = title or "Nova document"
        path = docs_dir / f"{_safe_slug(title, 'document')}.md"
        if not content:
            content = f"# {title}\n\nDraft owned by the user. Nova suggestions should be kept as sidecars until accepted.\n"
        atomic_write_text(path, content if content.endswith("\n") else content + "\n")
        return {"ok": True, "mode": "new", "name": path.stem, "path": str(path)}
    if action in {"read", "show"}:
        path = docs_dir / f"{_safe_slug(body, 'document')}.md"
        if not path.exists():
            return {"ok": False, "mode": action, "error": "document not found"}
        return {"ok": True, "mode": action, "name": path.stem, "path": str(path), "content": path.read_text(encoding="utf-8")[:8000]}
    if action in {"suggest", "edit"}:
        name, instruction = _split_arrow(body)
        path = docs_dir / f"{_safe_slug(name, 'document')}.md"
        if not path.exists():
            return {"ok": False, "mode": action, "error": "document not found"}
        suggestion = {
            "document": path.stem,
            "instruction": instruction or "improve clarity without changing meaning",
            "created_at": _now(),
            "patch_policy": "sidecar_only_until_user_accepts",
            "suggested_steps": [
                "Read the document and identify objective issues.",
                "Produce a diff or replacement section, not an invisible overwrite.",
                "Ask for acceptance before writing changes into the owned document.",
            ],
        }
        sidecar = unique_path(docs_dir, f"{path.stem}.suggestion", ".json")
        atomic_write_json(sidecar, suggestion, ensure_ascii=False)
        return {"ok": True, "mode": action, "path": str(path), "suggestion_path": str(sidecar), "suggestion": suggestion}
    if action == "export":
        export = {"exported_at": _now(), "documents": []}
        for p in sorted(docs_dir.glob("*.md")):
            export["documents"].append({"name": p.stem, "content": p.read_text(encoding="utf-8")})
        path = unique_path(docs_dir, "documents_export", ".json")
        atomic_write_json(path, export, ensure_ascii=False)
        return {"ok": True, "mode": "export", "path": str(path), "count": len(export["documents"])}
    return {"ok": False, "mode": action, "error": "Usage: /nova-docs list|new TITLE => CONTENT|read TITLE|suggest TITLE => INSTRUCTION|export"}


def render_docs(payload: dict[str, Any]) -> str:
    lines = ["# Nova Documents", ""]
    if not payload.get("ok"):
        return "\n".join(lines + [payload.get("error", "Unknown document error")])
    mode = payload.get("mode")
    if mode == "list":
        docs = payload.get("documents") or []
        if not docs:
            return "\n".join(lines + ["No workspace documents yet. Create one with `/nova-docs new TITLE => CONTENT`."])
        return "\n".join(lines + [f"- `{d['name']}` — {d['updated_at']} — `{d['path']}`" for d in docs])
    if mode in {"read", "show"}:
        return "\n".join(lines + [f"Document: `{payload.get('name')}`", f"Path: `{payload.get('path')}`", "", "```md", payload.get("content", ""), "```"])
    if mode in {"suggest", "edit"}:
        return "\n".join(lines + ["Suggestion sidecar created; document was not overwritten.", f"Document: `{payload.get('path')}`", f"Suggestion: `{payload.get('suggestion_path')}`"])
    if mode == "new":
        return "\n".join(lines + [f"Created document: `{payload.get('name')}`", f"Path: `{payload.get('path')}`"])
    return "\n".join(lines + [f"{mode}: `{payload.get('path')}`", f"Count: {payload.get('count','')}"])


def notes_action(root: Path | str, rest: str, *, task_mode: bool = False) -> dict[str, Any]:
    store_name = "tasks" if task_mode else "notes"
    state = _load_state(root, store_name, {store_name: []})
    rows = state.setdefault(store_name, [])
    words = rest.strip().split(maxsplit=1)
    action = words[0].lower() if words else "list"
    body = words[1] if len(words) > 1 else ""
    if action in {"add", "new", "task"} or (task_mode and action not in {"list", "search", "done", "export"}):
        text = body if action in {"add", "new", "task"} else rest
        if not text.strip():
            return {"ok": False, "mode": "add", "error": "Nothing to add."}
        item = {"id": ("task_" if task_mode else "note_") + uuid.uuid4().hex[:8], "text": text.strip(), "created_at": _now(), "done": False if task_mode else None}
        rows.append(item)
        _save_state(root, store_name, state)
        return {"ok": True, "mode": "add", "item": item, "path": str(_state_path(root, store_name))}
    if action in {"done", "complete"} and task_mode:
        ident = body.strip() or (words[1] if len(words) > 1 else "")
        for item in rows:
            if item.get("id") == ident or str(item.get("text", "")).startswith(ident):
                item["done"] = True
                item["done_at"] = _now()
                _save_state(root, store_name, state)
                return {"ok": True, "mode": "done", "item": item}
        return {"ok": False, "mode": "done", "error": "task not found"}
    if action == "search":
        q = body.lower()
        matches = [r for r in rows if q in str(r.get("text", "")).lower()]
        return {"ok": True, "mode": "search", "items": matches[-50:]}
    if action == "export":
        path = unique_path(_runtime_dir(root), f"{store_name}_export", ".json")
        atomic_write_json(path, state, ensure_ascii=False)
        return {"ok": True, "mode": "export", "path": str(path), "count": len(rows)}
    return {"ok": True, "mode": "list", "items": rows[-50:], "path": str(_state_path(root, store_name))}


def render_notes(payload: dict[str, Any], *, task_mode: bool = False) -> str:
    title = "Nova Tasks" if task_mode else "Nova Notes"
    lines = [f"# {title}", ""]
    if not payload.get("ok"):
        return "\n".join(lines + [payload.get("error", "Unknown note/task error")])
    if payload.get("mode") in {"add", "done"}:
        item = payload.get("item", {})
        return "\n".join(lines + [f"Saved `{item.get('id')}`: {item.get('text')}", f"Done: {item.get('done')}" if task_mode else ""]).strip()
    if payload.get("mode") == "export":
        return "\n".join(lines + [f"Exported {payload.get('count')} item(s) to `{payload.get('path')}`"])
    items = payload.get("items") or []
    if not items:
        return "\n".join(lines + ["No items yet."])
    for item in items:
        status = "[x]" if item.get("done") else "[ ]" if task_mode else "-"
        lines.append(f"{status} `{item.get('id')}` — {item.get('text')} ({item.get('created_at')})")
    return "\n".join(lines)


def keyed_library_action(root: Path | str, rest: str, *, store_name: str) -> dict[str, Any]:
    state = _load_state(root, store_name, {store_name: {}})
    rows = state.setdefault(store_name, {})
    words = rest.strip().split(maxsplit=1)
    action = words[0].lower() if words else "list"
    body = words[1] if len(words) > 1 else ""
    if action in {"add", "set", "new"}:
        name, value = _split_arrow(body)
        if not name or not value:
            return {"ok": False, "mode": action, "error": f"Usage: /nova-{store_name} add NAME => TEXT"}
        rows[_safe_slug(name)] = {"name": name.strip(), "text": value.strip(), "updated_at": _now()}
        _save_state(root, store_name, state)
        return {"ok": True, "mode": "add", "name": _safe_slug(name), "path": str(_state_path(root, store_name))}
    if action in {"show", "get"}:
        key = _safe_slug(body)
        item = rows.get(key)
        if not item:
            return {"ok": False, "mode": action, "error": "item not found"}
        return {"ok": True, "mode": "show", "name": key, "item": item}
    if action == "export":
        path = unique_path(_runtime_dir(root), f"{store_name}_export", ".json")
        atomic_write_json(path, state, ensure_ascii=False)
        return {"ok": True, "mode": "export", "path": str(path), "count": len(rows)}
    return {"ok": True, "mode": "list", "items": rows, "path": str(_state_path(root, store_name))}


def render_keyed_library(payload: dict[str, Any], *, title: str, command: str) -> str:
    lines = [f"# {title}", ""]
    if not payload.get("ok"):
        return "\n".join(lines + [payload.get("error", "Unknown library error")])
    if payload.get("mode") == "show":
        item = payload.get("item", {})
        return "\n".join(lines + [f"`{payload.get('name')}` — {item.get('name')}", "", item.get("text", "")])
    if payload.get("mode") == "add":
        return "\n".join(lines + [f"Saved `{payload.get('name')}` to `{payload.get('path')}`"])
    if payload.get("mode") == "export":
        return "\n".join(lines + [f"Exported {payload.get('count')} item(s) to `{payload.get('path')}`"])
    items = payload.get("items") or {}
    if not items:
        return "\n".join(lines + [f"No items yet. Add one with `{command} add NAME => TEXT`."])
    for key, item in sorted(items.items()):
        lines.append(f"- `{key}` — {item.get('name')} — {item.get('updated_at')}")
    return "\n".join(lines)


def memory_vault_action(root: Path | str, rest: str) -> dict[str, Any]:
    action = (rest.strip().split(maxsplit=1)[0].lower() if rest.strip() else "audit")
    runtime = _runtime_dir(root)
    targets = [runtime / "notes.json", runtime / "tasks.json", runtime / "skills.json", runtime / "presets.json", runtime / "tool_policy.json"]
    payload = {"ok": True, "mode": action, "generated_at": _now(), "items": []}
    for p in targets:
        if p.exists():
            payload["items"].append({"name": p.stem, "path": str(p), "bytes": p.stat().st_size})
    if action == "export":
        export = {"exported_at": _now(), "items": {}}
        for item in payload["items"]:
            export["items"][item["name"]] = read_json_file(Path(item["path"]), {}, quarantine=True)
        path = unique_path(runtime, "memory_vault_export", ".json")
        atomic_write_json(path, export, ensure_ascii=False)
        payload["export_path"] = str(path)
    return payload


def render_memory_vault(payload: dict[str, Any]) -> str:
    lines = ["# Nova Memory Vault", "", f"Mode: `{payload.get('mode')}`"]
    items = payload.get("items") or []
    if not items:
        lines.append("No Odysseus-suite memory artifacts exist yet.")
    else:
        for item in items:
            lines.append(f"- `{item['name']}` — {item['bytes']} bytes — `{item['path']}`")
    if payload.get("export_path"):
        lines += ["", f"Export: `{payload['export_path']}`"]
    return "\n".join(lines)


def build_fastapi_architecture_plan(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    modules = sorted(p.name for p in (root / "winlocalassistant").glob("*.py")) if (root / "winlocalassistant").exists() else []
    has_http_webui = "webui.py" in modules
    has_core = "core.py" in modules
    has_verified = "nova_verified_changes.py" in modules
    phases = [
        {
            "phase": "1. Keep NovaCore stable and add optional FastAPI sidecar",
            "why": "Avoid breaking the working CLI, tests and voice launcher while giving the GUI real API endpoints.",
            "routes": ["GET /api/health", "POST /api/command", "GET /api/activity", "GET /api/files"],
            "validation": ["existing CLI tests still pass", "TestClient route smoke", "web UI still opens from start script"],
            "risk": "low",
        },
        {
            "phase": "2. Add streaming/events layer",
            "why": "Nova's autonomous, voice and validation loops need live progress without polling-heavy UI code.",
            "routes": ["WebSocket /ws/events or SSE /api/events", "POST /api/command/{id}/stop", "GET /api/runs/{id}"],
            "validation": ["fake long command streams progress", "stop button cancels safe worker", "event log remains durable"],
            "risk": "medium",
        },
        {
            "phase": "3. Turn Odysseus-translated commands into panels",
            "why": "Cookbook, compare, docs, notes/tasks, skills and memory-vault should be clickable app surfaces, not only slash commands.",
            "routes": ["/api/cookbook/*", "/api/compare/*", "/api/docs/*", "/api/notes/*", "/api/tasks/*", "/api/skills/*"],
            "validation": ["one API smoke per panel", "permission gates before mutation", "round-trip JSON receipts"],
            "risk": "medium",
        },
        {
            "phase": "4. Optional auth/integration hardening",
            "why": "Only needed before exposing Nova beyond localhost or adding email/calendar/webhook credentials.",
            "routes": ["/api/auth/*", "/api/tokens/*", "/api/integration-gates/*"],
            "validation": ["localhost-only default", "admin-only privileged routes", "no secrets in logs"],
            "risk": "high",
        },
    ]
    # The architecture recommendation is independent of whether this helper is
    # pointed at a full checkout or a temporary test workspace. Missing files are
    # reported in `signals`, but the safest strategic path remains the hybrid
    # FastAPI sidecar rather than a wholesale rewrite.
    recommendation = "hybrid_fastapi_sidecar"
    return {
        "ok": True,
        "generated_at": _now(),
        "root": str(root),
        "recommendation": recommendation,
        "decision": "Yes, Nova would benefit from FastAPI for the GUI/API/event layer, but not from a risky one-shot rewrite.",
        "keep": ["NovaCore / AssistantCore command router", "CLI commands", "verified self-apply engine", "eval packs", "voice launcher"],
        "change": ["replace ThreadingHTTPServer web shell with optional FastAPI app", "move UI calls to typed JSON routes", "stream activity through WebSocket/SSE", "serve static GUI assets separately from backend logic"],
        "not_recommended": ["copy Odysseus app.py wholesale", "rename all modules at once", "put email/calendar/webhooks behind unauthenticated localhost bypass", "run heavy jobs inside request handlers"],
        "signals": {"has_http_webui": has_http_webui, "has_core": has_core, "has_verified_self_apply": has_verified, "module_count": len(modules)},
        "phases": phases,
    }


def render_fastapi_architecture_plan(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova FastAPI Architecture Plan",
        "",
        f"Decision: **{payload.get('decision')}**",
        f"Recommendation: `{payload.get('recommendation')}`",
        f"Generated: {payload.get('generated_at', '')}",
        "",
        "## Keep",
    ]
    lines += [f"- {item}" for item in payload.get("keep", [])]
    lines += ["", "## Change"]
    lines += [f"- {item}" for item in payload.get("change", [])]
    lines += ["", "## Do not do"]
    lines += [f"- {item}" for item in payload.get("not_recommended", [])]
    lines += ["", "## Staged migration"]
    for phase in payload.get("phases", []):
        lines.append(f"### {phase.get('phase')}")
        lines.append(phase.get("why", ""))
        lines.append("Routes: " + ", ".join(f"`{r}`" for r in phase.get("routes", [])))
        lines.append("Validation: " + ", ".join(phase.get("validation", [])))
        lines.append("")
    signals = payload.get("signals") or {}
    lines += ["## Current Nova signals"]
    for key, value in signals.items():
        lines.append(f"- `{key}`: {value}")
    return "\n".join(lines).rstrip()


def build_gui_workbench_plan(root: Path | str) -> dict[str, Any]:
    root = Path(root).resolve()
    webui_path = root / "winlocalassistant" / "webui.py"
    webui_text = webui_path.read_text(encoding="utf-8", errors="ignore") if webui_path.exists() else ""
    rail_items = [
        {"label": "Suite", "command": "/nova-odysseus-suite", "panel": "Feature coverage"},
        {"label": "Runtime", "command": "/nova-odysseus-runtime", "panel": "Optional Odysseus launcher"},
        {"label": "Gates", "command": "/nova-tool-permissions", "panel": "Privilege table"},
        {"label": "Cookbook", "command": "/nova-cookbook whatif ram=32 vram=16 => coding", "panel": "Hardware-aware model fit"},
        {"label": "Research", "command": "/research topic to investigate", "panel": "Deep research reports"},
        {"label": "Uploads", "command": "/context-files", "panel": "Shared file/image/PDF context"},
        {"label": "Compare", "command": "/nova-compare plan improve Nova => qwen2.5-coder:7b, qwen2.5:14b", "panel": "Blind model test"},
        {"label": "Docs", "command": "/nova-docs list", "panel": "Documents vault"},
        {"label": "Notes", "command": "/nova-notes list", "panel": "Quick notes"},
        {"label": "Tasks", "command": "/nova-tasks list", "panel": "Task checklist"},
        {"label": "Skills", "command": "/nova-skills", "panel": "Reusable behaviours"},
        {"label": "Memory", "command": "/nova-memory-vault audit", "panel": "Memory export/audit"},
        {"label": "Code", "command": "/search-nova-code", "panel": "Code tabs"},
        {"label": "FastAPI", "command": "/nova-fastapi-plan", "panel": "Architecture migration"},
    ]
    layout = [
        "Left command rail: permanent compact launcher for Nova workspaces",
        "Wide sidebar: chats/projects/models/commands remain searchable",
        "Centre: chat plus active workspace surface",
        "Right: status, voice, editor, receipts and transparent diff",
        "Modal/fullscreen surfaces: documents, cookbook, compare, research reports and tasks",
        "Mobile mode: collapse wide sidebars into the rail and keep touch targets large",
    ]
    return {
        "ok": True,
        "generated_at": _now(),
        "root": str(root),
        "webui_present": webui_path.exists(),
        "ui_markers": {
            "odysseus_workbench_panel": "odysseusWorkbenchPanel" in webui_text,
            "workbench_panel": "odysseusWorkbenchPanel" in webui_text,
            "launcher_buttons": "data-odysseus-command" in webui_text,
            "rail_buttons": "data-odysseus-command" in webui_text,
            "fastapi_plan_button": "/nova-fastapi-plan" in webui_text,
            "workspace_windows": "odysseusWorkspacePopup" in webui_text and "loadOdysseusWorkspace" in webui_text,
            "odysseus_runtime_launcher": "loadOdysseusRuntime" in webui_text and "runOdysseusRuntimeAction" in webui_text,
            "code_tabs": "renderCodeWorkbench" in webui_text and "openOdysseusCodeFile" in webui_text,
            "json_workbench_actions": "submitOdysseusWorkbenchAction" in webui_text and "data-workbench-action" in webui_text,
            "research_upload_windows": "id==='research'" in webui_text and "id==='uploads'" in webui_text,
            "odysseus_deep_links": "openOdysseusDeepLink" in webui_text and "/odysseus-research" in webui_text,
        },
        "layout": layout,
        "rail_items": rail_items,
        "next_panels": ["blind compare answer slots", "model cookbook install planner", "skills/memory import-export modal", "settings tab for permission gates", "route-backed mobile/PWA shell"],
    }


def render_gui_workbench_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Odysseus GUI Workbench Plan", "", f"Generated: {payload.get('generated_at', '')}", f"Web UI present: **{payload.get('webui_present')}**", "", "## Layout to emulate/adapt"]
    lines += [f"- {item}" for item in payload.get("layout", [])]
    lines += ["", "## Rail / panel mapping"]
    for item in payload.get("rail_items", []):
        lines.append(f"- **{item.get('label')}** -> `{item.get('command')}` -> {item.get('panel')}")
    lines += ["", "## Current UI markers"]
    for key, value in (payload.get("ui_markers") or {}).items():
        lines.append(f"- `{key}`: {value}")
    lines += ["", "## Next GUI panels"]
    lines += [f"- {item}" for item in payload.get("next_panels", [])]
    return "\n".join(lines)


def render_odysseus_runtime(payload: dict[str, Any]) -> str:
    status = payload.get("status") if isinstance(payload.get("status"), dict) else payload
    lines = [
        "# Nova Odysseus Runtime",
        "",
        f"Mode: `{payload.get('mode') or 'status'}`",
        f"State: **{status.get('status', 'unknown')}**",
        f"Running: **{status.get('running', False)}**",
        f"URL: `{status.get('url', '')}`",
        f"Path: `{status.get('path', '')}`",
        f"Launch mode: `{status.get('mode', '')}`",
    ]
    if status.get("pid"):
        lines.append(f"PID: `{status.get('pid')}` (alive: `{status.get('pid_alive')}`)")
    markers = status.get("markers") or {}
    lines += ["", "## Checkout markers"]
    for key in ["valid_checkout", "app_py", "requirements", "setup_py", "launch_windows", "docker_compose"]:
        lines.append(f"- `{key}`: {markers.get(key)}")
    if status.get("start_command"):
        lines += ["", "## Start command", "`" + " ".join(map(str, status.get("start_command") or [])) + "`"]
    notes = status.get("notes") or []
    if notes:
        lines += ["", "## Notes"]
        lines += [f"- {note}" for note in notes]
    lines += [
        "",
        "Usage:",
        "- `/nova-odysseus-runtime`",
        "- `/nova-odysseus-runtime configure C:\\path\\to\\odysseus`",
        "- `/nova-odysseus-runtime start --confirm`",
        "- `/nova-odysseus-runtime stop --confirm`",
    ]
    if payload.get("error"):
        lines += ["", f"Error: {payload.get('error')}"]
    return "\n".join(lines)


def scaffold_plan(feature: str) -> dict[str, Any]:
    feature = feature.lower().strip("/")
    plans = {
        "nova-email-plan": ["Add encrypted credential store", "Read-only inbox list first", "AI summary/draft only; never send without explicit confirmation", "Per-account allow/deny routing", "Regression tests for no-secret logging"],
        "nova-calendar-plan": ["Local .ics import/export", "Read-only event listing", "CalDAV credentials behind vault", "Invite/update actions require confirmation", "Timezone and recurrence tests"],
        "nova-mobile-plan": ["Responsive layout audit", "PWA manifest", "touch target checks", "offline-safe static shell", "Playwright viewport smoke tests"],
        "nova-theme-plan": ["Theme tokens", "high contrast fallback", "user preset export/import", "no hard-coded unreadable colours", "visual regression snapshots"],
        "nova-auth-plan": ["Local admin PIN/password option", "session timeout", "recovery codes", "privilege table integration", "no secrets in logs"],
        "nova-upload-plan": ["size limits", "type allowlist", "workspace quarantine", "vision/PDF extraction preview", "delete/export controls"],
    }
    return {"ok": True, "feature": feature, "generated_at": _now(), "steps": plans.get(feature, ["No scaffold available"]), "policy": "scaffold_only_no_credentials_no_network"}


def render_scaffold(payload: dict[str, Any]) -> str:
    lines = ["# Nova Odysseus Integration Scaffold", "", f"Feature: `{payload.get('feature')}`", f"Policy: `{payload.get('policy')}`", "", "## Steps"]
    for i, step in enumerate(payload.get("steps", []), start=1):
        lines.append(f"{i}. {step}")
    return "\n".join(lines)


def handle_odysseus_suite_command(root: Path | str, cmd: str, rest: str) -> str:
    root = Path(root).resolve()
    cmd = cmd.lower()
    rest = rest or ""
    if cmd in {"/nova-odysseus-suite", "/odysseus-suite"}:
        action = (rest.strip().split(maxsplit=1)[0].lower() if rest.strip() else "status")
        payload = write_suite_report(root) if action in {"write", "report", "validate"} else build_suite_status(root)
        return render_suite_status(payload)
    if cmd in {"/nova-odysseus-runtime", "/odysseus-runtime"}:
        bits = rest.strip().split(maxsplit=1)
        action = bits[0].lower() if bits else "status"
        body = bits[1] if len(bits) > 1 else ""
        confirmed = "--confirm" in rest.lower() or " confirm" in f" {rest.lower()} "
        payload: dict[str, Any] = {"action": action or "status", "confirmed": confirmed}
        if action in {"configure", "config", "set"}:
            payload["path"] = body.replace("--confirm", "").strip()
        result = odysseus_runtime_action(root, payload)
        return render_odysseus_runtime(result)
    if cmd in {"/nova-tool-permissions", "/tool-permissions"}:
        bits = rest.strip().split(maxsplit=1)
        action = bits[0].lower() if bits else "list"
        body = bits[1] if len(bits) > 1 else ""
        if action in {"check", "classify", "review"}:
            return render_policy(classify_action(root, body))
        if action == "set":
            left, reason = _split_arrow(body)
            segs = left.split()
            if len(segs) < 2:
                return render_policy({"ok": False, "error": "Usage: /nova-tool-permissions set TOOL LEVEL => REASON"})
            return render_policy(update_tool_policy(root, segs[0], segs[1], reason or "user override"))
        return render_policy(load_tool_policy(root))
    if cmd in {"/nova-cookbook", "/model-cookbook"}:
        bits = rest.strip().split(maxsplit=1)
        action = bits[0].lower() if bits else "recommend"
        body = bits[1] if len(bits) > 1 else ""
        if action in {"system", "hardware", "detect"}:
            return render_cookbook({"kind": "system", "hardware": detect_hardware(body)})
        if action == "whatif":
            hints, use_case = _split_arrow(body)
            return render_cookbook(recommend_models(detect_hardware(hints), use_case))
        use_case = body if action in {"recommend", "models", "rank"} else rest
        return render_cookbook(recommend_models(detect_hardware(""), use_case))
    if cmd in {"/nova-compare", "/model-compare"}:
        return render_compare(compare_action(root, rest))
    if cmd in {"/nova-docs", "/nova-documents"}:
        return render_docs(docs_action(root, rest))
    if cmd == "/nova-notes":
        return render_notes(notes_action(root, rest, task_mode=False), task_mode=False)
    if cmd == "/nova-tasks":
        return render_notes(notes_action(root, rest, task_mode=True), task_mode=True)
    if cmd == "/nova-skills":
        return render_keyed_library(keyed_library_action(root, rest, store_name="skills"), title="Nova Skills", command="/nova-skills")
    if cmd == "/nova-presets":
        return render_keyed_library(keyed_library_action(root, rest, store_name="presets"), title="Nova Presets", command="/nova-presets")
    if cmd == "/nova-memory-vault":
        return render_memory_vault(memory_vault_action(root, rest))
    if cmd in {"/nova-integration-gates", "/integration-gates"}:
        body = rest.strip()
        if body.lower().startswith("check "):
            return render_policy(classify_action(root, body[6:]))
        payload = build_suite_status(root)
        lines = ["# Nova Integration Gates", "", "Privileged Odysseus-style surfaces are classified before use.", "", "## High-risk surfaces"]
        for name, item in sorted(load_tool_policy(root)["policy"].items()):
            if item.get("level") in {"admin", "block"}:
                lines.append(f"- `{name}` -> `{item.get('level')}` — {item.get('reason')}")
        lines += ["", "Check a proposed action with `/nova-integration-gates check ACTION`.", "", f"Suite coverage: {payload['coverage']['covered']}/{payload['coverage']['total']} features mapped."]
        return "\n".join(lines)
    if cmd in {"/nova-fastapi-plan", "/fastapi-migration-plan"}:
        return render_fastapi_architecture_plan(build_fastapi_architecture_plan(root))
    if cmd in {"/nova-gui-workbench-plan", "/odysseus-gui-plan", "/nova-layout-plan"}:
        return render_gui_workbench_plan(build_gui_workbench_plan(root))
    if cmd in {"/nova-email-plan", "/nova-calendar-plan", "/nova-mobile-plan", "/nova-theme-plan", "/nova-auth-plan", "/nova-upload-plan"}:
        return render_scaffold(scaffold_plan(cmd.strip("/")))
    return "Unknown Odysseus suite command. Use /nova-odysseus-suite."
