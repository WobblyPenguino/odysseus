from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.creation_intent import analyze_creation_request, validate_created_artifact_matches_request
from winlocalassistant.tools import ToolRegistry


def test_snake_game_does_not_select_dodge_fallback() -> None:
    registry = ToolRegistry(AssistantConfig())
    fallback = registry._fallback_project_for_goal("make a snake game", "create")
    assert fallback is not None
    assert fallback["source"] == "generic_game_fallback"
    assert "dodge" not in fallback["folder"].lower()
    analysis = analyze_creation_request("make a snake game")
    assert analysis["requested_theme"] == "snake"
    assert "app.js" in analysis["likely_files"]
    assert analysis["dodge_fallback_allowed"] is False


def test_todo_web_app_and_calculator_use_request_aware_non_dodge_fallbacks() -> None:
    registry = ToolRegistry(AssistantConfig())
    todo = registry._fallback_project_for_goal("make a todo web app", "create")
    calc = registry._fallback_project_for_goal("make a calculator", "create")
    assert todo is not None and "todo" in (todo["human_summary"] + todo["folder"]).lower()
    assert calc is not None and "calculator" in (calc["human_summary"] + calc["folder"]).lower()
    assert "dodge" not in (todo["human_summary"] + todo["folder"]).lower()
    assert "dodge" not in (calc["human_summary"] + calc["folder"]).lower()
    assert analyze_creation_request("make a todo web app")["artifact_type"] == "web_app"
    assert analyze_creation_request("make a calculator")["requested_theme"] == "calculator"
    assert analyze_creation_request("make a file organiser script")["dodge_fallback_allowed"] is False


def test_broad_utility_app_gets_request_aware_fallback() -> None:
    registry = ToolRegistry(AssistantConfig())
    fallback = registry._fallback_project_for_goal("make a useful local utility application", "create")
    assert fallback is not None
    combined = (fallback["human_summary"] + " " + " ".join(fallback["files"].values())).lower()
    assert "utility" in combined
    assert "localstorage" in combined or "local storage" in combined
    assert "export" in combined
    assert "dodge" not in combined


def test_dodge_game_may_select_dodge_fallback() -> None:
    registry = ToolRegistry(AssistantConfig())
    fallback = registry._fallback_project_for_goal("make a dodge game", "create")
    assert fallback is not None
    assert "dodge" in (fallback["human_summary"] + fallback["notes"]).lower()
    assert analyze_creation_request("make a dodge game")["dodge_fallback_allowed"] is True


def test_shared_file_context_does_not_hide_simple_game_request() -> None:
    registry = ToolRegistry(AssistantConfig())
    goal = (
        "make a dodge game\n\n"
        "Use these user-shared files as context for this request:\n\n"
        "[Shared file context: screenshot.png | image | id=abc]\n"
        "Attached image: screenshot.png\n"
        "Type: image/png"
    )
    fallback = registry._fallback_project_for_goal(goal, "create")
    assert fallback is not None
    assert "dodge" in (fallback["human_summary"] + fallback["notes"]).lower()


def test_vague_simple_game_records_assumption() -> None:
    registry = ToolRegistry(AssistantConfig())
    fallback = registry._fallback_project_for_goal("make a simple game", "create")
    assert fallback is not None
    assert fallback["source"] == "generic_game_fallback"
    assert fallback.get("assumptions")
    analysis = analyze_creation_request("make a simple game")
    assert analysis["dodge_fallback_allowed"] is False
    assert analysis["assumptions"]


def test_artifact_validation_catches_calculator_dodge_mismatch() -> None:
    result = validate_created_artifact_matches_request(
        "make a calculator",
        ["index.html", "app.js", "style.css"],
        "Canvas Dodge Game with falling blocks",
    )
    assert result["matches_request"] is False
    assert result["unexpected_defaults"]
    assert result["missing_requirements"]


def test_creation_flow_validation_reports_mismatch_instead_of_success_shape() -> None:
    result = validate_created_artifact_matches_request(
        "make a file organiser script",
        ["index.html", "app.js"],
        "A browser game with canvas controls",
    )
    assert result["matches_request"] is False
    assert "does not match" in result["verification_summary"].lower()


def test_generated_plan_files_and_verification_follow_artifact_type() -> None:
    todo = analyze_creation_request("make a todo web app with search")
    assert todo["artifact_type"] == "web_app"
    assert {"index.html", "style.css", "app.js"}.issubset(set(todo["likely_files"]))
    assert any("node --check" in cmd for cmd in todo["verification_commands"])

    organiser = analyze_creation_request("make a file organiser script")
    assert organiser["artifact_type"] == "automation_script"
    assert any(path.endswith(".py") for path in organiser["likely_files"])
    assert any("py_compile" in cmd for cmd in organiser["verification_commands"])


def test_request_match_summary_reads_generated_file_contents() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_creation_summary_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<canvas id='game'></canvas><script src='app.js'></script>", encoding="utf-8")
        (root / "app.js").write_text("function updateDodgeGame(){ return 'dodge falling blocks'; }", encoding="utf-8")
        registry = ToolRegistry(AssistantConfig(workspace=tmp))
        summary = registry._created_artifact_request_summary(
            root,
            "Calculator",
            {"main_file": "index.html", "notes": "Generated browser app", "assumptions": []},
            [{"path": "index.html"}, {"path": "app.js"}],
        )
    result = validate_created_artifact_matches_request("make a calculator", ["index.html", "app.js"], summary)
    assert result["matches_request"] is False
    assert result["unexpected_defaults"]


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
