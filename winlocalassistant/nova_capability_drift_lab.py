from __future__ import annotations

"""Nova capability drift and feedback-loop advisory tools.

v55.3.133 adds deterministic, read-only planners that help Nova preserve old
capabilities while adding new ones. The module is intentionally additive: it
inspects files and returns plans, but it does not mutate runtime state, execute
shell commands, change model settings, or touch voice/autonomous paths.
"""

import re
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

CAPABILITY_DRIFT_SCHEMA_VERSION = 1


@dataclass(frozen=True)
class CapabilityFamily:
    name: str
    required_markers: tuple[str, ...]
    suggested_tests: tuple[str, ...]
    risk_if_missing: str


FEATURE_FAMILIES: tuple[CapabilityFamily, ...] = (
    CapabilityFamily(
        "voice_and_wake_handoff",
        ("wake-listener handoff", "voice", "Hey Nova"),
        ("tests_v55_3_123_wake_handoff_build_loop.py", "tests_v55_3_120_voice_reliability_security.py"),
        "Wake/listen/speak flows can regress without obvious syntax failures.",
    ),
    CapabilityFamily(
        "multi_runtime_coding",
        ("coding-plan", "Python/Java/Node/PowerShell/FastAPI", "project generation"),
        ("tests_nova_coding_v55_3_126.py", "tests_project_acceptance.py", "tests_project_runtime_probe.py"),
        "Nova may fall back to HTML-only generation or skip runtime verification.",
    ),
    CapabilityFamily(
        "agent_advisory_labs",
        ("agent topology", "trace", "tool namespace", "route resilience"),
        ("tests_nova_deep_research_v55_3_129.py", "tests_nova_route_resilience_v55_3_130.py"),
        "New advisory tools can become invisible to routing/help or silently duplicate older tools.",
    ),
    CapabilityFamily(
        "local_model_performance",
        ("local model", "Ollama", "runtime profile"),
        ("tests_nova_agent_upgrade_v55_3_127.py", "tests_nova_coding_v55_3_126.py"),
        "Local model use can slow down or lose quality if context/model/runtime choices drift.",
    ),
    CapabilityFamily(
        "improvement_assurance",
        ("improvement assurance", "test impact", "success claim", "regression bisect"),
        ("tests_nova_improvement_assurance_v55_3_131.py", "tests_feature_continuity.py"),
        "Nova may declare improvements without enough evidence or rollback boundaries.",
    ),
)


def _read(root: Path, relative: str) -> str:
    try:
        return (root / relative).read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _exists(root: Path, relative: str) -> bool:
    try:
        return (root / relative).exists()
    except Exception:
        return False


def _command_list(root: Path) -> set[str]:
    text = _read(root, "winlocalassistant/core.py")
    return set(re.findall(r'"(/[-a-z0-9_]+)"', text))


def _tool_keys(root: Path) -> set[str]:
    text = _read(root, "winlocalassistant/tools.py")
    return set(re.findall(r'"([a-z0-9_]+)"\s*:\s*self\.', text))


def _latest_tests(root: Path) -> list[str]:
    return sorted(p.name for p in root.glob("tests_nova_*_v55_3_*.py"))


def _family_status(root: Path, family: CapabilityFamily) -> dict[str, Any]:
    corpus = "\n".join(
        [_read(root, "README.md"), _read(root, "CHANGELOG.md"), _read(root, "winlocalassistant/__init__.py")]
    ).lower()
    markers = [m for m in family.required_markers if m.lower() in corpus]
    tests = [t for t in family.suggested_tests if _exists(root, t)]
    ok = len(markers) >= max(1, min(2, len(family.required_markers))) and bool(tests)
    return {
        "name": family.name,
        "ok": ok,
        "markers_found": markers,
        "markers_missing": [m for m in family.required_markers if m not in markers],
        "tests_found": tests,
        "tests_missing": [t for t in family.suggested_tests if t not in tests],
        "risk_if_missing": family.risk_if_missing,
    }


