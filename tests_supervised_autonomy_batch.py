import pytest
import subprocess
import json
import re
from pathlib import Path
from unittest.mock import MagicMock, patch

import tools.run_supervised_autonomy_batch as batch

@pytest.fixture
def mock_repo_root(tmp_path):
    (tmp_path / "run_nova_task_queue_loop.ps1").write_text("echo 'mock task loop'")
    mem_dir = tmp_path / "local_ai_cycles" / "memory"
    mem_dir.mkdir(parents=True)
    (mem_dir / "NOVA_TASK_LOOP_SUMMARY_LATEST.md").write_text("")
    (mem_dir / "NOVA_TASK_LOOP_MANUAL_REVIEW_LATEST.md").write_text("")
    return tmp_path

@pytest.fixture(autouse=True)
def mock_paths(mock_repo_root, monkeypatch):
    monkeypatch.setattr(batch, "REPO_ROOT", mock_repo_root)
    monkeypatch.setattr(batch, "TASK_LOOP_SCRIPT", mock_repo_root / "run_nova_task_queue_loop.ps1")
    monkeypatch.setattr(batch, "BATCH_SUMMARY_MD", mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.md")
    monkeypatch.setattr(batch, "BATCH_SUMMARY_JSON", mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_SUPERVISED_AUTONOMY_BATCH_LATEST.json")
    monkeypatch.setattr(batch, "TASK_LOOP_SUMMARY_LATEST", mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md")
    monkeypatch.setattr(batch, "TASK_LOOP_MANUAL_REVIEW_LATEST", mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_MANUAL_REVIEW_LATEST.md")

@pytest.fixture
def mock_subprocess_run():
    with patch("subprocess.run") as mock:
        yield mock

@pytest.fixture
def mock_git_clean(mock_subprocess_run):
    mock_subprocess_run.return_value = MagicMock(stdout="", stderr="", returncode=0)
    return mock_subprocess_run

@pytest.fixture
def mock_autonomy_readiness_100(monkeypatch):
    mock_readiness = MagicMock(return_value={"score": 100, "status": "ready"})
    monkeypatch.setattr(batch, "build_autonomy_readiness", mock_readiness)
    return mock_readiness

@pytest.fixture
def mock_lifecycle_success(mock_subprocess_run, mock_repo_root, mock_autonomy_readiness_100):
    summary_path = mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    
    def side_effect(args, **kwargs):
        cmd = args[-1] if isinstance(args, list) and len(args) > 0 else ""
        if "-PreflightOnly" in cmd:
            summary_path.write_text(f"Best task candidate task_1: score={batch.MIN_SCORE_THRESHOLD + 1}\nResult: preflight-only")
            return MagicMock(stdout="Preflight output", stderr="", returncode=0)
        elif "-Cycles 1" in cmd:
            summary_path.write_text("Result: committed\nValidation gates passed")
            return MagicMock(stdout="Live cycle output", stderr="", returncode=0)
        return MagicMock(stdout="", stderr="", returncode=0)

    mock_subprocess_run.side_effect = side_effect
    return mock_subprocess_run

def test_dirty_git_refusal(mock_subprocess_run, mock_autonomy_readiness_100):
    mock_subprocess_run.return_value = MagicMock(stdout="M  file.py", stderr="", returncode=0)
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert "Dirty git state detected" in batch.BATCH_SUMMARY_MD.read_text()

def test_readiness_below_100_refusal(mock_git_clean, monkeypatch):
    monkeypatch.setattr(batch, "build_autonomy_readiness", lambda p: {"score": 50})
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert "Autonomy readiness below 100/100" in batch.BATCH_SUMMARY_MD.read_text()

def test_low_score_refusal(mock_git_clean, mock_autonomy_readiness_100, mock_subprocess_run, mock_repo_root):
    summary_path = mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    def side_effect(args, **kwargs):
        cmd = args[-1] if isinstance(args, list) and len(args) > 0 else ""
        if "-PreflightOnly" in cmd:
            summary_path.write_text(f"Best task candidate task_1: score={batch.MIN_SCORE_THRESHOLD - 1}")
            return MagicMock(stdout="Preflight output", stderr="", returncode=0)
        return MagicMock(stdout="", stderr="", returncode=0)
    mock_subprocess_run.side_effect = side_effect
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert f"Selected task score {batch.MIN_SCORE_THRESHOLD - 1} below {batch.MIN_SCORE_THRESHOLD}" in batch.BATCH_SUMMARY_MD.read_text()

def test_task_pool_exhausted_refusal(mock_git_clean, mock_autonomy_readiness_100, mock_subprocess_run, mock_repo_root):
    summary_path = mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    def side_effect(args, **kwargs):
        cmd = args[-1] if isinstance(args, list) and len(args) > 0 else ""
        if "-PreflightOnly" in cmd:
            summary_path.write_text("Outcome category: task-pool-exhausted")
            return MagicMock(stdout="Preflight output", stderr="", returncode=0)
        return MagicMock(stdout="", stderr="", returncode=0)
    mock_subprocess_run.side_effect = side_effect
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert "Task pool exhausted in preflight." in batch.BATCH_SUMMARY_MD.read_text()

def test_failed_live_cycle_stop(mock_git_clean, mock_autonomy_readiness_100, mock_subprocess_run, mock_repo_root):
    summary_path = mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    def side_effect(args, **kwargs):
        cmd = args[-1] if isinstance(args, list) and len(args) > 0 else ""
        if "-PreflightOnly" in cmd:
            summary_path.write_text(f"Best task candidate task_1: score={batch.MIN_SCORE_THRESHOLD + 1}")
            return MagicMock(returncode=0)
        elif "-Cycles 1" in cmd:
            return MagicMock(stdout="", stderr="Live cycle failed", returncode=1)
        return MagicMock(stdout="", stderr="", returncode=0)
    mock_subprocess_run.side_effect = side_effect
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert "Live task loop cycle failed" in batch.BATCH_SUMMARY_MD.read_text()

def test_validation_failure_stop(mock_git_clean, mock_autonomy_readiness_100, mock_subprocess_run, mock_repo_root):
    summary_path = mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    def side_effect(args, **kwargs):
        cmd = args[-1] if isinstance(args, list) and len(args) > 0 else ""
        if "-PreflightOnly" in cmd:
            summary_path.write_text(f"Best task candidate task_1: score={batch.MIN_SCORE_THRESHOLD + 1}")
            return MagicMock(returncode=0)
        elif "-Cycles 1" in cmd:
            summary_path.write_text("Result: rejected\nValidation failed")
            return MagicMock(stdout="Live cycle output", stderr="", returncode=0)
        return MagicMock(stdout="", stderr="", returncode=0)
    mock_subprocess_run.side_effect = side_effect
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert "Validation failed in live cycle." in batch.BATCH_SUMMARY_MD.read_text()

def test_max_cycle_stop(mock_lifecycle_success):
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 0
    assert "Max cycles reached." in batch.BATCH_SUMMARY_MD.read_text()

def test_repeated_failed_task_stop(mock_git_clean, mock_autonomy_readiness_100, mock_subprocess_run, mock_repo_root):
    summary_path = mock_repo_root / "local_ai_cycles" / "memory" / "NOVA_TASK_LOOP_SUMMARY_LATEST.md"
    def side_effect(args, **kwargs):
        cmd = args[-1] if isinstance(args, list) and len(args) > 0 else ""
        if "-PreflightOnly" in cmd:
            summary_path.write_text(f"Best task candidate task_1: score={batch.MIN_SCORE_THRESHOLD + 1}")
            return MagicMock(returncode=0)
        elif "-Cycles 1" in cmd:
            summary_path.write_text("Result: rejected\nOutcome category: repeated-failure")
            return MagicMock(stdout="Live cycle output", stderr="", returncode=0)
        return MagicMock(stdout="", stderr="", returncode=0)
    mock_subprocess_run.side_effect = side_effect
    result = batch.run_supervised_autonomy_batch(1, "test_batch")
    assert result == 1
    assert "Repeated failed task detected in live cycle." in batch.BATCH_SUMMARY_MD.read_text()