from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
import shutil
import logging
from typing import Any

from .safe_io import atomic_write_json, atomic_write_text

CACHE_NAMES = {"__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache"}
CACHE_SUFFIXES = {".pyc", ".pyo"}
RUNTIME_DIRS = {".nova_runtime"}


@dataclass(frozen=True)
class ReleaseHygieneFinding:
    path: str
    kind: str
    severity: str
    fix: str

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


def _is_inside_ignored(rel: Path) -> bool:
    parts = set(rel.parts)
    return bool(parts & {".git", ".venv", "venv", "node_modules"})


def find_release_hygiene_findings(root: str | Path = ".", *, include_python_cache: bool = True) -> list[ReleaseHygieneFinding]:
    root = Path(root)
    findings: list[ReleaseHygieneFinding] = []
    for path in root.rglob("*"):
        rel = path.relative_to(root)
        if _is_inside_ignored(rel):
            continue
        rel_text = rel.as_posix()
        if path.name in CACHE_NAMES:
            if include_python_cache or path.name not in {"__pycache__", ".pytest_cache"}:
                findings.append(ReleaseHygieneFinding(rel_text, "cache_directory", "warning", "Delete this runtime cache before packaging a release zip."))
        elif path.suffix in CACHE_SUFFIXES:
            if include_python_cache:
                findings.append(ReleaseHygieneFinding(rel_text, "compiled_python", "warning", "Delete compiled Python bytecode before packaging."))
        elif any(part in RUNTIME_DIRS for part in rel.parts):
            findings.append(ReleaseHygieneFinding(rel_text, "runtime_state", "note", "Runtime state should normally be excluded from shared release zips."))
    return findings


def build_release_hygiene_report(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    findings = find_release_hygiene_findings(root)
    blocking = [f for f in findings if f.severity in {"critical", "warning"}]
    report = {
        "ok": not blocking,
        "summary": "Release hygiene passed" if not blocking else f"Release hygiene found {len(blocking)} package artifact(s)",
        "root": str(root),
        "findings": [f.to_dict() for f in findings],
    }
    docs = root / "docs"
    try:
        docs.mkdir(exist_ok=True)
        atomic_write_json(docs / "RELEASE_HYGIENE_LATEST.json", report, ensure_ascii=True)
        atomic_write_text(docs / "RELEASE_HYGIENE_LATEST.md", render_release_hygiene_report(report), encoding="utf-8")
    except Exception as exc:
        logging.getLogger(__name__).debug("Could not write release hygiene latest reports", exc_info=True)
    return report



def clean_release_hygiene_artifacts(root: str | Path = ".") -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    findings = find_release_hygiene_findings(root)
    removed: list[str] = []
    failed: list[dict[str, str]] = []
    for finding in findings:
        target = root / finding.path
        try:
            if target.is_dir():
                shutil.rmtree(target, ignore_errors=False)
            elif target.exists():
                target.unlink()
            removed.append(finding.path)
        except Exception as exc:
            failed.append({"path": finding.path, "error": repr(exc)})
    after = find_release_hygiene_findings(root)
    return {
        "ok": not [f for f in after if f.severity in {"critical", "warning"}],
        "root": str(root),
        "removed": removed,
        "failed": failed,
        "remaining": [f.to_dict() for f in after],
        "summary": f"Removed {len(removed)} release artifact(s); {len(after)} finding(s) remain.",
    }


def render_release_hygiene_report(report: dict[str, Any]) -> str:
    lines = ["# Nova Release Hygiene", "", f"Overall: **{'PASS' if report.get('ok') else 'ATTENTION'}**", f"Root: `{report.get('root')}`", f"Summary: {report.get('summary')}", ""]
    findings = report.get("findings") or []
    if not findings:
        lines.append("No cache, bytecode or runtime-state artifacts were detected in the release tree.")
    else:
        lines.append("## Findings")
        for f in findings[:100]:
            lines.append(f"- **{f.get('severity')}** `{f.get('path')}` — {f.get('kind')}: {f.get('fix')}")
    return "\n".join(lines)
