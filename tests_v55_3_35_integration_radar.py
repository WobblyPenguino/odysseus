from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.integration_radar import build_integration_radar, render_integration_radar_markdown


def test_integration_radar_returns_ranked_candidates(tmp_path):
    payload = build_integration_radar(tmp_path, "improve Nova integrations")
    assert payload["ok"] is True
    names = [c["name"] for c in payload["candidates"]]
    assert "Docker validation backend" in names
    assert "Git safety/worktree backend" in names
    assert "Playwright browser smoke tests" in names
    assert payload["next_best"]
    md = render_integration_radar_markdown(payload)
    assert "Nova Integration Radar" in md
    assert "Next best integrations" in md
    assert (tmp_path / "docs" / "INTEGRATION_RADAR_LATEST.md").exists()
    assert (tmp_path / "docs" / "INTEGRATION_RADAR_LATEST.json").exists()


def test_integration_radar_tool_and_command_route(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    reply = core.handle_command("/integration-radar improve validation")
    assert "Integration radar completed" in reply
    assert "Nova Integration Radar" in reply


def test_wla_doctor_checks_integration_radar_route():
    src = Path("winlocalassistant/wla_doctor.py").read_text(encoding="utf-8")
    assert "integration_radar.py" in src
    assert "/integration-radar" in src


def test_webui_exposes_integration_radar_button():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/integration-radar improve Nova" in html
    assert "Integration radar" in html
