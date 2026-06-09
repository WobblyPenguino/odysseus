from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.code_review_audit import run_code_review, write_code_review_report, render_code_review_markdown
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence


def test_code_review_detects_mutable_defaults_and_model_timeout() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        pkg = root / "winlocalassistant"
        pkg.mkdir()
        (pkg / "bad.py").write_text(
            "from winlocalassistant.model_router import model_chat\n"
            "def f(items=[]):\n"
            "    return items\n"
            "def g(config):\n"
            "    return model_chat(config, 'x', [])\n",
            encoding="utf-8",
        )
        report = run_code_review(root)
        titles = {f.title for f in report.findings}
        assert "Mutable default argument" in titles
        assert "Model call without explicit timeout" in titles
        assert not report.ok


def test_code_review_tool_writes_reports() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        cfg = AssistantConfig(workspace=str(root), allow_mutating_tools=True)
        result = ToolRegistry(cfg).call("code_review_audit", path=".")
        assert result.ok
        assert Path(result.data["markdown_path"]).exists()
        assert Path(result.data["json_path"]).exists()
        assert "Deep Code Review" in result.data["summary"]


def test_code_review_markdown_has_review_order() -> None:
    with tempfile.TemporaryDirectory() as td:
        root = Path(td)
        (root / "tests_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
        md, js, report = write_code_review_report(root)
        text = render_code_review_markdown(report)
        assert md.exists()
        assert js.exists()
        assert "Suggested review order" in text


def test_autonomous_sequence_includes_deep_code_review_before_mutation() -> None:
    plan = build_autonomous_tool_sequence("improve current project safely")
    tools = [step.tool for step in plan.steps]
    assert "code_review_audit" in tools
    if "improve_project" in tools:
        assert tools.index("code_review_audit") < tools.index("improve_project")