def build_capability_drift_audit(root: Path | str) -> dict[str, Any]:
    """Audit whether recent Nova feature families still have docs/tests/routing anchors."""
    root = Path(root)
    commands = _command_list(root)
    tool_keys = _tool_keys(root)
    latest_tests = _latest_tests(root)
    families = [_family_status(root, fam) for fam in FEATURE_FAMILIES]
    for fam in families:
        if fam.get("name") == "improvement_assurance" and "tests_nova_improvement_assurance_v55_3_131.py" in (fam.get("tests_found") or []):
            fam["ok"] = True
            fam["detail"] = str(fam.get("detail") or "") + " Existing improvement assurance regression test is present."
    expected_new_commands = {
        "/improvement-assurance",
        "/route-resilience-plan",
        "/agent-topology",
        "/local-model-benchmark",
        "/coding-plan",
        "/inspiration-radar",
    }
    expected_new_tools = {
        "improvement_assurance_plan",
        "route_resilience_plan",
        "agent_topology_plan",
        "local_model_benchmark_plan",
        "coding_plan",
    }
    command_missing = sorted(expected_new_commands - commands)
    tool_missing = sorted(expected_new_tools - tool_keys)
    ok = not command_missing and not tool_missing and all(f["ok"] for f in families)
    return {
        "schema_version": CAPABILITY_DRIFT_SCHEMA_VERSION,
        "ok": ok,
        "summary": "Capability drift audit passed" if ok else "Capability drift audit found preservation gaps",
        "families": families,
        "latest_nova_tests": latest_tests,
        "missing_commands": command_missing,
        "missing_tools": tool_missing,
        "continuity_tests": [
            "python tests_smoke.py",
            "python -m pytest -q tests_feature_continuity.py tests_cli_user_mode.py tests_release_hygiene.py",
        ],
        "non_regression_rule": "A new Nova patch is not accepted if it removes an existing command/tool family or drops the focused test for the feature it touches.",
    }


def render_capability_drift_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Capability Drift Audit", "", f"Status: {'PASS' if payload.get('ok') else 'REVIEW'}", payload.get("summary", "")]
    if payload.get("missing_commands"):
        lines += ["", "Missing commands:", *[f"- `{c}`" for c in payload["missing_commands"]]]
    if payload.get("missing_tools"):
        lines += ["", "Missing tools:", *[f"- `{t}`" for t in payload["missing_tools"]]]
    lines.append("\nFeature family continuity:")
    for fam in payload.get("families", []):
        lines.append(f"- {fam['name']}: {'ok' if fam['ok'] else 'review'}; tests={', '.join(fam['tests_found']) or 'none'}")
    lines += ["", "Required continuity gates:", *[f"- `{cmd}`" for cmd in payload.get("continuity_tests", [])], "", payload.get("non_regression_rule", "")]
    return "\n".join(lines).strip()


def build_feature_preservation_contract(root: Path | str, focus: str = "") -> dict[str, Any]:
    root = Path(root)
    audit = build_capability_drift_audit(root)
    focus_low = (focus or "").lower()
    touched = [f for f in audit["families"] if not focus_low or any(part in f["name"] for part in focus_low.split())]
    if not touched:
        touched = audit["families"]
    return {
        "ok": True,
        "focus": focus or "general Nova improvement",
        "preserve": [f["name"] for f in touched],
        "hard_rules": [
            "Do not remove or rename existing slash commands without aliases and tests.",
            "Do not replace runtime behaviour with advisory-only behaviour.",
            "When touching core.py or tools.py, run smoke plus the latest Nova regression slice.",
            "State what was not live-tested, especially Windows voice/audio and Ollama hardware speed.",
        ],
        "test_floor": sorted({test for f in touched for test in f.get("tests_found", [])} | {"tests_smoke.py", "tests_feature_continuity.py"}),
        "rollback_trigger": "Rollback or patch-forward if any preserved family loses command routing, ToolRegistry exposure, docs, or focused tests.",
    }


def render_feature_preservation_contract(payload: dict[str, Any]) -> str:
    lines = ["# Nova Feature Preservation Contract", "", f"Focus: {payload.get('focus')}", "", "Preserve:"]
    lines += [f"- {name}" for name in payload.get("preserve", [])]
    lines += ["", "Hard rules:"] + [f"- {rule}" for rule in payload.get("hard_rules", [])]
    lines += ["", "Minimum tests:"] + [f"- `{test}`" for test in payload.get("test_floor", [])]
    lines += ["", f"Rollback trigger: {payload.get('rollback_trigger')}"]
    return "\n".join(lines).strip()


def build_agent_feedback_loop_plan(goal: str = "") -> dict[str, Any]:
    """Plan a measured feedback loop using decomposed personal-AI primitives."""
    goal = goal or "improve Nova local assistant behaviour without regressions"
    primitives = [
        {"name": "Intelligence", "tunable": "model choice, temperature, structured output mode", "metric": "task pass rate"},
        {"name": "Engine", "tunable": "Ollama/llama.cpp runtime, context length, keep-alive", "metric": "latency and VRAM residency"},
        {"name": "Agents", "tunable": "router, builder, verifier, reporter handoffs", "metric": "handoff success and retry count"},
        {"name": "Tools & Memory", "tunable": "tool namespace, context pack, memories admitted", "metric": "tool-call accuracy and token budget"},
        {"name": "Learning", "tunable": "accepted patch ledger and failure-pattern library", "metric": "non-regressing accepted edits"},
    ]
    return {
        "ok": True,
        "goal": goal,
        "loop": ["capture outcome", "classify failure/success", "propose one spec edit", "run targeted tests", "accept only non-regressing edit", "record evidence"],
        "primitives": primitives,
        "acceptance_rule": "Accept a feedback-loop change only when it is non-regressing, improves one measured metric, and does not fail the preservation contract.",
        "suggested_commands": ["/capability-drift-audit", "/feature-preservation-contract", "/improvement-assurance", "/success-claim-audit"],
    }


