from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.jarvis_bridge import (
    build_capability_map,
    probe_jarvis_daemon,
    queue_proactive_action,
    update_bridge_policy,
)
from winlocalassistant.nova_operating_context import build_nova_operating_context
from winlocalassistant.feature_continuity import build_feature_continuity_audit


def test_jarvis_bridge_capability_map_is_safe_by_default():
    payload = build_capability_map()
    assert payload["ok"] if "ok" in payload else True
    names = {c["name"] for c in payload["capabilities"]}
    assert {"persistent_daemon", "sidecars", "screen_awareness", "file_access", "shell_access", "browser_control", "proactive_actions"} <= names
    policy = payload["policy"]
    assert policy["sidecar_level"] == "off"
    assert policy["allow_shell_execution"] is False
    assert policy["allow_browser_control"] is False


def test_jarvis_status_blocks_remote_by_default():
    result = probe_jarvis_daemon("http://example.com:3142")
    assert result["ok"] is False
    assert result.get("blocked") is True
    assert "Remote" in result["summary"]


def test_tool_registry_exposes_jarvis_bridge_tools():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    for name in ["jarvis_bridge", "jarvis_status", "sidecar_policy", "proactive_actions"]:
        assert name in registry.tools
    res = registry.call("jarvis_bridge")
    assert res.ok
    assert "persistent_daemon" in res.data["message"]
    assert "sidecar" in res.data["message"].lower()


def test_sidecar_policy_and_proactive_queue_are_gated(tmp_path, monkeypatch):
    # Use the real policy functions but keep dangerous capabilities disabled.
    update_bridge_policy(sidecar_level="off", proactive_level="queue_for_review", allow_shell=False, allow_browser=False, allow_file_write=False)
    record = queue_proactive_action(capability="shell", action="run diagnostics", reason="test", risk="high")
    assert record["status"] == "blocked"
    assert any("shell" in item for item in record["blockers"])


def test_nova_context_includes_external_daemon_context_for_jarvis_goals():
    ctx = build_nova_operating_context(Path.cwd(), goal="integrate jarvis sidecar screen awareness safely")
    assert ctx.get("external_daemon_context")
    assert "capabilities" in ctx["external_daemon_context"]
    assert any(c["name"] == "sidecars" for c in ctx["external_daemon_context"]["capabilities"])


def test_feature_continuity_knows_jarvis_bridge_markers():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    payload = build_feature_continuity_audit(Path.cwd(), tool_names=sorted(registry.tools))
    assert payload["ok"], payload.get("failed")
    names = [check["name"] for check in payload["checks"]]
    assert "webui:jarvis_bridge" in names
