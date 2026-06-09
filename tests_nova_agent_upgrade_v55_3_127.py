from __future__ import annotations

from pathlib import Path

from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_agent_upgrade_lab import (
    build_agent_upgrade_radar,
    build_coding_behavior_tests,
    build_context_budget_plan,
    build_ollama_runtime_profile,
    build_upgrade_regression_audit,
)
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.config import AssistantConfig

ROOT = Path(__file__).resolve().parent


def test_agent_upgrade_radar_is_additive_and_verifiable() -> None:
    payload = build_agent_upgrade_radar(ROOT, focus="improve Nova coding and local model performance")
    names = {item["name"] for item in payload["ideas"]}
    assert payload["ok"] is True
    assert "Context compaction before model calls" in names
    assert "Behavior-driven coding checks" in names
    assert "Patch continuity audit" in names
    assert "/upgrade-regression-audit" in payload["recommended_sequence"]


def test_context_budget_selects_relevant_files_without_dumping_repo() -> None:
    payload = build_context_budget_plan(ROOT, goal="improve Nova coding planner local model context", max_files=8)
    selected = payload["selected_files"]
    paths = {item["path"] for item in selected}
    assert 1 <= len(selected) <= 8
    assert any("nova_coding_capabilities.py" in path or "tools.py" in path for path in paths)
    assert payload["estimated_total_tokens"] > 0
    assert payload["excluded_candidate_count"] >= 0
    assert all(".env" not in item["path"].lower() for item in selected)


def test_coding_behavior_tests_are_request_specific() -> None:
    calc = build_coding_behavior_tests("make a Python calculator CLI")
    behaviour_names = {item["name"] for item in calc["behaviours"]}
    assert calc["plan"]["language"] == "Python"
    assert "calculator_behaviour" in behaviour_names
    assert any("py_compile" in item["check"] or "run `" in item["check"] for item in calc["behaviours"])

    game = build_coding_behavior_tests("make a browser snake game")
    game_names = {item["name"] for item in game["behaviours"]}
    assert "game_behaviour" in game_names


def test_ollama_runtime_profile_returns_read_only_modelfile_and_benchmark_plan() -> None:
    payload = build_ollama_runtime_profile("fix Python code", hardware_hint="GTX 1650 4GB VRAM")
    text = payload["modelfile"]
    assert text.startswith("FROM ")
    assert "PARAMETER num_ctx" in text
    assert "PARAMETER temperature" in text
    assert payload["benchmark_checklist"]
    assert payload["fallback_policy"]


def test_upgrade_regression_audit_tracks_recent_patch_families() -> None:
    payload = build_upgrade_regression_audit(ROOT)
    names = {check["name"] for check in payload["checks"]}
    assert payload["ok"] is True
    assert "v55_3_124_analytics_module" in names
    assert "v55_3_125_inspiration_module" in names
    assert "v55_3_126_coding_module" in names
    assert "v55_3_127_upgrade_lab_module" in names


def test_registry_and_core_route_new_upgrade_commands() -> None:
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    for name in [
        "agent_upgrade_radar",
        "context_budget",
        "coding_behavior_tests",
        "ollama_runtime_profile",
        "upgrade_regression_audit",
    ]:
        assert name in registry.tools
        result = registry.call(name, goal="make a Python calculator CLI") if name not in {"agent_upgrade_radar", "upgrade_regression_audit"} else registry.call(name)
        assert result.ok is True
        assert result.data.get("message")

    core = AssistantCore.load()
    assert "Nova Agent Upgrade Radar" in core.chat("/agent-upgrade-radar coding")
    assert "Nova Context Budget Plan" in core.chat("/context-budget improve coding")
    assert "Nova Coding Behaviour Test Plan" in core.chat("/coding-behavior-tests make a calculator")
    assert "Nova Ollama Runtime Profile" in core.chat("/ollama-runtime-profile fix code => GTX 1650 4GB VRAM")
    assert "Nova Upgrade Regression Audit" in core.chat("/upgrade-regression-audit")


def run_all(verbose: bool = False) -> None:
    tests = [
        test_agent_upgrade_radar_is_additive_and_verifiable,
        test_context_budget_selects_relevant_files_without_dumping_repo,
        test_coding_behavior_tests_are_request_specific,
        test_ollama_runtime_profile_returns_read_only_modelfile_and_benchmark_plan,
        test_upgrade_regression_audit_tracks_recent_patch_families,
        test_registry_and_core_route_new_upgrade_commands,
    ]
    for test in tests:
        test()
        if verbose:
            print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all(verbose=True)
