from __future__ import annotations

import json
import time
import uuid
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from . import __version__, VERSION_LABEL
from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text
from .autonomous_failure import AUTONOMOUS_FAILURE_MEMORY_PATH, load_autonomous_failure_memory
from .autonomous_journal import latest_run_journal
from .interaction_learning import load_interaction_lessons


@dataclass
class CapabilitySignal:
    name: str
    status: str
    evidence: str
    limitation: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class SelfAwarenessReport:
    version: str
    label: str
    workspace: str
    identity: str
    operating_mode: str
    capabilities: list[CapabilitySignal]
    safety_boundaries: list[str]
    known_limitations: list[str]
    recent_state: list[str]
    recommended_next_actions: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["capabilities"] = [cap.to_dict() for cap in self.capabilities]
        return data


CAPABILITY_FILES = {
    "plain-English command router": "core.py",
    "intent planning": "intent_planning.py",
    "task decomposition": "task_decomposition.py",
    "request intent guards": "request_intent.py",
    "creation intent": "creation_intent.py",
    "generic game design": "game_design.py",
    "project acceptance contracts": "project_acceptance.py",
    "runtime interaction probes": "project_runtime_probe.py",
    "project iteration logs": "project_iteration.py",
    "autonomous failure memory": "autonomous_failure.py",
    "autonomous sequence planner": "autonomous_sequence.py",
    "autonomous explainability": "autonomous_explain.py",
    "autonomous journal": "autonomous_journal.py",
    "action watcher": "action_watcher.py",
    "tool catalogue": "tool_catalog.py",
    "interaction learning": "interaction_learning.py",
    "planning dashboard": "planning_dashboard.py",
    "quality dashboard": "quality_dashboard.py",
    "surgical fallback": "surgical_fallback.py",
    "iterative coding loop": "iterative_coding.py",
    "manifest-first video planning": "nova_video.py",
    "docker validation backend": "docker_manager.py",
    "sandbox permission state": "sandbox_permissions.py",
    "cohesion engine": "cohesion_engine.py",
}


def _exists(module_dir: Path, filename: str) -> bool:
    return (module_dir / filename).exists()


