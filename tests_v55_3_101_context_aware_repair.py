from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry


def test_version_updated_for_context_aware_repair_release():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_local_model_context_pack_includes_runtime_analysis_and_verification(tmp_path):
    (tmp_path / "index.html").write_text("<canvas id='game'></canvas>", encoding="utf-8")
    (tmp_path / "app.js").write_text("let score = 0;", encoding="utf-8")
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    context = reg._local_model_implementation_context(
        tmp_path,
        goal="make a game in a new project about hair",
        last_reason="Game runtime sanity check failed: missing collision logic",
        attempts=[{"attempt": 1, "status": "validation_failed", "reason": "missing collision", "files": ["app.js"]}],
    )
    lower = context.lower()
    assert "verification_conditions" in lower
    assert "collision" in lower
    assert "previous_attempts" in lower
    assert "same validation reason" in lower
    assert "index.html" in context


def test_model_prompts_receive_local_run_context_and_retry_history():
    src = Path("winlocalassistant/tools.py").read_text(encoding="utf-8")
    assert "LOCAL RUN CONTEXT / ANALYSIS / VERIFICATION CONDITIONS" in src
    assert "_local_model_implementation_context(Path(self.workspace), goal=goal" in src
    assert "attempts=attempts" in src
    assert "If the same validation reason appears twice" in src


def test_existing_gui_and_tool_functionality_markers_were_not_removed():
    src = Path("winlocalassistant/webui.py").read_text(encoding="utf-8")
    for marker in [
        'id="projects"',
        'id="customTools"',
        'id="activityLog"',
        'deleteSelectedRuns',
        '/api/activity-delete-runs',
        'loadAssistantBox',
        'loadTools',
        'loadProjects',
        'Stop stuck task',
        'data-ui-overhaul="v55.3.115"',
    ]:
        assert marker in src


def test_game_verification_conditions_are_concrete(tmp_path):
    reg = ToolRegistry(AssistantConfig(workspace=str(tmp_path)))
    checks = reg._local_model_verification_conditions("make a game about hair")
    joined = "\n".join(checks).lower()
    assert "controls" in joined
    assert "collision" in joined
    assert "score" in joined
    assert "theme" in joined
