from __future__ import annotations

import importlib.util
import json
import os
import platform
import re
import shlex
import shutil
import socket
import subprocess
import ipaddress
import urllib.error
import urllib.request
from urllib.parse import urlparse
import textwrap
import time
from pathlib import Path
from typing import Any

from . import ASSISTANT_NAME, __version__
from .safe_io import atomic_write_text, atomic_write_json, read_json_file

REMOTE_STATUS_FILE = "REMOTE_ACCESS_STATUS.json"
REMOTE_GUIDE_FILE = "NOVA_REMOTE_ACCESS_SETUP.md"
REMOTE_PROFILES_FILE = "remote_profiles.json"
DEFAULT_API_PORT = 8767
DEFAULT_WOL_PORT = 9

_MAC_RE = re.compile(r"^[0-9A-Fa-f]{12}$")
_PROFILE_RE = re.compile(r"^[A-Za-z0-9_.-]{1,48}$")


def _root(root: Path | str | None = None) -> Path:
    return Path(root or Path.cwd()).resolve()


def remote_profiles_path(root: Path | str | None = None) -> Path:
    return _root(root) / "config" / REMOTE_PROFILES_FILE


def _valid_profile_name(name: str) -> str:
    cleaned = str(name or "").strip()
    if not _PROFILE_RE.fullmatch(cleaned):
        raise ValueError("Profile name must be 1-48 characters using letters, numbers, dot, underscore or hyphen.")
    return cleaned


def load_remote_profiles(root: Path | str | None = None) -> dict[str, Any]:
    """Load saved remote profiles without exposing or requiring raw tokens.

    Profiles are intentionally local config only. They may store a token
    environment-variable name, but never a token value. This keeps repeated
    phone/laptop setup commands short without leaking credentials into config.
    """
    path = remote_profiles_path(root)
    raw = read_json_file(path, {"profiles": {}, "default": ""}, expected_type=dict, quarantine=True)
    profiles_raw = raw.get("profiles") if isinstance(raw, dict) else {}
    profiles: dict[str, dict[str, Any]] = {}
    if isinstance(profiles_raw, dict):
        for name, profile in profiles_raw.items():
            if not isinstance(profile, dict):
                continue
            try:
                clean_name = _valid_profile_name(str(profile.get("name") or name))
            except Exception:
                continue
            try:
                port_value = int(profile.get("port") or DEFAULT_API_PORT)
            except Exception:
                port_value = DEFAULT_API_PORT
            if not (1 <= port_value <= 65535):
                port_value = DEFAULT_API_PORT
            mac_value = str(profile.get("mac") or "").strip()
            if mac_value:
                try:
                    mac_value = normalize_mac(mac_value)
                except Exception:
                    mac_value = ""
            item = {
                "name": clean_name,
                "host": str(profile.get("host") or "").strip(),
                "port": port_value,
                "mac": mac_value,
                "broadcast": str(profile.get("broadcast") or "255.255.255.255").strip(),
                "token_env": str(profile.get("token_env") or "").strip(),
                "created_at": str(profile.get("created_at") or ""),
                "updated_at": str(profile.get("updated_at") or ""),
            }
            profiles[clean_name] = item
    default = str(raw.get("default") or "") if isinstance(raw, dict) else ""
    if default not in profiles:
        default = ""
    return {"profiles": profiles, "default": default, "path": str(path)}


def save_remote_profiles(data: dict[str, Any], root: Path | str | None = None) -> Path:
    path = remote_profiles_path(root)
    payload = {"profiles": data.get("profiles", {}), "default": data.get("default", "")}
    return atomic_write_json(path, payload, indent=2)


def _parse_kv_options(parts: list[str]) -> tuple[list[str], dict[str, Any]]:
    positional: list[str] = []
    opts: dict[str, Any] = {"flags": set()}
    idx = 0
    value_options = {"--name", "--host", "--port", "--mac", "--broadcast", "--token-env"}
    flag_options = {"--set-default", "--confirm", "--dry-run", "--allow-public"}
    while idx < len(parts):
        item = parts[idx]
        if item in value_options:
            idx += 1
            if idx >= len(parts):
                raise ValueError(f"{item} requires a value.")
            opts[item[2:].replace("-", "_")] = parts[idx]
        elif item in flag_options:
            opts["flags"].add(item[2:].replace("-", "_"))
        else:
            positional.append(item)
        idx += 1
    return positional, opts


def parse_remote_profile_args(text: str) -> dict[str, Any]:
    parts = shlex.split(str(text or ""))
    if not parts:
        return {"action": "list"}
    action = parts[0].lower()
    aliases = {"ls": "list", "status": "list", "show": "show", "get": "show", "rm": "remove", "delete": "remove", "del": "remove", "set-default": "default", "use": "default", "test": "health", "probe": "health", "check": "validate", "verify": "validate", "wol": "wake"}
    action = aliases.get(action, action)
    positional, opts = _parse_kv_options(parts[1:])
    flags = opts.get("flags", set())
    if action in {"list", "help"}:
        return {"action": action}
    if action in {"show", "remove", "default", "health", "validate", "wake"}:
        if not positional:
            raise ValueError(f"/remote-profile {action} requires a profile name.")
        return {"action": action, "name": _valid_profile_name(positional[0]), "dry_run": "dry_run" in flags, "confirm": "confirm" in flags, "allow_public": "allow_public" in flags}
    if action == "add":
        if not positional:
            raise ValueError("/remote-profile add requires a profile name.")
        name = _valid_profile_name(positional[0])
        host = str(opts.get("host") or (positional[1] if len(positional) > 1 else "")).strip()
        if not host:
            raise ValueError("/remote-profile add requires --host HOST or a host after the name.")
        port = int(opts.get("port") or DEFAULT_API_PORT)
        if not (1 <= port <= 65535):
            raise ValueError("Profile port must be between 1 and 65535.")
        mac = ""
        if opts.get("mac"):
            mac = normalize_mac(str(opts["mac"]))
        token_env = str(opts.get("token_env") or "NOVA_API_TOKEN").strip()
        if token_env and not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", token_env):
            raise ValueError("--token-env must be a valid environment variable name.")
        return {
            "action": "add",
            "name": name,
            "host": host,
            "port": port,
            "mac": mac,
            "broadcast": str(opts.get("broadcast") or "255.255.255.255").strip(),
            "token_env": token_env,
            "set_default": "set_default" in flags,
            "allow_public": "allow_public" in flags,
        }
    raise ValueError("Usage: /remote-profile list | add NAME --host HOST [--port PORT] [--mac MAC] [--broadcast IP] [--token-env VAR] [--set-default] | show NAME | validate NAME | health NAME | wake NAME --dry-run|--confirm | default NAME | remove NAME --confirm")


def _shell_quote(value: str) -> str:
    text = str(value or "")
    if not text:
        return '""'
    if re.fullmatch(r"[A-Za-z0-9_.:/-]+", text):
        return text
    return shlex.quote(text)


