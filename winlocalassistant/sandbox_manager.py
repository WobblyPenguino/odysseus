
from __future__ import annotations

import os
import re
import shlex
import shutil
import subprocess
import time
import logging
from dataclasses import asdict, dataclass, field, replace
from pathlib import Path
from typing import Any

from .config import APP_DIR, AssistantConfig
from .eventlog import log_activity
from .safe_io import atomic_write_json, read_json_file, append_jsonl
from .sandbox_permissions import load_pending_sandbox_permission, render_pending_sandbox_permission_markdown

SANDBOX_STATE_PATH = APP_DIR / "sandbox_state.json"
SANDBOX_AUDIT_PATH = APP_DIR / "sandbox_audit.jsonl"
SANDBOX_WORKSPACES = APP_DIR / "sandboxes"

_SAFE_NAME_RE = re.compile(r"^[a-zA-Z0-9_.-]{1,48}$")
_HIGH_RISK_TERMS = {
    "metasploit", "msfconsole", "msfvenom", "hydra", "john", "hashcat",
    "aircrack", "aireplay", "sqlmap", "wpscan", "nikto", "bettercap",
    "ettercap", "responder", "evilginx", "beef", "social-engineer",
}
_NETWORK_TERMS = {"nmap", "masscan", "zmap", "ping", "curl", "wget", "ssh", "nc", "netcat"}
_HOST_ESCAPE_TERMS = {"docker", "podman", "mount", "nsenter", "modprobe", "insmod", "systemctl", "service"}


@dataclass
class SandboxProfile:
    name: str
    title: str
    image: str
    description: str
    kali: bool = False
    network_default: str = "none"
    readonly_root: bool = False
    cpu_limit: str = "1.5"
    memory_limit: str = "2g"
    pids_limit: int = 512
    capabilities: list[str] = field(default_factory=list)
    suggested_packages: list[str] = field(default_factory=list)


PROFILES: dict[str, SandboxProfile] = {
    "linux": SandboxProfile(
        name="linux",
        title="General Linux Sandbox",
        image="python:3.12-slim",
        description="Disposable Python/Linux container for build/test experiments and Linux tools.",
        suggested_packages=["git", "python3", "python3-pip", "ripgrep", "jq", "curl"],
    ),
    "kali": SandboxProfile(
        name="kali",
        title="Kali Linux Security Lab Sandbox",
        image="kalilinux/kali-rolling",
        description="Disposable Kali-based lab container for authorised, local-only security learning and defensive testing.",
        kali=True,
        cpu_limit="2",
        memory_limit="3g",
        pids_limit=768,
        suggested_packages=[
            "kali-linux-core",
            "kali-tools-information-gathering",
            "kali-tools-vulnerability",
            "kali-tools-web",
            "kali-tools-forensics",
            "kali-tools-reporting",
        ],
    ),
}


def normalize_sandbox_policy(level: str | None) -> str:
    value = (level or "balanced").strip().lower().replace("-", "_").replace(" ", "_")
    aliases = {
        "default": "balanced",
        "normal": "balanced",
        "less_strict": "trusted_lab",
        "trusted": "trusted_lab",
        "lab": "trusted_lab",
        "trustedlab": "trusted_lab",
    }
    value = aliases.get(value, value)
    if value not in {"strict", "balanced", "trusted_lab"}:
        value = "balanced"
    return value


def sandbox_policy_level(config: AssistantConfig) -> str:
    return normalize_sandbox_policy(getattr(config, "sandbox_policy_level", "balanced"))


def sandbox_trusted_lab_enabled(config: AssistantConfig) -> bool:
    return sandbox_policy_level(config) == "trusted_lab"


def _now() -> float:
    return time.time()


def _load_state() -> dict[str, Any]:
    state = read_json_file(SANDBOX_STATE_PATH, {}, expected_type=dict, quarantine=True)
    if not isinstance(state, dict):
        state = {}
    state.setdefault("sandboxes", {})
    state.setdefault("autonomous_sandbox_mode", False)
    state.setdefault("network_authorized", False)
    state.setdefault("trusted_lab_mode", False)
    state.setdefault("backend_preference", "auto")
    return state


def _save_state(state: dict[str, Any]) -> None:
    atomic_write_json(SANDBOX_STATE_PATH, state, ensure_ascii=True, indent=2)


def _audit(event: str, payload: dict[str, Any]) -> None:
    row = {"ts": _now(), "event": event, **payload}
    append_jsonl(SANDBOX_AUDIT_PATH, row)
    try:
        log_activity("sandbox_" + event, "Sandbox event: " + event, payload)
    except Exception as exc:
        import logging
        logging.getLogger(__name__).debug("Sandbox audit activity logging failed", exc_info=exc)


def _runtime_candidates(config: AssistantConfig) -> list[str]:
    pref = getattr(config, "sandbox_backend", "auto") or "auto"
    if pref in {"docker", "podman"}:
        return [pref]
    return ["podman", "docker"]


