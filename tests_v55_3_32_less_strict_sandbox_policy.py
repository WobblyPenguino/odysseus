from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.sandbox_manager import evaluate_sandbox_command, sandbox_status, set_sandbox_policy, start_sandbox


def test_trusted_lab_policy_allows_kali_tool_without_pending_permission(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    set_sandbox_policy(cfg, "trusted_lab")
    policy = evaluate_sandbox_command(cfg, "kali", "nikto -h http://127.0.0.1")
    assert policy["allowed"] is True
    assert policy["policy_level"] == "trusted_lab"
    assert any("allowed" in warning for warning in policy["warnings"])


def test_less_strict_command_sets_trusted_flags(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    reply = core.handle_command("/sandbox-less-strict on")
    assert "Sandbox policy" in reply
    assert cfg.sandbox_policy_level == "trusted_lab"
    assert cfg.sandbox_allow_network is True
    assert cfg.sandbox_authorized_security_lab is True
    status = sandbox_status(cfg)
    assert status["trusted_lab_mode"] is True
    assert status["network_authorized"] is True


def test_strict_policy_still_blocks_host_escape_and_destructive_patterns(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    set_sandbox_policy(cfg, "trusted_lab")
    host_escape = evaluate_sandbox_command(cfg, "kali", "docker ps")
    assert host_escape["allowed"] is False
    assert any("host-control" in reason for reason in host_escape["reasons"])
    destructive = evaluate_sandbox_command(cfg, "linux", "rm -rf /")
    assert destructive["allowed"] is False
    assert any("destructive" in reason for reason in destructive["reasons"])


def test_kali_start_defaults_to_bridge_in_trusted_lab(monkeypatch, tmp_path):
    import winlocalassistant.sandbox_manager as sm
    cfg = AssistantConfig(workspace=str(tmp_path))
    set_sandbox_policy(cfg, "trusted_lab")
    monkeypatch.setattr(sm, "detect_runtime", lambda config: {"available": True, "runtime": "docker", "version": "Docker test"})
    monkeypatch.setattr(sm, "_container_running", lambda runtime, name: False)
    monkeypatch.setattr(sm, "_image_exists", lambda runtime, image: False)
    monkeypatch.setattr(sm.subprocess, "run", lambda *a, **k: type("Proc", (), {"returncode": 0, "stdout": "cid\n", "stderr": ""})())
    result = start_sandbox(cfg, profile="kali")
    assert result["ok"] is True
    assert result["state"]["network"] == "bridge"


def test_webui_exposes_less_strict_controls_and_policy_status():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "/sandbox-less-strict on" in html
    assert "/sandbox-policy balanced" in html
    assert "data.sandbox_policy_level" in html
    assert "data.trusted_lab_mode" in html
