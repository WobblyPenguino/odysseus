from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_route_resilience_lab import (
    build_context_router_policy,
    build_guardrail_memory_plan,
    build_local_runtime_sentinel,
    build_route_resilience_plan,
    build_tool_health_map,
    render_context_router_policy,
    render_guardrail_memory_plan,
    render_local_runtime_sentinel,
    render_route_resilience_plan,
    render_tool_health_map,
)
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_route_resilience_plan_has_fallbacks_and_verifier():
    payload = build_route_resilience_plan(ROOT, "improve Nova coding without regressions")
    assert payload["ok"] is True
    names = [node["name"] for node in payload["nodes"]]
    assert "context_router" in names
    assert "verifier" in names
    assert payload["edges"]
    assert any(edge["kind"] == "fallback" for edge in payload["edges"])
    assert "silently" in payload["recovery_rule"]
    assert "Route Resilience" in render_route_resilience_plan(payload)


def test_tool_health_map_detects_new_and_legacy_surfaces():
    payload = build_tool_health_map(ROOT, "Nova route health")
    assert payload["ok"] is True, payload.get("checks")
    assert payload["registered_tool_count"] >= 60
    surfaces = {item["surface"]: item for item in payload["critical_surfaces"]}
    assert surfaces["route_resilience_plan"]["tool_registered"] is True
    assert surfaces["route_resilience_plan"]["core_routed"] is True
    assert surfaces["deep_research_lab"]["tool_registered"] is True
    assert "Tool Health" in render_tool_health_map(payload)


def test_guardrail_memory_preserves_benign_utility():
    payload = build_guardrail_memory_plan("change Nova safely", "avoid breaking voice or shell flows")
    assert payload["ok"] is True
    assert any(rule["name"] == "destructive_action_gate" for rule in payload["rules"])
    assert all(rule["preserves_utility_by"] for rule in payload["rules"])
    assert "Inject only" in payload["injection_policy"]
    assert "Guardrail Memory" in render_guardrail_memory_plan(payload)


def test_context_router_policy_is_role_aware_and_bounded():
    payload = build_context_router_policy(ROOT, "improve Nova local coding agent")
    assert payload["ok"] is True, payload.get("checks")
    roles = {route["role"] for route in payload["routes"]}
    assert {"triage", "builder", "verifier", "reporter"}.issubset(roles)
    assert payload["total_role_budget"] <= 14000
    assert payload["selected_files"]
    assert "Context Router" in render_context_router_policy(payload)


def test_local_runtime_sentinel_small_gpu_keeps_context_low():
    payload = build_local_runtime_sentinel("debug Python code", "GTX 1650 4GB VRAM")
    assert payload["ok"] is True
    assert payload["hardware_tier"] == "small_gpu_or_cpu_spill_risk"
    assert payload["recommended_num_ctx"] <= 4096
    assert any("ollama ps" in check["command_or_signal"] for check in payload["sentinel_checks"])
    assert any("PARAMETER num_ctx" in note for note in payload["modelfile_notes"])
    assert "Local Runtime Sentinel" in render_local_runtime_sentinel(payload)


def test_tool_registry_exposes_route_resilience_tools():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    calls = {
        "route_resilience_plan": {"goal": "improve Nova"},
        "tool_health_map": {"focus": "routes"},
        "guardrail_memory_plan": {"goal": "patch Nova", "risk_note": "avoid regression"},
        "context_router_policy": {"goal": "local coding"},
        "local_runtime_sentinel": {"goal": "debug code", "hardware": "4GB VRAM"},
    }
    for name, kwargs in calls.items():
        result = registry.call(name, **kwargs)
        assert result.ok is True, (name, result.summary, result.data)
        assert "message" in result.data


def test_core_routes_route_resilience_commands():
    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    commands = [
        "/route-resilience-plan improve Nova safely",
        "/tool-health-map Nova route health",
        "/guardrail-memory improve Nova => avoid regressions",
        "/context-router-policy improve coding reliability",
        "/local-runtime-sentinel debug code => GTX 1650 4GB VRAM",
    ]
    for command in commands:
        text = core.handle_command(command)
        assert "Unknown command" not in text
        assert "Nova" in text or "Status" in text or "Runtime" in text


def run_all(verbose: bool = False):
    tests = [
        test_route_resilience_plan_has_fallbacks_and_verifier,
        test_tool_health_map_detects_new_and_legacy_surfaces,
        test_guardrail_memory_preserves_benign_utility,
        test_context_router_policy_is_role_aware_and_bounded,
        test_local_runtime_sentinel_small_gpu_keeps_context_low,
        test_tool_registry_exposes_route_resilience_tools,
        test_core_routes_route_resilience_commands,
    ]
    for test in tests:
        test()
        if verbose:
            print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all(verbose=True)