def _runtime_daemon_status(runtime: str) -> dict[str, Any]:
    """Return daemon readiness separately from CLI availability.

    Docker Desktop can be installed and on PATH while its Linux engine pipe is
    stopped. Earlier builds treated `docker --version` as enough and then the
    sandbox failed with a raw npipe error. Keeping this separate lets status
    pages show the CLI while sandbox start/exec can fail early with a useful
    repair hint.
    """
    if not runtime:
        return {"daemon_running": False, "error": "No runtime selected."}
    try:
        if runtime == "docker":
            proc = subprocess.run([runtime, "info"], text=True, capture_output=True, timeout=12)
        elif runtime == "podman":
            proc = subprocess.run([runtime, "info"], text=True, capture_output=True, timeout=12)
        else:
            return {"daemon_running": False, "error": f"Unknown runtime {runtime!r}."}
        ok = proc.returncode == 0
        stderr = (proc.stderr or "").strip()
        stdout = (proc.stdout or "").strip()
        return {
            "daemon_running": ok,
            "error": "" if ok else (stderr or stdout or f"{runtime} daemon is not responding."),
            "hint": "" if ok else _runtime_repair_hint(runtime, stderr or stdout),
        }
    except Exception as exc:
        return {"daemon_running": False, "error": repr(exc), "hint": _runtime_repair_hint(runtime, repr(exc))}


def _runtime_repair_hint(runtime: str, error: str = "") -> str:
    low = (error or "").lower()
    if runtime == "docker":
        if "dockerdesktoplinuxengine" in low or "pipe" in low or "daemon" in low or "cannot connect" in low:
            return "Start Docker Desktop, wait until the engine is running, then retry /sandbox-status or /sandbox-linux start."
        return "Check Docker Desktop is running with `docker info`; restart Docker Desktop or PowerShell if needed."
    if runtime == "podman":
        return "Start the Podman machine with `podman machine start`, then retry the sandbox command."
    return "Install/start Docker Desktop or Podman, then retry /sandbox-status."


def detect_runtime(config: AssistantConfig) -> dict[str, Any]:
    for name in _runtime_candidates(config):
        path = shutil.which(name)
        if not path:
            continue
        try:
            proc = subprocess.run([name, "--version"], text=True, capture_output=True, timeout=8)
            if proc.returncode == 0:
                daemon = _runtime_daemon_status(name)
                return {
                    "available": True,
                    "runtime": name,
                    "path": path,
                    "version": proc.stdout.strip() or proc.stderr.strip(),
                    **daemon,
                }
        except Exception as exc:
            return {"available": False, "runtime": name, "path": path, "error": repr(exc), "daemon_running": False, "hint": _runtime_repair_hint(name, repr(exc))}
    return {"available": False, "runtime": "", "path": "", "error": "Docker or Podman was not found on PATH.", "daemon_running": False, "hint": "Install Docker Desktop or Podman, restart PowerShell/Nova, then run /sandbox-status."}


def sandbox_status(config: AssistantConfig) -> dict[str, Any]:
    state = _load_state()
    runtime = detect_runtime(config)
    rows: dict[str, Any] = {}
    for key, item in state.get("sandboxes", {}).items():
        rows[key] = dict(item)
    if runtime.get("daemon_running") is False:
        for item in rows.values():
            item["ok"] = False
            item["status_note"] = "runtime daemon/engine offline; live container state cannot be confirmed"
    runtime_name = str(runtime.get("runtime") or "")
    effective_profiles = {k: _effective_profile(config, v, runtime_name) for k, v in PROFILES.items()}
    return {
        "ok": True,
        "runtime": runtime,
        "state_path": str(SANDBOX_STATE_PATH),
        "audit_path": str(SANDBOX_AUDIT_PATH),
        "workspace_root": str(SANDBOX_WORKSPACES),
        "autonomous_sandbox_mode": bool(state.get("autonomous_sandbox_mode")),
        "network_authorized": bool(state.get("network_authorized")),
        "sandbox_policy_level": sandbox_policy_level(config),
        "trusted_lab_mode": sandbox_trusted_lab_enabled(config),
        "profiles": {k: asdict(v) for k, v in effective_profiles.items()},
        "profile_notes": {"kali": "Using wla-kali-tools:latest automatically when that local image exists."},
        "sandboxes": rows,
        "pending_permission": load_pending_sandbox_permission(),
        "policy": policy_summary(config),
    }


