# Nova Mega Test

Overall: **PASS**
Passed: 38/38
Duration: 2.848 sec
Copy/paste command: `/nova-mega-test --confirm`

## Sections
- ✅ dependency_check
- ✅ release_hygiene
- ✅ feature_audit
- ✅ gui_feature_map
- ✅ gui_regression
- ✅ gui_visual_gate
- ✅ blueprint_engine
- ✅ candidate_engine
- ✅ trace_cockpit
- ✅ mcp_manifest
- ✅ prompt_contract
- ✅ contract_validation
- ✅ candidate_tournament
- ✅ surgical_repair_v2
- ✅ mcp_security
- ✅ mission_planner
- ✅ model_output_coach
- ✅ environment_profile
- ✅ new_pc_benchmark
- ✅ project_state
- ✅ regression_memory
- ✅ build_quality_v3
- ✅ browser_runtime_tester
- ✅ model_reliability_controller
- ✅ model_requirement_download_planner
- ✅ model_fallback_strategy
- ✅ patch_queue
- ✅ gui_cockpit_v2
- ✅ voice_mode_upgrade
- ✅ template_builder
- ✅ preview_server
- ✅ feature_readiness
- ✅ error_translator
- ✅ support_report
- ✅ docs_index
- ✅ regression_test_generator
- ✅ mistake_learning
- ✅ interaction_flow_audit

## Details

### dependency_check
Nova Dependency Check

Python: 3.12.10 (ok)

Python packages
- PASS pytest (required) — run Nova regression and release tests
- MISSING pillow (optional) — image utilities and future real image outputs

External tools
- PASS git — git version 2.54.0.windows.1 — patch validation/promotion and project diff review
- PASS node — v24.16.0 — web UI JavaScript parsing and generated JS checks
- PASS npm — 11.13.0 — Playwright browser smoke tests
- PASS docker — Docker version 29.5.2, build 79eb04c — Docker sandbox and copied-workspace validation
- PASS ollama — ollama version is 0.30.7 — local LLM chat and code generation

### release_hygiene
# Nova Release Hygiene

Overall: **PASS**
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Summary: Release hygiene passed

No cache, bytecode or runtime-state artifacts were detected in the release tree.

### feature_audit
# Nova Requested Feature Audit

OK: **True**
Summary: Requested-feature audit passed
Implemented: **15**
Partial/environment-dependent: **1**
Missing: **0**

## Feature checks
- ✅ **spoken_audio_and_controls** — implemented: Browser speech, microphone voice input, microphone diagnostic preflight, long-response summarisation, mute/unmute and tutorial controls are wired in the GUI.
- ✅ **thin_left_rail_popups** — implemented: Left rail contains settings/audio/tutorial/changelog/release/chat shortcuts with popup panels.
- ✅ **custom_quick_commands** — implemented: Quick commands are flat, customisable, persistent and can execute sequential command lists.
- ✅ **live_activity_clarity** — implemented: Live Activity is taller/resizable, keeps previous runs, shows hover metadata and indented/subtask context.
- ✅ **backend_conversations** — implemented: Persistent backend conversations support create/list/switch/search/rename/delete.
- ✅ **project_memory_and_targeting** — implemented: Project memory is retrieved for build/edit prompts and project targeting can diagnose new-vs-current project intent.
- ✅ **file_cards_and_llm_context** — implemented: Generated/openable files appear as cards and the LLM status panel preserves compact recent prompt/reply context.
- ✅ **research_synthesis** — implemented: Research reports include a short synthesis plus source/excerpt/bias sections.
- ✅ **docker_validation_patch_promotion** — implemented: Docker copied-workspace validation, patch validation, hash locking and promotion rollback logic are present.
- ✅ **release_gate_and_doctor** — implemented: Nova Doctor, release gate and release checklist commands are present.
- ✅ **playwright_scaffold** — implemented: Playwright GUI smoke scaffold exists and release gate runs/skips it depending on environment readiness.
- ✅ **security_defensive_watch** — implemented: Defensive-only security status and watch commands are wired; direct vendor remediation remains intentionally manual/user-approved.
  - Remaining: Direct AVG quarantine/remediation requires documented vendor CLI/API and explicit approval.
- 🟡 **image_generation_status** — environment_dependent: Image generation refuses to fake real generation and provides setup guidance for SD WebUI/Diffusers/ComfyUI.
  - Remaining: Actual generation depends on a reachable/configured local image backend.
- ✅ **browser_console_hygiene** — implemented: The web UI avoids favicon 404 noise, avoids Web Audio before a user gesture, preserves LLM context text while refreshing, and supports multi-command quick buttons.
- ✅ **dependency_and_massive_system_test** — implemented: Startup dependency checks, optional pip install prompts, and one-click confirmed massive system tests are wired.
- ✅ **linux_sandbox_python_ready** — implemented: General Linux sandbox defaults to a Python-ready image and aliases python3 where possible.

## Remaining environment-dependent / approval-only work
- Direct AVG quarantine/remediation requires documented vendor CLI/API and explicit approval.
- Actual generation depends on a reachable/configured local image backend.

