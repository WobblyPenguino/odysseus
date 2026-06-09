from __future__ import annotations

import json
import logging
import os
import socket
import subprocess
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import append_jsonl, atomic_write_json

JARVIS_BRIDGE_SCHEMA_VERSION = 1
JARVIS_QUEUE_PATH = APP_DIR / "jarvis_bridge_actions.jsonl"
JARVIS_POLICY_PATH = APP_DIR / "jarvis_bridge_policy.json"
LOCAL_DAEMON_DEFAULT = "http://127.0.0.1:3142"

LOGGER = logging.getLogger(__name__)



def _run_readonly_command(cmd: list[str], timeout_sec: float = 5.0) -> dict[str, Any]:
    """Run a short read-only diagnostic command and return a receipt-like result."""
    try:
        completed = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=max(1.0, float(timeout_sec or 5.0)),
            check=False,
        )
        return {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout": (completed.stdout or "")[-4000:],
            "stderr": (completed.stderr or "")[-2000:],
            "command": cmd,
        }
    except FileNotFoundError as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": str(exc), "command": cmd, "missing": cmd[0] if cmd else ""}
    except Exception as exc:
        return {"ok": False, "returncode": None, "stdout": "", "stderr": repr(exc), "command": cmd}


def _read_url_json(url: str, timeout_sec: float = 2.0) -> dict[str, Any]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Nova-JarvisBridge/1.1"})
        with urllib.request.urlopen(req, timeout=max(0.5, float(timeout_sec or 2.0))) as resp:
            text = resp.read(8192).decode("utf-8", errors="replace")
            try:
                parsed = json.loads(text)
            except Exception:
                parsed = None
            return {"ok": True, "status_code": getattr(resp, "status", None), "text_preview": text[:500], "json": parsed, "url": url}
    except Exception as exc:
        return {"ok": False, "error": repr(exc), "url": url}

@dataclass
class Capability:
    name: str
    status: str
    risk: str
    default: str
    description: str
    wla_mapping: str
    required_gate: str


def _now() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")


def _is_loopback_url(url: str) -> tuple[bool, str]:
    """Return whether a URL is loopback-only. Nova should not probe/control remote Jarvis by default."""
    try:
        parsed = urllib.parse.urlparse(url)
    except Exception as exc:
        return False, f"invalid URL: {exc}"
    if parsed.scheme not in {"http", "https", "ws", "wss"}:
        return False, f"unsupported scheme {parsed.scheme!r}"
    host = (parsed.hostname or "").strip().lower()
    if host in {"localhost", "127.0.0.1", "::1"}:
        return True, "loopback host"
    try:
        infos = socket.getaddrinfo(host, None)
        if infos and all(info[4][0] in {"127.0.0.1", "::1"} for info in infos):
            return True, "resolved to loopback"
    except Exception:
        LOGGER.debug("Failed to resolve Jarvis bridge URL host %s", host, exc_info=True)
    return False, f"non-loopback host {host or '(missing)'}"


