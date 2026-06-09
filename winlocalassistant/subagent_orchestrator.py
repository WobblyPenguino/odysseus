from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class SubAgent:
    name: str
    role: str
    can_run_parallel: bool
    uses_llm: bool
    tools: list[str] = field(default_factory=list)
    validation: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


DEFAULT_SUBAGENTS = [
    SubAgent("router", "classify request, choose workflow and split work", True, False, ["pipeline_route", "request_intent"], ["route snapshot test"]),
    SubAgent("researcher", "gather docs/repo context and previous failures", True, False, ["repo_context_map", "doc_ingest", "activity_log"], ["source/citation check"]),
    SubAgent("builder", "make the smallest verified code/project change", False, True, ["ai_create_project", "ai_edit_project", "surgical_repair"], ["compile/test before promote"]),
    SubAgent("verifier", "run deterministic tests and user-scenario probes", True, False, ["auto_verify", "final_project_check", "regression_sweep"], ["must pass before completion"]),
    SubAgent("packager", "zip/release only after validators pass", True, False, ["release_package", "clean_release_package"], ["release hygiene check"]),
]


def build_subagent_plan(goal: str = "", *, slots: int = 3) -> dict[str, Any]:
    """Plan safe subagents without removing the local model lock.

    This is a contract for parallelisation: deterministic/read-only agents can
    run concurrently, but LLM/model-writing agents remain serialized unless a
    runtime adapter provides isolated workers.
    """
    slots = max(1, min(int(slots or 3), 6))
    agents = [a.to_dict() for a in DEFAULT_SUBAGENTS]
    waves: list[dict[str, Any]] = [
        {"wave": 1, "parallel": True, "agents": ["router", "researcher"], "why": "deterministic context gathering can run concurrently"},
        {"wave": 2, "parallel": False, "agents": ["builder"], "why": "LLM/code mutation stays serialized to avoid Ollama/request interference"},
        {"wave": 3, "parallel": True, "agents": ["verifier", "packager"], "why": "deterministic validation and packaging can overlap where files are stable"},
    ]
    return {
        "ok": True,
        "goal": goal or "improve Nova safely",
        "max_parallel_slots": slots,
        "model_lock_policy": "serialize LLM prompts per local runtime; allow non-LLM diagnostics in parallel",
        "agents": agents,
        "waves": waves,
        "acceptance": [
            "no subagent may bypass tool contracts or action watcher gates",
            "mutating subagent must produce backup/evidence/validation",
            "if a model call fails or crashes, verifier/researcher can continue but builder waits for recovery",
        ],
    }


def render_subagent_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Nova Safe Subagent Plan",
        "",
        f"Goal: {plan.get('goal','')}",
        f"Max deterministic parallel slots: {plan.get('max_parallel_slots')}",
        f"Model lock policy: {plan.get('model_lock_policy')}",
        "",
        "## Agents",
    ]
    for agent in plan.get("agents", []):
        tag = "parallel" if agent.get("can_run_parallel") else "serialized"
        llm = "LLM" if agent.get("uses_llm") else "no-LLM"
        lines.append(f"- **{agent.get('name')}** ({tag}, {llm}): {agent.get('role')}")
    lines += ["", "## Execution waves"]
    for wave in plan.get("waves", []):
        lines.append(f"- Wave {wave.get('wave')}: {', '.join(wave.get('agents', []))} — {wave.get('why')}")
    lines += ["", "## Acceptance"]
    lines.extend(f"- {x}" for x in plan.get("acceptance", []))
    return "\n".join(lines)
