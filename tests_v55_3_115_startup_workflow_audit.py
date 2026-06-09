from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.startup_validation import build_startup_validation, render_startup_validation
from winlocalassistant.jarvis_bridge import build_audit_log, build_workflow_execution, render_bridge_markdown


def test_startup_validation_compile_mode_passes_for_repo_root():
    payload = build_startup_validation(Path.cwd(), mode="compile", timeout=60)
    assert payload["ok"] is True
    assert any(check["name"] == "compileall" for check in payload["checks"])
    rendered = render_startup_validation(payload)
    assert "Nova Startup Validation" in rendered
    assert "compileall" in rendered


def test_registry_exposes_startup_audit_and_workflow_tools():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    for name in ["startup_validation", "audit_log", "workflow_run"]:
        assert name in registry.tools


def test_audit_log_aggregates_receipts_without_crashing():
    payload = build_audit_log(limit=5)
    assert payload["ok"] is True
    assert "audit_entries" in payload
    rendered = render_bridge_markdown(payload)
    assert "Audit log" in rendered


def test_workflow_execution_preview_queues_authority_receipt_only():
    payload = build_workflow_execution("validate Nova safely", confirm=False)
    assert payload["ok"] is True
    assert payload["outcome"] == "preview"
    assert any(step["id"] == "authority" for step in payload["steps"])
    rendered = render_bridge_markdown(payload)
    assert "Workflow execution" in rendered
    assert "Preview only" in rendered


def test_feature_continuity_knows_startup_audit_workflow_markers():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    result = registry.call("feature_continuity_audit", path=".")
    assert result.ok
    text = result.data.get("message", "")
    assert "startup_validation_and_audit" in text


def test_startup_bat_runs_validation_gate_before_ui():
    text = Path("start_windows_assistant.bat").read_text(encoding="utf-8")
    assert "winlocalassistant.startup_validation" in text
    assert "NOVA_SKIP_STARTUP_TESTS" in text
    assert "Continue anyway for debugging" in text