Report written: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\docs\NOVA_FEATURE_AUDIT_LATEST.md`

### gui_feature_map
# GUI Feature Map

Overall: **PASS**
Recommendation: Keep classic UI as default; add cockpit-preview behind /gui-mode cockpit until feature-map and visual tests pass.

## Feature coverage
- ✅ **Chat composer** — hits: Ask Nova, Send, attach
- ✅ **Voice controls** — hits: Mic test, Refresh mics, voice
- ✅ **Projects/files** — hits: Projects, Files, Zip project
- ✅ **Live Activity** — hits: Live activity, Current task
- ✅ **Model status** — hits: Local LLM status, LLM status
- ✅ **Sandbox/Docker** — hits: Sandbox, Docker, sandbox-linux
- ✅ **Idle/autonomous** — hits: Idle Self-Improvement, autonomous
- ✅ **Research/memory** — hits: Research, Memory, Project memory
- ✅ **Release/testing** — hits: Test all, Release gate
- ✅ **Architecture** — hits: Architecture, Planner, Validate, Repair

### gui_regression
# GUI Regression Test

Overall: **PASS**

# GUI Feature Map

Overall: **PASS**
Recommendation: Keep classic UI as default; add cockpit-preview behind /gui-mode cockpit until feature-map and visual tests pass.

## Feature coverage
- ✅ **Chat composer** — hits: Ask Nova, Send, attach
- ✅ **Voice controls** — hits: Mic test, Refresh mics, voice
- ✅ **Projects/files** — hits: Projects, Files, Zip project
- ✅ **Live Activity** — hits: Live activity, Current task
- ✅ **Model status** — hits: Local LLM status, LLM status
- ✅ **Sandbox/Docker** — hits: Sandbox, Docker, sandbox-linux
- ✅ **Idle/autonomous** — hits: Idle Self-Improvement, autonomous
- ✅ **Research/memory** — hits: Research, Memory, Project memory
- ✅ **Release/testing** — hits: Test all, Release gate
- ✅ **Architecture** — hits: Architecture, Planner, Validate, Repair

### gui_visual_gate
# GUI Visual Regression Gate

Spec present: **True**
npx available: **True**
Smoke command: `npx playwright test playwright/nova_gui_smoke.spec.js`
Snapshot update command: `npx playwright test --update-snapshots`

Visual screenshots are optional and require a running Nova browser target.

### blueprint_engine
# Project Blueprint

Goal: tiny useful local notes app with localStorage and JSON export
Artifact type: `html_css_js_app`
Confidence: **0.85**

## Likely files
- `index.html`
- `style.css`
- `app.js`
- `README.md`

## Must have
- JSON export
- add notes
- delete notes
- list saved notes
- localStorage persistence

## Must not have
- Dodge Game
- broken HTML/JS wiring
- fake README claims
- game controls or score unless requested
- unrelated default template

## Validation rules
- all blueprint files exist or are intentionally omitted
- HTML references local CSS/JS files that exist
- JS handlers referenced by HTML exist
- README claims are implemented in code
- must_not_have terms are absent unless explicitly requested
- project can be opened or syntax-checked without obvious errors
- app.js uses localStorage with safe JSON parse fallback
- app.js creates a JSON Blob/download or equivalent export

## Repair hints
- repair only the smallest failing requirement first
- do not switch templates unless the prompt requires it

### candidate_engine
# Candidate Build Plan

Goal: tiny useful local notes app with localStorage and JSON export
Recommended candidate: **robust**

## Blueprint summary
# Project Blueprint

Goal: tiny useful local notes app with localStorage and JSON export
Artifact type: `html_css_js_app`
Confidence: **0.85**

## Likely files
- `index.html`
- `style.css`
- `app.js`
- `README.md`

## Must have
- JSON export
- add notes
- delete notes
- list saved notes
- localStorage persistence

## Must not have
- Dodge Game
- broken HTML/JS wiring
- fake README claims
- game controls or score unless requested
- unrelated default template

## Validation rules
- all blueprint files exist or are intentionally omitted
- HTML references local CSS/JS files that exist
- JS handlers referenced by HTML exist
- README claims are implemented in code
- must_not_have terms are absent unless explicitly requested
- project can be opened or syntax-checked without obvious errors
- app.js uses localStorage with safe JSON parse fallback
- app.js creates a JSON Blob/download or equivalent export

## Repair hints
- repair only the smallest failing requirement first
- do not switch templates unless the prompt requires it

## Candidates
### minimal
- Strategy: smallest complete implementation
- Risk: low
- Score hint: 76
- Strength: fast and easy to repair
### polished
- Strategy: better UI, same core behaviours
- Risk: medium
- Score hint: 82
- Strength: more user-facing quality
### robust
- Strategy: adds validation, empty-state handling and README evidence
- Risk: medium
- Score hint: 88
- Strength: best for release-quality output

### trace_cockpit
# Nova Performance Dashboard

Generated: 2026-06-09 23:41:53
Recent operational events: **80**
Model log entries sampled: **20**

## Activity mix
- other: 55
- command: 17
- files: 3
- repair: 3
- memory: 1
- validate: 1

## Interpretation
- Work intensity score: 18
- If model events dominate, investigate prompt size/model speed.
- If repair/backtrack events dominate, strengthen blueprint/candidate validation.
- If command/validate events dominate and pass, Nova is likely doing useful verification rather than being stuck.

### mcp_manifest
# Nova MCP-style Tool Manifest

Name: Nova
Version: mcp-style-local-manifest-v1

## Security
- no arbitrary remote tool execution
- commands remain Nova allowlisted
- sandbox/dev runs use copied workspaces

## Tools exposed: 491
- `action_receipts` — internal_allowlisted
- `activity_log` — internal_allowlisted
- `adaptive_backlog` — internal_allowlisted
- `agent_execute` — internal_allowlisted
- `agent_feedback_loop_plan` — internal_allowlisted
- `agent_fuzzer_plan` — internal_allowlisted
- `agent_guardrail_memory` — internal_allowlisted
- `agent_harness` — internal_allowlisted
- `agent_topology_plan` — internal_allowlisted
- `agent_upgrade_radar` — internal_allowlisted
- `ai_create_project` — internal_allowlisted
- `ai_edit_project` — internal_allowlisted
- `analytics` — internal_allowlisted
- `analytics_dashboard` — internal_allowlisted
- `anti_repeat_check` — internal_allowlisted
- `append_file` — internal_allowlisted
- `assistant_box` — internal_allowlisted
- `assistant_db` — internal_allowlisted
- `audit_log` — internal_allowlisted
- `authority_gate` — internal_allowlisted
- `auto_self_repair` — internal_allowlisted
- `auto_verify` — internal_allowlisted
- `autonomous_explain_tools` — internal_allowlisted
- `autonomous_last_report` — internal_allowlisted
- `autonomous_memory` — internal_allowlisted
- `autonomous_mission_contract` — internal_allowlisted
- `autonomous_patch_mode` — internal_allowlisted
- `autonomous_progress_score` — internal_allowlisted
- `autonomous_tool_plan` — internal_allowlisted
- `backtrack_recover` — internal_allowlisted
- `behavior_fuzzer_plan` — internal_allowlisted
- `behaviour_evidence` — internal_allowlisted
- `benchmark_init` — internal_allowlisted
- `benchmark_run` — internal_allowlisted
- `benchmark_system` — internal_allowlisted
- `bisect_regression_plan` — internal_allowlisted
- `bridge_authority` — internal_allowlisted
- `bridge_receipts` — internal_allowlisted
- `browser_harness` — internal_allowlisted
- `browser_runtime_test` — internal_allowlisted
- `browser_smoke` — internal_allowlisted
- `browser_task_plan` — internal_allowlisted
- `browser_worker_plan` — internal_allowlisted
- `bug_hunt` — internal_allowlisted
- `bug_review` — internal_allowlisted
- `bug_sweep` — internal_allowlisted
- `build_quality_report` — internal_allowlisted
- `build_receipts` — internal_allowlisted
- `candidate_failure_report` — internal_allowlisted
- `candidate_tournament` — internal_allowlisted
- `capability_drift_audit` — internal_allowlisted
- `capability_manifests` — internal_allowlisted
- `chat_persona` — internal_allowlisted
- `claim_audit` — internal_allowlisted
- `clean_release_package` — internal_allowlisted
- `code_quality_gate` — internal_allowlisted
- `code_repair_audit` — internal_allowlisted
- `code_review_audit` — internal_allowlisted
- `codebase_advisor` — internal_allowlisted
- `codebase_improvement_plan` — internal_allowlisted
- `codebase_integrity_audit` — internal_allowlisted
- `codebase_sanity` — internal_allowlisted
- `codebase_sanity_audit` — internal_allowlisted
- `coding_acceptance_tests` — internal_allowlisted
- `coding_behavior_tests` — internal_allowlisted
- `coding_capability_audit` — internal_allowlisted
- `coding_loop_status` — internal_allowlisted
- `coding_plan` — internal_allowlisted
- `cohesion_report` — internal_allowlisted
- `command_catalog` — internal_allowlisted
- `command_contract_audit` — internal_allowlisted
- `command_flow_verify` — internal_allowlisted
- `command_verify` — internal_allowlisted
- `communication_quality_plan` — internal_allowlisted
- `completed_improvements` — internal_allowlisted
- `completion_audit` — internal_allowlisted
- `comprehensive_code_review` — internal_allowlisted
- `comprehensive_integration_review` — internal_allowlisted
- `console_test` — internal_allowlisted
- `context_budget` — internal_allowlisted
- ... 411 more

## Resources
- activity log
- model IO log
- project files
- release reports

### prompt_contract
# Prompt Contract

Goal: tiny useful local notes app with localStorage and JSON export
Artifact type: `html_css_js_app`

## Must have
- JSON export
- add notes
- delete notes
- display notes
- export notes as JSON
- list saved notes
- localStorage persistence
- persist notes in localStorage

## Must not have
- Dodge Game
- broken HTML/JS wiring
- fake README claims
- game controls or score unless requested
- score/player/enemy/canvas game defaults
- unrelated default template

## Static checks
- HTML references local CSS/JS files that exist
- JS handlers referenced by HTML exist
- README claims are implemented in code
- all blueprint files exist or are intentionally omitted
- app.js contains Blob or JSON.stringify download export
- app.js contains localStorage and safe JSON parse fallback
- app.js creates a JSON Blob/download or equivalent export
- app.js uses localStorage with safe JSON parse fallback
- must_not_have terms are absent unless explicitly requested
- project can be opened or syntax-checked without obvious errors

## Runtime checks
- open/run main entrypoint
- exercise key buttons/handlers
- verify output matches prompt

### contract_validation
# Prompt Contract Validation

Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
OK: **False**
Score: **48.2%**

## Checks
- ❌ HTML references local CSS/JS files that exist
- ✅ JS handlers referenced by HTML exist
- ✅ README claims are implemented in code
- ✅ all blueprint files exist or are intentionally omitted
- ❌ app.js contains Blob or JSON.stringify download export
- ❌ app.js contains localStorage and safe JSON parse fallback
- ❌ app.js creates a JSON Blob/download or equivalent export
- ❌ app.js uses localStorage with safe JSON parse fallback
- ✅ must_not_have terms are absent unless explicitly requested
- ✅ project can be opened or syntax-checked without obvious errors

## Forbidden hits
- none

## Missing requirements
- add notes
- list saved notes
- localStorage persistence

### candidate_tournament
# Candidate Tournament

Goal: tiny useful local notes app with localStorage and JSON export
Winner: **robust**

## Candidates
### robust
- Score: **56.2%**
- Strategy: adds validation, empty-state handling and README evidence
- Rank reason: needs repair: add notes, list saved notes, localStorage persistence
- Missing: add notes, list saved notes, localStorage persistence
- Forbidden: none
### polished
- Score: **52.2%**
- Strategy: better UI, same core behaviours
- Rank reason: needs repair: add notes, list saved notes, localStorage persistence
- Missing: add notes, list saved notes, localStorage persistence
- Forbidden: none
### minimal
- Score: **48.2%**
- Strategy: smallest complete implementation
- Rank reason: needs repair: add notes, list saved notes, localStorage persistence
- Missing: add notes, list saved notes, localStorage persistence
- Forbidden: none

## Promotion rule
Promote only the winner after contract validation, sandbox/Docker validation, and diff review pass.

### surgical_repair_v2
# Surgical Repair Engine v2

Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Failure type: **wrong_domain**
Risk: **medium**

## Minimal-diff policy
- prefer one file
- prefer smallest diff
- no broad rewrite unless two repairs fail
- snapshot before apply
- rollback available

## Plan
1. remove unrelated template artifacts
2. restore prompt-specific behaviours
3. rerun prompt contract validation

## Validation
- syntax/parse check
- prompt contract validation
- targeted regression test
- release gate when Nova code changed

### mcp_security
# Safe MCP / Connector Security Report

Generated: 2026-06-09 23:41:53
Tools inspected: **491**

## Policy
- default: `deny_execute_allow_readonly`
- read_only_tools: `True`
- command_execution: `disabled_until_allowlisted`
- raw_model_parameters: `never_forward_without_schema_validation`
- sandbox_risky_tools: `True`
- log_all_connector_calls: `True`

## Risky tools needing sandbox/approval
- agent_execute
- docker_clean
- docker_help
- docker_history
- docker_patch_validate
- docker_promote_patch
- docker_ps
- docker_smoke
- docker_status
- docker_validate
- install_package
- model_install
- project_delete
- rewrite_candidates
- run_shell
- sandbox_dev_run
- sandbox_exec
- sandbox_flag
- sandbox_policy
- sandbox_setup_help
- sandbox_start
- sandbox_status
- sandbox_stop
- tool_delete
- write_file
- write_files

## Recommendations
- keep connectors read-only by default
- sandbox risky tool execution
- deny external tool descriptions that request secrets or command execution
- require explicit user approval for install/promote/delete actions

### mission_planner
# Autonomous Mission Planner v2

Goal: improve Nova validation and file building
Status: **planned**

## Success conditions
- prompt contract created
- candidate or repair plan scored
- validation evidence collected
- no repeated no-op cycle
- release/test gate passes when Nova code changes

## Allowed tools
- `blueprint`
- `prompt-tests`
- `candidate-tournament`
- `contract-validate`
- `sandbox-dev-run`
- `trace-last`
- `gui-feature-map`
- `gui-regression-test`
- `gui-visual-test`

## Stop conditions
- no improvement after 2 cycles
- same failure repeated
- model unavailable
- user foreground task starts
- risk exceeds approval threshold

## Queue
- contract: `/prompt-contract improve Nova validation and file building`
- candidate: `/candidate-tournament improve Nova validation and file building`
- validate: `/contract-validate improve Nova validation and file building`
- trace: `/trace-last`

### model_output_coach
# Local Model Output Coach

Goal: tiny useful local notes app with localStorage and JSON export
JSON ok: **True**
Markdown fenced: **False**
Files detected: none
Score: **45.0%**

## Off-course signals
- missing requirements: JSON export, add notes, delete notes, list saved notes, localStorage persistence

## Coaching prompt
Your previous output was rejected for: missing requirements: JSON export, add notes, delete notes, list saved notes, localStorage persistence. User goal: tiny useful local notes app with localStorage and JSON export. Return only the required format. Add missing: JSON export, add notes, delete notes, list saved notes, localStorage persistence. Do not include: unrelated defaults. Split code into the correct files and keep README claims truthful.

### environment_profile
# Nova Environment Profile Doctor

Profile: `minimal`
OK: **True**

## Required
- ✅ python — 3.12.10
- ✅ pytest — import ok
- ✅ ollama — ollama version is 0.30.7

## Optional

## Install/fix plan
- none

### new_pc_benchmark
# Nova New-PC Benchmark / Migration Report

Generated: 2026-06-09 23:41:53
Platform: `Windows-11-10.0.26200-SP0`
Python: `3.12.10`
CPU count: **16**
Processor: `AMD64 Family 26 Model 68 Stepping 0, AuthenticAMD`

## Tool versions
- Docker: Docker version 29.5.2, build 79eb04c
- Ollama: ollama version is 0.30.7
- Node: v24.16.0

## Recommendations
- benchmark /fast build before and after new PC
- increase local model timeout only if model quality improves
- try larger coder model when VRAM >= 12GB
- raise Docker memory/CPU after confirming stability

### project_state
# Nova Project State Database v2

Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Original prompt: (not recorded)
Updated: 2026-06-09 23:41:53

## Counts
- blueprints: 0
- candidates: 0
- validation_failures: 0
- repair_attempts: 0
- file_diffs: 0
- user_feedback: 0

## Latest failures
- None recorded.

### regression_memory
# Regression Memory Engine

Count: **23**
## reg-1780669141
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780669399
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780669607
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780669960
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780670171
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780670956
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780679238
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780679452
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780680210
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780680680
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780681124
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780899931
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780900025
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780900283
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1780903144
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1781009236
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1781010195
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1781010899
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1781011422
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded
## reg-1781011956
- Description: test regression memory entry
- Repro: ``
- Expected: 
- Status: recorded

### build_quality_v3
# Nova Build Quality Report

Overall: **ATTENTION**
Score: **37.5%**
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Goal: tiny useful local notes app with localStorage and JSON export

## Checks
- ❌ **has_entrypoint** — Project has index.html or another obvious entrypoint.
- ❌ **html_links_js** — HTML should reference app.js for browser apps.
- ❌ **button_handler_wiring** — Inline handlers and common button IDs should exist in JS.
- ❌ **localstorage_when_requested** — localStorage is implemented when requested.
- ❌ **json_export_when_requested** — JSON export uses JSON.stringify plus Blob/download evidence when requested.
- ✅ **readme_claims_true** — README claims should have matching implementation evidence.
- ✅ **no_unrelated_dodge_default** — Reject unrelated Dodge Game/default-game leakage.
- ✅ **manual_test_clarity** — README/TEST_REPORT explain how to run or verify.

## Recommendations
- Fix has_entrypoint: Project has index.html or another obvious entrypoint.
- Fix html_links_js: HTML should reference app.js for browser apps.
- Fix button_handler_wiring: Inline handlers and common button IDs should exist in JS.
- Fix localstorage_when_requested: localStorage is implemented when requested.
- Fix json_export_when_requested: JSON export uses JSON.stringify plus Blob/download evidence when requested.

### browser_runtime_tester
# Browser Runtime Test

Overall: **ATTENTION**
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`

