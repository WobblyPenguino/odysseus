from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CapabilityRecord:
    """A concise machine-readable description of one Nova capability.

    Idle/autonomous code uses this catalog to decide what tool family to use,
    why it is useful, and which checks should follow. It intentionally lists
    capabilities rather than raw Python functions so plans stay understandable.
    """

    name: str
    commands: tuple[str, ...]
    tools: tuple[str, ...]
    use_when: tuple[str, ...]
    avoid_when: tuple[str, ...] = ()
    validates_with: tuple[str, ...] = ()
    risk: str = "low"
    produces: tuple[str, ...] = ()
    keywords: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class CapabilityMatch:
    capability: CapabilityRecord
    score: float
    why: str
    suggested_first_command: str

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capability"] = self.capability.to_dict()
        return data


@dataclass(frozen=True)
class MutablePlanStage:
    name: str
    purpose: str
    preferred_capabilities: tuple[str, ...]
    success_signals: tuple[str, ...]
    adapt_if: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class MutableMissionPlan:
    goal: str
    inferred_task_type: str
    confidence: float
    capabilities: tuple[CapabilityMatch, ...]
    stages: tuple[MutablePlanStage, ...]
    stop_conditions: tuple[str, ...]
    mutation_rules: tuple[str, ...]
    validation_contract: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]:
        return {
            "goal": self.goal,
            "inferred_task_type": self.inferred_task_type,
            "confidence": self.confidence,
            "capabilities": [m.to_dict() for m in self.capabilities],
            "stages": [s.to_dict() for s in self.stages],
            "stop_conditions": list(self.stop_conditions),
            "mutation_rules": list(self.mutation_rules),
            "validation_contract": list(self.validation_contract),
        }


