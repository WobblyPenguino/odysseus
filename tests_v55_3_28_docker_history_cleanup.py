import json
import time
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.docker_manager import docker_cleanup, docker_validation_history
from winlocalassistant.tools import ToolRegistry


def _write_report(run_dir: Path, run_id: str, ok: bool = True):
    run_dir.mkdir(parents=True, exist_ok=True)
    (run_dir / "validation_report.json").write_text(json.dumps({
        "run_id": run_id,
        "ok": ok,
        "summary": "Docker validation passed" if ok else "Docker validation failed",
        "command": "python -m compileall -q winlocalassistant",
        "image": "python:3.12-slim",
        "raw": {"elapsed_sec": 0.2},
    }), encoding="utf-8")


def test_docker_validation_history_reads_saved_reports(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm
    runs = tmp_path / "docker_runs"
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", runs)
    _write_report(runs / "run-old", "run-old", ok=True)
    time.sleep(0.01)
    _write_report(runs / "run-new", "run-new", ok=False)
    payload = docker_validation_history(AssistantConfig(workspace=str(tmp_path)), limit=10)
    assert payload["ok"] is True
    assert [r["run_id"] for r in payload["runs"]][:2] == ["run-new", "run-old"]
    assert payload["runs"][0]["ok"] is False


def test_docker_cleanup_keeps_newest_runs(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm
    runs = tmp_path / "docker_runs"
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", runs)
    for i in range(4):
        _write_report(runs / f"run-{i}", f"run-{i}")
        time.sleep(0.01)
    payload = docker_cleanup(AssistantConfig(workspace=str(tmp_path)), keep=2)
    remaining = sorted(p.name for p in runs.iterdir() if p.is_dir())
    assert payload["ok"] is True
    assert len(payload["removed"]) == 2
    assert remaining == ["run-2", "run-3"]


def test_core_wires_docker_history_and_clean_commands(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    calls = []

    def fake_call(name, **kwargs):
        calls.append((name, kwargs))
        from winlocalassistant.tools import ToolResult
        return ToolResult(True, "ok", {"message": name + " ok"})

    monkeypatch.setattr(core.tools, "call", fake_call)
    assert "docker_history ok" in core.handle_command("/docker-history 5")
    assert "docker_clean ok" in core.handle_command("/docker-clean 3")
    assert ("docker_history", {"limit": 5}) in calls
    assert ("docker_clean", {"keep": 3}) in calls


def test_tool_registry_exposes_docker_history_cleanup(tmp_path, monkeypatch):
    import winlocalassistant.tools as tools_mod
    monkeypatch.setattr(tools_mod, "docker_validation_history", lambda config, limit=20: {"ok": True, "summary": "loaded", "runs": [], "limit": limit})
    monkeypatch.setattr(tools_mod, "docker_cleanup", lambda config, keep=20: {"ok": True, "summary": "cleaned", "removed": [], "kept": keep})
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    assert registry.call("docker_history", limit=7).ok is True
    assert registry.call("docker_clean", keep=7).ok is True


def test_webui_exposes_docker_history_and_cleanup_controls():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/docker-history" in html
    assert "/docker-clean 20" in html
    assert "Recent validations" in html
    assert "Quick validate" in html
