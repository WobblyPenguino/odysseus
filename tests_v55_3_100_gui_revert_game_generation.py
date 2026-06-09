from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.game_design import analyze_game_request, build_generic_canvas_game_project
from winlocalassistant.tools import ToolRegistry


def test_pre_vscode_refined_cockpit_restored_without_losing_runtime_ids():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert 'data-ui-overhaul="v55.3.115"' in src
    assert 'vscodeWorkbench' not in src
    assert 'Control Centre' in src
    assert '<div id="smartTopStrip"' in src
    for marker in [
        'id="projects"',
        'id="customTools"',
        'id="activityLog"',
        'deleteSelectedRuns',
        '/api/activity-delete-runs',
        'runHumanTitle',
        'Stop stuck task',
    ]:
        assert marker in src


def test_nova_status_objects_are_rendered_readably_not_object_object():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    assert "function novaStatusValue" in src
    assert "String(live.autonomous)" not in src
    assert "String(live.idle)" not in src
    assert "[object Object]" not in src


def test_hair_game_theme_is_extracted_from_about_prompt():
    intent = analyze_game_request("make a game in a new project about hair")
    assert intent.requested_game_type == "hair game"
    assert "hair" in intent.core_objects
    assert intent.allowed_template_family == "custom_canvas_game"


def test_hair_game_fallback_is_themed_and_passes_static_contract(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    project = reg._fallback_project_for_goal("make a game in a new project about hair", "create")
    assert project is not None
    combined = "\n".join(project["files"].values()).lower()
    assert "hair" in combined
    assert "canvas" in combined
    assert "score" in combined
    assert "rectshit" in combined or "collision" in combined or "rects" in combined
    assert "keydown" in combined
    ok, reason = reg._validate_model_project(project, "make a game in a new project about hair")
    assert ok, reason


def test_repeating_weak_game_candidate_is_replaced_with_fallback(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    weak = {
        "folder": "Simplebrowsergame",
        "main_file": "index.html",
        "files": {
            "index.html": "<html><body><h1>Hair game</h1><p>Score: <span id='score'>0</span></p><script src='app.js'></script></body></html>",
            "app.js": "let score = 0; document.getElementById('score').textContent = score; console.log('game');",
            "README.md": "A game about hair with score."
        },
    }
    refined, edits = reg._deterministic_refine_candidate(
        weak,
        "make a game in a new project about hair User clarification: build a polished minimal html_css_js_page",
        "model output did not implement the requested domain"
    )
    combined = "\n".join(refined["files"].values()).lower()
    assert any(e["kind"] == "candidate_domain_fallback" for e in edits)
    assert "hair" in combined
    assert "canvas" in combined
    assert "keydown" in combined
    assert "score" in combined
    assert reg._validate_model_project(refined, "make a game in a new project about hair")[0]
