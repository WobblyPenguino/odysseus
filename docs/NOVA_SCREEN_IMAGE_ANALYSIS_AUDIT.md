# Nova Screen / Image Analysis Audit

Generated: 2026-06-11T20:41:43

## Goal

Assess how Nova can safely use screenshots or uploaded images to help with GUI debugging, terminal-output diagnosis, browser layout checks, and user-provided visual context.

## Safety / scope rules

- Do not enable always-on screen watching.
- Prefer user-provided screenshots or explicit manual capture.
- Keep image analysis optional and auditable.
- Do not redesign GUI in this pass.
- Add pure functions and tests before runtime wiring.

## Findings

### `.aider.chat.history.md`

Matched: Image, PIL, browser, console, gui, image, screen, screenshot, terminal, upload, vision

- `14: > Note: You may need to restart your terminal or command prompt for `setx` to take effect.  `
- `120: Looking at the rules and backlog, I need to identify a safe, low-risk improvement that addresses one of the prioritized areas: normal chat fallback and model timeout behaviour, GUI composer/live-activity/drawer overlap, `
- `139:   2. GUI composer/live-activity/drawer overlap`
- `143:   6. chat/help/GUI/code/write/run regression prevention`
- `193: - Avoid broad GUI redesigns.`
- `199: 2. python -m compileall -q app.py winlocalassistant nova`
- `284: - Avoid broad GUI redesigns.`
- `290: 2. python -m compileall -q app.py winlocalassistant nova`
- `328: - Avoid broad GUI redesigns.`
- `334: 2. python -m compileall -q app.py winlocalassistant nova`
- `444: > Can't initialize prompt toolkit: No Windows console found. Are you running cmd.exe?  `
- `448: > Can't initialize prompt toolkit: No Windows console found. Are you running cmd.exe?  `

### `AGENTS.md`

Matched: gui

- `14:   2. GUI composer/live-activity/drawer overlap`
- `18:   6. chat/help/GUI/code/write/run regression prevention`

### `CHANGELOG.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, terminal, upload, vision

- `22: - Hardened `/release-readiness --full` with clearer plain-English evidence categories for chat fallback, model health, GUI runtime, help, tools, scheduler, autonomous, remote/API, legacy continuity, project contracts and`
- `23: - Reworked the browser runtime evidence path so it starts a real Nova server, verifies `/chat`, renders Nova in Chromium, checks composer/help/drawer/live-activity geometry, and saves screenshot/JSON evidence without rel`
- `24: - Added strict direct request-contract checks for one-file Python, browser games, PowerShell scripts and Nova source edits.`
- `39: - Added final GUI stability layer for composer, Live Activity, cluttered drawers, popup cleanup and `fix UI`.`
- `40: - Added runtime browser diagnostic `window.NovaEmergencyStability.diagnose()`.`
- `47: - Added arcade GUI runtime and header launcher.`
- `48: - Updated build identity/layout storage/cache markers so stale browser builds are visible.`
- `49: - Added tests for arcade metadata, command help, GUI runtime markers and old smoke routes.`
- `55: - Added provider route bar/permission wording in the GUI and dry-run provider validation plans.`
- `56: - Added docs/SUBQ_NVIDIA_PROVIDER_INTEGRATION_V55_3_163.md from the uploaded PDFs.`
- `59: ## v55.3.164 - research-backed efficiency audit and focus GUI`
- `61: - Added `/nova-efficiency-audit` to write a deterministic local-model, GUI and code-health audit.`

### `CODEBASE_OVERVIEW.md`

Matched: browser, console

- `10:   - Supports `--web` for browser UI and one-shot CLI commands like `/nova-mega-test --confirm`.`
- `13:   - Configures console output.`

### `ERROR_INVESTIGATION.md`

Matched: Image, PIL, browser, gui, image

- `69:       "message": "# Nova Linux/Kali Sandbox Status\n\nRuntime available: **True**\nRuntime: `docker` — Docker version 29.5.2, build 79eb04c\nRuntime daemon/engine running: **False**\nRuntime note: failed to connect to th`
- `91:           "image": "python:3.12-slim",`
- `112:           "image": "kalilinux/kali-rolling",`
- `132:         "kali": "Using wla-kali-tools:latest automatically when that local image exists."`
- `138:           "image": "kalilinux/kali-rolling",`
- `157:     "tool": "tool_use_guide",`
- `174:     "tool": "tool_use_guide",`
- `176:     "summary": "Tool use guide",`
- `178:       "guide": "C:\\Users\\Daniel\\Documents\\Nova_v55_3_155_start_here_launcher_audit_hardening_20260606\\docs\\NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md",`
- `179:       "content": "# Nova Tool Use Guide\n\nNova identity: build exactly what the user requested using local tools and local models.\nTask levels 0-5: 0 answer/status, 1 inspect, 2 plan/propose, 3 create or edit a small a`
- `183:         "name": "tool_use_guide",`
- `198:       "tool": "tool_use_guide",`

### `IMPROVEMENTS_SESSION_3.md`

Matched: PIL

- `31: - **Tested**: ✅ py_compile clean, ✅ smoke tests 75/75 passing`
- `46: - **Tested**: ✅ py_compile clean, ✅ smoke tests passing`
- `61: - **Tested**: ✅ py_compile clean, ✅ smoke tests passing (includes game validation tests)`
- `120: python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py`
- `140: - ✅ py_compile verification: INTACT (self_improve_apply_approved uses it)`
- `214: - Each change tested individually with py_compile + smoke tests`

### `IMPROVEMENT_PROPOSALS.md`

Matched: gui

- `89:     "name": "tool_use_guide",`

### `NOVA_AGENT_MEMORY.md`

Matched: gui

- `10: Nova is Daniel's local-first Windows AI assistant. It includes chat, command handling, help, writing, reading, verification, coding, release-readiness validation, project-state memory, local model/Ollama support, GUI/run`

### `NOVA_APPROVED_FEATURE_BACKLOG.md`

Matched: gui

- `19: - Do not redesign GUI.`

### `NOVA_ARCHITECTURE_CONTEXT.md`

Matched: PIL

- `39: - python -m compileall -q app.py winlocalassistant nova`

### `NOVA_DEVELOPMENT_DIRECTOR.md`

Matched: browser, gui

- `4: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `35: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `NOVA_GUARDED_LOCAL_IMPROVEMENT_RULES.md`

Matched: PIL, gui

- `24: - Avoid broad GUI redesigns.`
- `30: 2. python -m compileall -q app.py winlocalassistant nova`

### `playwright.config.js`

Matched: browser, playwright

- `1: const chromiumPath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || '/usr/lib/chromium/chromium';`
- `7:     browserName: 'chromium',`

### `README.md`

Matched: Image, PIL, browser, gui, image, llama3.2-vision, playwright, screen, terminal, upload, vision

- `38: This build keeps the upgraded-PC local model profile (`qwen3-coder:30b`, `gemma2:2b`, `llama3.2-vision:11b`, `nomic-embed-text:latest`), preserves the manifest-first video pipeline, and adds clearer extracted-tree startu`
- `52: This build continues the repo-inspired upgrade timeline by making command verification a direct ToolRegistry tool and adding `/repo-upgrade-assurance` plus `/future-timeline`. These commands verify that pipeline manifest`
- `58: - Added repo-inspired capability manifests adapted from the OpenMontage/OpenHands/browser-use/Mem0/LiveKit/Tabby upgrade plan without copying external code.`
- `64: - Added planner routing for repo-integration prompts so they run manifests, evidence, browser smoke, bug review and regression sweep instead of jumping straight into a model edit loop.`
- `65: - Preserved the prior typed pipeline preflight, browser smoke, live timeline and project-pattern memory features.`
- `75: - Improves Orbit live activity readability, live working updates, chat timestamps, terminal evidence indicators and drawer clarity.`
- `81: This hotfix keeps the previous startup/coding/voice fixes and tightens the Orbit workspace: first load uses the new shell without showing the old GUI, chat lists stay in the drawer, per-chat mute/edit/delete is available`
- `160: - `/verifier-ladder GOAL => RUNTIME` generates runtime-specific syntax, smoke and regression checks for Python, Java, Node, PowerShell, FastAPI and browser projects.`
- `183: Nova v55.3.115 adds a supervised bridge inspired by Jarvis-style daemon/sidecar assistants. Start with `/jarvis-bridge`, `/jarvis-status`, `/sidecar-policy`, and `/proactive-actions list`. Sidecar, shell, browser, screen`
- `186: This release adds a feature-continuity/no-regression audit plus preservation-aware local model repair context so GUI redesigns and implementation attempts add or improve functionality instead of accidentally removing exi`
- `190: ## v55.3.113 GUI cockpit refinement`
- `209: The audit checks build/repair/model/autonomous/regression/sandbox pathways and verifies that prompt contracts, candidate tournaments, iterative repair, build quality, browser runtime tests, model readiness, patch queue a`

### `run_nova_guarded_context_loop.ps1`

Matched: PIL

- `503:     Run-Cmd "python -m compileall -q app.py winlocalassistant nova" $LastTestResults`
- `686:     Append-Success -Target $target -CommitHash (git rev-parse --short HEAD) -TestsPassed "compileall, baseline pytest, target pytest, and area-specific pytest from Validate-Nova" -WhySafe "Only the selected target change`

### `run_nova_guarded_context_loop_slim.ps1`

Matched: PIL

- `402:     Run-Cmd "python -m compileall -q app.py winlocalassistant nova"`

### `run_nova_guarded_continuous.ps1`

Matched: PIL

- `80:     Run-Cmd "python -m compileall -q app.py winlocalassistant nova"`

### `run_nova_local_planner_loop.ps1`

Matched: PIL

- `30:     "`n## Python compile smoke" | Add-Content $contextFile`
- `31:     python -m compileall -q winlocalassistant 2>&1 | Add-Content $contextFile`
- `32:     "compileall exit code: $LASTEXITCODE" | Add-Content $contextFile`

### `run_nova_loop_reliability_gate.ps1`

Matched: PIL

- `83:     Add-Report "- Benefit justification: accepted only after compile checks, targeted tests, baseline regression tests, Nova user sanity tests, generated-noise cleanup, and clean-git verification passed."`
- `115: Add-Report "- compile checks must pass"`
- `125: Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"`
- `152:     Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"`

### `run_nova_significance_gate.ps1`

Matched: PIL

- `104: Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"`
- `136:     Run-Cmd "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py"`

### `run_nova_task_queue_loop.ps1`

Matched: PIL, console, gui, terminal

- `25: # Keep Aider/Rich output safe in Windows PowerShell and VS Code terminals.`
- `36:     [Console]::OutputEncoding = [System.Text.Encoding]::UTF8`
- `328:     if ($lower -match "validation|compileall|py_compile|rejected") { return "validation-failed" }`
- `617:         Goal = "Promote the selected Nova idea-promotion candidate into one tiny source+test improvement. Add explain_next_action(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use `
- `626:         Goal = "Promote idea-2 from the Nova task idea pool into one tiny source+test improvement. Add actionable_work_items(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It mus`
- `635:         Goal = "Promote idea-1 from the Nova task idea pool into one tiny source+test improvement. Add select_next_work_item(items: Iterable[WorkItem]) -> WorkItem | None to nova_improvement_lab\autodev_sandbox.py. It mu`
- `644:         Goal = "Improve the tiny autonomous development sandbox with one small source+test change. Add sort_work_items_by_priority(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. `
- `653:         Goal = "Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py. The helper should return a higher`
- `662:         Goal = "Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py so blocked work ranks above review`
- `746:         Id = "fresh-model-health-guidance"`
- `747:         Goal = "Improve Nova model-health reporting, Ollama readiness guidance, or timeout/fallback diagnostics with a small source-backed source+test patch, only if a real behaviour gap exists. Do not edit winlocalassis`
- `2108:         "- This report does not replace compile, targeted tests, baseline regression tests, generated-noise cleanup, or clean-git gates.",`

### `run_nova_task_queue_loop_with_monitor.ps1`

Matched: terminal

- `51: # Run the real task loop in this terminal. The monitor is only an optional viewer.`

### `Start-NovaLoopMonitor.ps1`

Matched: screen, terminal

- `13: $form.StartPosition = "CenterScreen"`
- `212:         "Terminal-only:",`

### `start_better_models_env.ps1`

Matched: llama3.2-vision, vision

- `9: $env:NOVA_VISION_MODEL = "llama3.2-vision:11b"`
- `18: Write-Host "  Vision: llama3.2-vision:11b"`

### `start_nova_best_models.ps1`

Matched: llama3.2-vision, terminal, vision

- `48:     if (-not (Test-VenvValid $venvPath)) { throw '.venv creation failed. Close terminals using this folder, then run START_NOVA_HERE.bat again.' }`
- `97: $env:NOVA_VISION_MODEL = 'llama3.2-vision:11b'`
- `105: Write-Host 'Fast: gemma2:2b | Vision: llama3.2-vision:11b | Embeddings: nomic-embed-text:latest'`

### `start_nova_desktop_voice_listener.ps1`

Matched: browser, gui

- `5: - Browser SpeechRecognition can only listen while the Nova browser page is open and mic permission is allowed.`
- `6: - This Windows helper runs outside the browser and listens for a tiny grammar such as`
- `8: - When heard, it launches start_windows_assistant.bat in Browser UI mode by setting NOVA_START_CHOICE=2.`
- `28: function Start-NovaGui {`
- `33:     Say-Nova "Nova is starting. I will open the browser interface."`
- `56:             Start-NovaGui`

### `tests_autonomous_failure.py`

Matched: gui

- `236: def test_autonomous_guide_contains_failure_and_stop_guidance() -> None:`
- `237:     guide = Path("docs/NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md").read_text(encoding="utf-8")`
- `238:     low = guide.lower()`

### `tests_autonomous_release_gate.py`

Matched: gui

- `15:     guide = core.handle_command('/autonomous-guide')`
- `16:     assert 'autonomous' in guide.lower()`

### `tests_command_suggestions.py`

Matched: Image, gui, image, screen, screenshot

- `83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `84:     suggestions = suggest_next_commands("gui is broken, blank drawer panel in screenshot")`
- `86:     assert "/gui-visual-test" in commands`
- `91:     commands = _commands("make a video trailer and image storyboard")`
- `93:     assert any(cmd.startswith("/image-plan") or cmd.startswith("/video-package") for cmd in commands)`

### `tests_creation_intent.py`

Matched: Image, PIL, browser, image, screen, screenshot

- `60:         "[Shared file context: screenshot.png | image | id=abc]\n"`
- `61:         "Attached image: screenshot.png\n"`
- `62:         "Type: image/png"`
- `95:         "A browser game with canvas controls",`
- `110:     assert any("py_compile" in cmd for cmd in organiser["verification_commands"])`
- `122:             {"main_file": "index.html", "notes": "Generated browser app", "assumptions": []},`

### `tests_document_ingestion_pdf.py`

Matched: Image, image, playwright

- `17:     assert "honest image generation" in text`
- `23:     result = search_ingested_document(payload, "Validation ladder Playwright image generation")`

### `tests_emergency_stability.py`

Matched: gui

- `23: def test_grouped_help_covers_chat_code_files_run_gui_model():`
- `26:     for group in ['Chat', 'Code', 'Files', 'Run', 'GUI', 'Model']:`
- `55:     from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics`
- `63:     diag = build_gui_layout_diagnostics(ROOT)`

### `tests_feature_continuity.py`

Matched: gui

- `27:         "/tool-guide", "/tool-catalog", "/action-watch", "/interaction-lessons",`
- `36:         "NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md",`
- `37:         "NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md",`

### `tests_file_context.py`

Matched: Image, image, upload, vision

- `14:     image_size,`
- `17:     register_uploaded_file,`
- `18:     resolve_image_context,`
- `22: class _FakeImageEditResult:`
- `25:     message = "Edited a real image with fake backend."`
- `48: def test_upload_png_image_context_records_dimensions() -> None:`
- `52:         ctx = register_uploaded_file("photo.png", png, mime_type="image/png", profile_dir=Path(tmp))`
- `53:         assert ctx.kind == "image"`
- `55:         assert "image-analyze" in ctx.context_text`
- `59: def test_resolve_uploaded_image_by_latest_and_id() -> None:`
- `63:         ctx = register_uploaded_file("latest_photo.png", png, mime_type="image/png")`
- `64:         assert resolve_image_context("latest").context_id == ctx.context_id`

### `tests_full_codebase_bug_sweep_v55_3_9.py`

Matched: upload

- `95: def test_upload_size_should_be_checked_after_decoding_too():`
- `98:     assert "if len(blob) > MAX_UPLOAD_BYTES" in source`

### `tests_game_design.py`

Matched: browser

- `33:     intent = analyze_game_request("make a polished browser game about rabbits")`
- `36:     project = build_generic_canvas_game_project("make a polished browser game about rabbits")`

### `tests_gui_activity_autonomous_sandbox_v55_3_19.py`

Matched: Image, image

- `52: def test_effective_kali_image_prefers_configured_image(monkeypatch, tmp_path):`
- `54:     cfg.sandbox_kali_image = "wla-kali-tools:latest"`
- `56:     assert prof.image == "wla-kali-tools:latest"`

### `tests_gui_ai_help_overlay.py`

Matched: browser, gui

- `7: from winlocalassistant.gui_context_help import build_gui_context_help, render_gui_context_help`
- `13: def test_gui_ai_help_overlay_is_injected_into_html() -> None:`
- `14:     assert "NovaGuiAiHelp" in HTML`
- `17:     assert "/gui-ai-help" in HTML`
- `18:     assert "window.novaGuiAiHelpScan" in HTML`
- `21: def test_gui_ai_help_backend_explains_clicked_file_button(tmp_path: Path) -> None:`
- `23:     reply = core.handle_command('/gui-ai-help {"label":"Project files","command":"toggleOrbitDrawer(\'files\')","id":"files"}')`
- `24:     assert "Nova GUI AI Help" in reply`
- `30: def test_gui_ai_help_backend_routes_media_context() -> None:`
- `31:     payload = build_gui_context_help('{"label":"video package","command":"/video-package make trailer"}')`
- `32:     text = render_gui_context_help(payload)`
- `38: def test_gui_ai_upgrades_command_and_docs_exist(tmp_path: Path) -> None:`

### `tests_gui_cyberpunk_theme.py`

Matched: gui

- `12:     assert "cyberpunk GUI makeover v1" in theme`
- `27:     from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics`
- `30:     diag = build_gui_layout_diagnostics(ROOT)`

### `tests_gui_layout_v55_3_18.py`

Matched: upload

- `40:     assert "Upload files or photos" in HTML`

### `tests_idle_engine.py`

Matched: PIL

- `292:     assert "py_compile" in joined`

### `tests_image_generation_backend.py`

Matched: Image, image

- `9: from winlocalassistant.image_generation import edit_image, generate_image, image_generation_status, prepare_image_prompt`
- `10: from winlocalassistant.image_generation import ImageGenerationResult, render_image_setup_wizard`
- `13: def test_image_generation_status_shape() -> None:`
- `14:     status = image_generation_status()`
- `20: def test_image_setup_wizard_names_generate_edit_and_comfyui() -> None:`
- `21:     text = render_image_setup_wizard()`
- `22:     assert "/image-generate" in text`
- `23:     assert "/image-edit" in text`
- `25:     assert "refuses to fake real image generation" in text`
- `28: def test_generate_image_svg_backend_is_explicit_draft(monkeypatch) -> None:`
- `29:     monkeypatch.setenv("NOVA_IMAGE_BACKEND", "svg")`
- `31:         result = generate_image("blue robot", output_dir=Path(tmp))`

### `tests_nova_agent_upgrade_v55_3_127.py`

Matched: PIL, browser

- `45:     assert any("py_compile" in item["check"] or "run `" in item["check"] for item in calc["behaviours"])`
- `47:     game = build_coding_behavior_tests("make a browser snake game")`

### `tests_nova_arcade_help_completion.py`

Matched: gui

- `51:     from winlocalassistant.gui_layout_diagnostics import build_gui_layout_diagnostics`
- `58:     diag = build_gui_layout_diagnostics(ROOT)`

### `tests_nova_better_model_env.py`

Matched: llama3.2-vision, vision

- `11:     monkeypatch.setenv("NOVA_VISION_MODEL", "llama3.2-vision:11b")`
- `19:     assert cfg.vision_model == "llama3.2-vision:11b"`

### `tests_nova_clean_gui_docker_v55_3_159.py`

Matched: Image, gui, image

- `11: def test_clean_workspace_gui_has_visible_version_and_toggle():`
- `59:     def fake_validate(config, path=".", command="", image="python:3.12-slim", timeout=300):`
- `66:             "image": image,`

### `tests_nova_coding_v55_3_126.py`

Matched: PIL, browser

- `23:     assert "py_compile" in python_plan["verify_command"]`
- `25:     browser_plan = plan_coding_execution("make a browser game with score and controls")`
- `26:     assert browser_plan["artifact_type"] == "html_css_js_game"`
- `27:     assert browser_plan["main_file"] == "index.html"`
- `41: def test_project_type_registry_includes_non_browser_types() -> None:`

### `tests_nova_comprehensive_integration_v55_3_153.py`

Matched: browser, llama3.2-vision, vision

- `6: from winlocalassistant.browser_worker import build_browser_task_plan`
- `27:     plan = build_patch_plan('improve Nova video and browser planning', repo_map)`
- `32: def test_browser_worker_plan_is_read_only_by_default_and_gates_writes():`
- `33:     read_plan = build_browser_task_plan('research this page and summarize it')`
- `36:     write_plan = build_browser_task_plan('login and submit the form')`
- `53:     payload = build_model_registry(['nomic-embed-text:latest', 'qwen3-coder:30b', 'gemma2:2b', 'llama3.2-vision:11b'])`
- `74:         'browser_task_plan': {'goal': 'research a local page'},`
- `85:     for command in ['/repo-map .', '/patch-plan improve Nova', '/browser-plan read docs', '/model-registry', '/integration-review']:`

### `tests_nova_deep_research_v55_3_129.py`

Matched: PIL

- `64:     assert any("py_compile" in step["command"] for step in py_payload["steps"])`

### `tests_nova_efficiency_focus_v55_3_162.py`

Matched: gui

- `30: def test_focus_gui_markers_and_version_present():`

### `tests_nova_fastapi_gui_adaptation_v55_3_137.py`

Matched: gui, upload

- `9:     build_gui_workbench_plan,`
- `28: def test_core_routes_fastapi_and_gui_plans(tmp_path: Path, monkeypatch) -> None:`
- `39:     gui = core.handle_command("/nova-gui-workbench-plan")`
- `40:     assert "Nova Odysseus GUI Workbench Plan" in gui`
- `41:     assert "Left command rail" in gui`
- `42:     assert "/nova-fastapi-plan" in gui`
- `45: def test_gui_workbench_plan_detects_webui_markers() -> None:`
- `47:     payload = build_gui_workbench_plan(root)`
- `56:     assert payload["ui_markers"]["research_upload_windows"] is True`
- `62:     assert any(item["label"] == "Uploads" for item in payload["rail_items"])`
- `100:     assert {"docs", "runtime", "research", "uploads", "compare", "cookbook", "skills", "memory", "gates", "code"}.issubset(ids)`
- `104:     assert payload["commands"]["uploads"] == "/context-files"`

### `tests_nova_gui_startup_routes_v55_3_161.py`

Matched: Image, browser, gui, image, playwright

- `11:     assert "Nova Image Prompt Plan" in core.handle_command("/image-plan cinematic robot dog mascot")`
- `15: def test_gui_exposes_clean_version_and_media_routes():`
- `20:     for command in ["/media-status", "/image-plan", "/video-storyboard", "/video-package"]:`
- `37: def test_gui_sanity_rescue_layout_and_route_probe_are_present():`
- `39:     assert "gui-sanity-rescue" in src`
- `41:     assert "runGuiRouteSanity" in src`
- `53:     assert '"/gui-layout-status"' in src`
- `54:     assert '"/gui-reset-help"' in src`
- `57: def test_gui_layout_overhaul_module_is_injected_and_documents_contract():`
- `60:     docs = (ROOT / "docs" / "NOVA_GUI_ARCHITECTURE.md").read_text(encoding="utf-8")`
- `61:     assert "apply_gui_layout_overhaul" in src`
- `63:     assert "gui-overhaul-v3" in layout`

### `tests_nova_high_spec_subagents_v55_3_156.py`

Matched: llama3.2-vision, vision

- `13:     assert profile.vision_model == "llama3.2-vision:11b"`

### `tests_nova_improvement_assurance_v55_3_131.py`

Matched: PIL

- `56:     good = build_success_claim_audit("Validation passed: py_compile, smoke and targeted pytest. Full suite timed out, so I am not claiming full-suite completion. Windows audio was not live-tested.")`

### `tests_nova_inspiration_v55_3_125.py`

Matched: gui

- `23:     payload = build_handoff_plan("fix GUI and verify no regression", {"command_catalog", "tool_context_pack", "regression_sweep", "release_package"})`
- `59:         "handoff_plan": (dict(prompt="improve GUI and verify"), "Nova Handoff Plan"),`
- `72:     assert "Nova Handoff Plan" in core.chat("/handoff-plan improve GUI")`

### `tests_nova_launchers_v55_3_154.py`

Matched: llama3.2-vision, vision

- `8:     assert "llama3.2-vision:11b" in ps1`

### `tests_nova_media_and_gui_v55_3_156.py`

Matched: Image, gui, image

- `5: from winlocalassistant.image_generation import create_svg_draft`
- `22: def test_gui_exposes_safe_authority_and_subagent_buttons():`
- `30:     image = create_svg_draft("neon rabbit mascot for Nova", output_dir=tmp_path / "images")`
- `31:     assert image.exists()`
- `32:     assert "SVG draft only" in image.read_text(encoding="utf-8")`

### `tests_nova_media_refinement_v55_3_160.py`

Matched: Image, image

- `9: from winlocalassistant.image_generation import build_image_prompt_plan, render_image_prompt_plan_markdown`
- `11:     build_video_image_prompt_plan,`
- `20: def test_image_prompt_plan_creates_variants_without_backend():`
- `21:     plan = build_image_prompt_plan("friendly robot dog mascot", style="concept", variations=3)`
- `25:     assert "Nova Image Prompt Plan" in render_image_prompt_plan_markdown(plan)`
- `32:     prompts = build_video_image_prompt_plan(manifest)`
- `40:     assert Path(package["image_prompts_path"]).exists()`
- `46:     assert "Nova Image Prompt Plan" in core.handle_command("/image-plan robot dog mascot")`
- `55:         "image_plan": {"prompt": "robot dog mascot"},`

### `tests_nova_reliability_v55_3_128.py`

Matched: PIL

- `39:     assert any("py_compile" in cmd for cmd in payload["recommended_commands"])`

### `tests_nova_remote_access_v55_3_164.py`

Matched: gui

- `58:     guide = Path(written["setup_guide"]).read_text(encoding="utf-8")`
- `60:     assert "Do **not** expose Windows Remote Desktop" in guide`
- `61:     assert "NOVA_API_TOKEN" in guide`

### `tests_nova_route_resilience_v55_3_130.py`

Matched: PIL

- `69:     assert payload["hardware_tier"] == "small_gpu_or_cpu_spill_risk"`

### `tests_nova_video_validation_v55_3_151.py`

Matched: browser

- `14:     manifest = plan_video_manifest("Rainy alley. Robot builds a browser game.", project_id="video-test")`

### `tests_project_behaviour_contract.py`

Matched: console

- `18:         (root / "app.js").write_text("document.querySelector('button').addEventListener('click', () => console.log('clicked'));", encoding="utf-8")`
- `28:         (root / "app.js").write_text("function addTask(){ console.log('add'); }", encoding="utf-8")`
- `48:         (root / "app.js").write_text("document.querySelector('button').addEventListener('click', () => console.log('clicked'));", encoding="utf-8")`

### `tests_project_brief.py`

Matched: browser

- `35:     assert brief["artifact_type"] in {"snake_game", "browser_game"}`

### `tests_project_iteration.py`

Matched: console

- `53:     files = {"app.js": "console.log('fix')"}`
- `54:     assert proposed_files_digest(files) == proposed_files_digest({"app.js": "console.log('fix')"})`

### `tests_project_quality_ui.py`

Matched: console

- `19:         (root / "app.js").write_text("console.log('calculator placeholder');", encoding="utf-8")`

### `tests_project_runtime_probe.py`

Matched: console

- `14:         sources={"index.html": "<button>1</button><div id='result'></div>", "app.js": "console.log('static calculator')"},`
- `50:         (root / "app.js").write_text("document.querySelector('button').addEventListener('click', () => console.log('clicked'));", encoding="utf-8")`

### `tests_project_state_continuity.py`

Matched: PIL, browser

- `28:         "required_failed": [] if status == "PASS" else ["compileall"],`
- `40:         command="python -m compileall winlocalassistant",`
- `42:         tests_run=["python -m compileall winlocalassistant"],`
- `107:     payload = build_release_readiness(Path.cwd(), full=True, include_browser=False)`

### `tests_request_intent.py`

Matched: browser

- `63:             reply = core.chat("make a polished browser game about rabbits")`

### `tests_runtime_usability_release_gate.py`

Matched: browser

- `85:     game_contract = build_request_contract("make a browser game")`
- `102:     # Use the actual repo root for a deterministic quick gate.  Browser/full tests`
- `105:     payload = build_release_readiness(root, full=False, include_browser=False)`

### `tests_sandbox_integration_v55_3_16.py`

Matched: console

- `40:     blocked = evaluate_sandbox_command(cfg, "kali", "msfconsole -q")`
- `43:     allowed = evaluate_sandbox_command(cfg, "kali", "msfconsole -q", allow_high_risk=True)`

### `tests_smoke.py`

Matched: gui

- `23: import tests_tool_guides`
- `583:     tests_tool_guides.run_all(verbose=True)`

### `tests_surgical_fallback.py`

Matched: Image, image

- `34:         path = Path(tmp) / "image.bin"`

### `tests_task_decomposition.py`

Matched: gui

- `19:     assert "multiple tasks without explicit order" in plan.ambiguity`

### `tests_task_execution_hardening.py`

Matched: PIL, browser

- `43:     assert any("py_compile" in cmd for cmd in py_contract.verification_commands)`
- `45:     game_contract = build_task_contract("make a browser game", root=tmp_path)`
- `132:     payload = build_release_readiness(root, full=True, include_browser=False)`

### `tests_task_loop_static_contract.py`

Matched: PIL

- `642: def test_task_loop_live_compile_gate_includes_improvement_lab():`
- `644:     assert "python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py" in text`
- `645:     assert "python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py" not in text`
- `771:     assert "python -m py_compile tools/update_task_loop_roadmap.py" in validator`
- `772:     assert "Roadmap updater compile failed" in validator`

### `tests_tool_guides.py`

Matched: gui

- `8: from winlocalassistant.tool_guides import get_autonomous_tool_use_summary, get_local_model_tool_use_summary`
- `11: def test_local_model_guide_file_contains_required_sections() -> None:`
- `12:     text = Path("docs/NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md").read_text(encoding="utf-8")`
- `21: def test_autonomous_guide_file_contains_stop_and_repeated_failure_rules() -> None:`
- `22:     text = Path("docs/NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md").read_text(encoding="utf-8").lower()`
- `29: def test_tool_guide_returns_useful_text_without_writing_workspace_file() -> None:`
- `30:     with tempfile.TemporaryDirectory(prefix="wla_toolguide_") as tmp:`
- `32:         result = registry.tool_use_guide()`
- `37:         assert not (Path(tmp) / "TOOL_USE_GUIDE.md").exists()`

### `tests_v52_5_roadmap.py`

Matched: gui

- `37:     assert "This guide never runs commands" in html`

### `tests_v55_3_100_gui_revert_game_generation.py`

Matched: browser, console

- `58:         "folder": "Simplebrowsergame",`
- `62:             "app.js": "let score = 0; document.getElementById('score').textContent = score; console.log('game');",`

### `tests_v55_3_101_context_aware_repair.py`

Matched: gui

- `39: def test_existing_gui_and_tool_functionality_markers_were_not_removed():`

### `tests_v55_3_102_feature_continuity.py`

Matched: gui

- `28:     assert "Do not remove existing GUI/backend surfaces" in md`
- `42:     text = registry._local_model_implementation_context(Path.cwd(), goal="redesign the GUI and improve the game builder", last_reason="game_missing_collision")`

### `tests_v55_3_103_nova_operating_context.py`

