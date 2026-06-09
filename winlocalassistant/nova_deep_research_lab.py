from __future__ import annotations

"""Read-only Nova deep-research advisory helpers.

v55.3.129 implements the Nova Improvement Report's low-regression advisory
layer. The helpers in this module deliberately do not execute commands, edit
files, install packages, call models, change voice state, or alter scheduler /
autonomous behaviour. They turn current agent/local-model/Jarvis-style design
patterns into deterministic plans Nova can show before a risky implementation.
"""

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AgentStage:
    name: str
    role: str
    handoff_to: list[str] = field(default_factory=list)
    guardrail: str = "read-only planning unless user explicitly approves state changes"
    evidence: str = "structured summary and explicit next command"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class TraceSpan:
    name: str
    captures: list[str]
    redactions: list[str]
    pass_condition: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class VerifierStep:
    name: str
    command: str
    purpose: str
    required: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ToolNamespace:
    name: str
    purpose: str
    expose_when: list[str]
    representative_tools: list[str]
    defer_when: str = "prompt does not match namespace intent"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SECRET_MARKERS = {".env", "secret", "token", "apikey", "api_key", "password", "credential", "private_key"}


def _check(name: str, ok: bool, detail: str) -> dict[str, Any]:
    return {"name": name, "ok": bool(ok), "detail": detail}


