# Nova v55.3.156 Autonomous, Media and Safe Subagent Hardening

## Summary

This patch integrates the attached Codex worklog fixes into the latest v55.3.155 tree and adds the next hardening layer:

- Continuous autonomous mission mode now keeps running after a verified finite milestone when requested.
- Finite mode remains available with `--finite`, `--one-shot`, or `/autonomous once`.
- The autonomous loop guard no longer stops continuous missions after the first completed safe cycle; it chooses the next safe improvement or changes strategy after no-progress cycles.
- A high-spec local model profile is exposed for the upgraded PC: `qwen3-coder:30b`, `gemma2:2b`, `llama3.2-vision:11b`, `nomic-embed-text:latest`.
- Safe subagent planning is available without breaking Ollama: deterministic router/researcher/verifier/packager work can be parallelised, while LLM/code mutation stays serialized.
- GUI live activity gained a `Pin latest` toggle so reading older logs is not constantly forced back to the top/latest output.
- Authority controls are exposed in the command launcher and `/authority-mode` without silently granting unrestricted shell/admin access.
- Media proof artifacts are generated: SVG draft, video manifest, dependency-free AVI proof preview and preview HTML.

## User-facing commands

```text
/high-spec-profile
/subagents improve Nova without regressions
/authority-mode
/autonomous start --continuous improve Nova safely and keep choosing the next verified improvement
/autonomous start --finite run one careful improvement and stop when verified
/video-status
/video-plan 10 second cinematic trailer about Nova improving a project
/video-validate 10 second cinematic trailer about Nova improving a project
/image-draft neon rabbit mascot for Nova
/image-status
```

## Validation performed

```bash
python -m compileall -q app.py nova winlocalassistant
python -m pytest -q tests_nova_autonomous_continuous_v55_3_156.py tests_nova_high_spec_subagents_v55_3_156.py tests_nova_media_and_gui_v55_3_156.py
python -m pytest -q tests_request_intent.py tests_self_awareness.py tests_game_design.py tests_nova_video_manifest.py tests_nova_video_validation_v55_3_151.py tests_v55_3_123_wake_handoff_build_loop.py tests_v55_3_143_orbit_voice_file_workspace.py tests_nova_launchers_v55_3_154.py tests_nova_start_here_v55_3_155.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py
python tests_smoke.py
python -m winlocalassistant.validate --all
python app.py /version
node --check extracted_webui.js
```

## Results

- New v55.3.156 focused tests: PASS, 9 tests.
- Regression slice: PASS, 61 tests.
- Direct smoke suite: PASS.
- Layered validator: PASS, 18/18 sections.
- CLI `/version`: PASS, reports Nova 55.3.156 with version consistency aligned.
- WebUI JavaScript syntax: PASS using `node --check` on extracted script.

A full unbounded `python -m pytest -q` was attempted in the packaging container, but timed out before completion. No failure was captured before timeout. Use the targeted/regression commands above for the validated release gate, and run the full sweep on Windows when you can leave it running.

## Safety note

This patch does not remove the Ollama one-prompt-at-a-time model lock. Removing it risks self-interference, CUDA/runtime crashes, and mixed responses. The safer implementation is parallel deterministic subagents with serialized local model mutation/build steps.
