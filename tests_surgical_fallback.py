from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.surgical_fallback import apply_surgical_fallback_to_file


def test_surgical_fallback_fixes_common_doc_typos() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_surgical_doc_") as tmp:
        path = Path(tmp) / "report.md"
        path.write_text("# Report\n\nverifiaction sucess improves capabiltiies\n", encoding="utf-8")
        result = apply_surgical_fallback_to_file(path, "spelling", backup_dir=Path(tmp) / "backups")
        text = path.read_text(encoding="utf-8")
    assert result.attempted
    assert result.changed
    assert "verification success improves capabilities" in text
    assert result.backup_path


def test_surgical_fallback_normalises_confusable_semicolon() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_surgical_js_ була") as tmp:
        path = Path(tmp) / "app.js"
        path.write_text("const score = 0؛\nlet running = true\n", encoding="utf-8")
        result = apply_surgical_fallback_to_file(path, "Unexpected token", backup_dir=Path(tmp) / "backups")
        text = path.read_text(encoding="utf-8")
    assert result.changed
    assert "const score = 0;" in text
    assert "let running = true;" in text


def test_surgical_fallback_unsupported_file_is_noop() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_surgical_noop_") as tmp:
        path = Path(tmp) / "image.bin"
        path.write_bytes(b"abc")
        result = apply_surgical_fallback_to_file(path, "error", backup_dir=Path(tmp) / "backups")
    assert not result.attempted
    assert not result.changed


def test_surgical_fallback_fixes_simple_python_missing_colon() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_py_colon_") as tmp:
        target = Path(tmp) / "broken.py"
        target.write_text("def answer()\n    return 42\n", encoding="utf-8")
        result = apply_surgical_fallback_to_file(target, "SyntaxError: expected ':'", backup_dir=Path(tmp))
        text = target.read_text(encoding="utf-8")
    assert result.changed is True
    assert "def answer():" in text
    assert any("missing colon" in change.lower() for change in result.changes)


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
