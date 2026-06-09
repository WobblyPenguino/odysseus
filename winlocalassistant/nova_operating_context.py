from __future__ import annotations

import json
import logging
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .eventlog import ACTIVITY_PATH, MODEL_IO_PATH, tail_jsonl
from .safe_io import append_jsonl, atomic_write_json, atomic_write_text
from .role_router import build_role_route
from .jarvis_bridge import build_capability_map

LOGGER = logging.getLogger(__name__)

NOVA_CONTEXT_SCHEMA_VERSION = 1
CONTEXT_PATH = APP_DIR / "nova_operating_context_latest.json"
RECEIPT_PATH = APP_DIR / "nova_action_receipts.jsonl"


def _safe_tail(path: Path, limit: int) -> list[dict[str, Any]]:
    try:
        return [row for row in tail_jsonl(path, limit=limit) if isinstance(row, dict)]
    except Exception:
        return []


def _summarise_event(row: dict[str, Any]) -> dict[str, Any]:
    data = row.get("data") if isinstance(row.get("data"), dict) else {}
    return {
        "time": row.get("time", ""),
        "kind": row.get("kind", ""),
        "message": str(row.get("message", ""))[:260],
        "summary": str(data.get("summary") or data.get("reason") or data.get("failure_type") or data.get("output") or "")[:500],
        "run_id": data.get("run") or data.get("run_id") or row.get("run_id") or "",
        "ok": data.get("ok"),
    }


def _important_files(root: Path, max_files: int = 10) -> list[dict[str, Any]]:
    files: list[dict[str, Any]] = []
    if not root.exists():
        return files
    try:
        candidates = sorted([p for p in root.rglob("*") if p.is_file()], key=lambda p: p.stat().st_mtime, reverse=True)
    except Exception:
        return files
    allowed = {".py", ".js", ".html", ".css", ".json", ".md", ".txt", ".bat", ".ps1", ".yaml", ".yml"}
    skip_bits = {"__pycache__", ".git", "node_modules", ".venv", "venv", "dist", "build"}
    for p in candidates:
        if len(files) >= max_files:
            break
        rel = p.relative_to(root).as_posix() if p.is_relative_to(root) else p.name
        if any(bit in rel.split("/") for bit in skip_bits):
            continue
        if p.suffix.lower() not in allowed:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="replace")[:900]
            files.append({"path": rel, "size": p.stat().st_size, "preview": text})
        except Exception as exc:
            files.append({"path": rel, "error": repr(exc)})
    return files


def _verification_conditions(goal: str) -> list[str]:
    low = (goal or "").lower()
    checks = [
        "changed files must be real source/config/docs changes, not only status claims",
        "run command, entry point and verification steps must point to files that exist",
        "do not remove existing user-facing GUI/backend features while improving or redesigning",
        "report blocked/no-op honestly when no safe implementation is available",
        "write a short receipt containing changed files, validation commands and result",
    ]
    if "game" in low:
        checks += [
            "game must include controls, update/draw loop, collision or interaction, score/progress and restart/end-state",
            "theme words from the user request must be visible in code/UI, not only README",
        ]
    if "tool" in low:
        checks += [
            "tool work is complete only when the tool file exists, registry refresh lists it, and tool_test/tool_run passes",
        ]
    if "gui" in low or "ui" in low or "interface" in low:
        checks += [
            "GUI changes must preserve existing element IDs/function entry points unless compatibility wrappers are added",
            "new layout must reduce clutter without deleting access to existing commands/tools/projects/files/activity",
        ]
    if any(word in low for word in ["implement", "fix", "apply", "complete", "do it"]):
        checks += [
            "proposal-only output is not enough; choose a small safe implementation and validate it",
        ]
    return checks[:14]


