# Nova v55.3.151 bugfix/video validation notes

Changes:
- Added browser startup guards for stale UI settings and missing `populateSpecChoices`, fixing the screenshot console failure.
- Added video validation, execution dry-run and user-test scenarios on top of manifest-first video planning.
- Added `/video-validate` and `/video-user-test` command/tool surfaces.
- Kept upgraded local model recommendations around qwen3-coder:30b/gemma2:2b/llama3.2-vision.

Validation commands:
```powershell
python -m compileall app.py winlocalassistant
python -m pytest -q
```
