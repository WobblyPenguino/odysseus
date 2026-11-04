# Nova Task Loop Roadmap

Last updated: 2026-06-12T04:06:17

## Current status

- Branch: `nova-safe-batch-controller`
- HEAD: `2dd6be7`
- Candidate doctor accepted: `16`
- Candidate doctor rejected: `0`
- Fresh candidates available: `2`
- Recently completed/skipped candidates: `14`
- Next candidate: `tiny-autodev-sandbox-status-counts-line-v1`

## Latest commits

- `2dd6be7 Task queue improvement: candidate-factory-failure-feedback-gap-v1`
- `fc6fbfb Parse fallback-selected supervised batch task`
- `37810bd Allow supervised autonomy batch controller direct execution`
- `c1f2046 Add dry-run mode to supervised autonomy batch controller`
- `98ef304 Add supervised autonomy batch controller`
- `349dccd Update roadmap after task loop outcome`
- `6d6515b Task queue improvement: agent-browser-evidence-command-list-v1`
- `82aa419 Update roadmap after task loop outcome`
- `bb4c640 Task queue improvement: agent-browser-readonly-command-classifier-v1`
- `3adc7b2 Update roadmap after task loop outcome`
- `0ca1f5b Task queue improvement: agent-browser-safe-command-plan-markdown-v1`
- `5271f04 Use durable outcome memory for autonomous draft filtering`

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
