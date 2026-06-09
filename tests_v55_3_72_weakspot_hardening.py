from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.weakspot_audit import build_weakspot_audit, render_weakspot_audit
from winlocalassistant.custom_tools import validate_tool_code
from winlocalassistant.autonomy_capabilities import build_mutable_mission_plan
from winlocalassistant.autonomous_sequence import build_autonomous_tool_sequence
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.config import AssistantConfig


def test_v55_3_72_version_mentions_weakspot_and_custom_tool_hardening():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    assert f"v{__version__}" in VERSION_LABEL
    assert "no-regression" in low


def test_weakspot_audit_detects_silent_exception_pass(tmp_path):
    (tmp_path / "bad.py").write_text("try:\n    risky()\nexcept Exception:\n    pass\n", encoding="utf-8")
    report = build_weakspot_audit(tmp_path)
    assert any(i["category"] == "observability" for i in report["issues"])
    md = render_weakspot_audit(report)
    assert "Weakspot" in md and "Silent" in md


def test_custom_tool_validator_blocks_workspace_escape_attrs():
    code = """
def run(args, workspace, config):
    return {"ok": True, "data": workspace.parent.read_text()}
"""
    ok, problems = validate_tool_code(code)
    assert not ok
    assert any("parent" in p for p in problems)


def test_custom_tool_validator_still_allows_read_only_workspace_scan():
    code = """
def run(args, workspace, config):
    count = 0
    for path in workspace.rglob('*.py'):
        count += 1
    return {"ok": True, "summary": str(count), "data": {"count": count}}
"""
    ok, problems = validate_tool_code(code)
    assert ok, problems


def test_tool_registry_exposes_weakspot_audit(tmp_path):
    cfg = AssistantConfig(workspace=str(tmp_path))
    tools = ToolRegistry(cfg)
    assert "weakspot_audit" in tools.tools
    result = tools.call("weakspot_audit", path=".", write_report=False)
    assert "Weakspot" in result.data["markdown"]


def test_autonomy_capabilities_include_error_hunt_for_weakspot_prompt():
    plan = build_mutable_mission_plan("look for weakspots and do more error testing")
    names = [m.capability.name for m in plan.capabilities]
    assert "weakspot_error_hunt" in names


def test_autonomous_sequence_runs_weakspot_before_improvement():
    plan = build_autonomous_tool_sequence("improve Nova reliability and look for weakspots")
    tools = [step.tool for step in plan.steps]
    assert "weakspot_audit" in tools
