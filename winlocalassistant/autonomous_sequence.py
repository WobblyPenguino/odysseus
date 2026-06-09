from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any

from .action_watcher import evaluate_action_risk
from .task_decomposition import decompose_user_request
from .autonomy_capabilities import build_mutable_mission_plan


@dataclass(frozen=True)
class AutonomousToolStep:
    """A concrete tool call selected for an autonomous cycle."""

    title: str
    tool: str
    kwargs: dict[str, Any] = field(default_factory=dict)
    reason: str = ""
    required: bool = True
    run_if_previous_failed: bool = False
    stop_on_failure: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class AutonomousSequencePlan:
    """User-task-specific autonomous tool sequence.

    This is deliberately deterministic: it turns an interpreted user goal into a
    transparent sequence of existing Nova tools. The normal watcher and failure
    memory still gate execution.
    """

    goal: str
    intent: str
    plan_level: int
    confidence: float
    needs_clarification: bool
    rationale: str
    steps: list[AutonomousToolStep]
    verification_steps: list[AutonomousToolStep]
    risk_notes: list[str]
    capability_matches: list[dict[str, Any]] = field(default_factory=list)
    mutable_plan: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def build_autonomous_tool_sequence(goal: str, context: dict[str, Any] | None = None) -> AutonomousSequencePlan:
    """Build a sequential tool plan for an autonomous user task.

    The plan is not executed here. It describes what Nova should do first,
    second, third, and how it will verify the result. It avoids hidden shell or
    self-improvement actions and prefers Nova's existing commands/tools.
    """

    text = (goal or "").strip() or "Investigate logs and improve the current project safely."
    task_plan = decompose_user_request(text)
    mission_plan = build_mutable_mission_plan(text)
    low = task_plan.normalized_text.lower()
    intents = [s.intent for s in task_plan.subtasks]
    intent = _dominant_intent(intents, low)
    steps: list[AutonomousToolStep] = []
    verify: list[AutonomousToolStep] = []

    sandbox = (context or {}).get("sandbox") or {}
    sandbox_mode = bool(sandbox.get("autonomous_sandbox_mode"))
    linux_sandbox_ready = bool((sandbox.get("sandboxes") or {}).get("linux", {}).get("ok"))
    kali_sandbox_ready = bool((sandbox.get("sandboxes") or {}).get("kali", {}).get("ok"))

    # Sandbox-focused requests should actually exercise the sandboxes instead
    # of falling back to generic observe/propose loops. This is deterministic
    # and read-only: it starts missing containers if needed, checks OS identity,
    # verifies the Kali tools image, and reports results through sandbox logs.
    sandbox_goal = any(w in low for w in ["sandbox", "linux", "kali", "docker", "container"])
    if sandbox_goal and any(w in low for w in ["test", "check", "verify", "availability", "available", "works", "working"]):
        steps.extend([
            AutonomousToolStep("Check sandbox status", "sandbox_status", {}, "inspect Docker/Podman runtime and known sandboxes", required=False),
            AutonomousToolStep("Start Linux sandbox if needed", "sandbox_start", {"profile": "linux", "network": "none"}, "ensure the Linux sandbox exists before executing Linux checks", required=False),
            AutonomousToolStep("Linux OS smoke test", "sandbox_exec", {"profile": "linux", "command": "cat /etc/os-release && uname -a", "timeout": 25}, "prove the Linux container can execute commands", required=False),
            AutonomousToolStep("Start Kali sandbox if needed", "sandbox_start", {"profile": "kali", "network": "none"}, "ensure the Kali sandbox exists before executing Kali checks", required=False),
            AutonomousToolStep("Kali OS smoke test", "sandbox_exec", {"profile": "kali", "command": "cat /etc/os-release && whoami", "timeout": 25}, "prove the Kali container can execute commands", required=False),
            AutonomousToolStep("Kali tools smoke test", "sandbox_exec", {"profile": "kali", "command": "nmap --version || true; nikto -Version || true; whois --version || true", "timeout": 30}, "check whether the custom Kali tools image is being used", required=False),
        ])
        verify.append(AutonomousToolStep("Final sandbox status", "sandbox_status", {}, "summarise detected runtime, images and running containers", required=False))
        all_steps = _dedupe_steps(steps + verify)
        return AutonomousSequencePlan(
            goal=text,
            intent="sandbox_verification",
            plan_level=task_plan.plan_level,
            confidence=max(task_plan.intent_confidence, 0.88),
            needs_clarification=False,
            rationale="Sandbox requests should run concrete Linux/Kali status and smoke-test commands rather than generic improvement loops.",
            steps=all_steps,
            verification_steps=verify,
            risk_notes=_risk_notes_for_steps(all_steps),
            capability_matches=[m.to_dict() for m in mission_plan.capabilities],
            mutable_plan=mission_plan.to_dict(),
        )

    tool_goal = any(x in low for x in ["custom tool", "make its own tool", "create a tool", "tool-create", "reusable helper", "new tool"])
    if tool_goal:
        steps.extend([
            AutonomousToolStep("Inspect custom tool catalog", "custom_tools", {}, "see whether a built-in or existing custom tool already solves the task", required=False),
            AutonomousToolStep("Create safe custom tool", "tool_create", {"goal": text}, "create a reusable safe local helper only through Nova's validated custom-tool path", required=False),
            AutonomousToolStep("Clean stale tool proposals", "tool_clean_proposals", {}, "remove superseded or unsafe proposals after creation", required=False),
        ])
        verify.extend([
            AutonomousToolStep("Review custom tools", "custom_tools", {}, "confirm the tool is present/enabled or proposal is visible for approval", required=False),
            AutonomousToolStep("Record regression memory if tool creation failed", "regression_list", {}, "keep tool-creation failures visible for future planning", required=False),
        ])
        all_steps = _dedupe_steps(steps + verify)
        return AutonomousSequencePlan(
            goal=text,
            intent="custom_tool_extension",
            plan_level=task_plan.plan_level,
            confidence=max(task_plan.intent_confidence, 0.86),
            needs_clarification=False,
            rationale="The prompt asks Nova to create or use its own tool, so autonomous mode should use the guarded custom-tool validator instead of arbitrary code execution.",
            steps=all_steps,
            verification_steps=verify,
            risk_notes=_risk_notes_for_steps(all_steps),
            capability_matches=[m.to_dict() for m in mission_plan.capabilities],
            mutable_plan=mission_plan.to_dict(),
        )

    # Always begin with cheap state inspection. autonomous_once already runs
    # several of these as base steps, but keeping them in the plan makes the
    # exact intended sequence visible to users and the UI.
    steps.append(AutonomousToolStep("Detect current project", "detect_project", {}, "know whether the goal targets an existing project", required=False))
    steps.append(AutonomousToolStep("Run weakspot/error-hunt audit", "weakspot_audit", {"path": ".", "write_report": True}, "scan for silent exception swallowing, missing autonomy command coverage and release/runtime artifacts before acting", required=False))
    steps.append(AutonomousToolStep("Run code repair audit", "code_repair_audit", {"path": "."}, "find syntax, duplicate-definition, swallowed-exception and release-hygiene risks before acting", required=False))
    steps.append(AutonomousToolStep("Run deep code review", "code_review_audit", {"path": "."}, "review reliability, timeout, safety and maintainability risks before choosing autonomous edits", required=False))
    steps.append(AutonomousToolStep("Run CodeRabbit-style quality gate", "code_quality_gate", {"path": "."}, "turn code review signals into PR-style comments and a block/warn/pass gate before mutation", required=False))
    steps.append(AutonomousToolStep("Check sandbox capability", "sandbox_status", {}, "know whether disposable Linux/Kali execution is available before risky experiments", required=False))
    steps.append(AutonomousToolStep("Check local model readiness", "model_readiness", {"goal": text}, "know whether required/optional Ollama models are installed before model-heavy planning, coding or vision tasks", required=False))
    if sandbox_mode and linux_sandbox_ready:
        steps.append(AutonomousToolStep("Sandbox smoke test", "sandbox_exec", {"profile": "linux", "command": "python3 --version || uname -a", "timeout": 20}, "prove that higher-risk efficiency experiments can run inside the disposable sandbox rather than on the host", required=False))

    if intent == "create_project":
        steps.extend([
            AutonomousToolStep("Compile prompt contract", "prompt_contract", {"goal": text}, "turn the exact prompt into must-have and must-not-have validation checks before generation", required=False),
            AutonomousToolStep("Plan iterative edit/test/repair loop", "iterative_coding_loop", {"goal": text, "path": "."}, "prepare a mutable loop that uses prompt contract, build quality, browser/runtime checks and surgical fallback before accepting the result", required=False),
            AutonomousToolStep("Run candidate tournament", "candidate_tournament", {"goal": text, "path": "."}, "compare multiple candidate strategies and reject unrelated defaults before live promotion", required=False),
            AutonomousToolStep("Prepare project specification", "project_spec", {"goal": text}, "extract domain objects, workflows, edge cases and acceptance tests from the user's exact specification", required=True, stop_on_failure=False),
            AutonomousToolStep("Create requested project", "ai_create_project", {"goal": text, "build_mode": "long"}, "build the artifact described by the user using the project specification instead of a generic template", stop_on_failure=True),
            AutonomousToolStep("Coach model output if needed", "model_output_coach", {"goal": text}, "score the most recent model output and generate tighter correction context if it goes off course", required=False),
            AutonomousToolStep("Run/interpret created project", "run_project", {"path": "."}, "surface how the user can run the generated project", required=False),
        ])
        verify.extend([
            AutonomousToolStep("Run prompt contract checks", "prompt_test_run", {"goal": text, "path": "."}, "prove the files satisfy prompt-specific positive and negative checks", required=False),
            AutonomousToolStep("Verify created project", "auto_verify", {}, "run project-appropriate checks after generation"),
            AutonomousToolStep("Final requirement check", "final_project_check", {"path": ".", "goal": text}, "check generated output against the original request"),
            AutonomousToolStep("Post-build quality gate", "code_quality_gate", {"path": "."}, "review generated code with file/line comments before packaging", required=False),
            AutonomousToolStep("Zip completed project", "zip_path", {"path": "."}, "package the verified result for the user", required=False),
        ])
    elif intent == "repair_or_debug":
        steps.extend([
            AutonomousToolStep("Inspect recent failures", "investigate_logs", {"focus": text}, "collect evidence before changing files"),
            AutonomousToolStep("Classify repair with v2 engine", "repair_plan_v2", {"evidence": text, "path": "."}, "classify the failure and choose a minimal-diff repair strategy", required=False),
            AutonomousToolStep("Plan surgical fallback v2", "surgical_fallback_v2", {"goal": text, "path": "."}, "use concrete HTML/JS/README evidence to pick the smallest fallback repair instead of broad regeneration", required=False),
            AutonomousToolStep("Run code repair audit", "code_repair_audit", {"path": "."}, "scan code structure and release hygiene before choosing a repair", required=False),
            AutonomousToolStep("Reason about failure", "reasoning_diagnostics", {"goal": text, "failed_tool": "autonomous", "failure": {"goal": text}}, "ask Nova's diagnostic tool for the smallest safe repair path", required=False),
            AutonomousToolStep("Try surgical repair", "surgical_repair", {"goal": text, "path": "."}, "repair localised errors before broader fallback", stop_on_failure=False),
            AutonomousToolStep("Coach model output if needed", "model_output_coach", {"goal": text}, "detect invalid JSON, wrong-domain output, or file splitting mistakes before another retry", required=False),
        ])
        verify.extend([
            AutonomousToolStep("Verify repair", "auto_verify", {}, "confirm the repair did not break the project"),
            AutonomousToolStep("Final requirement check", "final_project_check", {"path": ".", "goal": text}, "confirm the original debugging request is satisfied", required=False),
        ])
    elif intent == "verify":
        steps.extend([
            AutonomousToolStep("Run project verification", "auto_verify", {}, "run the current project's normal checks"),
            AutonomousToolStep("Run final requirement check", "final_project_check", {"path": ".", "goal": text}, "summarise whether current files meet the stated goal", required=False),
        ])
    elif intent == "inspect":
        steps.extend([
            AutonomousToolStep("List project files", "list_files", {"subdir": ".", "limit": 120}, "inspect available files before acting"),
            AutonomousToolStep("Investigate logs", "investigate_logs", {"focus": text}, "turn recent failures into evidence"),
            AutonomousToolStep("Run weakspot/error-hunt audit", "weakspot_audit", {"path": ".", "write_report": True}, "find broad codebase weaknesses before proposing changes", required=False),
            AutonomousToolStep("Write improvement proposal", "propose_improvements", {"focus": text}, "produce a safe next-step proposal", required=False),
        ])
    elif intent == "improvement":
        steps.extend([
            AutonomousToolStep("Compile prompt contract", "prompt_contract", {"goal": text}, "derive the exact success criteria before improving", required=False),
            AutonomousToolStep("Create autonomous mission", "mission_create", {"goal": text}, "convert the broad improvement into a queue with success and stop conditions", required=False),
            AutonomousToolStep("Prepare improvement specification", "project_spec", {"goal": text}, "turn the requested improvement into concrete acceptance criteria before editing", required=False),
            AutonomousToolStep("Run weakspot/error-hunt audit", "weakspot_audit", {"path": ".", "write_report": True}, "identify broad regression, command-access and hygiene risks before editing", required=False),
            AutonomousToolStep("Run code repair audit", "code_repair_audit", {"path": "."}, "identify structural bugs and release hygiene issues before editing", required=False),
            AutonomousToolStep("Prepare iterative coding repair plan", "edit_repair_plan", {"goal": text, "path": "."}, "make the improvement path editable, testable and prompt-specific before mutating files", required=False),
            AutonomousToolStep("Run project verification", "auto_verify", {}, "establish the current project state before improving", required=False),
            AutonomousToolStep("Improve current project", "improve_project", {"goal": text}, "apply the smallest project-local improvement and verify it", stop_on_failure=False),
        ])
        if sandbox_mode and linux_sandbox_ready:
            steps.append(AutonomousToolStep("Run sandboxed efficiency probe", "sandbox_exec", {"profile": "linux", "command": "python3 - <<'EOF'\nimport platform, time\nprint('sandbox-ok', platform.platform(), time.time())\nEOF", "timeout": 30}, "use the disposable sandbox for experiments that should not touch the host", required=False))
        verify.extend([
            AutonomousToolStep("Verify improvement", "auto_verify", {}, "check the improvement after edits"),
            AutonomousToolStep("Final requirement check", "final_project_check", {"path": ".", "goal": text}, "confirm the improvement matches the user's goal", required=False),
            AutonomousToolStep("Post-improvement quality gate", "code_quality_gate", {"path": "."}, "ensure the edit does not introduce review-blocking quality issues", required=False),
        ])
    else:
        steps.extend([
            AutonomousToolStep("Investigate recent logs", "investigate_logs", {"focus": text}, "gather evidence for a safe next action", required=False),
            AutonomousToolStep("Propose safe improvements", "propose_improvements", {"focus": text}, "avoid acting before a useful target is known", required=False),
        ])

    all_steps = _dedupe_steps(steps + verify)
    risk_notes = _risk_notes_for_steps(all_steps)
    rationale = _rationale(intent, task_plan.task_count, task_plan.needs_clarification)
    return AutonomousSequencePlan(
        goal=text,
        intent=intent,
        plan_level=task_plan.plan_level,
        confidence=task_plan.intent_confidence,
        needs_clarification=task_plan.needs_clarification,
        rationale=rationale,
        steps=all_steps,
        verification_steps=verify,
        risk_notes=risk_notes,
        capability_matches=[m.to_dict() for m in mission_plan.capabilities],
        mutable_plan=mission_plan.to_dict(),
    )


