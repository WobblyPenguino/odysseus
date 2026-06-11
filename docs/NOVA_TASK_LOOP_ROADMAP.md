# Nova Task Loop Roadmap

Last updated: 2026-06-11T20:30:05

## Current status

- Branch: `nova-task-loop-experiments`
- HEAD: `a3e1486`
- Candidate doctor accepted: `11`
- Candidate doctor rejected: `0`
- Fresh candidates available: `3`
- Recently completed/skipped candidates: `8`
- Next candidate: `tiny-autodev-sandbox-next-item-line-v1`

## Latest commits

- `a3e1486 Task queue improvement: tiny-autodev-sandbox-next-item-line-v1`
- `7728c56 Add fresh autodev sandbox task candidates`
- `a40cfef Update roadmap after task loop auto-update wiring`
- `48b23b5 Update roadmap from task loop outcomes`
- `22a4a92 Avoid timestamp-only roadmap update churn`
- `aaaee59 Preserve manual roadmap section during updates`
- `189f3ef Validate task loop roadmap updater`
- `0e92720 Add task loop roadmap updater`
- `b8bcfc6 Add living task loop roadmap`
- `44cf409 Reject double-quoted markdown fences in task loop validation`
- `5ec7e79 Write failure review report for failed live tasks`
- `fa5ddf6 Clear stale review artifacts before live task runs`

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

<!-- NOVA_ROADMAP_MANUAL_START -->
## Long-term roadmap

### Phase 1 — Make the loop easier to operate

- Add a command that runs the standing audit rule.
- Add a compact latest-state report.
- Link this roadmap from task-loop summaries.

### Phase 2 — Improve candidate generation quality

- Generate fresh candidates that are narrow, deterministic, source+test, and low-risk.
- Reject vague or broad candidates earlier.
- Prefer small existing modules over runtime/GUI changes.

### Phase 3 — Improve failure learning

- Add failed command, exit code, and Aider output tail to failure review reports.
- Categorise failures more precisely.
- Suggest the next safe recovery action after each failed task.

### Phase 4 — Release-readiness

- Keep roadmap and JSON state updated after every pass.
- Add a release-readiness note when the loop reaches a stable milestone.
<!-- NOVA_ROADMAP_MANUAL_END -->
