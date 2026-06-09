# Nova v55.3.141 startup-validation hotfix

## User-reported failure
The Windows startup gate failed in `tests_smoke.py::test_game_fallback_without_ollama` because Nova's early coding fallback returned `source = "early_deterministic_fallback"` while the existing startup regression expected the stable public source label `deterministic_fallback`.

## Fix
- Kept the user-facing/public project source label stable as `deterministic_fallback`.
- Added `phase = "early_after_model_failure"` inside `attempt_history` so Nova still records that the fast path happened after a model timeout/invalid JSON failure.
- Kept the faster fallback behaviour from v55.3.141 intact; this is a contract/compatibility fix, not a rollback.

## Validation
- `python -m pytest -q tests_smoke.py::test_game_fallback_without_ollama tests_game_design.py` → PASS, 7/7
- `python -m winlocalassistant.startup_validation --mode quick --timeout 90` → PASS
- `python app.py /command-verify` → PASS, 19/19
- `python app.py /architecture-audit` → PASS with only existing low advisory for large modules/runtime artifacts before clean packaging
- `python app.py /bug-review` → PASS, 0 critical/high/medium findings
- `python app.py /regression-sweep` → PASS
- Clean package `PYTHONDONTWRITEBYTECODE=1 python app.py /doctor` → PASS, 9/9, 0 warnings

## Notes
Use this hotfix zip instead of the first v55.3.141 zip. It should not block at `Continue anyway for debugging?` during startup validation.
