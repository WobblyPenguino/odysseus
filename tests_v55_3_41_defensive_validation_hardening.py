from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore, load_idle_autonomy_settings
from winlocalassistant.security_status import build_security_status, render_security_status
from winlocalassistant.integration_radar import build_integration_radar
from winlocalassistant.release_checklist import build_release_checklist


def test_avatar_current_task_prefers_live_working_text(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    core.autonomous_state["current_action"] = "Idle"
    core._set_avatar("working", "", "Working", "Processing current request...")
    data = core.avatar_status_data()
    assert data["current_task"] == "Processing current request..."
    assert "Live state" in data.get("disclosure", "")
    assert "Idle" not in data.get("current_task", "")


def test_idle_low_risk_auto_apply_defaults_enabled_without_settings_file(monkeypatch, tmp_path):
    import winlocalassistant.core as core_mod
    monkeypatch.setattr(core_mod, "_idle_autonomy_settings_path", lambda: tmp_path / "missing.json")
    assert load_idle_autonomy_settings()["idle_auto_apply_low_risk"] is True


def test_security_status_renders_defensive_only_report():
    payload = build_security_status()
    text = render_security_status(payload)
    assert "Defensive Security Status" in text
    assert "defensive-only" in text.lower()
    assert "offensive" in text.lower()
    assert "recommendations" in payload


def test_integration_radar_includes_defensive_security_status(tmp_path):
    payload = build_integration_radar(tmp_path, "improve Nova security visibility")
    names = [c["name"] for c in payload["candidates"]]
    assert "Defensive security status" in names


def test_release_checklist_mentions_security_status(tmp_path):
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "NOVA_DOCTOR_LATEST.json").write_text('{"ok": true, "summary":"ok"}', encoding="utf-8")
    (tmp_path / "docs" / "NOVA_RELEASE_GATE_LATEST.json").write_text('{"ok": true, "summary":"ok"}', encoding="utf-8")
    (tmp_path / "CHANGELOG.md").write_text("x" * 150, encoding="utf-8")
    (tmp_path / "README.md").write_text("x" * 150, encoding="utf-8")
    payload = build_release_checklist(tmp_path)
    names = [i["name"] for i in payload["items"]]
    assert "Defensive security status" in names