def get_capability_catalog() -> tuple[CapabilityRecord, ...]:
    return (
        CapabilityRecord(
            name="project_build",
            commands=("/fast GOAL", "/long GOAL", "/project-spec GOAL"),
            tools=("project_spec", "ai_create_project", "write_files"),
            use_when=("the user asks to build an app, file set, script, tool, webpage or project",),
            avoid_when=("the user only asks a normal question", "the current project should be repaired instead of replaced"),
            validates_with=("auto_verify", "final_project_check", "project_quality_score"),
            risk="medium",
            produces=("project files", "README", "verification report"),
            keywords=("make", "build", "create", "app", "website", "file", "project", "tool"),
        ),
        CapabilityRecord(
            name="surgical_repair",
            commands=("/surgical-repair NOTE", "/fix-last"),
            tools=("surgical_repair", "known_error_recover", "final_project_check"),
            use_when=("validation fails but the project is close", "a specific file/error/selector/README claim is wrong"),
            avoid_when=("the generated artifact is completely unrelated",),
            validates_with=("node_syntax", "auto_verify", "final_project_check"),
            risk="medium",
            produces=("small diff", "repair report"),
            keywords=("fix", "repair", "broken", "error", "bug", "off course", "not working"),
        ),
        CapabilityRecord(
            name="candidate_validation",
            commands=("/test-project standard", "/project-target-check", "/release-gate final validation"),
            tools=("auto_verify", "final_project_check", "code_quality_gate", "project_runtime_probe"),
            use_when=("a candidate was generated", "before packaging or promoting changes", "when the model may be off course"),
            validates_with=("static_acceptance", "behavioural_contract", "project_quality_score"),
            risk="low",
            produces=("acceptance result", "quality score", "repair hints"),
            keywords=("validate", "verify", "test", "quality", "acceptance", "meets", "expectation"),
        ),
        CapabilityRecord(
            name="prompt_to_test",
            commands=("/prompt-contract GOAL", "/prompt-tests GOAL", "/prompt-test-run GOAL", "/contract-validate GOAL"),
            tools=("prompt_contract", "prompt_test_run"),
            use_when=("the prompt must be converted into must-have and must-not-have acceptance checks", "before /fast, /long, candidate generation, or repair"),
            avoid_when=("the user only wants a simple answer with no file/output validation",),
            validates_with=("prompt contract", "contract validation", "negative template checks"),
            risk="low",
            produces=("acceptance contract", "static checks", "negative checks"),
            keywords=("prompt", "contract", "test", "tests", "acceptance", "exact", "requirements", "expectation"),
        ),
        CapabilityRecord(
            name="candidate_tournament",
            commands=("/candidate-tournament GOAL", "/candidate-score GOAL", "/candidate-promote BEST", "/candidate-failure-report GOAL"),
            tools=("candidate_tournament", "candidate_failure_report"),
            use_when=("one model output may be weak or off-domain", "the user wants robust file building", "Dodge Game/default-template leakage has occurred"),
            avoid_when=("local model is very slow and the prompt only needs a tiny deterministic edit",),
            validates_with=("candidate score", "prompt contract", "project quality score"),
            risk="medium",
            produces=("ranked candidates", "winner", "failure report"),
            keywords=("candidate", "tournament", "compare", "best", "off course", "dodge", "default", "quality"),
        ),
        CapabilityRecord(
            name="surgical_repair_v2",
            commands=("/repair-diagnose", "/repair-plan", "/repair-apply", "/repair-verify", "/repair-rollback"),
            tools=("repair_plan_v2", "surgical_repair", "auto_verify"),
            use_when=("a generated project is close but has broken selectors, missing handlers, false README claims or wrong-domain evidence",),
            avoid_when=("no project/files are selected", "the user requested a fresh rebuild"),
            validates_with=("minimal-diff repair plan", "auto_verify", "final_project_check"),
            risk="medium",
            produces=("classified failure", "minimal repair steps", "rollback guidance"),
            keywords=("repair", "surgical", "minimal", "selector", "handler", "readme", "rollback"),
        ),
        CapabilityRecord(
            name="trace_observability",
            commands=("/trace-status", "/trace-timeline", "/trace-errors", "/performance-dashboard", "/replay-run RUN_ID"),
            tools=("trace_status", "activity_log", "efficiency_report"),
            use_when=("a run was slow, degraded, failed, or needs a copy/paste diagnosis", "autonomous/idle needs evidence before deciding"),
            validates_with=("trace events", "error timeline", "performance dashboard"),
            risk="low",
            produces=("trace timeline", "error list", "performance summary"),
            keywords=("trace", "timeline", "performance", "slow", "degraded", "replay", "errors"),
        ),
        CapabilityRecord(
            name="safe_mcp_connectors",
            commands=("/mcp-inspect", "/mcp-permissions", "/mcp-risk-report", "/mcp-sandbox-tool NAME", "/mcp-explain-tool NAME"),
            tools=("mcp_risk_report",),
            use_when=("tools/connectors need to be exposed or audited safely", "a new external capability may be useful"),
            avoid_when=("the connector asks for arbitrary command execution without allowlisting",),
            validates_with=("MCP risk report", "permission review", "sandboxed test"),
            risk="medium",
            produces=("connector manifest", "risk report", "permission policy"),
            keywords=("mcp", "connector", "tool", "permission", "external", "manifest"),
        ),
        CapabilityRecord(
            name="mission_planner",
            commands=("/mission-create GOAL", "/mission-status", "/mission-step", "/mission-queue", "/mission-stop"),
            tools=("mission_create", "mission_step", "autonomous_memory"),
            use_when=("a broad autonomous/idle goal needs success conditions, tool allowlists and stop conditions",),
            validates_with=("mission queue", "success conditions", "stop conditions"),
            risk="low",
            produces=("mission object", "next step", "queue"),
            keywords=("mission", "queue", "autonomous", "idle", "goal", "stop", "success"),
        ),
        CapabilityRecord(
            name="model_output_coach",
            commands=("/model-output-score GOAL", "/model-output-coach GOAL", "/model-output-repair-json", "/model-output-off-course"),
            tools=("model_output_coach",),
            use_when=("local model output is invalid JSON, fenced, off-domain, split into wrong files, or contaminated by defaults",),
            validates_with=("JSON/file split checks", "off-course detector", "coaching prompt"),
            risk="low",
            produces=("model score", "coaching prompt", "JSON repair advice"),
            keywords=("model", "json", "fence", "off course", "split", "files", "coach"),
        ),
        CapabilityRecord(
            name="environment_profiles",
            commands=("/env-profile minimal", "/env-doctor", "/env-fix-plan", "/env-install-plan"),
            tools=("env_profile", "dependency_check"),
            use_when=("a feature depends on Python, pytest, Ollama, git, node, Docker, Playwright or AI-heavy tooling",),
            validates_with=("env profile", "dependency check"),
            risk="low",
            produces=("profile report", "install plan"),
            keywords=("env", "environment", "dependency", "install", "profile", "setup"),
        ),
        CapabilityRecord(
            name="project_state_regression_memory",
            commands=("/project-state", "/project-history", "/regression-list", "/regression-add"),
            tools=("project_state", "regression_list", "regression_add"),
            use_when=("Nova must remember project failures, success criteria, repairs or user-reported regressions",),
            validates_with=("project state database", "regression memory export"),
            risk="low",
            produces=("project state", "regression memory"),
            keywords=("project state", "history", "failure", "regression", "memory", "remember"),
        ),
        CapabilityRecord(
            name="custom_tool_extension",
            commands=("/tool-create GOAL", "/tool-test NAME", "/tool-run NAME => JSON", "/custom-tools"),
            tools=("tool_create", "tool_test", "tool_run", "custom_tools"),
            use_when=("a reusable safe local helper would make the task easier", "the user asks Nova to make its own tool", "a repeated workflow can be automated"),
            avoid_when=("the tool would need unrestricted shell/network/host access", "a built-in command already solves the task"),
            validates_with=("safe custom tool validator", "tool_test", "tool_run output"),
            risk="medium",
            produces=("safe custom tool", "tool test report", "tool output"),
            keywords=("custom tool", "make its own tool", "tool-create", "reusable", "automate", "helper"),
        ),

        CapabilityRecord(
            name="iterative_coding_repair",
            commands=("/iterative-code-loop GOAL", "/surgical-fallback-v2 GOAL", "/edit-repair-plan GOAL", "/repair-strategy GOAL"),
            tools=("iterative_coding_loop", "surgical_fallback_v2", "edit_repair_plan", "prompt_contract", "build_quality_report", "browser_runtime_test", "model_output_coach"),
            use_when=("a generated app/file set needs repeated edit-test-repair passes", "surgical repair failed or backtracking is about to start", "the user asks to improve editing, fallback, or iterative coding capabilities"),
            avoid_when=("there are no project files to inspect", "the user only asks a normal chat question"),
            validates_with=("prompt contract", "build quality", "browser runtime/static wiring", "final project check"),
            risk="medium",
            produces=("iterative coding plan", "minimal repair targets", "promotion gate"),
            keywords=("iterative", "coding", "edit", "editing", "surgical", "fallback", "repair", "loop", "test and repair", "validate then change"),
        ),
        CapabilityRecord(
            name="sandbox_dev_copy",
            commands=("/sandbox-dev-run linux CMD", "/sandbox-dev-run kali CMD", "/docker-validate quick"),
            tools=("sandbox_dev_run", "docker_validate", "docker_patch_validate"),
            use_when=("code should be tested in a writable copy", "live files must not be touched until checks pass"),
            avoid_when=("the command needs live user files", "network/offensive Kali activity is not authorised"),
            validates_with=("compileall", "pytest", "sandbox command return code"),
            risk="medium",
            produces=("copied workspace", "stdout/stderr", "validation report"),
            keywords=("sandbox", "linux", "kali", "docker", "copy", "without touching", "validate"),
        ),
        CapabilityRecord(
            name="log_investigation",
            commands=("/activity", "/investigate-logs FOCUS", "/known-issues"),
            tools=("activity_log", "investigate_logs", "known_issues"),
            use_when=("recent behaviour is confusing", "a command failed", "idle/autonomous repeated a bad path"),
            validates_with=("error signatures", "known issue report"),
            risk="low",
            produces=("ERROR_INVESTIGATION.md", "failure signatures"),
            keywords=("logs", "output", "activity", "why", "degraded", "failed", "stuck", "slow"),
        ),
        CapabilityRecord(
            name="whole_codebase_review",
            commands=("/whole-codebase-review", "/review-codebase", "/comprehensive-code-review"),
            tools=("whole_codebase_review", "review_codebase", "comprehensive_code_review"),
            use_when=("the user asks to review the whole codebase", "after many new features were added", "before or after a broad improvement pass"),
            validates_with=("syntax scan", "command/tool integration scan", "release hygiene", "documentation/version consistency"),
            risk="low",
            produces=("whole-codebase review report", "integration warnings", "improvement follow-ups"),
            keywords=("whole codebase", "entire codebase", "review the codebase", "comprehensive review", "all code", "look for ways to improve"),
        ),
        CapabilityRecord(
            name="regression_sweep",
            commands=("/regression-sweep", "/no-regression-check", "/functionality-matrix", "/integration-health"),
            tools=("regression_sweep", "functionality_matrix", "integration_health"),
            use_when=("the user asks whether any functionality regressed", "after adding major command families", "before sharing a release zip"),
            validates_with=("command visibility", "ToolRegistry exposure", "capability catalog coverage", "feature-audit chat formatting", "release hygiene"),
            risk="low",
            produces=("cross-feature regression matrix", "integration health recommendations"),
            keywords=("regression", "regressed", "functionality", "damaged", "all features", "integration", "no errors", "whole codebase"),
        ),
        CapabilityRecord(
            name="bug_review",
            commands=("/bug-review", "/bug-hunt", "/bug-sweep", "/error-review"),
            tools=("bug_review", "bug_hunt", "bug_sweep", "error_review"),
            use_when=("the user asks for more bug review", "after broad command families are added", "before packaging a release after many patches"),
            validates_with=("syntax scan", "version marker scan", "command/tool integration scan", "chat markdown formatting scan", "release hygiene"),
            risk="low",
            produces=("bug review report", "blocking findings", "diagnostic warnings"),
            keywords=("bug review", "bug hunt", "bugs", "errors", "error review", "more bug", "broken", "regression"),
        ),
        CapabilityRecord(
            name="weakspot_error_hunt",
            commands=("/weakspot-audit", "/error-hunt", "/stability-audit"),
            tools=("weakspot_audit", "error_hunt"),
            use_when=("the user asks for weak spots, more error testing, or a broad regression sweep", "before packaging a risky autonomy/tooling change"),
            validates_with=("weakspot report", "silent exception scan", "autonomy command coverage", "release hygiene scan"),
            risk="low",
            produces=("NOVA_WEAKSPOT_AUDIT_LATEST.md", "actionable bug list"),
            keywords=("weakspot", "weak spots", "error testing", "bug hunt", "regression", "stability", "audit"),
        ),
        CapabilityRecord(
            name="improvement_proposal_cycle",
            commands=("/improvement-proposals FOCUS", "/improvement-cycle --confirm", "/completed-improvements"),
            tools=("improvement_proposals_v2", "improvement_cycle", "improvement_status"),
            use_when=("the user asks to propose improvements and do/complete them", "idle/autonomous needs ranked safe next actions with completed/skipped status", "after bug/user testing finds several low-risk improvements"),
            avoid_when=("the requested change is high-risk source mutation without validation",),
            validates_with=("improvement cycle report", "regression-memory seeds", "wla-mega-test", "release hygiene"),
            risk="low",
            produces=("ranked proposals", "completed proposal report", "done/skipped statuses"),
            keywords=("proposal", "proposals", "improvement", "improvements", "complete", "do them", "implement proposals"),
        ),
        CapabilityRecord(
            name="improvement_roadmap",
            commands=("/improvement-roadmap FOCUS", "/improvement-impact FOCUS", "/implement-improvements --confirm FOCUS", "/proposal-ledger"),
            tools=("improvement_roadmap", "improvement_impact", "implement_improvements", "proposal_ledger"),
            use_when=("the user asks to propose improvements and implement them", "after a no-regression sweep finds safe follow-up work", "idle/autonomous needs a ranked roadmap and completed ledger before repeating proposal work"),
            avoid_when=("the user needs an immediate direct answer and no code/tool changes",),
            validates_with=("impact matrix", "proposal ledger", "regression sweep", "wla mega-test"),
            risk="low",
            produces=("ranked roadmap", "impact matrix", "completed implementation ledger", "validation pack"),
            keywords=("propose", "improvement", "improvements", "implement", "roadmap", "ledger", "impact", "next"),
        ),

        CapabilityRecord(
            name="build_quality_browser_runtime",
            commands=("/build-quality-report GOAL", "/browser-run-test GOAL", "/browser-storage-test GOAL", "/browser-export-test GOAL"),
            tools=("build_quality_report", "browser_runtime_test"),
            use_when=("the user asks to improve generated app quality", "a project technically validates but may not satisfy the prompt", "before accepting /fast or /long output"),
            validates_with=("build quality score", "browser runtime wiring checks", "prompt-specific storage/export checks"),
            risk="low",
            produces=("build quality report", "browser runtime test report"),
            keywords=("quality", "browser", "runtime", "click", "storage", "export", "good app", "actually works"),
        ),
        CapabilityRecord(
            name="model_reliability_controller",
            commands=("/model-reliability", "/model-fallback-strategy", "/model-json-enforcer", "/model-stuck-diagnose"),
            tools=("model_reliability", "model_fallback_strategy", "model_output_coach"),
            use_when=("the local model is slow, degraded, stuck, returning bad JSON, or repeatedly off-course",),
            validates_with=("recent model attempt/rejection counts", "fallback strategy", "model output coaching"),
            risk="low",
            produces=("model reliability report", "retry/fallback strategy"),
            keywords=("model", "ollama", "stuck", "slow", "degraded", "json", "retry", "off course", "fallback"),
        ),
        CapabilityRecord(
            name="interaction_flow_validation",
            commands=("/flow-audit", "/interaction-flow-audit", "/command-flow-verify", "/learning-loop-audit", "/flow-improvements"),
            tools=("flow_audit", "interaction_flow_audit", "command_flow_verify", "learning_loop_audit", "flow_improvements"),
            use_when=("the user asks to ensure new features did not regress old pathways", "after adding many commands/tools", "idle/autonomous needs to verify command, tool and capability integration before acting"),
            avoid_when=("the task is a simple one-off answer that does not involve Nova feature integration",),
            validates_with=("flow group audit", "ToolRegistry coverage", "capability catalog coverage", "scenario tool-choice checks"),
            risk="low",
            produces=("interaction flow report", "command coverage matrix", "learning-loop audit"),
            keywords=("flow", "pathway", "pathways", "no regression", "regress", "functionality", "coverage", "learn", "mistakes", "whole codebase", "all commands"),
        ),

        CapabilityRecord(
            name="model_dependency_management",
            commands=("/model-requirements GOAL", "/model-readiness GOAL", "/model-download-plan GOAL", "/model-install NAME --confirm"),
            tools=("model_readiness", "model_requirements", "model_download_plan", "model_install"),
            use_when=("a task needs a missing local model", "the local model is degraded because the selected model is absent", "the user asks Nova to request or download required models", "a stronger coder/vision/embedding model would materially improve the task"),
            avoid_when=("the current installed model is already adequate", "download was not explicitly confirmed", "the task can be solved deterministically without model help"),
            validates_with=("ollama list", "model readiness report", "explicit install command review"),
            risk="medium",
            produces=("model requirements", "download plan", "confirmable ollama pull command", "install report"),
            keywords=("download model", "required model", "missing model", "ollama pull", "stronger model", "vision model", "embed", "model install"),
        ),
        CapabilityRecord(
            name="patch_queue_and_learning",
            commands=("/patch-queue", "/patch-propose", "/patch-validate", "/patch-promote", "/mistake-learning-status"),
            tools=("patch_queue", "regression_test_generate", "mistake_learning_status"),
            use_when=("autonomous/idle wants to stage changes safely", "a bug should become a regression seed", "the user asks Nova to learn from mistakes"),
            validates_with=("patch queue status", "regression seed", "mega-test"),
            risk="low",
            produces=("patch ledger", "mistake-learning loop", "regression seed"),
            keywords=("patch", "queue", "learn", "mistake", "rollback", "promote", "regression test"),
        ),
        CapabilityRecord(
            name="support_and_error_translation",
            commands=("/support-report", "/explain-error", "/error-fix-plan", "/copy-debug-context"),
            tools=("support_report", "explain_error"),
            use_when=("the user wants a clean report to paste into ChatGPT", "raw errors need translation", "the GUI/backend connection failed"),
            validates_with=("support report", "trace errors", "activity tail"),
            risk="low",
            produces=("support report", "error explanation", "next-step plan"),
            keywords=("support", "report", "chatgpt", "explain error", "failed to fetch", "debug context"),
        ),
        CapabilityRecord(
            name="templates_preview_feature_readiness",
            commands=("/template-list", "/template-build notes-app", "/preview-status", "/feature-readiness"),
            tools=("template_list", "template_build", "preview_server", "feature_readiness"),
            use_when=("the user asks for common apps like notes/dashboard/timer", "local model generation would be slower than a deterministic template", "features should be hidden/downgraded based on dependencies"),
            validates_with=("template manifest", "browser runtime test", "feature readiness report"),
            risk="low",
            produces=("deterministic template files", "preview instructions", "feature readiness matrix"),
            keywords=("template", "notes app", "dashboard", "timer", "preview", "feature readiness", "dependency"),
        ),

        CapabilityRecord(
            name="mission_intelligence",
            commands=("/mission-dashboard", "/mission-progress", "/mission-retrospective", "/mission-resume"),
            tools=("mission_dashboard", "mission_progress", "autonomous_last_report"),
            use_when=("autonomous or idle needs a real mission state, progress, next action and stop reason",),
            validates_with=("mission dashboard", "progress score", "tool-choice trace"),
            risk="low",
            produces=("mission dashboard", "next best action", "stop reason"),
            keywords=("mission dashboard", "mission progress", "autonomous useful", "idle useful", "goal directed"),
        ),
        CapabilityRecord(
            name="cycle_progress_scoring",
            commands=("/cycle-score", "/autonomous-progress-score", "/idle-progress-score"),
            tools=("cycle_score", "autonomous_progress_score", "idle_progress_score"),
            use_when=("after any idle/autonomous cycle", "when deciding whether a cycle actually made progress"),
            validates_with=("progress buckets", "no-progress recommendations"),
            risk="low",
            produces=("progress score", "recommendations"),
            keywords=("score", "progress", "cycle score", "actually helped", "no progress"),
        ),
        CapabilityRecord(
            name="tool_choice_trace",
            commands=("/tool-choice-trace GOAL", "/autonomous-explain-tools GOAL", "/idle-explain-tools GOAL"),
            tools=("tool_choice_trace", "autonomous_explain_tools", "idle_explain_tools"),
            use_when=("autonomous/idle must explain why it picked a tool", "a plan needs evidence for which command should run next"),
            validates_with=("tool reasons", "when/avoid guidance"),
            risk="low",
            produces=("tool-choice explanation",),
            keywords=("why this tool", "explain tools", "tool choice", "when to use"),
        ),
        CapabilityRecord(
            name="repetition_guard",
            commands=("/repetition-guard-status", "/repetition-memory", "/repetition-clear"),
            tools=("repetition_guard_status", "repetition_memory", "repetition_clear"),
            use_when=("the same model rejection, repair attempt or no-op proposal repeats",),
            validates_with=("failure signatures", "repetition count"),
            risk="low",
            produces=("repeat strategy warning", "strategy switch recommendation"),
            keywords=("repeat", "repeating", "same failure", "loop", "stuck", "no-op"),
        ),
        CapabilityRecord(
            name="background_idle_controls",
            commands=("/idle-background-only on", "/idle-summaries off", "/idle-silence on"),
            tools=("idle_background_settings",),
            use_when=("idle should analyse quietly without overwriting active user work",),
            validates_with=("idle settings", "foreground quiet window"),
            risk="low",
            produces=("idle background policy",),
            keywords=("idle noisy", "background only", "silence", "summaries off", "foreground"),
        ),
        CapabilityRecord(
            name="mistake_learning_regression",
            commands=("/mistake-log", "/mistake-to-regression", "/regression-protection-status"),
            tools=("mistake_log", "mistake_to_regression", "regression_test_generate"),
            use_when=("a failed cycle should become a lesson/regression instead of being forgotten",),
            validates_with=("mistake log", "regression seed"),
            risk="low",
            produces=("mistake lesson", "regression seed"),
            keywords=("learn from mistakes", "mistake log", "regression", "lesson", "failed cycle"),
        ),
        CapabilityRecord(
            name="release_hygiene",
            commands=("/release-hygiene", "/release-hygiene clean", "/nova-doctor"),
            tools=("release_hygiene", "wla_doctor", "wla_release_gate"),
            use_when=("before packaging", "doctor reports cache artifacts", "version labels changed"),
            validates_with=("release_hygiene", "wla_doctor", "release_gate"),
            risk="low",
            produces=("hygiene report", "cleaned release tree"),
            keywords=("release", "package", "zip", "hygiene", "cache", "pyc", "version"),
        ),
        CapabilityRecord(
            name="model_help_planning",
            commands=("/model-help-plan GOAL", "/model-help-implement GOAL"),
            tools=("model_context", "local_model", "improve_project"),
            use_when=("deterministic tools are not enough", "a repair plan needs model interpretation", "candidate keeps going off course"),
            avoid_when=("a local model prompt is already active", "a deterministic surgical repair is obvious"),
            validates_with=("plan JSON shape", "guarded implementation checks"),
            risk="medium",
            produces=("local model plan", "guarded improvement attempt"),
            keywords=("model", "help", "plan", "context", "off course", "iterate", "candidate"),
        ),
        CapabilityRecord(
            name="autonomous_memory",
            commands=("/autonomous-memory", "/autonomous-journal", "/auto-explain"),
            tools=("autonomous_memory", "cycle_schema", "autonomous_journal"),
            use_when=("autonomous mode repeated work", "the user wants to know what happened", "a plan needs mutation rules"),
            validates_with=("cycle journal", "progress score", "stop condition"),
            risk="low",
            produces=("cycle summary", "next strategy hint"),
            keywords=("autonomous", "idle", "summary", "cycle", "plan", "tools", "capabilities"),
        ),
    )


