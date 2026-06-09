# Nova v55.3.141 patch summary

This patch targets the user-reported GUI, voice and coding-flow issues from the attached run log.

## Fixed

- Added a short two-tone Hey Nova ready cue after the wake word is accepted.
- Paused the wake listener while typed, voice and `/reply` requests are in flight so the UI does not return to Listening while Nova is still thinking or speaking.
- Softened wake `no-speech` handling so it reports ready/listening instead of surfacing a scary error state for normal silence.
- Expanded centre-column resize rails across banner/workspace/subframe/activity panels and kept the existing live-activity split resize.
- Preserved Live Activity scroll position during polling refreshes, so reviewing older run events does not jump back to the top.
- Routed “test all of your functionality” style requests to QA/regression/bug-review/doctor tools rather than project generation.
- Added early deterministic coding fallbacks for simple games/apps after local model timeout or malformed JSON, reducing repeated long Ollama retry loops.
- Added `/user-feedback-tests` to print a practical manual command checklist for user feedback testing.
- Fixed one-shot non-slash CLI messages by routing them through `core.chat(...)` instead of the removed `handle_user_message(...)` method.

## Validation targets

- Compile checks for `app.py` and `winlocalassistant`.
- Web UI JavaScript syntax regression.
- Voice/wake routing marker tests.
- Planner routing regression for Nova functionality-test prompts.
- Release hygiene, doctor, architecture audit, bug review and command verification.
