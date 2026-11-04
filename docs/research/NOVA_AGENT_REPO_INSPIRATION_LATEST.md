# Nova Agent Repo Inspiration Latest

Status: Research-only
Date: 2026-06-10

## Safety rule

No source code copied.

This report is for planning only. It must not clone repos, copy external code, or edit Nova runtime source directly. Any idea from this report must be converted into a contracted task with RequiredChangedFiles, RequiredDiffContains, targeted tests, baseline regression tests, and clean-git validation.

## Sources reviewed

- SWE-agent: agent-computer interfaces for repository navigation, editing, and testing.
- OpenHands: sandboxed software-development agents with lifecycle controls and tool interfaces.
- OpenHands Software Agent SDK: production-agent architecture with lifecycle control, sandboxing, multi-model routing, and security analysis.
- SWE-bench: real GitHub issue benchmark showing repository tasks require cross-file reasoning.
- SWE-bench patch-correctness study: passing tests can still allow plausible but incorrect patches.

## Ranked ideas for Nova

### 1. Add a localizer step before every Aider edit

Problem:
Nova currently selects a task and lets Aider edit directly. This can work, but it can also cause drift or collateral changes.

Idea:
Before Aider edits, Nova should write a small localization report:
- likely files
- likely functions/classes
- why each file is relevant
- files that must not be edited
- targeted tests to run

Suggested contracted task:
RequiredChangedFiles:
- run_nova_task_queue_loop.ps1
- tests_task_loop_static_contract.py

RequiredDiffContains:
- NOVA_TASK_LOCALIZATION_LATEST.md
- Write-TaskLocalizationReport
- localization report

Validation commands:
- powershell -NoProfile -ExecutionPolicy Bypass -File .\tools\validate_task_loop_patch.ps1
- powershell -NoProfile -ExecutionPolicy Bypass -File .\run_nova_task_queue_loop.ps1 -Cycles 1 -Mode code -MaxRecoveryCandidates 3 -PreflightOnly

### 2. Add stronger invariant scanning after Aider patches

Problem:
Tests missed bad constants like 127.0.0-1 and 127.0.0..11434 until we added explicit guards.

Idea:
Add a centralized invariant scan for fragile constants:
- loopback URLs
- command names
- generated-noise paths
- known placeholder typos
- suspicious changed URLs

Suggested contracted task:
RequiredChangedFiles:
- run_nova_task_queue_loop.ps1
- tests_task_loop_static_contract.py

RequiredDiffContains:
- Test-DiffAgainstNovaInvariants
- Rejected Nova invariant breach

### 3. Keep research separate from mutation

Problem:
Repo inspiration is useful, but direct code copying is unsafe and may cause licence/security problems.

Idea:
Research tasks should produce docs/research reports only. Human approval should be required before converting a research idea into a code task.

Suggested contracted task:
RequiredChangedFiles:
- docs\research\NOVA_AGENT_REPO_INSPIRATION_LATEST.md

RequiredDiffContains:
- Research-only
- No source code copied
- RequiredChangedFiles
- RequiredDiffContains