def select_capabilities_for_goal(goal: str, limit: int = 5) -> tuple[CapabilityMatch, ...]:
    text = (goal or "").lower()
    matches: list[CapabilityMatch] = []
    for cap in get_capability_catalog():
        hits = [kw for kw in cap.keywords if kw and kw in text]
        score = min(1.0, 0.15 + 0.16 * len(hits))
        if cap.name in {"log_investigation", "candidate_validation"}:
            score += 0.08  # usually useful as supporting capabilities
        if cap.name == "custom_tool_extension" and any(w in text for w in ("tool", "custom tool", "make its own", "helper")):
            score += 0.35
        if cap.name == "candidate_tournament" and any(w in text for w in ("candidate", "tournament", "compare")):
            score += 0.45
        if cap.name == "prompt_to_test" and any(w in text for w in ("prompt", "acceptance", "requirements", "tests")):
            score += 0.30
        if cap.name == "build_quality_browser_runtime" and any(w in text for w in ("quality", "works", "browser", "runtime", "app")):
            score += 0.20
        if cap.name == "patch_queue_and_learning" and any(w in text for w in ("learn", "mistake", "patch", "rollback", "regression")):
            score += 0.25
        if cap.name in {"mission_intelligence", "cycle_progress_scoring", "tool_choice_trace", "repetition_guard"} and any(w in text for w in ("autonomous", "idle", "mission", "repeat", "progress", "useless")):
            score += 0.35
        if cap.name == "background_idle_controls" and any(w in text for w in ("idle", "background", "noisy", "summaries", "foreground")):
            score += 0.30
        if cap.name == "interaction_flow_validation" and any(w in text for w in ("flow", "pathway", "regress", "regression", "functionality", "all commands", "learn", "mistakes")):
            score += 0.35
        if hits or score >= 0.23:
            matches.append(CapabilityMatch(
                capability=cap,
                score=round(min(score, 1.0), 2),
                why=("matched keywords: " + ", ".join(hits)) if hits else "supporting capability for safe autonomous planning",
                suggested_first_command=cap.commands[0],
            ))
    matches.sort(key=lambda m: (m.score, -len(m.capability.avoid_when)), reverse=True)
    return tuple(matches[: max(1, limit)])


