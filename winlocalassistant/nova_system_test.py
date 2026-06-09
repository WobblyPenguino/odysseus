from __future__ import annotations

import ast
import json
import logging
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .adaptive_backlog import build_adaptive_backlog
from .feature_continuity import build_feature_continuity_audit
from .game_design import build_generic_canvas_game_project
from .jarvis_bridge import build_capability_map, build_safe_browser_harness, probe_jarvis_daemon
from .nova_operating_context import build_nova_operating_context
from .persona_profile import build_custom_chat_window_spec, load_persona_profile
from .request_intent import analyze_request_intent
from .role_router import build_role_route
from .startup_validation import build_startup_validation
from .validation_matrix import build_validation_matrix

LOGGER = logging.getLogger(__name__)

NOVA_SYSTEM_TEST_SCHEMA_VERSION = 1

LATEST_REGRESSION_TESTS = [
    "tests_nova_capability_drift_v55_3_132.py", "tests_nova_improvement_assurance_v55_3_131.py", "tests_nova_route_resilience_v55_3_130.py", "tests_nova_deep_research_v55_3_129.py", "tests_nova_reliability_v55_3_128.py", "tests_nova_agent_upgrade_v55_3_127.py", "tests_nova_coding_v55_3_126.py", "tests_nova_inspiration_v55_3_125.py", "tests_improvement_features_v55_3_124.py", "tests_v55_3_123_wake_handoff_build_loop.py",
    "tests_v55_3_122_voice_profile_comm_activity.py",
    "tests_v55_3_121_codebase_packaging_advisor.py",
    "tests_v55_3_120_voice_reliability_security.py",
    "tests_v55_3_119_autonomous_cockpit_reasoning.py",
    "tests_v55_3_118_unified_voice_ux.py",
    "tests_v55_3_117_completion_hardening.py",
    "tests_v55_3_116_nova_full_system_test.py",
    "tests_v55_3_115_startup_workflow_audit.py",
    "tests_v55_3_114_persona_local_model_harness.py",
    "tests_v55_3_113_voice_wake_chat_mute.py",
    "tests_v55_3_112_left_action_jarvis_ui.py",
    "tests_v55_3_111_jarvis_source_inspired_bridge.py",
    "tests_v55_3_110_jarvis_bridge.py",
    "tests_v55_3_109_self_routing_repair.py",
    "tests_v55_3_108_role_router_template_strategy.py",
    "tests_v55_3_107_idle_policy_receipts.py",
    "tests_v55_3_106_adaptive_validation_matrix.py",
    "tests_v55_3_105_development_governor.py",
    "tests_v55_3_104_mission_contract_iterative_repair.py",
    "tests_v55_3_103_nova_operating_context.py",
    "tests_v55_3_102_feature_continuity.py",
]

CORE_CHAT_TESTS = [
    "tests_smoke.py",
    "tests_format_result.py",
    "tests_request_intent.py",
    "tests_planning_dashboard.py",
]


@dataclass
class NovaSystemStep:
    name: str
    category: str
    ok: bool
    summary: str
    detail: str = ""
    elapsed_sec: float = 0.0
    command: list[str] | None = None
    data: dict[str, Any] | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        if payload["data"] is None:
            payload["data"] = {}
        return payload


def _tail(text: str, limit: int = 3000) -> str:
    return (text or "")[-limit:]


def _run(root: Path, name: str, category: str, command: list[str], timeout: int) -> NovaSystemStep:
    started = time.time()
    output_path: Path | None = None
    try:
        # v55.3.123: write subprocess output to a real temp file instead of a PIPE.
        # Some Windows/browser helper tests can leave a grandchild with inherited stdout;
        # a pipe can keep communicate() waiting after pytest has logically finished.
        with tempfile.NamedTemporaryFile("w+", encoding="utf-8", errors="replace", delete=False) as out:
            output_path = Path(out.name)
            proc = subprocess.run(command, cwd=root, stdout=out, stderr=subprocess.STDOUT, text=True, timeout=max(1, int(timeout)), check=False)
        output = _tail(output_path.read_text(encoding="utf-8", errors="replace") if output_path and output_path.exists() else "")
        ok = proc.returncode == 0
        return NovaSystemStep(
            name=name,
            category=category,
            ok=ok,
            summary="passed" if ok else f"failed with exit code {proc.returncode}",
            detail=output,
            elapsed_sec=round(time.time() - started, 3),
            command=command,
        )
    except subprocess.TimeoutExpired:
        out = ""
        try:
            if output_path and output_path.exists():
                out = output_path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            out = ""
        return NovaSystemStep(name, category, False, f"timed out after {timeout}s", _tail(out), round(time.time() - started, 3), command)
    except Exception as exc:
        return NovaSystemStep(name, category, False, repr(exc), "", round(time.time() - started, 3), command)
    finally:
        try:
            if output_path and output_path.exists():
                output_path.unlink()
        except Exception:
            LOGGER.debug("Failed to remove temporary Nova system test output %s", output_path, exc_info=True)