Matched: PIL

- `46:         validation=[{"name": "compile", "ok": True}],`

### `tests_v55_3_104_mission_contract_iterative_repair.py`

Matched: browser

- `40:     contract = project_type_contract("make a browser game about hair")`

### `tests_v55_3_106_adaptive_validation_matrix.py`

Matched: PIL

- `35: def test_validation_matrix_checks_behaviour_not_just_compile():`
- `38:     assert {"python_compile", "webui_contract", "feature_continuity", "behaviour_evidence"}.issubset(names)`

### `tests_v55_3_109_self_routing_repair.py`

Matched: gui

- `38:         "goal": "redesign GUI safely",`

### `tests_v55_3_110_jarvis_bridge.py`

Matched: browser, screen

- `21:     assert {"persistent_daemon", "sidecars", "screen_awareness", "file_access", "shell_access", "browser_control", "proactive_actions"} <= names`
- `25:     assert policy["allow_browser_control"] is False`
- `47:     update_bridge_policy(sidecar_level="off", proactive_level="queue_for_review", allow_shell=False, allow_browser=False, allow_file_write=False)`
- `54:     ctx = build_nova_operating_context(Path.cwd(), goal="integrate jarvis sidecar screen awareness safely")`

### `tests_v55_3_111_jarvis_source_inspired_bridge.py`

Matched: browser, gui, screen, screenshot, terminal

- `16: def test_jarvis_setup_doctor_exposes_docker_ollama_guidance():`
- `26:     payload = build_sidecar_preflight("terminal filesystem browser screenshot")`
- `28:     assert by_name["terminal"]["allowed_by_policy"] is False`
- `30:     assert by_name["browser"]["allowed_by_policy"] is False`
- `31:     assert by_name["screenshot"]["allowed_by_policy"] is False`
- `35:     record = build_authority_decision("browser", "open credentialed site", risk="high")`
- `38:     assert record["capability"] == "browser"`

### `tests_v55_3_112_left_action_jarvis_ui.py`

Matched: browser, gui, playwright, screen, screenshot, terminal

- `10:     build_safe_browser_harness,`
- `23: def test_gui_moves_commands_left_and_right_is_transparent_output():`
- `45:     for name in ["bridge_receipts", "sidecar_enrollment", "browser_harness", "jarvis_test_prompts"]:`
- `49: def test_sidecar_enrollment_and_browser_harness_are_policy_first():`
- `50:     checklist = build_sidecar_enrollment_checklist("terminal filesystem browser screenshot")`
- `53:     harness = build_safe_browser_harness("http://127.0.0.1:3142")`
- `55:     assert "Playwright" in " ".join(harness["steps"])`
- `56:     blocked = build_safe_browser_harness("https://example.com")`
- `68:     assert "/browser-harness http://127.0.0.1:3142" in names`

### `tests_v55_3_115_startup_workflow_audit.py`

Matched: PIL

- `11: def test_startup_validation_compile_mode_passes_for_repo_root():`
- `12:     payload = build_startup_validation(Path.cwd(), mode="compile", timeout=60)`
- `14:     assert any(check["name"] == "compileall" for check in payload["checks"])`
- `17:     assert "compileall" in rendered`

### `tests_v55_3_116_nova_full_system_test.py`

Matched: gui

- `30: def test_gui_exposes_nova_full_system_button():`

### `tests_v55_3_117_completion_hardening.py`

Matched: gui, playwright

- `22:     assert "nova_gui_button_and_palette" in names`
- `41: def test_gui_exposes_completion_audit_button_and_keeps_legacy_marker():`
- `45:     # Older v55.3.100-v116 GUI tests use this marker, so keep it intentionally.`
- `70:     payload = run_massive_system_test(Path.cwd(), include_docker=False, include_playwright=False)`

### `tests_v55_3_118_unified_voice_ux.py`

Matched: screen

- `43: def test_panels_are_resizable_collapsible_and_edge_rail_is_offscreen():`

### `tests_v55_3_119_autonomous_cockpit_reasoning.py`

Matched: PIL

- `53:     core._autonomous_event('act_start', 'Starting: Test compile', {'tool': 'runtime_self_check', 'timeout_sec': 30})`

### `tests_v55_3_120_voice_reliability_security.py`

Matched: screen

- `21:     assert "voiceScreenTranscript" in src`

### `tests_v55_3_121_codebase_packaging_advisor.py`

Matched: gui

- `83: def test_gui_and_validation_contracts_expose_new_commands():`

### `tests_v55_3_133_gui_tabs_resize_theme.py`

Matched: browser

- `15:     assert "Shared browser chat tab context selected by the user" in src`

### `tests_v55_3_137_model_task_classifier.py`

Matched: screen, screenshot, vision

- `22: def test_local_model_classifier_prioritizes_vision_and_document_context() -> None:`
- `23:     assert _kind("summarize this screenshot and identify the controls") == "vision"`

### `tests_v55_3_139_odysseus_layout_sanity.py`

Matched: gui

- `35:         "/nova-gui-workbench-plan",`

### `tests_v55_3_141_clean_studio_gui.py`

Matched: gui

- `7: def test_clean_studio_gui_hotfix_metadata_and_docs():`
- `9:     assert "Clean Studio GUI shell" in VERSION_LABEL`
- `10:     assert "Nova_v55_3_141_clean_studio_gui_hotfix_20260602.zip" in Path("README.md").read_text(encoding="utf-8")`
- `11:     assert "Clean Studio GUI shell hotfix" in Path("CHANGELOG.md").read_text(encoding="utf-8")`

### `tests_v55_3_141_orbit_gui_shell.py`

Matched: gui

- `7: def test_orbit_gui_shell_metadata_and_docs():`
- `9:     assert "Orbit GUI shell" in VERSION_LABEL`

### `tests_v55_3_143_orbit_voice_file_workspace.py`

Matched: PIL, gui

- `20: def test_command_ready_artifact_removed_and_state_pill_present():`
- `22:     assert "orbitStatePill" in WEBUI`
- `57: def test_orbit_inline_gui_handlers_have_function_wrappers():`

### `tests_v55_3_144_orbit_live_activity_voice_project_routing.py`

Matched: browser, screen, terminal

- `27: def test_orbit_live_activity_and_terminal_evidence_markers_are_present() -> None:`
- `29:     assert "messageTerminalHtml" in WEBUI`
- `31:     assert "msgTerminal" in WEBUI`
- `40:     assert "Ready cue could not play until browser audio is unlocked" in WEBUI`
- `43:     assert "redacted.push('Long technical details available on screen.');" in WEBUI`

### `tests_v55_3_146_pipeline_observability.py`

Matched: PIL, gui

- `16:     assert classify_pipeline("fix the GUI live activity drawer layout").kind == "gui"`
- `39:         assert "python -m compileall" in (root / "NOVA_PATTERNS.md").read_text(encoding="utf-8")`

### `tests_v55_3_147_repo_manifest_session_memory.py`

Matched: browser, gui

- `18:     chosen = choose_manifests_for_goal("continue integrating ideas from OpenMontage and browser-use repos")`
- `20:     assert "checkpointed_patch" in ids or "browser_gui_smoke" in ids`
- `24:     assert "browser-use" in text`
- `33:         catalog = registry.call("pipeline_catalog", goal="voice ready sound and GUI browser errors", write=False)`
- `73:     assert "browser_smoke" in tools`

### `tests_v55_3_148_tool_awareness_orchestration.py`

Matched: Image, image

- `74:     assert any(d.tool == "image_plan" for d in media.decisions)`

### `tests_v55_3_149_repo_upgrade_readiness.py`

Matched: browser

- `35:     assert "Real browser click-through" in timeline`

### `tests_v55_3_20_startup_sandbox_autonomy.py`

Matched: Image, browser, image

- `8: def test_windows_bat_opens_browser_for_web_mode():`
- `23: def test_kali_tools_image_preferred_over_default_when_present(monkeypatch, tmp_path):`
- `26:     cfg.sandbox_kali_image = "kalilinux/kali-rolling"`
- `27:     monkeypatch.setattr(sm, "_image_exists", lambda runtime, image: image == "wla-kali-tools:latest")`
- `29:     assert prof.image == "wla-kali-tools:latest"`
- `32: def test_explicit_non_default_kali_image_still_wins(monkeypatch, tmp_path):`
- `35:     cfg.sandbox_kali_image = "my-kali:dev"`
- `36:     monkeypatch.setattr(sm, "_image_exists", lambda runtime, image: True)`
- `38:     assert prof.image == "my-kali:dev"`

### `tests_v55_3_21_chat_gui_policy.py`

Matched: Image, image

- `18:     monkeypatch.setattr(core, "_with_shared_file_context", lambda text: text + "\n\nUse these user-shared files as context. Nova can pass this image to /image-analyze.")`

### `tests_v55_3_23_sandbox_permission_ui.py`

Matched: gui

- `84: def test_network_target_detection_distinguishes_local_and_public_targets():`

### `tests_v55_3_25_docker_diagnostics.py`

Matched: Image, image

- `33:             return {"ok": True, "stdout": '{"Names":"wla-test","Image":"python:3.12-slim","Status":"Up 2 seconds"}\n', "stderr": "", "returncode": 0, "command": args}`
- `34:         if "images" in cmd:`

### `tests_v55_3_26_docker_validation_backend.py`

Matched: Image, PIL, image

- `24:         return {"ok": True, "returncode": 0, "stdout": "compiled", "stderr": "", "elapsed_sec": 0.1, "command": args}`
- `47:     reply = core.handle_command("/docker-validate python -m compileall -q winlocalassistant")`
- `50:     assert calls[0][1]["command"] == "python -m compileall -q winlocalassistant"`
- `56:     def fake_validate(config, path=".", command="", image="python:3.12-slim", timeout=300):`
- `57:         return {"ok": True, "summary": "Docker validation passed", "run_id": "test", "image": image, "command": command, "workspace_copy": str(tmp_path), "copy_info": {"copied_files": 2, "skipped_items": 0}, "raw": {"std`

### `tests_v55_3_27_autonomous_docker_integration.py`

Matched: Image, PIL, image

- `27: def test_autonomous_docker_preflight_skips_surprise_image_pull(tmp_path, monkeypatch):`
- `32:         return ToolResult(True, "Docker is ready", {"installed": True, "daemon_running": True, "images": []})`
- `50:         assert "compileall" in kwargs["command"]`

### `tests_v55_3_28_docker_history_cleanup.py`

Matched: Image, PIL, image

- `17:         "command": "python -m compileall -q winlocalassistant",`
- `18:         "image": "python:3.12-slim",`

### `tests_v55_3_29_docker_patch_validation.py`

Matched: PIL

- `89:     assert "compileall" in calls[0][1]["command"]`

### `tests_v55_3_31_autonomous_patch_promotion.py`

Matched: PIL

- `71:     globbed = _run_local_command("python -m compileall -q tests_*.py", cwd=tmp_path)`

### `tests_v55_3_32_less_strict_sandbox_policy.py`

Matched: Image, image

- `47:     monkeypatch.setattr(sm, "_image_exists", lambda runtime, image: False)`

### `tests_v55_3_34_patch_integrity_release_gate.py`

Matched: PIL

- `42:     assert any(cmd["name"] == "compileall" for cmd in payload["commands"])`

### `tests_v55_3_35_integration_radar.py`

Matched: browser, playwright

- `14:     assert "Playwright browser smoke tests" in names`

### `tests_v55_3_37_backend_chats_release_project_memory.py`

Matched: gui, playwright

- `57: def test_playwright_smoke_scaffold_exists():`
- `58:     spec = Path("playwright/nova_gui_smoke.spec.js")`
- `61:     assert "playwright" in text.lower()`
- `62:     assert "hello playwright smoke test" in text`

### `tests_v55_3_39_gui_project_validation_polish.py`

Matched: Image, image

- `45: def test_linux_sandbox_defaults_to_python_ready_image(tmp_path):`
- `47:     assert cfg.sandbox_linux_image == "python:3.12-slim"`

### `tests_v55_3_40_validation_cleanup.py`

Matched: Image, image

- `14: def test_image_generate_without_backend_does_not_write_svg(tmp_path, monkeypatch):`
- `15:     monkeypatch.setenv("NOVA_IMAGE_BACKEND", "auto")`
- `19:     out = core.chat("/image-generate blue robot mascot")`
- `20:     assert "image generation is not ready" in out.lower()`
- `21:     assert "no real image-generation backend" in out.lower()`
- `22:     assert not list((Path(tmp_path) / "generated_images").glob("*.svg"))`

### `tests_v55_3_42_remaining_features.py`

Matched: Image, image, playwright

- `47: def test_release_gate_records_playwright_skip_without_failing(tmp_path):`
- `49:     payload = run_wla_release_gate(root, "playwright optional check", "python -m pytest -q tests_release_hygiene.py tests_report_hygiene.py")`
- `51:     assert "playwright_smoke" in names`
- `52:     assert names["playwright_smoke"].get("ok") is True`
- `55: def test_project_target_and_image_setup_commands(tmp_path):`
- `60:     image = core.handle_command("/image-setup-help")`
- `61:     assert "Image generation status" in image`
- `62:     assert "Stable Diffusion" in image or "Diffusers" in image`
- `70:     assert "playwright" in Path("winlocalassistant/wla_doctor.py").read_text(encoding="utf-8")`

### `tests_v55_3_45_console_feature_hardening.py`

Matched: Image, browser, console, image

- `16: def test_favicon_route_prevents_console_404_noise():`
- `19:     assert 'self._send(204, b"", "image/x-icon")' in src`
- `46: def test_feature_audit_includes_browser_console_hygiene(tmp_path):`
- `49:     assert "browser_console_hygiene" in names`
- `50:     assert names["browser_console_hygiene"]["status"] == "implemented"`

### `tests_v55_3_46_full_validation_hardening.py`

Matched: PIL

- `51:     assert "compileall" in names`

### `tests_v55_3_47_dependency_system_test.py`

Matched: playwright

- `79:     payload = run_massive_system_test(tmp_path, include_docker=True, include_playwright=False)`

### `tests_v55_3_48_sandbox_project_hardening.py`

Matched: Image, image

- `217:                 "image": "python:3.12-slim",`

### `tests_v55_3_49_intent_voice_mode.py`

Matched: browser

- `43: def test_voice_mode_command_explains_browser_speech_path() -> None:`

### `tests_v55_3_54_upgrade_voice_selector.py`

Matched: gui, playwright

- `18:     assert "Playwright GUI smoke tests" in text`

### `tests_v55_3_55_optional_upgrade_installer.py`

Matched: playwright

- `22:     assert {"ruff", "precommit", "playwright"}.issubset(keys)`

### `tests_v55_3_56_comprehensive_review.py`

Matched: PIL

- `22:     assert any(f.kind == "compiled_python" for f in findings)`

### `tests_v55_3_57_sandbox_autonomy_validation.py`

Matched: browser

- `17: def test_browser_static_acceptance_catches_broken_dom_ids(tmp_path: Path):`

### `tests_v55_3_63_blueprint_trace_gui_mcp.py`

Matched: gui, playwright

- `7: from winlocalassistant.gui_redesign import build_gui_feature_map, gui_regression_check`
- `10: from winlocalassistant.visual_regression import build_gui_snapshot_status`
- `43: def test_gui_feature_map_and_regression_cover_classic_features():`
- `44:     fmap = build_gui_feature_map(Path.cwd())`
- `47:     assert gui_regression_check(Path.cwd())["ok"]`
- `60:     status = build_gui_snapshot_status(Path.cwd())`
- `61:     assert "command" in status and "playwright" in status["command"]`
- `69:     assert "GUI Feature Map" in app.handle_command("/gui-feature-map")`
- `71:     assert "GUI Visual Regression" in app.handle_command("/gui-visual-test")`

### `tests_v55_3_70_major_upgrade_layers.py`

Matched: PIL

- `3: from winlocalassistant.prompt_test_compiler import build_prompt_contract, validate_contract`

### `tests_v55_3_86_quality_runtime_learning.py`

Matched: browser, gui

- `8:     build_browser_runtime_test,`
- `11:     build_gui_cockpit_v2,`
- `30: def test_quality_and_browser_runtime_detect_notes_app(tmp_path):`
- `35:     b = build_browser_runtime_test(tmp_path, "notes app with localStorage and JSON export")`
- `43:     assert build_gui_cockpit_v2(tmp_path)["classic_preserved"] is True`
- `57:     for tool in ["build_quality_report", "browser_runtime_test", "model_reliability", "patch_queue", "feature_readiness", "support_report", "mistake_learning_status"]:`
- `61:         "/browser-run-test notes app",`
- `64:         "/gui-feature-coverage",`

### `tests_v55_3_90_iterative_coding_autonomy.py`

Matched: browser, console

- `26: def test_iterative_loop_uses_quality_browser_and_surgical_tools(tmp_path):`
- `28:     (tmp_path / "app.js").write_text("console.log('ok')", encoding="utf-8")`
- `33:     assert "browser_runtime_test" in tools`

### `tests_v55_3_91_model_download_manager.py`

Matched: llama3.2-vision, screen, screenshot, vision

- `19:     report = build_model_readiness("build code and analyse a screenshot", tmp_path)`
- `23:     assert "llama3.2-vision" in md`
- `60:     plan = build_mutable_mission_plan("download the required model for a vision repair task")`

### `tests_v55_3_93_browser_runtime_reference_hardening.py`

Matched: browser, console

- `7: def test_webui_defines_all_runtime_functions_seen_in_browser_console():`
- `59:             "app.js": "const missing = document.getElementById('result'); console.log(missing);",`

### `tests_v55_3_94_codebase_flow_review.py`

Matched: browser

- `14:     assert scripts, "webui.py should embed a browser script"`
- `18: def test_webui_browser_script_references_existing_dom_ids() -> None:`

### `tests_v55_3_95_nova_gui_project_generation.py`

Matched: browser, gui

- `15: def test_version_and_nova_gui_controls_are_updated() -> None:`
- `86:     result = reg.ai_create_project("make a polished browser game about rabbits", build_mode="long")`

### `tests_v55_3_97_gui_overhaul.py`

Matched: gui

- `12: def test_version_bumped_for_gui_overhaul() -> None:`
- `16: def test_gui_has_refined_cockpit_markers_without_losing_inspector() -> None:`

### `tests_validation_chunked_full.py`

Matched: browser

- `14:         "browser_worker.py",`

### `tests_validation_reporting.py`

Matched: PIL

- `90:     assert any('"event": "section_started"' in line and '"section": "compileall"' in line for line in lines)`

### `tests_validation_status_command.py`

Matched: PIL

- `16:                 {"name": "compileall", "ok": True, "detail": {"elapsed_sec": 0.1}},`
- `24:             json.dumps({"ts": 1, "event": "section_started", "section": "compileall"}),`
- `25:             json.dumps({"ts": 2, "event": "section_completed", "section": "compileall", "ok": True, "detail": {"elapsed_sec": 0.1}}),`

### `tests_webui_planning_visibility.py`

Matched: gui

- `7: def test_gui_version_matches_package_version() -> None:`

### `tests_whole_codebase_real_bugfix_v55_3_8.py`

Matched: Image, PIL, gui, image

- `14:     for cmd in ["/autonomous-status", "/autonomous-guide", "/deps-status", "/providers", "/version", "/image-status"]:`
- `83: def test_code_review_does_not_flag_internal_ast_compile(tmp_path: Path):`
- `86:     (pkg / "audit_like.py").write_text("import ast\n\ndef check(text):\n    tree = ast.parse(text)\n    compile(tree, '<x>', 'exec')\n", encoding="utf-8")`

### `VALIDATION_BETTER_MODELS_VIDEO_PATCH.md`

Matched: Image, PIL, browser, gui, image, llama3.2-vision, vision

- `8: - Added environment override support for `NOVA_MODEL`, `NOVA_CODE_MODEL`, `NOVA_CHAT_MODEL`, `NOVA_PLANNER_MODEL`, `NOVA_VISION_MODEL`, and `NOVA_LOCAL_MODEL_TIMEOUT_SEC`.`
- `12:   - vision: `llama3.2-vision:11b``
- `27: python -m compileall app.py winlocalassistant`
- `29: python -m pytest -q tests_v52_roadmap.py tests_v52_5_roadmap.py tests_v55_3_23_sandbox_permission_ui.py tests_v55_3_24_webui_js_syntax.py tests_v55_3_25_docker_diagnostics.py tests_v55_3_26_docker_validation_backend.py t`
- `30: python -m pytest -q tests_model_health_timeout.py tests_image_generation_backend.py tests_v55_3_140_safety_validation_dock.py tests_v55_3_139_odysseus_layout_sanity.py`
- `36: - Compile: passed.`
- `39: - GUI compatibility group: passed.`
- `40: - Image/model-health/safety layout tests: passed.`

### `VALIDATION_V55_3_151_BUGFIX_VIDEO.md`

Matched: PIL, browser, console, llama3.2-vision, screen, screenshot, vision

- `4: - Added browser startup guards for stale UI settings and missing `populateSpecChoices`, fixing the screenshot console failure.`
- `7: - Kept upgraded local model recommendations around qwen3-coder:30b/gemma2:2b/llama3.2-vision.`
- `11: python -m compileall app.py winlocalassistant`

### `VALIDATION_V55_3_152_INTEGRATION_FOUNDATION.md`

Matched: PIL, browser, gui

- `6: python -m compileall app.py nova winlocalassistant`
- `8: python -m pytest -q tests_v55_3_149_repo_upgrade_readiness.py tests_v55_3_150_repo_research_codebase_audit.py tests_nova_webui_startup_guard_v55_3_151.py tests_v55_3_24_webui_js_syntax.py tests_v55_3_93_browser_runtime_r`
- `13: - Compileall: passed.`

### `VALIDATION_V55_3_153_COMPREHENSIVE_INTEGRATION.md`

Matched: PIL, browser

- `4: This patch focused on the repo-integration blueprint priorities: repo map, safe patch planning, browser worker planning, document ingestion/RAG fixture, model role registry, and comprehensive integration review.`
- `8: - `python -m compileall app.py nova winlocalassistant` — PASS`
- `20: - `/browser-plan research a local page``

### `VALIDATION_V55_3_154_REGRESSION_HARDENING.md`

Matched: PIL, browser, gui

- `8: python -m compileall app.py nova winlocalassistant`
- `11: python -m pytest -q tests_release_hygiene.py tests_nova_better_model_env.py tests_nova_video_manifest.py tests_nova_video_validation_v55_3_151.py tests_nova_orchestration_foundation_v55_3_152.py tests_nova_comprehensive_`

### `VALIDATION_V55_3_155_START_HERE_HARDENING.md`

Matched: PIL

- `8: python -m compileall app.py nova winlocalassistant`

### `VALIDATION_V55_3_156_AUTONOMOUS_MEDIA_SUBAGENTS.md`

Matched: Image, PIL, gui, image, llama3.2-vision, vision

- `10: - A high-spec local model profile is exposed for the upgraded PC: `qwen3-coder:30b`, `gemma2:2b`, `llama3.2-vision:11b`, `nomic-embed-text:latest`.`
- `12: - GUI live activity gained a `Pin latest` toggle so reading older logs is not constantly forced back to the top/latest output.`
- `27: /image-draft neon rabbit mascot for Nova`
- `28: /image-status`
- `34: python -m compileall -q app.py nova winlocalassistant`
- `35: python -m pytest -q tests_nova_autonomous_continuous_v55_3_156.py tests_nova_high_spec_subagents_v55_3_156.py tests_nova_media_and_gui_v55_3_156.py`

### `VALIDATION_V55_3_157_RESEARCH_VOICE_HARDENING.md`

Matched: PIL, gui

- `18: python -m compileall -q app.py winlocalassistant`
- `20: python -m pytest -q tests_nova_research_voice_v55_3_157.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py tests_nova_autonomous_continuous_v55_3_156.py tests_nova_media_and_gui_v55_3_156.py tests_nova_high`

### `VALIDATION_V55_3_158_SELF_REPAIR_OLLAMA_QUEUE.md`

Matched: PIL

- `13: python -m compileall -q app.py winlocalassistant`

### `VALIDATION_V55_3_159_CLEAN_GUI_DOCKER_HARDENING.md`

Matched: PIL, gui, screen, screenshot

- `1: # Nova v55.3.159 Clean GUI and Docker Validation Hardening`
- `6: - Added default `clean-workspace` GUI mode to reduce visual clutter, keep drawers/panels from fighting the chat, reduce drawer widths, hide redundant hero/workbench blocks, and make command/files/project lists scroll ins`
- `12: ## Screenshot-derived issue addressed`
- `14: The provided screenshot showed the Orbit UI with drawers/panels crowding the central chat, no obvious current version label, and Docker validation shown as a failure when the actual error was a missing Docker Desktop Lin`
- `19: python -m compileall -q app.py winlocalassistant`
- `20: python -m pytest -q tests_nova_clean_gui_docker_v55_3_159.py tests_nova_self_repair_ollama_queue_v55_3_158.py tests_nova_research_voice_v55_3_157.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py tests_v55`

### `VALIDATION_V55_3_160_MEDIA_REFINEMENT.md`

Matched: Image, PIL, gui, image

- `3: Added `/media-status`, `/image-plan`, `/video-storyboard`, and `/video-package`.`
- `8: python -m compileall -q app.py winlocalassistant`
- `9: python -m pytest -q tests_nova_media_refinement_v55_3_160.py tests_nova_clean_gui_docker_v55_3_159.py tests_nova_self_repair_ollama_queue_v55_3_158.py tests_nova_research_voice_v55_3_157.py tests_release_hygiene.py`

### `VALIDATION_V55_3_161_GUI_STARTUP_MEDIA_ROUTE_HARDENING.md`

Matched: Image, PIL, browser, gui, image

- `8: - Launcher checks for an already-running Nova server on port 8766 and prevents the browser from connecting to an older stale server.`
- `10: - Re-exposed `/media-status`, `/image-plan`, `/video-storyboard`, and `/video-package` through core routes, command palette, quick commands, and tests.`
- `11: - Added default calm workspace GUI styling to reduce drawer clutter and close right/activity panels on the first v55.3.161 load.`
- `16: python -m compileall -q app.py winlocalassistant`
- `17: python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py tests_nova_media_refinement_v55_3_160.py tests_nova_clean_gui_docker_v55_3_159.py tests_nova_release_sync_v55_3_154.py tests_release_hygiene.py`
- `35: /image-plan cinematic robot dog mascot`

### `webui_extracted.js`

Matched: Image, PIL, browser, clipboard, gui, image, playwright, screen, screenshot, terminal, upload

- `17:  {group:'Verify',label:'Validation matrix',command:'/validation-matrix',desc:'Compile, GUI contract, Feature-continuity audit and behaviour evidence checks',tags:'validation matrix regression evidence'},`
- `18:  {group:'Verify',label:'Startup validation',command:'/startup-validation',desc:'Run the same compile/smoke gate used by the startup .bat file',tags:'startup gate compile smoke pytest'},`
- `19:  {group:'Verify',label:'Nova full system test',command:'/nova-system-test',desc:'One-button test for chat routing, coding, GUI, voice/persona, Jarvis, startup and regression slices',tags:'nova full system test all one bu`
- `25:  {group:'Integrations',label:'Jarvis bridge',command:'/jarvis-bridge',desc:'Show safe daemon/sidecar/proactive action capability map',tags:'jarvis daemon sidecar proactive screen shell browser'},`
- `28:  {group:'Integrations',label:'Sidecar policy',command:'/sidecar-policy',desc:'Show or change external sidecar/screen/browser authority gates',tags:'sidecar policy screen browser shell safety'},`
- `29:  {group:'Integrations',label:'Sidecar preflight',command:'/sidecar-preflight terminal filesystem browser screenshot',desc:'Preview sidecar capabilities against current policy without enabling them',tags:'sidecar prefligh`
- `30:  {group:'Integrations',label:'Authority gate',command:'/bridge-authority browser open-site localhost low',desc:'Queue/deny external actions through authority receipts instead of executing silently',tags:'authority gate b`
- `33:  {group:'Integrations',label:'Sidecar enrollment',command:'/sidecar-enrollment terminal filesystem browser screenshot',desc:'Checklist before trusting a sidecar',tags:'sidecar enrollment checklist safety'},`
- `34:  {group:'Integrations',label:'Browser harness',command:'/browser-harness http://127.0.0.1:3142',desc:'Plan safe Playwright-only browser control for localhost/project URLs',tags:'browser harness playwright localhost jarvi`
- `40:  {group:'Verify',label:'Visual test',command:'/visual-test .',desc:'Browser/screenshot-style project checks',tags:'visual browser test'},`
- `41:  {group:'Tools',label:'Tool guide',command:'/tool-guide',desc:'How the model should choose tools',tags:'guide tools planner'},`
- `75:  {group:'Tests',label:'Playwright scaffold',command:'/playwright-smoke-help',desc:'Browser smoke test instructions'},`

### `.nova_runtime\browser_smoke_webui_extract.js`

Matched: Image, PIL, browser, clipboard, console, gui, image, llama3.2-vision, playwright, screen, screenshot, terminal, upload, vision

- `28:  {group:'Verify',label:'Validation matrix',command:'/validation-matrix',desc:'Compile, GUI contract, Feature-continuity audit and behaviour evidence checks',tags:'validation matrix regression evidence'},`
- `29:  {group:'Verify',label:'Startup validation',command:'/startup-validation',desc:'Run the same compile/smoke gate used by the startup .bat file',tags:'startup gate compile smoke pytest'},`
- `30:  {group:'Verify',label:'Nova full system test',command:'/nova-system-test',desc:'One-button test for chat routing, coding, GUI, voice/persona, Jarvis, startup and regression slices',tags:'nova full system test all one bu`
- `36:  {group:'Integrations',label:'Jarvis bridge',command:'/jarvis-bridge',desc:'Show safe daemon/sidecar/proactive action capability map',tags:'jarvis daemon sidecar proactive screen shell browser'},`
- `39:  {group:'Integrations',label:'Sidecar policy',command:'/sidecar-policy',desc:'Show or change external sidecar/screen/browser authority gates',tags:'sidecar policy screen browser shell safety'},`
- `40:  {group:'Integrations',label:'Sidecar preflight',command:'/sidecar-preflight terminal filesystem browser screenshot',desc:'Preview sidecar capabilities against current policy without enabling them',tags:'sidecar prefligh`
- `41:  {group:'Integrations',label:'Authority gate',command:'/bridge-authority browser open-site localhost low',desc:'Queue/deny external actions through authority receipts instead of executing silently',tags:'authority gate b`
- `44:  {group:'Integrations',label:'Sidecar enrollment',command:'/sidecar-enrollment terminal filesystem browser screenshot',desc:'Checklist before trusting a sidecar',tags:'sidecar enrollment checklist safety'},`
- `45:  {group:'Integrations',label:'Browser harness',command:'/browser-harness http://127.0.0.1:3142',desc:'Plan safe Playwright-only browser control for localhost/project URLs',tags:'browser harness playwright localhost jarvi`
- `51:  {group:'Verify',label:'Visual test',command:'/visual-test .',desc:'Browser/screenshot-style project checks',tags:'visual browser test'},`
- `52:  {group:'Tools',label:'Tool guide',command:'/tool-guide',desc:'How the model should choose tools',tags:'guide tools planner'},`
- `66:  {group:'Verify',label:'Verifier ladder',command:'/verifier-ladder build Java CLI => java',desc:'Generate runtime-specific syntax, smoke and regression checks',tags:'verifier ladder python java node powershell browser'},`

### `codebase_integrity_reports\codebase_integrity_20260609_224413_421402900_c14083.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_224804_342206600_201483.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_230022_817010400_4ebe95.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_230358_025228400_8b4c14.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_230953_227907300_b28854.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_231207_596987500_2ba8f7.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_231540_880272900_ebffe5.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_231825_556989700_aff9b6.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_232051_880695500_53729f.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_232423_406267200_d8c4ec.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_232938_619524000_14fe55.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_233319_051114300_2b4eab.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_233902_483086100_48aeb0.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `codebase_integrity_reports\codebase_integrity_20260609_234236_105720400_5a0b6b.md`

Matched: PIL, browser, gui

- `7: Version: `55.3.168` — v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-mac`
- `25: - Parsed and compiled 416 Python file(s) without syntax errors.`
- `45: python -m compileall -q winlocalassistant tests_*.py app.py`

