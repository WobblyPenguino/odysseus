from __future__ import annotations

"""Nova build/patch identity helpers.

Version numbers intentionally stay stable across compatibility patches so old
launchers/tests do not break.  This module gives humans, browsers and AI agents
a more precise patch fingerprint so they can verify they are running the newest
extracted folder instead of a stale server/tab.
"""

import hashlib
import platform
from pathlib import Path
from typing import Any

from . import ASSISTANT_NAME, VERSION_LABEL, __version__
from .gui_layout_diagnostics import LAYOUT_VERSION, build_gui_layout_diagnostics

PATCH_ID = "project-state-continuity-memory-v1"
SERVICE_WORKER_CACHE = "nova-orbit-shell-v55-3-168-project-state-v1"
LAYOUT_STORAGE_VERSION = "v55.3.168-project-state-v1"

_HASH_FILES = [
    "winlocalassistant/webui.py",
    "winlocalassistant/webui_layout_overhaul.py",
    "winlocalassistant/gui_layout_diagnostics.py",
    "winlocalassistant/webui_ai_help_overlay.py",
    "winlocalassistant/webui_cyberpunk_theme.py",
    "winlocalassistant/webui_interaction_overhaul.py",
    "winlocalassistant/command_help.py",
    "winlocalassistant/nova_arcade.py",
    "winlocalassistant/webui_arcade.py",
    "winlocalassistant/webui_emergency_stability.py",
    "winlocalassistant/legacy_continuity.py",
    "winlocalassistant/behavior_rules.py",
    "winlocalassistant/deterministic_generation.py",
    "winlocalassistant/performance_tuning.py",
    "winlocalassistant/gui_context_help.py",
    "winlocalassistant/llm_training_lab.py",
    "winlocalassistant/task_execution.py",
    "winlocalassistant/project_state.py",
    "winlocalassistant/core.py",
]


def _short_hash(root: Path) -> str:
    h = hashlib.sha256()
    for rel in _HASH_FILES:
        p = root / rel
        h.update(rel.encode("utf-8"))
        if p.exists():
            h.update(p.read_bytes())
        else:
            h.update(b"<missing>")
    return h.hexdigest()[:12]


def build_patch_identity(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    layout = build_gui_layout_diagnostics(root)
    return {
        "ok": True,
        "product": ASSISTANT_NAME,
        "version": __version__,
        "version_label": VERSION_LABEL,
        "patch_id": PATCH_ID,
        "layout_version": LAYOUT_VERSION,
        "layout_storage_version": LAYOUT_STORAGE_VERSION,
        "service_worker_cache": SERVICE_WORKER_CACHE,
        "source_fingerprint": _short_hash(root),
        "root": str(root),
        "python": platform.python_version(),
        "platform": platform.platform(),
        "gui_layout_ok": bool(layout.get("ok")),
        "gui_layout_failed_count": layout.get("failed_count", 0),
        "verification_commands": [
            "python -m compileall -q app.py nova winlocalassistant",
            "python -m pytest -q tests_smoke.py",
            "python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py",
            "python -m winlocalassistant.validate --all",
        ],
    }


def render_patch_identity(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Build / Patch Identity",
        "",
        f"Product: **{payload.get('product')}**",
        f"Version: `{payload.get('version')}`",
        f"Patch ID: `{payload.get('patch_id')}`",
        f"Source fingerprint: `{payload.get('source_fingerprint')}`",
        f"Layout version: `{payload.get('layout_version')}`",
        f"Layout storage version: `{payload.get('layout_storage_version')}`",
        f"Service-worker cache: `{payload.get('service_worker_cache')}`",
        f"Root: `{payload.get('root')}`",
        f"Python: `{payload.get('python')}`",
        "",
        "## GUI sanity",
        f"- Layout static contract OK: `{payload.get('gui_layout_ok')}`",
        f"- Layout failed count: `{payload.get('gui_layout_failed_count')}`",
        "",
        "## What to compare when debugging stale GUI problems",
        "- The top header/build badge should include the Patch ID above.",
        "- `/api/version` should return the same `patch_id` and `source_fingerprint`.",
        "- `/gui-layout-status` should report `PASS`.",
        "- Click `reset UI`, then `layout`; browser diagnostics should show no warnings.",
        "",
        "## Verification commands",
    ]
    for cmd in payload.get("verification_commands", []):
        lines.append(f"- `{cmd}`")
    return "\n".join(lines)
