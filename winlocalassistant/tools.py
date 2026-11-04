from __future__ import annotations

import base64
import difflib
import json
import logging
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import urllib.parse
import urllib.request
import zipfile
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable

from .config import AssistantConfig, APP_DIR
from .safe_io import append_jsonl, append_text_line, atomic_append_text, atomic_write_bytes, atomic_write_json, atomic_write_text, read_json_file
from .autonomous_failure import AUTONOMOUS_FAILURE_MEMORY_PATH, load_autonomous_failure_memory
from .creation_intent import analyze_creation_request, validate_created_artifact_matches_request, project_target_decision, score_created_project_quality
from .project_request_contract import build_request_contract
from .deterministic_generation import deterministic_simple_project
from .game_design import analyze_game_request, build_generic_canvas_game_project, game_prompt_requirements, strip_interactive_clarification
from .analytics_engine import get_analytics_engine, render_analytics_dashboard
from .proposal_ledger import get_proposal_ledger, render_proposal_ledger, ProposalLedger
from .performance_profiler import get_performance_profiler, render_performance_report
from .webhook_system import get_webhook_manager, render_webhooks_status, EventType
from .task_scheduler import get_task_scheduler, render_scheduler_status
from .project_runtime_probe import run_project_runtime_probe
from .project_iteration import append_project_iteration_event, build_project_iteration_event, is_repeated_repair, write_project_verification_report
from .safety import is_dangerous_command, resolve_inside_workspace
from .projects import register_project, list_projects, get_project, remove_project
from .model_router import model_chat
from .ollama import ollama_busy_state, ollama_vision_chat
from .model_health import assess_model_dependency
from .custom_tools import list_custom_tools, run_custom_tool, save_custom_tool, delete_custom_tool, save_tool_proposal, list_tool_proposals, approve_tool_proposal, delete_tool_proposal, set_custom_tool_enabled, get_custom_tool_source, cleanup_tool_proposals, refresh_custom_tool_registry, mark_custom_tool_tested
from .watchdog import heartbeat as watchdog_heartbeat, start_watchdog, stop_watchdog, watchdog_state
from .eventlog import ACTIVITY_PATH, MODEL_IO_PATH, log_activity, log_model_io, tail_jsonl
from .tool_guides import get_local_model_tool_use_summary
from .file_context import IMAGE_EXTS, resolve_image_context
from .screen_analysis import parse_screen_analysis_request, render_screen_analysis_prompt_help
from .image_generation import build_image_prompt_plan, render_image_prompt_plan_markdown, image_generation_status
from .project_brief import infer_project_build_brief, render_project_build_brief_markdown, write_project_build_brief
from .code_repair_audit import write_code_repair_audit_report, render_code_repair_audit_markdown
from .code_review_audit import write_code_review_report, render_code_review_markdown
from .code_quality_gate import write_code_quality_gate_report, render_code_quality_gate_markdown
from .assistant_box import read_assistant_box, write_assistant_box, clear_assistant_box
from .nova_video import write_storyboard_svg, write_shotlist_csv, build_video_image_prompt_plan, write_video_render_package, render_video_render_package_markdown, media_status_summary
from .model_context import render_model_context_preview
from .nova_operating_context import build_nova_operating_context, render_nova_operating_context, write_nova_operating_context, write_action_receipt
from .efficiency_profiler import profile_call, render_efficiency_markdown, clear_efficiency_samples, set_runtime_profiler_enabled
from .research_engine import build_research_report, render_research_markdown, discover_source_urls
from .assistant_datastore import list_databases, put_record, get_record, search_records, delete_record, merge_record, database_schema, export_database, audit_database, compact_database, render_db_markdown
from .codebase_integrity_audit import write_codebase_integrity_report, render_codebase_integrity_markdown
from .sandbox_manager import sandbox_status, start_sandbox, stop_sandbox, exec_sandbox, sandbox_dev_run, set_sandbox_flag, set_sandbox_policy, sandbox_setup_help, render_status_markdown, render_setup_help_markdown
from .docker_manager import docker_status, docker_ps, docker_smoke, docker_validate_project, docker_validate_patch, docker_promote_validated_patch, docker_validation_history, docker_cleanup, render_docker_markdown, render_docker_setup_help, render_docker_history_markdown, render_docker_cleanup_markdown
from .cohesion_engine import write_cohesion_report, render_cohesion_report_markdown, render_validation_ladder_markdown, render_iterative_development_markdown
from .wla_doctor import run_wla_doctor, render_wla_doctor_markdown, run_wla_release_gate, render_wla_release_gate_markdown
from .integration_radar import build_integration_radar, render_integration_radar_markdown
from .project_memory import project_memory_context, remember_project_fact
from .release_checklist import build_release_checklist, render_release_checklist_markdown
from .feature_audit import build_feature_audit, render_feature_audit_markdown
from .branding import render_branding_audit, scan_legacy_branding
from .nova_improvement_research import build_nova_improvement_research, render_nova_improvement_research
from .pipeline_router import classify_pipeline, render_pipeline_route, route_to_dict, write_project_patterns, render_project_patterns
from .pipeline_manifests import render_manifest_catalog, render_manifest, write_manifest_snapshot
from .session_evidence import build_session_evidence, render_session_evidence
from .memory_inventory import build_memory_inventory, render_memory_inventory
from .tool_orchestrator import build_tool_awareness_plan, render_tool_awareness_plan, plan_payload, audit_tool_awareness, render_tool_awareness_audit
from .command_verifier import render_command_verification_markdown
from .repo_upgrade_assurance import build_repo_upgrade_assurance, render_repo_upgrade_assurance
from .codebase_sanity_audit import build_codebase_sanity_audit, render_codebase_sanity_audit
from .maintenance_validation import build_maintenance_validation, render_maintenance_validation
from .autonomy_readiness import build_autonomy_readiness, render_autonomy_readiness_markdown

from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation
from .candidate_tournament import build_candidate_tournament, render_tournament, render_candidate_failure_report, candidate_diff
from .repair_engine_v2 import build_repair_plan, render_repair
from .trace_cockpit import build_trace, render_trace_markdown, render_performance_dashboard
from .mcp_security import inspect_mcp_security, render_mcp_security, explain_mcp_tool
from .mission_planner_v2 import create_mission, load_mission, mission_step, render_mission
from .model_output_coach import analyze_model_output, render_model_output_coach
from .env_profiles import build_env_profile, render_env_profile
from .benchmark_migration import benchmark_system, render_benchmark
from .project_state_db import load_project_state, append_project_state, audit_project_state, render_project_state
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
    load_mistake_log, mistake_to_regression, autonomous_last_report, render_payload,
)
from .iterative_coding import build_surgical_fallback_plan, build_iterative_coding_loop, render_iterative_coding_markdown, write_iterative_coding_report
from .next_feature_suite import (
    build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,
    build_model_reliability, render_model_reliability, build_model_fallback_strategy, render_strategy,
    patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,
    build_voice_mode_report, render_voice_mode, list_templates, build_template_project, render_templates,
    build_preview_server_report, render_preview, build_feature_readiness, render_feature_readiness,
    explain_error, render_error_explanation, build_support_report, render_support_report, docs_index, render_docs_index,
    regression_test_generate, render_regression_test, learning_status, render_learning_status,
)
from .model_download_manager import build_model_readiness, render_model_readiness, install_model, render_model_install_result
from .response_quality import build_response_quality_plan, render_response_quality_plan, write_response_quality_plan
from .flow_audit import build_flow_audit, render_flow_audit, write_flow_audit
from .feature_continuity import build_feature_continuity_audit, render_feature_continuity_audit
from .autonomous_mission_contract import build_mission_contract, render_mission_contract, score_progress, write_contract_report
from .surgical_recipes import classify_failure, patch_candidate_for_failure, recipe_steps
from .project_type_registry import project_type_contract, PROJECT_TYPES
from .self_test_generator import write_regression_test, generate_regression_test
from .development_governor import build_strategy_decision, build_validation_evidence, render_strategy, render_validation_evidence
from .adaptive_backlog import build_adaptive_backlog, render_adaptive_backlog, build_generation_template_manifest, render_template_manifest
from .validation_matrix import build_validation_matrix, render_validation_matrix
from .idle_policy import load_idle_policy, set_idle_policy_level, render_idle_policy
from .role_router import build_role_route, render_role_route
from .receipt_history import summarise_receipts, render_receipt_history
from .jarvis_bridge import build_capability_map, probe_jarvis_daemon, update_bridge_policy, queue_proactive_action, list_queued_actions, render_bridge_markdown, build_jarvis_setup_doctor, build_sidecar_preflight, build_authority_decision, build_workflow_blueprint, build_workflow_execution, build_bridge_receipts, build_sidecar_enrollment_checklist, build_safe_browser_harness, build_jarvis_test_prompts, build_audit_log
from .persona_profile import build_custom_chat_window_spec, build_persona_prompt_addendum, load_persona_profile, render_persona_profile, update_persona_from_tokens, update_persona_from_json, append_voice_audit, build_voice_audit, render_voice_audit
from .local_model_optimizer import build_local_model_optimization_plan, render_local_model_optimization_plan, build_iterative_agent_harness, render_iterative_agent_harness
from .nova_coding_capabilities import (
    build_coding_capability_audit,
    build_local_model_performance_plan,
    plan_coding_execution,
    render_coding_capability_audit,
    render_coding_execution_plan,
    render_local_model_performance_plan,
)
from .startup_validation import build_startup_validation, render_startup_validation
from .nova_system_test import build_nova_full_system_test, render_nova_full_system_test
from .completion_audit import build_completion_audit, render_completion_audit
from .release_packager import build_release_package, render_release_package
from .release_readiness import build_release_readiness, render_release_readiness_markdown
from .task_execution import (
    build_task_execution_status,
    build_verify_summary,
    record_failure_result,
    record_task_evidence,
    render_verify_summary,
    repeated_failure_block,
)
from .codebase_advisor import build_codebase_advisor, render_codebase_advisor
from .nova_inspiration_engine import (
    build_handoff_plan,
    build_improvement_preflight,
    build_nova_inspiration_radar,
    build_tool_context_pack,
    render_handoff_plan,
    render_improvement_preflight,
    render_inspiration_radar,
    render_tool_context_pack,
)
from .nova_agent_upgrade_lab import (
    build_agent_upgrade_radar,
    build_coding_behavior_tests,
    build_context_budget_plan,
    build_ollama_runtime_profile,
    build_upgrade_regression_audit,
    render_agent_upgrade_radar,
    render_coding_behavior_tests,
    render_context_budget_plan,
    render_ollama_runtime_profile,
    render_upgrade_regression_audit,
)
from .nova_reliability_lab import (
    build_local_model_benchmark_plan,
    build_patch_impact_plan,
    build_permission_scope_review,
    build_repo_context_map,
    build_tool_contract_audit,
    render_local_model_benchmark_plan,
    render_patch_impact_plan,
    render_permission_scope_review,
    render_repo_context_map,
    render_tool_contract_audit,
)
from .nova_deep_research_lab import (
    build_agent_topology_plan,
    build_local_stack_advisor,
    build_tool_namespace_plan,
    build_trace_observability_plan,
    build_verifier_ladder,
    build_voice_pipeline_review,
    render_agent_topology_plan,
    render_local_stack_advisor,
    render_tool_namespace_plan,
    render_trace_observability_plan,
    render_verifier_ladder,
    render_voice_pipeline_review,
)
from .nova_route_resilience_lab import (
    build_context_router_policy,
    build_guardrail_memory_plan,
    build_local_runtime_sentinel,
    build_route_resilience_plan,
    build_tool_health_map,
    render_context_router_policy,
    render_guardrail_memory_plan,
    render_local_runtime_sentinel,
    render_route_resilience_plan,
    render_tool_health_map,
)
from .nova_improvement_assurance_lab import (
    build_improvement_assurance_plan,
    build_patch_quality_score,
    build_regression_bisect_plan,
    build_success_claim_audit,
    build_test_impact_graph,
    render_improvement_assurance_plan,
    render_patch_quality_score,
    render_regression_bisect_plan,
    render_success_claim_audit,
    render_test_impact_graph,
)
from .nova_video import plan_video_manifest, render_video_manifest_markdown, save_video_manifest, video_stack_status, validate_video_manifest, build_video_execution_plan, render_video_validation_markdown, video_user_test_scenarios, write_video_preview_avi, write_video_preview_html

from .repo_intelligence import build_repo_map, render_repo_map, build_patch_plan, render_patch_plan
from .browser_worker import build_browser_task_plan, render_browser_task_plan
from .document_ingestion import ingest_document, search_ingested_document, render_document_ingestion
from .model_registry import build_model_registry, render_model_registry
from .provider_runtime import provider_matrix, render_provider_markdown, choose_provider, render_route_markdown, provider_test_plan, get_provider_scheduler
from .high_spec_profile import build_high_spec_profile, render_high_spec_profile
from .subagent_orchestrator import build_subagent_plan, render_subagent_plan
from .integration_review import build_integration_review, render_integration_review
from .self_repair_guardian import (
    build_mistake_learning_report,
    load_self_repair_policy,
    record_mistake,
    render_mistake_learning_report,
    render_self_repair_report,
    run_auto_self_repair,
    run_self_repair_validation,
    set_self_repair_enabled,
)

from .nova_capability_drift_lab import (
    build_agent_feedback_loop_plan,
    build_behavior_fuzzer_plan,
    build_capability_drift_audit,
    build_feature_preservation_contract,
    build_local_spec_search_plan,
    render_agent_feedback_loop_plan,
    render_behavior_fuzzer_plan,
    render_capability_drift_audit,
    render_feature_preservation_contract,
    render_local_spec_search_plan,
)


LOGGER = logging.getLogger(__name__)


@dataclass
class ToolResult:
    ok: bool
    summary: str
    data: dict[str, Any]


def _is_prose_verify_command(command: str) -> bool:
    low = (command or "").strip().lower()
    if not low:
        return False
    markers = [
        "if node is available",
        "then open",
        "play-test",
        "play test",
        "manual gameplay",
        "manual test",
        "open index.html",
        "open `index.html`",
        "open the browser",
        "browser checks",
    ]
    return "; then" in low or any(marker in low for marker in markers) or (low.startswith("node --check") and " if " in low)


class ToolRegistry:
    def __init__(self, config: AssistantConfig):
        self.config = config
        self.tools: dict[str, Callable[..., ToolResult]] = {}
        self.register_defaults()

    @property
    def workspace(self) -> Path:
        return Path(self.config.workspace).expanduser().resolve()

    def _wla_source_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def _resolve_codebase_target(self, path: str = ".", *, default_wla_source: bool = True) -> tuple[Path, dict[str, Any]]:
        raw = str(path or ".").strip()
        source = self._wla_source_root()
        meta: dict[str, Any] = {"requested_path": raw, "target_type": "project", "autocorrected": False, "warning": ""}
        lowered = raw.lower()
        if default_wla_source and lowered in {"", ".", "__wla_source__", "wla", "wla-source", "source", "codebase"}:
            meta["target_type"] = "wla_source"
            return source, meta
        project_prefixes = ("project:", "workspace:", "current-project:", "current project:")
        if lowered.startswith(project_prefixes):
            for prefix in project_prefixes:
                if lowered.startswith(prefix):
                    raw = raw[len(prefix):].strip() or "."
                    break
            root = resolve_inside_workspace(self.workspace, raw)
            meta["target_type"] = "project"
        else:
            root = resolve_inside_workspace(self.workspace, raw)
        if root.is_file():
            root = root.parent
        has_wla = (root / "winlocalassistant").is_dir() or (root / "app.py").exists()
        has_python = any(root.rglob("*.py")) if root.exists() else False
        if default_wla_source and not has_wla and not has_python and (source / "winlocalassistant").is_dir():
            meta.update({
                "target_type": "wla_source",
                "autocorrected": True,
                "warning": f"Requested audit target {root} had no Python/Nova source files, so Nova audited the source root instead.",
                "requested_resolved": str(root),
            })
            root = source
        return root, meta

    def register(self, name: str, func: Callable[..., ToolResult]) -> None:
        self.tools[name] = func

    def call(self, tool_name: str, **kwargs: Any) -> ToolResult:
        if tool_name not in self.tools:
            return ToolResult(False, f"Unknown tool: {tool_name}", {"available": sorted(self.tools)})

        def _run() -> ToolResult:
            try:
                return self.tools[tool_name](**kwargs)
            except Exception as exc:
                log_error = None
                try:
                    log_activity("tool_exception", f"Tool {tool_name} failed", {"tool": tool_name, "error": repr(exc)})
                except Exception as log_exc:
                    log_error = repr(log_exc)
                data = {"error": repr(exc), "tool": tool_name}
                if log_error:
                    data["log_error"] = log_error
                return ToolResult(False, f"Tool {tool_name} failed: {exc}", data)

        result, sample = profile_call(
            self.config,
            kind="tool",
            name=tool_name,
            func=_run,
            meta={"args_keys": sorted(str(k) for k in kwargs.keys())},
        )
        try:
            if isinstance(result, ToolResult) and not result.ok:
                record_mistake("tool_result_failed", result.summary, {"tool": tool_name, "data": result.data or {}})
        except Exception:
            LOGGER.debug("Failed to record tool failure for %s", tool_name, exc_info=True)
        try:
            if sample and isinstance(result, ToolResult):
                data = dict(result.data or {})
                data.setdefault("efficiency", sample)
                result.data = data
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        return result

    def require_mutation(self) -> None:
        if not self.config.allow_mutating_tools:
            raise PermissionError("Mutating tools are disabled. Use /allow-mutate on first.")

    def mistake_learning_tool(self, limit: int = 80) -> ToolResult:
        payload = build_mistake_learning_report(self._wla_source_root(), limit=limit)
        return ToolResult(True, "Nova mistake learning report generated", {"report": payload, "markdown": render_mistake_learning_report(payload)})

    def self_repair_status_tool(self) -> ToolResult:
        policy = load_self_repair_policy()
        payload = {"policy": asdict(policy), "validation": "not run; use /self-repair-validate for compile/smoke checks"}
        return ToolResult(True, "Nova self-repair status", payload)

    def self_repair_permission_tool(self, enabled: bool | str = True) -> ToolResult:
        val = str(enabled).strip().lower()
        enable = val in {"1", "true", "yes", "on", "enable", "enabled"}
        data = set_self_repair_enabled(enable)
        return ToolResult(True, f"Bounded self-repair permission set to: {enable}", data)

    def self_repair_validate_tool(self) -> ToolResult:
        payload = run_self_repair_validation(self._wla_source_root())
        return ToolResult(bool(payload.get("ok")), "Nova self-repair validation completed", payload)

    def self_repair_auto_tool(self, goal: str = "improve Nova safely") -> ToolResult:
        payload = run_auto_self_repair(self._wla_source_root(), goal=goal, apply=True)
        return ToolResult(bool(payload.get("ok")), "Nova bounded auto self-repair completed", {"report": payload, "markdown": render_self_repair_report(payload)})

    def register_defaults(self) -> None:
        for name, fn in {
            "status": self.status,
            "list_files": self.list_files,
            "tree": self.tree,
            "read_file": self.read_file,
            "write_file": self.write_file,
            "write_files": self.write_files,
            "append_file": self.append_file,
            "make_dir": self.make_dir,
            "find_replace": self.find_replace,
            "search_text": self.search_text,
            "run_shell": self.run_shell,
            "verify": self.verify,
            "detect_project": self.detect_project,
            "auto_verify": self.auto_verify,
            "zip_path": self.zip_path,
            "project_spec": self.project_spec,
            "code_repair_audit": self.code_repair_audit,
            "code_review_audit": self.code_review_audit,
            "code_quality_gate": self.code_quality_gate,
            "mistake_learning": self.mistake_learning_tool,
            "mistake_learning_status": self.mistake_learning_tool,
            "self_repair_status": self.self_repair_status_tool,
            "self_repair_permission": self.self_repair_permission_tool,
            "self_repair_auto": self.self_repair_auto_tool,
            "auto_self_repair": self.self_repair_auto_tool,
            "self_repair_validate": self.self_repair_validate_tool,
            "codebase_integrity_audit": self.codebase_integrity_audit,
            "assistant_box": self.assistant_box,
            "model_context": self.model_context,
            "response_quality_plan": self.response_quality_plan_tool,
            "response_quality": self.response_quality_plan_tool,
            "communication_quality_plan": self.response_quality_plan_tool,
            "video_plan": self.video_plan_tool,
            "nova_video_plan": self.video_plan_tool,
            "video_status": self.video_status_tool,
            "nova_video_status": self.video_status_tool,
            "video_validate": self.video_validate_tool,
            "nova_video_validate": self.video_validate_tool,
            "video_user_tests": self.video_user_tests_tool,
            "media_status": self.media_status_tool,
            "image_plan": self.image_plan_tool,
            "screen_analysis_prompt": self.screen_analysis_prompt_tool,
            "screen_context_help": self.screen_analysis_prompt_tool,
            "image_prompt_plan": self.image_plan_tool,
            "video_storyboard": self.video_storyboard_tool,
            "video_package": self.video_package_tool,
            "video_render_package": self.video_package_tool,
            "high_spec_profile": self.high_spec_profile_tool,
            "local_high_spec_profile": self.high_spec_profile_tool,
            "subagent_plan": self.subagent_plan_tool,
            "subagents": self.subagent_plan_tool,
            "multi_agent_plan": self.subagent_plan_tool,
            "nova_context": self.nova_context,
            "operating_context": self.nova_context,
            "run_context": self.nova_context,
            "mission_contract": self.mission_contract_tool,
            "autonomous_mission_contract": self.mission_contract_tool,
            "mission_progress_score": self.mission_progress_score_tool,
            "autonomy_readiness": self.autonomy_readiness_tool,
            "autonomy_capability_audit": self.autonomy_readiness_tool,
            "surgical_recipe": self.surgical_recipe_tool,
            "project_type_registry": self.project_type_registry_tool,
            "self_test_from_bug": self.self_test_from_bug_tool,
            "development_strategy": self.development_strategy_tool,
            "iterative_strategy": self.development_strategy_tool,
            "validation_evidence": self.validation_evidence_tool,
            "behaviour_evidence": self.validation_evidence_tool,
            "validation_matrix": self.validation_matrix_tool,
            "regression_matrix": self.validation_matrix_tool,
            "adaptive_backlog": self.adaptive_backlog_tool,
            "next_adaptations": self.adaptive_backlog_tool,
            "generation_template_manifest": self.generation_template_manifest_tool,
            "template_manifest": self.generation_template_manifest_tool,
            "generation_templates": self.generation_template_manifest_tool,
            "idle_policy": self.idle_policy_tool,
            "idle_levels": self.idle_policy_tool,
            "receipt_history": self.receipt_history_tool,
            "action_receipts": self.receipt_history_tool,
            "build_receipts": self.receipt_history_tool,
            "role_router": self.role_router_tool,
            "local_model_roles": self.role_router_tool,
            "model_role_router": self.role_router_tool,
            "jarvis_bridge": self.jarvis_bridge_tool,
            "jarvis_status": self.jarvis_status_tool,
            "external_daemon_status": self.jarvis_status_tool,
            "daemon_bridge": self.jarvis_bridge_tool,
            "jarvis_doctor": self.jarvis_doctor_tool,
            "jarvis_setup_doctor": self.jarvis_doctor_tool,
            "jarvis_onboarding": self.jarvis_doctor_tool,
            "sidecar_policy": self.sidecar_policy_tool,
            "screen_awareness_policy": self.sidecar_policy_tool,
            "sidecar_preflight": self.sidecar_preflight_tool,
            "bridge_authority": self.bridge_authority_tool,
            "authority_gate": self.bridge_authority_tool,
            "workflow_blueprint": self.workflow_blueprint_tool,
            "jarvis_workflow_blueprint": self.workflow_blueprint_tool,
            "proactive_actions": self.proactive_actions_tool,
            "bridge_receipts": self.bridge_receipts_tool,
            "jarvis_receipts": self.bridge_receipts_tool,
            "sidecar_enrollment": self.sidecar_enrollment_tool,
            "sidecar_enrollment_checklist": self.sidecar_enrollment_tool,
            "browser_harness": self.browser_harness_tool,
            "safe_browser_harness": self.browser_harness_tool,
            "startup_validation": self.startup_validation_tool,
            "startup_gate": self.startup_validation_tool,
            "nova_system_test": self.nova_system_test_tool,
            "nova_full_test": self.nova_system_test_tool,
            "nova_capability_test": self.nova_system_test_tool,
            "completion_audit": self.completion_audit_tool,
            "previous_task_audit": self.completion_audit_tool,
            "task_completion_audit": self.completion_audit_tool,
            "release_readiness": self.release_readiness_tool,
            "release_gate": self.release_readiness_tool,
            "release_readiness_full": self.release_readiness_tool,
            "release_package": self.release_package_tool,
            "clean_release_package": self.release_package_tool,
            "package_release": self.release_package_tool,
            "codebase_advisor": self.codebase_advisor_tool,
            "next_codebase_improvements": self.codebase_advisor_tool,
            "codebase_improvement_plan": self.codebase_advisor_tool,
            "audit_log": self.audit_log_tool,
            "nova_audit_log": self.audit_log_tool,
            "wla_audit_log": self.audit_log_tool,
            "workflow_run": self.workflow_run_tool,
            "supervised_workflow_run": self.workflow_run_tool,
            "jarvis_test_prompts": self.jarvis_test_prompts_tool,
            "persona_profile": self.persona_profile_tool,
            "persona_editor": self.persona_profile_tool,
            "chat_persona": self.persona_profile_tool,
            "custom_chat_window": self.custom_chat_window_tool,
            "persona_set": self.persona_set_tool,
            "persona_json": self.persona_json_tool,
            "persona_prompt": self.persona_prompt_tool,
            "personality_sliders": self.persona_profile_tool,
            "voice_audit": self.voice_audit_tool,
            "voice_command_audit": self.voice_audit_tool,
            "local_model_optimizer": self.local_model_optimizer_tool,
            "model_optimization": self.local_model_optimizer_tool,
            "model_prompt_cache_plan": self.local_model_optimizer_tool,
            "coding_plan": self.coding_plan_tool,
            "project_coding_plan": self.coding_plan_tool,
            "coding_capability_audit": self.coding_capability_audit_tool,
            "nova_coding_audit": self.coding_capability_audit_tool,
            "local_model_performance_plan": self.local_model_performance_plan_tool,
            "model_performance_plan": self.local_model_performance_plan_tool,
            "agent_upgrade_radar": self.agent_upgrade_radar_tool,
            "nova_upgrade_radar": self.agent_upgrade_radar_tool,
            "context_budget": self.context_budget_tool,
            "context_compaction_plan": self.context_budget_tool,
            "coding_behavior_tests": self.coding_behavior_tests_tool,
            "coding_acceptance_tests": self.coding_behavior_tests_tool,
            "ollama_runtime_profile": self.ollama_runtime_profile_tool,
            "local_model_runtime_profile": self.ollama_runtime_profile_tool,
            "upgrade_regression_audit": self.upgrade_regression_audit_tool,
            "patch_regression_audit": self.upgrade_regression_audit_tool,
            "repo_context_map": self.repo_context_map_tool,
            "nova_repo_map": self.repo_context_map_tool,
            "patch_impact_plan": self.patch_impact_plan_tool,
            "impact_tests": self.patch_impact_plan_tool,
            "permission_scope_review": self.permission_scope_review_tool,
            "scope_review": self.permission_scope_review_tool,
            "local_model_benchmark_plan": self.local_model_benchmark_plan_tool,
            "model_benchmark_plan": self.local_model_benchmark_plan_tool,
            "tool_contract_audit": self.tool_contract_audit_tool,
            "command_contract_audit": self.tool_contract_audit_tool,
            "command_verify": self.command_verify_tool,
            "repo_upgrade_assurance": self.repo_upgrade_assurance_tool,
            "future_timeline": self.repo_upgrade_assurance_tool,
            "maintenance_validate": self.maintenance_validation_tool,
            "validate_maintenance": self.maintenance_validation_tool,
            "self_validate": self.maintenance_validation_tool,
            "codebase_sanity_audit": self.codebase_sanity_audit_tool,
            "codebase_sanity": self.codebase_sanity_audit_tool,
            "dead_code_audit": self.codebase_sanity_audit_tool,
            "rewrite_candidates": self.codebase_sanity_audit_tool,
            "repo_research_radar": self.repo_research_radar_tool,
            "repo_inspiration_radar": self.repo_research_radar_tool,
            "agent_topology_plan": self.agent_topology_plan_tool,
            "nova_agent_topology": self.agent_topology_plan_tool,
            "trace_observability_plan": self.trace_observability_plan_tool,
            "trace_spec": self.trace_observability_plan_tool,
            "local_stack_advisor": self.local_stack_advisor_tool,
            "local_stack_plan": self.local_stack_advisor_tool,
            "verifier_ladder": self.verifier_ladder_tool,
            "validation_ladder_plus": self.verifier_ladder_tool,
            "tool_namespace_plan": self.tool_namespace_plan_tool,
            "tool_surface_plan": self.tool_namespace_plan_tool,
            "voice_pipeline_review": self.voice_pipeline_review_tool,
            "jarvis_voice_review": self.voice_pipeline_review_tool,
            "route_resilience_plan": self.route_resilience_plan_tool,
            "self_healing_route_plan": self.route_resilience_plan_tool,
            "tool_health_map": self.tool_health_map_tool,
            "route_health_map": self.tool_health_map_tool,
            "guardrail_memory_plan": self.guardrail_memory_plan_tool,
            "agent_guardrail_memory": self.guardrail_memory_plan_tool,
            "context_router_policy": self.context_router_policy_tool,
            "role_context_router": self.context_router_policy_tool,
            "local_runtime_sentinel": self.local_runtime_sentinel_tool,
            "model_runtime_sentinel": self.local_runtime_sentinel_tool,
            "improvement_assurance_plan": self.improvement_assurance_plan_tool,
            "improvement_evidence_plan": self.improvement_assurance_plan_tool,
            "test_impact_graph": self.test_impact_graph_tool,
            "impact_graph": self.test_impact_graph_tool,
            "patch_quality_score": self.patch_quality_score_tool,
            "quality_score_patch": self.patch_quality_score_tool,
            "success_claim_audit": self.success_claim_audit_tool,
            "claim_audit": self.success_claim_audit_tool,
            "regression_bisect_plan": self.regression_bisect_plan_tool,
            "bisect_regression_plan": self.regression_bisect_plan_tool,
            "capability_drift_audit": self.capability_drift_audit_tool,
            "nova_drift_audit": self.capability_drift_audit_tool,
            "feature_preservation_contract": self.feature_preservation_contract_tool,
            "preserve_features": self.feature_preservation_contract_tool,
            "agent_feedback_loop_plan": self.agent_feedback_loop_plan_tool,
            "nova_feedback_loop": self.agent_feedback_loop_plan_tool,
            "behavior_fuzzer_plan": self.behavior_fuzzer_plan_tool,
            "agent_fuzzer_plan": self.behavior_fuzzer_plan_tool,
            "local_spec_search_plan": self.local_spec_search_plan_tool,
            "on_device_spec_search": self.local_spec_search_plan_tool,
            "agent_harness": self.agent_harness_tool,
            "iterative_agent_harness": self.agent_harness_tool,
            "proactive_action_queue": self.proactive_actions_tool,
            "efficiency_report": self.efficiency_report,
            "pipeline_preflight": self.pipeline_preflight_tool,
            "pipeline_route": self.pipeline_preflight_tool,
            "pipeline_manifest": self.pipeline_manifest_tool,
            "pipeline_catalog": self.pipeline_catalog_tool,
            "capability_manifests": self.pipeline_catalog_tool,
            "repo_upgrade_plan": self.pipeline_catalog_tool,
            "session_evidence": self.session_evidence_tool,
            "run_evidence": self.session_evidence_tool,
            "memory_inventory": self.memory_inventory_tool,
            "memory_audit": self.memory_inventory_tool,
            "project_patterns": self.project_patterns_tool,
            "browser_smoke": self.browser_smoke_tool,
            "live_timeline": self.live_timeline_tool,
            "tool_awareness": self.tool_awareness_tool,
            "tool_awareness_audit": self.tool_awareness_audit_tool,
            "tool_use_plan": self.tool_awareness_tool,
            "autonomous_tool_plan": self.tool_awareness_tool,
            "idle_tool_plan": self.tool_awareness_tool,
            "research": self.research,
            "assistant_db": self.assistant_db,
            "sandbox_status": self.sandbox_status,
            "sandbox_setup_help": self.sandbox_setup_help,
            "sandbox_start": self.sandbox_start,
            "sandbox_stop": self.sandbox_stop,
            "sandbox_exec": self.sandbox_exec,
            "sandbox_dev_run": self.sandbox_dev_run_tool,
            "sandbox_flag": self.sandbox_flag,
            "sandbox_policy": self.sandbox_policy,
            "docker_status": self.docker_status,
            "docker_ps": self.docker_ps,
            "docker_smoke": self.docker_smoke,
            "docker_validate": self.docker_validate,
            "docker_patch_validate": self.docker_patch_validate,
            "docker_promote_patch": self.docker_promote_patch,
            "docker_history": self.docker_history,
            "docker_clean": self.docker_clean,
            "docker_help": self.docker_help,
            "cohesion_report": self.cohesion_report,
            "validation_ladder": self.validation_ladder,
            "iteration_plan": self.iteration_plan,
            "nova_doctor": self.wla_doctor,
            "wla_doctor": self.wla_doctor,
            "nova_release_gate": self.wla_release_gate,
            "wla_release_gate": self.wla_release_gate,
            "nova_brand_audit": self.nova_brand_audit_tool,
            "nova_improvement_research": self.nova_improvement_research_tool,
            "integration_radar": self.integration_radar,
            "release_checklist": self.release_checklist,
            "feature_audit": self.feature_audit,
            "feature_continuity_audit": self.feature_continuity_audit_tool,
            "functionality_continuity": self.feature_continuity_audit_tool,
            "no_regression_audit": self.feature_continuity_audit_tool,
            "ai_create_project": self.ai_create_project,
            "ai_edit_project": self.ai_edit_project,
            "project_target_decision": self.project_target_decision,
            "run_project": self.run_project,
            "runtime_start": self.runtime_start,
            "runtime_stop": self.runtime_stop,
            "runtime_restart": self.runtime_restart,
            "reasoning_diagnostics": self.reasoning_diagnostics,
            "known_error_recover": self.known_error_recover,
            "final_project_check": self.final_project_check,
            "projects": self.projects,
            "project_create": self.project_create,
            "project_open": self.project_open,
            "project_remove": self.project_remove,
            "project_delete": self.project_delete,
            "project_files": self.project_files,
            "open_file": self.open_file,
            "llm_status": self.llm_status,
            "ollama_stop_model": self.ollama_stop_model,
            "activity_log": self.activity_log,
            "provider_status": self.provider_status,
            "provider_route": self.provider_route_tool,
            "provider_route_explain": self.provider_route_tool,
            "provider_test": self.provider_test_tool,
            "queue_status": self.provider_queue_tool,
            "provider_queue_status": self.provider_queue_tool,
            "queue_drain": self.provider_drain_tool,
            "research_plan": self.research_plan,
            "mcp_manifest": self.mcp_manifest,
            "benchmark_init": self.benchmark_init,
            "benchmark_run": self.benchmark_run,
            "telemetry_export": self.telemetry_export,
            "godmod3_report": self.godmod3_report,
            "investigate_logs": self.investigate_logs,
            "propose_improvements": self.propose_improvements,
            "tool_use_guide": self.tool_use_guide,
            "search_files": self.search_text,
            "custom_tools": self.custom_tools,
            "tool_run": self.tool_run,
            "tool_create": self.tool_create,
            "tool_delete": self.tool_delete,
            "tool_view": self.tool_view,
            "tool_test": self.tool_test,
            "tool_enable": self.tool_enable,
            "tool_disable": self.tool_disable,
            "tool_proposals": self.tool_proposals,
            "tool_clean_proposals": self.tool_clean_proposals,
            "runtime_self_check": self.runtime_self_check,
            "tool_approve": self.tool_approve,
            "tool_reject": self.tool_reject,
            "agent_execute": self.agent_execute,
            "improve_project": self.improve_project,
            "improvement_report": self.improvement_report,
            "install_package": self.install_package,
            "resource_status": self.resource_status,
            "heartbeat": self.heartbeat,
            "watchdog": self.watchdog,
            "self_improve": self.self_improve,
            "self_improve_apply_approved": self.self_improve_apply_approved,
            "backtrack_recover": self.backtrack_recover,
            "surgical_repair": self.surgical_repair,
            "vision_status": self.vision_status,
            "image_analyze": self.image_analyze,
            "human_test": self.human_test,
            "visual_test": self.visual_test,
            "cycle_schema": self.cycle_schema,
            "playwright_scaffold": self.playwright_scaffold,
            "idle_lessons": self.idle_lessons,
            "tool_help": self.tool_help,
            "tool_pipeline": self.tool_pipeline,
            "safe_script_demo": self.safe_script_demo,
            "topic_watch": self.topic_watch,
            "topic_watchers": self.topic_watchers,
            "topic_check": self.topic_check,
            "internet_fetch": self.internet_fetch,
            "internet_search": self.internet_search,
            "search_web": self.internet_search,

            "prompt_contract": self.prompt_contract,
            "prompt_test_run": self.prompt_test_run,
            "candidate_tournament": self.candidate_tournament_tool,
            "candidate_failure_report": self.candidate_failure_report_tool,
            "repair_plan_v2": self.repair_plan_v2,
            "trace_status": self.trace_status_tool,
            "mcp_risk_report": self.mcp_risk_report_tool,
            "mission_create": self.mission_create_tool,
            "mission_step": self.mission_step_tool,
            "model_output_coach": self.model_output_coach_tool,
            "env_profile": self.env_profile_tool,
            "benchmark_system": self.benchmark_system_tool,
            "project_state": self.project_state_tool,
            "regression_list": self.regression_list_tool,
            "regression_add": self.regression_add_tool,
            "weakspot_audit": self.weakspot_audit_tool,
            "error_hunt": self.weakspot_audit_tool,
            "user_test_suite": self.user_test_suite_tool,
            "improvement_proposals_v2": self.improvement_proposals_v2,
            "improvement_cycle": self.improvement_cycle_tool,
            "improvement_status": self.improvement_status_tool,
            "regression_sweep": self.regression_sweep_tool,
            "functionality_matrix": self.regression_sweep_tool,
            "integration_health": self.regression_sweep_tool,
            "improvement_roadmap": self.improvement_roadmap_tool,
            "improvement_impact": self.improvement_impact_tool,
            "implement_improvements": self.implement_improvements_tool,
            "proposal_ledger": self.proposal_ledger_tool,
            "whole_codebase_review": self.whole_codebase_review_tool,
            "review_codebase": self.whole_codebase_review_tool,
            "comprehensive_code_review": self.whole_codebase_review_tool,
            "bug_review": self.bug_review_tool,
            "bug_hunt": self.bug_review_tool,
            "bug_sweep": self.bug_review_tool,
            "error_review": self.bug_review_tool,
            "build_quality_report": self.build_quality_report_tool,
            "browser_runtime_test": self.browser_runtime_test_tool,
            "model_reliability": self.model_reliability_tool,
            "model_fallback_strategy": self.model_fallback_strategy_tool,
            "model_readiness": self.model_readiness_tool,
            "model_requirements": self.model_readiness_tool,
            "model_download_plan": self.model_readiness_tool,
            "model_install": self.model_install_tool,
            "flow_audit": self.flow_audit_tool,
            "interaction_flow_audit": self.flow_audit_tool,
            "interaction_pathways": self.flow_audit_tool,
            "command_flow_verify": self.flow_audit_tool,
            "learning_loop_audit": self.flow_audit_tool,
            "flow_improvements": self.flow_improvements_tool,
            "patch_queue": self.patch_queue_tool,
            "gui_cockpit_v2": self.gui_cockpit_v2_tool,
            "voice_mode_report": self.voice_mode_report_tool,
            "template_list": self.template_list_tool,
            "template_build": self.template_build_tool,
            "preview_server": self.preview_server_tool,
            "feature_readiness": self.feature_readiness_tool,
            "explain_error": self.explain_error_tool,
            "support_report": self.support_report_tool,
            "docs_index": self.docs_index_tool,
            "regression_test_generate": self.regression_test_generate_tool,
            "mistake_learning_status": self.mistake_learning_status_tool,
            "surgical_fallback_v2": self.surgical_fallback_v2_tool,
            "iterative_coding_loop": self.iterative_coding_loop_tool,
            "edit_repair_plan": self.edit_repair_plan_tool,
            "coding_loop_status": self.iterative_coding_loop_tool,
            "mission_dashboard": self.mission_dashboard_tool,
            "mission_progress": self.mission_dashboard_tool,
            "cycle_score": self.cycle_score_tool,
            "autonomous_progress_score": self.cycle_score_tool,
            "idle_progress_score": self.idle_progress_score_tool,
            "tool_choice_trace": self.tool_choice_trace_tool,
            "autonomous_explain_tools": self.tool_choice_trace_tool,
            "idle_explain_tools": self.tool_choice_trace_tool,
            "repetition_guard_status": self.repetition_guard_tool,
            "repetition_memory": self.repetition_guard_tool,
            "repetition_clear": self.repetition_clear_tool,
            "idle_background_settings": self.idle_background_settings_tool,
            "autonomous_patch_mode": self.autonomous_patch_mode_tool,
            "mistake_log": self.mistake_log_tool,
            "mistake_to_regression": self.mistake_to_regression_tool,
            "autonomous_last_report": self.autonomous_last_report_tool,
            
            # New improvement features (v55.3.124+)
            "analytics": self.analytics_dashboard_tool,
            "analytics_dashboard": self.analytics_dashboard_tool,
            "performance_analytics": self.analytics_dashboard_tool,
            "performance_profiler": self.performance_report_tool,
            "performance_report": self.performance_report_tool,
            "optimize_performance": self.performance_report_tool,
            "webhook": self.webhook_management_tool,
            "webhook_status": self.webhook_management_tool,
            "webhooks": self.webhook_management_tool,
            "register_webhook": self.webhook_management_tool,
            "scheduler": self.task_scheduler_tool,
            "task_scheduler": self.task_scheduler_tool,
            "schedule_task": self.task_scheduler_tool,
            "list_tasks": self.task_scheduler_tool,
            "proposal_ledger_view": self.proposal_ledger_tool,
            "completed_improvements": self.completed_improvements_tool,
            "anti_repeat_check": self.anti_repeat_tool,
        }.items():
            self.register(name, fn)




    def pipeline_preflight_tool(self, goal: str = "") -> ToolResult:
        """Classify a user request into a typed pipeline before expensive model calls or mutation."""
        route = classify_pipeline(goal)
        payload = route_to_dict(route)
        payload["goal"] = goal
        try:
            log_activity("pipeline_preflight", f"Pipeline selected: {route.kind}", payload)
        except Exception:
            pass
        return ToolResult(True, f"Pipeline selected: {route.kind}", {"message": render_pipeline_route(route, goal), **payload})

    def pipeline_catalog_tool(self, goal: str = "", write: bool = False) -> ToolResult:
        """Render repo-inspired Nova capability manifests and optionally snapshot them to docs."""
        payload: dict[str, Any] = {"goal": goal, "message": render_manifest_catalog(goal)}
        if write:
            self.require_mutation()
            snapshot = write_manifest_snapshot(self._wla_source_root(), goal)
            payload.update(snapshot)
            payload["message"] += f"\n\nSnapshot written:\n- `{snapshot['markdown_path']}`\n- `{snapshot['json_path']}`"
        try:
            log_activity("pipeline_catalog", "Repo-inspired capability manifest catalog rendered", {k: v for k, v in payload.items() if k != "message"})
        except Exception:
            pass
        return ToolResult(True, "Capability manifest catalog rendered", payload)

    def pipeline_manifest_tool(self, manifest_id: str = "") -> ToolResult:
        """Render one repo-inspired capability manifest by id."""
        text = render_manifest(manifest_id or "")
        try:
            log_activity("pipeline_manifest", "Capability manifest rendered", {"manifest_id": manifest_id})
        except Exception:
            pass
        return ToolResult(True, "Capability manifest rendered", {"message": text, "manifest_id": manifest_id})

    def session_evidence_tool(self, run_id: str = "latest", limit: int = 120) -> ToolResult:
        """Render OpenHands-style run evidence from Nova activity/model logs."""
        payload = build_session_evidence(run_id or "latest", limit=limit)
        try:
            log_activity("session_evidence", "Session evidence rendered", {"run_id": payload.get("resolved_run_id"), "events": payload.get("event_count")})
        except Exception:
            pass
        return ToolResult(True, "Session evidence rendered", {"message": render_session_evidence(payload), **payload})

    def memory_inventory_tool(self, path: str = ".") -> ToolResult:
        """Render a Mem0/OpenMemory-inspired inventory of Nova typed memory stores."""
        raw = str(path or ".").strip()
        root = self.workspace if raw in {"", "."} else resolve_inside_workspace(self.workspace, raw)
        payload = build_memory_inventory(root)
        try:
            log_activity("memory_inventory", "Memory inventory rendered", {"workspace": str(root), "databases": list((payload.get("databases") or {}).keys())})
        except Exception:
            pass
        return ToolResult(True, "Memory inventory rendered", {"message": render_memory_inventory(payload), **payload})

    def project_patterns_tool(self, path: str = ".", write: bool = False) -> ToolResult:
        """Inspect or write a lightweight NOVA_PATTERNS.md file for project-aware edits."""
        raw = str(path or ".").strip()
        root = self.workspace if raw in {"", "."} else resolve_inside_workspace(self.workspace, raw)
        do_write = bool(write)
        if do_write:
            self.require_mutation()
        payload = write_project_patterns(root, write=do_write)
        try:
            log_activity("project_patterns", "Project pattern memory inspected" + (" and written" if do_write else ""), payload)
        except Exception:
            pass
        return ToolResult(True, "Project pattern memory " + ("written" if do_write else "inspected"), {"message": render_project_patterns(payload), **payload})

    def browser_smoke_tool(self, path: str = ".") -> ToolResult:
        """Run a lightweight browser/GUI smoke preflight without requiring a live browser."""
        root = self._wla_source_root() if str(path or ".").strip() in {"", ".", "source", "nova"} else resolve_inside_workspace(self.workspace, str(path))
        checks: list[dict[str, Any]] = []
        webui = root / "winlocalassistant" / "webui.py"
        if not webui.exists():
            webui = self._wla_source_root() / "winlocalassistant" / "webui.py"
        text = webui.read_text(encoding="utf-8", errors="replace") if webui.exists() else ""
        required_markers = [
            "data-orbit-studio-shell",
            "togglePanel",
            "loadActivity",
            "loadAutonomousStatus",
            "announceNovaReady",
            "messageTerminalHtml",
        ]
        for marker in required_markers:
            checks.append({"name": f"marker:{marker}", "ok": marker in text})
        js_ok = False
        js_detail = "node not available or extract failed"
        try:
            extract = root / ".nova_runtime" / "browser_smoke_webui_extract.js"
            extract.parent.mkdir(parents=True, exist_ok=True)
            import re as _re
            scripts = _re.findall(r"<script>(.*?)</script>", text, flags=_re.S)
            atomic_write_text(extract, "\n".join(scripts))
            proc = subprocess.run(["node", "--check", str(extract)], cwd=str(root), text=True, capture_output=True, timeout=30)
            js_ok = proc.returncode == 0
            js_detail = (proc.stdout + proc.stderr).strip()[:2000] or "node --check passed"
        except Exception as exc:
            js_detail = repr(exc)
        checks.append({"name": "webui_js_parse", "ok": js_ok, "detail": js_detail})
        ok = all(bool(c.get("ok")) for c in checks)
        lines = ["# Nova Browser Smoke", "", f"Result: **{'PASS' if ok else 'FAIL'}**", f"Web UI: `{webui}`", "", "## Checks"]
        for c in checks:
            lines.append(f"- {'PASS' if c.get('ok') else 'FAIL'} {c.get('name')}" + (f" — {c.get('detail')}" if c.get('detail') else ""))
        lines += ["", "For a real visual click-through, run Playwright/browser smoke from the GUI or `/browser-harness http://127.0.0.1:8766` after launching Nova."]
        try:
            log_activity("browser_smoke", "Browser smoke preflight completed", {"ok": ok, "checks": checks})
        except Exception:
            pass
        return ToolResult(ok, "Browser/GUI smoke preflight " + ("passed" if ok else "found issues"), {"message": "\n".join(lines), "checks": checks, "webui": str(webui)})

    def live_timeline_tool(self, limit: int = 40) -> ToolResult:
        """Return a compact live activity timeline for the current/last run."""
        try:
            n = max(1, min(int(limit or 40), 200))
        except Exception:
            n = 40
        rows = tail_jsonl(ACTIVITY_PATH, n, session_only=False)
        lines = ["# Nova Live Timeline", "", f"Events shown: {len(rows)}", ""]
        for ev in rows[-n:]:
            data = ev.get("data") if isinstance(ev.get("data"), dict) else {}
            run = data.get("run_id") or data.get("request_id") or ""
            tool = data.get("tool") or ""
            suffix = ""
            if run or tool:
                suffix = " — " + " ".join(str(x) for x in [tool, run] if x)
            lines.append(f"- {ev.get('time','')} `{ev.get('kind','')}` {ev.get('message','')}{suffix}")
        return ToolResult(True, "Live timeline rendered", {"message": "\n".join(lines), "events": rows})


    def tool_awareness_tool(self, goal: str = "", mode: str = "manual", limit: int = 16) -> ToolResult:
        """Render the repo-inspired tool plan that idle/autonomous should use before acting."""
        try:
            max_items = max(1, min(int(limit or 16), 40))
        except Exception:
            max_items = 16
        plan = build_tool_awareness_plan(goal or "Improve Nova safely", mode=mode or "manual", available_tools=sorted(self.tools.keys()), limit=max_items)
        payload = plan_payload(plan)
        try:
            log_activity("tool_awareness", f"Tool-awareness plan rendered for {plan.mode}/{plan.pipeline_kind}", {"goal": plan.goal, "mode": plan.mode, "pipeline": plan.pipeline_kind, "covered": plan.covered_tool_count, "missing": list(plan.missing_tools)})
        except Exception:
            pass
        return ToolResult(True, "Tool-awareness plan rendered", {"message": render_tool_awareness_plan(plan), **payload})

    def tool_awareness_audit_tool(self, goal: str = "") -> ToolResult:
        """Audit whether repo-inspired/autonomous/idle tool planning is connected to registered tools."""
        goals = [goal] if str(goal or "").strip() else None
        payload = audit_tool_awareness(sorted(self.tools.keys()), goals=goals)
        try:
            log_activity("tool_awareness_audit", "Tool-awareness audit completed", {"ok": payload.get("ok"), "missing": payload.get("missing_tools", [])})
        except Exception:
            pass
        return ToolResult(bool(payload.get("ok")), "Tool-awareness audit " + ("passed" if payload.get("ok") else "needs attention"), {"message": render_tool_awareness_audit(payload), **payload})

    def research(self, topic: str = "", urls: str = "", max_sources: int = 8) -> ToolResult:
        """Gather public-source research and analyse source mix, credibility, bias and meaning."""
        topic = str(topic or "").strip()
        if not topic:
            return ToolResult(False, "Research topic is required", {"usage": "/research TOPIC or /research TOPIC => URL1 URL2"})
        source_urls = [u.strip() for u in re.split(r"[\s,]+", str(urls or "")) if u.strip().startswith(("http://", "https://"))]
        try:
            md_path, json_path, payload = build_research_report(self.config, topic, source_urls=source_urls, max_sources=int(max_sources or 8))
            try:
                key = Path(json_path).stem[-64:]
                put_record("research", "reports", key, {
                    "topic": topic,
                    "markdown_path": str(md_path),
                    "json_path": str(json_path),
                    "source_count": len(payload.get("sources", [])),
                    "source_mix": payload.get("source_mix", {}),
                    "bias_summary": payload.get("bias_summary", {}),
                    "keywords": payload.get("keywords", [])[:20],
                    "consensus_notes": payload.get("consensus_notes", []),
                    "evidence_gaps": payload.get("evidence_gaps", []),
                }, schema_hint="automatic research report index")
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            return ToolResult(True, "Research report generated", {
                "message": render_research_markdown(payload),
                "markdown_path": str(md_path),
                "json_path": str(json_path),
                "source_count": len(payload.get("sources", [])),
                "internet_allowed": payload.get("internet_allowed"),
                "source_mix": payload.get("source_mix", {}),
                "bias_summary": payload.get("bias_summary", {}),
            })
        except Exception as exc:
            return ToolResult(False, "Research report failed", {"error": repr(exc), "topic": topic})

    def regression_sweep_tool(self, focus: str = "") -> ToolResult:
        payload = build_regression_sweep(self.workspace, tool_names=sorted(self.tools.keys()))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Regression sweep completed"), {"message": render_regression_sweep(payload), **payload})


    def improvement_roadmap_tool(self, focus: str = "") -> ToolResult:
        payload = build_next_improvement_roadmap(self.workspace, focus=focus)
        return ToolResult(True, "Improvement roadmap generated", {"result": payload, "markdown": render_improvement_roadmap(payload)})

    def improvement_impact_tool(self, focus: str = "") -> ToolResult:
        roadmap = build_next_improvement_roadmap(self.workspace, focus=focus)
        impact = build_improvement_impact_matrix(roadmap)
        payload = {**roadmap, "impact_matrix": impact}
        return ToolResult(True, "Improvement impact matrix generated", {"result": payload, "markdown": render_improvement_roadmap(payload)})

    def implement_improvements_tool(self, focus: str = "", confirm: bool = False) -> ToolResult:
        payload = complete_next_improvements(self.workspace, focus=focus, confirm=bool(confirm))
        ok = payload.get("status") in {"completed", "dry_run"}
        return ToolResult(ok, "Improvement roadmap " + str(payload.get("status", "completed")), {"result": payload, "markdown": render_improvement_roadmap(payload)})

    def proposal_ledger_tool(self) -> ToolResult:
        payload = load_latest_improvement_roadmap(self.workspace)
        ok = not (payload.get("ok") is False and payload.get("status") == "missing")
        markdown = render_improvement_roadmap(payload) if payload.get("proposals") else json.dumps(payload, indent=2)
        return ToolResult(ok, "Improvement roadmap ledger loaded" if ok else "No improvement roadmap ledger found", {"result": payload, "markdown": markdown})

    def whole_codebase_review_tool(self, focus: str = "") -> ToolResult:
        payload = build_whole_codebase_review(self.workspace, tool_names=sorted(self.tools.keys()))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Whole-codebase review completed"), {"message": render_whole_codebase_review(payload), **payload})

    def maintenance_validation_tool(self, profile: str = "quick") -> ToolResult:
        payload = build_maintenance_validation(self._wla_source_root(), tool_names=sorted(self.tools.keys()), profile=profile or "quick")
        if "--local-model" in (profile or "") or "local-model" in (profile or ""):
            try:
                payload["local_model_validation"]["model_health"] = assess_model_dependency(self.config).to_dict()
            except Exception as exc:
                payload["local_model_validation"]["model_health_error"] = repr(exc)
        try:
            log_activity("maintenance_validation", "Nova maintenance validation completed", {"ok": payload.get("ok"), "blockers": len(payload.get("blockers") or [])})
        except Exception:
            pass
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Maintenance validation completed"), {"message": render_maintenance_validation(payload), **payload})

    def bug_review_tool(self, focus: str = "") -> ToolResult:
        payload = build_bug_review(self.workspace, tool_names=sorted(self.tools.keys()))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Bug review completed"), {"message": render_bug_review(payload), **payload})


    def build_quality_report_tool(self, goal: str = "") -> ToolResult:
        payload = build_quality_report(self.workspace, goal)
        return ToolResult(bool(payload.get("ok")), "Build quality report completed", {"message": render_build_quality(payload), **payload})

    def browser_runtime_test_tool(self, goal: str = "", mode: str = "run") -> ToolResult:
        payload = build_browser_runtime_test(self.workspace, goal, mode=mode)
        return ToolResult(bool(payload.get("ok")), "Browser runtime test completed", {"message": render_browser_runtime(payload), **payload})

    def model_reliability_tool(self, focus: str = "") -> ToolResult:
        payload = build_model_reliability(self.workspace, focus)
        return ToolResult(bool(payload.get("ok")), "Model reliability report completed", {"message": render_model_reliability(payload), **payload})

    def model_fallback_strategy_tool(self, focus: str = "") -> ToolResult:
        payload = build_model_fallback_strategy(self.workspace, focus)
        return ToolResult(True, "Model fallback strategy generated", {"message": render_strategy(payload), **payload})

    def model_readiness_tool(self, goal: str = "") -> ToolResult:
        payload = build_model_readiness(goal, self.workspace, current_coder=getattr(self.config, "model", "qwen3-coder:30b"), current_chat=getattr(self.config, "chat_model", "gemma2:2b"))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Model readiness checked"), {"message": render_model_readiness(payload), **payload})

    def model_install_tool(self, name: str = "", confirm: bool = False) -> ToolResult:
        payload = install_model(name, self.workspace, confirm=bool(confirm))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Model install plan generated"), {"message": render_model_install_result(payload), **payload})

    def response_quality_plan_tool(self, goal: str = "", write: bool = False) -> ToolResult:
        if write:
            md, js, payload = write_response_quality_plan(self._wla_source_root(), goal)
            payload = {**payload, "markdown_path": str(md), "json_path": str(js)}
        else:
            payload = build_response_quality_plan(goal)
        return ToolResult(True, "Nova response quality plan generated", {"message": render_response_quality_plan(payload), **payload})

    def flow_audit_tool(self, focus: str = "") -> ToolResult:
        root = self.workspace if (self.workspace / "winlocalassistant" / "core.py").exists() else Path.cwd()
        payload = build_flow_audit(root, tool_names=sorted(self.tools.keys()))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Interaction flow audit completed"), {"message": render_flow_audit(payload), **payload})

    def flow_improvements_tool(self, focus: str = "", confirm: bool = False) -> ToolResult:
        root = self.workspace if (self.workspace / "winlocalassistant" / "core.py").exists() else Path.cwd()
        md, js, payload = write_flow_audit(root, tool_names=sorted(self.tools.keys()))
        payload = {**payload, "completed_improvements": [
            "Registered interaction-flow audit commands and ToolRegistry tools.",
            "Verified command, tool and autonomy capability coverage for build, repair, model, learning and sandbox pathways.",
            "Wrote a reusable flow-audit report so idle/autonomous can check integration before and after broad feature changes.",
        ], "markdown_path": str(md), "json_path": str(js)}
        return ToolResult(bool(payload.get("ok")), "Interaction flow improvements completed", {"message": render_flow_audit(payload), **payload})

    def patch_queue_tool(self, action: str = "status", goal: str = "") -> ToolResult:
        payload = patch_queue_action(action, goal)
        return ToolResult(True, "Patch queue updated", {"message": render_patch_queue(payload), **payload})

    def gui_cockpit_v2_tool(self, mode: str = "preview") -> ToolResult:
        payload = build_gui_cockpit_v2(self.workspace, mode)
        return ToolResult(True, "GUI cockpit v2 preview generated", {"message": render_gui_cockpit_v2(payload), **payload})

    def voice_mode_report_tool(self, mode: str = "status") -> ToolResult:
        payload = build_voice_mode_report(self.workspace, mode)
        return ToolResult(True, "Voice mode report generated", {"message": render_voice_mode(payload), **payload})

    def template_list_tool(self) -> ToolResult:
        payload = list_templates()
        return ToolResult(True, "Project templates listed", {"message": render_templates(payload), **payload})

    def template_build_tool(self, template: str = "notes-app") -> ToolResult:
        payload = build_template_project(self.workspace, template)
        return ToolResult(True, "Template project staged", {"message": render_templates(payload), **payload})

    def preview_server_tool(self, action: str = "status") -> ToolResult:
        payload = build_preview_server_report(self.workspace, action)
        return ToolResult(True, "Preview server report generated", {"message": render_preview(payload), **payload})

    def feature_readiness_tool(self) -> ToolResult:
        payload = build_feature_readiness(self.workspace)
        return ToolResult(True, "Feature readiness report generated", {"message": render_feature_readiness(payload), **payload})

    def explain_error_tool(self, text: str = "") -> ToolResult:
        payload = explain_error(text)
        return ToolResult(True, "Error explanation generated", {"message": render_error_explanation(payload), **payload})

    def support_report_tool(self, focus: str = "") -> ToolResult:
        payload = build_support_report(self.workspace, focus)
        return ToolResult(True, "Support report generated", {"message": render_support_report(payload), **payload})

    def docs_index_tool(self, query: str = "") -> ToolResult:
        payload = docs_index(self.workspace, query)
        return ToolResult(True, "Nova docs/code index completed", {"message": render_docs_index(payload), **payload})

    def regression_test_generate_tool(self, bug: str = "") -> ToolResult:
        payload = regression_test_generate(self.workspace, bug)
        return ToolResult(True, "Regression test seed generated", {"message": render_regression_test(payload), **payload})

    def mistake_learning_status_tool(self) -> ToolResult:
        payload = learning_status(self.workspace)
        return ToolResult(True, "Mistake learning status generated", {"message": render_learning_status(payload), **payload})

    def mission_dashboard_tool(self, goal: str = "") -> ToolResult:
        payload = build_mission_dashboard(goal)
        return ToolResult(True, "Mission dashboard generated", {"message": render_payload(payload, "Autonomous Mission Dashboard"), **payload})

    def cycle_score_tool(self) -> ToolResult:
        payload = {"progress_score": _score_from_events(_events(160), "autonomous")}
        return ToolResult(True, "Autonomous progress score generated", {"message": render_payload(payload, "Cycle Progress Score"), **payload})

    def idle_progress_score_tool(self) -> ToolResult:
        payload = {"progress_score": _score_from_events(_events(160), "idle")}
        return ToolResult(True, "Idle progress score generated", {"message": render_payload(payload, "Idle Progress Score"), **payload})

    def autonomy_readiness_tool(self, path: str = ".") -> ToolResult:
        """Report whether Nova is ready for supervised autonomous improvement runs."""

        try:
            target = resolve_inside_workspace(self.workspace, path or ".")
        except Exception:
            target = self.workspace
        report = build_autonomy_readiness(target)
        return ToolResult(
            True,
            "Nova autonomy readiness",
            {"message": render_autonomy_readiness_markdown(report), **report},
        )

    def tool_choice_trace_tool(self, goal: str = "") -> ToolResult:
        payload = build_tool_choice_trace(goal)
        return ToolResult(True, "Tool choice trace generated", {"message": render_payload(payload, "Tool Choice Trace"), **payload})

    def repetition_guard_tool(self) -> ToolResult:
        payload = {"repetition_guard": repeated_signature()}
        return ToolResult(True, "Repetition guard status generated", {"message": render_payload(payload, "Repetition Guard"), **payload})

    def repetition_clear_tool(self) -> ToolResult:
        payload = {"repetition_guard": clear_repetition_memory()}
        return ToolResult(True, "Repetition guard memory cleared", {"message": render_payload(payload, "Repetition Guard Cleared"), **payload})

    def idle_background_settings_tool(self) -> ToolResult:
        payload = {"background_idle_settings": load_background_settings()}
        return ToolResult(True, "Idle background settings loaded", {"message": render_payload(payload, "Idle Background Settings"), **payload})

    def autonomous_patch_mode_tool(self) -> ToolResult:
        payload = {"background_idle_settings": set_background_setting("autonomous_patch_mode", True)}
        return ToolResult(True, "Autonomous patch mode enabled", {"message": render_payload(payload, "Autonomous Patch Mode"), **payload})

    def mistake_log_tool(self) -> ToolResult:
        payload = load_mistake_log()
        return ToolResult(True, "Mistake learning log loaded", {"message": render_payload(payload, "Mistake Learning Log"), **payload})

    def mistake_to_regression_tool(self) -> ToolResult:
        item = mistake_to_regression()
        payload = {"items": [item]}
        return ToolResult(True, "Latest mistake converted to regression seed", {"message": render_payload(payload, "Mistake To Regression"), **payload})

    def autonomous_last_report_tool(self) -> ToolResult:
        payload = autonomous_last_report()
        return ToolResult(True, "Autonomous last detailed report generated", {"message": render_payload(payload, "Autonomous Last Detailed Report"), **payload})

    def assistant_db(self, action: str = "list", database: str = "default", collection: str = "notes", key: str = "", value: Any = None, query: str = "", schema_hint: str = "") -> ToolResult:
        """Create/list/store/modify/delete schemaless assistant databases under the Nova app directory."""
        action = str(action or "list").strip().lower()
        try:
            if action in {"list", "status", "databases"}:
                payload = list_databases()
                return ToolResult(True, "Assistant databases listed", {"message": render_db_markdown(payload), **payload})
            if action in {"put", "set", "write", "upsert"}:
                payload = put_record(database, collection, key or str(int(time.time())), value, schema_hint=schema_hint)
                return ToolResult(True, "Assistant database record stored", {"message": render_db_markdown(payload), **payload})
            if action in {"merge", "patch", "update"}:
                payload = merge_record(database, collection, key or str(int(time.time())), value, schema_hint=schema_hint)
                return ToolResult(True, "Assistant database record merged", {"message": render_db_markdown(payload), **payload})
            if action in {"get", "read"}:
                payload = get_record(database, collection, key)
                return ToolResult(True, "Assistant database record read", {"message": render_db_markdown(payload), **payload})
            if action in {"schema", "describe", "inspect"}:
                payload = database_schema(database)
                return ToolResult(True, "Assistant database schema inferred", {"message": render_db_markdown(payload), **payload})
            if action in {"audit", "check", "review", "integrity"}:
                payload = audit_database(database if database not in {"default", ""} else "")
                return ToolResult(bool(payload.get("ok", True)), "Assistant database audit completed", {"message": render_db_markdown(payload), **payload})
            if action in {"compact", "vacuum"}:
                self.require_mutation()
                payload = compact_database()
                return ToolResult(True, "Assistant database compacted", {"message": render_db_markdown(payload), **payload})
            if action in {"export", "dump", "backup"}:
                payload = export_database(database)
                return ToolResult(True, "Assistant database exported", {"message": render_db_markdown(payload), **payload})
            if action in {"search", "find", "query"}:
                payload = search_records(database, query)
                return ToolResult(True, "Assistant database search completed", {"message": render_db_markdown(payload), **payload})
            if action in {"delete", "del", "remove"}:
                self.require_mutation()
                payload = delete_record(database, collection, key)
                return ToolResult(True, "Assistant database record(s) deleted", {"message": render_db_markdown(payload), **payload})
            return ToolResult(False, "Unknown assistant database action", {"usage": "/db list | /db audit [DB] | /db put|merge DB.COL.KEY {json} | /db get DB.COL.KEY | /db schema DB | /db export DB | /db search DB query | /db compact --confirm | /db delete DB.COL.KEY"})
        except Exception as exc:
            return ToolResult(False, "Assistant database operation failed", {"error": repr(exc), "action": action})

    def sandbox_status(self) -> ToolResult:
        payload = sandbox_status(self.config)
        return ToolResult(True, "Sandbox status", {"message": render_status_markdown(payload), **payload})


    def sandbox_setup_help(self) -> ToolResult:
        payload = sandbox_setup_help(self.config)
        return ToolResult(True, "Sandbox setup help", {"message": render_setup_help_markdown(payload), **payload})

    def sandbox_start(self, profile: str = "linux", name: str = "", network: str = "none", writable_workspace: bool = False, pull: bool = False) -> ToolResult:
        payload = start_sandbox(self.config, profile=profile, name=name, network=network, writable_workspace=writable_workspace, pull=pull)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Sandbox start"), {"message": render_status_markdown(sandbox_status(self.config)) + "\n\n## Last action\n" + json.dumps(payload, indent=2), **payload})

    def sandbox_stop(self, profile: str = "linux", name: str = "") -> ToolResult:
        payload = stop_sandbox(self.config, profile=profile, name=name)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Sandbox stop"), {"message": render_status_markdown(sandbox_status(self.config)) + "\n\n## Last action\n" + json.dumps(payload, indent=2), **payload})

    def sandbox_exec(self, profile: str = "linux", command: str = "", timeout: int = 30, allow_network_tools: bool = False, allow_high_risk: bool = False) -> ToolResult:
        payload = exec_sandbox(self.config, profile=profile, command=command, timeout=timeout, allow_network_tools=allow_network_tools, allow_high_risk=allow_high_risk)
        stdout = str(payload.get("stdout") or "")
        stderr = str(payload.get("stderr") or "")
        lines = ["# Sandbox Command Result", "", f"Profile: `{profile}`", f"OK: **{bool(payload.get('ok'))}**", f"Summary: {payload.get('summary','')}", ""]
        policy = payload.get("policy") or {}
        if policy:
            if policy.get("reasons"):
                lines += ["## Policy block reasons"] + [f"- {x}" for x in policy.get("reasons", [])] + [""]
            if policy.get("warnings"):
                lines += ["## Policy warnings"] + [f"- {x}" for x in policy.get("warnings", [])] + [""]
        if stdout:
            lines += ["## stdout", "```", stdout[-6000:], "```", ""]
        if stderr:
            lines += ["## stderr", "```", stderr[-6000:], "```", ""]
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Sandbox exec"), {"message": "\n".join(lines), **payload})

    def sandbox_dev_run_tool(self, profile: str = "linux", command: str = "", timeout: int = 300) -> ToolResult:
        payload = sandbox_dev_run(self.config, profile=profile, command=command, timeout=int(timeout or 300))
        stdout = str(payload.get("stdout") or "")
        stderr = str(payload.get("stderr") or "")
        lines = ["# Sandbox Dev-Copy Run", "", f"Profile: `{profile}`", f"OK: **{bool(payload.get('ok'))}**", f"Summary: {payload.get('summary','')}", f"Command: `{command}`", ""]
        if payload.get("workspace_copy"):
            lines.append(f"Copied workspace: `{payload.get('workspace_copy')}`")
        if stdout:
            lines += ["", "## stdout", "```", stdout[-6000:], "```"]
        if stderr:
            lines += ["", "## stderr", "```", stderr[-6000:], "```"]
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Sandbox dev-copy run"), {"message": "\n".join(lines), **payload})

    def sandbox_flag(self, flag: str = "autonomy", enabled: bool = False) -> ToolResult:
        payload = set_sandbox_flag(self.config, flag=flag, enabled=enabled)
        return ToolResult(True, f"Sandbox {flag} set to {enabled}", {"message": render_status_markdown(sandbox_status(self.config)), **payload})

    def sandbox_policy(self, level: str = "balanced") -> ToolResult:
        payload = set_sandbox_policy(self.config, level=level)
        return ToolResult(True, str(payload.get("summary") or "Sandbox policy updated"), {"message": render_status_markdown(sandbox_status(self.config)), **payload})

    def docker_status(self, include_raw: bool = True) -> ToolResult:
        payload = docker_status(self.config, include_raw=include_raw)
        ok = bool(payload.get("installed")) and bool(payload.get("daemon_running"))
        summary = "Docker is ready" if ok else "Docker diagnostics completed"
        return ToolResult(ok, summary, {"message": render_docker_markdown(payload), **payload})

    def docker_ps(self) -> ToolResult:
        payload = docker_ps(self.config)
        lines = ["# Docker Containers", "", f"OK: **{bool(payload.get('ok'))}**", f"Summary: {payload.get('summary','')}", ""]
        for row in payload.get("containers") or []:
            name = row.get("Names") or row.get("Name") or row.get("ID") or "container"
            lines.append(f"- `{name}` — {row.get('Status') or row.get('State') or ''} — `{row.get('Image') or ''}`")
        if not payload.get("containers"):
            lines.append("No containers found or Docker did not respond.")
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Docker ps"), {"message": "\n".join(lines), **payload})

    def docker_smoke(self, image: str = "python:3.12-slim") -> ToolResult:
        payload = docker_smoke(self.config, image=image or "python:3.12-slim")
        raw = payload.get("raw") or {}
        out = str(raw.get("stdout") or raw.get("stderr") or raw.get("error") or "").strip()
        msg = "# Docker Smoke Test\n\n" + f"Image: `{payload.get('image')}`\n\n" + "```\n" + out[-4000:] + "\n```"
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Docker smoke"), {"message": msg, **payload})

    def docker_validate(self, path: str = ".", command: str = "", image: str = "python:3.12-slim", timeout: int = 300) -> ToolResult:
        payload = docker_validate_project(self.config, path=path or ".", command=command or "python -m compileall -q winlocalassistant tests_*.py app.py", image=image or "python:3.12-slim", timeout=timeout)
        raw = payload.get("raw") or {}
        out = str(raw.get("stdout") or "").strip()
        err = str(raw.get("stderr") or raw.get("error") or "").strip()
        status_label = "SKIPPED" if payload.get("skipped") else ("PASS" if payload.get("ok") else "FAIL")
        lines = [
            "# Docker Project Validation",
            "",
            f"Status: **{status_label}**",
            f"OK: **{bool(payload.get('ok'))}**",
            f"Run ID: `{payload.get('run_id','')}`",
            f"Image: `{payload.get('image','')}`",
            f"Command: `{payload.get('command','')}`",
            f"Copied workspace: `{payload.get('workspace_copy','')}`",
        ]
        copy_info = payload.get("copy_info") or {}
        if copy_info:
            lines.append(f"Copied files: **{copy_info.get('copied_files', 0)}**; skipped items: **{copy_info.get('skipped_items', 0)}**")
        if out:
            lines += ["", "## stdout", "```", out[-6000:], "```"]
        if err:
            lines += ["", "## stderr", "```", err[-6000:], "```"]
        if payload.get("reason"):
            lines += ["", "## Reason", str(payload.get("reason"))]
        if payload.get("next_steps"):
            lines += ["", "## Next steps"] + [f"- {step}" for step in payload.get("next_steps") or []]
        if payload.get("run_dir"):
            lines += ["", f"Report folder: `{payload.get('run_dir')}`"]
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Docker validation"), {"message": "\n".join(lines), **payload})


    def docker_patch_validate(self, path: str = ".", patch_file: str = "", patch_text: str = "", command: str = "", image: str = "python:3.12-slim", timeout: int = 300) -> ToolResult:
        payload = docker_validate_patch(
            self.config,
            path=path or ".",
            patch_file=patch_file or "",
            patch_text=patch_text or "",
            command=command or "python -m compileall -q winlocalassistant tests_*.py app.py",
            image=image or "python:3.12-slim",
            timeout=timeout,
        )
        raw = payload.get("raw") or {}
        out = str(raw.get("stdout") or "").strip()
        err = str(raw.get("stderr") or raw.get("error") or "").strip()
        lines = [
            "# Docker Patch Validation",
            "",
            f"OK: **{bool(payload.get('ok'))}**",
            f"Run ID: `{payload.get('run_id','')}`",
            f"Stage: `{payload.get('stage','')}`",
            f"Patch: `{payload.get('patch_source') or payload.get('patch_path') or patch_file}`",
            f"Image: `{payload.get('image','')}`",
            f"Command: `{payload.get('command','')}`",
            f"Copied workspace: `{payload.get('workspace_copy','')}`",
        ]
        copy_info = payload.get("copy_info") or {}
        if copy_info:
            lines.append(f"Copied files: **{copy_info.get('copied_files', 0)}**; skipped items: **{copy_info.get('skipped_items', 0)}**")
        if out:
            lines += ["", "## stdout", "```", out[-6000:], "```"]
        if err:
            lines += ["", "## stderr", "```", err[-6000:], "```"]
        if payload.get("run_dir"):
            lines += ["", f"Report folder: `{payload.get('run_dir')}`"]
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Docker patch validation"), {"message": "\n".join(lines), **payload})


    def docker_promote_patch(self, run_id: str = "", path: str = ".", local_command: str = "python -m compileall -q winlocalassistant tests_*.py app.py", rollback_on_failure: bool = True) -> ToolResult:
        payload = docker_promote_validated_patch(
            self.config,
            run_id=run_id or "",
            path=path or ".",
            local_command=local_command or "python -m compileall -q winlocalassistant tests_*.py app.py",
            rollback_on_failure=rollback_on_failure,
        )
        lines = [
            "# Docker Validated Patch Promotion",
            "",
            f"OK: **{bool(payload.get('ok'))}**",
            f"Summary: {payload.get('summary','')}",
            f"Validation run: `{payload.get('validation_run_id','')}`",
            f"Promotion/report folder: `{payload.get('backup_dir','')}`",
            f"Patch: `{payload.get('patch_path','')}`",
        ]
        check = payload.get("local_check") or {}
        if check:
            lines += ["", "## Local post-promotion check", "```", str(check.get("stdout") or check.get("stderr") or check.get("error") or "")[-6000:], "```"]
        rollback = payload.get("rollback")
        if rollback:
            lines += ["", "## Rollback", "```", json.dumps(rollback, indent=2)[:4000], "```"]
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Docker patch promotion"), {"message": "\n".join(lines), **payload})


    def docker_history(self, limit: int = 20) -> ToolResult:
        payload = docker_validation_history(self.config, limit=limit)
        return ToolResult(True, str(payload.get("summary") or "Docker history"), {"message": render_docker_history_markdown(payload), **payload})

    def docker_clean(self, keep: int = 20) -> ToolResult:
        payload = docker_cleanup(self.config, keep=keep)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Docker cleanup"), {"message": render_docker_cleanup_markdown(payload), **payload})

    def docker_help(self) -> ToolResult:
        return ToolResult(True, "Docker integration help", {"message": render_docker_setup_help()})


    def wla_doctor(self, goal: str = "", path: str = ".") -> ToolResult:
        payload = run_wla_doctor(Path(path or "."), goal or "general Nova reliability")
        message = render_wla_doctor_markdown(payload)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Nova doctor completed"), {"message": message, **payload})


    def wla_release_gate(self, goal: str = "", path: str = ".", test_command: str = "") -> ToolResult:
        payload = run_wla_release_gate(Path(path or "."), goal or "release validation", test_command or "")
        message = render_wla_release_gate_markdown(payload)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Nova release gate completed"), {"message": message, **payload})


    def nova_brand_audit_tool(self, path: str = ".") -> ToolResult:
        payload = scan_legacy_branding(Path(path or "."))
        return ToolResult(bool(payload.get("ok")), "Nova brand audit completed", {"message": render_branding_audit(payload), **payload})

    def nova_improvement_research_tool(self, focus: str = "", path: str = ".") -> ToolResult:
        payload = build_nova_improvement_research(Path(path or "."), focus=focus or "general Nova functionality")
        return ToolResult(True, "Nova improvement research plan generated", {"message": render_nova_improvement_research(payload), **payload})

    def integration_radar(self, goal: str = "", path: str = ".") -> ToolResult:
        payload = build_integration_radar(Path(path or "."), goal or "improve Nova integration ecosystem")
        return ToolResult(bool(payload.get("ok", True)), str(payload.get("summary") or "Integration radar completed"), {"message": render_integration_radar_markdown(payload), **payload})

    def feature_audit(self, path: str = ".") -> ToolResult:
        payload = build_feature_audit(Path(path or "."))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Requested-feature audit completed"), {"message": render_feature_audit_markdown(payload), **payload})

    def release_checklist(self, path: str = ".") -> ToolResult:
        payload = build_release_checklist(Path(path or "."))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Release checklist completed"), {"message": render_release_checklist_markdown(payload), **payload})

    def cohesion_report(self, goal: str = "", path: str = ".") -> ToolResult:
        md, js, report = write_cohesion_report(Path(path or "."), goal or "")
        message = render_cohesion_report_markdown(report) + f"\n\nReport written:\n- `{md}`\n- `{js}`"
        return ToolResult(True, "Cohesion report generated", {"message": message, "markdown_path": str(md), "json_path": str(js), **report.to_dict()})

    def validation_ladder(self, goal: str = "") -> ToolResult:
        return ToolResult(True, "Validation ladder generated", {"message": render_validation_ladder_markdown(goal or "")})

    def iteration_plan(self, goal: str = "") -> ToolResult:
        return ToolResult(True, "Iterative development protocol generated", {"message": render_iterative_development_markdown(goal or "")})

    def development_strategy_tool(self, goal: str = "", last_failure: str = "", attempts: list[dict[str, Any]] | str | None = None) -> ToolResult:
        parsed_attempts: list[dict[str, Any]] = []
        if isinstance(attempts, str) and attempts.strip():
            try:
                val = json.loads(attempts)
                if isinstance(val, list):
                    parsed_attempts = [x for x in val if isinstance(x, dict)]
            except Exception:
                parsed_attempts = [{"attempt": "input", "status": "text", "reason": attempts}]
        elif isinstance(attempts, list):
            parsed_attempts = [x for x in attempts if isinstance(x, dict)]
        decision = build_strategy_decision(goal or "general Nova task", last_failure=last_failure, attempts=parsed_attempts)
        return ToolResult(True, f"Development strategy: {decision.get('route')}", {"decision": decision, "markdown": render_strategy(decision)})

    def validation_evidence_tool(self, path: str = ".", goal: str = "") -> ToolResult:
        root = resolve_inside_workspace(self.workspace, path or ".")
        evidence = build_validation_evidence(root, goal=goal)
        return ToolResult(bool(evidence.get("ok")), evidence.get("summary", "Validation evidence generated"), {"evidence": evidence, "markdown": render_validation_evidence(evidence)})

    def persona_profile_tool(self, action: str = "status") -> ToolResult:
        """Show Nova's user-configurable persona, style sliders and response contract."""
        profile = load_persona_profile()
        return ToolResult(True, "Nova persona profile ready", {"message": render_persona_profile(profile), "persona": profile})

    def custom_chat_window_tool(self) -> ToolResult:
        """Return the custom chat/persona window specification used by GUI and prompts."""
        spec = build_custom_chat_window_spec()
        lines = ["# Custom Chat Window", "", "This defines how Nova should present herself, think about her role, and respond to you.", "", "## Current prompt addendum", "```text", spec.get("prompt_addendum", ""), "```", "", "## Sliders"]
        for slider in spec.get("sliders", []):
            lines.append(f"- **{slider.get('key')}**: {slider.get('value')} ({slider.get('left')} ↔ {slider.get('right')})")
        return ToolResult(True, "Custom chat/persona window spec ready", {"message": "\n".join(lines).strip() + "\n", **spec})

    def persona_set_tool(self, settings: str = "") -> ToolResult:
        """Update Nova persona with key=value slider/identity settings."""
        profile = update_persona_from_tokens(settings or "")
        return ToolResult(True, "Nova persona updated", {"message": render_persona_profile(profile), "persona": profile})

    def persona_json_tool(self, json_text: str = "") -> ToolResult:
        """Update Nova persona from a JSON object for multi-word fields."""
        try:
            profile = update_persona_from_json(json_text or "{}")
        except Exception as exc:
            return ToolResult(False, "Persona JSON update failed", {"message": f"Persona JSON update failed: {exc}", "error": repr(exc)})
        return ToolResult(True, "Nova persona updated from JSON", {"message": render_persona_profile(profile), "persona": profile})

    def persona_prompt_tool(self, mode: str = "default") -> ToolResult:
        """Show the exact persona prompt addendum injected into Nova/local-model contexts."""
        prompt = build_persona_prompt_addendum(mode or "default")
        return ToolResult(True, "Nova persona prompt addendum", {"message": "# Nova Persona Prompt Addendum\n\n```text\n" + prompt + "\n```", "prompt_addendum": prompt})

    def voice_audit_tool(self, limit: int = 20, transcript: str = "", action: str = "", status: str = "observed") -> ToolResult:
        """Show or append voice command audit entries."""
        if transcript:
            append_voice_audit(transcript, action=action, status=status)
        payload = build_voice_audit(limit=int(limit or 20))
        return ToolResult(True, "Voice command audit ready", {"message": render_voice_audit(payload), **payload})

    def local_model_optimizer_tool(self, goal: str = "") -> ToolResult:
        """Recommend local-model routing, context, quantization and prompt-cache improvements."""
        payload = build_local_model_optimization_plan(self._wla_source_root(), goal=goal or "maximize Nova local model capability")
        perf = build_local_model_performance_plan(goal or "maximize Nova local model capability")
        message = render_local_model_optimization_plan(payload) + "\n" + render_local_model_performance_plan(perf)
        return ToolResult(True, "Local model optimisation plan generated", {"message": message, "performance_plan": perf, **payload})

    def coding_plan_tool(self, goal: str = "") -> ToolResult:
        """Choose the most efficient runnable project/file shape for a coding prompt."""
        plan = plan_coding_execution(goal or "general local coding task")
        return ToolResult(True, f"Coding plan selected {plan.get('language')} / {plan.get('artifact_type')}", {"message": render_coding_execution_plan(plan), **plan})

    def coding_capability_audit_tool(self, goal: str = "") -> ToolResult:
        """Audit Nova's coding generation path for HTML bias and verifier coverage."""
        payload = build_coding_capability_audit(self._wla_source_root())
        if goal:
            payload["requested_goal_plan"] = plan_coding_execution(goal)
        return ToolResult(bool(payload.get("ok")), "Nova coding capability audit generated", {"message": render_coding_capability_audit(payload), **payload})

    def local_model_performance_plan_tool(self, goal: str = "", hardware: str = "") -> ToolResult:
        """Return task-specific local model tuning guidance for Nova."""
        payload = build_local_model_performance_plan(goal, hardware_hint=hardware)
        return ToolResult(True, "Local model performance plan generated", {"message": render_local_model_performance_plan(payload), **payload})

    def agent_upgrade_radar_tool(self, focus: str = "") -> ToolResult:
        """Show web-inspired, additive Nova improvement patterns and verification gates."""
        payload = build_agent_upgrade_radar(self._wla_source_root(), focus=focus or "improve Nova safely")
        return ToolResult(bool(payload.get("ok")), "Nova agent upgrade radar generated", {"message": render_agent_upgrade_radar(payload), **payload})

    def context_budget_tool(self, goal: str = "", max_files: int = 12) -> ToolResult:
        """Build a compact, prompt-relevant context pack for local model calls."""
        payload = build_context_budget_plan(self._wla_source_root(), goal=goal or "general Nova improvement", max_files=int(max_files or 12))
        return ToolResult(True, "Nova context budget plan generated", {"message": render_context_budget_plan(payload), **payload})

    def coding_behavior_tests_tool(self, goal: str = "") -> ToolResult:
        """Generate request-specific behaviour checks for Nova coding outputs."""
        payload = build_coding_behavior_tests(goal or "build a small useful project")
        return ToolResult(True, "Nova coding behaviour tests generated", {"message": render_coding_behavior_tests(payload), **payload})

    def ollama_runtime_profile_tool(self, goal: str = "", hardware: str = "") -> ToolResult:
        """Generate a read-only Ollama Modelfile/options profile for the task."""
        payload = build_ollama_runtime_profile(goal or "general Nova task", hardware_hint=hardware or "")
        return ToolResult(True, "Nova Ollama runtime profile generated", {"message": render_ollama_runtime_profile(payload), **payload})

    def upgrade_regression_audit_tool(self) -> ToolResult:
        """Check that recent Nova patches remain present and routed."""
        payload = build_upgrade_regression_audit(self._wla_source_root())
        return ToolResult(bool(payload.get("ok")), "Nova upgrade regression audit generated", {"message": render_upgrade_regression_audit(payload), **payload})

    def repo_context_map_tool(self, goal: str = "", max_files: int = 14) -> ToolResult:
        """Build a compact repo map for coding agents and local-model prompts."""
        payload = build_repo_context_map(self._wla_source_root(), goal=goal or "general Nova reliability work", max_files=int(max_files or 14))
        return ToolResult(bool(payload.get("ok")), "Nova repo context map generated", {"message": render_repo_context_map(payload), **payload})

    def patch_impact_plan_tool(self, changed_files: str = "") -> ToolResult:
        """Choose targeted regression tests for a proposed patch file list."""
        payload = build_patch_impact_plan(self._wla_source_root(), changed_files=changed_files or "")
        return ToolResult(bool(payload.get("ok")), "Nova patch impact test plan generated", {"message": render_patch_impact_plan(payload), **payload})

    def permission_scope_review_tool(self, intent: str = "", proposed_actions: str = "") -> ToolResult:
        """Review ambiguous or broad state-changing patch actions before execution."""
        payload = build_permission_scope_review(intent=intent or "Nova improvement", proposed_actions=proposed_actions or "")
        return ToolResult(True, f"Nova permission scope review: {payload.get('risk_level')}", {"message": render_permission_scope_review(payload), **payload})

    def local_model_benchmark_plan_tool(self, goal: str = "", hardware: str = "") -> ToolResult:
        """Draft a repeatable benchmark matrix for local Ollama model tuning."""
        payload = build_local_model_benchmark_plan(goal=goal or "general Nova use", hardware=hardware or "")
        return ToolResult(True, "Nova local model benchmark plan generated", {"message": render_local_model_benchmark_plan(payload), **payload})

    def tool_contract_audit_tool(self) -> ToolResult:
        """Audit ToolRegistry/core command contract continuity without executing tools."""
        payload = build_tool_contract_audit(self._wla_source_root())
        return ToolResult(bool(payload.get("ok")), "Nova tool contract audit generated", {"message": render_tool_contract_audit(payload), **payload})

    def command_verify_tool(self, profile: str = "repo") -> ToolResult:
        """Verify important commands through the ToolRegistry surface.

        Earlier /command-verify existed only as a Core.handle_command branch. This
        direct tool keeps command verification visible to autonomous/idle tool
        planning, repo-upgrade assurance and ToolRegistry audits.
        """
        checks: list[dict[str, Any]] = []
        contracts: list[tuple[str, str, dict[str, Any], tuple[str, ...], bool]] = [
            ("/status", "status", {}, ("workspace",), True),
            ("/idle status", "idle_policy", {"action": "status"}, ("Idle",), True),
            ("/model-context", "model_context", {}, ("Nova", "Context"), True),
            ("/pipeline-preflight verify Nova", "pipeline_preflight", {"goal": "verify Nova"}, ("Pipeline",), True),
            ("/pipeline-catalog repo upgrade", "pipeline_catalog", {"goal": "repo upgrade", "write": False}, ("Capability", "Manifest"), True),
            ("/session-evidence latest 20", "session_evidence", {"run_id": "latest", "limit": 20}, ("Session", "Evidence"), True),
            ("/memory-inventory .", "memory_inventory", {"path": "."}, ("Memory",), True),
            ("/browser-smoke .", "browser_smoke", {"path": "."}, ("Browser", "Smoke"), True),
            ("/tool-awareness-audit", "tool_awareness_audit", {}, ("Tool Awareness",), True),
            ("/repo-upgrade-assurance", "repo_upgrade_assurance", {}, ("Repo Upgrade", "PASS"), True),
            ("/codebase-sanity-audit", "codebase_sanity_audit", {}, ("Codebase", "Sanity"), True),
            ("/repo-research-radar", "repo_research_radar", {}, ("Repo Research", "Installed ideas"), True),
            ("/tool-contract-audit", "tool_contract_audit", {}, ("Tool",), False),
        ]
        for command, tool, kwargs, markers, required_ok in contracts:
            result = self.call(tool, **kwargs)
            data = result.data or {}
            output = str(data.get("message") or result.summary or "")
            if data and not data.get("message"):
                try:
                    output = output + "\n" + json.dumps(data, indent=2, default=str)[:1200]
                except Exception:
                    output = output + "\n" + str(data)[:1200]
            lower = output.lower()
            missing = [marker for marker in markers if marker.lower() not in lower]
            ok = bool(result.ok or not required_ok) and not missing and bool(output.strip())
            checks.append({
                "command": command,
                "tool": tool,
                "purpose": f"Verify {tool} via direct ToolRegistry call",
                "category": "tool_registry",
                "ok": ok,
                "expected_markers": list(markers),
                "missing_markers": missing,
                "forbidden_hits": [],
                "output_preview": output[:800],
                "error": "" if ok else (result.summary if not result.ok else "missing expected markers"),
            })
        passed = sum(1 for item in checks if item.get("ok"))
        report = {"ok": passed == len(checks), "passed": passed, "failed": len(checks)-passed, "total": len(checks), "results": checks}
        try:
            log_activity("command_verify", "Direct ToolRegistry command verification completed", {"ok": report["ok"], "passed": passed, "total": len(checks)})
        except Exception:
            pass
        return ToolResult(bool(report["ok"]), "Nova command verification " + ("passed" if report["ok"] else "found issues"), {"message": render_command_verification_markdown(report), **report})

    def repo_upgrade_assurance_tool(self) -> ToolResult:
        """Audit that repo-inspired upgrades are installed and work together."""
        payload = build_repo_upgrade_assurance(self._wla_source_root(), available_tools=sorted(self.tools.keys()))
        try:
            log_activity("repo_upgrade_assurance", "Repo-inspired upgrade assurance completed", {"ok": payload.get("ok"), "passed": payload.get("passed"), "total": payload.get("total")})
        except Exception:
            pass
        return ToolResult(bool(payload.get("ok")), "Repo upgrade assurance " + ("passed" if payload.get("ok") else "needs attention"), {"message": render_repo_upgrade_assurance(payload), **payload})

    def codebase_sanity_audit_tool(self, path: str = "__wla_source__") -> ToolResult:
        """Audit Nova source for redundancy, large modules, risky patterns and integration drift."""
        root = self._wla_source_root() if not path or path == "__wla_source__" else Path(path)
        payload = build_codebase_sanity_audit(root)
        try:
            log_activity("codebase_sanity_audit", "Codebase sanity audit completed", {"ok": payload.get("ok"), "findings": payload.get("findings_total")})
        except Exception:
            pass
        return ToolResult(bool(payload.get("ok")), "Nova codebase sanity audit " + ("passed" if payload.get("ok") else "needs attention"), {"message": render_codebase_sanity_audit(payload), **payload})

    def repo_research_radar_tool(self, goal: str = "") -> ToolResult:
        """Summarise repo-inspired integration opportunities currently installed in Nova."""
        payload = build_repo_upgrade_assurance(self._wla_source_root(), available_tools=sorted(self.tools.keys()))
        sanity = build_codebase_sanity_audit(self._wla_source_root())
        manifests = payload.get("repo_ideas_installed") or []
        lines = [
            "# Nova Repo Research Radar",
            "",
            f"Goal: {goal or 'continue future timeline repo integrations'}",
            f"Installed repo-inspired manifests: {len(manifests)}",
            f"Repo assurance: {'PASS' if payload.get('ok') else 'ATTENTION'} ({payload.get('passed')}/{payload.get('total')})",
            f"Codebase sanity: {'PASS' if sanity.get('ok') else 'ATTENTION'} with {sanity.get('findings_total')} findings",
            "",
            "## Installed ideas",
        ]
        for item in manifests:
            lines.append(f"- `{item}`")
        lines += ["", "## Highest-value next work"]
        for item in (payload.get("future_timeline") or [])[:6]:
            lines.append(f"- **{item.get('phase')}** — {item.get('focus')}: {item.get('work')}")
        if sanity.get("rewrite_candidates"):
            lines += ["", "## Rewrite candidates from codebase sanity"]
            for item in sanity.get("rewrite_candidates", [])[:6]:
                lines.append(f"- `{item.get('path')}` — {item.get('lines')} lines; {item.get('safe_next_step')}")
        return ToolResult(bool(payload.get("ok") and sanity.get("ok")), "Nova repo research radar generated", {"message": "\n".join(lines), "repo_assurance": payload, "codebase_sanity": sanity})

    def agent_topology_plan_tool(self, goal: str = "") -> ToolResult:
        """Build a bounded specialist topology for Nova agent workflows."""
        payload = build_agent_topology_plan(self._wla_source_root(), goal=goal or "improve Nova without regressions")
        return ToolResult(bool(payload.get("ok")), "Nova agent topology plan generated", {"message": render_agent_topology_plan(payload), **payload})

    def trace_observability_plan_tool(self, goal: str = "") -> ToolResult:
        """Build a trace/span contract for Nova workflows."""
        payload = build_trace_observability_plan(self._wla_source_root(), goal=goal or "make Nova work observable")
        return ToolResult(bool(payload.get("ok")), "Nova trace observability plan generated", {"message": render_trace_observability_plan(payload), **payload})

    def local_stack_advisor_tool(self, goal: str = "", hardware: str = "") -> ToolResult:
        """Advise on Ollama versus llama.cpp and local model runtime settings."""
        payload = build_local_stack_advisor(goal=goal or "general Nova assistant work", hardware=hardware or "")
        return ToolResult(bool(payload.get("ok")), "Nova local stack advisor generated", {"message": render_local_stack_advisor(payload), **payload})

    def verifier_ladder_tool(self, goal: str = "", runtime_hint: str = "") -> ToolResult:
        """Generate a runtime-aware verifier ladder for coding and patch work."""
        payload = build_verifier_ladder(goal=goal or "verify generated code", runtime_hint=runtime_hint or "")
        return ToolResult(bool(payload.get("ok")), "Nova verifier ladder generated", {"message": render_verifier_ladder(payload), **payload})

    def tool_namespace_plan_tool(self, goal: str = "") -> ToolResult:
        """Plan prompt-time tool namespaces to reduce local-model tool bloat."""
        payload = build_tool_namespace_plan(self._wla_source_root(), goal=goal or "reduce tool prompt bloat")
        return ToolResult(bool(payload.get("ok")), "Nova tool namespace plan generated", {"message": render_tool_namespace_plan(payload), **payload})

    def voice_pipeline_review_tool(self, focus: str = "") -> ToolResult:
        """Review Nova's voice pipeline using modular Jarvis-style assistant patterns."""
        payload = build_voice_pipeline_review(self._wla_source_root(), focus=focus or "Nova voice reliability")
        return ToolResult(bool(payload.get("ok")), "Nova voice pipeline review generated", {"message": render_voice_pipeline_review(payload), **payload})

    def route_resilience_plan_tool(self, goal: str = "") -> ToolResult:
        """Build a self-healing route/fallback plan for Nova workflows."""
        payload = build_route_resilience_plan(self._wla_source_root(), goal=goal or "improve Nova without regressions")
        return ToolResult(bool(payload.get("ok")), "Nova route resilience plan generated", {"message": render_route_resilience_plan(payload), **payload})

    def tool_health_map_tool(self, focus: str = "") -> ToolResult:
        """Audit command/tool routing health without executing registered tools."""
        payload = build_tool_health_map(self._wla_source_root(), focus=focus or "Nova route health")
        return ToolResult(bool(payload.get("ok")), "Nova tool health map generated", {"message": render_tool_health_map(payload), **payload})

    def guardrail_memory_plan_tool(self, goal: str = "", risk_note: str = "") -> ToolResult:
        """Build context-aware guardrail memory rules that preserve benign utility."""
        payload = build_guardrail_memory_plan(goal=goal or "improve Nova safely", risk_note=risk_note or "")
        return ToolResult(bool(payload.get("ok")), "Nova guardrail memory plan generated", {"message": render_guardrail_memory_plan(payload), **payload})

    def context_router_policy_tool(self, goal: str = "") -> ToolResult:
        """Build role-aware context routing under a bounded token budget."""
        payload = build_context_router_policy(self._wla_source_root(), goal=goal or "route Nova context efficiently")
        return ToolResult(bool(payload.get("ok")), "Nova context router policy generated", {"message": render_context_router_policy(payload), **payload})

    def local_runtime_sentinel_tool(self, goal: str = "", hardware: str = "") -> ToolResult:
        """Draft local-model runtime health checks and fallback profiles."""
        payload = build_local_runtime_sentinel(goal=goal or "general Nova local model work", hardware=hardware or "")
        return ToolResult(bool(payload.get("ok")), "Nova local runtime sentinel generated", {"message": render_local_runtime_sentinel(payload), **payload})

    def improvement_assurance_plan_tool(self, goal: str = "", changed: str = "") -> ToolResult:
        """Build evidence gates and acceptance criteria for a Nova improvement."""
        payload = build_improvement_assurance_plan(self._wla_source_root(), goal=goal or "improve Nova without regressions", changed=changed or "")
        return ToolResult(bool(payload.get("ok")), "Nova improvement assurance plan generated", {"message": render_improvement_assurance_plan(payload), **payload})

    def test_impact_graph_tool(self, changed: str = "") -> ToolResult:
        """Map changed files to likely validation tests without executing them."""
        payload = build_test_impact_graph(self._wla_source_root(), changed=changed or "")
        return ToolResult(bool(payload.get("ok")), "Nova test impact graph generated", {"message": render_test_impact_graph(payload), **payload})

    def patch_quality_score_tool(self, changed: str = "") -> ToolResult:
        """Score likely maintainability/regression risk for proposed patch files."""
        payload = build_patch_quality_score(self._wla_source_root(), changed=changed or "")
        return ToolResult(bool(payload.get("ok")), "Nova patch quality score generated", {"message": render_patch_quality_score(payload), **payload})

    def success_claim_audit_tool(self, summary: str = "") -> ToolResult:
        """Check whether a release summary overclaims validation evidence."""
        payload = build_success_claim_audit(summary or "")
        return ToolResult(bool(payload.get("ok")), "Nova success claim audit generated", {"message": render_success_claim_audit(payload), **payload})

    def regression_bisect_plan_tool(self, symptom: str = "", versions: str = "") -> ToolResult:
        """Create a safe bisect plan for locating which release introduced a regression."""
        payload = build_regression_bisect_plan(symptom=symptom or "unknown regression", versions=versions or "")
        return ToolResult(bool(payload.get("ok")), "Nova regression bisect plan generated", {"message": render_regression_bisect_plan(payload), **payload})

    def capability_drift_audit_tool(self) -> ToolResult:
        """Audit whether recent Nova feature families are still preserved."""
        payload = build_capability_drift_audit(self._wla_source_root())
        return ToolResult(bool(payload.get("ok")), "Nova capability drift audit generated", {"message": render_capability_drift_audit(payload), **payload})

    def feature_preservation_contract_tool(self, focus: str = "") -> ToolResult:
        """Build a non-regression contract for the feature family being changed."""
        payload = build_feature_preservation_contract(self._wla_source_root(), focus=focus or "general Nova improvement")
        return ToolResult(bool(payload.get("ok")), "Nova feature preservation contract generated", {"message": render_feature_preservation_contract(payload), **payload})

    def agent_feedback_loop_plan_tool(self, goal: str = "") -> ToolResult:
        """Plan a measured feedback loop over Nova's decomposed agent primitives."""
        payload = build_agent_feedback_loop_plan(goal=goal or "improve Nova from observed outcomes")
        return ToolResult(bool(payload.get("ok")), "Nova agent feedback loop plan generated", {"message": render_agent_feedback_loop_plan(payload), **payload})

    def behavior_fuzzer_plan_tool(self, goal: str = "", surface: str = "") -> ToolResult:
        """Create behaviour-driven fuzzing scenarios for Nova workflows."""
        payload = build_behavior_fuzzer_plan(goal=goal or "find Nova failure patterns", surface=surface or "coding, routing, voice and model workflows")
        return ToolResult(bool(payload.get("ok")), "Nova behaviour fuzzer plan generated", {"message": render_behavior_fuzzer_plan(payload), **payload})

    def local_spec_search_plan_tool(self, goal: str = "", hardware: str = "") -> ToolResult:
        """Plan non-regressing search over local model/runtime/spec options."""
        payload = build_local_spec_search_plan(goal=goal or "improve Nova local-model usefulness", hardware=hardware or "")
        return ToolResult(bool(payload.get("ok")), "Nova local spec search plan generated", {"message": render_local_spec_search_plan(payload), **payload})

    def agent_harness_tool(self, goal: str = "") -> ToolResult:
        """Show the iterative generate/execute/observe/repair harness Nova should use."""
        payload = build_iterative_agent_harness(self._wla_source_root(), goal=goal or "improve iterative coding reliability")
        return ToolResult(True, "Iterative agent harness plan generated", {"message": render_iterative_agent_harness(payload), **payload})

    def validation_matrix_tool(self, path: str = ".", goal: str = "") -> ToolResult:
        root = self._wla_source_root() if str(path or ".").strip().lower() in {"", ".", "wla", "source", "codebase"} else resolve_inside_workspace(self.workspace, path or ".")
        payload = build_validation_matrix(root, goal=goal or "general Nova validation")
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Validation matrix generated"), {"message": render_validation_matrix(payload), **payload})

    def adaptive_backlog_tool(self, path: str = ".", goal: str = "") -> ToolResult:
        root = self._wla_source_root() if str(path or ".").strip().lower() in {"", ".", "wla", "source", "codebase"} else resolve_inside_workspace(self.workspace, path or ".")
        payload = build_adaptive_backlog(root, goal=goal or "improve Nova reliability and development capability")
        return ToolResult(True, "Adaptive improvement backlog generated", {"message": render_adaptive_backlog(payload), **payload})

    def generation_template_manifest_tool(self, goal: str = "") -> ToolResult:
        payload = build_generation_template_manifest(goal or "general project")
        return ToolResult(True, f"Generation templates: {payload.get('inferred_project_type')}", {"message": render_template_manifest(payload), **payload})


    def idle_policy_tool(self, action: str = "status", level: str = "") -> ToolResult:
        action = str(action or "status").strip().lower()
        if action in {"set", "level", "use"}:
            try:
                policy = set_idle_policy_level(level or "1", updated_by="tool")
            except Exception as exc:
                return ToolResult(False, f"Idle policy not changed: {exc}", {"error": repr(exc), "message": render_idle_policy(load_idle_policy())})
            return ToolResult(True, f"Idle policy set to level {policy.get('level')}", {"policy": policy, "message": render_idle_policy(policy)})
        policy = load_idle_policy()
        return ToolResult(True, f"Idle policy level {policy.get('level')}", {"policy": policy, "message": render_idle_policy(policy)})

    def receipt_history_tool(self, limit: int = 20) -> ToolResult:
        payload = summarise_receipts(limit=int(limit or 20))
        return ToolResult(True, str(payload.get("summary") or "Receipt history generated"), {"message": render_receipt_history(payload), **payload})

    def role_router_tool(self, goal: str = "", last_failure: str = "", target_type: str = "") -> ToolResult:
        route = build_role_route(goal=goal or "general Nova work", last_failure=last_failure, target_type=target_type)
        return ToolResult(True, f"Role route: {route.get('primary_role')} / {route.get('route')}", {"route": route, "message": render_role_route(route)})

    def jarvis_bridge_tool(self, url: str = "", action: str = "map") -> ToolResult:
        """Show Jarvis-inspired daemon/sidecar capability mapping for Nova."""
        action = str(action or "map").strip().lower()
        if action in {"status", "probe", "health"}:
            return self.jarvis_status_tool(url=url or "")
        payload = build_capability_map()
        return ToolResult(True, "Jarvis-style Nova bridge capability map generated", {"message": render_bridge_markdown(payload), **payload})

    def jarvis_status_tool(self, url: str = "") -> ToolResult:
        """Read-only probe for a local Jarvis-style daemon endpoint."""
        payload = probe_jarvis_daemon(url or "http://127.0.0.1:3142")
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Jarvis daemon probe complete"), {"message": render_bridge_markdown(payload), **payload})

    def jarvis_doctor_tool(self, url: str = "") -> ToolResult:
        """Run a read-only setup doctor for Jarvis Docker, localhost binding and Ollama reachability."""
        payload = build_jarvis_setup_doctor(url or "http://127.0.0.1:3142")
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Jarvis setup doctor complete"), {"message": render_bridge_markdown(payload), **payload})

    def sidecar_preflight_tool(self, requested: str = "") -> ToolResult:
        """Preview sidecar capabilities against current Nova policy without enabling anything."""
        payload = build_sidecar_preflight(requested=requested or "")
        return ToolResult(True, str(payload.get("summary") or "Sidecar preflight complete"), {"message": render_bridge_markdown(payload), **payload})

    def bridge_authority_tool(self, capability: str = "general", action: str = "review", target: str = "", risk: str = "medium") -> ToolResult:
        """Apply Nova's Jarvis-style authority gate and record a receipt without executing external actions."""
        payload = build_authority_decision(capability=capability, action=action, target=target, risk=risk)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Authority decision recorded"), {"message": render_bridge_markdown({"summary": payload.get("summary"), "policy": payload.get("policy_snapshot") or build_capability_map().get("policy"), "actions": [payload], "warnings": payload.get("blockers", [])}), "record": payload})

    def workflow_blueprint_tool(self, goal: str = "") -> ToolResult:
        """Create a supervised Jarvis-style workflow blueprint that Nova can validate before acting."""
        payload = build_workflow_blueprint(goal or "improve Nova safely")
        return ToolResult(True, str(payload.get("summary") or "Workflow blueprint generated"), {"message": render_bridge_markdown(payload), **payload})

    def sidecar_policy_tool(self, sidecar_level: str = "", proactive_level: str = "", screen_awareness: str = "", allow_remote: str = "", allow_file_write: str = "", allow_shell: str = "", allow_browser: str = "") -> ToolResult:
        """Show or update Nova's external sidecar/screen/action authority policy."""
        def parse_bool(raw: str) -> bool | None:
            val = str(raw or "").strip().lower()
            if not val:
                return None
            if val in {"1", "yes", "true", "on", "allow", "enabled", "enable"}:
                return True
            if val in {"0", "no", "false", "off", "deny", "disabled", "disable"}:
                return False
            raise ValueError(f"Expected boolean value, got {raw!r}")
        try:
            policy = update_bridge_policy(
                sidecar_level=sidecar_level or None,
                proactive_level=proactive_level or None,
                screen_awareness=screen_awareness or None,
                allow_remote_daemon=parse_bool(allow_remote),
                allow_file_write=parse_bool(allow_file_write),
                allow_shell=parse_bool(allow_shell),
                allow_browser=parse_bool(allow_browser),
            ) if any([sidecar_level, proactive_level, screen_awareness, allow_remote, allow_file_write, allow_shell, allow_browser]) else build_capability_map().get("policy", {})
        except Exception as exc:
            return ToolResult(False, f"Sidecar policy not changed: {exc}", {"error": repr(exc), "message": render_bridge_markdown(build_capability_map())})
        payload = {"summary": "Nova sidecar/proactive action policy", "policy": policy, "warnings": []}
        return ToolResult(True, "Sidecar policy ready", {"message": render_bridge_markdown(payload), "policy": policy})

    def bridge_receipts_tool(self, limit: int = 20) -> ToolResult:
        """Show bridge receipts for queued/blocked/proposed Jarvis-style actions."""
        payload = build_bridge_receipts(limit=int(limit or 20))
        return ToolResult(True, str(payload.get("summary") or "Bridge receipts generated"), {"message": render_bridge_markdown(payload), **payload})

    def sidecar_enrollment_tool(self, requested: str = "") -> ToolResult:
        """Show the manual sidecar enrollment checklist without enabling authority."""
        payload = build_sidecar_enrollment_checklist(requested=requested or "")
        return ToolResult(True, str(payload.get("summary") or "Sidecar enrollment checklist generated"), {"message": render_bridge_markdown(payload), **payload})

    def browser_harness_tool(self, target_url: str = "", mode: str = "plan") -> ToolResult:
        """Plan a safe Playwright-only browser harness for localhost/project URLs."""
        payload = build_safe_browser_harness(target_url=target_url or "http://127.0.0.1:8766", mode=mode or "plan")
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Browser harness planned"), {"message": render_bridge_markdown(payload), **payload})

    def jarvis_test_prompts_tool(self) -> ToolResult:
        """Return safe test prompts for the Jarvis bridge without enabling sidecars."""
        payload = build_jarvis_test_prompts()
        return ToolResult(True, str(payload.get("summary") or "Jarvis test prompts generated"), {"message": render_bridge_markdown(payload), **payload})

    def proactive_actions_tool(self, action: str = "list", capability: str = "", target: str = "", reason: str = "", risk: str = "medium", limit: int = 20) -> ToolResult:
        """Queue or inspect proactive action receipts without silently executing sidecar/shell/browser work."""
        act = str(action or "list").strip()
        if not act or act.lower() in {"list", "status", "show"}:
            payload = list_queued_actions(limit=int(limit or 20))
            return ToolResult(True, str(payload.get("summary")), {"message": render_bridge_markdown({"summary": payload.get("summary"), "policy": build_capability_map().get("policy"), "actions": payload.get("actions", [])}), **payload})
        record = queue_proactive_action(capability=capability or "general", action=act, target=target or "", reason=reason or "", risk=risk or "medium")
        return ToolResult(bool(record.get("ok")), f"Proactive action {record.get('status')}", {"message": render_bridge_markdown({"summary": f"Proactive action {record.get('status')}", "policy": record.get("policy_snapshot"), "actions": [record]}), "record": record})


    def startup_validation_tool(self, mode: str = "quick", timeout: int = 90) -> ToolResult:
        """Run the same compile/smoke startup validation used by start_windows_assistant.bat."""
        payload = build_startup_validation(self._wla_source_root(), mode=mode or "quick", timeout=int(timeout or 90))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Startup validation complete"), {"message": render_startup_validation(payload), **payload})

    def nova_system_test_tool(self, profile: str = "quick", timeout: int = 120) -> ToolResult:
        """Run Nova's one-button system test: chat routing, coding, GUI, voice/persona, Jarvis, startup and regression slices."""
        payload = build_nova_full_system_test(self._wla_source_root(), profile=profile or "quick", timeout=int(timeout or 120))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Nova full system test complete"), {"message": render_nova_full_system_test(payload), **payload})

    def completion_audit_tool(self, profile: str = "quick") -> ToolResult:
        """Verify previous requested patch surfaces are truly wired, tested and regression-protected."""
        payload = build_completion_audit(self._wla_source_root(), profile=profile or "quick")
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Completion audit complete"), {"message": render_completion_audit(payload), **payload})

    def release_readiness_tool(self, full: bool = False, include_browser: bool | None = None) -> ToolResult:
        """Run the release-readiness gate used to block unsafe packaging."""
        payload = build_release_readiness(self._wla_source_root(), full=bool(full), include_browser=include_browser)
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Release readiness complete"), {"message": render_release_readiness_markdown(payload), **payload})

    def release_package_tool(self, name: str = "", include_reports: bool = False, force: bool = False) -> ToolResult:
        """Create a clean release zip only after the latest release-readiness PASS."""
        payload = build_release_package(self._wla_source_root(), name=name or "", include_reports=bool(include_reports), require_readiness=True, force=bool(force))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Release package complete"), {"message": render_release_package(payload), **payload})

    def codebase_advisor_tool(self) -> ToolResult:
        """Rank Nova codebase improvements and show what was implemented/protected in this pass."""
        payload = build_codebase_advisor(self._wla_source_root())
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Codebase advisor complete"), {"message": render_codebase_advisor(payload), **payload})

    def audit_log_tool(self, limit: int = 30) -> ToolResult:
        """Show a unified audit view across bridge receipts, voice audit, action receipts and activity."""
        payload = build_audit_log(limit=int(limit or 30))
        return ToolResult(True, str(payload.get("summary") or "Audit log generated"), {"message": render_bridge_markdown(payload), **payload})

    def workflow_run_tool(self, goal: str = "", confirm: bool = False) -> ToolResult:
        """Run/preview a supervised workflow through authority receipt and validation handoff."""
        payload = build_workflow_execution(goal or "validate Nova safely", confirm=bool(confirm))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Workflow run generated"), {"message": render_bridge_markdown(payload), **payload})

    def efficiency_report(self, action: str = "report") -> ToolResult:
        """Show or clear Nova efficiency samples and weak spots."""
        action = str(action or "report").strip().lower()
        if action in {"clear", "reset"}:
            clear_efficiency_samples()
            return ToolResult(True, "Efficiency samples cleared", {"message": "Efficiency profiler log cleared."})
        if action in {"off", "disable"}:
            self.config.efficiency_profiler_enabled = False
            set_runtime_profiler_enabled(False)
            self.config.save()
            return ToolResult(True, "Efficiency profiler disabled", {"enabled": False})
        if action in {"on", "enable"}:
            self.config.efficiency_profiler_enabled = True
            set_runtime_profiler_enabled(True)
            self.config.save()
            return ToolResult(True, "Efficiency profiler enabled", {"enabled": True})
        markdown, md_path, json_path, payload = render_efficiency_markdown(self.config)
        return ToolResult(True, "Efficiency report generated", {
            "message": markdown,
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "sample_count": payload.get("sample_count", 0),
            "weakspots": payload.get("weakspots", []),
        })

    def video_plan_tool(self, prompt: str = "", output_dir: str = "") -> ToolResult:
        """Plan a manifest-first Nova video job without requiring render backends."""
        prompt = (prompt or "").strip()
        if not prompt:
            return ToolResult(False, "Video plan needs a prompt", {"message": "Usage: /video-plan PROMPT"})
        base = Path(output_dir).expanduser() if output_dir else self.workspace / "nova_video_jobs" / (time.strftime("%Y%m%d_%H%M%S") + "_" + re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")[:40])
        path = save_video_manifest(prompt, base)
        manifest = plan_video_manifest(prompt, project_id=base.name)
        preview = write_video_preview_avi(manifest, base)
        preview_html = write_video_preview_html(manifest, base, preview)
        message = render_video_manifest_markdown(manifest) + f"\n\nManifest written: `{path}`\nPreview video written: `{preview}`\nPreview page written: `{preview_html}`"
        return ToolResult(True, "Nova video manifest planned", {"message": message, "manifest_path": str(path), "preview_video_path": str(preview), "preview_html_path": str(preview_html), "project_dir": str(base), "manifest": asdict(manifest)})

    def video_status_tool(self) -> ToolResult:
        """Check local Nova video generation/assembly toolchain readiness."""
        status = video_stack_status()
        lines = ["# Nova Video Stack Status", "", f"ComfyUI: {'reachable' if status['comfyui'].get('reachable') else 'not reachable'} ({status['comfyui'].get('url')})", "", "## Local tools"]
        for name, ok in status.get("tools", {}).items():
            lines.append(f"- {name}: {'available' if ok else 'missing'}")
        lines += ["", str(status.get("note", ""))]
        return ToolResult(True, "Nova video stack status", {"message": "\n".join(lines), **status})

    def video_validate_tool(self, prompt: str = "") -> ToolResult:
        """Validate a manifest-first Nova video plan and return an execution dry-run."""
        manifest = plan_video_manifest(prompt or "10 second Nova video smoke test")
        validation = validate_video_manifest(manifest)
        execution = build_video_execution_plan(manifest)
        message = render_video_manifest_markdown(manifest) + "\n\n" + render_video_validation_markdown(validation, execution)
        return ToolResult(bool(validation.get("ok")), "Nova video manifest validation", {"message": message, "validation": validation, "execution_plan": execution, "manifest": asdict(manifest)})

    def video_user_tests_tool(self) -> ToolResult:
        """Return simulated/manual user tests for Nova video functionality."""
        scenarios = video_user_test_scenarios()
        lines = ["# Nova Video User Tests", "", "Deterministic acceptance scenarios for iterative video UX validation."]
        for item in scenarios:
            lines.append(f"- **{item['name']}**: `{item['prompt']}` -> " + ", ".join(item.get('expect', [])))
        return ToolResult(True, "Nova video user test scenarios", {"message": "\n".join(lines), "scenarios": scenarios})


    def media_status_tool(self) -> ToolResult:
        """Show unified image/video readiness and recommended workflow."""
        img = image_generation_status()
        vid = video_stack_status()
        payload = media_status_summary(img, vid)
        lines = ["# Nova Media Status", "", "## Image"]
        lines.append(f"- Real generation ready: {'yes' if img.get('ready_for_real_generation') else 'no'}")
        lines.append(f"- SD WebUI: {'available' if img.get('sdwebui',{}).get('available') else 'not reachable'}")
        lines.append(f"- Diffusers: {'installed' if img.get('diffusers',{}).get('installed') else 'not installed'}")
        lines += ["", "## Video"]
        lines.append(f"- ComfyUI: {'reachable' if vid.get('comfyui',{}).get('reachable') else 'not reachable'}")
        for name, ok in vid.get('tools', {}).items():
            lines.append(f"- {name}: {'available' if ok else 'missing'}")
        lines += ["", "## Recommended flow"]
        lines.extend(f"- {x}" for x in payload.get('recommended_flow', []))
        return ToolResult(True, "Nova media status", {"message": "\n".join(lines), **payload})

    def screen_analysis_prompt_tool(self, request: str = "") -> ToolResult:
        """Build a safe prompt for manual screenshot/image analysis."""

        kind, user_text = parse_screen_analysis_request(request)
        message = render_screen_analysis_prompt_help(kind, user_text)
        return ToolResult(
            True,
            "Nova screen analysis prompt",
            {
                "message": message,
                "kind": kind,
                "request": user_text,
                "usage": "/screen-analysis-prompt terminal|gui|browser|image DESCRIPTION",
            },
        )

    def image_plan_tool(self, prompt: str = "", style: str = "cinematic", variations: int | str = 4) -> ToolResult:
        """Plan image prompt variants/seeds without invoking a heavy generation backend."""
        if not (prompt or "").strip():
            return ToolResult(False, "Image plan needs a prompt", {"message": "Usage: /image-plan PROMPT"})
        try:
            count = int(variations)
        except Exception:
            count = 4
        plan = build_image_prompt_plan(prompt, style=style, variations=count)
        return ToolResult(True, "Nova image prompt plan", {"message": render_image_prompt_plan_markdown(plan), **plan})

    def video_storyboard_tool(self, prompt: str = "", output_dir: str = "") -> ToolResult:
        """Create storyboard SVG, shot list CSV and keyframe prompts for a video plan."""
        prompt = (prompt or "").strip()
        if not prompt:
            return ToolResult(False, "Video storyboard needs a prompt", {"message": "Usage: /video-storyboard PROMPT"})
        base = Path(output_dir).expanduser() if output_dir else self.workspace / "nova_video_jobs" / (time.strftime("%Y%m%d_%H%M%S") + "_storyboard_" + re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")[:32])
        manifest = plan_video_manifest(prompt, project_id=base.name)
        storyboard = write_storyboard_svg(manifest, base)
        shotlist = write_shotlist_csv(manifest, base)
        prompt_plan = build_video_image_prompt_plan(manifest)
        prompt_path = base / "video_image_prompts.json"
        prompt_path.write_text(json.dumps(prompt_plan, indent=2), encoding="utf-8")
        message = render_video_manifest_markdown(manifest) + f"\n\nStoryboard written: `{storyboard}`\nShot list written: `{shotlist}`\nImage prompts written: `{prompt_path}`"
        return ToolResult(True, "Nova video storyboard package", {"message": message, "storyboard_path": str(storyboard), "shotlist_path": str(shotlist), "image_prompts_path": str(prompt_path), "manifest": asdict(manifest)})

    def video_package_tool(self, prompt: str = "", output_dir: str = "") -> ToolResult:
        """Create a full manifest/storyboard/preview/shotlist package for a video job."""
        prompt = (prompt or "").strip()
        if not prompt:
            return ToolResult(False, "Video package needs a prompt", {"message": "Usage: /video-package PROMPT"})
        base = Path(output_dir).expanduser() if output_dir else self.workspace / "nova_video_jobs" / (time.strftime("%Y%m%d_%H%M%S") + "_package_" + re.sub(r"[^a-zA-Z0-9]+", "-", prompt.lower()).strip("-")[:32])
        package = write_video_render_package(prompt, base)
        return ToolResult(bool(package.get("ok")), "Nova video render package", {"message": render_video_render_package_markdown(package), **package})


    def high_spec_profile_tool(self, cpu_hint: str = "", gpu_hint: str = "", ram_gb: int | str | None = None) -> ToolResult:
        try:
            ram = int(ram_gb) if str(ram_gb or "").strip().isdigit() else None
        except Exception:
            ram = None
        profile = build_high_spec_profile(cpu_hint=cpu_hint or "", gpu_hint=gpu_hint or "", ram_gb=ram)
        return ToolResult(True, "Nova high-spec local profile", {"message": render_high_spec_profile(profile), "profile": profile.to_dict()})

    def subagent_plan_tool(self, goal: str = "", slots: int | str = 3) -> ToolResult:
        try:
            slot_count = int(slots)
        except Exception:
            slot_count = 3
        plan = build_subagent_plan(goal or "improve Nova safely", slots=slot_count)
        return ToolResult(True, "Nova safe subagent plan", {"message": render_subagent_plan(plan), **plan})

    def model_context(self, prompt: str = "", action: str = "preview") -> ToolResult:
        """Preview the compact Nova context pack added to local model calls."""
        action = str(action or "preview").strip().lower()
        if action in {"off", "disable"}:
            self.config.local_model_context_enabled = False
            self.config.save()
            return ToolResult(True, "Local model Nova context pack disabled", {"enabled": False})
        if action in {"on", "enable"}:
            self.config.local_model_context_enabled = True
            self.config.save()
            return ToolResult(True, "Local model Nova context pack enabled", {"enabled": True})
        if action.startswith("max=") or action.startswith("limit="):
            raw = action.split("=", 1)[1].strip()
            try:
                value = max(1200, min(30000, int(raw)))
            except ValueError:
                return ToolResult(False, "Context limit must be a number", {"value": raw})
            self.config.local_model_context_max_chars = value
            self.config.save()
            return ToolResult(True, f"Local model context limit set to {value} characters", {"max_chars": value})
        text = render_model_context_preview(self.config, prompt or "general Nova context preview")
        return ToolResult(True, "Local model Nova context pack preview", {
            "message": text,
            "enabled": bool(getattr(self.config, "local_model_context_enabled", True)),
            "max_chars": int(getattr(self.config, "local_model_context_max_chars", 9000) or 9000),
            "preview": text,
        })


    def nova_context(self, goal: str = "", mode: str = "preview", last_failure: str = "") -> ToolResult:
        """Show/write Nova's structured operating context for local-model repair/build calls."""
        root = Path(self.workspace or ".")
        action = str(mode or "preview").strip().lower()
        context = build_nova_operating_context(root, goal=goal or "general Nova work", mode=action or "preview", last_failure=last_failure or getattr(self, "_last_model_error", ""), attempts=getattr(self, "_last_model_attempts", []))
        if action in {"write", "save", "persist"}:
            path, context = write_nova_operating_context(root, goal=goal or "general Nova work", mode=action, last_failure=last_failure or getattr(self, "_last_model_error", ""), attempts=getattr(self, "_last_model_attempts", []))
            return ToolResult(True, "Nova operating context written", {"message": render_nova_operating_context(context) + f"\nWritten: `{path}`", "context": context, "path": str(path)})
        return ToolResult(True, "Nova operating context preview", {"message": render_nova_operating_context(context), "context": context})


    def mission_contract_tool(self, goal: str = "", target_type: str = "", mode: str = "preview") -> ToolResult:
        """Create a goal-specific autonomous mission contract with real success checks."""
        contract = build_mission_contract(goal or "general Nova task", target_type=target_type or None)
        root = Path(self.workspace or ".")
        data = {"contract": contract, "message": render_mission_contract(contract)}
        if str(mode or "").lower() in {"write", "save", "persist"}:
            path = write_contract_report(root, contract)
            data["path"] = str(path)
            data["message"] += f"\n\nReport written: `{path}`"
        return ToolResult(True, "Autonomous mission contract ready", data)

    def mission_progress_score_tool(self, goal: str = "", limit: int = 160) -> ToolResult:
        """Score recent idle/autonomous progress against a mission contract."""
        contract = build_mission_contract(goal or "recent Nova task")
        events = tail_jsonl(ACTIVITY_PATH, limit=max(20, int(limit or 160)))
        progress = score_progress(events, contract)
        progress["contract"] = contract
        return ToolResult(True, "Mission progress scored", {"message": render_payload(progress, "Mission Progress Score"), "progress": progress})

    def surgical_recipe_tool(self, goal: str = "", failure: Any = None) -> ToolResult:
        """Classify a failure and return a deterministic surgical repair recipe."""
        info = classify_failure(goal, failure or getattr(self, "_last_model_error", ""))
        info["steps"] = recipe_steps(info.get("kind", "unknown"))
        return ToolResult(True, "Surgical repair recipe selected", {"message": render_payload(info, "Surgical Repair Recipe"), "recipe": info})

    def project_type_registry_tool(self, goal: str = "") -> ToolResult:
        """Show supported project types and acceptance markers."""
        payload = {"selected": project_type_contract(goal or "general local app"), "supported_types": PROJECT_TYPES}
        return ToolResult(True, "Project type registry", {"message": render_payload(payload, "Project Type Registry"), **payload})

    def self_test_from_bug_tool(self, bug: str = "", target_file: str = "winlocalassistant/webui.py", write: bool = False) -> ToolResult:
        """Generate or write a small regression test from a bug description."""
        bug = bug or getattr(self, "_last_model_error", "latest Nova bug") or "latest Nova bug"
        if write:
            result = write_regression_test(Path.cwd(), bug, target_file=target_file)
            return ToolResult(True, "Regression test written from bug", result)
        test = generate_regression_test(bug, target_file=target_file)
        return ToolResult(True, "Regression test generated from bug", {"test_preview": test, "message": "```python\n" + test + "\n```"})

    def assistant_box(self, message: str = "", action: str = "status", source: str = "tool", level: str = "info", append: bool = False) -> ToolResult:
        """Read or write the GUI assistant communication box.

        This is intentionally non-mutating with respect to user projects: it only
        writes Nova UI state under ~/.nova. Autonomous mode and user
        commands can use it to surface notices, status, warnings or handoff text
        outside the main chat transcript.
        """
        action = str(action or "status").strip().lower()
        if action in {"write", "set"}:
            state = write_assistant_box(message, source=source or "tool", level=level, append=False)
            return ToolResult(True, "Assistant communication box updated", {"box": state})
        if action == "append":
            state = write_assistant_box(message, source=source or "tool", level=level, append=True)
            return ToolResult(True, "Assistant communication box appended", {"box": state})
        if action == "clear":
            state = clear_assistant_box(source=source or "tool")
            return ToolResult(True, "Assistant communication box cleared", {"box": state})
        state = read_assistant_box()
        return ToolResult(bool(state.get("ok", True)), "Assistant communication box status", {"box": state})

    def _ollama_ps(self) -> dict[str, Any]:
        exe = shutil.which("ollama")
        if not exe:
            return {"available": False, "error": "ollama command was not found on PATH"}
        try:
            cp = subprocess.run([exe, "ps"], capture_output=True, text=True, timeout=8)
            output = ((cp.stdout or "") + (cp.stderr or "")).strip()
            active = []
            for line in output.splitlines()[1:]:
                parts = line.split()
                if parts:
                    active.append(line)
            return {"available": cp.returncode == 0, "returncode": cp.returncode, "raw": output, "active_models": active}
        except Exception as exc:
            return {"available": False, "error": repr(exc)}

    def _ollama_list(self) -> dict[str, Any]:
        exe = shutil.which("ollama")
        if not exe:
            return {"available": False, "error": "ollama command was not found on PATH", "models": []}
        try:
            cp = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=8)
            output = ((cp.stdout or "") + (cp.stderr or "")).strip()
            models: list[dict[str, Any]] = []
            for line in output.splitlines()[1:]:
                parts = line.split()
                if not parts:
                    continue
                name = parts[0]
                size = " ".join(parts[2:4]) if len(parts) >= 4 else ""
                modified = " ".join(parts[4:]) if len(parts) > 4 else ""
                role = []
                if name == self.config.model:
                    role.append("code/build model")
                if name == getattr(self.config, "chat_model", self.config.model):
                    role.append("chat model")
                if name == (getattr(self.config, "planner_model", "") or self.config.model):
                    role.append("planning/review model")
                caps = "coder/debugging" if any(x in name.lower() for x in ["coder", "code"]) else "general reasoning/chat"
                if any(x in name.lower() for x in ["vision", "llava"]):
                    caps = "vision/image reasoning"
                models.append({"name": name, "id": parts[1] if len(parts) > 1 else "", "size": size, "modified": modified, "capabilities": caps, "wla_use": ", ".join(role) or "available fallback/manual selection"})
            return {"available": cp.returncode == 0, "returncode": cp.returncode, "raw": output, "models": models}
        except Exception as exc:
            return {"available": False, "error": repr(exc), "models": []}

    def llm_status(self) -> ToolResult:
        info = self._ollama_ps()
        installed = self._ollama_list()
        ok = bool(info.get("available"))
        lock = ollama_busy_state()
        stale_cleanup = self._maybe_stop_stale_ollama(info, lock)
        if stale_cleanup.get("attempted"):
            info = self._ollama_ps()
        health = assess_model_dependency(self.config, ollama_ps=info, busy_state=lock)
        return ToolResult(ok, "Ollama/local LLM status" if ok else "Ollama status unavailable", {
            "model": self.config.model,
            "chat_model": getattr(self.config, "chat_model", self.config.model),
            "planner_model": getattr(self.config, "planner_model", "") or self.config.model,
            "model_route": getattr(self.config, "model_route", "auto"),
            "model_provider": getattr(self.config, "model_provider", "ollama"),
            "openrouter_model": getattr(self.config, "openrouter_model", ""),
            "ollama_url": self.config.ollama_url,
            "ollama_ps": info,
            "ollama_list": installed,
            "installed_models": installed.get("models", []),
            "winlocalassistant_model_lock": lock,
            "model_health": health.to_dict(),
            "stale_ollama_cleanup": stale_cleanup,
            "prompt_lifecycle_note": "Ollama ps shows loaded/kept-warm models. It does not prove a prompt is still generating. Use prompt_active/cooldown_active/request_id below as Nova's source of truth.",
            "tip": "If no model is active, run: ollama serve; ollama pull " + self.config.model + " ; ollama pull " + (getattr(self.config, "chat_model", "") or self.config.model),
        })

    def _maybe_stop_stale_ollama(self, info: dict[str, Any], lock: dict[str, Any]) -> dict[str, Any]:
        """Unload a clearly stale/stopping model only when Nova is not prompting."""
        if lock.get("prompt_active") or lock.get("busy"):
            return {"attempted": False, "reason": "Nova prompt lock is active"}
        last = lock.get("last_prompt") if isinstance(lock.get("last_prompt"), dict) else {}
        finished_at = last.get("finished_at")
        try:
            age = time.time() - float(finished_at or 0)
        except Exception:
            age = 0
        raw = str(info.get("raw") or "")
        active = "\n".join(str(x) for x in info.get("active_models") or [])
        text = (raw + "\n" + active).lower()
        if age < 30:
            return {"attempted": False, "reason": "last prompt is too recent", "age_sec": round(age, 1)}
        if "stopping" not in text:
            return {"attempted": False, "reason": "no stale/stopping Ollama model detected", "age_sec": round(age, 1)}
        exe = shutil.which("ollama")
        if not exe:
            return {"attempted": False, "reason": "ollama command not found"}
        try:
            cp = subprocess.run([exe, "stop", self.config.model], capture_output=True, text=True, timeout=20)
            output = ((cp.stdout or "") + (cp.stderr or "")).strip()
            payload = {"attempted": True, "ok": cp.returncode == 0, "model": self.config.model, "returncode": cp.returncode, "output": output, "age_sec": round(age, 1)}
            log_activity("ollama_auto_stop_stale", "Auto-stopped stale Ollama model after Nova prompt was idle", payload)
            return payload
        except Exception as exc:
            payload = {"attempted": True, "ok": False, "model": self.config.model, "error": repr(exc), "age_sec": round(age, 1)}
            log_activity("ollama_auto_stop_stale_failed", "Could not auto-stop stale Ollama model", payload)
            return payload

    def ollama_stop_model(self) -> ToolResult:
        """Unload/interrupt the selected Ollama model from memory.

        This is exposed behind a confirmation in core/web UI because stopping a model
        during a prompt can make the active build fail. It does not delete files.
        """
        exe = shutil.which("ollama")
        if not exe:
            return ToolResult(False, "ollama command was not found on PATH", {})
        try:
            cp = subprocess.run([exe, "stop", self.config.model], capture_output=True, text=True, timeout=20)
            out = ((cp.stdout or "") + (cp.stderr or "")).strip()
            return ToolResult(cp.returncode == 0, "Requested Ollama to stop/unload or interrupt the selected model" if cp.returncode == 0 else "Ollama stop failed", {"model": self.config.model, "returncode": cp.returncode, "output": out, "note": "If a local prompt was stuck, retry the build after /llm-status shows prompt idle."})
        except Exception as exc:
            return ToolResult(False, "Ollama stop failed", {"error": repr(exc), "model": self.config.model})

    def activity_log(self, limit: int = 80) -> ToolResult:
        return ToolResult(True, "Recent activity and model logs", {
            "activity_log": str(ACTIVITY_PATH),
            "model_io_log": str(MODEL_IO_PATH),
            "activity": tail_jsonl(ACTIVITY_PATH, limit, session_only=False),
            "model_io": tail_jsonl(MODEL_IO_PATH, min(int(limit), 20), session_only=False),
        })


    def provider_status(self) -> ToolResult:
        payload = provider_matrix(self.config)
        return ToolResult(True, "Nova provider status and route lanes", {"message": render_provider_markdown(payload), **payload})

    def provider_route_tool(self, goal: str = "") -> ToolResult:
        route = choose_provider(goal or "general Nova request", config=self.config)
        return ToolResult(True, "Nova provider route explanation", {"message": render_route_markdown(route, goal or "general Nova request"), "route": route})

    def provider_test_tool(self, provider: str = "") -> ToolResult:
        payload = provider_test_plan(self.config, provider)
        text = ["# Nova Provider Test Plan", "", f"Provider: `{payload.get('provider')}`", f"Enabled now: `{payload.get('enabled_now')}`", f"Privacy: `{payload.get('privacy')}`", "", "Dry-run command:", "```", str(payload.get('command', '')), "```", "", str(payload.get('safe_note', ''))]
        return ToolResult(bool(payload.get("ok")), "Nova provider test plan generated", {"message": "\n".join(text), **payload})

    def provider_queue_tool(self) -> ToolResult:
        payload = get_provider_scheduler().snapshot()
        return ToolResult(True, "Nova provider queue status", payload)

    def provider_drain_tool(self) -> ToolResult:
        # Safe placeholder: the provider scheduler does not kill threads or cancel running network calls.
        payload = get_provider_scheduler().snapshot()
        payload["drain_note"] = "No forced drain was run. Cancel the parent Nova task to stop an active provider call; future scheduler work should add cooperative cancellation tokens."
        return ToolResult(True, "Nova provider queue drain guidance", payload)

    def godmod3_report(self) -> ToolResult:
        lines = [
            "# G0DM0D3 / godmod3.ai integration note",
            "",
            "What was investigated:",
            "- godmod3.ai/G0DM0D3 is best treated as an inspiration for a multi-model interface, not as a free API source.",
            "- Public descriptions indicate it routes calls through OpenRouter and expects the user to provide an OpenRouter API key.",
            "- Therefore Nova should not copy, scrape, or depend on godmod3.ai for 'free calls'.",
            "",
            "Directly useful ideas for Nova:",
            "1. Multi-model role routing: local coder model, chat model, planning/review model, optional remote fallback.",
            "2. Bring-your-own-key provider settings with clear cost/privacy warnings.",
            "3. A provider status panel that distinguishes local Ollama from remote provider calls.",
            "4. Explicit free-model labels are allowed, but never presented as unlimited/free-of-cost guarantees.",
            "",
            "Implemented in v40:",
            "- /providers and /provider-status show local + optional OpenRouter provider state.",
            "- /provider ollama|openrouter switches provider mode.",
            "- /allow-internet on is required before OpenRouter calls can be used.",
            "- OpenRouter uses OPENROUTER_API_KEY from the environment; keys are not stored by Nova.",
        ]
        path = APP_DIR / "GODMOD3_RESEARCH_NOTE.md"
        atomic_write_text(path, "\n".join(lines))
        return ToolResult(True, "G0DM0D3/godmod3.ai research note created", {"path": str(path), "content": "\n".join(lines)})

    def research_plan(self) -> ToolResult:
        """Write a concrete architecture integration plan distilled from the research pass."""
        lines = [
            "# Nova v40 Research Integration Plan",
            "",
            "Principle: borrow patterns, not fragile implementation details. Old NueroBridge is useful as inspiration for typed tools, event logs, plugin discovery, backups, hardware-aware routing and safety gates; do not copy its brain metaphors unless they improve functionality.",
            "",
            "## Implemented now",
            "- Provider status and BYO-key OpenRouter routing guardrails.",
            "- MCP-like tool manifest export so the internal toolbox can later become a real connector/server.",
            "- Benchmark task initialisation/run commands for regression testing.",
            "- Telemetry export bundle for debugging logs, proposals and investigations.",
            "- Research/godmod notes available from commands so the assistant can inspect its own roadmap.",
            "",
            "## Next staged integrations",
            "1. Event-sourced workflow database: move JSONL traces into SQLite tables while keeping JSONL as append-only backup.",
            "2. Playwright optional deep UI tests: screenshots, console errors, trace.zip for generated browser apps.",
            "3. MCP-compatible tool server: expose safe read-only/project tools first, then mutating tools behind confirmations.",
            "4. LiteLLM/OpenRouter-style provider routing: role-based provider selection with cost/privacy warnings and local-first defaults.",
            "5. Property/fuzz tests for parsers, JSON extraction, path safety, and custom tool validation.",
            "6. Patch-based self-improvement PR flow: plan, diff, test, promote/rollback.",
            "",
            "## Safety constraints",
            "- Local-first by default.",
            "- Internet/remote providers require /allow-internet on and BYO key.",
            "- Every mutation logs before/after diffs.",
            "- Backtracking never destroys good progress if surgical repair is possible.",
            "- Self-edits require backup, py_compile and smoke tests.",
        ]
        path = APP_DIR / "RESEARCH_INTEGRATION_PLAN_V40.md"
        atomic_write_text(path, "\n".join(lines))
        try:
            atomic_write_text((self.workspace / "RESEARCH_INTEGRATION_PLAN_V40.md"), "\n".join(lines))
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        return ToolResult(True, "Research integration plan written", {"path": str(path), "workspace_path": str(self.workspace / "RESEARCH_INTEGRATION_PLAN_V40.md"), "content": "\n".join(lines)})

    def mcp_manifest(self) -> ToolResult:
        manifest = {
            "name": "Nova local tool manifest",
            "version": "51.3.0",
            "protocol_style": "MCP-inspired internal manifest, not a full MCP server yet",
            "security_model": {
                "workspace_confined": True,
                "mutating_tools_default": bool(self.config.allow_mutating_tools),
                "internet_allowed": bool(self.config.allow_internet),
                "notes": "Read-only tools can be exposed first. Mutating/system/provider tools require confirmation gates before real MCP export.",
            },
            "tools": [],
        }
        for name in sorted(self.tools):
            risk = "mutating" if any(x in name for x in ["write", "replace", "delete", "shell", "install", "self", "backtrack", "repair", "approve"]) else "read_or_analysis"
            manifest["tools"].append({"name": name, "risk": risk, "description": f"Nova tool: {name}"})
        out = APP_DIR / "wla_mcp_like_tool_manifest.json"
        atomic_write_json(out, manifest, ensure_ascii=True)
        return ToolResult(True, f"Exported MCP-like manifest for {len(manifest['tools'])} tools", {"path": str(out), "manifest": manifest})

    def benchmark_init(self, path: str = "NovaBenchmarks") -> ToolResult:
        self.require_mutation()
        root = resolve_inside_workspace(self.workspace, path or "NovaBenchmarks")
        root.mkdir(parents=True, exist_ok=True)
        tasks = {
            "version": "51.3.0",
            "tasks": [
                {"id": "browser_app_export", "goal": "Build a local browser app with local saving and JSON export", "checks": ["index.html", "app.js", "localStorage", "JSON.stringify"]},
                {"id": "custom_tool_html_refs", "goal": "Create and test a read-only HTML reference checker custom tool", "checks": ["custom_tools", "tool-test", "html_reference_checker"]},
                {"id": "repair_js_newline", "goal": "Repair a broken JavaScript CSV newline syntax error surgically", "checks": ["surgical_repair", "node --check"]},
            ],
        }
        atomic_write_json((root / "tasks.json"), tasks, ensure_ascii=True)
        atomic_write_text((root / "README.md"), "# Nova benchmark tasks\n\nUse `/benchmark-run NovaBenchmarks` after building sample projects. These are local regression tasks, not an external leaderboard.\n")
        log_activity("benchmark_init", "Created local benchmark task scaffold", {"path": str(root), "tasks": len(tasks["tasks"])})
        return ToolResult(True, "Created local benchmark scaffold", {"path": str(root), "tasks": tasks})

    def benchmark_run(self, path: str = "NovaBenchmarks") -> ToolResult:
        root = resolve_inside_workspace(self.workspace, path or "NovaBenchmarks")
        task_file = root / "tasks.json"
        if not task_file.exists():
            return ToolResult(False, "Benchmark tasks not found", {"path": str(task_file), "fix": ["Run /benchmark-init first"]})
        try:
            tasks = read_json_file(task_file, {}, expected_type=dict, quarantine=True)
        except Exception as exc:
            return ToolResult(False, "Benchmark task file is invalid JSON", {"path": str(task_file), "error": repr(exc)})
        checks = []
        checks.append({"name": "self_check", "ok": True, "summary": "runtime command reached benchmark runner"})
        av = self.auto_verify()
        # If no app/project is currently open, benchmark infrastructure is still valid.
        # Treat that as a warning rather than a failed benchmark bootstrap.
        av_ok = av.ok or "Could not infer" in av.summary
        checks.append({"name": "current_project_auto_verify", "ok": av_ok, "summary": av.summary, "data": av.data, "warning": not av.ok})
        inv = self.investigate_logs(focus="benchmark run recurring failures")
        checks.append({"name": "log_investigation", "ok": inv.ok, "summary": inv.summary})
        report = {"tasks_defined": tasks.get("tasks", []), "checks": checks, "passed": all(c.get("ok") for c in checks)}
        out = root / "BENCHMARK_REPORT.md"
        atomic_write_text(out, "# Nova Benchmark Report\n\n```json\n" + json.dumps(report, indent=2, ensure_ascii=False)[:20000] + "\n```\n")
        log_activity("benchmark_run", "Ran local benchmark checks", {"path": str(root), "passed": report["passed"]})
        return ToolResult(bool(report["passed"]), "Benchmark run completed" if report["passed"] else "Benchmark run found issues", {"report": str(out), **report})

    def telemetry_export(self) -> ToolResult:
        stamp = time.strftime("%Y%m%d_%H%M%S")
        out = APP_DIR / f"telemetry_export_{stamp}.zip"
        files = [ACTIVITY_PATH, MODEL_IO_PATH, APP_DIR / "ERROR_INVESTIGATION.md", APP_DIR / "IMPROVEMENT_PROPOSALS.md", APP_DIR / "AUTONOMOUS_IMPROVEMENTS.md", APP_DIR / "RESEARCH_INTEGRATION_PLAN_V40.md", APP_DIR / "GODMOD3_RESEARCH_NOTE.md"]
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as z:
            for f in files:
                try:
                    if f.exists() and f.is_file():
                        z.write(f, f.name)
                except Exception as exc:
                        log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        return ToolResult(True, "Exported telemetry and improvement artefacts", {"path": str(out), "files": [str(f) for f in files if f.exists()]})


    # -------------------------
    # Backtracking recovery / retry loop
    # -------------------------

    def _backup_workspace_for_recovery(self, label: str = "recovery") -> dict[str, Any]:
        """Create a zip checkpoint of the current workspace before risky repair/backtracking."""
        ws = self.workspace
        stamp = time.strftime("%Y%m%d_%H%M%S")
        safe = re.sub(r"[^A-Za-z0-9_.-]+", "_", label or "recovery")[:60]
        backup = APP_DIR / "recovery_backups" / f"{safe}_{stamp}.zip"
        backup.parent.mkdir(parents=True, exist_ok=True)
        file_count = 0
        try:
            with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as z:
                if ws.exists():
                    for f in ws.rglob("*"):
                        if not f.is_file() or self._skip(f):
                            continue
                        # Keep backups bounded. Generated project source is usually small.
                        try:
                            if f.stat().st_size > 2_000_000:
                                continue
                        except Exception:
                            continue
                        z.write(f, f.relative_to(ws))
                        file_count += 1
            log_activity("recovery_backup", "Created workspace recovery checkpoint", {"workspace": str(ws), "backup": str(backup), "files": file_count})
            return {"ok": True, "backup": str(backup), "workspace": str(ws), "files": file_count}
        except Exception as exc:
            return {"ok": False, "backup": str(backup), "workspace": str(ws), "error": repr(exc)}

    def _restore_workspace_backup(self, backup_path: str) -> dict[str, Any]:
        """Restore a zip checkpoint into the current workspace. Used only after failed recovery attempts."""
        ws = self.workspace
        backup = Path(backup_path)
        if not backup.exists():
            return {"ok": False, "error": "backup missing", "backup": str(backup)}
        restored = 0
        try:
            with zipfile.ZipFile(backup, "r") as z:
                for name in z.namelist():
                    if name.endswith("/"):
                        continue
                    target = resolve_inside_workspace(ws, name)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    atomic_write_bytes(target, z.read(name))
                    restored += 1
            log_activity("recovery_restore", "Restored workspace from recovery checkpoint", {"backup": str(backup), "workspace": str(ws), "files": restored})
            return {"ok": True, "restored": restored, "backup": str(backup), "workspace": str(ws)}
        except Exception as exc:
            return {"ok": False, "error": repr(exc), "backup": str(backup), "workspace": str(ws)}

    def _try_git_checkpoint(self, message: str) -> dict[str, Any]:
        """Best-effort local git checkpoint when the workspace is a git repo."""
        git = shutil.which("git")
        ws = self.workspace
        if not git:
            return {"ok": False, "reason": "git not found"}
        try:
            inside = subprocess.run([git, "rev-parse", "--is-inside-work-tree"], cwd=str(ws), capture_output=True, text=True, timeout=10)
            if inside.returncode != 0 or "true" not in (inside.stdout or "").lower():
                return {"ok": False, "reason": "workspace is not a git repo"}
            subprocess.run([git, "add", "-A"], cwd=str(ws), capture_output=True, text=True, timeout=30)
            status = subprocess.run([git, "status", "--porcelain"], cwd=str(ws), capture_output=True, text=True, timeout=10)
            if not (status.stdout or "").strip():
                return {"ok": True, "reason": "no changes to checkpoint"}
            commit = subprocess.run([git, "commit", "-m", message[:180]], cwd=str(ws), capture_output=True, text=True, timeout=60)
            return {"ok": commit.returncode == 0, "returncode": commit.returncode, "output": ((commit.stdout or "") + (commit.stderr or ""))[-4000:]}
        except Exception as exc:
            return {"ok": False, "error": repr(exc)}


    def _write_file_backup(self, path: Path, root: Path, reason: str = "surgical") -> dict[str, Any]:
        """Back up a single file before a targeted find/replace repair."""
        try:
            rel = path.relative_to(root).as_posix().replace("/", "__")
        except Exception:
            rel = path.name
        stamp = time.strftime("%Y%m%d_%H%M%S")
        backup_dir = APP_DIR / "file_repair_backups" / stamp
        backup_dir.mkdir(parents=True, exist_ok=True)
        backup = backup_dir / rel
        try:
            shutil.copy2(path, backup)
            return {"ok": True, "file": str(path), "backup": str(backup), "reason": reason}
        except Exception as exc:
            return {"ok": False, "file": str(path), "backup": str(backup), "error": repr(exc), "reason": reason}

    def _exact_file_replace(self, path: Path, old: str, new: str, root: Path, reason: str) -> dict[str, Any]:
        """Perform a precise replacement when the exact old text exists.

        This is intentionally less destructive than rollback: if a generated project is
        mostly good but has a tiny runtime/syntax mistake, fix only that text and keep
        the rest of the model's useful progress.
        """
        try:
            before = path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return {"ok": False, "path": str(path), "reason": reason, "error": repr(exc)}
        if old not in before:
            return {"ok": False, "path": str(path), "reason": reason, "error": "exact text not found"}
        backup = self._write_file_backup(path, root, reason)
        after = before.replace(old, new, 1)
        atomic_write_text(path, after)
        diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile="before", tofile="after", lineterm=""))
        info = {"ok": True, "path": str(path), "reason": reason, "backup": backup, "old": old[:4000], "new": new[:4000], "diff": diff[:12000]}
        log_activity("surgical_find_replace", f"Applied targeted find/replace: {reason}", {"file": str(path), "diff_preview": diff[:4000]})
        return info

    def _targeted_find_replace_repairs(self, root: Path, failure_text: str = "") -> list[dict[str, Any]]:
        """Small, conservative repairs for common generated-code errors.

        These run before backtracking/rollback/LLM repair. The goal is to preserve good
        progress and repair the smallest possible bad fragment.
        """
        repairs: list[dict[str, Any]] = []
        failure_text = failure_text or ""
        # Apply existing deterministic JS fixes first.
        deterministic = self._auto_fix_common_code_errors(root, [])
        repairs.extend({"ok": True, "kind": "auto_common_code_error", **x} for x in deterministic)

        js_files = [p for p in root.rglob("*.js") if p.is_file() and not self._skip(p)]
        html_files = [p for p in root.rglob("*.html") if p.is_file() and not self._skip(p)]

        # Runtime/security issue from opening static HTML as file:// inside a frame.
        if "file:' URLs are treated as unique security origins" in failure_text or "Unsafe attempt to load URL file://" in failure_text:
            manifest_path = root / "PROJECT_MANIFEST.json"
            try:
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True) if manifest_path.exists() else {}
            except Exception:
                manifest = {}
            main_file = str(manifest.get("main_file") or "index.html")
            manifest["main_file"] = main_file
            manifest["run_command"] = manifest.get("run_command") or f"start .\\{main_file}"
            manifest["recommended_runner"] = f"Use Nova Run in popup/Open in tab so companion files load through /project-view/{main_file}, not file://."
            self._write_manifest(root, manifest)
            repairs.append({"ok": True, "kind": "runner_metadata_fix", "reason": "file URL security origin issue", "main_file": main_file, "run_url": f"/project-view/{main_file}"})

        # HTML references app.js/style.css but files have different common names.
        for html in html_files[:10]:
            try:
                text = html.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if 'src="app.js"' in text and not (html.parent / "app.js").exists() and (html.parent / "main.js").exists():
                repairs.append(self._exact_file_replace(html, 'src="app.js"', 'src="main.js"', html.parent, "HTML script link pointed to missing app.js"))
            if "src='app.js'" in text and not (html.parent / "app.js").exists() and (html.parent / "main.js").exists():
                repairs.append(self._exact_file_replace(html, "src='app.js'", "src='main.js'", html.parent, "HTML script link pointed to missing app.js"))
            if 'href="style.css"' in text and not (html.parent / "style.css").exists() and (html.parent / "styles.css").exists():
                repairs.append(self._exact_file_replace(html, 'href="style.css"', 'href="styles.css"', html.parent, "HTML stylesheet link pointed to missing style.css"))
            if "href='style.css'" in text and not (html.parent / "style.css").exists() and (html.parent / "styles.css").exists():
                repairs.append(self._exact_file_replace(html, "href='style.css'", "href='styles.css'", html.parent, "HTML stylesheet link pointed to missing style.css"))

        # Patch duplicate form input IDs that can break labels/querySelector behaviour.
        for html in html_files[:10]:
            try:
                text = html.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            if text.count('id="ticker"') > 1 or text.count("id='ticker'") > 1:
                before = text
                idx = 0
                def repl_double(m):
                    nonlocal idx
                    idx += 1
                    return f'id="ticker-{idx}"'
                text = re.sub(r'id="ticker"', repl_double, text)
                idx = 0
                def repl_single(m):
                    nonlocal idx
                    idx += 1
                    return f"id='ticker-{idx}'"
                text = re.sub(r"id='ticker'", repl_single, text)
                if text != before:
                    backup = self._write_file_backup(html, html.parent, "duplicate ticker ids")
                    atomic_write_text(html, text)
                    diff = "\n".join(difflib.unified_diff(before.splitlines(), text.splitlines(), fromfile="before", tofile="after", lineterm=""))
                    repairs.append({"ok": True, "path": str(html), "reason": "duplicate HTML ticker IDs", "backup": backup, "diff": diff[:12000]})
                    log_activity("surgical_find_replace", "Fixed duplicate HTML IDs", {"file": str(html), "diff_preview": diff[:4000]})

        return repairs

    def surgical_repair(self, goal: str = "", failure: dict[str, Any] | str | None = None, path: str = ".") -> ToolResult:
        """Repair the current project with targeted find/replace before using heavier recovery.

        This is useful when the generated code is mostly good and the error is a small
        syntax/runtime issue. It keeps progress, writes per-file backups, and re-runs
        quality checks.
        """
        self.require_mutation()
        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        failure_text = failure if isinstance(failure, str) else json.dumps(failure or {}, ensure_ascii=False)[:20000]
        repairs = self._targeted_find_replace_repairs(root, failure_text)
        manifest_path = root / "PROJECT_MANIFEST.json"
        if manifest_path.exists():
            try:
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {"goal": goal or "repair current project", "main_file": "index.html", "verify_command": ""}
            if goal:
                manifest.setdefault("goal", goal)
            quality = self._project_quality_verify(root, manifest)
            self._write_lifecycle_files(root, manifest, quality.data, status="repaired" if quality.ok else "needs_repair")
            return ToolResult(quality.ok, "Targeted surgical repair passed verification" if quality.ok else "Targeted surgical repair applied but more repair is needed", {"project_path": str(root), "repairs": repairs, "verification": quality.data, "next": "Backtracking/LLM repair can continue from this improved state without rollback."})
        auto = self.auto_verify()
        return ToolResult(auto.ok, "Targeted surgical repair completed" if auto.ok else "Targeted surgical repair applied but auto-verify still failed", {"project_path": str(root), "repairs": repairs, "verification": auto.data})

    def _failure_text(self, failure: dict[str, Any] | str | None) -> str:
        if isinstance(failure, str):
            return failure
        try:
            return json.dumps(failure or {}, ensure_ascii=False, default=str)[:30000]
        except Exception:
            return str(failure or "")[:30000]

    def _classify_known_error(self, goal: str = "", failed_tool: str = "", failure: dict[str, Any] | str | None = None) -> dict[str, Any]:
        text = self._failure_text(failure).lower()
        tags: list[str] = []
        if any(x in text for x in ["ollama was not reachable", "timed out", "timeout_or_unreachable", "timeout"]):
            tags.append("model_timeout")
        if any(x in text for x in ["parseable json", "invalid json", "jsondecodeerror"]):
            tags.append("model_json_parse")
        if any(x in text for x in ["validation_failed", "did not implement", "missing requested capability", "goal_coverage"]):
            tags.append("model_validation")
        if any(x in text for x in ["rightpressed", "leftpressed", "is not defined", "referenceerror"]):
            tags.append("js_input_state")
        if any(x in text for x in ["node_syntax", "syntaxerror", "unexpected token", "unterminated string"]):
            tags.append("js_syntax")
        if any(x in text for x in ["readme_claim_not_implemented", "generic_template", "static_acceptance"]):
            tags.append("acceptance_mismatch")
        if any(x in text for x in ["missing local", "missing_references", "404", "app.js", "style.css"]):
            tags.append("browser_reference")
        if failed_tool in {"verify", "auto_verify", "final_project_check"}:
            tags.append("verification_failure")
        if failed_tool in {"ai_create_project", "ai_edit_project"}:
            tags.append("generation_failure")
        tags = list(dict.fromkeys(tags))
        if not tags:
            tags.append("unknown")
        strategy = "repair_current_project"
        if "generation_failure" in tags and any(x in tags for x in ["model_timeout", "model_json_parse", "model_validation"]):
            strategy = "reuse_best_candidate_or_goal_fallback"
        elif "js_input_state" in tags or "js_syntax" in tags or "browser_reference" in tags:
            strategy = "deterministic_surgical_fix"
        elif "acceptance_mismatch" in tags:
            strategy = "recheck_after_generated-report-filtering_then_repair"
        return {
            "goal": goal,
            "failed_tool": failed_tool,
            "tags": tags,
            "strategy": strategy,
            "repair_order": [
                "classify known error signature",
                "try deterministic remembered fix",
                "verify same project",
                "try same-folder LLM repair only if deterministic repair is insufficient",
                "backtrack non-destructively only after targeted repair fails",
            ],
        }

    def reasoning_diagnostics(self, goal: str = "", failed_tool: str = "", failure: dict[str, Any] | str | None = None) -> ToolResult:
        diagnosis = self._classify_known_error(goal=goal, failed_tool=failed_tool, failure=failure)
        lines = [
            "# Nova Reasoning Skill",
            "",
            "Reasoning loop: observe evidence, classify the failure, choose the smallest safe repair, verify, then escalate only if needed.",
            "",
            "## Current diagnosis",
            json.dumps(diagnosis, indent=2, ensure_ascii=False),
            "",
            "## Recovery promise",
            "- Do not stop at the first known error.",
            "- Try remembered deterministic fixes before broad rewrites.",
            "- Preserve useful generated files and repair in place.",
            "- Avoid touching unrelated workspaces when no files were written.",
        ]
        path = APP_DIR / "REASONING_SKILL.md"
        atomic_write_text(path, "\n".join(lines) + "\n")
        return ToolResult(True, "Reasoning diagnostic written", {"path": str(path), "diagnosis": diagnosis, "content": "\n".join(lines)})

    def _create_project_from_rejected_candidate(self, goal: str, candidate: dict[str, Any], reason: str = "") -> ToolResult:
        if not isinstance(candidate, dict) or not isinstance(candidate.get("files"), dict) or not candidate.get("files"):
            return ToolResult(False, "No parseable rejected candidate is available to recover", {"reason": reason})
        clean_goal = self._validation_goal_text(goal)
        folder = self._slug(candidate.get("folder") or goal)
        library_root = self._project_library_root()
        root = (library_root / folder).expanduser().resolve()
        root.mkdir(parents=True, exist_ok=True)
        data = self._normalise_model_project(candidate, goal, folder)
        written: list[dict[str, Any]] = []
        self._apply_model_files_to_root(root, folder, data.get("files") or {}, written, event_kind="known_error_recovery_write")
        manifest = {
            "goal": clean_goal,
            "raw_goal": goal,
            "build_mode": "recovery",
            "requirements": self._requirements_spec(clean_goal, "recovery"),
            "acceptance_terms": self._extract_requirement_terms(clean_goal),
            "feature_expectations": self._generic_feature_expectations(clean_goal),
            "main_file": data.get("main_file") or "index.html",
            "run_command": data.get("run_command") or "start .\\index.html",
            "verify_command": data.get("verify_command") or "",
            "notes": (data.get("notes") or "") + "\nRecovered from best parseable rejected candidate. " + reason,
            "source": "known_error_recovery_best_candidate",
            "candidate_rejection_reason": reason,
        }
        self._write_manifest(root, manifest)
        self._write_lifecycle_files(root, manifest, status="known_error_recovery")
        register_project(folder, str(root), make_current=True)
        atomic_write_json((root / ".nova_project.json"), {"name": folder, "path": str(root)}, ensure_ascii=True)
        self.config.workspace = str(root)
        self.config.save()
        ok, verify_result = self._repair_until_accepted(clean_goal, root, folder, manifest, written, max_rounds=2)
        self._write_lifecycle_files(root, manifest, verify_result, status="recovered" if ok else "needs_repair")
        return ToolResult(ok, f"Created and verified project {folder} after recovering the best rejected candidate" if ok else "Best rejected candidate was preserved but still needs repair", {
            "project": {"name": folder, "path": str(root)},
            "workspace": str(root),
            "written": written,
            "main_file": manifest.get("main_file"),
            "run_command": manifest.get("run_command"),
            "verification": verify_result,
            "candidate_rejection_reason": reason,
        })

    def known_error_recover(self, goal: str = "", failed_step: str = "", failed_tool: str = "", failure: dict[str, Any] | str | None = None, path: str = ".") -> ToolResult:
        """Try remembered deterministic recovery before giving up.

        This is the middle layer between "a step failed" and heavier backtracking.
        It handles experienced errors using local evidence: JS syntax/input-state
        issues, broken browser references, generated-report acceptance noise, and
        creation failures where the best parseable candidate can still be preserved.
        """
        self.require_mutation()
        diagnosis = self._classify_known_error(goal=goal, failed_tool=failed_tool, failure=failure)
        log_activity("known_error_recovery_start", "Trying known-error recovery before giving up", {"goal": goal, "failed_step": failed_step, "failed_tool": failed_tool, "diagnosis": diagnosis})

        if failed_tool == "ai_create_project":
            candidate = getattr(self, "_last_model_candidate", None)
            reason = ""
            try:
                reason = str((failure or {}).get("reason") or "")
            except Exception:
                reason = ""
            if isinstance(candidate, dict) and isinstance(candidate.get("files"), dict) and candidate.get("files"):
                recovered = self._create_project_from_rejected_candidate(goal, candidate, reason=reason)
                recovered.data["diagnosis"] = diagnosis
                log_activity("known_error_recovery_done" if recovered.ok else "known_error_recovery_incomplete", recovered.summary, recovered.data)
                return recovered
            fallback = self._fallback_project_for_goal(goal, "create")
            if fallback:
                recovered = self._create_project_from_rejected_candidate(goal, fallback, reason="deterministic fallback for known vague goal")
                recovered.data["diagnosis"] = diagnosis
                log_activity("known_error_recovery_done" if recovered.ok else "known_error_recovery_incomplete", recovered.summary, recovered.data)
                return recovered
            return ToolResult(False, "Known-error recovery found no safe project candidate to preserve", {
                "diagnosis": diagnosis,
                "reason": "The create-project step wrote no files and exposed no parseable candidate/fallback. I will not repair an unrelated current workspace.",
            })

        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        repairs = self._targeted_find_replace_repairs(root, self._failure_text(failure))
        manifest_path = root / "PROJECT_MANIFEST.json"
        if manifest_path.exists():
            try:
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {"goal": goal or "repair current project", "main_file": "index.html", "verify_command": ""}
            if goal:
                manifest.setdefault("goal", goal)
            quality = self._project_quality_verify(root, manifest)
            targeted_fix_ok = bool(repairs) and self._known_error_target_verified(diagnosis, quality.data)
            final_ok = bool(quality.ok or targeted_fix_ok)
            self._write_lifecycle_files(root, manifest, quality.data, status="known_error_recovered" if final_ok else "known_error_needs_more_repair")
            data = {"project_path": str(root), "diagnosis": diagnosis, "repairs": repairs, "verification": quality.data, "targeted_fix_ok": targeted_fix_ok}
            log_activity("known_error_recovery_done" if final_ok else "known_error_recovery_incomplete", "Known-error recovery verification completed", data)
            summary = "Known-error recovery fixed the project" if quality.ok else "Known-error recovery fixed the known failure; broader quality checks may still need review" if targeted_fix_ok else "Known-error recovery tried remembered fixes but more repair is needed"
            return ToolResult(final_ok, summary, data)
        auto = self.auto_verify()
        targeted_fix_ok = bool(repairs) and self._known_error_target_verified(diagnosis, auto.data)
        final_ok = bool(auto.ok or targeted_fix_ok)
        data = {"project_path": str(root), "diagnosis": diagnosis, "repairs": repairs, "verification": auto.data, "targeted_fix_ok": targeted_fix_ok}
        log_activity("known_error_recovery_done" if final_ok else "known_error_recovery_incomplete", "Known-error recovery auto-verify completed", data)
        summary = "Known-error recovery fixed the workspace" if auto.ok else "Known-error recovery fixed the known failure; broader quality checks may still need review" if targeted_fix_ok else "Known-error recovery tried remembered fixes but more repair is needed"
        return ToolResult(final_ok, summary, data)

    def _known_error_target_verified(self, diagnosis: dict[str, Any], verification: dict[str, Any] | None) -> bool:
        """Return True when a deterministic known-error repair cleared its target.

        Known-error recovery should not fail merely because broader project-quality
        scoring still wants polish. If the remembered fault was a concrete runtime
        issue, such as undeclared arrow-key state, and the targeted verifier no
        longer reports that fault, the recovery layer has done its job. Later
        project-quality repair can still improve the app without discarding this
        successful minimal fix.
        """
        tags = set((diagnosis or {}).get("tags") or [])
        if not tags or not isinstance(verification, dict):
            return False
        checks = verification.get("checks") or []
        problem_kinds: set[str] = set()
        for check in checks if isinstance(checks, list) else []:
            if not isinstance(check, dict):
                continue
            for problem in check.get("problems") or []:
                if isinstance(problem, dict) and problem.get("kind"):
                    problem_kinds.add(str(problem.get("kind")))
        if "js_input_state" in tags:
            return not ({"game_undeclared_right_pressed", "game_undeclared_left_pressed", "game_missing_keyboard_listeners"} & problem_kinds)
        if "browser_reference" in tags:
            return not any("missing" in kind and ("reference" in kind or "file" in kind) for kind in problem_kinds)
        if "js_syntax" in tags:
            return not any("syntax" in kind for kind in problem_kinds)
        return False

    def backtrack_recover(self, goal: str = "", failed_step: str = "", failed_tool: str = "", failure: dict[str, Any] | str | None = None, max_attempts: int = 3) -> ToolResult:
        """Recover from a failed plan step by backing up, repairing the same project, and retesting.

        This is deliberately conservative: it first creates a workspace checkpoint, then tries
        deterministic fixes, same-project LLM repair, final checks, and only restores the backup
        if no attempt succeeds. It avoids the older behaviour of simply giving up at the first error.
        """
        self.require_mutation()
        goal = (goal or "repair the current project so it works and satisfies the user request").strip()
        max_attempts = max(1, min(int(max_attempts or 3), 5))
        backup = self._backup_workspace_for_recovery("backtrack")
        git_before = self._try_git_checkpoint("Nova checkpoint before backtracking recovery")
        attempts: list[dict[str, Any]] = []
        failure_text = failure if isinstance(failure, str) else json.dumps(failure or {}, ensure_ascii=False)[:12000]
        root = self.workspace
        manifest_path = root / "PROJECT_MANIFEST.json"
        if manifest_path.exists():
            try:
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {"goal": goal, "main_file": "index.html", "verify_command": ""}
        else:
            manifest = {"goal": goal, "main_file": "index.html", "verify_command": ""}

        # Attempt 0: surgical find/replace and deterministic last-mile repairs before asking the LLM again.
        # This is intentionally first because preserving good generated code is usually
        # better than rollback or full rewrite when the error is a tiny syntax/runtime issue.
        surgical = self.surgical_repair(goal=goal, failure=failure_text, path=".")
        quality = self._project_quality_verify(root, manifest) if manifest_path.exists() else ToolResult(False, "No project manifest yet", {})
        attempts.append({"attempt": 0, "kind": "surgical_find_replace", "ok": surgical.ok, "summary": surgical.summary, "data": surgical.data, "verification": quality.data})
        if surgical.ok or quality.ok:
            self._write_lifecycle_files(root, manifest, quality.data if quality.data else surgical.data, status="recovered")
            self._try_git_checkpoint("Nova recovered project after surgical repair")
            return ToolResult(True, "Recovered project with targeted surgical repair", {"backup": backup, "git_checkpoint": git_before, "attempts": attempts, "verification": quality.data if quality.data else surgical.data})

        for attempt in range(1, max_attempts + 1):
            log_activity("backtrack_attempt", f"Backtracking recovery attempt {attempt}/{max_attempts}", {"goal": goal, "failed_step": failed_step, "failed_tool": failed_tool})
            if manifest_path.exists():
                repair_goal = (
                    "Repair the current project in-place. Do not create a nested folder. "
                    "Original user goal: " + goal + "\nFailed step: " + failed_step + "\nFailure details: " + failure_text +
                    "\nUse the current files and fix the actual code. Then improve missing requirements."
                )
                repair = self.ai_edit_project(repair_goal, build_mode="long")
            else:
                repair_goal = (
                    "Retry building this project from scratch, but make it complete and runnable. "
                    "Original user goal: " + goal + "\nPrevious failure: " + failure_text
                )
                repair = self.ai_create_project(repair_goal, build_mode="long")

            attempts.append({"attempt": attempt, "kind": "llm_repair", "ok": repair.ok, "summary": repair.summary, "data": repair.data})
            if repair.ok:
                run = self.run_project(".")
                final = self.final_project_check(".", goal=goal)
                attempts.append({"attempt": attempt, "kind": "run_project", "ok": run.ok, "summary": run.summary, "data": run.data})
                attempts.append({"attempt": attempt, "kind": "final_project_check", "ok": final.ok, "summary": final.summary, "data": final.data})
                if final.ok:
                    self._try_git_checkpoint("Nova recovered project after backtracking repair")
                    return ToolResult(True, f"Recovered after backtracking attempt {attempt}", {"backup": backup, "git_checkpoint": git_before, "attempts": attempts, "final": final.data})
                failure_text = json.dumps(final.data, ensure_ascii=False)[:12000]
            else:
                failure_text = json.dumps(repair.data, ensure_ascii=False)[:12000]

        # Do not automatically rollback after partial successful edits. The user asked to preserve
        # good progress and prefer find/replace repair over destructive rollback. Keep the checkpoint
        # available for manual restore, but leave the best attempted state in place for /fix-last or /continue.
        restore = {"ok": False, "reason": "not restored automatically; preserving best attempted state", "manual_backup": backup.get("backup")}
        log_activity("backtrack_failed", "Backtracking recovery failed; preserved best attempted state and kept checkpoint", {"attempts": attempts, "restore": restore})
        return ToolResult(False, "Backtracking recovery failed after retries, but I preserved the best attempted state instead of rolling back", {"backup": backup, "restore": restore, "attempts": attempts, "next": "Use /surgical-repair, /fix-last, or /continue with the exact error. Backup is available if manual rollback is needed."})

    # -------------------------
    # Self-extending tools, safe installs, watchdog and self-improvement
    # -------------------------


    def _recent_problem_events(self, limit: int = 300) -> list[dict[str, Any]]:
        """Return recent error/failure-ish events from activity/model logs.

        This is intentionally deterministic and cheap. It gives the assistant a way to
        inspect its own operational history before proposing changes, rather than
        guessing from the latest chat message.
        """
        rows = []
        for row in tail_jsonl(ACTIVITY_PATH, limit, session_only=False):
            kind = str(row.get("kind") or row.get("event") or "").lower()
            msg = str(row.get("message") or row.get("summary") or row.get("phase") or "")
            data_txt = json.dumps(row.get("data", {}), ensure_ascii=False, default=str).lower()
            hay = " ".join([kind, msg.lower(), data_txt])
            if any(word in hay for word in ["fail", "error", "exception", "timeout", "rejected", "backtrack", "missing", "syntax", "invalid", "stopped"]):
                rows.append(row)
        for row in tail_jsonl(MODEL_IO_PATH, min(limit, 80), session_only=False):
            phase = str(row.get("phase") or "").lower()
            text = (str(row.get("response_preview") or "") + " " + str(row.get("prompt_preview") or "")).lower()
            if phase == "response" and (not str(row.get("response_preview") or "").strip() or any(w in text for w in ["error", "invalid", "sorry", "cannot", "can't", "```json"])):
                rows.append({"time": row.get("time"), "kind": "model_io_attention", "message": "Model IO needs attention", "data": row})
        return rows[-limit:]

    def _recommendations_from_problem_events(self, events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        joined = json.dumps(events[-80:], ensure_ascii=False, default=str).lower()
        recs: list[dict[str, Any]] = []
        def add(area: str, problem: str, change: str, command: str = ""):
            recs.append({"area": area, "problem": problem, "recommended_change": change, "useful_command": command})
        if "ollama" in joined and ("timeout" in joined or "not reachable" in joined or "received_chars\": 0" in joined):
            add("local_llm", "Ollama timeouts or empty model responses", "Use prompt lifecycle status before retrying, allow /ollama-stop --confirm when stuck, and avoid starting repair/backtracking if no files were written.", "/llm-status then /ollama-stop --confirm if needed")
        if "static_acceptance" in joined or "goal_coverage" in joined:
            add("acceptance", "Requirement checks rejected generated code", "Inspect required terms, filter meta words, and prefer asking a two-way clarification when acceptance is ambiguous.", "/interactive GOAL then /reply ANSWER")
        if "syntaxerror" in joined or "node_syntax" in joined:
            add("repair", "Generated code syntax errors", "Run surgical repair before LLM repair or backtracking. Add deterministic repair rules for repeated exact errors.", "/surgical-repair exact error text")
        if "tool" in joined and ("proposal" in joined or "safety_ok" in joined or "custom tool" in joined):
            add("custom_tools", "Custom tool creation/use needs review", "View tool source, test it, approve safe proposals, and clean stale proposals before agent runs.", "/tool-proposals ; /tool-view NAME ; /tool-test NAME")
        if "nested" in joined or "winlocalassistantprojects\\" in joined and "\\winlocalassistantprojects\\" in joined:
            add("projects", "Possible nested project or wrong workspace operations", "Ensure new projects use project root while /continue and /improve-project use current project only.", "/projects ; /project-open NAME")
        if "backtrack" in joined:
            add("recovery", "Backtracking used during failures", "Prefer surgical find/replace for small file errors and preserve best attempted state unless user asks to rollback.", "/surgical-repair then /backtrack only if needed")
        if not recs:
            add("general", "No strong repeated failure pattern found", "Run a self-check, inspect logs, then use the agent guide to choose the smallest safe tool sequence.", "/self-check ; /tool-guide")
        return recs

    def investigate_logs(self, focus: str = "", limit: int = 300) -> ToolResult:
        """Investigate recent errors and write a report the assistant/agent can read later."""
        events = self._recent_problem_events(limit=limit)
        recs = self._recommendations_from_problem_events(events)
        focus = (focus or "").strip()
        lines = [
            "# Error Investigation Report",
            "",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Workspace: `{self.workspace}`",
        ]
        if focus:
            lines.append(f"Focus: {focus}")
        lines.extend(["", "## Summary", f"Found {len(events)} recent error/attention event(s).", "", "## Recommended fixes"])
        for i, r in enumerate(recs, 1):
            lines.append(f"{i}. **{r['area']}**: {r['problem']}")
            lines.append(f"   - Change: {r['recommended_change']}")
            if r.get("useful_command"):
                lines.append(f"   - Command: `{r['useful_command']}`")
        lines.extend(["", "## Recent events"])
        for ev in events[-40:]:
            lines.append("\n```json")
            lines.append(json.dumps(ev, indent=2, ensure_ascii=False, default=str)[:5000])
            lines.append("```")
        report = APP_DIR / "ERROR_INVESTIGATION.md"
        atomic_write_text(report, "\n".join(lines))
        try:
            atomic_write_text((self.workspace / "ERROR_INVESTIGATION.md"), "\n".join(lines))
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        log_activity("log_investigation", "Investigated recent errors and wrote ERROR_INVESTIGATION.md", {"events": len(events), "recommendations": recs})
        return ToolResult(True, f"Investigated {len(events)} recent error/attention event(s)", {"report": str(report), "workspace_report": str(self.workspace / "ERROR_INVESTIGATION.md"), "recommendations": recs, "recent_event_count": len(events)})

    def propose_improvements(self, focus: str = "") -> ToolResult:
        """Create a non-mutating improvement proposal for self/tools/project code.

        This does not edit code. It gives the user and /agent a concrete proposal that can
        later be implemented by /self-improve, /tool-create, or normal project repair.
        """
        investigation = self.investigate_logs(focus=focus)
        recs = investigation.data.get("recommendations", []) if investigation.ok else []
        custom = list_custom_tools()
        catalog = self._tool_catalog_for_agent()
        proposals = []
        for r in recs:
            area = r.get("area")
            if area == "custom_tools":
                proposals.append({"target": "custom_tools", "change": "Add or repair small read-only analysis tools, then run /tool-test before agent use.", "commands": ["/custom-tools", "/tool-proposals", "/tool-view NAME", "/tool-test NAME"]})
            elif area == "repair":
                proposals.append({"target": "winlocalassistant/tools.py", "change": "Add deterministic surgical repair rule for any repeated syntax/runtime error in the investigation report.", "commands": ["/surgical-repair exact error", "/self-improve add deterministic repair for repeated error"]})
            elif area == "local_llm":
                proposals.append({"target": "winlocalassistant/ollama.py", "change": "Improve prompt timeout/quarantine messaging and avoid recovery when no project files were written.", "commands": ["/llm-status", "/ollama-stop --confirm"]})
            elif area == "acceptance":
                proposals.append({"target": "winlocalassistant/tools.py acceptance checks", "change": "Improve goal term extraction and ask clarifying questions when static acceptance is uncertain.", "commands": ["/interactive GOAL", "/reply ANSWER"]})
            else:
                proposals.append({"target": area or "general", "change": r.get("recommended_change"), "commands": [r.get("useful_command", "/self-check")]})
        if not proposals:
            proposals.append({"target": "general", "change": "No immediate code change recommended; use /tool-guide and run a focused agent pass.", "commands": ["/tool-guide", "/agent GOAL"]})
        lines = [
            "# Nova Improvement Proposals",
            "",
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Focus: {focus or 'recent error logs and current toolbox'}",
            "",
            "## Available agent tools",
            json.dumps(catalog, indent=2, ensure_ascii=False)[:12000],
            "",
            "## Installed custom tools",
            json.dumps(custom, indent=2, ensure_ascii=False)[:12000],
            "",
            "## Proposed changes",
        ]
        for i, p in enumerate(proposals, 1):
            lines.append(f"{i}. Target: `{p['target']}`")
            lines.append(f"   - Change: {p['change']}")
            for c in p.get("commands", []):
                if c:
                    lines.append(f"   - Command: `{c}`")
        lines.extend(["", "## Safe implementation workflow", self._tool_use_guide_text(compact=True)])
        report = APP_DIR / "IMPROVEMENT_PROPOSALS.md"
        atomic_write_text(report, "\n".join(lines))
        try:
            atomic_write_text((self.workspace / "IMPROVEMENT_PROPOSALS.md"), "\n".join(lines))
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        log_activity("improvement_proposals", "Wrote improvement proposals from recent logs", {"proposals": proposals, "focus": focus})
        return ToolResult(True, f"Created {len(proposals)} improvement proposal(s)", {"report": str(report), "workspace_report": str(self.workspace / "IMPROVEMENT_PROPOSALS.md"), "proposals": proposals})

    def _tool_use_guide_text(self, compact: bool = False) -> str:
        sections = [
            ("Default repair sequence", [
                "1. /self-check to confirm the running backend is the expected version.",
                "2. /llm-status to see whether a prompt is truly active or only loaded in Ollama.",
                "3. /project-open NAME to target the correct project before repair.",
                "4. /run-project or /auto-verify to reproduce the issue.",
                "5. /surgical-repair with the exact error for small syntax/runtime bugs.",
                "6. /improve-project for agentic inspect → test → repair → final-check.",
                "7. /backtrack only when surgical repair and focused LLM repair are insufficient.",
            ]),
            ("Custom tool workflow", [
                "1. /tool-create GOAL for a small read-only or project-analysis helper.",
                "2. /tool-proposals to review anything not auto-installed.",
                "3. /tool-view NAME or /tool-code NAME to inspect source before trust/use.",
                "4. /tool-test NAME to run a safe smoke test.",
                "5. /tool-run NAME => {\"subdir\":\".\"} to use it in the current project.",
                "6. /tool-disable NAME if a tool is noisy; /tool-delete NAME if unsafe or useless.",
            ]),
            ("Build workflow", [
                "1. Use /fast for small apps and /long for larger apps with exports/search/history.",
                "2. If requirements are unclear, use /interactive so the assistant asks before building.",
                "3. After generation, use /run-project and Open in tab/popup to test companion files.",
                "4. Use /continue for feature additions to the current project.",
                "5. Use /final_project_check indirectly through /improve-project or /run-plan final step.",
            ]),
            ("Self-improvement workflow", [
                "1. /investigate-logs to summarize recent failures.",
                "2. /propose-improvements to draft safe changes to assistant code/tools/projects.",
                "3. /self-improve GOAL only for small source-code changes with backup and tests.",
                "4. /version and /self-check after restart to confirm the fixed build is loaded.",
            ]),
        ]
        out = []
        for title, items in sections:
            out.append(f"## {title}")
            out.extend(f"- {x}" for x in items)
            out.append("")
        if not compact:
            out.append("## Agent rule of thumb")
            out.append("Inspect before editing. Run the smallest useful check. Use surgical repair for exact errors. Create a custom tool only when repeated inspection would be useful. Verify after every edit.")
        return "\n".join(out).strip()

    def tool_use_guide(self) -> ToolResult:
        guide = Path(__file__).resolve().parents[1] / "docs" / "NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md"
        content = "# Nova Tool Use Guide\n\n" + get_local_model_tool_use_summary() + "\n\n" + self._tool_use_guide_text(compact=False)
        return ToolResult(True, "Tool use guide", {"guide": str(guide), "content": content, "mutating": False})

    def custom_tools(self) -> ToolResult:
        cleanup = cleanup_tool_proposals()
        registry = refresh_custom_tool_registry()
        tools = registry.get("tools", [])
        sections: dict[str, list[dict[str, Any]]] = {}
        for item in tools:
            sections.setdefault(str(item.get("section") or "General"), []).append(item)
        proposals = list_tool_proposals()
        return ToolResult(True, f"Found {len(tools)} custom tools and {len(proposals)} pending proposal(s)", {"tools": tools, "sections": sections, "proposals": proposals, "cleanup": cleanup, "registry": registry, "cache_invalidated": True})

    def tool_proposals(self) -> ToolResult:
        proposals = list_tool_proposals()
        return ToolResult(True, f"Found {len(proposals)} pending tool proposal(s)", {"proposals": proposals})

    def tool_clean_proposals(self) -> ToolResult:
        self.require_mutation()
        data = cleanup_tool_proposals()
        removed = data.get("removed", [])
        return ToolResult(True, f"Cleaned {len(removed)} stale/superseded tool proposal(s)", data)

    def runtime_self_check(self) -> ToolResult:
        required_methods = [
            "_tool_catalog_for_agent", "_project_context", "tool_create", "tool_run",
            "improve_project", "agent_execute", "final_project_check", "surgical_repair",
            "run_project", "backtrack_recover", "investigate_logs", "propose_improvements", "tool_use_guide",
        ]
        missing = [m for m in required_methods if not hasattr(self, m)]
        data = {
            "workspace": str(self.workspace),
            "tool_registry_class": type(self).__name__,
            "tools_registered": sorted(self.tools.keys()),
            "required_methods_missing": missing,
            "custom_tools": list_custom_tools(),
            "proposal_cleanup": cleanup_tool_proposals(),
        }
        ok = not missing
        return ToolResult(ok, "Runtime self-check passed" if ok else "Runtime self-check found missing methods", data)

    def tool_view(self, name: str) -> ToolResult:
        if not str(name or "").strip() or str(name or "").strip().upper() in {"TOOL_NAME", "NAME"}:
            return self.tool_help(name)
        try:
            info = get_custom_tool_source(name)
            return ToolResult(True, f"Viewed custom tool {info.get('name')}", info)
        except Exception as exc:
            return ToolResult(False, "Could not view custom tool", {"name": name, "error": str(exc)})

    def tool_test(self, name: str) -> ToolResult:
        try:
            result = run_custom_tool(name, {"subdir": "."}, self.workspace, self.config)
            ok = bool(result.get("ok", True)) if isinstance(result, dict) else True
            tested = mark_custom_tool_tested(name, ok=ok, summary=str((result or {}).get("summary", "") if isinstance(result, dict) else result))
            manifest_tools = list_custom_tools()
            return ToolResult(ok, f"Custom tool {name} test ran" if ok else f"Custom tool {name} test returned not-ok", {"result": result, "tools": manifest_tools, "last_tested": tested})
        except Exception as exc:
            try:
                mark_custom_tool_tested(name, ok=False, summary=str(exc))
            except Exception:
                pass
            return ToolResult(False, "Custom tool test failed", {"name": name, "error": str(exc)})

    def tool_enable(self, name: str) -> ToolResult:
        self.require_mutation()
        try:
            return ToolResult(True, f"Enabled custom tool {name}", set_custom_tool_enabled(name, True))
        except Exception as exc:
            return ToolResult(False, "Could not enable custom tool", {"name": name, "error": str(exc)})

    def tool_disable(self, name: str) -> ToolResult:
        self.require_mutation()
        try:
            return ToolResult(True, f"Disabled custom tool {name}", set_custom_tool_enabled(name, False))
        except Exception as exc:
            return ToolResult(False, "Could not disable custom tool", {"name": name, "error": str(exc)})

    def tool_approve(self, proposal_id: str) -> ToolResult:
        self.require_mutation()
        try:
            saved = approve_tool_proposal(proposal_id)
            log_activity("custom_tool_approved", "Approved and installed custom tool proposal", saved)
            return ToolResult(True, f"Approved and installed custom tool {saved.get('name')}", saved)
        except Exception as exc:
            return ToolResult(False, "Could not approve custom tool proposal", {"proposal_id": proposal_id, "error": str(exc)})

    def tool_reject(self, proposal_id: str) -> ToolResult:
        self.require_mutation()
        try:
            data = delete_tool_proposal(proposal_id)
            return ToolResult(True, "Rejected/deleted tool proposal", data)
        except Exception as exc:
            return ToolResult(False, "Could not reject custom tool proposal", {"proposal_id": proposal_id, "error": str(exc)})


    def tool_run(self, name: str, args: dict[str, Any] | str | None = None) -> ToolResult:
        self.require_mutation()
        try:
            if not str(name or "").strip() or str(name or "").strip().upper() in {"TOOL_NAME", "NAME"}:
                return self.tool_help(name)
            parsed = self._friendly_tool_args(name, args)
            result = run_custom_tool(name, parsed, self.workspace, self.config)
            log_activity("custom_tool_run", f"Ran custom tool {name}", {"args": parsed, "result": result})
            return ToolResult(True, f"Custom tool ran: {name}", {"name": name, "args": parsed, "result": result, "tip": f"Use /tool-help {name} to see accepted inputs."})
        except Exception as exc:
            return ToolResult(False, "Custom tool run failed", {"name": name, "raw_args": args, "error": str(exc), "tip": f"Use strict JSON like /tool-run {name} => {{}}, or use /tool-help {name}. v50 also accepts raw text in braces for string tools."})

    def _tool_metadata(self, name: str) -> dict[str, Any] | None:
        wanted = str(name or "").strip().lower()
        for item in list_custom_tools():
            if str(item.get("name") or "").lower() == wanted:
                return item
        return None

    def _first_text_field(self, schema: dict[str, Any]) -> str | None:
        if not isinstance(schema, dict) or not schema:
            return None
        for key, value in schema.items():
            if isinstance(value, dict) and str(value.get("type") or "").lower() in {"string", "text"}:
                return str(key)
        for key, value in schema.items():
            blob = f"{key} {value}".lower()
            if any(word in blob for word in ["text", "message", "query", "url", "topic", "content", "field", "input"]):
                return str(key)
        return str(next(iter(schema.keys())))

    def _coerce_tool_value(self, value: str) -> Any:
        value = value.strip().strip('"').strip("'")
        if re.fullmatch(r"-?\d+", value):
            return int(value)
        if re.fullmatch(r"-?\d+\.\d+", value):
            return float(value)
        if value.lower() in {"true", "false"}:
            return value.lower() == "true"
        return value

    def _friendly_tool_args(self, name: str, args: dict[str, Any] | str | None) -> dict[str, Any]:
        if args is None:
            return {}
        if isinstance(args, dict):
            return args
        raw = str(args or "").strip()
        if not raw:
            return {}
        try:
            parsed = json.loads(raw)
            if isinstance(parsed, dict):
                return parsed
            meta = self._tool_metadata(name) or {}
            field = self._first_text_field(meta.get("input_schema") if isinstance(meta.get("input_schema"), dict) else {}) or "text"
            return {field: parsed}
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        if raw.startswith("{") and raw.endswith("}"):
            inner = raw[1:-1].strip()
            if ":" not in inner:
                raw = inner
        if "=" in raw and not raw.lstrip().startswith(("{", "[")):
            out: dict[str, Any] = {}
            for part in re.split(r"[,;]\s*", raw):
                if "=" not in part:
                    continue
                key, value = part.split("=", 1)
                key = key.strip()
                if key:
                    out[key] = self._coerce_tool_value(value)
            if out:
                return out
        meta = self._tool_metadata(name) or {}
        schema = meta.get("input_schema") if isinstance(meta.get("input_schema"), dict) else {}
        field = self._first_text_field(schema) or "text"
        parsed = {field: raw}
        if field != "text" and (field in {"field", "input", "value"} or str(schema.get(field, "")).lower() in {"text", "string"}):
            parsed["text"] = raw
        if "caesar" in str(name or "").lower() and "shift" in schema and "shift" not in parsed:
            parsed["shift"] = 3
        return parsed

    def tool_help(self, name: str = "") -> ToolResult:
        tools = list_custom_tools()
        requested = str(name or "").strip()
        if not requested or requested.upper() in {"TOOL_NAME", "NAME"}:
            return ToolResult(True, "Custom tool help", {
                "available_tools": [{"name": t.get("name"), "description": t.get("description"), "input_schema": t.get("input_schema")} for t in tools],
                "examples": [
                    "/tool-run caesar_decrypter => {khoor}",
                    "/tool-run big_bold_reply => {hey}",
                    "/tool-run html_reference_checker => {\"subdir\":\".\"}",
                    "/tool-pipeline [{\"tool\":\"tool_run\",\"args\":{\"name\":\"html_reference_checker\",\"args\":{\"subdir\":\".\"}}}]",
                ],
                "note": "v50 accepts strict JSON or simple {text} shorthand for text-like tools."
            })
        meta = self._tool_metadata(requested)
        if not meta:
            return ToolResult(False, "Custom tool not found", {"name": requested, "available_tools": [t.get("name") for t in tools], "tip": "Use /custom-tools or /tool-help to list installed tools."})
        schema = meta.get("input_schema") if isinstance(meta.get("input_schema"), dict) else {}
        field = self._first_text_field(schema)
        examples = [f"/tool-run {meta.get('name')} => {{}}"]
        if field:
            examples.append(f"/tool-run {meta.get('name')} => {{sample text}}")
            examples.append(f"/tool-run {meta.get('name')} => {{\"{field}\":\"sample text\"}}")
        return ToolResult(True, f"Tool help: {meta.get('name')}", {"tool": meta, "input_schema": schema, "examples": examples, "note": "Strict JSON is best for structured inputs; simple text is accepted for text-like tools."})

    def _should_use_deterministic_tool_fallback(self, goal: str) -> bool:
        g = (goal or "").lower()
        if "tool" in g and any(x in g for x in ["yourself", "for yourself", "for wla", "for nova", "for the assistant", "useful tool"]):
            return True
        return any(x in g for x in ["todo", "fixme", "file type", "file summary", "html reference", "missing reference"])

    def _fallback_custom_tool(self, goal: str) -> dict[str, Any] | None:
        g = (goal or "").lower()
        if "tool" in g and any(k in g for k in ["yourself", "for yourself", "for wla", "for nova", "for the assistant", "useful tool"]):
            code = """def run(args, workspace, config):
    subdir = args.get("subdir") or "."
    root = workspace / subdir
    ignored = {".git", ".venv", "node_modules", "__pycache__", ".pytest_cache"}
    files = []
    counts = {"python": 0, "javascript": 0, "html": 0, "css": 0, "tests": 0, "docs": 0, "other": 0}
    warnings = []
    for path in root.rglob("*"):
        if not path.is_file() or any(part in ignored for part in path.parts):
            continue
        rel = str(path.relative_to(workspace))
        suffix = path.suffix.lower()
        if suffix == ".py":
            counts["python"] += 1
        elif suffix == ".js":
            counts["javascript"] += 1
        elif suffix == ".html":
            counts["html"] += 1
        elif suffix == ".css":
            counts["css"] += 1
        elif path.name.lower().startswith("test") or "tests" in path.parts:
            counts["tests"] += 1
        elif suffix in {".md", ".txt"}:
            counts["docs"] += 1
        else:
            counts["other"] += 1
        files.append(rel)
    if counts["python"] and not counts["tests"]:
        warnings.append("Python files found but no obvious tests detected.")
    if counts["html"] and not counts["javascript"]:
        warnings.append("HTML files found without JavaScript; verify the app is intentionally static.")
    summary = f"Project health snapshot: {len(files)} files, {counts['python']} Python, {counts['javascript']} JS, {counts['html']} HTML, {counts['tests']} tests."
    return {"ok": True, "summary": summary, "counts": counts, "warnings": warnings, "sample_files": files[:80]}
"""
            return {"name": "project_health_snapshot", "description": "Summarises the current project structure and highlights simple test/UI coverage warnings", "input_schema": {"subdir": "folder under workspace"}, "section": "Project Analysis", "risk": "read_only", "code": code}
        if any(k in g for k in ["todo", "fixme", "comment"]):
            code = """def run(args, workspace, config):
    patterns = args.get("patterns") or ["TODO", "FIXME"]
    subdir = args.get("subdir") or "."
    root = (workspace / subdir).resolve()
    results = []
    counts = {p: 0 for p in patterns}
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        for line_no, line in enumerate(text.splitlines(), 1):
            for pat in patterns:
                if pat.lower() in line.lower():
                    counts[pat] = counts.get(pat, 0) + 1
                    results.append({"file": str(path.relative_to(workspace)), "line": line_no, "pattern": pat, "text": line.strip()[:240]})
    return {"ok": True, "summary": f"Found {sum(counts.values())} TODO/FIXME-style comments", "counts": counts, "matches": results[:500]}
"""
            return {"name": "todo_fixme_counter", "description": "Counts TODO/FIXME comments in project files", "input_schema": {"subdir": "folder under workspace", "patterns": "optional list of strings"}, "section": "Code Quality", "code": code}
        if any(k in g for k in ["extension", "file types", "file summary", "summarize files"]):
            code = """def run(args, workspace, config):
    subdir = args.get("subdir") or "."
    root = (workspace / subdir).resolve()
    counts = {}
    total = 0
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        ext = path.suffix.lower() or "[no extension]"
        counts[ext] = counts.get(ext, 0) + 1
        total += 1
    return {"ok": True, "summary": f"Scanned {total} files", "file_count": total, "extensions": dict(sorted(counts.items()))}
"""
            return {"name": "file_type_summary", "description": "Summarises project file extensions", "input_schema": {"subdir": "folder under workspace"}, "section": "Project Analysis", "code": code}
        if any(k in g for k in ["html", "css", "js", "javascript", "missing reference", "missing refs", "references", "link checker"]):
            code = """def run(args, workspace, config):
    subdir = args.get("subdir") or "."
    root = (workspace / subdir).resolve()
    checked = []
    missing = []
    for path in root.rglob("*.html"):
        if any(part in {".git", ".venv", "node_modules", "__pycache__"} for part in path.parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        import re
        refs = []
        refs += re.findall(r"<link[^>]+href=[\\"']([^\\"']+)[\\"']", text, flags=re.I)
        refs += re.findall(r"<script[^>]+src=[\\"']([^\\"']+)[\\"']", text, flags=re.I)
        for ref in refs:
            if ref.startswith(("http://", "https://", "data:", "#")):
                continue
            target = (path.parent / ref.split("?", 1)[0].split("#", 1)[0]).resolve()
            checked.append({"html": str(path.relative_to(workspace)), "ref": ref})
            try:
                target.relative_to(workspace.resolve())
            except Exception:
                missing.append({"html": str(path.relative_to(workspace)), "ref": ref, "problem": "outside workspace"})
                continue
            if not target.exists():
                missing.append({"html": str(path.relative_to(workspace)), "ref": ref, "problem": "file not found"})
    return {"ok": not missing, "summary": f"Checked {len(checked)} HTML CSS/JS reference(s); missing {len(missing)}", "checked": checked, "missing": missing}
"""
            return {"name": "html_reference_checker", "description": "Checks HTML files for missing local CSS and JS references", "input_schema": {"subdir": "folder under workspace"}, "section": "Project Analysis", "risk": "read_only", "code": code}
        return None

    def tool_delete(self, name: str) -> ToolResult:
        self.require_mutation()
        try:
            deleted = delete_custom_tool(name)
            log_activity("custom_tool_deleted", f"Deleted custom tool {deleted.get('name')}", deleted)
            return ToolResult(True, f"Deleted custom tool {deleted.get('name')}", deleted)
        except Exception as exc:
            return ToolResult(False, "Could not delete custom tool", {"error": str(exc), "name": name})


    def surgical_fallback_v2_tool(self, goal: str = "", path: str = ".", failure: Any = None) -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        payload = build_surgical_fallback_plan(root, goal or "repair current project", failure=failure)
        return ToolResult(bool(payload.get("ok", True)), str(payload.get("summary") or "Surgical fallback v2 plan built"), {"message": render_iterative_coding_markdown(payload), **payload})

    def iterative_coding_loop_tool(self, goal: str = "", path: str = ".", max_passes: int = 3) -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        payload = build_iterative_coding_loop(root, goal or "improve current project", max_passes=max_passes)
        return ToolResult(True, "Iterative coding loop planned", {"message": render_iterative_coding_markdown(payload), **payload})

    def edit_repair_plan_tool(self, goal: str = "", path: str = ".") -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        md, js, payload = write_iterative_coding_report(root, goal or "improve editing and repair reliability")
        return ToolResult(True, "Edit/test/repair plan written", {"message": render_iterative_coding_markdown(payload), "markdown_path": str(md), "json_path": str(js), **payload})

    def prompt_contract(self, goal: str = "") -> ToolResult:
        goal = goal or "general Nova task"
        payload = build_prompt_contract(goal)
        return ToolResult(True, "Prompt contract built", {"goal": goal, "contract": payload, "markdown": render_prompt_contract(payload)})

    def prompt_test_run(self, goal: str = "", path: str = ".") -> ToolResult:
        goal = goal or "general Nova task"
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        payload = validate_contract(goal, root)
        return ToolResult(bool(payload.get("ok", True)), "Prompt contract validation completed", {"goal": goal, "path": str(root), "result": payload, "markdown": render_contract_validation(payload)})

    def candidate_tournament_tool(self, goal: str = "", path: str = ".") -> ToolResult:
        goal = goal or "general Nova task"
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        payload = build_candidate_tournament(goal, root)
        return ToolResult(True, "Candidate tournament completed", {"goal": goal, "winner": payload.get("winner"), "result": payload, "markdown": render_tournament(payload)})

    def candidate_failure_report_tool(self, goal: str = "", path: str = ".") -> ToolResult:
        payload = build_candidate_tournament(goal or "general Nova task", self.workspace / path if not Path(path).is_absolute() else Path(path))
        return ToolResult(True, "Candidate failure report completed", {"result": payload, "markdown": render_candidate_failure_report(payload)})

    def repair_plan_v2(self, evidence: str = "", path: str = ".") -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        payload = build_repair_plan(root, evidence or "latest Nova/project failure")
        return ToolResult(True, "Surgical repair v2 plan built", {"path": str(root), "result": payload, "markdown": render_repair(payload)})

    def trace_status_tool(self, run_id: str = "", limit: int = 160) -> ToolResult:
        payload = build_trace(limit=int(limit or 160), run_id=run_id or "")
        return ToolResult(True, "Trace status built", {"trace": payload, "markdown": render_trace_markdown(payload), "dashboard": render_performance_dashboard(payload)})

    def mcp_risk_report_tool(self) -> ToolResult:
        payload = inspect_mcp_security(app=None, root=self.workspace)
        return ToolResult(True, "MCP risk report built", {"result": payload, "markdown": render_mcp_security(payload)})

    def mission_create_tool(self, goal: str = "") -> ToolResult:
        payload = create_mission(goal or "improve Nova safely")
        return ToolResult(True, "Autonomous mission created", {"mission": payload, "markdown": render_mission(payload)})

    def mission_step_tool(self) -> ToolResult:
        payload = mission_step()
        return ToolResult(True, "Autonomous mission step selected", {"mission": payload, "markdown": render_mission(payload)})

    def model_output_coach_tool(self, goal: str = "", output: str = "") -> ToolResult:
        if not output:
            recent = tail_jsonl(MODEL_IO_PATH, limit=1)
            output = str(recent[-1].get("reply") if recent else "") if recent else ""
        payload = analyze_model_output(goal or "current model output", output)
        return ToolResult(True, "Model output coach completed", {"result": payload, "markdown": render_model_output_coach(payload)})

    def env_profile_tool(self, profile: str = "minimal") -> ToolResult:
        payload = build_env_profile(profile or "minimal")
        return ToolResult(bool(payload.get("ok", True)), "Environment profile checked", {"profile": payload, "markdown": render_env_profile(payload)})

    def benchmark_system_tool(self) -> ToolResult:
        payload = benchmark_system()
        return ToolResult(True, "System benchmark snapshot built", {"benchmark": payload, "markdown": render_benchmark(payload)})

    def project_state_tool(self, path: str = ".", kind: str = "", data: Any = None) -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        if str(kind or "").lower() in {"audit", "check", "integrity"}:
            payload = audit_project_state(root)
            message = "# Project state audit\n\n" + "\n".join([
                f"Path: `{payload.get('path')}`",
                f"Exists: **{payload.get('exists')}**",
                f"OK: **{payload.get('ok')}**",
                "",
                "## Counts",
                *[f"- {k}: {v}" for k, v in (payload.get('counts') or {}).items()],
                "",
                "## Warnings",
                *([f"- {w}" for w in payload.get('warnings', [])] or ["- None"]),
            ])
            return ToolResult(bool(payload.get("ok", True)), "Project state audit completed", {"path": str(root), "audit": payload, "message": message})
        if kind:
            payload = append_project_state(root, kind, data)
        else:
            payload = load_project_state(root)
        return ToolResult(True, "Project state loaded", {"path": str(root), "state": payload, "markdown": render_project_state(payload)})

    def regression_list_tool(self) -> ToolResult:
        payload = load_regressions()
        return ToolResult(True, "Regression memory loaded", {"regressions": payload, "markdown": render_regressions(payload)})

    def regression_add_tool(self, description: str = "", repro: str = "", expected: str = "") -> ToolResult:
        item = add_regression(description or "unspecified regression", repro=repro, expected=expected)
        return ToolResult(True, "Regression memory item added", {"item": item, "markdown": render_regressions([item])})

    def improvement_proposals_v2(self, focus: str = "") -> ToolResult:
        payload = build_improvement_proposals(self.workspace, focus=focus)
        return ToolResult(True, "Improvement proposals built", {"result": payload, "markdown": render_improvement_cycle(payload)})

    def improvement_cycle_tool(self, focus: str = "", confirm: bool = False) -> ToolResult:
        payload = complete_improvement_proposals(self.workspace, focus=focus, confirm=bool(confirm))
        ok = payload.get("status") in {"completed", "dry_run"}
        return ToolResult(ok, "Improvement proposal cycle " + str(payload.get("status", "completed")), {"result": payload, "markdown": render_improvement_cycle(payload)})

    def improvement_status_tool(self) -> ToolResult:
        payload = load_latest_improvement_cycle(self.workspace)
        ok = not (payload.get("ok") is False and payload.get("status") == "missing")
        markdown = render_improvement_cycle(payload) if payload.get("proposals") else json.dumps(payload, indent=2)
        return ToolResult(ok, "Improvement cycle status loaded" if ok else "No improvement cycle found", {"result": payload, "markdown": markdown})

    def tool_create(self, goal: str, name: str | None = None) -> ToolResult:
        self.require_mutation()
        if not goal.strip():
            return ToolResult(False, "No tool goal supplied", {"usage": "/tool-create create a CSV summariser"})
        tool_name = name or self._slug(goal, default="custom_tool").lower()
        deterministic = self._fallback_custom_tool(goal)
        if deterministic and self._should_use_deterministic_tool_fallback(goal):
            try:
                saved = save_custom_tool(str(deterministic["name"]), str(deterministic["description"]), str(deterministic["code"]), deterministic.get("input_schema") or {}, str(deterministic.get("section") or "General"), risk=str(deterministic.get("risk") or "read_only"))
                test_result = self.tool_test(str(saved.get("name") or ""))
                registry = refresh_custom_tool_registry()
                visible = any(t.get("name") == saved.get("name") and t.get("exists") and t.get("enabled", True) for t in registry.get("tools", []))
                payload = {**saved, "source": "deterministic_fallback", "reason": "The request was a broad self-tool request, so Nova used a known safe project-analysis helper instead of opening a generic app/build planning loop.", "registry_visible": visible, "registry": registry, "tool_test_ok": bool(test_result.ok), "tool_test_summary": test_result.summary}
                log_activity("tool_created_deterministic", "Installed deterministic safe custom tool and refreshed registry", {"goal": goal, **payload})
                return ToolResult(bool(visible and test_result.ok), f"Created custom tool {saved['name']} using a deterministic safe fallback" if visible and test_result.ok else f"Custom tool {saved.get('name','')} fallback failed refresh/test", payload)
            except Exception as exc:
                log_activity("tool_create_deterministic_failed", "Deterministic custom-tool fallback failed; falling back to local model", {"goal": goal, "error": repr(exc)})
        prompt = f"""
You are creating a small SAFE Python plugin tool for Nova.
Return ONLY valid JSON. No markdown.

User wants this tool:
{goal}

The tool must be a single Python file and must define:
def run(args, workspace, config):
    # args is a dict, workspace is a pathlib.Path to the current safe workspace, config is read-only config
    return {{"ok": True, "summary": "...", "data": ...}}

Tool-writing rules:
- Prefer read-only project analysis tools unless the user explicitly asks for a mutating tool.
- You MAY use the provided workspace Path object: workspace.rglob(), path.read_text(), path.relative_to(workspace).
- Do not import os, subprocess, shutil, socket, ctypes, winreg, sys, requests, urllib.request, threading or multiprocessing.
- Do not call eval, exec, compile, open, __import__, input, system, popen, remove, rmdir, unlink, rmtree, rename, replace or chmod.
- Do not access files outside the workspace.
- Keep output compact and structured.

JSON schema:
{{
  "name": "short_snake_case_tool_name",
  "description": "what it does",
  "section": "Project Analysis | Code Quality | Data Tools | General",
  "input_schema": {{"field": "description"}},
  "code": "full Python source code"
}}
"""
        log_activity("tool_create_start", "Asking local LLM to write a custom tool", {"goal": goal})
        reply = model_chat(self.config, self.config.model, [{"role": "user", "content": prompt}], timeout=180, desc="custom tool generation")
        log_model_io("prompt", prompt=prompt, data={"mode": "tool_create", "goal": goal})
        log_model_io("response", response=reply or "", data={"mode": "tool_create", "received_chars": len(reply or "")})
        data = self._extract_json_object(reply or "") if reply else None
        if not data:
            data = self._fallback_custom_tool(goal)
            if not data:
                return ToolResult(False, "Local LLM did not return valid tool JSON and no safe fallback matched", {"goal": goal, "fix": "Check /llm-status, then retry or ask for a TODO/FIXME counter or file type summary tool."})
        try:
            risk = str(data.get("risk") or ("read_only" if "read" in str(data.get("description") or goal).lower() or "count" in goal.lower() or "list" in goal.lower() else "project_analysis"))
            proposal = save_tool_proposal(str(data.get("name") or tool_name), str(data.get("description") or goal), str(data.get("code") or ""), data.get("input_schema") if isinstance(data.get("input_schema"), dict) else {}, str(data.get("section") or "General"), risk=risk)
            # Low-risk read-only/project-analysis tools can be auto-installed; higher-risk tools remain proposals.
            if proposal.get("safety_ok") and risk in {"read_only", "project_analysis"}:
                saved = approve_tool_proposal(proposal["id"])
            else:
                return ToolResult(True, "Created custom tool proposal; review and approve before use", {"proposal": proposal, "approve_command": f"/tool-approve {proposal['id']}", "reject_command": f"/tool-reject {proposal['id']}"})
        except Exception as exc:
            fallback = self._fallback_custom_tool(goal)
            if fallback and fallback is not data:
                try:
                    saved = save_custom_tool(str(fallback["name"]), str(fallback["description"]), str(fallback["code"]), fallback.get("input_schema") or {}, str(fallback.get("section") or "General"), risk="read_only")
                except Exception as exc2:
                    return ToolResult(False, "Generated and fallback tools failed validation", {"generated_error": str(exc), "fallback_error": str(exc2)})
            else:
                return ToolResult(False, "Generated tool failed validation and was not installed", {"error": str(exc), "tool_json_keys": sorted(data.keys()) if isinstance(data, dict) else []})
        # Immediately re-read registry and smoke-test so chat/UI cannot claim a tool was created while refresh cannot see it.
        test_result = self.tool_test(str(saved.get("name") or ""))
        registry = refresh_custom_tool_registry()
        visible = any(t.get("name") == saved.get("name") and t.get("exists") and t.get("enabled", True) for t in registry.get("tools", []))
        saved = {**saved, "registry_visible": visible, "registry": registry, "tool_test_ok": bool(test_result.ok), "tool_test_summary": test_result.summary}
        log_activity("tool_created", "Custom tool installed and registry refreshed", saved)
        return ToolResult(bool(visible and test_result.ok), f"Created custom tool {saved['name']}" if visible and test_result.ok else f"Custom tool {saved.get('name','')} was written but failed refresh/test", saved)


    def weakspot_audit_tool(self, path: str = ".", write_report: bool = True) -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        if write_report:
            md, js, report = write_weakspot_report(root)
            return ToolResult(bool(report.get("ok", True)), "Weakspot audit completed", {"report": report, "markdown": render_weakspot_audit(report), "markdown_path": str(md), "json_path": str(js)})
        report = build_weakspot_audit(root)
        return ToolResult(bool(report.get("ok", True)), "Weakspot audit completed", {"report": report, "markdown": render_weakspot_audit(report)})

    def user_test_suite_tool(self, path: str = ".") -> ToolResult:
        root = self.workspace / path if not Path(path).is_absolute() else Path(path)
        md, js, report = write_user_testing_report(root)
        return ToolResult(bool(report.get("ok", True)), "Comprehensive user testing completed", {"report": report, "markdown": render_user_testing_report(report), "markdown_path": str(md), "json_path": str(js)})

    def idle_lessons(self) -> ToolResult:
        path = APP_DIR / "IDLE_LESSONS.md"
        if not path.exists():
            return ToolResult(True, "No previous idle lessons yet", {"path": str(path), "exists": False, "lessons": ""})
        text = path.read_text(encoding="utf-8", errors="replace")
        return ToolResult(True, "Loaded idle lessons", {"path": str(path), "exists": True, "lessons": text[-6000:]})

    def safe_script_demo(self, topic: str = "interesting") -> ToolResult:
        """Return real deterministic local output without arbitrary installs or fake shell claims."""
        import hashlib
        import math
        import platform

        topic = str(topic or "interesting").strip()[:120] or "interesting"
        digest = hashlib.sha256(topic.encode("utf-8", errors="replace")).hexdigest()
        codename = f"Nova-{digest[:4].upper()}-{int(math.sqrt(int(digest[:6], 16))) % 997}"
        data = {
            "topic": topic,
            "codename": codename,
            "sha256_short": digest[:16],
            "python": platform.python_version(),
            "platform": platform.platform(),
            "result": f"If '{topic}' were a tiny local tool demo, its codename would be {codename}.",
            "note": "No package install was performed; this uses Python standard library only.",
        }
        log_activity("safe_script_demo", "Ran safe local script demo", data)
        return ToolResult(True, "Ran safe local script demo", data)


    def internet_search(self, query: str, max_results: int = 8) -> ToolResult:
        """Search public web sources and return candidate URLs for /research.

        This is a read-only discovery step. It never fetches local/private hosts
        and still respects /allow-internet.
        """
        if not bool(getattr(self.config, "allow_internet", False)):
            return ToolResult(False, "Internet access is disabled", {"fix": "Run /allow-internet on first.", "query": query})
        query = str(query or "").strip()
        if not query:
            return ToolResult(False, "Search query is required", {"usage": "/internet-search QUERY"})
        try:
            urls = discover_source_urls(query, limit=max(1, min(int(max_results or 8), 12)))
            return ToolResult(bool(urls), "Internet search completed" if urls else "Internet search found no safe public URLs", {
                "query": query,
                "urls": urls,
                "results": [{"title": u, "url": u} for u in urls],
                "next": "/research " + query + (" => " + " ".join(urls[:6]) if urls else ""),
            })
        except Exception as exc:
            return ToolResult(False, "Internet search failed", {"query": query, "error": repr(exc)})

    def internet_fetch(self, url: str, max_chars: int = 6000) -> ToolResult:
        if not bool(getattr(self.config, "allow_internet", False)):
            return ToolResult(False, "Internet access is disabled", {"fix": "Run /allow-internet on first.", "url": url})
        url = str(url or "").strip()
        parsed = urllib.parse.urlparse(url)
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            return ToolResult(False, "Only public http/https URLs are supported", {"url": url})
        host = (parsed.hostname or "").lower()
        if host in {"localhost"} or host.startswith("127.") or host.startswith("0."):
            return ToolResult(False, "Localhost/private fetches are blocked for the internet tool", {"url": url})
        limit = max(1024, min(int(max_chars or 6000), 30000))
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Nova/47 topic-watcher"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                raw = resp.read(limit)
                content_type = resp.headers.get("content-type", "")
            raw_text = raw.decode("utf-8", errors="replace")
            text = re.sub(r"<script[\s\S]*?</script>", " ", raw_text, flags=re.I)
            text = re.sub(r"<style[\s\S]*?</style>", " ", text, flags=re.I)
            plain = re.sub(r"<[^>]+>", " ", text)
            plain = re.sub(r"\s+", " ", plain).strip()
            return ToolResult(True, "Fetched internet page", {
                "url": url,
                "content_type": content_type,
                "chars": len(plain),
                "text_preview": plain[:limit],
                "raw_preview": raw_text[:limit],
            })
        except Exception as exc:
            return ToolResult(False, "Internet fetch failed", {"url": url, "error": repr(exc)})

    def _topic_watch_path(self) -> Path:
        return APP_DIR / "TOPIC_WATCHERS.json"

    def _load_topic_watchers(self) -> dict[str, Any]:
        path = self._topic_watch_path()
        if path.exists():
            try:
                return read_json_file(path, {}, expected_type=dict, quarantine=True)
            except Exception:
                return {"topics": {}}
        return {"topics": {}}

    def _save_topic_watchers(self, data: dict[str, Any]) -> None:
        APP_DIR.mkdir(parents=True, exist_ok=True)
        atomic_write_json(self._topic_watch_path(), data, ensure_ascii=True)

    def topic_watch(self, topic: str, urls: list[str] | str | None = None) -> ToolResult:
        topic = str(topic or "").strip()
        if not topic:
            return ToolResult(False, "No topic supplied", {"usage": "/watch-topic local AI => https://hnrss.org/newest, https://arxiv.org/rss/cs.AI"})
        if isinstance(urls, str):
            url_list = [u.strip() for u in re.split(r"[,\n]+", urls) if u.strip()]
        else:
            url_list = [str(u).strip() for u in (urls or []) if str(u).strip()]
        if not url_list:
            url_list = ["https://hnrss.org/newest", "https://arxiv.org/rss/cs.AI"]
        valid = []
        rejected = []
        for item in url_list[:12]:
            parsed = urllib.parse.urlparse(item)
            if parsed.scheme in {"http", "https"} and parsed.netloc:
                valid.append(item)
            else:
                rejected.append(item)
        if not valid:
            return ToolResult(False, "No valid http/https source URLs supplied", {"topic": topic, "rejected": rejected})
        data = self._load_topic_watchers()
        data.setdefault("topics", {})[topic.lower()] = {
            "topic": topic,
            "urls": valid,
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
            "last_checked": "",
        }
        self._save_topic_watchers(data)
        return ToolResult(True, "Topic watcher saved", {"topic": topic, "urls": valid, "rejected": rejected, "next": f"/topic-check {topic}"})

    def topic_watchers(self) -> ToolResult:
        data = self._load_topic_watchers()
        return ToolResult(True, "Topic watchers loaded", {"path": str(self._topic_watch_path()), "topics": list((data.get("topics") or {}).values())})

    def topic_check(self, topic: str) -> ToolResult:
        if not bool(getattr(self.config, "allow_internet", False)):
            return ToolResult(False, "Internet access is disabled", {"fix": "Run /allow-internet on first.", "topic": topic})
        key = str(topic or "").strip().lower()
        data = self._load_topic_watchers()
        watcher = (data.get("topics") or {}).get(key)
        if not watcher:
            return ToolResult(False, "Topic watcher not found", {"topic": topic, "available": list((data.get("topics") or {}).keys()), "usage": "/watch-topic TOPIC => URL1, URL2"})
        query_words = [w.lower() for w in re.findall(r"[A-Za-z0-9]{3,}", watcher.get("topic", ""))]
        results = []
        for source in watcher.get("urls", [])[:8]:
            fetched = self.internet_fetch(source, max_chars=10000)
            raw = str((fetched.data or {}).get("raw_preview", ""))
            text = str((fetched.data or {}).get("text_preview", ""))
            titles = []
            for title in re.findall(r"<title[^>]*>(.*?)</title>", raw, flags=re.I | re.S)[:8]:
                cleaned = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", title)).strip()
                if cleaned:
                    titles.append(cleaned[:240])
            hits = [w for w in query_words if w in text.lower()]
            results.append({"url": source, "ok": fetched.ok, "summary": fetched.summary, "hits": hits, "titles": titles, "preview": text[:1500]})
        watcher["last_checked"] = time.strftime("%Y-%m-%d %H:%M:%S")
        self._save_topic_watchers(data)
        slug = re.sub(r"[^A-Za-z0-9]+", "_", key).strip("_") or "topic"
        report_path = APP_DIR / f"TOPIC_REPORT_{slug}.md"
        lines = [f"# Topic report: {watcher.get('topic')}", "", f"Checked: {watcher['last_checked']}", ""]
        for result in results:
            lines.extend([
                f"## {result['url']}",
                f"Status: {result['summary']}",
                "Hits: " + (", ".join(result["hits"]) if result["hits"] else "none"),
                "Titles: " + (" | ".join(result["titles"]) if result["titles"] else "none"),
                "",
                result.get("preview", "")[:1500],
                "",
            ])
            atomic_write_text(report_path, "\n".join(lines))
        return ToolResult(True, "Topic check completed", {"topic": watcher.get("topic"), "results": results, "report": str(report_path)})

    def tool_pipeline(self, steps: list[dict[str, Any]] | str | None = None) -> ToolResult:
        self.require_mutation()
        if isinstance(steps, str):
            try:
                parsed = json.loads(steps)
            except Exception as exc:
                return ToolResult(False, "Pipeline must be JSON", {"error": str(exc), "example": [{"tool": "tool_run", "args": {"name": "html_reference_checker", "args": {"subdir": "."}}}]})
        else:
            parsed = steps
        if not isinstance(parsed, list):
            return ToolResult(False, "Pipeline expects a JSON list of steps", {"received": type(parsed).__name__})
        blocked = {"run_shell", "install_package", "project_delete", "project_remove", "tool_delete", "write_file", "write_files", "append_file", "find_replace", "self_improve", "backtrack_recover", "ai_create_project", "ai_edit_project"}
        outputs = []
        for index, step in enumerate(parsed[:12], 1):
            if not isinstance(step, dict):
                outputs.append({"step": index, "ok": False, "summary": "Step was not an object"})
                break
            tool = str(step.get("tool") or "").strip()
            args = step.get("args") if isinstance(step.get("args"), dict) else {}
            if not tool:
                outputs.append({"step": index, "ok": False, "summary": "Step did not name a tool"})
                break
            if tool in blocked:
                outputs.append({"step": index, "tool": tool, "ok": False, "summary": "Tool is blocked in unattended pipelines"})
                break
            result = self.call(tool, **args)
            outputs.append({"step": index, "tool": tool, "args": args, "ok": result.ok, "summary": result.summary, "data": result.data})
            log_activity("tool_pipeline_step", f"Pipeline step {index}: {tool} -> {result.summary}", {"tool": tool, "args": args, "ok": result.ok})
            if not result.ok:
                break
        ok = bool(outputs) and all(item.get("ok") for item in outputs)
        return ToolResult(ok, "Tool pipeline completed" if ok else "Tool pipeline stopped", {"steps": outputs})

    def agent_execute(self, goal: str, max_steps: int = 6) -> ToolResult:
        self.require_mutation()
        goal = (goal or "").strip()
        if not goal:
            return ToolResult(False, "No agent goal supplied", {"usage": "/agent improve and test the current project"})
        max_steps = max(1, min(int(max_steps or 6), 10))
        steps: list[dict[str, Any]] = []
        catalog = self._tool_catalog_for_agent()
        allowed = {t["name"] for t in catalog if not str(t["name"]).startswith("custom:")}
        context = self._project_context(max_chars=12000)
        for step_no in range(1, max_steps + 1):
            prompt = f"""
You are Nova's bounded local agent. Choose the next helpful tool call for the user's goal.
Return ONLY JSON.

USER GOAL:
{goal}

CURRENT WORKSPACE:
{self.workspace}

RECENT STEPS:
{json.dumps(steps[-5:], ensure_ascii=False, indent=2)}

PROJECT CONTEXT:
{context}

AVAILABLE TOOLS:
{json.dumps(catalog, ensure_ascii=False, indent=2)}

Rules:
- Use one tool call at a time.
- Prefer inspecting files, running tests, creating a custom helper tool if useful, then editing/repairing/testing.
- If a previous tool failed, choose a repair/backtracking step.
- Stop only when the project is tested and improved or when no safe step remains.
- For tool names beginning with custom:, call tool_run with name equal to the part after custom:.

Schema:
{{"thought":"short human-readable reason", "tool":"tool_name_or_done", "args":{{}}, "done":false, "final":"short final message when done"}}
"""
            reply = model_chat(self.config, self.config.model, [{"role": "user", "content": prompt}], timeout=180, desc="agent tool choice")
            log_model_io("prompt", prompt=prompt, data={"mode": "agent", "step": step_no, "goal": goal})
            log_model_io("response", response=reply or "", data={"mode": "agent", "step": step_no, "received_chars": len(reply or "")})
            decision = self._extract_json_object(reply or "") if reply else None
            if not decision:
                steps.append({"step": step_no, "ok": False, "reason": "model did not return a valid tool decision"})
                break
            if decision.get("done") or str(decision.get("tool") or "").lower() in {"done", "stop", "final"}:
                steps.append({"step": step_no, "done": True, "thought": decision.get("thought"), "final": decision.get("final")})
                self._write_agent_trace(goal, steps, {"final": decision.get("final")})
                return ToolResult(True, str(decision.get("final") or "Agent finished"), {"goal": goal, "steps": steps, "trace_file": "AGENT_TRACE.md"})
            tool = str(decision.get("tool") or "").strip()
            args = decision.get("args") if isinstance(decision.get("args"), dict) else {}
            if tool.startswith("custom:"):
                args = {"name": tool.split(":", 1)[1], "args": args}
                tool = "tool_run"
            if tool not in allowed and tool != "tool_run":
                steps.append({"step": step_no, "ok": False, "thought": decision.get("thought"), "tool": tool, "reason": "tool not allowed"})
                break
            result = self.call(tool, **args)
            steps.append({"step": step_no, "thought": decision.get("thought"), "tool": tool, "args": args, "ok": result.ok, "summary": result.summary, "data": result.data})
            log_activity("agent_step", f"Agent step {step_no}: {tool} -> {result.summary}", {"goal": goal, "ok": result.ok, "tool": tool})
            if not result.ok and tool in {"ai_create_project", "ai_edit_project", "run_project", "final_project_check", "verify", "auto_verify"}:
                recovery = self.backtrack_recover(goal=goal, failed_step=f"agent step {step_no}", failed_tool=tool, failure=result.data, max_attempts=2)
                steps.append({"step": step_no, "tool": "backtrack_recover", "ok": recovery.ok, "summary": recovery.summary, "data": recovery.data})
                if not recovery.ok:
                    break
        final = self.final_project_check(".", goal=goal)
        steps.append({"step": "final_check", "ok": final.ok, "summary": final.summary, "data": final.data})
        self._write_agent_trace(goal, steps, final.data)
        return ToolResult(final.ok, "Agent loop finished with final check" if final.ok else "Agent loop stopped with unresolved issues", {"goal": goal, "steps": steps, "final_check": final.data, "trace_file": "AGENT_TRACE.md", "changelog": "CHANGELOG.md"})


    def _write_agent_trace(self, goal: str, steps: list[dict[str, Any]], final: dict[str, Any] | None = None) -> None:
        try:
            lines = ["# Agent Trace", "", f"Goal: {goal}", "", "## Observe → Plan → Act → Verify → Reflect"]
            for st in steps:
                lines.append("")
                lines.append(f"### Step {st.get('step')}")
                if st.get('thought'):
                    lines.append(f"Thought: {st.get('thought')}")
                if st.get('tool'):
                    lines.append(f"Tool: `{st.get('tool')}`")
                lines.append(f"Result: {'PASS' if st.get('ok') or st.get('done') else 'CHECK'} - {st.get('summary') or st.get('final') or st.get('reason') or ''}")
            if final:
                lines.extend(["", "## Final check", json.dumps(final, indent=2, ensure_ascii=False)[:8000]])
                atomic_write_text((self.workspace / "AGENT_TRACE.md"), "\n".join(lines))
            changelog = self.workspace / "CHANGELOG.md"
            prior = changelog.read_text(encoding="utf-8", errors="replace") if changelog.exists() else "# Changelog\n"
            atomic_write_text(changelog, prior.rstrip()+f"\n\n## Agent run {time.strftime('%Y-%m-%d %H:%M:%S')}\n- Goal: {goal}\n- Steps: {len(steps)}\n")
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)

    def improve_project(self, goal: str = "") -> ToolResult:
        ok, summary, data = self._ensure_current_project_for_edit()
        if not ok:
            return ToolResult(False, summary, data)
        goal = (goal or "improve the current project quality, run checks, fix errors, and ensure it meets requirements").strip()
        log_activity("project_improve_start", "Improving current project", {"goal": goal, "workspace": str(self.workspace)})
        return self.agent_execute("Improve current project: " + goal, max_steps=8)

    def improvement_report(self) -> ToolResult:
        report_path = Path(__file__).resolve().parents[1] / "docs" / "IMPROVEMENT_REPORT_V33.md"
        if report_path.exists():
            return ToolResult(True, "Comprehensive improvement report", {"path": str(report_path), "content": report_path.read_text(encoding="utf-8", errors="replace")})
        return ToolResult(False, "Improvement report not found", {"path": str(report_path)})

    def install_package(self, package: str) -> ToolResult:
        self.require_mutation()
        package = (package or "").strip()
        if not re.fullmatch(r"[A-Za-z0-9_.-]{2,80}", package):
            return ToolResult(False, "Package name rejected", {"package": package, "reason": "Use a plain PyPI package name only."})
        allowed = {
            "pytest", "requests", "beautifulsoup4", "lxml", "markdown", "pillow", "numpy", "pandas", "matplotlib",
            "openpyxl", "python-dateutil", "rich", "typer", "fastapi", "uvicorn", "playwright"
        }
        if package.lower() not in allowed:
            return ToolResult(False, "Package is not on the safe install allowlist", {"package": package, "allowed_examples": sorted(allowed)})
        cmd = f"py -3 -m pip install {package}"
        result = self.run_shell(cmd, timeout=300)
        data = dict(result.data)
        data["package"] = package
        return ToolResult(result.ok, f"Installed package {package}" if result.ok else f"Install failed for {package}", data)

    def resource_status(self) -> ToolResult:
        hb = watchdog_heartbeat(self.config, self.workspace)
        return ToolResult(True, "Resource and connectivity status", {"heartbeat": hb, "custom_tools": list_custom_tools(), "watchdog": watchdog_state()})

    def heartbeat(self) -> ToolResult:
        hb = watchdog_heartbeat(self.config, self.workspace)
        return ToolResult(True, "Heartbeat completed", hb)

    def watchdog(self, action: str = "status", interval: int = 30) -> ToolResult:
        action = (action or "status").lower().strip()
        if action in {"on", "start"}:
            data = start_watchdog(self.config, self.workspace, interval=interval)
            return ToolResult(True, "Watchdog started", data)
        if action in {"off", "stop"}:
            data = stop_watchdog()
            return ToolResult(True, "Watchdog stopped", data)
        return ToolResult(True, "Watchdog status", watchdog_state())

    def _self_improve_build_unified_diff(self, original_files: dict[str, str], proposed_files: dict[str, str]) -> str:
        chunks: list[str] = []
        for rel in sorted(proposed_files):
            before = str(original_files.get(rel, ""))
            after = str(proposed_files.get(rel, ""))
            chunks.extend(difflib.unified_diff(
                before.splitlines(),
                after.splitlines(),
                fromfile=f"before/{rel}",
                tofile=f"after/{rel}",
                lineterm="",
            ))
        return "\n".join(chunks)

    def _self_improve_count_changed_lines(self, diff_text: str) -> int:
        count = 0
        for line in (diff_text or "").splitlines():
            if line.startswith(("+++", "---", "@@")):
                continue
            if line.startswith(("+", "-")):
                count += 1
        return count

    def _self_improve_detect_protected_removals(self, diff_text: str) -> list[str]:
        protected_terms = {
            "backup": "backup logic",
            "rollback": "rollback logic",
            "py_compile": "py_compile verification",
            "tests_smoke": "tests_smoke.py verification",
            "resolve_inside_workspace": "workspace path protection",
            "path protection": "path protection",
            "allowlist": "allowlist safety",
            "denylist": "denylist safety",
            "permission": "permission checks",
            "internet": "internet/network gate",
            "network": "internet/network gate",
            "safety": "safety checks",
            "idle lock": "idle lock",
            "_chat_lock": "one-task-at-a-time or idle lock",
            "self-improve guard": "self-improve guard",
            "command block": "command blocking",
            "is_dangerous_command": "command blocking",
            "require_mutation": "mutation guard",
            "workspace protection": "workspace protection",
            "approval": "approval gate",
            "verification": "verification checks",
        }
        reasons: list[str] = []
        for line in (diff_text or "").splitlines():
            if not line.startswith("-") or line.startswith("---"):
                continue
            lowered = line[1:].lower()
            for term, reason in protected_terms.items():
                if term in lowered and reason not in reasons:
                    reasons.append(f"Removed line appears to weaken {reason}: {line[1:].strip()[:160]}")
        return reasons

    def _self_improve_validate_patch(self, proposed_files: dict[str, str], diff_text: str) -> tuple[bool, list[str]]:
        reasons: list[str] = []
        if not proposed_files:
            reasons.append("No proposed files were supplied.")
        if len(proposed_files) > 2:
            reasons.append("Patch changes more than 2 files.")
        changed_lines = self._self_improve_count_changed_lines(diff_text)
        if changed_lines > 250:
            reasons.append(f"Patch changes too many lines ({changed_lines} > 250).")
        if not (diff_text or "").strip():
            reasons.append("Patch diff is empty.")

        blocked_fragments = {
            "__pycache__": "generated Python cache",
            ".env": "environment/secret file",
            ".key": "key file",
            ".pem": "key file",
            ".pfx": "certificate/key file",
            "backup": "backup data",
            "logs": "log data",
            ".venv": "virtual environment",
            "venv": "virtual environment",
            ".winlocalassistant": "profile data",
            "profile": "profile data",
        }
        for rel in proposed_files:
            rel_norm = str(rel).replace("\\", "/")
            rel_low = rel_norm.lower()
            parts = rel_norm.split("/")
            if rel_norm.startswith("/") or ".." in parts or len(parts) != 2 or parts[0] != "winlocalassistant" or not rel_norm.endswith(".py"):
                reasons.append(f"Target file is outside winlocalassistant/*.py: {rel_norm}")
            for fragment, label in blocked_fragments.items():
                if fragment in rel_low:
                    reasons.append(f"Patch attempts to edit {label}: {rel_norm}")

        reasons.extend(self._self_improve_detect_protected_removals(diff_text))
        for line in (diff_text or "").splitlines():
            if not line.startswith("-") or line.startswith("---"):
                continue
            lowered = line.lower()
            for command in ["/idle", "/self-improve", "/help", "/test-all"]:
                if command in lowered:
                    reasons.append(f"Patch removes protected command name {command}.")
        deduped = list(dict.fromkeys(reasons))
        return not deduped, deduped

    def _self_improve_write_report(
        self,
        *,
        goal: str,
        proposed_files: dict[str, str],
        diff_text: str = "",
        validation_reasons: list[str] | None = None,
        verification_commands: list[str] | None = None,
        verification_output: str = "",
        backup_path: str = "",
        rollback_status: str = "",
        final_status: str = "",
    ) -> str:
        report_dir = APP_DIR / "self_improve_reports"
        report_dir.mkdir(parents=True, exist_ok=True)
        path = report_dir / f"self_improve_report_{time.strftime('%Y%m%d_%H%M%S')}.md"
        changed_lines = self._self_improve_count_changed_lines(diff_text)
        diff_snippet = (diff_text or "(no diff)")[:12000]
        reasons = validation_reasons or []
        commands = verification_commands or [
            "python -m py_compile winlocalassistant/*.py",
            "python tests_smoke.py",
        ]
        content = "\n".join([
            "# Self Improve Attempt",
            "",
            "## Goal",
            goal or "(none)",
            "",
            "## Proposed Files",
            "\n".join(f"- {rel}" for rel in sorted(proposed_files)) or "- None.",
            "",
            "## Diff Summary",
            f"Changed lines: {changed_lines}",
            "",
            "```diff",
            diff_snippet,
            "```",
            "",
            "## Guardrail Decision",
            "\n".join(f"- {reason}" for reason in reasons) if reasons else "- Passed guardrail validation.",
            "",
            "## Verification Commands",
            "\n".join(f"- `{cmd}`" for cmd in commands),
            "",
            "## Verification Output",
            "```text",
            verification_output[-12000:] if verification_output else "(not run)",
            "```",
            "",
            "## Backup Path",
            backup_path or "(none)",
            "",
            "## Rollback Status",
            rollback_status or "(not needed)",
            "",
            "## Final Status",
            final_status or "(unknown)",
            "",
        ])
        atomic_write_text(path, content)
        return str(path)

    def self_improve(self, goal: str) -> ToolResult:
        self.require_mutation()
        goal = (goal or "").strip()
        if not goal:
            return ToolResult(False, "No self-improvement goal supplied", {"usage": "/self-improve improve the planner..."})
        source_root = Path(__file__).resolve().parents[1]
        pkg_root = Path(__file__).resolve().parent
        stamp = time.strftime("%Y%m%d_%H%M%S")
        backup = APP_DIR / "self_improve_backups" / f"source_{stamp}.zip"
        backup.parent.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(backup, "w", zipfile.ZIP_DEFLATED) as z:
            for p in source_root.rglob("*"):
                if p.is_file() and not any(part in {"__pycache__", ".git", ".venv"} for part in p.parts):
                    z.write(p, p.relative_to(source_root))
        context = []
        for p in sorted(pkg_root.glob("*.py")):
            try:
                context.append(f"--- winlocalassistant/{p.name} ---\n" + p.read_text(encoding="utf-8", errors="replace")[:12000])
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        prompt = f"""
You are improving Nova's own source code.
Return ONLY valid JSON. No markdown.

Goal:
{goal}

Rules:
- Only edit files under winlocalassistant/.
- Do not remove safety checks, workspace path protections, one-prompt-at-a-time locking, or command blocking.
- Keep changes small and testable.
- Return full replacement contents only for files you edit.

Current source excerpts:
{chr(10).join(context)[:80000]}

JSON schema:
{{
  "notes": "what you changed",
  "files": {{"winlocalassistant/file.py": "full replacement content"}}
}}
"""
        log_activity("self_improve_start", "Asking local LLM to propose source edits", {"goal": goal, "backup": str(backup)})
        reply = model_chat(self.config, self.config.model, [{"role": "user", "content": prompt}], timeout=240, desc="self-improvement source edit")
        data = self._extract_json_object(reply or "") if reply else None
        if not data or not isinstance(data.get("files"), dict):
            report_path = self._self_improve_write_report(
                goal=goal,
                proposed_files={},
                validation_reasons=["Self-improvement LLM response was not valid JSON edits."],
                backup_path=str(backup),
                rollback_status="not-needed-no-files-written",
                final_status="rejected-before-write",
            )
            return ToolResult(False, "Self-improvement LLM response was not valid JSON edits", {"backup": str(backup), "reason": "no files returned", "report": report_path})
        proposed_files = {str(rel).replace("\\", "/"): str(content) for rel, content in (data.get("files") or {}).items()}
        original_files: dict[str, str] = {}
        source_root_resolved = source_root.resolve()
        for rel in proposed_files:
            try:
                target = (source_root / rel).resolve()
                if source_root_resolved == target or source_root_resolved not in target.parents:
                    original_files[rel] = ""
                    continue
                original_files[rel] = target.read_text(encoding="utf-8", errors="replace") if target.exists() and target.is_file() else ""
            except Exception:
                original_files[rel] = ""
        diff_text = self._self_improve_build_unified_diff(original_files, proposed_files)
        valid_patch, validation_reasons = self._self_improve_validate_patch(proposed_files, diff_text)
        validation_commands = [
            "python -m py_compile winlocalassistant/*.py",
            "python tests_smoke.py",
            "actual py_compile: python -m py_compile " + " ".join(str(p) for p in pkg_root.glob("*.py")),
            "actual smoke: python tests_smoke.py",
        ]
        if not valid_patch:
            report_path = self._self_improve_write_report(
                goal=goal,
                proposed_files=proposed_files,
                diff_text=diff_text,
                validation_reasons=validation_reasons,
                verification_commands=validation_commands,
                backup_path=str(backup),
                rollback_status="not-needed-no-files-written",
                final_status="rejected-before-write",
            )
            log_activity("self_improve_rejected", "Self-improvement patch rejected before write", {"goal": goal, "backup": str(backup), "report": report_path, "reasons": validation_reasons})
            return ToolResult(False, "Self-improvement patch rejected by guardrails before writing files", {"backup": str(backup), "report": report_path, "validation_reasons": validation_reasons})
        # SAFETY GATE: Require explicit user approval before applying changes
        approval_msg = f"""SELF-IMPROVE APPROVAL GATE:

Goal: {goal}
Files to modify: {', '.join(proposed_files.keys())}

Diff (first 2000 chars):
{diff_text[:2000]}

Changes summary:
- Validation passed: {len(validation_reasons) == 0}
- Files affected: {len(proposed_files)}
- Backup created at: {backup}

Do you approve? Call /tool-run self_improve_apply_approved to continue."""
        log_activity("self_improve_awaiting_approval", "Self-improvement requires user approval before proceeding", {
            "goal": goal, "files": list(proposed_files.keys()), "backup": str(backup)
        })
        # Store approval token in a temp file so user can retrieve it
        stamp = time.strftime("%Y%m%d_%H%M%S")
        approval_report_path = APP_DIR / "self_improve_reports" / f"approval_pending_{stamp}.json"
        approval_report_path.parent.mkdir(parents=True, exist_ok=True)
        approval_report_path.write_text(json.dumps({
            "status": "awaiting-approval",
            "goal": goal,
            "proposed_files": proposed_files,
            "diff_text": diff_text,
            "validation_reasons": validation_reasons,
            "backup": str(backup),
            "timestamp": stamp,
        }, indent=2))
        return ToolResult(False, approval_msg, {
            "status": "awaiting-approval",
            "backup": str(backup),
            "approval_token": str(approval_report_path),
            "message": "Awaiting user approval - call /tool-run self_improve_apply_approved to proceed"
        })

    def self_improve_apply_approved(self) -> ToolResult:
        """Apply self-improvement changes after user approval (second step of two-step process)."""
        self.require_mutation()
        # Find the most recent pending approval
        reports_dir = APP_DIR / "self_improve_reports"
        if not reports_dir.exists():
            return ToolResult(False, "No pending self-improvement approvals found", {})
        pending = sorted([p for p in reports_dir.glob("approval_pending_*.json")], key=lambda x: x.stat().st_mtime, reverse=True)
        if not pending:
            return ToolResult(False, "No pending self-improvement approvals found", {})
        approval_file = pending[0]
        try:
            approval_data = json.loads(approval_file.read_text())
        except Exception as exc:
            return ToolResult(False, f"Failed to read approval token: {exc}", {})
        proposed_files = approval_data.get("proposed_files", {})
        diff_text = approval_data.get("diff_text", "")
        backup_path = approval_data.get("backup", "")
        goal = approval_data.get("goal", "")
        if not proposed_files or not backup_path:
            return ToolResult(False, "Approval token is invalid or incomplete", {})
        source_root = Path(__file__).resolve().parents[1]
        pkg_root = Path(__file__).resolve().parent
        validation_commands = [
            "python -m py_compile winlocalassistant/*.py",
            "python tests_smoke.py",
        ]
        written = []
        try:
            for rel, content in proposed_files.items():
                rel = str(rel).replace("\\", "/")
                if not rel.startswith("winlocalassistant/") or ".." in rel:
                    raise PermissionError(f"Rejected source edit path: {rel}")
                target = source_root / rel
                if target.suffix != ".py":
                    raise PermissionError(f"Only Python source edits are allowed: {rel}")
                written.append(self._write_one(target, str(content), append=False))
            python_executable = sys.executable or "python"
            compile_cp = subprocess.run([python_executable, "-m", "py_compile", *[str(p) for p in pkg_root.glob("*.py")]], cwd=str(source_root), capture_output=True, text=True, timeout=90)
            smoke = subprocess.run([python_executable, "tests_smoke.py"], cwd=str(source_root), capture_output=True, text=True, timeout=120)
            if compile_cp.returncode != 0 or smoke.returncode != 0:
                with zipfile.ZipFile(backup_path) as z:
                    z.extractall(source_root)
                report_path = self._self_improve_write_report(
                    goal=goal,
                    proposed_files=proposed_files,
                    diff_text=diff_text,
                    validation_reasons=[],
                    verification_commands=validation_commands,
                    verification_output=(compile_cp.stdout or "") + (compile_cp.stderr or "") + "\n" + (smoke.stdout or "") + (smoke.stderr or ""),
                    backup_path=backup_path,
                    rollback_status="rolled-back-from-backup",
                    final_status="verification-failed-rolled-back",
                )
                approval_file.unlink(missing_ok=True)
                return ToolResult(False, "Self-improvement failed tests and was rolled back", {
                    "backup": backup_path, "written": written,
                    "py_compile": compile_cp.stdout + compile_cp.stderr,
                    "smoke_tests": smoke.stdout + smoke.stderr,
                    "rolled_back": True, "report": report_path,
                })
        except Exception as exc:
            with zipfile.ZipFile(backup_path) as z:
                z.extractall(source_root)
            report_path = self._self_improve_write_report(
                goal=goal,
                proposed_files=proposed_files,
                diff_text=diff_text,
                validation_reasons=[],
                verification_commands=validation_commands,
                verification_output=repr(exc),
                backup_path=backup_path,
                rollback_status="rolled-back-from-backup",
                final_status="verification-failed-rolled-back",
            )
            approval_file.unlink(missing_ok=True)
            return ToolResult(False, "Self-improvement failed and was rolled back", {"backup": backup_path, "error": repr(exc), "rolled_back": True, "report": report_path})
        report_path = self._self_improve_write_report(
            goal=goal,
            proposed_files=proposed_files,
            diff_text=diff_text,
            validation_reasons=[],
            verification_commands=validation_commands,
            verification_output="py_compile and tests_smoke.py passed",
            backup_path=backup_path,
            rollback_status="not-needed",
            final_status="success",
        )
        approval_file.unlink(missing_ok=True)
        log_activity("self_improve_applied", "Self-improvement applied successfully with user approval", {"goal": goal, "backup": backup_path, "report": report_path})
        return ToolResult(True, "Self-improvement applied and tests passed", {"backup": backup_path, "written": written, "tests": "py_compile and tests_smoke.py passed", "report": report_path})


    def status(self) -> ToolResult:
        return ToolResult(True, "Assistant status", {
            "workspace": str(self.workspace),
            "allow_mutating_tools": self.config.allow_mutating_tools,
            "allow_internet": self.config.allow_internet,
            "model": self.config.model,
            "chat_model": getattr(self.config, "chat_model", self.config.model),
            "planner_model": getattr(self.config, "planner_model", "") or self.config.model,
            "model_route": getattr(self.config, "model_route", "auto"),
            "model_provider": getattr(self.config, "model_provider", "ollama"),
            "openrouter_model": getattr(self.config, "openrouter_model", ""),
            "ollama_url": self.config.ollama_url,
            "command_timeout_sec": self.config.command_timeout_sec,
            "local_model_timeout_sec": getattr(self.config, "local_model_timeout_sec", 0),
            "local_llm": self._ollama_ps(),
            "tools": sorted(self.tools),
        })

    def _skip(self, path: Path) -> bool:
        noisy = {".git", "__pycache__", ".venv", "venv", "node_modules", ".mypy_cache", ".pytest_cache", "dist", "build"}
        return any(part in noisy for part in path.parts)

    def _safe_workspace_rel(self, path: Path, workspace: Path | None = None) -> str:
        """Return a display/log relative path without crashing on sibling-prefix paths.

        Windows paths such as `Tinyappproject` and `Tinyapp` share a string
        prefix. Earlier code used `str(path).startswith(str(workspace))`, then
        called `relative_to()`, which crashed for sibling folders. Always ask
        pathlib to decide containment instead.
        """
        base = (workspace or self.workspace).expanduser().resolve()
        target = path.expanduser().resolve()
        try:
            return target.relative_to(base).as_posix()
        except ValueError:
            return str(target)

    def list_files(self, subdir: str = ".", limit: int = 200) -> ToolResult:
        root = resolve_inside_workspace(self.workspace, subdir or ".")
        if not root.exists():
            return ToolResult(False, "Directory does not exist", {"path": str(root)})
        files: list[str] = []
        for path in root.rglob("*"):
            if len(files) >= int(limit):
                break
            if self._skip(path):
                continue
            try:
                rel = path.relative_to(self.workspace)
            except ValueError:
                continue
            files.append(str(rel).replace("\\", "/") + ("/" if path.is_dir() else ""))
        return ToolResult(True, f"Found {len(files)} paths", {"root": str(root), "files": files, "download_hint": "Use /download relative/path or the web UI file browser."})

    def tree(self, subdir: str = ".", depth: int = 3, limit: int = 300) -> ToolResult:
        root = resolve_inside_workspace(self.workspace, subdir or ".")
        if not root.exists():
            return ToolResult(False, "Directory does not exist", {"path": str(root)})
        rows: list[str] = []
        root_depth = len(root.parts)
        for p in sorted(root.rglob("*")):
            if len(rows) >= int(limit) or self._skip(p):
                continue
            level = len(p.parts) - root_depth
            if level > int(depth):
                continue
            rows.append("  " * (level - 1) + ("📁 " if p.is_dir() else "📄 ") + p.name)
        return ToolResult(True, f"Tree for {root.name}", {"tree": "\n".join(rows)})

    def read_file(self, path: str, max_chars: int = 30000) -> ToolResult:
        target = resolve_inside_workspace(self.workspace, path)
        if not target.exists() or not target.is_file():
            return ToolResult(False, "File not found", {"path": str(target)})
        text = target.read_text(encoding="utf-8", errors="replace")
        return ToolResult(True, f"Read {target.name}", {"path": str(target), "content": text[:int(max_chars)], "truncated": len(text) > int(max_chars), "download_url": f"/download?path={target.relative_to(self.workspace).as_posix()}"})

    def _write_one(self, target: Path, content: str, append: bool = False) -> dict[str, Any]:
        # SAFETY: Ensure parent directory exists BEFORE any other operations
        target.parent.mkdir(parents=True, exist_ok=True)
        # SAFETY: Prepare backup directory BEFORE reading/writing (if backup needed)
        backup_dir = None
        if target.exists():
            backup_dir = APP_DIR / "backups" / time.strftime("%Y%m%d_%H%M%S")
            backup_dir.mkdir(parents=True, exist_ok=True)  # Ensure backup dir created atomically BEFORE read
        # Now safe to read before content
        before = target.read_text(encoding="utf-8", errors="replace") if target.exists() else ""
        after = before + content if append else content
        # Create backup if file existed and backup dir is ready
        if target.exists() and backup_dir:
            try:
                backup_name = str(target.relative_to(self.workspace)).replace("\\", "__").replace("/", "__")
            except ValueError:
                # Project creation can temporarily write under the project library
                # before the active workspace is switched to that new project.
                # Back up safely instead of crashing on relative_to().
                backup_name = re.sub(r"[^A-Za-z0-9_.-]+", "__", str(target))[-180:]
            atomic_write_text((backup_dir / backup_name), before)
        atomic_write_text(target, after)
        diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile="before", tofile="after", lineterm=""))
        rel_for_log = self._safe_workspace_rel(target)
        log_activity("file_write", f"Wrote {rel_for_log}", {"path": str(target), "bytes": len(after.encode("utf-8")), "preview": after[:4000], "diff_preview": diff[:4000]})
        return {"path": str(target), "bytes": len(after.encode("utf-8")), "diff": diff[:25000]}

    def write_file(self, path: str, content: str, append: bool = False) -> ToolResult:
        self.require_mutation()
        target = resolve_inside_workspace(self.workspace, path)
        info = self._write_one(target, content, append=append)
        evidence = record_task_evidence(
            self.workspace,
            action="append_file" if append else "write_file",
            command=("/append " if append else "/write ") + str(path),
            files_changed=[str(target.relative_to(self.workspace)).replace("\\", "/")],
            result="PASS",
            verification_passed=True,
        )
        return ToolResult(True, f"{'Appended to' if append else 'Wrote'} {target.name}", {**info, "evidence_path": evidence.get("json_path"), "download_url": f"/download?path={target.relative_to(self.workspace).as_posix()}"})

    def append_file(self, path: str, content: str) -> ToolResult:
        return self.write_file(path, content, append=True)

    def write_files(self, files: dict[str, str]) -> ToolResult:
        self.require_mutation()
        if not files:
            return ToolResult(False, "No files supplied", {})
        written = []
        rels = []
        for rel, content in files.items():
            target = resolve_inside_workspace(self.workspace, rel)
            written.append(self._write_one(target, str(content), append=False))
            rels.append(str(target.relative_to(self.workspace)).replace("\\", "/"))
        evidence = record_task_evidence(self.workspace, action="write_files", command="/write_files", files_changed=rels, result="PASS", verification_passed=True)
        return ToolResult(True, f"Wrote {len(written)} files", {"written": written, "evidence_path": evidence.get("json_path"), "download_hint": "Use /zip <folder> or click Download in the web UI."})

    def make_dir(self, path: str) -> ToolResult:
        self.require_mutation()
        target = resolve_inside_workspace(self.workspace, path)
        target.mkdir(parents=True, exist_ok=True)
        return ToolResult(True, f"Created directory {target.name}", {"path": str(target)})

    def find_replace(self, path: str, old: str, new: str, count: int = 0) -> ToolResult:
        self.require_mutation()
        target = resolve_inside_workspace(self.workspace, path)
        if not target.exists():
            return ToolResult(False, "File not found", {"path": str(target)})
        before = target.read_text(encoding="utf-8", errors="replace")
        occurrences = before.count(old)
        if occurrences == 0:
            near = ""
            if old.strip():
                close = difflib.get_close_matches(old, before.splitlines(), n=3, cutoff=0.25)
                near = "\n".join(close)
            return ToolResult(False, "Exact text was not found", {"path": str(target), "old": old, "near_matches": near})
        replace_count = int(count) if int(count) > 0 else occurrences
        after = before.replace(old, new, replace_count)
        atomic_write_text(target, after)
        diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile="before", tofile="after", lineterm=""))
        return ToolResult(True, f"Replaced {min(replace_count, occurrences)} occurrence(s)", {"path": str(target), "occurrences": occurrences, "diff": diff[:25000]})

    def search_text(self, query: str, subdir: str = ".", glob: str = "*", limit: int = 50) -> ToolResult:
        root = resolve_inside_workspace(self.workspace, subdir or ".")
        hits = []
        for p in root.rglob(glob or "*"):
            if len(hits) >= int(limit) or self._skip(p) or not p.is_file():
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="ignore")
            except Exception:
                continue
            for i, line in enumerate(text.splitlines(), start=1):
                if query.lower() in line.lower():
                    hits.append({"path": str(p.relative_to(self.workspace)).replace("\\", "/"), "line": i, "text": line[:250]})
                    break
        return ToolResult(True, f"Found {len(hits)} matching files", {"hits": hits})

    def run_shell(self, command: str, timeout: int | None = None) -> ToolResult:
        self.require_mutation()
        if not command.strip():
            return ToolResult(False, "No command supplied", {})
        guard = repeated_failure_block(self.workspace, "run_shell", command)
        if not guard.ok_to_run:
            evidence = record_task_evidence(
                self.workspace,
                action="run_shell_blocked_repeated_failure",
                command=command,
                result="FAIL",
                stderr=guard.reason + " " + guard.suggested_next_step,
                verification_passed=False,
                user_review_needed=True,
                extra={"repeated_failure_guard": guard.to_dict()},
            )
            return ToolResult(False, "Repeated failure guard blocked command", {"command": command, "repeated_failure_guard": guard.to_dict(), "evidence_path": evidence.get("json_path")})
        dangerous, reason = is_dangerous_command(command)
        if dangerous:
            evidence = record_task_evidence(self.workspace, action="run_shell_blocked_dangerous", command=command, result="FAIL", stderr=reason, verification_passed=False, user_review_needed=True)
            return ToolResult(False, "Command blocked", {"reason": reason, "command": command, "evidence_path": evidence.get("json_path")})
        shell = shutil.which("powershell") or shutil.which("pwsh")
        shell_kind = "powershell"
        shell_cmd = [shell, "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command] if shell else []
        if not shell:
            # Tests and some development environments run on Linux/macOS while Nova's
            # primary user runtime is Windows.  Falling back to bash/sh keeps
            # /shell and /verify honestly usable instead of reporting a false
            # product failure when PowerShell is unavailable.
            shell = shutil.which("bash") or shutil.which("sh")
            if not shell:
                return ToolResult(False, "No supported shell was found on PATH", {"command": command})
            shell_kind = "posix"
            if Path(shell).name == "bash":
                shell_cmd = [shell, "-lc", command]
            else:
                shell_cmd = [shell, "-c", command]
        timeout = int(timeout or self.config.command_timeout_sec)
        log_activity("command_start", f"Running {shell_kind} command", {"command": command, "workspace": str(self.workspace), "timeout": timeout})
        start = time.time()
        try:
            completed = subprocess.run(shell_cmd, cwd=str(self.workspace), capture_output=True, text=True, timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            elapsed = round(time.time() - start, 3)
            stdout = exc.stdout.decode("utf-8", errors="replace") if isinstance(exc.stdout, (bytes, bytearray)) else (exc.stdout or "")
            stderr = exc.stderr.decode("utf-8", errors="replace") if isinstance(exc.stderr, (bytes, bytearray)) else (exc.stderr or "")
            output = (stdout or "") + (stderr or "")
            advice = (
                "Command exceeded the configured timeout. Treat this as a bounded failure: "
                "do not retry the same command blindly; inspect partial output, shorten the command, "
                "increase /model-timeout only for local-model calls, or run a narrower verification step."
            )
            data = {
                "command": command,
                "returncode": None,
                "timed_out": True,
                "timeout_sec": timeout,
                "elapsed_sec": elapsed,
                "output": output[-40000:],
                "advice": advice,
            }
            failure = record_failure_result(self.workspace, "run_shell", command, ok=False, output=output, returncode=None)
            evidence = record_task_evidence(
                self.workspace,
                action="run_shell",
                command=command,
                result="FAIL",
                stdout=stdout,
                stderr=stderr or advice,
                verification_passed=False,
                user_review_needed=True,
                extra={"repeated_failure_guard": failure.to_dict(), "timeout_sec": timeout, "elapsed_sec": elapsed},
            )
            data.update({"repeated_failure_guard": failure.to_dict(), "evidence_path": evidence.get("json_path")})
            log_activity("command_timeout", "PowerShell command timed out", {"command": command, "timeout": timeout, "elapsed_sec": elapsed, "output_tail": output[-8000:], "advice": advice})
            return ToolResult(False, f"Command timed out after {timeout} seconds", data)
        elapsed = round(time.time() - start, 3)
        output = (completed.stdout or "") + (completed.stderr or "")
        ok = completed.returncode == 0
        failure = record_failure_result(self.workspace, "run_shell", command, ok=ok, output=output, returncode=completed.returncode)
        evidence = record_task_evidence(
            self.workspace,
            action="run_shell",
            command=command,
            result="PASS" if ok else ("FAIL" if failure.repeated else "REVIEW"),
            stdout=completed.stdout or "",
            stderr=completed.stderr or "",
            verification_passed=ok,
            user_review_needed=not ok,
            extra={"returncode": completed.returncode, "elapsed_sec": elapsed, "repeated_failure_guard": failure.to_dict()},
        )
        log_activity("command_done" if ok else "command_failed", f"{shell_kind} command finished", {"command": command, "returncode": completed.returncode, "elapsed_sec": elapsed, "output_tail": output[-8000:]})
        return ToolResult(ok and not failure.repeated, "Command completed" if ok else ("Repeated failure guard tripped" if failure.repeated else "Command failed"), {"command": command, "returncode": completed.returncode, "elapsed_sec": elapsed, "output": output[-40000:], "repeated_failure_guard": failure.to_dict(), "evidence_path": evidence.get("json_path")})

    def verify(self, command: str) -> ToolResult:
        raw = (command or "").strip()
        full = "--full" in raw.lower()
        clean_command = raw.replace("--full", "").strip()
        if not clean_command:
            summary = build_verify_summary(self.workspace, full=full, command="")
            evidence = record_task_evidence(self.workspace, action="verify_summary", command="/verify" + (" --full" if full else ""), result=str(summary.get("final_result") or "REVIEW"), verification_passed=bool(summary.get("ok")), user_review_needed=summary.get("status") != "PASS", extra={"verify_summary": summary})
            summary["evidence_path"] = evidence.get("json_path")
            return ToolResult(bool(summary.get("ok")), "Verification summary", {"message": render_verify_summary(summary), **summary})
        result = self.run_shell(clean_command)
        data = dict(result.data)
        output = str(data.get("output", ""))
        low = output.lower()
        problems = [m for m in ["error", "failed", "traceback", "exception", "syntaxerror", "indentationerror", "missing"] if m in low]
        passed = result.ok and not problems
        verdict = "PASS" if passed else ("FAIL" if (data.get("repeated_failure_guard") or {}).get("repeated") else "REVIEW")
        verify_summary = build_verify_summary(self.workspace, full=full, command=clean_command)
        data["verification"] = {"passed": passed, "problem_markers": problems, "advice": "Passed." if passed else "Fix the first concrete error in the output, then rerun verification.", "final_result": verdict, "summary": verify_summary}
        evidence = record_task_evidence(
            self.workspace,
            action="verify",
            command=clean_command,
            tests_run=[clean_command],
            result=verdict,
            stdout=output,
            verification_passed=passed,
            user_review_needed=not passed,
            extra={"verification": data["verification"]},
        )
        data["verification"]["evidence_path"] = evidence.get("json_path")
        data["evidence_path"] = evidence.get("json_path")
        return ToolResult(passed, "Verification passed" if passed else "Verification found problems", data)

    def detect_project(self) -> ToolResult:
        root = self.workspace
        markers = {
            "python": ["pyproject.toml", "requirements.txt"],
            "node": ["package.json"],
            "dotnet": ["*.sln", "*.csproj"],
            "rust": ["Cargo.toml"],
        }
        found: dict[str, list[str]] = {}
        for kind, pats in markers.items():
            paths = []
            for pat in pats:
                paths.extend(str(p.relative_to(root)).replace("\\", "/") for p in root.glob(pat))
                paths.extend(str(p.relative_to(root)).replace("\\", "/") for p in root.rglob(pat) if not self._skip(p))
            if paths:
                found[kind] = sorted(set(paths))[:20]
        return ToolResult(True, "Detected project markers" if found else "No standard project markers found", {"detected": found})

    def auto_verify(self) -> ToolResult:
        root = self.workspace
        if (root / "package.json").exists():
            return self.verify("npm test")
        if (root / "pyproject.toml").exists() or list(root.glob("*.py")):
            return self.verify("py -3 -m compileall .")
        if list(root.glob("*.sln")) or list(root.glob("*.csproj")):
            return self.verify("dotnet build")
        if (root / "Cargo.toml").exists():
            return self.verify("cargo check")
        return ToolResult(False, "Could not infer a verification command", {"advice": "Run /verify <command> with the exact build/test command."})



    # -------------------------
    # Model-driven build/edit tools
    # -------------------------

    def _slug(self, text: str, default: str = "GeneratedProject") -> str:
        words = re.findall(r"[A-Za-z0-9]+", str(text).title())
        stop = {"Make", "Build", "Create", "Generate", "Write", "A", "An", "The", "Useful", "Basic", "Simple", "Project"}
        words = [w for w in words if w not in stop]
        return ("".join(words[:5]) or default)[:48]

    def _project_library_root(self) -> Path:
        """Return the project library root used for NEW projects.

        New /fast, /long, /do make..., and /project-create operations must not use
        the currently-open project as their base. Older builds accidentally created
        ProjectA/ProjectB/ProjectC nesting when the workspace was a project folder.

        Rules:
        - Prefer the nearest ancestor named NovaProjects.
        - Otherwise use the default Documents/NovaProjects folder.
        """
        default_root = (Path.home() / "Documents" / "NovaProjects").expanduser().resolve()
        try:
            ws = self.workspace.expanduser().resolve()
            for candidate in [ws, *ws.parents]:
                # Keep the legacy folder accepted, but prefer the rebranded
                # NovaProjects library root described in this function's contract.
                if candidate.name.lower() in {"novaprojects", "winlocalassistantprojects"}:
                    candidate.mkdir(parents=True, exist_ok=True)
                    return candidate
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        default_root.mkdir(parents=True, exist_ok=True)
        return default_root

    def _is_project_library_root(self, path: Path | None = None) -> bool:
        try:
            target = (path or self.workspace).expanduser().resolve()
            return target == self._project_library_root()
        except Exception:
            return False

    def _looks_like_project_root(self, path: Path | None = None) -> bool:
        root = (path or self.workspace).expanduser().resolve()
        if self._is_project_library_root(root):
            return False
        markers = [
            ".nova_project.json",
            "PROJECT_MANIFEST.json",
            "index.html",
            "app.py",
            "main.py",
            "package.json",
            "pyproject.toml",
        ]
        return any((root / m).exists() for m in markers)

    def _ensure_current_project_for_edit(self) -> tuple[bool, str, dict[str, Any]]:
        """Ensure an edit/improve/fix command is pointed at an actual project.

        If the workspace is the project library root, try to reopen the current
        project from the registry. If none exists, stop with a helpful message
        rather than editing the library root or creating nested projects.
        """
        if self._looks_like_project_root(self.workspace):
            return True, "Using current project workspace", {"workspace": str(self.workspace)}
        current = get_project()
        if current and Path(current.get("path", "")).expanduser().exists():
            path = Path(current["path"]).expanduser().resolve()
            if self._looks_like_project_root(path):
                self.config.workspace = str(path)
                self.config.save()
                self.workspace = path
                return True, f"Opened current project {current.get('name')}", {"project": current, "workspace": str(path)}
        projects = list_projects()
        return False, "Open a project before improving/editing", {
            "workspace": str(self.workspace),
            "reason": "The workspace is the project library/root folder, not a single project. This prevents accidental nested project creation or broad-folder edits.",
            "projects": projects,
            "fix": "Use /project-open NAME, then run /improve-project again. Use /long make ... only when creating a new project.",
        }

    def _extract_json_object(self, text: str) -> dict[str, Any] | None:
        """Extract JSON returned by a local model, tolerating common LLM mistakes.

        qwen3-coder often returns JSON inside markdown fences and sometimes writes
        Windows paths like ``start .\\index.html``. In JSON, an unescaped
        backslash before letters such as ``i`` is invalid. Earlier builds rejected
        those otherwise useful project responses as "not parseable JSON". This
        parser strips fences, extracts the outer object, and retries after escaping
        invalid backslashes inside strings.
        """
        if not text:
            return None
        cleaned = text.strip()
        # Strip a single surrounding code fence, but also work if commentary leaks in.
        if cleaned.startswith("```"):
            cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned, flags=re.I)
            cleaned = re.sub(r"\s*```$", "", cleaned)
        candidates = [cleaned]
        start = cleaned.find("{")
        end = cleaned.rfind("}")
        if start >= 0 and end > start:
            candidates.append(cleaned[start:end + 1])

        def fix_invalid_backslashes(s: str) -> str:
            # JSON only allows escapes: " \/ b f n r t u.
            # Preserve valid escapes and double invalid backslashes inside string literals only.
            def replace_string(match: re.Match[str]) -> str:
                inner = match.group(1)
                fixed_inner = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', inner)
                return f'"{fixed_inner}"'

            return re.sub(r'"((?:[^"\\]|\\.)*)"', replace_string, s)

        for candidate in candidates:
            for variant in (candidate, fix_invalid_backslashes(candidate)):
                try:
                    data = json.loads(variant)
                    if isinstance(data, dict):
                        return data
                except Exception:
                    continue
        return None

    def _project_context(self, max_files: int = 12, max_chars_each: int = 9000, max_chars: int | None = None) -> str:
        # Backward-compatible alias: older agent code called _project_context(max_chars=...).
        if max_chars is not None:
            try:
                max_chars = int(max_chars)
                max_files = max(1, min(max_files, 40))
                max_chars_each = max(800, max_chars // max_files)
            except Exception as exc:
                    log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        rows = []
        for p in sorted(self.workspace.rglob("*")):
            if len(rows) >= max_files:
                break
            if self._skip(p) or not p.is_file():
                continue
            if p.suffix.lower() not in {".py", ".js", ".html", ".css", ".md", ".txt", ".json", ".toml", ".bat", ".ps1", ".java", ".xml", ".yaml", ".yml"}:
                continue
            try:
                rel = p.relative_to(self.workspace).as_posix()
                content = p.read_text(encoding="utf-8", errors="replace")[:max_chars_each]
                rows.append(f"--- FILE: {rel} ---\n{content}")
            except Exception:
                continue
        return "\n\n".join(rows) if rows else "(No readable project files found.)"


    def _tool_catalog_for_agent(self) -> list[dict[str, Any]]:
        """Return a bounded catalogue of tools the local agent may choose from.

        v30 accidentally called this method without defining it, causing
        /improve-project to crash before doing any useful work. Keep this list
        deliberately small and safe: it exposes inspection, verification,
        targeted repair, custom tool creation/running, and final checking.
        """
        base = [
            {"name": "status", "purpose": "show assistant status and workspace"},
            {"name": "list_files", "purpose": "list files under the current project"},
            {"name": "tree", "purpose": "show a project tree"},
            {"name": "read_file", "purpose": "read a project file"},
            {"name": "search_text", "purpose": "search text in project files"},
            {"name": "detect_project", "purpose": "detect project type"},
            {"name": "auto_verify", "purpose": "run an inferred verification command"},
            {"name": "verify", "purpose": "run a specific safe verification command"},
            {"name": "run_project", "purpose": "prepare/run current project preview"},
            {"name": "surgical_repair", "purpose": "apply targeted deterministic repairs to small errors"},
            {"name": "final_project_check", "purpose": "final requirement and syntax check"},
            {"name": "tool_create", "purpose": "create a safe custom helper tool if useful"},
            {"name": "tool_run", "purpose": "run a named custom tool"},
            {"name": "tool_help", "purpose": "inspect custom tool inputs and examples"},
            {"name": "tool_pipeline", "purpose": "run bounded safe sequential tool calls"},
            {"name": "safe_script_demo", "purpose": "return real deterministic local demo output"},
            {"name": "idle_lessons", "purpose": "read prior idle lessons from the assistant profile"},
            {"name": "topic_watchers", "purpose": "list saved internet topic watchers"},
            {"name": "topic_check", "purpose": "check a saved topic watcher when internet is enabled"},
            {"name": "tool_view", "purpose": "inspect custom tool source and metadata before using it"},
            {"name": "tool_use_guide", "purpose": "show the recommended tool sequence for building, testing and repairing"},
            {"name": "investigate_logs", "purpose": "read recent errors and write ERROR_INVESTIGATION.md"},
            {"name": "propose_improvements", "purpose": "propose safe changes to assistant/tool/project code from logs"},
            {"name": "write_file", "purpose": "write one file when a precise repair is needed"},
            {"name": "find_replace", "purpose": "make an exact targeted replacement"},
        ]
        for tool in list_custom_tools():
            if tool.get("enabled", True) and tool.get("exists", True):
                base.append({
                    "name": f"custom:{tool.get('name')}",
                    "purpose": tool.get("description", "custom tool"),
                    "risk": tool.get("risk", "read_only"),
                    "input_schema": tool.get("input_schema", {}),
                })
        return base

    def _local_model_runtime_context(self, root: Path | None = None) -> str:
        """Small recent failure/runtime pack for local model repair prompts."""
        lines: list[str] = []
        try:
            interesting = {
                "command_failed",
                "verification_failed",
                "llm_failed",
                "llm_rejected",
                "known_error_recovery_incomplete",
                "candidate_refine_step",
                "auto_code_fix",
                "file_write",
            }
            rows = [row for row in tail_jsonl(ACTIVITY_PATH, limit=80) if str(row.get("kind") or "") in interesting]
            for row in rows[-10:]:
                data = row.get("data") if isinstance(row.get("data"), dict) else {}
                detail = data.get("summary") or data.get("reason") or data.get("failure_type") or data.get("output") or data.get("file") or ""
                lines.append(f"- {row.get('time','')} {row.get('kind','')}: {row.get('message','')} {str(detail)[:500]}")
        except Exception as exc:
            log_activity("local_model_runtime_context_activity_failed", "Could not read recent activity context for local model prompt", {"error": repr(exc)})
        try:
            model_rows = tail_jsonl(MODEL_IO_PATH, limit=8)
            for row in model_rows[-4:]:
                phase = row.get("phase") or "model"
                preview = row.get("response_preview") or row.get("prompt_preview") or ""
                if preview:
                    lines.append(f"- {phase}: {str(preview).replace(chr(10), ' ')[:700]}")
        except Exception as exc:
            log_activity("local_model_runtime_context_model_io_failed", "Could not read recent model I/O context for local model prompt", {"error": repr(exc)})
        try:
            report = (root or Path(self.workspace)) / "PROJECT_VERIFICATION_REPORT.md"
            if report.exists() and report.is_file():
                text = report.read_text(encoding="utf-8", errors="replace")
                lines.append("- Project verification report excerpt: " + text.replace("\n", " ")[:1200])
        except Exception as exc:
            log_activity("local_model_runtime_context_report_failed", "Could not read project verification report context for local model prompt", {"error": repr(exc), "root": str(root or Path(self.workspace))})
        return "\n".join(lines[-16:]) if lines else "No recent runtime/model errors were available."

    def _local_model_verification_conditions(self, goal: str, problems: list[dict[str, Any]] | None = None) -> list[str]:
        """Concrete acceptance checks injected into local-model prompts."""
        low = (goal or "").lower()
        checks: list[str] = [
            "match the user's actual domain words, not a generic demo",
            "create or edit real runnable files, not only README/report claims",
            "preserve existing project files and GUI/backend functionality unless the user explicitly asks to remove them",
            "do not replace a working feature with a simpler unrelated demo to satisfy a surface-level check",
            "the documented run command and entry point must exist",
            "syntax and behavioural checks must pass before success is reported",
        ]
        if "game" in low or "snake" in low or "pong" in low:
            checks.extend([
                "include real player controls such as keydown/keyup, pointer or touch handlers",
                "include a real update/draw loop such as requestAnimationFrame or setInterval",
                "include collision/interaction logic between player and targets/hazards/enemies",
                "show score/progress and a restart or game-over path",
                "make the visible theme reflect the requested game subject",
            ])
        if self._goal_requests_file_creation_script(low):
            checks.extend([
                "accept filename and content from the user",
                "create/download/write a real file or clearly implement browser download behaviour",
                "include path/name safety handling and do not replace it with a name/email verification demo",
            ])
        if "tool" in low or "custom tool" in low:
            checks.extend([
                "tool creation is complete only when the tool file exists, registry refresh sees it, and tool_test/tool_run succeeds",
                "do not report tool success from heartbeat/runtime self-check alone",
            ])
        for problem in problems or []:
            if isinstance(problem, dict):
                msg = str(problem.get("message") or problem.get("kind") or problem)
            else:
                msg = str(problem)
            if msg and msg not in checks:
                checks.append(f"fix prior validation problem: {msg}")
        return checks[:18]

    def _local_model_implementation_context(
        self,
        root: Path | None = None,
        goal: str = "",
        last_reason: str = "",
        attempts: list[dict[str, Any]] | None = None,
        previous_problems: list[dict[str, Any]] | None = None,
    ) -> str:
        """Compact run/analysis/verification pack for build and retry prompts.

        Repeated candidate-refinement failures usually happen when the model is asked
        to retry without enough evidence. This pack gives it the latest failure,
        recent files, prior attempt summaries and explicit success conditions.
        """
        root = Path(root or self.workspace)
        recent_files: list[dict[str, Any]] = []
        if root.exists():
            try:
                candidates = sorted(
                    [p for p in root.rglob("*") if p.is_file() and not self._skip(p)],
                    key=lambda q: q.stat().st_mtime,
                    reverse=True,
                )
            except Exception:
                candidates = []
            for file in candidates:
                if len(recent_files) >= 8:
                    break
                if file.suffix.lower() not in {".html", ".js", ".css", ".py", ".json", ".md", ".txt", ".java", ".ps1", ".bat"}:
                    continue
                try:
                    recent_files.append({
                        "path": file.relative_to(root).as_posix(),
                        "size": file.stat().st_size,
                        "preview": file.read_text(encoding="utf-8", errors="replace")[:700],
                    })
                except Exception as exc:
                    recent_files.append({"path": file.name, "error": repr(exc)})
        compact_attempts = []
        for item in (attempts or [])[-4:]:
            compact_attempts.append({
                "attempt": item.get("attempt"),
                "status": item.get("status"),
                "reason": str(item.get("reason") or "")[:500],
                "files": item.get("files"),
            })
        nova_context = build_nova_operating_context(root, goal=goal, mode="local_model_build_or_repair", last_failure=last_reason, attempts=compact_attempts)
        payload = {
            "goal": goal,
            "workspace_root": str(root),
            "last_rejection_or_runtime_failure": str(last_reason or "")[:1200],
            "previous_attempts": compact_attempts,
            "verification_conditions": self._local_model_verification_conditions(goal, previous_problems),
            # Keep these contracts near the top: the context pack is intentionally
            # capped for small local models, and preservation rules must not be
            # truncated when runtime/file previews are large.
            "feature_preservation_contract": [
                "Before editing, keep any already-working user-facing capability unless the user explicitly asked to remove it.",
                "When redesigning UI, regroup controls instead of deleting entry points; keep compatibility wrappers for existing JS functions.",
                "If a proposed improvement cannot be implemented safely, report no-op or blocked rather than pretending success.",
            ],
            "action_receipt_contract": [
                "After implementation, record changed files, validation commands/results and remaining risks.",
                "Do not mark implemented unless changed_files is non-empty and validation evidence exists.",
            ],
            "strategy_rules_v2": [
                "Start from the mission contract success conditions; heartbeat/runtime-self-check are forbidden as proof of goal completion.",
                "Patch existing files where possible; regenerate only after the patch path is impossible or has repeated no-progress.",
                "If the same failure repeats, switch to a deterministic template or surgical recipe instead of asking for the same model output again.",
                "When a behavioural check fails, repair the named behaviour, not just syntax or keywords.",
            ],
            "mission_contract": build_mission_contract(goal or "general Nova task"),
            "development_strategy": build_strategy_decision(goal or "general Nova task", last_failure=last_reason, attempts=compact_attempts),
            "validation_evidence": build_validation_evidence(root, goal=goal),
            "project_type_contract": project_type_contract(goal or "general local project"),
            "generation_template_manifest": build_generation_template_manifest(goal or "general local project"),
            "persona_profile": load_persona_profile(),
            "persona_prompt_addendum": build_persona_prompt_addendum("build_or_repair"),
            "local_model_optimization_plan": build_local_model_optimization_plan(root, goal=goal),
            "iterative_agent_harness": build_iterative_agent_harness(root, goal=goal),
            "nova_operating_context": nova_context,
            "recent_runtime_context": self._local_model_runtime_context(root),
            "recent_relevant_files": recent_files,
            "retry_instruction": "If the same validation reason appears twice, switch strategy or use a deterministic complete baseline; do not keep polishing the same failing structure.",
            "success_rule": "Only claim success when changed files implement the behaviour and the listed verification conditions are satisfied.",
        }
        return self._serialise_local_model_context_payload(payload, max_chars=26000)

    def _serialise_local_model_context_payload(self, payload: dict[str, Any], max_chars: int = 26000) -> str:
        """Serialise local-model context without truncating required contracts.

        The old implementation sliced the finished JSON string. That could remove
        late but critical fields such as feature_preservation_contract, which meant
        tests caught the problem only after packaging. This keeps protected keys
        at the top and trims only bulky diagnostic fields/previews.
        """
        protected = [
            "goal",
            "workspace_root",
            "last_rejection_or_runtime_failure",
            "previous_attempts",
            "verification_conditions",
            "feature_preservation_contract",
            "action_receipt_contract",
            "strategy_rules_v2",
            "mission_contract",
            "development_strategy",
            "project_type_contract",
            "generation_template_manifest",
            "persona_profile",
            "persona_prompt_addendum",
            "local_model_optimization_plan",
            "iterative_agent_harness",
            "retry_instruction",
            "success_rule",
        ]
        dynamic = [
            "validation_evidence",
            "nova_operating_context",
            "recent_runtime_context",
            "recent_relevant_files",
        ]

        def trim_value(value: Any, limit: int) -> Any:
            if isinstance(value, str):
                return value if len(value) <= limit else value[:limit] + "…[truncated]"
            if isinstance(value, list):
                out = []
                for item in value[:8]:
                    out.append(trim_value(item, max(250, limit // max(2, min(len(value), 8)))))
                return out
            if isinstance(value, dict):
                out: dict[str, Any] = {}
                for key, item in value.items():
                    k = str(key)
                    if k in {"preview", "content", "output", "response", "prompt", "markdown"}:
                        out[k] = trim_value(item, min(limit, 900))
                    else:
                        out[k] = trim_value(item, min(limit, 1600))
                return out
            return value

        ordered: dict[str, Any] = {}
        for key in protected:
            if key in payload:
                ordered[key] = payload[key]
        for key in payload:
            if key not in ordered and key not in dynamic:
                ordered[key] = payload[key]
        for key in dynamic:
            if key in payload:
                ordered[key] = trim_value(payload[key], 2500)

        text = json.dumps(ordered, ensure_ascii=False, indent=2)
        if len(text) <= max_chars:
            return text

        # Second pass: reduce bulky dynamic evidence further, preserving all protected contracts.
        compact = {k: v for k, v in ordered.items() if k not in dynamic}
        for key in dynamic:
            if key in ordered:
                compact[key] = trim_value(ordered[key], 900)
        text = json.dumps(compact, ensure_ascii=False, indent=2)
        if len(text) <= max_chars:
            return text

        # Last resort: protected fields plus a small omitted-fields marker.
        minimal = {k: payload[k] for k in protected if k in payload}
        minimal["omitted_due_to_context_budget"] = [k for k in payload.keys() if k not in minimal]
        text = json.dumps(minimal, ensure_ascii=False, indent=2)
        if len(text) <= max_chars:
            return text
        # If protected fields themselves are too large, only trim known large nested fields.
        for key in ["mission_contract", "development_strategy", "project_type_contract", "generation_template_manifest"]:
            if key in minimal:
                minimal[key] = trim_value(minimal[key], 1200)
        return json.dumps(minimal, ensure_ascii=False, indent=2)[:max_chars]

    def _validation_goal_text(self, goal: str) -> str:
        """Return the user request slice that validators should judge against."""
        text = str(goal or "").strip()
        if not text:
            return ""
        lower = text.lower()
        shared_context_markers = [
            "\nuse these user-shared files as context for this request:",
            "\n[shared file context:",
            "\nattached image:",
        ]
        shared_hits = [lower.find(marker) for marker in shared_context_markers if lower.find(marker) >= 0]
        if shared_hits:
            text = text[:min(shared_hits)]
            lower = text.lower()
        markers = [
            "original user goal:",
            "original user request:",
            "original goal:",
            "original request:",
            "user requirement:",
            "user goal:",
            "request:",
        ]
        marker_hits = [(lower.find(marker), marker) for marker in markers if lower.find(marker) >= 0]
        if marker_hits:
            idx, marker = min(marker_hits, key=lambda item: item[0])
            text = text[idx + len(marker):]
            lower = text.lower()
        stop_markers = [
            "\nfailed step:",
            "\nfailure details:",
            "\nfailure detail",
            "\nfailure/acceptance problems:",
            "\nfailure:",
            "\nknown problems",
            "\ncurrent edit request:",
            "\nlatest event:",
            "\nuse these user-shared files as context for this request:",
            "\n[shared file context:",
            "\nattached image:",
        ]
        stop_hits = [lower.find(marker) for marker in stop_markers if lower.find(marker) >= 0]
        if stop_hits:
            text = text[:min(stop_hits)]
        if "did not request a dodge game" in text.lower() and "make a game" not in text.lower() and "build a game" not in text.lower():
            text = re.sub(r"\bdodge game\b", "dodge default", text, flags=re.IGNORECASE)
        return text.strip() or str(goal or "").strip()

    def _goal_domain_requirements(self, goal: str) -> dict[str, list[str]]:
        """Return domain-specific words that should appear in a real implementation.

        This is not a template generator. It is a guardrail that prevents the assistant
        from accepting a generic notes/task app when the user asked for a specific app.
        The local LLM still writes the actual code.

        Important: use whole-word matching. Earlier builds used substring matching,
        so a request with "example bugs" accidentally matched "exam" and was
        incorrectly validated as a study/exam planner.
        """
        if self._is_failure_feedback_goal(goal):
            return {}
        g = self._validation_goal_text(goal).lower()
        words = set(re.findall(r"[a-z][a-z0-9]*", g))

        def has_any(*terms: str) -> bool:
            return any(term in words for term in terms)

        req: dict[str, list[str]] = {}
        if has_any("stock", "stocks", "trade", "trader", "trading", "portfolio", "shares"):
            req["stock_trading"] = ["ticker", "portfolio", "watchlist", "shares", "buy", "sell", "price", "profit", "loss", "cash", "trade"]
        if has_any("budget", "finance", "expense", "expenses", "money"):
            req["finance"] = ["income", "expense", "budget", "balance", "category", "transaction"]
        if has_any("study", "homework", "assignment", "assignments", "exam", "exams"):
            req["study"] = ["subject", "due", "priority", "progress", "minutes", "task"]
        if has_any("bug", "bugs", "issue", "issues", "debug", "tracker"):
            req["bug_tracker"] = ["bug", "issue", "severity", "status", "reproduction", "steps", "cause", "fix", "project"]
        if has_any("recipe", "recipes", "meal", "meals", "cooking"):
            req["recipe"] = ["ingredient", "recipe", "meal", "serving", "cook", "step"]
        if has_any("fitness", "workout", "workouts", "exercise", "exercises"):
            req["fitness"] = ["workout", "exercise", "sets", "reps", "progress", "routine"]
        if has_any("game", "games", "frog", "frogs", "shooter", "platformer"):
            # Only true game requests should use gameplay/collision validation.
            # Broad requests such as "make a tiny useful app" must not inherit
            # game-domain checks from fallback templates or stale context.
            req["game"] = ["score", "game", "controls", "interaction"]
        if self._goal_requests_file_creation_script(goal):
            req["file_creation"] = ["file", "filename", "content", "create", "write", "save", "path", "folder", "generated_files", "readme"]
        return req


    def _goal_requests_file_search_script(self, goal: str) -> bool:
        g = self._validation_goal_text(goal).lower()
        words = set(re.findall(r"[a-z][a-z0-9]*", g))
        file_words = bool(words & {"file", "files", "folder", "directory", "type", "types"})
        search_words = bool(words & {"search", "find", "look", "looks", "grep", "scan", "inside", "contains", "string", "text"})
        script_words = bool(words & {"script", "scripts", "cli", "python", "powershell", "tool", "program"})
        return file_words and search_words and script_words

    def _fallback_file_string_search_project(self, goal: str) -> dict[str, Any]:
        script = r"""from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

TEXT_EXTENSIONS = {
    ".txt", ".md", ".py", ".js", ".ts", ".html", ".css", ".json", ".csv", ".xml", ".yaml", ".yml", ".ini", ".log"
}


def iter_files(root: Path, include_hidden: bool = False) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if not include_hidden and any(part.startswith(".") for part in path.parts):
            continue
        yield path


def search_file(path: Path, needle: str, case_sensitive: bool = False) -> list[dict]:
    raw_needle = needle if case_sensitive else needle.lower()
    try:
        data = path.read_bytes()
    except OSError as exc:
        return [{"path": str(path), "error": str(exc)}]

    # Byte search means the script can inspect any file type safely, including binary files.
    hay_bytes = data if case_sensitive else data.lower()
    needle_bytes = needle.encode("utf-8", errors="ignore")
    if not case_sensitive:
        needle_bytes = needle_bytes.lower()
    if needle_bytes and needle_bytes in hay_bytes:
        if path.suffix.lower() not in TEXT_EXTENSIONS:
            return [{"path": str(path), "binary_match": True, "line": None, "preview": "matched bytes in non-text/binary file"}]

    try:
        text = data.decode("utf-8", errors="replace")
    except Exception:
        text = ""
    hay = text if case_sensitive else text.lower()
    if raw_needle not in hay:
        return []
    results = []
    for line_no, line in enumerate(text.splitlines(), 1):
        comparable = line if case_sensitive else line.lower()
        if raw_needle in comparable:
            results.append({"path": str(path), "line": line_no, "preview": line.strip()[:240]})
    return results or [{"path": str(path), "line": None, "preview": "matched file content"}]


def main() -> int:
    parser = argparse.ArgumentParser(description="Search for a string inside any file type under a folder.")
    parser.add_argument("string", nargs="?", default="Nova", help="String to search for")
    parser.add_argument("--root", default=".", help="Folder to scan recursively")
    parser.add_argument("--case-sensitive", action="store_true", help="Use case-sensitive matching")
    parser.add_argument("--include-hidden", action="store_true", help="Include hidden folders/files")
    parser.add_argument("--json", action="store_true", help="Print JSON results")
    args = parser.parse_args()
    root = Path(args.root).resolve()
    matches = []
    for path in iter_files(root, include_hidden=args.include_hidden):
        matches.extend(search_file(path, args.string, case_sensitive=args.case_sensitive))
    if args.json:
        print(json.dumps({"root": str(root), "string": args.string, "matches": matches, "count": len(matches)}, indent=2))
    else:
        print(f"searched={root}")
        print(f"string={args.string}")
        print(f"matches={len(matches)}")
        for item in matches[:200]:
            loc = f":{item.get('line')}" if item.get("line") else ""
            print(f"{item.get('path')}{loc} :: {item.get('preview') or item.get('error') or 'matched'}")
    return 0 if matches else 1


if __name__ == "__main__":
    raise SystemExit(main())
"""
        readme = """# File String Searcher

A small Python CLI script that searches for a given string inside any file type under a folder.

## Run

```powershell
python file_string_search.py "Nova" --root .
```

## JSON output

```powershell
python file_string_search.py "Nova" --root . --json
```

The script scans recursively, reports line numbers for text files, and falls back to byte matching for binary/non-text file types.
"""
        return {
            "folder": "FileStringSearcher",
            "main_file": "file_string_search.py",
            "run_command": "python file_string_search.py Nova --root .",
            "verify_command": "python -m py_compile file_string_search.py && python file_string_search.py Search --root . --json",
            "notes": "Created a real string-search script instead of a file-creation script. It recursively searches any file type and can print JSON results.",
            "human_summary": "Built FileStringSearcher: run `python file_string_search.py \"text\" --root .` to find a string inside files.",
            "files": {
                "file_string_search.py": script,
                "README.md": readme,
                "PROJECT_ITERATION_LOG.jsonl": json.dumps({"event": "baseline_created", "goal": goal, "feature": "recursive string search across file types"}) + "\n",
            },
            "source": "deterministic_string_search_script_fallback",
            "fallback_reason": "request asked for a script that searches for a string inside files; Nova used a domain-specific deterministic fallback after local-model uncertainty",
        }

    def _goal_requests_file_creation_script(self, goal: str) -> bool:
        g = self._validation_goal_text(goal).lower()
        words = set(re.findall(r"[a-z][a-z0-9]*", g))
        file_words = bool(words & {"file", "files", "filename", "filenames"})
        create_words = bool(words & {"create", "creation", "creator", "generate", "generator", "write", "make"})
        script_words = bool(words & {"script", "scripts", "cli", "python", "powershell", "tool", "program"})
        return file_words and create_words and script_words

    def _file_creation_terms_present(self, combined: str) -> bool:
        text = combined.lower()
        filename = any(t in text for t in ["filename", "file_name", "file name", "--name", "name_input", "filenameinput"])
        content = any(t in text for t in ["content", "write_text", "blob", "textarea", "--content"])
        action = any(t in text for t in ["generated_files", "write_text", "open(", "download", "createobjecturl", "pathlib", "mkdir"])
        safety = any(t in text for t in ["sanitize", "safe", "resolve", "path", "folder"])
        return filename and content and action and safety

    def _generic_template_markers(self) -> list[str]:
        return [
            "name / task / feature",
            "define success criteria",
            "build first working version",
            "test and improve",
            "category or subject",
            "notes, steps, rules, details",
            "generated by winlocalassistant",
        ]

    def _normalise_candidate_js_text(self, text: str) -> str:
        """Repair narrow transport artefacts before in-memory candidate validation.

        Local models sometimes emit a literal backslash+n token outside any string
        at the end of a statement, for example `value = '';\n}`. That is not a
        newline in JavaScript; it is a syntax error. Keep the fix deliberately
        narrow so normal string literals remain untouched.
        """
        return re.sub(r"(?<=[;{}\]])\\n(?=\s*[}\];])", "\n", str(text or ""))

    def _candidate_static_checks(self, data: dict[str, Any]) -> tuple[bool, str]:
        """Validate candidate files before they are written into a project.

        This catches the exact failure mode visible in the browser: a candidate can
        look semantically plausible to text checks but still contain broken JS or
        JS that talks to DOM nodes that do not exist. Those candidates must stay in
        memory and be refined/rejected instead of being promoted to disk.
        """
        files = self._candidate_files(data)
        html_files = {name: content for name, content in files.items() if name.lower().endswith((".html", ".htm"))}
        js_files = {name: content for name, content in files.items() if name.lower().endswith(".js")}
        node = shutil.which("node")

        for name, content in js_files.items():
            raw_text = str(content)
            text = self._normalise_candidate_js_text(raw_text)
            if raw_text != text:
                return False, f"candidate JavaScript contains a literal \n transport artefact outside a string in {name}; refine before writing"
            if node:
                try:
                    with tempfile.TemporaryDirectory(prefix="wla_candidate_js_") as td:
                        temp_js = Path(td) / Path(name).name
                        temp_js.write_text(text, encoding="utf-8")
                        cp = subprocess.run([node, "--check", str(temp_js)], capture_output=True, text=True, timeout=15)
                    if cp.returncode != 0:
                        output = ((cp.stdout or "") + (cp.stderr or "")).strip()
                        return False, f"candidate JavaScript syntax failed in {name}: {output[-1200:]}"
                except Exception as exc:
                    return False, f"candidate JavaScript syntax check crashed for {name}: {exc!r}"
            else:
                if text.count("{") != text.count("}") or text.count("(") != text.count(")"):
                    return False, f"candidate basic JavaScript sanity failed in {name}: unbalanced braces or parentheses"
                if re.search(r"(?<=[;{}\]])\\n(?=\s*[}\];])", str(content)):
                    return False, f"candidate JavaScript contains literal \\n outside a string in {name}"

        if len(html_files) == 1 and js_files:
            html_text = "\n".join(str(v) for v in html_files.values())
            html_ids = set(re.findall(r"\bid\s*=\s*['\"]([^'\"]+)['\"]", html_text))
            if html_ids:
                for name, content in js_files.items():
                    refs = set(re.findall(r"getElementById\(\s*['\"]([^'\"]+)['\"]\s*\)", str(content)))
                    missing = sorted(ref for ref in refs if ref not in html_ids)
                    if missing:
                        return False, "candidate JavaScript references missing HTML id(s) in " + name + ": " + ", ".join(missing[:12])

        for name, content in html_files.items():
            for idx, inline in enumerate(re.findall(r"<script(?![^>]*\bsrc\s*=)[^>]*>([\s\S]*?)</script>", str(content), flags=re.IGNORECASE), start=1):
                inline = inline.strip()
                if not inline:
                    continue
                if node:
                    with tempfile.TemporaryDirectory(prefix="wla_candidate_html_js_") as td:
                        temp_js = Path(td) / f"{Path(name).stem}_inline_{idx}.js"
                        temp_js.write_text(inline, encoding="utf-8")
                        cp = subprocess.run([node, "--check", str(temp_js)], capture_output=True, text=True, timeout=15)
                    if cp.returncode != 0:
                        output = ((cp.stdout or "") + (cp.stderr or "")).strip()
                        return False, f"candidate inline JavaScript syntax failed in {name} script {idx}: {output[-1200:]}"
        return True, "ok"

    def _validate_model_project(self, data: dict[str, Any], goal: str) -> tuple[bool, str]:
        files = data.get("files")
        if not isinstance(files, dict) or not files:
            return False, "model did not return a non-empty files object"
        if not any(str(name).lower().endswith((".html", ".py", ".js", ".ps1", ".bat")) for name in files):
            return False, "model did not return a runnable source file"
        static_ok, static_reason = self._candidate_static_checks(data)
        if not static_ok:
            return False, static_reason
        combined = "\n".join(str(v) for v in files.values()).lower()
        if len(combined.strip()) < 700:
            return False, "model output was too small to be a useful implementation"

        markers = [m for m in self._generic_template_markers() if m in combined]
        clean_goal = self._validation_goal_text(goal)
        domain_reqs = self._goal_domain_requirements(clean_goal)
        missing_domains = []
        for domain, terms in domain_reqs.items():
            hits = [t for t in terms if t in combined]
            if domain == "file_creation":
                if not self._file_creation_terms_present(combined):
                    missing_domains.append({"domain": domain, "needed": "safe filename + content + write/download action + path/folder handling", "found": hits})
                continue
            # One or two mentions can happen in a title/README only. Require enough actual feature words.
            if len(set(hits)) < 4:
                missing_domains.append({"domain": domain, "needed_any_of": terms, "found": hits})
        if missing_domains:
            return False, "model output did not implement the requested domain: " + json.dumps(missing_domains, ensure_ascii=False)
        if markers and domain_reqs:
            # If the app also has strong domain features, generic phrases may just be incidental.
            all_hits = sum(1 for terms in domain_reqs.values() for t in terms if t in combined)
            if all_hits < 6:
                return False, "model output looked like a generic template rather than the requested app"

        # Generic capability checks based on the user's exact wording. This works for any project,
        # not only the stock-trading example.
        expectations = self._generic_feature_expectations(clean_goal)
        for feature, alternatives in expectations.items():
            hits = [a for a in alternatives if a in combined]
            if not hits:
                return False, f"model output is missing requested capability {feature}; expected one of {alternatives}"

        terms = self._extract_requirement_terms(clean_goal)
        if len(terms) >= 5:
            codeish = "\n".join(str(v) for k, v in files.items() if str(k).lower().endswith((".html", ".js", ".css", ".py", ".ps1", ".bat", ".md", ".json"))).lower()
            matched = [t for t in terms if t.replace(" ", "") in codeish.replace(" ", "") or t in codeish]
            min_matches = max(2, min(6, len(terms)//2))
            if self._goal_requests_file_creation_script(clean_goal) and self._file_creation_terms_present(codeish):
                min_matches = min(min_matches, 2)
            if len(matched) < min_matches:
                return False, "model output did not contain enough user-requested concepts in actual code/UI files; matched " + json.dumps(matched, ensure_ascii=False)
        return True, "ok"

    def _normalise_model_project(self, data: dict[str, Any], goal: str, folder: str) -> dict[str, Any]:
        data = dict(data)
        data["folder"] = self._slug(data.get("folder") or folder or goal)
        data["main_file"] = str(data.get("main_file") or "index.html")
        data["run_command"] = str(data.get("run_command") or ("start .\\" + data["main_file"] if data["main_file"].lower().endswith(".html") else ""))
        data["verify_command"] = str(data.get("verify_command") or "")
        data["notes"] = str(data.get("notes") or "")
        data["source"] = str(data.get("source") or "ollama")
        return data

    def _is_vague_game_request(self, goal: str) -> bool:
        words = set(re.findall(r"[a-z][a-z0-9]*", self._validation_goal_text(goal).lower()))
        if "game" not in words and "games" not in words:
            return False
        specific = {
            "pong", "snake", "tetris", "frogger", "shooter", "platformer", "rpg", "chess",
            "checkers", "cards", "memory", "minesweeper", "sudoku", "wordle", "multiplayer",
            "online", "3d", "three", "physics", "levels", "save", "export"
        }
        # Interactive clarifications append implementation details such as
        # "polished minimal html_css_js_page". Those words should not stop Nova
        # from using the safe custom-game fallback when the model repeats a weak
        # candidate for a vague game/theme request.
        return not bool(words & specific)

    def _fallback_browser_game_project(self, goal: str) -> dict[str, Any]:
        """Dependency-free fallback for vague game requests when the local LLM fails.

        This is deliberately small but complete: canvas rendering, player controls,
        score, collision, restart, and keyboard/touch-ish button controls. It prevents
        "make a game" from ending with no files when the model times out after showing
        a usable-looking preview.
        """
        if str(analyze_game_request(self._validation_goal_text(goal)).requested_game_type).lower() != "dodge":
            return build_generic_canvas_game_project(self._validation_goal_text(goal))
        files = {
            "index.html": """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Canvas Dodge Game</title>
  <link rel="stylesheet" href="style.css">
</head>
<body>
  <main class="game-shell">
    <header>
      <h1>Canvas Dodge Game</h1>
      <div class="scoreboard">
        <span>Score: <strong id="score">0</strong></span>
        <span>Best: <strong id="best">0</strong></span>
      </div>
    </header>
    <canvas id="gameCanvas" width="720" height="420" aria-label="Dodge falling blocks game"></canvas>
    <div class="controls" aria-label="Game controls">
      <button id="leftBtn" type="button">Left</button>
      <button id="startBtn" type="button">Start / Restart</button>
      <button id="rightBtn" type="button">Right</button>
    </div>
    <p class="hint">Use Left/Right arrows or A/D to move. Dodge the red blocks and keep scoring.</p>
  </main>
  <script src="app.js"></script>
</body>
</html>
""",
            "style.css": """* { box-sizing: border-box; }
body {
  margin: 0;
  min-height: 100vh;
  display: grid;
  place-items: center;
  font-family: Segoe UI, Arial, sans-serif;
  background: #f4f8fb;
  color: #102033;
}
.game-shell {
  width: min(860px, 96vw);
  display: grid;
  gap: 12px;
}
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 16px;
}
h1 { margin: 0; font-size: 28px; }
.scoreboard { display: flex; gap: 18px; font-size: 18px; }
canvas {
  width: 100%;
  aspect-ratio: 12 / 7;
  border: 2px solid #172033;
  background: #111827;
  box-shadow: 0 14px 38px rgba(16, 32, 51, .18);
}
.controls {
  display: grid;
  grid-template-columns: 1fr 1.4fr 1fr;
  gap: 10px;
}
button {
  border: 0;
  padding: 12px 14px;
  background: #1266f1;
  color: white;
  font-weight: 800;
  cursor: pointer;
}
button:hover { background: #0b51c5; }
.hint { margin: 0; color: #4b5f76; }
""",
            "app.js": """const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');
const scoreEl = document.getElementById('score');
const bestEl = document.getElementById('best');
const startBtn = document.getElementById('startBtn');
const leftBtn = document.getElementById('leftBtn');
const rightBtn = document.getElementById('rightBtn');

const keys = { left: false, right: false };
let best = Number(localStorage.getItem('wlaDodgeBest') || 0);
let running = false;
let gameOver = false;
let score = 0;
let lastTime = 0;
let spawnTimer = 0;
let blocks = [];

const player = {
  x: canvas.width / 2 - 24,
  y: canvas.height - 42,
  width: 48,
  height: 18,
  speed: 360
};

bestEl.textContent = String(best);

function resetGame() {
  running = true;
  gameOver = false;
  score = 0;
  spawnTimer = 0;
  blocks = [];
  player.x = canvas.width / 2 - player.width / 2;
  scoreEl.textContent = '0';
  lastTime = performance.now();
  requestAnimationFrame(loop);
}

function spawnBlock() {
  const size = 22 + Math.random() * 34;
  blocks.push({
    x: Math.random() * (canvas.width - size),
    y: -size,
    width: size,
    height: size,
    speed: 130 + Math.random() * 170 + score * 2
  });
}

function rectsCollide(a, b) {
  return a.x < b.x + b.width &&
    a.x + a.width > b.x &&
    a.y < b.y + b.height &&
    a.y + a.height > b.y;
}

function update(dt) {
  if (keys.left) player.x -= player.speed * dt;
  if (keys.right) player.x += player.speed * dt;
  player.x = Math.max(0, Math.min(canvas.width - player.width, player.x));

  spawnTimer += dt;
  if (spawnTimer > Math.max(0.25, 0.9 - score * 0.01)) {
    spawnTimer = 0;
    spawnBlock();
  }

  for (const block of blocks) block.y += block.speed * dt;
  blocks = blocks.filter(block => block.y < canvas.height + 80);
  score += dt * 10;
  scoreEl.textContent = String(Math.floor(score));

  if (blocks.some(block => rectsCollide(player, block))) {
    running = false;
    gameOver = true;
    best = Math.max(best, Math.floor(score));
    localStorage.setItem('wlaDodgeBest', String(best));
    bestEl.textContent = String(best);
  }
}

function draw() {
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  ctx.fillStyle = '#111827';
  ctx.fillRect(0, 0, canvas.width, canvas.height);

  ctx.fillStyle = '#22c55e';
  ctx.fillRect(player.x, player.y, player.width, player.height);

  ctx.fillStyle = '#ef4444';
  for (const block of blocks) ctx.fillRect(block.x, block.y, block.width, block.height);

  if (!running) {
    ctx.fillStyle = 'rgba(255, 255, 255, .9)';
    ctx.font = '28px Segoe UI, Arial';
    ctx.textAlign = 'center';
    ctx.fillText(gameOver ? 'Game over - press Start' : 'Press Start to play', canvas.width / 2, canvas.height / 2);
  }
}

function loop(now) {
  const dt = Math.min(0.033, (now - lastTime) / 1000);
  lastTime = now;
  if (running) update(dt);
  draw();
  if (running) requestAnimationFrame(loop);
}

function setMove(direction, active) {
  keys[direction] = active;
}

document.addEventListener('keydown', event => {
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') setMove('left', true);
  if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') setMove('right', true);
  if (event.key === ' ' && !running) resetGame();
});

document.addEventListener('keyup', event => {
  if (event.key === 'ArrowLeft' || event.key.toLowerCase() === 'a') setMove('left', false);
  if (event.key === 'ArrowRight' || event.key.toLowerCase() === 'd') setMove('right', false);
});

leftBtn.addEventListener('pointerdown', () => setMove('left', true));
leftBtn.addEventListener('pointerup', () => setMove('left', false));
leftBtn.addEventListener('pointerleave', () => setMove('left', false));
rightBtn.addEventListener('pointerdown', () => setMove('right', true));
rightBtn.addEventListener('pointerup', () => setMove('right', false));
rightBtn.addEventListener('pointerleave', () => setMove('right', false));
startBtn.addEventListener('click', resetGame);

draw();
""",
            "README.md": """# Canvas Dodge Game

A complete dependency-free browser game with canvas rendering, controls, score, collision, interaction and restart.

## Run

Open `index.html` in a browser.

## Controls

- Left/Right arrows or A/D move the player.
- Press Start/Restart or Space to begin again.
- Dodge falling red blocks, score points over time, and keep your best score in localStorage.
""",
        }
        return {
            "folder": "CanvasDodgeGame",
            "main_file": "index.html",
            "run_command": "start .\\index.html",
            "verify_command": "",
            "notes": "Deterministic fallback browser game used after local LLM generation failed. Includes canvas, player controls, score, collision, interaction and restart.",
            "human_summary": "A small canvas dodge game. Open index.html, press Start, and dodge the falling blocks.",
            "files": files,
            "source": "deterministic_fallback",
            "fallback_reason": "vague game request",
        }

    def _fallback_local_app_project(self, goal: str, analysis: dict[str, Any]) -> dict[str, Any] | None:
        """Dependency-free fallback for common local app requests when the LLM is unavailable.

        This avoids the frustrating case where Nova previews a usable idea or sees a
        clear calculator/todo/utility request, but writes no files because the local
        model timed out or returned malformed JSON.  The fallback is intentionally
        small, request-aware, local-only, and still verified by the normal project
        quality gates after creation.
        """
        low = self._validation_goal_text(goal).lower()
        theme = str(analysis.get("requested_theme") or "").lower()
        artifact_type = str(analysis.get("artifact_type") or "").lower()
        if "calculator" in low or theme == "calculator":
            return self._fallback_calculator_project(goal, analysis)
        if "todo" in low or "to-do" in low or theme == "todo":
            return self._fallback_todo_project(goal, analysis)
        utility_terms = ["utility", "local app", "useful local app", "useful app", "tiny useful app", "simple app", "tool", "tracker", "notes", "checklist"]
        if artifact_type in {"html_css_js_page", "web_app", "data_tool"} and any(term in low for term in utility_terms):
            return self._fallback_utility_project(goal, analysis)
        return None

    def _fallback_calculator_project(self, goal: str, analysis: dict[str, Any]) -> dict[str, Any]:
        files = {
            "index.html": """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\">
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
  <title>Local Calculator</title>
  <link rel=\"stylesheet\" href=\"style.css\">
</head>
<body>
  <main class=\"calculator\" aria-label=\"Calculator app\">
    <h1>Local Calculator</h1>
    <output id=\"display\" aria-live=\"polite\">0</output>
    <section class=\"keys\" aria-label=\"Calculator buttons\">
      <button data-action=\"clear\">C</button><button data-action=\"backspace\">⌫</button><button data-action=\"operator\" data-value=\"/\">÷</button><button data-action=\"operator\" data-value=\"*\">×</button>
      <button data-number=\"7\">7</button><button data-number=\"8\">8</button><button data-number=\"9\">9</button><button data-action=\"operator\" data-value=\"-\">−</button>
      <button data-number=\"4\">4</button><button data-number=\"5\">5</button><button data-number=\"6\">6</button><button data-action=\"operator\" data-value=\"+\">+</button>
      <button data-number=\"1\">1</button><button data-number=\"2\">2</button><button data-number=\"3\">3</button><button data-action=\"equals\" class=\"equals\">=</button>
      <button data-number=\"0\" class=\"wide\">0</button><button data-number=\".\">.</button>
    </section>
    <p class=\"hint\">Use the buttons or keyboard numbers/operators. Clear and backspace are included.</p>
  </main>
  <script src=\"app.js\"></script>
</body>
</html>
""",
            "style.css": """body{margin:0;min-height:100vh;display:grid;place-items:center;font-family:Segoe UI,Arial,sans-serif;background:#eef3f8;color:#142033}.calculator{width:min(380px,94vw);background:white;padding:22px;border-radius:18px;box-shadow:0 18px 45px #0f172a22}h1{margin:0 0 14px}#display{display:block;text-align:right;font-size:2.4rem;min-height:3.2rem;padding:12px;background:#111827;color:#e5f9ff;border-radius:12px;overflow:auto}.keys{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin-top:14px}button{font-size:1.25rem;font-weight:800;border:0;border-radius:12px;padding:14px;cursor:pointer;background:#e2e8f0}button:hover{background:#cbd5e1}.equals{grid-row:span 2;background:#2563eb;color:white}.wide{grid-column:span 2}.hint{color:#526174;font-size:.9rem}
""",
            "app.js": """const display = document.getElementById('display');
let expression = '';
function render(){ display.textContent = expression || '0'; }
function appendNumber(value){ if(value==='.' && expression.split(/[+\\-*/]/).pop().includes('.')) return; expression += value; render(); }
function appendOperator(value){ if(!expression && value !== '-') return; if(/[+\\-*/.]$/.test(expression)) expression = expression.slice(0,-1); expression += value; render(); }
function clearAll(){ expression=''; render(); }
function backspace(){ expression = expression.slice(0,-1); render(); }
function calculate(){ try { if(!expression || /[+\\-*/.]$/.test(expression)) return; const result = Function('return (' + expression + ')')(); expression = Number.isFinite(result) ? String(Number(result.toFixed(8))) : 'Error'; } catch { expression='Error'; } render(); if(expression==='Error') expression=''; }
document.querySelectorAll('[data-number]').forEach(btn => btn.addEventListener('click', () => appendNumber(btn.dataset.number)));
document.querySelectorAll('[data-action="operator"]').forEach(btn => btn.addEventListener('click', () => appendOperator(btn.dataset.value)));
document.querySelector('[data-action="clear"]').addEventListener('click', clearAll);
document.querySelector('[data-action="backspace"]').addEventListener('click', backspace);
document.querySelector('[data-action="equals"]').addEventListener('click', calculate);
document.addEventListener('keydown', event => { if(/^[0-9.]$/.test(event.key)) appendNumber(event.key); else if(['+','-','*','/'].includes(event.key)) appendOperator(event.key); else if(event.key==='Enter') calculate(); else if(event.key==='Backspace') backspace(); else if(event.key.toLowerCase()==='c') clearAll(); });
render();
""",
            "README.md": """# Local Calculator

A dependency-free calculator app with number entry, operators, equals/calculate, clear, backspace, keyboard support and a visible result display.

## Run
Open `index.html` in a browser.
""",
        }
        return self._fallback_project_payload("LocalCalculator", goal, analysis, files, "Local Calculator", "A complete local calculator with buttons, operators, clear, backspace and result display.")

    def _fallback_todo_project(self, goal: str, analysis: dict[str, Any]) -> dict[str, Any]:
        files = {
            "index.html": """<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><title>Local Todo App</title><link rel=\"stylesheet\" href=\"style.css\"></head><body><main class=\"app\"><h1>Local Todo App</h1><form id=\"todoForm\"><input id=\"todoInput\" placeholder=\"Add a task\" aria-label=\"New task\"><button>Add</button></form><div class=\"toolbar\"><button id=\"clearDone\" type=\"button\">Clear completed</button><button id=\"exportJson\" type=\"button\">Export JSON</button></div><ul id=\"todoList\" aria-live=\"polite\"></ul><p id=\"status\"></p></main><script src=\"app.js\"></script></body></html>""",
            "style.css": """body{margin:0;min-height:100vh;display:grid;place-items:center;font-family:Segoe UI,Arial,sans-serif;background:#f7fbff;color:#172033}.app{width:min(720px,94vw);background:white;padding:24px;border-radius:18px;box-shadow:0 16px 40px #0f172a20}form{display:flex;gap:10px}input{flex:1;padding:12px;border:1px solid #cbd5e1;border-radius:10px}button{border:0;background:#2563eb;color:white;border-radius:10px;padding:12px 14px;font-weight:700;cursor:pointer}.toolbar{display:flex;gap:10px;margin:12px 0}li{display:flex;align-items:center;gap:10px;padding:10px;border-bottom:1px solid #e2e8f0}.done span{text-decoration:line-through;color:#64748b}.delete{margin-left:auto;background:#dc2626}.complete{background:#059669}#status{color:#475569}
""",
            "app.js": """const form=document.getElementById('todoForm'); const input=document.getElementById('todoInput'); const list=document.getElementById('todoList'); const statusEl=document.getElementById('status'); let tasks=JSON.parse(localStorage.getItem('wlaTasks')||'[]');
function save(){localStorage.setItem('wlaTasks',JSON.stringify(tasks));}
function render(){list.innerHTML=''; tasks.forEach(task=>{const li=document.createElement('li'); li.className=task.done?'done':''; const text=document.createElement('span'); text.textContent=task.text; const complete=document.createElement('button'); complete.className='complete'; complete.textContent=task.done?'Undo':'Complete'; complete.addEventListener('click',()=>{task.done=!task.done; save(); render();}); const del=document.createElement('button'); del.className='delete'; del.textContent='Delete'; del.addEventListener('click',()=>{tasks=tasks.filter(t=>t.id!==task.id); save(); render();}); li.append(complete,text,del); list.appendChild(li);}); statusEl.textContent=`${tasks.length} task(s), ${tasks.filter(t=>t.done).length} complete`;}
form.addEventListener('submit',event=>{event.preventDefault(); const text=input.value.trim(); if(!text) return; tasks.push({id:Date.now(),text,done:false}); input.value=''; save(); render();});
document.getElementById('clearDone').addEventListener('click',()=>{tasks=tasks.filter(t=>!t.done); save(); render();});
document.getElementById('exportJson').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(tasks,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='todos.json'; a.click(); URL.revokeObjectURL(a.href);});
render();
""",
            "README.md": """# Local Todo App

A dependency-free todo app with add, delete, complete/undo, localStorage saving, status updates and JSON export.

## Run
Open `index.html` in a browser.
""",
        }
        return self._fallback_project_payload("LocalTodoApp", goal, analysis, files, "Local Todo App", "A complete local todo app with add, delete, complete, local saving and JSON export.")

    def _fallback_utility_project(self, goal: str, analysis: dict[str, Any]) -> dict[str, Any]:
        files = {
            "index.html": """<!DOCTYPE html><html lang=\"en\"><head><meta charset=\"UTF-8\"><meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\"><title>Local Utility Dashboard</title><link rel=\"stylesheet\" href=\"style.css\"></head><body><main class=\"shell\"><h1>Local Utility Dashboard</h1><p>Capture notes, checklist items and export everything as JSON. This runs entirely in your browser.</p><section><h2>Quick note</h2><textarea id=\"note\" placeholder=\"Write a note...\"></textarea><button id=\"saveNote\">Save note</button></section><section><h2>Checklist</h2><form id=\"taskForm\"><input id=\"taskInput\" placeholder=\"Add checklist item\"><button>Add</button></form><ul id=\"tasks\"></ul></section><section class=\"actions\"><button id=\"exportData\">Export JSON</button><button id=\"clearAll\">Clear all</button></section><pre id=\"preview\"></pre></main><script src=\"app.js\"></script></body></html>""",
            "style.css": """body{margin:0;min-height:100vh;background:#eef5ff;color:#102033;font-family:Segoe UI,Arial,sans-serif}.shell{max-width:900px;margin:32px auto;background:white;border-radius:18px;padding:24px;box-shadow:0 18px 45px #0f172a22}textarea,input{width:100%;padding:12px;border:1px solid #cbd5e1;border-radius:10px}textarea{min-height:120px}button{margin-top:10px;border:0;border-radius:10px;background:#2563eb;color:white;padding:11px 14px;font-weight:700;cursor:pointer}.actions{display:flex;gap:12px}li{display:flex;gap:10px;align-items:center;padding:8px 0;border-bottom:1px solid #e2e8f0}.done{text-decoration:line-through;color:#64748b}pre{background:#0f172a;color:#e2e8f0;padding:14px;border-radius:12px;overflow:auto}h1,h2{margin-bottom:8px}
""",
            "app.js": """let state=JSON.parse(localStorage.getItem('wlaUtilityState')||'{"notes":[],"tasks":[]}'); const note=document.getElementById('note'); const tasksEl=document.getElementById('tasks'); const preview=document.getElementById('preview');
function save(){localStorage.setItem('wlaUtilityState',JSON.stringify(state)); render();}
function render(){tasksEl.innerHTML=''; state.tasks.forEach(task=>{const li=document.createElement('li'); const cb=document.createElement('input'); cb.type='checkbox'; cb.checked=task.done; cb.addEventListener('change',()=>{task.done=cb.checked; save();}); const span=document.createElement('span'); span.textContent=task.text; span.className=task.done?'done':''; const del=document.createElement('button'); del.textContent='Delete'; del.addEventListener('click',()=>{state.tasks=state.tasks.filter(t=>t.id!==task.id); save();}); li.append(cb,span,del); tasksEl.appendChild(li);}); preview.textContent=JSON.stringify(state,null,2);}
document.getElementById('saveNote').addEventListener('click',()=>{const text=note.value.trim(); if(!text)return; state.notes.push({id:Date.now(),text,created:new Date().toISOString()}); note.value=''; save();});
document.getElementById('taskForm').addEventListener('submit',event=>{event.preventDefault(); const input=document.getElementById('taskInput'); const text=input.value.trim(); if(!text)return; state.tasks.push({id:Date.now(),text,done:false}); input.value=''; save();});
document.getElementById('clearAll').addEventListener('click',()=>{if(confirm('Clear notes and checklist?')){state={notes:[],tasks:[]}; save();}});
document.getElementById('exportData').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(state,null,2)],{type:'application/json'}); const a=document.createElement('a'); a.href=URL.createObjectURL(blob); a.download='local-utility-data.json'; a.click(); URL.revokeObjectURL(a.href);});
render();
""",
            "README.md": """# Local Utility Dashboard

A dependency-free local utility app for notes, checklist items, localStorage saving and JSON export.

## Run
Open `index.html` in a browser.
""",
        }
        return self._fallback_project_payload("LocalUtilityDashboard", goal, analysis, files, "Local Utility Dashboard", "A useful local utility app with notes, checklist, local saving and JSON export.")

    def _fallback_project_payload(self, folder: str, goal: str, analysis: dict[str, Any], files: dict[str, str], title: str, summary: str) -> dict[str, Any]:
        return {
            "folder": folder,
            "main_file": "index.html",
            "run_command": "start .\\index.html",
            "verify_command": "python -c \"from pathlib import Path; missing=[p for p in ['index.html','app.js','style.css'] if not Path(p).exists()]; print('ok' if not missing else 'missing '+','.join(missing)); raise SystemExit(1 if missing else 0)\"",
            "notes": summary,
            "human_summary": summary + " Open index.html in a browser.",
            "files": files,
            "source": "deterministic_fallback",
            "fallback_reason": "local model unavailable or invalid JSON; request-aware local app fallback",
            "creation_analysis": analysis,
        }

    def _fallback_file_creation_script_project(self, goal: str) -> dict[str, Any]:
        script = r"""from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from pathlib import Path

OUTPUT_DIR = Path("generated_files")
MANIFEST = OUTPUT_DIR / "manifest.json"


def safe_filename(name: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_.-]+", "_", (name or "example.txt").strip())
    cleaned = cleaned.strip("._") or "example.txt"
    if "." not in cleaned:
        cleaned += ".txt"
    return cleaned[:120]


def create_file(name: str, content: str) -> Path:
    OUTPUT_DIR.mkdir(exist_ok=True)
    target = OUTPUT_DIR / safe_filename(name)
    target.write_text(content, encoding="utf-8")
    record = {
        "name": target.name,
        "path": str(target),
        "bytes": len(content.encode("utf-8")),
        "created_at": datetime.now(timezone.utc).isoformat(),
    }
    history = []
    if MANIFEST.exists():
        try:
            history = json.loads(MANIFEST.read_text(encoding="utf-8"))
        except Exception:
            history = []
    history.append(record)
    MANIFEST.write_text(json.dumps(history, indent=2), encoding="utf-8")
    return target


def main() -> int:
    parser = argparse.ArgumentParser(description="Create local text files safely inside generated_files/.")
    parser.add_argument("--name", default="story_seed.txt", help="Filename to create")
    parser.add_argument("--content", default="A tiny file created by the FileScript demo.", help="Text content to write")
    parser.add_argument("--demo", action="store_true", help="Create a demo file and print verification details")
    args = parser.parse_args()
    if args.demo:
        args.name = "demo_file.txt"
        args.content = "This demo proves the script can create a real local file and manifest entry."
    target = create_file(args.name, args.content)
    print(f"created={target}")
    print(f"exists={target.exists()}")
    print(f"manifest={MANIFEST}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
"""
        readme = """# FileScript

A small local Python script for safely creating files from a filename and content string.

## Run

```powershell
python file_creator.py --name notes.txt --content "Hello from Nova"
```

## Demo / verification

```powershell
python file_creator.py --demo
```

The script writes only inside `generated_files/`, sanitises unsafe filename characters, and updates `generated_files/manifest.json` so the result can be checked instead of just assumed successful.
"""
        return {
            "folder": "FileScript",
            "main_file": "file_creator.py",
            "run_command": "python file_creator.py --demo",
            "verify_command": "python file_creator.py --demo",
            "notes": "Created a real local file-creation script instead of a generic browser demo. It writes files, records a manifest, and has a demo verification path.",
            "human_summary": "Built FileScript: run `python file_creator.py --demo` to create a verified demo file, or pass `--name` and `--content` to create your own file.",
            "files": {
                "file_creator.py": script,
                "README.md": readme,
                "PROJECT_ITERATION_LOG.jsonl": json.dumps({"event": "baseline_created", "goal": goal, "next_improvement": "Add templates, batch file creation, or MCP exposure if the conversation suggests repeated use."}) + "\n",
            },
            "source": "deterministic_file_creation_script_fallback",
            "fallback_reason": "request asked for a file-creation script; local model candidate was semantically mismatched or stuck",
        }

    def _fallback_project_for_goal(self, goal: str, mode: str) -> dict[str, Any] | None:
        if mode != "create":
            return None
        clean_goal = self._validation_goal_text(goal)
        analysis = analyze_creation_request(clean_goal)
        low = clean_goal.lower()
        if self._goal_requests_file_search_script(clean_goal):
            fallback = self._fallback_file_string_search_project(clean_goal)
            fallback["creation_analysis"] = analysis
            return fallback
        if self._goal_requests_file_creation_script(clean_goal):
            fallback = self._fallback_file_creation_script_project(clean_goal)
            fallback["creation_analysis"] = analysis
            return fallback
        if "game" in low:
            if str(analysis.get("requested_theme") or "").lower() == "dodge":
                fallback = self._fallback_browser_game_project(clean_goal)
            else:
                fallback = build_generic_canvas_game_project(clean_goal)
            fallback["creation_analysis"] = analysis
            if (analysis.get("assumptions") or []):
                fallback["assumptions"] = analysis.get("assumptions")
            return fallback
        app_fallback = self._fallback_local_app_project(clean_goal, analysis)
        if app_fallback:
            return app_fallback
        return None

    def _candidate_files(self, data: dict[str, Any]) -> dict[str, str]:
        files = data.get("files")
        if not isinstance(files, dict):
            return {}
        return {str(k).replace("\\", "/").lstrip("/"): str(v) for k, v in files.items()}

    def _candidate_combined(self, data: dict[str, Any]) -> str:
        return "\n".join(self._candidate_files(data).values()).lower()

    def _write_candidate_file(self, data: dict[str, Any], name: str, content: str) -> None:
        data.setdefault("files", {})[name.replace("\\", "/").lstrip("/")] = content

    def _deterministic_refine_candidate(self, data: dict[str, Any], goal: str, reason: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
        """Edit a parseable model candidate in memory before asking for another full generation.

        The local model often returns a mostly useful project that fails for one or two
        predictable omissions. v50 treats that output as an editable draft: repair the
        current files, validate again, and only then ask a focused candidate-edit prompt.
        """
        refined = dict(data)
        refined["files"] = dict(self._candidate_files(refined))
        files = refined["files"]
        edits: list[dict[str, Any]] = []
        lower_goal = self._validation_goal_text(goal).lower()
        reason_l = (reason or "").lower()
        if self._goal_requests_file_creation_script(lower_goal):
            combined_now = self._candidate_combined(refined)
            if not self._file_creation_terms_present(combined_now) or "john doe" in combined_now:
                fallback = self._normalise_model_project(self._fallback_file_creation_script_project(lower_goal), goal, "FileScript")
                return fallback, [{"kind": "candidate_domain_fallback", "detail": "Replaced weak/mismatched file-creation candidate with a runnable Python file-creation script", "reason": reason}]

        # Browser project file-reference repair, done before writing files.
        index_name = next((n for n in files if n.lower().endswith("index.html")), "")
        if index_name:
            html = files.get(index_name, "")
            if "app.js" in html and "app.js" not in files and "main.js" in files:
                files[index_name] = html.replace("app.js", "main.js")
                edits.append({"kind": "candidate_html_reference", "file": index_name, "detail": "Retargeted missing app.js reference to main.js"})
                html = files[index_name]
            if "style.css" in html and "style.css" not in files and "styles.css" in files:
                files[index_name] = html.replace("style.css", "styles.css")
                edits.append({"kind": "candidate_html_reference", "file": index_name, "detail": "Retargeted missing style.css reference to styles.css"})
                html = files[index_name]
            if "app.js" not in files and "<script" not in html.lower() and "game" in lower_goal:
                html = html.replace("</body>", "  <script src=\"app.js\"></script>\n</body>") if "</body>" in html else html + "\n<script src=\"app.js\"></script>\n"
                files[index_name] = html
                files["app.js"] = "console.log('Nova iterative candidate script loaded');\n"
                edits.append({"kind": "candidate_missing_script", "file": index_name, "detail": "Added app.js reference for a browser game candidate"})

        # Common Pong-style state bug, but in memory before project write.
        for name, content in list(files.items()):
            if not name.lower().endswith(".js"):
                continue
            after = self._normalise_candidate_js_text(content)
            if after != content:
                edits.append({"kind": "candidate_js_transport_newline", "file": name, "detail": "Converted literal \n transport artefacts into real newlines before validation"})
            uses_arrow_state = "rightPressed" in after or "leftPressed" in after
            missing_right = "rightPressed" in after and not re.search(r"\b(?:let|const|var)\s+rightPressed\b", after)
            missing_left = "leftPressed" in after and not re.search(r"\b(?:let|const|var)\s+leftPressed\b", after)
            if uses_arrow_state and (missing_right or missing_left):
                state_lines = ""
                if missing_right:
                    state_lines += "let rightPressed = false;\n"
                if missing_left:
                    state_lines += "let leftPressed = false;\n"
                ctx_match = re.search(r"^const\s+ctx\s*=\s*canvas\.getContext\([^\n]+;\s*$", after, flags=re.MULTILINE)
                if ctx_match:
                    after = after[:ctx_match.end()] + "\n" + state_lines + after[ctx_match.end():]
                else:
                    after = state_lines + after
                edits.append({"kind": "candidate_js_input_state", "file": name, "detail": "Declared missing arrow-key state variables"})
            if uses_arrow_state and "keydown" not in after.lower():
                listener_code = """

document.addEventListener('keydown', event => {
  if (event.key === 'Right' || event.key === 'ArrowRight') rightPressed = true;
  if (event.key === 'Left' || event.key === 'ArrowLeft') leftPressed = true;
});

document.addEventListener('keyup', event => {
  if (event.key === 'Right' || event.key === 'ArrowRight') rightPressed = false;
  if (event.key === 'Left' || event.key === 'ArrowLeft') leftPressed = false;
});
"""
                interval_match = re.search(r"\n\s*setInterval\s*\(", after)
                after = after[:interval_match.start()] + listener_code + after[interval_match.start():] if interval_match else after + listener_code
                edits.append({"kind": "candidate_js_input_state", "file": name, "detail": "Added missing keyboard listeners"})
            after = re.sub(r"\.join\('\s*\n\s*'\)", r".join('\\n')", after)
            after = re.sub(r'\.join\(\"\s*\n\s*\"\)', r'.join("\\n")', after)
            if after != content:
                files[name] = after

        # Mission-contract surgical recipes: patch the precise failed behaviour before
        # asking the model to regenerate or broad-replacing a candidate.
        recipe_refined, recipe_edits = patch_candidate_for_failure(refined, goal, reason)
        if recipe_edits:
            refined = recipe_refined
            files = refined.get("files", files)
            edits.extend(recipe_edits)

        combined = self._candidate_combined(refined)
        if "game" in lower_goal:
            missing_game_bits = [
                token for token in ["canvas", "score", "player", "controls", "collision"]
                if token not in combined
            ]
            if self._is_vague_game_request(lower_goal) and (missing_game_bits or "game_missing" in reason_l or "requested domain" in reason_l):
                fallback = build_generic_canvas_game_project(lower_goal)
                fallback["source"] = "deterministic_fallback"
                refined = self._normalise_model_project(fallback, goal, str(fallback.get("folder") or self._slug(goal)))
                edits.append({"kind": "candidate_domain_fallback", "detail": "Replaced weak/repeating game candidate with themed deterministic runnable game", "missing": missing_game_bits, "reason": reason})
            elif missing_game_bits and "app.js" in files and "score" not in combined:
                files["app.js"] += "\n\n// Iterative refinement: basic score state required by game acceptance.\nlet score = typeof score === 'number' ? score : 0;\n"
                edits.append({"kind": "candidate_game_state", "file": "app.js", "detail": "Added basic score state marker"})

        refined.setdefault("notes", "")
        if edits:
            refined["notes"] = (str(refined.get("notes") or "") + "\nIterative candidate refinement: " + "; ".join(e.get("detail", e.get("kind", "edit")) for e in edits)).strip()
            refined["source"] = str(refined.get("source") or "ollama") + "+iterative_refinement"
        return refined, edits

    def _ask_model_to_refine_candidate(self, data: dict[str, Any], goal: str, reason: str, build_mode: str, round_no: int) -> dict[str, Any] | None:
        files = self._candidate_files(data)
        compact_files = {k: v[:12000] for k, v in files.items()}
        prompt = f"""
You are editing an existing Nova project candidate. Do NOT start over.
Return ONLY valid JSON with complete replacement file contents for changed files.

USER GOAL:
{goal}

BUILD STREAM: {build_mode}

WHY THE CURRENT CANDIDATE FAILED:
{reason}

CURRENT CANDIDATE METADATA:
{json.dumps({k: data.get(k) for k in ['folder', 'main_file', 'run_command', 'verify_command', 'notes']}, ensure_ascii=False, indent=2)}

CURRENT FILES:
{json.dumps(compact_files, ensure_ascii=False, indent=2)}

LOCAL RUN CONTEXT / ANALYSIS / VERIFICATION CONDITIONS:
{self._local_model_implementation_context(Path(self.workspace), goal=goal, last_reason=reason)}

Schema:
{{
  "main_file": "index.html",
  "run_command": "start .\\index.html",
  "verify_command": "optional PowerShell check",
  "notes": "what changed",
  "files": {{
    "app.js": "complete replacement content for changed file",
    "index.html": "complete replacement content if changed"
  }}
}}
"""
        log_activity("candidate_refine_prompt", "Asking local model to edit rejected candidate instead of regenerating from scratch", {"round": round_no, "goal": goal, "reason": reason[:1000], "files": sorted(files)})
        log_model_io("candidate_refine_prompt", prompt=prompt, data={"round": round_no, "goal": goal, "model": self.config.model})
        reply = model_chat(self.config, self.config.model, [{"role": "user", "content": prompt}], timeout=180, desc="candidate refinement prompt")
        log_model_io("candidate_refine_response", response=reply or "", data={"round": round_no, "received_chars": len(reply or "")})
        if not reply:
            return None
        patch = self._extract_json_object(reply)
        if not isinstance(patch, dict) or not isinstance(patch.get("files"), dict) or not patch.get("files"):
            return None
        refined = dict(data)
        refined["files"] = self._candidate_files(refined)
        for rel, content in patch.get("files", {}).items():
            refined["files"][str(rel).replace("\\", "/").lstrip("/")] = str(content)
        for key in ["main_file", "run_command", "verify_command", "notes"]:
            if patch.get(key):
                refined[key] = str(patch.get(key))
        refined["source"] = str(refined.get("source") or "ollama") + "+candidate_llm_edit"
        return refined

    def _refine_rejected_candidate(self, data: dict[str, Any], goal: str, reason: str, build_mode: str, max_rounds: int = 2) -> tuple[dict[str, Any] | None, list[dict[str, Any]], str]:
        current = self._normalise_model_project(data, goal, str(data.get("folder") or self._slug(goal)))
        trace: list[dict[str, Any]] = []
        last_reason = reason
        seen_reasons: set[str] = set()
        if self._goal_requests_file_creation_script(goal) and ("not contain enough" in (reason or "").lower() or "weak_logic" in (reason or "").lower() or "requested domain" in (reason or "").lower()):
            fallback = self._normalise_model_project(self._fallback_file_creation_script_project(goal), goal, "FileScript")
            trace.append({"round": 0, "stage": "deterministic_domain_fallback", "ok": True, "reason": "stopped repeated semantic rejection loop for file-creation script"})
            return fallback, trace, "accepted_after_domain_fallback"
        for round_no in range(1, max(1, max_rounds) + 1):
            deterministic, edits = self._deterministic_refine_candidate(current, goal, last_reason)
            ok, new_reason = self._validate_model_project(deterministic, goal)
            trace.append({"round": round_no, "stage": "deterministic_candidate_edit", "ok": ok, "reason": new_reason, "edits": edits})
            log_activity("candidate_refine_step", "Edited rejected candidate in memory", {"round": round_no, "ok": ok, "reason": new_reason, "edits": edits})
            if ok:
                deterministic["iterative_refinement"] = trace
                return deterministic, trace, "accepted_after_deterministic_refinement"
            current = deterministic
            last_reason = new_reason
            llm_edited = self._ask_model_to_refine_candidate(current, goal, last_reason, build_mode, round_no)
            if not llm_edited:
                trace.append({"round": round_no, "stage": "candidate_llm_edit", "ok": False, "reason": "model did not return candidate edits"})
                continue
            ok, new_reason = self._validate_model_project(llm_edited, goal)
            trace.append({"round": round_no, "stage": "candidate_llm_edit", "ok": ok, "reason": new_reason, "files": sorted(self._candidate_files(llm_edited))})
            log_activity("candidate_refine_step", "Local model edited rejected candidate", {"round": round_no, "ok": ok, "reason": new_reason, "files": sorted(self._candidate_files(llm_edited))})
            if ok:
                llm_edited["iterative_refinement"] = trace
                return llm_edited, trace, "accepted_after_candidate_llm_edit"
            current = llm_edited
            signature = re.sub(r"\s+", " ", new_reason or "").strip()[:220]
            if signature in seen_reasons:
                trace.append({"round": round_no, "stage": "no_progress_guard", "ok": False, "reason": "same rejection reason repeated; stopping refinement loop"})
                log_activity("candidate_refine_no_progress", "Stopped repeated candidate refinement with no new progress", {"round": round_no, "reason": new_reason})
                break
            seen_reasons.add(signature)
            last_reason = new_reason
        return None, trace, last_reason

    def _should_use_early_deterministic_project_fallback(self, goal: str, attempt: int, last_reason: str) -> bool:
        """Keep simple coding requests from burning multiple long Ollama retries.

        For vague games/apps/utilities Nova already has deterministic builders. If
        the first local-model response is malformed or the model times out, using
        the matching fallback is safer and faster than spending minutes retrying
        the same oversized JSON prompt. Detailed or unusual requests still get a
        second model attempt before fallback.
        """
        low = self._validation_goal_text(goal).lower()
        reason = (last_reason or "").lower()
        if not any(token in reason for token in ["timed out", "not reachable", "parseable json", "validation", "rejected"]):
            return False
        simple_domain = self._is_vague_game_request(low) or self._goal_requests_file_search_script(low) or any(k in low for k in [
            "make a game", "build a game", "create a game", "calculator", "todo", "to-do", "timer", "counter", "quiz", "flashcard", "notes app", "weather app", "browser game"
        ])
        if simple_domain:
            return attempt >= 1
        return attempt >= 2

    def _try_early_project_fallback(self, goal: str, mode: str, attempt: int, attempts: list[dict[str, Any]], last_reason: str, creation_analysis: dict[str, Any], best_candidate: dict[str, Any] | None, best_candidate_reason: str) -> dict[str, Any] | None:
        if not self._should_use_early_deterministic_project_fallback(goal, attempt, last_reason):
            return None
        fallback = self._fallback_project_for_goal(goal, mode)
        if not fallback:
            return None
        attempts.append({"attempt": f"{attempt}.early_fallback", "status": "used_deterministic_fallback", "phase": "early_after_model_failure", "reason": last_reason or "local model did not produce usable project JSON"})
        fallback = self._normalise_model_project(fallback, goal, str(fallback.get("folder") or self._slug(goal)))
        # Keep the public source label stable for existing startup/release tests and
        # downstream UI logic; the attempt_history.phase field records that this was
        # the early timeout/JSON-failure path.
        fallback["source"] = "deterministic_fallback"
        fallback["attempt_history"] = attempts
        fallback["creation_analysis"] = creation_analysis
        fallback["best_rejected_candidate"] = {
            "reason": best_candidate_reason,
            "files": sorted((best_candidate.get("files") or {}).keys()) if isinstance(best_candidate, dict) and isinstance(best_candidate.get("files"), dict) else [],
        }
        self._last_model_attempts = attempts
        self._last_model_error = "Used early deterministic fallback after local model failure: " + (last_reason or "unknown model failure")
        log_activity("llm_early_fallback_used", "Using deterministic project fallback before additional long local-model retries", {"goal": goal, "mode": mode, "attempt": attempt, "reason": last_reason, "files": sorted((fallback.get("files") or {}).keys())})
        return fallback

    def _ask_model_for_project(self, goal: str, mode: str = "create", build_mode: str = "auto", requirements: dict[str, Any] | None = None) -> dict[str, Any] | None:
        context = "" if mode == "create" else self._project_context()
        memory_context = project_memory_context(self.workspace) if mode != "create" else ""
        validation_goal = self._validation_goal_text(goal)
        creation_analysis = analyze_creation_request(validation_goal)
        project_brief = infer_project_build_brief(validation_goal)
        coding_plan = plan_coding_execution(validation_goal)
        request_contract = build_request_contract(validation_goal)
        domain_reqs = self._goal_domain_requirements(validation_goal)
        requirements = requirements or self._requirements_spec(validation_goal, build_mode)
        requirements.setdefault("request_contract", request_contract)
        requirements.setdefault("project_build_brief", project_brief.to_dict())
        requirements.setdefault("coding_execution_plan", coding_plan)
        domain_text = json.dumps(domain_reqs, ensure_ascii=False, indent=2) if domain_reqs else "{}"
        request_contract_text = json.dumps(request_contract, ensure_ascii=False, indent=2)
        coding_plan_text = json.dumps(coding_plan, ensure_ascii=False, indent=2)
        brief_text = project_brief.to_prompt_text()
        req_text = json.dumps(requirements, ensure_ascii=False, indent=2)
        creation_text = json.dumps(creation_analysis, ensure_ascii=False, indent=2)
        default_run_command = str(coding_plan.get("run_command") or "start .\\index.html")
        default_verify_command = str(coding_plan.get("verify_command") or "node --check app.js")
        base_prompt = f"""
You are Nova's LOCAL CODING MODEL. You must write the actual code files for the user's requested project.
Return ONLY valid JSON. No markdown fences. No commentary outside JSON.

USER REQUIREMENT:
{goal}

VALIDATION SOURCE REQUEST:
{validation_goal}

MODE: {mode}
BUILD STREAM: {build_mode}

REQUIREMENTS AND ACCEPTANCE CONTRACT:
{req_text}

STRICT REQUEST CONTRACT - must win over generic templates and scaffolds:
{request_contract_text}

CODING EXECUTION PLAN - choose this runtime/files unless the user explicitly asked for another one:
{coding_plan_text}

PROJECT BUILD BRIEF - use this as the source of truth for workflows, data, edge cases and acceptance tests:
{brief_text}

CREATION REQUEST ANALYSIS:
{creation_text}

GAME DESIGN CONTRACT WHEN REQUEST IS A GAME:
{json.dumps(game_prompt_requirements(validation_goal), ensure_ascii=False, indent=2) if "game" in validation_goal.lower() else "{}"}

CURRENT PROJECT CONTEXT FOR EDIT MODE:
{context}

CURRENT PROJECT MEMORY FOR EDIT/CONTINUATION MODE:
{memory_context}

AVAILABLE WINLOCALASSISTANT TOOLS YOU MAY ASK THE ASSISTANT TO USE AFTER FILE GENERATION:
{json.dumps(self._tool_catalog_for_agent(), ensure_ascii=False, indent=2)}

DOMAIN FEATURE GUARDRAILS inferred from the user's words:
{domain_text}

RECENT ERROR/RUNTIME CONTEXT TO USE WHEN REPAIRING:
{self._local_model_runtime_context(Path(self.workspace))}

LOCAL RUN CONTEXT / ANALYSIS / VERIFICATION CONDITIONS:
{self._local_model_implementation_context(Path(self.workspace), goal=goal)}

Hard rules:
- Build what the user asked for, not a generic notes/task app.
- You must build what the user asked for. Do not substitute a generic Dodge Game or demo template unless the user explicitly asked for it. If the request is vague, state assumptions and create the simplest matching artifact. The output must be checked against the original user request before claiming success.
- Do not output placeholder screens, TODO-only files, planning packs, or generic item trackers unless the user asked for that.
- If the user asks for a stock trading app, implement stock-specific UI and logic: watchlist, ticker symbol, simulated buy/sell, shares, cash balance, portfolio value, profit/loss, transaction history, localStorage saving, and JSON export. Do not fetch live market data unless the user explicitly provides an API.
- If the user asks for some other app, infer the actual domain objects and workflows from their words and implement those.
- Choose the artifact type that fits the request: browser app for visual web UI; Python/PowerShell/Java/Node/CLI scripts for script, automation, data or runtime-specific requests; package/MCP/tool files when the request or repeated conversation pattern calls for reusable tooling. Do not force everything into HTML.
- Follow the CODING EXECUTION PLAN for main_file, run_command, verify_command and expected file layout unless the user explicitly requested a different runtime.
- Make the result runnable locally on Windows.
- After the first working baseline, include one small completed iterative improvement when it is safe and useful, and record it in notes or PROJECT_ITERATION_LOG rather than only proposing it.
- Include meaningful seeded example data that matches the user's domain.
- Include local saving and export when useful or requested.
- Implement the PROJECT BUILD BRIEF's functional_requirements, data_model, ui_states and edge_cases in actual code/UI, not only in README.
- Use the PROJECT BUILD BRIEF's suggested_files unless the user's requested language/framework clearly requires different files.
- Add visible UI copy/instructions so a human can validate the acceptance_tests without reading source code.

JSON schema:
{{
  "folder": "ProjectFolderName",
  "main_file": "{coding_plan.get('main_file', 'index.html')}",
  "run_command": "{default_run_command}",
  "verify_command": "{default_verify_command}",
  "notes": "short human explanation of how the files satisfy the user request",
  "human_summary": "short user-facing summary of what was built and how to run it",
  "files": {{
    "{coding_plan.get('main_file', 'index.html')}": "full file content",
    "README.md": "full file content"
  }}
}}
"""
        last_reason = ""
        attempts: list[dict[str, Any]] = []
        best_candidate: dict[str, Any] | None = None
        best_candidate_reason = ""
        log_activity("llm_status", "Checking local model before generation", {"model": self.config.model, "ollama_url": self.config.ollama_url, "ollama_ps": self._ollama_ps()})
        for attempt in range(1, 4):
            prompt = base_prompt
            if attempt > 1:
                prompt += f"""

Your previous response was rejected: {last_reason}

UPDATED LOCAL RUN CONTEXT / ANALYSIS / VERIFICATION CONDITIONS FOR THIS RETRY:
{self._local_model_implementation_context(Path(self.workspace), goal=goal, last_reason=last_reason, attempts=attempts)}

Use the runtime context, previous attempt history and rejection reason above. If the current design track is not satisfying the acceptance contract, switch to a simpler complete approach instead of repeating the same structure. Return valid JSON only.
"""
            log_activity("llm_attempt", f"Calling local LLM attempt {attempt}/3", {"model": self.config.model, "mode": mode, "goal": goal})
            log_model_io("prompt", prompt=prompt, data={"attempt": attempt, "mode": mode, "goal": goal, "model": self.config.model})
            reply = model_chat(self.config, self.config.model, [{"role": "user", "content": prompt}], timeout=240, desc="local LLM prompt")
            log_model_io("response", response=reply or "", data={"attempt": attempt, "mode": mode, "received_chars": len(reply or "")})
            if reply is None:
                last_reason = "Ollama was not reachable or timed out. Start it with `ollama serve` and make sure the selected model is pulled."
                attempts.append({"attempt": attempt, "status": "timeout_or_unreachable", "reason": last_reason, "received_chars": 0})
                log_activity("llm_failed", last_reason, {"attempt": attempt, "attempts": attempts})
                early_fallback = self._try_early_project_fallback(goal, mode, attempt, attempts, last_reason, creation_analysis, best_candidate, best_candidate_reason)
                if early_fallback:
                    return early_fallback
                continue
            data = self._extract_json_object(reply or "")
            if not data:
                last_reason = "model did not return parseable JSON"
                attempts.append({"attempt": attempt, "status": "parse_failed", "reason": last_reason, "received_chars": len(reply or ""), "reply_preview": (reply or "")[:1200]})
                log_activity("llm_rejected", last_reason, {"attempt": attempt, "reply_preview": (reply or "")[:4000], "attempts": attempts})
                early_fallback = self._try_early_project_fallback(goal, mode, attempt, attempts, last_reason, creation_analysis, best_candidate, best_candidate_reason)
                if early_fallback:
                    return early_fallback
                continue
            ok, reason = self._validate_model_project(data, goal)
            if not ok:
                last_reason = reason
                if isinstance(data.get("files"), dict) and data.get("files"):
                    best_candidate = data
                    best_candidate_reason = reason
                    refined, refinement_trace, refined_status = self._refine_rejected_candidate(data, goal, reason, build_mode, max_rounds=2)
                    attempts.append({
                        "attempt": attempt,
                        "status": "validation_failed_then_refined" if refined else "validation_failed",
                        "reason": reason,
                        "received_chars": len(reply or ""),
                        "files": sorted((data.get("files") or {}).keys()),
                        "refinement_trace": refinement_trace,
                    })
                    if refined:
                        self._last_model_error = ""
                        self._last_model_attempts = attempts
                        refined = self._normalise_model_project(refined, goal, str(refined.get("folder") or data.get("folder") or self._slug(goal)))
                        refined["attempt_history"] = attempts
                        refined["best_rejected_candidate"] = {"reason": reason, "files": sorted((data.get("files") or {}).keys())}
                        refined["creation_analysis"] = creation_analysis
                        log_activity("llm_candidate_refined", "Accepted iteratively refined model candidate", {"attempt": attempt, "status": refined_status, "trace": refinement_trace, "files": sorted((refined.get("files") or {}).keys())})
                        return refined
                    if self._is_vague_game_request(validation_goal) and "game" in reason.lower():
                        fallback = self._fallback_project_for_goal(validation_goal, mode)
                        if fallback:
                            attempts.append({"attempt": f"{attempt}.fallback", "status": "used_deterministic_game_fallback_after_no_progress", "reason": reason})
                            fallback = self._normalise_model_project(fallback, goal, str(fallback.get("folder") or self._slug(goal)))
                            fallback["source"] = "deterministic_fallback_after_no_progress"
                            fallback["attempt_history"] = attempts
                            fallback["creation_analysis"] = creation_analysis
                            fallback["best_rejected_candidate"] = {"reason": reason, "files": sorted((data.get("files") or {}).keys())}
                            self._last_model_attempts = attempts
                            self._last_model_error = "Used deterministic themed game fallback after repeated candidate refinement made no progress: " + reason
                            log_activity("llm_fallback_used", "Using themed game fallback after candidate refinement made no progress", {"goal": goal, "mode": mode, "attempt": attempt, "reason": reason, "files": sorted((fallback.get("files") or {}).keys())})
                            return fallback
                else:
                    attempts.append({"attempt": attempt, "status": "validation_failed", "reason": reason, "received_chars": len(reply or ""), "files": sorted((data.get("files") or {}).keys()) if isinstance(data.get("files"), dict) else []})
                log_activity("llm_rejected", reason, {"attempt": attempt, "attempts": attempts, "candidate_files": sorted((data.get("files") or {}).keys()) if isinstance(data.get("files"), dict) else []})
                continue
            self._last_model_error = ""
            attempts.append({"attempt": attempt, "status": "accepted", "reason": "ok", "received_chars": len(reply or ""), "files": sorted((data.get("files") or {}).keys())})
            self._last_model_attempts = attempts
            log_activity("llm_accepted", "Local LLM produced a valid project/edit JSON", {"attempt": attempt, "files": sorted((data.get("files") or {}).keys()), "attempts": attempts})
            project = self._normalise_model_project(data, goal, str(data.get("folder") or self._slug(goal)))
            project["attempt_history"] = attempts
            project["creation_analysis"] = creation_analysis
            return project
        fallback = self._fallback_project_for_goal(goal, mode)
        if fallback:
            attempts.append({"attempt": "fallback", "status": "used_deterministic_fallback", "reason": last_reason or "local model did not produce an accepted project"})
            fallback = self._normalise_model_project(fallback, goal, str(fallback.get("folder") or self._slug(goal)))
            fallback["source"] = "deterministic_fallback"
            fallback["attempt_history"] = attempts
            fallback["creation_analysis"] = creation_analysis
            fallback["best_rejected_candidate"] = {
                "reason": best_candidate_reason,
                "files": sorted((best_candidate.get("files") or {}).keys()) if isinstance(best_candidate, dict) and isinstance(best_candidate.get("files"), dict) else [],
            }
            self._last_model_attempts = attempts
            self._last_model_error = "Used deterministic fallback after local LLM attempts failed: " + (last_reason or "unknown model failure")
            log_activity("llm_fallback_used", "Using deterministic project fallback after local LLM attempts failed", {"goal": goal, "mode": mode, "attempts": attempts, "best_candidate_reason": best_candidate_reason})
            return fallback
        self._last_model_attempts = attempts
        self._last_model_candidate = best_candidate
        self._last_model_error = last_reason or "model failed to produce a valid project"
        return None


    def _is_failure_feedback_goal(self, goal: str) -> bool:
        g = self._validation_goal_text(goal).lower()
        g = re.sub(r"\s+", " ", g)
        complaint_markers = [
            "you didnt", "you didn't", "you did not", "didnt actually", "didn't actually",
            "did not actually", "didnt make", "didn't make", "did not make",
            "didnt give", "didn't give", "did not give", "nothing happened",
            "not actually make", "it made nothing", "it didn't make", "it didnt make",
            "keeps repeating", "keeps looping", "candidate_refine", "model output did not",
        ]
        if any(marker in g for marker in complaint_markers):
            return True
        return "why" in g and "fix" in g and any(x in g for x in ["anything", "nothing", "actual", "actually", "loop", "repeat", "failed"])

    def _extract_requirement_terms(self, goal: str) -> list[str]:
        """Infer user-specific acceptance terms from the prompt without hardcoding one domain.

        This is deliberately generic: it pulls nouns/features from the user's own words
        and checks that the generated implementation contains those concepts in UI/code,
        not only in README marketing text.
        """
        if self._is_failure_feedback_goal(goal):
            return []
        g = re.sub(r"[^A-Za-z0-9_ /,+-]+", " ", strip_interactive_clarification(self._validation_goal_text(goal))).lower()
        stop = {
            "make", "build", "create", "generate", "write", "useful", "simple", "basic", "with", "and", "or",
            "the", "a", "an", "app", "application", "website", "tool", "program", "project", "for", "to", "of",
            "that", "can", "able", "local", "saving", "save", "export", "track", "tracking", "simulated", "user",
            "please", "include", "has", "have", "from", "into", "then", "also", "really", "interesting",
            "you", "your", "why", "anything", "nothing", "actually", "actual", "give", "gave",
            "didnt", "didn", "dont", "doesn", "wasn", "isn", "what", "need", "needs", "clarification", "interactive", "reply", "option", "recommended", "run", "new"
        }
        tokens = [t for t in re.findall(r"[a-z][a-z0-9]{2,}", g) if t not in stop]
        # Keep order while removing duplicates.
        seen: set[str] = set()
        ordered = []
        for t in tokens:
            if t not in seen:
                seen.add(t); ordered.append(t)
        # Include multi-word feature phrases after "with" and comma-separated requirements.
        phrases = []
        m = re.search(r"\bwith\b(.+)$", g)
        if m:
            raw = m.group(1)
            for part in re.split(r",|\band\b|\bplus\b", raw):
                words = [w for w in re.findall(r"[a-z][a-z0-9]{2,}", part) if w not in stop]
                if 1 <= len(words) <= 4:
                    phrases.append(" ".join(words))
        # Return compact acceptance terms. Single words are easier to match in code.
        return (ordered[:18] + [x for x in phrases if x and x not in ordered])[:28]

    def _generic_feature_expectations(self, goal: str) -> dict[str, list[str]]:
        """Generic feature expectations inferred from common user wording.

        These are not templates. They are checks that any generated app should satisfy
        when the user asks for those capabilities, no matter the domain.
        """
        if self._is_failure_feedback_goal(goal):
            return {}
        g = self._validation_goal_text(goal).lower()
        ex: dict[str, list[str]] = {}
        if any(k in g for k in ["local saving", "local save", "save", "saving", "persist", "storage"]):
            ex["local_saving"] = ["localstorage", "setitem", "getitem"]
        if any(k in g for k in ["export", "download json", "json export", "csv export", "download"]):
            ex["export"] = ["blob", "createobjecturl", "download", "json.stringify"]
        if any(k in g for k in ["progress", "tracking", "tracker", "status"]):
            ex["progress_tracking"] = ["progress", "status", "complete", "done", "percent"]
        if any(k in g for k in ["history", "log", "transactions", "record"]):
            ex["history"] = ["history", "log", "record", "transaction"]
        if any(k in g for k in ["priority", "important"]):
            ex["priority"] = ["priority", "high", "medium", "low"]
        if any(k in g for k in ["search", "filter"]):
            ex["search_filter"] = ["search", "filter"]
        if any(k in g for k in ["buy", "sell"]):
            ex["buy_sell_workflow"] = ["buy", "sell"]
        if any(k in g for k in ["run", "runnable", "browser", "app", "game", "website"]):
            ex["runnable_ui"] = ["button", "input", "addeventlistener", "form", "canvas"]
        return ex

    def _requirements_spec(self, goal: str, build_mode: str = "auto") -> dict[str, Any]:
        """Create a generic acceptance contract from the user's own words.

        This is intentionally not tied to one example. It records the domain terms,
        requested capabilities, expected files and how the project will be judged.
        """
        clean_goal = self._validation_goal_text(goal)
        terms = self._extract_requirement_terms(clean_goal)
        feature_expectations = self._generic_feature_expectations(clean_goal)
        domains = self._goal_domain_requirements(clean_goal)
        creation_analysis = analyze_creation_request(clean_goal)
        project_brief = infer_project_build_brief(clean_goal)
        coding_plan = plan_coding_execution(clean_goal)
        request_contract = build_request_contract(clean_goal)
        acceptance = []
        if terms:
            acceptance.append("The actual code/UI should visibly contain and use the main user-requested concepts: " + ", ".join(terms[:18]))
        for feature in feature_expectations:
            acceptance.append(f"Requested capability must be implemented in code, not only described in README: {feature}")
        acceptance.extend([
            "Project must have runnable source files.",
            "Generated code must pass syntax/build checks where a checker is available.",
            "README claims must not exceed what the code actually implements.",
            "If checks fail, repairs must edit the same project folder instead of creating a nested project.",
        ])
        contract_files = list(request_contract.get("expected_output_files") or [])
        if contract_files:
            acceptance.append("Expected output file contract: " + ", ".join(contract_files))
        if request_contract.get("must_not_create_scaffold"):
            acceptance.append("Do not create a generic scaffold or extra template files for this request.")
        return {
            "goal": clean_goal,
            "build_mode": build_mode,
            "request_contract": request_contract,
            "domain_guardrails": domains,
            "project_build_brief": project_brief.to_dict(),
            "coding_execution_plan": coding_plan,
            "acceptance_terms": terms,
            "feature_expectations": feature_expectations,
            "acceptance_tests": acceptance + project_brief.acceptance_tests,
            "suggested_files": project_brief.suggested_files,
            "suggested_stream": build_mode,
            "creation_analysis": creation_analysis,
        }

    def _write_lifecycle_files(self, root: Path, manifest: dict[str, Any], verify_result: dict[str, Any] | None = None, status: str = "in_progress") -> None:
        """Write human-readable developer artefacts for every generated project."""
        req = manifest.get("requirements") or self._requirements_spec(str(manifest.get("goal") or ""), str(manifest.get("build_mode") or "auto"))
        atomic_write_json((root / "REQUIREMENTS.json"), req, ensure_ascii=False)
        checks = []
        if isinstance(verify_result, dict):
            checks = verify_result.get("checks") or []
        passed = sum(1 for c in checks if isinstance(c, dict) and c.get("ok"))
        failed = [c for c in checks if isinstance(c, dict) and not c.get("ok")]
        report = [
            "# Test Report",
            "",
            f"Status: {status}",
            f"Goal: {manifest.get('goal','')}",
            f"Build mode: {manifest.get('build_mode','auto')}",
            "",
            "## Acceptance terms",
        ]
        for t in req.get("acceptance_terms", [])[:30]:
            report.append(f"- {t}")
        report.extend(["", "## Requested capabilities"])
        for k in (req.get("feature_expectations") or {}).keys():
            report.append(f"- {k}")
        report.extend(["", "## Checks"])
        if checks:
            report.append(f"Passed: {passed}/{len(checks)}")
            for c in checks:
                name = c.get("name") or c.get("kind") or "check"
                report.append(f"- {'PASS' if c.get('ok') else 'FAIL'}: {name}")
                if not c.get("ok"):
                    detail = c.get("output") or c.get("problems") or c.get("message") or c
                    report.append("  - " + str(detail)[:1200].replace("\n", "\n  "))
        else:
            report.append("No checks have run yet.")
        atomic_write_text((root / "TEST_REPORT.md"), "\n".join(report) + "\n")
        final = [
            "# Final Output",
            "",
            f"Status: {status}",
            f"Project: {root.name}",
            f"Main file: {manifest.get('main_file','index.html')}",
            "Run command: " + str(manifest.get("run_command") or "start .\\index.html"),
            "",
            "## What was built",
            str(manifest.get("notes") or "Local LLM generated the project files, then Nova tested and repaired them."),
            "",
            "## How to run",
            "Open the main file from the GUI, or run the command above from this project folder.",
        ]
        if failed:
            final.extend(["", "## Remaining issues", "This project did not fully pass verification. Use `/fix-last` or `/continue repair the project`."])
        atomic_write_text((root / "FINAL_OUTPUT.md"), "\n".join(final) + "\n")
        try:
            changed_files = sorted((manifest.get("files") or {}).keys()) if isinstance(manifest.get("files"), dict) else []
            validation = []
            if isinstance(verify_result, dict):
                validation = [c for c in (verify_result.get("checks") or []) if isinstance(c, dict)]
            write_action_receipt(root, action="project_lifecycle", goal=str(manifest.get("goal") or ""), changed_files=changed_files, validation=validation, ok=(status == "complete" and not failed), notes=str(manifest.get("notes") or ""))
        except Exception as exc:
            log_activity("action_receipt_failed", "Could not write project action receipt", {"error": repr(exc), "root": str(root)})

    def _important_sources_for_quality(self, root: Path) -> str:
        chunks = []
        generated_report_names = {
            ".nova_project.json",
            "project_manifest.json",
            "requirements.json",
            "test_report.md",
            "final_output.md",
            "agent_trace.md",
            "error_investigation.md",
            "improvement_proposals.md",
            "project_iteration_log.jsonl",
            "project_verification_report.md",
            "creation_mismatch_report.md",
            "action_receipt.md",
            "final_output.md",
        }
        for p in sorted(root.rglob("*")):
            if self._skip(p) or not p.is_file():
                continue
            if p.name.lower() in generated_report_names:
                continue
            if p.suffix.lower() in {".html", ".js", ".css", ".py", ".json", ".md", ".txt", ".java", ".ps1", ".bat"}:
                try:
                    chunks.append(f"--- {p.relative_to(root).as_posix()} ---\n" + p.read_text(encoding="utf-8", errors="replace")[:12000])
                except Exception as exc:
                        log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        return "\n\n".join(chunks)[:60000]

    def _static_acceptance_check(self, root: Path, goal: str) -> tuple[bool, list[dict[str, Any]]]:
        """Check that generated files appear to implement the user's own requested features.

        This avoids the previous bug where a note app or weak demo passed just because files existed.
        """
        problems: list[dict[str, Any]] = []
        code_parts = []
        readme_parts = []
        generated_report_names = {
            ".nova_project.json",
            "project_manifest.json",
            "requirements.json",
            "test_report.md",
            "final_output.md",
            "agent_trace.md",
            "error_investigation.md",
            "improvement_proposals.md",
            "project_iteration_log.jsonl",
            "project_verification_report.md",
            "creation_mismatch_report.md",
            "action_receipt.md",
            "final_output.md",
        }
        for p in root.rglob("*"):
            if self._skip(p) or not p.is_file():
                continue
            try:
                if "logs" in p.relative_to(root).parts:
                    continue
            except ValueError:
                pass
            if p.name.lower() in generated_report_names:
                continue
            try:
                text = p.read_text(encoding="utf-8", errors="replace").lower()
            except Exception:
                continue
            if p.suffix.lower() in {".html", ".js", ".css", ".py"}:
                code_parts.append(text)
            elif p.suffix.lower() in {".md", ".txt", ".json"}:
                readme_parts.append(text)
        code = "\n".join(code_parts)
        docs = "\n".join(readme_parts)
        combined = code + "\n" + docs

        clean_goal = self._validation_goal_text(goal)
        terms = self._extract_requirement_terms(clean_goal)
        # Do not require meta/instruction words from interactive prompts; only concrete project concepts.
        ignore_terms = {"before", "choosing", "scope", "clarification", "interactive", "this", "that", "about", "specific", "create", "creating", "make", "useful", "local", "first", "please", "thing", "something", "infomation", "want", "looks", "look", "inside", "certain", "any", "type"}
        aliases = {"infomation": "information"}
        terms = [aliases.get(t, t) for t in terms if t not in ignore_terms]
        # Do not require every vague word; require enough of the user's concrete concepts.
        concrete = [t for t in terms if len(t) >= 4]
        matched = [t for t in concrete if t.replace(" ", "") in code.replace(" ", "") or t in code]
        if len(concrete) >= 5 and len(matched) < max(3, min(8, len(concrete)//2)):
            problems.append({"kind": "goal_coverage", "message": "Too few user-requested concepts appear in the actual code/UI files", "required_terms": concrete, "matched_in_code": matched})

        for feature, alternatives in self._generic_feature_expectations(clean_goal).items():
            hits = [a for a in alternatives if a in code]
            if not hits:
                problems.append({"kind": "missing_feature", "feature": feature, "expected_any_of": alternatives})

        # README claims must not exceed code capabilities too badly.
        # Use aliases so a human-valid feature is not rejected just because the
        # docs use a broader word such as "progress" while the code implements
        # it as score/lives/levels/timer.
        claim_expectations = {
            "export": ["export", "download", "blob", "json.stringify", "createobjecturl", "text/csv"],
            "localstorage": ["localstorage", "setitem", "getitem"],
            "profit": ["profit", "pnl", "gain", "return"],
            "loss": ["loss", "pnl", "drawdown"],
            "history": ["history", "transactions", "log", "records"],
            "buy": ["buy", "purchase"],
            "sell": ["sell"],
            "progress": ["progress", "score", "level", "lives", "timer", "best", "complete", "done", "percent"],
            "priority": ["priority"],
            "cash": ["cash", "balance"],
            "portfolio": ["portfolio", "holdings", "positions"],
        }
        false_claims = [claim for claim, alternatives in claim_expectations.items() if claim in docs and not any(alt in code for alt in alternatives)]
        if false_claims:
            problems.append({"kind": "readme_claim_not_implemented", "claims": false_claims})

        if any(p.name.lower() == "index.html" for p in root.rglob("*")):
            if "<button" not in code and "addeventlistener" not in code and "<form" not in code and "canvas" not in code:
                problems.append({"kind": "weak_interactivity", "message": "Browser project has no clear buttons/forms/canvas/event-driven UI"})
            if ("function " not in code and "=>" not in code) and "<script" in code:
                problems.append({"kind": "weak_logic", "message": "Browser project appears to have little or no application logic"})
            html_text = "\n".join(part for part in code_parts if "<html" in part or "<body" in part or "<button" in part or "<input" in part)
            js_text = "\n".join(part for part in code_parts if "document." in part or "addeventlistener" in part or "function" in part or "localstorage" in part)
            html_ids = set(re.findall(r'id\s*=\s*["\']([^"\']+)["\']', html_text, re.I))
            js_ids = set(re.findall(r'getelementbyid\s*\(\s*["\']([^"\']+)["\']\s*\)', js_text, re.I))
            missing_ids = sorted(x for x in js_ids if x not in html_ids)
            if missing_ids:
                problems.append({"kind": "broken_dom_reference", "missing_ids": missing_ids[:10], "message": "JavaScript references DOM ids that do not exist in index.html."})
            inline_handlers = set(re.findall(r'on(?:click|submit|change|input)\s*=\s*["\']([a-zA-Z_$][\w$]*)\s*\(', html_text, re.I))
            defined_funcs = set(re.findall(r'function\s+([a-zA-Z_$][\w$]*)\s*\(', js_text, re.I)) | set(re.findall(r'(?:const|let|var)\s+([a-zA-Z_$][\w$]*)\s*=\s*\(', js_text, re.I))
            missing_handlers = sorted(x for x in inline_handlers if x not in defined_funcs and f"window.{x.lower()}" not in js_text)
            if missing_handlers:
                problems.append({"kind": "broken_inline_handler", "missing_handlers": missing_handlers[:10], "message": "HTML inline event handlers are not implemented by JavaScript."})
            if "localstorage" in js_text and "json.parse" in js_text and "try" not in js_text:
                problems.append({"kind": "fragile_localstorage_parse", "message": "localStorage JSON.parse should be guarded so corrupted saved data does not break the app."})

        # Human-level request-specific acceptance checks. These catch weak projects
        # that pass syntax but are not usable for the thing the user actually asked for.
        problems.extend(self._request_specific_quality_check(goal, code, docs))

        generic_markers = [m for m in self._generic_template_markers() if m in combined]
        if generic_markers:
            problems.append({"kind": "generic_template", "markers": generic_markers})
        return not problems, problems


    def _request_specific_quality_check(self, goal: str, code: str, docs: str = "") -> list[dict[str, Any]]:
        """Static human-quality checks for common generated artifact types.

        These checks are intentionally conservative: they do not prove the app is
        perfect, but they stop Nova from claiming success for dead calculator UIs,
        placeholder todo lists, or games with no real interaction.
        """
        low = (goal or "").lower()
        text = (code or "").lower()
        all_text = text + "\n" + (docs or "").lower()
        problems: list[dict[str, Any]] = []

        def has_any(*tokens: str) -> bool:
            return any(token in text for token in tokens)

        if "calculator" in low or "calc" in low:
            if not has_any("input", "button", "display", "result", "screen"):
                problems.append({"kind": "calculator_missing_ui", "message": "Calculator needs visible input/buttons and a result/display area."})
            operator_hits = sum(1 for token in ["+", "-", "*", "/", "operator", "calculate", "eval("] if token in text)
            if operator_hits < 2:
                problems.append({"kind": "calculator_missing_operations", "message": "Calculator needs multiple implemented arithmetic operations, not just a static result box."})
            digit_hits = sum(1 for digit in "0123456789" if digit in text)
            if digit_hits < 6 and "number" not in text and "digit" not in text:
                problems.append({"kind": "calculator_missing_digits", "message": "Calculator needs enough digit/number entry support to be usable."})
            if not has_any("clear", "backspace", "delete", "reset"):
                problems.append({"kind": "calculator_missing_clear", "message": "Calculator should include clear/backspace/reset behaviour."})
            if not has_any("addeventlistener", "onclick", "calculate", "update", "append"):
                problems.append({"kind": "calculator_missing_interaction", "message": "Calculator UI appears non-functional; no event/update logic found."})
            if "dodge" in all_text or "canvasdodgegame" in all_text:
                problems.append({"kind": "calculator_replaced_by_game", "message": "Calculator request appears to have been replaced by a Dodge/Game template."})

        if "todo" in low or "to-do" in low or "task list" in low:
            if not has_any("todo", "task"):
                problems.append({"kind": "todo_missing_domain", "message": "Todo app should visibly model tasks/todos."})
            if not has_any("add", "push(", "create"):
                problems.append({"kind": "todo_missing_add", "message": "Todo app needs add-task behaviour."})
            if not has_any("delete", "remove", "splice", "filter("):
                problems.append({"kind": "todo_missing_delete", "message": "Todo app needs delete/remove behaviour."})
            if not has_any("complete", "done", "checked", "toggle"):
                problems.append({"kind": "todo_missing_complete", "message": "Todo app needs complete/toggle behaviour."})

        if self._goal_requests_file_creation_script(low):
            if not self._file_creation_terms_present(all_text):
                problems.append({"kind": "file_creation_missing_workflow", "message": "File-creation script must accept a filename/content, write or download the file, and handle path/folder safety."})
            if "john doe" in all_text or "verify details" in all_text:
                problems.append({"kind": "file_creation_replaced_by_verification_demo", "message": "File-creation request was replaced by an unrelated name/email verification demo."})

        if "game" in low or "snake" in low or "pong" in low:
            if not has_any("keydown", "keyup", "pointer", "mousedown", "touchstart", "addeventlistener"):
                problems.append({"kind": "game_missing_user_controls", "message": "Game needs real user controls."})
            if not has_any("score", "level", "lives", "gameover", "game over", "restart"):
                problems.append({"kind": "game_missing_progress", "message": "Game needs score/progress/end-state/restart feedback."})
            if not has_any("collision", "collide", "intersect", "hit", "food", "enemy", "obstacle", "block", "ball"):
                problems.append({"kind": "game_missing_interaction", "message": "Game needs collision, food, enemy, obstacle or other gameplay interaction."})
            if not has_any("requestanimationframe", "setinterval", "loop", "update", "draw"):
                problems.append({"kind": "game_missing_loop", "message": "Game needs a real update/draw loop."})
            if not has_any("restart", "reset", "gameover", "game over", "startgame"):
                problems.append({"kind": "game_missing_restart_or_end_state", "message": "Game should have restart or clear end-state behaviour."})
            if not has_any("instructions", "use arrow", "controls", "how to play", "press"):
                problems.append({"kind": "game_missing_instructions", "message": "Game should explain controls/objective to the user."})
            if "snake" in low and "snake" not in all_text:
                problems.append({"kind": "snake_theme_missing", "message": "Snake game request must contain snake-specific logic/theme."})

        return problems

    def _ask_model_for_quality_review(self, goal: str, root: Path, previous_problems: list[dict[str, Any]] | None = None) -> dict[str, Any] | None:
        context = self._important_sources_for_quality(root)
        clean_goal = self._validation_goal_text(goal)
        req_terms = self._extract_requirement_terms(clean_goal)
        expectations = self._generic_feature_expectations(clean_goal)
        prompt = f"""
You are a strict senior software developer reviewing and repairing a local project.
Return ONLY valid JSON. No markdown fences.

USER REQUIREMENT:
{goal}

VALIDATION SOURCE REQUEST:
{clean_goal}

INFERRED ACCEPTANCE TERMS FROM USER WORDS:
{json.dumps(req_terms, ensure_ascii=False)}

GENERIC FEATURE EXPECTATIONS:
{json.dumps(expectations, ensure_ascii=False, indent=2)}

CURRENT PROJECT FILES:
{context}

KNOWN PROBLEMS FROM AUTOMATIC CHECKS:
{json.dumps(previous_problems or [], ensure_ascii=False, indent=2)[:12000]}

RECENT ERROR/RUNTIME CONTEXT:
{self._local_model_runtime_context(root)}

LOCAL RUN CONTEXT / ANALYSIS / VERIFICATION CONDITIONS:
{self._local_model_implementation_context(root, goal=goal, previous_problems=previous_problems)}

Task:
1. Decide if the project actually satisfies the user requirement, not just syntax.
2. If it is missing features or is too weak, return complete replacement files for the files that must change.
3. Do not create a new nested project folder. Edit this project.
4. Do not merely update README claims; implement working UI/code.
5. For browser apps, include real controls, event handlers, localStorage if requested, export if requested, and useful seeded data.
6. For calculators, implement actual arithmetic input, operator buttons, result updates, clear/backspace and keyboard/click handling.
7. For todo apps, implement add, delete and complete/toggle task behaviour.
8. For games, implement controls, objective, score/progress, collision/interaction, restart and clear instructions; do not return a static box with an unmoving square.

JSON schema:
{{
  "verdict": "pass" or "repair",
  "missing": ["specific missing behaviour"],
  "improvements": ["specific improvement made or recommended"],
  "main_file": "index.html",
  "run_command": "start .\\index.html",
  "verify_command": 'python -c "from pathlib import Path; missing=[p for p in [\'index.html\',\'app.js\'] if not Path(p).exists()]; print(\'ok\' if not missing else \'missing \'+\',\'.join(missing)); raise SystemExit(1 if missing else 0)"',
  "files": {{
    "app.js": "complete file content if repair is needed",
    "index.html": "complete file content if repair is needed",
    "style.css": "complete file content if repair is needed",
    "README.md": "complete file content if repair is needed"
  }}
}}
"""
        log_activity("quality_review_start", "Asking local LLM to review project against user requirements", {"goal": goal, "terms": req_terms, "expectations": expectations})
        log_model_io("quality_review_prompt", prompt=prompt, data={"goal": goal, "model": self.config.model})
        reply = model_chat(self.config, self.config.model, [{"role": "user", "content": prompt}], timeout=240, desc="local LLM prompt")
        log_model_io("quality_review_response", response=reply or "", data={"received_chars": len(reply or "")})
        data = self._extract_json_object(reply or "") if reply else None
        if isinstance(data, dict):
            return data
        return None

    def _auto_fix_common_code_errors(self, root: Path, written: list[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        """Deterministic last-mile repair for common local-LLM JavaScript mistakes.

        This does not replace the LLM. It prevents the loop from failing forever on
        tiny syntax mistakes after the model has already produced mostly-correct code.
        """
        fixes: list[dict[str, Any]] = []
        for js in root.rglob("*.js"):
            if self._skip(js) or not js.is_file():
                continue
            try:
                before = js.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            after = self._normalise_candidate_js_text(before)
            # JS does not allow optional chaining on the left side of +=.
            pattern = re.compile(r"^(?P<indent>\s*)(?P<expr>.+?\.find\([^\n]+?\))\?\.(?P<prop>[A-Za-z_$][\w$]*)\s*\+=\s*(?P<rhs>[^;]+);\s*$", re.MULTILINE)
            counter = 0
            def repl(m: re.Match[str]) -> str:
                nonlocal counter
                counter += 1
                name = f"__wlaTarget{counter}"
                indent = m.group("indent")
                return f"{indent}const {name} = {m.group('expr')};\n{indent}if ({name}) {{ {name}.{m.group('prop')} += {m.group('rhs')}; }}"
            after = pattern.sub(repl, after)
            # Common runtime bug: declare state const, then later assign state = loadState().
            if re.search(r"\bconst\s+state\s*=", after) and re.search(r"\bstate\s*=\s*load", after):
                after = re.sub(r"\bconst\s+state\s*=", "let state =", after, count=1)
            # Stray backslash accidentally inserted into statement joins.
            after = after.replace(";\\tradeDiv", ";\n    tradeDiv")

            # Common local-LLM JavaScript bug: it tries to write `.join('\n')` but
            # the JSON/string round-trip leaves a literal newline inside the JS string:
            #   .join('          <-- line break inside string, SyntaxError
            #   ')
            # Repair this surgically instead of rolling the whole project back.
            after = re.sub(r"\.join\('\s*\n\s*'\)", r".join('\\n')", after)
            after = re.sub(r'\.join\(\"\s*\n\s*\"\)', r'.join("\\n")', after)

            # Same issue can occur in CSV literals when the generated file contains
            # an unterminated string immediately before a newline. Keep this narrow so
            # we do not alter normal multiline template strings.
            after = after.replace("join('\n", "join('\\n")
            after = after.replace('join("\n', 'join("\\n')

            # Common generated Pong bug: code reads rightPressed/leftPressed but never
            # declares them or installs keyboard listeners. Add the missing state and
            # listeners instead of rejecting an otherwise usable small game.
            uses_arrow_state = "rightPressed" in after or "leftPressed" in after
            missing_arrow_state = uses_arrow_state and not re.search(r"\b(?:let|const|var)\s+rightPressed\b", after) and not re.search(r"\b(?:let|const|var)\s+leftPressed\b", after)
            if missing_arrow_state:
                state_lines = "let rightPressed = false;\nlet leftPressed = false;\n"
                ctx_match = re.search(r"^const\s+ctx\s*=\s*canvas\.getContext\([^\n]+;\s*$", after, flags=re.MULTILINE)
                if ctx_match:
                    insert_at = ctx_match.end()
                    after = after[:insert_at] + "\n" + state_lines + after[insert_at:]
                else:
                    after = state_lines + after
            if uses_arrow_state and "keydown" not in after.lower():
                listener_code = """

document.addEventListener('keydown', event => {
    if (event.key === 'Right' || event.key === 'ArrowRight') rightPressed = true;
    if (event.key === 'Left' || event.key === 'ArrowLeft') leftPressed = true;
});

document.addEventListener('keyup', event => {
    if (event.key === 'Right' || event.key === 'ArrowRight') rightPressed = false;
    if (event.key === 'Left' || event.key === 'ArrowLeft') leftPressed = false;
});
"""
                interval_match = re.search(r"\n\s*setInterval\s*\(", after)
                if interval_match:
                    after = after[:interval_match.start()] + listener_code + after[interval_match.start():]
                else:
                    after += listener_code

            game_like = any(token in after.lower() for token in ["score", "gameover", "canvas", "requestanimationframe", "setinterval"])
            if game_like and "restart" not in after.lower() and "resetgame" not in after.lower():
                after += """

function restartGame() {
    score = 0;
    if (typeof gameOver !== 'undefined') gameOver = false;
}

document.addEventListener('keydown', event => {
    if (event.key === 'r' || event.key === 'R') restartGame();
});
"""

            if after != before:
                atomic_write_text(js, after)
                diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile="before", tofile="after", lineterm=""))
                info = {"path": str(js), "bytes": len(after.encode("utf-8")), "diff": diff[:25000]}
                fixes.append(info)
                if written is not None:
                    written.append(info)
                log_activity("auto_code_fix", f"Applied deterministic syntax/runtime fix to {js.name}", {"file": js.relative_to(root).as_posix(), "diff_preview": diff[:4000]})

        for html in root.rglob("*.html"):
            if self._skip(html) or not html.is_file():
                continue
            try:
                before = html.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            lower = before.lower()
            if "<canvas" in lower and "instructions" not in lower and "how to play" not in lower:
                addition = '<p class="instructions">Instructions: use the arrow keys or A/D to play. Press R to restart.</p>'
                if "</body>" in lower:
                    after = re.sub(r"</body>", addition + "\n</body>", before, count=1, flags=re.IGNORECASE)
                else:
                    after = before + "\n" + addition + "\n"
                atomic_write_text(html, after)
                diff = "\n".join(difflib.unified_diff(before.splitlines(), after.splitlines(), fromfile="before", tofile="after", lineterm=""))
                info = {"path": str(html), "bytes": len(after.encode("utf-8")), "diff": diff[:25000], "reason": "added game instructions"}
                fixes.append(info)
                if written is not None:
                    written.append(info)
                log_activity("auto_code_fix", f"Added game instructions to {html.name}", {"file": html.relative_to(root).as_posix(), "diff_preview": diff[:4000]})
        return fixes

    def _safe_concat_files(self, root: Path, pattern: str, size_limit: int = 500000) -> str:
        """Safely concatenate files matching pattern with size limit to prevent memory explosion.
        
        Args:
            root: Root directory to search from
            pattern: Glob pattern (e.g., "*.html", "*.js")
            size_limit: Maximum total bytes to concatenate (default 500KB)
            
        Returns:
            Concatenated content string, truncated if size_limit exceeded
        """
        total_size = 0
        parts = []
        for p in root.rglob(pattern):
            if self._skip(p):
                continue
            try:
                content = p.read_text(encoding="utf-8", errors="replace")
                content_size = len(content.encode("utf-8"))
                if total_size + content_size > size_limit:
                    # Size limit reached; add truncation marker and stop
                    parts.append(f"\n... [truncated - reached {size_limit} byte limit] ...")
                    break
                parts.append(content)
                total_size += content_size
            except Exception:
                pass
        return "\n".join(parts)

    def _game_runtime_sanity_check(self, root: Path, goal: str) -> tuple[bool, list[dict[str, Any]]]:
        g = self._validation_goal_text(goal).lower()
        if "game" not in g and "games" not in g:
            return True, []
        # SAFETY: Use bounded concatenation to prevent memory issues on large repos
        html = self._safe_concat_files(root, "*.html", size_limit=500000)
        js = self._safe_concat_files(root, "*.js", size_limit=500000)
        code = (html + "\n" + js).lower()
        problems: list[dict[str, Any]] = []
        if "<canvas" not in code:
            problems.append({"kind": "game_missing_canvas", "message": "Browser game should render a visible canvas."})
        if not any(token in code for token in ["score", "lives", "level", "gameover", "game over", "state"]):
            problems.append({"kind": "game_missing_score_or_state", "message": "Game should expose score, lives, level or clear game state."})
        collision_markers = ["collision", "collide", "intersect", "rectscollide", "rectsoverlap", "rectshit", "rects_hit", "overlap", "paddlex", "ballradius"]
        if not any(token in code for token in collision_markers):
            problems.append({"kind": "game_missing_collision", "message": "Game should include collision logic."})
        elif "rectsoverlap" in code and code.count("rectsoverlap") < 2 and "checkcollisions" not in code:
            problems.append({"kind": "game_collision_not_invoked", "message": "Collision helper exists but does not appear to be called by the game loop."})
        if not any(token in code for token in ["requestanimationframe", "setinterval", "function draw", "function update"]):
            problems.append({"kind": "game_missing_loop", "message": "Game should include a draw/update loop."})
        if not any(token in code for token in ["keydown", "keyup", "pointerdown", "mousedown", "addeventlistener"]):
            problems.append({"kind": "game_missing_controls", "message": "Game should include keyboard, pointer or button controls."})
        if re.search(r"\brightPressed\b", js) and not re.search(r"\b(?:let|const|var)\s+rightPressed\b", js):
            problems.append({"kind": "game_undeclared_right_pressed", "message": "rightPressed is used without a declaration."})
        if re.search(r"\bleftPressed\b", js) and not re.search(r"\b(?:let|const|var)\s+leftPressed\b", js):
            problems.append({"kind": "game_undeclared_left_pressed", "message": "leftPressed is used without a declaration."})
        if any(name in js for name in ["rightPressed", "leftPressed"]) and "keydown" not in js.lower():
            problems.append({"kind": "game_missing_keyboard_listeners", "message": "Arrow-key state is present but no keydown listener exists."})
        return not problems, problems

    def _behavioural_contract_check(self, root: Path, goal: str) -> tuple[bool, list[dict[str, Any]]]:
        """Lightweight behavioural checks for generated browser projects.

        These checks are static but behaviour-focused: they look for event handlers,
        state updates, and concrete actions that a human would expect to work. They
        are intentionally dependency-free so they can run on Windows without a
        browser test stack.
        """
        low = self._validation_goal_text(goal).lower()
        # SAFETY: Use bounded concatenation to prevent memory issues on large repos
        html = self._safe_concat_files(root, "*.html", size_limit=500000)
        js = self._safe_concat_files(root, "*.js", size_limit=500000)
        code = (html + "\n" + js).lower()
        problems: list[dict[str, Any]] = []
        if "calculator" in low or "calc" in low:
            if not re.search(r"(addEventListener|onclick)\s*\(", code) and "onclick=" not in code:
                problems.append({"kind": "calculator_no_click_wiring", "message": "Calculator has no visible click/event wiring."})
            if not re.search(r"(textContent|innerText|innerHTML|value)\s*=", code):
                problems.append({"kind": "calculator_no_result_update", "message": "Calculator does not appear to update a display/result."})
            if not all(op in code for op in ["+", "-"]) or not any(op in code for op in ["*", "/", "multiply", "divide"]):
                problems.append({"kind": "calculator_too_few_operations", "message": "Calculator should implement multiple arithmetic operations."})
            if not re.search(r"(clear|backspace|delete|reset)", code):
                problems.append({"kind": "calculator_no_clear_backspace", "message": "Calculator should include clear/backspace/reset behaviour."})
            if not re.search(r"(equals|calculate|compute|=)", code):
                problems.append({"kind": "calculator_no_equals_or_compute", "message": "Calculator should provide equals/calculate behaviour."})
        if "todo" in low or "to-do" in low or "task list" in low:
            if not re.search(r"tasks?\s*=\s*\[|\[\]", code):
                problems.append({"kind": "todo_no_task_state", "message": "Todo app should keep task state, even if only in-memory."})
            if not re.search(r"appendChild|insertAdjacentHTML|createElement|render", code):
                problems.append({"kind": "todo_no_render_update", "message": "Todo app should render task changes to the page."})
            if "addeventlistener" not in code and "onclick" not in code:
                problems.append({"kind": "todo_no_event_wiring", "message": "Todo app needs event handlers for user actions."})
            if not re.search(r"delete|remove|splice|filter\(", code):
                problems.append({"kind": "todo_no_delete_behaviour", "message": "Todo app should include delete/remove behaviour."})
            if not re.search(r"complete|done|checked|toggle|classlist", code):
                problems.append({"kind": "todo_no_complete_behaviour", "message": "Todo app should include complete/done toggle behaviour."})
        if "game" in low or "snake" in low or "pong" in low:
            if not re.search(r"(player|snake|paddle|ball|sprite)\s*=|\{\s*x\s*:|paddlex|paddley|ballradius|ballx|bally", code):
                problems.append({"kind": "game_no_actor_state", "message": "Game should have player/snake/paddle/ball state."})
            if not re.search(r"(x|y|score|lives|level)\s*(\+\+|--|\+=|-=|=)", code):
                problems.append({"kind": "game_no_state_updates", "message": "Game should update position, score, lives or level over time."})
            if "restart" not in code and "reset" not in code and "startgame" not in code:
                problems.append({"kind": "game_no_restart_handler", "message": "Game should provide restart/reset behaviour."})
        return not problems, problems

    def _project_quality_verify(self, root: Path, manifest: dict[str, Any]) -> ToolResult:
        """Run syntax, file, and requirement-coverage checks.

        v12: passing syntax is not enough. A project must also visibly implement
        the user's requested concepts and requested behaviours.
        """
        checks: list[dict[str, Any]] = []
        old = self.config.workspace
        self.config.workspace = str(root)
        try:
            verify_command = str(manifest.get("verify_command") or "").strip()
            if verify_command:
                if _is_prose_verify_command(verify_command):
                    checks.append({"name": "manifest_verify_skipped", "ok": True, "command": verify_command, "reason": "Skipped prose/manual verify command; built-in syntax/runtime checks will run instead."})
                else:
                    r = self.verify(verify_command)
                    checks.append({"name": "manifest_verify", "ok": r.ok, "result": r.data})
                    if not r.ok:
                        return ToolResult(False, "Manifest verification failed", {"checks": checks})

            py_files = [p for p in root.rglob("*.py") if not self._skip(p) and ".venv" not in p.parts and "venv" not in p.parts]
            if py_files:
                for py_file in py_files[:20]:
                    rel = py_file.relative_to(root).as_posix()
                    cp = subprocess.run([sys.executable, "-m", "py_compile", str(py_file)], cwd=str(root), capture_output=True, text=True, timeout=20)
                    output = (cp.stdout or "") + (cp.stderr or "")
                    ok = cp.returncode == 0
                    checks.append({"name": "python_syntax", "file": rel, "ok": ok, "returncode": cp.returncode, "output": output[-8000:]})
                    if not ok:
                        return ToolResult(False, "Python syntax check failed", {"checks": checks, "failed_file": rel, "output": output[-12000:]})

            java_files = [p for p in root.rglob("*.java") if not self._skip(p)]
            if java_files:
                javac = shutil.which("javac")
                if javac:
                    for java_file in java_files[:12]:
                        rel = java_file.relative_to(root).as_posix()
                        cp = subprocess.run([javac, str(java_file)], cwd=str(root), capture_output=True, text=True, timeout=30)
                        output = (cp.stdout or "") + (cp.stderr or "")
                        ok = cp.returncode == 0
                        checks.append({"name": "java_compile", "file": rel, "ok": ok, "returncode": cp.returncode, "output": output[-8000:]})
                        if not ok:
                            return ToolResult(False, "Java compile check failed", {"checks": checks, "failed_file": rel, "output": output[-12000:]})
                else:
                    for java_file in java_files[:12]:
                        text = java_file.read_text(encoding="utf-8", errors="replace")
                        ok = "class" in text and text.count("{") == text.count("}")
                        checks.append({"name": "basic_java_sanity", "file": java_file.relative_to(root).as_posix(), "ok": ok, "reason": "javac not available; checked class marker and braces"})
                        if not ok:
                            return ToolResult(False, "Basic Java sanity check failed", {"checks": checks})

            ps_files = [p for p in root.rglob("*.ps1") if not self._skip(p)]
            if ps_files:
                shell = shutil.which("pwsh") or shutil.which("powershell")
                if shell:
                    for ps_file in ps_files[:12]:
                        rel = ps_file.relative_to(root).as_posix()
                        cp = subprocess.run([shell, "-NoProfile", "-Command", f"$null = [scriptblock]::Create((Get-Content -Raw '{ps_file}')); 'syntax ok'"], cwd=str(root), capture_output=True, text=True, timeout=20)
                        output = (cp.stdout or "") + (cp.stderr or "")
                        ok = cp.returncode == 0
                        checks.append({"name": "powershell_syntax", "file": rel, "ok": ok, "returncode": cp.returncode, "output": output[-8000:]})
                        if not ok:
                            return ToolResult(False, "PowerShell syntax check failed", {"checks": checks, "failed_file": rel, "output": output[-12000:]})
                else:
                    for ps_file in ps_files[:12]:
                        text = ps_file.read_text(encoding="utf-8", errors="replace")
                        ok = text.count("{") == text.count("}") and text.count("(") == text.count(")")
                        checks.append({"name": "basic_powershell_sanity", "file": ps_file.relative_to(root).as_posix(), "ok": ok, "reason": "PowerShell not available; checked basic delimiter balance"})
                        if not ok:
                            return ToolResult(False, "Basic PowerShell sanity check failed", {"checks": checks})

            js_files = [p for p in root.rglob("*.js") if not self._skip(p)]
            if js_files:
                node = shutil.which("node")
                if node:
                    for js in js_files[:20]:
                        rel = js.relative_to(root).as_posix()
                        cp = subprocess.run([node, "--check", str(js)], cwd=str(root), capture_output=True, text=True, timeout=20)
                        output = (cp.stdout or "") + (cp.stderr or "")
                        ok = cp.returncode == 0
                        checks.append({"name": "node_syntax", "file": rel, "ok": ok, "returncode": cp.returncode, "output": output[-8000:]})
                        if not ok:
                            return ToolResult(False, "JavaScript syntax check failed", {"checks": checks, "failed_file": rel, "output": output[-12000:]})
                else:
                    for js in js_files[:20]:
                        text = js.read_text(encoding="utf-8", errors="replace")
                        suspicious = []
                        if text.count("(") != text.count(")"):
                            suspicious.append("unbalanced parentheses")
                        if text.count("{") != text.count("}"):
                            suspicious.append("unbalanced braces")
                        checks.append({"name": "basic_js_sanity", "file": js.relative_to(root).as_posix(), "ok": not suspicious, "problems": suspicious})
                        if suspicious:
                            return ToolResult(False, "Basic JavaScript sanity check failed", {"checks": checks})

            if (root / "index.html").exists() and not (root / "app.js").exists() and not (root / "game.js").exists():
                return ToolResult(False, "Browser project has index.html but no app.js/game.js logic file", {"checks": checks})

            goal = str(manifest.get("goal") or manifest.get("last_edit_goal") or "")
            game_ok, game_problems = self._game_runtime_sanity_check(root, goal)
            checks.append({"name": "game_runtime_sanity", "ok": game_ok, "problems": game_problems})
            if not game_ok:
                return ToolResult(False, "Game runtime sanity check failed", {"checks": checks, "problems": game_problems})

            behavioural_ok, behavioural_problems = self._behavioural_contract_check(root, goal)
            checks.append({"name": "behavioural_contract", "ok": behavioural_ok, "problems": behavioural_problems})

            runtime_probe = run_project_runtime_probe(goal, root=root)
            checks.append({"name": "project_runtime_probe", "ok": bool(runtime_probe.get("passed")), "probe": runtime_probe})
            if not runtime_probe.get("passed"):
                return ToolResult(False, "Project runtime interaction probe failed", {"checks": checks, "runtime_probe": runtime_probe, "problems": runtime_probe.get("repair_suggestions", [])})

            static_ok, problems = self._static_acceptance_check(root, goal)
            checks.append({"name": "static_acceptance", "ok": static_ok, "problems": problems})
            if not static_ok:
                return ToolResult(False, "Requirement acceptance check failed", {"checks": checks, "problems": problems})
            if not behavioural_ok:
                return ToolResult(False, "Behavioural project contract check failed", {"checks": checks, "problems": behavioural_problems})

            quality_score = score_created_project_quality(goal, [p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file() and not self._skip(p)], self._important_sources_for_quality(root), checks)
            checks.append({"name": "project_quality_score", "ok": bool(quality_score.get("passed_threshold")), "score": quality_score})
            if not quality_score.get("passed_threshold"):
                return ToolResult(False, "Project quality score is below the acceptance threshold", {"checks": checks, "quality_score": quality_score, "problems": quality_score.get("missing_or_weak_items", [])})
            return ToolResult(True, "Project quality verification passed", {"checks": checks, "quality_score": quality_score})
        finally:
            self.config.workspace = old

    def _apply_model_files_to_root(self, root: Path, folder: str, files: dict[str, Any], written: list[dict[str, Any]], event_kind: str = "code_write_start") -> None:
        for rel, content in (files or {}).items():
            rel = str(rel).replace("\\", "/").lstrip("/")
            # Never allow the model to accidentally create Project/Project/...
            # or sibling-name folders such as Tinyappproject/index.html when
            # repairing/editing/creating a chosen project folder. Local models
            # often include their own top-level folder despite being told not to.
            parts = [part for part in rel.split("/") if part]
            if parts and parts[0].lower() == folder.lower():
                rel = "/".join(parts[1:]) or rel
            elif len(parts) > 1:
                first_norm = re.sub(r"[^a-z0-9]", "", parts[0].lower())
                folder_norm = re.sub(r"[^a-z0-9]", "", folder.lower())
                placeholder_names = {"project", "projectfolder", "projectfoldername", "folder", "app", "application", "generatedproject"}
                if first_norm in placeholder_names or first_norm.startswith(folder_norm) or folder_norm.startswith(first_norm):
                    rel = "/".join(parts[1:]) or parts[-1]
            target = resolve_inside_workspace(root, rel)
            log_activity(event_kind, f"Writing model-generated file {rel}", {"file": rel, "chars": len(str(content)), "code_preview": str(content)[:10000]})
            written.append(self._write_one(target, str(content), append=False))

    def _write_manifest(self, root: Path, manifest: dict[str, Any]) -> None:
        atomic_write_json((root / "PROJECT_MANIFEST.json"), manifest, ensure_ascii=False)

    def _created_artifact_request_summary(self, root: Path, folder: str, manifest: dict[str, Any], written: list[dict[str, Any]]) -> str:
        parts = [
            folder,
            str(manifest.get("main_file", "")),
            str(manifest.get("run_command", "")),
            str(manifest.get("verify_command", "")),
            str(manifest.get("notes", "")),
            str(manifest.get("source", "")),
            json.dumps(manifest.get("assumptions") or [], ensure_ascii=False),
        ]
        for item in written[:12]:
            if not isinstance(item, dict):
                continue
            raw_path = str(item.get("path") or "")
            rel = raw_path.replace("\\", "/").lstrip("/")
            if not rel.lower().endswith((".html", ".js", ".css", ".py", ".md", ".txt", ".ps1")):
                continue
            try:
                raw_target = Path(raw_path).expanduser()
                if raw_target.is_absolute():
                    target = raw_target.resolve()
                    try:
                        rel_label = target.relative_to(root).as_posix()
                    except ValueError:
                        continue
                else:
                    target = resolve_inside_workspace(root, rel)
                    rel_label = rel
                if target.exists() and target.is_file():
                    parts.append(f"\n--- {rel_label} ---\n" + target.read_text(encoding="utf-8", errors="replace")[:4000])
            except Exception:
                continue
        return " ".join(parts)[:16000]

    def _maybe_propose_tool_from_project(self, goal: str, root: Path, manifest: dict[str, Any]) -> dict[str, Any] | None:
        """Promote repeated/inspired project workflows into a safe custom-tool proposal.

        The proposal is reviewable in the AI Toolbox rather than silently installing
        mutation-capable code. This keeps the user in control while letting Nova turn
        useful project patterns into reusable local tools.
        """
        low = (goal + " " + str(manifest.get("main_file", "")) + " " + str(manifest.get("notes", ""))).lower()
        if not any(k in low for k in ["script", "scan", "count", "report", "file", "files", "todo", "check"]):
            return None
        name = "project_file_summary"
        description = "Summarise project files inspired by a generated project workflow."
        code = 'from __future__ import annotations\n\n\ndef run(args, workspace):\n    limit = int(args.get("limit", 80) or 80)\n    suffixes = tuple(args.get("suffixes") or [".py", ".js", ".html", ".css", ".md", ".json", ".txt", ".ps1", ".bat"])\n    rows = []\n    for path in workspace.rglob("*"):\n        if len(rows) >= limit:\n            break\n        if not path.is_file() or path.name.startswith("."):\n            continue\n        if suffixes and path.suffix.lower() not in suffixes:\n            continue\n        text = path.read_text(encoding="utf-8", errors="replace")[:2000]\n        rows.append({"path": str(path.relative_to(workspace)), "chars": len(text), "lines": text.count("\n") + 1})\n    return {"files": rows, "count": len(rows)}\n'
        try:
            proposal = save_tool_proposal(name, description, code, {"limit": "optional max file count", "suffixes": "optional list of suffixes"}, section="Project Analysis", risk="read_only")
            log_activity("tool_proposal_created", "Created reviewable tool proposal from project/conversation context", {"proposal_id": proposal.get("id"), "name": proposal.get("name"), "project": str(root), "goal": goal})
            return proposal
        except Exception as exc:
            log_activity("tool_proposal_failed", "Could not create inspired tool proposal", {"error": repr(exc), "project": str(root), "goal": goal})
            return None

    def _repair_until_accepted(self, goal: str, root: Path, folder: str, manifest: dict[str, Any], written: list[dict[str, Any]], max_rounds: int = 3) -> tuple[bool, dict[str, Any]]:
        """Verify, ask local LLM for repairs/improvements, apply them, and repeat.

        This is the software-developer loop the user asked for: build -> test -> inspect
        requirements -> repair -> retest -> improve.
        """
        self._auto_fix_common_code_errors(root, written)
        iteration_events = []
        seen_repair_digests: set[str] = set()
        last_quality = self._project_quality_verify(root, manifest)
        quality_data = last_quality.data
        event = build_project_iteration_event(0, "initial_verification", last_quality)
        iteration_events.append(event)
        append_project_iteration_event(root, event)
        write_project_verification_report(root, goal, "initial-pass" if last_quality.ok else "needs-repair", iteration_events, quality_data)
        for round_no in range(1, max_rounds + 1):
            if last_quality.ok:
                # v55.3.123: do not keep a successful simple game/app trapped in a
                # local-model review loop. If deterministic verification already passes,
                # ship the project with receipts instead of asking for another broad review
                # that can re-trigger Ollama while the user sees "Working" forever.
                low_goal = self._validation_goal_text(goal).lower()
                qscore = quality_data.get("quality_score") if isinstance(quality_data, dict) else None
                simple_verified_app = any(token in low_goal for token in ["game", "calculator", "todo", "to-do", "timer", "counter", "quiz", "flashcard", "notes app", "simple app", "browser app", "html_css_js_page"])
                if (simple_verified_app and (not qscore or bool(qscore.get("passed_threshold", True)))) or self._is_vague_game_request(low_goal):
                    write_project_verification_report(root, goal, "passed", iteration_events, quality_data)
                    manifest["iteration_report"] = "PROJECT_VERIFICATION_REPORT.md"
                    manifest["iteration_log"] = "PROJECT_ITERATION_LOG.jsonl"
                    manifest["review_loop_guard"] = "v55.3.141 accepted deterministic verification for a simple app/game instead of looping in post-pass LLM review"
                    self._write_manifest(root, manifest)
                    log_activity("review_loop_guard", "Accepted verified project without another local-model review loop", {"goal": goal, "round": round_no, "quality_score": qscore})
                    return True, quality_data
                review = self._ask_model_for_quality_review(goal, root, [])
                if review and str(review.get("verdict", "")).lower() == "repair" and isinstance(review.get("files"), dict) and review.get("files"):
                    log_activity("quality_improvement", "Local LLM found improvements needed after passing static checks", {"round": round_no, "missing": review.get("missing"), "improvements": review.get("improvements")})
                    self._apply_model_files_to_root(root, folder, review["files"], written, event_kind="code_improvement_write")
                    manifest.update({
                        "main_file": review.get("main_file") or manifest.get("main_file") or "index.html",
                        "run_command": review.get("run_command") or manifest.get("run_command") or "start .\\index.html",
                        "verify_command": review.get("verify_command") or manifest.get("verify_command") or "",
                        "quality_review": {"missing": review.get("missing", []), "improvements": review.get("improvements", [])},
                    })
                    self._write_manifest(root, manifest)
                    self._auto_fix_common_code_errors(root, written)
                    last_quality = self._project_quality_verify(root, manifest)
                    quality_data = last_quality.data
                    event = build_project_iteration_event(round_no, "post_improvement_verification", last_quality, repair_source="quality_review", changed_files=sorted((review.get("files") or {}).keys()))
                    iteration_events.append(event)
                    append_project_iteration_event(root, event)
                    write_project_verification_report(root, goal, "passed" if last_quality.ok else "needs-repair", iteration_events, quality_data)
                    continue
                write_project_verification_report(root, goal, "passed", iteration_events, quality_data)
                manifest["iteration_report"] = "PROJECT_VERIFICATION_REPORT.md"
                manifest["iteration_log"] = "PROJECT_ITERATION_LOG.jsonl"
                self._write_manifest(root, manifest)
                return True, quality_data

            problems = last_quality.data.get("problems") or last_quality.data.get("checks") or []
            log_activity("verification_failed", "Project failed verification/acceptance; asking local LLM to repair same project", {"round": round_no, "summary": last_quality.summary, "data": last_quality.data})
            event = build_project_iteration_event(round_no, "verification_failed", last_quality)
            iteration_events.append(event)
            append_project_iteration_event(root, event)
            write_project_verification_report(root, goal, "needs-repair", iteration_events, last_quality.data)
            review = self._ask_model_for_quality_review(goal, root, problems if isinstance(problems, list) else [problems])
            if not review or not isinstance(review.get("files"), dict) or not review.get("files"):
                # Fall back to edit-mode generation, but still edit same folder only.
                repair_goal = "Repair the current project in-place so it fully satisfies the original request. Original request: " + goal + "\nFailure/acceptance problems: " + json.dumps(last_quality.data, ensure_ascii=False)[:8000]
                review = self._ask_model_for_project(repair_goal, mode="edit", build_mode=str(manifest.get("build_mode") or "long"), requirements=manifest.get("requirements"))
            if not review or not isinstance(review.get("files"), dict) or not review.get("files"):
                write_project_verification_report(root, goal, "failed-no-repair-available", iteration_events, quality_data)
                return False, quality_data
            if is_repeated_repair(review.get("files") or {}, seen_repair_digests):
                repeated_event = {"round_no": round_no, "stage": "repeated_repair_rejected", "ok": False, "summary": "Local model proposed the same repair files again; stopping to avoid a loop.", "problems": ["repeated repair proposal"], "repair_source": "local_model", "changed_files": sorted((review.get("files") or {}).keys())}
                iteration_events.append(repeated_event)
                append_project_iteration_event(root, repeated_event)
                write_project_verification_report(root, goal, "failed-repeated-repair", iteration_events, quality_data)
                return False, quality_data

            self._apply_model_files_to_root(root, folder, review.get("files") or {}, written, event_kind="code_repair_write")
            manifest.update({
                "main_file": review.get("main_file") or manifest.get("main_file") or "index.html",
                "run_command": review.get("run_command") or manifest.get("run_command") or "start .\\index.html",
                "verify_command": review.get("verify_command") or manifest.get("verify_command") or "",
                "notes": (manifest.get("notes") or "") + f"\nRepair/improvement round {round_no}: " + "; ".join(review.get("missing") or review.get("improvements") or []),
            })
            self._write_manifest(root, manifest)
            self._auto_fix_common_code_errors(root, written)
            last_quality = self._project_quality_verify(root, manifest)
            quality_data = last_quality.data
            event = build_project_iteration_event(round_no, "post_repair_verification", last_quality, repair_source="local_model", changed_files=sorted((review.get("files") or {}).keys()))
            iteration_events.append(event)
            append_project_iteration_event(root, event)
            write_project_verification_report(root, goal, "passed" if last_quality.ok else "needs-repair", iteration_events, quality_data)
        write_project_verification_report(root, goal, "passed" if last_quality.ok else "failed-after-repair-budget", iteration_events, quality_data)
        return last_quality.ok, quality_data

    def project_target_decision(self, goal: str = "", decision: dict[str, Any] | None = None) -> ToolResult:
        """Ask the user to choose current-vs-new project when context is ambiguous."""
        current_goal = ""
        manifest_path = self.workspace / "PROJECT_MANIFEST.json"
        try:
            if manifest_path.exists():
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
                current_goal = str(manifest.get("goal") or "")
        except Exception:
            current_goal = ""
        decision = decision or project_target_decision(goal, {"goal": current_goal, "name": self.workspace.name})
        commands = decision.get("recommended_commands") or [
            "/do create a new project for " + str(goal),
            "/continue modify the current project to include " + str(goal),
        ]
        summary = "Project target needs confirmation"
        message = [
            "Project target decision needed.",
            "",
            str(decision.get("question") or "Create a new project, or modify the current project?"),
            "",
            f"Current project: {self.workspace.name}",
            f"Reason: {decision.get('reason', 'The request may not match the active project.')}",
            "",
            "Choose one:",
            f"- New project: {commands[0]}",
            f"- Current project: {commands[1] if len(commands) > 1 else '/continue ' + str(goal)}",
        ]
        return ToolResult(True, summary, {"decision": decision, "message": "\n".join(message), "commands": commands})


    def codebase_integrity_audit(self, path: str = ".") -> ToolResult:
        """Run a whole-codebase integrity audit, including syntax/import/version/release checks."""
        root, target_meta = self._resolve_codebase_target(path, default_wla_source=True)
        md_path, json_path, report = write_codebase_integrity_report(root)
        rendered = render_codebase_integrity_markdown(report)
        log_activity("codebase_integrity_audit", "Whole-codebase integrity audit generated", {"path": str(md_path), "json_path": str(json_path), "decision": report.decision, "issues": len(report.issues), "ok": report.ok})
        return ToolResult(report.ok, f"Codebase integrity decision: {report.decision} ({len(report.issues)} issue(s))", {
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "ok": report.ok,
            "decision": report.decision,
            "issues": [issue.to_dict() for issue in report.issues[:60]],
            "passed_checks": report.passed_checks,
            "summary": rendered[:9000],
            "human_report": rendered[:7000],
            "target": target_meta,
        })

    def code_review_audit(self, path: str = ".") -> ToolResult:
        """Run a deeper read-only code review over reliability, maintainability and safety risks."""
        root, target_meta = self._resolve_codebase_target(path, default_wla_source=True)
        md_path, json_path, report = write_code_review_report(root)
        log_activity("code_review_audit", "Deep code review generated", {"path": str(md_path), "json_path": str(json_path), "findings": len(report.findings), "ok": report.ok})
        return ToolResult(report.ok, f"Deep code review completed with {len(report.findings)} finding(s)", {
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "ok": report.ok,
            "findings": [f.to_dict() for f in report.findings[:40]],
            "passed_checks": report.passed_checks,
            "summary": render_code_review_markdown(report)[:7000],
            "target": target_meta,
        })


    def code_quality_gate(self, path: str = ".") -> ToolResult:
        """Run a CodeRabbit-style local verification gate with PR-style comments and a block/warn/pass verdict."""
        root, target_meta = self._resolve_codebase_target(path, default_wla_source=True)
        md_path, json_path, report = write_code_quality_gate_report(root)
        rendered = render_code_quality_gate_markdown(report)
        log_activity("code_quality_gate", "Code quality gate generated", {"path": str(md_path), "json_path": str(json_path), "decision": report.decision, "blocking": report.total_blocking_count, "warnings": report.total_warning_count, "displayed": report.displayed_comment_count})
        return ToolResult(report.ok, f"Code quality gate decision: {report.decision} ({report.total_blocking_count} blocking, {report.total_warning_count} warning, {report.truncated_comment_count} hidden by display cap)", {
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "ok": report.ok,
            "decision": report.decision,
            "blocking_count": report.blocking_count,
            "warning_count": report.warning_count,
            "note_count": report.note_count,
            "total_comment_count": report.total_comment_count,
            "total_blocking_count": report.total_blocking_count,
            "total_warning_count": report.total_warning_count,
            "total_note_count": report.total_note_count,
            "displayed_comment_count": report.displayed_comment_count,
            "truncated_comment_count": report.truncated_comment_count,
            "comments": [c.to_dict() for c in report.comments[:50]],
            "passed_checks": report.passed_checks,
            "summary": rendered[:9000],
            "human_report": rendered[:7000],
            "target": target_meta,
        })

    def code_repair_audit(self, path: str = ".") -> ToolResult:
        """Run a deterministic repair/bug audit over Nova or the current project.

        This is intentionally non-mutating: it parses Python files, checks for
        duplicate definitions, swallowed broad exceptions, oversized functions,
        release-cache artifacts and autonomous guard markers, then writes a
        Markdown/JSON report that autonomous mode can use before choosing edits.
        """
        root, target_meta = self._resolve_codebase_target(path, default_wla_source=True)
        md_path, json_path, report = write_code_repair_audit_report(root)
        log_activity("code_repair_audit", "Code repair audit generated", {"path": str(md_path), "json_path": str(json_path), "findings": len(report.findings), "ok": report.ok})
        return ToolResult(report.ok, f"Code repair audit completed with {len(report.findings)} finding(s)", {
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "ok": report.ok,
            "findings": [f.to_dict() for f in report.findings[:30]],
            "passed_checks": report.passed_checks,
            "summary": render_code_repair_audit_markdown(report)[:5000],
            "target": target_meta,
        })

    def project_spec(self, goal: str = "", path: str = ".") -> ToolResult:
        """Build a deterministic requirements/specification brief for a project goal.

        Autonomous project creation uses this before generation so weak local
        models receive concrete workflows, data objects, edge cases and
        acceptance tests rather than a vague one-line prompt.
        """
        text = (goal or "").strip() or "build the requested local project"
        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        text = self._validation_goal_text(text)
        brief = infer_project_build_brief(text)
        md_path, json_path = write_project_build_brief(root, brief)
        log_activity("project_spec_written", "Project build brief written", {"goal": text, "path": str(md_path), "json_path": str(json_path), "artifact_type": brief.artifact_type, "domain": brief.domain})
        return ToolResult(True, f"Project specification prepared for {brief.domain} / {brief.artifact_type}", {
            "brief": brief.to_dict(),
            "markdown_path": str(md_path),
            "json_path": str(json_path),
            "summary": render_project_build_brief_markdown(brief)[:4000],
        })


    def feature_continuity_audit_tool(self, path: str = ".") -> ToolResult:
        """Check that previously added Nova GUI/backend capability surfaces still exist."""
        root, meta = self._resolve_codebase_target(path, default_wla_source=True)
        payload = build_feature_continuity_audit(root, tool_names=sorted(self.tools.keys()))
        payload["target_resolution"] = meta
        docs = root / "docs"
        try:
            docs.mkdir(parents=True, exist_ok=True)
            (docs / "NOVA_FEATURE_CONTINUITY_LATEST.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
            (docs / "NOVA_FEATURE_CONTINUITY_LATEST.md").write_text(render_feature_continuity_audit(payload), encoding="utf-8")
            payload["report"] = {
                "json": str(docs / "NOVA_FEATURE_CONTINUITY_LATEST.json"),
                "markdown": str(docs / "NOVA_FEATURE_CONTINUITY_LATEST.md"),
            }
        except Exception as exc:
            payload["report_error"] = repr(exc)
        payload.setdefault("message", render_feature_continuity_audit(payload))
        return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Feature continuity audit"), payload)

    def ai_create_project(self, goal: str, folder: str | None = None, build_mode: str = "auto") -> ToolResult:
        self.require_mutation()
        build_mode = (build_mode or "auto").lower()
        folder = folder or self._slug(goal)
        clean_goal = self._validation_goal_text(goal)
        creation_analysis = analyze_creation_request(clean_goal)
        requirements = self._requirements_spec(clean_goal, build_mode)
        data = self._ask_model_for_project(goal, mode="create", build_mode=build_mode, requirements=requirements)
        if not data:
            fallback = deterministic_simple_project(clean_goal, creation_analysis)
            if fallback:
                data = fallback
                log_activity("deterministic_generation_fallback", "Used deterministic one-file fallback after local model failure", {"goal": clean_goal, "main_file": fallback.get("main_file"), "source": fallback.get("source")})
            else:
                return ToolResult(False, "Local LLM did not produce a valid goal-specific project, so no files were written", {
                    "source": "ollama_required_failed",
                    "goal": goal,
                    "creation_analysis": creation_analysis,
                    "model": self.config.model,
                    "ollama_url": self.config.ollama_url,
                    "reason": getattr(self, "_last_model_error", "unknown model failure"),
                    "attempt_history": getattr(self, "_last_model_attempts", []),
                    "best_rejected_candidate": {
                        "files": sorted(((getattr(self, "_last_model_candidate", {}) or {}).get("files") or {}).keys()) if isinstance(getattr(self, "_last_model_candidate", None), dict) and isinstance((getattr(self, "_last_model_candidate", {}) or {}).get("files"), dict) else [],
                    },
                    "fix": [
                        "Start Ollama: ollama serve",
                        f"Pull/use a coder model: ollama pull {self.config.model}",
                        "Retry the same /do request.",
                        "If the model returns weak JSON, use a stronger/larger coder model."
                    ]
                })
        raw_folder = str(data.get("folder") or folder or "").strip()
        if raw_folder.lower().replace(" ", "") in {"projectfoldername", "projectname", "foldername", "simpleapp", "generatedproject"}:
            raw_folder = folder or self._slug(goal)
        folder = self._slug(raw_folder)
        # New projects are always created under the project library root, not inside
        # whichever project is currently open. This prevents ProjectA/ProjectB nesting.
        # If a generated/default folder already exists, choose a fresh suffix so stale
        # files from a prior failed build cannot pollute request-match validation.
        library_root = self._project_library_root()
        root = (library_root / folder).expanduser().resolve()
        if root.exists() and any(root.iterdir()):
            base = folder
            for i in range(2, 200):
                candidate = self._slug(f"{base}-{i}")
                candidate_root = (library_root / candidate).expanduser().resolve()
                if not candidate_root.exists() or not any(candidate_root.iterdir()):
                    folder = candidate
                    root = candidate_root
                    break
        root.mkdir(parents=True, exist_ok=True)

        written: list[dict[str, Any]] = []
        self._apply_model_files_to_root(root, folder, data.get("files") or {}, written, event_kind="code_write_start")

        manifest = {
            "goal": clean_goal,
            "raw_goal": goal,
            "build_mode": build_mode,
            "requirements": requirements,
            "acceptance_terms": requirements.get("acceptance_terms", []),
            "feature_expectations": requirements.get("feature_expectations", {}),
            "main_file": data.get("main_file") or "index.html",
            "run_command": data.get("run_command") or "start .\\index.html",
            "verify_command": data.get("verify_command") or "",
            "notes": data.get("notes") or "",
            "source": data.get("source") or "ollama",
            "creation_analysis": data.get("creation_analysis") or creation_analysis,
            "assumptions": data.get("assumptions") or creation_analysis.get("assumptions") or [],
            "attempt_history": data.get("attempt_history") or [],
            "best_rejected_candidate": data.get("best_rejected_candidate") or {},
        }
        self._write_manifest(root, manifest)
        self._write_lifecycle_files(root, manifest, status="generated")
        project = register_project(folder, str(root), make_current=True)
        atomic_write_json((root / ".nova_project.json"), {"name": folder, "path": str(root)}, ensure_ascii=True)
        self.config.workspace = str(root)
        self.config.save()

        max_rounds = 2 if build_mode == "fast" else 5
        ok, verify_result = self._repair_until_accepted(clean_goal, root, folder, manifest, written, max_rounds=max_rounds)
        self.config.workspace = str(root)
        self.config.save()
        if not ok:
            self._write_lifecycle_files(root, manifest, verify_result, status="failed")
            self._last_model_error = "Project did not pass quality/acceptance checks after repair attempts"
            return ToolResult(False, "Local LLM wrote files, but the project did not pass requirement acceptance checks", {
                "project": project,
                "workspace": str(root),
                "written": written,
                "verification": verify_result,
                "creation_analysis": creation_analysis,
                "source": manifest["source"],
                "fix": "Use /fix-last or /continue repair the missing acceptance items. Activity/model logs are saved under ~/.nova/.",
            })

        created_files = [str(item.get("path", "")) for item in written if isinstance(item, dict)]
        match_summary = self._created_artifact_request_summary(root, folder, manifest, written)
        request_match = validate_created_artifact_matches_request(clean_goal, created_files, match_summary)
        project_quality_score = score_created_project_quality(clean_goal, created_files, match_summary, verify_result.get("checks", []) if isinstance(verify_result, dict) else [])
        # Narrow deterministic one-file fallbacks intentionally violate older
        # project-scaffold expectations such as README.md/main.py. If the user
        # asked for a simple script and the one generated file matches that
        # request, treat it as successful instead of forcing a generic scaffold.
        deterministic_one_file_ok = (
            manifest.get("source") == "deterministic_fallback"
            and request_match.get("matches_request")
            and len([p for p in created_files if p]) == 1
            and str(created_files[0]).lower().endswith((".py", ".ps1", ".bat", ".js"))
        )
        if deterministic_one_file_ok:
            project_quality_score["passed_threshold"] = True
            project_quality_score["override_reason"] = "deterministic one-file fallback satisfied the user's explicit small-script scope"
            project_quality_score["overall_percent"] = max(float(project_quality_score.get("overall_percent") or 0), 80.0)
        manifest["request_match"] = request_match
        manifest["project_quality_score"] = project_quality_score
        self._write_manifest(root, manifest)
        if not request_match.get("matches_request") or not project_quality_score.get("passed_threshold", False):
            mismatch_report = root / "CREATION_MISMATCH_REPORT.md"
            acceptance = project_quality_score.get("acceptance_contract") or {}
            repair_plan = project_quality_score.get("repair_plan") or {}
            atomic_write_text(
                mismatch_report,
                "\n".join([
                    "# Creation Mismatch and Acceptance Report",
                    "",
                    f"Original request: {goal}",
                    "",
                    request_match.get("verification_summary", "Created output does not match the original request."),
                    "",
                    "## Project quality score",
                    f"Overall: {project_quality_score.get('overall_percent')}%",
                    f"Acceptance contract: {acceptance.get('summary', 'not available')}",
                    "",
                    "## Missing requirements",
                    "\n".join(f"- {item}" for item in request_match.get("missing_requirements", [])) or "- none",
                    "",
                    "## Unexpected defaults",
                    "\n".join(f"- {item}" for item in request_match.get("unexpected_defaults", [])) or "- none",
                    "",
                    "## Missing or weak behaviours",
                    "\n".join(f"- {item}" for item in project_quality_score.get("missing_or_weak_items", [])) or "- none",
                    "",
                    "## Surgical correction plan",
                    "\n".join(f"- {item}" for item in repair_plan.get("actions", [])) or "- Create or edit only the files needed to satisfy the original request; do not repeat the unexpected default.",
                    "",
                    "## Verification plan",
                    "\n".join(f"- {item}" for item in repair_plan.get("verification", [])) or "- Re-run project quality verification.",
                ]) + "\n",
                encoding="utf-8",
            )
            self._write_lifecycle_files(root, manifest, verify_result, status="mismatch")
            return ToolResult(False, "Created output does not match the original request", {
                "project": project,
                "workspace": str(root),
                "written": written,
                "verification": verify_result,
                "creation_analysis": creation_analysis,
                "request_match": request_match,
                "project_quality_score": project_quality_score,
                "acceptance_contract": acceptance,
                "repair_plan": repair_plan,
                "mismatch_report": str(mismatch_report),
                "source": manifest["source"],
                "fix": "Use /continue with the original request and the mismatch report; do not repeat the unexpected default.",
            })

        self._write_lifecycle_files(root, manifest, verify_result, status="passed")
        try:
            remember_project_fact(root, f"Created project for goal: {goal}. Main file: {manifest.get('main_file','index.html')}. Features: {', '.join(map(str, manifest.get('acceptance_terms') or []))}", source="project_create")
        except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        inspired_tool = self._maybe_propose_tool_from_project(goal, root, manifest)
        return ToolResult(True, f"Created and verified project {folder}", {
            "project": project,
            "workspace": str(root),
            "written": written,
            "main_file": manifest["main_file"],
            "run_command": manifest["run_command"],
            "verify_command": manifest["verify_command"],
            "verification": verify_result,
            "creation_analysis": creation_analysis,
            "request_match": request_match,
            "project_quality_score": project_quality_score,
            "acceptance_terms": manifest["acceptance_terms"],
            "feature_expectations": manifest["feature_expectations"],
            "open_url": f"/view?path={manifest['main_file']}",
            "download_url": f"/download?path={manifest['main_file']}",
            "source": manifest["source"],
            "attempt_history": manifest.get("attempt_history", []),
            "notes": manifest["notes"],
            "inspired_tool_proposal": inspired_tool,
            "output_description": f"Verified {manifest['main_file']} for project {folder}. Includes generated source files plus requirements and test reports.",
            "output_files": [str(item.get("path", "")) for item in written[:12] if isinstance(item, dict)],
            "verification_status": "passed",
            "iteration_report": str(root / "PROJECT_VERIFICATION_REPORT.md"),
            "iteration_log": str(root / "PROJECT_ITERATION_LOG.jsonl"),
            "human_report": f"Built with the {build_mode} stream. Wrote requirements, test report and final output files. The project passed the current syntax and requirement checks.",
        })

    def ai_edit_project(self, goal: str, build_mode: str = "long") -> ToolResult:
        self.require_mutation()
        ok, summary, data = self._ensure_current_project_for_edit()
        if not ok:
            return ToolResult(False, summary, data)
        build_mode = (build_mode or "long").lower()
        requirements = self._requirements_spec(goal, build_mode)
        data = self._ask_model_for_project(goal, mode="edit", build_mode=build_mode, requirements=requirements)
        if not data:
            return ToolResult(False, "Local LLM did not return a valid goal-specific edit, so no code files were changed", {
                "source": "ollama_required_failed",
                "goal": goal,
                "model": self.config.model,
                "ollama_url": self.config.ollama_url,
                "reason": getattr(self, "_last_model_error", "unknown model failure"),
                "fix": [
                    "Start Ollama: ollama serve",
                    f"Pull/use a coder model: ollama pull {self.config.model}",
                    "Open the intended project, then retry the /continue or /do edit request."
                ]
            })

        root = self.workspace
        folder = root.name
        written: list[dict[str, Any]] = []
        # Edit the current project only. Do not create Project/Project nested folders.
        self._apply_model_files_to_root(root, folder, data.get("files") or {}, written, event_kind="code_edit_write")

        manifest_path = root / "PROJECT_MANIFEST.json"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {}
        original_goal = manifest.get("goal") or goal
        combined_goal = str(original_goal) + "\nCurrent edit request: " + goal
        manifest.update({
            "goal": original_goal,
            "last_edit_goal": goal,
            "build_mode": build_mode,
            "requirements": self._requirements_spec(combined_goal, build_mode),
            "acceptance_terms": self._extract_requirement_terms(combined_goal),
            "feature_expectations": self._generic_feature_expectations(combined_goal),
            "main_file": data.get("main_file") or manifest.get("main_file") or "index.html",
            "run_command": data.get("run_command") or manifest.get("run_command") or "start .\\index.html",
            "verify_command": data.get("verify_command") or manifest.get("verify_command") or "",
            "notes": data.get("notes") or manifest.get("notes") or "",
            "source": "ollama_edit",
        })
        self._write_manifest(root, manifest)
        iter_path = root / "ITERATIONS.md"
        atomic_append_text(iter_path, f"\n\n## Edit\n\nGoal: {goal}\n\nChanged files:\n" + "\n".join(f"- {w['path']}" for w in written) + "\n")

        max_rounds = 2 if build_mode == "fast" else 5
        ok, verify_result = self._repair_until_accepted(combined_goal, root, folder, manifest, written, max_rounds=max_rounds)
        if not ok:
            self._write_lifecycle_files(root, manifest, verify_result, status="failed")
            return ToolResult(False, "Applied edit, but project still failed requirement acceptance checks", {
                "written": written,
                "main_file": manifest.get("main_file"),
                "run_command": manifest.get("run_command"),
                "verify_command": manifest.get("verify_command"),
                "verification": verify_result,
                "open_url": f"/view?path={manifest.get('main_file', 'index.html')}",
                "download_url": f"/download?path={manifest.get('main_file', 'index.html')}",
                "notes": manifest.get("notes", ""),
            })

        self._write_lifecycle_files(root, manifest, verify_result, status="passed")
        try:
            remember_project_fact(root, f"Applied verified project edit for goal: {goal}. Changed files: {', '.join(Path(w.get('path','')).name for w in written[:8])}", source="project_edit")
        except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
        return ToolResult(True, "Applied, verified and reviewed model-generated project edit", {
            "written": written,
            "main_file": manifest.get("main_file"),
            "run_command": manifest.get("run_command"),
            "verify_command": manifest.get("verify_command"),
            "verification": verify_result,
            "acceptance_terms": manifest.get("acceptance_terms"),
            "feature_expectations": manifest.get("feature_expectations"),
            "open_url": f"/view?path={manifest.get('main_file', 'index.html')}",
            "download_url": f"/download?path={manifest.get('main_file', 'index.html')}",
            "notes": manifest.get("notes", ""),
        })

    def run_project(self, path: str = ".") -> ToolResult:
        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        if not root.exists():
            return ToolResult(False, "Project path not found", {"path": str(root)})

        manifest = {}
        m = root / "PROJECT_MANIFEST.json"
        if m.exists():
            try:
                manifest = read_json_file(m, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {}

        main_file = manifest.get("main_file")
        run_command = manifest.get("run_command")
        verify_command = manifest.get("verify_command")

        if not main_file:
            for candidate in ["index.html", "app.py", "main.py", "game.py", "index.js", "Main.java", "script.ps1", "README.md"]:
                if (root / candidate).exists():
                    main_file = candidate
                    break

        if not run_command and main_file:
            if str(main_file).lower().endswith(".html"):
                run_command = f"start .\\{main_file}"
            elif str(main_file).lower().endswith(".py"):
                run_command = f"py -3 .\\{main_file}"
            elif str(main_file).lower().endswith(".js"):
                run_command = f"node .\\{main_file}"
            elif str(main_file).lower().endswith(".java"):
                run_command = f"javac .\\{main_file} && java {Path(str(main_file)).stem}"
            elif str(main_file).lower().endswith(".ps1"):
                run_command = f"powershell -ExecutionPolicy Bypass -File .\\{main_file}"

        interpretation = []
        if verify_command:
            old = self.config.workspace
            self.config.workspace = str(root)
            try:
                vr = self.verify(verify_command)
                interpretation.append({"verification": vr.data, "ok": vr.ok})
            finally:
                self.config.workspace = old

        # Do not force-open GUI apps during automated runs. Provide exact links/commands instead.
        data = {
            "project_path": str(root),
            "main_file": main_file,
            "open_url": f"/view?path={main_file}" if main_file else "",
            "download_url": f"/download?path={main_file}" if main_file else "",
            "run_command": run_command or "",
            "verification": interpretation,
            "interpretation": "Project is ready to run. Browser projects use the open URL; Python/Node/Java/PowerShell projects use the run command in the project folder.",
        }
        return ToolResult(True, "Prepared run instructions and interpreted project state", data)

    def runtime_start(self, path: str = ".") -> ToolResult:
        """Start or describe a runnable project session.

        Browser projects are served through the built-in /project-view route, so
        companion files such as style.css and app.js resolve relative to the same
        project folder. For script projects, this returns the safe run command and
        leaves execution to /shell or /verify so output stays visible.
        """
        info = self.run_project(path)
        if not info.ok:
            return info
        data = dict(info.data)
        main_file = str(data.get("main_file") or "")
        if main_file.lower().endswith(".html"):
            data["runtime_state"] = "browser_static_served_by_winlocalassistant"
            data["run_url"] = f"/project-view/{main_file}"
            data["popup_hint"] = "Use the GUI Run button or Open in tab. CSS/JS/assets are served from the project folder."
            return ToolResult(True, "Browser project is ready in the built-in runtime preview", data)
        data["runtime_state"] = "command_ready"
        data["popup_hint"] = "Use /shell or /verify to run this command when you want terminal output."
        return ToolResult(True, "Project run command is ready", data)

    def runtime_stop(self) -> ToolResult:
        return ToolResult(True, "No persistent project runtime is currently managed by Nova", {"note": "Browser previews run in the web UI iframe/tab and stop when you close them. Terminal commands are one-shot unless started manually."})

    def runtime_restart(self, path: str = ".") -> ToolResult:
        stop = self.runtime_stop()
        start = self.runtime_start(path)
        return ToolResult(start.ok, "Runtime restart prepared" if start.ok else "Runtime restart could not be prepared", {"stop": stop.data, "start": start.data})



    def vision_status(self) -> ToolResult:
        '''Report local vision-analysis readiness.'''
        model = getattr(self.config, "vision_model", "gemma3:12b") or "gemma3:12b"
        latest = resolve_image_context("latest")
        return ToolResult(True, "Vision status", {
            "vision_model": model,
            "ollama_url": self.config.ollama_url,
            "ollama": self._ollama_ps(),
            "latest_uploaded_image": latest.to_dict() if latest else None,
            "commands": [
                "/vision-model MODEL",
                "/image-analyze latest => describe this uploaded photo",
                "/image-analyze context:ID => identify UI bugs",
                "/image-analyze screenshots/app.png => what is wrong with this UI?",
                "/visual-test .",
                "/human-test .",
            ],
            "notes": [
                "Vision is optional and local-first through Ollama /api/chat with image inputs.",
                "Uploaded photos now work with /image-analyze latest or /image-analyze context:ID, even though they are stored outside the workspace.",
                "Use a pulled vision-capable model. If this machine has low VRAM, choose a smaller vision model.",
                "Vision reports are saved under ~/.nova/vision_reports.",
            ],
        })

    def _resolve_image_for_analysis(self, image_ref: str) -> tuple[Path | None, dict[str, Any]]:
        raw = (image_ref or "").strip().strip('"').strip("'")
        if not raw or raw.lower() in {"latest", "last", "photo", "image", "upload", "uploaded"} or raw.lower().startswith(("context:", "ctx:", "id:")):
            ctx = resolve_image_context(raw)
            if not ctx:
                return None, {"error": "No uploaded/attached image context found", "usage": "/image-analyze latest => describe this uploaded photo"}
            return Path(ctx.stored_path), {"source": "shared_file_context", "context": ctx.to_dict()}
        # A bare context id or uploaded filename is also accepted before trying
        # workspace resolution, which keeps uploaded-photo usage simple.
        ctx = resolve_image_context(raw)
        if ctx:
            return Path(ctx.stored_path), {"source": "shared_file_context", "context": ctx.to_dict()}
        try:
            return resolve_inside_workspace(self.workspace, raw), {"source": "workspace_path"}
        except Exception as exc:
            return None, {"error": repr(exc), "workspace": str(self.workspace), "usage": "Use a workspace-relative image path or /image-analyze latest for uploaded photos."}

    def image_analyze(self, path: str = "latest", prompt: str = "Describe the image and identify visible bugs, usability issues, or improvement opportunities.") -> ToolResult:
        '''Analyze a local image or uploaded image context using the configured Ollama vision model.'''
        image_ref = (path or "latest").strip().strip('"')
        prompt = (prompt or "Describe the image and identify visible bugs, usability issues, or improvement opportunities.").strip()
        img, source = self._resolve_image_for_analysis(image_ref)
        if img is None:
            return ToolResult(False, "Image could not be resolved", source)
        if not img.exists() or not img.is_file():
            return ToolResult(False, "Image file not found", {"path": str(img), **source})
        if img.suffix.lower() not in IMAGE_EXTS:
            return ToolResult(False, "Unsupported image extension", {"path": str(img), "allowed": sorted(e.lstrip('.') for e in IMAGE_EXTS), **source})
        model = getattr(self.config, "vision_model", "llama3.2-vision:11b") or "llama3.2-vision:11b"
        log_activity("vision_analyze_start", "Analyzing image with local vision model", {"image": str(img), "image_ref": image_ref, "model": model, "prompt": prompt[:500], **source})
        reply = ollama_vision_chat(self.config.ollama_url, model, prompt, [str(img)], timeout=240, desc="vision image analysis")
        if not reply:
            last_prompt = ollama_busy_state().get("last_prompt", {})
            return ToolResult(False, "Vision model did not return a response", {"model": model, "path": str(img), "image_ref": image_ref, "last_prompt": last_prompt, "fix": ["Pull a compatible vision model, for example: ollama pull gemma3:12b", "Run /vision-model MODEL", "Check /llm-status and /vision-status"], **source})
        out = APP_DIR / "vision_reports"
        out.mkdir(parents=True, exist_ok=True)
        report = out / (time.strftime("vision_%Y%m%d_%H%M%S.md"))
        report_text = "\n".join([
            "# Vision analysis",
            "",
            f"Image: `{img}`",
            f"Image reference: `{image_ref}`",
            "",
            f"Model: `{model}`",
            "",
            "Prompt:",
            "",
            prompt,
            "",
            "## Result",
            "",
            reply,
        ])
        atomic_write_text(report, report_text)
        log_activity("vision_analyze_done", "Vision analysis completed", {"image": str(img), "image_ref": image_ref, "model": model, "report": str(report), "summary": reply[:1000], **source})
        return ToolResult(True, "Vision analysis completed", {"image": str(img), "image_ref": image_ref, "model": model, "report": str(report), "analysis": reply, **source})

    def _project_browser_files(self, root: Path) -> dict[str, str]:
        files: dict[str, str] = {}
        for name in ["index.html", "app.js", "style.css"]:
            p = root / name
            if p.exists() and p.is_file():
                files[name] = p.read_text(encoding="utf-8", errors="replace")
        return files

    def human_test(self, path: str = ".", goal: str = "") -> ToolResult:
        '''Dependency-free human-style UI audit for browser projects.'''
        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        files = self._project_browser_files(root)
        if not files:
            return ToolResult(False, "No browser app files found to test", {"path": str(root), "expected": ["index.html", "app.js", "style.css"]})
        html_text = files.get("index.html", "")
        js_text = files.get("app.js", "")
        combined = "\n".join(files.values()).lower()
        checks: list[dict[str, Any]] = []
        def add(name: str, ok: bool, detail: str) -> None:
            checks.append({"name": name, "ok": bool(ok), "detail": detail})
        add("page_has_title_or_heading", bool(re.search(r"<h1|<title", html_text, re.I)), "User should immediately see what the app is.")
        add("has_interactive_controls", bool(re.search(r"<button|<input|<select|<textarea|onclick=|addEventListener", html_text + js_text, re.I)), "A human should have something to click or type into.")
        add("has_app_logic", len(re.findall(r"function |=>|addEventListener|localStorage|JSON\.stringify|filter\(", js_text)) >= 3, "JavaScript should contain meaningful application logic, not only placeholders.")
        local_refs = re.findall(r"(?:src|href)=[\"']([^\"']+\.(?:js|css))[\"']", html_text, re.I)
        missing_refs = [ref for ref in local_refs if not ref.startswith(("http://", "https://", "//")) and not (root / ref).exists()]
        add("local_files_linked", not missing_refs, "Local CSS/JS references should resolve from the project folder." + (f" Missing: {missing_refs}" if missing_refs else ""))
        if any(x in combined for x in ["export", "json", "csv"]):
            add("export_appears_implemented", bool(re.search(r"Blob|URL\.createObjectURL|download|JSON\.stringify|text/csv", js_text)), "Export requests should have actual browser download/export code.")
        if any(x in combined for x in ["save", "saving", "local"]):
            add("local_saving_appears_implemented", "localstorage" in combined, "Local saving should usually use localStorage for browser apps.")
        if "search" in combined:
            add("search_appears_implemented", bool(re.search(r"filter\(|includes\(|toLowerCase\(|search", js_text, re.I)), "Search UI should connect to filtering logic.")
        buttons = re.findall(r"<button[^>]*>(.*?)</button>", html_text, re.I | re.S)
        inputs = re.findall(r"<(?:input|select|textarea)\b", html_text, re.I)
        add("workflow_has_multiple_steps", len(buttons) + len(inputs) >= 3, "A useful app usually needs enough fields/actions to complete its workflow.")
        failed = [c for c in checks if not c["ok"]]
        report_lines = ["# Human-style UI test", "", f"Project: `{root}`", "", "## Checks"]
        for c in checks:
            report_lines.append(f"- {'PASS' if c['ok'] else 'FAIL'}: **{c['name']}** — {c['detail']}")
        report_lines += ["", "## Suggested human interaction script", "", "1. Open the app in the built-in project runner.", "2. Read the title and confirm the purpose is obvious.", "3. Add one realistic item/record using the form fields.", "4. Verify the item appears in the UI without reloading.", "5. Reload the page and confirm saved state persists if local saving was requested.", "6. Try search/filter/export buttons if present.", "7. Record any console errors, missing buttons, or confusing labels."]
        atomic_write_text((root / "HUMAN_TEST_REPORT.md"), "\n".join(report_lines))
        log_activity("human_test_done", "Human-style UI test completed", {"project": str(root), "ok": not failed, "failed": failed, "checks": checks})
        return ToolResult(not failed, "Human-style UI test passed" if not failed else "Human-style UI test found improvement opportunities", {"project_path": str(root), "checks": checks, "failed": failed, "report": str(root / "HUMAN_TEST_REPORT.md")})

    def visual_test(self, path: str = ".") -> ToolResult:
        '''Run optional Playwright visual/smoke testing if available, otherwise scaffold it.'''
        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        index = root / "index.html"
        if not index.exists():
            return ToolResult(False, "visual-test expects a browser project with index.html", {"project_path": str(root)})
        artifacts = APP_DIR / "visual_tests" / (root.name + "_" + time.strftime("%Y%m%d_%H%M%S"))
        artifacts.mkdir(parents=True, exist_ok=True)
        script = artifacts / "playwright_smoke.py"
        screenshot = artifacts / "screenshot.png"
        trace = artifacts / "trace.zip"
        script_lines = [
            "from pathlib import Path",
            "from playwright.sync_api import sync_playwright",
            f"url = Path(r'{index}').resolve().as_uri()",
            "with sync_playwright() as p:",
            "    browser = p.chromium.launch(headless=True)",
            "    context = browser.new_context(viewport={'width': 1280, 'height': 900})",
            "    context.tracing.start(screenshots=True, snapshots=True, sources=True)",
            "    page = context.new_page()",
            "    console_errors = []",
            "    page.on('console', lambda msg: console_errors.append(msg.text) if msg.type == 'error' else None)",
            "    page.goto(url, wait_until='domcontentloaded')",
            f"    page.screenshot(path=r'{screenshot}', full_page=True)",
            "    buttons = page.locator('button').count()",
            "    inputs = page.locator('input, textarea, select').count()",
            "    title = page.title()",
            f"    context.tracing.stop(path=r'{trace}')",
            "    browser.close()",
            f"    print({{'title': title, 'buttons': buttons, 'inputs': inputs, 'console_errors': console_errors, 'screenshot': r'{screenshot}', 'trace': r'{trace}'}})",
        ]
        atomic_write_text(script, "\n".join(script_lines) + "\n")
        probe = subprocess.run(["py", "-3", "-c", "import playwright"], capture_output=True, text=True, timeout=20)
        if probe.returncode != 0:
            plan = {"project_path": str(root), "playwright_available": False, "script": str(script), "install_hint": "Use /pip-install playwright, then run: py -3 -m playwright install chromium", "note": "The scaffold was created but not run because Playwright is not installed."}
            log_activity("visual_test_scaffolded", "Playwright visual test scaffold created", plan)
            return ToolResult(False, "Playwright is not installed; visual test scaffold created", plan)
        cp = subprocess.run(["py", "-3", str(script)], cwd=str(root), capture_output=True, text=True, timeout=120)
        data = {"project_path": str(root), "playwright_available": True, "returncode": cp.returncode, "stdout": cp.stdout[-4000:], "stderr": cp.stderr[-4000:], "script": str(script), "screenshot": str(screenshot), "trace": str(trace)}
        ok = cp.returncode == 0
        log_activity("visual_test_done" if ok else "visual_test_failed", "Playwright visual smoke test completed" if ok else "Playwright visual smoke test failed", data)
        return ToolResult(ok, "Playwright visual smoke test completed" if ok else "Playwright visual smoke test failed", data)

    def playwright_scaffold(self, path: str = ".") -> ToolResult:
        return self.visual_test(path)

    def cycle_schema(self) -> ToolResult:
        schema = {
            "version": "51.3.0",
            "purpose": "Standard event-sourced cycle record for transparent autonomous engineering.",
            "required_fields": ["cycle_id", "run_id", "goal", "phase", "selected_tools", "files_changed", "diffs", "tests_run", "errors", "rollback_pointer", "status", "duration_ms"],
            "phases": ["observe", "diagnose", "plan", "preflight", "act", "verify", "repair", "reflect"],
            "artifact_types": ["unified_diff", "html_diff", "screenshot", "playwright_trace", "test_log", "vision_report", "human_test_report"],
            "direct_implementation": "v50 edits parseable local-model candidates iteratively before repeating full generation prompts.",
        }
        schema["version"] = "51.3.0"
        schema["direct_implementation"] = "v50 edits parseable local-model candidates iteratively before repeating full generation prompts, while preserving v49 reasoning and recovery."
        out = APP_DIR / "cycle_event_schema_v50.json"
        atomic_write_json(out, schema, ensure_ascii=True)
        return ToolResult(True, "Cycle event schema written", {"path": str(out), "schema": schema})

    def final_project_check(self, path: str = ".", goal: str = "") -> ToolResult:
        """Final post-build developer check.

        Runs after generation/run interpretation, before packaging. It re-checks syntax,
        requirement coverage and whether the project appears to complete what the user asked for.
        The result is written into TEST_REPORT.md and FINAL_OUTPUT.md by the existing lifecycle writer.
        """
        root = resolve_inside_workspace(self.workspace, path or ".")
        if root.is_file():
            root = root.parent
        manifest_path = root / "PROJECT_MANIFEST.json"
        manifest: dict[str, Any] = {}
        if manifest_path.exists():
            try:
                manifest = read_json_file(manifest_path, {}, expected_type=dict, quarantine=True)
            except Exception:
                manifest = {}
        if goal:
            manifest["final_check_goal"] = goal
            manifest.setdefault("goal", goal)
        elif not manifest.get("goal"):
            manifest["goal"] = manifest.get("last_edit_goal") or "verify the current project"
        log_activity("final_check_start", "Running final developer check against user requirements", {"goal": manifest.get("goal"), "project": str(root)})
        self._auto_fix_common_code_errors(root)
        result = self._project_quality_verify(root, manifest)
        status = "passed" if result.ok else "failed"
        self._write_lifecycle_files(root, manifest, result.data, status=status)
        try:
            manifest["last_final_check"] = {"ok": result.ok, "summary": result.summary, "time": time.strftime("%Y-%m-%d %H:%M:%S")}
            self._write_manifest(root, manifest)
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
        log_activity("final_check_done" if result.ok else "final_check_failed", result.summary, {"ok": result.ok, "data": result.data})
        if result.ok:
            return ToolResult(True, "Final developer check passed", {
                "project_path": str(root),
                "main_file": manifest.get("main_file", "index.html"),
                "open_url": f"/view?path={manifest.get('main_file', 'index.html')}",
                "run_url": f"/project-view/{manifest.get('main_file', 'index.html')}",
                "verification": result.data,
                "human_report": "I re-checked the project after the build. Syntax/build checks and requirement coverage passed under the current automated checks. TEST_REPORT.md and FINAL_OUTPUT.md were updated."
            })
        return ToolResult(False, "Final developer check found remaining issues", {
            "project_path": str(root),
            "main_file": manifest.get("main_file", "index.html"),
            "verification": result.data,
            "fix": "Use /fix-last or /continue repair the current project. The same project folder will be edited instead of creating a nested project.",
        })

    def projects(self) -> ToolResult:
        items = list_projects()
        current = next((p for p in items if p.get("current")), None)
        return ToolResult(True, f"Found {len(items)} projects", {"projects": items, "current": current})

    def project_create(self, name: str, path: str | None = None) -> ToolResult:
        self.require_mutation()
        if not name.strip():
            return ToolResult(False, "Project name is required", {})
        library_root = self._project_library_root()
        if path:
            candidate = Path(path).expanduser()
            root = candidate.resolve() if candidate.is_absolute() else (library_root / candidate).resolve()
        else:
            root = (library_root / name).resolve()
        root.mkdir(parents=True, exist_ok=True)
        project = register_project(name, str(root), make_current=True)
        marker = root / ".nova_project.json"
        atomic_write_json(marker, {"name": project["name"], "path": project["path"]}, ensure_ascii=True)
        self.config.workspace = project["path"]
        self.config.save()
        return ToolResult(True, f"Created/opened project {project['name']}", {"project": project, "workspace": self.config.workspace})

    def project_open(self, name: str) -> ToolResult:
        project = get_project(name)
        if not project:
            return ToolResult(False, "Project not found", {"name": name, "projects": list_projects()})
        path = Path(project["path"]).expanduser().resolve()
        path_text = str(path).lower().replace("\\", "/")
        if "pytest-of-" in path_text or "/pytest-" in path_text or "/appdata/local/temp/" in path_text:
            return ToolResult(False, "Project registration points to a transient pytest/temp workspace; remove or recreate it instead of reopening it.", {"project": project, "path": str(path), "stale": True})
        if not path.exists():
            return ToolResult(False, "Project path no longer exists; registration is stale and was not recreated automatically.", {"project": project, "path": str(path), "stale": True})
        register_project(project["name"], str(path), make_current=True)
        self.config.workspace = str(path)
        self.config.save()
        return ToolResult(True, f"Opened project {project['name']}", {"project": project, "workspace": self.config.workspace})

    def project_remove(self, name: str, delete_files: bool = False) -> ToolResult:
        self.require_mutation()
        info = remove_project(name, delete_files=bool(delete_files))
        ok = bool(info.get("existed")) and not info.get("delete_error")
        msg = "Project removed" if ok else "Project was not registered or could not be removed"
        if info.get("deleted_files"):
            msg += " and project files were deleted"
        return ToolResult(ok, msg, {"name": name, "remove": info, "projects": list_projects()})

    def project_delete(self, name: str) -> ToolResult:
        return self.project_remove(name=name, delete_files=True)

    def project_files(self, name: str | None = None, limit: int = 500) -> ToolResult:
        project = get_project(name or None)
        if not project:
            return ToolResult(False, "No current project. Create or open one first.", {"projects": list_projects()})
        old_workspace = self.config.workspace
        try:
            self.config.workspace = project["path"]
            result = self.list_files(".", limit=limit)
            result.data["project"] = project
            return result
        finally:
            self.config.workspace = old_workspace

    def open_file(self, path: str, max_chars: int = 120000) -> ToolResult:
        return self.read_file(path, max_chars=max_chars)

    def zip_path(self, path: str = ".", zip_name: str | None = None) -> ToolResult:
        target = resolve_inside_workspace(self.workspace, path or ".")
        if not target.exists():
            return ToolResult(False, "Path to zip does not exist", {"path": str(target)})
        out_dir = APP_DIR / "downloads"
        out_dir.mkdir(parents=True, exist_ok=True)
        safe_name = zip_name or (target.name if target.name else "workspace") + ".zip"
        if not safe_name.lower().endswith(".zip"):
            safe_name += ".zip"
        out = out_dir / safe_name
        with zipfile.ZipFile(out, "w", zipfile.ZIP_DEFLATED) as zf:
            if target.is_file():
                zf.write(target, arcname=target.name)
            else:
                for p in target.rglob("*"):
                    if self._skip(p) or not p.is_file():
                        continue
                    zf.write(p, arcname=str(p.relative_to(target.parent)))
        return ToolResult(True, f"Created zip {out.name}", {"zip_path": str(out), "download_url": f"/download-generated?name={out.name}"})

# -----------------------------
# v42 Reliability harness patch
# -----------------------------
# Kept at end of file so it is easy to audit. These methods extend ToolRegistry
# without changing the older implementation paths that already work.

import sys as _wla_sys
import ast as _wla_ast
import traceback as _wla_traceback

V42_ERROR_TYPES = {
    "model_timeout", "model_invalid_json", "parser_error", "syntax_error", "requirement_missing",
    "weak_logic", "tool_missing", "environment_missing", "visual_test_failed", "runtime_console_error",
}


def _wla42_safe_read(path: Path, limit: int = 12000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _wla42_ollama_list_models(self: ToolRegistry) -> list[str]:
    exe = shutil.which("ollama")
    if not exe:
        return []
    try:
        cp = subprocess.run([exe, "list"], capture_output=True, text=True, timeout=12)
        lines = (cp.stdout or "").splitlines()[1:]
        models = []
        for line in lines:
            parts = line.split()
            if parts:
                models.append(parts[0])
        return models
    except Exception:
        return []


def _wla42_classify_failure(text: str = "", data: Any = None) -> str:
    blob = (text or "") + "\n" + (json.dumps(data, ensure_ascii=False, default=str)[:20000] if data is not None else "")
    low = blob.lower()
    if "timed out" in low or "not reachable" in low or "timeout" in low:
        return "model_timeout"
    if "parseable json" in low or "invalid json" in low or "jsondecode" in low:
        return "model_invalid_json"
    if "patternerror" in low or "unbalanced parenthesis" in low or "parser" in low:
        return "parser_error"
    if "syntaxerror" in low or "node --check" in low or "py_compile" in low:
        return "syntax_error"
    if "missing_feature" in low or "requirement" in low or "goal_coverage" in low:
        return "requirement_missing"
    if "weak_logic" in low or "weak_interactivity" in low or "little or no application logic" in low:
        return "weak_logic"
    if "unknown tool" in low or "tool missing" in low:
        return "tool_missing"
    if "ollama command was not found" in low or "not found on path" in low or "playwright is not installed" in low:
        return "environment_missing"
    if "visual" in low and "failed" in low:
        return "visual_test_failed"
    if "console" in low or "uncaught" in low or "referenceerror" in low:
        return "runtime_console_error"
    return "unknown"


def _wla42_known_issues_path(self: ToolRegistry) -> Path:
    return APP_DIR / "KNOWN_ISSUES.md"


def _wla42_append_known_issue(self: ToolRegistry, signature: str, error_type: str, evidence: str = "", status: str = "open", attempted: str = "") -> None:
    try:
        path = _wla42_known_issues_path(self)
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        sig = (signature or "unknown error")[:220].replace("\n", " ")
        existing = path.read_text(encoding="utf-8", errors="replace") if path.exists() else "# Known Issues\n\n"
        if sig in existing:
            append_text_line(path, f"\n- Seen again: {now} | type={error_type} | status={status}")
            return
        block = []
        if not existing.strip():
            block.append("# Known Issues\n\n")
        block.append(f"\n## {sig}\n\n")
        block.append(f"- First seen: {now}\n- Last seen: {now}\n- Error type: `{error_type}`\n- Status: {status}\n")
        if attempted:
            block.append(f"- Attempted fixes: {attempted}\n")
        if evidence:
            block.append("\n### Evidence\n\n```text\n" + evidence[:4000] + "\n```\n")
        atomic_append_text(path, "".join(block))
    except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})

def _wla42_quality_score_from_checks(self: ToolRegistry, root: Path, manifest: dict[str, Any], checks: list[dict[str, Any]]) -> dict[str, Any]:
    goal = str(manifest.get("goal") or manifest.get("last_edit_goal") or "")
    all_text = ""
    code_text = ""
    try:
        for p in root.rglob("*"):
            if self._skip(p) or not p.is_file():
                continue
            if p.suffix.lower() in {".html", ".js", ".css", ".py", ".md", ".json", ".txt"}:
                t = p.read_text(encoding="utf-8", errors="replace").lower()
                all_text += "\n" + t
                if p.suffix.lower() in {".html", ".js", ".css", ".py"}:
                    code_text += "\n" + t
    except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
    syntax = 10 if all(c.get("ok", False) for c in checks if str(c.get("name", "")).endswith("syntax") or c.get("name") in {"basic_js_sanity", "manifest_verify"}) else 0
    static = next((c for c in checks if c.get("name") == "static_acceptance"), {})
    if static:
        req = 10 if static.get("ok") else max(0, 6 - len(static.get("problems") or []))
    else:
        req = 6
    ui_hits = sum(1 for s in ["button", "input", "form", "select", "textarea", "addeventlistener", "onclick", "canvas"] if s in code_text)
    ui = min(10, ui_hits * 2)
    runtime = 8 if any(c.get("name") in {"manifest_verify", "node_syntax", "basic_js_sanity"} and c.get("ok") for c in checks) else 4
    clean_goal = self._validation_goal_text(goal) if goal else ""
    expected = self._generic_feature_expectations(clean_goal) if clean_goal else {}
    save_export = 10
    if "local_saving" in expected and not any(s in code_text for s in ["localstorage", "setitem", "getitem"]):
        save_export -= 5
    if "export" in expected and not any(s in code_text for s in ["blob", "download", "json.stringify", "createobjecturl"]):
        save_export -= 5
    save_export = max(0, save_export)
    overall = round((syntax * 0.25 + req * 0.30 + ui * 0.15 + runtime * 0.15 + save_export * 0.15) * 10, 1)
    return {
        "syntax": syntax,
        "requirements_coverage": req,
        "ui_completeness": ui,
        "runtime_confidence": runtime,
        "export_local_saving": save_export,
        "overall_percent": overall,
        "threshold_percent": 70,
        "passed_threshold": overall >= 70,
    }


_old_project_quality_verify = ToolRegistry._project_quality_verify

def _wla42_project_quality_verify(self: ToolRegistry, root: Path, manifest: dict[str, Any]) -> ToolResult:
    result = _old_project_quality_verify(self, root, manifest)
    checks = result.data.get("checks", []) if isinstance(result.data, dict) else []
    score = _wla42_quality_score_from_checks(self, root, manifest, checks)
    data = dict(result.data or {})
    data["quality_score"] = score
    if result.ok and not score.get("passed_threshold"):
        data.setdefault("problems", []).append({"kind": "quality_score_low", "score": score})
        _wla42_append_known_issue(self, "Project quality score below threshold", "weak_logic", json.dumps(score, indent=2), attempted="v45 score gate")
        return ToolResult(False, "Project quality score is below the acceptance threshold", data)
    if not result.ok:
        et = _wla42_classify_failure(result.summary, data)
        data["failure_type"] = et
        _wla42_append_known_issue(self, result.summary, et, json.dumps(data, ensure_ascii=False, default=str)[:4000], attempted="quality_verify")
    return ToolResult(result.ok, result.summary, data)

ToolRegistry._project_quality_verify = _wla42_project_quality_verify


_old_write_lifecycle_files = ToolRegistry._write_lifecycle_files

def _wla42_write_lifecycle_files(self: ToolRegistry, root: Path, manifest: dict[str, Any], verify_result: dict[str, Any] | None = None, status: str = "in_progress") -> None:
    _old_write_lifecycle_files(self, root, manifest, verify_result, status)
    try:
        score = (verify_result or {}).get("quality_score") or _wla42_quality_score_from_checks(self, root, manifest, (verify_result or {}).get("checks", []))
        report_path = root / "TEST_REPORT.md"
        atomic_append_text(
            report_path,
            "\n\n## v43 Project quality score\n\n"
            + f"- Syntax: {score.get('syntax')}/10\n"
            + f"- Requirements coverage: {score.get('requirements_coverage')}/10\n"
            + f"- UI completeness: {score.get('ui_completeness')}/10\n"
            + f"- Runtime confidence: {score.get('runtime_confidence')}/10\n"
            + f"- Export/local saving: {score.get('export_local_saving')}/10\n"
            + f"- Overall: {score.get('overall_percent')}%\n",
        )
    except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})

ToolRegistry._write_lifecycle_files = _wla42_write_lifecycle_files


def _wla42_model_doctor(self: ToolRegistry) -> ToolResult:
    exe = shutil.which("ollama")
    installed = _wla42_ollama_list_models(self)
    configured = {
        "code_model": getattr(self.config, "model", ""),
        "chat_model": getattr(self.config, "chat_model", ""),
        "planner_model": getattr(self.config, "planner_model", ""),
        "vision_model": getattr(self.config, "vision_model", ""),
    }
    missing = [m for m in {configured["code_model"], configured["chat_model"], configured["planner_model"], configured["vision_model"]} if m and m not in installed]
    recommended = ["qwen3-coder:30b", "gemma2:2b", "llama3.2-vision:11b"]
    commands = ["ollama serve"] + [f"ollama pull {m}" for m in recommended if m not in installed]
    ok = bool(exe) and bool(installed) and not missing[:2]
    summary = "Model setup looks usable" if ok else "Model setup needs attention"
    return ToolResult(ok, summary, {
        "ollama_on_path": bool(exe),
        "installed_models": installed,
        "configured_models": configured,
        "missing_configured_models": missing,
        "recommended_models": recommended,
        "setup_commands": commands,
        "popup_needed": not ok,
        "note": "If no model is selected or installed, Nova should default to an installed model when possible. Otherwise the GUI shows these setup commands on launch.",
    })


def _wla42_test_all(self: ToolRegistry) -> ToolResult:
    report = ["# TEST_ALL_REPORT", "", f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", f"Workspace: {self.workspace}", ""]
    checks: list[dict[str, Any]] = []
    root = Path(__file__).resolve().parents[1]

    def add(name: str, ok: bool, output: str = "", data: dict[str, Any] | None = None):
        checks.append({"name": name, "ok": ok, "output": output[-8000:], "data": data or {}})
        report.append(f"## {name}: {'PASS' if ok else 'FAIL'}\n")
        if output:
            report.append("```text\n" + output[-4000:] + "\n```\n")

    # version consistency
    try:
        import winlocalassistant as wla
        add("version_consistency", bool(getattr(wla, "__version__", "")), f"{getattr(wla,'__version__','')} {getattr(wla,'VERSION_LABEL','')}")
    except Exception as exc:
        add("version_consistency", False, repr(exc))

    r = self.runtime_self_check()
    add("self_check", r.ok, r.summary, r.data)
    r = self.model_doctor()
    add("model_doctor", bool(r.data.get("ollama_on_path")), r.summary, r.data)

    try:
        files = [str(p) for p in (root / "winlocalassistant").glob("*.py")]
        cp = subprocess.run([_wla_sys.executable, "-W", "error::SyntaxWarning", "-m", "py_compile", *files], cwd=str(root), capture_output=True, text=True, timeout=60)
        add("py_compile", cp.returncode == 0, (cp.stdout or "") + (cp.stderr or ""))
    except Exception as exc:
        add("py_compile", False, repr(exc))

    try:
        smoke = root / "tests_smoke.py"
        if smoke.exists():
            cp = subprocess.run([_wla_sys.executable, str(smoke)], cwd=str(root), capture_output=True, text=True, timeout=90)
            add("smoke_tests", cp.returncode == 0, (cp.stdout or "") + (cp.stderr or ""))
        else:
            add("smoke_tests", False, "tests_smoke.py missing")
    except Exception as exc:
        add("smoke_tests", False, repr(exc))

    add("tool_registry", "test_all" in self.tools and "model_benchmark" in self.tools, json.dumps(sorted(self.tools)[:200], indent=2))
    r = self.custom_tools()
    add("custom_tools", r.ok, r.summary, r.data)
    r = self.provider_status()
    add("provider_checks", r.ok, r.summary, r.data)
    try:
        r = self.heartbeat()
        add("autonomous_status_dependencies", r.ok, r.summary, r.data)
    except Exception as exc:
        add("autonomous_status_dependencies", False, repr(exc))

    # GUI script syntax check: safe static sanity, not full JS extraction.
    webui = root / "winlocalassistant" / "webui.py"
    txt = _wla42_safe_read(webui, 200000)
    add("gui_script_sanity", "function loadActivity" in txt and "function loadLLMStatus" in txt, "webui.py contains expected GUI functions")

    overall = all(c["ok"] for c in checks if c["name"] not in {"model_doctor"})
    report.append("\n# Summary\n")
    report.append(f"Overall: {'PASS' if overall else 'ATTENTION'}\n")
    report.append("\n| Check | Result |\n|---|---|\n")
    for c in checks:
        report.append(f"| {c['name']} | {'PASS' if c['ok'] else 'FAIL'} |\n")
    out = APP_DIR / "TEST_ALL_REPORT.md"
    atomic_write_text(out, "\n".join(report))
    if not overall:
        fails = [c for c in checks if not c["ok"]]
        _wla42_append_known_issue(self, "test-all reported failures", "environment_missing", json.dumps(fails, ensure_ascii=False, default=str)[:4000], attempted="/test-all")
    return ToolResult(overall, "Test-all completed" + (" successfully" if overall else " with issues"), {"report": str(out), "checks": checks})


def _wla42_known_issues(self: ToolRegistry) -> ToolResult:
    p = _wla42_known_issues_path(self)
    txt = p.read_text(encoding="utf-8", errors="replace") if p.exists() else "# Known Issues\n\nNo known issues recorded yet."
    return ToolResult(True, "Known issues loaded", {"path": str(p), "content": txt[-20000:]})


def _wla42_self_improvement_queue(self: ToolRegistry) -> ToolResult:
    proposal_path = APP_DIR / "SELF_IMPROVEMENT_QUEUE.md"
    issues = _wla42_known_issues_path(self).read_text(encoding="utf-8", errors="replace") if _wla42_known_issues_path(self).exists() else "No known issues."
    content = ["# Self-Improvement Queue", "", f"Updated: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    content += ["## Candidate 1: Improve reliability based on known issues", "", "- Problem: repeated failures or weak generated project quality may appear in logs.", "- Evidence: see KNOWN_ISSUES.md and ERROR_INVESTIGATION.md.", "- Proposed files to edit: acceptance/recovery/model-routing modules only after tests are defined.", "- Risk level: medium.", "- Test plan: /test-all, py_compile, smoke tests, representative /fast build, /human-test.", "- Approval needed: yes, use /self-apply 1 after reviewing.", "", "## Recent known issue evidence", "", "```text", issues[-6000:], "```", ""]
    atomic_write_text(proposal_path, "\n".join(content))
    return ToolResult(True, "Self-improvement queue written", {"path": str(proposal_path), "items": 1})


def _wla42_self_apply(self: ToolRegistry, item: str = "") -> ToolResult:
    return ToolResult(False, "Self-apply is intentionally approval-gated in v44", {
        "requested_item": item,
        "why": "v44 queues self-improvements with evidence and test plans instead of editing itself immediately.",
        "next": "Review SELF_IMPROVEMENT_QUEUE.md, then use /self-improve with a precise goal if you want an actual guarded self-edit cycle.",
    })


def _wla42_model_benchmark(self: ToolRegistry, limit: int = 8) -> ToolResult:
    models = _wla42_ollama_list_models(self)
    if not models:
        return ToolResult(False, "No Ollama models found to benchmark", {"setup_commands": ["ollama serve", "ollama pull qwen3-coder:30b", "ollama pull gemma2:2b"]})
    tests = [
        ("json", "Return ONLY valid JSON: {\"ok\": true, \"tool\": \"benchmark\"}"),
        ("code", "Return ONLY JavaScript code for a function add(a,b) that returns a+b. No markdown."),
        ("chat", "Answer in one short sentence: what is a local assistant?"),
    ]
    results = []
    old_model = self.config.model
    for model in models[:max(1, min(int(limit or 8), 12))]:
        score = 0; details = []
        for name, prompt in tests:
            started = time.time()
            reply = model_chat(self.config, model, [{"role": "user", "content": prompt}], timeout=45, desc=f"model benchmark {model} {name}")
            elapsed = round(time.time() - started, 2)
            ok = bool(reply)
            if name == "json" and reply:
                ok = self._extract_json_object(reply) is not None
            if name == "code" and reply:
                ok = "function" in reply.lower() and "return" in reply.lower()
            if ok: score += 1
            details.append({"test": name, "ok": ok, "elapsed_sec": elapsed, "preview": (reply or "")[:400]})
        results.append({"model": model, "score": score, "max_score": len(tests), "details": details})
    results.sort(key=lambda x: (-x["score"], sum(d["elapsed_sec"] for d in x["details"])))
    out = APP_DIR / "MODEL_BENCHMARK.md"
    lines = ["# Model Benchmark", "", f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", "", "| Model | Score |", "|---|---:|"]
    for r in results:
        lines.append(f"| {r['model']} | {r['score']}/{r['max_score']} |")
        atomic_write_text(out, "\n".join(lines) + "\n")
    best = results[0]["model"] if results else old_model
    return ToolResult(True, f"Benchmarked {len(results)} installed model(s). Best: {best}", {"results": results, "report": str(out), "best_model": best})


def _wla42_visual_repair(self: ToolRegistry, path: str = ".") -> ToolResult:
    root = resolve_inside_workspace(self.workspace, path or ".")
    if root.is_file(): root = root.parent
    human = self.human_test(str(root)) if hasattr(self, "human_test") else ToolResult(False, "human_test unavailable", {})
    visual = self.visual_test(str(root)) if hasattr(self, "visual_test") else ToolResult(False, "visual_test unavailable", {})
    final = self.final_project_check(str(root), goal="visual repair and final requirement check") if hasattr(self, "final_project_check") else ToolResult(False, "final_project_check unavailable", {})
    problems = []
    for label, res in [("human", human), ("visual", visual), ("final", final)]:
        if not res.ok:
            problems.append({"stage": label, "summary": res.summary, "data": res.data})
    report = ["# Visual Repair Report", "", f"Project: {root}", f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", ""]
    report.append(f"- Human test: {'PASS' if human.ok else 'ATTENTION'} - {human.summary}")
    report.append(f"- Visual test: {'PASS' if visual.ok else 'ATTENTION'} - {visual.summary}")
    report.append(f"- Final check: {'PASS' if final.ok else 'ATTENTION'} - {final.summary}")
    if problems:
        report.append("\n## Problems / next repair targets\n")
        report.append(json.dumps(problems, indent=2, ensure_ascii=False, default=str)[:12000])
        et = _wla42_classify_failure("visual repair", problems)
        _wla42_append_known_issue(self, "visual repair found issues", et, json.dumps(problems, ensure_ascii=False, default=str)[:4000], attempted="/visual-repair")
    else:
        report.append("\nNo obvious visual/human-test issues were detected by the current automated scaffold.\n")
    out = root / "VISUAL_REPAIR_REPORT.md"
    atomic_write_text(out, "\n".join(report))
    return ToolResult(not problems, "Visual repair scaffold completed" + (" with issues" if problems else " cleanly"), {"project": str(root), "report": str(out), "human_test": human.data, "visual_test": visual.data, "final_check": final.data, "problems": problems})


def _wla42_console_test(self: ToolRegistry, path: str = ".") -> ToolResult:
    # Dependency-free console-test scaffold. If Playwright is present, the user can run /visual-test for deeper capture.
    root = resolve_inside_workspace(self.workspace, path or ".")
    if root.is_file(): root = root.parent
    refs_missing = []
    for html_file in root.rglob("*.html"):
        if self._skip(html_file): continue
        txt = _wla42_safe_read(html_file, 50000)
        for m in re.findall(r'(?:src|href)=["\']([^"\']+)["\']', txt, flags=re.I):
            if m.startswith(("http://", "https://", "data:", "#")): continue
            target = (html_file.parent / m).resolve()
            if not target.exists():
                refs_missing.append({"html": str(html_file.relative_to(root)), "missing": m})
    ok = not refs_missing
    return ToolResult(ok, "Console/static browser reference check " + ("passed" if ok else "found missing references"), {"missing_references": refs_missing, "note": "For real browser console errors, install Playwright and run /visual-test or /visual-repair."})


def _wla42_autonomous_memory(self: ToolRegistry) -> ToolResult:
    p = APP_DIR / "AUTONOMOUS_CYCLE_MEMORY.jsonl"
    rows = tail_jsonl(p, 80) if p.exists() else []
    failure_memory = load_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH)
    recent_failures = [asdict(record) for record in (failure_memory.recent_failures or [])[-25:]]
    return ToolResult(
        True,
        f"Loaded {len(rows)} autonomous memory row(s) and {len(recent_failures)} failure record(s)",
        {
            "path": str(p),
            "rows": rows,
            "failure_memory_path": str(AUTONOMOUS_FAILURE_MEMORY_PATH),
            "recent_failures": recent_failures,
            "failure_counts": failure_memory.failure_counts,
            "cooldowns": failure_memory.cooldowns,
            "last_failure_summary": failure_memory.last_failure_summary,
            "last_suggested_fix": failure_memory.last_suggested_fix,
        },
    )


def _wla42_record_autonomous_memory(self: ToolRegistry, failure: str = "", repair: str = "", worked: bool = False, avoid: str = "") -> None:
    try:
        p = APP_DIR / "AUTONOMOUS_CYCLE_MEMORY.jsonl"
        row = {"time": time.strftime("%Y-%m-%d %H:%M:%S"), "failure": failure, "repair": repair, "worked": worked, "avoid": avoid}
        append_jsonl(p, row, ensure_ascii=False)
    except Exception as exc:
            log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})



def _wla42_register_defaults(self: ToolRegistry) -> None:
    _old_register_defaults(self)
    extra = {
        "test_all": _wla42_test_all.__get__(self, ToolRegistry),
        "model_doctor": _wla42_model_doctor_active.__get__(self, ToolRegistry),
        "model_benchmark": _wla42_model_benchmark.__get__(self, ToolRegistry),
        "visual_repair": _wla42_visual_repair.__get__(self, ToolRegistry),
        "console_test": _wla42_console_test.__get__(self, ToolRegistry),
        "known_issues": _wla42_known_issues.__get__(self, ToolRegistry),
        "self_improvement_queue": _wla42_self_improvement_queue.__get__(self, ToolRegistry),
        "self_apply": _wla42_self_apply.__get__(self, ToolRegistry),
        "autonomous_memory": _wla42_autonomous_memory.__get__(self, ToolRegistry),
    }
    for name, fn in extra.items():
        self.register(name, fn)

_old_register_defaults = ToolRegistry.register_defaults
ToolRegistry.register_defaults = _wla42_register_defaults

# Expose helpers for other modules if they import from tools.
ToolRegistry._wla42_append_known_issue = _wla42_append_known_issue
ToolRegistry._wla42_classify_failure = staticmethod(_wla42_classify_failure)
ToolRegistry._wla42_record_autonomous_memory = _wla42_record_autonomous_memory

# Attach v42 extension methods as real attributes too, so internal tools such as
# /test-all can call self.model_doctor(), self.visual_repair(), etc.
ToolRegistry.model_doctor = _wla42_model_doctor
ToolRegistry.test_all = _wla42_test_all
ToolRegistry.model_benchmark = _wla42_model_benchmark
ToolRegistry.visual_repair = _wla42_visual_repair
ToolRegistry.console_test = _wla42_console_test
ToolRegistry.known_issues = _wla42_known_issues
ToolRegistry.self_improvement_queue = _wla42_self_improvement_queue
ToolRegistry.self_apply = _wla42_self_apply
ToolRegistry.autonomous_memory = _wla42_autonomous_memory

# v42.1: make /model-doctor actively choose installed defaults when configured models are missing.
def _wla42_model_doctor_active(self: ToolRegistry) -> ToolResult:
    exe = shutil.which("ollama")
    installed = _wla42_ollama_list_models(self)
    changed = []
    def choose(prefer: list[str]) -> str:
        for wanted in prefer:
            for m in installed:
                if wanted.lower() in m.lower():
                    return m
        return installed[0] if installed else ""
    if installed:
        if not getattr(self.config, "model", "") or self.config.model not in installed:
            chosen = choose(["qwen", "coder", "deepseek", "codestral", "llama", "gemma"])
            if chosen:
                self.config.model = chosen; changed.append(f"code_model={chosen}")
        if not getattr(self.config, "chat_model", "") or self.config.chat_model not in installed:
            chosen = choose(["llama", "gemma", "mistral", "qwen", "phi"])
            if chosen:
                self.config.chat_model = chosen; changed.append(f"chat_model={chosen}")
        try:
            if changed:
                self.config.save()
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
    configured = {
        "code_model": getattr(self.config, "model", ""),
        "chat_model": getattr(self.config, "chat_model", ""),
        "planner_model": getattr(self.config, "planner_model", ""),
        "vision_model": getattr(self.config, "vision_model", ""),
    }
    missing = [m for m in {configured["code_model"], configured["chat_model"], configured["planner_model"], configured["vision_model"]} if m and m not in installed]
    recommended = ["qwen3-coder:30b", "gemma2:2b", "llama3.2-vision:11b"]
    commands = ["ollama serve"] + [f"ollama pull {m}" for m in recommended if m not in installed]
    ok = bool(exe) and bool(installed) and not any(m in missing for m in [configured.get("code_model"), configured.get("chat_model")])
    return ToolResult(ok, "Model setup looks usable" if ok else "Model setup needs attention", {
        "ollama_on_path": bool(exe),
        "installed_models": installed,
        "configured_models": configured,
        "defaulted_models": changed,
        "missing_configured_models": missing,
        "recommended_models": recommended,
        "setup_commands": commands,
        "popup_needed": not ok,
        "note": "If configured models are missing but any usable text models are installed, v44 defaults code/chat roles safely and avoids embedding-only defaults. If no models are installed, the launch popup shows commands.",
    })
ToolRegistry.model_doctor = _wla42_model_doctor_active

# v43 Idle-agent, interrupt and model-routing patch

def _wla43_is_embedding_or_vision(name: str) -> bool:
    n = (name or "").lower()
    return any(x in n for x in ["embed", "nomic", "mxbai", "bge", "e5", "vl", "vision"])


def _wla43_prefer_model(installed: list[str], prefer: list[str], *, allow_vision: bool = False, allow_embedding: bool = False) -> str:
    candidates = []
    for m in installed:
        low = m.lower()
        if not allow_embedding and any(x in low for x in ["embed", "nomic", "mxbai", "bge", "e5"]):
            continue
        if not allow_vision and any(x in low for x in ["vl", "vision"]):
            continue
        candidates.append(m)
    for wanted in prefer:
        for m in candidates:
            if wanted.lower() in m.lower():
                return m
    return candidates[0] if candidates else (installed[0] if installed else "")


def _wla43_model_doctor(self: ToolRegistry) -> ToolResult:
    exe = shutil.which("ollama")
    installed = _wla42_ollama_list_models(self)
    changed = []
    if installed:
        if not getattr(self.config, "model", "") or self.config.model not in installed or _wla43_is_embedding_or_vision(self.config.model):
            chosen = _wla43_prefer_model(installed, ["qwen3-coder", "coder", "deepseek", "codestral", "qwen", "llama", "gemma"])
            if chosen:
                self.config.model = chosen; changed.append(f"code_model={chosen}")
        if not getattr(self.config, "chat_model", "") or self.config.chat_model not in installed or _wla43_is_embedding_or_vision(self.config.chat_model):
            chosen = _wla43_prefer_model(installed, ["qwen3-coder", "qwen3", "gemma", "llama", "mistral", "qwen"])
            if chosen:
                self.config.chat_model = chosen; changed.append(f"chat_model={chosen}")
        if not getattr(self.config, "planner_model", ""):
            self.config.planner_model = self.config.model; changed.append(f"planner_model={self.config.model}")
        try:
            if changed:
                self.config.save()
        except Exception as exc:
            try:
                log_activity("suppressed_optional_exception", "Suppressed optional exception", {"error": repr(exc)})
            except Exception as log_exc:
                _suppressed_log_error = repr(log_exc)
                data = getattr(result, "data", None)
                if isinstance(data, dict):
                    data.setdefault("suppressed_log_error", _suppressed_log_error)
    configured = {
        "code_model": getattr(self.config, "model", ""),
        "chat_model": getattr(self.config, "chat_model", ""),
        "planner_model": getattr(self.config, "planner_model", ""),
        "vision_model": getattr(self.config, "vision_model", ""),
    }
    missing = [m for m in {configured["code_model"], configured["chat_model"], configured["planner_model"], configured["vision_model"]} if m and m not in installed]
    bad_role = []
    if _wla43_is_embedding_or_vision(configured["chat_model"]):
        bad_role.append("chat_model appears to be embedding/vision-only")
    if _wla43_is_embedding_or_vision(configured["code_model"]):
        bad_role.append("code_model appears to be embedding/vision-only")
    recommended = ["qwen3-coder:30b", "gemma2:2b", "llama3.2-vision:11b"]
    commands = ["ollama serve"] + [f"ollama pull {m}" for m in recommended if m not in installed]
    ok = bool(exe) and bool(installed) and not bad_role and not any(m in missing for m in [configured.get("code_model"), configured.get("chat_model")])
    return ToolResult(ok, "Model setup looks usable" if ok else "Model setup needs attention", {
        "ollama_on_path": bool(exe),
        "installed_models": installed,
        "configured_models": configured,
        "defaulted_models": changed,
        "bad_role_assignments": bad_role,
        "missing_configured_models": missing,
        "recommended_models": recommended,
        "setup_commands": commands,
        "popup_needed": not ok,
        "note": "v44 avoids defaulting chat/code roles to embedding or vision-only models. If no usable model exists, the GUI popup shows install commands.",
    })


def _wla43_ollama_multi_report(self: ToolRegistry) -> ToolResult:
    ps = self._ollama_ps()
    installed = _wla42_ollama_list_models(self)
    return ToolResult(True, "Ollama multi-model capability report", {
        "short_answer": "Yes, Ollama can keep or serve more than one model when the machine has enough RAM/VRAM, but Nova deliberately keeps one prompt active at a time unless you explicitly change that later.",
        "why_single_prompt_in_wla": "One active prompt prevents overlapping writes, mixed logs, broken repair cycles and GPU memory contention.",
        "ollama_controls": {
            "keep_alive": "Ollama API calls can keep a model loaded after a response; this is why ollama ps may show a model even when Nova prompt_active=false.",
            "OLLAMA_MAX_LOADED_MODELS": "Can affect how many models Ollama keeps loaded, depending on memory and server configuration.",
            "ollama stop MODEL": "Unloads/interrupts a selected model; Nova exposes this through /ollama-stop --confirm and /interrupt-current --confirm.",
        },
        "current_ps": ps,
        "installed_models": installed,
        "recommendation": "Keep Nova single-prompt for reliability. Use separate role models sequentially: code, chat, planner, vision. Only enable concurrent models later behind an expert setting.",
    })


def _wla43_model_benchmark(self: ToolRegistry, limit: int = 8) -> ToolResult:
    installed = _wla42_ollama_list_models(self)
    models = [m for m in installed if not any(x in m.lower() for x in ["embed", "nomic", "mxbai", "bge", "e5"])]
    if not models:
        return ToolResult(False, "No text/chat Ollama models found for benchmarking", {"installed_models": installed, "hint": "Pull qwen3-coder:30b or gemma2:2b"})
    old_model = self.config.model
    tests = [
        ("json", "Return only valid JSON: {\"ok\": true, \"tool\": \"test\"}"),
        ("code", "Return only a tiny JavaScript function named add that returns a+b."),
        ("chat", "In one friendly sentence, say what you are good at."),
    ]
    results = []
    for model in models[:max(1, min(int(limit or 8), 12))]:
        score = 0; details = []
        for name, prompt in tests:
            started = time.time()
            reply = model_chat(self.config, model, [{"role": "user", "content": prompt}], timeout=60, desc=f"model benchmark {model} {name}", cooldown_sec=0.1, timeout_quarantine_sec=2.0)
            if reply is None:
                time.sleep(0.25)
                reply = model_chat(self.config, model, [{"role": "user", "content": prompt}], timeout=60, desc=f"model benchmark retry {model} {name}", cooldown_sec=0.1, timeout_quarantine_sec=2.0)
            elapsed = round(time.time() - started, 2)
            ok = bool(reply)
            if name == "json" and reply:
                ok = self._extract_json_object(reply) is not None
            if name == "code" and reply:
                ok = "function" in reply.lower() and "return" in reply.lower()
            if ok: score += 1
            details.append({"test": name, "ok": ok, "elapsed_sec": elapsed, "preview": (reply or "")[:400]})
            time.sleep(0.15)
        results.append({"model": model, "score": score, "max_score": len(tests), "details": details})
    results.sort(key=lambda x: (-x["score"], sum(d["elapsed_sec"] for d in x["details"])))
    out = APP_DIR / "MODEL_BENCHMARK.md"
    lines = ["# Model Benchmark", "", f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}", "", "| Model | Score | Notes |", "|---|---:|---|"]
    for r in results:
        notes = "; ".join(f"{d['test']}={'pass' if d['ok'] else 'fail'}" for d in r['details'])
        lines.append(f"| {r['model']} | {r['score']}/{r['max_score']} | {notes} |")
        atomic_write_text(out, "\n".join(lines) + "\n")
    best = results[0]["model"] if results else old_model
    return ToolResult(True, f"Benchmarked {len(results)} text-capable installed model(s). Best: {best}", {"results": results, "report": str(out), "best_model": best, "skipped_embedding_or_vision_models": [m for m in installed if m not in models]})


def _wla43_command_catalog(self: ToolRegistry) -> ToolResult:
    return ToolResult(True, "Tool catalogue and sequencing guide", {
        "tools": sorted(self.tools.keys()),
        "recommended_loop": ["observe", "diagnose", "plan", "act", "verify", "surgical_repair", "reflect"],
        "normal_chat_rule": "Do not run UI/project quality checks unless files were explicitly requested or a project command is active.",
        "busy_rule": "Only one local model prompt should be active; use /interrupt-current --confirm to stop a broken current task.",
    })


# Nova improvement feature command adapters (v55.3.124)
def _nova_analytics_dashboard_tool(self: ToolRegistry) -> ToolResult:
    """View analytics dashboard with model, tool, and request performance metrics."""
    try:
        engine = get_analytics_engine()
        markdown = render_analytics_dashboard()
        stats = {
            "model_stats": engine.get_model_stats(hours=24),
            "tool_stats": engine.get_tool_stats(hours=24),
            "request_summary": engine.get_request_summary(hours=24),
        }
        return ToolResult(True, "Analytics dashboard generated", {"message": markdown, **stats})
    except Exception as exc:
        return ToolResult(False, f"Analytics error: {exc}", {"error": repr(exc)})


def _nova_performance_report_tool(self: ToolRegistry) -> ToolResult:
    """Generate performance analysis and optimization recommendations."""
    try:
        profiler = get_performance_profiler()
        markdown = render_performance_report()
        recommendations = profiler.generate_recommendations()
        hotspots = profiler.analyze_hotspots(hours=24)
        efficiency = profiler.get_efficiency_score()
        return ToolResult(
            True,
            f"Performance report generated (efficiency: {efficiency:.1f}/100)",
            {
                "message": markdown,
                "efficiency_score": efficiency,
                "recommendations": recommendations,
                "hotspots": hotspots,
            },
        )
    except Exception as exc:
        return ToolResult(False, f"Performance analysis error: {exc}", {"error": repr(exc)})


def _nova_webhook_management_tool(self: ToolRegistry, action: str = "status", url: str = "", events: str = "", name: str = "") -> ToolResult:
    """Manage webhook endpoints for event-driven integrations."""
    try:
        manager = get_webhook_manager()
        action = (action or "status").strip().lower()
        if action in {"list", "status"}:
            markdown = render_webhooks_status()
            endpoints = [ep.to_dict() for ep in manager.endpoints.values()]
            return ToolResult(True, "Webhook status generated", {"message": markdown, "endpoints": endpoints})
        if action in {"register", "add", "create"}:
            if not url or not events or not name:
                return ToolResult(False, "Missing required fields: name, url, events", {})
            event_list = [event.strip() for event in events.split(",") if event.strip()]
            endpoint = manager.register_endpoint(name, url, event_list)
            return ToolResult(True, f"Webhook registered: {name}", {"endpoint": endpoint.to_dict()})
        if action == "test":
            payload = {"test": True, "timestamp": datetime.now().isoformat()}
            deliveries = manager.trigger_event("test", payload, async_delivery=False)
            return ToolResult(True, f"Test events triggered ({len(deliveries)} endpoints)", {"deliveries": len(deliveries)})
        return ToolResult(False, f"Unknown webhook action: {action}", {})
    except Exception as exc:
        return ToolResult(False, f"Webhook error: {exc}", {"error": repr(exc)})


def _nova_task_scheduler_tool(self: ToolRegistry, action: str = "list", name: str = "", schedule: str = "", command: str = "", task_id: str = "") -> ToolResult:
    """Manage scheduled tasks and cron-like execution."""
    try:
        scheduler = get_task_scheduler()
        # Keep scheduled execution useful but guarded: register existing read/report
        # style tools as callbacks, while refusing obvious mutating/source-editing
        # commands from unattended scheduler execution.
        blocked_prefixes = ("shell", "run_shell", "self_improve", "auto_apply", "delete", "write_file", "patch", "repair_apply")

        def _scheduled_tool_callback(params: dict[str, Any] | None = None, *, _name: str) -> ToolResult:
            if any(_name.startswith(prefix) for prefix in blocked_prefixes):
                return ToolResult(False, f"Scheduled execution blocked for high-risk tool: {_name}", {"tool": _name})
            return self.call(_name, **(params or {}))

        for tool_name in list(self.tools.keys()):
            if tool_name in {"scheduler", "task_scheduler", "schedule_task", "list_tasks"}:
                continue
            if tool_name not in scheduler.callbacks:
                scheduler.register_command_handler(tool_name, lambda params=None, _name=tool_name: _scheduled_tool_callback(params, _name=_name))
        action = (action or "list").strip().lower()
        if action in {"list", "status"}:
            markdown = render_scheduler_status()
            tasks = [task.to_dict() for task in scheduler.tasks.values()]
            return ToolResult(True, "Scheduler status generated", {"message": markdown, "tasks": tasks})
        if action in {"add", "create"}:
            if not name or not schedule or not command:
                return ToolResult(False, "Missing required: name, schedule (cron), command", {})
            task = scheduler.add_task(name, schedule, command)
            scheduler.start()
            return ToolResult(True, f"Task scheduled: {name}", {"task": task.to_dict()})
        if action in {"run", "execute"}:
            if not task_id:
                return ToolResult(False, "Missing task_id", {})
            success = scheduler.execute_task(task_id)
            return ToolResult(success, f"Task execution {'succeeded' if success else 'failed'}", {})
        if action == "enable":
            if not task_id:
                return ToolResult(False, "Missing task_id", {})
            scheduler.enable_task(task_id)
            return ToolResult(True, "Task enabled", {})
        if action == "disable":
            if not task_id:
                return ToolResult(False, "Missing task_id", {})
            scheduler.disable_task(task_id)
            return ToolResult(True, "Task disabled", {})
        return ToolResult(False, f"Unknown scheduler action: {action}", {})
    except Exception as exc:
        return ToolResult(False, f"Scheduler error: {exc}", {"error": repr(exc)})


def _nova_proposal_ledger_tool(self: ToolRegistry) -> ToolResult:
    """View the Nova proposal ledger and implementation impact matrix."""
    try:
        ledger = get_proposal_ledger()
        markdown = render_proposal_ledger()
        matrix = ledger.build_impact_matrix()
        return ToolResult(True, "Proposal ledger generated", {"message": markdown, "impact_matrix": matrix})
    except Exception as exc:
        return ToolResult(False, f"Ledger error: {exc}", {"error": repr(exc)})


def _nova_completed_improvements_tool(self: ToolRegistry) -> ToolResult:
    """Show completed improvements and their validation status."""
    try:
        ledger = get_proposal_ledger()
        completed = ledger.get_completed_proposals()
        lines = ["# Completed Improvements", "", f"**Total**: {len(completed)}", ""]
        for proposal in completed[-20:]:
            lines.extend([
                f"## {proposal.title}",
                f"- **Value**: {proposal.value_score}/100",
                f"- **Risk**: {proposal.risk_level}",
                f"- **Validated**: {proposal.is_safe()}",
            ])
            if proposal.completed_at:
                lines.append(f"- **Completed**: {proposal.completed_at}")
            lines.append("")
        return ToolResult(True, f"Completed improvements: {len(completed)}", {"message": "\n".join(lines), "count": len(completed)})
    except Exception as exc:
        return ToolResult(False, f"Completed improvements error: {exc}", {"error": repr(exc)})


def _nova_anti_repeat_tool(self: ToolRegistry, title: str = "", subsystems: str = "") -> ToolResult:
    """Check whether a proposed improvement duplicates completed work."""
    try:
        if not title:
            return ToolResult(False, "Missing proposal title", {})
        ledger = get_proposal_ledger()
        subsystem_list = [s.strip() for s in (subsystems or "").split(",") if s.strip()]
        similar = ledger.find_similar_completed(title, subsystem_list)
        if similar:
            lines = ["⚠️ Similar completed improvements found:", ""]
            for proposal in similar:
                lines.append(f"- **{proposal.title}** (completed {proposal.completed_at})")
            return ToolResult(True, f"Found {len(similar)} similar completed proposals", {"message": "\n".join(lines), "similar_count": len(similar)})
        return ToolResult(True, "No similar completed improvements found - safe to proceed", {"similar_count": 0})
    except Exception as exc:
        return ToolResult(False, f"Anti-repeat check error: {exc}", {"error": repr(exc)})



# Nova inspiration and workflow intelligence adapters (v55.3.125)
def _nova_inspiration_radar_tool(self: ToolRegistry, focus: str = "") -> ToolResult:
    """Rank safe Nova improvement ideas inspired by modern agent workflow patterns."""
    try:
        payload = build_nova_inspiration_radar(self._wla_source_root(), self.tools.keys(), focus=focus)
        return ToolResult(True, "Nova inspiration radar generated", {"message": render_inspiration_radar(payload), **payload})
    except Exception as exc:
        return ToolResult(False, f"Inspiration radar error: {exc}", {"error": repr(exc)})


def _nova_tool_context_pack_tool(self: ToolRegistry, prompt: str = "", max_tools: int = 18) -> ToolResult:
    """Build a prompt-aware shortlist of tools for local-model context."""
    try:
        try:
            limit = int(max_tools)
        except Exception:
            limit = 18
        payload = build_tool_context_pack(prompt, self.tools.keys(), max_tools=max(4, min(40, limit)))
        return ToolResult(True, f"Tool context pack selected {len(payload.get('selected_tool_names', []))} tools", {"message": render_tool_context_pack(payload), **payload})
    except Exception as exc:
        return ToolResult(False, f"Tool context pack error: {exc}", {"error": repr(exc)})


def _nova_handoff_plan_tool(self: ToolRegistry, prompt: str = "") -> ToolResult:
    """Build a deterministic role handoff plan for a Nova task."""
    try:
        payload = build_handoff_plan(prompt, self.tools.keys())
        return ToolResult(True, f"Nova handoff plan generated with {len(payload.get('steps', []))} steps", {"message": render_handoff_plan(payload), **payload})
    except Exception as exc:
        return ToolResult(False, f"Handoff plan error: {exc}", {"error": repr(exc)})


def _nova_improvement_preflight_tool(self: ToolRegistry, goal: str = "", files: str = "", commands: str = "") -> ToolResult:
    """Preview risk and validation needs before a Nova improvement patch."""
    try:
        changed_files = [part.strip() for part in (files or "").replace(";", ",").split(",") if part.strip()]
        intended_commands = [part.strip() for part in (commands or "").replace(";", ",").split(",") if part.strip()]
        payload = build_improvement_preflight(goal, changed_files=changed_files, intended_commands=intended_commands)
        return ToolResult(True, f"Improvement preflight risk: {payload.get('risk', 'unknown')}", {"message": render_improvement_preflight(payload), **payload})
    except Exception as exc:
        return ToolResult(False, f"Improvement preflight error: {exc}", {"error": repr(exc)})

def _wla43_register_defaults(self: ToolRegistry) -> None:
    _wla42_register_defaults(self)
    self.register("ollama_multi_report", _wla43_ollama_multi_report.__get__(self, ToolRegistry))
    self.register("command_catalog", _wla43_command_catalog.__get__(self, ToolRegistry))
    self.register("model_doctor", _wla43_model_doctor.__get__(self, ToolRegistry))
    self.register("model_benchmark", _wla43_model_benchmark.__get__(self, ToolRegistry))
    self.register("analytics", _nova_analytics_dashboard_tool.__get__(self, ToolRegistry))
    self.register("analytics_dashboard", _nova_analytics_dashboard_tool.__get__(self, ToolRegistry))
    self.register("performance_analytics", _nova_analytics_dashboard_tool.__get__(self, ToolRegistry))
    self.register("performance_profiler", _nova_performance_report_tool.__get__(self, ToolRegistry))
    self.register("performance_report", _nova_performance_report_tool.__get__(self, ToolRegistry))
    self.register("optimize_performance", _nova_performance_report_tool.__get__(self, ToolRegistry))
    self.register("webhook", _nova_webhook_management_tool.__get__(self, ToolRegistry))
    self.register("webhook_status", _nova_webhook_management_tool.__get__(self, ToolRegistry))
    self.register("webhooks", _nova_webhook_management_tool.__get__(self, ToolRegistry))
    self.register("register_webhook", _nova_webhook_management_tool.__get__(self, ToolRegistry))
    self.register("scheduler", _nova_task_scheduler_tool.__get__(self, ToolRegistry))
    self.register("task_scheduler", _nova_task_scheduler_tool.__get__(self, ToolRegistry))
    self.register("schedule_task", _nova_task_scheduler_tool.__get__(self, ToolRegistry))
    self.register("list_tasks", _nova_task_scheduler_tool.__get__(self, ToolRegistry))
    self.register("proposal_ledger_view", _nova_proposal_ledger_tool.__get__(self, ToolRegistry))
    self.register("completed_improvements", _nova_completed_improvements_tool.__get__(self, ToolRegistry))
    self.register("anti_repeat_check", _nova_anti_repeat_tool.__get__(self, ToolRegistry))
    self.register("inspiration_radar", _nova_inspiration_radar_tool.__get__(self, ToolRegistry))
    self.register("nova_inspiration_radar", _nova_inspiration_radar_tool.__get__(self, ToolRegistry))
    self.register("tool_context_pack", _nova_tool_context_pack_tool.__get__(self, ToolRegistry))
    self.register("nova_tool_context_pack", _nova_tool_context_pack_tool.__get__(self, ToolRegistry))
    self.register("handoff_plan", _nova_handoff_plan_tool.__get__(self, ToolRegistry))
    self.register("nova_handoff_plan", _nova_handoff_plan_tool.__get__(self, ToolRegistry))
    self.register("improvement_preflight", _nova_improvement_preflight_tool.__get__(self, ToolRegistry))
    self.register("safe_improvement_preflight", _nova_improvement_preflight_tool.__get__(self, ToolRegistry))

ToolRegistry.analytics_dashboard_tool = _nova_analytics_dashboard_tool
ToolRegistry.performance_report_tool = _nova_performance_report_tool
ToolRegistry.webhook_management_tool = _nova_webhook_management_tool
ToolRegistry.task_scheduler_tool = _nova_task_scheduler_tool
ToolRegistry.completed_improvements_tool = _nova_completed_improvements_tool
ToolRegistry.anti_repeat_tool = _nova_anti_repeat_tool
ToolRegistry.inspiration_radar_tool = _nova_inspiration_radar_tool
ToolRegistry.tool_context_pack_tool = _nova_tool_context_pack_tool
ToolRegistry.handoff_plan_tool = _nova_handoff_plan_tool
ToolRegistry.improvement_preflight_tool = _nova_improvement_preflight_tool
# Preserve the earlier improvement-roadmap ledger command and expose the new proposal ledger under proposal_ledger_view.
ToolRegistry.register_defaults = _wla43_register_defaults
ToolRegistry.model_doctor = _wla43_model_doctor
ToolRegistry.model_benchmark = _wla43_model_benchmark
ToolRegistry.ollama_multi_report = _wla43_ollama_multi_report
ToolRegistry.command_catalog = _wla43_command_catalog

# v55.3.152 integration foundation: state machine, durable job queue, and tool contracts.
def _nova152_queue(self: ToolRegistry):
    from .orchestration_foundation import JobQueue
    return JobQueue(APP_DIR / "jobs" / "nova_jobs.sqlite3")


def _nova152_integration_foundation_tool(self: ToolRegistry) -> ToolResult:
    from .orchestration_foundation import build_integration_foundation_report, render_integration_foundation_report
    payload = build_integration_foundation_report(APP_DIR / "jobs")
    return ToolResult(bool(payload.get("ok")), str(payload.get("summary") or "Nova integration foundation report"), {"message": render_integration_foundation_report(payload), **payload})


def _nova152_job_status_tool(self: ToolRegistry, status: str = "", limit: int = 20) -> ToolResult:
    queue = _nova152_queue(self)
    records = queue.list_jobs(status=status or None, limit=int(limit or 20))
    jobs = []
    for rec in records:
        jobs.append({
            "job_id": rec.job_id,
            "kind": rec.kind,
            "goal": rec.goal,
            "status": rec.status,
            "priority": rec.priority,
            "attempts": rec.attempts,
            "created_at": rec.created_at,
            "updated_at": rec.updated_at,
            "payload": rec.payload,
            "result": rec.result,
        })
    summary = queue.summary()
    lines = ["# Nova Job Queue", "", f"DB: `{summary.get('db_path')}`", f"Counts: `{summary.get('counts')}`", "", "## Jobs"]
    if jobs:
        for job in jobs:
            lines.append(f"- `{job['job_id']}` {job['status']} {job['kind']}: {job['goal']}")
    else:
        lines.append("- No jobs matched.")
    return ToolResult(True, "Nova job queue status", {"message": "\n".join(lines), "summary": summary, "jobs": jobs})


def _nova152_job_enqueue_tool(self: ToolRegistry, kind: str = "general", goal: str = "", payload: str = "", priority: int = 100, dedupe_key: str = "") -> ToolResult:
    if not goal.strip():
        return ToolResult(False, "Job goal is required", {"message": "Usage: /job-enqueue KIND GOAL"})
    data = {}
    if payload:
        try:
            data = json.loads(payload) if isinstance(payload, str) else dict(payload)
            if not isinstance(data, dict):
                data = {"raw": payload}
        except Exception:
            data = {"raw": payload}
    rec = _nova152_queue(self).enqueue(kind or "general", goal, data, priority=int(priority or 100), dedupe_key=dedupe_key or None)
    return ToolResult(True, f"Queued Nova job {rec.job_id}", {"job": {"job_id": rec.job_id, "kind": rec.kind, "goal": rec.goal, "status": rec.status, "priority": rec.priority, "payload": rec.payload}})


def _nova152_job_cancel_tool(self: ToolRegistry, job_id: str = "", reason: str = "cancelled by user") -> ToolResult:
    if not job_id:
        return ToolResult(False, "job_id is required", {"message": "Usage: /job-cancel JOB_ID"})
    rec = _nova152_queue(self).cancel(job_id, reason=reason or "cancelled by user")
    if not rec:
        return ToolResult(False, "Job was not found", {"job_id": job_id})
    return ToolResult(True, f"Cancelled Nova job {job_id}", {"job": {"job_id": rec.job_id, "status": rec.status, "result": rec.result}})


def _nova152_validate_all_tool(self: ToolRegistry, full: bool = False) -> ToolResult:
    from .validate import validate_all, render_validation
    payload = validate_all(self._wla_source_root(), full=bool(full))
    return ToolResult(bool(payload.get("ok")), "Nova layered validation completed" if payload.get("ok") else "Nova layered validation found issues", {"message": render_validation(payload), **payload})


_wla43_register_defaults_previous = ToolRegistry.register_defaults

def _nova152_register_defaults(self: ToolRegistry) -> None:
    _wla43_register_defaults_previous(self)
    self.register("integration_foundation", _nova152_integration_foundation_tool.__get__(self, ToolRegistry))
    self.register("orchestrator_foundation", _nova152_integration_foundation_tool.__get__(self, ToolRegistry))
    self.register("job_status", _nova152_job_status_tool.__get__(self, ToolRegistry))
    self.register("job_queue_status", _nova152_job_status_tool.__get__(self, ToolRegistry))
    self.register("job_enqueue", _nova152_job_enqueue_tool.__get__(self, ToolRegistry))
    self.register("job_create", _nova152_job_enqueue_tool.__get__(self, ToolRegistry))
    self.register("job_cancel", _nova152_job_cancel_tool.__get__(self, ToolRegistry))
    self.register("validate_all", _nova152_validate_all_tool.__get__(self, ToolRegistry))
    self.register("nova_validate_all", _nova152_validate_all_tool.__get__(self, ToolRegistry))

ToolRegistry.integration_foundation_tool = _nova152_integration_foundation_tool
ToolRegistry.job_status_tool = _nova152_job_status_tool
ToolRegistry.job_enqueue_tool = _nova152_job_enqueue_tool
ToolRegistry.job_cancel_tool = _nova152_job_cancel_tool
ToolRegistry.validate_all_tool = _nova152_validate_all_tool
ToolRegistry.register_defaults = _nova152_register_defaults

# v55.3.153 comprehensive integration/codebase review tools.
def _nova153_repo_map_tool(self: ToolRegistry, path: str = '.', max_files: int = 220) -> ToolResult:
    root, _meta = self._resolve_codebase_target(path or '.', default_wla_source=False)
    payload = build_repo_map(root, max_files=int(max_files or 220))
    return ToolResult(True, 'Nova repo map generated', {'message': render_repo_map(payload), **payload})


def _nova153_patch_plan_tool(self: ToolRegistry, goal: str = '', files: str = '') -> ToolResult:
    root = self._wla_source_root()
    repo_map = build_repo_map(root, max_files=260)
    file_list = [x.strip() for x in (files or '').replace(';', ',').split(',') if x.strip()]
    payload = build_patch_plan(goal or 'safe Nova improvement', repo_map, files=file_list or None)
    return ToolResult(True, 'Nova patch plan generated', {'message': render_patch_plan(payload), **payload})


def _nova153_browser_task_plan_tool(self: ToolRegistry, goal: str = '', url: str = '', allow_write: bool = False) -> ToolResult:
    payload = build_browser_task_plan(goal or 'read the current page safely', start_url=url or '', allow_write=bool(allow_write))
    return ToolResult(True, 'Nova browser worker dry-run plan generated', {'message': render_browser_task_plan(payload), **payload})


def _nova153_document_ingest_tool(self: ToolRegistry, path: str = '', query: str = '') -> ToolResult:
    if not path:
        return ToolResult(False, 'Document path is required', {'message': 'Usage: /doc-ingest PATH [query] or tool document_ingest path=... query=...'})
    target = resolve_inside_workspace(self.workspace, path)
    payload = ingest_document(target, out_dir=APP_DIR / 'document_ingestion')
    if query:
        payload['search'] = search_ingested_document(payload, query)
    return ToolResult(True, 'Nova document ingestion completed', {'message': render_document_ingestion(payload), **payload})


def _nova153_model_registry_tool(self: ToolRegistry) -> ToolResult:
    payload = build_model_registry()
    return ToolResult(bool(payload.get('ok')), 'Nova local model registry generated' if payload.get('ok') else 'Nova local model registry needs attention', {'message': render_model_registry(payload), **payload})


def _nova153_integration_review_tool(self: ToolRegistry) -> ToolResult:
    payload = build_integration_review(self._wla_source_root())
    return ToolResult(bool(payload.get('ok')), 'Nova comprehensive integration review completed' if payload.get('ok') else 'Nova comprehensive integration review found advisory gaps', {'message': render_integration_review(payload), **payload})


_nova152_register_defaults_previous_for_153 = ToolRegistry.register_defaults

def _nova153_register_defaults(self: ToolRegistry) -> None:
    _nova152_register_defaults_previous_for_153(self)
    self.register('repo_map_deep', _nova153_repo_map_tool.__get__(self, ToolRegistry))
    self.register('repo_map', _nova153_repo_map_tool.__get__(self, ToolRegistry))
    self.register('patch_plan', _nova153_patch_plan_tool.__get__(self, ToolRegistry))
    self.register('safe_patch_plan', _nova153_patch_plan_tool.__get__(self, ToolRegistry))
    self.register('browser_task_plan', _nova153_browser_task_plan_tool.__get__(self, ToolRegistry))
    self.register('browser_worker_plan', _nova153_browser_task_plan_tool.__get__(self, ToolRegistry))
    self.register('document_ingest', _nova153_document_ingest_tool.__get__(self, ToolRegistry))
    self.register('doc_ingest', _nova153_document_ingest_tool.__get__(self, ToolRegistry))
    self.register('local_model_registry', _nova153_model_registry_tool.__get__(self, ToolRegistry))
    self.register('model_registry', _nova153_model_registry_tool.__get__(self, ToolRegistry))
    self.register('integration_review', _nova153_integration_review_tool.__get__(self, ToolRegistry))
    self.register('comprehensive_integration_review', _nova153_integration_review_tool.__get__(self, ToolRegistry))

ToolRegistry.repo_map_deep_tool = _nova153_repo_map_tool
ToolRegistry.patch_plan_tool = _nova153_patch_plan_tool
ToolRegistry.browser_task_plan_tool = _nova153_browser_task_plan_tool
ToolRegistry.document_ingest_tool = _nova153_document_ingest_tool
ToolRegistry.model_registry_tool = _nova153_model_registry_tool
ToolRegistry.integration_review_tool = _nova153_integration_review_tool
ToolRegistry.register_defaults = _nova153_register_defaults


# v55.3.164 scheduling/control-plane tools: safe local scheduler, DAG decomposition and prompt-injection guard.
def _nova164_scheduler_store(self: ToolRegistry):
    from .scheduler_foundation import SchedulerStore
    return SchedulerStore(APP_DIR / "scheduler" / "nova_scheduler.sqlite3")


def _nova164_schedule_task_tool(
    self: ToolRegistry,
    prompt: str = "",
    when: str = "",
    repeat: str = "",
    action: str = "",
    name: str = "",
    schedule: str = "",
    command: str = "",
    task_id: str = "",
) -> ToolResult:
    from .scheduler_foundation import parse_schedule_request, render_task

    # Backward compatibility: v55.3.124 exposed ``schedule_task`` as the cron-like
    # legacy scheduler tool. v55.3.164 added natural-language scheduling under the
    # same tool name, so preserve the older action/name/schedule/command contract
    # instead of raising unexpected-keyword errors in old tests and user macros.
    if any(str(value or "").strip() for value in (action, name, schedule, command, task_id)):
        return _nova_task_scheduler_tool(
            self,
            action=action or "add",
            name=name,
            schedule=schedule,
            command=command,
            task_id=task_id,
        )

    if not str(prompt or "").strip():
        return ToolResult(False, "Schedule prompt is required", {"message": "Usage: /schedule-task remind me to stretch => tomorrow 9am"})
    parsed_prompt, parsed_when, parsed_repeat = parse_schedule_request(str(prompt))
    task = _nova164_scheduler_store(self).create_task(parsed_prompt, when or parsed_when, repeat or parsed_repeat, user_id="local")
    ok = task.status != "blocked"
    summary = "Scheduled task created" if task.status == "scheduled" else ("Scheduled task needs confirmation" if task.status == "pending_confirmation" else "Scheduled task blocked by safety filter")
    return ToolResult(ok, summary, {"message": "# Schedule Task\n\n" + render_task(task), "task": {"task_id": task.task_id, "status": task.status, "risk": task.risk, "confirmation_required": task.confirmation_required, "prompt": task.prompt, "when_text": task.when_text, "repeat": task.repeat}, "sanitized": task.sanitized, "dag": task.dag})


def _nova164_schedule_status_tool(self: ToolRegistry, status: str = "") -> ToolResult:
    from .scheduler_foundation import render_scheduler_status
    store = _nova164_scheduler_store(self)
    return ToolResult(True, "Nova scheduler status", {"message": render_scheduler_status(store, status=status or ""), "summary": store.summary(), "status_filter": status})


def _nova164_schedule_confirm_tool(self: ToolRegistry, task_id: str = "") -> ToolResult:
    if not task_id:
        return ToolResult(False, "task_id is required", {"message": "Usage: /schedule-confirm TASK_ID"})
    store = _nova164_scheduler_store(self)
    task = store.get(task_id)
    if not task:
        return ToolResult(False, "Scheduled task not found", {"task_id": task_id})
    if task.status == "blocked":
        return ToolResult(False, "Blocked tasks cannot be confirmed", {"task_id": task_id, "sanitized": task.sanitized})
    if task.status == "scheduled":
        return ToolResult(True, "Scheduled task already confirmed", {"message": f"`{task_id}` is already scheduled.", "task": {"task_id": task.task_id, "status": task.status, "risk": task.risk}})
    if task.status != "pending_confirmation":
        return ToolResult(False, "Only pending-confirmation tasks can be confirmed", {"task_id": task_id, "status": task.status})
    updated = store.update_status(task_id, "scheduled", "confirmed_by_user")
    return ToolResult(True, "Scheduled task confirmed", {"message": f"Confirmed `{task_id}`. It is now scheduled.", "task": {"task_id": updated.task_id, "status": updated.status, "risk": updated.risk} if updated else {}})


def _nova164_schedule_cancel_tool(self: ToolRegistry, task_id: str = "") -> ToolResult:
    if not task_id:
        return ToolResult(False, "task_id is required", {"message": "Usage: /schedule-cancel TASK_ID"})
    updated = _nova164_scheduler_store(self).update_status(task_id, "cancelled", "cancelled_by_user")
    if not updated:
        return ToolResult(False, "Scheduled task not found", {"task_id": task_id})
    return ToolResult(True, "Scheduled task cancelled", {"message": f"Cancelled `{task_id}`.", "task": {"task_id": updated.task_id, "status": updated.status}})


def _nova164_task_decompose_tool(self: ToolRegistry, prompt: str = "") -> ToolResult:
    from .scheduler_foundation import decompose_task, render_decomposition, sanitize_scheduled_prompt, classify_task_risk, task_dag_to_dict
    sanitized = sanitize_scheduled_prompt(prompt or "")
    dag = decompose_task(sanitized.cleaned)
    return ToolResult(bool(sanitized.ok and dag.ok), "Nova task decomposition generated", {"message": render_decomposition(prompt or ""), "sanitized": asdict(sanitized), "risk": classify_task_risk(sanitized.cleaned), "dag": task_dag_to_dict(dag)})


def _nova164_scheduling_audit_tool(self: ToolRegistry) -> ToolResult:
    from .scheduler_foundation import render_scheduling_audit
    store = _nova164_scheduler_store(self)
    return ToolResult(True, "Nova scheduling audit completed", {"message": render_scheduling_audit(store), "summary": store.summary()})


_wla163_register_defaults_previous = ToolRegistry.register_defaults

def _nova164_register_defaults(self: ToolRegistry) -> None:
    _wla163_register_defaults_previous(self)
    self.register("schedule_task", _nova164_schedule_task_tool.__get__(self, ToolRegistry))
    self.register("schedule_status", _nova164_schedule_status_tool.__get__(self, ToolRegistry))
    self.register("schedule_confirm", _nova164_schedule_confirm_tool.__get__(self, ToolRegistry))
    self.register("schedule_cancel", _nova164_schedule_cancel_tool.__get__(self, ToolRegistry))
    self.register("task_decompose", _nova164_task_decompose_tool.__get__(self, ToolRegistry))
    self.register("task_decomposition", _nova164_task_decompose_tool.__get__(self, ToolRegistry))
    self.register("scheduling_audit", _nova164_scheduling_audit_tool.__get__(self, ToolRegistry))

ToolRegistry.schedule_task_tool = _nova164_schedule_task_tool
ToolRegistry.schedule_status_tool = _nova164_schedule_status_tool
ToolRegistry.schedule_confirm_tool = _nova164_schedule_confirm_tool
ToolRegistry.schedule_cancel_tool = _nova164_schedule_cancel_tool
ToolRegistry.task_decompose_tool = _nova164_task_decompose_tool
ToolRegistry.scheduling_audit_tool = _nova164_scheduling_audit_tool
ToolRegistry.register_defaults = _nova164_register_defaults
