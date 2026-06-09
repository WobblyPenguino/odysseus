from __future__ import annotations

from pathlib import Path

from winlocalassistant import __version__


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def test_version_bumped_for_gui_overhaul() -> None:
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)


def test_gui_has_refined_cockpit_markers_without_losing_inspector() -> None:
    src = _webui()
    for needle in [
        'data-ui-overhaul="v55.3.115"',
        '<div id="smartTopStrip"',
        'Control Centre',
        'Inspector',
        'Project files',
        'function setupInspectorTabs',
    ]:
        assert needle in src
    assert 'vscodeWorkbench' not in src
    assert 'class="activityBar"' not in src


def test_activity_runs_use_human_titles_and_visible_delete_controls() -> None:
    src = _webui()
    assert 'function runHumanTitle' in src
    assert 'Custom tool work' in src
    assert 'Codebase review' in src
    assert 'Delete selected logs' in src or 'Delete selected run logs' in src
    assert '/api/activity-delete-runs' in src
    assert 'backend id:' in src
    # The old duplicate renderer used raw "Run "+id and overrode checkboxes; it must not return.
    assert "const title=rid==='status/no-run'?'Current status / no run':'Run '+rid" not in src


def test_tool_creation_refreshes_toolbox_without_restart() -> None:
    src = _webui()
    assert "setTimeout(loadTools,800)" in src
    assert "setTimeout(loadTools,5000)" in src
    assert "Tool registry refreshed" in src
    assert "if(/^(\\/tool|\\/custom-tools|\\/topic-watch)/.test(text))" in src
