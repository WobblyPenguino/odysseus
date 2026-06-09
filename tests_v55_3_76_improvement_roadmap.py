from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.improvement_roadmap import (
    build_next_improvement_roadmap,
    build_improvement_impact_matrix,
    complete_next_improvements,
    load_latest_improvement_roadmap,
)
from winlocalassistant.autonomy_capabilities import select_capabilities_for_goal, get_capability_catalog


def test_v76_version_label_mentions_roadmap_and_legacy_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    for word in ["voice", "codebase", "packaging"]:
        assert word in low


def test_improvement_roadmap_generates_ranked_safe_proposals(tmp_path):
    payload = build_next_improvement_roadmap(tmp_path, "propose improvements and implement them")
    assert payload["ok"] is True
    assert payload["proposals"]
    assert payload["auto_implementable"]
    impact = build_improvement_impact_matrix(payload)
    assert impact["rows"]
    assert impact["rows"][0]["priority_score"] >= impact["rows"][-1]["priority_score"]


def test_implement_improvements_writes_ledger(tmp_path):
    payload = complete_next_improvements(tmp_path, "propose improvements and implement them", confirm=True)
    assert payload["status"] in {"completed", "implemented"}
    assert payload["completed_count"] >= 1
    assert payload.get("changed_files")
    assert Path(payload["markdown_path"]).exists()
    loaded = load_latest_improvement_roadmap(tmp_path)
    assert loaded["status"] in {"completed", "implemented"}


def test_core_routes_improvement_roadmap_commands(tmp_path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    out = app.handle_command("/improvement-roadmap propose improvements")
    assert "Improvement Roadmap" in out
    out2 = app.handle_command("/implement-improvements --confirm propose improvements")
    assert "Completed" in out2
    assert (tmp_path / "docs" / "NOVA_IMPROVEMENT_ROADMAP_LATEST.json").exists()


def test_tool_registry_exposes_improvement_roadmap_to_autonomy(tmp_path):
    app = AssistantCore(AssistantConfig(workspace=str(tmp_path)))
    for tool in ["improvement_roadmap", "improvement_impact", "implement_improvements", "proposal_ledger"]:
        assert tool in app.tools.tools
    result = app.tools.call("improvement_roadmap", focus="more improvements")
    assert result.ok
    assert "roadmap" in result.summary.lower()


def test_autonomy_catalog_knows_improvement_roadmap():
    names = {c.name for c in get_capability_catalog()}
    assert "improvement_roadmap" in names
    matches = select_capabilities_for_goal("propose improvements and implement the best safe ones", limit=10)
    assert "improvement_roadmap" in {m.capability.name for m in matches}
