from __future__ import annotations

import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .architecture_audit import run_architecture_audit
from .config import APP_DIR
from .docker_manager import docker_validation_history
from .safe_io import atomic_write_json, atomic_write_text
from .self_awareness import build_self_awareness_report


VALIDATION_LADDER: list[dict[str, str]] = [
    {
        "name": "syntax",
        "purpose": "Catch import/syntax failures before any model or autonomous step continues.",
        "command": "python -m compileall -q winlocalassistant tests_*.py app.py",
    },
    {
        "name": "command_contracts",
        "purpose": "Verify user-facing slash commands still route and return bounded text instead of exceptions.",
        "command": "/command-verify",
    },
    {
        "name": "architecture",
        "purpose": "Check module continuity, version text, docs, command routes and release hygiene.",
        "command": "/architecture-audit",
    },
    {
        "name": "self_awareness",
        "purpose": "Check Nova's evidence-based self-map, recent memories, journals and limitations.",
        "command": "/self-awareness",
    },
    {
        "name": "quality",
        "purpose": "Run code repair/review/quality gates before packaging.",
        "command": "/code-repair-audit && /code-review && /code-quality-gate",
    },
    {
        "name": "docker_copy_validation",
        "purpose": "Validate a copied workspace in Docker without touching the live project.",
        "command": "/docker-validate quick",
    },
    {
        "name": "docker_patch_validation",
        "purpose": "Apply a proposed patch only inside a Docker copy before promoting it.",
        "command": "/docker-validate-patch PATCH.diff => quick",
    },
    {
        "name": "autonomous_gate",
        "purpose": "Allow autonomous mode to act only after health, loop-guard and Docker validation gates pass.",
        "command": "/autonomous once --diagnostic improve reliability",
    },
]


ITERATIVE_LOOP: list[dict[str, str]] = [
    {"phase": "observe", "output": "current state, recent failures, user goal, workspace facts"},
    {"phase": "orient", "output": "cohesion report, architecture/self-awareness comparison, validation ladder"},
    {"phase": "propose", "output": "minimal patch or explicit improvement proposal"},
    {"phase": "simulate", "output": "apply/check patch in copied workspace only"},
    {"phase": "validate", "output": "syntax, targeted tests, Docker validation and command contracts"},
    {"phase": "promote", "output": "apply only verified patch to live tree, or reject with reason"},
    {"phase": "reflect", "output": "journal, lesson, next smallest action"},
]


@dataclass
class CohesionRisk:
    severity: str
    area: str
    issue: str
    recommendation: str


@dataclass
class CohesionReport:
    version: str
    label: str
    generated_at: str
    workspace: str
    goal: str
    score: int
    summary: str
    layers: dict[str, Any] = field(default_factory=dict)
    risks: list[CohesionRisk] = field(default_factory=list)
    validation_ladder: list[dict[str, str]] = field(default_factory=list)
    iterative_loop: list[dict[str, str]] = field(default_factory=list)
    next_actions: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["risks"] = [asdict(r) for r in self.risks]
        return data


def _score_from_risks(risks: list[CohesionRisk]) -> int:
    score = 100
    for risk in risks:
        sev = risk.severity.lower()
        if sev == "high":
            score -= 18
        elif sev == "medium":
            score -= 10
        else:
            score -= 4
    return max(0, min(100, score))


def build_cohesion_report(workspace: Path | str = ".", goal: str = "") -> CohesionReport:
    root = Path(workspace).expanduser()
    if not root.is_absolute():
        root = (Path.cwd() / root).resolve()
    risks: list[CohesionRisk] = []
    self_report = build_self_awareness_report(root, goal)
    arch = run_architecture_audit(root)

    capability_missing = [cap for cap in self_report.capabilities if cap.status != "present"]
    if capability_missing:
        risks.append(CohesionRisk(
            "high", "self_awareness", "Capability inventory has missing modules: " + ", ".join(c.name for c in capability_missing[:8]),
            "Restore missing capability modules or update the capability map with tested replacements.",
        ))

    high_arch = [f for f in arch.findings if f.severity.lower() == "high"]
    med_arch = [f for f in arch.findings if f.severity.lower() == "medium"]
    for finding in high_arch[:5]:
        risks.append(CohesionRisk("high", "architecture", finding.title, finding.recommendation))
    for finding in med_arch[:5]:
        risks.append(CohesionRisk("medium", "architecture", finding.title, finding.recommendation))

    try:
        history = docker_validation_history(None, limit=8)  # type: ignore[arg-type]
        runs = history.get("runs", []) if isinstance(history, dict) else []
    except Exception:
        runs = []
    failed_runs = [r for r in runs if not r.get("ok")]
    if failed_runs:
        risks.append(CohesionRisk(
            "medium", "validation", f"Recent Docker validation has {len(failed_runs)} failed run(s).",
            "Inspect /docker-history and fix the most recent failure before autonomous promotion.",
        ))
    if not runs:
        risks.append(CohesionRisk(
            "low", "validation", "No Docker validation history is available yet.",
            "Run /docker-validate quick once Docker is ready so autonomous mode has recent validation evidence.",
        ))

    core_path = root / "winlocalassistant" / "core.py"
    try:
        core_lines = len(core_path.read_text(encoding="utf-8", errors="replace").splitlines()) if core_path.exists() else 0
    except Exception:
        core_lines = 0
    if core_lines > 3500:
        risks.append(CohesionRisk(
            "low", "architecture", f"core.py remains large ({core_lines} lines).",
            "Continue extracting narrow helpers with regression tests rather than broad rewrites.",
        ))

    score = _score_from_risks(risks)
    layers = {
        "identity": {"version": self_report.version, "label": self_report.label, "mode": self_report.operating_mode},
        "capabilities": {"present": len([c for c in self_report.capabilities if c.status == "present"]), "total": len(self_report.capabilities)},
        "architecture": {"checks": len(arch.checks), "findings": len(arch.findings), "high_findings": len(high_arch), "medium_findings": len(med_arch)},
        "validation": {"recent_docker_runs": len(runs), "recent_docker_failures": len(failed_runs)},
        "iteration": {"loop_phases": [x["phase"] for x in ITERATIVE_LOOP]},
    }
    next_actions = [
        "Run /cohesion-report after major changes and before packaging.",
        "Use /validation-ladder to choose the smallest reliable verification set for the current risk level.",
        "Use /docker-validate-patch PATCH.diff => quick before applying self-improvement patches to the live tree.",
        "Use /autonomous once --diagnostic GOAL when you want a no-mutation investigation first.",
    ]
    for risk in risks[:4]:
        next_actions.append(risk.recommendation)
    summary = "healthy" if score >= 85 else "needs attention" if score >= 65 else "fragile"
    return CohesionReport(
        version=__version__,
        label=VERSION_LABEL,
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        workspace=str(root),
        goal=goal,
        score=score,
        summary=f"Cohesion score {score}/100: {summary}.",
        layers=layers,
        risks=risks,
        validation_ladder=VALIDATION_LADDER,
        iterative_loop=ITERATIVE_LOOP,
        next_actions=list(dict.fromkeys(next_actions))[:10],
    )


