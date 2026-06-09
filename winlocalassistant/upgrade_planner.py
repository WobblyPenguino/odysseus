from __future__ import annotations

import importlib.util
import shutil
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class UpgradeCandidate:
    name: str
    status: str
    priority: int
    benefit: str
    download_required: bool
    safe_to_install_automatically: bool
    check: str
    install_hint: str
    command: str
    risk: str = "low"


def _has_module(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def _has_cmd(name: str) -> bool:
    if shutil.which(name):
        return True
    if shutil.which(name + ".cmd"):
        return True
    if shutil.which(name + ".exe"):
        return True
    return False


def build_upgrade_radar(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    candidates: list[UpgradeCandidate] = []

    candidates.append(UpgradeCandidate(
        name="Voice device selector and microphone preflight",
        status="implemented",
        priority=98,
        benefit="Lets Bluetooth/Sony headset users select a browser-visible input device instead of relying on the Windows default mic.",
        download_required=False,
        safe_to_install_automatically=False,
        check="Browser getUserMedia + enumerateDevices",
        install_hint="No install required; use Chrome/Edge and Windows Settings > System > Sound > Input.",
        command="/mic-test",
        risk="low",
    ))
    candidates.append(UpgradeCandidate(
        name="Allowlisted optional upgrade installer",
        status="implemented",
        priority=96,
        benefit="Lets Nova install reviewed optional dev tools such as Ruff, pre-commit or Playwright only after an explicit --confirm, then records install/check reports.",
        download_required=False,
        safe_to_install_automatically=False,
        check="/upgrade-install ruff --confirm after reviewing the dry-run",
        install_hint="No automatic install; use /optional-upgrades to review commands first.",
        command="/optional-upgrades",
        risk="medium",
    ))
    candidates.append(UpgradeCandidate(
        name="Playwright GUI smoke tests",
        status="ready" if (root / "playwright" / "nova_gui_smoke.spec.js").exists() else "missing scaffold",
        priority=92,
        benefit="Catches send-button, microphone button, live activity, and layout regressions in a real browser.",
        download_required=not _has_cmd("npx"),
        safe_to_install_automatically=False,
        check="npx playwright test playwright/nova_gui_smoke.spec.js",
        install_hint="npm install -D @playwright/test && npx playwright install chromium",
        command="/playwright-smoke-help",
        risk="medium",
    ))
    candidates.append(UpgradeCandidate(
        name="Ruff lint/format gate",
        status="ready" if _has_cmd("ruff") else "optional download",
        priority=88,
        benefit="Fast linting catches unused imports, shadowed variables, broad exceptions, syntax drift and formatting regressions before release.",
        download_required=not _has_cmd("ruff"),
        safe_to_install_automatically=True,
        check="ruff check winlocalassistant tests_*.py",
        install_hint="py -m pip install ruff",
        command="/upgrade-radar",
        risk="low",
    ))
    candidates.append(UpgradeCandidate(
        name="Git worktree/branch guard",
        status="ready" if _has_cmd("git") and (root / ".git").exists() else ("git available; repo not initialised" if _has_cmd("git") else "optional download"),
        priority=86,
        benefit="Makes autonomous changes reversible and reviewable instead of patching the live tree blind.",
        download_required=not _has_cmd("git"),
        safe_to_install_automatically=False,
        check="git status --short",
        install_hint="Install Git for Windows, then initialise or clone Nova as a git repository.",
        command="git status --short",
        risk="low",
    ))
    candidates.append(UpgradeCandidate(
        name="Pre-commit release hook profile",
        status="ready" if _has_cmd("pre-commit") else "optional download",
        priority=82,
        benefit="Runs compile, tests and lint checks consistently before a zip is shared.",
        download_required=not _has_cmd("pre-commit"),
        safe_to_install_automatically=True,
        check="pre-commit run --all-files",
        install_hint="py -m pip install pre-commit",
        command="/release-gate final validation",
        risk="low",
    ))
    candidates.append(UpgradeCandidate(
        name="Docker copied-workspace validation",
        status="ready" if _has_cmd("docker") else "optional download",
        priority=78,
        benefit="Tests proposed patches in a copied workspace so failed validation cannot corrupt the live project.",
        download_required=not _has_cmd("docker"),
        safe_to_install_automatically=False,
        check="docker --version && /docker-validate quick",
        install_hint="Install Docker Desktop and start it before running Nova sandbox validation.",
        command="/docker-status",
        risk="medium",
    ))
    candidates.append(UpgradeCandidate(
        name="Optional local image backend",
        status="ready" if _has_module("diffusers") and _has_module("torch") else "optional heavy download",
        priority=54,
        benefit="Could enable local image experiments, but it is heavy and should stay optional on GTX 1650-class machines.",
        download_required=not (_has_module("diffusers") and _has_module("torch")),
        safe_to_install_automatically=False,
        check="python -c \"import torch, diffusers; print('ok')\"",
        install_hint="py -m pip install diffusers accelerate torch --index-url https://download.pytorch.org/whl/cu121  # heavy; review first",
        command="/image-status",
        risk="high",
    ))

    recommended = sorted(candidates, key=lambda c: c.priority, reverse=True)
    return {
        "root": str(root),
        "ok": True,
        "summary": "Upgrade radar completed",
        "recommended_next": recommended[0].name if recommended else "none",
        "candidates": [asdict(c) for c in recommended],
        "safe_optional_pip_installs": [c.install_hint for c in recommended if c.safe_to_install_automatically and c.download_required],
    }


def render_upgrade_radar(report: dict[str, Any]) -> str:
    lines = ["Nova Significant Upgrade Radar", "", f"Root: {report.get('root')}", f"Recommendation: {report.get('recommended_next')}", ""]
    lines.append("Best next upgrades")
    for c in report.get("candidates", [])[:8]:
        flag = "✅" if c.get("status") in {"ready", "implemented"} else "⚪"
        dl = "download required" if c.get("download_required") else "no download"
        lines.append(f"- {flag} {c.get('name')} — {c.get('status')} — priority {c.get('priority')} — {dl}")
        lines.append(f"  - Benefit: {c.get('benefit')}")
        lines.append(f"  - Check: `{c.get('check')}`")
        lines.append(f"  - Install/setup: `{c.get('install_hint')}`")
        lines.append(f"  - Nova command: `{c.get('command')}`")
    safe = report.get("safe_optional_pip_installs") or []
    if safe:
        lines.append("")
        lines.append("Safe optional Python downloads Nova may suggest after confirmation")
        for item in safe:
            lines.append(f"- `{item}`")
    lines.append("")
    lines.append("Implemented in this build: voice device selection, mic preflight, upgrade radar, allowlisted optional upgrade installer, and release-safe version alignment.")
    return "\n".join(lines)
