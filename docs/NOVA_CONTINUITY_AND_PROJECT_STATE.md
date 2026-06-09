# Nova Continuity and Project State

Nova project-state is a small evidence snapshot that connects the current build identity, task evidence, release-readiness report, package manifest, and host-only checks. It exists so prompts like `continue`, `again`, or `do the next best improvement` start from concrete evidence rather than chat memory alone.

## What project-state records

`/project-state` writes:

- current Nova version and root folder
- latest `/release-readiness --full` verdict if present
- latest task evidence files from `logs/task_evidence/`
- changed files recorded by task evidence
- latest package manifest if present
- host-only advisory checks such as Ollama/GPU calibration
- known limitations
- whether packaging is currently allowed
- the safest next action

Latest evidence is written to:

- `docs/NOVA_PROJECT_STATE_LATEST.md`
- `docs/NOVA_PROJECT_STATE_LATEST.json`
- `logs/project_state/`

## Commands

Use:

```text
/project-state
/project-state --json
/project-state --next
/task-evidence
/release-readiness --full
```

`/project-state --next` is the best command after a completed patch, a failed validation run, or a vague prompt like “again”. It summarizes the version, last readiness verdict, known limitations, and safest next step.

## How Nova knows what changed

Nova reads task evidence produced by `/verify`, `/shell`, `/write`, `/do`, and the task execution helper. v55.3.168 adds backwards-compatible fields such as `changed_files`, `verification_commands`, `review_status`, and `repeated_failure_status` so state snapshots can summarize older and newer evidence consistently.

## Deciding the next safe patch

Before editing Nova again:

1. Run `/project-state --next`.
2. Run `/task-contract GOAL` for the proposed next change.
3. Patch narrowly.
4. Run targeted tests.
5. Run `/release-readiness --full`.
6. Package only after PASS.

## What to do when release-readiness fails

Do not package. Open `docs/NOVA_RELEASE_READINESS_LATEST.md`, inspect the first failed required check, fix that exact failure, then rerun `/release-readiness --full`. If the repeated-failure guard is active, stop retrying unchanged commands and inspect `/task-evidence` first.
