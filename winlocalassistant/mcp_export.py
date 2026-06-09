from __future__ import annotations
import json
from pathlib import Path
from typing import Any


def build_mcp_manifest(app: Any | None = None, root: Path | None = None) -> dict[str, Any]:
    commands = sorted(getattr(app, "tools", None).tools.keys()) if getattr(getattr(app, "tools", None), "tools", None) else []
    return {
        "name": "Nova",
        "version": "mcp-style-local-manifest-v1",
        "description": "Local Nova tool manifest for future connector/MCP-style use. Execution remains allowlisted inside Nova.",
        "resources": ["activity log", "model IO log", "project files", "release reports"],
        "tools": [{"name": c, "description": "Nova internal tool", "risk": "internal_allowlisted"} for c in commands],
        "prompts": ["project blueprint", "candidate repair", "surgical repair", "release validation"],
        "security": ["no arbitrary remote tool execution", "commands remain Nova allowlisted", "sandbox/dev runs use copied workspaces"],
    }


def render_mcp_manifest(payload: dict[str, Any]) -> str:
    lines = ["# Nova MCP-style Tool Manifest", "", f"Name: {payload.get('name')}", f"Version: {payload.get('version')}", "", "## Security"]
    lines += [f"- {x}" for x in payload.get("security", [])]
    lines += ["", f"## Tools exposed: {len(payload.get('tools', []))}"]
    for tool in payload.get("tools", [])[:80]:
        lines.append(f"- `{tool.get('name')}` — {tool.get('risk')}")
    if len(payload.get("tools", [])) > 80:
        lines.append(f"- ... {len(payload.get('tools', [])) - 80} more")
    lines += ["", "## Resources"] + [f"- {x}" for x in payload.get("resources", [])]
    return "\n".join(lines)
