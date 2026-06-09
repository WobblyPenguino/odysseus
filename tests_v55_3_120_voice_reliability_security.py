from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.feature_continuity import build_feature_continuity_audit
from winlocalassistant.validation_matrix import build_validation_matrix


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8", errors="replace")


def test_version_120_voice_reliability_label():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 120)
    assert f"v{__version__}" in VERSION_LABEL
    assert "voice reliability" in VERSION_LABEL


def test_voice_duplicate_filter_and_silence_gate_markers_present():
    src = _webui()
    assert "collapseRepeatedTranscript" in src
    assert "voiceScreenTranscript" in src
    assert "issueVoiceToChat" in src
    assert "voiceCandidateTimer" in src
    assert "Waiting for silence" in src
    assert "Ignored duplicate voice command" in src


def test_voice_auth_and_speech_controls_are_visible():
    src = _webui()
    assert "voiceAuthPanel" in src
    assert "Require voice login before spoken commands act" in src
    assert "Unlock voice" in src
    assert "Test AI voice" in src
    assert "speechVoiceSelect" in src
    assert "voiceVolume" in src
    assert "voiceRate" in src
    assert "voicePitch" in src
    assert "u.volume=Number(uiSettings.voiceVolume" in src


def test_auto_idle_no_longer_auto_resumes_without_explicit_opt_in():
    src = _webui()
    assert "autoIdleAfterFive:false" in src
    assert "wlaAutoIdleExplicitOptIn" in src
    assert "function setAutoIdleOptIn" in src
    assert "localStorage.getItem('wlaAutoIdleExplicitOptIn')!=='1'" in src


def test_vs_code_style_resize_gutters_and_scrollable_activity():
    src = _webui()
    assert "VS Code-style layout polish" in src
    assert "col-resize" in src
    assert "setupPanelResize" in src
    assert ".runbody{max-height:340px;overflow:auto}" in src
    assert ".activity #activityLog{max-height:min(52vh,520px);overflow:auto}" in src


def test_core_trace_no_longer_double_logs_same_event():
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8", errors="replace")
    assert 'log_activity("trace", event, payload)\n            log_activity("trace", event, payload)' not in src


def test_feature_continuity_and_validation_matrix_include_v120_markers():
    continuity = build_feature_continuity_audit(Path.cwd())
    assert continuity["ok"], continuity.get("failed")
    matrix = build_validation_matrix(Path.cwd(), goal="voice reliability and auth regression")
    assert matrix["ok"], matrix.get("failed")
