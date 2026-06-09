# Nova Local Model Tool Use Guide

Nova should keep local models focused by giving them compact context, explicit tool choices and deterministic verification.

## Model routing

- Use smaller chat models for ordinary answers.
- Use coding/planning models for edits, bug diagnosis and verification plans.
- Send compact project context instead of the full repository where possible.
- When a model proposes actions, route them through Nova's allowlisted commands rather than raw execution.

## Verification loop

- Generate or select targeted checks before editing.
- Run command contracts after route changes.
- Run eval packs after broad refactors.
- Keep traces and receipts so failed outputs can be replayed.

## Verification ladder

- Level 0: answer from existing context without tools.
- Level 1: inspect status, docs or safe local files before deciding.
- Level 2: create a plan with targeted validation.
- Level 3: apply a narrow edit with backup and rollback available.
- Level 4: run focused tests, command contracts or eval packs.
- Level 5: run broader smoke/release checks before claiming completion.

## Repair fallback

- Use surgical fallback when the model output is invalid, too broad, or misses the requested artifact.
- Create a custom tool only when repeated work would benefit from a small validated helper.
- Keep model-generated code as a draft until the verification ladder passes.

Useful commands: `/model-context`, `/context-budget`, `/tool-context-pack`, `/nova-eval-packs`.
