from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL

WEBUI = Path("winlocalassistant/webui.py")


def test_version_122_voice_profile_label():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 122)
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice-profile" in VERSION_LABEL or "fuzzy Hey Nova" in VERSION_LABEL


def test_right_panel_communication_centre_replaces_improvement_state():
    src = WEBUI.read_text(encoding="utf-8")
    assert "communicationCentreBoard" in src
    assert "Communication centre" in src
    assert "voiceGuardCard" in src
    assert "Live communication trace" in src
    assert "id=\"improvementStateBoard\"" not in src


def test_voice_profile_lock_and_testing_bypass_are_present():
    src = WEBUI.read_text(encoding="utf-8")
    for marker in [
        "startVoiceProfileEnrollment",
        "storedVoiceProfile",
        "voiceProfileSimilarity",
        "voiceTestingBypassActive",
        "Testing bypass unlock",
        "Locked on load",
        "sessionStorage.removeItem('wlaVoiceAuthorized')",
    ]:
        assert marker in src
    assert "localStorage.getItem('wlaVoiceRememberedAuth')==='1'" not in src


def test_fuzzy_wake_word_and_two_stage_capture_pipeline():
    src = WEBUI.read_text(encoding="utf-8")
    for marker in [
        "hanover",
        "hangover",
        "hova",
        "findWakeMatch",
        "startPostWakeCommandCapture",
        "Wake accepted. Listening for your request",
        "wake-followup",
    ]:
        assert marker in src
    # The old one-shot path sent after-text almost immediately; the new flow starts post-wake capture first.
    assert "voiceCandidateTimer=setTimeout(()=>issueVoiceToChat(wakeCandidateText,'wake'),900)" not in src


def test_activity_api_is_session_isolated_by_default():
    src = WEBUI.read_text(encoding="utf-8")
    assert "from .eventlog import delete_activity_runs, SESSION_ID" in src
    assert "scope = (qs.get(\"scope\", [\"session\"])[0]" in src
    assert "Live Activity is session-isolated by default" in src
    assert "scope=all" in src


def test_assistant_box_no_visible_refresh_spam():
    src = WEBUI.read_text(encoding="utf-8")
    assert 'onclick="loadAssistantBox()">Refresh' not in src
    assert "setInterval(loadAssistantBox,12000)" in src
