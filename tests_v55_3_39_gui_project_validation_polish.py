from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.creation_intent import analyze_creation_request
from winlocalassistant.tools import ToolRegistry


def test_avatar_working_face_is_single_icon(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    mood, emoji, title = core._avatar_profile("working", "", "")
    assert mood == "working"
    assert emoji == "🤖"
    assert "⚙" not in emoji


def test_webui_speech_is_contextual_and_strips_emoji():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "function stripEmojiForSpeech" in html
    assert "function maybeSpeakReply" in html
    assert "avatarSay(j.reply||'')" not in html
    assert "maybeSpeakReply(j.reply||'', text)" in html


def test_llm_context_panel_keeps_previous_text_instead_of_loading_flash():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "llmCtxSpinner" in html
    assert "oldCtx=document.getElementById('llmRecentContext')" in html
    # The refresh function may mention waiting for a first preview, but should not overwrite with a loading placeholder every poll.
    load_fn = html.split("async function loadLLMStatus()", 1)[1].split("async function loadRecentModelContext", 1)[0]
    assert "Loading recent prompt/reply context" not in load_fn


def test_simple_useful_app_uses_utility_fallback_not_game_rules(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    tools = ToolRegistry(cfg)
    analysis = analyze_creation_request("make a tiny useful app")
    fallback = tools._fallback_local_app_project("make a tiny useful app", analysis)
    assert fallback is not None
    text = "\n".join(map(str, fallback["files"].values())).lower()
    assert "dodge" not in text
    assert "localstorage" in text or "json" in text or "notes" in text


def test_linux_sandbox_defaults_to_python_ready_image(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    assert cfg.sandbox_linux_image == "python:3.12-slim"
