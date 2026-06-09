from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
import winlocalassistant.webui as webui


def _registry(tmp: str) -> ToolRegistry:
    return ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))


def test_calculator_quality_rejects_dead_ui() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_calc_quality_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Calculator</h1><button>1</button><div id='result'></div><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("console.log('calculator placeholder');", encoding="utf-8")
        ok, problems = _registry(tmp)._static_acceptance_check(root, "make a calculator app")
    assert not ok
    assert any(p["kind"] in {"calculator_missing_operations", "calculator_missing_interaction"} for p in problems)


def test_todo_quality_requires_add_delete_complete() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_todo_quality_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Todo</h1><input><button>Add</button><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("const tasks=[]; function addTask(){ tasks.push('x'); }", encoding="utf-8")
        ok, problems = _registry(tmp)._static_acceptance_check(root, "make a todo app with add delete and complete")
    assert not ok
    assert any(p["kind"] == "todo_missing_delete" for p in problems)
    assert any(p["kind"] == "todo_missing_complete" for p in problems)


def test_simple_game_quality_rejects_unmoving_square() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_game_quality_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<canvas id='game'></canvas><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("const canvas=document.getElementById('game'); const score=0; function draw(){ } setInterval(draw,16);", encoding="utf-8")
        ok, problems = _registry(tmp)._static_acceptance_check(root, "make a simple game")
    assert not ok
    assert any(p["kind"] in {"game_missing_user_controls", "game_missing_interaction"} for p in problems)


def test_webui_created_output_is_above_activity_and_details_open_by_default() -> None:
    html = webui.HTML
    assert html.index('id="artifactPanel"') < html.index('id="chat"') < html.index('id="activityLog"')
    assert 'Created output' in html
    assert 'Current AI file focus' in html
    assert "shouldEventOpen(detailsKey,true)" in html


def test_webui_panel_controls_and_settings_exist() -> None:
    html = webui.HTML
    assert 'Left panel' in html and 'togglePanel' in html and 'left' in html
    assert 'Right panel' in html and 'togglePanel' in html and 'right' in html
    assert 'settingsPanel' in html
    assert 'showQuickButtons' in html
    assert 'toggleSettingsPanel' in html


def test_calculator_quality_requires_digits_and_clear_behaviour() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_calc_digits_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Calculator</h1><button>+</button><button>=</button><div id='result'></div><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("function calculate(){ result.textContent = 1 + 1; } document.querySelector('button').addEventListener('click', calculate);", encoding="utf-8")
        ok, problems = _registry(tmp)._static_acceptance_check(root, "make a calculator app")
    assert not ok
    assert any(p["kind"] in {"calculator_missing_digits", "calculator_missing_clear"} for p in problems)


def test_simple_game_quality_requires_restart_and_instructions() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_game_restart_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<canvas id='game'></canvas><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("""
let score = 0; let player = {x:1,y:1}; let enemy = {x:3,y:3};
document.addEventListener('keydown', e => { player.x += 1; });
function collision(){ return player.x === enemy.x; }
function update(){ score++; if(collision()) score = 0; }
function draw(){}
requestAnimationFrame(function loop(){ update(); draw(); requestAnimationFrame(loop); });
""", encoding="utf-8")
        ok, problems = _registry(tmp)._static_acceptance_check(root, "make a simple game")
    assert not ok
    assert any(p["kind"] in {"game_missing_restart_or_end_state", "game_missing_instructions"} for p in problems)


def test_pytest_ini_discovers_tests_underscore_files() -> None:
    ini = Path("pytest.ini").read_text(encoding="utf-8")
    assert "python_files = tests_*.py" in ini


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
