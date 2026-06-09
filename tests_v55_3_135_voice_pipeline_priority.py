from __future__ import annotations

from pathlib import Path


def _webui() -> str:
    return Path("winlocalassistant/webui.py").read_text(encoding="utf-8", errors="replace")


def test_voice_pipeline_primary_state_prioritises_speaking_then_processing() -> None:
    src = _webui()
    assert "function voicePipelinePrimaryState" in src
    assert "if(speechOn)return {state:'Speaking'" in src
    assert "if(requestOn)return {state:'Processing request'" in src


def test_voice_request_completion_does_not_overwrite_active_speech_state() -> None:
    src = _webui()
    expected = (
        "function setVoiceRequestInFlight(on,detail){voiceRequestInFlight=!!on;"
        "const p=voicePipelinePrimaryState(voiceRequestInFlight,novaSpeechActive,"
        "on?'Processing request':'Request complete',detail||'');"
        "setVoicePipelineState(p.state,p.detail);maybeResumeWakeAfterProcessing();}"
    )
    assert expected in src


def test_speech_completion_does_not_overwrite_active_request_state() -> None:
    src = _webui()
    expected = (
        "function setNovaSpeechActive(on,detail){novaSpeechActive=!!on;"
        "const p=voicePipelinePrimaryState(voiceRequestInFlight,novaSpeechActive,"
        "on?'Speaking':'Speech complete',detail||'');"
        "setVoicePipelineState(p.state,p.detail);maybeResumeWakeAfterProcessing();}"
    )
    assert expected in src


def run_all(verbose: bool = False) -> None:
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            if verbose:
                print(f"PASS {name}")


if __name__ == "__main__":
    run_all(True)
