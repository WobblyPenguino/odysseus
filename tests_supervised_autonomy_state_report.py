import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
import tools.report_supervised_autonomy_state as report

@pytest.fixture
def mock_repo(tmp_path, monkeypatch):
    """Setup mock repository root."""
    monkeypatch.setattr(report, "REPO_ROOT", tmp_path)
    monkeypatch.setattr(report, "SUMMARY_PATH", tmp_path / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md")
    (tmp_path / "local_ai_cycles" / "memory").mkdir(parents=True)
    return tmp_path

def test_readiness_sourced_from_function_call(mock_repo):
    """Test that readiness is sourced from build_autonomy_readiness call."""
    with patch("tools.report_supervised_autonomy_state.build_autonomy_readiness") as mock_readiness, \
         patch("tools.report_supervised_autonomy_state.run_git") as mock_git, \
         patch("builtins.print"):
        
        mock_readiness.return_value = {"score": 100, "status": "ready"}
        mock_git.return_value = "mock"
        
        report.generate_report()
        mock_readiness.assert_called_once_with(".")

def test_dirty_git_blocks_live_mode(mock_repo):
    """Test that dirty git state blocks live mode even if readiness is 100."""
    with patch("tools.report_supervised_autonomy_state.build_autonomy_readiness") as mock_readiness, \
         patch("tools.report_supervised_autonomy_state.run_git") as mock_git, \
         patch("builtins.print") as mock_print:
        
        mock_readiness.return_value = {"score": 100, "status": "ready"}
        # Simulate dirty git on status call
        mock_git.side_effect = lambda args: "M file.py" if args == ["status", "--porcelain"] else "main"
        
        report.generate_report()
        
        output = "\n".join([str(c.args[0]) for c in mock_print.call_args_list])
        assert "**Live Supervised Autonomy Allowed:** False" in output
        assert "**Dirty / Generated-Noise Status:** Dirty" in output

def test_task_parsing_precedence_and_fallback(mock_repo):
    """Test that final fallback task is parsed over earlier candidates."""
    report.SUMMARY_PATH.write_text(
        "Best task candidate weak-task: score=20\n"
        "Autonomous candidate fallback selected productive task: strong-task\n"
        "Autonomous candidate fallback score: 90\n"
        "Selected task: strong-task\n"
        "Result: preflight-only"
    )
    
    info = report.parse_latest_task_info()
    assert info["task_id"] == "strong-task"
    assert info["score"] == "90"
    assert info["result"] == "preflight-only"

def test_safest_command_is_always_dry_run(mock_repo):
    """Test that the safest command is dry-run regardless of state."""
    with patch("tools.report_supervised_autonomy_state.build_autonomy_readiness") as mock_readiness, \
         patch("tools.report_supervised_autonomy_state.run_git") as mock_git, \
         patch("builtins.print") as mock_print:
        
        mock_readiness.return_value = {"score": 100, "status": "ready"}
        mock_git.return_value = "" # Clean
        
        report.generate_report()
        output = "\n".join([str(c.args[0]) for c in mock_print.call_args_list])
        assert "--dry-run" in output
        assert "run_supervised_autonomy_batch.py" in output

def test_report_read_only_integrity(mock_repo):
    """Test that report generation does not modify summary files."""
    content = "persisted summary text"
    report.SUMMARY_PATH.write_text(content)
    with patch("tools.report_supervised_autonomy_state.build_autonomy_readiness"), \
         patch("tools.report_supervised_autonomy_state.run_git"), \
         patch("builtins.print"):
        report.generate_report()
    assert report.SUMMARY_PATH.read_text() == content