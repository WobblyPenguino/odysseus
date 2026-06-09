from __future__ import annotations

"""Read-only GUI layout diagnostics for Nova.

This module is intentionally small and independent from the huge legacy
``webui.py`` HTML string. It gives humans/agents a quick static contract check
before they try to debug the GUI visually in a browser.
"""

from pathlib import Path
from typing import Any


LAYOUT_VERSION = "v55.3.164-gui-overhaul-v10-legacy-continuity"

_REQUIRED_MARKERS: list[tuple[str, str, str, str]] = [
    (
        "body_class",
        "gui-overhaul-v3",
        "webui_layout_overhaul.py",
        "Layout module injects the active layout class into the HTML body.",
    ),
    (
        "modular_layout_import",
        "apply_gui_layout_overhaul",
        "webui.py",
        "webui.py imports/applies the isolated layout module.",
    ),
    (
        "left_drawer_position",
        "left:calc(var(--orbit-left) + var(--orbit-safe-gap))",
        "webui_layout_overhaul.py",
        "Left drawer starts after the icon rail instead of covering it.",
    ),
    (
        "right_drawer_hidden_default",
        "not(.orbit-right-open) #orbitRightDrawer",
        "webui_layout_overhaul.py",
        "Right inspector is hidden until explicitly opened.",
    ),
    (
        "right_drawer_no_ghost",
        "transform:translateX(calc(100% + 32px))",
        "webui_layout_overhaul.py",
        "Closed right drawer is moved off-canvas to prevent a grey ghost panel.",
    ),
    (
        "wide_left_rail",
        "--orbit-left-wide:208px",
        "webui_layout_overhaul.py",
        "Permanent left navigation rail is wide enough for readable labels.",
    ),
    (
        "rail_labels_readable",
        "Wide permanent left rail: labels stay readable",
        "webui_layout_overhaul.py",
        "Desktop rail labels are visible and ellipsized instead of clipped under the drawer.",
    ),
    (
        "runtime_hardener",
        "novaGuiHardenLayout",
        "webui_layout_overhaul.py",
        "Runtime JS re-applies safe drawer state after load.",
    ),
    (
        "runtime_diagnose",
        "novaGuiLayoutDiagnose",
        "webui_layout_overhaul.py",
        "Browser-side geometry diagnostic is available for visual debugging.",
    ),
    (
        "route_health_button",
        "runGuiRouteSanity",
        "webui.py",
        "GUI can test backend command route health from the header.",
    ),
    (
        "layout_health_button",
        "runGuiLayoutSanity",
        "webui.py",
        "GUI can report browser-visible layout health from the header.",
    ),
    (
        "ui_reset_button",
        "resetNovaUiLayout",
        "webui.py",
        "Header exposes a reset UI action that clears stale drawer widths without deleting project data.",
    ),
    (
        "ui_reset_header_button",
        "reset UI",
        "webui.py",
        "Users can recover from stale browser layout state without editing localStorage manually.",
    ),
    (
        "ui_reset_clears_cache",
        "resetNovaUiLayout(true)",
        "webui.py",
        "Header reset UI action requests Nova browser cache/service-worker cleanup as well as drawer reset.",
    ),
    (
        "layout_storage_version",
        "novaGuiLayoutStorageVersion",
        "webui_layout_overhaul.py",
        "Browser automatically clears stale layout-only localStorage when the layout storage version changes.",
    ),

    (
        "ai_help_overlay_module",
        "apply_ai_help_overlay",
        "webui.py",
        "webui.py applies the isolated contextual AI help overlay module.",
    ),
    (
        "ai_help_browser_runtime",
        "NovaGuiAiHelp",
        "webui_ai_help_overlay.py",
        "Browser exposes contextual AI help dots for GUI elements.",
    ),
    (
        "ai_help_dots",
        "novaAiHelpDot",
        "webui_ai_help_overlay.py",
        "Tiny semi-transparent help symbols are injected onto interactive GUI controls.",
    ),
    (
        "ai_help_backend_command",
        "/gui-ai-help",
        "core.py",
        "Clicked GUI context can be sent to Nova for command-aware help.",
    ),
    (
        "cyberpunk_theme_module",
        "apply_cyberpunk_theme",
        "webui.py",
        "webui.py applies the isolated cyberpunk visual theme module.",
    ),
    (
        "cyberpunk_runtime",
        "NovaCyberpunkTheme",
        "webui_cyberpunk_theme.py",
        "Browser exposes the cyberpunk theme runtime/status helper.",
    ),
    (
        "cyberpunk_class",
        "nova-theme-cyberpunk2077",
        "webui_cyberpunk_theme.py",
        "Cyberpunk body class drives the visual makeover.",
    ),
    (
        "cyberpunk_theme_status",
        "novaCyberpunkThemeStatus",
        "webui_cyberpunk_theme.py",
        "Browser can report theme activation status for screenshot-style debugging.",
    ),

    (
        "arcade_runtime",
        "window.NovaArcade",
        "webui_arcade.py",
        "Nova Arcade browser runtime is injected safely.",
    ),
    (
        "arcade_registry",
        "Nova: System Runner",
        "nova_arcade.py",
        "Nova Arcade registry includes the first playable local game.",
    ),
    (
        "grouped_command_help",
        "COMMANDS",
        "command_help.py",
        "Grouped command help metadata exists for searchable help.",
    ),
    (
        "concise_help_replaces_wall",
        "render_concise_help",
        "command_help.py",
        "The default /help can be concise and searchable instead of a huge wall.",
    ),
    (
        "emergency_stability_module",
        "apply_emergency_stability",
        "webui.py",
        "webui.py applies the final stability layer after theme/arcade overlays.",
    ),
    (
        "emergency_runtime_status",
        "NovaEmergencyStability",
        "webui_emergency_stability.py",
        "Browser exposes emergency GUI reset, help hub and overlap diagnostics.",
    ),
    (
        "fix_ui_button",
        "novaPanicReset",
        "webui_emergency_stability.py",
        "Floating fix UI button can close cluttered popups and restore chat composer.",
    ),
    (
        "legacy_continuity_guard",
        "build_legacy_continuity_audit",
        "legacy_continuity.py",
        "Historical capability anchors can be checked before packaging.",
    ),

]

