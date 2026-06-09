from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_capability_drift_lab import (
    build_agent_feedback_loop_plan,
    build_behavior_fuzzer_plan,
    build_capability_drift_audit,
    build_feature_preservation_contract,
    build_local_spec_search_plan,
    render_agent_feedback_loop_plan,
    render_behavior_fuzzer_plan,
    render_capability_drift_audit,
    render_feature_preservation_contract,
    render_local_spec_search_plan,
)
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_capability_drift_audit_preserves_recent_feature_families():
    payload = build_capability_drift_audit(ROOT)
    assert payload["ok"] is True, payload
    names = {item["name"] for item in payload["families"]}
    assert {"voice_and_wake_handoff", "multi_runtime_coding", "improvement_assurance"}.issubset(names)
    assert "tests_nova_improvement_assurance_v55_3_131.py" in payload["latest_nova_tests"]
    assert "Capability Drift" in render_capability_drift_audit(payload)


def test_feature_preservation_contract_has_hard_rules_and_tests():
    payload = build_feature_preservation_contract(ROOT, "coding local model")
    assert payload["ok"] is True
    assert any("Do not remove" in rule for rule in payload["hard_rules"])
    assert "tests_smoke.py" in payload["test_floor"]
    assert "Feature Preservation" in render_feature_preservation_contract(payload)


def test_agent_feedback_loop_has_five_optimisable_primitives():
    payload = build_agent_feedback_loop_plan("make Nova improve from user outcomes")
    primitive_names = {item["name"] for item in payload["primitives"]}
    assert {"Intelligence", "Engine", "Agents", "Tools & Memory", "Learning"}.issubset(primitive_names)
    assert "non-regressing" in payload["acceptance_rule"]
    assert "Agent Feedback Loop" in render_agent_feedback_loop_plan(payload)


def test_behavior_fuzzer_plan_targets_known_nova_failure_patterns():
    payload = build_behavior_fuzzer_plan("fuzz Nova coding", "coding and routing")
    patterns = {item["pattern"] for item in payload["patterns"]}
    assert "wrong-runtime coding" in patterns
    assert "overclaim validation" in patterns
    assert payload["safe_start"].startswith("Generate advisory")
    assert "Behaviour Fuzzer" in render_behavior_fuzzer_plan(payload)


def test_local_spec_search_adapts_to_small_gpu_hint():
    payload = build_local_spec_search_plan("coding reliability", "GTX 1650 4GB VRAM")
    assert "4k-8k" in payload["context_target"]
    assert "num_ctx" in payload["spec_fields"]
    assert any("compact context" in spec for spec in payload["starting_specs"])
    assert "Local Spec Search" in render_local_spec_search_plan(payload)


def test_tool_registry_exposes_capability_drift_tools():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    calls = {
        "capability_drift_audit": {},
        "feature_preservation_contract": {"focus": "coding"},
        "agent_feedback_loop_plan": {"goal": "improve Nova"},
        "behavior_fuzzer_plan": {"goal": "fuzz", "surface": "routing"},
        "local_spec_search_plan": {"goal": "local model", "hardware": "4GB VRAM"},
    }
    for name, kwargs in calls.items():
        result = registry.call(name, **kwargs)
        assert result.ok is True, (name, result.summary, result.data)
        assert "message" in result.data


def test_core_routes_capability_drift_commands():
    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    commands = [
        "/capability-drift-audit",
        "/feature-preservation-contract coding",
        "/agent-feedback-loop improve Nova",
        "/behavior-fuzzer-plan fuzz coding => routing",
        "/local-spec-search coding => GTX 1650 4GB VRAM",
    ]
    for command in commands:
        text = core.handle_command(command)
        assert "Unknown command" not in text
        assert "Nova" in text or "Feature" in text or "Fuzzer" in text or "Spec" in text


def run_all(verbose: bool = False):
    tests = [
        test_capability_drift_audit_preserves_recent_feature_families,
        test_feature_preservation_contract_has_hard_rules_and_tests,
        test_agent_feedback_loop_has_five_optimisable_primitives,
        test_behavior_fuzzer_plan_targets_known_nova_failure_patterns,
        test_local_spec_search_adapts_to_small_gpu_hint,
        test_tool_registry_exposes_capability_drift_tools,
        test_core_routes_capability_drift_commands,
    ]
    for test in tests:
        test()
        if verbose:
            print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all(verbose=True)
