from __future__ import annotations

from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.nova_deep_research_lab import (
    build_agent_topology_plan,
    build_local_stack_advisor,
    build_tool_namespace_plan,
    build_trace_observability_plan,
    build_verifier_ladder,
    build_voice_pipeline_review,
    render_agent_topology_plan,
    render_local_stack_advisor,
    render_tool_namespace_plan,
    render_trace_observability_plan,
    render_verifier_ladder,
    render_voice_pipeline_review,
)
from winlocalassistant.tools import ToolRegistry

ROOT = Path(__file__).resolve().parent


def test_agent_topology_plan_has_router_builder_verifier():
    payload = build_agent_topology_plan(ROOT, "implement Nova feature without regression")
    assert payload["ok"] is True
    names = [stage["name"] for stage in payload["stages"]]
    assert "triage_router" in names
    assert "builder" in names
    assert "verifier" in names
    assert len(names) <= 8
    assert "verifier" in render_agent_topology_plan(payload).lower()


def test_trace_observability_plan_has_verifier_and_redaction():
    payload = build_trace_observability_plan(ROOT, "debug coding agent workflow")
    assert payload["ok"] is True
    spans = payload["spans"]
    assert any(span["name"] == "verification.run" for span in spans)
    assert all(span["redactions"] for span in spans)
    assert any("num_ctx" in span["captures"] for span in spans)
    assert "Trace" in render_trace_observability_plan(payload)


def test_local_stack_advisor_prefers_small_models_for_small_vram():
    payload = build_local_stack_advisor("debug Python code", "GTX 1650 4GB VRAM")
    assert payload["ok"] is True
    assert payload["hardware_tier"] == "small_gpu"
    assert payload["recommended_options"]["num_ctx"] <= 4096
    assert any("qwen3:4b" in model for model in payload["recommended_models"])
    assert any("ollama ps" in cmd for cmd in payload["benchmark_commands"])
    assert "Local Stack" in render_local_stack_advisor(payload)


def test_verifier_ladder_is_runtime_specific():
    py_payload = build_verifier_ladder("build a Python CLI", "python")
    java_payload = build_verifier_ladder("build a Java CLI", "java")
    ps_payload = build_verifier_ladder("write a PowerShell helper", "ps1")
    assert py_payload["runtime"] == "python"
    assert java_payload["runtime"] == "java"
    assert ps_payload["runtime"] == "powershell"
    assert any("py_compile" in step["command"] for step in py_payload["steps"])
    assert any("javac" in step["command"] for step in java_payload["steps"])
    assert any("PSParser" in step["command"] for step in ps_payload["steps"])
    assert "Verifier Ladder" in render_verifier_ladder(py_payload)


def test_tool_namespace_plan_groups_large_tool_surface():
    payload = build_tool_namespace_plan(ROOT, "reduce tool schema bloat for local models")
    assert payload["ok"] is True
    names = {ns["name"] for ns in payload["namespaces"]}
    assert {"repo", "coding", "models", "voice", "release"}.issubset(names)
    assert payload["registered_tool_name_estimate"] >= 40
    assert "Tool Namespace" in render_tool_namespace_plan(payload)


def test_voice_pipeline_review_detects_voice_files_and_stays_read_only():
    payload = build_voice_pipeline_review(ROOT, "Hey Nova wake pipeline")
    assert payload["ok"] is True
    assert payload["voice_files"]
    assert "wake_word" in payload["pipeline_stages"]
    assert "stt" in payload["pipeline_stages"]
    assert "tts" in payload["pipeline_stages"]
    assert "review_is_read_only" in str(payload["checks"])
    assert "Voice Pipeline" in render_voice_pipeline_review(payload)


def test_tool_registry_exposes_deep_research_tools():
    registry = ToolRegistry(AssistantConfig(workspace=str(ROOT)))
    calls = {
        "agent_topology_plan": {"goal": "improve Nova"},
        "trace_observability_plan": {"goal": "observe Nova"},
        "local_stack_advisor": {"goal": "debug code", "hardware": "4GB VRAM"},
        "verifier_ladder": {"goal": "build Python CLI", "runtime_hint": "python"},
        "tool_namespace_plan": {"goal": "reduce tool surface"},
        "voice_pipeline_review": {"focus": "voice reliability"},
    }
    for name, kwargs in calls.items():
        result = registry.call(name, **kwargs)
        assert result.ok is True, (name, result.summary, result.data)
        assert "message" in result.data


def test_core_routes_new_deep_research_commands():
    core = AssistantCore(AssistantConfig(workspace=str(ROOT)))
    commands = [
        "/agent-topology improve Nova safely",
        "/trace-observability improve Nova",
        "/local-stack-advisor debug Python => GTX 1650 4GB VRAM",
        "/verifier-ladder build Java CLI => java",
        "/tool-namespace-plan reduce tool bloat",
        "/voice-pipeline-review Hey Nova wake pipeline",
    ]
    for command in commands:
        text = core.handle_command(command)
        assert "Unknown command" not in text
        assert "Nova" in text or "Status" in text


def run_all(verbose: bool = False):
    tests = [
        test_agent_topology_plan_has_router_builder_verifier,
        test_trace_observability_plan_has_verifier_and_redaction,
        test_local_stack_advisor_prefers_small_models_for_small_vram,
        test_verifier_ladder_is_runtime_specific,
        test_tool_namespace_plan_groups_large_tool_surface,
        test_voice_pipeline_review_detects_voice_files_and_stays_read_only,
        test_tool_registry_exposes_deep_research_tools,
        test_core_routes_new_deep_research_commands,
    ]
    for test in tests:
        test()
        if verbose:
            print(f"PASS {test.__name__}")


if __name__ == "__main__":
    run_all(verbose=True)
