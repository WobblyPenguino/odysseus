from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.code_repair_audit import run_code_repair_audit, write_code_repair_audit_report
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore


def test_code_repair_audit_detects_duplicate_defs_and_cache_artifacts() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_repair_audit_") as tmp:
        root = Path(tmp)
        pkg = root / "winlocalassistant"
        pkg.mkdir()
        (pkg / "demo.py").write_text("def a():\n    return 1\ndef a():\n    return 2\n", encoding="utf-8")
        cache = root / ".pytest_cache"
        cache.mkdir()
        (cache / "README.md").write_text("cache", encoding="utf-8")
        report = run_code_repair_audit(root)
    titles = {finding.title for finding in report.findings}
    assert "Duplicate definition shadows earlier code" in titles
    assert "Runtime/cache artifact present" in titles
    assert not report.ok


def test_code_repair_audit_command_writes_report() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_repair_audit_cmd_") as tmp:
        root = Path(tmp)
        pkg = root / "winlocalassistant"
        pkg.mkdir()
        (pkg / "ok.py").write_text("def ok():\n    return True\n", encoding="utf-8")
        cfg = AssistantConfig(workspace=str(root), allow_mutating_tools=False, allow_internet=False)
        core = AssistantCore(cfg)
        out = core.chat("/repair-audit")
        assert "Code repair audit completed" in out
        assert (root / "repair_audits").exists()


def test_code_repair_audit_report_renderer_has_repair_order() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_repair_audit_report_") as tmp:
        root = Path(tmp)
        pkg = root / "winlocalassistant"
        pkg.mkdir()
        (pkg / "ok.py").write_text("def ok():\n    return True\n", encoding="utf-8")
        md, js, report = write_code_repair_audit_report(root)
        assert md.exists()
        assert js.exists()
        text = md.read_text(encoding="utf-8")
        assert "Recommended repair order" in text
        assert report.files_scanned >= 1


def test_code_repair_audit_zero_python_files_reports_wrong_target() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_repair_no_py_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>project</h1>", encoding="utf-8")
        report = run_code_repair_audit(root)
    assert report.files_scanned == 0
    assert not report.ok
    assert any(f.category == "targeting" for f in report.findings)
    assert not any("Autonomous guard markers missing" in f.title for f in report.findings)

from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence


def test_autonomous_sequence_runs_repair_audit_before_project_mutation() -> None:
    plan = build_autonomous_tool_sequence("improve current project by fixing bugs and checking all code")
    tools = [step.tool for step in plan.steps]
    assert "code_repair_audit" in tools
    if "improve_project" in tools:
        assert tools.index("code_repair_audit") < tools.index("improve_project")
