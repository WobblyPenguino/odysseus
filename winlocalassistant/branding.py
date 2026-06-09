from __future__ import annotations

import re
from pathlib import Path
from typing import Iterable

PRODUCT_NAME = "Nova"
ASSISTANT_NAME = "Nova"
LEGACY_PRODUCT_NAMES = ("WinLocalAssistant", "Win Local Assistant", "Windows Local Assistant")
LEGACY_SHORT_NAME = "WLA"

# Keep legacy commands accepted at the command parser, but never advertise them.
LEGACY_COMMAND_ALIASES: dict[str, str] = {
    "/wla-doctor": "/nova-doctor",
    "/wla-mega-test": "/nova-mega-test",
    "/test-wla-all": "/nova-test-all",
    "/index-wla": "/index-nova",
    "/search-wla-docs": "/search-nova-docs",
    "/search-wla-code": "/search-nova-code",
    "/wla-audit-log": "/nova-audit-log",
}

PRIMARY_NOVA_COMMANDS: tuple[str, ...] = (
    "/nova-doctor",
    "/release-gate",
    "/nova-mega-test",
    "/nova-brand-audit",
    "/nova-improvement-research",
    "/nova-eval-packs",
    "/nova-system-test",
)

USER_VISIBLE_SUFFIXES = {
    ".bat",
    ".cmd",
    ".css",
    ".html",
    ".ini",
    ".js",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}

BRAND_AUDIT_EXCLUDED_FILES = {"winlocalassistant/branding.py", "RELEASE_MANIFEST.json"}

SCAN_EXCLUDED_DIRS = {
    ".git",
    ".pytest_cache",
    "__pycache__",
    ".mypy_cache",
    ".ruff_cache",
    ".nova_runtime",
    ".venv",
    "venv",
    "node_modules",
    "dist",
    "build",
    "code_quality_gates",
    "code_reviews",
    "codebase_integrity_reports",
}

GENERATED_DOC_PREFIXES = (
    "IMPROVEMENT_REPORT",
    "V55_",
    "FULL_CODEBASE",
    "CODEBASE_",
    "ERROR_",
    "RELEASE_HYGIENE",
    "REPORT_HYGIENE",
    "NOVA_",
)

LEGACY_BRAND_RE = re.compile(r"WinLocalAssistant|Win Local Assistant|Windows Local Assistant|\bWLA\b")
LEGACY_VISIBLE_LOWER_RE = re.compile(r"(?<![A-Za-z0-9])(?:wla[-_][a-z0-9_.-]+|/[a-z-]*wla[a-z-]*|test-wla-all|\bwla\b)(?![A-Za-z0-9])")


def canonical_command(cmd: str) -> str:
    """Return the Nova command name for both current and legacy aliases."""
    return LEGACY_COMMAND_ALIASES.get((cmd or "").strip().lower(), (cmd or "").strip().lower())


def rebrand_text(text: str) -> str:
    """Convert visible legacy brand wording to Nova without touching lowercase package names."""
    updated = str(text or "")
    for name in LEGACY_PRODUCT_NAMES:
        updated = updated.replace(name, PRODUCT_NAME)
    updated = re.sub(r"\bWLA\b", PRODUCT_NAME, updated)
    updated = updated.replace("/wla-doctor", "/nova-doctor")
    updated = updated.replace("/wla-mega-test", "/nova-mega-test")
    updated = updated.replace("/test-wla-all", "/nova-test-all")
    updated = updated.replace("/index-wla", "/index-nova")
    updated = updated.replace("/search-wla-docs", "/search-nova-docs")
    updated = updated.replace("/search-wla-code", "/search-nova-code")
    updated = updated.replace("/wla-audit-log", "/nova-audit-log")
    return updated


def _iter_scannable_files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        if any(part in SCAN_EXCLUDED_DIRS for part in path.parts):
            continue
        try:
            rel = path.relative_to(root).as_posix()
        except ValueError:
            rel = path.as_posix()
        if path.name.startswith(("tests_", "test_")):
            continue
        if rel in BRAND_AUDIT_EXCLUDED_FILES:
            continue
        if path.name.startswith(GENERATED_DOC_PREFIXES):
            continue
        if rel.startswith("docs/") and (path.suffix.lower() == ".json" or path.name.startswith(GENERATED_DOC_PREFIXES)):
            continue
        if path.suffix.lower() not in USER_VISIBLE_SUFFIXES:
            continue
        yield path


def scan_legacy_branding(root: Path | str = ".", *, max_items: int = 120) -> dict:
    """Scan release-visible text files for legacy brand mentions."""
    base = Path(root).resolve()
    matches: list[dict] = []
    total = 0
    for path in _iter_scannable_files(base):
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        except OSError:
            continue
        for line_no, line in enumerate(text.splitlines(), start=1):
            # Test and unpack directories may still contain the legacy archive
            # name in absolute paths. That is not a visible product label in
            # the release text, so normalize the current root before matching.
            visible_line = line.replace(str(base), "<release-root>").replace(base.name, "<release-root>")
            lower_legacy = path.suffix.lower() != ".py" and LEGACY_VISIBLE_LOWER_RE.search(visible_line)
            if not (LEGACY_BRAND_RE.search(visible_line) or lower_legacy):
                continue
            # Internal lowercase package/import names are deliberately allowed in
            # Python source for compatibility; non-code release text should use
            # Nova wording.
            total += 1
            if len(matches) < max_items:
                matches.append({"path": str(path.relative_to(base)), "line": line_no, "text": visible_line.strip()[:240]})
    return {
        "ok": total == 0,
        "product": PRODUCT_NAME,
        "legacy_mentions": total,
        "matches": matches,
        "truncated": total > len(matches),
        "scanned_root": str(base),
    }


def render_branding_audit(payload: dict) -> str:
    status = "PASS" if payload.get("ok") else "ATTENTION"
    lines = [
        "# Nova Brand Audit",
        "",
        f"Overall: **{status}**",
        f"Legacy visible mentions: **{payload.get('legacy_mentions', 0)}**",
        f"Scanned root: `{payload.get('scanned_root', '')}`",
    ]
    matches = payload.get("matches") or []
    if matches:
        lines += ["", "## Remaining legacy mentions"]
        for item in matches:
            lines.append(f"- `{item.get('path')}`:{item.get('line')} — {item.get('text')}")
        if payload.get("truncated"):
            lines.append("- ...additional matches omitted from preview.")
    else:
        lines += ["", "No visible legacy brand markers were found in scanned text files."]
    lines += ["", "## Compatibility", "Legacy command aliases are still accepted internally, but Nova commands are the documented primary surface."]
    return "\n".join(lines)
