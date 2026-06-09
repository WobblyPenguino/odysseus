from __future__ import annotations

import json
import shlex
import shutil
import subprocess
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text


@dataclass(frozen=True)
class OptionalUpgrade:
    key: str
    title: str
    purpose: str
    check_command: list[str]
    install_command: list[str]
    verify_command: list[str]
    files_expected: tuple[str, ...] = ()
    risk: str = "low"
    download_required: bool = True


CATALOG: dict[str, OptionalUpgrade] = {
    "ruff": OptionalUpgrade(
        key="ruff",
        title="Ruff lint and format gate",
        purpose="Fast Python linting/format checks before release-gate, idle auto-apply, or patch promotion.",
        check_command=["ruff", "--version"],
        install_command=[sys.executable, "-m", "pip", "install", "ruff"],
        verify_command=["ruff", "check", "winlocalassistant", "tests_*.py"],
        files_expected=("pyproject.toml",),
    ),
    "precommit": OptionalUpgrade(
        key="precommit",
        title="pre-commit release hook profile",
        purpose="Runs a repeatable local gate before commits or zip packaging.",
        check_command=["pre-commit", "--version"],
        install_command=[sys.executable, "-m", "pip", "install", "pre-commit"],
        verify_command=["pre-commit", "run", "--all-files"],
        files_expected=(".pre-commit-config.yaml",),
    ),
    "playwright": OptionalUpgrade(
        key="playwright",
        title="Playwright browser GUI smoke testing",
        purpose="Catches microphone button, Send button, layout, and live activity regressions in a real Chromium browser.",
        check_command=["npx", "playwright", "--version"],
        install_command=["npm", "install", "-D", "@playwright/test"],
        verify_command=["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"],
        files_expected=("playwright/nova_gui_smoke.spec.js",),
        risk="medium",
    ),
}

ALIASES = {
    "pre-commit": "precommit",
    "pre_commit": "precommit",
    "gui": "playwright",
    "browser": "playwright",
    "lint": "ruff",
}


def normalise_upgrade_key(key: str) -> str:
    raw = (key or "").strip().lower()
    return ALIASES.get(raw, raw)


def _cmd_exists(cmd: list[str]) -> bool:
    if not cmd:
        return False
    exe = cmd[0]
    return bool(shutil.which(exe) or shutil.which(exe + ".cmd") or shutil.which(exe + ".exe"))