def _read(path: Path, limit: int = 180_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _token_estimate(text: str) -> int:
    return max(1, math.ceil(len(text or "") / 4))


def _words(text: str) -> set[str]:
    base = {w for w in re.findall(r"[a-z0-9_]{3,}", (text or "").lower())}
    expansions = {
        "voice": {"wake", "audio", "microphone", "tts", "stt", "headset", "mute", "listen"},
        "coding": {"code", "repo", "tests", "runtime", "python", "java", "node", "verify", "patch"},
        "model": {"ollama", "llama", "gguf", "context", "num_ctx", "vram", "quant", "tokens"},
        "agent": {"handoff", "trace", "guardrail", "tool", "namespace", "session", "planner"},
        "jarvis": {"voice", "wake", "assistant", "mqtt", "skill", "pipeline"},
        "autonomous": {"idle", "scheduler", "rollback", "proposal", "receipt", "approval"},
    }
    for key, extra in expansions.items():
        if key in base or key in (text or "").lower():
            base.update(extra)
    return base or {"nova", "assistant", "agent"}


def _safe_path(path: Path) -> bool:
    low = path.as_posix().lower()
    return not any(marker in low for marker in _SECRET_MARKERS)


def _repo_summary(repo_root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    root = Path(repo_root)
    wanted = _words(goal)
    files: list[dict[str, Any]] = []
    for pattern in ("AGENTS.md", "README.md", "CHANGELOG.md", "winlocalassistant/core.py", "winlocalassistant/tools.py", "winlocalassistant/nova_*.py", "tests_nova_*.py", "tests_smoke.py"):
        for path in sorted(root.glob(pattern)):
            if not path.is_file() or not _safe_path(path):
                continue
            rel = path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix()
            text = _read(path, limit=60_000)
            score = 0
            low_rel = rel.lower()
            low_text = text.lower()
            for word in wanted:
                if word in low_rel:
                    score += 3
                elif word in low_text:
                    score += 1
            if rel in {"AGENTS.md", "README.md", "CHANGELOG.md"}:
                score += 4
            if rel.endswith(("core.py", "tools.py")):
                score += 6
            if "nova_" in rel:
                score += 3
            files.append({"path": rel, "score": score, "estimated_tokens": _token_estimate(text[:40_000])})
    files = sorted(files, key=lambda item: (-int(item["score"]), int(item["estimated_tokens"]), str(item["path"])))[:16]
    return {"files": files, "estimated_tokens": sum(int(item["estimated_tokens"]) for item in files)}


def build_agent_topology_plan(repo_root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    """Design a bounded specialist topology for a Nova task."""
    goal = (goal or "improve Nova without regressions").strip()
    stages = [
        AgentStage("triage_router", "classify request type, risk and required specialists", ["context_mapper", "safety_gate"]),
        AgentStage("context_mapper", "select only relevant repo/context files and compress stale history", ["builder"], evidence="context pack with token estimate"),
        AgentStage("safety_gate", "detect destructive, network, install, voice-device or broad-scope actions before execution", ["builder"], evidence="permission/scope finding list"),
        AgentStage("builder", "propose or implement the smallest useful patch", ["runtime_runner"], guardrail="never self-certify; must hand off to verifier"),
        AgentStage("runtime_runner", "run only approved validation commands", ["verifier"], guardrail="bounded timeout and no background promise"),
        AgentStage("verifier", "compare claimed behaviour against tests, syntax gates and acceptance evidence", ["reporter"], evidence="pass/fail evidence per command"),
        AgentStage("reporter", "summarise changes, failures, limitations, artifacts and next safest step", []),
    ]
    checks = [
        _check("bounded_specialist_count", len(stages) <= 8, f"{len(stages)} specialists/stages planned."),
        _check("verifier_is_separate", any(stage.name == "verifier" for stage in stages), "Builder cannot self-certify."),
        _check("safety_gate_present", any(stage.name == "safety_gate" for stage in stages), "Permission and scope review occurs before execution."),
    ]
    return {
        "goal": goal,
        "ok": all(c["ok"] for c in checks),
        "source_inspiration": ["agent handoffs", "context filters", "guardrails", "separate verifier authority"],
        "stages": [stage.to_dict() for stage in stages],
        "checks": checks,
        "next_safe_step": "Use /trace-observability and /verifier-ladder before changing runtime behaviour.",
    }


def render_agent_topology_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Agent Topology Plan", "", f"Goal: {payload.get('goal','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Specialists and handoffs"]
    for stage in payload.get("stages", []) or []:
        handoff = ", ".join(stage.get("handoff_to") or []) or "finish"
        lines.append(f"- `{stage.get('name')}` → {handoff}: {stage.get('role')} Guardrail: {stage.get('guardrail')}")
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    lines.append(f"\nNext safe step: {payload.get('next_safe_step','')}")
    return "\n".join(lines).strip() + "\n"


def build_trace_observability_plan(repo_root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    """Define a trace/span contract for a Nova workflow."""
    goal = (goal or "make Nova work observable without changing behaviour").strip()
    spans = [
        TraceSpan("request.received", ["command", "goal", "entry_surface"], ["raw user secrets", "local absolute paths unless needed"], "request id is created"),
        TraceSpan("context.selected", ["files", "estimated_tokens", "reason"], ["secret-like files", "large pasted blobs by default"], "token budget is bounded"),
        TraceSpan("model.call", ["provider", "model", "num_ctx", "duration_ms", "tokens"], ["prompt body unless debug export is approved"], "latency and model settings are recorded"),
        TraceSpan("tool.route", ["tool_name", "namespace", "arguments_schema", "result_ok"], ["secret-like argument values"], "unknown tools are visible as failures"),
        TraceSpan("verification.run", ["command", "timeout", "exit_code", "tail_output"], ["credential-like output"], "verification evidence exists before success claim"),
        TraceSpan("report.final", ["artifact_paths", "limitations", "regression_status"], ["private scratchpad"], "final report distinguishes passed, failed and untested items"),
    ]
    checks = [
        _check("verification_span_present", any(span.name == "verification.run" for span in spans), "Verifier evidence is traced."),
        _check("redaction_present", all(span.redactions for span in spans), "Each span has a redaction rule."),
        _check("model_settings_visible", any("num_ctx" in span.captures for span in spans), "Local-model runtime choices can be audited."),
    ]
    return {
        "goal": goal,
        "ok": all(c["ok"] for c in checks),
        "spans": [span.to_dict() for span in spans],
        "retention_policy": "Keep compact JSONL traces locally; export only on explicit user request.",
        "checks": checks,
    }


def render_trace_observability_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Trace / Observability Contract", "", f"Goal: {payload.get('goal','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Required spans"]
    for span in payload.get("spans", []) or []:
        lines.append(f"- `{span.get('name')}` captures `{', '.join(span.get('captures') or [])}`; redacts `{', '.join(span.get('redactions') or [])}`; pass: {span.get('pass_condition')}")
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    lines.append(f"\nRetention: {payload.get('retention_policy','')}")
    return "\n".join(lines).strip() + "\n"


def _hardware_tier(hardware: str) -> str:
    low = (hardware or "").lower()
    match = re.search(r"(\d+)\s*(?:gb|gib)\s*(?:vram|gpu)?", low)
    gb = int(match.group(1)) if match else 0
    if gb and gb <= 6:
        return "small_gpu"
    if 7 <= gb <= 12:
        return "mid_gpu"
    if 13 <= gb <= 24:
        return "large_consumer_gpu"
    if gb >= 25:
        return "workstation"
    if "cpu" in low and "gpu" not in low:
        return "cpu_first"
    return "unknown"


def build_local_stack_advisor(goal: str = "", hardware: str = "") -> dict[str, Any]:
    """Advise when Nova should use Ollama or llama.cpp for local models."""
    goal = (goal or "general Nova assistant work").strip()
    tier = _hardware_tier(hardware)
    task_words = _words(goal)
    coding = bool({"code", "coding", "debug", "repo", "python", "java", "node", "tests"} & task_words)
    voice = bool({"voice", "wake", "audio", "tts", "stt", "jarvis"} & task_words)
    if tier in {"small_gpu", "cpu_first"}:
        models = ["qwen3:4b", "gemma3:4b", "deepseek-r1:8b only for hard debugging if latency is acceptable"]
        num_ctx = 4096 if coding else 2048
        engine = "Ollama default; llama.cpp only for carefully chosen small GGUF files"
    elif tier == "mid_gpu":
        models = ["qwen3:8b or qwen3:14b", "deepseek-r1:14b for reasoning", "gemma3:12b for mixed assistant tasks"]
        num_ctx = 8192 if coding else 4096
        engine = "Ollama default; consider llama.cpp for explicit GPU offload benchmarking"
    elif tier == "large_consumer_gpu":
        models = ["qwen3:30b", "gpt-oss:20b", "gemma3:27b", "deepseek-r1:14b fast fallback"]
        num_ctx = 32768 if coding else 8192
        engine = "Ollama for integration; llama.cpp for GGUF, grammar, speculative or benchmark paths"
    elif tier == "workstation":
        models = ["llama3.3:70b", "qwen3:30b", "gpt-oss:20b low-latency fallback"]
        num_ctx = 65536 if coding else 16384
        engine = "Ollama or llama.cpp server depending benchmark results"
    else:
        models = ["qwen3:4b", "qwen3:8b", "gemma3:4b", "deepseek-r1:8b"]
        num_ctx = 4096 if coding else 2048
        engine = "Start with Ollama and verify actual residency with ollama ps"
    commands = [
        "ollama list",
        "ollama ps",
        f"ollama run {models[0].split()[0]} \"Summarise this task in JSON with risks and tests.\"",
    ]
    if "llama.cpp" in engine:
        commands.extend(["llama-bench -m path/to/model.gguf", "llama-server -m path/to/model.gguf -ngl 999 -c 8192"])
    checks = [
        _check("hardware_tier_set", bool(tier), f"Hardware tier: {tier}."),
        _check("context_is_explicit", num_ctx > 0, f"Recommended num_ctx: {num_ctx}."),
        _check("engine_choice_explained", bool(engine), engine),
    ]
    return {
        "goal": goal,
        "hardware": hardware or "unspecified",
        "hardware_tier": tier,
        "task_flags": {"coding": coding, "voice": voice},
        "ok": all(c["ok"] for c in checks),
        "recommended_engine": engine,
        "recommended_models": models,
        "recommended_options": {"num_ctx": num_ctx, "temperature": 0.2 if coding else 0.4, "num_predict": 1024 if coding else 512, "keep_alive": "10m"},
        "benchmark_commands": commands,
        "rules": [
            "Prefer compact context maps before increasing num_ctx.",
            "Use structured JSON/schema outputs for planner and verifier steps.",
            "Use llama.cpp only when its controls are actually needed, not by default.",
            "Record settings in trace spans before comparing model quality.",
        ],
        "checks": checks,
    }


def render_local_stack_advisor(payload: dict[str, Any]) -> str:
    lines = ["# Nova Local Stack Advisor", "", f"Goal: {payload.get('goal','')}", f"Hardware: `{payload.get('hardware','')}` → `{payload.get('hardware_tier','')}`", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", f"Recommended engine: {payload.get('recommended_engine','')}", "", "## Model shortlist"]
    lines.extend(f"- `{model}`" for model in payload.get("recommended_models", []) or [])
    lines.extend(["", "## Options", "```json"])
    import json
    lines.append(json.dumps(payload.get("recommended_options", {}), indent=2))
    lines.extend(["```", "", "## Benchmark commands"])
    lines.extend(f"```powershell\n{cmd}\n```" for cmd in payload.get("benchmark_commands", []) or [])
    lines.extend(["", "## Rules"])
    lines.extend(f"- {rule}" for rule in payload.get("rules", []) or [])
    return "\n".join(lines).strip() + "\n"


def build_verifier_ladder(goal: str = "", runtime_hint: str = "") -> dict[str, Any]:
    """Create a runtime-aware verifier ladder for code generation/patches."""
    blob = f"{goal} {runtime_hint}".lower()
    runtime = "browser"
    if any(w in blob for w in ["python", ".py", "fastapi"]):
        runtime = "python"
    elif any(w in blob for w in ["java", ".java", "javac"]):
        runtime = "java"
    elif any(w in blob for w in ["node", "javascript", "typescript", "npm", ".js", ".ts"]):
        runtime = "node"
    elif any(w in blob for w in ["powershell", ".ps1", "ps1"]):
        runtime = "powershell"
    elif any(w in blob for w in ["fastapi", "api service"]):
        runtime = "fastapi"
    base = [VerifierStep("syntax_compile", "python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py", "protect Nova source files")]
    by_runtime: dict[str, list[VerifierStep]] = {
        "python": [VerifierStep("python_compile", "python -m py_compile path/to/main.py", "check generated Python syntax"), VerifierStep("python_smoke", "python path/to/main.py --help", "verify entrypoint starts", False)],
        "java": [VerifierStep("java_compile", "javac Main.java", "check Java syntax and imports"), VerifierStep("java_run", "java Main", "verify CLI/main flow", False)],
        "node": [VerifierStep("node_syntax", "node --check app.js", "check JavaScript syntax"), VerifierStep("npm_test", "npm test", "run project tests if package.json exists", False)],
        "powershell": [VerifierStep("ps_parse", "powershell -NoProfile -Command \"$null=[System.Management.Automation.PSParser]::Tokenize((Get-Content .\\script.ps1 -Raw), [ref]$null)\"", "parse script without executing it"), VerifierStep("ps_help", "powershell -NoProfile -ExecutionPolicy Bypass -File .\\script.ps1 -Help", "optional script help path", False)],
        "fastapi": [VerifierStep("python_compile", "python -m py_compile app.py", "check API syntax"), VerifierStep("fastapi_import", "python -c \"import app; print('import ok')\"", "verify app imports without starting server")],
        "browser": [VerifierStep("html_files", "dir /b index.html app.js style.css", "confirm expected browser files", False), VerifierStep("node_syntax", "node --check app.js", "check JS syntax if Node exists", False)],
    }
    steps = base + by_runtime.get(runtime, by_runtime["browser"]) + [VerifierStep("smoke", "python tests_smoke.py", "run Nova smoke suite")]
    checks = [
        _check("runtime_specific", runtime in by_runtime, f"Runtime selected: {runtime}."),
        _check("syntax_gate_present", any("compile" in s.name or "syntax" in s.name or "parse" in s.name for s in steps), "Syntax/parse gate exists."),
        _check("smoke_gate_present", any(s.name == "smoke" for s in steps), "Nova smoke gate remains present."),
    ]
    return {"goal": goal or "verify generated code", "runtime": runtime, "ok": all(c["ok"] for c in checks), "steps": [s.to_dict() for s in steps], "checks": checks}


def render_verifier_ladder(payload: dict[str, Any]) -> str:
    lines = ["# Nova Verifier Ladder", "", f"Goal: {payload.get('goal','')}", f"Runtime: `{payload.get('runtime','')}`", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Steps"]
    for step in payload.get("steps", []) or []:
        req = "required" if step.get("required", True) else "optional"
        lines.append(f"- **{step.get('name')}** ({req}): {step.get('purpose')}\n  ```powershell\n  {step.get('command')}\n  ```")
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    return "\n".join(lines).strip() + "\n"


def build_tool_namespace_plan(repo_root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    """Plan conditional tool exposure for Nova's large tool surface."""
    namespaces = [
        ToolNamespace("repo", "codebase reading, context maps and patch impact planning", ["repo", "code", "tests", "patch"], ["repo_context_map", "patch_impact_plan", "codebase_advisor"]),
        ToolNamespace("coding", "project generation, coding plans and verifier ladders", ["build", "create code", "debug", "runtime"], ["coding_plan", "coding_behavior_tests", "verifier_ladder"]),
        ToolNamespace("models", "local model choice, context budgets and benchmarks", ["ollama", "local model", "vram", "latency"], ["context_budget", "local_stack_advisor", "local_model_benchmark_plan"]),
        ToolNamespace("voice", "wake-word, STT/TTS, headset and Jarvis-style pipeline review", ["hey nova", "voice", "microphone", "audio"], ["voice_audit", "voice_pipeline_review"]),
        ToolNamespace("autonomy", "idle/autonomous plans, receipts and guarded scheduled work", ["autonomous", "idle", "scheduler", "self improve"], ["upgrade_regression_audit", "proposal_ledger_view", "list_tasks"]),
        ToolNamespace("release", "packaging, version hygiene and no-regression reporting", ["release", "zip", "package", "version"], ["release_package", "tool_contract_audit", "completion_audit"]),
    ]
    tools_text = _read(Path(repo_root) / "winlocalassistant" / "tools.py", limit=240_000)
    registered_count = len(re.findall(r'"[a-zA-Z0-9_]+"\s*:\s*self\.', tools_text))
    checks = [
        _check("namespace_count_bounded", 4 <= len(namespaces) <= 8, f"{len(namespaces)} namespaces planned."),
        _check("voice_namespace_present", any(ns.name == "voice" for ns in namespaces), "Voice tools remain explicit."),
        _check("large_tool_surface_detected", registered_count >= 40, f"Detected about {registered_count} registered names."),
    ]
    return {
        "goal": goal or "reduce tool prompt bloat without removing commands",
        "ok": all(c["ok"] for c in checks),
        "registered_tool_name_estimate": registered_count,
        "namespaces": [ns.to_dict() for ns in namespaces],
        "rules": [
            "Do not remove old slash commands; namespace planning is a prompt/context optimisation first.",
            "Expose only matching namespaces to local models when command intent is clear.",
            "Always keep status/help/safety tools available.",
            "Add trace spans before automatic hidden-tool behaviour is enabled.",
        ],
        "checks": checks,
    }


def render_tool_namespace_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Tool Namespace Plan", "", f"Goal: {payload.get('goal','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", f"Registered tool-name estimate: `{payload.get('registered_tool_name_estimate', 0)}`", "", "## Namespaces"]
    for ns in payload.get("namespaces", []) or []:
        lines.append(f"- `{ns.get('name')}` — {ns.get('purpose')}; expose when: {', '.join(ns.get('expose_when') or [])}; examples: `{', '.join(ns.get('representative_tools') or [])}`")
    lines.extend(["", "## Rules"])
    lines.extend(f"- {rule}" for rule in payload.get("rules", []) or [])
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    return "\n".join(lines).strip() + "\n"


def build_voice_pipeline_review(repo_root: Path | str = ".", focus: str = "") -> dict[str, Any]:
    """Review Nova's voice pipeline using Jarvis-style modular-assistant ideas."""
    root = Path(repo_root)
    voice_files = []
    for pattern in ("winlocalassistant/*voice*.py", "winlocalassistant/*audio*.py", "winlocalassistant/webui.py", "winlocalassistant/core.py"):
        for path in sorted(root.glob(pattern)):
            if path.is_file() and _safe_path(path):
                text = _read(path, limit=80_000)
                if any(marker in text.lower() or marker in path.name.lower() for marker in ["voice", "wake", "speech", "microphone", "audio", "tts", "stt"]):
                    voice_files.append({"path": path.relative_to(root).as_posix() if path.is_relative_to(root) else path.as_posix(), "estimated_tokens": _token_estimate(text[:50_000])})
    recommendations = [
        "Keep wake-word detection, STT, TTS, device selection and command routing as separate diagnosable stages.",
        "Add explicit listening/speaking/muted receipts before changing headset or wake behaviour.",
        "Prefer a voice backend capability map over hidden assumptions about Windows audio devices.",
        "Borrow satellite/message-bus ideas only as optional adapters; do not replace the desktop-first pipeline yet.",
        "Require voice-specific regression prompts before any live audio change ships.",
    ]
    checks = [
        _check("voice_files_detected", bool(voice_files), f"Found {len(voice_files)} likely voice/UI files."),
        _check("review_is_read_only", True, "This review does not touch live audio or wake-word state."),
        _check("modular_stages_named", all(word in " ".join(recommendations).lower() for word in ["wake", "stt", "tts"]), "Wake/STT/TTS are named separately."),
    ]
    return {
        "focus": focus or "Nova Jarvis-style voice reliability",
        "ok": all(c["ok"] for c in checks),
        "voice_files": voice_files[:12],
        "pipeline_stages": ["wake_word", "audio_capture", "stt", "intent_router", "tool_or_chat", "tts", "mute/listening_receipts"],
        "recommendations": recommendations,
        "defer_until_tests": ["automatic device switching", "voice satellite abstraction", "live wake-word refactor"],
        "checks": checks,
    }


def render_voice_pipeline_review(payload: dict[str, Any]) -> str:
    lines = ["# Nova Voice Pipeline Review", "", f"Focus: {payload.get('focus','')}", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Candidate voice files"]
    lines.extend(f"- `{item.get('path')}` — est. `{item.get('estimated_tokens')}` tokens" for item in payload.get("voice_files", []) or [])
    lines.extend(["", "## Modular stages", ", ".join(f"`{s}`" for s in payload.get("pipeline_stages", []) or []), "", "## Recommendations"])
    lines.extend(f"- {item}" for item in payload.get("recommendations", []) or [])
    lines.extend(["", "## Defer until tests exist"])
    lines.extend(f"- {item}" for item in payload.get("defer_until_tests", []) or [])
    lines.extend(["", "## Checks"])
    lines.extend(f"- {'PASS' if c.get('ok') else 'REVIEW'} `{c.get('name')}`: {c.get('detail')}" for c in payload.get("checks", []) or [])
    return "\n".join(lines).strip() + "\n"


__all__ = [
    "build_agent_topology_plan",
    "render_agent_topology_plan",
    "build_trace_observability_plan",
    "render_trace_observability_plan",
    "build_local_stack_advisor",
    "render_local_stack_advisor",
    "build_verifier_ladder",
    "render_verifier_ladder",
    "build_tool_namespace_plan",
    "render_tool_namespace_plan",
    "build_voice_pipeline_review",
    "render_voice_pipeline_review",
]
