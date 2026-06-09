import time
from pathlib import Path

from winlocalassistant.assistant_datastore import export_database, put_record
from winlocalassistant.autonomous_loop_guard import MUTATING_TOOLS, should_skip_repeated_action, action_signature
from winlocalassistant.code_quality_gate import CodeQualityGateReport, ReviewComment, render_code_quality_gate_markdown
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore, NON_BLOCKING_STATUS_COMMANDS
from winlocalassistant.research_engine import build_research_report
from winlocalassistant.tools import ToolRegistry


def test_status_aliases_are_non_blocking_and_handled(tmp_path: Path):
    for cmd in ["/autonomous-status", "/autonomous-guide", "/deps-status", "/providers", "/version", "/image-status"]:
        assert cmd in NON_BLOCKING_STATUS_COMMANDS
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "Unknown command" not in app.chat("/autonomous-status")


def test_loop_guard_knows_actual_mutating_tool_names():
    for tool in ["find_replace", "append_file", "make_dir", "ai_edit_project", "project_delete", "install_package"]:
        assert tool in MUTATING_TOOLS
    sig = action_signature("Replace file text", "find_replace", {"path": "app.py", "old": "a", "new": "b"})
    skip, reason = should_skip_repeated_action(
        {"recent_action_signatures": [sig, sig], "no_progress_cycles": 1},
        "Replace file text",
        "find_replace",
        {"path": "app.py", "old": "a", "new": "b"},
        required=True,
    )
    assert skip
    assert "same mutating action" in reason


def test_quality_gate_markdown_hidden_count_matches_total_not_display_cap():
    comments = [ReviewComment("low", "test", "a.py", i + 1, f"n{i}", "body", "fix") for i in range(125)]
    report = CodeQualityGateReport(
        generated_at="now",
        repo_root=".",
        decision="pass",
        files_scanned=1,
        blocking_count=0,
        warning_count=0,
        note_count=120,
        comments=comments[:120],
        total_comment_count=125,
        total_blocking_count=0,
        total_warning_count=0,
        total_note_count=125,
        displayed_comment_count=120,
        truncated_comment_count=5,
    )
    md = render_code_quality_gate_markdown(report)
    assert "35 additional comments" in md  # 125 total, 90 rendered in markdown


def test_research_reports_do_not_overwrite_fast_repeated_runs(tmp_path: Path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_internet=False)
    md1, js1, _ = build_research_report(cfg, "collision test topic", source_urls=[])
    md2, js2, _ = build_research_report(cfg, "collision test topic", source_urls=[])
    assert md1 != md2
    assert js1 != js2
    assert md1.exists() and md2.exists() and js1.exists() and js2.exists()


def test_database_exports_do_not_overwrite_fast_repeated_runs():
    db = f"collision_{time.time_ns()}"
    put_record(db, "notes", "alpha", {"ok": True})
    e1 = export_database(db)
    e2 = export_database(db)
    assert e1["export_path"] != e2["export_path"]
    assert Path(e1["export_path"]).exists() and Path(e2["export_path"]).exists()


def test_registry_has_no_duplicate_literal_tool_run_entry():
    text = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")
    register_block = text.split("def register_defaults", 1)[1].split("}.items()", 1)[0]
    assert register_block.count('"tool_run": self.tool_run') == 1
    registry = ToolRegistry(AssistantConfig.load())
    assert "tool_run" in registry.tools


def test_code_review_does_not_flag_internal_ast_compile(tmp_path: Path):
    pkg = tmp_path / "winlocalassistant"
    pkg.mkdir()
    (pkg / "audit_like.py").write_text("import ast\n\ndef check(text):\n    tree = ast.parse(text)\n    compile(tree, '<x>', 'exec')\n", encoding="utf-8")
    from winlocalassistant.code_review_audit import run_code_review
    report = run_code_review(tmp_path)
    assert not any(f.title == "Dynamic code execution call" for f in report.findings)
