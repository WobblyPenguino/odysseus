from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolResult


def test_docker_patch_validation_copies_workspace_applies_patch_then_runs_docker(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm

    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("print('old')\n", encoding="utf-8")
    patch = tmp_path / "change.diff"
    patch.write_text(
        "diff --git a/app.py b/app.py\n"
        "--- a/app.py\n"
        "+++ b/app.py\n"
        "@@ -1 +1 @@\n"
        "-print('old')\n"
        "+print('new')\n",
        encoding="utf-8",
    )
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", tmp_path / "docker_runs")
    monkeypatch.setattr(dm, "DOCKER_LAST_VALIDATION_PATH", tmp_path / "last_validation.json")
    monkeypatch.setattr(dm, "_docker_cli", lambda: "docker")
    monkeypatch.setattr(dm.shutil, "which", lambda name: "git" if name == "git" else "docker")
    calls = []

    def fake_run(args, timeout=20):
        calls.append(args)
        if args[:3] == ["git", "-C", str((tmp_path / "docker_runs" / calls[0][2] if False else project))]:
            pass
        if args and args[0] == "git":
            return {"ok": True, "returncode": 0, "stdout": "", "stderr": "", "elapsed_sec": 0.01, "command": args}
        if args and args[0] == "docker":
            return {"ok": True, "returncode": 0, "stdout": "validated", "stderr": "", "elapsed_sec": 0.02, "command": args}
        return {"ok": False, "returncode": 1, "stdout": "", "stderr": "unexpected", "elapsed_sec": 0.01, "command": args}

    monkeypatch.setattr(dm, "_run", fake_run)
    result = dm.docker_validate_patch(AssistantConfig(workspace=str(project)), path=str(project), patch_file=str(patch))
    assert result["ok"] is True
    assert result["type"] == "patch_validation"
    assert result["stage"] == "docker_validate"
    assert (Path(result["run_dir"]) / "validation_report.json").exists()
    assert any(args and args[0] == "git" and "--check" in args for args in calls)
    assert any(args and args[0] == "git" and "apply" in args and "--check" not in args for args in calls)
    assert any(args and args[0] == "docker" and "--network" in args for args in calls)


def test_docker_patch_validation_rejects_patch_that_does_not_apply(tmp_path, monkeypatch):
    import winlocalassistant.docker_manager as dm

    project = tmp_path / "project"
    project.mkdir()
    (project / "app.py").write_text("print('old')\n", encoding="utf-8")
    patch = tmp_path / "bad.diff"
    patch.write_text("not a real patch", encoding="utf-8")
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", tmp_path / "docker_runs")
    monkeypatch.setattr(dm, "DOCKER_LAST_VALIDATION_PATH", tmp_path / "last_validation.json")
    monkeypatch.setattr(dm, "_docker_cli", lambda: "docker")
    monkeypatch.setattr(dm.shutil, "which", lambda name: "git" if name == "git" else "docker")

    def fake_run(args, timeout=20):
        assert args[0] == "git"
        return {"ok": False, "returncode": 1, "stdout": "", "stderr": "patch failed", "elapsed_sec": 0.01, "command": args}

    monkeypatch.setattr(dm, "_run", fake_run)
    result = dm.docker_validate_patch(AssistantConfig(workspace=str(project)), path=str(project), patch_file=str(patch))
    assert result["ok"] is False
    assert result["stage"] == "patch_check"
    assert "does not apply" in result["summary"]


def test_docker_validate_patch_command_routes_to_tool(tmp_path, monkeypatch):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    calls = []

    def fake_call(name, **kwargs):
        calls.append((name, kwargs))
        return ToolResult(True, "Docker patch validation passed", {"message": "patch ok", "ok": True})

    monkeypatch.setattr(core.tools, "call", fake_call)
    reply = core.handle_command("/docker-validate-patch change.diff => quick")
    assert "patch ok" in reply
    assert calls[0][0] == "docker_patch_validate"
    assert calls[0][1]["patch_file"] == "change.diff"
    assert "compileall" in calls[0][1]["command"]


def test_docker_panel_exposes_patch_validation_fill_command():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/docker-validate-patch path/to/patch.diff" in html or "/docker-validate-patch path\\to\\patch.diff" in html
    assert "Patch validate" in html
