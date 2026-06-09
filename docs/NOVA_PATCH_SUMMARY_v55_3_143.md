# Nova v55.3.143 Orbit voice/file workspace hotfix

This patch addresses the user feedback from the Orbit GUI screenshots/log output. It keeps the Odysseus-inspired layout but removes the remaining legacy flash, reduces speech noise, improves chat/file management, and stops project-verification follow-ups from being misrouted into new project generation.

## Key changes

- Network-first service worker and body-level Orbit shell class so the new GUI appears on first load.
- Chat drawer supports local chat search, switch, rename/edit, delete and per-chat mute.
- Spoken replies are concise and voice-triggered by default.
- Top-left Nova state pill shows current state without needing hover.
- Voice challenge phrase and foreign-voice mismatch guard harden spoken command routing, with temporary testing bypass retained.
- Project files can open in a draggable Odysseus-style editor window with save/download/run controls.
- Current-project test follow-ups route to run_project, human_test, user_test_suite and final_project_check.
- String-search script requests receive a deterministic `file_string_search.py` fallback instead of unrelated file creation.