def _static_webui_js_check(root: Path) -> NovaSystemStep:
    started = time.time()
    path = root / "winlocalassistant" / "webui.py"
    try:
        text = path.read_text(encoding="utf-8", errors="replace")
        ast.parse(text)
        required = [
            "send()",
            "maybeSpeakReply",
            "toggleWakeWordListening",
            "toggleCurrentChatMute",
            "renderTransparentOutputEvidence",
            "loadAssistantBox",
            "deleteSelectedRuns",
            "jarvis-bridge",
            "persona-set",
            "startup-validation",
            "nova-system-test",
        ]
        missing = [marker for marker in required if marker not in text]
        node_ok = True
        node_detail = "node not available; static contract used"
        if shutil.which("node"):
            match = re.search(r"<script>(.*?)</script>", text, flags=re.S)
            if match:
                tmp = Path(tempfile.gettempdir()) / "wla_nova_system_test_webui.js"
                tmp.write_text(match.group(1), encoding="utf-8")
                proc = subprocess.run(["node", "--check", str(tmp)], cwd=root, capture_output=True, text=True, timeout=30)
                node_ok = proc.returncode == 0
                node_detail = _tail((proc.stdout or "") + (proc.stderr or ""), 1200) or "node --check passed"
            else:
                node_ok = False
                node_detail = "No <script> block found"
        ok = not missing and node_ok
        detail = "missing markers: " + ", ".join(missing) if missing else "browser contract markers present"
        detail += f"\n{node_detail}"
        return NovaSystemStep("webui_contract_and_js", "gui", ok, "GUI contract passed" if ok else "GUI contract failed", detail, round(time.time() - started, 3))
    except Exception as exc:
        return NovaSystemStep("webui_contract_and_js", "gui", False, repr(exc), "", round(time.time() - started, 3))


def _intent_and_role_checks(root: Path) -> list[NovaSystemStep]:
    started = time.time()
    cases = [
        ("normal_chat", "hello Nova, explain what you can do", "chat"),
        ("coding_build", "make a tiny calculator app in a new project", "project_build"),
        ("diagnostic_repair", "you didn't actually make anything, why? fix it", "diagnostic_repair"),
        ("wla_self_improve", "improve Nova's autonomous coding capability", "self_improvement"),
    ]
    results: list[NovaSystemStep] = []
    for name, prompt, expected in cases:
        intent = analyze_request_intent(prompt)
        route = build_role_route(prompt, target_type="wla_source" if expected == "self_improvement" else "project")
        ok = intent.category == expected
        results.append(NovaSystemStep(
            name=f"intent_{name}",
            category="routing",
            ok=ok,
            summary=f"{intent.category} / {route.get('primary_role')}",
            detail=json.dumps({"prompt": prompt, "intent": intent.to_dict(), "role_route": route}, indent=2, default=str)[:2200],
            elapsed_sec=round(time.time() - started, 3),
        ))
    return results


