from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.command_help import command_help_payload, render_concise_help

ROOT = Path(__file__).resolve().parent


def test_help_is_concise_and_legacy_help_remains_available(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, local_model_timeout_sec=0))
    out = core.chat('/help')
    assert 'Nova Help Hub' in out
    assert '/command-help code' in out
    assert len(out) < 4000
    legacy = core.chat('/help-full')
    assert 'Commands:' in legacy
    assert '/write PATH CONTENT' in legacy


def test_grouped_help_covers_chat_code_files_run_gui_model():
    payload = command_help_payload('')
    groups = set(payload['categories'])
    for group in ['Chat', 'Code', 'Files', 'Run', 'GUI', 'Model']:
        assert group in groups
    rendered = render_concise_help()
    assert '/write PATH CONTENT' in rendered
    assert '/verify COMMAND' in rendered


def test_instant_chat_fallback_for_hi_and_capabilities(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, local_model_timeout_sec=0))
    hi = core.chat('hi/')
    assert 'Nova is responsive' in hi
    assert '/llm-status' in hi
    caps = core.chat('what can you do?')
    assert 'write code' in caps.lower()
    assert '/command-help code' in caps


def test_webui_emergency_stability_layer_is_injected():
    from winlocalassistant.webui import HTML
    assert 'NovaEmergencyStability' in HTML
    assert 'nova-emergency-stability-v1' in HTML
    assert 'novaPanicReset' in HTML
    assert 'novaHelpHubOverlay' in HTML
    assert 'emergency stability v1' in HTML


def test_build_identity_and_layout_diagnostics_include_emergency_layer():
    from winlocalassistant import __version__
    from winlocalassistant.build_info import PATCH_ID, SERVICE_WORKER_CACHE, LAYOUT_STORAGE_VERSION, build_patch_identity
    from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics

    version_key = __version__.replace(".", "-")
    assert PATCH_ID == 'project-state-continuity-memory-v1'
    assert SERVICE_WORKER_CACHE == f'nova-orbit-shell-v{version_key}-project-state-v1'
    assert LAYOUT_STORAGE_VERSION == f'v{__version__}-project-state-v1'
    patch = build_patch_identity(ROOT)
    assert patch['patch_id'] == PATCH_ID
    diag = build_gui_layout_diagnostics(ROOT)
    assert diag['ok'] is True
    assert any(c['name'] == 'emergency_stability_module' and c['ok'] for c in diag['checks'])
    assert any(c['name'] == 'fix_ui_button' and c['ok'] for c in diag['checks'])


def test_shell_and_verify_work_in_non_windows_test_environment(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, local_model_timeout_sec=0))
    shell = core.chat('/shell echo nova-ok')
    assert 'nova-ok' in shell
    verify = core.chat('/verify echo nova-ok')
    assert 'Verification passed' in verify
