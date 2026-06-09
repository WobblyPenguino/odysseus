from __future__ import annotations

import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .feature_continuity import build_feature_continuity_audit
from .validation_matrix import build_validation_matrix
from .nova_system_test import build_nova_full_system_test

COMPLETION_AUDIT_SCHEMA_VERSION = 1


@dataclass
class CompletionCheck:
    name: str
    ok: bool
    detail: str
    evidence: str = ""
    category: str = "completion"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except Exception:
        return ""


def _has_all(text: str, markers: list[str]) -> tuple[bool, list[str]]:
    missing = [m for m in markers if m not in text]
    return not missing, missing


def _compile_contract(root: Path) -> CompletionCheck:
    try:
        proc = subprocess.run(
            [sys.executable, "-m", "compileall", "-q", "winlocalassistant", "app.py"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=120,
            check=False,
        )
        out = ((proc.stdout or "") + (proc.stderr or ""))[-1800:]
        return CompletionCheck("python_compile_contract", proc.returncode == 0, "compileall passed" if proc.returncode == 0 else "compileall failed", out, "validation")
    except Exception as exc:
        return CompletionCheck("python_compile_contract", False, repr(exc), category="validation")


def build_completion_audit(root: str | Path = ".", profile: str = "quick") -> dict[str, Any]:
    """Audit whether the recent user-requested Nova tasks are actually complete.

    This is deliberately different from a normal smoke test: it checks the surfaces
    promised to the user (commands, GUI buttons, batch options, legacy compatibility,
    reports, and no-regression gates) so Nova does not merely compile while silently
    dropping a requested feature.
    """
    root = Path(root).expanduser().resolve()
    profile = (profile or "quick").strip().lower()
    started = time.time()
    core = _read(root / "winlocalassistant" / "core.py")
    tools = _read(root / "winlocalassistant" / "tools.py")
    webui = _read(root / "winlocalassistant" / "webui.py")
    bat = _read(root / "start_windows_assistant.bat")
    init_text = _read(root / "winlocalassistant" / "__init__.py")
    system_test = _read(root / "winlocalassistant" / "system_test.py")
    tests116 = _read(root / "tests_v55_3_116_nova_full_system_test.py")
    tests117 = _read(root / "tests_v55_3_117_completion_hardening.py")
    tests121 = _read(root / "tests_v55_3_121_codebase_packaging_advisor.py")

    checks: list[CompletionCheck] = []

    version_match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    version = version_match.group(1) if version_match else ""
    checks.append(CompletionCheck(
        "version_label_current_and_legacy_safe",
        bool(version and f"v{version}" in init_text and "Hey Nova" in init_text and "data-ui-overhaul=\"v55.3.115\"" in webui),
        "version label includes current version, Hey Nova continuity, and legacy UI marker" if version else "version marker missing",
        f"version={version}",
        "release",
    ))

    ok, missing = _has_all(core, ["/nova-system-test", "/nova-full-test", "/nova-test-all", "/test-nova", "nova_system_test"])
    checks.append(CompletionCheck("nova_command_routing", ok, "Nova test command aliases route to backend" if ok else "missing command markers", json.dumps(missing), "commands"))

    ok, missing = _has_all(tools, ["nova_system_test", "nova_full_test", "nova_capability_test", "build_nova_full_system_test", "render_nova_full_system_test"])
    checks.append(CompletionCheck("nova_tool_registry", ok, "Nova system test registered as ToolRegistry capability" if ok else "missing tool markers", json.dumps(missing), "tools"))

    ok, missing = _has_all(webui, ["/nova-system-test", "Nova full test", "Nova full system test", "nova_system_test"])
    checks.append(CompletionCheck("nova_gui_button_and_palette", ok, "GUI exposes Nova full test quick button and command palette item" if ok else "missing GUI markers", json.dumps(missing), "gui"))

    ok, missing = _has_all(bat, ["Run Nova full system test", "winlocalassistant.nova_system_test", "http://127.0.0.1:8766", "NOVA_SKIP_STARTUP_TESTS"])
    checks.append(CompletionCheck("batch_startup_and_one_button_flow", ok, "batch file offers startup gate, one-button Nova test, and browser launch" if ok else "missing batch markers", json.dumps(missing), "startup"))

    ok, missing = _has_all(tests116, ["test_nova_system_test_tool_registered_and_renderable", "test_gui_exposes_nova_full_system_button", "test_core_routes_nova_full_system_command"])
    checks.append(CompletionCheck("nova_regression_tests_present", ok, "v116 regression tests cover backend, GUI and routing" if ok else "missing regression test markers", json.dumps(missing), "tests"))

    ok, missing = _has_all(system_test, ["build_nova_full_system_test", "nova_full_system_contract", "tests_v55_3_116_nova_full_system_test.py"])
    checks.append(CompletionCheck("massive_test_includes_latest_nova_patch", ok, "massive test now includes Nova contract and latest regression slice" if ok else "massive test does not cover latest Nova patch", json.dumps(missing), "tests"))

    ok, missing = _has_all(core + tools + webui + tests117, ["completion_audit", "/completion-audit", "previous-task-audit"])
    checks.append(CompletionCheck("completion_audit_self_registered", ok, "completion audit command/tool/test surface exists" if ok else "completion audit is not fully registered", json.dumps(missing), "commands"))

    ok, missing = _has_all(core + tools + webui + tests121, ["release_package", "/release-package", "codebase_advisor", "/codebase-advisor", "test_release_packager_collects_files"])
    checks.append(CompletionCheck("codebase_packaging_advisor_registered", ok, "codebase advisor and clean release package surfaces exist" if ok else "codebase advisor/release package surface is incomplete", json.dumps(missing), "commands"))

    checks.append(_compile_contract(root))

    try:
        continuity = build_feature_continuity_audit(root, tool_names=[])
        checks.append(CompletionCheck("feature_continuity_no_regression", bool(continuity.get("ok")), continuity.get("summary", "feature continuity"), json.dumps(continuity.get("failed", []), indent=2)[:2200], "validation"))
    except Exception as exc:
        checks.append(CompletionCheck("feature_continuity_no_regression", False, repr(exc), category="validation"))

    try:
        matrix = build_validation_matrix(root, goal="previous task completion and no regression")
        checks.append(CompletionCheck("validation_matrix_no_regression", bool(matrix.get("ok")), matrix.get("summary", "validation matrix"), json.dumps(matrix.get("failed", []), indent=2)[:2200], "validation"))
    except Exception as exc:
        checks.append(CompletionCheck("validation_matrix_no_regression", False, repr(exc), category="validation"))

    try:
        nova = build_nova_full_system_test(root, profile="contract", timeout=30)
        checks.append(CompletionCheck("nova_contract_still_passes", bool(nova.get("ok")), nova.get("summary", "Nova contract"), json.dumps(nova.get("failed", []), indent=2)[:2200], "validation"))
    except Exception as exc:
        checks.append(CompletionCheck("nova_contract_still_passes", False, repr(exc), category="validation"))

    if profile in {"full", "release", "deep"}:
        test_files = ["tests_nova_capability_drift_v55_3_132.py", "tests_nova_improvement_assurance_v55_3_131.py", "tests_nova_route_resilience_v55_3_130.py", "tests_nova_deep_research_v55_3_129.py", "tests_nova_reliability_v55_3_128.py", "tests_nova_agent_upgrade_v55_3_127.py", "tests_nova_coding_v55_3_126.py", "tests_nova_inspiration_v55_3_125.py", "tests_improvement_features_v55_3_124.py", "tests_v55_3_123_wake_handoff_build_loop.py", "tests_v55_3_122_voice_profile_comm_activity.py", "tests_v55_3_121_codebase_packaging_advisor.py", "tests_v55_3_120_voice_reliability_security.py", "tests_v55_3_119_autonomous_cockpit_reasoning.py", "tests_v55_3_118_unified_voice_ux.py", "tests_v55_3_117_completion_hardening.py", "tests_v55_3_116_nova_full_system_test.py"]
        existing = [t for t in test_files if (root / t).exists()]
        if existing:
            try:
                proc = subprocess.run([sys.executable, "-m", "pytest", "-q", *existing], cwd=root, capture_output=True, text=True, timeout=180, check=False)
                checks.append(CompletionCheck("completion_pytest_slice", proc.returncode == 0, "completion pytest slice passed" if proc.returncode == 0 else "completion pytest slice failed", ((proc.stdout or "") + (proc.stderr or ""))[-2200:], "tests"))
            except Exception as exc:
                checks.append(CompletionCheck("completion_pytest_slice", False, repr(exc), category="tests"))

    failed = [c.to_dict() for c in checks if not c.ok]
    categories: dict[str, dict[str, int]] = {}
    for c in checks:
        bucket = categories.setdefault(c.category, {"passed": 0, "failed": 0})
        bucket["passed" if c.ok else "failed"] += 1

    return {
        "schema_version": COMPLETION_AUDIT_SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "profile": profile,
        "ok": not failed,
        "summary": "Previous-task completion audit passed" if not failed else f"Previous-task completion audit found {len(failed)} issue(s)",
        "elapsed_sec": round(time.time() - started, 3),
        "categories": categories,
        "checks": [c.to_dict() for c in checks],
        "failed": failed,
        "version": version,
    }


def render_completion_audit(payload: dict[str, Any]) -> str:
    lines = [
        "# Previous Task Completion Audit",
        "",
        str(payload.get("summary") or ""),
        "",
        f"Profile: `{payload.get('profile', 'quick')}`",
        f"Version: `{payload.get('version', '')}`",
        f"Root: `{payload.get('root', '')}`",
        f"Elapsed: {payload.get('elapsed_sec', 0)}s",
        "",
        "## Checks",
    ]
    for check in payload.get("checks") or []:
        mark = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {mark} **{check.get('name')}** ({check.get('category')}): {check.get('detail')}")
    if payload.get("failed"):
        lines.append("\n## Fix next")
        for check in payload.get("failed") or []:
            lines.append(f"### {check.get('name')}")
            evidence = str(check.get("evidence") or "").strip()
            if evidence:
                lines.append("```text")
                lines.append(evidence[-1600:])
                lines.append("```")
    lines.append("\n## Interpretation")
    if payload.get("ok"):
        lines.append("The requested Nova one-button test, GUI/batch wiring, release packaging/advisor surfaces, legacy compatibility marker, and no-regression gates are all present.")
    else:
        lines.append("One or more promised surfaces are missing or failing; do not treat this build as release-clean until the failed checks are fixed.")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Audit whether recent Nova requested tasks are actually complete.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--profile", default="quick", choices=["quick", "full", "release", "deep"])
    args = parser.parse_args(argv)
    payload = build_completion_audit(args.root, profile=args.profile)
    print(render_completion_audit(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
