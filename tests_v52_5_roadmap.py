from __future__ import annotations

from pathlib import Path

import winlocalassistant.webui as webui_module
from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import APP_DIR


ROOT = Path(__file__).resolve().parent


def _webui_html() -> str:
    return webui_module.HTML


def test_version_is_current() -> None:
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_app_dir_is_writable() -> None:
    assert APP_DIR.exists()
    probe = APP_DIR / ".v52_5_write_probe"
    probe.write_text("ok", encoding="utf-8")
    assert probe.read_text(encoding="utf-8") == "ok"
    probe.unlink(missing_ok=True)


def test_first_load_tutorial_exists_and_is_safe() -> None:
    html = _webui_html()
    assert "tutorialOverlay" in html
    assert "NOVA_TUTORIAL_SEEN" in html
    assert "showTutorial(false)" in html
    assert "Nova voice orb" in html
    assert "Start a new chat, focus typing" in html
    assert "This guide never runs commands" in html


def test_tutorial_mentions_key_sections() -> None:
    html = _webui_html()
    for phrase in [
        "Nova voice orb",
        "Sliding Nova rail",
        "Fast actions",
        "Chat first",
        "Live Activity",
        "Unified right panel",
        "Settings",
    ]:
        assert phrase in html


def test_settings_can_hide_major_ui_sections() -> None:
    html = _webui_html()
    for setting in [
        "showQuickButtons",
        "showComposerButtons",
        "showCommandSuggestions",
        "showFeedbackButtons",
        "showCreatedOutputs",
        "showLiveActivity",
        "showAvatarPanel",
    ]:
        assert setting in html
    assert "uiCreatedOutputs" in html
    assert "uiLiveActivity" in html
    assert "uiAvatarPanel" in html


def test_suggestion_buttons_still_fill_input_not_autorun() -> None:
    html = _webui_html()
    assert "insertSuggestedCommand(command)" in html
    assert "fillCommand(command)" in html
    assert "Suggested commands never auto-run" in html


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
