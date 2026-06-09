from pathlib import Path

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.bug_review import build_bug_review, render_bug_review
from winlocalassistant.config import AssistantConfig
from winlocalassistant.core import AssistantCore
from winlocalassistant.tools import ToolRegistry


def _version_tuple(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def test_version_is_current_and_mentions_active_release():
    assert _version_tuple(__version__) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL
    for word in ["wake", "voice", "no-regression"]:
        assert word in VERSION_LABEL.lower()


def test_bug_review_passes_current_tree():
    payload = build_bug_review(Path.cwd())
    assert payload["ok"] is True
    assert not [f for f in payload["findings"] if f["severity"] in {"critical", "high"}]
    text = render_bug_review(payload)
    assert "Nova Bug Review" in text
    assert "Check summary" in text


def test_bug_review_ignores_historical_readme_versions():
    payload = build_bug_review(Path.cwd())
    readme_version_findings = [
        f for f in payload["findings"]
        if f["path"] == "README.md" and f["category"] == "versioning"
    ]
    assert not readme_version_findings


def test_bug_review_ignores_webui_compatibility_markers():
    payload = build_bug_review(Path.cwd())
    webui_version_findings = [
        f for f in payload["findings"]
        if f["path"] == "winlocalassistant/webui.py" and f["category"] == "versioning"
    ]
    assert not webui_version_findings


def test_bug_review_command_and_tool_are_routed(tmp_path):
    cfg = AssistantConfig(workspace=str(Path.cwd()))
    app = AssistantCore(cfg)
    assert "bug_review" in app.tools.tools
    out = app.handle_command("/bug-review")
    assert "Nova Bug Review" in out
    assert "Overall" in out


def test_format_result_renders_markdown_payload():
    cfg = AssistantConfig(workspace=str(Path.cwd()))
    app = AssistantCore(cfg)
    result = app.tools.call("improvement_roadmap", focus="bug review smoke")
    rendered = app.format_result(result)
    assert "Improvement Roadmap" in rendered
    assert "Technical details" not in rendered[:300]


def test_autonomy_catalog_exposes_bug_review():
    from winlocalassistant.autonomy_capabilities import render_capability_markdown
    text = render_capability_markdown("more bug review and error testing")
    assert "bug_review" in text
    assert "/bug-review" in text
