from __future__ import annotations

import json
import re
import time
from dataclasses import asdict, dataclass
from pathlib import Path

from .safe_io import atomic_write_text
from typing import Any


@dataclass
class SurgicalFallbackResult:
    attempted: bool
    changed: bool
    reason: str
    changes: list[str]
    backup_path: str | None = None


TYPO_FIXES = {
    "verifiaction": "verification",
    "verfication": "verification",
    "sucess": "success",
    "succes": "success",
    "caopabiltiies": "capabilities",
    "capabiltiies": "capabilities",
    "improvment": "improvement",
    "imrpovement": "improvement",
    "autonmous": "autonomous",
    "autonomousness": "autonomy",
}

CONFUSABLE_SEMICOLONS = {
    "؛": ";",  # Arabic semicolon
    ";": ";",  # Greek question mark often pasted by mistake
    "﹔": ";",
    "；": ";",  # full-width semicolon
}


def apply_surgical_fallback_to_file(path: Path, error_text: str = "", backup_dir: Path | None = None) -> SurgicalFallbackResult:
    """Apply only tiny deterministic fallback fixes to one file.

    This is intentionally conservative. It is for obvious text/source damage such as
    confusable semicolons, missing semicolons on simple JS statements, non-breaking
    spaces in Python files, and common documentation typos. It never rewrites whole
    files and returns a backup path when it changes anything.
    """
    path = Path(path)
    if not path.exists() or not path.is_file():
        return SurgicalFallbackResult(False, False, f"Target file does not exist: {path}", [])
    suffix = path.suffix.lower()
    if suffix not in {".py", ".js", ".ts", ".css", ".html", ".md", ".txt", ".json"}:
        return SurgicalFallbackResult(False, False, f"Unsupported surgical fallback file type: {suffix}", [])

    original = path.read_text(encoding="utf-8", errors="replace")
    updated = original
    changes: list[str] = []

    if "\u00a0" in updated:
        updated = updated.replace("\u00a0", " ")
        changes.append("Replaced non-breaking spaces with regular spaces.")

    for bad, good in CONFUSABLE_SEMICOLONS.items():
        if bad in updated:
            updated = updated.replace(bad, good)
            changes.append(f"Replaced confusable semicolon {bad!r} with ';'.")

    if suffix in {".md", ".txt"}:
        updated2 = _fix_common_typos(updated)
        if updated2 != updated:
            updated = updated2
            changes.append("Corrected common documentation spelling mistakes.")

    if suffix in {".js", ".ts"}:
        updated2, js_changes = _fix_simple_js_semicolon_damage(updated)
        if js_changes:
            updated = updated2
            changes.extend(js_changes)

    if suffix == ".py":
        updated2, py_changes = _fix_simple_python_colon_damage(updated, error_text)
        if py_changes:
            updated = updated2
            changes.extend(py_changes)

    if updated != original and not updated.endswith("\n"):
        updated += "\n"
        changes.append("Ensured trailing newline after surgical fallback.")

    if updated == original:
        return SurgicalFallbackResult(True, False, "No safe surgical fallback matched the file/error.", [])

    backup_dir = backup_dir or path.parent
    backup_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y%m%d_%H%M%S")
    backup = backup_dir / f"{path.name}.surgical_fallback_{stamp}.bak"
    atomic_write_text(backup, original)
    atomic_write_text(path, updated)
    return SurgicalFallbackResult(True, True, "Applied conservative surgical fallback fixes.", changes, str(backup))


def _fix_common_typos(text: str) -> str:
    def repl(match: re.Match[str]) -> str:
        word = match.group(0)
        fixed = TYPO_FIXES.get(word.lower(), word)
        return fixed.capitalize() if word[:1].isupper() else fixed
    return re.sub(r"\b(" + "|".join(re.escape(k) for k in TYPO_FIXES) + r")\b", repl, text, flags=re.IGNORECASE)


def _fix_simple_js_semicolon_damage(text: str) -> tuple[str, list[str]]:
    changes: list[str] = []
    out: list[str] = []
    for line in text.splitlines():
        stripped = line.strip()
        new_line = line
        if _simple_js_statement_needs_semicolon(stripped):
            new_line = line.rstrip() + ";"
            changes.append("Added missing semicolon to simple JavaScript statement.")
        out.append(new_line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), changes[:10]


def _simple_js_statement_needs_semicolon(stripped: str) -> bool:
    if not stripped or stripped.endswith((";", "{", "}", ",", ":")):
        return False
    if stripped.startswith(("//", "/*", "*", "if ", "for ", "while ", "switch ", "function ", "class ", "else")):
        return False
    if re.match(r"^(const|let|var)\s+[A-Za-z_$][\w$]*\s*=.+", stripped):
        return True
    if re.match(r"^[A-Za-z_$][\w$.]*\s*=.+", stripped):
        return True
    if re.match(r"^return\s+.+", stripped):
        return True
    return False


def _fix_simple_python_colon_damage(text: str, error_text: str = "") -> tuple[str, list[str]]:
    """Repair only obvious missing-colon Python block headers.

    This targets tiny syntax damage such as `if x` or `def f()` when the
    interpreter reports that a colon is expected. It deliberately avoids changing
    arbitrary lines so a failed autonomous edit does not turn into a rewrite.
    """
    low_error = (error_text or "").lower()
    if "expected ':'" not in low_error and "expected ':'" not in text.lower() and "syntaxerror" not in low_error:
        return text, []
    changes: list[str] = []
    out: list[str] = []
    pattern = re.compile(r"^(\s*)(if|elif|else|for|while|def|class|try|except|finally|with)\b(.*[^:])\s*$")
    for line in text.splitlines():
        stripped = line.strip()
        new_line = line
        if stripped and not stripped.startswith("#") and not stripped.endswith(":"):
            m = pattern.match(line)
            if m and not stripped.endswith((",", "\\")):
                new_line = line.rstrip() + ":"
                changes.append("Added missing colon to simple Python block header.")
        out.append(new_line)
    return "\n".join(out) + ("\n" if text.endswith("\n") else ""), changes[:10]


def surgical_fallback_report_payload(result: SurgicalFallbackResult) -> dict[str, Any]:
    return asdict(result)
