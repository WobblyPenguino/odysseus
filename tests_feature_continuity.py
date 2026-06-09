from __future__ import annotations

from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL

ROOT = Path(__file__).resolve().parent


def test_roadmap_modules_from_v51_to_v53_are_present() -> None:
    modules = [
        "idle_engine.py", "surgical_fallback.py", "autonomous_failure.py", "request_intent.py",
        "intent_planning.py", "task_decomposition.py", "creation_intent.py", "project_acceptance.py",
        "game_design.py", "project_runtime_probe.py", "project_iteration.py", "quality_dashboard.py",
        "action_watcher.py", "tool_catalog.py", "interaction_learning.py", "planning_dashboard.py", "autonomous_explain.py", "autonomous_sequence.py",
    ]
    missing = [m for m in modules if not (ROOT / "winlocalassistant" / m).exists()]
    assert not missing, f"Lost roadmap modules: {missing}"


def test_roadmap_commands_are_still_routed_or_visible() -> None:
    core = (ROOT / "winlocalassistant" / "core.py").read_text(encoding="utf-8")
    webui = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    combined = core + "\n" + webui
    commands = [
        "/idle", "/idle auto-apply", "/idle propose", "/autonomous", "/autonomous-memory",
        "/tool-guide", "/tool-catalog", "/action-watch", "/interaction-lessons",
        "/planning-dashboard", "/autonomous-explain", "/autonomous-plan", "/quality-dashboard", "/test-all", "/reply",
    ]
    missing = [cmd for cmd in commands if cmd not in combined]
    assert not missing, f"Lost routed/visible commands: {missing}"


def test_roadmap_docs_are_present() -> None:
    docs = [
        "NOVA_AUTONOMOUS_TOOL_USE_GUIDE.md",
        "NOVA_LOCAL_MODEL_TOOL_USE_GUIDE.md",
        "NOVA_TOOL_CATALOG.md",
        "IMPROVEMENT_REPORT_V53_4.md",
        "IMPROVEMENT_REPORT_V53_5.md",
        "IMPROVEMENT_REPORT_V53_6.md", "IMPROVEMENT_REPORT_V53_7.md", "IMPROVEMENT_REPORT_V53_8.md", "IMPROVEMENT_REPORT_V54_2.md",
    ]
    missing = [d for d in docs if not (ROOT / "docs" / d).exists()]
    assert not missing, f"Lost roadmap docs: {missing}"


def test_webui_keeps_panel_restore_and_created_output_features() -> None:
    html = (ROOT / "winlocalassistant" / "webui.py").read_text(encoding="utf-8")
    required = [
        "Show left panel", "Show right panel", "Show Live Activity",
        "Created output", "Current AI file focus", "Plan before run", "What autonomous is doing",
        "renderCommandSuggestions", "insertSuggestedCommand",
    ]
    missing = [x for x in required if x not in html]
    assert not missing, f"Lost UI continuity markers: {missing}"


def test_version_is_current_or_newer() -> None:
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def run_all(verbose: bool = False) -> None:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        fn()
        if verbose:
            print(f"PASS {name}")


if __name__ == "__main__":
    run_all(verbose=True)
