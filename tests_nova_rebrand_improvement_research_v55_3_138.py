from pathlib import Path

from winlocalassistant.branding import canonical_command, scan_legacy_branding
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_improvement_research import build_nova_improvement_research, render_nova_improvement_research


def test_nova_brand_audit_has_no_visible_legacy_markers() -> None:
    payload = scan_legacy_branding(Path.cwd())
    assert payload["ok"] is True
    assert payload["legacy_mentions"] == 0


def test_legacy_command_aliases_preserve_old_workflows() -> None:
    assert canonical_command("/wla-mega-test") == "/nova-mega-test"
    assert canonical_command("/wla-doctor") == "/nova-doctor"
    assert canonical_command("/search-wla-docs") == "/search-nova-docs"


def test_nova_rebrand_commands_are_routed() -> None:
    core = AssistantCore(AssistantConfig())
    assert "Nova Brand Audit" in core.handle_command("/nova-brand-audit")
    assert "Nova Improvement Research Plan" in core.handle_command("/nova-improvement-research guardrails")
    assert "Nova Mega Test" in core.handle_command("/wla-mega-test")


def test_improvement_research_ranks_safe_functionality_candidates() -> None:
    payload = build_nova_improvement_research(Path.cwd(), focus="guardrails")
    rendered = render_nova_improvement_research(payload)
    assert payload["ok"] is True
    assert payload["recommendations"]
    assert "Guarded tool execution" in rendered
    assert "Validate with" in rendered
