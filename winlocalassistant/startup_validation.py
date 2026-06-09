from __future__ import annotations

import argparse
import json
import logging
import subprocess
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json

LOGGER = logging.getLogger(__name__)

STARTUP_VALIDATION_SCHEMA_VERSION = 1
DEFAULT_STARTUP_TESTS = [
    "tests_smoke.py",
    "tests_format_result.py",
    "tests_request_intent.py",
    "tests_planning_dashboard.py",
]


@dataclass
class StartupCheck:
    name: str
    ok: bool
    command: list[str]
    returncode: int | None
    elapsed_sec: float
    output: str


def _run(root: Path, name: str, command: list[str], timeout: int) -> StartupCheck:
    started = time.time()
    try:
        proc = subprocess.run(
            command,
            cwd=root,
            capture_output=True,
            text=True,
            timeout=max(1, int(timeout)),
            check=False,
        )
        output = ((proc.stdout or "") + (proc.stderr or ""))[-6000:]
        return StartupCheck(name, proc.returncode == 0, command, proc.returncode, round(time.time() - started, 3), output)
    except subprocess.TimeoutExpired as exc:
        output = ((exc.stdout or "") if isinstance(exc.stdout, str) else "") + ((exc.stderr or "") if isinstance(exc.stderr, str) else "")
        return StartupCheck(name, False, command, None, round(time.time() - started, 3), (output + f"\nTIMEOUT after {timeout}s")[-6000:])
    except Exception as exc:
        return StartupCheck(name, False, command, None, round(time.time() - started, 3), repr(exc))


def build_startup_validation(root: str | Path = ".", mode: str = "quick", timeout: int = 90) -> dict[str, Any]:
    """Run the startup gate used by the .bat file.

    This intentionally runs a small, high-signal validation set: compileall plus the
    core smoke/planning tests. Full pytest remains manual because it can be slow.
    """
    root = Path(root).expanduser().resolve()
    mode = (mode or "quick").strip().lower()
    checks: list[StartupCheck] = []
    py = sys.executable
    checks.append(_run(root, "compileall", [py, "-m", "compileall", "-q", "winlocalassistant", "app.py"], timeout=max(45, int(timeout))))
    if mode not in {"compile", "compile-only", "minimal"}:
        existing_tests = [test for test in DEFAULT_STARTUP_TESTS if (root / test).exists()]
        if existing_tests:
            checks.append(_run(root, "smoke_pytest", [py, "-m", "pytest", "-q", *existing_tests], timeout=max(60, int(timeout))))
        else:
            checks.append(StartupCheck("smoke_pytest", False, [py, "-m", "pytest", "-q", *DEFAULT_STARTUP_TESTS], None, 0, "No startup test files found."))
    failed = [asdict(check) for check in checks if not check.ok]
    payload = {
        "schema_version": STARTUP_VALIDATION_SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "mode": mode,
        "ok": not failed,
        "summary": "startup validation passed" if not failed else f"startup validation failed ({len(failed)} check(s))",
        "checks": [asdict(check) for check in checks],
        "failed": failed,
        "manual_full_suite": "python -m pytest -q",
    }
    try:
        out = APP_DIR / "startup_validation_latest.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        atomic_write_json(out, payload)
        payload["json_path"] = str(out)
    except Exception:
        LOGGER.debug("Failed to write startup validation report to %s", out, exc_info=True)
    return payload


def render_startup_validation(payload: dict[str, Any]) -> str:
    lines = ["# Nova Startup Validation", "", str(payload.get("summary") or ""), "", f"Root: `{payload.get('root','')}`", f"Mode: `{payload.get('mode','quick')}`", "", "## Checks"]
    for check in payload.get("checks") or []:
        mark = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {mark} {check.get('name')} — {check.get('elapsed_sec')}s")
        if not check.get("ok") and check.get("output"):
            lines.append("  ```text")
            lines.append(str(check.get("output"))[-1200:])
            lines.append("  ```")
    lines.append("")
    lines.append("## Next")
    if payload.get("ok"):
        lines.append("Startup gate passed. Open the browser UI normally.")
    else:
        lines.append("Fix the failed startup check before release. You can still continue manually for debugging, but Nova should not be treated as release-clean.")
    lines.append(f"Full suite when you have time: `{payload.get('manual_full_suite','python -m pytest -q')}`")
    if payload.get("json_path"):
        lines.append(f"Report: `{payload.get('json_path')}`")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run Nova startup compile/smoke validation.")
    parser.add_argument("--mode", default="quick", choices=["quick", "compile", "compile-only", "minimal"], help="Validation depth")
    parser.add_argument("--root", default=".")
    parser.add_argument("--timeout", type=int, default=90)
    args = parser.parse_args(argv)
    payload = build_startup_validation(args.root, mode=args.mode, timeout=args.timeout)
    print(render_startup_validation(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
