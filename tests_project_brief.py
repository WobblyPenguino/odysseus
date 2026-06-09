from __future__ import annotations

from winlocalassistant.project_brief import infer_project_build_brief
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def test_project_brief_infers_stock_trading_workflows() -> None:
    brief = infer_project_build_brief("build a stock trading simulator with buy sell portfolio profit loss local saving and export")
    assert brief.domain == "stock_trading"
    text = " ".join(brief.functional_requirements + brief.data_model + brief.acceptance_tests).lower()
    assert "buy" in text and "sell" in text
    assert "profit" in text or "loss" in text
    assert "export" in text
    assert "localstorage" in " ".join(brief.nonfunctional_requirements).lower() or "persist" in text


def test_autonomous_create_project_starts_with_project_spec() -> None:
    plan = build_autonomous_tool_sequence("build a chemistry quiz app with scoring and review mode")
    tools = [step.tool for step in plan.steps]
    assert tools[0] == "detect_project"
    assert "project_spec" in tools
    assert tools.index("project_spec") < tools.index("ai_create_project")


def test_project_spec_tool_writes_brief(tmp_path) -> None:
    config = AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True)
    registry = ToolRegistry(config)
    result = registry.call("project_spec", goal="make a snake game with score restart and keyboard controls")
    assert result.ok
    assert (tmp_path / "PROJECT_BUILD_BRIEF.md").exists()
    assert (tmp_path / "PROJECT_BUILD_BRIEF.json").exists()
    brief = result.data["brief"]
    assert brief["artifact_type"] in {"snake_game", "browser_game"}
    assert any("restart" in item.lower() for item in brief["acceptance_tests"])


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    import tempfile
    from pathlib import Path
    for name, fn in tests:
        if name.endswith("tool_writes_brief"):
            with tempfile.TemporaryDirectory() as d:
                fn(Path(d))
        else:
            fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