def build_self_awareness_report(workspace: Path | str = ".", goal: str = "") -> SelfAwarenessReport:
    """Build a local, dependency-free report of what Nova can do and where it is limited.

    This is intentionally read-only. It does not call a model, run shell commands,
    mutate project files, or infer success without evidence from local files/state.
    """
    root = Path(workspace)
    module_dir = Path(__file__).resolve().parent
    capabilities: list[CapabilitySignal] = []
    recommendations: list[str] = []

    for name, filename in CAPABILITY_FILES.items():
        if _exists(module_dir, filename):
            capabilities.append(CapabilitySignal(name, "present", f"winlocalassistant/{filename}"))
        else:
            capabilities.append(CapabilitySignal(name, "missing", f"winlocalassistant/{filename} not found", "Feature may have regressed or is not installed."))
            recommendations.append(f"Restore or implement {name} ({filename}).")

    recent_state: list[str] = []
    try:
        memory = load_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH)
        active_cooldowns = {k: v for k, v in (memory.cooldowns or {}).items() if int(v or 0) > 0}
        if active_cooldowns:
            recent_state.append(f"Autonomous memory has {len(active_cooldowns)} active cooldown(s); repeated actions should diagnose before retrying.")
            recommendations.append("Review /autonomous-memory before running another similar autonomous action.")
        elif memory.recent_failures:
            recent_state.append(f"Autonomous memory has {len(memory.recent_failures)} recent failure record(s), with no active cooldowns.")
        else:
            recent_state.append("Autonomous memory has no recent failures recorded.")
    except Exception as exc:
        recent_state.append(f"Autonomous memory could not be read: {exc}")
        recommendations.append("Repair autonomous failure memory if /autonomous-memory also fails.")

    try:
        journal_path, journal = latest_run_journal()
        if journal_path and journal:
            recent_state.append(f"Latest autonomous journal: {journal_path.name}, status={journal.get('status','unknown')}, failed_steps={journal.get('failed_steps',0)}.")
            if int(journal.get("failed_steps") or 0) > 0:
                recommendations.append("Inspect /autonomous-journal and generate a repair proposal before repeating the same sequence.")
        else:
            recent_state.append("No autonomous sequence journal has been written yet.")
    except Exception as exc:
        recent_state.append(f"Autonomous journal could not be read: {exc}")

    try:
        lessons = load_interaction_lessons()
        recent_state.append(f"Interaction learning has {len(lessons)} local lesson(s).")
    except Exception as exc:
        recent_state.append(f"Interaction lessons could not be read: {exc}")

    if not root.exists():
        recommendations.append("Set a valid workspace before running project-quality or autonomous project tasks.")
    if goal:
        recommendations.append(f"For this goal, preview /planning-dashboard {goal} and /autonomous-plan {goal} before running autonomous mode.")
    if not recommendations:
        recommendations.append("Use /quality-dashboard, /planning-dashboard GOAL, then a focused verified command or autonomous plan.")

    safety_boundaries = [
        "Do not call /self-improve automatically.",
        "Use action watcher decisions before risky tool/command execution.",
        "Keep auto-apply explicit, low-risk, backed up, verified, reported and rollback-capable.",
        "Use failure memory/cooldowns to avoid repeating failed autonomous actions.",
        "Do not claim project creation success unless acceptance/quality checks support it.",
    ]
    known_limitations = [
        "Generated web apps are still checked with dependency-free probes, not full Playwright/Selenium browser automation.",
        "Self-awareness is evidence-based from local files/state; it is not hidden model introspection.",
        "Local model repair proposals are report-first and should remain gated by watcher/verification before applying.",
    ]
    return SelfAwarenessReport(
        version=__version__,
        label=VERSION_LABEL,
        workspace=str(root),
        identity="Nova is a local Windows-first coding, project-generation and autonomous assistance system.",
        operating_mode="evidence-based self-awareness: local modules, tests, memories, journals, watcher and dashboards",
        capabilities=capabilities,
        safety_boundaries=safety_boundaries,
        known_limitations=known_limitations,
        recent_state=recent_state,
        recommended_next_actions=recommendations[:8],
    )


def render_self_awareness_markdown(report: SelfAwarenessReport) -> str:
    lines = [
        "# Nova Self-Awareness Report",
        "",
        f"Version: {report.version}",
        f"Label: {report.label}",
        f"Workspace: `{report.workspace}`",
        "",
        "## Identity",
        report.identity,
        "",
        "## Operating Mode",
        report.operating_mode,
        "",
        "## Capability Inventory",
    ]
    for cap in report.capabilities:
        marker = "PASS" if cap.status == "present" else "WARN"
        line = f"- {marker}: **{cap.name}** — {cap.evidence}"
        if cap.limitation:
            line += f" ({cap.limitation})"
        lines.append(line)
    lines += ["", "## Recent State"]
    lines.extend(f"- {item}" for item in report.recent_state)
    lines += ["", "## Safety Boundaries"]
    lines.extend(f"- {item}" for item in report.safety_boundaries)
    lines += ["", "## Known Limitations"]
    lines.extend(f"- {item}" for item in report.known_limitations)
    lines += ["", "## Recommended Next Actions"]
    lines.extend(f"- {item}" for item in report.recommended_next_actions)
    return "\n".join(lines)


def write_self_awareness_report(workspace: Path | str = ".", goal: str = "") -> tuple[Path, Path, SelfAwarenessReport]:
    report = build_self_awareness_report(workspace, goal)
    out_dir = APP_DIR / "self_awareness"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Include millisecond time plus a short random suffix so rapid repeated
    # report requests never overwrite each other within the same second.
    stamp = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    md = out_dir / f"self_awareness_{stamp}.md"
    js = out_dir / f"self_awareness_{stamp}.json"
    atomic_write_text(md, render_self_awareness_markdown(report))
    atomic_write_json(js, report.to_dict(), ensure_ascii=True)
    return md, js, report
