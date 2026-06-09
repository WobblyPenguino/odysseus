# Nova Requested Feature Audit

OK: **True**
Summary: Requested-feature audit passed
Implemented: **15**
Partial/environment-dependent: **1**
Missing: **0**

## Feature checks
- ✅ **spoken_audio_and_controls** — implemented: Browser speech, microphone voice input, microphone diagnostic preflight, long-response summarisation, mute/unmute and tutorial controls are wired in the GUI.
- ✅ **thin_left_rail_popups** — implemented: Left rail contains settings/audio/tutorial/changelog/release/chat shortcuts with popup panels.
- ✅ **custom_quick_commands** — implemented: Quick commands are flat, customisable, persistent and can execute sequential command lists.
- ✅ **live_activity_clarity** — implemented: Live Activity is taller/resizable, keeps previous runs, shows hover metadata and indented/subtask context.
- ✅ **backend_conversations** — implemented: Persistent backend conversations support create/list/switch/search/rename/delete.
- ✅ **project_memory_and_targeting** — implemented: Project memory is retrieved for build/edit prompts and project targeting can diagnose new-vs-current project intent.
- ✅ **file_cards_and_llm_context** — implemented: Generated/openable files appear as cards and the LLM status panel preserves compact recent prompt/reply context.
- ✅ **research_synthesis** — implemented: Research reports include a short synthesis plus source/excerpt/bias sections.
- ✅ **docker_validation_patch_promotion** — implemented: Docker copied-workspace validation, patch validation, hash locking and promotion rollback logic are present.
- ✅ **release_gate_and_doctor** — implemented: Nova Doctor, release gate and release checklist commands are present.
- ✅ **playwright_scaffold** — implemented: Playwright GUI smoke scaffold exists and release gate runs/skips it depending on environment readiness.
- ✅ **security_defensive_watch** — implemented: Defensive-only security status and watch commands are wired; direct vendor remediation remains intentionally manual/user-approved.
  - Remaining: Direct AVG quarantine/remediation requires documented vendor CLI/API and explicit approval.
- 🟡 **image_generation_status** — environment_dependent: Image generation refuses to fake real generation and provides setup guidance for SD WebUI/Diffusers/ComfyUI.
  - Remaining: Actual generation depends on a reachable/configured local image backend.
- ✅ **browser_console_hygiene** — implemented: The web UI avoids favicon 404 noise, avoids Web Audio before a user gesture, preserves LLM context text while refreshing, and supports multi-command quick buttons.
- ✅ **dependency_and_massive_system_test** — implemented: Startup dependency checks, optional pip install prompts, and one-click confirmed massive system tests are wired.
- ✅ **linux_sandbox_python_ready** — implemented: General Linux sandbox defaults to a Python-ready image and aliases python3 where possible.

## Remaining environment-dependent / approval-only work
- Direct AVG quarantine/remediation requires documented vendor CLI/API and explicit approval.
- Actual generation depends on a reachable/configured local image backend.