def render_cohesion_report_markdown(report: CohesionReport) -> str:
    lines = [
        "# Nova Cohesion Report",
        "",
        f"Version: **{report.version}** ({report.label})",
        f"Generated: {report.generated_at}",
        f"Workspace: `{report.workspace}`",
        f"Goal: {report.goal or '(general reliability)'}",
        f"Score: **{report.score}/100**",
        "",
        report.summary,
        "",
        "## System Layers",
    ]
    for key, value in report.layers.items():
        lines.append(f"- **{key}**: `{value}`")
    lines += ["", "## Risks"]
    if report.risks:
        for risk in report.risks:
            lines.append(f"- **{risk.severity.upper()} / {risk.area}**: {risk.issue}")
            lines.append(f"  - Fix: {risk.recommendation}")
    else:
        lines.append("- No major cohesion risks detected by the local checks.")
    lines += ["", "## Validation Ladder"]
    for i, item in enumerate(report.validation_ladder, 1):
        lines.append(f"{i}. **{item['name']}** — {item['purpose']}")
        lines.append(f"   - `{item['command']}`")
    lines += ["", "## Iterative Development Loop"]
    for i, item in enumerate(report.iterative_loop, 1):
        lines.append(f"{i}. **{item['phase']}** → {item['output']}")
    lines += ["", "## Next Actions"]
    lines.extend(f"- {x}" for x in report.next_actions)
    return "\n".join(lines)


def render_validation_ladder_markdown(goal: str = "") -> str:
    lines = ["# Nova Validation Ladder", ""]
    if goal:
        lines.append(f"Goal: {goal}")
        lines.append("")
    for i, item in enumerate(VALIDATION_LADDER, 1):
        lines.append(f"{i}. **{item['name']}**")
        lines.append(f"   - Purpose: {item['purpose']}")
        lines.append(f"   - Command: `{item['command']}`")
    lines += [
        "",
        "Use the earliest failing rung as the next repair target. Do not move to broader/autonomous changes until the lower rung passes.",
    ]
    return "\n".join(lines)


def render_iterative_development_markdown(goal: str = "") -> str:
    lines = ["# Nova Iterative Development Protocol", ""]
    if goal:
        lines.append(f"Goal: {goal}")
        lines.append("")
    lines += [
        "This protocol is designed for self-improvement work without guessing or silently changing live files.",
        "",
        "## Loop",
    ]
    for i, item in enumerate(ITERATIVE_LOOP, 1):
        lines.append(f"{i}. **{item['phase']}** — output: {item['output']}")
    lines += [
        "",
        "## Recommended command sequence",
        "```text",
        "/cohesion-report " + (goal or "improve Nova reliability"),
        "/validation-ladder " + (goal or "improve Nova reliability"),
        "/docker-validate quick",
        "/autonomous once --diagnostic " + (goal or "improve Nova reliability"),
        "# after reviewing a patch:",
        "/docker-validate-patch PATCH.diff => quick",
        "```",
    ]
    return "\n".join(lines)


def write_cohesion_report(workspace: Path | str = ".", goal: str = "") -> tuple[Path, Path, CohesionReport]:
    report = build_cohesion_report(workspace, goal)
    out_dir = APP_DIR / "cohesion_reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    md = out_dir / f"cohesion_report_{stamp}.md"
    js = out_dir / f"cohesion_report_{stamp}.json"
    atomic_write_text(md, render_cohesion_report_markdown(report))
    atomic_write_json(js, report.to_dict(), ensure_ascii=True, indent=2)
    return md, js, report
