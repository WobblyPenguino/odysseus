# Nova Task Loop Roadmap

Last updated: 2026-06-11T20:01:39

## Current status

Nova's task-loop improvement work is making progress. The current branch has a safer autonomous improvement pipeline with:

- external JSON task candidates
- candidate validation and candidate doctor reports
- runtime task registration
- preflight localization
- Aider edit execution
- compile, targeted test, baseline test, generated-noise cleanup, and clean-git gates
- patch review and subagent review reports
- failure review reports for failed live tasks
- protected checks against stale review artifacts and unsafe Markdown fence syntax

Current known good checkpoint:

- Latest validation hardening commit: `44cf409 Reject double-quoted markdown fences in task loop validation`
- Latest successful source/test task: `cb33785 Task queue improvement: tiny-autodev-sandbox-action-plan-debug-json-v1`
- Current external candidate pool status: exhausted cleanly after 8 accepted/recently-completed candidates.

## Completed milestones

### Task-loop safety and validation

- Added external JSON candidate validation.
- Added candidate doctor report and JSON output.
- Added preflight-only task localization.
- Added compile gate coverage for `nova_improvement_lab`.
- Added clean external candidate pool exhaustion behavior.
- Added below-minimum task wording and clean exhausted preflight behavior.
- Added Aider add-file prompt detection and denial summary.
- Added stale review artifact clearing before live runs.
- Added failed live-task review reporting.
- Added validator guard against double-quoted Markdown fences in PowerShell.

### Successful source/test improvements

- `build_action_plan_debug_dict`
- `render_action_plan_debug_lines`
- `render_action_plan_debug_markdown`
- `render_action_plan_debug_json`
- safe prompt-named file signature handling in model context

## Current process rule

Before every patch or task run:

1. Run PowerShell parser audit.
2. Run Markdown fence audit.
3. Run Python compile.
4. Run pytest audit.
5. Run candidate validation.
6. Run task-loop validation.
7. Clean generated noise.
8. Run `git diff --check`.
9. Inspect diff.
10. Commit only after validation.
11. Run preflight proof.
12. Update this roadmap.

## Current blockers / weak spots

### Candidate pool exhaustion

The external JSON candidate pool is currently exhausted. New candidates must be added before another useful live Aider task can run.

### Some built-in tasks are low-scoring or quarantined

Several older built-in tasks remain below the productive threshold or quarantined due to earlier failures, low-value outcomes, or success cooldowns. Avoid forcing them unless deliberately doing a supervised recovery pass.

### Aider can still produce syntax errors

Aider previously produced an unterminated f-string in `tests_autodev_sandbox.py`. The runner rejected it safely, but future task prompts should continue to be narrow, testable, and low-context.

## Near-term roadmap

### Phase 1 — Make the loop easier to operate

- Add a command/script to update this roadmap automatically after each validated commit.
- Add a compact `latest state` report that shows:
  - current commit
  - latest successful task
  - latest failed task
  - candidate pool status
  - next recommended action
- Add a task-loop command that prints the audit checklist before any live run.

### Phase 2 — Improve candidate generation quality

- Add a fresh candidate generator that prefers:
  - small source+test changes
  - existing narrow modules
  - deterministic outputs
  - no GUI/runtime broad edits
- Add validator checks for:
  - overly broad goals
  - risky editable files
  - vague acceptance criteria
  - missing targeted tests
  - repeated recently completed task patterns

### Phase 3 — Improve failure learning

- Make failure review reports include:
  - failed command
  - exit code
  - Aider output tail
  - changed files before reset
  - suggested next safe action
- Add failure categories that distinguish:
  - syntax error
  - test failure
  - off-scope edit
  - no-change
  - low-significance
  - prompt scope failure
  - token/context failure

### Phase 4 — Improve roadmap/memory continuity

- Keep this file updated after every successful improvement.
- Add a JSON version beside it for machine-readable state.
- Link latest roadmap state from task-loop summaries.
- Add a release-readiness note when the roadmap reaches a stable milestone.

## Next recommended action

Add a small roadmap updater script:

- path: `tools/update_task_loop_roadmap.py`
- purpose: update `docs/NOVA_TASK_LOOP_ROADMAP.md` and optionally `docs/NOVA_TASK_LOOP_ROADMAP.json`
- validation: pytest/static contract test
- reason: keeps the local project-state memory current instead of relying only on chat history.

## Standing instruction for future passes

Do not continue to a new feature until:

- parser audit passes
- Markdown fence audit passes
- compile passes
- tests pass
- task-loop validation passes
- git status is clean or expected
- this roadmap is updated
