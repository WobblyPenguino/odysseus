from __future__ import annotations

from winlocalassistant.creation_intent import score_created_project_quality, validate_created_artifact_matches_request


def test_project_quality_score_rejects_dead_calculator() -> None:
    score = score_created_project_quality("make a calculator", ["index.html"], "<button>1</button><div>Dodge Game</div>")
    assert not score["passed_threshold"]
    assert score["overall_percent"] < 75


def test_project_quality_score_accepts_reasonable_calculator_evidence() -> None:
    summary = "calculator buttons 0 1 2 3 4 5 6 7 8 9 + - * / clear backspace result display textContent addEventListener calculate"
    score = score_created_project_quality("make a calculator with clear", ["index.html", "app.js", "style.css"], summary, [{"ok": True}, {"ok": True}])
    assert score["passed_threshold"]
    assert score["behaviour_score"] >= 80


def test_validation_and_quality_catch_todo_dodge_mismatch() -> None:
    match = validate_created_artifact_matches_request("make a todo web app", ["index.html", "app.js"], "Canvas Dodge Game")
    score = score_created_project_quality("make a todo web app", ["index.html", "app.js"], "Canvas Dodge Game")
    assert not match["matches_request"]
    assert not score["passed_threshold"]


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
