from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolResult


def test_autonomous_docker_preflight_skips_when_docker_unavailable(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    calls = []

    def fake_autonomous_call(title, tool, kwargs, report, run_id):
        calls.append((title, tool, kwargs))
        assert tool == "docker_status"
        return ToolResult(False, "Docker diagnostics completed", {"installed": False, "daemon_running": False})

    monkeypatch.setattr(core, "_autonomous_call_tool", fake_autonomous_call)
    report = []
    should_run, reason, data = core._autonomous_docker_validation_preflight(report, "run-test")
    assert should_run is False
    assert "Docker is unavailable" in reason
    assert core.autonomous_state["docker_validation_skipped_reason"]
    assert any("Docker validation skipped" in line for line in report)


def test_autonomous_docker_preflight_skips_surprise_image_pull(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)

    def fake_autonomous_call(title, tool, kwargs, report, run_id):
        return ToolResult(True, "Docker is ready", {"installed": True, "daemon_running": True, "images": []})

    monkeypatch.setattr(core, "_autonomous_call_tool", fake_autonomous_call)
    should_run, reason, data = core._autonomous_docker_validation_preflight([], "run-test")
    assert should_run is False
    assert "is not local" in reason
    assert "docker-smoke" in reason


def test_autonomous_docker_checkpoint_records_state(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    seen = []

    def fake_autonomous_call(title, tool, kwargs, report, run_id):
        seen.append((title, tool, kwargs))
        assert tool == "docker_validate"
        assert kwargs["path"] == "."
        assert "compileall" in kwargs["command"]
        return ToolResult(True, "Docker validation passed", {"run_id": "docker-run-1", "run_dir": str(tmp_path / "docker-run-1"), "command": kwargs["command"]})

    monkeypatch.setattr(core, "_autonomous_call_tool", fake_autonomous_call)
    ok, result = core._autonomous_docker_validation_checkpoint([], "run-test", stage="pre-action", required=True)
    assert ok is True
    assert result is not None and result.ok
    assert core.autonomous_state["last_docker_validation"]["stage"] == "pre-action"
    assert core.autonomous_state["last_docker_validation"]["run_id"] == "docker-run-1"


def test_autonomous_cycle_source_contains_docker_gates():
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "_autonomous_docker_validation_preflight" in src
    assert "_autonomous_docker_validation_checkpoint(report, run_id, stage=\"pre-action\", required=True)" in src
    assert "_autonomous_docker_validation_checkpoint(report, run_id, stage=\"post-action\", required=False)" in src
    assert "Docker pre-action validation failed; mutation skipped" in src
    assert "--no-docker" in src