def policy_summary(config: AssistantConfig) -> dict[str, Any]:
    level = sandbox_policy_level(config)
    return {
        "policy_level": level,
        "trusted_lab_mode": level == "trusted_lab",
        "default_network": "none",
        "trusted_lab_kali_network": "bridge when trusted_lab is enabled and sandbox networking is authorised",
        "host_mounts": "workspace bind-mounted read-only by default; writable scratch is inside Nova profile only",
        "dangerous_host_controls": "docker/podman/mount/systemctl style commands are still blocked inside sandbox exec",
        "kali_limits": "trusted_lab is less strict for user-owned/local labs, but Nova still blocks host escape and destructive root patterns and logs commands.",
        "sandbox_dev_mode": "Writable code experiments run in a copied /workspace and must be promoted separately after validation.",
        "sandbox_autonomy": "Autonomous higher-risk experiments are allowed only when a disposable sandbox is running and sandbox autonomy is on.",
        "resource_limits": {"cpu": getattr(config, "sandbox_cpu_limit", "2"), "memory": getattr(config, "sandbox_memory_limit", "3g"), "pids": getattr(config, "sandbox_pids_limit", 768)},
    }


def _validate_profile(profile: str) -> SandboxProfile:
    profile = (profile or "linux").strip().lower()
    if profile not in PROFILES:
        raise ValueError(f"Unknown sandbox profile {profile!r}. Use one of: {', '.join(sorted(PROFILES))}")
    return PROFILES[profile]


def _container_name(profile: str, name: str | None = None) -> str:
    base = (name or f"wla-{profile}-sandbox").strip()
    if not _SAFE_NAME_RE.match(base):
        raise ValueError("Sandbox name must use only letters, numbers, underscore, dash or dot and be at most 48 chars.")
    if not base.startswith("wla-"):
        base = "wla-" + base
    return base


def _sandbox_workspace(profile: str) -> Path:
    target = SANDBOX_WORKSPACES / profile
    target.mkdir(parents=True, exist_ok=True)
    return target



def _image_exists(runtime: str, image: str) -> bool:
    if not runtime or not image:
        return False
    try:
        proc = subprocess.run([runtime, "image", "inspect", image], text=True, capture_output=True, timeout=8)
        return proc.returncode == 0
    except Exception:
        return False


def _container_running(runtime: str, name: str) -> bool:
    if not runtime or not name:
        return False
    try:
        proc = subprocess.run([runtime, "inspect", "-f", "{{.State.Running}}", name], text=True, capture_output=True, timeout=8)
        return proc.returncode == 0 and proc.stdout.strip().lower() == "true"
    except Exception:
        return False


def _container_image(runtime: str, name: str) -> str:
    if not runtime or not name:
        return ""
    try:
        proc = subprocess.run([runtime, "inspect", "-f", "{{.Config.Image}}", name], text=True, capture_output=True, timeout=8)
        if proc.returncode == 0:
            return proc.stdout.strip()
    except Exception:
        return ""
    return ""


def _effective_profile(config: AssistantConfig, prof: SandboxProfile, runtime: str = "") -> SandboxProfile:
    """Return the profile Nova should actually use on this machine.

    If the user has built the recommended Kali tools image, prefer it so Nova
    does not start the bare Kali image and then report nmap/nikto missing.
    """
    if prof.name == "kali":
        configured = str(getattr(config, "sandbox_kali_image", "") or "").strip()
        default_image = PROFILES["kali"].image
        # The dataclass default is the bare Kali image. Prefer the user's
        # locally prepared Nova tools image when present, unless they explicitly
        # configured a different non-default image.
        if runtime and (not configured or configured == default_image) and _image_exists(runtime, "wla-kali-tools:latest"):
            return replace(prof, image="wla-kali-tools:latest")
        if configured:
            return replace(prof, image=configured)
    return prof

def _run_runtime(args: list[str], timeout: int = 45) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, text=True, capture_output=True, timeout=timeout)


