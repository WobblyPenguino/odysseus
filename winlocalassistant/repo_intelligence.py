from __future__ import annotations

"""Lightweight repo intelligence for safe Nova code work.

This module intentionally avoids external dependencies.  It borrows the useful
shape of modern coding-agent systems: a compact repository map, explicit patch
plans, risk flags and validation suggestions before edits happen.
"""

import ast
import json
import re
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

_CODE_EXTENSIONS = {".py", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".md", ".json", ".toml", ".yaml", ".yml"}
_SKIP_DIRS = {".git", "__pycache__", ".pytest_cache", ".venv", "venv", "node_modules", "dist", "build", ".mypy_cache"}
_ENTRYPOINTS = {"app.py", "winlocalassistant/main.py", "winlocalassistant/nova_api.py"}


@dataclass(slots=True)
class RepoSymbol:
    name: str
    kind: str
    line: int
    signature: str = ""


@dataclass(slots=True)
class RepoFileSummary:
    path: str
    kind: str
    lines: int
    symbols: list[RepoSymbol] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    risk_flags: list[str] = field(default_factory=list)


@dataclass(slots=True)
class RepoMap:
    root: str
    generated_at: str
    files: list[RepoFileSummary]
    tests: list[str]
    entrypoints: list[str]
    dependencies: list[str]
    risk_flags: list[str]
    validation_commands: list[str]


