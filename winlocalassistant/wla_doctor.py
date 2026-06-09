from __future__ import annotations

import ast
import json
import re
import subprocess
import sys
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text
from .release_hygiene import find_release_hygiene_findings


@dataclass
class DoctorCheck:
    name: str
    ok: bool
    severity: str
    summary: str
    detail: str = ""
    fix: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


IMPORTANT_COMMANDS = [
    "/nova-doctor", "/bug-scan", "/improvement-plan", "/release-gate", "/validate-release",
    "/cohesion-report", "/validation-ladder", "/integration-radar", "/next-integrations",
    "/docker-status", "/docker-validate", "/docker-validate-patch", "/docker-promote-patch",
    "/sandbox-status", "/sandbox-policy", "/sandbox-less-strict", "/autonomous", "/self-awareness",
    "/security-watch", "/image-setup-help", "/project-target", "/chat-rename", "/chat-delete",
    "/feature-audit", "/implementation-status", "/dependency-check", "/massive-test", "/full-validation",
    "/release-hygiene", "/package-hygiene",
]

IMPORTANT_MODULES = [
    "core.py", "tools.py", "webui.py", "docker_manager.py", "sandbox_manager.py",
    "sandbox_permissions.py", "cohesion_engine.py", "integration_radar.py", "feature_audit.py", "dependency_check.py", "system_test.py", "self_awareness.py", "architecture_audit.py", "release_hygiene.py",
]

FORBIDDEN_INLINE_PATTERNS = [
    # Past send-button breakages came from dynamically generated nested quoted
    # commands, not ordinary static quick buttons. Keep this scanner focused on
    # patterns that are known fragile or should use data-command instead.
    r"fillCommand\('/attach-file\s+C:\\",
    r"onclick=\"quick\('/sandbox-approve\s+yes'\)\"",
    r"onclick=\"quick\('/docker-promote-patch\s+RUN_ID'\)\"",
]


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return path.read_text(errors="replace")


def _version_from_init(root: Path) -> str:
    try:
        tree = ast.parse((root / "winlocalassistant" / "__init__.py").read_text(encoding="utf-8"))
    except Exception:
        return ""
    for node in tree.body:
        value_node = None
        if isinstance(node, ast.Assign):
            if any(isinstance(target, ast.Name) and target.id == "__version__" for target in node.targets):
                value_node = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id == "__version__":
            value_node = node.value
        if isinstance(value_node, ast.Constant):
            return str(value_node.value or "")
    return ""


def _check_python_syntax(root: Path) -> DoctorCheck:
    bad: list[str] = []
    for path in list((root / "winlocalassistant").rglob("*.py")) + list(root.glob("tests_*.py")) + [root / "app.py"]:
        if not path.exists():
            continue
        try:
            ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception as exc:
            bad.append(f"{path.relative_to(root)}: {exc}")
    return DoctorCheck(
        "python_syntax",
        not bad,
        "critical" if bad else "info",
        "Python syntax scan passed" if not bad else f"Python syntax errors found: {len(bad)}",
        "\n".join(bad[:20]),
        "Fix syntax errors before running autonomous or promotion flows.",
    )


def _check_version_consistency(root: Path) -> DoctorCheck:
    version = _version_from_init(root)
    files = [root / "README.md", root / "CHANGELOG.md", root / "tests_release_hygiene.py", root / "winlocalassistant" / "webui.py"]
    missing: list[str] = []
    for path in files:
        if path.exists() and version and version not in _read(path):
            missing.append(str(path.relative_to(root)))
    return DoctorCheck(
        "version_consistency",
        not missing,
        "warning" if missing else "info",
        f"Version {version or 'unknown'} is consistently visible" if not missing else "Version mismatch in visible release files",
        "Missing current version in: " + ", ".join(missing) if missing else "",
        "Update README, CHANGELOG, release tests and web UI banner together.",
    )


def _check_required_modules(root: Path) -> DoctorCheck:
    missing = [m for m in IMPORTANT_MODULES if not (root / "winlocalassistant" / m).exists()]
    return DoctorCheck(
        "required_modules",
        not missing,
        "critical" if missing else "info",
        "Required Nova modules are present" if not missing else "Required modules are missing",
        ", ".join(missing),
        "Restore missing modules from the latest release zip or rollback.",
    )


def _check_command_routes(root: Path) -> DoctorCheck:
    core = _read(root / "winlocalassistant" / "core.py") if (root / "winlocalassistant" / "core.py").exists() else ""
    missing = [cmd for cmd in IMPORTANT_COMMANDS if cmd not in core]
    return DoctorCheck(
        "command_routes",
        not missing,
        "warning" if missing else "info",
        "Important command routes are visible in core.py" if not missing else "Some important command routes are missing",
        ", ".join(missing),
        "Add command routing in AssistantCore.handle_command and include it in command help/non-blocking lists where appropriate.",
    )


