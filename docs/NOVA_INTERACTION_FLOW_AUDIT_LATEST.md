# Nova Interaction Flow and No-Regression Audit

Generated: 2026-06-09 23:42:30
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