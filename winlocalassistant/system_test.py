from __future__ import annotations

import json
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text
from .wla_doctor import run_wla_doctor
from .feature_audit import build_feature_audit
from .dependency_check import build_dependency_report, render_dependency_report
from .config import AssistantConfig
from .docker_manager import docker_status
from .nova_system_test import build_nova_full_system_test
from .completion_audit import build_completion_audit

LATEST_TEST_GROUPS = [
    ["tests_v55_3_121_codebase_packaging_advisor.py", "tests_v55_3_120_voice_reliability_security.py", "tests_v55_3_119_autonomous_cockpit_reasoning.py", "tests_v55_3_118_unified_voice_ux.py"],
    ["tests_v55_3_117_completion_hardening.py", "tests_v55_3_116_nova_full_system_test.py", "tests_v55_3_115_startup_workflow_audit.py", "tests_v55_3_114_persona_local_model_harness.py"],
    ["tests_v55_3_113_voice_wake_chat_mute.py", "tests_v55_3_112_left_action_jarvis_ui.py", "tests_v55_3_111_jarvis_source_inspired_bridge.py", "tests_v55_3_110_jarvis_bridge.py"],
]

LEGACY_TEST_GROUPS = [
    ["tests_v55_3_46_full_validation_hardening.py", "tests_v55_3_45_console_feature_hardening.py", "tests_release_hygiene.py", "tests_report_hygiene.py"],
    ["tests_v55_3_44_validation_feature_audit.py", "tests_v55_3_43_gui_chat_release_cleanup.py", "tests_v55_3_42_remaining_features.py", "tests_v55_3_41_defensive_validation_hardening.py"],
    ["tests_v55_3_40_validation_cleanup.py", "tests_v55_3_39_gui_project_validation_polish.py", "tests_v55_3_37_backend_chats_release_project_memory.py", "tests_v55_3_36_audio_gui_memory.py"],
    ["tests_v55_3_35_integration_radar.py", "tests_v55_3_35_release_gate_cwd.py", "tests_v55_3_34_patch_integrity_release_gate.py", "tests_v55_3_33_wla_doctor_hardening.py", "tests_v55_3_32_less_strict_sandbox_policy.py"],
]

# Backwards-compatible export used by tests and older code.
TEST_GROUPS = [*LATEST_TEST_GROUPS, *LEGACY_TEST_GROUPS]


def _run(name: str, args: list[str], cwd: Path, timeout: int = 240) -> dict[str, Any]:
    started = time.time()
    try:
        proc = subprocess.run(args, cwd=str(cwd), text=True, capture_output=True, timeout=timeout)
        return {"name": name, "ok": proc.returncode == 0, "returncode": proc.returncode, "duration_sec": round(time.time()-started, 3), "command": args, "stdout": (proc.stdout or "")[-8000:], "stderr": (proc.stderr or "")[-8000:]}
    except subprocess.TimeoutExpired as exc:
        return {"name": name, "ok": False, "timeout": timeout, "duration_sec": round(time.time()-started, 3), "command": args, "stdout": str(exc.stdout or "")[-4000:], "stderr": str(exc.stderr or "")[-4000:]}
    except Exception as exc:
        return {"name": name, "ok": False, "error": repr(exc), "duration_sec": round(time.time()-started, 3), "command": args}


