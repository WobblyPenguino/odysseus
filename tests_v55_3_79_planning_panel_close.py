from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL


def test_version_bumped_for_planning_panel_fix():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_active_run_panel_hides_when_not_waiting_for_user():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "function clearActiveRunPanel()" in html
    assert "status==='waiting_for_user'||status==='paused'" in html
    assert "This panel automatically closes after you choose an option" in html
    assert "clearActiveRunPanel();if(v)quick('/reply '+v);" in html


def test_active_run_api_only_reports_interactive_states_active():
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert 'status in {"waiting_for_user", "paused"}' in webui
    assert "stale two-way planning panel reopen" in webui
