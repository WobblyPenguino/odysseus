# Intent understanding and voice mode update — 2026-05-27

## Summary
Implemented a focused Nova update that improves natural-language intent handling and adds browser-based voice mode.

## Intent understanding improvements
- Expanded typo normalization for common user input errors such as `determineing`, `huma`, `bvopice`, `talkl`, `uit`, and split/garbled `imp,lemen t`.
- Expanded request/task intent detection for `implement`, `integrate`, `better at`, `audit`, `review`, `validate`, voice-mode phrases, and intent-router/source-improvement phrases.
- Added success criteria for intent-analysis work and voice-mode work so planning/validation can judge the requested behaviour instead of using unrelated criteria.
- Ensured typo-heavy requests to improve Nova's own intent detection and voice mode are treated as Nova/self-improvement, not as a random app build.

## Voice mode implementation
- Added GUI microphone button beside Send.
- Added left rail voice button.
- Added browser SpeechRecognition / webkitSpeechRecognition microphone capture.
- Added final transcript auto-send into the normal Nova chat pipeline.
- Added voice status text below the composer.
- Added settings for Voice mode and Always speak replies while voice mode is on.
- Reused existing speechSynthesis spoken-reply support and made it speak replies automatically during voice mode.
- Added `/voice-mode`, `/voice`, and `/speech-mode` help commands.

## Browser/runtime notes
Voice mode is browser-side. Microphone transcription depends on browser/OS support. Chrome and Edge usually support SpeechRecognition best. Spoken replies use speechSynthesis. No new cloud backend is added by this patch.

## Validation run
- `python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py tests_v55_3_49_intent_voice_mode.py`
- `python tests_v55_3_49_intent_voice_mode.py`
- `python -m pytest -q tests_v55_3_49_intent_voice_mode.py tests_request_intent.py tests_intent_planning.py tests_task_decomposition.py tests_v55_3_36_audio_gui_memory.py tests_v55_3_44_validation_feature_audit.py`
- `python tests_smoke.py`
- `python -m pytest -q tests_v55_3_24_webui_js_syntax.py tests_v55_3_45_console_feature_hardening.py tests_v55_3_49_intent_voice_mode.py tests_v55_3_36_audio_gui_memory.py`