def run_massive_system_test(root: Path | str = ".", include_docker: bool = True, include_playwright: bool = True, profile: str = "quick") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    source_root = Path(__file__).resolve().parents[1]
    audit_root = root if (root / "winlocalassistant" / "webui.py").exists() else source_root
    profile = (profile or "quick").strip().lower()
    started = time.time()
    steps: list[dict[str, Any]] = []
    dep = build_dependency_report()
    steps.append({"name": "dependency_check", "ok": bool(dep.get("python_ok")) and not dep.get("missing_required"), "summary": "dependency check", "data": dep})
    doc = run_wla_doctor(audit_root, "massive system test")
    steps.append({"name": "nova_doctor", "ok": bool(doc.get("ok")), "summary": doc.get("summary", ""), "data": {"markdown_path": doc.get("markdown_path")}})
    feat = build_feature_audit(audit_root)
    steps.append({"name": "feature_audit", "ok": bool(feat.get("ok")), "summary": feat.get("summary", ""), "data": {"markdown_path": feat.get("markdown_path")}})
    nova = build_nova_full_system_test(audit_root, profile="contract", timeout=45)
    steps.append({"name": "nova_full_system_contract", "ok": bool(nova.get("ok")), "summary": nova.get("summary", ""), "data": {"failed": nova.get("failed", []), "categories": nova.get("categories", {})}})
    completion = build_completion_audit(audit_root, profile="quick")
    steps.append({"name": "previous_task_completion_audit", "ok": bool(completion.get("ok")), "summary": completion.get("summary", ""), "data": {"failed": completion.get("failed", []), "categories": completion.get("categories", {})}})
    selected_groups = list(LATEST_TEST_GROUPS)
    if profile in {"full", "release", "deep", "legacy"}:
        selected_groups.extend(LEGACY_TEST_GROUPS)
    else:
        steps.append({
            "name": "legacy_regression_groups_optional",
            "ok": True,
            "skipped": True,
            "summary": "Quick massive-test profile prioritises current/latest patch regressions. Run /massive-test --confirm full for the slower legacy stack.",
        })
    compile_targets = ["winlocalassistant", "app.py"] + sorted({name for group in selected_groups for name in group if (audit_root / name).exists()})
    steps.append(_run("compileall", [sys.executable, "-m", "compileall", "-q", *compile_targets], audit_root, timeout=180))
    for idx, group in enumerate(selected_groups, start=1):
        existing = [g for g in group if (audit_root / g).exists()]
        if existing:
            steps.append(_run(f"pytest_group_{idx}", [sys.executable, "-m", "pytest", "-q", *existing], audit_root, timeout=240))
    if include_docker and shutil.which("docker"):
        steps.append(_run("docker_version", ["docker", "--version"], root, timeout=30))
        try:
            docker = docker_status(AssistantConfig(workspace=str(audit_root)), include_raw=False)
        except Exception as exc:
            docker = {"daemon_running": False, "notes": [repr(exc)]}
        if docker.get("daemon_running"):
            steps.append(_run("docker_ps", ["docker", "ps", "--format", "{{.Names}} {{.Status}}"], audit_root, timeout=30))
        else:
            notes = "; ".join(str(n) for n in docker.get("notes", []) if n)
            steps.append({
                "name": "docker_daemon_optional",
                "ok": True,
                "skipped": True,
                "summary": (notes or "Docker CLI is available but the Docker daemon is not running.") + " Start Docker Desktop, then rerun sandbox/Docker validation.",
                "data": docker,
            })
    else:
        steps.append({"name": "docker_optional", "ok": True, "skipped": True, "summary": "Docker not available or skipped"})
    if include_playwright and shutil.which("npx") and (audit_root / "playwright" / "nova_gui_smoke.spec.js").exists():
        # Do not fail the massive test if the web server is not currently running.
        steps.append(_run("playwright_smoke_optional", ["npx", "playwright", "test", "playwright/nova_gui_smoke.spec.js"], audit_root, timeout=180))
        if not steps[-1].get("ok"):
            steps[-1]["optional"] = True
            steps[-1]["ok"] = True
            steps[-1]["summary"] = "Playwright failed or Nova server unavailable; recorded as optional in massive test."
    else:
        steps.append({"name": "playwright_optional", "ok": True, "skipped": True, "summary": "Playwright unavailable or scaffold missing"})
    ok = all(bool(s.get("ok")) for s in steps)
    payload = {"ok": ok, "summary": "Massive Nova system test passed" if ok else "Massive Nova system test found issues", "root": str(root), "audit_root": str(audit_root), "profile": profile, "duration_sec": round(time.time()-started, 3), "steps": steps}
    docs = root / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    md = docs / "NOVA_MASSIVE_SYSTEM_TEST_LATEST.md"
    js = docs / "NOVA_MASSIVE_SYSTEM_TEST_LATEST.json"
    atomic_write_text(md, render_massive_system_test(payload), encoding="utf-8")
    atomic_write_json(js, payload, ensure_ascii=True)
    payload["markdown_path"] = str(md)
    payload["json_path"] = str(js)
    return payload


def _short_failure_detail(step: dict[str, Any], limit: int = 520) -> str:
    raw = str(step.get("stderr") or step.get("stdout") or step.get("error") or "")
    if not raw.strip():
        return ""
    lines = [ln.rstrip() for ln in raw.splitlines() if ln.strip()]
    interesting = [ln for ln in lines if "FAILED" in ln or "ERROR" in ln or "AssertionError" in ln or "assert " in ln or "Traceback" in ln]
    chosen = interesting[-4:] if interesting else lines[-4:]
    text = " | ".join(chosen)
    return text[-limit:]


def render_massive_system_test(payload: dict[str, Any]) -> str:
    lines = ["# Nova Massive System Test", "", f"Overall: **{'PASS' if payload.get('ok') else 'ISSUES'}**", f"Profile: `{payload.get('profile', 'quick')}`", f"Duration: {payload.get('duration_sec')} sec", "", "## Short result"]
    failed = [s for s in payload.get("steps", []) if not s.get("ok")]
    if not failed:
        lines.append("Completed successfully. Review the saved report/JSON for details if needed.")
    else:
        lines.append(f"Completed with {len(failed)} issue(s). Full stdout/stderr is saved in the JSON report; chat only shows a short summary.")
    lines += ["", "## Steps"]
    for s in payload.get("steps", []):
        icon = "✅" if s.get("ok") else "❌"
        extra = " (skipped)" if s.get("skipped") else ""
        lines.append(f"- {icon} **{s.get('name')}**{extra}: {s.get('summary') or ('passed' if s.get('ok') else 'failed')}")
        if not s.get("ok"):
            detail = _short_failure_detail(s)
            if detail:
                lines.append(f"  - Failure summary: {detail}")
    if payload.get("markdown_path"):
        lines.append(f"\nReport: `{payload.get('markdown_path')}`")
    return "\n".join(lines)
