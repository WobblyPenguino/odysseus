from __future__ import annotations
from pathlib import Path
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant import __version__, VERSION_LABEL
ROOT = Path(__file__).resolve().parent

def test_media_commands_route_from_core(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    assert "Nova Media Status" in core.handle_command("/media-status")
    assert "Nova Image Prompt Plan" in core.handle_command("/image-plan cinematic robot dog mascot")
    assert "Storyboard written" in core.handle_command("/video-storyboard Nova improves a project")
    assert "Nova Video Render Package" in core.handle_command("/video-package Nova improves a project")

def test_gui_exposes_clean_version_and_media_routes():
    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert f"Nova v{__version__}" in src
    assert "calm-workspace" in src
    assert "/api/version" in src
    for command in ["/media-status", "/image-plan", "/video-storyboard", "/video-package"]:
        assert command in src

def test_start_launcher_is_current_and_stale_safe():
    ps1 = (ROOT / "start_nova_best_models.ps1").read_text(encoding="utf-8")
    bat = (ROOT / "START_NOVA_HERE.bat").read_text(encoding="utf-8")
    assert __version__ in ps1
    assert __version__ in bat
    assert "Stop-StaleNovaServer" in ps1
    assert "Get-RunningNovaVersion" in ps1
    assert "pip install --upgrade pip" not in ps1
    assert "ensurepip --upgrade" in ps1

def test_version_label_current():
    assert __version__
    assert f"v{__version__}" in VERSION_LABEL

def test_gui_sanity_rescue_layout_and_route_probe_are_present():
    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "gui-sanity-rescue" in src
    assert "focusChatLayout" in src
    assert "runGuiRouteSanity" in src
    assert "/api/route-health" in src
    assert "Backend route sanity warning" in src
    assert "grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0" in src


def test_route_health_probe_does_not_execute_file_writing_media_commands():
    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "known_write_heads" in src
    assert '"/video-storyboard"' in src
    assert "route known; not executed because it writes files" in src
    assert "safe_probe_heads" in src
    assert '"/gui-layout-status"' in src
    assert '"/gui-reset-help"' in src


def test_gui_layout_overhaul_module_is_injected_and_documents_contract():
    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    layout = (ROOT / "winlocalassistant" / "webui_layout_overhaul.py").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "NOVA_GUI_ARCHITECTURE.md").read_text(encoding="utf-8")
    assert "apply_gui_layout_overhaul" in src
    assert "apply_cyberpunk_theme" in src
    assert "gui-overhaul-v3" in layout
    assert "gui-overhaul-v4-wide-left-rail" in layout
    assert "grid-template-columns:var(--orbit-left) 0 minmax(0,1fr) 0 0" in layout
    assert "#orbitDrawer" in layout and "left:calc(var(--orbit-left) + var(--orbit-safe-gap))" in layout
    assert "#orbitRightDrawer" in layout and "right:var(--orbit-safe-gap)" in layout
    assert "--orbit-left-wide:208px" in layout
    assert "Wide permanent left rail: labels stay readable" in layout
    assert "not(.orbit-right-open) #orbitRightDrawer" in layout
    assert "Opening either drawer must not resize or crush the central chat canvas" in docs


def test_webui_html_contains_modular_layout_after_import():
    from winlocalassistant.webui import HTML
    assert "gui-overhaul-v3" in HTML
    assert "NovaCyberpunkTheme" in HTML
    assert "GUI layout overhaul v4" in HTML
    assert "NovaGuiOverhaulV3" in HTML
    assert "Overlay drawer: it stays beside the rail" in HTML


def test_ai_context_docs_exist_for_no_context_agents():
    for rel in [
        "docs/AI_CONTEXT_START_HERE.md",
        "docs/NOVA_GUI_ARCHITECTURE.md",
        "docs/NOVA_INSTALL_AND_TEST_ALL.md",
    ]:
        text = (ROOT / rel).read_text(encoding="utf-8")
        assert "Nova" in text
        assert "winlocalassistant" in text or "app.py" in text



