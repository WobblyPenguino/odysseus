from pathlib import Path
import subprocess
import sys

from winlocalassistant import __version__, VERSION_LABEL
from winlocalassistant.autonomy_capabilities import select_capabilities_for_goal
from winlocalassistant.config import AssistantConfig
from winlocalassistant.tools import ToolRegistry
from winlocalassistant.whole_codebase_review import build_whole_codebase_review, render_whole_codebase_review


def _version_tuple(value: str) -> tuple[int, int, int]:
    return tuple(int(part) for part in value.split("."))  # type: ignore[return-value]


def test_version_metadata_current_and_active_release_words():
    assert _version_tuple(__version__) >= (55, 3, 123)
    assert f"v{__version__}" in VERSION_LABEL
    for word in ["wake", "voice", "packaging", "codebase"]:
        assert word in VERSION_LABEL.lower()


def test_whole_codebase_review_passes_and_writes_reports(tmp_path):
    root = Path.cwd()
    tools = ToolRegistry(AssistantConfig(workspace=str(root)))
    payload = build_whole_codebase_review(root, tool_names=sorted(tools.tools.keys()))
    assert payload["ok"] is True
    assert not payload["blockers"]
    assert payload["python"]["python_file_count"] > 20
    assert not payload["routes"]["missing_runtime_tools"]
    assert payload["docs"]["version_label_mentions_current_version"] is True
    assert payload["docs"]["version_label_mentions_current_capabilities"] is True
    assert "version_label_contains_legacy_terms" not in payload["docs"]
    md = render_whole_codebase_review(payload)
    assert "Whole Codebase Review" in md
    assert "Command/tool integration" in md
    assert (root / "docs" / "NOVA_WHOLE_CODEBASE_REVIEW_LATEST.md").exists()


def test_whole_codebase_review_tool_is_registered():
    tools = ToolRegistry(AssistantConfig(workspace=str(Path.cwd())))
    for name in ["whole_codebase_review", "review_codebase", "comprehensive_code_review"]:
        assert name in tools.tools
    result = tools.call("whole_codebase_review")
    assert result.ok
    assert "Whole Codebase Review" in result.data.get("message", "")


def test_autonomy_selects_whole_codebase_review_capability():
    matches = select_capabilities_for_goal("review the whole codebase and look for ways to improve all code", limit=8)
    names = [m.capability.name for m in matches]
    assert "whole_codebase_review" in names


def test_app_supports_one_shot_slash_command():
    proc = subprocess.run(
        [sys.executable, "app.py", "/whole-codebase-review"],
        cwd=Path.cwd(),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=40,
    )
    assert proc.returncode == 0, proc.stderr
    assert "Whole Codebase Review" in proc.stdout