def build_remote_profile_wizard(root: Path | str | None = None, text: str = "") -> dict[str, Any]:
    """Build a read-only remote profile setup plan.

    The wizard deliberately returns commands to review/copy instead of writing
    config. This avoids accidental profile creation through chat/API flows while
    still reducing repeated risky typing of IP/MAC/port details.
    """
    root_path = _root(root)
    parts = shlex.split(str(text or ""))
    positional, opts = _parse_kv_options(parts)
    flags = opts.get("flags", set())
    name = str(opts.get("name") or (positional[0] if positional else "newpc")).strip()
    try:
        name = _valid_profile_name(name)
        name_ok = True
        name_error = ""
    except Exception as exc:
        name_ok = False
        name_error = str(exc)
        name = "newpc"
    host = str(opts.get("host") or (positional[1] if len(positional) > 1 else "")).strip()
    port_raw = str(opts.get("port") or DEFAULT_API_PORT)
    try:
        port = int(port_raw)
        port_ok = 1 <= port <= 65535
    except Exception:
        port = DEFAULT_API_PORT
        port_ok = False
    mac_raw = str(opts.get("mac") or "").strip()
    mac = ""
    mac_ok = True
    mac_error = ""
    if mac_raw:
        try:
            mac = normalize_mac(mac_raw)
        except Exception as exc:
            mac_ok = False
            mac_error = str(exc)
    broadcast = str(opts.get("broadcast") or "255.255.255.255").strip()
    token_env = str(opts.get("token_env") or "NOVA_API_TOKEN").strip()
    token_env_ok = bool(re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]{0,63}", token_env))
    host_check = _resolve_remote_host(host) if host else {"ok": False, "reason": "Host not supplied yet."}
    profiles = load_remote_profiles(root_path)
    exists = name in (profiles.get("profiles") or {})
    checks: list[dict[str, Any]] = []

    def add(field: str, ok: bool, detail: str, *, status: str | None = None, evidence: Any = None) -> None:
        checks.append({"field": field, "status": status or ("pass" if ok else "warn"), "ok": bool(ok), "detail": detail, "evidence": evidence})

    add("name", name_ok, "Profile name is valid." if name_ok else name_error, status="warn" if exists else None, evidence={"exists": exists})
    add("host", bool(host and host_check.get("ok") and (host_check.get("safe_default") or "allow_public" in flags)), "Host is private/Tailscale/localhost and safe by default." if host and host_check.get("safe_default") else ("Public host requires --allow-public and is not recommended." if host_check.get("ok") else str(host_check.get("reason"))), evidence=host_check)
    add("port", port_ok, f"Port {port} is valid." if port_ok else "Port must be between 1 and 65535.")
    add("mac", mac_ok and bool(mac), "MAC address is valid for Wake-on-LAN." if mac else "MAC not supplied; API health can still work, Wake-on-LAN profile wake will not.", status="pass" if mac_ok and mac else "warn", evidence={"normalized": mac})
    add("token_env", token_env_ok, f"Token env var name `{token_env}` is valid." if token_env_ok else "Token env var name is invalid.", evidence={"configured_now": bool(os.environ.get(token_env)) if token_env_ok else False})

    command_bits = ["/remote-profile", "add", name, "--host", host or "YOUR_TAILSCALE_IP", "--port", str(port)]
    if mac:
        command_bits += ["--mac", mac]
    else:
        command_bits += ["--mac", "AA:BB:CC:DD:EE:FF"]
    if broadcast:
        command_bits += ["--broadcast", broadcast]
    if token_env:
        command_bits += ["--token-env", token_env]
    if "set_default" in flags or not profiles.get("default"):
        command_bits.append("--set-default")
    if "allow_public" in flags:
        command_bits.append("--allow-public")
    add_command = " ".join(_shell_quote(item) for item in command_bits)
    commands = {
        "set_token_powershell": f'[Environment]::SetEnvironmentVariable("{token_env if token_env_ok else "NOVA_API_TOKEN"}", "paste-a-long-random-token", "User")',
        "add_profile": add_command,
        "show_profile": f"/remote-profile show {name}",
        "health_dry_run": f"/remote-profile health {name} --dry-run",
        "health_live": f"/remote-profile health {name}",
        "wake_dry_run": f"/remote-profile wake {name} --dry-run",
        "wake_confirm": f"/remote-profile wake {name} --confirm",
    }
    ok = all(check.get("status") == "pass" for check in checks if check["field"] in {"name", "host", "port", "token_env"})
    next_steps = [
        "Run `/remote-access-test` first; generate missing helpers with `/remote-access-scripts` if needed.",
        "Set NOVA_API_TOKEN before binding Nova API to a Tailscale IP.",
        "Review the suggested add-profile command, then run it when the host/MAC are correct.",
        "Test `/remote-profile health NAME --dry-run`, then live health, then Wake-on-LAN dry-run before `--confirm`.",
    ]
    return {"ok": ok, "workspace": str(root_path), "checks": checks, "commands": commands, "profile_exists": exists, "host_supplied": bool(host), "mac_supplied": bool(mac), "next_steps": next_steps}


def render_remote_profile_wizard(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Remote Profile Wizard",
        "",
        f"Workspace: `{payload.get('workspace')}`",
        f"Ready to save profile: **{payload.get('ok')}**",
        f"Profile already exists: **{payload.get('profile_exists')}**",
        "",
        "## Checks",
    ]
    for check in payload.get("checks", []):
        lines.append(f"- **{str(check.get('status', '')).upper()}** `{check.get('field')}` — {check.get('detail')}")
    lines += ["", "## Suggested commands"]
    for key, value in (payload.get("commands") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "## Next steps"]
    lines.extend(f"- {step}" for step in payload.get("next_steps", []))
    lines += ["", "Safety: this wizard is read-only. It does not create profiles, store tokens, send Wake-on-LAN packets, or probe the network."]
    return "\n".join(lines)


