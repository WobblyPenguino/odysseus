from __future__ import annotations

"""Read-only Nova route resilience helpers.

v55.3.130 turns recent agent research into deterministic diagnostics for Nova:
self-healing route graphs, context-aware guardrail memory, role-aware context
routing, tool-health maps, and local-runtime sentinel profiles.  Nothing in this
module executes shell commands, calls models, edits files, installs packages, or
changes live autonomy/voice/model behaviour.
"""

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class RouteNode:
    name: str
    role: str
    primary_next: list[str] = field(default_factory=list)
    fallback_next: list[str] = field(default_factory=list)
    health_signal: str = "span status and last ToolResult.ok"
    fail_policy: str = "escalate visibly; never silently skip"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class GuardrailRule:
    name: str
    inject_when: list[str]
    rule: str
    preserves_utility_by: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ContextRoute:
    role: str
    include: list[str]
    exclude: list[str]
    token_budget: int
    refresh_trigger: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class SentinelCheck:
    name: str
    command_or_signal: str
    threshold: str
    fallback: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SECRET_MARKERS = {".env", "secret", "token", "apikey", "api_key", "password", "credential", "private_key"}


def _read(path: Path, limit: int = 220_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _safe(path: Path) -> bool:
    low = path.as_posix().lower()
    return not any(marker in low for marker in _SECRET_MARKERS)


def _token_estimate(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


def _goal_words(goal: str) -> set[str]:
    words = {w for w in re.findall(r"[a-z0-9_]{3,}", (goal or "").lower())}
    expansions = {
        "agent": {"route", "handoff", "tool", "trace", "guardrail", "context"},
        "coding": {"code", "tests", "verify", "patch", "repo", "runtime"},
        "model": {"ollama", "llama", "num_ctx", "vram", "tokens", "benchmark"},
        "voice": {"wake", "stt", "tts", "audio", "mic", "device"},
        "autonomous": {"idle", "approval", "rollback", "receipt", "mutation"},
        "jarvis": {"voice", "assistant", "bridge", "sidecar", "daemon"},
    }
    low = (goal or "").lower()
    for key, extra in expansions.items():
        if key in low or key in words:
            words.update(extra)
    return words or {"nova", "assistant", "tool", "verify"}


def _repo_files(root: Path, goal: str, limit: int = 16) -> list[dict[str, Any]]:
    wanted = _goal_words(goal)
    patterns = [
        "AGENTS.md", "README.md", "CHANGELOG.md", "winlocalassistant/core.py", "winlocalassistant/tools.py",
        "winlocalassistant/nova_*.py", "winlocalassistant/model_*.py", "winlocalassistant/*voice*.py",
        "tests_nova_*.py", "tests_smoke.py", "tests_feature_continuity.py",
    ]
    items: list[dict[str, Any]] = []
    seen: set[str] = set()
    for pattern in patterns:
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or not _safe(path):
                continue
            try:
                rel = path.relative_to(root).as_posix()
            except Exception:
                rel = path.as_posix()
            if rel in seen:
                continue
            seen.add(rel)
            text = _read(path, 90_000)
            low_path = rel.lower()
            low_text = text.lower()
            score = 0
            for word in wanted:
                if word in low_path:
                    score += 4
                elif word in low_text:
                    score += 1
            if rel.endswith(("core.py", "tools.py")):
                score += 8
            if rel.startswith("winlocalassistant/nova_"):
                score += 5
            if rel.startswith("tests_nova_") or rel == "tests_smoke.py":
                score += 3
            items.append({"path": rel, "score": score, "estimated_tokens": _token_estimate(text[:50_000])})
    return sorted(items, key=lambda item: (-int(item["score"]), int(item["estimated_tokens"]), str(item["path"])))[:limit]


def _hardware_tier(hardware: str) -> str:
    low = (hardware or "").lower()
    match = re.search(r"(\d+)\s*(?:gb|gib)\s*(?:vram|gpu)?", low)
    gb = int(match.group(1)) if match else 0
    if gb and gb <= 6:
        return "small_gpu_or_cpu_spill_risk"
    if 7 <= gb <= 12:
        return "mid_gpu"
    if 13 <= gb <= 24:
        return "large_consumer_gpu"
    if gb >= 25:
        return "workstation"
    if "cpu" in low and "gpu" not in low:
        return "cpu_first"
    return "unknown"


def build_route_resilience_plan(repo_root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    """Build a deterministic fallback graph for Nova agent workflows."""
    root = Path(repo_root).expanduser().resolve()
    goal = (goal or "improve Nova without breaking existing behaviour").strip()
    nodes = [
        RouteNode("request_triage", "classify goal, risk and required runtime", ["context_router"], ["ask_for_scope_or_use_read_only_plan"]),
        RouteNode("context_router", "select role-specific files and tool namespaces", ["permission_gate"], ["compact_repo_map"]),
        RouteNode("permission_gate", "block destructive/broad/network/install/secret-adjacent changes until approved", ["builder_or_advisor"], ["read_only_advisory"]),
        RouteNode("builder_or_advisor", "produce the smallest useful patch or plan", ["verifier"], ["surgical_recipe", "human_review_packet"], fail_policy="return evidence and fallback route"),
        RouteNode("verifier", "run syntax, smoke and targeted regression evidence", ["reporter"], ["regression_matrix", "patch_impact_plan"], fail_policy="failed verification is visible evidence and demotes success claim"),
        RouteNode("reporter", "summarise pass/fail/untested surfaces and package links", [], ["audit_log"], health_signal="final evidence checklist"),
    ]
    edges = []
    for node in nodes:
        for target in node.primary_next:
            edges.append({"from": node.name, "to": target, "kind": "primary", "cost": 1})
        for target in node.fallback_next:
            edges.append({"from": node.name, "to": target, "kind": "fallback", "cost": 3})
    checks = [
        {"name": "fallbacks_present", "ok": all(n.fallback_next or not n.primary_next for n in nodes), "detail": "Every non-terminal route has at least one fallback."},
        {"name": "verifier_not_optional", "ok": any(n.name == "verifier" for n in nodes), "detail": "A separate verifier stage is required before success."},
        {"name": "silent_skip_forbidden", "ok": all("silently" in n.fail_policy or "evidence" in n.fail_policy or "visible" in n.fail_policy or not n.primary_next for n in nodes), "detail": "Failure policies require visible escalation or evidence."},
    ]
    return {
        "ok": all(c["ok"] for c in checks),
        "goal": goal,
        "source_inspiration": ["self-healing tool routing", "traceable fallback edges", "cost-aware deterministic recovery"],
        "nodes": [n.to_dict() for n in nodes],
        "edges": edges,
        "recovery_rule": "If a tool fails, mark the route unhealthy, choose the lowest-risk fallback, and report the reroute instead of silently skipping the step.",
        "relevant_context": _repo_files(root, goal, 10),
        "checks": checks,
    }


def render_route_resilience_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Route Resilience Plan", "", f"Goal: {payload.get('goal','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Route nodes"]
    for node in payload.get("nodes", []) or []:
        lines.append(f"- `{node.get('name')}`: {node.get('role')} | primary: {', '.join(node.get('primary_next') or []) or 'finish'} | fallback: {', '.join(node.get('fallback_next') or []) or 'none'}")
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    lines.append(f"\nRecovery rule: {payload.get('recovery_rule','')}")
    return "\n".join(lines).strip() + "\n"


def build_tool_health_map(repo_root: Path | str = ".", focus: str = "") -> dict[str, Any]:
    """Inspect command/tool registration continuity without invoking tools."""
    root = Path(repo_root).expanduser().resolve()
    tools_text = _read(root / "winlocalassistant" / "tools.py")
    core_text = _read(root / "winlocalassistant" / "core.py")
    webui_text = _read(root / "winlocalassistant" / "webui.py")
    registered = sorted(set(re.findall(r'"([a-zA-Z0-9_]+)"\s*:\s*self\.([a-zA-Z0-9_]+)', tools_text)))
    registered_names = {name for name, _method in registered}
    methods = set(re.findall(r"def\s+([a-zA-Z0-9_]+)\s*\(", tools_text))
    missing_methods = sorted([f"{name}->{method}" for name, method in registered if method not in methods])[:40]
    critical = {
        "route_resilience_plan": ["route_resilience_plan", "/route-resilience-plan"],
        "tool_health_map": ["tool_health_map", "/tool-health-map"],
        "guardrail_memory_plan": ["guardrail_memory_plan", "/guardrail-memory"],
        "context_router_policy": ["context_router_policy", "/context-router-policy"],
        "local_runtime_sentinel": ["local_runtime_sentinel", "/local-runtime-sentinel"],
        "deep_research_lab": ["agent_topology_plan", "/agent-topology"],
        "reliability_lab": ["tool_contract_audit", "/tool-contract-audit"],
        "coding_lab": ["coding_plan", "/coding-plan"],
    }
    surfaces = []
    for label, markers in critical.items():
        tool_marker, command_marker = markers
        surfaces.append({
            "surface": label,
            "tool_registered": tool_marker in registered_names or tool_marker in tools_text,
            "core_routed": command_marker in core_text,
            "webui_visible": command_marker in webui_text,
        })
    new_methods = {
        "route_resilience_plan_tool",
        "tool_health_map_tool",
        "guardrail_memory_plan_tool",
        "context_router_policy_tool",
        "local_runtime_sentinel_tool",
    }
    missing_new_methods = sorted(method for method in new_methods if method not in methods)
    checks = [
        {"name": "new_route_methods_exist", "ok": not missing_new_methods, "detail": f"missing={missing_new_methods}" if missing_new_methods else "All v55.3.130 route-resilience wrappers have definitions."},
        {"name": "critical_surfaces_routed", "ok": all(s["tool_registered"] and s["core_routed"] for s in surfaces[:5]), "detail": "New route-resilience commands have tool and core markers."},
        {"name": "tool_surface_large_enough_for_namespacing", "ok": len(registered_names) >= 60, "detail": f"registered tool names parsed: {len(registered_names)}"},
    ]
    return {
        "ok": all(c["ok"] for c in checks),
        "focus": focus or "Nova route health and command continuity",
        "registered_tool_count": len(registered_names),
        "legacy_missing_registered_methods_preview": missing_methods[:20],
        "critical_surfaces": surfaces,
        "checks": checks,
    }


def render_tool_health_map(payload: dict[str, Any]) -> str:
    lines = ["# Nova Tool Health Map", "", f"Focus: {payload.get('focus','')}", f"Registered tool names parsed: `{payload.get('registered_tool_count',0)}`", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Critical surfaces"]
    for s in payload.get("critical_surfaces", []) or []:
        lines.append(f"- `{s.get('surface')}`: tool={'yes' if s.get('tool_registered') else 'no'}, core={'yes' if s.get('core_routed') else 'no'}, webui={'yes' if s.get('webui_visible') else 'no'}")
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    return "\n".join(lines).strip() + "\n"


def build_guardrail_memory_plan(goal: str = "", risk_note: str = "") -> dict[str, Any]:
    """Create context-aware, utility-preserving guardrail memory rules."""
    goal = (goal or "improve Nova safely").strip()
    risk_note = (risk_note or "avoid breaking existing behaviour while allowing useful benign tasks").strip()
    rules = [
        GuardrailRule("scope_boundary", ["broad patch", "multiple files", "autonomous edit"], "Prefer read-only plan or smallest patch; require explicit evidence for each touched surface.", "allows narrow local edits with tests"),
        GuardrailRule("destructive_action_gate", ["delete", "overwrite", "shell", "install", "network"], "Require approval/backup/rollback before state-changing actions.", "does not block read-only diagnostics or local syntax checks"),
        GuardrailRule("secret_and_path_redaction", ["logs", "trace", "model prompt", "report"], "Redact secret-like values and avoid dumping unnecessary absolute local paths.", "keeps non-secret filenames and error summaries visible"),
        GuardrailRule("voice_device_caution", ["wake word", "microphone", "headset", "tts", "stt"], "Review pipeline/device impacts before changing live audio state.", "permits advisory voice diagnostics and receipt inspection"),
        GuardrailRule("local_model_context_budget", ["large repo", "long chat", "big context", "slow model"], "Use compact context routes before raising num_ctx.", "preserves quality by selecting relevant files rather than shrinking blindly"),
    ]
    checks = [
        {"name": "context_aware_rules", "ok": all(r.inject_when for r in rules), "detail": "Each rule has injection triggers."},
        {"name": "utility_preservation", "ok": all(r.preserves_utility_by for r in rules), "detail": "Rules include benign-use preservation notes."},
        {"name": "voice_and_model_risks_covered", "ok": any("voice" in r.name for r in rules) and any("model" in r.name for r in rules), "detail": "Voice and local-model risks have dedicated rules."},
    ]
    return {"ok": all(c["ok"] for c in checks), "goal": goal, "risk_note": risk_note, "rules": [r.to_dict() for r in rules], "injection_policy": "Inject only the rules whose triggers match the current role/task; do not dump every rule into every prompt.", "checks": checks}


def render_guardrail_memory_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Guardrail Memory Plan", "", f"Goal: {payload.get('goal','')}", f"Risk note: {payload.get('risk_note','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Context-aware rules"]
    for r in payload.get("rules", []) or []:
        lines.append(f"- `{r.get('name')}` inject when {', '.join(r.get('inject_when') or [])}: {r.get('rule')} Utility: {r.get('preserves_utility_by')}")
    lines.append(f"\nInjection policy: {payload.get('injection_policy','')}")
    return "\n".join(lines).strip() + "\n"


def build_context_router_policy(repo_root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    """Plan role-aware context routing under a strict token budget."""
    root = Path(repo_root).expanduser().resolve()
    goal = (goal or "route context for Nova agents efficiently").strip()
    files = _repo_files(root, goal, 12)
    # Keep the advisory context map compact enough for local-model use by
    # trimming lowest-priority files when unusually large modules dominate.
    while len(files) > 6 and sum(int(f.get("estimated_tokens", 0)) for f in files) > 62000:
        files.pop()
    routes = [
        ContextRoute("triage", ["command names", "goal", "risk words", "recent failure summary"], ["full file bodies", "logs over 2KB"], 1200, "new command or risk class changes"),
        ContextRoute("builder", ["target files", "nearby tests", "AGENTS.md constraints", "one recent similar module"], ["irrelevant docs", "old reports", "secret-like files"], 6000, "target file set changes"),
        ContextRoute("verifier", ["changed file list", "expected behaviours", "test commands", "error tails"], ["model brainstorming", "private scratchpad"], 3000, "test failure or changed runtime"),
        ContextRoute("reporter", ["diff summary", "validation evidence", "known limitations", "artifact paths"], ["full trace payloads", "raw secrets"], 1600, "final answer or handoff"),
    ]
    total_budget = sum(route.token_budget for route in routes)
    file_tokens = sum(int(f.get("estimated_tokens", 0)) for f in files)
    checks = [
        {"name": "bounded_role_budget", "ok": total_budget <= 14000, "detail": f"role budget={total_budget} tokens"},
        {"name": "repo_context_compacted", "ok": len(files) <= 12 and file_tokens <= 65000, "detail": f"files={len(files)}, estimated file tokens={file_tokens}"},
        {"name": "verifier_has_distinct_context", "ok": any(r.role == "verifier" and "test commands" in r.include for r in routes), "detail": "Verifier receives evidence context, not builder scratchpad."},
    ]
    return {"ok": all(c["ok"] for c in checks), "goal": goal, "selected_files": files, "routes": [r.to_dict() for r in routes], "total_role_budget": total_budget, "checks": checks}


def render_context_router_policy(payload: dict[str, Any]) -> str:
    lines = ["# Nova Context Router Policy", "", f"Goal: {payload.get('goal','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", f"Role budget: `{payload.get('total_role_budget',0)}` tokens", "", "## Role routes"]
    for r in payload.get("routes", []) or []:
        lines.append(f"- `{r.get('role')}` budget {r.get('token_budget')}: include {', '.join(r.get('include') or [])}; exclude {', '.join(r.get('exclude') or [])}")
    lines.extend(["", "## Selected repo files"])
    for f in payload.get("selected_files", [])[:8]:
        lines.append(f"- `{f.get('path')}` score={f.get('score')} est_tokens={f.get('estimated_tokens')}")
    return "\n".join(lines).strip() + "\n"


def build_local_runtime_sentinel(goal: str = "", hardware: str = "") -> dict[str, Any]:
    """Draft observable local-model health checks and fallback profiles."""
    goal = (goal or "general Nova local model use").strip()
    tier = _hardware_tier(hardware)
    if tier in {"small_gpu_or_cpu_spill_risk", "cpu_first"}:
        num_ctx = 4096
        primary = "small coder/chat model with compact repo context"
        fallback = "reduce context to 2k-4k and route only selected files"
    elif tier == "mid_gpu":
        num_ctx = 8192
        primary = "7B-14B model with focused context"
        fallback = "drop to 4k or smaller model if CPU/GPU split degrades"
    else:
        num_ctx = 16384 if tier == "unknown" else 32768
        primary = "larger coding/reasoning model when benchmark evidence supports it"
        fallback = "use task-specific small profile for trivial chat or quick code fixes"
    checks = [
        SentinelCheck("gpu_residency", "ollama ps", "model should be mostly/fully on GPU when GPU is expected", "lower num_ctx or smaller quant/model"),
        SentinelCheck("latency_budget", "tokens/sec and first-token latency from model response metadata", "slowdown > 2x from baseline triggers reroute", fallback),
        SentinelCheck("context_pressure", "prompt token estimate + num_ctx profile", f"default num_ctx <= {num_ctx} for this tier", "compact context with /context-router-policy"),
        SentinelCheck("quality_canary", "same deterministic prompt across profiles", "answer must preserve required facts and command names", "keep old profile and mark new one experimental"),
    ]
    return {"ok": True, "goal": goal, "hardware": hardware or "unspecified", "hardware_tier": tier, "recommended_num_ctx": num_ctx, "primary_profile": primary, "sentinel_checks": [c.to_dict() for c in checks], "modelfile_notes": [f"PARAMETER num_ctx {num_ctx}", "PARAMETER temperature 0.2 for planner/verifier steps", "Use higher num_ctx only after checking `ollama ps` and latency."], "fallback_policy": "Never globally switch model profiles without trace evidence and an easy rollback path."}


def render_local_runtime_sentinel(payload: dict[str, Any]) -> str:
    lines = ["# Nova Local Runtime Sentinel", "", f"Goal: {payload.get('goal','')}", f"Hardware tier: `{payload.get('hardware_tier')}`", f"Recommended num_ctx: `{payload.get('recommended_num_ctx')}`", f"Primary profile: {payload.get('primary_profile')}", "", "## Sentinel checks"]
    for c in payload.get("sentinel_checks", []) or []:
        lines.append(f"- `{c.get('name')}` via `{c.get('command_or_signal')}`: threshold {c.get('threshold')}; fallback {c.get('fallback')}")
    lines.extend(["", "## Modelfile notes"])
    lines.extend(f"- `{note}`" for note in payload.get("modelfile_notes", []) or [])
    lines.append(f"\nFallback policy: {payload.get('fallback_policy','')}")
    return "\n".join(lines).strip() + "\n"