def _capability_tool_checks(root: Path) -> list[NovaSystemStep]:
    checks: list[NovaSystemStep] = []
    started = time.time()
    try:
        continuity = build_feature_continuity_audit(root)
        checks.append(NovaSystemStep("feature_continuity", "no_regression", bool(continuity.get("ok")), continuity.get("summary", "feature continuity"), json.dumps(continuity.get("failed", []), indent=2)[:2200], round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("feature_continuity", "no_regression", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    try:
        matrix = build_validation_matrix(root, goal="Nova full system validation")
        checks.append(NovaSystemStep("validation_matrix", "no_regression", bool(matrix.get("ok")), matrix.get("summary", "validation matrix"), json.dumps(matrix.get("failed", []), indent=2)[:2200], round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("validation_matrix", "no_regression", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    try:
        context = build_nova_operating_context(root, goal="Nova full system validation", mode="preview")
        checks.append(NovaSystemStep("nova_operating_context", "planning", bool(context.get("ok", True)), context.get("summary", "context built"), json.dumps({"role_route": context.get("role_route"), "verification_conditions": context.get("verification_conditions")}, indent=2, default=str)[:2200], round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("nova_operating_context", "planning", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    try:
        persona = load_persona_profile()
        chat_spec = build_custom_chat_window_spec()
        ok = bool(persona.get("identity")) and bool(chat_spec.get("sliders")) and bool(chat_spec.get("prompt_addendum"))
        checks.append(NovaSystemStep("persona_and_custom_chat", "persona", ok, "persona/custom chat contract available" if ok else "persona/custom chat incomplete", json.dumps({"persona": persona, "custom_chat": chat_spec}, indent=2, default=str)[:2200], round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("persona_and_custom_chat", "persona", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    try:
        bridge = build_capability_map()
        probe = probe_jarvis_daemon(timeout_sec=1.5)
        ok = bool(bridge.get("policy"))
        detail = json.dumps({"policy": bridge.get("policy"), "daemon_probe": probe}, indent=2, default=str)[:2200]
        checks.append(NovaSystemStep("jarvis_bridge_and_policy", "integrations", ok, "Jarvis bridge policy available" if ok else "Jarvis bridge missing", detail, round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("jarvis_bridge_and_policy", "integrations", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    try:
        harness = build_safe_browser_harness("http://127.0.0.1:8766", mode="plan")
        checks.append(NovaSystemStep("safe_browser_harness", "integrations", bool(harness.get("ok")), harness.get("summary", "browser harness"), json.dumps(harness, indent=2, default=str)[:2200], round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("safe_browser_harness", "integrations", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    try:
        backlog = build_adaptive_backlog(root, goal="Nova full system validation and next improvements")
        checks.append(NovaSystemStep("adaptive_backlog", "improvement", bool(backlog.get("ok", True)), backlog.get("summary", "adaptive backlog"), json.dumps(backlog.get("ranked", backlog.get("proposals", [])), indent=2, default=str)[:2200], round(time.time() - started, 3)))
    except Exception as exc:
        checks.append(NovaSystemStep("adaptive_backlog", "improvement", False, repr(exc), elapsed_sec=round(time.time() - started, 3)))
    return checks


def _coding_capability_check(root: Path) -> NovaSystemStep:
    started = time.time()
    try:
        project = build_generic_canvas_game_project("make a tiny game about stars")
        files = project.get("files", {})
        js = str(files.get("app.js", ""))
        html = str(files.get("index.html", ""))
        required_js = ["requestAnimationFrame", "rectsHit", "score", "keydown", "localStorage"]
        missing = [marker for marker in required_js if marker not in js]
        ok = not missing and "gameCanvas" in html and "style.css" in files and ("restart" in js.lower() or "resetgame" in js.lower())
        detail = json.dumps({"folder": project.get("folder"), "missing": missing, "files": sorted(files)}, indent=2)
        return NovaSystemStep("deterministic_coding_fallback", "coding", ok, "coding fallback can build a validated browser game" if ok else "coding fallback is incomplete", detail, round(time.time() - started, 3))
    except Exception as exc:
        return NovaSystemStep("deterministic_coding_fallback", "coding", False, repr(exc), elapsed_sec=round(time.time() - started, 3))


def build_nova_full_system_test(root: str | Path = ".", profile: str = "quick", timeout: int = 120) -> dict[str, Any]:
    """Run Nova's high-signal one-button test plan without mutating user projects."""
    root = Path(root).expanduser().resolve()
    profile = (profile or "quick").strip().lower()
    started = time.time()
    steps: list[NovaSystemStep] = []
    py = sys.executable
    contract_only = profile in {"contract", "static", "unit"}
    if not contract_only:
        steps.append(_run(root, "python_compile", "code", [py, "-m", "compileall", "-q", "winlocalassistant", "app.py"], timeout=min(max(timeout, 60), 240)))
    steps.append(_static_webui_js_check(root))
    steps.extend(_intent_and_role_checks(root))
    steps.append(_coding_capability_check(root))
    steps.extend(_capability_tool_checks(root))
    if not contract_only:
        try:
            startup = build_startup_validation(root, mode="quick", timeout=min(max(timeout, 90), 180))
            steps.append(NovaSystemStep("startup_validation_gate", "release", bool(startup.get("ok")), startup.get("summary", "startup validation"), json.dumps(startup.get("failed", []), indent=2, default=str)[:2500], 0.0, data={"json_path": startup.get("json_path")}))
        except Exception as exc:
            steps.append(NovaSystemStep("startup_validation_gate", "release", False, repr(exc)))
        latest = [test for test in LATEST_REGRESSION_TESTS if (root / test).exists()]
        tests = [test for test in CORE_CHAT_TESTS if (root / test).exists()]
        # v55.3.123: run quick pytest coverage in one subprocess. On some Windows/Python
        # combinations, running multiple nested pytest subprocesses in the same validation
        # process can leave inherited stdio handles open and make the second slice appear
        # stuck even after tests finish.
        if profile in {"full", "release", "deep"} and latest:
            combined = latest + [t for t in tests if t not in latest]
            steps.append(_run(root, "latest_regression_pytest_stack", "tests", [py, "-m", "pytest", "-q", *combined], timeout=min(max(timeout * 2, 180), 420)))
        else:
            sample = latest[:4]
            combined = sample + [t for t in tests if t not in sample]
            if combined:
                step = _run(root, "latest_regression_pytest_sample", "tests", [py, "-m", "pytest", "-q", *combined], timeout=min(max(timeout, 120), 240))
                steps.append(step)
                if tests:
                    steps.append(NovaSystemStep("core_pytest_smoke_slice", "tests", step.ok, "covered inside latest_regression_pytest_sample" if step.ok else "combined pytest slice failed", step.detail, step.elapsed_sec, step.command))
    failed = [step.to_dict() for step in steps if not step.ok]
    warnings = []
    if profile not in {"full", "release", "deep"}:
        warnings.append("Quick profile runs a representative regression slice. Use /nova-system-test full for the slower stack.")
    categories: dict[str, dict[str, int]] = {}
    for step in steps:
        bucket = categories.setdefault(step.category, {"passed": 0, "failed": 0})
        bucket["passed" if step.ok else "failed"] += 1
    return {
        "schema_version": NOVA_SYSTEM_TEST_SCHEMA_VERSION,
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "profile": profile,
        "ok": not failed,
        "summary": "Nova full system test passed" if not failed else f"Nova full system test found {len(failed)} issue(s)",
        "elapsed_sec": round(time.time() - started, 3),
        "categories": categories,
        "steps": [step.to_dict() for step in steps],
        "failed": failed,
        "warnings": warnings,
        "manual_next": [
            "/feature-continuity-audit",
            "/validation-matrix",
            "/jarvis-status",
            "/persona",
            "make a tiny calculator app in a new project",
        ],
    }


def render_nova_full_system_test(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Full System Test",
        "",
        str(payload.get("summary") or ""),
        "",
        f"Profile: `{payload.get('profile','quick')}`",
        f"Root: `{payload.get('root','')}`",
        f"Elapsed: {payload.get('elapsed_sec', 0)}s",
        "",
        "## One-by-one capability results",
    ]
    for step in payload.get("steps") or []:
        mark = "PASS" if step.get("ok") else "FAIL"
        lines.append(f"- {mark} **{step.get('name')}** ({step.get('category')}): {step.get('summary')}")
    if payload.get("warnings"):
        lines.append("\n## Notes")
        for warning in payload.get("warnings") or []:
            lines.append(f"- {warning}")
    if payload.get("failed"):
        lines.append("\n## Fix next")
        for step in payload.get("failed") or []:
            lines.append(f"### {step.get('name')}")
            if step.get("command"):
                lines.append("Command: `" + " ".join(str(x) for x in step.get("command") or []) + "`")
            detail = str(step.get("detail") or "").strip()
            if detail:
                lines.append("```text")
                lines.append(detail[-1600:])
                lines.append("```")
    lines.append("\n## Manual follow-up")
    for item in payload.get("manual_next") or []:
        lines.append(f"- `{item}`")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    import argparse
    parser = argparse.ArgumentParser(description="Run Nova full-system one-button validation.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--profile", default="quick", choices=["quick", "full", "release", "deep", "contract", "static", "unit"])
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args(argv)
    payload = build_nova_full_system_test(args.root, profile=args.profile, timeout=args.timeout)
    print(render_nova_full_system_test(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