def infer_task_type(goal: str) -> tuple[str, float]:
    low = (goal or "").lower()
    buckets = [
        ("create_project", ("make", "build", "create", "app", "website", "script", "project")),
        ("repair_or_debug", ("fix", "repair", "broken", "error", "bug", "not working", "off course")),
        ("validate", ("validate", "verify", "test", "quality", "acceptance")),
        ("sandbox_dev", ("sandbox", "linux", "kali", "docker", "without touching")),
        ("autonomy_upgrade", ("autonomous", "idle", "capabilities", "tools", "plans", "self")),
    ]
    best_name = "general_improvement"
    best_hits = 0
    for name, words in buckets:
        hits = sum(1 for w in words if w in low)
        if hits > best_hits:
            best_name, best_hits = name, hits
    return best_name, round(min(0.98, 0.45 + best_hits * 0.12), 2)


def build_mutable_mission_plan(goal: str) -> MutableMissionPlan:
    task_type, confidence = infer_task_type(goal)
    caps = select_capabilities_for_goal(goal, limit=12)
    cap_names = tuple(m.capability.name for m in caps)
    validation_focus = _validation_contract_for(goal, task_type)
    stages = (
        MutablePlanStage(
            name="observe",
            purpose="Resolve the target workspace, recent failures, model state and available capability set before acting.",
            preferred_capabilities=tuple(n for n in ("log_investigation", "autonomous_memory") if n in cap_names) or ("log_investigation",),
            success_signals=("correct workspace selected", "recent blockers classified", "no active local model prompt conflict"),
            adapt_if=("if target has no source files, switch to target-resolution instead of code review",),
        ),
        MutablePlanStage(
            name="plan",
            purpose="Compile a task-specific acceptance contract and choose the smallest useful tool sequence.",
            preferred_capabilities=cap_names[:4] or ("candidate_validation",),
            success_signals=("must-have and must-not-have checks are explicit", "chosen tools explain why they match the prompt"),
            adapt_if=("if confidence is low, ask/plan before mutation", "if a prior default-template bug exists, add negative checks"),
        ),
        MutablePlanStage(
            name="act",
            purpose="Make one bounded change or build attempt in the safest suitable environment.",
            preferred_capabilities=tuple(n for n in cap_names if n in {"sandbox_dev_copy", "project_build", "surgical_repair", "model_help_planning"}) or cap_names[:2],
            success_signals=("files changed only in the intended target", "candidate matches the prompt domain"),
            adapt_if=("if generated candidate is off-course, preserve it as evidence and use surgical/model-help repair",),
        ),
        MutablePlanStage(
            name="validate",
            purpose="Run prompt-derived positive and negative checks before any promotion or final answer.",
            preferred_capabilities=tuple(n for n in ("candidate_validation", "sandbox_dev_copy", "release_hygiene") if n in cap_names) or ("candidate_validation",),
            success_signals=validation_focus,
            adapt_if=("if validation fails, classify the failure and move to repair rather than regenerate blindly",),
        ),
        MutablePlanStage(
            name="reflect",
            purpose="Record what worked, what failed, what tool should be preferred next time, and when to stop.",
            preferred_capabilities=("autonomous_memory", "log_investigation"),
            success_signals=("cycle report names changed files/tools", "next strategy is different after repeated no-progress"),
            adapt_if=("if two cycles have no useful change, stop and report instead of looping",),
        ),
    )
    return MutableMissionPlan(
        goal=(goal or "Improve Nova safely").strip(),
        inferred_task_type=task_type,
        confidence=confidence,
        capabilities=caps,
        stages=stages,
        stop_conditions=(
            "all prompt-specific acceptance checks pass",
            "local model is unavailable or already busy and deterministic tools cannot continue",
            "same blocker repeats twice without a new tool/strategy",
            "requested action needs user permission or unsafe external/network activity",
        ),
        mutation_rules=(
            "prefer copied sandbox/worktree validation before live promotion",
            "never replace a project when surgical repair can satisfy the prompt",
            "each mutation must add or update validation evidence",
            "negative checks must block unrelated defaults such as Dodge Game when the prompt is not a dodge game",
        ),
        validation_contract=validation_focus,
    )


