from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore

ROOT = Path(__file__).resolve().parent


def test_arcade_registry_and_commands_route(tmp_path):
    from winlocalassistant.nova_arcade import arcade_registry, render_arcade_registry

    payload = arcade_registry()
    assert payload["ok"] is True
    assert payload["games"][0]["game_id"] == "system-runner"
    assert "Nova: System Runner" in render_arcade_registry(payload)

    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    assert "Nova Arcade" in core.handle_command("/arcade")
    assert "Nova: System Runner" in core.handle_command("/arcade-launch system-runner")


def test_command_help_is_grouped_searchable_and_routes(tmp_path):
    from winlocalassistant.command_help import command_help_payload, render_command_help

    payload = command_help_payload("arcade")
    text = render_command_help(payload)
    assert payload["count"] >= 1
    assert "Arcade" in payload["categories"]
    assert "/arcade" in text

    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    reply = core.handle_command("/command-help arcade")
    assert "Nova Command Help" in reply
    assert "/arcade" in reply


def test_webui_arcade_runtime_and_help_markers_present():
    from winlocalassistant.webui import HTML

    assert "window.NovaArcade" in HTML
    assert "Nova: System Runner" in HTML
    assert "novaSystemRunnerCanvas" in HTML
    assert "Nova Command Help" in HTML


def test_build_identity_and_diagnostics_include_completion_patch():
    from winlocalassistant import __version__
    from winlocalassistant.build_info import PATCH_ID, SERVICE_WORKER_CACHE, LAYOUT_STORAGE_VERSION, build_patch_identity
    from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics

    version_key = __version__.replace(".", "-")
    assert PATCH_ID == "project-state-continuity-memory-v1"
    assert SERVICE_WORKER_CACHE == f"nova-orbit-shell-v{version_key}-project-state-v1"
    assert LAYOUT_STORAGE_VERSION == f"v{__version__}-project-state-v1"
    assert build_patch_identity(ROOT)["patch_id"] == PATCH_ID
    diag = build_gui_layout_diagnostics(ROOT)
    assert diag["ok"] is True
    assert any(c["name"] == "arcade_runtime" and c["ok"] for c in diag["checks"])
    assert any(c["name"] == "grouped_command_help" and c["ok"] for c in diag["checks"])


def test_arcade_manifest_write_is_explicit(tmp_path):
    from winlocalassistant.nova_arcade import write_arcade_manifest

    out = write_arcade_manifest(tmp_path)
    assert out.exists()
    assert "system-runner" in out.read_text(encoding="utf-8")
