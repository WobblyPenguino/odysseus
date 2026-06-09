from __future__ import annotations

from winlocalassistant.high_spec_profile import build_high_spec_profile, render_high_spec_profile
from winlocalassistant.subagent_orchestrator import build_subagent_plan, render_subagent_plan
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry


def test_high_spec_profile_uses_upgraded_pc_models():
    profile = build_high_spec_profile(gpu_hint="RTX 5070 Ti 16GB", ram_gb=32)
    assert profile.code_model == "qwen3-coder:30b"
    assert profile.vision_model == "llama3.2-vision:11b"
    assert profile.local_model_timeout_sec >= 420
    assert profile.context_chars >= 16000
    assert "prompt lock" in "\n".join(profile.notes).lower()
    assert "qwen3-coder:30b" in render_high_spec_profile(profile)


def test_subagent_plan_keeps_ollama_model_calls_serialized():
    plan = build_subagent_plan("improve Nova safely", slots=4)
    assert plan["ok"] is True
    assert plan["max_parallel_slots"] == 4
    assert "serialize LLM prompts" in plan["model_lock_policy"]
    builder = [a for a in plan["agents"] if a["name"] == "builder"][0]
    assert builder["uses_llm"] is True
    assert builder["can_run_parallel"] is False
    assert "builder" in render_subagent_plan(plan)


def test_subagent_and_high_spec_tools_and_commands_are_exposed(tmp_path):
    registry = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    assert registry.call("high_spec_profile").ok is True
    assert registry.call("subagent_plan", goal="improve Nova").ok is True
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    assert "qwen3-coder:30b" in core.chat("/high-spec-profile")
    assert "serialized" in core.chat("/subagents improve Nova").lower()
    assert "Authority" in core.chat("/authority-mode")
