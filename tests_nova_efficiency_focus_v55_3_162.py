from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_efficiency_audit import build_nova_efficiency_audit, render_nova_efficiency_audit

ROOT = Path(__file__).resolve().parent


def test_efficiency_audit_builds_research_backed_payload():
    payload = build_nova_efficiency_audit(ROOT)
    assert "research_signals" in payload
    assert any("Ollama" in item["source"] for item in payload["research_signals"])
    text = render_nova_efficiency_audit(payload)
    assert "Nova Efficiency and UX Audit" in text
    assert "Validation ladder" in text


def test_efficiency_audit_command_writes_docs(tmp_path):
    # Use the real root because the audit checks Nova files.
    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    out = core.handle_command("/nova-efficiency-audit")
    assert "Nova Efficiency and UX Audit" in out
    assert (ROOT / "docs" / "NOVA_EFFICIENCY_AUDIT_LATEST.md").exists()
    assert (ROOT / "docs" / "NOVA_EFFICIENCY_AUDIT_LATEST.json").exists()


def test_focus_gui_markers_and_version_present():
    webui = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    assert "focus-workspace" in webui
    assert "toggleFocusWorkspace" in webui
    assert "Nova v55.3.164" in webui
    assert "/nova-efficiency-audit" in webui
    assert "novaEfficiencyAudit" in webui


def test_release_version_synced():
    import winlocalassistant
    assert winlocalassistant.__version__
    assert f"v{winlocalassistant.__version__}" in winlocalassistant.VERSION_LABEL
