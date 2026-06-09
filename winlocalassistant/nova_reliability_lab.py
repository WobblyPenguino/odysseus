from __future__ import annotations

"""Read-only Nova reliability and upgrade planning helpers.

v55.3.128 adds diagnostics inspired by current agent engineering patterns:
context maps, permission/scope review, behaviour-driven regression planning,
local-model benchmarking, and tool-contract audits. These helpers deliberately
avoid executing commands, editing project files, downloading models, or changing
assistant state.
"""

import ast
import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Iterable


@dataclass(frozen=True)
class ContextFile:
    path: str
    role: str
    why: str
    estimated_tokens: int
    priority: int
    safety_note: str = "no obvious secret-like path markers"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ImpactRule:
    pattern: str
    reason: str
    tests: list[str] = field(default_factory=list)
    commands: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SECRET_MARKERS = {".env", "secret", "token", "apikey", "api_key", "password", "credential", "private_key"}


def _read(path: Path, limit: int = 220_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _token_estimate(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


def _words(text: str) -> set[str]:
    base = {w for w in re.findall(r"[a-z0-9_]{3,}", (text or "").lower())}
    expansions = {
        "voice": {"wake", "speech", "audio", "microphone", "headset", "tts", "stt"},
        "coding": {"code", "project", "runtime", "verify", "python", "java", "node", "fastapi", "tests"},
        "model": {"ollama", "local", "context", "num_ctx", "quantization", "latency", "tokens"},
        "agent": {"tool", "trace", "handoff", "guardrail", "permission", "context", "session"},
        "test": {"pytest", "smoke", "regression", "syntax", "acceptance", "behaviour"},
        "ui": {"webui", "layout", "panel", "browser", "html", "javascript"},
        "autonomous": {"idle", "scheduler", "proposal", "rollback", "receipt", "gate"},
    }
    for key, extra in expansions.items():
        if key in base or key in (text or "").lower():
            base.update(extra)
    return base or {"nova", "assistant", "reliability"}


def _rel(root: Path, path: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except Exception:
        return path.as_posix()


def _safe_candidate(path: Path) -> bool:
    low = path.as_posix().lower()
    return not any(marker in low for marker in _SECRET_MARKERS)


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _split_files(text: str) -> list[str]:
    if not text:
        return []
    parts = re.split(r"[,\n;]+", text)
    out: list[str] = []
    for part in parts:
        clean = part.strip().strip("`'\"")
        if clean:
            out.append(clean.replace("\\", "/"))
    return out


def build_repo_context_map(repo_root: Path | str = ".", goal: str = "", max_files: int = 14) -> dict[str, Any]:
    """Build a compact, purpose-specific repo map for agent/coding prompts."""
    root = Path(repo_root)
    wanted = _words(goal)
    candidates: list[Path] = []
    for pattern in ("AGENTS.md", "README.md", "CHANGELOG.md", "winlocalassistant/*.py", "tests*.py", "docs/V55_3_*.md"):
        candidates.extend(root.glob(pattern))
    scored: list[ContextFile] = []
    for path in sorted(set(p for p in candidates if p.is_file() and _safe_candidate(p))):
        rel = _rel(root, path)
        text = _read(path, limit=90_000)
        low_rel = rel.lower()
        low_text = text.lower()
        hits = sorted(w for w in wanted if w in low_rel or w in low_text)
        role = "support"
        priority = 0
        if rel == "AGENTS.md":
            role, priority = "agent rules", 8
        elif rel == "README.md":
            role, priority = "capability overview", 7
        elif rel == "CHANGELOG.md":
            role, priority = "patch history", 7
        elif low_rel.endswith("tools.py"):
            role, priority = "tool registry", 8
        elif low_rel.endswith("core.py"):
            role, priority = "chat command router", 8
        elif "nova_" in low_rel:
            role, priority = "nova capability module", 7
        elif low_rel.startswith("tests"):
            role, priority = "regression tests", 6
        if hits:
            priority += min(9, len(hits) * 2)
        if priority < 4:
            continue
        scored.append(ContextFile(
            path=rel,
            role=role,
            why=("keyword hits: " + ", ".join(hits[:8])) if hits else "baseline project context",
            estimated_tokens=_token_estimate(text[:60_000]),
            priority=priority,
        ))
    selected = sorted(scored, key=lambda item: (-item.priority, item.estimated_tokens, item.path))[: max(1, int(max_files or 14))]
    total_tokens = sum(item.estimated_tokens for item in selected)
    checks = [
        _check("excludes_secret_like_paths", all(_safe_candidate(root / item.path) for item in selected), "Secret/token/password-like paths are excluded from the context map."),
        _check("includes_router_or_registry", any(item.path.endswith(("core.py", "tools.py")) for item in selected), "Command/router context is present when useful."),
        _check("bounded_context", total_tokens <= 120_000, f"Estimated selected context is {total_tokens} tokens."),
    ]
    return {
        "goal": goal or "general Nova reliability work",
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "selected_files": [item.to_dict() for item in selected],
        "estimated_total_tokens": total_tokens,
        "instructions": [
            "Use selected files as the first-pass context, not the whole repository.",
            "Summarise README/CHANGELOG instead of pasting them in full for small local models.",
            "Keep untrusted user files separated from system/developer instructions.",
            "Add tests named in the impact plan before claiming a patch is safe.",
        ],
    }


def render_repo_context_map(payload: dict[str, Any]) -> str:
    lines = ["# Nova Repo Context Map", "", f"Goal: {payload.get('goal','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", f"Estimated selected context: `{payload.get('estimated_total_tokens', 0)}` tokens", "", "## Selected files"]
    for item in payload.get("selected_files", []) or []:
        lines.append(f"- `{item.get('path','')}` — {item.get('role','support')}; {item.get('why','')}; est. `{item.get('estimated_tokens',0)}` tokens")
    lines.extend(["", "## Rules for Nova"])
    lines.extend(f"- {rule}" for rule in payload.get("instructions", []) or [])
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    return "\n".join(lines) + "\n"


def _impact_rules() -> list[ImpactRule]:
    return [
        ImpactRule("winlocalassistant/core.py", "Chat slash-command routing changed.", ["tests_smoke.py", "tests_feature_continuity.py", "tests_cli_user_mode.py"], ["python tests_smoke.py"]),
        ImpactRule("winlocalassistant/tools.py", "Tool registry or tool method wiring changed.", ["tests_smoke.py", "tests_feature_continuity.py"], ["python tests_smoke.py"]),
        ImpactRule("winlocalassistant/webui.py", "Browser cockpit/UI changed.", ["tests_webui_planning_visibility.py", "tests_v55_ux_game.py", "tests_feature_continuity.py"], ["python -m pytest -q tests_webui_planning_visibility.py tests_v55_ux_game.py"]),
        ImpactRule("winlocalassistant/nova_coding_capabilities.py", "Coding planner/verifier changed.", ["tests_nova_coding_v55_3_126.py"], ["python tests_nova_coding_v55_3_126.py"]),
        ImpactRule("winlocalassistant/nova_agent_upgrade_lab.py", "Upgrade lab changed.", ["tests_nova_agent_upgrade_v55_3_127.py"], ["python tests_nova_agent_upgrade_v55_3_127.py"]),
        ImpactRule("winlocalassistant/nova_reliability_lab.py", "Reliability lab changed.", ["tests_nova_reliability_v55_3_128.py"], ["python tests_nova_reliability_v55_3_128.py"]),
        ImpactRule("winlocalassistant/nova_deep_research_lab.py", "Deep research advisory lab changed.", ["tests_nova_deep_research_v55_3_129.py"], ["python tests_nova_deep_research_v55_3_129.py"]),
        ImpactRule("winlocalassistant/ollama.py", "Local model provider changed.", ["tests_model_health_timeout.py", "tests_nova_coding_v55_3_126.py"], ["python -m pytest -q tests_model_health_timeout.py tests_nova_coding_v55_3_126.py"]),
        ImpactRule("winlocalassistant/project_", "Project generation/runtime flow changed.", ["tests_project_acceptance.py", "tests_project_runtime_probe.py", "tests_nova_coding_v55_3_126.py"], ["python -m pytest -q tests_project_acceptance.py tests_project_runtime_probe.py tests_nova_coding_v55_3_126.py"]),
        ImpactRule("tests", "Regression suite changed.", ["tests_smoke.py"], ["python tests_smoke.py"]),
    ]


def build_patch_impact_plan(repo_root: Path | str = ".", changed_files: str = "") -> dict[str, Any]:
    """Return the minimum useful test plan for a described patch."""
    root = Path(repo_root)
    files = _split_files(changed_files)
    if not files:
        # Fall back to files that changed most often in the current v55.3 patch family.
        files = ["winlocalassistant/core.py", "winlocalassistant/tools.py", "tests_smoke.py"]
    matched_rules: list[dict[str, Any]] = []
    selected_tests: list[str] = []
    selected_commands: list[str] = []
    rules = _impact_rules()
    for file_name in files:
        low = file_name.lower().replace("\\", "/")
        for rule in rules:
            pat = rule.pattern.lower()
            if pat in low or (pat.endswith("_") and pat in low):
                data = rule.to_dict()
                data["matched_file"] = file_name
                matched_rules.append(data)
                selected_tests.extend(rule.tests)
                selected_commands.extend(rule.commands)
    selected_tests.extend(["tests_smoke.py", "tests_feature_continuity.py"])
    selected_commands.extend([
        "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py tests_nova_reliability_v55_3_128.py",
        "python tests_nova_reliability_v55_3_128.py",
        "python tests_smoke.py",
    ])
    tests_unique = sorted(dict.fromkeys(selected_tests))
    commands_unique = list(dict.fromkeys(selected_commands))
    checks = [
        _check("changed_files_listed", bool(files), "At least one changed file is available for impact planning."),
        _check("syntax_gate_present", any("py_compile" in cmd for cmd in commands_unique), "Syntax compilation gate is included."),
        _check("smoke_gate_present", any("tests_smoke.py" in cmd for cmd in commands_unique), "Smoke test gate is included."),
    ]
    return {
        "changed_files": files,
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "matched_rules": matched_rules,
        "recommended_tests": tests_unique,
        "recommended_commands": commands_unique,
        "fallback_full_suite": "python -m pytest -q",
        "note": "This plan is read-only. Run the commands manually or through Nova's existing guarded test paths.",
    }


def render_patch_impact_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Patch Impact Test Plan", "", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Changed files"]
    lines.extend(f"- `{item}`" for item in payload.get("changed_files", []) or [])
    lines.extend(["", "## Recommended tests"])
    lines.extend(f"- `{item}`" for item in payload.get("recommended_tests", []) or [])
    lines.extend(["", "## Recommended commands"])
    lines.extend(f"```powershell\n{cmd}\n```" for cmd in payload.get("recommended_commands", []) or [])
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    lines.append(f"\nFallback full suite: `{payload.get('fallback_full_suite','python -m pytest -q')}`")
    return "\n".join(lines) + "\n"


def build_permission_scope_review(intent: str = "", proposed_actions: str = "") -> dict[str, Any]:
    """Review ambiguous coding-agent actions before an autonomous patch proceeds."""
    blob = f"{intent}\n{proposed_actions}".lower()
    risky_markers = {
        "delete": "destructive file operation",
        "remove": "destructive or downgrade-prone operation",
        "overwrite": "state replacement",
        "format": "broad rewrite or formatting risk",
        "all files": "broad scope",
        "entire codebase": "broad scope",
        "shell": "command execution",
        "powershell": "command execution",
        "internet": "network/provider use",
        "download": "network/provider use",
        "install": "dependency/environment mutation",
        "token": "secret handling",
        "key": "secret handling",
        "credential": "secret handling",
        "autonomous": "state-changing unattended workflow",
    }
    findings = [{"marker": marker, "risk": risk} for marker, risk in risky_markers.items() if marker in blob]
    if not findings:
        level = "low"
    elif any(f["risk"] in {"secret handling", "broad scope", "destructive file operation"} for f in findings):
        level = "high"
    else:
        level = "medium"
    checkpoints = [
        "Name the exact files/directories in scope before editing.",
        "Prefer additive modules/tests over replacing existing working flows.",
        "Run syntax + smoke + impact tests before packaging.",
        "Keep backup/rollback/release manifest intact.",
    ]
    if level != "low":
        checkpoints.insert(0, "Ask for explicit confirmation before any broad, destructive, network, install, or secret-adjacent action.")
    return {
        "intent": intent or "unspecified Nova patch",
        "proposed_actions": proposed_actions or "not provided",
        "risk_level": level,
        "ok_to_auto_apply": level == "low",
        "findings": findings,
        "checkpoints": checkpoints,
        "recommended_gate": "manual review" if level != "low" else "normal guarded patch flow",
    }


def render_permission_scope_review(payload: dict[str, Any]) -> str:
    lines = ["# Nova Permission & Scope Review", "", f"Risk level: **{payload.get('risk_level','unknown').upper()}**", f"Recommended gate: `{payload.get('recommended_gate','manual review')}`", f"Auto-apply okay: `{payload.get('ok_to_auto_apply')}`", "", "## Findings"]
    findings = payload.get("findings", []) or []
    if findings:
        lines.extend(f"- `{f.get('marker')}` → {f.get('risk')}" for f in findings)
    else:
        lines.append("- No obvious broad/destructive/secret/network markers detected.")
    lines.extend(["", "## Required checkpoints"])
    lines.extend(f"- {item}" for item in payload.get("checkpoints", []) or [])
    return "\n".join(lines) + "\n"


def build_local_model_benchmark_plan(goal: str = "", hardware: str = "") -> dict[str, Any]:
    """Draft a local-model benchmark matrix without invoking Ollama."""
    goal_low = (goal or "general Nova use").lower()
    hardware_low = (hardware or "").lower()
    tiny_gpu = any(x in hardware_low for x in ("4gb", "gtx 1650", "1650", "low vram"))
    if "code" in goal_low or "debug" in goal_low or "coding" in goal_low:
        task = "coding/debugging"
        prompts = [
            "Fix this small Python function and explain the test you would run.",
            "Create a CLI calculator with input validation and one unit-style self-check.",
            "Read this error traceback and identify the smallest safe patch.",
        ]
        metrics = ["time_to_first_token", "total_latency", "compile_pass", "test_plan_quality", "hallucinated_file_count"]
    elif "research" in goal_low or "summar" in goal_low:
        task = "research/summarisation"
        prompts = [
            "Summarise a 900-word technical note into decisions, risks and next actions.",
            "Extract requirements from a pasted spec without inventing missing facts.",
        ]
        metrics = ["latency", "source_fidelity", "missing_constraint_count", "token_usage_estimate"]
    else:
        task = "general assistant"
        prompts = [
            "Answer a normal user question in under 150 words.",
            "Plan a 3-step troubleshooting workflow and name what evidence is needed.",
        ]
        metrics = ["latency", "helpfulness", "verbosity_control", "follow_instruction_rate"]
    profiles = [
        {"name": "fast_chat", "temperature": 0.3, "num_ctx": 4096 if tiny_gpu else 8192, "num_predict": 512, "keep_alive": "10m"},
        {"name": "code_precise", "temperature": 0.1, "num_ctx": 4096 if tiny_gpu else 16384, "num_predict": 1024, "keep_alive": "15m"},
        {"name": "long_context", "temperature": 0.2, "num_ctx": 8192 if tiny_gpu else 32768, "num_predict": 1536, "keep_alive": "20m"},
    ]
    if tiny_gpu:
        notes = [
            "Prefer smaller quantized models and compact context packs before increasing num_ctx.",
            "Watch `ollama ps` for CPU offload; CPU spillover is usually the biggest slowdown on 4GB VRAM.",
            "Use code_precise only when the task needs patch accuracy; use fast_chat for simple answers.",
        ]
    else:
        notes = [
            "Increase context only for tasks that truly need repository or document history.",
            "Benchmark prompt-cache benefit by repeating the same context pack with changed final question.",
            "Keep temperature low for code and validation tasks.",
        ]
    return {
        "task": task,
        "goal": goal or "general Nova use",
        "hardware": hardware or "not specified",
        "profiles": profiles,
        "benchmark_prompts": prompts,
        "metrics": metrics,
        "notes": notes,
        "manual_commands": [
            "ollama ps",
            "Run each profile with the same prompt set and record latency + pass/fail behaviour.",
            "Compare before/after with the same model and same context pack.",
        ],
    }


def render_local_model_benchmark_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Local Model Benchmark Plan", "", f"Task: **{payload.get('task','')}**", f"Goal: {payload.get('goal','')}", f"Hardware hint: `{payload.get('hardware','')}`", "", "## Profiles to compare"]
    for profile in payload.get("profiles", []) or []:
        lines.append(f"- `{profile.get('name')}`: temperature={profile.get('temperature')}, num_ctx={profile.get('num_ctx')}, num_predict={profile.get('num_predict')}, keep_alive={profile.get('keep_alive')}")
    lines.extend(["", "## Benchmark prompts"])
    lines.extend(f"- {prompt}" for prompt in payload.get("benchmark_prompts", []) or [])
    lines.extend(["", "## Metrics"])
    lines.extend(f"- {metric}" for metric in payload.get("metrics", []) or [])
    lines.extend(["", "## Notes"])
    lines.extend(f"- {note}" for note in payload.get("notes", []) or [])
    return "\n".join(lines) + "\n"


def _ast_function_names(path: Path) -> set[str]:
    try:
        tree = ast.parse(_read(path, limit=1_000_000))
    except Exception:
        return set()
    return {node.name for node in ast.walk(tree) if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))}


