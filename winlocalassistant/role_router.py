from __future__ import annotations

import re
import time
from dataclasses import dataclass, asdict
from typing import Any


@dataclass
class RoleRoute:
    goal: str
    primary_role: str
    supporting_roles: list[str]
    route: str
    reason: str
    model_hint: str
    context_sections: list[str]
    output_contract: list[str]
    validation_focus: list[str]
    mutation_default: str
    generated_at: str = ""

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["generated_at"] = data.get("generated_at") or time.strftime("%Y-%m-%d %H:%M:%S")
        return data


def _norm(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip().lower())


def build_role_route(goal: str = "", last_failure: str = "", target_type: str = "") -> dict[str, Any]:
    """Choose a narrow local-model role and prompt contract.

    Nova's local models perform better when asked to do one role at a time.  This
    router is deterministic so command routing, autonomous planning and prompt
    construction can share the same role decision instead of relying on broad
    free-form prompts.
    """
    low = _norm(goal)
    failure = _norm(last_failure)
    target = _norm(target_type)

    role = "Planner"
    route = "plan_acceptance_contract"
    reason = "The goal needs an acceptance contract before any mutation."
    model_hint = "planner/review model"
    supporting = ["Verifier"]
    mutation = "no_mutation_until_plan_clear"
    context = ["user_goal", "target_type", "available_tools", "constraints"]
    output = ["acceptance_checks", "smallest_safe_next_step", "mutation_permission_needed"]
    validation = ["contract is specific", "next action is bounded"]

    if any(w in low for w in ["fix", "bug", "error", "broken", "regression", "failing", "repair"]) or failure:
        role = "Repairer"
        route = "diagnose_patch_validate"
        reason = "The request or latest evidence points at a failure that should be patched directly."
        model_hint = "code model with failure context"
        supporting = ["Verifier", "SurgicalFallback"]
        mutation = "patch_allowed_if_user_requested_fix"
        context = ["user_goal", "latest_failure", "changed_files", "relevant_file_previews", "validation_conditions", "do_not_repeat"]
        output = ["root_cause", "minimal_patch", "validation_commands", "rollback_notes"]
        validation = ["changed_files non-empty", "targeted test passes", "feature continuity preserved"]
    elif any(w in low for w in ["make", "build", "create", "generate", "new project", "game", "script", "app", "dashboard"]):
        role = "Builder"
        route = "build_minimal_working_artifact"
        reason = "The user is asking for a new or changed artifact."
        model_hint = "code model with project type contract"
        supporting = ["Verifier", "Repairer"]
        mutation = "mutation_expected_after_plan"
        context = ["user_goal", "project_type", "template_manifest", "acceptance_checks", "existing_files_if_any"]
        output = ["complete_files", "run_command", "verify_command", "manual_test_steps"]
        validation = ["syntax check", "behaviour evidence", "action receipt"]
    elif any(w in low for w in ["validate", "test", "check", "audit", "verify", "no regression"]):
        role = "Verifier"
        route = "collect_validation_evidence"
        reason = "The user wants proof the system still works."
        model_hint = "review model or deterministic tools first"
        supporting = ["Planner"]
        mutation = "read_only_by_default"
        context = ["target_root", "validation_matrix", "feature_continuity", "recent_receipts"]
        output = ["checks_run", "passed_failed_summary", "remaining_risks"]
        validation = ["compile", "browser JS check", "feature continuity", "behaviour evidence"]
    elif any(w in low for w in ["tool", "mcp", "custom tool", "toolsmith"]):
        role = "Toolsmith"
        route = "create_register_test_tool"
        reason = "The goal concerns reusable tool creation or modification."
        model_hint = "code model with tool schema examples"
        supporting = ["Verifier"]
        mutation = "tool_file_allowed_if_user_requested_tool"
        context = ["tool_goal", "custom_tool_schema", "registry_state", "tool_test_contract"]
        output = ["tool_file", "manifest_metadata", "test_input", "expected_output"]
        validation = ["tool file exists", "registry refresh lists it", "tool_test passes", "tool_run passes"]
    elif any(w in low for w in ["research", "investigate", "look up", "compare"]):
        role = "Researcher"
        route = "gather_summarise_sources"
        reason = "The user is asking for investigation before implementation."
        model_hint = "chat/review model plus source tools"
        supporting = ["Planner"]
        mutation = "no_mutation_unless_followed_by_implement_request"
        context = ["research_goal", "sources", "constraints", "next_implementation_options"]
        output = ["findings", "confidence", "adaptable_lessons", "recommended_patch"]
        validation = ["sources cited when external", "implementation path is explicit"]

    if target in {"wla", "source", "wla_source", "codebase"}:
        context.append("wla_source_root")
        validation.append("version markers consistent")
    if "same failure" in failure or "candidate_refine_no_progress" in failure or "loop" in failure:
        supporting = list(dict.fromkeys([*supporting, "DevelopmentGovernor", "SurgicalFallback"]))
        output.append("strategy_switch_reason")
        validation.append("same failure is not retried unchanged")

    return RoleRoute(
        goal=goal or "general Nova work",
        primary_role=role,
        supporting_roles=list(dict.fromkeys(supporting)),
        route=route,
        reason=reason,
        model_hint=model_hint,
        context_sections=list(dict.fromkeys(context)),
        output_contract=list(dict.fromkeys(output)),
        validation_focus=list(dict.fromkeys(validation)),
        mutation_default=mutation,
    ).to_dict()


def render_role_route(route: dict[str, Any]) -> str:
    lines = [
        "# Local Model Role Router",
        "",
        f"Goal: {route.get('goal','')}",
        f"Primary role: **{route.get('primary_role','')}**",
        f"Route: `{route.get('route','')}`",
        f"Model hint: {route.get('model_hint','')}",
        f"Mutation default: {route.get('mutation_default','')}",
        "",
        f"Reason: {route.get('reason','')}",
        "",
        "## Supporting roles",
    ]
    lines.extend(f"- {x}" for x in route.get("supporting_roles") or [])
    lines.append("\n## Context sections to give the local model")
    lines.extend(f"- {x}" for x in route.get("context_sections") or [])
    lines.append("\n## Required output contract")
    lines.extend(f"- {x}" for x in route.get("output_contract") or [])
    lines.append("\n## Validation focus")
    lines.extend(f"- {x}" for x in route.get("validation_focus") or [])
    return "\n".join(lines) + "\n"
