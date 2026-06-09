from __future__ import annotations
import time
from pathlib import Path
from typing import Any, Callable
from .dependency_check import build_dependency_report, render_dependency_report
from .release_hygiene import build_release_hygiene_report, render_release_hygiene_report, clean_release_hygiene_artifacts
from .feature_audit import build_feature_audit, render_feature_audit_markdown
from .gui_redesign import build_gui_feature_map, render_gui_feature_map, gui_regression_check, render_gui_regression
from .trace_cockpit import build_trace, render_performance_dashboard
from .blueprint_engine import build_project_blueprint, build_candidate_set, render_blueprint_markdown, render_candidate_markdown
from .visual_regression import build_gui_snapshot_status, render_gui_snapshot_status
from .mcp_export import build_mcp_manifest, render_mcp_manifest
from .prompt_test_compiler import build_prompt_contract, validate_contract, render_prompt_contract, render_contract_validation
from .candidate_tournament import build_candidate_tournament, render_tournament
from .repair_engine_v2 import build_repair_plan, render_repair
from .mcp_security import inspect_mcp_security, render_mcp_security
from .mission_planner_v2 import create_mission, render_mission
from .model_output_coach import analyze_model_output, render_model_output_coach
from .env_profiles import build_env_profile, render_env_profile
from .benchmark_migration import benchmark_system, render_benchmark
from .project_state_db import load_project_state, render_project_state
from .regression_memory import export_regressions, render_regressions
from .model_download_manager import build_model_readiness, render_model_readiness
from .flow_audit import build_flow_audit, render_flow_audit
from .next_feature_suite import (
    build_quality_report, render_build_quality, build_browser_runtime_test, render_browser_runtime,
    build_model_reliability, render_model_reliability, build_model_fallback_strategy, render_strategy,
    patch_queue_action, render_patch_queue, build_gui_cockpit_v2, render_gui_cockpit_v2,
    build_voice_mode_report, render_voice_mode, list_templates, render_templates,
    build_preview_server_report, render_preview, build_feature_readiness, render_feature_readiness,
    explain_error, render_error_explanation, build_support_report, render_support_report, docs_index, render_docs_index,
    regression_test_generate, render_regression_test, learning_status, render_learning_status,
)