def _run(command: list[str], root: Path, timeout: int = 120) -> dict[str, Any]:
    try:
        cp = subprocess.run(command, cwd=root, text=True, capture_output=True, timeout=timeout, shell=False)
        return {
            "command": command,
            "returncode": cp.returncode,
            "ok": cp.returncode == 0,
            "stdout": cp.stdout[-4000:],
            "stderr": cp.stderr[-4000:],
        }
    except FileNotFoundError as exc:
        return {"command": command, "returncode": 127, "ok": False, "stderr": str(exc), "stdout": ""}
    except subprocess.TimeoutExpired as exc:
        return {"command": command, "returncode": 124, "ok": False, "stderr": f"Timed out after {timeout}s", "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else ""}


def build_optional_upgrade_status(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root)
    items = []
    for item in CATALOG.values():
        files_ok = all((root / rel).exists() for rel in item.files_expected)
        check_available = _cmd_exists(item.check_command)
        status = "ready" if check_available and files_ok else ("tool installed; scaffold missing" if check_available else "optional download")
        items.append({
            **asdict(item),
            "status": status,
            "tool_available": check_available,
            "scaffold_present": files_ok,
            "install_command_text": " ".join(shlex.quote(x) for x in item.install_command),
            "check_command_text": " ".join(shlex.quote(x) for x in item.check_command),
            "verify_command_text": " ".join(shlex.quote(x) for x in item.verify_command),
        })
    return {"ok": True, "root": str(root), "items": items}


def render_optional_upgrade_status(report: dict[str, Any]) -> str:
    lines = ["Nova Optional Upgrade Installer", "", f"Root: {report.get('root')}", ""]
    lines.append("These upgrades may require downloads, so Nova only installs them with an explicit `--confirm`.")
    for item in report.get("items", []):
        flag = "✅" if item.get("status") == "ready" else "⚪"
        lines.append(f"- {flag} {item.get('title')} (`{item.get('key')}`) — {item.get('status')} — risk {item.get('risk')}")
        lines.append(f"  - Purpose: {item.get('purpose')}")
        lines.append(f"  - Install: `{item.get('install_command_text')}`")
        lines.append(f"  - Verify: `{item.get('verify_command_text')}`")
        lines.append(f"  - Command: `/upgrade-install {item.get('key')} --confirm`")
    lines.append("")
    lines.append("Use `/upgrade-install NAME` for a dry run or `/upgrade-install NAME --confirm` to install an allowlisted upgrade.")
    return "\n".join(lines)


def install_optional_upgrade(name: str, root: str | Path = ".", confirm: bool = False, timeout: int = 300) -> dict[str, Any]:
    key = normalise_upgrade_key(name)
    item = CATALOG.get(key)
    root = Path(root)
    if not item:
        return {"ok": False, "summary": f"Unknown optional upgrade: {name}", "available": sorted(CATALOG)}
    dry_run = not confirm
    result: dict[str, Any] = {
        "ok": True,
        "summary": "Dry run only; add --confirm to install." if dry_run else f"Installing optional upgrade: {item.title}",
        "dry_run": dry_run,
        "upgrade": asdict(item),
        "install_command_text": " ".join(shlex.quote(x) for x in item.install_command),
        "verify_command_text": " ".join(shlex.quote(x) for x in item.verify_command),
    }
    if dry_run:
        return result
    install = _run(item.install_command, root, timeout=timeout)
    verify = _run(item.check_command, root, timeout=120)
    result["install"] = install
    result["check"] = verify
    result["ok"] = bool(install.get("ok") and verify.get("ok"))
    result["summary"] = "Optional upgrade installed and command check passed" if result["ok"] else "Optional upgrade install/check failed"
    out_dir = root / "docs"
    out_dir.mkdir(exist_ok=True)
    json_path = out_dir / f"OPTIONAL_UPGRADE_{key.upper()}_LATEST.json"
    md_path = out_dir / f"OPTIONAL_UPGRADE_{key.upper()}_LATEST.md"
    atomic_write_json(json_path, result)
    atomic_write_text(md_path, render_optional_upgrade_install_result(result))
    result["json_path"] = str(json_path)
    result["markdown_path"] = str(md_path)
    return result


def render_optional_upgrade_install_result(result: dict[str, Any]) -> str:
    upgrade = result.get("upgrade") or {}
    lines = ["Nova Optional Upgrade Install", "", f"Upgrade: {upgrade.get('title') or upgrade.get('key')}", f"Status: {'PASS' if result.get('ok') else 'ATTENTION'}", f"Summary: {result.get('summary')}", ""]
    lines.append(f"Install command: `{result.get('install_command_text')}`")
    lines.append(f"Verify command: `{result.get('verify_command_text')}`")
    if result.get("dry_run"):
        lines.append("")
        lines.append("Dry run only. Nothing was installed. Re-run with `--confirm` after reviewing the command.")
        return "\n".join(lines)
    for key in ["install", "check"]:
        step = result.get(key) or {}
        lines.append("")
        lines.append(f"## {key}")
        lines.append(f"Return code: {step.get('returncode')}")
        if step.get("stdout"):
            lines.append("stdout:")
            lines.append("```text")
            lines.append(str(step.get("stdout"))[-2000:])
            lines.append("```")
        if step.get("stderr"):
            lines.append("stderr:")
            lines.append("```text")
            lines.append(str(step.get("stderr"))[-2000:])
            lines.append("```")
    return "\n".join(lines)
