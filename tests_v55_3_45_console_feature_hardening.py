from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.feature_audit import build_feature_audit


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def test_version_55_3_45_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 113)
    assert f"v{__version__}" in VERSION_LABEL


def test_favicon_route_prevents_console_404_noise():
    src = _webui()
    assert 'if path == "/favicon.ico"' in src
    assert 'self._send(204, b"", "image/x-icon")' in src


def test_audio_context_is_user_gesture_gated():
    src = _webui()
    assert "avatarAudioActivated=false" in src
    assert "!avatarAudioActivated" in src
    assert "avatarAudioActivated=true" in src
    # The startup avatar poll can still update visuals, but should not create AudioContext until activation.
    assert "avatarAudioCtx=avatarAudioCtx||new Ctx()" in src


def test_llm_status_preserves_context_without_loading_overwrite():
    src = _webui()
    assert "Loading recent prompt/reply context" not in src
    assert "llmCtxSpinner" in src
    assert "oldCtx" in src


def test_custom_quick_commands_can_run_sequentially_without_duplicate_function_names():
    src = _webui()
    assert "function commandSteps(command)" in src
    assert "async function runQuickCommand" in src
    assert "split(/\\n|;;/)" in src
    assert src.count("function runQuickCommand") == 1


def test_feature_audit_includes_browser_console_hygiene(tmp_path):
    payload = build_feature_audit(Path.cwd())
    names = {item["name"]: item for item in payload["checks"]}
    assert "browser_console_hygiene" in names
    assert names["browser_console_hygiene"]["status"] == "implemented"
    assert payload["ok"] is True
