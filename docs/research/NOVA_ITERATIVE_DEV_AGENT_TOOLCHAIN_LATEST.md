# Nova Iterative Development Agent Toolchain Research

Status: Research-only
Scope: Improve the Nova improvement loop, not Nova product features.
Rule: No source code copied from external repos.

## Goal

Build a local-first iterative development pipeline that can safely improve an existing codebase through narrow tasks, localization, review, validation, rollback, and memory.

## Recommended staged pipeline

1. Snapshot current HEAD, branch, dirty state, tags, failures.
2. Select one narrow task with explicit source files and tests.
3. Write a localization report before mutation.
4. Write a task contract before mutation.
5. Run baseline prechecks.
6. Let Aider or another mutator edit only allowed files.
7. Generate a local CodeRabbit-style patch review report.
8. Run static analysis.
9. Run targeted tests.
10. Run baseline regression tests.
11. Run invariant checks.
12. Commit or revert.
13. Record result in memory.
14. Reduce scores for repeated failures and cooldown recent successes.
15. Require human approval for broad/risky changes.

## Tools to consider

### Agent architecture inspiration
- OpenHands
- SWE-agent
- Aider
- RepoReviewer

### Code review inspiration
- CodeRabbit-style diff review
- Qodo-style contextual review
- reviewdog-style inline comments

### Static analysis
- ruff
- mypy or pyright
- semgrep
- bandit
- pip-audit
- detect-secrets or gitleaks
- vulture
- radon

### Testing
- pytest
- pytest-cov
- pytest-randomly
- mutmut
- hypothesis

### Repo understanding
- ripgrep
- ast-grep
- tree-sitter
- import/dependency graph reports

## Highest-value next local task

Add a local patch review report stage:

Path:
- local_ai_cycles\memory\NOVA_PATCH_REVIEW_LATEST.md

Suggested helper:
- Write-PatchReviewReport

Suggested tests:
- test_task_loop_writes_patch_review_report
- test_task_loop_patch_review_report_mentions_unexpected_files
- test_task_loop_patch_review_report_mentions_validation_commands

Suggested RequiredDiffContains:
- Write-PatchReviewReport
- NOVA_PATCH_REVIEW_LATEST.md
- test_task_loop_writes_patch_review_report

Acceptance:
- Report is generated before commit.
- Report includes changed files, allowed files, unexpected files, risk notes, test commands, and reviewer verdict.
- It does not replace validation; it informs validation.
