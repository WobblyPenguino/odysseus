from __future__ import annotations

import re
from pathlib import Path

DANGEROUS_PATTERNS = [
    r"\bformat\b",
    r"\bdiskpart\b",
    r"\bbcdedit\b",
    r"\bshutdown\b",
    r"\brestart-computer\b",
    r"\bstop-computer\b",
    r"\bremove-item\b.*\b-recurse\b.*\b-force\b.*(c:\\|/|\$env:userprofile)",
    r"\brd\b\s+/s\s+/q\s+(c:\\|\\|\.)",
    r"\bdel\b\s+/s\s+/q\s+(c:\\|\\|\.)",
    r"\bset-executionpolicy\b\s+unrestricted",
    r"\bdisable-windowsdefender\b",
    r"\badd-mppreference\b.*exclusion",
]


def is_dangerous_command(command: str) -> tuple[bool, str]:
    lowered = command.lower().strip()
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, lowered):
            return True, f"Blocked by safety rule: {pattern}"
    return False, ""


def resolve_inside_workspace(workspace: Path, user_path: str) -> Path:
    base = workspace.expanduser().resolve()
    target = Path(user_path)
    if not target.is_absolute():
        target = base / target
    resolved = target.expanduser().resolve()
    if base != resolved and base not in resolved.parents:
        raise PermissionError(f"Path is outside workspace: {resolved}")
    return resolved
