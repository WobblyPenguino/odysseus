from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.project_runtime_probe import run_project_runtime_probe
from winlocalassistant.tools import ToolRegistry


def test_runtime_probe_rejects_static_calculator() -> None:
    result = run_project_runtime_probe(
        "make a calculator",
        sources={"index.html": "<button>1</button><div id='result'></div>", "app.js": "console.log('static calculator')"},
    )
    assert not result["passed"]
    assert any(not check["ok"] for check in result["checks"])
    assert result["manual_test_steps"]


def test_runtime_probe_accepts_interactive_calculator_evidence() -> None:
    js = """
    let current = ''; let previous = ''; let operator = '';
    document.querySelectorAll('.digit').forEach(b=>b.addEventListener('click',()=>{current += b.textContent; display.textContent=current;}));
    document.querySelector('#plus').addEventListener('click',()=>{operator='+'; previous=current; current='';});
    document.querySelector('#equals').addEventListener('click',()=>{display.textContent = calculate(previous, current, operator);});
    document.querySelector('#clear').addEventListener('click',()=>{current=''; previous=''; display.textContent='0';});
    """
    html = "<button class='digit'>1</button><button class='digit'>2</button><button class='digit'>3</button><button class='digit'>4</button><button id='plus'>+</button><button id='equals'>=</button><button id='clear'>Clear</button><div id='display'></div>"
    result = run_project_runtime_probe("make a calculator", sources={"index.html": html, "app.js": js})
    assert result["passed"]
    assert result["percent"] >= 80


def test_runtime_probe_checks_custom_game_theme() -> None:
    weak = run_project_runtime_probe("make a fishing game", sources={"index.html": "<canvas></canvas>", "app.js": "let score=0; function loop(){requestAnimationFrame(loop)} document.addEventListener('keydown',()=>{}); function restart(){}"})
    assert not weak["passed"]
    assert any("theme" in check["name"] or "objective" in check["name"] for check in weak["checks"])
    strong = run_project_runtime_probe(
        "make a fishing game",
        sources={"index.html": "<p>Instructions: use arrows to move the hook in the water, use timing to catch fish, score points, and press restart.</p><canvas></canvas>", "app.js": "let player={x:0,y:0}; let hook={x:0,y:1}; let water={}; let fish={x:2,y:3}; let score=0; let timing=0; document.addEventListener('keydown', move); function catching(){ collision(); } function collision(){ score += 1; } function update(){ timing++; catching(); draw(); requestAnimationFrame(update); } function restart(){score=0; timing=0;}"},
    )
    assert strong["passed"]


def test_project_quality_verify_includes_runtime_probe() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Calculator</h1><button>1</button><button>+</button><div id='result'></div><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("document.querySelector('button').addEventListener('click', () => console.log('clicked'));", encoding="utf-8")
        result = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))._project_quality_verify(root, {"goal": "make a calculator app", "main_file": "index.html"})
    assert not result.ok
    assert any(check.get("name") == "project_runtime_probe" for check in result.data.get("checks", []))


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
