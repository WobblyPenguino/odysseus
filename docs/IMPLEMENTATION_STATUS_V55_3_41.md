# Nova user-request implementation status after v55.3.43

## Implemented
- Spoken audio with summarised long replies, mute controls, replay tutorial and no emoji-readout emphasis.
- Thin left rail for settings/audio/tutorial/changelog/chat/release controls.
- Customisable quick commands with add/edit/move/delete/reset and saved browser state.
- Quick commands moved away from the chat composer and grouped in the left panel.
- Taller, resizable, indented Live Activity with hover metadata and decision context.
- Better AI communication box behaviour and file-write retry handling.
- Changelog popup and release checklist popup.
- Backend persistent multi-chat store with search/switch/new-chat commands.
- Project memory commands and project-memory injection into build/edit prompts.
- Generated file cards in chat.
- LLM status prompt/reply context without loading-text flicker.
- Research report synthesis before raw claims.
- Docker validation, Docker patch validation, patch hash locking and patch promotion.
- Nova Doctor, release gate, release checklist, cohesion report and Integration Radar.
- Linux sandbox switched to a Python-ready image by default.
- Honest image generation: `/image-generate` only uses real backends; `/image-draft` is explicitly a placeholder.
- Defensive security inventory for Windows Defender/AVG-style status, firewall, ports and Nova/Docker lab context.

## Partially implemented / needs future work
- Full GUI release/security checklist view exists as popup/checklist but could be expanded into a richer docked panel.
- Playwright smoke tests are scaffolded but not automatically run by release gate unless you run them manually.
- Project-targeting is improved, but vague build requests can still benefit from a confirmation prompt when a different project is open.
- Direct vendor-specific AVG actions are not implemented; this should start with documented read-only CLI/API integration before any user-approved remediation.
- Offensive cyber-response automation is intentionally not implemented. Defensive monitoring, evidence capture and owned-lab analysis are the safe scope.
