from __future__ import annotations

"""Read-only Nova improvement assurance helpers.

v55.3.131 adds deterministic assurance planning for Nova's own upgrade loop.
The module is intentionally advisory: it does not execute shell commands, edit
files, call models, install packages, read secrets, or change live runtime
behaviour.  It turns a proposed improvement into evidence requirements,
test-impact hints, rollback boundaries, and success-claim checks.
"""

import math
import re
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class EvidenceGate:
    name: str
    purpose: str
    required_evidence: list[str]
    pass_rule: str
    blocks_success_claim: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ImpactEdge:
    source: str
    likely_tests: list[str] = field(default_factory=list)
    risk: str = "medium"
    reason: str = "changed file participates in a core Nova surface"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class ClaimCheck:
    claim: str
    allowed_when: list[str]
    safer_wording: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


_SECRET_MARKERS = {".env", "secret", "token", "apikey", "api_key", "password", "credential", "private_key"}
_CORE_SURFACES = {
    "winlocalassistant/core.py": ["tests_cli_user_mode.py", "tests_feature_continuity.py", "tests_smoke.py"],
    "winlocalassistant/tools.py": ["tests_feature_continuity.py", "tests_command_verifier.py", "tests_smoke.py"],
    "winlocalassistant/webui.py": ["tests_webui_idle_status.py", "tests_release_hygiene.py", "tests_smoke.py"],
    "winlocalassistant/nova_system_test.py": ["tests_smoke.py"],
    "tests_smoke.py": ["tests_smoke.py"],
}
_RUNTIME_TESTS = {
    "python": ["python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py"],
    "javascript": ["node --check <changed-js-file>"],
    "java": ["javac <changed-java-file>"],
    "powershell": ["powershell -NoProfile -Command parser-check <changed-ps1-file>"],
    "browser": ["project runtime probe or browser harness for changed browser app"],
}


def _read(path: Path, limit: int = 160_000) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")[:limit]
    except Exception:
        return ""


def _safe(path: str | Path) -> bool:
    low = str(path).replace("\\", "/").lower()
    return not any(marker in low for marker in _SECRET_MARKERS)


def _split_items(text: str) -> list[str]:
    raw = re.split(r"[\n,;]+|\s+=>\s+", text or "")
    out: list[str] = []
    seen: set[str] = set()
    for item in raw:
        clean = item.strip().strip('"\'')
        if not clean:
            continue
        clean = clean.replace("\\", "/")
        if clean not in seen:
            seen.add(clean)
            out.append(clean)
    return out


def _changed_files(files: str | list[str] | tuple[str, ...]) -> list[str]:
    if isinstance(files, str):
        return [f for f in _split_items(files) if "." in f or "/" in f]
    return [str(f).replace("\\", "/") for f in files if str(f).strip()]


def _runtime_for(path: str) -> str:
    low = path.lower()
    if low.endswith(".py"):
        return "python"
    if low.endswith((".js", ".mjs", ".cjs", ".ts")):
        return "javascript"
    if low.endswith(".java"):
        return "java"
    if low.endswith(".ps1"):
        return "powershell"
    if low.endswith((".html", ".css")):
        return "browser"
    return "generic"


def _risk_for(path: str) -> tuple[str, str]:
    low = path.lower().replace("\\", "/")
    if not _safe(low):
        return "high", "secret-adjacent path must not be read or modified by autonomous improvement"
    if low in {"winlocalassistant/core.py", "winlocalassistant/tools.py", "app.py"}:
        return "high", "central command/tool routing surface"
    if any(part in low for part in ["voice", "audio", "wake", "autonomous", "rollback", "scheduler", "provider"]):
        return "high", "live behaviour surface that needs extra regression evidence"
    if low.startswith("tests_") or "/tests" in low:
        return "medium", "test surface can accidentally weaken validation"
    if low.startswith("winlocalassistant/nova_"):
        return "medium", "Nova advisory/capability module; low runtime risk but needs registry and command tests"
    if low.startswith("docs/") or low.endswith(".md"):
        return "low", "documentation-only or non-runtime path"
    return "medium", "unknown impact needs targeted smoke evidence"


def _score(value: int, max_value: int = 100) -> int:
    return max(0, min(max_value, int(value)))


