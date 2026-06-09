from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.core import AssistantCore
from winlocalassistant.sandbox_manager import evaluate_sandbox_command, sandbox_status, PROFILES


def make_config(tmp_path: Path) -> AssistantConfig:
    return AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)


def test_sandbox_tools_registered(tmp_path: Path):
    tools = ToolRegistry(make_config(tmp_path))
    for name in ["sandbox_status", "sandbox_start", "sandbox_stop", "sandbox_exec", "sandbox_flag"]:
        assert name in tools.tools


def test_sandbox_status_is_safe_without_runtime(tmp_path: Path):
    cfg = make_config(tmp_path)
    payload = sandbox_status(cfg)
    assert payload["ok"] is True
    assert "runtime" in payload
    assert "linux" in payload["profiles"]
    assert "kali" in payload["profiles"]
    assert payload["policy"]["default_network"] == "none"


def test_sandbox_command_policy_blocks_host_control(tmp_path: Path):
    cfg = make_config(tmp_path)
    policy = evaluate_sandbox_command(cfg, "linux", "docker ps")
    assert policy["allowed"] is False
    assert any("host-control" in r for r in policy["reasons"])


def test_kali_high_risk_requires_authorized_lab(tmp_path: Path):
    cfg = make_config(tmp_path)
    blocked = evaluate_sandbox_command(cfg, "kali", "msfconsole -q")
    assert blocked["allowed"] is False
    cfg.sandbox_authorized_security_lab = True
    allowed = evaluate_sandbox_command(cfg, "kali", "msfconsole -q", allow_high_risk=True)
    assert allowed["allowed"] is True
    assert allowed["warnings"]


def test_core_sandbox_commands_do_not_crash(tmp_path: Path):
    core = AssistantCore(make_config(tmp_path))
    text = core.handle_command("/sandbox-status")
    assert "Sandbox" in text
    text2 = core.handle_command("/sandbox-exec linux")
    assert "Usage" in text2 or "No sandbox command" in text2


def test_autonomous_sequence_includes_sandbox_when_enabled():
    from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence
    plan = build_autonomous_tool_sequence(
        "improve efficiency safely",
        {"sandbox": {"autonomous_sandbox_mode": True, "sandboxes": {"linux": {"ok": True}}}},
    )
    tools = [step.tool for step in plan.steps]
    assert "sandbox_status" in tools
    assert "sandbox_exec" in tools
