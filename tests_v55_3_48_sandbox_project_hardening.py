from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.game_design import build_generic_canvas_game_project
from winlocalassistant.projects import list_projects, register_project
from winlocalassistant.project_runtime_probe import run_project_runtime_probe
from winlocalassistant.request_intent import analyze_request_intent
from winlocalassistant.sandbox_manager import detect_runtime, sandbox_status, start_sandbox
from winlocalassistant.tools import ToolRegistry


def test_version_55_3_48_current():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_visible_assistant_name_is_nova_without_version_change():
    from winlocalassistant import ASSISTANT_NAME

    assert ASSISTANT_NAME == "Nova"
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)


def test_autonomous_wla_goal_resolves_to_source_target(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=False))
    text = "work on your coding and validation capabilities"
    assert core._autonomous_goal_targets_wla_source(text, analyze_request_intent(text))


def test_transient_pytest_project_registration_is_not_persisted(monkeypatch, tmp_path):
    import winlocalassistant.projects as projects

    monkeypatch.setattr(projects, "PROJECTS_PATH", tmp_path / "projects.json")
    transient = tmp_path / "pytest-of-Daniel" / "pytest-1" / "RealProject"
    transient.mkdir(parents=True)
    row = register_project("RealProject", str(transient), make_current=True)
    assert row["transient"] is True
    assert list_projects() == []


def test_write_one_does_not_crash_on_sibling_prefix_path(tmp_path):
    # Regression for Tinyapp vs Tinyappproject: string-prefix containment is not
    # the same as pathlib relative containment.
    workspace = tmp_path / "Tinyapp"
    sibling = tmp_path / "Tinyappproject"
    workspace.mkdir()
    cfg = AssistantConfig(workspace=str(workspace), allow_mutating_tools=True)
    registry = ToolRegistry(cfg)
    target = sibling / "index.html"
    info = registry._write_one(target, "<h1>ok</h1>")
    assert info["path"].endswith("index.html")
    assert target.exists()


def test_model_top_level_sibling_project_folder_is_stripped(tmp_path):
    root = tmp_path / "Tinyapp"
    root.mkdir()
    cfg = AssistantConfig(workspace=str(root), allow_mutating_tools=True)
    registry = ToolRegistry(cfg)
    written = []
    registry._apply_model_files_to_root(root, "Tinyapp", {"Tinyappproject/index.html": "<h1>ok</h1>"}, written)
    assert (root / "index.html").exists()
    assert not (root / "Tinyappproject" / "index.html").exists()


def test_repair_diagnostic_text_does_not_trigger_game_domain_requirements(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    registry = ToolRegistry(cfg)
    reqs = registry._goal_domain_requirements(
        "Repair the current project in-place so it fully satisfies the original request. "
        "Original request: make a tiny useful app\n"
        "Failure/acceptance problems: Dodge Game default appeared even though the user did not request a dodge game."
    )
    assert "game" not in reqs


def test_failed_repair_wrapper_uses_original_user_goal_for_validation(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    registry = ToolRegistry(cfg)
    wrapped_goal = (
        "Repair the current project in-place. Do not create a nested folder. "
        "Original user goal: make a tiny useful app\n"
        "Failed step: Extract requirements, generate code with local LLM, write files, test and repair\n"
        "Failure details: model output did not implement the requested domain: "
        "[{\"domain\":\"game\",\"needed_any_of\":[\"score\",\"game\",\"controls\",\"interaction\"]}]"
    )
    project = {
        "files": {
            "index.html": "<main><h1>Tiny Useful App</h1><input id='note'><button id='save'>Save</button><button id='export'>Export</button><ul id='items'></ul><script src='app.js'></script></main>",
            "app.js": "const items=JSON.parse(localStorage.getItem('items')||'[]');function render(){document.getElementById('items').innerHTML=items.map(x=>`<li>${x}</li>`).join('')}document.getElementById('save').addEventListener('click',()=>{items.push(document.getElementById('note').value||'note');localStorage.setItem('items',JSON.stringify(items));render()});document.getElementById('export').addEventListener('click',()=>{const blob=new Blob([JSON.stringify(items)],{type:'application/json'});const a=document.createElement('a');a.download='items.json';a.href=URL.createObjectURL(blob);a.click()});render();",
            "style.css": "body{font-family:Segoe UI,Arial,sans-serif}button,input{padding:10px}",
        }
    }
    ok, reason = registry._validate_model_project(project, wrapped_goal)

    assert ok, reason
    assert "game" not in registry._goal_domain_requirements(wrapped_goal)


def test_platformer_fallback_contains_real_platformer_mechanics():
    project = build_generic_canvas_game_project("make a platformer game")
    js = project["files"]["app.js"].lower()
    assert project["verify_command"] == "node --check app.js"
    assert "manual_test_steps" in project
    assert "gravity" in js
    assert "vy" in js
    assert "onground" in js
    assert "platforms" in js
    assert "jumpimpulse" in js
    probe = run_project_runtime_probe("make a platformer game", sources=project["files"])
    assert probe["passed"]


def test_fake_platformer_top_down_game_is_rejected_by_runtime_probe():
    fake = {
        "index.html": "<p>Platformer with jumping gravity platforms goal</p><canvas></canvas>",
        "app.js": "let player={x:0,y:0,speed:1}; let score=0; document.addEventListener('keydown',()=>{}); function update(){player.y+=1; score++; draw(); requestAnimationFrame(update)} function collision(){} function restart(){}",
    }
    probe = run_project_runtime_probe("make a platformer game", sources=fake)
    assert not probe["passed"]
    assert any(check["name"].startswith("platformer_") and not check["ok"] for check in probe["checks"])


def test_prose_verify_command_is_skipped_instead_of_run_as_powershell(tmp_path):
    (tmp_path / "index.html").write_text("<canvas></canvas><script src='app.js'></script>", encoding="utf-8")
    (tmp_path / "app.js").write_text(build_generic_canvas_game_project("make a platformer game")["files"]["app.js"], encoding="utf-8")
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True))
    result = registry._project_quality_verify(tmp_path, {
        "goal": "make a platformer game",
        "main_file": "index.html",
        "verify_command": "node --check app.js if Node is available; then open index.html and play-test controls/objective/restart",
    })
    names = [check.get("name") for check in result.data.get("checks", [])]
    assert "manifest_verify_skipped" in names
    assert "manifest_verify" not in names