def test_gui_layout_overhaul_geometry_with_playwright_when_available():
    import os
    if os.environ.get("NOVA_RUN_PLAYWRIGHT_LAYOUT_TEST") != "1":
        return
    try:
        from playwright.sync_api import sync_playwright
    except Exception:
        return
    import shutil

    chromium = shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome")
    if not chromium:
        return

    from winlocalassistant.webui import HTML

    with sync_playwright() as p:
        browser = p.chromium.launch(
            headless=True,
            executable_path=chromium,
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-gpu", "--disable-crash-reporter", "--disable-breakpad"],
        )
        page = browser.new_page(viewport={"width": 1920, "height": 1000})
        page.set_content(HTML, wait_until="domcontentloaded", timeout=20000)
        page.wait_for_timeout(1200)
        page.evaluate("toggleOrbitDrawer('files')")
        page.wait_for_timeout(200)
        geometry = page.evaluate(
            """() => {
              const box = id => { const e = document.getElementById(id); const r = e.getBoundingClientRect(); const cs = getComputedStyle(e); return {x:r.x,y:r.y,w:r.width,h:r.height,display:cs.display,visibility:cs.visibility,opacity:cs.opacity}; };
              const navLabel = getComputedStyle(document.querySelector('#orbitNav .orbitNavButton .label')).display;
              const composerEl = document.querySelector('.composer');
              const composerRect = composerEl.getBoundingClientRect();
              return { drawer: box('orbitDrawer'), rail: box('orbitNav'), right: box('orbitRightDrawer'), chat: box('chat'), composer:{x:composerRect.x,w:composerRect.width}, navLabel };
            }"""
        )
        browser.close()

    assert geometry["rail"]["w"] >= 200
    assert geometry["navLabel"] != "none"
    assert geometry["drawer"]["x"] >= geometry["rail"]["w"]
    assert geometry["right"]["visibility"] == "hidden"
    assert geometry["right"]["opacity"] == "0"
    assert geometry["chat"]["w"] >= 1500
    assert geometry["composer"]["x"] >= geometry["drawer"]["x"] + geometry["drawer"]["w"]
    assert geometry["composer"]["x"] + geometry["composer"]["w"] <= 1920


def test_gui_layout_status_command_and_endpoint_are_present(tmp_path):
    from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics

    payload = build_gui_layout_diagnostics(ROOT)
    text = render_gui_layout_diagnostics(payload)
    assert payload["ok"] is True
    assert "Nova GUI Layout Diagnostics" in text
    assert "window.novaGuiLayoutDiagnose" in text

    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    reply = core.handle_command("/gui-layout-status")
    assert "Nova GUI Layout Diagnostics" in reply
    assert "Layout version" in reply

    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "/api/gui-layout-health" in src
    assert "runGuiLayoutSanity" in src
    assert "layout</button>" in src
    assert "resetNovaUiLayout" in src
    assert "reset UI" in src
    assert "resetNovaUiLayout(true)" in src
    assert "build</button>" in src
    assert "/api/build-info" in src


def test_gui_reset_help_command_and_docs_are_present(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    reply = core.handle_command("/gui-reset-help")
    assert "Nova GUI Reset Help" in reply
    assert "does **not** delete project files" in reply

    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    docs = (ROOT / "docs" / "NOVA_GUI_RESET_AND_ROUTE_DIAGNOSTICS.md").read_text(encoding="utf-8")
    diag = (ROOT / "winlocalassistant" / "gui_layout_diagnostics.py").read_text(encoding="utf-8")
    assert "resetNovaUiLayout" in src
    assert "staleKeys" in src
    assert "reset UI" in src
    assert "resetNovaUiLayout(true)" in src
    assert "build</button>" in src
    assert "/api/build-info" in src
    assert "NOVA_GUI_RESET_AND_ROUTE_DIAGNOSTICS.md" in diag
    assert "NOVA_CYBERPUNK_THEME.md" in (ROOT / "docs" / "NOVA_CYBERPUNK_THEME.md").read_text(encoding="utf-8")
    assert "reset UI" in docs


def test_gui_runtime_layout_diagnostic_function_is_injected():
    from winlocalassistant.webui import HTML
    assert "novaGuiLayoutDiagnose" in HTML
    assert "NovaGuiOverhaulV3.diagnose" in HTML
    assert "data-layout-role" in HTML
    assert "right drawer visible while closed" in HTML
    assert "novaGuiLayoutStorageVersion" in HTML
    assert "legacy-continuity-regression-guard-v1" in HTML



def test_build_info_command_and_api_markers_are_present(tmp_path):
    from winlocalassistant.build_info import build_patch_identity, render_patch_identity, PATCH_ID, SERVICE_WORKER_CACHE, LAYOUT_STORAGE_VERSION
    payload = build_patch_identity(ROOT)
    text = render_patch_identity(payload)
    assert payload["patch_id"] == PATCH_ID
    assert PATCH_ID == "project-state-continuity-memory-v1"
    assert payload["service_worker_cache"] == SERVICE_WORKER_CACHE
    assert payload["layout_storage_version"] == LAYOUT_STORAGE_VERSION
    assert len(payload["source_fingerprint"]) == 12
    assert "Nova Build / Patch Identity" in text

    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    reply = core.handle_command("/build-info")
    assert PATCH_ID in reply
    assert "Source fingerprint" in reply

    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "/api/build-info" in src
    assert "/api/patch-info" in src
    assert SERVICE_WORKER_CACHE in src
    assert "resetNovaUiLayout(true)" in src