def render_autonomous_sequence_markdown(plan: AutonomousSequencePlan) -> str:
    lines = [
        "# Autonomous Tool Sequence",
        "",
        f"Goal: {plan.goal}",
        f"Intent: {plan.intent}",
        f"Plan level: {plan.plan_level}",
        f"Confidence: {plan.confidence:.2f}",
        f"Needs clarification: {plan.needs_clarification}",
        "",
        "## Why this sequence",
        plan.rationale,
        "",
        "## Capability choices",
    ]
    for match in plan.capability_matches[:6]:
        cap = match.get("capability", {}) if isinstance(match, dict) else {}
        lines.append(f"- **{cap.get('name', 'capability')}** — score {match.get('score', 0):.2f}: {match.get('why', '')}")
        if cap.get("commands"):
            lines.append(f"  - first command: `{cap.get('commands')[0]}`")
    mutable = plan.mutable_plan or {}
    stages = mutable.get("stages") or []
    if stages:
        lines += ["", "## Mutable plan", "These stages can change when evidence shows the current path is going nowhere."]
        for stage in stages:
            lines.append(f"- **{stage.get('name')}**: {stage.get('purpose')}")
            if stage.get("adapt_if"):
                lines.append("  - adapt if: " + "; ".join(stage.get("adapt_if") or []))
    lines += ["", "## Steps"]
    for index, step in enumerate(plan.steps, 1):
        lines.append(f"{index}. **{step.title}** → `{step.tool}`")
        if step.reason:
            lines.append(f"   - reason: {step.reason}")
        if step.kwargs:
            lines.append(f"   - args: {step.kwargs}")
    lines += ["", "## Risk notes"]
    lines += [f"- {n}" for n in plan.risk_notes] or ["- No elevated risk detected."]
    return "\n".join(lines)


