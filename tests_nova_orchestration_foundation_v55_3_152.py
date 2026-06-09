from __future__ import annotations

import subprocess
import sys

from winlocalassistant.config import AssistantConfig
from winlocalassistant.orchestration_foundation import (
    JobQueue,
    ToolContract,
    build_integration_foundation_report,
    validate_transition,
)
from winlocalassistant.tools import ToolRegistry


def test_state_machine_blocks_mic_reentry_while_processing():
    blocked = validate_transition("processing", "listening")
    assert blocked.ok is False
    assert "processing/speaking" in blocked.illegal_because
    allowed = validate_transition("processing", "speaking")
    assert allowed.ok is True


def test_job_queue_dedupes_and_leases_jobs(tmp_path):
    queue = JobQueue(tmp_path / "jobs.sqlite3")
    first = queue.enqueue("coding", "fix bug", {"x": 1}, dedupe_key="same")
    second = queue.enqueue("coding", "fix bug again", {"x": 2}, dedupe_key="same")
    assert first.job_id == second.job_id
    leased = queue.lease_next("worker-a", lease_seconds=5)
    assert leased is not None
    assert leased.status == "running"
    assert leased.payload["worker_id"] == "worker-a"
    done = queue.mark(leased.job_id, "succeeded", {"tests": "passed"})
    assert done is not None
    assert done.status == "succeeded"
    assert queue.summary()["counts"]["succeeded"] == 1


def test_tool_contract_requires_approval_for_high_risk():
    bad = ToolContract("windows_tweak", "change services", risk_level="high", requires_approval=False, working_dir_policy="system")
    assert bad.validate()
    good = ToolContract("windows_tweak", "change services", risk_level="high", requires_approval=True, working_dir_policy="system")
    assert good.validate() == []


def test_integration_foundation_tool_registry(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    result = registry.call("integration_foundation")
    assert result.ok is True, result.data
    assert "state_machine" in result.data
    assert "job_queue" in result.data
    assert "Tool contracts" in result.data["message"]


def test_job_queue_tool_can_enqueue_and_cancel(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    created = registry.call("job_enqueue", kind="video", goal="plan test video", dedupe_key="video-1")
    assert created.ok is True
    job_id = created.data["job"]["job_id"]
    status = registry.call("job_status")
    assert status.ok is True
    assert "queued" in status.data["summary"]["counts"]
    cancelled = registry.call("job_cancel", job_id=job_id, reason="test done")
    assert cancelled.ok is True
    assert cancelled.data["job"]["status"] == "cancelled"


def test_validation_cli_smoke():
    cp = subprocess.run([sys.executable, "-m", "winlocalassistant.validate", "--all"], text=True, capture_output=True, timeout=120)
    assert cp.returncode == 0, cp.stdout + cp.stderr
    assert "Nova Validation" in cp.stdout
    assert "creative_worker_fixture" in cp.stdout
