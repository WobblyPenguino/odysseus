from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.sandbox_manager import sandbox_status, render_status_markdown
from winlocalassistant.sandbox_permissions import (
    create_pending_sandbox_permission,
    clear_pending_sandbox_permission,
    load_pending_sandbox_permission,
    sandbox_command_targets_network,
)
from winlocalassistant.tools import ToolResult


def test_blocked_kali_target_command_creates_visible_pending_permission(tmp_path, monkeypatch):
    import winlocalassistant.sandbox_permissions as sp
    import winlocalassistant.core as core_mod
    monkeypatch.setattr(sp, "PENDING_SANDBOX_PERMISSION_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(core_mod, "load_pending_sandbox_permission", sp.load_pending_sandbox_permission)
    monkeypatch.setattr(core_mod, "create_pending_sandbox_permission", sp.create_pending_sandbox_permission)
    monkeypatch.setattr(core_mod, "render_pending_sandbox_permission_markdown", sp.render_pending_sandbox_permission_markdown)
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)

    reply = core.sandbox_command("kali", "exec nikto -h http://example.com")

    assert "Sandbox permission needed" in reply
    assert "Authorised Kali lab mode" in reply
    assert "Sandbox network access" in reply
    assert "sandbox-approve" in reply
    pending = load_pending_sandbox_permission()
    assert pending["command"] == "nikto -h http://example.com"
    assert set(pending["required"]) == {"authorized_lab", "network"}


def test_sandbox_status_surfaces_pending_permission(tmp_path, monkeypatch):
    import winlocalassistant.sandbox_permissions as sp
    import winlocalassistant.sandbox_manager as sm
    monkeypatch.setattr(sp, "PENDING_SANDBOX_PERMISSION_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(sm, "load_pending_sandbox_permission", sp.load_pending_sandbox_permission)
    monkeypatch.setattr(sm, "render_pending_sandbox_permission_markdown", sp.render_pending_sandbox_permission_markdown)
    cfg = AssistantConfig(workspace=str(tmp_path))
    create_pending_sandbox_permission("kali", "nikto -h http://example.com", ["authorized_lab", "network"], {"reasons": ["blocked"]})

    status = sandbox_status(cfg)
    rendered = render_status_markdown(status)

    assert status["pending_permission"]["command"] == "nikto -h http://example.com"
    assert "Pending sandbox permission" in rendered
    assert "sandbox-approve" in rendered


def test_approve_permission_enables_flags_restarts_network_and_runs(tmp_path, monkeypatch):
    import winlocalassistant.sandbox_permissions as sp
    import winlocalassistant.core as core_mod
    monkeypatch.setattr(sp, "PENDING_SANDBOX_PERMISSION_PATH", tmp_path / "pending.json")
    monkeypatch.setattr(core_mod, "load_pending_sandbox_permission", sp.load_pending_sandbox_permission)
    monkeypatch.setattr(core_mod, "clear_pending_sandbox_permission", sp.clear_pending_sandbox_permission)
    monkeypatch.setattr(core_mod, "create_pending_sandbox_permission", sp.create_pending_sandbox_permission)
    monkeypatch.setattr(core_mod, "render_pending_sandbox_permission_markdown", sp.render_pending_sandbox_permission_markdown)
    cfg = AssistantConfig(workspace=str(tmp_path))
    core = AssistantCore(cfg)
    core.sandbox_command("kali", "exec nikto -h http://example.com")
    calls = []

    def fake_call(name, **kwargs):
        calls.append((name, kwargs))
        if name == "sandbox_exec":
            return ToolResult(True, "Sandbox command completed", {"message": "ran pending command"})
        return ToolResult(True, "ok", {"message": "ok"})

    monkeypatch.setattr(core.tools, "call", fake_call)
    reply = core.approve_sandbox_permission("yes")

    assert "Permission approved" in reply
    assert "ran pending command" in reply
    assert ("sandbox_flag", {"flag": "authorized_lab", "enabled": True}) in calls
    assert ("sandbox_flag", {"flag": "network", "enabled": True}) in calls
    assert any(name == "sandbox_start" and kwargs.get("network") == "bridge" for name, kwargs in calls)
    assert any(name == "sandbox_exec" and kwargs.get("allow_high_risk") and kwargs.get("allow_network_tools") for name, kwargs in calls)
    assert load_pending_sandbox_permission() == {}


def test_network_target_detection_distinguishes_local_and_public_targets():
    assert sandbox_command_targets_network("nikto -h http://example.com")
    assert sandbox_command_targets_network("nmap scanme.nmap.org")
    assert sandbox_command_targets_network("curl https://example.com")
    assert not sandbox_command_targets_network("nmap 127.0.0.1")
    assert not sandbox_command_targets_network("nmap 192.168.1.20")


def test_webui_has_pending_permission_controls():
    html = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "pending_permission" in html
    assert "/sandbox-approve yes" in html
    assert "/sandbox-cancel" in html
    assert "Pending permission" in html
