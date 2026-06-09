# Nova Agent Task Queue

Purpose:
Give the local improvement loop explicit, source-backed tasks so it stops making tiny repeated test-only edits.

Rules:
- Prefer source + test changes.
- Test-only changes are allowed only with explicit manual override.
- Each task must name editable files, tests, acceptance criteria, and risk.
- The loop may make no change if the task is already good.
- Never edit broad files like app.py, README.md, CHANGELOG.md, startup scripts, core.py, tools.py, or webui.py without manual approval.

## Task: command-suggestions-behaviour
Editable files:
- winlocalassistant/command_suggestions.py
- tests_command_suggestions.py

Goal:
Improve Nova's command suggestion behaviour only if a real source/test improvement is obvious.

Acceptance:
- Suggestions remain capped and safe.
- Dangerous commands are not suggested.
- Existing command-suggestion tests pass.
- Nova user sanity tests pass.

## Task: command-verifier-contracts
Editable files:
- winlocalassistant/command_verifier.py
- tests_command_verifier.py

Goal:
Improve command verification contracts or reporting if a real edge case is missing.

Acceptance:
- /command-verify stays safe.
- Default contracts do not include mutating commands.
- Existing verifier tests pass.
- Nova user sanity tests pass.

## Task: model-health-timeout
Editable files:
- winlocalassistant/model_health.py
- winlocalassistant/ollama.py
- tests_model_health_timeout.py

Goal:
Improve local-model timeout/fallback reliability only if a real bug or missing edge case is found.

Acceptance:
- Timeout and model-health tests pass.
- Fallbacks do not pretend the model answered.
- Nova user sanity tests pass.

## Task: project-state-continuity
Editable files:
- winlocalassistant/project_state.py
- tests_project_state_continuity.py
- tests_model_context_pack.py

Goal:
Improve Nova's project-state/context continuity only if a real source-backed improvement is obvious.

Acceptance:
- Context/project-state tests pass.
- Generated report noise is cleaned after validation.
- Nova user sanity tests pass.

## Task: validation-status
Editable files:
- winlocalassistant/validate.py
- nova/validate.py
- tests_validation_status_command.py
- tests_validation_reporting.py

Goal:
Improve validation status/reporting behaviour only if it strengthens real validation reliability.

Acceptance:
- Validation tests pass.
- python -m nova.validate --help works.
- Nova user sanity tests pass.