def build_test_impact_graph(repo_root: Path | str = ".", changed: str | list[str] = "") -> dict[str, Any]:
    """Map changed files to the most likely validation commands/tests."""
    root = Path(repo_root).expanduser().resolve()
    files = _changed_files(changed) or ["winlocalassistant/core.py", "winlocalassistant/tools.py", "tests_smoke.py"]
    edges: list[ImpactEdge] = []
    commands: list[str] = ["python -W error::SyntaxWarning -m py_compile app.py winlocalassistant/*.py tests_smoke.py"]
    tests: list[str] = []
    for file in files:
        risk, reason = _risk_for(file)
        likely = list(_CORE_SURFACES.get(file, []))
        runtime = _runtime_for(file)
        if file.startswith("winlocalassistant/nova_"):
            guessed = "tests_" + Path(file).stem + ".py"
            likely.extend([guessed, "tests_smoke.py", "tests_feature_continuity.py"])
        if file.startswith("tests_"):
            likely.append(file)
        if runtime in _RUNTIME_TESTS:
            commands.extend(_RUNTIME_TESTS[runtime])
        if not likely:
            likely.extend(["tests_smoke.py", "tests_feature_continuity.py"])
        existing = [t for t in dict.fromkeys(likely) if (root / t).exists() or t.startswith("tests_")]
        tests.extend(existing)
        edges.append(ImpactEdge(file, existing, risk, reason))
    unique_tests = list(dict.fromkeys(tests))
    if unique_tests:
        commands.append("python -m pytest -q " + " ".join(unique_tests[:12]))
    checks = [
        {"name": "has_changed_files", "ok": bool(files), "detail": "At least one file or fallback core surface is mapped."},
        {"name": "has_targeted_tests", "ok": bool(unique_tests), "detail": "Every patch should map to at least one targeted validation test."},
        {"name": "avoids_secret_paths", "ok": all(_safe(f) for f in files), "detail": "Secret-adjacent paths are excluded from autonomous improvement."},
    ]
    return {
        "ok": all(c["ok"] for c in checks),
        "root": str(root),
        "changed_files": files,
        "edges": [e.to_dict() for e in edges],
        "targeted_tests": unique_tests,
        "validation_commands": list(dict.fromkeys(commands)),
        "checks": checks,
        "source_inspiration": ["graph-based impact analysis", "test-driven agentic development", "regression-first patch validation"],
    }


