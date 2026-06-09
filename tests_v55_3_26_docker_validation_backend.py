from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.docker_manager import docker_validate_project
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry


def test_docker_validate_project_copies_workspace_and_saves_report(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm
    src = tmp_path / "project"
    src.mkdir()
    (src / "app.py").write_text("print('ok')\n", encoding="utf-8")
    (src / "__pycache__").mkdir()
    (src / "__pycache__" / "ignored.pyc").write_bytes(b"x")
    runs = tmp_path / "docker_runs"
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", runs)
    monkeypatch.setattr(dm, "DOCKER_LAST_VALIDATION_PATH", tmp_path / "last_validation.json")
    monkeypatch.setattr(dm, "_docker_cli", lambda: "docker")
    captured = {}

    def fake_run(args, timeout=20):
        captured["args"] = args
        return {"ok": True, "returncode": 0, "stdout": "compiled", "stderr": "", "elapsed_sec": 0.1, "command": args}

    monkeypatch.setattr(dm, "_run", fake_run)
    payload = docker_validate_project(AssistantConfig(workspace=str(tmp_path)), path=str(src), command="python app.py")
    assert payload["ok"] is True
    assert payload["copy_info"]["copied_files"] == 1
    assert "--network" in captured["args"]
    assert "none" in captured["args"]
    assert (Path(payload["run_dir"]) / "validation_report.json").exists()
    assert (tmp_path / "last_validation.json").exists()


def test_docker_validate_command_is_wired_through_core(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    calls = []

    def fake_call(name, **kwargs):
        calls.append((name, kwargs))
        from winlocalassistant.tools import ToolResult
        return ToolResult(True, "Docker validation passed", {"message": "validated"})

    monkeypatch.setattr(core.tools, "call", fake_call)
    reply = core.handle_command("/docker-validate python -m compileall -q winlocalassistant")
    assert "validated" in reply
    assert calls[0][0] == "docker_validate"
    assert calls[0][1]["command"] == "python -m compileall -q winlocalassistant"


def test_tool_registry_exposes_docker_validate(tmp_path, monkeypatch):
    import winlocalassistant.tools as tools_mod

    def fake_validate(config, path=".", command="", image="python:3.12-slim", timeout=300):
        return {"ok": True, "summary": "Docker validation passed", "run_id": "test", "image": image, "command": command, "workspace_copy": str(tmp_path), "copy_info": {"copied_files": 2, "skipped_items": 0}, "raw": {"stdout": "ok", "stderr": ""}}

    monkeypatch.setattr(tools_mod, "docker_validate_project", fake_validate)
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    result = registry.call("docker_validate", path=".", command="python --version")
    assert result.ok is True
    assert "Docker Project Validation" in result.data["message"]
    assert "python --version" in result.data["message"]


def test_webui_has_docker_validation_button():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/docker-validate" in html
    assert "Quick validate" in html
    assert "Last validation" in html
