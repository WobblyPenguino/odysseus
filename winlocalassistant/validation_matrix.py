from __future__ import annotations

import ast
import subprocess
import sys
from pathlib import Path
from typing import Any

from .development_governor import build_validation_evidence
from .feature_continuity import build_feature_continuity_audit


def _compile_python(root: Path) -> dict[str, Any]:
    targets = [str(root / "winlocalassistant")]
    if (root / "app.py").exists():
        targets.append(str(root / "app.py"))
    try:
        proc = subprocess.run([sys.executable, "-m", "compileall", "-q", *targets], cwd=root, capture_output=True, text=True, timeout=60)
        return {"name": "python_compile", "ok": proc.returncode == 0, "detail": (proc.stdout + proc.stderr)[-2000:] or "compileall passed"}
    except Exception as exc:
        return {"name": "python_compile", "ok": False, "detail": repr(exc)}


def _webui_ast(root: Path) -> dict[str, Any]:
    path = root / "winlocalassistant" / "webui.py"
    try:
        ast.parse(path.read_text(encoding="utf-8", errors="replace"))
        return {"name": "webui_python_ast", "ok": True, "detail": "webui.py parses"}
    except Exception as exc:
        return {"name": "webui_python_ast", "ok": False, "detail": repr(exc)}


def _webui_contract(root: Path) -> dict[str, Any]:
    text = ""
    try:
        text = (root / "winlocalassistant" / "webui.py").read_text(encoding="utf-8", errors="replace")
    except Exception as exc:
        return {"name": "webui_contract", "ok": False, "detail": repr(exc)}
    required = [
        "loadAssistantBox",
        "deleteSelectedRuns",
        "renderRuns",
        "loadProjects",
        "loadTools",
        "maybeSpeakReply",
        "!avatarAudioActivated",
        "toggleSettingsPanel",
        "jarvis-bridge",
        "sidecar-policy",
        "bridge-receipts",
        "browser-harness",
        "transparentOutputPanel",
        "leftActionDock",
        "personaMiniPanel",
        "custom-chat-window",
        "local-model-optimizer",
        "voice-audit",
        "startup-validation",
        "audit-log",
        "workflow-run",
        "nova-system-test",
        "completion-audit",
        "release-package",
        "codebase-advisor",
        "autonomousCockpit",
        "Scrollable reasoning timeline",
        "voiceAuthPanel",
        "voiceScreenTranscript",
        "issueVoiceToChat",
        "wlaAutoIdleExplicitOptIn",
        "communicationCentreBoard",
        "voiceGuardCard",
        "findWakeMatch",
        "startPostWakeCommandCapture",
        "SESSION_ID",
        "wakeRestartPausedForCommand",
        "finishPostWakeCapture",
        "restartWakeAfterCommand",
        "hidden-panel layout reclaim",
    ]
    missing = [x for x in required if x not in text]
    return {"name": "webui_contract", "ok": not missing, "detail": "missing: " + ", ".join(missing) if missing else "critical browser/UI markers present"}


def build_validation_matrix(root: Path, goal: str = "") -> dict[str, Any]:
    root = Path(root)
    checks: list[dict[str, Any]] = []
    checks.append(_compile_python(root))
    checks.append(_webui_ast(root))
    checks.append(_webui_contract(root))
    try:
        bridge_text = (root / "winlocalassistant" / "jarvis_bridge.py").read_text(encoding="utf-8", errors="replace")
        bridge_markers = ["probe_jarvis_daemon", "queue_proactive_action", "update_bridge_policy", "build_jarvis_setup_doctor", "build_sidecar_preflight", "build_workflow_blueprint", "build_bridge_receipts", "build_sidecar_enrollment_checklist", "build_safe_browser_harness", "build_jarvis_test_prompts", "build_audit_log", "build_workflow_execution", "host.docker.internal", "localhost"]
        missing_bridge = [m for m in bridge_markers if m not in bridge_text]
        checks.append({"name": "jarvis_bridge_contract", "ok": not missing_bridge, "detail": "Jarvis bridge markers present" if not missing_bridge else "missing: " + ", ".join(missing_bridge)})
    except Exception as exc:
        checks.append({"name": "jarvis_bridge_contract", "ok": False, "detail": repr(exc)})
    try:
        continuity = build_feature_continuity_audit(root)
        checks.append({"name": "feature_continuity", "ok": bool(continuity.get("ok")), "detail": continuity.get("summary", "feature-continuity audit")})
    except Exception as exc:
        checks.append({"name": "feature_continuity", "ok": False, "detail": repr(exc)})
    try:
        evidence = build_validation_evidence(root, goal=goal or "Nova behaviour")
        # Evidence over Nova source may not be a project, so treat as informative unless the goal is project-like.
        project_like = any(k in (goal or "").lower() for k in ["game", "project", "app", "script", "tool"])
        checks.append({"name": "behaviour_evidence", "ok": bool(evidence.get("ok") or not project_like), "detail": evidence.get("summary", "behaviour evidence")})
    except Exception as exc:
        checks.append({"name": "behaviour_evidence", "ok": False, "detail": repr(exc)})
    failed = [c for c in checks if not c.get("ok")]
    return {
        "ok": not failed,
        "root": str(root),
        "goal": goal,
        "checks": checks,
        "failed": failed,
        "summary": "validation matrix passed" if not failed else f"{len(failed)} validation matrix check(s) failed",
    }


def render_validation_matrix(payload: dict[str, Any]) -> str:
    lines = ["# Nova Validation Matrix", "", f"Root: `{payload.get('root','')}`", f"Goal: {payload.get('goal') or 'general Nova validation'}", f"Summary: {payload.get('summary','')}", "", "## Checks"]
    for check in payload.get("checks") or []:
        mark = "PASS" if check.get("ok") else "FAIL"
        lines.append(f"- {mark} {check.get('name')}: {check.get('detail')}")
    if payload.get("failed"):
        lines.append("\n## Repair focus")
        for check in payload.get("failed") or []:
            lines.append(f"- Fix `{check.get('name')}` before promotion/release.")
    return "\n".join(lines)
