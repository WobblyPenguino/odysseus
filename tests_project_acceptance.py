from __future__ import annotations

from winlocalassistant.project_acceptance import build_project_acceptance_contract, build_project_repair_plan, evaluate_project_acceptance
from winlocalassistant.creation_intent import score_created_project_quality


def test_acceptance_contract_for_calculator_requires_real_behaviour() -> None:
    contract = build_project_acceptance_contract("make a calculator")
    assert contract.artifact_type == "calculator"
    assert any("clear" in item for item in contract.required_behaviours)
    assert any("event" in item.lower() for item in contract.required_behaviours)


def test_acceptance_rejects_static_calculator_mockup() -> None:
    result = evaluate_project_acceptance("make a calculator", ["index.html"], "<button>1</button><div>calculator</div>")
    assert not result["passed"]
    assert result["percent"] < 80
    assert result["missing_behaviours"]


def test_acceptance_accepts_functional_calculator_evidence() -> None:
    summary = "index.html app.js style.css calculator buttons 0 1 2 3 4 5 6 7 8 9 operator + - * / clear backspace result display textContent addEventListener calculate input"
    result = evaluate_project_acceptance("make a calculator", ["index.html", "app.js", "style.css", "README.md"], summary)
    assert result["passed"]
    assert result["percent"] >= 80


def test_game_acceptance_requires_restart_and_instructions() -> None:
    result = evaluate_project_acceptance("make a simple game", ["index.html", "app.js"], "keydown requestAnimationFrame score collision")
    assert not result["passed"]
    assert any("Restart" in item or "instructions" in item.lower() for item in result["missing_behaviours"])


def test_quality_score_includes_acceptance_contract_and_repair_plan() -> None:
    score = score_created_project_quality("make a simple game", ["index.html", "app.js"], "keydown requestAnimationFrame score collision")
    assert "acceptance_contract" in score
    assert "repair_plan" in score
    assert not score["passed_threshold"]
    assert score["repair_plan"]["actions"]


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