def test_detect_runtime_reports_daemon_not_running(monkeypatch, tmp_path):
    import shutil
    import winlocalassistant.sandbox_manager as sm

    monkeypatch.setattr(shutil, "which", lambda name: f"C:/fake/{name}.exe" if name == "docker" else None)

    def fake_run(args, **kwargs):
        if args[:2] == ["docker", "--version"]:
            return type("Proc", (), {"returncode": 0, "stdout": "Docker version test", "stderr": ""})()
        if args[:2] == ["docker", "info"]:
            return type("Proc", (), {"returncode": 1, "stdout": "", "stderr": "failed to connect to the docker API at npipe:////./pipe/dockerDesktopLinuxEngine"})()
        raise AssertionError(args)

    monkeypatch.setattr(sm.subprocess, "run", fake_run)
    cfg = AssistantConfig(workspace=str(tmp_path))
    rt = detect_runtime(cfg)
    assert rt["available"] is True
    assert rt["daemon_running"] is False
    assert "Docker Desktop" in rt["hint"]


def test_detect_runtime_does_not_show_repair_hint_when_daemon_is_running(monkeypatch, tmp_path):
    import shutil
    import winlocalassistant.sandbox_manager as sm

    monkeypatch.setattr(shutil, "which", lambda name: f"C:/fake/{name}.exe" if name == "docker" else None)

    def fake_run(args, **kwargs):
        if args[:2] == ["docker", "--version"]:
            return type("Proc", (), {"returncode": 0, "stdout": "Docker version test", "stderr": ""})()
        if args[:2] == ["docker", "info"]:
            return type("Proc", (), {"returncode": 0, "stdout": "Docker info ok", "stderr": ""})()
        raise AssertionError(args)

    monkeypatch.setattr(sm.subprocess, "run", fake_run)
    cfg = AssistantConfig(workspace=str(tmp_path))
    rt = detect_runtime(cfg)
    assert rt["available"] is True
    assert rt["daemon_running"] is True
    assert rt["hint"] == ""


def test_start_sandbox_fails_early_when_daemon_is_down(monkeypatch, tmp_path):
    import winlocalassistant.sandbox_manager as sm

    cfg = AssistantConfig(workspace=str(tmp_path))
    monkeypatch.setattr(sm, "detect_runtime", lambda config: {
        "available": True,
        "runtime": "docker",
        "version": "Docker version test",
        "daemon_running": False,
        "error": "npipe dockerDesktopLinuxEngine missing",
        "hint": "Start Docker Desktop",
    })
    result = start_sandbox(cfg, profile="linux")
    assert result["ok"] is False
    assert "daemon" in result["summary"].lower() or "engine" in result["summary"].lower()
    assert "Start Docker Desktop" in result["hint"]


def test_sandbox_status_marks_known_rows_unconfirmed_when_daemon_is_down(monkeypatch, tmp_path):
    import winlocalassistant.sandbox_manager as sm

    cfg = AssistantConfig(workspace=str(tmp_path))
    monkeypatch.setattr(sm, "detect_runtime", lambda config: {
        "available": True,
        "runtime": "docker",
        "version": "Docker version test",
        "daemon_running": False,
        "error": "engine stopped",
        "hint": "Start Docker Desktop",
    })
    monkeypatch.setattr(sm, "_load_state", lambda: {
        "sandboxes": {
            "linux": {
                "profile": "linux",
                "name": "wla-linux-sandbox",
                "image": "python:3.12-slim",
                "network": "none",
                "ok": True,
            }
        }
    })
    monkeypatch.setattr(sm, "_effective_profile", lambda config, prof, runtime="": prof)

    payload = sandbox_status(cfg)
    linux = payload["sandboxes"]["linux"]
    assert linux["ok"] is False
    assert "cannot be confirmed" in linux["status_note"]
