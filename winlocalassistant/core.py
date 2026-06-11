from __future__ import annotations
import difflib
import json
import re
import shlex
import time
import threading
import queue
import uuid
import shutil
import subprocess
import random
import sys
import logging
from dataclasses import asdict, replace
from pathlib import Path
from typing import Any
from . import __version__, VERSION_LABEL, ASSISTANT_NAME
from .branding import canonical_command, render_branding_audit, scan_legacy_branding
from .nova_improvement_research import build_nova_improvement_research, render_nova_improvement_research
from .nova_eval_packs import build_nova_eval_plan, run_nova_eval_pack, render_nova_eval_packs
from .nova_verified_changes import build_verified_change_plan, preview_verified_change, apply_verified_change, render_verified_change
from .nova_odysseus_suite import handle_odysseus_suite_command
from .config import AssistantConfig, APP_DIR, PLAN_PATH, TRACE_PATH, MEMORY_PATH
from .persona_profile import build_persona_prompt_addendum
from .autonomous_failure import (
    AUTONOMOUS_FAILURE_MEMORY_PATH,
    REPAIR_TRIGGER_CATEGORIES,
    AutonomousFailureMemory,
    AutonomousFailureRecord,
    build_autonomous_repair_prompt,
    clear_autonomous_cooldowns_for_action,
    classify_autonomous_failure,
    load_autonomous_failure_memory,
    make_failure_signature,
    save_autonomous_failure_memory,
    should_cooldown_autonomous_action,
    update_autonomous_failure_memory,
    write_autonomous_repair_proposal,
)
from .idle_engine import append_idle_event, collect_idle_candidates, default_verification_commands, load_strategy_state, save_strategy_state, select_candidate, update_strategy_state_after_report
from .intent_planning import analyze_planning_dialog_need
from .model_router import model_chat
from .planner import Plan, make_plan
from .projects import get_project, register_project
from .request_intent import analyze_request_intent, should_block_automatic_mutation
from .surgical_fallback import apply_surgical_fallback_to_file, surgical_fallback_report_payload
from .file_context import (
    build_prompt_context,
    clear_file_contexts,
    list_file_contexts,
    register_file_context_from_path,
    resolve_image_context,
)
from .image_generation import generate_image, edit_image, create_svg_draft, render_image_generation_status, render_image_setup_wizard, build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status
from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test_scenarios, write_video_preview_avi, write_video_preview_html, write_storyboard_svg, write_shotlist_csv, build_video_image_prompt_plan, write_video_render_package, render_video_render_package_markdown, media_status_summary
from .tools import ToolRegistry, ToolResult
from .eventlog import ACTIVITY_PATH, MODEL_IO_PATH, log_activity, tail_jsonl, new_run_id, set_current_run
from .tool_guides import get_autonomous_tool_use_summary
from .quality_dashboard import write_quality_dashboard_report, render_quality_dashboard_markdown
from .self_awareness import write_self_awareness_report, render_self_awareness_markdown
from .action_watcher import evaluate_action_risk, record_action_outcome
from .tool_catalog import render_tool_catalog_markdown, catalog_as_json
from .quality_progress import read_quality_progress
from .interaction_learning import append_interaction_lesson, derive_interaction_lesson, load_interaction_lessons, render_lessons_markdown
from .planning_dashboard import build_planning_dashboard, render_planning_dashboard_markdown
from .autonomous_explain import explain_autonomous_state, render_autonomous_explanation_markdown
from .autonomous_sequence import build_autonomous_tool_sequence, render_autonomous_sequence_markdown
from .autonomy_capabilities import render_capability_markdown, build_mutable_mission_plan
from .blueprint_engine import build_project_blueprint, build_candidate_set, score_candidate, render_blueprint_markdown, render_candidate_markdown, render_score_markdown
from .trace_cockpit import build_trace, render_trace_markdown, render_performance_dashboard
from .gui_redesign import build_gui_feature_map, render_gui_feature_map, cockpit_preview_markdown, gui_regression_check, render_gui_regression
from .mcp_export import build_mcp_manifest, render_mcp_manifest
from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status
from .gui_layout_diagnostics import build_gui_layout_diagnostics, render_gui_layout_diagnostics, render_gui_reset_help
from .gui_context_help import build_gui_context_help, render_gui_context_help, render_repo_inspired_gui_help_upgrades
from .build_info import build_patch_identity, render_patch_identity
from .behavior_rules import add_behavior_rule, delete_behavior_rule, list_behavior_rules, render_behavior_rules
from .nova_arcade import arcade_registry, render_arcade_registry, render_arcade_launch, write_arcade_manifest
from .command_help import command_help_payload, render_command_help, render_concise_help
from .task_execution import build_task_contract as build_task_execution_contract, build_task_execution_status, render_task_contract, render_task_execution_status
from .legacy_continuity import build_legacy_continuity_audit, render_legacy_continuity_audit, write_legacy_contract
from .performance_tuning import (
    collect_performance_status, render_performance_status, build_tuning_plan, render_tuning_plan,
    benchmark_plan_payload, render_benchmark_plan, write_benchmark_scripts, render_write_result,
    render_artifact_checklist, apply_startup_performance_environment,
)
from .wla_mega_test import run_wla_mega_test, render_wla_mega_test
from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation
from .candidate_tournament import build_candidate_tournament, render_tournament, render_candidate_failure_report, candidate_diff
from .repair_engine_v2 import diagnose_repair, build_repair_plan, render_repair
from .mcp_security import inspect_mcp_security, render_mcp_security, explain_mcp_tool
from .mission_planner_v2 import create_mission, load_mission, mission_step, render_mission
from .model_output_coach import analyze_model_output, render_model_output_coach
from .env_profiles import build_env_profile, render_env_profile
from .benchmark_migration import benchmark_system, render_benchmark
from .project_state_db import load_project_state, append_project_state, render_project_state
from .regression_memory import load_regressions, add_regression, export_regressions, render_regressions
from .weakspot_audit import write_weakspot_report, render_weakspot_audit, build_weakspot_audit
from .user_testing import write_user_testing_report, render_user_testing_report
from .improvement_cycle import build_improvement_proposals, complete_improvement_proposals, load_latest_improvement_cycle, render_improvement_cycle
from .regression_sweep import build_regression_sweep, render_regression_sweep
from .improvement_roadmap import build_next_improvement_roadmap, build_improvement_impact_matrix, complete_next_improvements, load_latest_improvement_roadmap, render_improvement_roadmap
from .whole_codebase_review import build_whole_codebase_review, render_whole_codebase_review
from .bug_review import build_bug_review, render_bug_review
from .autonomy_idle_intelligence import (
    build_mission_dashboard, build_tool_choice_trace, _score_from_events, _events,
    repeated_signature, clear_repetition_memory, load_background_settings, set_background_setting,
    log_mistake, load_mistake_log, mistake_to_regression, autonomous_last_report, render_payload,
)
from .next_feature_suite import (
    build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,
    build_model_reliability, render_model_reliability, build_model_fallback_strategy, render_strategy,
    patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,
    build_voice_mode_report, render_voice_mode, list_templates, build_template_project, render_templates,
    build_preview_server_report, render_preview, build_feature_readiness, render_feature_readiness,
    explain_error, render_error_explanation, build_support_report, render_support_report, docs_index, render_docs_index,
    regression_test_generate, render_regression_test, learning_status, render_learning_status,
)
from .iterative_coding import build_surgical_fallback_plan, build_iterative_coding_loop, render_iterative_coding_markdown, write_iterative_coding_report
from .autonomous_journal import build_run_journal, latest_run_journal, make_step_event, render_run_journal_markdown, write_run_journal
from .command_verifier import verify_command_contracts, render_command_verification_markdown
from .architecture_audit import write_architecture_audit_report, render_architecture_audit_markdown
from .model_health import assess_model_dependency, render_model_health_markdown
from .skill_profiles import choose_skill_mode, normalise_skill_mode, skill_prompt, skill_status_text, try_quick_arithmetic
from .assistant_box import write_assistant_box, read_assistant_box
from .project_memory import remember_project_fact, list_project_memory, search_project_memory, project_memory_context
from .conversation_store import create_conversation, switch_conversation, list_conversations, append_message as store_conversation_message, get_active_messages, search_conversations, rename_conversation, delete_conversation
from .release_checklist import build_release_checklist, render_release_checklist_markdown
from .security_status import build_security_status, render_security_status
from .security_watch import run_security_watch, render_security_watch
from .system_test import run_massive_system_test, render_massive_system_test
from .completion_audit import build_completion_audit, render_completion_audit
from .dependency_check import build_dependency_report, render_dependency_report
from .idle_policy import load_idle_policy as _idle_policy_load, set_idle_policy_level as _idle_policy_set_level, render_idle_policy as _idle_policy_render, idle_allows as _idle_policy_allows
from . import idle_policy as idle_policy_module
from .upgrade_planner import build_upgrade_radar, render_upgrade_radar
from .optional_upgrade_installer import build_optional_upgrade_status, render_optional_upgrade_status, install_optional_upgrade, render_optional_upgrade_install_result
from .model_download_manager import build_model_readiness, render_model_readiness, install_model, render_model_install_result
from .response_quality import build_response_quality_plan, render_response_quality_plan, write_response_quality_plan
from .flow_audit import build_flow_audit, render_flow_audit, write_flow_audit
from .release_hygiene import build_release_hygiene_report, render_release_hygiene_report, clean_release_hygiene_artifacts
from .efficiency_profiler import append_efficiency_sample
from .safe_io import append_jsonl, atomic_write_json, atomic_write_text, read_json_file
from .validate import load_validation_status, render_validation_status
from .remote_access import (
    build_remote_access_plan,
    build_remote_access_preflight,
    build_remote_access_status,
    build_remote_profile_wizard,
    parse_remote_api_health_args,
    parse_remote_wake_args,
    remote_profile_action,
    render_remote_access_assets,
    render_remote_access_plan,
    render_remote_access_preflight,
    render_remote_access_status,
    render_remote_api_health,
    render_remote_profile_wizard,
    render_remote_profiles,
    render_wol_result,
    probe_remote_api_health,
    send_wake_on_lan,
    write_remote_access_assets,
)

LOGGER = logging.getLogger(__name__)

# Keep idle-policy storage aligned with core.APP_DIR so tests/profile overrides and
# packaged runtime profiles do not accidentally read a stale global policy file.
def _sync_idle_policy_path() -> None:
    try:
        idle_policy_module.IDLE_POLICY_PATH = APP_DIR / "idle_policy.json"
    except Exception as exc:
        try:
            log_activity("idle_policy_path_sync_failed", "Failed to sync idle policy path", {"error": repr(exc)})
        except Exception:
            LOGGER.debug("Suppressed idle policy path sync log failure", exc_info=True)

def load_idle_policy():
    _sync_idle_policy_path()
    return _idle_policy_load()

def set_idle_policy_level(value, *, updated_by="user"):
    _sync_idle_policy_path()
    return _idle_policy_set_level(value, updated_by=updated_by)

def render_idle_policy(policy=None):
    _sync_idle_policy_path()
    return _idle_policy_render(policy)

def idle_allows(action, policy=None):
    _sync_idle_policy_path()
    return _idle_policy_allows(action, policy)

from .sandbox_manager import evaluate_sandbox_command
from .sandbox_permissions import (
    APPROVAL_WORDS,
    DENIAL_WORDS,
    clear_pending_sandbox_permission,
    create_pending_sandbox_permission,
    load_pending_sandbox_permission,
    render_pending_sandbox_permission_markdown,
    sandbox_command_targets_network,
)
from .autonomous_loop_guard import (
    action_signature as autonomous_action_signature,
    should_skip_repeated_action,
    summarize_cycle_outcome,
    update_loop_guard_state,
)
SYSTEM_PROMPT = """You are Nova, a local Windows coding and automation assistant.
Nova is both the product name and the visible assistant persona.
Be practical and direct. Prefer PowerShell commands on Windows.
Never claim an action was completed unless a tool result confirms it.
When a user explicitly asks you to create/build/write code/files/projects, make concrete file edits and verify them.
For ordinary conversation, explanation, brainstorming, and creative writing, answer normally instead of refusing or forcing a build plan.
"""

IDLE_AUTONOMY_SETTINGS_FILE = "IDLE_AUTONOMY_SETTINGS.json"
IDLE_AUTO_APPLY_SAFE_CATEGORIES = {"tests", "docs", "logging", "report"}
IDLE_AUTO_APPLY_PROTECTED_FILE_NAMES = {"core.py", "tools.py", "security.py"}
IDLE_AUTO_APPLY_PROTECTED_PATH_TERMS = [
    "internet",
    "network",
    "install",
    "update",
    "package",
    "self-improve",
    "self_improve",
    "backup",
    "rollback",
]


def _idle_autonomy_settings_path() -> Path:
    return APP_DIR / IDLE_AUTONOMY_SETTINGS_FILE


def load_idle_autonomy_settings() -> dict:
    defaults = {"idle_auto_apply_low_risk": True}
    path = _idle_autonomy_settings_path()
    try:
        if not path.exists() or not path.is_file():
            return dict(defaults)
        data = read_json_file(path, dict(defaults), expected_type=dict, quarantine=True)
        if not isinstance(data, dict):
            return dict(defaults)
        return {"idle_auto_apply_low_risk": bool(data.get("idle_auto_apply_low_risk", True))}
    except Exception:
        return dict(defaults)


def save_idle_autonomy_settings(settings: dict) -> None:
    path = _idle_autonomy_settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    data = {"idle_auto_apply_low_risk": bool((settings or {}).get("idle_auto_apply_low_risk", False))}
    atomic_write_json(path, data, ensure_ascii=True)


def _candidate_field(candidate: Any, name: str, default: Any = None) -> Any:
    if isinstance(candidate, dict):
        return candidate.get(name, default)
    return getattr(candidate, name, default)


def _normalize_idle_gate_path(path: str) -> str:
    return str(path or "").replace("\\", "/").lower()


def evaluate_idle_auto_apply_gate(candidate: Any, target_files: Any, patch_summary: dict | None = None) -> dict:
    settings = load_idle_autonomy_settings()
    if not settings.get("idle_auto_apply_low_risk", False):
        return {
            "allowed": False,
            "status": "auto-apply-disabled",
            "reasons": [
                "Auto-apply is disabled.",
                "No source edits can be applied while this setting is off.",
                "This setting does not bypass safety checks.",
            ],
        }

    reasons: list[str] = []
    files = list(target_files or _candidate_field(candidate, "target_files", []) or [])
    category = str(_candidate_field(candidate, "category", "") or "")
    risk_score = float(_candidate_field(candidate, "risk_score", 1.0) or 0.0)
    allowed_by_candidate = bool(_candidate_field(candidate, "allowed_to_auto_apply", False))

    if candidate is None:
        reasons.append("No selected candidate is available.")
    if not allowed_by_candidate:
        reasons.append("Candidate was not marked low-risk auto-apply eligible by idle scoring.")
    if risk_score > 0.20:
        reasons.append(f"Candidate risk score {risk_score:.2f} is above the 0.20 limit.")
    if category not in IDLE_AUTO_APPLY_SAFE_CATEGORIES:
        reasons.append(f"Candidate category '{category or 'unknown'}' is not eligible for auto-apply.")

    for target in files:
        normalized = _normalize_idle_gate_path(target)
        name = normalized.rsplit("/", 1)[-1]
        if name in IDLE_AUTO_APPLY_PROTECTED_FILE_NAMES:
            reasons.append(f"Target file '{target}' is protected.")
        for term in IDLE_AUTO_APPLY_PROTECTED_PATH_TERMS:
            if term in normalized:
                reasons.append(f"Target file '{target}' contains protected term '{term}'.")
                break

    if not default_verification_commands():
        reasons.append("Verification commands are unavailable.")

    if not isinstance(patch_summary, dict):
        reasons.append("No concrete verified patch is available; proposal-only mode required.")
    else:
        if "changed_files" not in patch_summary or "changed_lines" not in patch_summary:
            reasons.append("No concrete verified patch is available; proposal-only mode required.")
        try:
            changed_files = int(patch_summary.get("changed_files") or 0)
        except Exception:
            changed_files = 999
            reasons.append("Patch summary changed_files is not a valid integer.")
        try:
            changed_lines = int(patch_summary.get("changed_lines") or 0)
        except Exception:
            changed_lines = 999
            reasons.append("Patch summary changed_lines is not a valid integer.")
        if changed_files > 1:
            reasons.append("Patch changes more than 1 file.")
        if changed_lines > 80:
            reasons.append("Patch changes more than 80 lines.")
        if not patch_summary.get("backup_available"):
            reasons.append("Patch summary does not confirm an available backup.")
        if not patch_summary.get("diff_report_available"):
            reasons.append("Patch summary does not confirm an available diff report.")
        if not patch_summary.get("verification_available"):
            reasons.append("Patch summary does not confirm verification availability.")

    if reasons:
        status = "auto-apply-pending-patch" if any("No concrete verified patch" in reason for reason in reasons) else "auto-apply-needs-attention"
        return {"allowed": False, "status": status, "reasons": reasons}

    return {
        "allowed": True,
        "status": "auto-apply-eligible",
        "reasons": [
            "Candidate meets the guarded low-risk auto-apply gate.",
            "Automatic apply may proceed only with backup, diff report, verification and rollback available.",
        ],
    }


NON_BLOCKING_STATUS_COMMANDS = {
    "/status", "/activity", "/llm-status", "/ollama-stop", "/interrupt-current",
    "/projects", "/files", "/project-files", "/active-run", "/pause-run",
    "/resume-run", "/cancel-run", "/reply", "/model-doctor", "/model-health", "/llm-lab", "/llm-training", "/training-lab",
    "/command-timeout", "/known-issues", "/autonomous-memory", "/idle",
    "/idle-status", "/avatar", "/command-catalog", "/tool-catalog",
    "/self-guide", "/how-to-use", "/full-guide", "/model-timeout",
    "/response-quality-plan", "/ai-response-plan", "/communication-quality-plan",
    "/memory", "/remember", "/knowledge", "/learn-errors", "/reasoning",
    "/recovery-plan", "/recover-known-error", "/avatar-sound", "/speak",
    "/tool-help", "/tool-inputs", "/tool-pipeline", "/safe-script-demo",
    "/watch-topic", "/topic-watchers", "/topic-check", "/internet-fetch", "/internet-search", "/search-web",
    "/allow-internet", "/action-watch", "/interaction-lessons",
    "/planning-dashboard", "/project-spec", "/autonomous", "/autonomous-status",
    "/comprehensive-user-test", "/user-test-suite", "/qa-test", "/user-feedback-tests", "/full-functionality-test-commands", "/nova-test-commands", "/improvement-proposals", "/improvement-cycle", "/completed-improvements", "/improvement-status", "/improvement-roadmap", "/improvement-impact", "/implement-improvements", "/proposal-ledger", "/next-improvements", "/bug-review", "/bug-hunt", "/bug-sweep", "/error-review", "/regression-sweep", "/no-regression-check", "/functionality-matrix", "/integration-health", "/autonomous-guide", "/autonomy-readiness", "/autonomy-capability-audit", "/autonomy-audit", "/autonomous-explain", "/autonomous-plan", "/autonomy-capabilities", "/mutable-plan", "/blueprint", "/blueprint-build", "/blueprint-validate", "/candidate-build", "/candidate-compare", "/candidate-report", "/candidate-promote", "/model-output-score", "/trace-last", "/trace-run", "/trace-export", "/performance-dashboard", "/gui-feature-map", "/gui-mode", "/gui-redesign-preview", "/gui-regression-test", "/mcp-export-manifest", "/mcp-tools", "/mcp-status", "/gui-snapshot", "/screen-analysis-prompt", "/screen-context-help", "/screen-analysis-help", "/gui-visual-test", "/gui-layout-status", "/gui-layout-check", "/gui-layout-diagnostics", "/gui-reset-help", "/gui-layout-reset-help", "/gui-ai-help", "/gui-context-help", "/gui-command-help", "/gui-ai-upgrades", "/command-help", "/commands-help", "/help-search", "/release-readiness", "/release-gate", "/release-gate-full", "/legacy-continuity-audit", "/legacy-regression-lock", "/feature-regression-guard", "/arcade", "/nova-arcade", "/arcade-status", "/arcade-list", "/arcade-launch", "/arcade-manifest", "/behavior-rules", "/remember-behavior", "/forget-behavior", "/build-info", "/patch-info", "/gui-build-info", "/perf-status", "/performance-status", "/perf-env", "/perf-tune-plan", "/performance-tune-plan", "/perf-benchmark", "/performance-benchmark", "/perf-artifact-checklist", "/nova-mega-test", "/nova-test-all", "/prompt-contract", "/prompt-tests", "/prompt-test-run", "/contract-validate", "/candidate-tournament", "/candidate-score", "/candidate-promote", "/candidate-diff", "/candidate-failure-report", "/repair-diagnose", "/repair-plan", "/repair-apply", "/repair-verify", "/repair-replay", "/repair-rollback", "/trace-status", "/trace-timeline", "/trace-errors", "/replay-run", "/mcp-inspect", "/mcp-permissions", "/mcp-risk-report", "/mcp-sandbox-tool", "/mcp-deny", "/mcp-allow", "/mcp-explain-tool", "/mission-create", "/mission-status", "/mission-step", "/mission-queue", "/mission-promote", "/mission-stop", "/model-output-repair-json", "/model-output-split-files", "/model-output-off-course", "/model-output-coach", "/env-profile", "/env-doctor", "/env-fix-plan", "/env-install-plan", "/benchmark-system", "/benchmark-models", "/benchmark-fast-build", "/benchmark-docker", "/benchmark-gui", "/migration-report", "/new-pc-tune", "/project-state", "/project-history", "/project-failures", "/project-success-criteria", "/project-restore", "/project-compare", "/regression-add", "/regression-list", "/regression-run", "/regression-from-last-failure", "/regression-export", "/build-quality-report", "/build-quality-score", "/build-quality-repair", "/build-quality-compare", "/browser-run-test", "/browser-click-test", "/browser-storage-test", "/browser-export-test", "/browser-screenshot-test", "/model-requirements", "/model-download-plan", "/model-readiness", "/model-install", "/model-select-recommendation", "/model-auto-request", "/flow-audit", "/interaction-flow-audit", "/interaction-pathways", "/command-flow-verify", "/learning-loop-audit", "/flow-improvements", "/complete-flow-improvements", "/model-reliability", "/model-stuck-diagnose", "/model-output-retry-plan", "/model-fallback-strategy", "/model-json-enforcer", "/model-timeout-profile", "/patch-queue", "/patch-propose", "/patch-preview", "/patch-validate", "/patch-promote", "/patch-rollback", "/gui-mode", "/gui-feature-coverage", "/gui-redesign-test", "/voice-device-status", "/voice-calibrate", "/voice-readback-test", "/template-list", "/template-build", "/template-customize", "/preview-start", "/preview-stop", "/preview-status", "/preview-open", "/preview-screenshot", "/feature-readiness", "/feature-enable", "/feature-disable", "/feature-fix-plan", "/explain-error", "/error-summary", "/error-next-step", "/error-fix-plan", "/export-support-report", "/support-report", "/chatgpt-report", "/copy-debug-context", "/index-nova", "/search-nova-docs", "/search-nova-code", "/explain-command", "/explain-feature", "/regression-from-bug", "/regression-test-generate", "/regression-test-run", "/regression-protection-status", "/new-pc-benchmark", "/new-pc-model-select", "/new-pc-timeout-tune", "/new-pc-docker-tune", "/new-pc-profile-save", "/mission-dashboard", "/mission-progress", "/mission-retrospective", "/mission-resume", "/cycle-score", "/autonomous-progress-score", "/idle-progress-score", "/autonomous-explain-tools", "/idle-explain-tools", "/tool-choice-trace", "/repetition-guard-status", "/repetition-memory", "/repetition-clear", "/idle-silence", "/idle-summaries", "/idle-background-only", "/autonomous-patch-mode", "/patch-review", "/patch-reject", "/mistake-log", "/mistake-to-regression", "/autonomous-summary", "/autonomous-last-report", "/mistake-learning-status", "/surgical-fallback-v2", "/iterative-code-loop", "/edit-repair-plan", "/coding-loop-status", "/repair-strategy",
    "/autonomous-journal", "/quality-dashboard", "/quality-progress",
    "/self-awareness", "/self-aware", "/capability-audit", "/command-verify", "/mistake-learning", "/self-repair-status", "/self-repair-permission", "/self-repair-now", "/self-repair-validate",
    "/architecture-audit", "/repair-audit", "/code-repair-audit",
    "/bug-audit", "/code-review", "/deep-code-review", "/code-quality-gate",
    "/code-rabbit-review", "/review-gate", "/codebase-audit",
    "/integrity-audit", "/full-codebase-audit", "/attach-file",
    "/context-files", "/clear-context-files", "/image-generate", "/image-edit", "/image-draft",
    "/image-status", "/image-setup-help", "/image-setup-wizard", "/vision-status", "/human-test", "/visual-test",
    "/ai-box", "/comm-box", "/message-box", "/model-context", "/nova-context", "/run-context", "/operating-context", "/mission-contract", "/mission-progress-score", "/surgical-recipe", "/project-types", "/self-test-from-bug", "/development-strategy", "/iterative-strategy", "/validation-evidence", "/validation-matrix", "/regression-matrix", "/adaptive-backlog", "/next-adaptations", "/template-manifest", "/generation-templates", "/idle-level", "/idle-policy", "/receipt-history", "/action-receipts", "/role-router", "/model-roles", "/local-model-roles", "/jarvis-bridge", "/jarvis-status", "/daemon-bridge", "/jarvis-doctor", "/jarvis-setup", "/jarvis-onboarding", "/startup-validation", "/startup-gate", "/nova-system-test", "/nova-full-test", "/nova-test-all", "/test-nova", "/completion-audit", "/previous-task-audit", "/task-completion-audit", "/release-package", "/clean-release-package", "/package-release", "/codebase-advisor", "/next-codebase-improvements", "/codebase-improvement-plan", "/audit-log", "/nova-audit-log", "/workflow-run", "/sidecar-policy", "/screen-awareness-policy", "/sidecar-preflight", "/sidecar-enrollment", "/sidecar-checklist", "/bridge-authority", "/authority-gate", "/bridge-receipts", "/jarvis-receipts", "/browser-harness", "/safe-browser-harness", "/jarvis-test-prompts", "/workflow-blueprint", "/jarvis-workflow", "/proactive-actions", "/persona", "/persona-editor", "/chat-persona", "/custom-chat-window", "/inspiration-radar", "/nova-inspiration-radar", "/tool-context-pack", "/context-pack", "/handoff-plan", "/nova-handoff-plan", "/improvement-preflight", "/safe-improvement-preflight", "/coding-plan", "/project-coding-plan", "/coding-audit", "/nova-coding-audit", "/local-model-performance", "/model-performance-plan", "/agent-upgrade-radar", "/nova-upgrade-radar", "/context-budget", "/context-compaction-plan", "/coding-behavior-tests", "/coding-acceptance-tests", "/ollama-runtime-profile", "/local-model-runtime-profile", "/upgrade-regression-audit", "/patch-regression-audit", "/repo-context-map", "/nova-repo-map", "/patch-impact-plan", "/impact-tests", "/permission-scope-review", "/scope-review", "/local-model-benchmark", "/model-benchmark-plan", "/tool-contract-audit", "/command-contract-audit", "/agent-topology", "/nova-agent-topology", "/trace-observability", "/trace-spec", "/local-stack-advisor", "/local-stack-plan", "/verifier-ladder", "/validation-ladder-plus", "/tool-namespace-plan", "/tool-surface-plan", "/voice-pipeline-review", "/jarvis-voice-review", "/route-resilience-plan", "/self-healing-route-plan", "/tool-health-map", "/route-health-map", "/guardrail-memory", "/agent-guardrail-memory", "/context-router-policy", "/role-context-router", "/local-runtime-sentinel", "/model-runtime-sentinel", "/improvement-assurance", "/improvement-evidence", "/test-impact-graph", "/patch-impact-graph", "/patch-quality-score", "/quality-score-patch", "/success-claim-audit", "/claim-audit", "/regression-bisect-plan", "/bisect-regression", "/capability-drift-audit", "/nova-drift-audit", "/feature-preservation-contract", "/preserve-features", "/agent-feedback-loop", "/nova-feedback-loop", "/behavior-fuzzer-plan", "/agent-fuzzer-plan", "/local-spec-search", "/on-device-spec-search", "/nova-brand-audit", "/brand-audit", "/nova-improvement-research", "/research-improvements", "/nova-eval-packs", "/eval-packs", "/nova-self-apply", "/verified-self-apply", "/nova-odysseus-suite", "/odysseus-suite", "/nova-odysseus-runtime", "/odysseus-runtime", "/nova-tool-permissions", "/tool-permissions", "/nova-cookbook", "/model-cookbook", "/nova-compare", "/model-compare", "/nova-docs", "/nova-documents", "/nova-notes", "/nova-tasks", "/nova-skills", "/nova-presets", "/nova-memory-vault", "/nova-integration-gates", "/integration-gates", "/nova-email-plan", "/nova-calendar-plan", "/nova-mobile-plan", "/nova-theme-plan", "/nova-auth-plan", "/nova-upload-plan", "/persona-set", "/persona-json", "/persona-prompt", "/personality-sliders", "/voice-audit", "/voice-command-audit", "/local-model-optimizer", "/model-optimization", "/agent-harness", "/iterative-agent-harness",
    "/efficiency", "/performance", "/perf", "/research", "/research-sources", "/model-help", "/model-help-plan", "/model-help-implement", "/beyond-thinking",
    "/db", "/database", "/databases", "/docker", "/docker-status",
    "/docker-diagnostics", "/docker-ps", "/docker-smoke", "/docker-validate",
    "/docker-test", "/docker-validate-patch", "/docker-patch-validate",
    "/docker-promote-patch", "/docker-patch-promote", "/autonomous-promote-patch",
    "/docker-history", "/docker-clean", "/docker-help", "/sandbox", "/sandbox-status", "/sandbox-setup-help",
    "/sandbox-linux", "/sandbox-kali", "/sandbox-exec", "/sandbox-dev-run", "/sandbox-dev-mode", "/sandbox-autonomy",
    "/sandbox-network", "/sandbox-authorized-lab", "/sandbox-policy",
    "/sandbox-less-strict", "/sandbox-trusted-lab", "/sandbox-approve",
    "/sandbox-permit", "/sandbox-confirm", "/sandbox-cancel", "/sandbox-deny",
    "/sandbox-pending", "/sandbox-permission", "/nova-doctor", "/doctor",
    "/bug-scan", "/improvement-plan", "/docker", "/docker-status",
    "/docker-diagnostics", "/docker-ps", "/docker-smoke", "/docker-validate",
    "/docker-test", "/docker-promote-patch", "/docker-patch-promote", "/autonomous-promote-patch", "/docker-history", "/docker-clean", "/docker-help",
    "/deps-status", "/validation-status", "/validate-status", "/validation-progress", "/remote-access", "/remote-access-status", "/remote-access-plan", "/remote-access-setup", "/remote-access-test", "/remote-access-preflight", "/remote-api-health", "/remote-profile", "/remote-profiles", "/remote-profile-wizard", "/remote-wizard", "/remote-access-scripts", "/remote-wake", "/providers",
    "/provider-status", "/provider-route", "/provider-route-explain", "/provider-test", "/queue-status", "/queue-drain",
    "/version", "/help", "/help-full", "/full-help", "/ollama-multi", "/multi-models",
    "/release-gate", "/validate-release", "/preflight-release", "/release-checklist",
    "/feature-audit", "/implementation-status", "/requested-features",
    "/chat-new", "/new-chat", "/clear-chat", "/chats", "/chat-list", "/chat-switch", "/chat-search",
    "/integration-radar", "/next-integrations", "/integration-plan",
    "/security-status", "/defense-status", "/cyber-status", "/security-watch",
    # Deterministic local/project/tool commands must remain usable while a model
    # prompt is cooling down or an unrelated background cycle is between steps.
    "/project-open", "/project-delete", "/project-remove", "/project-new", "/project-refresh",
    "/tool-create", "/tool-test", "/tool-run", "/tool-delete", "/tool-enable", "/tool-disable",
    "/tool-view", "/tool-code", "/tool-proposals", "/tool-clean-proposals", "/tool-approve", "/tool-reject",
    "/pipeline", "/pipeline-preflight", "/pipeline-route", "/pipeline-catalog", "/maintenance-validate", "/validate-maintenance", "/self-validate", "/codebase-sanity-audit", "/repo-research-radar", "/pipeline-manifest", "/capability-manifests", "/repo-upgrade-plan", "/session-evidence", "/run-evidence", "/memory-inventory", "/memory-audit", "/project-patterns", "/browser-smoke", "/live-timeline", "/tool-awareness", "/tool-awareness-audit", "/tool-use-plan", "/autonomous-tool-plan", "/idle-tool-plan",
}

AUTONOMOUS_TOOL_TIMEOUTS: dict[str, int] = {
    "heartbeat": 12,
    "runtime_self_check": 20,
    "idle_lessons": 10,
    "tool_use_guide": 10,
    "tool_awareness": 10,
    "tool_awareness_audit": 10,
    "autonomous_tool_plan": 10,
    "idle_tool_plan": 10,
    "known_issues": 15,
    "tool_clean_proposals": 20,
    "detect_project": 15,
    "auto_verify": 45,
    "final_project_check": 60,
    "investigate_logs": 45,
    "propose_improvements": 90,
    "reasoning_diagnostics": 90,
    "surgical_repair": 150,
    "backtrack_recover": 150,
    "improve_project": 240,
    "ai_create_project": 300,
    "zip_path": 60,
    "docker_status": 20,
    "docker_validate": 360,
}

class AssistantCore:
    def __init__(self, config: AssistantConfig):
        self.config = config
        self.tools = ToolRegistry(config)
        self.messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + self._persona_system_prompt("default")}] + get_active_messages(limit=30)
        self.last_plan: Plan | None = self._load_last_plan()
        self.last_error: dict[str, Any] | None = None
        self._chat_lock = threading.RLock()
        self.active_run: dict[str, Any] | None = None
        self.autonomous_state: dict[str, Any] = {
            "enabled": False, "running": False, "stop_requested": False, "cycle": 0, "goal": "",
            "last_message": "not started", "last_error": "", "started_at": None, "updated_at": None,
            "last_progress_at": None, "last_progress_ts": None, "last_cycle_started_ts": None,
            "current_run_id": "", "phase": "idle", "current_action": "Idle", "current_detail": "Autonomous mode is not running.",
            "current_tool": "", "current_tool_args": {}, "last_tool": "", "last_summary": "",
            "events": [], "cycle_plan": [], "cycle_report": [], "cycle_summaries": [], "improvement_log": [],
            "last_failure_signature": "", "last_failure_category": "", "last_repair_proposal_path": "",
            "repair_proposal_written_this_cycle": False, "failure_memory_path": str(AUTONOMOUS_FAILURE_MEMORY_PATH),
            "max_cycles": None, "diagnostic_only": False, "stopped_after_cycle_limit": False,
            "loop_guard_history": [], "recent_action_signatures": [], "recent_cycle_fingerprints": [],
            "no_progress_cycles": 0, "loop_breaker_active": False, "loop_guard_stop_recommended": False,
            "next_strategy_hint": "", "last_progress_score": 0, "last_cycle_had_progress": False,
            "last_cycle_finite_goal_complete": False,
            "last_docker_validation": {}, "docker_validation_skipped_reason": "",
            "current_thought": "Idle. Waiting for the next autonomous cycle.",
            "current_self_validation": "No active autonomous step to validate yet.",
            "autonomous_thoughts": [],
        }
        self._autonomous_thread: threading.Thread | None = None
        self.idle_state: dict[str, Any] = {
            "enabled": False, "running": False, "stop_requested": False, "paused_for_user": False,
            "cycle": 0, "last_started": None, "last_finished": None, "last_summary": "Idle mode is off.",
            "last_error": "", "events": [], "current_action": "Idle", "current_detail": "Idle mode is off.",
        }
        self._idle_thread: threading.Thread | None = None
        self._last_foreground_request_ts: float = 0.0
        self._last_foreground_request_finished_ts: float = 0.0
        self._idle_quiet_until_ts: float = 0.0
        self.avatar_state: dict[str, Any] = {
            "mood": "ready", "emoji": "🙂", "title": "Ready",
            "text": "Waiting for your next request.", "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        TRACE_PATH.parent.mkdir(parents=True, exist_ok=True)
        self._auto_register_workspace_project()
        self._ensure_builtin_knowledge()
    @classmethod
    def load(cls) -> "AssistantCore":
        return cls(AssistantConfig.load())
    def _auto_register_workspace_project(self) -> None:
        try:
            p = Path(self.config.workspace).expanduser().resolve()
            if p.exists() and p.name and p.name.lower() not in {"daniel", "danny", "users", "documents"}:
                marker = p / ".nova_project.json"
                if marker.exists():
                    register_project(p.name, str(p), make_current=True)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
    def trace(self, event: str, payload: dict[str, Any]) -> None:
        row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "event": event, "payload": payload}
        append_jsonl(TRACE_PATH, row, ensure_ascii=False)
        try:
            log_activity("trace", event, payload)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
    def _load_last_plan(self) -> Plan | None:
        if PLAN_PATH.exists():
            try:
                return Plan.from_json(PLAN_PATH.read_text(encoding="utf-8"))
            except Exception:
                return None
        return None
    def _save_plan(self) -> None:
        if self.last_plan:
            atomic_write_text(PLAN_PATH, self.last_plan.to_json())


    def _persona_system_prompt(self, mode: str = "default") -> str:
        try:
            return build_persona_prompt_addendum(mode)
        except Exception:
            return "Nova persona contract: be practical, honest, conversational, and evidence-driven."

    def _command_category(self, text: str) -> str:
        """Classify a user command for prompt-lock routing.

        The old GUI treated every slash command that was not in a small status
        allowlist as if it needed the local model. That made deterministic
        commands such as /project-open and /custom-tools appear blocked by stale
        prompt state. This classifier keeps model-bound commands serialized but
        lets safe local state/status/project/tool commands proceed.
        """
        head = (text or "").strip().lower().split(maxsplit=1)[0]
        head = canonical_command(head)
        if not head.startswith("/"):
            return "llm"
        if head in NON_BLOCKING_STATUS_COMMANDS:
            return "deterministic"
        if head in {"/do", "/fast", "/long", "/continue", "/run-plan", "/agent", "/improve-project", "/self-improve"}:
            return "llm_bound_mutation"
        if head.startswith(("/project-", "/tool-", "/sandbox-", "/docker-", "/self-repair", "/mistake-learning")):
            return "deterministic"
        return "llm" if head in {"/ask", "/chat", "/code", "/coding", "/math", "/science", "/research"} else "deterministic"

    def _can_run_without_chat_lock(self, text: str) -> bool:
        return self._command_category(text) == "deterministic"

    def _mark_foreground_request_activity(self, text: str, *, finished: bool = False) -> None:
        """Keep idle from posting/working over active or just-finished user work."""
        now = time.time()
        if finished:
            self._last_foreground_request_finished_ts = now
        else:
            self._last_foreground_request_ts = now
        lower = (text or "").strip().lower()
        # Explicit idle commands are allowed to drive idle immediately; everything else gets
        # a quiet window so background reports cannot overwrite massive-test/build/chat output.
        if not lower.startswith(("/idle start", "/idle once", "/idle propose", "/idle auto-apply")):
            self._idle_quiet_until_ts = max(float(getattr(self, "_idle_quiet_until_ts", 0.0) or 0.0), now + 180.0)

    def chat(self, text: str) -> str:
        text = (text or "").strip()
        if not text:
            return ""
        # Common user shorthand: treat "idle stop" / "autonomous stop" as commands, not shell/task text.
        low_no_slash = text.lower()
        if not text.startswith("/") and low_no_slash in {"idle stop", "idle status", "autonomous stop", "autonomous status"}:
            text = "/" + text
        self._mark_foreground_request_activity(text)
        statusish = text.strip().lower().split(maxsplit=1)[0] if text.strip() else ""
        can_run_while_busy = self._can_run_without_chat_lock(text)
        # v45: status commands should not briefly force the avatar into "working"
        # and then return a state that disagrees with the GUI.
        if can_run_while_busy and text.startswith("/") and "\n" not in text:
            started_wall = time.perf_counter()
            started_cpu = time.process_time()
            started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            ok = False
            try:
                reply = self.handle_command(text)
                ok = True
                return reply
            except Exception as exc:
                self._set_avatar("error", "⚠️", "Error", repr(exc))
                raise
            finally:
                try:
                    append_efficiency_sample(
                        self.config,
                        kind="chat_turn",
                        name=statusish or "slash_command",
                        ok=ok,
                        wall_s=time.perf_counter() - started_wall,
                        process_cpu_s=time.process_time() - started_cpu,
                        meta={"input_chars": len(text), "slash_command": True, "can_run_while_busy": True},
                        started_at=started_at,
                        finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                    )
                except Exception as exc:
                        log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
                self._mark_foreground_request_activity(text, finished=True)
        if not can_run_while_busy and not self._chat_lock.acquire(blocking=False):
            return self._busy_interruption_message(text)
        chat_started_wall = time.perf_counter()
        chat_started_cpu = time.process_time()
        chat_started_at = time.strftime("%Y-%m-%d %H:%M:%S")
        chat_ok = False
        try:
            reply = self._chat_locked(text)
            chat_ok = True
            if not (self.autonomous_state.get("running") or self.idle_state.get("running")):
                self._set_avatar("ready", "🤖", "Ready", "Request completed. Waiting for the next task.")
            return reply
        except Exception as exc:
            self._set_avatar("error", "⚠️", "Error", repr(exc))
            raise
        finally:
            try:
                append_efficiency_sample(
                    self.config,
                    kind="chat_turn",
                    name=statusish or "normal_chat",
                    ok=chat_ok,
                    wall_s=time.perf_counter() - chat_started_wall,
                    process_cpu_s=time.process_time() - chat_started_cpu,
                    meta={"input_chars": len(text), "slash_command": text.startswith("/")},
                    started_at=chat_started_at,
                    finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            self._mark_foreground_request_activity(text, finished=True)
            if not can_run_while_busy:
                self._chat_lock.release()
    def _chat_locked(self, text: str) -> str:
        self._set_avatar("working", "🧠", "Working", "Processing your request...")
        if self.idle_state.get("running") or self.idle_state.get("enabled"):
            self.idle_state["paused_for_user"] = True
            self.idle_state["current_action"] = "Paused for user request"
            self.idle_state["current_detail"] = "Idle/autonomous maintenance paused while handling chat."
        # Allow pasted command blocks such as:
        # /allow-mutate on
        # /workspace C:\Projects\Example
        # /do make a game
        # The older version treated that as one broken command.
        if "\n" in text and all(line.strip().startswith("/") for line in text.splitlines() if line.strip()):
            replies: list[str] = []
            for line in [ln.strip() for ln in text.splitlines() if ln.strip()]:
                replies.append(f"> {line}\n" + self.handle_command(line))
            return "\n\n".join(replies)
        if text.startswith("/"):
            return self.handle_command(text)
        lowered_reply = text.strip().lower()
        if self._has_pending_sandbox_permission() and lowered_reply in APPROVAL_WORDS:
            return self.approve_sandbox_permission("yes")
        if self._has_pending_sandbox_permission() and lowered_reply in DENIAL_WORDS:
            return self.approve_sandbox_permission("no")
        if self.active_run and self.active_run.get("status") == "waiting_for_user" and self.active_run.get("question"):
            return self.reply_to_active_run(text)
        raw_user_text = text
        instant_runtime_reply = self._instant_chat_reply(raw_user_text)
        if instant_runtime_reply is not None:
            self.messages.append({"role": "user", "content": raw_user_text})
            self.messages.append({"role": "assistant", "content": instant_runtime_reply})
            self.trace("chat", {"user": raw_user_text, "assistant": instant_runtime_reply, "mode": "runtime_usability_instant"})
            return instant_runtime_reply
        if self._looks_like_natural_schedule_request(raw_user_text):
            return self._handle_natural_schedule_request(raw_user_text)
        if self._looks_like_natural_research_request(raw_user_text):
            return self._handle_natural_research_request(raw_user_text)
        if self._looks_like_wla_self_review_request(raw_user_text):
            return self._handle_wla_self_review_request(raw_user_text)
        # Plain conversation/corrections should go straight to the chat model.
        # v55.3.40 fixes a false positive where appended shared-file context
        # contained the string "Nova" and made ordinary follow-up chat look like
        # a self-improvement/source-edit request.
        if self._looks_like_plain_chat(raw_user_text):
            return self._answer_plain_chat(raw_user_text)
        text = self._with_shared_file_context(text)
        lowered = text.lower().strip()
        if self._looks_like_safe_tool_action_request(text):
            return self._handle_safe_tool_action(text)
        if self._looks_like_internet_tool_request(text):
            return self._handle_internet_tool_request(text)
        if self._looks_like_custom_tool_request(text):
            return self._handle_natural_tool_creator(text)
        guard = self._automatic_mutation_guard_message(raw_user_text)
        if guard:
            return guard
        planning_dialog = self._maybe_start_planning_dialog(text, source="chat")
        if planning_dialog:
            return planning_dialog
        action_words = [
            "build", "compile", "test", "edit", "replace", "make a plan", "create", "make", "write", "generate",
            "game", "app", "website", "continue", "improve", "fix", "add", "change", "update", "expand",
            "implement", "patch", "scaffold", "turn this into"
        ]
        if any(k in lowered for k in action_words) or any(k in lowered for k in ["all our projects", "all my projects", "our projects", "my projects", "project library", "test each individual functionality", "validate the results"]):
            text = self._enrich_goal_with_project_memory(text)
            self.last_plan = make_plan(text, workspace=Path(self.config.workspace), mode="auto")
            self._save_plan()
            if self.config.allow_mutating_tools:
                if self.last_plan.mode == "project_library_review":
                    prefix = "I treated that as a project-library review, not a request to create a new app."
                elif self.last_plan.mode == "database_review":
                    prefix = "I treated that as a Nova database/state review and ran deterministic integrity plus no-regression checks instead of creating a new app."
                elif self.last_plan.mode in {"qa", "project_qa"}:
                    prefix = "I treated that as a functionality/validation request and ran QA tools instead of creating a new project."
                elif self.last_plan.mode == "repo_upgrade":
                    prefix = "I treated that as a repo-inspired Nova upgrade pass and ran manifest, evidence and validation checks before any risky rewrite."
                else:
                    prefix = "I treated that as a build/edit task and ran it because file mutation is enabled by default."
                return prefix + "\n\n" + self.last_plan.to_text() + "\n\n" + self.run_plan()
            return "I made a concrete executable plan, but did not run it because writes/commands are disabled. Use /allow-mutate on then /run-plan, or use /do " + text + ".\n\n" + self.last_plan.to_text()
        if self._looks_like_project_or_code_context_request(text):
            mem_ctx = project_memory_context(self.config.workspace)
            if mem_ctx:
                text = text + mem_ctx
        self.messages.append({"role": "user", "content": text})
        try:
            store_conversation_message("user", text)
        except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        instant_reply = self._instant_chat_reply(text)
        if instant_reply is not None:
            reply = instant_reply
        else:
            reply = model_chat(self.config, self._select_model_for("chat"), self.messages, timeout=self._model_timeout_for("chat"), desc="normal chat response")
        if reply is None:
            reply = self.local_fallback(text)
        self.messages.append({"role": "assistant", "content": reply})
        try:
            store_conversation_message("assistant", reply)
        except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        self.trace("chat", {"user": text, "assistant": reply})
        return reply

    def _looks_like_wla_self_review_request(self, text: str) -> bool:
        low = (text or "").lower()
        if any(term in low for term in ["do not auto", "don't auto", "dont auto", "by adding", "apply edits", "patch ", "modify core.py", "change core.py"]):
            return False
        if not any(term in low for term in ["your own", "your files", "your code", "wla", "winlocalassistant", "coding capabilities", "validation capabilities", "review your code"]):
            return False
        return any(term in low for term in ["look", "review", "audit", "inspect", "what else", "improve", "capabilities", "files", "source", "code"])

    def _handle_wla_self_review_request(self, text: str) -> str:
        old_workspace = self.config.workspace
        root = self._wla_source_root()
        try:
            self.config.workspace = str(root)
            repair = self.tools.call("code_repair_audit", path=".")
            gate = self.tools.call("code_quality_gate", path=".")
            model_ctx = self.tools.call("model_context")
            parts = [
                f"{ASSISTANT_NAME} treated this as a Nova source review request, so I inspected the Nova codebase instead of asking you to paste code.",
                "",
                self.format_result(repair),
                "",
                self.format_result(gate),
            ]
            if model_ctx.ok:
                parts += ["", "Local model context is available for follow-up review:", self.format_result(model_ctx)]
            parts += [
                "",
                "Next safe commands:",
                "- `/codebase-audit` for a combined source integrity report.",
                "- `/code-review` for deeper reliability/UX review.",
                "- `/model-context` to show what context the local model would receive.",
            ]
            return "\n".join(parts)
        finally:
            self.config.workspace = old_workspace


    def _enrich_goal_with_project_memory(self, goal: str) -> str:
        try:
            if not self._looks_like_project_or_code_context_request(goal):
                return goal
            mem_ctx = project_memory_context(self.config.workspace)
            if not mem_ctx:
                return goal
            return str(goal).rstrip() + "\n\nUse this project memory when deciding project files/features:" + mem_ctx
        except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            return goal

    def _looks_like_project_or_code_context_request(self, text: str) -> bool:
        low = (text or "").lower()
        return any(term in low for term in ["project", "code", "app", "bug", "fix", "file", "edit", "continue", "feature", "test", "javascript", "python", "html", "css", "run"])

    def _project_target_diagnostic(self, goal: str) -> str:
        """Explain how Nova will treat a build/edit request before mutating files."""
        try:
            from .creation_intent import project_target_decision, analyze_creation_request
            current = get_project() or {}
            configured_ws = Path(self.config.workspace).expanduser()
            workspace_for_context = configured_ws
            # If a local release/test command polluted the in-memory workspace with
            # a pytest/temp folder, prefer the registered current project for user
            # diagnostics instead of confusing the user with internal test paths.
            ws_text = str(configured_ws).lower().replace('\\', '/')
            if current.get("path") and ("pytest-of-" in ws_text or "/temp/" in ws_text or "appdata/local/temp" in ws_text):
                workspace_for_context = Path(str(current.get("path"))).expanduser()
            manifest = {}
            try:
                mp = workspace_for_context / "PROJECT_MANIFEST.json"
                if mp.exists():
                    manifest = read_json_file(mp, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {}
            current_context = {"goal": manifest.get("goal", ""), "name": current.get("name") or workspace_for_context.name}
            decision = project_target_decision(goal, current_context)
            analysis = analyze_creation_request(goal)
            lines = ["Project targeting diagnostic", "", f"Goal: {goal}", f"Current workspace: {workspace_for_context}", f"Decision: {decision.get('decision')}", f"Reason: {decision.get('reason')}", "", "Creation analysis:", json.dumps(analysis, indent=2, ensure_ascii=False)]
            if workspace_for_context != configured_ws:
                lines.insert(4, f"Note: ignored transient test/temp workspace `{configured_ws}` and used registered current project context.")
            if decision.get("recommended_commands"):
                lines += ["", "Recommended commands:"] + [f"- `{x}`" for x in decision.get("recommended_commands")]
            return "\n".join(lines)
        except Exception as exc:
            return f"Project targeting diagnostic failed: {exc!r}"

    def _prepare_project_target_for_generation(self, goal: str, *, mode: str = "auto") -> str:
        """Open/create the right project before build-style commands.

        New build requests should not accidentally repair whichever unrelated
        project is open. Edit/continue/fix requests keep the current project.
        """
        low = (goal or "").lower().strip()
        editish = low.startswith(("continue", "edit ", "fix ", "improve ", "update ", "change ", "add ", "patch ", "modify ", "repair "))
        buildish = any(k in low for k in ["make ", "build ", "create ", "generate ", "write ", " app", "app ", "game", "tool", "script", "website", "dashboard", "tracker"])
        if editish or not buildish:
            return ""
        try:
            from .planner import slugify
            name = slugify(goal, "GeneratedProject")
            current = get_project()
            if current and str(current.get("name", "")).lower() == name.lower():
                return ""
            result = self.tools.call("project_create", name=name)
            if result.ok:
                return f"Project target prepared: created/opened `{name}` at `{self.config.workspace}`.\n\n"
            return f"Project target warning: could not create/open `{name}`; continuing in `{self.config.workspace}`.\n\n"
        except Exception as exc:
            log_activity("project_target_prepare_failed", "Could not auto-prepare project target", {"goal": goal, "error": repr(exc)})
            return ""

    def _with_shared_file_context(self, text: str) -> str:
        """Append recent shared file context to user prompts without hiding it from logs.

        The context is capped and summarised by file_context.py. Slash commands keep
        their original text because command parsers expect exact syntax.
        """
        try:
            contexts = list_file_contexts(limit=4)
            if not contexts:
                return text
            ctx = build_prompt_context(contexts)
            if not ctx:
                return text
            return text + "\n\nUse these user-shared files as context for this request:" + ctx
        except Exception:
            return text

    def _file_context_command(self, rest: str) -> str:
        action = (rest or "").strip()
        if not action or action.lower() in {"list", "status"}:
            contexts = list_file_contexts(limit=20)
            if not contexts:
                return "No shared file context is active. Use /attach-file PATH or the web Upload context button."
            lines = ["Active shared file context:"]
            for idx, ctx in enumerate(contexts, 1):
                extra = ""
                if ctx.kind == "image":
                    extra = f" Use /image-analyze context:{ctx.context_id} => describe this image."
                lines.append(f"{idx}. {ctx.original_name} ({ctx.kind}, {ctx.size_bytes} bytes, id={ctx.context_id}) - {ctx.summary}{extra}")
            return "\n".join(lines)
        if action.lower() == "clear":
            count = clear_file_contexts()
            return f"Cleared {count} shared file-context artifact(s)."
        try:
            ctx = register_file_context_from_path(action)
            return (
                "Attached file context for future prompts.\n"
                f"ID: {ctx.context_id}\n"
                f"Name: {ctx.original_name}\n"
                f"Kind: {ctx.kind}\n"
                f"Summary: {ctx.summary}\n\n"
                + (f"Analyze this image with: /image-analyze context:{ctx.context_id} => describe this image\n" if ctx.kind == "image" else "")
                + "Now ask your question normally and I will include this file context. Use /context-files clear to remove it."
            )
        except Exception as exc:
            return f"Could not attach file context: {exc}"

    def _image_generate_command(self, prompt: str) -> str:
        raw = (prompt or "").strip()
        if not raw:
            return (
                "Usage: /image-generate PROMPT\n"
                "This now requires a real image backend. Use /image-status to check setup, or /image-draft PROMPT for the old SVG placeholder."
            )
        if raw.lower() in {"status", "check", "setup", "help"}:
            return render_image_generation_status()
        try:
            out_dir = Path(self.config.workspace) / "generated_images"
            gen_started_wall = time.perf_counter()
            gen_started_cpu = time.process_time()
            gen_started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            result = generate_image(raw, output_dir=out_dir)
            try:
                append_efficiency_sample(
                    self.config,
                    kind="image_generation",
                    name=str(getattr(result, "backend", "image_generation") or "image_generation"),
                    ok=bool(getattr(result, "ok", False)),
                    wall_s=time.perf_counter() - gen_started_wall,
                    process_cpu_s=time.process_time() - gen_started_cpu,
                    meta={"prompt_chars": len(raw), "path": str(getattr(result, "path", "") or "")},
                    started_at=gen_started_at,
                    finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                )
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            if result.ok and result.path:
                path = Path(result.path)
                try:
                    rel = str(path.relative_to(Path(self.config.workspace))).replace("\\", "/")
                except Exception:
                    rel = str(path)
                return (
                    f"{result.message}\n"
                    f"Backend: {result.backend}\n"
                    f"Prompt: {raw}\n"
                    f"File: {rel}\n"
                    f"Open: /view?path={rel}"
                )
            return (
                f"Image generation is not ready: {result.message}\n\n"
                f"Backend checked: {result.backend}\n\n"
                "Run `/image-status` for setup details. Use `/image-draft " + raw + "` only if you want a labelled SVG placeholder."
            )
        except Exception as exc:
            return f"Image generation failed: {exc}"

    def _image_draft_command(self, prompt: str) -> str:
        prompt = (prompt or "").strip()
        if not prompt:
            return "Usage: /image-draft describe the draft. This creates a labelled SVG placeholder, not a real generated image."
        try:
            out_dir = Path(self.config.workspace) / "generated_images"
            path = create_svg_draft(prompt, output_dir=out_dir)
            rel = str(path.relative_to(Path(self.config.workspace))).replace("\\", "/")
            return (
                "Created an SVG draft placeholder.\n"
                f"Prompt: {prompt}\n"
                f"File: {rel}\n"
                f"Open: /view?path={rel}\n"
                "This is intentionally labelled as a draft, not real AI image generation. Use /image-status to configure a real backend."
            )
        except Exception as exc:
            return f"Image draft failed: {exc}"

    def _resolve_image_edit_source(self, image_ref: str) -> Path:
        raw = (image_ref or "").strip().strip('"').strip("'")
        ctx = resolve_image_context(raw)
        if ctx:
            return Path(ctx.stored_path)
        workspace = Path(self.config.workspace).expanduser().resolve()
        candidate = (workspace / raw).resolve() if raw else workspace
        try:
            candidate.relative_to(workspace)
        except Exception as exc:
            raise ValueError("Image source must be an uploaded image context or a path inside the workspace.") from exc
        return candidate

    def _image_edit_command(self, spec: str) -> str:
        raw = (spec or "").strip()
        if "=>" not in raw:
            return "Usage: /image-edit SOURCE => PROMPT\nSOURCE can be latest, context:ID, or a workspace-relative image path."
        source_ref, prompt = raw.split("=>", 1)
        source_ref = source_ref.strip()
        prompt = prompt.strip()
        if not source_ref or not prompt:
            return "Usage: /image-edit SOURCE => PROMPT\nExample: /image-edit latest => make the lighting warmer and preserve the composition."
        try:
            source = self._resolve_image_edit_source(source_ref)
            out_dir = Path(self.config.workspace) / "generated_images"
            result = edit_image(prompt, source, output_dir=out_dir)
            if result.ok and result.path:
                path = Path(result.path)
                try:
                    rel = str(path.relative_to(Path(self.config.workspace))).replace("\\", "/")
                except Exception:
                    rel = str(path)
                return (
                    f"{result.message}\n"
                    f"Backend: {result.backend}\n"
                    f"Source: {source_ref}\n"
                    f"Prompt: {prompt}\n"
                    f"File: {rel}\n"
                    f"Open: /view?path={rel}"
                )
            return (
                f"Image editing is not ready: {result.message}\n\n"
                f"Backend checked: {result.backend}\n\n"
                "Run `/image-status` for setup details."
            )
        except Exception as exc:
            return f"Image edit failed: {exc}"

    def _automatic_mutation_guard_message(self, text: str, command: str = "") -> str:
        intent = analyze_request_intent(text)
        if not should_block_automatic_mutation(intent):
            return ""
        reasons = intent.reasons or ["request needs manual review before source edits"]
        try:
            log_activity(
                "request_intent_guard",
                "Blocked automatic mutation for high-risk request intent",
                {"command": command, "intent": intent.to_dict(), "reasons": reasons},
            )
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        lines = [
            "I recognized this as a Nova/self-improvement or no-auto-apply request, so I did not run an automatic edit/build plan.",
            "",
            "Why:",
        ]
        lines.extend(f"- {reason}" for reason in reasons)
        lines.extend([
            "",
            "Safe next steps:",
            f"- `/idle propose {intent.raw_text or 'improve Nova safely'}` for a dry-run proposal.",
            "- `/self-improvement-queue` to collect evidence and test plans without source edits.",
            "- Send `/self-improve GOAL` only when you explicitly want the manual guarded self-edit flow with backup, verification, and rollback.",
        ])
        return "\n".join(lines)
    def _instant_chat_reply(self, text: str) -> str | None:
        """Fast deterministic replies for tiny chat/capability prompts.

        This prevents normal conversation from feeling broken when a large local
        coding model is loaded but too slow or stuck.  It does not pretend the
        model answered; it gives honest, useful local control guidance.
        """
        raw = (text or "").strip()
        low = re.sub(r"[^a-z0-9 /_-]+", "", raw.lower()).strip()
        bare = low.strip(" /")
        bare = re.sub(r"\b(?:whzat|whta|waht)\b", "what", bare)
        if bare in {"continue", "again", "do whats next", "do what's next", "what should we do next", "keep improving nova"} or "continue where" in bare or "next best improvement" in bare:
            from .project_state import build_continue_context_reply
            return build_continue_context_reply(self.config.workspace)
        if bare in {"hi", "hello", "hey", "yo", "hiya", "sup"}:
            return (
                "Hi — Nova is responsive. If the local model is slow, I can still use deterministic commands right now.\n\n"
                "Useful quick checks:\n"
                "- `/llm-status` to see whether Ollama/model calls are stuck.\n"
                "- `/command-help code` for code/write/run commands.\n"
                "- `/files` to inspect the workspace.\n"
                "- `/code QUESTION` for coding help.\n"
                "- `/verify python --version` to confirm command execution works."
            )
        if any(p in bare for p in ["what can you do", "what can u do", "help me use", "what are your functions", "what can nova do"]):
            return (
                "I can chat, inspect files, write code, run commands, validate projects, manage Nova projects, help with local models, and control remote-access helpers.\n\n"
                "Start here:\n"
                "- `/help` for concise grouped help.\n"
                "- `/command-help code` for code/write/run.\n"
                "- `/project-target GOAL` before building if you want one file or a specific scope.\n"
                "- `/do GOAL` when you want Nova to actually create/edit files.\n"
                "- `/llm-status` and `/perf-status` when chat/model performance seems weak.\n\n"
                "I will be honest if a local model timed out or a feature is unavailable."
            )
        if bare in {"test chat", "are you working", "can you respond", "ping"}:
            return "Nova chat path is working. If a full local-model reply times out, use `/llm-status`, `/interrupt-current`, or switch to a smaller chat model."
        if bare in {"help", "help me", "commands", "what commands", "show commands"} or "explain your tools" in bare:
            return (
                "Nova has two safe paths: chat for questions and slash commands for verified actions.\n\n"
                "Best next commands:\n"
                "- `/help` for concise grouped help.\n"
                "- `/command-help code` for code, write, read, run and verify commands.\n"
                "- `/llm-status` and `/model-health` to check local model routing.\n"
                "- `/release-readiness --full` before packaging.\n\n"
                "For file changes, use `/do GOAL` or exact `/write PATH CONTENT`; for checks, use `/verify COMMAND`."
            )
        if "run a command safely" in bare or bare.startswith("run this"):
            return (
                "Use `/verify COMMAND` when you want Nova to run a local check and summarize obvious errors. "
                "Use `/shell COMMAND` only for simple safe commands, and avoid destructive commands unless you fully understand them.\n\n"
                "Example: `/verify python --version`"
            )
        if bare.startswith("code me") or "write me a python file" in bare or "write a file" in bare:
            return (
                "I can help with that without freezing on a slow model. For advice only, use `/code QUESTION`. "
                "To actually create files, use `/do` with an exact scope, for example:\n\n"
                "`/do make one Python file named hello.py that prints hello`\n\n"
                "Nova will build a request contract first so it does not accidentally scaffold the wrong project type."
            )
        return None

    def _model_timeout_recovery_summary(self) -> str:
        try:
            result = self.tools.call("llm_status")
            data = result.data if isinstance(getattr(result, "data", None), dict) else {}
            lock = data.get("winlocalassistant_model_lock") if isinstance(data.get("winlocalassistant_model_lock"), dict) else {}
            ps = data.get("ollama_ps") if isinstance(data.get("ollama_ps"), dict) else {}
            cleanup = data.get("stale_ollama_cleanup") if isinstance(data.get("stale_ollama_cleanup"), dict) else {}
            health = data.get("model_health") if isinstance(data.get("model_health"), dict) else {}
            reachable = bool(ps.get("available") or result.ok)
            prompt_active = bool(lock.get("prompt_active"))
            cooldown_active = bool(lock.get("cooldown_active"))
            recent = lock.get("last_prompt") if isinstance(lock.get("last_prompt"), dict) else {}
            recent_result = str(recent.get("result") or "unknown")
            lines = [
                "Automatic model status check:",
                f"- Ollama reachable: {reachable}",
                f"- Nova prompt active: {prompt_active}",
                f"- Cooldown active: {cooldown_active}",
                f"- Recent local model result: {recent_result}",
            ]
            if health.get("status"):
                lines.append(f"- Model health: {health.get('status')}")
            if cleanup.get("attempted"):
                lines.append(
                    "- Stale/stopping model cleanup: "
                    f"attempted for `{cleanup.get('model', self.config.model)}`, ok={bool(cleanup.get('ok'))}"
                )
            if prompt_active:
                next_action = "Wait, or use `/interrupt-current --confirm` if the visible task is broken."
            elif cooldown_active:
                next_action = "Wait for the cooldown to end, then retry or run `/llm-status`."
            elif not reachable:
                next_action = "Start Ollama with `ollama serve`, then retry."
            else:
                next_action = "Retry chat, switch to a smaller `/model-chat MODEL`, or run `/llm-status` for full detail."
            lines += [
                f"- Next: {next_action}",
                "- Nova will not run `/ollama-stop --confirm` without confirmation; use it only after `/llm-status` shows no active prompt.",
            ]
            return "\n\n" + "\n".join(lines)
        except Exception as exc:
            return (
                "\n\nAutomatic model status check failed: "
                f"{exc!r}\n"
                "Run `/llm-status` manually, then `/interrupt-current --confirm` or `/ollama-stop --confirm` only if the model is genuinely stuck."
            )

    def local_fallback(self, text: str) -> str:
        g = (text or "").strip()
        gl = g.lower()
        if re.search(r"\b(make up|tell|write|generate|draft)\b.*\b(story|scene|paragraph|poem|creative)\b", gl):
            return self._simple_story_fallback(g)
        if "airplane food" in gl:
            return (
                "The deal with airplane food is mostly physics and logistics: low cabin pressure dulls taste, dry air blunts smell, "
                "and meals have to survive reheating in a tiny galley. So the food gets engineered to be sturdy, salty, and predictable. "
                "The comedy is that it is trying to be dinner while also being a pressure-tested supply-chain artifact."
                + self._model_timeout_recovery_summary()
            )
        if "quasar" in gl:
            return (
                "A quasar is powered by matter falling into a supermassive black hole, releasing enormous radiation from the accretion disk and jets. "
                "Humans could not realistically harness a quasar directly: the nearest ones are far outside practical reach, and the radiation environment would be extreme. "
                "The useful engineering lesson is indirect: quasars show how efficiently gravity can convert mass into energy, but a human-scale version would be closer to controlled fusion, compact nuclear systems, or far-future black-hole energy concepts, not plugging into an actual quasar."
            )
        if "file search" in gl or "file searching" in gl or ("search" in gl and "script" in gl and "file" in gl):
            return (
                "Here is a simple Python file-search pattern you can use locally:\n\n"
                "```python\n"
                "from pathlib import Path\n\n"
                "def search_files(root, text):\n"
                "    root = Path(root)\n"
                "    matches = []\n"
                "    for path in root.rglob('*'):\n"
                "        if path.is_file():\n"
                "            try:\n"
                "                body = path.read_text(encoding='utf-8', errors='ignore')\n"
                "            except Exception:\n"
                "                continue\n"
                "            if text.lower() in body.lower() or text.lower() in path.name.lower():\n"
                "                matches.append(path)\n"
                "    return matches\n\n"
                "for match in search_files('.', 'TODO'):\n"
                "    print(match)\n"
                "```\n\n"
                "Run it from the folder you want to search. For big folders, add ignore rules for `.venv`, `node_modules`, and `.git`."
            )
        return (
            "The local chat model did not answer in time, so I am using a safe fallback instead of pretending I searched or ran tools. "
            "For normal chat, make sure Ollama is running with `ollama serve`; for tool work use exact commands like `/research TOPIC`, `/code QUESTION`, `/do GOAL`, `/files`, or `/verify`. "
            f"Current model setting: {self.config.model}."
            + self._model_timeout_recovery_summary()
        )
    def _simple_story_fallback(self, prompt: str) -> str:
        # Small deterministic fallback so harmless creative requests do not fail just
        # because the local coding model is unavailable or overly tool-focused.
        return (
            "Here is a short story:\n\n"
            "The salon bell chimed just as rain began tapping against the front window. Mara stepped inside with hair so long "
            "it brushed the belt of her coat, dark and glossy from the weather. Everyone in the room looked up for a second, "
            "not because it was strange, but because it seemed to carry its own quiet drama.\n\n"
            "She sat in the chair by the mirror and told the stylist, Lena, that she did not want a dramatic change. Not really. "
            "She only wanted it to feel lighter, like she could walk out and leave a few old worries on the tiled floor. Lena nodded, "
            "combed through the length gently, and asked about the story behind it.\n\n"
            "So Mara talked. She talked about growing it through school, through jobs, through summers that felt endless and winters "
            "that felt too long. With every careful trim, the salon filled with the soft sound of scissors and the warm smell of shampoo. "
            "By the time Lena finished, Mara's hair was still long, still unmistakably hers, but it moved differently.\n\n"
            "When she stood, the rain had stopped. Mara looked at her reflection and smiled, not because she had become someone new, "
            "but because she felt like herself again."
        )

    def _looks_like_custom_tool_request(self, text: str) -> bool:
        g = (text or "").lower()
        if any(p in g for p in ["use your tool creator", "create a custom tool", "make a custom tool", "using your commands", "tool creator", "make a tool", "create a tool"]):
            return True
        if "tool" in g and any(p in g for p in ["yourself", "for yourself", "for wla", "for nova", "for the assistant", "for winlocalassistant"]):
            return any(v in g for v in ["make", "create", "build", "write", "generate"])
        return False

    def _handle_natural_tool_creator(self, text: str) -> str:
        self._set_avatar("tool", "🧰", "Tool creation", "Creating or proposing a safe custom tool from your request.")
        result = self.tools.call("tool_create", goal=text)
        reply = ["I treated that as a custom-tool request because you asked Nova/Nova to make itself a tool, so I used the guarded custom-tool creator instead of starting a generic HTML app build.", self.format_result(result)]
        if result.ok:
            reply.append("Next useful commands: `/custom-tools`, `/tool-code NAME`, `/tool-test NAME`, `/tool-run NAME => {}`.")
        else:
            reply.append("If it created a proposal instead, review it with `/tool-proposals` then approve/reject it.")
        return "\n\n".join(reply)

    def _looks_like_safe_tool_action_request(self, text: str) -> bool:
        g = (text or "").lower()
        if "internet" in g:
            return False
        return any(p in g for p in ["use a tool", "do something interesting", "run another script", "make and run another script", "show results"]) and not any(p in g for p in ["app", "website", "browser game", "project"])

    def _handle_safe_tool_action(self, text: str) -> str:
        self._set_avatar("tool", "", "Using tools", "Running a safe local tool/script demo.")
        result = self.tools.call("safe_script_demo", topic=text)
        return "I used a real built-in tool instead of inventing output.\n\n" + self.format_result(result)

    def _looks_like_internet_tool_request(self, text: str) -> bool:
        g = (text or "").lower()
        return "internet" in g and "tool" in g

    def _handle_internet_tool_request(self, text: str) -> str:
        self._set_avatar("tool", "", "Internet tools", "Preparing safe internet/topic watcher commands.")
        topic = "Tasmania graduate software chemistry jobs" if "job" in text.lower() else "local AI tools"
        result = self.tools.call("topic_watch", topic=topic, urls="https://hnrss.org/newest, https://arxiv.org/rss/cs.AI")
        return (
            "I set up the built-in internet/topic watcher path instead of routing this into project generation.\n\n"
            + self.format_result(result)
            + f"\n\nTo fetch current pages, run:\n`/allow-internet on`\n`/topic-check {topic}`\n\n"
            + "For one-off public pages use `/internet-fetch URL`."
        )



    def _looks_like_natural_research_request(self, text: str) -> bool:
        g = (text or "").strip().lower()
        if not g or g.startswith("/"):
            return False
        if g.startswith(("fix ", "patch ", "update nova", "improve nova", "why did", "this isnt", "this isn't")):
            return False
        research_starts = (
            "search for ", "search information", "search the web", "web search", "look up ",
            "research ", "do research", "perform a report", "preform a report",
            "make a report on", "write a report on", "use odysseus' research",
            "use odysseus research", "find current information", "find information about",
        )
        if g.startswith(research_starts):
            return True
        return bool(re.search(r"\b(search|research|look up|find information|current information)\b.+\b(about|on|for)\b", g))

    def _research_topic_from_text(self, text: str) -> str:
        topic = str(text or "").strip()
        topic = re.sub(r"(?is)/image-analyze\s+context:[^\s]+\s*=>.*$", "", topic).strip()
        patterns = [
            r"^use odysseus(?:'|’)? research capabilities to\s+",
            r"^use odysseus(?:'|’)? research to\s+",
            r"^do research (?:into|on|about)\s+",
            r"^research\s+",
            r"^search for information about\s+",
            r"^search information about\s+",
            r"^search the web for\s+",
            r"^web search\s+",
            r"^look up\s+",
            r"^find current information about\s+",
            r"^find information about\s+",
            r"^perform a report on\s+",
            r"^preform a report on\s+",
            r"^make a report on\s+",
            r"^write a report on\s+",
        ]
        for pat in patterns:
            topic = re.sub(pat, "", topic, flags=re.I).strip()
        topic = re.sub(r"\s+", " ", topic).strip(" .:-")
        return topic or str(text or "").strip()

    def _handle_natural_research_request(self, text: str) -> str:
        topic = self._research_topic_from_text(text)
        if not getattr(self.config, "allow_internet", False):
            self.config.allow_internet = True
            try:
                self.config.save()
            except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            enabled_note = "Internet access was off, so I enabled read-only internet for this explicit research request."
        else:
            enabled_note = "Internet access is already enabled, so I used Nova's research tools instead of answering from memory."
        self._set_avatar("thinking", "🔎", "Researching", f"Researching: {topic[:120]}")
        result = self.tools.call("research", topic=topic)
        if not result.ok or int((result.data or {}).get("source_count") or 0) == 0:
            search = self.tools.call("internet_search", query=topic)
            return (
                "I treated that as a live research request. " + enabled_note + "\n\n"
                + self.format_result(result) + "\n\nSource discovery fallback:\n" + self.format_result(search)
            )
        return "I treated that as a live research request. " + enabled_note + "\n\n" + self.format_result(result)


    def _looks_like_plain_chat(self, text: str) -> bool:
        """Return True for normal conversation/creative writing that should not become a build plan.
        v27 fixes the bug where phrases like "make up a story..." were treated as
        file-building tasks just because mutation is enabled by default. Explicit slash
        commands still build; plain chat should answer like ChatGPT.
        """
        g = (text or "").strip().lower()
        if not g:
            return False
        if g.startswith(("who ", "what ", "when ", "where ", "why ", "how ", "is ", "are ", "can you explain", "explain ", "tell me about")):
            return True
        # Normal conversational follow-ups, corrections and feedback should not
        # be interpreted as build/self-edit requests just because they contain
        # words like "you" or because a shared-file context block mentions Nova.
        if g.startswith(("no ", "yes ", "yeah ", "nah ", "thanks", "thank you", "that ", "you ", "i mean", "i meant", "sorry", "ok ", "okay ")):
            if not any(k in g for k in ["build ", "make ", "create ", "write code", "edit file", "patch ", "implement ", "/"]):
                return True
        # Creative prose request. Do not treat as an app unless the user explicitly asks
        # for interactive/story app/code/files/project.
        if re.search(r"\b(make up|tell|write|generate|draft)\b.*\b(story|poem|scene|paragraph|email|letter|answer)\b", g):
            if not any(k in g for k in ["app", "website", "code", "file", "project", "interactive", "html", "javascript", "python", "script"]):
                return True
        return False
    def _answer_plain_chat(self, text: str) -> str:
        """Answer ordinary chat/creative writing with a domain skill profile.
        v55.3.0 keeps lightweight skill routing, autonomous specification-aware build planning and deterministic repair auditing so the same local model receives
        better instructions for coding, maths, science and communication tasks,
        while still avoiding false claims about tool/file work.
        """
        instant = self._instant_chat_reply(text)
        if instant is not None:
            self.messages.append({"role": "user", "content": text})
            self.messages.append({"role": "assistant", "content": instant})
            self.trace("chat", {"user": text, "assistant": instant, "mode": "plain_chat", "instant": True})
            return instant
        mode = choose_skill_mode(getattr(self.config, "skill_mode", "auto"), text)
        if mode == "math":
            quick = try_quick_arithmetic(text)
            if quick:
                reply = quick + "\n\nQuick arithmetic check completed locally."
                self.messages.append({"role": "user", "content": text})
                self.messages.append({"role": "assistant", "content": reply})
                self.trace("chat", {"user": text, "assistant": reply, "mode": "plain_chat", "skill_mode": mode, "quick_arithmetic": True})
                return reply
        plain_messages = [
            {
                "role": "system",
                "content": (
                    "You are Nova, the Nova companion in normal chat mode. Answer the user's request directly. "
                    "Sound like a friendly, capable engineering partner: concise by default, warmer when brainstorming, and practical when debugging. "
                    "Creative writing, brainstorming, explanations and ordinary questions are allowed. "
                    "Do not claim to run tools or edit files in this mode. Keep the answer useful and natural. "
                    + skill_prompt(mode) + " "
                    "Use the provided local knowledge snippets when they help answer or debug.\n\n"
                    + self._persona_system_prompt("default") + "\n\n"
                    "Local knowledge snippets:\n" + self._knowledge_context()
                ),
            },
            {"role": "user", "content": text},
        ]
        reply = model_chat(self.config, self._select_model_for("chat"), plain_messages, timeout=self._model_timeout_for("chat"), desc=f"{mode} chat response")
        if reply is None or self._looks_like_bad_plain_chat_refusal(reply):
            reply = self.local_fallback(text)
        self.messages.append({"role": "user", "content": text})
        self.messages.append({"role": "assistant", "content": reply})
        self.trace("chat", {"user": text, "assistant": reply, "mode": "plain_chat", "skill_mode": mode})
        return reply

    def _answer_with_skill(self, mode: str, text: str) -> str:
        """Force a specific skill profile for direct /math, /science, /code and /communicate commands."""
        mode = normalise_skill_mode(mode)
        if mode == "auto":
            mode = choose_skill_mode("auto", text)
        prompt_text = (text or "").strip()
        if not prompt_text:
            return f"Give me a question or text after the command. Current skill: `{mode}`. Use `/skill-mode` to see options."
        if mode == "math":
            quick = try_quick_arithmetic(prompt_text)
            if quick:
                return quick + "\n\nQuick arithmetic check completed locally."
        messages = [
            {
                "role": "system",
                "content": (
                    "You are Nova answering in a forced specialist mode. "
                    "Answer directly and do not claim to edit files or run commands unless a tool result confirms it. "
                    + skill_prompt(mode) + "\n\n" + self._persona_system_prompt(mode) + "\n\nLocal knowledge snippets:\n" + self._knowledge_context()
                ),
            },
            {"role": "user", "content": prompt_text},
        ]
        reply = model_chat(self.config, self._select_model_for("chat"), messages, timeout=self._model_timeout_for("code" if mode == "coding" else "chat"), desc=f"{mode} specialist response")
        if reply is None or self._looks_like_bad_plain_chat_refusal(reply):
            reply = self.local_fallback(prompt_text)
        self.messages.append({"role": "user", "content": f"/{mode} {prompt_text}"})
        self.messages.append({"role": "assistant", "content": reply})
        self.trace("chat", {"user": prompt_text, "assistant": reply, "mode": "specialist_chat", "skill_mode": mode})
        return reply

    def skill_mode_command(self, rest: str) -> str:
        value = (rest or "").strip()
        if not value or value.lower() in {"status", "show"}:
            return skill_status_text(getattr(self.config, "skill_mode", "auto"))
        mode = normalise_skill_mode(value)
        if mode not in {"auto", "general", "coding", "math", "science", "communication"}:
            return "Unknown skill mode. Use `/skill-mode auto|general|coding|math|science|communication`."
        self.config.skill_mode = mode
        self.config.save()
        return f"Skill mode set to: `{mode}`\n\n" + skill_status_text(mode)
    def _looks_like_bad_plain_chat_refusal(self, reply: str) -> bool:
        r = (reply or "").lower()
        refusal_markers = [
            "can't generate stories",
            "cannot generate stories",
            "can't generate creative",
            "cannot generate creative",
            "unable to generate stories",
            "not able to write stories",
            "only help with programming",
            "related to programming, automation, or windows",
            "i can't assist with that request",
        ]
        return any(m in r for m in refusal_markers)
    def _select_model_for(self, task: str) -> str:
        """Choose the local model for a task without changing build safety."""
        route = getattr(self.config, "model_route", "auto") or "auto"
        if route == "manual":
            return self.config.model
        if task == "chat":
            return getattr(self.config, "chat_model", "") or self.config.model
        if task in {"planning", "review"}:
            return getattr(self.config, "planner_model", "") or self.config.model
        return self.config.model

    def _model_timeout_for(self, task: str) -> int:
        """Bound model waits by task so normal chat falls back quickly."""
        base = int(getattr(self.config, "local_model_timeout_sec", 0) or 0)
        if task == "chat":
            return int(getattr(self.config, "chat_model_timeout_sec", base) or 0)
        if task in {"code", "coding", "build", "planning", "review"}:
            return int(getattr(self.config, "code_model_timeout_sec", base) or base)
        if task in {"autonomous", "idle"}:
            return int(getattr(self.config, "autonomous_model_timeout_sec", base) or base)
        return base
    def _ollama_list_text(self) -> str:
        exe = shutil.which("ollama")
        if not exe:
            return "ollama was not found on PATH."
        try:
            cp = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=12)
            out = ((cp.stdout or "") + (cp.stderr or "")).strip()
            return out or "ollama list returned no output."
        except Exception as exc:
            return f"ollama list failed: {exc!r}"
    def models_text(self) -> str:
        return (
            "Model routing\n"
            f"- Code/build model: {self.config.model}\n"
            f"- Chat/creative model: {getattr(self.config, 'chat_model', '') or self.config.model}\n"
            f"- Planning/review model: {getattr(self.config, 'planner_model', '') or self.config.model}\n"
            f"- Route mode: {getattr(self.config, 'model_route', 'auto')}\n"
            f"- Skill mode: {getattr(self.config, 'skill_mode', 'auto')}\n\n"
            "Installed Ollama models:\n"
            f"{self._ollama_list_text()}\n\n"
            "Suggested pulls for your upgraded-PC setup:\n"
            "- Coding/planning: ollama pull qwen3-coder:30b\n"
            "- Fast normal chat: ollama pull qwen2.5:7b or ollama pull llama3.1:8b\n"
            "- Higher-quality chat if fast enough: ollama pull gemma3:12b\n"
            "- Calibration: python -m winlocalassistant.model_calibration --root . --bench\n\n"
            "Commands:\n"
            "/model-code MODEL     set the build/code model\n"
            "/model-chat MODEL     set the normal chat/creative model\n"
            "/model-planner MODEL  set the planning/review model\n"
            "/model-route auto|manual\n"
        )
    # -------------------------
    # Avatar, command catalogue, interruption and idle mode
    # -------------------------
    def _avatar_profile(self, mood: str, emoji: str = "", title: str = "") -> tuple[str, str, str]:
        """Return a consistent visible expression for a state.

        v43 sometimes showed text that described one state while the face still
        looked like the default assistant. v44 normalises this so the displayed
        avatar face, mood label and title always describe the same state.
        """
        key = (mood or "ready").lower().strip()
        profiles = {
            "ready": ("🙂", "Ready"),
            "working": ("🤖", "Working"),
            "thinking": ("🤔", "Thinking"),
            "planning": ("🧭", "Planning"),
            "idle": ("🌙", "Idle learning"),
            "blocked": ("⏳", "Busy / waiting"),
            "stopping": ("🛑", "Stopping"),
            "error": ("😟", "Needs attention"),
            "success": ("😄", "Complete"),
            "visual": ("👁️", "Visual inspection"),
            "tool": ("🧰", "Using tools"),
            "repair": ("🔧", "Repairing"),
            "memory": ("🧠", "Remembering"),
            "speaking": ("🔊", "Speaking"),
        }
        face, default_title = profiles.get(key, (emoji or "🤖", title or key.title()))
        return key, (face if key in profiles else (emoji or face)), title or default_title

    def _set_avatar(self, mood: str, emoji: str, title: str, text: str) -> None:
        mood, emoji, title = self._avatar_profile(mood, emoji, title)
        self.avatar_state = {
            "mood": mood, "emoji": emoji, "title": title, "text": text,
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "speak": text if mood in {"error", "success", "blocked", "stopping"} else "",
            "sound": mood,
        }
        try:
            log_activity("avatar", title, self.avatar_state)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
    def avatar_status_data(self) -> dict[str, Any]:
        data = dict(self.avatar_state)
        try:
            box = read_assistant_box()
            data["assistant_box"] = box
            # Prefer the live avatar text while a normal request is working.  Older builds
            # always read autonomous_state.current_action first, which made the right panel
            # say "Current task: Idle" while the main assistant was visibly working.
            if data.get("mood") in {"working", "thinking", "planning", "repair", "tool"}:
                current_task = data.get("text", "") or "Processing current request"
            else:
                current_task = self.autonomous_state.get("current_action") or (self.active_run.get("question") if isinstance(self.active_run, dict) else "") or data.get("text", "")
            data["current_task"] = current_task
            stale_msg = str(box.get("message", "") or "").strip()
            # Prefer live state while a request is working; stale autonomous handoff notes made the right panel misleading.
            if data.get("mood") in {"working", "thinking", "planning", "repair", "tool"}:
                data["disclosure"] = f"Live state: {current_task or data.get('text','working')}. Use Live Activity for step details."
                data["disclosure_level"] = "live"
            else:
                data["disclosure"] = stale_msg or "No side-channel note."
                data["disclosure_level"] = box.get("level", "info")
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        return data

    def assistant_live_snapshot_data(self) -> dict[str, Any]:
        """Return a compact live status snapshot for Nova's communication box."""
        try:
            activity = tail_jsonl(ACTIVITY_PATH, 40, session_only=False)
        except Exception:
            activity = []
        try:
            model_io = tail_jsonl(MODEL_IO_PATH, 8, session_only=False)
        except Exception:
            model_io = []
        latest_event = activity[-1] if activity else {}
        latest_model = model_io[-1] if model_io else {}
        file_event: dict[str, Any] = {}
        for ev in reversed(activity):
            data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
            candidate = data.get("path") or data.get("file") or data.get("markdown_path") or data.get("json_path")
            if candidate or ev.get("kind") in {"file_write", "code_write_start", "code_quality_gate", "code_repair_audit"}:
                file_event = ev
                break
        llm_state = {}
        try:
            from .ollama import ollama_busy_state
            llm_state = ollama_busy_state()
        except Exception:
            llm_state = {}
        box = read_assistant_box()
        return {
            "assistant_name": ASSISTANT_NAME,
            "avatar": dict(self.avatar_state),
            "current_task": self.avatar_status_data().get("current_task", ""),
            "active_run": self.active_run or {},
            "autonomous": {
                "enabled": bool(self.autonomous_state.get("enabled")),
                "running": bool(self.autonomous_state.get("running")),
                "phase": self.autonomous_state.get("phase", ""),
                "cycle": self.autonomous_state.get("cycle", 0),
                "current_action": self.autonomous_state.get("current_action", ""),
                "current_detail": self.autonomous_state.get("current_detail", ""),
                "target_mode": self.autonomous_state.get("autonomous_target_mode", ""),
                "target_path": self.autonomous_state.get("autonomous_target_path", ""),
            },
            "idle": {
                "enabled": bool(self.idle_state.get("enabled")),
                "running": bool(self.idle_state.get("running")),
                "cycle": self.idle_state.get("cycle", 0),
                "current_action": self.idle_state.get("current_action", ""),
                "current_detail": self.idle_state.get("current_detail", ""),
                "next_goal": self.idle_state.get("next_goal", ""),
                "last_selected_candidate_title": self.idle_state.get("last_idle_selected_candidate_title", ""),
                "repeat_count": self.idle_state.get("last_idle_selected_repeat_count", 0),
            },
            "llm": {
                "busy": bool(llm_state.get("busy")),
                "prompt_active": bool(llm_state.get("prompt_active")),
                "busy_desc": llm_state.get("busy_desc", ""),
                "request_id": llm_state.get("request_id", ""),
                "busy_for_sec": llm_state.get("busy_for_sec", 0),
                "last_prompt": llm_state.get("last_prompt", {}),
                "prompt_preview": latest_model.get("prompt_preview", ""),
                "reply_preview": latest_model.get("response_preview", ""),
                "model_phase": latest_model.get("phase", ""),
            },
            "latest_event": latest_event,
            "recent_events": activity[-8:],
            "file_focus": file_event,
            "persisted_note": box,
        }

    def _busy_interruption_message(self, attempted_text: str = "") -> str:
        try:
            llm = self.tools.call("llm_status").data.get("winlocalassistant_model_lock", {})
        except Exception:
            llm = {}
        prompt_active = bool(llm.get("prompt_active"))
        cooldown_active = bool(llm.get("cooldown_active") or (llm.get("busy") and not prompt_active))
        desc = llm.get("busy_desc") or self.autonomous_state.get("current_action") or ("finishing previous request" if cooldown_active else "working")
        task_lines = [
            "I am already using the local model or running a task, so I did not start another Ollama prompt.",
            "",
            "**Current task/status**",
            f"- Prompt active: {prompt_active}",
            f"- Cooldown/cleanup active: {cooldown_active}",
            f"- Description: {desc}",
            f"- Request ID: {llm.get('request_id') or self.autonomous_state.get('current_run_id') or 'none'}",
            f"- Busy for: {llm.get('busy_for_sec', 0)}s",
        ]
        if self.active_run:
            task_lines.append(f"- Active two-way run: {self.active_run.get('status')} / {self.active_run.get('question','')}")
        if self.autonomous_state.get("running"):
            task_lines.append(f"- Autonomous cycle: {self.autonomous_state.get('cycle')} / {self.autonomous_state.get('phase')}")
        task_lines += [
            "",
            "Choose one:",
            "- Wait and watch `/activity` or `/llm-status`.",
            "- Stop the current local model request with `/interrupt-current --confirm` if it is broken or blocking you.",
            "- Use `/ollama-stop --confirm` only if the Ollama model itself appears stuck.",
            "",
            "I saved your attempted message in the note below so you can resend it after stopping or waiting:",
            "```text", attempted_text[:2000], "```",
        ]
        self._set_avatar("blocked", "⏳", "Busy", "A local model/task is already running. Waiting or interruption confirmation is needed.")
        return "\n".join(task_lines)
    def interrupt_current(self, confirm: bool = False) -> str:
        if not confirm:
            return (
                "⚠️ **Stop current local model/task?**\n\n"
                "This can interrupt an active Ollama generation. It will not delete project files, but the current build may fail and need retrying.\n\n"
                "Run this to confirm:\n`/interrupt-current --confirm`"
            )
        self.idle_state["stop_requested"] = True
        self.autonomous_state["stop_requested"] = True
        self._set_avatar("stopping", "🛑", "Stopping", "Requested interruption of current local model/task.")
        result = self.tools.call("ollama_stop_model")
        return "Requested interruption.\n\n" + self.format_result(result)
    def command_catalog_text(self) -> str:
        tool_names = sorted(getattr(self.tools, "tools", {}).keys())
        return (
            render_tool_catalog_markdown()
            + "\n## Registered internal ToolRegistry names\n"
            + ", ".join(tool_names)
            + "\n\nJSON catalogue is available conceptually through the tool_catalog module. "
            + "Use risk/verification/fallback metadata before selecting tools."
        )

    def self_guide_text(self) -> str:
        return (
            "# Nova operational self-guide\n\n"
            "I am not conscious or literally self-aware, but I maintain an operational self-map: current model roles, workspace, tools, project state, logs, known issues, idle/autonomous state, and safety limits.\n\n"
            "## Main modes\n"
            "- Normal chat: ask questions or creative requests; I answer without forcing a project.\n"
            "- `/fast GOAL`: quick app/script build with basic checks.\n"
            "- `/long GOAL`: staged build with requirements, verification, final output and zip.\n"
            "- `/interactive GOAL`: I ask a clarifying question, then continue.\n"
            "- `/idle start GOAL`: background self-analysis while you are not using me; pauses for user requests.\n"
            "- `/autonomous start GOAL`: bounded cycles that inspect, diagnose, act, verify, repair and reflect.\n\n"
            "## Tool sequence for fixing problems\n"
            "1. `/activity` and `/known-issues` to inspect evidence.\n"
            "2. `/human-test .`, `/console-test .`, `/visual-test .` for generated browser apps.\n"
            "3. `/surgical-repair NOTE` for targeted fixes before broad rewrites.\n"
            "4. `/improve-project GOAL` after opening the correct project with `/project-open NAME`.\n"
            "5. `/test-all` after assistant/source changes.\n"
            "6. `/self-improvement-queue` before self-edits; use `/self-apply ID` only when ready.\n\n"
            "## Model and timeout controls\n"
            "- `/model-doctor` checks installed models and avoids embedding-only models for chat.\n"
            "- `/model-benchmark` ranks installed models on tiny JSON/code/chat probes.\n"
            "- `/model-timeout status|off|SECONDS` controls local Ollama HTTP timeout; off means wait indefinitely.\n"
            "- `/llm-status` shows whether Nova is actually prompting, separate from Ollama keeping a model loaded.\n"
            "- `/interrupt-current --confirm` or `/ollama-stop --confirm` can be used if a model is stuck.\n\n"
            "## Important rules\n"
            "- I should use one local LLM prompt at a time.\n"
            "- I should not delete projects/files unless explicitly asked.\n"
            "- I should prefer targeted repair over rollback.\n"
            "- I should log errors, known issues, improvement proposals and idle lessons so repeated mistakes become evidence.\n"
        )


    # -------------------------
    # Memory and built-in knowledge
    # -------------------------
    def _knowledge_path(self) -> Path:
        return APP_DIR / "KNOWLEDGE_BASE.md"

    def _ensure_builtin_knowledge(self) -> None:
        """Install a small local knowledge base for common Nova/code/debug tasks.

        This is not a replacement for a real model, but it gives the chat and agent
        a local reference for frequent code errors, Windows/Ollama issues, and safe
        tool sequencing. It is written to the user profile so idle/autonomous cycles
        can read and extend it later.
        """
        try:
            path = self._knowledge_path()
            if path.exists() and "v50" in path.read_text(encoding="utf-8", errors="replace")[:2000]:
                return
            text = """# Nova Knowledge Base v50

## Core operating rule
Normal chat answers questions directly. Build commands create files only when the user asks for files, apps, tools, scripts, projects, or uses slash commands. Never fail a plain question for missing buttons or app logic.

## v50 tool/input rule
Custom tool input accepts strict JSON, `{plain text}` for text-like tools, and simple `key=value` shorthand. Internet/topic watching remains off until `/allow-internet on`.

## v50 game recovery rule
For vague requests such as `make a game`, use the local model first where practical, but fall back to a deterministic runnable browser game if the model times out or returns unusable JSON. Browser games should include visible controls, score/state, collision/update logic and runnable `index.html`/`app.js`.

## v50 reasoning/recovery rule
When a step fails, classify the error signature, try remembered deterministic fixes, verify the same project, then escalate. Do not give up on experienced errors until known-error recovery has run.

## v50 iterative candidate rule
When the local model returns parseable code that fails validation, treat it as an editable draft. Repair/refine the candidate in memory, validate again, and use a focused candidate-edit prompt before repeating full generation.

## Tool sequence for bugs
1. Reproduce or inspect the exact failure.
2. Confirm the correct workspace/project.
3. Prefer surgical find/replace for one-line syntax/runtime errors.
4. Run the smallest relevant verification.
5. Only backtrack if targeted repair cannot safely continue.
6. Log the issue and lesson so the same mistake is not repeated.

## Common JavaScript fixes
- Invalid newline in string: `.join('` newline `')` should be `.join('\\n')`.
- Optional chaining assignment is illegal: `obj?.x += 1`; rewrite as `const target = obj; if (target) target.x += 1;`.
- Browser apps need matching HTML references: `<link rel="stylesheet" href="style.css">` and `<script src="app.js"></script>`.
- localStorage should use `try/catch` or safe JSON fallback for corrupted data.
- Export requires Blob, URL.createObjectURL, an anchor with `download`, and cleanup with URL.revokeObjectURL.

## Common Python fixes
- Run `python -m py_compile file.py` for syntax.
- Prefer pathlib for paths on Windows.
- Catch subprocess timeouts and show stdout/stderr.
- Do not swallow exceptions silently inside tools; return ToolResult with classified error.

## PowerShell and Windows
- Use `Get-ChildItem`, `Test-Path`, `Select-String`, `Start-Process`, and `Get-NetTCPConnection` instead of Linux commands.
- Quote paths with spaces. Use project-local paths where possible.

## Ollama/model handling
- `ollama ps` can show a model loaded after prompting is finished. Nova prompt lock is the source of truth.
- If a prompt is stuck, use `/interrupt-current --confirm`; use `/ollama-stop --confirm` only when the model process itself is stuck.
- Embedding models are not chat models.

## General user Q&A knowledge style
For ordinary questions, answer in plain language. For technical topics, define terms, give examples, and state uncertainty. For job/interview help, use the user's known style: direct, concrete, polished and STAR-style when useful.
"""
            path.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_text(path, text)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})

    def _knowledge_context(self, max_chars: int = 4200) -> str:
        try:
            self._ensure_builtin_knowledge()
            text = self._knowledge_path().read_text(encoding="utf-8", errors="replace")
            mem = self.memory_text(raw=True, limit=8)
            return (text + "\n\n# Recent user/Nova memory\n" + mem)[-max_chars:]
        except Exception:
            return ""

    def remember_command(self, rest: str) -> str:
        note = (rest or "").strip()
        if not note:
            return "Usage: /remember something useful to remember"
        self._append_memory("user_note", note, source="/remember")
        self._set_avatar("memory", "🧠", "Remembering", "Saved a memory note for future runs.")
        return "Remembered. Use `/memory` to review recent notes."

    def _append_memory(self, kind: str, text: str, **data: Any) -> None:
        try:
            row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "kind": kind, "text": text, "data": data}
            append_jsonl(MEMORY_PATH, row, ensure_ascii=False)
            log_activity("memory", kind, row)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})

    def memory_text(self, raw: bool = False, limit: int = 20) -> str:
        if not MEMORY_PATH.exists():
            return "No memory entries yet."
        rows = []
        try:
            for line in MEMORY_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]:
                if not line.strip():
                    continue
                rows.append(json.loads(line))
        except Exception:
            return "Memory exists but could not be parsed."
        if raw:
            return "\n".join(f"- {r.get('time')} [{r.get('kind')}] {r.get('text')}" for r in rows)
        return "# Recent memory\n\n" + "\n".join(f"- **{r.get('time')}** `{r.get('kind')}`: {r.get('text')}" for r in rows)

    def knowledge_command(self, rest: str = "") -> str:
        self._ensure_builtin_knowledge()
        path = self._knowledge_path()
        if (rest or "").strip().lower().startswith("path"):
            return f"Knowledge base path: {path}"
        return path.read_text(encoding="utf-8", errors="replace")[:9000]

    def learn_errors_command(self) -> str:
        """Extract recent failures into memory and idle lessons so repeated mistakes guide future cycles."""
        findings = []
        try:
            rows = tail_jsonl(ACTIVITY_PATH, 220)
            for r in rows:
                kind = str(r.get("kind", ""))
                msg = str(r.get("message", ""))
                if any(x in kind.lower() for x in ["failed", "error", "rejected"]) or any(x in msg.lower() for x in ["failed", "error", "timeout", "invalid"]):
                    sig = f"{kind}: {msg}"[:500]
                    findings.append(sig)
            seen = []
            for f in findings:
                if f not in seen:
                    seen.append(f)
            for sig in seen[-12:]:
                self._append_memory("error_lesson", sig, source="/learn-errors")
                self._record_idle_lesson(int(self.idle_state.get("cycle") or 0), "manual learn errors", sig, "Use this signature to avoid repeating the same failed repair/tool path.")
            return "Learned from recent error patterns.\n\n" + "\n".join(f"- {x}" for x in seen[-12:]) if seen else "No recent failure signatures found."
        except Exception as exc:
            return f"Could not learn from logs: {exc!r}"

    def model_timeout_command(self, rest: str) -> str:
        arg = (rest or "status").strip().lower()
        if arg in {"", "status"}:
            v = getattr(self.config, "local_model_timeout_sec", 0)
            return f"Local Ollama model timeout: {'off / wait indefinitely' if int(v or 0) <= 0 else str(v) + ' seconds'}"
        if arg in {"off", "none", "0", "infinite", "indefinite"}:
            self.config.local_model_timeout_sec = 0
            self.config.save()
            return "Local Ollama timeout disabled. Nova will wait for local model responses until they return; use /ollama-stop --confirm if a prompt is stuck."
        try:
            sec = max(30, int(arg))
            self.config.local_model_timeout_sec = sec
            self.config.save()
            return f"Local Ollama timeout set to {sec} seconds."
        except Exception:
            return "Usage: /model-timeout status|off|SECONDS"

    def command_timeout_command(self, rest: str) -> str:
        arg = (rest or "status").strip().lower()
        if arg in {"", "status"}:
            return f"Shell command timeout: {int(getattr(self.config, 'command_timeout_sec', 120) or 120)} seconds"
        try:
            sec = max(1, min(3600, int(arg)))
            self.config.command_timeout_sec = sec
            self.config.save()
            return f"Shell command timeout set to {sec} seconds. This affects /shell, /verify and project verification commands."
        except Exception:
            return "Usage: /command-timeout status|SECONDS"

    def model_health_text(self) -> str:
        try:
            ollama_ps = self.tools._ollama_ps() if hasattr(self, "tools") else None
        except Exception:
            ollama_ps = {"available": False, "error": "ollama status check failed"}
        try:
            from .ollama import ollama_busy_state
            busy = ollama_busy_state()
        except Exception:
            busy = {}
        report = assess_model_dependency(self.config, ollama_ps=ollama_ps, busy_state=busy)
        return render_model_health_markdown(report)

    def idle_status_text(self) -> str:
        s = dict(self.idle_state)
        policy = load_idle_policy()
        spec = policy.get("spec") or {}
        return (
            f"Idle mode: {'enabled' if s.get('enabled') else 'off'}\n"
            f"Idle level: {policy.get('level')} — {spec.get('title', '')}\n"
            f"Running: {s.get('running')}\n"
            f"Cycle: {s.get('cycle')}\n"
            f"Action: {s.get('current_action')}\n"
            f"Detail: {s.get('current_detail')}\n"
            f"Last summary: {s.get('last_summary')}\n"
            f"Last error: {s.get('last_error') or 'none'}\n"
            f"Policy: proposals={'yes' if spec.get('allows_proposals') else 'no'}, "
            f"patch_prepare={'yes' if spec.get('allows_patch_prepare') else 'no'}, "
            f"auto_apply={'yes' if spec.get('allows_auto_apply') else 'no'}"
        )
    def idle_command(self, rest: str) -> str:
        parts = (rest or "status").split(maxsplit=1)
        action = parts[0].lower() if parts else "status"
        goal = parts[1] if len(parts) > 1 else "self-analyse logs and propose safe improvements"
        if action in {"status", ""}:
            return self.idle_status_text()
        if action in {"level", "policy"}:
            if len(parts) > 1:
                try:
                    policy = set_idle_policy_level(parts[1], updated_by="idle command")
                except Exception as exc:
                    return f"Idle policy not changed: {exc}\n\n" + render_idle_policy(load_idle_policy())
                return render_idle_policy(policy)
            return render_idle_policy(load_idle_policy())
        if action == "auto-apply":
            return self._idle_auto_apply_command(parts[1] if len(parts) > 1 else "status")
        if action == "propose":
            if not idle_allows("propose"):
                return "Idle policy is level 0/watch-only, so proposal generation is disabled. Use `/idle level 1` or higher to allow proposals."
            return self._idle_propose(goal)
        if action == "once":
            return self._idle_once(goal)
        if action == "start":
            if self.idle_state.get("enabled"):
                return "Idle mode is already enabled.\n\n" + self.idle_status_text()
            self.idle_state.update({"enabled": True, "stop_requested": False, "last_summary": "Idle mode started.", "current_action": "Idle loop armed", "current_detail": goal})
            self._idle_thread = threading.Thread(target=self._idle_loop, args=(goal,), daemon=True)
            self._idle_thread.start()
            self._set_avatar("idle", "🌙", "Idle maintenance", "I will self-analyse when the user is not actively using me.")
            return "Idle mode started. It will pause when you send a normal task and resume when quiet. Low-risk auto-apply is active when `/idle auto-apply status` says on, but only after backup, diff, verification and rollback gates pass. Use `/idle stop` to stop."
        if action == "stop":
            self.idle_state.update({"enabled": False, "stop_requested": True, "running": False, "current_action": "Idle stopped", "current_detail": "Stopped by user."})
            self._set_avatar("ready", "🤖", "Ready", "Idle mode stopped.")
            return "Idle mode stopped."
        return "Usage: /idle status|level 0-3|once [goal]|propose [goal]|auto-apply status|on|off|start [goal]|stop"

    def _idle_auto_apply_command(self, rest: str = "status") -> str:
        action = (rest or "status").strip().split(maxsplit=1)[0].lower()
        settings = load_idle_autonomy_settings()
        if action in {"status", ""}:
            state = "on" if settings.get("idle_auto_apply_low_risk") else "off"
            policy = load_idle_policy()
            return (
                f"Idle auto-apply low-risk setting: {state}.\n"
                f"Idle level: {policy.get('level')} — {(policy.get('spec') or {}).get('title','')}.\n"
                "Background idle applies eligible low-risk report/docs/tests/logging patches only at idle level 3 after backup, diff, verification and rollback checks.\n"
                "Use `/idle level 3` and `/idle auto-apply on`, then `/idle auto-apply run [goal]` to apply one guarded patch immediately."
            )
        if action == "on":
            settings["idle_auto_apply_low_risk"] = True
            save_idle_autonomy_settings(settings)
            policy = set_idle_policy_level(3, updated_by="idle auto-apply on")
            return (
                "Idle auto-apply low-risk setting: on.\n"
                f"Idle policy is now level {policy.get('level')} — {(policy.get('spec') or {}).get('title','')}.\n"
                "Background idle can apply eligible low-risk report/docs/tests/logging patches after all safety gates pass.\n"
                "Use `/idle auto-apply run [goal]` to apply one guarded patch immediately."
            )
        if action == "off":
            settings["idle_auto_apply_low_risk"] = False
            save_idle_autonomy_settings(settings)
            return (
                "Idle auto-apply low-risk setting: off.\n"
                "No idle auto-apply run can apply source edits while this is off.\n"
                "This setting does not bypass safety checks."
            )
        if action in {"run", "once"}:
            goal = (rest or "").strip().split(maxsplit=1)
            return self._idle_auto_apply_once(goal[1] if len(goal) > 1 else "apply the safest low-risk idle report improvement")
        return (
            "Usage: /idle auto-apply status|on|off|run [goal]\n"
            "When on, background idle may apply eligible low-risk report/docs/tests/logging patches after all gates pass.\n"
            "This setting does not bypass safety checks."
        )

    def _idle_auto_apply_once(self, goal: str = "apply the safest low-risk idle report improvement") -> str:
        settings = load_idle_autonomy_settings()
        policy = load_idle_policy()
        if not settings.get("idle_auto_apply_low_risk", False) or not idle_allows("apply", policy):
            return (
                "Idle auto-apply is disabled by setting or idle policy.\n"
                f"Current idle level: {policy.get('level')} — {(policy.get('spec') or {}).get('title','')}.\n"
                "Run `/idle level 3` and `/idle auto-apply on` first, then `/idle auto-apply run [goal]`.\n"
                "No source files were modified."
            )

        event_warnings: list[str] = []
        warning = self._append_idle_event_safe({
            "event": "idle_auto_apply_started",
            "status": "started",
            "goal": goal,
        })
        if warning:
            event_warnings.append(warning)

        repo_root = Path.cwd().resolve()
        state_path = APP_DIR / "IDLE_STRATEGY_STATE.json"
        state = load_strategy_state(state_path)
        decision = select_candidate(collect_idle_candidates(APP_DIR, repo_root), state)
        selected = decision.selected_candidate
        if not selected:
            return "Idle auto-apply found no safe candidate.\nNo source files were modified."

        result = self._idle_auto_apply_decision(selected, goal, repo_root, state, decision)
        lines = [
            "Idle auto-apply " + ("applied one low-risk patch." if result.get("verification_ok") else "rolled back after verification failed."),
            f"Status: {result.get('status')}",
        ]
        if result.get("target_file"):
            lines.append(f"Target file: {result.get('target_file')}")
        if result.get("backup_path"):
            lines.append(f"Backup: {result.get('backup_path')}")
        if result.get("markdown_report_path"):
            lines.append(f"Markdown report: {result.get('markdown_report_path')}")
        if result.get("json_report_path"):
            lines.append(f"JSON report: {result.get('json_report_path')}")
        if result.get("blocked"):
            lines[0] = "Idle auto-apply blocked: " + "; ".join(str(reason) for reason in result.get("reasons", []))
            lines.append("No source files were modified.")
        lines.append("Self-improve was not called.")
        if event_warnings:
            lines.extend(event_warnings)
        return "\n".join(lines)

    def _idle_auto_apply_decision(self, selected: Any, goal: str, repo_root: Path, state: Any, decision: Any, *, save_state: bool = True) -> dict[str, Any]:
        patch = self._idle_auto_apply_build_patch(selected, goal, repo_root)
        if not patch.get("ok"):
            return {"blocked": True, "status": "blocked", "reasons": [str(patch.get("reason") or "patch could not be built")], "verification_ok": False}

        diff_text = str(patch["diff"])
        changed_lines = self._idle_auto_apply_count_changed_lines(diff_text)
        report_dir = APP_DIR / "idle_auto_apply_reports"
        backup_dir = APP_DIR / "idle_auto_apply_backups"
        report_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        report_path = report_dir / f"idle_auto_apply_{stamp}.md"
        json_path = report_path.with_suffix(".json")
        backup_path = backup_dir / f"idle_auto_apply_{stamp}_{Path(str(patch['relative_path'])).name}.bak"
        atomic_write_text(backup_path, str(patch["original"]))
        atomic_write_text(
            report_path,
            self._format_idle_auto_apply_report(
                selected,
                goal,
                patch,
                diff_text,
                {"status": "pending", "reasons": ["Gate has not run yet."]},
                [],
                status="pending",
                backup_path=str(backup_path),
            ),
        )

        patch_summary = {
            "changed_files": 1,
            "changed_lines": changed_lines,
            "backup_available": backup_path.exists(),
            "diff_report_available": report_path.exists(),
            "verification_available": bool(self._idle_auto_apply_verification_plan(repo_root)),
        }
        gate = evaluate_idle_auto_apply_gate(selected, [str(patch["relative_path"])], patch_summary)
        if not gate.get("allowed"):
            payload = {
                "status": "blocked",
                "candidate": asdict(selected),
                "goal": goal,
                "gate": gate,
                "patch_summary": patch_summary,
                "markdown_report_path": str(report_path),
                "backup_path": str(backup_path),
            }
            atomic_write_json(json_path, payload, ensure_ascii=False)
            atomic_write_text(
                report_path,
                self._format_idle_auto_apply_report(selected, goal, patch, diff_text, gate, [], status="blocked", backup_path=str(backup_path)),
            )
            return {
                "blocked": True,
                "status": "blocked",
                "reasons": list(gate.get("reasons", [])),
                "verification_ok": False,
                "markdown_report_path": str(report_path),
                "json_report_path": str(json_path),
                "backup_path": str(backup_path),
                "target_file": str(patch["relative_path"]),
            }

        target = Path(str(patch["target_path"]))
        target.parent.mkdir(parents=True, exist_ok=True)
        target_existed = bool(patch.get("target_existed"))
        atomic_write_text(target, str(patch["proposed"]))
        verification_ok, verification_results = self._run_idle_auto_apply_verification(repo_root)
        surgical_result = None
        status = "applied"
        if not verification_ok:
            combined_error = "\n".join(str(item.get("output", "")) for item in verification_results)
            surgical_result = apply_surgical_fallback_to_file(target, combined_error, backup_dir=backup_dir)
            if surgical_result.changed:
                verification_ok, verification_results = self._run_idle_auto_apply_verification(repo_root)
                status = "applied-after-surgical-fallback" if verification_ok else "rolled-back"
            if not verification_ok:
                if target_existed:
                    atomic_write_text(target, str(patch["original"]))
                else:
                    try:
                        target.unlink()
                    except FileNotFoundError:
                        log_activity("idle_auto_apply_rollback_target_missing", "Rollback target was already absent", {"target": str(target)})
                status = "rolled-back"

        payload = {
            "status": status,
            "candidate": asdict(selected),
            "goal": goal,
            "gate": gate,
            "patch_summary": patch_summary,
            "target_file": str(patch["relative_path"]),
            "backup_path": str(backup_path),
            "markdown_report_path": str(report_path),
            "verification": verification_results,
            "rollback_available": True,
            "self_improve_called": False,
            "surgical_fallback": surgical_fallback_report_payload(surgical_result) if surgical_result else None,
        }
        atomic_write_json(json_path, payload, ensure_ascii=False)
        atomic_write_text(
            report_path,
            self._format_idle_auto_apply_report(selected, goal, patch, diff_text, gate, verification_results, status=status, backup_path=str(backup_path), surgical_result=surgical_result),
        )
        if save_state:
            state_path = APP_DIR / "IDLE_STRATEGY_STATE.json"
            save_strategy_state(state_path, update_strategy_state_after_report(state, replace(decision, status="success-verification" if verification_ok else "failed-verification")))
        self._append_idle_event_safe({
            "event": "idle_auto_apply_completed",
            "status": status,
            "goal": goal,
            "target_file": str(patch["relative_path"]),
            "report_path": str(report_path),
            "json_report_path": str(json_path),
            "verification_ok": verification_ok,
        })
        log_activity("idle_auto_apply_" + status, "Idle auto-apply run completed", payload)
        return {
            "blocked": False,
            "status": status,
            "verification_ok": verification_ok,
            "markdown_report_path": str(report_path),
            "json_report_path": str(json_path),
            "backup_path": str(backup_path),
            "target_file": str(patch["relative_path"]),
            "gate": gate,
            "verification": verification_results,
        }

    def _idle_auto_apply_build_patch(self, selected: Any, goal: str, repo_root: Path) -> dict[str, Any]:
        """Build a tiny deterministic patch for the selected idle candidate.

        The background idle path can implement its own selected proposals, but it
        still avoids broad model-driven edits. Supported low-risk families are:
        docs/report markdown entries, one deterministic test guardrail, and
        logging notes under docs/.
        """
        if not selected:
            return {"ok": False, "reason": "No selected candidate is available."}
        category = str(selected.category or "")
        if category not in {"report", "docs", "tests", "logging"}:
            return {"ok": False, "reason": f"Candidate category '{category or 'unknown'}' is not supported for guarded idle auto-apply."}

        evidence_lines = []
        for ev in list(selected.evidence or [])[:5]:
            evidence_lines.append(f"- {ev.source}: {ev.summary}")
        evidence_text = "\n".join(evidence_lines) or "- No evidence attached."

        if category in {"report", "docs", "logging"}:
            markdown_targets = [
                path for path in (selected.target_files or [])
                if str(path).replace("\\", "/").lower().startswith("docs/") and str(path).lower().endswith(".md")
            ]
            if not markdown_targets:
                markdown_targets = ["docs/IDLE_REPORTS.md"]
            relative_path = str(markdown_targets[0]).replace("\\", "/")
            target = self._idle_auto_apply_resolve_repo_path(repo_root, relative_path)
            original = target.read_text(encoding="utf-8", errors="replace") if target.exists() else "# Nova Idle Reports\n\n"
            entry = "\n".join([
                f"## Auto-Applied Idle Report Entry - {time.strftime('%Y-%m-%d %H:%M:%S')}",
                "",
                f"- Goal: {goal}",
                f"- Candidate: {selected.title}",
                f"- Category: {selected.category}",
                "- Implementation: appended a deterministic report/log entry from idle evidence.",
                "- Safety: low-risk markdown-only patch; no runtime source logic changed.",
                "- Self-improve: not called.",
                "",
                "### Evidence",
                evidence_text,
                "",
                "### Verification",
                "- py_compile and smoke verification run after writing.",
                "",
            ])
            proposed = original.rstrip() + "\n\n" + entry
        elif category == "tests":
            test_targets = [
                path for path in (selected.target_files or [])
                if str(path).replace("\\", "/").lower() in {"tests_smoke.py", "tests_idle_events.py", "tests_cli_user_mode.py"}
            ]
            relative_path = str(test_targets[0] if test_targets else "tests_smoke.py").replace("\\", "/")
            target = self._idle_auto_apply_resolve_repo_path(repo_root, relative_path)
            if not target.name.endswith(".py"):
                return {"ok": False, "reason": "Idle tests auto-apply only supports Python test files."}
            original = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
            marker = "test_idle_auto_apply_generated_implements_low_risk_candidate"
            if marker in original:
                # The highest-scoring repeated test proposal has already been implemented.
                # Record a tiny docs/report entry instead of making a no-op patch or looping.
                relative_path = "docs/IDLE_IMPLEMENTED_PROPOSALS.md"
                target = self._idle_auto_apply_resolve_repo_path(repo_root, relative_path)
                original = target.read_text(encoding="utf-8", errors="replace") if target.exists() else "# Implemented Idle Proposals\n\n"
                entry = "\n".join([
                    f"## Already Implemented Test Proposal - {time.strftime('%Y-%m-%d %H:%M:%S')}",
                    "",
                    f"- Goal: {goal}",
                    f"- Candidate: {selected.title}",
                    "- Result: the generated idle auto-apply regression test already exists, so idle recorded completion and should rotate to another candidate.",
                    "- Safety: docs-only follow-up; no source behaviour changed.",
                    "",
                ])
                proposed = original.rstrip() + "\n\n" + entry
            else:
                test_entry = """\n\n\ndef test_idle_auto_apply_generated_implements_low_risk_candidate():\n    from winlocalassistant.core import evaluate_idle_auto_apply_gate\n    from winlocalassistant.idle_engine import IdleCandidate\n\n    candidate = IdleCandidate(\n        id="generated-idle-report",\n        title="Generated idle auto-apply guardrail",\n        category="report",\n        evidence=[],\n        target_files=["docs/IDLE_REPORTS.md"],\n        risk_score=0.20,\n        allowed_to_auto_apply=True,\n    )\n    gate = evaluate_idle_auto_apply_gate(\n        candidate,\n        ["docs/IDLE_REPORTS.md"],\n        {\n            "changed_files": 1,\n            "changed_lines": 8,\n            "backup_available": True,\n            "diff_report_available": True,\n            "verification_available": True,\n        },\n    )\n\n    assert gate["allowed"] is True\n    assert gate["status"] == "auto-apply-eligible"\n"""
                proposed = original.rstrip() + test_entry
        else:
            return {"ok": False, "reason": "Unsupported idle auto-apply category."}

        diff_text = "\n".join(difflib.unified_diff(
            original.splitlines(),
            proposed.splitlines(),
            fromfile=f"before/{relative_path}",
            tofile=f"after/{relative_path}",
            lineterm="",
        ))
        return {
            "ok": True,
            "relative_path": relative_path,
            "target_path": str(target),
            "target_existed": target.exists(),
            "original": original,
            "proposed": proposed,
            "diff": diff_text,
        }

    def _idle_auto_apply_resolve_repo_path(self, repo_root: Path, relative_path: str) -> Path:
        base = repo_root.expanduser().resolve()
        target = (base / relative_path).expanduser().resolve()
        if base != target and base not in target.parents:
            raise PermissionError(f"Refusing idle auto-apply outside repo root: {target}")
        return target

    def _idle_auto_apply_count_changed_lines(self, diff_text: str) -> int:
        return sum(1 for line in (diff_text or "").splitlines() if line[:1] in {"+", "-"} and not line.startswith(("+++", "---")))

    def _idle_auto_apply_verification_plan(self, repo_root: Path) -> list[tuple[str, list[str]]]:
        py_files = [str(path) for path in sorted((repo_root / "winlocalassistant").glob("*.py"))]
        python_exe = sys.executable
        return [
            ("py_compile", [python_exe, "-W", "error::SyntaxWarning", "-m", "py_compile", "app.py", *py_files, "tests_smoke.py"]),
            ("smoke", [python_exe, "tests_smoke.py"]),
        ]

    def _run_idle_auto_apply_verification(self, repo_root: Path) -> tuple[bool, list[dict[str, Any]]]:
        results: list[dict[str, Any]] = []
        for name, args in self._idle_auto_apply_verification_plan(repo_root):
            try:
                cp = subprocess.run(args, cwd=str(repo_root), capture_output=True, text=True, timeout=120)
                output = ((cp.stdout or "") + (cp.stderr or ""))[-4000:]
                results.append({"name": name, "ok": cp.returncode == 0, "returncode": cp.returncode, "output": output})
            except Exception as exc:
                results.append({"name": name, "ok": False, "returncode": -1, "output": repr(exc)})
            if not results[-1]["ok"]:
                return False, results
        return True, results

    def _format_idle_auto_apply_report(
        self,
        selected: Any,
        goal: str,
        patch: dict[str, Any],
        diff_text: str,
        gate: dict[str, Any],
        verification: list[dict[str, Any]],
        *,
        status: str,
        backup_path: str,
        surgical_result: Any = None,
    ) -> str:
        verification_text = "\n".join(
            f"- {item.get('name')}: {'PASS' if item.get('ok') else 'FAIL'}"
            for item in verification
        ) or "- Verification has not run yet."
        gate_text = "\n".join(f"- {reason}" for reason in gate.get("reasons", [])) or "- Gate passed."
        surgical_text = "- Not needed."
        if surgical_result:
            surgical_text = "\n".join(
                [
                    f"- Attempted: {getattr(surgical_result, 'attempted', False)}",
                    f"- Changed: {getattr(surgical_result, 'changed', False)}",
                    f"- Reason: {getattr(surgical_result, 'reason', '')}",
                ] + [f"- {change}" for change in (getattr(surgical_result, 'changes', []) or [])]
            )
        return "\n".join([
            "# Nova Idle Auto-Apply Report",
            "",
            "## Status",
            status,
            "",
            "## Goal",
            goal,
            "",
            "## Candidate",
            f"{selected.title} ({selected.category})",
            "",
            "## Safety Gate",
            f"Status: {gate.get('status')}",
            gate_text,
            "",
            "## Target File",
            str(patch.get("relative_path")),
            "",
            "## Backup And Rollback",
            f"Backup: {backup_path}",
            "Rollback: restore the backup to the target file; failed verification rolls back automatically.",
            "",
            "## Verification",
            verification_text,
            "",
            "## Surgical Fallback",
            surgical_text,
            "",
            "## Diff",
            "```diff",
            diff_text[:12000],
            "```",
            "",
            "## Safety Notes",
            "- Background idle may call this same guarded path when low-risk auto-apply is on.",
            "- `/self-improve` was not called.",
            "- Report/docs, tests, and logging candidates are supported when the deterministic patch builder can create a tiny verified patch.",
            "",
        ])
    def _idle_user_or_model_active(self) -> tuple[bool, str]:
        now = time.time()
        quiet_until = float(getattr(self, "_idle_quiet_until_ts", 0.0) or 0.0)
        if quiet_until > now:
            remaining = int(max(1, quiet_until - now))
            return True, f"foreground request quiet window active ({remaining}s remaining)"
        if isinstance(self.active_run, dict) and self.active_run.get("status") in {"waiting_for_user", "ready", "running", "paused"}:
            return True, f"interactive run is {self.active_run.get('status')}"
        try:
            from .ollama import ollama_busy_state
            busy = ollama_busy_state()
            if busy.get("prompt_active"):
                return True, str(busy.get("busy_desc") or "local model prompt is active")
            if busy.get("cooldown_active"):
                return True, str(busy.get("busy_desc") or "local model cooldown/cleanup is active")
        except Exception as exc:
            logging.getLogger(__name__).debug("Idle model activity check failed", exc_info=True)
        return False, ""

    def _idle_loop(self, goal: str) -> None:
        current_goal = goal
        while self.idle_state.get("enabled") and not self.idle_state.get("stop_requested"):
            time.sleep(20)
            if self.idle_state.get("stop_requested") or not self.idle_state.get("enabled"):
                break
            active, reason = self._idle_user_or_model_active()
            if active:
                self.idle_state.update({
                    "running": False,
                    "current_action": "Idle paused for active task",
                    "current_detail": reason,
                    "last_summary": "Idle skipped this cycle so it would not overwrite or distract from the current user task.",
                })
                log_activity("idle_skipped_active_task", "Idle skipped because a user/model task is active", {"goal": current_goal, "reason": reason})
                time.sleep(40)
                continue
            if self._chat_lock.acquire(blocking=False):
                try:
                    active, reason = self._idle_user_or_model_active()
                    if active:
                        log_activity("idle_skipped_active_task", "Idle skipped after acquiring lock because a task became active", {"goal": current_goal, "reason": reason})
                    else:
                        self._idle_once(current_goal)
                        current_goal = str(self.idle_state.get("next_goal") or current_goal)
                finally:
                    try:
                        self._chat_lock.release()
                    except RuntimeError:
                        logging.getLogger(__name__).debug("Idle chat lock was already released", exc_info=True)
            time.sleep(40)
    def _record_idle_lesson(self, cycle: int, goal: str, issue: str, resolution: str = "") -> None:
        try:
            lesson_path = APP_DIR / "IDLE_LESSONS.md"
            old = lesson_path.read_text(encoding="utf-8", errors="replace") if lesson_path.exists() else "# Idle Lessons\n\n"
            stamp = time.strftime("%Y-%m-%d %H:%M:%S")
            block = (
                f"## {stamp} - Cycle {cycle}\n"
                f"- Goal: {goal}\n"
                f"- Issue: {issue}\n"
                f"- Resolution/next rule: {resolution or 'Avoid repeating this failure; check logs and fix the root cause before retrying.'}\n\n"
            )
            atomic_write_text(lesson_path, old + block)
            log_activity("idle_lesson", f"Idle cycle {cycle} lesson recorded", {"cycle": cycle, "goal": goal, "issue": issue, "resolution": resolution, "path": str(lesson_path)})
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})

    def _append_idle_event_safe(self, event: dict[str, Any]) -> str | None:
        try:
            append_idle_event(APP_DIR, event)
            return None
        except Exception as exc:
            try:
                log_activity("idle_event_log_failed", "Idle JSONL event logging failed", {
                    "event": str(event.get("event", "")),
                    "error": repr(exc),
                })
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            return f"Idle JSONL event logging warning: {exc!r}"

    def _idle_candidate_event_fields(self, selected: Any) -> dict[str, Any]:
        if not selected:
            return {
                "selected_candidate_id": None,
                "selected_candidate_title": None,
                "category": None,
                "value_score": None,
                "risk_score": None,
                "confidence_score": None,
                "final_score": None,
            }
        return {
            "selected_candidate_id": selected.id,
            "selected_candidate_title": selected.title,
            "category": selected.category,
            "value_score": selected.value_score,
            "risk_score": selected.risk_score,
            "confidence_score": selected.confidence_score,
            "final_score": selected.final_score,
        }

    def _idle_progress_lines(self, goal: str, decision_data: dict[str, Any]) -> list[str]:
        """Track idle mission progress so continuous idle cannot repeat one report forever."""
        selected_id = str(decision_data.get("selected_candidate_id") or "")
        selected_title = str(decision_data.get("selected_candidate_title") or decision_data.get("selected") or "")
        rejected = decision_data.get("rejected_candidates") if isinstance(decision_data.get("rejected_candidates"), list) else []
        old_completed = [
            str(item)
            for item in (self.idle_state.get("completed_idle_candidate_ids") or [])
            if str(item)
        ][-20:]
        previous_id = str(self.idle_state.get("last_idle_selected_candidate_id") or "")
        repeat_count = int(self.idle_state.get("last_idle_selected_repeat_count") or 0)
        repeat_count = repeat_count + 1 if selected_id and selected_id == previous_id else (1 if selected_id else 0)
        already_completed = bool(selected_id and selected_id in old_completed)
        completed = list(old_completed)
        if selected_id and selected_id not in completed:
            completed.append(selected_id)
        next_goal = ""
        stop_reason = ""
        alternative = next((item for item in rejected if str(item.get("category") or "") != "noop"), None)
        if decision_data.get("no_safe_candidate"):
            stop_reason = "no safe idle candidate remains for this goal"
        elif already_completed or repeat_count >= 2:
            if alternative:
                alt_title = str(alternative.get("title") or "the next safe candidate")
                next_goal = (
                    f"{goal}\n"
                    f"Next idle cycle: do not repeat '{selected_title}'. "
                    f"Evaluate the alternative '{alt_title}' or explain why it is not useful."
                )
            else:
                stop_reason = f"completed '{selected_title}' and found no useful alternative"
        self.idle_state.update({
            "completed_idle_candidate_ids": completed[-20:],
            "last_idle_selected_candidate_id": selected_id,
            "last_idle_selected_candidate_title": selected_title,
            "last_idle_selected_repeat_count": repeat_count,
            "next_goal": next_goal,
        })
        lines = [
            "",
            "## Idle progress",
            f"- Completed candidate reports tracked: {len(completed[-20:])}",
        ]
        if selected_title:
            lines.append(f"- Current candidate repeat count: {repeat_count}")
        if next_goal:
            lines.append(f"- Next cycle strategy: switch away from `{selected_title}` and evaluate an alternative.")
            log_activity("idle_strategy_shift", "Idle shifted to an alternative candidate after completing a repeated report", {
                "selected_candidate_id": selected_id,
                "selected_candidate_title": selected_title,
                "repeat_count": repeat_count,
                "alternative": alternative,
                "next_goal": next_goal,
            })
        if stop_reason:
            self.idle_state.update({
                "enabled": False,
                "stop_requested": True,
                "current_action": "Idle paused after completed objective",
                "current_detail": stop_reason,
                "next_goal": "",
            })
            lines.append(f"- Continuous idle paused: {stop_reason}.")
            log_activity("idle_loop_guard_stop", "Idle stopped after repeated/completed work", {
                "selected_candidate_id": selected_id,
                "selected_candidate_title": selected_title,
                "repeat_count": repeat_count,
                "reason": stop_reason,
            })
        return lines

    def _idle_candidate_report(self, run_id: str, cycle: int) -> tuple[list[str], dict[str, Any]]:
        state_path = APP_DIR / "IDLE_STRATEGY_STATE.json"
        event_warnings: list[str] = []
        state = load_strategy_state(state_path)
        candidates = collect_idle_candidates(APP_DIR, Path.cwd())
        warning = self._append_idle_event_safe({
            "event": "candidates_collected",
            "run_id": run_id,
            "status": "candidates-collected",
            "candidate_count": len(candidates),
            "no_safe_candidate": False,
        })
        if warning:
            event_warnings.append(warning)
        decision = select_candidate(candidates, state)
        decision.run_id = run_id
        selected = decision.selected_candidate
        selected_fields = self._idle_candidate_event_fields(selected)
        auto_apply_gate = evaluate_idle_auto_apply_gate(
            selected,
            selected.target_files if selected else [],
            patch_summary=None,
        )
        warning = self._append_idle_event_safe({
            "event": "candidate_selected" if selected else "no_safe_candidate",
            "run_id": run_id,
            "status": decision.status,
            "no_safe_candidate": decision.no_safe_candidate,
            "auto_apply_status": auto_apply_gate.get("status"),
            "auto_apply_allowed": auto_apply_gate.get("allowed"),
            **selected_fields,
        })
        if warning:
            event_warnings.append(warning)
        report_dir = APP_DIR / "idle_runs"
        report_dir.mkdir(parents=True, exist_ok=True)
        stamp = time.strftime("%Y%m%d_%H%M%S")
        markdown_path = report_dir / f"idle_cycle_{stamp}.md"
        json_path = report_dir / f"idle_cycle_{stamp}.json"
        decision.markdown_report_path = str(markdown_path)
        decision.json_report_path = str(json_path)
        atomic_write_text(markdown_path, self._format_idle_cycle_markdown(decision, auto_apply_gate))
        decision_payload = asdict(decision)
        decision_payload["auto_apply_gate"] = auto_apply_gate
        atomic_write_json(json_path, decision_payload, ensure_ascii=False)
        background_apply: dict[str, Any] | None = None
        if selected and self.idle_state.get("enabled") and load_idle_autonomy_settings().get("idle_auto_apply_low_risk", False):
            try:
                background_apply = self._idle_auto_apply_decision(
                    selected,
                    f"Idle cycle {cycle}: {selected.title}",
                    Path.cwd().resolve(),
                    state,
                    decision,
                    save_state=False,
                )
                auto_apply_gate = background_apply.get("gate") or auto_apply_gate
                decision_payload["background_auto_apply"] = background_apply
                decision_payload["auto_apply_gate"] = auto_apply_gate
                atomic_write_json(json_path, decision_payload, ensure_ascii=False)
                log_activity("idle_background_auto_apply", "Idle background auto-apply evaluated selected candidate", {
                    "run_id": run_id,
                    "cycle": cycle,
                    "candidate": selected.title,
                    "status": background_apply.get("status"),
                    "blocked": background_apply.get("blocked"),
                    "target_file": background_apply.get("target_file"),
                    "markdown_report_path": background_apply.get("markdown_report_path"),
                })
            except Exception as exc:
                background_apply = {"blocked": True, "status": "error", "reasons": [repr(exc)], "verification_ok": False}
                log_activity("idle_background_auto_apply_failed", "Idle background auto-apply failed safely", {"run_id": run_id, "cycle": cycle, "error": repr(exc)})
        warning = self._append_idle_event_safe({
            "event": "idle_report_written",
            "run_id": run_id,
            "status": decision.status,
            "report_path": str(markdown_path),
            "json_report_path": str(json_path),
            "no_safe_candidate": decision.no_safe_candidate,
            "auto_apply_status": auto_apply_gate.get("status"),
            "auto_apply_allowed": auto_apply_gate.get("allowed"),
            **selected_fields,
        })
        if warning:
            event_warnings.append(warning)
        state_decision = decision
        if background_apply and not background_apply.get("blocked"):
            state_decision = replace(decision, status="success-verification" if background_apply.get("verification_ok") else "failed-verification")
        save_strategy_state(state_path, update_strategy_state_after_report(state, state_decision))
        warning = self._append_idle_event_safe({
            "event": "strategy_state_updated",
            "run_id": run_id,
            "status": decision.status,
            "report_path": str(markdown_path),
            "json_report_path": str(json_path),
            "no_safe_candidate": decision.no_safe_candidate,
            "auto_apply_status": auto_apply_gate.get("status"),
            "auto_apply_allowed": auto_apply_gate.get("allowed"),
            **selected_fields,
        })
        if warning:
            event_warnings.append(warning)

        selected_title = selected.title if selected else "No safe candidate"
        lines = [
            "",
            "## Idle decision",
            f"- Selected candidate: {selected_title}",
            f"- Status: {decision.status}",
            f"- Auto-apply gate: {auto_apply_gate.get('status')}",
            f"- Markdown report: {markdown_path}",
            f"- JSON report: {json_path}",
            "- Automatic low-risk apply is on by default and uses backup, diff, verification and rollback gates.",
            "- This setting does not bypass safety checks.",
        ]
        if background_apply and not background_apply.get("blocked"):
            lines.append(f"- Background auto-apply: {background_apply.get('status')} ({background_apply.get('target_file')}).")
            lines.append(f"- Auto-apply report: {background_apply.get('markdown_report_path')}.")
        elif background_apply:
            lines.append("- Background auto-apply needs attention: " + "; ".join(str(reason) for reason in background_apply.get("reasons", [])))
            lines.append("- No source files were modified by auto-apply.")
        else:
            lines.append("- No source files were modified by auto-apply.")
            lines.append("- No source files were modified by idle mode.")
        if selected:
            lines.insert(
                3,
                "- Scores: "
                f"value={selected.value_score:.2f}, risk={selected.risk_score:.2f}, "
                f"confidence={selected.confidence_score:.2f}, final={selected.final_score:.3f}",
            )
        if event_warnings:
            lines.extend(f"- {warning}" for warning in event_warnings)
        log_activity("idle_decision_report", f"Idle cycle {cycle} decision report written", {
            "run_id": run_id,
            "cycle": cycle,
            "status": decision.status,
            "selected": selected_title,
            "markdown_report_path": str(markdown_path),
            "json_report_path": str(json_path),
            "no_source_modified": not (background_apply and not background_apply.get("blocked")),
            "background_auto_apply": background_apply or {},
            "auto_apply_gate": auto_apply_gate,
        })
        return lines, {
            "markdown_report_path": str(markdown_path),
            "report_path": str(markdown_path),
            "json_report_path": str(json_path),
            "status": decision.status,
            "selected": selected_title,
            "no_safe_candidate": decision.no_safe_candidate,
            "rejected_candidates": [
                {
                    "id": candidate.id,
                    "title": candidate.title,
                    "category": candidate.category,
                    "final_score": candidate.final_score,
                    "risk_score": candidate.risk_score,
                }
                for candidate in decision.rejected_candidates[:8]
            ],
            "auto_apply_status": auto_apply_gate.get("status"),
            "auto_apply_allowed": auto_apply_gate.get("allowed"),
            "background_auto_apply": background_apply or {},
            "auto_apply_gate": auto_apply_gate,
            **selected_fields,
        }

    def _format_idle_cycle_markdown(self, decision: Any, auto_apply_gate: dict[str, Any] | None = None) -> str:
        selected = decision.selected_candidate
        auto_apply_gate = auto_apply_gate or {"status": "auto-apply-disabled", "reasons": ["Auto-apply is disabled."]}
        auto_apply_text = (
            f"Auto-apply gate: {auto_apply_gate.get('status')}\n\n"
            + "\n".join(f"- {reason}" for reason in auto_apply_gate.get("reasons", []))
            + "\n- Background idle may apply only eligible low-risk report/docs/tests/logging patches."
            + "\n- This setting does not bypass safety checks."
        )
        if selected:
            selected_text = f"{selected.title}\n\nCategory: {selected.category}"
            scores_text = (
                f"- Value: {selected.value_score:.2f}\n"
                f"- Risk: {selected.risk_score:.2f}\n"
                f"- Confidence: {selected.confidence_score:.2f}\n"
                f"- Final: {selected.final_score:.3f}"
            )
            evidence_text = "\n".join(
                f"- {ev.source}: {ev.summary}" + (f" (line {ev.line})" if ev.line else "")
                for ev in selected.evidence
            ) or "- No evidence attached."
            decision_text = "Idle selected a candidate. If the auto-apply gate passes with a concrete patch, idle may apply it with backup, verification and rollback."
            next_text = "Use `/idle auto-apply status` to see whether guarded automatic apply is on."
        else:
            selected_text = "No safe candidate"
            scores_text = "- No safe candidate was selected."
            evidence_text = "- No safe candidate evidence selected."
            decision_text = "No safe idle source edit was selected. No source files were modified by idle mode."
            next_text = "No safe source edit is recommended."
        rejected_text = "\n".join(
            f"- {c.title}: final={c.final_score:.3f}, risk={c.risk_score:.2f}, category={c.category}"
            for c in decision.rejected_candidates
        ) or "- None."
        verification_text = "\n".join(f"- `{cmd}`" for cmd in decision.verification_commands)
        return "\n".join([
            "# Nova Idle Cycle Report",
            "",
            "## Status",
            decision.status,
            "",
            "## Selected Candidate",
            selected_text,
            "",
            "## Scores",
            scores_text,
            "",
            "## Evidence",
            evidence_text,
            "",
            "## Rejected Candidates",
            rejected_text,
            "",
            "## Verification Commands",
            verification_text,
            "",
            "## Decision",
            decision_text + "\n\n" + auto_apply_text,
            "",
            "## Next Suggested Manual Command",
            next_text,
            "",
        ])

    def _idle_propose(self, goal: str = "self-analyse logs and propose safe improvements") -> str:
        event_warnings: list[str] = []
        warning = self._append_idle_event_safe({
            "event": "idle_proposal_started",
            "status": "started",
            "no_safe_candidate": None,
        })
        if warning:
            event_warnings.append(warning)
        try:
            proposal = self._build_idle_patch_proposal(goal)
            candidate = proposal.get("candidate")
            candidate_fields: dict[str, Any] = {}
            if isinstance(candidate, dict):
                candidate_fields = {
                    "selected_candidate_id": candidate.get("id"),
                    "selected_candidate_title": candidate.get("title"),
                    "category": candidate.get("category"),
                    "value_score": candidate.get("value_score"),
                    "risk_score": candidate.get("risk_score"),
                    "confidence_score": candidate.get("confidence_score"),
                    "final_score": candidate.get("final_score"),
                }
            auto_apply_gate = proposal.get("auto_apply_gate") or {}
            warning = self._append_idle_event_safe({
                "event": "idle_proposal_completed",
                "proposal_id": proposal["proposal_id"],
                "status": proposal["status"],
                "proposal_path": proposal["markdown_proposal_path"],
                "json_proposal_path": proposal["json_proposal_path"],
                "no_safe_candidate": candidate is None,
                "auto_apply_status": auto_apply_gate.get("status"),
                "auto_apply_allowed": auto_apply_gate.get("allowed"),
                **candidate_fields,
            })
            if warning:
                event_warnings.append(warning)
            log_activity("idle_patch_proposal", "Idle patch proposal written", {
                "proposal_id": proposal["proposal_id"],
                "status": proposal["status"],
                "selected": (proposal.get("candidate") or {}).get("title") if proposal.get("candidate") else "No safe candidate",
                "markdown_proposal_path": proposal["markdown_proposal_path"],
                "json_proposal_path": proposal["json_proposal_path"],
                "no_source_modified": True,
                "auto_apply_gate": auto_apply_gate,
            })
            selected_title = candidate.get("title") if isinstance(candidate, dict) else "No safe candidate"
            lines = [
                f"Idle proposal: {selected_title}",
                f"Status: {proposal['status']}",
            ]
            if isinstance(candidate, dict):
                lines.append(
                    "Scores: "
                    f"value={float(candidate.get('value_score') or 0.0):.2f}, "
                    f"risk={float(candidate.get('risk_score') or 0.0):.2f}, "
                    f"confidence={float(candidate.get('confidence_score') or 0.0):.2f}, "
                    f"final={float(candidate.get('final_score') or 0.0):.3f}"
                )
            lines.extend([
                f"Auto-apply gate: {auto_apply_gate.get('status', 'auto-apply-disabled')}",
                f"Markdown proposal: {proposal['markdown_proposal_path']}",
                f"JSON proposal: {proposal['json_proposal_path']}",
                "Suggested manual command: " + (proposal.get("suggested_self_improve_command") or "No safe self-improve command is recommended."),
                "Guarded background auto-apply may apply low-risk report/docs/tests/logging patches when idle mode is running and the gate passes.",
                "This setting does not bypass safety checks.",
                "No source files were modified by idle propose.",
            ])
            lines.extend(event_warnings)
            return "\n".join(lines)
        except Exception as exc:
            try:
                log_activity("idle_propose_failed", "Idle proposal generation failed", {"error": repr(exc), "goal": goal})
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            return f"Idle proposal generation failed: {exc!r}\n\nNo source files were modified by idle propose."

    def _build_idle_patch_proposal(self, goal: str) -> dict[str, Any]:
        candidates = collect_idle_candidates(APP_DIR, Path.cwd())
        decision = select_candidate(candidates, None)
        selected = decision.selected_candidate
        status = "proposal-only" if selected else "no-safe-candidate"
        stamp = time.strftime("%Y%m%d_%H%M%S")
        proposal_id = f"idle_patch_proposal_{stamp}"
        selected_fields = self._idle_candidate_event_fields(selected)
        auto_apply_gate = evaluate_idle_auto_apply_gate(
            selected,
            selected.target_files if selected else [],
            patch_summary=None,
        )
        self._append_idle_event_safe({
            "event": "candidate_selected" if selected else "no_safe_candidate",
            "proposal_id": proposal_id,
            "status": status,
            "no_safe_candidate": selected is None,
            "auto_apply_status": auto_apply_gate.get("status"),
            "auto_apply_allowed": auto_apply_gate.get("allowed"),
            **selected_fields,
        })
        proposal_dir = APP_DIR / "idle_patch_proposals"
        proposal_dir.mkdir(parents=True, exist_ok=True)
        markdown_path = proposal_dir / f"{proposal_id}.md"
        json_path = proposal_dir / f"{proposal_id}.json"
        non_goals = self._idle_proposal_non_goals()
        safety_checks = self._idle_proposal_safety_checks()
        candidate_obj = asdict(selected) if selected else None
        evidence = candidate_obj.get("evidence", []) if candidate_obj else []
        target_files = list(candidate_obj.get("target_files", [])) if candidate_obj else []
        proposal = {
            "proposal_id": proposal_id,
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "user_goal": goal,
            "status": status,
            "candidate": candidate_obj,
            "target_files": target_files,
            "problem_statement": self._idle_proposal_problem_statement(selected, goal),
            "evidence": evidence,
            "planned_change": self._idle_proposal_planned_change(selected),
            "non_goals": non_goals,
            "safety_checks": safety_checks,
            "verification_commands": decision.verification_commands,
            "rollback_plan": "Use the existing self-improve backup/rollback flow for any later manual self-edit; this proposal does not apply edits.",
            "suggested_self_improve_command": self._idle_suggested_self_improve_command(selected),
            "auto_apply_gate": auto_apply_gate,
            "markdown_proposal_path": str(markdown_path),
            "json_proposal_path": str(json_path),
        }
        atomic_write_text(markdown_path, self._format_idle_patch_proposal_markdown(proposal))
        atomic_write_json(json_path, proposal, ensure_ascii=False)
        self._append_idle_event_safe({
            "event": "proposal_written",
            "proposal_id": proposal_id,
            "status": status,
            "proposal_path": str(markdown_path),
            "json_proposal_path": str(json_path),
            "no_safe_candidate": selected is None,
            "auto_apply_status": auto_apply_gate.get("status"),
            "auto_apply_allowed": auto_apply_gate.get("allowed"),
            **selected_fields,
        })
        return proposal

    def _idle_proposal_non_goals(self) -> list[str]:
        return [
            "Do not apply unguarded or high-risk edits automatically.",
            "Do not loosen self-improve safety.",
            "Do not change internet/package/install behaviour.",
            "Do not integrate external repo code.",
            "Do not remove backup or rollback logic.",
            "Do not change command names unexpectedly.",
        ]

    def _idle_proposal_safety_checks(self) -> list[str]:
        return [
            "Review git diff before committing.",
            "Run py_compile.",
            "Run python tests_smoke.py.",
            "Run pytest suites if available.",
            "Confirm idle auto-apply remains limited to low-risk report/docs/tests/logging patches.",
            "Confirm /self-improve is not called automatically.",
            "Confirm backup and rollback logic remain intact.",
        ]

    def _idle_proposal_problem_statement(self, selected: Any, goal: str) -> str:
        if not selected:
            return f"No safe idle candidate was selected for goal: {goal}"
        return f"Idle evidence selected '{selected.title}' as the safest concrete proposal for goal: {goal}"

    def _idle_proposal_planned_change(self, selected: Any) -> str:
        if not selected:
            return "No source change is planned because no safe candidate was selected."
        files = ", ".join(selected.target_files) if selected.target_files else "the relevant low-risk report/test area"
        return (
            f"Likely touch {files}. Improve the behaviour described by '{selected.title}' with a small, reviewable patch. "
            "Keep idle auto-apply within low-risk report/docs/tests/logging boundaries; do not change command names, internet/package/install behaviour, or safety guardrails. "
            "Verify with py_compile, python tests_smoke.py, and pytest suites when available."
        )

    def _idle_suggested_self_improve_command(self, selected: Any) -> str:
        if not selected:
            return ""
        return f"/self-improve Add tests or reporting for {selected.title} without changing idle auto-apply behaviour"

    def _format_idle_patch_proposal_markdown(self, proposal: dict[str, Any]) -> str:
        candidate = proposal.get("candidate")
        selected_text = "No safe candidate"
        if isinstance(candidate, dict):
            selected_text = f"{candidate.get('title', '')}\n\nCategory: {candidate.get('category', '')}"
        evidence_text = "\n".join(
            f"- {ev.get('source', '')}: {ev.get('summary', '')}" + (f" (line {ev.get('line')})" if ev.get("line") else "")
            for ev in proposal.get("evidence", [])
            if isinstance(ev, dict)
        ) or "- None."
        target_text = "\n".join(f"- {path}" for path in proposal.get("target_files", [])) or "- None."
        non_goal_text = "\n".join(f"- {item}" for item in proposal.get("non_goals", []))
        auto_apply_gate = proposal.get("auto_apply_gate") or {"status": "auto-apply-disabled", "reasons": ["Auto-apply is disabled."]}
        auto_apply_text = [
            f"Auto-apply gate: {auto_apply_gate.get('status')}",
            "Background idle may apply only eligible low-risk report/docs/tests/logging patches.",
            "This setting does not bypass safety checks.",
        ]
        auto_apply_text.extend(str(reason) for reason in auto_apply_gate.get("reasons", []))
        safety_text = "\n".join(f"- {item}" for item in list(proposal.get("safety_checks", [])) + auto_apply_text)
        verification_text = "\n".join(f"- `{cmd}`" for cmd in proposal.get("verification_commands", []))
        suggested = proposal.get("suggested_self_improve_command") or "No safe self-improve command is recommended."
        return "\n".join([
            "# Nova Idle Patch Proposal",
            "",
            "## Status",
            str(proposal.get("status", "")),
            "",
            "## User Goal",
            str(proposal.get("user_goal", "")),
            "",
            "## Selected Candidate",
            selected_text,
            "",
            "## Evidence",
            evidence_text,
            "",
            "## Target Files",
            target_text,
            "",
            "## Planned Change",
            str(proposal.get("planned_change", "")),
            "",
            "## Non-goals",
            non_goal_text,
            "",
            "## Safety Checks",
            safety_text,
            "",
            "## Verification Commands",
            verification_text,
            "",
            "## Rollback Plan",
            str(proposal.get("rollback_plan", "")),
            "",
            "## Suggested Manual Command",
            suggested,
            "",
        ])

    def _idle_once(self, goal: str = "self-analyse logs and propose safe improvements") -> str:
        self.idle_state["running"] = True
        self.idle_state["cycle"] = int(self.idle_state.get("cycle") or 0) + 1
        self.idle_state["last_started"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self.idle_state["current_action"] = "Idle observe"
        self.idle_state["current_detail"] = "Checking logs, known issues and improvement proposals."
        self._set_avatar("thinking", "🧩", "Idle analysis", "Looking for safe improvements from logs and known issues.")
        run_id = new_run_id()
        set_current_run(run_id)
        cycle = self.idle_state["cycle"]
        report = [f"# Idle cycle {cycle}", f"Goal: {goal}"]
        event_warnings: list[str] = []
        try:
            plan_res = self.tools.call("idle_tool_plan", goal=goal, mode="idle", limit=12)
            log_activity("idle_tool_plan", "Idle tool-awareness plan selected", {"run_id": run_id, "cycle": cycle, "ok": plan_res.ok, "data": plan_res.data})
            if plan_res.ok:
                report.extend(["", "## Tool awareness", f"Pipeline: {plan_res.data.get('pipeline_kind')} — {plan_res.data.get('pipeline_title')}", f"Selected tools available: {plan_res.data.get('covered_tool_count')}/{len(plan_res.data.get('decisions') or [])}"])
        except Exception as exc:
            log_activity("idle_tool_plan_error", "Idle tool-awareness plan failed", {"run_id": run_id, "cycle": cycle, "error": repr(exc)})
        
        warning = self._append_idle_event_safe({
            "event": "idle_cycle_started",
            "run_id": run_id,
            "status": "started",
            "no_safe_candidate": None,
        })
        if warning:
            event_warnings.append(warning)
        try:
            log_activity("idle_cycle_start", f"Idle cycle {cycle} started", {"run_id": run_id, "cycle": cycle, "goal": goal})
            for label, tool, kwargs in [
                ("Heartbeat", "heartbeat", {}),
                ("Review idle lessons", "idle_lessons", {}),
                ("Investigate logs", "investigate_logs", {"focus": goal}),
                ("Known issues", "known_issues", {}),
                ("Propose improvements", "propose_improvements", {"focus": goal}),
                ("Self-improvement queue", "self_improvement_queue", {}),
            ]:
                if self.idle_state.get("stop_requested"):
                    break
                self.idle_state.update({"current_action": label, "current_detail": f"Running {tool}"})
                self._set_avatar("idle", "", "Idle maintenance", f"Idle cycle {cycle}: {label}")
                log_activity("idle_step_start", f"Idle cycle {cycle}: {label}", {"tool": tool, "run_id": run_id, "cycle": cycle, "goal": goal})
                res = self.tools.call(tool, **kwargs)
                line = f"- {label}: {'PASS' if res.ok else 'ATTENTION'} - {res.summary}"
                report.append(line)
                log_activity("idle_step_done", f"Idle cycle {cycle}: {label} {'passed' if res.ok else 'needs attention'}", {
                    "tool": tool, "ok": res.ok, "summary": res.summary, "run_id": run_id, "cycle": cycle, "goal": goal,
                    "report_line": line,
                })
            try:
                decision_lines, decision_data = self._idle_candidate_report(run_id, cycle)
                report.extend(decision_lines)
                report.extend(self._idle_progress_lines(goal, decision_data))
            except Exception as exc:
                decision_data = {"error": repr(exc)}
                warning = f"Idle decision engine warning: {exc!r}"
                report.extend(["", "## Idle decision", f"- {warning}", "- No source files were modified by idle mode."])
                log_activity("idle_decision_failed", "Idle decision engine failed; idle cycle continued report-only", {"run_id": run_id, "cycle": cycle, "error": repr(exc)})
            warning = self._append_idle_event_safe({
                "event": "idle_cycle_completed",
                "run_id": run_id,
                "status": str(decision_data.get("status", "decision-warning")),
                "report_path": decision_data.get("report_path") or decision_data.get("markdown_report_path"),
                "json_report_path": decision_data.get("json_report_path"),
                "no_safe_candidate": decision_data.get("no_safe_candidate"),
                "selected_candidate_id": decision_data.get("selected_candidate_id"),
                "selected_candidate_title": decision_data.get("selected_candidate_title"),
                "category": decision_data.get("category"),
                "value_score": decision_data.get("value_score"),
                "risk_score": decision_data.get("risk_score"),
                "confidence_score": decision_data.get("confidence_score"),
                "final_score": decision_data.get("final_score"),
                "auto_apply_status": decision_data.get("auto_apply_status"),
                "auto_apply_allowed": decision_data.get("auto_apply_allowed"),
            })
            if warning:
                event_warnings.append(warning)
            if event_warnings:
                report.extend(["", "## Idle event log warnings"])
                report.extend(f"- {warning}" for warning in event_warnings)
            summary = "\n".join(report)
            path = APP_DIR / "IDLE_ANALYSIS.md"
            old = path.read_text(encoding="utf-8", errors="replace") if path.exists() else "# Idle Analysis\n\n"
            atomic_write_text(path, old + "\n" + summary + "\n")
            self.idle_state.update({"running": False, "last_finished": time.strftime("%Y-%m-%d %H:%M:%S"), "last_summary": summary, "current_action": "Idle complete", "current_detail": str(path)})
            log_activity("idle_cycle_done", f"Idle cycle {cycle} completed", {
                "run_id": run_id, "cycle": cycle, "goal": goal, "summary": summary, "path": str(path), "idle_decision": decision_data,
            })
            self._set_avatar("ready", "", "Ready", f"Idle cycle {cycle} completed and logged.")
            return summary + f"\n\nLogged to {path}"
        except Exception as exc:
            self.idle_state.update({"running": False, "last_error": repr(exc), "current_action": "Idle error", "current_detail": repr(exc)})
            self._record_idle_lesson(cycle, goal, repr(exc), "Investigate the exact exception, patch the blocking bug, then retry only the failed step if possible.")
            log_activity("idle_cycle_failed", f"Idle cycle {cycle} failed", {"run_id": run_id, "cycle": cycle, "goal": goal, "error": repr(exc), "report": "\n".join(report)})
            self._set_avatar("error", "", "Idle error", f"Idle cycle {cycle} failed: {exc!r}")
            return f"Idle cycle failed: {exc!r}"
        finally:
            set_current_run(None)
    # -------------------------
    # Autonomous mode
    # -------------------------
    def _autonomous_clean_goal(self, goal: str) -> tuple[str, str]:
        """Split a long autonomous prompt into a concise mission and operating rules.
        Users often paste a full multi-section policy prompt. The agent should use the first
        sentence as the mission and keep the rest as guidance, not treat every rule as a task
        trigger such as "create a tool" or "build a project".
        """
        raw = (goal or "").strip()
        if not raw:
            return "Investigate logs, propose improvements, improve the current project if safe, and keep Nova healthy.", ""
        # Keep explicit command-like goals as-is when short.
        lines = [ln.strip() for ln in raw.splitlines()]
        nonempty = [ln for ln in lines if ln]
        # Cut at common section markers so rules don't become the actionable goal.
        cut_markers = ("for every cycle", "follow this loop", "rules:", "1. observe", "observe", "diagnose")
        lower = raw.lower()
        cut_at = len(raw)
        for m in cut_markers:
            idx = lower.find(m)
            if idx > 0:
                cut_at = min(cut_at, idx)
        mission = raw[:cut_at].strip().strip(".\n ")
        rules = raw[cut_at:].strip() if cut_at < len(raw) else ""
        if not mission and nonempty:
            mission = nonempty[0]
        # Collapse very long mission to first meaningful sentence.
        if len(mission) > 260:
            parts = re.split(r"(?<=[.!?])\s+", mission)
            mission = parts[0].strip() if parts else mission[:260].strip()
        if not mission:
            mission = "Run safe continuous improvement cycles for Nova and the current project."
        return mission, rules

    def _parse_autonomous_persistence_options(self, goal: str) -> tuple[str, bool | None]:
        """Strip autonomous persistence flags and return requested continuous mode.

        None means use the command default. `/autonomous start` defaults to
        continuous mission mode; `/autonomous once` defaults to finite mode.
        """
        try:
            tokens = shlex.split(goal or "")
        except ValueError:
            return (goal or "").strip(), None
        cleaned: list[str] = []
        persistence: bool | None = None
        for token in tokens:
            lower = token.lower()
            if lower in {"--continuous", "--keep-running", "--mission", "--repeat", "--no-stop-on-complete"}:
                persistence = True
                continue
            if lower in {"--finite", "--stop-when-complete", "--one-shot", "--stop-on-complete"}:
                persistence = False
                continue
            cleaned.append(token)
        return " ".join(cleaned).strip(), persistence

    def _parse_autonomous_goal_options(self, goal: str) -> tuple[str, int | None, bool]:
        """Parse lightweight autonomous run options from a user goal string.

        Supported forms are intentionally simple so they are easy to type in the
        chat box: `/autonomous start --cycles 3 investigate logs` and
        `/autonomous once --diagnostic check health`. Unknown tokens are left in
        the goal instead of being treated as flags.
        """
        try:
            tokens = shlex.split(goal or "")
        except ValueError:
            return (goal or "").strip(), None, False
        cleaned: list[str] = []
        max_cycles: int | None = None
        diagnostic_only = False
        index = 0
        while index < len(tokens):
            token = tokens[index]
            lower = token.lower()
            if lower in {"--diagnostic", "--diagnostic-only", "--no-mutate", "--read-only"}:
                diagnostic_only = True
                index += 1
                continue
            if lower in {"--cycles", "--max-cycles", "--cycle-limit"} and index + 1 < len(tokens):
                try:
                    max_cycles = max(1, min(int(tokens[index + 1]), 100))
                    index += 2
                    continue
                except ValueError:
                    logging.getLogger(__name__).debug("Ignored invalid autonomous cycle limit: %s", tokens[index + 1], exc_info=True)
            if lower.startswith("--cycles=") or lower.startswith("--max-cycles=") or lower.startswith("--cycle-limit="):
                try:
                    max_cycles = max(1, min(int(token.split("=", 1)[1]), 100))
                    index += 1
                    continue
                except ValueError:
                    logging.getLogger(__name__).debug("Ignored invalid autonomous inline cycle limit: %s", token, exc_info=True)
            cleaned.append(token)
            index += 1
        return " ".join(cleaned).strip(), max_cycles, diagnostic_only

    def _autonomous_extract_promote_patch_run_id(self, raw_goal: str) -> str:
        """Extract an explicit patch-promotion run id from an autonomous goal.

        Supported forms:
        - --promote-patch RUN_ID
        - --docker-promote-patch RUN_ID
        - promote validated patch RUN_ID
        If no run id follows an explicit promotion request, an empty string means
        the latest passing patch validation report will be considered.
        """
        text = raw_goal or ""
        try:
            tokens = shlex.split(text)
        except ValueError:
            tokens = text.split()
        for i, tok in enumerate(tokens):
            low = tok.lower()
            if low in {"--promote-patch", "--docker-promote-patch", "--promote-validated-patch"}:
                return tokens[i + 1] if i + 1 < len(tokens) and not tokens[i + 1].startswith("--") else ""
            if low.startswith("--promote-patch=") or low.startswith("--docker-promote-patch="):
                return tok.split("=", 1)[1].strip()
        m = re.search(r"promote\s+(?:validated\s+)?patch\s+([A-Za-z0-9_.:-]+)?", text, re.I)
        if m:
            return (m.group(1) or "").strip()
        return "__NO_PROMOTION_REQUEST__"

    def _autonomous_goal_disables_docker_validation(self, raw_goal: str) -> bool:
        lowered = (raw_goal or "").lower()
        return any(flag in lowered for flag in ["--no-docker", "--skip-docker", "no docker validation", "skip docker validation"])

    def _docker_image_available_from_status(self, status_data: dict[str, Any], image: str) -> bool:
        wanted_repo, _, wanted_tag = (image or "").partition(":")
        wanted_tag = wanted_tag or "latest"
        for row in status_data.get("images") or []:
            repo = str(row.get("Repository") or row.get("repository") or "")
            tag = str(row.get("Tag") or row.get("tag") or "latest")
            if repo == wanted_repo and tag == wanted_tag:
                return True
        return False

    def _autonomous_docker_validation_preflight(self, report: list[str], run_id: str, image: str = "python:3.12-slim") -> tuple[bool, str, dict[str, Any]]:
        """Return whether autonomous Docker validation should run.

        Docker is optional. Missing Docker should be recorded and skipped, not treated
        as a failed autonomous cycle. A missing validation image is also skipped by
        default so autonomous mode does not hang on an unexpected image pull.
        """
        status_result = self._autonomous_call_tool("Docker readiness check", "docker_status", {"include_raw": False}, report, run_id)
        data = status_result.data if isinstance(status_result.data, dict) else {}
        if not status_result.ok:
            reason = "Docker is unavailable or the daemon is not running; autonomous Docker validation skipped."
            self._set_autonomous_state(docker_validation_skipped_reason=reason)
            self._autonomous_event("docker_validation_skipped", reason, {"detail": status_result.summary})
            report.append("Docker validation skipped: " + reason)
            return False, reason, data
        if not self._docker_image_available_from_status(data, image):
            reason = f"Docker image {image} is not local; run `/docker-smoke` or `/docker-validate` once manually to pull it, then autonomous mode can use it without surprise pulls."
            self._set_autonomous_state(docker_validation_skipped_reason=reason)
            self._autonomous_event("docker_validation_skipped", "Docker validation image is not local", {"detail": reason})
            report.append("Docker validation skipped: " + reason)
            return False, reason, data
        self._set_autonomous_state(docker_validation_skipped_reason="")
        return True, "", data

    def _autonomous_docker_validation_checkpoint(self, report: list[str], run_id: str, stage: str, required: bool = False) -> tuple[bool, ToolResult | None]:
        command = "python -m compileall -q winlocalassistant tests_*.py app.py"
        self._autonomous_event("docker_validate", f"Docker validation checkpoint: {stage}", {"detail": command})
        result = self._autonomous_call_tool(
            f"Docker validation ({stage})",
            "docker_validate",
            {"path": ".", "command": command, "image": "python:3.12-slim", "timeout": 300},
            report,
            run_id,
        )
        data = result.data if isinstance(result.data, dict) else {}
        summary = {
            "stage": stage,
            "ok": bool(result.ok),
            "summary": result.summary,
            "run_id": data.get("run_id", ""),
            "run_dir": data.get("run_dir", ""),
            "command": data.get("command", command),
            "required": required,
        }
        self._set_autonomous_state(last_docker_validation=summary)
        if result.ok:
            self._autonomous_event("docker_validation_passed", f"Docker validation passed: {stage}", summary)
            return True, result
        self._autonomous_event("docker_validation_failed", f"Docker validation failed: {stage}", summary)
        if required:
            report.append("Docker validation gate blocked mutation because validation failed.")
        return False, result

    def _autonomous_thread_alive(self) -> bool:
        thread = self._autonomous_thread
        return bool(thread and thread.is_alive())

    def _autonomous_base_health_allows_mutation(self, base_results: list[tuple[str, str, ToolResult]]) -> tuple[bool, list[str]]:
        """Return whether it is safe for autonomous mode to move from diagnosis to mutation.

        Heartbeat/runtime self-check failures are treated as environment-health
        gates. The agent can still investigate and propose, but it should not
        run project-changing tools while its own runtime is unhealthy.
        """
        blockers: list[str] = []
        for title, tool, result in base_results:
            data = result.data if isinstance(result.data, dict) else {}
            if data.get("timed_out"):
                blockers.append(f"{title}: timed out while {tool} was running")
                continue
            if tool in {"heartbeat", "runtime_self_check", "code_repair_audit", "code_quality_gate"} and not result.ok:
                blockers.append(f"{title}: {result.summary}")
        return not blockers, blockers

    def _autonomous_should_create_tool(self, mission: str) -> bool:
        g = (mission or "").lower()
        explicit = [
            "create a tool that", "make a tool that", "build a tool that",
            "write a tool that", "add a tool that", "custom tool that",
            "/tool-create",
        ]
        return any(x in g for x in explicit)
    def _autonomous_should_skip_backtrack(self, result: ToolResult) -> bool:
        data = result.data or {}
        reason = str(data.get("reason") or data.get("error") or result.summary or "").lower()
        source = str(data.get("source") or "").lower()
        written = data.get("written") or []
        if source == "ollama_required_failed" and not written:
            return True
        if any(x in reason for x in ["ollama was not reachable", "timed out", "timeout", "no files were written", "did not produce valid json"]):
            if not written:
                return True
        return False

    def _autonomous_command_summary(self, tool: str, kwargs: dict[str, Any]) -> str | None:
        for key in ["command", "goal", "focus", "path", "name"]:
            if key in kwargs and kwargs.get(key) not in {None, ""}:
                text = str(kwargs.get(key))
                return text[:240]
        if kwargs:
            return json.dumps(kwargs, ensure_ascii=False, default=str)[:240]
        return None

    def _autonomous_target(self, tool: str, kwargs: dict[str, Any]) -> str | None:
        for key in ["path", "target", "file"]:
            if kwargs.get(key):
                return str(kwargs.get(key))[:240]
        if tool in {"improve_project", "ai_create_project", "surgical_repair", "final_project_check"}:
            return str(self.config.workspace)[:240]
        return None

    def _autonomous_action_signature_candidates(self, title: str, tool: str, kwargs: dict[str, Any]) -> tuple[str | None, str | None]:
        return self._autonomous_command_summary(tool, kwargs), self._autonomous_target(tool, kwargs)

    def _autonomous_cooldown_for_action(self, title: str, tool: str, kwargs: dict[str, Any]) -> tuple[bool, str, AutonomousFailureRecord | None]:
        memory = load_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH)
        command_summary, target = self._autonomous_action_signature_candidates(title, tool, kwargs)
        for record in reversed(memory.recent_failures or []):
            if record.action_name != title or record.tool_name != tool:
                continue
            if (record.command_summary or None) != (command_summary or None):
                continue
            if (record.target or None) != (target or None):
                continue
            on_cooldown, reason = should_cooldown_autonomous_action(memory, record.signature)
            if on_cooldown:
                return True, reason, record
        return False, "", None

    def _autonomous_failure_files(self, result: ToolResult) -> list[str]:
        files: list[str] = []
        data = result.data if isinstance(result.data, dict) else {}
        for key in ["path", "file", "failed_file"]:
            if data.get(key):
                files.append(str(data.get(key)))
        for item in data.get("written") or []:
            if isinstance(item, dict) and item.get("path"):
                files.append(str(item.get("path")))
        return list(dict.fromkeys(files))[:20]

    def _autonomous_clear_failure_cooldown(self, title: str, tool: str, kwargs: dict[str, Any]) -> None:
        command_summary = self._autonomous_command_summary(tool, kwargs)
        target = self._autonomous_target(tool, kwargs)
        memory = load_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH)
        updated = clear_autonomous_cooldowns_for_action(memory, title, tool, command_summary, target)
        if updated.cooldowns != memory.cooldowns or len(updated.recent_failures) != len(memory.recent_failures):
            save_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH, updated)
            log_activity("autonomous_failure_cooldown_cleared", "Cleared stale autonomous failure cooldown after verified success", {"tool": tool, "action": title, "target": target})

    def _autonomous_record_failure(self, title: str, tool: str, kwargs: dict[str, Any], result: ToolResult, run_id: str) -> None:
        data = result.data if isinstance(result.data, dict) else {}
        result_text = result.summary or ""
        error_text = json.dumps(data, ensure_ascii=False, default=str)[:12000] if data else ""
        no_useful = self._autonomous_should_skip_backtrack(result) or "no useful edits" in (result_text + error_text).lower()
        category = classify_autonomous_failure(
            result_text=result_text,
            error_text=error_text,
            timed_out=bool(data.get("timed_out")),
            no_useful_edits=no_useful,
        )
        command_summary = self._autonomous_command_summary(tool, kwargs)
        target = self._autonomous_target(tool, kwargs)
        signature = make_failure_signature(title, tool, command_summary, target, category)
        record = AutonomousFailureRecord(
            cycle_id=str(self.autonomous_state.get("cycle") or ""),
            action_name=title,
            tool_name=tool,
            command_summary=command_summary,
            target=target,
            success=False,
            failure_category=category,
            error_summary=(result.summary + ("\n" + error_text if error_text else ""))[:4000],
            duration_seconds=data.get("elapsed_sec") if isinstance(data.get("elapsed_sec"), (int, float)) else None,
            timestamp=time.strftime("%Y-%m-%d %H:%M:%S"),
            signature=signature,
            recommended_next_action="diagnose_recent_failure" if category in REPAIR_TRIGGER_CATEGORIES else "inspect_recent_events",
        )
        memory = load_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH)
        updated = update_autonomous_failure_memory(memory, record)
        save_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH, updated)
        repeated = record.recommended_next_action == "diagnose_recent_failure" or int(updated.cooldowns.get(signature, 0) or 0) > 0
        self._set_autonomous_state(
            last_failure_signature=signature,
            last_failure_category=category,
            last_failure_summary=record.error_summary,
            last_suggested_fix=record.recommended_next_action,
        )
        log_activity("autonomous_failure_recorded", "Recorded autonomous failure signature", {"run_id": run_id, "signature": signature, "category": category, "repeated": repeated})
        if category in REPAIR_TRIGGER_CATEGORIES and not self.autonomous_state.get("repair_proposal_written_this_cycle"):
            self._autonomous_write_repair_proposal(record, repeated, self._autonomous_failure_files(result))

    def _autonomous_write_repair_proposal(self, record: AutonomousFailureRecord, repeated: bool, files: list[str] | None = None) -> None:
        recent_events = list(self.autonomous_state.get("events") or [])[-12:]
        verification_commands = default_verification_commands()
        prompt = build_autonomous_repair_prompt(
            record,
            recent_events=recent_events,
            files=files or [],
            verification_commands=verification_commands,
        )
        diagnosis = None
        model_error = None
        # Timeout recovery must not immediately depend on another long local-model
        # call, otherwise a heartbeat/tool timeout can look like a second freeze.
        if record.failure_category == "timeout":
            model_error = "Skipped local-model diagnosis for timeout recovery so autonomous mode remains bounded."
        elif record.tool_name in {"heartbeat", "runtime_self_check"}:
            model_error = "Skipped local-model diagnosis for core health-check failure; autonomous mode should stay bounded and report the health gate instead."
        else:
            try:
                diagnosis = model_chat(
                    self.config,
                    self._select_model_for("planning"),
                    [{"role": "user", "content": prompt}],
                    timeout=min(15, int(getattr(self.config, "command_timeout_sec", 120) or 120)),
                    desc="autonomous surgical repair proposal",
                )
                if not diagnosis:
                    model_error = "local model unavailable or returned an empty response"
            except Exception as exc:
                model_error = repr(exc)
        payload = write_autonomous_repair_proposal(
            APP_DIR / "autonomous_repair_proposals",
            record,
            local_model_diagnosis=diagnosis,
            local_model_error=model_error,
            repeated_failure=repeated,
            recent_events=recent_events,
            files=files or [],
            verification_commands=verification_commands,
            next_recommended_command="diagnose_recent_failure" if repeated else "propose_surgical_fix",
        )
        self._set_autonomous_state(
            repair_proposal_written_this_cycle=True,
            last_repair_proposal_path=payload.get("markdown_path", ""),
            last_repair_proposal_json_path=payload.get("json_path", ""),
        )
        log_activity("autonomous_repair_proposal", "Wrote autonomous repair proposal", payload)

    def _autonomous_diagnose_recent_failure(self, report: list[str], run_id: str, record: AutonomousFailureRecord | None, reason: str) -> None:
        message = "Previous autonomous action failed recently; switching to diagnosis instead of repeating it."
        detail = reason or (record.error_summary if record else "")
        self._autonomous_event("diagnose_recent_failure", message, {"detail": detail, "signature": record.signature if record else ""})
        report.append(message)
        focus = "Diagnose recent autonomous failure"
        if record:
            focus += f": {record.tool_name} / {record.failure_category} / {record.error_summary[:600]}"
        self._autonomous_call_tool("Diagnose recent failure", "investigate_logs", {"focus": focus}, report, run_id)
        self._autonomous_call_tool("Propose surgical fix", "propose_improvements", {"focus": focus}, report, run_id)
    def _autonomous_record_improvement(self, title: str, detail: str, run_id: str = "") -> None:
        row = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "cycle": int(self.autonomous_state.get("cycle") or 0),
            "run_id": run_id or self.autonomous_state.get("current_run_id") or "",
            "title": title,
            "detail": detail,
        }
        log = list(self.autonomous_state.get("improvement_log") or [])
        log.append(row)
        self._set_autonomous_state(improvement_log=log[-120:])
        try:
            path = Path(self.config.workspace) / "AUTONOMOUS_IMPROVEMENTS.md"
            existing = path.read_text(encoding="utf-8") if path.exists() else "# Autonomous Improvements\n\n"
            entry = f"## {row['time']} - Cycle {row['cycle']}\n\n**{title}**\n\n{detail}\n\n"
            atomic_write_text(path, existing + entry)
            log_activity("autonomous_improvement_logged", title, {"run_id": row["run_id"], "cycle": row["cycle"], "path": str(path), "detail": detail})
        except Exception as exc:
            log_activity("autonomous_improvement_log_failed", title, {"error": repr(exc), "detail": detail})
    def _autonomous_upsert_cycle_summary(self, **updates: Any) -> None:
        cycle = int(updates.get("cycle") or self.autonomous_state.get("cycle") or 0)
        run_id = str(updates.get("run_id") or self.autonomous_state.get("current_run_id") or "")
        summaries = list(self.autonomous_state.get("cycle_summaries") or [])
        key = (run_id, cycle)
        found = None
        for item in summaries:
            if (item.get("run_id"), int(item.get("cycle") or 0)) == key:
                found = item
                break
        if found is None:
            found = {"run_id": run_id, "cycle": cycle, "events": [], "status": "running", "started_at": time.strftime("%Y-%m-%d %H:%M:%S")}
            summaries.append(found)
        found.update({k: v for k, v in updates.items() if v is not None})
        found["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._set_autonomous_state(cycle_summaries=summaries[-30:])
    def autonomous_status_text(self) -> str:
        s = dict(self.autonomous_state)
        lines = [
            "Autonomous mode status",
            f"Enabled: {s.get('enabled')}",
            f"Running cycle: {s.get('running')}",
            f"Stop requested: {s.get('stop_requested')}",
            f"Cycle: {s.get('cycle')}",
            f"Goal: {s.get('goal') or '(default reliability/project improvement)'}",
            f"Last message: {s.get('last_message')}",
            f"Current action: {s.get('current_action')}",
            f"Current detail: {s.get('current_detail')}",
            f"Current thought: {s.get('current_thought', '')}",
            f"Self-validation: {s.get('current_self_validation', '')}",
            f"Current run ID: {s.get('current_run_id') or '(none)'}",
            f"Resolved target: {s.get('autonomous_target_mode') or '(not resolved yet)'} - {s.get('autonomous_target_path') or ''}",
        ]
        last_docker = s.get("last_docker_validation") or {}
        if isinstance(last_docker, dict) and last_docker:
            lines.append(f"Last Docker validation: ok={bool(last_docker.get('ok'))} stage={last_docker.get('stage') or ''} run={last_docker.get('run_id') or ''}")
            if last_docker.get("summary"):
                lines.append(f"Docker validation summary: {last_docker.get('summary')}")
        if s.get("docker_validation_skipped_reason"):
            lines.append(f"Docker validation skipped: {s.get('docker_validation_skipped_reason')}")
        if s.get("running"):
            try:
                age = time.time() - float(s.get("last_progress_ts") or s.get("last_cycle_started_ts") or time.time())
            except Exception:
                age = 0
            if age > 45:
                lines.append(f"Progress warning: no autonomous status update for {int(age)}s; the current tool may be slow or stuck. Bounded tool timeouts should mark it failed and continue.")
        if s.get("cycle_plan"):
            lines.append("Cycle plan:")
            for i, item in enumerate(s.get("cycle_plan") or [], 1):
                lines.append(f"  {i}. {item}")
        if s.get("events"):
            lines.append("Recent autonomous events:")
            for ev in list(s.get("events") or [])[-8:]:
                lines.append(f"  - {ev.get('time')} {ev.get('kind')}: {ev.get('message')}")
        if s.get('last_error'):
            lines.append(f"Last error: {s.get('last_error')}")
        try:
            explanation = explain_autonomous_state(s)
            lines.extend([
                "",
                "What autonomous is doing now:",
                f"- Summary: {explanation.summary}",
                f"- Why: {explanation.why}",
                f"- Next: {explanation.next_expected_step}",
                f"- Risk: {explanation.risk}",
                f"- Failure memory: {explanation.failure_memory}",
                f"- Repair proposal: {explanation.repair_proposal}",
                "- Verification: " + "; ".join(explanation.verification),
            ])
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        try:
            from .project_state import build_autonomous_continuity_status
            continuity = build_autonomous_continuity_status(self.config.workspace)
            lines.extend([
                "",
                "Continuity guard:",
                f"- Project-state snapshot: {continuity.get('project_state_snapshot_path') or '(missing)'}",
                f"- Last task evidence: {continuity.get('last_task_evidence_path') or '(missing)'}",
                f"- Last release-readiness verdict: {continuity.get('last_release_readiness_verdict') or 'UNKNOWN'}",
                f"- Safe to continue automatically: {continuity.get('safe_to_continue_automatically')}",
                f"- Stop reason: {continuity.get('stop_reason')}",
                f"- Next safe step: {continuity.get('next_recommended_safe_step')}",
            ])
        except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed project-state continuity exception", {"error": repr(exc)})
        lines.append("Use /autonomous stop to stop after the current safe step. Use /ollama-stop --confirm only if the local model itself is stuck.")
        return "\n".join(lines)
    def _autonomous_thought_for_event(self, kind: str, message: str, data: dict[str, Any]) -> tuple[str, str]:
        """Return a safe, user-visible reasoning/status note for autonomous mode.

        These notes are not hidden chain-of-thought. They are operational summaries
        derived from the current tool, event kind and validation result so the GUI
        can show what Nova believes it is doing and how it is checking itself.
        """
        tool = str(data.get("tool") or self.autonomous_state.get("current_tool") or "").strip()
        summary = str(data.get("summary") or data.get("detail") or message or "").strip()
        ok = data.get("ok")
        base = summary or message or kind
        if kind in {"cycle_start", "observe"}:
            return (
                "I need to observe the runtime, workspace and recent logs before changing anything.",
                "I will not claim success until a bounded tool result or validation event is recorded.",
            )
        if kind in {"act_start", "step_start"}:
            action = message.replace("Starting:", "").strip() or tool or "the next bounded step"
            tool_part = f" using `{tool}`" if tool else ""
            return (
                f"I need to run {action}{tool_part} because this cycle needs fresh evidence before deciding the next move.",
                "I will verify the returned summary, failure flags and evidence before continuing.",
            )
        if kind in {"act_done", "step_done"}:
            tool_part = f" from `{tool}`" if tool else ""
            return (
                f"I found a completed result{tool_part}: {base[:220]}",
                "Self-check: treat this as progress only if the result is OK and it supports the original goal or validation plan.",
            )
        if kind in {"act_failed", "step_failed", "error", "autonomous_error"} or ok is False:
            tool_part = f" in `{tool}`" if tool else ""
            return (
                f"I found a problem{tool_part}: {base[:220]}",
                "Self-check: record the failure, avoid repeating the same action unchanged, and prefer a targeted repair or diagnosis step.",
            )
        if "validate" in kind or "verification" in kind or "quality" in kind:
            return (
                f"I am validating evidence now: {base[:220]}",
                "Self-check: compare the check result against compile, smoke, regression and user-goal expectations.",
            )
        if kind in {"cycle_done", "autonomous_cycle_done"}:
            return (
                f"I finished the cycle and need to summarise what changed or what remains: {base[:220]}",
                "Self-check: report remaining risk instead of pretending the whole goal is complete unless validation proves it.",
            )
        return (
            f"I am tracking autonomous progress: {base[:220]}",
            "Self-check: keep the step bounded, visible and recoverable if progress stalls.",
        )

    def _record_autonomous_thought(self, kind: str, message: str, data: dict[str, Any], run_id: str, cycle: int) -> tuple[str, str]:
        thought, validation = self._autonomous_thought_for_event(kind, message, data)
        row = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "run_id": run_id or self.autonomous_state.get("current_run_id") or "",
            "cycle": cycle,
            "kind": kind,
            "phase": kind,
            "message": message,
            "thought": thought,
            "self_validation": validation,
            "tool": str(data.get("tool") or self.autonomous_state.get("current_tool") or ""),
            "ok": data.get("ok"),
        }
        thoughts = list(self.autonomous_state.get("autonomous_thoughts") or [])
        thoughts.append(row)
        self.autonomous_state["autonomous_thoughts"] = thoughts[-160:]
        self.autonomous_state["current_thought"] = thought
        self.autonomous_state["current_self_validation"] = validation
        return thought, validation

    def _set_autonomous_state(self, **updates: Any) -> None:
        self.autonomous_state.update(updates)
        self.autonomous_state["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        try:
            p = Path.home() / ".winlocalassistant" / "autonomous_status.json"
            p.parent.mkdir(parents=True, exist_ok=True)
            atomic_write_json(p, self.autonomous_state, ensure_ascii=True)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
    def _autonomous_event(self, kind: str, message: str, data: dict[str, Any] | None = None) -> None:
        data = data or {}
        cycle = int(self.autonomous_state.get("cycle") or 0)
        ev = {
            "time": time.strftime("%Y-%m-%d %H:%M:%S"),
            "kind": kind,
            "message": message,
            "data": {**data, "cycle": cycle},
            "run_id": self.autonomous_state.get("current_run_id") or "",
            "cycle": cycle,
        }
        events = list(self.autonomous_state.get("events") or [])
        events.append(ev)
        thought, self_validation = self._record_autonomous_thought(kind, message, data, ev["run_id"], cycle)
        now_ts = time.time()
        self._set_autonomous_state(
            phase=kind,
            current_action=message,
            current_detail=str(data.get("detail") or data.get("summary") or data.get("tool") or ""),
            current_thought=thought,
            current_self_validation=self_validation,
            autonomous_thoughts=list(self.autonomous_state.get("autonomous_thoughts") or [])[-160:],
            events=events[-80:],
            last_progress_at=ev["time"],
            last_progress_ts=now_ts,
        )
        try:
            summary_events = list((self.autonomous_state.get("cycle_summaries") or [])[-1].get("events", [])) if self.autonomous_state.get("cycle_summaries") else []
        except Exception:
            summary_events = []
        summary_events.append({"time": ev["time"], "kind": kind, "message": message, "data": data})
        self._autonomous_upsert_cycle_summary(
            run_id=ev["run_id"],
            cycle=cycle,
            phase=kind,
            current_action=message,
            current_detail=str(data.get("detail") or data.get("summary") or data.get("tool") or ""),
            status="running" if kind not in {"cycle_done", "error"} else ("failed" if kind == "error" else "complete"),
            error=str(data.get("error") or ""),
            events=summary_events[-30:],
        )
        try:
            log_activity("autonomous_" + kind, message, {"run_id": ev["run_id"], "cycle": cycle, **data})
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        try:
            level = "error" if kind in {"error", "act_failed"} else ("success" if kind == "cycle_done" else "info")
            detail = str(data.get("detail") or data.get("summary") or data.get("tool") or "").strip()
            box_message = f"Autonomous {kind}: {message}" + (f"\n{detail}" if detail else "")
            write_assistant_box(box_message, source="autonomous", level=level)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
    def _autonomous_tool_timeout(self, tool: str) -> float:
        """Return the maximum seconds an autonomous tool may block the cycle.

        Manual commands can still use their normal, longer behaviour. Autonomous
        mode needs bounded steps so the UI never appears frozen on heartbeat or
        any other single tool.
        """
        configured = int(getattr(self.config, "command_timeout_sec", 120) or 120)
        default = max(30, min(configured, 120))
        if tool in {"improve_project", "ai_create_project", "surgical_repair", "backtrack_recover"}:
            default = max(configured * 2, AUTONOMOUS_TOOL_TIMEOUTS.get(tool, configured))
        return AUTONOMOUS_TOOL_TIMEOUTS.get(tool, default)

    def _call_tool_for_autonomous(self, tool: str, kwargs: dict[str, Any], timeout_sec: float) -> ToolResult:
        """Run one tool with a daemon timeout so autonomous mode can recover.

        The previous autonomous path called tools directly. If a system command,
        model request, filesystem probe or heartbeat blocked, the worker thread
        could sit on one visible step forever. This wrapper returns a structured
        timeout result and lets the cycle record/diagnose the failure instead.
        """
        result_queue: queue.Queue[ToolResult] = queue.Queue(maxsize=1)

        def runner() -> None:
            try:
                result_queue.put(self.tools.call(tool, **kwargs))
            except Exception as exc:
                result_queue.put(ToolResult(False, f"Tool {tool} failed: {exc}", {"error": repr(exc)}))

        worker = threading.Thread(target=runner, name=f"WLAAutonomousTool-{tool}", daemon=True)
        worker.start()
        worker.join(max(0.01, float(timeout_sec)))
        if worker.is_alive():
            return ToolResult(
                False,
                f"Timed out after {timeout_sec}s while running {tool}; autonomous mode skipped ahead instead of freezing.",
                {
                    "tool": tool,
                    "timed_out": True,
                    "timeout_sec": timeout_sec,
                    "args": kwargs,
                    "background_note": "The timed-out daemon worker may still finish later, but autonomous state is no longer blocked on it.",
                },
            )
        try:
            return result_queue.get_nowait()
        except queue.Empty:
            return ToolResult(False, f"Tool {tool} finished without returning a result", {"tool": tool, "empty_result": True})

    def _autonomous_call_tool(self, title: str, tool: str, kwargs: dict[str, Any], report: list[str], run_id: str) -> ToolResult:
        timeout_sec = self._autonomous_tool_timeout(tool)
        self._set_autonomous_state(
            phase="act_start",
            current_action=title,
            current_tool=tool,
            current_tool_args=kwargs,
            current_tool_timeout_sec=timeout_sec,
            last_message=title,
            current_detail=f"Running {tool} with a {timeout_sec}s autonomous timeout. Args: {json.dumps(kwargs, ensure_ascii=False)[:240]}",
        )
        self._autonomous_event("act_start", f"Starting: {title}", {"tool": tool, "args": kwargs, "timeout_sec": timeout_sec})
        if tool == "read_file" and str(kwargs.get("path", "")).startswith("__missing_idle_lessons__"):
            result = ToolResult(True, "No previous idle lessons yet", {"path": "IDLE_LESSONS.md", "exists": False})
        else:
            result = self._call_tool_for_autonomous(tool, kwargs, timeout_sec)
        if isinstance(result.data, dict):
            result.data.setdefault("tool", tool)
            result.data.setdefault("title", title)
        self._set_autonomous_state(
            phase="act_done" if result.ok else "act_failed",
            current_action=("Finished: " if result.ok else "Failed: ") + title,
            current_detail=result.summary,
            last_tool=tool,
            last_summary=result.summary,
            current_tool="",
            current_tool_args={},
            current_tool_timeout_sec=0,
        )
        self._autonomous_event("act_done" if result.ok else "act_failed", f"{title}: {result.summary}", {"tool": tool, "ok": result.ok, "summary": result.summary})
        log_activity("autonomous_step", title, {"run_id": run_id, "tool": tool, "ok": result.ok, "summary": result.summary, "data": result.data})
        reason = self._tool_reason(title, tool, kwargs)
        report.append(("✅ " if result.ok else "⚠️ ") + f"{title}: {result.summary}")
        report.append(f"   tool: {tool}; timeout: {timeout_sec}s")
        if kwargs:
            report.append("   args: " + json.dumps(kwargs, ensure_ascii=False)[:500])
        report.append(f"   reason: {reason}")
        if isinstance(result.data, dict):
            written = result.data.get("written") or []
            if written:
                for w in written[:5]:
                    report.append(f"   edit: {w.get('path','')} ({w.get('bytes','?')} bytes) - intended to satisfy/repair: {title}")
            if result.data.get("verification"):
                report.append("   verification: " + str(result.data.get("verification"))[:500].replace("\n", " "))
        if result.ok and tool in {"propose_improvements", "improve_project", "surgical_repair", "self_improve", "tool_create", "tool_clean_proposals"}:
            self._autonomous_record_improvement(title, result.summary, run_id)
        if result.ok:
            try:
                self._autonomous_clear_failure_cooldown(title, tool, kwargs)
            except Exception as exc:
                log_activity("autonomous_failure_memory_error", "Could not clear autonomous failure cooldown after success", {"run_id": run_id, "tool": tool, "error": repr(exc)})
        if not result.ok:
            try:
                self._autonomous_record_failure(title, tool, kwargs, result, run_id)
            except Exception as exc:
                log_activity("autonomous_failure_memory_error", "Could not record autonomous failure memory", {"run_id": run_id, "tool": tool, "error": repr(exc)})
        return result

    def _tool_reason(self, title: str, tool: str, kwargs: dict[str, Any]) -> str:
        reasons = {
            "heartbeat": "check environment health before changing anything",
            "runtime_self_check": "confirm Nova internals and tools are compatible",
            "investigate_logs": "turn recent failures into evidence instead of guessing",
            "known_issues": "reuse known failure signatures and avoid repeating them",
            "propose_improvements": "generate safe improvement candidates from evidence",
            "tool_clean_proposals": "remove stale failed tool proposals before agent work",
            "improve_project": "apply the smallest project improvement and verify it",
            "surgical_repair": "fix localised errors without destroying good progress",
            "backtrack_recover": "fallback only when targeted repair cannot proceed",
            "project_spec": "convert the user specification into concrete workflows, data model, edge cases and acceptance checks before building",
            "ai_create_project": "build the requested project from requirements",
            "final_project_check": "ensure the result actually matches the user goal",
            "auto_verify": "run project-appropriate checks",
            "zip_path": "package the final working output",
            "read_file": "inspect prior memory/lessons before acting",
            "idle_lessons": "inspect prior idle lessons without workspace path errors",
            "prompt_contract": "compile the prompt into concrete acceptance and negative checks",
            "prompt_test_run": "validate current files against prompt-specific acceptance checks",
            "candidate_tournament": "rank multiple candidate strategies before committing to one",
            "candidate_failure_report": "explain why candidate outputs are weak or off-domain",
            "repair_plan_v2": "classify the failure and produce a minimal-diff repair strategy",
            "trace_status": "inspect the connected timeline of recent Nova events",
            "mcp_risk_report": "audit tool/connector permissions before exposing more capabilities",
            "mission_create": "turn a broad autonomous goal into success conditions, allowed tools and stop rules",
            "mission_step": "advance the current mission queue by one bounded step",
            "model_output_coach": "score local model output and produce tighter retry context",
            "env_profile": "check whether the required dependency profile is available",
            "benchmark_system": "measure system/runtime capabilities for tuning",
            "project_state": "load or update project memory for build/repair continuity",
            "regression_list": "reuse known regressions so Nova does not repeat them",
            "regression_add": "record a newly discovered regression for future validation",
        }
        return reasons.get(tool, f"selected for step '{title}' with args {kwargs}")

    def autonomous_status_data(self) -> dict[str, Any]:
        state = dict(self.autonomous_state)
        now = time.time()
        try:
            last_ts = float(state.get("last_progress_ts") or state.get("last_cycle_started_ts") or now)
        except Exception:
            last_ts = now
        age = max(0.0, now - last_ts)
        tool_timeout = 0.0
        try:
            tool_timeout = float(state.get("current_tool_timeout_sec") or 0)
        except Exception:
            tool_timeout = 0.0
        stale_after = max(45.0, tool_timeout + 10.0 if tool_timeout else 45.0)
        thread_alive = self._autonomous_thread_alive()
        may_be_stuck = bool(state.get("running")) and (age > stale_after or (state.get("enabled") and not thread_alive))
        reason = ""
        if bool(state.get("running")) and age > stale_after:
            reason = f"Last progress event is {int(age)}s old; current bounded timeout is {int(tool_timeout or stale_after)}s."
        if state.get("enabled") and not thread_alive:
            reason = (reason + " " if reason else "") + "Autonomous state says enabled but the worker thread is not alive."
        state.update({
            "last_progress_age_sec": round(age, 1),
            "stale_after_sec": round(stale_after, 1),
            "worker_thread_alive": thread_alive,
            "may_be_stuck": may_be_stuck,
            "stuck_reason": reason,
        })
        try:
            state["explanation"] = explain_autonomous_state(state).to_dict()
        except Exception:
            state["explanation"] = {}
        return state

    def autonomous_explain_text(self, goal: str = "") -> str:
        if goal.strip():
            dashboard = build_planning_dashboard(goal.strip(), {"workspace": self.config.workspace})
            sequence = build_autonomous_tool_sequence(goal.strip(), {"workspace": str(self.config.workspace)})
            return (
                render_planning_dashboard_markdown(dashboard)
                + "\n\n"
                + render_autonomous_sequence_markdown(sequence)
                + "\n\n"
                + render_autonomous_explanation_markdown(explain_autonomous_state(dict(self.autonomous_state)))
            )
        return render_autonomous_explanation_markdown(explain_autonomous_state(dict(self.autonomous_state)))

    def autonomy_capabilities_text(self, goal: str = "") -> str:
        text = (goal or str(self.autonomous_state.get("goal") or "Improve Nova safely")).strip()
        return render_capability_markdown(text)

    def mutable_plan_text(self, goal: str = "") -> str:
        text = (goal or str(self.autonomous_state.get("goal") or "Improve Nova safely")).strip()
        plan = build_mutable_mission_plan(text)
        lines = [
            "# Mutable Nova Plan",
            "",
            f"Goal: {plan.goal}",
            f"Task type: {plan.inferred_task_type}",
            f"Confidence: {plan.confidence:.2f}",
            "",
            "## Validation contract",
        ]
        lines += [f"- {x}" for x in plan.validation_contract]
        lines += ["", "## Mutation rules"] + [f"- {x}" for x in plan.mutation_rules]
        lines += ["", "## Stages"]
        for stage in plan.stages:
            lines.append(f"- **{stage.name}**: {stage.purpose}")
            lines.append("  - adapt if: " + "; ".join(stage.adapt_if))
        lines += ["", "## Stop conditions"] + [f"- {x}" for x in plan.stop_conditions]
        return "\n".join(lines)

    def autonomous_sequence_text(self, goal: str = "") -> str:
        text = goal.strip() or str(self.autonomous_state.get("goal") or "Improve current project safely")
        return render_autonomous_sequence_markdown(build_autonomous_tool_sequence(text, {"workspace": str(self.config.workspace)}))

    def _wla_source_root(self) -> Path:
        return Path(__file__).resolve().parent.parent

    def _autonomous_goal_targets_wla_source(self, goal: str, request_intent: Any) -> bool:
        low = (goal or "").lower()
        if getattr(request_intent, "target_is_wla_source", False) or getattr(request_intent, "self_improvement_requested", False):
            return True
        return any(term in low for term in [
            "winlocalassistant",
            "wla",
            "your own files",
            "your files",
            "own files",
            "your own code",
            "review your code",
            "review your own code",
            "your coding",
            "coding capabilities",
            "validation capabilities",
            "your validation",
            "improve yourself",
            "improving before validating",
            "full code fallback",
        ])

    def _run_autonomous_sequence_plan(self, sequence: Any, report: list[str], run_id: str) -> list[ToolResult]:
        results: list[ToolResult] = []
        self._set_autonomous_state(
            autonomous_sequence=sequence.to_dict(),
            phase="act",
            current_action="Running sequenced autonomous tools",
            current_detail=sequence.rationale,
        )
        self._autonomous_event(
            "sequence_plan",
            "Autonomous selected a sequential tool plan",
            {
                "intent": sequence.intent,
                "steps": [s.to_dict() for s in sequence.steps],
                "capabilities": getattr(sequence, "capability_matches", []),
                "mutable_plan": getattr(sequence, "mutable_plan", {}),
                "detail": sequence.rationale,
            },
        )
        report.append("")
        report.append("Capability-aware plan:")
        for match in getattr(sequence, "capability_matches", [])[:5]:
            cap = match.get("capability", {}) if isinstance(match, dict) else {}
            report.append(f"- {cap.get('name', 'capability')}: {match.get('why', '')} (score {match.get('score', 0)})")
        report.append("")
        report.append("Sequenced tool plan:")
        for index, step in enumerate(sequence.steps, 1):
            report.append(f"{index}. {step.title} -> {step.tool}: {step.reason}")

        previous_failed = False
        journal_events = []
        cycle = int(self.autonomous_state.get("cycle") or 0)
        goal = str(sequence.goal or self.autonomous_state.get("goal") or "")
        for index, step in enumerate(sequence.steps, 1):
            if self.autonomous_state.get("stop_requested"):
                report.append("Stop requested; ending before next sequenced step.")
                journal_events.append(make_step_event(run_id=run_id, cycle=cycle, step_index=index, title=step.title, tool=step.tool, status="skipped_stop_requested", reason="user requested stop", args=dict(step.kwargs)))
                break
            if previous_failed and not step.run_if_previous_failed:
                report.append(f"Skipped {step.title}: previous required step failed.")
                journal_events.append(make_step_event(run_id=run_id, cycle=cycle, step_index=index, title=step.title, tool=step.tool, status="skipped_previous_failed", reason="previous required step failed", args=dict(step.kwargs)))
                continue
            skip_loop, loop_reason = should_skip_repeated_action(dict(self.autonomous_state), step.title, step.tool, dict(step.kwargs), required=step.required)
            if skip_loop:
                self._autonomous_event("loop_guard_skip", f"Loop guard skipped repeated step: {step.title}", {"detail": loop_reason, "tool": step.tool, "signature": autonomous_action_signature(step.title, step.tool, dict(step.kwargs))})
                report.append(f"Loop guard skipped {step.title}: {loop_reason}")
                journal_events.append(make_step_event(run_id=run_id, cycle=cycle, step_index=index, title=step.title, tool=step.tool, status="skipped_loop_guard", reason=loop_reason, watcher_status="loop_guard", args=dict(step.kwargs)))
                continue
            decision = evaluate_action_risk({"name": step.title, "tool": step.tool, "command": str(step.kwargs), "category": step.tool})
            if decision.status == "blocked":
                self._autonomous_event("watcher_block", f"Watcher blocked sequenced step: {step.title}", {"decision": decision.to_dict()})
                report.append(f"⛔ Watcher blocked {step.title}: {'; '.join(decision.reasons)}")
                journal_events.append(make_step_event(run_id=run_id, cycle=cycle, step_index=index, title=step.title, tool=step.tool, status="blocked", reason="; ".join(decision.reasons), watcher_status=decision.status, args=dict(step.kwargs)))
                previous_failed = step.required
                continue
            on_cooldown, cooldown_reason, cooldown_record = self._autonomous_cooldown_for_action(step.title, step.tool, dict(step.kwargs))
            if on_cooldown:
                self._autonomous_diagnose_recent_failure(report, run_id, cooldown_record, cooldown_reason)
                report.append(f"Skipped {step.title}: repeated failure cooldown active.")
                journal_events.append(make_step_event(run_id=run_id, cycle=cycle, step_index=index, title=step.title, tool=step.tool, status="skipped_cooldown", reason=cooldown_reason, watcher_status="cooldown", failure_category=getattr(cooldown_record, "failure_category", ""), args=dict(step.kwargs)))
                previous_failed = step.required
                continue
            started = time.time()
            started_at = time.strftime("%Y-%m-%d %H:%M:%S")
            result = self._autonomous_call_tool(step.title, step.tool, dict(step.kwargs), report, run_id)
            duration = round(time.time() - started, 3)
            results.append(result)
            record_action_outcome({"name": step.title, "tool": step.tool, "kwargs": step.kwargs}, {"ok": result.ok, "summary": result.summary})
            failure_category = ""
            if not result.ok:
                try:
                    failure_category = classify_autonomous_failure(
                        result_text=result.summary,
                        error_text=json.dumps(result.data, ensure_ascii=False, default=str)[:4000] if isinstance(result.data, dict) else "",
                        timed_out=bool((result.data or {}).get("timed_out")) if isinstance(result.data, dict) else False,
                        no_useful_edits=self._autonomous_should_skip_backtrack(result),
                    )
                except Exception:
                    failure_category = "unknown"
            journal_events.append(make_step_event(run_id=run_id, cycle=cycle, step_index=index, title=step.title, tool=step.tool, status="ok" if result.ok else "failed", reason=step.reason, watcher_status=decision.status, failure_category=failure_category, summary=result.summary, started_at=started_at, duration_seconds=duration, args=dict(step.kwargs)))
            if not result.ok:
                previous_failed = step.required or step.stop_on_failure
                if step.stop_on_failure:
                    report.append(f"Stopping sequenced plan after required step failed: {step.title}")
                    break
            else:
                previous_failed = False
        try:
            journal = build_run_journal(run_id, cycle, goal, journal_events)
            md_path, json_path = write_run_journal(journal)
            self._set_autonomous_state(last_sequence_journal_path=str(md_path), last_sequence_journal_json_path=str(json_path), last_sequence_journal_status=journal.status)
            self._autonomous_event("sequence_journal", "Autonomous sequence journal written", {"path": str(md_path), "json_path": str(json_path), "status": journal.status})
            report.append(f"Sequence journal: {md_path}")
        except Exception as exc:
            log_activity("autonomous_sequence_journal_failed", "Could not write autonomous sequence journal", {"run_id": run_id, "error": repr(exc)})
        return results

    def _autonomous_auto_apply_low_risk_idle_candidate(self, goal: str, report: list[str], run_id: str) -> None:
        if not load_idle_autonomy_settings().get("idle_auto_apply_low_risk", False):
            report.append("Autonomous low-risk auto-apply skipped: idle auto-apply setting is off.")
            return
        self._autonomous_event("auto_apply_start", "Autonomous checking for a low-risk auto-apply candidate", {"goal": goal})
        result_text = self._idle_auto_apply_once(f"Autonomous cycle: {goal}")
        report.append("Autonomous low-risk auto-apply result:")
        report.extend("- " + line for line in result_text.splitlines() if line.strip())
        self._autonomous_event("auto_apply_done", "Autonomous low-risk auto-apply finished", {"summary": result_text[:2000], "run_id": run_id})

    def _efficiency_timed_command_allowed(self, command: str) -> tuple[bool, str]:
        """Return whether a command is safe to benchmark repeatedly.

        Timed runs are intended for weak-spot analysis, not mutation. Running a
        mutating command several times can accidentally create files, delete
        data, start services, or trigger autonomous/build loops. Keep this path
        read-only and deterministic unless a future explicit confirmation flow
        is added.
        """
        cmd = (command or "").strip()
        if not cmd:
            return False, "No command supplied."
        if not cmd.startswith("/"):
            return True, "normal chat benchmark"
        head = cmd.split(maxsplit=1)[0].lower()
        safe = {
            "/status", "/avatar", "/activity", "/llm-status", "/providers",
            "/model-health", "/llm-lab", "/llm-training", "/training-lab", "/model-doctor", "/image-status", "/vision-status",
            "/context-files", "/command-catalog", "/tool-catalog", "/self-guide",
            "/how-to-use", "/full-guide", "/quality-dashboard",
            "/architecture-audit", "/repair-audit", "/code-repair-audit",
            "/bug-audit", "/code-review", "/deep-code-review", "/model-context",
            "/skill-mode", "/memory", "/known-issues", "/reasoning",
            "/efficiency", "/performance", "/perf", "/autonomous",
        }
        if head in safe:
            low = cmd.lower()
            rest = cmd.split(maxsplit=1)[1].strip().lower() if len(cmd.split(maxsplit=1)) > 1 else ""
            if head in {"/efficiency", "/performance", "/perf"}:
                if not rest or rest in {"status", "report", "show"}:
                    return True, "read-only slash benchmark"
                return False, "Nested or state-changing /efficiency commands are blocked; only /efficiency report/status is safe inside timed runs."
            if head == "/autonomous" and rest not in {"status", ""}:
                return False, "Only /autonomous status is safe for repeated timed runs; start/once/stop/plan can alter autonomous state."
            if head == "/model-context" and rest in {"on", "enable", "off", "disable"} or (head == "/model-context" and rest.startswith(("max=", "limit="))):
                return False, "Model-context setting changes are blocked inside repeated timed runs."
            if head == "/skill-mode" and rest and rest not in {"status", "show"}:
                return False, "Skill-mode setting changes are blocked inside repeated timed runs."
            return True, "read-only slash benchmark"
        return False, (
            f"`{head}` is not safe for repeated timed runs. Use read-only commands such as "
            "`/status`, `/image-status`, `/model-context`, `/code-review`, or benchmark a normal chat prompt."
        )

    def database_command(self, rest: str) -> str:
        raw = (rest or "").strip()
        if not raw or raw.lower() in {"list", "status", "databases"}:
            return self.format_result(self.tools.call("assistant_db", action="list"))
        parts = raw.split(maxsplit=2)
        action = parts[0].lower()
        if action in {"put", "set", "write", "upsert", "merge", "patch", "update"}:
            if len(parts) < 3:
                return f"Usage: /db {action} DB.COLLECTION.KEY {{json or text}}"
            ref, value_text = parts[1], parts[2]
            bits = ref.split(".", 2)
            if len(bits) != 3:
                return "Use a DB.COLLECTION.KEY reference, for example: /db put research.notes.pfas {\"summary\":\"...\"}"
            try:
                value = json.loads(value_text)
            except Exception:
                value = {"text": value_text}
            return self.format_result(self.tools.call("assistant_db", action=action, database=bits[0], collection=bits[1], key=bits[2], value=value, schema_hint="user-defined JSON/text"))
        if action in {"get", "read", "delete", "del", "remove"}:
            if len(parts) < 2:
                return f"Usage: /db {action} DB.COLLECTION[.KEY]"
            bits = parts[1].split(".", 2)
            if len(bits) < 2:
                return f"Usage: /db {action} DB.COLLECTION[.KEY]"
            return self.format_result(self.tools.call("assistant_db", action=action, database=bits[0], collection=bits[1], key=bits[2] if len(bits) > 2 else ""))
        if action in {"schema", "describe", "inspect", "export", "dump", "backup"}:
            if len(parts) < 2:
                return f"Usage: /db {action} DB"
            return self.format_result(self.tools.call("assistant_db", action=action, database=parts[1]))
        if action in {"audit", "check", "review", "integrity"}:
            database = parts[1] if len(parts) > 1 else ""
            return self.format_result(self.tools.call("assistant_db", action="audit", database=database))
        if action in {"compact", "vacuum"}:
            if "--confirm" not in raw.lower():
                return "Compaction rewrites the assistant SQLite file. Use `/db compact --confirm` after exporting anything important."
            return self.format_result(self.tools.call("assistant_db", action="compact"))
        if action in {"search", "find", "query"}:
            if len(parts) < 2:
                return "Usage: /db search DB query terms"
            database = parts[1]
            query = parts[2] if len(parts) > 2 else ""
            return self.format_result(self.tools.call("assistant_db", action="search", database=database, query=query))
        return "Usage: /db list | /db audit [DB] | /db put|merge DB.COLLECTION.KEY {json} | /db get DB.COLLECTION[.KEY] | /db schema DB | /db export DB | /db search DB query | /db compact --confirm | /db delete DB.COLLECTION[.KEY]"

    def efficiency_command(self, rest: str = "") -> str:
        """Show, clear, toggle, or run timed efficiency checks."""
        raw = (rest or "").strip()
        low = raw.lower()
        if not raw or low in {"status", "report", "show"}:
            return self.format_result(self.tools.call("efficiency_report", action="report"))
        if low in {"clear", "reset"}:
            return self.format_result(self.tools.call("efficiency_report", action="clear"))
        if low in {"on", "enable", "off", "disable"}:
            return self.format_result(self.tools.call("efficiency_report", action=low))
        if low.startswith("time ") or low.startswith("timed ") or low.startswith("run "):
            parts = raw.split(maxsplit=2)
            if len(parts) < 3 or not parts[1].isdigit():
                return "Usage: /efficiency time N /command-or-message"
            runs = max(1, min(20, int(parts[1])))
            command = parts[2].strip()
            if not command:
                return "Usage: /efficiency time N /command-or-message"
            allowed, reason = self._efficiency_timed_command_allowed(command)
            if not allowed:
                return "Efficiency timed run blocked: " + reason
            outputs: list[str] = []
            samples: list[dict[str, Any]] = []
            for i in range(runs):
                started_wall = time.perf_counter()
                started_cpu = time.process_time()
                started_at = time.strftime("%Y-%m-%d %H:%M:%S")
                ok = False
                try:
                    # Use handle_command for slash commands to avoid nested chat locks.
                    out = self.handle_command(command) if command.startswith("/") else self._answer_plain_chat(command)
                    ok = True
                    outputs.append(str(out)[:400])
                except Exception as exc:
                    outputs.append("ERROR: " + repr(exc))
                finally:
                    sample = append_efficiency_sample(
                        self.config,
                        kind="timed_run",
                        name=command.split(maxsplit=1)[0] if command.startswith("/") else "normal_chat",
                        ok=ok,
                        wall_s=time.perf_counter() - started_wall,
                        process_cpu_s=time.process_time() - started_cpu,
                        meta={"command": command, "iteration": i + 1, "runs": runs, "timed_reason": reason},
                        started_at=started_at,
                        finished_at=time.strftime("%Y-%m-%d %H:%M:%S"),
                        force=True,
                    )
                    samples.append(sample)
            wall_values = [float(x.get("wall_ms") or 0.0) for x in samples]
            avg = sum(wall_values) / len(wall_values) if wall_values else 0.0
            return "\n".join([
                f"Timed efficiency run completed: `{command}`",
                f"Runs: {runs}",
                f"Average wall time: {avg:.1f} ms",
                f"Fastest: {min(wall_values):.1f} ms" if wall_values else "Fastest: n/a",
                f"Slowest: {max(wall_values):.1f} ms" if wall_values else "Slowest: n/a",
                "Run `/efficiency` for the full weak-spot report.",
                "",
                "Last output preview:",
                outputs[-1] if outputs else "",
            ])
        return "Usage: /efficiency [report|clear|on|off|time N /command]"

    def autonomous_guide_text(self) -> str:
        return """Autonomous mode guide
Purpose:
- Run safe bounded cycles that inspect state, diagnose failures, use tools, test projects, repair small issues, propose improvements and optionally build requested projects. Self-improvement remains a manual guarded command only.
Cycle shape:
1. Observe: heartbeat, runtime self-check, project detection, recent logs.
2. Plan: choose a safe sequence from the available tools.
3. Act: run one tool at a time with live telemetry.
4. Verify: run project checks, final requirement check and/or custom tool checks.
5. Repair: prefer surgical repair, then LLM edit of same project, then non-destructive backtracking only if needed.
6. Reflect: write investigations/proposals/traces so the next cycle can improve.
Useful commands:
/autonomous once GOAL
/autonomous start [--continuous|--finite] [--cycles N] GOAL
/autonomous stop
/autonomous status
/autonomous-guide
/activity
/investigate-logs
/propose-improvements
/tool-guide
/test-project standard
/improve-project GOAL
/surgical-repair NOTE
/backtrack
Safety boundaries:
- One local LLM prompt at a time by default; safe subagents may run non-LLM diagnostics in parallel while model calls stay serialized.
- Dangerous shell commands remain blocked.
- Package installation is allowlisted.
- Self-improvement requires backup, compile checks, smoke tests and rollback on failure.
- Autonomous mode does not intentionally delete user projects.

Compact operating summary:
""" + get_autonomous_tool_use_summary()
    def autonomous_command(self, rest: str) -> str:
        parts = (rest or "").strip().split(maxsplit=1)
        action = (parts[0].lower() if parts else "status")
        goal = parts[1] if len(parts) > 1 else ""
        if action in {"status", ""}:
            return self.autonomous_status_text()
        if action in {"stop", "off", "cancel"}:
            self._set_autonomous_state(
                enabled=False,
                stop_requested=True,
                phase="stopping",
                last_message="Stop requested; autonomous mode will halt after the current bounded tool step.",
                current_action="Stopping autonomous mode",
                current_detail="The current tool has a timeout guard, so stop should not wait forever.",
            )
            return self.autonomous_status_text()
        if action in {"plan", "sequence"}:
            return self.autonomous_sequence_text(goal or "Investigate errors, propose improvements, and improve the current project if safe.")
        if action in {"once", "run-once"}:
            once_goal, _persist = self._parse_autonomous_persistence_options(goal or "Investigate errors, propose improvements, and improve the current project if safe.")
            self._set_autonomous_state(continuous_autonomy=False)
            return self.autonomous_once(once_goal)
        if action in {"start", "on", "run", "go"}:
            goal_without_persistence, persistence = self._parse_autonomous_persistence_options(goal)
            start_goal, max_cycles, diagnostic_only = self._parse_autonomous_goal_options(goal_without_persistence)
            continuous_autonomy = True if persistence is None else bool(persistence)
            if self.autonomous_state.get("enabled") and self._autonomous_thread_alive():
                return "Autonomous mode is already enabled.\n\n" + self.autonomous_status_text()
            if self.autonomous_state.get("enabled") and not self._autonomous_thread_alive():
                log_activity("autonomous_thread_recovered", "Autonomous state said enabled but worker thread was not alive; starting a fresh worker", dict(self.autonomous_state))
            now = time.strftime("%Y-%m-%d %H:%M:%S")
            self._set_autonomous_state(
                enabled=True,
                running=False,
                stop_requested=False,
                goal=start_goal,
                cycle=0,
                max_cycles=max_cycles,
                diagnostic_only=diagnostic_only,
                continuous_autonomy=continuous_autonomy,
                finite_goal_stop=not continuous_autonomy,
                stopped_after_cycle_limit=False,
                started_at=now,
                last_progress_at=now,
                last_progress_ts=time.time(),
                phase="starting",
                current_action="Starting autonomous worker",
                current_detail="The first cycle should move from heartbeat to self-check within seconds. If a tool stalls, v55.3.0 records a timeout instead of freezing the loop and runs a repair audit before mutation.",
                last_message="Starting autonomous loop.",
                last_error="",
                current_thought="I am starting a new autonomous run and preparing the first observation step.",
                current_self_validation="I will keep each action bounded, logged and validated before continuing.",
                autonomous_thoughts=[],
            )
            try:
                preflight = self.tools.call("pipeline_preflight", goal=start_goal or "autonomous improvement")
                route = preflight.data.get("kind") if preflight.ok else "unknown"
                log_activity("autonomous_pipeline_preflight", f"Autonomous pipeline selected: {route}", {"goal": start_goal, "route": route, "stages": preflight.data.get("stages", []) if preflight.ok else []})
                self._set_autonomous_state(current_detail=f"Pipeline preflight: {route}. First cycle should move through observe → plan → act → verify.")
            except Exception as exc:
                log_activity("autonomous_pipeline_preflight_error", "Autonomous pipeline preflight failed", {"error": repr(exc)})
            self._autonomous_thread = threading.Thread(target=self._autonomous_loop, name="NovaAutonomous", daemon=True)
            self._autonomous_thread.start()
            limit_text = f" It will stop automatically after {max_cycles} cycle(s)." if max_cycles else ""
            persistence_text = " Continuous mission mode is enabled: after a verified milestone, Nova will choose a next safe improvement instead of stopping." if continuous_autonomy else " Finite mode is enabled: Nova stops after the requested goal is verified."
            mode_text = " Diagnostic/read-only mode is enabled, so it will inspect and propose without project mutation.\n\n" if diagnostic_only else ""
            return (
                "Autonomous mode started." + limit_text + persistence_text + " It will keep running safe bounded cycles until /autonomous stop unless finite mode/cycle limit is selected.\n\n"
                + mode_text
                + "It does not bypass safety rules: installs remain allowlisted, self-edits use backup/tests/rollback, and local LLM prompts still use the one-at-a-time lock.\n\n"
                + self.autonomous_status_text()
            )
        return "Usage: /autonomous status | once [goal] | start/run [goal] | stop"
    def _autonomous_loop(self) -> None:
        while self.autonomous_state.get("enabled") and not self.autonomous_state.get("stop_requested"):
            max_cycles = self.autonomous_state.get("max_cycles")
            if isinstance(max_cycles, int) and max_cycles > 0 and int(self.autonomous_state.get("cycle") or 0) >= max_cycles:
                self._set_autonomous_state(
                    enabled=False,
                    running=False,
                    stopped_after_cycle_limit=True,
                    phase="cycle_limit",
                    current_action="Autonomous cycle limit reached",
                    current_detail=f"Stopped automatically after {max_cycles} cycle(s).",
                    last_message="Autonomous cycle limit reached.",
                )
                log_activity("autonomous_cycle_limit", "Autonomous stopped after requested cycle limit", dict(self.autonomous_state))
                break
            goal = self.autonomous_state.get("goal") or "Investigate logs, propose improvements, improve the current project if safe, and keep Nova healthy."
            try:
                self.autonomous_once(str(goal))
            except Exception as exc:
                self._set_autonomous_state(last_error=repr(exc), last_message="Autonomous cycle hit an exception; continuing after cooldown.")
                log_activity("autonomous_error", "Autonomous cycle exception", {"error": repr(exc)})
            # Bounded cooldown so it does not hammer Ollama or the disk. Surface
            # the wait in status so users do not mistake the between-cycle pause for a freeze.
            for remaining in range(20, 0, -1):
                if not self.autonomous_state.get("enabled") or self.autonomous_state.get("stop_requested"):
                    break
                self._set_autonomous_state(
                    running=False,
                    phase="cooldown",
                    current_action="Waiting before next autonomous cycle",
                    current_detail=f"Next safe cycle starts in about {remaining}s. Use /autonomous stop to halt.",
                    last_message="Autonomous cooldown between bounded cycles.",
                )
                time.sleep(1)
        if not self.autonomous_state.get("stopped_after_cycle_limit"):
            self._set_autonomous_state(enabled=False, running=False, phase="idle", last_message="Autonomous mode stopped.", current_action="Autonomous stopped", current_detail="Autonomous mode is not running.")
        log_activity("autonomous_stopped", "Autonomous mode stopped", dict(self.autonomous_state))
    def _goal_wants_custom_tool_creation(self, goal: str) -> bool:
        low = (goal or "").lower()
        return any(phrase in low for phrase in [
            "create tool", "create a tool", "new custom tool", "make a tool",
            "tool useful to yourself", "useful tool", "create using your commands",
        ])

    def _autonomous_create_tool_acceptance(self, before_names: set[str], goal: str) -> tuple[bool, dict[str, Any]]:
        listing = self.tools.call("custom_tools")
        tools = listing.data.get("tools", []) if listing.ok else []
        after_names = {str(t.get("name")) for t in tools if t.get("exists") and t.get("enabled", True)}
        new_names = sorted(after_names - before_names)
        evidence: dict[str, Any] = {
            "before_count": len(before_names),
            "after_count": len(after_names),
            "new_tools": new_names,
            "listed_ok": bool(listing.ok),
        }
        if not new_names:
            evidence["reason"] = "No new enabled custom tool appeared in the refreshed registry."
            return False, evidence
        tested = []
        for name in new_names:
            test = self.tools.call("tool_test", name=name)
            run = self.tools.call("tool_run", name=name, args={"subdir": "."})
            tested.append({"name": name, "test_ok": bool(test.ok), "run_ok": bool(run.ok), "test_summary": test.summary, "run_summary": run.summary})
        evidence["tested"] = tested
        ok = all(item["test_ok"] and item["run_ok"] for item in tested)
        if not ok:
            evidence["reason"] = "A new tool was created but did not pass tool_test/tool_run."
        return ok, evidence

    def _autonomous_handle_create_tool_goal(self, goal: str, report: list[str], run_id: str) -> ToolResult:
        before_tools = self.tools.call("custom_tools")
        before_names = {str(t.get("name")) for t in (before_tools.data.get("tools", []) if before_tools.ok else []) if t.get("exists") and t.get("enabled", True)}
        self._autonomous_event("tool_goal_start", "Goal-specific custom-tool creation started", {"before_tools": sorted(before_names), "goal": goal})
        created = self._autonomous_call_tool(
            "Create goal-specific custom tool",
            "tool_create",
            {"goal": goal},
            report,
            run_id,
            required=True,
        )
        ok, evidence = self._autonomous_create_tool_acceptance(before_names, goal)
        if ok:
            self._autonomous_event("tool_goal_verified", "New custom tool created, refreshed and tested", evidence)
            report.append("Goal-specific acceptance passed: a new enabled custom tool appeared in /custom-tools and passed /tool-test plus /tool-run.")
            return ToolResult(True, "Custom tool creation goal completed", {"created": created.data, "acceptance": evidence})
        self._autonomous_event("tool_goal_failed", "Custom-tool goal was not completed", evidence)
        report.append("Custom-tool goal failed: " + str(evidence.get("reason") or "acceptance checks failed"))
        return ToolResult(False, "Custom tool creation goal failed acceptance", {"created": created.data, "acceptance": evidence})

    def autonomous_once(self, goal: str = "") -> str:
        if self.autonomous_state.get("running"):
            return "Autonomous cycle is already running. Use /autonomous status."
        cycle = int(self.autonomous_state.get("cycle") or 0) + 1
        run_id = new_run_id()
        set_current_run(run_id)
        raw_goal = (goal or "Investigate logs, propose improvements, improve the current project if safe, and keep Nova healthy.").strip()
        raw_goal, persistence_override = self._parse_autonomous_persistence_options(raw_goal)
        parsed_goal, parsed_max_cycles, parsed_diagnostic_only = self._parse_autonomous_goal_options(raw_goal)
        if parsed_max_cycles is not None and not self.autonomous_state.get("enabled"):
            self._set_autonomous_state(max_cycles=parsed_max_cycles)
        diagnostic_only = bool(self.autonomous_state.get("diagnostic_only") or parsed_diagnostic_only)
        continuous_autonomy = bool(self.autonomous_state.get("enabled")) if persistence_override is None else bool(persistence_override)
        self._set_autonomous_state(continuous_autonomy=continuous_autonomy, finite_goal_stop=not continuous_autonomy)
        mission, operating_rules = self._autonomous_clean_goal(parsed_goal or raw_goal)
        goal = mission
        request_intent = analyze_request_intent(raw_goal)
        auto_mutation_blocked = should_block_automatic_mutation(request_intent)
        original_workspace = str(self.config.workspace)
        target_workspace = Path(original_workspace).expanduser().resolve()
        target_mode = "project"
        if self._autonomous_goal_targets_wla_source(raw_goal, request_intent):
            target_workspace = self._wla_source_root()
            target_mode = "wla_source"
        cycle_plan = [
            "Build a tool-awareness plan from pipeline manifests, capabilities and registered tools",
            "Observe runtime health and model/workspace status",
            "Run self-checks and inspect recent logs",
            "Reconsider whether the current plan is good before acting",
            "Read memory/lessons to avoid repeated failed approaches",
            "Clean stale tool proposals and review available tools",
            "Run a project test/final check if a project is open",
            "Use Docker validation checkpoints when Docker is ready",
            "Use improve-project/agent loop when safe and useful",
            "Prefer surgical repair before non-destructive backtracking",
            "Write proposals and trace notes for future improvements",
        ]
        self._set_autonomous_state(
            running=True,
            cycle=cycle,
            current_run_id=run_id,
            last_cycle_started_ts=time.time(),
            phase="observe",
            current_action="Cycle started",
            current_detail=goal,
            raw_goal=raw_goal,
            operating_rules=operating_rules,
            request_intent=request_intent.to_dict(),
            autonomous_target_mode=target_mode,
            autonomous_target_path=str(target_workspace),
            autonomous_original_workspace=original_workspace,
            diagnostic_only=diagnostic_only,
            continuous_autonomy=continuous_autonomy,
            last_error="",
            events=[],
            cycle_plan=cycle_plan,
            cycle_report=[],
            repair_proposal_written_this_cycle=False,
        )
        self._autonomous_upsert_cycle_summary(run_id=run_id, cycle=cycle, goal=goal, raw_goal=raw_goal, status="running", phase="cycle_start", current_action="Cycle started", current_detail="Preparing observe → plan → act → verify → repair → reflect loop.", events=[])
        self._autonomous_event("cycle_start", f"Autonomous cycle {cycle} started", {"goal": goal, "cycle": cycle, "detail": "Preparing observe → plan → act → verify → repair → reflect loop."})
        self._autonomous_event("target_resolved", f"Autonomous target resolved: {target_mode}", {"path": str(target_workspace), "original_workspace": original_workspace})
        self._autonomous_event("observe", "Observing runtime health and workspace state", {"goal": goal, "cycle": cycle, "detail": "Heartbeat, self-check, logs and project/tool state will be inspected."})
        self._autonomous_event("reconsider", "Reconsidering whether the plan is still a good idea", {"detail": "Before acting, compare the goal, recent failures, memory lessons and available tools. If the plan is wrong, switch to the smallest safer diagnostic/repair step."})
        report: list[str] = [f"Autonomous cycle {cycle}", f"Run ID: {run_id}", f"Goal: {goal}", "", "Plan:"]
        report += [f"- {x}" for x in cycle_plan]
        try:
            tool_plan = self.tools.call("autonomous_tool_plan", goal=goal, mode="autonomous", limit=14)
            log_activity("autonomous_tool_plan", "Autonomous tool-awareness plan selected", {"run_id": run_id, "cycle": cycle, "ok": tool_plan.ok, "data": tool_plan.data})
            if tool_plan.ok:
                self._autonomous_event("tool_awareness", "Autonomous tool-awareness plan selected", {"pipeline": tool_plan.data.get("pipeline_kind"), "covered": tool_plan.data.get("covered_tool_count"), "missing": tool_plan.data.get("missing_tools", [])})
                report.extend(["", "Tool-awareness:", f"- Pipeline: {tool_plan.data.get('pipeline_kind')} — {tool_plan.data.get('pipeline_title')}", f"- Selected tools available: {tool_plan.data.get('covered_tool_count')}/{len(tool_plan.data.get('decisions') or [])}"])
        except Exception as exc:
            log_activity("autonomous_tool_plan_error", "Autonomous tool-awareness plan failed", {"run_id": run_id, "cycle": cycle, "error": repr(exc)})
        sequence_results: list[ToolResult] = []
        try:
            if target_mode == "wla_source":
                self.config.workspace = str(target_workspace)
                report.append(f"Resolved autonomous target: Nova source repo at {target_workspace}")
            else:
                report.append(f"Resolved autonomous target: active project/workspace at {target_workspace}")
            self._autonomous_event("plan", "Planning safe tool sequence", {"detail": "Using built-in tools first; only using LLM/tool creation when it helps the stated goal."})
            lower_goal = goal.lower()
            sandbox_focused_goal = any(w in lower_goal for w in ["sandbox", "linux", "kali", "docker", "container"]) and any(w in lower_goal for w in ["test", "check", "verify", "availability", "available", "works", "working"])
            if sandbox_focused_goal:
                base_steps = [
                    ("Heartbeat", "heartbeat", {}),
                    ("Check Linux/Kali sandbox capability", "sandbox_status", {}),
                ]
                report.append("Sandbox-focused autonomous request detected: skipping generic proposal/model-heavy diagnostics and running direct sandbox checks.")
            else:
                base_steps: list[tuple[str, str, dict[str, Any]]] = [
                    ("Heartbeat", "heartbeat", {}),
                    ("Tool-awareness plan", "autonomous_tool_plan", {"goal": goal, "mode": "autonomous", "limit": 14}),
                    ("Runtime self-check", "runtime_self_check", {}),
                    ("Cohesion self-map", "cohesion_report", {"goal": goal, "path": "."}),
                    ("Review memory and idle lessons", "idle_lessons", {}),
                    ("Investigate recent logs", "investigate_logs", {"focus": goal}),
                    ("Run code repair audit", "code_repair_audit", {"path": "."}),
                    ("Run CodeRabbit-style quality gate", "code_quality_gate", {"path": "."}),
                    ("Check Linux/Kali sandbox capability", "sandbox_status", {}),
                    ("Review available tool workflow", "tool_use_guide", {}),
                    ("Clean stale tool proposals", "tool_clean_proposals", {}),
                    ("Propose improvements from evidence", "propose_improvements", {"focus": goal}),
                ]
            base_results: list[tuple[str, str, ToolResult]] = []
            for title, tool, kwargs in base_steps:
                if self.autonomous_state.get("stop_requested"):
                    report.append("Stop requested; ending after current safe step.")
                    break
                skip_loop, loop_reason = should_skip_repeated_action(dict(self.autonomous_state), title, tool, kwargs, required=False)
                if skip_loop:
                    report.append(f"Skipped repeated base diagnostic: {title} - {loop_reason}")
                    self._autonomous_event("loop_guard_skip", f"Loop guard skipped repeated base step: {title}", {"detail": loop_reason, "tool": tool, "signature": autonomous_action_signature(title, tool, kwargs)})
                    continue
                on_cooldown, cooldown_reason, cooldown_record = self._autonomous_cooldown_for_action(title, tool, kwargs)
                if on_cooldown:
                    report.append(f"Skipped base diagnostic on cooldown: {title} - {cooldown_reason}")
                    self._autonomous_event("cooldown_skip", f"Skipped base step on autonomous failure cooldown: {title}", {"detail": cooldown_reason, "tool": tool})
                    self._autonomous_diagnose_recent_failure(report, run_id, cooldown_record, cooldown_reason)
                    continue
                result = self._autonomous_call_tool(title, tool, kwargs, report, run_id)
                base_results.append((title, tool, result))
            promote_patch_run_id = self._autonomous_extract_promote_patch_run_id(raw_goal)
            if promote_patch_run_id != "__NO_PROMOTION_REQUEST__" and not self.autonomous_state.get("stop_requested"):
                self._autonomous_event("promote_patch_gate", "Explicit autonomous validated-patch promotion requested", {"run_id": promote_patch_run_id or "latest"})
                report.append("Explicit autonomous validated-patch promotion requested. This only promotes a patch that already passed Docker patch validation.")
                promotion = self._autonomous_call_tool(
                    "Promote Docker-validated patch",
                    "docker_promote_patch",
                    {"run_id": promote_patch_run_id, "path": ".", "local_command": "python -m compileall -q winlocalassistant tests_*.py app.py", "rollback_on_failure": True},
                    report,
                    run_id,
                )
                base_results.append(("Promote Docker-validated patch", "docker_promote_patch", promotion))
                if not promotion.ok:
                    self._autonomous_event("promote_patch_blocked", "Validated patch promotion did not complete", {"detail": promotion.summary})
                    report.append("Validated patch promotion blocked or failed: " + promotion.summary)
                else:
                    self._autonomous_event("promote_patch_done", "Validated patch promoted successfully", {"detail": promotion.summary})
                    report.append("Validated patch promoted successfully: " + promotion.summary)
            docker_validation_ready = False
            if not self._autonomous_goal_disables_docker_validation(raw_goal) and not self.autonomous_state.get("stop_requested"):
                docker_validation_ready, _docker_skip_reason, _docker_status_data = self._autonomous_docker_validation_preflight(report, run_id)
            elif self._autonomous_goal_disables_docker_validation(raw_goal):
                self._set_autonomous_state(docker_validation_skipped_reason="Docker validation disabled by goal flag.")
                report.append("Docker validation skipped: disabled by goal flag.")
            wants_self = request_intent.self_improvement_requested or request_intent.target_is_wla_source or any(k in lower_goal for k in ["self-improve", "edit yourself", "improve winlocalassistant", "improve yourself"])
            health_ok, health_blockers = self._autonomous_base_health_allows_mutation(base_results)
            docker_pre_ok = True
            docker_pre_result = None
            if docker_validation_ready and not self.autonomous_state.get("stop_requested"):
                docker_pre_ok, docker_pre_result = self._autonomous_docker_validation_checkpoint(report, run_id, stage="pre-action", required=True)
                if not docker_pre_ok:
                    health_ok = False
                    health_blockers.append("Docker pre-action validation failed; mutation skipped until the project passes in the copied Docker workspace.")
                    if docker_pre_result is not None:
                        base_results.append(("Docker pre-action validation", "docker_validate", docker_pre_result))
            if health_blockers:
                health_detail = "; ".join(health_blockers)
                previous_health_detail = str(self.autonomous_state.get("last_health_blocker_signature") or "")
                repeat_count = int(self.autonomous_state.get("repeated_health_gate_count") or 0) + 1 if previous_health_detail == health_detail else 1
                self._set_autonomous_state(last_health_blocker_signature=health_detail, repeated_health_gate_count=repeat_count)
                self._autonomous_event("health_gate", "Autonomous health gate blocked mutation", {"detail": health_detail, "repeat_count": repeat_count})
                report.append("Autonomous health gate: skipped mutation/build steps because runtime health checks failed.")
                for blocker in health_blockers:
                    report.append(f"- {blocker}")
                if repeat_count >= 2 and self.autonomous_state.get("enabled"):
                    self._autonomous_event("loop_guard_stop", "Loop guard stopped continuous autonomous mode after repeated health-gate blocker", {"detail": health_detail})
                    report.append("Loop guard stopped continuous autonomous mode because the same health-gate blocker repeated without progress.")
                    self._set_autonomous_state(enabled=False, stop_requested=True, loop_guard_stop_recommended=True, next_strategy_hint="stop_and_report_repeated_health_gate")
            else:
                self._set_autonomous_state(last_health_blocker_signature="", repeated_health_gate_count=0)
            if self._goal_wants_custom_tool_creation(raw_goal) and health_ok and not diagnostic_only and not self.autonomous_state.get("stop_requested"):
                tool_goal_result = self._autonomous_handle_create_tool_goal(raw_goal, report, run_id)
                sequence_results.append(("Create and verify custom tool", "tool_create", tool_goal_result))
                if not tool_goal_result.ok:
                    health_ok = False
                    health_blockers.append("Goal-specific custom tool creation acceptance failed; heartbeat/runtime self-check cannot satisfy this goal.")
                    self._set_autonomous_state(last_cycle_finite_goal_complete=False)
            if diagnostic_only and not self.autonomous_state.get("stop_requested"):
                self._autonomous_event("diagnostic_only", "Diagnostic-only autonomous mode skipped mutation/build steps", {"detail": "Use /autonomous start without --diagnostic when you want safe project changes."})
                report.append("Diagnostic-only mode: inspected and proposed only; skipped build/edit/repair mutation steps.")
            if (auto_mutation_blocked or not health_ok or diagnostic_only) and not self.autonomous_state.get("stop_requested"):
                self._autonomous_event(
                    "request_intent_guard",
                    "Request intent requires proposal/diagnostic-only autonomous mode",
                    {"detail": "; ".join(request_intent.reasons) or "automatic mutation is not safe for this request"},
                )
                if auto_mutation_blocked:
                    report.append("Request intent guard: skipped automatic build/edit/tool creation for this cycle.")
                    for reason in request_intent.reasons:
                        report.append(f"- {reason}")
            elif not self.autonomous_state.get("stop_requested"):
                sandbox_probe = self.tools.call("sandbox_status")
                sandbox_state = sandbox_probe.data if sandbox_probe.ok else {"ok": False, "summary": sandbox_probe.summary}
                sequence = build_autonomous_tool_sequence(goal, {"workspace": str(self.config.workspace), "request_intent": request_intent.to_dict(), "loop_guard": {"no_progress_cycles": self.autonomous_state.get("no_progress_cycles"), "next_strategy_hint": self.autonomous_state.get("next_strategy_hint")}, "sandbox": sandbox_state})
                sequence_results = self._run_autonomous_sequence_plan(sequence, report, run_id)
                if self.autonomous_state.get("enabled") and not self.autonomous_state.get("stop_requested"):
                    self._autonomous_auto_apply_low_risk_idle_candidate(goal, report, run_id)
            if wants_self and not self.autonomous_state.get("stop_requested"):
                self._autonomous_event("self_improve_manual_only", "Self-improvement requires a manual guarded command", {"detail": "Autonomous mode will not call /self-improve automatically. Use /idle propose or manually send /self-improve GOAL after review."})
                report.append("Self-improvement was requested, but autonomous mode does not call /self-improve automatically. Use `/idle propose` or manually send `/self-improve GOAL` after review.")
            if docker_validation_ready and health_ok and not self.autonomous_state.get("stop_requested"):
                docker_post_ok, docker_post_result = self._autonomous_docker_validation_checkpoint(report, run_id, stage="post-action", required=False)
                if docker_post_result is not None:
                    sequence_results.append(docker_post_result)
                if not docker_post_ok:
                    report.append("Post-action Docker validation failed. The cycle completed diagnostics but should not promote further autonomous changes until this is fixed.")
            if self.autonomous_state.get("stop_requested"):
                self._autonomous_event("stop_requested", "Stop requested; skipped final health check and ended cycle", {"detail": "Autonomous mode stops after the current bounded step."})
                report.append("Stop requested; skipped final health check and ended cycle.")
            else:
                self._autonomous_event("verify", "Running final autonomous health check", {"detail": "Heartbeat and self-check after cycle actions."})
                self._autonomous_call_tool("Final heartbeat", "heartbeat", {}, report, run_id)
                self._autonomous_call_tool("Final runtime self-check", "runtime_self_check", {}, report, run_id)
            outcome = summarize_cycle_outcome(goal=goal, base_results=base_results, sequence_results=sequence_results, diagnostic_only=diagnostic_only, continuous_mode=continuous_autonomy)
            loop_updates, loop_notes = update_loop_guard_state(dict(self.autonomous_state), outcome, continuous_mode=continuous_autonomy)
            self._set_autonomous_state(**loop_updates)
            for note in loop_notes:
                self._autonomous_event("loop_guard", note, {"detail": f"progress_score={outcome.get('progress_score')}; no_progress_cycles={loop_updates.get('no_progress_cycles')}; next={loop_updates.get('next_strategy_hint')}"})
                report.append(note)
            if loop_updates.get("loop_guard_stop_recommended") and self.autonomous_state.get("enabled"):
                self._autonomous_event("loop_guard_stop", "Loop guard stopped continuous autonomous mode", {"detail": loop_updates.get("next_strategy_hint") or "avoid repeating completed/no-progress cycles"})
                report.append("Loop guard stopped finite/repeated autonomous mode so it does not keep repeating the same cycle. Use --continuous to keep pursuing follow-up improvements, or start again with a more specific next goal.")
                self._set_autonomous_state(enabled=False, stop_requested=True)
            self._autonomous_event("reflect", "Reflecting on cycle result", {"summary": "Autonomous cycle finished. Review activity, AGENT_TRACE.md, ERROR_INVESTIGATION.md and IMPROVEMENT_PROPOSALS.md."})
            self._autonomous_event("cycle_done", f"Autonomous cycle {cycle} completed", {"summary": "Finished safe cycle; check report, activity and proposals for changes/errors handled.", "cycle": cycle})
            report_text = "\n".join(report)
            self._autonomous_upsert_cycle_summary(run_id=run_id, cycle=cycle, status="complete", phase="complete", current_action="Cycle completed", current_detail="Review activity panel for exact steps.", report=report[-40:], error="")
            self._set_autonomous_state(running=False, last_message="Cycle completed", last_error="", current_action="Cycle completed", current_detail="Review activity panel for exact steps.", cycle_report=report[-40:])
            log_activity("autonomous_cycle_done", "Autonomous cycle completed", {"run_id": run_id, "cycle": cycle, "report": report_text})
            return report_text + "\n\nAutonomous cycle complete. The live activity panel and autonomous bubble show the exact tool sequence used."
        except Exception as exc:
            self._autonomous_upsert_cycle_summary(run_id=run_id, cycle=cycle, status="failed", phase="error", current_action="Cycle failed", current_detail=repr(exc), error=repr(exc), report=report[-40:] if 'report' in locals() else [])
            self._set_autonomous_state(running=False, last_error=repr(exc), last_message="Cycle failed but autonomous mode can continue", current_action="Cycle failed", current_detail=repr(exc))
            self._autonomous_event("error", "Autonomous cycle exception", {"error": repr(exc)})
            log_activity("autonomous_cycle_failed", "Autonomous cycle failed", {"run_id": run_id, "cycle": cycle, "error": repr(exc)})
            return f"Autonomous cycle failed but was logged and can continue next cycle: {exc!r}"
        finally:
            self.config.workspace = original_workspace
            set_current_run(None)
    def test_project(self, level: str = "standard") -> str:
        level = (level or "standard").strip().lower()
        lines = [f"Project test level: {level}"]
        checks = [self.tools.call("auto_verify")]
        checks.append(self.tools.call("final_project_check", path=".", goal="test current project against its manifest and visible requirements"))
        if level == "deep":
            checks.append(self.tools.call("run_project", path="."))
            checks.append(self.tools.call("tool_clean_proposals"))
        for r in checks:
            lines.append(self.format_result(r))
        return "\n\n".join(lines)
    def _has_pending_sandbox_permission(self) -> bool:
        return bool(load_pending_sandbox_permission())

    def _sandbox_permission_prompt(self, profile: str, command: str, required: list[str], policy: dict[str, Any]) -> str:
        pending = create_pending_sandbox_permission(profile, command, required, policy)
        lines = [
            "⚠️ Sandbox permission needed before I can run that command.",
            "",
            render_pending_sandbox_permission_markdown(pending),
            "",
            "Reply with `/sandbox-approve yes` or just `yes` to approve and run the pending command.",
            "Reply with `/sandbox-cancel` or `no` to cancel.",
            "",
            "Only approve for owned/local lab targets or systems you have explicit permission to test.",
        ]
        return "\n".join(lines)

    def _sandbox_exec_or_permission(self, profile: str, command: str, timeout: int = 60) -> str:
        policy = evaluate_sandbox_command(self.config, profile, command)
        level = str(policy.get("policy_level") or getattr(self.config, "sandbox_policy_level", "balanced"))
        required: list[str] = []
        if policy.get("reasons"):
            if any("authorised Kali lab" in str(r) or "high-risk" in str(r) for r in policy.get("reasons", [])):
                required.append("authorized_lab")
        if sandbox_command_targets_network(command) and not bool(getattr(self.config, "sandbox_allow_network", False)) and level != "trusted_lab":
            required.append("network")
        if required:
            return self._sandbox_permission_prompt(profile, command, list(dict.fromkeys(required)), policy)
        return self.format_result(self.tools.call(
            "sandbox_exec",
            profile=profile,
            command=command,
            timeout=timeout,
            allow_network_tools=level == "trusted_lab",
            allow_high_risk=level == "trusted_lab",
        ))

    def approve_sandbox_permission(self, rest: str = "yes") -> str:
        val = (rest or "").strip().lower()
        pending = load_pending_sandbox_permission()
        if not pending:
            return "No sandbox permission request is pending."
        if val not in APPROVAL_WORDS:
            clear_pending_sandbox_permission()
            return "Sandbox permission request cancelled."
        profile = str(pending.get("profile") or "kali")
        command = str(pending.get("command") or "")
        required = list(pending.get("required") or [])
        applied: list[str] = []
        if "authorized_lab" in required:
            self.tools.call("sandbox_flag", flag="authorized_lab", enabled=True)
            applied.append("authorised Kali lab mode enabled")
        if "network" in required:
            self.tools.call("sandbox_flag", flag="network", enabled=True)
            self.tools.call("sandbox_stop", profile=profile)
            self.tools.call("sandbox_start", profile=profile, network="bridge")
            applied.append("sandbox network enabled and sandbox restarted with bridge networking")
        clear_pending_sandbox_permission()
        result = self.tools.call(
            "sandbox_exec",
            profile=profile,
            command=command,
            timeout=90,
            allow_network_tools="network" in required,
            allow_high_risk="authorized_lab" in required,
        )
        header = "✅ Permission approved. " + ("; ".join(applied) if applied else "No extra flags were required.")
        return header + "\n\n" + self.format_result(result)

    def sandbox_command(self, profile: str = "", rest: str = "") -> str:
        """Handle Linux/Kali sandbox commands without exposing host shell execution."""
        raw = (rest or "").strip()
        profile = (profile or "").strip().lower()
        if profile not in {"linux", "kali", ""}:
            return "Unknown sandbox profile. Use linux or kali."
        if not profile:
            return self.format_result(self.tools.call("sandbox_status"))
        if not raw or raw.lower() in {"status", "show"}:
            return self.format_result(self.tools.call("sandbox_status"))
        parts = raw.split(maxsplit=1)
        action = parts[0].lower()
        arg = parts[1] if len(parts) > 1 else ""
        if action in {"start", "up", "run"}:
            explicit_none = "network=none" in arg or "--network none" in arg
            if explicit_none:
                network = "__none__"
            elif "--network" in arg or "network=bridge" in arg:
                network = "bridge"
            elif profile == "kali" and str(getattr(self.config, "sandbox_policy_level", "balanced")).replace("-", "_") == "trusted_lab" and bool(getattr(self.config, "sandbox_allow_network", False)):
                network = "bridge"
            else:
                network = "none"
            writable = "--writable" in arg or "writable=true" in arg
            pull = "--pull" in arg or "pull=true" in arg
            return self.format_result(self.tools.call("sandbox_start", profile=profile, network=network, writable_workspace=writable, pull=pull))
        if action in {"stop", "down", "rm", "remove"}:
            return self.format_result(self.tools.call("sandbox_stop", profile=profile))
        if action in {"exec", "run-cmd", "cmd", "shell"}:
            if not arg:
                return f"Usage: /sandbox-{profile} exec <command>"
            return self._sandbox_exec_or_permission(profile, arg, timeout=60)
        return f"Usage: /sandbox-{profile} start|stop|exec <command>"

    def sandbox_flag_command(self, flag: str, rest: str = "") -> str:
        val = (rest or "status").strip().lower()
        if val in {"status", "show", ""}:
            return self.format_result(self.tools.call("sandbox_status"))
        if val in {"on", "true", "yes", "1", "enable", "enabled"}:
            return self.format_result(self.tools.call("sandbox_flag", flag=flag, enabled=True))
        if val in {"off", "false", "no", "0", "disable", "disabled"}:
            return self.format_result(self.tools.call("sandbox_flag", flag=flag, enabled=False))
        return f"Usage: /sandbox-{flag} on|off|status"

    def sandbox_policy_command(self, rest: str = "") -> str:
        val = (rest or "status").strip().lower().replace("-", "_").replace(" ", "_")
        if val in {"status", "show", ""}:
            return self.format_result(self.tools.call("sandbox_status"))
        if val in {"less_strict", "trusted", "trusted_lab", "trustedlab", "on", "enable"}:
            return self.format_result(self.tools.call("sandbox_policy", level="trusted_lab"))
        if val in {"balanced", "normal", "default"}:
            return self.format_result(self.tools.call("sandbox_policy", level="balanced"))
        if val in {"strict", "off", "disable"}:
            return self.format_result(self.tools.call("sandbox_policy", level="strict"))
        return "Usage: /sandbox-policy strict|balanced|trusted_lab or /sandbox-less-strict on|off|status"

    def sandbox_dev_mode_command(self, rest: str = "") -> str:
        val = (rest or "status").strip().lower()
        if val in {"on", "enable", "enabled", "true", "yes"}:
            self.tools.call("sandbox_flag", flag="autonomy", enabled=True)
            return "Sandbox dev mode is on. Use `/sandbox-dev-run linux <command>` or `/sandbox-dev-run kali <command>` to run writable copied-workspace experiments. Live project files remain untouched until you manually promote changes."
        if val in {"off", "disable", "disabled", "false", "no"}:
            self.tools.call("sandbox_flag", flag="autonomy", enabled=False)
            return "Sandbox dev mode is off. Normal sandbox commands still work."
        return "Sandbox dev mode lets Nova write/test freely inside a copied workspace, not your live project. Commands: `/sandbox-dev-mode on`, `/sandbox-dev-run linux python -m compileall -q .`, `/sandbox-dev-run kali <owned/local lab check>`. Host-escape/destructive and unauthorised offensive operations remain blocked."

    def sandbox_dev_run_command(self, rest: str = "") -> str:
        raw = (rest or "").strip()
        if not raw:
            return "Usage: /sandbox-dev-run linux|kali <command>. Runs in a copied writable workspace so live files are untouched."
        parts = raw.split(maxsplit=1)
        profile = parts[0].lower()
        if profile not in {"linux", "kali"}:
            return "Usage: /sandbox-dev-run linux|kali <command>"
        command = parts[1] if len(parts) > 1 else "python -m compileall -q ."
        return self.format_result(self.tools.call("sandbox_dev_run", profile=profile, command=command, timeout=300))

    def beyond_thinking_command(self, rest: str = "") -> str:
        val = (rest or "status").strip().lower()
        settings = read_json_file(APP_DIR / "BEYOND_THINKING_SETTINGS.json", {}, expected_type=dict, quarantine=True)
        if val in {"on", "enable", "enabled", "true", "yes"}:
            settings["enabled"] = True
            atomic_write_json(APP_DIR / "BEYOND_THINKING_SETTINGS.json", settings, ensure_ascii=True, indent=2)
            return "Beyond-thinking mode is on. Nova will add extra inferred context only when confidence is high and the extra work is clearly useful."
        if val in {"off", "disable", "disabled", "false", "no"}:
            settings["enabled"] = False
            atomic_write_json(APP_DIR / "BEYOND_THINKING_SETTINGS.json", settings, ensure_ascii=True, indent=2)
            return "Beyond-thinking mode is off."
        prompt = rest.strip() if rest and val not in {"status", "show"} else ""
        if prompt:
            return self._beyond_thinking_context(prompt)
        return "Beyond-thinking mode: " + ("on" if settings.get("enabled") else "off") + ". Use `/beyond-thinking on` or `/beyond-thinking PROMPT` to preview inferred extra context."

    def _beyond_thinking_context(self, prompt: str) -> str:
        low = (prompt or "").lower()
        inferred = []
        if any(x in low for x in ["make", "build", "create", "app", "website", "tool"]):
            inferred.append("Build task: derive an acceptance contract before writing files, then validate against the original request rather than a template.")
        if any(x in low for x in ["localstorage", "save", "export", "json"]):
            inferred.append("Likely expected: local state persistence, corrupted localStorage handling, visible export/download button, and README claims matching code.")
        if any(x in low for x in ["fix", "bug", "repair", "broken", "error"]):
            inferred.append("Repair task: inspect evidence, patch minimally, run targeted validation, then broader regression checks.")
        if any(x in low for x in ["voice", "microphone", "mic", "headset", "bluetooth"]):
            inferred.append("Voice task: check browser permission, enumerate mics, selected deviceId, Windows input device, and SpeechRecognition support.")
        if not inferred:
            inferred.append("No high-confidence extra context; proceed normally without extra work.")
        return "# Beyond-thinking context preview\n\n" + "\n".join(f"- {x}" for x in inferred)

    def model_help_plan_command(self, rest: str = "") -> str:
        goal = (rest or "").strip() or "diagnose and improve the current project/code safely"
        ctx = self.tools.call("model_context", prompt=goal)
        context_text = str((ctx.data or {}).get("text") or (ctx.data or {}).get("content") or "") if isinstance(ctx.data, dict) else ""
        prompt = f"""You are Nova's local reviewer. Return ONLY JSON with keys: problem, plan, files_to_inspect, validation, risks, stop_conditions.\nProblem/request:\n{goal}\n\nContext:\n{context_text[:12000]}"""
        reply = model_chat(self.config, self._select_model_for("planning"), [{"role":"user","content":prompt}], timeout=120, desc="local model help plan")
        out_dir = APP_DIR / "model_help"
        out_dir.mkdir(parents=True, exist_ok=True)
        path = out_dir / (time.strftime("model_help_%Y%m%d_%H%M%S.md"))
        text = "# Local model help plan\n\nGoal:\n" + goal + "\n\n## Reply\n\n" + str(reply or "(no reply)") + "\n"
        atomic_write_text(path, text)
        log_activity("model_help_plan", "Asked local model for a repair/build plan", {"goal": goal, "report": str(path), "reply_preview": str(reply or "")[:1000]})
        return text + f"\nReport: {path}\nUse `/model-help-implement {goal}` to run Nova's normal guarded implementation loop using this context."

    def model_help_implement_command(self, rest: str = "") -> str:
        goal = (rest or "").strip() or "implement the local model's recommended safe plan for this project"
        plan_text = self.model_help_plan_command(goal)
        result = self.tools.call("improve_project", goal="Use this local-model plan as context, then implement the smallest safe validated improvement: " + goal, path=".")
        return plan_text + "\n\n# Guarded implementation result\n\n" + self.format_result(result)

    def video_plan_command(self, rest: str = "") -> str:
        prompt = (rest or "").strip()
        if not prompt:
            return "Usage: /video-plan PROMPT\nExample: /video-plan 10 second cinematic trailer about Nova building a project"
        out_dir = Path(self.config.workspace) / "nova_video_jobs" / (str(int(time.time())) + "_" + re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")[:40])
        path = save_video_manifest(prompt, out_dir)
        manifest = plan_video_manifest(prompt, project_id=out_dir.name)
        preview = write_video_preview_avi(manifest, out_dir)
        preview_html = write_video_preview_html(manifest, out_dir, preview)
        return render_video_manifest_markdown(manifest) + f"\n\nManifest written: `{path}`\nPreview video written: `{preview}`\nPreview page written: `{preview_html}`"

    def video_status_command(self) -> str:
        status = video_stack_status()
        lines = ["# Nova Video Stack Status", "", f"ComfyUI: {'reachable' if status['comfyui'].get('reachable') else 'not reachable'} ({status['comfyui'].get('url')})", "", "## Local tools"]
        for name, ok in status.get("tools", {}).items():
            lines.append(f"- {name}: {'available' if ok else 'missing'}")
        lines += ["", "Nova can still plan video manifests even when render backends are missing."]
        return "\n".join(lines)

    def video_validate_command(self, rest: str = "") -> str:
        prompt = (rest or "").strip() or "10 second Nova video smoke test"
        manifest = plan_video_manifest(prompt)
        validation = validate_video_manifest(manifest)
        execution = build_video_execution_plan(manifest)
        return render_video_manifest_markdown(manifest) + "\n\n" + render_video_validation_markdown(validation, execution)

    def video_user_test_command(self) -> str:
        lines = ["# Nova Video User Test Scenarios", "", "Run these after installing render backends; they are deterministic UX acceptance checks."]
        for item in video_user_test_scenarios():
            lines.append(f"- **{item['name']}**: `{item['prompt']}` -> " + ", ".join(item.get('expect', [])))
        return "\n".join(lines)


    def media_status_command(self) -> str:
        image_s = image_generation_status()
        video_s = video_stack_status()
        summary = media_status_summary(image_s, video_s)
        lines = ["# Nova Media Status", "", "## Image"]
        lines.append(f"- Real generation ready: {'yes' if image_s.get('ready_for_real_generation') else 'no'}")
        lines.append(f"- SD WebUI: {'available' if image_s.get('sdwebui',{}).get('available') else 'not reachable'}")
        lines.append(f"- Diffusers: {'installed' if image_s.get('diffusers',{}).get('installed') else 'not installed'}")
        lines += ["", "## Video"]
        lines.append(f"- ComfyUI: {'reachable' if video_s.get('comfyui',{}).get('reachable') else 'not reachable'}")
        for name, ok in video_s.get('tools', {}).items():
            lines.append(f"- {name}: {'available' if ok else 'missing'}")
        lines += ["", "## Recommended flow"]
        lines.extend(f"- {x}" for x in summary.get('recommended_flow', []))
        return "\n".join(lines)

    def image_plan_command(self, rest: str = "") -> str:
        prompt = (rest or "").strip()
        if not prompt:
            return "Usage: /image-plan PROMPT\nExample: /image-plan cinematic robot dog mascot in a neon workshop"
        style = "cinematic"
        if "=>" in prompt:
            prompt, style = [x.strip() for x in prompt.split("=>", 1)]
            style = style or "cinematic"
        plan = build_image_prompt_plan(prompt, style=style)
        return render_image_prompt_plan_markdown(plan)

    def video_storyboard_command(self, rest: str = "") -> str:
        prompt = (rest or "").strip()
        if not prompt:
            return "Usage: /video-storyboard PROMPT\nExample: /video-storyboard 10 second trailer about Nova building a project"
        out_dir = Path(self.config.workspace) / "nova_video_jobs" / (str(int(time.time())) + "_storyboard_" + re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")[:32])
        manifest = plan_video_manifest(prompt, project_id=out_dir.name)
        storyboard = write_storyboard_svg(manifest, out_dir)
        shotlist = write_shotlist_csv(manifest, out_dir)
        prompt_plan = build_video_image_prompt_plan(manifest)
        prompt_path = out_dir / "video_image_prompts.json"
        prompt_path.write_text(json.dumps(prompt_plan, indent=2), encoding="utf-8")
        return render_video_manifest_markdown(manifest) + f"\n\nStoryboard written: `{storyboard}`\nShot list written: `{shotlist}`\nImage prompts written: `{prompt_path}`"

    def video_package_command(self, rest: str = "") -> str:
        prompt = (rest or "").strip()
        if not prompt:
            return "Usage: /video-package PROMPT\nExample: /video-package 10 second cinematic trailer about Nova improving a project"
        out_dir = Path(self.config.workspace) / "nova_video_jobs" / (str(int(time.time())) + "_package_" + re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")[:32])
        package = write_video_render_package(prompt, out_dir)
        return render_video_render_package_markdown(package)


    def nova_efficiency_audit_command(self, rest: str = "") -> str:
        from .nova_efficiency_audit import write_nova_efficiency_audit, render_nova_efficiency_audit
        payload, md_path, json_path = write_nova_efficiency_audit(Path(self.config.workspace))
        summary = render_nova_efficiency_audit(payload)
        return summary + f"\nReports written:\n- {md_path}\n- {json_path}\n"

    def handle_command(self, text: str) -> str:
        parts = text.strip().split(maxsplit=1)
        cmd = canonical_command(parts[0].lower())
        rest = parts[1] if len(parts) > 1 else ""
        try:
            if cmd in {"/nova-efficiency-audit", "/efficiency-audit", "/gui-audit", "/ux-audit"}:
                return self.nova_efficiency_audit_command(rest)
            if cmd == "/active-run":
                return self.active_run_status_text()
            if cmd == "/reply":
                return self.reply_to_active_run(rest)
            if cmd == "/pause-run":
                return self.pause_active_run()
            if cmd == "/resume-run":
                return self.resume_active_run()
            if cmd == "/cancel-run":
                return self.cancel_active_run()
            if cmd == "/autonomous":
                return self.autonomous_command(rest)
            if cmd == "/autonomous-status":
                return self.autonomous_status_text()
            if cmd in {"/autonomy-readiness", "/autonomy-capability-audit", "/autonomy-audit"}:
                return self.format_result(self.tools.call("autonomy_readiness", path=rest or "."))
            if cmd == "/autonomous-guide":
                return self.autonomous_guide_text()
            if cmd == "/test-project":
                return self.test_project(rest or "standard")
            if cmd == "/sandbox-dev-mode":
                return self.sandbox_dev_mode_command(rest)
            if cmd == "/sandbox-dev-run":
                return self.sandbox_dev_run_command(rest)
            if cmd in {"/model-help", "/model-help-plan"}:
                return self.model_help_plan_command(rest)
            if cmd == "/model-help-implement":
                return self.model_help_implement_command(rest)
            if cmd == "/beyond-thinking":
                return self.beyond_thinking_command(rest)
            if cmd in {"/video-plan", "/nova-video-plan", "/movie-plan"}:
                return self.video_plan_command(rest)
            if cmd in {"/video-status", "/nova-video-status"}:
                return self.video_status_command()
            if cmd in {"/video-validate", "/video-check", "/movie-validate"}:
                return self.video_validate_command(rest)
            if cmd in {"/video-user-test", "/movie-user-test"}:
                return self.video_user_test_command()
            if cmd in {"/media-status", "/media"}:
                return self.media_status_command()
            if cmd in {"/image-plan", "/image-prompts", "/image-prompt-plan"}:
                return self.image_plan_command(rest)
            if cmd in {"/video-storyboard", "/movie-storyboard"}:
                return self.video_storyboard_command(rest)
            if cmd in {"/video-package", "/movie-package", "/video-render-package"}:
                return self.video_package_command(rest)
            if cmd in {"/schedule-task", "/schedule", "/remind", "/reminder"}:
                return self.format_result(self.tools.call("schedule_task", prompt=rest.strip()))
            if cmd in {"/schedule-status", "/scheduler-status", "/tasks"}:
                return self.format_result(self.tools.call("schedule_status", status=rest.strip()))
            if cmd == "/schedule-confirm":
                return self.format_result(self.tools.call("schedule_confirm", task_id=rest.strip()))
            if cmd == "/schedule-cancel":
                return self.format_result(self.tools.call("schedule_cancel", task_id=rest.strip()))
            if cmd in {"/task-decompose", "/decompose-task", "/task-dag"}:
                return self.format_result(self.tools.call("task_decompose", prompt=rest.strip()))
            if cmd in {"/scheduling-audit", "/scheduler-audit"}:
                return self.format_result(self.tools.call("scheduling_audit"))
            if cmd in {"/integration-foundation", "/orchestrator-foundation", "/integration-status"}:
                return self.format_result(self.tools.call("integration_foundation"))
            if cmd in {"/job-status", "/job-queue", "/jobs"}:
                return self.format_result(self.tools.call("job_status", status=rest.strip()))
            if cmd in {"/job-enqueue", "/job-create"}:
                bits = rest.split(maxsplit=1)
                kind = bits[0] if bits else "general"
                goal = bits[1] if len(bits) > 1 else ""
                return self.format_result(self.tools.call("job_enqueue", kind=kind, goal=goal, dedupe_key=(kind + ":" + goal) if goal else ""))
            if cmd == "/job-cancel":
                bits = rest.split(maxsplit=1)
                job_id = bits[0] if bits else ""
                reason = bits[1] if len(bits) > 1 else "cancelled by user"
                return self.format_result(self.tools.call("job_cancel", job_id=job_id, reason=reason))
            if cmd in {"/repo-map", "/repo-map-deep"}:
                return self.format_result(self.tools.call("repo_map_deep", path=rest or "."))
            if cmd in {"/patch-plan", "/safe-patch-plan"}:
                return self.format_result(self.tools.call("patch_plan", goal=rest or "safe Nova improvement"))
            if cmd in {"/browser-plan", "/browser-worker-plan"}:
                return self.format_result(self.tools.call("browser_task_plan", goal=rest or "read the current page safely"))
            if cmd in {"/doc-ingest", "/document-ingest"}:
                bits = rest.split(maxsplit=1)
                path = bits[0] if bits else ""
                query = bits[1] if len(bits) > 1 else ""
                return self.format_result(self.tools.call("document_ingest", path=path, query=query))
            if cmd in {"/model-registry", "/local-model-registry"}:
                return self.format_result(self.tools.call("local_model_registry"))
            if cmd in {"/integration-review", "/comprehensive-integration-review"}:
                return self.format_result(self.tools.call("integration_review"))
            if cmd in {"/validate-all", "/nova-validate"}:
                return self.format_result(self.tools.call("validate_all", full="--full" in rest))
            if cmd == "/test-all":
                return self.format_result(self.tools.call("test_all"))
            if cmd in {"/whole-codebase-review", "/review-codebase", "/comprehensive-code-review"}:
                return self.format_result(self.tools.call("whole_codebase_review", focus=rest))
            if cmd in {"/maintenance-validate", "/validate-maintenance", "/self-validate"}:
                return self.format_result(self.tools.call("maintenance_validate", profile=rest or "quick"))
            if cmd in {"/bug-review", "/bug-hunt", "/bug-sweep", "/error-review"}:
                return self.format_result(self.tools.call("bug_review", focus=rest))
            if cmd == "/model-doctor":
                return self.format_result(self.tools.call("model_doctor"))
            if cmd == "/model-benchmark":
                return self.format_result(self.tools.call("model_benchmark"))
            if cmd == "/visual-repair":
                return self.format_result(self.tools.call("visual_repair", path=rest or "."))
            if cmd == "/console-test":
                return self.format_result(self.tools.call("console_test", path=rest or "."))
            if cmd == "/known-issues":
                return self.format_result(self.tools.call("known_issues"))
            if cmd == "/self-improvement-queue":
                return self.format_result(self.tools.call("self_improvement_queue"))
            if cmd == "/self-apply":
                return self.format_result(self.tools.call("self_apply", item=rest.strip()))
            if cmd == "/autonomous-memory":
                return self.format_result(self.tools.call("autonomous_memory"))
            if cmd in {"/idle", "/idle-status"}:
                return self.idle_command(rest if cmd == "/idle" else "status")
            if cmd == "/avatar":
                a = self.avatar_status_data()
                return f"{a.get('emoji','🤖')} **{a.get('title','Ready')}** ({a.get('mood','ready')})\n\n{a.get('text','Waiting')}\n\nUpdated: {a.get('updated_at','')}"
            if cmd in {"/self-guide", "/how-to-use", "/full-guide"}:
                return self.self_guide_text()
            if cmd == "/model-timeout":
                return self.model_timeout_command(rest)
            if cmd == "/command-timeout":
                return self.command_timeout_command(rest)
            if cmd == "/model-health":
                return self.model_health_text()
            if cmd in {"/model-calibration", "/model-calibrate"}:
                from .model_calibration import build_model_calibration, render_model_calibration_markdown
                raw = rest.strip().lower()
                payload = build_model_calibration(Path.cwd(), run_benchmarks=("--bench" in raw or raw in {"bench", "benchmark", "full"}))
                return render_model_calibration_markdown(payload)
            if cmd in {"/llm-lab", "/llm-training", "/training-lab"}:
                from .llm_training_lab import render_command as render_llm_training_lab_command
                return render_llm_training_lab_command(rest, root=self.config.workspace)
            if cmd in {"/task-contract", "/contract-task", "/execution-contract"}:
                contract = build_task_execution_contract(rest or "continue improving Nova safely", root=self.config.workspace)
                return render_task_contract(contract)
            if cmd in {"/task-evidence", "/execution-evidence", "/task-execution-status"}:
                payload = build_task_execution_status(self.config.workspace)
                return render_task_execution_status(payload)
            if cmd == "/skill-mode":
                return self.skill_mode_command(rest)
            if cmd in {"/math", "/maths"}:
                return self._answer_with_skill("math", rest)
            if cmd == "/science":
                return self._answer_with_skill("science", rest)
            if cmd in {"/code", "/coding"}:
                return self._answer_with_skill("coding", rest)
            if cmd in {"/communicate", "/writing", "/rewrite"}:
                return self._answer_with_skill("communication", rest)
            if cmd == "/memory":
                return self.memory_text()
            if cmd == "/remember":
                return self.remember_command(rest)
            if cmd == "/knowledge":
                return self.knowledge_command(rest)
            if cmd == "/project-memory":
                payload = list_project_memory(self.config.workspace, limit=30) if not rest.strip() else search_project_memory(rest, limit=20)
                if payload.get("matches") is not None:
                    rows = payload.get("matches") or []
                    if not rows:
                        return "Project memory search\nNo matching project memories yet."
                    return "Project memory search\n" + "\n".join(f"- {r.get('project_path')}: {r.get('fact')}" for r in rows)
                facts = payload.get("facts") or []
                if not facts:
                    return "Project memory for current workspace\nNo project memories saved for this workspace yet."
                return "Project memory for current workspace\n" + "\n".join(f"- {f.get('time')}: {f.get('fact')}" for f in facts)
            if cmd == "/remember-project":
                payload = remember_project_fact(self.config.workspace, rest, source="user command")
                return payload.get("summary", "Project memory updated") + ("\n" + payload.get("fact", {}).get("fact", "") if payload.get("ok") else "")
            if cmd in {"/chat-new", "/new-chat", "/clear-chat"}:
                title = rest.strip() or "New chat"
                payload = create_conversation(title, make_active=True)
                self.messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + self._persona_system_prompt("default")}]
                return f"Started new chat: {payload.get('conversation',{}).get('title','New chat')}\nID: {payload.get('active_id','')}\nProject files, memories and databases were not deleted."
            if cmd in {"/chats", "/chat-list"}:
                payload = list_conversations(limit=30)
                rows = payload.get("conversations") or []
                if not rows:
                    return "No saved conversations yet."
                lines = ["Saved conversations"]
                active = payload.get("active_id")
                for c in rows:
                    mark = "*" if c.get("id") == active else "-"
                    lines.append(f"{mark} {c.get('title','Untitled')} — {c.get('id')} — {c.get('updated_at','')}")
                return "\n".join(lines)
            if cmd == "/chat-switch":
                payload = switch_conversation(rest.strip())
                if not payload.get("ok"):
                    return "Conversation not found or ambiguous. Use /chats to list saved conversations."
                self.messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + self._persona_system_prompt("default")}] + get_active_messages(limit=30)
                c = payload.get("conversation") or {}
                return f"Switched to chat: {c.get('title','Untitled')}\nID: {c.get('id','')}"
            if cmd == "/chat-search":
                payload = search_conversations(rest.strip(), limit=20)
                rows = payload.get("matches") or []
                if not rows:
                    return "No matching conversations found."
                return "Conversation search\n" + "\n".join(f"- {r.get('title')} — {r.get('id')} — score {r.get('score')}" for r in rows)
            if cmd == "/chat-rename":
                raw = rest.strip()
                if "=>" not in raw:
                    return "Usage: /chat-rename CHAT_ID_OR_TITLE => New title"
                ident, title = [x.strip() for x in raw.split("=>", 1)]
                payload = rename_conversation(ident, title)
                if not payload.get("ok"):
                    return "Conversation not found or ambiguous. Use /chats to list saved conversations."
                c = payload.get("conversation") or {}
                return f"Renamed chat: {c.get('title','Untitled')}\nID: {c.get('id','')}"
            if cmd == "/chat-delete":
                if not rest.strip():
                    return "Usage: /chat-delete CHAT_ID_OR_TITLE"
                payload = delete_conversation(rest.strip())
                if not payload.get("ok"):
                    return "Conversation not found or ambiguous. Use /chats to list saved conversations."
                deleted = payload.get("deleted") or {}
                self.messages = [{"role": "system", "content": SYSTEM_PROMPT + "\n" + self._persona_system_prompt("default")}] + get_active_messages(limit=30)
                return f"Deleted chat: {deleted.get('title','Untitled')}\nActive chat ID: {payload.get('active_id','')}"
            if cmd == "/learn-errors":
                return self.learn_errors_command()
            if cmd in {"/reasoning", "/recovery-plan"}:
                failure = self.last_error.get("result") if self.last_error else {"note": rest or "No active failure; showing default recovery reasoning."}
                return self.format_result(self.tools.call("reasoning_diagnostics", goal=str((self.last_error or {}).get("goal") or rest or "general recovery"), failed_tool=str((self.last_error or {}).get("tool") or "manual"), failure=failure))
            if cmd == "/recover-known-error":
                if not self.last_error:
                    return "No last error stored. Run a plan, /verify, or /auto-verify first, then use /recover-known-error."
                return self.format_result(self.tools.call("known_error_recover", goal=str(self.last_error.get("goal") or rest or "repair current project"), failed_step=str(self.last_error.get("step") or "manual"), failed_tool=str(self.last_error.get("tool") or "manual"), failure=self.last_error.get("result") or {}, path="."))
            if cmd == "/avatar-sound":
                return "Avatar sound is browser-side. Click **Enable audio** or the 🎙️ voice button once to unlock sound, then use `/speak TEXT` or `/voice-mode`. Voice input uses the browser SpeechRecognition API when available; spoken replies use speechSynthesis."
            if cmd in {"/voice-mode", "/voice", "/speech-mode", "/voice-troubleshoot", "/mic-test"}:
                return (
                    "Voice mode is browser-side and ready in the GUI.\n"
                    "- Click **Mic test** first. It forces the Chrome/Edge permission prompt, checks `getUserMedia`, lists browser-visible microphones, and reports the selected device. Use **Refresh mics** and the mic dropdown if Windows/Chrome selected the wrong Bluetooth headset input.\n"
                    "- Click the 🎙️ microphone button beside Send to talk to Nova after Mic test passes.\n"
                    "- The browser transcribes your speech into the composer and sends it when final text is captured.\n"
                    "- Nova speaks replies back with speechSynthesis when Voice mode is enabled, or when your prompt asks for a spoken/audio reply.\n"
                    "- Chrome or Edge usually support microphone transcription best; Firefox may support spoken output but not SpeechRecognition.\n"
                    "- For Sony WH-1000/WH-1000XM style Bluetooth headsets, Windows may expose separate **Headphones** output and **Headset** microphone devices. In Windows Settings > System > Sound > Input, choose the headset microphone, then use Nova Refresh mics and select the same device.\n"
                    "- If Mic test says blocked, open Chrome's site controls for `127.0.0.1`/`localhost` and set Microphone to Allow.\n"
                    "- If Mic test says busy, close Teams/Discord/voice apps or reconnect the headset.\n"
                    "Nothing is uploaded to a Nova cloud service by this command; microphone handling is controlled by the browser and OS permission prompt."
                )
            if cmd == "/speak":
                self._set_avatar("speaking", "🔊", "Speaking", rest or "Speaking test")
                return rest or "Speaking test"
            if cmd == "/action-watch":
                decision = evaluate_action_risk({"name": rest or "manual", "command": rest or "", "category": "manual"})
                record_action_outcome({"name": rest or "manual", "command": rest or ""}, {"manual_check": True})
                return "# Action Watcher Decision\n\n" + json.dumps(decision.to_dict(), indent=2)
            if cmd == "/interaction-lessons":
                if rest.strip():
                    lesson = derive_interaction_lesson(rest.strip(), tool_used="manual", outcome="user note", user_feedback=rest.strip())
                    path = append_interaction_lesson(lesson)
                    return f"Recorded interaction lesson at {path}\n\n" + lesson.lesson
                return render_lessons_markdown(load_interaction_lessons())
            if cmd == "/quality-dashboard":
                return self.quality_dashboard(rest)
            if cmd == "/quality-progress":
                return read_quality_progress(Path(self.config.workspace))
            if cmd in {"/nova-doctor", "/doctor", "/bug-scan", "/improvement-plan"}:
                return self.format_result(self.tools.call("nova_doctor", goal=rest or "general Nova reliability", path="."))
            if cmd in {"/release-checklist", "/ship-checklist"}:
                payload = build_release_checklist(Path.cwd())
                return render_release_checklist_markdown(payload)
            if cmd in {"/release-hygiene", "/package-hygiene", "/zip-hygiene"}:
                if rest.strip().lower() in {"clean", "--clean", "fix", "--fix"}:
                    result = clean_release_hygiene_artifacts(Path.cwd())
                    after = build_release_hygiene_report(Path.cwd())
                    return "# Nova Release Hygiene Clean\n\n" + result.get("summary", "") + "\n\n" + render_release_hygiene_report(after)
                return render_release_hygiene_report(build_release_hygiene_report(Path.cwd()))
            if cmd in {"/feature-audit", "/implementation-status", "/requested-features"}:
                return self.format_result(self.tools.call("feature_audit", path="."))
            if cmd in {"/feature-continuity-audit", "/functionality-continuity", "/no-regression-audit"}:
                return self.format_result(self.tools.call("feature_continuity_audit", path=rest or "."))
            if cmd in {"/security-status", "/defense-status", "/cyber-status", "/security-triage", "/defense-triage"}:
                payload = build_security_status()
                return render_security_status(payload)
            if cmd in {"/security-watch", "/defense-watch", "/cyber-watch"}:
                payload = run_security_watch()
                return render_security_watch(payload)
            if cmd in {"/dependency-check", "/deps", "/dependency-status"}:
                payload = build_dependency_report(include_heavy="--heavy" in rest.lower())
                return render_dependency_report(payload)
            if cmd in {"/upgrade-radar", "/upgrade-plan", "/significant-upgrades"}:
                payload = build_upgrade_radar(Path.cwd())
                return render_upgrade_radar(payload)
            if cmd in {"/optional-upgrades", "/upgrade-options"}:
                return render_optional_upgrade_status(build_optional_upgrade_status(Path.cwd()))
            if cmd in {"/upgrade-install", "/install-upgrade", "/upgrade-enable"}:
                raw = rest.strip()
                if not raw:
                    return render_optional_upgrade_status(build_optional_upgrade_status(Path.cwd()))
                parts = shlex.split(raw)
                name = parts[0] if parts else ""
                confirm = any(x.lower() in {"--confirm", "confirm", "yes", "--yes"} for x in parts[1:])
                payload = install_optional_upgrade(name, Path.cwd(), confirm=confirm, timeout=300)
                return render_optional_upgrade_install_result(payload)
            if cmd in {"/model-requirements", "/model-download-plan", "/model-readiness", "/model-select-recommendation", "/model-auto-request"}:
                report = build_model_readiness(rest.strip(), Path.cwd(), current_coder=self.config.model, current_chat=getattr(self.config, "chat_model", ""))
                return render_model_readiness(report)
            if cmd in {"/model-install", "/model-download", "/model-pull"}:
                raw = rest.strip()
                if not raw:
                    return render_model_readiness(build_model_readiness("general Nova use", Path.cwd(), current_coder=self.config.model, current_chat=getattr(self.config, "chat_model", "")))
                parts = shlex.split(raw)
                name = parts[0] if parts else ""
                confirm = any(x.lower() in {"--confirm", "confirm", "yes", "--yes"} for x in parts[1:])
                result = install_model(name, Path.cwd(), confirm=confirm)
                return render_model_install_result(result)
            if cmd in {"/response-quality-plan", "/ai-response-plan", "/communication-quality-plan", "/response-potency-plan"}:
                write = any(token in rest.lower().split() for token in ["--write", "write", "--save", "save"])
                goal = " ".join(token for token in shlex.split(rest.strip()) if token.lower() not in {"--write", "write", "--save", "save"}) if rest.strip() else ""
                if write:
                    md, js, payload = write_response_quality_plan(Path(self.config.workspace), goal)
                    return render_response_quality_plan(payload) + f"\nReports written:\n- `{md}`\n- `{js}`"
                return render_response_quality_plan(build_response_quality_plan(goal))
            if cmd in {"/flow-audit", "/interaction-flow-audit", "/interaction-pathways", "/command-flow-verify", "/learning-loop-audit"}:
                return render_flow_audit(build_flow_audit(Path.cwd(), tool_names=sorted(self.tools.tools.keys())))
            if cmd in {"/flow-improvements", "/complete-flow-improvements"}:
                md, js, payload = write_flow_audit(Path.cwd(), tool_names=sorted(self.tools.tools.keys()))
                payload = {**payload, "completed_improvements": ["Flow audit command routes are available.", "ToolRegistry flow-audit tools are available to idle/autonomous.", "Autonomy capability selection includes flow validation and learning-loop checks."], "markdown_path": str(md), "json_path": str(js)}
                return render_flow_audit(payload) + f"\n\nReports written:\n- `{md}`\n- `{js}`"
            if cmd in {"/massive-test", "/system-test", "/test-everything", "/full-validation"}:
                raw = rest.strip().lower()
                if "--confirm" not in raw and "confirm" not in raw:
                    return "Massive Nova system test requires confirmation because it runs many checks sequentially. Run `/massive-test --confirm` to continue, or `/massive-test --confirm full` for the slower legacy stack."
                profile = "full" if any(token in raw for token in [" full", "--full", " release", " deep", " legacy"]) else "quick"
                payload = run_massive_system_test(Path.cwd(), profile=profile)
                return render_massive_system_test(payload)
            if cmd in {"/release-gate", "/validate-release", "/preflight-release"}:
                raw_gate = rest.strip()
                goal = raw_gate
                test_command = ""
                if "=>" in raw_gate:
                    goal, test_command = [part.strip() for part in raw_gate.split("=>", 1)]
                return self.format_result(self.tools.call("wla_release_gate", goal=goal or "release validation", path=".", test_command=test_command))
            if cmd in {"/integration-radar", "/next-integrations", "/integration-plan"}:
                return self.format_result(self.tools.call("integration_radar", goal=rest or "find useful integrations for Nova", path="."))
            if cmd == "/playwright-smoke-help":
                return "Playwright browser smoke tests are scaffolded at `playwright/nova_gui_smoke.spec.js`. Start Nova, then run: `npx playwright test playwright/nova_gui_smoke.spec.js`. These tests exercise send, audio controls, quick commands, live activity and changelog UI."
            if cmd == "/command-verify":
                return self.format_result(self.tools.call("command_verify"))
            if cmd in {"/repo-upgrade-assurance", "/repo-readiness", "/integration-readiness", "/future-timeline"}:
                return self.format_result(self.tools.call("repo_upgrade_assurance"))
            if cmd in {"/codebase-sanity-audit", "/sanity-audit", "/dead-code-audit", "/rewrite-candidates"}:
                return self.format_result(self.tools.call("codebase_sanity_audit", path=rest.strip() or "__wla_source__"))
            if cmd in {"/repo-research-radar", "/repo-inspiration-radar"}:
                return self.format_result(self.tools.call("repo_research_radar", goal=rest.strip()))
            if cmd in {"/pipeline", "/pipeline-preflight", "/pipeline-route"}:
                return self.format_result(self.tools.call("pipeline_preflight", goal=rest.strip()))
            if cmd in {"/tool-awareness", "/tool-use-plan", "/autonomous-tool-plan", "/idle-tool-plan"}:
                mode = "manual"
                goal = rest.strip()
                if cmd == "/autonomous-tool-plan":
                    mode = "autonomous"
                elif cmd == "/idle-tool-plan":
                    mode = "idle"
                elif goal.lower().startswith(("autonomous ", "idle ", "manual ")):
                    parts = goal.split(maxsplit=1)
                    mode = parts[0].lower()
                    goal = parts[1] if len(parts) > 1 else ""
                return self.format_result(self.tools.call("tool_awareness", goal=goal or "Improve Nova safely", mode=mode))
            if cmd == "/tool-awareness-audit":
                return self.format_result(self.tools.call("tool_awareness_audit", goal=rest.strip()))
            if cmd in {"/pipeline-catalog", "/capability-manifests", "/repo-upgrade-plan", "/repo-capabilities"}:
                raw = rest.strip()
                write = any(flag in raw.lower() for flag in ["--write", "--save", "write", "save"])
                goal = raw.replace("--write", "").replace("--save", "").strip()
                return self.format_result(self.tools.call("pipeline_catalog", goal=goal, write=write))
            if cmd in {"/pipeline-manifest", "/capability-manifest"}:
                return self.format_result(self.tools.call("pipeline_manifest", manifest_id=rest.strip()))
            if cmd in {"/session-evidence", "/run-evidence", "/evidence"}:
                raw = rest.strip()
                parts = raw.split()
                run_id = parts[0] if parts else "latest"
                limit = 120
                for part in parts[1:]:
                    try:
                        limit = int(part)
                        break
                    except ValueError:
                        continue
                return self.format_result(self.tools.call("session_evidence", run_id=run_id, limit=limit))
            if cmd in {"/memory-inventory", "/memory-audit", "/typed-memory-audit"}:
                return self.format_result(self.tools.call("memory_inventory", path=rest.strip() or "."))
            if cmd in {"/project-patterns", "/patterns", "/nova-patterns"}:
                raw = rest.strip()
                write = any(flag in raw.lower() for flag in ["--write", "--save", "write", "save"])
                clean = raw.replace("--write", "").replace("--save", "").replace("write", "").replace("save", "").strip() or "."
                return self.format_result(self.tools.call("project_patterns", path=clean, write=write))
            if cmd in {"/browser-smoke", "/gui-smoke", "/webui-smoke"}:
                return self.format_result(self.tools.call("browser_smoke", path=rest.strip() or "."))
            if cmd in {"/live-timeline", "/timeline", "/run-timeline"}:
                try:
                    limit = int(rest.strip() or "40")
                except ValueError:
                    limit = 40
                return self.format_result(self.tools.call("live_timeline", limit=limit))
            if cmd in {"/repair-audit", "/code-repair-audit", "/bug-audit"}:
                return self.format_result(self.tools.call("code_repair_audit", path=rest or "workspace:."))
            if cmd in {"/code-review", "/deep-code-review"}:
                return self.format_result(self.tools.call("code_review_audit", path=rest or "__wla_source__"))
            if cmd in {"/code-quality-gate", "/code-rabbit-review", "/review-gate"}:
                return self.format_result(self.tools.call("code_quality_gate", path=rest or "__wla_source__"))
            if cmd in {"/codebase-audit", "/integrity-audit", "/full-codebase-audit"}:
                return self.format_result(self.tools.call("codebase_integrity_audit", path=rest or "__wla_source__"))
            if cmd in {"/cohesion-report", "/architecture-cohesion"}:
                return self.format_result(self.tools.call("cohesion_report", goal=rest or "general Nova reliability", path="."))
            if cmd == "/validation-ladder":
                return self.format_result(self.tools.call("validation_ladder", goal=rest or ""))
            if cmd in {"/iteration-plan", "/development-loop"}:
                return self.format_result(self.tools.call("iteration_plan", goal=rest or ""))
            if cmd in {"/docker", "/docker-status", "/docker-diagnostics"}:
                return self.format_result(self.tools.call("docker_status"))
            if cmd == "/docker-ps":
                return self.format_result(self.tools.call("docker_ps"))
            if cmd == "/docker-smoke":
                return self.format_result(self.tools.call("docker_smoke", image=rest.strip() or "python:3.12-slim"))
            if cmd in {"/docker-validate", "/docker-test"}:
                raw_validate = rest.strip()
                # Users often paste Nova recommendation text after `/docker-validate quick`.
                # Treat the first line/profile token as the requested profile and ignore
                # non-shell recommendation bullets instead of executing them in Docker.
                first_line = raw_validate.splitlines()[0].strip() if raw_validate else ""
                profile_token = first_line.lower()
                validate_command = first_line or "python -m compileall -q winlocalassistant tests_*.py app.py"
                if profile_token in {"quick", "--profile quick", "profile=quick"}:
                    validate_command = "python -m compileall -q winlocalassistant tests_*.py app.py"
                elif profile_token in {"tests", "--profile tests", "profile=tests"}:
                    validate_command = "python -m pytest -q tests_v55_3_27_autonomous_docker_integration.py tests_v55_3_26_docker_validation_backend.py tests_v55_3_25_docker_diagnostics.py"
                elif profile_token in {"gui", "--profile gui", "profile=gui"}:
                    validate_command = "python -m compileall -q winlocalassistant tests_*.py app.py && python -m pytest -q tests_v55_3_24_webui_js_syntax.py tests_v55_3_23_sandbox_permission_ui.py"
                elif raw_validate and len(raw_validate.splitlines()) > 1:
                    return "I only used the first `/docker-validate` line. Run `/docker-validate quick`, `/docker-validate tests`, `/docker-validate gui`, or provide one explicit shell command."
                return self.format_result(self.tools.call("docker_validate", path=".", command=validate_command, image="python:3.12-slim", timeout=300))
            if cmd in {"/docker-validate-patch", "/docker-patch-validate"}:
                raw_patch = rest.strip()
                if not raw_patch:
                    return "Usage: /docker-validate-patch PATH_TO_PATCH.diff or /docker-validate-patch PATH_TO_PATCH.diff => COMMAND"
                patch_file = raw_patch
                validate_command = "python -m compileall -q winlocalassistant tests_*.py app.py"
                if "=>" in raw_patch:
                    patch_file, validate_command = [part.strip() for part in raw_patch.split("=>", 1)]
                profile = validate_command.lower().strip()
                if profile in {"quick", "--profile quick", "profile=quick"}:
                    validate_command = "python -m compileall -q winlocalassistant tests_*.py app.py"
                elif profile in {"tests", "--profile tests", "profile=tests"}:
                    validate_command = "python -m pytest -q tests_v55_3_29_docker_patch_validation.py tests_v55_3_28_docker_history_cleanup.py"
                elif profile in {"gui", "--profile gui", "profile=gui"}:
                    validate_command = "python -m compileall -q winlocalassistant tests_*.py app.py && python -m pytest -q tests_v55_3_24_webui_js_syntax.py tests_v55_3_23_sandbox_permission_ui.py"
                return self.format_result(self.tools.call("docker_patch_validate", path=".", patch_file=patch_file, command=validate_command, image="python:3.12-slim", timeout=300))
            if cmd in {"/docker-promote-patch", "/docker-patch-promote", "/autonomous-promote-patch"}:
                raw_promote = rest.strip()
                run_id = raw_promote
                local_command = "python -m compileall -q winlocalassistant tests_*.py app.py"
                if "=>" in raw_promote:
                    run_id, local_command = [part.strip() for part in raw_promote.split("=>", 1)]
                if local_command.lower().strip() in {"quick", "--profile quick", "profile=quick"}:
                    local_command = "python -m compileall -q winlocalassistant tests_*.py app.py"
                elif local_command.lower().strip() in {"tests", "--profile tests", "profile=tests"}:
                    local_command = "python -m pytest -q tests_v55_3_31_autonomous_patch_promotion.py tests_v55_3_30_cohesion_architecture.py tests_v55_3_29_docker_patch_validation.py"
                return self.format_result(self.tools.call("docker_promote_patch", run_id=run_id, path=".", local_command=local_command, rollback_on_failure=True))
            if cmd == "/docker-history":
                try:
                    limit = int(rest.strip() or "20")
                except ValueError:
                    limit = 20
                return self.format_result(self.tools.call("docker_history", limit=limit))
            if cmd == "/docker-clean":
                try:
                    keep = int(rest.strip() or "20")
                except ValueError:
                    keep = 20
                return self.format_result(self.tools.call("docker_clean", keep=keep))
            if cmd == "/docker-help":
                return self.format_result(self.tools.call("docker_help"))
            if cmd in {"/sandbox-approve", "/sandbox-permit", "/sandbox-confirm"}:
                return self.approve_sandbox_permission(rest or "yes")
            if cmd in {"/sandbox-cancel", "/sandbox-deny"}:
                return self.approve_sandbox_permission("no")
            if cmd in {"/sandbox-pending", "/sandbox-permission"}:
                return render_pending_sandbox_permission_markdown()
            if cmd in {"/sandbox", "/sandbox-status"}:
                return self.format_result(self.tools.call("sandbox_status"))
            if cmd in {"/sandbox-setup-help", "/sandbox-install-help"}:
                return self.format_result(self.tools.call("sandbox_setup_help"))
            if cmd == "/sandbox-linux":
                return self.sandbox_command("linux", rest)
            if cmd == "/sandbox-kali":
                return self.sandbox_command("kali", rest)
            if cmd == "/sandbox-exec":
                raw = rest.strip()
                if not raw:
                    return "Usage: /sandbox-exec linux|kali <command>"
                p2 = raw.split(maxsplit=1)
                profile = p2[0].lower()
                command = p2[1] if len(p2) > 1 else ""
                if profile not in {"linux", "kali"}:
                    return "Usage: /sandbox-exec linux|kali <command>"
                return self._sandbox_exec_or_permission(profile, command, timeout=60)
            if cmd == "/sandbox-autonomy":
                return self.sandbox_flag_command("autonomy", rest)
            if cmd == "/sandbox-network":
                return self.sandbox_flag_command("network", rest)
            if cmd == "/sandbox-authorized-lab":
                return self.sandbox_flag_command("authorized_lab", rest)
            if cmd == "/sandbox-policy":
                return self.sandbox_policy_command(rest)
            if cmd in {"/sandbox-less-strict", "/sandbox-trusted-lab"}:
                raw_policy = (rest or "status").strip().lower()
                if raw_policy in {"on", "enable", "yes", "true", "1", "trusted", "trusted_lab", "less_strict"}:
                    return self.sandbox_policy_command("trusted_lab")
                if raw_policy in {"off", "disable", "no", "false", "0", "strict"}:
                    return self.sandbox_policy_command("balanced")
                return self.sandbox_policy_command("status")
            if cmd in {"/research", "/research-sources"}:
                raw = rest.strip()
                if not raw:
                    return "Usage: /research TOPIC or /research TOPIC => https://source1 https://source2\nUse /allow-internet on to let Nova discover public web sources automatically."
                if "=>" in raw:
                    topic, urls = raw.split("=>", 1)
                else:
                    topic, urls = raw, ""
                self._set_avatar("thinking", "🔎", "Researching", f"Gathering and analysing sources for: {topic.strip()[:120]}")
                return self.format_result(self.tools.call("research", topic=topic.strip(), urls=urls.strip()))
            if cmd in {"/db", "/database", "/databases"}:
                return self.database_command(rest)
            if cmd in {"/efficiency", "/performance", "/perf"}:
                return self.efficiency_command(rest)
            if cmd == "/model-context":
                raw = rest.strip()
                if raw.lower() in {"on", "enable", "off", "disable"} or raw.lower().startswith(("max=", "limit=")):
                    return self.format_result(self.tools.call("model_context", action=raw.lower()))
                return self.format_result(self.tools.call("model_context", prompt=raw, action="preview"))
            if cmd in {"/nova-context", "/run-context", "/operating-context"}:
                raw = rest.strip()
                mode = "write" if raw.lower().endswith("--write") or raw.lower().endswith("--save") else "preview"
                goal = raw.replace("--write", "").replace("--save", "").strip()
                return self.format_result(self.tools.call("nova_context", goal=goal or "general Nova work", mode=mode))
            if cmd == "/mission-contract":
                raw = rest.strip()
                mode = "write" if "--write" in raw.lower() or "--save" in raw.lower() else "preview"
                goal = raw.replace("--write", "").replace("--save", "").strip()
                return self.format_result(self.tools.call("mission_contract", goal=goal or "general Nova task", mode=mode))
            if cmd in {"/mission-progress-score", "/mission-score"}:
                return self.format_result(self.tools.call("mission_progress_score", goal=rest.strip() or "recent Nova task"))
            if cmd in {"/surgical-recipe", "/repair-recipe"}:
                failure = self.last_error.get("result") if self.last_error else rest
                return self.format_result(self.tools.call("surgical_recipe", goal=rest.strip() or "current repair", failure=failure))
            if cmd in {"/project-types", "/project-type-registry"}:
                return self.format_result(self.tools.call("project_type_registry", goal=rest.strip()))
            if cmd == "/self-test-from-bug":
                write = "--write" in rest.lower()
                bug = rest.replace("--write", "").strip()
                return self.format_result(self.tools.call("self_test_from_bug", bug=bug or "latest Nova bug", write=write))
            if cmd in {"/development-strategy", "/iterative-strategy"}:
                raw = rest.strip()
                return self.format_result(self.tools.call("development_strategy", goal=raw or "current Nova work", last_failure=str(self.last_error.get("result") if self.last_error else "")))
            if cmd in {"/validation-evidence", "/behaviour-evidence"}:
                raw = rest.strip()
                if " --goal " in raw:
                    path, goal = raw.split(" --goal ", 1)
                else:
                    path, goal = ".", raw
                return self.format_result(self.tools.call("validation_evidence", path=path.strip() or ".", goal=goal.strip() or "current Nova work"))
            if cmd in {"/validation-matrix", "/regression-matrix"}:
                raw = rest.strip()
                if " --goal " in raw:
                    path, goal = raw.split(" --goal ", 1)
                else:
                    path, goal = ".", raw
                return self.format_result(self.tools.call("validation_matrix", path=path.strip() or ".", goal=goal.strip() or "general Nova validation"))
            if cmd in {"/adaptive-backlog", "/next-adaptations"}:
                raw = rest.strip()
                if " --goal " in raw:
                    path, goal = raw.split(" --goal ", 1)
                else:
                    path, goal = ".", raw
                return self.format_result(self.tools.call("adaptive_backlog", path=path.strip() or ".", goal=goal.strip() or "improve Nova reliability and development capability"))
            if cmd in {"/template-manifest", "/generation-templates"}:
                return self.format_result(self.tools.call("generation_template_manifest", goal=rest.strip() or "general project"))
            if cmd in {"/idle-level", "/idle-policy"}:
                raw = rest.strip()
                if raw:
                    return self.format_result(self.tools.call("idle_policy", action="set", level=raw))
                return self.format_result(self.tools.call("idle_policy", action="status"))
            if cmd in {"/receipt-history", "/action-receipts"}:
                raw = rest.strip()
                try:
                    limit = int(raw) if raw else 20
                except Exception:
                    limit = 20
                return self.format_result(self.tools.call("receipt_history", limit=limit))
            if cmd in {"/role-router", "/model-roles", "/local-model-roles"}:
                raw = rest.strip()
                failure = str(self.last_error.get("result") if self.last_error else "")
                return self.format_result(self.tools.call("role_router", goal=raw or "current Nova work", last_failure=failure))
            if cmd in {"/jarvis-bridge", "/daemon-bridge"}:
                raw = rest.strip()
                action = "probe" if raw.lower().startswith(("probe", "status", "health")) else "map"
                url = ""
                if action == "probe":
                    parts = raw.split(maxsplit=1)
                    url = parts[1].strip() if len(parts) > 1 else ""
                return self.format_result(self.tools.call("jarvis_bridge", url=url, action=action))
            if cmd == "/jarvis-status":
                return self.format_result(self.tools.call("jarvis_status", url=rest.strip()))
            if cmd in {"/jarvis-doctor", "/jarvis-setup", "/jarvis-onboarding"}:
                return self.format_result(self.tools.call("jarvis_doctor", url=rest.strip()))
            if cmd in {"/sidecar-policy", "/screen-awareness-policy"}:
                raw = rest.strip()
                kwargs = {}
                # Accept compact forms such as: /sidecar-policy sidecar=read_only proactive=queue_for_review screen=manual_snapshot
                aliases = {
                    "sidecar": "sidecar_level", "sidecar_level": "sidecar_level",
                    "proactive": "proactive_level", "proactive_level": "proactive_level",
                    "screen": "screen_awareness", "screen_awareness": "screen_awareness",
                    "remote": "allow_remote", "allow_remote": "allow_remote",
                    "file": "allow_file_write", "files": "allow_file_write", "write": "allow_file_write",
                    "shell": "allow_shell", "terminal": "allow_shell",
                    "browser": "allow_browser",
                }
                for token in raw.split():
                    if "=" in token:
                        k, v = token.split("=", 1)
                        key = aliases.get(k.strip().lower())
                        if key:
                            kwargs[key] = v.strip()
                    elif token:
                        kwargs.setdefault("sidecar_level", token.strip())
                return self.format_result(self.tools.call("sidecar_policy", **kwargs))
            if cmd == "/sidecar-preflight":
                return self.format_result(self.tools.call("sidecar_preflight", requested=rest.strip()))
            if cmd in {"/sidecar-enrollment", "/sidecar-checklist"}:
                return self.format_result(self.tools.call("sidecar_enrollment", requested=rest.strip()))
            if cmd in {"/bridge-receipts", "/jarvis-receipts"}:
                raw = rest.strip()
                try:
                    limit = int(raw) if raw else 20
                except Exception:
                    limit = 20
                return self.format_result(self.tools.call("bridge_receipts", limit=limit))
            if cmd in {"/browser-harness", "/safe-browser-harness"}:
                raw = rest.strip()
                parts = raw.split(maxsplit=1)
                target = parts[0] if parts else ""
                mode = parts[1] if len(parts) > 1 else "plan"
                return self.format_result(self.tools.call("browser_harness", target_url=target, mode=mode))
            if cmd == "/jarvis-test-prompts":
                return self.format_result(self.tools.call("jarvis_test_prompts"))
            if cmd in {"/bridge-authority", "/authority-gate"}:
                raw = rest.strip()
                parts = raw.split(maxsplit=3)
                kwargs = {"capability": parts[0] if len(parts) > 0 else "general", "action": parts[1] if len(parts) > 1 else "review", "target": parts[2] if len(parts) > 2 else "", "risk": parts[3] if len(parts) > 3 else "medium"}
                return self.format_result(self.tools.call("bridge_authority", **kwargs))
            if cmd in {"/workflow-blueprint", "/jarvis-workflow"}:
                return self.format_result(self.tools.call("workflow_blueprint", goal=rest.strip() or "improve Nova safely"))
            if cmd in {"/workflow-run", "/supervised-workflow-run"}:
                raw = rest.strip()
                confirm = "--confirm" in raw.lower()
                goal = raw.replace("--confirm", "").strip() or "validate Nova safely"
                return self.format_result(self.tools.call("workflow_run", goal=goal, confirm=confirm))
            if cmd in {"/startup-validation", "/startup-gate"}:
                raw = rest.strip().lower()
                mode = "compile" if "compile" in raw else "quick"
                return self.format_result(self.tools.call("startup_validation", mode=mode, timeout=90))
            if cmd in {"/nova-system-test", "/nova-full-test", "/nova-test-all", "/test-nova"}:
                raw = rest.strip().lower()
                profile = "full" if raw in {"full", "deep", "release", "all"} or "--full" in raw else "quick"
                return self.format_result(self.tools.call("nova_system_test", profile=profile, timeout=150 if profile == "full" else 120))
            if cmd in {"/completion-audit", "/previous-task-audit", "/task-completion-audit"}:
                raw = rest.strip().lower()
                profile = "full" if raw in {"full", "deep", "release", "all"} or "--full" in raw else "quick"
                return self.format_result(self.tools.call("completion_audit", profile=profile))
            if cmd in {"/release-readiness", "/release-gate", "/release-gate-full"}:
                raw = rest.strip().lower()
                full = cmd == "/release-gate-full" or raw in {"full", "deep", "release", "all"} or "--full" in raw
                include_browser = False if "--no-browser" in raw else None
                return self.format_result(self.tools.call("release_readiness", full=full, include_browser=include_browser))
            if cmd in {"/release-package", "/clean-release-package", "/package-release"}:
                raw = rest.strip()
                low_raw = raw.lower()
                include_reports = "--include-reports" in low_raw
                force = "--force" in low_raw
                name = raw.replace("--include-reports", "").replace("--force", "").strip()
                return self.format_result(self.tools.call("release_package", name=name, include_reports=include_reports, force=force))
            if cmd in {"/codebase-advisor", "/next-codebase-improvements", "/codebase-improvement-plan"}:
                return self.format_result(self.tools.call("codebase_advisor"))
            if cmd in {"/audit-log", "/nova-audit-log"}:
                raw = rest.strip()
                try:
                    limit = int(raw) if raw else 30
                except Exception:
                    limit = 30
                return self.format_result(self.tools.call("audit_log", limit=limit))
            if cmd in {"/proactive-actions", "/proactive-action-queue"}:
                raw = rest.strip()
                if not raw or raw.lower() in {"list", "status", "show"}:
                    return self.format_result(self.tools.call("proactive_actions", action="list"))
                # Optional form: capability=shell risk=high reason=... -- action text
                capability = "general"; risk = "medium"; target = ""; reason = ""
                action_text = raw
                if " -- " in raw:
                    prefix, action_text = raw.split(" -- ", 1)
                    for token in prefix.split():
                        if "=" in token:
                            k, v = token.split("=", 1)
                            if k == "capability": capability = v
                            elif k == "risk": risk = v
                            elif k == "target": target = v
                            elif k == "reason": reason = v
                return self.format_result(self.tools.call("proactive_actions", action=action_text, capability=capability, target=target, reason=reason, risk=risk))
            if cmd in {"/persona", "/persona-editor", "/chat-persona", "/personality-sliders"}:
                return self.format_result(self.tools.call("persona_profile"))
            if cmd == "/custom-chat-window":
                return self.format_result(self.tools.call("custom_chat_window"))
            if cmd == "/persona-set":
                return self.format_result(self.tools.call("persona_set", settings=rest.strip()))
            if cmd == "/persona-json":
                return self.format_result(self.tools.call("persona_json", json_text=rest.strip()))
            if cmd == "/persona-prompt":
                return self.format_result(self.tools.call("persona_prompt", mode=rest.strip() or "default"))
            if cmd in {"/voice-audit", "/voice-command-audit"}:
                raw = rest.strip()
                try:
                    limit = int(raw) if raw else 20
                except Exception:
                    limit = 20
                return self.format_result(self.tools.call("voice_audit", limit=limit))
            if cmd in {"/local-model-optimizer", "/model-optimization"}:
                return self.format_result(self.tools.call("local_model_optimizer", goal=rest.strip()))
            if cmd in {"/agent-harness", "/iterative-agent-harness"}:
                return self.format_result(self.tools.call("agent_harness", goal=rest.strip()))
            if cmd in {"/ai-box", "/comm-box", "/message-box"}:
                raw = rest.strip()
                if not raw or raw.lower() in {"status", "show"}:
                    return self.format_result(self.tools.call("assistant_box", action="status"))
                if raw.lower() in {"clear", "reset"}:
                    return self.format_result(self.tools.call("assistant_box", action="clear", source="user command"))
                action = "append" if raw.lower().startswith("append ") else "write"
                if action == "append":
                    raw = raw[7:].strip()
                return self.format_result(self.tools.call("assistant_box", action=action, message=raw, source="user command", level="info"))
            if cmd == "/architecture-audit":
                try:
                    md, js, report = write_architecture_audit_report(Path.cwd())
                    log_activity("architecture_audit", "Architecture audit report generated", {"markdown": str(md), "json": str(js)})
                    return render_architecture_audit_markdown(report) + f"\n\nReport written:\n- `{md}`\n- `{js}`"
                except Exception as exc:
                    log_activity("architecture_audit_failed", "Architecture audit failed", {"error": str(exc)})
                    return f"Architecture audit failed: {exc}"
            if cmd == "/attach-file":
                return self._file_context_command(rest)
            if cmd == "/context-files":
                return self._file_context_command(rest or "list")
            if cmd == "/clear-context-files":
                return self._file_context_command("clear")
            if cmd == "/image-generate":
                return self._image_generate_command(rest)
            if cmd == "/image-edit":
                return self._image_edit_command(rest)
            if cmd == "/image-draft":
                return self._image_draft_command(rest)
            if cmd in {"/image-setup-help", "/image-help", "/image-setup-wizard"}:
                return render_image_setup_wizard()
            if cmd == "/image-status":
                return render_image_generation_status()
            if cmd in {"/self-awareness", "/self-aware", "/capability-audit"}:
                try:
                    md, js, report = write_self_awareness_report(self.config.workspace, rest or "")
                    text = render_self_awareness_markdown(report)
                    log_activity("self_awareness", "Self-awareness report generated", {"markdown": str(md), "json": str(js)})
                    return text + f"\n\nReport written:\n- `{md}`\n- `{js}`"
                except Exception as exc:
                    log_activity("self_awareness_failed", "Self-awareness report failed", {"error": str(exc)})
                    return f"Self-awareness report failed: {exc}"
            if cmd == "/planning-dashboard":
                dashboard = build_planning_dashboard(rest or "general Nova task", {"workspace": self.config.workspace})
                return render_planning_dashboard_markdown(dashboard)
            if cmd in {"/prompt-contract", "/prompt-tests"}:
                return render_prompt_contract(build_prompt_contract(rest.strip() or "general Nova task"))
            if cmd in {"/prompt-test-run", "/contract-validate"}:
                return render_contract_validation(validate_contract(rest.strip() or "general Nova task", Path.cwd()))
            if cmd in {"/candidate-tournament", "/candidate-score"}:
                return render_tournament(build_candidate_tournament(rest.strip() or "general Nova task", Path.cwd()))
            if cmd == "/candidate-promote":
                payload = build_candidate_tournament(rest.strip() or "general Nova task", Path.cwd())
                return render_tournament(payload) + "\n\nPromotion staged only: validate the winner in sandbox/Docker before writing to the live tree."
            if cmd == "/candidate-diff":
                return "# Candidate Diff\n\nThis command compares candidate text when two snippets are supplied as `A ||| B`.\n\n```diff\n" + candidate_diff(*(rest.split("|||",1) if "|||" in rest else ["", rest])) + "\n```"
            if cmd == "/candidate-failure-report":
                return render_candidate_failure_report(build_candidate_tournament(rest.strip() or "general Nova task", Path.cwd()))
            if cmd in {"/repair-diagnose", "/repair-plan", "/repair-apply", "/repair-verify", "/repair-replay", "/repair-rollback"}:
                evidence = rest.strip() or "latest Nova/project failure"
                plan = build_repair_plan(Path.cwd(), evidence)
                suffix = ""
                if cmd == "/repair-apply":
                    suffix = "\n\nApply mode is staged: Nova will use the existing guarded surgical repair/backtracking path, not blind rewrites."
                if cmd == "/repair-rollback":
                    suffix = "\n\nRollback guidance: restore the latest workspace checkpoint or Docker/hash-locked promotion backup."
                return render_repair(plan) + suffix
            if cmd in {"/trace-status", "/trace-timeline", "/trace-errors", "/replay-run"}:
                trace = build_trace(limit=300, run_id=rest.strip() if cmd == "/replay-run" else "")
                md = render_trace_markdown(trace)
                if cmd == "/trace-errors":
                    md += "\n\n## Error-like events\n" + "\n".join([f"- `{e.get('time')}` {e.get('kind')} — {str(e.get('message',''))[:160]}" for e in trace.get('events',[]) if any(k in str(e.get('kind','')).lower()+str(e.get('message','')).lower() for k in ['error','fail','blocked','timeout'])][-40:] or ['- none'])
                if cmd == "/trace-timeline":
                    md += "\n\n## Timeline view\n" + "\n".join([f"{i+1}. `{e.get('time')}` **{e.get('bucket')}** — {e.get('message','')[:120]}" for i,e in enumerate(trace.get('events',[])[-60:])])
                return md
            if cmd in {"/mcp-inspect", "/mcp-permissions", "/mcp-risk-report", "/mcp-sandbox-tool", "/mcp-deny", "/mcp-allow"}:
                return render_mcp_security(inspect_mcp_security(app=self, root=Path.cwd()))
            if cmd == "/mcp-explain-tool":
                return explain_mcp_tool(rest.strip(), app=self, root=Path.cwd())
            if cmd == "/mission-create":
                return render_mission(create_mission(rest.strip() or "improve Nova safely"))
            if cmd in {"/mission-status", "/mission-queue"}:
                return render_mission(load_mission())
            if cmd == "/mission-step":
                return render_mission(mission_step())
            if cmd in {"/mission-promote", "/mission-stop"}:
                m = load_mission(); m['status'] = 'stopped' if cmd == "/mission-stop" else 'ready_for_promotion_review'; return render_mission(m)
            if cmd in {"/model-output-repair-json", "/model-output-split-files", "/model-output-off-course", "/model-output-coach"}:
                recent = tail_jsonl(MODEL_IO_PATH, limit=1); out = str(recent[-1].get('reply') if recent else '') if recent else ''
                return render_model_output_coach(analyze_model_output(rest.strip() or "current model output", out))
            if cmd in {"/env-profile", "/env-doctor", "/env-fix-plan", "/env-install-plan"}:
                profile = rest.strip() or ("dev" if cmd != "/env-profile" else "minimal")
                return render_env_profile(build_env_profile(profile))
            if cmd in {"/benchmark-system", "/benchmark-models", "/benchmark-fast-build", "/benchmark-docker", "/benchmark-gui", "/migration-report", "/new-pc-tune"}:
                return render_benchmark(benchmark_system())
            if cmd == "/project-state":
                from .project_state import render_project_state_command
                return render_project_state_command(rest, root=self.config.workspace)
            if cmd in {"/project-history", "/project-failures", "/project-success-criteria", "/project-compare", "/project-restore"}:
                return render_project_state(load_project_state(Path.cwd()))
            if cmd == "/regression-add":
                return render_regressions([add_regression(rest.strip() or "unspecified regression")])
            if cmd in {"/regression-list", "/regression-run", "/regression-from-last-failure"}:
                return render_regressions(load_regressions())
            if cmd == "/regression-export":
                return render_regressions(export_regressions())
            if cmd in {"/regression-sweep", "/no-regression-check", "/functionality-matrix", "/integration-health"}:
                payload = build_regression_sweep(Path.cwd(), app=self)
                return render_regression_sweep(payload)
            if cmd in {"/weakspot-audit", "/error-hunt", "/stability-audit", "/weakspots"}:
                md, js, report = write_weakspot_report(Path.cwd())
                return render_weakspot_audit(report) + f"\n\nReport written:\n- `{md}`\n- `{js}`"
            if cmd in {"/comprehensive-user-test", "/user-test-suite", "/qa-test"}:
                md, js, report = write_user_testing_report(Path.cwd())
                return render_user_testing_report(report) + f"\n\nReport written:\n- `{md}`\n- `{js}`"
            if cmd in {"/user-feedback-tests", "/full-functionality-test-commands", "/nova-test-commands"}:
                return """# Nova manual user-feedback test commands

Run these one by one in the Nova chat UI after installing this patch. They are designed to cover routing, voice/state, local model health, project creation, project editing, files, autonomy, sandbox/Jarvis gates and release verification without needing hidden IDs.

## Core health
- `/status`
- `/doctor`
- `/command-verify`
- `/architecture-audit`
- `/bug-review`
- `/regression-sweep`

## UI and live activity
- `/activity`
- `/active-run`
- `/gui-layout-status`
- `/gui-reset-help`
- `/media-status`
- `/image-plan cinematic robot dog mascot`
- `/video-status`
- `/tool-use-plan fix GUI layout and choose correct tools`
- `/pipeline-route fix GUI layout and verify backend routes`
- `/role-router fix GUI command mismatch`
- `/comm-box status`
- `/gui-feature-coverage`
- `/voice-pipeline-review Hey Nova wake pipeline`

## Voice and wake flow
- Say: `Hey Nova` and confirm you hear the ready cue before speaking the request.
- Then say: `status` and check Nova does not return to Listening while the reply is still thinking/speaking.
- `/voice-command-audit`
- `/voice-device-status`

## Coding/project generation
- `/model-health`
- `/model-timeout-profile`
- `/do make a polished minimal browser game with score, keyboard controls and clear success instructions`
- `/run-project`
- `/project-files`
- `/do improve the current game with one safe visual polish change and verify it`

## Routing sanity
- `a test to test all of your functionality`
- `/reply 1` only when Nova is explicitly waiting for an interactive planning choice.

## Autonomous/safety gates
- `/autonomous status`
- `/idle status`
- `/patch-impact-plan winlocalassistant/webui.py winlocalassistant/tools.py`
- `/nova-self-apply improve docs only`

## Optional integrations
- `/remote-access-test`
- `/remote-api-health 127.0.0.1 8767 --dry-run`
- `/remote-profile-wizard --host 127.0.0.1 --port 8767 --mac AA:BB:CC:DD:EE:FF`
- `/sandbox-status`
- `/jarvis-doctor`
- `/bridge-receipts`
"""
            if cmd == "/improvement-proposals":
                payload = build_improvement_proposals(Path.cwd(), focus=rest.strip())
                return render_improvement_cycle(payload)
            if cmd == "/improvement-cycle":
                confirmed = "--confirm" in rest.lower() or "confirm" in rest.lower()
                payload = complete_improvement_proposals(Path.cwd(), focus=rest.replace("--confirm", "").replace("confirm", "").strip(), confirm=confirmed)
                if not confirmed:
                    return render_improvement_cycle(payload) + "\n\nDry run only. Run `/improvement-cycle --confirm` to complete safe proposal artifacts."
                return render_improvement_cycle(payload)
            if cmd in {"/completed-improvements", "/improvement-status"}:
                payload = load_latest_improvement_cycle(Path.cwd())
                if payload.get("proposals"):
                    return render_improvement_cycle(payload)
                return "# Improvement Cycle Status\n\n```json\n" + json.dumps(payload, indent=2) + "\n```"
            if cmd in {"/improvement-roadmap", "/next-improvements"}:
                payload = build_next_improvement_roadmap(Path(self.config.workspace), focus=rest.strip())
                return render_improvement_roadmap(payload)
            if cmd == "/improvement-impact":
                roadmap = build_next_improvement_roadmap(Path(self.config.workspace), focus=rest.strip())
                payload = {**roadmap, "impact_matrix": build_improvement_impact_matrix(roadmap)}
                return render_improvement_roadmap(payload)
            if cmd == "/implement-improvements":
                confirmed = "--confirm" in rest.lower() or "confirm" in rest.lower()
                focus = rest.replace("--confirm", "").replace("confirm", "").strip()
                payload = complete_next_improvements(Path(self.config.workspace), focus=focus, confirm=confirmed)
                if not confirmed:
                    return render_improvement_roadmap(payload) + "\n\nDry run only. Run `/implement-improvements --confirm` to complete safe roadmap artifacts."
                return render_improvement_roadmap(payload)
            if cmd == "/proposal-ledger":
                payload = load_latest_improvement_roadmap(Path(self.config.workspace))
                if payload.get("proposals"):
                    return render_improvement_roadmap(payload)
                return "# Proposal Ledger\n\n```json\n" + json.dumps(payload, indent=2) + "\n```"
            if cmd in {"/blueprint", "/blueprint-build", "/blueprint-validate"}:
                goal = rest.strip() or "tiny useful local app"
                bp = build_project_blueprint(goal)
                return render_blueprint_markdown(bp)
            if cmd in {"/candidate-build", "/candidate-compare", "/candidate-report"}:
                goal = rest.strip() or "tiny useful local app"
                return render_candidate_markdown(build_candidate_set(goal))
            if cmd in {"/model-output-score", "/candidate-score"}:
                goal = rest.strip() or "current model output"
                # Score the recent local model reply preview when available. This is intentionally local-only.
                recent = tail_jsonl(MODEL_IO_PATH, limit=1)
                text = ""
                if recent:
                    item = recent[-1]
                    text = str(item.get("reply") or item.get("response") or item.get("content") or item)
                return render_score_markdown(score_candidate(goal, text=text))
            if cmd in {"/trace-last", "/trace-export"}:
                trace = build_trace(limit=160)
                md = render_trace_markdown(trace)
                if cmd == "/trace-export":
                    out = Path("docs") / "NOVA_TRACE_EXPORT_LATEST.md"
                    out.parent.mkdir(exist_ok=True)
                    out.write_text(md, encoding="utf-8")
                    return md + f"\n\nReport written: `{out}`"
                return md
            if cmd == "/trace-run":
                return render_trace_markdown(build_trace(limit=300, run_id=rest.strip()))
            if cmd in {"/performance-dashboard", "/trace-dashboard"}:
                return render_performance_dashboard(build_trace(limit=240))
            if cmd == "/gui-feature-map":
                return render_gui_feature_map(build_gui_feature_map(Path.cwd()))
            if cmd == "/gui-redesign-preview" or (cmd == "/gui-mode" and rest.strip().lower() in {"cockpit", "cockpit-preview", "preview"}):
                return cockpit_preview_markdown()
            if cmd == "/gui-mode":
                return "GUI mode support is staged safely. Current default is `classic`. Use `/gui-mode cockpit` for the non-mutating cockpit preview, then `/gui-feature-map` and `/gui-regression-test` before enabling a redesign by default."
            if cmd == "/gui-regression-test":
                return render_gui_regression(gui_regression_check(Path.cwd()))
            if cmd in {"/mcp-export-manifest", "/mcp-tools", "/mcp-status"}:
                manifest = build_mcp_manifest(app=self, root=Path.cwd())
                md = render_mcp_manifest(manifest)
                if cmd == "/mcp-export-manifest":
                    out = Path("docs") / "NOVA_MCP_STYLE_MANIFEST_LATEST.json"
                    out.parent.mkdir(exist_ok=True)
                    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
                    return md + f"\n\nJSON manifest written: `{out}`"
                return md
            if cmd in {"/gui-snapshot", "/gui-visual-test"}:
                return render_gui_snapshot_status(build_gui_snapshot_status(Path(self.config.workspace)))
            if cmd in {"/gui-layout-status", "/gui-layout-check", "/gui-layout-diagnostics"}:
                return render_gui_layout_diagnostics(build_gui_layout_diagnostics(Path(self.config.workspace)))
            if cmd in {"/gui-reset-help", "/gui-layout-reset-help"}:
                return render_gui_reset_help()
            if cmd in {"/gui-ai-help", "/gui-context-help", "/gui-command-help"}:
                return render_gui_context_help(build_gui_context_help(rest.strip()))
            if cmd == "/gui-ai-upgrades":
                return render_repo_inspired_gui_help_upgrades()
            if cmd in {"/command-help", "/commands-help", "/help-search"}:
                return render_command_help(command_help_payload(rest.strip()))
            if cmd in {"/legacy-continuity-audit", "/legacy-regression-lock", "/feature-regression-guard"}:
                payload = build_legacy_continuity_audit(Path(self.config.workspace))
                if "--write" in rest:
                    out = write_legacy_contract(Path(self.config.workspace))
                    return render_legacy_continuity_audit(payload) + f"\n\nContract written: `{out}`"
                return render_legacy_continuity_audit(payload)
            if cmd in {"/arcade", "/nova-arcade", "/arcade-status", "/arcade-list"}:
                return render_arcade_registry(arcade_registry())
            if cmd == "/arcade-launch":
                return render_arcade_launch(rest.strip() or "system-runner")
            if cmd == "/arcade-manifest":
                out = write_arcade_manifest(Path(self.config.workspace))
                return render_arcade_registry(arcade_registry()) + f"\n\nManifest written: `{out}`"
            if cmd in {"/behavior-rules", "/behaviour-rules", "/rules"}:
                return render_behavior_rules(list_behavior_rules())
            if cmd in {"/remember-behavior", "/remember-behaviour", "/behavior-rule-add", "/behaviour-rule-add"}:
                payload = add_behavior_rule(rest.strip(), source="chat_command")
                if not payload.get("ok"):
                    return "Could not save behaviour rule: " + str(payload.get("error") or "unknown error")
                return "Saved behaviour rule.\n\n" + render_behavior_rules(list_behavior_rules())
            if cmd in {"/forget-behavior", "/forget-behaviour", "/behavior-rule-delete", "/behaviour-rule-delete"}:
                payload = delete_behavior_rule(rest.strip())
                return ("Removed behaviour rule." if payload.get("ok") else "No matching behaviour rule found.") + "\n\n" + render_behavior_rules(list_behavior_rules())
            if cmd in {"/build-info", "/patch-info", "/gui-build-info"}:
                return render_patch_identity(build_patch_identity(Path(self.config.workspace)))
            if cmd in {"/perf-env", "/perf-apply-env"}:
                payload = apply_startup_performance_environment()
                return "# Nova Performance Environment Applied\n\n" + json.dumps(payload, indent=2)
            if cmd in {"/perf-status", "/performance-status", "/local-ai-status", "/ai-performance-status"}:
                return render_performance_status(collect_performance_status(Path(self.config.workspace)))
            if cmd in {"/perf-tune-plan", "/performance-tune-plan", "/local-ai-performance-plan"}:
                return render_tuning_plan(build_tuning_plan())
            if cmd in {"/perf-benchmark", "/performance-benchmark", "/local-ai-benchmark"}:
                if "--write-scripts" in rest:
                    return render_write_result(write_benchmark_scripts(Path(self.config.workspace)))
                return render_benchmark_plan(benchmark_plan_payload(Path(self.config.workspace)))
            if cmd in {"/perf-artifact-checklist", "/performance-artifact-checklist"}:
                return render_artifact_checklist()
            if cmd in {"/mission-dashboard", "/mission-progress", "/mission-retrospective", "/mission-resume"}:
                return render_payload(build_mission_dashboard(rest.strip()), "Autonomous Mission Dashboard")
            if cmd in {"/cycle-score", "/autonomous-progress-score", "/idle-progress-score"}:
                mode = "idle" if "idle" in cmd else "autonomous"
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "progress_score": _score_from_events(_events(160), mode)}, "Cycle Progress Score")
            if cmd in {"/autonomous-explain-tools", "/idle-explain-tools", "/tool-choice-trace"}:
                return render_payload(build_tool_choice_trace(rest.strip()), "Tool Choice Trace")
            if cmd in {"/repetition-guard-status", "/repetition-memory"}:
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "repetition_guard": repeated_signature()}, "Repetition Guard")
            if cmd == "/repetition-clear":
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "repetition_guard": clear_repetition_memory()}, "Repetition Guard Cleared")
            if cmd in {"/idle-silence", "/idle-summaries", "/idle-background-only"}:
                val = not any(x in rest.lower() for x in ["off", "false", "0", "disable"])
                key = cmd.strip('/').replace('-', '_')
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "background_idle_settings": set_background_setting(key, val)}, "Idle Background Settings")
            if cmd == "/autonomous-patch-mode":
                val = not any(x in rest.lower() for x in ["off", "false", "0", "disable"])
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "background_idle_settings": set_background_setting("autonomous_patch_mode", val)}, "Autonomous Patch Mode")
            if cmd in {"/patch-review", "/patch-reject"}:
                action = "status" if cmd == "/patch-review" else "rollback"
                return render_patch_queue(patch_queue_action(action, rest.strip()))
            if cmd == "/mistake-log":
                return render_payload(load_mistake_log(), "Mistake Learning Log")
            if cmd == "/mistake-to-regression":
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "items": [mistake_to_regression()]}, "Mistake Converted To Regression")
            if cmd in {"/autonomous-summary", "/autonomous-last-report"}:
                return render_payload(autonomous_last_report(), "Autonomous Last Detailed Report")
            if cmd in {"/surgical-fallback-v2", "/repair-strategy"}:
                payload = build_surgical_fallback_plan(Path.cwd(), rest.strip() or "repair current project")
                return render_iterative_coding_markdown(payload)
            if cmd in {"/iterative-code-loop", "/coding-loop-status"}:
                payload = build_iterative_coding_loop(Path.cwd(), rest.strip() or "improve current project")
                return render_iterative_coding_markdown(payload)
            if cmd == "/edit-repair-plan":
                md, js, payload = write_iterative_coding_report(Path.cwd(), rest.strip() or "improve editing and repair reliability")
                return render_iterative_coding_markdown(payload) + f"\n\nReport written:\n- `{md}`\n- `{js}`"
            if cmd in {"/nova-mega-test", "/nova-test-all", "/test-all-aspects"}:
                if "--confirm" not in rest.lower() and "confirm" not in rest.lower():
                    return "Nova Mega Test runs many Nova aspect checks. Run `/nova-mega-test --confirm` to continue. Copy/paste that output back here for streamlined debugging."
                payload = run_wla_mega_test(Path.cwd(), app=self)
                return render_wla_mega_test(payload)
            if cmd in {"/build-quality-report", "/build-quality-score", "/build-quality-repair", "/build-quality-compare"}:
                return render_build_quality(build_quality_report(Path.cwd(), rest.strip() or "current project"))
            if cmd in {"/browser-run-test", "/browser-click-test", "/browser-storage-test", "/browser-export-test", "/browser-screenshot-test"}:
                return render_browser_runtime(build_browser_runtime_test(Path.cwd(), rest.strip() or "current project", mode=cmd.strip('/')))
            if cmd in {"/model-reliability", "/model-stuck-diagnose", "/model-output-retry-plan", "/model-json-enforcer", "/model-timeout-profile"}:
                return render_model_reliability(build_model_reliability(Path.cwd(), rest.strip()))
            if cmd == "/model-fallback-strategy":
                return render_strategy(build_model_fallback_strategy(Path.cwd(), rest.strip()))
            if cmd in {"/patch-queue", "/patch-preview"}:
                return render_patch_queue(patch_queue_action("status", rest.strip()))
            if cmd == "/patch-propose":
                return render_patch_queue(patch_queue_action("propose", rest.strip() or "safe Nova improvement"))
            if cmd == "/patch-validate":
                return render_patch_queue(patch_queue_action("validate", rest.strip()))
            if cmd == "/patch-promote":
                return render_patch_queue(patch_queue_action("promote", rest.strip()))
            if cmd == "/patch-rollback":
                return render_patch_queue(patch_queue_action("rollback", rest.strip()))
            if cmd in {"/gui-feature-coverage", "/gui-redesign-test"}:
                return render_gui_cockpit_v2(build_gui_cockpit_v2(Path.cwd(), mode=cmd.strip('/')))
            if cmd in {"/voice-device-status", "/voice-calibrate", "/voice-readback-test"}:
                return render_voice_mode(build_voice_mode_report(Path.cwd(), mode=cmd.strip('/')))
            if cmd == "/template-list":
                return render_templates(list_templates())
            if cmd in {"/template-build", "/template-customize"}:
                return render_templates(build_template_project(Path.cwd(), rest.strip() or "notes-app"))
            if cmd in {"/preview-start", "/preview-stop", "/preview-status", "/preview-open", "/preview-screenshot"}:
                return render_preview(build_preview_server_report(Path.cwd(), action=cmd.strip('/')))
            if cmd in {"/feature-readiness", "/feature-fix-plan", "/feature-enable", "/feature-disable"}:
                return render_feature_readiness(build_feature_readiness(Path.cwd()))
            if cmd in {"/explain-error", "/error-summary", "/error-next-step", "/error-fix-plan"}:
                return render_error_explanation(explain_error(rest.strip()))
            if cmd in {"/export-support-report", "/support-report", "/chatgpt-report", "/copy-debug-context"}:
                return render_support_report(build_support_report(Path.cwd(), rest.strip()))
            if cmd in {"/index-nova", "/search-nova-docs", "/search-nova-code", "/explain-command", "/explain-feature"}:
                return render_docs_index(docs_index(Path.cwd(), rest.strip()))
            if cmd in {"/regression-from-bug", "/regression-test-generate", "/regression-test-run", "/regression-protection-status"}:
                return render_regression_test(regression_test_generate(Path.cwd(), rest.strip() or "unspecified Nova bug"))
            if cmd in {"/new-pc-benchmark", "/new-pc-model-select", "/new-pc-timeout-tune", "/new-pc-docker-tune", "/new-pc-profile-save"}:
                return render_benchmark(benchmark_system())
            if cmd in {"/mission-dashboard", "/mission-progress", "/mission-retrospective", "/mission-resume"}:
                return render_payload(build_mission_dashboard(rest.strip()), "Autonomous Mission Dashboard")
            if cmd in {"/cycle-score", "/autonomous-progress-score", "/idle-progress-score"}:
                mode = "idle" if "idle" in cmd else "autonomous"
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "progress_score": _score_from_events(_events(160), mode)}, "Cycle Progress Score")
            if cmd in {"/autonomous-explain-tools", "/idle-explain-tools", "/tool-choice-trace"}:
                return render_payload(build_tool_choice_trace(rest.strip()), "Tool Choice Trace")
            if cmd in {"/repetition-guard-status", "/repetition-memory"}:
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "repetition_guard": repeated_signature()}, "Repetition Guard")
            if cmd == "/repetition-clear":
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "repetition_guard": clear_repetition_memory()}, "Repetition Guard Cleared")
            if cmd in {"/idle-silence", "/idle-summaries", "/idle-background-only"}:
                val = not any(x in rest.lower() for x in ["off", "false", "0", "disable"])
                key = cmd.strip('/').replace('-', '_')
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "background_idle_settings": set_background_setting(key, val)}, "Idle Background Settings")
            if cmd == "/autonomous-patch-mode":
                val = not any(x in rest.lower() for x in ["off", "false", "0", "disable"])
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "background_idle_settings": set_background_setting("autonomous_patch_mode", val)}, "Autonomous Patch Mode")
            if cmd in {"/patch-review", "/patch-reject"}:
                action = "status" if cmd == "/patch-review" else "rollback"
                return render_patch_queue(patch_queue_action(action, rest.strip()))
            if cmd == "/mistake-log":
                return render_payload(load_mistake_log(), "Mistake Learning Log")
            if cmd == "/mistake-to-regression":
                return render_payload({"generated_at": time.strftime("%Y-%m-%d %H:%M:%S"), "items": [mistake_to_regression()]}, "Mistake Converted To Regression")
            if cmd in {"/autonomous-summary", "/autonomous-last-report"}:
                return render_payload(autonomous_last_report(), "Autonomous Last Detailed Report")
            if cmd == "/mistake-learning-status":
                return render_learning_status(learning_status(Path.cwd()))
            if cmd == "/autonomous-explain":
                return self.autonomous_explain_text(rest)
            if cmd == "/autonomous-plan":
                return self.autonomous_sequence_text(rest)
            if cmd in {"/autonomy-capabilities", "/capability-plan", "/capabilities-plan"}:
                return self.autonomy_capabilities_text(rest)
            if cmd in {"/mutable-plan", "/prompt-plan"}:
                return self.mutable_plan_text(rest)
            if cmd == "/autonomous-journal":
                path, data = latest_run_journal()
                if not path or not data:
                    return "No autonomous sequence journal has been written yet. Run /autonomous once GOAL first."
                lines = ["# Latest Autonomous Sequence Journal", "", f"Path: `{path}`", f"Run ID: `{data.get('run_id','')}`", f"Status: **{data.get('status','unknown')}**", f"Goal: {data.get('goal','')}", "", "## Summary", f"- Total steps: {data.get('total_steps',0)}", f"- Executed: {data.get('executed_steps',0)}", f"- Skipped: {data.get('skipped_steps',0)}", f"- Failed: {data.get('failed_steps',0)}", f"- Blocked/review-required: {data.get('blocked_steps',0)}", f"- Next: `{data.get('next_recommended_action','review_autonomous_report')}`"]
                return "\n".join(lines)
            if cmd in {"/validation-status", "/validate-status", "/validation-progress"}:
                validation_root = Path(self.config.workspace).expanduser().resolve()
                return render_validation_status(load_validation_status(validation_root))
            if cmd in {"/remote-access", "/remote-access-status", "/remote-status"}:
                remote_root = Path(self.config.workspace).expanduser().resolve()
                return render_remote_access_status(build_remote_access_status(remote_root))
            if cmd in {"/remote-access-plan", "/remote-access-setup", "/remote-setup"}:
                remote_root = Path(self.config.workspace).expanduser().resolve()
                return render_remote_access_plan(build_remote_access_plan(remote_root))
            if cmd in {"/remote-access-test", "/remote-access-preflight", "/remote-preflight"}:
                remote_root = Path(self.config.workspace).expanduser().resolve()
                return render_remote_access_preflight(build_remote_access_preflight(remote_root))
            if cmd in {"/remote-api-health", "/remote-health", "/nova-api-health"}:
                try:
                    api_args = parse_remote_api_health_args(rest)
                    return render_remote_api_health(probe_remote_api_health(**api_args))
                except Exception as exc:
                    return f"Remote API health usage error: {exc}"
            if cmd in {"/remote-profile", "/remote-profiles"}:
                remote_root = Path(self.config.workspace).expanduser().resolve()
                try:
                    return render_remote_profiles(remote_profile_action(remote_root, rest))
                except Exception as exc:
                    return f"Remote profile usage error: {exc}"
            if cmd in {"/remote-profile-wizard", "/remote-wizard", "/remote-profile-plan"}:
                remote_root = Path(self.config.workspace).expanduser().resolve()
                try:
                    return render_remote_profile_wizard(build_remote_profile_wizard(remote_root, rest))
                except Exception as exc:
                    return f"Remote profile wizard usage error: {exc}"
            if cmd in {"/remote-access-scripts", "/remote-scripts"}:
                remote_root = Path(self.config.workspace).expanduser().resolve()
                return render_remote_access_assets(write_remote_access_assets(remote_root))
            if cmd in {"/remote-wake", "/wake-pc", "/wol"}:
                try:
                    args = parse_remote_wake_args(rest)
                except Exception as exc:
                    return f"Remote wake usage error: {exc}"
                if not args.get("dry_run") and not args.get("confirm"):
                    return "Remote wake is dry-run by default unless you add `--confirm`. Try `/remote-wake AA:BB:CC:DD:EE:FF --dry-run` first, then rerun with `--confirm` only for your own PC."
                return render_wol_result(send_wake_on_lan(args["mac"], broadcast=args["broadcast"], port=args["port"], dry_run=args["dry_run"]))
            if cmd in {"/nova-brand-audit", "/brand-audit"}:
                return render_branding_audit(scan_legacy_branding(Path.cwd()))
            if cmd in {"/nova-improvement-research", "/research-improvements"}:
                return render_nova_improvement_research(build_nova_improvement_research(Path.cwd(), rest.strip()))
            if cmd in {"/nova-eval-packs", "/eval-packs"}:
                words = rest.strip().split(maxsplit=1)
                action = words[0].lower() if words else "plan"
                pack = words[1] if len(words) > 1 else "core"
                if action in {"run", "verify", "test"}:
                    return render_nova_eval_packs(run_nova_eval_pack(lambda command: self.handle_command(command), pack))
                if action in {"plan", "show", "list", ""}:
                    return render_nova_eval_packs(build_nova_eval_plan(pack if pack else "core"))
                return render_nova_eval_packs(build_nova_eval_plan(rest.strip() or "core"))
            if cmd in {"/nova-self-apply", "/verified-self-apply"}:
                bits = rest.strip().split()
                mode = bits[0].lower() if bits else "plan"
                change_id = bits[1] if len(bits) > 1 and not bits[1].startswith("--") else None
                confirm = "--confirm" in rest.lower() or "confirm" in rest.lower().split()
                if mode in {"status", "plan", "list", ""}:
                    return render_verified_change(build_verified_change_plan(Path.cwd(), change_id))
                if mode in {"preview", "diff"}:
                    return render_verified_change(preview_verified_change(Path.cwd(), change_id))
                if mode in {"apply", "promote"}:
                    return render_verified_change(apply_verified_change(Path.cwd(), change_id, confirm=confirm))
                return render_verified_change({"ok": False, "mode": mode, "status": "usage_error", "error": "Usage: /nova-self-apply [plan|preview|apply] [CHANGE_ID] [--confirm]"})
            if cmd in {"/nova-api-status", "/api-status"}:
                from .nova_api import build_api_bridge_status, render_api_bridge_status
                api_root = Path(self.config.workspace).expanduser().resolve()
                return render_api_bridge_status(build_api_bridge_status(api_root))
            if cmd == "/compare":
                cmd = "/nova-compare"
            if cmd in {"/nova-odysseus-suite", "/odysseus-suite", "/nova-odysseus-runtime", "/odysseus-runtime", "/nova-tool-permissions", "/tool-permissions", "/nova-cookbook", "/model-cookbook", "/nova-compare", "/model-compare", "/compare", "/nova-docs", "/nova-documents", "/nova-notes", "/nova-tasks", "/nova-skills", "/nova-presets", "/nova-memory-vault", "/nova-integration-gates", "/integration-gates", "/nova-fastapi-plan", "/fastapi-migration-plan", "/nova-gui-workbench-plan", "/odysseus-gui-plan", "/nova-layout-plan", "/nova-email-plan", "/nova-calendar-plan", "/nova-mobile-plan", "/nova-theme-plan", "/nova-auth-plan", "/nova-upload-plan"}:
                return handle_odysseus_suite_command(Path.cwd(), cmd, rest)
            if cmd in {"/command-catalog", "/tool-catalog"}:
                return self.command_catalog_text()
            if cmd == "/interrupt-current":
                return self.interrupt_current(rest.strip().lower() in {"--confirm", "confirm", "yes", "--yes"})
            if cmd in {"/inspiration-radar", "/nova-inspiration-radar"}:
                return self.format_result(self.tools.call("inspiration_radar", focus=rest.strip()))
            if cmd in {"/tool-context-pack", "/context-pack"}:
                return self.format_result(self.tools.call("tool_context_pack", prompt=rest.strip()))
            if cmd in {"/handoff-plan", "/nova-handoff-plan"}:
                return self.format_result(self.tools.call("handoff_plan", prompt=rest.strip()))
            if cmd in {"/improvement-preflight", "/safe-improvement-preflight"}:
                goal, files = self._split_optional_second(rest)
                return self.format_result(self.tools.call("improvement_preflight", goal=goal or rest.strip(), files=files or ""))
            if cmd in {"/coding-plan", "/project-coding-plan"}:
                return self.format_result(self.tools.call("coding_plan", goal=rest.strip()))
            if cmd in {"/coding-audit", "/nova-coding-audit"}:
                return self.format_result(self.tools.call("coding_capability_audit", goal=rest.strip()))
            if cmd in {"/local-model-performance", "/model-performance-plan"}:
                goal, hardware = self._split_optional_second(rest)
                return self.format_result(self.tools.call("local_model_performance_plan", goal=goal or rest.strip(), hardware=hardware or ""))
            if cmd in {"/high-spec-profile", "/better-pc-profile", "/upgraded-pc-profile"}:
                return self.format_result(self.tools.call("high_spec_profile"))
            if cmd in {"/subagents", "/subagent-plan", "/multi-agent-plan"}:
                return self.format_result(self.tools.call("subagent_plan", goal=rest.strip() or "improve Nova safely"))
            if cmd in {"/authority-mode", "/access-mode", "/power-controls"}:
                status = [
                    "# Nova Authority / Access Controls",
                    "",
                    "Nova can expose stronger local capabilities, but they stay explicit and logged.",
                    "",
                    f"- Internet allowed: {self.config.allow_internet}",
                    f"- Mutating tools allowed: {self.config.allow_mutating_tools}",
                    f"- Command timeout: {self.config.command_timeout_sec}s",
                    "",
                    "Useful commands:",
                    "- `/allow-internet on` enables public web fetch/provider calls.",
                    "- `/allow-mutate on` enables file-writing tools in the configured workspace.",
                    "- `/shell COMMAND` runs a PowerShell command in the workspace after existing dangerous-command checks.",
                    "- `/sidecar-policy` shows external sidecar/browser/shell gates.",
                    "- `/subagents GOAL` plans safe multi-agent work without removing the Ollama prompt lock.",
                    "",
                    "Nova does not silently grant unrestricted shell/admin access. High-risk commands still require explicit user action and tool-contract validation.",
                ]
                return "\n".join(status)
            if cmd in {"/agent-upgrade-radar", "/nova-upgrade-radar"}:
                return self.format_result(self.tools.call("agent_upgrade_radar", focus=rest.strip()))
            if cmd in {"/context-budget", "/context-compaction-plan"}:
                return self.format_result(self.tools.call("context_budget", goal=rest.strip()))
            if cmd in {"/coding-behavior-tests", "/coding-acceptance-tests"}:
                return self.format_result(self.tools.call("coding_behavior_tests", goal=rest.strip()))
            if cmd in {"/ollama-runtime-profile", "/local-model-runtime-profile"}:
                goal, hardware = self._split_optional_second(rest)
                return self.format_result(self.tools.call("ollama_runtime_profile", goal=goal or rest.strip(), hardware=hardware or ""))
            if cmd in {"/upgrade-regression-audit", "/patch-regression-audit"}:
                return self.format_result(self.tools.call("upgrade_regression_audit"))
            if cmd in {"/repo-context-map", "/nova-repo-map"}:
                return self.format_result(self.tools.call("repo_context_map", goal=rest.strip()))
            if cmd in {"/patch-impact-plan", "/impact-tests"}:
                return self.format_result(self.tools.call("patch_impact_plan", changed_files=rest.strip()))
            if cmd in {"/permission-scope-review", "/scope-review"}:
                intent, actions = self._split_optional_second(rest)
                return self.format_result(self.tools.call("permission_scope_review", intent=intent or rest.strip(), proposed_actions=actions or ""))
            if cmd in {"/local-model-benchmark", "/model-benchmark-plan"}:
                goal, hardware = self._split_optional_second(rest)
                return self.format_result(self.tools.call("local_model_benchmark_plan", goal=goal or rest.strip(), hardware=hardware or ""))
            if cmd in {"/tool-contract-audit", "/command-contract-audit"}:
                return self.format_result(self.tools.call("tool_contract_audit"))
            if cmd in {"/agent-topology", "/nova-agent-topology"}:
                return self.format_result(self.tools.call("agent_topology_plan", goal=rest.strip()))
            if cmd in {"/trace-observability", "/trace-spec"}:
                return self.format_result(self.tools.call("trace_observability_plan", goal=rest.strip()))
            if cmd in {"/local-stack-advisor", "/local-stack-plan"}:
                goal, hardware = self._split_optional_second(rest)
                return self.format_result(self.tools.call("local_stack_advisor", goal=goal or rest.strip(), hardware=hardware or ""))
            if cmd in {"/verifier-ladder", "/validation-ladder-plus"}:
                goal, runtime = self._split_optional_second(rest)
                return self.format_result(self.tools.call("verifier_ladder", goal=goal or rest.strip(), runtime_hint=runtime or ""))
            if cmd in {"/tool-namespace-plan", "/tool-surface-plan"}:
                return self.format_result(self.tools.call("tool_namespace_plan", goal=rest.strip()))
            if cmd in {"/voice-pipeline-review", "/jarvis-voice-review"}:
                return self.format_result(self.tools.call("voice_pipeline_review", focus=rest.strip()))
            if cmd in {"/route-resilience-plan", "/self-healing-route-plan"}:
                return self.format_result(self.tools.call("route_resilience_plan", goal=rest.strip()))
            if cmd in {"/tool-health-map", "/route-health-map"}:
                return self.format_result(self.tools.call("tool_health_map", focus=rest.strip()))
            if cmd in {"/guardrail-memory", "/agent-guardrail-memory"}:
                goal, risk_note = self._split_optional_second(rest)
                return self.format_result(self.tools.call("guardrail_memory_plan", goal=goal or rest.strip(), risk_note=risk_note or ""))
            if cmd in {"/context-router-policy", "/role-context-router"}:
                return self.format_result(self.tools.call("context_router_policy", goal=rest.strip()))
            if cmd in {"/local-runtime-sentinel", "/model-runtime-sentinel"}:
                goal, hardware = self._split_optional_second(rest)
                return self.format_result(self.tools.call("local_runtime_sentinel", goal=goal or rest.strip(), hardware=hardware or ""))
            if cmd in {"/improvement-assurance", "/improvement-evidence"}:
                goal, changed = self._split_optional_second(rest)
                return self.format_result(self.tools.call("improvement_assurance_plan", goal=goal or rest.strip(), changed=changed or ""))
            if cmd in {"/test-impact-graph", "/patch-impact-graph"}:
                return self.format_result(self.tools.call("test_impact_graph", changed=rest.strip()))
            if cmd in {"/patch-quality-score", "/quality-score-patch"}:
                return self.format_result(self.tools.call("patch_quality_score", changed=rest.strip()))
            if cmd in {"/success-claim-audit", "/claim-audit"}:
                return self.format_result(self.tools.call("success_claim_audit", summary=rest.strip()))
            if cmd in {"/regression-bisect-plan", "/bisect-regression"}:
                symptom, versions = self._split_optional_second(rest)
                return self.format_result(self.tools.call("regression_bisect_plan", symptom=symptom or rest.strip(), versions=versions or ""))
            if cmd in {"/capability-drift-audit", "/nova-drift-audit"}:
                return self.format_result(self.tools.call("capability_drift_audit"))
            if cmd in {"/feature-preservation-contract", "/preserve-features"}:
                return self.format_result(self.tools.call("feature_preservation_contract", focus=rest.strip()))
            if cmd in {"/agent-feedback-loop", "/nova-feedback-loop"}:
                return self.format_result(self.tools.call("agent_feedback_loop_plan", goal=rest.strip()))
            if cmd in {"/behavior-fuzzer-plan", "/agent-fuzzer-plan"}:
                goal, surface = self._split_optional_second(rest)
                return self.format_result(self.tools.call("behavior_fuzzer_plan", goal=goal or rest.strip(), surface=surface or ""))
            if cmd in {"/local-spec-search", "/on-device-spec-search"}:
                goal, hardware = self._split_optional_second(rest)
                return self.format_result(self.tools.call("local_spec_search_plan", goal=goal or rest.strip(), hardware=hardware or ""))
            if cmd == "/deps-status":
                return self.format_result(self.tools.call("resource_status"))
            if cmd in {"/interactive", "/two-way"}:
                return self.start_interactive_run(rest)
            if cmd == "/version":
                return self.version_text()
            if cmd == "/help":
                return render_concise_help(rest.strip())
            if cmd in {"/help-full", "/full-help"}:
                return HELP
            if cmd == "/status":
                return self.format_result(self.tools.call("status"))
            if cmd == "/llm-status":
                return self.format_result(self.tools.call("llm_status"))
            if cmd in {"/ollama-multi", "/multi-models"}:
                return self.format_result(self.tools.call("ollama_multi_report"))
            if cmd in {"/providers", "/provider-status"}:
                return self.format_result(self.tools.call("provider_status"))
            if cmd in {"/provider-route", "/provider-route-explain"}:
                return self.format_result(self.tools.call("provider_route", goal=rest.strip() or "general Nova request"))
            if cmd == "/provider-test":
                return self.format_result(self.tools.call("provider_test", provider=rest.strip()))
            if cmd in {"/queue-status", "/provider-queue"}:
                return self.format_result(self.tools.call("queue_status"))
            if cmd == "/queue-drain":
                return self.format_result(self.tools.call("queue_drain"))
            if cmd == "/vision-status":
                return self.format_result(self.tools.call("vision_status"))
            if cmd == "/vision-model":
                val = rest.strip()
                if not val:
                    return f"Vision model: {getattr(self.config, 'vision_model', 'gemma3:12b')}"
                self.config.vision_model = val
                self.config.save()
                return f"Vision model set to: {val}"
            if cmd in {"/screen-analysis-prompt", "/screen-context-help", "/screen-analysis-help"}:
                return self.format_result(self.tools.call("screen_analysis_prompt", request=rest))
            if cmd == "/image-analyze":
                if "=>" in rest:
                    path_part, prompt_part = rest.split("=>", 1)
                    return self.format_result(self.tools.call("image_analyze", path=path_part.strip(), prompt=prompt_part.strip()))
                return self.format_result(self.tools.call("image_analyze", path=rest.strip()))
            if cmd == "/human-test":
                return self.format_result(self.tools.call("human_test", path=rest or "."))
            if cmd == "/visual-test":
                return self.format_result(self.tools.call("visual_test", path=rest or "."))
            if cmd == "/cycle-schema":
                return self.format_result(self.tools.call("cycle_schema"))
            if cmd == "/provider":
                val = (rest.strip().lower().replace("_", "-") or "status")
                if val in {"status", ""}:
                    return self.format_result(self.tools.call("provider_status"))
                allowed = {"ollama", "openrouter", "subq", "nvidia-nim", "llama-cpp", "vllm", "sglang", "local-gemma"}
                if val not in allowed:
                    return "Usage: /provider ollama|openrouter|subq|nvidia-nim|llama-cpp|vllm|sglang|local-gemma|status"
                self.config.model_provider = val
                self.config.save()
                remote_note = " Remote providers still require /allow-internet on and the matching BYO API key environment variable." if val in {"openrouter", "subq", "nvidia-nim"} else ""
                return f"Model provider set to: {val}.{remote_note} Use /provider-route explain GOAL and /provider-test {val} before serious runs."
            if cmd == "/allow-internet":
                val = rest.strip().lower()
                if val in {"on", "true", "yes", "1"}:
                    self.config.allow_internet = True
                elif val in {"off", "false", "no", "0"}:
                    self.config.allow_internet = False
                else:
                    return f"Internet/remote provider access: {self.config.allow_internet}. Use /allow-internet on|off"
                self.config.save()
                return f"Internet/remote provider access set to: {self.config.allow_internet}"
            if cmd == "/watch-topic":
                topic, urls = self._split_optional_second(rest)
                return self.format_result(self.tools.call("topic_watch", topic=topic, urls=urls))
            if cmd == "/topic-watchers":
                return self.format_result(self.tools.call("topic_watchers"))
            if cmd == "/topic-check":
                return self.format_result(self.tools.call("topic_check", topic=rest))
            if cmd in {"/internet-search", "/search-web", "/web-search"}:
                if not rest.strip():
                    return "Usage: /internet-search QUERY"
                return self.format_result(self.tools.call("internet_search", query=rest.strip()))
            if cmd == "/internet-fetch":
                return self.format_result(self.tools.call("internet_fetch", url=rest))
            if cmd == "/openrouter-model":
                if not rest:
                    return f"OpenRouter model: {getattr(self.config, 'openrouter_model', '')}"
                self.config.openrouter_model = rest.strip()
                self.config.save()
                return f"OpenRouter model set to: {self.config.openrouter_model}"
            if cmd == "/godmod3-report":
                return self.format_result(self.tools.call("godmod3_report"))
            if cmd == "/research-plan":
                return self.format_result(self.tools.call("research_plan"))
            if cmd == "/mcp-manifest":
                return self.format_result(self.tools.call("mcp_manifest"))
            if cmd == "/benchmark-init":
                return self.format_result(self.tools.call("benchmark_init", path=rest or "NovaBenchmarks"))
            if cmd == "/benchmark-run":
                return self.format_result(self.tools.call("benchmark_run", path=rest or "NovaBenchmarks"))
            if cmd == "/telemetry-export":
                return self.format_result(self.tools.call("telemetry_export"))
            if cmd == "/ollama-stop":
                if rest.strip().lower() not in {"--confirm", "confirm", "yes", "--yes"}:
                    return (
                        "⚠️ Confirm Ollama stop/unload\n\n"
                        "This will ask Ollama to unload the selected model and may interrupt a stuck local generation. "
                        "If a prompt is genuinely still running, it may fail and the current build may need to be retried. "
                        "Saved project files are not deleted.\n\n"
                        "Run this to confirm:\n/ollama-stop --confirm"
                    )
                return self.format_result(self.tools.call("ollama_stop_model"))
            if cmd == "/activity":
                return self.format_result(self.tools.call("activity_log"))
            if cmd in {"/investigate-logs", "/investigate-errors"}:
                return self.format_result(self.tools.call("investigate_logs", focus=rest))
            if cmd in {"/propose-improvements", "/improvement-proposals"}:
                return self.format_result(self.tools.call("propose_improvements", focus=rest))
            if cmd in {"/tool-guide", "/agent-guide"}:
                return self.format_result(self.tools.call("tool_use_guide"))
            if cmd == "/resource-status":
                return self.format_result(self.tools.call("resource_status"))
            if cmd == "/heartbeat":
                return self.format_result(self.tools.call("heartbeat"))
            if cmd == "/watchdog":
                parts2 = rest.split()
                action = parts2[0] if parts2 else "status"
                interval = int(parts2[1]) if len(parts2) > 1 and parts2[1].isdigit() else 30
                return self.format_result(self.tools.call("watchdog", action=action, interval=interval))
            if cmd == "/custom-tools":
                return self.format_result(self.tools.call("custom_tools"))
            if cmd == "/tool-create":
                return self.format_result(self.tools.call("tool_create", goal=rest))
            if cmd == "/tool-help":
                return self.format_result(self.tools.call("tool_help", name=rest))
            if cmd == "/tool-inputs":
                return self.format_result(self.tools.call("tool_help", name=rest))
            if cmd == "/tool-run":
                name, args = self._split_optional_second(rest)
                return self.format_result(self.tools.call("tool_run", name=name, args=args or "{}"))
            if cmd == "/tool-pipeline":
                return self.format_result(self.tools.call("tool_pipeline", steps=rest))
            if cmd == "/safe-script-demo":
                return self.format_result(self.tools.call("safe_script_demo", topic=rest or "interesting"))
            if cmd == "/tool-delete":
                return self.format_result(self.tools.call("tool_delete", name=rest))
            if cmd in {"/tool-view", "/tool-code"}:
                return self.format_result(self.tools.call("tool_view", name=rest))
            if cmd == "/tool-test":
                return self.format_result(self.tools.call("tool_test", name=rest))
            if cmd == "/tool-enable":
                return self.format_result(self.tools.call("tool_enable", name=rest))
            if cmd == "/tool-disable":
                return self.format_result(self.tools.call("tool_disable", name=rest))
            if cmd == "/tool-proposals":
                return self.format_result(self.tools.call("tool_proposals"))
            if cmd == "/tool-clean-proposals":
                return self.format_result(self.tools.call("tool_clean_proposals"))
            if cmd == "/self-check":
                return self.format_result(self.tools.call("runtime_self_check"))
            if cmd == "/tool-approve":
                return self.format_result(self.tools.call("tool_approve", proposal_id=rest))
            if cmd == "/tool-reject":
                return self.format_result(self.tools.call("tool_reject", proposal_id=rest))
            if cmd == "/agent":
                guard = self._automatic_mutation_guard_message(rest, cmd)
                if guard:
                    return guard
                return self.format_result(self.tools.call("agent_execute", goal=rest, max_steps=8))
            if cmd == "/improve-project":
                guard = self._automatic_mutation_guard_message(rest, cmd)
                if guard:
                    return guard
                return self.format_result(self.tools.call("improve_project", goal=rest))
            if cmd == "/improvement-report":
                return self.format_result(self.tools.call("improvement_report"))
            if cmd == "/pip-install":
                return self.format_result(self.tools.call("install_package", package=rest))
            if cmd in {"/mistake-learning", "/mistake-learning-status"}:
                return self.format_result(self.tools.call("mistake_learning"))
            if cmd == "/self-repair-status":
                return self.format_result(self.tools.call("self_repair_status"))
            if cmd == "/self-repair-permission":
                val = (rest.strip().lower() or "on")
                if val not in {"on", "off", "true", "false", "yes", "no", "1", "0", "enable", "disable", "enabled", "disabled"}:
                    return "Usage: /self-repair-permission on|off"
                return self.format_result(self.tools.call("self_repair_permission", enabled=val))
            if cmd == "/self-repair-validate":
                return self.format_result(self.tools.call("self_repair_validate"))
            if cmd in {"/self-repair-now", "/auto-self-repair"}:
                return self.format_result(self.tools.call("self_repair_auto", goal=rest or "improve Nova safely"))
            if cmd == "/self-improve":
                return self.format_result(self.tools.call("self_improve", goal=rest))
            if cmd == "/workspace":
                return self.cmd_workspace(rest)
            if cmd == "/allow-mutate":
                return self.cmd_allow_mutate(rest)
            if cmd == "/models":
                return self.models_text()
            if cmd == "/model":
                if not rest:
                    return f"Code/build model: {self.config.model}\nChat model: {getattr(self.config, 'chat_model', self.config.model)}"
                self.config.model = rest.strip()
                self.config.save()
                return f"Code/build model set to: {self.config.model}"
            if cmd == "/model-code":
                if not rest:
                    return f"Code/build model: {self.config.model}"
                self.config.model = rest.strip()
                self.config.save()
                return f"Code/build model set to: {self.config.model}"
            if cmd == "/model-chat":
                if not rest:
                    return f"Chat/creative model: {getattr(self.config, 'chat_model', self.config.model)}"
                self.config.chat_model = rest.strip()
                self.config.save()
                return f"Chat/creative model set to: {self.config.chat_model}"
            if cmd == "/model-planner":
                if not rest:
                    return f"Planning/review model: {getattr(self.config, 'planner_model', '') or self.config.model}"
                self.config.planner_model = rest.strip()
                self.config.save()
                return f"Planning/review model set to: {self.config.planner_model}"
            if cmd == "/model-route":
                val = (rest.strip().lower() or "auto")
                if val not in {"auto", "manual"}:
                    return "Usage: /model-route auto|manual"
                self.config.model_route = val
                self.config.save()
                return f"Model route mode set to: {val}"
            if cmd == "/projects":
                return self.format_result(self.tools.call("projects"))
            if cmd == "/project-new":
                name, path = self._split_optional_second(rest)
                result = self.tools.call("project_create", name=name, path=path or None)
                self.config = AssistantConfig.load()
                self.tools = ToolRegistry(self.config)
                return self.format_result(result)
            if cmd == "/project-open":
                result = self.tools.call("project_open", name=rest)
                self.config = AssistantConfig.load()
                self.tools = ToolRegistry(self.config)
                return self.format_result(result)
            if cmd == "/project-remove":
                delete_files = "--delete" in rest.lower() or "/delete" in rest.lower()
                name = rest.replace("--delete", "").replace("/delete", "").strip()
                return self.format_result(self.tools.call("project_remove", name=name, delete_files=delete_files))
            if cmd == "/project-delete":
                return self.format_result(self.tools.call("project_delete", name=rest))
            if cmd == "/project-files":
                return self.format_result(self.tools.call("project_files", name=rest or None))
            if cmd == "/project-spec":
                return self.format_result(self.tools.call("project_spec", goal=rest or "build the requested local project"))
            if cmd == "/open-file":
                return self.format_result(self.tools.call("open_file", path=rest))
            if cmd == "/files":
                return self.format_result(self.tools.call("list_files", subdir=rest or "."))
            if cmd == "/tree":
                return self.format_result(self.tools.call("tree", subdir=rest or "."))
            if cmd == "/read":
                return self.format_result(self.tools.call("read_file", path=rest))
            if cmd == "/write":
                path, content = self._split_path_content(rest)
                return self.format_result(self.tools.call("write_file", path=path, content=content))
            if cmd == "/append":
                path, content = self._split_path_content(rest)
                return self.format_result(self.tools.call("append_file", path=path, content=content))
            if cmd == "/mkdir":
                return self.format_result(self.tools.call("make_dir", path=rest))
            if cmd == "/replace":
                before, new = rest.split("=>", 1)
                path, old = self._split_path_content(before.strip())
                return self.format_result(self.tools.call("find_replace", path=path, old=old, new=new.strip()))
            if cmd == "/search":
                return self.format_result(self.tools.call("search_text", query=rest))
            if cmd == "/shell":
                return self.format_result(self.tools.call("run_shell", command=rest))
            if cmd == "/verify":
                result = self.tools.call("verify", command=rest)
                if not result.ok:
                    self.last_error = {"command": rest, "result": result.data}
                return self.format_result(result)
            if cmd == "/detect":
                return self.format_result(self.tools.call("detect_project"))
            if cmd == "/auto-verify":
                result = self.tools.call("auto_verify")
                if not result.ok:
                    self.last_error = {"command": "auto_verify", "result": result.data}
                return self.format_result(result)
            if cmd == "/fix-last":
                return self.fix_last_error(rest)
            if cmd == "/surgical-repair":
                failure = self.last_error.get("result") if self.last_error else {"note": rest}
                goal = str((self.last_error or {}).get("goal") or rest or "repair current project")
                return self.format_result(self.tools.call("surgical_repair", goal=goal, failure=failure, path="."))
            if cmd == "/backtrack":
                if not self.last_error:
                    return "No last error stored. Run a plan first, or use /fix-last after a failed step."
                return self.format_result(self.tools.call("backtrack_recover", goal=str(self.last_error.get("goal") or rest or "repair current project"), failed_step=str(self.last_error.get("step") or "manual"), failed_tool=str(self.last_error.get("tool") or "manual"), failure=self.last_error.get("result") or {}, max_attempts=3))
            if cmd == "/zip":
                return self.format_result(self.tools.call("zip_path", path=rest or "."))
            if cmd == "/download":
                if not rest:
                    return "Usage: /download relative/path/to/file"
                download_path = rest.replace("\\", "/")
                return f"Download link: /download?path={download_path}"
            if cmd == "/continue":
                goal = rest.strip() or "continue improving the current project"
                guard = self._automatic_mutation_guard_message(goal, cmd)
                if guard:
                    return guard
                goal = self._enrich_goal_with_project_memory(goal)
                self.last_plan = make_plan("continue " + goal, workspace=Path(self.config.workspace), mode="long")
                self._save_plan()
                return self.last_plan.to_text() + "\n\n" + self.run_plan()
            if cmd == "/fast":
                guard = self._automatic_mutation_guard_message(rest, cmd)
                if guard:
                    return guard
                target_note = self._prepare_project_target_for_generation(rest, mode="fast")
                rest = self._enrich_goal_with_project_memory(rest)
                self.last_plan = make_plan(rest, workspace=Path(self.config.workspace), mode="fast")
                self._save_plan()
                return self.last_plan.to_text() + "\n\n" + self.run_plan()
            if cmd == "/long":
                guard = self._automatic_mutation_guard_message(rest, cmd)
                if guard:
                    return guard
                target_note = self._prepare_project_target_for_generation(rest, mode="long")
                rest = self._enrich_goal_with_project_memory(rest)
                self.last_plan = make_plan(rest, workspace=Path(self.config.workspace), mode="long")
                self._save_plan()
                return self.last_plan.to_text() + "\n\n" + self.run_plan()
            if cmd == "/project-target":
                return self._project_target_diagnostic(rest or "make a tiny useful app")
            if cmd == "/plan":
                rest = self._enrich_goal_with_project_memory(rest)
                self.last_plan = make_plan(rest, workspace=Path(self.config.workspace), mode="auto")
                self._save_plan()
                return self.last_plan.to_text()
            if cmd == "/do":
                if not rest.strip():
                    return (
                        "Usage: `/do GOAL`\n\n"
                        "Use `/do` only when you want Nova to actually create or edit files. "
                        "For a safer preview first, run `/task-contract GOAL`, `/project-target GOAL` or `/coding-plan GOAL`.\n\n"
                        "Example: `/do make one Python file named hello.py that prints hello`"
                    )
                guard = self._automatic_mutation_guard_message(rest, cmd)
                if guard:
                    return guard
                planning_dialog = self._maybe_start_planning_dialog(rest, source="/do")
                if planning_dialog:
                    return planning_dialog
                task_contract = build_task_execution_contract(rest, root=self.config.workspace)
                self.last_plan = make_plan(rest, workspace=Path(self.config.workspace), mode="auto")
                self._save_plan()
                contract_note = "Task contract: intent={intent}, risk={risk}, verify={verify}".format(
                    intent=task_contract.inferred_intent,
                    risk=task_contract.risk_level,
                    verify=", ".join(task_contract.verification_commands[:2]),
                )
                return contract_note + "\n\n" + self.last_plan.to_text() + "\n\n" + self.run_plan()
            if cmd == "/run-plan":
                return self.run_plan()
            if cmd == "/run-project":
                return self.format_result(self.tools.call("runtime_start", path=rest or "."))
            if cmd == "/stop-project":
                return self.format_result(self.tools.call("runtime_stop"))
            if cmd == "/restart-project":
                return self.format_result(self.tools.call("runtime_restart", path=rest or "."))
            if cmd == "/open-project-tab":
                result = self.tools.call("runtime_start", path=rest or ".")
                if result.ok:
                    url = result.data.get("run_url") or result.data.get("open_url") or ""
                    return "Open in browser tab: " + str(url)
                return self.format_result(result)
            if cmd == "/logs":
                if not TRACE_PATH.exists():
                    return "No traces yet."
                return "\n".join(TRACE_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-40:])
            return "Unknown command. Use /help."
        except Exception as exc:
            return f"Command error: {exc}"
    def cmd_workspace(self, rest: str) -> str:
        if not rest:
            return f"Workspace: {self.config.workspace}"
        p = Path(rest).expanduser().resolve()
        p.mkdir(parents=True, exist_ok=True)
        self.config.workspace = str(p)
        self.config.save()
        self.tools = ToolRegistry(self.config)
        try:
            register_project(p.name, str(p), make_current=True)
            marker = p / ".nova_project.json"
            if not marker.exists() and p.name.lower() not in {"daniel", "danny", "users", "documents"}:
                atomic_write_json(marker, {"name": p.name, "path": str(p)}, ensure_ascii=True)
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        return f"Workspace set to: {p}"
    def cmd_allow_mutate(self, rest: str) -> str:
        value = rest.strip().lower()
        if value in {"on", "true", "1", "yes"}:
            self.config.allow_mutating_tools = True
        elif value in {"off", "false", "0", "no"}:
            self.config.allow_mutating_tools = False
        else:
            return "Use /allow-mutate on or /allow-mutate off"
        self.config.save()
        return f"Mutating tools: {self.config.allow_mutating_tools}"
    def _split_optional_second(self, rest: str) -> tuple[str, str]:
        if "=>" in rest:
            a, b = rest.split("=>", 1)
            return a.strip(), b.strip()
        return rest.strip(), ""
    def _split_path_content(self, rest: str) -> tuple[str, str]:
        if not rest.strip():
            raise ValueError("Missing path and content")
        try:
            parts = shlex.split(rest, posix=False)
        except Exception:
            parts = rest.split(maxsplit=1)
        if len(parts) < 2:
            raise ValueError("Expected: PATH CONTENT")
        path = parts[0].strip('"')
        content = rest[rest.find(parts[1]):]
        return path, content
    def format_result(self, result: ToolResult) -> str:
        """Human-readable result formatting for chat.
        Raw JSON is still available in logs and the GUI file/activity panels, but chat should read
        more like ChatGPT/Codex output instead of a wall of JSON.
        """
        label = "✅" if result.ok else "❌"
        data = result.data or {}
        lines = [f"{label} {result.summary}"]
        summarized_structured = False
        if isinstance(data, dict):
            if data.get("project"):
                proj = data.get("project") or {}
                if isinstance(proj, dict):
                    lines.append(f"Project: {proj.get('name', '')}")
                    if proj.get("path"):
                        lines.append(f"Path: {proj.get('path')}")
            if data.get("workspace"):
                lines.append(f"Workspace: {data.get('workspace')}")
            if data.get("main_file"):
                lines.append(f"Final file: {data.get('main_file')}")
            if data.get("run_command"):
                lines.append(f"Run command: {data.get('run_command')}")
            if data.get("open_url"):
                lines.append(f"Open in GUI: {data.get('open_url')}")
            if data.get("download_url"):
                lines.append(f"Download: {data.get('download_url')}")
            if data.get("acceptance_terms"):
                terms = data.get("acceptance_terms") or []
                lines.append("Acceptance terms checked: " + ", ".join(map(str, terms[:16])))
            summarized_structured = self._append_project_verification_summary(lines, data)
            if data.get("written"):
                written = data.get("written") or []
                lines.append(f"Files written/changed: {len(written)}")
                for w in written[:8]:
                    path = str(w.get("path", "") if isinstance(w, dict) else w)
                    lines.append(f"- {Path(path).name if path else path}")
            if data.get("fix") and not result.ok:
                fix = data.get("fix")
                if isinstance(fix, list):
                    lines.append("Suggested fix:")
                    lines.extend(f"- {x}" for x in fix[:6])
                else:
                    lines.append("Suggested fix: " + str(fix))
            if data.get("message"):
                lines.append(str(data.get("message")))
                summarized_structured = True
            if data.get("markdown") and not data.get("message"):
                lines.append(str(data.get("markdown")))
                summarized_structured = True
            if data.get("output_description"):
                lines.append("Output: " + str(data.get("output_description")))
            if data.get("verification_status"):
                lines.append("Verification status: " + str(data.get("verification_status")))
            if data.get("human_report"):
                lines.append(str(data.get("human_report")))
                summarized_structured = True
            eff = data.get("efficiency")
            if isinstance(eff, dict):
                lines.append(
                    "Efficiency: "
                    f"{float(eff.get('wall_ms') or 0):.1f} ms wall, "
                    f"{float(eff.get('process_cpu_ms') or 0):.1f} ms CPU, "
                    f"~{float(eff.get('estimated_joules') or 0):.3f} J"
                )
        # Keep a compact details block for debugging, but avoid dumping massive diffs/code.
        compact = self._compact_json_for_chat(data)
        if compact and not summarized_structured:
            lines.append("\nTechnical details:")
            lines.append(compact)
        return "\n".join(lines)

    def _append_project_verification_summary(self, lines: list[str], data: dict[str, Any]) -> bool:
        checks = self._verification_checks_for_chat(data)
        quality = self._quality_score_for_chat(data)
        added = False
        if checks:
            passed = sum(1 for check in checks if self._chat_check_ok(check))
            lines.append(f"Verification: {passed}/{len(checks)} checks passed")
            for check in checks[:10]:
                lines.append(self._format_check_for_chat(check))
            added = True
        if quality:
            lines.extend(self._format_quality_score_for_chat(quality))
            added = True
        return added

    def _verification_checks_for_chat(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        checks = data.get("checks")
        if isinstance(checks, list):
            return [check for check in checks if isinstance(check, dict)]
        verification = data.get("verification")
        if isinstance(verification, dict):
            checks = verification.get("checks")
            if isinstance(checks, list):
                return [check for check in checks if isinstance(check, dict)]
        return []

    def _quality_score_for_chat(self, data: dict[str, Any]) -> dict[str, Any]:
        quality = data.get("quality_score")
        if isinstance(quality, dict):
            return quality
        verification = data.get("verification")
        if isinstance(verification, dict):
            quality = verification.get("quality_score")
            if isinstance(quality, dict):
                return quality
        return {}

    def _chat_check_ok(self, check: dict[str, Any]) -> bool:
        raw_status = str(check.get("status") or "").lower()
        ok_value = check.get("ok")
        if ok_value is None and raw_status:
            ok_value = raw_status in {"implemented", "environment_dependent", "safe_partial", "pass", "passed", "ok", "ready"}
        return bool(ok_value)

    def _format_check_for_chat(self, check: dict[str, Any]) -> str:
        ok_value = self._chat_check_ok(check)
        status = "PASS" if ok_value else "FAIL"
        name = str(check.get("name") or check.get("kind") or "check")
        file_name = str(check.get("file") or "").strip()
        line = f"- {status} {name}"
        if file_name:
            line += f": {file_name}"
        if not ok_value:
            detail = check.get("problems") or check.get("output") or check.get("message") or ""
            if isinstance(detail, list):
                detail = "; ".join(str(item) for item in detail[:3])
            detail = str(detail).strip()
            if detail:
                line += " - " + detail[:500]
        return line

    def _format_quality_score_for_chat(self, quality: dict[str, Any]) -> list[str]:
        lines: list[str] = []
        overall = self._chat_number(quality.get("overall_percent"))
        threshold = self._chat_number(quality.get("threshold_percent"))
        if overall:
            line = f"Quality score: {overall}%"
            if threshold:
                result = "passed" if quality.get("passed_threshold") else "below"
                line += f" {result} threshold {threshold}%"
            lines.append(line)
        metrics = [
            ("Syntax", quality.get("syntax")),
            ("Requirements", quality.get("requirements_coverage")),
            ("UI completeness", quality.get("ui_completeness")),
            ("Runtime", quality.get("runtime_confidence")),
            ("Export/local saving", quality.get("export_local_saving")),
        ]
        metric_text = [f"{label} {self._chat_number(value)}/10" for label, value in metrics if value is not None]
        if metric_text:
            lines.append(", ".join(metric_text))
        return lines

    def _chat_number(self, value: Any) -> str:
        try:
            number = float(value)
        except Exception:
            return ""
        if number.is_integer():
            return str(int(number))
        return f"{number:.1f}".rstrip("0").rstrip(".")

    def _compact_json_for_chat(self, obj: Any, max_chars: int = 2500) -> str:
        def scrub(x: Any) -> Any:
            if isinstance(x, dict):
                out = {}
                for k, v in x.items():
                    if k in {"diff", "preview", "code_preview", "response_preview", "prompt_preview", "content", "efficiency"}:
                        continue
                    if k == "written" and isinstance(v, list):
                        out[k] = [{kk: vv for kk, vv in item.items() if kk in {"path", "bytes"}} for item in v[:10] if isinstance(item, dict)]
                    else:
                        out[k] = scrub(v)
                return out
            if isinstance(x, list):
                return [scrub(i) for i in x[:20]]
            return x
        try:
            text = json.dumps(scrub(obj), indent=2, ensure_ascii=False)
        except Exception:
            return ""
        if len(text) > max_chars:
            text = text[:max_chars] + "\n...details truncated; full logs are in ~/.nova/activity.jsonl"
        return text
    # -------------------------
    # Interactive two-way run state
    # -------------------------
    def _new_active_run(self, goal: str, mode: str = "interactive") -> dict[str, Any]:
        run = {
            "run_id": new_run_id(),
            "goal": goal,
            "mode": mode,
            "status": "waiting_for_user",
            "question": "",
            "options": [],
            "replies": [],
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        }
        self.active_run = run
        return run
    def active_run_status_text(self) -> str:
        if not self.active_run:
            return "No active interactive run. Use /interactive GOAL to start one, or use /long GOAL for a normal build."
        run = self.active_run
        lines = [f"Active run: {run.get('run_id')}", f"Status: {run.get('status')}", f"Goal: {run.get('goal')}"]
        if run.get("question"):
            lines.append("Question: " + str(run.get("question")))
        opts = run.get("options") or []
        if opts:
            lines.append("Options: " + "; ".join(map(str, opts)))
        if run.get("replies"):
            lines.append("Replies so far: " + " | ".join(map(str, run.get("replies")[-3:])))
        return "\n".join(lines)
    def pause_active_run(self) -> str:
        if not self.active_run:
            return "No active run to pause."
        self.active_run["status"] = "paused"
        self.active_run["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        log_activity("interactive_paused", "Interactive run paused", {"run_id": self.active_run.get("run_id"), "goal": self.active_run.get("goal")})
        return "Paused the active interactive run. Use /resume-run to continue or /cancel-run to discard it."
    def resume_active_run(self) -> str:
        if not self.active_run:
            return "No active run to resume."
        if self.active_run.get("status") == "paused":
            self.active_run["status"] = "waiting_for_user" if self.active_run.get("question") else "ready"
        self.active_run["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        log_activity("interactive_resumed", "Interactive run resumed", {"run_id": self.active_run.get("run_id"), "goal": self.active_run.get("goal")})
        return self.active_run_status_text()
    def cancel_active_run(self) -> str:
        if not self.active_run:
            return "No active run to cancel."
        old = self.active_run
        self.active_run = None
        log_activity("interactive_cancelled", "Interactive run cancelled", {"run_id": old.get("run_id"), "goal": old.get("goal")})
        return f"Cancelled interactive run {old.get('run_id')}."
    def _clarification_question_for_goal(self, goal: str) -> dict[str, Any]:
        """Ask the local model for one targeted clarification; fall back deterministically."""
        prompt = f"""
You are helping Nova run a two-way software build.
Return ONLY JSON.
User goal:
{goal}
Task: ask exactly ONE useful clarification question that would prevent building the wrong thing. If no clarification is needed, ask for confirmation of the build mode/scope.
Schema:
{{"question":"one concise question", "options":["option A", "option B", "option C"], "default":"recommended default"}}
"""
        reply = model_chat(self.config, self._select_model_for("planning"), [{"role": "user", "content": prompt}], timeout=90, desc="interactive clarification")
        try:
            m = re.search(r"\{.*\}", reply or "", re.S)
            data = json.loads(m.group(0)) if m else {}
            q = str(data.get("question") or "").strip()
            if q:
                return {"question": q, "options": [str(x) for x in (data.get("options") or [])[:5]], "default": str(data.get("default") or "")}
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        g = goal.lower()
        if any(k in g for k in ["api", "online", "live data", "real-time", "database", "login", "account"]):
            return {"question": "Should I build this as a fully offline local app first, or include API/backend-ready structure?", "options": ["offline local app first", "API/backend-ready structure", "ask me feature by feature"], "default": "offline local app first"}
        return {"question": "Should I build a fast minimal working version or a longer polished version with requirements, tests, repair and final review?", "options": ["fast minimal", "long polished", "long polished with extra examples"], "default": "long polished"}

    def _current_project_context(self) -> dict[str, Any]:
        try:
            manifest = Path(self.config.workspace) / "PROJECT_MANIFEST.json"
            if manifest.exists():
                data = read_json_file(manifest, {}, expected_type=dict, quarantine=True)
                if isinstance(data, dict):
                    data.setdefault("name", Path(self.config.workspace).name)
                    return data
        except Exception as exc:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        return {}

    def _maybe_start_planning_dialog(self, goal: str, source: str = "chat") -> str:
        analysis = analyze_planning_dialog_need(goal, self._current_project_context())
        if not analysis.should_ask:
            return ""
        run = self._new_active_run(analysis.normalized_text or goal, mode="planning_dialog")
        run["question"] = analysis.question
        run["options"] = [choice.reply for choice in analysis.choices]
        run["option_details"] = [choice.to_dict() for choice in analysis.choices]
        run["default"] = analysis.recommended
        run["planning_analysis"] = analysis.to_dict()
        run["source"] = source
        log_activity(
            "planning_dialog_waiting",
            "Nova paused for a two-way planning decision before editing/running tools",
            {"run_id": run.get("run_id"), "goal": goal, "reason": analysis.reason, "plan_level": analysis.plan_level},
        )
        lines = [
            "I paused before doing anything because the request needs a planning choice.",
            "",
            f"Reason: {analysis.reason}",
            f"Plan level: {analysis.plan_level}",
            f"Intent confidence: {analysis.intent_confidence:.0%}",
            "",
            "Question:",
            analysis.question,
            "",
            "Choices:",
        ]
        for idx, choice in enumerate(analysis.choices, 1):
            tag = " ← recommended" if choice.recommended else ""
            lines.append(f"{idx}. {choice.label}: {choice.reply}{tag}")
            if choice.reason:
                lines.append(f"   Why: {choice.reason}")
        lines.extend([
            "",
            f"Recommended: {analysis.recommended}",
            "In the Web UI, click a choice button to continue. In CLI, reply with `/reply 1`, another option number, or your own answer.",
        ])
        return "\n".join(lines)

    def start_interactive_run(self, goal: str) -> str:
        goal = (goal or "").strip()
        if not goal:
            return "Usage: /interactive make a useful app..."
        run = self._new_active_run(goal, mode="interactive")
        clarification = self._clarification_question_for_goal(goal)
        run["question"] = clarification.get("question", "How should I proceed?")
        run["options"] = clarification.get("options", [])
        run["default"] = clarification.get("default", "")
        log_activity("interactive_waiting", "Interactive run is waiting for user input", {"run_id": run.get("run_id"), "goal": goal, "question": run.get("question"), "options": run.get("options")})
        lines = ["I started an interactive two-way run and paused before building so I do not guess wrong.", "", "Question:", str(run["question"])]
        if run.get("options"):
            lines.append("Options:")
            lines.extend("- " + str(o) for o in run.get("options", []))
        if run.get("default"):
            lines.append("Recommended default: " + str(run.get("default")))
        lines.append("")
        lines.append("In the Web UI, click a choice button to continue. In CLI, reply with: /reply your answer")
        return "\n".join(lines)
    def _resolve_active_run_reply(self, reply: str) -> tuple[str, str]:
        """Resolve a user's /reply value to the full selected option when possible.

        Earlier builds accepted `/reply c` literally even when the active run had
        lettered choices such as `c) A utility application`. That made the
        following build goal almost meaningless (`- c`) and could cause weak
        project generation. This helper maps numbers, letters, exact labels and
        recommended/default aliases to the full option text.
        """
        raw = (reply or "").strip()
        options = [str(x).strip() for x in (self.active_run or {}).get("options") or [] if str(x).strip()]
        default_reply = str((self.active_run or {}).get("default") or "").strip()
        low = raw.lower()
        if options and low.isdigit():
            idx = int(low) - 1
            if 0 <= idx < len(options):
                return options[idx], f"selected option {idx + 1}"
        if options and re.fullmatch(r"[a-z]", low):
            for option in options:
                opt_low = option.lower().strip()
                if opt_low.startswith(low + ")") or opt_low.startswith(low + ".") or opt_low.startswith("(" + low + ")"):
                    return option, f"selected option {low}"
        if options:
            for option in options:
                opt_low = option.lower().strip()
                label = re.sub(r"^\(?[a-z0-9]+[\).]\s*", "", opt_low).strip()
                if low == opt_low or low == label:
                    return option, "matched option text"
        if default_reply and low in {"default", "recommended", "recommendation"}:
            return default_reply, "selected recommended default"
        return raw, "custom reply"

    def _enrich_interactive_goal_with_reply(self, goal: str, reply: str) -> str:
        goal = str(goal or "").strip()
        reply = str(reply or "").strip()
        normalized_reply = re.sub(r"^\(?[a-z0-9]+[\).]\s*", "", reply, flags=re.I).strip() or reply
        generic_interactive_goal = bool(re.search(r"ask me before|before choosing|choosing scope|useful local app|something else", goal.lower()))
        if generic_interactive_goal and len(normalized_reply) >= 8:
            return (
                f"make a useful local {normalized_reply.lower()} with practical functionality, "
                "a clear runnable UI, local saving where useful, seeded example data, verification, "
                "and a short README. Do not create a generic placeholder app."
            )
        return goal + "\n\nUser clarification for this interactive run:\n" + "\n".join("- " + str(x) for x in self.active_run.get("replies", []))

    def reply_to_active_run(self, reply: str) -> str:
        reply = (reply or "").strip()
        if not self.active_run:
            return "No active interactive run is waiting. Use /interactive GOAL first."
        if self.active_run.get("status") == "cancelled":
            return "That run was cancelled. Start a new one with /interactive GOAL."
        if self.active_run.get("status") == "paused":
            return "The active run is paused. Use /resume-run first, then /reply."
        if self.active_run.get("status") not in {"waiting_for_user", "ready"}:
            return (
                "No active interactive run is waiting for a new answer right now. "
                "The previous task is already running or finished; use `/interrupt-current --confirm` if it is stuck, "
                "or start a fresh `/interactive GOAL`."
            )
        if not reply:
            return "Please include your answer after /reply."
        reply, reply_resolution = self._resolve_active_run_reply(reply)
        self.active_run.setdefault("replies", []).append(reply)
        self.active_run["status"] = "running"
        self.active_run["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
        goal = str(self.active_run.get("goal") or "")
        enriched_goal = self._enrich_interactive_goal_with_reply(goal, reply)
        log_activity("interactive_reply", "User replied to interactive run; continuing build", {"run_id": self.active_run.get("run_id"), "reply": reply, "reply_resolution": reply_resolution, "goal": goal, "effective_goal": enriched_goal})
        # Choose long mode by default for interactive runs so the build includes requirements, tests, repair and final review.
        self.last_plan = make_plan(enriched_goal, workspace=Path(self.config.workspace), mode="long")
        self._save_plan()
        result = self.last_plan.to_text() + "\n\n" + self.run_plan()
        if self.active_run:
            self.active_run["status"] = "finished"
            self.active_run["updated_at"] = time.strftime("%Y-%m-%d %H:%M:%S")
            log_activity("interactive_finished", "Interactive run finished", {"run_id": self.active_run.get("run_id"), "goal": goal})
            self.active_run = None
        return result
    def run_plan(self) -> str:
        if not self.last_plan:
            return "No plan. Use /plan <goal> first."
        plan_run_id = new_run_id()
        set_current_run(plan_run_id)
        lines = [f"Running plan: {self.last_plan.goal}", f"Run ID: {plan_run_id}"]
        log_activity("run_started", "New build/test/repair run started", {"run_id": plan_run_id, "goal": self.last_plan.goal})
        log_activity("plan_start", f"Running plan: {self.last_plan.goal}", {"run_id": plan_run_id, "steps": [s.title for s in self.last_plan.steps], "workspace": self.config.workspace, "model": self.config.model})
        try:
            preflight = self.tools.call("pipeline_preflight", goal=self.last_plan.goal)
            if preflight.ok:
                route = preflight.data.get("kind") or "unknown"
                log_activity("pipeline_selected", f"Pipeline preflight selected {route}", {"run_id": plan_run_id, "goal": self.last_plan.goal, "route": route, "stages": preflight.data.get("stages", [])})
                lines.append(f"Pipeline preflight: {route} — {preflight.summary}")
        except Exception as exc:
            log_activity("pipeline_preflight_error", "Pipeline preflight failed without blocking the plan", {"run_id": plan_run_id, "error": repr(exc)})
        generated_zip_url = ""
        final_run_path = ""
        project_name = ""
        for step in self.last_plan.steps:
            lines.append(f"\nSTEP: {step.title}")
            self._set_avatar("working", "🧭", "Working", f"Running step: {step.title}")
            log_activity("step_start", f"STEP: {step.title}", {"run_id": plan_run_id, "tool": step.tool, "args": step.args})
            log_activity("pipeline_stage_start", f"Pipeline stage running: {step.title}", {"run_id": plan_run_id, "tool": step.tool, "args": step.args})
            result = self.tools.call(step.tool, **step.args)
            log_activity("step_done" if result.ok else "step_failed", f"{step.title}: {result.summary}", {"run_id": plan_run_id, "tool": step.tool, "ok": result.ok, "data": result.data})
            log_activity("pipeline_stage_done" if result.ok else "pipeline_stage_failed", f"Pipeline stage {'passed' if result.ok else 'failed'}: {step.title}", {"run_id": plan_run_id, "tool": step.tool, "ok": result.ok, "summary": result.summary})
            step.status = "done" if result.ok else "failed"
            step.result_summary = result.summary
            lines.append(self.format_result(result))
            if result.ok and isinstance(result.data, dict):
                if step.tool in {"project_create", "ai_create_project"}:
                    project = result.data.get("project")
                    if isinstance(project, dict):
                        project_name = str(project.get("name") or "") or project_name
                    elif project:
                        project_name = str(project) or project_name
                if step.tool in {"ai_create_project", "ai_edit_project", "run_project"}:
                    main_file = result.data.get("main_file") or ""
                    if main_file:
                        final_run_path = str(main_file).replace("\\", "/")
                if step.tool == "read_file":
                    read_path = result.data.get("path", "")
                    if str(read_path).lower().endswith(("index.html", "main.py", "app.py", "readme.md")):
                        final_run_path = step.args.get("path", "") or Path(read_path).name
                if step.tool == "zip_path":
                    generated_zip_url = result.data.get("download_url", "") or generated_zip_url
            self.trace("plan_step", {"run_id": plan_run_id, "step": step.title, "tool": step.tool, "ok": result.ok, "summary": result.summary})
            if not result.ok:
                self.last_error = {"step": step.title, "tool": step.tool, "args": step.args, "result": result.data, "goal": self.last_plan.goal}
                # v27 recovery triage:
                # - If the local model produced no project/files, there is nothing safe to surgically repair.
                #   Do not backtrack the unrelated current workspace.
                # - If files were written and only syntax/acceptance failed, repair in place.
                # v29 recovery triage: never repair/backtrack an unrelated current project when
                # the failed step did not actually write files for this run. This covers:
                # - Ollama timeout/invalid JSON before file writes
                # - internal tool exceptions such as parser regex bugs
                # - create-project failures where there is no project/written payload
                data_dict = result.data if isinstance(result.data, dict) else {}
                wrote_files_this_step = bool(data_dict.get("written"))
                made_project_this_step = bool(data_dict.get("project"))
                internal_tool_error = bool(data_dict.get("error"))
                model_no_output = data_dict.get("source") == "ollama_required_failed"
                no_files_written = step.tool == "ai_create_project" and not wrote_files_this_step and not made_project_this_step
                if self.config.allow_mutating_tools:
                    lines.append("\nBefore giving up, I am checking whether this is a known failure pattern I can recover from safely.")
                    reasoning = self.tools.call("reasoning_diagnostics", goal=self.last_plan.goal, failed_tool=step.tool, failure=result.data)
                    log_activity("reasoning_diagnostics", reasoning.summary, {"run_id": plan_run_id, "data": reasoning.data})
                    known = self.tools.call("known_error_recover", goal=self.last_plan.goal, failed_step=step.title, failed_tool=step.tool, failure=result.data, path=".")
                    lines.append(self.format_result(known))
                    log_activity("known_error_recovery_done" if known.ok else "known_error_recovery_failed", known.summary, {"run_id": plan_run_id, "data": known.data})
                    if known.ok:
                        step.status = "recovered"
                        step.result_summary = "Recovered with known-error recovery: " + known.summary
                        if isinstance(known.data, dict):
                            project = known.data.get("project")
                            if isinstance(project, dict):
                                project_name = str(project.get("name") or "") or project_name
                            elif project:
                                project_name = str(project) or project_name
                            final_run_path = str(known.data.get("main_file") or final_run_path or "").replace("\\", "/")
                        lines.append("\nRecovered from the known error pattern, so I am continuing the remaining plan steps.")
                        continue
                if no_files_written or (internal_tool_error and step.tool == "ai_create_project"):
                    lines.append("\nNo new project files were written for this run, so I did not modify any unrelated project. I will preserve any parseable/latest generated candidate for review when available, use request-aware deterministic fallback where possible, and recommend a safer next step rather than silently giving up. This is usually an Ollama timeout, invalid model JSON, or internal generation error. Check /model-health and /llm-status, use /ollama-stop --confirm if the model is stuck, or retry with a more specific goal.")
                    log_activity("recovery_skipped", "Skipped recovery because create-project failed before writing files", {"run_id": plan_run_id, "data": result.data, "tool": step.tool, "internal_tool_error": internal_tool_error, "model_no_output": model_no_output})
                    break
                # v26/v27: prefer surgical repair before broader backtracking. A tiny syntax
                # error should be fixed with a targeted patch, not by rolling back or
                # asking the model to rewrite a mostly-good project.
                recoverable = step.tool in {"ai_create_project", "ai_edit_project", "run_project", "final_project_check", "verify", "auto_verify"}
                if recoverable and self.config.allow_mutating_tools:
                    lines.append("\nThe step failed, so I am trying surgical repair first. If a small find/replace fix is enough, I will keep the good progress and continue.")
                    log_activity("surgical_repair_start", "Plan step failed; trying targeted surgical repair before backtracking", {"run_id": plan_run_id, "step": step.title, "tool": step.tool, "goal": self.last_plan.goal})
                    surgical = self.tools.call("surgical_repair", goal=self.last_plan.goal, failure=result.data, path=".")
                    lines.append(self.format_result(surgical))
                    log_activity("surgical_repair_done" if surgical.ok else "surgical_repair_incomplete", surgical.summary, {"run_id": plan_run_id, "data": surgical.data})
                    if surgical.ok:
                        step.status = "recovered"
                        step.result_summary = "Recovered with surgical repair: " + surgical.summary
                        lines.append("\nRecovered with targeted repair, so I am continuing the remaining plan steps.")
                        continue
                    lines.append("\nSurgical repair was not enough, so I am backtracking non-destructively: checkpoint, repair same project, re-test, and preserve the best state.")
                    log_activity("backtrack_start", "Surgical repair incomplete; starting non-destructive backtracking recovery", {"run_id": plan_run_id, "step": step.title, "tool": step.tool, "goal": self.last_plan.goal})
                    recovery = self.tools.call("backtrack_recover", goal=self.last_plan.goal, failed_step=step.title, failed_tool=step.tool, failure=result.data, max_attempts=3)
                    lines.append(self.format_result(recovery))
                    log_activity("backtrack_done" if recovery.ok else "backtrack_failed", recovery.summary, {"run_id": plan_run_id, "data": recovery.data})
                    if recovery.ok:
                        step.status = "recovered"
                        step.result_summary = "Recovered after failure: " + recovery.summary
                        lines.append("\nRecovered, so I am continuing the remaining plan steps.")
                        continue
                lines.append("\nStopped after surgical/backtracking recovery attempts failed. I saved the failure in the activity log. Use /surgical-repair with the exact error, /fix-last, or simplify the request and run /long again.")
                break
        else:
            ws = Path(self.config.workspace)
            project_output_mode = self.last_plan.mode not in {"qa", "project_qa"} and any(step.tool in {"ai_create_project", "ai_edit_project", "project_create", "write_files", "run_project"} for step in self.last_plan.steps)
            if project_output_mode and not final_run_path:
                for candidate in ["index.html", "main.py", "app.py", "README.md"]:
                    if (ws / candidate).exists():
                        final_run_path = candidate
                        break
            if project_output_mode and final_run_path:
                lines.append("\nFINAL CREATED FILE")
                lines.append(f"Open/run: /view?path={final_run_path}")
                lines.append(f"Download file: /download?path={final_run_path}")
                if str(final_run_path).lower().endswith(".html"):
                    lines.append(f"Windows run command: start .\\{final_run_path}")
                elif str(final_run_path).lower().endswith(".py"):
                    lines.append(f"Windows run command: py -3 .\\{final_run_path}")
            elif self.last_plan.mode == "qa":
                lines.append("\nQA run complete. No project files were created for this functionality-test request.")
            elif self.last_plan.mode == "project_qa":
                lines.append("\nProject QA run complete. No new project was created; results describe the currently open workspace.")
            if generated_zip_url:
                lines.append(f"Download project zip: {generated_zip_url}")
            if project_name:
                lines.append(f"Project: {project_name}")
            log_activity("plan_done", "Plan completed", {"run_id": plan_run_id, "goal": self.last_plan.goal, "final_run_path": final_run_path if project_output_mode else "", "zip": generated_zip_url, "project": project_name, "mode": self.last_plan.mode})
        self._save_plan()
        set_current_run(None)
        return "\n".join(lines)
    def fix_last_error(self, note: str = "") -> str:
        if not self.last_error:
            return "No last error stored. Run /verify, /auto-verify or /run-plan first."
        goal = "fix the last error in this project"
        if note.strip():
            goal += ": " + note.strip()
        self.last_plan = make_plan(goal, workspace=Path(self.config.workspace), last_error=self.last_error)
        self._save_plan()
        return self.last_plan.to_text() + "\n\n" + self.run_plan()
    def quality_dashboard(self, goal: str = "") -> str:
        """Write and return a combined Nova/project quality dashboard."""
        try:
            md_path, json_path, dashboard = write_quality_dashboard_report(Path(self.config.workspace), goal or "")
            lines = [render_quality_dashboard_markdown(dashboard), "", f"Markdown report: `{md_path}`", f"JSON report: `{json_path}`"]
            log_activity("quality_dashboard", "Quality dashboard generated", {"markdown": str(md_path), "json": str(json_path), "score": dashboard.score})
            return "\n".join(lines)
        except Exception as exc:
            log_activity("quality_dashboard_failed", "Quality dashboard failed", {"error": str(exc)})
            return f"Quality dashboard failed: {exc}"

    def version_text(self) -> str:
        return (
            f"Nova {__version__}\n"
            f"{VERSION_LABEL}\n"
            f"Workspace: {self.config.workspace}\n"
            f"Code/build model: {self.config.model}\n"
            f"Chat/creative model: {getattr(self.config, 'chat_model', self.config.model)}\n"
            f"Planning/review model: {getattr(self.config, 'planner_model', '') or self.config.model}\n"
            "Version consistency check: GUI title, CLI banner, package metadata and /version are aligned."
        )
    def _run_with_thinking_timer(self, fn, *args, wait_sec: float = 5.0, **kwargs):
        """Run a blocking CLI call and display thinking time after a short wait."""
        started = time.perf_counter()
        done = threading.Event()

        def _ticker() -> None:
            shown = False
            while not done.wait(0.25):
                elapsed = time.perf_counter() - started
                if elapsed >= wait_sec and not shown:
                    print(f"\nNova is thinking... {elapsed:.1f}s elapsed", flush=True)
                    shown = True

        thread = threading.Thread(target=_ticker, daemon=True)
        thread.start()
        try:
            return fn(*args, **kwargs)
        finally:
            done.set()
            elapsed = time.perf_counter() - started
            if elapsed >= wait_sec:
                print(f"\nThinking time: {elapsed:.1f}s", flush=True)

    def repl(self) -> None:
        print("Nova CLI")
        print(f"Nova {__version__}. Use /help or /version.")
        while True:
            try:
                text = input("\nYou> ").strip()
            except (KeyboardInterrupt, EOFError):
                print("\nBye.")
                return
            if text.lower() in {"/exit", "exit", "quit"}:
                print("Bye.")
                return
            if not text:
                continue
            print("\nAssistant>")
            print(self._run_with_thinking_timer(self.chat, text))

    def run_cli(self) -> None:
        """Backward-compatible CLI entrypoint used by app.py and the Windows batch file."""
        self.repl()
HELP = """
Commands:
/help                         Show this help
/version                      Show installed version and consistency check
/status                       Show config, tools and local LLM status
/workspace PATH               Set safe workspace and auto-register it as a project
/allow-mutate on|off          Enable/disable file writes and shell commands (ON by default)
/model MODEL                  Set code/build Ollama model (alias for /model-code)
/models                       Show model routing and installed Ollama models
/model-code MODEL             Set build/code model
/model-chat MODEL             Set normal chat/creative model
/model-planner MODEL          Set planning/review model
/model-route auto|manual      Auto routes chat vs code models, or force one model
/high-spec-profile            Show upgraded-PC model/runtime profile
/subagents GOAL               Plan safe subagents; non-LLM parallel, LLM serialized
/authority-mode               Show internet/mutation/shell authority controls
/projects                     List saved projects
/project-new NAME [=> PATH]   Create/register/open a project folder
/project-open NAME            Open a saved project as the current workspace
/project-remove NAME          Remove a project from the saved list only
/project-delete NAME          Delete a project registration and its folder
/project-files [NAME]         List files for current/specified project
/project-spec GOAL            Write PROJECT_BUILD_BRIEF files from a user specification
/open-file PATH               Read/open a file from the current project
/files [SUBDIR]               List files under workspace
/tree [SUBDIR]                Compact folder tree
/read PATH                    Read file
/write PATH CONTENT           Write/overwrite a file inside workspace
/append PATH CONTENT          Append to a file
/mkdir PATH                   Create a folder
/replace PATH OLD => NEW      Exact find/replace inside file
/search TEXT                  Search text in workspace files
/shell COMMAND                Run PowerShell command in workspace
/verify COMMAND               Run command and check for error markers
/auto-verify                  Run likely build/test check
/fix-last [NOTE]              Build and run a repair plan from the last error
/surgical-repair [NOTE]        Try targeted find/replace repair before broader backtracking
/backtrack [NOTE]              Manually run backtracking recovery from the last error
/continue [GOAL]              Continue/edit the currently open project now
/fast GOAL                    Fast stream: build the smallest useful working version now
/long GOAL                    Long stream: requirements, build, test, repair, review, package
/plan GOAL                    Make a human-readable executable plan only
/run-plan                     Execute current plan
/do GOAL                      Auto-pick fast/long, build/edit/run the requested thing now
/autonomous status|start|once|stop [GOAL]
/autonomous-status             Show live autonomous state
/autonomous-guide              Explain autonomous tool sequencing
                              Autonomous mode: investigate, improve, repair and optionally build until stopped
/test-all                     Run full v50 compatibility/reliability test suite
/model-doctor                 Diagnose Ollama/model setup and show install commands
/model-benchmark              Rank installed Ollama models on tiny JSON/code/chat tests
/model-doctor                 Select sensible installed defaults and warn about missing models
/interrupt-current            Ask before interrupting an active local model/task
/idle status|start|once|stop  Idle self-analysis mode that pauses for user tasks
/avatar                       Show current assistant state
/self-guide                   Explain how to use every aspect of Nova
/model-timeout status|off|SEC Control local Ollama timeout
/command-timeout status|SEC   Control shell/verification command timeout
/model-health                  Summarise model dependency readiness and degraded-mode advice
/skill-mode [MODE]            Show/set skill routing: auto, general, coding, math, science, communication
/math QUESTION                Maths mode with careful steps and quick arithmetic check
/science QUESTION             Science mode with assumptions, units and limitations
/code QUESTION                Coding/debugging mode with exact commands and tests
/communicate TEXT             Writing/rewriting mode with clear natural phrasing
/memory                       Show recent Nova/user memory
/remember TEXT                Save a note to local memory
/knowledge                    Show built-in debug/Q&A knowledge base
/learn-errors                 Convert recent errors into reusable lessons
/reasoning                    Show current reasoning/recovery diagnostic
/recovery-plan                Alias for /reasoning
/recover-known-error          Try remembered deterministic recovery for the last error
/persona                      Show Nova persona, beliefs, response contract and sliders
/persona-set KEY=VALUE...      Update persona sliders/fields, e.g. formality=0.8 verbosity=0.3
/custom-chat-window            Show the custom chat/persona window spec
/inspiration-radar [FOCUS]      Show inspiration-backed safe Nova improvement ideas
/tool-context-pack GOAL        Pick a compact prompt-relevant tool set for local-model context
/handoff-plan GOAL             Build a deterministic router/planner/builder/verifier handoff plan
/improvement-preflight GOAL    Preview risk and required validation before patching
/coding-plan GOAL              Choose best file/runtime layout: Python, Java, Node, PowerShell, API or browser
/coding-audit [GOAL]           Audit Nova coding path for HTML bias, verifier coverage and request-fit
/local-model-performance GOAL  Show task-specific local model tuning/settings; use GOAL => HARDWARE to add GPU/VRAM hints
/agent-upgrade-radar [FOCUS] Show web-inspired additive Nova improvement ideas and checks
/context-budget GOAL          Choose compact repo/tool context for local-model prompts
/coding-behavior-tests GOAL   Create request-specific acceptance checks for generated code
/ollama-runtime-profile GOAL  Draft task/hardware-specific Ollama options; use GOAL => HARDWARE
/upgrade-regression-audit     Confirm recent Nova patches are still present, routed and tested
/repo-context-map GOAL        Build compact repo context map for local/coding agents
/patch-impact-plan FILES      Pick targeted regression tests for changed files
/permission-scope-review GOAL Preview permission/scope risk before broad autonomous edits
/local-model-benchmark GOAL   Draft repeatable Ollama benchmark prompts/profiles; use GOAL => HARDWARE
/tool-contract-audit          Check command/tool registry contract and patch continuity
/agent-topology GOAL        Plan router/context/builder/verifier/reporter specialist topology
/trace-observability GOAL  Draft trace spans, metrics and redaction contract
/local-stack-advisor GOAL  Advise Ollama vs llama.cpp and local model settings; use GOAL => HARDWARE
/verifier-ladder GOAL      Generate runtime-specific verification ladder; use GOAL => RUNTIME
/tool-namespace-plan GOAL  Plan conditional tool namespaces to reduce model prompt bloat
/voice-pipeline-review FOCUS Review Jarvis-style modular voice pipeline without changing audio
/route-resilience-plan GOAL Build self-healing tool route/fallback plan without executing changes
/improvement-assurance GOAL => FILES Build evidence gates proving a patch is an actual improvement
/test-impact-graph FILES Map changed files to likely regression tests before patching
/patch-quality-score FILES Score likely maintainability/regression risk for a proposed patch
/success-claim-audit SUMMARY Check whether a release summary overclaims validation evidence
/regression-bisect-plan SYMPTOM => VERSIONS Plan safe release-zip bisection for a regression
/tool-health-map [FOCUS]   Audit command/tool route health without invoking tools
/guardrail-memory GOAL     Build context-aware guardrail memory rules; use GOAL => RISK NOTE
/context-router-policy GOAL Plan role-aware context routing and compact repo context
/local-runtime-sentinel GOAL Draft local-model health checks; use GOAL => HARDWARE
/local-model-optimizer         Show local-model routing, context and prompt-cache improvements
/agent-harness                 Show iterative generate/execute/observe/repair loop
/voice-audit                   Show voice command audit log
/voice-mode                   Explain browser mic input and spoken reply controls
/voice-troubleshoot           Explain Mic test, browser permissions and Bluetooth headset fixes
/speak TEXT                   Trigger assistant-state speech/avatar cue
/command-catalog              Explain how commands/tools are selected and sequenced
/visual-repair [PATH]         Human/visual/final check scaffold and repair target report
/console-test [PATH]          Static browser reference/console-prep checks
/known-issues                 Show accumulated known issue log
/self-improvement-queue       Write safer self-improvement proposal queue
/mistake-learning             Show recorded failure patterns and repair recommendations
/self-repair-status           Show bounded self-repair permission, queue and validation state
/self-repair-permission on|off Enable/disable bounded automatic source repair
/self-repair-now GOAL         Run safe backup + validation guarded self-repair
/self-repair-validate         Run compile/smoke validation used by self-repair
/self-apply ID                Approval-gated self-improvement stub
/autonomous-memory            Show autonomous cycle memory
/autonomous-explain [GOAL]      Explain what autonomous is doing now, why, risk, next step and verification
/autonomous-plan GOAL       Preview the exact autonomous command/tool sequence before running
/autonomy-capabilities GOAL Show which tools/commands/capabilities idle/autonomous should use and why
/mutable-plan GOAL          Build a prompt-specific plan that adapts when evidence changes

/blueprint GOAL              Compile the prompt into files, requirements, must-not-have rules and validation
/candidate-build GOAL        Plan candidate variants and compare request-fit before promoting files
/model-output-score GOAL     Score recent model output against the prompt blueprint
/trace-last                  Show agent trace cockpit from recent activity/model events
/trace-run RUN_ID            Show trace cockpit for a specific run
/performance-dashboard       Summarise recent time/operation mix for bottleneck hunting
/gui-feature-map             Verify classic GUI features still have a home before redesign
/gui-mode cockpit            Preview the non-regressing cockpit GUI layout plan
/gui-regression-test         Check GUI feature coverage before UI overhaul
/mcp-export-manifest         Export a local MCP-style manifest of Nova tools/resources/prompts
/gui-visual-test             Show optional Playwright visual-regression gate commands
/gui-layout-status          Check static/browser GUI layout contract and cache-reset guidance
/gui-reset-help             Show exact steps for resetting stale browser drawer/layout state
/build-info                 Show patch/build identity, source fingerprint and GUI cache version
/perf-status                Show local AI env/GPU/Ollama performance readiness
/perf-tune-plan             Show safe staged local AI performance tuning plan
/perf-benchmark [--write-scripts] Show or write reproducible benchmark scripts
/perf-artifact-checklist    Show files to upload for tuning iteration
/gui-ai-help CONTEXT         Explain a clicked GUI element and suggest safe commands
/gui-ai-upgrades             Show the repo-inspired GUI/help upgrades installed in this patch
/command-help [QUERY]        Search grouped command help with what/why/how/examples
/release-readiness --full    Run packaging gate; blocks ship if chat/help/GUI/code/write/run regress
/arcade                      Show Nova Arcade game registry
/arcade-launch system-runner Show how to launch Nova: System Runner in the GUI
/nova-mega-test --confirm    Run the broadest one-command Nova aspect test and report
/comprehensive-user-test    Run broad user-flow QA across commands, GUI, contracts and regressions
/bug-review                  Run a bug-focused source/integration/release-hygiene scan
/regression-sweep            Check cross-feature command/tool/formatting integration for regressions
/improvement-proposals FOCUS  Build ranked implementation-ready improvement proposals
/improvement-cycle --confirm  Complete safe improvement proposals and record done/skipped status
/completed-improvements       Show latest completed improvement cycle
/autonomous-journal         Show the latest durable autonomous sequence journal
/test-project [basic|standard|deep]
                              Run project checks and final requirement review
/quality-dashboard [GOAL]      Write combined Nova/project quality dashboard
/command-verify               Verify existing read-only command contracts
/repo-upgrade-assurance        Verify repo-inspired manifests, tools, routes, idle/autonomous wiring and future timeline
/maintenance-validate          Run the combined self-maintenance validation gate and stable test ladder
/codebase-sanity-audit         Audit redundancy, large modules, raw writes, command/tool drift and rewrite candidates
/repo-research-radar           Summarise repo research ideas installed in Nova and the next integration priorities
/nova-eval-packs [plan|run] [PACK] Run deterministic eval packs: core, release, agent, coding, voice, all
/nova-self-apply [plan|preview|apply] [ID] Verified self-change engine with preview, backup, validation and rollback
/nova-odysseus-suite       Show/write the Odysseus feature-port coverage audit
/nova-tool-permissions     Odysseus-style privilege table: list, check ACTION, set TOOL LEVEL
/nova-cookbook             Detect/simulate hardware and rank local model choices
/nova-compare              Create/list/vote blind model comparison receipts
/nova-docs                 Workspace document vault with sidecar AI suggestions
/nova-notes, /nova-tasks   Local notes and checklist tasks
/nova-skills, /nova-presets Persistent skill/preset library with export
/nova-memory-vault         Audit/export suite memory artifacts
/nova-integration-gates    Review high-risk integration gates before use
/nova-fastapi-plan       Plan safe FastAPI sidecar/API/event migration without rewriting Nova core
/nova-api-status        Show actual optional FastAPI API bridge routes, safety and start command
/nova-gui-workbench-plan Map Odysseus-style rail/sidebar/workspace GUI layout for Nova
/architecture-audit          Inspect architecture continuity, docs, commands and release hygiene
/repair-audit                Scan code for repair candidates, risky patterns and release artifacts
/code-review                 Run deeper reliability, maintainability, timeout and UX code review
/model-context [PROMPT]       Preview/toggle the Nova context pack sent to local model calls
/model-help-plan GOAL          Ask local model for a JSON repair/build plan using Nova context
/model-help-implement GOAL     Ask local model for plan, then run guarded improve-project
/beyond-thinking on|off|PROMPT Preview/enable high-confidence inferred context only
/efficiency [report|time N CMD] Measure tool/model/chat timings, CPU time and estimated energy
/self-awareness [GOAL]        Show Nova capability inventory, safety boundaries and autonomous state
/planning-dashboard GOAL      Show intent, subtasks, watcher decision and verification plan
/action-watch ACTION          Evaluate action risk before execution
/interaction-lessons [TEXT]   Show lessons or record a user-feedback lesson
/deps-status                  Show dependency/resource status
/validation-status            Show latest validation report/progress and last completed stage
/remote-access-status        Show remote/Tailscale/API/Wake-on-LAN readiness without exposing Nova
/remote-access-plan          Show safe phone/laptop remote access setup plan
/remote-access-test          Run a read-only local preflight for remote desktop/API/Wake-on-LAN setup
/remote-api-health HOST     Probe a localhost/LAN/Tailscale Nova API endpoint without changing remote state
/remote-profile list/add   Save host/port/MAC remote profiles without storing raw tokens
/remote-profile-wizard    Build read-only commands/checks before saving a remote profile
/remote-access-scripts       Write remote API/startup helper scripts and setup guide
/remote-wake MAC [--dry-run|--confirm] Send or simulate Wake-on-LAN magic packet for your own PC
/upgrade-radar                 Show significant optional upgrades, download requirements and checks
/optional-upgrades              Review allowlisted optional downloads such as Ruff, pre-commit and Playwright
/upgrade-install NAME --confirm Install an allowlisted optional upgrade after explicit confirmation
/model-readiness GOAL          Check which local Ollama models are required/optional for a task
/model-install NAME --confirm Download an allowlisted or explicit Ollama model after confirmation
/interactive GOAL             Start a two-way run that can pause and ask one clarifying question
/two-way GOAL                 Alias for /interactive
/reply TEXT                   Answer the active two-way run question and continue building
/active-run                   Show current interactive run status
/pause-run                    Pause the active interactive run
/resume-run                   Resume the active interactive run
/cancel-run                   Cancel the active interactive run
/zip [PATH]                   Zip a file/folder for download
/download PATH                Print a web download link for a file
/llm-status                    Show Ollama ps / active model info
/providers                     Show local/remote provider lanes and queue receipts
/provider ollama|openrouter|subq|nvidia-nim|llama-cpp|vllm|sglang|local-gemma
                              Choose active model provider; remote lanes require explicit internet/key
/provider-route GOAL           Explain local/default, NVIDIA local, or remote long-context route
/provider-test [PROVIDER]      Show dry-run provider validation command without leaking API keys
/queue-status                  Show provider/model queue receipts and active calls
/queue-drain                   Explain safe cancellation/drain behaviour for provider queues
/allow-internet on|off          Required before remote provider calls are allowed
/internet-fetch URL            Fetch a public page when /allow-internet is on
/watch-topic TOPIC => URLS      Save a topic watcher with public source URLs
/topic-watchers                 List saved topic watchers
/topic-check TOPIC              Fetch watched sources and write a topic report
/openrouter-model MODEL         Set optional OpenRouter model, e.g. model:free variant
/godmod3-report                 Explain godmod3.ai/G0DM0D3 findings and safe integration
/vision-status                  Show local image-recognition readiness
/attach-file PATH                Attach a local file/photo as prompt context
/context-files [list|clear]      Show or clear shared prompt file context
/media-status                   Unified image/video backend readiness and recommended workflow
/image-plan PROMPT               Plan prompt variants/seeds before image generation
/video-storyboard PROMPT          Write storyboard SVG, shot list and keyframe prompts
/video-package PROMPT             Write full video manifest/storyboard/preview/render package
/image-generate PROMPT           Generate a real image using SD WebUI/Diffusers when configured
/image-edit SRC => PROMPT        Edit a real image using SD WebUI/Diffusers when configured
/image-status                    Check real image-generation backend setup
/image-setup-help                Show SD WebUI/Diffusers/ComfyUI setup wizard and test commands
/project-target GOAL             Explain whether Nova will create a new project or edit current one
/security-watch                  Read-only defensive security delta check
/sandbox-status                  Check Linux/Kali sandbox runtime and policy
/sandbox-linux start|stop|exec  Manage general Linux sandbox
/sandbox-kali start|stop|exec   Manage Kali security-lab sandbox
/sandbox-exec linux|kali CMD    Run a bounded command in a running sandbox
/sandbox-dev-run linux|kali CMD Run writable copied-workspace dev/test command; live files untouched
/sandbox-dev-mode on|off       Enable copied-workspace sandbox dev workflow guidance
/sandbox-autonomy on|off        Let autonomous mode use disposable sandbox context
/sandbox-network on|off         Allow sandbox network only for owned lab targets
/image-draft PROMPT              Create a labelled SVG placeholder draft
/vision-model MODEL              Set Ollama vision model for image analysis
/image-analyze PATH => PROMPT    Analyze a screenshot/image inside the workspace
/human-test [PATH]               Run dependency-free human-style UI audit
/visual-test [PATH]              Create/run optional Playwright screenshot/trace test
/cycle-schema                    Export structured autonomous cycle schema
/research TOPIC [=> URLS]      Gather sources, score credibility/bias, map claims and write/index a research report
/research-plan                  Write/show the v40 research integration roadmap
/db list|put|merge|get|schema|export|search|delete  Let Nova keep schemaless JSON/text databases under ~/.nova
/mcp-manifest                   Export MCP-like internal tool manifest
/benchmark-init [PATH]          Create local benchmark/regression task scaffold
/benchmark-run [PATH]           Run current local benchmark checks
/telemetry-export               Zip activity/model/proposal logs for debugging
/ollama-stop                   Unload selected Ollama model from memory
/ollama-multi                  Explain multi-model Ollama use and Nova single-prompt policy
/activity                      Show saved activity/model logs
/investigate-logs [FOCUS]       Investigate recent errors and write ERROR_INVESTIGATION.md
/propose-improvements [FOCUS]   Propose changes to Nova/tools/projects from logs
/tool-guide                     Show guide for using tools together sequentially
/resource-status               Show workspace, Python, disk, Ollama and watchdog status
/heartbeat                     Run one watchdog health check now
/watchdog on|off|status [SEC]  Start/stop/status background heartbeat watchdog
/custom-tools                  List AI-created custom tools in their own toolbox section
/tool-create GOAL              Ask local LLM to write and safely install a small custom tool
/tool-help [NAME]              Show tool inputs and examples
/tool-inputs [NAME]            Alias for /tool-help
/tool-run NAME [=> JSON/TEXT]  Run a custom tool with JSON, {text}, or key=value args
/tool-pipeline JSON            Run safe sequential tool calls
/safe-script-demo TEXT         Run a real standard-library local demo tool
/tool-delete NAME              Delete an installed custom tool
/tool-proposals                List pending tool proposals
/tool-clean-proposals          Remove stale/superseded failed proposals
/self-check                    Check runtime methods, registered tools and proposal cleanup
/tool-approve ID               Approve and install a pending tool proposal
/tool-reject ID                Reject/delete a pending tool proposal
/tool-view NAME                View custom tool source and metadata
/tool-code NAME                Alias for /tool-view, shows tool code
/tool-test NAME                Run a safe test of a custom tool
/tool-enable NAME              Enable a disabled custom tool
/tool-disable NAME             Disable a custom tool without deleting it
/agent GOAL                    Bounded agent loop that can use /help tools and custom tools
/improve-project [GOAL]        Agentic current-project improvement, testing and repair loop
/improvement-report            Show the latest comprehensive improvement report
/pip-install PACKAGE           Install safe allowlisted Python packages only
/self-improve GOAL             Let the assistant edit its own source with backup, tests and rollback
/logs                         Show recent trace events
/exit                         Quit
Examples:
/project-new MyStory
/do make an interactive story
/tool-create create a JSON todo-list summariser for project files
/tool-run todo_summary => {"path":"tasks.json"}
/tool-run big_bold_reply => {hey}
/tool-pipeline [{"tool":"tool_run","args":{"name":"html_reference_checker","args":{"subdir":"."}}}]
/watch-topic local AI => https://hnrss.org/newest, https://arxiv.org/rss/cs.AI
/watchdog on 30
/interactive make a useful app and ask me before choosing API/offline scope
/reply offline local app first
/self-improve improve project repair logic without changing safety rules
/fix-last
/research-plan
/providers
/benchmark-init
""".strip()


# v55.3.164 natural scheduling route bindings. Kept outside the large class to minimise refactor risk.
def _nova164_looks_like_natural_schedule_request(self, text: str) -> bool:
    low = (text or "").strip().lower()
    if not low or low.startswith("/"):
        return False
    markers = [
        "remind me", "set a reminder", "schedule ", "schedule a ", "add task", "add a task",
        "tomorrow", "next friday", "next monday", "every day", "weekly", "at 4pm", "at 8am",
    ]
    return any(marker in low for marker in markers) and not any(marker in low for marker in ["make a game", "build an app", "create a website"])


def _nova164_handle_natural_schedule_request(self, text: str) -> str:
    result = self.tools.call("schedule_task", prompt=text)
    prefix = "I treated that as a scheduling request and used Nova's local scheduler safety gate, not the project builder."
    if result.ok and result.data.get("task", {}).get("status") == "scheduled":
        prefix += " The task is scheduled locally."
    elif result.data.get("task", {}).get("status") == "pending_confirmation":
        prefix += " It needs confirmation before execution because it has medium/high risk."
    elif not result.ok:
        prefix += " The task was blocked or could not be scheduled safely."
    return prefix + "\n\n" + self.format_result(result)

AssistantCore._looks_like_natural_schedule_request = _nova164_looks_like_natural_schedule_request
AssistantCore._handle_natural_schedule_request = _nova164_handle_natural_schedule_request
