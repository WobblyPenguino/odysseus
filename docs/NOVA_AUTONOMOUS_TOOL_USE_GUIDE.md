# Nova Autonomous Tool Use Guide

Nova's autonomous mode should work as an inspect-plan-act-verify loop, not as unchecked background mutation.

## Safe operating contract

- Prefer read-only inspection first: status, project files, audits, traces and route plans.
- Before mutating project files, produce a narrow plan and identify validation commands.
- After changing code, run the smallest useful targeted tests before broader release checks.
- Record validation evidence and do not claim success without command output.
- Keep legacy command aliases accepted, but expose Nova commands in user-facing help.

## Failure memory and repeated-action handling

- If the same action fails repeatedly, Nova should record the repeated failure signature and avoid looping on the same tool, command, or target.
- Treat a repeated failed action, or a case where the same signature fails again, as a signal to change strategy instead of retrying blindly.
- Repeated failures should trigger a strategy switch: inspect logs, narrow the changed files, or ask for confirmation before another mutating attempt.
- Failure memory should be compact, visible through `/autonomous-memory`, and used as a cooldown signal rather than as a permanent block.

## Verification ladder

A safe autonomous cycle should climb a verification ladder instead of jumping straight to broad claims:

1. Syntax/import check for changed files.
2. Targeted unit test or command contract for the touched feature.
3. Relevant Nova eval pack such as `/nova-eval-packs run core`, `/nova-eval-packs run release`, or `/nova-eval-packs run odysseus`.
4. Broader release checks only after the narrow checks pass.

## Local-model repair loop

When a local-model repair produces invalid code or a failed patch, Nova should treat the output as a draft. It should keep the useful parts, repair locally when possible, and re-run the verification ladder before claiming success.

## Stop conditions

Autonomous mode should stop, pause, or request review when:

- The same failure signature appears repeatedly.
- A validation command fails after a repair attempt.
- A task requires credentials, private data access, email/calendar sending, shell execution, or broad file mutation.
- The finite user goal is already complete.
- The next action has higher risk than the permission scope the user approved.

## Recommended checks

- `/autonomous status`
- `/autonomous-plan GOAL`
- `/improvement-preflight GOAL`
- `/nova-eval-packs run release`
- `/nova-eval-packs run odysseus`
- `/nova-eval-packs run all`
