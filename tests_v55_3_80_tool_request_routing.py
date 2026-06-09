from __future__ import annotations

import tempfile
from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.intent_planning import analyze_planning_dialog_need
from winlocalassistant.tools import ToolRegistry


def test_version_bumped_for_tool_routing_fix() -> None:
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_make_yourself_tool_does_not_open_generic_project_planning_dialog() -> None:
    dialog = analyze_planning_dialog_need("now make yourself a useful tool", {})
    assert dialog.should_ask is False
    assert "tool" in dialog.detected_intents[0]


def test_core_routes_self_tool_request_to_guarded_tool_creator() -> None:
    core = object.__new__(AssistantCore)
    assert core._looks_like_custom_tool_request("now make yourself a useful tool") is True
    assert core._looks_like_custom_tool_request("create a custom tool to inspect files") is True


def test_generic_self_tool_request_gets_deterministic_safe_tool_without_llm() -> None:
    with tempfile.TemporaryDirectory(prefix="wla_tool_route_") as tmp:
        root = Path(tmp)
        (root / "index.html").write_text("<h1>ok</h1>", encoding="utf-8")
        registry = ToolRegistry(AssistantConfig(workspace=tmp, allow_mutating_tools=True))
        result = registry.tool_create("now make yourself a useful tool")
        assert result.ok, result.data
        assert result.data.get("source") == "deterministic_fallback"
        assert result.data.get("name") == "project_health_snapshot"
