from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def build_local_model_optimization_plan(root: Path | str, goal: str = "") -> dict[str, Any]:
    root = Path(root)
    return {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "goal": goal or "maximize local model usefulness",
        "principles": [
            "Route each request to the smallest model that can reliably do the job.",
            "Keep prompts short, structured and role-specific; do not pass raw logs unless needed.",
            "Cache stable context sections by hash so repeated retries do not rebuild giant prompts.",
            "Use deterministic templates and surgical recipes after repeated validation failure.",
            "Treat execution results as ground truth and feed concise stderr/stdout back into repair prompts.",
        ],
        "ollama_runtime_tuning": [
            {"setting": "OLLAMA_KV_CACHE_TYPE=q8_0", "why": "Reduce KV cache memory for longer contexts with low quality impact."},
            {"setting": "Use q4_K_M or q5_K_M quantized models", "why": "Improve fit/speed on modest GPUs while keeping useful coding ability."},
            {"setting": "Separate chat/planner/code models", "why": "Avoid using a coder model for every simple chat or a tiny chat model for repairs."},
            {"setting": "Short retry contexts", "why": "Small local models follow compact failure contracts better than giant transcripts."},
        ],
        "prompt_cache_design": {
            "cache_key": "sha256(role + persona + stable Nova contract + project manifest)",
            "cacheable_sections": ["persona contract", "feature preservation contract", "tool catalog summary", "project type contract"],
            "non_cacheable_sections": ["latest failure", "changed file preview", "validation stderr", "user's current instruction"],
            "implementation_note": "Ollama does not expose portable KV-cache reuse through Nova directly, so Nova should cache compact prompt sections and avoid recomputing/scanning them on every retry.",
        },
        "model_routing": {
            "chat": "small general model, short context, persona-aware",
            "planner": "small/medium model, outputs mission contract only",
            "builder": "coder model, exact file JSON contract",
            "verifier": "deterministic checks first, model review second",
            "repairer": "surgical recipe + exact failed check + only relevant files",
            "toolsmith": "coder model with tool schema and self-test requirement",
        },
        "success_metrics": [
            "fewer candidate_refine repeats",
            "lower average prompt length during repair",
            "higher validation pass rate after first fallback",
            "more ACTION_RECEIPT.md files with real changed_files and validation evidence",
        ],
    }


def render_local_model_optimization_plan(payload: dict[str, Any]) -> str:
    lines = ["# Local Model Optimisation Plan", "", f"Goal: {payload.get('goal','')}", f"Root: `{payload.get('root','')}`", "", "## Principles"]
    for item in payload.get("principles", []):
        lines.append(f"- {item}")
    lines.append("\n## Ollama/runtime tuning")
    for item in payload.get("ollama_runtime_tuning", []):
        lines.append(f"- **{item.get('setting')}** — {item.get('why')}")
    lines.append("\n## Prompt cache design")
    cache = payload.get("prompt_cache_design", {})
    for key, val in cache.items():
        if isinstance(val, list):
            lines.append(f"- **{key}**: " + ", ".join(val))
        else:
            lines.append(f"- **{key}**: {val}")
    lines.append("\n## Model routing")
    for key, val in (payload.get("model_routing") or {}).items():
        lines.append(f"- **{key}**: {val}")
    lines.append("\n## Success metrics")
    for item in payload.get("success_metrics", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"


def build_iterative_agent_harness(root: Path | str, goal: str = "") -> dict[str, Any]:
    root = Path(root)
    steps = [
        {"step": "contract", "action": "create mission + project type acceptance contract", "stop_if": "goal is ambiguous or risky"},
        {"step": "baseline", "action": "choose deterministic template or existing project patch path", "stop_if": "target cannot be resolved"},
        {"step": "generate_or_patch", "action": "ask role-routed model for only the smallest needed change", "stop_if": "model returns unparseable output twice"},
        {"step": "execute", "action": "write in copied workspace or safe project scope", "stop_if": "path escapes workspace or deletes protected files"},
        {"step": "validate", "action": "run syntax + behaviour evidence + validation matrix where relevant", "stop_if": "same failure repeats"},
        {"step": "repair", "action": "use surgical recipe for named failure before regeneration", "stop_if": "no-progress score <= 0 twice"},
        {"step": "receipt", "action": "write changed files, commands, outputs and remaining risks", "stop_if": "changed_files is empty"},
    ]
    return {"ok": True, "root": str(root), "goal": goal or "iterative development", "steps": steps, "loop_policy": "maximum three model attempts, then deterministic fallback or honest stop", "integration": ["voice commands can trigger the harness", "idle can prepare patches at level 2", "autonomous can promote only with receipts at level 3/policy approval"]}


def render_iterative_agent_harness(payload: dict[str, Any]) -> str:
    lines = ["# Iterative Agent Harness", "", f"Goal: {payload.get('goal','')}", f"Loop policy: {payload.get('loop_policy','')}", "", "## Loop"]
    for item in payload.get("steps", []):
        lines.append(f"- **{item.get('step')}**: {item.get('action')} — stop if {item.get('stop_if')}")
    lines.append("\n## Nova integration")
    for item in payload.get("integration", []):
        lines.append(f"- {item}")
    return "\n".join(lines).strip() + "\n"
