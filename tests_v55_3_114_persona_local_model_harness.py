from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.persona_profile import (
    build_custom_chat_window_spec,
    build_persona_prompt_addendum,
    load_persona_profile,
    update_persona_from_tokens,
)
from winlocalassistant.local_model_optimizer import build_local_model_optimization_plan, build_iterative_agent_harness
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.feature_continuity import build_feature_continuity_audit
from winlocalassistant.validation_matrix import build_validation_matrix


def _root() -> Path:
    return Path.cwd()


def test_persona_profile_and_sliders_are_persistent_and_prompted():
    profile = update_persona_from_tokens("formality=0.8 humor=0.1 verbosity=0.25 technical_depth=0.9")
    assert profile["sliders"]["formality"] == 0.8
    assert profile["sliders"]["humor"] == 0.1
    prompt = build_persona_prompt_addendum("voice")
    assert "Nova persona contract" in prompt
    assert "Response contract" in prompt
    assert "formality=formal" in prompt
    assert "technical_depth=deep technical" in prompt


def test_custom_chat_window_spec_has_identity_response_contract_and_sliders():
    spec = build_custom_chat_window_spec()
    assert spec["title"] == "Custom Chat / Persona Window"
    assert "prompt_addendum" in spec
    keys = {s["key"] for s in spec["sliders"]}
    assert {"formality", "creativity", "humor", "empathy", "verbosity", "technical_depth", "proactivity"}.issubset(keys)
    assert "response_contract" in spec["persona"]


def test_local_model_optimizer_and_agent_harness_are_available():
    opt = build_local_model_optimization_plan(_root(), goal="repair repeated game generation")
    assert opt["ok"] is True
    assert "prompt_cache_design" in opt
    assert "model_routing" in opt
    assert any("OLLAMA_KV_CACHE_TYPE" in item["setting"] for item in opt["ollama_runtime_tuning"])
    harness = build_iterative_agent_harness(_root(), goal="build and repair app")
    assert harness["ok"] is True
    assert [step["step"] for step in harness["steps"]][:3] == ["contract", "baseline", "generate_or_patch"]
    assert "receipt" in [step["step"] for step in harness["steps"]]


def test_tool_registry_exposes_persona_voice_audit_and_optimizer_tools():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    for name in ["persona_profile", "persona_set", "persona_prompt", "custom_chat_window", "voice_audit", "local_model_optimizer", "agent_harness"]:
        assert name in registry.tools
    assert registry.call("persona_profile").ok
    assert registry.call("custom_chat_window").ok
    assert registry.call("local_model_optimizer").ok
    assert registry.call("agent_harness").ok


def test_local_model_context_contains_persona_and_optimization_contracts():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    text = registry._local_model_implementation_context(_root(), goal="redesign chat persona and repair code generation", last_reason="candidate_refine_repeat")
    assert "persona_profile" in text
    assert "persona_prompt_addendum" in text
    assert "local_model_optimization_plan" in text
    assert "iterative_agent_harness" in text
    assert "feature_preservation_contract" in text


def test_webui_contains_persona_left_controls_and_voice_audit_markers():
    webui = (_root() / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    for marker in ["personaMiniPanel", "personaCommandPreview", "/persona-set", "/custom-chat-window", "/local-model-optimizer", "/agent-harness", "/voice-audit", "updatePersonaCommandPreview"]:
        assert marker in webui


def test_feature_continuity_and_validation_matrix_cover_new_features():
    registry = ToolRegistry(AssistantConfig(workspace="."))
    audit = build_feature_continuity_audit(_root(), tool_names=list(registry.tools))
    assert audit["ok"], audit.get("failed")
    names = {c["name"] for c in audit["checks"]}
    assert "webui:persona_editor" in names
    assert "webui:local_model_optimizer" in names
    matrix = build_validation_matrix(_root(), goal="general Nova validation")
    assert matrix["ok"], matrix.get("failed")
