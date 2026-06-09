from pathlib import Path
import json
import subprocess

from winlocalassistant.config import AssistantConfig
from winlocalassistant.docker_manager import docker_promote_validated_patch


def test_webui_has_missing_popup_containers_and_flat_quick_controls():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert 'id="releaseChecklistPopup"' in src
    assert 'id="chatsPopup"' in src
    assert "function showReleaseChecklistPopup" in src
    assert "function showChatsPopup" in src
    assert "runQuickCommand" in src
    assert "one command per line" in src
    assert "Object.keys(groups).map" not in src
    assert "quickControlsBox" in src


def test_webui_preserves_activity_and_chat_on_refresh():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "fetch('/api/activity?since=0')" in src
    assert "restoreActiveChatSession" in src
    assert "persistCurrentChatSoon" in src
    assert "for(const rid of ids.slice(0," in src


def test_webui_hides_active_planning_panel_after_reply():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "function replyActiveRun()" in src
    assert "box.style.display='none'" in src
    assert "box.innerHTML=''" in src


def _init_git_workspace(path: Path) -> None:
    subprocess.run(["git", "init"], cwd=path, check=True, text=True, capture_output=True)
    subprocess.run(["git", "config", "user.email", "wla@example.local"], cwd=path, check=True)
    subprocess.run(["git", "config", "user.name", "Nova Test"], cwd=path, check=True)


def test_promote_validated_patch_tolerates_windows_crlf(monkeypatch, tmp_path):
    import winlocalassistant.docker_manager as dm
    monkeypatch.setattr(dm, "APP_DIR", tmp_path / "profile")
    monkeypatch.setattr(dm, "DOCKER_RUNS_DIR", tmp_path / "docker_runs")
    workspace = tmp_path / "repo"
    workspace.mkdir()
    _init_git_workspace(workspace)
    # Simulate a Windows worktree file with CRLF while the patch was produced in a Linux copy.
    (workspace / "app.txt").write_bytes(b"old\r\n")
    run_id = "run_patch_crlf"
    run_dir = tmp_path / "docker_runs" / run_id
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
    report = {"ok": True, "run_id": run_id, "type": "patch_validation", "patch_path": str(patch), "source_path": str(workspace)}
    (run_dir / "validation_report.json").write_text(json.dumps(report), encoding="utf-8")
    result = docker_promote_validated_patch(AssistantConfig(workspace=str(workspace)), run_id=run_id, path=str(workspace), local_command="python -c \"print('ok')\"")
    assert result["ok"] is True, result
    assert "new" in (workspace / "app.txt").read_text(encoding="utf-8")
