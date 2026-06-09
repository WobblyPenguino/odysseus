from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.docker_manager import docker_validate_project
from winlocalassistant.tools import ToolRegistry
from winlocalassistant import __version__

ROOT = Path(__file__).resolve().parent


def test_clean_workspace_gui_has_visible_version_and_toggle():
    src = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "Nova v55.3.164" in src or "Nova v55.3.161" in src or "Nova v55.3.159" in src
    assert "novaVersionBadge" in src
    assert "clean-workspace" in src
    assert "toggleCleanWorkspace" in src
    assert "applyCleanWorkspaceMode" in src
    assert "Docker validation skipped" in src or "docker validation skipped" in src.lower()


def test_release_metadata_mentions_159():
    assert __version__ in (ROOT / "winlocalassistant" / "__init__.py").read_text(encoding="utf-8")
    assert f"Nova v{__version__}" in (ROOT / "README.md").read_text(encoding="utf-8")
    assert __version__ in (ROOT / "RELEASE_MANIFEST.json").read_text(encoding="utf-8")


def test_docker_validate_skips_gracefully_when_daemon_pipe_missing(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm

    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("print('ok')\n", encoding="utf-8")
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", tmp_path / "docker_runs")
    monkeypatch.setattr(dm, "DOCKER_LAST_VALIDATION_PATH", tmp_path / "last_validation.json")
    monkeypatch.setattr(dm, "_docker_cli", lambda: "docker")

    def fake_run(args, timeout=20):
        return {
            "ok": False,
            "returncode": 1,
            "stdout": "",
            "stderr": "failed to connect to the Docker API at npipe:////./pipe/dockerDesktopLinuxEngine: The system cannot find the file specified.",
            "elapsed_sec": 0.1,
            "command": args,
        }

    monkeypatch.setattr(dm, "_run", fake_run)
    payload = docker_validate_project(AssistantConfig(workspace=str(tmp_path)), path=str(project), command="python app.py")
    assert payload["ok"] is True
    assert payload["skipped"] is True
    assert payload["degraded"] is True
    assert "unavailable" in payload["summary"].lower()
    assert payload["next_steps"]


def test_tool_registry_renders_docker_skip_as_skipped(tmp_path, monkeypatch):
    import winlocalassistant.tools as tools_mod

    def fake_validate(config, path=".", command="", image="python:3.12-slim", timeout=300):
        return {
            "ok": True,
            "skipped": True,
            "degraded": True,
            "summary": "Docker validation skipped - Docker Desktop/Linux engine is unavailable",
            "run_id": "skiptest",
            "image": image,
            "command": command,
            "workspace_copy": "",
            "copy_info": {"copied_files": 0, "skipped_items": 0},
            "reason": "daemon not running",
            "next_steps": ["Start Docker Desktop"],
            "raw": {"stderr": "daemon unavailable"},
        }

    monkeypatch.setattr(tools_mod, "docker_validate_project", fake_validate)
    result = ToolRegistry(AssistantConfig(workspace=str(tmp_path))).call("docker_validate", path=".", command="python --version")
    assert result.ok is True
    assert "Status: **SKIPPED**" in result.data["message"]
    assert "Start Docker Desktop" in result.data["message"]
