from __future__ import annotations

import json
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


@dataclass
class IntegrationCandidate:
    name: str
    category: str
    available: bool
    priority: int
    status: str
    value: str
    next_step: str
    command: str = ""
    risk: str = "low"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _run(args: list[str], timeout: int = 8, cwd: Path | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout, cwd=str(cwd) if cwd else None)
        return {
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-3000:],
            "stderr": (proc.stderr or "")[-3000:],
            "command": args,
        }
    except Exception as exc:
        return {"ok": False, "error": repr(exc), "command": args}


def _exe(name: str) -> bool:
    return bool(shutil.which(name))


def _python_module(name: str) -> bool:
    return _run([sys.executable, "-c", f"import {name}"], timeout=10).get("ok", False)


def _git_repo(root: Path) -> bool:
    return bool(_run(["git", "rev-parse", "--is-inside-work-tree"], cwd=root, timeout=8).get("ok")) if _exe("git") else False


def build_integration_radar(root: Path, goal: str = "") -> dict[str, Any]:
    root = Path(root or ".").resolve()
    candidates: list[IntegrationCandidate] = []
    git_available = _exe("git")
    in_git = _git_repo(root)
    docker_available = _exe("docker")
    node_available = _exe("node")
    pytest_available = _python_module("pytest")
    ruff_available = _exe("ruff") or _python_module("ruff")
    mypy_available = _exe("mypy") or _python_module("mypy")
    semgrep_available = _exe("semgrep") or _python_module("semgrep")
    playwright_available = _exe("npx") or _python_module("playwright")
    precommit_available = _exe("pre-commit") or _python_module("pre_commit")
    uv_available = _exe("uv")
    rg_available = _exe("rg")

    candidates.append(IntegrationCandidate(
        "Git safety/worktree backend", "source-control", git_available and in_git, 100,
        "ready" if git_available and in_git else ("git available but current folder is not a repo" if git_available else "git missing"),
        "Make every autonomous/promotion change reviewable, reversible and branch/worktree isolated.",
        "Add /git-guard and optional git worktree validation before live promotion.",
        "git status --short", "low",
    ))
    candidates.append(IntegrationCandidate(
        "Pre-commit release hooks", "validation", precommit_available, 90,
        "ready" if precommit_available else "optional tool missing",
        "Run a consistent local gate before promotion: syntax, formatting, static checks and tests.",
        "Add a .pre-commit-config.yaml template and /precommit-check command.",
        "pre-commit run --all-files", "low",
    ))
    candidates.append(IntegrationCandidate(
        "Ruff lint/format", "validation", ruff_available, 88,
        "ready" if ruff_available else "optional tool missing",
        "Fast Python linting catches unused imports, obvious bugs and style drift before Docker tests.",
        "Add optional /ruff-check and include it in release-gate when available.",
        "ruff check winlocalassistant tests_*.py", "low",
    ))
    candidates.append(IntegrationCandidate(
        "Mypy type checking", "validation", mypy_available, 72,
        "ready" if mypy_available else "optional tool missing",
        "Find interface drift between modules as Nova grows.",
        "Start with a relaxed mypy profile for new modules only, then expand.",
        "mypy winlocalassistant", "medium",
    ))
    candidates.append(IntegrationCandidate(
        "Semgrep security/static rules", "security", semgrep_available, 70,
        "ready" if semgrep_available else "optional tool missing",
        "Find risky subprocess, unsafe path handling, injection-prone strings and weak validation gates.",
        "Add optional semgrep scan profile to /release-gate.",
        "semgrep scan --config auto", "medium",
    ))
    candidates.append(IntegrationCandidate(
        "Playwright browser smoke tests", "gui-testing", playwright_available and node_available, 86,
        "ready" if playwright_available and node_available else "node/npx/playwright not fully available",
        "Catch Send-button and JavaScript UI failures through real browser interaction, not just static JS parsing.",
        "Add a browser smoke test for sending chat, toggling tabs and Docker panel buttons.",
        "npx playwright test", "medium",
    ))
    candidates.append(IntegrationCandidate(
        "Defensive security status", "security", True, 74,
        "integrated; read-only local inventory available",
        "Inventory Windows Defender/AVG-style tooling, firewall state, listening ports and Nova/Docker lab context before security work.",
        "Run /security-status before lab/security tasks and include the report in release checklist context.",
        "/security-status", "low",
    ))

    candidates.append(IntegrationCandidate(
        "Docker validation backend", "sandbox-validation", docker_available, 95,
        "integrated; docker CLI available" if docker_available else "integrated; docker CLI missing/offline possible",
        "Validate copied workspaces and proposed patches without touching the live tree.",
        "Keep Docker as the main patch simulation backend and add profile history/GUI review.",
        "/docker-status", "low",
    ))
    candidates.append(IntegrationCandidate(
        "uv environment manager", "environment", uv_available, 63,
        "ready" if uv_available else "optional tool missing",
        "Faster, reproducible Python environment setup and lockfile-based dependency installs.",
        "Add optional /env-doctor checks for uv and requirements drift.",
        "uv sync", "low",
    ))
    candidates.append(IntegrationCandidate(
        "ripgrep code search", "developer-experience", rg_available, 62,
        "ready" if rg_available else "optional tool missing",
        "Faster codebase scans and bug triage than recursive Python text scans.",
        "Use rg automatically in codebase scans when present, fallback to Python otherwise.",
        "rg TODO winlocalassistant tests_*.py", "low",
    ))

    ready = [c for c in candidates if c.available]
    missing = [c for c in candidates if not c.available]
    ranked = sorted(candidates, key=lambda c: c.priority, reverse=True)
    next_best = [c for c in ranked if c.available][:5] + [c for c in ranked if not c.available][:3]
    payload = {
        "ok": True,
        "summary": "Integration radar completed",
        "goal": goal or "improve Nova integration ecosystem",
        "root": str(root),
        "ready_count": len(ready),
        "missing_count": len(missing),
        "candidates": [c.to_dict() for c in ranked],
        "next_best": [c.to_dict() for c in next_best],
        "recommendation": _recommendation(ranked),
    }
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    atomic_write_json(docs / "INTEGRATION_RADAR_LATEST.json", payload, ensure_ascii=True)
    atomic_write_text(docs / "INTEGRATION_RADAR_LATEST.md", render_integration_radar_markdown(payload))
    return payload