def render_capability_markdown(goal: str) -> str:
    plan = build_mutable_mission_plan(goal)
    lines = [
        "# Autonomous/Idle Capability Map",
        "",
        f"Goal: {plan.goal}",
        f"Inferred task type: {plan.inferred_task_type}",
        f"Confidence: {plan.confidence:.2f}",
        "",
        "## Selected capabilities",
    ]
    for match in plan.capabilities:
        cap = match.capability
        lines += [
            f"- **{cap.name}** — score {match.score:.2f}",
            f"  - why: {match.why}",
            f"  - use when: {'; '.join(cap.use_when)}",
            f"  - first command: `{match.suggested_first_command}`",
            f"  - validates with: {', '.join(cap.validates_with) or 'manual evidence'}",
        ]
    lines += ["", "## Mutable plan stages"]
    for stage in plan.stages:
        lines += [
            f"- **{stage.name}**: {stage.purpose}",
            f"  - capabilities: {', '.join(stage.preferred_capabilities)}",
            f"  - success: {', '.join(stage.success_signals)}",
            f"  - adapt if: {', '.join(stage.adapt_if)}",
        ]
    lines += ["", "## Stop conditions"] + [f"- {x}" for x in plan.stop_conditions]
    return "\n".join(lines)


def _validation_contract_for(goal: str, task_type: str) -> tuple[str, ...]:
    low = (goal or "").lower()
    checks = ["output matches the original user prompt", "no unrelated default/template behaviour appears"]
    if any(w in low for w in ("localstorage", "save", "persist")):
        checks.append("localStorage save/load is implemented with safe JSON fallback")
    if any(w in low for w in ("export", "json", "download")):
        checks.append("export/download behaviour exists and README claims match code")
    if task_type == "sandbox_dev":
        checks.append("test code runs in a copied writable workspace and live files remain untouched")
    if task_type == "repair_or_debug":
        checks.append("the specific observed failure no longer reproduces")
    if task_type == "autonomy_upgrade":
        checks.append("idle/autonomous summary includes tools, reasons, capabilities, and next adaptation")
    return tuple(checks)
