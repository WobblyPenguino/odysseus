# Nova v55.3.155 validation notes

This release makes `START_NOVA_HERE.bat` the obvious first-run path and adds validation coverage for extracted-tree startup files.

Validation targets:

```powershell
python -m compileall app.py nova winlocalassistant
python -m pytest -q tests_release_hygiene.py tests_nova_start_here_v55_3_155.py tests_nova_better_model_env.py tests_nova_video_manifest.py tests_nova_launchers_v55_3_154.py tests_nova_release_sync_v55_3_154.py
python -m winlocalassistant.validate --all
python app.py /version
```

Expected launcher:

```bat
START_NOVA_HERE.bat
```
