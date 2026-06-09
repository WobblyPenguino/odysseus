from __future__ import annotations

import ast
import importlib.util
import json
import re
from pathlib import Path
from types import ModuleType
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text, read_json_file
import time

CUSTOM_TOOLS_DIR = APP_DIR / "custom_tools"
CUSTOM_TOOLS_MANIFEST = CUSTOM_TOOLS_DIR / "manifest.json"
CUSTOM_TOOL_PROPOSALS = CUSTOM_TOOLS_DIR / "proposals.json"

SAFE_IMPORTS = {
    "json", "re", "math", "statistics", "datetime", "time", "csv", "random",
    "collections", "itertools", "functools", "decimal", "textwrap", "html", "urllib.parse"
}
BLOCKED_IMPORTS = {
    "os", "subprocess", "shutil", "socket", "ctypes", "winreg", "multiprocessing",
    "threading", "asyncio", "requests", "urllib.request", "sys", "builtins"
}
# pathlib is intentionally allowed because tools receive a safe workspace Path.
BLOCKED_CALLS = {"eval", "exec", "compile", "open", "__import__", "input", "breakpoint"}
BLOCKED_ATTR_CALLS = {
    "system", "popen", "remove", "rmdir", "unlink", "rmtree", "replace", "rename",
    "symlink_to", "hardlink_to", "chmod", "write_bytes"
}
# Attribute access that commonly indicates a custom tool is attempting to escape
# the supplied workspace Path rather than inspect files below it. Existing safe
# tools can still use workspace.rglob(), path.read_text(), path.relative_to(workspace), etc.
BLOCKED_ATTR_ACCESS = {"parent", "parents", "root", "anchor", "drive", "home", "expanduser", "resolve", "absolute"}




def normalize_tool_code(code: str) -> str:
    """Normalise code returned by local models before safety validation.

    Local models sometimes return the tool source double-escaped, for example
    ``def run(...):\n    ...`` instead of real newlines. That made safe tools
    appear to fail validation with "unexpected character after line continuation".
    This keeps normal Python source unchanged, strips markdown fences, and decodes
    common escaped newline/tab/quote sequences when the text clearly looks escaped.
    """
    text = str(code or "").strip()
    if text.startswith("```"):
        text = re.sub(r"^```(?:python|py)?\s*", "", text, flags=re.I)
        text = re.sub(r"\s*```$", "", text)
    # If source is one long line with literal \n escapes, decode it.
    if "\\n" in text and "\n" not in text[:200]:
        try:
            text = bytes(text, "utf-8").decode("unicode_escape")
        except Exception:
            text = text.replace("\\n", "\n").replace("\\t", "\t")
    return text.strip() + "\n"


def safe_tool_name(name: str) -> str:
    name = re.sub(r"[^A-Za-z0-9_]+", "_", name or "").strip("_").lower()
    if not name:
        raise ValueError("Tool name is empty")
    if not re.match(r"^[a-z_][a-z0-9_]{1,48}$", name):
        raise ValueError("Tool name must be 2-49 chars and use letters, numbers or underscore")
    return name


def _load_manifest() -> dict[str, Any]:
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if CUSTOM_TOOLS_MANIFEST.exists():
        try:
            return read_json_file(CUSTOM_TOOLS_MANIFEST, {"tools": {}}, expected_type=dict, quarantine=True)
        except Exception:
            return {"tools": {}}
    return {"tools": {}}


def _save_manifest(data: dict[str, Any]) -> None:
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(CUSTOM_TOOLS_MANIFEST, data, ensure_ascii=True)


def list_custom_tools() -> list[dict[str, Any]]:
    data = _load_manifest()
    tools = data.get("tools") or {}
    out = []
    for name, spec in sorted(tools.items()):
        path = CUSTOM_TOOLS_DIR / f"{name}.py"
        item = {"name": name, **(spec if isinstance(spec, dict) else {}), "exists": path.exists(), "path": str(path)}
        item.setdefault("risk", "read_only")
        item.setdefault("enabled", True)
        item.setdefault("last_tested", "")
        item.setdefault("last_used", "")
        out.append(item)
    return out



def refresh_custom_tool_registry() -> dict[str, Any]:
    """Return a fresh manifest-backed tool list for UI refresh/API tests.

    The registry is file-backed, so this intentionally re-reads the manifest
    from disk instead of trusting any cached frontend state.
    """
    tools = list_custom_tools()
    return {"tools": tools, "count": len(tools), "manifest_path": str(CUSTOM_TOOLS_MANIFEST), "custom_tools_dir": str(CUSTOM_TOOLS_DIR)}