def start_sandbox(config: AssistantConfig, profile: str = "linux", name: str = "", network: str = "none", writable_workspace: bool = False, pull: bool = False) -> dict[str, Any]:
    prof = _validate_profile(profile)
    rt = detect_runtime(config)
    if not rt.get("available"):
        return {"ok": False, "summary": "No container runtime available", "runtime": rt, "hint": "Install Docker Desktop/Podman, then run /sandbox-status."}
    if rt.get("daemon_running") is False:
        return {"ok": False, "summary": "Container runtime is installed but its daemon/engine is not running", "runtime": rt, "hint": rt.get("hint") or "Start Docker Desktop/Podman and retry."}
    runtime = str(rt["runtime"])
    prof = _effective_profile(config, prof, runtime)
    cname = _container_name(prof.name, name or f"wla-{prof.name}-sandbox")
    raw_network = str(network or "").strip().lower()
    explicit_none = raw_network in {"__none__", "isolated", "none"} and raw_network == "__none__"
    network_mode = ("none" if raw_network == "__none__" else (network or prof.network_default or "none")).strip().lower()
    if sandbox_trusted_lab_enabled(config) and bool(getattr(config, "sandbox_allow_network", False)) and prof.name == "kali" and network_mode == "none" and not explicit_none:
        network_mode = "bridge"
    if network_mode not in {"none", "bridge"}:
        network_mode = "none"
    if _container_running(runtime, cname):
        running_image = _container_image(runtime, cname)
        state = _load_state()
        running_state = state.get("sandboxes", {}).get(prof.name, {})
        running_network = str(running_state.get("network") or "").lower()
        must_recreate = False
        if running_image and running_image != prof.image:
            must_recreate = True
        if running_network and running_network != network_mode:
            must_recreate = True
        if must_recreate:
            # Recreate stale containers when the preferred image or network mode changes.
            try:
                subprocess.run([runtime, "rm", "-f", cname], text=True, capture_output=True, timeout=20)
            except Exception:
                logging.getLogger(__name__).debug("Failed to remove stale sandbox container before recreation", exc_info=True)
        else:
            state.setdefault("sandboxes", {})[prof.name] = {
                "profile": prof.name, "name": cname, "image": prof.image, "container_id": "",
                "runtime": runtime, "network": network_mode, "workspace_mount": "rw" if writable_workspace else "ro",
                "started_at": _now(), "ok": True, "last_stdout": "already running", "last_stderr": "",
            }
            _save_state(state)
            return {"ok": True, "summary": "Sandbox already running", "profile": asdict(prof), "state": state["sandboxes"][prof.name]}
    if network_mode != "none" and not bool(getattr(config, "sandbox_allow_network", False)):
        return {"ok": False, "summary": "Sandbox network access is disabled", "hint": "Use /sandbox-network on only for owned lab targets, then restart the sandbox."}
    if pull:
        _run_runtime([runtime, "pull", prof.image], timeout=180)
    # Remove stale stopped containers that keep the Nova sandbox name reserved.
    try:
        subprocess.run([runtime, "rm", "-f", cname], text=True, capture_output=True, timeout=12)
    except Exception:
        logging.getLogger(__name__).debug("Failed to remove stale stopped sandbox container", exc_info=True)
    scratch = _sandbox_workspace(prof.name)
    mount_mode = "rw" if writable_workspace else "ro"
    cmd = [
        runtime, "run", "-d", "--name", cname,
        "--label", "wla.sandbox=true",
        "--label", f"wla.profile={prof.name}",
        "--network", network_mode,
        "--cpus", str(getattr(config, "sandbox_cpu_limit", prof.cpu_limit) or prof.cpu_limit),
        "--memory", str(getattr(config, "sandbox_memory_limit", prof.memory_limit) or prof.memory_limit),
        "--pids-limit", str(getattr(config, "sandbox_pids_limit", prof.pids_limit) or prof.pids_limit),
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges:true",
        "-v", f"{Path(config.workspace).expanduser().resolve()}:/workspace:{mount_mode}",
        "-v", f"{scratch.resolve()}:/wla_scratch:rw",
    ]
    if runtime == "docker":
        cmd += ["--rm"]
    # Keep the container alive without requiring systemd.
    cmd += [prof.image, "sh", "-lc", "mkdir -p /wla_scratch && while true; do sleep 3600; done"]
    proc = _run_runtime(cmd, timeout=60)
    ok = proc.returncode == 0
    container_id = (proc.stdout or "").strip()
    state = _load_state()
    state.setdefault("sandboxes", {})[prof.name] = {
        "profile": prof.name,
        "name": cname,
        "image": prof.image,
        "container_id": container_id,
        "runtime": runtime,
        "network": network_mode,
        "workspace_mount": mount_mode,
        "started_at": _now(),
        "ok": ok,
        "last_stdout": proc.stdout.strip(),
        "last_stderr": proc.stderr.strip(),
    }
    _save_state(state)
    _audit("start", {"profile": prof.name, "name": cname, "runtime": runtime, "ok": ok, "network": network_mode, "stderr": proc.stderr[-1000:]})
    return {"ok": ok, "summary": "Sandbox started" if ok else "Sandbox failed to start", "profile": asdict(prof), "command": _redact_cmd(cmd), "stdout": proc.stdout, "stderr": proc.stderr, "container_id": container_id, "state": state["sandboxes"][prof.name]}


def stop_sandbox(config: AssistantConfig, profile: str = "linux", name: str = "") -> dict[str, Any]:
    prof = _validate_profile(profile)
    rt = detect_runtime(config)
    if not rt.get("available"):
        return {"ok": False, "summary": "No container runtime available", "runtime": rt}
    if rt.get("daemon_running") is False:
        return {"ok": False, "summary": "Container runtime is installed but its daemon/engine is not running", "runtime": rt, "hint": rt.get("hint") or "Start Docker Desktop/Podman and retry."}
    runtime = str(rt["runtime"])
    state = _load_state()
    item = state.get("sandboxes", {}).get(prof.name, {})
    cname = _container_name(prof.name, name or item.get("name") or f"wla-{prof.name}-sandbox")
    proc = _run_runtime([runtime, "rm", "-f", cname], timeout=45)
    ok = proc.returncode == 0 or "No such" in (proc.stderr or "")
    if prof.name in state.get("sandboxes", {}):
        state["sandboxes"][prof.name]["stopped_at"] = _now()
        state["sandboxes"][prof.name]["ok"] = False
        state["sandboxes"][prof.name]["last_stdout"] = proc.stdout.strip()
        state["sandboxes"][prof.name]["last_stderr"] = proc.stderr.strip()
    _save_state(state)
    _audit("stop", {"profile": prof.name, "name": cname, "runtime": runtime, "ok": ok, "stderr": proc.stderr[-1000:]})
    return {"ok": ok, "summary": "Sandbox stopped" if ok else "Sandbox stop failed", "stdout": proc.stdout, "stderr": proc.stderr, "name": cname}