def render_test_impact_graph(payload: dict[str, Any]) -> str:
    lines = ["# Nova Test Impact Graph", "", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Changed-file impact"]
    for edge in payload.get("edges", []) or []:
        lines.append(f"- `{edge.get('source')}` -> {', '.join(edge.get('likely_tests') or []) or 'manual review'} | risk: **{edge.get('risk')}** | {edge.get('reason')}")
    lines.extend(["", "## Validation commands"])
    lines.extend(f"- `{cmd}`" for cmd in payload.get("validation_commands", []) or [])
    return "\n".join(lines).strip() + "\n"


def build_improvement_assurance_plan(repo_root: Path | str = ".", goal: str = "", changed: str | list[str] = "") -> dict[str, Any]:
    """Build acceptance/evidence gates for a proposed Nova improvement."""
    goal = (goal or "improve Nova without regressions").strip()
    impact = build_test_impact_graph(repo_root, changed)
    high_risk = [e for e in impact["edges"] if e.get("risk") == "high"]
    gates = [
        EvidenceGate("intent_preservation", "prove the patch preserves existing user-facing behaviour", ["feature continuity test", "old command still routes", "no removed public slash command"], "no continuity failure is acceptable"),
        EvidenceGate("syntax_and_imports", "catch broken Python imports/registry wiring before runtime", ["py_compile over app.py and winlocalassistant/*.py", "focused test module import"], "zero syntax/import errors"),
        EvidenceGate("targeted_regression", "validate exactly the surfaces touched by the patch", impact.get("targeted_tests", [])[:10], "all mapped tests pass or are explicitly marked untested"),
        EvidenceGate("claim_honesty", "prevent overstating sandbox-only validation", ["list passed tests", "list not live-tested surfaces", "state timeout honestly"], "final report separates passed, timed out, and untested"),
        EvidenceGate("rollback_boundary", "make the change reversible and small", ["single-purpose module or minimal touched file set", "no broad rewrites", "release zip and manifest"], "user can revert to previous zip if validation fails"),
    ]
    if high_risk:
        gates.append(EvidenceGate("high_risk_manual_gate", "extra caution for live behaviour surfaces", ["manual review", "explicit user approval before live behaviour change", "voice/autonomous/runtime-specific tests"], "high-risk live-path changes remain advisory unless specifically validated"))
    complexity_penalty = min(35, len(impact.get("changed_files", [])) * 4 + len(high_risk) * 9)
    evidence_bonus = min(35, len(impact.get("targeted_tests", [])) * 3 + 10)
    assurance_score = _score(60 + evidence_bonus - complexity_penalty)
    checks = [
        {"name": "has_evidence_gates", "ok": len(gates) >= 5, "detail": "Improvement plan includes syntax, regression, honesty and rollback evidence gates."},
        {"name": "has_impact_graph", "ok": bool(impact.get("edges")), "detail": "Patch has a mapped test-impact graph."},
        {"name": "read_only_plan", "ok": True, "detail": "This module is advisory and does not execute or modify files."},
    ]
    return {
        "ok": all(c["ok"] for c in checks),
        "goal": goal,
        "assurance_score": assurance_score,
        "risk_level": "high" if high_risk else "medium" if assurance_score < 80 else "low",
        "evidence_gates": [g.to_dict() for g in gates],
        "impact_graph": impact,
        "acceptance_rule": "A patch is not an improvement until it has a specific user-facing benefit, targeted evidence, no known regression, and honest untested-surface disclosure.",
        "checks": checks,
    }


def render_improvement_assurance_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Improvement Assurance Plan", "", f"Goal: {payload.get('goal','')}", f"Assurance score: **{payload.get('assurance_score')}** | risk: **{payload.get('risk_level')}**", "", "## Evidence gates"]
    for gate in payload.get("evidence_gates", []) or []:
        evidence = "; ".join(gate.get("required_evidence") or [])
        lines.append(f"- `{gate.get('name')}`: {gate.get('purpose')} | evidence: {evidence} | pass rule: {gate.get('pass_rule')}")
    lines.append(f"\nAcceptance rule: {payload.get('acceptance_rule','')}")
    return "\n".join(lines).strip() + "\n"


def build_patch_quality_score(repo_root: Path | str = ".", changed: str | list[str] = "") -> dict[str, Any]:
    """Score likely maintainability/regression risk for a proposed patch."""
    root = Path(repo_root).expanduser().resolve()
    files = _changed_files(changed) or []
    if not files:
        files = ["winlocalassistant/core.py", "winlocalassistant/tools.py"]
    items: list[dict[str, Any]] = []
    total_penalty = 0
    for file in files:
        risk, reason = _risk_for(file)
        path = root / file
        text = _read(path, 80_000) if path.exists() and _safe(file) else ""
        lines = text.count("\n") + (1 if text else 0)
        has_tests = file.startswith("tests_") or bool(re.search(r"tests?[_/].*\.py$", file))
        penalty = {"low": 3, "medium": 10, "high": 22}[risk]
        if lines > 1000:
            penalty += 8
        if file.endswith(".py") and "except Exception" in text:
            penalty += 4
        if not has_tests and file.startswith("winlocalassistant/"):
            penalty += 3
        total_penalty += penalty
        items.append({"path": file, "risk": risk, "reason": reason, "line_count_observed": lines, "penalty": penalty})
    score = _score(100 - total_penalty)
    recommendations = [
        "Prefer one additive module plus small registry/routing wrappers over broad rewrites.",
        "Add or update a focused tests_nova_* file and include it in tests_smoke.py.",
        "Keep final claims tied to commands that actually ran.",
    ]
    if any(i["risk"] == "high" for i in items):
        recommendations.append("High-risk surfaces need extra continuity tests and clear manual follow-up notes.")
    return {"ok": score >= 60 and all(_safe(f) for f in files), "score": score, "changed_files": files, "items": items, "recommendations": recommendations}


def render_patch_quality_score(payload: dict[str, Any]) -> str:
    lines = ["# Nova Patch Quality Score", "", f"Score: **{payload.get('score')}** | Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## File risks"]
    for item in payload.get("items", []) or []:
        lines.append(f"- `{item.get('path')}`: {item.get('risk')} risk, penalty {item.get('penalty')} — {item.get('reason')}")
    lines.extend(["", "## Recommendations"])
    lines.extend(f"- {rec}" for rec in payload.get("recommendations", []) or [])
    return "\n".join(lines).strip() + "\n"


def build_success_claim_audit(summary: str = "") -> dict[str, Any]:
    """Audit a final release summary for overclaims and missing caveats."""
    text = summary or ""
    low = text.lower()
    checks = [
        {"name": "mentions_validation", "ok": any(w in low for w in ["validation", "tests", "smoke", "pytest", "py_compile"]), "detail": "Success claims should name actual validation."},
        {"name": "separates_timeout", "ok": "timeout" not in low or any(w in low for w in ["not claiming", "partial", "timed out"]), "detail": "Timeouts must not be described as full-suite success."},
        {"name": "mentions_untested_live_surfaces", "ok": any(w in low for w in ["could not live-test", "not live-tested", "untested", "manual"]), "detail": "Windows-only/audio/model hardware gaps should be disclosed when relevant."},
        {"name": "no_absolute_overclaim", "ok": not any(p in low for p in ["guaranteed no regressions", "everything works", "fully verified"]), "detail": "Avoid absolute claims that exceed evidence."},
    ]
    claim_checks = [
        ClaimCheck("No regression", ["syntax passed", "smoke passed", "targeted regression slice passed", "untested surfaces listed"], "Targeted regression checks passed; no failure was observed in the executed suites."),
        ClaimCheck("Implemented", ["files changed", "commands/tests added", "validation run"], "Implemented and validated with the listed commands."),
        ClaimCheck("Full suite passed", ["full suite command completed successfully"], "Full suite was attempted but did not complete; targeted suites passed."),
    ]
    return {"ok": all(c["ok"] for c in checks), "checks": checks, "claim_checks": [c.to_dict() for c in claim_checks], "summary_length": len(text)}


def render_success_claim_audit(payload: dict[str, Any]) -> str:
    lines = ["# Nova Success Claim Audit", "", f"Status: **{'PASS' if payload.get('ok') else 'REVIEW'}**", "", "## Checks"]
    for check in payload.get("checks", []) or []:
        lines.append(f"- {'PASS' if check.get('ok') else 'REVIEW'} `{check.get('name')}`: {check.get('detail')}")
    lines.extend(["", "## Safer claim wording"])
    for item in payload.get("claim_checks", []) or []:
        lines.append(f"- `{item.get('claim')}`: {item.get('safer_wording')}")
    return "\n".join(lines).strip() + "\n"


def build_regression_bisect_plan(symptom: str = "", versions: str = "") -> dict[str, Any]:
    """Create a safe bisect-style plan for locating a regression across Nova zips."""
    symptom = (symptom or "unknown regression").strip()
    version_items = _split_items(versions) or ["v55.3.124", "v55.3.125", "v55.3.126", "v55.3.127", "v55.3.128", "v55.3.129", "v55.3.130", "current"]
    probes = [
        "Run the smallest reproduction command first, not the whole suite.",
        "Compare last-known-good and first-known-bad release zips in separate folders.",
        "Run syntax + targeted test-impact graph at each midpoint.",
        "Record exact command, pass/fail, stdout/stderr tail and version label.",
        "Do not edit while bisecting; only reproduce and record until the culprit range is isolated.",
    ]
    midpoint_index = len(version_items) // 2
    return {
        "ok": True,
        "symptom": symptom,
        "versions": version_items,
        "first_probe": version_items[midpoint_index],
        "strategy": "binary search over release zips when there are 5+ candidates; linear check only for very small ranges",
        "probes": probes,
        "stop_rule": "Stop when one version transition changes from pass to fail, then inspect only the files changed in that release.",
    }


def render_regression_bisect_plan(payload: dict[str, Any]) -> str:
    lines = ["# Nova Regression Bisect Plan", "", f"Symptom: {payload.get('symptom','')}", f"First probe: **{payload.get('first_probe')}**", f"Strategy: {payload.get('strategy')}", "", "## Probes"]
    lines.extend(f"- {p}" for p in payload.get("probes", []) or [])
    lines.append(f"\nStop rule: {payload.get('stop_rule','')}")
    return "\n".join(lines).strip() + "\n"
