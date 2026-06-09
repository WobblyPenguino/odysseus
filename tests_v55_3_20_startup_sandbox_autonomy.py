
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.sandbox_manager import PROFILES, _effective_profile, start_sandbox


def test_windows_bat_opens_browser_for_web_mode():
    bat = Path("start_windows_assistant.bat").read_text(encoding="utf-8")
    assert "http://127.0.0.1:8766" in bat
    assert "Start-Process" in bat
    assert "app.py --web" in bat
    assert "docker info" in bat
    assert "Docker Desktop.exe" in bat


def test_webui_defines_check_model_setup_hook():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "function checkModelSetup()" in html
    assert "setInterval(checkModelSetup" in html


def test_kali_tools_image_preferred_over_default_when_present(monkeypatch, tmp_path):
    import winlocalassistant.sandbox_manager as sm
    cfg = AssistantConfig(workspace=str(tmp_path))
    cfg.sandbox_kali_image = "kalilinux/kali-rolling"
    monkeypatch.setattr(sm, "_image_exists", lambda runtime, image: image == "wla-kali-tools:latest")
    prof = _effective_profile(cfg, PROFILES["kali"], "docker")
    assert prof.image == "wla-kali-tools:latest"


def test_explicit_non_default_kali_image_still_wins(monkeypatch, tmp_path):
    import winlocalassistant.sandbox_manager as sm
    cfg = AssistantConfig(workspace=str(tmp_path))
    cfg.sandbox_kali_image = "my-kali:dev"
    monkeypatch.setattr(sm, "_image_exists", lambda runtime, image: True)
    prof = _effective_profile(cfg, PROFILES["kali"], "docker")
    assert prof.image == "my-kali:dev"


def test_autonomous_sandbox_goal_skips_model_heavy_proposal_step():
    src = Path("winlocalassistant/core.py").read_text(encoding="utf-8")
    assert "Sandbox-focused autonomous request detected" in src
    assert "sandbox_focused_goal" in src
    assert "Propose improvements from evidence" in src