## Checks
- ❌ browser_entrypoint_exists — index.html exists for browser testing.
- ❌ script_reference_resolves — index.html references existing app.js.
- ❌ domcontent_or_safe_script — JS should run after DOM is available or script is at body end.
- ❌ clickable_controls — App has clickable controls.
- ❌ storage_flow — localStorage get/set flow present when requested.
- ❌ export_flow — JSON export flow present when requested.
- ✅ no_obvious_missing_dom_id — JS getElementById/querySelector references IDs present in HTML.

## Manual steps
- Open index.html or run /preview-start.
- Click every primary button.
- Refresh page and verify persistence if localStorage was requested.
- Try export if requested.

### model_reliability_controller
# Local Model Reliability

Overall: **DEGRADED/ATTENTION**
Recent attempts: 2
Recent rejections: 2
Recent failures: 9

## Recommendations
- Stop repeating the same prompt after two rejections; switch to prompt-contract + candidate tournament or deterministic template fallback.
- Use /model-output-coach and /model-fallback-strategy before another local model retry.

### model_requirement_download_planner
Nova Model Requirement and Download Planner

Goal: tiny useful local notes app with localStorage and JSON export
Status: ATTENTION
Summary: Required local models need attention or download approval

Ollama CLI: available
Installed models: gemma3:12b, nomic-embed-text:latest, gemma2:2b, llama3.2-vision:11b, qwen3-coder:30b

