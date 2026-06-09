from pathlib import Path

from winlocalassistant.code_quality_gate import run_code_quality_gate, render_code_quality_gate_markdown
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.core import AssistantCore
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence


def test_code_quality_gate_blocks_syntax_error(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    (pkg / "broken.py").write_text("def bad(:\n    pass\n", encoding="utf-8")
    report = run_code_quality_gate(tmp_path)
    assert report.decision == "block"
    assert report.blocking_count >= 1
    assert any(c.blocking and c.path.endswith("broken.py") for c in report.comments)
    md = render_code_quality_gate_markdown(report)
    assert "CodeRabbit-style" in md
    assert "BLOCK" in md


def test_code_quality_gate_warns_on_silent_exception(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    (pkg / "sample.py").write_text("def f():\n    try:\n        1 / 0\n    except Exception:\n        pass\n", encoding="utf-8")
    report = run_code_quality_gate(tmp_path)
    assert report.decision in {"warn", "block"}
    assert any("exception" in c.title.lower() for c in report.comments)


def test_tool_registry_exposes_code_quality_gate(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    (pkg / "ok.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False)
    tool = ToolRegistry(cfg)
    result = tool.call("code_quality_gate", path=".")
    assert result.summary.startswith("Code quality gate decision:")
    assert result.data["decision"] in {"pass", "warn", "block"}
    assert Path(result.data["markdown_path"]).exists()


def test_core_command_exposes_code_quality_gate(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    (pkg / "ok.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False))
    text = app.handle_command("/code-quality-gate .")
    assert "Code quality gate decision" in text


def test_autonomous_sequence_includes_quality_gate_for_builds():
    plan = build_autonomous_tool_sequence("build a calculator app with save load and tests")
    tools = [step.tool for step in plan.steps]
    assert "code_quality_gate" in tools
    assert tools.index("code_quality_gate") < tools.index("ai_create_project")
    assert any(step.title == "Post-build quality gate" for step in plan.steps)

from winlocalassistant.code_quality_gate import write_code_quality_gate_report
from winlocalassistant.tool_catalog import find_tool_entry


def test_quality_gate_reports_do_not_overwrite_fast_repeated_runs(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    (pkg / "ok.py").write_text("def f():\n    return 1\n", encoding="utf-8")
    md1, js1, _ = write_code_quality_gate_report(tmp_path)
    md2, js2, _ = write_code_quality_gate_report(tmp_path)
    assert md1 != md2
    assert js1 != js2
    assert md1.exists() and md2.exists() and js1.exists() and js2.exists()


def test_quality_gate_preserves_total_counts_when_display_is_capped(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    source = "\n".join([
        "def f():",
        "    try:",
        "        1 / 0",
        "    except Exception:",
        "        pass",
        "def g():",
        "    try:",
        "        1 / 0",
        "    except Exception:",
        "        pass",
    ])
    (pkg / "sample.py").write_text(source, encoding="utf-8")
    report = run_code_quality_gate(tmp_path, max_comments=1)
    assert report.displayed_comment_count == 1
    assert report.total_comment_count >= report.displayed_comment_count
    assert report.truncated_comment_count == report.total_comment_count - report.displayed_comment_count
    assert "total comments found" in render_code_quality_gate_markdown(report)


def test_quality_tools_are_registered_in_tool_catalog():
    for name in ["code_repair_audit", "code_review_audit", "code_quality_gate"]:
        entry = find_tool_entry(name)
        assert entry is not None
        assert entry.risk == "low"
        assert "mutation" in entry.never_use_for


def test_quality_progress_command_is_available(tmp_path: Path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False))
    text = app.handle_command("/quality-progress")
    assert "Quality Progress Ledger" in text
