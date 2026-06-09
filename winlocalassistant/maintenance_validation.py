from __future__ import annotations

import ast
import os
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from .codebase_sanity_audit import build_codebase_sanity_audit
from .feature_audit import build_feature_audit
from .release_hygiene import build_release_hygiene_report
from .safe_io import atomic_write_json, atomic_write_text
from .whole_codebase_review import build_whole_codebase_review

EXCLUDED_DIRS = {
    "__pycache__",
    ".pytest_cache",
    ".git",
    ".nova_runtime",
    ".ruff_cache",
    "node_modules",
    "venv",
    ".venv",
    "dist",
    "build",
}

VALIDATION_LADDER = [
    "python -W error::SyntaxWarning -m compileall -q app.py winlocalassistant tests_smoke.py",
    "python tests_smoke.py",
    "$env:NOVA_IMAGE_BACKEND='auto'; $env:NOVA_DIFFUSERS_MODEL=''; $env:NOVA_ALLOW_DIFFUSERS_DOWNLOAD='0'; python -m pytest",
    "python app.py /feature-audit",
    "python app.py /whole-codebase-review",
    "python app.py /codebase-sanity-audit",
    "python app.py /release-hygiene",
]


@dataclass(frozen=True)
class MaintenanceCheck:
    name: str
    ok: bool
    severity: str
    summary: str
    detail: dict[str, Any] | None = None


def _iter_python_files(root: Path) -> Iterable[Path]:
    candidates = []
    package = root / "winlocalassistant"
    if package.exists():
        candidates.extend(package.rglob("*.py"))
    candidates.extend(root.glob("tests_*.py"))
    if (root / "app.py").exists():
        candidates.append(root / "app.py")
    for path in sorted(set(candidates)):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        yield path


def _safe_rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path).replace("\\", "/")


def _read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""


def _parse_for_python_310(root: Path) -> dict[str, Any]:
    errors: list[dict[str, Any]] = []
    files = list(_iter_python_files(root))
    for path in files:
        text = _read_text(path)
        try:
            try:
                ast.parse(text, filename=_safe_rel(path, root), feature_version=(3, 10))
            except TypeError:
                ast.parse(text, filename=_safe_rel(path, root))
        except SyntaxError as exc:
            errors.append({
                "path": _safe_rel(path, root),
                "line": exc.lineno,
                "message": exc.msg,
                "text": (exc.text or "").strip()[:180],
            })
    return {"ok": not errors, "files_checked": len(files), "errors": errors[:50]}


def _image_backend_test_env() -> dict[str, Any]:
    values = {
        "NOVA_IMAGE_BACKEND": os.environ.get("NOVA_IMAGE_BACKEND", ""),
        "NOVA_DIFFUSERS_MODEL": os.environ.get("NOVA_DIFFUSERS_MODEL", ""),
        "NOVA_ALLOW_DIFFUSERS_DOWNLOAD": os.environ.get("NOVA_ALLOW_DIFFUSERS_DOWNLOAD", ""),
    }
    fallback_isolated = not values["NOVA_DIFFUSERS_MODEL"] and values["NOVA_ALLOW_DIFFUSERS_DOWNLOAD"].lower() not in {"1", "true", "yes", "on"}
    return {
        "ok": fallback_isolated,
        "values": values,
        "stable_pytest_prefix": "$env:NOVA_IMAGE_BACKEND='auto'; $env:NOVA_DIFFUSERS_MODEL=''; $env:NOVA_ALLOW_DIFFUSERS_DOWNLOAD='0'",
        "summary": "Image fallback tests are isolated" if fallback_isolated else "Image backend is enabled; fallback tests must clear image env first",
    }


def _local_model_validation_context() -> dict[str, Any]:
    configured_models = {
        "OLLAMA_MODEL": os.environ.get("OLLAMA_MODEL", ""),
        "NOVA_MODEL": os.environ.get("NOVA_MODEL", ""),
        "NOVA_CODE_MODEL": os.environ.get("NOVA_CODE_MODEL", ""),
        "NOVA_CHAT_MODEL": os.environ.get("NOVA_CHAT_MODEL", ""),
        "NOVA_FAST_MODEL": os.environ.get("NOVA_FAST_MODEL", ""),
    }
    active = {key: value for key, value in configured_models.items() if value}
    prompt = (
        "Review this Nova maintenance report for unhandled release blockers. "
        "Prioritise Python 3.10 compatibility, failing gates, command/tool drift, unsafe writes, "
        "and tests whose result depends on local optional backends. Return only concrete blockers "
        "and the smallest next verification command for each."
    )
    return {
        "configured_models": configured_models,
        "has_configured_local_model": bool(active),
        "review_prompt": prompt,
        "suggested_command": "/model-health",
    }


def _check(name: str, ok: bool, severity: str, summary: str, detail: dict[str, Any] | None = None) -> MaintenanceCheck:
    return MaintenanceCheck(name=name, ok=bool(ok), severity=severity, summary=summary, detail=detail or {})