## Recommended models
- ❌ **Qwen2.5 Coder 7B** (`qwen2.5-coder:7b`) — required; risk low
  - Purpose: Default Nova coding, file generation, repair, JSON plans and validation-aware edits.
  - Size: ~5GB download/model storage
  - Install: `ollama pull qwen2.5-coder:7b`
- ✅ **Configured coding model** (`qwen3-coder:30b`) — required; risk low
  - Purpose: Configured in Nova settings.
  - Size: unknown
  - Install: `ollama pull qwen3-coder:30b`
- ✅ **Configured chat model** (`gemma2:2b`) — required; risk low
  - Purpose: Configured in Nova settings.
  - Size: unknown
  - Install: `ollama pull gemma2:2b`

## Safe download rule
Nova may request a missing model, but it only downloads through `/model-install NAME --confirm` after showing the exact command.
Next step: Run /model-install NAME --confirm only after reviewing the exact ollama pull command.

### model_fallback_strategy
# Model Fallback Strategy

- If JSON invalid: run /model-output-repair-json before retrying.
- If off-course twice: run /prompt-contract and block unrelated templates.
- If local model busy/degraded: switch to deterministic template or ask for confirmation before retrying.
- If generated files fail browser runtime checks: run /repair-plan then /build-quality-repair.

