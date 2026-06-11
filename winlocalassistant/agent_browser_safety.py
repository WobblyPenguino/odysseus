"""Safety helpers for future Agent Browser integration.

This module is intentionally pure. It does not install Agent Browser, launch a
browser, connect to Chrome, browse the web, or execute shell commands.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from urllib.parse import urlparse
from typing import Mapping


LOCALHOST_HOSTS = {"localhost", "127.0.0.1", "::1"}


@dataclass(frozen=True)
class AgentBrowserSafetyPolicy:
    allowed_hosts: tuple[str, ...] = ("localhost", "127.0.0.1", "::1")
    read_only_first: bool = True
    allow_existing_profile: bool = False
    allow_saved_state: bool = False
    allow_external_domains: bool = False
    require_manual_install: bool = True
    require_manual_approval_for_actions: bool = True
    max_output_chars: int = 12000

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


def default_agent_browser_safety_policy() -> AgentBrowserSafetyPolicy:
    """Return Nova's safest default policy for Agent Browser experiments."""

    return AgentBrowserSafetyPolicy()


def summarise_agent_browser_policy(policy: AgentBrowserSafetyPolicy | None = None) -> str:
    """
    Return a stable human‑readable summary of the given safety policy.
    The summary mentions localhost‑only defaults, read‑only‑first behaviour,
    manual install requirement, and manual approval for action commands.
    """
    policy = policy or default_agent_browser_safety_policy()
    parts: list[str] = []

    # localhost‑only defaults
    if set(policy.allowed_hosts) == {"localhost", "127.0.0.1", "::1"} and not policy.allow_external_domains:
        parts.append("Default: only localhost hosts are allowed.")
    else:
        parts.append(f"Allowed hosts: {', '.join(policy.allowed_hosts)}")

    # read‑only‑first behaviour
    if policy.read_only_first:
        parts.append("Read-only commands run first.")
    else:
        parts.append("Action commands may run before evidence collection.")

    # manual install requirement
    if policy.require_manual_install:
        parts.append("Manual installation of Agent Browser is required.")
    else:
        parts.append("Agent Browser can be installed automatically.")

    # manual approval for action commands
    if policy.require_manual_approval_for_actions:
        parts.append("Action commands require manual approval.")
    else:
        parts.append("Action commands are allowed without manual approval.")

    return " ".join(parts)


def normalise_agent_browser_host(url: str) -> str:
    """Extract a lowercase host from a URL-ish string."""

    raw = (url or "").strip()
    if not raw:
        return ""

    parsed = urlparse(raw if "://" in raw else f"http://{raw}")
    return (parsed.hostname or "").lower()


def is_agent_browser_url_allowed(url: str, policy: AgentBrowserSafetyPolicy | None = None) -> bool:
    """Return True only when the URL is allowed by the safety policy."""

    policy = policy or default_agent_browser_safety_policy()
    host = normalise_agent_browser_host(url)

    if not host:
        return False
    if policy.allow_external_domains:
        return True
    return host in set(policy.allowed_hosts)


def safe_agent_browser_readonly_commands() -> tuple[str, ...]:
    """Commands Nova may plan first because they collect evidence without interaction."""

    return (
        "doctor",
        "snapshot",
        "screenshot",
        "get title",
        "get url",
        "get text",
        "is visible",
    )


def unsafe_agent_browser_action_commands() -> tuple[str, ...]:
    """Commands that should require manual approval in Nova before use."""

    return (
        "click",
        "dblclick",
        "fill",
        "type",
        "press",
        "keyboard",
        "upload",
        "drag",
        "eval",
        "connect",
        "chat",
    )


def classify_agent_browser_command(command: str) -> str:
    """
    Classify an Agent Browser command string.

    Returns:
        - 'readonly' for known evidence commands,
        - 'requires-approval' for known action/interaction commands,
        - 'unknown' for any other command.
    """
    cmd = command.strip().lower()
    if cmd in safe_agent_browser_readonly_commands():
        return "readonly"
    if cmd in unsafe_agent_browser_action_commands():
        return "requires-approval"
    return "unknown"


def build_agent_browser_localhost_plan(url: str) -> dict[str, object]:
    """Build a safe, read‑only first validation plan for a localhost URL."""

    policy = default_agent_browser_safety_policy()
    allowed = is_agent_browser_url_allowed(url, policy)
    commands: list[list[str]] = []

    if allowed:
        commands = [
            ["agent-browser", "open", url],
            ["agent-browser", "snapshot"],
            ["agent-browser", "screenshot", "--annotate"],
            ["agent-browser", "get", "title"],
            ["agent-browser", "get", "url"],
        ]

    return {
        "allowed": allowed,
        "url": url,
        "policy": policy.to_dict(),
        "commands": commands,
        "blocked_reason": "" if allowed else "URL is outside Nova's default localhost-only Agent Browser policy.",
    }


def render_agent_browser_plan_markdown(plan: Mapping[str, object]) -> str:
    """
    Render a markdown representation of an agent‑browser plan.

    The output includes the URL, whether it is allowed or blocked,
    any blocked reason, and a list of planned commands (without executing them).
    """
    lines = []
    lines.append("## Agent Browser Plan")
    lines.append("")
    url = plan.get("url", "")
    lines.append(f"- **URL**: `{url}`")

    status = "Allowed" if plan.get("allowed") else "Blocked"
    lines.append(f"- **Status**: {status}")

    if not plan.get("allowed"):
        blocked_reason = plan.get("blocked_reason", "")
        if blocked_reason:
            lines.append(f"- **Reason**: {blocked_reason}")

    commands = plan.get("commands", [])
    if commands:
        lines.append("")
        lines.append("- Commands:")
        for cmd in commands:
            # Each command is a list of strings
            lines.append(f"  - `{ ' '.join(cmd) }`")

    return "\n".join(lines)
