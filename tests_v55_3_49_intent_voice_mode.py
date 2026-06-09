from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.intent_planning import analyze_planning_dialog_need, normalize_user_goal
from winlocalassistant.request_intent import analyze_request_intent, should_block_automatic_mutation
from winlocalassistant.task_decomposition import decompose_user_request, normalize_request_text


def test_typo_heavy_voice_and_intent_request_is_understood_as_wla_improvement() -> None:
    raw = "make the ai bettter at determineing what the huma is asking for and imp,lemen t a bvopice mode so I can talkl to uit"
    assert "voice" in normalize_request_text(raw).lower()
    assert "human" in normalize_user_goal(raw).lower()
    intent = analyze_request_intent(raw)
    assert intent.category == "self_improvement"
    assert intent.target_is_wla_source is True
    assert should_block_automatic_mutation(intent) is True


def test_task_decomposition_extracts_intent_and_voice_success_criteria() -> None:
    plan = decompose_user_request("improve intent detection and implement voice mode with spoken replies")
    assert any(s.intent == "modify" for s in plan.subtasks)
    joined = "\n".join(plan.success_criteria).lower()
    assert "intent analysis" in joined
    assert "voice mode" in joined


def test_planning_detects_voice_modify_intent() -> None:
    dialog = analyze_planning_dialog_need("implement voice mode and improve intent detection")
    assert "modify" in dialog.detected_intents
    assert "voice" in dialog.detected_intents


def test_webui_voice_mode_controls_are_present() -> None:
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    for marker in ["voiceBtn", "toggleVoiceInput", "diagnoseVoiceInput", "getUserMedia", "enumerateDevices", "SpeechRecognition", "webkitSpeechRecognition", "voiceMode", "autoSpeakVoiceMode", "voiceStatus", "voiceDeviceStatus", "railVoiceBtn", "Mic test"]:
        assert marker in html


def test_voice_mode_command_explains_browser_speech_path() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_voice_mode_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        reply = core.handle_command("/voice-mode")
    assert "microphone" in reply.lower()
    assert "speechrecognition" in reply.lower()
    assert "speechsynthesis" in reply.lower()
    assert "mic test" in reply.lower()
    assert "wh-1000" in reply.lower()


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
