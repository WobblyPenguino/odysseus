# Nova v55.3.159 Clean GUI and Docker Validation Hardening

## Changes

- Added a visible `Nova v55.3.159` version badge in the Orbit header.
- Added default `clean-workspace` GUI mode to reduce visual clutter, keep drawers/panels from fighting the chat, reduce drawer widths, hide redundant hero/workbench blocks, and make command/files/project lists scroll inside their own areas.
- Added a Clean toggle in the header so the user can switch clean mode on/off; the preference is saved in `localStorage`.
- Hardened Docker validation when Docker Desktop or the Linux engine is not running. Nova now reports `SKIPPED` with next steps instead of making it look like the Nova code failed validation.
- Preserved v55.3.158 self-repair and Ollama same-model queue hardening.
- Fixed legacy dependency/massive-system-test regressions in launcher markers and system-test output folder creation.

## Screenshot-derived issue addressed

The provided screenshot showed the Orbit UI with drawers/panels crowding the central chat, no obvious current version label, and Docker validation shown as a failure when the actual error was a missing Docker Desktop Linux engine pipe. v55.3.159 fixes those as layout/diagnostic problems rather than treating them as code-validation failures.

## Validation run

```powershell
python -m compileall -q app.py winlocalassistant
python -m pytest -q tests_nova_clean_gui_docker_v55_3_159.py tests_nova_self_repair_ollama_queue_v55_3_158.py tests_nova_research_voice_v55_3_157.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py tests_v55_3_47_dependency_system_test.py tests_v55_3_116_nova_full_system_test.py tests_request_intent.py tests_planning_dashboard.py
python -m winlocalassistant.validate --all
python app.py /version
python app.py /codebase-audit
```

## Results

- Focused regression slice: PASS.
- Layered validator: PASS.
- CLI `/version`: `Nova 55.3.159`.
- `/codebase-audit`: PASS, no blocking whole-codebase issues.
- A full unbounded `python -m pytest -q` was attempted but exceeded the container execution window before completion; no failure was captured before timeout. The targeted regression set and layered validator passed.
