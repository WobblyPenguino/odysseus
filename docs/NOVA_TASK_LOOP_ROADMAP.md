# Nova Task Loop Roadmap

Last updated: 2026-06-11T22:10:40

## Current status

- Branch: `nova-task-loop-experiments`
- HEAD: `780a12c`
- Candidate doctor accepted: `16`
- Candidate doctor rejected: `0`
- Fresh candidates available: `6`
- Recently completed/skipped candidates: `10`
- Next candidate: `tiny-autodev-sandbox-status-counts-line-v1`

## Latest commits

- `780a12c Allow Agent Browser safety task candidates`
- `c1c3968 Add Agent Browser safety research`
- `474afe6 Update roadmap after readiness summary blocking`
- `46051e4 Detect task pool exhaustion from loop summary`
- `d763c1d Block autonomy readiness on exhausted task pool`
- `ec2318f Update roadmap after autonomy readiness command`
- `1a6d4ba Add autonomy readiness command`
- `e800161 Rank task loop failures by severity`
- `db30d09 Add autonomy full codebase audit`
- `35bd114 Update roadmap after screen analysis prompt command`
- `0202bfa Add manual screen analysis prompt command`
- `deadf3d Update roadmap after screen command routing`

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
