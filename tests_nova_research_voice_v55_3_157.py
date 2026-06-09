from __future__ import annotations

from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.game_design import analyze_game_request
from winlocalassistant.research_engine import discover_source_urls
from winlocalassistant.tools import ToolResult


def test_natural_language_search_routes_to_research(tmp_path):
    core = AssistantCore(AssistantConfig(workspace=str(tmp_path), allow_mutating_tools=True, allow_internet=False))
    assert core._looks_like_natural_research_request("search for information about ww2")
    calls = []
    def fake_call(name, **kwargs):
        calls.append((name, kwargs))
        if name == "research":
            return ToolResult(True, "Research report generated", {"source_count": 2, "message": "# Research report"})
        return ToolResult(True, "ok", {})
    core.tools.call = fake_call  # type: ignore[method-assign]
    reply = core.chat("search for information about ww2")
    assert "live research request" in reply
    assert core.config.allow_internet is True
    assert calls and calls[0][0] == "research"
    assert "ww2" in calls[0][1]["topic"].lower()


def test_seeded_sources_cover_ww2_and_neil_without_generic_search():
    ww2 = discover_source_urls("World War II", limit=3)
    neil = discover_source_urls("Neil the seal Tasmania", limit=3)
    assert any("World_War_II" in u or "World-War-II" in u for u in ww2)
    assert any("Neil" in u or "neil-the-seal" in u.lower() for u in neil)


def test_game_theme_strips_interactive_clarification_text():
    intent = analyze_game_request("make a funny game about dogs\n\nUser clarification for this interactive run:\n- create a new project for make a funny game about dogs")
    assert intent.requested_game_type == "dogs game"
    assert "clarification" not in intent.normalized_text


def test_compare_alias_and_voice_summary_markers_present():
    core_text = __import__('pathlib').Path('winlocalassistant/core.py').read_text(encoding='utf-8')
    webui = __import__('pathlib').Path('winlocalassistant/webui.py').read_text(encoding='utf-8')
    assert '"/compare"' in core_text
    assert 'Nova voice summary v55.3.158' in webui
    assert '/internet-search' in core_text