def _check_webui_inline_js(root: Path) -> DoctorCheck:
    webui = _read(root / "winlocalassistant" / "webui.py") if (root / "winlocalassistant" / "webui.py").exists() else ""
    findings: list[str] = []
    for pattern in FORBIDDEN_INLINE_PATTERNS:
        for match in re.finditer(pattern, webui):
            start = max(0, match.start() - 80)
            end = min(len(webui), match.end() + 80)
            findings.append(webui[start:end].replace("\n", " "))
    return DoctorCheck(
        "webui_inline_js_safety",
        not findings,
        "critical" if findings else "info",
        "Web UI inline command strings passed static scan" if not findings else "Unsafe inline command string patterns found",
        "\n".join(findings[:10]),
        "Use data-command with fillDatasetCommand/runDatasetCommand instead of nested quoted JS commands.",
    )


def _check_node_js_syntax(root: Path) -> DoctorCheck:
    webui_path = root / "winlocalassistant" / "webui.py"
    if not webui_path.exists():
        return DoctorCheck("webui_js_parse", False, "warning", "webui.py missing", "", "Restore webui.py.")
    node = None
    try:
        proc = subprocess.run(["node", "--version"], text=True, capture_output=True, timeout=8)
        if proc.returncode == 0:
            node = "node"
    except Exception:
        node = None
    if not node:
        return DoctorCheck("webui_js_parse", True, "info", "Node unavailable; skipped JS parser check", "Install Node to enable node --check validation.")
    text = _read(webui_path)
    marker = "<script>"
    end_marker = "</script>"
    if marker not in text or end_marker not in text:
        return DoctorCheck("webui_js_parse", False, "warning", "Could not extract web UI script", "", "Keep script tags intact in webui.py.")
    js = text.split(marker, 1)[1].split(end_marker, 1)[0]
    out = root / ".nova_runtime" / "doctor_webui_extract.js"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(js, encoding="utf-8")
    proc = subprocess.run([node, "--check", str(out)], text=True, capture_output=True, timeout=20)
    return DoctorCheck(
        "webui_js_parse",
        proc.returncode == 0,
        "critical" if proc.returncode else "info",
        "Web UI JavaScript parses" if proc.returncode == 0 else "Web UI JavaScript parse failed",
        (proc.stdout + proc.stderr)[-4000:],
        "Fix webui.py script syntax before shipping; a parse failure can break send().",
    )



def _check_release_hygiene(root: Path) -> DoctorCheck:
    findings = find_release_hygiene_findings(root, include_python_cache=False)
    package_artifacts = [f for f in findings if f.severity in {"critical", "warning"}]
    return DoctorCheck(
        "release_hygiene",
        not package_artifacts,
        "warning" if package_artifacts else "info",
        "Release tree has no cache/bytecode package artifacts" if not package_artifacts else f"Release tree contains {len(package_artifacts)} cache/bytecode artifact(s)",
        "; ".join(f.path for f in package_artifacts[:20]),
        "The shared zip should exclude caches; runtime-created Python caches are ignored during live Doctor checks.",
    )

def _check_tests_present(root: Path) -> DoctorCheck:
    tests = sorted(p.name for p in root.glob("tests_v55_3_*.py"))
    latest = tests[-5:]
    ok = bool(tests)
    return DoctorCheck(
        "regression_tests_present",
        ok,
        "warning" if not ok else "info",
        f"Regression tests present: {len(tests)}" if ok else "No versioned regression tests found",
        "Latest: " + ", ".join(latest),
        "Add a tests_v55_3_xx file for each new capability or bugfix.",
    )



def _check_patch_hash_locking(root: Path) -> DoctorCheck:
    docker_manager = _read(root / "winlocalassistant" / "docker_manager.py") if (root / "winlocalassistant" / "docker_manager.py").exists() else ""
    required = ["patch_sha256", "_sha256_file", "_sha256_text", "Refusing to promote because the saved patch hash"]
    missing = [token for token in required if token not in docker_manager]
    return DoctorCheck(
        "patch_hash_locking",
        not missing,
        "critical" if missing else "info",
        "Docker patch promotion is hash-locked" if not missing else "Docker patch promotion is missing hash-lock guardrails",
        "Missing tokens: " + ", ".join(missing) if missing else "Validated patches include a SHA256 lock and promotion verifies it before applying.",
        "Store patch_sha256 during validation and refuse promotion if the saved patch file differs from the validation report.",
    )


