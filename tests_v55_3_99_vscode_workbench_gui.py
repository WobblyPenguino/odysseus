from pathlib import Path


def _webui() -> str:
    return Path('winlocalassistant/webui.py').read_text(encoding='utf-8')


def test_vscode_workbench_shell_was_reverted_to_refined_cockpit() -> None:
    src = _webui()
    assert 'data-ui-overhaul="v55.3.115"' in src
    assert 'class="vscodeWorkbench"' not in src
    assert 'class="activityBar"' not in src
    assert '<div id="smartTopStrip"' in src
    assert 'Control Centre' in src
    assert 'integratedRight' in src


def test_existing_functional_ids_preserved_after_revert() -> None:
    src = _webui()
    for element_id in [
        'projects',
        'customTools',
        'commandPalette',
        'quickControlsGrouped',
        'llmStatus',
        'idleSelfImprovement',
        'workspace',
        'activityLog',
        'assistantBoxText',
        'files',
        'editor',
        'codePreview',
    ]:
        assert f'id="{element_id}"' in src


def test_assistant_box_functions_exported_for_inline_handlers() -> None:
    src = _webui()
    assert 'function loadAssistantBox' in src
    assert 'function synthAssistantBox' in src
    assert 'function clearAssistantBox' in src
    assert 'window.loadAssistantBox=window.loadAssistantBox||loadAssistantBox' in src


def test_nova_status_does_not_render_object_object() -> None:
    src = _webui()
    assert 'function novaStatusValue' in src
    assert 'String(live.autonomous)' not in src
    assert 'String(live.idle)' not in src


def test_version_is_current_or_newer() -> None:
    from winlocalassistant import __version__, VERSION_LABEL
    assert tuple(map(int, __version__.split('.'))) >= (55, 3, 123)
    assert f'v{__version__}' in VERSION_LABEL
    assert f'Nova v{__version__}' in _webui()
