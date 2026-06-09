from pathlib import Path

WEBUI = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")


def test_webui_defines_spec_choice_startup_guard():
    assert "NOVA_STARTUP_GUARD_V55_3_151" in WEBUI
    assert "function populateSpecChoices()" in WEBUI
    assert "function safeApplyUiSettings()" in WEBUI
    assert "safeApplyUiSettings();populateSpecChoices();" in WEBUI


def test_webui_prefers_upgraded_model_labels():
    assert "qwen3-coder:30b, gemma2:2b" in WEBUI
    assert "Ollama model setup needed" in WEBUI


def test_video_commands_are_visible_in_launcher():
    assert "/video-plan" in WEBUI
    assert "/video-status" in WEBUI
    assert "/video-validate" in WEBUI
