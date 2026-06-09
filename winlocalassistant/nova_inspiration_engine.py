from __future__ import annotations

"""Additive Nova workflow intelligence inspired by modern agent products.

This module is deliberately read-only. It builds planning, routing, and
preflight reports that help Nova pick better tools and validations without
changing autonomous execution, shell permissions, project files, or wake-word
behaviour.
"""

import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Iterable

LOGGER = logging.getLogger(__name__)

PROTECTED_FILE_HINTS = (
    "winlocalassistant/core.py",
    "winlocalassistant/tools.py",
    "winlocalassistant/security.py",
    ".env",
    ".key",
    ".pem",
    ".pfx",
)

MUTATING_COMMAND_HINTS = (
    "write_file",
    "write_files",
    "append_file",
    "find_replace",
    "run_shell",
    "shell",
    "self_improve",
    "install_package",
    "patch_promote",
    "repair_apply",
    "delete",
    "tool_delete",
    "docker_clean",
)

VALIDATION_BASELINE = (
    "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py",
    "python tests_smoke.py",
)

KEYWORD_TOOL_GROUPS: dict[str, tuple[str, ...]] = {
    "voice": ("voice_audit", "voice_device_status", "voice_calibrate", "startup_validation", "nova_system_test"),
    "wake": ("voice_audit", "startup_validation", "nova_system_test", "flow_audit"),
    "gui": ("gui_feature_coverage", "gui_regression_test", "gui_snapshot", "browser_run_test", "feature_readiness"),
    "webui": ("gui_feature_coverage", "gui_regression_test", "gui_snapshot", "browser_run_test"),
    "code": ("code_review_audit", "code_quality_gate", "repair_audit", "architecture_audit", "regression_sweep"),
    "bug": ("bug_review", "regression_sweep", "repair_audit", "explain_error", "mistake_to_regression"),
    "test": ("command_verify", "regression_sweep", "nova_system_test", "wla_mega_test", "architecture_audit"),
    "model": ("model_health", "model_doctor", "model_reliability", "local_model_optimizer", "model_readiness"),
    "ollama": ("model_health", "model_doctor", "ollama_multi_report", "local_model_optimizer"),
    "docker": ("docker_status", "docker_validate", "sandbox_status", "benchmark_docker"),
    "image": ("image_analyze", "image_generate", "vision_status", "vision_model"),
    "file": ("context_files", "attach_file", "search_text", "docs_index"),
    "autonomous": ("autonomy_capabilities", "mission_contract", "tool_choice_trace", "cycle_score", "idle_policy"),
    "improve": ("improvement_roadmap", "proposal_ledger_view", "anti_repeat_check", "feature_continuity_audit"),
    "schedule": ("task_scheduler", "list_tasks", "analytics", "performance_report"),
    "analytics": ("analytics", "performance_report", "trace_last", "telemetry_export"),
}

DEFAULT_TOOL_SEED = (
    "status",
    "command_catalog",
    "model_health",
    "architecture_audit",
    "regression_sweep",
    "feature_continuity_audit",
    "analytics",
    "performance_report",
)


@dataclass
class InspirationIdea:
    title: str
    source_pattern: str
    value: int
    risk: str
    implemented_now: str
    why_it_helps: str
    suggested_command: str
    validation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "title": self.title,
            "source_pattern": self.source_pattern,
            "value": self.value,
            "risk": self.risk,
            "implemented_now": self.implemented_now,
            "why_it_helps": self.why_it_helps,
            "suggested_command": self.suggested_command,
            "validation": list(self.validation),
        }


@dataclass
class HandoffStep:
    name: str
    responsibility: str
    trigger: str
    tools: list[str]
    exit_check: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "responsibility": self.responsibility,
            "trigger": self.trigger,
            "tools": list(self.tools),
            "exit_check": self.exit_check,
        }


def _normalise_tool_names(tool_names: Iterable[str] | None) -> set[str]:
    return {str(name).strip().replace("-", "_") for name in (tool_names or []) if str(name).strip()}


