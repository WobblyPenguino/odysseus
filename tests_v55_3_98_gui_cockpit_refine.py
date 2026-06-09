from pathlib import Path


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def test_missing_assistant_box_runtime_functions_restored():
    src = _webui()
    assert "function loadAssistantBox" in src
    assert "function synthAssistantBox" in src
    assert "function clearAssistantBox" in src
    assert "setInterval(loadAssistantBox" in src


def test_vscode_workbench_reverted_to_refined_cockpit():
    src = _webui()
    assert 'vscodeWorkbench' not in src
    assert 'class="activityBar"' not in src
    assert '<div id="smartTopStrip"' in src
    assert 'data-ui-overhaul="v55.3.115"' in src


def test_inspector_is_tabbed_without_losing_existing_panels():
    src = _webui()
    assert "function setupInspectorTabs" in src
    assert "function setInspectorTab" in src
    assert "setInspectorTab('files')" in src
    assert "Project files" in src
    assert "Latest generated output" in src


def test_live_activity_has_human_names_delete_and_stop_controls():
    src = _webui()
    assert "function runHumanTitle" in src
    assert "deleteSelectedRuns" in src
    assert "/api/activity-delete-runs" in src
    assert "Stop stuck task" in src
    assert "backendId" in src
    assert "possible stale task" in src


def test_version_bumped_to_55_3_98():
    from winlocalassistant import __version__, VERSION_LABEL
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL
    assert f"Nova v{__version__}" in _webui()
