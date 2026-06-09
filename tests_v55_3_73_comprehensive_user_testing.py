from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.user_testing import build_user_testing_report, render_user_testing_report


def test_v55_3_73_version_and_legacy_words():
    assert tuple(map(int, __version__.split("."))) >= (55, 3, 123)
    low = VERSION_LABEL.lower()
    for word in ["voice", "packaging", "codebase"]:
        assert word in low


def test_comprehensive_user_testing_report_smoke():
    report = build_user_testing_report(Path.cwd())
    assert report["total"] >= 10
    names = {c["name"] for c in report["checks"]}
    assert "python_syntax" in names
    assert "command_routes" in names
    assert "feature_audit" in names
    assert "candidate_tournament" in names
    rendered = render_user_testing_report(report)
    assert "Nova Comprehensive User Testing" in rendered
    assert "Recommended follow-up" in rendered


def test_comprehensive_user_testing_command_route():
    app = AssistantCore(AssistantConfig(workspace=str(Path.cwd()), allow_mutating_tools=True))
    out = app.handle_command("/comprehensive-user-test")
    assert "Nova Comprehensive User Testing" in out
    assert "Report written" in out


def test_comprehensive_user_testing_tool_registry_access():
    registry = ToolRegistry(AssistantConfig(workspace=str(Path.cwd()), allow_mutating_tools=True))
    result = registry.call("user_test_suite", path=".")
    assert result.summary == "Comprehensive user testing completed"
    assert "markdown" in result.data