### `code_quality_gates\code_quality_gate_20260609_224359_845832200_63dcba.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_224404_217037500_01db84.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_230010_843935000_e240a6.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_230014_834241500_e1c5a3.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_230941_277781700_351026.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_230945_254099300_f9c4d3.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_231155_723123800_668c4e.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_231159_684681900_f73898.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_231813_811111000_e55ed6.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `198:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `223: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_231817_681324100_1eeb14.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `198:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `223: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_232040_034501000_bc209f.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_232043_928072500_804fec.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_232925_849154900_5a45cc.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_232929_872133800_9fea72.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_233850_437830300_6edae7.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_quality_gates\code_quality_gate_20260609_233854_425276100_c4e172.md`

Matched: PIL, browser, gui

- `36:    - location: `winlocalassistant/gui_context_help.py:118``
- `203:    - why it matters: `_fallback_browser_game_project` is 246 lines long, which makes autonomous repair riskier.`
- `228: python -m compileall -q winlocalassistant tests_*.py`

### `code_reviews\code_review_20260609_224406_999073600_4ced00.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_230017_379024000_f90a60.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_230947_811219300_e24b24.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_231202_219318200_b12166.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_231820_169216300_45d702.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `137: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_232046_445044300_71b72a.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_232932_375032300_9406af.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `code_reviews\code_review_20260609_233856_975959200_0d4bb0.md`

Matched: PIL, gui

- `25:    - location: `winlocalassistant/gui_context_help.py:118``
- `141: 4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.`

### `docs\AGENT_TOOL_USE_GUIDE.md`

Matched: gui

- `1: # Agent Tool Use Guide`

### `docs\AI_CONTEXT_START_HERE.md`

Matched: PIL, browser, gui

- `6: Nova is a Windows-first local assistant with a CLI, browser GUI, optional FastAPI bridge, local model routing, project tooling, scheduling, autonomous/idle workflows, remote PC access helpers, and validation/reporting ga`
- `13: - `winlocalassistant/webui.py`: legacy static browser UI shell. Avoid large rewrites.`
- `14: - `winlocalassistant/webui_layout_overhaul.py`: current modular GUI layout override layer. Prefer editing this for drawer/layout fixes.`
- `17: - `winlocalassistant/validate.py`: compile, test and chunked validation runner.`
- `23: 4. Run compile checks and targeted tests.`
- `31: ## GUI contextual AI help overlay`
- `33: If the user says the GUI is confusing or asks for small help symbols on controls, inspect:`
- `36: - `winlocalassistant/gui_context_help.py``
- `37: - `winlocalassistant/gui_layout_diagnostics.py``
- `38: - `tests_nova_gui_startup_routes_v55_3_161.py``
- `40: The commands `/gui-ai-help`, `/gui-context-help`, `/gui-command-help`, and `/gui-ai-upgrades` are read-only help/planning helpers. They must not auto-run mutating commands.`

### `docs\CODEX_REPAIR_PROMPT_V55_3_48.md`

Matched: PIL, console, gui

- `17: py -3 -m compileall -q winlocalassistant tests_*.py app.py`
- `19: py -3 -m pytest -q tests_v55_3_46_full_validation_hardening.py tests_v55_3_45_console_feature_hardening.py tests_v55_3_44_validation_feature_audit.py tests_v55_3_43_gui_chat_release_cleanup.py`

### `docs\IMPLEMENTATION_STATUS_V55_3_41.md`

Matched: Image, browser, gui, image, playwright

- `6: - Customisable quick commands with add/edit/move/delete/reset and saved browser state.`
- `18: - Linux sandbox switched to a Python-ready image by default.`
- `19: - Honest image generation: `/image-generate` only uses real backends; `/image-draft` is explicitly a placeholder.`
- `23: - Full GUI release/security checklist view exists as popup/checklist but could be expanded into a richer docked panel.`
- `24: - Playwright smoke tests are scaffolded but not automatically run by release gate unless you run them manually.`

### `docs\INTEGRATION_BLUEPRINT_ADAPTATION_V55_3_152.md`

Matched: browser

- `38: - Risky browser, Windows utility and autonomous execution work remains gated by future worker-specific approvals.`

### `docs\INTEGRATION_RADAR_LATEST.md`

Matched: browser, gui, playwright

- `7: Recommendation: Highest value next integration: Playwright browser smoke tests, because Nova has had real GUI regressions that static tests only partly cover.`
- `11:   - Next: Keep Docker as the main patch simulation backend and add profile history/GUI review.`
- `19: - **Playwright browser smoke tests** (ready, priority 86): Catch Send-button and JavaScript UI failures through real browser interaction, not just static JS parsing.`
- `20:   - Next: Add a browser smoke test for sending chat, toggling tabs and Docker panel buttons.`
- `21:   - Command: `npx playwright test``
- `40: ✅ **Playwright browser smoke tests** — ready — risk `medium``

### `docs\INTEGRATION_REVIEW_V55_3_153.md`

Matched: browser, vision

- `7: - browser-worker dry-run plans with read-only defaults and approval gates`
- `9: - local model role registry that prevents embedding/vision models from being selected for chat/code`
- `12: The code stays adapter-first: it does not copy external repo code or run risky browser/system actions.`

### `docs\INTENT_AND_VOICE_MODE_UPDATE_20260527.md`

Matched: PIL, browser, console, gui

- `4: Implemented a focused Nova update that improves natural-language intent handling and adds browser-based voice mode.`
- `13: - Added GUI microphone button beside Send.`
- `15: - Added browser SpeechRecognition / webkitSpeechRecognition microphone capture.`
- `22: ## Browser/runtime notes`
- `23: Voice mode is browser-side. Microphone transcription depends on browser/OS support. Chrome and Edge usually support SpeechRecognition best. Spoken replies use speechSynthesis. No new cloud backend is added by this patch.`
- `26: - `python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py tests_v55_3_49_intent_voice_mode.py``
- `28: - `python -m pytest -q tests_v55_3_49_intent_voice_mode.py tests_request_intent.py tests_intent_planning.py tests_task_decomposition.py tests_v55_3_36_audio_gui_memory.py tests_v55_3_44_validation_feature_audit.py``
- `30: - `python -m pytest -q tests_v55_3_24_webui_js_syntax.py tests_v55_3_45_console_feature_hardening.py tests_v55_3_49_intent_voice_mode.py tests_v55_3_36_audio_gui_memory.py``

### `docs\LOCAL_AI_RESEARCH_NOTES_V55_3_162.md`

Matched: gui, playwright, screen, screenshot

- `7: - Playwright visual comparison/screenshot workflows are appropriate for catching GUI regressions that unit tests miss.`
- `10: Implemented in this patch: /nova-efficiency-audit, focus-workspace GUI, validation markers, and docs output.`

### `docs\NOVA_ARCADE_AND_HELP_COMPLETION.md`

Matched: PIL, browser, console, gui

- `8: - Adds the first game, `Nova: System Runner`, as a cyberpunk browser canvas game.`
- `9: - Adds a backend registry in `winlocalassistant/nova_arcade.py` so future games can be listed without rewriting the core GUI.`
- `10: - Adds `winlocalassistant/webui_arcade.py` to inject the local game overlay into the browser shell.`
- `15: - Arcade is local-only and stores high score in browser `localStorage`.`
- `28: - `/command-help gui``
- `31: ## Browser checks`
- `41: Console checks:`
- `44: - `window.novaGuiLayoutDiagnose()``
- `52: python -m compileall -q app.py nova winlocalassistant`
- `53: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests_nova_arcade_help_completion.py tests_gui_interaction_overhaul.py tests_smoke.py`

### `docs\NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md`

Matched: gui

- `1: # Nova Autonomous Tool Use Guide`

### `docs\NOVA_BROWSER_RUNTIME_TEST_LATEST.md`

Matched: browser, playwright, screen, screenshot

- `1: # Nova Browser Runtime Test`
- `9: - browser rendered Nova HTML`
- `14: Screenshot: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\docs\runtime_evidence\nova_runtime_usability_playwright.png``

### `docs\NOVA_BUILD_IDENTITY_AND_CACHE_RECOVERY.md`

Matched: browser, gui

- `3: Nova keeps the compatibility version `55.3.164` across several safe patches. That preserves launchers and old tests, but it can make a stale browser/server look like the newest patch.`
- `5: Use these checks when debugging GUI or backend mismatch problems:`
- `9: /gui-layout-status`
- `13: The GUI header also includes a `build` button. `/api/version` and `/api/build-info` return the same patch ID and source fingerprint.`
- `15: ## Browser reset`
- `22: gui-reset-adaptive-routing-build-identity-v1`

### `docs\NOVA_BUILD_QUALITY_LATEST.md`

Matched: browser

- `10: - ❌ **html_links_js** — HTML should reference app.js for browser apps.`
- `20: - Fix html_links_js: HTML should reference app.js for browser apps.`

### `docs\NOVA_COMPREHENSIVE_USER_TEST_LATEST.md`

Matched: gui

- `15: - ✅ **gui_feature_map** — GUI feature map has no missing required features`
- `16: - ✅ **gui_regression** — GUI regression check completed`
- `27: - For GUI issues, run `/gui-feature-map` and `/gui-regression-test` before switching GUI modes.`

### `docs\NOVA_CYBERPUNK_THEME.md`

Matched: PIL, browser, console, gui

- `5: This patch adds a modular **Cyberpunk 2077 inspired** visual skin to Nova's GUI.`
- `24: - `python -m compileall -q app.py nova winlocalassistant``
- `25: - `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q tests_gui_cyberpunk_theme.py tests_nova_gui_startup_routes_v55_3_161.py tests_smoke.py``
- `30: 2. Open the GUI and hard refresh.`
- `33: 5. In the browser console run:`
- `34:    - `window.novaGuiLayoutDiagnose()``

### `docs\NOVA_DOCTOR_LATEST.md`

Matched: PIL

- `22: - Run the validation ladder before shipping: compileall -> targeted pytest -> web UI JS parse -> Docker validation when available.`

### `docs\NOVA_EFFICIENCY_AUDIT_LATEST.md`

Matched: gui, playwright, screen, screenshot

- `10: - **Playwright visual comparisons**: Screenshot baselines catch GUI regressions that unit tests miss. Action: Keep optional Playwright visual tests and add a calm-layout screenshot smoke test for the chat/drawers/popups.`
- `11: - **OpenTelemetry-style instrumentation**: Spans and structured events make failures visible across agent, tool, model and GUI layers. Action: Continue replacing silent exceptions with structured events that self-repair `
- `16:   - Fix: Prefer additive extraction around stable seams: routing tables, GUI command metadata, media planning, and audits should live in smaller modules with focused tests.`
- `18:   - Found 321 broad exception handlers without structured logging. Examples: scripts\run_gui_runtime_test.py:31, scripts\run_gui_runtime_test.py:197, scripts\run_gui_runtime_test.py:200, scripts\run_gui_runtime_test.py:2`
- `20: - **MEDIUM / gui** — Monolithic GUI file is a regression risk (winlocalassistant/webui.py)`
- `26: - Run a focused pytest slice for changed GUI/media/model files.`
- `29: - Use optional Playwright visual smoke tests before changing GUI layout again.`

### `docs\NOVA_EMERGENCY_STABILITY_FIX.md`

Matched: PIL, browser, console, gui

- `15: ## Browser checks`
- `16: Open the GUI and run in console:`
- `20: window.novaGuiLayoutDiagnose()`
- `28: python -m compileall -q app.py nova winlocalassistant`

### `docs\NOVA_FASTAPI_API_BRIDGE.md`

Matched: browser, gui

- `3: Nova now includes an optional FastAPI sidecar instead of a risky backend rewrite. The existing CLI and browser UI remain the source of truth; the API bridge exposes safe HTTP routes for dashboards, evals, workbench launc`
- `32: `POST /api/v1/command` is read-only by default. Commands classified as mutating or privileged are blocked unless the caller sets `allow_mutation=true`. This keeps the API useful for GUI panels and automation dashboards w`

### `docs\NOVA_FASTAPI_MIGRATION_PLAN.md`

Matched: gui

- `3: Decision: **Yes, Nova would benefit from FastAPI for the GUI/API/event layer, but not from a risky one-shot rewrite.**`
- `18: - serve static GUI assets separately from backend logic`
- `28: Avoid breaking the working CLI, tests and voice launcher while giving the GUI real API endpoints.`

### `docs\NOVA_FEATURE_AUDIT_LATEST.md`

Matched: Image, browser, console, gui, image, playwright

- `10: - ✅ **spoken_audio_and_controls** — implemented: Browser speech, microphone voice input, microphone diagnostic preflight, long-response summarisation, mute/unmute and tutorial controls are wired in the GUI.`
- `20: - ✅ **playwright_scaffold** — implemented: Playwright GUI smoke scaffold exists and release gate runs/skips it depending on environment readiness.`
- `23: - 🟡 **image_generation_status** — environment_dependent: Image generation refuses to fake real generation and provides setup guidance for SD WebUI/Diffusers/ComfyUI.`
- `24:   - Remaining: Actual generation depends on a reachable/configured local image backend.`
- `25: - ✅ **browser_console_hygiene** — implemented: The web UI avoids favicon 404 noise, avoids Web Audio before a user gesture, preserves LLM context text while refreshing, and supports multi-command quick buttons.`
- `27: - ✅ **linux_sandbox_python_ready** — implemented: General Linux sandbox defaults to a Python-ready image and aliases python3 where possible.`
- `31: - Actual generation depends on a reachable/configured local image backend.`

### `docs\NOVA_FEATURE_CONTINUITY_LATEST.md`

Matched: browser, gui

- `8: - ✅ **webui:chat_input** — required browser/UI markers are present`
- `9: - ✅ **webui:project_panel** — required browser/UI markers are present`
- `10: - ✅ **webui:toolbox** — required browser/UI markers are present`
- `11: - ✅ **webui:live_activity_runs** — required browser/UI markers are present`
- `12: - ✅ **webui:assistant_box** — required browser/UI markers are present`
- `13: - ✅ **webui:audio_guard** — required browser/UI markers are present`
- `14: - ✅ **webui:inspector** — required browser/UI markers are present`
- `15: - ✅ **webui:settings_popup** — required browser/UI markers are present`
- `16: - ✅ **webui:validation_matrix** — required browser/UI markers are present`
- `17: - ✅ **webui:role_router** — required browser/UI markers are present`
- `18: - ✅ **webui:jarvis_bridge** — required browser/UI markers are present`
- `19: - ✅ **webui:left_action_cockpit** — required browser/UI markers are present`

### `docs\NOVA_GUI_AI_HELP_OVERLAY.md`

Matched: browser, console, gui

- `1: # Nova GUI AI Help Overlay`
- `3: This patch adds small semi-transparent `?` symbols to interactive GUI elements and important panels.`
- `8: - Clicking a dot opens a local browser help panel with element context.`
- `9: - The help panel can ask Nova to explain the element with `/gui-ai-help`, or generate adaptive plans with `/tool-use-plan`, `/pipeline-route`, and `/role-router`.`
- `14: - `winlocalassistant/webui_ai_help_overlay.py` — browser overlay CSS/JS injection.`
- `15: - `winlocalassistant/gui_context_help.py` — backend context-to-command help renderer.`
- `17: - `winlocalassistant/core.py` — routes `/gui-ai-help`, `/gui-context-help`, `/gui-command-help`, and `/gui-ai-upgrades`.`
- `18: - `winlocalassistant/gui_layout_diagnostics.py` — static contract checks for layout and help overlay.`
- `23: /gui-ai-help {"label":"files","command":"toggleOrbitDrawer('files')"}`
- `24: /gui-ai-upgrades`
- `25: /gui-layout-status`
- `27: /pipeline-route fix a GUI layout issue and verify command routes`

### `docs\NOVA_GUI_ARCHITECTURE.md`

Matched: Image, PIL, gui, image

- `1: # Nova GUI Architecture Notes`
- `4: The GUI is a legacy single-file static HTML shell inside `winlocalassistant/webui.py`. It includes many historic compatibility markers and tests depend on route strings being present.`
- `10: - `apply_gui_layout_overhaul(HTML)` in `webui.py``
- `21: ## Regression tests to run after GUI changes`
- `23: python -m compileall -q winlocalassistant/webui.py winlocalassistant/webui_layout_overhaul.py`
- `24: python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py tests_command_suggestions.py`
- `25: python -m pytest -q tests_v55_3_24_webui_js_syntax.py tests_v55_3_141_clean_studio_gui.py tests_v55_3_142_orbit_workspace_drawer.py tests_webui_planning_visibility.py tests_webui_idle_status.py`
- `28: ## Manual GUI checks`
- `42: /image-plan cinematic robot dog mascot`
- `45: /tool-use-plan fix GUI layout and choose correct tools`

### `docs\NOVA_GUI_COCKPIT_V2_LATEST.md`

Matched: gui

- `1: # GUI Cockpit v2 Preview`
- `3: Mode: `gui-feature-coverage``
- `15: - run /gui-regression-test and /gui-visual-test before default switch`

### `docs\NOVA_GUI_INTERACTION_OVERHAUL.md`

Matched: browser, console, gui

- `1: # Nova GUI Interaction Overhaul`
- `3: Patch identity: `gui-autonomous-interaction-fix-v1`.`
- `9: - `winlocalassistant/webui_interaction_overhaul.py` — browser-only interaction layer.`
- `16: Open Nova and run in the browser console:`
- `24: Expected GUI features:`
- `48: - `docs/NOVA_GUI_INTERACTION_OVERHAUL_VISUAL_20260609.png``
- `49: - `logs/gui_interaction_overhaul_visual_20260609.json``

### `docs\NOVA_GUI_LAYOUT_STATUS.md`

Matched: browser, console, gui, screen, screenshot, terminal, upload

- `1: # Nova GUI Layout Status and Recovery`
- `9: - `winlocalassistant/gui_layout_diagnostics.py` contains read-only static layout contract checks.`
- `10: - `tests_nova_gui_startup_routes_v55_3_161.py` contains the focused GUI route/layout regression tests.`
- `17: python app.py /gui-layout-status`
- `18: python app.py /gui-visual-test`
- `19: python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py`
- `22: In the browser header, click:`
- `25: - `layout` to run browser geometry checks`
- `29: ## Browser console check`
- `34: window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose()`
- `43: 1. Stop the Nova terminal.`
- `44: 2. Close the browser tab.`

### `docs\NOVA_GUI_RESET_AND_ROUTE_DIAGNOSTICS.md`

Matched: Image, PIL, browser, console, gui, image

- `1: # Nova GUI Reset and Route Diagnostics`
- `3: Purpose: give future humans or AI agents a fast way to diagnose the exact class of GUI bug where the browser shows a stale drawer, a ghost right panel, or command buttons that look available but return `Unknown command`.`
- `7: - `winlocalassistant/webui.py` — legacy static web UI, endpoint handlers, header buttons and browser helpers.`
- `9: - `winlocalassistant/gui_layout_diagnostics.py` — static layout contract and reset guidance shown by `/gui-layout-status` and `/gui-reset-help`.`
- `10: - `tests_nova_gui_startup_routes_v55_3_161.py` — GUI route/layout regression tests.`
- `18: - `layout` runs browser geometry diagnostics.`
- `19: - `reset UI` clears stale browser layout keys and reapplies `gui-overhaul-v3` without deleting backend data.`
- `25: /gui-layout-status`
- `26: /gui-reset-help`
- `28: /image-plan cinematic robot dog mascot`
- `33: ## Browser console check`
- `36: window.novaGuiLayoutDiagnose && window.novaGuiLayoutDiagnose()`

### `docs\NOVA_GUI_VISUAL_VERIFICATION.md`

Matched: Image, gui, image, playwright

- `1: # Nova GUI visual verification`
- `3: This patch was visually checked with a headless Chromium/Playwright render at a 1920x1000 viewport using Nova's generated HTML.`
- `14: Evidence image:`
- `16: - `docs/NOVA_GUI_VISUAL_VERIFICATION_20260608.png``
- `30: Future GUI-edit rule: do not put new layout overrides back into the large HTML string unless unavoidable. Prefer `winlocalassistant/webui_layout_overhaul.py`, then add a route/static test in `tests_nova_gui_startup_route`

### `docs\NOVA_INSTALL_AND_TEST_ALL.md`

Matched: Image, PIL, gui, image

- `1: # Nova Install and Test All Guide`
- `5:    `C:\Users\Daniel\Documents\Nova_v55_3_164_gui_overhaul_final_patch_20260608``
- `13: .\.venv\Scripts\python.exe -m compileall -q app.py nova winlocalassistant`
- `26: python app.py /image-plan cinematic robot dog mascot`
- `32: python app.py /tool-use-plan fix GUI layout and verify command routes`
- `33: python app.py /pipeline-route fix GUI layout and media command mismatch`
- `34: python app.py /role-router fix GUI layout and backend command mismatch`
- `37: ## GUI start`
- `42: In the GUI, press `focus` first. Then press `routes`. If route sanity warns about unknown media commands, restart Nova and confirm you are running the extracted patched folder.`

### `docs\NOVA_INTERACTION_FLOW_AUDIT_LATEST.md`

Matched: browser, vision

- `12:   - commands: `/prompt-contract`, `/candidate-tournament`, `/iterative-code-loop`, `/build-quality-report`, `/browser-run-test`, `/model-output-coach``
- `13:   - tools: `prompt_contract`, `candidate_tournament`, `iterative_coding_loop`, `build_quality_report`, `browser_runtime_test`, `model_output_coach``
- `14:   - capabilities: `prompt_to_test`, `candidate_tournament`, `iterative_coding_repair`, `build_quality_browser_runtime``
- `43:   - selected: build_quality_browser_runtime, project_build, model_output_coach, model_reliability_controller, templates_preview_feature_readiness`
- `46:   - selected: build_quality_browser_runtime, surgical_repair, bug_review, project_build`
- `59: - Keep generated-project flows gated by prompt contracts, candidate tournaments and browser/runtime quality checks.`
- `61: - Require model-readiness checks before model-heavy/vision/coding tasks and explicit --confirm before downloads.`

### `docs\NOVA_LEGACY_CONTINUITY_GUARD.md`

Matched: gui

- `3: Nova has accumulated many valuable features across v55.3.139-v55.3.164: Odysseus-style workspace surfaces, wake/voice reliability, resize rails, live timeline observability, command verification, provider routing, remote`
- `19: Before any major patch is packaged, Nova should check that important historic capability anchors still exist. This prevents accidental deletion of old functionality when new GUI/theme/autonomous patches are added.`

### `docs\NOVA_LOCAL_AI_PERFORMANCE_TUNING.md`

Matched: upload

- `3: This document implements the safe parts of the uploaded performance research PDF.`
- `11: - `/perf-artifact-checklist` - show exactly what to upload for further tuning.`

### `docs\NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md`

Matched: gui

- `1: # Nova Local Model Tool Use Guide`

### `docs\NOVA_MAINTENANCE_VALIDATION_LATEST.md`

Matched: Image, PIL, image

- `14: - WARN **image_backend_test_env**: Image backend is enabled; fallback tests must clear image env first`
- `19: - **image_backend_test_env**: Image backend is enabled; fallback tests must clear image env first`
- `22: - `python -W error::SyntaxWarning -m compileall -q app.py winlocalassistant tests_smoke.py``
- `24: - `$env:NOVA_IMAGE_BACKEND='auto'; $env:NOVA_DIFFUSERS_MODEL=''; $env:NOVA_ALLOW_DIFFUSERS_DOWNLOAD='0'; python -m pytest``

### `docs\NOVA_MASSIVE_SYSTEM_TEST_LATEST.md`

Matched: PIL, playwright

- `17: - ✅ **compileall**: stubbed`
- `22: - ✅ **playwright_optional** (skipped): Playwright unavailable or scaffold missing`

### `docs\NOVA_MEGA_TEST_LATEST.md`

Matched: Image, PIL, browser, console, gui, image, llama3.2-vision, playwright, screen, screenshot, vision

- `12: - ✅ gui_feature_map`
- `13: - ✅ gui_regression`
- `14: - ✅ gui_visual_gate`
- `31: - ✅ browser_runtime_tester`
- `36: - ✅ gui_cockpit_v2`
- `57: - MISSING pillow (optional) — image utilities and future real image outputs`
- `62: - PASS npm — 11.13.0 — Playwright browser smoke tests`
- `85: - ✅ **spoken_audio_and_controls** — implemented: Browser speech, microphone voice input, microphone diagnostic preflight, long-response summarisation, mute/unmute and tutorial controls are wired in the GUI.`
- `95: - ✅ **playwright_scaffold** — implemented: Playwright GUI smoke scaffold exists and release gate runs/skips it depending on environment readiness.`
- `98: - 🟡 **image_generation_status** — environment_dependent: Image generation refuses to fake real generation and provides setup guidance for SD WebUI/Diffusers/ComfyUI.`
- `99:   - Remaining: Actual generation depends on a reachable/configured local image backend.`
- `100: - ✅ **browser_console_hygiene** — implemented: The web UI avoids favicon 404 noise, avoids Web Audio before a user gesture, preserves LLM context text while refreshing, and supports multi-command quick buttons.`

### `docs\NOVA_ODYSSEUS_ADAPTATION_PLAN.md`

Matched: gui

- `10: 2. **Cookbook-style local model setup** — scan hardware, recommend fitting models, then provide one-click or one-command setup guidance.`

### `docs\NOVA_ODYSSEUS_FULL_FEATURE_PORT.md`

Matched: Image, gui, image, upload, vision

- `3: Source: uploaded odysseus-main.zip and public README feature map`
- `26:   - Adaptation: Nova now detects RAM/CPU/NVIDIA VRAM where available, accepts what-if hardware hints, ranks local model choices and prints install/serve guidance without auto-downloading.`
- `43: - **Extras: uploads, vision, image, themes, sessions, web search, presets, 2FA style hardening** — `native_plus_scaffold` via `/attach-file, /image-analyze, /image-generate, /chats, /nova-presets, /nova-theme-plan, /nova`
- `44:   - Adaptation: Nova already has file/image/chat/web search surfaces; this patch adds presets plus theme/auth hardening plans.`

### `docs\NOVA_ODYSSEUS_GUI_WORKBENCH_PLAN.md`

Matched: gui, screen

- `1: # Nova Odysseus GUI Workbench Plan`
- `11: - Modal/fullscreen surfaces: documents, cookbook, compare, research reports and tasks`
- `33: ## Next GUI panels`

### `docs\NOVA_PATCH_SUMMARY_v55_3_139.md`

Matched: PIL, gui

- `8: - The GUI already had Odysseus-inspired workbench pieces, but the main centre workspace still looked like a chat panel first and hid the workspace map inside the left drawer/popup.`
- `21: - `python -m compileall -q app.py winlocalassistant` -> PASS.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_140.md`

Matched: PIL, gui

- `12: - The main GUI now includes an Odysseus-style validation command dock directly below the voyage workspace cards.`
- `17: - The new GUI buttons fill commands only; they do not auto-run checks or mutate project files.`
- `22: - Compileall passed for `app.py` and `winlocalassistant`.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_141.md`

Matched: PIL, gui

- `3: This patch targets the user-reported GUI, voice and coding-flow issues from the attached run log.`
- `19: - Compile checks for `app.py` and `winlocalassistant`.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_141_clean_studio_gui.md`

Matched: gui, screen

- `1: # Nova v55.3.141 clean Studio GUI hotfix`
- `10: - Odysseus voyage cards and validation dock are still present in the source/workbench, but no longer dominate the default screen.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_142.md`

Matched: browser, gui

- `3: This patch responds to GUI usability feedback from the Odysseus-inspired shell. It keeps backend routes and IDs stable while changing the presentation layer so panels dock and reserve space instead of covering the chat.`
- `18: The patch is GUI/browser-side except for release metadata and tests. No shell execution, auto-apply, file mutation policy, project deletion, Jarvis/sidecar authority, or model routing permissions were broadened.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_143.md`

Matched: PIL, gui, screen, screenshot

- `3: This patch addresses the user feedback from the Orbit GUI screenshots/log output. It keeps the Odysseus-inspired layout but removes the remaining legacy flash, reduces speech noise, improves chat/file management, and sto`
- `7: - Network-first service worker and body-level Orbit shell class so the new GUI appears on first load.`
- `10: - Top-left Nova state pill shows current state without needing hover.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_144.md`

Matched: browser, gui, terminal

- `8: - Added visible message timestamps and collapsed terminal/evidence indicators for assistant replies.`
- `12: - Made the Hey Nova ready cue more visible and added browser-audio unlock/fallback status.`
- `21: - Dedicated v55.3.144 GUI/routing regression tests.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_146.md`

Matched: browser, gui

- `5: This patch starts the OpenMontage/OpenHands-inspired upgrade plan without a risky rewrite. It adds typed pipeline routing, live timeline evidence, browser smoke checks, and project-pattern memory so broad requests do not`
- `10:   - Classifies broad goals into `project_review`, `database_review`, `qa`, `gui`, `voice`, `coding`, `autonomous`, or `status` pipelines.`
- `17: - `/browser-smoke [PATH]``
- `33: - Browser smoke is static unless the user explicitly starts a browser harness.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_147.md`

Matched: PIL, browser, gui

- `7: - Repo-inspired capability manifest catalog based on OpenMontage/OpenHands/browser-use/Mem0/LiveKit/Tabby-style architecture ideas.`
- `16: - the prior typed pipeline preflight, live timeline, browser smoke, project patterns, database audit, Orbit GUI, voice and route hardening.`
- `21: Compileall, targeted pytest, startup validation, Doctor, command verify, browser smoke, bug review, regression sweep, and package hygiene.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_148.md`

Matched: browser, gui, playwright, screen, screenshot

- `23: - Add real Playwright click-through for the Orbit GUI, not just static browser smoke markers.`
- `25: - Add a compact live “tool rationale” card to the GUI activity drawer.`
- `28: - Split the very large `core.py` command routing into route modules by area: GUI/voice, project, autonomy, validation, docker/sandbox.`
- `33: - Add browser-use-style visual assertions and screenshot diffs.`
- `39: See packaged validation artifacts for startup validation, Doctor, command verification, browser smoke, bug review, regression sweep, architecture audit and tool-awareness audit.`

### `docs\NOVA_PATCH_SUMMARY_v55_3_149.md`

Matched: PIL, browser, gui

- `10: - Added regression tests proving repo-inspired features are installed and wired across manifests, tools, commands, autonomous/idle planning, browser-smoke assets and GUI/voice observability markers.`
- `13: - compileall`
- `20: - `/browser-smoke``

### `docs\NOVA_PATCH_SUMMARY_v55_3_150.md`

Matched: PIL, browser

- `14: - Compileall, targeted pytest, startup validation, Doctor, command verify, repo assurance, browser smoke, bug review and regression sweep.`

### `docs\NOVA_REBRAND_IMPROVEMENT_REPORT_20260602.md`

Matched: PIL

- `31: python -m compileall -q app.py winlocalassistant`

### `docs\NOVA_RELEASE_GATE_LATEST.md`

Matched: PIL, browser, gui, playwright

- `11: - `compileall`: passed`
- `13: - `playwright_smoke`: passed`
- `20: - If Nova is running in the browser and Playwright is installed, /release-gate now runs the GUI smoke test automatically.`

### `docs\NOVA_RELEASE_READINESS_LATEST.md`

Matched: PIL, browser, gui

- `11: - **PASS** — GUI runtime status`
- `25: - **PASS** `compileall` [compile] (required, 0.266s)`
- `34:   - Reason: Strict generation contracts passed for one-file Python, browser game, PowerShell script, and Nova source-edit prompts.`
- `42:   - Reason: Autonomous status, stop, and guide routes responded without starting a long run.`
- `49: - **PASS** `real browser GUI runtime test` [gui] (required, 7.765s)`

### `docs\NOVA_RESPONSE_QUALITY_PLAN_LATEST.md`

Matched: gui

- `28: - OpenAI prompt engineering guidance: Put clear instructions before context, separate context with delimiters, prefer specific constraints, and say what to do instead of only what not to do. (https://help.openai.com/en/a`
- `29: - OpenAI reasoning best practices: Use straightforward prompts with clear end goals, delimiters, and explicit constraints; avoid forcing chain-of-thought style prompts. (https://platform.openai.com/docs/guides/reasoning-`
- `30: - OpenAI structured outputs guidance: Use structured outputs or function calling for machine-readable subtasks instead of parsing free-form prose. (https://platform.openai.com/docs/guides/structured-outputs)`

### `docs\NOVA_TASK_LOOP_ROADMAP.md`

Matched: PIL, gui

