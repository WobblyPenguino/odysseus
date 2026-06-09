from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.pipeline_router import classify_pipeline, write_project_patterns
from winlocalassistant.tools import ToolRegistry


def test_pipeline_router_classifies_broad_requests_away_from_build() -> None:
    assert classify_pipeline("all our projects and identify improvements").kind == "project_review"
    assert classify_pipeline("review the entire database and ensure no regression").kind == "database_review"
    assert classify_pipeline("test each individual functionality and validate results").kind == "qa"
    assert classify_pipeline("fix the GUI live activity drawer layout").kind == "gui"
    assert classify_pipeline("set up remote phone laptop access with Tailscale and Wake-on-LAN").kind == "remote_access"
    assert classify_pipeline("make a 10 second video trailer and check ComfyUI/ffmpeg").kind == "media"
    assert classify_pipeline("Hey Nova ready sound and voice state machine").kind == "voice"


def test_pipeline_preflight_tool_returns_stage_contract() -> None:
    with tempfile.TemporaryDirectory(prefix="nova146_pipeline_") as tmp:
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        result = registry.call("pipeline_preflight", goal="review the entire database and ensure no regression")
        assert result.ok
        assert result.data["kind"] == "database_review"
        assert "Audit assistant DB" in result.data["message"]
        assert result.data["stages"]


def test_project_patterns_writes_memory_file_when_confirmed() -> None:
    with tempfile.TemporaryDirectory(prefix="nova146_patterns_") as tmp:
        root = Path(tmp)
        (root / "app.py").write_text("print('hello')\n", encoding="utf-8")
        payload = write_project_patterns(root, write=True)
        assert payload["runtime"] == "python"
        assert (root / "NOVA_PATTERNS.md").exists()
        assert "python -m compileall" in (root / "NOVA_PATTERNS.md").read_text(encoding="utf-8")


def test_core_pipeline_commands_are_deterministic_and_non_llm() -> None:
    with tempfile.TemporaryDirectory(prefix="nova146_core_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        reply = core.chat("/pipeline-preflight all our projects and identify improvements")
        assert "Project library review pipeline" in reply
        assert "ai_create_project" not in reply
        timeline = core.chat("/live-timeline 5")
        assert "Nova Live Timeline" in timeline


def test_broad_project_review_natural_text_does_not_create_new_app_plan() -> None:
    with tempfile.TemporaryDirectory(prefix="nova146_route_") as tmp:
        core = AssistantCore(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        reply = core.chat("all our projects and identify the projects that need improvements")
        assert "project-library review" in reply.lower()
        assert "ai_create_project" not in reply
        assert core.last_plan is not None
        assert core.last_plan.mode == "project_library_review"