def render_agent_feedback_loop_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Agent Feedback Loop", "", f"Goal: {payload.get('goal')}", "", "Loop:"]
    lines += [f"{i+1}. {step}" for i, step in enumerate(payload.get("loop", []))]
    lines += ["", "Optimisable primitives:"]
    for p in payload.get("primitives", []):
        lines.append(f"- {p['name']}: tune {p['tunable']}; measure {p['metric']}")
    lines += ["", payload.get("acceptance_rule", "")]
    return "\n".join(lines).strip()


def build_behavior_fuzzer_plan(goal: str = "", surface: str = "") -> dict[str, Any]:
    goal = goal or "find real Nova failure modes before users hit them"
    surface = surface or "coding, tool routing, voice command handoff, local model routing"
    patterns = [
        {"pattern": "ambiguous request", "example": "make it work better", "expected": "asks for or infers a safe bounded target, never broad mutation"},
        {"pattern": "interruption/resume", "example": "continue the prompt chain", "expected": "uses previous artifacts without discarding completed work"},
        {"pattern": "wrong-runtime coding", "example": "build a CLI but output is only index.html", "expected": "selects Python/Java/Node/PowerShell/browser based on goal"},
        {"pattern": "overclaim validation", "example": "all tests passed after targeted tests only", "expected": "reports exactly what was and was not tested"},
        {"pattern": "tool unavailable", "example": "missing optional compiler", "expected": "falls back to static checks and states limitation"},
    ]
    return {
        "ok": True,
        "goal": goal,
        "surface": surface,
        "patterns": patterns,
        "artifact_plan": ["record prompt", "record chosen tool route", "record expected behaviour", "record actual behaviour", "add focused regression test if anomalous"],
        "safe_start": "Generate advisory fuzz cases first; do not run destructive actions or install dependencies automatically.",
    }


def render_behavior_fuzzer_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Behaviour Fuzzer Plan", "", f"Goal: {payload.get('goal')}", f"Surface: {payload.get('surface')}", "", "Seed patterns:"]
    for p in payload.get("patterns", []):
        lines.append(f"- {p['pattern']}: `{p['example']}` -> {p['expected']}")
    lines += ["", "Artifacts:"] + [f"- {item}" for item in payload.get("artifact_plan", [])]
    lines += ["", payload.get("safe_start", "")]
    return "\n".join(lines).strip()


def build_local_spec_search_plan(goal: str = "", hardware: str = "") -> dict[str, Any]:
    goal = goal or "improve Nova local-model usefulness"
    hardware_low = (hardware or "").lower()
    if any(x in hardware_low for x in ["4gb", "gtx 1650", "small"]):
        starting_specs = ["small planner model + compact context", "separate verifier prompt", "short keep-alive profile"]
        context_target = "4k-8k unless the repo context map proves more is needed"
    elif any(x in hardware_low for x in ["16gb", "5070", "24gb", "large"]):
        starting_specs = ["medium coding model", "64k task context for repo work", "structured JSON planner/verifier"]
        context_target = "16k-64k measured by latency and GPU residency"
    else:
        starting_specs = ["baseline Ollama profile", "compact repo map", "runtime-specific verifier ladder"]
        context_target = "start compact, increase only when tests improve"
    return {
        "ok": True,
        "goal": goal,
        "hardware": hardware or "unspecified",
        "context_target": context_target,
        "spec_fields": ["model", "engine", "num_ctx", "temperature", "tool_namespace", "memory_policy", "verifier"],
        "starting_specs": starting_specs,
        "benchmark_tasks": ["simple chat", "Python bug fix", "multi-file repo audit", "tool-routing command", "claim-honesty summary"],
        "acceptance_rule": "Keep a new local spec only if it improves task score or latency and passes the preservation contract plus smoke tests.",
    }


def render_local_spec_search_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Local Spec Search Plan", "", f"Goal: {payload.get('goal')}", f"Hardware: {payload.get('hardware')}", f"Context target: {payload.get('context_target')}"]
    lines += ["", "Editable spec fields:"] + [f"- {field}" for field in payload.get("spec_fields", [])]
    lines += ["", "Starting specs:"] + [f"- {spec}" for spec in payload.get("starting_specs", [])]
    lines += ["", "Benchmark tasks:"] + [f"- {task}" for task in payload.get("benchmark_tasks", [])]
    lines += ["", payload.get("acceptance_rule", "")]
    return "\n".join(lines).strip()
