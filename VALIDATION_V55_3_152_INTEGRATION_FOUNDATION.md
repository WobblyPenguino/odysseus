# Validation v55.3.152 Integration Foundation

Commands run in the extracted Linux sandbox:

```bash
python -m compileall app.py nova winlocalassistant
python -m pytest -q tests_nova_orchestration_foundation_v55_3_152.py tests_nova_video_manifest.py tests_nova_video_validation_v55_3_151.py tests_nova_better_model_env.py
python -m pytest -q tests_v55_3_149_repo_upgrade_readiness.py tests_v55_3_150_repo_research_codebase_audit.py tests_nova_webui_startup_guard_v55_3_151.py tests_v55_3_24_webui_js_syntax.py tests_v55_3_93_browser_runtime_reference_hardening.py tests_v55_3_94_codebase_flow_review.py tests_v55_3_97_gui_overhaul.py
```

Results:

- Compileall: passed.
- New orchestration/video/better-model tests: 15 passed.
- Focused upgrade/readiness/web UI regression group: 28 passed.

The complete full-suite command was started in the container but exceeded the available tool execution window. Run the full suite on the Windows target after extraction:

```powershell
python -m pytest -q
```

Known generated artifacts from full validation should be cleaned before committing:

```powershell
git clean -fd code_quality_gates code_reviews codebase_integrity_reports
git restore AUTONOMOUS_IMPROVEMENTS.md docs
```
