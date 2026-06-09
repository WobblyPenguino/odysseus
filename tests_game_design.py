from __future__ import annotations

from winlocalassistant.config import AssistantConfig
from winlocalassistant.game_design import analyze_game_request, build_generic_canvas_game_project, game_prompt_requirements
from winlocalassistant.creation_intent import analyze_creation_request
from winlocalassistant.project_acceptance import evaluate_project_acceptance
from winlocalassistant.tools import ToolRegistry


def test_arbitrary_named_game_intent_is_not_dodge_template() -> None:
    intent = analyze_game_request("make a fishing game with upgrades")
    assert intent.requested_game_type == "fishing"
    assert intent.genre == "collection"
    assert "fish" in intent.core_objects
    assert intent.allowed_template_family == "custom_canvas_game"
    creation = analyze_creation_request("make a fishing game with upgrades")
    assert creation["dodge_fallback_allowed"] is False
    assert creation["requested_theme"] == "fishing"


def test_generic_game_fallback_uses_requested_theme() -> None:
    project = build_generic_canvas_game_project("make a fishing game with upgrades")
    combined = "\n".join(project["files"].values()).lower()
    assert project["source"] == "generic_game_fallback"
    assert "fishing" in combined or "fish" in combined
    assert "canvas dodge game" not in combined
    assert "restart" in combined
    assert "score" in combined
    assert "instructions" in combined


def test_about_theme_beats_polish_adjectives_for_game_fallback() -> None:
    intent = analyze_game_request("make a polished browser game about rabbits")
    assert intent.requested_game_type == "rabbits game"
    assert "rabbits" in intent.core_objects
    project = build_generic_canvas_game_project("make a polished browser game about rabbits")
    combined = "\n".join(project["files"].values()).lower()
    assert "rabbit" in combined
    assert "canvas dodge game" not in combined


def test_tool_fallback_for_custom_game_is_generic_not_dodge() -> None:
    registry = ToolRegistry(AssistantConfig())
    project = registry._fallback_project_for_goal("make a fishing game with upgrades", "create")
    assert project is not None
    assert project["source"] == "generic_game_fallback"
    assert "dodge" not in project["folder"].lower()
    assert project["game_design"]["requested_game_type"] == "fishing"


def test_explicit_dodge_still_uses_dodge_fallback() -> None:
    registry = ToolRegistry(AssistantConfig())
    project = registry._fallback_project_for_goal("make a dodge game", "create")
    assert project is not None
    assert project["source"] == "deterministic_fallback"
    assert "dodge" in project["human_summary"].lower()


def test_game_prompt_requirements_warn_against_fixed_demo() -> None:
    req = game_prompt_requirements("make a maze game")
    rules = " ".join(req["prompt_rules"]).lower()
    assert "not a fixed dodge demo" in rules
    assert req["game_design"]["requested_game_type"] == "maze"


def test_acceptance_contract_checks_custom_game_theme() -> None:
    weak = evaluate_project_acceptance("make a fishing game", ["index.html", "app.js"], "keydown requestAnimationFrame score collision restart instructions")
    assert not weak["passed"]
    assert any("fish" in str(item).lower() or "theme" in str(item).lower() for item in weak["missing_behaviours"])
    strong = evaluate_project_acceptance(
        "make a fishing game",
        ["index.html", "app.js", "style.css", "README.md"],
        "fishing fish hook water catching timing keydown requestAnimationFrame score collision restart instructions controls update draw",
    )
    assert strong["passed"]


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
