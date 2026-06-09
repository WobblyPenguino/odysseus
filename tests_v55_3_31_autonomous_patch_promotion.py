from pathlib import Path
import json
import subprocess

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.docker_manager import docker_promote_validated_patch


def _init_git_workspace(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, text=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "wla@example.local"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Nova Test"], cwd=path, check=True)


def _write_validated_patch_run(monkeypatch, tmp_path: Path, workspace: Path, ok: bool = True) -> str:
    import winlocalassistant.docker_manager as dm
    runs = tmp_path / "docker_runs"
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", runs)
    run_id = "run_patch_001"
    run_dir = runs / run_id
    run_dir.mkdir(parents=True)
    patch = run_dir / "input.patch"
    patch.write_text(
        "diff --git a/app.txt b/app.txt\n"
        "--- a/app.txt\n"
        "+++ b/app.txt\n"
        "@@ -1 +1 @@\n"
        "-old\n"
        "+new\n",
        encoding="utf-8",
    )
    report = {
        "ok": ok,
        "summary": "Docker patch validation passed" if ok else "Docker patch validation failed",
        "run_id": run_id,
        "type": "patch_validation",
        "stage": "docker_validate",
        "patch_path": str(patch),
        "source_path": str(workspace),
        "command": "python -c pass",
    }
    (run_dir / "validation_report.json").write_text(json.dumps(report), encoding="utf-8")
    return run_id


def test_promote_validated_patch_applies_to_live_tree(monkeypatch, tmp_path):
    import winlocalassistant.docker_manager as dm
    monkeypatch.setattr(dm, "APP_DIR", tmp_path / "profile")
    workspace = tmp_path / "repo"
    workspace.mkdir()
    _init_git_workspace(workspace)
    (workspace / "app.txt").write_text("old\n", encoding="utf-8")
    run_id = _write_validated_patch_run(monkeypatch, tmp_path, workspace, ok=True)
    cfg = AssistantConfig(workspace=str(workspace))
    result = docker_promote_validated_patch(cfg, run_id=run_id, path=str(workspace), local_command="python -c 'print(\"ok\")'")
    assert result["ok"] is True
    assert "promoted" in result["summary"]
    assert (workspace / "app.txt").read_text(encoding="utf-8") == "new\n"
    assert (Path(result["backup_dir"]) / "promotion_report.json").exists()


def test_promotion_local_command_runner_handles_python_quotes_and_globs(tmp_path):
    from winlocalassistant.docker_manager import _run_local_command

    quoted = _run_local_command('python -c \'print("ok")\'', cwd=tmp_path)
    assert quoted["ok"] is True
    assert "ok" in quoted["stdout"]

    (tmp_path / "tests_demo.py").write_text("x = 1\n", encoding="utf-8")
    globbed = _run_local_command("python -m compileall -q tests_*.py", cwd=tmp_path)
    assert globbed["ok"] is True


def test_promote_rejects_failed_patch_validation(monkeypatch, tmp_path):
    import winlocalassistant.docker_manager as dm
    monkeypatch.setattr(dm, "APP_DIR", tmp_path / "profile")
    workspace = tmp_path / "repo"
    workspace.mkdir()
    _init_git_workspace(workspace)
    (workspace / "app.txt").write_text("old\n", encoding="utf-8")
    run_id = _write_validated_patch_run(monkeypatch, tmp_path, workspace, ok=False)
    cfg = AssistantConfig(workspace=str(workspace))
    result = docker_promote_validated_patch(cfg, run_id=run_id, path=str(workspace), local_command="python -c 'print(\"ok\")'")
    assert result["ok"] is False
    assert "did not pass" in result["summary"]
    assert (workspace / "app.txt").read_text(encoding="utf-8") == "old\n"


def test_core_exposes_patch_promotion_commands_and_autonomous_parser(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    assert core._autonomous_extract_promote_patch_run_id("--promote-patch abc123 improve Nova") == "abc123"
    assert core._autonomous_extract_promote_patch_run_id("promote validated patch run_1") == "run_1"
    assert core._autonomous_extract_promote_patch_run_id("normal autonomous run") == "__NO_PROMOTION_REQUEST__"
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "/docker-promote-patch" in src
    assert "docker_promote_patch" in src


def test_tools_registry_includes_docker_promote_patch(tmp_path):
    from winlocalassistant.tools import ToolRegistry
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    assert "docker_promote_patch" in reg.tools
