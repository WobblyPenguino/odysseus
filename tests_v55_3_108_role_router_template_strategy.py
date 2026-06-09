from pathlib import Path

from winlocalassistant.role_router import build_role_route, render_role_route
from winlocalassistant.nova_operating_context import build_nova_operating_context
from winlocalassistant.development_governor import build_strategy_decision
from winlocalassistant.feature_continuity import build_feature_continuity_audit
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.config import AssistantConfig

ROOT = Path(__file__).resolve().parent


def test_role_router_selects_repairer_for_failures():
    route = build_role_route("fix the game generation bug", last_failure="game_missing_collision")
    assert route["primary_role"] == "Repairer"
    assert "latest_failure" in route["context_sections"]
    assert any("targeted" in item or "validation" in item for item in route["validation_focus"])
    assert "Repairer" in render_role_route(route)


def test_role_router_selects_builder_for_project_creation():
    route = build_role_route("make a new game about hair")
    assert route["primary_role"] == "Builder"
    assert "project_type" in route["context_sections"]
    assert "manual_test_steps" in route["output_contract"]


def test_nova_context_contains_role_route():
    ctx = build_nova_operating_context(ROOT, goal="make a game about hair", last_failure="game_missing_collision")
    assert ctx["role_route"]["primary_role"] in {"Builder", "Repairer"}
    assert "role_route" in ctx
    assert any("Route local-model" in rule for rule in ctx["strategy_rules"])


def test_repeated_failure_uses_template_or_recipe_strategy():
    decision = build_strategy_decision(
        "make a game about hair",
        last_failure="candidate_refine_no_progress game_missing_collision",
        attempts=[{"reason": "game_missing_collision"}, {"reason": "game_missing_collision"}],
    )
    assert decision["route"] == "template_or_recipe_fallback"
    assert decision["recommended_template"] == "html_css_js_game"
    assert any("deterministic template" in action for action in decision["next_actions"])


def test_tool_registry_exposes_role_router():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    result = registry.call("role_router", goal="validate Nova after patch")
    assert result.ok
    assert "Verifier" in result.data.get("message", "")


def test_feature_continuity_includes_role_router():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    payload = build_feature_continuity_audit(ROOT, tool_names=sorted(registry.tools.keys()))
    assert payload["ok"], payload.get("failed")
    names = [check["name"] for check in payload["checks"]]
    assert "webui:role_router" in names