def build_maintenance_validation(root: str | Path = ".", tool_names: list[str] | None = None, profile: str = "quick") -> dict[str, Any]:
    """Build a single read-only maintenance validation report for Nova."""
    root = Path(root).resolve()
    py310 = _parse_for_python_310(root)
    whole = build_whole_codebase_review(root, tool_names=tool_names)
    sanity = build_codebase_sanity_audit(root)
    feature = build_feature_audit(root)
    hygiene = build_release_hygiene_report(root)
    image_env = _image_backend_test_env()
    local_model = _local_model_validation_context()

    tool_names_set = set(tool_names or [])
    missing_tools = sorted({"maintenance_validate", "validate_maintenance", "self_validate", "validation_ladder"} - tool_names_set) if tool_names is not None else []
    hygiene_findings = hygiene.get("findings") or []
    hygiene_warning_count = len([item for item in hygiene_findings if item.get("severity") in {"warning", "error"}])

    release_warning = hygiene_warning_count > 0
    image_warning = not image_env["ok"]
    checks = [
        _check("python_310_compat", py310["ok"], "critical", "Python parses under the configured py310 target" if py310["ok"] else f"{len(py310['errors'])} Python 3.10 compatibility error(s)", py310),
        _check("whole_codebase_review", whole.get("ok", False), "high", str(whole.get("summary") or "Whole-codebase review completed"), {"warnings": whole.get("warnings", []), "blockers": whole.get("blockers", [])}),
        _check("codebase_sanity_audit", sanity.get("ok", False), "high", str(sanity.get("summary") or "Codebase sanity audit completed"), {"findings_total": sanity.get("findings_total"), "severity_counts": sanity.get("severity_counts")}),
        _check("feature_audit", feature.get("ok", False), "high", str(feature.get("summary") or "Feature audit completed"), {"implemented": feature.get("implemented"), "partial": feature.get("partial"), "missing": feature.get("missing")}),
        _check("release_hygiene", True, "warning" if release_warning else "info", str(hygiene.get("summary") or "Release hygiene checked"), {"warning_count": hygiene_warning_count}),
        _check("image_backend_test_env", True, "warning" if image_warning else "info", image_env["summary"], image_env),
        _check("maintenance_tool_registry", not missing_tools, "high", "Maintenance validation tools are registered" if not missing_tools else "Maintenance validation aliases are missing", {"missing_tools": missing_tools}),
    ]
    blocker_checks = [asdict(check) for check in checks if not check.ok and check.severity in {"critical", "high"}]
    warning_checks = [asdict(check) for check in checks if check.severity == "warning"]
    payload = {
        "ok": not blocker_checks,
        "summary": "Nova maintenance validation passed" if not blocker_checks else f"Nova maintenance validation found {len(blocker_checks)} blocker(s)",
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "root": str(root),
        "profile": profile or "quick",
        "checks": [asdict(check) for check in checks],
        "blockers": blocker_checks,
        "warnings": warning_checks,
        "validation_ladder": VALIDATION_LADDER,
        "local_model_validation": local_model,
        "source_reports": {
            "whole_codebase_review": {
                "ok": whole.get("ok"),
                "warnings": whole.get("warnings", []),
                "blockers": whole.get("blockers", []),
            },
            "codebase_sanity_audit": {
                "ok": sanity.get("ok"),
                "findings_total": sanity.get("findings_total"),
                "severity_counts": sanity.get("severity_counts"),
            },
            "feature_audit": {
                "ok": feature.get("ok"),
                "summary": feature.get("summary"),
                "missing": feature.get("missing"),
                "partial": feature.get("partial"),
            },
            "release_hygiene": {
                "ok": hygiene.get("ok"),
                "summary": hygiene.get("summary"),
                "finding_count": len(hygiene_findings),
            },
        },
    }
    docs_dir = root / "docs"
    docs_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_json(docs_dir / "NOVA_MAINTENANCE_VALIDATION_LATEST.json", payload)
    atomic_write_text(docs_dir / "NOVA_MAINTENANCE_VALIDATION_LATEST.md", render_maintenance_validation(payload))
    return payload


def render_maintenance_validation(payload: dict[str, Any]) -> str:
    lines = [
        "# Nova Maintenance Validation",
        "",
        f"Generated: {payload.get('generated_at', '')}",
        f"Root: `{payload.get('root', '')}`",
        f"Profile: `{payload.get('profile', 'quick')}`",
        f"Overall: {'PASS' if payload.get('ok') else 'BLOCKED'}",
        "",
        "## Checks",
    ]
    for check in payload.get("checks") or []:
        marker = "WARN" if check.get("severity") == "warning" else ("PASS" if check.get("ok") else check.get("severity", "issue").upper())
        lines.append(f"- {marker} **{check.get('name')}**: {check.get('summary')}")
    blockers = payload.get("blockers") or []
    if blockers:
        lines += ["", "## Blockers"]
        for check in blockers:
            detail = check.get("detail") or {}
            lines.append(f"- **{check.get('name')}**: {check.get('summary')}")
            if detail.get("errors"):
                for err in detail.get("errors", [])[:8]:
                    lines.append(f"  - `{err.get('path')}:{err.get('line')}` {err.get('message')}")
    warnings = payload.get("warnings") or []
    if warnings:
        lines += ["", "## Warnings"]
        for check in warnings:
            lines.append(f"- **{check.get('name')}**: {check.get('summary')}")
    lines += ["", "## Stable Validation Ladder"]
    for command in payload.get("validation_ladder") or []:
        lines.append(f"- `{command}`")
    local_model = payload.get("local_model_validation") or {}
    lines += [
        "",
        "## Local Model Review",
        f"- Configured local model env: {'yes' if local_model.get('has_configured_local_model') else 'no'}",
        f"- First run: `{local_model.get('suggested_command', '/model-health')}`",
        f"- Review prompt: {local_model.get('review_prompt', '')}",
    ]
    return "\n".join(lines)
