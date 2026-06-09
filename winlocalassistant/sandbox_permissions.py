from __future__ import annotations

import logging
import re
import time
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, read_json_file

PENDING_SANDBOX_PERMISSION_PATH = APP_DIR / "pending_sandbox_permission.json"
PENDING_PERMISSION_TTL_SEC = 600

APPROVAL_WORDS = {"yes", "y", "approve", "approved", "green light", "go ahead", "ok", "okay", "true", "1"}
DENIAL_WORDS = {"no", "n", "cancel", "deny", "stop", "false", "0"}


def sandbox_command_targets_network(command: str) -> bool:
    """Best-effort detection for commands that target network resources.

    Version/help checks are handled by the sandbox command policy. This function
    is intentionally conservative: obvious URLs, public IP addresses, and common
    scanner/downloader commands aimed at hostnames require explicit network
    approval before Nova enables bridge networking.
    """
    low = (command or "").lower().strip()
    if not low:
        return False
    if re.search(r"https?://|www\.", low):
        return True
    for match in re.findall(r"\b\d{1,3}(?:\.\d{1,3}){3}\b", low):
        parts = match.split(".")
        try:
            nums = [int(p) for p in parts]
        except ValueError:
            continue
        if any(n > 255 for n in nums):
            continue
        private = (
            nums[0] == 10
            or nums[0] == 127
            or (nums[0] == 192 and nums[1] == 168)
            or (nums[0] == 172 and 16 <= nums[1] <= 31)
            or (nums[0] == 169 and nums[1] == 254)
        )
        if not private:
            return True
    if re.search(r"\b(nmap|nikto|whois|curl|wget|sqlmap|whatweb|gobuster|ffuf)\b", low):
        for host in re.findall(r"\b[a-z0-9-]+(?:\.[a-z0-9-]+)+\b", low):
            if not re.fullmatch(r"\d{1,3}(?:\.\d{1,3}){3}", host):
                return True
    return False


def create_pending_sandbox_permission(profile: str, command: str, required: list[str], policy: dict[str, Any]) -> dict[str, Any]:
    now = time.time()
    pending = {
        "profile": str(profile or "kali"),
        "command": str(command or ""),
        "required": list(dict.fromkeys(required or [])),
        "policy": policy or {},
        "created_at": now,
        "expires_at": now + PENDING_PERMISSION_TTL_SEC,
    }
    atomic_write_json(PENDING_SANDBOX_PERMISSION_PATH, pending, ensure_ascii=True)
    return pending


def load_pending_sandbox_permission() -> dict[str, Any]:
    pending = read_json_file(PENDING_SANDBOX_PERMISSION_PATH, {}, expected_type=dict, quarantine=True)
    if not pending or not pending.get("command"):
        return {}
    if float(pending.get("expires_at") or 0) <= time.time():
        clear_pending_sandbox_permission()
        return {}
    return pending


def clear_pending_sandbox_permission() -> None:
    try:
        Path(PENDING_SANDBOX_PERMISSION_PATH).unlink(missing_ok=True)
    except Exception:
        logging.getLogger(__name__).debug("Failed to clear pending sandbox permission file", exc_info=True)


def render_pending_sandbox_permission_markdown(pending: dict[str, Any] | None = None) -> str:
    pending = pending or load_pending_sandbox_permission()
    if not pending:
        return "No sandbox permission request is pending."
    required = list(pending.get("required") or [])
    policy = pending.get("policy") or {}
    reasons = policy.get("reasons") or []
    warnings = policy.get("warnings") or []
    expires_at = float(pending.get("expires_at") or 0)
    remaining = max(0, int(expires_at - time.time()))
    lines = [
        "## Pending sandbox permission",
        f"Profile: `{pending.get('profile', '')}`",
        f"Command: `{pending.get('command', '')}`",
        f"Expires in: **{remaining}s**",
        "",
        "Required permission:",
    ]
    for item in required:
        if item == "authorized_lab":
            lines.append("- Authorised Kali lab mode for an owned/local lab or explicitly permitted target.")
        elif item == "network":
            lines.append("- Sandbox network access for this command.")
        else:
            lines.append(f"- {item}")
    if reasons:
        lines += ["", "Policy reasons:"] + [f"- {r}" for r in reasons]
    if warnings:
        lines += ["", "Policy warnings:"] + [f"- {w}" for w in warnings]
    lines += [
        "",
        "Approve with `/sandbox-approve yes` or cancel with `/sandbox-cancel`.",
    ]
    return "\n".join(lines)
