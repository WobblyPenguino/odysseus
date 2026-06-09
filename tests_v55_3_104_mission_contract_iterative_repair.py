from pathlib import Path

from winlocalassistant.autonomous_mission_contract import build_mission_contract, score_progress, should_switch_strategy
from winlocalassistant.project_type_registry import project_type_contract
from winlocalassistant.surgical_recipes import classify_failure, patch_candidate_for_failure, recipe_steps
from winlocalassistant.self_test_generator import generate_regression_test
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def test_mission_contract_for_game_forbids_heartbeat_success():
    contract = build_mission_contract("make a game about hair")
    text = "\n".join(contract["success_conditions"] + contract["forbidden_success_conditions"])
    assert "collision" in text.lower()
    assert "heartbeat only" in text.lower()
    assert contract["target_type"] == "project"


def test_progress_scoring_detects_no_progress_loop():
    events = [
        {"kind": "heartbeat", "message": "Heartbeat completed", "data": {}},
        {"kind": "candidate_refine_prompt", "message": "Asking local model", "data": {}},
        {"kind": "candidate_refine_prompt", "message": "Asking local model", "data": {}},
        {"kind": "candidate_refine_no_progress", "message": "Stopped repeated candidate refinement", "data": {}},
    ]
    progress = score_progress(events, build_mission_contract("make a game"))
    assert progress["score"] < 0
    assert should_switch_strategy(progress)


def test_surgical_recipe_patches_missing_game_collision_candidate():
    candidate = {"files": {"app.js": "const player={x:0,y:0,w:10,h:10}; window.targets=[]; window.hazards=[];"}}
    patched, edits = patch_candidate_for_failure(candidate, "make a game", "game_missing_collision")
    assert edits
    assert "rectsOverlap" in patched["files"]["app.js"]
    assert "checkCollisions" in patched["files"]["app.js"]


def test_project_type_registry_selects_game_contract():
    contract = project_type_contract("make a browser game about hair")
    assert contract["kind"] == "html_css_js_game"
    assert "collision" in contract["markers"]


def test_self_test_generator_for_reference_error():
    test_src = generate_regression_test("Uncaught ReferenceError: loadAssistantBox is not defined")
    assert "loadAssistantBox" in test_src
    assert "window.loadAssistantBox" in test_src


def test_tool_registry_exposes_new_mission_and_recipe_tools(tmp_path):
    tools = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    result = tools.call("mission_contract", goal="implement a game fix")
    assert result.ok
    assert "Mission Contract" in result.data["message"]
    recipe = tools.call("surgical_recipe", goal="make a game", failure="game_missing_collision")
    assert recipe.ok
    assert "inject_collision_loop" in str(recipe.data)
    registry = tools.call("project_type_registry", goal="python script")
    assert registry.ok
    assert registry.data["selected"]["kind"] == "python_cli_script"


def test_local_model_context_includes_mission_and_patch_not_regenerate_rules(tmp_path):
    tools = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    text = tools._local_model_implementation_context(tmp_path, goal="make a game about hair", last_reason="game_missing_collision")
    assert "mission_contract" in text
    assert "project_type_contract" in text
    assert "Patch existing files" in text
    assert "deterministic template" in text