def _root_snapshot(root: Path) -> dict[str, Any]:
    root = Path(root)
    files = {
        "agents_md": (root / "AGENTS.md").exists(),
        "smoke_tests": (root / "tests_smoke.py").exists(),
        "changelog": (root / "CHANGELOG.md").exists(),
        "readme": (root / "README.md").exists(),
        "docs_dir": (root / "docs").is_dir(),
        "webui": (root / "winlocalassistant" / "webui.py").exists(),
        "core": (root / "winlocalassistant" / "core.py").exists(),
        "tools": (root / "winlocalassistant" / "tools.py").exists(),
    }
    test_count = 0
    py_count = 0
    try:
        test_count = sum(1 for _ in root.glob("tests_*.py"))
        py_count = sum(1 for _ in (root / "winlocalassistant").glob("*.py"))
    except Exception:
        LOGGER.debug("Failed to count Nova inspiration snapshot files under %s", root, exc_info=True)
    return {"root": str(root), "files": files, "test_count": test_count, "module_count": py_count}


def build_tool_context_pack(prompt: str, tool_names: Iterable[str] | None, *, max_tools: int = 18) -> dict[str, Any]:
    """Build a compact, prompt-aware tool shortlist for local-model context."""
    prompt_text = (prompt or "").strip()
    lowered = prompt_text.lower()
    available = _normalise_tool_names(tool_names)
    scores: dict[str, dict[str, Any]] = {}

    def bump(tool: str, points: int, reason: str) -> None:
        norm = tool.replace("-", "_")
        if available and norm not in available:
            return
        entry = scores.setdefault(norm, {"tool": norm, "score": 0, "reasons": []})
        entry["score"] += points
        entry["reasons"].append(reason)

    for tool in DEFAULT_TOOL_SEED:
        bump(tool, 2, "baseline diagnostic/context tool")

    for keyword, tools in KEYWORD_TOOL_GROUPS.items():
        if keyword in lowered:
            for tool in tools:
                bump(tool, 6, f"prompt mentions {keyword!r}")

    # Extra semantic nudges for common Nova phrasing and typos.
    if any(word in lowered for word in ("nova", "wla", "assistant", "workflow", "tool")):
        for tool in ("command_catalog", "tool_choice_trace", "autonomy_capabilities", "feature_continuity_audit"):
            bump(tool, 4, "Nova/Nova workflow relevance")
    if any(word in lowered for word in ("regression", "no regression", "does not break", "preserve", "continuity")):
        for tool in ("regression_sweep", "feature_continuity_audit", "architecture_audit", "command_verify"):
            bump(tool, 7, "explicit no-regression requirement")
    if any(word in lowered for word in ("implement", "build", "fix", "patch", "change")):
        for tool in ("improvement_preflight", "code_quality_gate", "regression_sweep", "architecture_audit"):
            bump(tool, 5, "implementation/change request")

    selected = sorted(scores.values(), key=lambda item: (-int(item["score"]), str(item["tool"])))[: max(1, max_tools)]
    selected_tools = [str(item["tool"]) for item in selected]
    hidden = sorted(available - set(selected_tools))[:50] if available else []
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": prompt_text,
        "max_tools": max_tools,
        "selected_tools": selected,
        "selected_tool_names": selected_tools,
        "hidden_available_tool_count": max(0, len(available) - len(selected_tools)) if available else 0,
        "hidden_available_preview": hidden,
        "policy": "read-only context packing; no tool is executed by this report",
    }


