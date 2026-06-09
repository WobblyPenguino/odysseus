from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_improvement_assurance_lab import (
    build_improvement_assurance_plan,
    build_patch_quality_score,
    build_regression_bisect_plan,
    build_success_claim_audit,
    build_test_impact_graph,
    render_improvement_assurance_plan,
    render_patch_quality_score,
    render_regression_bisect_plan,
    render_success_claim_audit,
    render_test_impact_graph,
)
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_improvement_assurance_has_evidence_and_rollback_gates():
    payload = build_improvement_assurance_plan(ROOT, "improve Nova verification", "winlocalassistant/tools.py, tests_smoke.py")
    assert payload["ok"] is True, payload.get("checks")
    gate_names = {gate["name"] for gate in payload["evidence_gates"]}
    assert {"syntax_and_imports", "targeted_regression", "claim_honesty", "rollback_boundary"}.issubset(gate_names)
    assert payload["impact_graph"]["targeted_tests"]
    assert "not an improvement until" in payload["acceptance_rule"]
    assert "Improvement Assurance" in render_improvement_assurance_plan(payload)


def test_test_impact_graph_maps_core_files_to_regression_tests():
    payload = build_test_impact_graph(ROOT, "winlocalassistant/core.py, winlocalassistant/tools.py")
    assert payload["ok"] is True, payload.get("checks")
    assert "tests_feature_continuity.py" in payload["targeted_tests"]
    assert "tests_smoke.py" in payload["targeted_tests"]
    assert any("pytest" in cmd for cmd in payload["validation_commands"])
    assert "Test Impact Graph" in render_test_impact_graph(payload)


def test_patch_quality_score_flags_high_risk_routes():
    payload = build_patch_quality_score(ROOT, "winlocalassistant/core.py, docs/example.md")
    assert payload["score"] < 100
    risks = {item["path"]: item["risk"] for item in payload["items"]}
    assert risks["winlocalassistant/core.py"] == "high"
    assert any("focused tests_nova" in rec for rec in payload["recommendations"])
    assert "Patch Quality Score" in render_patch_quality_score(payload)


def test_success_claim_audit_rejects_absolute_overclaims():
    bad = build_success_claim_audit("Everything works and there are guaranteed no regressions.")
    assert bad["ok"] is False
    assert any(check["name"] == "no_absolute_overclaim" and not check["ok"] for check in bad["checks"])
    good = build_success_claim_audit("Validation passed: py_compile, smoke and targeted pytest. Full suite timed out, so I am not claiming full-suite completion. Windows audio was not live-tested.")
    assert good["ok"] is True, good.get("checks")
    assert "Success Claim Audit" in render_success_claim_audit(good)


def test_regression_bisect_plan_selects_midpoint_and_stop_rule():
    payload = build_regression_bisect_plan("wake command stopped listening", "v55.3.127, v55.3.128, v55.3.129, v55.3.130, v55.3.131")
    assert payload["ok"] is True
    assert payload["first_probe"] == "v55.3.129"
    assert "Stop when" in payload["stop_rule"]
    assert "Regression Bisect" in render_regression_bisect_plan(payload)


def test_tool_registry_exposes_improvement_assurance_tools():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    calls = {
        "improvement_assurance_plan": {"goal": "improve Nova", "changed": "winlocalassistant/tools.py"},
        "test_impact_graph": {"changed": "winlocalassistant/core.py"},
        "patch_quality_score": {"changed": "winlocalassistant/tools.py"},
        "success_claim_audit": {"summary": "Validation passed with smoke tests; Windows audio was not live-tested."},
        "regression_bisect_plan": {"symptom": "regression", "versions": "v1,v2,v3"},
    }
    for name, kwargs in calls.items():
        result = registry.call(name, **kwargs)
        assert result.ok is True or name in {"patch_quality_score"}, (name, result.summary, result.data)
        assert "message" in result.data


def test_core_routes_improvement_assurance_commands():
    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    commands = [
        "/improvement-assurance improve Nova => winlocalassistant/tools.py",
        "/test-impact-graph winlocalassistant/core.py, winlocalassistant/tools.py",
        "/patch-quality-score winlocalassistant/core.py",
        "/success-claim-audit Validation passed with smoke tests; Windows audio was not live-tested.",
        "/regression-bisect-plan wake bug => v55.3.128, v55.3.129, v55.3.130",
    ]
    for command in commands:
        text = core.handle_command(command)
        assert "Unknown command" not in text
        assert "Nova" in text or "Graph" in text or "Score" in text or "Audit" in text or "Bisect" in text


def run_all(verbose: bool = False):
    tests = [
        test_improvement_assurance_has_evidence_and_rollback_gates,
        test_test_impact_graph_maps_core_files_to_regression_tests,
        test_patch_quality_score_flags_high_risk_routes,
        test_success_claim_audit_rejects_absolute_overclaims,
        test_regression_bisect_plan_selects_midpoint_and_stop_rule,
        test_tool_registry_exposes_improvement_assurance_tools,
        test_core_routes_improvement_assurance_commands,
    ]
    for test in tests:
        test()
        if verbose:
            print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all(verbose=True)