def validate_remote_profile(root: Path | str | None, name: str, *, allow_public: bool = False) -> dict[str, Any]:
    data = load_remote_profiles(root)
    profiles = data.get("profiles") or {}
    clean_name = _valid_profile_name(name)
    if clean_name not in profiles:
        return {"ok": False, "name": clean_name, "checks": [], "message": f"Remote profile `{clean_name}` was not found."}
    profile = profiles[clean_name]
    checks: list[dict[str, Any]] = []

    def add(name_: str, status: str, detail: str, *, evidence: Any = None) -> None:
        checks.append({"name": name_, "status": status, "detail": detail, "evidence": evidence})

    host_check = _resolve_remote_host(str(profile.get("host") or ""))
    if not host_check.get("ok"):
        add("host", "fail", str(host_check.get("reason") or "Host could not be resolved."), evidence=host_check)
    elif not host_check.get("safe_default") and not allow_public:
        add("host", "warn", "Profile host is public; use Tailscale/LAN/localhost or rerun validation with --allow-public only if intentional.", evidence=host_check)
    else:
        add("host", "pass", f"Host resolves as {host_check.get('category')}.", evidence=host_check)
    port = int(profile.get("port") or DEFAULT_API_PORT)
    add("port", "pass" if 1 <= port <= 65535 else "fail", f"Port: {port}")
    mac = str(profile.get("mac") or "")
    add("mac", "pass" if mac else "warn", "MAC is stored for Wake-on-LAN." if mac else "No MAC stored; profile health works but Wake-on-LAN will not.")
    token_env = str(profile.get("token_env") or "")
    if token_env:
        add("token_env", "pass" if os.environ.get(token_env) else "warn", f"Token env `{token_env}` {'is configured' if os.environ.get(token_env) else 'is not configured in this process'}.")
    else:
        add("token_env", "warn", "No token environment variable name stored.")
    counts = {"pass": 0, "warn": 0, "fail": 0}
    for check in checks:
        counts[check["status"]] = counts.get(check["status"], 0) + 1
    return {"ok": counts.get("fail", 0) == 0, "name": clean_name, "profile": profile, "checks": checks, "counts": counts, "message": f"Remote profile `{clean_name}` validation completed."}

def remote_profile_action(root: Path | str | None, text: str) -> dict[str, Any]:
    args = parse_remote_profile_args(text)
    action = args["action"]
    data = load_remote_profiles(root)
    profiles: dict[str, dict[str, Any]] = dict(data.get("profiles") or {})
    changed = False
    message = ""
    result: dict[str, Any] = {"ok": True, "action": action, "path": data.get("path"), "changed": False, "profiles": profiles, "default": data.get("default", "")}

    if action == "help":
        result["message"] = "Remote profiles store host/port/MAC/token-env names only; raw tokens are never saved."
        return result
    if action == "list":
        result["message"] = "Loaded remote profiles."
        return result

    name = args.get("name", "")
    if action == "add":
        resolved = _resolve_remote_host(args["host"])
        if not resolved.get("ok"):
            return {**result, "ok": False, "message": resolved.get("reason") or "Could not resolve profile host."}
        if not resolved.get("safe_default") and not args.get("allow_public"):
            return {**result, "ok": False, "message": "Refusing to save a public remote host by default. Use a Tailscale, LAN/private, or localhost address."}
        now = time.strftime("%Y-%m-%d %H:%M:%S")
        existing = profiles.get(name, {})
        profiles[name] = {
            "name": name,
            "host": args["host"],
            "port": int(args["port"]),
            "mac": args.get("mac", ""),
            "broadcast": args.get("broadcast") or "255.255.255.255",
            "token_env": args.get("token_env") or "NOVA_API_TOKEN",
            "created_at": existing.get("created_at") or now,
            "updated_at": now,
            "host_category": resolved.get("category"),
        }
        default = name if args.get("set_default") or not data.get("default") else data.get("default", "")
        save_remote_profiles({"profiles": profiles, "default": default}, root)
        return {**result, "changed": True, "profiles": profiles, "default": default, "profile": profiles[name], "message": f"Saved remote profile `{name}`. Raw tokens were not stored."}

    if name not in profiles:
        return {**result, "ok": False, "message": f"Remote profile `{name}` was not found. Use /remote-profile list."}
    profile = profiles[name]

    if action == "show":
        return {**result, "profile": profile, "message": f"Loaded remote profile `{name}`."}
    if action == "default":
        save_remote_profiles({"profiles": profiles, "default": name}, root)
        return {**result, "changed": True, "default": name, "profile": profile, "message": f"Default remote profile set to `{name}`."}
    if action == "remove":
        if not args.get("confirm"):
            return {**result, "ok": False, "profile": profile, "message": "Removing a remote profile requires --confirm."}
        profiles.pop(name, None)
        default = "" if data.get("default") == name else data.get("default", "")
        save_remote_profiles({"profiles": profiles, "default": default}, root)
        return {**result, "changed": True, "profiles": profiles, "default": default, "message": f"Removed remote profile `{name}`."}
    if action == "validate":
        validation = validate_remote_profile(root, name, allow_public=bool(args.get("allow_public")))
        return {**result, "ok": bool(validation.get("ok")), "profile": profile, "validation": validation, "message": validation.get("message", f"Remote profile `{name}` validation completed.")}
    if action == "health":
        token_env = str(profile.get("token_env") or "")
        token = os.environ.get(token_env, "") if token_env else ""
        health = probe_remote_api_health(
            str(profile.get("host") or ""),
            port=int(profile.get("port") or DEFAULT_API_PORT),
            token=token,
            allow_public=bool(args.get("allow_public")),
            dry_run=bool(args.get("dry_run")),
        )
        return {**result, "profile": profile, "health": health, "message": f"Remote profile `{name}` health probe completed."}
    if action == "wake":
        if not profile.get("mac"):
            return {**result, "ok": False, "profile": profile, "message": f"Remote profile `{name}` has no MAC address. Re-add it with --mac AA:BB:CC:DD:EE:FF."}
        if not args.get("dry_run") and not args.get("confirm"):
            return {**result, "ok": False, "profile": profile, "message": "Remote profile wake is dry-run by default unless you add --confirm."}
        wol = send_wake_on_lan(str(profile.get("mac")), broadcast=str(profile.get("broadcast") or "255.255.255.255"), dry_run=not bool(args.get("confirm")))
        return {**result, "profile": profile, "wake": wol, "message": f"Remote profile `{name}` wake {'sent' if args.get('confirm') else 'dry-run'} completed."}
    return {**result, "ok": False, "message": "Unknown remote profile action."}


def render_remote_profiles(payload: dict[str, Any]) -> str:
    lines = ["# Nova Remote Profiles", "", f"OK: **{payload.get('ok')}**", f"Changed: **{payload.get('changed', False)}**", f"Config: `{payload.get('path')}`"]
    if payload.get("message"):
        lines.append(f"Message: {payload.get('message')}")
    default = payload.get("default") or ""
    profiles = payload.get("profiles") or {}
    if payload.get("profile"):
        p = payload["profile"]
        lines += ["", "## Selected profile", f"- Name: `{p.get('name')}`", f"- Host: `{p.get('host')}`", f"- Port: `{p.get('port')}`", f"- MAC stored: **{bool(p.get('mac'))}**", f"- Broadcast: `{p.get('broadcast') or ''}`", f"- Token env: `{p.get('token_env') or 'not set'}`"]
    lines += ["", "## Profiles"]
    if not profiles:
        lines.append("- No profiles saved yet. Add one with `/remote-profile add newpc --host YOUR_TAILSCALE_IP --port 8767 --mac AA:BB:CC:DD:EE:FF --set-default`.")
    else:
        for name in sorted(profiles):
            p = profiles[name]
            marker = " (default)" if name == default else ""
            lines.append(f"- `{name}`{marker}: `{p.get('host')}`:`{p.get('port')}`; MAC stored: **{bool(p.get('mac'))}**; token env: `{p.get('token_env') or 'not set'}`")
    if payload.get("validation"):
        validation = payload["validation"]
        lines += ["", "## Profile validation", f"Validation OK: **{validation.get('ok')}**"]
        for check in validation.get("checks", []):
            lines.append(f"- **{str(check.get('status', '')).upper()}** `{check.get('name')}` — {check.get('detail')}")
    if payload.get("health"):
        lines += ["", "## Health probe", render_remote_api_health(payload["health"])]
    if payload.get("wake"):
        lines += ["", "## Wake result", render_wol_result(payload["wake"])]
    lines += ["", "## Safety notes", "- Raw tokens are never stored in remote profiles; only the environment variable name is saved.", "- Public hosts are blocked by default. Use Tailscale/LAN/localhost for routine access.", "- Real wake sends still require `--confirm` and working BIOS/NIC/router Wake-on-LAN settings."]
    return "\n".join(lines)