def mark_custom_tool_tested(name: str, *, ok: bool, summary: str = "") -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    manifest = _load_manifest()
    spec = manifest.setdefault("tools", {}).get(tool_name)
    if spec is None:
        raise FileNotFoundError(f"Custom tool not found: {tool_name}")
    spec["last_tested"] = time.strftime("%Y-%m-%d %H:%M:%S")
    spec["last_test_ok"] = bool(ok)
    spec["last_test_summary"] = str(summary or "")[:300]
    _save_manifest(manifest)
    return {"name": tool_name, "last_tested": spec["last_tested"], "last_test_ok": bool(ok), "summary": spec["last_test_summary"]}

def _load_proposals() -> dict[str, Any]:
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    if CUSTOM_TOOL_PROPOSALS.exists():
        try:
            return read_json_file(CUSTOM_TOOL_PROPOSALS, {"proposals": {}}, expected_type=dict, quarantine=True)
        except Exception:
            return {"proposals": {}}
    return {"proposals": {}}


def _save_proposals(data: dict[str, Any]) -> None:
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    atomic_write_json(CUSTOM_TOOL_PROPOSALS, data, ensure_ascii=True)



def cleanup_tool_proposals() -> dict[str, Any]:
    """Delete stale/invalid proposals when an equivalent installed tool exists.

    v31 could correctly install a deterministic fallback tool while leaving the
    model's broken proposal behind. That confused the GUI because /custom-tools
    showed both an installed tool and a pending unsafe proposal for the same job.
    """
    data = _load_proposals()
    proposals = data.get("proposals") or {}
    installed = {t.get("name") for t in list_custom_tools() if t.get("exists")}
    installed_desc = "\n".join((str(t.get("name", "")) + " " + str(t.get("description", ""))).lower() for t in list_custom_tools())
    removed = []
    for pid, spec in list(proposals.items()):
        name = str(spec.get("name") or "")
        desc = str(spec.get("description") or "").lower()
        duplicate = name in installed
        similar_html_ref = "html" in desc and ("css" in desc or "js" in desc) and "html_reference_checker" in installed
        unsafe = not bool(spec.get("safety_ok"))
        if duplicate or (unsafe and similar_html_ref):
            removed.append({"id": pid, "name": name, "reason": "duplicate_or_superseded_by_installed_tool"})
            proposals.pop(pid, None)
    data["proposals"] = proposals
    _save_proposals(data)
    return {"removed": removed, "remaining": [{"id": pid, **spec} for pid, spec in sorted(proposals.items())]}


def list_tool_proposals() -> list[dict[str, Any]]:
    data = _load_proposals()
    proposals = data.get("proposals") or {}
    return [{"id": pid, **spec} for pid, spec in sorted(proposals.items())]


def save_tool_proposal(name: str, description: str, code: str, input_schema: dict[str, Any] | None = None, section: str = "General", risk: str = "read_only") -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    code = normalize_tool_code(code)
    ok, problems = validate_tool_code(code)
    proposal_id = f"{int(time.time())}_{tool_name}"
    data = _load_proposals()
    data.setdefault("proposals", {})[proposal_id] = {
        "name": tool_name,
        "description": description or "Custom local tool proposal",
        "input_schema": input_schema or {},
        "section": section or "General",
        "risk": risk or "read_only",
        "code": code,
        "safety_ok": bool(ok),
        "safety_problems": problems,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
    }
    _save_proposals(data)
    return {"id": proposal_id, **data["proposals"][proposal_id]}


def get_tool_proposal(proposal_id: str) -> dict[str, Any] | None:
    return (_load_proposals().get("proposals") or {}).get(proposal_id)


def delete_tool_proposal(proposal_id: str) -> dict[str, Any]:
    data = _load_proposals()
    existed = proposal_id in data.get("proposals", {})
    data.setdefault("proposals", {}).pop(proposal_id, None)
    _save_proposals(data)
    return {"id": proposal_id, "existed": existed, "deleted": existed}


def approve_tool_proposal(proposal_id: str) -> dict[str, Any]:
    proposal = get_tool_proposal(proposal_id)
    if not proposal:
        raise FileNotFoundError(f"Tool proposal not found: {proposal_id}")
    if not proposal.get("safety_ok"):
        raise ValueError("Proposal failed safety validation: " + "; ".join(proposal.get("safety_problems") or []))
    saved = save_custom_tool(
        proposal.get("name") or proposal_id,
        proposal.get("description") or "Custom tool",
        proposal.get("code") or "",
        proposal.get("input_schema") if isinstance(proposal.get("input_schema"), dict) else {},
        proposal.get("section") or "General",
        risk=proposal.get("risk") or "read_only",
    )
    delete_tool_proposal(proposal_id)
    return saved


