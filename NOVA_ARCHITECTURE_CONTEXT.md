# Nova Architecture Context

High-level architecture:
- app.py is the top-level Python entrypoint.
- nova/ provides a lightweight package layer and validation entrypoints.
- winlocalassistant/ contains the main Nova assistant implementation.
- tests_*.py files are the regression suite.
- docs/*_LATEST.* files are generated/updated by validation and should not be hand-edited as the main fix.
- logs/ contains runtime and validation evidence.
- local_ai_cycles/ contains local AI loop scratch logs and context packs.

Important user-facing behaviour to preserve:
- normal chat works
- /help is concise
- /help-full preserves legacy help
- command help is searchable
- composer remains usable after files/activity/help panels
- /write, /read, /verify, /code, /do still work
- /legacy-continuity-audit passes
- /release-readiness passes

Good improvement targets:
- Tests that prevent known regressions.
- Better release-readiness gates.
- Better project-state/current-release memory.
- Better command/help duplication protection.
- Better model timeout/fallback behaviour.
- Better generated-report hygiene through generators/tests, not manual report edits.
- Better local autonomous loop guardrails.

Risky files/areas:
- app.py: requires manual review.
- start_*.bat, start_*.ps1, START_NOVA_HERE.bat: startup scripts require manual review.
- docs/*_LATEST.*, logs/release_readiness/*: generated evidence; usually restore after validation.
- .venv/: never commit.
- new top-level test_*.py files: reject; use existing tests_*.py naming.

Validation baseline:
- python -m compileall -q app.py winlocalassistant nova
- python -m pytest -q tests_model_health_timeout.py tests_runtime_usability_release_gate.py tests_validation_reporting.py tests_validation_status_command.py
- command/help changes should also run tests_command_suggestions.py and tests_command_verifier.py
- project/memory changes should also run tests_project_state_continuity.py tests_model_context_pack.py tests_feature_continuity.py