def exec_sandbox(config: AssistantConfig, profile: str = "linux", command: str = "", timeout: int = 30, allow_network_tools: bool = False, allow_high_risk: bool = False) -> dict[str, Any]:
    prof = _validate_profile(profile)
    command = (command or "").strip()
    if not command:
        return {"ok": False, "summary": "No sandbox command supplied", "usage": "/sandbox-exec linux uname -a"}
    policy = evaluate_sandbox_command(config, prof.name, command, allow_network_tools=allow_network_tools, allow_high_risk=allow_high_risk)
    if not policy["allowed"]:
        _audit("blocked_exec", {"profile": prof.name, "command": command, "reasons": policy["reasons"]})
        return {"ok": False, "summary": "Sandbox command blocked by policy", "policy": policy}
    rt = detect_runtime(config)
    if not rt.get("available"):
        return {"ok": False, "summary": "No container runtime available", "runtime": rt}
    if rt.get("daemon_running") is False:
        return {"ok": False, "summary": "Container runtime is installed but its daemon/engine is not running", "runtime": rt, "hint": rt.get("hint") or "Start Docker Desktop/Podman and retry.", "policy": policy}
    runtime = str(rt["runtime"])
    prof = _effective_profile(config, prof, runtime)
    state = _load_state()
    item = state.get("sandboxes", {}).get(prof.name, {})
    cname = item.get("name") or _container_name(prof.name, f"wla-{prof.name}-sandbox")
    if not _container_running(runtime, cname):
        started = start_sandbox(config, profile=prof.name, network=item.get("network") or prof.network_default or "none")
        if not started.get("ok"):
            return {"ok": False, "summary": "Sandbox is not running and auto-start failed", "hint": f"Run /sandbox-{prof.name} start, then retry the command.", "start_result": started, "policy": policy}
        state = _load_state()
        item = state.get("sandboxes", {}).get(prof.name, {})
        cname = item.get("name") or cname
    args = [runtime, "exec", cname, "sh", "-lc", command]
    start = _now()
    try:
        proc = _run_runtime(args, timeout=max(1, min(int(timeout or 30), 300)))
        elapsed = _now() - start
        ok = proc.returncode == 0
        _audit("exec", {"profile": prof.name, "name": cname, "ok": ok, "elapsed_sec": elapsed, "command": command[:500], "returncode": proc.returncode})
        return {"ok": ok, "summary": "Sandbox command completed" if ok else "Sandbox command failed", "stdout": proc.stdout[-8000:], "stderr": proc.stderr[-8000:], "returncode": proc.returncode, "elapsed_sec": elapsed, "policy": policy}
    except subprocess.TimeoutExpired as exc:
        _audit("exec_timeout", {"profile": prof.name, "name": cname, "command": command[:500], "timeout": timeout})
        return {"ok": False, "summary": "Sandbox command timed out", "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "", "timeout": timeout, "policy": policy}


def evaluate_sandbox_command(config: AssistantConfig, profile: str, command: str, allow_network_tools: bool = False, allow_high_risk: bool = False) -> dict[str, Any]:
    low = command.lower()
    reasons: list[str] = []
    warnings: list[str] = []
    level = sandbox_policy_level(config)
    trusted_lab = level == "trusted_lab"
    for term in _HOST_ESCAPE_TERMS:
        if re.search(r"(^|[^a-z0-9_-])" + re.escape(term) + r"([^a-z0-9_-]|$)", low):
            reasons.append(f"blocked host-control term `{term}`")
    if any(term in low for term in _NETWORK_TERMS) and not (allow_network_tools or bool(getattr(config, "sandbox_allow_network", False)) or trusted_lab):
        warnings.append("network-capable tool detected; sandbox networking remains disabled unless /sandbox-network on or /sandbox-less-strict on is used")
    elif any(term in low for term in _NETWORK_TERMS) and trusted_lab:
        warnings.append("trusted_lab mode: network-capable sandbox tool allowed without per-command approval; command is logged")
    high_risk = [term for term in _HIGH_RISK_TERMS if term in low]
    metadata_only = _metadata_only_security_tool_check(low)
    if high_risk:
        if metadata_only:
            warnings.append("security tool metadata/version check allowed; no target operation requested")
        elif profile == "kali" and (trusted_lab or allow_high_risk or bool(getattr(config, "sandbox_authorized_security_lab", False))):
            warnings.append("high-risk Kali tool allowed for owned/local lab or defensive target; action logged")
        else:
            reasons.append("high-risk offensive/security tool requested without authorised Kali lab mode or trusted_lab policy: " + ", ".join(high_risk[:5]))
    if re.search(r"\brm\s+-rf\s+/(\s|$)", low):
        reasons.append("destructive root filesystem deletion pattern blocked")
    return {"allowed": not reasons, "reasons": reasons, "warnings": warnings, "profile": profile, "policy_level": level, "command_preview": command[:240]}




def _metadata_only_security_tool_check(low: str) -> bool:
    """Return True for harmless installed-tool/version/help checks.

    This keeps the Kali safety gate intact for target operations while allowing
    setup verification such as `nikto -Version`, `sqlmap --version` or
    `msfconsole --help`.
    """
    text = (low or "").strip()
    if not text:
        return False
    # Split simple shell chains and require every part to look like metadata.
    parts = [p.strip() for p in re.split(r"\s*(?:&&|;|\|\|)\s*", text) if p.strip()]
    if not parts:
        return False
    allowed_flags = {"--version", "-version", "-v", "--help", "-h", "version", "help"}
    for part in parts:
        toks = shlex.split(part) if part else []
        if not toks:
            continue
        # Permit wrappers like `bash -lc "nikto -Version"` only if the original
        # string clearly contains a metadata flag and no obvious target.
        if toks[0] in {"bash", "sh"}:
            if not any(flag in part for flag in allowed_flags):
                return False
            continue
        if len(toks) > 3:
            return False
        if not any(tok.lower() in allowed_flags for tok in toks[1:]):
            return False
        if any(re.search(pat, part) for pat in [r"https?://", r"\b\d{1,3}(?:\.\d{1,3}){3}\b", r"\b-p\s+\d", r"--target", r"--url"]):
            return False
    return True

def set_sandbox_policy(config: AssistantConfig, level: str = "balanced") -> dict[str, Any]:
    normalized = normalize_sandbox_policy(level)
    state = _load_state()
    setattr(config, "sandbox_policy_level", normalized)
    if normalized == "trusted_lab":
        # Less strict mode: remove repeated prompts for common lab workflows while
        # keeping host-escape/destructive patterns blocked and commands audited.
        setattr(config, "sandbox_allow_network", True)
        setattr(config, "sandbox_authorized_security_lab", True)
        state["network_authorized"] = True
        state["autonomous_sandbox_mode"] = True
        state["trusted_lab_mode"] = True
    elif normalized == "strict":
        setattr(config, "sandbox_allow_network", False)
        setattr(config, "sandbox_authorized_security_lab", False)
        state["network_authorized"] = False
        state["autonomous_sandbox_mode"] = False
        state["trusted_lab_mode"] = False
    else:
        state["trusted_lab_mode"] = False
    config.save()
    _save_state(state)
    _audit("policy", {"level": normalized})
    return {"ok": True, "summary": f"Sandbox policy set to {normalized}", "policy_level": normalized, "state": state, "policy": policy_summary(config)}


def set_sandbox_flag(config: AssistantConfig, flag: str, enabled: bool) -> dict[str, Any]:
    state = _load_state()
    if flag == "autonomy":
        state["autonomous_sandbox_mode"] = bool(enabled)
    elif flag == "network":
        setattr(config, "sandbox_allow_network", bool(enabled))
        state["network_authorized"] = bool(enabled)
        config.save()
    elif flag == "authorized_lab":
        setattr(config, "sandbox_authorized_security_lab", bool(enabled))
        config.save()
    else:
        raise ValueError("Unknown sandbox flag")
    _save_state(state)
    _audit("flag", {"flag": flag, "enabled": bool(enabled)})
    return {"ok": True, "flag": flag, "enabled": bool(enabled), "state": state, "policy": policy_summary(config)}



SANDBOX_DEV_RUNS = APP_DIR / "sandbox_dev_runs"
_DEV_EXCLUDES = {"__pycache__", ".pytest_cache", ".git", ".mypy_cache", ".ruff_cache", ".nova_runtime", "node_modules"}


def _copy_for_dev_run(source: Path, dest: Path) -> dict[str, Any]:
    copied = 0
    skipped = 0
    def ignore(_dir: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            low = name.lower()
            if name in _DEV_EXCLUDES or low.endswith((".pyc", ".pyo")):
                ignored.add(name)
        return ignored
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(source, dest, ignore=ignore)
    for item in dest.rglob("*"):
        if item.is_file():
            copied += 1
    return {"copied_files": copied, "skipped_policy": "cache/runtime folders excluded", "source": str(source), "dest": str(dest)}


def sandbox_dev_run(config: AssistantConfig, profile: str = "linux", command: str = "", timeout: int = 300, network: str = "none") -> dict[str, Any]:
    """Run a writable experiment against a copied workspace, never the live tree.

    This is the mode Nova should use when it wants to freely create/edit/test code
    without touching the user's actual project until validation is good enough to
    promote separately. It intentionally does not remove every guardrail: host
    escape/destructive-root patterns and non-authorised offensive target work stay
    blocked, but project files inside the copied /workspace are writable.
    """
    prof = _validate_profile(profile)
    command = (command or "python -m compileall -q .").strip()
    rt = detect_runtime(config)
    if not rt.get("available"):
        return {"ok": False, "summary": "No container runtime available", "runtime": rt}
    if rt.get("daemon_running") is False:
        return {"ok": False, "summary": "Container runtime is installed but its daemon/engine is not running", "runtime": rt, "hint": rt.get("hint")}
    runtime = str(rt["runtime"])
    prof = _effective_profile(config, prof, runtime)
    # Check command policy with trusted dev permissions but keep host-escape and destructive-root blocking.
    policy = evaluate_sandbox_command(
        config,
        prof.name,
        command,
        allow_network_tools=(str(network).lower() == "bridge" or sandbox_trusted_lab_enabled(config)),
        allow_high_risk=(prof.name == "kali" and sandbox_trusted_lab_enabled(config)),
    )
    if not policy.get("allowed"):
        _audit("dev_blocked", {"profile": prof.name, "command": command[:500], "reasons": policy.get("reasons", [])})
        return {"ok": False, "summary": "Sandbox dev run blocked by safety policy", "policy": policy, "command": command}
    if str(network).lower() == "bridge" and not bool(getattr(config, "sandbox_allow_network", False)):
        return {"ok": False, "summary": "Sandbox dev network access is disabled", "hint": "Use /sandbox-network on only for owned/local lab targets, then retry.", "policy": policy}
    run_id = time.strftime("%Y%m%d_%H%M%S") + "_" + str(int(time.time() * 1000) % 1000000)
    run_dir = SANDBOX_DEV_RUNS / run_id
    workspace_copy = run_dir / "workspace"
    run_dir.mkdir(parents=True, exist_ok=True)
    source = Path(config.workspace).expanduser().resolve()
    copy_info = _copy_for_dev_run(source, workspace_copy)
    net = "bridge" if str(network).lower() == "bridge" else "none"
    args = [
        runtime, "run", "--rm",
        "--network", net,
        "--cpus", str(getattr(config, "sandbox_cpu_limit", prof.cpu_limit) or prof.cpu_limit),
        "--memory", str(getattr(config, "sandbox_memory_limit", prof.memory_limit) or prof.memory_limit),
        "--pids-limit", str(getattr(config, "sandbox_pids_limit", prof.pids_limit) or prof.pids_limit),
        "--security-opt", "no-new-privileges:true",
        "-v", f"{workspace_copy.resolve()}:/workspace:rw",
        "-w", "/workspace",
        prof.image, "sh", "-lc", command,
    ]
    started = _now()
    try:
        proc = _run_runtime(args, timeout=max(1, min(int(timeout or 300), 900)))
        elapsed = _now() - started
        ok = proc.returncode == 0
        report = {
            "ok": ok,
            "summary": "Sandbox dev run passed" if ok else "Sandbox dev run failed",
            "run_id": run_id,
            "profile": prof.name,
            "image": prof.image,
            "command": command,
            "network": net,
            "run_dir": str(run_dir),
            "workspace_copy": str(workspace_copy),
            "copy_info": copy_info,
            "stdout": (proc.stdout or "")[-12000:],
            "stderr": (proc.stderr or "")[-12000:],
            "returncode": proc.returncode,
            "elapsed_sec": elapsed,
            "policy": policy,
            "promotion_note": "Changes are in the copied workspace only. Promote manually after review/validation; the live workspace was not touched.",
        }
        atomic_write_json(run_dir / "sandbox_dev_run.json", report, ensure_ascii=True, indent=2)
        _audit("dev_run", {"profile": prof.name, "ok": ok, "run_id": run_id, "command": command[:500], "elapsed_sec": elapsed})
        return report
    except subprocess.TimeoutExpired as exc:
        report = {"ok": False, "summary": "Sandbox dev run timed out", "run_id": run_id, "profile": prof.name, "command": command, "timeout": timeout, "workspace_copy": str(workspace_copy), "stdout": (exc.stdout or "")[-4000:] if isinstance(exc.stdout, str) else "", "stderr": (exc.stderr or "")[-4000:] if isinstance(exc.stderr, str) else "", "policy": policy}
        atomic_write_json(run_dir / "sandbox_dev_run.json", report, ensure_ascii=True, indent=2)
        _audit("dev_timeout", {"profile": prof.name, "run_id": run_id, "command": command[:500], "timeout": timeout})
        return report


def render_status_markdown(payload: dict[str, Any]) -> str:
    rt = payload.get("runtime", {})
    lines = ["# Nova Linux/Kali Sandbox Status", ""]
    lines.append(f"Runtime available: **{bool(rt.get('available'))}**")
    if rt.get("runtime"):
        lines.append(f"Runtime: `{rt.get('runtime')}` — {rt.get('version','')}")
        if "daemon_running" in rt:
            lines.append(f"Runtime daemon/engine running: **{bool(rt.get('daemon_running'))}**")
    if rt.get("error"):
        lines.append(f"Runtime note: {rt.get('error')}")
        if rt.get("hint"):
            lines.append(f"Repair hint: {rt.get('hint')}")
        lines.append("Setup help: run `/sandbox-setup-help` for Docker Desktop/Podman installation checks.")
    lines.append(f"Sandbox policy: **{payload.get('sandbox_policy_level', 'balanced')}**")
    lines.append(f"Trusted lab mode: **{payload.get('trusted_lab_mode', False)}**")
    lines.append(f"Autonomous sandbox mode: **{payload.get('autonomous_sandbox_mode')}**")
    lines.append(f"Network authorised: **{payload.get('network_authorized')}**")
    pending = payload.get("pending_permission") or {}
    if pending:
        lines.append("")
        lines.append(render_pending_sandbox_permission_markdown(pending))
    lines.append("")
    lines.append("## Profiles")
    for key, prof in payload.get("profiles", {}).items():
        note = " (auto-detected custom tools image)" if key == "kali" and prof.get("image") == "wla-kali-tools:latest" else ""
        lines.append(f"- **{prof.get('title', key)}** (`{key}`): image `{prof.get('image')}`{note}; default network `{prof.get('network_default')}`")
    lines.append("")
    lines.append("## Running/known sandboxes")
    sandboxes = payload.get("sandboxes", {}) or {}
    if not sandboxes:
        lines.append("- None recorded yet.")
    else:
        for key, item in sandboxes.items():
            note = f"; {item.get('status_note')}" if item.get("status_note") else ""
            lines.append(f"- `{key}`: name `{item.get('name')}`, image `{item.get('image')}`, network `{item.get('network')}`, ok={item.get('ok')}{note}")
    lines.append("")
    lines.append("## Commands")
    lines += [
        "- `/sandbox-status`",
        "- `/sandbox-linux start|stop|exec <command>`",
        "- `/sandbox-kali start|stop|exec <command>`",
        "- `/sandbox-exec linux|kali <command>`",
        "- `/sandbox-dev-run linux|kali <command>` — writable copied-workspace experiment; live files are untouched",
        "- `/sandbox-autonomy on|off|status`",
        "- `/sandbox-network on|off|status`",
        "- `/sandbox-authorized-lab on|off|status` for owned/local security labs only",
    ]
    lines.append("")
    lines.append("Safety: by default network is disabled, host mounts are read-only, container capabilities are dropped, and high-risk Kali tools are blocked unless authorised lab mode is enabled.")
    return "\n".join(lines)


def sandbox_setup_help(config: AssistantConfig) -> dict[str, Any]:
    """Return host setup guidance when Docker/Podman is missing from PATH."""
    rt = detect_runtime(config)
    windows_steps = [
        "Install Docker Desktop for Windows from https://www.docker.com/products/docker-desktop/ or install Podman Desktop.",
        "Enable WSL 2 integration in Docker Desktop settings if prompted.",
        "Close and reopen PowerShell/VS Code after installation so docker.exe is on PATH.",
        "Check: docker --version",
        "Start Docker Desktop, wait until it says the engine is running, then run: docker info",
        "Pull the Python sandbox image once: docker pull python:3.12-slim",
        "Optional Kali image: docker pull kalilinux/kali-rolling",
    ]
    podman_steps = [
        "Install Podman Desktop or podman CLI.",
        "Run: podman machine init",
        "Run: podman machine start",
        "Check: podman --version",
    ]
    return {
        "ok": True,
        "summary": "Sandbox setup help",
        "runtime": rt,
        "windows_docker_steps": windows_steps,
        "podman_steps": podman_steps,
        "powershell_checks": [
            "where docker",
            "docker --version",
            "docker info",
            "docker pull python:3.12-slim",
            "docker pull kalilinux/kali-rolling",
        ],
    }


def render_setup_help_markdown(payload: dict[str, Any]) -> str:
    rt = payload.get("runtime", {}) or {}
    lines = ["# Sandbox setup help", ""]
    lines.append(f"Runtime available now: **{bool(rt.get('available'))}**")
    if rt.get("runtime"):
        lines.append(f"Detected runtime: `{rt.get('runtime')}` — {rt.get('version','')}")
    elif rt.get("error"):
        lines.append(f"Current issue: {rt.get('error')}")
    lines += ["", "## Windows Docker Desktop path"]
    lines += [f"{i+1}. {step}" for i, step in enumerate(payload.get("windows_docker_steps", []))]
    lines += ["", "## Podman alternative"]
    lines += [f"{i+1}. {step}" for i, step in enumerate(payload.get("podman_steps", []))]
    lines += ["", "## PowerShell checks", "```powershell"]
    lines += list(payload.get("powershell_checks", []))
    lines += ["```", "", "After installing, restart Nova and run `/sandbox-status`."]
    return "\n".join(lines)


def _redact_cmd(cmd: list[str]) -> list[str]:
    return [str(x)[:300] for x in cmd]