def _run_gate_command(name: str, args: list[str], timeout: int = 120, cwd: Path | None = None) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=max(1, timeout), cwd=str(cwd) if cwd else None)
        return {
            "name": name,
            "ok": proc.returncode == 0,
            "returncode": proc.returncode,
            "stdout": (proc.stdout or "")[-6000:],
            "stderr": (proc.stderr or "")[-6000:],
            "command": args,
            "cwd": str(cwd) if cwd else "",
        }
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "ok": False, "timeout": timeout, "stdout": str(exc.stdout or "")[-3000:], "stderr": str(exc.stderr or "")[-3000:], "command": args, "cwd": str(cwd) if cwd else ""}
    except Exception as exc:
        return {"name": name, "ok": False, "error": repr(exc), "command": args, "cwd": str(cwd) if cwd else ""}


def _server_reachable(url: str = "http://127.0.0.1:8766", timeout: float = 1.0) -> bool:
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            return 200 <= int(resp.status) < 500
    except Exception:
        return False


def _playwright_available(root: Path) -> bool:
    spec = root / "playwright" / "nova_gui_smoke.spec.js"
    if not spec.exists():
        return False
    try:
        node = subprocess.run(["node", "--version"], text=True, capture_output=True, timeout=8)
        npx = subprocess.run(["npx", "--version"], text=True, capture_output=True, timeout=8)
        return node.returncode == 0 and npx.returncode == 0
    except Exception:
        return False


def run_wla_release_gate(root: Path | str = ".", goal: str = "", test_command: str = "") -> dict[str, Any]:
    """Run a practical pre-release validation bundle.

    The release gate is deliberately local and deterministic: doctor checks,
    compileall, and a compact regression set. Docker validation remains a
    separate optional gate because Docker may not be installed or the image may
    need pulling.
    """
    root = Path(root).expanduser().resolve()
    doctor = run_wla_doctor(root, goal or "release gate")
    commands: list[dict[str, Any]] = []
    commands.append(_run_gate_command("compileall", [sys.executable, "-m", "compileall", "-q", "winlocalassistant", "app.py"], timeout=180, cwd=root))
    default_tests = [
        "tests_v55_3_48_sandbox_project_hardening.py",
        "tests_v55_3_47_dependency_system_test.py",
        "tests_v55_3_46_full_validation_hardening.py",
        "tests_v55_3_45_console_feature_hardening.py",
        "tests_v55_3_44_validation_feature_audit.py",
        "tests_v55_3_43_gui_chat_release_cleanup.py",
        "tests_v55_3_42_remaining_features.py",
        "tests_v55_3_41_defensive_validation_hardening.py",
        "tests_release_hygiene.py",
        "tests_report_hygiene.py",
    ]
    if test_command.strip():
        if sys.platform.startswith("win"):
            commands.append(_run_gate_command("custom_tests", ["powershell", "-NoProfile", "-Command", test_command], timeout=300, cwd=root))
        else:
            commands.append(_run_gate_command("custom_tests", ["sh", "-lc", test_command], timeout=300, cwd=root))
    else:
        existing_tests = [name for name in default_tests if (root / name).exists()]
        if existing_tests:
            commands.append(_run_gate_command("targeted_pytest", [sys.executable, "-m", "pytest", "-q", *existing_tests], timeout=300, cwd=root))
    # Optional browser UI gate: run only when Playwright tooling is installed and
    # a Nova web server is already reachable. Missing server/tooling is recorded as
    # a skip, not a failure, so release-gate remains usable in CLI-only contexts.
    if _playwright_available(root) and _server_reachable():
        commands.append(_run_gate_command("playwright_smoke", ["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"], timeout=180, cwd=root))
    else:
        commands.append({"name": "playwright_smoke", "ok": True, "skipped": True, "summary": "Skipped because Playwright is unavailable or Nova server is not reachable at http://127.0.0.1:8766", "command": ["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"], "cwd": str(root)})
    ok = bool(doctor.get("ok")) and all(bool(c.get("ok")) for c in commands)
    payload = {
        "ok": ok,
        "goal": goal,
        "root": str(root),
        "summary": "Nova release gate passed" if ok else "Nova release gate found issues",
        "doctor": doctor,
        "commands": commands,
        "recommendations": [
            "Run /nova-doctor before packaging every release.",
            "Run /release-gate before sharing a zip.",
            "For code-changing patches, run /docker-validate-patch and only promote hash-locked passing reports.",
            "If Docker is available, also run /docker-validate quick after /release-gate.",
            "If Nova is running in the browser and Playwright is installed, /release-gate now runs the GUI smoke test automatically.",
        ],
    }
    report_dir = root / "docs"
    report_dir.mkdir(exist_ok=True)
    md = report_dir / "NOVA_RELEASE_GATE_LATEST.md"
    js = report_dir / "NOVA_RELEASE_GATE_LATEST.json"
    atomic_write_text(md, render_wla_release_gate_markdown(payload), encoding="utf-8")
    atomic_write_json(js, payload, ensure_ascii=True)
    payload["markdown_path"] = str(md)
    payload["json_path"] = str(js)
    return payload