- `36: - Compile, targeted test, baseline test, generated-noise cleanup, and clean-git gates protect commits.`
- `59: 3. Python compile.`
- `83: - Prefer small existing modules over runtime/GUI changes.`

### `docs\NOVA_VERIFIED_SELF_CHANGE_FLOW.md`

Matched: upload

- `19: - No writes to `.git`, runtime data, logs, uploads, generated artefacts, virtual environments, build folders or dependency folders.`

### `docs\NOVA_WHOLE_CODEBASE_REVIEW_LATEST.md`

Matched: PIL, gui

- `34: - **Keep direct CLI command execution for one-shot QA** — implemented_in_v55.3.89: Allows `python app.py /nova-mega-test --confirm` and other copy/paste diagnostics without opening the GUI.`
- `39: - python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py`

### `docs\NOVA_WIDE_LEFT_RAIL.md`

Matched: browser, gui, screen

- `7: - `winlocalassistant/webui_layout_overhaul.py` — source of the width variables and browser geometry diagnostic.`
- `8: - `winlocalassistant/gui_layout_diagnostics.py` — static contract for `/gui-layout-status`.`
- `9: - `tests_nova_gui_startup_routes_v55_3_161.py` — regression tests for rail width, drawer position, and browser layout markers.`
- `18: - On small screens, the rail collapses back to icon-only mode.`

### `docs\PDF_REVIEW_IMPLEMENTATION.md`

Matched: Image, gui, image, playwright

- `12: - Image setup guidance is now a dedicated `/image-setup-wizard` path with make/edit test commands, SD WebUI/Diffusers setup, ComfyUI status caveat, and honest draft-vs-real-generation boundaries.`
- `13: - Image command routing now has regression coverage for real `/image-generate` and `/image-edit` success responses.`
- `18: - Optional Playwright release-gate behavior when dependencies and a running Nova server are available.`

### `docs\QUALITY_PROGRESS_LEDGER.md`

Matched: PIL

- `7: - Reviewed the v55.3.5 CodeRabbit-style quality gate installation and verified the suite compiled and passed before patching.`

### `docs\RELEASE_HYGIENE_LATEST.md`

Matched: PIL, browser, gui, playwright

- `12: - **note** `.nova_runtime/playwright` — runtime_state: Runtime state should normally be excluded from shared release zips.`
- `15: - **warning** `__pycache__/app.cpython-312.pyc` — compiled_python: Delete compiled Python bytecode before packaging.`
- `16: - **warning** `__pycache__/tests_emergency_stability.cpython-312-pytest-9.0.3.pyc` — compiled_python: Delete compiled Python bytecode before packaging.`
- `17: - **warning** `__pycache__/tests_model_calibration.cpython-312-pytest-9.0.3.pyc` — compiled_python: Delete compiled Python bytecode before packaging.`
- `18: - **warning** `__pycache__/tests_model_health_timeout.cpython-312-pytest-9.0.3.pyc` — compiled_python: Delete compiled Python bytecode before packaging.`
- `19: - **warning** `__pycache__/tests_runtime_usability_release_gate.cpython-312-pytest-9.0.3.pyc` — compiled_python: Delete compiled Python bytecode before packaging.`
- `21: - **note** `.nova_runtime/playwright/activity.jsonl` — runtime_state: Runtime state should normally be excluded from shared release zips.`
- `22: - **note** `.nova_runtime/playwright/analytics` — runtime_state: Runtime state should normally be excluded from shared release zips.`
- `23: - **note** `.nova_runtime/playwright/config.json` — runtime_state: Runtime state should normally be excluded from shared release zips.`
- `24: - **note** `.nova_runtime/playwright/conversations.json` — runtime_state: Runtime state should normally be excluded from shared release zips.`
- `25: - **note** `.nova_runtime/playwright/efficiency_metrics.jsonl` — runtime_state: Runtime state should normally be excluded from shared release zips.`
- `26: - **note** `.nova_runtime/playwright/KNOWLEDGE_BASE.md` — runtime_state: Runtime state should normally be excluded from shared release zips.`

### `docs\SUBQ_NVIDIA_PROVIDER_INTEGRATION_V55_3_163.md`

Matched: PIL, browser, gui, upload

- `3: This note converts the uploaded SubQ and local-runtime PDFs into Nova-local-assistant implementation work. References to "Nova" in the PDFs were treated as design targets for this local assistant only; any unrelated prod`
- `10: - **NVIDIA local lane:** vLLM and SGLang are modeled as advanced local OpenAI-compatible servers for stronger NVIDIA systems. TensorRT-LLM/Triton remain scale-up guidance, not default desktop dependencies.`
- `28: Remote providers are only active when `/allow-internet on` is set. Keys stay server-side and are not put into browser JavaScript or downloadable config.`
- `33: python -m compileall -q app.py winlocalassistant`

### `local_ai_cycles\context_20260610_005116.md`

Matched: Image, PIL, gui, image, screen, screenshot

- `62: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `63: tests_gui_ai_help_overlay.py`
- `64: tests_gui_cyberpunk_theme.py`
- `65: tests_gui_interaction_overhaul.py`
- `66: tests_gui_layout_v55_3_18.py`
- `69: tests_image_generation_backend.py`
- `84: tests_nova_clean_gui_docker_v55_3_159.py`
- `91: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `92: tests_nova_gui_startup_routes_v55_3_161.py`
- `97: tests_nova_media_and_gui_v55_3_156.py`
- `144: tests_tool_guides.py`
- `148: tests_v55_3_100_gui_revert_game_generation.py`

### `local_ai_cycles\context_20260610_005445.md`

Matched: Image, PIL, gui, image, screen, screenshot

- `48: >>> python -m compileall -q app.py winlocalassistant nova`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`
- `154: tests_nova_media_and_gui_v55_3_156.py`
- `201: tests_tool_guides.py`

### `local_ai_cycles\context_20260610_005729.md`

Matched: Image, PIL, gui, image, screen, screenshot

- `48: >>> python -m compileall -q app.py winlocalassistant nova`
- `99: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `100: tests_gui_ai_help_overlay.py`
- `101: tests_gui_cyberpunk_theme.py`
- `102: tests_gui_interaction_overhaul.py`
- `103: tests_gui_layout_v55_3_18.py`
- `106: tests_image_generation_backend.py`
- `121: tests_nova_clean_gui_docker_v55_3_159.py`
- `128: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `129: tests_nova_gui_startup_routes_v55_3_161.py`
- `134: tests_nova_media_and_gui_v55_3_156.py`
- `181: tests_tool_guides.py`

### `local_ai_cycles\context_20260610_005832.md`

Matched: Image, PIL, gui, image, screen, screenshot

- `49: >>> python -m compileall -q app.py winlocalassistant nova`
- `100: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `101: tests_gui_ai_help_overlay.py`
- `102: tests_gui_cyberpunk_theme.py`
- `103: tests_gui_interaction_overhaul.py`
- `104: tests_gui_layout_v55_3_18.py`
- `107: tests_image_generation_backend.py`
- `122: tests_nova_clean_gui_docker_v55_3_159.py`
- `129: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `130: tests_nova_gui_startup_routes_v55_3_161.py`
- `135: tests_nova_media_and_gui_v55_3_156.py`
- `182: tests_tool_guides.py`

### `local_ai_cycles\context_20260610_010230.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `50: >>> python -m compileall -q app.py winlocalassistant nova`
- `101: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `102: tests_gui_ai_help_overlay.py`
- `103: tests_gui_cyberpunk_theme.py`
- `104: tests_gui_interaction_overhaul.py`
- `105: tests_gui_layout_v55_3_18.py`
- `108: tests_image_generation_backend.py`
- `123: tests_nova_clean_gui_docker_v55_3_159.py`
- `130: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `131: tests_nova_gui_startup_routes_v55_3_161.py`
- `136: tests_nova_media_and_gui_v55_3_156.py`
- `183: tests_tool_guides.py`

### `local_ai_cycles\context_20260610_011126.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `51: >>> python -m compileall -q app.py winlocalassistant nova`
- `131:     resolve_image_context,`
- `133: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `134: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `137: from .tool_guides import get_autonomous_tool_use_summary`
- `150: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `152: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `153: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `154: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `167: from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation`
- `190:     build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,`
- `192:     patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,`

### `local_ai_cycles\context_20260610_012321.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `58: >>> python -m compileall -q app.py winlocalassistant nova`
- `138:     resolve_image_context,`
- `140: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `141: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `144: from .tool_guides import get_autonomous_tool_use_summary`
- `157: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `159: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `160: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `161: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `265: # Ollama will happily accept more than one HTTP request, but small local models`
- `266: # often degrade, stall or return partial JSON if we pile prompts onto them.`
- `370: tests_gui_activity_autonomous_sandbox_v55_3_19.py`

### `local_ai_cycles\context_20260610_013313.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `65: >>> python -m compileall -q app.py winlocalassistant nova`
- `145:     resolve_image_context,`
- `147: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `148: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `151: from .tool_guides import get_autonomous_tool_use_summary`
- `164: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `166: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `167: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `168: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `272: # Ollama will happily accept more than one HTTP request, but small local models`
- `273: # often degrade, stall or return partial JSON if we pile prompts onto them.`
- `377: tests_gui_activity_autonomous_sandbox_v55_3_19.py`

### `local_ai_cycles\context_20260610_014241.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `133: >>> python -m compileall -q app.py winlocalassistant nova`
- `213:     resolve_image_context,`
- `215: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `216: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `219: from .tool_guides import get_autonomous_tool_use_summary`
- `232: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `234: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `235: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `236: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `340: # Ollama will happily accept more than one HTTP request, but small local models`
- `341: # often degrade, stall or return partial JSON if we pile prompts onto them.`
- `445: tests_gui_activity_autonomous_sandbox_v55_3_19.py`

### `local_ai_cycles\context_20260610_014645.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `140: >>> python -m compileall -q app.py winlocalassistant nova`
- `220:     resolve_image_context,`
- `222: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `223: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `226: from .tool_guides import get_autonomous_tool_use_summary`
- `239: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `241: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `242: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `243: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `347: # Ollama will happily accept more than one HTTP request, but small local models`
- `348: # often degrade, stall or return partial JSON if we pile prompts onto them.`
- `452: tests_gui_activity_autonomous_sandbox_v55_3_19.py`

### `local_ai_cycles\context_20260610_015042.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `147: >>> python -m compileall -q app.py winlocalassistant nova`
- `303:     resolve_image_context,`
- `305: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `306: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `309: from .tool_guides import get_autonomous_tool_use_summary`
- `322: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `324: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `325: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `326: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `369: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `370: tests_gui_ai_help_overlay.py`
- `371: tests_gui_cyberpunk_theme.py`

### `local_ai_cycles\context_20260610_015455.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, upload, vision

- `154: >>> python -m compileall -q app.py winlocalassistant nova`
- `221:         add("Feature continuity", "/feature-continuity-audit", "Check key Nova GUI/tool surfaces were not accidentally removed.", category="wla")`
- `228:     if any(term in text for term in ["gui", "ui", "layout", "drawer", "blank panel", "broken screen", "screenshot"]):`
- `229:         add("Focus chat", "/validation-status", "Check whether the running backend is current before changing GUI code.", category="gui")`
- `230:         add("GUI visual test", "/gui-visual-test", "Use the existing GUI visual-regression gate before and after layout changes.", category="gui")`
- `231:         add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `233:     if any(term in text for term in ["video", "image", "media", "comfyui", "storyboard", "trailer", "render"]):`
- `234:         add("Media status", "/media-status", "Check image/video backend readiness before trying expensive generation.", category="media")`
- `235:         add("Image plan", "/image-plan cinematic robot dog mascot", "Create prompt variants and safety metadata before generation.", category="media")`
- `271: from .file_context import MAX_UPLOAD_BYTES, register_uploaded_file, list_file_contexts, clear_file_contexts`
- `279: from .webui_layout_overhaul import apply_gui_layout_overhaul`
- `376: tests_gui_activity_autonomous_sandbox_v55_3_19.py`

### `local_ai_cycles\context_20260610_015618.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, vision

- `161: >>> python -m compileall -q app.py winlocalassistant nova`
- `234:     resolve_image_context,`
- `236: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `237: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `240: from .tool_guides import get_autonomous_tool_use_summary`
- `253: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `255: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `256: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `257: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `361: # Ollama will happily accept more than one HTTP request, but small local models`
- `362: # often degrade, stall or return partial JSON if we pile prompts onto them.`
- `466: tests_gui_activity_autonomous_sandbox_v55_3_19.py`

### `local_ai_cycles\slim_context_20260610_020418.md`

Matched: PIL, browser, gui

- `156: >>> python -m compileall -q app.py winlocalassistant nova`
- `190: - Do not redesign GUI.`
- `200: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `231: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `264: 24: CommandHelpItem("Core", "/status", "Show workspace and runtime status.", "Confirms Nova is alive and pointed at the expected workspace.", "Run it before debugging model, GUI or command issues.", "/status"),`
- `282: 42: CommandHelpItem("Run", "/sandbox-dev-run", "Run a command in a copied writable dev workspace.", "Lets Nova test risky edits without touching the live project until promotion.", "Use `linux` or `kali`, then the comman`
- `283: 43: CommandHelpItem("GUI", "/gui-layout-status", "Check static GUI layout contract.", "Finds missing layout/theme/interaction markers.", "Run then click `layout` in GUI for browser geometry.", "/gui-layout-status"),`
- `284: 44: CommandHelpItem("GUI", "/gui-reset-help", "Explain safe UI reset.", "Recover stale drawer/cache state without deleting data.", "Run it or press reset UI/fix UI.", "/gui-reset-help"),`
- `285: 45: CommandHelpItem("GUI", "fix UI button", "Close cluttered drawers/popups and restore the composer.", "Emergency recovery when the GUI is blocking chat.", "Click the floating `fix UI` button.", "fix UI"),`
- `290: 50: CommandHelpItem("Model", "/model-help-plan", "Ask the selected local model for a contextual repair/build plan.", "Useful when deterministic checks need model reasoning before code changes.", "Give a goal and review t`
- `299: 59: CommandHelpItem("Regression Guard", "/legacy-continuity-audit", "Check historical Nova capability anchors.", "Prevents valuable old voice, GUI, provider, command and validation features from being accidentally droppe`
- `300: 60: CommandHelpItem("Regression Guard", "/release-readiness --full", "Run the packaging gate.", "Blocks shipping when chat/help/GUI/code/write/run or continuity checks regress.", "Run it before /release-package; it write`

### `local_ai_cycles\slim_context_20260610_020450.md`

Matched: PIL, browser, gui

- `156: >>> python -m compileall -q app.py winlocalassistant nova`
- `190: - Do not redesign GUI.`
- `200: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `231: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `264: 24: CommandHelpItem("Core", "/status", "Show workspace and runtime status.", "Confirms Nova is alive and pointed at the expected workspace.", "Run it before debugging model, GUI or command issues.", "/status"),`
- `282: 42: CommandHelpItem("Run", "/sandbox-dev-run", "Run a command in a copied writable dev workspace.", "Lets Nova test risky edits without touching the live project until promotion.", "Use `linux` or `kali`, then the comman`
- `283: 43: CommandHelpItem("GUI", "/gui-layout-status", "Check static GUI layout contract.", "Finds missing layout/theme/interaction markers.", "Run then click `layout` in GUI for browser geometry.", "/gui-layout-status"),`
- `284: 44: CommandHelpItem("GUI", "/gui-reset-help", "Explain safe UI reset.", "Recover stale drawer/cache state without deleting data.", "Run it or press reset UI/fix UI.", "/gui-reset-help"),`
- `285: 45: CommandHelpItem("GUI", "fix UI button", "Close cluttered drawers/popups and restore the composer.", "Emergency recovery when the GUI is blocking chat.", "Click the floating `fix UI` button.", "fix UI"),`
- `290: 50: CommandHelpItem("Model", "/model-help-plan", "Ask the selected local model for a contextual repair/build plan.", "Useful when deterministic checks need model reasoning before code changes.", "Give a goal and review t`
- `299: 59: CommandHelpItem("Regression Guard", "/legacy-continuity-audit", "Check historical Nova capability anchors.", "Prevents valuable old voice, GUI, provider, command and validation features from being accidentally droppe`
- `300: 60: CommandHelpItem("Regression Guard", "/release-readiness --full", "Run the packaging gate.", "Blocks shipping when chat/help/GUI/code/write/run or continuity checks regress.", "Run it before /release-package; it write`

### `local_ai_cycles\slim_context_20260610_020709.md`

Matched: PIL, browser, gui

- `156: >>> python -m compileall -q app.py winlocalassistant nova`
- `190: - Do not redesign GUI.`
- `200: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `231: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `local_ai_cycles\slim_context_20260610_020740.md`

Matched: PIL, browser, gui

- `156: >>> python -m compileall -q app.py winlocalassistant nova`
- `190: - Do not redesign GUI.`
- `200: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `231: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `local_ai_cycles\slim_context_20260610_020957.md`

Matched: browser, gui

- `188: - Do not redesign GUI.`
- `198: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `229: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `local_ai_cycles\slim_context_20260610_021155.md`

Matched: browser, gui

- `188: - Do not redesign GUI.`
- `198: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `229: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `local_ai_cycles\slim_context_20260610_021705.md`

Matched: browser, gui

- `188: - Do not redesign GUI.`
- `198: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `229: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `local_ai_cycles\slim_context_20260610_021916.md`

Matched: browser, gui

- `199: - Do not redesign GUI.`
- `209: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `240: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`

### `local_ai_cycles\slim_context_20260610_022317.md`

Matched: PIL, browser, gui

- `200: - Do not redesign GUI.`
- `210: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `241: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `307: 318: compile_result = run_section("compileall", [sys.executable, "-m", "compileall", "app.py", "nova", "winlocalassistant"], timeout=300)`

### `local_ai_cycles\slim_context_20260610_022331.md`

Matched: browser, gui

- `199: - Do not redesign GUI.`
- `209: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `240: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `259: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:67: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `277: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `282: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_022431.md`

Matched: browser, gui

- `198: - Do not redesign GUI.`
- `208: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `239: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `258: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `276: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `281: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_022728.md`

Matched: browser, gui

- `199: - Do not redesign GUI.`
- `209: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `240: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `259: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `277: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `282: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_023558.md`

Matched: browser, gui

- `204: - Do not redesign GUI.`
- `214: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `245: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `264: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `282: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `287: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_023915.md`

Matched: browser, gui

- `209: - Do not redesign GUI.`
- `219: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `250: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `269: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `287: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `292: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_023951.md`

Matched: browser, gui

- `210: - Do not redesign GUI.`
- `220: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `251: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `270: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `288: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `293: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_024046.md`

Matched: browser, gui

- `214: - Do not redesign GUI.`
- `224: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `255: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `274: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `292: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `297: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_024155.md`

Matched: browser, gui

- `215: - Do not redesign GUI.`
- `225: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `256: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `275: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:69: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `293: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `298: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_024300.md`

Matched: browser, gui

- `215: - Do not redesign GUI.`
- `225: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `256: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `275: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:71: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `293: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `298: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_024406.md`

Matched: browser, gui

- `215: - Do not redesign GUI.`
- `225: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `256: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `275: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:75: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `293: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `298: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_024515.md`

Matched: browser, gui

- `215: - Do not redesign GUI.`
- `225: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `256: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `275: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:80: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `293: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `298: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_024604.md`

Matched: browser, gui

- `216: - Do not redesign GUI.`
- `226: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `257: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `276: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:80: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `294: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `299: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025154.md`

Matched: browser, gui

- `216: - Do not redesign GUI.`
- `226: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `257: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `276: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `294: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `299: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025255.md`

Matched: browser, gui

- `217: - Do not redesign GUI.`
- `227: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `258: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `277: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `295: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `300: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025334.md`

Matched: browser, gui

- `218: - Do not redesign GUI.`
- `228: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `259: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `278: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `296: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `301: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025613.md`

Matched: browser, gui

- `219: - Do not redesign GUI.`
- `229: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `260: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `279: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `297: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `302: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025651.md`

Matched: browser, gui

- `220: - Do not redesign GUI.`
- `230: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `261: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `280: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `298: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `303: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025730.md`

Matched: browser, gui

- `221: - Do not redesign GUI.`
- `231: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `262: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `281: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `299: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `304: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025809.md`

Matched: browser, gui

- `222: - Do not redesign GUI.`
- `232: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `263: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `282: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `300: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `305: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\slim_context_20260610_025848.md`

Matched: browser, gui

- `223: - Do not redesign GUI.`
- `233: Guide the guarded loop toward the next best Nova improvement, not just random small edits.`
- `264: - For GUI/runtime work, require manual review unless existing safe browser/runtime tests exist.`
- `283: C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\tests_command_suggestions.py:83: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `301: 57: add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `306: 116: if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`

### `local_ai_cycles\task_context_20260610_030947.md`

Matched: PIL

- `24: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_031126.md`

Matched: PIL

- `24: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `39: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_031402.md`

Matched: PIL

- `24: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `39: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `49: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_031450.md`

Matched: PIL

- `22: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `37: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `47: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `77: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `87: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_031656.md`

Matched: PIL

- `20: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `30: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `60: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `70: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `87: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_032204.md`

Matched: PIL

- `41: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `51: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `68: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_032723.md`

Matched: PIL

- `22: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `32: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `49: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_032911.md`

Matched: PIL

- `30: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `56: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_033012.md`

Matched: PIL

- `23: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `49: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `68: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `87: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_033457.md`

Matched: PIL

- `30: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `49: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `68: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_033600.md`

Matched: PIL

- `25: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `44: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `70: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `80: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_033742.md`

Matched: PIL

- `25: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `51: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `61: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_033846.md`

Matched: PIL

- `28: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `38: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `71: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `81: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_034332.md`

Matched: PIL

- `19: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `52: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `62: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_034434.md`

Matched: PIL

- `44: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `54: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `86: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_034650.md`

Matched: PIL

- `25: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `57: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_034814.md`

Matched: PIL

- `33: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `51: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `70: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `80: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_035200.md`

Matched: PIL, terminal

- `8: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `32: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `51: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `61: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_035303.md`

Matched: PIL, terminal

- `8: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `28: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `38: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `71: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `81: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_035433.md`

Matched: PIL, terminal

- `8: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `28: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `38: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `61: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `94: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_035534.md`

Matched: PIL, terminal

- `8: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `21: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `31: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `54: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `87: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_035914.md`

Matched: PIL, terminal

- `9: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `46: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `63: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `92: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_040030.md`

Matched: PIL, terminal

- `10: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `26: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `43: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `72: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `84: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_040143.md`

Matched: PIL, terminal

- `10: 4572cce Improve task loop terminal handling and Aider skip prompts`
- `25: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_043009.md`

Matched: PIL

- `84: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_045854.md`

Matched: PIL

- `84: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_050142.md`

Matched: PIL

- `32: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `52: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `83: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_122915.md`

Matched: PIL

- `83: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `local_ai_cycles\task_context_20260610_134123.md`

Matched: PIL

- `41: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_134146.md`

Matched: PIL

- `49: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_134210.md`

Matched: PIL

- `22: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_135339.md`

Matched: PIL

- `48: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_135538.md`

Matched: PIL

- `25: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `56: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_135914.md`

Matched: PIL

- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_140116.md`

Matched: PIL

- `56: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_140443.md`

Matched: PIL

- `78: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_141527.md`

Matched: PIL

- `33: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_141815.md`

Matched: PIL

- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_141844.md`

Matched: PIL

- `54: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_142316.md`

Matched: PIL

- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`

### `local_ai_cycles\task_context_20260610_142415.md`

Matched: PIL

- `36: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `62: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `63: Gate: compile: PASS - python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `78: Validation gates passed: compile: PASS | targeted tests: PASS | baseline regression + Nova sanity: PASS | generated-noise cleanup: PASS | clean git: PASS`
- `79: Validation commands passed: python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py | python -m pytest -q tests_model_health_timeout.py | python -m pytest -q tests_nova_user_sanity.py tests_model_`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `

### `local_ai_cycles\task_context_20260610_143138.md`

Matched: PIL

- `33: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `34: Gate: compile: PASS - python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `49: Validation gates passed: compile: PASS | targeted tests: PASS | baseline regression + Nova sanity: PASS | generated-noise cleanup: PASS | clean git: PASS`
- `50: Validation commands passed: python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py | python -m pytest -q tests_validation_status_command.py tests_validation_reporting.py | python -m pytest -q tes`
- `79: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`

### `local_ai_cycles\task_context_20260610_144325.md`

Matched: PIL

- `78: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `160: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_144756.md`

Matched: PIL

- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `161: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_150350.md`

Matched: PIL, gui

- `2: Task: fresh-model-health-guidance`
- `3: Goal: Improve Nova model-health reporting, Ollama readiness guidance, or timeout/fallback diagnostics with a small source-backed source+test patch, only if a real behaviour gap exists. Do not edit winlocalassistant/core.`
- `48: - fresh-model-health-guidance: score=70, state=eligible, reasons=source+test candidate`
- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `87: - fresh-model-health-guidance: score=70, state=eligible, reasons=source+test candidate`
- `97: Selected task fresh-model-health-guidance: score=70; reasons=source+test candidate`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_190341.md`

Matched: PIL, gui

- `30: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `41: - fresh-model-health-guidance: score=70, state=eligible, reasons=source+test candidate`
- `51: Selected task fresh-model-health-guidance: score=70; reasons=source+test candidate`
- `54: Task: fresh-model-health-guidance`
- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_190449.md`

Matched: PIL, gui

- `31: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `44: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `164: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_190600.md`

Matched: PIL, gui

- `31: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `44: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `165: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_190639.md`

Matched: PIL, gui

- `30: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `43: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `76: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `88: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `166: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_191146.md`

Matched: PIL, gui

- `48: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `88: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `167: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `170: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260610_191222.md`

Matched: PIL, gui

- `28: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `41: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `87: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `168: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_191330.md`

Matched: PIL, gui

- `2: Task: fresh-model-health-guidance`
- `3: Goal: Improve Nova model-health reporting, Ollama readiness guidance, or timeout/fallback diagnostics with a small source-backed source+test patch, only if a real behaviour gap exists. Do not edit winlocalassistant/core.`
- `29: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `41: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `86: - fresh-model-health-guidance: score=35, state=eligible, reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `97: Selected task fresh-model-health-guidance: score=35; reasons=source+test candidate; 1 recent low-value/no-change outcome(s); 1 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `

### `local_ai_cycles\task_context_20260610_192217.md`

Matched: PIL, gui

- `49: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `170: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_192321.md`

Matched: PIL, gui

- `29: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `43: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `75: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260610_200730.md`

Matched: PIL, gui

- `47: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `73: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `172: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_201326.md`

Matched: PIL, gui

- `46: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `73: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `173: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_201519.md`

Matched: PIL, gui

- `24: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `40: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `72: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260610_201821.md`

Matched: PIL, gui

- `45: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `71: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `174: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_202122.md`

Matched: PIL, gui

- `21: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `39: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `71: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260610_202442.md`

Matched: PIL, gui

- `43: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `69: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `176: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_202816.md`

Matched: PIL, gui

- `37: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `69: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `177: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260610_203526.md`

Matched: PIL, gui

- `42: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `68: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `155: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260610_204915.md`

Matched: PIL, gui

- `41: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `67: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `155: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260610_233941.md`

Matched: PIL, gui

- `40: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `66: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `155: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260610_234414.md`

Matched: PIL, gui

- `39: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `66: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `155: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260610_235101.md`

Matched: PIL, gui

- `40: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `66: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `155: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260610_235337.md`

Matched: PIL, gui

- `33: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `66: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `105: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `106: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `136: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `137: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `140: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `155: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260610_235755.md`

Matched: PIL, gui

- `33: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `65: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `104: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `105: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `133: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `134: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `135: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `136: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `139: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `146: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `154: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260611_000331.md`

Matched: PIL, gui

- `38: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `64: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `104: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `105: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `133: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `134: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `135: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `136: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `139: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `146: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `154: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260611_001558.md`

Matched: PIL, gui

- `37: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `64: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `103: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `104: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `132: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `133: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `134: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `135: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `138: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `145: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `153: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`

### `local_ai_cycles\task_context_20260611_004619.md`

Matched: PIL, gui

- `22: Validation gates passed: compile: PASS | targeted tests: PASS | baseline regression + Nova sanity: PASS | generated-noise cleanup: PASS | clean git: PASS`
- `23: Validation commands passed: python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py | python -m pytest -q tests_model_context_pack.py | python -m pytest -q tests_nova_user_sanity.py tests_model_he`
- `64: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `102: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `103: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `131: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `132: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `133: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `134: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `137: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `144: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260611_005044.md`

Matched: PIL, gui

- `3: Goal: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py so blocked work ranks above review work, rev`
- `35: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `63: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `102: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `103: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `131: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `132: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `133: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `134: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `137: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `144: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260611_005351.md`

Matched: PIL, gui

- `3: Goal: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py. The helper should return a higher score for`
- `34: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `62: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `101: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `102: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `130: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `131: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `132: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `133: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `136: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `143: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260611_005949.md`

Matched: PIL, gui

- `3: Goal: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py. The helper should return a higher score for`
- `34: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `62: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `100: {"created_at":"2026-06-10T12:31:33","task":"project-state-continuity","result":"committed","category":"success-cooldown","reason":"source/test task passed targeted tests, baseline tests, Nova user sanity tests, generated`
- `101: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `129: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `130: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `131: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `132: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `135: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `142: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`

### `local_ai_cycles\task_context_20260611_011539.md`

Matched: PIL, gui

