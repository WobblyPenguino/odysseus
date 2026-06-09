# Codex prompt: full Nova codebase repair and sandbox hardening

You are Codex working on Nova. Your task is to repair the entire codebase without broad rewrites.

## Goals

1. Run syntax and regression checks first.
2. Fix sandbox failures where Docker CLI exists but Docker Desktop/daemon is stopped. Show actionable errors instead of raw npipe failures.
3. Fix project-creation path bugs such as `Tinyappproject/index.html` being written while active workspace is `Tinyapp`, causing `Path.relative_to` crashes.
4. Prevent diagnostic text like `Dodge Game default appeared...` from causing game/collision validation for non-game requests.
5. Keep all UI/audio/chat/release-gate/dependency features intact.
6. Add narrow tests for each fix.

## Validation commands

```powershell
py -3 -m compileall -q winlocalassistant tests_*.py app.py
py -3 -m pytest -q tests_v55_3_48_sandbox_project_hardening.py tests_v55_3_47_dependency_system_test.py tests_release_hygiene.py tests_report_hygiene.py
py -3 -m pytest -q tests_v55_3_46_full_validation_hardening.py tests_v55_3_45_console_feature_hardening.py tests_v55_3_44_validation_feature_audit.py tests_v55_3_43_gui_chat_release_cleanup.py
```

## Rules

- Do not delete user projects or Nova state.
- Do not bypass sandbox safety policy.
- Do not perform external/offensive network action.
- Prefer small targeted fixes with tests.
- Update version metadata, README and CHANGELOG together.