_DOCS = [
    "docs/AI_CONTEXT_START_HERE.md",
    "docs/NOVA_GUI_ARCHITECTURE.md",
    "docs/NOVA_GUI_VISUAL_VERIFICATION.md",
    "docs/NOVA_GUI_LAYOUT_STATUS.md",
    "docs/NOVA_GUI_RESET_AND_ROUTE_DIAGNOSTICS.md",
    "docs/NOVA_BUILD_IDENTITY_AND_CACHE_RECOVERY.md",
    "docs/NOVA_WIDE_LEFT_RAIL.md",
    "docs/NOVA_GUI_AI_HELP_OVERLAY.md",
    "docs/NOVA_CYBERPUNK_THEME.md",
    "docs/NOVA_ARCADE_AND_HELP_COMPLETION.md",
    "docs/NOVA_EMERGENCY_STABILITY_FIX.md",
    "docs/NOVA_LEGACY_CONTINUITY_GUARD.md",
]


def _read(root: Path, rel: str) -> str:
    try:
        return (root / rel).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def build_gui_layout_diagnostics(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    webui = _read(root, "winlocalassistant/webui.py")
    layout = _read(root, "winlocalassistant/webui_layout_overhaul.py")
    ai_overlay = _read(root, "winlocalassistant/webui_ai_help_overlay.py")
    cyberpunk = _read(root, "winlocalassistant/webui_cyberpunk_theme.py")
    interaction = _read(root, "winlocalassistant/webui_interaction_overhaul.py")
    arcade = _read(root, "winlocalassistant/webui_arcade.py")
    emergency = _read(root, "winlocalassistant/webui_emergency_stability.py")
    arcade_meta = _read(root, "winlocalassistant/nova_arcade.py")
    command_help = _read(root, "winlocalassistant/command_help.py")
    legacy = _read(root, "winlocalassistant/legacy_continuity.py")
    core = _read(root, "winlocalassistant/core.py")
    sources = {
        "webui.py": webui,
        "webui_layout_overhaul.py": layout,
        "webui_ai_help_overlay.py": ai_overlay,
        "core.py": core,
        "webui_cyberpunk_theme.py": cyberpunk,
        "webui_interaction_overhaul.py": interaction,
        "webui_arcade.py": arcade,
        "webui_emergency_stability.py": emergency,
        "nova_arcade.py": arcade_meta,
        "command_help.py": command_help,
        "legacy_continuity.py": legacy,
    }
    checks: list[dict[str, Any]] = []
    for name, marker, source, description in _REQUIRED_MARKERS:
        text = sources.get(source, "")
        ok = marker in text
        checks.append(
            {
                "name": name,
                "ok": ok,
                "source": f"winlocalassistant/{source}",
                "marker": marker,
                "description": description,
            }
        )

    docs = []
    for rel in _DOCS:
        path = root / rel
        docs.append({"path": rel, "ok": path.exists(), "description": "context/visual verification documentation"})

    visual_log = root / "logs" / "gui_cyberpunk_visual_verification_20260608.json"
    if not visual_log.exists():
        visual_log = root / "logs" / "gui_visual_verification_20260608.json"
    visual = None
    if visual_log.exists():
        try:
            import json

            visual = json.loads(visual_log.read_text(encoding="utf-8"))
        except Exception as exc:
            visual = {"ok": False, "error": str(exc), "path": str(visual_log)}

    failed = [c for c in checks if not c.get("ok")]
    missing_docs = [d for d in docs if not d.get("ok")]
    return {
        "ok": not failed and not missing_docs,
        "layout_version": LAYOUT_VERSION,
        "root": str(root),
        "checks": checks,
        "docs": docs,
        "visual_verification": visual,
        "failed_count": len(failed) + len(missing_docs),
        "browser_console_check": "window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose(); window.NovaGuiAiHelp && window.NovaGuiAiHelp.count; window.novaCyberpunkThemeStatus && window.novaCyberpunkThemeStatus(); window.NovaEmergencyStability && window.NovaEmergencyStability.diagnose();",
        "recommended_runtime_check": "Click `layout`, then `files`, then any small `?` help dot, then `reset UI`, then `layout` again. Verify the header/button chrome uses the cyberpunk yellow/cyan theme.",
        "cache_reset_steps": [
            "Close the Nova terminal and browser tab.",
            "Start the patched folder with START_NOVA_HERE.bat.",
            "Open http://127.0.0.1:8766/?layout_check=1 and press Ctrl+Shift+R.",
            "Click `reset UI`, then `layout`; if it reports overlap, upload the screenshot and latest logs.",
        ],
    }


def render_gui_layout_diagnostics(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova GUI Layout Diagnostics",
        "",
        f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**",
        f"Layout version: `{payload.get('layout_version')}`",
        f"Root: `{payload.get('root')}`",
        "",
        "## Static layout contract",
    ]
    for check in payload.get("checks", []):
        status = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {status}: `{check.get('name')}` — {check.get('description')} ({check.get('source')})")
    lines.append("")
    lines.append("## Context documents")
    for doc in payload.get("docs", []):
        status = "PASS" if doc.get("ok") else "MISSING"
        lines.append(f"- {status}: `{doc.get('path')}`")
    visual = payload.get("visual_verification")
    lines.append("")
    lines.append("## Visual/browser check")
    if visual:
        lines.append(f"- Last visual verification log loaded: `{visual.get('path', 'logs/gui_visual_verification_20260608.json')}`")
        if isinstance(visual, dict) and visual.get("ok") is not None:
            lines.append(f"- Visual log status: **{visual.get('ok')}**")
    else:
        lines.append("- No visual verification JSON log found yet. This is not fatal, but browser screenshot verification is stronger than static checks.")
    lines.append(f"- Browser console check: `{payload.get('browser_console_check')}`")
    lines.append(f"- Runtime check: {payload.get('recommended_runtime_check')}")
    lines.append("")
    lines.append("## If the old layout still appears")
    for step in payload.get("cache_reset_steps", []):
        lines.append(f"- {step}")
    return "\n".join(lines)


def render_gui_reset_help() -> str:
    return """# Nova GUI Reset Help

Use this when the browser still shows an old/broken drawer layout after extracting a patched Nova zip.

## In the GUI
1. Click `reset UI`. This now also clears Nova browser cache/service-worker state, but does not delete project data.
2. Click `layout`.
3. Click `files`, then `focus`, then `layout` again.
4. If warnings remain, close the Nova browser tab and terminal, restart `START_NOVA_HERE.bat`, open `http://127.0.0.1:8766/?layout_check=1`, then press `Ctrl+Shift+R`.

## Browser console check
Run:

```js
window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose()
```

Expected result: `ok: true` and `warnings: []`.

## What reset UI does
- closes left/right/activity drawers
- clears stale drawer width/collapse keys from browser localStorage
- reapplies the `gui-overhaul-v3` layout class
- reruns browser layout diagnostics

It does **not** delete project files, memories, logs, remote profiles, or backend data.
"""
