from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.docker_manager import docker_status, render_docker_markdown


def test_docker_status_handles_missing_cli(monkeypatch, tmp_path):
    import winlocalassistant.docker_manager as dm
    monkeypatch.setattr(dm, "_docker_cli", lambda: "")
    monkeypatch.setattr(dm, "_wsl_cli", lambda: "")
    payload = docker_status(AssistantConfig(workspace=str(tmp_path)))
    assert payload["installed"] is False
    assert payload["daemon_running"] is False
    assert payload["notes"]
    assert "Docker CLI" in render_docker_markdown(payload)


def test_docker_status_parses_container_json(monkeypatch, tmp_path):
    import winlocalassistant.docker_manager as dm
    monkeypatch.setattr(dm, "_docker_cli", lambda: "docker")
    monkeypatch.setattr(dm, "_wsl_cli", lambda: "")

    def fake_run(args, timeout=20):
        cmd = " ".join(args)
        if "--version" in cmd:
            return {"ok": True, "stdout": "Docker version 29.0.0", "stderr": "", "returncode": 0, "command": args}
        if "compose version" in cmd:
            return {"ok": True, "stdout": "Docker Compose version v2.40.0", "stderr": "", "returncode": 0, "command": args}
        if "info" in cmd:
            return {"ok": True, "stdout": "Server Version: 29.0.0", "stderr": "", "returncode": 0, "command": args}
        if "ps -a" in cmd:
            return {"ok": True, "stdout": '{"Names":"wla-test","Image":"python:3.12-slim","Status":"Up 2 seconds"}\n', "stderr": "", "returncode": 0, "command": args}
        if "images" in cmd:
            return {"ok": True, "stdout": '{"Repository":"python","Tag":"3.12-slim"}\n', "stderr": "", "returncode": 0, "command": args}
        return {"ok": True, "stdout": "", "stderr": "", "returncode": 0, "command": args}

    monkeypatch.setattr(dm, "_run", fake_run)
    payload = docker_status(AssistantConfig(workspace=str(tmp_path)))
    assert payload["installed"] is True
    assert payload["daemon_running"] is True
    assert payload["compose_available"] is True
    assert payload["containers"][0]["Names"] == "wla-test"


def test_core_docker_commands_are_registered(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "docker_status" in core.tools.tools
    assert "docker_ps" in core.tools.tools
    assert "docker_smoke" in core.tools.tools
    assert "docker_help" in core.tools.tools
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert '"/docker-status"' in src
    assert '"/docker-smoke"' in src


def test_webui_has_docker_tab_and_safe_js():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "tab_docker" in src
    assert "dockerPanel" in src
    assert "/api/docker-status" in src
    assert "function loadDockerStatus()" in src
    assert "quick('/sandbox-approve yes')" not in src
