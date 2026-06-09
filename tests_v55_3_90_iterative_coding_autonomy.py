from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.iterative_coding import build_surgical_fallback_plan, build_iterative_coding_loop
from winlocalassistant.autonomy_capabilities import get_capability_catalog, build_mutable_mission_plan
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence


def test_version_label_mentions_iterative_coding():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL


def test_surgical_fallback_detects_html_js_mismatch(tmp_path):
    (tmp_path / "index.html").write_text('<button onclick="saveNote()">Save</button><div id="notes"></div>', encoding="utf-8")
    (tmp_path / "app.js").write_text("document.getElementById('missing').textContent='x';", encoding="utf-8")
    payload = build_surgical_fallback_plan(tmp_path, "make a notes app")
    kinds = {w["kind"] for w in payload["state"]["warnings"]}
    assert "missing_handler" in kinds
    assert "missing_dom_id" in kinds
    assert any(a["type"].startswith("minimal") for a in payload["actions"])


def test_iterative_loop_uses_quality_browser_and_surgical_tools(tmp_path):
    (tmp_path / "index.html").write_text('<script src="app.js"></script>', encoding="utf-8")
    (tmp_path / "app.js").write_text("console.log('ok')", encoding="utf-8")
    payload = build_iterative_coding_loop(tmp_path, "notes app with localStorage and JSON export")
    tools = [s["tool"] for p in payload["passes"] for s in p["steps"]]
    assert "prompt_contract" in tools
    assert "build_quality_report" in tools
    assert "browser_runtime_test" in tools
    assert "surgical_fallback_v2" in tools
    assert "model_output_coach" in tools


def test_tool_registry_exposes_iterative_repair_tools(tmp_path):
    cfg = AssistantConfig.load()
    cfg.workspace = str(tmp_path)
    tr = ToolRegistry(cfg)
    for name in ["iterative_coding_loop", "surgical_fallback_v2", "edit_repair_plan", "coding_loop_status"]:
        assert name in tr.tools
    result = tr.call("iterative_coding_loop", goal="build and iteratively test notes app")
    assert result.ok
    assert "Iterative" in result.summary or "iterative" in result.data.get("message", "").lower()


def test_autonomy_capability_and_sequence_include_iterative_repair():
    catalog_names = {c.name for c in get_capability_catalog()}
    assert "iterative_coding_repair" in catalog_names
    plan = build_mutable_mission_plan("improve editing surgical fallback and iterative coding capabilities")
    assert any(m.capability.name == "iterative_coding_repair" for m in plan.capabilities)
    seq = build_autonomous_tool_sequence("fix broken generated app with surgical fallback and iterative tests")
    tools = [s.tool for s in seq.steps]
    assert "surgical_fallback_v2" in tools or "iterative_coding_loop" in tools or "edit_repair_plan" in tools
