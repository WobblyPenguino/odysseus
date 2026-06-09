from pathlib import Path

from winlocalassistant.codebase_sanity_audit import build_codebase_sanity_audit, render_codebase_sanity_audit
from winlocalassistant.pipeline_manifests import MANIFESTS, render_manifest_catalog
from winlocalassistant.repo_upgrade_assurance import build_repo_upgrade_assurance
from winlocalassistant.tool_orchestrator import build_tool_awareness_plan
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_expanded_repo_research_manifests_are_installed():
    expected = {
        "agent_observability_trace",
        "swe_issue_repair_loop",
        "agent_state_checkpoint_branch",
        "agent_control_plane",
    }
    assert expected.issubset(set(MANIFESTS))
    catalog = render_manifest_catalog("observability repair checkpoint control plane")
    assert "OpenTelemetry" in catalog
    assert "SWE-agent" in catalog
    assert "AgentGit" in catalog
    assert "Agno" in catalog


def test_codebase_sanity_audit_scans_nova_without_blockers():
    payload = build_codebase_sanity_audit(ROOT)
    assert payload["ok"] is True
    assert payload["files_scanned"] >= 100
    assert payload["tool_registry_entries_estimate"] >= 100
    assert any(item["path"].endswith("tools.py") for item in payload["largest_modules"])
    rendered = render_codebase_sanity_audit(payload)
    assert "Rewrite candidates" in rendered
    assert "ToolRegistry entries" in rendered


def test_tool_registry_exposes_repo_research_and_codebase_audit_tools():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT), allow_mutating_tools=False))
    for name in [
        "codebase_sanity_audit",
        "repo_research_radar",
        "repo_upgrade_assurance",
        "tool_awareness_audit",
        "trace_observability_plan",
        "verifier_ladder",
    ]:
        assert name in registry.tools
    result = registry.call("codebase_sanity_audit")
    assert result.ok
    assert "Codebase Sanity" in result.data["message"]


def test_repo_upgrade_assurance_includes_expanded_capability_set():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT), allow_mutating_tools=False))
    payload = build_repo_upgrade_assurance(ROOT, available_tools=registry.tools.keys())
    assert payload["ok"] is True
    for manifest in [
        "agent_observability_trace",
        "swe_issue_repair_loop",
        "agent_state_checkpoint_branch",
        "agent_control_plane",
    ]:
        assert manifest in payload["repo_ideas_installed"]


def test_autonomous_tool_plan_uses_expanded_validation_hooks():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT), allow_mutating_tools=False))
    plan = build_tool_awareness_plan(
        "autonomous repair with checkpoint, observability trace and verifier ladder",
        mode="autonomous",
        available_tools=registry.tools.keys(),
    )
    tools = {decision.tool for decision in plan.decisions}
    assert "pipeline_preflight" in tools
    assert "session_evidence" in tools
    assert "tool_awareness" in tools
    assert plan.covered_tool_count >= 5
    assert not plan.missing_tools