def build_handoff_plan(prompt: str, tool_names: Iterable[str] | None = None) -> dict[str, Any]:
    """Build a deterministic role handoff plan for Nova without spawning agents."""
    tools = _normalise_tool_names(tool_names)
    context = build_tool_context_pack(prompt, tools, max_tools=20)
    chosen = set(context["selected_tool_names"])

    def have(*names: str) -> list[str]:
        result = []
        for name in names:
            norm = name.replace("-", "_")
            if not tools or norm in tools:
                result.append(norm)
        return result

    steps = [
        HandoffStep(
            "Intake router",
            "Normalize the request, detect ambiguity, and decide whether this is chat, code, GUI, voice, model, or autonomous work.",
            "Any user goal before tools are used.",
            have("command_catalog", "tool_context_pack", "planning_dashboard"),
            "A short plan exists and the selected tools fit the prompt.",
        ),
        HandoffStep(
            "Planner",
            "Break the task into ordered subtasks and identify protected behaviours that must not regress.",
            "The request implies implementation, debugging, or multi-step improvement.",
            have("improvement_preflight", "autonomy_capabilities", "mission_contract", "feature_continuity_audit"),
            "Preflight risk, expected files, and validation commands are known.",
        ),
        HandoffStep(
            "Builder",
            "Make additive or surgical changes only after the plan and preflight checks are clear.",
            "The user explicitly asked for implementation or repair.",
            have("code_quality_gate", "repair_audit", "project_spec", "template_manifest"),
            "Changes are small, reversible, and avoid protected behaviours unless explicitly approved.",
        ),
        HandoffStep(
            "Verifier",
            "Run syntax, smoke, targeted functional tests, and no-regression checks before claiming success.",
            "After any source change, test update, or release package.",
            have("regression_sweep", "architecture_audit", "nova_system_test", "command_verify"),
            "Validation output proves old functionality still loads and the new feature has tests.",
        ),
        HandoffStep(
            "Reporter",
            "Summarize what changed, what passed, what could not be tested, and the next safe command for the user.",
            "At the end of each improvement cycle.",
            have("proposal_ledger_view", "completed_improvements", "release_package", "analytics"),
            "The user receives exact changed files, test results, and a downloadable package when applicable.",
        ),
    ]

    if chosen.intersection({"voice_audit", "voice_device_status", "voice_calibrate"}):
        steps.insert(
            2,
            HandoffStep(
                "Voice UX specialist",
                "Preserve wake/listen/speak handoff timing and avoid changing headset/audio behaviour without focused tests.",
                "The prompt mentions wake word, mic, headset, speaking, or voice mode.",
                have("voice_audit", "voice_device_status", "voice_calibrate", "startup_validation"),
                "Voice state changes remain observable and no new always-on mutation is introduced.",
            ),
        )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "prompt": (prompt or "").strip(),
        "steps": [step.to_dict() for step in steps],
        "context_pack": context,
        "policy": "deterministic handoff plan only; does not spawn autonomous agents or run mutating tools",
    }


def build_improvement_preflight(
    goal: str,
    *,
    changed_files: Iterable[str] | None = None,
    intended_commands: Iterable[str] | None = None,
) -> dict[str, Any]:
    """Check an improvement idea before implementation without applying it."""
    file_list = [str(item).replace("\\", "/").strip() for item in (changed_files or []) if str(item).strip()]
    command_list = [str(item).strip() for item in (intended_commands or []) if str(item).strip()]
    risk = "low"
    findings: list[dict[str, str]] = []

    for file_name in file_list:
        lowered = file_name.lower()
        if any(hint.lower() in lowered or lowered.endswith(hint.lower()) for hint in PROTECTED_FILE_HINTS):
            risk = "high"
            findings.append({"level": "high", "item": file_name, "reason": "protected or regression-sensitive file"})
        elif lowered.endswith(".py"):
            findings.append({"level": "medium", "item": file_name, "reason": "Python source change requires py_compile and smoke tests"})
            if risk == "low":
                risk = "medium"

    for command in command_list:
        lowered = command.lower().replace("-", "_")
        if any(hint in lowered for hint in MUTATING_COMMAND_HINTS):
            risk = "high"
            findings.append({"level": "high", "item": command, "reason": "mutating or high-risk command should require explicit confirmation"})
        elif command.startswith("/"):
            findings.append({"level": "low", "item": command, "reason": "slash command should have a command routing or ToolRegistry smoke check"})

    lower_goal = (goal or "").lower()
    targeted_tests = list(VALIDATION_BASELINE)
    if "voice" in lower_goal or "wake" in lower_goal or "mic" in lower_goal:
        targeted_tests.append("python -m pytest -q tests_v55_3_122_voice_profile_comm_activity.py tests_v55_3_123_wake_handoff_build_loop.py")
    if "gui" in lower_goal or "webui" in lower_goal or "layout" in lower_goal:
        targeted_tests.append("python -m pytest -q tests_webui_planning_visibility.py tests_gui_layout_v55_3_18.py")
    if "scheduler" in lower_goal or "analytics" in lower_goal or "proposal" in lower_goal:
        targeted_tests.append("python -m pytest -q tests_improvement_features_v55_3_124.py")
    if "inspiration" in lower_goal or "handoff" in lower_goal or "context" in lower_goal:
        targeted_tests.append("python -m pytest -q tests_nova_inspiration_v55_3_125.py")

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "goal": (goal or "").strip(),
        "risk": risk,
        "changed_files": file_list,
        "intended_commands": command_list,
        "findings": findings,
        "required_behaviour": [
            "Preserve backup, rollback, command safety, and idle/autonomous approval gates.",
            "Keep all new workflow intelligence read-only unless a separate command explicitly mutates state.",
            "Add or update functional tests for every new command/tool alias.",
        ],
        "validation_plan": targeted_tests,
        "permission_note": "High-risk findings do not block the report, but they should force human review before mutation.",
    }


