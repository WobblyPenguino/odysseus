# Nova v55.3.161 validation

## Fixed from user-attached run

- PowerShell activation confusion and incomplete `.venv` setup are handled by the launcher.
- `START_NOVA_HERE.bat` and companion launchers now say v55.3.161 instead of stale v55.3.159.
- Startup no longer tries to self-upgrade pip during normal setup, avoiding the Windows `~ip` partial-uninstall lock.
- Launcher checks for an already-running Nova server on port 8766 and prevents the browser from connecting to an older stale server.
- Added `/api/version` for launcher/version sanity checks.
- Re-exposed `/media-status`, `/image-plan`, `/video-storyboard`, and `/video-package` through core routes, command palette, quick commands, and tests.
- Added default calm workspace GUI styling to reduce drawer clutter and close right/activity panels on the first v55.3.161 load.

## Validation run

```powershell
python -m compileall -q app.py winlocalassistant
python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py tests_nova_media_refinement_v55_3_160.py tests_nova_clean_gui_docker_v55_3_159.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py
python -m winlocalassistant.validate --all
python app.py /codebase-audit
python app.py /version
```

## Results

- Focused regression tests: PASS, 20 passed.
- Launcher/start-here/release tests: PASS, 15 passed.
- `python -m winlocalassistant.validate --all`: PASS.
- `python app.py /codebase-audit`: PASS, no whole-codebase blocking issues.
- `python app.py /version`: Nova 55.3.161 and version consistency aligned.

## Manual user-flow checks

```text
/media-status
/image-plan cinematic robot dog mascot
/video-storyboard 10 second cinematic trailer about Nova improving a project
/video-package 10 second cinematic trailer about Nova improving a project
```

All four commands returned valid outputs in one-shot CLI testing.
