from __future__ import annotations

import argparse
import hashlib
import json
import logging
import re
import time
import zipfile
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

from .config import APP_DIR
from .safe_io import atomic_write_json, atomic_write_text
from .release_readiness import latest_release_readiness, latest_release_readiness_ok

LOGGER = logging.getLogger(__name__)

RELEASE_PACKAGER_SCHEMA_VERSION = 1

EXCLUDE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
    ".nova_runtime",
    "logs",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".venv",
    "venv",
}

EXCLUDE_SUFFIXES = {
    ".pyc",
    ".pyo",
    ".tmp",
    ".log",
}

# Large generated evidence folders are useful locally, but they make the release
# zip noisy and slow to download. Docs and tests stay in the package.
DEFAULT_EXCLUDE_TOP_LEVEL = {
    "codebase_integrity_reports",
    "code_quality_gates",
    "code_reviews",
    "repair_audits",
}

REQUIRED_RELEASE_FILES = [
    "app.py",
    "README.md",
    "CHANGELOG.md",
    "start_windows_assistant.bat",
    "winlocalassistant/__init__.py",
    "winlocalassistant/core.py",
    "winlocalassistant/tools.py",
    "winlocalassistant/webui.py",
]


@dataclass
class PackageFile:
    path: str
    size: int
    sha256: str


def _read_version(root: Path) -> str:
    init_path = root / "winlocalassistant" / "__init__.py"
    try:
        text = init_path.read_text(encoding="utf-8", errors="replace")
        match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', text)
        if match:
            return match.group(1)
    except Exception:
        LOGGER.debug("Failed to read Nova version from %s", init_path, exc_info=True)
    return "unknown"


def _slug(text: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9._-]+", "_", text or "release").strip("._-")
    return clean[:80] or "release"


def _should_skip(rel: Path, *, include_reports: bool = False) -> tuple[bool, str]:
    parts = rel.parts
    if not parts:
        return False, ""
    if parts[0] in EXCLUDE_DIRS:
        return True, f"excluded directory {parts[0]}"
    if not include_reports and parts[0] in DEFAULT_EXCLUDE_TOP_LEVEL:
        return True, f"generated report folder {parts[0]}"
    if any(part in EXCLUDE_DIRS for part in parts):
        return True, "excluded nested cache/tooling directory"
    if rel.name == "RELEASE_MANIFEST.json":
        return True, "generated release manifest is rewritten during packaging"
    if rel.name.startswith(".") and rel.name not in {".gitignore", ".pre-commit-config.yaml"}:
        return True, "hidden transient file"
    if rel.suffix.lower() in EXCLUDE_SUFFIXES:
        return True, f"excluded suffix {rel.suffix}"
    return False, ""


def collect_release_files(root: str | Path, *, include_reports: bool = False) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    files: list[PackageFile] = []
    skipped: list[dict[str, Any]] = []
    missing_required = [path for path in REQUIRED_RELEASE_FILES if not (root / path).exists()]
    if not root.exists():
        return {
            "ok": False,
            "root": str(root),
            "summary": "source root does not exist",
            "files": [],
            "skipped": [],
            "missing_required": REQUIRED_RELEASE_FILES,
        }
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        skip, reason = _should_skip(rel, include_reports=include_reports)
        if skip:
            skipped.append({"path": rel.as_posix(), "reason": reason})
            continue
        try:
            data = path.read_bytes()
            files.append(PackageFile(rel.as_posix(), len(data), hashlib.sha256(data).hexdigest()))
        except Exception as exc:
            skipped.append({"path": rel.as_posix(), "reason": f"read failed: {exc!r}"})
    ok = not missing_required and bool(files)
    return {
        "ok": ok,
        "root": str(root),
        "version": _read_version(root),
        "summary": "release file set is ready" if ok else "release file set needs attention",
        "files": [asdict(item) for item in files],
        "skipped": skipped,
        "missing_required": missing_required,
        "include_reports": include_reports,
        "total_size_bytes": sum(item.size for item in files),
    }


