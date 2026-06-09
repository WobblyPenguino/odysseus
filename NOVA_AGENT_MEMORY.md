# Nova Agent Memory

Purpose:
This file gives local coding agents stable memory about Nova so they do not repeat old mistakes.

Current release family:
Nova v55.3.168 startup/release gate hotfix.

Project identity:
Nova is Daniel's local-first Windows AI assistant. It includes chat, command handling, help, writing, reading, verification, coding, release-readiness validation, project-state memory, local model/Ollama support, GUI/runtime usability, and guarded autonomous improvement workflows.

Important lessons learned:
- Local Codex/Ollama text worked, but tool execution failed or produced unsupported tool calls.
- Aider with ollama_chat/qwen3-coder:30b can edit files locally.
- Aider sometimes edits despite "do not edit yet", so it must be guarded by git, tests, and risk checks.
- Aider previously created placeholder tests with pass statements. Those must be rejected.
- Aider previously touched app.py without approval. app.py edits require manual review.
- Generated LATEST reports and release logs change during validation. They should not be treated as source improvements.
- Do not create top-level test_*.py files. This repo uses tests_*.py naming.
- Prefer improving existing tests_*.py files over creating new files.
- Do not delete startup scripts or hand-edit generated reports.

Successful guarded commits:
- Ignore local AI and runtime scratch files.
- Forward nova validate CLI arguments.
- Add guarded local improvement rules.
- Add local Nova planning loop.
- Add guarded continuous Nova improvement loop.
- Harden guarded loop against fake tests and report noise.
- Remove placeholder local AI test artifacts.
- Harden guarded loop cleanup and test naming checks.

Current local-agent strategy:
- Use local_ai_cycles/ for ignored scratch logs.
- Use this file and NOVA_ARCHITECTURE_CONTEXT.md as read-only memory.
- One tiny patch per cycle.
- Validate before commit.
- Revert on risky diffs or failed tests.