def build_nova_inspiration_radar(root: Path, tool_names: Iterable[str] | None = None, focus: str = "") -> dict[str, Any]:
    """Return a ranked read-only roadmap of inspiration-backed Nova upgrades."""
    tools = _normalise_tool_names(tool_names)
    snapshot = _root_snapshot(Path(root))
    focus_text = (focus or "").strip()
    ideas = [
        InspirationIdea(
            title="Prompt-aware tool context pack",
            source_pattern="short-term tool/context memory",
            value=92,
            risk="low",
            implemented_now="/tool-context-pack GOAL",
            why_it_helps="Stops Nova from stuffing every command into the model context and instead gives local models a small relevant tool set.",
            suggested_command="/tool-context-pack improve voice wake handoff without regression",
            validation=["tests_nova_inspiration_v55_3_125.py::test_tool_context_pack_prioritises_prompt_relevant_tools"],
        ),
        InspirationIdea(
            title="Deterministic handoff planner",
            source_pattern="multi-agent orchestration and handoff testing",
            value=89,
            risk="low",
            implemented_now="/handoff-plan GOAL",
            why_it_helps="Turns vague improvement goals into explicit router/planner/builder/verifier/reporter steps while still using one safe process.",
            suggested_command="/handoff-plan fix GUI layout and validate no regression",
            validation=["tests_nova_inspiration_v55_3_125.py::test_handoff_plan_contains_verifier_and_reporter"],
        ),
        InspirationIdea(
            title="Improvement preflight contract",
            source_pattern="guardrails, durable execution and human-in-the-loop checkpoints",
            value=87,
            risk="low",
            implemented_now="/improvement-preflight GOAL",
            why_it_helps="Before a patch, Nova can state risk, protected files, and exact tests so the build loop does not damage existing features.",
            suggested_command="/improvement-preflight add analytics widget => winlocalassistant/tools.py",
            validation=["tests_nova_inspiration_v55_3_125.py::test_improvement_preflight_flags_protected_files"],
        ),
        InspirationIdea(
            title="Inspiration radar ledger",
            source_pattern="repository-level context files and agent configuration artifacts",
            value=82,
            risk="low",
            implemented_now="/inspiration-radar FOCUS",
            why_it_helps="Keeps future improvement ideas tied to product patterns, local project signals, and known validation gates instead of random feature creep.",
            suggested_command="/inspiration-radar autonomous reliability",
            validation=["tests_nova_inspiration_v55_3_125.py::test_inspiration_radar_reports_implemented_commands"],
        ),
    ]

    available_commands = sorted(
        command for command in (
            "tool_context_pack",
            "handoff_plan",
            "improvement_preflight",
            "inspiration_radar",
            "analytics",
            "proposal_ledger_view",
            "regression_sweep",
        )
        if not tools or command in tools
    )
    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "focus": focus_text,
        "snapshot": snapshot,
        "available_inspired_commands": available_commands,
        "ideas": [idea.to_dict() for idea in sorted(ideas, key=lambda item: (-item.value, item.title))],
        "no_regression_policy": "All implemented ideas are read-only planning/diagnostic tools and do not alter current execution behaviour.",
    }


