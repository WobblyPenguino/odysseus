# Nova Task Loop Roadmap

Last updated: 2026-06-11T20:05:22

## Current status

- Branch: `nova-task-loop-experiments`
- HEAD: `b8bcfc6`
- Candidate doctor accepted: `8`
- Candidate doctor rejected: `0`
- Fresh candidates available: `0`
- Recently completed/skipped candidates: `8`
- Next candidate: `none`

## Latest commits

- `b8bcfc6 Add living task loop roadmap`
- `44cf409 Reject double-quoted markdown fences in task loop validation`
- `5ec7e79 Write failure review report for failed live tasks`
- `fa5ddf6 Clear stale review artifacts before live task runs`
- `cb33785 Task queue improvement: tiny-autodev-sandbox-action-plan-debug-json-v1`
- `f04ee6a Add fresh action plan debug JSON candidate`
- `c6b4eeb Task queue improvement: tiny-autodev-sandbox-action-plan-debug-markdown-v1`
- `7f78c2b Add fresh action plan debug markdown candidate`
- `fb1f6ca Record denied Aider add-file prompts`
- `ab079b8 Task queue improvement: real-model-context-prompt-file-signature-safe-v1`
- `aad55be Allow model context file in task loop candidate validation`
- `fdb50c5 Avoid literal off-scope filenames in Aider task prompts`

## What we have achieved

- External JSON task candidates are validated before use.
- Candidate doctor reports tell us whether there is fresh work.
- Runtime task registration and picker merge work.
- Preflight localization shows exact editable files and tests before Aider runs.
- Compile, targeted test, baseline test, generated-noise cleanup, and clean-git gates protect commits.
- Failed live tasks write failure review evidence.
- Stale patch/subagent reviews are cleared before live runs.
- Double-quoted Markdown code fences in PowerShell are rejected by validation.
- A local roadmap exists and can now be updated by script.

## Current blockers / weak spots

- External candidate pool can become exhausted after successful runs.
- Older built-in tasks are still low-scoring or quarantined.
- Aider can still produce syntax mistakes, so narrow scoped tasks are safer.
- The task loop does not yet call this updater automatically.

## Next recommended action

Add a fresh narrow source+test external candidate or improve task-loop workflow safety.

## Standing audit rule

Before committing or running the next live task:

1. PowerShell parser audit.
2. Markdown fence audit.
3. Python compile.
4. Pytest audit.
5. Candidate validation.
6. Task-loop validation.
7. Generated-noise cleanup.
8. `git diff --check`.
9. Inspect diff.
10. Commit.
11. Preflight proof.
12. Update this roadmap.