def _dominant_intent(intents: list[str], low: str) -> str:
    if any(w in low for w in ["make", "create", "build", "generate", "write an app", "write a game"]):
        return "create_project"
    if "repair" in intents or any(w in low for w in ["fix", "broken", "error", "traceback", "not working"]):
        return "repair_or_debug"
    if "verify" in intents or any(w in low for w in ["test", "verify", "check"]):
        return "verify"
    if "inspect" in intents:
        return "inspect"
    if "modify" in intents or any(w in low for w in ["improve", "refactor", "update"]):
        return "improvement"
    return "general"


def _dedupe_steps(steps: list[AutonomousToolStep]) -> list[AutonomousToolStep]:
    out: list[AutonomousToolStep] = []
    seen: set[tuple[str, str, str]] = set()
    for step in steps:
        key = (step.title, step.tool, repr(sorted(step.kwargs.items())))
        if key not in seen:
            seen.add(key)
            out.append(step)
    return out


def _risk_notes_for_steps(steps: list[AutonomousToolStep]) -> list[str]:
    notes: list[str] = []
    for step in steps:
        decision = evaluate_action_risk({"name": step.title, "tool": step.tool, "command": str(step.kwargs), "category": step.tool})
        if decision.status != "allow":
            notes.append(f"{step.tool}: {decision.status} ({'; '.join(decision.reasons)})")
    return notes[:10]


def _rationale(intent: str, count: int, needs_clarification: bool) -> str:
    extra = " The request contains ambiguity, so Nova should pause or keep the sequence proposal-first where needed." if needs_clarification else ""
    if intent == "create_project":
        return "Create-project tasks need generation, project-local verification, requirement checking and packaging in sequence." + extra
    if intent == "repair_or_debug":
        return "Repair tasks should inspect evidence first, then use surgical repair and verification rather than broad rewrites." + extra
    if intent == "verify":
        return "Verification tasks should run checks and report evidence before proposing edits." + extra
    if intent == "improvement":
        return "Improvement tasks should test current state, make one project-local change, then verify." + extra
    if count > 1:
        return "Multi-step tasks should be executed one tool at a time with verification between stages." + extra
    return "The goal is not specific enough for direct mutation, so Nova should inspect and propose safe next steps." + extra