def render_wla_release_gate_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Nova Release Gate", "", f"OK: **{bool(payload.get('ok'))}**", f"Summary: {payload.get('summary','')}"]
    doctor = payload.get("doctor") or {}
    lines += ["", "## Doctor", f"- OK: **{bool(doctor.get('ok'))}**", f"- Summary: {doctor.get('summary','')}"]
    lines += ["", "## Commands"]
    for cmd in payload.get("commands") or []:
        lines.append(f"- `{cmd.get('name','')}`: {'passed' if cmd.get('ok') else 'failed'}")
        if not cmd.get("ok"):
            detail = str(cmd.get("stderr") or cmd.get("stdout") or cmd.get("error") or "")[-1500:]
            if detail:
                lines += ["  ```", detail, "  ```"]
    recs = payload.get("recommendations") or []
    if recs:
        lines += ["", "## Recommendations"] + [f"- {r}" for r in recs]
    if payload.get("markdown_path"):
        lines += ["", f"Report: `{payload.get('markdown_path')}`"]
    return "\n".join(lines)


def run_wla_doctor(root: Path | str = ".", goal: str = "") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    checks = [
        _check_python_syntax(root),
        _check_version_consistency(root),
        _check_required_modules(root),
        _check_command_routes(root),
        _check_webui_inline_js(root),
        _check_patch_hash_locking(root),
        _check_node_js_syntax(root),
        _check_tests_present(root),
        _check_release_hygiene(root),
    ]
    counts = {"critical": 0, "warning": 0, "info": 0}
    for check in checks:
        if not check.ok:
            counts[check.severity] = counts.get(check.severity, 0) + 1
    ok = counts.get("critical", 0) == 0
    recommendations = build_improvement_recommendations(checks, goal)
    payload = {
        "ok": ok,
        "goal": goal,
        "root": str(root),
        "checks": [c.to_dict() for c in checks],
        "counts": counts,
        "recommendations": recommendations,
        "summary": "Nova doctor passed critical checks" if ok else "Nova doctor found critical issues",
    }
    report_dir = root / "docs"
    report_dir.mkdir(exist_ok=True)
    md = report_dir / "NOVA_DOCTOR_LATEST.md"
    js = report_dir / "NOVA_DOCTOR_LATEST.json"
    atomic_write_text(md, render_wla_doctor_markdown(payload), encoding="utf-8")
    atomic_write_json(js, payload, ensure_ascii=True)
    payload["markdown_path"] = str(md)
    payload["json_path"] = str(js)
    return payload


def build_improvement_recommendations(checks: list[DoctorCheck], goal: str = "") -> list[str]:
    failed = [c for c in checks if not c.ok]
    recs: list[str] = []
    for check in failed:
        if check.fix:
            recs.append(f"Fix {check.name}: {check.fix}")
    recs.extend([
        "Run the validation ladder before shipping: compileall -> targeted pytest -> web UI JS parse -> Docker validation when available.",
        "Prefer data-command buttons over inline quoted command strings in webui.py.",
        "For autonomous changes, generate a patch, validate it in Docker, then promote only after checks pass.",
        "Keep README, version label, CHANGELOG and release tests updated in the same commit/build.",
    ])
    if goal:
        recs.append(f"Goal-specific next step: create a small patch for `{goal}`, run /docker-validate-patch, then promote only if the report passes.")
    # De-duplicate while preserving order.
    return list(dict.fromkeys(recs))[:12]


def render_wla_doctor_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Nova Doctor Report", "", f"Goal: {payload.get('goal') or 'general reliability'}", f"Root: `{payload.get('root')}`", "", f"Overall: **{'PASS' if payload.get('ok') else 'NEEDS ATTENTION'}**", ""]
    counts = payload.get("counts") or {}
    lines.append(f"Critical issues: **{counts.get('critical', 0)}**; warnings: **{counts.get('warning', 0)}**")
    lines.append("")
    lines.append("## Checks")
    for item in payload.get("checks", []):
        icon = "✅" if item.get("ok") else "❌"
        lines.append(f"- {icon} **{item.get('name')}** [{item.get('severity')}]: {item.get('summary')}")
        if item.get("detail") and not item.get("ok"):
            lines.append(f"  - Detail: `{str(item.get('detail'))[:700]}`")
    lines.append("")
    lines.append("## Recommended next improvements")
    for rec in payload.get("recommendations", []):
        lines.append(f"- {rec}")
    if payload.get("markdown_path"):
        lines.append("")
        lines.append(f"Report written: `{payload.get('markdown_path')}`")
    return "\n".join(lines)