def build_nova_operating_context(
    root: Path,
    goal: str = "",
    mode: str = "general",
    last_failure: str = "",
    attempts: list[dict[str, Any]] | None = None,
    max_chars: int = 18000,
) -> dict[str, Any]:
    events = [_summarise_event(r) for r in _safe_tail(ACTIVITY_PATH, 80)]
    interesting = [e for e in events if str(e.get("kind") or "") in {
        "verification_failed", "llm_rejected", "candidate_refine_step", "candidate_refine_no_progress",
        "command_failed", "command_timeout", "file_write", "tool_create", "tool_test", "autonomous_loop_guard",
        "codebase_integrity_audit", "docker_validate", "feature_continuity_audit",
    }]
    model_rows = _safe_tail(MODEL_IO_PATH, 8)
    model_summary = []
    for row in model_rows[-4:]:
        model_summary.append({
            "phase": row.get("phase", ""),
            "prompt_preview": str(row.get("prompt_preview") or "")[:500],
            "response_preview": str(row.get("response_preview") or "")[:500],
        })
    context = {
        "schema_version": NOVA_CONTEXT_SCHEMA_VERSION,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "assistant": "Nova / Nova",
        "mode": mode,
        "goal": goal,
        "workspace_root": str(root),
        "target_type_hint": "wla_source" if (root / "winlocalassistant").exists() or (root / "app.py").exists() else "project",
        "last_failure": str(last_failure or "")[:1200],
        "attempt_history": (attempts or [])[-6:],
        "role_route": build_role_route(goal=goal, last_failure=last_failure, target_type="wla_source" if (root / "winlocalassistant").exists() or (root / "app.py").exists() else "project"),
        "verification_conditions": _verification_conditions(goal),
        "recent_relevant_activity": interesting[-14:],
        "recent_model_io": model_summary,
        "recent_relevant_files": _important_files(root),
        "strategy_rules": [
            "When the same rejection repeats, switch strategy instead of asking the model to polish the same failing candidate.",
            "For implementation requests, move proposal -> patch/edit -> validation -> receipt; do not stop at a report.",
            "Prefer deterministic fallback templates for common failures after local-model retries stall.",
            "Use sandbox/Docker validation when available before promoting risky code changes.",
            "Route local-model calls through Planner/Builder/Verifier/Repairer/Toolsmith roles instead of one giant prompt.",
            "Keep exact failure causes in the next prompt so the local model can repair behaviour, not just syntax.",
            "For external daemon/sidecar/screen/shell/browser work, keep Nova as supervisor and queue actions through policy/receipts instead of silent execution.",
        ],
        "external_daemon_context": build_capability_map() if any(k in (goal or '').lower() for k in ["jarvis", "daemon", "sidecar", "screen", "browser", "shell", "proactive"]) else {},
        "success_receipt_required": True,
    }
    # Bound heavy previews.
    text = json.dumps(context, ensure_ascii=False)
    if len(text) > max_chars:
        context["recent_relevant_files"] = context["recent_relevant_files"][:4]
        context["recent_relevant_activity"] = context["recent_relevant_activity"][-8:]
        context["truncated"] = True
    return context


def render_nova_operating_context(context: dict[str, Any]) -> str:
    lines = [
        "# Nova Operating Context",
        "",
        f"Mode: {context.get('mode','')}",
        f"Goal: {context.get('goal','') or '(none)'}",
        f"Workspace: `{context.get('workspace_root','')}`",
        f"Target: {context.get('target_type_hint','unknown')}",
        "",
        "## Role route",
    ]
    rr = context.get("role_route") or {}
    if rr:
        lines.extend([f"Primary role: **{rr.get('primary_role','')}**", f"Route: `{rr.get('route','')}`", f"Reason: {rr.get('reason','')}", ""])
    lines.append("## Verification conditions")
    for item in context.get("verification_conditions") or []:
        lines.append(f"- {item}")
    if context.get("last_failure"):
        lines += ["", "## Latest failure", str(context.get("last_failure"))]
    lines += ["", "## Strategy rules"]
    for item in context.get("strategy_rules") or []:
        lines.append(f"- {item}")
    activity = context.get("recent_relevant_activity") or []
    lines += ["", "## Recent relevant activity"]
    if activity:
        for row in activity[-8:]:
            lines.append(f"- {row.get('time','')} {row.get('kind','')}: {row.get('message','')} {row.get('summary','')}")
    else:
        lines.append("No relevant recent activity found.")
    files = context.get("recent_relevant_files") or []
    lines += ["", "## Recent files available to the model"]
    if files:
        for file in files[:8]:
            lines.append(f"- {file.get('path')} ({file.get('size','?')} bytes)")
    else:
        lines.append("No readable recent project files found.")
    return "\n".join(lines) + "\n"


def write_nova_operating_context(root: Path, goal: str = "", mode: str = "general", last_failure: str = "", attempts: list[dict[str, Any]] | None = None) -> tuple[Path, dict[str, Any]]:
    context = build_nova_operating_context(root, goal=goal, mode=mode, last_failure=last_failure, attempts=attempts)
    atomic_write_json(CONTEXT_PATH, context, ensure_ascii=False)
    return CONTEXT_PATH, context


def write_action_receipt(
    root: Path,
    action: str,
    goal: str,
    changed_files: list[str] | None = None,
    validation: list[dict[str, Any]] | None = None,
    ok: bool = False,
    notes: str = "",
) -> tuple[Path, dict[str, Any]]:
    receipt = {
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
        "action": action,
        "goal": goal,
        "workspace_root": str(root),
        "changed_files": changed_files or [],
        "validation": validation or [],
        "ok": bool(ok),
        "notes": notes,
    }
    append_jsonl(RECEIPT_PATH, receipt, ensure_ascii=False)
    project_receipt = root / "ACTION_RECEIPT.md"
    try:
        lines = ["# Action Receipt", "", f"Action: {action}", f"Goal: {goal}", f"Status: {'PASS' if ok else 'ATTENTION'}", "", "## Changed files"]
        for f in receipt["changed_files"]:
            lines.append(f"- {f}")
        if not receipt["changed_files"]:
            lines.append("- No changed files recorded.")
        lines += ["", "## Validation"]
        for item in receipt["validation"]:
            lines.append(f"- {'PASS' if item.get('ok') else 'FAIL'}: {item.get('name') or item.get('command') or item}")
        if not receipt["validation"]:
            lines.append("- No validation evidence recorded.")
        if notes:
            lines += ["", "## Notes", notes]
        atomic_write_text(project_receipt, "\n".join(lines) + "\n")
    except Exception:
        LOGGER.debug("Failed to write project action receipt to %s", project_receipt, exc_info=True)
    return RECEIPT_PATH, receipt
