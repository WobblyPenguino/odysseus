from __future__ import annotations

from pathlib import Path

from .safe_io import atomic_write_text

LEDGER_RELATIVE_PATH = Path("docs") / "QUALITY_PROGRESS_LEDGER.md"


def quality_progress_path(repo_root: Path) -> Path:
    return repo_root.resolve() / LEDGER_RELATIVE_PATH


def read_quality_progress(repo_root: Path) -> str:
    path = quality_progress_path(repo_root)
    if not path.exists():
        return "# Quality Progress Ledger\n\nNo patched issues have been recorded yet.\n"
    return path.read_text(encoding="utf-8")


def append_quality_progress(repo_root: Path, version: str, entries: list[str]) -> Path:
    path = quality_progress_path(repo_root)
    path.parent.mkdir(parents=True, exist_ok=True)
    existing = path.read_text(encoding="utf-8") if path.exists() else "# Quality Progress Ledger\n\nThis file tracks code-quality/integrity issues patched across future Nova releases so progress is visible between versions.\n"
    block = ["", f"## {version}", ""]
    for entry in entries:
        text = str(entry).strip()
        if text:
            block.append(f"- {text}")
    block.append("")
    atomic_write_text(path, existing.rstrip() + "\n" + "\n".join(block))
    return path
