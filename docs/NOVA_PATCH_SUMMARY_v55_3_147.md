# Nova Patch Summary v55.3.147 — Repo Manifest + Session Evidence + Memory Inventory Upgrade

This patch continues the repo-inspired upgrade plan without copying external project code.

## Added

- Repo-inspired capability manifest catalog based on OpenMontage/OpenHands/browser-use/Mem0/LiveKit/Tabby-style architecture ideas.
- `/pipeline-catalog [GOAL] [--write]` to select and optionally snapshot capability manifests.
- `/pipeline-manifest ID` to inspect one manifest contract.
- `/session-evidence [RUN] [LIMIT]` to show OpenHands-style run/tool/file/model evidence from Nova logs.
- `/memory-inventory [PATH]` to audit typed Nova memory stores and project-state health.
- Planner route for repo-integration requests so they inspect manifests/session evidence and run validation instead of jumping straight into a model edit loop.

## Preserved

- the prior typed pipeline preflight, live timeline, browser smoke, project patterns, database audit, Orbit GUI, voice and route hardening.
- Existing startup/Doctor/command/regression validation ladder.

## Validation target

Compileall, targeted pytest, startup validation, Doctor, command verify, browser smoke, bug review, regression sweep, and package hygiene.
