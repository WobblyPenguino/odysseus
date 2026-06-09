from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

PYTHON_PACKAGES = [
    {"name": "pytest", "import": "pytest", "purpose": "run Nova regression and release tests", "required": True},
    {"name": "pillow", "import": "PIL", "purpose": "image utilities and future real image outputs", "required": False},
]
OPTIONAL_HEAVY_PACKAGES = [
    {"name": "diffusers", "import": "diffusers", "purpose": "optional local Diffusers image backend", "required": False},
    {"name": "torch", "import": "torch", "purpose": "optional local Diffusers image backend", "required": False},
    {"name": "accelerate", "import": "accelerate", "purpose": "optional local Diffusers acceleration", "required": False},
]
CLI_TOOLS = [
    {"name": "git", "purpose": "patch validation/promotion and project diff review", "required": False},
    {"name": "node", "purpose": "web UI JavaScript parsing and generated JS checks", "required": False},
    {"name": "npm", "purpose": "Playwright browser smoke tests", "required": False},
    {"name": "docker", "purpose": "Docker sandbox and copied-workspace validation", "required": False},
    {"name": "ollama", "purpose": "local LLM chat and code generation", "required": False},
]


def _has_py(import_name: str) -> bool:
    return importlib.util.find_spec(import_name) is not None


def _cmd_version(name: str) -> tuple[bool, str]:
    executable = _resolve_cli_executable(name)
    if not executable:
        return False, "not on PATH"
    try:
        proc = subprocess.run([executable, "--version"], text=True, capture_output=True, timeout=8)
        out = (proc.stdout or proc.stderr or "").strip().splitlines()
        return proc.returncode == 0, out[0] if out else f"{name} found"
    except Exception as exc:
        return True, f"found but version check failed: {exc!r}"


def _resolve_cli_executable(name: str) -> str:
    """Return a directly executable CLI path on Windows.

    Some tools, notably npm, may appear on PATH as a command shim without an
    executable extension before the `.cmd` wrapper. PowerShell can launch that,
    but `subprocess.run([name, ...])` cannot. Prefer launchable Windows shims
    so the dependency report does not show a false warning.
    """
    if os.name == "nt":
        for suffix in (".cmd", ".exe", ".bat", ""):
            found = shutil.which(name + suffix)
            if found:
                return found
    return shutil.which(name) or ""


def build_dependency_report(include_heavy: bool = False) -> dict[str, Any]:
    py_items = PYTHON_PACKAGES + (OPTIONAL_HEAVY_PACKAGES if include_heavy else [])
    packages = []
    for item in py_items:
        ok = _has_py(item["import"])
        packages.append({**item, "ok": ok, "install": item["name"]})
    cli = []
    for item in CLI_TOOLS:
        ok, detail = _cmd_version(item["name"])
        cli.append({**item, "ok": ok, "detail": detail})
    missing_required = [p for p in packages if p.get("required") and not p.get("ok")]
    missing_optional = [p for p in packages if not p.get("required") and not p.get("ok")]
    return {
        "ok": not missing_required,
        "python": sys.version.split()[0],
        "python_ok": sys.version_info >= (3, 10),
        "packages": packages,
        "cli_tools": cli,
        "missing_required": missing_required,
        "missing_optional": missing_optional,
        "recommendations": [
            "Install required Python packages before running release tests.",
            "Install Docker Desktop only if you want sandbox and copied-workspace validation.",
            "Install Node/npm only if you want browser smoke tests and JS syntax validation.",
            "Install Ollama only if you want local model replies and code generation.",
            "Heavy image packages are optional; Nova can still run without Diffusers/Torch.",
        ],
    }


def render_dependency_report(report: dict[str, Any]) -> str:
    lines = ["Nova Dependency Check", "", f"Python: {report.get('python')} ({'ok' if report.get('python_ok') else 'too old'})", ""]
    lines.append("Python packages")
    for p in report.get("packages", []):
        req = "required" if p.get("required") else "optional"
        lines.append(f"- {'PASS' if p.get('ok') else 'MISSING'} {p.get('name')} ({req}) — {p.get('purpose')}")
    lines.append("")
    lines.append("External tools")
    for c in report.get("cli_tools", []):
        lines.append(f"- {'PASS' if c.get('ok') else 'MISSING'} {c.get('name')} — {c.get('detail')} — {c.get('purpose')}")
    return "\n".join(lines)


def install_python_packages(packages: list[str]) -> int:
    if not packages:
        return 0
    cmd = [sys.executable, "-m", "pip", "install", "--upgrade", *packages]
    return subprocess.call(cmd)


def interactive_main(argv: list[str] | None = None) -> int:
    argv = argv or sys.argv[1:]
    include_heavy = "--include-heavy" in argv
    yes = "--yes" in argv or "-y" in argv
    json_mode = "--json" in argv
    report = build_dependency_report(include_heavy=include_heavy)
    if json_mode:
        print(json.dumps(report, indent=2))
        return 0 if report.get("python_ok") else 1
    print(render_dependency_report(report))
    if not report.get("python_ok"):
        print("\nPython 3.10+ is required. Install a newer Python and rerun Nova.")
        return 1
    missing = [p for p in report.get("packages", []) if not p.get("ok") and (p.get("required") or include_heavy)]
    if not missing:
        print("\nRequired Python dependencies are present.")
        return 0
    names = [p["install"] for p in missing]
    print("\nMissing Python packages: " + ", ".join(names))
    if not yes:
        ans = input("Install missing Python packages now with pip? [y/N]: ").strip().lower()
        if ans not in {"y", "yes"}:
            print("Skipped dependency installation. Nova may still run, but tests/features may be limited.")
            return 0
    rc = install_python_packages(names)
    if rc == 0:
        print("Dependency installation completed.")
    else:
        print(f"Dependency installation returned exit code {rc}.")
    return rc


if __name__ == "__main__":
    raise SystemExit(interactive_main())
