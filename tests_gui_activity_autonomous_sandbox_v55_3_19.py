from dataclasses import replace
from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence
from winlocalassistant.config import AssistantConfig
from winlocalassistant.sandbox_manager import PROFILES, _effective_profile


def test_version_55_3_20():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_live_activity_uses_stable_minimize_not_hidden_display_none():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "activityToggleBtn" in html
    assert "toggleActivityOpen" in html
    assert "#activityLog{display:none" in html or "log.hidden=!open" in html
    assert "body.collapse-activity .activity{display:block" in html
    assert "body.collapse-activity .activity{display:none" not in html
    assert "Live activity" in html and "Minimize" in html


def test_autonomous_status_ui_surfaces_stale_state_and_current_tool():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "last_progress_age_sec" in html
    assert "may_be_stuck" in html
    assert "Current tool:" in html
    assert "Possible stall" in html


def test_ollama_raw_diagnostics_open_by_default():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "<details open><summary>Raw diagnostic details</summary>" in html
    assert "cache:'no-store'" in html


def test_sandbox_sequence_tests_actual_sandboxes_for_sandbox_goal():
    plan = build_autonomous_tool_sequence(
        "test sandbox execution, check Linux and Kali availability, and report what works without changing host files",
        {"sandbox": {"autonomous_sandbox_mode": True, "sandboxes": {}}},
    )
    tools = [(s.tool, s.kwargs.get("profile"), s.kwargs.get("command", "")) for s in plan.steps]
    assert plan.intent == "sandbox_verification"
    assert ("sandbox_start", "linux", "") in tools
    assert ("sandbox_start", "kali", "") in tools
    assert any(t == "sandbox_exec" and p == "linux" for t, p, c in tools)
    assert any(t == "sandbox_exec" and p == "kali" and "nmap" in c for t, p, c in tools)


def test_effective_kali_image_prefers_configured_image(monkeypatch, tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    cfg.sandbox_kali_image = "wla-kali-tools:latest"
    prof = _effective_profile(cfg, PROFILES["kali"], "docker")
    assert prof.image == "wla-kali-tools:latest"
