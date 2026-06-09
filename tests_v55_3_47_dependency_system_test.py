from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.dependency_check import _resolve_cli_executable, build_dependency_report, render_dependency_report
from winlocalassistant.system_test import run_massive_system_test, render_massive_system_test
from winlocalassistant.feature_audit import build_feature_audit


def test_current_version_metadata():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_dependency_report_is_bounded_and_renderable():
    report = build_dependency_report()
    text = render_dependency_report(report)
    assert "Nova Dependency Check" in text
    assert "pytest" in text
    assert "docker" in text.lower()
    assert "missing_required" in report


def test_dependency_checker_prefers_windows_cmd_shim_for_npm(monkeypatch):
    import winlocalassistant.dependency_check as dc

    monkeypatch.setattr(dc.os, "name", "nt")
    monkeypatch.setattr(dc.shutil, "which", lambda name: f"C:/nodejs/{name}" if name == "npm.cmd" else "")
    assert _resolve_cli_executable("npm").endswith("npm.cmd")


def test_bat_runs_dependency_checker_before_launch():
    bat = Path("start_windows_assistant.bat").read_text(encoding="utf-8")
    assert "winlocalassistant.dependency_check" in bat
    assert "Install missing Python packages" in bat or "dependency" in bat.lower()
    assert "Continue anyway" in bat


def test_webui_has_confirmed_massive_test_button_and_command():
    webui = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "confirmMassiveSystemTest" in webui
    assert "/massive-test --confirm" in webui
    assert "Massive system test" in webui


def test_core_routes_dependency_and_massive_test():
    core = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "/dependency-check" in core
    assert "/massive-test" in core
    assert "run_massive_system_test" in core


def test_feature_audit_covers_dependency_and_massive_system_test():
    payload = build_feature_audit(Path("."))
    names = {c["name"]: c for c in payload["checks"]}
    assert "dependency_and_massive_system_test" in names
    assert names["dependency_and_massive_system_test"]["status"] == "implemented"


def test_massive_system_test_render_smoke(monkeypatch, tmp_path):
    # Avoid running real commands here; this checks reporting renderer shape.
    payload = {"ok": True, "duration_sec": 1.2, "steps": [{"name": "dependency_check", "ok": True, "summary": "ok"}]}
    text = render_massive_system_test(payload)
    assert "Nova Massive System Test" in text
    assert "dependency_check" in text


def test_massive_system_test_treats_offline_docker_daemon_as_optional(monkeypatch, tmp_path):
    import winlocalassistant.system_test as st

    monkeypatch.setattr(st.shutil, "which", lambda name: "docker.exe" if name == "docker" else "")
    monkeypatch.setattr(st, "build_dependency_report", lambda: {"python_ok": True, "missing_required": []})
    monkeypatch.setattr(st, "run_wla_doctor", lambda root, goal: {"ok": True, "summary": "doctor ok", "markdown_path": ""})
    monkeypatch.setattr(st, "build_feature_audit", lambda root: {"ok": True, "summary": "features ok", "markdown_path": ""})
    monkeypatch.setattr(st, "docker_status", lambda config, include_raw=False: {
        "daemon_running": False,
        "notes": ["Docker CLI exists, but the Docker daemon did not respond."],
    })
    monkeypatch.setattr(st, "_run", lambda name, args, cwd, timeout=240: {"name": name, "ok": True, "summary": "stub"})
    payload = run_massive_system_test(tmp_path, include_docker=True, include_playwright=False)
    steps = {s["name"]: s for s in payload["steps"]}
    assert payload["ok"] is True
    assert steps["docker_daemon_optional"]["ok"] is True
    assert steps["docker_daemon_optional"]["skipped"] is True
    assert "Start Docker Desktop" in steps["docker_daemon_optional"]["summary"]
    assert "docker_ps" not in steps