def render_tool_context_pack(payload: dict[str, Any]) -> str:
    lines = ["# Nova Tool Context Pack", "", f"Generated: `{payload.get('generated_at', '')}`"]
    if payload.get("prompt"):
        lines.append(f"Prompt: {payload.get('prompt')}")
    lines.extend(["", "## Selected tools"])
    for item in payload.get("selected_tools", []):
        reasons = "; ".join(str(reason) for reason in item.get("reasons", [])[:3])
        lines.append(f"- **{item.get('tool')}** — score {item.get('score')}: {reasons}")
    lines.extend([
        "",
        "## Context budget",
        f"- Selected: {len(payload.get('selected_tool_names', []))}/{payload.get('max_tools')}",
        f"- Hidden available tools: {payload.get('hidden_available_tool_count', 0)}",
        f"- Policy: {payload.get('policy', '')}",
    ])
    return "\n".join(lines)


def render_handoff_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Handoff Plan", "", f"Generated: `{payload.get('generated_at', '')}`"]
    if payload.get("prompt"):
        lines.append(f"Goal: {payload.get('prompt')}")
    lines.extend(["", "## Steps"])
    for idx, step in enumerate(payload.get("steps", []), 1):
        tools = ", ".join(step.get("tools", [])) or "none available"
        lines.extend([
            f"### {idx}. {step.get('name')}",
            f"- Responsibility: {step.get('responsibility')}",
            f"- Trigger: {step.get('trigger')}",
            f"- Tools: `{tools}`",
            f"- Exit check: {step.get('exit_check')}",
            "",
        ])
    lines.append(f"Policy: {payload.get('policy', '')}")
    return "\n".join(lines)


def render_improvement_preflight(payload: dict[str, Any]) -> str:
    lines = ["# Nova Improvement Preflight", "", f"Risk: **{payload.get('risk', 'unknown')}**"]
    if payload.get("goal"):
        lines.append(f"Goal: {payload.get('goal')}")
    lines.extend(["", "## Findings"])
    findings = payload.get("findings", [])
    if findings:
        for finding in findings:
            lines.append(f"- **{finding.get('level')}** `{finding.get('item')}` — {finding.get('reason')}")
    else:
        lines.append("- No high-risk files or mutating commands were supplied.")
    lines.extend(["", "## Required behaviour"])
    for item in payload.get("required_behaviour", []):
        lines.append(f"- {item}")
    lines.extend(["", "## Validation plan"])
    for command in payload.get("validation_plan", []):
        lines.append(f"- `{command}`")
    lines.extend(["", payload.get("permission_note", "")])
    return "\n".join(lines)


def render_inspiration_radar(payload: dict[str, Any]) -> str:
    lines = ["# Nova Inspiration Radar", "", f"Generated: `{payload.get('generated_at', '')}`"]
    if payload.get("focus"):
        lines.append(f"Focus: {payload.get('focus')}")
    snapshot = payload.get("snapshot", {})
    lines.extend([
        "",
        "## Local signals",
        f"- Root: `{snapshot.get('root', '')}`",
        f"- Python modules: {snapshot.get('module_count', 0)}",
        f"- Test files: {snapshot.get('test_count', 0)}",
        f"- Implemented inspired commands: {', '.join(payload.get('available_inspired_commands', []))}",
        "",
        "## Ranked ideas",
    ])
    for idea in payload.get("ideas", []):
        lines.extend([
            f"### {idea.get('title')}",
            f"- Pattern: {idea.get('source_pattern')}",
            f"- Value: {idea.get('value')}/100; Risk: {idea.get('risk')}",
            f"- Implemented now: `{idea.get('implemented_now')}`",
            f"- Why: {idea.get('why_it_helps')}",
            f"- Try: `{idea.get('suggested_command')}`",
            "",
        ])
    lines.append(payload.get("no_regression_policy", ""))
    return "\n".join(lines)
