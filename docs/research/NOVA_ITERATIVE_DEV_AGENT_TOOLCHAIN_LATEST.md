# Nova Iterative Development Agent Toolchain Research

Status: Research-only
Scope: Improve the Nova improvement loop, not Nova product features.
Rule: No source code copied from external repos.

## Goal

Build a local-first iterative development pipeline that can safely improve an existing codebase through narrow tasks, localization, review, validation, rollback, and memory.

## Recommended staged pipeline

1. Snapshot current HEAD, branch, dirty state, tags, failures.
2. Select one narrow source+test task.
3. Write a localization report before mutation.
4. Write a task contract before mutation.
5. Run baseline prechecks.
6. Let Aider edit only allowed files.
7. Generate a local CodeRabbit-style patch review report.
8. Run static analysis/tool status checks.
9. Run targeted tests.
10. Run baseline regression tests.
11. Run invariant checks.
12. Commit or revert.
13. Record result in memory.
14. Reduce scores for repeated failures and cooldown recent successes.
15. Require human approval for broad or risky changes.

## Tool buckets

Agent architecture:
- OpenHands
- SWE-agent
- Aider
- RepoReviewer-style review pipelines

Code review:
- CodeRabbit-style patch summaries
- Qodo-style contextual review
- reviewdog-style comments

Static analysis:
- ruff
- mypy or pyright
- semgrep
- bandit
- pip-audit
- detect-secrets or gitleaks
- vulture
- radon

Testing:
- pytest
- pytest-cov
- pytest-randomly
- mutmut
- hypothesis

Repo understanding:
- ripgrep
- ast-grep
- tree-sitter
- import graph reports

## Highest-value next local implementation

Add a local patch review report:

Path:
- local_ai_cycles\memory\NOVA_PATCH_REVIEW_LATEST.md

Helper:
- Write-PatchReviewReport

It should include:
- task id
- changed files
- allowed files
- unexpected files
- required files
- required diff markers
- targeted tests
- risk notes
- reviewer verdict

This report does not replace validation. It gives Nova and the user a patch-review checkpoint before commit.
