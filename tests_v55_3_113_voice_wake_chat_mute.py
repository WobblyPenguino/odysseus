from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL


def _webui() -> str:
    return Path('winlocalassistant/webui.py').read_text(encoding='utf-8')


def test_version_113_voice_wake_label():
    assert tuple(map(int, __version__.split('.'))) >= (55, 3, 113)
    assert f'v{__version__}' in VERSION_LABEL
    assert 'Hey Nova' in VERSION_LABEL or 'voice activation' in VERSION_LABEL


def test_edge_rail_is_non_blocking_and_has_wake_button():
    src = _webui()
    assert 'bottom:18px' in src
    assert 'left:14px' in src
    assert 'railWakeBtn' in src
    assert 'toggleWakeWordListening' in src
    assert "onclick=\"toggleGlobalAudio()\"" in src


def test_wake_word_listener_uses_hey_nova_and_voice_commands():
    src = _webui()
    assert 'wakeWordEnabled' in src
    assert 'Always listen for “Hey Nova” wake word' in src
    assert 'function processWakeTranscript' in src
    assert 'function voiceCommandToAction' in src
    assert 'hey\\s+nova' in src
    assert '/validation-matrix' in src
    assert '/jarvis-status' in src
    assert 'toggleSettingsPanel(true)' in src


def test_per_chat_mute_is_separate_from_global_audio():
    src = _webui()
    assert 'wlaMutedChatSessions' in src
    assert 'function activeChatId' in src
    assert 'function toggleCurrentChatMute' in src
    assert 'isCurrentChatMuted()' in src
    assert 'Global spoken audio muted' in src
    assert 'This chat is muted' in src


def test_spoken_replies_are_conversational_not_raw_markdown():
    src = _webui()
    assert 'function conversationalVoiceSummary' in src
    assert 'I have code output ready in the chat' in src
    assert "replace(/^#{1,6}" in src
    assert 'Done. The checks passed' in src