```json
{
  "same_rejection": 2,
  "same_candidate_refinement": 2,
  "llm_attempts_before_fallback": 3
}
```

### patch_queue
# Nova Patch Queue

Items: **23**
- `patch_1780669156_4` **proposed** risk=low — test patch
- `patch_1780669414_5` **proposed** risk=low — test patch
- `patch_1780669621_6` **proposed** risk=low — test patch
- `patch_1780669974_7` **proposed** risk=low — test patch
- `patch_1780670186_8` **proposed** risk=low — test patch
- `patch_1780670971_9` **proposed** risk=low — test patch
- `patch_1780679257_10` **proposed** risk=low — test patch
- `patch_1780679466_11` **proposed** risk=low — test patch
- `patch_1780680224_12` **proposed** risk=low — test patch
- `patch_1780680695_13` **proposed** risk=low — test patch
- `patch_1780681139_14` **proposed** risk=low — test patch
- `patch_1780899965_15` **proposed** risk=low — test patch
- `patch_1780900059_16` **proposed** risk=low — test patch
- `patch_1780900316_17` **proposed** risk=low — test patch
- `patch_1780903176_18` **proposed** risk=low — test patch
- `patch_1781009274_19` **proposed** risk=low — test patch
- `patch_1781010230_20` **proposed** risk=low — test patch
- `patch_1781010933_21` **proposed** risk=low — test patch
- `patch_1781011456_22` **proposed** risk=low — test patch
- `patch_1781011991_23` **proposed** risk=low — test patch

