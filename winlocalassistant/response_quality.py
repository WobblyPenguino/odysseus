from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


RESEARCH_SOURCES = [
    {
        "name": "OpenAI prompt engineering guidance",
        "url": "https://help.openai.com/en/articles/6654000-best-practices-for-prompting",
        "finding": "Put clear instructions before context, separate context with delimiters, prefer specific constraints, and say what to do instead of only what not to do.",
    },
    {
        "name": "OpenAI reasoning best practices",
        "url": "https://platform.openai.com/docs/guides/reasoning-best-practices",
        "finding": "Use straightforward prompts with clear end goals, delimiters, and explicit constraints; avoid forcing chain-of-thought style prompts.",
    },
    {
        "name": "OpenAI structured outputs guidance",
        "url": "https://platform.openai.com/docs/guides/structured-outputs",
        "finding": "Use structured outputs or function calling for machine-readable subtasks instead of parsing free-form prose.",
    },
    {
        "name": "Ollama structured outputs",
        "url": "https://docs.ollama.com/capabilities/structured-outputs",
        "finding": "Local Ollama calls can use JSON/schema-style formats for reliable extraction and consistent response shapes.",
    },
    {
        "name": "ReAct paper",
        "url": "https://arxiv.org/abs/2210.03629",
        "finding": "Interleaving reasoning with actions helps agents update plans, handle exceptions, and gather external evidence.",
    },
    {
        "name": "Retrieval-Augmented Generation paper",
        "url": "https://arxiv.org/abs/2005.11401",
        "finding": "Retrieval plus generation improves factual specificity and allows knowledge to be updated outside model weights.",
    },
]


def response_contract_for_intents(intent_tags: list[str] | tuple[str, ...] | None = None) -> list[str]:
    tags = {str(t).lower() for t in (intent_tags or [])}
    rules = [
        "Start from the user's exact goal and answer that goal before adjacent ideas.",
        "Separate instructions, evidence, assumptions, and final answer; do not blend quoted/context text into instructions.",
        "Use concrete checks, commands, file paths, or dates when the answer depends on verification.",
        "Do not claim success, installation, network access, tests, or file edits unless tool output or provided evidence proves it.",
        "Prefer short, direct answers for simple chat; use sections only when they improve scanning.",
    ]
    if tags & {"code_debug", "project_build", "autonomous"}:
        rules.extend([
            "For build/debug work, state the observed failure, the smallest fix path, and the verification command.",
            "For machine-readable planning or repair, prefer JSON-shaped intermediate data and validate it before using it.",
        ])
    if tags & {"file_context", "math_science"}:
        rules.append("When using retrieved/file context, cite or identify the specific context item that supports the answer.")
    if tags & {"communication"}:
        rules.append("Match tone to the recipient and preserve the user's intent instead of over-polishing away meaning.")
    return rules


def build_response_quality_plan(goal: str = "", *, intent_tags: list[str] | None = None) -> dict[str, Any]:
    text = (goal or "").strip() or "improve Nova response quality and communication"
    low = text.lower()
    tags = list(intent_tags or [])
    if not tags:
        if any(w in low for w in ["code", "bug", "fix", "test", "validation", "install", "remote"]):
            tags.append("code_debug")
        if any(w in low for w in ["build", "app", "project", "feature", "function"]):
            tags.append("project_build")
        if any(w in low for w in ["communicate", "voice", "chat", "response", "reply", "explain"]):
            tags.append("communication")
        if any(w in low for w in ["research", "current", "latest", "source", "evidence"]):
            tags.append("file_context")
        if not tags:
            tags.append("general")
    actions = [
        {
            "name": "Context discipline",
            "impact": "higher factuality and fewer off-course replies",
            "implementation": "Keep a bounded context pack with labeled sections and explicit operating rules before the user prompt.",
        },
        {
            "name": "Response contract",
            "impact": "clearer, more trustworthy communication",
            "implementation": "Inject compact rules for evidence, assumptions, verification and concise tone into model calls.",
        },
        {
            "name": "Structured subtasks",
            "impact": "more reliable tool/project planning",
            "implementation": "Use JSON/schema-shaped intermediate plans for routing, extraction and repair before rendering user prose.",
        },
        {
            "name": "Evidence loop",
            "impact": "less hallucinated progress",
            "implementation": "Prefer observe-fix-verify loops; report only validated actions and keep dry-runs separate from live actions.",
        },
        {
            "name": "Retrieval before recall",
            "impact": "better answers on repo/current-state questions",
            "implementation": "Search local docs/code/activity first, then browse current primary sources only when the fact may have changed.",
        },
    ]
    return {
        "ok": True,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "goal": text,
        "intent_tags": tags,
        "response_contract": response_contract_for_intents(tags),
        "actions": actions,
        "research_sources": RESEARCH_SOURCES,
        "validation": [
            "Context preview contains response_quality_contract.",
            "ToolRegistry exposes response_quality_plan.",
            "Slash commands render the plan without calling a model.",
            "Targeted tests and Nova validation pass.",
        ],
    }


def render_response_quality_plan(plan: dict[str, Any]) -> str:
    lines = [
        "# Nova Response Quality Plan",
        "",
        f"Goal: {plan.get('goal', '')}",
        f"Intent tags: {', '.join(plan.get('intent_tags') or [])}",
        "",
        "## Response quality contract",
    ]
    lines += [f"- {rule}" for rule in plan.get("response_contract") or []]
    lines += ["", "## Improvement actions"]
    for action in plan.get("actions") or []:
        lines.append(f"- **{action.get('name')}**: {action.get('impact')}")
        lines.append(f"  Implementation: {action.get('implementation')}")
    lines += ["", "## Research basis"]
    for source in plan.get("research_sources") or []:
        lines.append(f"- {source.get('name')}: {source.get('finding')} ({source.get('url')})")
    lines += ["", "## Validation"]
    lines += [f"- {item}" for item in plan.get("validation") or []]
    return "\n".join(lines).strip() + "\n"


def write_response_quality_plan(root: str | Path, goal: str = "") -> tuple[Path, Path, dict[str, Any]]:
    base = Path(root)
    docs = base / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    plan = build_response_quality_plan(goal)
    json_path = docs / "NOVA_RESPONSE_QUALITY_PLAN_LATEST.json"
    md_path = docs / "NOVA_RESPONSE_QUALITY_PLAN_LATEST.md"
    atomic_write_json(json_path, plan, ensure_ascii=True)
    atomic_write_text(md_path, render_response_quality_plan(plan))
    return md_path, json_path, plan