def build_release_package(root: str | Path = ".", *, name: str = "", include_reports: bool = False, out_dir: str | Path | None = None, require_readiness: bool = False, force: bool = False) -> dict[str, Any]:
    root = Path(root).expanduser().resolve()
    readiness = latest_release_readiness(root)
    if require_readiness and not force and not latest_release_readiness_ok(root):
        collected = collect_release_files(root, include_reports=include_reports)
        return {
            **collected,
            "ok": False,
            "summary": "release-readiness gate has not passed; run /release-readiness --full before packaging",
            "package_path": "",
            "manifest_path": "",
            "readiness_gate": readiness,
        }
    collected = collect_release_files(root, include_reports=include_reports)
    if not collected.get("ok"):
        return {**collected, "package_path": "", "manifest_path": ""}
    version = str(collected.get("version") or "unknown")
    stamp = time.strftime("%Y%m%d_%H%M%S")
    release_name = _slug(name or f"Nova_v{version}_clean_release")
    target_dir = Path(out_dir).expanduser().resolve() if out_dir else (APP_DIR / "release_packages")
    target_dir.mkdir(parents=True, exist_ok=True)
    package_path = target_dir / f"{release_name}_{stamp}.zip"
    manifest_path = target_dir / f"{release_name}_{stamp}_manifest.json"
    try:
        with zipfile.ZipFile(package_path, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
            for item in collected.get("files", []):
                rel = Path(item["path"])
                zf.write(root / rel, rel.as_posix())
            manifest = {
                "schema_version": RELEASE_PACKAGER_SCHEMA_VERSION,
                "created_at": time.strftime("%Y-%m-%d %H:%M:%S"),
                "source_root": str(root),
                "version": version,
                "release_name": release_name,
                "package_path": str(package_path),
                "file_count": len(collected.get("files", [])),
                "skipped_count": len(collected.get("skipped", [])),
                "total_size_bytes": collected.get("total_size_bytes", 0),
                "include_reports": include_reports,
                "readiness_gate": readiness,
                "files": collected.get("files", []),
                "skipped": collected.get("skipped", []),
                "validation_hint": [
                    "python -m compileall -q winlocalassistant app.py",
                    "python -m winlocalassistant.startup_validation --mode quick --timeout 90",
                    "python -m winlocalassistant.nova_system_test --profile quick --timeout 120",
                ],
            }
            zf.writestr("RELEASE_MANIFEST.json", json.dumps(manifest, indent=2, ensure_ascii=True))
        atomic_write_json(manifest_path, manifest, ensure_ascii=True)
        package_bytes = package_path.read_bytes()
        return {
            **collected,
            "ok": True,
            "summary": f"clean release package created with {len(collected.get('files', []))} file(s)",
            "package_path": str(package_path),
            "manifest_path": str(manifest_path),
            "package_size_bytes": len(package_bytes),
            "package_sha256": hashlib.sha256(package_bytes).hexdigest(),
            "readiness_gate": readiness,
        }
    except Exception as exc:
        return {**collected, "ok": False, "summary": f"release package failed: {exc}", "error": repr(exc), "package_path": str(package_path), "manifest_path": str(manifest_path)}


def render_release_package(payload: dict[str, Any]) -> str:
    lines = [
        "# Clean Release Package",
        "",
        f"Summary: {payload.get('summary','')}",
        f"Root: `{payload.get('root','')}`",
        f"Version: `{payload.get('version','unknown')}`",
        "",
        "## Result",
    ]
    if payload.get("ok") and payload.get("package_path"):
        lines.extend([
            f"- Package: `{payload.get('package_path')}`",
            f"- Manifest: `{payload.get('manifest_path')}`",
            f"- Files included: {len(payload.get('files') or [])}",
            f"- Skipped: {len(payload.get('skipped') or [])}",
            f"- ZIP size: {payload.get('package_size_bytes', 0)} bytes",
            f"- SHA256: `{payload.get('package_sha256','')}`",
        ])
    else:
        lines.append("- Package was not created.")
    readiness = payload.get("readiness_gate") or {}
    if readiness:
        lines.append("\n## Release-readiness gate")
        lines.append(f"- Status: `{readiness.get('status', 'unknown')}`")
        lines.append(f"- Summary: {readiness.get('summary', '')}")
    if payload.get("missing_required"):
        lines.append("\n## Missing required files")
        for item in payload.get("missing_required") or []:
            lines.append(f"- `{item}`")
    skipped = payload.get("skipped") or []
    if skipped:
        lines.append("\n## Excluded examples")
        for item in skipped[:14]:
            lines.append(f"- `{item.get('path')}` — {item.get('reason')}")
        if len(skipped) > 14:
            lines.append(f"- ... {len(skipped) - 14} more excluded item(s)")
    lines.append("\n## Validation after unzipping")
    for command in [
        "python -m compileall -q winlocalassistant app.py",
        "python -m winlocalassistant.startup_validation --mode quick --timeout 90",
        "python -m winlocalassistant.nova_system_test --profile quick --timeout 120",
    ]:
        lines.append(f"- `{command}`")
    return "\n".join(lines).strip() + "\n"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build a clean Nova release package.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--name", default="")
    parser.add_argument("--include-reports", action="store_true")
    parser.add_argument("--out-dir", default="")
    parser.add_argument("--force", action="store_true", help="Bypass the latest /release-readiness gate. Use only for diagnostics, not shipping.")
    args = parser.parse_args(argv)
    payload = build_release_package(args.root, name=args.name, include_reports=args.include_reports, out_dir=args.out_dir or None, require_readiness=True, force=args.force)
    print(render_release_package(payload))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