def _iter_repo_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*"):
        if any(part in _SKIP_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_file() and path.suffix.lower() in _CODE_EXTENSIONS:
            files.append(path)
    return sorted(files, key=lambda p: str(p.relative_to(root)).lower())


def _is_entrypoint(rel: str) -> bool:
    return rel in _ENTRYPOINTS or rel.endswith("/webui.py")


def _is_test_file(rel: str) -> bool:
    name = Path(rel).name
    return rel.startswith("tests") or name.startswith("tests_") or name.startswith("test_")


def _repo_file_priority(root: Path, path: Path) -> tuple[int, str]:
    rel = path.relative_to(root).as_posix()
    rel_low = rel.lower()
    if _is_entrypoint(rel):
        return (0, rel_low)
    if rel.startswith(("winlocalassistant/", "nova/")):
        return (1, rel_low)
    if _is_test_file(rel):
        return (2, rel_low)
    return (3, rel_low)


def _python_summary(root: Path, path: Path, text: str) -> RepoFileSummary:
    rel = path.relative_to(root).as_posix()
    symbols: list[RepoSymbol] = []
    imports: list[str] = []
    risk_flags: list[str] = []
    try:
        tree = ast.parse(text)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                args = []
                for arg in node.args.args[:8]:
                    args.append(arg.arg)
                symbols.append(RepoSymbol(node.name, "function", getattr(node, "lineno", 0), f"{node.name}({', '.join(args)})"))
            elif isinstance(node, ast.ClassDef):
                symbols.append(RepoSymbol(node.name, "class", getattr(node, "lineno", 0), node.name))
            elif isinstance(node, ast.Import):
                imports.extend(alias.name.split(".")[0] for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module.split(".")[0])
    except SyntaxError as exc:
        risk_flags.append(f"syntax_error:{exc.lineno}")
    lines = text.count("\n") + (1 if text else 0)
    if lines > 2500:
        risk_flags.append("large_file")
    if "subprocess" in imports or "os.system" in text:
        risk_flags.append("shell_execution")
    if "shutil.rmtree" in text or "os.remove" in text or "unlink(" in text:
        risk_flags.append("delete_operation")
    if "Set-ExecutionPolicy" in text or "reg add" in text.lower():
        risk_flags.append("windows_system_change")
    return RepoFileSummary(rel, "python", lines, symbols[:30], sorted(set(imports))[:30], risk_flags)


def _plain_summary(root: Path, path: Path, text: str) -> RepoFileSummary:
    rel = path.relative_to(root).as_posix()
    lines = text.count("\n") + (1 if text else 0)
    risk_flags: list[str] = []
    low = text.lower()
    if lines > 2500:
        risk_flags.append("large_file")
    if "curl " in low or "irm " in low or "iex" in low:
        risk_flags.append("downloads_or_remote_shell")
    if "rm -rf" in low or "remove-item" in low:
        risk_flags.append("delete_operation")
    return RepoFileSummary(rel, path.suffix.lower().lstrip(".") or "text", lines, [], [], risk_flags)


def build_repo_map(root: Path | str, *, max_files: int = 220) -> dict[str, Any]:
    root = Path(root).resolve()
    summaries: list[RepoFileSummary] = []
    tests: list[str] = []
    entrypoints: list[str] = []
    dependencies: set[str] = set()
    repo_risks: list[str] = []

    selected_files = sorted(_iter_repo_files(root), key=lambda p: _repo_file_priority(root, p))[:max(1, int(max_files))]
    for path in selected_files:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except Exception:
            continue
        summary = _python_summary(root, path, text) if path.suffix == ".py" else _plain_summary(root, path, text)
        summaries.append(summary)
        dependencies.update(summary.imports)
        if summary.risk_flags:
            repo_risks.extend(f"{summary.path}:{flag}" for flag in summary.risk_flags)
        rel = path.relative_to(root).as_posix()
        if _is_test_file(rel):
            tests.append(rel)
        if _is_entrypoint(rel):
            entrypoints.append(rel)

    validation = ["python -m compileall app.py winlocalassistant", "python -m pytest -q"]
    if (root / "package.json").exists():
        validation.append("npm test --if-present")
    if (root / "pyproject.toml").exists():
        validation.append("python -m pytest -q tests_nova_orchestration_foundation_v55_3_152.py tests_nova_video_manifest.py")

    repo_map = RepoMap(
        root=str(root),
        generated_at=time.strftime("%Y-%m-%d %H:%M:%S"),
        files=summaries,
        tests=sorted(set(tests)),
        entrypoints=sorted(set(entrypoints)),
        dependencies=sorted(d for d in dependencies if d and not d.startswith("."))[:120],
        risk_flags=sorted(set(repo_risks))[:120],
        validation_commands=validation,
    )
    return asdict(repo_map)


def render_repo_map(payload: dict[str, Any], *, max_files: int = 40) -> str:
    lines = ["# Nova Repo Map", "", f"Root: `{payload.get('root')}`", f"Generated: {payload.get('generated_at')}", ""]
    lines += ["## Entrypoints", *[f"- `{x}`" for x in payload.get("entrypoints", []) or ["(none found)"]], ""]
    lines += ["## Test surface", f"- Tests discovered: **{len(payload.get('tests', []))}**", ""]
    lines += ["## File summaries"]
    for item in (payload.get("files") or [])[:max_files]:
        symbols = item.get("symbols") or []
        symbol_text = ", ".join(s.get("signature") or s.get("name") for s in symbols[:6]) if symbols else "no symbols"
        risk = "; risks=" + ",".join(item.get("risk_flags") or []) if item.get("risk_flags") else ""
        lines.append(f"- `{item.get('path')}` — {item.get('kind')}, {item.get('lines')} lines, {symbol_text}{risk}")
    if payload.get("risk_flags"):
        lines += ["", "## Risk flags", *[f"- {x}" for x in payload.get("risk_flags", [])[:40]]]
    lines += ["", "## Recommended validation", *[f"- `{cmd}`" for cmd in payload.get("validation_commands", [])]]
    return "\n".join(lines)


def build_patch_plan(goal: str, repo_map: dict[str, Any], *, files: list[str] | None = None) -> dict[str, Any]:
    goal_low = (goal or "").lower()
    candidates = files or []
    if not candidates:
        for item in repo_map.get("files", []):
            path = str(item.get("path") or "")
            if "video" in goal_low and "video" in path:
                candidates.append(path)
            if "web" in goal_low and "webui" in path:
                candidates.append(path)
            if "state" in goal_low and "orchestration" in path:
                candidates.append(path)
            if "test" in goal_low and Path(path).name.startswith("tests"):
                candidates.append(path)
    candidates = sorted(set(candidates))[:12]
    risk = "medium" if any("webui.py" in f or "core.py" in f or "tools.py" in f for f in candidates) else "low"
    return {
        "goal": goal,
        "files_to_inspect": candidates,
        "risk": risk,
        "apply_policy": "patch-first, no broad rewrites, preserve tests, rollback with git diff or clean branch",
        "validation_commands": repo_map.get("validation_commands", []),
        "approval_required": risk in {"medium", "high"},
    }


def render_patch_plan(plan: dict[str, Any]) -> str:
    lines = ["# Nova Patch Plan", "", f"Goal: {plan.get('goal')}", f"Risk: **{plan.get('risk')}**", f"Approval required: {plan.get('approval_required')}", "", "## Files to inspect"]
    lines += [f"- `{f}`" for f in plan.get("files_to_inspect", [])] or ["- No files selected yet; inspect repo map first."]
    lines += ["", "## Validation", *[f"- `{cmd}`" for cmd in plan.get("validation_commands", [])], "", f"Policy: {plan.get('apply_policy')}"]
    return "\n".join(lines)
