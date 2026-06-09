from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def _registry(tmp: str) -> ToolRegistry:
    return ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))


def test_calculator_behaviour_contract_rejects_no_result_update() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Calculator</h1><button>1</button><button>+</button><button>-</button><button>*</button><div id='result'></div><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("document.querySelector('button').addEventListener('click', () => console.log('clicked'));", encoding="utf-8")
        ok, problems = _registry(tmp)._behavioural_contract_check(root, "make a calculator app")
    assert not ok
    assert any(p["kind"] == "calculator_no_result_update" for p in problems)


def test_todo_behaviour_contract_rejects_no_render_or_state() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Todo</h1><button>Add</button><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("function addTask(){ console.log('add'); }", encoding="utf-8")
        ok, problems = _registry(tmp)._behavioural_contract_check(root, "make a todo app")
    assert not ok
    assert any(p["kind"] in {"todo_no_task_state", "todo_no_render_update"} for p in problems)


def test_game_behaviour_contract_rejects_no_actor_or_updates() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<canvas></canvas><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("let score = 0; function draw(){} requestAnimationFrame(draw);", encoding="utf-8")
        ok, problems = _registry(tmp)._behavioural_contract_check(root, "make a simple game")
    assert not ok
    assert any(p["kind"] in {"game_no_actor_state", "game_no_state_updates"} for p in problems)


def test_project_quality_includes_behavioural_contract_check() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>Calculator</h1><button>1</button><button>+</button><button>-</button><button>*</button><button>clear</button><div id='result'></div><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("document.querySelector('button').addEventListener('click', () => console.log('clicked'));", encoding="utf-8")
        result = _registry(tmp)._project_quality_verify(root, {"goal": "make a calculator app", "main_file": "index.html"})
    assert not result.ok
    assert any(c.get("name") == "behavioural_contract" for c in result.data.get("checks", []))


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