### gui_cockpit_v2
# GUI Cockpit v2 Preview

Mode: `mega-test`
Classic preserved: **True**

## Layout
- **left**: Chat, Projects, Build, Validate, Repair, Sandbox, Autonomous, Research, Memory, Settings
- **center**: Prompt, Plan, Candidate, Files, Validation, Final Output
- **right**: Model status, Current trace, Autonomous state, Warnings, Next best action
- **bottom**: Attach, Mic, Mic test, Send, Model progress

## Regression rules
- classic mode remains default
- every classic feature mapped before cockpit default
- run /gui-regression-test and /gui-visual-test before default switch

### voice_mode_upgrade
# Voice Mode Upgrade

- browser mic permission
- selected input device
- speech recognition support
- transcript preview before send
- readback using speechSynthesis

## Bluetooth notes
- For WH-1000/WH-1000XM, select the Headset input device, not only Headphones output.
- If no speech is detected, run /mic-test and Windows Settings > Sound > Input.

### template_builder
# Project Templates

- notes-app
- dashboard
- timer
- crud-app
- markdown-tool

Use deterministic templates for common apps, then let the model customize details.

### preview_server
# Preview Server

Action: `status`
URL: `http://127.0.0.1:8767`
Command: `python -m http.server 8767`
- Staged helper: run the command from the project folder for browser tests.
- Use /browser-run-test after starting preview.

### feature_readiness
# Feature Readiness

- **Docker validation** — ready
- **Playwright GUI tests** — ready
- **Voice input** — browser-dependent
- **Image generation** — optional backend required
- **Release hygiene** — ready

### error_translator
# Error Explanation

The browser could not reach the Nova backend. The server may have restarted, crashed, or the page may be stale.

## Next steps
- Refresh the browser page.
- Run /status.
- If still broken, restart Nova from the .bat file.

### support_report
# Nova Support Report

Generated: 2026-06-09 23:41:54
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Focus: mega-test
Release hygiene: None

## Recent activity
- `2026-06-09 23:41:17` sandbox_policy — Sandbox event: policy
- `2026-06-09 23:41:18` sandbox_policy — Sandbox event: policy
- `2026-06-09 23:41:18` sandbox_policy — Sandbox event: policy
- `2026-06-09 23:41:18` sandbox_start — Sandbox event: start
- `2026-06-09 23:41:26` candidate_refine_step — Edited rejected candidate in memory
- `2026-06-09 23:41:26` avatar — Working
- `2026-06-09 23:41:32` docker_promote_patch — Docker event: promote_patch
- `2026-06-09 23:41:50` file_write — Wrote C:\Users\Daniel\AppData\Local\Temp\pytest-of-Daniel\pytest-366\test_write_one_does_not_crash_0\Tinyappproject\index.html
- `2026-06-09 23:41:50` code_write_start — Writing model-generated file index.html
- `2026-06-09 23:41:50` file_write — Wrote index.html

## Commands to paste
- `/nova-mega-test --confirm`
- `/bug-review`
- `/trace-errors`
- `/support-report`

### docs_index
# Nova Docs/Code Index

- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\AGENTS.md` — # Nova Agent Instructions  ## Project Nova is a Windows-first local assistant with CLI, web UI, event logging, idle anal
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\CHANGELOG.md` — ## v55.3.168 — Project-state continuity memory  - Added project-state snapshots under `docs/NOVA_PROJECT_STATE_LATEST.*`
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\CODEBASE_OVERVIEW.md` — # Nova Codebase Overview  ## Purpose Nova is a local Windows assistant framework for planning, code generation, autonomo
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\ERROR_INVESTIGATION.md` — # Error Investigation Report  Generated: 2026-06-07 00:19:50 Workspace: `C:\Users\Daniel\Documents\Nova_v55_3_155_start_
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\IMPROVEMENTS_SESSION_3.md` — # Nova Comprehensive Inspection & Improvement - Session 3 Summary  ## Overview This session conducted a full audit of No
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\IMPROVEMENT_PROPOSALS.md` — # Nova Improvement Proposals  Generated: 2026-06-07 00:19:50 Focus: make improvements to NOVA  ## Available agent tools 
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\README.md` — # Nova v55.3.168  Legacy continuity anchor: Nova v55.3.164 runtime usability/release-readiness history is preserved for 
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_BETTER_MODELS_VIDEO_PATCH.md` — # Nova better-model + video-manifest patch validation  Patch date: 2026-06-06  ## Implemented  - Added explicit better-P
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_151_BUGFIX_VIDEO.md` — # Nova v55.3.151 bugfix/video validation notes  Changes: - Added browser startup guards for stale UI settings and missin
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_152_INTEGRATION_FOUNDATION.md` — # Validation v55.3.152 Integration Foundation  Commands run in the extracted Linux sandbox:  ```bash python -m compileal
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_153_COMPREHENSIVE_INTEGRATION.md` — # Nova v55.3.153 Comprehensive Integration Validation  ## Scope This patch focused on the repo-integration blueprint pri
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_154_REGRESSION_HARDENING.md` — # Nova v55.3.154 validation notes  This release hardens the v55.3.153 integration package by synchronising release metad
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_155_START_HERE_HARDENING.md` — # Nova v55.3.155 validation notes  This release makes `START_NOVA_HERE.bat` the obvious first-run path and adds validati
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_156_AUTONOMOUS_MEDIA_SUBAGENTS.md` — # Nova v55.3.156 Autonomous, Media and Safe Subagent Hardening  ## Summary  This patch integrates the attached Codex wor
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_157_RESEARCH_VOICE_HARDENING.md` — # Nova v55.3.159 validation  ## Purpose This patch hardens the v55.3.156 package using the v55.3.155 runtime logs suppli
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_158_SELF_REPAIR_OLLAMA_QUEUE.md` — # Nova v55.3.158 Self-Repair and Ollama Queue Validation  Changes: - Adds bounded mistake-learning/self-repair guardian.
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_159_CLEAN_GUI_DOCKER_HARDENING.md` — # Nova v55.3.159 Clean GUI and Docker Validation Hardening  ## Changes  - Added a visible `Nova v55.3.159` version badge
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_160_MEDIA_REFINEMENT.md` — # Nova v55.3.160 Media Refinement Validation  Added `/media-status`, `/image-plan`, `/video-storyboard`, and `/video-pac
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\VALIDATION_V55_3_161_GUI_STARTUP_MEDIA_ROUTE_HARDENING.md` — # Nova v55.3.161 validation  ## Fixed from user-attached run  - PowerShell activation confusion and incomplete `.venv` s
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\docs\AI_CONTEXT_START_HERE.md` — # Nova AI Context Start Here  Read this first when you are an AI or human developer entering Nova without prior context.
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\docs\CODEX_REPAIR_PROMPT_V55_3_48.md` — # Codex prompt: full Nova codebase repair and sandbox hardening  You are Codex working on Nova. Your task is to repair t
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\docs\IMPLEMENTATION_STATUS_V55_3_41.md` — # Nova user-request implementation status after v55.3.43  ## Implemented - Spoken audio with summarised long replies, mu
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530\docs\IMPROVEMENT_REPORT_V53_4.md` — # Nova Historical Improvement Report  This restored continuity marker preserves roadmap evidence required by the feature
- `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gat

### regression_test_generator
# Regression Test Generator

Test seed: `tests_generated_regression_mega_test_regression_seed.py`
Status: **seed_generated_not_written**

```python
def test_regression_memory_placeholder():
    bug = 'mega-test regression seed'
    assert bug
    # Generated protection seed: convert this placeholder into an executable reproduction.

```

### mistake_learning
# Nova Mistake Learning Status

Regression memory: **False**
Patch queue items: **23**

## Loop
- capture failure in trace
- convert to regression seed
- add to prompt-contract must_not/must_have
- validate through /nova-mega-test
- record outcome in project state

### interaction_flow_audit
# Nova Interaction Flow and No-Regression Audit

Generated: 2026-06-09 23:41:54
Root: `C:\Users\Daniel\Documents\Nova_v55_3_168_startup_release_gate_hotfix_20260609_20260609_123530`
Version: 55.3.168
Overall: **PASS**
Summary: Interaction flow audit passed

## Flow groups
- ✅ **build_and_validate** — Prompt-specific app/file building path from user goal to validated artifact.
  - why: Prevents technically-valid-but-wrong projects and validates real prompt requirements.
  - commands: `/prompt-contract`, `/candidate-tournament`, `/iterative-code-loop`, `/build-quality-report`, `/browser-run-test`, `/model-output-coach`
  - tools: `prompt_contract`, `candidate_tournament`, `iterative_coding_loop`, `build_quality_report`, `browser_runtime_test`, `model_output_coach`
  - capabilities: `prompt_to_test`, `candidate_tournament`, `iterative_coding_repair`, `build_quality_browser_runtime`
