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
from .project_runtime_probe import run_project_runtime_probe


@dataclass
class DashboardItem:
    name: str
    status: str
    detail: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityDashboard:
    version: str
    label: str
    workspace: str
    score: int
    items: list[DashboardItem]
    recommendations: list[str]

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["items"] = [item.to_dict() for item in self.items]
        return data


def build_quality_dashboard(workspace: Path, goal: str = "") -> QualityDashboard:
    """Return a dependency-free health/quality overview for Nova and the current project.

    The dashboard intentionally does not mutate files or call models. It combines
    version, autonomous-memory, iteration-log and project runtime-probe signals so
    users can quickly see what needs attention before running more autonomous work.
    """
    root = Path(workspace)
    items: list[DashboardItem] = []
    recommendations: list[str] = []

    def add(name: str, status: str, detail: str) -> None:
        items.append(DashboardItem(name, status, detail))
        if status in {"warn", "fail"}:
            recommendations.append(f"{name}: {detail}")

    add("version", "ok", f"{__version__} ({VERSION_LABEL})")
    add("workspace", "ok" if root.exists() else "warn", str(root))

    try:
        memory = load_autonomous_failure_memory(AUTONOMOUS_FAILURE_MEMORY_PATH)
        cooldowns = {k: v for k, v in (memory.cooldowns or {}).items() if int(v or 0) > 0}
        if cooldowns:
            add("autonomous memory", "warn", f"{len(cooldowns)} action(s) currently on cooldown; diagnose before repeating.")
        elif memory.recent_failures:
            add("autonomous memory", "ok", f"{len(memory.recent_failures)} recent failure record(s), no active cooldowns.")
        else:
            add("autonomous memory", "ok", "No recent autonomous failures recorded.")
    except Exception as exc:
        add("autonomous memory", "warn", f"Could not read memory: {exc}")

    # Workspace-local project iteration logs are written next to generated projects.
    iteration_log = Path(workspace) / "PROJECT_ITERATION_LOG.jsonl"
    try:
        if iteration_log.exists():
            lines = [ln for ln in iteration_log.read_text(encoding="utf-8", errors="replace").splitlines() if ln.strip()]
            add("project iteration log", "ok", f"{len(lines)} recorded project iteration event(s).")
        else:
            add("project iteration log", "warn", "No project iteration log yet; create/verify a project to populate it.")
    except Exception as exc:
        add("project iteration log", "warn", f"Could not read iteration log: {exc}")

    if root.exists() and root.is_dir():
        try:
            probe = run_project_runtime_probe(goal or root.name, root=root)
            status = "ok" if probe.get("passed") else "warn"
            add("runtime probe", status, f"{probe.get('artifact_type')} interaction score {probe.get('percent')}%.")
            for suggestion in (probe.get("repair_suggestions") or [])[:3]:
                recommendations.append("Runtime probe: " + str(suggestion))
        except Exception as exc:
            add("runtime probe", "warn", f"Probe failed: {exc}")
    else:
        add("runtime probe", "warn", "Workspace is not a readable directory.")

    ok_count = sum(1 for item in items if item.status == "ok")
    score = round(100 * ok_count / max(1, len(items)))
    if not recommendations:
        recommendations.append("No urgent issues found. Continue with a focused verified change or project-quality test.")
    return QualityDashboard(__version__, VERSION_LABEL, str(root), score, items, recommendations[:8])


def render_quality_dashboard_markdown(dashboard: QualityDashboard) -> str:
    lines = [
        "# Nova Quality Dashboard",
        "",
        f"Version: {dashboard.version}",
        f"Label: {dashboard.label}",
        f"Workspace: `{dashboard.workspace}`",
        f"Overall readiness: {dashboard.score}%",
        "",
        "## Signals",
    ]
    for item in dashboard.items:
        icon = "PASS" if item.status == "ok" else ("FAIL" if item.status == "fail" else "WARN")
        lines.append(f"- {icon}: **{item.name}** — {item.detail}")
    lines += ["", "## Recommended next actions"]
    for rec in dashboard.recommendations:
        lines.append(f"- {rec}")
    return "\n".join(lines)


def write_quality_dashboard_report(workspace: Path, goal: str = "") -> tuple[Path, Path, QualityDashboard]:
    dash = build_quality_dashboard(workspace, goal)
    out_dir = APP_DIR / "quality_dashboards"
    out_dir.mkdir(parents=True, exist_ok=True)
    # Use millisecond time plus a short random suffix so rapid repeated dashboard
    # requests never overwrite each other within the same second.
    safe = f"{int(time.time() * 1000)}_{uuid.uuid4().hex[:8]}"
    md = out_dir / f"quality_dashboard_{safe}.md"
    js = out_dir / f"quality_dashboard_{safe}.json"
    atomic_write_text(md, render_quality_dashboard_markdown(dash))
    atomic_write_json(js, dash.to_dict(), ensure_ascii=True)
    return md, js, dash
