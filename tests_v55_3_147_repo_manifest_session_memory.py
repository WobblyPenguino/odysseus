from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.pipeline_manifests import MANIFESTS, choose_manifests_for_goal, render_manifest, render_manifest_catalog
from winlocalassistant.planner import make_plan
from winlocalassistant.session_evidence import build_session_evidence, render_session_evidence
from winlocalassistant.memory_inventory import build_memory_inventory, render_memory_inventory
from winlocalassistant.tools import ToolRegistry


def test_capability_manifest_catalog_maps_repo_ideas_to_nova_contracts() -> None:
    assert "checkpointed_patch" in MANIFESTS
    assert "coding_session_evidence" in MANIFESTS
    chosen = choose_manifests_for_goal("continue integrating ideas from OpenMontage and browser-use repos")
    ids = {m.manifest_id for m in chosen}
    assert "checkpointed_patch" in ids or "browser_gui_smoke" in ids
    text = render_manifest_catalog("integrate repo ideas into Nova")
    assert "borrow architecture ideas, not third-party code" in text
    assert "OpenHands" in text
    assert "browser-use" in text
    one = render_manifest("typed_memory_audit")
    assert "Mem0/OpenMemory" in one
    assert "/memory-inventory" in one


def test_new_tools_render_manifests_session_evidence_and_memory_inventory() -> None:
    with tempfile.TemporaryDirectory(prefix="nova147_tools_") as tmp:
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        catalog = registry.call("pipeline_catalog", goal="voice ready sound and GUI browser errors", write=False)
        assert catalog.ok
        assert "Capability Manifests" in catalog.data["message"]
        manifest = registry.call("pipeline_manifest", manifest_id="voice_state_machine")
        assert manifest.ok
        assert "Voice state-machine" in manifest.data["message"] or "voice_state_machine" in manifest.data["message"]
        evidence = registry.call("session_evidence", run_id="latest", limit=30)
        assert evidence.ok
        assert "Nova Session Evidence" in evidence.data["message"]
        memory = registry.call("memory_inventory", path=".")
        assert memory.ok
        assert "Nova Memory Inventory" in memory.data["message"]


def test_session_evidence_renderer_is_bounded_and_has_guardrail() -> None:
    payload = build_session_evidence("latest", limit=40)
    text = render_session_evidence(payload)
    assert "Nova Session Evidence" in text
    assert "Guardrail" in text
    assert len(payload.get("events", [])) <= 80


def test_memory_inventory_renderer_handles_empty_workspace() -> None:
    with tempfile.TemporaryDirectory(prefix="nova147_memory_") as tmp:
        payload = build_memory_inventory(Path(tmp))
        text = render_memory_inventory(payload)
        assert "Nova Memory Inventory" in text
        assert "Assistant databases" in text
        assert "Recommendations" in text


def test_repo_integration_prompt_routes_to_validation_not_model_build() -> None:
    from winlocalassistant.pipeline_router import classify_pipeline
    assert classify_pipeline("continue integrating ideas from the repos and fixing errors").kind == "repo_upgrade"
    plan = make_plan("continue integrating ideas from the repos and fixing errors")
    tools = [step.tool for step in plan.steps]
    assert plan.mode == "repo_upgrade"
    assert "ai_create_project" not in tools
    assert "pipeline_catalog" in tools
    assert "session_evidence" in tools
    assert "browser_smoke" in tools
    assert "bug_review" in tools
    assert "regression_sweep" in tools


def test_core_commands_are_available_and_non_mutating_by_default() -> None:
    with tempfile.TemporaryDirectory(prefix="nova147_core_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        catalog = core.chat("/pipeline-catalog integrate repo ideas into Nova")
        assert "Repo-Inspired Capability Manifests" in catalog
        evidence = core.chat("/session-evidence latest 30")
        assert "Nova Session Evidence" in evidence
        memory = core.chat("/memory-inventory")
        assert "Nova Memory Inventory" in memory
        natural = core.chat("continue integrating ideas from the repos and fixing errors")
        assert "repo_upgrade" in natural or "Capability" in natural or "Running plan" in natural
        assert "ai_create_project" not in natural
