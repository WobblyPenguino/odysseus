from pathlib import Path

from winlocalassistant.idle_policy import IDLE_LEVELS, idle_allows, load_idle_policy, render_idle_policy, set_idle_policy_level
from winlocalassistant.receipt_history import render_receipt_history, summarise_receipts
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.config import AssistantConfig
from winlocalassistant.feature_continuity import build_feature_continuity_audit


def test_idle_policy_levels_are_explicit_and_safe(tmp_path, monkeypatch):
    # Use the real module API but redirect path-like globals through monkeypatch where possible.
    import winlocalassistant.idle_policy as idle_policy
    monkeypatch.setattr(idle_policy, "IDLE_POLICY_PATH", tmp_path / "idle_policy.json")
    assert len(IDLE_LEVELS) == 4
    policy = set_idle_policy_level("watch", updated_by="test")
    assert policy["level"] == 0
    assert not idle_allows("propose", policy)
    assert not idle_allows("apply", policy)
    policy = set_idle_policy_level("apply-low-risk", updated_by="test")
    assert policy["level"] == 3
    assert idle_allows("propose", policy)
    assert idle_allows("prepare", policy)
    assert idle_allows("apply", policy)
    assert "Auto-apply low-risk" in render_idle_policy(policy)


def test_tool_registry_exposes_idle_policy_and_receipts(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    reg = ToolRegistry(cfg)
    assert "idle_policy" in reg.tools
    assert "receipt_history" in reg.tools
    status = reg.call("idle_policy", action="status")
    assert status.ok
    assert "Idle Behaviour Policy" in status.data.get("message", "")
    receipts = reg.call("receipt_history", limit=5)
    assert receipts.ok
    assert "Nova Receipt History" in receipts.data.get("message", "")


def test_receipt_history_renders_empty_history(monkeypatch, tmp_path):
    import winlocalassistant.receipt_history as rh
    import winlocalassistant.nova_operating_context as noc
    path = tmp_path / "receipts.jsonl"
    monkeypatch.setattr(noc, "RECEIPT_PATH", path)
    monkeypatch.setattr(rh, "RECEIPT_PATH", path)
    payload = summarise_receipts(limit=10)
    assert payload["count"] == 0
    assert "No receipts" in render_receipt_history(payload)


def test_feature_continuity_includes_new_tools():
    root = Path(__file__).resolve().parent
    cfg = AssistantConfig(workspace=str(root))
    reg = ToolRegistry(cfg)
    payload = build_feature_continuity_audit(root, tool_names=sorted(reg.tools))
    assert payload["ok"], payload.get("failed")
    names = {c["name"] for c in payload["checks"]}
    assert "tool_registry:critical_commands" in names