def set_custom_tool_enabled(name: str, enabled: bool) -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    manifest = _load_manifest()
    spec = manifest.setdefault("tools", {}).get(tool_name)
    if spec is None:
        raise FileNotFoundError(f"Custom tool not found: {tool_name}")
    spec["enabled"] = bool(enabled)
    _save_manifest(manifest)
    return {"name": tool_name, "enabled": bool(enabled)}


def get_custom_tool_source(name: str) -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    path = CUSTOM_TOOLS_DIR / f"{tool_name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Custom tool not found: {tool_name}")
    manifest = _load_manifest()
    return {"name": tool_name, "path": str(path), "metadata": (manifest.get("tools") or {}).get(tool_name, {}), "code": path.read_text(encoding="utf-8", errors="replace")}


def validate_tool_code(code: str) -> tuple[bool, list[str]]:
    code = normalize_tool_code(code)
    problems: list[str] = []
    if len(code) > 40000:
        problems.append("Tool code is too large")
    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        return False, [f"Syntax error: {exc}"]
    has_run = False
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "run":
            has_run = True
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [(node.module or "").split(".")[0]]
            for name in names:
                if name in BLOCKED_IMPORTS or (name and name not in SAFE_IMPORTS):
                    problems.append(f"Import is not allowed: {name}")
        if isinstance(node, ast.Attribute) and node.attr in BLOCKED_ATTR_ACCESS:
            problems.append(f"Workspace escape-prone attribute is not allowed: .{node.attr}")
        if isinstance(node, ast.Call):
            fn = node.func
            if isinstance(fn, ast.Name) and fn.id in BLOCKED_CALLS:
                problems.append(f"Call is not allowed: {fn.id}()")
            if isinstance(fn, ast.Attribute) and fn.attr in BLOCKED_ATTR_CALLS:
                problems.append(f"Potentially unsafe call is not allowed: .{fn.attr}()")
    if not has_run:
        problems.append("Tool must define: run(args, workspace, config)")
    return not problems, problems


def save_custom_tool(name: str, description: str, code: str, input_schema: dict[str, Any] | None = None, section: str = "General", risk: str = "read_only") -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    code = normalize_tool_code(code)
    ok, problems = validate_tool_code(code)
    if not ok:
        raise ValueError("; ".join(problems))
    CUSTOM_TOOLS_DIR.mkdir(parents=True, exist_ok=True)
    path = CUSTOM_TOOLS_DIR / f"{tool_name}.py"
    atomic_write_text(path, code)
    manifest = _load_manifest()
    manifest.setdefault("tools", {})[tool_name] = {
        "description": description or "Custom local tool",
        "input_schema": input_schema or {},
        "section": section or "General",
        "risk": risk or "read_only",
        "enabled": True,
        "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "last_tested": "",
        "last_used": "",
        "created_by": "local_llm_or_fallback",
    }
    _save_manifest(manifest)
    return {"name": tool_name, "path": str(path), "description": description, "input_schema": input_schema or {}}


def _load_module(path: Path, name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"winlocalassistant_custom_{name}", str(path))
    if spec is None or spec.loader is None:
        raise RuntimeError("Could not load tool module")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


def delete_custom_tool(name: str) -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    path = CUSTOM_TOOLS_DIR / f"{tool_name}.py"
    manifest = _load_manifest()
    existed = path.exists()
    if existed:
        path.unlink()
    manifest.setdefault("tools", {}).pop(tool_name, None)
    _save_manifest(manifest)
    return {"name": tool_name, "existed": existed, "deleted": existed}


def run_custom_tool(name: str, args: dict[str, Any], workspace: Path, config: Any) -> dict[str, Any]:
    tool_name = safe_tool_name(name)
    path = CUSTOM_TOOLS_DIR / f"{tool_name}.py"
    if not path.exists():
        raise FileNotFoundError(f"Custom tool not found: {tool_name}")
    manifest = _load_manifest()
    spec = manifest.get("tools", {}).get(tool_name, {})
    if spec.get("enabled", True) is False:
        raise PermissionError(f"Custom tool is disabled: {tool_name}")
    code = path.read_text(encoding="utf-8", errors="replace")
    ok, problems = validate_tool_code(code)
    if not ok:
        raise ValueError("Tool failed safety validation before run: " + "; ".join(problems))
    module = _load_module(path, tool_name)
    run = getattr(module, "run", None)
    if not callable(run):
        raise RuntimeError("Tool has no callable run(args, workspace, config)")
    result = run(args or {}, workspace, config)
    try:
        manifest.setdefault("tools", {}).setdefault(tool_name, spec)["last_used"] = time.strftime("%Y-%m-%d %H:%M:%S")
        _save_manifest(manifest)
    except Exception:
        import logging as _wla_logging
        _wla_logging.getLogger(__name__).debug("Suppressed optional exception", exc_info=True)
    if isinstance(result, dict):
        return result
    return {"result": result}
