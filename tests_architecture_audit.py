from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.architecture_audit import (
    render_architecture_audit_markdown,
    run_architecture_audit,
    write_architecture_audit_report,
)
from winlocalassistant.core import AssistantCore


def test_architecture_audit_reports_core_checks() -> None:
    report = run_architecture_audit(Path.cwd())
    names = {check["name"] for check in report.checks}
    assert "version_consistency" in names
    assert "required_modules" in names
    assert "command_routes" in names
    assert "test_to_module_ratio" in names
    assert report.version
    text = render_architecture_audit_markdown(report)
    assert "Nova Architecture Audit" in text
    assert "Check Summary" in text
    assert "Recommendations" in text


def test_architecture_audit_writes_unique_reports() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_arch_audit_") as tmp:
        md1, js1, _ = write_architecture_audit_report(Path.cwd(), Path(tmp))
        md2, js2, _ = write_architecture_audit_report(Path.cwd(), Path(tmp))
        assert md1.exists() and js1.exists()
        assert md2.exists() and js2.exists()
        assert md1 != md2
        assert js1 != js2
        assert "Architecture Audit" in md1.read_text(encoding="utf-8")


def test_architecture_audit_command_returns_useful_text() -> None:
    core = AssistantCore.load()
    out = core.chat("/architecture-audit")
    assert "Architecture Audit" in out
    assert "Check Summary" in out
    assert "Report written" in out


def run_all(verbose: bool = False) -> None:
    for fn in [
        test_architecture_audit_reports_core_checks,
        test_architecture_audit_writes_unique_reports,
        test_architecture_audit_command_returns_useful_text,
    ]:
        fn()
        if verbose:
            print(f"PASS {fn.__name__}")