def _recommendation(candidates: list[IntegrationCandidate]) -> str:
    if any(c.name.startswith("Git safety") and c.available for c in candidates):
        return "Highest value next integration: Git safety/worktree backend, because it makes all future autonomous changes more reviewable and reversible."
    if any(c.name.startswith("Playwright") and c.available for c in candidates):
        return "Highest value next integration: Playwright browser smoke tests, because Nova has had real GUI regressions that static tests only partly cover."
    return "Highest value next integration: keep Docker validation as the baseline, then add Git and browser smoke testing when those tools are available."


def render_integration_radar_markdown(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Integration Radar",
        "",
        f"Goal: **{payload.get('goal','')}**",
        f"Ready integrations: **{payload.get('ready_count', 0)}**",
        f"Missing/optional integrations: **{payload.get('missing_count', 0)}**",
        "",
        f"Recommendation: {payload.get('recommendation','')}",
        "",
        "## Next best integrations",
    ]
    for item in payload.get("next_best", []):
        status = "ready" if item.get("available") else "optional/missing"
        lines.append(f"- **{item.get('name')}** ({status}, priority {item.get('priority')}): {item.get('value')}")
        lines.append(f"  - Next: {item.get('next_step')}")
        if item.get("command"):
            lines.append(f"  - Command: `{item.get('command')}`")
    lines += ["", "## Full candidate list"]
    for item in payload.get("candidates", []):
        icon = "✅" if item.get("available") else "⚪"
        lines.append(f"{icon} **{item.get('name')}** — {item.get('status')} — risk `{item.get('risk')}`")
    return "\n".join(lines)