- ✅ **repair_and_fallback** — Minimal-diff repair path before broad regeneration.
  - why: Keeps repairs small, evidence-driven, staged and reversible.
  - commands: `/repair-diagnose`, `/repair-plan`, `/surgical-fallback-v2`, `/edit-repair-plan`, `/repair-verify`, `/patch-propose`
  - tools: `repair_plan_v2`, `surgical_fallback_v2`, `edit_repair_plan`, `patch_queue`
  - capabilities: `surgical_repair_v2`, `iterative_coding_repair`, `patch_queue_and_learning`
- ✅ **autonomous_idle_learning** — Mission-aware autonomy with progress scoring, repetition guard and mistake learning.
  - why: Stops vague no-op cycles and records lessons from repeated failures.
  - commands: `/mission-dashboard`, `/cycle-score`, `/tool-choice-trace`, `/repetition-guard-status`, `/mistake-learning-status`, `/mistake-to-regression`
  - tools: `mission_dashboard`, `cycle_score`, `tool_choice_trace`, `repetition_guard_status`, `mistake_learning_status`, `mistake_to_regression`
  - capabilities: `mission_intelligence`, `cycle_progress_scoring`, `tool_choice_trace`, `repetition_guard`, `patch_queue_and_learning`
- ✅ **model_dependency_and_reliability** — Model readiness, fallback, stuck detection and confirmable model downloads.
  - why: Prevents long stuck prompts and explains when a stronger/missing model is required.
  - commands: `/model-requirements`, `/model-readiness`, `/model-download-plan`, `/model-install`, `/model-reliability`, `/model-fallback-strategy`
  - tools: `model_readiness`, `model_requirements`, `model_download_plan`, `model_install`, `model_reliability`, `model_fallback_strategy`
  - capabilities: `model_dependency_management`, `model_reliability_controller`
- ✅ **regression_support_and_reporting** — No-regression checks, support export, error translation and one-command coverage.
  - why: Keeps new features from hiding old breakage and produces clean diagnostics.
  - commands: `/regression-sweep`, `/bug-review`, `/whole-codebase-review`, `/nova-mega-test`, `/support-report`, `/explain-error`
  - tools: `regression_sweep`, `bug_review`, `whole_codebase_review`, `support_report`, `explain_error`
  - capabilities: `weakspot_error_hunt`, `support_and_error_translation`, `improvement_roadmap`
- ✅ **tool_extension_and_sandboxing** — Guarded self-extension and copied-workspace sandbox testing before live promotion.
  - why: Lets Nova add helpers while keeping new code validated away from live files.
  - commands: `/tool-create`, `/tool-test`, `/tool-run`, `/sandbox-dev-run`, `/docker-validate`
  - tools: `tool_create`, `tool_test`, `tool_run`, `sandbox_dev_run`, `docker_validate`
  - capabilities: `custom_tool_extension`, `sandbox_dev_copy`

## Scenario tool choices
- **build_path** — make a tiny useful notes app with localStorage and JSON export
  - selected: build_quality_browser_runtime, project_build, model_output_coach, model_reliability_controller, templates_preview_feature_readiness
  - first commands: `/build-quality-report GOAL`, `/fast GOAL`, `/model-output-score GOAL`, `/model-reliability`, `/template-list`
- **repair_path** — fix the app because export button and localStorage are broken
  - selected: build_quality_browser_runtime, surgical_repair, bug_review, project_build
  - first commands: `/build-quality-report GOAL`, `/surgical-repair NOTE`, `/bug-review`, `/fast GOAL`
- **model_path** — download or request the required coding model for a difficult repair
  - selected: iterative_coding_repair, model_output_coach, model_reliability_controller, surgical_repair, surgical_repair_v2, model_help_planning
  - first commands: `/iterative-code-loop GOAL`, `/model-output-score GOAL`, `/model-reliability`, `/surgical-repair NOTE`, `/repair-diagnose`
- **autonomy_path** — make autonomous and idle learn from mistakes and avoid repeating failed strategies
  - selected: repetition_guard, interaction_flow_validation, patch_queue_and_learning, mission_intelligence, cycle_progress_scoring, tool_choice_trace, mission_planner, autonomous_memory
  - first commands: `/repetition-guard-status`, `/flow-audit`, `/patch-queue`, `/mission-dashboard`, `/cycle-score`
- **tool_path** — make yourself a useful custom tool and test it in a sandbox copy
  - selected: custom_tool_extension, project_build, sandbox_dev_copy, candidate_validation, prompt_to_test, safe_mcp_connectors
  - first commands: `/tool-create GOAL`, `/fast GOAL`, `/sandbox-dev-run linux CMD`, `/test-project standard`, `/prompt-contract GOAL`

## Implemented/proposed improvement policy
- Keep generated-project flows gated by prompt contracts, candidate tournaments and browser/runtime quality checks.
- Use repair v2 and iterative coding before broad regeneration when a project is close but broken.
- Require model-readiness checks before model-heavy/vision/coding tasks and explicit --confirm before downloads.
- Route idle/autonomous through mission progress scoring and repetition guard after every cycle.
- Export support reports after failures so future debugging carries version, trace, model and project state together.