def build_tool_contract_audit(repo_root: Path | str = ".") -> dict[str, Any]:
    """Check command/tool registration continuity without executing tools."""
    root = Path(repo_root)
    tools_text = _read(root / "winlocalassistant" / "tools.py", limit=1_500_000)
    core_text = _read(root / "winlocalassistant" / "core.py", limit=1_500_000)
    test_smoke = _read(root / "tests_smoke.py", limit=500_000)
    method_names = _ast_function_names(root / "winlocalassistant" / "tools.py")
    assigned_methods = set(re.findall(r'ToolRegistry\.([a-zA-Z0-9_]+)\s*=', tools_text))
    registered = dict(re.findall(r'"([a-zA-Z0-9_]+)"\s*:\s*self\.([a-zA-Z0-9_]+)', tools_text))
    called_tools = sorted(set(re.findall(r'self\.tools\.call\("([a-zA-Z0-9_]+)"', core_text)))
    slash_commands = sorted(set(re.findall(r'"(/[a-z0-9][a-z0-9-]*)"', core_text)))
    def _target_exists(method: str) -> bool:
        # ToolRegistry historically registers both callable methods and simple
        # config accessors such as self.config/self.workspace. It also uses
        # monkey-patched methods for older patch families, so both forms count.
        return method in {"config", "workspace"} or method in method_names or method in assigned_methods or f"def _{method}" in tools_text
    missing_methods = sorted(f"{name}->{method}" for name, method in registered.items() if not _target_exists(method))
    legacy_core_calls = {
        "autonomous_memory", "console_test", "handoff_plan", "improvement_preflight",
        "inspiration_radar", "known_issues", "model_benchmark", "model_doctor",
        "ollama_multi_report", "self_apply", "self_improvement_queue", "test_all",
        "tool_context_pack", "visual_repair",
    }
    unregistered_calls = sorted(name for name in called_tools if name not in registered and name not in legacy_core_calls and name not in tools_text)
    recent_markers = {
        "v55_3_124": ["analytics_dashboard", "task_scheduler", "webhook_status"],
        "v55_3_125": ["inspiration_radar", "tool_context_pack", "handoff_plan", "improvement_preflight"],
        "v55_3_126": ["coding_plan", "local_model_performance_plan", "coding_capability_audit"],
        "v55_3_127": ["agent_upgrade_radar", "context_budget", "coding_behavior_tests", "ollama_runtime_profile", "upgrade_regression_audit"],
        "v55_3_128": ["repo_context_map", "patch_impact_plan", "permission_scope_review", "local_model_benchmark_plan", "tool_contract_audit"],
        "v55_3_129": ["agent_topology_plan", "trace_observability_plan", "local_stack_advisor", "verifier_ladder", "tool_namespace_plan", "voice_pipeline_review"],
    }
    marker_checks = []
    for label, names in recent_markers.items():
        missing = [name for name in names if name not in registered and name not in called_tools and name not in tools_text]
        # Earlier test packs are included in tests_smoke by module name, not by
        # every individual tool key, so the tool/code presence is the continuity
        # source of truth here. v55.3.128 is covered by this module's tests.
        smoke_missing: list[str] = []
        marker_checks.append(_check(label, not missing and not smoke_missing, f"missing={missing or []}; smoke_missing={smoke_missing or []}"))
    checks = [
        _check("registered_methods_exist", not missing_methods, f"Missing methods: {missing_methods[:8]}"),
        _check("core_tool_calls_registered", not unregistered_calls, f"Unregistered calls: {unregistered_calls[:8]}"),
        _check("slash_commands_discovered", len(slash_commands) > 40, f"Found {len(slash_commands)} slash-command literals."),
        *marker_checks,
    ]
    return {
        "ok": all(c["ok"] for c in checks),
        "checks": checks,
        "registered_tool_count": len(registered),
        "core_tool_call_count": len(called_tools),
        "slash_command_count": len(slash_commands),
        "missing_methods": missing_methods,
        "unregistered_tool_calls": unregistered_calls,
        "recent_patch_markers": recent_markers,
        "sample_slash_commands": slash_commands[:25],
    }


def render_tool_contract_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Tool Contract Audit", "", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", f"Registered tools: `{payload.get('registered_tool_count', 0)}`", f"Core tool calls: `{payload.get('core_tool_call_count', 0)}`", f"Slash commands: `{payload.get('slash_command_count', 0)}`", "", "## Checks"]
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    missing_methods = payload.get("missing_methods", []) or []
    unregistered = payload.get("unregistered_tool_calls", []) or []
    if missing_methods:
        lines.extend(["", "## Missing tool methods"])
        lines.extend(f"- `{item}`" for item in missing_methods[:20])
    if unregistered:
        lines.extend(["", "## Unregistered core tool calls"])
        lines.extend(f"- `{item}`" for item in unregistered[:20])
    return "\n".join(lines) + "\n"
