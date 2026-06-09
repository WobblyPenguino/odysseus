# Nova Guarded Local Improvement Rules

Nova may be improved continuously only through guarded cycles.

Cycle rule:
- One small targeted improvement per cycle.
- Never edit more than 3 source/test files without user approval.
- Never delete files.
- Never hand-edit generated LATEST reports as the main fix.
- Never package a release unless all release gates pass.
- Never claim success unless commands verify it.
- Stop and ask Daniel if unsure, if tests fail, or if changing startup/release/validation behaviour.

Research rule:
- Inspect actual files before proposing a patch.
- Ground claims in file paths, test names, command output, or git diff.
- Do not invent repo structure, commands, or test names.
- If external/current research is needed, stop and ask Daniel to use ChatGPT/web or provide sources.

Patch rule:
- State exact files before editing.
- Prefer tests, guardrails, validation, project-state memory, startup reliability, model timeout/fallback, help consistency, and report hygiene.
- Avoid flashy new feature categories.
- Avoid broad GUI redesigns.
- Avoid changing generated report outputs unless changing the generator/test.

Validation rule:
After every patch run:
1. git diff --stat
2. python -m compileall -q app.py winlocalassistant nova
3. targeted pytest for the changed area
4. git status --short

Commit rule:
- Commit only after tests pass.
- If tests fail, do not continue. Revert or ask Daniel.
