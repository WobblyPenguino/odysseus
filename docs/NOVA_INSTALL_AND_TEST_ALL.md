# Nova Install and Test All Guide

## Extract and start
1. Extract the zip to a clean folder, for example:
   `C:\Users\Daniel\Documents\Nova_v55_3_164_gui_overhaul_final_patch_20260608`
2. Open PowerShell in the extracted inner Nova folder, the one containing `app.py`.
3. Run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv\Scripts\python.exe -m compileall -q app.py nova winlocalassistant
.\.venv\Scripts\python.exe -m pytest -q tests_smoke.py
.\.venv\Scripts\python.exe -m winlocalassistant.validate --all
```

Using `.\.venv\Scripts\python.exe` avoids the PowerShell activation trust prompt.

## Feature sanity commands
```powershell
python app.py /version
python app.py /status
python app.py /validation-status
python app.py /media-status
python app.py /image-plan cinematic robot dog mascot
python app.py /video-status
python app.py /remote-access-test
python app.py /remote-api-health 127.0.0.1 8767 --dry-run
python app.py /remote-profile-wizard --host 127.0.0.1 --port 8767 --mac AA:BB:CC:DD:EE:FF
python app.py /remote-wake AA:BB:CC:DD:EE:FF --dry-run
python app.py /tool-use-plan fix GUI layout and verify command routes
python app.py /pipeline-route fix GUI layout and media command mismatch
python app.py /role-router fix GUI layout and backend command mismatch
```

## GUI start
```powershell
.\START_NOVA_HERE.bat
```

In the GUI, press `focus` first. Then press `routes`. If route sanity warns about unknown media commands, restart Nova and confirm you are running the extracted patched folder.

## Full validation
```powershell
python -m winlocalassistant.validate --all --full --chunk-size 20
```

If it reports `REVIEW`, inspect `logs/validation_latest.txt` and `logs/validation_progress.jsonl`. Chunked validation is designed to identify the exact failing chunk.
