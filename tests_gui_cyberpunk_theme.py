from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent


def test_cyberpunk_theme_module_is_present_and_injected():
    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    theme = (ROOT / "winlocalassistant" / "webui_cyberpunk_theme.py").read_text(encoding="utf-8")
    assert "apply_cyberpunk_theme" in src
    assert "cyberpunk GUI makeover v1" in theme
    assert "nova-theme-cyberpunk2077" in theme
    assert "novaCyberpunkThemeStatus" in theme


def test_webui_html_contains_cyberpunk_theme_after_import():
    from winlocalassistant.webui import HTML
    assert "NovaCyberpunkTheme" in HTML
    assert "nova-theme-cyberpunk2077" in HTML
    assert "CYBERPUNK CONTROL LINK" in HTML


def test_build_info_and_diagnostics_track_cyberpunk_theme():
    from winlocalassistant import __version__
    from winlocalassistant.build_info import PATCH_ID, SERVICE_WORKER_CACHE, LAYOUT_STORAGE_VERSION, build_patch_identity
    from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics

    patch = build_patch_identity(ROOT)
    diag = build_gui_layout_diagnostics(ROOT)

    version_key = __version__.replace(".", "-")
    assert PATCH_ID == "project-state-continuity-memory-v1"
    assert SERVICE_WORKER_CACHE == f"nova-orbit-shell-v{version_key}-project-state-v1"
    assert LAYOUT_STORAGE_VERSION == f"v{__version__}-project-state-v1"
    assert patch["patch_id"] == PATCH_ID
    assert diag["ok"] is True
    assert any(c["name"] == "cyberpunk_theme_module" and c["ok"] for c in diag["checks"])
