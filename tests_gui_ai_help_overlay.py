from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.gui_context_help import build_gui_context_help, render_gui_context_help
from winlocalassistant.webui import HTML

ROOT = Path(__file__).resolve().parent


def test_gui_ai_help_overlay_is_injected_into_html() -> None:
    assert "NovaGuiAiHelp" in HTML
    assert "novaAiHelpDot" in HTML
    assert "nova-ai-help-enabled" in HTML
    assert "/gui-ai-help" in HTML
    assert "window.novaGuiAiHelpScan" in HTML


def test_gui_ai_help_backend_explains_clicked_file_button(tmp_path: Path) -> None:
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    reply = core.handle_command('/gui-ai-help {"label":"Project files","command":"toggleOrbitDrawer(\'files\')","id":"files"}')
    assert "Nova GUI AI Help" in reply
    assert "Project files drawer" in reply
    assert "/files" in reply
    assert "/tree" in reply


def test_gui_ai_help_backend_routes_media_context() -> None:
    payload = build_gui_context_help('{"label":"video package","command":"/video-package make trailer"}')
    text = render_gui_context_help(payload)
    assert payload["topic"] == "media"
    assert "/media-status" in text
    assert "/video-package PROMPT" in text


def test_gui_ai_upgrades_command_and_docs_exist(tmp_path: Path) -> None:
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    reply = core.handle_command("/gui-ai-upgrades")
    assert "Nova GUI/Agent Upgrade Ideas Applied" in reply
    assert "Contextual inline help dots" in reply
    assert (ROOT / "docs" / "NOVA_GUI_AI_HELP_OVERLAY.md").exists()


def test_gui_layout_diagnostics_include_ai_help_contract() -> None:
    from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics

    payload = build_gui_layout_diagnostics(ROOT)
    text = render_gui_layout_diagnostics(payload)
    assert payload["ok"] is True
    assert "ai_help_overlay_module" in text
    assert "ai_help_browser_runtime" in text
    assert "NOVA_GUI_AI_HELP_OVERLAY.md" in text
