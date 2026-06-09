from __future__ import annotations

"""Read-only Nova agent upgrade helpers.

This module turns current agent/coding/local-model product patterns into safe,
additive Nova diagnostics. It does not execute shell commands, edit user
projects, download models, or mutate assistant state. ToolRegistry exposes these
helpers so Nova can plan better work before it changes anything.
"""

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable

from .nova_coding_capabilities import build_local_model_performance_plan, plan_coding_execution


@dataclass(frozen=True)
class UpgradeIdea:
    name: str
    inspiration: str
    why_it_helps: str
    safe_implementation: str
    verification: list[str] = field(default_factory=list)
    risk: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(path: Path, limit: int = 250_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _token_estimate(text: str) -> int:
    # Conservative local-model context estimate. It is intentionally simple and
    # deterministic so it remains useful without tokenizer dependencies.
    return max(1, math.ceil(len(text or "") / 4))


def _keyword_set(goal: str) -> set[str]:
    low = (goal or "").lower()
    words = set(re.findall(r"[a-z0-9_]{3,}", low))
    expansions = {
        "code": {"coding", "project", "runtime", "verify", "tests", "python", "java", "node"},
        "model": {"ollama", "local", "context", "router", "performance", "tokens"},
        "voice": {"wake", "audio", "microphone", "headset", "speech"},
        "agent": {"handoff", "tool", "planner", "trace", "context", "guard"},
        "test": {"pytest", "smoke", "regression", "validation", "quality"},
    }
    for key, extra in expansions.items():
        if key in words or key in low:
            words.update(extra)
    return words or {"nova", "assistant", "tool", "test"}


def build_agent_upgrade_radar(repo_root: Path | str = ".", focus: str = "") -> dict[str, Any]:
    """Return additive improvement ideas inspired by modern agent systems."""
    root = Path(repo_root)
    focus_low = (focus or "improve Nova safely").lower()
    files = {
        "core": _read(root / "winlocalassistant" / "core.py"),
        "tools": _read(root / "winlocalassistant" / "tools.py"),
        "coding": _read(root / "winlocalassistant" / "nova_coding_capabilities.py"),
        "context": _read(root / "winlocalassistant" / "model_context.py") + _read(root / "winlocalassistant" / "nova_operating_context.py"),
        "tests": "\n".join(p.name for p in root.glob("tests*.py")),
    }
    ideas = [
        UpgradeIdea(
            name="Context compaction before model calls",
            inspiration="Agent coding products treat context window usage as a scarce runtime resource.",
            why_it_helps="Nova can pass the smallest relevant file/tool pack to local models, reducing slow prompts and accidental instruction loss.",
            safe_implementation="Use /context-budget GOAL to choose include/exclude files before generation or repair.",
            verification=["Check selected files mention the requested topic", "Keep AGENTS.md/README only as compact summaries", "Do not remove existing model-context tools"],
        ),
        UpgradeIdea(
            name="Behavior-driven coding checks",
            inspiration="Coding-agent robustness research turns real failure reports into reusable behaviour tests.",
            why_it_helps="Nova can test whether generated apps actually satisfy the user's behaviour, not only whether syntax passes.",
            safe_implementation="Use /coding-behavior-tests GOAL to produce a runnable acceptance checklist for the selected runtime.",
            verification=["Syntax check", "Run command check", "At least one request-specific behaviour check", "No template/dodge mismatch"],
        ),
        UpgradeIdea(
            name="Local model runtime profiles",
            inspiration="Local inference stacks expose context, generation, keep-alive and quantization knobs that should vary by task.",
            why_it_helps="Nova avoids one-size-fits-all local-model settings by separating chat, code, long-context, vision and tooling prompts.",
            safe_implementation="Use /ollama-runtime-profile GOAL => HARDWARE to generate read-only Modelfile/options guidance.",
            verification=["Compare latency before/after", "Keep code temperature low", "Reduce context before increasing model size"],
        ),
        UpgradeIdea(
            name="Patch continuity audit",
            inspiration="Agent systems need durable state and regression checks so later patches do not silently downgrade earlier capabilities.",
            why_it_helps="Nova can confirm previous patch families still exist before claiming a new release is safe.",
            safe_implementation="Use /upgrade-regression-audit to check v55.3.124-v55.3.130 command/module/test continuity.",
            verification=["Tool commands still routed", "Modules still import", "Latest tests included in smoke/system slices"],
        ),
        UpgradeIdea(
            name="Handoff-ready work packets",
            inspiration="Multi-agent systems use specialist handoffs with filtered inputs instead of dumping all history into each worker.",
            why_it_helps="Nova can give planner/builder/verifier roles only what they need, improving local model reliability.",
            safe_implementation="Combine /handoff-plan with /context-budget and /coding-behavior-tests before mutating code.",
            verification=["Planner receives goal/constraints", "Builder receives files/entrypoint", "Verifier receives commands/acceptance checks"],
        ),
    ]
    if any(word in focus_low for word in ("voice", "wake", "headset", "audio")):
        ideas.insert(0, UpgradeIdea(
            name="Voice session trace packet",
            inspiration="Observability/tracing in agent systems makes intermittent failures easier to debug.",
            why_it_helps="Nova can collect wake/listen/speak state transitions without changing the fragile audio path.",
            safe_implementation="Keep this as a diagnostic/report command until Windows audio can be live-tested on the user's machine.",
            verification=["Confirm no microphone state mutation", "Confirm headset/TTS transitions are only logged", "Run voice audit command"],
        ))
    checks = [
        _check("coding_planner_present", "plan_coding_execution" in files["coding"], "Multi-runtime coding planner is present."),
        _check("inspiration_tools_present", "inspiration_radar" in files["tools"], "Existing inspiration commands remain wired."),
        _check("tests_reference_recent_patches", "tests_nova_coding_v55_3_126.py" in files["tests"], "Recent coding tests are present."),
    ]
    return {
        "focus": focus or "improve Nova safely",
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "ideas": [idea.to_dict() for idea in ideas],
        "recommended_sequence": [
            "/upgrade-regression-audit",
            "/context-budget GOAL",
            "/coding-behavior-tests GOAL",
            "/ollama-runtime-profile GOAL => HARDWARE",
            "run smoke/targeted tests before packaging",
        ],
    }


def render_agent_upgrade_radar(payload: dict[str, Any]) -> str:
    lines = ["# Nova Agent Upgrade Radar", "", f"Focus: {payload.get('focus','')}", f"Continuity baseline: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Inspired additive improvements"]
    for idea in payload.get("ideas", []) or []:
        lines.extend([
            f"### {idea.get('name','')}",
            f"- Inspiration: {idea.get('inspiration','')}",
            f"- Why it helps: {idea.get('why_it_helps','')}",
            f"- Safe implementation: {idea.get('safe_implementation','')}",
            f"- Risk: `{idea.get('risk','low')}`",
        ])
        checks = idea.get("verification") or []
        if checks:
            lines.append("- Verification:")
            lines.extend(f"  - {item}" for item in checks)
    lines.extend(["", "## Recommended sequence"])
    lines.extend(f"- {item}" for item in payload.get("recommended_sequence", []) or [])
    return "\n".join(lines) + "\n"


def build_context_budget_plan(repo_root: Path | str = ".", goal: str = "", max_files: int = 12) -> dict[str, Any]:
    """Choose a compact file pack for local model context without reading secrets."""
    root = Path(repo_root)
    keywords = _keyword_set(goal)
    candidate_paths: list[Path] = []
    for pattern in ("winlocalassistant/*.py", "tests*.py", "README.md", "CHANGELOG.md", "AGENTS.md"):
        candidate_paths.extend(root.glob(pattern))
    protected_markers = {".env", "secret", "token", "key", "password", "credential"}
    scored: list[dict[str, Any]] = []
    for path in sorted(set(candidate_paths)):
        rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.name
        low_rel = rel.lower()
        if any(marker in low_rel for marker in protected_markers):
            continue
        text = _read(path, limit=80_000)
        low_text = text.lower()
        keyword_hits = sorted(k for k in keywords if k in low_text or k in low_rel)
        role_bonus = 0
        if rel in {"AGENTS.md", "README.md", "CHANGELOG.md"}:
            role_bonus += 2
        if any(name in rel for name in ("nova_", "model_", "project_", "tools.py", "core.py")):
            role_bonus += 3
        score = len(keyword_hits) * 3 + role_bonus
        if score <= 0:
            continue
        scored.append({
            "path": rel,
            "score": score,
            "estimated_tokens": _token_estimate(text),
            "hits": keyword_hits[:12],
            "why": "matches goal keywords" if keyword_hits else "core context file",
        })
    scored.sort(key=lambda item: (-int(item["score"]), int(item["estimated_tokens"]), item["path"]))
    selected = scored[: max(1, int(max_files or 12))]
    selected_tokens = sum(int(item["estimated_tokens"]) for item in selected)
    excluded_count = max(0, len(scored) - len(selected))
    return {
        "goal": goal or "general Nova improvement",
        "keywords": sorted(keywords),
        "selected_files": selected,
        "excluded_candidate_count": excluded_count,
        "estimated_total_tokens": selected_tokens,
        "local_model_guidance": [
            "Send selected snippets, not the whole repository, to local models.",
            "Summarise README/CHANGELOG when token pressure is high.",
            "Keep tool contracts and verifier commands in context for coding tasks.",
            "Exclude secrets, runtime caches, release zips and generated reports.",
        ],
        "suggested_budget": "2048-4096 tokens for quick planner calls; 4096-8192 for code repair when hardware allows",
    }


def render_context_budget_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Context Budget Plan", "", f"Goal: {payload.get('goal','')}", f"Estimated selected context: **{payload.get('estimated_total_tokens',0)} tokens**", f"Suggested budget: {payload.get('suggested_budget','')}", "", "## Selected files"]
    for item in payload.get("selected_files", []) or []:
        hits = ", ".join(item.get("hits") or []) or "core context"
        lines.append(f"- `{item.get('path','')}` — score {item.get('score')} / ~{item.get('estimated_tokens')} tokens / {hits}")
    if not payload.get("selected_files"):
        lines.append("- No focused files found; use AGENTS.md, README.md and the direct target file only.")
    lines.extend(["", "## Guidance"])
    lines.extend(f"- {item}" for item in payload.get("local_model_guidance", []) or [])
    lines.append(f"- Excluded lower-priority candidate files: {payload.get('excluded_candidate_count', 0)}")
    return "\n".join(lines) + "\n"


def build_coding_behavior_tests(goal: str = "") -> dict[str, Any]:
    """Turn a coding prompt into request-specific behaviour checks."""
    plan = plan_coding_execution(goal or "build a small useful project")
    low = (goal or "").lower()
    behaviours = [
        {"name": "entrypoint_exists", "check": f"`{plan.get('main_file')}` exists and is not empty", "risk_caught": "model produced prose or wrong file type"},
        {"name": "syntax_or_compile", "check": f"run `{plan.get('verify_command')}`", "risk_caught": "invalid syntax before runtime testing"},
        {"name": "documented_run", "check": "README.md includes the exact run and verify commands", "risk_caught": "user cannot run the generated artifact"},
    ]
    if any(word in low for word in ("calculator", "calc", "math")):
        behaviours.append({"name": "calculator_behaviour", "check": "2+3 returns 5, clear/reset works, invalid input is handled", "risk_caught": "static calculator mockup"})
    elif any(word in low for word in ("todo", "task list", "checklist")):
        behaviours.append({"name": "todo_behaviour", "check": "can add, complete and delete a task without page/script errors", "risk_caught": "dead UI or missing persistence"})
    elif any(word in low for word in ("game", "pong", "snake", "platformer")):
        behaviours.append({"name": "game_behaviour", "check": "player/object moves, scoring or win/loss changes, restart works, instructions are visible", "risk_caught": "animated demo with no gameplay"})
    elif any(word in low for word in ("api", "server", "fastapi", "endpoint")):
        behaviours.append({"name": "api_behaviour", "check": "health route returns JSON and at least one requested route returns sample data", "risk_caught": "server starts but requested endpoints are missing"})
    elif any(word in low for word in ("file", "csv", "json", "rename", "convert")):
        behaviours.append({"name": "fixture_behaviour", "check": "run against temporary fixture files and confirm output files/content match expected values", "risk_caught": "script works only on assumed local paths"})
    else:
        behaviours.append({"name": "request_fit", "check": "output behaviour visibly matches the user's nouns/verbs, not a generic template", "risk_caught": "template substitution or dodge response"})
    repair_loop = [
        "Run syntax/compile verifier first.",
        "Run the smallest behaviour check that proves the requested function.",
        "If it fails, patch only the failing file/function and rerun the same check.",
        "Regenerate the whole project only after two targeted repairs fail.",
    ]
    return {"goal": goal, "plan": plan, "behaviours": behaviours, "repair_loop": repair_loop, "ok": True}


def render_coding_behavior_tests(payload: dict[str, Any]) -> str:
    plan = payload.get("plan", {})
    lines = ["# Nova Coding Behaviour Test Plan", "", f"Goal: {payload.get('goal') or 'unspecified'}", f"Runtime: **{plan.get('language','')}** / `{plan.get('artifact_type','')}`", "", "## Behaviour checks"]
    for item in payload.get("behaviours", []) or []:
        lines.append(f"- **{item.get('name','')}**: {item.get('check','')} _(catches: {item.get('risk_caught','')})_")
    lines.extend(["", "## Repair loop"])
    lines.extend(f"- {item}" for item in payload.get("repair_loop", []) or [])
    return "\n".join(lines) + "\n"


def build_ollama_runtime_profile(goal: str = "", hardware_hint: str = "") -> dict[str, Any]:
    """Create read-only Ollama profile guidance for a task/hardware pairing."""
    perf = build_local_model_performance_plan(goal, hardware_hint)
    profile = perf.get("profile", {})
    options = dict(profile.get("suggested_ollama_options", {}) or {})
    task = profile.get("task_kind", "chat")
    model_map = {
        "coding": "qwen3-coder:30b",
        "long_context": "qwen2.5:7b",
        "vision": "llama3.2-vision:11b",
        "tooling": "qwen2.5:3b",
        "chat": "gemma2:2b",
    }
    base_model = model_map.get(str(task), "gemma2:2b")
    # Keep generated settings conservative and visible. This is not executed.
    temp = options.get("temperature", 0.2)
    num_ctx = options.get("num_ctx", 4096)
    num_predict = options.get("num_predict", 700)
    modelfile = "\n".join([
        f"FROM {base_model}",
        f"PARAMETER temperature {temp}",
        f"PARAMETER num_ctx {num_ctx}",
        f"PARAMETER num_predict {num_predict}",
        "SYSTEM \"\"\"You are Nova's local specialist. Follow the provided plan, keep outputs concise, and return runnable code or focused diagnostics.\"\"\"",
    ]) + "\n"
    return {
        "goal": goal or "general Nova task",
        "hardware_hint": hardware_hint,
        "base_model": base_model,
        "modelfile": modelfile,
        "ollama_options": options,
        "benchmark_checklist": [
            "Record model name, num_ctx, temperature and keep_alive.",
            "Measure latency and tokens/sec on the same prompt before/after changes.",
            "Run the same deterministic verifier/behaviour test after changing profile.",
            "Prefer smaller context packs over larger context windows on low-VRAM machines.",
        ],
        "fallback_policy": [
            "If the coder model is too slow, ask a small model for a plan and use deterministic tools for verification.",
            "If a larger quantized model gives worse answers, return to the smaller passing profile.",
            "If VRAM pressure appears, reduce num_ctx before increasing temperature or model size.",
        ],
        "performance_plan": perf,
    }


def render_ollama_runtime_profile(payload: dict[str, Any]) -> str:
    lines = ["# Nova Ollama Runtime Profile", "", f"Goal: {payload.get('goal','')}", f"Suggested base model role/name: `{payload.get('base_model','')}`", "", "## Modelfile draft", "```Modelfile", str(payload.get("modelfile", "")).rstrip(), "```", "", "## Runtime options"]
    for key, value in (payload.get("ollama_options") or {}).items():
        lines.append(f"- `{key}`: `{value}`")
    lines.extend(["", "## Benchmark checklist"])
    lines.extend(f"- {item}" for item in payload.get("benchmark_checklist", []) or [])
    lines.extend(["", "## Fallback policy"])
    lines.extend(f"- {item}" for item in payload.get("fallback_policy", []) or [])
    return "\n".join(lines) + "\n"


def build_upgrade_regression_audit(repo_root: Path | str = ".") -> dict[str, Any]:
    """Check that recent additive patch families still exist and are routed."""
    root = Path(repo_root)
    init_text = _read(root / "winlocalassistant" / "__init__.py")
    core_text = _read(root / "winlocalassistant" / "core.py", limit=1_000_000)
    tools_text = _read(root / "winlocalassistant" / "tools.py", limit=1_000_000)
    webui_text = _read(root / "winlocalassistant" / "webui.py", limit=1_000_000)
    tests_smoke = _read(root / "tests_smoke.py")
    expected = [
        ("v55_3_124_analytics", "winlocalassistant/analytics_engine.py", ["analytics_dashboard", "proposal_ledger", "task_scheduler"], "tests_improvement_features_v55_3_124"),
        ("v55_3_125_inspiration", "winlocalassistant/nova_inspiration_engine.py", ["inspiration_radar", "tool_context_pack", "handoff_plan", "improvement_preflight"], "tests_nova_inspiration_v55_3_125"),
        ("v55_3_126_coding", "winlocalassistant/nova_coding_capabilities.py", ["coding_plan", "local_model_performance_plan", "coding_capability_audit"], "tests_nova_coding_v55_3_126"),
        ("v55_3_127_upgrade_lab", "winlocalassistant/nova_agent_upgrade_lab.py", ["agent_upgrade_radar", "context_budget", "coding_behavior_tests", "ollama_runtime_profile", "upgrade_regression_audit"], "tests_nova_agent_upgrade_v55_3_127"),
        ("v55_3_128_reliability_lab", "winlocalassistant/nova_reliability_lab.py", ["repo_context_map", "patch_impact_plan", "permission_scope_review", "local_model_benchmark_plan", "tool_contract_audit"], "tests_nova_reliability_v55_3_128"),
        ("v55_3_129_deep_research", "winlocalassistant/nova_deep_research_lab.py", ["agent_topology_plan", "trace_observability_plan", "local_stack_advisor", "verifier_ladder", "tool_namespace_plan", "voice_pipeline_review"], "tests_nova_deep_research_v55_3_129"),
        ("v55_3_130_route_resilience", "winlocalassistant/nova_route_resilience_lab.py", ["route_resilience_plan", "tool_health_map", "guardrail_memory_plan", "context_router_policy", "local_runtime_sentinel"], "tests_nova_route_resilience_v55_3_130"),
    ]
    checks: list[dict[str, Any]] = []
    route_text = core_text.replace("-", "_")
    route_aliases = {
        "analytics_dashboard": ["analytics", "analytics_dashboard"],
        "task_scheduler": ["list_tasks", "task_scheduler", "scheduler"],
        "proposal_ledger": ["proposal_ledger", "proposal_ledger_view"],
        "local_model_performance_plan": ["local_model_performance_plan", "model_performance_plan"],
        "coding_capability_audit": ["coding_capability_audit", "nova_coding_audit", "coding_audit"],
    }
    for name, module_rel, command_markers, test_marker in expected:
        checks.append(_check(f"{name}_module", (root / module_rel).exists(), f"{module_rel} exists"))
        for marker in command_markers:
            tool_ok = marker in tools_text
            aliases = route_aliases.get(marker, [marker])
            # Some older v55.3.124 utilities are registered as ToolRegistry tools and
            # exercised by smoke tests rather than exposed in the slash-command router.
            route_ok = any(alias in route_text for alias in aliases) or (name == "v55_3_124_analytics" and test_marker in tests_smoke)
            checks.append(_check(f"{name}_tool_{marker}", tool_ok and route_ok, f"{marker} appears in ToolRegistry and is routed or covered by smoke tests"))
        checks.append(_check(f"{name}_tests", (root / f"{test_marker}.py").exists() and test_marker in tests_smoke, f"{test_marker}.py exists and is called by smoke tests"))
    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    version = version_match.group(1) if version_match else ""
    try:
        version_tuple = tuple(int(part) for part in version.split("."))
    except Exception:
        version_tuple = (0, 0, 0)
    checks.extend([
        _check("version_current_visible", bool(version and version_tuple >= (55, 3, 129) and version in webui_text), f"Package and web UI show current v{version}."),
        _check("html_not_forced", "Do not force everything into HTML" in tools_text and "CODING EXECUTION PLAN" in tools_text, "Coding prompt still preserves multi-runtime planner."),
        _check("safe_no_auto_mutation", "approval" in tools_text.lower() and "self_improve" in tools_text.lower(), "Self-improvement paths still mention approval/guarded flow."),
    ])
    failed = [c for c in checks if not c["ok"]]
    return {
        "ok": not failed,
        "checks": checks,
        "failed": failed,
        "summary": "Recent patch continuity passed" if not failed else f"Recent patch continuity found {len(failed)} issue(s)",
        "recommended_validation": [
            "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py tests_nova_route_resilience_v55_3_130.py tests_nova_deep_research_v55_3_129.py tests_nova_agent_upgrade_v55_3_127.py tests_nova_reliability_v55_3_128.py",
            "python tests_nova_route_resilience_v55_3_130.py && python tests_nova_agent_upgrade_v55_3_127.py",
            "python tests_smoke.py",
            "python -m pytest -q tests_nova_route_resilience_v55_3_130.py tests_nova_deep_research_v55_3_129.py tests_nova_reliability_v55_3_128.py tests_nova_agent_upgrade_v55_3_127.py tests_nova_coding_v55_3_126.py tests_nova_inspiration_v55_3_125.py tests_improvement_features_v55_3_124.py",
        ],
    }


def render_upgrade_regression_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Upgrade Regression Audit", "", f"Overall: **{'PASS' if payload.get('ok') else 'REVIEW'}**", str(payload.get("summary") or ""), "", "## Checks"]
    for check in payload.get("checks", []) or []:
        mark = "✅" if check.get("ok") else "⚠️"
        lines.append(f"- {mark} **{check.get('name','')}** — {check.get('detail','')}")
    lines.extend(["", "## Recommended validation"])
    lines.extend(f"- `{cmd}`" for cmd in payload.get("recommended_validation", []) or [])
    return "\n".join(lines) + "\n"