- `3: Goal: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py so blocked work ranks above review work, rev`
- `22: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `23: Gate: compile: PASS - python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `42: Validation gates passed: compile: PASS | targeted tests: PASS | baseline regression + Nova sanity: PASS | generated-noise cleanup: PASS | clean git: PASS`
- `43: Validation commands passed: python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py | python -m pytest -q tests_autodev_sandbox.py | python -m pytest -q tests_nova_user_sanity.py tests_model_healt`
- `62: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `100: {"created_at":"2026-06-10T12:34:30","task":"project-state-continuity","result":"rejected","category":"reverted-success","reason":"success commit was later reverted: 7cd582a","model":"ollama_chat/gemma3:12b","mode":"fast"`
- `128: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `129: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `130: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `131: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`

### `local_ai_cycles\task_context_20260611_011858.md`

Matched: PIL, gui

- `3: Goal: Improve the tiny autonomous development sandbox with one small source+test change. Add sort_work_items_by_priority(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It must re`
- `32: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `60: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `127: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `128: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `129: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `130: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `133: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `140: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `148: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `149: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_012719.md`

Matched: PIL, gui

- `3: Goal: Improve the tiny autonomous development sandbox with one small source+test change. Add sort_work_items_by_priority(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It must re`
- `26: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `60: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `126: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `127: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `128: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `129: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `132: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `139: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `148: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_013007.md`

Matched: PIL, gui

- `3: Goal: Promote idea-1 from the Nova task idea pool into one tiny source+test improvement. Add select_next_work_item(items: Iterable[WorkItem]) -> WorkItem | None to nova_improvement_lab\autodev_sandbox.py. It must ignore `
- `30: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `59: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `126: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `127: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `128: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `129: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `132: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `139: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `147: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `148: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_013511.md`

Matched: PIL, gui

- `3: Goal: Promote idea-2 from the Nova task idea pool into one tiny source+test improvement. Add actionable_work_items(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It must return o`
- `29: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `58: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `125: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `126: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `127: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `128: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `131: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `138: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `146: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `147: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_014238.md`

Matched: PIL, gui

- `3: Goal: Promote the selected Nova idea-promotion candidate into one tiny source+test improvement. Add explain_next_action(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use select_nex`
- `26: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `57: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `124: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `125: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `126: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `127: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `130: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `137: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `145: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `146: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_014835.md`

Matched: PIL, gui

- `3: Goal: Promote the selected Nova idea-promotion candidate into one tiny source+test improvement. Add explain_next_action(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use select_nex`
- `56: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `123: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `124: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `125: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `126: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `129: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `136: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `144: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `145: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `147: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_015506.md`

Matched: PIL, gui

- `3: Goal: Promote the drafted Nova idea-promotion task into one tiny source+test improvement. Add group_work_items_by_status(items: Iterable[WorkItem]) -> dict[str, list[WorkItem]] to nova_improvement_lab\autodev_sandbox.py.`
- `18: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `53: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `123: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `124: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `125: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `126: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `129: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `136: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `144: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `145: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_020420.md`

Matched: PIL, gui

- `3: Goal: Promote the next safe Nova idea into one tiny source+test improvement. Add summarise_action_plan(items: Iterable[WorkItem]) -> dict[str, object] to nova_improvement_lab\autodev_sandbox.py. It must return a small su`
- `53: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `122: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `123: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `124: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `125: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `128: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `135: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `143: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `144: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `146: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_020941.md`

Matched: PIL, gui

- `3: Goal: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add format_action_plan_summary(summary: Mapping[str, object]) -> str to nova_improvement_lab\autodev_sandbox.py. It must format t`
- `53: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `121: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `122: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `123: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `124: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `127: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `134: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `142: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `143: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `145: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_021955.md`

Matched: PIL, gui

- `3: Goal: Promote the next external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_markdown(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use summ`
- `53: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `120: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `121: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `122: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `123: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `126: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `133: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `141: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `142: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `144: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_023229.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_status_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It `
- `53: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `119: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `120: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `121: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `122: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `125: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `132: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `140: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `141: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `143: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_024641.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add build_action_plan_debug_dict(items: Iterable[WorkItem]) -> dict[str, object] to nova_improvement_lab\autodev_san`
- `53: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `118: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `119: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `120: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `121: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `124: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `131: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `139: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `140: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `142: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_024933.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add build_action_plan_debug_dict(items: Iterable[WorkItem]) -> dict[str, object] to nova_improvement_lab\autodev_san`
- `8: 0883aa9 Include improvement lab in task loop compile gate`
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `117: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `118: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `119: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `120: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `123: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `130: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `138: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `139: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_025942.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_debug_lines(items: Iterable[WorkItem]) -> list[str] to nova_improvement_lab\autodev_sandbox.p`
- `11: 0883aa9 Include improvement lab in task loop compile gate`
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `116: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `117: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `118: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `119: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `122: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `129: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `137: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `138: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`

### `local_ai_cycles\task_context_20260611_190433.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one narrow source+test robustness fix. Improve winlocalassistant/model_context.py so prompt-named file context cache signatures cannot crash if a name`
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `115: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `116: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `117: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `118: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `121: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `128: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `136: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `137: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `139: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_191444.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_debug_markdown(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. `
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `114: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `115: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `116: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `117: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `120: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `127: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `135: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `136: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `138: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_193534.md`

Matched: PIL, gui

- `3: Goal: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_debug_json(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It m`
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `113: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `114: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `115: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `116: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `119: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `126: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `134: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `135: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `137: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_202849.md`

Matched: PIL, gui

- `3: Goal: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_next_work_item_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use the exis`
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `112: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `113: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `114: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `115: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `118: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `125: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `133: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `134: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `136: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_203352.md`

Matched: PIL, gui

- `3: Goal: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_titles(items: Iterable[WorkItem]) -> list[str] to nova_improvement_lab\autodev_sandbox.py. It must return `
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `111: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `112: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `113: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `114: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `117: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `124: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `132: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `133: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `135: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_context_20260611_203817.md`

Matched: PIL, gui

- `3: Goal: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_status_counts_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must summarise nor`
- `53: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `89: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`
- `110: {"schema_version":2,"created_at":"2026-06-10T14:24:14","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `111: {"schema_version":2,"created_at":"2026-06-10T14:25:50","task":"fresh-validation-status-diagnostics","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, ba`
- `112: {"schema_version":2,"created_at":"2026-06-10T14:32:58","task":"fresh-model-timeout-fallback","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, baseline `
- `113: {"schema_version":2,"created_at":"2026-06-10T14:38:02","task":"fresh-model-timeout-fallback","result":"rejected","category":"reverted-success","stage":"post-commit-audit","reason":"success commit was later reverted: 5121`
- `116: {"schema_version":2,"created_at":"2026-06-10T15:04:14","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `123: {"schema_version":2,"created_at":"2026-06-10T19:13:59","task":"fresh-model-health-guidance","result":"no-change","category":"no-change","stage":"aider-run","reason":"model found no source-backed improvement or produced i`
- `131: {"schema_version":2,"created_at":"2026-06-10T20:28:51","task":"lab-risk-contract-source-test-v3","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted tests, basel`
- `132: {"schema_version":2,"created_at":"2026-06-10T20:36:34","task":"real-model-context-named-file-preview-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targeted test`
- `134: {"schema_version":2,"created_at":"2026-06-10T23:45:37","task":"real-model-context-named-file-cache-freshness-v1","result":"committed","category":"success-cooldown","stage":"commit","reason":"source/test task passed targe`

### `local_ai_cycles\task_prompt_20260610_150350.md`

Matched: gui

- `9: fresh-model-health-guidance`
- `12: Improve Nova model-health reporting, Ollama readiness guidance, or timeout/fallback diagnostics with a small source-backed source+test patch, only if a real behaviour gap exists. Do not edit winlocalassistant/core.py.`

### `local_ai_cycles\task_prompt_20260610_191330.md`

Matched: gui

- `9: fresh-model-health-guidance`
- `12: Improve Nova model-health reporting, Ollama readiness guidance, or timeout/fallback diagnostics with a small source-backed source+test patch, only if a real behaviour gap exists. Do not edit winlocalassistant/core.py.`

### `local_ai_cycles\task_prompt_20260611_005044.md`

Matched: gui

- `11: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py so blocked work ranks above review work, review ra`

### `local_ai_cycles\task_prompt_20260611_005351.md`

Matched: gui

- `11: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py. The helper should return a higher score for block`

### `local_ai_cycles\task_prompt_20260611_005949.md`

Matched: gui

- `11: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py. The helper should return a higher score for block`

### `local_ai_cycles\task_prompt_20260611_011539.md`

Matched: gui

- `11: Improve the tiny autonomous development sandbox with one small source+test change. Add a priority_score(item: WorkItem) helper to nova_improvement_lab\autodev_sandbox.py so blocked work ranks above review work, review ra`

### `local_ai_cycles\task_prompt_20260611_011858.md`

Matched: gui

- `11: Improve the tiny autonomous development sandbox with one small source+test change. Add sort_work_items_by_priority(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It must return i`

### `local_ai_cycles\task_prompt_20260611_012719.md`

Matched: gui

- `11: Improve the tiny autonomous development sandbox with one small source+test change. Add sort_work_items_by_priority(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It must return i`

### `local_ai_cycles\task_prompt_20260611_013007.md`

Matched: gui

- `11: Promote idea-1 from the Nova task idea pool into one tiny source+test improvement. Add select_next_work_item(items: Iterable[WorkItem]) -> WorkItem | None to nova_improvement_lab\autodev_sandbox.py. It must ignore comple`

### `local_ai_cycles\task_prompt_20260611_013511.md`

Matched: gui

- `11: Promote idea-2 from the Nova task idea pool into one tiny source+test improvement. Add actionable_work_items(items: Iterable[WorkItem]) -> list[WorkItem] to nova_improvement_lab\autodev_sandbox.py. It must return only un`

### `local_ai_cycles\task_prompt_20260611_014238.md`

Matched: gui

- `11: Promote the selected Nova idea-promotion candidate into one tiny source+test improvement. Add explain_next_action(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use select_next_work`

### `local_ai_cycles\task_prompt_20260611_014835.md`

Matched: gui

- `11: Promote the selected Nova idea-promotion candidate into one tiny source+test improvement. Add explain_next_action(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use select_next_work`

### `local_ai_cycles\task_prompt_20260611_015506.md`

Matched: gui

- `11: Promote the drafted Nova idea-promotion task into one tiny source+test improvement. Add group_work_items_by_status(items: Iterable[WorkItem]) -> dict[str, list[WorkItem]] to nova_improvement_lab\autodev_sandbox.py. It mu`

### `local_ai_cycles\task_prompt_20260611_020420.md`

Matched: gui

- `11: Promote the next safe Nova idea into one tiny source+test improvement. Add summarise_action_plan(items: Iterable[WorkItem]) -> dict[str, object] to nova_improvement_lab\autodev_sandbox.py. It must return a small summary `

### `local_ai_cycles\task_prompt_20260611_020941.md`

Matched: gui

- `11: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add format_action_plan_summary(summary: Mapping[str, object]) -> str to nova_improvement_lab\autodev_sandbox.py. It must format the out`

### `local_ai_cycles\task_prompt_20260611_021955.md`

Matched: gui

- `11: Promote the next external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_markdown(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use summarise_`

### `local_ai_cycles\task_prompt_20260611_023229.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_status_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must u`

### `local_ai_cycles\task_prompt_20260611_024641.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add build_action_plan_debug_dict(items: Iterable[WorkItem]) -> dict[str, object] to nova_improvement_lab\autodev_sandbox.p`

### `local_ai_cycles\task_prompt_20260611_024933.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add build_action_plan_debug_dict(items: Iterable[WorkItem]) -> dict[str, object] to nova_improvement_lab\autodev_sandbox.p`

### `local_ai_cycles\task_prompt_20260611_025942.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_debug_lines(items: Iterable[WorkItem]) -> list[str] to nova_improvement_lab\autodev_sandbox.py. It `

### `local_ai_cycles\task_prompt_20260611_190433.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one narrow source+test robustness fix. Improve winlocalassistant/model_context.py so prompt-named file context cache signatures cannot crash if a named file`

### `local_ai_cycles\task_prompt_20260611_191444.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_debug_markdown(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It mus`

### `local_ai_cycles\task_prompt_20260611_193534.md`

Matched: gui

- `11: Promote the next validated external JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_debug_json(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must us`

### `local_ai_cycles\task_prompt_20260611_202849.md`

Matched: gui

- `11: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_next_work_item_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must use the existing n`

### `local_ai_cycles\task_prompt_20260611_203352.md`

Matched: gui

- `11: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_action_plan_titles(items: Iterable[WorkItem]) -> list[str] to nova_improvement_lab\autodev_sandbox.py. It must return the wo`

### `local_ai_cycles\task_prompt_20260611_203817.md`

Matched: gui

- `11: Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_status_counts_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must summarise normalise`

### `playwright\nova_gui_smoke.spec.js`

Matched: gui, playwright

- `1: // Playwright smoke tests for Nova GUI.`
- `3: //   npx playwright test playwright/nova_gui_smoke.spec.js`
- `4: const { test, expect } = require('@playwright/test');`
- `9:   await page.fill('#input', 'hello playwright smoke test');`
- `11:   await expect(page.locator('#chat')).toContainText('hello playwright smoke test');`

### `playwright\nova_runtime_usability.spec.js`

Matched: playwright, screen, screenshot

- `1: const { test, expect } = require('@playwright/test');`
- `70:   await page.screenshot({ path: 'logs/runtime_usability_playwright.png', fullPage: true });`

### `playwright\nova_runtime_usability_runner.js`

Matched: browser, console, playwright, screen, screenshot

- `1: const { chromium } = require('playwright');`
- `5: const executablePath = process.env.PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH || '/usr/lib/chromium/chromium';`
- `21:   let browser;`
- `35:     browser = await chromium.launch({`
- `40:     const page = await browser.newPage({ viewport: { width: 1366, height: 900 } });`
- `42:     evidence.steps.push('browser rendered Nova HTML');`
- `82:     await page.screenshot({ path: 'logs/runtime_usability_playwright.png', fullPage: true });`
- `85:     console.log(JSON.stringify(evidence, null, 2));`
- `87:     if (browser) await browser.close().catch(() => {});`
- `90:   console.error(err && err.stack ? err.stack : String(err));`

### `scripts\run_gui_runtime_test.py`

Matched: browser, gui, playwright, screen, screenshot

- `48: def run_python_playwright(base: str, html: str, result: dict) -> int:`
- `50:         from playwright.sync_api import sync_playwright`
- `52:         result.update({"error": "python playwright is not installed", "exception": repr(exc), "fix": "Run .\\.venv\\Scripts\\python.exe -m pip install -r requirements-dev.txt, then rerun release-readiness with .\\.venv\\`
- `55:     screenshot_path = EVIDENCE / "nova_runtime_usability_playwright.png"`
- `56:     result["screenshot_path"] = str(screenshot_path)`
- `57:     with sync_playwright() as p:`
- `58:         executable = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH") or shutil_which_chromium()`
- `65:         browser = p.chromium.launch(**launch_kwargs)`
- `67:             page = browser.new_page(viewport={"width": 1366, "height": 900})`
- `69:             result["steps"].append("browser rendered Nova HTML")`
- `128:             page.screenshot(path=str(screenshot_path), full_page=True)`
- `132:             browser.close()`

### `tools\update_task_loop_roadmap.py`

Matched: PIL, gui

- `52: - Prefer small existing modules over runtime/GUI changes.`
- `119: - Compile, targeted test, baseline test, generated-noise cleanup, and clean-git gates protect commits.`
- `142: 3. Python compile.`

### `tools\validate_idea_promotion_candidates.py`

Matched: PIL

- `13: ID_RE = re.compile(r"^[A-Za-z0-9._-]+$")`

### `tools\validate_task_loop_patch.ps1`

Matched: PIL

- `25: Invoke-Checked "python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py tests_task_loop_static_contract.py tests_improvement_lab_contract.py"`
- `55: Write-Host ">>> python -m py_compile tools/update_task_loop_roadmap.py"`
- `56: python -m py_compile tools/update_task_loop_roadmap.py`
- `58:     throw "Roadmap updater compile failed"`

### `winlocalassistant\action_watcher.py`

Matched: gui

- `37:     sandbox; it is a policy gate that can be reused by autonomous planning, GUI`

### `winlocalassistant\adaptive_backlog.py`

Matched: PIL, browser, gui, screen

- `72:         return ["python -m py_compile", "entrypoint/import smoke", "README usage evidence"]`
- `97:         validation=["browser JS syntax", "feature continuity audit", "manual check: panel displays goal/failure/next action"],`
- `112:         why="Users need one quick command proving the code is not just compiling but still has key behaviours and no obvious GUI/tool regressions.",`
- `116:         implementation_hint="Combine compile, browser-JS extraction signal, feature-continuity markers and behaviour evidence into one tool result.",`
- `117:         validation=["validation matrix unit test", "feature-continuity audit", "compileall"],`
- `122:         why="Idle should distinguish watch/propose/prepare/apply so it remains useful without silently mutating the codebase.",`
- `137:         validation=["receipt history smoke", "feature-continuity audit", "compileall"],`
- `156:         implementation_hint="Use /jarvis-bridge, /jarvis-status, /sidecar-policy and /proactive-actions. Keep sidecar/screen/shell/browser permissions off by default and route action proposals through receipts.",`
- `172:         title="Add Jarvis test prompts, bridge receipts, sidecar enrollment and safe browser harness",`
- `173:         why="Jarvis integration is more useful when Nova can prove reachability, show receipts, plan browser tests and keep sidecar enrollment explicit.",`
- `177:         implementation_hint="Use /jarvis-test-prompts, /bridge-receipts, /sidecar-enrollment and /browser-harness.",`
- `199:         implementation_hint="Use /persona, /persona-set, /persona-prompt and /custom-chat-window. The GUI settings panel exposes sliders that fill/apply persona commands.",`

### `winlocalassistant\architecture_audit.py`

Matched: browser, gui

- `37:     "docs/NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md",`
- `117:             "Update version metadata, visible GUI text, README and CHANGELOG together in every release.",`
- `139:             "Keep architecture, tool catalogue and autonomous operating guides versioned with the build.",`
- `228:         "Add optional browser automation later for true interactive project acceptance tests.",`

### `winlocalassistant\assistant_datastore.py`

Matched: PIL

- `18: _NAME_RE = re.compile(r"^[A-Za-z0-9_.-]{1,64}$")`

### `winlocalassistant\autonomous_explain.py`

Matched: PIL

- `135:     return ["py_compile if Nova code changed", "python tests_smoke.py", "relevant pytest suites"]`

### `winlocalassistant\autonomous_failure.py`

Matched: PIL

- `88:     if any(term in text for term in ["verification failed", "tests failed", "py_compile failed"]):`

### `winlocalassistant\autonomous_journal.py`

Matched: PIL

- `67: SENSITIVE_KEY_RE = re.compile(r"(api[_-]?key|token|secret|password|authorization|bearer|credential)", re.I)`
- `69:     re.compile(r"Bearer\s+[A-Za-z0-9._~+/=-]+", re.I),`
- `70:     re.compile(r"(api[_-]?key|token|secret|password)=([^\s&]+)", re.I),`

### `winlocalassistant\autonomous_loop_guard.py`

Matched: gui

- `36:     "tool_use_guide",`

### `winlocalassistant\autonomous_sequence.py`

Matched: Image, PIL, browser, gui, image, vision

- `77:     # verifies the Kali tools image, and reports results through sandbox logs.`
- `86:             AutonomousToolStep("Kali tools smoke test", "sandbox_exec", {"profile": "kali", "command": "nmap --version || true; nikto -Version || true; whois --version || true", "timeout": 30}, "check whether the custom `
- `88:         verify.append(AutonomousToolStep("Final sandbox status", "sandbox_status", {}, "summarise detected runtime, images and running containers", required=False))`
- `139:     steps.append(AutonomousToolStep("Check local model readiness", "model_readiness", {"goal": text}, "know whether required/optional Ollama models are installed before model-heavy planning, coding or vision tasks", requ`
- `145:             AutonomousToolStep("Compile prompt contract", "prompt_contract", {"goal": text}, "turn the exact prompt into must-have and must-not-have validation checks before generation", required=False),`
- `146:             AutonomousToolStep("Plan iterative edit/test/repair loop", "iterative_coding_loop", {"goal": text, "path": "."}, "prepare a mutable loop that uses prompt contract, build quality, browser/runtime checks and su`
- `188:             AutonomousToolStep("Compile prompt contract", "prompt_contract", {"goal": text}, "derive the exact success criteria before improving", required=False),`
- `303:     extra = " The request contains ambiguity, so Nova should pause or keep the sequence proposal-first where needed." if needs_clarification else ""`

### `winlocalassistant\autonomy_capabilities.py`

Matched: PIL, browser, gui, playwright, vision

- `143:             produces=("classified failure", "minimal repair steps", "rollback guidance"),`
- `191:             use_when=("a feature depends on Python, pytest, Ollama, git, node, Docker, Playwright or AI-heavy tooling",),`
- `222:             tools=("iterative_coding_loop", "surgical_fallback_v2", "edit_repair_plan", "prompt_contract", "build_quality_report", "browser_runtime_test", "model_output_coach"),`
- `225:             validates_with=("prompt contract", "build quality", "browser runtime/static wiring", "final project check"),`
- `236:             validates_with=("compileall", "pytest", "sandbox command return code"),`
- `315:             name="build_quality_browser_runtime",`
- `316:             commands=("/build-quality-report GOAL", "/browser-run-test GOAL", "/browser-storage-test GOAL", "/browser-export-test GOAL"),`
- `317:             tools=("build_quality_report", "browser_runtime_test"),`
- `319:             validates_with=("build quality score", "browser runtime wiring checks", "prompt-specific storage/export checks"),`
- `321:             produces=("build quality report", "browser runtime test report"),`
- `322:             keywords=("quality", "browser", "runtime", "click", "storage", "export", "good app", "actually works"),`
- `350:             use_when=("a task needs a missing local model", "the local model is degraded because the selected model is absent", "the user asks Nova to request or download required models", "a stronger coder/vision/embedd`

### `winlocalassistant\autonomy_idle_intelligence.py`

Matched: browser, gui

- `92:         "user_facing_issue": any(k in text for k in ["gui", "voice", "planning", "browser", "support"]),`
- `144:         add("/browser-run-test", "Generated web apps need runtime behaviour evidence, not only syntax.", "after files are written")`

### `winlocalassistant\branding.py`

Matched: PIL

- `80: LEGACY_BRAND_RE = re.compile(r"WinLocalAssistant|Win Local Assistant|Windows Local Assistant|\bWLA\b")`
- `81: LEGACY_VISIBLE_LOWER_RE = re.compile(r"(?<![A-Za-z0-9])(?:wla[-_][a-z0-9_.-]+|/[a-z-]*wla[a-z-]*|test-wla-all|\bwla\b)(?![A-Za-z0-9])")`

### `winlocalassistant\browser_worker.py`

Matched: browser, screen, screenshot

- `3: """Safe browser-worker planning primitives.`
- `6: browser unless a future worker explicitly implements the generated plan.`
- `12: BrowserAction = Literal["navigate", "read", "screenshot", "click", "type", "submit", "download"]`
- `19: class BrowserStep:`
- `20:     action: BrowserAction`
- `28: def classify_browser_request(goal: str) -> dict[str, Any]:`
- `36:         "reason": "contains form/account/download/purchase-like wording" if wants_write else "read-only research/screenshot plan",`
- `40: def build_browser_task_plan(goal: str, *, start_url: str = "", allow_write: bool = False) -> dict[str, Any]:`
- `41:     classification = classify_browser_request(goal)`
- `42:     steps: list[BrowserStep] = []`
- `44:         steps.append(BrowserStep("navigate", start_url, evidence=["url"], reason="open the requested page"))`
- `46:         steps.append(BrowserStep("read", "current page", evidence=["dom_snapshot"], reason="inspect current page before acting"))`

### `winlocalassistant\bug_review.py`

Matched: PIL

- `53:     release_line = re.compile(r"^\s*(?:#+\s*)?(?:Nova\s+)?v?55\.3\.\d+\b", re.IGNORECASE)`
- `166:     version_pat = re.compile(r"55\.3\.(\d+)")`
- `258:     runtime_cache_kinds = {"cache_directory", "compiled_python"}`
- `329:     lines += ["", "## Recommended validation", "- `python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py`", "- `python tests_smoke.py`", "- `/nova-mega-test --confirm`", "- `/bug-revie`

### `winlocalassistant\build_info.py`

Matched: PIL, browser, gui

- `6: launchers/tests do not break.  This module gives humans, browsers and AI agents`
- `17: from .gui_layout_diagnostics import LAYOUT_VERSION, build_gui_layout_diagnostics`
- `26:     "winlocalassistant/gui_layout_diagnostics.py",`
- `38:     "winlocalassistant/gui_context_help.py",`
- `60:     layout = build_gui_layout_diagnostics(root)`
- `74:         "gui_layout_ok": bool(layout.get("ok")),`
- `75:         "gui_layout_failed_count": layout.get("failed_count", 0),`
- `77:             "python -m compileall -q app.py nova winlocalassistant",`
- `79:             "python -m pytest -q tests_nova_gui_startup_routes_v55_3_161.py",`
- `99:         "## GUI sanity",`
- `100:         f"- Layout static contract OK: `{payload.get('gui_layout_ok')}`",`
- `101:         f"- Layout failed count: `{payload.get('gui_layout_failed_count')}`",`

### `winlocalassistant\codebase_advisor.py`

Matched: browser, gui

- `61:     """Return served GUI HTML for the active checkout when it is cheap to import."""`
- `116:             recommendation="Next: move browser JS helpers into a versioned web asset module or template fragments, then test with node --check and existing GUI regression tests.",`
- `133:             title="Current version is visible in the package and GUI",`
- `136:             evidence=f"v{version} appears in the served GUI HTML and __init__.py.",`
- `145:             evidence=f"Package version is {version}, but the GUI banner may not expose that exact version.",`

### `winlocalassistant\codebase_integrity_audit.py`

Matched: PIL, gui

- `97:             compile(tree, str(path), "exec")`
- `99:             issues.append(_issue("critical", "syntax", rel, exc.lineno or 1, "Python syntax/compile error", exc.msg, "open", "Fix syntax before any behavioural work."))`
- `102:             issues.append(_issue("critical", "compile", rel, 1, "Python compile error", repr(exc), "open", "Fix compile failure before release."))`
- `157:         passed.append(f"Parsed and compiled {len(py_files)} Python file(s) without syntax errors.")`
- `245:         "python -m compileall -q winlocalassistant tests_*.py app.py",`
- `271:     The whole-codebase audit intentionally imports and scans many modules. GUI and`

### `winlocalassistant\codebase_sanity_audit.py`

Matched: browser, gui, terminal

- `115:             recommendation="Ensure sleeps are bounded and do not run on GUI/request paths; prefer polling with visible activity events.",`
- `221:         "/session-evidence", "/memory-inventory", "/browser-smoke", "/command-verify",`
- `232:     gui_required = ["data-orbit-studio-shell", "messageTerminalHtml", "announceNovaReady", "loadActivity"]`
- `233:     missing_gui = [m for m in gui_required if m not in webui_text]`
- `234:     if missing_gui:`
- `237:             "gui_observability_marker_gap",`
- `239:             "missing markers: " + ", ".join(missing_gui),`
- `240:             "Restore Orbit GUI observability markers or update tests if the GUI intentionally changed.",`
- `278:             "Prioritise live browser click-through tests for GUI claims.",`

### `winlocalassistant\code_quality_gate.py`

Matched: PIL

- `196:         "python -m compileall -q winlocalassistant tests_*.py",`

### `winlocalassistant\code_repair_audit.py`

Matched: PIL

- `82:             findings.append(CodeRepairFinding("critical", "syntax", rel, exc.lineno or 1, "Python syntax error", exc.msg, "Fix syntax first, then run python -m compileall -q winlocalassistant tests_*.py."))`
- `144:         "4. Run `python -m compileall -q winlocalassistant tests_*.py` and `python -m pytest -q`.",`

### `winlocalassistant\code_review_audit.py`

Matched: Image, PIL, image

- `38: RISKY_CALLS = {"eval", "exec", "compile"}`
- `169:     lines.extend(["", "## Suggested review order", "1. Fix critical/high items before autonomous mutation.", "2. Fix medium observability and timeout issues that hide root causes.", "3. Remove release artifacts before zi`
- `213:         if _is_safe_internal_compile(node):`
- `218: def _is_safe_internal_compile(node: ast.Call) -> bool:`
- `219:     """Allow compile(ast_tree, filename, 'exec') in deterministic source audits.`
- `222:     integrity auditor parses files with ast.parse and then compiles the AST to`
- `226:     if _call_name(node.func) != "compile" or len(node.args) < 3:`
- `315:         findings.append(CodeReviewFinding("low", "testing", ".", 1, "Low test density signal", f"Detected {total_tests} tests for {total_functions} functions.", "Prioritise tests around autonomous loops, file/image conte`

### `winlocalassistant\cohesion_engine.py`

Matched: PIL

- `21:         "command": "python -m compileall -q winlocalassistant tests_*.py app.py",`

### `winlocalassistant\command_help.py`

Matched: PIL, browser, gui

- `24:     CommandHelpItem("Core", "/status", "Show workspace and runtime status.", "Confirms Nova is alive and pointed at the expected workspace.", "Run it before debugging model, GUI or command issues.", "/status"),`
- `42:     CommandHelpItem("Run", "/sandbox-dev-run", "Run a command in a copied writable dev workspace.", "Lets Nova test risky edits without touching the live project until promotion.", "Use `linux` or `kali`, then the comman`
- `43:     CommandHelpItem("GUI", "/gui-layout-status", "Check static GUI layout contract.", "Finds missing layout/theme/interaction markers.", "Run then click `layout` in GUI for browser geometry.", "/gui-layout-status"),`
- `44:     CommandHelpItem("GUI", "/gui-reset-help", "Explain safe UI reset.", "Recover stale drawer/cache state without deleting data.", "Run it or press reset UI/fix UI.", "/gui-reset-help"),`
- `45:     CommandHelpItem("GUI", "fix UI button", "Close cluttered drawers/popups and restore the composer.", "Emergency recovery when the GUI is blocking chat.", "Click the floating `fix UI` button.", "fix UI"),`
- `50:     CommandHelpItem("Model", "/model-help-plan", "Ask the selected local model for a contextual repair/build plan.", "Useful when deterministic checks need model reasoning before code changes.", "Give a goal and review t`
- `59:     CommandHelpItem("Regression Guard", "/legacy-continuity-audit", "Check historical Nova capability anchors.", "Prevents valuable old voice, GUI, provider, command and validation features from being accidentally droppe`
- `60:     CommandHelpItem("Regression Guard", "/release-readiness --full", "Run the packaging gate.", "Blocks shipping when chat/help/GUI/code/write/run or continuity checks regress.", "Run it before /release-package; it write`
- `62:     CommandHelpItem("Arcade", "/arcade", "List local Nova Arcade games.", "Launch mini-games without modifying project files.", "Run `/arcade`, then click arcade in the GUI.", "/arcade"),`
- `63:     CommandHelpItem("Arcade", "/arcade-launch system-runner", "Show launch instructions for System Runner.", "Starts the first modular game safely from the GUI.", "Open GUI and press arcade/play.", "/arcade-launch system`
- `90:     lines += ["", "GUI: click `help` for searchable expandable command cards."]`
- `113:         "- GUI recovery: click `fix UI` or run `/gui-layout-status` and `/gui-reset-help`.",`

### `winlocalassistant\command_suggestions.py`

Matched: Image, gui, image, screen, screenshot

- `47:         add("Feature continuity", "/feature-continuity-audit", "Check key Nova GUI/tool surfaces were not accidentally removed.", category="wla")`
- `54:     if any(term in text for term in ["gui", "ui", "layout", "drawer", "blank panel", "broken screen", "screenshot"]):`
- `55:         add("Focus chat", "/validation-status", "Check whether the running backend is current before changing GUI code.", category="gui")`
- `56:         add("GUI visual test", "/gui-visual-test", "Use the existing GUI visual-regression gate before and after layout changes.", category="gui")`
- `57:         add("Route health", "/tool-health-map gui routes", "Check command/tool route health instead of assuming a stale template is correct.", category="gui")`
- `59:     if any(term in text for term in ["video", "image", "media", "comfyui", "storyboard", "trailer", "render"]):`
- `60:         add("Media status", "/media-status", "Check image/video backend readiness before trying expensive generation.", category="media")`
- `61:         add("Image plan", "/image-plan cinematic robot dog mascot", "Create prompt variants and safety metadata before generation.", category="media")`
- `116:     if any(term in text for term in ["tools", "commands", "what can you do", "help", "tool guide"]):`
- `118:         add("Tool guide", "/tool-guide", "Show the local model tool-use guide.", category="help")`

### `winlocalassistant\completion_audit.py`

Matched: PIL, browser, gui

- `43: def _compile_contract(root: Path) -> CompletionCheck:`
- `46:             [sys.executable, "-m", "compileall", "-q", "winlocalassistant", "app.py"],`
- `54:         return CompletionCheck("python_compile_contract", proc.returncode == 0, "compileall passed" if proc.returncode == 0 else "compileall failed", out, "validation")`
- `56:         return CompletionCheck("python_compile_contract", False, repr(exc), category="validation")`
- `63:     promised to the user (commands, GUI buttons, batch options, legacy compatibility,`
- `64:     reports, and no-regression gates) so Nova does not merely compile while silently`
- `99:     checks.append(CompletionCheck("nova_gui_button_and_palette", ok, "GUI exposes Nova full test quick button and command palette item" if ok else "missing GUI markers", json.dumps(missing), "gui"))`
- `102:     checks.append(CompletionCheck("batch_startup_and_one_button_flow", ok, "batch file offers startup gate, one-button Nova test, and browser launch" if ok else "missing batch markers", json.dumps(missing), "startup"))`
- `104:     ok, missing = _has_all(tests116, ["test_nova_system_test_tool_registered_and_renderable", "test_gui_exposes_nova_full_system_button", "test_core_routes_nova_full_system_command"])`
- `105:     checks.append(CompletionCheck("nova_regression_tests_present", ok, "v116 regression tests cover backend, GUI and routing" if ok else "missing regression test markers", json.dumps(missing), "tests"))`
- `116:     checks.append(_compile_contract(root))`
- `194:         lines.append("The requested Nova one-button test, GUI/batch wiring, release packaging/advisor surfaces, legacy compatibility marker, and no-regression gates are all present.")`

### `winlocalassistant\config.py`

Matched: Image, image, llama3.2-vision, vision

- `58:         "NOVA_VISION_MODEL": "vision_model",`
- `135:     # Optional local vision model for /image-analyze and visual project audits.`
- `136:     vision_model: str = "llama3.2-vision:11b"`
- `156:     sandbox_linux_image: str = "python:3.12-slim"`
- `157:     sandbox_kali_image: str = "kalilinux/kali-rolling"`

### `winlocalassistant\core.py`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, screenshot, terminal, upload, vision

- `53:     resolve_image_context,`
- `55: from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `56: from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test`
- `59: from .tool_guides import get_autonomous_tool_use_summary`
- `72: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression`
- `74: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `75: from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help`
- `76: from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades`
- `89: from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation`
- `112:     build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,`
- `114:     patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,`
- `358:     "/self-guide", "/how-to-use", "/full-guide", "/model-timeout",`

### `winlocalassistant\creation_intent.py`

Matched: PIL, browser, gui

- `28:         verification_commands = ["python -m compileall -q winlocalassistant app.py", "python -m pytest -q tests_smoke.py if available"]`
- `42:         verification_commands = ["python -m py_compile script.py"]`
- `44:     elif any(term in low for term in ["todo", "to-do", "web app", "website", "browser app", "html", "css", "javascript"]):`
- `47:         verification_commands = ["node --check app.js if Node is available", "open index.html in a browser"]`
- `55:         verification_commands = ["python -m py_compile file_organiser.py", "run against temporary fixture files only"]`
- `60:         verification_commands = ["python -m py_compile script.py"]`
- `71:         if game_intent.genre == "generic_browser_game":`
- `72:             safety_notes.append("Use a custom generic browser-game scaffold; do not silently substitute a fixed Dodge template.")`
- `73:     elif "document" in words or "readme" in words or "guide" in words:`
- `86:         assumptions.append("Broad utility request; create a small local browser utility with notes, checklist, local saving and export.")`
- `87:     elif any(term in low for term in ["gui", "desktop app"]):`
- `88:         artifact_type = "gui_app"`

### `winlocalassistant\custom_tools.py`

Matched: PIL, gui

- `28: BLOCKED_CALLS = {"eval", "exec", "compile", "open", "__import__", "input", "breakpoint"}`
- `145:     model's broken proposal behind. That confused the GUI because /custom-tools`

### `winlocalassistant\dependency_check.py`

Matched: Image, PIL, browser, image, playwright

- `15:     {"name": "pillow", "import": "PIL", "purpose": "image utilities and future real image outputs", "required": False},`
- `18:     {"name": "diffusers", "import": "diffusers", "purpose": "optional local Diffusers image backend", "required": False},`
- `19:     {"name": "torch", "import": "torch", "purpose": "optional local Diffusers image backend", "required": False},`
- `25:     {"name": "npm", "purpose": "Playwright browser smoke tests", "required": False},`
- `86:             "Install Node/npm only if you want browser smoke tests and JS syntax validation.",`
- `88:             "Heavy image packages are optional; Nova can still run without Diffusers/Torch.",`

### `winlocalassistant\deterministic_generation.py`

Matched: PIL, browser

- `14:     if any(x in low for x in ["game", "website", "web app", "html", "browser"]):`
- `21:         "verify_command": "python -m py_compile script.py",`
- `53:     pattern = re.compile(r"\\b(" + re.escape(target) + r")\\b", re.IGNORECASE)`

### `winlocalassistant\docker_manager.py`

Matched: Image, PIL, gui, image

- `177:     GUI can show why Docker is unavailable instead of silently failing.`
- `189:         "images": [],`
- `217:     images = _run([docker, "images", "--format", "{{json .}}"], timeout=12)`
- `218:     payload["raw"]["docker_images"] = images if include_raw else {k: images.get(k) for k in ["ok", "returncode", "stderr", "elapsed_sec"]}`
- `219:     if images.get("ok"):`
- `220:         payload["images"] = _parse_json_lines(images.get("stdout", ""))[:80]`
- `250: def docker_smoke(config: AssistantConfig, image: str = "python:3.12-slim") -> dict[str, Any]:`
- `254:     # Deliberately simple smoke test. It may pull the image if missing, so expose the exact command.`
- `255:     args = [docker, "run", "--rm", image, "python", "--version"]`
- `257:     _audit("smoke", {"ok": bool(result.get("ok")), "image": image, "returncode": result.get("returncode")})`
- `258:     return {"ok": bool(result.get("ok")), "summary": "Docker smoke test completed" if result.get("ok") else "Docker smoke test failed", "image": image, "raw": result}`
- `276: def _docker_skipped_payload(run_id: str, image: str, command: str, source: Path | None, result: dict[str, Any], reason: str) -> dict[str, Any]:`

### `winlocalassistant\efficiency_profiler.py`

Matched: Image, image

- `81:     relative weak spots: long-running local model/image/tool calls, high CPU time,`
- `91:     extra = model_watts if kind in {"model_call", "image_generation"} else 0.0`

### `winlocalassistant\env_profiles.py`

Matched: gui, playwright

- `8:  'gui-test': {'required':['node','npm'], 'optional':['playwright','chromium']},`
- `38:     if key=='gui-test': return ['npm install -D @playwright/test','npx playwright install chromium']`

### `winlocalassistant\eventlog.py`

Matched: PIL, gui

- `23:     re.compile(r"(?i)\bBearer\s+[A-Za-z0-9._~+/=-]{8,}"),`
- `24:     re.compile(r"(?i)(api[_-]?key|token|password|passwd|secret|authorization)\s*[:=]\s*[^\s,;&\"']{4,}"),`
- `149:     This is a GUI cleanup helper only. It does not touch project files, model output`

### `winlocalassistant\feature_audit.py`

Matched: Image, browser, console, gui, image, playwright

- `65:         "Browser speech, microphone voice input, microphone diagnostic preflight, long-response summarisation, mute/unmute and tutorial controls are wired in the GUI.",`
- `123:         "playwright_scaffold",`
- `124:         "implemented" if _exists(root, "playwright/nova_gui_smoke.spec.js") and "playwright_smoke" in _read(root, "winlocalassistant/wla_doctor.py") else "missing",`
- `125:         "Playwright GUI smoke scaffold exists and release gate runs/skips it depending on environment readiness.",`
- `126:         ["playwright/nova_gui_smoke.spec.js", "playwright_smoke"],`
- `136:         "image_generation_status",`
- `137:         "environment_dependent" if _exists(root, "winlocalassistant/image_generation.py") and all(x in core for x in ["/image-generate", "/image-draft", "/image-setup-help"]) else "missing",`
- `138:         "Image generation refuses to fake real generation and provides setup guidance for SD WebUI/Diffusers/ComfyUI.",`
- `139:         ["/image-generate", "/image-draft", "/image-setup-help"],`
- `140:         "Actual generation depends on a reachable/configured local image backend.",`
- `144:         "browser_console_hygiene",`
- `161:         "General Linux sandbox defaults to a Python-ready image and aliases python3 where possible.",`

### `winlocalassistant\feature_continuity.py`

Matched: browser, gui, screen

- `24:     "jarvis_ui_harness": ["sidecar-enrollment", "bridge-receipts", "browser-harness", "jarvis-test-prompts"],`
- `33:     "voice_reliability_auth": ["voiceAuthPanel", "voiceScreenTranscript", "collapseRepeatedTranscript", "issueVoiceToChat", "Test AI voice", "wlaAutoIdleExplicitOptIn"],`
- `74:     "browser_harness",`
- `108:     but it catches accidental GUI rewrites, missing JS functions, removed command tools,`
- `122:             detail="required browser/UI markers are present" if not missing else "missing required browser/UI markers",`
- `141:         detail="version appears in package and GUI" if version_ok else "version marker is not visible in both package and GUI",`
- `152:         "guidance": [`
- `153:             "Do not remove existing GUI/backend surfaces to make a redesign cleaner; hide, group, or improve them instead.",`
- `171:     lines.append("## Guidance")`
- `172:     for item in payload.get("guidance", []):`

### `winlocalassistant\file_context.py`

Matched: Image, image, upload, vision

- `19: MAX_UPLOAD_BYTES = 25 * 1024 * 1024`
- `22: IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp", ".svg"}`
- `36:     source: str = "upload"`
- `59:     if ext in IMAGE_EXTS or mime.startswith("image/"):`
- `60:         return "image"`
- `149: def image_size(path: Path) -> tuple[int, int] | None:`
- `167:     if kind == "image":`
- `168:         dims = image_size(path)`
- `170:         summary = f"Image file {path.name} ({mime or 'image'}, {size} bytes{dim_text}). Use /image-analyze for vision-model analysis."`
- `171:         context = f"Attached image: {path.name}\nType: {mime or path.suffix}\nSize: {size} bytes{dim_text}\nNote: Nova can pass this image to /image-analyze if a vision model is configured."`
- `196: def register_uploaded_file(name: str, data: bytes, *, mime_type: str = "", profile_dir: Path | None = None) -> SharedFileContext:`
- `197:     if len(data) > MAX_UPLOAD_BYTES:`

### `winlocalassistant\flow_audit.py`

Matched: browser, vision

- `14:         "commands": ["/prompt-contract", "/candidate-tournament", "/iterative-code-loop", "/build-quality-report", "/browser-run-test", "/model-output-coach"],`
- `15:         "tools": ["prompt_contract", "candidate_tournament", "iterative_coding_loop", "build_quality_report", "browser_runtime_test", "model_output_coach"],`
- `16:         "capabilities": ["prompt_to_test", "candidate_tournament", "iterative_coding_repair", "build_quality_browser_runtime"],`
- `96:     return {"ok": ok, "version": __version__, "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "root": str(root), "summary": "Interaction flow audit passed" if ok else f"Interaction flow audit found {len(issues)} issu`

### `winlocalassistant\game_design.py`

Matched: browser

- `85:             explicit_type = "simple browser game"`
- `86:             genre = "generic_browser_game"`
- `93:     if genre == "generic_browser_game":`
- `94:         assumptions.append("The user asked for a vague game, so Nova should create a small custom browser game and state the assumed objective.")`
- `99:     return GameDesignIntent(raw, low, explicit_type, genre not in {"generic_browser_game", "not_game"}, genre, objects, mechanics, behaviours, "custom_canvas_game", assumptions)`
- `118:     title = _title(intent.requested_game_type or "Custom Browser Game")`
- `172: A dependency-free custom browser game generated for: `{user_text}`.`
- `187: Open `index.html` in a browser.`
- `190:         "folder": re.sub(r"[^A-Za-z0-9]+", "", title) or "CustomBrowserGame",`
- `196:         "human_summary": f"A custom browser game: {title}. Open index.html, press Start, use WASD/arrow keys, collect targets, avoid hazards, and restart after game over.",`
- `280: Open `index.html` in a browser.`
- `289:         "human_summary": "A real browser platformer. Open index.html, press Start, move with A/D or arrows, jump with W/Up/Space, collect coins and reach the goal.",`

### `winlocalassistant\gui_context_help.py`

Matched: Image, PIL, browser, gui, image, screen, screenshot, upload

- `3: """Contextual GUI help for Nova.`
- `5: This module is deliberately small and deterministic.  The browser overlay sends`
- `19: class GuiHelpTopic:`
- `28: _TOPICS: tuple[GuiHelpTopic, ...] = (`
- `29:     GuiHelpTopic(`
- `33:         purpose="Type normal prompts or slash commands. Use it for planning, code help, validation checks, and GUI recovery commands.",`
- `37:     GuiHelpTopic(`
- `45:     GuiHelpTopic(`
- `49:         purpose="Find available Nova commands and check whether the visible GUI is connected to the correct backend routes.",`
- `50:         common_commands=("/help", "/command-catalog", "/tool-health-map", "/gui-layout-status", "/build-info"),`
- `53:     GuiHelpTopic(`
- `54:         key="gui",`

### `winlocalassistant\gui_layout_diagnostics.py`

Matched: browser, console, gui, screen, screenshot, terminal, upload

- `3: """Read-only GUI layout diagnostics for Nova.`
- `7: before they try to debug the GUI visually in a browser.`
- `14: LAYOUT_VERSION = "v55.3.164-gui-overhaul-v10-legacy-continuity"`
- `19:         "gui-overhaul-v3",`
- `25:         "apply_gui_layout_overhaul",`
- `61:         "novaGuiHardenLayout",`
- `67:         "novaGuiLayoutDiagnose",`
- `69:         "Browser-side geometry diagnostic is available for visual debugging.",`
- `73:         "runGuiRouteSanity",`
- `75:         "GUI can test backend command route health from the header.",`
- `79:         "runGuiLayoutSanity",`
- `81:         "GUI can report browser-visible layout health from the header.",`

### `winlocalassistant\gui_redesign.py`

Matched: browser, gui, playwright

- `19: def build_gui_feature_map(root: Path) -> dict[str, Any]:`
- `26:     return {"ok": ok, "features": features, "mode_options": ["classic", "cockpit-preview"], "recommendation": "Keep classic UI as default; add cockpit-preview behind /gui-mode cockpit until feature-map and visual tests p`
- `29: def render_gui_feature_map(payload: dict[str, Any]) -> str:`
- `30:     lines = ["# GUI Feature Map", "", f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**", f"Recommendation: {payload.get('recommendation','')}", "", "## Feature coverage"]`
- `38:     return """# Cockpit GUI Redesign Preview\n\nThis is a non-regressing layout plan, not a forced replacement.\n\n## Left rail\nChat, Projects, Build, Validate, Repair, Sandbox, Autonomous, Research, Memory, Settings.\n`
- `41: def gui_regression_check(root: Path) -> dict[str, Any]:`
- `42:     fmap = build_gui_feature_map(root)`
- `43:     return {"ok": fmap.get("ok", False), "feature_map": fmap, "checks": ["feature labels present", "classic mode preserved", "cockpit preview documented"], "next": "Run Playwright visual tests when browser is available."`
- `46: def render_gui_regression(payload: dict[str, Any]) -> str:`
- `47:     return "# GUI Regression Test\n\n" + ("Overall: **PASS**" if payload.get("ok") else "Overall: **ATTENTION**") + "\n\n" + render_gui_feature_map(payload.get("feature_map", {}))`

### `winlocalassistant\high_spec_profile.py`

Matched: llama3.2-vision, vision

- `15:     vision_model: str`
- `43:         "Keep vision model on demand; vision/video jobs are expensive and should not stay hot unnecessarily.",`
- `51:         vision_model="llama3.2-vision:11b",`
- `70:         f"Vision model: `{data.get('vision_model')}`",`

### `winlocalassistant\idle_engine.py`

Matched: PIL

- `104:         "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py",`

### `winlocalassistant\image_generation.py`

Matched: Image, PIL, camera, image, upload

- `17: DEFAULT_IMAGE_NEGATIVE_PROMPT = (`
- `20:     "bad eyes, crossed eyes, uneven eyes, malformed pupils, warped mouth, bad teeth, "`
- `29: PERSON_PROMPT_RE = re.compile(r"\b(face|portrait|person|people|human|woman|man|girl|boy|character|mascot|selfie)\b", re.IGNORECASE)`
- `30: UNSAFE_PROMPT_RE = re.compile(r"\b(naked|nude|nudity|nsfw|topless|porn|explicit)\b", re.IGNORECASE)`
- `34: class ImageGenerationResult:`
- `56:     s = re.sub(r"[^A-Za-z0-9._-]+", "_", text or "generated_image").strip("._")`
- `57:     return (s or "generated_image")[:limit]`
- `61:     configured = _env("NOVA_IMAGE_NEGATIVE_PROMPT", DEFAULT_IMAGE_NEGATIVE_PROMPT)`
- `68: def prepare_image_prompt(prompt: str) -> dict[str, Any]:`
- `77:     enhance = _env("NOVA_IMAGE_ENHANCE_PROMPT", "1").lower() not in {"0", "false", "no", "off"}`
- `78:     quality_prompt = _env("NOVA_IMAGE_QUALITY_PROMPT", "")`
- `123:         import PIL  # noqa: F401`

### `winlocalassistant\improvement_cycle.py`

Matched: browser, gui

- `85:             "Voice issues depend on browser/device state, so completed proposals should preserve mic-test and setup wizard guidance.",`
- `154:             "- Seeded regression-memory guidance in the report so recurring failures remain visible.",`

### `winlocalassistant\improvement_roadmap.py`

Matched: PIL, gui

- `69:             "Write a reusable validation checklist into the proposal ledger covering compile, smoke, focused pytest, mega-test, and hygiene gates.",`
- `75:     if any(w in low for w in ["gui", "cockpit", "ui"]):`
- `77:             "next-gui-safe-rollout",`
- `78:             "Add GUI redesign rollout gates to the proposal roadmap",`
- `79:             "A GUI redesign is valuable but risky; it needs a staged plan before becoming default.",`
- `80:             "Add GUI mode, feature map, regression test and visual-gate references to the roadmap's validation pack.",`
- `81:             commands=["/gui-feature-map", "/gui-regression-test", "/gui-visual-test"],`
- `84:             validation=["/gui-feature-map", "/gui-regression-test"],`
- `106:             "gui": ["gui", "cockpit", "visual"],`
- `137:         f"Validation: compile/readback checks are recorded in the roadmap JSON.",`
- `158:         cmd = [sys.executable, "-m", "compileall", "-q", "winlocalassistant", "app.py"]`
- `203:             "python -m compileall -q winlocalassistant app.py",`

### `winlocalassistant\integration_radar.py`

Matched: browser, gui, playwright

- `67:     playwright_available = _exe("npx") or _python_module("playwright")`
- `108:         "Playwright browser smoke tests", "gui-testing", playwright_available and node_available, 86,`
- `109:         "ready" if playwright_available and node_available else "node/npx/playwright not fully available",`
- `110:         "Catch Send-button and JavaScript UI failures through real browser interaction, not just static JS parsing.",`
- `111:         "Add a browser smoke test for sending chat, toggling tabs and Docker panel buttons.",`
- `112:         "npx playwright test", "medium",`
- `126:         "Keep Docker as the main patch simulation backend and add profile history/GUI review.",`
- `169:     if any(c.name.startswith("Playwright") and c.available for c in candidates):`
- `170:         return "Highest value next integration: Playwright browser smoke tests, because Nova has had real GUI regressions that static tests only partly cover."`
- `171:     return "Highest value next integration: keep Docker validation as the baseline, then add Git and browser smoke testing when those tools are available."`

### `winlocalassistant\integration_review.py`

Matched: browser, gui, playwright, screen, screenshot

- `11: from .browser_worker import build_browser_task_plan`
- `31:     browser_plan = build_browser_task_plan("read a local documentation page and capture screenshot evidence")`
- `42:         {"name": "browser_worker_is_read_only_by_default", "ok": browser_plan.get("classification", {}).get("read_only") is True},`
- `50:         gaps.append("GUI webui.py missing; browser smoke cannot run.")`
- `68:         "browser_plan": browser_plan,`
- `75:             "browser-use/Playwright-style browser worker as a permission-gated plan with evidence",`

### `winlocalassistant\intent_planning.py`

Matched: browser, gui

- `34:     ambiguity: list[str] | None = None`
- `96:     ambiguity = task_plan.ambiguity`
- `116:         return PlanningDialog(False, "", [], "", "Request has enough detail.", normalized, intents, subtasks, plan_level, intent_confidence, ambiguity, success_criteria)`
- `164:     return PlanningDialog(False, "", [], "", "No planning dialog needed.", normalized, intents, subtasks, plan_level, intent_confidence, ambiguity, success_criteria)`
- `170:     return PlanningDialog(True, question, choices, rec, reason, normalized, intents, subtasks, plan_level, plan.intent_confidence, plan.ambiguity, plan.success_criteria)`
- `218:     if isinstance(game_design, dict) and game_design.get("genre") == "generic_browser_game":`

### `winlocalassistant\iterative_coding.py`

Matched: PIL, browser

- `116:         actions.append({"type": "verify_only", "target": ".", "reason": "No obvious static surgical repair target found", "instruction": "Run prompt-contract, build-quality, browser-runtime and final checks before broad `
- `137:                 {"tool": "prompt_contract", "why": "compile prompt-specific must-have and must-not-have checks"},`
- `139:                 {"tool": "browser_runtime_test", "why": "exercise UI/storage/export behaviour where possible"},`
- `154:         "promotion_gate": ["py_compile if Python changed", "node --check for JS when available", "prompt_test_run", "build_quality_report", "browser_runtime_test", "final_project_check"],`

### `winlocalassistant\jarvis_bridge.py`

Matched: Image, PIL, browser, clipboard, console, gui, image, playwright, screen, screenshot, terminal

- `107:         "allow_browser_control": False,`
- `108:         "screen_awareness": "off",`
- `112:             "Sidecar, screen, browser, filesystem and shell control remain disabled until explicitly changed.",`
- `153:             "Sidecars can extend reach to desktop, files, terminal, clipboard and browser.",`
- `158:             "screen_awareness",`
- `162:             "Screen context can help an assistant notice errors or stuck tasks.",`
- `163:             "Nova stores only user-approved summaries/receipts, not continuous screenshots by default.",`
- `185:             "browser_control",`
- `186:             "planned_as_test_harness_not_general_autopilot",`
- `189:             "Browser automation can validate GUI flows and generated web apps.",`
- `190:             "Expose as Playwright/browser smoke tests first, not silent browsing of user accounts.",`
- `212:             "Sidecar/screen/browser/shell actions must be visible, reversible where possible, and recorded.",`

### `winlocalassistant\legacy_continuity.py`

Matched: browser, gui, upload

- `59:         commands=("/activity", "/live-timeline", "/gui-layout-status"),`
- `60:         test_suggestions=("tests_v55_3_141_voice_resize_coding_flow.py", "tests_gui_interaction_overhaul.py", "tests_emergency_stability.py"),`
- `65:         name="Pipeline routing, browser smoke and live timeline observability",`
- `68:         required_text=(("winlocalassistant/core.py", "/pipeline-route"), ("winlocalassistant/core.py", "/browser-smoke"), ("winlocalassistant/core.py", "/live-timeline"), ("winlocalassistant/tools.py", "live_timeline")),`
- `69:         commands=("/pipeline-route", "/browser-smoke", "/live-timeline", "/project-patterns"),`
- `182:             "This deterministic check covers known uploaded/diffed historical anchors and local zip candidates visible to this runtime.",`
- `244:         "- Run `/legacy-continuity-audit` before packaging any GUI/core/autonomous patch.",`

### `winlocalassistant\main.py`

Matched: browser, console

- `10: def _configure_console_output() -> None:`
- `22:     _configure_console_output()`
- `24:     parser.add_argument("--web", action="store_true", help="Run browser UI on localhost.")`

### `winlocalassistant\maintenance_validation.py`

Matched: Image, PIL, image

- `31:     "python -W error::SyntaxWarning -m compileall -q app.py winlocalassistant tests_smoke.py",`
- `33:     "$env:NOVA_IMAGE_BACKEND='auto'; $env:NOVA_DIFFUSERS_MODEL=''; $env:NOVA_ALLOW_DIFFUSERS_DOWNLOAD='0'; python -m pytest",`
- `98: def _image_backend_test_env() -> dict[str, Any]:`
- `100:         "NOVA_IMAGE_BACKEND": os.environ.get("NOVA_IMAGE_BACKEND", ""),`
- `108:         "stable_pytest_prefix": "$env:NOVA_IMAGE_BACKEND='auto'; $env:NOVA_DIFFUSERS_MODEL=''; $env:NOVA_ALLOW_DIFFUSERS_DOWNLOAD='0'",`
- `109:         "summary": "Image fallback tests are isolated" if fallback_isolated else "Image backend is enabled; fallback tests must clear image env first",`
- `148:     image_env = _image_backend_test_env()`
- `157:     image_warning = not image_env["ok"]`
- `164:         _check("image_backend_test_env", True, "warning" if image_warning else "info", image_env["summary"], image_env),`

### `winlocalassistant\mission_planner_v2.py`

Matched: gui

- `13:     if any(k in low for k in ['gui','ui','layout']): allowed += ['gui-feature-map','gui-regression-test','gui-visual-test']`

### `winlocalassistant\model_calibration.py`

Matched: browser

- `30:     "make a browser game",`

### `winlocalassistant\model_context.py`

Matched: Image, PIL, gui, image, screen, screenshot, upload, vision

- `176:                 "image_hint": f"Use /image-analyze context:{ctx.context_id} => PROMPT analyzes an uploaded image/photo" if ctx.kind == "image" else "",`
- `249:         "code_debug": ["code", "traceback", "bug", "fix", "repair", "test", "pytest", "compile", ".py", ".js"],`
- `250:         "file_context": ["uploaded", "attached", "file", "photo", "image", "screenshot", "context"],`
- `301:         vision_model="",`
- `333:             "/context-files lists uploaded files/photos and IDs",`
- `334:             "/image-analyze context:ID => PROMPT analyzes an uploaded image/photo",`
- `336:             "/comm-box MESSAGE writes to the GUI AI communication box",`

### `winlocalassistant\model_download_manager.py`

Matched: Image, gui, image, llama3.2-vision, screen, screenshot, upload, vision

- `68:     "vision": OllamaModelSpec(`
- `69:         key="vision",`
- `70:         model="llama3.2-vision:11b",`
- `71:         title="Llama 3.2 Vision 11B",`
- `72:         purpose="Optional image/photo understanding for uploaded screenshots and visual repair context.",`
- `73:         use_when=("image analysis is requested", "GUI screenshot diagnosis", "visual project repair"),`
- `74:         avoid_when=("no image tasks", "low VRAM/disk headroom"),`
- `99:     "image": "vision",`
- `100:     "photo": "vision",`
- `101:     "screenshot": "vision",`
- `155:     if any(w in low for w in ("image", "photo", "screenshot", "vision", "gui screenshot", "visual")):`
- `156:         keys.append("vision")`

### `winlocalassistant\model_registry.py`

Matched: Image, image, llama3.2-vision, vision

- `44:         ModelRole("vision", "llama3.2-vision:11b", "llama3.2-vision:11b" in installed_set, "", "image analysis only"),`
- `55:             "vision models are only selected for image tasks",`

### `winlocalassistant\next_feature_suite.py`

Matched: Image, PIL, browser, gui, image, playwright

- `61:     add('html_links_js', ('app.js' in html) if html else False, 'HTML should reference app.js for browser apps.')`
- `108:     return recs or ['Build quality checks passed; run browser runtime tests for stronger evidence.']`
- `119: def build_browser_runtime_test(root: Path, goal: str = '', mode: str = 'run') -> dict[str, Any]:`
- `125:     add('browser_entrypoint_exists', bool(html), 'index.html exists for browser testing.')`
- `134:     path = _docs(root) / 'NOVA_BROWSER_RUNTIME_TEST_LATEST.json'`
- `136:     atomic_write_text(path.with_suffix('.md'), render_browser_runtime(payload))`
- `147: def render_browser_runtime(payload: dict[str, Any]) -> str:`
- `148:     lines = ['# Browser Runtime Test','',f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**",f"Root: `{payload.get('root','')}`",'','## Checks']`
- `173:     payload={'ok': True,'focus':focus,'strategy':['If JSON invalid: run /model-output-repair-json before retrying.','If off-course twice: run /prompt-contract and block unrelated templates.','If local model busy/degraded`
- `188:     q=load_patch_queue(); item={'id':f"patch_{int(time.time())}_{len(q.get('patches',[]))+1}", 'goal':goal or 'safe Nova patch', 'risk':risk, 'diff':diff, 'status':'proposed', 'created_at':_now(), 'validation':['python -`
- `218: def build_gui_cockpit_v2(root: Path, mode: str='preview') -> dict[str, Any]:`
- `220:     payload={'ok': True,'mode':mode,'feature_flagged': True,'classic_preserved': True,'layout':{'left':['Chat','Projects','Build','Validate','Repair','Sandbox','Autonomous','Research','Memory','Settings'],'center':['Prom`

### `winlocalassistant\nova_agent_upgrade_lab.py`

Matched: PIL, gui, llama3.2-vision, vision

- `95:             why_it_helps="Nova avoids one-size-fits-all local-model settings by separating chat, code, long-context, vision and tooling prompts.",`
- `96:             safe_implementation="Use /ollama-runtime-profile GOAL => HARDWARE to generate read-only Modelfile/options guidance.",`
- `203:         "local_model_guidance": [`
- `220:     lines.extend(["", "## Guidance"])`
- `221:     lines.extend(f"- {item}" for item in payload.get("local_model_guidance", []) or [])`
- `232:         {"name": "syntax_or_compile", "check": f"run `{plan.get('verify_command')}`", "risk_caught": "invalid syntax before runtime testing"},`
- `248:         "Run syntax/compile verifier first.",`
- `267:     """Create read-only Ollama profile guidance for a task/hardware pairing."""`
- `275:         "vision": "llama3.2-vision:11b",`
- `377:             "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py tests_nova_route_resilience_v55_3_130.py tests_nova_deep_research_v55_3_129.py tests_nova_agent_upgrade_v55_3_127.py `

### `winlocalassistant\nova_api.py`

Matched: gui

- `13: from .nova_odysseus_suite import build_gui_workbench_plan, build_odysseus_workspace_snapshot, build_suite_status, odysseus_dependency_status, odysseus_runtime_action, odysseus_workspace_action`
- `46:     "/nova-gui-workbench-plan",`
- `126:     "/nova-gui-workbench-plan",`
- `320:         return build_gui_workbench_plan(root)`

### `winlocalassistant\nova_arcade.py`

Matched: browser, gui

- `6: actual browser game runtime is injected by ``webui_arcade.py`` so future games`
- `7: can be added by extending the registry without rewriting the core GUI shell.`
- `62:         "A local-only modular mini-game shelf embedded in Nova. Future games are added through the registry instead of rewriting the GUI.",`
- `80:         "## GUI usage",`
- `81:         "Click the `arcade` header button, or run `/arcade-launch system-runner` and then use the GUI launcher button.",`
- `82:         "High score is stored in browser `localStorage`, not in backend project files.",`
- `95:         f"Use the GUI header button `arcade`, then click **Launch {game.name}**.\n\n"`
- `97:         "This is a local browser mini-game. It does not modify Nova project files and does not call external services."`

### `winlocalassistant\nova_capability_drift_lab.py`

Matched: PIL, browser

- `232:         {"pattern": "wrong-runtime coding", "example": "build a CLI but output is only index.html", "expected": "selects Python/Java/Node/PowerShell/browser based on goal"},`
- `234:         {"pattern": "tool unavailable", "example": "missing optional compiler", "expected": "falls back to static checks and states limitation"},`

### `winlocalassistant\nova_coding_capabilities.py`

Matched: Image, PIL, browser, console, gui, image, screen, screenshot, vision

- `49:     if one_file_requested and has_any("python", ".py", "script") and not has_any("website", "browser", "html", "game"):`
- `58:             verify_command="py -3 -m py_compile script.py",`
- `72:             why="The prompt explicitly asks for TypeScript, so Nova should create TypeScript sources and supporting Node project metadata instead of plain browser files.",`
- `76:             verify_command="node -e \"const fs=require('fs'); for (const p of ['package.json','tsconfig.json','src/index.ts']) if (!fs.existsSync(p)) throw new Error('missing '+p); console.log('typescript project files o`
- `82:                 "Avoid browser DOM code unless the user requested a browser UI.",`
- `105:     elif has_any("markdown", "readme", "documentation", "docs") and not has_any("website", "browser", "html", "web app"):`
- `123:     elif has_any("json config", "json schema", "config file", "configuration file", "settings file", "settings json") or (has_any("json") and not has_any("parse", "parser", "python", "script", "api", "browser", "website"`
- `147:             why="The prompt explicitly asks for Java or Java runtime concepts, so Nova should not convert it into browser files.",`
- `156:                 "Use console I/O for CLI tasks or Swing only when a desktop GUI is explicitly requested.",`
- `159:             efficiency_notes=["A single-file Java program is fastest to compile, inspect and run for small tasks."],`
- `170:             verify_command="py -3 -m py_compile main.py",`
- `179:             efficiency_notes=["Use py_compile first; only start the server when the user explicitly asks to run it."],`

### `winlocalassistant\nova_deep_research_lab.py`

Matched: PIL, browser, gui

- `180:         TraceSpan("report.final", ["artifact_paths", "limitations", "regression_status"], ["private scratchpad"], "final report distinguishes passed, failed and untested items"),`
- `298:     runtime = "browser"`
- `309:     base = [VerifierStep("syntax_compile", "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py", "protect Nova source files")]`
- `311:         "python": [VerifierStep("python_compile", "python -m py_compile path/to/main.py", "check generated Python syntax"), VerifierStep("python_smoke", "python path/to/main.py --help", "verify entrypoint starts", False)`
- `312:         "java": [VerifierStep("java_compile", "javac Main.java", "check Java syntax and imports"), VerifierStep("java_run", "java Main", "verify CLI/main flow", False)],`
- `315:         "fastapi": [VerifierStep("python_compile", "python -m py_compile app.py", "check API syntax"), VerifierStep("fastapi_import", "python -c \"import app; print('import ok')\"", "verify app imports without starting s`
- `316:         "browser": [VerifierStep("html_files", "dir /b index.html app.js style.css", "confirm expected browser files", False), VerifierStep("node_syntax", "node --check app.js", "check JS syntax if Node exists", False)],`
- `318:     steps = base + by_runtime.get(runtime, by_runtime["browser"]) + [VerifierStep("smoke", "python tests_smoke.py", "run Nova smoke suite")]`
- `321:         _check("syntax_gate_present", any("compile" in s.name or "syntax" in s.name or "parse" in s.name for s in steps), "Syntax/parse gate exists."),`

### `winlocalassistant\nova_efficiency_audit.py`

Matched: Image, gui, image, playwright, screen, screenshot

- `73:             recommendation="Prefer additive extraction around stable seams: routing tables, GUI command metadata, media planning, and audits should live in smaller modules with focused tests.",`
- `98:             category="gui",`
- `99:             title="Monolithic GUI file is a regression risk",`
- `109:             findings.append(AuditFinding("low", "gui", title, f"Missing marker `{marker}` in webui.py.", "Install the focus-mode GUI layer and command palette shortcut.", "winlocalassistant/webui.py"))`
- `122:     for cmd in ["/media-status", "/image-plan", "/video-storyboard", "/video-package", "/nova-efficiency-audit"]:`
- `138:             source="Playwright visual comparisons",`
- `139:             relevance="Screenshot baselines catch GUI regressions that unit tests miss.",`
- `140:             nova_action="Keep optional Playwright visual tests and add a calm-layout screenshot smoke test for the chat/drawers/popups.",`
- `144:             relevance="Spans and structured events make failures visible across agent, tool, model and GUI layers.",`
- `152:         "Run a focused pytest slice for changed GUI/media/model files.",`
- `155:         "Use optional Playwright visual smoke tests before changing GUI layout again.",`

### `winlocalassistant\nova_eval_packs.py`

Matched: gui

- `72:             NovaEvalCase("gui_workbench", "/nova-gui-workbench-plan", "Odysseus-style GUI workbench plan remains available", ("GUI Workbench Plan", "Rail"), "ux"),`

### `winlocalassistant\nova_improvement_assurance_lab.py`

Matched: PIL, browser

- `61:     "python": ["python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py"],`
- `65:     "browser": ["project runtime probe or browser harness for changed browser app"],`
- `113:         return "browser"`
- `143:     commands: list[str] = ["python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py"]`
- `197:         EvidenceGate("syntax_and_imports", "catch broken Python imports/registry wiring before runtime", ["py_compile over app.py and winlocalassistant/*.py", "focused test module import"], "zero syntax/import errors"),`
- `281:         {"name": "mentions_validation", "ok": any(w in low for w in ["validation", "tests", "smoke", "pytest", "py_compile"]), "detail": "Success claims should name actual validation."},`

### `winlocalassistant\nova_improvement_research.py`

Matched: browser

- `11:         "why": "Local assistants gain power from file, shell and browser tools, so every mutating action should carry a risk label, approval state and validation receipt.",`

### `winlocalassistant\nova_inspiration_engine.py`

Matched: Image, PIL, browser, gui, image, vision

- `46:     "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py",`
- `53:     "gui": ("gui_feature_coverage", "gui_regression_test", "gui_snapshot", "browser_run_test", "feature_readiness"),`
- `54:     "webui": ("gui_feature_coverage", "gui_regression_test", "gui_snapshot", "browser_run_test"),`
- `61:     "image": ("image_analyze", "image_generate", "vision_status", "vision_model"),`
- `215:             "Normalize the request, detect ambiguity, and decide whether this is chat, code, GUI, voice, model, or autonomous work.",`
- `289:             findings.append({"level": "medium", "item": file_name, "reason": "Python source change requires py_compile and smoke tests"})`
- `305:     if "gui" in lower_goal or "webui" in lower_goal or "layout" in lower_goal:`
- `306:         targeted_tests.append("python -m pytest -q tests_webui_planning_visibility.py tests_gui_layout_v55_3_18.py")`
- `352:             suggested_command="/handoff-plan fix GUI layout and validate no regression",`

### `winlocalassistant\nova_odysseus_suite.py`

Matched: Image, gui, image, playwright, screen, upload, vision

- `23: ODYSSEUS_SOURCE = "uploaded odysseus-main.zip and public README feature map"`
- `57:         "nova_adaptation": "Nova now detects RAM/CPU/NVIDIA VRAM where available, accepts what-if hardware hints, ranks local model choices and prints install/serve guidance without auto-downloading.",`
- `125:         "name": "Extras: uploads, vision, image, themes, sessions, web search, presets, 2FA style hardening",`
- `126:         "odysseus_surface": "Image editor, theme editor, uploads, vision/PDF, web search, presets, sessions and two-factor extras.",`
- `127:         "nova_command": "/attach-file, /image-analyze, /image-generate, /chats, /nova-presets, /nova-theme-plan, /nova-auth-plan",`
- `129:         "nova_adaptation": "Nova already has file/image/chat/web search surfaces; this patch adds presets plus theme/auth hardening plans.",`
- `148:         "id": "gui_workbench_layout",`
- `149:         "name": "Odysseus-style GUI workbench layout",`
- `150:         "odysseus_surface": "Odysseus uses an icon rail, collapsible sidebar, tool launchers, modals/fullscreen workspaces, settings tabs, theme controls and mobile/PWA routing.",`
- `151:         "nova_command": "/nova-gui-workbench-plan",`
- `161:         "nova_adaptation": "Nova now detects a configured Odysseus checkout, reports runtime health, and exposes confirmed GUI/API controls to start or stop the optional dependency.",`
- `180:     "image_generation": {"level": "ask", "reason": "generation uses external/local GPU resources and may write files"},`

### `winlocalassistant\nova_operating_context.py`

Matched: browser, gui, screen

- `72:         "do not remove existing user-facing GUI/backend features while improving or redesigning",`
- `85:     if "gui" in low or "ui" in low or "interface" in low:`
- `87:             "GUI changes must preserve existing element IDs/function entry points unless compatibility wrappers are added",`
- `141:             "For external daemon/sidecar/screen/shell/browser work, keep Nova as supervisor and queue actions through policy/receipts instead of silent execution.",`
- `143:         "external_daemon_context": build_capability_map() if any(k in (goal or '').lower() for k in ["jarvis", "daemon", "sidecar", "screen", "browser", "shell", "proactive"]) else {},`

### `winlocalassistant\nova_reliability_lab.py`

Matched: PIL, browser, console

- `66:         "ui": {"webui", "layout", "panel", "browser", "html", "javascript"},`
- `181:         ImpactRule("winlocalassistant/webui.py", "Browser cockpit/UI changed.", ["tests_webui_planning_visibility.py", "tests_v55_ux_game.py", "tests_feature_continuity.py"], ["python -m pytest -q tests_webui_planning_vi`
- `215:         "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py tests_nova_reliability_v55_3_128.py",`
- `223:         _check("syntax_gate_present", any("py_compile" in cmd for cmd in commands_unique), "Syntax compilation gate is included."),`
- `321:         metrics = ["time_to_first_token", "total_latency", "compile_pass", "test_plan_quality", "hallucinated_file_count"]`
- `344:             "Watch `ollama ps` for CPU offload; CPU spillover is usually the biggest slowdown on 4GB VRAM.",`
- `408:         "autonomous_memory", "console_test", "handoff_plan", "improvement_preflight",`

### `winlocalassistant\nova_route_resilience_lab.py`

Matched: PIL, terminal

- `146:         return "small_gpu_or_cpu_spill_risk"`
- `177:         {"name": "fallbacks_present", "ok": all(n.fallback_next or not n.primary_next for n in nodes), "detail": "Every non-terminal route has at least one fallback."},`
- `330:     if tier in {"small_gpu_or_cpu_spill_risk", "cpu_first"}:`

### `winlocalassistant\nova_system_test.py`

Matched: PIL, browser, gui

- `19: from .jarvis_bridge import build_capability_map, build_safe_browser_harness, probe_jarvis_daemon`
- `91:         # Some Windows/browser helper tests can leave a grandchild with inherited stdout;`
- `159:         detail = "missing markers: " + ", ".join(missing) if missing else "browser contract markers present"`
- `161:         return NovaSystemStep("webui_contract_and_js", "gui", ok, "GUI contract passed" if ok else "GUI contract failed", detail, round(time.time() - started, 3))`
- `163:         return NovaSystemStep("webui_contract_and_js", "gui", False, repr(exc), "", round(time.time() - started, 3))`
- `224:         harness = build_safe_browser_harness("http://127.0.0.1:8766", mode="plan")`
- `225:         checks.append(NovaSystemStep("safe_browser_harness", "integrations", bool(harness.get("ok")), harness.get("summary", "browser harness"), json.dumps(harness, indent=2, default=str)[:2200], round(time.time() - star`
- `227:         checks.append(NovaSystemStep("safe_browser_harness", "integrations", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))`
- `247:         return NovaSystemStep("deterministic_coding_fallback", "coding", ok, "coding fallback can build a validated browser game" if ok else "coding fallback is incomplete", detail, round(time.time() - started, 3))`
- `261:         steps.append(_run(root, "python_compile", "code", [py, "-m", "compileall", "-q", "winlocalassistant", "app.py"], timeout=min(max(timeout, 60), 240)))`

### `winlocalassistant\nova_verified_changes.py`

Matched: PIL, gui, upload

- `16: BLOCKED_PARTS = {".git", "__pycache__", ".venv", "venv", "node_modules", "data", "logs", "uploads", "generated", "dist", "build"}`
- `76:         f"{sys.executable} -m compileall -q app.py winlocalassistant",`
- `92: 2. **Cookbook-style local model setup** — scan hardware, recommend fitting models, then provide one-click or one-command setup guidance.`
- `137: - No writes to `.git`, runtime data, logs, uploads, generated artefacts, virtual environments, build folders or dependency folders.`

### `winlocalassistant\nova_video.py`

Matched: Image, camera, image

- `38:     storyboard_image: str | None = None`
- `93:                 storyboard_image=f"assets/storyboards/{shot_id}.png",`
- `426:             "output": shot.get("storyboard_image"),`
- `483: def build_video_image_prompt_plan(manifest: VideoManifest | dict[str, Any]) -> dict[str, Any]:`
- `484:     """Map each video shot to storyboard, keyframe and final-frame image prompts."""`
- `493:             "start_keyframe_prompt": f"first frame for image-to-video, stable subject identity, {base}",`
- `494:             "end_keyframe_prompt": f"final frame for image-to-video, consistent subject and camera direction, {base}",`
- `584:     prompt_plan = build_video_image_prompt_plan(manifest)`
- `585:     prompt_plan_path = output_dir / "video_image_prompts.json"`
- `599:         "image_prompts_path": str(prompt_plan_path),`
- `604:         "image_prompt_plan": prompt_plan,`
- `618:     for key in ["manifest_path", "storyboard_path", "shotlist_path", "image_prompts_path", "preview_video_path", "preview_html_path", "validation_path", "ffmpeg_plan_path"]:`

### `winlocalassistant\ollama.py`

Matched: Image, PIL, image, vision

- `14: # Ollama will happily accept more than one HTTP request, but small local models`
- `15: # often degrade, stall or return partial JSON if we pile prompts onto them.`
- `247: def ollama_vision_chat(`
- `251:     image_paths: list[str],`
- `253:     desc: str = "local vision model call",`
- `258:     """Call Ollama vision-capable models through /api/chat using image inputs.`
- `260:     This uses the same single-prompt lock as text generation. Ollama vision-capable`
- `261:     models accept base64-encoded images in the message `images` field. If the`
- `262:     selected model is not a vision model, Ollama will usually return an error or`
- `294:         images: list[str] = []`
- `295:         for image_path in image_paths:`
- `296:             with open(image_path, "rb") as f:`

### `winlocalassistant\optional_upgrade_installer.py`

Matched: browser, gui, playwright

- `47:     "playwright": OptionalUpgrade(`
- `48:         key="playwright",`
- `49:         title="Playwright browser GUI smoke testing",`
- `50:         purpose="Catches microphone button, Send button, layout, and live activity regressions in a real Chromium browser.",`
- `51:         check_command=["npx", "playwright", "--version"],`
- `52:         install_command=["npm", "install", "-D", "@playwright/test"],`
- `53:         verify_command=["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"],`
- `54:         files_expected=("playwright/nova_gui_smoke.spec.js",),`
- `62:     "gui": "playwright",`
- `63:     "browser": "playwright",`

### `winlocalassistant\orchestration_foundation.py`

Matched: PIL, browser, gui, screen, screenshot

- `307:         ToolContract("run_project_tests", "Run pytest/compile checks in the current project", risk_level="low", timeout_seconds=600, validation_command="python -m pytest -q"),`
- `309:         ToolContract("browser_research", "Read-only browser research with screenshots", risk_level="medium", requires_approval=True, timeout_seconds=180),`
- `334:             "Wire GUI state badge to NovaStateMachine.state",`
- `335:             "Route long-running coding/browser/video tasks through JobQueue leases",`

### `winlocalassistant\performance_tuning.py`

Matched: upload

- `156:     lines += ["", "Use `/perf-benchmark --write-scripts` to generate reproducible benchmark scripts and `/perf-artifact-checklist` before uploading results."]`
- `274: Upload these after running the benchmark collector:`
- `357: This document implements the safe parts of the uploaded performance research PDF.`
- `365: - `/perf-artifact-checklist` - show exactly what to upload for further tuning.`

### `winlocalassistant\persona_profile.py`

Matched: browser, gui

- `30:         "Ask or gate before risky file, shell, browser, sidecar, or system actions.",`
- `148:         f"- Current mode: {mode}; mode guidance: {(profile.get('modes') or {}).get(mode) or (profile.get('modes') or {}).get('default','')}",`

### `winlocalassistant\pipeline_manifests.py`

Matched: browser, console, gui, playwright, screen, screenshot, terminal

- `54:         triggers=("what did you run", "show evidence", "terminal", "commands", "why did it fail"),`
- `63:         upgrade_notes="Backs the collapsed terminal indicator requested in the Orbit GUI.",`
- `65:     "browser_gui_smoke": CapabilityManifest(`
- `66:         manifest_id="browser_gui_smoke",`
- `67:         inspired_by="browser-use style web interaction checks",`
- `68:         purpose="Catch GUI regressions that static JS parsing misses.",`
- `69:         nova_area="webui/orbit-gui/voice-panels",`
- `70:         triggers=("gui", "drawer", "button", "browser", "overlap", "console error"),`
- `74:             "prepare browser harness command",`
- `75:             "record console/layout risk notes",`
- `77:         validation=("/browser-smoke", "/browser-harness", "node --check extracted JS"),`
- `78:         guardrails=("do not rely on screenshots alone", "record console errors", "keep fallback static smoke"),`

### `winlocalassistant\pipeline_router.py`

Matched: Image, PIL, browser, gui, image

- `53:             PipelineStage("Run browser smoke", "browser_smoke", "Catch GUI/runtime marker issues early.", "Browser smoke passes."),`
- `94:     "gui": PipelineRoute(`
- `95:         kind="gui",`
- `96:         title="GUI/browser smoke pipeline",`
- `98:         reason="The request targets UI/GUI/browser layout; verify static JS and browser-ready markers before claiming a visual fix.",`
- `100:             PipelineStage("Parse Web UI JavaScript", "browser_smoke", "Catch missing functions and syntax errors before launch.", "JS parse/checks pass."),`
- `101:             PipelineStage("Run GUI regression sweep", "regression_sweep", "Ensure new layout did not drop features.", "GUI-related sweep returns ok."),`
- `120:         title="Image/video media planning pipeline",`
- `122:         reason="The request asks for image/video/storyboard/media generation; check backend readiness and produce manifests before heavy rendering.",`
- `124:             PipelineStage("Check media status", "media_status", "Know whether SD WebUI, Diffusers, ComfyUI, ffmpeg and Node are ready.", "Status distinguishes unavailable, simulated and real backends."),`
- `125:             PipelineStage("Plan image prompts", "image_plan", "Create prompt variants before expensive generation.", "Prompt plan renders seeds/variants and negative prompts."),`
- `178:     if any(x in g for x in ["repo", "repos", "github", "openmontage", "openhands", "open hands", "browser-use", "mem0", "tabby", "livekit", "odysseus"]):`

### `winlocalassistant\planner.py`

Matched: browser, gui

- `108:     registered/current projects and produce improvement guidance or safe targeted`
- `171:     repo_markers = ["repo", "repos", "github", "openmontage", "open hands", "openhands", "browser-use", "mem0", "tabby", "livekit", "odysseus"]`
- `215:             PlanStep("Run browser/GUI smoke preflight", "browser_smoke", {"path": "."}),`

### `winlocalassistant\planning_dashboard.py`

Matched: PIL, gui

- `91:         return "Nova should pause or show choices because the request has ambiguity, multiple steps, lower confidence, or watcher review requirements."`
- `125:         return ["py_compile", "tests_smoke.py", "relevant pytest suites", "quality dashboard"]`
- `252:     return ["py_compile", "python tests_smoke.py", "relevant pytest suites"]`

### `winlocalassistant\project_acceptance.py`

Matched: PIL, browser, screen

- `40:             repair_hints=["Do not convert TypeScript requests into browser-only JavaScript; create src/index.ts plus package metadata."],`
- `47:             verification_focus=["FastAPI", "route", "py_compile", "uvicorn", "README"],`
- `56:             repair_hints=["Do not convert Java requests into browser code; create compileable Java source."],`
- `80:             repair_hints=["Use Node CLI files rather than browser DOM code when the prompt asks for a command-line tool."],`
- `86:             required_behaviours=["runnable Python entrypoint", "clear input/output handling", "error handling", "py_compile verification"],`
- `87:             verification_focus=["if __name__", "argparse or main", "py_compile", "README"],`
- `90:     if any(term in low for term in ["markdown", "readme", "documentation", "docs"]) and not any(term in low for term in ["website", "browser", "html", "web app", "server", "script", "cli"]):`
- `98:     if any(term in low for term in ["json config", "json schema", "config file", "configuration file", "settings file", "settings json"]) or ("json" in low and not any(term in low for term in ["parse", "parser", "python"`
- `167:             artifact_type="browser_game",`
- `206:             # README is desirable but not always mandatory for one-file browser artifacts.`
- `215:         add("calculator_result", has_any("result", "display", "screen", "textcontent", "value"), "Visible result update")`
- `223:     elif contract.artifact_type in {"browser_game", "snake_game"}:`

### `winlocalassistant\project_brief.py`

Matched: PIL, browser, console, screen

- `51:     specific_browser_types = {"calculator", "todo_app", "snake_game", "browser_game"}`
- `52:     if contract_type in specific_browser_types and planned_type in {"html_css_js_app", "html_css_js_game"}:`
- `102:         ("UI states / screens", brief.ui_states),`
- `200:     if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:`
- `205:         return ["Implement runnable Java source", "Use a public class matching the filename", "Provide clear console or desktop interactions", "Document javac/java commands"]`
- `234:     if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:`
- `255:     if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:`
- `256:         return ["start screen", "playing", "paused if supported", "game over", "restart"]`
- `264:         return ["health response", "valid endpoint response", "invalid request response", "README curl/browser example"]`
- `286:     if artifact_type in {"browser_game", "snake_game", "html_css_js_game"}:`
- `314:     if artifact_type in {"calculator", "todo_app", "browser_game", "snake_game", "generic_project", "html_css_js_app", "html_css_js_game"}:`
- `332:         return ["py -3 -m py_compile file_organiser.py", "py -3 -m pytest -q"]`

### `winlocalassistant\project_request_contract.py`

Matched: PIL, browser

- `28:     if _has_any(low, "html", "css", "javascript", "browser", "website", "web app", "game"):`
- `54:         verify_command = "python -m compileall -q winlocalassistant app.py"`
- `63:             verify_command = "python -m py_compile script.py"`

### `winlocalassistant\project_runtime_probe.py`

Matched: browser

- `39:     This is not a browser emulator. It checks whether a project has enough actual`
- `41:     manual test steps the user can run in the browser.`

### `winlocalassistant\project_type_registry.py`

Matched: browser, gui

- `9:     "python_gui_app": {"markers": ["tkinter", "mainloop"], "files": ["app.py", "README.md"]},`
- `34:     if any(term in low for term in ["markdown", "readme", "documentation", "docs"]) and not any(term in low for term in ["website", "browser", "html", "web app"]):`
- `36:     if any(term in low for term in ["json config", "json schema", "config file", "configuration file", "settings file", "settings json"]) or ("json" in low and not any(term in low for term in ["parse", "parser", "python"`
- `50:     if any(term in low for term in ["website", "html", "browser", "ui", "calculator", "todo"]):`

### `winlocalassistant\provider_runtime.py`

Matched: browser, multimodal

- `179:             "lane": "local-multimodal",`
- `184:             "best_for": "official/open local Gemma-style multimodal or reasoning model served by llama.cpp/vLLM",`
- `229:             "remote API keys live only in environment variables, never browser JavaScript or zip exports",`

### `winlocalassistant\release_hygiene.py`

Matched: PIL

- `45:                 findings.append(ReleaseHygieneFinding(rel_text, "compiled_python", "warning", "Delete compiled Python bytecode before packaging."))`

### `winlocalassistant\release_packager.py`

Matched: PIL

- `194:                     "python -m compileall -q winlocalassistant app.py",`
- `255:         "python -m compileall -q winlocalassistant app.py",`

### `winlocalassistant\release_readiness.py`

Matched: PIL, browser, gui, playwright, screen, screenshot

- `193:         guide = core.handle_command("/autonomous-guide")`
- `196:     assert "autonomous" in guide.lower(), guide[:300]`
- `197:     return "Autonomous status, stop, and guide routes responded without starting a long run."`
- `263:     game_contract = build_request_contract("make a browser game")`
- `276:     return "Strict generation contracts passed for one-file Python, browser game, PowerShell script, and Nova source-edit prompts."`
- `341: def _check_browser_runtime_contract(root: Path) -> str:`
- `342:     """Run the GUI runtime test and require fresh PASS evidence."""`
- `343:     script = root / "scripts" / "run_gui_runtime_test.py"`
- `344:     assert script.exists(), "scripts/run_gui_runtime_test.py is missing"`
- `345:     latest = root / "logs" / "gui_runtime_usability_latest.json"`
- `346:     screenshot = root / "docs" / "runtime_evidence" / "nova_runtime_usability_playwright.png"`
- `350:     out_path = logs_dir / "real_browser_gui_runtime_test.stdout.txt"`

### `winlocalassistant\remote_access.py`

Matched: PIL, gui

- `25: REMOTE_GUIDE_FILE = "NOVA_REMOTE_ACCESS_SETUP.md"`
- `30: _MAC_RE = re.compile(r"^[0-9A-Fa-f]{12}$")`
- `31: _PROFILE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,48}$")`
- `745:         "setup_guide": root_path / "docs" / REMOTE_GUIDE_FILE,`
- `803:         next_steps.append("Run /remote-access-scripts to generate the helper scripts and setup guide.")`
- `851:         "docs": str(root_path / "docs" / REMOTE_GUIDE_FILE),`
- `890:     lines.append(f"- Setup guide: `{payload.get('docs')}`")`
- `930:                     "Run `/remote-access-scripts` in Nova to write the helper launchers and setup guide.",`
- `931:                     "Start Nova locally with `START_NOVA_HERE.bat` for GUI or `start_nova_remote_api.ps1` for the optional API bridge.",`
- `1115:         "setup_guide": docs_dir / REMOTE_GUIDE_FILE,`
- `1121:     atomic_write_text(paths["setup_guide"], _setup_markdown(), encoding="utf-8")`

### `winlocalassistant\repair_engine_v2.py`

Matched: PIL, browser, console, playwright

- `6: _FAILURES = ['syntax_error','missing_file','missing_handler','wrong_domain','readme_claim_false','validation_contract_failed','local_model_json_invalid','project_path_wrong','dependency_missing','browser_runtime_error']`
- `23:       'syntax_error':['patch the smallest syntax error','run parser/compile check','run targeted tests'],`
- `32:       'browser_runtime_error':['capture console error','patch the smallest JS/UI issue','rerun Playwright or static JS check']}`

### `winlocalassistant\repo_intelligence.py`

Matched: PIL

- `156:     validation = ["python -m compileall app.py winlocalassistant", "python -m pytest -q"]`

### `winlocalassistant\repo_upgrade_assurance.py`

Matched: browser, console, gui, playwright, screen, screenshot, terminal

- `53:         "playwright_smoke": root / "playwright" / "nova_gui_smoke.spec.js",`
- `66:         "browser_gui_smoke",`
- `89:         "browser_smoke",`
- `90:         "browser_harness",`
- `115:         "/browser-smoke",`
- `150:             any(d.tool in {"command_verify", "tool_awareness_audit", "browser_smoke", "regression_sweep", "nova_doctor", "verifier_ladder", "auto_verify"} for d in plan.decisions),`
- `164:     gui_markers = ["data-orbit-studio-shell", "messageTerminalHtml", "loadActivity", "announceNovaReady", "wlaVoiceAuthorized"]`
- `165:     missing_gui = [marker for marker in gui_markers if marker not in webui_text]`
- `167:         "gui_voice_observability:markers",`
- `168:         not missing_gui,`
- `169:         "missing=" + (", ".join(missing_gui) if missing_gui else "none"),`
- `170:         "gui",`

### `winlocalassistant\response_quality.py`

Matched: gui

- `12:         "name": "OpenAI prompt engineering guidance",`
- `18:         "url": "https://platform.openai.com/docs/guides/reasoning-best-practices",`
- `22:         "name": "OpenAI structured outputs guidance",`
- `23:         "url": "https://platform.openai.com/docs/guides/structured-outputs",`

### `winlocalassistant\role_router.py`

Matched: PIL, browser

- `84:         validation = ["compile", "browser JS check", "feature continuity", "behaviour evidence"]`

### `winlocalassistant\sandbox_manager.py`

Matched: Image, PIL, console, gui, image

- `24: _SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,48}$")`
- `26:     "metasploit", "msfconsole", "msfvenom", "hydra", "john", "hashcat",`
- `38:     image: str`
- `54:         image="python:3.12-slim",`
- `61:         image="kalilinux/kali-rolling",`
- `225:         "profile_notes": {"kali": "Using wla-kali-tools:latest automatically when that local image exists."},`
- `271: def _image_exists(runtime: str, image: str) -> bool:`
- `272:     if not runtime or not image:`
- `275:         proc = subprocess.run([runtime, "image", "inspect", image], text=True, capture_output=True, timeout=8)`
- `291: def _container_image(runtime: str, name: str) -> str:`
- `295:         proc = subprocess.run([runtime, "inspect", "-f", "{{.Config.Image}}", name], text=True, capture_output=True, timeout=8)`
- `306:     If the user has built the recommended Kali tools image, prefer it so Nova`

### `winlocalassistant\scheduler_foundation.py`

Matched: PIL, browser, upload

- `18:     re.compile(pattern, re.I)`
- `35: MEDIUM_RISK_TERMS = {"download", "install", "upload", "post", "message", "browser", "external", "internet", "schedule server"}`

### `winlocalassistant\security_status.py`

Matched: Image, gui, image

- `84:         for name in ["avg", "avgui", "avgsvc", "msmpeng", "securityhealthservice", "sense", "windefend", "mbam", "crowdstrike", "sentinel", "sophos", "carbonblack"]:`
- `115:                     containers.append({"name": obj.get("Names"), "image": obj.get("Image"), "network": obj.get("Networks"), "status": obj.get("Status")})`
- `143:         "For active compromise concerns, use Windows Security/AVG quarantine features and trusted incident-response guidance rather than automated retaliation.",`
- `209:         lines.append(f"- `{c.get('name')}` image `{c.get('image')}` network `{c.get('network')}` status `{c.get('status')}`")`

### `winlocalassistant\self_awareness.py`

Matched: browser, playwright

- `145:         "Generated web apps are still checked with dependency-free probes, not full Playwright/Selenium browser automation.",`

### `winlocalassistant\self_repair_guardian.py`

Matched: PIL, gui

- `23:     [sys.executable, "-m", "compileall", "-q", "app.py", "winlocalassistant"],`
- `32:     require_compile: bool = True`
- `108:     if "syntaxerror" in low or "compile" in low:`
- `129:         recommended.append("Run command-route regression checks and add aliases before GUI/help surfaces expose a command.")`
- `131:         recommended.append("Run compileall plus targeted pytest before packaging and record the failure signature as a regression.")`
- `179:     text = "# Nova Self-Repair Policy\n\nBounded automatic self-repair is enabled for deterministic, test-backed fixes only.\n\nRules:\n- Record every failure as a mistake signature.\n- Serialize same-model Ollama calls.`

### `winlocalassistant\session_evidence.py`

Matched: browser

- `12:     "file_write", "project_open", "browser_smoke", "bug_review", "regression_sweep", "nova_doctor",`

### `winlocalassistant\skill_profiles.py`

Matched: PIL

- `65:     ("coding", ("traceback", "python", "javascript", "typescript", "powershell", "bug", "debug", "function", "class", "repo", "pytest", "compile", "api", "code", "script")),`

### `winlocalassistant\startup_validation.py`

Matched: PIL, browser

- `60:     This intentionally runs a small, high-signal validation set: compileall plus the`
- `67:     checks.append(_run(root, "compileall", [py, "-m", "compileall", "-q", "winlocalassistant", "app.py"], timeout=max(45, int(timeout))))`
- `68:     if mode not in {"compile", "compile-only", "minimal"}:`
- `108:         lines.append("Startup gate passed. Open the browser UI normally.")`
- `118:     parser = argparse.ArgumentParser(description="Run Nova startup compile/smoke validation.")`
- `119:     parser.add_argument("--mode", default="quick", choices=["quick", "compile", "compile-only", "minimal"], help="Validation depth")`

### `winlocalassistant\subagent_orchestrator.py`

Matched: PIL

- `23:     SubAgent("builder", "make the smallest verified code/project change", False, True, ["ai_create_project", "ai_edit_project", "surgical_repair"], ["compile/test before promote"]),`

### `winlocalassistant\surgical_fallback.py`

Matched: PIL

- `152:     pattern = re.compile(r"^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\b(.*[^:])\s*$")`

### `winlocalassistant\system_test.py`

Matched: PIL, console, gui, playwright

- `27:     ["tests_v55_3_46_full_validation_hardening.py", "tests_v55_3_45_console_feature_hardening.py", "tests_release_hygiene.py", "tests_report_hygiene.py"],`
- `28:     ["tests_v55_3_44_validation_feature_audit.py", "tests_v55_3_43_gui_chat_release_cleanup.py", "tests_v55_3_42_remaining_features.py", "tests_v55_3_41_defensive_validation_hardening.py"],`
- `29:     ["tests_v55_3_40_validation_cleanup.py", "tests_v55_3_39_gui_project_validation_polish.py", "tests_v55_3_37_backend_chats_release_project_memory.py", "tests_v55_3_36_audio_gui_memory.py"],`
- `48: def run_massive_system_test(root: Path | str = ".", include_docker: bool = True, include_playwright: bool = True, profile: str = "quick") -> dict[str, Any]:`
- `75:     compile_targets = ["winlocalassistant", "app.py"] + sorted({name for group in selected_groups for name in group if (audit_root / name).exists()})`
- `76:     steps.append(_run("compileall", [sys.executable, "-m", "compileall", "-q", *compile_targets], audit_root, timeout=180))`
- `100:     if include_playwright and shutil.which("npx") and (audit_root / "playwright" / "nova_gui_smoke.spec.js").exists():`
- `102:         steps.append(_run("playwright_smoke_optional", ["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"], audit_root, timeout=180))`
- `106:             steps[-1]["summary"] = "Playwright failed or Nova server unavailable; recorded as optional in massive test."`
- `108:         steps.append({"name": "playwright_optional", "ok": True, "skipped": True, "summary": "Playwright unavailable or scaffold missing"})`

### `winlocalassistant\task_decomposition.py`

Matched: gui

- `30:     ambiguity: list[str]`
- `90:     ambiguity = _ambiguities(low, subtasks)`
- `91:     confidence = _confidence(low, ambiguity, subtasks)`
- `92:     needs_clarification = confidence < 0.85 or bool(ambiguity)`
- `96:     return TaskPlan(original, normalized, len(subtasks), subtasks, plan_level, confidence, ambiguity, needs_clarification, first, criteria)`
- `128: def _ambiguities(low: str, subtasks: list[Subtask]) -> list[str]:`
- `139: def _confidence(low: str, ambiguity: list[str], subtasks: list[Subtask]) -> float:`
- `141:     score -= 0.18 * len(ambiguity)`

### `winlocalassistant\task_execution.py`

Matched: PIL, browser

- `75:     if low.startswith("/verify") or low.startswith("verify ") or "test" in low or "compile" in low:`
- `83:     if _has_any(low, "browser game", "make a game", "build an app", "create a project"):`
- `113:             "run focused tests/compile checks for the touched area",`
- `147:             "python -m compileall -q winlocalassistant app.py scripts",`
- `153:             "python -m compileall -q winlocalassistant app.py scripts",`
- `158:         verification = [re.sub(r"^/?verify\s+", "", text, flags=re.I).strip() or "python -m compileall -q winlocalassistant app.py"]`
- `460:         "syntax_compile_status": "not run by summary" if not full else "run through release-readiness when requested",`
- `475:         f"Syntax/compile status: {payload.get('syntax_compile_status')}",`

### `winlocalassistant\tools.py`

Matched: Image, PIL, browser, console, gui, image, llama3.2-vision, playwright, screen, screenshot, terminal, upload, vision

- `38: from .ollama import ollama_busy_state, ollama_vision_chat`
- `43: from .tool_guides import get_local_model_tool_use_summary`
- `44: from .file_context import IMAGE_EXTS, resolve_image_context`
- `45: from .image_generation import build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status`
- `51: from .nova_video import write_storyboard_svg, write_shotlist_csv, build_video_image_prompt_plan, write_video_render_package, render_video_render_package_markdown, media_status_summary`
- `78: from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation`
- `103:     build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,`
- `105:     patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,`
- `125: from .jarvis_bridge import build_capability_map, probe_jarvis_daemon, update_bridge_policy, queue_proactive_action, list_queued_actions, render_bridge_markdown, build_jarvis_setup_doctor, build_sidecar_preflight, build_a`
- `225: from .browser_worker import build_browser_task_plan, render_browser_task_plan`
- `280:         "open the browser",`
- `281:         "browser checks",`

### `winlocalassistant\tool_catalog.py`

Matched: PIL, terminal

- `32:     ToolCatalogEntry("self_improve", "Manual guarded Nova source improvement", "high", True, ["backup", "diff", "py_compile", "smoke tests", "rollback"], ["rollback", "surgical fallback"], ["automatic idle/autonomous inv`
- `40:     ToolCatalogEntry("sandbox_exec", "Run a policy-checked command inside an existing disposable sandbox", "medium", True, ["stdout/stderr", "return code", "audit log"], ["sandbox_status", "manual terminal"], ["host-cont`

### `winlocalassistant\tool_guides.py`

Matched: PIL, browser, gui

- `18: Tool selection: use /idle once and /idle propose for safe diagnostics, /tool-guide for command knowledge, project tools for user artifacts, and /self-improve only when a human explicitly sends it.`
- `19: Verification ladder: py_compile or syntax check, smoke tests, targeted pytest/project checks, final requirement check, and manual/browser review where relevant.`

### `winlocalassistant\tool_orchestrator.py`

Matched: browser, gui

- `64:         "browser_harness": "browser_harness",`
- `65:         "node": "browser_smoke",`
- `66:         "node_check": "browser_smoke",`
- `108:     - autonomy capability matches (when/how/validation guidance), and`

### `winlocalassistant\upgrade_planner.py`

Matched: Image, PIL, browser, gui, image, playwright

- `46:         benefit="Lets Bluetooth/Sony headset users select a browser-visible input device instead of relying on the Windows default mic.",`
- `49:         check="Browser getUserMedia + enumerateDevices",`
- `58:         benefit="Lets Nova install reviewed optional dev tools such as Ruff, pre-commit or Playwright only after an explicit --confirm, then records install/check reports.",`
- `67:         name="Playwright GUI smoke tests",`
- `68:         status="ready" if (root / "playwright" / "nova_gui_smoke.spec.js").exists() else "missing scaffold",`
- `70:         benefit="Catches send-button, microphone button, live activity, and layout regressions in a real browser.",`
- `73:         check="npx playwright test playwright/nova_gui_smoke.spec.js",`
- `74:         install_hint="npm install -D @playwright/test && npx playwright install chromium",`
- `75:         command="/playwright-smoke-help",`
- `106:         benefit="Runs compile, tests and lint checks consistently before a zip is shared.",`
- `127:         name="Optional local image backend",`
- `130:         benefit="Could enable local image experiments, but it is heavy and should stay optional on GTX 1650-class machines.",`

### `winlocalassistant\user_testing.py`

Matched: PIL, gui

- `11: from .gui_redesign import build_gui_feature_map, gui_regression_check`
- `13: from .prompt_test_compiler import build_prompt_contract`
- `108:     fmap = build_gui_feature_map(root)`
- `109:     missing_gui = [item for item in fmap.get("features", []) if not item.get("ok", item.get("present", False))]`
- `110:     checks.append(UserTestCheck("gui_feature_map", not missing_gui, "GUI feature map has no missing required features" if not missing_gui else f"{len(missing_gui)} GUI feature(s) missing", "high" if missing_gui else "inf`
- `112:     gui_reg = gui_regression_check(root)`
- `113:     checks.append(UserTestCheck("gui_regression", bool(gui_reg.get("ok", True)), str(gui_reg.get("summary", "GUI regression check completed")), "high" if not gui_reg.get("ok", True) else "info", gui_reg))`
- `146:     lines += ["", "## Recommended follow-up", "- If any high/critical item fails, run `/weakspot-audit`, `/nova-mega-test --confirm`, and the named command area before packaging.", "- For user-flow issues, run `/prompt-c`

### `winlocalassistant\validate.py`

Matched: PIL, browser, gui

- `299:     required = ["v55.3.164", "populateSpecChoices", "safeApplyUiSettings", "/video-plan", "/media-status", "/video-package", "focus-workspace", "/nova-efficiency-audit", "qwen3-coder:30b", "natural-research-routing", "/p`
- `319:     compile_result = run_section("compileall", [sys.executable, "-m", "compileall", "app.py", "nova", "winlocalassistant"], timeout=300)`
- `320:     add("compileall", compile_result.get("ok"), compile_result)`
- `338:         "tests_nova_clean_gui_docker_v55_3_159.py",`
- `346:         "tests_nova_gui_startup_routes_v55_3_161.py",`
- `349:         "tests_gui_ai_help_overlay.py",`
- `350:         "tests_gui_cyberpunk_theme.py",`
- `351:         "tests_gui_interaction_overhaul.py",`
- `381:     add("gui_smoke", web.get("ok"), web)`
- `384:     add("browser_worker_fixture", (root / "winlocalassistant" / "browser_worker.py").exists())`
- `396:         "note": "Layered validation: environment, imports, compile, targeted tests, version sync, launchers, CLI/web smoke, worker surfaces and package/license surface. Progress is written to logs/validation_progress.jso`
- `441:     GUI/CLI can still report the last known validation stage after a crash,`

### `winlocalassistant\validation_matrix.py`

Matched: PIL, browser, screen

- `13: def _compile_python(root: Path) -> dict[str, Any]:`
- `18:         proc = subprocess.run([sys.executable, "-m", "compileall", "-q", *targets], cwd=root, capture_output=True, text=True, timeout=60)`
- `19:         return {"name": "python_compile", "ok": proc.returncode == 0, "detail": (proc.stdout + proc.stderr)[-2000:] or "compileall passed"}`
- `21:         return {"name": "python_compile", "ok": False, "detail": repr(exc)}`
- `51:         "browser-harness",`
- `68:         "voiceScreenTranscript",`
- `82:     return {"name": "webui_contract", "ok": not missing, "detail": "missing: " + ", ".join(missing) if missing else "critical browser/UI markers present"}`
- `88:     checks.append(_compile_python(root))`
- `93:         bridge_markers = ["probe_jarvis_daemon", "queue_proactive_action", "update_bridge_policy", "build_jarvis_setup_doctor", "build_sidecar_preflight", "build_workflow_blueprint", "build_bridge_receipts", "build_sidec`

### `winlocalassistant\visual_regression.py`

Matched: browser, gui, playwright, screen, screenshot

- `7: def build_gui_snapshot_status(root: Path) -> dict[str, Any]:`
- `8:     playwright = root / "playwright" / "nova_gui_smoke.spec.js"`
- `10:     return {"ok": playwright.exists(), "playwright_spec": str(playwright), "npx_available": has_npx, "command": "npx playwright test playwright/nova_gui_smoke.spec.js", "snapshot_command": "npx playwright test --update-s`
- `13: def render_gui_snapshot_status(payload: dict[str, Any]) -> str:`
- `14:     lines = ["# GUI Visual Regression Gate", "", f"Spec present: **{payload.get('ok')}**", f"npx available: **{payload.get('npx_available')}**", f"Smoke command: `{payload.get('command')}`", f"Snapshot update command: `{`

### `winlocalassistant\weakspot_audit.py`

Matched: PIL

- `53:             issues.append(_issue("warning", "release_hygiene", rel, "Compiled Python artifact present in working tree.", "Run /release-hygiene clean before packaging."))`

### `winlocalassistant\webui.py`

Matched: Image, PIL, attachment, browser, clipboard, console, gui, image, llama3.2-vision, playwright, screen, screenshot, terminal, upload, vision

- `14: from .file_context import MAX_UPLOAD_BYTES, register_uploaded_file, list_file_contexts, clear_file_contexts`
- `22: from .webui_layout_overhaul import apply_gui_layout_overhaul`
- `160:     "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml", "purpose": "any maskable"}],`
- `162:         {"name": "Workbench", "short_name": "Workbench", "url": "/odysseus-workbench", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},`
- `163:         {"name": "Odysseus Runtime", "short_name": "Runtime", "url": "/odysseus-runtime", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},`
- `164:         {"name": "Research", "short_name": "Research", "url": "/odysseus-research", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},`
- `165:         {"name": "Uploads", "short_name": "Uploads", "url": "/odysseus-uploads", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},`
- `166:         {"name": "Code", "short_name": "Code", "url": "/odysseus-code", "icons": [{"src": "/pwa-icon.svg", "sizes": "any", "type": "image/svg+xml"}]},`
- `181:   '/odysseus-uploads',`
- `222: <link rel="icon" href="/pwa-icon.svg" type="image/svg+xml">`
- `230: .composer{padding:10px;border-top:1px solid var(--line);background:white}.artifact{border-top:1px solid var(--line);background:#f8fbff;padding:10px 14px;font-size:13px}.artifact a{font-weight:900;color:var(--blue);margin`
- `243: /* v55.3.115 GUI cockpit overhaul: three-zone layout, workflow cards, clearer panels and durable run management. */`

### `winlocalassistant\webui_ai_help_overlay.py`

Matched: clipboard, gui

- `11: /* v55.3.164 AI contextual help overlay: tiny semi-transparent guide symbols. */`
- `64: window.NovaGuiAiHelp = window.NovaGuiAiHelp || {version:'v55.3.164-ai-context-help-v1', enabled:true};`
- `91:     try{return encodeURIComponent(JSON.stringify(ctx));}catch(e){return encodeURIComponent(String(ctx.label||'GUI element'));}`
- `109:       '<h3>AI help: '+esc(ctx.label||'GUI element')+'</h3>'+`
- `110:       '<div class="small">Tiny contextual help for the selected Nova GUI element. It can explain the control or ask Nova to plan how to use/build with it.</div>'+`
- `113:       '<button onclick="quick(\'/gui-ai-help '+encoded+'\')">Explain this</button>'+`
- `114:       '<button onclick="quick(\'/tool-use-plan use this GUI element: '+escAttr(ctx.label||'element')+'\')">AI plan</button>'+`
- `115:       '<button onclick="quick(\'/pipeline-route use this GUI element: '+escAttr(ctx.label||'element')+'\')">Pipeline</button>'+`
- `116:       '<button onclick="quick(\'/role-router use this GUI element: '+escAttr(ctx.label||'element')+'\')">Role</button>'+`
- `117:       '<button onclick="navigator.clipboard&&navigator.clipboard.writeText('+JSON.stringify(JSON.stringify(ctx))+')">Copy context</button>'+`
- `148:       window.NovaGuiAiHelp.count=document.querySelectorAll('.novaAiHelpDot').length;`
- `149:     }catch(e){window.NovaGuiAiHelp.error=String(e);}  `

### `winlocalassistant\webui_arcade.py`

Matched: browser, gui

- `3: """Local-only Nova Arcade GUI runtime.`
- `5: The arcade is component-style: a registry describes games, and the browser`
- `32:   function open(){const ov=ensureOverlay();ov.style.display='flex';ov.innerHTML='<div id="novaArcadePanel"><div class="novaArcadeHeader"><h2>Nova Arcade</h2><div class="row wrap"><button type="button" onclick="NovaArcade`

### `winlocalassistant\webui_cyberpunk_theme.py`

Matched: gui, screen

- `10: /* v55.3.164 cyberpunk GUI makeover v1: neon yellow/cyan/magenta shell with angular chrome. */`
- `31:   opacity:.42;mix-blend-mode:screen;`
- `185: window.NovaCyberpunkTheme = window.NovaCyberpunkTheme || {theme:'cyberpunk2077-nova-v1', patchId:'cyberpunk2077-gui-makeover-v1'};`
- `223:     if 'cyberpunk GUI makeover v1' not in html:`

### `winlocalassistant\webui_emergency_stability.py`

Matched: gui, screen, screenshot

- `5: This layer fixes the product-breaking issues seen in real user screenshots/logs:`
- `195:     ['Code','/code QUESTION','Ask for coding/debugging guidance without creating a project.','/code explain how to run a Python file'],`
- `203:     ['Layout','/gui-layout-status','Check GUI layout markers and runtime diagnostics.','/gui-layout-status'],`
- `211:   function showHelp(){let ov=document.getElementById('novaHelpHubOverlay');if(!ov){ov=document.createElement('div');ov.id='novaHelpHubOverlay';ov.className='novaHelpHubOverlay';document.body.appendChild(ov);}const cards=`
- `218:   function addPanic(){if(document.getElementById('novaPanicReset'))return;const b=document.createElement('button');b.id='novaPanicReset';b.className='novaPanicReset tiny secondary';b.type='button';b.textContent='fix UI';`
- `219:   function diagnose(){const composer=document.querySelector('.composer');const activity=document.getElementById('liveActivityPanel')||document.querySelector('.activity');const chat=document.getElementById('chat');functio`
- `220:   function init(){document.body.classList.add('nova-emergency-stability-v1');addButton('novaHelpHubButton','help hub',showHelp);addPanic();patchDrawer();minimizeActivityOnStartup();setTimeout(()=>{patchDrawer();if(window`

### `winlocalassistant\webui_interaction_overhaul.py`

Matched: browser, clipboard, console, gui

- `7: """GUI interaction fixes for Nova.`
- `9: This layer is browser/UI-only. It fixes panel stacking, help dots, live activity`
- `63: window.NovaInteractionOverhaul = window.NovaInteractionOverhaul || {version:'v55.3.164-interaction-overhaul-v1', patchId:'gui-autonomous-interaction-fix-v1'};`
- `67:   function postCommand(cmd){try{const msg=document.getElementById('msg'); if(msg){msg.value=cmd;} if(typeof send==='function') return send(); return fetch('/chat',{method:'POST',headers:{'Content-Type':'application/json'`
- `69:   function ensureStatusBoxes(){const target=document.querySelector('#orbitNav,.sidebar.card,.rightbar.card,#orbitRightDrawer .orbitDrawerBody')||document.body;if(!document.getElementById('novaMicListenerStatus')){const b`
- `70:   function updateMicStatus(){const box=document.getElementById('novaMicListenerStatus'); if(!box)return;let state='unavailable', detail='Browser has not granted microphone access or devices cannot be enumerated.';try{con`
- `73:   function enhanceCodeBlocks(){document.querySelectorAll('.bubble pre.codeblock:not([data-codebox-ready="1"]),.bubble pre.jsonblock:not([data-codebox-ready="1"])').forEach(pre=>{pre.dataset.codeboxReady='1';const wrapper`
- `78:   function commandHelp(){let ov=document.getElementById('novaCommandHelpOverlay'); if(!ov){ov=document.createElement('div');ov.id='novaCommandHelpOverlay';ov.className='novaCommandHelpOverlay';document.body.appendChild(o`
- `80:   async function updateAutonomousGuard(){let ov=document.getElementById('novaAutonomousGuardOverlay'); if(!ov){ov=document.createElement('div');ov.id='novaAutonomousGuardOverlay';ov.className='novaAutonomousGuardOverlay'`
- `82:   window.NovaInteractionOverhaul={version:'v55.3.164-interaction-overhaul-v1',patchId:'gui-autonomous-interaction-fix-v1',commandHelp,filterCommandHelp,useCommand:postCommand,updateModelMini,updateMicStatus,addMessageNav`

### `winlocalassistant\webui_layout_overhaul.py`

Matched: gui

- `5: Legacy compatibility marker retained: gui-overhaul-v4-wide-left-rail.`
- `9: layout fixes live here so future humans/agents can adjust the GUI without`
- `13: GUI_LAYOUT_OVERHAUL_CSS = r"""`
- `14: /* v55.3.164 GUI layout overhaul v4: wide readable left rail + drawer/chat split, no drawer rail overlap, no ghost right panel. */`
- `15: body.nova-orbit-shell.gui-overhaul-v3{`
- `25: body.nova-orbit-shell.gui-overhaul-v3 main[data-ui-overhaul]{`
- `34: body.nova-orbit-shell.gui-overhaul-v3 .sidebar.card{`
- `44: body.nova-orbit-shell.gui-overhaul-v3 #orbitNav{`
- `53: body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton{`
- `64: body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton .label{`
- `74: body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton .plus,`
- `75: body.nova-orbit-shell.gui-overhaul-v3 #orbitNav .orbitNavButton small{`

### `winlocalassistant\whole_codebase_review.py`

Matched: PIL, gui

- `149:             "why": "Allows `python app.py /nova-mega-test --confirm` and other copy/paste diagnostics without opening the GUI.",`
- `229:     lines += ["", "## Recommended validation ladder", "- python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py", "- python tests_smoke.py", "- /nova-mega-test --confirm", "- /release-h`

### `winlocalassistant\wla_doctor.py`

Matched: Image, PIL, browser, console, gui, image, playwright

- `34:     "/security-watch", "/image-setup-help", "/project-target", "/chat-rename", "/chat-delete",`
- `259: def _playwright_available(root: Path) -> bool:`
- `260:     spec = root / "playwright" / "nova_gui_smoke.spec.js"`
- `275:     compileall, and a compact regression set. Docker validation remains a`
- `276:     separate optional gate because Docker may not be installed or the image may`
- `282:     commands.append(_run_gate_command("compileall", [sys.executable, "-m", "compileall", "-q", "winlocalassistant", "app.py"], timeout=180, cwd=root))`
- `287:         "tests_v55_3_45_console_feature_hardening.py",`
- `289:         "tests_v55_3_43_gui_chat_release_cleanup.py",`
- `304:     # Optional browser UI gate: run only when Playwright tooling is installed and`
- `307:     if _playwright_available(root) and _server_reachable():`
- `308:         commands.append(_run_gate_command("playwright_smoke", ["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"], timeout=180, cwd=root))`
- `310:         commands.append({"name": "playwright_smoke", "ok": True, "skipped": True, "summary": "Skipped because Playwright is unavailable or Nova server is not reachable at http://127.0.0.1:8766", "command": ["npx", "playw`

### `winlocalassistant\wla_mega_test.py`

Matched: PIL, browser, gui

- `8: from .gui_redesign import build_gui_feature_map, render_gui_feature_map, gui_regression_check, render_gui_regression`
- `11: from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status`
- `13: from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation`
- `26:     build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,`
- `28:     patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,`
- `52:     fmap = build_gui_feature_map(root)`
- `53:     add("gui_feature_map", fmap.get("ok", False), render_gui_feature_map(fmap))`
- `54:     greg = gui_regression_check(root)`
- `55:     add("gui_regression", greg.get("ok", False), render_gui_regression(greg))`
- `56:     snap = build_gui_snapshot_status(root)`
- `57:     add("gui_visual_gate", bool(snap.get("ok")), render_gui_snapshot_status(snap))`
- `80:     add("browser_runtime_tester", True, render_browser_runtime(build_browser_runtime_test(root, goal)))`

### `winlocalassistant\__init__.py`

Matched: browser, gui

- `3: VERSION_LABEL = 'v55.3.168 project-state continuity memory | preserves v55.3.167 task execution evidence/autonomy hardening | preserves v55.3.166 LLM-from-scratch inspired training lab | preserves v55.3.165 real-machine `

### `.nova_runtime\playwright\KNOWLEDGE_BASE.md`

Matched: PIL, browser

- `10: For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include vi`
- `29: - Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.`
- `34: - Run `python -m py_compile file.py` for syntax.`

### `.nova_runtime\release_readiness\chat_fallback_status\KNOWLEDGE_BASE.md`

Matched: PIL, browser

- `10: For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include vi`
- `29: - Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.`
- `34: - Run `python -m py_compile file.py` for syntax.`

### `.nova_runtime\release_readiness\command_help_status\KNOWLEDGE_BASE.md`

Matched: PIL, browser

- `10: For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include vi`
- `29: - Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.`
- `34: - Run `python -m py_compile file.py` for syntax.`

### `.nova_runtime\release_readiness\model_health_and_host_calibration_status\KNOWLEDGE_BASE.md`

Matched: PIL, browser

- `10: For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include vi`
- `29: - Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.`
- `34: - Run `python -m py_compile file.py` for syntax.`

### `.nova_runtime\release_readiness\real_browser_gui_runtime_test\KNOWLEDGE_BASE.md`

Matched: PIL, browser

- `10: For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include vi`
- `29: - Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.`
- `34: - Run `python -m py_compile file.py` for syntax.`

### `.nova_runtime\release_readiness\write_read_verify_code_do_status\KNOWLEDGE_BASE.md`

Matched: PIL, browser

- `10: For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include vi`
- `29: - Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.`
- `34: - Run `python -m py_compile file.py` for syntax.`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_010230.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `54: nova_vision_verify.png`
- `57: playwright`
- `58: playwright.config.js`
- `118: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `119: tests_gui_ai_help_overlay.py`
- `120: tests_gui_cyberpunk_theme.py`
- `121: tests_gui_interaction_overhaul.py`
- `122: tests_gui_layout_v55_3_18.py`
- `125: tests_image_generation_backend.py`
- `140: tests_nova_clean_gui_docker_v55_3_159.py`
- `147: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `148: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_011020.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_011126.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `54: nova_vision_verify.png`
- `57: playwright`
- `58: playwright.config.js`
- `118: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `119: tests_gui_ai_help_overlay.py`
- `120: tests_gui_cyberpunk_theme.py`
- `121: tests_gui_interaction_overhaul.py`
- `122: tests_gui_layout_v55_3_18.py`
- `125: tests_image_generation_backend.py`
- `140: tests_nova_clean_gui_docker_v55_3_159.py`
- `147: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `148: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_012229.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_012321.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `54: nova_vision_verify.png`
- `57: playwright`
- `58: playwright.config.js`
- `118: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `119: tests_gui_ai_help_overlay.py`
- `120: tests_gui_cyberpunk_theme.py`
- `121: tests_gui_interaction_overhaul.py`
- `122: tests_gui_layout_v55_3_18.py`
- `125: tests_image_generation_backend.py`
- `140: tests_nova_clean_gui_docker_v55_3_159.py`
- `147: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `148: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_013228.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_013313.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `54: nova_vision_verify.png`
- `57: playwright`
- `58: playwright.config.js`
- `118: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `119: tests_gui_ai_help_overlay.py`
- `120: tests_gui_cyberpunk_theme.py`
- `121: tests_gui_interaction_overhaul.py`
- `122: tests_gui_layout_v55_3_18.py`
- `125: tests_image_generation_backend.py`
- `140: tests_nova_clean_gui_docker_v55_3_159.py`
- `147: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `148: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_014241.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `54: nova_vision_verify.png`
- `57: playwright`
- `58: playwright.config.js`
- `118: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `119: tests_gui_ai_help_overlay.py`
- `120: tests_gui_cyberpunk_theme.py`
- `121: tests_gui_interaction_overhaul.py`
- `122: tests_gui_layout_v55_3_18.py`
- `125: tests_image_generation_backend.py`
- `140: tests_nova_clean_gui_docker_v55_3_159.py`
- `147: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `148: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_014645.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_015042.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_015455.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\context\NOVA_CODE_RADAR_20260610_015618.md`

Matched: Image, PIL, browser, console, gui, image, playwright, screen, vision

- `55: nova_vision_verify.png`
- `58: playwright`
- `59: playwright.config.js`
- `119: tests_gui_activity_autonomous_sandbox_v55_3_19.py`
- `120: tests_gui_ai_help_overlay.py`
- `121: tests_gui_cyberpunk_theme.py`
- `122: tests_gui_interaction_overhaul.py`
- `123: tests_gui_layout_v55_3_18.py`
- `126: tests_image_generation_backend.py`
- `141: tests_nova_clean_gui_docker_v55_3_159.py`
- `148: tests_nova_fastapi_gui_adaptation_v55_3_137.py`
- `149: tests_nova_gui_startup_routes_v55_3_161.py`

### `local_ai_cycles\memory\LAST_TEST_RESULTS.md`

Matched: PIL

- `3: >>> python -m compileall -q app.py winlocalassistant nova`

### `local_ai_cycles\memory\NOVA_IDEA_PROMOTION_TASK_DRAFT_LATEST.md`

Matched: gui

- `16:         Goal = "Promote the next fresh JSON-drafted Nova task into one tiny source+test improvement. Add render_status_counts_line(items: Iterable[WorkItem]) -> str to nova_improvement_lab\autodev_sandbox.py. It must sum`

### `local_ai_cycles\memory\NOVA_LOOP_SUMMARY_LATEST.md`

Matched: Image, PIL, console, gui, image, llama3.2-vision, screen, screenshot, terminal, vision

- `10: - compile checks must pass`
- `18: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `32: Detected Ollama models: gpt-oss:20b, gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b`
- `39: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `41: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `43: Terminal does not support pretty output (UnicodeDecodeError)`
- `150: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `151:     suggestions = suggest_next_commands("gui is broken, blank drawer panel in screenshot")`
- `153:     assert "/gui-visual-test" in commands`
- `158:     commands = _commands("make a video trailer and image storyboard")`
- `160:     assert any(cmd.startswith("/image-plan") or cmd.startswith("/video-package") for cmd in commands)`
- `182: >>> python -m compileall -q app.py winlocalassistant nova`

### `local_ai_cycles\memory\NOVA_SIGNIFICANCE_SUMMARY_LATEST.md`

Matched: Image, console, gui, image, llama3.2-vision, screen, screenshot, terminal, vision

- `9: Detected Ollama models: gpt-oss:20b, gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b`
- `16: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `18: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `20: Terminal does not support pretty output (UnicodeDecodeError)`
- `125: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `126:     suggestions = suggest_next_commands("gui is broken, blank drawer panel in screenshot")`
- `128:     assert "/gui-visual-test" in commands`
- `133:     commands = _commands("make a video trailer and image storyboard")`
- `135:     assert any(cmd.startswith("/image-plan") or cmd.startswith("/video-package") for cmd in commands)`
- `162: Detected Ollama models: gpt-oss:20b, gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b`
- `169: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `171: Can't initialize prompt toolkit: No Windows console found. Are you running `

### `local_ai_cycles\memory\NOVA_TASK_IDEA_POOL_LATEST.md`

Matched: gui

- `12: - Avoid documentation-only, test-only, speculative, or GUI redesign tasks.`

### `local_ai_cycles\memory\NOVA_TASK_LOOP_SUMMARY_LATEST.md`

Matched: PIL, gui

- `38: >>> python -m compileall -q app.py winlocalassistant nova nova_improvement_lab tests_nova_user_sanity.py`
- `74: - fresh-model-health-guidance: score=0, state=eligible, reasons=source+test candidate; 2 recent low-value/no-change outcome(s); 2 recent no-change outcome(s); category=no-change`

### `local_ai_cycles\memory\NO_CHANGE_TARGETS.md`

Matched: gui

- `66: 2026-06-10T15:04:14 task=fresh-model-health-guidance category=no-change reason=no-change structured_event=1`
- `73: 2026-06-10T19:13:59 task=fresh-model-health-guidance category=no-change reason=no-change structured_event=1`

### `local_ai_cycles\memory\RELIABILITY_GATE_20260610_025143.md`

Matched: Image, PIL, console, gui, image, llama3.2-vision, screen, screenshot, terminal, vision

- `10: - compile checks must pass`
- `18: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `32: Detected Ollama models: gpt-oss:20b, gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b`
- `39: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `41: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `43: Terminal does not support pretty output (UnicodeDecodeError)`
- `150: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `151:     suggestions = suggest_next_commands("gui is broken, blank drawer panel in screenshot")`
- `153:     assert "/gui-visual-test" in commands`
- `158:     commands = _commands("make a video trailer and image storyboard")`
- `160:     assert any(cmd.startswith("/image-plan") or cmd.startswith("/video-package") for cmd in commands)`
- `182: >>> python -m compileall -q app.py winlocalassistant nova`

### `local_ai_cycles\memory\SIGNIFICANCE_GATE_20260610_025602.md`

Matched: Image, console, gui, image, llama3.2-vision, screen, screenshot, terminal, vision

- `9: Detected Ollama models: gpt-oss:20b, gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b`
- `16: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `18: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `20: Terminal does not support pretty output (UnicodeDecodeError)`
- `125: def test_gui_problem_suggests_adaptive_gui_checks() -> None:`
- `126:     suggestions = suggest_next_commands("gui is broken, blank drawer panel in screenshot")`
- `128:     assert "/gui-visual-test" in commands`
- `133:     commands = _commands("make a video trailer and image storyboard")`
- `135:     assert any(cmd.startswith("/image-plan") or cmd.startswith("/video-package") for cmd in commands)`
- `162: Detected Ollama models: gpt-oss:20b, gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b`
- `169: Can't initialize prompt toolkit: No Windows console found. Are you running `
- `171: Can't initialize prompt toolkit: No Windows console found. Are you running `

### `local_ai_cycles\memory\TASK_LOOP_MEMORY.md`

Matched: PIL, gui

- `7: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `22: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `32: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `62: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `72: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `89: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `115: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `134: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `153: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `179: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `189: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`
- `222: >>> python -m compileall -q app.py winlocalassistant nova tests_nova_user_sanity.py`

### `test-results\playwright-nova_runtime_us-980b0-ivity-cannot-cover-composer\error-context.md`

Matched: Image, browser, gui, image, playwright, screen, screenshot

- `3: - Following Playwright test failed.`
- `4: - Explain why, be concise, respect Playwright best practices.`
- `9: - Name: playwright/nova_runtime_usability.spec.js >> chat help drawers activity cannot cover composer`
- `10: - Location: playwright/nova_runtime_usability.spec.js:25:1`
- `136:           - button "layout AI help for Check visible GUI drawer/chat geometry" [ref=e90] [cursor=pointer]:`
- `138:             - button "AI help for Check visible GUI drawer/chat geometry" [ref=e91]: "? ?"`
- `139:           - button "reset UI AI help for Reset drawer/chat layout state and clear stale Nova browser cache/service worker without deleting project data" [ref=e92] [cursor=pointer]:`
- `141:             - button "AI help for Reset drawer/chat layout state and clear stale Nova browser cache/service worker without deleting project data" [ref=e93]: "? ?"`
- `168:           - paragraph [ref=e113]: Local AI workspace. Chat stays centred; projects, tools, voice, activity and output open as drawers instead of covering the whole screen.`
- `179:           - textbox "Ask Nova, attach files with +, or choose a mode such as research, image, Linux sandbox, or autonomous build." [active] [ref=e123]: hi`
- `250:             - button "Playwright scaffold"`
- `272:             - button "Browser harness"`

## Recommended implementation plan

1. Add a small pure module for screen-analysis request classification.
2. Add tests proving when Nova should ask for/accept a screenshot.
3. Add a vision prompt builder for screenshots, terminal images, GUI images, and browser layout images.
4. Wire into GUI/terminal flows only after tests pass.
5. Use local vision models when available, such as detected Ollama vision models, but keep graceful fallback text-only behaviour.
