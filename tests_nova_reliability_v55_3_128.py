from pathlib import Path

from winlocalassistant.nova_reliability_lab import (
    build_local_model_benchmark_plan,
    build_patch_impact_plan,
    build_permission_scope_review,
    build_repo_context_map,
    build_tool_contract_audit,
    render_local_model_benchmark_plan,
    render_patch_impact_plan,
    render_permission_scope_review,
    render_repo_context_map,
    render_tool_contract_audit,
)
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_repo_context_map_is_bounded_and_relevant():
    payload = build_repo_context_map(ROOT, "improve Nova coding tools and local model performance")
    assert payload["ok"] is True
    assert payload["selected_files"]
    paths = {item["path"] for item in payload["selected_files"]}
    assert "README.md" in paths or "AGENTS.md" in paths
    assert any(path.endswith(("core.py", "tools.py")) or "nova_" in path for path in paths)
    assert all("secret" not in item["path"].lower() for item in payload["selected_files"])
    assert "Nova Repo Context Map" in render_repo_context_map(payload)


def test_patch_impact_plan_selects_targeted_regression_tests():
    payload = build_patch_impact_plan(ROOT, "winlocalassistant/core.py, winlocalassistant/tools.py, winlocalassistant/webui.py")
    assert payload["ok"] is True
    tests = set(payload["recommended_tests"])
    assert "tests_smoke.py" in tests
    assert "tests_feature_continuity.py" in tests
    assert "tests_webui_planning_visibility.py" in tests
    assert any("py_compile" in cmd for cmd in payload["recommended_commands"])
    assert "Nova Patch Impact Test Plan" in render_patch_impact_plan(payload)


def test_permission_scope_review_flags_broad_destructive_scope():
    payload = build_permission_scope_review("clean entire codebase", "delete all old files and install dependencies")
    assert payload["risk_level"] == "high"
    assert payload["ok_to_auto_apply"] is False
    assert payload["findings"]
    assert "manual review" in payload["recommended_gate"]
    assert "Permission" in render_permission_scope_review(payload)


def test_permission_scope_review_allows_low_risk_readonly_work():
    payload = build_permission_scope_review("summarise repo context", "read README and tests")
    assert payload["risk_level"] == "low"
    assert payload["ok_to_auto_apply"] is True


def test_local_model_benchmark_plan_adapts_to_small_vram():
    payload = build_local_model_benchmark_plan("debug Python code", "GTX 1650 4GB VRAM")
    assert payload["task"] == "coding/debugging"
    assert payload["profiles"][0]["num_ctx"] <= 4096
    assert any("ollama ps" in cmd for cmd in payload["manual_commands"])
    assert "Local Model Benchmark" in render_local_model_benchmark_plan(payload)


def test_tool_contract_audit_passes_after_wiring():
    payload = build_tool_contract_audit(ROOT)
    assert payload["ok"] is True, payload
    assert payload["registered_tool_count"] > 50
    assert not payload["missing_methods"]
    assert not payload["unregistered_tool_calls"]
    assert "Tool Contract Audit" in render_tool_contract_audit(payload)


def test_tool_registry_exposes_reliability_commands():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    for name in [
        "repo_context_map",
        "patch_impact_plan",
        "permission_scope_review",
        "local_model_benchmark_plan",
        "tool_contract_audit",
    ]:
        result = registry.call(name, goal="improve Nova") if name == "repo_context_map" else registry.call(name)
        assert result.ok is True, (name, result.summary, result.data)
        assert "message" in result.data


def run_all(verbose: bool = False):
    tests = [
        test_repo_context_map_is_bounded_and_relevant,
        test_patch_impact_plan_selects_targeted_regression_tests,
        test_permission_scope_review_flags_broad_destructive_scope,
        test_permission_scope_review_allows_low_risk_readonly_work,
        test_local_model_benchmark_plan_adapts_to_small_vram,
        test_tool_contract_audit_passes_after_wiring,
        test_tool_registry_exposes_reliability_commands,
    ]
    for test in tests:
        test()
        if verbose:
            print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all(verbose=True)