def normalize_mac(mac: str) -> str:
    compact = re.sub(r"[^0-9A-Fa-f]", "", str(mac or ""))
    if not _MAC_RE.fullmatch(compact):
        raise ValueError("MAC address must contain exactly 12 hex characters, for example AA:BB:CC:DD:EE:FF.")
    return ":".join(compact[i : i + 2].upper() for i in range(0, 12, 2))


def build_wol_magic_packet(mac: str) -> bytes:
    normalised = normalize_mac(mac)
    mac_bytes = bytes.fromhex(normalised.replace(":", ""))
    return b"\xff" * 6 + mac_bytes * 16


def send_wake_on_lan(
    mac: str,
    *,
    broadcast: str = "255.255.255.255",
    port: int = DEFAULT_WOL_PORT,
    dry_run: bool = False,
    timeout: float = 2.0,
) -> dict[str, Any]:
    normalised = normalize_mac(mac)
    try:
        port_int = int(port)
    except Exception as exc:
        raise ValueError("Wake-on-LAN port must be an integer.") from exc
    if not (1 <= port_int <= 65535):
        raise ValueError("Wake-on-LAN port must be between 1 and 65535.")
    packet = build_wol_magic_packet(normalised)
    payload = {
        "ok": True,
        "dry_run": bool(dry_run),
        "mac": normalised,
        "broadcast": str(broadcast or "255.255.255.255"),
        "port": port_int,
        "packet_bytes": len(packet),
        "sent_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    if dry_run:
        payload["message"] = "Dry run only: Wake-on-LAN packet was built but not sent."
        return payload
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
            sock.settimeout(float(timeout))
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            sent = sock.sendto(packet, (payload["broadcast"], port_int))
        payload["bytes_sent"] = sent
        payload["message"] = "Wake-on-LAN magic packet sent. This only works if BIOS/UEFI, Windows power settings, NIC and network path support it."
        return payload
    except Exception as exc:
        return {**payload, "ok": False, "error": repr(exc), "message": "Failed to send Wake-on-LAN packet."}


def _run_probe(cmd: list[str], *, timeout: int = 5) -> dict[str, Any]:
    try:
        cp = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout)
        return {"ok": cp.returncode == 0, "returncode": cp.returncode, "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip(), "cmd": cmd}
    except Exception as exc:
        return {"ok": False, "cmd": cmd, "error": repr(exc)}


def detect_tailscale() -> dict[str, Any]:
    exe = shutil.which("tailscale") or shutil.which("tailscale.exe")
    if not exe:
        return {"installed": False, "running": False, "ip4": "", "note": "tailscale executable was not found on PATH."}
    ip = _run_probe([exe, "ip", "-4"], timeout=5)
    return {
        "installed": True,
        "running": bool(ip.get("ok") and ip.get("stdout")),
        "ip4": str(ip.get("stdout") or "").splitlines()[0] if ip.get("stdout") else "",
        "probe": {k: v for k, v in ip.items() if k not in {"stdout", "stderr"}},
    }



_TAILSCALE_SHARED = ipaddress.ip_network("100.64.0.0/10")


def _resolve_remote_host(host: str) -> dict[str, Any]:
    """Resolve and classify a host for safe remote-access probes.

    Nova's remote API health check should help the user verify localhost,
    LAN/private VPN and Tailscale endpoints. By default it should not become a
    general-purpose public internet scanner when exposed through the API bridge.
    """
    raw = str(host or "").strip()
    if not raw:
        return {"ok": False, "host": raw, "reason": "Host is required."}
    if "://" in raw or "/" in raw or "?" in raw or "#" in raw:
        return {"ok": False, "host": raw, "reason": "Provide a host/IP only, not a full URL or path."}
    try:
        ip = ipaddress.ip_address(raw.strip("[]"))
        resolved = str(ip)
    except ValueError:
        try:
            resolved = socket.gethostbyname(raw)
            ip = ipaddress.ip_address(resolved)
        except Exception as exc:
            return {"ok": False, "host": raw, "reason": f"Could not resolve host: {exc}"}
    is_tailscale = ip in _TAILSCALE_SHARED
    safe = bool(ip.is_loopback or ip.is_private or ip.is_link_local or is_tailscale)
    category = "tailscale" if is_tailscale else ("loopback" if ip.is_loopback else ("private" if ip.is_private else ("link_local" if ip.is_link_local else "public")))
    return {"ok": True, "host": raw, "resolved_ip": resolved, "category": category, "safe_default": safe}


def parse_remote_api_health_args(text: str) -> dict[str, Any]:
    """Parse `/remote-api-health HOST [PORT]` arguments.

    Accepted examples:
    - `/remote-api-health 127.0.0.1 8767`
    - `/remote-api-health 100.101.102.103 --port 8767 --token abc`
    - `/remote-api-health http://127.0.0.1:8767 --dry-run`
    """
    parts = str(text or "").split()
    if not parts:
        raise ValueError("Usage: /remote-api-health HOST [PORT] [--token TOKEN|--env-token] [--timeout SECONDS] [--https] [--dry-run]")
    token: str | None = None
    timeout = 3.0
    scheme = "http"
    dry_run = False
    allow_public = False
    host = ""
    port = DEFAULT_API_PORT
    idx = 0
    positional: list[str] = []
    while idx < len(parts):
        item = parts[idx]
        if item == "--token":
            idx += 1
            if idx >= len(parts):
                raise ValueError("--token requires a value.")
            token = parts[idx]
        elif item == "--env-token":
            token = os.environ.get("NOVA_API_TOKEN") or ""
        elif item == "--timeout":
            idx += 1
            if idx >= len(parts):
                raise ValueError("--timeout requires seconds.")
            timeout = float(parts[idx])
        elif item == "--port":
            idx += 1
            if idx >= len(parts):
                raise ValueError("--port requires a value.")
            port = int(parts[idx])
        elif item == "--https":
            scheme = "https"
        elif item == "--http":
            scheme = "http"
        elif item == "--dry-run":
            dry_run = True
        elif item == "--allow-public":
            allow_public = True
        else:
            positional.append(item)
        idx += 1
    if positional:
        first = positional[0]
        parsed = urlparse(first if "://" in first else "")
        if parsed.scheme and parsed.netloc:
            scheme = parsed.scheme
            host = parsed.hostname or ""
            if parsed.port:
                port = parsed.port
            if parsed.path not in {"", "/", "/api/v1/health"}:
                raise ValueError("Remote API health accepts a host/root URL only; do not include arbitrary paths.")
        else:
            host = first
        if len(positional) >= 2:
            port = int(positional[1])
    if not host:
        raise ValueError("Remote API host is required.")
    if scheme not in {"http", "https"}:
        raise ValueError("Scheme must be http or https.")
    if not (1 <= int(port) <= 65535):
        raise ValueError("Port must be between 1 and 65535.")
    if not (0.2 <= float(timeout) <= 30):
        raise ValueError("Timeout must be between 0.2 and 30 seconds.")
    return {"host": host, "port": int(port), "token": token or "", "timeout": float(timeout), "scheme": scheme, "dry_run": dry_run, "allow_public": allow_public}


def _http_probe(url: str, *, token: str = "", timeout: float = 3.0) -> dict[str, Any]:
    headers = {"User-Agent": f"NovaRemoteProbe/{__version__}"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers, method="GET")
    try:
        with urllib.request.urlopen(req, timeout=float(timeout)) as resp:  # nosec B310 - URL is private-network guarded by probe_remote_api_health.
            body = resp.read(4096).decode("utf-8", errors="replace")
            return {"ok": 200 <= int(resp.status) < 300, "status": int(resp.status), "body_preview": body[:300]}
    except urllib.error.HTTPError as exc:
        body = exc.read(1024).decode("utf-8", errors="replace") if hasattr(exc, "read") else ""
        return {"ok": False, "status": int(exc.code), "error": str(exc), "body_preview": body[:300]}
    except Exception as exc:
        return {"ok": False, "status": None, "error": repr(exc), "body_preview": ""}


def probe_remote_api_health(
    host: str,
    *,
    port: int = DEFAULT_API_PORT,
    token: str = "",
    timeout: float = 3.0,
    scheme: str = "http",
    allow_public: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    """Check a Nova API endpoint without mutating remote state."""
    resolved = _resolve_remote_host(host)
    base = f"{scheme}://{host}:{int(port)}"
    payload: dict[str, Any] = {
        "ok": False,
        "dry_run": bool(dry_run),
        "base_url": base,
        "health_url": f"{base}/api/v1/health",
        "status_url": f"{base}/api/v1/status",
        "host_check": resolved,
        "token_supplied": bool(token),
        "timeout": float(timeout),
        "public_allowed": bool(allow_public),
    }
    if not resolved.get("ok"):
        payload["message"] = resolved.get("reason") or "Host resolution failed."
        return payload
    if not resolved.get("safe_default") and not allow_public:
        payload["message"] = "Refusing to probe a public host by default. Use a Tailscale, LAN/private, or localhost address."
        return payload
    if dry_run:
        payload["ok"] = True
        payload["message"] = "Dry run only: endpoint URLs and host safety were checked; no HTTP request was sent."
        return payload
    health = _http_probe(payload["health_url"], timeout=timeout)
    status = _http_probe(payload["status_url"], token=token, timeout=timeout)
    payload["health"] = health
    payload["status"] = status
    payload["ok"] = bool(health.get("ok"))
    if health.get("ok"):
        if status.get("status") == 401 and not token:
            payload["message"] = "Nova API health is reachable. Status route requires NOVA_API_TOKEN; rerun with --token or --env-token to verify authenticated status."
        elif status.get("ok"):
            payload["message"] = "Nova API health and authenticated/readable status are reachable."
        else:
            payload["message"] = "Nova API health is reachable, but status route did not return OK. Check token or server logs."
    else:
        payload["message"] = "Nova API health endpoint is not reachable. Check Tailscale/IP, host binding, port, firewall, and whether Nova API is running."
    return payload


def render_remote_api_health(payload: dict[str, Any]) -> str:
    host_check = payload.get("host_check") or {}
    lines = [
        "# Nova Remote API Health",
        "",
        f"Overall OK: **{payload.get('ok')}**",
        f"Dry run: **{payload.get('dry_run')}**",
        f"Endpoint: `{payload.get('base_url')}`",
        f"Resolved IP: `{host_check.get('resolved_ip') or 'not resolved'}` ({host_check.get('category') or 'unknown'})",
        f"Token supplied: **{payload.get('token_supplied')}**",
        f"Message: {payload.get('message', '')}",
    ]
    if payload.get("health"):
        health = payload["health"]
        lines += ["", "## `/api/v1/health`", f"- OK: **{health.get('ok')}**", f"- HTTP status: `{health.get('status')}`"]
        if health.get("error"):
            lines.append(f"- Error: `{health.get('error')}`")
    if payload.get("status"):
        status = payload["status"]
        lines += ["", "## `/api/v1/status`", f"- OK: **{status.get('ok')}**", f"- HTTP status: `{status.get('status')}`"]
        if status.get("status") == 401:
            lines.append("- Auth: token required or token rejected.")
        if status.get("error"):
            lines.append(f"- Error: `{status.get('error')}`")
    lines += [
        "",
        "## Next checks",
        "- Start Nova API on the target PC with `start_nova_remote_api.ps1`.",
        "- Use the Tailscale IPv4 address, not a public IP.",
        "- Keep `NOVA_API_TOKEN` set before binding beyond localhost.",
    ]
    return "\n".join(lines)

def _env_token_status() -> dict[str, Any]:
    token = os.environ.get("NOVA_API_TOKEN", "")
    return {
        "configured": bool(token),
        "source": "NOVA_API_TOKEN environment variable" if token else "not configured",
        "length": len(token),
        "masked": (token[:4] + "…" + token[-4:]) if len(token) >= 12 else "",
    }



def build_remote_access_preflight(root: Path | str | None = None) -> dict[str, Any]:
    """Return a read-only remote-access readiness checklist.

    This deliberately avoids changing system settings, opening network sockets or
    installing services. Hardware/BIOS/Wake-on-LAN support cannot be proven from
    Python, so those checks are reported as manual instead of pretending Nova can
    verify them remotely.
    """
    root_path = _root(root)
    token = _env_token_status()
    tailscale = detect_tailscale()
    checks: list[dict[str, Any]] = []

    def add(name: str, status: str, detail: str, *, evidence: Any = None) -> None:
        checks.append({"name": name, "status": status, "detail": detail, "evidence": evidence})

    add("workspace", "pass" if root_path.exists() else "fail", f"Workspace path: {root_path}")
    app_py = root_path / "app.py"
    add("nova_launcher", "pass" if app_py.exists() else "fail", "app.py is required for the remote API launcher.", evidence=str(app_py))

    script_paths = {
        "remote_api_ps1": root_path / "start_nova_remote_api.ps1",
        "remote_api_bat": root_path / "start_nova_remote_api.bat",
        "startup_task_helper": root_path / "install_nova_remote_startup_task.ps1",
        "setup_guide": root_path / "docs" / REMOTE_GUIDE_FILE,
    }
    missing = [name for name, path in script_paths.items() if not path.exists()]
    add(
        "remote_assets",
        "pass" if not missing else "warn",
        "Remote helper scripts/docs are present." if not missing else "Remote helper scripts/docs are missing; run /remote-access-scripts.",
        evidence={name: str(path) for name, path in script_paths.items()},
    )

    add(
        "api_dependency",
        "pass" if importlib.util.find_spec("fastapi") and importlib.util.find_spec("uvicorn") else "warn",
        "FastAPI and Uvicorn are available for the optional Nova API bridge." if importlib.util.find_spec("fastapi") and importlib.util.find_spec("uvicorn") else "FastAPI/Uvicorn are optional but missing; remote desktop still works, API bridge will not.",
    )

    add(
        "api_token",
        "pass" if token.get("configured") else "warn",
        "NOVA_API_TOKEN is set for remote API use." if token.get("configured") else "NOVA_API_TOKEN is not set; keep Nova API bound to 127.0.0.1 until it is configured.",
        evidence={k: v for k, v in token.items() if k != "masked"} | ({"masked": token.get("masked")} if token.get("masked") else {}),
    )

    profile_data = load_remote_profiles(root_path)
    profile_count = len(profile_data.get("profiles") or {})
    add(
        "remote_profiles",
        "pass" if profile_count else "warn",
        f"{profile_count} remote profile(s) saved." if profile_count else "No saved remote profiles yet; add one after you know the Tailscale IP/MAC.",
        evidence={"path": profile_data.get("path"), "default": profile_data.get("default", ""), "count": profile_count},
    )

    add(
        "tailscale",
        "pass" if tailscale.get("running") else ("warn" if tailscale.get("installed") else "manual"),
        "Tailscale is installed and has an IPv4 address." if tailscale.get("running") else ("Tailscale is installed but no IPv4 was detected." if tailscale.get("installed") else "Tailscale was not detected on PATH; install/sign in on PC, phone and laptop for safest access."),
        evidence=tailscale,
    )

    system = platform.system() or "Unknown"
    add(
        "remote_desktop_host",
        "manual",
        "On Windows 11 Pro, enable Settings > System > Remote Desktop. On Windows Home, use Chrome Remote Desktop instead." if system == "Windows" else "Remote Desktop host readiness can only be checked on the Windows PC itself.",
        evidence={"platform": system},
    )
    add(
        "wake_on_lan_hardware",
        "manual",
        "Verify BIOS/UEFI Wake-on-LAN or PCIe wake, Ethernet NIC magic-packet wake, and router/subnet broadcast behaviour on the real PC.",
    )

    counts: dict[str, int] = {"pass": 0, "warn": 0, "fail": 0, "manual": 0}
    for check in checks:
        counts[check["status"]] = counts.get(check["status"], 0) + 1
    ok = counts.get("fail", 0) == 0
    next_steps: list[str] = []
    if missing:
        next_steps.append("Run /remote-access-scripts to generate the helper scripts and setup guide.")
    if not token.get("configured"):
        next_steps.append("Set NOVA_API_TOKEN before binding the Nova API to a Tailscale IP.")
    if not tailscale.get("running"):
        next_steps.append("Install/sign in to Tailscale on the new PC, phone and laptop, then check `tailscale ip -4`.")
    if not profile_count:
        next_steps.append("After you know the Tailscale IP/MAC, save a profile with `/remote-profile add newpc --host YOUR_TAILSCALE_IP --port 8767 --mac AA:BB:CC:DD:EE:FF --set-default`.")
    next_steps.append("Test remote desktop first; use the API bridge only after desktop access and token checks work.")
    return {"ok": ok, "workspace": str(root_path), "checks": checks, "counts": counts, "next_steps": next_steps}


def render_remote_access_preflight(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Remote Access Preflight",
        "",
        f"Workspace: `{payload.get('workspace')}`",
        f"Overall OK: **{payload.get('ok')}**",
        "",
        "## Checks",
    ]
    icon = {"pass": "PASS", "warn": "WARN", "fail": "FAIL", "manual": "MANUAL"}
    for check in payload.get("checks", []):
        status = str(check.get("status", "unknown"))
        lines.append(f"- **{icon.get(status, status.upper())}** `{check.get('name')}` — {check.get('detail')}")
    lines += ["", "## Summary"]
    counts = payload.get("counts") or {}
    for key in ("pass", "warn", "fail", "manual"):
        lines.append(f"- {key}: `{counts.get(key, 0)}`")
    lines += ["", "## Next steps"]
    lines.extend(f"- {step}" for step in payload.get("next_steps", []))
    return "\n".join(lines)

def build_remote_access_status(root: Path | str | None = None) -> dict[str, Any]:
    root_path = _root(root)
    return {
        "ok": True,
        "product": ASSISTANT_NAME,
        "version": __version__,
        "workspace": str(root_path),
        "recommended_mode": "Tailscale VPN + Windows Remote Desktop or Chrome Remote Desktop + optional token-protected Nova FastAPI bridge",
        "default_api": {"host": "127.0.0.1", "port": DEFAULT_API_PORT, "remote_safe_host": "Tailscale IPv4 only"},
        "token": _env_token_status(),
        "tailscale": detect_tailscale(),
        "launchers": {
            "remote_api_ps1": str(root_path / "start_nova_remote_api.ps1"),
            "remote_api_bat": str(root_path / "start_nova_remote_api.bat"),
            "startup_task_helper": str(root_path / "install_nova_remote_startup_task.ps1"),
        },
        "docs": str(root_path / "docs" / REMOTE_GUIDE_FILE),
        "security_warnings": [
            "Do not port-forward Nova or Windows RDP directly to the public internet.",
            "Use Tailscale or another private VPN for off-network access.",
            "Set NOVA_API_TOKEN before exposing Nova's API beyond localhost.",
            "Wake-on-LAN starts a powered-but-sleeping PC only when motherboard, NIC, Windows and router support it.",
        ],
    }


def render_remote_access_status(payload: dict[str, Any]) -> str:
    tailscale = payload.get("tailscale", {}) or {}
    token = payload.get("token", {}) or {}
    lines = [
        "# Nova Remote Access Status",
        "",
        f"Workspace: `{payload.get('workspace')}`",
        f"Recommended mode: **{payload.get('recommended_mode')}**",
        "",
        "## API",
        f"- Local default: `http://{payload.get('default_api', {}).get('host')}:{payload.get('default_api', {}).get('port')}`",
        f"- Remote-safe host: **{payload.get('default_api', {}).get('remote_safe_host')}**",
        f"- `NOVA_API_TOKEN` configured: **{token.get('configured')}**",
    ]
    if token.get("configured"):
        lines.append(f"- Token source: {token.get('source')} ({token.get('length')} chars, masked `{token.get('masked')}`)")
    else:
        lines.append("- Token source: not configured; keep API on `127.0.0.1` until a token is set.")
    lines += [
        "",
        "## Tailscale probe",
        f"- Installed: **{tailscale.get('installed')}**",
        f"- Running/IP available: **{tailscale.get('running')}**",
        f"- IPv4: `{tailscale.get('ip4') or 'not detected'}`",
        "",
        "## Launchers/docs",
    ]
    for key, value in (payload.get("launchers") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines.append(f"- Setup guide: `{payload.get('docs')}`")
    lines += ["", "## Safety warnings"]
    lines.extend(f"- {item}" for item in payload.get("security_warnings", []))
    return "\n".join(lines)


def build_remote_access_plan(root: Path | str | None = None) -> dict[str, Any]:
    root_path = _root(root)
    return {
        "ok": True,
        "workspace": str(root_path),
        "architecture": "phone/laptop -> Tailscale private network -> Remote Desktop/Chrome Remote Desktop -> Nova on new PC; optional token-protected Nova API for command/status calls",
        "phases": [
            {
                "name": "Prepare new PC",
                "steps": [
                    "Use Windows 11 Pro if you want Microsoft Remote Desktop host support; Windows Home can still use Chrome Remote Desktop.",
                    "Enable BIOS/UEFI Wake-on-LAN/PCIe wake and disable ErP/deep power-off if needed.",
                    "In Windows Device Manager, enable the network adapter options that allow the device/magic packet to wake the computer.",
                    "Use Ethernet for the new PC where possible; Wake-on-LAN over Wi-Fi is unreliable on many systems.",
                ],
            },
            {
                "name": "Private remote network",
                "steps": [
                    "Install Tailscale on the new PC, phone and laptop, then sign in to the same tailnet.",
                    "Confirm the new PC has a Tailscale IPv4 address with `tailscale ip -4`.",
                    "Do not expose RDP or Nova API through router port forwarding.",
                ],
            },
            {
                "name": "Remote desktop",
                "steps": [
                    "For Windows 11 Pro, enable Settings > System > Remote Desktop and connect from phone/laptop with the Microsoft Remote Desktop client using the Tailscale IP.",
                    "For Windows Home or simpler phone access, install Chrome Remote Desktop host and set up unattended access with a PIN.",
                ],
            },
            {
                "name": "Nova launch",
                "steps": [
                    "Run `/remote-access-scripts` in Nova to write the helper launchers and setup guide.",
                    "Start Nova locally with `START_NOVA_HERE.bat` for GUI or `start_nova_remote_api.ps1` for the optional API bridge.",
                    "For remote API access, set `NOVA_API_TOKEN` and bind to the Tailscale IPv4 address only.",
                ],
            },
            {
                "name": "Testing",
                "steps": [
                    "Run `/remote-access-status` to check local script/config status.",
                    "Run `/remote-wake AA:BB:CC:DD:EE:FF --dry-run` first to verify the magic packet build without sending.",
                    "From laptop/phone on Tailscale, test RDP/Chrome Remote Desktop, then run `/remote-api-health YOUR_TAILSCALE_IP 8767 --token YOUR_TOKEN` or open the API health endpoint.",
                ],
            },
        ],
    }


def render_remote_access_plan(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Remote PC Access Plan",
        "",
        f"Architecture: **{payload.get('architecture')}**",
        "",
    ]
    for idx, phase in enumerate(payload.get("phases", []), start=1):
        lines.append(f"## {idx}. {phase.get('name')}")
        for step in phase.get("steps", []):
            lines.append(f"- {step}")
        lines.append("")
    return "\n".join(lines).rstrip()


def _launcher_ps1() -> str:
    return r'''param(
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8767,
    [switch]$RequireToken
)

$ErrorActionPreference = "Stop"
Set-Location -LiteralPath $PSScriptRoot

if ($HostAddress -ne "127.0.0.1" -and $HostAddress -ne "localhost") {
    if (-not $env:NOVA_API_TOKEN) {
        Write-Host "Refusing to expose Nova API beyond localhost without NOVA_API_TOKEN." -ForegroundColor Red
        Write-Host "Set a user environment token first, for example:" -ForegroundColor Yellow
        Write-Host '  [Environment]::SetEnvironmentVariable("NOVA_API_TOKEN", "paste-a-long-random-token", "User")'
        exit 2
    }
}

if ($RequireToken -and -not $env:NOVA_API_TOKEN) {
    Write-Host "NOVA_API_TOKEN is required but not set." -ForegroundColor Red
    exit 2
}

Write-Host "Starting Nova API on http://$HostAddress`:$Port" -ForegroundColor Cyan
Write-Host "Use Tailscale/VPN only. Do not router-port-forward this API." -ForegroundColor Yellow
$VenvPython = Join-Path $PSScriptRoot ".venv\Scripts\python.exe"
if (Test-Path $VenvPython) {
    & $VenvPython app.py --api --host $HostAddress --port $Port
} else {
    py -3 app.py --api --host $HostAddress --port $Port
}
'''


def _launcher_bat() -> str:
    return r'''@echo off
setlocal
cd /d "%~dp0"
REM Keep the default localhost-only. For Tailscale use PowerShell:
REM powershell -ExecutionPolicy Bypass -File .\\start_nova_remote_api.ps1 -HostAddress YOUR_TAILSCALE_IP -Port 8767
powershell -ExecutionPolicy Bypass -File "%~dp0start_nova_remote_api.ps1" -HostAddress 127.0.0.1 -Port 8767
'''


def _startup_task_ps1() -> str:
    return r'''param(
    [string]$TaskName = "Nova Remote API",
    [string]$HostAddress = "127.0.0.1",
    [int]$Port = 8767
)

$ErrorActionPreference = "Stop"
$Root = $PSScriptRoot
$Script = Join-Path $Root "start_nova_remote_api.ps1"
if (!(Test-Path $Script)) { throw "Missing $Script. Run /remote-access-scripts first." }

if ($HostAddress -ne "127.0.0.1" -and $HostAddress -ne "localhost" -and -not $env:NOVA_API_TOKEN) {
    throw "Refusing remote bind without NOVA_API_TOKEN. Set it as a User environment variable first."
}

$Action = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-ExecutionPolicy Bypass -File `"$Script`" -HostAddress $HostAddress -Port $Port"
$Trigger = New-ScheduledTaskTrigger -AtLogOn
$Settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName $TaskName -Action $Action -Trigger $Trigger -Settings $Settings -Description "Start Nova API bridge at user logon. Use only on localhost or Tailscale with NOVA_API_TOKEN." -Force | Out-Null
Write-Host "Installed scheduled task: $TaskName" -ForegroundColor Green
Write-Host "Test with: Get-ScheduledTask -TaskName '$TaskName'" -ForegroundColor Cyan
'''


def _setup_markdown() -> str:
    return textwrap.dedent(
        """
        # Nova remote PC access setup

        ## Safe architecture

        Use this route:

        `phone/laptop -> Tailscale private network -> Remote Desktop or Chrome Remote Desktop -> new PC -> Nova`

        Optional advanced route:

        `phone/laptop -> Tailscale private network -> token-protected Nova FastAPI bridge`

        Do **not** expose Windows Remote Desktop or Nova's API through router port forwarding.

        ## New PC setup

        1. Plug the new PC into Ethernet if possible.
        2. Enable Wake-on-LAN / PCIe device wake in BIOS or UEFI.
        3. In Windows Device Manager, open the Ethernet adapter, then enable wake options such as allowing the device or magic packet to wake the computer.
        4. Install Tailscale on the new PC, phone and laptop, and sign in to the same tailnet.
        5. For Windows 11 Pro, enable Settings > System > Remote Desktop. Use the Tailscale IPv4 address when connecting.
        6. For Windows Home or easier phone use, set up Chrome Remote Desktop unattended access.

        ## Nova API setup

        Local-only default:

        ```powershell
        .\\start_nova_remote_api.ps1
        ```

        Tailscale-only remote API:

        ```powershell
        [Environment]::SetEnvironmentVariable("NOVA_API_TOKEN", "use-a-long-random-token", "User")
        # Open a new PowerShell window after setting the User environment variable.
        .\\start_nova_remote_api.ps1 -HostAddress YOUR_TAILSCALE_IP -Port 8767 -RequireToken
        ```

        Test from the laptop while connected to Tailscale:

        ```powershell
        curl http://YOUR_TAILSCALE_IP:8767/api/v1/health
        curl -H "Authorization: Bearer YOUR_TOKEN" http://YOUR_TAILSCALE_IP:8767/api/v1/status
        ```

        ## Useful Nova commands

        - `/remote-access-plan`
        - `/remote-access-status`
        - `/remote-access-scripts`
        - `/remote-access-test`
        - `/remote-api-health YOUR_TAILSCALE_IP 8767 --token YOUR_TOKEN`
        - `/remote-profile-wizard --host YOUR_TAILSCALE_IP --mac AA:BB:CC:DD:EE:FF`
        - `/remote-profile add newpc --host YOUR_TAILSCALE_IP --port 8767 --mac AA:BB:CC:DD:EE:FF --set-default`
        - `/remote-profile validate newpc`
        - `/remote-profile health newpc`
        - `/remote-profile wake newpc --dry-run`
        - `/remote-profile wake newpc --confirm`
        - `/remote-wake AA:BB:CC:DD:EE:FF --dry-run`
        - `/remote-wake AA:BB:CC:DD:EE:FF --confirm`

        ## Troubleshooting

        - Wake-on-LAN usually works best over Ethernet and from sleep/hibernate, not after a full shutdown on every motherboard.
        - If RDP connects on LAN but not away from home, use Tailscale and connect to the Tailscale IPv4, not your public IP.
        - If Nova API is remote, set `NOVA_API_TOKEN` and bind to the Tailscale IP only.
        - If Windows sleeps too aggressively, adjust power settings so the network adapter can wake the PC.
        """
    ).strip() + "\n"


def write_remote_access_assets(root: Path | str | None = None) -> dict[str, Any]:
    root_path = _root(root)
    docs_dir = root_path / "docs"
    docs_dir.mkdir(exist_ok=True)
    paths = {
        "remote_api_ps1": root_path / "start_nova_remote_api.ps1",
        "remote_api_bat": root_path / "start_nova_remote_api.bat",
        "startup_task_helper": root_path / "install_nova_remote_startup_task.ps1",
        "setup_guide": docs_dir / REMOTE_GUIDE_FILE,
        "status_json": root_path / "logs" / REMOTE_STATUS_FILE,
    }
    atomic_write_text(paths["remote_api_ps1"], _launcher_ps1(), encoding="utf-8")
    atomic_write_text(paths["remote_api_bat"], _launcher_bat(), encoding="utf-8")
    atomic_write_text(paths["startup_task_helper"], _startup_task_ps1(), encoding="utf-8")
    atomic_write_text(paths["setup_guide"], _setup_markdown(), encoding="utf-8")
    status = build_remote_access_status(root_path)
    atomic_write_json(paths["status_json"], status, ensure_ascii=True)
    return {"ok": True, "written": {key: str(value) for key, value in paths.items()}, "status": status}


def render_remote_access_assets(payload: dict[str, Any]) -> str:
    lines = ["# Nova Remote Access Assets", "", "Written files:"]
    for key, value in (payload.get("written") or {}).items():
        lines.append(f"- {key}: `{value}`")
    lines += ["", "Next: read `docs/NOVA_REMOTE_ACCESS_SETUP.md`, run `/remote-access-test`, then run `/remote-profile-wizard --host YOUR_TAILSCALE_IP --mac AA:BB:CC:DD:EE:FF` before saving a profile."]
    return "\n".join(lines)


def render_wol_result(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Remote Wake Result",
        "",
        f"OK: **{payload.get('ok')}**",
        f"Dry run: **{payload.get('dry_run')}**",
        f"MAC: `{payload.get('mac')}`",
        f"Broadcast: `{payload.get('broadcast')}`",
        f"Port: `{payload.get('port')}`",
        f"Packet bytes: `{payload.get('packet_bytes')}`",
        f"Message: {payload.get('message', '')}",
    ]
    if payload.get("error"):
        lines.append(f"Error: `{payload.get('error')}`")
    return "\n".join(lines)


def parse_remote_wake_args(text: str) -> dict[str, Any]:
    parts = str(text or "").split()
    dry_run = "--dry-run" in parts or "--test" in parts
    confirm = "--confirm" in parts or "confirm" in parts
    filtered = [p for p in parts if p not in {"--dry-run", "--test", "--confirm", "confirm"}]
    if not filtered:
        raise ValueError("Usage: /remote-wake AA:BB:CC:DD:EE:FF [broadcast] [port] [--dry-run|--confirm]")
    mac = filtered[0]
    broadcast = filtered[1] if len(filtered) >= 2 else "255.255.255.255"
    port = int(filtered[2]) if len(filtered) >= 3 else DEFAULT_WOL_PORT
    return {"mac": mac, "broadcast": broadcast, "port": port, "dry_run": dry_run, "confirm": confirm}
