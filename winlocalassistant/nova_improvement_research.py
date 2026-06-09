from __future__ import annotations

from pathlib import Path
from typing import Iterable

from .branding import PRODUCT_NAME

RESEARCH_BACKED_THEMES = [
    {
        "name": "Guarded tool execution",
        "why": "Local assistants gain power from file, shell and browser tools, so every mutating action should carry a risk label, approval state and validation receipt.",
        "signals": ("guardrail", "permission", "receipt", "approval", "scope_review"),
        "add": "Add a unified tool input/output guardrail ledger with per-tool risk, approval reason, execution result and rollback hint.",
        "validation": ("/nova-brand-audit", "/command-verify", "/release-gate"),
    },
    {
        "name": "Trace-first debugging",
        "why": "Agent runs are easier to debug when model calls, tool calls, guardrail decisions and validation steps are observable as a timeline.",
        "signals": ("trace", "timeline", "observability", "activity_log", "model_io"),
        "add": "Promote a single Nova trace timeline that correlates chat turns, tool calls, validation commands and generated artifacts.",
        "validation": ("/trace-observability", "/trace-last", "/nova-system-test quick"),
    },
    {
        "name": "Evaluation packs",
        "why": "A local assistant should keep small deterministic eval packs for common workflows so upgrades prove behavior, not just imports.",
        "signals": ("eval", "test", "contract", "regression", "acceptance"),
        "add": "Create named eval packs for coding, voice, project generation, research planning and release hygiene with pass/fail summaries. Implemented surface: /nova-eval-packs.",
        "validation": ("/nova-eval-packs run all", "/coding-acceptance-tests", "/feature-preservation-contract"),
    },
    {
        "name": "MCP-compatible context surfaces",
        "why": "Resources, prompts and tools are becoming a standard shape for agent integrations, so Nova should expose its local capabilities predictably.",
        "signals": ("mcp", "manifest", "tools", "resources", "prompts"),
        "add": "Expand the manifest to include resources and prompt templates, not only tool names, while keeping local execution allowlisted.",
        "validation": ("/mcp-export-manifest", "/tool-contract-audit", "/command-flow-verify"),
    },
    {
        "name": "Memory governance",
        "why": "Persistent local memory is useful only when the user can inspect, edit, delete and scope what the assistant remembers.",
        "signals": ("memory", "knowledge", "remember", "conversation", "datastore"),
        "add": "Add a memory control panel with source, age, scope, confidence and delete/export actions for every durable note.",
        "validation": ("/memory", "/db list", "/feature-continuity"),
    },
    {
        "name": "Voice reliability and privacy",
        "why": "Voice assistants need clear microphone state, local wake-word boundaries, interruption handling and visible privacy controls.",
        "signals": ("voice", "wake", "microphone", "speech", "audio"),
        "add": "Add a voice diagnostics page that records wake detection, selected mic, mute state and last command routing without storing raw audio.",
        "validation": ("/voice-pipeline-review", "/voice-device-status", "/startup-gate"),
    },
]


def _read_some(root: Path, names: Iterable[str]) -> str:
    chunks: list[str] = []
    for rel in names:
        path = root / rel
        if path.exists() and path.is_file():
            try:
                chunks.append(path.read_text(encoding="utf-8", errors="ignore")[:120_000].lower())
            except OSError:
                pass
    return "\n".join(chunks)


def build_nova_improvement_research(root: Path | str = ".", focus: str = "") -> dict:
    base = Path(root).resolve()
    corpus = _read_some(base, ["README.md", "winlocalassistant/core.py", "winlocalassistant/tools.py", "winlocalassistant/webui.py"])
    focus_low = (focus or "").lower()
    recommendations: list[dict] = []
    for theme in RESEARCH_BACKED_THEMES:
        hits = sorted({signal for signal in theme["signals"] if signal in corpus})
        focus_bonus = 12 if focus_low and (focus_low in theme["name"].lower() or any(focus_low in s for s in theme["signals"])) else 0
        gap_score = max(0, 45 - len(hits) * 6) + focus_bonus
        recommendations.append({
            "name": theme["name"],
            "why": theme["why"],
            "existing_signals": hits,
            "gap_score": gap_score,
            "recommended_addition": theme["add"],
            "validation": list(theme["validation"]),
        })
    recommendations.sort(key=lambda item: (-int(item["gap_score"]), item["name"]))
    return {
        "ok": True,
        "product": PRODUCT_NAME,
        "focus": focus or "general Nova functionality",
        "root": str(base),
        "recommendations": recommendations,
        "top_next": recommendations[:3],
    }


def render_nova_improvement_research(payload: dict) -> str:
    lines = [
        "# Nova Improvement Research Plan",
        "",
        f"Focus: **{payload.get('focus', '')}**",
        f"Root: `{payload.get('root', '')}`",
        "",
        "## Top implementation candidates",
    ]
    for item in payload.get("top_next", []):
        lines += [
            f"### {item.get('name')}",
            f"- Why: {item.get('why')}",
            f"- Current signals found: {', '.join(item.get('existing_signals') or ['none'])}",
            f"- Add: {item.get('recommended_addition')}",
            f"- Validate with: {', '.join(f'`{cmd}`' for cmd in item.get('validation', []))}",
            "",
        ]
    lines += ["## Full ranked list"]
    for item in payload.get("recommendations", []):
        lines.append(f"- **{item.get('name')}** — gap score {item.get('gap_score')}: {item.get('recommended_addition')}")
    return "\n".join(lines).rstrip()
