from pathlib import Path


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def test_central_chat_tabs_have_add_close_and_shared_context_controls() -> None:
    src = _webui()
    assert 'id="chatTabs"' in src
    assert "class=\"chatTabAdd\"" in src
    assert "function renderChatTabs" in src
    assert "function toggleChatTabShared" in src
    assert "function buildSharedChatContext" in src
    assert "Shared browser chat tab context selected by the user" in src
    assert "buildSharedChatContext(text)" in src
    assert "if(!restoredChat){" in src
    assert "saveCurrentChatSession();}loadProjects()" in src


def test_live_activity_resize_rail_sits_between_chat_and_activity() -> None:
    src = _webui()
    assert "id==='liveActivityPanel')target.before(rail)" in src
    assert 'data-resize-target="\'+id+\'"' in src
    assert 'middleResizeRail[data-resize-target="liveActivityPanel"]' in src
    assert "Resize chat and live activity split" in src


def test_banner_is_visually_removed_and_modern_theme_markers_exist() -> None:
    src = _webui()
    assert "v55.3.134 sci-fi assistant shell" in src
    assert ".topbar>div:first-child{display:none}" in src
    assert "--accent-cyan" in src
    assert "--accent-rose" in src
    assert "--accent-green" in src
    assert "Plan loop" in src
    assert "Quality" in src