def load_policy() -> dict[str, Any]:
    default = {
        "schema_version": JARVIS_BRIDGE_SCHEMA_VERSION,
        "sidecar_level": "off",
        "proactive_level": "suggest_only",
        "allow_remote_daemon": False,
        "allow_direct_file_write": False,
        "allow_shell_execution": False,
        "allow_browser_control": False,
        "screen_awareness": "off",
        "updated_at": "",
        "notes": [
            "Daemon probing is read-only by default.",
            "Sidecar, screen, browser, filesystem and shell control remain disabled until explicitly changed.",
            "Nova should queue proposed actions through receipts/validation instead of granting direct authority.",
        ],
    }
    try:
        if JARVIS_POLICY_PATH.exists():
            data = json.loads(JARVIS_POLICY_PATH.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                merged = dict(default)
                merged.update(data)
                return merged
    except Exception:
        LOGGER.debug("Failed to load Jarvis bridge policy from %s", JARVIS_POLICY_PATH, exc_info=True)
    return default


def save_policy(policy: dict[str, Any]) -> dict[str, Any]:
    policy = dict(policy)
    policy["schema_version"] = JARVIS_BRIDGE_SCHEMA_VERSION
    policy["updated_at"] = _now()
    JARVIS_POLICY_PATH.parent.mkdir(parents=True, exist_ok=True)
    atomic_write_json(JARVIS_POLICY_PATH, policy)
    return policy


def build_capability_map() -> dict[str, Any]:
    capabilities = [
        Capability(
            "persistent_daemon",
            "integrated_as_read_only_supervisor",
            "medium",
            "probe_only",
            "Monitor a local always-on assistant daemon without giving it Nova write authority.",
            "Nova can display daemon health, version hints, connection warnings and lifecycle receipts.",
            "localhost-only probe; no remote dashboard exposure by default",
        ),
        Capability(
            "sidecars",
            "policy_defined_not_trusted_by_default",
            "high",
            "off",
            "Sidecars can extend reach to desktop, files, terminal, clipboard and browser.",
            "Nova treats sidecars as external actuators that must be enrolled, audited and approval-gated.",
            "explicit sidecar policy + per-action approval + emergency stop",
        ),
        Capability(
            "screen_awareness",
            "planned_with_privacy_gate",
            "high",
            "off",
            "Screen context can help an assistant notice errors or stuck tasks.",
            "Nova stores only user-approved summaries/receipts, not continuous screenshots by default.",
            "visible recording indicator + explicit session start/stop + redaction",
        ),
        Capability(
            "file_access",
            "already_available_in_wla_with_workspace_boundaries",
            "medium",
            "workspace_limited",
            "Read/write project files with path checks and receipts.",
            "Keep Nova as the verifier/promoter; external daemons may propose but not directly write Nova files.",
            "safe_io path resolution + mutation permission + rollback/receipt",
        ),
        Capability(
            "shell_access",
            "already_available_through_guarded_tools_and_sandbox",
            "high",
            "sandbox_preferred",
            "Shell commands are useful for tests, installs and diagnostics but risky.",
            "Prefer Docker/sandbox validation and allowlisted commands; record exact commands in receipts.",
            "risk classifier + timeout + sandbox/copy workspace + user confirmation when needed",
        ),
        Capability(
            "browser_control",
            "planned_as_test_harness_not_general_autopilot",
            "medium_high",
            "test_only",
            "Browser automation can validate GUI flows and generated web apps.",
            "Expose as Playwright/browser smoke tests first, not silent browsing of user accounts.",
            "test mode + localhost/project URLs + no credentialed sites by default",
        ),
        Capability(
            "proactive_actions",
            "integrated_as_suggest_or_queue_first",
            "medium_high",
            "suggest_only",
            "A proactive assistant can notice failures and propose next steps.",
            "Nova idle/autonomous can suggest or queue patches, then validate/promote only under policy.",
            "idle level policy + mission contract + progress score + receipt evidence",
        ),
    ]
    policy = load_policy()
    return {
        "schema_version": JARVIS_BRIDGE_SCHEMA_VERSION,
        "summary": "Jarvis-inspired bridge capabilities are mapped into Nova as supervised, approval-gated features.",
        "policy": policy,
        "capabilities": [asdict(c) for c in capabilities],
        "integration_principles": [
            "Nova remains the supervisor/verifier for Nova file changes.",
            "External daemons can be observed first, then bridged only through explicit policy.",
            "Sidecar/screen/browser/shell actions must be visible, reversible where possible, and recorded.",
            "Proactive actions default to suggestions or queued proposals, not silent execution.",
        ],
    }


def probe_jarvis_daemon(url: str = LOCAL_DAEMON_DEFAULT, timeout_sec: float = 2.0, allow_remote: bool | None = None) -> dict[str, Any]:
    """Read-only local daemon probe. This intentionally does not send chat/command messages."""
    policy = load_policy()
    allow_remote = bool(policy.get("allow_remote_daemon")) if allow_remote is None else bool(allow_remote)
    url = (url or LOCAL_DAEMON_DEFAULT).strip().rstrip("/")
    loopback, loopback_reason = _is_loopback_url(url)
    if not loopback and not allow_remote:
        return {
            "ok": False,
            "reachable": False,
            "url": url,
            "blocked": True,
            "summary": "Remote Jarvis daemon probing is blocked by Nova policy.",
            "reason": loopback_reason,
            "advice": "Use localhost for first tests, or explicitly change policy after reviewing security.",
            "policy": policy,
        }
    candidates = ["/health", "/api/health", "/status", "/api/status", "/"]
    attempts: list[dict[str, Any]] = []
    for suffix in candidates:
        target = url + suffix
        try:
            req = urllib.request.Request(target, headers={"User-Agent": "Nova-JarvisBridge/1.0"})
            with urllib.request.urlopen(req, timeout=max(0.5, float(timeout_sec or 2.0))) as resp:
                raw = resp.read(4096)
                text = raw.decode("utf-8", errors="replace")
                parsed: Any = None
                try:
                    parsed = json.loads(text)
                except Exception:
                    parsed = None
                return {
                    "ok": True,
                    "reachable": True,
                    "url": url,
                    "endpoint": suffix,
                    "status_code": getattr(resp, "status", None),
                    "summary": "Jarvis-style daemon endpoint is reachable (read-only probe).",
                    "body_preview": text[:500],
                    "json": parsed,
                    "policy": policy,
                    "warnings": _bridge_warnings(policy),
                    "attempts": attempts,
                }
        except Exception as exc:
            attempts.append({"endpoint": suffix, "ok": False, "error": repr(exc)})
    return {
        "ok": False,
        "reachable": False,
        "url": url,
        "summary": "No Jarvis-style daemon endpoint responded to read-only probes.",
        "attempts": attempts,
        "policy": policy,
        "warnings": _bridge_warnings(policy),
    }


def _bridge_warnings(policy: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    if policy.get("sidecar_level") not in {"off", "disabled", "none"}:
        warnings.append("Sidecar policy is not off; review screen/file/shell/browser authority carefully.")
    if policy.get("allow_shell_execution"):
        warnings.append("Shell execution is enabled in bridge policy; prefer sandbox/copy-workspace validation.")
    if policy.get("allow_browser_control"):
        warnings.append("Browser control is enabled; avoid credentialed sites and keep actions visible.")
    if policy.get("proactive_level") not in {"suggest_only", "off"}:
        warnings.append("Proactive actions can queue or execute work; require receipts and validation evidence.")
    return warnings


def update_bridge_policy(
    *,
    sidecar_level: str | None = None,
    proactive_level: str | None = None,
    screen_awareness: str | None = None,
    allow_remote_daemon: bool | None = None,
    allow_file_write: bool | None = None,
    allow_shell: bool | None = None,
    allow_browser: bool | None = None,
) -> dict[str, Any]:
    policy = load_policy()
    if sidecar_level is not None:
        level = str(sidecar_level).strip().lower().replace("-", "_")
        allowed = {"off", "read_only", "approve_each", "lab_only"}
        if level not in allowed:
            raise ValueError(f"sidecar_level must be one of {sorted(allowed)}")
        policy["sidecar_level"] = level
    if proactive_level is not None:
        level = str(proactive_level).strip().lower().replace("-", "_")
        allowed = {"off", "suggest_only", "queue_for_review", "auto_low_risk"}
        if level not in allowed:
            raise ValueError(f"proactive_level must be one of {sorted(allowed)}")
        policy["proactive_level"] = level
    if screen_awareness is not None:
        level = str(screen_awareness).strip().lower().replace("-", "_")
        allowed = {"off", "manual_snapshot", "session_summary"}
        if level not in allowed:
            raise ValueError(f"screen_awareness must be one of {sorted(allowed)}")
        policy["screen_awareness"] = level
    if allow_remote_daemon is not None:
        policy["allow_remote_daemon"] = bool(allow_remote_daemon)
    if allow_file_write is not None:
        policy["allow_direct_file_write"] = bool(allow_file_write)
    if allow_shell is not None:
        policy["allow_shell_execution"] = bool(allow_shell)
    if allow_browser is not None:
        policy["allow_browser_control"] = bool(allow_browser)
    return save_policy(policy)


def queue_proactive_action(
    *,
    capability: str,
    action: str,
    target: str = "",
    reason: str = "",
    risk: str = "medium",
    source: str = "wla",
) -> dict[str, Any]:
    policy = load_policy()
    capability = str(capability or "general").strip().lower().replace(" ", "_")
    action = str(action or "").strip()
    if not action:
        return {"ok": False, "status": "rejected", "summary": "No action was provided.", "policy": policy}
    blockers: list[str] = []
    if capability in {"sidecar", "screen", "screen_awareness", "desktop"} and policy.get("sidecar_level") == "off":
        blockers.append("sidecar policy is off")
    if capability in {"shell", "terminal"} and not policy.get("allow_shell_execution"):
        blockers.append("shell execution is disabled")
    if capability in {"browser", "web_browser"} and not policy.get("allow_browser_control"):
        blockers.append("browser control is disabled")
    if capability in {"file", "filesystem"} and not policy.get("allow_direct_file_write"):
        blockers.append("direct file writes are disabled; use Nova safe_io/patch queue")
    proactive_level = str(policy.get("proactive_level") or "suggest_only")
    status = "suggested"
    if blockers:
        status = "blocked"
    elif proactive_level == "queue_for_review":
        status = "queued_for_review"
    elif proactive_level == "auto_low_risk" and str(risk).lower() in {"low", "read_only", "readonly"}:
        status = "eligible_for_low_risk_auto_apply"
    elif proactive_level == "off":
        status = "blocked"
        blockers.append("proactive actions are off")
    record = {
        "ok": not blockers,
        "schema_version": JARVIS_BRIDGE_SCHEMA_VERSION,
        "created_at": _now(),
        "status": status,
        "capability": capability,
        "action": action,
        "target": target,
        "reason": reason,
        "risk": risk,
        "source": source,
        "blockers": blockers,
        "policy_snapshot": policy,
    }
    JARVIS_QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)
    append_jsonl(JARVIS_QUEUE_PATH, record)
    return record


def list_queued_actions(limit: int = 20) -> dict[str, Any]:
    rows: list[dict[str, Any]] = []
    try:
        if JARVIS_QUEUE_PATH.exists():
            for line in JARVIS_QUEUE_PATH.read_text(encoding="utf-8", errors="replace").splitlines()[-int(limit or 20):]:
                try:
                    val = json.loads(line)
                    if isinstance(val, dict):
                        rows.append(val)
                except Exception:
                    LOGGER.debug("Skipped malformed Jarvis bridge action row", exc_info=True)
    except Exception:
        LOGGER.debug("Failed to read Jarvis bridge action queue from %s", JARVIS_QUEUE_PATH, exc_info=True)
    return {
        "ok": True,
        "path": str(JARVIS_QUEUE_PATH),
        "count": len(rows),
        "actions": rows,
        "summary": f"{len(rows)} Jarvis/Nova bridge action receipt(s)",
    }



def inspect_jarvis_docker() -> dict[str, Any]:
    """Inspect local Docker containers for Jarvis daemon exposure without changing them."""
    cmd = ["docker", "ps", "--format", "{{json .}}"]
    res = _run_readonly_command(cmd, timeout_sec=5.0)
    containers: list[dict[str, Any]] = []
    for line in (res.get("stdout") or "").splitlines():
        try:
            row = json.loads(line)
        except Exception:
            continue
        image = str(row.get("Image") or "")
        name = str(row.get("Names") or "")
        ports = str(row.get("Ports") or "")
        if "jarvis" in image.lower() or "jarvis" in name.lower() or "3142" in ports:
            exposed_all = "0.0.0.0:3142" in ports or "[::]:3142" in ports or ":::3142" in ports
            localhost_only = "127.0.0.1:3142" in ports and not exposed_all
            containers.append({
                "name": name,
                "image": image,
                "ports": ports,
                "status": str(row.get("Status") or ""),
                "localhost_only": localhost_only,
                "exposed_all_interfaces": exposed_all,
                "safe_binding": localhost_only,
            })
    return {
        "ok": bool(res.get("ok")),
        "docker_available": bool(res.get("ok")) or bool(containers),
        "containers": containers,
        "summary": f"Found {len(containers)} Jarvis-like Docker container(s)." if containers else "No Jarvis Docker container found by docker ps.",
        "raw": res,
    }


def inspect_ollama_for_jarvis() -> dict[str, Any]:
    """Inspect host Ollama and produce Docker-safe Jarvis setup hints."""
    local = _read_url_json("http://127.0.0.1:11434/api/tags", timeout_sec=2.0)
    names: list[str] = []
    if isinstance(local.get("json"), dict):
        models = local["json"].get("models")
        if isinstance(models, list):
            for item in models:
                if isinstance(item, dict) and item.get("name"):
                    names.append(str(item.get("name")))
    cli = _run_readonly_command(["ollama", "list"], timeout_sec=5.0) if not names else {"ok": True, "stdout": "", "stderr": "", "command": ["ollama", "list"], "skipped": "api succeeded"}
    if not names and cli.get("stdout"):
        for line in str(cli.get("stdout") or "").splitlines()[1:]:
            parts = line.split()
            if parts:
                names.append(parts[0])
    preferred = next((m for m in names if m.startswith("llama3.2")), None) or next((m for m in names if "qwen" in m.lower()), None) or (names[0] if names else "")
    return {
        "ok": bool(names),
        "host_ollama_reachable": bool(local.get("ok")),
        "jarvis_docker_base_url": "http://host.docker.internal:11434",
        "wrong_docker_base_url": "http://localhost:11434",
        "models": names,
        "recommended_model": preferred,
        "local_api": local,
        "cli": cli,
        "summary": "Ollama models detected for Jarvis Docker setup." if names else "No Ollama models detected from Nova host checks.",
    }


def build_jarvis_setup_doctor(url: str = LOCAL_DAEMON_DEFAULT) -> dict[str, Any]:
    """Combine daemon, Docker binding and Ollama checks into one onboarding report."""
    daemon = probe_jarvis_daemon(url=url or LOCAL_DAEMON_DEFAULT, timeout_sec=1.5)
    docker = inspect_jarvis_docker()
    ollama = inspect_ollama_for_jarvis()
    warnings: list[str] = []
    for item in docker.get("containers", []):
        if item.get("exposed_all_interfaces"):
            warnings.append(f"Container {item.get('name')} exposes 3142 on all interfaces; prefer 127.0.0.1:3142 binding.")
    if ollama.get("host_ollama_reachable") and ollama.get("models"):
        pass
    else:
        warnings.append("Host Ollama is not reachable or has no models visible; Jarvis Ollama setup may fail.")
    return {
        "ok": bool(daemon.get("ok")) and bool(ollama.get("ok")) and not any("all interfaces" in w for w in warnings),
        "summary": "Jarvis setup doctor completed",
        "daemon": daemon,
        "docker": docker,
        "ollama": ollama,
        "policy": load_policy(),
        "warnings": warnings + _bridge_warnings(load_policy()),
        "safe_jarvis_docker_run": "docker run --rm -d --name jarvis-test -p 127.0.0.1:3142:3142 ghcr.io/vierisid/jarvis:0.5.2",
        "jarvis_ollama_fields": {
            "provider": "Ollama (local)",
            "ollama_base_url_inside_docker": "http://host.docker.internal:11434",
            "model": ollama.get("recommended_model") or "exact name from `ollama list`",
        },
    }


def build_sidecar_preflight(requested: str = "") -> dict[str, Any]:
    requested_caps = [c.strip().lower().replace(" ", "_") for c in str(requested or "").replace(",", " ").split() if c.strip()]
    caps = {
        "terminal": "Run shell commands through a native sidecar.",
        "filesystem": "Read/write files outside Nova's workspace sandbox.",
        "clipboard": "Read or set clipboard content.",
        "screenshot": "Capture screen images.",
        "desktop": "Window and UI automation.",
        "browser": "Chrome/CDP browser control.",
        "system_info": "Host system details.",
    }
    policy = load_policy()
    decisions = []
    for name, desc in caps.items():
        wanted = not requested_caps or name in requested_caps
        blocked = []
        if name in {"terminal"} and not policy.get("allow_shell_execution"):
            blocked.append("shell execution disabled")
        if name in {"filesystem"} and not policy.get("allow_direct_file_write"):
            blocked.append("direct file write disabled")
        if name in {"browser"} and not policy.get("allow_browser_control"):
            blocked.append("browser control disabled")
        if name in {"clipboard", "screenshot", "desktop"} and policy.get("sidecar_level") == "off":
            blocked.append("sidecar disabled")
        decisions.append({"capability": name, "description": desc, "requested": wanted, "allowed_by_policy": wanted and not blocked, "blockers": blocked})
    return {"ok": True, "summary": "Sidecar capability preflight generated", "policy": policy, "capabilities": decisions, "warnings": _bridge_warnings(policy)}


def build_authority_decision(capability: str, action: str, target: str = "", risk: str = "medium") -> dict[str, Any]:
    record = queue_proactive_action(capability=capability or "general", action=action or "review", target=target or "", reason="authority decision preview", risk=risk or "medium")
    record["summary"] = "Authority decision recorded as a receipt; no external action was executed."
    return record


def build_workflow_blueprint(goal: str = "") -> dict[str, Any]:
    goal = str(goal or "improve Nova safely").strip()
    nodes = [
        {"id": "trigger", "type": "manual_or_idle_trigger", "description": "User or idle mode proposes a goal."},
        {"id": "context", "type": "nova_operating_context", "description": "Collect goal, target, recent failures, policy, receipts and validation conditions."},
        {"id": "authority", "type": "authority_gate", "description": "Classify sidecar/shell/browser/file risk before any external action."},
        {"id": "plan", "type": "role_router", "description": "Route to Planner, Builder, Verifier, Repairer or Toolsmith."},
        {"id": "act", "type": "patch_or_queue", "description": "Prefer Nova patch queue or safe sandbox; external actions remain queued."},
        {"id": "validate", "type": "validation_matrix", "description": "Compile, GUI contract, feature continuity and behaviour evidence."},
        {"id": "receipt", "type": "action_receipt", "description": "Write changed files, commands, outcome and rollback/proof."},
    ]
    return {"ok": True, "summary": "Jarvis-style supervised workflow blueprint generated", "goal": goal, "nodes": nodes, "export_hint": "This is a NOVA-safe blueprint, not an auto-executing workflow."}



def build_bridge_receipts(limit: int = 20) -> dict[str, Any]:
    """Human-readable bridge receipts view for GUI/commands.

    This is intentionally read-only: it surfaces queued/blocked/proposed external
    actions so Nova can be transparent about what it did *not* execute silently.
    """
    payload = list_queued_actions(limit=limit)
    actions = payload.get("actions") or []
    by_status: dict[str, int] = {}
    for item in actions:
        status = str(item.get("status") or "unknown")
        by_status[status] = by_status.get(status, 0) + 1
    payload.update({
        "summary": f"Bridge receipts: {len(actions)} recent queued/blocked/proposed action(s)",
        "by_status": by_status,
        "transparency_notes": [
            "Blocked/queued actions are evidence, not silent execution.",
            "Shell, browser, screen and direct file authority remain policy-gated.",
            "Use /bridge-authority to preview a decision before allowing sidecar-style work.",
        ],
    })
    return payload


def build_sidecar_enrollment_checklist(requested: str = "") -> dict[str, Any]:
    """Create a safe, explicit checklist before a sidecar can be trusted.

    Nova does not enable sidecars here. It tells the user which proof must exist
    first, keeping enrollment manual, reversible and auditable.
    """
    policy = load_policy()
    requested_caps = [c.strip().lower().replace(" ", "_") for c in str(requested or "").replace(",", " ").split() if c.strip()]
    steps = [
        {"id": "identify", "title": "Identify sidecar", "required": True, "detail": "Record sidecar name/version, local endpoint, machine name and operator."},
        {"id": "localhost", "title": "Keep daemon local", "required": True, "detail": "Confirm any daemon dashboard/API is bound to 127.0.0.1, not 0.0.0.0."},
        {"id": "capabilities", "title": "Declare capabilities", "required": True, "detail": "List requested capabilities: terminal, filesystem, clipboard, screenshot, desktop, browser, system_info."},
        {"id": "approval", "title": "Approval mode", "required": True, "detail": "Use approve_each or read_only first; never jump straight to broad shell/browser authority."},
        {"id": "receipt", "title": "Receipt proof", "required": True, "detail": "Every sidecar action must create a bridge receipt with action, target, risk, blockers and outcome."},
        {"id": "emergency_stop", "title": "Emergency stop", "required": True, "detail": "Know the exact stop command/container/process before enabling any sidecar work."},
        {"id": "redaction", "title": "Screen privacy", "required": "screen" in requested_caps or "screenshot" in requested_caps, "detail": "For screen awareness, require visible recording indicator, manual session start/stop and redaction notes."},
        {"id": "browser_scope", "title": "Browser scope", "required": "browser" in requested_caps, "detail": "Limit browser automation to localhost/project URLs until explicitly reviewed."},
    ]
    return {
        "ok": True,
        "summary": "Sidecar enrollment checklist generated; no authority was enabled.",
        "requested": requested_caps,
        "policy": policy,
        "steps": steps,
        "warnings": _bridge_warnings(policy),
    }


def build_safe_browser_harness(target_url: str = "", mode: str = "plan") -> dict[str, Any]:
    """Plan a safe Playwright/browser-control harness instead of general browsing.

    This deliberately restricts browser automation to localhost/project URLs unless
    bridge policy explicitly allows broader browser control.
    """
    target_url = str(target_url or "http://127.0.0.1:8766").strip()
    mode = str(mode or "plan").strip().lower()
    policy = load_policy()
    loopback, reason = _is_loopback_url(target_url)
    localhost_like = loopback or target_url.startswith("file://")
    allowed = bool(localhost_like or policy.get("allow_browser_control"))
    blockers = [] if allowed else ["target is not localhost/file and browser control is disabled by policy"]
    steps = [
        "Launch Playwright in test mode only; do not use credentialed user profiles.",
        "Open target URL and capture console errors, page title and screenshot path.",
        "Exercise Nova/generated-app controls only when target is localhost/project-scoped.",
        "Write browser harness receipt: target, actions, console errors, screenshot/trace path and pass/fail.",
    ]
    return {
        "ok": allowed,
        "summary": "Safe browser-control harness is ready" if allowed else "Browser harness blocked by policy",
        "target_url": target_url,
        "mode": mode,
        "policy": policy,
        "allowed": allowed,
        "blockers": blockers,
        "steps": steps,
        "playwright_command_hint": "python -m pytest -q playwright/nova_gui_smoke.spec.js" if mode == "test" else "Use /visual-test . or /playwright-smoke-help for runnable scaffolds.",
        "warnings": _bridge_warnings(policy),
        "reason": reason,
    }


def build_jarvis_test_prompts() -> dict[str, Any]:
    """Return safe prompts/commands that prove Jarvis bridge integration works without granting authority."""
    prompts = [
        {"area": "daemon", "prompt": "/jarvis-status", "expected": "reachable or clear unavailable status; no crash"},
        {"area": "doctor", "prompt": "/jarvis-doctor", "expected": "Docker binding, Ollama base URL and exact model hints"},
        {"area": "policy", "prompt": "/sidecar-policy", "expected": "sidecar/screen/shell/browser/direct file authority off by default"},
        {"area": "preflight", "prompt": "/sidecar-preflight terminal filesystem browser screenshot", "expected": "capability blockers shown, no enablement"},
        {"area": "authority", "prompt": "/bridge-authority browser open-localhost http://127.0.0.1:3142 low", "expected": "receipt recorded; no silent browser action"},
        {"area": "receipts", "prompt": "/bridge-receipts", "expected": "recent queued/blocked action receipts visible"},
        {"area": "browser harness", "prompt": "/browser-harness http://127.0.0.1:3142", "expected": "localhost test harness allowed; no credentialed browsing"},
        {"area": "workflow", "prompt": "/workflow-blueprint validate Jarvis daemon safely", "expected": "trigger/context/authority/role/validate/receipt blueprint"},
        {"area": "Nova safety", "prompt": "/validation-matrix", "expected": "jarvis bridge and feature-continuity checks pass"},
    ]
    return {"ok": True, "summary": "Jarvis/Nova bridge test prompts generated", "prompts": prompts, "policy": load_policy()}


def build_audit_log(limit: int = 30) -> dict[str, Any]:
    """Aggregate Nova/Jarvis/voice receipts into one read-only audit view."""
    limit = max(1, min(int(limit or 30), 100))
    sources = [
        ("jarvis_bridge", JARVIS_QUEUE_PATH),
        ("voice", APP_DIR / "voice_audit.jsonl"),
        ("receipts", APP_DIR / "action_receipts.jsonl"),
        ("activity", APP_DIR / "activity.jsonl"),
    ]
    entries: list[dict[str, Any]] = []
    for source, path in sources:
        try:
            if not path.exists():
                continue
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()[-limit:]
            for line in lines:
                try:
                    item = json.loads(line)
                except Exception:
                    item = {"raw": line[:500]}
                if isinstance(item, dict):
                    item = dict(item)
                    item.setdefault("source", source)
                    item.setdefault("audit_source", source)
                    entries.append(item)
        except Exception as exc:
            entries.append({"source": source, "audit_source": source, "error": repr(exc)})
    entries = entries[-limit:]
    by_source: dict[str, int] = {}
    for item in entries:
        src = str(item.get("audit_source") or item.get("source") or "unknown")
        by_source[src] = by_source.get(src, 0) + 1
    return {
        "ok": True,
        "summary": f"Audit log: {len(entries)} recent event(s) across Nova receipts, voice, activity and Jarvis bridge",
        "policy": load_policy(),
        "audit_entries": entries,
        "by_source": by_source,
        "warnings": _bridge_warnings(load_policy()),
    }


def build_workflow_execution(goal: str = "", *, confirm: bool = False) -> dict[str, Any]:
    """Execute a safe supervised workflow skeleton.

    This does not run arbitrary external sidecar/browser/shell work. It proves the
    flow wiring: context -> authority receipt -> validation -> receipt. Mutating
    action steps remain queued unless the relevant policy and user confirmation
    are present.
    """
    goal = str(goal or "validate Nova safely").strip()
    blueprint = build_workflow_blueprint(goal)
    policy = load_policy()
    steps: list[dict[str, Any]] = []
    steps.append({"id": "trigger", "ok": True, "status": "observed", "detail": "Manual workflow trigger received."})
    authority = build_authority_decision(
        capability="workflow",
        action="execute" if confirm else "preview",
        target=goal,
        risk="medium",
    )
    steps.append({"id": "authority", "ok": bool(authority.get("ok")), "status": authority.get("status"), "detail": authority.get("summary"), "receipt": authority})
    if confirm:
        # Confirmed workflow may run NOVA-internal validation only. External authority stays gated.
        steps.append({"id": "validate", "ok": True, "status": "ready", "detail": "Run /validation-matrix for full compile/UI/continuity checks; external sidecar actions remain queued."})
        outcome = "confirmed_internal_validation_ready"
    else:
        steps.append({"id": "validate", "ok": True, "status": "preview_only", "detail": "Preview only. Add --confirm to queue a supervised workflow receipt."})
        outcome = "preview"
    return {
        "ok": True,
        "summary": "Supervised workflow execution preview generated" if not confirm else "Supervised workflow receipt queued; run validation matrix next",
        "goal": goal,
        "confirm": bool(confirm),
        "policy": policy,
        "blueprint": blueprint,
        "steps": steps,
        "outcome": outcome,
        "warnings": _bridge_warnings(policy),
    }


def render_bridge_markdown(payload: dict[str, Any]) -> str:
    lines = ["# Nova Jarvis-Style Bridge", "", str(payload.get("summary") or "Jarvis bridge status"), ""]
    if "url" in payload:
        mark = "✅" if payload.get("ok") else "❌"
        lines.append(f"{mark} Probe: `{payload.get('url')}` — {payload.get('summary','')}")
        if payload.get("endpoint"):
            lines.append(f"- Endpoint: `{payload.get('endpoint')}`")
        if payload.get("blocked"):
            lines.append(f"- Blocked: {payload.get('reason','policy block')}")
        if payload.get("attempts"):
            lines.append("- Probe attempts: " + str(len(payload.get("attempts") or [])))
        lines.append("")
    policy = payload.get("policy") if isinstance(payload.get("policy"), dict) else load_policy()
    lines.extend([
        "## Current policy",
        f"- Sidecar: `{policy.get('sidecar_level')}`",
        f"- Screen awareness: `{policy.get('screen_awareness')}`",
        f"- Proactive actions: `{policy.get('proactive_level')}`",
        f"- Remote daemon probing: `{bool(policy.get('allow_remote_daemon'))}`",
        f"- Direct file write: `{bool(policy.get('allow_direct_file_write'))}`",
        f"- Shell execution: `{bool(policy.get('allow_shell_execution'))}`",
        f"- Browser control: `{bool(policy.get('allow_browser_control'))}`",
        "",
    ])
    if payload.get("warnings"):
        lines.append("## Warnings")
        for warning in payload.get("warnings", []):
            lines.append(f"- ⚠️ {warning}")
        lines.append("")
    if payload.get("capabilities"):
        lines.append("## Capability map")
        for cap in payload.get("capabilities", []):
            lines.append(f"- **{cap.get('name')}** — {cap.get('status')} / default `{cap.get('default')}`")
            lines.append(f"  - Nova mapping: {cap.get('wla_mapping')}")
            lines.append(f"  - Gate: {cap.get('required_gate')}")
        lines.append("")
    if payload.get("daemon") or payload.get("docker") or payload.get("ollama"):
        lines.append("## Setup doctor")
        daemon = payload.get("daemon") or {}
        docker = payload.get("docker") or {}
        ollama = payload.get("ollama") or {}
        if daemon:
            lines.append(f"- Daemon: {'reachable' if daemon.get('ok') else 'not reachable'} at `{daemon.get('url', LOCAL_DAEMON_DEFAULT)}`")
        if docker:
            containers = docker.get("containers") or []
            lines.append(f"- Docker: {len(containers)} Jarvis-like container(s) found")
            for c in containers[:5]:
                bind = 'localhost-only' if c.get('localhost_only') else ('all interfaces' if c.get('exposed_all_interfaces') else 'unknown binding')
                lines.append(f"  - `{c.get('name')}` {c.get('image')} — {bind} — {c.get('status')}")
        if ollama:
            lines.append(f"- Ollama for Docker: base URL should be `{ollama.get('jarvis_docker_base_url')}`")
            if ollama.get("recommended_model"):
                lines.append(f"- Suggested model: `{ollama.get('recommended_model')}`")
            elif not ollama.get("models"):
                lines.append("- No local Ollama models detected; run `ollama list` on the host and use an exact model name.")
        if payload.get("safe_jarvis_docker_run"):
            lines.append(f"- Safer run command: `{payload.get('safe_jarvis_docker_run')}`")
        lines.append("")
    if payload.get("capabilities") and isinstance(payload.get("capabilities"), list) and payload.get("summary", "").lower().startswith("sidecar"):
        lines.append("## Sidecar preflight")
        for cap in payload.get("capabilities", []):
            mark = "✅" if cap.get("allowed_by_policy") else "⛔"
            blockers = "; ".join(cap.get("blockers") or [])
            lines.append(f"- {mark} `{cap.get('capability')}` — {cap.get('description')}" + (f" — blocked: {blockers}" if blockers else ""))
        lines.append("")
    if payload.get("nodes"):
        lines.append("## Supervised workflow blueprint")
        for node in payload.get("nodes", []):
            lines.append(f"- **{node.get('id')}** / `{node.get('type')}` — {node.get('description')}")
        lines.append("")
    if payload.get("actions"):
        lines.append("## Bridge action receipts")
        for item in payload.get("actions", []):
            blockers = item.get('blockers') or []
            blocker_txt = (" — blockers: " + "; ".join(map(str, blockers))) if blockers else ""
            lines.append(f"- `{item.get('status')}` {item.get('capability')}: {item.get('action')} — {item.get('reason','')}{blocker_txt}")
        if payload.get("by_status"):
            lines.append("- Status counts: " + ", ".join(f"{k}={v}" for k, v in payload.get("by_status", {}).items()))
        lines.append("")
    if payload.get("steps") and payload.get("summary", "").lower().startswith("sidecar enrollment"):
        lines.append("## Sidecar enrollment checklist")
        for step in payload.get("steps", []):
            mark = "✅" if step.get("required") else "•"
            lines.append(f"- {mark} **{step.get('title')}** — {step.get('detail')}")
        lines.append("")
    if payload.get("steps") and "browser" in str(payload.get("summary", "")).lower():
        lines.append("## Safe browser harness")
        if payload.get("target_url"):
            lines.append(f"- Target: `{payload.get('target_url')}`")
        if payload.get("blockers"):
            for b in payload.get("blockers", []):
                lines.append(f"- ⛔ {b}")
        for step in payload.get("steps", []):
            lines.append(f"- {step}")
        if payload.get("playwright_command_hint"):
            lines.append(f"- Command hint: `{payload.get('playwright_command_hint')}`")
        lines.append("")
    if payload.get("prompts"):
        lines.append("## Test prompts")
        for p in payload.get("prompts", []):
            lines.append(f"- `{p.get('prompt')}` — {p.get('expected')}")
        lines.append("")
    if payload.get("audit_entries"):
        lines.append("## Audit log")
        if payload.get("by_source"):
            lines.append("- Sources: " + ", ".join(f"{k}={v}" for k, v in payload.get("by_source", {}).items()))
        for item in payload.get("audit_entries", [])[:20]:
            source = item.get("audit_source") or item.get("source") or "unknown"
            action = item.get("action") or item.get("kind") or item.get("event") or item.get("summary") or item.get("raw") or "event"
            status = item.get("status") or item.get("ok") or ""
            lines.append(f"- `{source}` — {action}" + (f" — {status}" if status != "" else ""))
        lines.append("")
    if payload.get("steps") and payload.get("outcome"):
        lines.append("## Workflow execution")
        for step in payload.get("steps", []):
            mark = "✅" if step.get("ok") else "❌"
            lines.append(f"- {mark} **{step.get('id')}** — {step.get('status')}: {step.get('detail')}")
        lines.append("")
    lines.append("## Safe next step")
    lines.append("Start with `/jarvis-doctor`, `/jarvis-status`, or `/jarvis-bridge`; do not enable sidecar/shell/browser authority until Nova can show receipts and validation for every action.")
    return "\n".join(lines).strip() + "\n"
