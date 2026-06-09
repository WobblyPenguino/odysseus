from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.improvement_cycle import build_improvement_proposals, complete_improvement_proposals, load_latest_improvement_cycle, render_improvement_cycle
from winlocalassistant.autonomy_capabilities import get_capability_catalog, select_capabilities_for_goal, build_mutable_mission_plan
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.core import AssistantCore


def test_version_label_mentions_improvement_cycle_and_legacy_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    for word in ["voice", "codebase", "packaging"]:
        assert word in low


def test_improvement_proposals_are_ranked_and_implementation_ready(tmp_path):
    payload = build_improvement_proposals(tmp_path, "propose improvements and complete them")
    assert payload["proposal_count"] >= 3
    assert payload["proposals"][0]["id"] == "proposal-loop-report"
    assert payload["proposals"][-1]["category"] == "targeting"
    assert any("/improvement-cycle --confirm" in p["commands"] for p in payload["proposals"])
    md = render_improvement_cycle(payload)
    assert "Proposed improvements" in md
    assert "Make improvement proposals completable" in md


def test_improvement_cycle_confirm_writes_report_and_done_status(tmp_path):
    (tmp_path / "tests_smoke.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    payload = complete_improvement_proposals(tmp_path, "improvements", confirm=True)
    assert payload["status"] == "completed"
    assert payload["completed_count"] >= 3
    assert Path(payload["markdown_path"]).exists()
    assert Path(payload["json_path"]).exists()
    latest = load_latest_improvement_cycle(tmp_path)
    assert latest["status"] == "completed"
    assert latest["completed_count"] == payload["completed_count"]


def test_autonomy_catalog_can_select_improvement_cycle():
    catalog_names = {c.name for c in get_capability_catalog()}
    assert "improvement_proposal_cycle" in catalog_names
    matches = select_capabilities_for_goal("propose improvements and complete improvement proposals", limit=5)
    assert any(m.capability.name == "improvement_proposal_cycle" for m in matches)
    plan = build_mutable_mission_plan("propose improvements and implement proposals")
    assert any(m.capability.name == "improvement_proposal_cycle" for m in plan.capabilities)


def test_tool_registry_exposes_improvement_cycle_tools(tmp_path):
    cfg = AssistantConfig(workspace=tmp_path, allow_mutating_tools=True)
    tools = ToolRegistry(cfg)
    for name in ["improvement_proposals_v2", "improvement_cycle", "improvement_status"]:
        assert name in tools.tools
    result = tools.call("improvement_cycle", focus="complete improvements", confirm=True)
    assert result.ok
    assert result.data["result"]["status"] == "completed"


def test_core_routes_improvement_cycle_commands(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    app = AssistantCore(AssistantConfig(workspace=tmp_path, allow_mutating_tools=True))
    out = app.handle_command("/improvement-proposals complete improvements")
    assert "Nova Improvement Proposal Completion Cycle" in out
    out = app.handle_command("/improvement-cycle --confirm")
    assert "Completed:" in out
    out = app.handle_command("/completed-improvements")
    assert "completed" in out.lower()
