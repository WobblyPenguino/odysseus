# Nova Patch Summary v55.3.146 — Pipeline + Observability Upgrade

## Purpose

This patch starts the OpenMontage/OpenHands-inspired upgrade plan without a risky rewrite. It adds typed pipeline routing, live timeline evidence, browser smoke checks, and project-pattern memory so broad requests do not fall into unrelated app generation and running tasks expose progress sooner.

## Added

- `winlocalassistant/pipeline_router.py`
  - Classifies broad goals into `project_review`, `database_review`, `qa`, `gui`, `voice`, `coding`, `autonomous`, or `status` pipelines.
  - Renders a preflight contract with stage reasons and validation expectations.
  - Provides `NOVA_PATTERNS.md` project-pattern memory generation.
- `/pipeline-preflight GOAL`
  - Shows the selected pipeline before expensive model calls or mutation.
- `/project-patterns [PATH] [--write]`
  - Inspects a project and optionally writes `NOVA_PATTERNS.md`.
- `/browser-smoke [PATH]`
  - Runs marker checks and `node --check` over extracted Web UI JavaScript.
- `/live-timeline [LIMIT]`
  - Shows recent run/activity events in a compact timeline.

## Improved

- `run_plan()` now logs a pipeline preflight and per-stage start/done events so Live Activity has evidence while a plan is running.
- Autonomous start now records a pipeline preflight event before the worker begins.
- Added regression tests for pipeline classification, commands, project patterns and natural-language project-review routing.

## Safety

- No broad refactor of `core.py` or `tools.py`.
- No automatic network access.
- Project-pattern writes require mutating tools to be enabled.
- Browser smoke is static unless the user explicitly starts a browser harness.
