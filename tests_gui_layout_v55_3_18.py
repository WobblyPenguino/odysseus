from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.webui import HTML


def test_version_55_3_18():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 101)
    assert f"v{__version__}" in VERSION_LABEL


def test_sandbox_tabs_are_compact_and_panels_scroll():
    assert ".sandboxTabs{display:flex" in HTML
    assert "min-height:44px" in HTML
    assert "overflow-x:auto" in HTML
    assert ".sandboxPanel{border-bottom" in HTML
    assert "max-height:230px" in HTML
    assert "overflow:auto" in HTML
    assert ".chat-wrap{display:flex;flex-direction:column" in HTML
    assert "#chat{flex:1 1 auto;min-height:0}" in HTML


def test_live_activity_collapse_minimizes_panel_without_destroying_chat_layout():
    assert "body.collapse-activity .activity{display:block!important;" in HTML
    assert "body.collapse-activity .activity #activityLog{display:none!important}" in HTML
    assert "toggleActivityOpen" in HTML
    assert "activityToggleBtn" in HTML


def test_left_state_merged_with_right_presence():
    assert "AI state & communication" in HTML
    assert "AI presence / disclosure panel" not in HTML
    assert "Quick controls" in HTML
    assert "AI mood, disclosure and communication now live in the right panel" in HTML
    assert "id=\"avatarBox\"" not in HTML
    assert "id=\"aiPresenceBox\"" in HTML


def test_chatgpt_style_plus_menu_exists():
    assert "id=\"plusBtn\"" in HTML
    assert "id=\"plusMenu\"" in HTML
    assert "Upload files or photos" in HTML
    assert "Research mode" in HTML
    assert "Linux sandbox command" in HTML
    assert "Kali sandbox command" in HTML
    assert "function togglePlusMenu" in HTML
    assert "function hidePlusMenu" in HTML