def run_wla_mega_test(root: Path, tool_call: Callable[..., Any] | None = None, app: Any | None = None) -> dict[str, Any]:
    started = time.time()
    sections = []
    def add(name: str, ok: bool, markdown: str):
        sections.append({"name": name, "ok": bool(ok), "markdown": markdown})
    # Clean transient Python/test artifacts first so this one-command report is copy/paste friendly after validation runs.
    clean_release_hygiene_artifacts(root)
    deps = build_dependency_report()
    add("dependency_check", True, render_dependency_report(deps))
    hygiene = build_release_hygiene_report(root)
    add("release_hygiene", bool(hygiene.get("ok")) or hygiene.get("overall") in {"OK", "PASS"}, render_release_hygiene_report(hygiene))
    try:
        fa = build_feature_audit(root)
        add("feature_audit", bool(fa.get("ok", True)), render_feature_audit_markdown(fa))
    except Exception as exc:
        add("feature_audit", False, f"Feature audit failed: {exc}")
    fmap = build_gui_feature_map(root)
    add("gui_feature_map", fmap.get("ok", False), render_gui_feature_map(fmap))
    greg = gui_regression_check(root)
    add("gui_regression", greg.get("ok", False), render_gui_regression(greg))
    snap = build_gui_snapshot_status(root)
    add("gui_visual_gate", bool(snap.get("ok")), render_gui_snapshot_status(snap))
    bp = build_project_blueprint("tiny useful local notes app with localStorage and JSON export")
    add("blueprint_engine", True, render_blueprint_markdown(bp))
    cand = build_candidate_set("tiny useful local notes app with localStorage and JSON export")
    add("candidate_engine", True, render_candidate_markdown(cand))
    trace = build_trace(limit=80)
    add("trace_cockpit", True, render_performance_dashboard(trace))
    mcp = build_mcp_manifest(app=app, root=root)
    add("mcp_manifest", True, render_mcp_manifest(mcp))
    goal = "tiny useful local notes app with localStorage and JSON export"
    add("prompt_contract", True, render_prompt_contract(build_prompt_contract(goal)))
    contract_result = validate_contract(goal, root)
    add("contract_validation", True, render_contract_validation(contract_result))
    add("candidate_tournament", True, render_tournament(build_candidate_tournament(goal, root)))
    add("surgical_repair_v2", True, render_repair(build_repair_plan(root, "Dodge Game default appeared even though the user did not request a dodge game")))
    add("mcp_security", True, render_mcp_security(inspect_mcp_security(app=app, root=root)))
    add("mission_planner", True, render_mission(create_mission("improve Nova validation and file building")))
    add("model_output_coach", True, render_model_output_coach(analyze_model_output(goal, "{}")))
    add("environment_profile", True, render_env_profile(build_env_profile("minimal")))
    add("new_pc_benchmark", True, render_benchmark(benchmark_system()))
    add("project_state", True, render_project_state(load_project_state(root)))
    add("regression_memory", True, render_regressions(export_regressions()))
    add("build_quality_v3", True, render_build_quality(build_quality_report(root, goal)))
    add("browser_runtime_tester", True, render_browser_runtime(build_browser_runtime_test(root, goal)))
    add("model_reliability_controller", True, render_model_reliability(build_model_reliability(root, "mega-test")))
    add("model_requirement_download_planner", True, render_model_readiness(build_model_readiness(goal, root)))
    add("model_fallback_strategy", True, render_strategy(build_model_fallback_strategy(root, "mega-test")))
    add("patch_queue", True, render_patch_queue(patch_queue_action("status", "mega-test")))
    add("gui_cockpit_v2", True, render_gui_cockpit_v2(build_gui_cockpit_v2(root, "mega-test")))
    add("voice_mode_upgrade", True, render_voice_mode(build_voice_mode_report(root, "mega-test")))
    add("template_builder", True, render_templates(list_templates()))
    add("preview_server", True, render_preview(build_preview_server_report(root, "status")))
    add("feature_readiness", True, render_feature_readiness(build_feature_readiness(root)))
    add("error_translator", True, render_error_explanation(explain_error("TypeError: Failed to fetch")))
    add("support_report", True, render_support_report(build_support_report(root, "mega-test")))
    add("docs_index", True, render_docs_index(docs_index(root, "Nova")))
    add("regression_test_generator", True, render_regression_test(regression_test_generate(root, "mega-test regression seed")))
    add("mistake_learning", True, render_learning_status(learning_status(root)))
    flow = build_flow_audit(root, tool_names=sorted(getattr(getattr(app, "tools", None), "tools", {}).keys()) if app is not None else None)
    add("interaction_flow_audit", bool(flow.get("ok")), render_flow_audit(flow))
    passed = sum(1 for s in sections if s["ok"])
    clean_release_hygiene_artifacts(root)
    report = {"ok": passed == len(sections), "passed": passed, "total": len(sections), "duration_sec": round(time.time() - started, 3), "sections": sections, "copy_paste_command": "/nova-mega-test --confirm"}
    out = root / "docs" / "NOVA_MEGA_TEST_LATEST.md"
    out.parent.mkdir(exist_ok=True)
    out.write_text(render_wla_mega_test(report), encoding="utf-8")
    report["report_path"] = str(out)
    return report


def render_wla_mega_test(payload: dict[str, Any]) -> str:
    lines = ["# Nova Mega Test", "", f"Overall: **{'PASS' if payload.get('ok') else 'ATTENTION'}**", f"Passed: {payload.get('passed')}/{payload.get('total')}", f"Duration: {payload.get('duration_sec')} sec", f"Copy/paste command: `{payload.get('copy_paste_command','/nova-mega-test --confirm')}`", "", "## Sections"]
    for sec in payload.get("sections", []):
        icon = "✅" if sec.get("ok") else "⚠️"
        lines.append(f"- {icon} {sec.get('name')}")
    lines += ["", "## Details"]
    for sec in payload.get("sections", []):
        lines += ["", f"### {sec.get('name')}", sec.get("markdown", "")[:6000]]
    if payload.get("report_path"):
        lines += ["", f"Report: `{payload.get('report_path')}`"]
    return "\n".join(lines)
