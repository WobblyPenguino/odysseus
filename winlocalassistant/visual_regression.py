from __future__ import annotations
import shutil, time
from pathlib import Path
from typing import Any


def build_gui_snapshot_status(root: Path) -> dict[str, Any]:
    playwright = root / "playwright" / "nova_gui_smoke.spec.js"
    has_npx = shutil.which("npx") is not None
    return {"ok": playwright.exists(), "playwright_spec": str(playwright), "npx_available": has_npx, "command": "npx playwright test playwright/nova_gui_smoke.spec.js", "snapshot_command": "npx playwright test --update-snapshots", "note": "Visual screenshots are optional and require a running Nova browser target."}


def render_gui_snapshot_status(payload: dict[str, Any]) -> str:
    lines = ["# GUI Visual Regression Gate", "", f"Spec present: **{payload.get('ok')}**", f"npx available: **{payload.get('npx_available')}**", f"Smoke command: `{payload.get('command')}`", f"Snapshot update command: `{payload.get('snapshot_command')}`", "", payload.get("note", "")]
    return "\n".join(lines)
